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
    'nav.home': 'Home', 'nav.products': 'Yoga Mats & Gear', 'nav.about': 'About',
    'nav.contact': 'Contact', 'nav.quote': 'Get a Quote', 'nav.blog': 'Blog',
    // Pilates 器械一级入口（/pilates/ 独立板块，与 Products 平行）
    'nav.pilates': 'Pilates Equipment',
    'nav.pl.reformer': 'Pilates Reformer',
    'nav.pl.cadillac': 'Pilates Cadillac',
    'nav.pl.wunda-chair': 'Pilates Wunda Chair',
    'nav.pl.ladder-barrel': 'Pilates Ladder Barrel',
    'nav.pl.spine-corrector': 'Pilates Spine Corrector',
    'nav.pl.reformer-tower': 'Reformer Tower & 3-in-1',
    'nav.pl.studio-set': 'Pilates Studio Set',
    'nav.pl.specialty': 'Pilates Specialty',
    'nav.pl.all': 'All Pilates apparatus',

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
    'str1.t': 'Proven Track Record', 'str1.d': 'Since 2013 we have supplied yoga and fitness brands across North America, Europe and Australia — 600+ workers, 200K+ mats/month, stable reorders.',
    'str2.t': 'Quality You Can Verify', 'str2.d': 'In-house QC with batch traceability, ISO 9001 & BSCI audited, materials tested to ROHS / CE / REACH. Not just a promise — documented.',
    'str3.t': 'Low MOQ, Fast Lead Time', 'str3.d': 'TPE mats from 100 pcs and 7-day sampling with flexible production. Test the market, then scale without heavy inventory risk.',
    'str4.t': 'Full Customization', 'str4.d': 'Material, size, thickness, color, double-color, logo, fold and packaging — engineered to your exact spec.',

    // Factory at a glance
    'factory.title': 'Factory at a Glance',
    'factory.sub': 'A vertically integrated manufacturer in Fujian — R&D, production and QC under one roof.',
    'factory.stat1': '2013', 'factory.s1': 'Established',
    'factory.stat2': '600+', 'factory.s2': 'Workers',
    'factory.stat3': '12,000㎡', 'factory.s3': 'Facility',
    'factory.stat4': '12', 'factory.s4': 'Production Lines',
    'factory.vertical': '<strong>In-house from foaming to finishing.</strong> We operate three owned plants — two dedicated to TPE yoga mats and one to PU / rubber mats — running 6 foaming machines and 12 production lines. Because foaming, the most capacity-critical step, happens inside our own factories, we hold a steady output of 7,000–8,000 mats per day (about 200,000 per month) and control quality from raw material through to the finished mat.',
    'factory.cap.title': 'Monthly Production Capacity',
    'cap1.t': 'Yoga Mats', 'cap1.d': '200,000 pcs / month',
    'cap2.t': 'Sports Bags', 'cap2.d': '150,000 pcs / month',
    'cap3.t': 'Yoga Wears', 'cap3.d': '120,000 pcs / month',
    'cap4.t': 'Yoga Leggings', 'cap4.d': '100,000 pcs / month',
    'cap5.t': 'Yoga Blocks', 'cap5.d': '100,000 pcs / month',
    'factory.media': 'SANFAN factory building',

    // Product range (5 cards)
    // Product range (10 category cards — 双语 span，无需字典)
    'range.title': 'Our Product Range',
    'range.sub': 'From yoga essentials to full fitness lines — all factory-direct and customizable.',

    // Featured products (12 款跨分类主推)
    'featured.title': 'Featured Products',
    'featured.sub': 'A hand-picked selection across our 10 product lines — every one customizable with your logo, size, thickness and packaging.',
    'featured.cta': 'Browse all 141 products',

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
    'ym1.t': 'TPE Yoga Mat', 'ym1.d': 'Eco TPE (single / double layer), non-slip textured surface, widths 61 / 66 / 80 / 90 cm (24" / 26" / 31.5" / 35.5"), thickness 6–12 mm (1/4"–1/2"). Solid, economy and special grades.',
    'ym2.t': 'Wide TPE Yoga Mat', 'ym2.d': 'Extra-wide 80 / 90 cm TPE mat for dynamic and partner practice; same eco TPE grip.',
    'ym3.t': 'TPE Double Yoga Mat', 'ym3.d': 'Wide-format TPE mat for couples and family use; non-slip, easy to clean.',
    'ym4.t': 'TPE Folding Yoga Mat', 'ym4.d': 'Tri-fold design opens flat with no curl; 6 mm (1/4") cushioning; ultra-portable, packs into a backpack.',
    'ym5.t': 'PU Rubber Yoga Mat', 'ym5.d': 'Natural rubber base + PU anti-slip top; premium grip for hot yoga and studios.',
    'ym6.t': 'Matte PU Rubber Yoga Mat', 'ym6.d': 'Matte frosted PU surface, elegant feel, high sweat-absorption grip for intense sessions.',
    'ym7.t': 'TPE Camouflage Yoga Mat', 'ym7.d': 'Camouflage-print TPE mat with a bold look, ideal for branded lines.',
    'ym8.t': 'Balance Trainer', 'ym8.d': 'Half-ball balance trainer for core stability, rehab and functional training; custom colors and resistance levels.',
    'pr1.t': 'Aerial Yoga Hammock', 'pr1.d': 'Anti-gravity aerial yoga hammock in high-strength polyester or 210T nylon taffeta; ceiling mount kit available; custom colors and lengths for aerial yoga and flying pilates.',
    'pr2.t': 'Yoga Wheel', 'pr2.d': 'ABS inner core with TPE cushioning; deepens backbends, stretches shoulders and opens the chest; custom colors.',
    'pr3.t': 'Meditation Mat & Yoga Bolster', 'pr3.d': 'PU + natural rubber meditation mat (40×60 / 60×60 cm, 4.5 mm) with a 100% polyester bolster (64×24×13 cm, 550 g); custom colors.',
    'pr4.t': 'Yoga Blocks (EVA)', 'pr4.d': 'High-density EVA blocks; stable support for poses and stretches, multiple colors.',
    'pr5.t': 'Knee Pad', 'pr5.d': 'Thick kneeling knee pad for yoga, gardening and floor work; shock-absorbing, non-slip base.',
    'fr1.t': 'Yoga Foam Roller (Wolf-tooth)', 'fr1.d': 'EVA foam roller with wolf-tooth texture; 45 cm (18") muscle recovery and myofascial release.',
    'fr2.t': 'Solid Foam Roller', 'fr2.d': 'Solid EVA roller for deep-tissue massage and core training.',
    'fr3.t': 'Electric Foam Roller', 'fr3.d': 'Rechargeable vibrating foam roller for professional recovery.',
    'fr4.t': 'EVA Massage Rollers', 'fr4.d': 'Multiple textures and sizes — smooth, grid and half-roller options; custom colors and hardness.',
    'fr5.t': 'Massage Ball', 'fr5.d': 'Fascia massage ball for shoulders, back, waist and foot relief.',
    'rb1.t': 'Resistance Bands', 'rb1.d': 'Latex and fabric resistance bands — loops, tubes and figure-8 styles; multiple tensions, custom colors and prints.',
    'rb2.t': 'Mini Yoga Ball (25 cm / 10")', 'rb2.d': '25 cm (10") anti-slip gymnastic ball for pilates, rehab and core work.',
    'rb3.t': 'Balance Dome', 'rb3.d': 'BOSU-style balance dome for core strength, stability and rehab; anti-slip base, custom colors.',
    'rb4.t': 'Balance Board', 'rb4.d': 'Wooden balance board with non-slip surface for stability, coordination and rehab training.',
    'fi1.t': 'Stair Climber', 'fi1.d': 'Compact home stepper for cardio and lower-body training; adjustable resistance, small footprint.',
    'fi2.t': 'Kettlebell', 'fi2.d': 'Coated kettlebell for swings, squats and functional strength training; custom weights and colors.',
    'fi3.t': 'Jump Rope', 'fi3.d': 'Speed jump rope with ball-bearing handles; adjustable length, custom grips and colors.',
    'fi4.t': 'Home Stepper', 'fi4.d': 'Home cardio stepper with hydraulic resistance; low-impact workout, custom branding available.',
    'fi5.t': 'Dumbbell & Barbell', 'fi5.d': 'Silicone dumbbells (1–2.5 kg) and cast-iron dumbbells / barbells (0.5–10 kg; bar 91 / 110 cm); six silicone colorways, custom logo.',

    // Spec overview
    'spec.title': 'Specification Overview',
    'spec.sub': 'Popular sizes and MOQs at a glance. Custom sizes, colors and packaging available on request.',
    'spec1.t': 'TPE Yoga Mat', 'spec1.d': '1830×610 / 1830×800 / 1850×900 / 2000×1000 / 1850×1220 mm (48")\nThickness 4–12 mm (5/32"–1/2")\nMOQ 100 pcs',
    'spec2.t': 'Wide / Double TPE Mat', 'spec2.d': '80 cm (31") / 122 cm (48") widths\nEco double-layer TPE\nMOQ 100 pcs',
    'spec3.t': 'PU / Rubber Mat', 'spec3.d': 'Natural rubber base + PU anti-slip top\n1830×610 / 1850×800 mm (31")\nMOQ on request',
    'spec4.t': 'Balance Trainer', 'spec4.d': 'Half-ball balance trainer\nAnti-slip base\nCustom colors\nMOQ on request',
    'spec5.t': 'Aerial Yoga Hammock', 'spec5.d': 'High-strength aerial silk\nCeiling mount kit available\nCustom colors & sizes\nMOQ on request',
    'spec6.t': 'Yoga Wheel', 'spec6.d': 'ABS core + TPE cushion\n33 / 38 cm (15") diameters\nCustom colors\nMOQ on request',
    'spec7.t': 'Yoga Blocks (EVA)', 'spec7.d': 'High-density EVA\n9×15×23 cm (9") standard\nMOQ 500 pcs',
    'spec8.t': 'Yoga Foam Roller', 'spec8.d': '25×7.5 to 45×14 cm (6")\nSmooth / wolf-tooth / solid\nMOQ 500 pcs',
    'spec9.t': 'Yoga / Fitness Ball', 'spec9.d': '25 cm (10") mini / standard sizes\nAnti-burst\nMOQ on request',
    'spec10.t': 'Resistance Bands', 'spec10.d': 'Latex & fabric bands\nLoops / tubes / figure-8\nMultiple tensions\nMOQ on request',
    'spec11.t': 'Balance Pad / Knee Pad', 'spec11.d': 'TPE balance & knee pads\nCustom sizes & colors\nMOQ on request',
    'spec12.t': 'Fitness Gear', 'spec12.d': 'Dumbbells · Kettlebells\nJump Ropes · Steppers\nMultiple weights & colors\nMOQ on request',

    // About
    'about.title': 'About SANFAN',
    'about.sub': 'A yoga & fitness equipment source factory trusted by brands worldwide.',
    'about.h1': 'FUJIAN SANFAN Sports Products Co., Ltd.',
    'about.p1': 'Founded in 2013 and headquartered in Xiamen, Fujian, SANFAN is a leading OEM/ODM manufacturer of yoga mats and sports products, with our manufacturing base in Jinjiang — the heart of China’s sporting-goods belt.',
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
    'contact.sub': 'Tell us what you need — we usually reply within 2 hours, 09:00–22:00 China time.',
    'contact.info.title': 'Contact Information',
    'c.addr.label': 'Factory Address', 'c.email.label': 'Email', 'c.phone.label': 'WhatsApp', 'c.hours.label': 'Service',
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
    'foot.products': 'Yoga Mats & Gear', 'foot.company': 'Company', 'foot.contact': 'Contact',
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

    // FAQ page (GEO)
    'nav.faq': 'FAQ',
    'faq.h1': 'Yoga Mat Sourcing FAQ — Answered by the Factory',
    'faq.sub': 'The real questions overseas buyers ask when sourcing yoga mats & fitness gear from China — MOQ, certification, customization, lead time and why a direct Fujian factory wins.',
    'faq.cat1': 'Sourcing & MOQ',
    'faq.cat2': 'Quality & Certifications',
    'faq.cat3': 'Customization',
    'faq.cat4': 'Lead Time & Shipping',
    'faq.cat5': 'Why Fujian SANFAN',
    'faq.q1': 'What is the minimum order quantity (MOQ) for custom yoga mats?',
    'faq.a1': 'TPE yoga mats start at 100 pcs per design and color; foam rollers and EVA yoga blocks from 500 pcs; most accessories 500–1,000 pcs. Low MOQ lets new and small brands test the market with minimal inventory risk.',
    'faq.q2': 'Can I order a small batch of yoga mats to test a new brand?',
    'faq.a2': 'Yes. Our 100-pcs MOQ on TPE mats is designed for brand launches and market testing. You can start with one color and size, validate demand, then scale up.',
    'faq.q3': 'Where are the best yoga mat manufacturers in China?',
    'faq.a3': "China's main yoga and fitness gear clusters are in Fujian (Jinjiang/Quanzhou), Zhejiang and Guangdong. Fujian, where SANFAN is based, is known for integrated sports-goods supply chains, fast sampling and export experience.",
    'faq.q4': 'How do I find a reliable OEM yoga mat factory in China?',
    'faq.a4': 'Look for a real manufacturing base (not a trader), verifiable certifications (ISO 9001, BSCI), export track record, transparent MOQ/lead time and a responsive team. SANFAN meets all of these — visit our factory anytime.',
    'faq.q5': 'TPE vs PU/rubber yoga mat: which should my brand choose?',
    'faq.a5': 'TPE is lightweight, eco-friendly and cost-effective — ideal for mass-market and private-label lines. PU/rubber offers premium grip for hot yoga and studios. We make both and help you choose by use case and price.',
    'faq.q6': 'What is the difference between OEM, ODM and private label for yoga mats?',
    'faq.a6': 'OEM = we produce to your spec/design. ODM = we provide existing designs you brand as yours. Private label = our standard products shipped under your brand with your logo and packaging. All three are available at SANFAN.',
    'faq.q7': 'Are your yoga mats non-toxic and eco-friendly?',
    'faq.a7': 'Yes. Our TPE mats are odorless, recyclable and free of harmful plasticizers. Materials are selected for ROHS / CE / REACH compliance so they are safe for daily use in any market.',
    'faq.q8': 'What certifications do yoga mats need for the US/EU market?',
    'faq.a8': 'For the US, ROHS and CE marking matter; for the EU, REACH (SVHC) compliance is required. SANFAN holds ISO 9001 and BSCI, and our materials are tested to these standards.',
    'faq.q9': 'How do you keep quality consistent across production batches?',
    'faq.a9': 'We run in-house QC with batch traceability: incoming material checks, in-process inspection and final AQL inspection before shipment. Consistent formulations and tooling keep every batch stable.',
    'faq.q10': 'Are TPE yoga mats biodegradable?',
    'faq.a10': 'TPE is more eco-friendly than PVC and is recyclable, though not soil-biodegradable. For brands prioritizing sustainability we offer recyclable TPE lines and can advise on eco messaging.',
    'faq.q11': 'How slip-resistant are your mats for hot yoga or sweaty sessions?',
    'faq.a11': 'PU/rubber mats give the strongest grip even when wet — our top choice for hot yoga. TPE double-layer mats offer reliable dry grip. We can match surface texture to your practice profile.',
    'faq.q12': 'Can you print my logo on the yoga mats?',
    'faq.a12': 'Yes. We offer logo printing, embossing and laser engraving on mats and most accessories, with color-matched packaging to build your brand identity.',
    'faq.q13': 'What can be customized — size, thickness, color, double-color, packaging?',
    'faq.a13': 'Nearly everything: material, size, thickness (6–12 mm (1/4"–1/2")), color, double-color, surface finish, logo, fold style and packaging. Just share your spec and we engineer it.',
    'faq.q14': 'Can you make non-standard sizes such as 1830×610×3 mm (1/8"), wide or double-wide?',
    'faq.a14': 'Yes. Beyond standard 1830×610 mm (72" × 24") we produce wide (80 / 90 cm) and double-wide (122 cm) formats, plus custom lengths and thicknesses. Send your dimensions and we confirm tooling.',
    'faq.q15': 'Do you provide custom packaging, barcodes and inserts?',
    'faq.a15': 'Yes. We design and produce custom boxes, belly bands, barcodes, QR codes and inserts, so your product arrives shelf-ready under your brand.',
    'faq.q16': 'Can you develop a new product from my sample or design?',
    'faq.a16': 'Absolutely. Our R&D team develops new items from your sample, sketch or concept — from material selection to final mass production, with a physical sample in about 7 days.',
    'faq.q17': 'How fast can I get a sample and bulk production?',
    'faq.a17': 'Physical samples are ready in about 7 days with your logo, color and packaging. Bulk lead time depends on order size and customization; we confirm a clear timeline at quotation.',
    'faq.q18': 'What is your monthly production capacity?',
    'faq.a18': 'We produce 200,000+ yoga mats per month across 5 production lines, plus rollers, blocks, bags and apparel — enough to support both growing brands and large repeat orders.',
    'faq.q19': 'Do you ship to the US, EU or Australia? Which incoterms (FOB, EXW, DDP)?',
    'faq.a19': 'Yes, worldwide. We ship under FOB, EXW, CIF or DDP depending on your preference, and handle export documentation for smooth customs clearance.',
    'faq.q20': 'Can you ship directly to Amazon FBA warehouses?',
    'faq.a20': 'Yes. We prepare FBA-compliant labeling, cartons and paperwork and can ship directly to Amazon fulfillment centers in the US, EU and other regions.',
    'faq.q21': 'Why source yoga mats from Fujian, China?',
    'faq.a21': 'Fujian (Jinjiang/Quanzhou) is a mature sports-goods manufacturing hub with deep supply chains, skilled labor and strong export logistics — shorter lead times and competitive pricing for buyers.',
    'faq.q22': 'What does a vertically integrated factory give a buyer?',
    'faq.a22': 'Vertical integration means R&D, foaming, cutting, molding, printing and QC sit under one roof. You get faster sampling, tighter quality control and one accountable partner instead of many sub-suppliers.',
    'faq.q23': 'How do I verify a supplier is a real factory, not a trading company?',
    'faq.a23': 'Request a factory video call, business license, audit reports (BSCI/ISO) and production photos. SANFAN welcomes scheduled factory tours (in person or virtual) and shares verifiable credentials.',
    'faq.q24': 'What makes SANFAN different from other yoga mat suppliers?',
    'faq.a24': '12+ years focused on yoga and fitness gear, 600+ workers, low 100-pcs MOQ, 7-day sampling, full customization and certified quality — backed by a direct factory, not a middleman.',
  },

  zh: {
    'nav.home': '首页', 'nav.products': '瑜伽垫与健身', 'nav.about': '关于',
    'nav.contact': '联系', 'nav.quote': '获取报价', 'nav.blog': '博客',
    // Pilates 器械一级入口（与「产品」平行的独立板块）
    'nav.pilates': '普拉提器械',
    'nav.pl.reformer': '普拉提核心床',
    'nav.pl.cadillac': '普拉提凯迪拉克床',
    'nav.pl.wunda-chair': '普拉提稳踏椅',
    'nav.pl.ladder-barrel': '普拉提梯桶',
    'nav.pl.spine-corrector': '普拉提矫正器',
    'nav.pl.reformer-tower': '半高架与三合一',
    'nav.pl.studio-set': '普拉提五件套',
    'nav.pl.specialty': '普拉提特殊器械',
    'nav.pl.all': '全部普拉提器械',

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
    'str1.t': '有实绩的工厂', 'str1.d': '自 2013 年起为北美、欧洲、澳洲的瑜伽与健身品牌供货——600+ 员工、月产 20 万+ 垫，复购稳定。',
    'str2.t': '可验证的品质', 'str2.d': '厂内 QC 加批次追溯，ISO 9001 与 BSCI 审核，材质按 ROHS / CE / REACH 检测。不是空话，有凭证。',
    'str3.t': '低起订、快交期', 'str3.d': 'TPE 垫 100 片起、7 天打样、生产灵活。先试市场，再放量，库存风险小。',
    'str4.t': '全定制', 'str4.d': '材质、尺寸、厚度、颜色、双色、logo、折叠方式与包装——按你的规格实现。',

    'factory.title': '工厂一览',
    'factory.sub': '福建一体化制造工厂 — 研发、生产、质检一站式。',
    'factory.stat1': '2013', 'factory.s1': '成立年份',
    'factory.stat2': '600+', 'factory.s2': '员工规模',
    'factory.stat3': '12000㎡', 'factory.s3': '厂房面积',
    'factory.stat4': '12', 'factory.s4': '生产线',
    'factory.vertical': '<strong>从发泡到成品全自有。</strong>我们运营三家自有工厂——两家专做 TPE 瑜伽垫，一家专做 PU/橡胶垫，共配备 6 台发泡机、12 条生产线。由于发泡这道最影响产能的工序掌握在自己手里，我们能稳定做到日产 7,000–8,000 片（约 20 万片/月），并从原料到成品全程控质。',
    'factory.cap.title': '月度产能',
    'cap1.t': '瑜伽垫', 'cap1.d': '200,000 片 / 月',
    'cap2.t': '运动包', 'cap2.d': '150,000 个 / 月',
    'cap3.t': '瑜伽服', 'cap3.d': '120,000 件 / 月',
    'cap4.t': '瑜伽裤', 'cap4.d': '100,000 条 / 月',
    'cap5.t': '瑜伽砖', 'cap5.d': '100,000 块 / 月',
    'factory.media': '三梵工厂厂房',

    'range.title': '产品系列',
    'range.sub': '从瑜伽刚需到完整健身线 — 全部工厂直供、可定制。',
    'range.title': '产品系列',
    'range.sub': '从瑜伽刚需到完整健身线 — 全部工厂直供、可定制。',

    // 精选产品（12 款跨分类主推）
    'featured.title': '精选产品',
    'featured.sub': '横跨 10 条产品线的精选主推款 —— 每一款都支持 logo、尺寸、厚度与包装定制。',
    'featured.cta': '浏览全部 141 款产品',
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
    'ym1.t': 'TPE 瑜伽垫', 'ym1.d': '环保 TPE（单层/双层），防滑纹理表面，宽度 61 / 66 / 80 / 90 cm，厚度 6–12 mm。可选实重、经济、特供等级。',
    'ym2.t': '加宽 TPE 瑜伽垫', 'ym2.d': '80 / 90 cm 加宽 TPE 垫，适合流瑜伽与双人练习；同样环保抓地。',
    'ym3.t': 'TPE 双人瑜伽垫', 'ym3.d': '加宽版 TPE 垫，适合情侣与家庭使用；防滑、易清洁。',
    'ym4.t': 'TPE 折叠瑜伽垫', 'ym4.d': '三折设计平铺不卷边；6 mm 缓冲；超便携，可塞入背包。',
    'ym5.t': 'PU 橡胶瑜伽垫', 'ym5.d': '天然橡胶底 + PU 防滑面；高温瑜伽与瑜伽馆高端抓地（“土豪垫”）。',
    'ym6.t': '磨砂 PU 橡胶瑜伽垫', 'ym6.d': '磨砂 PU 表面，触感高级，高强度下吸汗抓地更稳。',
    'ym7.t': 'TPE 迷彩瑜伽垫', 'ym7.d': '迷彩印花 TPE 垫，外观硬朗，适合做品牌定制线。',
    'ym8.t': '平衡训练器', 'ym8.d': '半圆平衡球训练器，核心稳定、康复与功能性训练；颜色与阻力可定制。',
    'pr1.t': '空中瑜伽吊床', 'pr1.d': '高强度聚酯纤维或 210T 尼龙塔夫绸反重力空中瑜伽吊床，可配天花板挂件套装；颜色与长度均可定制，适用空中瑜伽与飞行普拉提。',
    'pr2.t': '瑜伽轮', 'pr2.d': 'ABS 内芯 + TPE 缓冲；加深后弯、开肩扩胸；颜色可定制。',
    'pr3.t': '冥想垫与瑜伽抱枕', 'pr3.d': 'PU + 天然橡胶冥想垫（40×60 / 60×60 cm，4.5 mm）搭配 100% 聚酯纤维抱枕（64×24×13 cm，550 g）；颜色与尺寸可定制。',
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
    'fi1.t': '迷你踏步机', 'fi1.d': '紧凑型家用踏步机，有氧与下肢训练，阻力可调、占地小。',
    'fi2.t': '壶铃', 'fi2.d': '包胶壶铃，甩摆、深蹲与功能性力量训练；重量与颜色可定制。',
    'fi3.t': '跳绳', 'fi3.d': '轴承竞速跳绳，长度可调；握柄与颜色可定制。',
    'fi4.t': '家用踏步机', 'fi4.d': '液压阻力家用踏步机，低冲击有氧训练；可定制品牌标识。',
    'fi5.t': '哑铃与杠铃', 'fi5.d': '硅胶哑铃（1–2.5 kg）与铸铁哑铃 / 杠铃（0.5–10 kg，杆长 91 / 110 cm）；六种硅胶配色，可定制 logo。',

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
    'contact.sub': '告诉我们你的需求，通常 2 小时内回复（中国时间 09:00–22:00）。',
    'contact.info.title': '联系方式',
    'c.addr.label': '工厂地址', 'c.email.label': '邮箱', 'c.phone.label': 'WhatsApp', 'c.hours.label': '服务',
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
    'foot.products': '瑜伽垫与健身', 'foot.company': '公司', 'foot.contact': '联系',
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

    // FAQ 页面（GEO）
    'nav.faq': '常见问题',
    'faq.h1': '瑜伽垫采购 FAQ —— 由工厂直接解答',
    'faq.sub': '海外买家从中国采购瑜伽垫与健身器材时的真实疑问——起订量、认证、定制、交期，以及为何源头工厂更靠谱。',
    'faq.cat1': '选厂与起订量',
    'faq.cat2': '品质与认证',
    'faq.cat3': '定制能力',
    'faq.cat4': '交期与物流',
    'faq.cat5': '为何选择福建三梵',
    'faq.q1': '定制瑜伽垫的最小起订量（MOQ）是多少？',
    'faq.a1': 'TPE 瑜伽垫每款每色 100 片起订；瑜伽柱、EVA 瑜伽砖 500 片起；多数配件 500–1,000 片。低起订量让新品牌和小团队以最小库存风险试水市场。',
    'faq.q2': '可以小批量下单瑜伽垫来测试新品牌吗？',
    'faq.a2': '可以。TPE 垫 100 片起订正是为品牌上线和市场测试设计。你可先做一个颜色、一个尺寸验证需求，再逐步放量。',
    'faq.q3': '中国最好的瑜伽垫工厂在哪里？',
    'faq.a3': '中国瑜伽及健身器材主要产业集群在福建（晋江/泉州）、浙江和广东。三梵所在的福建以完整的体育用品供应链、快速打样和出口经验著称。',
    'faq.q4': '如何找到靠谱的中国瑜伽垫 OEM 工厂？',
    'faq.a4': '看四点：真实制造基地（非贸易商）、可验证认证（ISO 9001、BSCI）、出口实绩、透明的 MOQ/交期，以及响应及时的团队。三梵全部满足，欢迎随时验厂。',
    'faq.q5': 'TPE 与 PU/橡胶瑜伽垫：我的品牌该选哪个？',
    'faq.a5': 'TPE 轻量、环保、性价比高，适合大众与贴牌走量；PU/橡胶抓地更强，适合高温瑜伽和瑜伽馆。两种我们都做，按使用场景和价位帮你选。',
    'faq.q6': '瑜伽垫的 OEM、ODM 和私标（private label）有什么区别？',
    'faq.a6': 'OEM＝按你的规格/设计生产；ODM＝我们提供现有设计、你贴牌；私标＝我们的标准产品加你的 logo 和包装出货。三梵三种都支持。',
    'faq.q7': '你们的瑜伽垫无毒、环保吗？',
    'faq.a7': '是的。TPE 垫无异味、可回收、不含害增塑剂，材质按 ROHS / CE / REACH 选型，确保各市场日常使用安全。',
    'faq.q8': '出口美国/欧盟的瑜伽垫需要哪些认证？',
    'faq.a8': '美国看 ROHS 与 CE 认证；欧盟需 REACH（SVHC）合规。三梵持有 ISO 9001 与 BSCI，材质均按这些标准检测。',
    'faq.q9': '你们如何保证各批次品质稳定？',
    'faq.a9': '我们做厂内 QC 与批次追溯：来料检验、制程抽检、出货前 AQL 终检。稳定的配方与模具让每一批都一致。',
    'faq.q10': 'TPE 瑜伽垫可生物降解吗？',
    'faq.a10': 'TPE 比 PVC 更环保、可回收，但并非土壤可降解。对主打可持续的品牌，我们提供可回收 TPE 系列并可协助环保话术。',
    'faq.q11': '你们垫子在热瑜伽/出汗时防滑吗？',
    'faq.a11': 'PU/橡胶垫即使湿滑也抓地最强，是我们高温瑜伽的首选；TPE 双层垫干态抓地可靠。我们可按练习场景匹配表面纹理。',
    'faq.q12': '可以在瑜伽垫上印我的 logo 吗？',
    'faq.a12': '可以。我们提供 logo 印刷、压印与激光雕刻，覆盖垫子与多数配件，并配套同色系包装，帮你建立品牌识别。',
    'faq.q13': '哪些可以定制——尺寸、厚度、颜色、双色、包装？',
    'faq.a13': '几乎都能：材质、尺寸、厚度（6–12 mm）、颜色、双色、表面工艺、logo、折叠方式与包装。发来规格，我们帮你实现。',
    'faq.q14': '能做非标尺寸吗，比如 1830×610×3 mm、加宽或双宽？',
    'faq.a14': '能。除标准 1830×610 mm 外，我们做加宽（80 / 90 cm）与双宽（122 cm），以及定制长度与厚度。发来尺寸，我们确认模具。',
    'faq.q15': '你们提供定制包装、条码和卡片吗？',
    'faq.a15': '提供。我们设计生产定制彩盒、腰封、条码、二维码与卡片，让你的产品以自有品牌、可直接上架的状态到达。',
    'faq.q16': '能根据我的样品或设计开发新品吗？',
    'faq.a16': '当然。研发团队可从你的样品、草图或概念开发新品——从选材到量产，约 7 天出实物样品。',
    'faq.q17': '打样和量产要多久？',
    'faq.a17': '实物样品约 7 天可带你的 logo、颜色与包装出货。量产地交期视订单量与定制程度而定，报价时给明确时间表。',
    'faq.q18': '你们的月产能是多少？',
    'faq.a18': '5 条产线月产瑜伽垫 20 万+，另有瑜伽柱、瑜伽砖、包袋与服饰，足以支撑成长型品牌与大额复购。',
    'faq.q19': '发美国/欧盟/澳洲吗？用哪些贸易术语（FOB/EXW/DDP）？',
    'faq.a19': '全球可发。可按你偏好走 FOB、EXW、CIF 或 DDP，并办理出口单证，确保清关顺畅。',
    'faq.q20': '能直发亚马逊 FBA 仓库吗？',
    'faq.a20': '能。我们按 FBA 要求做标签、纸箱与单证，可直接发往美国、欧盟等地的亚马逊履约中心。',
    'faq.q21': '为什么从福建采购瑜伽垫？',
    'faq.a21': '福建（晋江/泉州）是成熟的体育用品制造基地，供应链深、技工足、出口物流强——买家拿到的交期更短、价格更有竞争力。',
    'faq.q22': '垂直整合工厂对买家意味着什么？',
    'faq.a22': '垂直整合意味着研发、发泡、裁切、模压、印刷与 QC 都在一栋厂里。你得到更快打样、更紧的品质管控，以及一个而非多个责任方。',
    'faq.q23': '如何辨别供应商是真实工厂而非贸易商？',
    'faq.a23': '要求工厂视频连线、营业执照、审核报告（BSCI/ISO）与生产实景。三梵欢迎预约验厂（实地或线上），并出具可验证资质。',
    'faq.q24': '三梵和其他瑜伽垫供应商有什么不同？',
    'faq.a24': '12 年专注瑜伽与健身器材、600+ 员工、100 片低起订、7 天打样、全定制与认证品质——背后是源头工厂，而非中间商。',
  }
};
window.I18N = I18N;

