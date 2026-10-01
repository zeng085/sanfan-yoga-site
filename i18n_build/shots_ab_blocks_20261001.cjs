/**
 * 逐区块截图：线上版 vs 新版（消费者视角逐块对比）
 * 用法：先起 http.server 8862，再跑本脚本
 */
const { chromium } = require('playwright');
const path = require('path');

const BASE = 'http://127.0.0.1:8862';
const OUT = path.join(__dirname, 'reports');

const JOBS = [
  { key: 'live', url: '/pilates/_ab_live_ladder-barrel.html',
    blocks: [
      { n: '01-lead',       sel: 'body > main > section:nth-of-type(1), section.section:nth-of-type(1)' },
      { n: '02-models',     sel: 'section.pl-soft:nth-of-type(1)' },
      { n: '03-rest',       sel: 'section.section:nth-of-type(3)' },
    ] },
  { key: 'new', url: '/pilates/pilates-ladder-barrel.html',
    blocks: [
      { n: '01-lead',       sel: 'body > main > section:nth-of-type(1), section.section:nth-of-type(1)' },
      { n: '02-specs',      sel: '#specs' },
      { n: '03-catalog',    sel: '#catalog' },
    ] },
];

(async () => {
  const browser = await chromium.launch();
  for (const job of JOBS) {
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
        const parts = b.sel.split(', ');
        let el = null;
        for (const s of parts) { el = await p.$(s.trim()); if (el) break; }
        if (!el) { console.log(`  ✗ ${job.key} ${b.n} 未定位（${b.sel}）`); continue; }
        const box = await el.boundingBox();
        if (!box || box.height < 20) { console.log(`  ✗ ${job.key} ${b.n} 高度异常 ${box && box.height}`); continue; }
        const file = path.join(OUT, `abblk_${job.key}_${b.n}_${vp.n}_20261001.png`);
        // 超高的区块分片截，避免缩略到看不清
        const MAXH = vp.n === 'mobile' ? 2600 : 2200;
        if (box.height <= MAXH) {
          await el.screenshot({ path: file });
        } else {
          const n = Math.ceil(box.height / MAXH);
          for (let i = 0; i < n; i++) {
            await p.screenshot({
              path: path.join(OUT, `abblk_${job.key}_${b.n}_${vp.n}_p${i + 1}_20261001.png`),
              clip: { x: box.x, y: box.y + i * MAXH, width: box.width, height: Math.min(MAXH, box.height - i * MAXH) },
              fullPage: true,
            });
          }
        }
        console.log(`  ✓ ${job.key} ${b.n} ${vp.n}  h=${Math.round(box.height)}px`);
      }
      await ctx.close();
    }
  }
  await browser.close();
  console.log('完成');
})();
