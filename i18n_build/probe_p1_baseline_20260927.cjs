/* P1 基线/复测探针：焦点可见性 / 锚点被固定头部遮挡 / prefers-reduced-motion / safe-area
 *
 * 用法：
 *   node i18n_build/probe_p1_baseline_20260927.cjs --tag=before
 *
 * ⚠️ 关键约束：`:focus-visible` 必须用**真实键盘 Tab** 触发。
 *    `el.focus()` 是脚本聚焦，Chrome 判定为「非键盘交互」→ 不会匹配 :focus-visible
 *    （文本框例外，它们永远匹配），所以用脚本 focus() 测会得出完全错误的结论。
 * ⚠️ 为了「同一次 Tab 序列里对比聚焦/未聚焦样式」，不能 blur（blur 会把 Tab 位置归零）。
 *    做法：先给全部可聚焦元素打 data-p1i 索引并记下未聚焦态，Tab 时按索引取回基线比对。
 */
const { chromium } = require('playwright');

const arg = (k, d) => { const a = process.argv.find(x => x.startsWith('--' + k + '=')); return a ? a.split('=').slice(1).join('=') : d; };
const TAG = arg('tag', 'before');
const BASE = 'file:///Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16';
const PAGES = ['index.html', 'contact.html', 'pilates/index.html'];
const SEL = 'a[href],button,input,select,textarea,summary,[tabindex]:not([tabindex="-1"])';
const BLOCK = r => /google-analytics|googletagmanager|clarity|facebook/.test(r.request().url()) ? r.abort() : r.continue();

