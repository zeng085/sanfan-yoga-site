// 移动端问题定位：搜索浮层真实尺寸 + 溢出元素的祖先滚动容器
const { chromium } = require('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:8123';
const PAGES = (process.env.PAGES || 'products.html,materials.html,applications/yoga-pilates-studios.html,de/products.html').split(',');

(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
  for (const pg of PAGES) {
    const p = await ctx.newPage();
    await p.goto(BASE + '/' + pg, { waitUntil: 'load', timeout: 45000 });
    await p.waitForTimeout(600);
    console.log('\n===== /' + pg + ' =====');
    // 1) 搜索按钮可见性 + 浮层真实盒模型
    const s = await p.evaluate(() => {
      const btn = document.querySelector('.sr-btn');
      const cs = btn ? getComputedStyle(btn) : null;
      return btn ? { btnDisplay: cs.display, btnVis: cs.visibility, w: btn.getBoundingClientRect().width, h: btn.getBoundingClientRect().height } : null;
    });
    console.log('sr-btn:', JSON.stringify(s));
    try { await p.locator('.sr-btn').first().click({ timeout: 3000 }); } catch (e) { console.log('点击失败:', e.message.split('\n')[0]); }
    await p.waitForTimeout(400);
    const box = await p.evaluate(() => {
      const m = document.querySelector('.sr-modal');
      const bx = document.querySelector('.sr-box');
      if (!bx) return { err: 'no sr-box' };
      const r = bx.getBoundingClientRect();
      const mb = m ? m.getBoundingClientRect() : null;
      return {
        modalHidden: m ? m.hidden : null,
        modalBox: mb ? [Math.round(mb.x), Math.round(mb.width)] : null,
        box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        modalDisplay: m ? getComputedStyle(m).display : null,
      };
    });
    console.log('sr-box:', JSON.stringify(box));

    // 2) 溢出元素及其可滚动祖先
    const ov = await p.evaluate(() => {
      const vw = document.documentElement.clientWidth;
      const out = [];
      document.querySelectorAll('body *').forEach(el => {
        const r = el.getBoundingClientRect();
        if (r.width <= 0 || r.right <= vw + 2) return;
        if (getComputedStyle(el).position === 'fixed') return;
        // 找最近的横向可滚动祖先
        let a = el.parentElement, sc = null;
        while (a && a !== document.body) {
          const cs = getComputedStyle(a);
          if (cs.overflowX === 'auto' || cs.overflowX === 'scroll') { sc = a.tagName + '.' + (a.className || '').toString().split(' ')[0]; break; }
          a = a.parentElement;
        }
        out.push({
          el: (el.tagName + '.' + (el.className || '').toString().split(' ')[0]).slice(0, 34),
          x: Math.round(r.x), w: Math.round(r.width), right: Math.round(r.right),
          scrollParent: sc,
        });
      });
      // 去重按 el
      const seen = {};
      return out.filter(o => { if (seen[o.el]) return false; seen[o.el] = 1; return true; }).slice(0, 12);
    });
    ov.forEach(o => console.log('  溢出', o.el, 'x=' + o.x, 'w=' + o.w, 'right=' + o.right, '可滚祖先=' + (o.scrollParent || '无(被裁切!)')));
    await p.close();
  }
  await b.close();
})();
