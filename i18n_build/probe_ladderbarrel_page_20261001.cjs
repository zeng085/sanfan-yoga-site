// 对真实站点页做浏览器级验收：静态读 HTML 看不出渲染层缺陷（项目铁律 5）
// 覆盖：表格/卡片数值、画册区块顺序与图是否真加载、横向溢出、JSON-LD 可解析、锚点悬空
const { chromium } = require('playwright');

(async () => {
  const url = process.argv[2];
  const want = {
    table: ['ladder-barre-3', 'ladder-barre-19-f', 'ladder-barre-1-a', 'ladder-barre-2-a',
            'ladder-barre-4-t', 'ladder-barre-21-fo', 'ladder-barre-20-v5'],
    figPages: ['32', '34', '35'],
    figSrcs: ['p33.webp', 'p35.webp', 'p36.webp'],
    metal221: '1190×700×1170 mm',
  };
  let fail = 0;
  const bad = (m) => { console.log('   ✗ ' + m); fail++; };
  const ok = (m) => console.log('   ✓ ' + m);

  const b = await chromium.launch();
  for (const W of [1280, 390]) {
    const p = await b.newPage({ viewport: { width: W, height: 900 } });
    const errs = [];
    p.on('pageerror', e => errs.push('pageerror: ' + e.message));
    p.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()); });
    const resp = await p.goto(url, { waitUntil: 'load' });
    console.log(`\n═══ 视口 ${W}px（HTTP ${resp.status()}）═══`);

    // lazy 图必须先逐屏预热，否则 naturalWidth=0 是假阴性。
    // ⚠️ 用 documentElement.scrollHeight（body.scrollHeight 在长页面下偏小，
    //    会漏掉页尾最后一张图 —— 本轮在 390px 实测踩到）
    await p.evaluate(async () => {
      const step = 500;
      for (let y = 0; y < document.documentElement.scrollHeight; y += step) {
        window.scrollTo(0, y);
        await new Promise(r => setTimeout(r, 55));
      }
      window.scrollTo(0, document.documentElement.scrollHeight);  // 确保触底
      await new Promise(r => setTimeout(r, 400));
      window.scrollTo(0, 0);
    });
    await p.waitForFunction(
      () => [...document.images].every(i => i.complete), null, { timeout: 15000 }
    ).catch(() => {});
    await p.waitForTimeout(700);

    const d = await p.evaluate(() => {
      const rows = [...document.querySelectorAll('table.pl-spec tbody tr')];
      const ids = new Set([...document.querySelectorAll('[id]')].map(e => e.id));
      return {
        tableSlug: rows.map(r => (r.querySelector('td.model a')?.getAttribute('href') || '').slice(1)),
        tableCells: rows.map(r => [...r.querySelectorAll('td')].map(c => c.textContent.trim())),
        cards: [...document.querySelectorAll('article.model-card')].map(a => ({
          id: a.id,
          sub: a.querySelector('.model-card-sub .lang-en')?.textContent.trim(),
          dd: [...a.querySelectorAll('dd')].map(x => x.textContent.trim()),
        })),
        blocks: [...document.querySelectorAll('.cat-unit')].map(x => {
          const img = x.querySelector('img');
          return {
            id: x.id,
            src: (img?.getAttribute('src') || '').split('/').pop(),
            loaded: !!img && img.complete && img.naturalWidth > 0,
            nw: img?.naturalWidth || 0,
            // ⚠️ 不能「去掉所有非数字」——图注是 "2026 catalogue · page 32"，会拼成 202632
            capRaw: x.querySelector('figcaption .lang-en')?.textContent.trim() || '',
            models: [...x.querySelectorAll('h3')].map(h => h.textContent.trim()),
          };
        }),
        imgBroken: [...document.images].filter(i => !(i.complete && i.naturalWidth > 0))
                                    .map(i => i.getAttribute('src')),
        imgTotal: document.images.length,
        overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        ld: [...document.querySelectorAll('script[type="application/ld+json"]')]
              .map(s => { try { JSON.parse(s.textContent); return 'OK'; } catch (e) { return 'ERR'; } }),
        dangling: [...document.querySelectorAll('a[href^="#"]')]
              .map(a => a.getAttribute('href').slice(1)).filter(h => h && !ids.has(h)),
      };
    });

    // 1) 表格顺序与数值
    if (JSON.stringify(d.tableSlug) === JSON.stringify(want.table)) ok(`表格 ${d.tableSlug.length} 行、顺序与数据源一致`);
    else bad(`表格顺序不符：${d.tableSlug}`);

    const rows = d.tableCells;
    const get = (slug) => rows[d.tableSlug.indexOf(slug)];
    const two = ['ladder-barre-21-fo', 'ladder-barre-20-v5'];
    for (const s of two) {
      const c = get(s);
      if (!c) { bad(`表格缺 ${s}`); continue; }
      if (c[2] === want.metal221) ok(`表格 ${c[0]} 包装尺寸 = ${c[2]}（原为稳踏椅的 920×720×790）`);
      else bad(`表格 ${c[0]} 包装尺寸 = ${c[2]}，期望 ${want.metal221}`);
      if (c[4] === '85 kg') ok(`表格 ${c[0]} 毛重 ${c[4]}`);
      else bad(`表格 ${c[0]} 毛重 ${c[4]}`);
    }

    // 2) 卡片与表格同序
    const cardIds = d.cards.map(c => c.id);
    if (JSON.stringify(cardIds) === JSON.stringify(want.table)) ok(`卡片 ${cardIds.length} 张、与表格同序（表↔卡不再错位）`);
    else bad(`卡片顺序 ${cardIds}`);

    for (const c of d.cards.filter(c => c.id.includes('21-fo') || c.id.includes('20-v5'))) {
      if (c.dd[1] === '1190 × 700 × 1170 mm') ok(`卡片 ${c.id} 包装尺寸 ${c.dd[1]}`);
      else bad(`卡片 ${c.id} 包装尺寸 ${c.dd[1]}`);
      // 页面用的是 "Catalogue p35 · model 1 of 2"（不是 "page 35"）
      if (/p35\b/.test(c.sub || '')) ok(`卡片 ${c.id} 副标题 = ${c.sub}`);
      else bad(`卡片 ${c.id} 副标题 = ${c.sub}（应指向画册第 35 页）`);
    }

    // 3) 画册区块顺序 + 图
    const pages = d.blocks.map(b => (b.capRaw.match(/page\s+(\d+)/) || [])[1]);
    if (JSON.stringify(pages) === JSON.stringify(want.figPages)) ok(`画册区块页序 ${pages.join(' → ')}（升序，不再倒挂）`);
    else bad(`画册区块页序 ${pages}（原始图注：${d.blocks.map(b => b.capRaw).join(' | ')}）`);
    const srcs = d.blocks.map(b => b.src);
    if (JSON.stringify(srcs) === JSON.stringify(want.figSrcs)) ok(`画册用图 ${srcs.join(' / ')}`);
    else bad(`画册用图 ${srcs}`);
    for (const b of d.blocks) {
      if (b.loaded && b.nw > 1000) ok(`区块 ${b.id} 图已加载 ${b.src} (${b.nw}px)`);
      else bad(`区块 ${b.id} 图未加载 ${b.src} (naturalWidth=${b.nw})`);
    }
    const lastBlock = d.blocks[d.blocks.length - 1];
    if (lastBlock.models.join('|') === 'Ladder Barre 21-FO|Ladder Barre 20-V5')
      ok(`21-FO / 20-V5 卡片与 p36 画页同块：${lastBlock.models.join(' + ')}`);
    else bad(`末块卡片 ${lastBlock.models}`);

    // 4) 图片全加载 / 溢出 / JSON-LD / 锚点
    if (d.imgBroken.length === 0) ok(`全页 ${d.imgTotal} 张图 0 破图`);
    else bad(`破图 ${d.imgBroken.join(', ')}`);
    if (d.overflow <= 0) ok(`无横向溢出（scrollWidth == clientWidth）`);
    else bad(`横向溢出 ${d.overflow}px`);
    if (d.ld.every(x => x === 'OK')) ok(`JSON-LD ${d.ld.length} 块全部可解析`);
    else bad(`JSON-LD 解析失败：${d.ld}`);
    if (d.dangling.length === 0) ok(`锚点无悬空`);
    else bad(`悬空锚点 ${d.dangling.join(', ')}`);

    // 5) 真实网络错误（过滤第三方 GA 离线）
    const real = errs.filter(e => !/googletagmanager|google-analytics|gstatic|doubleclick/i.test(e));
    if (real.length === 0) ok(`无本域 console/page 错误`);
    else bad(`错误 ${real.slice(0, 3).join(' | ')}`);

    await p.close();
  }
  await b.close();
  console.log(fail === 0 ? '\n✅ 全部通过' : `\n❌ ${fail} 项未通过`);
  process.exit(fail === 0 ? 0 : 1);
})();
