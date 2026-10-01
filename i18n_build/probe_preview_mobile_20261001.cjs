// 实测预览页在移动视口下的表格行为：是横向滚动，还是列被隐藏/吃掉
const { chromium } = require('playwright');
const URL = process.argv[2];
const W = parseInt(process.argv[3] || '390', 10);

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: W, height: 900 } });
  await p.goto(URL, { waitUntil: 'load' });
  await p.waitForTimeout(400);

  const r = await p.evaluate(() => {
    const out = { doc: { sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }, tables: [] };
    document.querySelectorAll('table').forEach((t, i) => {
      const wrap = t.closest('.pl-spec-wrap');
      const cs = getComputedStyle(t);
      out.tables.push({
        i,
        cls: t.className,
        tableW: +t.getBoundingClientRect().width.toFixed(1),
        tableSW: t.scrollWidth,
        wrapW: wrap ? +wrap.getBoundingClientRect().width.toFixed(1) : null,
        wrapSW: wrap ? wrap.scrollWidth : null,
        wrapOverflowX: wrap ? getComputedStyle(wrap).overflowX : null,
        display: cs.display,
        heads: [...t.querySelectorAll('thead th')].map((th) => ({
          txt: th.textContent.trim(),
          w: +th.getBoundingClientRect().width.toFixed(1),
          vis: getComputedStyle(th).display !== 'none' && th.getBoundingClientRect().width > 0,
          pos: getComputedStyle(th).position,
          left: +th.getBoundingClientRect().left.toFixed(1),
        })),
        firstRow: [...(t.querySelectorAll('tbody tr')[0]?.querySelectorAll('td') || [])].map((td) => ({
          txt: td.textContent.trim().slice(0, 22),
          w: +td.getBoundingClientRect().width.toFixed(1),
          left: +td.getBoundingClientRect().left.toFixed(1),
        })),
      });
    });
    // 找出所有超出视口右边缘的元素
    const over = [];
    document.querySelectorAll('body *').forEach((el) => {
      const rc = el.getBoundingClientRect();
      if (rc.width === 0 || rc.height === 0) return;
      if (rc.right > document.documentElement.clientWidth + 1) {
        const par = el.parentElement;
        if (par && par.scrollWidth > par.clientWidth) return; // 在可滚动容器内，合法
        over.push({ tag: el.tagName.toLowerCase(), cls: (el.className || '').toString().slice(0, 40), right: +rc.right.toFixed(1) });
      }
    });
    out.overflow = over.slice(0, 15);
    return out;
  });

  console.log('viewport width =', W);
  console.log('doc scrollWidth', r.doc.sw, 'clientWidth', r.doc.cw, r.doc.sw > r.doc.cw ? '<<< 横向溢出' : '(无溢出)');
  r.tables.forEach((t) => {
    console.log(`\n--- table[${t.i}] .${t.cls} ---`);
    console.log(`  table ${t.tableW}px (scrollWidth ${t.tableSW})  wrap ${t.wrapW}px (scrollWidth ${t.wrapSW}, overflowX=${t.wrapOverflowX})`);
    console.log('  表头:');
    t.heads.forEach((h) => console.log(`    ${h.vis ? '可见' : '不可见'} w=${String(h.w).padStart(6)} left=${String(h.left).padStart(6)} pos=${h.pos}  "${h.txt}"`));
    console.log('  首行:', t.firstRow.map((c) => `${c.txt}@${c.left}`).join(' | '));
  });
  console.log('\n视口外元素:', r.overflow.length);
  r.overflow.forEach((o) => console.log('  ', o.tag, '.' + o.cls, 'right=' + o.right));
  await b.close();
})();
