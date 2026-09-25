// 英文站正文词数：静态抽取 vs 真实浏览器渲染，交叉验证
// 目的：确认 audit_en_seo_standard_20260925.py 的 C1 词数判据不是「静态抽少了」的误报
// 浏览器口径：移除 header/footer/nav/script/style 后取 body.innerText
//   → innerText 尊重 CSS，.lang-zh{display:none} 的中文块天然不计入，与静态剥块口径一致
// 用法：BASE=http://127.0.0.1:8848 node i18n_build/verify_en_wordcount_20260925.cjs
const { chromium } = require('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:8848';

const PAGES = [
  ['首页', '/index.html'],
  ['关于我们', '/about.html'],
  ['联系我们', '/contact.html'],
  ['一级分类', '/tpe-yoga-mats.html'],
  ['产品详情页', '/products/ab-wheel.html'],
  ['产品详情页', '/products/alignment-line-tpe-yoga-mat.html'],
  ['Blog文章', '/blog/tpe-vs-pu.html'],
  ['FAQ页', '/faq.html'],
  ['支持/知识页', '/materials.html'],
];

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1440, height: 900 } });
  console.log('页面类型'.padEnd(12), '路径'.padEnd(48), '渲染词数');
  console.log('-'.repeat(80));
  for (const [type, path] of PAGES) {
    await p.goto(BASE + path, { waitUntil: 'domcontentloaded', timeout: 30000 });
    const n = await p.evaluate(() => {
      document.querySelectorAll('header,footer,nav,script,style,svg').forEach(e => e.remove());
      const t = document.body.innerText || '';
      return t.split(/\s+/).filter(w => /[A-Za-z]/.test(w)).length;
    });
    console.log(type.padEnd(12), path.padEnd(48), String(n));
  }
  await b.close();
})();
