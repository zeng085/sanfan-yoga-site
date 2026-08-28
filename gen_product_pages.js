// Static product-page generator for SANFAN site
// Reads products-data.js (data) + main.js I18N (titles/descs), emits one static
// HTML file per product into products/<id>.html — crawlable, dual-language (EN/zh),
// with canonical + Open Graph + Product/BreadcrumbList JSON-LD.
const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const BASE = 'https://sanfan-yoga-site.vercel.app';
const WA = '8615959029082';

// ---- load product data ----
const pdSrc = fs.readFileSync(path.join(ROOT, 'assets/js/products-data.js'), 'utf8');
const products = new Function(
  'var SANFAN_PRODUCTS;' +
  pdSrc.replace('window.SANFAN_PRODUCTS', 'SANFAN_PRODUCTS') +
  ';return SANFAN_PRODUCTS;'
)();

// ---- extract I18N object from main.js (brace match) ----
const mainSrc = fs.readFileSync(path.join(ROOT, 'assets/js/main.js'), 'utf8');
const wi = mainSrc.indexOf('const I18N');
const start = mainSrc.indexOf('{', wi);
let depth = 0, end = -1, inS = false, q = '';
for (let i = start; i < mainSrc.length; i++) {
  const c = mainSrc[i];
  if (inS) {
    if (c === '\\') { i++; continue; }
    if (c === q) inS = false;
    continue;
  }
  if (c === "'" || c === '"') { inS = true; q = c; continue; }
  if (c === '{') depth++;
  else if (c === '}') { depth--; if (depth === 0) { end = i; break; } }
}
const I18N = eval('(' + mainSrc.slice(start, end + 1) + ')');

