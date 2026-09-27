#!/usr/bin/env node
/**
 * 移动端 WIG 体检 —— 浏览器实测（第 2 层）  2026-09-27
 *
 * 判据来源：i18n_build/reference/vercel_wig_AGENTS.md（vercel-labs 官方）
 *   MUST: Hit target ≥24px (mobile ≥44px); if visual <24px, expand hit area
 *   MUST: touch-action: manipulation to prevent double-tap zoom
 *   SHOULD: -webkit-tap-highlight-color
 *   MUST: overscroll-behavior: contain in modals/drawers
 *   MUST: :focus-visible 可见焦点环
 *   MUST: Avoid unwanted scrollbars; fix overflows
 *   SHOULD: <meta name="theme-color"> 匹配页背景
 *
 * ⚠️ 防误报（关键设计）：
 *   - 正文内联链（<p>/<li>/<td>/.article 里的文本链）豁免 44px —— 真实网站做不到，
 *     且跨类对比会得出相反结论（项目已有同类教训）。
 *   - 排除 display:none / visibility:hidden / 0 尺寸。
 *   - 不用 networkidle（会被 GA 拦住）→ 用 domcontentloaded。
 *
 * 用法: node audit_mobile_wig_browser_20260927.cjs [--vp=390] [--base=http://127.0.0.1:8851]
 */
const { chromium } = require('playwright');

const argv = process.argv.slice(2);
const VP = Number((argv.find(a => a.startsWith('--vp=')) || '--vp=390').split('=')[1]);
const BASE = (argv.find(a => a.startsWith('--base=')) || '--base=http://127.0.0.1:8851').split('=')[1];

const PAGES = [
  'index.html',
  'products.html',
  'products/ab-wheel.html',
  'materials.html',
  'faq.html',
  'contact.html',
  'pilates/index.html',
  'pilates/pilates-reformer.html',
  'pilates/pilates-wunda-chair.html',
  'blog.html',
  'de/index.html',
  'ja/index.html',
];

