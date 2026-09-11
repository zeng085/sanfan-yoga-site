// 采样：缩略图渲染后的实际像素 vs 卡片空白处，判断 multiply 是否真的把白底融掉
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const ROOT = process.cwd();

(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 390, height: 1400 }, deviceScaleFactor: 1 });
  const p = await ctx.newPage();
  await p.goto('file://' + path.join(ROOT, 'products.html'), { waitUntil: 'load' });
  await p.evaluate(() => document.documentElement.classList.add('show-zh'));
  await p.waitForTimeout(700);
  await p.evaluate(() => window.scrollTo(0, 0));
  await p.waitForTimeout(300);

  const data = await p.evaluate(() => {
    const tile = document.querySelector('.cat-tile');
    const tr = tile.getBoundingClientRect();
    // 卡片空白基准点：标题左侧空白（ct-body 内、缩略图上方）
    const blank = document.querySelector('.cat-tile .ct-kw').getBoundingClientRect();
    const thumbs = [...tile.querySelectorAll('.ct-thumbs a')].map((a) => {
      const r = a.getBoundingClientRect();
      return {
        src: a.querySelector('img').getAttribute('src').split('/').pop(),
        rect: [r.left, r.top, r.width, r.height],
      };
    });
    return {
      blankPt: [blank.right + 20, blank.top + blank.height / 2],
      tile: [tr.left, tr.top, tr.width, tr.height],
      thumbs,
    };
  });

  await p.screenshot({ path: '/tmp/thumbs_page.png', fullPage: false });
  fs.writeFileSync('/tmp/thumbs_geom.json', JSON.stringify(data, null, 1));
  console.log('tile 宽:', Math.round(data.tile[2]));
  console.log('空白基准点:', data.blankPt.map(Math.round));
  data.thumbs.forEach((t, i) => console.log(`  ${i + 1}. ${t.src.padEnd(38)} @ ${t.rect.map(Math.round)}`));
  await b.close();
})();
