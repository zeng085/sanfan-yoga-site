const { chromium } = require('playwright');
const BASE = 'http://127.0.0.1:8851';
const WA = 'https://wa.me/8615959029082';
let bad = 0;
const ok = (c, m) => { if (!c) bad++; console.log(`  ${c ? '✓' : '✗'} ${m}`); };

// 移动菜单「搜索产品」项解析后的绝对路径
const NAV_CASES = [
  { url: '/index.html',             expect: '/products.html' },
  { url: '/products.html',          expect: '/products.html' },
  { url: '/de/index.html',          expect: '/de/products.html' },
  { url: '/ja/products.html',       expect: '/ja/products.html' },
  { url: '/de/products/ym1.html',   expect: '/de/products.html' },  // 深层页 ROOT='../'
  { url: '/es/blog/tpe-vs-pu.html', expect: '/es/products.html' },  // 深层页 ROOT='../../'
  { url: '/pilates/index.html',     expect: '/products.html' },     // 子目录 ROOT='../'
  { url: '/ko/products/ym1.html',   expect: '/ko/products.html' },
];

(async () => {
  const browser = await chromium.launch();

  // ══ 1. product.html 的空 href 修复：禁用 JS 时静态兜底必须可用 ══
  console.log('===== 1. product.html · 禁用 JS（爬虫 / 脚本被拦 / 白屏兜底）=====');
  {
    const ctx = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 1440, height: 1000 } });
    const page = await ctx.newPage();
    await page.goto(BASE + '/product.html?id=ym1', { waitUntil: 'domcontentloaded' });
    const href = await page.getAttribute('#pd-wa', 'href');
    const txt = (await page.textContent('#pd-wa') || '').trim();
    console.log(`  #pd-wa href = ${href.slice(0, 96)}…`);
    ok(href && href.startsWith(WA), 'href 指向 wa.me 真实号码');
    ok(href && href.includes('text='), 'href 带 prefill 文案');
    ok(href !== '#' && href !== '', '不再是 # / 空值');
    ok(txt.length > 0, `按钮文案可见（${txt}）`);
    await ctx.close();
  }

  // ══ 2. JS 正常：动态页应重定向到静态可爬产品页 ══
  console.log('\n===== 2. product.html · JS 正常（重定向行为不变）=====');
  let landed = '';
  {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    const page = await ctx.newPage();
    const errs = [];
    page.on('pageerror', e => errs.push(String(e)));
    await page.goto(BASE + '/product.html?id=ym1', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(900);
    landed = new URL(page.url()).pathname;
    console.log(`  落点 = ${landed}`);
    ok(landed.includes('/products/ym1.html'), '已重定向到 products/ym1.html');
    ok(errs.length === 0, `无 JS 报错（${errs.length}）`);
    await ctx.close();
  }

  // ══ 3. 静态产品页（用户实际看到的那个）无空 href，按钮指向 wa.me ══
  console.log('\n===== 3. 静态产品页 · 无空 href 且按钮指向 wa.me =====');
  for (const [dir, label] of [['', 'EN'], ['de/', 'de'], ['ja/', 'ja'], ['es/', 'es']]) {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    const page = await ctx.newPage();
    await page.goto(BASE + '/' + dir + 'products/ym1.html', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(400);
    const emptyHash = await page.locator('a[href="#"]').count();
    const wa = await page.$$eval('a[href*="wa.me"]', as => as.filter(a => a.offsetParent !== null).map(a => a.getAttribute('href')));
    console.log(`  ${label}: 可见 wa 链接 ${wa.length} 个 · 空 href ${emptyHash} 个`);
    ok(emptyHash === 0, `${label} 无 href="#"`);
    ok(wa.length > 0 && wa.every(h => h.startsWith(WA)), `${label} wa 链接均指向真实号码`);
    await ctx.close();
  }

  // ══ 4. 移动菜单「搜索产品」项：href 必须是真实产品总览（本轮 JS 修复）══
  console.log('\n===== 4. 移动菜单「搜索产品」项 · 路径解析（390px）=====');
  for (const c of NAV_CASES) {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await ctx.newPage();
    const errs = [];
    page.on('pageerror', e => errs.push(String(e)));
    await page.goto(BASE + c.url, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(700);
    const r = await page.evaluate(() => {
      const a = document.querySelector('.nav-search-item');
      return a ? { attr: a.getAttribute('href'), abs: new URL(a.href).pathname, vis: a.offsetParent !== null } : null;
    });
    if (!r) { bad++; console.log(`  ✗ ${c.url} 找不到 .nav-search-item`); await ctx.close(); continue; }
    const good = r.attr !== '#' && r.abs === c.expect;
    if (!good) bad++;
    console.log(`  ${good ? '✓' : '✗'} ${c.url.padEnd(26)} → ${r.abs.padEnd(20)} (期望 ${c.expect}) 可见=${r.vis}`);
    if (errs.length) { bad++; console.log(`      ✗ JS 报错: ${errs[0].slice(0, 110)}`); }
    await ctx.close();
  }

  // ══ 5. 断点与交互行为不变 ══
  console.log('\n===== 5. 断点与交互（行为不变）=====');
  {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    const page = await ctx.newPage();
    await page.goto(BASE + '/index.html', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(600);
    const r = await page.evaluate(() => {
      const a = document.querySelector('.nav-search-item'), b = document.querySelector('.sr-btn');
      return { itemHidden: a ? a.offsetParent === null : null, btnVis: b ? b.offsetParent !== null : null };
    });
    console.log(`  1440px: 移动菜单项隐藏=${r.itemHidden} · 头部搜索图标可见=${r.btnVis}`);
    ok(r.itemHidden === true, '1440px 移动菜单项隐藏（1279px 断点生效）');
    ok(r.btnVis === true, '1440px 头部搜索图标可见');
    await ctx.close();
  }
  {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await ctx.newPage();
    await page.goto(BASE + '/index.html', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(700);
    await page.evaluate(() => { const n = document.querySelector('.nav-links'); if (n) n.classList.add('open'); });
    await page.waitForTimeout(200);
    const before = page.url();
    await page.click('.nav-search-item', { force: true });
    await page.waitForTimeout(500);
    const after = page.url();
    const srVisible = await page.evaluate(() => {
      const cands = ['.sr-modal', '.sr-overlay', '.sr-wrap', '.sr'];
      for (const s of cands) { const e = document.querySelector(s); if (e && getComputedStyle(e).display !== 'none') return true; }
      const inp = document.querySelector('.sr-input');
      return !!inp && inp.offsetParent !== null;
    });
    console.log(`  点击后 URL: ${before === after ? '未跳转（preventDefault 生效）' : '(跳转了！)'} · 搜索层可见=${srVisible}`);
    ok(before === after, '点击未触发跳转（preventDefault 行为保持）');
    ok(srVisible, '点击打开了搜索层');
    await ctx.close();
  }

  await browser.close();
  console.log(`\n${bad === 0 ? '全部通过' : bad + ' 项异常'}`);
  process.exit(bad === 0 ? 0 : 1);
})();
