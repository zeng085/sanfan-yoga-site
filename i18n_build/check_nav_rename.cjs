/**
 * check_nav_rename.cjs — 验导航改名：Products → Yoga Mats & Gear、Pilates → Pilates Equipment
 *
 * 断言：
 *   1. 一级导航文案正确（EN / 中文切换态 / DE / JA / KO）
 *   2. footer 栏目名同步改对
 *   3. ⭐ 文案变长后导航不溢出：.nav-links.scrollWidth ≤ clientWidth，页面无横向滚动
 *   4. 中文态切换后导航项正确变为「瑜伽垫与健身」+「普拉提器械」
 *   5. 无控制台错误、无 4xx（排除 GA 噪音）
 *
 * 坑（沿用站内既有经验）：
 *   · waitUntil:'networkidle' 在本机永久超时（GA 请求挂住）→ 用 domcontentloaded + 拦 GA
 *   · 中文态必须写 localStorage.siteLang='zh' 后 reload，直接加 class 不会触发 applyLang
 *
 * 用法:
 *   NODE_PATH=/Users/mac-zlg/.workbuddy/binaries/node/workspace/node_modules \
 *     /Users/mac-zlg/.workbuddy/binaries/node/versions/22.12.0/bin/node i18n_build/check_nav_rename.cjs
 */
const { chromium } = require('playwright');

const BASE = process.env.BASE || 'http://127.0.0.1:8848';

const EN_PROD = 'Yoga Mats & Gear';
const EN_PIL = 'Pilates Equipment';

const PAGES = [
  { url: '/',                                     name: 'EN 首页',        lang: 'en' },
  { url: '/products.html',                        name: 'EN 产品列表',    lang: 'en' },
  { url: '/pilates/',                             name: 'EN 普拉提首页',  lang: 'en' },
  { url: '/pilates/pilates-reformer.html',        name: 'EN 器械族页',    lang: 'en' },
  { url: '/products/ab-roller-training-set.html', name: 'EN 深层产品页',  lang: 'en' },
  { url: '/blog.html',                            name: 'EN 博客索引',    lang: 'en' },
  { url: '/tpe-yoga-mats.html',                   name: 'EN 分类页',      lang: 'en' },
  { url: '/de/',                                  name: 'DE 首页',        lang: 'de' },
  { url: '/ja/products.html',                     name: 'JA 产品列表',    lang: 'ja' },
  { url: '/ko/index.html',                        name: 'KO 首页',        lang: 'ko' },
  // 这页 footer 用另一套栏目结构（FUJIAN SANFAN / Entdecken / Kontakt），本就没有产品栏目
  { url: '/de/blog/yoga-mat-materials.html',      name: 'DE 博客(异形footer)', lang: 'de', footSkip: true },
];

const VIEWPORTS = [1440, 1280, 1024, 900, 768, 375];

const EXPECT = {
  en: { nav: [EN_PROD, EN_PIL], foot: EN_PROD },
  de: { nav: ['Yogamatten & Fitness'], foot: 'Yogamatten & Fitness' },
  ja: { nav: ['ヨガマット＆フィットネス'], foot: 'ヨガマット＆フィットネス' },
  ko: { nav: ['요가 매트 & 피트니스'], foot: '요가 매트 & 피트니스' },
};

let fails = 0, warns = 0, checks = 0;
const bad = [];

function ok(cond, label, detail) {
  checks++;
  if (!cond) { fails++; bad.push(label + (detail ? ' → ' + detail : '')); }
  return cond;
}
function warn(cond, label, detail) {
  checks++;
  if (!cond) { warns++; bad.push('[WARN] ' + label + (detail ? ' → ' + detail : '')); }
}

async function blockGA(ctx) {
  await ctx.route(/google-analytics|googletagmanager/, (r) => r.abort());
}

