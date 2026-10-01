#!/usr/bin/env node
/**
 * 普拉提板块「画册重构」全量验收
 *
 * 覆盖 9 个页面 × 双视口，检查：
 *   1. HTTP 200、无 4xx/5xx、无控制台报错
 *   2. 横向溢出（documentElement.scrollWidth > clientWidth）
 *   3. 元素越界（排除可横滚容器 .pl-spec-wrap 内部的 table）
 *   4. 画册图全部加载成功（naturalWidth > 0）—— lazy 图必须先滚动预热
 *   5. 计数对账：cat-unit / model-card 与数据一致
 *   6. 灯箱：点图打开 → Esc 关闭（本轮新增交互，必须实测）
 *   7. 中文态 show-zh 正常、无掉行
 *
 * 用法：BASE=http://127.0.0.1:8866 node verify_pilates_rebuild_20261001.cjs
 */
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE = process.env.BASE || 'http://127.0.0.1:8866';
const OUT = path.resolve(__dirname, '..', 'outputs', 'pilates_rebuild_20261001');
fs.mkdirSync(OUT, { recursive: true });

// 进度实时落盘：stdout 重定向到文件时 Node 是块缓冲（4KB），
// 脚本卡住时 tail 什么都看不到，等于没有进度可言 —— 上一次就是这样
// 白等了 19 分钟才知道卡在第二页。
const PROGRESS = '/tmp/rebuild_verify_progress.log';
try { fs.unlinkSync(PROGRESS); } catch (e) {}
const _log = console.log.bind(console);
console.log = (...a) => {
  const s = a.map((x) => (typeof x === 'string' ? x : JSON.stringify(x))).join(' ');
  _log(s);
  try { fs.appendFileSync(PROGRESS, s + '\n'); } catch (e) {}
};

// --only=<子串> 只跑匹配的页面，便于分批判定（reformer 页很重，单独跑）
const ONLY = (process.argv.find((x) => x.startsWith('--only=')) || '').split('=')[1];

// [路径, 期望 cat-unit 数, 期望 model-card 数, 截图目标选择器, 截图名]
const PAGES = [
  ['/pilates/index.html', 0, 0, '#lines', 'index-lines'],
  ['/pilates/pilates-reformer.html', 27, 46, '#catalogue-pages .cat-unit', 'reformer-catunit'],
  ['/pilates/pilates-reformer-tower.html', 7, 11, '#catalogue-pages .cat-unit', 'tower-catunit'],
  ['/pilates/pilates-wunda-chair.html', 4, 9, '#catalogue-pages .cat-unit', 'chair-catunit'],
  ['/pilates/pilates-cadillac.html', 2, 4, '#catalogue-pages .cat-unit', 'cadillac-catunit'],
  ['/pilates/pilates-ladder-barrel.html', 3, 7, '#catalog', 'ladderbarrel-catalog'],
  ['/pilates/pilates-specialty.html', 2, 3, '#models-compared', 'specialty-table'],
  ['/pilates/pilates-spine-corrector.html', 0, 0, '#catalog', 'spine-catalog'],
  ['/pilates/pilates-studio-set.html', 0, 0, '#what-we-need', 'studioset-checklist'],
];
if (ONLY) PAGES.splice(0, PAGES.length, ...PAGES.filter((p) => p[0].includes(ONLY)));

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function warm(page) {
  // 第一遍：按真实用户行为滚动预热 lazy 图（步长 400 / 间隔 130ms —— 600/55 太快，
  // IntersectionObserver 回调来不及触发，reformer 页 31 张图只加载出 10 张）
  await page.evaluate(async () => {
    const h = document.documentElement.scrollHeight;
    for (let y = 0; y < h; y += 400) { window.scrollTo(0, y); await new Promise((r) => setTimeout(r, 130)); }
    window.scrollTo(0, 0);
  });
  try { await page.waitForLoadState('networkidle', { timeout: 8000 }); } catch (e) {}
  // 第二遍：把仍未加载的 lazy 图强制转 eager。
  //   目的：区分「lazy 还没轮到加载」（正常）与「图真的 404 / 解码失败」（真缺陷）。
  //   只靠滚动预热分不清两者，会把它误报成破图。
  await page.evaluate(() => {
    document.querySelectorAll('img[loading="lazy"]').forEach((i) => i.setAttribute('loading', 'eager'));
  });
  // 再等所有 img 解码完成。
  // ⚠️ 必须带超时。reformer 页 30 张图里 27 张是 lazy 的画册原页，只要有一张
  //    滚过之后 load / error 都没触发，Promise.all 就永挂 ——
  //    实测把整个脚本卡死在第二页 19 分钟（log 停在第一页无任何输出）。
  await page.evaluate(async () => {
    const imgs = [...document.images];
    const wait = (i) => (i.complete && i.naturalWidth)
      ? Promise.resolve()
      : new Promise((res) => {
          i.addEventListener('load', res, { once: true });
          i.addEventListener('error', res, { once: true });
        });
    await Promise.race([
      Promise.all(imgs.map(wait)),
      new Promise((r) => setTimeout(r, 8000)),
    ]);
  });
  await sleep(400);
}

