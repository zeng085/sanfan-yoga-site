#!/usr/bin/env node
/**
 * 语言切换功能验证（2026-09-25 补内容后）
 *
 * 为什么必须实测：本轮的导语 + FAQ 是**成对的 `span.lang-en` / `span.lang-zh`**，
 * 靠 `applyLang()` 用 textContent 整体替换。如果配对写错（少一个、嵌套了子元素），
 * 静态审计**看不出来**，只有真点一次才暴露。
 *
 * ⚠️ 中文态必须 `localStorage.siteLang='zh'` **且** 设 cookie，再 reload —— 缺一不可
 *    （站内 `applyLang` 走 localStorage，但首屏初始化读 cookie）。
 * ⚠️ 不用 `networkidle`（GA 长连）。
 */
const { chromium } = require('playwright');
const BASE = 'file:///Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16';
const PAGES = ['foam-rollers.html', 'jump-ropes.html', 'resistance-bands.html',
  'suede-cork-yoga-mats.html', 'meditation-pilates-mats.html',
  'yoga-props-accessories.html', 'strength-training.html', 'massage-recovery.html'];

const CJK = /[\u4e00-\u9fff]/;

(async () => {
  const b = await chromium.launch();
  let bad = 0;
  for (const f of PAGES) {
    const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
    await p.goto(`${BASE}/${f}`, { waitUntil: 'domcontentloaded' });
    await p.waitForTimeout(200);

    const en = await p.evaluate(() => ({
      intro: (document.querySelector('section p') || {}).innerText || '',
      faq: (document.querySelector('details.faq-item') || {}).innerText || '',
      h2: [...document.querySelectorAll('h2')].map(h => h.innerText.trim()).filter(Boolean),
    }));

    await p.evaluate(() => {
      localStorage.setItem('siteLang', 'zh');
      document.cookie = 'siteLang=zh; path=/';
    });
    await p.reload({ waitUntil: 'domcontentloaded' });
    await p.waitForTimeout(320);

    const zh = await p.evaluate(() => ({
      intro: (document.querySelector('section p') || {}).innerText || '',
      faq: (document.querySelector('details.faq-item') || {}).innerText || '',
      h2: [...document.querySelectorAll('h2')].map(h => h.innerText.trim()).filter(Boolean),
    }));

    // 判据：英文态新内容无 CJK；中文态导语/FAQ/H2 都出现 CJK
    const checks = [
      ['EN 导语无中文', !CJK.test(en.intro)],
      ['EN FAQ 无中文', !CJK.test(en.faq)],
      ['ZH 导语有中文', CJK.test(zh.intro)],
      ['ZH FAQ 有中文', CJK.test(zh.faq)],
      ['ZH H2 有中文', zh.h2.some(h => CJK.test(h))],
      ['EN/ZH 导语不同', en.intro !== zh.intro && en.intro.length > 20],
    ];
    const fails = checks.filter(([, ok]) => !ok);
    if (fails.length) bad++;
    console.log(`${fails.length ? '✗' : '✓'} ${f.padEnd(30)} H2 ${en.h2.length}→${zh.h2.length}`
      + `  导语 ${en.intro.length}→${zh.intro.length} 字  FAQ ${en.faq.length}→${zh.faq.length} 字`);
    for (const [name] of fails) console.log(`     ✗ ${name}`);
    if (fails.length) {
      console.log(`     EN导语: ${en.intro.slice(0, 70)}`);
      console.log(`     ZH导语: ${zh.intro.slice(0, 70)}`);
    }
    await p.close();
  }
  await b.close();
  console.log(`\n语言切换检查 ${PAGES.length} 页 | 异常 ${bad}`);
  process.exit(bad ? 1 : 0);
})();
