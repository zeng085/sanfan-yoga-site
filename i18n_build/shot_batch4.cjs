/**
 * 第四批「品类通用款」6 个新页 + 3 个分类页的本地实拍。
 *
 * 运行：
 *   NODE_PATH=/Users/mac-zlg/.workbuddy/binaries/node/workspace/node_modules \
 *   node i18n_build/shot_batch4.cjs
 *
 * 依赖本地 http 服务：python3 -m http.server 8848
 * ⚠️ 不要用 file:// —— search 缩略图与图片预取在 file:// 下会误报。
 */
const {chromium} = require('playwright');
const path = require('path');
const fs = require('fs');

const ROOT = process.cwd();
const OUT = path.join(ROOT, 'outputs', 'batch4-preview');
const BASE = process.env.PREVIEW_BASE || 'http://127.0.0.1:8848';
const U = f => BASE + '/' + f;

const PRODUCTS = ['ab-wheel', 'adjustable-dumbbell', 'beaded-jump-rope',
                  'color-kettlebell', 'suspension-training', 'vibration-machine'];
const CATS = ['strength-training', 'jump-ropes', 'massage-recovery'];

(async () => {
  fs.mkdirSync(OUT, {recursive: true});
  const b = await chromium.launch();
  const p = await b.newPage({viewport: {width: 1440, height: 900}, deviceScaleFactor: 2});

  for (const s of PRODUCTS) {
    await p.goto(U(`products/${s}.html`), {waitUntil: 'load'});
    await p.waitForTimeout(1200);
    await p.screenshot({path: path.join(OUT, `p-${s}-top.png`)});
    await p.locator('table.spec-table').first().scrollIntoViewIfNeeded();
    await p.waitForTimeout(600);
    await p.screenshot({path: path.join(OUT, `p-${s}-spec.png`)});
    console.log('  ok', s);
  }

  for (const c of CATS) {
    await p.goto(U(`${c}.html`), {waitUntil: 'load'});
    await p.waitForTimeout(1500);
    await p.screenshot({path: path.join(OUT, `c-${c}-top.png`)});
    await p.evaluate(() => {
      const g = document.querySelector('.prod-grid, .grid, .cards');
      if (g) window.scrollTo(0, g.getBoundingClientRect().top + window.scrollY - 120);
    });
    await p.waitForTimeout(700);
    await p.screenshot({path: path.join(OUT, `c-${c}-grid.png`)});
    console.log('  ok', c);
  }

  await b.close();
  console.log('→', path.relative(ROOT, OUT));
})();
