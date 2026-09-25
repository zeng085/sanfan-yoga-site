/**
 * 全站溢出扫描（本轮改动页面）—— 2026-09-25
 *
 * 判据（收紧，避免误报）：
 *   1. 页面级横向溢出：max(html.scrollWidth, body.scrollWidth) - html.clientWidth > 1
 *   2. 真的能横向滚动：scrollTo(9999,0) 后 window.scrollX > 0
 *   3. 改动点元素超出自身父容器 > 1.5px
 *   ⚠️ 不把「元素超出视口」当失败 —— 表格等元素本身是可滚动的，内部 rect 超出
 *      不代表布局坏了（本轮已实测 de 版表格即为既有可滚动形态）。
 *
 * 页面源：git diff 的改动 HTML；视口：默认 390（最易溢出），可传 --vp=1280
 */
const { chromium } = require('playwright');
const { execSync } = require('child_process');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const BASE = 'http://127.0.0.1:8851';
const vpArg = process.argv.find(a => a.startsWith('--vp='));
const VW = vpArg ? parseInt(vpArg.split('=')[1], 10) : 390;
const limitArg = process.argv.find(a => a.startsWith('--limit='));
const LIMIT = limitArg ? parseInt(limitArg.split('=')[1], 10) : 0;

const POINTS = [
  { name: 'cat-title', sel: '.cat-head .cat-title' },
  { name: 'pd-specs-h2', sel: '.pd-specs h2' },
  { name: 'faq-cat', sel: '.faq-cat' },
  { name: 'pc-body-h2', sel: '.pc-body h2' },
];

function changedHtml() {
  const out = execSync('git diff --no-renames --name-only', { cwd: ROOT, maxBuffer: 1 << 28 })
    .toString().split('\n').filter(f => f.endsWith('.html'));
  return out;
}

const probe = (POINTS) => {
  const de = document.documentElement, bd = document.body;
  // 是否真能横向滚动（比 scrollWidth 更硬）
  const before = window.scrollX;
  window.scrollTo(9999, 0);
  const canScrollX = window.scrollX > 0;
  window.scrollTo(before, window.scrollY);

  const res = {
    pageOver: Math.max(de.scrollWidth, bd.scrollWidth) - de.clientWidth,
    canScrollX,
    pts: {},
  };
  for (const pt of POINTS) {
    const els = [...document.querySelectorAll(pt.sel)];
    if (!els.length) continue;
    const el = els[0], parent = el.parentElement;
    const r = el.getBoundingClientRect(), pr = parent.getBoundingClientRect();
    res.pts[pt.name] = {
      n: els.length,
      overRight: Math.round(r.right - pr.right),
      w: Math.round(r.width),
      txt: el.textContent.trim().slice(0, 20),
    };
  }
  return res;
};

(async () => {
  let files = changedHtml();
  if (LIMIT) files = files.slice(0, LIMIT);
  console.log('=== 全站溢出扫描 ===');
  console.log('视口宽度 %d | 待检页面 %d', VW, files.length);

  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: VW, height: 900 } });
  const page = await ctx.newPage();
  const fails = [], softs = [];
  let n = 0, t0 = Date.now();

  for (const f of files) {
    const url = BASE + '/' + f;
    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 10000 });
      await page.waitForTimeout(90);
      const r = await page.evaluate(probe, POINTS);
      n++;
      if (r.pageOver > 1 || r.canScrollX) {
        fails.push(`${f} 页面横向溢出 ${r.pageOver}px, 可滚动=${r.canScrollX}`);
      }
      for (const [k, v] of Object.entries(r.pts)) {
        if (v.overRight > 1.5) softs.push(`${f} ${k} 超出父容器 ${v.overRight}px (w=${v.w}, "${v.txt}")`);
      }
    } catch (e) {
      fails.push(`${f} 打开失败: ${String(e.message).slice(0, 50)}`);
    }
    if (n % 120 === 0) console.log('   ...已检 %d 页 (%ds)', n, Math.round((Date.now() - t0) / 1000));
  }

  console.log('');
  console.log('已检 %d 页，用时 %ds', n, Math.round((Date.now() - t0) / 1000));
  console.log('【页面级横向溢出】%d 处', fails.length);
  fails.slice(0, 25).forEach(x => console.log('   ❌', x));
  console.log('【改动点超出父容器】%d 处', softs.length);
  softs.slice(0, 25).forEach(x => console.log('   ⚠️', x));
  await browser.close();
})();
