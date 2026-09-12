# -*- coding: utf-8 -*-
"""L3 场景落地页数据 —— 6 个「按用途/按客户生意」的采购入口。

设计原则：
1. 每页是一份**采购方案**，不是产品清单：先给整单配置表（品项 / 用在什么环节 / 建议规格），
   再落到具体 SKU。客户不懂材质也能照着下单。
2. 产品只从既有 141 款里挑（不新增 SKU），靠组合与规格建议产生价值。
3. FAQ 与配置表写进静态 HTML，供 Google 与 AI 抓取（GEO 资产）。
"""

ICON_YOGA = ('<svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">'
             '<rect x="3" y="9" width="18" height="4" rx="2" stroke="#0e6b5c" stroke-width="1.8"/>'
             '<path d="M6 13v7M18 13v7" stroke="#0e6b5c" stroke-width="1.8" stroke-linecap="round"/></svg>')
ICON_GYM = ('<svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">'
            '<path d="M4 9v6M8 7v10M16 7v10M20 9v6" stroke="#0e6b5c" stroke-width="1.8" stroke-linecap="round"/>'
            '<path d="M11 12h2" stroke="#0e6b5c" stroke-width="1.8" stroke-linecap="round"/></svg>')
ICON_HOTEL = ('<svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">'
              '<path d="M3 20h18M5 20V9l7-5 7 5v11" stroke="#0e6b5c" stroke-width="1.8" '
              'stroke-linecap="round" stroke-linejoin="round"/></svg>')
ICON_RETAIL = ('<svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">'
               '<path d="M4 8h16l-1 12H5L4 8Z" stroke="#0e6b5c" stroke-width="1.8" stroke-linejoin="round"/>'
               '<path d="M9 8V6a3 3 0 0 1 6 0v2" stroke="#0e6b5c" stroke-width="1.8" stroke-linecap="round"/></svg>')
ICON_RECOVERY = ('<svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">'
                 '<circle cx="8" cy="12" r="4" stroke="#0e6b5c" stroke-width="1.8"/>'
                 '<circle cx="17" cy="9" r="2.6" stroke="#0e6b5c" stroke-width="1.8"/>'
                 '<circle cx="17" cy="16" r="2.6" stroke="#0e6b5c" stroke-width="1.8"/></svg>')
ICON_HOME = ('<svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">'
             '<path d="M3 7h11v8H3zM14 10h4l3 3v2h-7z" stroke="#0e6b5c" stroke-width="1.8" stroke-linejoin="round"/>'
             '<circle cx="7" cy="18" r="1.8" stroke="#0e6b5c" stroke-width="1.6"/>'
             '<circle cx="17" cy="18" r="1.8" stroke="#0e6b5c" stroke-width="1.6"/></svg>')

