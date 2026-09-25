// 验收：中文块 h1→h2.post-title 的视觉等价性 + 引号清理后的页面健康度
// 用法：OUT=/tmp NODE_PATH=... node verify_zh_h1_quote_20260925.cjs
const { chromium } = require('playwright');
const BASE = 'http://127.0.0.1:8851';
const fs = require('fs');
const OUT = process.env.OUT || '/tmp';

const BLOGS = [
  '7day-sampling', 'compliance', 'custom-sizes', 'moq-explained',
  'private-label-yoga-mats', 'top-12-china-yoga-mat-manufacturers',
  'tpe-vs-pu', 'vet-factory', 'yoga-mat-materials', 'yoga-mat-spec-guide',
].map(n => `/blog/${n}.html`);

const DE_PILATES = [
  '/de/pilates/index.html', '/de/pilates/pilates-reformer.html',
  '/de/pilates/pilates-wunda-chair.html', '/de/pilates/pilates-studio-set.html',
];
const QUOTE_PAGES = [
  '/de/blog/top-12-china-yoga-mat-manufacturers.html',
  '/es/blog/top-12-china-yoga-mat-manufacturers.html',
  '/fr/blog/top-12-china-yoga-mat-manufacturers.html',
  '/it/blog/top-12-china-yoga-mat-manufacturers.html',
  '/ja/blog/top-12-china-yoga-mat-manufacturers.html',
  '/ko/blog/private-label-yoga-mats.html',
];

// 注意：必须写成**单层**函数 —— 柯里化双层箭头被 evaluate 序列化后会返回内层函数，无法执行。
// localStorage 与 cookie **两个通道都要设**（main.js 是双通道回退）。
function setLang(z) {
  localStorage.setItem('siteLang', z ? 'zh' : 'en');
  if (z) document.cookie = 'siteLang=zh; path=/; Max-Age=31536000';
  else document.cookie = 'siteLang=; path=/; Max-Age=0';
}

