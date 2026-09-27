/* 实测移动抽屉的真实滚动行为 —— 决定 overscroll-behavior 该不该加、加在哪。
   用法: node probe_drawer_behavior_20260927.cjs [--vp=390] */
const { chromium } = require('playwright');
const BASE = 'file:///Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16';
const arg = (k, d) => { const m = process.argv.find(s => s.startsWith('--' + k + '=')); return m ? m.split('=')[1] : d; };
const VP = +arg('vp', 390);
const HT = +arg('h', 844);
const PAGES = ['index.html', 'products.html', 'pilates/index.html', 'faq.html'];

(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: VP, height: HT }, isMobile: true, hasTouch: true });
  const p = await ctx.newPage();
  await p.route('**/*', r => /google-analytics|googletagmanager|clarity|facebook|doubleclick/.test(r.request().url()) ? r.abort() : r.continue());

  console.log(`##### 视口 ${VP}x844 #####\n`);
  for (const f of PAGES) {
    await p.goto(`${BASE}/${f}`, { waitUntil: 'domcontentloaded' });
    await p.waitForTimeout(400);

    // 展开抽屉
    const tg = await p.$('.menu-toggle');
    if (!tg) { console.log(`${f}: ❌ 无 .menu-toggle`); continue; }
    await tg.click();
    await p.waitForTimeout(350);

    const r = await p.evaluate(() => {
      const nl = document.querySelector('.nav-links');
      const hd = document.querySelector('.site-header');
      const cs = getComputedStyle(nl);
      const hs = hd ? getComputedStyle(hd) : null;
      const btn = document.querySelector('.menu-toggle');
      const bs = btn ? getComputedStyle(btn) : null;
      const br = btn ? btn.getBoundingClientRect() : null;
      return {
        open: nl.classList.contains('open'),
        pos: cs.position, of: cs.overflowY, ob: cs.overscrollBehaviorY,
        nh: Math.round(nl.getBoundingClientRect().height),
        sh: nl.scrollHeight, ch: nl.clientHeight,
        vh: window.innerHeight,
        headerPos: hs ? hs.position : '(无)', headerTop: hs ? hs.top : '',
        bodyOB: getComputedStyle(document.body).overscrollBehaviorY,
        htmlOB: getComputedStyle(document.documentElement).overscrollBehaviorY,
        htmlOS: getComputedStyle(document.documentElement).overflowY,
        bodyOS: getComputedStyle(document.body).overflowY,
        toggle: br ? `${Math.round(br.width)}x${Math.round(br.height)}` : '(无)',
        toggleTa: bs ? bs.touchAction : '',
        // 抽屉内各项可见性
        lastItemBottom: (() => {
          const as = nl.querySelectorAll('a');
          if (!as.length) return null;
          return Math.round(as[as.length - 1].getBoundingClientRect().bottom);
        })(),
        nItems: nl.querySelectorAll('a').length,
      };
    });

    console.log(`--- ${f}`);
    console.log(`    抽屉 open=${r.open}  position=${r.pos}  overflow-y=${r.of}  overscroll-y=${r.ob}`);
    console.log(`    抽屉高 ${r.nh}px  scrollHeight ${r.sh}  clientHeight ${r.ch}  视口高 ${r.vh}`);
    console.log(`    header position=${r.headerPos}  最后一项 bottom=${r.lastItemBottom} (${r.nItems} 项)  → ${r.lastItemBottom > r.vh ? '⚠️ 超出视口' : '在视口内'}`);
    console.log(`    汉堡 ${r.toggle}  touch-action=${r.toggleTa}`);
    console.log(`    body/html overscroll-y=${r.bodyOB}/${r.htmlOB}   overflow-y=${r.bodyOS}/${r.htmlOS}`);

    // 在抽屉上滚动，看是抽屉滚还是页面滚
    const before = await p.evaluate(() => ({ doc: document.scrollingElement.scrollTop, nl: document.querySelector('.nav-links').scrollTop }));
    await p.mouse.move(VP / 2, r.vh - 100);
    await p.mouse.wheel(0, 600);
    await p.waitForTimeout(320);
    const after = await p.evaluate(() => ({ doc: document.scrollingElement.scrollTop, nl: document.querySelector('.nav-links').scrollTop }));
    console.log(`    抽屉内滚动 600px → 页面 scrollTop ${before.doc}→${after.doc}  抽屉 scrollTop ${before.nl}→${after.nl}`);

    // 关闭
    await tg.click().catch(() => { });
    await p.waitForTimeout(250);
    console.log('');
  }
  await b.close();
})().catch(e => { console.log('FAIL', e.message.slice(0, 300)); process.exit(1); });
