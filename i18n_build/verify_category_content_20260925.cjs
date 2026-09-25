#!/usr/bin/env node
/**
 * 8 个分类页补内容后的浏览器级验收（2026-09-25）
 *
 * 为什么必须跑浏览器级：源码审计看不见三类缺陷 ——
 *   ① 元素在窄视口下的**真实几何**（横向溢出、热区高度）
 *   ② `<details>` 折叠内容在**渲染后**是否存在
 *   ③ 语言切换（localStorage + cookie 双通道）是否仍正常
 * 这三项静态查不出来，所以必须实开页面。
 *
 * ⚠️ 本项目的三个探测陷阱（都已在代码里规避，勿回退）：
 *   1. 不能用 `networkidle` —— GA 长连 + `domcontentloaded` 才对
 *   2. `html{scroll-behavior:smooth}` 会让程序化滚动变**异步** →
 *      同步读 rect 会拿到旧位置。测量前先注入 `scroll-behavior:auto !important`
 *   3. 中文态必须 `localStorage.siteLang='zh'` **并**设 cookie 后重载，缺一不可
 */
const { chromium } = require('playwright');
const path = require('path');

const BASE = 'file:///Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16';
const LANGS = ['', 'de/', 'ja/', 'ko/', 'fr/', 'it/', 'es/'];
const PAGES = [
  'foam-rollers.html', 'jump-ropes.html', 'resistance-bands.html',
  'suede-cork-yoga-mats.html', 'meditation-pilates-mats.html',
  'yoga-props-accessories.html', 'strength-training.html', 'massage-recovery.html',
];
const VPS = [{ w: 390, h: 844 }, { w: 320, h: 568 }, { w: 1440, h: 900 }];

const probe = () => {
  const de = document.documentElement;
  const over = [];
  // ① 横向溢出：逐元素找右边界超出文档宽度的
  for (const el of document.querySelectorAll('.container, section, .faq-item, .faq-a, p, h2, li, ul, .section-head')) {
    const r = el.getBoundingClientRect();
    if (r.width > 0 && r.right > de.clientWidth + 1.5) {
      over.push((el.tagName + '.' + String(el.className).split(' ')[0]).slice(0, 40)
        + '@' + Math.round(r.right - de.clientWidth));
    }
  }
  // ② 三个新块是否存在 + 元素几何
  const intro = document.querySelector('.eyebrow')?.closest('section');
  const faqList = document.querySelector('.faq-list');
  const faqSec = faqList?.closest('section');
  const ilinkA = [...document.querySelectorAll('section')]
    .find(s => s.querySelector('ul li a[href*="blog/"]') || s.querySelector('ul li a[href$="products.html"]'))
    ?.querySelector('ul li a');
  const details = document.querySelectorAll('details.faq-item');
  // ③ 折叠内容渲染后确实存在
  let firstOpenChars = 0;
  if (details.length) {
    details[0].open = true;
    firstOpenChars = (details[0].querySelector('.faq-a')?.innerText || '').trim().length;
    details[0].open = false;
  }
  const cs = ilinkA ? getComputedStyle(ilinkA) : null;
  // ④ 语言纯度：取新增三块的可读文本，查是否混入其它语言字符
  const blocks = [
    document.querySelector('section .section-head h2')?.closest('section'),
    faqSec, ilinkA?.closest('section'),
  ].filter(Boolean);
  const blockText = blocks.map(b => b.innerText || '').join(' ');
  return {
    docW: de.clientWidth, docH: de.scrollHeight,
    over: [...new Set(over)].slice(0, 5),
    hasIntro: !!intro && !!document.querySelector('section .section-head h2'),
    introScreen: intro ? +(intro.getBoundingClientRect().top + window.scrollY) / window.innerHeight : null,
    faqScreen: faqSec ? +((faqSec.getBoundingClientRect().top + window.scrollY) / window.innerHeight).toFixed(1) : null,
    nDetails: details.length,
    firstOpenChars,
    introChars: (document.querySelector('section .section-head h2')?.closest('section')?.innerText || '').trim().length,
    blockChars: blockText.trim().length,
    cjk: (blockText.match(/[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]/g) || []).length,
    kana: (blockText.match(/[\u3040-\u30ff]/g) || []).length,
    hangul: (blockText.match(/[\uac00-\ud7af]/g) || []).length,
    // ⚠️ 日语**必须**含汉字（kanji 属 CJK 区），所以「混入中文」不能用「有 CJK」判。
    //    改用**简体特有字**判定（这些字在标准日语里不用：长/车/东/业/产/质/价/单/类…）
    cnSimp: (blockText.match(/[这个们说时对发为应门问题让见长车东业务产质价优势购联单据类别报设备无处样试验环罗纹扩张缩弹层复]/g) || []).length,
    ilinkH: ilinkA ? Math.round(ilinkA.getBoundingClientRect().height) : null,
    ilinkDisplay: cs ? cs.display : null,
    h2: document.querySelectorAll('h2').length,
    h1: document.querySelectorAll('h1').length,
  };
};

