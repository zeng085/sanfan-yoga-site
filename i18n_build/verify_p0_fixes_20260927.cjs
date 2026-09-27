/* P0 四条修复的前后对比探针（单文件 CSS → 改动即全站生效，故用「多页 × 多视口」验证）
   用法: node verify_p0_fixes_20260927.cjs [--tag=before|after] */
const { chromium } = require('playwright');
const BASE = 'file:///Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16';
const arg = (k, d) => { const m = process.argv.find(s => s.startsWith('--' + k + '=')); return m ? m.split('=')[1] : d; };
const TAG = arg('tag', 'before');

const VPS = [[390, 844], [320, 568], [844, 390]];
const PAGES = ['index.html', 'contact.html', 'products.html', 'pilates/index.html', 'faq.html', 'de/index.html'];

(async () => {
  const b = await chromium.launch();
  console.log(`########## ${TAG} ##########`);
  const agg = { ta: {}, inputFs: {}, toggle: {}, overflow: [], drawer: null, headerH: {} };

  for (const [w, h] of VPS) {
    const ctx = await b.newContext({ viewport: { width: w, height: h }, isMobile: w < 900, hasTouch: w < 900 });
    const p = await ctx.newPage();
    await p.route('**/*', r => /google-analytics|googletagmanager|clarity|facebook|doubleclick/.test(r.request().url()) ? r.abort() : r.continue());
    console.log(`\n=== 视口 ${w}x${h} ===`);

    for (const f of PAGES) {
      await p.goto(`${BASE}/${f}`, { waitUntil: 'domcontentloaded' });
      await p.waitForTimeout(300);
      const r = await p.evaluate(() => {
        const de = document.documentElement;
        // 触控目标类元素
        const sel = 'a[href], button, input, select, textarea, [role="button"], label';
        const ta = {};
        for (const el of document.querySelectorAll(sel)) {
          const cs = getComputedStyle(el);
          if (cs.display === 'none' || cs.visibility === 'hidden') continue;
          const v = cs.touchAction;
          ta[v] = (ta[v] || 0) + 1;
        }
        // 表单字号
        const fi = document.querySelector('.field input, .field select, .field textarea');
        // 汉堡
        const tg = document.querySelector('.menu-toggle');
        const tr = tg ? tg.getBoundingClientRect() : null;
        const hd = document.querySelector('.site-header');
        const nl = document.querySelector('.nav-links');
        const nlcs = nl ? getComputedStyle(nl) : null;
        // 横向溢出
        const over = de.scrollWidth - de.clientWidth;
        let wide = [];
        if (over > 0) {
          for (const el of document.querySelectorAll('body *')) {
            const rc = el.getBoundingClientRect();
            if (rc.width > 0 && rc.right > de.clientWidth + 1) {
              wide.push(`${el.tagName.toLowerCase()}.${String(el.className || '').trim().split(/\s+/)[0]}@${Math.round(rc.right)}`);
              if (wide.length >= 3) break;
            }
          }
        }
        return {
          ta, inputFs: fi ? getComputedStyle(fi).fontSize : null,
          toggle: tr ? `${Math.round(tr.width)}x${Math.round(tr.height)}` : null,
          headerH: hd ? Math.round(hd.getBoundingClientRect().height) : null,
          nlMaxH: nlcs ? nlcs.maxHeight : null, nlOf: nlcs ? nlcs.overflowY : null, nlOb: nlcs ? nlcs.overscrollBehaviorY : null,
          over, wide,
        };
      });
      agg.inputFs[f] = r.inputFs; agg.toggle[f] = r.toggle; agg.headerH[f] = r.headerH;
      for (const k in r.ta) agg.ta[k] = (agg.ta[k] || 0) + r.ta[k];
      if (r.over > 0) agg.overflow.push(`${w}px ${f} 溢出 ${r.over}px  ${r.wide.join(' ')}`);
      const fl = r.over > 0 ? `⚠️ 溢出 ${r.over}px` : '✅ 无溢出';
      console.log(`  ${f.padEnd(24)} 溢出 ${fl.padEnd(16)} 汉堡 ${String(r.toggle).padEnd(8)} header ${r.headerH}px  表单字号 ${r.inputFs || '-'}`);
      if (w === 844) agg.drawer = { nlMaxH: r.nlMaxH, nlOf: r.nlOf, nlOb: r.nlOb };
    }
    await ctx.close();
  }

  console.log(`\n--- 汇总 ${TAG} ---`);
  console.log(`  ① 触控元素 touch-action 分布: ${JSON.stringify(agg.ta)}`);
  console.log(`  ② 汉堡尺寸: ${JSON.stringify(agg.toggle)}`);
  console.log(`  ③ 表单 input 字号: ${JSON.stringify(agg.inputFs)}`);
  console.log(`  ④ 抽屉 max-height=${agg.drawer?.nlMaxH} overflow-y=${agg.drawer?.nlOf} overscroll-y=${agg.drawer?.nlOb}`);
  console.log(`  ⑤ header 高度: ${JSON.stringify(agg.headerH)}`);
  console.log(`  ⑥ 溢出: ${agg.overflow.length ? agg.overflow.join(' | ') : '全 0'}`);

  // 抽屉在横屏下的可达性
  const ctx = await b.newContext({ viewport: { width: 844, height: 390 }, isMobile: true, hasTouch: true });
  const p = await ctx.newPage();
  await p.route('**/*', r => /google-analytics|googletagmanager|clarity|facebook/.test(r.request().url()) ? r.abort() : r.continue());
  await p.goto(`${BASE}/index.html`, { waitUntil: 'domcontentloaded' });
  await p.waitForTimeout(300);
  await (await p.$('.menu-toggle')).click();
  await p.waitForTimeout(350);
  const d = await p.evaluate(() => {
    const nl = document.querySelector('.nav-links');
    const as = nl.querySelectorAll('a');
    const last = as[as.length - 1].getBoundingClientRect();
    nl.scrollTop = 9999;                       // 尝试滚到底
    const after = as[as.length - 1].getBoundingClientRect();
    const cbar = document.querySelector('.cbar');
    const cb = cbar ? cbar.getBoundingClientRect() : null;
    return {
      lastBottomBefore: Math.round(last.bottom), lastBottomAfter: Math.round(after.bottom),
      vh: window.innerHeight, nlScrollTop: nl.scrollTop, canScroll: nl.scrollHeight > nl.clientHeight,
      docScroll: document.scrollingElement.scrollTop,
      cbarTop: cb ? Math.round(cb.top) : null, cbarH: cb ? Math.round(cb.height) : 0,
      cbarZ: cbar ? getComputedStyle(cbar).zIndex : null, nlZ: getComputedStyle(nl).zIndex,
    };
  });
  console.log(`\n--- 横屏 844x390 抽屉可达性 ${TAG} ---`);
  console.log(`  最后一项 bottom: 未滚 ${d.lastBottomBefore} → 滚到底 ${d.lastBottomAfter}  视口 ${d.vh}`);
  console.log(`  抽屉自身可滚=${d.canScroll}  抽屉 scrollTop=${d.nlScrollTop}  页面 scrollTop=${d.docScroll}`);
  console.log(`  .cbar top=${d.cbarTop} 高=${d.cbarH} z-index=${d.cbarZ}（抽屉 z=${d.nlZ}）`);
  console.log(`  判定: ${d.lastBottomAfter <= d.vh ? '✅ 在视口内' : '❌ 超出视口 ' + (d.lastBottomAfter - d.vh) + 'px'}` +
    ` / ${d.cbarTop === null ? '无 cbar' : (d.lastBottomAfter <= d.cbarTop ? '✅ 未被 cbar 遮挡' : '❌ 被 cbar 遮挡 ' + (d.lastBottomAfter - d.cbarTop) + 'px')}`);
  await b.close();
})().catch(e => { console.log('FAIL', e.message.slice(0, 300)); process.exit(1); });
