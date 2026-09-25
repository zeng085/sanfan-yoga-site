// 多语言 x 多视口的抽样验收 —— 结构类改动（A1-A5）之后跑。
// 检查四件事：新标签在渲染后的字号/字重是否与预期一致、cat-head 的 flex 容器是否完好
// （子元素在桌面态横排 = DOM 未被破坏）、页面是否出现横向溢出。
// 用法：NODE_PATH=~/.workbuddy/binaries/node/workspace/node_modules node verify_multilang_headings_20260925.cjs
const { chromium } = require('playwright');

const BASE = 'http://127.0.0.1:8848/';
// [页面, 选择器, 期望字号, 期望字重]
const CASES = [
  ['de/products/ab-wheel.html', '.pd-specs h2', '19px', '700'],
  ['ja/products/ab-wheel.html', '.pd-specs h2', '19px', '700'],
  ['ko/products/ab-wheel.html', '.pd-specs h2', '19px', '700'],
  ['fr/products/ab-wheel.html', '.pd-specs h2', '19px', '700'],
  ['it/products/ab-wheel.html', '.pd-specs h2', '19px', '700'],
  ['es/products/ab-wheel.html', '.pd-specs h2', '19px', '700'],
  ['de/faq.html', '.faq-cat', '20px', '700'],
  ['ja/faq.html', '.faq-cat', '20px', '700'],
  ['es/faq.html', '.faq-cat', '20px', '700'],
  ['de/blog.html', '.pc-body h2', '18px', '700'],
  ['ko/blog.html', '.pc-body h2', '18px', '700'],
  ['de/foam-rollers.html', '.cat-head .cat-title', '24px', '700'],
  ['ja/tpe-yoga-mats.html', '.cat-head .cat-title', '24px', '700'],
  ['it/jump-ropes.html', '.cat-head .cat-title', '24px', '700'],
  ['en tpe-yoga-mats.html', '.cat-head .cat-title', '24px', '700'],
];
const VIEWPORTS = [[1280, 900], [390, 844]];   // 桌面 + 移动

(async () => {
  const b = await chromium.launch();
  let fails = 0;
  for (const [w, h] of VIEWPORTS) {
    console.log('\n================ 视口 ' + w + 'x' + h + ' ================');
    const p = await b.newPage({ viewport: { width: w, height: h } });
    for (const [page, sel, wantSize, wantWeight] of CASES) {
      const real = page.startsWith('en ') ? page.slice(3) : page;
      await p.goto(BASE + real, { waitUntil: 'domcontentloaded' });
      await p.waitForTimeout(150);
      const r = await p.evaluate(([sel, vw]) => {
        const el = document.querySelector(sel);
        const out = { ok: !!el, vw };
        if (el) {
          const cs = getComputedStyle(el);
          out.fontSize = cs.fontSize;
          out.fontWeight = cs.fontWeight;
          out.tag = el.tagName;
        }
        const ch = document.querySelector('.cat-head');
        if (ch) {
          // 判据说明：.cat-head 是 align-items:baseline，不同字号的子元素 top 天然不同，
          // 不能用 top 判断是否横排。真正要验的是「容器还在 + flex 仍生效 + 3 个子元素都在里面」。
          const ccs = getComputedStyle(ch);
          out.catKids = ch.children.length;
          out.catDisp = ccs.display;
        }
        out.overflow = document.documentElement.scrollWidth > window.innerWidth + 1;
        return out;
      }, [sel, w]);

      const bad = [];
      if (!r.ok) bad.push('选择器缺失');
      if (r.ok && r.fontSize !== wantSize) bad.push('字号 ' + r.fontSize + '≠' + wantSize);
      if (r.ok && r.fontWeight !== wantWeight) bad.push('字重 ' + r.fontWeight + '≠' + wantWeight);
      if (r.catKids !== undefined && r.catKids !== 3) bad.push('cat-head 子元素 ' + r.catKids + ' != 3');
      if (r.catDisp && r.catDisp !== 'flex') bad.push('cat-head display=' + r.catDisp);
      if (r.overflow) bad.push('横向溢出');
      if (bad.length) fails++;
      console.log('  ' + (bad.length ? '❌' : '✅') + ' ' + real.padEnd(32) + ' ' +
        sel.padEnd(22) + ' ' + ((r.fontSize || '-') + '/' + (r.fontWeight || '-')).padEnd(12) +
        ' 子元素=' + (r.catKids === undefined ? '-' : r.catKids) +
        (bad.length ? '   ' + bad.join('; ') : ''));
    }
    await p.close();
  }
  console.log('\n===== 多语言抽样验收：' + (fails === 0 ? '全部通过 ✅' : fails + ' 项异常 ❌') + ' =====');
  await b.close();
  process.exit(fails === 0 ? 0 : 1);
})();
