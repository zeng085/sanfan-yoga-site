/**
 * shot_i18n.cjs — 多语言页实拍验收
 *
 * 用法:
 *   NODE_PATH=<node_modules> node i18n_build/shot_i18n.cjs
 *   BASE=http://127.0.0.1:8848 可覆盖（默认即此）
 *
 * 除截图外，还会收集 status>=400 的响应与 requestfailed，
 * 用来验证语言页的 assets/js/main.js 是否真的 200（历史上这里曾 404）。
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE = process.env.BASE || 'http://127.0.0.1:8848';
const OUT = 'outputs/i18n-preview';
fs.mkdirSync(OUT, { recursive: true });

const SHOTS = [
  { url: '/de/tpe-yoga-mats.html',          name: 'de-cat-tpe-top',    w: 1280, h: 900,  full: false },
  { url: '/de/tpe-yoga-mats.html',          name: 'de-cat-tpe-full',   w: 1280, h: 900,  full: true  },
  { url: '/de/products/massage-stick.html', name: 'de-prod-massage',   w: 1280, h: 900,  full: true  },
  { url: '/ja/tpe-yoga-mats.html',          name: 'ja-cat-tpe-top',    w: 1280, h: 900,  full: false },
  { url: '/de/tpe-yoga-mats.html',          name: 'de-cat-tpe-mobile', w: 390,  h: 844,  full: false },
];

(async () => {
  const browser = await chromium.launch();
  const bad = [];
  for (const s of SHOTS) {
    const ctx = await browser.newContext({ viewport: { width: s.w, height: s.h } });
    const page = await ctx.newPage();
    page.on('response', r => { if (r.status() >= 400) bad.push(`${r.status()}  ${r.url()}`); });
    page.on('requestfailed', r => bad.push(`FAIL  ${r.url()}`));
    try {
      await page.goto(BASE + s.url, { waitUntil: 'networkidle', timeout: 60000 });
      const file = path.join(OUT, s.name + '.png');
      await page.screenshot({ path: file, fullPage: !!s.full });
      const info = await page.evaluate(() => ({
        lang: document.documentElement.lang,
        title: document.title.slice(0, 60),
        // 语言切换器由 fix_site.py 注入，验证它还在
        switcher: !!document.querySelector('.lang-switch, .lang-btn, [data-lang]'),
        imgs: [...document.images].filter(i => !i.complete || i.naturalWidth === 0).length,
      }));
      console.log(`  ${s.name.padEnd(20)} lang=${info.lang} 破图=${info.imgs} 切换器=${info.switcher}`);
      console.log(`      ${file}`);
    } catch (e) {
      console.log(`  ${s.name}: 失败 ${e.message}`);
    }
    await ctx.close();
  }
  await browser.close();
  console.log('\n=== 失败请求（status>=400）===');
  console.log(bad.length ? [...new Set(bad)].join('\n') : '  无 ✅');
})();
