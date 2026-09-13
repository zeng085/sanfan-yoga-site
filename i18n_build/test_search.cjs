// 全站搜索功能验证：英文站回归 + 6 语言站新启用
// 用法：本地 http://127.0.0.1:8123 或线上 https://fjsanfan.com
const { chromium } = require('playwright');

const BASE = process.env.BASE || 'http://127.0.0.1:8123';
const CASES = [
  // 英文根页 ROOT 为空 → href 是相对路径 products/x.html（不含前导斜杠）
  { page: '', q: 'tpe yoga mat', expect: 'products/' },
  { page: 'de/', q: 'Yogamatte', expect: '/de/' },
  { page: 'de/products/ab-wheel.html', q: 'Rad', expect: '/de/' },
  { page: 'ja/', q: 'ヨガマット', expect: '/ja/' },
  { page: 'ko/', q: '요가', expect: '/ko/' },
  { page: 'fr/', q: 'tapis', expect: '/fr/' },
  { page: 'it/', q: 'tappetino', expect: '/it/' },
  { page: 'es/', q: 'esterilla', expect: '/es/' },
];

(async () => {
  const b = await chromium.launch();
  let fail = 0;
  for (const c of CASES) {
    const p = await b.newPage({ viewport: { width: 1440, height: 900 } });
    const errs = [];
    p.on('response', (r) => { if (r.status() >= 400) errs.push(r.status() + ' ' + r.url()); });
    p.on('pageerror', (e) => errs.push('JS: ' + e.message.slice(0, 80)));
    await p.goto(BASE + '/' + c.page, { waitUntil: 'load', timeout: 45000 });
    await p.waitForTimeout(900);

    const hasBtn = await p.locator('.sr-btn').count();
    if (!hasBtn) { console.log('❌ 无搜索按钮  /' + c.page); fail++; await p.close(); continue; }

    await p.click('.sr-btn');
    await p.waitForTimeout(700);
    const ph = await p.getAttribute('.sr-input', 'placeholder');
    await p.fill('.sr-input', c.q);
    await p.waitForTimeout(600);
    const n = await p.locator('.sr-item').count();
    const first = n ? await p.locator('.sr-item').first().getAttribute('href') : null;
    const title = n ? (await p.locator('.sr-item .sr-t').first().textContent()).trim() : '';
    const badge = n ? (await p.locator('.sr-item .sr-badge').first().textContent()).trim() : '';
    const hot = await p.locator('.sr-hints .h-row button').count();

    const ok = n > 0 && first && first.indexOf(c.expect) >= 0;
    if (!ok) fail++;
    console.log(
      (ok ? '✅' : '❌') + ' /' + (c.page || '(en)') +
      '  q="' + c.q + '"  结果 ' + n +
      '  首条: ' + (first || '—') + '  「' + title.slice(0, 28) + '」[' + badge + ']' +
      '  热门词 ' + hot + '  4xx ' + errs.length
    );
    console.log('      占位符: ' + (ph || '').slice(0, 70));
    if (errs.length) console.log('      ⚠ ' + errs.slice(0, 3).join(' | '));
    await p.close();
  }
  await b.close();
  console.log(fail === 0 ? '\n✅ 搜索全部通过（含英文站回归）' : '\n❌ 失败 ' + fail + ' 项');
  process.exit(fail ? 1 : 0);
})();
