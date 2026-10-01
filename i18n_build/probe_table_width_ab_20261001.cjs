const { chromium } = require('playwright');
const BASE = 'http://127.0.0.1:8864';
const PAGES = [['live', '/pilates/_ab_live_ladder-barrel.html'], ['new', '/pilates/pilates-ladder-barrel.html']];
(async () => {
  const b = await chromium.launch();
  for (const vp of [{ n: 'desktop', w: 1440, h: 900 }, { n: 'mobile', w: 390, h: 844 }]) {
    for (const [k, u] of PAGES) {
      const ctx = await b.newContext({ viewport: { width: vp.w, height: vp.h }, isMobile: vp.n === 'mobile', hasTouch: vp.n === 'mobile' });
      const p = await ctx.newPage();
      await p.goto(BASE + u, { waitUntil: 'load' });
      await p.waitForTimeout(400);
      const m = await p.evaluate(() => {
        const wrap = document.querySelector('.pl-spec-wrap');
        const tb = document.querySelector('.pl-spec');
        if (!tb) return { err: 'no table' };
        const R = (e) => { const r = e.getBoundingClientRect(); return { w: Math.round(r.width), h: Math.round(r.height) }; };
        const ths = Array.from(tb.querySelectorAll('thead th')).map((t) => ({ txt: t.innerText.replace(/\s+/g, ' ').trim().slice(0, 20), ...R(t) }));
        const tds0 = Array.from(tb.querySelectorAll('tbody tr:first-child td')).map((t) => ({ txt: t.innerText.replace(/\s+/g, ' ').trim().slice(0, 22), ...R(t) }));
        const tbr = R(tb);
        return {
          wrap: R(wrap), wrapClient: wrap.clientWidth, wrapScroll: wrap.scrollWidth,
          table: tbr, tableCS: getComputedStyle(tb).width,
          ths, tds0,
          rowCount: tb.querySelectorAll('tbody tr').length,
          pctOfWrap: Math.round((tbr.w / wrap.clientWidth) * 100),
        };
      });
      console.log('\n=== ' + k + ' @ ' + vp.n + ' ===');
      if (m.err) { console.log('  ' + m.err); await ctx.close(); continue; }
      console.log('  .pl-spec-wrap  宽 ' + m.wrap.w + '  clientWidth ' + m.wrapClient + '  scrollWidth ' + m.wrapScroll + (m.wrapScroll > m.wrapClient ? '   <- 需横滑' : ''));
      console.log('  table          宽 ' + m.table.w + '  computed width=' + m.tableCS + '  = 容器的 ' + m.pctOfWrap + '%');
      console.log('  行数 ' + m.rowCount);
      console.log('  表头列宽: ' + m.ths.map((t) => t.txt + ':' + t.w).join('  '));
      console.log('  首行列宽: ' + m.tds0.map((t) => t.txt + ':' + t.w).join('  '));
      await ctx.close();
    }
  }
  await b.close();
})();
