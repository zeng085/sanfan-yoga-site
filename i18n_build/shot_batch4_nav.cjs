// 第四批实拍：新页面线上健康度 + 导航栏结构视觉验证
// 用法：NODE_PATH=<workspace>/node_modules node i18n_build/shot_batch4_nav.cjs
// 产出：outputs/i18n-batch1/b4-*-nav.png（该目录已在 .gitignore 内）
const { chromium } = require('playwright');

const OUT = 'outputs/i18n-batch1';
const PATHS = ['/de/materials.html',
               '/de/applications/yoga-pilates-studios.html',
               '/ja/applications/index.html',
               '/es/materials.html',
               '/de/products/lilac-tpe-yoga-mat.html',
               '/de/'];

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  let bad = new Set();
  page.on('response', r => { if (r.status() >= 400) bad.add(r.status() + ' ' + r.url()); });

  for (const p of PATHS) {
    bad = new Set();
    await page.goto('https://fjsanfan.com' + p, { waitUntil: 'networkidle', timeout: 60000 });
    await page.waitForTimeout(1200);

    const broken = await page.evaluate(() => Array.from(document.images)
      .filter(i => i.complete && i.naturalWidth === 0).map(i => i.currentSrc || i.src));

    // 导航结构：切换器与 "Get a Quote" 是否同一行、按钮是否还在 nav-actions 内
    const nav = await page.evaluate(() => {
      const sw = document.querySelector('.lang-switch');
      const na = document.querySelector('.nav-actions');
      const btn = document.querySelector('.nav-actions .btn-primary');
      if (!sw || !na || !btn) return null;
      const a = sw.getBoundingClientRect(), b = btn.getBoundingClientRect();
      const n = na.getBoundingClientRect();
      return {
        sameRow: Math.abs((a.top + a.height / 2) - (b.top + b.height / 2)) < 12,
        escaped: !(b.top >= n.top - 2 && b.bottom <= n.bottom + 2),
      };
    });

    const name = p.replace(/\//g, '_').replace(/^_/, '');
    await page.screenshot({ path: `${OUT}/b4-${name}-nav.png`,
                            clip: { x: 0, y: 0, width: 1440, height: 120 } });

    console.log(p.padEnd(44)
      + '破图 ' + broken.length
      + '  >=400 ' + bad.size
      + '  同排 ' + (nav ? (nav.sameRow ? '✅' : '❌') : '?')
      + '  溢出容器 ' + (nav ? (nav.escaped ? '❌' : '✅无') : '?'));
    [...bad].slice(0, 5).forEach(x => console.log('        ' + x));
    broken.slice(0, 3).forEach(x => console.log('        破图: ' + x));
  }
  await browser.close();
})();
