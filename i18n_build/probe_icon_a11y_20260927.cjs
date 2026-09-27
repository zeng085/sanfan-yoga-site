/**
 * 自审探针：严谨复核「纯图标 a/button 缺可访问名」
 * 用途：验证 audit_mobile_wig_20260927.py 的 WIG-21（报 3550/3550）是否误报
 */
const { chromium } = require('playwright');
const PAGES = ['index.html', 'products.html', 'pilates/pilates-reformer.html', 'faq.html', 'contact.html', 'pilates/index.html'];
const B = 'file:///Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16';

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 390, height: 844 } });
  await p.route('**/*', r => /google-analytics|googletagmanager|clarity|facebook/.test(r.request().url()) ? r.abort() : r.continue());
  let T = 0, BAD = 0;
  const samples = [], badSamples = [];
  for (const f of PAGES) {
    await p.goto(B + '/' + f, { waitUntil: 'domcontentloaded' });
    await p.waitForTimeout(400);
    const r = await p.evaluate(() => {
      const out = { tot: 0, bad: 0, all: [], bads: [] };
      for (const el of document.querySelectorAll('a[href], button')) {
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden') continue;
        const rect = el.getBoundingClientRect();
        if (rect.width < 1 || rect.height < 1) continue;
        const vis = (el.innerText || '').trim();
        if (vis) continue;                       // 有可见文字 → 不是纯图标
        const sr = el.querySelector('.sr-only,.visually-hidden,[class*="sr-"],[class*="screen-reader"]');
        const hasName = !!(el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') ||
                           el.getAttribute('title') || el.querySelector('img[alt]:not([alt=""])') ||
                           (sr && sr.textContent.trim()));
        out.tot++;
        const desc = el.tagName.toLowerCase() + '.' + String(el.className || '').trim().split(/\s+/)[0];
        if (out.all.length < 10) out.all.push(desc + '  name=' + (hasName ? 'Y' : 'N'));
        if (!hasName) {
          out.bad++;
          if (out.bads.length < 6) out.bads.push(desc + '  html=' + el.outerHTML.slice(0, 120).replace(/\s+/g, ' '));
        }
      }
      return out;
    });
    T += r.tot; BAD += r.bad;
    console.log(f.padEnd(34) + ' 纯图标 ' + String(r.tot).padStart(4) + '   缺可访问名 ' + String(r.bad).padStart(4));
    samples.push(...r.all); badSamples.push(...r.bads);
  }
  console.log('\n合计：纯图标 a/button ' + T + ' 个，其中缺可访问名 ' + BAD + ' 个');
  console.log('\n【有名字的】样例：'); samples.slice(0, 10).forEach(s => console.log('  ' + s));
  console.log('\n【真缺名字的】样例：'); badSamples.slice(0, 8).forEach(s => console.log('  ' + s));
  await b.close();
})().catch(e => { console.log('FAIL ' + e.message.slice(0, 200)); process.exit(1); });
