// 内页 hero 裁剪复核（10-02 推送前）：确认 220%/320% 裁剪后不露海报中文
const { chromium } = require('playwright');
const BASE = 'http://127.0.0.1:8872';
const OUT = 'i18n_build/reports/';
const SHOTS = [
  { name: 'herochk_products_desktop', url: '/tpe-yoga-mats.html',                vp: [1440, 900] },
  { name: 'herochk_de_index_desktop', url: '/de/index.html',                     vp: [1440, 900] },
  { name: 'herochk_de_products_mobile', url: '/de/products/yoga-mats.html',      vp: [390, 844] },
  { name: 'herochk_pilates_mobile', url: '/pilates/pilates-reformer.html',       vp: [390, 844] },
];
(async () => {
  const browser = await chromium.launch();
  for (const s of SHOTS) {
    const page = await browser.newPage({ viewport: { width: s.vp[0], height: s.vp[1] } });
    const resp = await page.goto(BASE + s.url, { waitUntil: 'networkidle', timeout: 30000 }).catch(() => null);
    await page.waitForTimeout(700);
    const hero = await page.$('.hero');
    if (hero) {
      // hero 区域单独截（含 ::after 背景）
      await hero.screenshot({ path: OUT + s.name + '_20261002.png' });
    } else {
      await page.screenshot({ path: OUT + s.name + '_20261002.png' });
    }
    console.log('✓', s.name, '| HTTP', resp ? resp.status() : 'ERR', '| hero:', !!hero);
    await page.close();
  }
  await browser.close();
})();