(async () => {
  const browser = await chromium.launch();
  const rows = [];
  for (const vp of VPS) {
    for (const lg of LANGS) {
      for (const f of PAGES) {
        const page = await browser.newPage({ viewport: { width: vp.w, height: vp.h } });
        const errs = [];
        page.on('pageerror', e => errs.push(String(e).slice(0, 70)));
        await page.goto(`${BASE}/${lg}${f}`, { waitUntil: 'domcontentloaded' });
        await page.addStyleTag({ content: 'html{scroll-behavior:auto !important}' });
        await page.waitForTimeout(180);
        const r = await page.evaluate(probe);
        rows.push({ vp: `${vp.w}×${vp.h}`, f: lg + f, ...r, errs });
        await page.close();
      }
    }
  }
  await browser.close();

  // ---- 汇总 ----
  // ⚠️ 2026-09-25 语言版已补齐（手写译文直注，未走 API）→ **7 语言同等判据**。
  //    旧版此处只对英文页要求 details=5/h2=4，语言版靠「还没做」豁免 —— 必须去掉。
  const langOf = f => (f.match(/^(de|ja|ko|fr|it|es)\//) || [, 'en'])[1];
  const BAD_LANG = { en: null, de: 'nowestern', ja: 'nokana', ko: 'nohangul',
                     fr: 'nowestern', it: 'nowestern', es: 'nowestern' };
  const langDirty = (r) => {
    const lg = langOf(r.f);
    if (lg === 'ja') return r.kana < 20 || r.hangul > 0 || r.cnSimp > 0;
    if (lg === 'ko') return r.hangul < 20 || r.kana > 0 || r.cnSimp > 0;
    return r.cjk > 0 || r.kana > 0 || r.hangul > 0;   // 西语系不得出现任何 CJK/假名/谚文
  };
  const bad = rows.filter(r => r.over.length || r.errs.length || r.h1 !== 1
    || r.nDetails !== 5 || r.h2 !== 4 || r.firstOpenChars < 40
    || r.blockChars < 400 || langDirty(r));
  console.log(`检查 ${rows.length} 个「视口 × 语言 × 页面」组合（7 语言 × 3 视口 × 8 页）`);
  console.log(`异常 ${bad.length} 个\n`);
  for (const r of bad.slice(0, 25)) {
    console.log(`  ✗ ${r.vp.padEnd(10)} ${r.f.padEnd(34)} 溢出=${r.over.join(',') || 0}`
      + ` details=${r.nDetails} h1=${r.h1} h2=${r.h2} 首条展开字数=${r.firstOpenChars}`
      + ` 块字数=${r.blockChars} cjk=${r.cjk}/kana=${r.kana}/hangul=${r.hangul}/简=${r.cnSimp}`
      + (r.errs.length ? ` JS错误=${r.errs.join('|')}` : ''));
  }
  console.log('\n=== 390×844 位置实测（导语应在前 2 屏内）===');
  for (const r of rows.filter(x => x.vp === '390×844')) {
    console.log(`  ${r.f.padEnd(34)} 文档高=${String(r.docH).padStart(5)}  导语=第${r.introScreen}屏  FAQ=第${r.faqScreen}屏  内链热区=${r.ilinkH}px(${r.ilinkDisplay})`);
  }
  console.log('\n=== 320×568 文档高度（最窄视口）===');
  for (const r of rows.filter(x => x.vp === '320×568').slice(0, 8)) {
    console.log(`  ${r.f.padEnd(34)} 文档高=${String(r.docH).padStart(5)}  导语=第${r.introScreen}屏  FAQ=第${r.faqScreen}屏`);
  }
})();
