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
    'range1.t': 'Yoga Mats', 'range1.s': 'TPE · Cork · PU · NBR · Alignment · Foldable', 'range1.alt': 'Yoga mat collection',
    'range2.t': 'Yoga & Pilates Accessories', 'range2.s': 'Rollers · Blocks · Wheels · Balls · Straps · Towels', 'range2.alt': 'Yoga accessories',
    'range3.t': 'Fitness Equipment', 'range3.s': 'Dumbbells · Barbells · Grips · Racks · Weights', 'range3.alt': 'Fitness equipment',

    // Full gallery
    'gallery.title': 'Full Product Gallery',
    'gallery.sub': 'Every category we manufacture — ready for OEM, ODM and private label.',
    'gallery.note': 'Some images are illustrative references. Contact us for real factory photos and free samples.',
    'g1.n': 'TPE Yoga Mat', 'g1.s': 'Eco double-layer, 4–12 mm',
    'g2.n': 'Alignment Yoga Mat', 'g2.s': 'Posture guide lines',
    'g3.n': 'NBR Yoga Mat', 'g3.s': 'High-elastic, 0.8–2 cm',
    'g4.n': 'Yoga Foam Roller', 'g4.s': 'Smooth / textured',
    'g5.n': 'PU / Rubber Mat', 'g5.s': 'Premium grip',
    'g6.n': 'Suede / Velvet Mat', 'g6.s': 'Soft microfiber',
    'g7.n': 'Foldable Travel Mat', 'g7.s': 'Tri-fold, portable',
    'g8.n': 'Cork Yoga Mat', 'g8.s': 'Natural cork grip',
    'g9.n': 'Yoga Wheel', 'g9.s': 'Back & core',
    'g10.n': 'Yoga Blocks', 'g10.s': 'EVA / cork',
    'g11.n': 'Massage Series', 'g11.s': 'Deep tissue relief',
    'g12.n': 'Half Balance Ball', 'g12.s': 'BOSU / balance',
    'g13.n': 'Balance Pad', 'g13.s': 'Stability trainer',
    'g14.n': 'Bath / Non-slip Mat', 'g14.s': 'Suction, home use',
    'g15.n': 'Yoga / Exercise Ball', 'g15.s': 'Anti-burst',
    'g16.n': 'Hex Dumbbell', 'g16.s': 'Rubber coated',
    'g17.n': 'Beam Barbell', 'g17.s': 'Silicone bar',
    'g18.n': 'Hand Grip Strengthener', 'g18.s': '5–60 kg adjustable',
    'g19.n': 'Wearable Weights', 'g19.s': 'Wrist & ankle',
    'g20.n': 'Yoga Mat Rack', 'g20.s': 'Holds 25 mats',
    'g21.n': 'Training Stick', 'g21.s': 'Stretch & posture',

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
    'cat.yoga.title': 'Yoga Mats', 'cat.yoga.sub': 'TPE · Cork · PU · NBR · Alignment · Foldable',
    'cat.acc.title': 'Yoga & Pilates Accessories', 'cat.acc.sub': 'Rollers · Blocks · Wheels · Balls · Straps · Towels',
    'cat.fit.title': 'Fitness Equipment', 'cat.fit.sub': 'Dumbbells · Barbells · Grips · Racks · Weights',
    'ym1.t': 'TPE Yoga Mat', 'ym1.d': 'Eco double-layer TPE, non-slip textured surface, widths 61–122 cm, thickness 4–12 mm. Solid, economy and special grades.',
    'ym2.t': 'Foldable TPE Yoga Mat', 'ym2.d': 'Tri-fold design opens flat with no curl; 6 mm cushioning; ultra-portable, packs into a backpack.',
    'ym3.t': 'Folding Cork Rubber Yoga Mat', 'ym3.d': '100% natural cork top + rubber base; renewable, moisture-resistant, high friction.',
    'ym4.t': 'Alignment Yoga Mat', 'ym4.d': 'Lotus-printed guide lines for correct posture; TPE base, 61/80 cm widths.',
    'ym5.t': 'Custom-logo Wall-mount Yoga Mat', 'ym5.d': '8 mm double-sided embossed, anti-skid upgrade; eyelets for wall display; custom logo.',
    'ym6.t': 'PU / Rubber Mat', 'ym6.d': 'Natural rubber base + PU anti-slip top; premium grip for hot yoga.',
    'ym7.t': 'Suede / Velvet Mat', 'ym7.d': 'Soft microfiber suede surface; absorbs moisture, elegant feel.',
    'ym8.t': 'NBR Yoga Mat', 'ym8.d': 'High-elastic matte anti-slip NBR; best-seller 183×61×1 cm; thickness 0.8–2 cm.',
    'ac1.t': 'Yoga Foam Roller', 'ac1.d': 'PVC/PP core, smooth or textured (wolf-tooth, moon, corrugated, diamond); 25×7.5–45×14 cm.',
    'ac2.t': 'Yoga Blocks', 'ac2.d': 'EVA or cork; stable support for poses and stretches.',
    'ac3.t': 'Yoga Wheel', 'ac3.d': 'PP core with TPE/cork cover; 12/15 cm; back & core opener.',
    'ac4.t': 'Yoga Straps', 'ac4.d': 'Cotton / polyester; adjustable buckle for deeper stretches.',
    'ac5.t': 'Cork Massage Ball / Peanut', 'ac5.d': 'Eco cork massage balls & peanut balls for muscle recovery.',
    'ac6.t': 'Foldable Beach / Yoga Towel', 'ac6.d': '2-in-1 microfiber towel with integrated storage bag.',
    'ac7.t': 'Half Balance Ball (BOSU)', 'ac7.d': 'Rubber dome on rigid platform; balance & core training.',
    'ac8.t': 'Balance Pad', 'ac8.d': 'Textured foam pad for stability and rehab training.',
    'ac9.t': 'Bath / Non-slip Mat', 'ac9.d': 'Suction-dot PVC mat for shower & home safety.',
    'ac10.t': 'Yoga / Exercise Ball', 'ac10.d': 'Anti-burst inflatable ball for pilates & fitness.',
    'fi1.t': 'Hex Dumbbell', 'fi1.d': 'Rubber-coated hexagonal dumbbell; ergonomic non-slip handle; 1–70 kg / 2–150 lb.',
    'fi2.t': 'Beam Barbell', 'fi2.d': 'Silicone barbell bar; durable, flexible; unisex design.',
    'fi3.t': 'Adjustable Dumbbell Set', 'fi3.d': 'Colorful multi-weight set 1–10 kg for home gym.',
    'fi4.t': 'Cement Barbell-Dumbbell Set', 'fi4.d': 'Adjustable home-gym cement set.',
    'fi5.t': 'Hand Grip Strengthener', 'fi5.d': 'Adjustable 5–60 kg TPR grip; non-slip; home fitness & rehab.',
    'fi6.t': 'Hand Gripper Set (Counting)', 'fi6.d': 'Adjustable counting grip trainer; strength & rehab.',
    'fi7.t': 'Wearable Wrist & Ankle Weights', 'fi7.d': 'Silicone + iron core; hands-free resistance; multiple weights.',
    'fi8.t': 'Adjustable Mat Rack', 'fi8.d': 'Iron pipe rack, powder-coated; holds up to 25 eyelet mats.',
    'fi9.t': 'Fitness Training Stick', 'fi9.d': 'Detachable steel stretching stick with foam handles; 30/45/60 in.',

    // Spec overview
    'spec.title': 'Specification Overview',
    'spec.sub': 'Popular sizes and MOQs at a glance. Custom sizes, colors and packaging available on request.',
    'spec1.t': 'TPE Yoga Mat', 'spec1.d': '1830×610 / 1830×800 / 1850×900 / 2000×1000 / 1850×1220 mm\nThickness 4–12 mm\nMOQ 100 pcs',
    'spec2.t': 'Alignment Yoga Mat', 'spec2.d': '61 cm / 80 cm widths\nLotus + centerline guides\nMOQ 100 pcs',
    'spec3.t': 'NBR Yoga Mat', 'spec3.d': '183×61×0.8–2 cm\n185×80×1 / 185×90×1 cm\nMOQ 1,000 pcs',
    'spec4.t': 'Yoga Foam Roller', 'spec4.d': '25×7.5 to 45×14 cm\nSmooth / wolf-tooth / moon / corrugated / diamond\nMOQ 500 pcs',
    'spec5.t': 'PU / Rubber Mat', 'spec5.d': 'Natural rubber base + PU anti-slip top\n1830×610 / 1850×800 mm\nMOQ on request',
    'spec6.t': 'Yoga Wheel', 'spec6.d': '12 / 15 cm diameter, PP core\nTPE or cork surface\nMOQ on request',
    'spec7.t': 'Hex Dumbbell', 'spec7.d': '1/2/3–10 kg, 2.5–70 kg\n5–150 lb\nRubber coated',
    'spec8.t': 'Hand Gripper', 'spec8.d': '5–60 kg adjustable\nTPR, counting model\nMOQ on request',

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
    'str1.t': '低起订量', 'str1.d': 'TPE 瑜伽垫 100 片起订；瑜伽柱 500 个起订；NBR 1000 条起订。小批量试水无库存压力。',
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
    'range1.t': '瑜伽垫', 'range1.s': 'TPE · 软木 · PU · NBR · 体位线 · 折叠', 'range1.alt': '瑜伽垫系列',
    'range2.t': '瑜伽 & 普拉提配件', 'range2.s': '瑜伽柱 · 瑜伽砖 · 瑜伽轮 · 按摩球 · 伸展带 · 毛巾', 'range2.alt': '瑜伽配件',
    'range3.t': '健身器材', 'range3.s': '哑铃 · 杠铃 · 握力器 · 器材架 · 负重', 'range3.alt': '健身器材',

    'gallery.title': '全产品图库',
    'gallery.sub': '我们生产的每一个品类，均支持 OEM、ODM 与贴牌定制。',
    'gallery.note': '部分图片为示意参考，联系我们获取真实工厂照片与免费样品。',
    'g1.n': 'TPE 瑜伽垫', 'g1.s': '环保双层，4–12 mm',
    'g2.n': '体位线瑜伽垫', 'g2.s': '引导线辅助',
    'g3.n': 'NBR 瑜伽垫', 'g3.s': '高弹，0.8–2 cm',
    'g4.n': '瑜伽柱', 'g4.s': '光面 / 纹理',
    'g5.n': 'PU / 橡胶垫', 'g5.s': '高端防滑',
    'g6.n': '麂皮绒垫', 'g6.s': '柔软绒面',
    'g7.n': '折叠便携垫', 'g7.s': '三折易携',
    'g8.n': '软木瑜伽垫', 'g8.s': '天然软木防滑',
    'g9.n': '瑜伽轮', 'g9.s': '腰背核心',
    'g10.n': '瑜伽砖', 'g10.s': 'EVA / 软木',
    'g11.n': '按摩系列', 'g11.s': '深层放松',
    'g12.n': '波速球', 'g12.s': 'BOSU 平衡',
    'g13.n': '平衡垫', 'g13.s': '稳定性训练',
    'g14.n': '浴室防滑垫', 'g14.s': '吸盘居家',
    'g15.n': '瑜伽健身球', 'g15.s': '防爆设计',
    'g16.n': '六角哑铃', 'g16.s': '橡胶包胶',
    'g17.n': '硅胶杠铃', 'g17.s': '硅胶杆',
    'g18.n': '握力训练器', 'g18.s': '5–60 kg 可调',
    'g19.n': '穿戴式负重', 'g19.s': '手腕 & 脚踝',
    'g20.n': '瑜伽器材架', 'g20.s': '可挂 25 张垫',
    'g21.n': '健身拉伸棒', 'g21.s': '拉伸 & 体态',

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
    'cat.yoga.title': '瑜伽垫', 'cat.yoga.sub': 'TPE · 软木 · PU · NBR · 体位线 · 折叠',
    'cat.acc.title': '瑜伽 & 普拉提配件', 'cat.acc.sub': '瑜伽柱 · 瑜伽砖 · 瑜伽轮 · 按摩球 · 伸展带 · 毛巾',
    'cat.fit.title': '健身器材', 'cat.fit.sub': '哑铃 · 杠铃 · 握力器 · 器材架 · 负重',
    'ym1.t': 'TPE 瑜伽垫', 'ym1.d': '环保双层 TPE，防滑纹理表面，宽度 61–122 cm，厚度 4–12 mm。可选实重、经济、特供等级。',
    'ym2.t': '折叠 TPE 瑜伽垫', 'ym2.d': '三折设计平铺不卷边；6 mm 缓冲；超便携，可塞入背包。',
    'ym3.t': '折叠软木橡胶瑜伽垫', 'ym3.d': '100% 天然软木面 + 橡胶底；可再生、防潮、高摩擦。',
    'ym4.t': '体位线瑜伽垫', 'ym4.d': '莲花印花引导线辅助正确练习；TPE 基材，61/80 cm 宽度。',
    'ym5.t': '定制 logo 挂墙瑜伽垫', 'ym5.d': '8 mm 双面压纹，防滑升级；带挂孔可上墙展示；支持定制 logo。',
    'ym6.t': 'PU / 橡胶瑜伽垫', 'ym6.d': '天然橡胶底 + PU 防滑面；高温瑜伽高端抓地。',
    'ym7.t': '麂皮绒瑜伽垫', 'ym7.d': '柔软麂皮绒表面；吸汗、触感高级。',
    'ym8.t': 'NBR 瑜伽垫', 'ym8.d': '高弹亚光防滑 NBR；爆款 183×61×1 cm；厚度 0.8–2 cm。',
    'ac1.t': '瑜伽柱', 'ac1.d': 'PVC/PP 内管，光面或狼牙、月牙、水波纹、菱形等纹理；25×7.5–45×14 cm。',
    'ac2.t': '瑜伽砖', 'ac2.d': 'EVA 或软木；稳定支撑体式与拉伸。',
    'ac3.t': '瑜伽轮', 'ac3.d': 'PP 内胆 + TPE/软木外套；12/15 cm；开肩开背。',
    'ac4.t': '瑜伽伸展带', 'ac4.d': '棉 / 涤纶；可调扣环加深拉伸。',
    'ac5.t': '软木按摩球 / 花生球', 'ac5.d': '环保软木按摩球与花生球，缓解肌肉酸痛。',
    'ac6.t': '折叠浴巾 / 瑜伽巾', 'ac6.d': '二合一超细纤维毛巾，自带收纳袋。',
    'ac7.t': '波速球 (BOSU)', 'ac7.d': '橡胶半球 + 硬质底座；平衡与核心训练。',
    'ac8.t': '平衡垫', 'ac8.d': '纹理泡沫垫，稳定性与康复训练。',
    'ac9.t': '浴室防滑垫', 'ac9.d': '吸盘式 PVC 垫，浴室居家防滑。',
    'ac10.t': '瑜伽健身球', 'ac10.d': '防爆充气球，普拉提与健身通用。',
    'fi1.t': '六角哑铃', 'fi1.d': '橡胶包胶六角哑铃；人体工学防滑手柄；1–70 kg / 2–150 lb。',
    'fi2.t': '硅胶杠铃', 'fi2.d': '硅胶杆；耐用柔韧；男女通用。',
    'fi3.t': '可调哑铃套装', 'fi3.d': '彩色多重量套装 1–10 kg，家用健身房。',
    'fi4.t': '水泥可调杠哑铃组', 'fi4.d': '家用可调水泥重量组。',
    'fi5.t': '握力训练器', 'fi5.d': '5–60 kg 可调 TPR 握力器；防滑；家用与康复。',
    'fi6.t': '计数握力器套装', 'fi6.d': '可调计数握力训练器；力量与康复。',
    'fi7.t': '穿戴式手腕脚踝负重', 'fi7.d': '硅胶 + 铁芯；免手持阻力；多种重量。',
    'fi8.t': '可调瑜伽器材架', 'fi8.d': '铁管喷粉器材架；可挂最多 25 张带孔垫。',
    'fi9.t': '健身拉伸棒', 'fi9.d': '可拆卸钢制拉伸棒，泡沫手柄；30/45/60 英寸。',

    'spec.title': '规格一览',
    'spec.sub': '常见尺寸与起订量速查。支持定制尺寸、颜色与包装。',
    'spec1.t': 'TPE 瑜伽垫', 'spec1.d': '1830×610 / 1830×800 / 1850×900 / 2000×1000 / 1850×1220 mm\n厚度 4–12 mm\n起订量 100 片',
    'spec2.t': '体位线瑜伽垫', 'spec2.d': '61 cm / 80 cm 宽度\n莲花 + 中线引导\n起订量 100 片',
    'spec3.t': 'NBR 瑜伽垫', 'spec3.d': '183×61×0.8–2 cm\n185×80×1 / 185×90×1 cm\n起订量 1000 条',
    'spec4.t': '瑜伽柱', 'spec4.d': '25×7.5 至 45×14 cm\n光面 / 狼牙 / 月牙 / 水波纹 / 菱形\n起订量 500 个',
    'spec5.t': 'PU / 橡胶垫', 'spec5.d': '天然橡胶底 + PU 防滑面\n1830×610 / 1850×800 mm\n起订量 面议',
    'spec6.t': '瑜伽轮', 'spec6.d': '直径 12 / 15 cm，PP 内胆\nTPE 或软木面\n起订量 面议',
    'spec7.t': '六角哑铃', 'spec7.d': '1/2/3–10 kg，2.5–70 kg\n5–150 lb\n橡胶包胶',
    'spec8.t': '握力器', 'spec8.d': '5–60 kg 可调\nTPR，计数款\n起订量 面议',

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
