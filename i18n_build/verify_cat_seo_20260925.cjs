// 分类页 SEO 区块渲染验收（#205 FAQ + #206 PVC vs TPE）
// 以注释区间精确定位插入内容，检查：条数 / 标题 / 语言态 / 语言配对是否「半可见」/
// JSON-LD FAQPage 是否与可见块同源同数量 / 内链是否可解析 / 横向溢出 / JS 报错。
//
// 三个坑（沿用 verify_internal_links.cjs 的教训，勿删）：
//   ① 语言态是 localStorage 优先 + **cookie 兜底**（main.js）→ 两处都要写，只清 localStorage 会被 cookie 顶回
//   ② <details> 折叠时 .faq-a 的 innerText 为空 → 取词一律用 textContent，可见性用 getComputedStyle 判 span
//   ③ 这里是模板字面量，\s 会被吃成 s → 正则里的反斜杠必须写 \\
const { chromium } = require('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:8851';
const OUT = process.env.OUT || '/tmp';

const LANGS = [
  { dir: '', lang: 'en' },
  { dir: 'de/', lang: 'de' },
  { dir: 'ja/', lang: 'ja' },
  { dir: 'ko/', lang: 'ko' },
  { dir: 'fr/', lang: 'fr' },
  { dir: 'it/', lang: 'it' },
  { dir: 'es/', lang: 'es' },
];

// kind: faq = 分类页 FAQ 块；pvc-mat = materials.html 的对比小节；pvc-blog = 博客里的交叉小节
// blocks：该页应有的注释区间个数。⚠️ EN 的博客文章页是「英文正文 + 块级 div.lang-zh 中文正文」
//   双体结构（其余语言页只有单正文），两体各有一个 ilink:v1，插入点因此也是两个 ——
//   这是**正确**的：中文正文若拿不到这个小节，切换中文后会缺内容。所以 EN 博客页是 2 个块、
//   但任一时刻只有 1 个可见（另一个整块 display:none）。子语言页为 1。
const PAGES = [];
for (const L of LANGS) {
  const blogBlocks = L.lang === 'en' ? 2 : 1;
  PAGES.push({ url: `/${L.dir}tpe-yoga-mats.html`, lang: L.lang, kind: 'faq', items: 5, links: 0, blocks: 1 });
  PAGES.push({ url: `/${L.dir}pu-rubber-yoga-mats.html`, lang: L.lang, kind: 'faq', items: 5, links: 0, blocks: 1 });
  PAGES.push({ url: `/${L.dir}materials.html`, lang: L.lang, kind: 'pvc-mat', items: 5, links: 2, blocks: 1 });
  PAGES.push({ url: `/${L.dir}blog/tpe-vs-pu.html`, lang: L.lang, kind: 'pvc-blog', items: 0, links: 1, blocks: blogBlocks });
}

// 以注释区间收集兄弟节点（博客块是多个平级元素，不是一个容器）
const CHECK = (marker) => `(() => {
  const M = ${JSON.stringify(marker)};
  const walker = document.createTreeWalker(document.documentElement, NodeFilter.SHOW_COMMENT);
  const opens = [];
  let n;
  while (n = walker.nextNode()) if (n.data.trim() === M) opens.push(n);
  const segs = opens.map(o => {
    const nodes = [];
    let s = o.nextSibling;
    while (s) {
      if (s.nodeType === 8 && s.data.trim() === '/' + M) break;
      nodes.push(s);
      s = s.nextSibling;
    }
    const els = nodes.filter(x => x.nodeType === 1);
    const links = [];
    for (const e of els) {
      links.push(...e.querySelectorAll('a[href]'));
      if (e.tagName === 'A') links.push(e);
    }
    const spans = [];
    for (const e of els) spans.push(...e.querySelectorAll('.lang-en, .lang-zh'));
    // 半可见 = 同一个承载元素里 en/zh 两个 span 的 display 一个显示一个隐藏不一致
    const htmlCls = document.documentElement.className;
    const showZh = htmlCls.indexOf('show-zh') >= 0;
    let badPairs = 0, pairCount = 0;
    const parents = new Set(spans.map(s => s.parentElement));
    for (const p of parents) {
      const en = p.querySelector(':scope > .lang-en'), zh = p.querySelector(':scope > .lang-zh');
      const enD = en ? getComputedStyle(en).display : null;
      const zhD = zh ? getComputedStyle(zh).display : null;
      if (!en && !zh) continue;
      if (!en || !zh) { badPairs++; continue; }
      pairCount++;
      const ok = showZh ? (enD === 'none' && zhD !== 'none') : (zhD === 'none' && enD !== 'none');
      if (!ok) badPairs++;
    }
    // 可见语言取词：抓一个显示中的 lang 容器，用 textContent（<details> 折叠时 innerText 为空）
    const firstVisible = spans.find(s => getComputedStyle(s).display !== 'none');
    const sample = firstVisible ? (firstVisible.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 78) : '';
    const details = [];
    for (const e of els) details.push(...e.querySelectorAll('details.faq-item'));
    const rows = [];
    for (const e of els) { const tb = e.querySelector('tbody'); if (tb) rows.push(...tb.querySelectorAll('tr')); }
    return {
      n: els.length,
      faqItems: details.length,
      rows: rows.length,
      links: links.length,
      hrefs: links.map(a => a.getAttribute('href')),
      // 块本身是否可见（整块 display:none 时不参与渲染）
      vis: els.length ? els[0].offsetParent !== null : false,
      visibleLinks: links.filter(a => a.offsetParent !== null).length,
      hasHeading: els.some(x => /^H[1-6]$/.test(x.tagName) || !!x.querySelector('h2,h3')),
      pairCount, badPairs, sample,
      lastAnchor: (els[els.length - 1] || {}).id || '',
    };
  });
  // JSON-LD 侧：找 @id 以 #faq-cat 结尾的 FAQPage，数 mainEntity
  let ldItems = -1, ldId = '';
  for (const sc of document.querySelectorAll('script[type="application/ld+json"]')) {
    let j; try { j = JSON.parse(sc.textContent); } catch (e) { continue; }
    const arr = Array.isArray(j) ? j : [j];
    for (const o of arr) {
      const g = o && o['@graph'] ? o['@graph'] : [o];
      for (const x of g) {
        if (x && x['@type'] === 'FAQPage' && typeof x['@id'] === 'string' && x['@id'].indexOf('#faq-cat') >= 0) {
          ldId = x['@id'];
          ldItems = (x.mainEntity || []).length;
        }
      }
    }
  }
  return {
    count: segs.length, segs, htmlCls: document.documentElement.className,
    ldItems, ldId,
    overflowX: document.documentElement.scrollWidth > window.innerWidth + 2,
  };
})()`;

// 内链可解析：拿到 href 后逐个 fetch 头，确认 200 且不是 301 到别处
async function headOk(page, base, fromUrl, href) {
  if (!href || href.startsWith('#') || href.startsWith('mailto:')) return 'skip';
  const u = new URL(href, base + fromUrl).href;
  const r = await page.request.get(u, { failOnStatusCode: false, maxRedirects: 0 });
  return r.status();
}

(async () => {
  const browser = await chromium.launch();
  let bad = 0, checked = 0;

  for (const vp of [{ w: 1440, h: 900, tag: '桌面' }, { w: 390, h: 844, tag: '手机' }]) {
    const ctx = await browser.newContext({ viewport: { width: vp.w, height: vp.h } });
    const page = await ctx.newPage();
    const errs = [];
    page.on('pageerror', e => errs.push(String(e).slice(0, 70)));
    let curLang = null;

    for (const p of PAGES) {
      const tag = `${p.lang}/${vp.tag}`;
      const want = p.kind === 'faq' ? 'cfaq:v1' : 'pvctpe:v1';
      try {
        // 语言态与上一页隔离：只在语言切换时重置，避免 56 次多余的根页跳转
        if (curLang !== p.lang) {
          await page.goto(BASE + '/index.html', { waitUntil: 'domcontentloaded', timeout: 25000 });
          await page.evaluate(z => {
            try {
              if (z) localStorage.setItem('siteLang', 'zh'); else localStorage.removeItem('siteLang');
              document.cookie = 'siteLang=' + (z ? 'zh' : '') + '; path=/; Max-Age=' + (z ? 31536000 : 0);
            } catch (e) { }
          }, false);
          curLang = p.lang;
        }
        await page.goto(BASE + p.url, { waitUntil: 'domcontentloaded', timeout: 25000 });
        await page.waitForTimeout(160);
        const r = await page.evaluate(CHECK(want));
        const msgs = [];
        if (r.count !== p.blocks) msgs.push(`块数 ${r.count}≠${p.blocks}`);
        // 任一时刻**恰好 1 个块可见** —— 这正是「英文正文 / 中文正文」互斥的判据。
        // EN 博客页有 2 个块，若两个都可见说明双语正文同时露出来了。
        const visBlocks = r.segs.filter(x => x.vis).length;
        if (visBlocks !== 1) msgs.push(`可见块 ${visBlocks} 个（应 1）`);
        const s = r.segs.find(x => x.vis) || r.segs[0];
        if (s) {
          if (p.kind === 'faq' && s.faqItems !== p.items) msgs.push(`FAQ ${s.faqItems}≠${p.items} 条`);
          if (p.kind === 'pvc-mat' && s.rows !== p.items) msgs.push(`表行 ${s.rows}≠${p.items}`);
          if (!s.hasHeading) msgs.push('缺标题');
          if (s.badPairs) msgs.push(`语言配对异常 ${s.badPairs}/${s.pairCount}`);
          if (!!p.links && s.links !== p.links) msgs.push(`链接 ${s.links}≠${p.links}`);
          if (p.kind === 'pvc-mat' && s.lastAnchor !== 'pvc-vs-tpe') msgs.push(`锚点 id=${s.lastAnchor || '无'}`);
          // 可见语言下应有可见内容（折叠 details 也算可见 summary）
          for (const h of s.hrefs) {
            const st = await headOk(page, BASE, p.url, h);
            if (st !== 'skip' && st !== 200) msgs.push(`${h} → ${st}`);
          }
        }
        // FAQ 块必须有配套 JSON-LD，且条数一致
        if (p.kind === 'faq') {
          if (r.ldItems < 0) msgs.push('缺 FAQPage(#faq-cat) JSON-LD');
          else if (r.ldItems !== p.items) msgs.push(`JSON-LD ${r.ldItems}≠${p.items} 条`);
        }
        if (r.overflowX) msgs.push('横向溢出');
        checked++;
        if (msgs.length) { bad++; console.log(`✗ ${tag.padEnd(10)} ${p.url}  ${msgs.join(' / ')}`); }
        else console.log(`✓ ${tag.padEnd(10)} ${p.url.padEnd(38)} [${r.htmlCls || 'en'}] ${s ? s.sample.slice(0, 60) : ''}`);
      } catch (e) {
        bad++; console.log(`✗ ${tag.padEnd(10)} ${p.url}  ERR ${String(e).slice(0, 70)}`);
      }
    }
    if (errs.length) { bad++; console.log(`✗ ${vp.tag} JS 报错: ${errs.slice(0, 2).join(' ; ')}`); }
    await ctx.close();
  }

  // 出图：确认视觉上确实是「FAQ / 对比表」而不是裸文本。
  // ⚠️ 两个坑：
  //   ① clip 的坐标系是**整页绝对坐标**，而 boundingBox() 在滚动后返回的是视口坐标 ——
  //      两者混用会把截图裁到页面顶部（实测截出来是产品网格，不是 FAQ）。
  //      这里改为 getBoundingClientRect() + scrollY/X 自己算绝对坐标。
  //   ② 一个标记可能有多个区间（EN 博客页双语正文），必须挑**当前可见**的那个。
  const shotJobs = [
    { url: '/tpe-yoga-mats.html', m: 'cfaq:v1', zh: false, name: 'cfaq_tpe_en' },
    { url: '/ja/tpe-yoga-mats.html', m: 'cfaq:v1', zh: false, name: 'cfaq_tpe_ja' },
    { url: '/materials.html', m: 'pvctpe:v1', zh: false, name: 'pvctpe_mat_en' },
    { url: '/blog/tpe-vs-pu.html', m: 'pvctpe:v1', zh: true, name: 'pvctpe_blog_zh' },
  ];
  for (const j of shotJobs) {
    const ctx = await browser.newContext({ viewport: { width: 1400, height: 900 } });
    const page = await ctx.newPage();
    await page.goto(BASE + '/index.html', { waitUntil: 'domcontentloaded' });
    await page.evaluate(z => {
      try {
        if (z) localStorage.setItem('siteLang', 'zh'); else localStorage.removeItem('siteLang');
        document.cookie = 'siteLang=' + (z ? 'zh' : '') + '; path=/; Max-Age=' + (z ? 31536000 : 0);
      } catch (e) { }
    }, j.zh);
    await page.goto(BASE + j.url, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(320);
    await page.addStyleTag({ content: 'html{scroll-behavior:auto !important}' });
    const box = await page.evaluate(M => {
      document.querySelectorAll('details.faq-item').forEach(d => { d.open = true; });
      const w = document.createTreeWalker(document.documentElement, NodeFilter.SHOW_COMMENT);
      const opens = []; let n;
      while (n = w.nextNode()) if (n.data.trim() === M) opens.push(n);
      const all = opens.map(o => {
        const els = []; let s = o.nextSibling;
        while (s) { if (s.nodeType === 8 && s.data.trim() === '/' + M) break; if (s.nodeType === 1) els.push(s); s = s.nextSibling; }
        return els;
      }).filter(els => els.length && els[0].offsetParent !== null);
      if (!all.length) return null;
      const els = all[all.length - 1];
      const rs = els.map(e => e.getBoundingClientRect());
      const top = Math.min(...rs.map(r => r.top)) + window.scrollY;
      const bot = Math.max(...rs.map(r => r.bottom)) + window.scrollY;
      const left = Math.min(...rs.map(r => r.left)) + window.scrollX;
      const right = Math.max(...rs.map(r => r.right)) + window.scrollX;
      return { top: Math.max(0, Math.round(top) - 16), height: Math.round(bot - top) + 32, left: Math.max(0, Math.round(left) - 16), width: Math.round(right - left) + 32 };
    }, j.m);
    if (box) {
      await page.screenshot({
        path: `${OUT}/${j.name}.png`, fullPage: true,
        clip: { x: box.left, y: box.top, width: Math.min(box.width, 1400), height: Math.min(box.height, 2600) },
      });
      console.log(`  📷 ${j.name}.png  (${box.width}×${box.height})`);
    } else console.log(`  📷 ${j.name}.png  跳过（无可视块）`);
    await ctx.close();
  }
  await browser.close();
  console.log(`\n共检查 ${checked} 页 · ` + (bad === 0 ? '全部通过' : `${bad} 项异常`));
  process.exit(bad === 0 ? 0 : 1);
})();
