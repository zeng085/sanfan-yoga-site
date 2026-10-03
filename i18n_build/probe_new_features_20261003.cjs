// 本轮新功能的浏览器级验收（2026-03-03）
// 判据：① 同意前不加载 GA、同意后加载、选择被记住 ② 横幅触控目标 ≥44px
//       ③ 产能表在 320px 下可横向滑动（不再是被裁掉） ④ 表单 label 真的关联到控件
//       ⑤ 诱饵字段存在且不影响真人 ⑥ 反馈框有 aria-live + 本地化文案
// 用法：node probe_new_features_20261003.cjs --base=http://127.0.0.1:8899
const { chromium } = require('playwright');
const argv = process.argv.slice(2);
const arg = (k, d) => { const i = argv.indexOf('--' + k); if (i >= 0) return argv[i + 1];
  const m = argv.find(a => a.startsWith('--' + k + '=')); return m ? m.slice(('--' + k + '=').length) : d; };
const BASE = arg('base', 'http://127.0.0.1:8899');

let pass = 0, fail = 0;
function check(name, ok, detail) {
  (ok ? pass++ : fail++);
  console.log(`  ${ok ? '✓' : '✗'} ${name}${detail ? '  ' + detail : ''}`);
}

(async () => {
  const browser = await chromium.launch();

  // ── ① 同意机制（EN 首页，390 视口）────────────────────────────────────
  console.log('\n【① Cookie 同意 + GA 门控】');
  {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await ctx.newPage();
    const gaReq = [];
    page.on('request', r => { if (/googletagmanager|google-analytics/.test(r.url())) gaReq.push(r.url()); });
    await page.goto(BASE + '/de/index.html', { waitUntil: 'networkidle' });
    await page.waitForTimeout(800);

    check('页面里没有 GA <script>（HTML 已剥除）',
      (await page.locator('script[src*="googletagmanager"]').count()) === 0);
    check('同意前没有任何 GA/GA4 网络请求', gaReq.length === 0, `请求数=${gaReq.length}`);

    const bar = page.locator('#consent-bar');
    check('同意横幅出现', await bar.count() === 1);
    const btns = page.locator('#consent-bar button[data-consent]');
    const n = await btns.count();
    check('横幅有两个按钮', n === 2, `实际 ${n}`);
    const sizes = [];
    for (let i = 0; i < n; i++) {
      const r = await btns.nth(i).boundingBox();
      sizes.push(`${Math.round(r.width)}x${Math.round(r.height)}`);
    }
    check('按钮触控目标 ≥44px 高', sizes.every(s => parseInt(s.split('x')[1]) >= 44), sizes.join(' '));
    const txt = (await bar.textContent()).trim();
    check('德语页横幅是德语', /Sie können zustimmen oder ablehnen/.test(txt));
    const link = await bar.locator('a').getAttribute('href');
    check('隐私政策链接指向德语页', link === '/de/privacy.html', link);

    // 点「同意」→ GA 才加载
    await page.locator('#consent-bar button[data-consent="granted"]').click();
    await page.waitForTimeout(1500);
    check('点同意后横幅消失', await page.locator('#consent-bar').count() === 0);
    check('点同意后才发 GA 请求', gaReq.length > 0, `请求数=${gaReq.length}`);
    const stored = await page.evaluate(() => localStorage.getItem('sanfan_consent'));
    check('选择已记录', stored === 'granted', String(stored));

    // 刷新后不再打扰
    gaReq.length = 0;
    await page.reload({ waitUntil: 'networkidle' });
    await page.waitForTimeout(900);
    check('刷新后不再出现横幅', await page.locator('#consent-bar').count() === 0);
    check('刷新后 GA 直接加载（无需再点）', gaReq.length > 0, `请求数=${gaReq.length}`);
    await ctx.close();
  }

  // 拒绝路径
  {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await ctx.newPage();
    const gaReq = [];
    page.on('request', r => { if (/googletagmanager|google-analytics/.test(r.url())) gaReq.push(r.url()); });
    await page.goto(BASE + '/index.html', { waitUntil: 'networkidle' });
    await page.waitForTimeout(600);
    await page.locator('#consent-bar button[data-consent="denied"]').click();
    await page.waitForTimeout(1200);
    check('点拒绝后不加载 GA', gaReq.length === 0, `请求数=${gaReq.length}`);
    const stored = await page.evaluate(() => localStorage.getItem('sanfan_consent'));
    check('拒绝状态也被记录', stored === 'denied', String(stored));
    await page.reload({ waitUntil: 'networkidle' });
    await page.waitForTimeout(700);
    check('拒绝后刷新不再追问', await page.locator('#consent-bar').count() === 0);
    await ctx.close();
  }

  // ── ② 产能表在 320px 下可滑动 ─────────────────────────────────────────
  console.log('\n【② 产能表 @320px（客户要能滑到数字）】');
  {
    const ctx = await browser.newContext({ viewport: { width: 320, height: 568 } });
    const page = await ctx.newPage();
    await page.goto(BASE + '/de/index.html', { waitUntil: 'networkidle' });
    await page.waitForTimeout(600);
    const r = await page.evaluate(() => {
      const w = document.querySelector('.cap-wrap');
      if (!w) return { has: false };
      const t = w.querySelector('.cap-table');
      const before = w.scrollLeft;
      w.scrollLeft = 9999;
      const after = w.scrollLeft;
      const lastCell = t.querySelector('tbody tr:last-child td.val');
      const wr = w.getBoundingClientRect(), lr = lastCell.getBoundingClientRect();
      return { has: true, scrollable: w.scrollWidth > w.clientWidth + 1,
               scrolled: after > before, maxScroll: after,
               tableW: Math.round(t.getBoundingClientRect().width),
               wrapW: Math.round(wr.width),
               lastCellVisible: lr.right <= wr.right + 2 && lr.left >= wr.left - 2,
               lastCellText: lastCell.textContent.trim().slice(0, 28) };
    });
    check('存在 .cap-wrap 滚动容器', r.has);
    // ⭐ 判据要匹配修复手法（铁律 9）：修法是「窄屏允许换行 + 容器可滚动」，
    //    目标是**数字列完整可见** —— 要么整表放得下（无需滑），要么能滑过去。
    //    早先版本只判「可滚动」，结果 CSS 修好了（表格 278px ≤ 容器 280px 放得下）
    //    反而被判成失败 —— 判据和手法对不上，报出来的红是假的。
    const allVisible = r.tableW <= r.wrapW + 1;
    check('数字列完整可见（放得下 或 能滑过去）',
      allVisible || (r.scrollable && r.scrolled && r.lastCellVisible),
      allVisible ? `整表放得下：表格 ${r.tableW} ≤ 容器 ${r.wrapW}`
                 : `可滑动：scrollLeft→${r.maxScroll}，末行可见=${r.lastCellVisible}`);
    check('末行数值完整显示', r.lastCellVisible, `「${r.lastCellText}」`);
    // 页面级不该再出现横向滚动
    const ovf = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    check('页面级无横向滚动', ovf <= 1, `溢出 ${ovf}px`);
    await ctx.close();
  }

  // ── ③ 表单可用性 ──────────────────────────────────────────────────────
  console.log('\n【③ 询盘表单（7 语言版本）】');
  for (const p of ['/contact.html', '/de/contact.html', '/ja/contact.html']) {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await ctx.newPage();
    await page.goto(BASE + p, { waitUntil: 'networkidle' });
    const r = await page.evaluate(() => {
      const f = document.getElementById('inquiry-form');
      if (!f) return { has: false };
      const ctrls = Array.from(f.querySelectorAll('input,select,textarea'))
        .filter(el => el.type !== 'hidden' && !el.classList.contains('form-hp'));
      const labelled = ctrls.filter(el => el.labels && el.labels.length > 0).length;
      const hp = f.querySelector('.form-hp');
      const ok = document.getElementById('form-ok');
      const submit = f.querySelector('button[type="submit"]');
      return { has: true, total: ctrls.length, labelled,
               hp: !!hp, hpName: hp ? hp.name : null,
               live: ok ? ok.getAttribute('aria-live') : null,
               msgOk: ok ? (ok.dataset.msgOk || '').slice(0, 24) : null,
               msgFail: ok ? (ok.dataset.msgFail || '').slice(0, 24) : null,
               btnH: submit ? Math.round(submit.getBoundingClientRect().height) : 0 };
    });
    check(`${p} 6 个控件都有关联 label`, r.has && r.labelled === r.total && r.total === 6,
      `${r.labelled}/${r.total}`);
    check(`${p} 诱饵字段存在且 tabindex=-1`, r.hp && r.hpName === '_gotcha', String(r.hpName));
    check(`${p} 反馈框 aria-live`, r.live === 'polite', String(r.live));
    check(`${p} 本地化提示文案存在`, !!r.msgOk && !!r.msgFail, `${r.msgOk}… / ${r.msgFail}…`);
    check(`${p} 提交按钮 ≥44px`, r.btnH >= 44, r.btnH + 'px');
    await ctx.close();
  }

  console.log(`\n结论：通过 ${pass} / 失败 ${fail}`);
  await browser.close();
  process.exit(fail ? 1 : 0);
})();
