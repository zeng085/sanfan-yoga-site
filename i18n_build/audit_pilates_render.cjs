/**
 * 普拉提板块：多视口溢出与渲染审计
 *   - 页面级横向溢出（documentElement.scrollWidth > 视口宽）
 *   - 越界元素定位（排除「内部可滚动容器」这一合法情况）
 *   - 文字被裁切（overflow:hidden 容器内 scrollWidth > clientWidth）
 *   - 坏图（naturalWidth == 0）
 *   - console error / 4xx / 请求失败（GA 噪音除外）
 *   - 规格表在窄屏是否可横向滑动
 *   - 中英双语态的可见性（互斥）
 */
const fs = require('fs');
const { chromium } = require('playwright');

const BASE = process.env.BASE || 'http://127.0.0.1:8848';
const OUT = 'outputs/pilates-preview';
fs.mkdirSync(OUT, { recursive: true });

const FAMILIES = [
  'pilates-reformer', 'pilates-cadillac', 'pilates-wunda-chair', 'pilates-ladder-barrel',
  'pilates-spine-corrector', 'pilates-reformer-tower', 'pilates-studio-set', 'pilates-specialty',
];
const PAGES = ['/pilates/index.html', ...FAMILIES.map((f) => `/pilates/${f}.html`)];

const VIEWPORTS = [
  { w: 320, h: 640, name: '320' },   // 极小屏（iPhone SE1 竖屏）
  { w: 360, h: 740, name: '360' },
  { w: 390, h: 844, name: '390' },
  { w: 414, h: 896, name: '414' },
  { w: 768, h: 1024, name: '768' },  // 平板
  { w: 1024, h: 768, name: '1024' },
  { w: 1280, h: 800, name: '1280' },
  { w: 1440, h: 900, name: '1440' },
  { w: 1920, h: 1080, name: '1920' },
];

const fails = [];
const warns = [];
const rows = [];

const isNoise = (u) => /google-analytics|googletagmanager|doubleclick|clarity\.ms/i.test(u);

async function probe(page) {
  return page.evaluate(() => {
    const vw = window.innerWidth;
    const de = document.documentElement;
    const docW = de.scrollWidth;

    const items = [];
    if (docW > vw + 1) {
      document.querySelectorAll('body *').forEach((el) => {
        const r = el.getBoundingClientRect();
        if (r.width < 2 || r.height < 2) return;
        if (r.right <= vw + 1) return;
        // 祖先里若有「可横向滚动」的容器，属合法情况
        let p = el.parentElement, ok = false;
        while (p && p !== document.body) {
          const s = getComputedStyle(p);
          if (/(auto|scroll)/.test(s.overflowX) && p.scrollWidth > p.clientWidth + 1) { ok = true; break; }
          p = p.parentElement;
        }
        if (ok) return;
        items.push({
          tag: el.tagName,
          cls: String(el.className || '').slice(0, 48),
          right: Math.round(r.right),
          w: Math.round(r.width),
          txt: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 36),
        });
      });
    }

    // 文字被裁切：overflow hidden 且内容更宽/更高
    const clipped = [];
    document.querySelectorAll('.pl-hero h1, .pl-hero .lead, .pl-card h3, .pl-block h3, .pl-spec td, .pl-chip, .hs .lab, .hs .num').forEach((el) => {
      const s = getComputedStyle(el);
      if (/(hidden|clip)/.test(s.overflowX + s.overflowY)) {
        if (el.scrollWidth > el.clientWidth + 2 || el.scrollHeight > el.clientHeight + 2) {
          clipped.push({ cls: String(el.className || '').slice(0, 40), txt: (el.textContent || '').trim().slice(0, 30) });
        }
      }
    });

    // 坏图
    const badImgs = [];
    document.querySelectorAll('img').forEach((im) => {
      if (im.complete && im.naturalWidth === 0) badImgs.push(im.getAttribute('src'));
    });

    // 规格表在窄屏的滚动能力
    const wrap = document.querySelector('.pl-spec-wrap');
    const specScroll = wrap ? { cw: wrap.clientWidth, sw: wrap.scrollWidth, ox: getComputedStyle(wrap).overflowX } : null;

    // 双语可见性
    const vis = (sel) => [...document.querySelectorAll(sel)].filter((e) => {
      const r = e.getBoundingClientRect();
      const s = getComputedStyle(e);
      return s.display !== 'none' && s.visibility !== 'hidden' && e.offsetParent !== null && r.height > 0;
    }).length;
    const blocks = {
      en: document.querySelectorAll('.lang-en').length,
      zh: document.querySelectorAll('.lang-zh').length,
    };

    return {
      vw, docW, overflow: docW > vw + 1, items: items.slice(0, 10),
      clipped: clipped.slice(0, 6), badImgs, specScroll,
      visEn: vis('.lang-en'), visZh: vis('.lang-zh'),
      shownZh: document.documentElement.classList.contains('show-zh'),
      navPilates: !!document.querySelector('.nav-drop'),
      h1: (document.querySelector('h1') || {}).textContent,
    };
  });
}

