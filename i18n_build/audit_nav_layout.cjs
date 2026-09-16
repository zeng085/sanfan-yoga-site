// 导航布局体检：多语言 × 多断点，量化「溢出 / 换行 / 与 logo 重叠 / 横向滚动」
//
// 判定口径（别改成凭感觉）：
//  1) 导航是 flex + space-between，一旦内容放不下，浏览器**不会**横向滚动，
//     而是让文字换行、并把 .nav-links 挤到 logo 上 —— 视觉上就是「导航溢出了」。
//     所以三条硬指标：①任一导航项高度 > WRAP_H（换行）②.nav-links 与 .nav-brand 重叠
//     ③.nav-links 右边缘越出 .nav 内容盒。
//  2) 横向滚动单独看 documentElement.scrollWidth，那是另一类缺陷。
// 用法：node i18n_build/audit_nav_layout.cjs [--json]
const { chromium } = require('playwright');

const BASE = process.env.BASE || 'http://127.0.0.1:8848';
const WIDTHS = (process.env.WIDTHS || '1024,1152,1280,1440,1680').split(',').map(Number);
const LANGS = ['', 'de', 'ja', 'ko', 'fr', 'it', 'es'];
const PAGES = ['', 'products.html', 'products/fr2.html', 'blog.html'];
const WRAP_H = 26;   // 单行导航项实测 ~22px；>26 即发生换行

(async () => {
  const b = await chromium.launch();
  const out = [];
  for (const w of WIDTHS) {
    const ctx = await b.newContext({ viewport: { width: w, height: 900 } });
    const page = await ctx.newPage();
    for (const lg of LANGS) {
      for (const p of PAGES) {
        const url = BASE + '/' + (lg ? lg + '/' : '') + p;
        const r = await page.goto(url, { waitUntil: 'domcontentloaded' }).catch(() => null);
        if (!r || !r.ok()) { out.push({ w, lg: lg || 'en', p, err: 'HTTP ' + (r ? r.status() : 'NA') }); continue; }
        await page.waitForTimeout(160);
        const m = await page.evaluate((WRAP_H) => {
          const q = (s) => document.querySelector(s);
          const box = (el) => { if (!el) return null; const b = el.getBoundingClientRect(); return { l: b.left, r: b.right, t: b.top, b: b.bottom, w: b.width, h: b.height }; };
          const nav = q('.nav'), links = q('.nav-links'), brand = q('.nav-brand'), acts = q('.nav-actions');
          if (!nav || !links) return { noNav: true };
          // 汉堡态（.nav-links 被 display:none 收起）不是缺陷，直接跳过 ——
          // 否则隐藏元素的 rect 全 0，会被当成「导航压在 logo 上」的假阳性。
          if (getComputedStyle(links).display === 'none') return { hamburger: true };
          const items = [...links.querySelectorAll(':scope > a, :scope > .nav-drop > a')].map((a) => ({
            txt: (a.textContent || '').trim().slice(0, 24),
            h: Math.round(a.getBoundingClientRect().height),
            w: Math.round(a.getBoundingClientRect().width),
          }));
          const wraps = items.filter((i) => i.h > WRAP_H);
          const nb = box(nav), lb = box(links), bb = box(brand), ab = box(acts);
          // .nav 内容盒右边界（去掉 container 右 padding 后的可用右缘）
          const cs = getComputedStyle(nav);
          const padR = parseFloat(cs.paddingRight) || 0;
          return {
            navRight: Math.round(nb.r - padR),
            linksRight: Math.round(lb.r),
            linksLeft: Math.round(lb.l),
            brandRight: Math.round(bb.r),
            actionsLeft: Math.round(ab.l),
            overlapBrand: Math.round(bb.r - lb.l),      // >0 = 与 logo 重叠
            overlapActions: Math.round(lb.r - ab.l),
            overflowRight: Math.round(lb.r - (nb.r - padR)),
            wraps: wraps.map((x) => x.txt + ':' + x.h),
            maxItemH: Math.max(0, ...items.map((i) => i.h)),
            docScroll: document.documentElement.scrollWidth - window.innerWidth,
            navH: Math.round(nb.h),
            linksH: Math.round(lb.h),
          };
        }, WRAP_H).catch((e) => ({ evalErr: String(e).slice(0, 120) }));
        out.push({ w, lg: lg || 'en', p, ...m });
      }
    }
    await ctx.close();
  }
  await b.close();

  if (process.argv.includes('--json')) { console.log(JSON.stringify(out, null, 1)); return; }
  const bad = out.filter((x) => x.err || x.noNav || x.evalErr ||
    (x.wraps && x.wraps.length) || x.overlapBrand > 0 || x.overflowRight > 2 || x.docScroll > 1);
  const ham = out.filter((x) => x.hamburger).length;
  console.log('检查 %d 个组合（其中汉堡态 %d）→ 异常 %d 个\n', out.length, ham, bad.length);
  let cur = null;
  for (const x of bad) {
    const key = x.w + ' | ' + x.lg;
    if (key !== cur) { console.log('── viewport ' + x.w + '  ' + x.lg); cur = key; }
    if (x.err) { console.log('   %s  %s', x.p || '/', x.err); continue; }
    if (x.noNav) { console.log('   %s  无 .nav-links', x.p || '/'); continue; }
    const f = [];
    if (x.wraps && x.wraps.length) f.push('换行[' + x.wraps.join(' ') + ']');
    if (x.overlapBrand > 0) f.push('压logo ' + x.overlapBrand + 'px');
    if (x.overflowRight > 2) f.push('越右缘 ' + x.overflowRight + 'px');
    if (x.docScroll > 1) f.push('横滚 ' + x.docScroll + 'px');
    console.log('   %-20s %s', x.p || '/', f.join(' · '));
  }
})();