// 语言偏好：记住访客的选择，直到他手动改。
// 访客选了中文就一直中文，选了英文就一直英文 —— 整个站点跟随，不因跳页而丢失。
//
// 存储用 localStorage 优先 + cookie 兜底：
// 隐私模式或浏览器阻止站点数据时，localStorage.setItem 会静默失败（被 try/catch 吞掉），
// 结果就是"当前页切了，跳到下一页又回去"，加 cookie 后这种情况仍能保持。
function setLangPref(l) {
  try { localStorage.setItem('siteLang', l); } catch (e) {}
  try {
    document.cookie = 'siteLang=' + encodeURIComponent(l) +
      ';path=/;max-age=31536000;samesite=Lax';
  } catch (e) {}
}

function getLangPref() {
  var v = null;
  try { v = localStorage.getItem('siteLang'); } catch (e) {}
  if (!v) {
    try {
      var m = document.cookie.match(/(?:^|;\s*)siteLang=([^;]*)/);
      if (m) v = decodeURIComponent(m[1]);
    } catch (e) {}
  }
  return v;
}

// 分语言 URL 的页面（/de/ /ja/ /ko/ /fr/ /it/ /es/）自身就是目标语言，
// 静态 HTML 已带正确的 <html lang>。绝不能用 en 覆盖掉，
// 否则 Google 与屏幕阅读器会把法语页面当成英文页面。
function isLocalizedPage() {
  const cur = (document.documentElement.lang || '').toLowerCase();
  return cur !== '' && cur !== 'en' && !cur.startsWith('zh');
}

