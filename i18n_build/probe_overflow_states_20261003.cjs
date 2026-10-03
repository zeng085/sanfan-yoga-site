// 交叉核对：320px 溢出到底在哪个状态下出现（2026-10-03）
// 背景：WIG 浏览器审计报 de/index.html 320px 溢出 57px，而通用探针报 0px ——
//       两个测量结论冲突，必须交叉核对（铁律：100% 的统计先怀疑自己）。
// 假设：溢出发生在「导航抽屉打开」状态，关闭态测不到。
const { chromium } = require('playwright');
const argv = process.argv.slice(2);
const arg = (k, d) => { const i = argv.indexOf('--' + k); if (i >= 0) return argv[i + 1];
  const m = argv.find(a => a.startsWith('--' + k + '=')); return m ? m.slice(('--' + k + '=').length) : d; };
const BASE = arg('base', 'http://127.0.0.1:8877');
const TARGETS = [
  { name: 'de/index',      url: '/de/index.html' },
  { name: 'pilates/ref',   url: '/pilates/pilates-reformer.html' },
  { name: 'pilates/wunda', url: '/pilates/pilates-wunda-chair.html' },
];

(async () => {
  const browser = await chromium.launch();
  for (const t of TARGETS) {
    for (const vp of [[320, 568], [390, 844]]) {
      const page = await browser.newPage({ viewport: { width: vp[0], height: vp[1] } });
      await page.goto(BASE + t.url, { waitUntil: 'networkidle', timeout: 45000 }).catch(() => null);
      await page.waitForTimeout(600);

      const states = {};
      const measure = async (label) => {
        states[label] = await page.evaluate(() => {
          const de = document.documentElement;
          const over = de.scrollWidth - de.clientWidth;
          const bad = [];
          if (over > 0) {
            document.querySelectorAll('body *').forEach(el => {
              const r = el.getBoundingClientRect();
              if (r.width === 0 || r.height === 0) return;
              if (r.right > de.clientWidth + 1 && getComputedStyle(el).position !== 'fixed') {
                bad.push((el.tagName.toLowerCase() + (typeof el.className === 'string' && el.className ? '.' + el.className.trim().split(/\s+/).slice(0,2).join('.') : ''))
                  + ' right=' + Math.round(r.right) + ' w=' + Math.round(r.width) + ' «' + (el.textContent||'').trim().slice(0,28) + '»');
              }
            });
          }
          return { over, bad: bad.slice(0, 6) };
        });
      };
      await measure('关闭态');

      // 打开汉堡抽屉
      const opened = await page.evaluate(() => {
        const b = document.querySelector('.menu-toggle');
        if (!b) return false;
        b.click();
        return true;
      });
      await page.waitForTimeout(500);
      if (opened) await measure('抽屉打开');
      await page.keyboard.press('Escape').catch(() => {});
      await page.waitForTimeout(300);

      // 打开语言切换下拉
      const langOpened = await page.evaluate(() => {
        const b = document.querySelector('.lang-current');
        if (!b) return false;
        b.click();
        return true;
      });
      await page.waitForTimeout(400);
      if (langOpened) await measure('语言下拉');

      console.log(`\n■ ${t.name} @ ${vp[0]}px`);
      for (const [k, v] of Object.entries(states)) {
        console.log(`   ${k.padEnd(8)} 溢出 ${String(v.over).padStart(3)}px ${v.over > 0 ? '✗' : '✓'}`);
        v.bad.forEach(b => console.log(`        · ${b}`));
      }
      await page.close();
    }
  }
  await browser.close();
})();
