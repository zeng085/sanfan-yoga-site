/* 验证 20261001h：画册缩略图墙默认显示（按钮=收起/再展开），规格对比表仍默认折叠
   覆盖：reformer 双视口（1440/390）交互全链路、cadillac 抽检、无 JS 降级 */
const { chromium } = require('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:8866';
const CAT_LABEL_EN = 'Browse the catalogue \u2014 27 pages, 46 models';

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
      const labels = bars.map(b => {
        const en = b.querySelector('.lang-en');
        return en ? en.textContent : '';
      });
      return {
        total: document.documentElement.scrollHeight,
        catGrid: cat.classList.contains('cat-grid-mode') && getComputedStyle(cat).display === 'grid',
        specFolded: spec.classList.contains('is-folded') && getComputedStyle(spec).display === 'none',
        aria: bars.map(b => b.querySelector('.cat-fold-toggle')).map(t => t.getAttribute('aria-expanded')).join(','),
        labels,
        overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      };
    });
    chk('画册墙默认显示（grid 模式）', init.catGrid);
    chk('规格对比表默认折叠', init.specFolded);
    chk('aria-expanded=true,false', init.aria === 'true,false', init.aria);
    chk('画册按钮显示「Collapse」', init.labels[0] === 'Collapse', init.labels[0]);
    chk('规格按钮显示原文案', /Show the full spec table/.test(init.labels[1]), init.labels[1]);
    chk('横向溢出 0', init.overflow <= 1, `overflow=${init.overflow}`);
    chk('整页高度适中', init.total < 11000, `${init.total}px ≈ ${(init.total / 900).toFixed(1)} 屏`);

    const grid = await page.evaluate(() => {
      const cat = document.getElementById('cat-all');
      const cs = getComputedStyle(cat);
      return {
        cols: cs.gridTemplateColumns.split(' ').length,
        units: [...document.querySelectorAll('#cat-all .cat-unit')]
          .filter(u => getComputedStyle(u).display !== 'none').length,
        hiddenModels: [...document.querySelectorAll('#cat-all .cat-models')]
          .filter(c => getComputedStyle(c).display === 'none').length,
      };
    });
    chk('网格列数 4/3', grid.cols === (vw === 1440 ? 4 : 3), `cols=${grid.cols}`);
    chk('27 单元全可见', grid.units === 27);
    chk('27 组型号卡容器隐藏', grid.hiddenModels === 27, `${grid.hiddenModels}/27`);

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

    // chip 跳转（墙默认展开态）
    await page.click('.cat-chip[data-jump][href="#cat-p19"]');
    await page.waitForTimeout(900);
    const chip = await page.evaluate(() => ({
      top: Math.round(document.querySelector('#cat-p19').getBoundingClientRect().top),
      hash: location.hash,
    }));
    chk('chip 跳转落点 0~400', chip.top >= 0 && chip.top < 400, `top=${chip.top}px hash=${chip.hash}`);

    // 收起画册 → 再展开
    await page.click('#cat-fold-toggle');
    await page.waitForTimeout(200);
    const folded = await page.evaluate(() => ({
      display: getComputedStyle(document.getElementById('cat-all')).display,
      label: document.querySelector('#cat-fold-toggle .lang-en').textContent,
      aria: document.getElementById('cat-fold-toggle').getAttribute('aria-expanded'),
    }));
    chk('点击收起画册', folded.display === 'none');
    chk('收起后按钮恢复原文案', folded.label === CAT_LABEL_EN, folded.label);
    chk('aria-expanded=false', folded.aria === 'false');
    await page.click('#cat-fold-toggle');
    await page.waitForTimeout(300);
    const re = await page.evaluate(() => ({
      grid: document.getElementById('cat-all').classList.contains('cat-grid-mode'),
      display: getComputedStyle(document.getElementById('cat-all')).display,
      label: document.querySelector('#cat-fold-toggle .lang-en').textContent,
    }));
    chk('再点恢复缩略图墙', re.grid && re.display === 'grid');
    chk('按钮回到「Collapse」', re.label === 'Collapse', re.label);

    // 规格对比表：锚点自动展开（line-overview 卡 → #line-al）
    await page.click('a.line-card[href="#line-al"]');
    await page.waitForTimeout(900);
    const anchor = await page.evaluate(() => {
      const spec = document.getElementById('spec-all');
      const row = document.getElementById('line-al');
      return { expanded: !spec.classList.contains('is-folded'),
               rowTop: Math.round(row.getBoundingClientRect().top),
               hash: location.hash };
    });
    chk('line-card 自动展开规格表', anchor.expanded);
    chk('滚动后 #line-al 在视口内', anchor.rowTop >= 0 && anchor.rowTop < 400, `top=${anchor.rowTop}px hash=${anchor.hash}`);

    // 规格表控制条开合 + 文案
    await page.click('.cat-fold-bar[data-fold="spec-all"] .cat-fold-toggle');
    await page.waitForTimeout(200);
    chk('规格表可再收起', await page.evaluate(() =>
      getComputedStyle(document.getElementById('spec-all')).display === 'none'));
    await page.close();
  }

  // cadillac 抽检：仅规格表折叠（无画册墙，行为应与之前一致）
  const cad = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await cad.goto(BASE + '/pilates/pilates-cadillac.html', { waitUntil: 'load' });
  await cad.waitForTimeout(300);
  const c1 = await cad.evaluate(() => ({
    folded: getComputedStyle(document.getElementById('spec-all')).display === 'none',
    label: document.querySelector('.cat-fold-bar[data-fold="spec-all"] .lang-en').textContent,
  }));
  console.log('\n===== cadillac 抽检 =====');
  chk('规格表默认折叠', c1.folded);
  chk('按钮显示原文案', /Show the full spec table/.test(c1.label), c1.label);
  await cad.click('.cat-fold-bar[data-fold="spec-all"] .cat-fold-toggle');
  await cad.waitForTimeout(200);
  const c2 = await cad.evaluate(() => ({
    open: getComputedStyle(document.getElementById('spec-all')).display !== 'none',
    label: document.querySelector('.cat-fold-bar[data-fold="spec-all"] .lang-en').textContent,
  }));
  chk('展开后表格可见 + 按钮变「Collapse」', c2.open && c2.label === 'Collapse', c2.label);
  await cad.close();

  // 无 JS 降级：内容完整可见、控制条不可见
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