function applyLang(lang) {
  // 分语言 URL 页面（/de/ /fr/ 等）本身就是目标语言，中英文切换对它们无意义。
  // 如果不整体返回，用户在英文页选过中文后，访问法语页会把中文内容混进去。
  if (isLocalizedPage()) return;
  document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';
  document.documentElement.classList.toggle('show-zh', lang === 'zh');
  document.documentElement.classList.toggle('show-en', lang === 'en');
  // 同步下拉按钮上显示的当前语言。漏掉这步的话，
  // 页面已经换成中文了，按钮却还写着 EN —— 看起来像切换没生效。
  document.querySelectorAll('.lang-cur-txt').forEach(el => {
    el.textContent = lang === 'zh' ? '中文' : 'EN';
  });
  // 同步菜单项高亮：切到中文时高亮"中文"，切回英文时高亮 EN
  document.querySelectorAll('.lang-menu a[data-setlang], .lang-menu button[data-setlang]')
    .forEach(el => {
      const l = el.getAttribute('data-setlang');
      if (l === 'en' || l === 'zh') {
        el.classList.toggle('active', l === lang);
      }
    });
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    const val = I18N[lang][key];
    if (val != null) {
      // 值里含标签时按 HTML 渲染（如带 <strong> 的说明段），否则按纯文本，
      // 避免把标签当字面量显示出来
      if (/<[a-z][\s\S]*>/i.test(val)) {
        el.innerHTML = (key.startsWith('spec') && key.endsWith('.d'))
          ? val.replace(/\n/g, '<br>') : val;
      } else {
        el.textContent = val;
      }
    }
  });
  document.querySelectorAll('[data-i18n-ph]').forEach(el => {
    const key = el.getAttribute('data-i18n-ph');
    if (I18N[lang][key] != null) el.setAttribute('placeholder', I18N[lang][key]);
  });
  const btn = document.querySelector('.lang-btn');
  if (btn) btn.textContent = lang === 'zh' ? 'EN' : '中文';
  setLangPref(lang);      // 记住选择，后续页面沿用
  window.dispatchEvent(new Event('sanfan-langchange'));
}

