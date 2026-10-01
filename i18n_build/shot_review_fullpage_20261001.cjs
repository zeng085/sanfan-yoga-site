// 给改版预览页截全页图（供人工浏览）
// 关键：某些图带 loading="lazy"，直接 fullPage 截图会得到空白块 →
//   必须先滚动整页预热让浏览器发起加载，等图片 complete 后再滚回顶部截图。
// 用法：node shot_review_fullpage_20261001.cjs <url> <out.png> <width>
const { chromium } = require('playwright');

(async () => {
  const url = process.argv[2];
  const out = process.argv[3];
  const width = parseInt(process.argv[4] || '1280', 10);
  const browser = await chromium.launch();
  const page = await browser.newPage({
    viewport: { width, height: 1000 },
    deviceScaleFactor: 2,   // 2x 便于放大看文字
  });

  const errors = [];
  page.on('requestfailed', (r) => {
    if (r.url().startsWith('http://127.0.0.1')) errors.push('REQ FAIL ' + r.url());
  });
  page.on('response', (r) => {
    if (r.status() >= 400 && r.url().startsWith('http://127.0.0.1'))
      errors.push('HTTP ' + r.status() + ' ' + r.url());
  });

  await page.goto(url, { waitUntil: 'load' });

  // 1) 滚动预热：逐屏下滚，逼所有 lazy 图进入视口
  const H = await page.evaluate(() => document.documentElement.scrollHeight);
  for (let y = 0; y < H; y += 700) {
    await page.evaluate((v) => window.scrollTo(0, v), y);
    await page.waitForTimeout(120);
  }
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  // 2) 等所有 img 解码完成（含 lazy）
  await page.waitForFunction(
    () => [...document.images].every((i) => i.complete),
    null, { timeout: 15000 }
  ).catch(() => {});
  await page.waitForTimeout(500);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(400);

  const broken = await page.evaluate(() =>
    [...document.images].filter((i) => !i.complete || i.naturalWidth === 0)
      .map((i) => ({ src: i.src, wk: i.getAttribute('width'), hk: i.getAttribute('height') }))
  );

  await page.screenshot({ path: out, fullPage: true });
  console.log('width', width, 'height', H, 'errors', errors.length,
              'brokenImgs', broken.length);
  if (errors.length) console.log(errors.join('\n'));
  if (broken.length) console.log('BROKEN: ' + JSON.stringify(broken, null, 1));
  await browser.close();
})();
