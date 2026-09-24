// EVA≡TPE 小节交付验收（真实浏览器，不是"看源码像对的"）
//
// 校验：
//   1 七种语言的 TPE 页都能看到新小节，h2 文案正确、2 条 FAQ 都在
//   2 FAQ 展开后答案文字可见（details 折叠机制没被破坏）
//   3 EN 页中文态（localStorage.siteLang='zh' + 重载）显示中文 h2，
//     且英文层隐藏 —— 记忆里踩过「只 add('show-zh') 不触发 applyLang」的坑
//   4 无横向溢出（1440 桌面 / 390 手机）
//   5 FAQPage JSON-LD 在 DOM 里且可解析，且带站内主流字段 @id(...#faq) / inLanguage
//   6 description ≤155 显示宽（CJK 记 2）—— v1 只盯着「有没有 EVA 关键词」，
//     把语言版推到 199–306 宽，属于"修好一处、弄坏一处"，故列为硬断言
//   7 materials 页 EVA 行口径已更新
// 用法：BASE=http://127.0.0.1:8848 node i18n_build/verify_eva_tpe_note.cjs
const { chromium } = require('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:8848';

const CASES = [
  ['en', '/tpe-yoga-mats.html', 'Searching for an EVA yoga mat?', 'Do you make EVA yoga mats?'],
  ['de', '/de/tpe-yoga-mats.html', 'Sie suchen eine EVA-Yogamatte?', 'Stellen Sie auch EVA-Yogamatten her?'],
  ['ja', '/ja/tpe-yoga-mats.html', 'EVA ヨガマットをお探しですか？', 'EVA ヨガマットは作っていますか？'],
  ['ko', '/ko/tpe-yoga-mats.html', 'EVA 요가 매트를 찾고 계신가요?', 'EVA 요가 매트도 만드나요?'],
  ['fr', '/fr/tpe-yoga-mats.html', 'Vous cherchez un tapis de yoga EVA ?', 'Fabriquez-vous aussi des tapis de yoga EVA ?'],
  ['it', '/it/tpe-yoga-mats.html', 'Cerchi un tappetino da yoga EVA?', 'Producete anche tappetini da yoga EVA?'],
  ['es', '/es/tpe-yoga-mats.html', '\u00bfBusca una esterilla de yoga EVA?', '\u00bfTambi\u00e9n fabrican esterillas de yoga EVA?'],
];

const MAT = [
  ['en', '/materials.html', 'supplied as TPE'],
  ['de', '/de/materials.html', 'als TPE geliefert'],
  ['ja', '/ja/materials.html', 'TPE として供給されます'],
  ['ko', '/ko/materials.html', 'TPE로 공급됩니다'],
  ['fr', '/fr/materials.html', 'fournis en TPE'],
  ['it', '/it/materials.html', 'forniti in TPE'],
  ['es', '/es/materials.html', 'se suministran en TPE'],
];

const findSection = `(() => {
  // 显示宽度：CJK 记 2 —— 按字符数看不出 ja/ko 超长（记忆里的标定结论）
  const dispW = (s) => [...s.replace(/&amp;/g, '&')].reduce((n, c) => n + (c.codePointAt(0) > 0x2E80 ? 2 : 1), 0);
  const meta = document.querySelector('meta[name="description"]');
  const faq = [...document.querySelectorAll('script[type="application/ld+json"]')]
    .map(s => { try { return JSON.parse(s.textContent); } catch (e) { return null; } })
    .find(x => x && x['@type'] === 'FAQPage');
  const secs = [...document.querySelectorAll('section.section')];
  const s = secs.find(x => x.querySelector('.eyebrow'));
  if (!s) return null;
  const h2 = s.querySelector('h2');
  const items = [...s.querySelectorAll('details.faq-item')];
  return {
    h2: h2 ? h2.innerText.trim().replace(/\\s+/g, ' ') : null,
    h2en: h2 ? getComputedStyle(h2.querySelector('.lang-en') || h2).display : null,
    h2zh: h2 ? getComputedStyle(h2.querySelector('.lang-zh') || h2).display : null,
    faq: items.length,
    firstQ: items[0] ? items[0].querySelector('summary').innerText.trim() : null,
    firstA: items[0] ? items[0].querySelector('.faq-a').innerText.trim().replace(/\\s+/g, ' ').slice(0, 90) : null,
    descW: meta ? dispW(meta.content) : -1,
    desc: meta ? meta.content : '',
    // JSON-LD 里还有第 4 份描述（@graph 的 CollectionPage）——它与 meta 不是同一个串
    // （HTML 里 &amp; 转义、JSON-LD 里裸 &），漏同步就会出现「页面有两套描述」
    ldDesc: (() => {
      for (const s of document.querySelectorAll('script[type="application/ld+json"]')) {
        let o; try { o = JSON.parse(s.textContent); } catch (e) { continue; }
        const items = o && o['@graph'] ? o['@graph'] : (Array.isArray(o) ? o : [o]);
        for (const it of (Array.isArray(items) ? items : [items])) {
          if (it && it['@type'] === 'CollectionPage' && typeof it.description === 'string') return it.description;
        }
      }
      return '(无)';
    })(),
    ldId: faq ? (faq['@id'] || '') : '',
    ldLang: faq ? (faq.inLanguage || '') : '',
  };
})()`;

(async () => {
  const b = await chromium.launch();
  let fail = 0;
  const bad = (m) => { console.log('   !! ' + m); fail++; };

  for (const [lang, path, h2want, qwant] of CASES) {
    console.log('== ' + lang + '  ' + path);
    for (const vw of [1440, 390]) {
      const ctx = await b.newContext({ viewport: { width: vw, height: 900 } });
      const pg = await ctx.newPage();
      const errs = [];
      pg.on('pageerror', (e) => errs.push(String(e)));
      await pg.route('**googletagmanager.com/**', (r) => r.abort());
      await pg.route('**google-analytics.com/**', (r) => r.abort());
      await pg.goto(BASE + path, { waitUntil: 'domcontentloaded' });
      await pg.waitForTimeout(500);

      const info = await pg.evaluate(findSection);
      if (!info) bad(vw + ' 找不到新小节');
      else {
        if (vw === 1440) {
          if (info.h2 !== h2want) bad('h2 文案不符 → ' + info.h2);
          if (!info.firstQ || !info.firstQ.includes(qwant.slice(0, 12))) bad('首问不符 → ' + info.firstQ);
          if (info.faq !== 2) bad('FAQ 条数 ' + info.faq + '（应 2）');
          // description 宽度：这条是 v1 翻车的地方，必须由验收脚本守住
          if (info.descW < 0) bad('读不到 meta description');
          else if (info.descW > 155) bad('description ' + info.descW + ' 显示宽（预算 155）');
          // 第 4 份描述（JSON-LD CollectionPage）必须与 meta 同步，否则 Google/AI 拿到的是没 EVA 的那份
          if (info.ldDesc !== info.desc) {
            bad('JSON-LD 描述与 meta 不同步 → ' + String(info.ldDesc).slice(0, 60));
          }
          // 站内 328 个既有 FAQPage 都带 @id + inLanguage，本轮 v1 漏了
          if (!info.ldId.endsWith('#faq')) bad('FAQPage @id 不是 ...#faq → ' + (info.ldId || '缺失'));
          if (info.ldLang !== lang) bad('FAQPage inLanguage=' + (info.ldLang || '缺失') + '（应 ' + lang + '）');
          // 展开 FAQ，答案必须可见、有文字
          // ⚠️ 折叠的 <details> 里 innerText 取不到内容（未渲染），必须**展开后**再读，
          //    否则会得到「首答过短」的假失败。
          await pg.locator('section.section details.faq-item').first().locator('summary').click();
          await pg.waitForTimeout(250);
          const ans = await pg.evaluate(`(() => {
            const a = document.querySelector('section.section details.faq-item .faq-a');
            if (!a) return { h: 0, t: '' };
            return { h: a.getBoundingClientRect().height, t: a.innerText.trim() }; })()`);
          if (!ans.h) bad('FAQ 展开后答案高度为 0');
          if (ans.t.length < 80) bad('首答文字过短（' + ans.t.length + '）→ ' + ans.t.slice(0, 60));
        }
      }
      // 溢出
      const ov = await pg.evaluate('document.documentElement.scrollWidth - window.innerWidth');
      if (ov > 1) bad(vw + 'px 横向溢出 ' + ov + 'px');
      if (errs.length) bad('页面 JS 报错 ' + errs[0].slice(0, 120));
      // FAQPage JSON-LD
      const ld = await pg.evaluate(`(() => {
        const o = [...document.querySelectorAll('script[type="application/ld+json"]')]
          .map(s => { try { return JSON.parse(s.textContent); } catch (e) { return null; } })
          .filter(x => x && x['@type'] === 'FAQPage');
        return o.length ? o[0].mainEntity.length : 0; })()`);
      if (!ld) bad('DOM 里没有可解析的 FAQPage');
      await ctx.close();
    }
  }

  // EN 页中文态
  console.log('== EN 页中文态');
  {
    const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } });
    const pg = await ctx.newPage();
    await pg.route('**googletagmanager.com/**', (r) => r.abort());
    await pg.goto(BASE + '/tpe-yoga-mats.html', { waitUntil: 'domcontentloaded' });
    await pg.evaluate(`localStorage.setItem('siteLang','zh')`);
    await pg.reload({ waitUntil: 'domcontentloaded' });
    await pg.waitForTimeout(600);
    const info = await pg.evaluate(findSection);
    if (!info) bad('中文态找不到小节');
    else {
      if (!info.h2 || !info.h2.includes('在找 EVA 瑜伽垫')) bad('中文态 h2 → ' + info.h2);
      if (info.h2en !== 'none') bad('中文态英文层未隐藏（display=' + info.h2en + '）');
      if (info.faq !== 2) bad('中文态 FAQ 条数 ' + info.faq);
    }
    await ctx.close();
  }

  for (const [lang, path, want] of MAT) {
    const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } });
    const pg = await ctx.newPage();
    await pg.route('**googletagmanager.com/**', (r) => r.abort());
    await pg.goto(BASE + path, { waitUntil: 'domcontentloaded' });
    await pg.waitForTimeout(300);
    const ok = await pg.evaluate(`document.body.innerText.includes(${JSON.stringify(want)})`);
    console.log((ok ? 'OK  ' : '!!  ') + 'materials/' + lang + '  含「' + want + '」');
    if (!ok) fail++;
    await ctx.close();
  }

  await b.close();
  console.log('\n最终：' + (fail ? fail + ' 项不合格' : '全部通过'));
  process.exit(fail ? 1 : 0);
})();