async function probe(page, label) {
  return await page.evaluate((lbl) => {
    const de = document.documentElement;
    const out = {
      label: lbl,
      hOverflow: de.scrollWidth - de.clientWidth,
      offenders: [],
      images: { total: 0, loaded: 0, broken: [] },
      catUnits: document.querySelectorAll('.cat-unit').length,
      modelCards: document.querySelectorAll('.model-card').length,
      langEn: document.querySelectorAll('.lang-en').length,
      langZh: document.querySelectorAll('.lang-zh').length,
      showZh: de.classList.contains('show-zh'),
      lbExists: !!document.querySelector('.lb'),
    };
    const bw = de.clientWidth;
    // 可横滚容器内部的不算越界
    const scrollable = (el) => {
      let p = el.parentElement;
      while (p) {
        const ov = getComputedStyle(p).overflowX;
        if (ov === 'auto' || ov === 'scroll') return true;
        p = p.parentElement;
      }
      return false;
    };
    document.querySelectorAll('section, .cat-unit, .model-card, .line-card, .pl-card, table').forEach((el) => {
      const r = el.getBoundingClientRect();
      if (r.width > bw + 1 || r.right > bw + 1) {
        if (scrollable(el)) return;
        out.offenders.push({
          tag: el.tagName, cls: (el.className || '').toString().slice(0, 46),
          w: Math.round(r.width), right: Math.round(r.right),
        });
      }
    });
    document.querySelectorAll('img').forEach((i) => {
      out.images.total++;
      if (i.naturalWidth > 0) out.images.loaded++;
      else out.images.broken.push((i.getAttribute('src') || '').slice(0, 80));
    });
    return out;
  }, label);
}

