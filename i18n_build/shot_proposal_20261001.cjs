// 给提案预览页截全屏图，用于人工核对版式
// 用法：node shot_proposal_20261001.cjs <url> <out.png> [width]
const { chromium } = require('playwright');

(async () => {
  const url = process.argv[2];
  const out = process.argv[3];
  const width = parseInt(process.argv[4] || '1280', 10);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width, height: 900 }, deviceScaleFactor: 1.5 });
  const errors = [];
  page.on('requestfailed', (r) => {
    const u = r.url();
    if (u.startsWith('http://127.0.0.1')) errors.push('REQ FAIL ' + u);
  });
  page.on('response', (r) => {
    if (r.status() >= 400 && r.url().startsWith('http://127.0.0.1')) {
      errors.push('HTTP ' + r.status() + ' ' + r.url());
    }
  });
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForTimeout(600);
  const h = await page.evaluate(() => document.documentElement.scrollHeight);
  await page.screenshot({ path: out, fullPage: true });
  const broken = await page.evaluate(() =>
    [...document.images].filter((i) => !i.complete || i.naturalWidth === 0).map((i) => i.src));
  console.log('height', h, 'errors', errors.length, 'brokenImgs', broken.length);
  if (errors.length) console.log(errors.join('\n'));
  if (broken.length) console.log('BROKEN:\n' + broken.join('\n'));
  await browser.close();
})();
