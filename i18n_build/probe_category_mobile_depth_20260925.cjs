/**
 * 分类页补内容 —— 移动端第二轮：内容深度 + 内链热区（2026-09-25）
 *
 * 第一轮已确认：三块零横向溢出、details 折叠正常、段宽 35–44 字/行、summary 热区 60–85px。
 * 本轮只查两件事：
 *   A. 内容垂直深度 —— 8 页卡片数 7–23，最厚那页要滑几屏才看到导语/FAQ？
 *   B. ilink 的 <li><a> 点击热区 —— 第一轮实测仅 18px，低于 WCAG 2.5.8 的 24×24 下限。
 *      并验证修复（inline-block + 纵向 padding）能否达标，以及会不会引入新溢出。
 */
const { chromium } = require('playwright');

const BASE = process.env.BASE || 'file:///Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16';
const PAGES = [
  { f: '__mobtest_yoga_props_accessories.html', n: 'yoga-props', cards: 23 },
  { f: '__mobtest_suede_cork_yoga_mats.html', n: 'suede-cork', cards: 14 },
  { f: '__mobtest_foam.html', n: 'foam-rollers', cards: 12 },
  { f: '__mobtest_jump_ropes.html', n: 'jump-ropes', cards: 7 },
];
const VPS = [{ w: 390, h: 844 }, { w: 320, h: 568 }, { w: 1440, h: 900 }];

const depth = () => {
  const de = document.documentElement, vh = window.innerHeight;
  const S = [...document.querySelectorAll('section')];
  const f = (el) => el ? {
    top: Math.round(el.getBoundingClientRect().top + window.scrollY),
    screens: Math.round((el.getBoundingClientRect().top + window.scrollY) / vh * 10) / 10,
    pct: Math.round((el.getBoundingClientRect().top + window.scrollY) / de.scrollHeight * 100),
    h: Math.round(el.getBoundingClientRect().height),
  } : null;
  return {
    docH: de.scrollHeight, vh,
    gridH: S[1] ? Math.round(S[1].getBoundingClientRect().height) : null,
    intro: f(S[2]), faq: f(S[3]), ilink: f(S[4]),
  };
};

const linkInfo = () => {
  const sec = [...document.querySelectorAll('section')].find(s => s.querySelector('ul') && s.querySelector('li a') && !s.querySelector('.faq-list'));
  if (!sec) return null;
  return [...sec.querySelectorAll('li a')].map(a => {
    const cs = getComputedStyle(a), r = a.getBoundingClientRect();
    const li = a.closest('li');
    return {
      txt: a.textContent.trim().slice(0, 22),
      h: Math.round(r.height * 10) / 10, w: Math.round(r.width),
      liH: Math.round(li.getBoundingClientRect().height),
      display: cs.display, fs: cs.fontSize, lh: cs.lineHeight,
      pad: cs.paddingTop + '/' + cs.paddingBottom,
    };
  });
};

(async () => {
  const b = await chromium.launch();
  for (const vp of VPS) {
    console.log('\n' + '='.repeat(94));
    console.log(`视口 ${vp.w}×${vp.h}`);
    console.log('='.repeat(94));
    for (const p of PAGES) {
      const page = await b.newPage({ viewport: { width: vp.w, height: vp.h }, deviceScaleFactor: 2 });
      await page.goto(`${BASE}/${p.f}`, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(200);
      const d = await page.evaluate(depth);
      console.log(`\n${p.n} (${p.cards} 张产品卡)  文档高 ${d.docH}px = ${(d.docH / d.vh).toFixed(1)} 屏 | 产品网格区高 ${d.gridH}px (${(d.gridH / d.vh).toFixed(1)} 屏)`);
      for (const k of ['intro', 'faq', 'ilink']) {
        const v = d[k];
        console.log(`   ${k.padEnd(6)} 距顶 ${String(v.top).padStart(5)}px = 第 ${v.screens} 屏 / 文档 ${v.pct}% 处   块高 ${v.h}px`);
      }

      const before = await page.evaluate(linkInfo);
      if (before) {
        console.log(`   [内链热区 · 现状] ${before[0].display} ${before[0].fs} 行高${before[0].lh} 纵向padding ${before[0].pad}`);
        for (const l of before) console.log(`      ${String(l.h).padStart(5)}px 高 × ${String(l.w).padStart(3)}px 宽   li 行高 ${l.liH}px   "${l.txt}"`);
      }
      await page.addStyleTag({ content: '.ilink-fix-probe li a{display:inline-block;padding:6px 0}' });
      await page.evaluate(() => { const s = [...document.querySelectorAll('section')].find(x => x.querySelector('li a') && !x.querySelector('.faq-list')); if (s) s.classList.add('ilink-fix-probe'); });
      await page.waitForTimeout(120);
      const after = await page.evaluate(linkInfo);
      const over = await page.evaluate(() => Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) - document.documentElement.clientWidth);
      if (after) {
        for (const l of after) console.log(`      [修复验证] ${String(l.h).padStart(5)}px 高 × ${String(l.w).padStart(3)}px 宽  display=${l.display}`);
        console.log(`      [修复验证] 修复后页面横向溢出 ${over} ${over > 1 ? '<<<溢出' : ''}`);
      }
      await page.close();
    }
  }
  await b.close();
})();
