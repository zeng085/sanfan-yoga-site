/*
 * Reformer 族页「画册重构」样板 —— 多视口实拍 + 指标
 *
 * 与梯桶页那套探针的区别：本页是**重页**（27 个 cat-unit / 46 行表），
 * 所以额外测三件事：
 *   ① lazy 图是否全部真正加载（逐屏滚动后再查 naturalWidth）
 *   ② 规格表 6 列在 390 下是否可横滚而不撑破 body
 *   ③ 三线概览卡在窄屏是否塌成单列
 *
 * 用法：BASE=http://127.0.0.1:8866 node shot_reformer_family_20261001.cjs
 */
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE = process.env.BASE || 'http://127.0.0.1:8866';
const URL = BASE + '/pilates/pilates-reformer.html';
const OUT = path.resolve(__dirname, '..', 'outputs', 'pilates_family_reformer_20261001');

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function warmLazy(page) {
  // 逐屏滚动只触发 lazy 的「进入视口」，但 27 张 1576×1600 的 webp 解码慢，
  // 实测滚完只 loaded 11/31。所以：① 把 loading 改成 eager ② 逐屏慢滚
  // ③ 最后 await 每张图的 load/error（带 10s 上限），确保查的是真实加载结果。
  await page.evaluate(async () => {
    const imgs = [...document.querySelectorAll('img[loading="lazy"]')];
    imgs.forEach((im) => { im.loading = 'eager'; });
    const h = document.documentElement.scrollHeight;
    for (let y = 0; y < h; y += 600) {
      window.scrollTo(0, y);
      await new Promise((r) => setTimeout(r, 130));
    }
    window.scrollTo(0, 0);
    await Promise.all(imgs.map((im) => (im.complete && im.naturalWidth > 0)
      ? Promise.resolve()
      : new Promise((res) => {
        im.addEventListener('load', res, { once: true });
        im.addEventListener('error', res, { once: true });
        setTimeout(res, 10000);
      })));
  });
  await sleep(800);
}

async function probe(page, label) {
  return await page.evaluate((lbl) => {
    const de = document.documentElement;
    const out = {
      label: lbl,
      overflow: de.scrollWidth - de.clientWidth,
      docHeight: de.scrollHeight,
      imgs: { total: 0, loaded: 0, broken: [] },
      catUnits: document.querySelectorAll('.cat-unit').length,
      modelCards: document.querySelectorAll('.model-card').length,
      lineCards: document.querySelectorAll('.line-card').length,
      tableRows: document.querySelectorAll('table.pl-spec tbody tr').length,
      lineRows: document.querySelectorAll('table.pl-spec tr.line-row').length,
      // 三线卡在窄屏是否单列
      lineCols: (() => {
        const g = document.querySelector('.line-overview');
        if (!g) return null;
        return getComputedStyle(g).gridTemplateColumns.split(' ').length;
      })(),
      // 表格是否可横滚且不撑破 body
      tableWrap: (() => {
        const w = document.querySelector('.pl-spec-wrap');
        if (!w) return null;
        return { scrollW: w.scrollWidth, clientW: w.clientWidth, canScroll: w.scrollWidth > w.clientWidth + 1 };
      })(),
      // 越界元素（相对 body 宽度）
      offenders: [],
    };
    document.querySelectorAll('img').forEach((im) => {
      out.imgs.total++;
      if (im.complete && im.naturalWidth > 0) out.imgs.loaded++;
      else out.imgs.broken.push(im.getAttribute('src'));
    });
    const bw = de.clientWidth;
    // 判据修正（探针自身误报）：表格在 overflow-x:auto 的 .pl-spec-wrap 里
    // 横向超出**是设计如此**（移动端横滚看 6 列），不该算越界。
    // 只看「不在可横滚祖先内」的元素是否超出视口。
    const inScrollable = (el) => {
      let p = el.parentElement;
      while (p && p !== document.body) {
        const ox = getComputedStyle(p).overflowX;
        if (ox === 'auto' || ox === 'scroll') return true;
        p = p.parentElement;
      }
      return false;
    };
    document.querySelectorAll('section, .cat-unit, .model-card, .line-card, table').forEach((el) => {
      const r = el.getBoundingClientRect();
      if ((r.width > bw + 1 || r.right > bw + 1) && !inScrollable(el)) {
        out.offenders.push({
          tag: el.tagName,
          cls: (el.className || '').toString().slice(0, 40),
          w: Math.round(r.width),
          right: Math.round(r.right),
        });
      }
    });
    out.offenders = out.offenders.slice(0, 6);
    return out;
  }, label);
}