// ---- helpers ----
function esc(s) {
  return (s == null ? '' : String(s))
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
function T(id, lang) { return (I18N[lang] && I18N[lang][id] != null) ? I18N[lang][id] : ''; }

const SPEC_ORDER = ['material', 'size', 'thickness', 'moq', 'colors', 'cert', 'packing'];
const SPEC_LABEL = {
  en: { material: 'Material', size: 'Size', thickness: 'Thickness', moq: 'MOQ', colors: 'Colors & Print', cert: 'Compliance', packing: 'Packaging' },
  zh: { material: '材质', size: '尺寸', thickness: '厚度', moq: '起订量', colors: '颜色与印花', cert: '合规认证', packing: '包装' }
};
const CAT_TITLE = {
  en: { yoga: 'Yoga Mats', props: 'Yoga Props & Accessories', rollers: 'Foam Rollers & Massage', bands: 'Resistance Bands & Pilates', fit: 'Fitness Equipment' },
  zh: { yoga: '瑜伽垫', props: '瑜伽道具与配件', rollers: '瑜伽柱与按摩', bands: '弹力带与普拉提', fit: '健身器材' }
};
const APPLY = {
  en: {
    yoga: 'Ideal for yoga studios, gyms, hot-yoga classes, private-label retail and promotional giveaways.',
    props: 'Used in yoga studios, meditation rooms, rehab centers and boutique fitness retail.',
    rollers: 'Perfect for sports recovery, physiotherapy clinics, gym retail and home fitness.',
    bands: 'Great for pilates studios, rehab, home workouts and private-label fitness retail.',
    fit: 'Suited to home gyms, boutique fitness brands, corporate wellness and e-commerce.'
  },
  zh: {
    yoga: '适用于瑜伽馆、健身房、高温瑜伽课程、贴牌零售与赠品促销。',
    props: '用于瑜伽馆、冥想室、康复中心与精品健身零售。',
    rollers: '适用于运动恢复、理疗诊所、健身房零售与居家健身。',
    bands: '适用于普拉提馆、康复训练、居家锻炼与贴牌健身零售。',
    fit: '适用于居家健身房、精品健身品牌、企业健康与电商。'
  }
};
const CUSTOM_BULLETS = {
  en: [
    ['Custom logo printing', 'Silk-screen, heat transfer or laser engraving on mat or packaging.'],
    ['Size & thickness', 'Made to your spec — length, width and thickness all adjustable.'],
    ['Color & material', 'Pantone color matching with TPE, PU/rubber or EVA options.'],
    ['Packaging', 'Custom inner box, carton, barcode and hang-tag for retail-ready shipping.']
  ],
  zh: [
    ['定制 logo 印刷', '丝印、热转印或激光雕刻，可用于垫面或包装。'],
    ['尺寸与厚度', '按你的规格定制——长度、宽度、厚度均可调。'],
    ['颜色与材质', '潘通色卡配色，可选 TPE、PU/橡胶或 EVA 材质。'],
    ['包装', '定制内盒、外箱、条码与吊牌，达成零售级出货。']
  ]
};

function langBlocks(en, zh) {
  return '<span class="lang-en">' + esc(en) + '</span><span class="lang-zh">' + esc(zh) + '</span>';
}

function buildPage(id) {
  const p = products[id];
  const cat = p.cat;
  const enTitle = T(id + '.t', 'en') || (p.en && p.en.title) || id;
  const zhTitle = T(id + '.t', 'zh') || enTitle;
  const enDesc = T(id + '.d', 'en') || '';
  const zhDesc = T(id + '.d', 'zh') || enDesc;
  const enOverview = p.en && p.en.overview || '';
  const zhOverview = p.zh && p.zh.overview || '';
  const enFeatures = (p.en && p.en.features) || [];
  const zhFeatures = (p.zh && p.zh.features) || [];
  const catEn = CAT_TITLE.en[cat], catZh = CAT_TITLE.zh[cat];
  const imgRel = p.img;
  const imgAbs = imgRel.indexOf('http') === 0 ? imgRel : BASE + '/' + imgRel;
  const gallery = (p.gallery && p.gallery.length) ? p.gallery : [p.img];
  const galleryAbs = gallery.map(s => s.indexOf('http') === 0 ? s : BASE + '/' + s);
  const url = BASE + '/products/' + id + '.html';
  const waTextEn = 'Hi SANFAN, I am interested in ' + enTitle;
  const waTextZh = '你好三梵，我想了解 ' + zhTitle;
  const waEn = 'https://wa.me/' + WA + '?text=' + encodeURIComponent(waTextEn);
  const waZh = 'https://wa.me/' + WA + '?text=' + encodeURIComponent(waTextZh);

  // specs rows (dual language labels, neutral values)
  let specRows = '';
  SPEC_ORDER.forEach(k => {
    const v = p.specs && p.specs[k];
    if (!v) return;
    specRows += '<tr><th>' + langBlocks(SPEC_LABEL.en[k], SPEC_LABEL.zh[k]) + '</th><td>' + esc(v) + '</td></tr>';
  });

  // features (dual blocks)
  let featEn = '', featZh = '';
  const n = Math.max(enFeatures.length, zhFeatures.length);
  for (let i = 0; i < n; i++) {
    featEn += '<li>' + esc(enFeatures[i] || zhFeatures[i] || '') + '</li>';
    featZh += '<li>' + esc(zhFeatures[i] || enFeatures[i] || '') + '</li>';
  }

  // related (same cat, exclude self, max 4) — cards are direct grid children,
  // each card carries EN/ZH text via dual spans so the grid layout stays intact.
  const related = Object.keys(products)
    .filter(k => products[k].cat === cat && k !== id).slice(0, 4);
  let relCards = '';
  related.forEach(k => {
    const rp = products[k];
    const rt = T(k + '.t', 'en') || (rp.en && rp.en.title) || k;
    const rz = T(k + '.t', 'zh') || rt;
    const rd = T(k + '.d', 'en') || '';
    const rdz = T(k + '.d', 'zh') || rd;
    const rimg = rp.img;
    relCards += '<a class="prod-card" href="../products/' + k + '.html"><div class="ph"><img src="../' + esc(rimg) + '" alt="' + esc(rt) + '"></div><div class="info"><h4>' + langBlocks(rt, rz) + '</h4><p>' + langBlocks(rd, rdz) + '</p></div></a>';
  });

  // customization bullets
  let cbEn = '', cbZh = '';
  CUSTOM_BULLETS.en.forEach((b, i) => {
    cbEn += '<li><strong>' + esc(b[0]) + '</strong> — ' + esc(b[1]) + '</li>';
    cbZh += '<li><strong>' + esc(CUSTOM_BULLETS.zh[i][0]) + '</strong> — ' + esc(CUSTOM_BULLETS.zh[i][1]) + '</li>';
  });

  // JSON-LD
  const jsonLd = {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'Product',
        name: enTitle,
        description: enDesc,
        image: galleryAbs,
        brand: { '@type': 'Brand', name: 'SANFAN' },
        category: catEn,
        url: url,
        offers: { '@type': 'Offer', priceCurrency: 'USD', availability: 'https://schema.org/InStock', url: url }
      },
      {
        '@type': 'BreadcrumbList',
        itemListElement: [
          { '@type': 'ListItem', position: 1, name: 'Home', item: BASE + '/index.html' },
          { '@type': 'ListItem', position: 2, name: 'Products', item: BASE + '/products.html' },
          { '@type': 'ListItem', position: 3, name: catEn, item: BASE + '/products.html#' + cat },
          { '@type': 'ListItem', position: 4, name: enTitle, item: url }
        ]
      }
    ]
  };
  const jsonLdStr = JSON.stringify(jsonLd, null, 2);

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${esc(enTitle)} — SANFAN Yoga & Fitness Manufacturer</title>
  <meta name="description" content="${esc(enDesc)}" />
  <link rel="canonical" href="${url}" />
  <link rel="alternate" hreflang="en" href="${url}" />
  <link rel="alternate" hreflang="zh" href="${url}" />
  <link rel="alternate" hreflang="x-default" href="${url}" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="${esc(enTitle)} — SANFAN" />
  <meta property="og:description" content="${esc(enDesc)}" />
  <meta property="og:image" content="${esc(imgAbs)}" />
  <meta property="og:url" content="${url}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="${esc(enTitle)} — SANFAN" />
  <meta name="twitter:description" content="${esc(enDesc)}" />
  <meta name="twitter:image" content="${esc(imgAbs)}" />
  <link rel="stylesheet" href="../assets/css/styles.css" />
  <link rel="icon" href="../assets/img/logo.jpg" />
  <script type="application/ld+json">${jsonLdStr}</script>
