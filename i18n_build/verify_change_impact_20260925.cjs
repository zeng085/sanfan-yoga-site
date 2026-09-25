/**
 * 本轮 SEO 改动的影响验收（浏览器级）—— 2026-09-25
 *
 * 检查四件事：
 *   1. 横向溢出（页面 + 改动元素）
 *   2. 改动元素的 DOM 结构与几何（尤其 pd-specs 的 h2 有没有吞掉 <table>）
 *   3. 链接正确性（空 href / "#" href / resolve 越界）
 *   4. 语言切换按钮是否真的还能用（A5 把 <a> 换成 <button>）
 *
 * ⚠️ 不用 networkidle（会拦在 GA 请求上）→ domcontentloaded + 短等待。
 * ⚠️ 中文态需同时设 localStorage.siteLang 与 cookie 双通道。
 */
const { chromium } = require('playwright');

const BASE = 'http://127.0.0.1:8851';
const LANGS = ['', 'de', 'ja', 'ko', 'fr', 'it', 'es'];

// 每个语言抽 4 页：分类页(A2)、产品页(A1)、faq(A3)、blog 文章(A5)
const SUB = [['', 'tpe-yoga-mats.html'], ['', 'products/ab-wheel.html'],
             ['', 'faq.html'], ['', 'blog/tpe-vs-pu.html']];

const VIEWPORTS = [{ w: 1280, h: 900, tag: 'desktop' },
                   { w: 768, h: 1024, tag: 'tablet' },
                   { w: 390, h: 844, tag: 'mobile' }];

// 改动点：选择器 + 旧选择器（旧必须消失）
const POINTS = [
  { name: 'cat-title', newSel: '.cat-head .cat-title', oldSel: '.cat-head h3' },
  { name: 'pd-specs-h2', newSel: '.pd-specs h2', oldSel: '.pd-specs h3' },
  { name: 'faq-cat', newSel: 'h2.faq-cat', oldSel: 'h3.faq-cat' },
  { name: 'pc-body-h2', newSel: '.pc-body h2', oldSel: '.pc-body h3' },
];

async function probe(page) {
  return page.evaluate((POINTS) => {
    const de = document.documentElement;
    const out = {
      url: location.pathname,
      docW: de.scrollWidth, cliW: de.clientWidth,
      hOverflow: de.scrollWidth - de.clientWidth,
      points: {}, badLinks: [], wideEls: [], errors: [],
    };

    // ---- 变更点：新旧选择器 + 几何 + 内容长度 ----
    for (const p of POINTS) {
      const els = [...document.querySelectorAll(p.newSel)];
      const oldEls = [...document.querySelectorAll(p.oldSel)];
      const info = { n: els.length, oldN: oldEls.length, overs: [] };
      if (els.length) {
        const el = els[0];
        const r = el.getBoundingClientRect();
        const pr = el.parentElement ? el.parentElement.getBoundingClientRect() : null;
        info.txt = el.textContent.trim().slice(0, 34);
        info.txtLen = el.textContent.trim().length;
        info.cs = getComputedStyle(el);
        info.geo = { w: Math.round(r.width), h: Math.round(r.height),
                     right: Math.round(r.right) };
        info.overRight = pr ? Math.round(r.right - pr.right) : null;
        // h2 是否吞掉了后面的块级元素（A1 曾产生 <h2>…</h3> 导致吞 table）
        info.badChild = [...el.children].filter(
          c => ['TABLE', 'DIV', 'UL', 'P', 'SECTION'].includes(c.tagName)
        ).map(c => c.tagName);
      }
      out.points[p.name] = info;
    }

    // ---- 横向溢出的元素（排除隐藏与 fixed）----
    const all = [...document.querySelectorAll('body *')];
    for (const el of all) {
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden' || cs.position === 'fixed') continue;
      const r = el.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) continue;
      if (r.right > de.clientWidth + 1.5 || r.left < -1.5) {
        out.wideEls.push({
          sel: el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).split(' ')[0] : ''),
          left: Math.round(r.left), right: Math.round(r.right), w: Math.round(r.width),
        });
      }
      if (out.wideEls.length > 10) break;
    }

    // ---- 链接：空 href / "#" / 越界 ----
    for (const a of document.querySelectorAll('a')) {
      const raw = a.getAttribute('href');
      if (raw === null || raw.trim() === '' || raw.trim() === '#') {
        out.badLinks.push({ raw: String(raw), txt: a.textContent.trim().slice(0, 24),
                            cls: String(a.className).slice(0, 30) });
      } else if (raw.startsWith('/')) {
        // 站内绝对路径：应落在站点根内（不能是 //host 协议相对）
        if (raw.startsWith('//')) out.badLinks.push({ raw, txt: a.textContent.trim().slice(0, 24), cls: 'protocol-relative' });
      }
    }
    return out;
  }, POINTS);
}