APPS = [
    # =============================================================== 1 瑜伽馆 / 普拉提工作室
    {
        "key": "yoga-pilates-studios",
        "en": "Yoga & Pilates Studios",
        "zh": "瑜伽馆与普拉提工作室",
        "icon": ICON_YOGA,
        "tag_en": "Full studio fit-out on one PO",
        "tag_zh": "一单配齐整个馆",
        "card_en": "Opening a studio or refitting one — mats, blocks, bolsters, straps and "
                   "hammocks bundled so they arrive together, in your colours.",
        "card_zh": "开新馆或旧馆翻新 —— 垫子、砖、抱枕、伸展带与吊床打包同柜到货，统一你的配色。",
        "kit_en": "Mats · blocks · bolsters · straps · hammocks · reformer mats",
        "kit_zh": "垫类 · 瑜伽砖 · 抱枕 · 伸展带 · 吊床 · 器械垫",
        "title_seo": "Yoga &amp; Pilates Studio Equipment Manufacturer | OEM / ODM — SANFAN",
        "desc_seo": "Fit out a yoga or Pilates studio from one factory: TPE, PU-rubber, cork and "
                    "suede mats, blocks, bolsters, reformer mats and aerial hammocks with your "
                    "logo. MOQ 100 pcs, 7-day sampling, FOB Xiamen.",
        "hero_en": "Fit out a whole studio on one purchase order. Teacher mats, member mats, "
                   "blocks, straps, bolsters, reformer mats and aerial hammocks — same factory, "
                   "same colour system, one shipment, your logo on all of it. Whether it is a "
                   "10-person boutique or a 200-member chain, we spec the kit to your class mix "
                   "and your budget.",
        "hero_zh": "一张订单配齐整个馆。教练垫、会员垫、瑜伽砖、伸展带、抱枕、器械垫与空中吊床 —— "
                   "同一家工厂、同一套配色、同柜到货，全部可加你的 Logo。无论 10 人精品馆还是 "
                   "200 人连锁，我们按你的课程结构与预算配货。",
        "kit": [
            ("Main practice mats", "主课垫",
             "Daily classes and member mats — the highest-volume line in a studio order",
             "日常大课与会员垫，馆内用量最大的一项",
             "TPE 183 × 61 cm, 6–8 mm. Widen to 80 / 90 cm for dynamic or partner classes",
             "TPE 183×61 cm、6–8 mm；动态课或双人课选 80 / 90 cm 加宽"),
            ("Hot yoga / vinyasa mats", "高温与流瑜伽垫",
             "Sweaty sessions where sweat-soaked grip is what members judge you on",
             "大汗课程 —— 湿手防滑是会员评价的核心",
             "PU top + natural rubber base, 4.5–5 mm; suede surface also grips more when wet",
             "PU 面层 + 天然橡胶底、4.5–5 mm；麂皮面层同样遇汗更防滑"),
            ("Meditation & yin corner", "冥想与阴瑜伽区",
             "A separate quiet zone — round mats and bolsters read as a considered studio",
             "独立安静区 —— 圆形垫与抱枕让场馆显得讲究",
             "Round 60 × 60 cm, 4.5 mm; bolsters 64 × 24 × 13 cm; cork for a warmer look",
             "圆形 60×60 cm、4.5 mm；抱枕 64×24×13 cm；软木面更暖"),
            ("Props kit", "辅具套组",
             "Blocks, straps, rings and mini balls — usually 20–30 sets per classroom",
             "瑜伽砖、伸展带、普拉提圈与小瑜伽球 —— 每间教室通常配 20–30 套",
             "High-density EVA blocks, TPE loops, silicone Pilates rings; colour-matched to mats",
             "高密度 EVA 砖、TPE 环形带、硅胶普拉提圈；与垫子同色系"),
            ("Reformer mats", "普拉提器械垫",
             "Cut to your machine's headrest and carriage dimensions, with your studio logo",
             "按器械头枕与滑车尺寸裁切，可压印会馆 Logo",
             "Made to order to your machine drawing; anti-slip base, printed or embossed logo",
             "按器械图纸定制；防滑底，印花或压印 Logo"),
            ("Aerial hammocks", "空中瑜伽吊床",
             "Aerial and fly-pilates classes — the highest-margin add-on in a studio fit-out",
             "空中瑜伽与空中普拉提，整馆项目中毛利最高的一项",
             "5 × 2.8 m or 4 × 2.8 m, high-strength polyester / 210T nylon, ceiling kit available",
             "5×2.8 m 或 4×2.8 m，高强涤纶 / 210T 尼龙，可配吊装件"),
            ("Bags & storage", "收纳与零售",
             "Mat bags and block covers — for member retail or just to keep the room tidy",
             "瑜伽包与砖套 —— 门店零售或单纯让教室更整洁",
             "Custom print, your logo, retail-ready hang tag",
             "可印花、加 Logo，含零售吊牌"),
        ],
        "products": [
            "ym1", "ym2", "eco-friendly-tpe-yoga-mat", "alignment-line-tpe-yoga-mat",
            "ym5", "solid-black-pu-rubber-yoga-mat", "pu-rubber-yoga-mat-with-alignment-lines",
            "cork-rubber-yoga-mat", "pr3", "round-mandala-meditation-mat", "tpe-meditation-mat",
            "pilates-reformer-mat-custom-logo", "pilates-reformer-mat-mandala", "pr4",
            "eva-yoga-block", "yoga-bolster", "yoga-bag", "pr1", "tpe-resistance-loop-band",
            "pilates-ring-2",
        ],
        "guide_en": "Studios usually order in two waves: a fit-out wave (mats for the room, "
                    "props per class, hammocks or reformers) and a reorder wave (replacing worn "
                    "member mats once a year). Order both in the same colour system the first time "
                    "— reorders match exactly because we keep your colour and logo files on record. "
                    "Tell us your class count and room size and we will come back with a BOM "
                    "(bill of materials) and a suggested split between teacher-grade and member-grade mats.",
        "guide_zh": "瑜伽馆通常分两批下单：开业配置批（教室垫、按班配辅具、吊床或器械）与补货批"
                    "（会员垫每年替换一次）。第一次就把两批放进同一套配色体系 —— 我们会存档你的"
                    "颜色与 Logo 文件，之后的补货能做到完全一致。告诉我们教室数量与面积，"
                    "我们会回一份配置清单（BOM），并建议教练级与会员级垫子的配比。",
        "faq": [
            ("Can you supply a complete studio fit-out, not just mats?",
             "你们能配齐整个馆，而不只是垫子吗？",
             "Yes. Mats, blocks, straps, bolsters, Pilates rings, mini balls, reformer mats, "
             "aerial hammocks and bags all come from our own plants, so one PO covers the room. "
             "We ship them together in one container, which is usually 15–25% cheaper than "
             "sourcing each item separately.",
             "可以。垫类、瑜伽砖、伸展带、抱枕、普拉提圈、小瑜伽球、器械垫、空中吊床与包袋都出自"
             "我们自有工厂，一张订单就能覆盖整间教室，同柜出货通常比分开采购省 15–25%。"),
            ("What is the MOQ for a studio order?",
             "瑜伽馆订单的起订量是多少？",
             "100 pcs per SKU, and you can mix SKUs to reach a container. A typical boutique "
             "studio order is 40–60 mats plus 20 prop sets; a chain order is 300–800 mats. "
             "Sampling takes 7 days with your logo and colour.",
             "单款 100 片起订，可多款拼柜。精品馆通常订 40–60 张垫 + 20 套辅具；"
             "连锁馆在 300–800 张。打样 7 天，可带你的 Logo 与颜色。"),
            ("Can you match our existing studio colours?",
             "能按我们现有的会馆配色做吗？",
             "Send a Pantone code, a fabric swatch or even a photo — we match the mat surface, "
             "the block and the bag to it, and keep the recipe on file so every reorder is "
             "identical. Double-colour mats and custom block colours are standard, not special.",
             "发 Pantone 号、色卡甚至照片都行 —— 我们把垫面、瑜伽砖与包袋统一到同一个色，"
             "并归档配方，保证每次补货完全一致。双色垫与定制砖色都是常规能力，不是特例。"),
        ],
    },

    # =============================================================== 2 健身房 / 团课俱乐部
    {
        "key": "gyms-fitness-clubs",
        "en": "Gyms & Fitness Clubs",
        "zh": "健身房与团课俱乐部",
        "icon": ICON_GYM,
        "tag_en": "One colour system across the whole floor",
        "tag_zh": "整层设备一套配色",
        "card_en": "Free weights, floor mats, ropes, bands and recovery tools — one supplier, "
                   "one colour system, ready for your own branding.",
        "card_zh": "自由重量、地垫、跳绳、弹力带与恢复工具 —— 一家供应商、一套配色，可贴你的牌。",
        "kit_en": "Silicone weights · mats · ropes · bands · rollers · recovery",
        "kit_zh": "硅胶配重 · 地垫 · 跳绳 · 弹力带 · 泡沫轴 · 恢复工具",
        "title_seo": "Gym &amp; Fitness Club Equipment Manufacturer | OEM / ODM — SANFAN",
        "desc_seo": "Factory-direct gym equipment for fitness clubs: silicone dumbbells, barbells, "
                    "weighted balls and rings, floor mats, jump ropes, resistance bands and "
                    "recovery tools. One colour system, private-label ready, MOQ 100 pcs.",
        "hero_en": "The whole training floor from one factory. Silicone-skinned free weights in a "
                   "single colour system, mats for the functional zone, ropes and bands for group "
                   "classes, rollers and guns for the recovery corner. One supplier means one "
                   "colour reference, one quality standard and one shipment — and your logo can go "
                   "on all of it.",
        "hero_zh": "整层训练区，一家工厂供齐。硅胶包覆自由重量统一配色，功能性训练区地垫，"
                   "团课用跳绳与弹力带，恢复角的泡沫轴与筋膜枪。一家供应商意味着一个色号、"
                   "一套品质标准、一次到货 —— 而且全都可以打你的 Logo。",
        "kit": [
            ("Functional-zone mats", "功能性训练区地垫",
             "Sled tracks, kettlebells and bodyweight circuits need a hard-wearing surface",
             "雪橇道、壶铃与自重循环训练区需要耐用面层",
             "High-density TPE or PU + rubber, 8–12 mm; 183 × 61–90 cm, cut lengths on request",
             "高密度 TPE 或 PU + 橡胶、8–12 mm；183×61–90 cm，长度可定制"),
            ("Free weights", "自由重量",
             "The one category where a consistent colour system reads as a premium club",
             "唯一一个「配色统一就显高级」的品类",
             "Silicone-coated dumbbells, barbells, weighted balls and rings — iron core, "
             "silicone skin, no paint chipping",
             "硅胶包覆哑铃、杠铃、配重球与配重环 —— 铸铁芯 + 硅胶外壳，不掉漆"),
            ("Group-class equipment", "团课器材",
             "HIIT, jump-rope and circuits classes: high turnover, low unit cost",
             "HIIT、跳绳与循环课 —— 高周转、低单价",
             "Speed, counting and cordless ropes; power bands, tube sets and loop bands in "
             "graded resistance",
             "速度款、计数款与无绳跳绳；力量带、拉力管与环形带，阻力分级"),
            ("Core & functional", "核心与功能训练",
             "Ab rollers, fitness boards and steppers for the small-equipment corner",
             "健腹轮、健身板与登山机，配齐小器械角",
             "Ab rollers with resistance bands, multi-function boards, compact hydraulic steppers",
             "带阻力带健腹轮、多功能健身板、紧凑型液压登山机"),
            ("Recovery corner", "恢复角",
             "Post-training self-myofascial release — increasingly a member expectation",
             "训练后自主筋膜放松 —— 越来越多会员的期待项",
             "EVA and EPP rollers (solid, hollow, wolf-tooth), vibrating rollers, fascia guns, "
             "balls and sticks",
             "EVA 与 EPP 泡沫轴（实心 / 空心 / 狼牙）、震动款、筋膜枪、筋膜球与按摩棒"),
            ("Retail shelf", "会员零售",
             "Optional: sell the same SKUs at the front desk under your own brand",
             "可选：同一批 SKU 挂你的牌，在前台零售",
             "Blocks, bags, mini balls, resistance sets with retail packaging and barcode",
             "瑜伽砖、包袋、小瑜伽球、弹力带套装，含零售包装与条码"),
        ],
        "products": [
            "ym1", "solid-black-pu-rubber-yoga-mat", "eco-friendly-tpe-yoga-mat",
            "triangular-silicone-dumbbell", "wave-silicone-barbell", "weighted-training-ball",
            "weighted-training-ring", "silicone-wrist-ankle-weights", "fi2", "fi5",
            "ab-roller-training-set", "multi-function-fitness-board", "adjustable-stair-climber",
            "speed-jump-rope", "smart-counting-jump-rope", "cordless-jump-rope",
            "power-band", "exercise-bands", "resistance-tube-2",
            "fr2", "vibrating-foam-roller", "fascia-gun-3", "fascial-sphere-3",
        ],
        "guide_en": "Gyms buy in three buckets: capital equipment at fit-out, consumables on an "
                    "annual cycle (ropes, bands, mats) and retail stock at the front desk. The "
                    "single biggest saving is ordering all three from one factory on one colour "
                    "reference — no mismatch between the dumbbell rack and the mats, no three "
                    "different lead times. We can also laser-engrave your club logo into the "
                    "silicone weights and mats at no tooling cost.",
        "guide_zh": "健身房采购通常分三块：开业时的固定资产、年度循环的耗材（跳绳、弹力带、垫子）、"
                    "以及前台的零售库存。最大的省钱点是把三块放进同一家工厂、同一个色号 —— "
                    "哑铃架与地垫不会色差，也不用等三个交期。硅胶配重与地垫上的会所 Logo "
                    "可激光雕刻，不收开模费。",
        "faq": [
            ("Do the silicone weights chip or peel with daily gym use?",
             "硅胶配重日常高频使用会掉漆、脱皮吗？",
             "No. The skin is a single moulded silicone shell over a cast-iron core — there is "
             "no paint layer to chip. Tested against ROHS / CE / REACH, and the surface is "
             "wipe-clean, which matters in a shared training floor.",
             "不会。外壳是整体模压硅胶包裹铸铁芯，本身没有漆层可掉。通过 ROHS / CE / REACH 检测，"
             "表面可直接擦拭清洁 —— 公共训练区很重要。"),
            ("Can we order the whole floor in our club colours?",
             "能按我们会所配色订整层设备吗？",
             "Yes, and we recommend it. Send your two accent colours plus your logo; we apply "
             "them across mats, dumbbells, barbells, balls, rings, ropes, bands and rollers, "
             "then keep the recipe on file. Reorders match because the files never leave us.",
             "可以，而且我们建议这样做。给我们两个主色 + Logo，我们统一应用到地垫、哑铃、杠铃、"
             "配重球、配重环、跳绳、弹力带与泡沫轴上，并归档配方，之后补货完全一致。"),
            ("What about lead time for a club-scale order?",
             "俱乐部级别的订单交期多久？",
             "Sampling 7 days. Mass production is typically 20–30 days depending on mix, and we "
             "run 12 production lines with 200,000 mats/month capacity, so a mixed floor order "
             "does not have to wait for a single slow SKU.",
             "打样 7 天。量产一般 20–30 天，视组合而定。我们有 12 条产线、月产 20 万张垫的产能，"
             "整层混合订单不会被某一个慢款拖住。"),
        ],
    },

    # =============================================================== 3 酒店 / 度假村 / SPA
    {
        "key": "hotels-resorts-spas",
        "en": "Hotels, Resorts & Spas",
        "zh": "酒店、度假村与 SPA",
        "icon": ICON_HOTEL,
        "tag_en": "Hospitality-grade, housekeeping-friendly",
        "tag_zh": "酒店级品质，易维护",
        "card_en": "Quiet, low-odour mats and props with your logo — the in-room yoga kit and "
                   "the spa retail range.",
        "card_zh": "低气味静音垫与辅具，可加酒店 Logo —— 客房瑜伽套装与 SPA 零售款。",
        "kit_en": "In-room mats · meditation rounds · cork & suede retail · travel mats",
        "kit_zh": "客房垫 · 圆形冥想垫 · 软木与麂皮零售款 · 旅行垫",
        "title_seo": "Hotel &amp; Resort Yoga Mat Supplier | Custom Logo OEM — SANFAN",
        "desc_seo": "Hospitality-grade yoga mats with your hotel logo: low-odour TPE and natural "
                    "rubber mats for guest rooms, round meditation mats for wellness areas, cork "
                    "and suede retail ranges for the spa. MOQ 100 pcs, 7-day sampling.",
        "hero_en": "Wellness floors, spa treatment rooms and in-room yoga kits, built for "
                   "housekeeping rather than shelf appeal. Low-odour materials, wipe-clean "
                   "surfaces, mat sizes that fit a standard wardrobe shelf — and your crest "
                   "embossed on every mat. We also produce the cork and suede retail range your "
                   "spa shop sells at the door.",
        "hero_zh": "康体楼层、SPA 理疗室与客房瑜伽套装 —— 按客房部的维护逻辑做，而不是按货架好看做。"
                   "低气味材质、可擦洗表面、能放进标准衣柜层的垫子尺寸，每张垫子压印你的店徽。"
                   "我们同时生产 SPA 门口零售的软木与麂皮款。",
        "kit": [
            ("In-room yoga mats", "客房瑜伽垫",
             "The mat that lives in the wardrobe — rolled tight, low odour, easy to wipe",
             "放在衣柜里的垫子 —— 卷径小、气味低、好擦洗",
             "TPE 173–183 × 61 cm, 6 mm; embossed or laser-engraved logo; carry strap optional",
             "TPE 173–183×61 cm、6 mm；压印或激光雕刻 Logo；可选背带"),
            ("Wellness / meditation area", "康体与冥想区",
             "A dedicated quiet floor or studio — round mats read as designed, not improvised",
             "专属安静区或教室 —— 圆形垫看起来是设计过的，而不是临时凑的",
             "Round 60 × 60 cm, 4.5 mm in cork or PU; bolsters 64 × 24 × 13 cm",
             "圆形 60×60 cm、4.5 mm，软木或 PU；抱枕 64×24×13 cm"),
            ("Poolside & spa treatment", "泳池边与 SPA 理疗",
             "Wet, chlorinated or oily environments where grip and cleaning matter most",
             "潮湿、含氯或带油环境 —— 最考验防滑与清洁",
             "PU + natural rubber, 4.5–5 mm; cork surface; closed-cell so it does not soak water",
             "PU + 天然橡胶、4.5–5 mm；软木面层；闭孔结构不吸水"),
            ("Spa retail range", "SPA 零售款",
             "Sold at the spa door or gifted to suite guests — needs print, not just function",
             "在 SPA 前台售卖或赠予套房客人 —— 要能印花，不只要好用",
             "Suede microfibre and cork surfaces take HD prints; your artwork or ours",
             "麂皮超细纤维与软木面层可做高清印花，可来图或我们出图"),
            ("Travel mats", "旅行垫",
             "Concierge and airline-kit item — 1.5 mm, folds or rolls into a tote",
             "礼宾与航空套装用品 —— 1.5 mm，可折叠或卷进手提袋",
             "Ultra-thin PU rubber travel mat, 1.5 mm; printed carry sleeve",
             "超薄 PU 橡胶旅行垫、1.5 mm；可印收纳袋"),
            ("Props & storage", "辅具与收纳",
             "Blocks, straps and bags so the kit looks complete in the room",
             "瑜伽砖、伸展带与包袋，让客房里的套装看起来是完整的",
             "EVA blocks, TPE straps, custom-printed bags with your property name",
             "EVA 瑜伽砖、TPE 伸展带、可印酒店名的包袋"),
        ],
        "products": [
            "ym1", "alignment-line-tpe-yoga-mat", "ym5", "cork-rubber-yoga-mat",
            "two-tone-cork-tpe-yoga-mat", "tpe-meditation-mat", "round-mandala-meditation-mat",
            "pu-meditation-mat-set", "pr3", "yoga-bolster", "aurora-gradient-suede-yoga-mat",
            "starry-night-print-suede-yoga-mat", "watercolor-floral-suede-yoga-mat",
            "ultra-thin-pu-rubber-travel-mat", "yoga-bag", "pr4", "eva-yoga-block",
            "yoga-block-cover",
        ],
        "guide_en": "Hospitality buyers care about three things our specs answer directly: "
                    "material odour (TPE and natural rubber are closed-cell and low-VOC, so a "
                    "mat does not scent a wardrobe), cleaning (closed-cell surfaces can be "
                    "wiped with a standard hotel sanitiser) and rolling diameter (a 6 mm mat "
                    "rolls to roughly 16 cm, which fits standard wardrobe shelving). Tell us "
                    "your room count and whether the kit is per-room or per wellness floor, and "
                    "we will quote both a full-house rollout and a 10% housekeeping float.",
        "guide_zh": "酒店采购最在意的三点，我们的规格都能直接回答：材质气味（TPE 与天然橡胶是闭孔"
                    "低挥发材质，垫子不会给衣柜留味）、清洁（闭孔表面可用酒店常规消毒剂擦拭）、"
                    "卷径（6 mm 垫卷起约 16 cm，能放进标准衣柜层板）。告诉我们房间数、以及"
                    "套装是按房配还是按康体楼层配，我们会同时报「全店铺开」与「10% 客房部周转备品」"
                    "两套价格。",
        "faq": [
            ("Will the mats smell in a closed wardrobe?",
             "垫子放在密闭衣柜里会有味道吗？",
             "Our TPE and natural-rubber mats are closed-cell and low-VOC — no plasticiser smell, "
             "which is why hospitality buyers specify them over PVC. PVC mats are available for "
             "budget projects but we will tell you when they are the wrong choice.",
             "我们的 TPE 与天然橡胶垫为闭孔低挥发材质，没有增塑剂气味 —— 这正是酒店客户指定它们"
             "而不是 PVC 的原因。预算型项目也可以做 PVC，但如果是错的选择我们会直接说明。"),
            ("Can you emboss our hotel crest on the mat?",
             "能在垫子上压印酒店店徽吗？",
             "Yes — embossing, laser engraving or full-colour printing. Logo files are kept on "
             "record, so a reorder in two years produces an identical mat. Tooling for embossing "
             "is usually free above 300 pcs.",
             "可以 —— 压印、激光雕刻或全彩印花都行。Logo 文件我们会归档，两年后补货做出来的垫子"
             "完全一致。压印模具在 300 片以上通常免费。"),
            ("Do you ship to hotel projects on a staged schedule?",
             "酒店项目能分批交货吗？",
             "Yes. Many projects ship in two or three stages to match the opening schedule — "
             "we hold produced stock and release it against your dates, and we handle export "
             "documents for FOB, CIF or DDP terms.",
             "可以。很多项目按开业节点分两到三批交货 —— 我们备好库存，按你的日期放货，"
             "并按 FOB、CIF 或 DDP 条款办理出口单证。"),
        ],
    },

    # =============================================================== 4 零售 / 贴牌
    {
        "key": "retail-private-label",
        "en": "Retail & Private Label",
        "zh": "零售与贴牌",
        "icon": ICON_RETAIL,
        "tag_en": "141 SKUs under your own brand",
        "tag_zh": "141 款全部贴你的牌",
        "card_en": "The whole catalogue with OEM/ODM — your colour, your logo, your packaging, "
                   "one factory and one PO per season.",
        "card_zh": "全系列 OEM/ODM —— 你的颜色、你的 Logo、你的包装，一家工厂、一季一张订单。",
        "kit_en": "Full range · custom logo · colour system · packaging & barcodes",
        "kit_zh": "全系列 · 定制 Logo · 配色体系 · 包装与条码",
        "title_seo": "Yoga &amp; Fitness Private Label Manufacturer | OEM / ODM — SANFAN",
        "desc_seo": "Private-label yoga mats, foam rollers, resistance bands, jump ropes and "
                    "fitness equipment from a single factory. 141 OEM/ODM SKUs, custom colour, "
                    "logo, retail packaging and barcodes. MOQ 100 pcs, 7-day sampling.",
        "hero_en": "One factory for the whole shelf. Mats, rollers, bands, ropes, props and "
                   "fitness equipment — all built with your colour, your logo and retail-ready "
                   "packaging, so what lands in the warehouse can go straight onto a shelf or "
                   "into an FBA carton. 141 SKUs, one quality standard, one PO per season.",
        "hero_zh": "一层货架，一家工厂供齐。垫类、泡沫轴、弹力带、跳绳、辅具与健身器械 —— "
                   "全部按你的颜色、你的 Logo 与零售级包装生产，进仓即可上架或直接装 FBA 箱。"
                   "141 款 SKU、一套品质标准、一季一张订单。",
        "kit": [
            ("Hero / traffic SKUs", "主推与引流款",
             "The 2–4 items you advertise — must be flawless and always in stock",
             "你用来投流的那 2–4 款 —— 必须零瑕疵、不断货",
             "TPE mats, cork mats, wolf-tooth rollers — our highest-volume lines",
             "TPE 垫、软木垫、狼牙泡沫轴 —— 我们走量最大的几条线"),
            ("Category fillers", "品类补齐款",
             "One or two per category so the shelf looks complete without dead stock",
             "每类补 1–2 款，让货架看起来完整，同时不压死库存",
             "PU-rubber, suede, meditation, props, bands, ropes, recovery",
             "PU 橡胶、麂皮、冥想垫、辅具、弹力带、跳绳、恢复类"),
            ("Colour system", "配色体系",
             "The single cheapest way to make 20 SKUs look like one brand",
             "让 20 个 SKU 看起来像一个品牌，成本最低的一招",
             "Pick 2–3 Pantone colours; we apply them across every material and keep the recipe",
             "选 2–3 个 Pantone 色；我们贯穿所有材质并归档配方"),
            ("Logo application", "Logo 工艺",
             "Surface matters more than method — we pick the technique per material",
             "材质决定工艺，比工艺本身更重要 —— 我们按材质选",
             "Emboss, laser-engrave, screen print, heat transfer, woven label, printed sleeve",
             "压印、激光雕刻、丝印、热转印、织标、印字束带"),
            ("Retail packaging", "零售包装",
             "Box, belly band, hang tag, barcode, QR — arrives shelf-ready",
             "彩盒、腰封、吊牌、条码、二维码 —— 到货即可上架",
             "Custom colour box, kraft sleeve, polybag with warning text, FBA-ready cartons",
             "定制彩盒、牛皮纸套、带警示文字的胶袋、可直接入 FBA 的外箱"),
            ("Compliance pack", "合规资料",
             "The paperwork your marketplace or importer will ask for",
             "平台与进口商会问你要的那套文件",
             "ISO 9001, BSCI, SGS, ROHS / CE / REACH test reports; material declarations",
             "ISO 9001、BSCI、SGS、ROHS / CE / REACH 检测报告；材质声明"),
        ],
        "products": [
            "ym1", "ym2", "eco-friendly-tpe-yoga-mat", "ym5", "ym6", "ym7",
            "aurora-gradient-suede-yoga-mat", "cork-rubber-yoga-mat", "round-mandala-meditation-mat",
            "fr1", "fr2", "vibrating-foam-roller", "rb1", "tpe-resistance-loop-band", "power-band",
            "pr1", "pr4", "yoga-bag", "fi3", "speed-jump-rope", "weighted-training-ring",
            "yoga-ball", "fascia-gun", "pilates-ring-2",
        ],
        "guide_en": "Private label is mostly a sequencing problem. Start with two hero SKUs that "
                    "prove the colour and the logo technique, add fillers in the second order, then "
                    "consolidate packaging so one carton size serves several SKUs — that alone "
                    "typically cuts freight 8–12%. We keep your colour recipe, logo files and "
                    "packaging artwork on record, so every season's order is a repeat, not a "
                    "re-setup. Ask for the compliance pack on the first order; importers always "
                    "want it eventually.",
        "guide_zh": "贴牌本质上是排序问题。先用 2 个主推款验证颜色与 Logo 工艺，第二单再补品类款，"
                    "然后合并包装规格让一个箱型覆盖多个 SKU —— 仅这一项通常就能降 8–12% 运费。"
                    "我们会归档你的色号配方、Logo 文件与包装稿件，所以每一季都是「复单」而不是"
                    "「重新开一次」。第一单就要合规资料包，进口商迟早会要。",
        "faq": [
            ("What is the minimum order for a private-label run?",
             "贴牌起订量是多少？",
             "100 pcs per SKU, mixable across the range so you can test a whole shelf cheaply. "
             "Sampling is 7 days with your logo and colour. There is no separate artwork or "
             "tooling fee on standard logo techniques.",
             "单款 100 片起订，可跨品类混订，方便低成本试整层货架。打样 7 天，可带你的 Logo 与颜色。"
             "常规 Logo 工艺不收单独的稿件费或开模费。"),
            ("Can you develop an entirely new product from our idea?",
             "能按我们的想法开发全新产品吗？",
             "Yes — that is the ODM half. Send a sketch, a competitor sample or just a target "
             "price and use case; our R&D team comes back with materials, tooling cost and a "
             "physical sample, usually within 7 days.",
             "可以，这正是 ODM 的部分。发草图、竞品样品，或只给目标价与使用场景都行；"
             "研发团队会给出材质方案、开模成本与实物样品，通常 7 天内。"),
            ("Will you send the test reports our marketplace requires?",
             "能提供平台要求的检测报告吗？",
             "Yes. We hold ISO 9001 and BSCI audits plus SGS testing, and can arrange "
             "ROHS / CE / REACH reports for your specific materials and colours — including "
             "whatever additional testing Amazon or your importer asks for.",
             "可以。我们有 ISO 9001 与 BSCI 审核，以及 SGS 检测，并能针对你的具体材质与颜色"
             "出 ROHS / CE / REACH 报告 —— 包括亚马逊或进口商额外要求的项目。"),
        ],
    },

    # =============================================================== 5 恢复理疗
    {
        "key": "recovery-physio",
        "en": "Recovery & Physio",
        "zh": "恢复与理疗",
        "icon": ICON_RECOVERY,
        "tag_en": "Clinics, physio rooms, post-training corners",
        "tag_zh": "诊所、理疗室、训练后放松区",
        "card_en": "Rollers, fascia guns, balls and sticks — density, texture and colour "
                   "specified per order for clinics and recovery studios.",
        "card_zh": "泡沫轴、筋膜枪、筋膜球与按摩棒 —— 密度、纹理与颜色按单指定，面向诊所与恢复工作室。",
        "kit_en": "Rollers · fascia guns · balls · sticks · mobility tools",
        "kit_zh": "泡沫轴 · 筋膜枪 · 筋膜球 · 按摩棒 · 活动度工具",
        "title_seo": "Foam Roller &amp; Massage Tool Manufacturer | OEM / ODM — SANFAN",
        "desc_seo": "Factory-direct foam rollers, fascia guns, massage balls and sticks for "
                    "clinics, physio rooms and gyms. EVA and EPP, solid, hollow and vibrating "
                    "builds, custom density and texture. MOQ 100 pcs, 7-day sampling.",
        "hero_en": "Recovery is a spec-driven category: a physio room wants a firm EPP roller "
                   "that does not compress, a studio wants a soft EVA surface that a member can "
                   "lie on, and a clinic wants a gun with controlled amplitude. We build all of "
                   "it and set density, length, texture and colour per order — not per catalogue.",
        "hero_zh": "恢复类是个「看参数」的品类：理疗室要的是不塌陷的硬质 EPP 轴，工作室要会员能躺上去"
                   "的软 EVA 面，诊所要振幅可控的筋膜枪。我们都做，并且密度、长度、纹理与颜色"
                   "都是按单指定，而不是按目录固定。",
        "kit": [
            ("Large-surface release", "大面积放松",
             "Quads, back and IT band work — the roller that gets used every session",
             "股四头肌、背部与髂胫束 —— 每次训练都要用的那根",
             "EVA or EPP, 33 / 45 / 60 cm, 90–150 mm diameter; smooth, wave or wolf-tooth surface",
             "EVA 或 EPP，33 / 45 / 60 cm，直径 90–150 mm；光面 / 波浪 / 狼牙"),
            ("Deep-tissue / dense", "深层与高密度",
             "Athletes and clinics who need a roller that will not compress under load",
             "运动员与诊所 —— 需要承重不塌陷的轴",
             "High-density EPP, solid or hollow; harder durometer, tighter texture",
             "高密度 EPP，实心或空心；硬度更高、纹理更密"),
            ("Vibrating / powered", "震动与电动",
             "Rehab protocols and premium retail — a visible step up on the shelf",
             "康复流程与高端零售 —— 货架上明显高一档",
             "Vibrating rollers with rechargeable battery; electric rollers with adjustable speed",
             "充电式震动泡沫轴；电动款可调转速"),
            ("Percussion guns", "筋膜枪",
             "Fast, targeted release between sessions and after treatment",
             "训练间隔与治疗后的快速点压",
             "Four build styles — compact, T-shape, ring-grip and professional; multiple heads",
             "四种结构 —— 便携、T 型、环形握把与专业款；多档按摩头"),
            ("Point release", "精准点压",
             "Trigger points, feet, forearms and small muscle groups",
             "激痛点、足底、前臂与小肌群",
             "Textured and smooth fascia balls, 6-colour sets, massage sticks 32 / 34 cm",
             "浮点与光面筋膜球、6 色套装、32 / 34 cm 按摩棒"),
            ("Mobility & assist", "活动度与辅助",
             "Stretch and mobility work that complements the treatment room",
             "与理疗室互补的拉伸与活动度训练",
             "Stretch boards, beaded and spiral massage rollers, dual-head sticks",
             "拉伸板、串珠与螺旋按摩棒、双头按摩棒"),
        ],
        "products": [
            "fr1", "fr2", "fr3", "fr4", "vibrating-foam-roller", "advanced-yoga-roller",
            "eva-foam-roller", "eva-foam-roller-2", "foam-roller", "fascia-gun", "fascia-gun-1",
            "fascia-gun-2", "fascia-gun-3", "fascial-sphere-1", "fascial-sphere-2",
            "fascial-sphere-3", "fr5", "massage-stick", "massage-stick-2", "massager-1",
            "massager-2", "massager-3", "circular-leg-clamps", "stretch-board", "yoga-ball",
        ],
        "guide_en": "Buyers in this category should specify three numbers before anything else: "
                    "density (durometer), diameter and surface pattern. Density decides whether "
                    "the roller holds up under a 90 kg athlete; diameter decides how much of the "
                    "muscle group it covers per stroke; pattern decides whether it is a general "
                    "release tool or a trigger-point tool. Ask us for a density and pattern sample "
                    "set — we send EVA and EPP in the same size so your clinicians can compare "
                    "before you commit to a container.",
        "guide_zh": "这个品类的采购方在下单前应先定三个数字：密度（硬度）、直径与表面纹理。"
                    "密度决定这根轴能不能承受 90 kg 的运动员；直径决定单次滚压能覆盖多大肌群；"
                    "纹理决定它是通用放松工具还是激痛点工具。可以找我们要密度与纹理的样品组 —— "
                    "同尺寸的 EVA 与 EPP 各一根，让你这边的治疗师比较过再决定整柜。",
        "faq": [
            ("What is the difference between EVA and EPP rollers?",
             "EVA 与 EPP 泡沫轴有什么区别？",
             "EVA is softer and lighter — comfortable for general self-release and studio use. "
             "EPP is denser and springs back, so it does not compress under heavy athletes and "
             "is the usual clinic choice. We make both, in the same sizes, so you can compare "
             "like for like.",
             "EVA 更软更轻，适合日常自主放松与工作室使用。EPP 密度更高、回弹性好，"
             "在大体重运动员身下不塌陷，是诊所的常规选择。两种我们都做，尺寸一致，可直接对比。"),
            ("Can we order custom textures and densities?",
             "能定制纹理与密度吗？",
             "Yes — surface pattern, durometer, length, diameter and colour are all set per "
             "order. Tooling for a new texture is quoted once and then lives with your SKU, so "
             "reorders carry no tooling cost.",
             "可以 —— 表面纹理、硬度、长度、直径与颜色全部按单指定。新纹理的开模费只报一次，"
             "之后归属你的 SKU，补货不再收开模费。"),
            ("Are the fascia guns suitable for professional clinic use?",
             "筋膜枪适合专业诊所使用吗？",
             "The professional build has adjustable amplitude and speed with interchangeable "
             "heads, and is CE / ROHS compliant. We supply both the clinic version and the "
             "consumer retail version — tell us which channel you sell into and we will spec "
             "the right one.",
             "专业款可调振幅与转速，配可更换按摩头，符合 CE / ROHS。诊所版与消费零售版我们都供，"
             "说明你的销售渠道，我们会推荐合适的那一款。"),
        ],
    },

    # =============================================================== 6 家庭 / 电商卖家
    {
        "key": "home-online-sellers",
        "en": "Home & Online Sellers",
        "zh": "家庭用户与电商卖家",
        "icon": ICON_HOME,
        "tag_en": "Light SKUs, low MOQ, retail-ready",
        "tag_zh": "轻量 SKU、低起订、到货即上架",
        "card_en": "Light, high-turn SKUs that ship cheaply — ropes, bands, balls, blocks and "
                   "travel mats, built for marketplace and DTC sellers.",
        "card_zh": "轻量高周转、运费友好的 SKU —— 跳绳、弹力带、筋膜球、瑜伽砖与旅行垫，"
                   "为平台与独立站卖家准备。",
        "kit_en": "Ropes · bands · balls · blocks · travel mats · bundles",
        "kit_zh": "跳绳 · 弹力带 · 筋膜球 · 瑜伽砖 · 旅行垫 · 组合装",
        "title_seo": "Amazon &amp; E-commerce Yoga Fitness Supplier | Low MOQ — SANFAN",
        "desc_seo": "Light, high-turn yoga and fitness SKUs for Amazon, Shopify and TikTok Shop "
                    "sellers: jump ropes, resistance bands, fascia balls, yoga blocks and travel "
                    "mats. MOQ 100 pcs, FBA-ready packaging and barcodes, 7-day sampling.",
        "hero_en": "Built for sellers, not for showrooms: light cartons, low MOQ, small-batch "
                   "colours and packaging that arrives with barcodes and warning text already on "
                   "it. Ropes, bands, balls, blocks and travel mats are the SKUs where a light "
                   "unit weight turns directly into margin on every shipped order.",
        "hero_zh": "为卖家做，不为展厅做：轻箱型、低起订、小批量配色，到货即带条码与警示文字。"
                   "跳绳、弹力带、筋膜球、瑜伽砖与旅行垫属于「单件重量轻」的品类 —— "
                   "重量直接等于每一单省下来的运费与留下的利润。",
        "kit": [
            ("Traffic SKUs", "引流款",
             "Cheap to ship, easy to explain, high search volume — where the ad budget goes",
             "运费低、易讲清、搜索量大 —— 投流预算该放的地方",
             "Speed and counting jump ropes, resistance loops and tubes, figure-8 bands",
             "速度与计数跳绳、环形与拉力管弹力带、8 字带"),
            ("Bundle / set SKUs", "组合装",
             "Higher AOV without a new product — bundle what you already sell",
             "不用开新品就能抬客单价 —— 把手上的款捆起来",
             "5-level resistance band sets, 6-colour fascia ball sets, mat + strap bundles",
             "5 级阻力带套装、6 色筋膜球套装、垫 + 伸展带组合"),
            ("Light big-ticket", "轻量高单价",
             "AOV lifters that still ship cheaply per unit",
             "能提客单价、但单件运费仍然低",
             "1.5 mm travel mats, alignment-line TPE mats, ab rollers, stretch boards",
             "1.5 mm 旅行垫、带体位线 TPE 垫、健腹轮、拉伸板"),
            ("Packaging & compliance", "包装与合规",
             "The part that decides whether your listing survives, not just converts",
             "决定你的 listing 能不能活下来，而不只是能不能转化",
             "Polybag warning text, hang tag, barcode / FNSKU labels, FBA carton specs, "
             "ROHS / REACH reports",
             "胶袋警示文字、吊牌、条码 / FNSKU 标签、FBA 外箱规格、ROHS / REACH 报告"),
            ("Small-batch colour", "小批量配色",
             "Test a colour with 100 pcs instead of a container",
             "用 100 片试一个颜色，而不是压一个柜",
             "Any SKU in the range, 100 pcs per colour per order",
             "全系列任意款，每单每色 100 片起"),
        ],
        "products": [
            "speed-jump-rope", "smart-counting-jump-rope", "cordless-jump-rope",
            "electronic-counting-jump-rope", "kids-jump-rope", "two-tone-kids-jump-rope",
            "tpe-resistance-loop-band", "resistance-band", "resistance-band-2",
            "figure-8-resistance-bands", "foot-pedal-resistance-band", "exercise-bands",
            "resistance-tube", "fascial-sphere-3", "massage-stick", "fr5",
            "pr4", "eva-yoga-block", "yoga-block-cover", "yoga-bag",
            "ultra-thin-pu-rubber-travel-mat", "alignment-line-tpe-yoga-mat",
            "ab-roller-with-resistance-band", "stretch-board", "multi-color-tpe-yoga-mat-bundle",
            "yoga-ring",
        ],
        "guide_en": "For marketplace sellers the winning order is small and often: 100–300 pcs "
                    "per SKU, three or four SKUs per shipment, replenished as listings prove out. "
                    "Unit weight is the number to optimise — a jump rope or a band set ships at "
                    "under 300 g, which is where the marketplace fee maths works. Order the "
                    "compliance pack with the first shipment: polybag warning text, FNSKU labels "
                    "and the ROHS / REACH report, so nothing has to be re-labelled in a "
                    "three-week warehouse window.",
        "guide_zh": "对平台卖家来说，最优的订单是「小批量、高频率」：单款 100–300 片，每批三四个 SKU，"
                    "哪个 listing 跑出来就补哪个。要优化的核心数字是单件重量 —— 跳绳或弹力带套装"
                    "单件不到 300 g，平台费用的账才算得过来。第一批发货就要一起订合规包："
                    "胶袋警示文字、FNSKU 标签与 ROHS / REACH 报告，免得在只有三周的入仓窗口里"
                    "还要重新贴标。",
        "faq": [
            ("What is the real MOQ if we want to test several colours?",
             "想试几个颜色的话，真实起订量是多少？",
             "100 pcs per SKU per colour. You can split one order across several colours and "
             "several SKUs as long as you reach a shipable weight — most sellers start with "
             "3–5 SKUs at 100–200 pcs each.",
             "单款单色 100 片起订。一个订单可以在多个颜色与多个 SKU 之间拆分，只要凑够可发运重量 —— "
             "多数卖家首批做 3–5 款、每款 100–200 片。"),
            ("Do you supply FBA-ready packaging and labels?",
             "你们提供可直接入 FBA 的包装与标签吗？",
             "Yes. We produce polybags with the required warning text, apply barcodes and FNSKU "
             "labels, and pack to Amazon carton specs. Tell us the marketplace and we will match "
             "the current requirement rather than a two-year-old spec sheet.",
             "提供。我们做带规定警示文字的胶袋、贴条码与 FNSKU 标签，并按亚马逊外箱规格装箱。"
             "告诉我们具体站点，我们按当前要求执行，而不是照两年前的旧规格。"),
            ("How fast can you ship a first small order?",
             "首批小单多久能发货？",
             "Sampling 7 days; a 100–300 pcs per SKU order is typically produced in 10–15 days "
             "and we ship by air or express if you need to catch a launch. Export documents and "
             "courier booking are handled on our side.",
             "打样 7 天；单款 100–300 片的订单通常 10–15 天完成生产，赶上线可以走空运或快递。"
             "出口单证与快递订舱由我们这边处理。"),
        ],
    },
]

APP_BY_KEY = {a["key"]: a for a in APPS}


if __name__ == "__main__":
    for a in APPS:
        print("%-24s %2d products  %d kit rows  %d faq"
              % (a["key"], len(a["products"]), len(a["kit"]), len(a["faq"])))
