// 内链渲染验收：以 <!-- ilink:v1 --> … <!-- /ilink:v1 --> 注释区间精确定位插入内容，
// 检查可见性 / 语言态取词 / 条数 / 横向溢出 / JS 报错。
// 注意两个坑：
//   ① 语言态存在 localStorage.siteLang，同一 context 内跨页会串扰 → 每页显式设定后再导航
//   ② 博客块是**多个平级元素**（h2+p+ul），不是一个容器 → 必须按注释区间收集兄弟节点
const { chromium } = require('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:8851';
const OUT = process.env.OUT || '/tmp';

const PAGES = [
  { url: '/blog/yoga-mat-materials.html', lang: 'en', want: 2, zhMode: false },
  { url: '/blog/yoga-mat-materials.html', lang: 'zh', want: 2, zhMode: true },
  { url: '/de/blog/yoga-mat-materials.html', lang: 'de', want: 1, zhMode: false },
  { url: '/ja/blog/top-12-china-yoga-mat-manufacturers.html', lang: 'ja', want: 1, zhMode: false },
  { url: '/blog/top-12-china-yoga-mat-manufacturers.html', lang: 'en', want: 2, zhMode: false },
  { url: '/tpe-yoga-mats.html', lang: 'en', want: 1, zhMode: false },
  { url: '/tpe-yoga-mats.html', lang: 'zh', want: 1, zhMode: true },
  { url: '/es/products.html', lang: 'es', want: 1, zhMode: false },
  { url: '/fr/materials.html', lang: 'fr', want: 1, zhMode: false },
];

const CHECK = `(() => {
  const walker = document.createTreeWalker(document.documentElement, NodeFilter.SHOW_COMMENT);
  const opens = [];
  let n;
  while (n = walker.nextNode()) if (n.data.trim() === 'ilink:v1') opens.push(n);
  const segs = opens.map(o => {
    const nodes = [];
    let s = o.nextSibling;
    while (s) {
      if (s.nodeType === 8 && s.data.trim() === '/ilink:v1') break;
      nodes.push(s);
      s = s.nextSibling;
    }
    const links = [];
    let host = null;
    for (const nd of nodes) {
      if (nd.nodeType !== 1) continue;
      if (!host) host = nd;
      links.push(...nd.querySelectorAll('a[href]'));
      if (nd.tagName === 'A') links.push(nd);
    }
    // 取词用 innerText：它只返回**渲染可见**的文字。
    // ⚠️ 这里是模板字面量，\s 会被吃成 s —— 必须写 \\s。
    const shown = links.map(a => (a.innerText || a.textContent || '').trim().replace(/\\s+/g, ' '));
    const pair = links.length ? !!(links[0].querySelector('.lang-en') && links[0].querySelector('.lang-zh')) : false;
    // 语言态不靠猜：以 html 的 show-en / show-zh 类名为准，检查 en/zh span 的 display 是否与之相符
    const htmlCls = document.documentElement.className;
    const enSpan = links.length ? links[0].querySelector('.lang-en') : null;
    const zhSpan = links.length ? links[0].querySelector('.lang-zh') : null;
    const enDisp = enSpan ? getComputedStyle(enSpan).display : null;
    const zhDisp = zhSpan ? getComputedStyle(zhSpan).display : null;
    const langOk = !pair ? null
      : (htmlCls.indexOf('show-zh') >= 0 ? (enDisp === 'none' && zhDisp !== 'none')
                                         : (zhDisp === 'none' && enDisp !== 'none'));
    return {
      tag: host ? host.tagName : '?',
      n: links.length,
      pair,
      shown,
      langOk,
      hrefs: links.map(a => a.getAttribute('href')),
      visibleLinks: links.filter(a => a.offsetParent !== null).length,
      hasHeading: nodes.some(x => x.nodeType === 1 && (/^H[1-6]$/.test(x.tagName) || !!x.querySelector('h2,h3'))),
    };
  });
  return { count: segs.length, segs, htmlCls: document.documentElement.className, overflowX: document.documentElement.scrollWidth > window.innerWidth + 2 };
})()`;

(async () => {
  const browser = await chromium.launch();
  let bad = 0;
  for (const vp of [{ w: 1440, h: 900, tag: '桌面' }, { w: 390, h: 844, tag: '手机' }]) {
    const ctx = await browser.newContext({ viewport: { width: vp.w, height: vp.h } });
    const page = await ctx.newPage();
    const errs = [];
    page.on('pageerror', e => errs.push(String(e).slice(0, 70)));
    for (const p of PAGES) {
      const tag = `${p.lang}/${vp.tag}`;
      try {
        // 先到同源根页设定语言态，避免上一页的串扰。
        // ⚠️ 站内语言态是 localStorage 优先 + **cookie 兜底**（main.js:538/540），
        //    只清 localStorage 会被 cookie 顶回去 —— 两处都要清。
        await page.goto(BASE + '/index.html', { waitUntil: 'domcontentloaded', timeout: 25000 });
        await page.evaluate(z => {
          try {
            if (z) localStorage.setItem('siteLang', 'zh'); else localStorage.removeItem('siteLang');
            document.cookie = 'siteLang=' + (z ? 'zh' : '') + '; path=/; Max-Age=' + (z ? 31536000 : 0);
          } catch (e) { }
        }, p.zhMode);
        await page.goto(BASE + p.url, { waitUntil: 'domcontentloaded', timeout: 25000 });
        await page.waitForTimeout(200);
        const r = await page.evaluate(CHECK);
        const msgs = [];
        if (r.count !== p.want) msgs.push(`块数 ${r.count}≠${p.want}`);
        for (const s of r.segs) {
          if (s.n < 3 || s.n > 5) msgs.push(`链接 ${s.n} 条`);
          if (!s.hasHeading) msgs.push('缺标题');
          // 双语 EN 页有两个语言块，语言开关会让其中一个整块隐藏 —— 允许整块隐藏，
          // 但绝不允许「半可见」（那说明 en/zh 配对漏了）
          if (s.visibleLinks !== 0 && s.visibleLinks !== s.n) msgs.push(`半可见 ${s.visibleLinks}/${s.n}`);
          if (s.langOk === false) msgs.push(`语言态不符（html=${r.htmlCls || '?'}）`);
        }
        const vis = r.segs.filter(s => s.visibleLinks === s.n).length;
        if (vis !== 1) msgs.push(`当前语言下可见块 ${vis} 个（应 1）`);
        if (r.overflowX) msgs.push('横向溢出');
        if (msgs.length) { bad++; console.log(`✗ ${tag.padEnd(9)} ${p.url}  ${msgs.join(' / ')}`); }
        else {
          console.log(`✓ ${tag.padEnd(9)} ${p.url}`);
          console.log(`      [${r.htmlCls}] ` + r.segs.map(s => s.shown.join(' | ')).join('  ‖  ').slice(0, 150));
        }
      } catch (e) {
        bad++; console.log(`✗ ${tag.padEnd(9)} ${p.url}  ERR ${String(e).slice(0, 70)}`);
      }
    }
    if (errs.length) { bad++; console.log(`✗ ${vp.tag} JS 报错: ${errs.slice(0, 2).join(' ; ')}`); }
    await ctx.close();
  }
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  for (const [u, name] of [['/blog/yoga-mat-materials.html', 'ilink_blog_en.png'], ['/tpe-yoga-mats.html', 'ilink_cat_en.png']]) {
    await page.goto(BASE + u, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(300);
    await page.evaluate(() => {
      const w = document.createTreeWalker(document.documentElement, NodeFilter.SHOW_COMMENT);
      let n, last = null;
      while (n = w.nextNode()) if (n.data.trim() === 'ilink:v1') last = n;
      let el = last && last.nextSibling;
      while (el && el.nodeType !== 1) el = el.nextSibling;
      if (el) el.scrollIntoView({ block: 'center' });
    });
    await page.waitForTimeout(400);
    await page.screenshot({ path: `${OUT}/${name}` });
  }
  await browser.close();
  console.log(bad === 0 ? '\n全部通过' : `\n${bad} 项异常`);
  process.exit(bad === 0 ? 0 : 1);
})();
