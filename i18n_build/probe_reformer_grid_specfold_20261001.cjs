/* 验证 20261001g：画册展开=缩略图墙 + 规格对比表默认折叠（本地 8866）
   覆盖：reformer 双视口（1440/390）交互全链路、cadillac 抽检、无 JS 降级 */
const { chromium } = require('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:8866';

(async () => {
  const browser = await chromium.launch();
  let fail = 0;
  const chk = (name, ok, extra = '') => {
    console.log(`${ok ? '✓' : '✗'} ${name}${extra ? '  ' + extra : ''}`);
    if (!ok) fail++;
  };

  for (const vw of [1440, 390]) {
    const page = await browser.newPage({ viewport: { width: vw, height: 900 } });
    await page.goto(BASE + '/pilates/pilates-reformer.html', { waitUntil: 'load' });
    await page.waitForTimeout(400);
    console.log(`\n===== reformer ${vw}px =====`);

    const init = await page.evaluate(() => {
      const cat = document.getElementById('cat-all');
      const spec = document.getElementById('spec-all');
      const bars = [...document.querySelectorAll('.cat-fold-bar')];
      return {
        total: document.documentElement.scrollHeight,
        catFolded: cat.classList.contains('is-folded') && getComputedStyle(cat).display === 'none',
        specFolded: spec.classList.contains('is-folded') && getComputedStyle(spec).display === 'none',
        barsVisible: bars.length === 2 && bars.every(b => !b.hidden),
        specAria: bars.map(b => b.querySelector('.cat-fold-toggle')).filter(Boolean)
                       .map(t => t.getAttribute('aria-expanded')).join(','),
        overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      };
    });
    chk('双折叠体默认折叠', init.catFolded && init.specFolded);
    chk('两条控制条可见', init.barsVisible);
    chk('aria-expanded=false ×2', init.specAria === 'false,false', init.specAria);
    chk('横向溢出 0', init.overflow <= 1, `overflow=${init.overflow}`);
    chk('初始整页高度适中', init.total < 9000, `${init.total}px ≈ ${(init.total / 900).toFixed(1)} 屏`);

    // 展开画册 → 缩略图墙
    await page.click('#cat-fold-toggle');
    await page.waitForTimeout(300);
    const grid = await page.evaluate(() => {
      const cat = document.getElementById('cat-all');
      const cs = getComputedStyle(cat);
      const hiddenModels = [...document.querySelectorAll('#cat-all .cat-models')]
        .filter(c => getComputedStyle(c).display === 'none').length;
      const cols = cs.gridTemplateColumns.split(' ').length;
      return {
        mode: cat.classList.contains('cat-grid-mode'),
        display: cs.display,
        cols,
        total: document.documentElement.scrollHeight,
        units: [...document.querySelectorAll('#cat-all .cat-unit')]
          .filter(u => getComputedStyle(u).display !== 'none').length,
        hiddenModels,
      };
    });
    chk('进入 cat-grid-mode', grid.mode && grid.display === 'grid');
    chk('网格列数 4/3', grid.cols === (vw === 1440 ? 4 : 3), `cols=${grid.cols}`);
    chk('27 单元全可见', grid.units === 27);
    chk('46 组型号卡容器隐藏（.cat-models display:none）', grid.hiddenModels === 27, `${grid.hiddenModels}/27`);
    const delta = grid.total - init.total;
    chk('展开增量 <2500px（原全页增量 20000+）', delta < 2500, `总高 ${grid.total}px，增量 ${delta}px`);
    chk('网格态横向溢出 0',
      await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth) <= 1);

    // 点缩略图 → 灯箱
    await page.click('#cat-p04 .cat-fig img');
    await page.waitForTimeout(250);
    const lb = await page.evaluate(() => {
      const el = document.querySelector('.lb');
      return { open: !!el && el.classList.contains('is-open'),
               src: el && el.querySelector('img').getAttribute('src') || '' };
    });
    chk('点击缩略图打开灯箱', lb.open, lb.src.split('/').pop());
    await page.keyboard.press('Escape');
    await page.waitForTimeout(200);

    // chip 跳转（网格态）
    await page.click('.cat-chip[data-jump][href="#cat-p19"]');
    await page.waitForTimeout(900);
    const chip = await page.evaluate(() => ({
      top: Math.round(document.querySelector('#cat-p19').getBoundingClientRect().top),
      hash: location.hash,
    }));
    chk('chip 网格态跳转落点 0~400', chip.top >= 0 && chip.top < 400, `top=${chip.top}px hash=${chip.hash}`);

    // 收起画册
    await page.click('#cat-fold-toggle');
    await page.waitForTimeout(200);
    chk('画册再点收起', await page.evaluate(() =>
      getComputedStyle(document.getElementById('cat-all')).display === 'none'));

    // 规格对比表：锚点自动展开（line-overview 卡 → #line-al）
    await page.click('a.line-card[href="#line-al"]');
    await page.waitForTimeout(900);
    const anchor = await page.evaluate(() => {
      const spec = document.getElementById('spec-all');
      const row = document.getElementById('line-al');
      return { expanded: !spec.classList.contains('is-folded'),
               display: getComputedStyle(spec).display,
               rowTop: Math.round(row.getBoundingClientRect().top),
               hash: location.hash };
    });
    chk('line-card 自动展开规格表', anchor.expanded && anchor.display !== 'none');
    chk('滚动后 #line-al 在视口内', anchor.rowTop >= 0 && anchor.rowTop < 400, `top=${anchor.rowTop}px hash=${anchor.hash}`);
    chk('行级落点未压在 sticky 头部下', anchor.rowTop > 60);

    // 规格表控制条开合
    await page.click('.cat-fold-bar[data-fold="spec-all"] .cat-fold-toggle');
    await page.waitForTimeout(200);
    chk('规格表可再收起', await page.evaluate(() =>
      getComputedStyle(document.getElementById('spec-all')).display === 'none'));
    await page.close();
  }

  // cadillac 抽检：仅规格表折叠
  const cad = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await cad.goto(BASE + '/pilates/pilates-cadillac.html', { waitUntil: 'load' });
  await cad.waitForTimeout(300);
  const c1 = await cad.evaluate(() => {
    const spec = document.getElementById('spec-all');
    const bar = document.querySelector('.cat-fold-bar[data-fold="spec-all"]');
    return { folded: spec.classList.contains('is-folded') && getComputedStyle(spec).display === 'none',
             bar: !!bar && !bar.hidden,
             wrap: spec.classList.contains('pl-spec-wrap') };
  });
  console.log('\n===== cadillac 抽检 =====');
  chk('规格表默认折叠', c1.folded);
  chk('控制条可见', c1.bar);
  chk('原 pl-spec-wrap 类保留（样式不丢）', c1.wrap);
  await cad.click('.cat-fold-bar[data-fold="spec-all"] .cat-fold-toggle');
  await cad.waitForTimeout(200);
  chk('展开后表格可见', await cad.evaluate(() =>
    getComputedStyle(document.getElementById('spec-all')).display !== 'none'));
  await cad.close();

  // 无 JS 降级
  const ctx = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 1440, height: 900 } });
  const nojs = await ctx.newPage();
  await nojs.goto(BASE + '/pilates/pilates-reformer.html', { waitUntil: 'load' });
  const nj = await nojs.evaluate(() => ({
    barsHidden: [...document.querySelectorAll('.cat-fold-bar')].every(b => b.hidden),
    cat: getComputedStyle(document.getElementById('cat-all')).display,
    spec: getComputedStyle(document.getElementById('spec-all')).display,
    units: document.querySelectorAll('.cat-unit').length,
    cards: document.querySelectorAll('.model-card').length,
  }));
  console.log('\n===== 无 JS 降级 =====');
  chk('控制条全 hidden', nj.barsHidden);
  chk('画册完整可见', nj.cat !== 'none');
  chk('规格表完整可见', nj.spec !== 'none');
  chk('27 单元 / 46 卡全在', nj.units === 27 && nj.cards === 46);
  await ctx.close();

  await browser.close();
  console.log(fail === 0 ? '\n✓ 全部通过' : `\n✗ ${fail} 项失败`);
  process.exit(fail === 0 ? 0 : 1);
})();
