// 线上语言页实拍校验：0 破图、0 个 >=400 响应
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  let bad = new Set();
  page.on('response', r => { if (r.status() >= 400) bad.add(r.status() + ' ' + r.url()); });

  const paths = ['/de/', '/ja/', '/ko/', '/fr/', '/it/', '/es/', '/de/products.html', '/ja/tpe-yoga-mats.html'];

  for (const p of paths) {
    bad = new Set();
    await page.goto('https://fjsanfan.com' + p, { waitUntil: 'networkidle', timeout: 60000 });
    await page.waitForTimeout(1500);
    const broken = await page.evaluate(() => Array.from(document.images)
      .filter(i => i.complete && i.naturalWidth === 0).map(i => i.currentSrc || i.src));
    const title = await page.title();
    console.log(p.padEnd(24) + '破图 ' + broken.length + '  >=400 ' + bad.size + '  | ' + title.slice(0, 40));
    [...bad].slice(0, 4).forEach(x => console.log('        ' + x));
  }
  await browser.close();
})();
