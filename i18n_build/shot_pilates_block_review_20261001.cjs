/**
 * shot_pilates_block_review_20261001.cjs
 * 改版后的普拉提器械版块 —— 真实渲染确认 + 双视口体检
 *
 * 输出：
 *   outputs/pilates_block_review_20261001/
 *     desktop-full.jpg      桌面 1440 全页
 *     mobile-full.jpg       移动 390  全页
 *     catalog-desktop.jpg   画册原页型号区（新块）特写 桌面
 *     catalog-mobile.jpg    画册原页型号区（新块）特写 移动
 *     spec-desktop.jpg      规格总表 特写
 *     hero-desktop.jpg      首屏 特写
 *     report.json           测量：图片状态 / 横向溢出 / 导航 / 语言切换
 *
 * 用法：
 *   BASE=http://127.0.0.1:8866 NODE_PATH=<node_modules> node i18n_build/shot_pilates_block_review_20261001.cjs
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE = process.env.BASE || 'http://127.0.0.1:8866';
const PAGE = '/pilates/pilates-ladder-barrel.html';
const OUT = path.resolve(__dirname, '..', 'outputs', 'pilates_block_review_20261001');
fs.mkdirSync(OUT, { recursive: true });

/** GA 在本机无外网时会一直挂着 → 拦掉，避免 networkidle 卡死 */
async function blockGA(ctx) {
  await ctx.route(/google-analytics|googletagmanager/, (r) => r.abort());
}

/** 滚到底触发 lazy，再等所有 img decode 完成；用 documentElement.scrollHeight */
async function settle(page) {
  await page.evaluate(async () => {
    const de = document.documentElement;
    const H = () => de.scrollHeight;
    for (let y = 0; y < H(); y += 600) {
      window.scrollTo(0, y);
      await new Promise((r) => setTimeout(r, 45));
    }
    window.scrollTo(0, 0);
    await new Promise((r) => setTimeout(r, 260));
    await Promise.all([...document.images].map((im) => (im.complete ? 0 : im.decode().catch(() => 0))));
  });
  await page.waitForTimeout(400);
}

/** 关键测量：溢出用「真能横向滚」判定，不用 scrollWidth 单指标 */
const MEASURE = (vw) => {
  const de = document.documentElement;
  const q = (s) => document.querySelector(s);
  const rect = (el) => { if (!el) return null; const b = el.getBoundingClientRect(); return { l: Math.round(b.left), r: Math.round(b.right), w: Math.round(b.width), h: Math.round(b.height) }; };

  // 真能横滚吗
  const before = window.scrollX;
  window.scrollTo(9999, window.scrollY);
  const scrolledX = window.scrollX;
  window.scrollTo(before, window.scrollY);

  const imgs = [...document.images].map((im) => ({
    src: im.getAttribute('src'),
    natural: im.naturalWidth + 'x' + im.naturalHeight,
    rendered: Math.round(im.getBoundingClientRect().width) + 'x' + Math.round(im.getBoundingClientRect().height),
    broken: !im.complete || im.naturalWidth === 0,
  }));

  // 新增块内部：cat-unit 是否溢出其容器
  const units = [...document.querySelectorAll('.cat-unit')].map((u) => {
    const host = u.parentElement;
    const ub = u.getBoundingClientRect(), hb = host.getBoundingClientRect();
    return {
      id: u.id,
      overflowsHost: Math.round(ub.right - hb.right),
      figW: rect(u.querySelector('.cat-fig'))?.w,
      modelsW: rect(u.querySelector('.cat-models'))?.w,
    };
  });

  const cards = [...document.querySelectorAll('.model-card')].map((c) => {
    const p = c.parentElement.getBoundingClientRect(), cb = c.getBoundingClientRect();
    return { id: c.id, overflowsParent: Math.round(cb.right - p.right), w: Math.round(cb.width) };
  });

  const nav = q('.nav');
  const navLinks = q('.nav-links');
  const brand = q('.nav-brand');
  const acts = q('.nav-actions');
  const toggle = q('.menu-toggle');
  const navInfo = nav ? {
    toggleVisible: toggle ? getComputedStyle(toggle).display !== 'none' : null,
    linksHidden: navLinks ? getComputedStyle(navLinks).display === 'none' : null,
    linksWraps: navLinks ? [...navLinks.querySelectorAll(':scope > a, :scope > .nav-drop > a')]
      .filter((a) => a.getBoundingClientRect().height > 26).map((a) => a.textContent.trim()) : [],
    overlapBrand: (navLinks && brand && getComputedStyle(navLinks).display !== 'none')
      ? Math.round(navLinks.getBoundingClientRect().left - brand.getBoundingClientRect().right) : null,
    overlapActions: (navLinks && acts && getComputedStyle(navLinks).display !== 'none')
      ? Math.round(acts.getBoundingClientRect().left - navLinks.getBoundingClientRect().right) : null,
    height: Math.round(nav.getBoundingClientRect().height),
  } : null;

  // 页脚链接数（导航完整性）
  const footLinks = document.querySelectorAll('.footer a, footer a').length;

  return {
    vw,
    docScrollOverflow: de.scrollWidth - de.clientWidth,
    reallyScrollsX: scrolledX > 0,
    scrollHeight: de.scrollHeight,
    imgs, units, cards, nav: navInfo, footLinks,
    catUnits: document.querySelectorAll('.cat-unit').length,
    modelCards: document.querySelectorAll('.model-card').length,
    specRows: document.querySelectorAll('table.pl-spec tbody tr').length,
  };
};