async function open(page, url) {
  await page.goto(BASE + url, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForSelector('.nav-links', { state: 'attached', timeout: 15000 });
  await page.waitForTimeout(250);
}

/** 一级导航项文本（.nav-links 直接子 a + .nav-drop 的触发 a） */
async function navItems(page) {
  return page.$$eval('.nav-links > a, .nav-links > .nav-drop > a', (els) =>
    els.map((e) => e.innerText.replace(/\s+/g, ' ').trim()).filter(Boolean));
}

/** 导航与页面的溢出度量 */
async function overflow(page) {
  return page.evaluate(() => {
    const nav = document.querySelector('.nav-links');
    const header = document.querySelector('.site-header');
    const de = document.documentElement;
    const navVisible = !!nav && nav.getClientRects().length > 0;
    const toggle = document.querySelector('.menu-toggle');
    return {
      navScrollW: nav ? nav.scrollWidth : -1,
      navClientW: nav ? nav.clientWidth : -1,
      navRatio: nav ? +(nav.scrollWidth / Math.max(nav.clientWidth, 1)).toFixed(3) : 0,
      navVisible,
      hasToggle: !!toggle && toggle.getClientRects().length > 0,
      headerScrollW: header ? header.scrollWidth : -1,
      headerClientW: header ? header.clientWidth : -1,
      docW: de.scrollWidth,
      winW: window.innerWidth,
    };
  });
}

async function footerHeadings(page) {
  return page.$$eval('.site-footer h5', (els) =>
    els.map((e) => e.innerText.replace(/\s+/g, ' ').trim()));
}

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext();
  await blockGA(ctx);
  const page = await ctx.newPage();

  const consoleErrs = [];
  const reqFails = [];
  page.on('pageerror', (e) => consoleErrs.push(String(e).slice(0, 160)));
  page.on('response', (r) => {
    if (r.status() >= 400 && !/google-analytics|googletagmanager/.test(r.url()))
      reqFails.push(r.status() + ' ' + r.url().replace(BASE, ''));
  });

  console.log('=== 1) 一级导航文案 + footer 栏目名 ===');
  for (const p of PAGES) {
    await page.setViewportSize({ width: 1440, height: 900 });
    await open(page, p.url);
    const items = await navItems(page);
    const h5 = await footerHeadings(page);
    const exp = EXPECT[p.lang];
    console.log(`  ${p.name.padEnd(20)} nav=[${items.join(' | ')}]`);
    for (const want of exp.nav) ok(items.includes(want), `${p.name} 导航含「${want}」`, `实际=${items.join('/')}`);
    // ⚠️ footer 的 h5 带 text-transform:uppercase，innerText 拿到的是大写 → 必须忽略大小写比较
    if (!p.footSkip) {
      ok(h5.some((x) => x.toLowerCase() === exp.foot.toLowerCase()),
        `${p.name} footer 含「${exp.foot}」`, `实际=${h5.join('/')}`);
    }
    // 旧词不应残留
    ok(!items.includes('Products') && !items.some((x) => /^(Produkte|Prodotti|Productos|Produits|製品|제품)$/.test(x)),
      `${p.name} 导航无旧词残留`, items.join('/'));
  }

  console.log('\n=== 2) 中文态（EN 页需 localStorage.siteLang=zh 后 reload）===');
  for (const p of PAGES.filter((x) => x.lang === 'en')) {
    await page.setViewportSize({ width: 1440, height: 900 });
    await open(page, p.url);
    await page.evaluate(() => localStorage.setItem('siteLang', 'zh'));
    await open(page, p.url);
    const items = await navItems(page);
    console.log(`  ${p.name.padEnd(20)} zh nav=[${items.join(' | ')}]`);
    ok(items.includes('瑜伽垫与健身'), `${p.name} 中文态含「瑜伽垫与健身」`, items.join('/'));
    ok(items.includes('普拉提器械'), `${p.name} 中文态含「普拉提器械」`, items.join('/'));
    const h5 = await footerHeadings(page);
    ok(h5.includes('瑜伽垫与健身'), `${p.name} 中文态 footer 含「瑜伽垫与健身」`, h5.join('/'));
    await page.evaluate(() => localStorage.setItem('siteLang', 'en'));
  }

  console.log('\n=== 3) 多视口导航溢出（文案变长的主要风险）===');
  for (const p of PAGES) {
    const rows = [];
    for (const w of VIEWPORTS) {
      await page.setViewportSize({ width: w, height: 900 });
      await open(page, p.url);
      const m = await overflow(page);
      rows.push(`${w}:${m.navVisible ? m.navRatio : '收起'}`);
      // 窄屏导航收起为汉堡菜单：此时验它真的收起了，且页面无横向滚动
      if (m.navVisible) {
        ok(m.navRatio <= 1.02, `${p.name} @${w}px 导航不溢出`, `scrollW=${m.navScrollW} clientW=${m.navClientW}`);
      } else {
        ok(m.hasToggle, `${p.name} @${w}px 收起态有汉堡按钮`, '未见 .menu-toggle');
      }
      ok(m.docW <= m.winW + 1, `${p.name} @${w}px 页面无横向滚动`, `doc=${m.docW} win=${m.winW}`);
    }
    console.log(`  ${p.name.padEnd(20)} nav 宽高比 ${rows.join('  ')}`);
  }

  console.log('\n=== 4) 控制台错误 / 4xx ===');
  const GA = /google-analytics|googletagmanager/;
  const realErrs = consoleErrs.filter((e) => !GA.test(e));
  ok(realErrs.length === 0, '无控制台错误', realErrs.slice(0, 3).join(' ; '));
  ok(reqFails.length === 0, '无 4xx 请求', reqFails.slice(0, 3).join(' ; '));
  if (realErrs.length) console.log('  pageerror:', realErrs.slice(0, 5));
  if (reqFails.length) console.log('  4xx:', [...new Set(reqFails)].slice(0, 5));

  await browser.close();

  console.log('\n================ 结果 ================');
  console.log(`  检查项 ${checks}  FAIL ${fails}  WARN ${warns}`);
  if (bad.length) bad.slice(0, 25).forEach((b) => console.log('   ' + b));
  process.exit(fails ? 1 : 0);
})();
