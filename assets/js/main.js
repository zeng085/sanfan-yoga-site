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
    'hero.eyebrow': 'TPE / NBR Yoga Mats & Foam Rollers — OEM Factory',
    'hero.title': 'Direct from Jinjiang, China. Built for Your Brand.',
    'hero.lead': 'Fujian Sanfan Sports Goods Industrial Co., Ltd. — 12 years manufacturing TPE mats, alignment mats, NBR mats and foam rollers. MOQ from 100 pcs (TPE) / 500 pcs (rollers) / 1,000 pcs (NBR). 7-day sampling.',
    'hero.cta1': 'Request a Quote', 'hero.cta2': 'View Products',
    'hero.stat1.n': '12+', 'hero.stat1.l': 'Years Manufacturing',
    'hero.stat2.n': '100', 'hero.stat2.l': 'Pcs Min. Order',
    'hero.stat3.n': '7', 'hero.stat3.l': 'Day Sampling',
    'hero.media': 'Factory / Product photo placeholder',
    'str.title': 'Why Buyers Choose Us',
    'str.sub': 'A flexible supply chain engineered for private-label success.',
    'str1.t': 'Low MOQ', 'str1.d': 'TPE mats from 100 pcs; foam rollers from 500 pcs; NBR mats from 1,000 pcs. Test without heavy inventory risk.',
    'str2.t': 'Fast Sampling', 'str2.d': 'Physical samples in 7 days with your logo, color and packaging options.',
    'str3.t': 'Full Customization', 'str3.d': 'Material, size, thickness, color, double-color, logo, fold and packaging — all made to spec.',
    'str4.t': 'Certified Quality', 'str4.d': 'REACH, CA Prop 65, 6P/7P compliance for global markets.',
    'prod.title': 'Our Products',
    'prod.sub': 'TPE/NBR yoga mats, alignment mats and foam rollers, ready for private label.',
    'prod1.t': 'TPE Yoga Mat', 'prod1.d': 'Eco-friendly double-layer TPE, non-slip textured surface, 61-122 cm widths, 4-12 mm thickness. Solid, economy and special grades available.',
    'prod2.t': 'Alignment Yoga Mat', 'prod2.d': 'Lotus-printed guide lines for correct posture. TPE base, 61/80 cm widths, matching strap and mesh bag sets.',
    'prod3.t': 'NBR Yoga Mat', 'prod3.d': 'High-elastic matte anti-slip NBR rubber. Best-seller 183×61×1 cm; thickness 0.8-2 cm; wide versions 80/90 cm.',
    'prod3.thumb': 'NBR Yoga Mat',
    'prod4.t': 'Yoga Foam Roller', 'prod4.d': 'PVC/PP core, 50° hardness, smooth or textured surfaces including wolf-tooth, moon, corrugated and diamond patterns.',
    'prod4.thumb': 'Yoga Foam Roller',
    'prod.spec.moq': 'MOQ', 'prod.spec.lead': 'Sampling', 'prod.spec.cert': 'Cert.', 'prod.spec.oem': 'OEM',
    'spec.title': 'Specification Overview',
    'spec.sub': 'Popular sizes and MOQs at a glance. Custom sizes, colors and packaging available on request.',
    'spec1.t': 'TPE Yoga Mat',
    'spec1.d': '1830×610 / 1830×800 / 1850×900 / 2000×1000 / 1850×1220 mm\nThickness 4-12 mm\nMOQ 100 pcs',
    'spec2.t': 'Alignment Yoga Mat',
    'spec2.d': '61 cm / 80 cm widths\nLotus + centerline guides\nMOQ 100 pcs',
    'spec3.t': 'NBR Yoga Mat',
    'spec3.d': '183×61×0.8-2 cm\n185×80×1 / 185×90×1 cm\nMOQ 1,000 pcs (regular colors)',
    'spec4.t': 'Yoga Foam Roller',
    'spec4.d': '25×7.5 to 45×14 cm\nSmooth / wolf-tooth / moon / corrugated / diamond\nMOQ 500 pcs',
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
    'about.h1': 'Fujian Sanfan Sports Goods Industrial Co., Ltd.',
    'about.p1': 'Founded in Jinjiang, Quanzhou — the heart of China\'s sporting-goods manufacturing belt — SANFAN has spent 12 years building yoga mats and rollers for brands, retailers and studios around the world.',
    'about.p2': 'We specialize in TPE yoga mats, alignment mats, NBR yoga mats and foam rollers. Our flexible supply chain supports small test orders, fast 7-day sampling and full private-label customization including material, size, color, double-color finish, logo, fold and packaging.',
    'about.p3': 'Whether you are a yoga brand looking for a reliable OEM partner, a retailer building your own line, or a studio chain that needs consistent quality at scale, we ship from our Fujian factory to your warehouse.',
    'contact.title': 'Get in Touch',
    'contact.sub': 'Tell us what you need — we reply within 1 business day.',
    'f.home': 'Home', 'f.products': 'Products', 'f.about': 'About', 'f.contact': 'Contact',
    'f.brand': 'SANFAN Yoga', 'f.tag': 'TPE/NBR yoga mat & foam roller source factory.',
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
    'hero.eyebrow': 'TPE / NBR 瑜伽垫 & 瑜伽柱 源头工厂',
    'hero.title': '来自中国晋江，为你的品牌而生。',
    'hero.lead': '福建三梵体育用品实业有限公司 — 12 年专注 TPE 瑜伽垫、体位线垫、NBR 瑜伽垫与瑜伽柱制造。TPE 100 片起订，瑜伽柱 500 个起订，NBR 1000 条起订。7 天打样。',
    'hero.cta1': '立即询价', 'hero.cta2': '查看产品',
    'hero.stat1.n': '12+', 'hero.stat1.l': '年制造经验',
    'hero.stat2.n': '100', 'hero.stat2.l': '片起订',
    'hero.stat3.n': '7', 'hero.stat3.l': '天打样',
    'hero.media': '工厂 / 产品图占位',
    'str.title': '为什么选择我们',
    'str.sub': '为贴牌成功而生的柔性供应链。',
    'str1.t': '低起订量', 'str1.d': 'TPE 瑜伽垫 100 片起订；瑜伽柱 500 个起订；NBR 瑜伽垫 1000 条起订。小批量试水无库存压力。',
    'str2.t': '快速打样', 'str2.d': '7 天出实物样，支持你的品牌 logo、配色与包装。',
    'str3.t': '全面定制', 'str3.d': '材质、尺寸、厚度、颜色、双色、logo、折叠、包装，全部按需定制。',
    'str4.t': '认证品质', 'str4.d': '符合 REACH、CA Prop 65、6P/7P 等国际市场要求。',
    'prod.title': '我们的产品',
    'prod.sub': 'TPE/NBR 瑜伽垫、体位线垫与瑜伽柱，支持贴牌定制。',
    'prod1.t': 'TPE 瑜伽垫', 'prod1.d': '环保双层 TPE，防滑纹理表面，宽度 61-122 cm，厚度 4-12 mm。可选实重、经济、特供等级。',
    'prod2.t': '体位线瑜伽垫', 'prod2.d': '莲花印花引导线，帮助正确练习。TPE 基材，61/80 cm 宽度，可配套背带与网包。',
    'prod3.t': 'NBR 瑜伽垫', 'prod3.d': '高弹亚光防滑 NBR 橡胶。爆款 183×61×1 cm；厚度 0.8-2 cm；可加宽至 80/90 cm。',
    'prod3.thumb': 'NBR 瑜伽垫',
    'prod4.t': '瑜伽柱', 'prod4.d': 'PVC/PP 内管，50 度硬度，光面或狼牙、月牙、水波纹、菱形等纹理表面。',
    'prod4.thumb': '瑜伽柱',
    'prod.spec.moq': '起订量', 'prod.spec.lead': '打样', 'prod.spec.cert': '认证', 'prod.spec.oem': '贴牌',
    'spec.title': '规格一览',
    'spec.sub': '常见尺寸与起订量速查。支持定制尺寸、颜色与包装。',
    'spec1.t': 'TPE 瑜伽垫',
    'spec1.d': '1830×610 / 1830×800 / 1850×900 / 2000×1000 / 1850×1220 mm\n厚度 4-12 mm\n起订量 100 片',
    'spec2.t': '体位线瑜伽垫',
    'spec2.d': '61 cm / 80 cm 宽度\n莲花 + 中线引导\n起订量 100 片',
    'spec3.t': 'NBR 瑜伽垫',
    'spec3.d': '183×61×0.8-2 cm\n185×80×1 / 185×90×1 cm\n起订量 1000 条（常规色）',
    'spec4.t': '瑜伽柱',
    'spec4.d': '25×7.5 至 45×14 cm\n光面 / 狼牙 / 月牙 / 水波纹 / 菱形\n起订量 500 个',
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
    'about.h1': '福建三梵体育用品实业有限公司',
    'about.p1': '三梵创立于中国体育用品制造重镇 — 泉州晋江。12 年来，我们为世界各地的瑜伽品牌、零售商与场馆生产瑜伽垫与瑜伽柱。',
    'about.p2': '我们专注 TPE 瑜伽垫、体位线垫、NBR 瑜伽垫与瑜伽柱。柔性供应链支持小批量试单、7 天快速打样及全面贴牌定制，包括材质、尺寸、颜色、双色、logo、折叠与包装。',
    'about.p3': '无论你是寻找可靠 OEM 伙伴的瑜伽品牌、打造自有产品线的零售商，还是需要稳定品质大规模供货的场馆连锁，我们都能从福建工厂直发至你的仓库。',
    'contact.title': '联系我们',
    'contact.sub': '告诉我们你的需求，1 个工作日内回复。',
    'f.home': '首页', 'f.products': '产品', 'f.about': '关于', 'f.contact': '联系',
    'f.brand': '三梵瑜伽', 'f.tag': 'TPE/NBR 瑜伽垫 / 瑜伽柱 源头工厂。',
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
    if (I18N[lang][key] != null) {
      // preserve line breaks in spec cards
      if (key.startsWith('spec') && key.endsWith('.d')) {
        el.innerHTML = I18N[lang][key].replace(/\n/g, '<br>');
      } else {
        el.textContent = I18N[lang][key];
      }
    }
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
        okBox.style.background = '';
        okBox.style.color = '';
        okBox.style.borderColor = '';
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
