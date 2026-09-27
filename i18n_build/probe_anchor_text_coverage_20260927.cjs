/* 锚点遮挡的**文字级**判定：不是看 #lines 包裹层的 top，而是看「有没有可读文字
   真的落在固定头部那条带子里」。改前/改后各测一次，避免用包裹层坐标夸大或掩盖问题。
   用法：node i18n_build/probe_anchor_text_coverage_20260927.cjs */
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = 'file:///Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16';
const HEAD_CSS = fs.readFileSync('/tmp/p1ab/styles_head.css', 'utf8');

async function measure(b, ver) {
  const ctx = await b.newContext({ viewport: { width: 1280, height: 800 } });
  const p = await ctx.newPage();
  await p.route('**/*', r => /google-analytics|googletagmanager|clarity|facebook/.test(r.request().url()) ? r.abort() : r.continue());
  if (ver === 'before') await p.route('**/assets/css/styles.css*', r => r.fulfill({ contentType: 'text/css', body: HEAD_CSS }));
  await p.goto(`${BASE}/pilates/index.html#lines`, { waitUntil: 'domcontentloaded' });
  const r = await p.evaluate(async () => {
    let last = -1, same = 0; const t0 = Date.now();
    while (Date.now() - t0 < 6000) {
      const y = Math.round(window.scrollY);
      if (y === last) { if (++same >= 6) break; } else { same = 0; last = y; }
      await new Promise(rr => requestAnimationFrame(rr));
    }
    const hd = document.querySelector('.site-header').getBoundingClientRect();
    const t = document.querySelector('#lines');
    const tr = t.getBoundingClientRect();
    // 找出所有「有可见文字且与头部带子(hd.bottom 以上)相交」的元素
    const covered = [];
    for (const el of t.querySelectorAll('*')) {
      const txt = (el.textContent || '').trim();
      if (!txt || el.children.length) continue;          // 只看叶子文本节点
      const r = el.getBoundingClientRect();
      if (r.height < 1 || r.width < 1) continue;
      if (r.top < hd.bottom && r.bottom > hd.top) {
        covered.push({ tag: el.tagName.toLowerCase(), cls: String(el.className || '').trim().slice(0, 24),
                       top: Math.round(r.top), bottom: Math.round(r.bottom), txt: txt.replace(/\s+/g, ' ').slice(0, 34) });
      }
    }
    return { headerBottom: Math.round(hd.bottom),
             tTag: t.tagName.toLowerCase() + '.' + String(t.className || '').trim().split(/\s+/)[0],
             tTop: Math.round(tr.top), tPadTop: getComputedStyle(t).paddingTop,
             smt: getComputedStyle(t).scrollMarginTop, covered, scrollY: Math.round(window.scrollY) };
  });
  await ctx.close();
  return r;
}

(async () => {
  const b = await chromium.launch();
  for (const ver of ['before', 'after']) {
    const r = await measure(b, ver);
    console.log(`\n### ${ver}  scrollY=${r.scrollY}  头部 bottom=${r.headerBottom}`);
    console.log(`    #lines 元素 = ${r.tTag}  视口内 top=${r.tTop}  padding-top=${r.tPadTop}  scroll-margin-top=${r.smt}`);
    console.log(`    被头部那条带子覆盖的文字节点：${r.covered.length} 个`);
    r.covered.forEach(c => console.log(`      ❌ <${c.tag} class="${c.cls}"> top=${c.top} bottom=${c.bottom}  「${c.txt}」`));
    if (!r.covered.length) console.log('      ✅ 没有文字被头部遮挡');
  }
  await b.close();
})().catch(e => { console.log('FAIL ' + e.message.slice(0, 250)); process.exit(1); });
