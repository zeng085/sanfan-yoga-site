// 导航下拉交互验收（真实鼠标轨迹，不是"改完看着像好了"）
//
// 覆盖三个用户反馈的现场：
//   A 缓慢下移穿过「触发项 ↔ 菜单」的 12px 空隙 → 菜单必须还在（旧代码在此消失）
//   B 悬停打开 mega 面板 → 移入面板 → 面板保持；移到远处 → 400ms 内收起
//   C 键盘 focus 打开 mega → 鼠标从未进入面板 → 移开鼠标后必须收起
//     （旧代码只有 mouseleave 一条关闭路径，这条会永久卡开）
// 用法：node i18n_build/verify_nav_hover.cjs
const { chromium } = require('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:8848';
// 用户原话是「除中英文以外，其它的导航会溢出」—— 所以 7 种语言一个都不能少，
// 只测 en/de/ja/es 会漏掉 it（1427px 需求，最长）与 es（1436px）。
const CASES = [['en', '/'], ['de', '/de/'], ['ja', '/ja/'], ['ko', '/ko/'],
               ['fr', '/fr/'], ['it', '/it/'], ['es', '/es/']];

const VIS = (sel) => `(() => { const el = document.querySelector('${sel}');
  if (!el) return false; const b = el.getBoundingClientRect();
  return b.width > 0 && b.height > 0 && getComputedStyle(el).display !== 'none'; })()`;

(async () => {
  const b = await chromium.launch();
  let fail = 0;
  for (const [lang, path] of CASES) {
    const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();
    await page.goto(BASE + path, { waitUntil: 'load' });
    await page.waitForTimeout(400);

    // ---------- A：Pilates 下拉（纯 CSS hover + 桥） ----------
    const trig = page.locator('.nav-links .nav-drop > a').first();
    const tb = await trig.boundingBox();
    if (tb) {
      await page.mouse.move(tb.x + tb.width / 2, tb.y + tb.height / 2);
      await page.waitForTimeout(220);
      const openBefore = await page.evaluate(VIS('.nav-drop:hover .nav-drop-menu'));
      // 分 8 步缓慢下移，穿过空隙进入菜单
      const tgtY = tb.y + tb.height + 34;
      for (let i = 1; i <= 8; i++) {
        await page.mouse.move(tb.x + tb.width / 2, tb.y + tb.height / 2 + (tgtY - tb.y - tb.height / 2) * i / 8);
        await page.waitForTimeout(45);
      }
      await page.waitForTimeout(120);
      const openAfter = await page.evaluate(VIS('.nav-drop:hover .nav-drop-menu'));
      const ok = openBefore && openAfter;
      if (!ok) fail++;
      console.log('%s A 下拉穿越空隙：打开=%s 缓慢下移后仍在=%s  %s',
        lang, openBefore, openAfter, ok ? 'PASS' : 'FAIL ← 菜单在到达前消失');
      // 移开后应收起
      await page.mouse.move(700, 600);
      await page.waitForTimeout(200);
      const closed = !(await page.evaluate(VIS('.nav-drop:hover .nav-drop-menu')));
      if (!closed) fail++;
      console.log('%s A2 移开后收起：%s', lang, closed ? 'PASS' : 'FAIL');
    }

    // ---------- B：mega 面板 ----------
    const prod = page.locator('.nav-links a[href$="products.html"]').first();
    const pb = await prod.boundingBox();
    if (pb) {
      await page.mouse.move(pb.x + pb.width / 2, pb.y + pb.height / 2);
      await page.waitForTimeout(700);
      const openB = await page.evaluate(VIS('.mm-wrap:not([hidden]) .mm-panel'));
      // 移入面板中部
      const mp = await page.locator('.mm-panel').first().boundingBox().catch(() => null);
      if (mp) { await page.mouse.move(mp.x + mp.width / 2, mp.y + 60); await page.waitForTimeout(250); }
      const keptB = await page.evaluate(VIS('.mm-wrap:not([hidden]) .mm-panel'));
      // 移到面板之外的「外围」。⚠️ 不能写死坐标：非英语语言的面板高得多
      // （ja 944px / de 792px，en 仅 508px），写死 (700,700) 在 en 是外围、
      // 在 de/ja 却落在面板里 —— 会报出假失败。按实际面板矩形选点。
      const outside = await page.evaluate(() => {
        const p = document.querySelector('.mm-panel');
        const r = p.getBoundingClientRect();
        const vw = window.innerWidth, vh = window.innerHeight;
        const cand = [[vw - 8, vh - 8], [8, Math.min(vh - 8, r.bottom + 30)],
                      [Math.min(vw - 8, r.right + 24), r.top + 20], [8, r.top + 20]];
        for (const [x, y] of cand) {
          if (x > r.left && x < r.right && y > r.top && y < r.bottom) continue;
          if (y <= 0 || y >= vh || x <= 0 || x >= vw) continue;
          return { x, y };
        }
        return { x: vw - 8, y: vh - 8 };
      });
      await page.mouse.move(outside.x, outside.y);
      await page.waitForTimeout(600);
      const closedB = !(await page.evaluate(VIS('.mm-wrap:not([hidden]) .mm-panel')));
      const ok = openB && keptB && closedB;
      if (!ok) fail++;
      console.log('%s B mega：悬停打开=%s 移入面板保持=%s 移到外围(%d,%d)收起=%s  %s',
        lang, openB, keptB, Math.round(outside.x), Math.round(outside.y), closedB, ok ? 'PASS' : 'FAIL');
    }

    // ---------- C：focus 打开后，鼠标从未进入面板 ----------
    // 旧代码只有 prodLink / mega 各自的 mouseleave 关闭路径：从没进过面板，
    // 就没有 mouseleave，菜单永久卡开。这里模拟「键盘/点击打开 → 鼠标在页面别处」。
    await page.evaluate(() => { const w = document.querySelector('.mm-wrap'); if (w) w.hidden = true; });
    await page.mouse.move(12, 12);
    await page.evaluate(() => document.querySelector('.nav-links a[href$="products.html"]').focus());
    await page.waitForTimeout(600);
    const openC = await page.evaluate(VIS('.mm-wrap:not([hidden]) .mm-panel'));
    // 鼠标移到页面别处（真实移动；先确认落点不在面板里）
    const awayPt = await page.evaluate(() => {
      const p = document.querySelector('.mm-panel');
      const r = p ? p.getBoundingClientRect() : null;
      const vw = window.innerWidth, vh = window.innerHeight;
      const cand = [[vw - 8, vh - 8], [8, vh - 8], [vw - 8, 12], [8, 12]];
      for (const [x, y] of cand) {
        if (r && x > r.left && x < r.right && y > r.top && y < r.bottom) continue;
        return { x, y };
      }
      return { x: vw - 8, y: vh - 8 };
    });
    await page.mouse.move(awayPt.x, awayPt.y);
    await page.waitForTimeout(550);
    const closedC = !(await page.evaluate(VIS('.mm-wrap:not([hidden]) .mm-panel')));
    const okC = openC && closedC;
    if (!okC) fail++;
    console.log('%s C focus 打开=%s → 鼠标移到页面别处后收起=%s  %s',
      lang, openC, closedC, okC ? 'PASS' : 'FAIL ← 会永久卡开');

    // ---------- D：Esc 关闭 ----------
    await page.locator('.nav-links a[href$="products.html"]').first().hover();
    await page.waitForTimeout(600);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(200);
    const closedD = !(await page.evaluate(VIS('.mm-wrap:not([hidden]) .mm-panel')));
    if (!closedD) fail++;
    console.log('%s D Esc 关闭：%s', lang, closedD ? 'PASS' : 'FAIL');

    await ctx.close();
  }

  // ---------- E：汉堡态（≤1279px）导航可用性 ----------
  for (const [lang, path] of CASES) {
    const ctx = await b.newContext({ viewport: { width: 1024, height: 900 } });
    const page = await ctx.newPage();
    await page.goto(BASE + path, { waitUntil: 'load' });
    await page.waitForTimeout(350);
    const tog = await page.evaluate(VIS('.menu-toggle'));
    const linksHidden = !(await page.evaluate(VIS('.nav-links')));
    await page.locator('.menu-toggle').first().click().catch(() => {});
    await page.waitForTimeout(250);
    const panelOpen = await page.evaluate(VIS('.nav-links.open'));
    // 面板内的下拉（静态展开）与搜索项
    // ⚠️ 必须用真实鼠标移动：`.nav-drop-menu` 靠 CSS :hover 展开，
    //    合成 MouseEvent 不会建立 hover 状态，会报「子下拉=false」的假失败。
    let dv = false;
    try {
      await page.locator('.nav-links .nav-drop > a').first().hover({ timeout: 2000 });
      await page.waitForTimeout(200);
      dv = await page.evaluate(() => {
        const m = document.querySelector('.nav-links .nav-drop-menu');
        return !!m && getComputedStyle(m).display !== 'none';
      });
    } catch (e) { dv = false; }
    const srch = await page.evaluate(VIS('.nav-search-item'));
    const noScroll = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth <= 1);
    const ok = tog && linksHidden && panelOpen && srch && noScroll;
    if (!ok) fail++;
    console.log('%s E 汉堡态(1024)：按钮=%s 面板收起=%s 点击展开=%s 子下拉=%s 搜索项=%s 无横滚=%s  %s',
      lang, tog, linksHidden, panelOpen, dv, srch, noScroll, ok ? 'PASS' : 'FAIL');
    await ctx.close();
  }

  await b.close();
  console.log('\n失败项：%d', fail);
  process.exit(fail ? 1 : 0);
})();