const PROBE = () => {
  const results = { targets: [], touchActions: {}, tapHighlight: {}, metaTheme: null, bodyBg: null, overflow: null, drawer: null, err: null };
  try {
    results.bodyBg = getComputedStyle(document.body).backgroundColor;
    const mt = document.querySelector('meta[name="theme-color"]');
    results.metaTheme = mt ? mt.getAttribute('content') : null;
    results.overflow = {
      doc: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      body: document.body.scrollWidth - document.documentElement.clientWidth,
    };

    const sel = 'a[href], button, input:not([type="hidden"]), select, textarea, [role="button"], [tabindex]:not([tabindex="-1"])';
    const vis = el => {
      const s = getComputedStyle(el);
      if (s.display === 'none' || s.visibility === 'hidden' || Number(s.opacity) === 0) return false;
      const r = el.getBoundingClientRect();
      return r.width > 0 && r.height > 0;
    };
    const isInline = el => {
      if (el.tagName !== 'A') return false;
      if (!(el.textContent || '').trim()) return false;
      const c = (el.className || '') + ' ' + ((el.parentElement && el.parentElement.className) || '');
      if (/btn|button|cta|tab|chip|pill/i.test(c)) return false;
      return !!el.closest('p, li, td, dd, .article, .pc-body, .faq-a, .cfaq, .ilink, .blog-body, .lang-zh');
    };
    const kind = el => {
      if (isInline(el)) return 'inline';
      const tag = el.tagName.toLowerCase();
      if (tag === 'input' || tag === 'select' || tag === 'textarea') return 'form';
      const cls = (el.className || '') + '';
      const txt = (el.textContent || '').replace(/\s+/g, '').trim();
      if (/btn|button|cta/i.test(cls) || tag === 'button') return 'btn';
      if (!txt && (el.querySelector('svg,img') || tag === 'a')) return 'icon';
      if (el.closest('nav, .nav, header, footer')) return 'nav';
      return 'other';
    };

    const nodes = document.querySelectorAll(sel);
    for (const el of nodes) {
      if (!vis(el)) continue;
      const r = el.getBoundingClientRect();
      const s = getComputedStyle(el);
      const id = el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).trim().split(/\s+/)[0] : '');
      results.targets.push({
        id, kind: kind(el),
        w: Math.round(r.width * 10) / 10,
        h: Math.round(r.height * 10) / 10,
        min: Math.round(Math.min(r.width, r.height) * 10) / 10,
        ta: s.touchAction,
        tap: s.webkitTapHighlightColor || '',
      });
      results.touchActions[s.touchAction] = (results.touchActions[s.touchAction] || 0) + 1;
      results.tapHighlight[s.webkitTapHighlightColor || '(none)'] = (results.tapHighlight[s.webkitTapHighlightColor || '(none)'] || 0) + 1;
    }

    // 抽屉：点击汉堡后测 overscroll-behavior
    const burger = document.querySelector('.menu-toggle');
    if (burger && getComputedStyle(burger).display !== 'none') {
      const b = { found: true, size: null, panel: null, overscroll: null, bodyOverscroll: null, ta: null };
      const br = burger.getBoundingClientRect();
      b.size = { w: Math.round(br.width * 10) / 10, h: Math.round(br.height * 10) / 10 };
      burger.click();
      const panel = document.querySelector('.nav-links.open, .nav-links.is-open, nav .open');
      if (panel) {
        const ps = getComputedStyle(panel);
        b.panel = (panel.className || '').split(/\s+/)[0];
        b.overscroll = ps.overscrollBehavior;
        b.ta = ps.touchAction;
      }
      b.bodyOverscroll = getComputedStyle(document.body).overscrollBehavior;
      results.drawer = b;
    }
  } catch (e) {
    results.err = String(e).slice(0, 200);
  }
  return results;
};

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: VP, height: 844 }, deviceScaleFactor: 2 });
  await page.route('**/*', r => {
    const u = r.request().url();
    if (/google-analytics|googletagmanager|doubleclick|clarity|facebook/.test(u)) return r.abort();
    return r.continue();
  });

  const allTargets = [];
  const perPage = [];
  console.log(`\n${'='.repeat(76)}`);
  console.log(`移动端 WIG 浏览器实测   视口 ${VP}x844   代表页 ${PAGES.length} 个`);
  console.log('='.repeat(76));
  console.log(`${'页面'.padEnd(38)}${'可点'.padStart(5)}${'<24'.padStart(6)}${'<44'.padStart(6)}${'溢出'.padStart(6)}  汉堡`);
  console.log('-'.repeat(76));

  for (const p of PAGES) {
    try {
      await page.goto(`${BASE}/${p}`, { waitUntil: 'domcontentloaded', timeout: 20000 });
      await page.waitForTimeout(600);
      const r = await page.evaluate(PROBE);
      if (r.err) { console.log(`${p.padEnd(38)}  ⚠️ ${r.err}`); continue; }
      const act = r.targets.filter(t => t.kind !== 'inline');
      const lt24 = act.filter(t => t.min < 24).length;
      const lt44 = act.filter(t => t.min < 44).length;
      const ov = Math.max(r.overflow.doc, r.overflow.body);
      const burgerTxt = r.drawer ? `${r.drawer.size.w || '?'}x${r.drawer.size.h || '?'}` : '—';
      console.log(`${p.padEnd(38)}${String(act.length).padStart(5)}${String(lt24).padStart(6)}${String(lt44).padStart(6)}${String(ov).padStart(6)}  ${burgerTxt}`);
      perPage.push({ page: p, targets: r.targets, overflow: ov, drawer: r.drawer, metaTheme: r.metaTheme, bodyBg: r.bodyBg });
      allTargets.push(...r.targets.map(t => ({ ...t, page: p })));
    } catch (e) {
      console.log(`${p.padEnd(38)}  ❌ ${String(e).split('\n')[0].slice(0, 90)}`);
    }
  }

  // ---------- 汇总 ----------
  const kinds = {};
  for (const t of allTargets) {
    const k = (kinds[t.kind] = kinds[t.kind] || { n: 0, lt24: 0, lt44: 0, mins: [] });
    k.n++; if (t.min < 24) k.lt24++; if (t.min < 44) k.lt44++; k.mins.push(t.min);
  }
  const med = a => { const s = [...a].sort((x, y) => x - y); return s[Math.floor(s.length / 2)]; };

  console.log(`\n${'='.repeat(76)}`);
  console.log('① 触控热区（按类型；inline=正文内联链，按 WIG 精神豁免）');
  console.log('-'.repeat(76));
  console.log(`${'类型'.padEnd(10)}${'数量'.padStart(6)}${'中位边长'.padStart(10)}${'<24px'.padStart(9)}${'<44px'.padStart(9)}`);
  for (const [k, v] of Object.entries(kinds).sort((a, b) => b[1].n - a[1].n)) {
    console.log(`${k.padEnd(10)}${String(v.n).padStart(6)}${String(med(v.mins)).padStart(10)}${String(v.lt24).padStart(9)}${String(v.lt44).padStart(9)}`);
  }

  const worst = allTargets.filter(t => t.kind !== 'inline' && t.min < 24)
    .sort((a, b) => a.min - b.min).slice(0, 14);
  console.log(`\n② 最严重的 <24px 交互控件（前 ${worst.length} 个 / 共 ${allTargets.filter(t => t.kind !== 'inline' && t.min < 24).length} 个）`);
  console.log('-'.repeat(76));
  for (const t of worst) {
    console.log(`  ${String(t.min).padStart(6)}px  ${t.id.slice(0, 40).padEnd(42)}${t.kind.padEnd(7)} ${t.page}`);
  }

  const taSet = {};
  for (const t of allTargets) taSet[t.ta] = (taSet[t.ta] || 0) + 1;
  console.log('\n③ computed touch-action 分布（全站可点元素）');
  console.log('-'.repeat(76));
  for (const [v, n] of Object.entries(taSet).sort((a, b) => b[1] - a[1])) console.log(`  ${String(n).padStart(6)}  ${v}`);
  const tapSet = {};
  for (const t of allTargets) tapSet[t.tap] = (tapSet[t.tap] || 0) + 1;
  console.log('\n④ computed -webkit-tap-highlight-color 分布');
  for (const [v, n] of Object.entries(tapSet).sort((a, b) => b[1] - a[1]).slice(0, 4)) console.log(`  ${String(n).padStart(6)}  ${v}`);

  console.log('\n⑤ 汉堡按钮与抽屉');
  console.log('-'.repeat(76));
  for (const p of perPage) {
    if (!p.drawer) continue;
    const d = p.drawer;
    console.log(`  ${p.page.padEnd(36)} 汉堡 ${d.size.w}x${d.size.h}  面板 ${d.panel || '(未捕获)'}  overscroll=${d.overscroll || '—'}  body=${d.bodyOverscroll || '—'}`);
  }

  console.log('\n⑥ theme-color vs 页背景');
  console.log('-'.repeat(76));
  for (const p of perPage.slice(0, 6)) {
    console.log(`  ${p.page.padEnd(36)} meta=${p.metaTheme || '(无)'}  body=${p.bodyBg}`);
  }

  const ovf = perPage.filter(p => p.overflow > 1);
  console.log(`\n⑦ 横向溢出：${ovf.length}/${perPage.length} 页溢出`);
  for (const p of ovf) console.log(`  ${p.page}  ${p.overflow}px`);

  await browser.close();
  console.log(`\n${'='.repeat(76)}\n`);
})();