const langBtn = document.querySelector('.lang-btn');
if (langBtn) {
  langBtn.addEventListener('click', () => {
    const cur = document.documentElement.lang.startsWith('zh') ? 'zh' : 'en';
    applyLang(cur === 'zh' ? 'en' : 'zh');
  });
}
// 多语言下拉菜单（8 种语言横排放不下，改用下拉）
(function () {
  function closeAll(except) {
    document.querySelectorAll('.lang-switch.open').forEach(sw => {
      if (sw === except) return;
      sw.classList.remove('open');
      const b = sw.querySelector('.lang-current');
      if (b) b.setAttribute('aria-expanded', 'false');
    });
  }
  document.querySelectorAll('.lang-switch').forEach(sw => {
    const btn = sw.querySelector('.lang-current');
    if (!btn) return;                       // 旧结构无下拉按钮，跳过
    btn.addEventListener('click', e => {
      e.preventDefault();
      e.stopPropagation();
      const willOpen = !sw.classList.contains('open');
      closeAll(sw);
      sw.classList.toggle('open', willOpen);
      btn.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
    });
    // 选中语言后收起菜单
    sw.querySelectorAll('.lang-menu a, .lang-menu button').forEach(item => {
      item.addEventListener('click', () => {
        sw.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
      });
    });
  });
  document.addEventListener('click', e => {
    const t = e.target;
    if (t && t.closest && !t.closest('.lang-switch')) closeAll(null);
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeAll(null);
  });
})();

