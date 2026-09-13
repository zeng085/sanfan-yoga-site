// 榜单页语言块修复的浏览器级验证
// 用法: NODE_PATH=<workspace>/node_modules node i18n_build/verify_listicle.cjs
// 前提: 先起本地服务 python3 -m http.server 8848
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = 'http://127.0.0.1:8848';
const OUT = 'outputs/blog_check';

const CASES = [
  // 榜单页（双语块）
  { name: 'en-listicle-EN', url: '/blog/top-12-china-yoga-mat-manufacturers.html', lang: 'en', shot: 'listicle-en-mode.png' },
  { name: 'en-listicle-ZH', url: '/blog/top-12-china-yoga-mat-manufacturers.html', lang: 'zh', shot: 'listicle-zh-mode.png' },
  { name: 'de-listicle-DE', url: '/de/blog/top-12-china-yoga-mat-manufacturers.html', lang: 'de', shot: null },
  // 9 篇博客文章页：中文块全量补齐后，逐页跑 ZH/EN 双模式
  { name: 'blog-moq-ZH', url: '/blog/moq-explained.html', lang: 'zh', shot: 'blog-moq-zh-mode.png' },
  { name: 'blog-moq-EN', url: '/blog/moq-explained.html', lang: 'en', shot: null },
  { name: 'blog-sampling-ZH', url: '/blog/7day-sampling.html', lang: 'zh', shot: null },
  { name: 'blog-compliance-ZH', url: '/blog/compliance.html', lang: 'zh', shot: null },
  { name: 'blog-customsizes-ZH', url: '/blog/custom-sizes.html', lang: 'zh', shot: null },
  { name: 'blog-tpevspu-ZH', url: '/blog/tpe-vs-pu.html', lang: 'zh', shot: 'blog-tpevspu-zh-mode.png' },
  { name: 'blog-vetfactory-ZH', url: '/blog/vet-factory.html', lang: 'zh', shot: null },
  { name: 'blog-materials-ZH', url: '/blog/yoga-mat-materials.html', lang: 'zh', shot: 'blog-materials-zh-mode.png' },
  { name: 'blog-specguide-ZH', url: '/blog/yoga-mat-spec-guide.html', lang: 'zh', shot: 'blog-specguide-zh-mode.png' },
  { name: 'blog-flagship-ZH', url: '/blog/private-label-yoga-mats.html', lang: 'zh', shot: 'blog-private-zh-mode.png' },
  { name: 'blog-flagship-EN', url: '/blog/private-label-yoga-mats.html', lang: 'en', shot: null },
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
      // ⭐ 只统计**真正渲染**的文字：元素 getClientRects() 为空即被 CSS 隐藏。
      // 不能用 el.innerText —— 不可渲染的元素会回退成 textContent，隐藏块也会被算进来，
      // 于是「防白页」断言永远通过，中文残块就是这么混过验收的（2026-09-13 踩到）。
      const visibleText = (el) => {
        if (!el) return '';
        let out = '';
        const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
        while (w.nextNode()) {
          const p = w.currentNode.parentElement;
          if (p && p.getClientRects().length > 0) out += w.currentNode.nodeValue;
        }
        return out.replace(/\s+/g, '');
      };
      // 取「当前可见」那个语言块里的 article-body —— 不能直接 querySelector('article .article-body')，
      // DOM 里 en 块在前，中文模式下会拿到隐藏块，量出 0
      const activeBlock = (en && en.getClientRects().length > 0) ? en
                        : ((zh && zh.getClientRects().length > 0) ? zh : null);
      const body = activeBlock ? activeBlock.querySelector('.article-body')
                               : document.querySelector('article .article-body');
      const meta = document.querySelector('.post-meta');
      const art = document.querySelector('article');
      const enLen = en ? (en.textContent || '').replace(/\s+/g, '').length : 0;
      const zhLen = zh ? (zh.textContent || '').replace(/\s+/g, '').length : 0;
      return {
        htmlClass: document.documentElement.className,
        htmlLang: document.documentElement.lang,
        enVis: vis('.lang-en'), zhVis: vis('.lang-zh'),
        zhBox: box(zh), contBox: box(cont),
        // 可见正文文字量（真实渲染的部分）
        bodyTextLen: body ? visibleText(body).length : 0,
        artVisLen: art ? visibleText(art).length : 0,
        visEnLen: visibleText(en).length,
        visZhLen: visibleText(zh).length,
        enLen, zhLen,
        zhRatio: enLen ? zhLen / enLen : 0,
        firstMeta: meta ? meta.innerText.trim().slice(0, 40) : null,
        h1: document.querySelectorAll('h1').length,
        visibleH1: [...document.querySelectorAll('h1')].filter((e) => e.getBoundingClientRect().width > 0).length,
        thCount: document.querySelectorAll('table.cap-table th').length,
        overflowX: document.documentElement.scrollWidth - window.innerWidth,
      };
    });

    const problems = [];
    // 1) 不能白页：**可见**正文文字必须够长
    //    注意：原来用 el.innerText —— 不可渲染元素会回退成 textContent，隐藏块也被计入，
    //    于是「防白页」断言永远通过。中文残块正是这样混过验收的（2026-09-13 踩到）。
    if (r.bodyTextLen < 1200) problems.push(`可见正文过短/白页 visBodyText=${r.bodyTextLen}`);
    if (r.artVisLen < 1200) problems.push(`article 可见文字过短 artVisLen=${r.artVisLen}`);
    // 1b) ⭐ 内容对等性：中文块不得是摘要残块
    //     标定：站内 1237 组人工忠实配对实测中/英字符比 中位 0.353（中文天然更密，忠实译文≈1/3）
    //     全站静态版见 i18n_build/check_zh_parity.py
    if (r.enLen > 2000 && r.zhRatio < 0.25) {
      problems.push(`中文块疑似摘要残块 zhRatio=${r.zhRatio.toFixed(3)}（zh=${r.zhLen} / en=${r.enLen}）`);
    }
    // 2) 期望的语言块可见，另一块不仅隐藏、而且**可见文字必须为 0**
    // 分语言 URL 页（de/ja/...）自身没有语言块（applyLang 对它们直接 return），跳过这项
    if (c.lang === 'en' || c.lang === 'zh') {
      const wantVis = c.lang === 'zh' ? r.zhVis : r.enVis;
      const otherVis = c.lang === 'zh' ? r.enVis : r.zhVis;
      const wantVisLen = c.lang === 'zh' ? r.visZhLen : r.visEnLen;
      const otherVisLen = c.lang === 'zh' ? r.visEnLen : r.visZhLen;
      if (wantVis === null) problems.push(`${c.lang} 模式期望块不存在`);
      else if (wantVis.display === 'none' || wantVis.w === 0) problems.push(`${c.lang} 模式期望块不可见`);
      else if (wantVisLen < 1200) problems.push(`${c.lang} 模式期望块可见文字仅 ${wantVisLen} 字（疑似白页/残块）`);
      if (otherVis && otherVis.display !== 'none' && otherVis.w > 0) {
        problems.push(`另一语言块仍可见 (${otherVis.display})`);
      }
      if (otherVisLen > 0) problems.push(`另一语言块仍有可见文字 ${otherVisLen} 字`);
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
    console.log(`${ok ? '✅' : '❌'} ${c.name.padEnd(18)} ${r.htmlClass.padEnd(10)} lang=${r.htmlLang.padEnd(5)} visBody=${String(r.bodyTextLen).padStart(5)} visEN=${String(r.visEnLen).padStart(5)} visZH=${String(r.visZhLen).padStart(5)} zhRatio=${r.zhRatio.toFixed(3)} th=${r.thCount} ovf=${r.overflowX}` + (ok ? '' : '\n     ' + problems.join('\n     ')));
    await ctx.close();
  }
  await browser.close();
  console.log(fail ? `\n❌ ${fail} 个用例未通过` : '\n✅ 全部用例通过');
  process.exit(fail ? 1 : 0);
})();
