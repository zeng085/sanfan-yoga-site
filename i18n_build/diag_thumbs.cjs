// 诊断 products.html 分类卡缩略图在移动端的渲染差异
const { chromium } = require('playwright');
const path = require('path');
const ROOT = process.cwd();

(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 3 });
  const p = await ctx.newPage();
  await p.goto('file://' + path.join(ROOT, 'products.html'), { waitUntil: 'load' });
  await p.evaluate(() => document.documentElement.classList.add('show-zh'));
  await p.waitForTimeout(600);

  const info = await p.evaluate(() => {
    const out = [];
    document.querySelectorAll('.cat-tile').forEach((tile, ti) => {
      const h3 = tile.querySelector('h3');
      const thumbs = [...tile.querySelectorAll('.ct-thumbs a')].map((a) => {
        const img = a.querySelector('img');
        const acs = getComputedStyle(a), ics = getComputedStyle(img);
        const ar = a.getBoundingClientRect(), ir = img.getBoundingClientRect();
        return {
          src: (img.getAttribute('src') || '').split('/').pop(),
          aBox: [Math.round(ar.width), Math.round(ar.height)],
          iBox: [Math.round(ir.width), Math.round(ir.height)],
          aBg: acs.backgroundColor, aPad: acs.padding, aIso: acs.isolation,
          blend: ics.mixBlendMode, fit: ics.objectFit,
          natural: [img.naturalWidth, img.naturalHeight],
        };
      });
      out.push({ i: ti, name: h3 ? h3.textContent.trim().slice(0, 24) : '?', thumbs });
    });
    return out;
  });

  info.slice(0, 3).forEach((t) => {
    console.log(`\n=== cat-tile[${t.i}] ${t.name} ===`);
    t.thumbs.forEach((x, k) => {
      console.log(`  ${k + 1}. ${x.src.padEnd(38)} a=${x.aBox.join('x').padEnd(9)} img=${x.iBox.join('x').padEnd(9)}` +
        ` natural=${x.natural.join('x').padEnd(11)} fit=${x.fit.padEnd(8)} blend=${x.blend}` +
        `\n     aBg=${x.aBg} pad=${x.aPad} iso=${x.aIso}`);
    });
  });

  // 只截第一张分类卡，3 倍图便于看细节
  const tile = await p.$('.cat-tile');
  await tile.screenshot({ path: 'outputs/诊断-缩略图-移动端.png' });
  console.log('\n截图: outputs/诊断-缩略图-移动端.png');
  await b.close();
})();
