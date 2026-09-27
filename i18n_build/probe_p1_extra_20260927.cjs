/* P1 补充探针：
 *  B2. 锚点落点（等滚动真正停稳再量，避免把「平滑滚动进行中」误判为遮挡）
 *  A2. .sr-input（JS 注入的搜索弹层）焦点可见性——不在初始可聚焦名单里
 *  E.  用 CDP 模拟刘海，测 env(safe-area-inset-*) 是否会变成非 0
 *      （若桌面 Chromium 不把 viewport-fit=cover 当回事，那 CSS env() 就永远是 0，
 *       P1-4 光加 CSS 等于没做——必须把这件事钉死，不能靠推断）
 */
const { chromium } = require('playwright');
const BASE = 'file:///Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16';
const BLOCK = r => /google-analytics|googletagmanager|clarity|facebook/.test(r.request().url()) ? r.abort() : r.continue();

(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1280, height: 800 } });
  const p = await ctx.newPage();
  await p.route('**/*', BLOCK);

  // ── B2. 锚点落点（等滚停）──
  console.log('=== B2. #lines 锚点（等滚动停稳）===');
  for (const vp of [[390, 844], [1280, 800]]) {
    await p.setViewportSize({ width: vp[0], height: vp[1] });
    await p.goto(`${BASE}/pilates/index.html#lines`, { waitUntil: 'domcontentloaded' });
    const st = await p.evaluate(async () => {
      // 轮询直到 scrollY 连续 6 帧不变（最多 6s）
      let last = -1, same = 0, t0 = Date.now();
      while (Date.now() - t0 < 6000) {
        const y = Math.round(window.scrollY);
        if (y === last) { if (++same >= 6) break; } else { same = 0; last = y; }
        await new Promise(r => requestAnimationFrame(r));
      }
      const t = document.querySelector('#lines').getBoundingClientRect();
      const h = document.querySelector('.site-header').getBoundingClientRect();
      return { scrollY: Math.round(window.scrollY), tTop: Math.round(t.top), docTop: Math.round(t.top + window.scrollY),
               hBottom: Math.round(h.bottom), hH: Math.round(h.height), settled: same >= 6 };
    });
    console.log(`  ${vp[0]}x${vp[1]} 滚停=${st.settled} scrollY=${st.scrollY}  #lines 文档内 y=${st.docTop}  视口内 top=${st.tTop}  header bottom=${st.hBottom}`);
    console.log(`        → ${st.tTop < st.hBottom ? '❌ 标题被固定头部遮挡 ' + (st.hBottom - st.tTop) + 'px' : '✅ 可见（top≥' + st.hBottom + '）'}`);
  }
  await p.setViewportSize({ width: 390, height: 844 });

  // ── A2. 搜索弹层输入框 ──
  console.log('\n=== A2. 搜索弹层 .sr-input 焦点指示 ===');
  await p.goto(`${BASE}/index.html`, { waitUntil: 'domcontentloaded' });
  await p.waitForTimeout(400);
  try {
    const n = await p.evaluate(() => {
      const btn = document.querySelector('.sr-btn');
      if (!btn) return { ok: false, why: '没有 .sr-btn' };
      const cs = getComputedStyle(btn);
      btn.click();                       // JS 触发：按钮在 390 视口不可见时 click() 仍有效
      return { ok: true, vis: cs.display + '/' + cs.visibility };
    });
    if (!n.ok) { console.log('  ⚠️ ' + n.why + '，跳过'); throw { skip: true }; }
    console.log(`  .sr-btn display/visibility = ${n.vis}（用 JS click 触发）`);
    await p.waitForTimeout(600);
    const r = await p.evaluate(() => {
      const el = document.querySelector('.sr-input');
      if (!el) return { err: '弹层里没有 .sr-input' };
      const before = getComputedStyle(el);
      const un = { ow: before.outlineWidth, os: before.outlineStyle, bs: before.boxShadow, bc: before.borderColor, bg: before.backgroundColor };
      el.focus();
      const forced = { ow: getComputedStyle(el).outlineWidth, os: getComputedStyle(el).outlineStyle,
                       bs: getComputedStyle(el).boxShadow, bc: getComputedStyle(el).borderColor, bg: getComputedStyle(el).backgroundColor };
      return { un, forced, fv: el.matches(':focus-visible'),
               srBoxShadow: getComputedStyle(document.querySelector('.sr-box')).boxShadow,
               esc: !!document.querySelector('.sr-esc') };
    });
    if (r.err) console.log('  ' + r.err);
    else {
      console.log(`  未聚焦: outline=${r.un.os}/${r.un.ow}  border=${r.un.bc}  bg=${r.un.bg}  box-shadow=${r.un.bs.slice(0, 28)}`);
      console.log(`  已聚焦: outline=${r.forced.os}/${r.forced.ow}  border=${r.forced.bc}  bg=${r.forced.bg}  box-shadow=${r.forced.bs.slice(0, 28)}`);
      const hasOutline = !(r.forced.os === 'none' || parseFloat(r.forced.ow) === 0);
      const changed = r.forced.bs !== r.un.bs || r.forced.bc !== r.un.bc || r.forced.bg !== r.un.bg;
      console.log(`  → outline 生效=${hasOutline}  其它样式有变化=${changed}  判定: ${hasOutline || changed ? '有指示' : '❌ 完全无焦点指示（WIG NEVER outline:0 无替代）'}`);
    }
    await p.keyboard.press('Escape');
    await p.waitForTimeout(300);
  } catch (e) {
    if (!e || !e.skip) console.log('  A2 段异常: ' + String(e && e.message).slice(0, 160));
  }

  // ── E. CDP 模拟刘海 → env() 是否非 0 ──
  console.log('\n=== E. CDP 刘海模拟下的 env(safe-area-inset-*) ===');
  const ctx3 = await b.newContext({ viewport: { width: 844, height: 390 }, isMobile: true, hasTouch: true });
  const p3 = await ctx3.newPage();
  await p3.route('**/*', BLOCK);
  const cdp = await ctx3.newCDPSession(p3);
  const probeEnv = async (label) => {
    await p3.goto(`${BASE}/pilates/index.html`, { waitUntil: 'domcontentloaded' });
    await p3.waitForTimeout(300);
    const v = await p3.evaluate(() => {
      const d = document.createElement('div');
      d.style.cssText = 'position:absolute;padding:env(safe-area-inset-top,0px) env(safe-area-inset-right,0px) env(safe-area-inset-bottom,0px) env(safe-area-inset-left,0px)';
      document.body.appendChild(d);
      const cs = getComputedStyle(d); const out = cs.padding; d.remove();
      const m = document.querySelector('meta[name="viewport"]');
      return { padding: out, meta: m ? m.content : null };
    });
    console.log(`  [${label}] meta="${v.meta}"  env 解析 = "${v.padding}"`);
  };
  try {
    await probeEnv('无刘海基线');
    try {
      await cdp.send('Emulation.setDisplayFeaturesOverride', { features: [{ orientation: 'vertical', offset: 0, maskLength: 44 }] });
      console.log('  ✓ setDisplayFeaturesOverride 调用成功');
    } catch (e) {
      console.log('  ⚠️ setDisplayFeaturesOverride 失败: ' + e.message.split('\n')[0]);
      try {
        await cdp.send('Emulation.setDisplayFeaturesOverride', { features: [{ bounds: { x: 0, y: 0, width: 44, height: 390 }, type: 'cutout' }] });
        console.log('  ✓ bounds+type 形式调用成功');
      } catch (e2) { console.log('  ⚠️ bounds 形式也失败: ' + e2.message.split('\n')[0]); }
    }
    await probeEnv('模拟刘海后');
  } catch (e) { console.log('  CDP 段异常: ' + e.message.slice(0, 160)); }
  await ctx3.close();

  await b.close();
})().catch(e => { console.log('FAIL ' + e.message.slice(0, 300)); process.exit(1); });
