// 对比：contain内缩 vs contain内缩+纸色蒙版（不同浓度）
const { chromium } = require('playwright');
const path = require('path');
const ROOT = process.cwd();

const MASKS = [
  { n: 'A-noMask', css: '' },
  { n: 'B-mask12', css: '.ct-thumbs a{position:relative}.ct-thumbs a::after{content:"";position:absolute;inset:0;background:rgba(249,247,242,.12);pointer-events:none}' },
  { n: 'C-mask24', css: '.ct-thumbs a{position:relative}.ct-thumbs a::after{content:"";position:absolute;inset:0;background:rgba(249,247,242,.24);pointer-events:none}' },
  { n: 'D-mask38', css: '.ct-thumbs a{position:relative}.ct-thumbs a::after{content:"";position:absolute;inset:0;background:rgba(249,247,242,.38);pointer-events:none}' },
];

(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 390, height: 1400 }, deviceScaleFactor: 2 });
  for (const m of MASKS) {
    const p = await ctx.newPage();
    await p.goto('file://' + path.join(ROOT, 'products.html'), { waitUntil: 'load' });
    await p.evaluate(() => document.documentElement.classList.add('show-zh'));
    if (m.css) await p.addStyleTag({ content: m.css });
    await p.waitForTimeout(600);
    const t = (await p.$$('.cat-tile'))[0];
    // 只截缩略图区，便于横向对比
    const box = await p.evaluate(() => {
      const el = document.querySelector('.cat-tile .ct-thumbs');
      const r = el.getBoundingClientRect();
      return { x: r.x - 6, y: r.y - 6, width: r.width + 12, height: r.height + 12 };
    });
    await p.screenshot({ path: `outputs/蒙版对比-${m.n}.png`, clip: box });
    console.log('已截', m.n);
    await p.close();
  }
  await b.close();
})();
