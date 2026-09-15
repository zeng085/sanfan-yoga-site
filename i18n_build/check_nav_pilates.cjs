/**
 * check_nav_pilates.cjs — 验「全站导航注入」在浏览器端真的成立
 *
 * 覆盖三种页型：EN 根页 / EN 深层页 / 语言页
 * 断言：
 *   1. 导航里出现 Pilates 一级入口，**紧跟 Home 之后**（顺序 Home → Pilates → Products）
 *      ⚠️ 不能断言固定下标：main.js 运行时会往 .nav-links 最前面插一个 .nav-search-item
 *   2. EN 页悬停出现 8 族下拉；下拉里 9 个链接（8 族 + All）全部 200
 *   3. 中文态下入口文案变「普拉提器械」（必须用 localStorage.siteLang=zh 后重载，
 *      直接 classList.add('show-zh') 不会触发 main.js 的 applyLang → 字典不生效）
 *   4. 语言页只有裸入口、没有下拉
 *   5. 页面无 4xx / 请求失败（排除 GA 噪音）
 *
 * 用法:
 *   NODE_PATH=<node_modules> node i18n_build/check_nav_pilates.cjs
 */
const { chromium } = require('playwright');

const BASE = process.env.BASE || 'http://127.0.0.1:8848';

/** 本机无外网时 GA 请求会一直挂着，networkidle 永不触发 → 统一拦掉。 */
async function blockGA(ctx) {
  await ctx.route(/google-analytics|googletagmanager/, (r) => r.abort());
}