(async () => {
  const browser = await chromium.launch();
  for (const vp of VIEWPORTS) {
    for (const url of PAGES) {
      for (const lang of ['en', 'zh']) {
        const ctx = await browser.newContext({
          viewport: { width: vp.w, height: vp.h },
          deviceScaleFactor: 1,
        });
        const page = await ctx.newPage();
        const errs = [];
        page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text().slice(0, 120)); });
        page.on('pageerror', (e) => errs.push('pageerror: ' + String(e).slice(0, 120)));
        page.on('response', (r) => {
          if (r.status() >= 400 && !isNoise(r.url())) errs.push(`${r.status()} ${r.url().slice(0, 90)}`);
        });
        page.on('requestfailed', (r) => {
          if (!isNoise(r.url())) errs.push(`FAILED ${r.url().slice(0, 90)}`);
        });
        if (lang === 'zh') {
          await ctx.addInitScript(() => {
            try { localStorage.setItem('siteLang', 'zh'); document.cookie = 'siteLang=zh;path=/'; } catch (e) {}
          });
        }
        try {
          await page.goto(BASE + url, { waitUntil: 'domcontentloaded', timeout: 30000 });
          await page.waitForTimeout(200);
          const r = await probe(page);
          const tag = `${url.replace('/pilates/', '')} @${vp.name} ${lang}`;
          rows.push({ tag, ...r, errs });
          if (r.overflow) {
            fails.push(`${tag} 页面横向溢出 ${r.docW} > ${r.vw}px :: ` +
              r.items.map((i) => `${i.tag}.${i.cls}[right=${i.right} w=${i.w}] "${i.txt}"`).join(' ; '));
          }
          if (r.clipped.length) {
            fails.push(`${tag} 文字被裁切 :: ` +
              r.clipped.map((c) => `${c.cls} "${c.txt}"`).join(' ; '));
          }
          if (r.badImgs.length) fails.push(`${tag} 坏图 :: ${r.badImgs.join(', ')}`);
          const realErrs = errs.filter((e) => !isNoise(e));
          if (realErrs.length) fails.push(`${tag} 控制台/网络错误 :: ${realErrs.slice(0, 3).join(' | ')}`);
          // 双语互斥
          if (lang === 'zh' && r.visEn > 0) fails.push(`${tag} 中文态下仍有 ${r.visEn} 个英文块可见`);
          if (lang === 'en' && r.visZh > 0) fails.push(`${tag} 英文态下仍有 ${r.visZh} 个中文块可见`);
          if (lang === 'zh' && r.visZh === 0) fails.push(`${tag} 中文态下中文块 0 可见`);
          if (lang === 'en' && r.visEn === 0) fails.push(`${tag} 英文态下英文块 0 可见`);
          if (!r.navPilates) warns.push(`${tag} 导航未见 Pilates 入口`);
          if (vp.w <= 414 && r.specScroll && r.specScroll.sw > r.specScroll.cw + 1
              && !/auto|scroll/.test(r.specScroll.ox)) {
            fails.push(`${tag} 规格表溢出但不可横向滚动（overflow-x:${r.specScroll.ox}）`);
          }
        } catch (e) {
          fails.push(`${url} @${vp.name} ${lang} 加载失败: ${String(e).slice(0, 90)}`);
        }
        await ctx.close();
      }
    }
  }
  await browser.close();

  fs.writeFileSync(OUT + '/audit-render.json', JSON.stringify(rows, null, 1));
  const byViewport = {};
  for (const r of rows) {
    const vp = r.tag.split('@')[1].split(' ')[0];
    byViewport[vp] = byViewport[vp] || { n: 0, of: 0, clip: 0 };
    byViewport[vp].n++;
    if (r.overflow) byViewport[vp].of++;
    if (r.clipped.length) byViewport[vp].clip++;
  }
  console.log('='.repeat(78));
  console.log('多视口溢出与渲染审计');
  console.log('='.repeat(78));
  console.log('组合数 %d（%d 页 × %d 视口 × 双语）', rows.length, PAGES.length, VIEWPORTS.length);
  console.log('\n各视口：溢出页面 / 文字裁切');
  for (const k of Object.keys(byViewport)) {
    const v = byViewport[k];
    console.log(`  ${k.padEnd(6)} 溢出 ${v.of}/${v.n}   裁切 ${v.clip}/${v.n}`);
  }
  console.log('');
  if (fails.length) {
    console.log('FAIL %d', fails.length);
    const uniq = [...new Set(fails.map((f) => f.replace(/@\d+ (en|zh)/, '@* *')))];
    uniq.slice(0, 40).forEach((f) => console.log('  ✗', f));
    if (uniq.length > 40) console.log(`  ... 去重后 ${uniq.length} 类，另有 ${uniq.length - 40} 类`);
  } else {
    console.log('FAIL 0 ✓');
  }
  if (warns.length) {
    console.log('\nWARN ' + warns.length);
    [...new Set(warns)].slice(0, 10).forEach((w) => console.log('  !', w));
  }
  process.exit(fails.length ? 1 : 0);
})();