// 语言切换器 data-setlang：
//  - 带 href（如 /de/ /ja/ /ko/ 页面上的"中文"）→ 先记下偏好，再跳转到对应页面
//  - 不带 href（英文页上的"中文"按钮）→ 记下偏好并同页切换，不跳转
document.querySelectorAll('[data-setlang]').forEach(el => {
  el.addEventListener('click', e => {
    e.preventDefault();
    const L = el.getAttribute('data-setlang');
    setLangPref(L);
    const href = el.getAttribute('href');
    if (href) {
      location.href = href;
    } else {
      applyLang(L);
      // 同步高亮：当前项标记为 active
      document.querySelectorAll('.lang-menu a, .lang-menu button').forEach(x => {
        x.classList.remove('active');
      });
      el.classList.add('active');
    }
  });
});
// 多语言"跟随"：访客此前选过 6 国之一，进入根页（英文/中文同页）时，
// 自动跳到对应语言站的同页，保证"选了 de 整站一路德文，直到手动改"。
// 例：siteLang=de 访问 /blog.html → 跳 /de/blog.html；/products/ym1.html → 跳 /de/products/ym1.html。
(function followPreferredLang() {
  var pref = getLangPref();
  var LANGS = ['de', 'ja', 'ko', 'fr', 'it', 'es'];
  if (LANGS.indexOf(pref) === -1) return;            // 仅 6 国需要跟随跳转
  var p = location.pathname;
  if (p.indexOf('/' + pref + '/') === 0) return;     // 已在对应语言站内则不跳
  var target = '/' + pref + (p.charAt(0) === '/' ? p : '/' + p);
  if (target !== p) location.replace(target);        // 替换历史，避免后退成死循环
})();
// 沿用访客上次选择的语言；没选过（或选过但存储不可用）则默认英文。
applyLang(getLangPref() === 'zh' ? 'zh' : 'en');

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
        // GA4 转化事件：只有表单真正提交成功才记，避免把失败也算成询盘
        if (typeof gtag === 'function') {
          gtag('event', 'generate_lead', {
            form_name: 'inquiry',
            product_interest: data.get('product') || 'unspecified',
            page_language: document.documentElement.lang || 'en',
            page_path: location.pathname
          });
        }
        form.reset();
        okBox.style.display = 'block';
        okBox.style.background = '';
        okBox.style.color = '';
        okBox.style.borderColor = '';
        okBox.textContent = I18N[document.documentElement.lang.startsWith('zh') ? 'zh' : 'en']['form.ok'];
        // 尊重系统「减弱动态效果」：CSS 里的 prefers-reduced-motion 管不到 JS 显式写了
        // behavior:'smooth' 的 scrollIntoView（规范里显式 behavior 优先于 CSS scroll-behavior），
        // 所以这里必须自己判一次偏好，否则开关打开后这一跳仍然是动画。
        okBox.scrollIntoView({
          behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
          block: 'center'
        });
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

// ---------- Floating contact bar: 全站一键联系（WhatsApp / Email / 复制号码） ----------
(function () {
  var WA_NUM = '8615959029082';
  var TEL_TXT = '+86 15959029082';
  var MAIL = 'zenglinggun@gmail.com';
  var lang = (document.documentElement.lang || 'en').toLowerCase();
  var MSG = {
    en: "Hi SANFAN, I found your website and I'm interested in your yoga mats. Could you share MOQ, price and sampling time?",
    zh: "你好三梵，我在官网看到贵司，想咨询瑜伽垫定制。请问起订量、报价与打样周期？",
    de: "Hallo SANFAN, ich habe Ihre Website gefunden und interessiere mich für Ihre Yogamatten. Können Sie mir MOQ, Preis und Musterzeit nennen?",
    ja: "SANFAN様、サイトを拝見しました。ヨガマットについて伺いたいです。MOQ・価格・サンプル期間を教えてください。",
    ko: "안녕하세요 SANFAN, 웹사이트를 보고 연락드립니다. 요가매트 관련해 MOQ, 가격, 샘플 제작 기간을 알려주세요.",
    fr: "Bonjour SANFAN, j'ai trouvé votre site et je m'intéresse à vos tapis de yoga. Pouvez-vous m'indiquer le MOQ, le prix et le délai d'échantillonnage ?",
    it: "Ciao SANFAN, ho trovato il vostro sito e sono interessato ai vostri tappetini yoga. Potete indicarmi MOQ, prezzo e tempi di campionatura?",
    es: "Hola SANFAN, encontré su web y me interesan sus esterillas de yoga. ¿Pueden indicarme MOQ, precio y plazo de muestras?"
  };
  var body = MSG[lang.slice(0, 2)] || MSG.en;
  var tail = '\n\n— sent from ' + location.href;
  var waHref = 'https://wa.me/' + WA_NUM + '?text=' + encodeURIComponent(body + tail);
  var mailHref = 'mailto:' + MAIL + '?subject=' + encodeURIComponent('Inquiry from fjsanfan.com') + '&body=' + encodeURIComponent(body + tail);

  var ICON_WA = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M17.47 14.38c-.3-.15-1.75-.86-2.02-.96-.27-.1-.47-.15-.67.15-.2.3-.77.96-.95 1.16-.17.2-.35.22-.65.07-.3-.15-1.27-.47-2.42-1.5-.9-.8-1.5-1.79-1.68-2.09-.17-.3-.02-.46.13-.61.13-.13.3-.35.45-.52.15-.17.2-.3.3-.5.1-.2.05-.37-.02-.52-.08-.15-.67-1.61-.92-2.2-.24-.58-.49-.5-.67-.51h-.57c-.2 0-.52.07-.79.37-.27.3-1.04 1.01-1.04 2.47 0 1.46 1.06 2.87 1.21 3.07.15.2 2.09 3.19 5.06 4.47.71.3 1.26.49 1.69.63.71.23 1.36.19 1.87.12.57-.09 1.75-.72 2-1.41.25-.69.25-1.28.17-1.41-.07-.13-.27-.2-.57-.35z"/><path d="M12.04 2C6.6 2 2.18 6.42 2.18 11.86c0 1.74.46 3.44 1.32 4.94L2 22l5.36-1.4a9.86 9.86 0 0 0 4.68 1.19h.01c5.43 0 9.85-4.42 9.85-9.86 0-2.63-1.02-5.1-2.88-6.96A9.77 9.77 0 0 0 12.04 2zm0 18.02h-.01a8.2 8.2 0 0 1-4.18-1.14l-.3-.18-3.1.81.83-3.02-.2-.31a8.15 8.15 0 0 1-1.25-4.36c0-4.52 3.68-8.19 8.2-8.19 2.19 0 4.25.85 5.8 2.4a8.15 8.15 0 0 1 2.4 5.8c0 4.52-3.68 8.19-8.19 8.19z"/></svg>';
  var ICON_MAIL = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2zm0 4.24-8 4.8-8-4.8V6l8 4.8L20 6v2.24z"/></svg>';
  var ICON_COPY = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M16 1H4a2 2 0 0 0-2 2v14h2V3h12V1zm3 4H8a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2zm0 16H8V7h11v14z"/></svg>';
  var ICON_WECHAT = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8.69 4C4.98 4 2 6.5 2 9.6c0 1.8 1 3.4 2.6 4.4l-.65 2 2.3-1.16c.6.17 1.24.26 1.9.27-.13-.44-.2-.9-.2-1.37 0-2.98 2.9-5.4 6.47-5.4h.46C14.3 5.9 11.75 4 8.69 4zM6.6 7.3a.85.85 0 1 1 0 1.7.85.85 0 0 1 0-1.7zm4.2 0a.85.85 0 1 1 0 1.7.85.85 0 0 1 0-1.7z"/><path d="M22 13.74c0-2.6-2.6-4.7-5.8-4.7s-5.8 2.1-5.8 4.7 2.6 4.7 5.8 4.7c.63 0 1.24-.09 1.8-.25l1.98 1-.56-1.73C20.9 16.6 22 15.27 22 13.74zm-7.7-1.2a.75.75 0 1 1 0 1.5.75.75 0 0 1 0-1.5zm3.8 0a.75.75 0 1 1 0 1.5.75.75 0 0 1 0-1.5z"/></svg>';

  var WX_ID = 'sanfan_999';
  var QR_IMG = (function () {
    var stat = document.querySelector('img[src*="wechat-qr"]');
    if (stat) return stat.getAttribute('src');
    // ⚠️ 目录形式 URL（/de/ 、/ja/）的最后一段是「语言目录」而不是文件名，
    //    用 seg.length-1 会少算一层 → 请求 /de/assets/img/wechat-qr.webp（404）。
    //    实测：语言站首页的浮动联系条二维码一直是破图。
    var segs = location.pathname.split('/').filter(Boolean);
    var depth = /\/$/.test(location.pathname)
      ? segs.length                       // /de/ → 1 层
      : Math.max(segs.length - 1, 0);     // /de/products.html → 1 层；/ → 0
    return '../'.repeat(depth) + 'assets/img/wechat-qr.webp';
  })();
  var WX_TXT = {
    en: { scan: 'Scan this QR code in WeChat, or add us by ID:', copy: 'Copy WeChat ID' },
    zh: { scan: '微信扫码加我，或搜索微信号：', copy: '复制微信号' },
    de: { scan: 'QR-Code in WeChat scannen oder uns per ID hinzufügen:', copy: 'WeChat-ID kopieren' },
    ja: { scan: 'WeChatでQRコードをスキャン、またはIDで追加：', copy: 'WeChat IDをコピー' },
    ko: { scan: 'WeChat에서 QR코드를 스캔하거나 ID로 추가하세요:', copy: 'WeChat ID 복사' },
    fr: { scan: 'Scannez ce QR code dans WeChat, ou ajoutez-nous par ID :', copy: 'Copier l\'ID WeChat' },
    it: { scan: 'Scansiona questo QR code in WeChat, o aggiungici per ID:', copy: 'Copia ID WeChat' },
    es: { scan: 'Escanea este código QR en WeChat, o añádenos por ID:', copy: 'Copiar ID de WeChat' }
  };
  var wx = WX_TXT[lang.slice(0, 2)] || WX_TXT.en;

  var bar = document.createElement('div');
  bar.className = 'cbar';
  bar.innerHTML =
    '<a class="cb-wa" href="' + waHref + '" target="_blank" rel="noopener" aria-label="Chat on WhatsApp" title="WhatsApp ' + TEL_TXT + '">' + ICON_WA + '<span class="cb-lab">WhatsApp</span></a>' +
    '<a class="cb-mail" href="' + mailHref + '" aria-label="Send us an email">' + ICON_MAIL + '<span class="cb-lab">Email</span></a>' +
    '<button class="cb-wechat" type="button" aria-label="WeChat">' + ICON_WECHAT + '<span class="cb-lab">WeChat</span></button>' +
    '<button class="cb-copy" type="button" aria-label="Copy phone number">' + ICON_COPY + '<span class="cb-lab">Copy</span></button>';
  document.body.appendChild(bar);

  // WeChat QR modal (site-wide, reused by any [data-wx-open] trigger)
  var modal = document.createElement('div');
  modal.className = 'wx-modal';
  modal.innerHTML =
    '<div class="wx-card" role="dialog" aria-modal="true" aria-label="WeChat">' +
    '<button class="wx-close" type="button" aria-label="Close">&times;</button>' +
    '<img src="' + QR_IMG + '" alt="SANFAN WeChat QR code" width="261" height="312">' +
    '<div class="wx-title">WeChat 微信</div>' +
    '<p class="wx-scan">' + wx.scan + ' <b>' + WX_ID + '</b></p>' +
    '<button class="wx-copy" type="button">' + wx.copy + '</button>' +
    '</div>';
  modal.style.display = 'none';
  document.body.appendChild(modal);
  function openWx() {
    modal.style.display = 'flex';
    track('wechat_qr');
  }
  function closeWx() { modal.style.display = 'none'; }
  modal.addEventListener('click', function (e) { if (e.target === modal) closeWx(); });
  modal.querySelector('.wx-close').addEventListener('click', closeWx);
  modal.querySelector('.wx-copy').addEventListener('click', function () {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(WX_ID).then(function () { showToast('Copied ' + WX_ID); }, function () { showToast(WX_ID); });
    } else { showToast(WX_ID); }
    track('copy_wechat_id');
  });
  bar.querySelector('.cb-wechat').addEventListener('click', openWx);
  document.addEventListener('click', function (e) {
    var t = e.target.closest ? e.target.closest('[data-wx-open]') : null;
    if (t) openWx();
  });
  window.sanfanOpenWeChat = openWx;

  var toast = document.createElement('div');
  toast.className = 'cbar-toast';
  document.body.appendChild(toast);
  var toastTimer;
  function showToast(t) {
    toast.textContent = t;
    toast.classList.add('on');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toast.classList.remove('on'); }, 2200);
  }
  function track(channel) {
    if (typeof gtag === 'function') {
      gtag('event', 'contact_click', { channel: channel, page_path: location.pathname });
    }
  }
  bar.querySelector('.cb-wa').addEventListener('click', function () { track('whatsapp'); });
  bar.querySelector('.cb-mail').addEventListener('click', function () { track('email'); });
  bar.querySelector('.cb-copy').addEventListener('click', function () {
    track('copy_number');
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(TEL_TXT).then(
        function () { showToast('Copied ' + TEL_TXT); },
        function () { fallbackCopy(); }
      );
    } else { fallbackCopy(); }
  });
  function fallbackCopy() {
    var ta = document.createElement('textarea');
    ta.value = TEL_TXT;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); showToast('Copied ' + TEL_TXT); }
    catch (e) { showToast(TEL_TXT); }
    document.body.removeChild(ta);
  }
})();

