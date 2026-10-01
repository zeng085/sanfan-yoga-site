/* 文案改动后的抽检：确认 FAQ 换词没破坏渲染（3 个改动页 × 2 视口） */
const { chromium } = require('playwright');
const BASE = 'file:///Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16';
const PAGES = [
  'pilates/index.html',
  'pilates/pilates-cadillac.html',
  'pilates/pilates-wunda-chair.html',
];
const VPS = [
  { name: 'desktop-1440', w: 1440, h: 900 },
  { name: 'mobile-390', w: 390, h: 844 },
];

(async () => {
  const browser = await chromium.launch();
  let bad = 0;
  for (const vp of VPS) {
    const ctx = await browser.newContext({ viewport: { width: vp.w, height: vp.h } });
    const page = await ctx.newPage();
    for (const rel of PAGES) {
      await page.goto(`${BASE}/${rel}`, { waitUntil: 'load' });
      await page.waitForTimeout(250);
      const r = await page.evaluate(() => {
        const t = document.documentElement.scrollWidth - document.documentElement.clientWidth;
        // ⚠️ 坑：不能用 body.innerText —— FAQ 在折叠的 <details> 里，innerText 会排除
        //    display:none 的内容，导致「新文案=false」的假阴性。必须用 textContent，
        //    并单独取「可见正文」做旧词核验（两者判据不同，不能混）。
        const all = document.body.textContent || '';
        const visible = document.body.innerText || '';
        const legacy = /rubberwood|white maple|Croatian beech|piano.?lacquer/i.test(all);
        const hasNew = /Material is set per model/.test(all);
        // 折叠内容里也要查旧词（FAQ 是新写的，这里应无旧词）
        const faqTxt = [...document.querySelectorAll('details.faq-item')].map(d => d.textContent).join(' ');
        const faqLegacy = /rubberwood|white maple|Croatian beech|piano.?lacquer/i.test(faqTxt);
        const faq = document.querySelectorAll('details.faq-item').length;
        return { overflow: t, legacy, hasNew, faqLegacy, faq };
      });
      const flag = (r.overflow > 0 || r.faqLegacy || !r.hasNew) ? '⚠️' : '✓';
      if (flag === '⚠️') bad++;
      console.log(`  ${flag} ${vp.name.padEnd(14)} ${rel.padEnd(34)} 溢出${String(r.overflow).padStart(3)}px  新文案=${r.hasNew}  FAQ内旧词=${r.faqLegacy}  FAQ项=${r.faq}`);
    }
    await ctx.close();
  }
  console.log(bad === 0 ? '\n✅ 抽检全部通过' : `\n⚠️ ${bad} 处异常`);
  await browser.close();
})();