async function shoot(page, sel, file, full = false) {
  const f = path.join(OUT, file);
  try {
    if (full) {
      await page.screenshot({ path: f, fullPage: true });
    } else {
      const el = await page.$(sel);
      if (!el) { console.log(`  MISS ${sel}`); return; }
      await el.scrollIntoViewIfNeeded();
      await sleep(250);
      await el.screenshot({ path: f });
    }
    const kb = Math.round(fs.statSync(f).size / 1024);
    console.log(`  OK ${file} (${kb} KB)`);
  } catch (e) {
    console.log(`  ERR ${file}: ${e.message}`);
  }
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const report = { url: URL, desktop: null, mobile: null, httpErrors: [] };

  // ---------- 桌面 ----------
  {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    const page = await ctx.newPage();
    page.on('response', (r) => { if (r.status() >= 400) report.httpErrors.push(`${r.status()} ${r.url()}`); });
    page.on('requestfailed', (r) => report.httpErrors.push(`FAILED ${r.url()}`));
    await page.goto(URL, { waitUntil: 'load', timeout: 90000 });
    await warmLazy(page);
    report.desktop = await probe(page, 'desktop-1440');
    console.log('桌面:', JSON.stringify(report.desktop, null, 0).slice(0, 600));
    await shoot(page, '#catalog', 'r-lines-desktop.jpg');
    await shoot(page, '#catalogue-pages .cat-unit', 'r-catunit-desktop.jpg');
    await shoot(page, '#models-compared .pl-spec-wrap', 'r-table-desktop.jpg');
    await shoot(page, null, 'r-full-desktop.jpg', true);

    // 中文态（必须走 localStorage + reload 才会触发 main.js 的 applyLang；
    // 直接 classList.add('show-zh') 不生效 —— 见 check_nav_pilates.cjs 的同款注释）
    await page.evaluate(() => localStorage.setItem('siteLang', 'zh'));
    await page.reload({ waitUntil: 'load', timeout: 90000 });
    await warmLazy(page);
    const zhProbe = await page.evaluate(() => ({
      showZh: document.documentElement.classList.contains('show-zh'),
      h2: (document.querySelector('#catalog h2') || {}).textContent,
      lineCard3: (document.querySelectorAll('.line-card h3')[2] || {}).textContent,
      tableLineRow: (document.querySelector('table.pl-spec tr.line-row td') || {}).textContent,
    }));
    report.zh = zhProbe;
    console.log('中文态:', JSON.stringify(zhProbe));
    await shoot(page, '#catalog', 'r-lines-desktop-zh.jpg');
    await page.evaluate(() => localStorage.setItem('siteLang', 'en'));
    await ctx.close();
  }

  // ---------- 移动端 ----------
  {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
    const page = await ctx.newPage();
    await page.goto(URL, { waitUntil: 'load', timeout: 90000 });
    await warmLazy(page);
    report.mobile = await probe(page, 'mobile-390');
    console.log('移动:', JSON.stringify(report.mobile, null, 0).slice(0, 600));
    await shoot(page, '#catalog .line-overview', 'r-lines-mobile.jpg');
    await shoot(page, '#catalogue-pages .cat-unit', 'r-catunit-mobile.jpg');
    await shoot(page, '#models-compared .pl-spec-wrap', 'r-table-mobile.jpg');
    await ctx.close();
  }

  await browser.close();
  fs.writeFileSync(path.join(OUT, 'probe_reformer.json'), JSON.stringify(report, null, 2), 'utf8');
  console.log('\n报告已写:', path.join(OUT, 'probe_reformer.json'));
  console.log('HTTP 错误:', report.httpErrors.length ? report.httpErrors.slice(0, 8) : '无');
})();
