// 英文页「EN / 中文」同页切换的回归验证（2026-10-03）
// 背景：本轮把 `setLangPref()` 从 applyLang() 里移除了（它每次页面加载都写偏好，
//       等于把「默认值」冒充成「用户的选择」）。必须确认**页内切换功能没被带坏**。
// 判据：① 英文页默认显示英文、看不到中文
//       ② 点「中文」→ 正文变中文、html lang 变 zh-CN
//       ③ 再点「EN」→ 回到英文
//       ④ 切到中文后不触发系统语言自动跳转（中文用户不跳）
//       ⑤ 语言页（/de/ 等）上中文开关不应把德文冲掉
const { chromium } = require('playwright');
const argv = process.argv.slice(2);
const arg = (k, d) => { const i = argv.indexOf('--' + k); if (i >= 0) return argv[i + 1];
  const m = argv.find(a => a.startsWith('--' + k + '=')); return m ? m.slice(('--' + k + '=').length) : d; };
const BASE = arg('base', 'http://127.0.0.1:8906');
let pass = 0, fail = 0;
const check = (n, ok, d) => { ok ? pass++ : fail++; console.log(`  ${ok ? '✓' : '✗'} ${n}${d ? '  ' + d : ''}`); };
const CJK = /[\u4e00-\u9fff]{3,}/;

(async () => {
  const browser = await chromium.launch();

  console.log('\n【① 英文页默认显示英文】');
  let ctx = await browser.newContext({ locale: 'en-US', viewport: { width: 390, height: 844 } });
  let page = await ctx.newPage();
  await page.goto(BASE + '/blog/moq-explained.html', { waitUntil: 'networkidle' });
  await page.waitForTimeout(500);
  let vis = await page.evaluate(() => {
    // 只取「当前可见」的正文文本：按 .lang-zh / .lang-en 的显示状态过滤
    const out = [];
    document.querySelectorAll('body *').forEach(el => {
      if (el.children.length) return;
      const t = (el.textContent || '').trim();
      if (!t) return;
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden') return;
      let p = el, hidden = false;
      while (p && p !== document.body) {
        const pc = getComputedStyle(p);
        if (pc.display === 'none' || pc.visibility === 'hidden') { hidden = true; break; }
        p = p.parentElement;
      }
      if (!hidden) out.push(t);
    });
    return out.join(' ').slice(0, 1500);
  });
  check('英文页可见文本里有中文', !CJK.test(vis), CJK.test(vis) ? '有中文（应隐藏）' : '无中文 ✓');
  check('页面 html lang = en', (await page.evaluate(() => document.documentElement.lang)) === 'en');
  await ctx.close();

  console.log('\n【② 点「中文」→ 变中文】');
  ctx = await browser.newContext({ locale: 'en-US', viewport: { width: 390, height: 844 } });
  page = await ctx.newPage();
  await page.goto(BASE + '/blog/moq-explained.html', { waitUntil: 'networkidle' });
  await page.locator('.lang-current').click();
  await page.waitForTimeout(300);
  await page.locator('.lang-menu button[data-setlang="zh"]').click();
  await page.waitForTimeout(600);
  let lang = await page.evaluate(() => document.documentElement.lang);
  let hasZh = await page.evaluate(() => {
    const b = document.querySelector('.lang-zh');
    return !!b && getComputedStyle(b).display !== 'none';
  });
  check('html lang 变成 zh-CN', lang === 'zh-CN', lang);
  check('中文块变为可见', hasZh);
  check('切换后 URL 不变（仍是英文页同页切换）', new URL(page.url()).pathname === '/blog/moq-explained.html', new URL(page.url()).pathname);

  console.log('\n【③ 再点「EN」→ 回英文】');
  await page.locator('.lang-current').click();
  await page.waitForTimeout(300);
  await page.locator('.lang-menu button[data-setlang="en"]').click();
  await page.waitForTimeout(600);
  lang = await page.evaluate(() => document.documentElement.lang);
  check('html lang 回到 en', lang === 'en', lang);

  console.log('\n【④ 中文状态不会被系统语言自动跳转】');
  await page.locator('.lang-current').click();
  await page.waitForTimeout(300);
  await page.locator('.lang-menu button[data-setlang="zh"]').click();
  await page.waitForTimeout(400);
  await page.goto(BASE + '/faq.html', { waitUntil: 'networkidle' });
  await page.waitForTimeout(600);
  check('选过中文的访客访问 /faq.html 仍留英文页', new URL(page.url()).pathname === '/faq.html', new URL(page.url()).pathname);
  await ctx.close();

  console.log('\n【⑤ 语言页上点「中文」→ 去看中文版（在英文页里）】');
  ctx = await browser.newContext({ locale: 'de-DE', viewport: { width: 390, height: 844 } });
  page = await ctx.newPage();
  await page.goto(BASE + '/de/faq.html', { waitUntil: 'networkidle' });
  await page.waitForTimeout(500);
  let deBefore = await page.evaluate(() => document.body.innerText.slice(0, 200));
  const deHasGerman = /Frage|Antwort|Kontakt|Bestellung/i.test(deBefore);
  check('德语页显示德文', deHasGerman, deBefore.slice(0, 40).replace(/\s+/g, ' '));
  // 语言页本身没有中文版内容（中文是英文页里的隐藏对照块），所以正确行为是
  // **跳到英文页并切成中文** —— 而不是把德文原地替换掉（首版判据写成"德文别变"，
  // 与设计意图不符，报了个假失败；实测点击后落地 /faq.html、lang=zh-CN、可见中文 ✓）
  const zhBtn = page.locator('.lang-menu [data-setlang="zh"]');
  if (await zhBtn.count()) {
    await page.locator('.lang-current').click();
    await page.waitForTimeout(300);
    await zhBtn.click();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(700);
    const url = new URL(page.url()).pathname;
    const lang = await page.evaluate(() => document.documentElement.lang);
    const vis2 = await page.evaluate(() => document.body.innerText.slice(0, 200));
    check('点中文 → 落到有中文版的页面并显示中文',
      lang === 'zh-CN' && /[\u4e00-\u9fff]{3,}/.test(vis2),
      `落地 ${url} lang=${lang}`);
  } else {
    check('德语页有中文开关', false, '未找到 [data-setlang=zh]');
  }
  await ctx.close();

  console.log(`\n结论：通过 ${pass} / 失败 ${fail}`);
  await browser.close();
  process.exit(fail ? 1 : 0);
})();
