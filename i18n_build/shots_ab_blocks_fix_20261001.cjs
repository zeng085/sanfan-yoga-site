/** 补截线上版区块（用文本定位，避免 nth-of-type 失配） */
const { chromium } = require('playwright');
const path = require('path');
const BASE = 'http://127.0.0.1:8863';
const OUT = path.join(__dirname, 'reports');

(async () => {
  const browser = await chromium.launch();
  const jobs = [
    { key: 'live', url: '/pilates/_ab_live_ladder-barrel.html',
      blocks: [
        { n: '02-glance', text: 'Model range at a glance' },
        { n: '03-compared', text: 'models, compared' },
        { n: '04-custom', text: 'What can be customized' },
      ] },
    { key: 'new', url: '/pilates/pilates-ladder-barrel.html',
      blocks: [
        { n: '02-glance', text: 'models, one bench' },
      ] },
  ];
  for (const job of jobs) {
    for (const vp of [{ n: 'desktop', w: 1440, h: 900 }, { n: 'mobile', w: 390, h: 844 }]) {
      const ctx = await browser.newContext({
        viewport: { width: vp.w, height: vp.h },
        deviceScaleFactor: vp.n === 'mobile' ? 2 : 1,
        isMobile: vp.n === 'mobile', hasTouch: vp.n === 'mobile',
      });
      const p = await ctx.newPage();
      await p.goto(BASE + job.url, { waitUntil: 'load' });
      await p.evaluate(async () => {
        const s = window.innerHeight;
        for (let y = 0; y < document.body.scrollHeight; y += s) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 90)); }
        window.scrollTo(0, 0);
      });
      await p.waitForTimeout(700);
      for (const b of job.blocks) {
        const sec = p.locator('section').filter({ hasText: b.text }).first();
        const cnt = await sec.count();
        if (!cnt) { console.log(`  ✗ ${job.key} ${b.n} 未找到「${b.text}」`); continue; }
        const box = await sec.boundingBox();
        const f = path.join(OUT, `abblk_${job.key}_${b.n}_${vp.n}_20261001.png`);
        const MAXH = vp.n === 'mobile' ? 2600 : 2200;
        if (box.height <= MAXH) await sec.screenshot({ path: f });
        else {
          const n = Math.ceil(box.height / MAXH);
          for (let i = 0; i < n; i++) await p.screenshot({
            path: path.join(OUT, `abblk_${job.key}_${b.n}_${vp.n}_p${i+1}_20261001.png`),
            clip: { x: box.x, y: box.y + i*MAXH, width: box.width, height: Math.min(MAXH, box.height - i*MAXH) },
            fullPage: true,
          });
        }
        console.log(`  ✓ ${job.key} ${b.n} ${vp.n} h=${Math.round(box.height)}`);
      }
      await ctx.close();
    }
  }
  await browser.close();
})();
