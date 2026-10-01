/**
 * 消费者视角 A/B 渲染对比：线上版 vs 新版
 *
 * 为什么要做：静态读 HTML 无法回答「消费者更喜欢哪个」。必须看真实渲染
 * —— 首屏看到什么、图多大、表格宽不宽、要滚多久才见到实物图。
 *
 * ⚠️ 必须起本地 HTTP 服务（file:// 会破 main.js 的相对路径推算 → 假失败）
 *    用法：先 `python3 -m http.server 8861 --bind 127.0.0.1 &`，再跑本脚本
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE = 'http://127.0.0.1:8861';
const OUT = path.join(__dirname, 'reports');
const VPS = [
  { name: 'mobile-390', w: 390, h: 844, dpr: 2, mobile: true },
  { name: 'desktop-1440', w: 1440, h: 900, dpr: 1, mobile: false },
];
const PAGES = [
  { key: 'live', url: '/pilates/_ab_live_ladder-barrel.html', label: '线上版' },
  { key: 'new', url: '/pilates/pilates-ladder-barrel.html', label: '新版' },
];

(async () => {
  const browser = await chromium.launch();
  const summary = {};

  for (const vp of VPS) {
    for (const page of PAGES) {
      const ctx = await browser.newContext({
        viewport: { width: vp.w, height: vp.h },
        deviceScaleFactor: vp.dpr,
        isMobile: vp.mobile,
        hasTouch: vp.mobile,
        locale: 'en-US',
      });
      const p = await ctx.newPage();
      await p.goto(BASE + page.url, { waitUntil: 'load' });
      // 分步滚到底触发懒加载，再回顶（否则 lazy 图未解码）
      await p.evaluate(async () => {
        const step = window.innerHeight;
        for (let y = 0; y < document.body.scrollHeight; y += step) {
          window.scrollTo(0, y);
          await new Promise(r => setTimeout(r, 90));
        }
        window.scrollTo(0, 0);
      });
      await p.waitForTimeout(900);

      const m = await p.evaluate(() => {
        const Q = (s) => document.querySelector(s);
        const QA = (s) => Array.from(document.querySelectorAll(s));
        const txt = (el) => el ? el.innerText.replace(/\s+/g, ' ').trim() : '';
        const rect = (el) => { const r = el.getBoundingClientRect(); return { t: Math.round(r.top + window.scrollY), h: Math.round(r.height), w: Math.round(r.width) }; };
        const H = document.body.scrollHeight;

        // 首屏里有什么（0 ~ 一屏高）
        const fold = window.innerHeight;
        const inFold = (el) => { const r = el.getBoundingClientRect(); return r.top < fold && r.bottom > 0; };
        const foldTexts = QA('h1,h2,h3,p,li,a.btn,button').filter(inFold).map(e => txt(e).slice(0, 70)).filter(Boolean);

        // 第一张「实物图」距顶部的距离 —— 消费者多久能看到真东西
        const imgs = QA('img').map(im => ({ src: im.getAttribute('src') || '', ...rect(im), nat: im.naturalWidth + 'x' + im.naturalHeight }));
        const photos = imgs.filter(x => /catalog|\.webp|\.jpg/i.test(x.src) && x.h > 60);

        // 表格水平是否溢出容器
        const tbl = Q('table');
        const tblOverflow = tbl ? (tbl.scrollWidth > tbl.parentElement.clientWidth + 2) : null;

        // 主要区块顺序
        const secs = QA('section, div[class*=sec], h2').slice(0, 40).map(e => ({ tag: e.tagName, cls: e.className.slice(0, 40), ...rect(e) }));

        // FAQ 是否可见（折叠时也算，取 details 汇总）
        const details = QA('details');
        const faqOpen = details.filter(d => d.open).length;

        // 页面总高（消费者要滚多久）
        return {
          title: document.title,
          pageH: H,
          screens: +(H / fold).toFixed(1),
          foldTexts,
          imgCount: imgs.length,
          photoCount: photos.length,
          firstPhotoTop: photos.length ? Math.min(...photos.map(x => x.t)) : null,
          photoSizes: photos.map(x => `${x.w}x${x.h}@${x.t}`).slice(0, 8),
          tblRows: tbl ? tbl.querySelectorAll('tr').length : 0,
          tblOverflow,
          details: details.length,
          faqOpen,
          secs,
        };
      });

      const shot = path.join(OUT, `ab_${page.key}_${vp.name}_20261001.png`);
      await p.screenshot({ path: shot, fullPage: true });
      // 首屏单独截一张（消费者第一眼）
      const foldShot = path.join(OUT, `ab_${page.key}_${vp.name}_FOLD_20261001.png`);
      await p.screenshot({ path: foldShot, fullPage: false });

      summary[`${page.key}@${vp.name}`] = { label: page.label, ...m, shot, foldShot };
      await ctx.close();
    }
  }

  await browser.close();

  // 打印对比
  for (const vp of VPS) {
    console.log(`\n${'='.repeat(78)}\n视口 ${vp.name}（${vp.w}×${vp.h}）\n${'='.repeat(78)}`);
    for (const page of PAGES) {
      const s = summary[`${page.key}@${vp.name}`];
      console.log(`\n【${s.label}】`);
      console.log(`  页面总高        ${s.pageH}px = ${s.screens} 屏（消费者要滚几下）`);
      console.log(`  img 总数        ${s.imgCount}（其中实物大图 ${s.photoCount}）`);
      console.log(`  首张实物图距顶  ${s.firstPhotoTop === null ? '无' : s.firstPhotoTop + 'px'}  ${s.firstPhotoTop === null ? '' : s.firstPhotoTop < vp.h ? '← 首屏内 ✅' : '← 需滚动'}`);
      console.log(`  实物图尺寸      ${s.photoSizes.join('  ')}`);
      console.log(`  表格行数        ${s.tblRows}    水平溢出=${s.tblOverflow}`);
      console.log(`  FAQ 条数        ${s.details}（默认展开 ${s.faqOpen}）`);
      console.log(`  首屏可见文本（${s.foldTexts.length} 条）:`);
      s.foldTexts.slice(0, 9).forEach(t => console.log(`      · ${t}`));
    }
  }
  fs.writeFileSync(path.join(OUT, 'ab_consumer_view_20261001.json'), JSON.stringify(summary, null, 2), 'utf-8');
  console.log(`\n截图与数据已写入 ${OUT}/ab_*_20261001.png / .json`);
})();
