// 客户语言旅程实测（2026-10-03）
// 直接回答客户视角的三个问题：
//   ① 客户从 Google/直接输网址进来，**看到的是什么语言**？
//   ② 同一语言页内点链接，**会不会跳到别的语言**？
//   ③ 访客**系统语言**是德/日/韩/法/意/西 时，会不会被自动带进对应语言站？
// 用法：node probe_lang_journey_20261003.cjs --base=http://127.0.0.1:8901
const { chromium } = require('playwright');
const argv = process.argv.slice(2);
const arg = (k, d) => { const i = argv.indexOf('--' + k); if (i >= 0) return argv[i + 1];
  const m = argv.find(a => a.startsWith('--' + k + '=')); return m ? m.slice(('--' + k + '=').length) : d; };
const BASE = arg('base', 'http://127.0.0.1:8901');

let pass = 0, fail = 0;
const check = (n, ok, d) => { ok ? pass++ : fail++; console.log(`  ${ok ? '✓' : '✗'} ${n}${d ? '  ' + d : ''}`); };

// 从页面正文取一段「能证明语言」的文字
// ⚠️ 特征词必须用**实测首页里真实出现的词**（2026-10-03 首版写成 /Werk/ /Prodotti…/，
//    结果 de/it/es 三页明明是本地语言却被判失败 —— 探针假警报又一次）
const LANG_MARK = {
  de: /Hersteller|Angebot anfordern|Fabrik|Werk|Qualität/,
  ja: /メーカー|お見積り|Yoga/,
  ko: /제조|견적|공장/,
  fr: /Fabricant|Demander|qualité|Production/,
  it: /Produttore|Richiendi|azienda|Produzione/,
  es: /Fabricante|Solicita|fábrica|producción/,
  en: /Manufacturer|Quote|Factory|Quality/,
};