</head>
<body>

  <header class="site-header">
    <div class="container nav">
      <a href="../index.html" class="nav-brand"><img src="../assets/img/logo.jpg" alt="SANFAN" /><span>SAN<span class="accent">FAN</span></span></a>
      <nav class="nav-links">
        <a href="../index.html" data-i18n="nav.home">Home</a>
        <a href="../products.html" data-i18n="nav.products">Products</a>
        <a href="../about.html" data-i18n="nav.about">About</a>
        <a href="../faq.html" data-i18n="nav.faq">FAQ</a>
        <a href="../blog.html" data-i18n="nav.blog">Blog</a>
        <a href="../contact.html" data-i18n="nav.contact">Contact</a>
      </nav>
      <div class="nav-actions">
        <button class="lang-btn" type="button">中文</button>
        <a href="../contact.html" class="btn btn-primary" data-i18n="nav.quote">Get a Quote</a>
      </div>
      <button class="menu-toggle" aria-label="menu">☰</button>
    </div>
  </header>

  <section class="hero" style="background:linear-gradient(120deg,var(--brand-ink),var(--brand));">
    <div class="container hero-inner" style="padding:52px 0 30px;">
      <nav class="breadcrumb">
        <a href="../products.html" data-i18n="pd.back">Back to Products</a>
        <span class="bc-sep">/</span>
        <span class="bc-cat">${langBlocks(catEn, catZh)}</span>
      </nav>
      <h1>${langBlocks(esc(enTitle) + ' — SANFAN', esc(zhTitle) + ' — 三梵')}</h1>
    </div>
  </section>

  <section class="section">
    <div class="container product-detail">
      <div class="pd-gallery">
        <div class="pd-main"><img id="pd-main-img" src="../${esc(gallery[0])}" alt="${esc(enTitle)}" /></div>
        <div class="pd-thumbs" id="pd-thumbs">
