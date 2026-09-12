// 实拍第一批多语言页：门面页（index / products）+ 分类页 + 产品页 + blog
// 同时收集页面内 404 请求与破图，作为验收证据。
const { chromium } = require('playwright');
const fs = require('fs');

const BASE = process.env.BASE || 'http://127.0.0.1:8848';
const OUT = 'outputs/i18n-batch1';

const SHOTS = [
  ['de-index-top',        '/de/',                         { y: 0 }],
  ['de-index-apps',       '/de/',                         { sel: '#applications' }],
  ['de-products-grid',    '/de/products.html',            { sel: '.cat-grid' }],
  ['de-cat-tpe-top',      '/de/tpe-yoga-mats.html',       { y: 0 }],
  ['de-cat-tpe-cards',    '/de/tpe-yoga-mats.html',       { sel: '.prod-grid' }],
  ['ja-products-grid',    '/ja/products.html',            { sel: '.cat-grid' }],
  ['ja-cat-props-cards',  '/ja/yoga-props-accessories.html', { sel: '.prod-grid' }],
  ['ko-index-apps',       '/ko/',                         { sel: '#applications' }],
  ['fr-cat-suede-cards',  '/fr/suede-cork-yoga-mats.html', { sel: '.prod-grid' }],
  ['es-blog-list',        '/es/blog.html',                { y: 0 }],
  ['it-index-top',        '/it/',                         { y: 0 }],
];

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();

  const bad = [];
  page.on('response', r => {
    if (r.status() >= 400 && r.url().startsWith(BASE)) bad.push(r.status() + ' ' + r.url());
  });

  for (const [name, path, opt] of SHOTS) {
    await page.goto(BASE + path, { waitUntil: 'networkidle', timeout: 45000 });
    await page.waitForTimeout(600);
    if (opt.sel) {
      try {
        await page.locator(opt.sel).first().scrollIntoViewIfNeeded();
        await page.waitForTimeout(500);
      } catch (e) { /* 元素不存在时仍截图，便于发现问题 */ }
    } else if (opt.y) {
      await page.evaluate(y => window.scrollTo(0, y), opt.y);
      await page.waitForTimeout(300);
    }
    await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: false });

    // 破图统计
    const broken = await page.evaluate(() => Array.from(document.images)
      .filter(i => i.complete && i.naturalWidth === 0).map(i => i.currentSrc || i.src));
    console.log(`${name.padEnd(22)} 破图 ${broken.length}${broken.length ? ' -> ' + broken.slice(0, 3).join(', ') : ''}`);
  }

  console.log('\n本地 4xx/5xx 请求：' + (bad.length ? '\n  ' + [...new Set(bad)].slice(0, 12).join('\n  ') : '无 ✅'));
  await browser.close();
})();