// ---------- 页面内联系按钮 + 实时中国时间 ----------
(function () {
  var TEL = '+86 15959029082';
  function toastEl() { return document.querySelector('.cbar-toast'); }
  function show(msg) {
    var t = toastEl();
    if (!t) return;
    t.textContent = msg;
    t.classList.add('on');
    setTimeout(function () { t.classList.remove('on'); }, 2200);
  }
  document.querySelectorAll('[data-copy-phone]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(TEL).then(function () { show('Copied ' + TEL); }, function () { show(TEL); });
      } else { show(TEL); }
      if (typeof gtag === 'function') gtag('event', 'contact_click', { channel: 'copy_number', page_path: location.pathname });
    });
  });
  var clocks = document.querySelectorAll('.cn-time');
  if (clocks.length) {
    var upd = function () {
      var s = new Date().toLocaleTimeString('en-GB', { timeZone: 'Asia/Shanghai', hour: '2-digit', minute: '2-digit' });
      clocks.forEach(function (c) { c.textContent = s; });
    };
    upd();
    setInterval(upd, 30000);
  }
})();

// =====================================================================
// 导航引导 + 全站搜索（2026-09-12）
//   L1  Products 下拉（Mega Menu）：品类 3 分组 + 按用途入口
//   搜索  头部放大镜 → 浮层，索引懒加载
// 2026-09-12 起**分语言站也启用**：索引不再是英文一份 —— 每个语言有
// assets/data/navdata.<lang>.js，里面的产品名/分类名取自该语言的静态页面，
// 链接统一加 BASE 前缀（'de/'），所以不会出现指向英文页的死链。
//   英文 / 中文同页  -> navdata.js          -> window.SANFAN_NAV
//   de/ja/ko/fr/it/es -> navdata.<lang>.js  -> window.SANFAN_NAV_<LANG>
// =====================================================================
(function () {
  var cur = (document.documentElement.lang || 'en').toLowerCase();
  var LKEY = (cur && cur !== 'en' && cur.indexOf('zh') !== 0) ? cur.slice(0, 2) : '';
  var BASE = LKEY ? LKEY + '/' : '';        // 语言子目录前缀，拼在站内路径前

  var header = document.querySelector('.site-header');
  var navActions = document.querySelector('.nav-actions');
  var navLinks = document.querySelector('.nav-links');
  if (!header || !navActions || !navLinks) return;

  // 相对前缀：直接从 <link href> 上取，而不是数 pathname 层级。
  // file:// 下 pathname 是整个磁盘路径（/Users/…/index.html），数层级会得到
  // 一串 ../ 直接冲出站点目录；从样式表 href 反推 '' / '../' 两种都成立。
  var linkEl = document.querySelector('link[href*="styles.css"]');
  var linkHref = linkEl ? (linkEl.getAttribute('href') || '') : '';
  var ROOT = linkHref.replace(/assets\/css\/styles\.css.*$/, '');
  if (!/^(\.\.\/)*$/.test(ROOT)) {
    // 同 QR_IMG 的坑：目录形式 URL 的最后一段是目录，不能减 1
    var segs = location.pathname.split('/').filter(Boolean);
    var d = /\/$/.test(location.pathname) ? segs.length : Math.max(0, segs.length - 1);
    ROOT = new Array(d + 1).join('../');
  }
  var vm = linkHref.match(/[?&]v([A-Za-z0-9]+)/);
  var VER = vm ? vm[1] : '1';

  function isZh() { return document.documentElement.classList.contains('show-zh'); }
  function L(en, zh) { return isZh() ? zh : en; }
  function nameOf(e) { return isZh() ? (e.z || e.t) : e.t; }

  // 语言站的 UI 文案来自该语言索引里的 ui 字段（build_navdata_i18n.py 生成）；
  // 英文/中文同页没有 ui，退回内置双语串。rep 用来替换 {n}（产品总数）/ {q}（查询词）。
  var UI = null;
  function T(key, en, zh, rep) {
    var s = (UI && UI[key] != null) ? UI[key] : L(en, zh);
    if (rep) { for (var k in rep) s = s.split('{' + k + '}').join(rep[k]); }
    return s;
  }

  var ICON_SEARCH = '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">' +
    '<circle cx="11" cy="11" r="6.4" stroke="currentColor" stroke-width="1.9"/>' +
    '<path d="M15.8 15.8 20 20" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/></svg>';

  // ------------------------------------------------------------ 数据懒加载
  var dataPromise = null;
  var GLOBAL = LKEY ? 'SANFAN_NAV_' + LKEY.toUpperCase() : 'SANFAN_NAV';
  function loadData() {
    if (window[GLOBAL]) return Promise.resolve(window[GLOBAL]);
    if (dataPromise) return dataPromise;
    dataPromise = new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      // file:// 下 Chrome 不认带查询串的资源路径（会 ERR_FILE_NOT_FOUND），
      // 本地预览时省掉 ?v；线上照常带版本号。
      s.src = ROOT + 'assets/data/navdata' + (LKEY ? '.' + LKEY : '') + '.js' +
              (location.protocol === 'file:' ? '' : '?v=' + VER);
      s.onload = function () { window[GLOBAL] ? resolve(window[GLOBAL]) : reject(); };
      s.onerror = reject;
      document.head.appendChild(s);
    });
    return dataPromise;
  }

  // 数据到手后再套用文案：产品总数 {n} 来自索引，未加载前只能给个兜底
  function applyUI(D) {
    if (D) { D_ = D; UI = D.ui || null; }
    var n = (D_ && D_.total) || 147;
    input.setAttribute('placeholder', T('ph', 'Search ' + n + ' products, categories, applications…',
                                        '搜索 ' + n + ' 款产品、分类、应用场景…', { n: n }));
    srBtn.setAttribute('aria-label', T('aria', 'Search', '搜索'));
    menuItem.textContent = T('menu', 'Search products', '搜索产品');
  }
  var D_ = null;

  // ------------------------------------------------------------ L1 Mega Menu
  var mega = null;
  var hideTimer = null;
  var prodLink = null;
  navLinks.querySelectorAll('a').forEach(function (a) {
    if ((a.getAttribute('data-i18n') || '') === 'nav.products') prodLink = a;
  });
  // 语言页是静态翻译的，没有 data-i18n 锚点 → 退按 href 找「产品」入口
  if (!prodLink) {
    navLinks.querySelectorAll('a').forEach(function (a) {
      if (!prodLink && /products\.html$/.test(a.getAttribute('href') || '')) prodLink = a;
    });
  }
  if (prodLink) {
    prodLink.setAttribute('aria-haspopup', 'true');
    prodLink.setAttribute('aria-expanded', 'false');
    prodLink.setAttribute('aria-controls', 'mm-mega');
  }

  // 关闭延迟（hover-intent）。旧值 160ms 太短：鼠标从「产品」项下移到面板要穿过
  // 约 23px 的 header 空白（项高 22px、header 68px、面板贴 header 下沿），
  // 手速稍慢就被判成"已离开"，面板在指针到达前消失。
  var MEGA_CLOSE_DELAY = 320;
  // 与 CSS 的 hamburger 断点严格保持一致（2026-09-16 由 920 上调到 1279）
  var MEGA_BP = 1279;

  function closeMega() {
    clearTimeout(hideTimer);
    if (mega) mega.hidden = true;
    if (prodLink) {
      prodLink.classList.remove('mm-active');
      prodLink.setAttribute('aria-expanded', 'false');
    }
  }
  function scheduleClose() {
    clearTimeout(hideTimer);
    hideTimer = setTimeout(closeMega, MEGA_CLOSE_DELAY);
  }
  function cancelClose() { clearTimeout(hideTimer); }
  function megaOpen() { return !!(mega && !mega.hidden); }

  // 兜底关闭路径。旧代码只挂了 prodLink 与 mega 各自的 mouseleave ——
  // focus（Tab 键或点击触发项）打开面板后，若指针从没进过面板，mouseleave
  // 永不触发，菜单就**永远关不掉**（用户反馈「鼠标移到外围时导航栏不自动收缩」）。
  document.addEventListener('mouseover', function (e) {
    if (!megaOpen()) return;
    if (mega.contains(e.target) || (prodLink && prodLink.contains(e.target))) return;
    scheduleClose();                       // 移到「触发项 + 面板」之外 → 延时收起
  });
  document.addEventListener('mouseout', function (e) {  // 指针移出窗口
    if (!e.relatedTarget && !e.toElement) closeMega();
  });
  document.documentElement.addEventListener('mouseleave', closeMega);
  window.addEventListener('blur', closeMega);
  document.addEventListener('visibilitychange', function () { if (document.hidden) closeMega(); });
  window.addEventListener('scroll', closeMega, { passive: true });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' || e.keyCode === 27) closeMega();
  });

  function renderMega(D) {
    var byKey = {};
    D.cats.forEach(function (c) { byKey[c.k] = c; });
    var groups = D.groups.map(function (g) {
      var items = g.items.map(function (k) {
        var c = byKey[k];
        if (!c) return '';
        return '<a href="' + ROOT + BASE + c.k + '.html">' + L(c.en, c.zh) +
               '<em>' + c.n + '</em></a>';
      }).join('');
      return '<div class="mm-group"><span class="mm-glabel">' + L(g.en, g.zh) + '</span>' +
             '<div class="mm-links">' + items + '</div></div>';
    }).join('');
    var apps = D.apps.map(function (a) {
      return '<a href="' + ROOT + BASE + 'applications/' + a.k + '.html">' +
             '<span class="an">' + L(a.en, a.zh) + '</span>' +
             '<span class="ad">' + L(a.d, a.dz) + '</span></a>';
    }).join('');
    var html =
      '<div class="mm-panel">' +
        '<div class="mm-cats">' +
          '<p class="mm-eyebrow">' + T('shop_cat', 'Shop by category', '按品类选购') + '</p>' +
          groups +
          '<div class="mm-all"><a href="' + ROOT + BASE + 'products.html">' +
            T('view_all', 'View all ' + D.total + ' products', '查看全部 ' + D.total + ' 款', { n: D.total }) + ' &rarr;</a>' +
            ' &nbsp;·&nbsp; <a href="' + ROOT + BASE + 'materials.html">' +
            T('compare', 'Compare materials', '材质对比') + ' &rarr;</a>' +
          '</div>' +
        '</div>' +
        '<aside class="mm-apps">' +
          '<p class="mm-eyebrow">' + T('shop_app', 'Shop by application', '按用途选购') + '</p>' +
          apps +
          '<div class="mm-foot"><a href="' + ROOT + BASE + 'contact.html">' +
            T('not_sure', 'Not sure which spec?', '不确定选什么规格？') +
            '<span>' + T('send_price', 'Send your target price — we quote in 24h',
                            '把目标价发给我们 —— 24 小时内报价') + '</span></a></div>' +
        '</aside>' +
      '</div>';
    if (mega) mega.innerHTML = html;
  }

  function ensureMega(D) {
    if (!mega) {
      mega = document.createElement('div');
      mega.className = 'mm-wrap';
      mega.id = 'mm-mega';
      mega.hidden = true;
      mega.addEventListener('mouseenter', cancelClose);
      mega.addEventListener('mouseleave', scheduleClose);
      header.appendChild(mega);
    }
    renderMega(D);
  }

  if (prodLink) {
    prodLink.addEventListener('mouseenter', function () {
      if (window.innerWidth <= MEGA_BP) return;
      cancelClose();
      loadData().then(function (D) {
        D_ = D; UI = D.ui || null; applyUI(D); ensureMega(D);
        if (prodLink.matches(':hover')) {
          mega.hidden = false;
          prodLink.classList.add('mm-active');
          prodLink.setAttribute('aria-expanded', 'true');
        }
      }).catch(function () {});
    });
    prodLink.addEventListener('mouseleave', scheduleClose);
    prodLink.addEventListener('focus', function () {
      if (window.innerWidth <= MEGA_BP) return;
      loadData().then(function (D) {
        D_ = D; UI = D.ui || null; applyUI(D);
        ensureMega(D); mega.hidden = false; prodLink.classList.add('mm-active');
        prodLink.setAttribute('aria-expanded', 'true');
      }).catch(function () {});
    });
  }

  // ------------------------------------------------------------ 搜索
  var modal = document.createElement('div');
  modal.className = 'sr-modal';
  modal.hidden = true;
  modal.innerHTML =
    '<div class="sr-box" role="dialog" aria-modal="true">' +
      '<div class="sr-inputrow">' + ICON_SEARCH +
        '<input class="sr-input" type="search" autocomplete="off" ' +
        'placeholder="' + L('Search 147 products, categories, applications…',
                            '搜索 147 款产品、分类、应用场景…') + '">' +
        '<span class="sr-esc">ESC</span>' +
      '</div>' +
      '<div class="sr-results"></div>' +
      '<div class="sr-hints"><p class="h-cap"></p><div class="h-row"></div></div>' +
    '</div>';
  document.body.appendChild(modal);   // 必须挂进 DOM，否则 hidden 切换看不到任何东西

  var srBtn = document.createElement('button');
  srBtn.type = 'button';
  srBtn.className = 'sr-btn';
  srBtn.setAttribute('aria-label', L('Search', '搜索'));
  srBtn.innerHTML = ICON_SEARCH;
  navActions.insertBefore(srBtn, navActions.firstChild);

  // 窄屏：导航栏放不下图标 → 改成移动菜单里的一项
  // href 指向真实的产品总览页（与 mega menu 的「全部产品」入口同目标）。
  // 点击由下方 preventDefault 接管去开搜索框；而中键 / 新标签 / 脚本未跑到这里时
  // 落到产品总览，而不是 href="#" 跳回页顶。
  var menuItem = document.createElement('a');
  menuItem.className = 'nav-search-item';
  menuItem.href = ROOT + BASE + 'products.html';
  menuItem.textContent = L('Search products', '搜索产品');
  navLinks.insertBefore(menuItem, navLinks.firstChild);

  var input = modal.querySelector('.sr-input');
  var resultsEl = modal.querySelector('.sr-results');
  var hintsEl = modal.querySelector('.sr-hints');
  var D = null;
  applyUI(null);          // 先套一次；索引加载后会用 {n} 的真实值再套一次
  var items = [];
  var active = -1;

  // 热门词：语言站用索引里译好的（ui.hot），英文/中文同页用内置双语
  var HOT = function () {
    if (UI && UI.hot && UI.hot.length) return UI.hot;
    return isZh()
      ? ['TPE 瑜伽垫', '高温瑜伽', '泡沫轴', '跳绳', '筋膜枪', '瑜伽馆', '材质对比', '贴牌']
      : ['TPE yoga mat', 'hot yoga', 'foam roller', 'jump rope', 'fascia gun',
         'studio', 'materials', 'private label'];
  };

  var TYPE_KEY = {
    product: 't_product', category: 't_category',
    application: 't_application', page: 't_page'
  };
  var TYPE_FALLBACK = {
    product: ['Product', '产品'], category: ['Category', '分类'],
    application: ['Solution', '方案'], page: ['Page', '页面']
  };

  function norm(s) { return (s || '').toLowerCase(); }

  function scoreOne(e, q) {
    var t = norm(e.t), z = norm(e.z), c = norm(e.c), cz = norm(e.cz), k = norm(e.k), s = 0;
    if (t === q) s += 100; else if (t.indexOf(q) === 0) s += 84; else if (t.indexOf(q) >= 0) s += 62;
    if (z) { if (z === q) s += 96; else if (z.indexOf(q) >= 0) s += 74; }
    if (cz && cz.indexOf(q) >= 0) s += 48;
    if (c && c.indexOf(q) >= 0) s += 44;
    if (k && k.indexOf(q) >= 0) s += 30;
    return s;
  }

  // 中文说法 ↔ 英文说法互通：搜「泡沫轴」也能出 foam roller，
  // 否则中文用户只会搜到中文里恰好含这三个字的产品名。
  function expandToken(tok) {
    var out = [tok];
    var syn = (D && D.syn) || {};
    for (var key in syn) {
      if (key === tok || tok.indexOf(key) >= 0 || key.indexOf(tok) >= 0) out.push(syn[key]);
    }
    return out;
  }

  function search(q) {
    if (!D) return [];
    var toks = norm(q).split(/[\s,，、]+/).filter(Boolean).map(expandToken);
    if (!toks.length) return [];
    var hits = [];
    for (var i = 0; i < D.idx.length; i++) {
      var e = D.idx[i], total = 0, ok = true;
      for (var j = 0; j < toks.length; j++) {
        var best = 0;
        for (var m = 0; m < toks[j].length; m++) {
          var v = scoreOne(e, toks[j][m]);
          if (v > best) best = v;
        }
        if (!best) { ok = false; break; }
        total += best;
      }
      if (ok) {
        // 产品优先于分类/页面：同分时客户要的是具体款，不是导航页
        hits.push({ e: e, s: total + (e.y === 'product' ? 12 : e.y === 'category' ? 8 : 0) });
      }
    }
    hits.sort(function (a, b) { return b.s - a.s; });
    return hits.slice(0, 9).map(function (h) { return h.e; });
  }

  function thumbHTML(e) {
    if (e.img) {
      return '<span class="sr-thumb"><img src="' + ROOT + e.img +
             '" alt="" loading="lazy"></span>';
    }
    var ch = (nameOf(e) || '?').replace(/[^A-Za-z0-9\u4e00-\u9fff]/, '').charAt(0).toUpperCase();
    return '<span class="sr-thumb sr-thumb-txt">' + ch + '</span>';
  }

  function render(q) {
    var sub = '';
    if (!q) {
      resultsEl.innerHTML = '';
      var hot = HOT();
      hintsEl.querySelector('.h-cap').textContent = T('popular', 'Popular searches', '热门搜索');
      hintsEl.querySelector('.h-row').innerHTML = hot.map(function (h) {
        return '<button type="button" data-q="' + h + '">' + h + '</button>';
      }).join('');
      hintsEl.style.display = '';
      items = []; active = -1;
      return;
    }
    items = search(q);
    hintsEl.style.display = 'none';
    if (!items.length) {
      resultsEl.innerHTML = '<div class="sr-empty">' +
        T('empty',
          'No match for “' + q + '”. Tell us the spec and we will build it — ' +
          'or ask us directly on WhatsApp.',
          '没有匹配「' + q + '」的结果。把规格发给我们，我们来做 —— 或直接 WhatsApp 联系我们。',
          { q: q }) +
        '</div>';
      active = -1;
      return;
    }
    resultsEl.innerHTML = items.map(function (e, i) {
      var tf = TYPE_FALLBACK[e.y] || TYPE_FALLBACK.page;
      sub = isZh() ? (e.cz || '') : (e.c || '');
      return '<a class="sr-item' + (i === 0 ? ' on' : '') + '" href="' + ROOT + BASE + e.u + '">' +
        thumbHTML(e) +
        '<span class="sr-txt"><span class="sr-t">' + nameOf(e) + '</span>' +
        '<span class="sr-s">' + sub + '</span></span>' +
        '<span class="sr-badge">' + T(TYPE_KEY[e.y] || TYPE_KEY.page, tf[0], tf[1]) + '</span></a>';
    }).join('');
    active = 0;
  }

  function highlight(i) {
    var list = resultsEl.querySelectorAll('.sr-item');
    if (!list.length) return;
    if (i < 0) i = list.length - 1;
    if (i >= list.length) i = 0;
    list.forEach(function (a, n) { a.classList.toggle('on', n === i); });
    active = i;
    if (list[i].scrollIntoView) list[i].scrollIntoView({ block: 'nearest' });
  }

  function openSearch() {
    loadData().then(function (d) { D = d; D_ = d; UI = d.ui || null; applyUI(d); }).catch(function () {});
    modal.hidden = false;
    document.body.style.overflow = 'hidden';
    loadData().then(function (d) {
      D = d;
      render(input.value.trim());
    }).catch(function () {});
    render('');
    setTimeout(function () { input.focus(); }, 30);
  }
  function closeSearch() {
    modal.hidden = true;
    document.body.style.overflow = '';
  }

  srBtn.addEventListener('click', openSearch);
  menuItem.addEventListener('click', function (ev) { ev.preventDefault(); navLinks.classList.remove('open'); openSearch(); });
  modal.addEventListener('click', function (ev) { if (ev.target === modal) closeSearch(); });
  modal.querySelector('.sr-esc').addEventListener('click', closeSearch);

  input.addEventListener('input', function () { render(input.value.trim()); });
  input.addEventListener('keydown', function (ev) {
    if (ev.key === 'ArrowDown') { ev.preventDefault(); highlight(active + 1); }
    else if (ev.key === 'ArrowUp') { ev.preventDefault(); highlight(active - 1); }
    else if (ev.key === 'Enter') {
      var on = resultsEl.querySelector('.sr-item.on') || resultsEl.querySelector('.sr-item');
      if (on) { ev.preventDefault(); location.href = on.getAttribute('href'); }
    } else if (ev.key === 'Escape') { closeSearch(); }
  });
  hintsEl.addEventListener('click', function (ev) {
    var b = ev.target.closest ? ev.target.closest('button[data-q]') : null;
    if (!b) return;
    input.value = b.getAttribute('data-q');
    render(input.value.trim());
    input.focus();
  });

  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape' && !modal.hidden) { closeSearch(); return; }
    var tag = (ev.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea') return;
    if (ev.key === '/' || ((ev.metaKey || ev.ctrlKey) && (ev.key === 'k' || ev.key === 'K'))) {
      ev.preventDefault();
      openSearch();
    }
  });

  // ------------------------------------------------------------ 语言切换后重建
  window.addEventListener('sanfan-langchange', function () {
    applyUI(D);
    if (!modal.hidden) render(input.value.trim());
    if (D) renderMega(D);
  });

  // 页面空闲时预热，让首次悬停 / 首次搜索即时响应
  function warm() {
    loadData().then(function (d) {
      D = d; applyUI(d); ensureMega(d);
    }).catch(function () {});
  }
  if (window.requestIdleCallback) window.requestIdleCallback(warm, { timeout: 3000 });
  else window.addEventListener('load', function () { setTimeout(warm, 1200); });
})();

