// 移动端（390×844）场景检查：裁切溢出 / 触控目标 / 图片 / 搜索浮层 / 4xx / 极小字号
//
// 判定口径（踩过坑，别改回去）：
//  1) 溢出 ≠ 缺陷。html/body 是 overflow-x:clip，元素超出视口会被**静默裁掉**。
//     所以只有「没有横向可滚动祖先」的溢出才算缺陷；表格在 .mat-wrap/.kit-wrap
//     里 overflow-x:auto 是可以横滑的，属正常设计。
//  2) 搜索浮层在窄屏不能点 .sr-btn（≤640px 被 display:none，改放在汉堡菜单里），
//     必须走「汉堡 → 搜索产品」入口，否则 boundingBox() 返回 0 会误报溢出。
//  3) 触控目标 <40px 分两类：header/nav/CTA 等关键控件算缺陷；正文里的行内链接
//     （面包屑、页脚列表项）只提示，不算失败。
// 用法：BASE=http://127.0.0.1:8123 node i18n_build/check_mobile.cjs
const { chromium } = require('playwright');

const BASE = process.env.BASE || 'http://127.0.0.1:8123';
const PAGES = [
  '', 'products.html', 'tpe-yoga-mats.html', 'products/lilac-tpe-yoga-mat.html',
  'materials.html', 'applications/yoga-pilates-studios.html', 'applications/index.html',
  'de/', 'de/products.html', 'de/products/ab-wheel.html', 'de/materials.html',
  'ja/', 'ja/products/ym1.html',
  'ko/', 'fr/', 'it/', 'es/',
  'de/applications/index.html', 'ja/tpe-yoga-mats.html',
];

(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({
    viewport: { width: 390, height: 844 },
    isMobile: true, hasTouch: true, deviceScaleFactor: 2,
  });
  let fail = 0;
  for (const pg of PAGES) {
    const p = await ctx.newPage();
    const errs = [];
    p.on('response', r => { if (r.status() >= 400) errs.push(r.status() + ' ' + r.url().split('/').pop()); });
    p.on('pageerror', e => errs.push('JS ' + e.message.slice(0, 60)));
    await p.goto(BASE + '/' + pg, { waitUntil: 'load', timeout: 45000 });
    await p.waitForTimeout(700);

    const r = await p.evaluate(() => {
      const de = document.documentElement;
      const vw = de.clientWidth;
      const scrollableAncestor = el => {
        let a = el.parentElement;
        while (a && a !== document.body) {
          const ox = getComputedStyle(a).overflowX;
          if (ox === 'auto' || ox === 'scroll') return true;
          a = a.parentElement;
        }
        return false;
      };
      // 1 被裁切的溢出（无横向滚动祖先）
      const clipped = [], scrollable = [];
      document.querySelectorAll('body *').forEach(el => {
        const b = el.getBoundingClientRect();
        if (b.width > 0 && b.right > vw + 2 && getComputedStyle(el).position !== 'fixed') {
          const tag = (el.tagName + '.' + (el.className || '').toString().split(' ')[0]).slice(0, 34)
                    + '@' + Math.round(b.right);
          (scrollableAncestor(el) ? scrollable : clipped).push(tag);
        }
      });
      // 2 触控目标：关键控件 vs 正文内链
      const KEY = '.nav-brand,.menu-toggle,.lang-current,.nav-actions a,.nav-actions button,.btn,.sr-btn,.nav-search-item,.nav-links a';
      const keySmall = [], inlineSmall = [];
      document.querySelectorAll('a,button').forEach(el => {
        const b = el.getBoundingClientRect();
        if (!(b.width > 0 && b.height > 0) || b.height >= 40) return;
        if (!(el.textContent || '').trim()) return;
        const label = ((el.textContent || '').trim().slice(0, 14)) + ':' + Math.round(b.height);
        if (el.matches(KEY)) keySmall.push(label); else inlineSmall.push(label);
      });
      let imgOver = 0;
      document.querySelectorAll('img').forEach(im => {
        if (im.getBoundingClientRect().width > vw + 2) imgOver++;
      });
      return {
        scrollW: de.scrollWidth, clientW: vw,
        clipped: clipped.slice(0, 4), clippedN: clipped.length, scrollN: scrollable.length,
        keySmall: keySmall.slice(0, 4), keyN: keySmall.length, inlineN: inlineSmall.length,
        imgOver,
        hasViewport: !!document.querySelector('meta[name="viewport"]'),
        fontSmall: [...document.querySelectorAll('p,li,td,th')]
          .filter(e => parseFloat(getComputedStyle(e).fontSize) < 11).length,
      };
    });

    // 3 搜索浮层：窄屏走「汉堡 → 搜索产品」
    let searchOk = null;
    const srBtn = p.locator('.sr-btn');
    if (await srBtn.count()) {
      if (await srBtn.first().isVisible().catch(() => false)) {
        await srBtn.first().click().catch(() => {});
      } else {
        await p.locator('.menu-toggle').first().click().catch(() => {});
        await p.waitForTimeout(250);
        await p.locator('.nav-search-item').first().click().catch(() => {});
      }
      await p.waitForTimeout(500);
      const box = await p.locator('.sr-box').boundingBox().catch(() => null);
      searchOk = box ? (box.width <= 390 + 1 && box.x >= -1 && box.width > 200) : false;
      await p.keyboard.press('Escape').catch(() => {});
    }

    const bad = r.scrollW > r.clientW + 2 || r.clippedN > 0 || r.imgOver > 0
             || searchOk === false || !r.hasViewport || r.keyN > 0 || r.fontSmall > 0;
    if (bad) fail++;
    console.log(
      (bad ? '❌' : '✅') + ' /' + (pg || '(en)') +
      '  滚动宽 ' + r.scrollW + '/' + r.clientW +
      '  裁切 ' + r.clippedN + '  可横滑 ' + r.scrollN +
      '  关键控件<40 ' + r.keyN + '  正文内链<40 ' + r.inlineN +
      '  图溢出 ' + r.imgOver + '  极小字号 ' + r.fontSmall +
      '  搜索浮层 ' + (searchOk === null ? '—' : (searchOk ? 'OK' : '异常')) +
      '  4xx/JS ' + errs.length
    );
    if (r.clipped.length) console.log('      裁切: ' + r.clipped.join(' | '));
    if (r.keySmall.length) console.log('      关键控件: ' + r.keySmall.join(' | '));
    if (errs.length) console.log('      ⚠ ' + errs.slice(0, 3).join(' | '));
    await p.close();
  }
  await b.close();
  console.log(fail === 0 ? '\n✅ 移动端全部通过' : '\n❌ 移动端问题页面 ' + fail + ' 个');
  process.exit(fail ? 1 : 0);
})();