(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  const p = await ctx.newPage();
  await p.route('**/*', BLOCK);

  console.log(`########## P1 探针  tag=${TAG} ##########`);
  console.log(`（视口 390x844，真实键盘 Tab）\n`);

  // ─────────────────────────────────────────────────────────
  // A. 焦点可见性
  // ─────────────────────────────────────────────────────────
  console.log('=== A. 焦点可见性（Tab 前 30 个可聚焦元素）===');
  let gTot = 0, gNoVis = 0, gFv = 0, gUntested = 0;
  const noVisSamples = [];
  for (const f of PAGES) {
    await p.goto(`${BASE}/${f}`, { waitUntil: 'domcontentloaded' });
    await p.waitForTimeout(350);
    const base = await p.evaluate((SEL) => {
      const els = [...document.querySelectorAll(SEL)].filter(e => {
        const r = e.getBoundingClientRect(); return r.width > 1 && r.height > 1;
      });
      return els.map((e, i) => {
        e.setAttribute('data-p1i', String(i));
        const cs = getComputedStyle(e);
        return { i, tag: e.tagName.toLowerCase(), cls: String(e.className || '').trim().split(/\s+/)[0] || '',
                 ow: cs.outlineWidth, os: cs.outlineStyle, bs: cs.boxShadow, bc: cs.borderColor };
      });
    }, SEL);

    const visible = [];
    for (let k = 0; k < 30; k++) {
      await p.keyboard.press('Tab');
      const r = await p.evaluate(() => {
        const el = document.activeElement;
        if (!el || !el.getAttribute) return { stop: 'no-active' };
        const attr = el.getAttribute('data-p1i');
        if (attr === null) return { stop: 'left-page(' + el.tagName.toLowerCase() + ')' };
        const cs = getComputedStyle(el);
        return { i: +attr, tag: el.tagName.toLowerCase(), cls: String(el.className || '').trim().split(/\s+/)[0] || '',
                 fv: el.matches(':focus-visible'), ow: cs.outlineWidth, os: cs.outlineStyle, oc: cs.outlineColor,
                 bs: cs.boxShadow, bc: cs.borderColor,
                 txt: (el.innerText || el.value || '').trim().replace(/\s+/g, ' ').slice(0, 20) };
      });
      if (r.stop) { gUntested++; break; }
      visible.push(r);
    }

    let novis = 0, fv = 0;
    for (const r of visible) {
      const u = base.find(x => x.i === r.i) || {};
      const hasOutline = !(r.os === 'none' || parseFloat(r.ow) === 0);
      const chgBox = r.bs !== u.bs;
      const chgBorder = r.bc !== u.bc;
      if (r.fv) fv++;
      if (!hasOutline && !chgBox && !chgBorder) {
        novis++;
        if (noVisSamples.length < 6) noVisSamples.push(`${f}  ${r.tag}.${r.cls}  「${r.txt}」  outline=${r.os}/${r.ow}`);
      }
    }
    gTot += visible.length; gNoVis += novis; gFv += fv;
    console.log(`  ${f.padEnd(22)} 可聚焦 ${String(base.length).padStart(3)}  实测 ${String(visible.length).padStart(2)}  匹配:focus-visible ${String(fv).padStart(2)}  ❌无任何可见指示 ${novis}`);
  }
  console.log(`  合计：实测 ${gTot} 个，匹配 :focus-visible ${gFv} 个，❌无可见指示 ${gNoVis} 个`);
  if (noVisSamples.length) { console.log('  无可见指示样例：'); noVisSamples.forEach(s => console.log('    ' + s)); }

  // ─────────────────────────────────────────────────────────
  // A3. 定点验证表单控件与搜索框（Tab 只走前 30 个，走不到它们）
  //     ⚠️ 文本框/搜索框属「需要键盘输入」的元素，Chrome 判定它们**永远**匹配
  //        :focus-visible（与按钮不同），所以这里用 focus() 触发是有效的。
  // ─────────────────────────────────────────────────────────
  console.log('\n=== A3. 定点：.field 控件 与 .sr-input ===');
  await p.goto(`${BASE}/contact.html`, { waitUntil: 'domcontentloaded' });
  await p.waitForTimeout(400);
  const a3 = await p.evaluate(() => {
    const out = [];
    for (const el of document.querySelectorAll('.field input, .field select, .field textarea')) {
      const un = getComputedStyle(el);
      const b = { ow: un.outlineWidth, os: un.outlineStyle, bs: un.boxShadow, bc: un.borderColor };
      el.focus();
      const f = getComputedStyle(el);
      out.push({ what: el.tagName.toLowerCase() + (el.type ? '[' + el.type + ']' : ''), fv: el.matches(':focus-visible'), b,
                 f: { ow: f.outlineWidth, os: f.outlineStyle, oc: f.outlineColor, bs: f.boxShadow, bc: f.borderColor } });
      el.blur();
    }
    return out;
  });
  for (const r of a3) {
    const solid = !(r.f.os === 'none' || parseFloat(r.f.ow) === 0);
    console.log(`  .field ${r.what.padEnd(14)} :focus-visible=${r.fv}  聚焦后 outline=${r.f.os}/${r.f.ow} ${r.f.oc}  border ${r.b.bc} → ${r.f.bc}`);
    console.log(`         → ${solid ? '✅ 有实心焦点环' : (r.f.bc !== r.b.bc ? '⚠️ 仅 border 变色，无焦点环' : '❌ 无任何可见指示')}`);
  }
  if (!a3.length) console.log('  ⚠️ contact.html 上没有 .field 控件');

  const sr = await p.evaluate(async () => {
    const btn = document.querySelector('.sr-btn');
    if (!btn) return null;
    btn.click();
    await new Promise(r => setTimeout(r, 400));
    const el = document.querySelector('.sr-input');
    if (!el) return null;
    const un = getComputedStyle(el);
    const b = { ow: un.outlineWidth, os: un.outlineStyle, bs: un.boxShadow, bc: un.borderColor, bg: un.backgroundColor };
    el.focus();
    const f = getComputedStyle(el);
    return { fv: el.matches(':focus-visible'), b,
             f: { ow: f.outlineWidth, os: f.outlineStyle, oc: f.outlineColor, bs: f.boxShadow, bc: f.borderColor, bg: f.backgroundColor } };
  });
  if (!sr) console.log('  .sr-input: 未能打开搜索弹层或找不到该元素');
  else {
    const solid = !(sr.f.os === 'none' || parseFloat(sr.f.ow) === 0);
    console.log(`  .sr-input      :focus-visible=${sr.fv}  聚焦后 outline=${sr.f.os}/${sr.f.ow} ${sr.f.oc}  border ${sr.b.bc} → ${sr.f.bc}  bg 变化=${sr.b.bg !== sr.f.bg}`);
    console.log(`         → ${solid ? '✅ 有实心焦点环' : '❌ 仍无任何焦点指示'}`);
  }
  await p.keyboard.press('Escape');

  // ─────────────────────────────────────────────────────────
  // B. 锚点是否被固定头部遮挡
  // ─────────────────────────────────────────────────────────
  console.log('\n=== B. 页内锚点 #lines 落点 vs 固定头部 ===');
  for (const vp of [[390, 844], [1280, 800]]) {
    await p.setViewportSize({ width: vp[0], height: vp[1] });
    await p.goto(`${BASE}/pilates/index.html#lines`, { waitUntil: 'domcontentloaded' });
    // ⚠️ 必须等平滑滚动**真正停稳**再量：固定 waitForTimeout 会把「还在滚」误判成遮挡
    const a = await p.evaluate(async () => {
      let last = -1, same = 0; const t0 = Date.now();
      while (Date.now() - t0 < 6000) {
        const y = Math.round(window.scrollY);
        if (y === last) { if (++same >= 6) break; } else { same = 0; last = y; }
        await new Promise(r => requestAnimationFrame(r));
      }
      const t = document.querySelector('#lines');
      const h = document.querySelector('.site-header');
      const tr = t.getBoundingClientRect(), hr = h.getBoundingClientRect();
      const cs = getComputedStyle(t);
      return { tTop: Math.round(tr.top), hBottom: Math.round(hr.bottom), hH: Math.round(hr.height),
               hSticky: getComputedStyle(h).position, smt: cs.scrollMarginTop, scrollY: Math.round(window.scrollY) };
    });
    const covered = a.tTop < a.hBottom;
    console.log(`  ${vp[0]}x${vp[1]}  #lines top=${String(a.tTop).padStart(5)}  header bottom=${a.hBottom} (h=${a.hH}, ${a.hSticky})  scroll-margin-top=${a.smt}`);
    console.log(`            → ${covered ? '❌ 被头部遮挡 ' + (a.hBottom - a.tTop) + 'px' : '✅ 未被遮挡'}`);
  }
  await p.setViewportSize({ width: 390, height: 844 });

  // ─────────────────────────────────────────────────────────
  // C. prefers-reduced-motion
  // ─────────────────────────────────────────────────────────
  console.log('\n=== C. prefers-reduced-motion: reduce 下的动效 ===');
  const ctx2 = await b.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
  const p2 = await ctx2.newPage();
  await p2.route('**/*', BLOCK);
  await p2.goto(`${BASE}/index.html`, { waitUntil: 'domcontentloaded' });
  await p2.waitForTimeout(400);
  const rm = await p2.evaluate(() => {
    const html = getComputedStyle(document.documentElement);
    let nz = 0, tot = 0, maxDur = 0; const ex = [];
    for (const el of document.querySelectorAll('body *')) {
      const cs = getComputedStyle(el);
      if (cs.transitionDuration === '0s') continue;
      tot++;
      const durs = cs.transitionDuration.split(',').map(s => parseFloat(s));
      const mx = Math.max(...durs);
      if (mx > maxDur) maxDur = mx;
      // ⚠️ 判据用 ≥50ms 而不是 >0：减弱动效的写法是 .01ms（=1e-05s），
      //    它在数值上 >0 但在观感上是「瞬间」，用 >0 判会把修好的状态误报成没修。
      if (mx >= 0.05) {
        nz++;
        if (ex.length < 4) ex.push(el.tagName.toLowerCase() + '.' + (String(el.className || '').trim().split(/\s+/)[0] || '-') + '  ' + cs.transitionDuration);
      }
    }
    return { mq: matchMedia('(prefers-reduced-motion: reduce)').matches, scrollBehavior: html.scrollBehavior, nz, tot, maxDur, ex };
  });
  console.log(`  媒体查询命中=${rm.mq}   html scroll-behavior = ${rm.scrollBehavior}`);
  console.log(`  ⚠️ 仍在动（transition-duration ≥50ms）的元素：${rm.nz} / ${rm.tot}   全站最长单值 = ${rm.maxDur}s`);
  rm.ex.forEach(s => console.log('    ' + s));
  const jsSrc = require('fs').readFileSync('/Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16/assets/js/main.js', 'utf8');
  console.log(`  main.js 里 behavior:'smooth' 出现 ${(jsSrc.match(/behavior:\s*'smooth'/g) || []).length} 处；matchMedia 判断 ${(jsSrc.match(/prefers-reduced-motion/g) || []).length} 处`);
  await ctx2.close();

  // ─────────────────────────────────────────────────────────
  // D. safe-area / viewport-fit
  // ─────────────────────────────────────────────────────────
  console.log('\n=== D. 安全区（safe-area-inset）===');
  const sa = await p.evaluate(() => {
    const m = document.querySelector('meta[name="viewport"]');
    const d = document.createElement('div');
    d.style.cssText = 'position:absolute;padding-bottom:env(safe-area-inset-bottom, 0px);padding-left:env(safe-area-inset-left, 0px)';
    document.body.appendChild(d);
    const cs = getComputedStyle(d);
    const v = { pb: cs.paddingBottom, pl: cs.paddingLeft };
    d.remove();
    const cb = document.querySelector('.cbar');
    return { meta: m ? m.content : null, envOK: CSS.supports('padding-bottom', 'env(safe-area-inset-bottom)'), envVal: v,
             cbarPB: cb ? getComputedStyle(cb).paddingBottom : null };
  });
  console.log(`  meta viewport      : ${sa.meta}`);
  console.log(`  含 viewport-fit     : ${/viewport-fit/.test(sa.meta || '') ? '有' : '❌ 无（则 env() 恒为 0，加 CSS 也无效）'}`);
  console.log(`  浏览器支持 env()    : ${sa.envOK}   实测解析值 pb=${sa.envVal.pb} pl=${sa.envVal.pl}（桌面无刘海→0 属正常）`);
  console.log(`  .cbar padding-bottom: ${sa.cbarPB}`);

  await b.close();
})().catch(e => { console.log('FAIL ' + e.message.slice(0, 300)); process.exit(1); });
