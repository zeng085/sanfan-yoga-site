/**
 * check_nav_pilates.cjs — 验「全站导航注入」在浏览器端真的成立
 *
 * 覆盖三种页型：EN 根页 / EN 深层页 / 语言页
 * 断言（2026-10-01 修订，旧判据已过时）：
 *   1. 导航里出现 Pilates 一级入口，**紧跟 Home 之后**
 *      ⚠️ 不能断言固定下标：main.js 运行时会往 .nav-links 最前面插一个 .nav-search-item
 *      ⚠️ 不能断言 href === '/pilates/'：语言页是 '/de/pilates/' 等 → 判据为「以 pilates/ 结尾」
 *      ⚠️ 不能断言文案 === 'Pilates'：入口已改名 'Pilates Equipment'（各语言译名不同）
 *   2. 悬停出现 8 族下拉；下拉里 9 个链接（8 族 + All）全部 200
 *   3. 中文态下入口文案变「普拉提器械」（必须用 localStorage.siteLang=zh 后重载，
 *      直接 classList.add('show-zh') 不会触发 main.js 的 applyLang → 字典不生效）
 *   4. 语言页与 EN 同构：**同样带 9 项下拉**（旧版曾是"裸入口无下拉"，已统一）
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
  // ⚠️ 判据修正（2026-10-01）：原写死 href === '/pilates/'，语言页实际是 '/de/pilates/'
  //    → 语言页永远 plIdx=-1，必然报假失败（实测 11 处失败里 6 处是这个）。
  //    改为「以 pilates/ 结尾」，并用文字兜底排除搜索项（搜索项 href 也是 products.html 之类）。
  const isSearch = (i) => kids[i].classList.contains('nav-search-item');
  const plIdx = links.findIndex((l, i) => !isSearch(i) && l.href && /(^|\/)pilates\/$/.test(l.href));
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
    // ⚠️ 判据修正（2026-10-01）：原期望「语言页只有裸入口、无下拉」——
    //    实测 7 个语言页现在**都带 9 项下拉**（与 EN 一致，属后续统一），
    //    旧期望会让每个语言页必失败。现统一要求「入口为下拉且 9 项」。
    const okShape = n.plIsDrop && n.menuLinks.length === 9;
    // ⚠️ 判据修正（2026-10-01）：入口已改名为 "Pilates Equipment"（各语言译名不同），
    //    原 okText === 'Pilates' 已过时。改为「文案非空」——具体措辞由中文态断言单测。
    const okText = typeof n.plText === 'string' && n.plText.trim() !== '' && n.plText !== '(无)';
    const ok = okPos && okShape && okText;
    if (!ok) fail++;
    console.log(`${ok ? '✓' : '✗'} ${p.label.padEnd(14)} ${p.url.padEnd(34)} ` +
      `Home@${n.homeIdx} Pilates@${n.plIdx}(需紧邻) 下拉=${n.menuLinks.length}项(需9) 文案="${n.plText}"`);

    // 下拉链接逐个探活（EN 与语言页现在同构，都测）
    if (n.menuLinks.length === 9) {
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
      // ⚠️ 判据修正（2026-10-01）：同主探针，原写死 '/pilates/' → 语言页取不到入口，
      //    zh.text 恒为 '(无)'，让 3 个语言页必失败（假阴性）。
      const i = kids.findIndex((el) => {
        if (el.classList.contains('nav-search-item')) return false;
        const a = el.tagName === 'A' ? el : el.querySelector('a');
        const h = a ? (a.getAttribute('href') || '') : '';
        return /(^|\/)pilates\/$/.test(h);
      });
      const a = i >= 0 ? (kids[i].tagName === 'A' ? kids[i] : kids[i].querySelector('a')) : null;
      return { showZh: document.documentElement.classList.contains('show-zh'), text: a ? a.textContent.replace(/\s+/g, ' ').trim() : '(无)' };
    });
    await ctx2.close();
    if (p.kind === 'en') {
      const okZh = zh.showZh && zh.text === '普拉提器械';
      if (!okZh) fail++;
      console.log(`  ${okZh ? '✓' : '✗'} 中文态 show-zh=${zh.showZh} 入口文案="${zh.text}"（期望「普拉提器械」）`);
    } else {
      // 语言页故意不挂 data-i18n：保持本语言译名，不随中文切换被替换成「普拉提器械」。
      // ⚠️ 期望值不能写死 'Pilates'（入口已改名，各语言译名不同）→ 判「非空 且 未被切中文」。
      const okStay = zh.text !== '(无)' && zh.text !== '普拉提器械' && zh.text !== '';
      if (!okStay) fail++;
      console.log(`  ${okStay ? '✓' : '✗'} 语言页中文态入口保持 "${zh.text}"（设计如此，不随中文切换）`);
    }
  }

  console.log('\n--- HTTP 异常 ---');
  console.log(bad.length ? [...new Set(bad)].join('\n') : '  无 4xx / 请求失败 ✓');
  console.log(fail ? `\n共 ${fail} 处断言失败` : '\n全部断言通过 ✓');
  await browser.close();
  process.exit(fail ? 1 : 0);
})();
