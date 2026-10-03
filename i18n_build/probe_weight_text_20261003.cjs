// 客户体感两项实测：① 小字分布（<12px）在长页里的分布 ② 首屏真实下载体积/请求数
// 2026-10-03 —— 客户视角：老板用手机打开页面，第一屏等多久、看不看得清
const { chromium } = require('playwright');
const argv = process.argv.slice(2);
const arg = (k, d) => { const i = argv.indexOf('--' + k); if (i >= 0) return argv[i + 1];
  const m = argv.find(a => a.startsWith('--' + k + '=')); return m ? m.slice(('--' + k + '=').length) : d; };
const BASE = arg('base', 'http://127.0.0.1:8881');
const PAGES = [
  { n: 'home-de',  u: '/de/index.html' },
  { n: 'home-en',  u: '/index.html' },
  { n: 'pilates',  u: '/pilates/pilates-reformer.html' },
  { n: 'product',  u: '/products/alignment-line-tpe-yoga-mat.html' },
  { n: 'contact',  u: '/contact.html' },
];

(async () => {
  const b = await chromium.launch();
  for (const p of PAGES) {
    const page = await b.newPage({ viewport: { width: 390, height: 844 } });
    // 计量传输体积
    const bytes = { total: 0, byType: {}, count: 0, byHost: {} };
    page.on('response', async (res) => {
      try {
        const h = res.headers();
        const len = parseInt(h['content-length'] || '0', 10);
        const ct = (h['content-type'] || '?').split(';')[0];
        const host = new URL(res.url()).host;
        bytes.total += len; bytes.count++;
        bytes.byType[ct] = (bytes.byType[ct] || 0) + len;
        bytes.byHost[host] = (bytes.byHost[host] || 0) + len;
      } catch (e) {}
    });
    const t0 = Date.now();
    await page.goto(BASE + p.u, { waitUntil: 'networkidle', timeout: 60000 });
    const loadMs = Date.now() - t0;
    const perf = await page.evaluate(() => {
      const nav = performance.getEntriesByType('navigation')[0] || {};
      const fcp = (performance.getEntriesByName('first-contentful-paint')[0] || {}).startTime || null;
      // 小字分布
      const tiny = {};
      document.querySelectorAll('p, li, td, th, dd, dt, span, a, button, label, figcaption, h1, h2, h3, h4').forEach(el => {
        if (!el.textContent || !el.textContent.trim()) return;
        if (el.children.length > 2) return;
        const f = Math.round(parseFloat(getComputedStyle(el).fontSize) * 10) / 10;
        if (f > 0 && f < 12) {
          const k = el.tagName.toLowerCase() + (typeof el.className === 'string' && el.className ? '.' + el.className.trim().split(/\s+/)[0] : '');
          tiny[k] = (tiny[k] || 0) + 1;
        }
      });
      return { domContentLoaded: Math.round(nav.domContentLoadedEventEnd || 0), fcp: fcp ? Math.round(fcp) : null,
               imgs: document.images.length, tiny,
               bodyText: (document.body.innerText || '').length };
    });
    const top = Object.entries(bytes.byType).sort((a, x) => x[1] - a[1]).slice(0, 5)
      .map(([k, v]) => `${k.split('/').pop()} ${(v / 1024).toFixed(0)}K`).join('  ');
    console.log(`\n■ ${p.n}`);
    console.log(`   首屏传输 ${(bytes.total / 1024).toFixed(0)} KB / ${bytes.count} 请求  FCP ${perf.fcp}ms  DCL ${perf.domContentLoaded}ms  (networkidle ${loadMs}ms)`);
    console.log(`   构成: ${top}`);
    const hosts = Object.entries(bytes.byHost).filter(([h]) => !h.includes('127.0.0.1')).map(([h, v]) => `${h} ${(v / 1024).toFixed(0)}K`);
    if (hosts.length) console.log(`   站外: ${hosts.join('  ')}   ← 第三方直连会拖慢首屏`);
    const tiny = Object.entries(perf.tiny).sort((a, x) => x[1] - a[1]);
    if (tiny.length) console.log(`   小字(<12px) 合计 ${Object.values(perf.tiny).reduce((a, b) => a + b, 0)} 处: ` + tiny.slice(0, 8).map(([k, v]) => `${k}×${v}`).join('  '));
    await page.close();
  }
  await b.close();
})();
