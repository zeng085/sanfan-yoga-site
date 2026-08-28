// Product detail page renderer
(function () {
  const PRODUCTS = window.SANFAN_PRODUCTS || {};
  const I18N = window.I18N || {};
  const WA_NUMBER = '8615959029082';

  function getLang() {
    return document.documentElement.lang && document.documentElement.lang.startsWith('zh') ? 'zh' : 'en';
  }
  function t(key) {
    const l = getLang();
    return (I18N[l] && I18N[l][key] != null) ? I18N[l][key] : (key || '');
  }
  function esc(s) {
    return (s == null) ? '' : String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  }

  const SPEC_ORDER = ['material', 'size', 'thickness', 'moq', 'colors', 'cert', 'packing'];
  const SPEC_KEY = { material: 'pd.material', size: 'pd.size', thickness: 'pd.thickness', moq: 'pd.moq', colors: 'pd.colors', cert: 'pd.cert', packing: 'pd.packing' };

  function getId() {
    const p = new URLSearchParams(location.search).get('id');
    return p || '';
  }

  function notFound() {
    document.getElementById('pd-breadcrumb').textContent = '—';
    document.getElementById('pd-title').textContent = t('pd.notfound');
    document.querySelector('.product-detail').innerHTML =
      '<div class="pd-notfound"><p>' + esc(t('pd.notfound.d')) + '</p>' +
      '<a class="btn btn-primary" href="products.html">' + esc(t('pd.back')) + '</a></div>';
    const ov = document.getElementById('pd-overview');
    if (ov) ov.closest('.section').style.display = 'none';
  }

  function render() {
    const id = getId();
    const p = PRODUCTS[id];
    if (!p) { notFound(); return; }

    const lang = getLang();
    const title = t(id + '.t') || (p[lang] && p[lang].title) || id;
    const desc = t(id + '.d') || '';

    document.title = title + ' — SANFAN';

    // SEO: 按产品动态更新 canonical + Open Graph / Twitter Card
    (function updateSeoMeta() {
      var canon = location.origin + '/product.html?id=' + encodeURIComponent(id);
      var imgAbs = p.img ? (p.img.indexOf('http') === 0 ? p.img : location.origin + '/' + p.img) : '';
      function setMeta(selector, attr, val) {
        var el = document.head.querySelector(selector);
        if (el) el.setAttribute(attr, val);
      }
      setMeta('link[rel="canonical"]', 'href', canon);
      setMeta('meta[property="og:url"]', 'content', canon);
      setMeta('meta[property="og:title"]', 'content', title + ' — SANFAN');
      setMeta('meta[name="twitter:title"]', 'content', title + ' — SANFAN');
      setMeta('meta[property="og:description"]', 'content', desc);
      setMeta('meta[name="twitter:description"]', 'content', desc);
      if (imgAbs) {
        setMeta('meta[property="og:image"]', 'content', imgAbs);
        setMeta('meta[name="twitter:image"]', 'content', imgAbs);
      }
    })();

    document.getElementById('pd-title').textContent = title;
    document.getElementById('pd-desc').textContent = desc;
    document.getElementById('pd-breadcrumb').textContent = t('cat.' + p.cat + '.title') || '';

    // Overview section title (reuse product title)
    document.getElementById('pd-overview-title').textContent = title;
    document.getElementById('pd-overview').textContent = (p[lang] && p[lang].overview) || '';

    // Gallery
    const mainImg = document.getElementById('pd-main-img');
    const thumbs = document.getElementById('pd-thumbs');
    const gallery = (p.gallery && p.gallery.length) ? p.gallery : [p.img];
    mainImg.src = gallery[0];
    mainImg.alt = title;
    thumbs.innerHTML = '';
    gallery.forEach((src, i) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'pd-thumb' + (i === 0 ? ' active' : '');
      b.innerHTML = '<img src="' + esc(src) + '" alt="' + esc(title) + '">';
      b.addEventListener('click', () => {
        mainImg.src = src;
        thumbs.querySelectorAll('.pd-thumb').forEach(x => x.classList.remove('active'));
        b.classList.add('active');
      });
      thumbs.appendChild(b);
    });

    // Specs
    const body = document.getElementById('pd-specs-body');
    body.innerHTML = '';
    SPEC_ORDER.forEach(k => {
      const v = p.specs && p.specs[k];
      if (!v) return;
      const tr = document.createElement('tr');
      tr.innerHTML = '<th>' + esc(t(SPEC_KEY[k])) + '</th><td>' + esc(v) + '</td>';
      body.appendChild(tr);
    });

    // Features
    const ul = document.getElementById('pd-features');
    ul.innerHTML = '';
    const feats = (p[lang] && p[lang].features) || [];
    feats.forEach(f => {
      const li = document.createElement('li');
      li.textContent = f;
      ul.appendChild(li);
    });

    // WhatsApp link
    const wa = document.getElementById('pd-wa');
    const text = (lang === 'zh' ? '你好三梵，我想了解 ' : 'Hi SANFAN, I am interested in ') + title;
    wa.href = 'https://wa.me/' + WA_NUMBER + '?text=' + encodeURIComponent(text);

    // Related products (same category, exclude current)
    const related = document.getElementById('pd-related');
    related.innerHTML = '';
    Object.keys(PRODUCTS)
      .filter(k => PRODUCTS[k].cat === p.cat && k !== id)
      .slice(0, 4)
      .forEach(k => {
        const rp = PRODUCTS[k];
        const a = document.createElement('a');
        a.className = 'prod-card';
        a.href = 'product.html?id=' + k;
        const rtitle = t(k + '.t') || '';
        a.innerHTML = '<div class="ph"><img src="' + esc(rp.img) + '" alt="' + esc(rtitle) + '"></div>' +
          '<div class="info"><h4>' + esc(rtitle) + '</h4><p>' + esc(t(k + '.d') || '') + '</p></div>';
        related.appendChild(a);
      });
  }

  // Redirect legacy ?id= URLs to the static, crawlable product page.
  (function redirectToStatic() {
    var id = getId();
    if (id && PRODUCTS[id]) {
      window.location.replace('products/' + encodeURIComponent(id) + '.html');
    }
  })();

  document.addEventListener('DOMContentLoaded', render);
  window.addEventListener('sanfan-langchange', render);
})();
