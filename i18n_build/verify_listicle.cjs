// 榜单页语言块修复的浏览器级验证
// 用法: NODE_PATH=<workspace>/node_modules node i18n_build/verify_listicle.cjs
// 前提: 先起本地服务 python3 -m http.server 8848
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = 'http://127.0.0.1:8848';
const OUT = 'outputs/blog_check';

const CASES = [
  { name: 'en-listicle-EN', url: '/blog/top-12-china-yoga-mat-manufacturers.html', lang: 'en', shot: 'listicle-en-mode.png' },
  { name: 'en-listicle-ZH', url: '/blog/top-12-china-yoga-mat-manufacturers.html', lang: 'zh', shot: 'listicle-zh-mode.png' },
  { name: 'de-listicle-DE', url: '/de/blog/top-12-china-yoga-mat-manufacturers.html', lang: 'de', shot: null },
  { name: 'blog-moq-ZH', url: '/blog/moq-explained.html', lang: 'zh', shot: 'blog-moq-zh-mode.png' },
  { name: 'blog-moq-EN', url: '/blog/moq-explained.html', lang: 'en', shot: null },
  { name: 'blog-flagship-ZH', url: '/blog/private-label-yoga-mats.html', lang: 'zh', shot: null },
];

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  let fail = 0;
  for (const c of CASES) {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    await ctx.addInitScript((l) => {
      try { localStorage.setItem('siteLang', l); } catch (e) {}
    }, c.lang);
    const page = await ctx.newPage();
    const errs = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    page.on('pageerror', (e) => errs.push('pageerror: ' + e.message));
    await page.goto(BASE + c.url, { waitUntil: 'networkidle' });

    const r = await page.evaluate(() => {
      const vis = (sel) => {
        const el = document.querySelector(sel);
        if (!el) return null;
        const cs = getComputedStyle(el);
        const rc = el.getBoundingClientRect();
        return { display: cs.display, w: Math.round(rc.width), top: Math.round(rc.top) };
      };
      const zh = document.querySelector('.lang-zh');
      const en = document.querySelector('.lang-en');
      const box = (el) => {
        if (!el) return null;
        const rc = el.getBoundingClientRect();
        return { left: Math.round(rc.left), w: Math.round(rc.width) };
      };
      const cont = document.querySelector('section.section .container');
      // 正文首段文字长度（判断是否白页）
      const body = document.querySelector('article .article-body');
      const meta = document.querySelector('.post-meta');
      return {
        htmlClass: document.documentElement.className,
        htmlLang: document.documentElement.lang,
        enVis: vis('.lang-en'), zhVis: vis('.lang-zh'),
        zhBox: box(zh), contBox: box(cont),
        bodyTextLen: body ? body.innerText.replace(/\s+/g, ' ').length : 0,
        firstMeta: meta ? meta.innerText.trim().slice(0, 40) : null,
        h1: document.querySelectorAll('h1').length,
        visibleH1: [...document.querySelectorAll('h1')].filter((e) => e.getBoundingClientRect().width > 0).length,
        thCount: document.querySelectorAll('table.cap-table th').length,
        overflowX: document.documentElement.scrollWidth - window.innerWidth,
      };
    });

    const problems = [];
    // 1) 不能白页：正文文字必须够长
    if (r.bodyTextLen < 1200) problems.push(`正文过短/白页 bodyText=${r.bodyTextLen}`);
    // 2) 期望的语言块可见，另一块不可见
    // 分语言 URL 页（de/ja/...）自身没有语言块（applyLang 对它们直接 return），跳过这项
    if (c.lang === 'en' || c.lang === 'zh') {
      const wantVis = c.lang === 'zh' ? r.zhVis : r.enVis;
      const otherVis = c.lang === 'zh' ? r.enVis : r.zhVis;
      if (wantVis === null) problems.push(`${c.lang} 模式期望块不存在`);
      else if (wantVis.display === 'none' || wantVis.w === 0) problems.push(`${c.lang} 模式期望块不可见`);
      if (otherVis && otherVis.display !== 'none' && otherVis.w > 0) {
        problems.push(`另一语言块仍可见 (${otherVis.display})`);
      }
    }
    // 3) 中文块必须在容器内（左右留白 > 0，宽度 ≤ 容器宽度）
    if (c.lang === 'zh' && r.zhBox && r.contBox) {
      if (r.zhBox.left < r.contBox.left) problems.push(`中文块溢出容器 left=${r.zhBox.left} < container=${r.contBox.left}`);
      if (r.zhBox.w > r.contBox.w + 2) problems.push(`中文块比容器宽 ${r.zhBox.w} > ${r.contBox.w}`);
    }
    // 4) 只有一个 h1 可见（榜单页 & 旗舰页用 h2.post-title 承接中文标题）
    if (r.visibleH1 !== 1) problems.push(`可见 h1 数=${r.visibleH1}（期望 1）`);
    // 5) 无横向溢出、无 console error
    if (r.overflowX > 2) problems.push(`横向溢出 ${r.overflowX}px`);
    if (errs.length) problems.push('console error: ' + errs.slice(0, 2).join(' | '));
    // 6) 榜单页表格 6 列
    if (c.url.includes('top-12') && r.thCount !== 6 && r.thCount !== 12) problems.push(`th=${r.thCount}`);

    if (c.shot) await page.screenshot({ path: `${OUT}/${c.shot}`, fullPage: false });
    const ok = problems.length === 0;
    if (!ok) fail++;
    console.log(`${ok ? '✅' : '❌'} ${c.name.padEnd(18)} html.class=${r.htmlClass.padEnd(10)} lang=${r.htmlLang.padEnd(5)} bodyText=${String(r.bodyTextLen).padStart(5)} th=${r.thCount} overflowX=${r.overflowX}` + (ok ? '' : '\n     ' + problems.join('\n     ')));
    await ctx.close();
  }
  await browser.close();
  console.log(fail ? `\n❌ ${fail} 个用例未通过` : '\n✅ 全部用例通过');
  process.exit(fail ? 1 : 0);
})();
