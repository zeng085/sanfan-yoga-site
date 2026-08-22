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
    'hero.title': 'FUJIAN SANFAN — Your Direct Factory for Yoga & Fitness Gear',
    'hero.lead': 'Since 2013, a leading OEM/ODM manufacturer of yoga mats, aerial yoga hammocks, yoga props, foam rollers, resistance bands and fitness equipment. 600+ skilled workers, monthly capacity of 200,000+ yoga mats, 24-hour service team. MOQ from 100 pcs, 7-day sampling.',
    'hero.cta1': 'Request a Quote', 'hero.cta2': 'Explore Products',
    'hero.stat1.n': '2013', 'hero.stat1.l': 'Established',
    'hero.stat2.n': '600+', 'hero.stat2.l': 'Skilled Workers',
    'hero.stat3.n': '200K+', 'hero.stat3.l': 'Mats / Month',
    'hero.stat4.n': '24/7', 'hero.stat4.l': 'Service Team',
    'hero.media': 'SANFAN factory',

    // Why choose us
    'str.title': 'Why Buyers Choose SANFAN',
    'str.sub': 'A flexible supply chain engineered for private-label success.',
    'str1.t': 'Low MOQ', 'str1.d': 'TPE mats from 100 pcs; foam rollers from 500 pcs; most accessories from 500–1,000 pcs. Test the market without heavy inventory risk.',
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

    // Product range (5 cards)
    'range.title': 'Our Product Range',
    'range.sub': 'From yoga essentials to full fitness lines — all factory-direct and customizable.',
    'range1.t': 'Yoga Mats', 'range1.s': 'TPE · PU/Rubber · Foldable', 'range1.alt': 'Yoga mat collection',
    'range2.t': 'Yoga Props & Accessories', 'range2.s': 'Aerial Yoga · Wheel · Blocks · Cushion · Knee Pad', 'range2.alt': 'Yoga props and accessories',
    'range3.t': 'Foam Rollers & Massage', 'range3.s': 'Rollers · Electric Roller · Massage Ball', 'range3.alt': 'Foam rollers',
    'range4.t': 'Resistance Bands & Pilates', 'range4.s': 'Bands · Yoga Balls · Balance Board', 'range4.alt': 'Resistance bands and pilates gear',
    'range5.t': 'Fitness Equipment', 'range5.s': 'Dumbbells · Kettlebells · Jump Rope', 'range5.alt': 'Fitness equipment',

    // Full gallery
    'gallery.title': 'Full Product Gallery',
    'gallery.sub': 'Every category we manufacture — ready for OEM, ODM and private label.',
    'gallery.note': 'Every photo is a real shot from our Alibaba.com international factory store — the exact products we make and ship.',
    'g1.n': 'TPE Yoga Mat', 'g1.s': 'Eco double-layer, 4–12 mm',
    'g2.n': 'Wide TPE Yoga Mat', 'g2.s': 'Extra-wide 80/122 cm',
    'g3.n': 'Double-wide TPE Mat', 'g3.s': 'Wide format for 2 persons',
    'g4.n': 'Foldable TPE Yoga Mat', 'g4.s': 'Tri-fold, ultra-portable',
    'g5.n': 'PU / Rubber Premium Mat', 'g5.s': 'Premium grip',
    'g6.n': 'Frosted PU Yoga Mat', 'g6.s': 'Matte frosted surface',
    'g7.n': 'Camo PU Yoga Mat', 'g7.s': 'Bold camo print',
    'g8.n': 'Balance Trainer', 'g8.s': 'Half-ball balance trainer',
    'g9.n': 'Aerial Yoga Hammock', 'g9.s': 'Anti-gravity silk',
    'g10.n': 'Aerial Yoga Set', 'g10.s': 'Silk + mount kit',
    'g11.n': 'Yoga Wheel', 'g11.s': 'Backbend & stretch',
    'g12.n': 'Meditation Cushion', 'g12.s': 'Zafu, buckwheat fill',
    'g13.n': 'Yoga Blocks (EVA)', 'g13.s': 'High-density EVA',
    'g14.n': 'Knee Pad', 'g14.s': 'Thick kneeling cushion',
    'g15.n': 'Foam Roller (Wolf-tooth)', 'g15.s': 'EVA wolf-tooth texture',
    'g16.n': 'Solid Foam Roller', 'g16.s': 'Solid EVA core',
    'g17.n': 'Electric Foam Roller', 'g17.s': 'Rechargeable vibration',
    'g18.n': 'Massage Ball', 'g18.s': 'Fascia relief',
    'g19.n': 'Resistance Band', 'g19.s': 'Multi-tension',
    'g20.n': 'Mini Yoga Ball (25 cm)', 'g20.s': '25 cm anti-slip',
    'g21.n': 'Yoga / Fitness Ball', 'g21.s': 'Anti-burst training ball',
    'g22.n': 'Balance Board', 'g22.s': 'Wooden balance board',
    'g23.n': 'Mini Stepper', 'g23.s': 'Compact home stepper',
    'g24.n': 'Kettlebell', 'g24.s': 'Functional strength',
    'g25.n': 'Jump Rope', 'g25.s': 'Ball-bearing speed rope',
    'g26.n': 'Home Stepper', 'g26.s': 'Cardio stepper machine',

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
    'prod.sub': 'Yoga mats, aerial yoga, yoga props, foam rollers, resistance bands and fitness equipment — all factory-direct and customizable.',
    'prod.nav.title': 'Categories',
    'cat.yoga.title': 'Yoga Mats', 'cat.yoga.sub': 'TPE · PU/Rubber · Foldable',
    'cat.props.title': 'Yoga Props & Accessories', 'cat.props.sub': 'Aerial Yoga · Wheel · Blocks · Cushion · Knee Pad',
    'cat.rollers.title': 'Foam Rollers & Massage', 'cat.rollers.sub': 'Rollers · Electric Roller · Massage Ball',
    'cat.bands.title': 'Resistance Bands & Pilates', 'cat.bands.sub': 'Bands · Yoga Balls · Balance Board',
    'cat.fit.title': 'Fitness Equipment', 'cat.fit.sub': 'Dumbbells · Kettlebells · Jump Rope',
    'ym1.t': 'TPE Yoga Mat', 'ym1.d': 'Eco double-layer TPE, non-slip textured surface, widths 61–122 cm, thickness 4–12 mm. Solid, economy and special grades.',
    'ym2.t': 'Wide TPE Yoga Mat', 'ym2.d': 'Extra-wide 80/122 cm TPE mat for dynamic and partner practice; same eco double-layer grip.',
    'ym3.t': 'Double-wide TPE Mat', 'ym3.d': 'Wide-format TPE mat for couples and family use; non-slip, easy to clean.',
    'ym4.t': 'Foldable TPE Yoga Mat', 'ym4.d': 'Tri-fold design opens flat with no curl; 6 mm cushioning; ultra-portable, packs into a backpack.',
    'ym5.t': 'PU / Rubber Premium Mat', 'ym5.d': 'Natural rubber base + PU anti-slip top; premium grip for hot yoga and studios (the "premium" mat).',
    'ym6.t': 'Frosted PU Yoga Mat', 'ym6.d': 'Matte frosted PU surface, elegant feel, high sweat-absorption grip for intense sessions.',
    'ym7.t': 'Camo PU Yoga Mat', 'ym7.d': 'Camouflage-print PU rubber mat with a bold look, ideal for branded lines.',
    'ym8.t': 'Balance Trainer', 'ym8.d': 'Half-ball balance trainer for core stability, rehab and functional training; custom colors and resistance levels.',
    'pr1.t': 'Aerial Yoga Hammock', 'pr1.d': 'Anti-gravity aerial yoga hammock in high-strength silk; ceiling mount kit available; custom colors and lengths for aerial yoga and flying pilates.',
    'pr2.t': 'Yoga Wheel', 'pr2.d': 'ABS inner core with TPE cushioning; deepens backbends, stretches shoulders and opens the chest; custom colors.',
    'pr3.t': 'Meditation Cushion (Zafu)', 'pr3.d': 'Zafu meditation cushion with buckwheat fill and cotton cover; round and rectangular styles, custom fabrics.',
    'pr4.t': 'Yoga Blocks (EVA)', 'pr4.d': 'High-density EVA blocks; stable support for poses and stretches, multiple colors.',
    'pr5.t': 'Knee Pad', 'pr5.d': 'Thick kneeling knee pad for yoga, gardening and floor work; shock-absorbing, non-slip base.',
    'fr1.t': 'Yoga Foam Roller (Wolf-tooth)', 'fr1.d': 'EVA foam roller with wolf-tooth texture; 45 cm muscle recovery and myofascial release.',
    'fr2.t': 'Solid Foam Roller', 'fr2.d': 'Solid EVA roller for deep-tissue massage and core training.',
    'fr3.t': 'Electric Foam Roller', 'fr3.d': 'Rechargeable vibrating foam roller for professional recovery.',
    'fr4.t': 'EVA Massage Rollers', 'fr4.d': 'Multiple textures and sizes — smooth, grid and half-roller options; custom colors and hardness.',
    'fr5.t': 'Massage Ball', 'fr5.d': 'Fascia massage ball for shoulders, back, waist and foot relief.',
    'rb1.t': 'Resistance Bands', 'rb1.d': 'Latex and fabric resistance bands — loops, tubes and figure-8 styles; multiple tensions, custom colors and prints.',
    'rb2.t': 'Mini Yoga Ball (25 cm)', 'rb2.d': '25 cm anti-slip gymnastic ball for pilates, rehab and core work.',
    'rb3.t': 'Balance Dome', 'rb3.d': 'BOSU-style balance dome for core strength, stability and rehab; anti-slip base, custom colors.',
    'rb4.t': 'Balance Board', 'rb4.d': 'Wooden balance board with non-slip surface for stability, coordination and rehab training.',
    'fi1.t': 'Mini Stepper', 'fi1.d': 'Compact home stepper for cardio and lower-body training; adjustable resistance, small footprint.',
    'fi2.t': 'Kettlebell', 'fi2.d': 'Coated kettlebell for swings, squats and functional strength training; custom weights and colors.',
    'fi3.t': 'Jump Rope', 'fi3.d': 'Speed jump rope with ball-bearing handles; adjustable length, custom grips and colors.',
    'fi4.t': 'Home Stepper', 'fi4.d': 'Home cardio stepper with hydraulic resistance; low-impact workout, custom branding available.',
    'fi5.t': 'Dumbbell / Kettlebell Set', 'fi5.d': 'Home light-training dumbbell & kettlebell set (6 kg / 2 kg), portable shaping fitness gear.',

    // Spec overview
    'spec.title': 'Specification Overview',
    'spec.sub': 'Popular sizes and MOQs at a glance. Custom sizes, colors and packaging available on request.',
    'spec1.t': 'TPE Yoga Mat', 'spec1.d': '1830×610 / 1830×800 / 1850×900 / 2000×1000 / 1850×1220 mm\nThickness 4–12 mm\nMOQ 100 pcs',
    'spec2.t': 'Wide / Double TPE Mat', 'spec2.d': '80 cm / 122 cm widths\nEco double-layer TPE\nMOQ 100 pcs',
    'spec3.t': 'PU / Rubber Mat', 'spec3.d': 'Natural rubber base + PU anti-slip top\n1830×610 / 1850×800 mm\nMOQ on request',
    'spec4.t': 'Balance Trainer', 'spec4.d': 'Half-ball balance trainer\nAnti-slip base\nCustom colors\nMOQ on request',
    'spec5.t': 'Aerial Yoga Hammock', 'spec5.d': 'High-strength aerial silk\nCeiling mount kit available\nCustom colors & sizes\nMOQ on request',
    'spec6.t': 'Yoga Wheel', 'spec6.d': 'ABS core + TPE cushion\n33 / 38 cm diameters\nCustom colors\nMOQ on request',
    'spec7.t': 'Yoga Blocks (EVA)', 'spec7.d': 'High-density EVA\n9×15×23 cm standard\nMOQ 500 pcs',
    'spec8.t': 'Yoga Foam Roller', 'spec8.d': '25×7.5 to 45×14 cm\nSmooth / wolf-tooth / solid\nMOQ 500 pcs',
    'spec9.t': 'Yoga / Fitness Ball', 'spec9.d': '25 cm mini / standard sizes\nAnti-burst\nMOQ on request',
    'spec10.t': 'Resistance Bands', 'spec10.d': 'Latex & fabric bands\nLoops / tubes / figure-8\nMultiple tensions\nMOQ on request',
    'spec11.t': 'Balance Pad / Knee Pad', 'spec11.d': 'TPE balance & knee pads\nCustom sizes & colors\nMOQ on request',
    'spec12.t': 'Fitness Gear', 'spec12.d': 'Dumbbells · Kettlebells\nJump Ropes · Steppers\nMultiple weights & colors\nMOQ on request',

    // About
    'about.title': 'About SANFAN',
    'about.sub': 'A yoga & fitness equipment source factory trusted by brands worldwide.',
    'about.h1': 'FUJIAN SANFAN Sports Products Co., Ltd.',
    'about.p1': 'Founded in 2013 and based in Xiamen, Fujian, SANFAN is a leading OEM/ODM manufacturer of yoga mats and sports products, with our manufacturing base in Jinjiang — the heart of China’s sporting-goods belt.',
    'about.p2': 'We provide customized designing, developing, manufacturing and exporting for customers worldwide. Our range covers yoga mats, aerial yoga hammocks, yoga wheels, foam rollers, blocks, balls, resistance bands and a broad selection of fitness gear.',
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
    'form.opt.yoga': 'Yoga Mats', 'form.opt.props': 'Yoga Props & Accessories',
    'form.opt.rollers': 'Foam Rollers & Massage', 'form.opt.bands': 'Resistance Bands & Pilates',
    'form.opt.fit': 'Fitness Equipment', 'form.opt.other': 'Other / Not sure',

    // Footer
    'f.home': 'Home', 'f.products': 'Products', 'f.about': 'About', 'f.contact': 'Contact',
    'f.brand': 'SANFAN', 'f.tag': 'OEM / ODM yoga & fitness manufacturer.',
    'foot.products': 'Products', 'foot.company': 'Company', 'foot.contact': 'Contact',
    'foot.addr': 'Address', 'foot.email': 'Email', 'foot.phone': 'WhatsApp',
    'foot.copyright': '© 2026 FUJIAN SANFAN Sports Products Co., Ltd. All rights reserved.',

    // CTA
    'cta.title': 'Ready to Build Your Brand?',
    'cta.sub': 'Get a tailored quote and free samples today.',
    'cta.btn': 'Contact Our Team',

    // Product detail page
    'pd.back': 'Back to Products',
    'pd.specs': 'Specifications',
    'pd.features': 'Key Features',
    'pd.custom': 'Customization & OEM/ODM',
    'pd.related': 'Related Products',
    'pd.overview': 'Product Overview',
    'pd.whatsapp': 'Chat on WhatsApp',
    'pd.quote': 'Request a Quote',
    'pd.notfound': 'Product not found',
    'pd.notfound.d': 'The product you are looking for does not exist.',
    'pd.material': 'Material', 'pd.size': 'Size', 'pd.thickness': 'Thickness',
    'pd.moq': 'MOQ', 'pd.colors': 'Colors & Print', 'pd.cert': 'Compliance', 'pd.packing': 'Packaging',
    'pd.custom.d': 'Full OEM/ODM support: material, size, thickness, color, double-color, logo printing, embossing and packaging. Physical samples ready in 7 days with your spec.',
    'pd.brand': 'Branding',
  },

  zh: {
    'nav.home': '首页', 'nav.products': '产品', 'nav.about': '关于',
    'nav.contact': '联系', 'nav.quote': '获取报价',

    'hero.eyebrow': '瑜伽 & 健身器材 OEM / ODM 制造工厂',
    'hero.title': '福建三梵 — 你的瑜伽与健身器材直供工厂',
    'hero.lead': '自 2013 年起，三梵是领先的瑜伽垫、空中瑜伽吊床、瑜伽道具、瑜伽柱、弹力带及健身器材 OEM/ODM 制造商。600+ 熟练工人，瑜伽垫月产能 20 万+，24 小时服务团队。100 片起订，7 天打样。',
    'hero.cta1': '立即询价', 'hero.cta2': '浏览产品',
    'hero.stat1.n': '2013', 'hero.stat1.l': '成立年份',
    'hero.stat2.n': '600+', 'hero.stat2.l': '熟练工人',
    'hero.stat3.n': '20万+', 'hero.stat3.l': '垫子/月',
    'hero.stat4.n': '24/7', 'hero.stat4.l': '服务团队',
    'hero.media': '三梵工厂',

    'str.title': '为什么选择三梵',
    'str.sub': '为贴牌成功而生的柔性供应链。',
    'str1.t': '低起订量', 'str1.d': 'TPE 瑜伽垫 100 片起订；瑜伽柱 500 个起订；其余配件 500–1,000 件起订。小批量试水无库存压力。',
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
    'range1.t': '瑜伽垫', 'range1.s': 'TPE · PU/橡胶 · 折叠', 'range1.alt': '瑜伽垫系列',
    'range2.t': '瑜伽道具与配件', 'range2.s': '空中瑜伽 · 瑜伽轮 · 瑜伽砖 · 冥想坐垫 · 膝盖垫', 'range2.alt': '瑜伽道具与配件',
    'range3.t': '瑜伽柱与按摩', 'range3.s': '狼牙柱 · 电动柱 · 按摩球', 'range3.alt': '瑜伽柱',
    'range4.t': '弹力带与普拉提', 'range4.s': '弹力带 · 瑜伽球 · 平衡垫', 'range4.alt': '弹力带与普拉提',
    'range5.t': '健身器材', 'range5.s': '哑铃 · 壶铃 · 跳绳', 'range5.alt': '健身器材',

    'gallery.title': '全产品图库',
    'gallery.sub': '我们生产的每一个品类，均支持 OEM、ODM 与贴牌定制。',
    'gallery.note': '每一张都是来自我们阿里巴巴国际站工厂店的真实产品图 — 正是我们目前在做的品类。',
    'g1.n': 'TPE 瑜伽垫', 'g1.s': '环保双层，4–12 mm',
    'g2.n': '加宽 TPE 瑜伽垫', 'g2.s': '80/122 cm 加宽',
    'g3.n': '双人加宽 TPE 垫', 'g3.s': '双人加宽版',
    'g4.n': '折叠 TPE 瑜伽垫', 'g4.s': '三折超便携',
    'g5.n': 'PU / 橡胶高端垫', 'g5.s': '高端防滑',
    'g6.n': '磨砂 PU 瑜伽垫', 'g6.s': '磨砂 PU 表面',
    'g7.n': '迷彩 PU 瑜伽垫', 'g7.s': '硬朗迷彩印花',
    'g8.n': '平衡训练器', 'g8.s': '半圆平衡球',
    'g9.n': '空中瑜伽吊床', 'g9.s': '反重力空中丝绸',
    'g10.n': '空中瑜伽套装', 'g10.s': '丝绸 + 挂件套装',
    'g11.n': '瑜伽轮', 'g11.s': '后弯与开肩',
    'g12.n': '冥想坐垫', 'g12.s': '荞麦填充 Zafu',
    'g13.n': '瑜伽砖（EVA）', 'g13.s': '高密度 EVA',
    'g14.n': '膝盖垫', 'g14.s': '加厚跪姿缓冲',
    'g15.n': '狼牙瑜伽柱', 'g15.s': 'EVA 狼牙齿纹',
    'g16.n': '实心瑜伽柱', 'g16.s': '实心 EVA',
    'g17.n': '电动瑜伽柱', 'g17.s': '可充电震动',
    'g18.n': '按摩球', 'g18.s': '筋膜放松',
    'g19.n': '弹力带', 'g19.s': '多档阻力',
    'g20.n': '迷你瑜伽球（25cm）', 'g20.s': '25 cm 防滑',
    'g21.n': '瑜伽 / 健身球', 'g21.s': '防爆训练球',
    'g22.n': '平衡垫', 'g22.s': 'TPE 稳定性训练垫',
    'g23.n': '硅胶哑铃', 'g23.s': '防滚不伤地板',
    'g24.n': '壶铃', 'g24.s': '功能性力量训练',
    'g25.n': '跳绳', 'g25.s': '轴承竞速跳绳',
    'g26.n': '家用踏步机', 'g26.s': '有氧踏步训练',

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
    'prod.sub': '瑜伽垫、空中瑜伽、瑜伽道具、瑜伽柱、弹力带与健身器材 — 全部工厂直供、可定制。',
    'prod.nav.title': '产品分类',
    'cat.yoga.title': '瑜伽垫', 'cat.yoga.sub': 'TPE · PU/橡胶 · 折叠',
    'cat.props.title': '瑜伽道具与配件', 'cat.props.sub': '空中瑜伽 · 瑜伽轮 · 瑜伽砖 · 冥想坐垫 · 膝盖垫',
    'cat.rollers.title': '瑜伽柱与按摩', 'cat.rollers.sub': '狼牙柱 · 电动柱 · 按摩球',
    'cat.bands.title': '弹力带与普拉提', 'cat.bands.sub': '弹力带 · 瑜伽球 · 平衡垫',
    'cat.fit.title': '健身器材', 'cat.fit.sub': '哑铃 · 壶铃 · 跳绳',
    'ym1.t': 'TPE 瑜伽垫', 'ym1.d': '环保双层 TPE，防滑纹理表面，宽度 61–122 cm，厚度 4–12 mm。可选实重、经济、特供等级。',
    'ym2.t': '加宽 TPE 瑜伽垫', 'ym2.d': '80/122 cm 加宽 TPE 垫，适合流瑜伽与双人练习；同样环保双层抓地。',
    'ym3.t': '双人加宽 TPE 垫', 'ym3.d': '加宽版 TPE 垫，适合情侣与家庭使用；防滑、易清洁。',
    'ym4.t': '折叠 TPE 瑜伽垫', 'ym4.d': '三折设计平铺不卷边；6 mm 缓冲；超便携，可塞入背包。',
    'ym5.t': 'PU / 橡胶高端垫', 'ym5.d': '天然橡胶底 + PU 防滑面；高温瑜伽与瑜伽馆高端抓地（"土豪垫"）。',
    'ym6.t': '磨砂 PU 瑜伽垫', 'ym6.d': '磨砂 PU 表面，触感高级，高强度下吸汗抓地更稳。',
    'ym7.t': '迷彩 PU 瑜伽垫', 'ym7.d': '迷彩印花 PU 橡胶垫，外观硬朗，适合做品牌定制线。',
    'ym8.t': '平衡训练器', 'ym8.d': '半圆平衡球训练器，核心稳定、康复与功能性训练；颜色与阻力可定制。',
    'pr1.t': '空中瑜伽吊床', 'pr1.d': '高强度丝绸反重力空中瑜伽吊床，可配天花板挂件套装；颜色与长度均可定制，适用空中瑜伽与飞行普拉提。',
    'pr2.t': '瑜伽轮', 'pr2.d': 'ABS 内芯 + TPE 缓冲；加深后弯、开肩扩胸；颜色可定制。',
    'pr3.t': '冥想坐垫（Zafu）', 'pr3.d': '荞麦填充 Zafu 冥想坐垫，棉质外套；圆形/长方形可选，面料可定制。',
    'pr4.t': '瑜伽砖（EVA）', 'pr4.d': '高密度 EVA 瑜伽砖；稳定支撑体式与拉伸，多色可选。',
    'pr5.t': '膝盖垫', 'pr5.d': '加厚跪姿膝盖垫，瑜伽、园艺与地板作业通用；减震缓冲、底部防滑。',
    'fr1.t': '狼牙瑜伽柱', 'fr1.d': 'EVA 狼牙齿纹瑜伽柱；45 cm 肌肉放松与筋膜放松。',
    'fr2.t': '实心瑜伽柱', 'fr2.d': '实心 EVA 瑜伽柱，深层按摩与核心训练。',
    'fr3.t': '电动瑜伽柱', 'fr3.d': '可充电震动瑜伽柱，专业级肌肉恢复。',
    'fr4.t': 'EVA 按摩柱', 'fr4.d': '多种纹路与规格 — 光面、网格、半柱可选；颜色与硬度可定制。',
    'fr5.t': '按摩球', 'fr5.d': '筋膜按摩球，舒缓肩、背、腰、脚底酸痛。',
    'rb1.t': '弹力带', 'rb1.d': '乳胶与织布弹力带 — 环形、管状与 8 字型；多档阻力，颜色与印花可定制。',
    'rb2.t': '迷你瑜伽球（25cm）', 'rb2.d': '25 cm 防滑小球，普拉提、康复与核心训练。',
    'rb3.t': '瑜伽 / 健身球', 'rb3.d': '防爆瑜伽健身球，核心、平衡与日常训练通用。',
    'rb4.t': '平衡垫', 'rb4.d': 'TPE 平衡垫，稳定性训练、康复与普拉提；尺寸颜色可定制。',
    'fi1.t': '硅胶哑铃', 'fi1.d': '硅胶包胶哑铃，防滚不伤地板；多重量多色可选，适合家用与健身房产品线。',
    'fi2.t': '壶铃', 'fi2.d': '包胶壶铃，甩摆、深蹲与功能性力量训练；重量与颜色可定制。',
    'fi3.t': '跳绳', 'fi3.d': '轴承竞速跳绳，长度可调；握柄与颜色可定制。',
    'fi4.t': '家用踏步机', 'fi4.d': '液压阻力家用踏步机，低冲击有氧训练；可定制品牌标识。',
    'fi5.t': '哑铃 / 壶铃套装', 'fi5.d': '家用轻训哑铃 & 壶铃套装（6 kg / 2 kg），便携塑形健身器材。',

    'spec.title': '规格一览',
    'spec.sub': '常见尺寸与起订量速查。支持定制尺寸、颜色与包装。',
    'spec1.t': 'TPE 瑜伽垫', 'spec1.d': '1830×610 / 1830×800 / 1850×900 / 2000×1000 / 1850×1220 mm\n厚度 4–12 mm\n起订量 100 片',
    'spec2.t': '加宽 / 双人 TPE 垫', 'spec2.d': '80 cm / 122 cm 宽度\n环保双层 TPE\n起订量 100 片',
    'spec3.t': 'PU / 橡胶垫', 'spec3.d': '天然橡胶底 + PU 防滑面\n1830×610 / 1850×800 mm\n起订量 面议',
    'spec4.t': '平衡训练器', 'spec4.d': '半圆平衡球\n防滑底座\n颜色可定制\n起订量 面议',
    'spec5.t': '空中瑜伽吊床', 'spec5.d': '高强度空中丝绸\n可配天花板挂件\n颜色尺寸可定制\n起订量 面议',
    'spec6.t': '瑜伽轮', 'spec6.d': 'ABS 内芯 + TPE 缓冲\n直径 33 / 38 cm\n颜色可定制\n起订量 面议',
    'spec7.t': '瑜伽砖（EVA）', 'spec7.d': '高密度 EVA\n标准 9×15×23 cm\n起订量 500 块',
    'spec8.t': '瑜伽柱', 'spec8.d': '25×7.5 至 45×14 cm\n光面 / 狼牙 / 实心\n起订量 500 个',
    'spec9.t': '瑜伽 / 健身球', 'spec9.d': '25 cm 迷你 / 标准尺寸\n防爆设计\n起订量 面议',
    'spec10.t': '弹力带', 'spec10.d': '乳胶与织布材质\n环形 / 管状 / 8 字型\n多档阻力\n起订量 面议',
    'spec11.t': '平衡垫 / 膝盖垫', 'spec11.d': 'TPE 平衡垫与膝盖垫\n尺寸颜色可定制\n起订量 面议',
    'spec12.t': '健身器材', 'spec12.d': '哑铃 · 壶铃\n跳绳 · 踏步机\n多重量多色可选\n起订量 面议',

    'about.title': '关于三梵',
    'about.sub': '全球品牌信赖的瑜伽与健身器材源头工厂。',
    'about.h1': '福建三梵体育用品有限公司',
    'about.p1': '三梵成立于 2013 年，总部位于福建厦门，是领先的瑜伽垫及运动用品 OEM/ODM 制造商，制造基地坐落于中国体育用品制造重镇 — 泉州晋江。',
    'about.p2': '我们为全球客户提供设计、研发、制造与出口的一体化定制服务，产品涵盖瑜伽垫、空中瑜伽吊床、瑜伽轮、瑜伽柱、瑜伽砖、瑜伽球、弹力带及丰富的健身器材。',
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
    'form.opt.yoga': '瑜伽垫', 'form.opt.props': '瑜伽道具与配件',
    'form.opt.rollers': '瑜伽柱与按摩', 'form.opt.bands': '弹力带与普拉提',
    'form.opt.fit': '健身器材', 'form.opt.other': '其他 / 不确定',

    'f.home': '首页', 'f.products': '产品', 'f.about': '关于', 'f.contact': '联系',
    'f.brand': '三梵 SANFAN', 'f.tag': '瑜伽 & 健身器材 OEM / ODM 制造工厂。',
    'foot.products': '产品', 'foot.company': '公司', 'foot.contact': '联系',
    'foot.addr': '地址', 'foot.email': '邮箱', 'foot.phone': 'WhatsApp',
    'foot.copyright': '© 2026 福建三梵体育用品有限公司 版权所有。',

    'cta.title': '准备好打造你的品牌了吗？',
    'cta.sub': '立即获取专属报价与免费样品。',
    'cta.btn': '联系我们',

    // 产品详情页
    'pd.back': '返回产品',
    'pd.specs': '规格参数',
    'pd.features': '核心卖点',
    'pd.custom': '定制与 OEM/ODM',
    'pd.related': '相关产品',
    'pd.overview': '产品概述',
    'pd.whatsapp': 'WhatsApp 咨询',
    'pd.quote': '获取报价',
    'pd.notfound': '未找到产品',
    'pd.notfound.d': '你访问的产品不存在。',
    'pd.material': '材质', 'pd.size': '尺寸', 'pd.thickness': '厚度',
    'pd.moq': '起订量', 'pd.colors': '颜色与印花', 'pd.cert': '合规认证', 'pd.packing': '包装',
    'pd.custom.d': '全面支持 OEM/ODM：材质、尺寸、厚度、颜色、双色、logo 印刷、压印及包装均可定制。7 天按你的规格出实物样品。',
    'pd.brand': '品牌定制',
  }
};
window.I18N = I18N;

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
  window.dispatchEvent(new Event('sanfan-langchange'));
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
