#!/usr/bin/env node
/**
 * 灯箱标题（caption）取证探针 —— 2026-10-01
 *
 * 为什么单独写：
 *   .cat-fig 的 <figcaption> 里同时存在 .lang-en / .lang-zh 两套文本，
 *   靠 CSS display 切换。JS 里 figcaption.textContent 会把两套 **一起** 读出来，
 *   还会带上链接文案（"view larger" + "放大查看" 之间没有空白 → 两个词粘在一起）。
 *   只跑「灯箱能开能关」的检查抓不到这个问题 —— 必须断言 caption 的**具体文本**。
 *
 * 用法：BASE=https://fjsanfan.com node probe_lightbox_caption_20261001.cjs
 */
const { chromium } = require('playwright');

const BASE = process.env.BASE || 'http://127.0.0.1:8866';
const PAGES = [
  'pilates/pilates-reformer.html',
  'pilates/pilates-ladder-barrel.html',
];

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  let bad = 0;

  for (const p of PAGES) {
    const page = await ctx.newPage();
    await page.goto(`${BASE}/${p}`, { waitUntil: 'load', timeout: 60000 });
    // 预热 lazy 图
    await page.evaluate(async () => {
      for (let y = 0; y < document.body.scrollHeight; y += 600) {
        window.scrollTo(0, y);
        await new Promise(r => setTimeout(r, 40));
      }
      window.scrollTo(0, 0);
    });
    await page.waitForTimeout(400);

    console.log(`\n=== ${p} ===`);

    for (const lang of ['en', 'zh']) {
      await page.evaluate(l => {
        document.documentElement.classList.toggle('show-zh', l === 'zh');
      }, lang);
      await page.waitForTimeout(150);

      // 点第一张画册图 → 灯箱
      const fig = page.locator('.cat-fig').first();
      const hasFig = await fig.count();
      if (!hasFig) { console.log(`  [${lang}] 无 .cat-fig，跳过`); continue; }
      await fig.locator('img').first().click({ force: true });
      await page.waitForTimeout(350);

      const open = await page.evaluate(() =>
        !!document.querySelector('.lb.is-open'));
      const cap = await page.evaluate(() => {
        const c = document.querySelector('.lb-cap');
        return c ? c.textContent : '(无 .lb-cap)';
      });
      const imgOk = await page.evaluate(() => {
        const i = document.querySelector('.lb img');
        return !!(i && i.getAttribute('src'));
      });

      const expectCJK = lang === 'zh';
      const hasCJK = /[\u4e00-\u9fff]/.test(cap);
      const hasLatin = /catalogue|page/i.test(cap);
      const glued = /[a-z][\u4e00-\u9fff]|[\u4e00-\u9fff][a-z]/i.test(cap);
      const actionLeak = /view (larger|full size)|放大查看|查看原图/i.test(cap);

      let note = '';
      if (!open) { note += ' ✗ 灯箱未打开'; bad++; }
      else if (!imgOk) { note += ' ✗ 灯箱图 src 为空'; bad++; }
      if (open && hasCJK === expectCJK && hasLatin !== expectCJK) {
        // 与当前语言一致 ✓
      } else if (open) {
        note += ` ✗ 语言不纯（期望${expectCJK ? '中文' : '英文'}）`; bad++;
      }
      if (glued) { note += ' ✗ 中英粘连'; bad++; }
      if (actionLeak) { note += ' ✗ 串进了链接文案'; bad++; }

      console.log(`  [${lang}] open=${open ? 'Y' : 'N'} img=${imgOk ? 'Y' : 'N'}`);
      console.log(`         caption = ${JSON.stringify(cap)}${note}`);
      await page.evaluate(() => {
        const c = document.querySelector('.lb-close');
        if (c) c.click();
      });
      await page.waitForTimeout(150);
    }

    // 链接入口是否也接上灯箱（非图片点击路径）
    await page.evaluate(() => document.documentElement.classList.remove('show-zh'));
    const zoom = page.locator('.cat-zoom').first();
    const nZoom = await page.locator('.cat-zoom').count();
    if (nZoom > 0) {
      await zoom.click();
      await page.waitForTimeout(300);
      const open = await page.evaluate(() => !!document.querySelector('.lb.is-open'));
      console.log(`  [链接入口] .cat-zoom 数=${nZoom}  点链接开灯箱=${open ? 'Y ✓' : 'N ✗'}`);
      if (!open) bad++;
      await page.keyboard.press('Escape');
    } else {
      // 没有 cat-zoom → 点 figcaption 里的 a 看是否新窗口行为
      const link = page.locator('.cat-fig figcaption a').first();
      if (await link.count()) {
        const cls = await link.getAttribute('class');
        console.log(`  [链接入口] 无 .cat-zoom；figcaption 链接 class=${JSON.stringify(cls)} → 走原生新窗口（行为不一致）`);
      }
    }
    await page.close();
  }

  await browser.close();
  console.log(`\n失败项：${bad}`);
  process.exit(bad ? 5 : 0);
})();
