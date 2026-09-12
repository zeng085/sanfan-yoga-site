# -*- coding: utf-8 -*-
"""生成材质对比页 materials.html（EN + 中文同页）。

为什么值得单独做一页：材质是这个品类里买家最纠结、也最爱在搜索引擎/AI 里问的一层
（"TPE 和 PU 哪个好""热瑜伽垫选什么材质"）。把对比结论写成**静态表格**而不是图片或
JS 渲染，Google 与 AI 爬虫都读得到，属于低成本高回报的 GEO 资产。

用法
    python3 i18n_build/build_materials_page.py --dry-run
    python3 i18n_build/build_materials_page.py
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from site_templates import (SITE, VER, bi, cat_nav, cta, footer, head, nav,  # noqa: E402
                            trust_strip)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PF = ""
CANON = SITE + "/materials.html"

TITLE = "Yoga Mat Materials Compared — TPE vs PVC vs PU vs Cork | SANFAN"
DESC = ("Compare yoga mat materials side by side: TPE, PVC, NBR, PU + natural rubber, suede, "
        "cork, EVA and EPP — grip, durability, recyclability, thickness range, printability "
        "and price band. Factory-direct guidance from SANFAN, MOQ 100 pcs.")

# ---------------------------------------------------------------- 快速选材
# (角标, 标题en, 标题zh, 说明en, 说明zh, 跳转到哪个分类)
PICKS = [
    ("Budget &amp; volume", "预算与走量",
     "PVC or single-layer TPE", "PVC 或单层 TPE",
     "Lowest unit cost. Works for entry-level retail and promotional SKUs.",
     "单件成本最低，适合入门零售价带与促销款。",
     "tpe-yoga-mats"),
    ("Eco positioning", "环保定位",
     "Double-layer TPE", "双层 TPE",
     "Closed-cell, odour-free and recyclable — the default for most brands.",
     "闭孔、无异味、可回收 —— 多数品牌的默认选择。",
     "tpe-yoga-mats"),
    ("Hot yoga", "高温瑜伽",
     "PU top on a natural rubber base", "PU 面层 + 天然橡胶底",
     "The only surface that grips properly once you sweat.",
     "出汗后仍然真正防滑的唯一一类面层。",
     "pu-rubber-yoga-mats"),
    ("Brand &amp; design", "品牌与设计",
     "Suede or cork", "麂皮或软木",
     "Takes HD prints and reads as a designed product, not a commodity mat.",
     "可做高清印花，看起来是「设计过的产品」而不是通货垫。",
     "suede-cork-yoga-mats"),
]

# ---------------------------------------------------------------- 对比表
# 列：材质 | 干湿防滑 | 耐用 | 可回收 | 常见厚度 | 印花定制 | 最适合 | 价格带 | 我们的做法
COLS = [
    ("Material", "材质"),
    ("Grip — dry / wet", "防滑 — 干手 / 湿手"),
    ("Durability", "耐用性"),
    ("Recyclable", "可回收"),
    ("Common thickness", "常见厚度"),
    ("Print & custom", "印花与定制"),
    ("Best for", "最适合"),
    ("Price band", "价格带"),
    ("How we build it", "我们的做法"),
]

ROWS = [
    {
        "n_en": "TPE", "n_zh": "TPE（环保热塑弹性体）",
        "grip_en": "Good / fair", "grip_zh": "干手好 / 湿手一般",
        "dur_en": "2–3 years daily studio use", "dur_zh": "瑜伽馆日常使用 2–3 年",
        "rec_en": '<span class="yes">Yes</span>', "rec_zh": '<span class="yes">可回收</span>',
        "th_en": "4–12 mm; 6 mm standard", "th_zh": "4–12 mm；常规 6 mm",
        "pr_en": "Emboss, print, dual-colour", "pr_zh": "压印、印花、双色",
        "best_en": "General practice, eco-positioned brands, hotel and studio volume",
        "best_zh": "常规练习、环保定位品牌、酒店与瑜伽馆的走量款",
        "band": 2,
        "how_en": "Single or double layer, widths 61–90 cm, closed-cell and odour-free. "
                  "Our highest-volume line — 5 lines dedicated to it.",
        "how_zh": "单层或双层，宽度 61–90 cm，闭孔无异味。我们产能最大的产品线，专设 5 条产线。",
    },
    {
        "n_en": "PVC", "n_zh": "PVC",
        "grip_en": "Good / fair", "grip_zh": "干手好 / 湿手一般",
        "dur_en": "3–4 years — very abrasion-resistant", "dur_zh": "3–4 年，耐磨性最好",
        "rec_en": '<span class="no">No</span>', "rec_zh": '<span class="no">不可回收</span>',
        "th_en": "4–8 mm", "th_zh": "4–8 mm",
        "pr_en": "Emboss, print, dual-colour", "pr_zh": "压印、印花、双色",
        "best_en": "Entry-level retail, promotional SKUs, floor mats where cost leads",
        "best_zh": "入门零售、促销款、以成本为先的地垫",
        "band": 1,
        "how_en": "Available on request, but we quote TPE first for most projects — PVC "
                  "carries plasticiser odour and cannot be recycled, which increasingly "
                  "fails retail and hospitality procurement.",
        "how_zh": "可以按需生产，但多数项目我们会优先报 TPE —— PVC 有增塑剂气味且不可回收，"
                  "在零售与酒店采购里越来越难过关。",
    },
    {
        "n_en": "NBR", "n_zh": "NBR（丁腈橡胶发泡）",
        "grip_en": "Fair / fair", "grip_zh": "一般 / 一般",
        "dur_en": "1–2 years — compresses over time", "dur_zh": "1–2 年，长期会塌陷",
        "rec_en": '<span class="no">No</span>', "rec_zh": '<span class="no">不可回收</span>',
        "th_en": "8–15 mm (thick cushioning)", "th_zh": "8–15 mm（厚垫）",
        "pr_en": "Limited — emboss only", "pr_zh": "受限，基本只能压印",
        "best_en": "Thick comfort mats, rehab and floor-exercise use, kids",
        "best_zh": "厚垫舒适款、康复与垫上体操、儿童",
        "band": 1,
        "how_en": "Softer and thicker than TPE — the right answer when cushioning matters more "
                  "than grip. Not a hot-yoga product.",
        "how_zh": "比 TPE 更软更厚 —— 当「缓冲」比「防滑」更重要时才是正确答案。"
                  "不适合高温瑜伽。",
    },
    {
        "n_en": "PU + natural rubber", "n_zh": "PU + 天然橡胶",
        "grip_en": '<span class="yes">Excellent / excellent</span>',
        "grip_zh": '<span class="yes">干手优 / 湿手优</span>',
        "dur_en": "3–5 years — premium tier", "dur_zh": "3–5 年，属高端档",
        "rec_en": "Rubber base only", "rec_zh": "橡胶底可回收",
        "th_en": "1.5–5 mm; 4.5–5 mm standard", "th_zh": "1.5–5 mm；常规 4.5–5 mm",
        "pr_en": "Suede-feel, matte, HD print", "pr_zh": "绒感、磨砂、高清印花",
        "best_en": "Hot yoga, vinyasa and professional studios — the grip benchmark",
        "best_zh": "高温瑜伽、流瑜伽与专业馆 —— 防滑的行业基准",
        "band": 4,
        "how_en": "Natural rubber base bonded to a moisture-absorbing PU top. Heavier and "
                  "pricier than TPE, and worth it the moment sweat is involved.",
        "how_zh": "天然橡胶底贴合吸湿 PU 面层。比 TPE 更重、更贵，但只要课程会出汗就值得。",
    },
    {
        "n_en": "Suede microfibre", "n_zh": "麂皮超细纤维",
        "grip_en": "Fair / excellent (grippier when wet)", "grip_zh": "干手一般 / 湿手优（遇汗更防滑）",
        "dur_en": "2–4 years depending on base", "dur_zh": "视底层而定，2–4 年",
        "rec_en": "Depends on base", "rec_zh": "取决于底层材质",
        "th_en": "1.5–6 mm", "th_zh": "1.5–6 mm",
        "pr_en": '<span class="yes">Full-surface HD print</span>',
        "pr_zh": '<span class="yes">整面高清印花</span>',
        "best_en": "Branded and design-led collections, gift and spa retail",
        "best_zh": "品牌联名与设计驱动系列、礼品与 SPA 零售",
        "band": 3,
        "how_en": "Printed to your artwork across the whole surface — this is the material that "
                  "makes a collection look like a collection.",
        "how_zh": "可整面按你的图稿印花 —— 想让一个系列看起来像一个系列，靠的就是这个材质。",
    },
    {
        "n_en": "Cork", "n_zh": "软木",
        "grip_en": "Good / excellent when damp", "grip_zh": "干手好 / 微湿时优",
        "dur_en": "3+ years", "dur_zh": "3 年以上",
        "rec_en": '<span class="yes">Yes</span>', "rec_zh": '<span class="yes">可回收</span>',
        "th_en": "3–5 mm on a rubber or TPE base", "th_zh": "3–5 mm，贴合橡胶或 TPE 底",
        "pr_en": "Laser engraving, screen print", "pr_zh": "激光雕刻、丝印",
        "best_en": "Eco-premium positioning, hospitality and spa, wellness retail",
        "best_zh": "环保高端定位、酒店与 SPA、康体零售",
        "band": 4,
        "how_en": "Natural cork sheet laminated to a rubber or TPE base. Warm to the touch, "
                  "naturally antimicrobial — but not the cheapest way to a full studio floor.",
        "how_zh": "天然软木片复合橡胶或 TPE 底。触感温润、天然抑菌 —— 但不适合用来铺满整个教室。",
    },
    {
        "n_en": "EVA", "n_zh": "EVA",
        "grip_en": "n/a — structural", "grip_zh": "不适用 —— 结构材料",
        "dur_en": "3–5 years", "dur_zh": "3–5 年",
        "rec_en": '<span class="yes">Yes</span>', "rec_zh": '<span class="yes">可回收</span>',
        "th_en": "Blocks 3–10 cm; rollers 33–60 cm long", "th_zh": "瑜伽砖 3–10 cm；泡沫轴 33–60 cm",
        "pr_en": "Dual-colour, printed logo", "pr_zh": "双色、印标",
        "best_en": "Blocks, soft rollers, props — the accessory half of the order",
        "best_zh": "瑜伽砖、软质泡沫轴、辅具 —— 订单里的配件那一半",
        "band": 2,
        "how_en": "High-density EVA blocks and softer EVA rollers, colour-matched to the mats "
                  "so the whole order looks like one product line.",
        "how_zh": "高密度 EVA 瑜伽砖与较软的 EVA 泡沫轴，与垫子同色系，"
                  "让整张订单看起来像一条产品线。",
    },
    {
        "n_en": "EPP", "n_zh": "EPP",
        "grip_en": "n/a — structural", "grip_zh": "不适用 —— 结构材料",
        "dur_en": "5+ years — does not compress", "dur_zh": "5 年以上，不塌陷",
        "rec_en": '<span class="yes">Yes</span>', "rec_zh": '<span class="yes">可回收</span>',
        "th_en": "Rollers 33–90 cm, 90–150 mm Ø", "th_zh": "泡沫轴 33–90 cm、直径 90–150 mm",
        "pr_en": "Colour, texture tooling", "pr_zh": "颜色、纹理开模",
        "best_en": "Clinic and physio rollers, gym recovery corners, heavy athletes",
        "best_zh": "诊所与理疗轴、健身房恢复角、大体重运动员",
        "band": 3,
        "how_en": "Denser and springier than EVA — holds shape under load, which is why "
                  "clinics specify it. Same sizes as EVA so buyers can compare like for like.",
        "how_zh": "比 EVA 密度更高、回弹更好，承重不塌陷 —— 诊所因此指定用 EPP。"
                  "尺寸与 EVA 一致，方便采购方直接对比。",
    },
]

# ---------------------------------------------------------------- 材质卡
CARDS = [
    {
        "n_en": "TPE — the default", "n_zh": "TPE —— 默认选择",
        "sub_en": "Eco TPE, single or double layer", "sub_zh": "环保 TPE，单层或双层",
        "rows": [
            ("Feel", "触感", "Soft, slightly tacky, warm to the touch — most people's idea of "
                             "what a yoga mat feels like.",
             "柔软、微涩、上手温润 —— 大多数人印象里「瑜伽垫该有的手感」。"),
            ("Grip", "防滑", "Dry grip is excellent. Wet grip is fair: fine for general and "
                             "hatha classes, not ideal for hot yoga.",
             "干手防滑优秀。湿手一般：常规课与哈他课没问题，高温瑜伽不理想。"),
            ("Watch out", "注意", "Density varies a lot between suppliers. A cheap TPE mat "
                                  "flattens within months — ask for the density, not just the "
                                  "material name.",
             "不同供应商的密度差别很大。低价 TPE 垫几个月就塌 —— 要问密度，不能只问材质名。"),
            ("OEM", "定制", "Widths 61 / 66 / 80 / 90 cm, 4–12 mm, single or double layer, "
                            "dual-colour, embossed logo, printed strap and retail box.",
             "宽度 61 / 66 / 80 / 90 cm、4–12 mm、单层或双层、双色、压印 Logo、印花背带与彩盒。"),
        ],
    },
    {
        "n_en": "PU + natural rubber — the grip benchmark", "n_zh": "PU + 天然橡胶 —— 防滑基准",
        "sub_en": "Moisture-absorbing top on a rubber base", "sub_zh": "吸湿 PU 面层 + 橡胶底",
        "rows": [
            ("Feel", "触感", "Matte or suede-feel top, firm and dense — reads as a premium "
                             "product the moment it is unrolled.",
             "磨砂或绒感面层，扎实致密 —— 一展开就有高端感。"),
            ("Grip", "防滑", "Gets grippier as it gets wet. This is the only family that stays "
                             "safe in a 38°C hot-yoga room.",
             "越湿越防滑。这是唯一能在 38°C 高温瑜伽房里保持安全的一类。"),
            ("Watch out", "注意", "Heavier than TPE, so freight per unit is higher, and the "
                                  "rubber base needs to be natural rubber — some suppliers "
                                  "substitute reclaimed rubber and grip suffers.",
             "比 TPE 重，单件运费更高；橡胶底必须是天然橡胶 —— 有些供应商用再生胶替代，"
             "防滑会明显变差。"),
            ("OEM", "定制", "1.5–5 mm, alignment lines, matte or suede finish, HD printing, "
                            "laser-engraved logo, travel-mat builds at 1.5 mm.",
             "1.5–5 mm、体位线、磨砂或绒面、高清印花、激光雕刻 Logo，另有 1.5 mm 旅行款。"),
        ],
    },
    {
        "n_en": "Suede & cork — for brands that sell on looks", "n_zh": "麂皮与软木 —— 卖给「看起来好」的品牌",
        "sub_en": "Print-first surfaces", "sub_zh": "以印花为核心的面层",
        "rows": [
            ("Feel", "触感", "Suede is soft and cloth-like; cork is warm, dry and slightly "
                             "textured. Neither feels like a commodity mat.",
             "麂皮柔软似布；软木温润干爽、带细微纹理。两者都不像通货垫。"),
            ("Grip", "防滑", "Both grip better once slightly damp — the opposite behaviour to "
                             "PVC, and the reason they suit vinyasa and hot classes.",
             "两者都是微湿后更防滑 —— 与 PVC 相反，也是它们适合流瑜伽与高温课的原因。"),
            ("Watch out", "注意", "Suede needs washing before first use to activate grip; "
                                  "cork dislikes being left in direct sun. Tell your customers, "
                                  "or you will get returns.",
             "麂皮首次使用前需清洗以激活防滑；软木不耐长时间日晒。这两点要写进产品说明，"
             "否则会招来退货。"),
            ("OEM", "定制", "Full-surface HD printing on suede; laser engraving and screen "
                            "print on cork. Base can be rubber, TPE or a foldable build.",
             "麂皮可整面高清印花；软木做激光雕刻与丝印。底层可选橡胶、TPE 或可折叠结构。"),
        ],
    },
    {
        "n_en": "PVC & NBR — still the right answer sometimes", "n_zh": "PVC 与 NBR —— 有时仍是正确答案",
        "sub_en": "Cost-led and cushioning-led builds", "sub_zh": "以成本或缓冲为导向的方案",
        "rows": [
            ("Feel", "触感", "PVC is firm and glassy in cheap grades; NBR is thick and spongy "
                             "and sinks under a knee.",
             "低价 PVC 硬而发亮；NBR 厚而绵软，膝盖会陷进去。"),
            ("Grip", "防滑", "Both are dry-grip products. NBR in particular becomes slippery "
                             "when wet — do not sell it into hot yoga.",
             "两者都是干手产品。尤其 NBR 遇水变滑 —— 不要卖进高温瑜伽渠道。"),
            ("Watch out", "注意", "PVC plasticiser odour and non-recyclability now fail "
                                  "procurement at many retailers and most hotels. We will "
                                  "still quote it, but we will say so when it is the wrong call.",
             "PVC 的增塑剂气味与不可回收，已经让它在不少零售商与多数酒店的采购环节过不了。"
             "我们照样可以报价，但如果这是错的选择我们会直说。"),
            ("OEM", "定制", "Both take embossing and dual-colour. NBR is limited to emboss "
                            "only — do not plan a printed design on it.",
             "两者都能压印与双色。NBR 基本只能压印 —— 不要在上面做印花设计。"),
        ],
    },
]

FAQS = [
    ("Which yoga mat material is best?",
     "哪种瑜伽垫材质最好？",
     "There is no single best — it depends on the class. TPE for general practice and eco "
     "positioning, PU + natural rubber for hot yoga and professional studios, suede or cork "
     "for branded and design-led collections, NBR when thick cushioning matters more than grip. "
     "Tell us the class type and the retail price band and we will recommend one.",
     "没有绝对最好的，取决于课程类型。常规练习与环保定位选 TPE；高温瑜伽与专业馆选 PU + 天然橡胶；"
     "品牌联名与设计驱动选麂皮或软木；缓冲比防滑更重要时选 NBR。告诉我们课程类型与零售价带，"
     "我们给出具体建议。"),
    ("Is TPE really more eco-friendly than PVC?",
     "TPE 真的比 PVC 更环保吗？",
     "Yes, verifiably: TPE is closed-cell, free of phthalate plasticisers, and recyclable at "
     "end of life; PVC contains plasticisers, cannot be recycled in practice and is the reason "
     "some retailers refuse mats on sustainability grounds. TPE also has no material odour, "
     "which matters for hotels and for unboxing reviews.",
     "可以验证：TPE 是闭孔结构、不含邻苯类增塑剂、报废后可回收；PVC 含增塑剂、实际上无法回收，"
     "这正是部分零售商以可持续为由拒收的原因。TPE 另外没有材质气味，这对酒店采购与开箱评价都重要。"),
    ("How thick should a yoga mat be?",
     "瑜伽垫该选多厚？",
     "6 mm is the volume standard for general practice. 4–5 mm is the studio and travel "
     "preference (better balance, easier to carry). 8–12 mm is for comfort-led, rehab and "
     "floor-exercise use. Over 12 mm the mat becomes unstable in standing poses, which is why "
     "we do not recommend it for serious practice.",
     "常规练习的走量标准是 6 mm。专业馆与旅行更偏 4–5 mm（平衡更好、易携带）。"
     "8–12 mm 用于舒适导向、康复与垫上体操。超过 12 mm 站立体式会不稳，"
     "所以我们不建议用于正经练习。"),
    ("Can you send samples of several materials to compare?",
     "能寄几种材质的样品让我对比吗？",
     "Yes. Tell us the materials and thicknesses you are considering and we send physical "
     "samples in the same size, with your logo on them, in about 7 days. Buyers usually compare "
     "TPE against PU + rubber and decide in the hand rather than on a spec sheet — which is the "
     "right way to decide.",
     "可以。告诉我们你在考虑的材质与厚度，我们做成同尺寸、带你 Logo 的实物样品，约 7 天寄出。"
     "买家通常是拿 TPE 和 PU + 橡胶上手比，而不是看规格表 —— 这本来就是更靠谱的决策方式。"),
]


def jsonld():
    faq = [{"@type": "Question", "name": q_en,
            "acceptedAnswer": {"@type": "Answer", "text": a_en}}
           for (q_en, _qz, a_en, _az) in FAQS]
    return json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Products",
                 "item": SITE + "/products.html"},
                {"@type": "ListItem", "position": 3, "name": "Materials Compared",
                 "item": CANON},
            ]},
            {"@type": "Article",
             "headline": "Yoga Mat Materials Compared — TPE vs PVC vs PU vs Cork",
             "url": CANON,
             "description": DESC,
             "author": {"@type": "Organization", "name": "FUJIAN SANFAN Sports Products Co., Ltd."},
             "publisher": {"@type": "Organization", "name": "SANFAN",
                           "logo": {"@type": "ImageObject",
                                    "url": SITE + "/assets/img/logo.webp"}}},
            {"@type": "FAQPage", "mainEntity": faq},
        ],
    }, ensure_ascii=False)


def picks_section():
    cards = "".join(
        '        <a class="mp-card" href="%s.html">\n'
        '          <div class="mp-k">%s</div>\n'
        '          <h4>%s</h4>\n'
        '          <p>%s</p>\n'
        '        </a>' % (slug, bi(k_en, k_zh), bi(t_en, t_zh), bi(d_en, d_zh))
        for (k_en, k_zh, t_en, t_zh, d_en, d_zh, slug) in PICKS)
    return ('  <section class="section" id="quick-picks">\n'
            '    <div class="container">\n'
            '      <div class="section-head">\n'
            '        <div class="eyebrow">%s</div>\n'
            '        <h2>%s</h2>\n'
            '        <p>%s</p>\n'
            '      </div>\n'
            '      <div class="mat-hero-picks">\n%s\n      </div>\n'
            '    </div>\n'
            '  </section>\n\n'
            % (bi("Start here", "从这里开始"),
               bi("Four ways this decision usually goes", "这个选择通常的四个答案"),
               bi("Match your buyer and your price band, and the material picks itself. "
                  "Click through to the range that uses it.",
                  "对上你的客户与价格带，材质基本就定了。点击可直达对应的产品线。"),
               cards))


def table_section():
    head_row = "".join('<th scope="col">%s</th>' % bi(en, zh) for en, zh in COLS)
    body = []
    for r in ROWS:
        dots = '<span class="price-dots">%s</span>' % ("●" * r["band"] + "○" * (4 - r["band"]))
        body.append(
            '          <tr>\n'
            '            <th scope="row">%s</th>\n'
            '            <td>%s</td>\n'
            '            <td>%s</td>\n'
            '            <td>%s</td>\n'
            '            <td>%s</td>\n'
            '            <td>%s</td>\n'
            '            <td>%s</td>\n'
            '            <td>%s</td>\n'
            '            <td>%s</td>\n'
            '          </tr>'
            % (bi(r["n_en"], r["n_zh"]), bi(r["grip_en"], r["grip_zh"]),
               bi(r["dur_en"], r["dur_zh"]), bi(r["rec_en"], r["rec_zh"]),
               bi(r["th_en"], r["th_zh"]), bi(r["pr_en"], r["pr_zh"]),
               bi(r["best_en"], r["best_zh"]), dots,
               bi(r["how_en"], r["how_zh"])))
    return ('  <section class="section soft" id="compare">\n'
            '    <div class="container">\n'
            '      <div class="section-head">\n'
            '        <div class="eyebrow">%s</div>\n'
            '        <h2>%s</h2>\n'
            '        <p>%s</p>\n'
            '      </div>\n'
            '      <div class="mat-wrap">\n'
            '        <table class="mat-table">\n'
            '          <thead><tr>%s</tr></thead>\n'
            '          <tbody>\n%s\n          </tbody>\n'
            '        </table>\n'
            '      </div>\n'
            '      <p style="font-size:12.5px;color:var(--muted);margin:12px 2px 0;">%s</p>\n'
            '    </div>\n'
            '  </section>\n\n'
            % (bi("Side by side", "横向对比"),
               bi("Every material we make, on the same nine points",
                  "我们常做的八种材质，同样九个维度"),
               bi("Price band is relative to our factory-gate cost within this range, not a "
                  "retail price.",
                  "价格带是与本系列内的出厂价相对比较，不是零售价。"),
               head_row, "\n".join(body),
               bi("Price band: ●○ least expensive → ●●●● most expensive. "
                  "Grip and durability are for normal commercial use, not lab conditions.",
                  "价格带：●○ 最经济 → ●●●● 最高。防滑与耐用性按常规商用条件评估，非实验室数据。")))


def cards_section():
    out = []
    for c in CARDS:
        rows = "".join('<dt>%s</dt><dd>%s</dd>' % (bi(k_en, k_zh), bi(v_en, v_zh))
                       for (k_en, k_zh, v_en, v_zh) in c["rows"])
        out.append(
            '        <div class="mat-card">\n'
            '          <h3>%s</h3>\n'
            '          <div class="mc-sub">%s</div>\n'
            '          <dl>%s</dl>\n'
            '        </div>' % (bi(c["n_en"], c["n_zh"]), bi(c["sub_en"], c["sub_zh"]), rows))
    return ('  <section class="section" id="detail">\n'
            '    <div class="container">\n'
            '      <div class="section-head">\n'
            '        <div class="eyebrow">%s</div>\n'
            '        <h2>%s</h2>\n'
            '        <p>%s</p>\n'
            '      </div>\n'
            '      <div class="mat-cards">\n%s\n      </div>\n'
            '    </div>\n'
            '  </section>\n\n'
            % (bi("Material by material", "逐种材质"),
               bi("What each material is actually like in the hand",
                  "每种材质上手到底是什么样"),
               bi("Written from what our own production lines see, including the failure modes "
                  "— because the failure modes are what decide your return rate.",
                  "写的是我们自己产线上看到的情况，包括踩坑点 —— 因为踩坑点决定你的退货率。"),
               "\n".join(out)))


def cert_section():
    return ('  <section class="section soft" id="certifications">\n'
            '    <div class="container">\n'
            '      <div class="guide-wrap">\n'
            '        <div class="gw-head">\n'
            '          <div class="eyebrow">%s</div>\n'
            '          <h2>%s</h2>\n'
            '        </div>\n'
            '        <div class="gw-body"><p>%s</p></div>\n'
            '      </div>\n'
            '    </div>\n'
            '  </section>\n\n'
            % (bi("Certifications & testing", "认证与检测"),
               bi("What the paperwork covers", "这套资料覆盖什么"),
               bi("Materials are tested to ROHS, CE and REACH, and our plants hold ISO 9001 and "
                  "BSCI audits with SGS third-party testing. Test reports are issued per material "
                  "and colour, and we will tell you which tests your specific market and "
                  "marketplace require rather than sending a generic pack.",
                  "材质通过 ROHS、CE 与 REACH 检测；工厂持有 ISO 9001 与 BSCI 审核，并有 SGS 第三方检测。"
                  "检测报告按材质与颜色出具。我们会告诉你你的目标市场与平台具体需要哪些测试，"
                  "而不是发一份通用资料包了事。")))


def faq_section():
    items = "".join(
        '        <details class="faq-item">\n'
        '          <summary>%s</summary>\n'
        '          <div class="faq-a">%s</div>\n'
        '        </details>\n' % (bi(qe, qz), bi(ae, az))
        for (qe, qz, ae, az) in FAQS)
    return ('  <section class="section">\n'
            '    <div class="container">\n'
            '      <div class="section-head">\n'
            '        <div class="eyebrow">%s</div>\n'
            '        <h2>%s</h2>\n'
            '      </div>\n'
            '      <div class="faq-list">\n%s      </div>\n'
            '    </div>\n'
            '  </section>\n\n'
            % (bi("FAQ", "常见问题"),
               bi("Material questions buyers actually ask",
                  "买家真正会问的材质问题"),
               items))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    body = [head(title=TITLE, desc=DESC, canonical=CANON,
                 og_img=SITE + "/assets/img/tpe-mat-2.webp",
                 jsonld=jsonld(), prefix=PF)]
    body.append(nav(PF))
    body.append(
        '  <section class="hero" style="background:linear-gradient(120deg,var(--brand-ink),var(--brand));">\n'
        '    <div class="container hero-inner" style="padding:52px 0 40px;">\n'
        '      <div class="breadcrumb"><a href="/">Home</a> / <a href="products.html">Products</a>'
        ' / <span>%s</span></div>\n'
        '      <h1>%s</h1>\n'
        '      <p class="lead">%s</p>\n'
        '    </div>\n'
        '  </section>\n\n'
        % (bi("Materials Compared", "材质对比"),
           bi("Yoga mat materials, compared honestly",
              "瑜伽垫材质，诚实地比一次"),
           bi("Eight materials we actually run on our own lines — grip wet and dry, "
              "durability, recyclability, thickness, printability and where each one is the "
              "wrong choice. Written for buyers, not for a brochure.",
              "我们自己在产线上真正在做的八种材质 —— 干湿防滑、耐用性、可回收性、厚度、"
              "印花能力，以及每种材质在什么情况下是错的选择。写给采购看的，不是宣传册。")))
    body.append(cat_nav(None, PF))
    body.append(trust_strip())
    body.append(picks_section())
    body.append(table_section())
    body.append(cards_section())
    body.append(cert_section())
    body.append(faq_section())
    body.append(cta(PF))
    body.append(footer(PF))

    path = os.path.join(ROOT, "materials.html")
    html = "".join(body)
    if not args.dry_run:
        open(path, "w", encoding="utf-8").write(html)
    print("%s materials.html  %d 字节  %d 材质  %d FAQ" %
          ("[dry]" if args.dry_run else "生成", len(html), len(ROWS), len(FAQS)))


if __name__ == "__main__":
    main()