${gallery.map((s, i) => '          <button type="button" class="pd-thumb' + (i === 0 ? ' active' : '') + '"><img src="../' + esc(s) + '" alt="' + esc(enTitle) + '"></button>').join('\n')}
        </div>
      </div>
      <div class="pd-info">
        <p class="pd-desc">${langBlocks(esc(enDesc), esc(zhDesc))}</p>
        <div class="pd-actions">
          <a class="btn btn-primary" href="../contact.html" data-i18n="pd.quote">Request a Quote</a>
          <a class="btn btn-ghost" id="pd-wa-en" href="${waEn}" data-i18n="pd.whatsapp">Chat on WhatsApp</a>
        </div>
        <div class="pd-specs">
          <h3 data-i18n="pd.specs">Specifications</h3>
          <table class="spec-table"><tbody>${specRows}</tbody></table>
        </div>
      </div>
    </div>
  </section>

  <section class="section soft">
    <div class="container">
      <div class="section-head">
        <div class="eyebrow" data-i18n="pd.overview">Product Overview</div>
        <h2>${langBlocks(esc(enTitle), esc(zhTitle))}</h2>
      </div>
      <p class="pd-overview">${langBlocks(esc(enOverview), esc(zhOverview))}</p>
      <div class="pd-lang-cols">
        <div class="lang-en"><h3 class="pd-features-title" data-i18n="pd.features">Key Features</h3><ul class="pd-features">${featEn}</ul></div>
        <div class="lang-zh"><h3 class="pd-features-title">核心特点</h3><ul class="pd-features">${featZh}</ul></div>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="container">
      <div class="section-head">
        <div class="eyebrow" data-i18n="pd.brand">Branding</div>
        <h2 data-i18n="pd.custom">Customization &amp; OEM/ODM</h2>
      </div>
      <p class="pd-custom">${langBlocks(esc(T('pd.custom.d', 'en')), esc(T('pd.custom.d', 'zh')))}</p>
      <div class="pd-lang-cols">
        <div class="lang-en"><ul class="pd-custom-list">${cbEn}</ul></div>
        <div class="lang-zh"><ul class="pd-custom-list">${cbZh}</ul></div>
      </div>
    </div>
  </section>

  <section class="section soft">
    <div class="container">
      <div class="section-head">
        <div class="eyebrow" data-i18n="pd.apply">Applications</div>
        <h2 data-i18n="pd.apply.t">Where It Is Used</h2>
      </div>
      <p class="pd-overview">${langBlocks(esc(APPLY.en[cat]), esc(APPLY.zh[cat]))}</p>
    </div>
  </section>

  <section class="section soft">
    <div class="container">
      <div class="section-head">
        <h2 data-i18n="pd.related">Related Products</h2>
      </div>
      <div class="prod-grid">${relCards}</div>
    </div>
  </section>

  <section class="section">
    <div class="container">
      <div class="cta-band">
        <h2 data-i18n="cta.title">Ready to Build Your Brand?</h2>
        <p data-i18n="cta.sub">Get a tailored quote and free samples today.</p>
        <a href="../contact.html" class="btn btn-light" data-i18n="cta.btn">Contact Our Team</a>
      </div>
    </div>
  </section>

  <footer class="site-footer">
    <div class="container footer-grid">
      <div>
        <div class="brand"><img src="../assets/img/logo.jpg" alt="SANFAN" /> <span>SAN<span style="color:var(--brand-2)">FAN</span></span></div>
        <p style="font-size:14px;max-width:300px" data-i18n="f.tag">OEM / ODM yoga &amp; fitness manufacturer.</p>
      </div>
      <div><h5 data-i18n="foot.products">Products</h5><ul>
        <li><a href="../products.html#yoga" data-i18n="cat.yoga.title">Yoga Mats</a></li>
        <li><a href="../products.html#props" data-i18n="cat.props.title">Yoga Props &amp; Accessories</a></li>
        <li><a href="../products.html#rollers" data-i18n="cat.rollers.title">Foam Rollers &amp; Massage</a></li>
        <li><a href="../products.html#bands" data-i18n="cat.bands.title">Resistance Bands &amp; Pilates</a></li>
        <li><a href="../products.html#fitness" data-i18n="cat.fit.title">Fitness Equipment</a></li>
      </ul></div>
      <div><h5 data-i18n="foot.company">Company</h5><ul>
        <li><a href="../about.html" data-i18n="nav.about">About</a></li>
        <li><a href="../about.html" data-i18n="process.title">Production Process</a></li>
        <li><a href="../contact.html" data-i18n="nav.contact">Contact</a></li>
      </ul></div>
      <div><h5 data-i18n="foot.contact">Contact</h5>
        <div class="contact-line"><span data-i18n="foot.addr">Address</span>: No. 8 Haiguang Road, Yuejin Industrial Zone, Xibin Town, Jinjiang, Quanzhou, Fujian, China</div>
        <div class="contact-line"><span data-i18n="foot.email">Email</span>: zenglinggun@gmail.com</div>
        <div class="contact-line"><span data-i18n="foot.phone">WhatsApp</span>: +86 15959029082</div>
      </div>
    </div>
    <div class="container footer-bottom" data-i18n="foot.copyright">© 2026 FUJIAN SANFAN Sports Products Co., Ltd. All rights reserved.</div>
  </footer>

  <script src="../assets/js/main.js"></script>
  <script>
    (function () {
      var thumbs = document.getElementById('pd-thumbs');
      var main = document.getElementById('pd-main-img');
      if (thumbs && main) {
        thumbs.addEventListener('click', function (e) {
          var btn = e.target.closest('.pd-thumb');
          if (!btn) return;
          var img = btn.querySelector('img');
          main.src = img.getAttribute('src');
          main.alt = img.getAttribute('alt');
          thumbs.querySelectorAll('.pd-thumb').forEach(function (x) { x.classList.remove('active'); });
          btn.classList.add('active');
        });
      }
      // keep WhatsApp link in sync with the active language
      function syncWa() {
        var zh = document.documentElement.classList.contains('show-zh');
        var a = document.getElementById('pd-wa-en');
        if (a) a.href = zh ? ${JSON.stringify(waZh)} : ${JSON.stringify(waEn)};
      }
      syncWa();
      document.addEventListener('sanfan-langchange', syncWa);
    })();
  </script>
</body>
</html>
`;
  return html;
}

// ---- emit ----
const outDir = path.join(ROOT, 'products');
if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
const ids = Object.keys(products);
ids.forEach(id => {
  const html = buildPage(id);
  fs.writeFileSync(path.join(outDir, id + '.html'), html, 'utf8');
});
console.log('Generated', ids.length, 'static product pages:', ids.join(', '));