/* ---------------------------------------------------------------- 画册图灯箱
   2026 画册页搬进族页后，图上印的规格字很小，采购商需要放大看。
   做法：事件委托 + 惰性建 DOM —— 全站 1331 页共用 main.js，
   没有 .cat-fig 的页面零开销、零副作用（不建节点、不绑元素级监听）。
   键盘：Esc 关闭；打开时焦点落到关闭按钮，关闭后归还触发元素。
   ⚠️ .cat-zoom 本身是 <a href="原图">，这里 preventDefault 后接管 ——
      无 JS 或脚本报错时仍按原链接新窗口打开，功能不丢。 */
(function () {
  var lb, im, cap, lastFocus;

  function build() {
    lb = document.createElement('div');
    lb.className = 'lb';
    lb.setAttribute('role', 'dialog');
    lb.setAttribute('aria-modal', 'true');
    lb.setAttribute('aria-label', 'Catalogue page');
    lb.innerHTML = '<button class="lb-close" type="button" aria-label="Close">\u00d7</button>' +
                   '<img alt="" /><p class="lb-cap"></p>';
    document.body.appendChild(lb);
    im = lb.querySelector('img');
    cap = lb.querySelector('.lb-cap');
    lb.querySelector('.lb-close').addEventListener('click', close);
    lb.addEventListener('click', function (e) { if (e.target === lb) close(); });
  }

  function open(src, alt, caption) {
    if (!lb) build();
    lastFocus = document.activeElement;
    im.setAttribute('src', src);
    im.setAttribute('alt', alt || '');
    cap.textContent = caption || '';
    lb.classList.add('is-open');
    document.body.classList.add('lb-open');
    lb.querySelector('.lb-close').focus();
  }

  function close() {
    if (!lb || !lb.classList.contains('is-open')) return;
    lb.classList.remove('is-open');
    document.body.classList.remove('lb-open');
    im.removeAttribute('src');
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  function fromFig(fig, src) {
    if (!fig) return;
    var i = fig.querySelector('img');
    var c = fig.querySelector('figcaption');
    open(src || (i && (i.currentSrc || i.src)), i && i.getAttribute('alt'),
         c ? c.textContent.replace(/\s+/g, ' ').trim() : '');
  }

  document.addEventListener('click', function (e) {
    var el = e.target;
    if (!el || !el.closest) return;
    var a = el.closest('.cat-zoom');           // 「放大查看」链接 → 就地放大
    if (a) {
      e.preventDefault();
      fromFig(a.closest('.cat-fig'), a.getAttribute('href'));
      return;
    }
    var img = el.closest('.cat-fig img');      // 点图本身 → 同样放大
    if (img) fromFig(img.closest('.cat-fig'), null);
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' || e.keyCode === 27) close();
  });
})();