(async () => {
  const browser = await chromium.launch();
  const report = { desktop: [], mobile: [], lightbox: null, zh: [] };
  const problems = [];

  // ---------------- 桌面 ----------------
  for (const [url, expCat, expCard, sel, shotName] of PAGES) {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();
    const errs = [];
    page.on('response', (r) => { if (r.status() >= 400 && !/google|gtag|analytics/.test(r.url())) errs.push(r.status() + ' ' + r.url().slice(0, 90)); });
    page.on('pageerror', (e) => errs.push('JS: ' + e.message.slice(0, 120)));
    const resp = await page.goto(BASE + url, { waitUntil: 'domcontentloaded' });
    await warm(page);
    const r = await probe(page, 'desktop ' + url);
    r.status = resp.status();
    r.errors = errs;
    report.desktop.push(r);

    if (r.status !== 200) problems.push(`${url} HTTP ${r.status}`);
    if (r.hOverflow > 1) problems.push(`${url} 桌面横向溢出 ${r.hOverflow}px`);
    if (r.offenders.length) problems.push(`${url} 桌面越界 ${r.offenders.length} 个: ${JSON.stringify(r.offenders.slice(0, 3))}`);
    if (r.images.broken.length) problems.push(`${url} 破图 ${r.images.broken.length}: ${r.images.broken.slice(0, 3).join(' | ')}`);
    if (r.catUnits !== expCat) problems.push(`${url} cat-unit ${r.catUnits} ≠ ${expCat}`);
    if (r.modelCards !== expCard) problems.push(`${url} model-card ${r.modelCards} ≠ ${expCard}`);
    if (r.langEn !== r.langZh) problems.push(`${url} 双语不配对 ${r.langEn}/${r.langZh}`);
    if (errs.length) problems.push(`${url} 请求/JS 错误: ${errs.slice(0, 3).join(' | ')}`);

    console.log(`[桌面] ${url.padEnd(42)} HTTP ${r.status} 溢出 ${r.hOverflow} 越界 ${r.offenders.length} 图 ${r.images.loaded}/${r.images.total} catUnit ${r.catUnits}/${expCat} card ${r.modelCards}/${expCard}`);

    if (sel && shotName) {
      const el = await page.$(sel);
      if (el) {
        try { await el.screenshot({ path: path.join(OUT, shotName + '-desktop.jpg'), type: 'jpeg', quality: 82 }); }
        catch (e) { console.log('   截图失败 ' + sel + ': ' + e.message.slice(0, 80)); }
      } else console.log('   ⚠ 选择器未命中: ' + sel);
    }
    await ctx.close();
  }

  // ---------------- 移动端 ----------------
  for (const [url, expCat, expCard, sel, shotName] of PAGES) {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
    const page = await ctx.newPage();
    await page.goto(BASE + url, { waitUntil: 'domcontentloaded' });
    await warm(page);
    const r = await probe(page, 'mobile ' + url);
    report.mobile.push(r);
    if (r.hOverflow > 1) problems.push(`${url} 移动端横向溢出 ${r.hOverflow}px`);
    if (r.offenders.length) problems.push(`${url} 移动端越界 ${r.offenders.length} 个: ${JSON.stringify(r.offenders.slice(0, 3))}`);
    if (r.images.broken.length) problems.push(`${url} 移动端破图 ${r.images.broken.length}`);
    console.log(`[移动] ${url.padEnd(42)} 溢出 ${r.hOverflow} 越界 ${r.offenders.length} 图 ${r.images.loaded}/${r.images.total}`);
    if (sel && shotName && ['index-lines', 'reformer-catunit', 'spine-catalog'].includes(shotName)) {
      const el = await page.$(sel);
      if (el) { try { await el.screenshot({ path: path.join(OUT, shotName + '-mobile.jpg'), type: 'jpeg', quality: 82 }); } catch (e) {} }
    }
    await ctx.close();
  }

  // ---------------- 灯箱交互（本轮新增，必须实测） ----------------
  {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();
    await page.goto(BASE + '/pilates/pilates-cadillac.html', { waitUntil: 'domcontentloaded' });
    await warm(page);
    const before = await page.evaluate(() => !!document.querySelector('.lb.is-open'));
    await page.evaluate(() => { const a = document.querySelector('.cat-zoom'); a.scrollIntoView(); });
    await sleep(300);
    // (a) 点「放大查看」链接
    await page.click('.cat-zoom');
    await sleep(500);
    const opened = await page.evaluate(() => {
      const lb = document.querySelector('.lb');
      const im = lb && lb.querySelector('img');
      return { open: !!(lb && lb.classList.contains('is-open')), src: im ? im.getAttribute('src') : null,
               nat: im ? im.naturalWidth : 0, bodyLocked: document.body.classList.contains('lb-open') };
    });
    await page.screenshot({ path: path.join(OUT, 'lightbox-open.jpg'), type: 'jpeg', quality: 82 });
    // (b) Esc 关闭
    await page.keyboard.press('Escape');
    await sleep(350);
    const afterEsc = await page.evaluate(() => ({
      open: !!document.querySelector('.lb.is-open'),
      bodyLocked: document.body.classList.contains('lb-open'),
      scrollY: window.scrollY,
    }));
    // (c) 点图本身
    await page.evaluate(() => { const i = document.querySelector('.cat-fig img'); i.scrollIntoView({ block: 'center' }); });
    await sleep(300);
    await page.click('.cat-fig img');
    await sleep(450);
    const openedByImg = await page.evaluate(() => !!document.querySelector('.lb.is-open'));
    // (d) 点遮罩关闭
    await page.mouse.click(20, 20);
    await sleep(350);
    const afterOverlay = await page.evaluate(() => !!document.querySelector('.lb.is-open'));

    report.lightbox = { before, opened, afterEsc, openedByImg, afterOverlay };
    if (before) problems.push('灯箱初始就是打开状态');
    if (!opened.open) problems.push('灯箱：点「放大查看」未打开');
    if (opened.open && !opened.nat) problems.push('灯箱：打开但图未加载 naturalWidth=0');
    if (!opened.bodyLocked) problems.push('灯箱：打开后 body 未锁滚动');
    if (afterEsc.open) problems.push('灯箱：Esc 未关闭');
    if (afterEsc.bodyLocked) problems.push('灯箱：关闭后 body 未解锁滚动');
    if (!openedByImg) problems.push('灯箱：点图片本身未打开');
    if (afterOverlay) problems.push('灯箱：点遮罩未关闭');
    console.log('\n[灯箱] ' + JSON.stringify(report.lightbox));
    await ctx.close();
  }

  // ---------------- 中文态 ----------------
  for (const [url] of PAGES.filter((p) => ['/pilates/index.html', '/pilates/pilates-wunda-chair.html', '/pilates/pilates-spine-corrector.html'].includes(p[0]))) {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();
    await page.goto(BASE + url, { waitUntil: 'domcontentloaded' });
    await page.evaluate(() => localStorage.setItem('siteLang', 'zh'));
    await page.reload({ waitUntil: 'domcontentloaded' });
    await warm(page);
    const zh = await page.evaluate(() => {
      const vis = (sel) => [...document.querySelectorAll(sel)].filter((e) => e.offsetParent !== null).length;
      return {
        showZh: document.documentElement.classList.contains('show-zh'),
        langZhVisible: vis('.lang-zh'), langEnVisible: vis('.lang-en'),
        hiddenZh: [...document.querySelectorAll('.lang-zh')].length - vis('.lang-zh'),
      };
    });
    report.zh.push({ url, ...zh });
    // 中文态下不应有可见的 .lang-en（设计上中文态隐藏英文）
    if (!zh.showZh) problems.push(`${url} 中文态 show-zh 未生效`);
    if (zh.langEnVisible > 0) problems.push(`${url} 中文态仍有 ${zh.langEnVisible} 处英文可见`);
    console.log(`[中文] ${url.padEnd(42)} show-zh=${zh.showZh} 可见中文 ${zh.langZhVisible} / 隐藏 ${zh.hiddenZh} 可见英文 ${zh.langEnVisible}`);
    await ctx.close();
  }

  await browser.close();
  fs.writeFileSync(path.join(OUT, 'report.json'), JSON.stringify(report, null, 2), 'utf-8');

  console.log('\n' + '='.repeat(74));
  if (problems.length) {
    console.log(`✗ 发现 ${problems.length} 个问题：`);
    problems.forEach((p) => console.log('  · ' + p));
  } else {
    console.log('✓ 全部通过（桌面 9 页 / 移动 9 页 / 灯箱 6 项 / 中文 3 页）');
  }
  console.log('产物: ' + OUT);
  process.exit(problems.length ? 1 : 0);
})();
