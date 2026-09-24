/**
 * FAQ 注入验收（P0-A pilates 63 页 + P0-C 产品页 1029 页）
 *
 * 断言（每页）：
 *   1. 可见 FAQ 区块存在且可见（.faq-list 内 details.faq-item 数量 = 6 / 5）
 *   2. 点开第一条 → details[open]，答案文字可见且非空
 *   3. 1280 / 1440 / 1920 三档视口无横向溢出（documentElement.scrollWidth <= clientWidth+2）
 *   4. FAQPage JSON-LD 存在、可解析、mainEntity 条数与可见条数一致、inLanguage 正确
 *   5. 无 console error / 无 4xx（GA 噪音除外）
 *
 * 用法：BASE=http://127.0.0.1:8848 node i18n_build/verify_faq_20260924.cjs
 */
const { chromium } = require('playwright');

const BASE = process.env.BASE || 'http://127.0.0.1:8848';
const WIDTHS = [1280, 1440, 1920];

const CASES = [
  // [语言, URL, 期望 FAQ 条数]
  ['en', '/pilates/pilates-reformer.html', 6],
  ['de', '/de/pilates/pilates-reformer.html', 6],
  ['ja', '/ja/pilates/index.html', 6],
  ['en', '/products/cork-suede-yoga-mat.html', 5],
  ['de', '/de/products/cork-suede-yoga-mat.html', 5],
  ['ja', '/ja/products/rb2.html', 5],
  ['es', '/es/products/adjustable-stair-climber.html', 5],
  ['ko', '/ko/products/ym3.html', 5],
];

let pass = 0, fail = 0;
const bad = [];

function check(ok, tag, msg) {
  if (ok) { pass++; } else { fail++; bad.push(`${tag} → ${msg}`); }
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errs = [];
  page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text().slice(0, 120)); });
  page.on('requestfailed', (r) => { if (!/google|ga4|analytics/.test(r.url())) errs.push('REQFAIL ' + r.url().slice(0, 80)); });
  page.on('response', (r) => { if (r.status() >= 400 && !/google|analytics/.test(r.url())) errs.push(r.status() + ' ' + r.url().slice(0, 80)); });

  for (const [lang, url, expectN] of CASES) {
    const tag = `${lang} ${url}`;
    errs.length = 0;
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(BASE + url, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(400);

    // 1 条数
    const n = await page.locator('.faq-list .faq-item').count();
    check(n === expectN, tag, `FAQ 条数 ${n} ≠ ${expectN}`);

    const visible = await page.locator('.faq-list').first().isVisible();
    check(visible, tag, 'FAQ 区块不可见');

    // 2 点开第一条
    const first = page.locator('.faq-list .faq-item').first();
    await first.locator('summary').click();
    await page.waitForTimeout(200);
    const opened = await first.evaluate((el) => el.hasAttribute('open'));
    check(opened, tag, '点击后 details 未展开');
    const ansTxt = (await first.locator('.faq-a').innerText()).trim();
    check(ansTxt.length > 60, tag, `答案文字过短（${ansTxt.length}）`);

    // 3 无横向溢出（抽 3 档视口）
    for (const w of WIDTHS) {
      await page.setViewportSize({ width: w, height: 900 });
      await page.waitForTimeout(150);
      const ov = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      check(ov <= 2, tag, `@${w} 横向溢出 ${ov}px`);
    }

    // 4 JSON-LD
    const ld = await page.evaluate(() => {
      const out = [];
      document.querySelectorAll('script[type="application/ld+json"]').forEach((s) => {
        try { out.push(JSON.parse(s.textContent)); } catch (e) { out.push({ __err: e.message }); }
      });
      return out;
    });
    const badLd = ld.filter((x) => x.__err);
    check(badLd.length === 0, tag, `JSON-LD 解析失败 ${badLd.length} 块`);
    const faq = ld.find((x) => x && x['@type'] === 'FAQPage');
    check(!!faq, tag, '缺 FAQPage');
    if (faq) {
      check(faq.mainEntity.length === expectN, tag, `FAQPage 条数 ${faq.mainEntity.length} ≠ ${expectN}`);
      check(faq.inLanguage === lang, tag, `inLanguage=${faq.inLanguage} ≠ ${lang}`);
      check(faq.mainEntity.every((q) => q.acceptedAnswer.text && q.acceptedAnswer.text.length > 40), tag, '有答案过短');
    }
    const web = ld.find((x) => x && x['@type'] === 'WebPage');
    check(!!web && !!web.dateModified, tag, '缺 WebPage.dateModified');

    // 5 控制台/请求
    check(errs.length === 0, tag, 'console/请求异常：' + errs.slice(0, 2).join(' ; '));
  }

  await browser.close();
  console.log('='.repeat(70));
  console.log(`FAQ 验收：${CASES.length} 页 × 多视口`);
  console.log(`PASS ${pass} / FAIL ${fail}`);
  bad.forEach((b) => console.log('  ✗ ' + b));
  console.log(fail === 0 ? '全部通过 ✓' : '存在失败项 ✗');
  process.exit(fail === 0 ? 0 : 1);
})();
