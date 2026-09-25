#!/usr/bin/env node
/**
 * 17 处移动端横向溢出：既有 or 本轮引入？—— A/B 实证（2026-09-25）
 *
 * 纪律：禁止用「我没改这里」推断。做法是把 `git show HEAD:<file>` 导出到**同目录**
 * 新文件（相对路径 ../assets 不变），用**同一探针**测同一个值，两者一致才算既有。
 *
 * 用法：node ab_overflow_20260925.cjs
 */
const { chromium } = require('playwright');
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const BASE = 'http://127.0.0.1:8851';
const VW = 390;

const FILES = [
  'blog/private-label-yoga-mats.html', 'blog/yoga-mat-materials.html', 'de/about.html',
  'de/blog/moq-explained.html', 'de/blog/private-label-yoga-mats.html', 'de/blog/tpe-vs-pu.html',
  'de/blog/yoga-mat-materials.html', 'de/blog/yoga-mat-spec-guide.html',
  'es/blog/private-label-yoga-mats.html', 'es/blog/yoga-mat-materials.html',
  'fr/blog/moq-explained.html', 'fr/blog/private-label-yoga-mats.html',
  'fr/blog/yoga-mat-materials.html', 'fr/contact.html',
  'it/blog/moq-explained.html', 'it/blog/private-label-yoga-mats.html',
  'it/blog/yoga-mat-materials.html',
];

const probe = () => {
  const de = document.documentElement, bd = document.body;
  const before = window.scrollX;
  window.scrollTo(9999, 0);
  const canScrollX = window.scrollX > 0;
  window.scrollTo(before, window.scrollY);
  return Math.max(de.scrollWidth, bd.scrollWidth) - de.clientWidth;
};

const abFiles = [];
function exportHead(rel) {
  const txt = execSync(`git show "HEAD:${rel}"`, { cwd: ROOT, maxBuffer: 1 << 28 }).toString();
  const dir = path.join(ROOT, path.dirname(rel));
  const base = path.basename(rel);
  const out = path.join(dir, `__ab__${base}`);
  fs.writeFileSync(out, txt);
  abFiles.push(out);
  return path.relative(ROOT, out).split(path.sep).join('/');
}
function cleanup() {
  for (const f of abFiles) { try { fs.unlinkSync(f); } catch (e) {} }
}

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: VW, height: 900 } });
  const page = await ctx.newPage();
  const rows = [];
  for (const rel of FILES) {
    let abRel;
    try { abRel = exportHead(rel); } catch (e) { rows.push([rel, '导出失败', '', '']); continue; }
    const now = await page.goto(`${BASE}/${rel}`, { waitUntil: 'domcontentloaded' }).then(
      () => page.waitForTimeout(90)).then(() => page.evaluate(probe)).catch(() => null);
    const was = await page.goto(`${BASE}/${abRel}`, { waitUntil: 'domcontentloaded' }).then(
      () => page.waitForTimeout(90)).then(() => page.evaluate(probe)).catch(() => null);
    rows.push([rel, was, now, was === now ? '一致→既有' : '★不一致→本轮引入']);
  }
  await browser.close();
  cleanup();

  console.log(`视口 ${VW}px | A/B 文件已清理\n`);
  console.log('%-46s %10s %10s  %s'.replace(/%-?\d+s/g, m => m), '');
  console.log('文件'.padEnd(46) + 'HEAD(既有)'.padStart(10) + '现在'.padStart(10) + '  判定');
  console.log('-'.repeat(92));
  let bad = 0;
  for (const [f, was, now, verdict] of rows) {
    if (!String(verdict).startsWith('一致')) bad++;
    console.log(f.padEnd(46) + String(was).padStart(10) + String(now).padStart(10) + '  ' + verdict);
  }
  console.log('\n合计 %d 处 | 一致（既有）%d | 新增 %d', rows.length, rows.length - bad, bad);
  process.exit(bad ? 1 : 0);
})();
