// 提案预览页尺寸探针：实测表格/卡片/缩略图的实际像素，不靠目测
// 用法：node probe_proposal_20261001.cjs <url>
const { chromium } = require('playwright');

const probe = async (page) => page.evaluate(() => {
  const r = (el) => {
    if (!el) return null;
    const b = el.getBoundingClientRect();
    return { w: Math.round(b.width), h: Math.round(b.height), x: Math.round(b.left) };
  };
  const wrap = document.querySelector('.pv-spec') ? document.querySelector('.pv-spec-wrap') : null;
  const table = document.querySelector('.pv-spec');
  const firstThumb = document.querySelector('.pv-spec .pv-model img');
  const cards = document.querySelector('.pv-cards');
  const cardEls = [...document.querySelectorAll('.pv-card')];
  // 卡片是否等宽：取第一行所有卡的宽度
  const firstTop = cardEls.length ? Math.round(cardEls[0].getBoundingClientRect().top) : 0;
  const firstRow = cardEls.filter((c) => Math.abs(c.getBoundingClientRect().top - firstTop) < 4);
  const cardImgs = [...document.querySelectorAll('.pv-card .pv-shot img')];
  const broken = cardImgs.filter((i) => !i.complete || i.naturalWidth === 0).length;
  return {
    viewport: { w: window.innerWidth, h: window.innerHeight },
    docScrollW: document.documentElement.scrollWidth,
    overflowX: document.documentElement.scrollWidth - window.innerWidth,
    wrap: r(wrap),
    table: r(table),
    thumb: r(firstThumb),
    cards: r(cards),
    perRow: firstRow.length,
    cardW: firstRow.length ? Math.round(firstRow[0].getBoundingClientRect().width) : null,
    cardImgBroken: broken,
    cardImgSizes: cardImgs.map((i) => `${i.naturalWidth}x${i.naturalHeight}`),
  };
});

(async () => {
  const url = process.argv[2];
  const browser = await chromium.launch();
  for (const [name, width, height] of [['desktop', 1280, 900], ['mobile', 390, 844]]) {
    const page = await browser.newPage({ viewport: { width, height } });
    const errs = [];
    page.on('response', (r) => {
      if (r.status() >= 400 && r.url().startsWith('http://127.0.0.1')) errs.push(`${r.status()} ${r.url()}`);
    });
    await page.goto(url, { waitUntil: 'networkidle' });
    // 强制加载全部懒加载图，避免 naturalWidth=0 假阴性
    await page.evaluate(async () => {
      document.querySelectorAll('img[loading="lazy"]').forEach((i) => { i.loading = 'eager'; });
      window.scrollTo(0, document.body.scrollHeight);
    });
    await page.waitForTimeout(1200);
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(300);
    const out = await probe(page);
    console.log(`\n===== ${name} ${width}x${height} =====`);
    console.log(JSON.stringify(out, null, 1));
    if (errs.length) console.log('HTTP 错误:', errs.join(' | '));
    await page.close();
  }
  await browser.close();
})();
