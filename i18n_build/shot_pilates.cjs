/**
 * shot_pilates.cjs — /pilates/ 板块实拍验收
 *
 * 用法:
 *   NODE_PATH=<node_modules> node i18n_build/shot_pilates.cjs
 *   BASE=http://127.0.0.1:8848 可覆盖（默认即此）
 *   ONLY=pilates-reformer 可只拍某页
 *
 * 除截图外还会：
 *   · 收集 status>=400 的响应 / requestfailed（验证 CSS/JS 真 200）
 *   · 中英双语态逐项断言：show-zh 下 .lang-zh 必须全可见、.lang-en 必须全隐藏
 *   · 断言 .pl-bar-inner 桌面不横向溢出、hero 统计数字不折行
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE = process.env.BASE || 'http://127.0.0.1:8848';
const OUT = 'outputs/pilates-preview';
fs.mkdirSync(OUT, { recursive: true });

const FAMILIES = [
  'pilates-reformer', 'pilates-cadillac', 'pilates-wunda-chair',
  'pilates-ladder-barrel', 'pilates-spine-corrector',
  'pilates-reformer-tower', 'pilates-studio-set', 'pilates-specialty',
];
const PAGES = [{ url: '/pilates/index.html', name: 'index' }].concat(
  FAMILIES.map((k) => ({ url: `/pilates/${k}.html`, name: k.replace('pilates-', '') }))
);

const SHOTS = [];
for (const p of PAGES) {
  SHOTS.push({ url: p.url, name: `${p.name}-en-top`, w: 1280, h: 900, full: false });
  SHOTS.push({ url: p.url, name: `${p.name}-zh-top`, w: 1280, h: 900, full: false, lang: 'zh' });
}
// 只有版块首页与样板页出整页图 + 移动图，控制体积
SHOTS.push({ url: '/pilates/index.html', name: 'index-en-full', w: 1280, h: 900, full: true, lang: 'en' });
SHOTS.push({ url: '/pilates/pilates-reformer.html', name: 'reformer-en-full', w: 1280, h: 900, full: true, lang: 'en' });
SHOTS.push({ url: '/pilates/index.html', name: 'index-en-mobile', w: 390, h: 844, full: false });

const only = process.env.ONLY;
const shots = only ? SHOTS.filter((s) => s.name.startsWith(only)) : SHOTS;

(async () => {
  const browser = await chromium.launch();
  const bad = [];
  const report = [];

  for (const s of shots) {
    const ctx = await browser.newContext({
      viewport: { width: s.w, height: s.h },
      deviceScaleFactor: 2,
    });
    // 本机无外网时 GA 请求会挂住 networkidle，直接拦掉
    await ctx.route(/google-analytics|googletagmanager/, (r) => r.abort());
    const page = await ctx.newPage();
    page.on('response', (r) => {
      if (r.status() >= 400 && !/google-analytics|googletagmanager/.test(r.url())) {
        bad.push(`${s.name}  ${r.status()}  ${r.url()}`);
      }
    });
    page.on('requestfailed', (r) => {
      if (/google-analytics|googletagmanager/.test(r.url())) return; // 本机无外网，噪音
      bad.push(`${s.name}  FAILED  ${r.url()}  ${r.failure() && r.failure().errorText}`);
    });

    if (s.lang) {
      await ctx.addInitScript((lang) => {
        try {
          localStorage.setItem('siteLang', lang);
          document.cookie = 'siteLang=' + lang + ';path=/';
        } catch (e) {}
      }, s.lang);
    }

    await page.goto(BASE + s.url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForSelector('.pl-bar', { timeout: 15000 });
    await page.waitForTimeout(400);

    // 双语态断言
    const counts = await page.evaluate(() => {
      const vis = (el) => {
        const st = getComputedStyle(el);
        return st.display !== 'none' && st.visibility !== 'hidden' && st.opacity !== '0';
      };
      const zh = [...document.querySelectorAll('.lang-zh')];
      const en = [...document.querySelectorAll('.lang-en')];
      return {
        zhTotal: zh.length, zhShown: zh.filter(vis).length,
        enTotal: en.length, enShown: en.filter(vis).length,
        isZh: document.documentElement.classList.contains('show-zh'),
      };
    });

    // 布局断言
    const layout = await page.evaluate(() => {
      const bar = document.querySelector('.pl-bar-inner');
      const stats = document.querySelector('.pl-stats');
      const grab = (sel) => {
        const el = document.querySelector(sel);
        return el ? Math.round(el.getBoundingClientRect().height) : null;
      };
      return {
        barOverflow: bar ? bar.scrollWidth - bar.clientWidth : null,
        barHeight: grab('.pl-bar-inner'),
        statsHeight: grab('.pl-stats'),
        hsHeights: stats
          ? [...stats.children].map((c) => Math.round(c.getBoundingClientRect().height))
          : [],
      };
    });

    report.push({ shot: s.name, lang: s.lang || 'en(default)', ...counts, ...layout });

    await page.screenshot({
      path: path.join(OUT, `${s.name}.png`),
      fullPage: !!s.full,
    });
    await ctx.close();
    console.log(`  ✓ ${s.name}.png`);
  }

  await browser.close();

  console.log('\n--- 双语态断言 ---');
  for (const r of report) {
    const expectZh = r.lang === 'zh';
    const ok = expectZh
      ? r.isZh && r.zhShown === r.zhTotal && r.enShown === 0
      : !r.isZh && r.enShown === r.enTotal && r.zhShown === 0;
    console.log(
      `${ok ? '  ✓' : '  ✗'} ${r.shot}`.padEnd(30) +
      ` show-zh=${r.isZh}  zh ${r.zhShown}/${r.zhTotal}  en ${r.enShown}/${r.enTotal}`
    );
  }

  console.log('\n--- 布局断言 ---');
  console.log('  桌面(1280) 分类条必须不溢出；移动(390) 允许横向滚动（设计如此）');
  for (const r of report) {
    const mobile = r.shot.includes('mobile');
    let warn = '';
    if (mobile) warn = r.barOverflow > 1 ? '  ✓ 横向滚动（设计）' : '  ! 未溢出，chip 可能被压扁';
    else warn = r.barOverflow > 1 ? '  ✗ 桌面横向溢出' : '  ✓ 桌面不溢出';
    const hs = r.hsHeights.length ? ` hs高度=${r.hsHeights.join(',')}` : '';
    const hsOdd = r.hsHeights.length && new Set(r.hsHeights).size > 1 ? '  ✗ hs 高度不一致(折行)' : '';
    console.log(`  ${r.shot}`.padEnd(30) + ` 分类条溢出=${r.barOverflow}px${hs}${warn}${hsOdd}`);
  }

  console.log('\n--- HTTP 异常 ---');
  console.log(bad.length ? bad.join('\n') : '  无 4xx / 请求失败 ✓');
})();
