/**
 * dump_nav_structure_20261001.cjs
 * 把各页型的实际导航结构打出来（不看断言，只看事实）——
 * 用于判断 check_nav_pilates.cjs 的 11 处失败是「过时断言」还是「真缺陷」。
 *
 * 输出：每页的 .nav-links 子项（text / href / 是否含下拉 / 下拉链接数）
 */
const { chromium } = require('playwright');

const BASE = process.env.BASE || 'http://127.0.0.1:8866';

const PAGES = [
  ['EN 根页', '/index.html'],
  ['EN 深层产品页', '/products/ym1.html'],
  ['EN 分类页', '/tpe-yoga-mats.html'],
  ['EN 普拉提族页', '/pilates/pilates-ladder-barrel.html'],
  ['DE 语言页', '/de/index.html'],
  ['JA 语言页', '/ja/products.html'],
  ['DE 普拉提族页', '/de/pilates/pilates-ladder-barrel.html'],
];

(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } });
  await ctx.route(/google-analytics|googletagmanager/, (r) => r.abort());
  const page = await ctx.newPage();

  for (const [label, url] of PAGES) {
    const r = await page.goto(BASE + url, { waitUntil: 'domcontentloaded' }).catch(() => null);
    if (!r || !r.ok()) { console.log(`\n### ${label} ${url}  → HTTP ${r ? r.status() : 'NA'}`); continue; }
    await page.waitForTimeout(220);
    const info = await page.evaluate(() => {
      const nav = document.querySelector('.nav-links');
      if (!nav) return { err: 'no .nav-links' };
      const kids = [...nav.children];
      const rows = kids.map((el) => {
        const a = el.tagName === 'A' ? el : el.querySelector('a');
        const menu = el.querySelector('.nav-drop-menu');
        const isSearch = el.classList.contains('nav-search-item');
        return {
          tag: el.tagName.toLowerCase() + (el.className ? '.' + el.className.toString().split(' ')[0] : ''),
          text: a ? a.textContent.replace(/\s+/g, ' ').trim().slice(0, 26) : '(无a)',
          href: a ? a.getAttribute('href') : null,
          menu: menu ? menu.querySelectorAll('a').length : 0,
          menuHrefs: menu ? [...menu.querySelectorAll('a')].map((x) => x.getAttribute('href')) : null,
          search: isSearch,
        };
      });
      return { count: kids.length, rows };
    });
    console.log(`\n### ${label}  ${url}`);
    if (info.err) { console.log('   ' + info.err); continue; }
    console.log(`   子项 ${info.count} 个：`);
    info.rows.forEach((r2, i) => {
      console.log(`   [${i}] ${r2.search ? '(搜索项) ' : ''}text="${r2.text}"  href=${r2.href}  下拉=${r2.menu}`);
    });
    const pil = info.rows.find((r2) => r2.href && /pilates\/?$/.test(r2.href));
    console.log(`   → Pilates 入口：${pil ? `找到 @${info.rows.indexOf(pil)} href=${pil.href} 下拉=${pil.menu}` : '未找到（href 不以 pilates/ 结尾）'}`);
  }

  await b.close();
})();
