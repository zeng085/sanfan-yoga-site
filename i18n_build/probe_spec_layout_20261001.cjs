// 诊断：桌面规格表留白 + 移动端型号卡长度
const { chromium } = require('playwright');

(async () => {
  const base = process.env.BASE || 'http://127.0.0.1:8866';
  const browser = await chromium.launch();

  // ---- A. 桌面 1080 / 1440：规格表 vs 容器宽度 ----
  for (const vw of [1080, 1440]) {
    const page = await browser.newPage({ viewport: { width: vw, height: 900 } });
    await page.goto(base + '/pilates/pilates-cadillac.html', { waitUntil: 'load' });
    const m = await page.evaluate(() => {
      const wrap = document.querySelector('.pl-spec-wrap');
      const table = document.querySelector('table.pl-spec');
      const cs = getComputedStyle(table);
      const th = table.querySelector('thead th');
      return {
        vw: innerWidth,
        wrapW: wrap.clientWidth,
        tableW: table.getBoundingClientRect().width,
        tableScrollW: table.scrollWidth,
        tableCS: { width: cs.width, minWidth: cs.minWidth, maxWidth: cs.maxWidth, display: cs.display },
        wrapDisplay: getComputedStyle(wrap).display,
        thW: th.getBoundingClientRect().width,
        nCols: table.rows[0].cells.length,
        cssHref: [...document.styleSheets].map(s => s.href).filter(Boolean).pop(),
      };
    });
    console.log(`\n=== 桌面 ${vw}px ===`);
    console.log(JSON.stringify(m, null, 1));
    await page.close();
  }

  // ---- B. 移动 390：型号卡尺寸与结构 ----
  const mp = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await mp.goto(base + '/pilates/pilates-cadillac.html', { waitUntil: 'load' });
  const mm = await mp.evaluate(() => {
    const cards = [...document.querySelectorAll('.model-card')];
    const r = el => { const b = el.getBoundingClientRect(); return Math.round(b.height); };
    const card = cards[0];
    const dl = card.querySelector('dl');
    const btn = card.querySelector('.btn, a.btn');
    const cs = getComputedStyle(dl);
    return {
      cardH: r(card),
      cardCount: cards.length,
      dlH: r(dl),
      dlCols: cs.gridTemplateColumns,
      subH: r(card.querySelector('.model-card-sub')),
      btnH: btn ? r(btn) : null,
      docScrollH: document.documentElement.scrollHeight,
    };
  });
  console.log('\n=== 移动 390px 型号卡 ===');
  console.log(JSON.stringify(mm, null, 1));
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
