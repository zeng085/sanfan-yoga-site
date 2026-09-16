// 量「导航需要多宽」：把 .nav-links 的每个项按 max-content 摆开，算出最小可用宽度需求。
// 输出：品牌宽 + 导航项 max-content 宽 + 动作区宽 + 间距 = 需要的最小容器宽度（含 container 左右 padding）。
// 用法：node i18n_build/measure_nav_need.cjs
const { chromium } = require('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:8848';
const LANGS = ['', 'de', 'ja', 'ko', 'fr', 'it', 'es'];

(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const rows = [];
  for (const lg of LANGS) {
    await page.goto(BASE + '/' + (lg ? lg + '/' : ''), { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(150);
    const m = await page.evaluate(() => {
      const q = (s) => document.querySelector(s);
      const nav = q('.nav'), links = q('.nav-links'), brand = q('.nav-brand'), acts = q('.nav-actions');
      if (!nav) return null;
      // max-content 宽度：临时把容器放开成 auto/fit-content 量一次
      const clone = nav.cloneNode(true);
      clone.style.cssText = 'position:absolute;left:-9999px;top:0;width:max-content;max-width:none;display:flex;';
      document.body.appendChild(clone);
      const cl = clone.querySelector('.nav-links');
      const items = [...cl.querySelectorAll(':scope > a, :scope > .nav-drop > a')].map((a) => ({
        t: (a.textContent || '').trim().slice(0, 22),
        w: Math.ceil(a.getBoundingClientRect().width),
        h: Math.ceil(a.getBoundingClientRect().height),
      }));
      const linksW = Math.ceil(cl.getBoundingClientRect().width);
      const brandW = Math.ceil(clone.querySelector('.nav-brand').getBoundingClientRect().width);
      const actsW = Math.ceil((clone.querySelector('.nav-actions') || { getBoundingClientRect: () => ({ width: 0 }) }).getBoundingClientRect().width);
      clone.remove();
      const gap = parseFloat(getComputedStyle(links).columnGap || getComputedStyle(links).gap) || 0;
      return { brandW, linksW, actsW, gap, items, n: items.length, navH: Math.round(nav.getBoundingClientRect().height) };
    });
    if (m) rows.push({ lg: lg || 'en', ...m });
  }
  await b.close();
  console.log('语言  项数 导航项合计  品牌   动作   需要容器宽(=品牌+导航+动作+80padding)');
  for (const r of rows) {
    const need = r.brandW + r.linksW + r.actsW + 80;
    console.log('%s  %d  %d  %d  %d  → %d',
      r.lg.padEnd(3), r.n, r.linksW, r.brandW, r.actsW, need);
  }
  console.log('\n最宽的 5 个导航项：');
  for (const r of rows) {
    const top = r.items.slice().sort((a, b) => b.w - a.w).slice(0, 5);
    console.log('  %s: %s', r.lg.padEnd(3), top.map((t) => `"${t.t}"(${t.w}×${t.h})`).join('  '));
  }
})();
