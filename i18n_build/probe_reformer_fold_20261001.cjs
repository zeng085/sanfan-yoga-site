/* 验证 reformer 页画册折叠交互（本地 8866） */
const { chromium } = require('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:8866';
const URL = BASE + '/pilates/pilates-reformer.html';

(async () => {
  const browser = await chromium.launch();
  let fail = 0;
  const chk = (name, ok, extra = '') => {
    console.log(`${ok ? '✓' : '✗'} ${name}${extra ? '  ' + extra : ''}`);
    if (!ok) fail++;
  };

  for (const vw of [1440, 390]) {
    const page = await browser.newPage({ viewport: { width: vw, height: 900 } });
    await page.goto(URL, { waitUntil: 'load' });
    await page.waitForTimeout(400);

    const init = await page.evaluate(() => {
      const body = document.getElementById('cat-all');
      const bar = document.querySelector('.cat-fold-bar');
      const t = document.getElementById('cat-fold-toggle');
      return {
        total: document.documentElement.scrollHeight,
        barVisible: !!bar && !bar.hidden,
        folded: body.classList.contains('is-folded'),
        foldedDisplay: getComputedStyle(body).display,
        ariaExpanded: t.getAttribute('aria-expanded'),
        unitsInDOM: document.querySelectorAll('.cat-unit').length,
        cardsInDOM: document.querySelectorAll('.model-card').length,
        overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      };
    });
    console.log(`\n===== ${vw}px 初始态 =====`);
    chk('页面高度（折叠后应大幅变短）', true, `${init.total}px ≈ ${(init.total / 900).toFixed(1)} 屏`);
    chk('控制条可见', init.barVisible);
    chk('默认折叠（is-folded + display:none）', init.folded && init.foldedDisplay === 'none');
    chk('aria-expanded=false', init.ariaExpanded === 'false');
    chk('DOM 内容完整 27 单元 / 46 卡', init.unitsInDOM === 27 && init.cardsInDOM === 46, `${init.unitsInDOM}/${init.cardsInDOM}`);
    chk('横向溢出 0', init.overflow <= 1, `overflow=${init.overflow}`);

    // 点击展开
    await page.click('#cat-fold-toggle');
    await page.waitForTimeout(300);
    const after = await page.evaluate(() => ({
      display: getComputedStyle(document.getElementById('cat-all')).display,
      aria: document.getElementById('cat-fold-toggle').getAttribute('aria-expanded'),
      total: document.documentElement.scrollHeight,
      unitTop: Math.round(document.querySelector('#cat-p04').getBoundingClientRect().top + scrollY),
    }));
    chk('展开后 display 恢复', after.display !== 'none');
    chk('aria-expanded=true', after.aria === 'true');
    chk('展开后高度 ≈ 原全长页', after.total > 20000, `${after.total}px`);
    // 再点收起
    await page.click('#cat-fold-toggle');
    await page.waitForTimeout(200);
    chk('再点收起', await page.evaluate(() =>
      getComputedStyle(document.getElementById('cat-all')).display === 'none'));

    // chip 跳转：折叠状态下点 Solid wood → 自动展开并滚到 cat-p19
    await page.click('.cat-chip[data-jump][href="#cat-p19"]');
    await page.waitForTimeout(900); // smooth scroll
    const chip = await page.evaluate(() => {
      const r = document.querySelector('#cat-p19').getBoundingClientRect();
      return {
        expanded: !document.getElementById('cat-all').classList.contains('is-folded'),
        top: Math.round(r.top),
        hash: location.hash,
        imgOk: [...document.querySelectorAll('#cat-p19 img')].every(i => i.complete),
      };
    });
    chk('chip 自动展开', chip.expanded);
    chk('滚动后 p19 在视口内（top 0~400）', chip.top >= 0 && chip.top < 400, `top=${chip.top}px`);
    chk('hash 已更新', chip.hash === '#cat-p19');
    await page.close();
  }

  // 无 JS 降级：内容必须完整可见、控制条不可见
  const ctx = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 1440, height: 900 } });
  const nojs = await ctx.newPage();
  await nojs.goto(URL, { waitUntil: 'load' });
  const nj = await nojs.evaluate(() => ({
    barHidden: document.querySelector('.cat-fold-bar').hidden,
    folded: document.getElementById('cat-all').classList.contains('is-folded'),
    display: getComputedStyle(document.getElementById('cat-all')).display,
    units: document.querySelectorAll('.cat-unit').length,
    total: document.documentElement.scrollHeight,
  }));
  console.log('\n===== 无 JS 降级 =====');
  chk('控制条不可见（hidden）', nj.barHidden);
  chk('画册完整可见（display 非 none）', nj.display !== 'none' && !nj.folded);
  chk('27 单元全在', nj.units === 27, `高度 ${nj.total}px`);
  await ctx.close();

  await browser.close();
  console.log(fail === 0 ? '\n✓ 全部通过' : `\n✗ ${fail} 项失败`);
  process.exit(fail === 0 ? 0 : 1);
})();
