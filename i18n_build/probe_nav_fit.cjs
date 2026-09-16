// 断点标定器：注入候选 CSS，扫描一串视口宽度，找出「全部语言都放得下」的最小宽度。
// 用途：给导航的桌面/汉堡切换点定一个**实测**出来的值，而不是拍脑袋。
// 用法：CSSFILE=/tmp/nav_candidate.css node i18n_build/probe_nav_fit.cjs
const { chromium } = require('playwright');
const fs = require('fs');

const BASE = process.env.BASE || 'http://127.0.0.1:8848';
const CSS = process.env.CSSFILE ? fs.readFileSync(process.env.CSSFILE, 'utf8') : '';
const LANGS = ['', 'de', 'ja', 'ko', 'fr', 'it', 'es'];
const FROM = +(process.env.FROM || 980), TO = +(process.env.TO || 1680), STEP = +(process.env.STEP || 20);

(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const rows = [];
  for (let w = FROM; w <= TO; w += STEP) {
    await page.setViewportSize({ width: w, height: 900 });
    const line = { w, langs: {} };
    for (const lg of LANGS) {
      await page.goto(BASE + '/' + (lg ? lg + '/' : ''), { waitUntil: 'domcontentloaded' });
      if (CSS) await page.addStyleTag({ content: CSS });
      await page.waitForTimeout(60);
      const m = await page.evaluate(() => {
        const q = (s) => document.querySelector(s);
        const nav = q('.nav'), links = q('.nav-links'), brand = q('.nav-brand'), acts = q('.nav-actions'), tog = q('.menu-toggle');
        if (!nav || !links) return null;
        const toggleVisible = tog && getComputedStyle(tog).display !== 'none';
        const cs = getComputedStyle(links);
        if (cs.display === 'none') return { hamburger: true };
        const lb = links.getBoundingClientRect(), bb = brand.getBoundingClientRect(), ab = acts.getBoundingClientRect();
        const items = [...links.querySelectorAll(':scope > a, :scope > .nav-drop > a')];
        const wraps = items.filter((a) => a.getBoundingClientRect().height > 26).length;
        return {
          gapBrand: Math.round(lb.left - bb.right),      // ≥0 才不重叠
          gapActions: Math.round(ab.left - lb.right),    // ≥0 才不重叠
          wraps,
          maxH: Math.max(...items.map((a) => Math.round(a.getBoundingClientRect().height))),
          docScroll: document.documentElement.scrollWidth - window.innerWidth,
          toggleVisible,
          linksW: Math.round(lb.width),
        };
      });
      line.langs[lg || 'en'] = m;
    }
    rows.push(line);
  }
  await b.close();

  // 每种语言的「首次全部合格」宽度（合格 = 无换行 且 与品牌/动作区均不重叠 且 无横滚）
  const ok = (m) => m && !m.hamburger && m.wraps === 0 && m.gapBrand >= 4 && m.gapActions >= 4 && m.docScroll <= 1;
  const first = {};
  for (const r of rows) for (const [lg, m] of Object.entries(r.langs)) {
    if (ok(m) && first[lg] === undefined) first[lg] = r.w;
  }
  console.log('各语言「桌面导航首次放得下」的视口宽度：');
  for (const lg of ['en', 'de', 'ja', 'ko', 'fr', 'it', 'es'])
    console.log('  %-3s %s', lg, first[lg] === undefined ? '在扫描范围内始终放不下' : first[lg] + 'px');
  const worst = Math.max(0, ...Object.values(first).filter((v) => v !== undefined));
  console.log('\n最宽语言需要：%dpx  → 汉堡切换点应设为 ≥%dpx', worst, worst);

  // 细看最差语言在临界处的余量
  console.log('\n各宽度下的最小余量（gapBrand / gapActions / 换行数）：');
  for (const r of rows) {
    const vals = Object.entries(r.langs).filter(([, m]) => m && !m.hamburger);
    if (!vals.length) continue;
    const minGap = Math.min(...vals.map(([, m]) => Math.min(m.gapBrand, m.gapActions)));
    const worstLg = vals.find(([, m]) => Math.min(m.gapBrand, m.gapActions) === minGap)[0];
    const anyWrap = vals.reduce((a, [, m]) => a + m.wraps, 0);
    console.log('  %d  余量最小 %s %dpx  换行合计 %d', r.w, worstLg, minGap, anyWrap);
  }
})();
