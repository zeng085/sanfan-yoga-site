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
    'factory.title': 'Factory at a Glance',
    'factory.sub': '15,000 m² facility with ISO 9001, SGS and 1688 Super Factory status.',
    'factory.stat1': '12+', 'factory.s1': 'Years Experience',
    'factory.stat2': '15,000 m²', 'factory.s2': 'Factory Floor',
    'factory.stat3': '50+', 'factory.s3': 'Production Machines',
    'factory.stat4': '5M+', 'factory.s4': 'Annual Capacity',
    'range.title': 'Full Product Range',
    'range.sub': 'Yoga mats, foam rollers, blocks, straps and studio accessories.',
    'cert.title': 'Certifications',
    'cert.sub': 'ISO 9001, SGS, 1688 Super Factory, audited supplier.',
    'process.title': 'Production Process',
    'process.sub': 'Foaming → Cutting → Forming → QC → Packing.',
    'custom.title': 'OEM / ODM Flow',
    'custom.sub': '6 clear steps from concept to finished goods.',
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
    'about.p1': 'Founded in Jinjiang, Quanzhou — the heart of China\'s sporting-goods manufacturing belt — SANFAN integrates R&D, production and supply chain for yoga and home fitness equipment.',
    'about.p2': 'Our main products include TPE yoga mats, natural rubber mats, PU anti-slip mats, cork mats, yoga blocks, yoga wheels, foam rollers, yoga sticks and fitness accessories. We support OEM, ODM and private-label customization, exporting to Europe, the US, Japan and beyond.',
    'about.p3': 'With a 15,000 m² factory, 50+ production machines and a 5-million-piece annual capacity, we deliver consistent quality at scale for yoga brands, retailers and studio chains.',
    'about.cap.title': 'Capabilities',
    'about.cap.l1': 'Material selection and formulation control',
    'about.cap.l2': 'Custom size, thickness, color and surface finish',
    'about.cap.l3': 'Logo printing, embossing and packaging design',
    'about.cap.l4': 'In-house QC and batch traceability',
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
    'proc.flow.t1': 'Foaming', 'proc.flow.t2': 'Cutting', 'proc.flow.t3': 'Forming', 'proc.flow.t4': 'Quality Check', 'proc.flow.t5': 'Packing',
    'proc.flow.d1': 'Material foamed to spec', 'proc.flow.d2': 'Precision-cut to size', 'proc.flow.d3': 'Molded & finished', 'proc.flow.d4': 'Inspected per batch', 'proc.flow.d5': 'Packed to ship',
    'oem.t1': 'Inquiry', 'oem.t2': 'Design & Quote', 'oem.t3': 'Sampling', 'oem.t4': 'Confirm & Deposit', 'oem.t5': 'Mass Production', 'oem.t6': 'QC & Shipping',
    'oem.d1': 'Share specs', 'oem.d2': 'Quote & artwork', 'oem.d3': 'Physical sample', 'oem.d4': 'Pay deposit', 'oem.d5': 'Bulk run', 'oem.d6': 'Inspect & ship',
    'cert1.n': 'ISO 9001', 'cert1.s': 'Quality system',
    'cert2.n': 'SGS', 'cert2.s': 'Third-party tested',
    'cert3.n': '1688 Super Factory', 'cert3.s': 'Verified maker',
    'cert4.n': 'Audited Supplier', 'cert4.s': 'CMN certified',
    'cat1.n': 'TPE Mats', 'cat1.s': '4-12 mm',
    'cat2.n': 'Alignment Mats', 'cat2.s': 'Guide lines',
    'cat3.n': 'NBR Mats', 'cat3.s': 'High-elastic',
    'cat4.n': 'Foam Rollers', 'cat4.s': 'Multi-texture',
    'cat5.n': 'Yoga Blocks', 'cat5.s': 'EVA / cork',
    'cat6.n': 'Yoga Straps', 'cat6.s': 'Cotton / poly',
    'cat7.n': 'Yoga Wheels', 'cat7.s': 'Back & core',
    'cat8.n': 'Cork Mats', 'cat8.s': 'Natural grip',
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
    'factory.title': '工厂一览',
    'factory.sub': '15000 ㎡ 厂房，通过 ISO 9001、SGS 及 1688 超级工厂认证。',
    'factory.stat1': '12+', 'factory.s1': '年行业经验',
    'factory.stat2': '15000 ㎡', 'factory.s2': '厂房面积',
    'factory.stat3': '50+', 'factory.s3': '生产设备',
    'factory.stat4': '500万+', 'factory.s4': '年产能',
    'range.title': '全系列产品',
    'range.sub': '瑜伽垫、瑜伽柱、瑜伽砖、伸展带及场馆配套。',
    'cert.title': '资质认证',
    'cert.sub': 'ISO 9001、SGS、1688 超级工厂、中国制造网认证供应商。',
    'process.title': '生产流程',
    'process.sub': '发泡 → 裁切 → 成型 → 质检 → 包装。',
    'custom.title': 'OEM / ODM 定制流程',
    'custom.sub': '从概念到成品，六步清晰可控。',
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
    'about.p1': '三梵坐落于中国体育用品制造重镇 — 泉州晋江，是一家集研发、生产、供应链为一体的瑜伽与家用健身装备企业。',
    'about.p2': '主营 TPE 瑜伽垫、天然橡胶垫、PU 防滑垫、软木垫、瑜伽砖、瑜伽轮、泡沫轴、瑜伽棒及健身小器材；支持 OEM、ODM 及贴牌定制，产品远销欧洲、美国、日本等市场。',
    'about.p3': '工厂占地 15000 ㎡，拥有 50 余台生产设备，年产能超 500 万件，可为瑜伽品牌、零售商及场馆连锁提供稳定的大规模供货。',
    'about.cap.title': '核心能力',
    'about.cap.l1': '原材料选择与配方把控',
    'about.cap.l2': '尺寸、厚度、颜色、表面工艺定制',
    'about.cap.l3': 'Logo 印刷、压印及包装设计',
    'about.cap.l4': '内部质检与批次可追溯',
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
    'proc.flow.t1': '发泡', 'proc.flow.t2': '裁切', 'proc.flow.t3': '成型', 'proc.flow.t4': '质检', 'proc.flow.t5': '包装',
    'proc.flow.d1': '原料按规格发泡', 'proc.flow.d2': '精密裁切定尺', 'proc.flow.d3': '模压与表面处理', 'proc.flow.d4': '逐批检验', 'proc.flow.d5': '包装待发',
    'oem.t1': '询盘', 'oem.t2': '设计与报价', 'oem.t3': '打样', 'oem.t4': '确认与定金', 'oem.t5': '批量生产', 'oem.t6': '质检发货',
    'oem.d1': '告知规格', 'oem.d2': '报价与图稿', 'oem.d3': '实物样品', 'oem.d4': '支付定金', 'oem.d5': '规模量产', 'oem.d6': '检验出货',
    'cert1.n': 'ISO 9001', 'cert1.s': '质量管理体系',
    'cert2.n': 'SGS', 'cert2.s': '第三方检测',
    'cert3.n': '1688 超级工厂', 'cert3.s': '认证制造工厂',
    'cert4.n': '认证供应商', 'cert4.s': '中国制造网认证',
    'cat1.n': 'TPE 瑜伽垫', 'cat1.s': '4-12 mm',
    'cat2.n': '体位线垫', 'cat2.s': '引导线',
    'cat3.n': 'NBR 瑜伽垫', 'cat3.s': '高弹',
    'cat4.n': '瑜伽柱', 'cat4.s': '多纹理',
    'cat5.n': '瑜伽砖', 'cat5.s': 'EVA / 软木',
    'cat6.n': '伸展带', 'cat6.s': '棉 / 涤纶',
    'cat7.n': '瑜伽轮', 'cat7.s': '腰背核心',
    'cat8.n': '软木垫', 'cat8.s': '天然防滑',
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
