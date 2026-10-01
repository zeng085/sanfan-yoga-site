/**
 * shot_pilates_mobile_20261001.cjs
 * 移动端（390）逐块实拍 —— 只设 viewport，不用 isMobile/hasTouch
 * （上一版带 isMobile+hasTouch+scale2，6 分钟零产出，疑似上下文初始化卡死）
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE = process.env.BASE || 'http://127.0.0.1:8866';
const PAGE = '/pilates/pilates-ladder-barrel.html';
const OUT = path.resolve(__dirname, '..', 'outputs', 'pilates_block_review_20261001');
fs.mkdirSync(OUT, { recursive: true });

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
  await ctx.route(/google-analytics|googletagmanager/, (r) => r.abort());
  const page = await ctx.newPage();
  const errs = [];
  page.on('pageerror', (e) => errs.push('pageerror: ' + e.message.slice(0, 140)));
  page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text().slice(0, 140)); });
  const failed = [];
  page.on('requestfailed', (r) => {
    if (/google-analytics|googletagmanager|doubleclick/.test(r.url())) return;
    failed.push(r.url().replace(BASE, '') + ' :: ' + (r.failure()?.errorText || ''));
  });

  console.log('goto...');
  await page.goto(BASE + PAGE, { waitUntil: 'domcontentloaded', timeout: 25000 });
  await page.waitForTimeout(600);
  console.log('loaded, settling...');

  // 滚到底触发 lazy
  await page.evaluate(async () => {
    const de = document.documentElement;
    for (let y = 0; y < de.scrollHeight; y += 600) {
      window.scrollTo(0, y);
      await new Promise((r) => setTimeout(r, 35));
    }
    window.scrollTo(0, 0);
    await new Promise((r) => setTimeout(r, 250));
  });
  await page.waitForTimeout(300);
  console.log('settled, shooting...');

  const shots = [];
  const shot = async (sel, name) => {
    const el = await page.$(sel);
    if (!el) { console.log('  (缺) ' + sel); return; }
    await el.scrollIntoViewIfNeeded();
    await page.waitForTimeout(160);
    await el.screenshot({ path: path.join(OUT, `${name}.jpg`), quality: 84, type: 'jpeg' });
    shots.push(name);
    console.log('  ✓ ' + name);
  };

  await page.screenshot({ path: path.join(OUT, 'm-hero.jpg'), quality: 84, type: 'jpeg' });
  shots.push('m-hero'); console.log('  ✓ m-hero');

  await shot('.pl-spec-wrap', 'm-spec');
  await shot('#cat-p33', 'm-unit1');
  await shot('#cat-p35', 'm-unit2');
  await shot('#cat-p36', 'm-unit3');

  const report = await page.evaluate(() => {
    const de = document.documentElement;
    const before = window.scrollX;
    window.scrollTo(9999, window.scrollY);
    const scrolledX = window.scrollX;
    window.scrollTo(before, window.scrollY);

    const imgs = [...document.images].map((im) => ({
      src: (im.getAttribute('src') || '').slice(-22),
      natural: im.naturalWidth + 'x' + im.naturalHeight,
      renderedW: Math.round(im.getBoundingClientRect().width),
      broken: !im.complete || im.naturalWidth === 0,
    }));

    const units = [...document.querySelectorAll('.cat-unit')].map((u) => {
      const host = u.parentElement.getBoundingClientRect();
      const ub = u.getBoundingClientRect();
      const fig = u.querySelector('.cat-fig')?.getBoundingClientRect();
      const mod = u.querySelector('.cat-models')?.getBoundingClientRect();
      return {
        id: u.id,
        overflowsHost: Math.round(ub.right - host.right),
        figW: fig ? Math.round(fig.width) : null,
        modelsW: mod ? Math.round(mod.width) : null,
        stackedGap: (fig && mod) ? Math.round(mod.top - fig.bottom) : null,
      };
    });

    const cards = [...document.querySelectorAll('.model-card')].map((c) => {
      const p = c.parentElement.getBoundingClientRect(), cb = c.getBoundingClientRect();
      return { id: c.id, overflowsParent: Math.round(cb.right - p.right), w: Math.round(cb.width) };
    });

    const dlOver = [...document.querySelectorAll('.model-card dl')].map((dl) => {
      const db = dl.getBoundingClientRect();
      const cb = dl.closest('.model-card').getBoundingClientRect();
      return Math.round(db.right - cb.right);
    });

    const tog = document.querySelector('.menu-toggle');
    const nav = document.querySelector('.nav');
    const fc = document.querySelector('.cat-fig figcaption');
    const spec = document.querySelector('.pl-spec-wrap');

    return {
      docScrollOverflow: de.scrollWidth - de.clientWidth,
      reallyScrollsX: scrolledX > 0,
      scrollHeight: de.scrollHeight,
      brokenImgs: imgs.filter((i) => i.broken),
      imgCount: imgs.length,
      units, cards,
      dlOverMax: dlOver.length ? Math.max(...dlOver) : null,
      navHeight: nav ? Math.round(nav.getBoundingClientRect().height) : null,
      toggleBox: tog ? (() => { const b = tog.getBoundingClientRect(); return { w: Math.round(b.width), h: Math.round(b.height) }; })() : null,
      figcaption: fc ? { h: Math.round(fc.getBoundingClientRect().height), text: fc.textContent.replace(/\s+/g, ' ').trim() } : null,
      specWrapW: spec ? Math.round(spec.getBoundingClientRect().width) : null,
      specTableScroll: (() => { const t = spec && spec.querySelector('table'); return t ? Math.round(t.scrollWidth - t.clientWidth) : null; })(),
      catUnits: document.querySelectorAll('.cat-unit').length,
      modelCards: document.querySelectorAll('.model-card').length,
      specRows: document.querySelectorAll('table.pl-spec tbody tr').length,
    };
  });

  report.widestInCatalog = await page.evaluate(() => {
    const de = document.documentElement;
    const out = [];
    for (const el of document.querySelectorAll('#catalog *')) {
      const b = el.getBoundingClientRect();
      const over = Math.round(b.right - de.clientWidth);
      if (over > 1) out.push({ tag: el.tagName.toLowerCase(), cls: el.className.toString().slice(0, 36), over });
    }
    return out.slice(0, 12);
  });

  const tog = await page.$('.menu-toggle');
  if (tog) {
    await tog.click().catch(() => {});
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(OUT, 'm-nav-open.jpg'), quality: 84, type: 'jpeg' });
    shots.push('m-nav-open');
    console.log('  ✓ m-nav-open');
    report.drawer = await page.evaluate(() => {
      const l = document.querySelector('.nav-links');
      if (!l) return null;
      const b = l.getBoundingClientRect();
      return { visible: getComputedStyle(l).display !== 'none', w: Math.round(b.width), h: Math.round(b.height) };
    });
  }

  report.consoleErrors = errs;
  report.failedRequests = failed;
  report.shots = shots;
  fs.writeFileSync(path.join(OUT, 'report-mobile.json'), JSON.stringify(report, null, 2));
  console.log('\n===== 移动端 390 测量 =====');
  console.log(JSON.stringify({
    docScrollOverflow: report.docScrollOverflow,
    reallyScrollsX: report.reallyScrollsX,
    scrollHeight: report.scrollHeight,
    imgCount: report.imgCount,
    brokenImgs: report.brokenImgs,
    failedRequests: report.failedRequests,
    consoleErrors: report.consoleErrors,
    units: report.units,
    cards: report.cards,
    dlOverMax: report.dlOverMax,
    navHeight: report.navHeight,
    toggleBox: report.toggleBox,
    figcaption: report.figcaption,
    specWrapW: report.specWrapW,
    specTableScroll: report.specTableScroll,
    widestInCatalog: report.widestInCatalog,
    drawer: report.drawer,
    catUnits: report.catUnits, modelCards: report.modelCards, specRows: report.specRows,
  }, null, 2));
  await browser.close();
})();
