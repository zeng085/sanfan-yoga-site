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

    // Hero
    'hero.eyebrow': 'OEM / ODM Yoga & Fitness Manufacturer',
    'hero.title': 'XIAMEN SANFAN — Your Direct Factory for Yoga & Fitness Gear',
    'hero.lead': 'Since 2013, a leading OEM/ODM manufacturer of yoga mats, foam rollers, yoga accessories and fitness equipment. 600+ skilled workers, monthly capacity of 200,000+ yoga mats, 24-hour service team. MOQ from 100 pcs, 7-day sampling.',
    'hero.cta1': 'Request a Quote', 'hero.cta2': 'Explore Products',
    'hero.stat1.n': '2013', 'hero.stat1.l': 'Established',
    'hero.stat2.n': '600+', 'hero.stat2.l': 'Skilled Workers',
    'hero.stat3.n': '200K+', 'hero.stat3.l': 'Mats / Month',
    'hero.stat4.n': '24/7', 'hero.stat4.l': 'Service Team',
    'hero.media': 'SANFAN factory',

    // Why choose us
    'str.title': 'Why Buyers Choose SANFAN',
    'str.sub': 'A flexible supply chain engineered for private-label success.',
    'str1.t': 'Low MOQ', 'str1.d': 'TPE mats from 100 pcs; foam rollers from 500 pcs; NBR from 1,000 pcs. Test the market without heavy inventory risk.',
    'str2.t': 'Fast Sampling', 'str2.d': 'Physical samples in 7 days with your logo, color and packaging options.',
    'str3.t': 'Full Customization', 'str3.d': 'Material, size, thickness, color, double-color, logo, fold and packaging — all made to spec.',
    'str4.t': 'Certified Quality', 'str4.d': 'REACH, CA Prop 65, 6P/7P compliance, ISO 9001 & BSCI audited for global markets.',

    // Factory at a glance
    'factory.title': 'Factory at a Glance',
    'factory.sub': 'A vertically integrated manufacturer in Fujian — R&D, production and QC under one roof.',
    'factory.stat1': '2013', 'factory.s1': 'Established',
    'factory.stat2': '600+', 'factory.s2': 'Workers',
    'factory.stat3': '12,000㎡', 'factory.s3': 'Facility',
    'factory.stat4': '5 Lines', 'factory.s4': 'Production Lines',
    'factory.cap.title': 'Monthly Production Capacity',
    'cap1.t': 'Yoga Mats', 'cap1.d': '200,000 pcs / month',
    'cap2.t': 'Sports Bags', 'cap2.d': '150,000 pcs / month',
    'cap3.t': 'Yoga Wears', 'cap3.d': '120,000 pcs / month',
    'cap4.t': 'Yoga Leggings', 'cap4.d': '100,000 pcs / month',
    'cap5.t': 'Yoga Blocks', 'cap5.d': '100,000 pcs / month',
    'factory.media': 'SANFAN factory building',

    // Product range (3 cards)
    'range.title': 'Our Product Range',
    'range.sub': 'From yoga essentials to full fitness lines — all factory-direct and customizable.',
    'range1.t': 'Yoga Mats', 'range1.s': 'TPE · PU/Rubber · PVC · Foldable', 'range1.alt': 'Yoga mat collection',
    'range2.t': 'Yoga & Pilates Accessories', 'range2.s': 'Rollers · Blocks · Balls · Bands · Gripper · Shoes', 'range2.alt': 'Yoga accessories',
    'range3.t': 'Fitness Equipment', 'range3.s': 'Dumbbell & Kettlebell Sets', 'range3.alt': 'Fitness equipment',

    // Full gallery
    'gallery.title': 'Full Product Gallery',
    'gallery.sub': 'Every category we manufacture — ready for OEM, ODM and private label.',
    'gallery.note': 'Every photo is a real shot from our live 1688 factory store — the exact products we make and ship.',
    'g1.n': 'TPE Yoga Mat', 'g1.s': 'Eco double-layer, 4–12 mm',
    'g2.n': 'Wide TPE Yoga Mat', 'g2.s': 'Extra-wide 80/122 cm',
    'g3.n': 'Double-wide TPE Mat', 'g3.s': 'Wide format for 2 persons',
    'g4.n': 'Foldable TPE Yoga Mat', 'g4.s': 'Tri-fold, ultra-portable',
    'g5.n': 'PU / Rubber Premium Mat', 'g5.s': 'Premium grip',
    'g6.n': 'Frosted PU Yoga Mat', 'g6.s': 'Matte frosted surface',
    'g7.n': 'Camo PU Yoga Mat', 'g7.s': 'Bold camo print',
    'g8.n': 'PVC Yoga Mat', 'g8.s': 'Durable & cost-effective',
    'g9.n': 'Yoga Foam Roller (Wolf-tooth)', 'g9.s': 'EVA wolf-tooth texture',
    'g10.n': 'Solid Foam Roller', 'g10.s': 'Solid EVA core',
    'g11.n': 'Electric Foam Roller', 'g11.s': 'Rechargeable vibration',
    'g12.n': 'Yoga Blocks (EVA)', 'g12.s': 'High-density EVA',
    'g13.n': 'Mini Yoga Ball (25 cm)', 'g13.s': '25 cm anti-slip',
    'g14.n': 'Yoga Ball (1700 g)', 'g14.s': '1700 g anti-burst',
    'g15.n': 'Massage Ball', 'g15.s': 'Fascia relief',
    'g16.n': 'Resistance Band', 'g16.s': 'Multi-tension',
    'g17.n': 'Hand Gripper', 'g17.s': 'Silicone grip ring',
    'g18.n': 'Yoga Shoes', 'g18.s': 'Non-slip indoor',
    'g19.n': 'Dumbbell / Kettlebell Set', 'g19.s': '6 kg / 2 kg set',

    // Certifications
    'cert.title': 'Certifications',
    'cert.sub': 'ISO 9001, SGS, BSCI, 1688 Super Factory and Made-in-China Audited.',
    'cert1.n': 'ISO 9001', 'cert1.s': 'Quality system',
    'cert2.n': 'SGS', 'cert2.s': 'Third-party tested',
    'cert3.n': '1688 Super Factory', 'cert3.s': 'Verified maker',
    'cert4.n': 'BSCI', 'cert4.s': 'Social compliance',
    'cert5.n': 'Made-in-China Audited', 'cert5.s': 'Verified supplier',
    'cert6.n': 'Fujian High-Tech', 'cert6.s': 'Innovation recognized',
    'cert.wall.alt': 'SANFAN certification wall',

    // Production process
    'process.title': 'Production Process',
    'process.sub': 'Foaming → Cutting → Molding → QC → Packing.',
    'proc.flow.t1': 'Foaming', 'proc.flow.d1': 'Material foamed to spec',
    'proc.flow.t2': 'Cutting', 'proc.flow.d2': 'Precision-cut to size',
    'proc.flow.t3': 'Molding', 'proc.flow.d3': 'Molded & finished',
    'proc.flow.t4': 'Quality Check', 'proc.flow.d4': 'Inspected per batch',
    'proc.flow.t5': 'Packing', 'proc.flow.d5': 'Packed to ship',

    // OEM / ODM flow
    'custom.title': 'OEM / ODM Flow',
    'custom.sub': 'Six clear steps from concept to finished goods.',
    'oem.t1': 'Inquiry', 'oem.d1': 'Share specs',
    'oem.t2': 'Design & Quote', 'oem.d2': 'Quote & artwork',
    'oem.t3': 'Sampling', 'oem.d3': 'Physical sample',
    'oem.t4': 'Confirm & Deposit', 'oem.d4': 'Pay deposit',
    'oem.t5': 'Mass Production', 'oem.d5': 'Bulk run',
    'oem.t6': 'QC & Shipping', 'oem.d6': 'Inspect & ship',

    // How it works
    'proc.title': 'How It Works',
    'proc.sub': 'From inquiry to delivery in four clear steps.',
    'proc1.t': 'Send Inquiry', 'proc1.d': 'Tell us your specs, quantity and target market.',
    'proc2.t': 'Sample & Quote', 'proc2.d': 'We send a quote and a physical sample within 7 days.',
    'proc3.t': 'Production', 'proc3.d': 'Confirm order, we manufacture and QC every batch.',
    'proc4.t': 'Ship & Support', 'proc4.d': 'Global shipping and ongoing reorder support.',

    // Products page
    'prod.title': 'Our Products',
    'prod.sub': 'Yoga mats, accessories and fitness equipment — all factory-direct and customizable.',
    'prod.nav.title': 'Categories',
    'cat.yoga.title': 'Yoga Mats', 'cat.yoga.sub': 'TPE · PU/Rubber · PVC · Foldable',
    'cat.acc.title': 'Yoga & Pilates Accessories', 'cat.acc.sub': 'Rollers · Blocks · Balls · Bands · Gripper · Shoes',
    'cat.fit.title': 'Fitness Equipment', 'cat.fit.sub': 'Dumbbell & Kettlebell Sets',
    'ym1.t': 'TPE Yoga Mat', 'ym1.d': 'Eco double-layer TPE, non-slip textured surface, widths 61–122 cm, thickness 4–12 mm. Solid, economy and special grades.',
    'ym2.t': 'Wide TPE Yoga Mat', 'ym2.d': 'Extra-wide 80/122 cm TPE mat for dynamic and partner practice; same eco double-layer grip.',
    'ym3.t': 'Double-wide TPE Mat', 'ym3.d': 'Wide-format TPE mat for couples and family use; non-slip, easy to clean.',
    'ym4.t': 'Foldable TPE Yoga Mat', 'ym4.d': 'Tri-fold design opens flat with no curl; 6 mm cushioning; ultra-portable, packs into a backpack.',
    'ym5.t': 'PU / Rubber Premium Mat', 'ym5.d': 'Natural rubber base + PU anti-slip top; premium grip for hot yoga and studios (the "premium" mat).',
    'ym6.t': 'Frosted PU Yoga Mat', 'ym6.d': 'Matte frosted PU surface, elegant feel, high sweat-absorption grip for intense sessions.',
    'ym7.t': 'Camo PU Yoga Mat', 'ym7.d': 'Camouflage-print PU rubber mat with a bold look, ideal for branded lines.',
    'ym8.t': 'PVC Yoga Mat', 'ym8.d': 'Durable, cost-effective PVC mat for gyms and studios; MOQ-friendly for bulk orders.',
    'ac1.t': 'Yoga Foam Roller (Wolf-tooth)', 'ac1.d': 'EVA foam roller with wolf-tooth texture; 45 cm muscle recovery and myofascial release.',
    'ac2.t': 'Yoga Blocks (EVA)', 'ac2.d': 'High-density EVA blocks; stable support for poses and stretches, multiple colors.',
    'ac3.t': 'Solid Foam Roller', 'ac3.d': 'Solid EVA roller for deep-tissue massage and core training.',
    'ac4.t': 'Electric Foam Roller', 'ac4.d': 'Rechargeable vibrating foam roller for professional recovery.',
    'ac5.t': 'Mini Yoga Ball (25 cm)', 'ac5.d': '25 cm anti-slip gymnastic ball for pilates, rehab and core work.',
    'ac6.t': 'Yoga Ball (1700 g)', 'ac6.d': '1700 g anti-burst yoga / fitness ball, pregnancy and general training.',
    'ac7.t': 'Massage Ball', 'ac7.d': 'Fascia massage ball for shoulders, back, waist and foot relief.',
    'ac8.t': 'Resistance Band', 'ac8.d': 'Elastic bands / 拉力带 for strength, stretch and glute training.',
    'ac9.t': 'Hand Gripper', 'ac9.d': 'Silicone grip ring for hand and forearm strength training.',
    'ac10.t': 'Yoga Shoes', 'ac10.d': 'Lightweight non-slip indoor training shoes for yoga and dance.',
    'fi1.t': 'Dumbbell / Kettlebell Set', 'fi1.d': 'Home light-training dumbbell & kettlebell set (6 kg / 2 kg), portable shaping fitness gear.',

    // Spec overview
    'spec.title': 'Specification Overview',
    'spec.sub': 'Popular sizes and MOQs at a glance. Custom sizes, colors and packaging available on request.',
    'spec1.t': 'TPE Yoga Mat', 'spec1.d': '1830×610 / 1830×800 / 1850×900 / 2000×1000 / 1850×1220 mm\nThickness 4–12 mm\nMOQ 100 pcs',
    'spec2.t': 'Wide / Double TPE Mat', 'spec2.d': '80 cm / 122 cm widths\nEco double-layer TPE\nMOQ 100 pcs',
    'spec3.t': 'PU / Rubber Mat', 'spec3.d': 'Natural rubber base + PU anti-slip top\n1830×610 / 1850×800 mm\nMOQ on request',
    'spec4.t': 'PVC Yoga Mat', 'spec4.d': 'Durable PVC construction\n61 / 80 / 122 cm widths\nMOQ friendly',
    'spec5.t': 'Yoga Blocks (EVA)', 'spec5.d': 'High-density EVA\n9×15×23 cm standard\nMOQ 500 pcs',
    'spec6.t': 'Yoga Foam Roller', 'spec6.d': '25×7.5 to 45×14 cm\nSmooth / wolf-tooth / solid\nMOQ 500 pcs',
    'spec7.t': 'Yoga / Fitness Ball', 'spec7.d': '25 cm mini / 1700 g standard\nAnti-burst\nMOQ on request',
    'spec8.t': 'Resistance Band / Gripper', 'spec8.d': 'Bands & silicone grip rings\nMultiple tensions\nMOQ on request',

    // About
    'about.title': 'About SANFAN',
    'about.sub': 'A yoga & fitness equipment source factory trusted by brands worldwide.',
    'about.h1': 'XIAMEN SANFAN Sports Products Co., Ltd.',
    'about.p1': 'Founded in 2013 and based in Xiamen, Fujian, SANFAN is a leading OEM/ODM manufacturer of yoga mats and sports products, with our manufacturing base in Jinjiang — the heart of China’s sporting-goods belt.',
    'about.p2': 'We provide customized designing, developing, manufacturing and exporting for customers worldwide. Our range covers yoga mats, foam rollers, blocks, apparel, towels, balls and a broad selection of fitness accessories.',
    'about.p3': 'With 600+ skilled workers and high-tech machines, we guarantee high-output, high-quality production and on-time delivery at competitive prices. Our service team is on standby 24 hours to support our customers.',
    'about.cap.title': 'Core Capabilities',
    'about.cap.l1': 'Material formulation & product development',
    'about.cap.l2': 'Custom size, thickness, color & surface finish',
    'about.cap.l3': 'Logo printing, embossing & packaging design',
    'about.cap.l4': 'In-house QC and batch traceability',
    'about.cap.t1': 'Material & Development', 'about.cap.t2': 'Custom Finish', 'about.cap.t3': 'Branding & Packaging', 'about.cap.t4': 'Quality Control',

    // Contact
    'contact.title': 'Get in Touch',
    'contact.sub': 'Tell us what you need — we reply within 1 business day.',
    'contact.info.title': 'Contact Information',
    'c.addr.label': 'Address', 'c.email.label': 'Email', 'c.phone.label': 'WhatsApp', 'c.hours.label': 'Service',
    'form.name': 'Your Name', 'form.company': 'Company', 'form.email': 'Email',
    'form.product': 'Product of Interest', 'form.qty': 'Estimated Quantity',
    'form.msg': 'Message', 'form.send': 'Send Inquiry', 'form.note': 'We never share your information.',
    'form.ok': 'Thanks! Your inquiry has been sent. We will reply within 1 business day.',
    'form.fail': 'Something went wrong. Please email us directly.',
    'form.opt.yoga': 'Yoga Mats', 'form.opt.acc': 'Yoga & Pilates Accessories',
    'form.opt.fit': 'Fitness Equipment', 'form.opt.other': 'Other / Not sure',

    // Footer
    'f.home': 'Home', 'f.products': 'Products', 'f.about': 'About', 'f.contact': 'Contact',
    'f.brand': 'SANFAN', 'f.tag': 'OEM / ODM yoga & fitness manufacturer.',
    'foot.products': 'Products', 'foot.company': 'Company', 'foot.contact': 'Contact',
    'foot.addr': 'Address', 'foot.email': 'Email', 'foot.phone': 'WhatsApp',
    'foot.copyright': '© 2026 XIAMEN SANFAN Sports Products Co., Ltd. All rights reserved.',

    // CTA
    'cta.title': 'Ready to Build Your Brand?',
    'cta.sub': 'Get a tailored quote and free samples today.',
    'cta.btn': 'Contact Our Team',
  },

  zh: {
    'nav.home': '首页', 'nav.products': '产品', 'nav.about': '关于',
    'nav.contact': '联系', 'nav.quote': '获取报价',

    'hero.eyebrow': '瑜伽 & 健身器材 OEM / ODM 制造工厂',
    'hero.title': '厦门三梵 — 你的瑜伽与健身器材直供工厂',
    'hero.lead': '自 2013 年起，三梵是领先的瑜伽垫、瑜伽柱、瑜伽配件及健身器材 OEM/ODM 制造商。600+ 熟练工人，瑜伽垫月产能 20 万+，24 小时服务团队。100 片起订，7 天打样。',
    'hero.cta1': '立即询价', 'hero.cta2': '浏览产品',
    'hero.stat1.n': '2013', 'hero.stat1.l': '成立年份',
    'hero.stat2.n': '600+', 'hero.stat2.l': '熟练工人',
    'hero.stat3.n': '20万+', 'hero.stat3.l': '垫子/月',
    'hero.stat4.n': '24/7', 'hero.stat4.l': '服务团队',
    'hero.media': '三梵工厂',

    'str.title': '为什么选择三梵',
    'str.sub': '为贴牌成功而生的柔性供应链。',
    'str1.t': '低起订量', 'str1.d': 'TPE 瑜伽垫 100 片起订；瑜伽柱 500 个起订；其余品类起订量面议。小批量试水无库存压力。',
    'str2.t': '快速打样', 'str2.d': '7 天出实物样，支持你的品牌 logo、配色与包装。',
    'str3.t': '全面定制', 'str3.d': '材质、尺寸、厚度、颜色、双色、logo、折叠、包装，全部按需定制。',
    'str4.t': '认证品质', 'str4.d': '符合 REACH、CA Prop 65、6P/7P，通过 ISO 9001 与 BSCI 审核，进军全球市场。',

    'factory.title': '工厂一览',
    'factory.sub': '福建一体化制造工厂 — 研发、生产、质检一站式。',
    'factory.stat1': '2013', 'factory.s1': '成立年份',
    'factory.stat2': '600+', 'factory.s2': '员工规模',
    'factory.stat3': '12000㎡', 'factory.s3': '厂房面积',
    'factory.stat4': '5 条', 'factory.s4': '生产线',
    'factory.cap.title': '月度产能',
    'cap1.t': '瑜伽垫', 'cap1.d': '200,000 片 / 月',
    'cap2.t': '运动包', 'cap2.d': '150,000 个 / 月',
    'cap3.t': '瑜伽服', 'cap3.d': '120,000 件 / 月',
    'cap4.t': '瑜伽裤', 'cap4.d': '100,000 条 / 月',
    'cap5.t': '瑜伽砖', 'cap5.d': '100,000 块 / 月',
    'factory.media': '三梵工厂厂房',

    'range.title': '产品系列',
    'range.sub': '从瑜伽刚需到完整健身线 — 全部工厂直供、可定制。',
    'range1.t': '瑜伽垫', 'range1.s': 'TPE · PU/橡胶 · PVC · 折叠', 'range1.alt': '瑜伽垫系列',
    'range2.t': '瑜伽 & 普拉提配件', 'range2.s': '瑜伽柱 · 瑜伽砖 · 瑜伽球 · 弹力带 · 握力器 · 瑜伽鞋', 'range2.alt': '瑜伽配件',
    'range3.t': '健身器材', 'range3.s': '哑铃 & 壶铃套装', 'range3.alt': '健身器材',

    'gallery.title': '全产品图库',
    'gallery.sub': '我们生产的每一个品类，均支持 OEM、ODM 与贴牌定制。',
    'gallery.note': '每一张都是来自我们 1688 工厂店的真实产品图 — 正是我们目前在做的品类。',
    'g1.n': 'TPE 瑜伽垫', 'g1.s': '环保双层，4–12 mm',
    'g2.n': '加宽 TPE 瑜伽垫', 'g2.s': '80/122 cm 加宽',
    'g3.n': '双人加宽 TPE 垫', 'g3.s': '双人加宽版',
    'g4.n': '折叠 TPE 瑜伽垫', 'g4.s': '三折超便携',
    'g5.n': 'PU / 橡胶高端垫', 'g5.s': '高端防滑',
    'g6.n': '磨砂 PU 瑜伽垫', 'g6.s': '磨砂 PU 表面',
    'g7.n': '迷彩 PU 瑜伽垫', 'g7.s': '硬朗迷彩印花',
    'g8.n': 'PVC 瑜伽垫', 'g8.s': '耐用高性价比',
    'g9.n': '狼牙瑜伽柱', 'g9.s': 'EVA 狼牙齿纹',
    'g10.n': '实心瑜伽柱', 'g10.s': '实心 EVA',
    'g11.n': '电动瑜伽柱', 'g11.s': '可充电震动',
    'g12.n': '瑜伽砖（EVA）', 'g12.s': '高密度 EVA',
    'g13.n': '迷你瑜伽球（25cm）', 'g13.s': '25 cm 防滑',
    'g14.n': '瑜伽球（1700g）', 'g14.s': '1700 g 防爆',
    'g15.n': '按摩球', 'g15.s': '筋膜放松',
    'g16.n': '弹力带', 'g16.s': '多档阻力',
    'g17.n': '握力圈', 'g17.s': '硅胶握力圈',
    'g18.n': '瑜伽鞋', 'g18.s': '防滑室内鞋',
    'g19.n': '哑铃 / 壶铃套装', 'g19.s': '6 kg / 2 kg 套装',

    'cert.title': '资质认证',
    'cert.sub': 'ISO 9001、SGS、BSCI、1688 超级工厂及中国制造网认证。',
    'cert1.n': 'ISO 9001', 'cert1.s': '质量管理体系',
    'cert2.n': 'SGS', 'cert2.s': '第三方检测',
    'cert3.n': '1688 超级工厂', 'cert3.s': '认证制造工厂',
    'cert4.n': 'BSCI', 'cert4.s': '社会责任认证',
    'cert5.n': '中国制造网认证', 'cert5.s': '认证供应商',
    'cert6.n': '福建高新技术企业', 'cert6.s': '创新型企业',
    'cert.wall.alt': '三梵证书墙',

    'process.title': '生产流程',
    'process.sub': '发泡 → 裁切 → 成型 → 质检 → 包装。',
    'proc.flow.t1': '发泡', 'proc.flow.d1': '原料按规格发泡',
    'proc.flow.t2': '裁切', 'proc.flow.d2': '精密裁切定尺',
    'proc.flow.t3': '成型', 'proc.flow.d3': '模压与表面处理',
    'proc.flow.t4': '质检', 'proc.flow.d4': '逐批检验',
    'proc.flow.t5': '包装', 'proc.flow.d5': '包装待发',

    'custom.title': 'OEM / ODM 定制流程',
    'custom.sub': '从概念到成品，六步清晰可控。',
    'oem.t1': '询盘', 'oem.d1': '告知规格',
    'oem.t2': '设计与报价', 'oem.d2': '报价与图稿',
    'oem.t3': '打样', 'oem.d3': '实物样品',
    'oem.t4': '确认与定金', 'oem.d4': '支付定金',
    'oem.t5': '批量生产', 'oem.d5': '规模量产',
    'oem.t6': '质检发货', 'oem.d6': '检验出货',

    'proc.title': '合作流程',
    'proc.sub': '四步清晰，从询盘到交付。',
    'proc1.t': '提交询盘', 'proc1.d': '告知规格、数量与目标市场。',
    'proc2.t': '打样报价', 'proc2.d': '7 天内寄出报价与实物样品。',
    'proc3.t': '生产', 'proc3.d': '确认订单后生产，每批严格质检。',
    'proc4.t': '发货支持', 'proc4.d': '全球发货，长期复购支持。',

    'prod.title': '我们的产品',
    'prod.sub': '瑜伽垫、配件与健身器材 — 全部工厂直供、可定制。',
    'prod.nav.title': '产品分类',
    'cat.yoga.title': '瑜伽垫', 'cat.yoga.sub': 'TPE · PU/橡胶 · PVC · 折叠',
    'cat.acc.title': '瑜伽 & 普拉提配件', 'cat.acc.sub': '瑜伽柱 · 瑜伽砖 · 瑜伽球 · 弹力带 · 握力器 · 瑜伽鞋',
    'cat.fit.title': '健身器材', 'cat.fit.sub': '哑铃 & 壶铃套装',
    'ym1.t': 'TPE 瑜伽垫', 'ym1.d': '环保双层 TPE，防滑纹理表面，宽度 61–122 cm，厚度 4–12 mm。可选实重、经济、特供等级。',
    'ym2.t': '加宽 TPE 瑜伽垫', 'ym2.d': '80/122 cm 加宽 TPE 垫，适合流瑜伽与双人练习；同样环保双层抓地。',
    'ym3.t': '双人加宽 TPE 垫', 'ym3.d': '加宽版 TPE 垫，适合情侣与家庭使用；防滑、易清洁。',
    'ym4.t': '折叠 TPE 瑜伽垫', 'ym4.d': '三折设计平铺不卷边；6 mm 缓冲；超便携，可塞入背包。',
    'ym5.t': 'PU / 橡胶高端垫', 'ym5.d': '天然橡胶底 + PU 防滑面；高温瑜伽与瑜伽馆高端抓地（"土豪垫"）。',
    'ym6.t': '磨砂 PU 瑜伽垫', 'ym6.d': '磨砂 PU 表面，触感高级，高强度下吸汗抓地更稳。',
    'ym7.t': '迷彩 PU 瑜伽垫', 'ym7.d': '迷彩印花 PU 橡胶垫，外观硬朗，适合做品牌定制线。',
    'ym8.t': 'PVC 瑜伽垫', 'ym8.d': '耐用高性价比 PVC 垫，适合健身房与瑜伽馆批量采购；起订友好。',
    'ac1.t': '狼牙瑜伽柱', 'ac1.d': 'EVA 狼牙齿纹瑜伽柱；45 cm 肌肉放松与筋膜放松。',
    'ac2.t': '瑜伽砖（EVA）', 'ac2.d': '高密度 EVA 瑜伽砖；稳定支撑体式与拉伸，多色可选。',
    'ac3.t': '实心瑜伽柱', 'ac3.d': '实心 EVA 瑜伽柱，深层按摩与核心训练。',
    'ac4.t': '电动瑜伽柱', 'ac4.d': '可充电震动瑜伽柱，专业级肌肉恢复。',
    'ac5.t': '迷你瑜伽球（25cm）', 'ac5.d': '25 cm 防滑小球，普拉提、康复与核心训练。',
    'ac6.t': '瑜伽球（1700g）', 'ac6.d': '1700 g 防爆瑜伽/健身球，孕产与日常训练通用。',
    'ac7.t': '按摩球', 'ac7.d': '筋膜按摩球，舒缓肩、背、腰、脚底酸痛。',
    'ac8.t': '弹力带', 'ac8.d': '弹力带 / 拉力带，练力、拉伸与翘臀训练。',
    'ac9.t': '握力圈', 'ac9.d': '硅胶握力圈，锻炼手部与前臂力量。',
    'ac10.t': '瑜伽鞋', 'ac10.d': '轻量防滑室内训练鞋，瑜伽与舞蹈通用。',
    'fi1.t': '哑铃 / 壶铃套装', 'fi1.d': '家用轻训哑铃 & 壶铃套装（6 kg / 2 kg），便携塑形健身器材。',

    'spec.title': '规格一览',
    'spec.sub': '常见尺寸与起订量速查。支持定制尺寸、颜色与包装。',
    'spec1.t': 'TPE 瑜伽垫', 'spec1.d': '1830×610 / 1830×800 / 1850×900 / 2000×1000 / 1850×1220 mm\n厚度 4–12 mm\n起订量 100 片',
    'spec2.t': '加宽 / 双人 TPE 垫', 'spec2.d': '80 cm / 122 cm 宽度\n环保双层 TPE\n起订量 100 片',
    'spec3.t': 'PU / 橡胶垫', 'spec3.d': '天然橡胶底 + PU 防滑面\n1830×610 / 1850×800 mm\n起订量 面议',
    'spec4.t': 'PVC 瑜伽垫', 'spec4.d': '耐用 PVC 材质\n61 / 80 / 122 cm 宽度\n起订友好',
    'spec5.t': '瑜伽砖（EVA）', 'spec5.d': '高密度 EVA\n标准 9×15×23 cm\n起订量 500 块',
    'spec6.t': '瑜伽柱', 'spec6.d': '25×7.5 至 45×14 cm\n光面 / 狼牙 / 实心\n起订量 500 个',
    'spec7.t': '瑜伽 / 健身球', 'spec7.d': '25 cm 迷你 / 1700 g 标准\n防爆设计\n起订量 面议',
    'spec8.t': '弹力带 / 握力器', 'spec8.d': '弹力带与硅胶握力圈\n多档阻力\n起订量 面议',

    'about.title': '关于三梵',
    'about.sub': '全球品牌信赖的瑜伽与健身器材源头工厂。',
    'about.h1': '厦门三梵体育用品有限公司',
    'about.p1': '三梵成立于 2013 年，总部位于福建厦门，是领先的瑜伽垫及运动用品 OEM/ODM 制造商，制造基地坐落于中国体育用品制造重镇 — 泉州晋江。',
    'about.p2': '我们为全球客户提供设计、研发、制造与出口的一体化定制服务，产品涵盖瑜伽垫、瑜伽柱、瑜伽砖、运动服饰、毛巾、健身球及丰富的健身小器材。',
    'about.p3': '600+ 熟练工人与高精设备，保证高产出、高品质与准时交付，且价格具竞争力。我们的服务团队 24 小时待命，随时响应客户需求。',
    'about.cap.title': '核心能力',
    'about.cap.l1': '材料配方与产品研发',
    'about.cap.l2': '尺寸、厚度、颜色与表面工艺定制',
    'about.cap.l3': 'Logo 印刷、压印及包装设计',
    'about.cap.l4': '内部质检与批次可追溯',
    'about.cap.t1': '材料与研发', 'about.cap.t2': '定制工艺', 'about.cap.t3': '品牌与包装', 'about.cap.t4': '质量控制',

    'contact.title': '联系我们',
    'contact.sub': '告诉我们你的需求，1 个工作日内回复。',
    'contact.info.title': '联系方式',
    'c.addr.label': '地址', 'c.email.label': '邮箱', 'c.phone.label': 'WhatsApp', 'c.hours.label': '服务',
    'form.name': '姓名', 'form.company': '公司', 'form.email': '邮箱',
    'form.product': '意向产品', 'form.qty': '预估数量',
    'form.msg': '留言', 'form.send': '发送询盘', 'form.note': '我们绝不会泄露你的信息。',
    'form.ok': '已收到！我们将在 1 个工作日内回复。',
    'form.fail': '发送失败，请直接邮件联系我们。',
    'form.opt.yoga': '瑜伽垫', 'form.opt.acc': '瑜伽 & 普拉提配件',
    'form.opt.fit': '健身器材', 'form.opt.other': '其他 / 不确定',

    'f.home': '首页', 'f.products': '产品', 'f.about': '关于', 'f.contact': '联系',
    'f.brand': '三梵 SANFAN', 'f.tag': '瑜伽 & 健身器材 OEM / ODM 制造工厂。',
    'foot.products': '产品', 'foot.company': '公司', 'foot.contact': '联系',
    'foot.addr': '地址', 'foot.email': '邮箱', 'foot.phone': 'WhatsApp',
    'foot.copyright': '© 2026 厦门三梵体育用品有限公司 版权所有。',

    'cta.title': '准备好打造你的品牌了吗？',
    'cta.sub': '立即获取专属报价与免费样品。',
    'cta.btn': '联系我们',
  }
};

function applyLang(lang) {
  document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (I18N[lang][key] != null) {
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
