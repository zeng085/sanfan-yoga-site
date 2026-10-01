#!/usr/bin/env node
/**
 * 2026 画册型号块 —— 浏览器渲染探针  2026-10-01
 *
 * 为什么必需（项目铁律 5）：
 *   源码审计归零 ≠ DOM 干净。`.cat-*` / `.model-card` 这套样式只加在 styles.css 里，
 *   页面是否真的排成两栏、图片是否真的解码成功、锚点是否真的能跳、窄屏是否溢出，
 *   静态读 HTML 全部看不出来 → 必须浏览器级实测，且**按视口分别查**。
 *   本探针首次运行就抓到一个真缺陷（19-F 卡片把两个空字段合并成句子说明，
 *   与同页总表的 `—` 口径矛盾），已修。
 *
 * 本文件自身踩过的 3 个坑（已修，改动前请勿"优化"掉）：
 *   1. `.cat-fig img` 带 loading="lazy" → 未进入视口的图 naturalWidth=0，
 *      会被误判为"解码失败"。修法：测量前先分步滚到底触发懒加载。
 *   2. 期望值 `dl 项数 >= 4` 是我拍脑袋写的，实际每卡 3 项 → 报假警。
 *      修法：改为 `dt === dd && dt >= 3`（每台至少 材质/包装/毛重 三行）。
 *   3. `wechat-qr.webp` 必然报失败：main.js 按**目录深度**推算相对路径
 *      （'../'.repeat(depth)），file:// 下算出的深度与线上不同 → 假失败。
 *      修法：起本地 HTTP 服务加载，与线上同构。
 *
 * 用法：直接跑，无需参数。返回码 0 = 全绿。
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const REL = 'pilates/pilates-ladder-barrel.html';
const MIME = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript',
  '.webp': 'image/webp', '.jpg': 'image/jpeg', '.png': 'image/png',
  '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.pdf': 'application/pdf',
  '.txt': 'text/plain', '.json': 'application/json' };

const VIEWPORTS = [
  { name: 'mobile-390', width: 390, height: 844, mobile: true },
  { name: 'desktop-1440', width: 1440, height: 900, mobile: false },
];

let fails = 0;
const report = (ok, label, extra) => {
  if (!ok) fails++;
  console.log(`  ${ok ? '✅' : '❌'} ${label}${extra ? '   ' + extra : ''}`);
};

function startServer() {
  const server = http.createServer((req, res) => {
    let p = decodeURIComponent(req.url.split('?')[0]);
    if (p === '/') p = '/' + REL;
    const f = path.join(ROOT, p);
    if (!f.startsWith(ROOT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) {
      res.writeHead(404); return res.end('404');
    }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/octet-stream' });
    fs.createReadStream(f).pipe(res);
  });
  return new Promise(r => server.listen(0, '127.0.0.1', () => r(server)));
}

(async () => {
  const server = await startServer();
  const BASE = `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch();

  for (const vp of VIEWPORTS) {
    console.log(`\n=== 视口 ${vp.name} (${vp.width}×${vp.height}) ===`);
    const ctx = await browser.newContext({
      viewport: { width: vp.width, height: vp.height },
      isMobile: vp.mobile, hasTouch: vp.mobile,
      deviceScaleFactor: vp.mobile ? 3 : 1,
    });
    const page = await ctx.newPage();
    // 只统计**本域**请求失败。第三方（GA 上报等）在离线/沙箱环境必然失败，
    // 与页面质量无关 —— 混在一起判会让探针常年报假警（"狼来了"）。
    const bad = [], thirdParty = [];
    const isLocal = u => u.startsWith(BASE);
    page.on('requestfailed', r => (isLocal(r.url()) ? bad : thirdParty)
      .push(r.url().replace(BASE, '').slice(0, 80)));
    page.on('response', r => {
      if (r.status() >= 400 && isLocal(r.url())) bad.push(`${r.url().replace(BASE, '')} → ${r.status()}`);
    });

    await page.goto(`${BASE}/${REL}`, { waitUntil: 'load' });
    await page.waitForTimeout(500);

    // 坑 3：先分步滚到底，触发所有 loading="lazy" 的图（否则误判解码失败）
    await page.evaluate(async () => {
      const step = window.innerHeight;
      for (let y = 0; y < document.body.scrollHeight; y += step) {
        window.scrollTo(0, y);
        await new Promise(r => setTimeout(r, 120));
      }
      window.scrollTo(0, 0);
    });
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(400);

    // 1) 结构计数
    const counts = await page.evaluate(() => ({
      catUnit: document.querySelectorAll('.cat-unit').length,
      modelCard: document.querySelectorAll('.model-card').length,
      catFig: document.querySelectorAll('.cat-fig').length,
    }));
    report(counts.catUnit === 3, `画册页块 .cat-unit = ${counts.catUnit}（期望 3）`);
    report(counts.modelCard === 7, `型号卡 .model-card = ${counts.modelCard}（期望 7）`);
    report(counts.catFig === 3, `画册图 .cat-fig = ${counts.catFig}（期望 3）`);

    // 2) 图片真实解码
    const imgs = await page.evaluate(() =>
      [...document.querySelectorAll('.cat-fig img')].map(i => ({
        src: i.getAttribute('src'), nat: i.naturalWidth, alt: i.getAttribute('alt') || '',
        w: Math.round(i.getBoundingClientRect().width),
      })));
    const broken = imgs.filter(i => !i.nat);
    report(broken.length === 0, `.cat-fig 图片解码 ${imgs.length - broken.length}/${imgs.length}`,
      broken.length ? broken.map(b => b.src).join(',') : imgs.map(i => `${i.w}px 宽`).join(' '));
    report(imgs.every(i => i.alt.trim()), `图片 alt 覆盖（缺 ${imgs.filter(i => !i.alt.trim()).length} 张）`);

    // 3) 锚点解析
    const anchors = await page.evaluate(() => {
      const ids = [...document.querySelectorAll('.model-card[id]')].map(e => e.id);
      const links = [...document.querySelectorAll('a[href^="#"]')]
        .map(a => a.getAttribute('href').slice(1)).filter(Boolean);
      return { ids, linkCount: links.length, dangling: links.filter(h => !document.getElementById(h)) };
    });
    report(anchors.ids.length === 7, `型号锚点 id ${anchors.ids.length} 个`);
    report(anchors.dangling.length === 0, `站内锚点全部可解析（${anchors.linkCount} 个）`,
      anchors.dangling.length ? '悬空: ' + anchors.dangling.join(',') : '');

    // 4) 横向溢出
    const ov = await page.evaluate(() => ({
      docW: document.documentElement.scrollWidth, winW: window.innerWidth }));
    report(ov.docW <= ov.winW + 1, `无横向溢出 doc=${ov.docW} win=${ov.winW}`
      + (ov.docW > ov.winW + 1 ? `  超出 ${ov.docW - ov.winW}px` : ''));

    // 5) 布局
    const layout = await page.evaluate(() => {
      const u = document.querySelector('.cat-unit');
      const cs = getComputedStyle(u);
      return { cols: cs.gridTemplateColumns, tracks: cs.gridTemplateColumns.split(' ').filter(Boolean).length,
        figPos: getComputedStyle(document.querySelector('.cat-fig')).position };
    });
    if (vp.mobile) {
      report(layout.tracks === 1, `.cat-unit 单栏（tracks=${layout.tracks}）`, layout.cols);
      report(layout.figPos === 'static', `.cat-fig 移动端不吸顶（${layout.figPos}）`);
    } else {
      report(layout.tracks === 2, `.cat-unit 两栏（tracks=${layout.tracks}）`, layout.cols);
      report(layout.figPos === 'sticky', `.cat-fig 桌面吸顶（${layout.figPos}）`);
    }

    // 6) 双语内联
    const lang = await page.evaluate(() => {
      const el = document.querySelector('.cat-fig figcaption .lang-zh');
      if (!el) return { none: true };
      const before = getComputedStyle(el).display;
      document.documentElement.classList.add('show-zh');
      const during = getComputedStyle(el).display;
      document.documentElement.classList.remove('show-zh');
      return { before, during };
    });
    if (lang.none) report(false, '.cat-fig figcaption 缺 .lang-zh 中文配对');
    else {
      report(lang.before === 'none', `EN 态 .lang-zh 隐藏（${lang.before}）`);
      report(lang.during === 'inline', `中文态 .lang-zh 内联（${lang.during}）—— 不撑行`);
    }

    // 7) 每张卡 dl 配对（坑 2：期望 3 项，不是 4 项）
    const cards = await page.evaluate(() =>
      [...document.querySelectorAll('.model-card')].map(c => ({
        id: c.id,
        dt: c.querySelectorAll('dl dt').length,
        dd: c.querySelectorAll('dl dd').length,
        labels: [...c.querySelectorAll('dl dt')].map(d => d.textContent.trim().split('画')[0].trim()),
      })));
    const badCards = cards.filter(c => c.dt !== c.dd || c.dt < 3);
    report(badCards.length === 0, `7 张卡 dl 均配对且 ≥3 项`,
      badCards.length ? JSON.stringify(badCards) : cards.map(c => c.dt).join(','));
    const merged = cards.filter(c => c.labels.some(l => /[\/]/.test(l)));
    report(merged.length === 0, `无合并标签（如 Material / weight）`,
      merged.length ? JSON.stringify(merged.map(c => c.labels)) : '');

    // 8) 空值必须是破折号 '—'（用户决策：画册未印就写 —）
    const dash = await page.evaluate(() => {
      const out = [];
      document.querySelectorAll('.model-card dl dd').forEach(d => {
        const t = d.textContent.trim();
        if (/not listed|未列/i.test(t)) out.push(t);
      });
      return out;
    });
    report(dash.length === 0, `无「未列」类句子说明（应为 —）`, dash.join(';'));

    // 9) tabular-nums
    const num = await page.evaluate(() => {
      const td = document.querySelector('table.pl-spec td:not(.note)');
      return td ? getComputedStyle(td).fontVariantNumeric : 'n/a';
    });
    report(String(num).includes('tabular-nums'), `规格表数字等宽（${num}）`);

    // 10) 资源请求（本域）
    report(bad.length === 0, `本域资源请求全部成功（${bad.length} 失败）`, bad.join(' ; '));
    if (thirdParty.length) console.log(`  ℹ️  第三方请求 ${thirdParty.length} 项未完成（离线环境正常，不计入判定）`);

    await page.screenshot({ path: path.join(ROOT, 'i18n_build/reports',
      `probe_catalog_${vp.name}_20261001.png`), fullPage: false });
    await ctx.close();
  }
  await browser.close();
  server.close();
  console.log(`\n${fails === 0 ? '✅ 全部通过' : `❌ ${fails} 项不符`}`);
  process.exit(fails === 0 ? 0 : 1);
})();
