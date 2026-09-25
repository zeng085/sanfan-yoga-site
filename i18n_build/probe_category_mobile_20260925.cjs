/**
 * 分类页补内容 —— 移动端友好度实测（2026-09-25）
 *
 * 目的：回答「新增的导语块 / FAQ 块 / 内链块在移动端好不好用」，用实测数据，不用推断。
 *
 * 被测：
 *   · __mobtest_foam.html  —— 把 tpe-yoga-mats.html 的三块原样注入 foam-rollers.html
 *                             得到的「补完后」形态（结构等价，内容为 EVA 代理）
 *   · tpe-yoga-mats.html   —— 线上已有的真实样板页（交叉验证）
 *   · foam-rollers.html    —— 补之前（对照基线）
 *
 * 判据：
 *   1. 页面级横向溢出 = max(html,body).scrollWidth - html.clientWidth（>1 记为溢出）
 *   2. 真能横向滚动：scrollTo(9999,0) 后 window.scrollX > 0
 *   3. 块内元素超出自身父容器 > 1.5px
 *   4. 正文每行字符数（<30 或 >90 都算可读性问题）
 *   5. 点击热区：summary >= 44px（Apple HIG 下限）
 *   6. 内容垂直深度：距页顶 / 视口高 = 要滑几屏才看到
 */
const { chromium } = require('playwright');

const BASE = process.env.BASE || 'http://127.0.0.1:8862';
const VP = [
  { name: 'iphone-14', w: 390, h: 844 },
  { name: 'narrow', w: 360, h: 800 },
  { name: 'iphone-se1', w: 320, h: 568 },
];
const PAGES = [
  { file: '__mobtest_foam.html', label: '补完后(注入模拟)' },
  { file: 'tpe-yoga-mats.html', label: '样板页(线上已有)' },
  { file: 'foam-rollers.html', label: '补之前(基线)' },
];

const probe = () => {
  const de = document.documentElement;
  const before = window.scrollX;
  window.scrollTo(9999, 0);
  const canScrollX = window.scrollX > 0;
  window.scrollTo(before, window.scrollY);

  const pageOver = Math.max(de.scrollWidth, document.body.scrollWidth) - de.clientWidth;
  const docH = de.scrollHeight;
  const vh = window.innerHeight;
  const bodyOX = getComputedStyle(document.body).overflowX;

  const sections = [...document.querySelectorAll('section')];
  const hasNew = sections.length >= 6;

  function block(el) {
    if (!el) return null;
    const r = el.getBoundingClientRect();
    let maxOver = 0, overEl = '';
    for (const c of el.querySelectorAll('*')) {
      const cr = c.getBoundingClientRect();
      const pr = c.parentElement.getBoundingClientRect();
      const o = cr.right - pr.right;
      if (o > maxOver) { maxOver = o; overEl = c.tagName + '.' + String(c.className || '').slice(0, 24); }
    }
    const p = el.querySelector('p');
    let line = null;
    if (p) {
      const cs = getComputedStyle(p);
      const pw = p.getBoundingClientRect().width;
      const fs = parseFloat(cs.fontSize);
      line = {
        fs: fs, lh: cs.lineHeight, w: Math.round(pw),
        charsPerLine: Math.round(pw / (fs * 0.5)),
        maxw: cs.maxWidth,
      };
    }
    const sum = el.querySelector('summary');
    let tap = null, sumLines = null, sumFs = null;
    if (sum) {
      const sr = sum.getBoundingClientRect();
      tap = Math.round(sr.height);
      sumFs = getComputedStyle(sum).fontSize;
      const sp = sum.querySelector('.lang-en') || sum.querySelector('span');
      sumLines = sp ? sp.getClientRects().length : null;
    }
    const a = el.querySelector('li a');
    const linkTap = a ? Math.round(a.getBoundingClientRect().height) : null;
    const li = el.querySelector('ul');
    const liPad = li ? getComputedStyle(li).paddingLeft : null;
    return {
      top: Math.round(r.top + window.scrollY),
      screens: Math.round((r.top + window.scrollY) / vh * 10) / 10,
      pct: Math.round((r.top + window.scrollY) / docH * 100),
      h: Math.round(r.height),
      w: Math.round(r.width),
      maxOver: Math.round(maxOver * 10) / 10,
      overEl: overEl,
      nFaq: el.querySelectorAll('.faq-item').length,
      nLink: el.querySelectorAll('li').length,
      line: line, tap: tap, sumLines: sumLines, sumFs: sumFs,
      linkTap: linkTap, liPad: liPad,
    };
  }

  const out = { pageOver, canScrollX, docH, vh, bodyOX, nSec: sections.length, blocks: null };
  if (hasNew) {
    out.blocks = {
      intro: block(sections[2]),
      faq: block(sections[3]),
      ilink: block(sections[4]),
    };
  }
  return out;
};

(async () => {
  const browser = await chromium.launch();
  for (const vp of VP) {
    console.log('\n' + '='.repeat(96));
    console.log(`视口 ${vp.w}×${vp.h} (${vp.name})`);
    console.log('='.repeat(96));
    for (const pg of PAGES) {
      const page = await browser.newPage({ viewport: { width: vp.w, height: vp.h }, deviceScaleFactor: 2 });
      await page.goto(`${BASE}/${pg.file}`, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(260);

      let r = await page.evaluate(probe);

      // 折叠态：先量完，再展开第一个 FAQ 重量一次
      let expanded = null;
      const sum = await page.$('section:has(.faq-list) summary');
      if (sum) {
        await sum.click();
        await page.waitForTimeout(160);
        const r2 = await page.evaluate(probe);
        expanded = { docH: r2.docH, dH: r2.docH - r.docH, faqH: r2.blocks && r2.blocks.faq.h, pageOver: r2.pageOver };
      }

      const flag = (v) => (v > 1 ? ' <<<溢出' : '');
      console.log(`\n-- ${pg.label}  (${pg.file})`);
      console.log(`   section=${r.nSec}  文档高=${r.docH}px  页面横向溢出=${r.pageOver}${flag(r.pageOver)}  可横向滚动=${r.canScrollX}  body.overflow-x=${r.bodyOX}`);
      if (r.blocks) {
        for (const k of ['intro', 'faq', 'ilink']) {
          const b = r.blocks[k];
          if (!b) continue;
          const l = b.line ? `段宽${b.line.w}px/${b.line.fs}px 行${b.line.lh} ≈${b.line.charsPerLine}字/行(max-w:${b.line.maxw})` : '';
          const t = b.tap ? ` | summary 热区${b.tap}px 字${b.sumFs} ${b.sumLines}行` : '';
          const lk = b.linkTap ? ` | li 链接热区${b.linkTap}px ul左缩进${b.liPad}` : '';
          console.log(`   [${k.padEnd(5)}] 距顶${String(b.top).padStart(5)}px (${b.screens}屏, ${b.pct}%处) 高${b.h}px 宽${b.w}px 内溢${b.maxOver}${flag(b.maxOver)} ${b.overEl}`);
          console.log(`           ${l}${t}${lk}`);
        }
      }
      if (expanded) {
        console.log(`   展开首条FAQ: 文档高 ${r.docH} → ${expanded.docH} (+${expanded.dH}px)  FAQ块高 ${expanded.faqH}px  展开后页面溢出 ${expanded.pageOver}${flag(expanded.pageOver)}`);
      }
      await page.close();
    }
  }
  await browser.close();
})();
