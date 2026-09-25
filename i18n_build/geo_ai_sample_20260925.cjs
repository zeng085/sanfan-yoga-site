/**
 * AI 答案层采样器（秘塔 metaso.cn）—— fjsanfan.com AI 引用基线的「路 B」。
 *
 * ── 为什么用秘塔 ──
 * 本机在墙内，Perplexity / ChatGPT / Gemini / Google 全部不可达（DNS 被污染：
 * chatgpt.com→31.13.94.36、google.com→31.13.92.37，均为 Facebook IP）。秘塔是
 * 唯一可直连、且**带来源列表**的 AI 答案引擎。
 *
 * ── 两个关键坑 ──
 * ① 来源的真实域名 **不在 DOM 里**：来源卡片 innerText 只有标题，锚点无 href。
 *    唯一可靠来源是页面自动请求的 favicon：`https://cdn.metaso.cn/favicon/<域名>.ico`
 *    → 所以必须监听 network request，不能靠解析 HTML 或数 innerText。
 *    （首版靠标题里出现的公司名人工推断域名，与文本计数对不上，属不严谨。）
 * ② 不要用 waitUntil:'networkidle' —— 页面有常驻轮询，永远不会 idle。
 *
 * 用法：
 *   NODE_PATH=/Users/mac-zlg/.workbuddy/binaries/node/workspace/node_modules \
 *   /Users/mac-zlg/.workbuddy/binaries/node/versions/22.12.0/bin/node \
 *     i18n_build/geo_ai_sample_20260925.cjs queries.json out.json
 */
const fs = require('fs');
const { chromium } = require('playwright');

const QFILE = process.argv[2];
const OUT = process.argv[3] || '/tmp/metaso_raw.json';
if (!QFILE) {
  console.error('用法: node geo_ai_sample_20260925.cjs <queries.json> [out.json]');
  process.exit(1);
}
const QS = JSON.parse(fs.readFileSync(QFILE, 'utf8'));

/** 从 favicon 请求里抠来源域名 */
function faviconDomain(url) {
  const m = url.match(/cdn\.metaso\.cn\/favicon\/([a-z0-9.-]+\.[a-z]{2,})\.ico/i);
  return m ? m[1].toLowerCase() : null;
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const out = [];

  for (const q of QS) {
    const rec = { q, ok: false, url: '', answer: '', src_domains: [], err: '' };
    const domains = new Set();
    const onReq = (r) => {
      const d = faviconDomain(r.url());
      if (d) domains.add(d);
    };
    page.on('request', onReq);
    try {
      await page.goto('https://metaso.cn/', { waitUntil: 'domcontentloaded', timeout: 45000 });
      await page.waitForTimeout(3000);
      const ta = page.locator('textarea').first();
      await ta.click();
      await ta.fill(q);
      await page.waitForTimeout(400);
      await ta.press('Enter');
      await page.waitForTimeout(20000); // 固定等待，避开 networkidle
      rec.url = page.url();
      rec.answer = await page.evaluate(() => document.body.innerText);
      rec.src_domains = [...domains].sort();
      rec.ok = rec.answer.length > 200;
    } catch (e) {
      rec.err = String(e.message).slice(0, 160);
    }
    page.off('request', onReq);
    out.push(rec);

    const has = (d) => (rec.src_domains.some((x) => x === d || x.endsWith('.' + d)) ? '✓' : '-');
    console.log(
      `[${rec.ok ? 'OK ' : 'ERR'}] ${q.slice(0, 40).padEnd(40)} len=${String(rec.answer.length).padStart(5)}` +
      `  来源域${String(rec.src_domains.length).padStart(3)} 个 | fjsanfan:${has('fjsanfan.com')} sanfanyoga:${has('sanfanyoga.com')}`
    );
    console.log(`        来源: ${rec.src_domains.slice(0, 10).join(', ')}`);
  }

  fs.writeFileSync(OUT, JSON.stringify(out, null, 1), 'utf8');
  console.log('原始记录 ->', OUT);
  await browser.close();
})();
