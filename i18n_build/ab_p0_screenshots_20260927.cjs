/* P0 修复的视觉回归 A/B：用路由拦截把 styles.css 换成 HEAD 版做「改前」，
   不修改任何站点文件。输出 /tmp/p0ab/*.png */
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = 'file:///Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16';
const HEAD_CSS = fs.readFileSync('/tmp/p0ab/styles_head.css', 'utf8');
const OUT = '/tmp/p0ab';

// [标签, 页面, 宽, 高, 动作, 裁剪区域(null=全屏)]
const SCENES = [
  ['A-header', 'index.html', 390, 844, null, { x: 0, y: 0, width: 390, height: 90 }],
  ['B-drawer', 'index.html', 390, 844, 'burger', { x: 0, y: 0, width: 390, height: 620 }],
  ['C-landscape', 'index.html', 844, 390, 'burger', null],
  ['E-bottom', 'index.html', 844, 390, 'burger-scroll', null],
  ['D-form', 'contact.html', 390, 844, 'form', null],
];

(async () => {
  const b = await chromium.launch();
  for (const [tag, page, w, h, act, clip] of SCENES) {
    for (const ver of ['before', 'after']) {
      const ctx = await b.newContext({ viewport: { width: w, height: h }, isMobile: w < 900, hasTouch: w < 900, deviceScaleFactor: 1 });
      const p = await ctx.newPage();
      await p.route('**/*', r => /google-analytics|googletagmanager|clarity|facebook|doubleclick/.test(r.request().url()) ? r.abort() : r.continue());
      if (ver === 'before') {
        // 拦截 CSS，喂 HEAD 版（相对路径不变，页面其余部分完全一致）
        await p.route('**/assets/css/styles.css*', r => r.fulfill({ contentType: 'text/css', body: HEAD_CSS }));
      }
      await p.goto(`${BASE}/${page}`, { waitUntil: 'domcontentloaded' });
      await p.waitForTimeout(500);
      if (act === 'burger' || act === 'burger-scroll') { await (await p.$('.menu-toggle')).click(); await p.waitForTimeout(400); }
      if (act === 'burger-scroll') { await p.evaluate(() => { document.querySelector('.nav-links').scrollTop = 9999; }); await p.waitForTimeout(200); }
      if (act === 'form') {
        await p.evaluate(() => document.querySelector('.field input, .field input')?.scrollIntoView({ block: 'center' }));
        await p.waitForTimeout(300);
      }
      const file = `${OUT}/${tag}_${ver}.png`;
      await p.screenshot({ path: file, clip: clip || undefined });
      console.log(`${file}  ${w}x${h}  ${act || '顶部'}`);
      await ctx.close();
    }
  }
  await b.close();
})().catch(e => { console.log('FAIL', e.message.slice(0, 300)); process.exit(1); });
