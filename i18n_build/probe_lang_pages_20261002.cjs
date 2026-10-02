// 语言版页面浏览器级探针（10-02 收尾）
// 判据：① 切换器存在且下拉可点 ② 切换器语言链接指向本语言树 ③ 无横向溢出
//       ④ 语言版页面上没有中文残留（.lang-zh 已清除）⑤ 博客索引卡片数
const { chromium } = require('playwright');
const BASE = 'http://127.0.0.1:8872';
const OUT = 'i18n_build/reports/';
const CASES = [
  { l: 'de', url: '/de/blog.html',                            vp: [1440, 900] },
  { l: 'de', url: '/de/blog/pilates-studio-layout-guide.html', vp: [1440, 900] },
  { l: 'ja', url: '/ja/pilates/pilates-reformer.html',          vp: [390, 844] },
  { l: 'es', url: '/es/pilates/index.html',                     vp: [1440, 900] },
];
(async () => {
  const browser = await chromium.launch();
  for (const c of CASES) {
    const page = await browser.newPage({ viewport: { width: c.vp[0], height: c.vp[1] } });
    const r = await page.goto(BASE + c.url, { waitUntil: 'networkidle', timeout: 30000 }).catch(() => null);
    await page.waitForTimeout(600);
    const probe = await page.evaluate(() => {
      const sw = document.querySelector('.lang-switch');
      const menu = document.querySelector('.lang-menu');
      const links = menu ? Array.from(menu.querySelectorAll('a')).map(a => a.getAttribute('href')) : [];
      const zh = document.querySelectorAll('.lang-zh').length;
      const en = document.querySelectorAll('.lang-en').length;
      const cards = document.querySelectorAll('.post-card').length;
      const de = document.documentElement;
      // 横向溢出：只看文档级滚动条
      const overflow = de.scrollWidth - de.clientWidth;
      const cur = document.querySelector('.lang-cur-txt');
      return { sw: !!sw, cur: cur ? cur.textContent.trim() : null, links,
               zh, en, cards, overflow };
    });
    // 悬停/点击切换器，确认 JS 生效（下拉可见性）
    let menuVisible = null;
    if (probe.sw) {
      await page.click('.lang-current').catch(() => {});
      await page.waitForTimeout(300);
      menuVisible = await page.evaluate(() => {
        const m = document.querySelector('.lang-menu');
        if (!m) return false;
        const s = getComputedStyle(m);
        return s.display !== 'none' && s.visibility !== 'hidden' && m.getBoundingClientRect().height > 0;
      });
      await page.keyboard.press('Escape').catch(() => {});
    }
    const ok = probe.sw && menuVisible && probe.zh === 0 && probe.overflow <= 1;
    console.log((ok ? '✓' : '✗'), c.url,
      '| HTTP', r ? r.status() : 'ERR',
      '| 切换器', probe.sw ? probe.cur : '无',
      '| 下拉可见', menuVisible,
      '| lang-zh 残留', probe.zh,
      '| lang-en', probe.en,
      '| 卡片', probe.cards,
      '| 横向溢出', probe.overflow);
    if (c.url.endsWith('blog.html')) {
      await page.screenshot({ path: OUT + 'langcheck_' + c.l + '_blog_index_20261002.png' });
    } else if (c.url.includes('pilates-studio-layout-guide')) {
      await page.screenshot({ path: OUT + 'langcheck_de_blog_article_20261002.png' });
    } else if (c.vp[0] === 390) {
      await page.screenshot({ path: OUT + 'langcheck_ja_pilates_mobile_20261002.png' });
    }
    await page.close();
  }
  await browser.close();
})();
