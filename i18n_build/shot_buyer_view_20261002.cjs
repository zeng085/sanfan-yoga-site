// 买家视角首屏截图（10-02）：5 张关键页首屏
const { chromium } = require('playwright');
const BASE = 'http://127.0.0.1:8872';
const OUT = 'i18n_build/reports/';
const SHOTS = [
  { name: 'buyer_home_desktop',  url: '/index.html',            vp: [1440, 900],  full: false },
  { name: 'buyer_home_mobile',   url: '/index.html',            vp: [390, 844],   full: false },
  { name: 'buyer_tpe_desktop',   url: '/tpe-yoga-mats.html',    vp: [1440, 900],  full: false },
  { name: 'buyer_reformer_desktop', url: '/pilates/pilates-reformer.html', vp: [1440, 900], full: false },
  { name: 'buyer_contact_desktop',  url: '/contact.html',       vp: [1440, 900],  full: false },
];
(async () => {
  const browser = await chromium.launch();
  for (const s of SHOTS) {
    const page = await browser.newPage({ viewport: { width: s.vp[0], height: s.vp[1] } });
    await page.goto(BASE + s.url, { waitUntil: 'networkidle', timeout: 30000 }).catch(() => {});
    await page.waitForTimeout(800);
    await page.screenshot({ path: OUT + s.name + '_20261002.png', fullPage: s.full });
    console.log('✓', s.name);
    await page.close();
  }
  await browser.close();
})();
