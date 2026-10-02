/* 截图复核：新增的「Our methodology」段与「Sources」段的实际渲染
 * ⚠️ 必须先预热 lazy 图（否则整页截图里图是空白块），再截。
 * 用法：NODE_PATH=... node i18n_build/shot_blog_p1p3_20261002.cjs [base]
 */
const { chromium } = require('playwright');
const BASE = process.argv[2] || 'http://127.0.0.1:8866';
const OUT = '/Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16/i18n_build/reports';

async function warmLazy(page) {
  await page.evaluate(async () => {
    const step = Math.round(window.innerHeight * 0.8);
    const max = document.documentElement.scrollHeight;
    for (let y = 0; y < max; y += step) {
      window.scrollTo(0, y);
      await new Promise(r => setTimeout(r, 50));
    }
    window.scrollTo(0, 0);
  });
  try {
    await page.waitForFunction(
      () => Array.from(document.images).every(i => i.complete), null, { timeout: 12000 });
  } catch (e) { /* 容错 */ }
}

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1180, height: 900 } });

  // ① 桌面：layout 页的「Our methodology + Sources」两段
  const p1 = await ctx.newPage();
  await p1.goto(`${BASE}/blog/pilates-studio-layout-guide.html`, { waitUntil: 'load' });
  await warmLazy(p1);
  await p1.evaluate(() => {
    const h = Array.from(document.querySelectorAll('.lang-en .article-body h2'))
      .find(x => x.textContent.trim().toLowerCase() === 'our methodology');
    if (h) h.scrollIntoView({ block: 'start' });
  });
  await p1.waitForTimeout(600);
  const rect = await p1.evaluate(() => {
    const hs = Array.from(document.querySelectorAll('.lang-en .article-body h2'));
    const a = hs.find(x => x.textContent.trim().toLowerCase() === 'our methodology');
    const b = hs.find(x => /^sources$/i.test(x.textContent.trim()));
    if (!a || !b) return null;
    const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
    // 注意：H2 有 margin:36px 0 12px，getBoundingClientRect 不含 margin，
    // 顶部要额外让开（实测 -16 会把 H2 裁掉，标题跑到裁剪线之上）。
    return { x: 0, y: Math.max(0, Math.round(window.scrollY + ra.top - 90)),
             width: document.documentElement.clientWidth,
             height: Math.round(rb.bottom - ra.top + 120),
             dbg: { scrollY: Math.round(window.scrollY), h2top: Math.round(ra.top),
                    h2text: a.textContent.trim() } };
  });
  if (rect) {
    console.log(`  实测坐标：scrollY=${rect.dbg.scrollY} h2.top=${rect.dbg.h2top} clip.y=${rect.y}`);
    await p1.screenshot({ path: `${OUT}/blog_methodology_sources_desktop_20261002.png`,
                          fullPage: true, clip: rect });
    console.log(`✓ 桌面 方法论+来源段截图  ${rect.width}×${rect.height}`);
  } else {
    console.log('✗ 未定位到方法论/来源段');
  }
  await p1.close();

  // ② 移动：reformer 页方法论段
  const m = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const p2 = await m.newPage();
  await p2.goto(`${BASE}/blog/pilates-reformer-buyers-guide.html`, { waitUntil: 'load' });
  await warmLazy(p2);
  await p2.evaluate(() => {
    const h = Array.from(document.querySelectorAll('.lang-en .article-body h2'))
      .find(x => x.textContent.trim().toLowerCase() === 'our methodology');
    if (h) h.scrollIntoView({ block: 'start' });
  });
  await p2.waitForTimeout(600);
  await p2.screenshot({ path: `${OUT}/blog_methodology_mobile_20261002.png` });
  console.log('✓ 移动 方法论段截图');

  await browser.close();
})();
