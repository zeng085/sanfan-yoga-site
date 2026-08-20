// ---------- Mobile nav ----------
const toggle = document.querySelector('.menu-toggle');
const links = document.querySelector('.nav-links');
if (toggle && links) {
  toggle.addEventListener('click', () => links.classList.toggle('open'));
  links.querySelectorAll('a').forEach(a => a.addEventListener('click', () => links.classList.remove('open')));
}

// ---------- Bilingual (EN / 中文) ----------
const I18N = {
  en: {
    'nav.home': 'Home', 'nav.products': 'Products', 'nav.about': 'About',
    'nav.contact': 'Contact', 'nav.quote': 'Get a Quote',
    'hero.eyebrow': 'TPE Yoga Mat & Foam Roller Source Factory',
    'hero.title': 'Direct from the Factory. Built for Your Brand.',
    'hero.lead': '12 years of OEM/ODM expertise. 100 pcs MOQ, 7-day sampling, full customization. We help yoga brands, retailers and studios launch faster.',
    'hero.cta1': 'Request a Quote', 'hero.cta2': 'View Products',
    'hero.stat1.n': '12+', 'hero.stat1.l': 'Years Manufacturing',
    'hero.stat2.n': '100', 'hero.stat2.l': 'Pcs Min. Order',
    'hero.stat3.n': '7', 'hero.stat3.l': 'Day Sampling',
    'hero.media': 'Factory / Product photo placeholder',
    'str.title': 'Why Buyers Choose Us',
    'str.sub': 'A flexible supply chain engineered for private-label success.',
    'str1.t': 'Low MOQ', 'str1.d': 'Start from 100 pcs. Test the market without heavy inventory risk.',
    'str2.t': 'Fast Sampling', 'str2.d': 'Physical samples in 7 days with your logo and color options.',
    'str3.t': 'Full Customization', 'str3.d': 'Material, size, color, double-color, packaging — all made to spec.',
    'str4.t': 'Certified Quality', 'str4.d': 'REACH, CA Prop 65, 6P/7P compliance for global markets.',
    'prod.title': 'Our Products',
    'prod.sub': 'TPE yoga mats and foam rollers, ready for private label.',
    'prod1.t': 'TPE Yoga Mat', 'prod1.d': 'Eco-friendly, non-slip, double-color options. Perfect for premium brands.',
    'prod2.t': 'Yoga Foam Roller', 'prod2.d': 'High-density EVA, smooth or textured. Ideal for recovery and studios.',
    'prod3.t': 'Alignment Yoga Mat', 'prod3.d': 'Printed guide lines to help users practice with correct posture.',
    'prod.spec.moq': 'MOQ', 'prod.spec.lead': 'Sampling', 'prod.spec.cert': 'Cert.', 'prod.spec.oem': 'OEM',
    'proc.title': 'How It Works',
    'proc.sub': 'From inquiry to delivery in four clear steps.',
    'proc1.t': 'Send Inquiry', 'proc1.d': 'Tell us your specs, quantity and target market.',
    'proc2.t': 'Sample & Quote', 'proc2.d': 'We send a quote and a physical sample within 7 days.',
    'proc3.t': 'Production', 'proc3.d': 'Confirm order, we manufacture and QC every batch.',
    'proc4.t': 'Ship & Support', 'proc4.d': 'Global shipping and ongoing reorder support.',
    'cta.title': 'Ready to Build Your Brand?',
    'cta.sub': 'Get a tailored quote and free samples today.',
    'cta.btn': 'Contact Our Team',
    'about.title': 'About SANFAN',
    'about.sub': 'A yoga equipment source factory trusted by brands worldwide.',
    'contact.title': 'Get in Touch',
    'contact.sub': 'Tell us what you need — we reply within 1 business day.',
    'f.home': 'Home', 'f.products': 'Products', 'f.about': 'About', 'f.contact': 'Contact',
    'f.brand': 'SANFAN Yoga', 'f.tag': 'TPE yoga mat & foam roller source factory.',
    'foot.products': 'Products', 'foot.company': 'Company', 'foot.contact': 'Contact',
    'foot.addr': 'Address', 'foot.email': 'Email', 'foot.phone': 'WhatsApp',
    'form.name': 'Your Name', 'form.company': 'Company', 'form.email': 'Email',
    'form.product': 'Product of Interest', 'form.qty': 'Estimated Quantity',
    'form.msg': 'Message', 'form.send': 'Send Inquiry', 'form.note': 'We never share your information.',
    'form.ok': 'Thanks! Your inquiry has been sent. We will reply within 1 business day.',
    'form.fail': 'Something went wrong. Please email us directly.',
  },
  zh: {
    'nav.home': '首页', 'nav.products': '产品', 'nav.about': '关于',
    'nav.contact': '联系', 'nav.quote': '获取报价',
    'hero.eyebrow': 'TPE 瑜伽垫 / 瑜伽柱 源头工厂',
    'hero.title': '工厂直供，为你的品牌而生。',
    'hero.lead': '12 年 OEM/ODM 经验。100 片起订、7 天打样、全面定制。我们帮瑜伽品牌、零售商与场馆更快上市。',
    'hero.cta1': '立即询价', 'hero.cta2': '查看产品',
    'hero.stat1.n': '12+', 'hero.stat1.l': '年制造经验',
    'hero.stat2.n': '100', 'hero.stat2.l': '片起订',
    'hero.stat3.n': '7', 'hero.stat3.l': '天打样',
    'hero.media': '工厂 / 产品图占位',
    'str.title': '为什么选择我们',
    'str.sub': '为贴牌成功而生的柔性供应链。',
    'str1.t': '低起订量', 'str1.d': '100 片起订，小批量试水无库存压力。',
    'str2.t': '快速打样', 'str2.d': '7 天出实物样，支持你的品牌 logo 与配色。',
    'str3.t': '全面定制', 'str3.d': '材质、尺寸、颜色、双色、包装，全部按需定制。',
    'str4.t': '认证品质', 'str4.d': '符合 REACH、CA Prop 65、6P/7P 等国际市场要求。',
    'prod.title': '我们的产品',
    'prod.sub': 'TPE 瑜伽垫与瑜伽柱，支持贴牌定制。',
    'prod1.t': 'TPE 瑜伽垫', 'prod1.d': '环保防滑，支持双色。适合高端品牌。',
    'prod2.t': '瑜伽柱', 'prod2.d': '高密度 EVA，光面或浮点。适合康复与场馆。',
    'prod3.t': '正位瑜伽垫', 'prod3.d': '印刷引导线，帮助用户正确练习体式。',
    'prod.spec.moq': '起订量', 'prod.spec.lead': '打样', 'prod.spec.cert': '认证', 'prod.spec.oem': '贴牌',
    'proc.title': '合作流程',
    'proc.sub': '四步清晰，从询盘到交付。',
    'proc1.t': '提交询盘', 'proc1.d': '告知规格、数量与目标市场。',
    'proc2.t': '打样报价', 'proc2.d': '7 天内寄出报价与实物样品。',
    'proc3.t': '生产', 'proc3.d': '确认订单后生产，每批严格质检。',
    'proc4.t': '发货支持', 'proc4.d': '全球发货，长期复购支持。',
    'cta.title': '准备好打造你的品牌了吗？',
    'cta.sub': '立即获取专属报价与免费样品。',
    'cta.btn': '联系我们',
    'about.title': '关于 三梵',
    'about.sub': '全球品牌信赖的瑜伽器材源头工厂。',
    'contact.title': '联系我们',
    'contact.sub': '告诉我们你的需求，1 个工作日内回复。',
    'f.home': '首页', 'f.products': '产品', 'f.about': '关于', 'f.contact': '联系',
    'f.brand': '三梵瑜伽', 'f.tag': 'TPE 瑜伽垫 / 瑜伽柱 源头工厂。',
    'foot.products': '产品', 'foot.company': '公司', 'foot.contact': '联系',
    'foot.addr': '地址', 'foot.email': '邮箱', 'foot.phone': 'WhatsApp',
    'form.name': '姓名', 'form.company': '公司', 'form.email': '邮箱',
    'form.product': '意向产品', 'form.qty': '预估数量',
    'form.msg': '留言', 'form.send': '发送询盘', 'form.note': '我们绝不会泄露你的信息。',
    'form.ok': '已收到！我们将在 1 个工作日内回复。',
    'form.fail': '发送失败，请直接邮件联系我们。',
  }
};

