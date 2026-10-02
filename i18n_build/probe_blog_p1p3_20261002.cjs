/* 6 篇普拉提博客 —— 改进后（P1/P2/P3）渲染复核
 * 判据来源：本项目实测踩过的坑
 *   ① loading="lazy" 的图未进视口时 naturalWidth=0 → 假「解码失败」
 *      → 必须先按 documentElement.scrollHeight 逐屏滚到底、等全部 img.complete、再滚回顶部
 *   ② 「视口外元素」要认容器：cap-table 在窄屏是 overflow-x:auto 容器内滚动，是既有设计
 *   ③ 本地必须走 HTTP（file:// 会破 JS 按目录深度推算的相对路径）
 * 用法：NODE_PATH=... node i18n_build/probe_blog_p1p3_20261002.cjs [base]
 */
const { chromium } = require('playwright');

const BASE = process.argv[2] || 'http://127.0.0.1:8866';
const SLUGS = [
  'pilates-reformer-buyers-guide', 'pilates-apparatus-differences',
  'pilates-studio-equipment-list', 'oem-pilates-equipment-china',
  'pilates-studio-layout-guide', 'pilates-equipment-commercial-use',
];
const VIEWPORTS = [
  { name: '桌面 1440', width: 1440, height: 900 },
  { name: '移动 390', width: 390, height: 844 },
];

let fail = 0;
function chk(label, cond, detail) {
  if (!cond) fail++;
  console.log(`  ${cond ? '✓' : '✗'} ${label}${detail !== undefined ? '  ' + detail : ''}`);
}

async function warmLazy(page) {
  await page.evaluate(async () => {
    const step = Math.round(window.innerHeight * 0.8);
    const max = document.documentElement.scrollHeight;   // ⚠️ 不要用 body.scrollHeight（偏小，漏页尾）
    for (let y = 0; y < max; y += step) {
      window.scrollTo(0, y);
      await new Promise(r => setTimeout(r, 60));
    }
    window.scrollTo(0, max);
    await new Promise(r => setTimeout(r, 200));
    window.scrollTo(0, 0);
  });
  try {
    await page.waitForFunction(
      () => Array.from(document.images).every(i => i.complete),
      null, { timeout: 15000 });
  } catch (e) {
    // 容错：超时也继续，后面按张报
  }
}

(async () => {
  const browser = await chromium.launch();
  for (const vp of VIEWPORTS) {
    console.log(`\n${'='.repeat(74)}\n视口：${vp.name}\n${'='.repeat(74)}`);
    const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
    for (const slug of SLUGS) {
      const page = await ctx.newPage();
      const errs = [];
      page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
      await page.goto(`${BASE}/blog/${slug}.html`, { waitUntil: 'load' });
      await warmLazy(page);

      const r = await page.evaluate(() => {
        const doc = document.documentElement;
        const overflow = doc.scrollWidth - doc.clientWidth;
        const badImgs = Array.from(document.images)
          .filter(i => i.complete && i.naturalWidth === 0)
          .map(i => i.getAttribute('src'));

        // 新增段落：方法论 + 来源（英文侧）
        const h2s = Array.from(document.querySelectorAll('.article-body h2'))
          .map(h => h.textContent.trim());
        // 引擎判据要求 h_text 恰好等于 "our methodology"
        const exactMethodology = h2s.some(t => t.toLowerCase() === 'our methodology');
        const hasSources = h2s.some(t => /^sources$/i.test(t));

        // 「we measured」类一手数据信号（引擎 _FIRST_PARTY_PATTERNS）
        const text = document.body.innerText;
        const fpSignals = (text.match(/we measured|our data shows|we tested|our findings/gi) || []).length;
        const ownData = (text.match(/\b(?:we|our team|our company)\s+\w+\s+\d+/gi) || []).length;

        // 外链
        const ext = Array.from(document.querySelectorAll('a[href^="http"]'))
          .filter(a => !a.href.includes('fjsanfan.com'))
          .map(a => ({ href: a.getAttribute('href'), target: a.getAttribute('target'), rel: a.getAttribute('rel') }));

        // 署名
        const byline = /SANFAN production/i.test(text);

        // FaQ 可见问答：英/中两个块各 5 条（双语 DOM 都要在，别把总数当预期值）
        const faqEn = document.querySelectorAll('.lang-en .article-body h3').length;
        const faqZh = document.querySelectorAll('.lang-zh .article-body h3').length;

        return { overflow, badImgs, h2s, exactMethodology, hasSources, fpSignals, ownData,
                 ext, byline, faqEn, faqZh, docH: doc.scrollHeight };
      });

      console.log(`\n${slug}`);
      chk('横向溢出 = 0', r.overflow <= 0, `溢出 ${r.overflow}px，页高 ${r.docH}px`);
      chk('图片无解码失败', r.badImgs.length === 0, r.badImgs.length ? r.badImgs.join(', ') : '全部加载');
      chk('H2 = "Our methodology"（引擎精确匹配判据）', r.exactMethodology,
          r.h2s.filter(t => /method/i.test(t)).join(' / ') || '（未见）');
      chk('含 Sources 小节', r.hasSources);
      chk('一手数据信号 ≥2（we measured 类）', r.fpSignals >= 2, `${r.fpSignals} 处`);
      chk('自有数据信号 ≥1（we/our team 紧邻数字）', r.ownData >= 1, `${r.ownData} 处`);
      // 双语 DOM 各 1 组 Sources → 4 个 Wikipedia 链接；另有 JS 注入的 .cbar（wa.me），别混算
      const wiki = r.ext.filter(a => a.href.includes('wikipedia.org'));
      chk('Wikipedia 外链 2 组（双语）且均 target=_blank rel=noopener',
          wiki.length === 4 && wiki.every(a => a.target === '_blank' && (a.rel || '').includes('noopener')),
          wiki.map(a => a.href.replace('https://en.wikipedia.org/wiki/', '')).join(' , ') || '（无）');
      chk('团队署名可见', r.byline);
      chk('FAQ 可见问答 h3 英/中各 5', r.faqEn === 5 && r.faqZh === 5, `英 ${r.faqEn} / 中 ${r.faqZh}`);
      chk('无 JS 控制台报错', errs.length === 0, errs.slice(0, 2).join(' | '));
      await page.close();
    }
    await ctx.close();
  }
  await browser.close();
  console.log(`\n${'='.repeat(74)}\n${fail === 0 ? '✓ 全部通过' : '✗ ' + fail + ' 项失败'}\n`);
  process.exit(fail ? 1 : 0);
})();
