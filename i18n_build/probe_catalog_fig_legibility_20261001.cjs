const { chromium } = require('playwright');
const BASE = 'http://127.0.0.1:8865';
(async () => {
  const b = await chromium.launch();
  for (const vp of [{ n: 'desktop', w: 1440, h: 900 }, { n: 'mobile', w: 390, h: 844 }]) {
    const ctx = await b.newContext({ viewport: { width: vp.w, height: vp.h }, deviceScaleFactor: vp.n === 'mobile' ? 2 : 1, isMobile: vp.n === 'mobile', hasTouch: vp.n === 'mobile' });
    const p = await ctx.newPage();
    await p.goto(BASE + '/pilates/pilates-ladder-barrel.html', { waitUntil: 'load' });
    await p.evaluate(async () => { const s = window.innerHeight; for (let y = 0; y < document.body.scrollHeight; y += s) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 100)); } window.scrollTo(0, 0); });
    await p.waitForTimeout(800);
    const m = await p.evaluate(() => {
      const out = { figs: [], cards: [], quotes: [] };
      document.querySelectorAll('.cat-fig').forEach((f) => {
        const img = f.querySelector('img');
        if (!img) return;
        const r = img.getBoundingClientRect();
        const cs = getComputedStyle(img);
        out.figs.push({
          src: (img.getAttribute('src') || '').split('/').pop(),
          cssW: Math.round(r.width), cssH: Math.round(r.height),
          natW: img.naturalWidth, natH: img.naturalHeight,
          objectFit: cs.objectFit,
          // 画册页在屏幕上的实际渲染比例：图片按 cssW 显示 A4 页宽
          shrink: img.naturalWidth ? +(r.width / img.naturalWidth).toFixed(3) : null,
          // 画册页上原字号约 9-10px（A4 扫描 2480px 宽时约 21px），换算到屏幕
          estTextPx: img.naturalWidth ? +(r.width / img.naturalWidth * 21).toFixed(1) : null,
        });
      });
      document.querySelectorAll('.model-card').forEach((c) => {
        const r = c.getBoundingClientRect();
        const dds = Array.from(c.querySelectorAll('dd')).map((d) => d.innerText.replace(/\s+/g, ' ').trim());
        out.cards.push({ w: Math.round(r.width), h: Math.round(r.height), vals: dds, emptyCount: dds.filter((x) => x === '—').length });
      });
      out.quotes = Array.from(document.querySelectorAll('.model-card a')).map((a) => a.innerText.replace(/\s+/g, ' ').trim()).slice(0, 8);
      return out;
    });
    console.log('\n===== ' + vp.n + ' (' + vp.w + 'px) =====');
    m.figs.forEach((f) => {
      console.log('  画册图 ' + f.src + ':  显示 ' + f.cssW + '×' + f.cssH + '  原始 ' + f.natW + '×' + f.natH + '  fit=' + f.objectFit);
      console.log('      缩放比 ' + f.shrink + '  → 画册上 21px 的字在屏幕上约 ' + f.estTextPx + 'px  ' + (f.estTextPx < 7 ? '❌ 肉眼不可读（必须点开大图）' : f.estTextPx < 10 ? '⚠️ 勉强可辨' : '✅ 可读'));
    });
    m.cards.forEach((c, i) => console.log('  型号卡 ' + (i + 1) + ': ' + c.w + '×' + c.h + '  值=' + JSON.stringify(c.vals) + '  空值 ' + c.emptyCount + '/3'));
    console.log('  卡片 CTA: ' + JSON.stringify(m.quotes));
    await ctx.close();
  }
  await b.close();
})();