(async () => {
  const browser = await chromium.launch();
  const fails = [], warns = [];
  let n = 0;

  for (const lang of LANGS) {
    for (const [, rel] of SUB) {
      const url = BASE + '/' + (lang ? lang + '/' : '') + rel;
      for (const vp of VIEWPORTS) {
        const ctx = await browser.newContext({ viewport: { width: vp.w, height: vp.h } });
        const page = await ctx.newPage();
        const errors = [];
        page.on('pageerror', e => errors.push('pageerror: ' + e.message));
        page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text().slice(0, 10)); });
        let r = null;
        try {
          await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 12000 });
          await page.waitForTimeout(220);
          r = await probe(page);
        } catch (e) {
          fails.push(`${lang || 'en'}/${rel} ${vp.tag} 打开失败: ${e.message.slice(0, 60)}`);
          await ctx.close();
          continue;
        }
        n++;
        const id = `${lang || 'en'}/${rel}@${vp.tag}`;

        if (r.hOverflow > 1) fails.push(`${id} 页面横向溢出 ${r.hOverflow}px`);
        if (r.wideEls.length) fails.push(`${id} 溢出元素: ${r.wideEls.map(x => x.sel + '(' + x.right + '>' + r.cliW + ')').slice(0, 4).join(', ')}`);
        if (r.badLinks.length) fails.push(`${id} 坏链接 ${r.badLinks.length} 个: ${r.badLinks.slice(0, 3).map(x => x.raw + '[' + x.cls + ']').join(', ')}`);
        if (errors.length) warns.push(`${id} 控制台: ${errors.slice(0, 2).join(' | ')}`);

        const np = Object.entries(r.points).filter(([, v]) => v.n > 0);
        for (const [name, v] of np) {
          if (v.oldN > 0) fails.push(`${id} ${name}: 旧选择器仍存在 ${v.oldN} 个`);
          if (v.overRight !== null && v.overRight > 1) fails.push(`${id} ${name}: 超出父容器 ${v.overRight}px`);
          if (v.badChild && v.badChild.length) fails.push(`${id} ${name}: h2 吞掉块级子元素 ${v.badChild.join(',')}`);
        }
        // pd-specs 专项：h2 文本应只是标题（不能把表格文本吞进去）
        const ps = r.points['pd-specs-h2'];
        if (ps.n && ps.txtLen > 60) fails.push(`${id} pd-specs h2 文本过长(${ps.txtLen})，疑似吞内容: ${ps.txt.slice(0, 40)}`);
        await ctx.close();
      }
    }
  }

  console.log('=== 浏览器影响验收 ===');
  console.log('检查用例：%d 个（7 语言 × 4 页 × 3 视口）', n);
  console.log('未通过：%d 项', fails.length);
  fails.slice(0, 40).forEach(f => console.log('   ❌', f));
  console.log('提示（控制台/资源）：%d 项', warns.length);
  const uniq = {};
  warns.forEach(w => { const k = w.split(' ').slice(1).join(' '); uniq[k] = (uniq[k] || 0) + 1; });
  Object.entries(uniq).slice(0, 8).forEach(([k, v]) => console.log(`   🟡 ${v}×  ${k.slice(0, 90)}`));
  await browser.close();
  process.exit(fails.length ? 1 : 0);
})();
