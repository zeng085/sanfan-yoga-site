/* 普拉提族页「画册型号区」截图 + 布局探针
   用法:
     NODE_PATH=<node_modules> node shot_pilates_catalog_20261001.cjs [--base=file:///abs/root] [--tag=name]
   产出:
     i18n_build/reports/pilates_catalog_shots_<tag>/<vp>-<section>.png
   同时打印：横向溢出、画册图实际渲染尺寸、卡片数、sticky 状态、表格滚动宽度
*/
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const arg = (k, d) => { const m = process.argv.find(s => s.startsWith('--' + k + '=')); return m ? m.split('=')[1] : d; };
const BASE = arg('base', 'file:///Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16');
const TAG = arg('tag', 'live');
const OUT = path.join(__dirname, 'reports', `pilates_catalog_shots_${TAG}`);
const URL = `${BASE}/pilates/pilates-ladder-barrel.html`;

const VPS = [
  { name: 'desktop-1440', w: 1440, h: 900 },
  { name: 'desktop-1440-zh', w: 1440, h: 900, zh: true },
  { name: 'tablet-820', w: 820, h: 1180 },
  { name: 'mobile-390', w: 390, h: 844 },
  { name: 'mobile-320', w: 320, h: 568 },
  { name: 'landscape-844x390', w: 844, h: 390 },
];

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  let problems = 0;

  for (const vp of VPS) {
    const ctx = await browser.newContext({ viewport: { width: vp.w, height: vp.h }, deviceScaleFactor: 1 });
    const page = await ctx.newPage();
    const errs = [];
    page.on('pageerror', e => errs.push(String(e).slice(0, 160)));
    page.on('requestfailed', r => errs.push(`${r.url().split('/').pop()} ${r.failure()?.errorText}`));

    await page.goto(URL, { waitUntil: 'load' });
    if (vp.zh) {
      // 语言按钮在折叠菜单 .lang-menu 里，必须先展开 .lang-current 才能点
      await page.click('.lang-current').catch(() => {});
      await page.waitForTimeout(200);
      await page.click('.lang-menu button[data-setlang="zh"]').catch(() => {});
      await page.waitForTimeout(300);
    }
    // 触发 lazy 图片：逐块滚进视口停留（快速划过时 Chromium 可能不发起懒加载）
    await page.evaluate(async () => {
      for (const u of document.querySelectorAll('.cat-unit')) {
        u.scrollIntoView({ block: 'center' });
        await new Promise(r => setTimeout(r, 450));
      }
      window.scrollTo(0, 0);
    });
    await page.evaluate(async () => {
      const imgs = [...document.querySelectorAll('img')];
      await Promise.all(imgs.map(i => (i.complete && i.naturalWidth) ? 0 : new Promise(r => {
        i.addEventListener('load', r, { once: true });
        i.addEventListener('error', r, { once: true });
        setTimeout(r, 8000);
      })));
    });
    await page.waitForTimeout(400);

    // --- 探针 ---
    const probe = await page.evaluate(() => {
      const out = {};
      out.docW = document.documentElement.scrollWidth;
      out.vw = window.innerWidth;
      out.overflow = document.documentElement.scrollWidth - window.innerWidth;
      const imgs = [...document.querySelectorAll('.cat-fig img')].map(i => ({
        src: i.getAttribute('src').split('/').pop(),
        nat: `${i.naturalWidth}x${i.naturalHeight}`,
        box: `${Math.round(i.getBoundingClientRect().width)}x${Math.round(i.getBoundingClientRect().height)}`,
        loaded: i.complete && i.naturalWidth > 0,
      }));
      out.catImgs = imgs;
      out.units = document.querySelectorAll('.cat-unit').length;
      out.cards = document.querySelectorAll('.model-card').length;
      const fig = document.querySelector('.cat-fig');
      out.figPosition = fig ? getComputedStyle(fig).position : null;
      out.htmlClass = document.documentElement.className;
      const fc = document.querySelector('.cat-fig figcaption');
      if (fc) {
        const zh = fc.querySelector('.lang-zh'), en = fc.querySelector('.lang-en');
        out.caption = {
          text: fc.innerText.replace(/\s+/g, ' ').trim().slice(0, 60),
          zhDisplay: zh ? getComputedStyle(zh).display : null,
          enDisplay: en ? getComputedStyle(en).display : null,
          link: !!fc.querySelector('a'),
        };
      }
      const wrap = document.querySelector('.pl-spec-wrap');
      out.specScrollW = wrap ? `${wrap.scrollWidth}/${wrap.clientWidth}` : null;
      const card = document.querySelector('.model-card');
      if (card) {
        const cs = getComputedStyle(card);
        out.cardStyle = { radius: cs.borderRadius, padding: cs.padding, bg: cs.backgroundColor };
      }
      // 溢出元素
      out.wide = [];
      document.querySelectorAll('body *').forEach(el => {
        const r = el.getBoundingClientRect();
        if (r.width > 0 && r.right > window.innerWidth + 1 && getComputedStyle(el).position !== 'fixed') {
          if (out.wide.length < 5) out.wide.push(`${el.tagName}.${(el.className || '').toString().split(' ')[0]} right=${Math.round(r.right)}`);
        }
      });
      return out;
    });

    console.log(`\n── ${vp.name} (${vp.w}×${vp.h}) ──`);
    console.log(`   横向溢出 ${probe.overflow}px   .cat-unit ${probe.units}  .model-card ${probe.cards}   fig.position=${probe.figPosition}`);
    console.log(`   html.class="${probe.htmlClass}"`);
    if (probe.caption) console.log(`   figcaption "${probe.caption.text}"  zh=${probe.caption.zhDisplay} en=${probe.caption.enDisplay} link=${probe.caption.link}`);
    console.log(`   规格表滚动 ${probe.specScrollW}`);
    probe.catImgs.forEach(i => console.log(`   图 ${i.src}  自然 ${i.nat}  渲染 ${i.box}  loaded=${i.loaded}`));
    if (probe.wide.length) { console.log('   ⚠️ 超出视口的元素:', probe.wide); }
    if (errs.length) { console.log('   ⚠️ 页面错误:', [...new Set(errs)].slice(0, 4)); }
    if (probe.overflow > 0 || probe.catImgs.some(i => !i.loaded)) problems++;

    // --- 截图 ---
    const shots = [
      ['hero', '.pl-hero'],
      ['specs', '#specs'],
      ['catalog', '#catalog'],
    ];
    for (const [name, sel] of shots) {
      const el = await page.$(sel);
      if (!el) continue;
      await el.scrollIntoViewIfNeeded();
      await page.waitForTimeout(250);
      await el.screenshot({ path: path.join(OUT, `${vp.name}-${name}.png`) }).catch(() => {});
    }
    await ctx.close();
  }

  await browser.close();
  console.log(`\n${problems === 0 ? '✅' : '❌'} 有问题的视口数: ${problems}`);
  console.log(`截图 -> ${OUT}`);
})();
