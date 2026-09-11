// 改后效果截图：移动端 + 桌面端的分类卡缩略图
const { chromium } = require('playwright');
const path = require('path');
const ROOT = process.cwd();

(async () => {
  const b = await chromium.launch();
  for (const vp of [{ n: 'mobile', w: 390, h: 1400, dpr: 3 }, { n: 'desktop', w: 1440, h: 1200, dpr: 2 }]) {
    const ctx = await b.newContext({ viewport: { width: vp.w, height: vp.h }, deviceScaleFactor: vp.dpr });
    const p = await ctx.newPage();
    await p.goto('file://' + path.join(ROOT, 'products.html'), { waitUntil: 'load' });
    await p.evaluate(() => document.documentElement.classList.add('show-zh'));
    await p.waitForTimeout(700);
    const tiles = await p.$$('.cat-tile');
    for (let i = 0; i < Math.min(3, tiles.length); i++) {
      await tiles[i].screenshot({ path: `outputs/改后-${vp.n}-card${i + 1}.png` });
    }
    // 采样：格子角部像素 vs 卡片空白，验证是否统一
    const s = await p.evaluate(() => {
      const tile = document.querySelector('.cat-tile');
      const thumb = tile.querySelector('.ct-thumbs a');
      const img = thumb.querySelector('img');
      const ics = getComputedStyle(img);
      const ar = thumb.getBoundingClientRect(), ir = img.getBoundingClientRect();
      const gapPt = { x: Math.round(ar.right + 4), y: Math.round(ar.top + ar.height / 2) };
      return { fit: ics.objectFit, thumb: [Math.round(ar.width), Math.round(ar.height)],
               imgBox: [Math.round(ir.width), Math.round(ir.height)],
               padPx: Math.round(ar.width - ir.width), gapPt };
    });
    console.log(`[${vp.n}] thumb=${s.thumb.join('x')} img=${s.imgBox.join('x')} fit=${s.fit} 内缩=${s.padPx}px`);
    await ctx.close();
  }
  console.log('截图已写入 outputs/改后-*.png');
  await b.close();
})();