function applyLang(lang) {
  document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (I18N[lang][key] != null) el.textContent = I18N[lang][key];
  });
  document.querySelectorAll('[data-i18n-ph]').forEach(el => {
    const key = el.getAttribute('data-i18n-ph');
    if (I18N[lang][key] != null) el.setAttribute('placeholder', I18N[lang][key]);
  });
  const btn = document.querySelector('.lang-btn');
  if (btn) btn.textContent = lang === 'zh' ? 'EN' : '中文';
  try { localStorage.setItem('siteLang', lang); } catch (e) {}
}

const langBtn = document.querySelector('.lang-btn');
if (langBtn) {
  langBtn.addEventListener('click', () => {
    const cur = document.documentElement.lang.startsWith('zh') ? 'zh' : 'en';
    applyLang(cur === 'zh' ? 'en' : 'zh');
  });
}
const saved = (function () { try { return localStorage.getItem('siteLang'); } catch (e) { return null; } })();
applyLang(saved === 'zh' ? 'zh' : 'en');

// ---------- Inquiry form (Formspree) ----------
const form = document.getElementById('inquiry-form');
if (form) {
  const okBox = document.getElementById('form-ok');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = new FormData(form);
    const endpoint = form.getAttribute('action');
    try {
      const res = await fetch(endpoint, { method: 'POST', body: data, headers: { Accept: 'application/json' } });
      if (res.ok) {
        form.reset();
        okBox.style.display = 'block';
        okBox.textContent = I18N[document.documentElement.lang.startsWith('zh') ? 'zh' : 'en']['form.ok'];
        okBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
      } else {
        throw new Error('bad');
      }
    } catch (err) {
      const fail = I18N[document.documentElement.lang.startsWith('zh') ? 'zh' : 'en']['form.fail'];
      okBox.style.display = 'block';
      okBox.style.background = '#fdecec';
      okBox.style.color = '#a32d2d';
      okBox.style.borderColor = '#f3b5b5';
      okBox.textContent = fail;
    }
  });
}