/** 只用 domcontentloaded：我们要的是 DOM + main.js 执行完，不等图片/埋点。 */
async function open(page, url) {
  await page.goto(BASE + url, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForSelector('.nav-links', { timeout: 15000 });
  await page.waitForTimeout(200);
}

const PAGES = [
  { url: '/index.html', kind: 'en', label: 'EN 根页' },
  { url: '/products/ym1.html', kind: 'en', label: 'EN 深层产品页' },
  { url: '/tpe-yoga-mats.html', kind: 'en', label: 'EN 分类页' },
  { url: '/blog/compliance.html', kind: 'en', label: 'EN 博客页' },
  { url: '/applications/gyms-fitness-clubs.html', kind: 'en', label: 'EN 场景页' },
  { url: '/de/index.html', kind: 'lang', label: 'DE 语言页' },
  { url: '/ja/products.html', kind: 'lang', label: 'JA 语言页' },
  { url: '/ko/blog.html', kind: 'lang', label: 'KO 语言页' },
];

const probe = () => {
  const nav = document.querySelector('.nav-links');
  if (!nav) return { err: 'no .nav-links' };
  const kids = [...nav.children];
  const hrefOf = (el) => (el.tagName === 'A' ? el : el.querySelector('a'));
  const links = kids.map((el) => {
    const a = hrefOf(el);
    return { href: a ? a.getAttribute('href') : '', text: a ? a.textContent.trim() : '' };
  });
  const homeIdx = links.findIndex((l) => l.text === 'Home' || /^(Startseite|ホーム|홈|Accueil|Home|Inicio)$/.test(l.text));
  const plIdx = links.findIndex((l) => l.href === '/pilates/');
  const drop = nav.querySelector('.nav-drop');
  const menuLinks = drop ? [...drop.querySelectorAll('.nav-drop-menu a')].map((a) => a.getAttribute('href')) : [];
  return {
    links, homeIdx, plIdx,
    plText: plIdx >= 0 ? links[plIdx].text : '(无)',
    plIsDrop: plIdx >= 0 ? kids[plIdx].classList.contains('nav-drop') : false,
    menuLinks,
  };
};

(async () => {
  const browser = await chromium.launch();
  let fail = 0;
  const bad = [];

  for (const p of PAGES) {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    await blockGA(ctx);
    const page = await ctx.newPage();
    page.on('response', (r) => {
      if (r.status() >= 400 && !/google-analytics|googletagmanager/.test(r.url())) {
        bad.push(`${p.url}  ${r.status()}  ${r.url()}`);
      }
    });
    page.on('requestfailed', (r) => {
      if (!/google-analytics|googletagmanager/.test(r.url())) {
        bad.push(`${p.url}  FAILED  ${r.url()}`);
      }
    });
    await open(page, p.url);

    const n = await page.evaluate(probe);
    if (n.err) {
      console.log(`  ✗ ${p.label.padEnd(14)} ${p.url}  ${n.err}`);
      fail++;
      await ctx.close();
      continue;
    }
    const okPos = n.plIdx >= 0 && n.plIdx === n.homeIdx + 1;
    const okShape = p.kind === 'en' ? (n.plIsDrop && n.menuLinks.length === 9) : (!n.plIsDrop && n.menuLinks.length === 0);
    const okText = n.plText === 'Pilates';
    const ok = okPos && okShape && okText;
    if (!ok) fail++;
    console.log(`${ok ? '✓' : '✗'} ${p.label.padEnd(14)} ${p.url.padEnd(34)} ` +
      `Home@${n.homeIdx} Pilates@${n.plIdx}(需紧邻) 下拉=${n.menuLinks.length}项(${p.kind === 'en' ? 'EN需9' : '语言需0'}) 文案="${n.plText}"`);

    // EN 页：悬停取下拉 → 逐个探活
    if (p.kind === 'en' && n.menuLinks.length === 9) {
      await page.hover('.nav-drop > a');
      await page.waitForTimeout(300);
      const vis = await page.evaluate(() => {
        const m = document.querySelector('.nav-drop-menu');
        return !!m && getComputedStyle(m).display !== 'none' && m.getBoundingClientRect().height > 10;
      });
      if (!vis) { console.log('  ✗ 悬停未出现下拉'); fail++; }
      else {
        for (const href of n.menuLinks) {
          const r = await page.request.get(BASE + href);
          if (r.status() !== 200) { console.log(`  ✗ 下拉链接 ${href} → ${r.status()}`); fail++; }
        }
      }
    }
    await ctx.close();

    // 中文态：必须走 localStorage.siteLang=zh + 重载（applyLang 才会跑字典）
    const ctx2 = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    await blockGA(ctx2);
    await ctx2.addInitScript(() => {
      try { localStorage.setItem('siteLang', 'zh'); document.cookie = 'siteLang=zh;path=/'; } catch (e) {}
    });
    const p2 = await ctx2.newPage();
    await open(p2, p.url);
    const zh = await p2.evaluate(() => {
      const nav = document.querySelector('.nav-links');
      const kids = [...nav.children];
      const i = kids.findIndex((el) => {
        const a = el.tagName === 'A' ? el : el.querySelector('a');
        return a && a.getAttribute('href') === '/pilates/';
      });
      const a = i >= 0 ? (kids[i].tagName === 'A' ? kids[i] : kids[i].querySelector('a')) : null;
      return { showZh: document.documentElement.classList.contains('show-zh'), text: a ? a.textContent.trim() : '(无)' };
    });
    await ctx2.close();
    if (p.kind === 'en') {
      const okZh = zh.showZh && zh.text === '普拉提器械';
      if (!okZh) fail++;
      console.log(`  ${okZh ? '✓' : '✗'} 中文态 show-zh=${zh.showZh} 入口文案="${zh.text}"（期望「普拉提器械」）`);
    } else {
      // 语言页故意不挂 data-i18n：保持各语言下的 "Pilates" 原词
      const okStay = zh.text === 'Pilates';
      if (!okStay) fail++;
      console.log(`  ${okStay ? '✓' : '·'} 语言页中文态入口保持 "${zh.text}"（设计如此，不随中文切换）`);
    }
  }

  console.log('\n--- HTTP 异常 ---');
  console.log(bad.length ? [...new Set(bad)].join('\n') : '  无 4xx / 请求失败 ✓');
  console.log(fail ? `\n共 ${fail} 处断言失败` : '\n全部断言通过 ✓');
  await browser.close();
  process.exit(fail ? 1 : 0);
})();
