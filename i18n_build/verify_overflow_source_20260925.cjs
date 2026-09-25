/**
 * 17 处「页面级横向溢出」的来源判定 —— HEAD 版 vs 当前版 A/B
 * 做法：把 HEAD 版本导出成同目录新文件（相对路径不变），同判据对比。
 * 若两版数值相同 → 既有问题，与本轮改动无关。
 */
const { chromium } = require('playwright');
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const BASE = 'http://127.0.0.1:8851';

const SAMPLES = [
  ['blog/yoga-mat-materials.html',              'EN 文章页（A5 + 版本号）'],
  ['de/about.html',                             'de about（仅版本号）'],
  ['fr/contact.html',                           'fr contact（仅版本号）'],
  ['de/blog/yoga-mat-materials.html',           'de 文章页（仅版本号）'],
];

const probe = () => {
  const de = document.documentElement, bd = document.body;
  window.scrollTo(9999, 0);
  const canScroll = window.scrollX > 0;
  window.scrollTo(0, 0);
  // 找出被裁的最右元素（用于定位是谁撑宽的）
  let maxRight = 0, owner = '';
  for (const el of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const r = el.getBoundingClientRect();
    if (r.right > maxRight) { maxRight = r.right; owner = el.tagName.toLowerCase() + '.' + (String(el.className).split(' ')[0] || '-'); }
  }
  return {
    pageOver: Math.max(de.scrollWidth, bd.scrollWidth) - de.clientWidth,
    canScroll,
    maxRight: Math.round(maxRight),
    owner,
    hasTable: document.querySelectorAll('table').length,
  };
};

(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 } });
  const page = await ctx.newPage();
  const rows = [];

  for (const [rel, label] of SAMPLES) {
    const dir = path.dirname(path.join(ROOT, rel));
    const base = path.basename(rel, '.html');
    const abName = '_ab_head_' + base + '.html';
    const abPath = path.join(dir, abName);
    // 导出 HEAD 版
    fs.writeFileSync(abPath, execSync('git show HEAD:' + rel, { cwd: ROOT, maxBuffer: 1 << 26 }));

    const cur = await load(page, BASE + '/' + rel);
    const head = await load(page, BASE + '/' + path.relative(ROOT, abPath));
    fs.unlinkSync(abPath);

    const same = cur.pageOver === head.pageOver && cur.maxRight === head.maxRight;
    rows.push({ label, rel, cur, head, same });
  }

  console.log('=== 17 处溢出的来源判定（HEAD vs 当前）===');
  for (const r of rows) {
    console.log('── %s  [%s]', r.label, r.rel);
    console.log('   当前版: 溢出=%dpx 最右元素=%d(%s) 表格数=%d',
      r.cur.pageOver, r.cur.maxRight, r.cur.owner, r.cur.hasTable);
    console.log('   HEAD版: 溢出=%dpx 最右元素=%d(%s) 表格数=%d',
      r.head.pageOver, r.head.maxRight, r.head.owner, r.head.hasTable);
    console.log('   → %s', r.same ? '两版完全一致 ⇒ 既有问题，与本轮改动无关 ✓'
      : '⚠️ 两版不同 ⇒ 需进一步定位');
  }
  await b.close();

  async function load(pg, url) {
    await pg.goto(url, { waitUntil: 'domcontentloaded', timeout: 12000 });
    await pg.waitForTimeout(220);
    return pg.evaluate(probe);
  }
})();