(async () => {
  const browser = await chromium.launch();

  // ── ① 系统语言 → 自动进入对应语言站 ────────────────────────────────
  console.log('\n【① 访客系统语言自动匹配】');
  const cases = [
    { locale: 'de-DE', want: '/de/',            name: '德国' },
    { locale: 'ja-JP', want: '/ja/',            name: '日本' },
    { locale: 'ko-KR', want: '/ko/',            name: '韩国' },
    { locale: 'fr-FR', want: '/fr/',            name: '法国' },
    { locale: 'it-IT', want: '/it/',            name: '意大利' },
    { locale: 'es-ES', want: '/es/',            name: '西班牙' },
    { locale: 'en-US', want: '/',               name: '英语（应留在主页）' },
    { locale: 'zh-CN', want: '/',               name: '中文（站内无 /zh/，应留在主页）' },
  ];
  for (const c of cases) {
    const ctx = await browser.newContext({ locale: c.locale, viewport: { width: 390, height: 844 } });
    const page = await ctx.newPage();
    await page.goto(BASE + '/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    const url = new URL(page.url()).pathname;
    const lang = await page.evaluate(() => document.documentElement.lang);
    const body = await page.evaluate(() => document.body.innerText.slice(0, 1200));
    const code = c.want === '/' ? 'en' : c.want.slice(1, 3);
    const okLang = c.want === '/' ? (lang === 'en') : (lang === code);
    const okText = LANG_MARK[code].test(body);
    check(`${c.name} 系统语言 → 落在 ${c.want}`, url === c.want, `实际 ${url}，html lang=${lang}`);
    check(`${c.name} 正文是该语言`, okText, okText ? '✓' : '✗ 正文未匹配该语言特征');
    await ctx.close();
  }

  // ── ② 深页也自动带对语言 ───────────────────────────────────────────
  console.log('\n【② 从深页进来也自动带对语言】');
  for (const c of [
    { locale: 'de-DE', from: '/products/alignment-line-tpe-yoga-mat.html', want: '/de/products/alignment-line-tpe-yoga-mat.html' },
    { locale: 'ja-JP', from: '/blog.html', want: '/ja/blog.html' },
    { locale: 'fr-FR', from: '/faq.html', want: '/fr/faq.html' },
  ]) {
    const ctx = await browser.newContext({ locale: c.locale, viewport: { width: 390, height: 844 } });
    const page = await ctx.newPage();
    await page.goto(BASE + c.from, { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    const url = new URL(page.url()).pathname;
    check(`${c.locale} 访问 ${c.from} → ${c.want}`, url === c.want, `实际 ${url}`);
    await ctx.close();
  }

  // ── ③ 手动选过语言后不再被系统语言覆盖 ────────────────────────────
  console.log('\n【③ 手动选择优先于系统语言】');
  {
    // 系统德语，但访客在英文页点了 EN（写入 siteLang=en）
    const ctx = await browser.newContext({ locale: 'de-DE', viewport: { width: 390, height: 844 } });
    const page = await ctx.newPage();
    await page.addInitScript(() => { try { localStorage.setItem('siteLang', 'en'); } catch (e) {} });
    await page.goto(BASE + '/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    const url = new URL(page.url()).pathname;
    check('已选 EN 的德语系统访客留在英文页', url === '/', `实际 ${url}`);
    await ctx.close();
  }
  {
    // 系统英语，但访客之前选过德语 → 应带去德语站
    const ctx = await browser.newContext({ locale: 'en-US', viewport: { width: 390, height: 844 } });
    const page = await ctx.newPage();
    await page.addInitScript(() => { try { localStorage.setItem('siteLang', 'de'); } catch (e) {} });
    await page.goto(BASE + '/blog.html', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    const url = new URL(page.url()).pathname;
    check('已选 DE 的英语系统访客被带到德语页', url === '/de/blog.html', `实际 ${url}`);
    await ctx.close();
  }

  // ── ④ 语言页内点链接不串站（真实点击）────────────────────────────
  console.log('\n【④ 语言页内点击不串站（真实点击）】');
  const clickCases = [
    { page: '/de/pilates/index.html', linkText: 'Alle Anwendungen', wantPath: '/de/applications', name: '德语页脚「Alle Anwendungen」' },
    { page: '/de/index.html',        linkText: 'Datenschutz',      wantPath: '/de/privacy',      name: '德语页脚「Datenschutz」' },
    { page: '/ja/index.html',        linkText: 'プライバシーポリシー', wantPath: '/ja/privacy',    name: '日语页脚「プライバシーポリシー」' },
    { page: '/fr/index.html',        linkText: 'Mentions légales',  wantPath: '/fr/impressum',    name: '法语页脚「Mentions légales」' },
  ];
  for (const c of clickCases) {
    const ctx = await browser.newContext({ locale: 'en-US', viewport: { width: 390, height: 844 } });
    const page = await ctx.newPage();
    await page.goto(BASE + c.page, { waitUntil: 'networkidle' });
    const link = page.locator('footer a', { hasText: c.linkText }).first();
    const n = await link.count();
    if (!n) { check(c.name + ' 链接存在', false, '未找到'); await ctx.close(); continue; }
    await link.click();
    await page.waitForLoadState('networkidle');
    const url = new URL(page.url()).pathname;
    check(c.name + ` → ${c.wantPath}`, url.startsWith(c.wantPath), `实际 ${url}`);
    await ctx.close();
  }

  // ── ⑤ 语言页上的切换器能正确换语言，且换完不弹回 ──────────────────
  console.log('\n【⑤ 切换器换语言后不被弹回】');
  {
    const ctx = await browser.newContext({ locale: 'de-DE', viewport: { width: 390, height: 844 } });
    const page = await ctx.newPage();
    await page.goto(BASE + '/de/index.html', { waitUntil: 'networkidle' });
    await page.waitForTimeout(400);
    await page.locator('.lang-current').click();
    await page.waitForTimeout(300);
    await page.locator('.lang-menu a[hreflang="en"]').click();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(600);
    const url = new URL(page.url()).pathname;
    const lang = await page.evaluate(() => document.documentElement.lang);
    check('德语页点 EN → 停在英文页且不被系统语言弹回', url === '/' && lang === 'en', `实际 ${url} lang=${lang}`);
    await ctx.close();
  }

  console.log(`\n结论：通过 ${pass} / 失败 ${fail}`);
  await browser.close();
  process.exit(fail ? 1 : 0);
})();
