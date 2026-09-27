/* P1 修复的视觉 A/B：路由拦截把 styles.css 换成 HEAD 版做「改前」，不修改任何站点文件。
   输出 /tmp/p1ab/*.png */
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = 'file:///Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16';
const HEAD_CSS = fs.readFileSync('/tmp/p1ab/styles_head.css', 'utf8');
const OUT = '/tmp/p1ab';

// [标签, 页面, hash, 宽, 高, 动作, 裁剪区域]
const SCENES = [
  ['F-field', 'contact.html', '', 390, 844, 'field-focus', { x: 0, y: 150, width: 390, height: 330 }],
  ['G-search', 'index.html', '', 390, 844, 'search-focus', null],
  ['H-anchor', 'pilates/index.html', '#lines', 1280, 800, 'anchor', { x: 0, y: 0, width: 1280, height: 300 }],
  ['I-tab', 'index.html', '', 1280, 800, 'tab3', { x: 0, y: 0, width: 900, height: 120 }],
];

(async () => {
  const b = await chromium.launch();
  for (const [tag, page, hash, w, h, act, clip] of SCENES) {
    for (const ver of ['before', 'after']) {
      const ctx = await b.newContext({ viewport: { width: w, height: h }, isMobile: w < 900, hasTouch: w < 900, deviceScaleFactor: 1 });
      const p = await ctx.newPage();
      await p.route('**/*', r => /google-analytics|googletagmanager|clarity|facebook|doubleclick/.test(r.request().url()) ? r.abort() : r.continue());
      if (ver === 'before') {
        await p.route('**/assets/css/styles.css*', r => r.fulfill({ contentType: 'text/css', body: HEAD_CSS }));
      }
      await p.goto(`${BASE}/${page}${hash}`, { waitUntil: 'domcontentloaded' });
      await p.waitForTimeout(400);

      if (act === 'anchor') {
        // 等平滑滚动停稳（否则量到的是「还在滚」的中间态）
        await p.evaluate(async () => {
          let last = -1, same = 0; const t0 = Date.now();
          while (Date.now() - t0 < 6000) {
            const y = Math.round(window.scrollY);
            if (y === last) { if (++same >= 6) break; } else { same = 0; last = y; }
            await new Promise(r => requestAnimationFrame(r));
          }
        });
        await p.waitForTimeout(200);
      }
      if (act === 'field-focus') {
        // 文本框永远匹配 :focus-visible（已实测），故 focus() 与键盘 Tab 等效
        await p.evaluate(() => { const el = document.querySelector('.field input'); el.scrollIntoView({ block: 'center' }); });
        await p.waitForTimeout(250);
        await p.evaluate(() => document.querySelector('.field input').focus());
        await p.waitForTimeout(200);
      }
      if (act === 'search-focus') {
        await p.evaluate(() => document.querySelector('.sr-btn').click());
        await p.waitForTimeout(500);
        await p.evaluate(() => document.querySelector('.sr-input').focus());
        await p.waitForTimeout(200);
      }
      if (act === 'tab3') {
        // 真实键盘 Tab：走 nav 里的链接/按钮，验证键盘路径确实出现焦点环
        await p.keyboard.press('Tab'); await p.waitForTimeout(120);
        await p.keyboard.press('Tab'); await p.waitForTimeout(120);
        await p.keyboard.press('Tab'); await p.waitForTimeout(250);
      }

      const file = `${OUT}/${tag}_${ver}.png`;
      await p.screenshot({ path: file, clip: clip || undefined });
      console.log(`${file}  ${w}x${h}  ${act}`);
      await ctx.close();
    }
  }
  await b.close();
})().catch(e => { console.log('FAIL', e.message.slice(0, 300)); process.exit(1); });
