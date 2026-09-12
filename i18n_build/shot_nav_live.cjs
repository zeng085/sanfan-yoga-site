/**
 * 本地实拍：导航 Mega Menu / 全站搜索 / L2 分组分类条 / 场景页 / 材质页。
 * 用 file:// 打开本地页面，因此这些截图就是"改动后的真实样子"，不是设计稿。
 *
 * 运行：
 *   NODE_PATH=/Users/mac-zlg/.workbuddy/binaries/node/workspace/node_modules \
 *   node i18n_build/shot_nav_live.cjs
 */
const {chromium} = require('playwright');
const path = require('path');
const fs = require('fs');

const ROOT = process.cwd();
const OUT = path.join(ROOT, 'outputs', 'nav-preview');
// 默认走 http://127.0.0.1:8848（先起 `python3 -m http.server 8848`）。
// 用 file:// 也能跑，但 file:// 下 Chrome 会在 search 缩略图 / 预取脚本上误报，
// 而且中文搜索结果里的图片路径行为与线上不一致 —— 验收一律用 http。
const BASE = process.env.PREVIEW_BASE || 'http://127.0.0.1:8848';
const U = f => BASE + '/' + f;

(async () => {
  fs.mkdirSync(OUT, {recursive: true});
  const b = await chromium.launch();

  // ---------- 桌面端 ----------
  const p = await b.newPage({viewport: {width: 1440, height: 900}, deviceScaleFactor: 2});

  // 1) 首页场景入口区 + 材质引导
  await p.goto(U('index.html'), {waitUntil: 'load'});
  await p.waitForTimeout(2500);
  const appY = await p.evaluate(() => {
    const el = document.querySelector('#applications');
    return el ? Math.round(el.getBoundingClientRect().top + window.scrollY) : 0;
  });
  await p.evaluate(y => window.scrollTo(0, y - 10), appY);
  await p.waitForTimeout(500);
  await p.screenshot({path: path.join(OUT, '01-home-applications.png')});
  console.log('01 首页场景区 ok y=', appY);

  // 2) Mega Menu（悬停 Products）
  await p.evaluate(() => window.scrollTo(0, 0));
  await p.waitForTimeout(300);
  await p.hover('.nav-links a[data-i18n="nav.products"]');
  await p.waitForTimeout(1200);
  await p.screenshot({path: path.join(OUT, '02-mega-menu.png'), clip: {x: 0, y: 0, width: 1440, height: 760}});
  console.log('02 mega menu ok');

  // 3) Mega Menu 中文态
  await p.evaluate(() => {
    const btn = document.querySelector('.lang-menu button[data-setlang="zh"]');
    if (btn) btn.click();
  });
  await p.waitForTimeout(700);
  await p.mouse.move(700, 500);
  await p.waitForTimeout(300);
  await p.hover('.nav-links a[data-i18n="nav.products"]');
  await p.waitForTimeout(800);
  await p.screenshot({path: path.join(OUT, '03-mega-menu-zh.png'), clip: {x: 0, y: 0, width: 1440, height: 760}});
  console.log('03 mega menu 中文 ok');

  // 4) 搜索：中文查询「泡沫轴」
  await p.mouse.move(700, 620);
  await p.waitForTimeout(400);
  await p.click('.sr-btn');
  await p.waitForTimeout(1200);
  await p.fill('.sr-input', '泡沫轴');
  await p.waitForTimeout(600);
  await p.screenshot({path: path.join(OUT, '04-search-zh.png'), clip: {x: 0, y: 0, width: 1440, height: 760}});
  const zhHits = await p.$$eval('.sr-item .sr-t', els => els.slice(0, 5).map(e => e.textContent));
  console.log('04 搜索「泡沫轴」ok →', zhHits.join(' | '));

  // 5) 搜索：英文查询 hot yoga
  await p.fill('.sr-input', 'hot yoga');
  await p.waitForTimeout(600);
  await p.screenshot({path: path.join(OUT, '05-search-en.png'), clip: {x: 0, y: 0, width: 1440, height: 760}});
  const enHits = await p.$$eval('.sr-item .sr-t', els => els.slice(0, 5).map(e => e.textContent));
  console.log('05 搜索「hot yoga」ok →', enHits.join(' | '));
  await p.keyboard.press('Escape');
  await p.waitForTimeout(300);

  // 6) 分类页：分组分类条 + 场景快捷行
  await p.goto(U('jump-ropes.html'), {waitUntil: 'load'});
  await p.waitForTimeout(1500);
  await p.screenshot({path: path.join(OUT, '06-cat-bar.png'), clip: {x: 0, y: 0, width: 1440, height: 980}});
  console.log('06 分类页引导条 ok');

  // 7) 场景落地页
  await p.goto(U('applications/recovery-physio.html'), {waitUntil: 'load'});
  await p.waitForTimeout(1800);
  await p.screenshot({path: path.join(OUT, '07-app-page-hero.png'), clip: {x: 0, y: 0, width: 1440, height: 1000}});
  const kitY = await p.evaluate(() => Math.round(document.querySelector('#kit').getBoundingClientRect().top + window.scrollY));
  await p.evaluate(y => window.scrollTo(0, y - 20), kitY);
  await p.waitForTimeout(500);
  await p.screenshot({path: path.join(OUT, '08-app-kit-table.png')});
  console.log('07/08 场景页 ok');

  // 9) 材质对比表
  await p.goto(U('materials.html'), {waitUntil: 'load'});
  await p.waitForTimeout(1500);
  const matY = await p.evaluate(() => Math.round(document.querySelector('#compare').getBoundingClientRect().top + window.scrollY));
  await p.evaluate(y => window.scrollTo(0, y - 20), matY);
  await p.waitForTimeout(500);
  await p.screenshot({path: path.join(OUT, '09-materials-table.png')});
  await p.evaluate(() => window.scrollTo(0, 0));
  await p.waitForTimeout(400);
  await p.screenshot({path: path.join(OUT, '10-materials-top.png')});
  console.log('09/10 材质页 ok');

  await p.close();

  // ---------- 移动端 ----------
  const m = await b.newPage({viewport: {width: 390, height: 844}, deviceScaleFactor: 2, isMobile: true});
  await m.goto(U('index.html'), {waitUntil: 'load'});
  await m.waitForTimeout(2500);
  const my = await m.evaluate(() => Math.round(document.querySelector('#applications').getBoundingClientRect().top + window.scrollY));
  await m.evaluate(y => window.scrollTo(0, y - 10), my);
  await m.waitForTimeout(500);
  await m.screenshot({path: path.join(OUT, '11-mobile-apps.png')});
  await m.evaluate(() => window.scrollTo(0, 0));
  await m.waitForTimeout(300);
  await m.screenshot({path: path.join(OUT, '12-mobile-header.png'), clip: {x: 0, y: 0, width: 390, height: 300}});
  await m.click('.menu-toggle');
  await m.waitForTimeout(500);
  await m.screenshot({path: path.join(OUT, '13-mobile-menu.png'), clip: {x: 0, y: 0, width: 390, height: 500}});
  console.log('11/12/13 移动端 ok');

  await b.close();
  console.log('\n全部截图 →', OUT);
})();
