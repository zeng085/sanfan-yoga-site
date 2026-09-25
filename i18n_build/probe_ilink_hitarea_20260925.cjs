/**
 * 内链点击热区 —— 真实命中区间探测（2026-09-25）
 *
 * 为什么要这样测：
 *   inline 元素 getBoundingClientRect().height = 18px（content area），
 *   但浏览器对 inline 的**点击命中判定**用的是行框范围，不是 content area。
 *   两者可能差一倍以上 —— 所以必须用 elementFromPoint 逐点扫出真实可点区间。
 *
 * 扫法：以 <a> 的水平中心为 x，从 rect.top-14 到 rect.bottom+14 每 1px 取
 *       elementFromPoint，统计返回自身/后代的连续像素高度 = 真实热区。
 *       但这样测的是「该 x 处最上层元素」，需要同时确认 a 是命中者本身。
 *
 * 三种形态对比：
 *   current        现状（ul 上 line-height:2，a 是 inline 无纵向 padding）
 *   fix-lh         修法1：把 line-height 挪到 a 上（视觉零变化）
 *   fix-block      修法2：a 改 inline-block + padding:6px 0（Apple HIG 44px）
 */
const { chromium } = require('playwright');

const BASE = process.env.BASE || 'file:///Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16';
const PAGES = ['__mobtest_foam.html', '__mobtest_yoga_props_accessories.html'];

const scan = () => {
  const sec = [...document.querySelectorAll('section')].find(s => s.querySelector('li a') && !s.querySelector('.faq-list'));
  if (!sec) return null;
  const a = sec.querySelector('li a');
  const r = a.getBoundingClientRect();
  const cx = r.left + r.width / 2;
  let hit = 0, top = null, bot = null;
  for (let dy = -34; dy <= 34; dy++) {
    const y = r.top + r.height / 2 + dy;
    if (y < 2 || y > window.innerHeight - 2) continue;
    const el = document.elementFromPoint(cx, y);
    const isHit = el === a || a.contains(el);
    if (isHit) { hit++; if (top === null || dy < top) top = dy; if (bot === null || dy > bot) bot = dy; }
  }
  const cs = getComputedStyle(a);
  const probeY = r.top + r.height / 2;
  const who = (probeY >= 2 && probeY <= window.innerHeight - 2) ? document.elementFromPoint(cx, probeY) : null;
  const ul = a.closest('ul');
  const ulH = ul ? Math.round(ul.getBoundingClientRect().height) : null;
  const liH = Math.round(a.closest('li').getBoundingClientRect().height);
  return {
    ulH, liH,
    rectTopInVp: Math.round(r.top),
    atCenter: who ? (who.tagName + (who.className ? '.' + String(who.className).slice(0, 16) : '')) : 'OUT',
    rectH: Math.round(r.height * 10) / 10,
    hitH: hit,
    hitTop: top, hitBot: bot,
    display: cs.display, aLh: cs.lineHeight, aPad: cs.paddingTop + '/' + cs.paddingBottom,
  };
};

const FIXES = [
  { tag: 'current', css: '' },
  { tag: 'fix-lh', css: '.ilinksec ul li a{line-height:2}' },
  { tag: 'fix-block', css: '.ilinksec ul li a{display:inline-block;padding:6px 0}' },
];

(async () => {
  const b = await chromium.launch();
  for (const vp of [{ w: 390, h: 844 }, { w: 320, h: 568 }]) {
    console.log('\n' + '='.repeat(88));
    console.log(`视口 ${vp.w}×${vp.h}`);
    console.log('='.repeat(88));
    for (const f of PAGES) {
      console.log(`\n${f}`);
      for (const fx of FIXES) {
        const page = await b.newPage({ viewport: { width: vp.w, height: vp.h } });
        await page.goto(`${BASE}/${f}`, { waitUntil: 'domcontentloaded' });
        await page.evaluate(() => {
          const s = [...document.querySelectorAll('section')].find(x => x.querySelector('li a') && !x.querySelector('.faq-list'));
          if (s) s.classList.add('ilinksec');
        });
        if (fx.css) await page.addStyleTag({ content: fx.css });
        await page.addStyleTag({ content: 'html{scroll-behavior:auto !important}' });
        await page.waitForTimeout(120);
        await page.evaluate(() => {
          const s = [...document.querySelectorAll('section')].find(x => x.querySelector('li a') && !x.querySelector('.faq-list'));
          const a = s && s.querySelector('li a');
          if (a) window.scrollTo(0, a.getBoundingClientRect().top + window.scrollY - window.innerHeight / 2);
        });
        await page.waitForTimeout(220);
        const r = await page.evaluate(scan);
        const over = await page.evaluate(() => Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) - document.documentElement.clientWidth);
        if (r) {
          console.log(`   ${fx.tag.padEnd(10)} rect高 ${String(r.rectH).padStart(5)}px | 真实可点区间 ${String(r.hitH).padStart(3)}px (上探${r.hitTop} 下探${r.hitBot}) | display=${r.display.padEnd(12)} a纵padding=${r.aPad.padEnd(9)} | 横向溢出=${over}${over > 1 ? ' <<<' : ''}  [li高=${r.liH} ul高=${r.ulH}]`);
        }
        await page.close();
      }
    }
  }
  await b.close();
})();
