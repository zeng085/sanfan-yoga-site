// 结构类改动（A1-A5）的视觉验收 —— 改前改后各跑一次，computed style 必须一致。
// 每个目标同时探测「新选择器」与「旧选择器」：新选择器应有值且数值与改前一致；
// 旧选择器应消失（证明确实改到位、没有残留双份）。
// 用法：NODE_PATH=~/.workbuddy/binaries/node/workspace/node_modules node measure_headings_20260925.cjs
const { chromium } = require('playwright');

const BASE = 'http://127.0.0.1:8848/';
// [页面, 新选择器, 旧选择器(改前用), 改前实测值]
const TARGETS = [
  ['tpe-yoga-mats.html', '.cat-head .cat-title', '.cat-head h3',
    { tag: 'H3', fontSize: '24px', fontWeight: '700', marginTop: '0px', marginBottom: '0px', lineHeight: '39.6px', color: 'rgb(21, 32, 28)' }],
  ['faq.html', '.faq-cat', null,
    { tag: 'H3', fontSize: '20px', fontWeight: '700', marginTop: '8px', marginBottom: '12px', lineHeight: '33px', color: 'rgb(10, 77, 66)' }],
  ['blog.html', '.pc-body h2', '.pc-body h3',
    { tag: 'H3', fontSize: '18px', fontWeight: '700', marginTop: '0px', marginBottom: '0px', lineHeight: '25.2px', color: 'rgb(21, 32, 28)' }],
  ['products/ab-wheel.html', '.pd-specs h2', '.pd-specs h3',
    { tag: 'H3', fontSize: '19px', fontWeight: '700', marginTop: '0px', marginBottom: '14px', lineHeight: '31.35px', color: 'rgb(21, 32, 28)' }],
  ['de/tpe-yoga-mats.html', '.cat-head .cat-title', null, null],   // 语言版抽检
  ['index.html', '.hero h1', null, null],                          // 对照组
];

const KEYS = ['fontSize', 'fontWeight', 'marginTop', 'marginBottom', 'lineHeight', 'color'];

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
  let fails = 0;
  for (const [page, newSel, oldSel, before] of TARGETS) {
    await p.goto(BASE + page, { waitUntil: 'domcontentloaded' });
    await p.waitForTimeout(250);
    const r = await p.evaluate(([ns, os]) => {
      const pick = (sel) => {
        if (!sel) return null;
        const el = document.querySelector(sel);
        if (!el) return { missing: true };
        const cs = getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        return {
          tag: el.tagName, fontSize: cs.fontSize, fontWeight: cs.fontWeight,
          marginTop: cs.marginTop, marginBottom: cs.marginBottom,
          lineHeight: cs.lineHeight, color: cs.color,
          w: Math.round(rect.width), h: Math.round(rect.height),
        };
      };
      return { now: pick(ns), old: pick(os) };
    }, [newSel, oldSel]);

    const now = r.now;
    console.log('\n--- %s  [%s]', page, newSel);
    if (!now || now.missing) {
      console.log('   ❌ 新选择器不存在');
      fails++;
      continue;
    }
    console.log('   实际: %s %s / %s / mt %s mb %s / lh %s / %sx%s',
      now.tag, now.fontSize, now.fontWeight, now.marginTop, now.marginBottom,
      now.lineHeight, now.w, now.h);
    if (before) {
      const diff = KEYS.filter((k) => before[k] !== now[k]);
      if (diff.length) {
        console.log('   ❌ 与改前不一致: %s', diff.map((k) => k + ' ' + before[k] + '->' + now[k]).join(', '));
        fails++;
      } else {
        console.log('   ✅ 与改前完全一致（%s）', KEYS.map((k) => now[k]).join(' / '));
      }
    }
    if (oldSel) {
      console.log(r.old && r.old.missing
        ? '   ✅ 旧选择器 ' + oldSel + ' 已消失（证明确实改到位）'
        : '   ⚠️ 旧选择器 ' + oldSel + ' 仍存在！');
      if (r.old && !r.old.missing) fails++;
    }
  }
  console.log('\n===== 视觉验收：%s =====', fails === 0 ? '全部通过 ✅' : fails + ' 项异常 ❌');
  await b.close();
  process.exit(fails === 0 ? 0 : 1);
})();