(async () => {
  const browser = await chromium.launch();
  let bad = 0, checked = 0;
  const msgs = [];

  // ---------- A. EN 博客页：中英两态视觉等价 ----------
  for (const vp of [{ w: 1440, h: 1000, tag: 'desktop' }, { w: 390, h: 844, tag: 'mobile' }]) {
    const ctx = await browser.newContext({ viewport: { width: vp.w, height: vp.h } });
    const page = await ctx.newPage();
    const errs = [];
    page.on('pageerror', e => errs.push(String(e).slice(0, 120)));

    for (const url of BLOGS) {
      // 英文态
      await page.goto(BASE + '/index.html', { waitUntil: 'domcontentloaded' });
      await page.evaluate(setLang, false);
      await page.goto(BASE + url, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(180);
      const en = await page.evaluate(() => {
        const h1 = document.querySelector('.article h1, h1');
        const zh = document.querySelector('div.lang-zh');
        return {
          h1Count: document.querySelectorAll('h1').length,
          h1Size: h1 ? getComputedStyle(h1).fontSize : null,
          zhVisible: zh ? zh.offsetParent !== null : null,
          zhH1: zh ? zh.querySelectorAll('h1').length : null,
          zhH2: zh ? zh.querySelectorAll('h2.post-title').length : null,
        };
      });
      // 中文态
      await page.evaluate(setLang, true);
      await page.reload({ waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(180);
      const zh = await page.evaluate(() => {
        const blk = document.querySelector('div.lang-zh');
        const t = blk ? blk.querySelector('h2.post-title') : null;
        return {
          zhVisible: blk ? blk.offsetParent !== null : null,
          titleVisible: t ? t.offsetParent !== null : null,
          titleSize: t ? getComputedStyle(t).fontSize : null,
          titleText: t ? t.innerText.trim().slice(0, 40) : null,
          h1Count: document.querySelectorAll('h1').length,
          overflow: document.documentElement.scrollWidth > window.innerWidth + 1,
        };
      });
      checked++;
      const ok = en.h1Count === 1 && zh.h1Count === 1
        && en.zhH1 === 0 && en.zhH2 === 1
        && en.zhVisible === false && zh.zhVisible === true && zh.titleVisible === true
        && en.h1Size === zh.titleSize && !zh.overflow;
      if (!ok) { bad++; msgs.push(`✗ ${vp.tag} ${url} en=${JSON.stringify(en)} zh=${JSON.stringify(zh)}`); }
      if (vp.tag === 'desktop' || url === '/blog/tpe-vs-pu.html') {
        console.log(`${ok ? '✓' : '✗'} [${vp.tag}] ${url.padEnd(46)} h1=${en.h1Count}/${zh.h1Count} zhH2=${en.zhH2} 字号 ${en.h1Size}/${zh.titleSize} 中块可见 ${en.zhVisible}→${zh.zhVisible}`);
      }
    }
    if (errs.length) { bad += errs.length; msgs.push(`✗ ${vp.tag} JS 报错: ${errs.join(' | ')}`); }
    await ctx.close();
  }

  // ---------- B. 中文态截图（人工确认视觉） ----------
  {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    const page = await ctx.newPage();
    await page.goto(BASE + '/index.html', { waitUntil: 'domcontentloaded' });
    await page.evaluate(setLang, true);
    await page.goto(BASE + '/blog/tpe-vs-pu.html', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(400);
    await page.evaluate(() => {
      const h = document.querySelector('div.lang-zh h2.post-title');
      if (h) h.scrollIntoView({ block: 'start' });
    });
    await page.waitForTimeout(300);
    await page.screenshot({ path: `${OUT}/zh_h1_after.png` });
    await ctx.close();
  }

  // ---------- C. 引号清理后的页面健康度 ----------
  {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    const page = await ctx.newPage();
    const errs = [];
    page.on('pageerror', e => errs.push(String(e).slice(0, 120)));
    for (const url of [...DE_PILATES, ...QUOTE_PAGES]) {
      const r = await page.goto(BASE + url, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(150);
      const info = await page.evaluate(() => ({
        h1: document.querySelectorAll('h1').length,
        ld: document.querySelectorAll('script[type="application/ld+json"]').length,
        ldOk: Array.from(document.querySelectorAll('script[type="application/ld+json"]'))
          .every(s => { try { JSON.parse(s.textContent); return true; } catch (e) { return false; } }),
        overflow: document.documentElement.scrollWidth > window.innerWidth + 1,
        // 可见文本里是否还残留「成对引号紧贴术语」
        badQuote: (document.body.innerText.match(/[„“”«»「」『』]\s*(?:TPE|PVC|PU|REACH|BSCI|ISO 9001|CA Prop 65|6P\/7P|MOQ)\s*[„“”«»「」『』]/g) || []).length,
      }));
      checked++;
      const ok = r.status() === 200 && info.h1 === 1 && info.ldOk && !info.overflow && info.badQuote === 0;
      if (!ok) { bad++; msgs.push(`✗ ${url} status=${r.status()} ${JSON.stringify(info)}`); }
      console.log(`${ok ? '✓' : '✗'} ${url.padEnd(56)} HTTP=${r.status()} h1=${info.h1} LD=${info.ld}/${info.ldOk} 引号残留=${info.badQuote}`);
    }
    if (errs.length) { bad += errs.length; msgs.push(`✗ JS 报错: ${errs.join(' | ')}`); }
    await ctx.close();
  }

  // ---------- D. 视觉对比截图：英文 h1 vs 中文 h2 ----------
  {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();
    for (const [zh, name] of [[false, 'title_en.png'], [true, 'title_zh.png']]) {
      await page.goto(BASE + '/index.html', { waitUntil: 'domcontentloaded' });
      await page.evaluate(setLang, zh);
      await page.goto(BASE + '/blog/moq-explained.html', { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(300);
      await page.evaluate(z => {
        const t = z ? document.querySelector('div.lang-zh h2.post-title') : document.querySelector('.article h1, h1');
        if (t) t.scrollIntoView({ block: 'start' });
      }, zh);
      await page.waitForTimeout(300);
      const el = await page.evaluate(z => {
        const t = z ? document.querySelector('div.lang-zh h2.post-title') : document.querySelector('.article h1, h1');
        if (!t) return null;
        const r = t.getBoundingClientRect();
        return { top: r.top + window.scrollY, h: r.height };
      }, zh);
      if (el) {
        await page.screenshot({
          path: `${OUT}/${name}`,
          clip: { x: 0, y: Math.max(0, el.top - 30), width: 1440, height: Math.min(260, el.h + 120) },
          fullPage: true,
        });
      }
    }
    await ctx.close();
  }

  await browser.close();
  console.log(`\n共检查 ${checked} 项 · ` + (bad === 0 ? '全部通过' : `${bad} 项异常`));
  if (msgs.length) console.log(msgs.join('\n'));
  process.exit(bad === 0 ? 0 : 1);
})();
