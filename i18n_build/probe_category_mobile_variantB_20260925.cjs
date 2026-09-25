/**
 * 分类页补内容 —— 位置方案 A/B 对比实测（2026-09-25）
 *
 * A（现方案）：导语 / FAQ / 内链 三块全在产品网格之后
 * B（调整）  ：导语上移到网格之前，FAQ / 内链留在网格之后
 *
 * 关心：移动端用户要滑几屏才看到导语与 FAQ；产品网格被推到第几屏。
 * 识别按 DOM 特征，不按索引 —— 两种变体的 section 顺序不同。
 */
const { chromium } = require('playwright');

const BASE = process.env.BASE || 'file:///Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16';
const SET = [
  { n: 'yoga-props', a: '__mobtest_yoga_props_accessories.html', b: '__mobtestB_yoga_props_accessories.html', cards: 23 },
  { n: 'suede-cork', a: '__mobtest_suede_cork_yoga_mats.html', b: '__mobtestB_suede_cork_yoga_mats.html', cards: 14 },
  { n: 'foam-rollers', a: '__mobtest_foam.html', b: '__mobtestB_foam_rollers.html', cards: 12 },
  { n: 'jump-ropes', a: '__mobtest_jump_ropes.html', b: '__mobtestB_jump_ropes.html', cards: 7 },
];
const VPS = [{ w: 390, h: 844 }, { w: 320, h: 568 }, { w: 1440, h: 900 }];

const probe = () => {
  const de = document.documentElement, vh = window.innerHeight;
  const S = [...document.querySelectorAll('section')];
  const gridIdx = S.findIndex(s => s.querySelector('.prod-card'));
  const intro = gridIdx === 1 ? S[2] : S[1];
  const grid  = S[gridIdx];
  const faq   = S[gridIdx + 1];
  const ilink = S[gridIdx + 2];
  const m = (el) => {
    if (!el) return null;
    const t = el.getBoundingClientRect().top + window.scrollY;
    return { top: Math.round(t), screens: Math.round(t / vh * 10) / 10, pct: Math.round(t / de.scrollHeight * 100) };
  };
  return { docH: de.scrollHeight, vh, gridIdx, intro: m(intro), grid: m(grid), faq: m(faq), ilink: m(ilink) };
};

(async () => {
  const b = await chromium.launch();
  for (const vp of VPS) {
    console.log('\n' + '='.repeat(100));
    console.log(`视口 ${vp.w}×${vp.h}  —— 数值为「距页顶 px / 第几屏 / 文档百分比」`);
    console.log('='.repeat(100));
    console.log(`${'页面'.padEnd(14)}${'卡'.padStart(3)}  ${'方案'.padEnd(4)}${'文档高'.padStart(8)}  ${'导语'.padStart(20)}  ${'FAQ'.padStart(20)}  ${'内链'.padStart(20)}  ${'产品网格'.padStart(20)}`);
    for (const p of SET) {
      for (const [tag, file] of [['A', p.a], ['B', p.b]]) {
        const page = await b.newPage({ viewport: { width: vp.w, height: vp.h } });
        await page.goto(`${BASE}/${file}`, { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(180);
        const r = await page.evaluate(probe);
        const f = (v) => v ? `${String(v.top).padStart(5)}px ${String(v.screens).padStart(4)}屏 ${String(v.pct).padStart(3)}%`.padEnd(20) : '—'.padEnd(20);
        console.log(`${(tag === 'A' ? p.n : '').padEnd(14)}${(tag === 'A' ? p.cards : '').toString().padStart(3)}  ${tag.padEnd(4)}${String(r.docH).padStart(6)}px  ${f(r.intro)}  ${f(r.faq)}  ${f(r.ilink)}  ${f(r.grid)}`);
        await page.close();
      }
      console.log('');
    }
  }
  await b.close();
})();