(async () => {
  const browser = await chromium.launch();
  const report = { page: PAGE, shots: {}, runs: {} };

  for (const [name, vp] of [['desktop', { width: 1440, height: 900 }], ['mobile', { width: 390, height: 844 }]]) {
    const ctx = await browser.newContext({ viewport: vp, deviceScaleFactor: name === 'mobile' ? 2 : 1 });
    await blockGA(ctx);
    const page = await ctx.newPage();
    const errs = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text().slice(0, 160)); });
    page.on('pageerror', (e) => errs.push('pageerror: ' + e.message.slice(0, 160)));

    const failedReq = [];
    page.on('requestfailed', (r) => {
      const u = r.url();
      if (/google-analytics|googletagmanager|doubleclick/.test(u)) return;
      failedReq.push(u.replace(BASE, '') + ' :: ' + (r.failure()?.errorText || ''));
    });

    await page.goto(BASE + PAGE, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(400);
    await settle(page);

    report.runs[name] = { ...(await page.evaluate(MEASURE, vp.width)), consoleErrors: errs, failedRequests: failedReq };

    // 全页
    await page.screenshot({ path: path.join(OUT, `${name}-full.jpg`), fullPage: true, quality: 82, type: 'jpeg' });
    report.shots[`${name}-full`] = true;

    // 各区块特写
    const targets = [
      ['hero', '.pl-hero'],
      ['spec', '.pl-spec-wrap'],
      ['catalog', '#catalog'],
    ];
    for (const [label, sel] of targets) {
      const el = await page.$(sel);
      if (!el) continue;
      await el.scrollIntoViewIfNeeded();
      await page.waitForTimeout(220);
      await el.screenshot({ path: path.join(OUT, `${label}-${name}.jpg`), quality: 85, type: 'jpeg' });
      report.shots[`${label}-${name}`] = true;
    }

    // 中文态：画册区再截一张（验证双语内联没把 figcaption 弄断行）
    await page.evaluate(() => { localStorage.setItem('siteLang', 'zh'); });
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(400);
    await settle(page);
    const zhEl = await page.$('#catalog');
    if (zhEl) {
      await zhEl.scrollIntoViewIfNeeded();
      await page.waitForTimeout(220);
      await zhEl.screenshot({ path: path.join(OUT, `catalog-${name}-zh.jpg`), quality: 85, type: 'jpeg' });
      report.shots[`catalog-${name}-zh`] = true;
    }
    // 中文态下复核 figcaption 是否单行（「查看原图」不应掉行）
    report.runs[name].zhFigcaption = await page.evaluate(() => {
      const fc = document.querySelector('.cat-fig figcaption');
      if (!fc) return null;
      const lines = Math.round(fc.getBoundingClientRect().height / parseFloat(getComputedStyle(fc).lineHeight || '18'));
      return { height: Math.round(fc.getBoundingClientRect().height), approxLines: lines, text: fc.textContent.replace(/\s+/g, ' ').trim().slice(0, 80) };
    });
    // 语言切换后导航文案
    report.runs[name].navZhLabel = await page.evaluate(() => {
      const a = [...document.querySelectorAll('.nav-links > a')].find((x) => /pilates|普拉提/i.test(x.textContent));
      return a ? a.textContent.trim() : null;
    });

    await ctx.close();
  }

  fs.writeFileSync(path.join(OUT, 'report.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify({
    out: OUT,
    desktop: {
      docScrollOverflow: report.runs.desktop.docScrollOverflow,
      reallyScrollsX: report.runs.desktop.reallyScrollsX,
      scrollHeight: report.runs.desktop.scrollHeight,
      catUnits: report.runs.desktop.catUnits,
      modelCards: report.runs.desktop.modelCards,
      specRows: report.runs.desktop.specRows,
      brokenImgs: report.runs.desktop.imgs.filter((i) => i.broken).length,
      failedReq: report.runs.desktop.failedRequests,
      consoleErrors: report.runs.desktop.consoleErrors,
      nav: report.runs.desktop.nav,
      footLinks: report.runs.desktop.footLinks,
      zhFigcaption: report.runs.desktop.zhFigcaption,
      navZhLabel: report.runs.desktop.navZhLabel,
    },
    mobile: {
      docScrollOverflow: report.runs.mobile.docScrollOverflow,
      reallyScrollsX: report.runs.mobile.reallyScrollsX,
      scrollHeight: report.runs.mobile.scrollHeight,
      brokenImgs: report.runs.mobile.imgs.filter((i) => i.broken).length,
      failedReq: report.runs.mobile.failedRequests,
      nav: report.runs.mobile.nav,
      zhFigcaption: report.runs.mobile.zhFigcaption,
      navZhLabel: report.runs.mobile.navZhLabel,
    },
  }, null, 2));

  await browser.close();
})();
