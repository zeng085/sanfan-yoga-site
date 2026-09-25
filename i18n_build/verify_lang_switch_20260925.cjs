/**
 * A5 功能实测：<a data-setlang> → <button> 后，语言切换是否仍然可用
 * （main.js 的选择器是 `[data-setlang]`，标签无关；但必须实测，不靠读代码下结论）
 */
const { chromium } = require('playwright');

const CASES = [
  ['/blog/tpe-vs-pu.html', 'EN 文章页（A5 改动点）'],
  ['/index.html', 'EN 首页（对照，本来就是 button）'],
];

(async () => {
  const b = await chromium.launch();
  let fail = 0;
  for (const [path, label] of CASES) {
    const ctx = await b.newContext({ viewport: { width: 1280, height: 900 } });
    const page = await ctx.newPage();
    const errs = [];
    page.on('pageerror', e => errs.push(e.message));
    await page.goto('http://127.0.0.1:8851' + path, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(300);

    const urlBefore = page.url();
    const info = await page.evaluate(() => {
      const zh = document.querySelector('.lang-menu [data-setlang="zh"]');
      const en = document.querySelector('.lang-menu [data-setlang="en"]');
      return {
        zhTag: zh ? zh.tagName : null,
        enTag: en ? en.tagName : null,
        zhHasHref: zh ? zh.hasAttribute('href') : null,
        deHref: (document.querySelector('.lang-menu a[hreflang="de"]') || {}).getAttribute
          ? document.querySelector('.lang-menu a[hreflang="de"]').getAttribute('href') : null,
        lang0: document.documentElement.lang,
        curTxt0: (document.querySelector('.lang-cur-txt') || {}).textContent,
        enNavText: (document.querySelector('nav a[data-i18n="nav.products"]') || {}).textContent,
      };
    });

    // 打开语言下拉（部分页面菜单默认收起）
    await page.evaluate(() => {
      const sw = document.querySelector('.lang-current');
      if (sw) sw.click();
    });
    await page.waitForTimeout(150);
    await page.click('.lang-menu [data-setlang="zh"]', { force: true });
    await page.waitForTimeout(400);

    const after = await page.evaluate(() => ({
      url: location.href,
      lang: document.documentElement.lang,
      showZh: document.documentElement.classList.contains('show-zh'),
      showEn: document.documentElement.classList.contains('show-en'),
      ls: (() => { try { return localStorage.getItem('siteLang'); } catch (e) { return 'ERR'; } })(),
      cookie: document.cookie,
      curTxt: (document.querySelector('.lang-cur-txt') || {}).textContent,
      zhActive: (() => {
        const z = document.querySelector('.lang-menu [data-setlang="zh"]');
        return z ? z.classList.contains('active') : null;
      })(),
      navText: (document.querySelector('nav a[data-i18n="nav.products"]') || {}).textContent,
    }));

    console.log('── %s', label);
    console.log('   切换按钮标签: zh=%s en=%s | zh 带 href=%s | DE 链接=%s',
      info.zhTag, info.enTag, info.zhHasHref, info.deHref);
    console.log('   点击前: lang=%s 按钮文字=%s 导航文字=%s', info.lang0, info.curTxt0, info.enNavText);
    console.log('   点击后: lang=%s showZh=%s 按钮文字=%s 导航文字=%s',
      after.lang, after.showZh, after.curTxt, after.navText);
    console.log('   localStorage.siteLang=%s | zh 高亮=%s | URL 是否跳转=%s',
      after.ls, after.zhActive, after.url !== urlBefore ? '是(⚠️ 不应跳转)' : '否 ✓');

    const ok = after.lang === 'zh-CN' && after.showZh === true && after.ls === 'zh'
      && after.curTxt === '中文' && after.url === urlBefore && after.zhActive === true;
    if (!ok) { fail++; console.log('   ❌ 语言切换未按预期工作'); }
    else console.log('   ✅ 语言切换正常（同页切换、偏好已存、按钮文字与高亮同步）');
    if (errs.length) { fail++; console.log('   ❌ JS 错误:', errs.slice(0, 2).join(' | ')); }
    await ctx.close();
  }
  await b.close();
  process.exit(fail ? 1 : 0);
})();
