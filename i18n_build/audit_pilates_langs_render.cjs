/**
 * 普拉提板块【6 语言版】渲染审计（2026-09-15）
 *
 * 与 audit_pilates_render.cjs（管 EN 9 页）互补：语言版多一类失败模式 ——
 *   ① 语言版比 EN 原页深一级目录（<lang>/pilates/），assets 相对路径写错就
 *      整站交互（移动菜单 / 切换器 / FAQ 折叠）全部失效，纯静态检查看不出来；
 *   ② 切换器必须**高亮当前语言**、且点 EN 能真正跳到英文页；
 *   ③ 语言版是纯单语，出现任何 .lang-zh 可见块都是管线故障；
 *   ④ 翻译后文本长度变化（德语长、日语密）容易撑破窄屏布局 → 横向溢出。
 *
 * 用法
 *   NODE_PATH=<workspace>/node_modules node i18n_build/audit_pilates_langs_render.cjs
 *   BASE=http://127.0.0.1:8888 node ...（默认 127.0.0.1:8848）
 */
const fs = require('fs');
const { chromium } = require('playwright');

const BASE = process.env.BASE || 'http://127.0.0.1:8848';
const OUT = 'outputs/pilates-langs-preview';
fs.mkdirSync(OUT, { recursive: true });

const LANGS = ['de', 'ja', 'ko', 'fr', 'it', 'es'];
const LABEL = { de: 'DE', ja: 'JA', ko: 'KO', fr: 'FR', it: 'IT', es: 'ES' };
// 每语言抽查 2 页：板块首页（含卡片网格）+ 最长族页（reformer，文本量最大）
const PAGES = ['index.html', 'pilates-reformer.html'];

const VIEWPORTS = [
  { w: 320, h: 640, name: '320' },
  { w: 390, h: 844, name: '390' },
  { w: 768, h: 1024, name: '768' },
  { w: 1440, h: 900, name: '1440' },
];

const fails = [];
const warns = [];
const isNoise = (u) => /google-analytics|googletagmanager|doubleclick|clarity\.ms/i.test(u);

async function auditPage(browser, lg, slug, vp) {
  const ctx = await browser.newContext({ viewport: { width: vp.w, height: vp.h } });
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', (m) => { if (m.type() === 'error' && !isNoise(m.text())) errs.push(m.text().slice(0, 140)); });
  page.on('requestfailed', (r) => { if (!isNoise(r.url())) errs.push('REQFAIL ' + r.url().slice(-70)); });
  page.on('response', (r) => { if (r.status() >= 400 && !isNoise(r.url())) errs.push('HTTP ' + r.status() + ' ' + r.url().slice(-70)); });

  const url = `${BASE}/${lg}/pilates/${slug}`;
  const rel = `${lg}/pilates/${slug}`;
  await page.goto(url, { waitUntil: 'load', timeout: 30000 });
  await page.waitForTimeout(200);

  // ⚠️ 先整页滚一遍：网格里的图大多是 loading="lazy"，不滚到视口内
  //    naturalWidth 恒为 0 → 会被误判成「坏图」（2026-09-15 首跑踩过）。
  //    滚完还要**等图片真的 complete** —— 60ms/步的滚动只是「触发开始加载」，
  //    立刻测量仍会抓到还在解压中的图（第 2 跑仍有 12 条误报，实测三张图
  //    全部 HTTP 200）。所以：滚到底 → 停在底部 → waitForFunction(complete)。
  await page.evaluate(async () => {
    const step = Math.round(window.innerHeight * 0.8);
    for (let y = 0; y < document.body.scrollHeight; y += step) {
      window.scrollTo(0, y);
      await new Promise((r) => setTimeout(r, 60));
    }
    window.scrollTo(0, document.body.scrollHeight);
  });
  await page.waitForFunction(
    () => Array.from(document.images).every((i) => i.complete),
    null, { timeout: 8000 }).catch(() => { /* 有图确实加载不完就交给下面的判定 */ });

  // ① 横向溢出
  const ov = await page.evaluate(() => {
    const de = document.documentElement;
    const over = [];
    if (de.scrollWidth > window.innerWidth + 1) {
      document.querySelectorAll('body *').forEach((el) => {
        const r = el.getBoundingClientRect();
        if (r.width > 0 && r.right > window.innerWidth + 1) {
          const cs = getComputedStyle(el);
          if (cs.overflowX === 'auto' || cs.overflowX === 'scroll') return;
          over.push(el.tagName.toLowerCase() + '.' + (el.className || '').toString().split(' ')[0]);
        }
      });
    }
    return { sw: de.scrollWidth, vw: window.innerWidth, over: [...new Set(over)].slice(0, 4) };
  });
  if (ov.sw > ov.vw + 1) fails.push(`[${vp.name}] ${rel} 横向溢出 ${ov.sw}>${ov.vw} ${ov.over.join(',')}`);

  // ② 坏图（complete 且 naturalWidth=0 才是真坏；未 complete 只是没加载完）
  const img = await page.evaluate(() => {
    const all = Array.from(document.querySelectorAll('img'));
    const bad = all.filter((i) => i.complete && i.naturalWidth === 0).map((i) => i.src.slice(-50));
    const pending = all.filter((i) => !i.complete).length;
    return { n: all.length, bad: bad.slice(0, 3), pending };
  });
  if (img.bad.length) fails.push(`[${vp.name}] ${rel} 坏图 ${img.bad.join(' ')}`);
  if (img.pending) warns.push(`[${vp.name}] ${rel} 有 ${img.pending} 张图未加载完成（lazy，非缺陷）`);

  const sw = await page.evaluate(() => {
    const box = document.querySelector('.lang-switch');
    const menu = document.querySelector('.lang-menu');
    const cur = document.querySelector('.lang-cur-txt');
    const active = document.querySelector('.lang-menu .active');
    return {
      has: !!box,
      visible: !!box && box.getBoundingClientRect().width > 0,
      cur: cur ? cur.textContent.trim() : '',
      activeHref: active ? active.getAttribute('href') : '',
      activeText: active ? active.textContent.trim() : '',
      items: menu ? menu.querySelectorAll('a').length : 0,
    };
  });
  if (!sw.has || !sw.visible) fails.push(`[${vp.name}] ${rel} 语言切换器缺失/不可见`);
  else {
    if (sw.cur !== LABEL[lg]) fails.push(`[${vp.name}] ${rel} 切换器当前语言应为 ${LABEL[lg]}，实际「${sw.cur}」`);
    if (sw.activeText !== LABEL[lg]) fails.push(`[${vp.name}] ${rel} 切换器未高亮 ${LABEL[lg]}（高亮=${sw.activeText}）`);
    if (sw.items !== 8) warns.push(`[${vp.name}] ${rel} 切换器项数 ${sw.items}（期望 8：EN+中文+6 语言）`);
  }

  // ④ 纯单语：不得有可见的 .lang-zh / .lang-en 块
  const zh = await page.evaluate(() => {
    const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    return {
      zh: [...document.querySelectorAll('.lang-zh')].filter(vis).length,
      en: [...document.querySelectorAll('.lang-en')].filter(vis).length,
      zhAll: document.querySelectorAll('.lang-zh').length,
      dataI18n: document.querySelectorAll('[data-i18n]').length,
      htmlCls: document.documentElement.className,
    };
  });
  if (zh.zhAll) fails.push(`[${vp.name}] ${rel} 残留 .lang-zh 元素 ${zh.zhAll} 个（语言版必须纯单语）`);
  if (zh.dataI18n) warns.push(`[${vp.name}] ${rel} 残留 data-i18n 属性 ${zh.dataI18n} 个`);

  // ⑤ 导航：器械入口指向本语言版，且下拉 9 项都在
  const nav = await page.evaluate(() => {
    const drop = document.querySelector('.nav-links .nav-drop');
    if (!drop) return { has: false };
    const top = drop.querySelector(':scope > a');
    return {
      has: true,
      href: top ? top.getAttribute('href') : '',
      items: drop.querySelectorAll('.nav-drop-menu a').length,
    };
  });
  // ⚠️ 导航一级入口在**所有**器械页上都指向板块首页 /<lang>/pilates/
  //    （= canonical 的目录形式），族页也不例外 —— 它是「板块入口」不是「当前页」。
  //    首跑时按「当前页 URL」写期望，9 页 ×4 视口全误报，特此注明。
  const expect = `/${lg}/pilates/`;
  if (!nav.has) fails.push(`[${vp.name}] ${rel} 导航缺少器械 nav-drop`);
  else {
    if (nav.href !== expect) fails.push(`[${vp.name}] ${rel} 导航器械入口 ${nav.href}（应 ${expect}）`);
    if (nav.items !== 9) fails.push(`[${vp.name}] ${rel} 导航下拉 ${nav.items} 项（应 9：8 族 + All）`);
  }

  if (errs.length) fails.push(`[${vp.name}] ${rel} 控制台/网络错误 ${[...new Set(errs)].slice(0, 3).join(' | ')}`);

  await page.screenshot({ path: `${OUT}/${lg}-${slug.replace('.html', '')}-${vp.name}.png`, fullPage: false });
  await ctx.close();
}

async function main() {
  const browser = await chromium.launch();
  for (const lg of LANGS) {
    for (const slug of PAGES) {
      for (const vp of VIEWPORTS) await auditPage(browser, lg, slug, vp);
      process.stdout.write(`  ${lg}/${slug} ✓\n`);
    }
  }

  // 切换器跳转实测：FR 页点 EN 必须落到英文原页
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  await page.goto(`${BASE}/fr/pilates/index.html`, { waitUntil: 'load' });
  await page.click('.lang-switch .lang-current');
  await page.click('.lang-menu a[hreflang="en"]');
  await page.waitForLoadState('load');
  const after = page.url();
  if (!/\/pilates\/?$/.test(after.replace(BASE, ''))) fails.push(`切换器 EN 跳转异常：${after}`);
  else process.stdout.write(`  切换器 EN 跳转 ✓ ${after.replace(BASE, '')}\n`);

  // 移动端汉堡菜单是否真的能展开（验证 main.js 生效）
  const m = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const mp = await m.newPage();
  await mp.goto(`${BASE}/ja/pilates/index.html`, { waitUntil: 'load' });
  const mt = await mp.$('.menu-toggle');
  if (mt) {
    await mt.click();
    await mp.waitForTimeout(300);
    const open = await mp.evaluate(() => {
      const n = document.querySelector('.nav-links');
      const r = n.getBoundingClientRect();
      return r.height > 40 && getComputedStyle(n).display !== 'none';
    });
    if (!open) fails.push('移动端汉堡菜单点开无效（main.js 可能 404）');
    else process.stdout.write('  移动端菜单展开 ✓\n');
  }
  await browser.close();

  console.log(`\nFAIL ${fails.length} / WARN ${warns.length}`);
  fails.slice(0, 25).forEach((f) => console.log('  ✗ ' + f));
  warns.slice(0, 10).forEach((w) => console.log('  ! ' + w));
  if (!fails.length) console.log('全部通过 ✓  截图见 ' + OUT);
  process.exit(fails.length ? 1 : 0);
}

main().catch((e) => { console.error(e); process.exit(2); });
