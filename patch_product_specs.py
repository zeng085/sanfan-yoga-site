#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fjsanfan.com 产品页规格表批量修正（阶段 1）

权威源：sanfansport.com 英文站 + 两份目录 PDF
        价格不上站；MOQ 保留站点现行值（本脚本不动 MOQ 行）

用法：
  PY=/Users/mac-zlg/.workbuddy/binaries/python/envs/default/bin/python
  $PY patch_product_specs.py --check          # 只体检，不改文件
  $PY patch_product_specs.py --lang en        # 只改 EN 27 页（阶段 1）
  $PY patch_product_specs.py --lang all       # EN + 6 语言（阶段 2，需先补译文）

设计：
  · 规格表 7 行顺序在所有 189 个页面里完全一致，按「行位」定位最稳
    0=Material 1=Size 2=Thickness 3=MOQ 4=Colors&Print 5=Compliance 6=Packaging
  · 只替换 <td> 内容，<th> 标签一律不动（各语言译文原样保留）
  · 值里没有 "&"，无需 HTML 转义；幂等，重复跑结果一致
"""
import argparse
import glob
import json
import os
import re
import sys
from urllib.parse import quote, unquote

ROOT = os.path.dirname(os.path.abspath(__file__))
LANGS = ["", "de", "ja", "ko", "fr", "it", "es"]
ROOT_EN_FILES = ["index.html", "products.html", "about.html", "faq.html", "contact.html", "blog.html"]
IDX = {"Material": 0, "Size": 1, "Thickness": 2, "MOQ": 3, "Colors": 4,
       "Compliance": 5, "Packing": 6}

CERT = "ROHS / CE / ISO 9001 / BSCI / REACH"

# 阶段 1 新增行：目标顺序固定 10 行，缺值的行不输出
DESIRED_ORDER = ["Material", "Size", "Thickness", "Weight", "MOQ",
                 "Colors", "Feature", "Logo", "Compliance", "Packaging"]

# 10 字段的最终表头。非 EN 表头一律沿用各语言站点现有译名，
# 避免同一张表里出现两套术语（如 Weight 用站点既有的 Gewicht 而非 Körpergewicht）。
LABELS = {
    "en": {"Material": "Material", "Size": "Size", "Thickness": "Thickness",
           "Weight": "Weight", "MOQ": "MOQ", "Colors": "Colors &amp; Print",
           "Feature": "Feature", "Logo": "Logo", "Compliance": "Compliance",
           "Packaging": "Packaging"},
    "de": {"Material": "Material", "Size": "Größe", "Thickness": "Dicke",
           "Weight": "Gewicht", "MOQ": "Mindestbestellmenge",
           "Colors": "Farben &amp; Druck", "Feature": "Eigenschaften", "Logo": "Logo",
           "Compliance": "Einhaltung der Vorschriften", "Packaging": "Verpackung"},
    "ja": {"Material": "素材", "Size": "サイズ", "Thickness": "厚さ",
           "Weight": "重量", "MOQ": "最小発注数量（MOQ）",
           "Colors": "カラー＆プリント", "Feature": "特徴", "Logo": "ロゴ",
           "Compliance": "コンプライアンス", "Packaging": "パッケージ"},
    "ko": {"Material": "재료", "Size": "크기", "Thickness": "두께",
           "Weight": "중량", "MOQ": "최소 주문 수량(MOQ)",
           "Colors": "색상 및 프린트", "Feature": "특징", "Logo": "로고",
           "Compliance": "규정 준수", "Packaging": "포장"},
    "fr": {"Material": "Matériau", "Size": "Taille", "Thickness": "Épaisseur",
           "Weight": "Poids", "MOQ": "Quantité minimale de commande",
           "Colors": "Couleurs et imprimés", "Feature": "Caractéristiques",
           "Logo": "Logo", "Compliance": "Conformité", "Packaging": "Emballage"},
    "it": {"Material": "Materiale", "Size": "Dimensioni", "Thickness": "Spessore",
           "Weight": "Peso", "MOQ": "Quantità minima ordinabile",
           "Colors": "Colori e stampe", "Feature": "Caratteristiche",
           "Logo": "Logo", "Compliance": "Conformità", "Packaging": "Confezione"},
    "es": {"Material": "Material", "Size": "Tamaño", "Thickness": "Espesor",
           "Weight": "Peso", "MOQ": "Cantidad mínima de pedido",
           "Colors": "Colores y estampados", "Feature": "Características",
           "Logo": "Logo", "Compliance": "Cumplimiento normativo", "Packaging": "Embalaje"},
}
NEW_LABELS = {lg: {k: v for k, v in d.items() if k in ("Weight", "Feature", "Logo")}
              for lg, d in LABELS.items()}
# 表头文本 -> 字段名。用于识别页面现有行，兼容旧 7 行与已改的 10 行。
REV = {lg: {v: k for k, v in d.items()} for lg, d in LABELS.items()}
# 新增行的中文标签（EN 页带 lang-en/lang-zh 双 span）
NEW_LABELS_ZH = {"Weight": "重量", "Feature": "特性", "Logo": "定制标识"}

# 阶段 2：各语言本地化值表（由 i18n_build/build_spec_values.py 生成）
_SPEC_JSON = os.path.join(ROOT, "i18n_build", "spec_values.json")
LANG_MAP = json.load(open(_SPEC_JSON, encoding="utf-8"))["map"] if os.path.exists(_SPEC_JSON) else {}

# ---------------------------------------------------------------- 页面数据表
# 键 = 站点 slug；值为 {字段: 英文值}。未列出的行保持原样。
# MOQ / Colors / Packing 本阶段不动。
S = {}

S["ym1"] = dict(
    Material="TPE (single layer / double layer)",
    Size="183×61 / 183×66 / 183×80 cm",
    Thickness="6 / 8 / 10 / 12 mm",
    Weight="550 g/pc (6 mm, 61 cm) – 1200 g/pc (80 cm, double layer)",
    Feature="Non-slip, Eco Friendly, Wear-Resistant, Anti-Tears",
    Logo="Laser engraving / Screen print / Emboss (customizable)",
)
S["ym2"] = dict(
    Material="TPE (double layer)",
    Size="183×80 / 183×90 cm",
    Thickness="6 / 8 / 10 / 12 mm",
    Weight="1100 g/pc (80 cm) / 1200 g/pc (90 cm)",
    Feature="Non-slip, Eco Friendly, Anti-Tears",
    Logo="Laser engraving / Screen print / Emboss",
)
S["ym3"] = dict(
    Material="TPE (double layer)",
    Size="185×122 cm",
    Thickness="6 / 8 mm",
    Weight="1450 g/pc (6 mm) / 2000 g/pc (8 mm)",
    Feature="Non-slip, Eco Friendly, Anti-Tears",
    Logo="Laser engraving / Screen print / Emboss",
)
S["ym4"] = dict(
    Material="TPE (eco double-layer)",
    Size="183×61 cm; folded 14×61 cm",
    Thickness="6 mm",
    Feature="Non-slip, Eco Friendly, Foldable, Space-saving",
    Logo="Laser engraving / Screen print / Heat transfer",
)
S["ym5"] = dict(
    Material="Natural rubber base + PU top",
    Size="185×68 cm",
    Thickness="4.5 mm",
    Weight="2900 g/pc",
    Feature="Non-slip, Eco Friendly, Wear-Resistant",
    Logo="Laser engraving / Screen print / Emboss / UV print",
)
S["ym6"] = dict(
    Material="Frosted PU + Natural Rubber",
    Size="185×68 cm",
    Thickness="4.5 mm",
    Weight="2900 g/pc",
    Feature="Non-slip, Eco Friendly, Wear-Resistant, Matte Surface",
    Logo="Laser engraving / Screen print / Emboss / UV print",
)
S["ym7"] = dict(
    Material="TPE (camouflage print)",
    Size="183×66 cm",
    Thickness="6 mm",
    Feature="Non-slip, Eco Friendly, Wear-Resistant, Camo Print",
    Logo="Laser engraving / Screen print / Emboss",
)
S["ym8"] = dict(
    Material="PVC (dome) / PVC + ABS (with base)",
    Size="Ø 58 cm",
    Feature="Anti-burst, Non-slip Base",
    Logo="Screen printing",
)
S["pr1"] = dict(
    Material="Polyester (solid / gradient / colourful) / 210T Nylon Taffeta (with handles)",
    Feature="High strength, Soft, Easy install",
    Logo="Customization Available",
)
S["pr2"] = dict(
    Material="TPE + PP / PU Rubber + PP / Cork + PP / PVC + PP",
    Size="Ø 31.5–32 cm × W 12.6–12.7 cm",
    Feature="Non-slip, High load, Eco Friendly",
    Logo="Laser engraving / Screen print / Emboss",
)
S["pr3"] = dict(
    Material="PU + Natural Rubber (meditation mat) / 100% Polyester + Sponge (bolster)",
    Size="40×60 cm (rect.) / 60×60 cm (round); bolster 64×24×13 cm",
    Thickness="4.5 mm (meditation mat)",
    Weight="550 g (bolster)",
    Feature="Non-slip, Eco Friendly, Wear-Resistant",
    Logo="Laser engraving / Screen print / Emboss",
)
S["pr4"] = dict(
    Material="EVA / POE / Cork",
    Size='23×15×7.5 cm (9" × 6" × 3")',
    Thickness='7.5 cm (3")',
    Weight="200 g/pc (EVA) / 750 g/pc (Cork)",
    Feature="Non-slip, Eco Friendly, Durable",
    Logo="Laser engraving / Screen print / Emboss",
)
S["pr5"] = dict(
    Material="TPE / EVA",
    Size="28×17×6 cm / 20×20×1.3 cm / 21×19×2 cm",
    Thickness="13 mm / 20 mm",
    Feature="Non-slip, Cushioning",
    Logo="Customization Available",
)
S["fr1"] = dict(
    Material="EVA + PVC (wolf-tooth surface)",
    Size="45×14 cm / 33×14 cm / 30×8.5 cm",
    Thickness="Ø 14 cm",
    Weight="310 g/pc",
    Feature="Non-slip, Eco Friendly, Wear-Resistant",
    Logo="Silk printing",
)
S["fr2"] = dict(
    Material="Solid EVA / EVA + PVC",
    Size="33×13 cm / 45×13.5 cm / 30×12.5 cm / 34×12.5 cm",
    Thickness="Ø 12.5 / 13 / 13.5 cm",
    Feature="Non-slip, Eco Friendly, Wear-Resistant",
    Logo="Customization Available",
)
S["fr3"] = dict(
    Material="PU + ABS",
    Size="31×10 cm",
    Feature="Vibrating, Rechargeable",
    Logo="Customization Available",
)
S["fr4"] = dict(
    Material="EVA",
    Size="34×12.5 cm / 33×13.5 cm / 52×12 cm",
    Thickness="Ø 12.5 / 13.5 cm",
    Feature="Non-slip, Eco Friendly, Wear-Resistant",
    Logo="Customization Available",
)
S["fr5"] = dict(
    Material="EVA / TPE",
    Size="Ø 6 / 7 / 7.5 / 10 cm",
    Feature="Non-slip, Eco Friendly, Deep Tissue",
    Logo="Customization Available",
)
S["rb1"] = dict(
    Material="Latex / TPE / Rubber / Polyester Cotton + Latex / Silicone",
    Size="600×50×0.35–1.1 mm / 1500×150×0.45 mm / 660×60 mm / 42×14 cm / 33×6.9 cm",
    Thickness="0.35–1.1 mm",
    Feature="Non-slip, Eco Friendly, Wear-Resistant",
    Logo="Customization Available",
)
S["rb2"] = dict(
    Material="Anti-burst PVC",
    Size="Ø 25 cm (mini) / Ø 55 / 65 / 75 cm",
    Feature="Anti-burst, Non-slip",
    Logo="Customization Available",
)
S["rb3"] = dict(
    Material="PVC (dome) / PVC + ABS (with base)",
    Size="Ø 58 cm",
    Feature="Anti-burst, Non-slip Base",
    Logo="Screen printing",
)
S["rb4"] = dict(
    Material="Plywood / Eucalyptus Multilayer Board / PP + TPE",
    Size="40×32×15 cm / 43×33×8 cm / 40×33.5×4 cm / 41.5×41.5×8.5 cm",
    Thickness="4–15 cm (by model)",
    Feature="Non-slip, Balance Training",
    Logo="Customization Available",
)
S["fi1"] = dict()  # 英文站无规格；本阶段只修标题
S["fi2"] = dict(
    Material="Cast iron + Rubber / Cast iron + Neoprene / PVC / PVC + PP / Silicone + Cast Iron",
    Size="2–20 kg (iron) / 0.5–10 kg (rubber / neoprene) / 2–10 kg (PVC) / bag 20×18 cm",
    Weight="4500 g (silicone bag kettlebell)",
    Feature="Non-slip, Eco Friendly, Wear-Resistant",
    Logo="Customized Logo Available",
)
S["fi3"] = dict(
    Material="Steel Wire + PVC / ABS + PVC / Aluminium Alloy + PVC-coated wire / PP + PVC + EVA",
    Size="Rope 2.2 / 2.4 / 2.8 / 3 m; handles 12×2 – 19.3×3.1 cm",
    Feature="Adjustable Length, Tangle-free",
    Logo="Customized Logo Available",
)
S["fi4"] = dict(
    Material="Steel + Hydraulic / PP / PE / ABS",
    Size="110×41×20 cm / 40×40×30 cm / 68×28×15 cm / 72×35×10 cm / 78×30×10 cm",
    Thickness="Adjustable 10 / 15 / 20 / 25 / 30 cm",
    Feature="Height Adjustable, Compact",
    Logo="Customization Available",
)
S["fi5"] = dict(
    Material="Silicone + Cast Iron / Cast iron + Rubber + Steel / Cast iron + Neoprene",
    Size="1–10 kg (dumbbells); barbell 91 / 110 cm",
    Weight="1–2.5 kg (silicone) / 15 / 25 lb (barbell)",
    Feature="Non-slip, Eco Friendly, Wear-Resistant",
    Logo="Customized Logo Available",
)

# ---------------------------------------------------------------- 文本修正
# GLOBAL_TEXT：对全部 EN 文件生效（27 产品页 + products.html + index.html）
# 顺序敏感：先清历史重复碎片，再改数值，最后改名/改材质措辞
GLOBAL_TEXT = [
    # ① 历史遗留的重复碎片（本次改动之前就存在，属页面上的可见乱码）
    ('widths 61–122 cm (24"–48") (24"–48") (24–48"), thickness 4–12 mm (5/32"–1/2") (5/32"–1/2").',
     'widths 61 / 66 / 80 cm (24" / 26" / 31.5"), thickness 6–12 mm (1/4"–1/2").'),
    ('Eco double-layer, 4–12 mm (5/32"–1/2") (5/32"–1/2")',
     'Eco double-layer, 6–12 mm (1/4"–1/2")'),
    # ② 数值错误（裸引号与 &quot; 两种编码都覆盖）
    ('widths 61–122 cm (24"–48"), thickness 4–12 mm (5/32"–1/2")',
     'widths 61 / 66 / 80 cm (24" / 26" / 31.5"), thickness 6–12 mm (1/4"–1/2")'),
    ('widths 61–122 cm (24&quot;–48&quot;), thickness 4–12 mm (5/32&quot;–1/2&quot;)',
     'widths 61 / 66 / 80 cm (24&quot; / 26&quot; / 31.5&quot;), thickness 6–12 mm (1/4&quot;–1/2&quot;)'),
    ('Widths 61–122 cm (24"–48"), thickness 4–12 mm (5/32"–1/2")',
     'Widths 61 / 66 / 80 cm (24" / 26" / 31.5"), thickness 6–12 mm (1/4"–1/2")'),
    ('61–122 cm', '61 / 66 / 80 cm'),
    ('(24"–48")', '(24" / 26" / 31.5")'),
    ('(24&quot;–48&quot;)', '(24&quot; / 26&quot; / 31.5&quot;)'),
    ('4–12 mm', '6–12 mm'),
    ('(5/32"–1/2")', '(1/4"–1/2")'),
    ('(5/32&quot;–1/2&quot;)', '(1/4&quot;–1/2&quot;)'),
    ('80/122 cm', '80 / 90 cm'),
    ('1830×610 / 1830×800 / 1850×900 / 2000×1000 / 1850×1220 mm (48")',
     '183×61 / 183×66 / 183×80 cm'),
    ('1830×610 / 1850×800 mm (31")', '185×68 cm (73" × 27")'),
    ('80 cm (31") / 122 cm (48") widths', '183×80 / 183×90 cm widths'),
    ('33 / 38 cm (15") diameters', 'Ø 31.5–32 cm × W 12.6–12.7 cm'),
    ('9×15×23 cm (9") standard', '23×15×7.5 cm (9" × 6" × 3")'),
    ('25×7.5 to 45×14 cm (6")', 'Ø 12.5–14 cm, length 30–52 cm'),
    ('25 cm (10") mini / standard sizes', 'Ø 25 cm mini / 55 / 65 / 75 cm'),
    ('4–24 kg', '0.5–20 kg by material'),
    # ③ 首页认证叙述
    ('REACH, CA Prop 65, 6P/7P compliance, ISO 9001 &amp; BSCI audited for global markets.',
     'ROHS / CE / ISO 9001 / BSCI / REACH compliance for global markets.'),
    # ④ 产品名与材质措辞
    ('Eco double-layer TPE', 'Eco TPE (single / double layer)'),
    ('Double-layer eco TPE, no PVC, no odor', 'Eco TPE, no PVC, no odor'),
    ('双层环保 TPE，无 PVC、无异味', '环保 TPE，无 PVC、无异味'),
    ('Camo PU Yoga Mat', 'Camouflage TPE Yoga Mat'),
    ('迷彩 PU 瑜伽垫', '迷彩 TPE 瑜伽垫'),
    ('Camouflage-print PU rubber mat', 'Camouflage-print TPE mat'),
    ('迷彩印花 PU 橡胶垫', '迷彩印花 TPE 垫'),
    ('Bold camo print PU rubber grip', 'Bold camo print TPE grip'),
    ('Mini Stepper', 'Stair Climber'),
    ('Meditation Cushion (Zafu)', 'Meditation Mat & Yoga Bolster'),
    ('冥想坐垫（Zafu）', '冥想垫与瑜伽抱枕'),
    ('alt="Meditation Cushion"', 'alt="Meditation Mat &amp; Yoga Bolster"'),
    ('"name": "Dumbbell Set"', '"name": "Dumbbell & Barbell"'),
    ('Dumbbell / Kettlebell Set', 'Dumbbell &amp; Barbell'),
    ('哑铃 / 壶铃套装', '哑铃与杠铃'),
    ('high-strength silk', 'high-strength polyester or 210T nylon taffeta'),
    ('High-strength aerial silk', 'High-strength polyester / 210T nylon'),
    ('高强度空中丝绸', '高强度聚酯纤维 / 210T 尼龙'),
    # —— 以下为阶段 1 复查补漏：正文/meta/JSON-LD 里残留的旧证书口径与旧规格 ——
    # about.html / faq.html 的 meta description（裸 & 与 &amp; 两种编码都要覆盖）
    ("7-day sampling, REACH & CA Prop 65 compliant.",
     "7-day sampling, ROHS / CE / REACH compliant."),
    ("7-day sampling, REACH &amp; CA Prop 65 compliant.",
     "7-day sampling, ROHS / CE / REACH compliant."),
    ("MOQ, REACH/CA Prop 65 certification, customization, sampling & Amazon FBA shipping",
     "MOQ, ROHS / CE / REACH certification, customization, sampling & Amazon FBA shipping"),
    ("MOQ, REACH/CA Prop 65 certification, customization, lead time, Amazon FBA shipping",
     "MOQ, ROHS / CE / REACH certification, customization, lead time, Amazon FBA shipping"),
    # faq.html 的 JSON-LD 与内联兜底文案（正文里也有同句）
    ("For the US, CA Prop 65 and 6P/7P phthalate limits matter; for the EU, REACH (SVHC) compliance is required.",
     "For the US, ROHS and CE marking matter; for the EU, REACH (SVHC) compliance is required."),
    # products/fi5.html 的 JSON-LD description（RELATED_FIX 只覆盖 &amp; 变体，漏了裸 & 变体）
    ("Home light-training dumbbell & kettlebell set (6 kg / 2 kg), portable shaping fitness gear.",
     "Silicone dumbbells (1–2.5 kg) and cast-iron dumbbells / barbells (0.5–10 kg; bar 91 / 110 cm); "
     "six silicone colorways, custom logo."),
]

# 博客文章（blog/*.html）不在 ROOT_EN_FILES 里，单独一套对，避免误伤正文里的法规科普。
# 注意：文章正文里把 Prop 65 / 6P/7P 当「法规」讲的部分必须保留，只改自称持证的表述。
BLOG_TEXT = [
    # 榜单页里「三梵」自己那一行的证书列
    ("ISO 9001, BSCI, SGS, REACH, CA Prop 65", "ROHS / CE / ISO 9001 / BSCI / REACH"),
    ("Publishes MOQ 100 pcs, 7-day sampling, ISO 9001 and BSCI audits, and SGS, REACH and CA Prop 65 compliance.",
     "Publishes MOQ 100 pcs, 7-day sampling, ISO 9001 and BSCI audits, and ROHS, CE and REACH compliance."),
]

# 关联产品卡的修正：同名产品卡散布在各产品页；fi1 卡的副标题还串成了 fi5 的产品名
RELATED_FIX = {
    "fi1": [("Mini Stepper", "Stair Climber"), ("硅胶哑铃", "迷你踏步机"),
            ("Compact home stepper", "Compact stair climber"),
            ("硅胶包胶哑铃，防滚不伤地板；多重量多色可选，适合家用与健身房产品线。",
             "紧凑型家用踏步机，有氧与下肢训练，阻力可调、占地小。")],
    "fi5": [
        ("Home light-training dumbbell &amp; kettlebell set (6 kg / 2 kg), portable shaping fitness gear.",
         "Silicone dumbbells (1–2.5 kg) and cast-iron dumbbells / barbells (0.5–10 kg; bar 91 / 110 cm); six silicone colorways, custom logo."),
        ("家用轻训哑铃 &amp; 壶铃套装（6 kg / 2 kg），便携塑形健身器材。",
         "硅胶哑铃（1–2.5 kg）与铸铁哑铃 / 杠铃（0.5–10 kg，杆长 91 / 110 cm）；六种硅胶配色，可定制 logo。"),
    ],
    "pr3": [
        ("Zafu meditation cushion with buckwheat fill and cotton cover; round and rectangular styles, custom fabrics.",
         "PU + natural rubber meditation mat (40×60 / 60×60 cm, 4.5 mm) with a 100% polyester bolster (64×24×13 cm, 550 g); custom colors."),
        ("荞麦填充 Zafu 冥想坐垫，棉质外套；圆形/长方形可选，面料可定制。",
         "PU + 天然橡胶冥想垫（40×60 / 60×60 cm，4.5 mm）搭配 100% 聚酯纤维抱枕（64×24×13 cm，550 g）；颜色与尺寸可定制。"),
    ],
}

# WhatsApp 预填文案里的产品名（URL 编码，普通文本替换抓不到）
WA_NAME = {
    "ym7": (("Camo PU Yoga Mat", "迷彩 PU 瑜伽垫"),
            ("Camouflage TPE Yoga Mat", "迷彩 TPE 瑜伽垫")),
    "fi1": (("Mini Stepper", "硅胶哑铃"), ("Stair Climber", "迷你踏步机")),
    "fi5": (("Dumbbell / Kettlebell Set", "哑铃 / 壶铃套装"),
            ("Dumbbell & Barbell", "哑铃与杠铃")),
    "pr3": (("Meditation Cushion (Zafu)", "冥想坐垫（Zafu）"),
            ("Meditation Mat & Yoga Bolster", "冥想垫与瑜伽抱枕")),
}
WA_PREFIX = {"en": "Hi SANFAN, I am interested in ", "zh": "你好三梵，我想了解 "}

# PER_PAGE_TEXT：只在指定文件生效
PER_PAGE_TEXT = {
    # fi5：6 kg / 2 kg「哑铃+壶铃套装」三源皆无依据 → 改为硅胶系列（1–2.5 kg）+ 铸铁系列（0.5–10 kg）+ 杠铃
    "products/fi5.html": [
        ("Home light-training dumbbell &amp; kettlebell set (6 kg / 2 kg), portable shaping fitness gear.",
         "Silicone dumbbells (1–2.5 kg) and cast-iron dumbbells / barbells (0.5–10 kg; bar 91 / 110 cm); six silicone colorways, custom logo."),
        ("Home light-training dumbbell &amp; kettlebell set (6 kg / 2 kg) — portable shaping fitness gear for private-label lines.",
         "Silicone dumbbells (1–2.5 kg) and cast-iron dumbbells / barbells (0.5–10 kg; bar 91 / 110 cm) — six silicone colorways for private-label lines."),
        ("家用轻训哑铃 &amp; 壶铃套装（6 kg / 2 kg），便携塑形健身器材。",
         "硅胶哑铃（1–2.5 kg）与铸铁哑铃 / 杠铃（0.5–10 kg，杆长 91 / 110 cm）；六种硅胶配色，可定制 logo。"),
        ("家用轻训哑铃 &amp; 壶铃套装（6 kg / 2 kg），便携塑形健身器材，适合贴牌线。",
         "硅胶哑铃（1–2.5 kg）与铸铁哑铃 / 杠铃（0.5–10 kg，杆长 91 / 110 cm）——六种硅胶配色，适合贴牌线。"),
        ("<li>Dumbbell + kettlebell set</li>", "<li>Silicone &amp; cast-iron ranges</li>"),
        ("<li>6 kg / 2 kg portable</li>", "<li>Dumbbells 0.5–10 kg; bar 91 / 110 cm</li>"),
        ("<li>Home shaping gear</li>", "<li>Six silicone colorways</li>"),
        ("<li>哑铃 + 壶铃套装</li>", "<li>硅胶 / 铸铁两种系列</li>"),
        ("<li>6 kg / 2 kg 便携</li>", "<li>哑铃 0.5–10 kg；杆长 91 / 110 cm</li>"),
        ("<li>家用塑形器材</li>", "<li>六种硅胶配色</li>"),
    ],
    # fi1 页自身的 H1/H2 中文副标题都串成了 fi5 的产品名
    "products/fi1.html": [
        ("硅胶哑铃 — 三梵", "迷你踏步机 — 三梵"),
        ('<span class="lang-en">Mini Stepper</span><span class="lang-zh">硅胶哑铃</span>',
         '<span class="lang-en">Mini Stepper</span><span class="lang-zh">迷你踏步机</span>'),
        # 简介段整段串成了 fi5（哑铃）的文案
        ("硅胶包胶哑铃，防滚不伤地板；多重量多色可选，适合家用与健身房产品线。",
         "紧凑型家用踏步机，有氧与下肢训练，阻力可调、占地小。"),
    ],
    "products/pr3.html": [
        ("Meditation Cushion (Zafu)", "Meditation Mat & Yoga Bolster"),
        ("冥想坐垫（Zafu）", "冥想垫与瑜伽抱枕"),
        ("Zafu meditation cushion with buckwheat fill and cotton cover; round and rectangular styles, custom fabrics.",
         "PU + natural rubber meditation mat (40×60 / 60×60 cm, 4.5 mm) with a 100% polyester bolster (64×24×13 cm, 550 g); custom colors."),
        ("Zafu meditation cushion with buckwheat fill and cotton cover — round and rectangular styles, custom fabrics.",
         "PU + natural rubber meditation mat (40×60 / 60×60 cm, 4.5 mm) with a 100% polyester bolster (64×24×13 cm, 550 g) — custom colors and sizes."),
        ("荞麦填充 Zafu 冥想坐垫，棉质外套；圆形/长方形可选，面料可定制。",
         "PU + 天然橡胶冥想垫（40×60 / 60×60 cm，4.5 mm）搭配 100% 聚酯纤维抱枕（64×24×13 cm，550 g）；颜色与尺寸可定制。"),
        ("Buckwheat fill, cotton cover", "PU + natural rubber meditation mat"),
        ("Round &amp; rectangular styles", "Polyester bolster with sponge fill"),
        ("荞麦填充、棉质外套", "PU + 天然橡胶冥想垫"),
        ("圆形与长方形可选", "聚酯纤维内芯抱枕"),
        ("面料可定制", "颜色与尺寸可定制"),
    ],
}

# 改名同步到 EN 列表页/首页（保持 EN 版本内部一致；语言站属阶段 2）
ROOT_FIX = {
    "products.html": [("Camo PU Yoga Mat", "Camouflage TPE Yoga Mat"),
                      ("Camouflage-print PU rubber mat", "Camouflage-print TPE mat"),
                      ("Mini Stepper", "Stair Climber")],
    "index.html": [("Camo PU Yoga Mat", "Camouflage TPE Yoga Mat"),
                   ("Mini Stepper", "Stair Climber")],
}

# ---------------------------------------------------------------- i18n 字典
# main.js 里的 I18N 是首页/列表页中英切换的数据源，必须与页面同步
I18N_NEW = {
    "g1.s": ("Eco TPE, 6–12 mm, widths 61 / 66 / 80 cm", "环保 TPE，6–12 mm，宽度 61 / 66 / 80 cm"),
    "g2.s": ("Extra-wide 80 / 90 cm", "80 / 90 cm 加宽"),
    "g7.n": ("Camouflage TPE Yoga Mat", "迷彩 TPE 瑜伽垫"),
    "g7.s": ("Bold camo print, TPE", "迷彩印花，TPE"),
    "g9.s": ("Anti-gravity polyester", "反重力聚酯纤维"),
    "g10.s": ("Polyester + mount kit", "聚酯纤维 + 挂件套装"),
    "g12.n": ("Meditation Mat & Bolster", "冥想垫与抱枕"),
    "g12.s": ("PU + rubber mat, polyester bolster", "PU + 橡胶垫，聚酯抱枕"),
    "g23.n": ("Stair Climber", "迷你踏步机"),
    "g23.s": ("Compact stair climber", "有氧踏步训练"),
    "ym1.d": ('Eco TPE (single / double layer), non-slip textured surface, widths 61 / 66 / 80 cm (24" / 26" / 31.5"), thickness 6–12 mm (1/4"–1/2"). Solid, economy and special grades.',
              "环保 TPE（单层/双层），防滑纹理表面，宽度 61 / 66 / 80 cm，厚度 6–12 mm。可选实重、经济、特供等级。"),
    "ym2.d": ("Extra-wide 80 / 90 cm TPE mat for dynamic and partner practice; same eco TPE grip.",
              "80 / 90 cm 加宽 TPE 垫，适合流瑜伽与双人练习；同样环保抓地。"),
    "ym7.t": ("Camouflage TPE Yoga Mat", "迷彩 TPE 瑜伽垫"),
    "ym7.d": ("Camouflage-print TPE mat with a bold look, ideal for branded lines.",
              "迷彩印花 TPE 垫，外观硬朗，适合做品牌定制线。"),
    "pr1.d": ("Anti-gravity aerial yoga hammock in high-strength polyester or 210T nylon taffeta; ceiling mount kit available; custom colors and lengths for aerial yoga and flying pilates.",
              "高强度聚酯纤维或 210T 尼龙塔夫绸反重力空中瑜伽吊床，可配天花板挂件套装；颜色与长度均可定制，适用空中瑜伽与飞行普拉提。"),
    "pr3.t": ("Meditation Mat & Yoga Bolster", "冥想垫与瑜伽抱枕"),
    "pr3.d": ("PU + natural rubber meditation mat (40×60 / 60×60 cm, 4.5 mm) with a 100% polyester bolster (64×24×13 cm, 550 g); custom colors.",
              "PU + 天然橡胶冥想垫（40×60 / 60×60 cm，4.5 mm）搭配 100% 聚酯纤维抱枕（64×24×13 cm，550 g）；颜色与尺寸可定制。"),
    "fi1.t": ("Stair Climber", "迷你踏步机"),
    "fi1.d": ("Compact home stepper for cardio and lower-body training; adjustable resistance, small footprint.",
              "紧凑型家用踏步机，有氧与下肢训练，阻力可调、占地小。"),
    "fi5.t": ("Dumbbell & Barbell", "哑铃与杠铃"),
    "fi5.d": ("Silicone dumbbells (1–2.5 kg) and cast-iron dumbbells / barbells (0.5–10 kg; bar 91 / 110 cm); six silicone colorways, custom logo.",
              "硅胶哑铃（1–2.5 kg）与铸铁哑铃 / 杠铃（0.5–10 kg，杆长 91 / 110 cm）；六种硅胶配色，可定制 logo。"),
    "spec1.d": ('183×61 / 183×66 / 183×80 cm\\nThickness 6–12 mm (1/4"–1/2")\\nMOQ 100 pcs',
                "183×61 / 183×66 / 183×80 cm\\n厚度 6–12 mm\\n起订量 100 片"),
    "spec2.d": ("183×80 / 183×90 cm widths\\nEco TPE\\nMOQ 100 pcs",
                "183×80 / 183×90 cm 宽度\\n环保 TPE\\n起订量 100 片"),
    "spec3.d": ('Natural rubber base + PU anti-slip top\\n185×68 cm (73" × 27")\\nMOQ on request',
                "天然橡胶底 + PU 防滑面\\n185×68 cm\\n起订量 面议"),
    "spec5.d": ("Polyester / 210T nylon\\nCeiling mount kit available\\nCustom colors & sizes\\nMOQ on request",
                "聚酯纤维 / 210T 尼龙\\n可配天花板挂件\\n颜色尺寸可定制\\n起订量 面议"),
    "spec6.d": ("TPE / PU rubber / Cork / PVC\\nØ 31.5–32 cm × W 12.6–12.7 cm\\nCustom colors\\nMOQ on request",
                "TPE / PU 橡胶 / 软木 / PVC\\n直径 31.5–32 cm × 宽 12.6–12.7 cm\\n颜色可定制\\n起订量 面议"),
    "spec7.d": ('EVA / POE / Cork\\n23×15×7.5 cm (9" × 6" × 3")\\nMOQ 500 pcs',
                "EVA / POE / 软木\\n23×15×7.5 cm\\n起订量 500 块"),
    "spec8.d": ("Ø 12.5–14 cm, length 30–52 cm\\nSmooth / wolf-tooth / solid\\nMOQ 500 pcs",
                "直径 12.5–14 cm，长度 30–52 cm\\n光面 / 狼牙 / 实心\\n起订量 500 个"),
    "spec9.d": ("Ø 25 cm mini / 55 / 65 / 75 cm\\nAnti-burst\\nMOQ on request",
                "Ø 25 cm 迷你 / 55 / 65 / 75 cm\\n防爆设计\\n起订量 面议"),
    "str2.d": ("In-house QC with batch traceability, ISO 9001 & BSCI audited, materials tested to ROHS / CE / REACH. Not just a promise — documented.",
               "厂内 QC 加批次追溯，ISO 9001 与 BSCI 审核，材质按 ROHS / CE / REACH 检测。不是空话，有凭证。"),
    "faq.a7": ("Yes. Our TPE mats are odorless, recyclable and free of harmful plasticizers. Materials are selected for ROHS / CE / REACH compliance so they are safe for daily use in any market.",
               "是的。TPE 垫无异味、可回收、不含害增塑剂，材质按 ROHS / CE / REACH 选型，确保各市场日常使用安全。"),
    "faq.a8": ("For the US, ROHS and CE marking matter; for the EU, REACH (SVHC) compliance is required. SANFAN holds ISO 9001 and BSCI, and our materials are tested to these standards.",
               "美国看 ROHS 与 CE 认证；欧盟需 REACH（SVHC）合规。三梵持有 ISO 9001 与 BSCI，材质均按这些标准检测。"),
    "faq.a13": ('Nearly everything: material, size, thickness (6–12 mm (1/4"–1/2")), color, double-color, surface finish, logo, fold style and packaging. Just share your spec and we engineer it.',
                "几乎都能：材质、尺寸、厚度（6–12 mm）、颜色、双色、表面工艺、logo、折叠方式与包装。发来规格，我们帮你实现。"),
    "faq.a14": ('Yes. Beyond standard 1830×610 mm (72" × 24") we produce wide (80 / 90 cm) and double-wide (122 cm) formats, plus custom lengths and thicknesses. Send your dimensions and we confirm tooling.',
                "能。除标准 1830×610 mm 外，我们做加宽（80 / 90 cm）与双宽（122 cm），以及定制长度与厚度。发来尺寸，我们确认模具。"),
}


def fix_i18n(path):
    """把 I18N_NEW 写进 main.js 的中英两个字典块"""
    src = open(path, encoding="utf-8").read()
    i = src.find("const I18N = {")
    if i < 0:
        return 0
    j = src.find("\n  zh: {", i)
    k = src.find("\n};", j)
    if j < 0 or k < 0:
        return 0
    en, zh, tail = src[:j], src[j:k], src[k:]
    n = 0
    for key, (new_en, new_zh) in I18N_NEW.items():
        pat = re.compile(r"'%s': '(?:[^'\\\\]|\\\\.)*'," % re.escape(key))
        en2, c1 = pat.subn(lambda m: "'%s': '%s'," % (key, new_en), en, count=1)
        zh2, c2 = pat.subn(lambda m: "'%s': '%s'," % (key, new_zh), zh, count=1)
        # 只统计真正被改写的条目，保证脚本可重复运行且计数可信
        n += int(en2 != en and c1) + int(zh2 != zh and c2)
        en, zh = en2, zh2
    open(path, "w", encoding="utf-8").write(en + zh + tail)
    return n


ROW_RE = re.compile(r"<tr><th>.*?</th><td>.*?</td></tr>", re.S)
TD_RE = re.compile(r"<td>.*?</td>", re.S)
TH_RE = re.compile(r"<th>(.*?)</th>", re.S)
FIELD_ORDER = ["Material", "Size", "Thickness", "MOQ", "Colors", "Compliance", "Packaging"]


def esc(v):
    """只转义裸 &，不碰已有实体（表头含 &amp;）"""
    return re.sub(r"&(?!(?:amp|lt|gt|quot|#\d+|#x[0-9a-fA-F]+);)", "&amp;", v)


def row_field(block, lang):
    """从一行 <tr> 反查字段名；EN 页取 .lang-en span 文本"""
    m = TH_RE.search(block)
    if not m:
        return None
    inner = m.group(1)
    sp = re.search(r'<span class="lang-en">(.*?)</span>', inner, re.S)
    txt = re.sub(r"<[^>]+>", "", sp.group(1) if sp else inner).strip()
    return REV[lang].get(txt)


def row_value(block):
    m = TD_RE.search(block)
    return re.sub(r"</?td>", "", m.group(0)).strip() if m else None


def fix_table(html, fields, lang):
    """按字段名替换 <td>，并按 DESIRED_ORDER 重建 tbody。返回 (新html, 改动计数)

    按字段名匹配（而非行序），因此旧 7 行表和已改的 10 行表都能正确处理，
    脚本可重复运行。表中若有无法识别的行则整体跳过，避免丢数据。
    """
    m = re.search(r'(<table class="spec-table"><tbody>)(.*?)(</tbody></table>)', html, re.S)
    if not m:
        return html, 0
    blocks = ROW_RE.findall(m.group(2))
    orig = {}
    for block in blocks:
        k = row_field(block, lang)
        if k and k not in orig:
            orig[k] = block
    if not orig or len(orig) != len(blocks):
        return html, 0

    changed = 0
    labels = LABELS[lang]

    def cell(key, block):
        """替换 block 里唯一的 <td>"""
        val = fields.get(key)
        if val is None:
            return block, False
        new_td = "<td>%s</td>" % esc(str(val))
        out = TD_RE.sub(lambda _: new_td, block, count=1)
        return out, out != block

    body = []
    for key in DESIRED_ORDER:
        if key in orig:
            block, ch = cell(key, orig[key])
            changed += 1 if ch else 0
            body.append(block)
        elif fields.get(key):
            if lang == "en":
                th = ('<th><span class="lang-en">%s</span>'
                      '<span class="lang-zh">%s</span></th>' % (labels[key], NEW_LABELS_ZH[key]))
            else:
                th = "<th><span >%s</span></th>" % labels[key]
            body.append("<tr>%s<td>%s</td></tr>" % (th, esc(str(fields[key]))))
            changed += 1

    return html[:m.start(2)] + "".join(body) + html[m.end(2):], changed


def lang_fields(src, slug, lang):
    """语言页字段值 = 该页现有译法（含 MOQ，保持冻结）+ 已变化字段按译表覆盖

    用户约束：MOQ 以站点现有值为准，因此 MOQ 永不覆盖；
    EN 侧没变的字段保持该语言既有译法，只补 EN 侧真正修正过的值。
    """
    out = {}
    m = re.search(r'<table class="spec-table".*?</table>', src, re.S)
    if m:
        for b in ROW_RE.findall(m.group(0)):
            k = row_field(b, lang)
            if k and k not in out:
                out[k] = row_value(b)
    lmap = LANG_MAP.get(lang, {})
    for f in DESIRED_ORDER:
        if f == "MOQ":                      # 约束 2：MOQ 冻结
            continue
        en = S[slug].get(f)
        if f == "Compliance":
            en = en or CERT                 # EN 侧认证行全站统一，S 表未单独登记
        if not en:
            continue
        tgt = lmap.get("%s|%s" % (f, en))
        if tgt:
            out[f] = tgt
    return out


def apply_pairs(text, pairs):
    n = 0
    for old, rep in pairs:
        if old in text:
            n += text.count(old)
            text = text.replace(old, rep)
    return text, n


def fix_related_cards(html, slug):
    """修正「相关产品」卡片块里指向 slug 的标题/描述"""
    pairs = RELATED_FIX.get(slug)
    if not pairs:
        return html, 0
    pat = re.compile(r'(<a class="prod-card" href="(?:\.\./)?products/%s\.html">)(.*?)(</a>)' % slug, re.S)
    n = 0

    def sub(m):
        nonlocal n
        body, k = apply_pairs(m.group(2), pairs)
        n += k
        return m.group(1) + body + m.group(3)

    return pat.sub(sub, html), n


def fix_wa_text(html, slug):
    """修 WhatsApp 预填文案里的产品名（先解码、再改名、再统一编码）"""
    if slug not in WA_NAME:
        return html, 0
    (old_en, old_zh), (new_en, new_zh) = WA_NAME[slug]
    n = [0]

    def sub(m):
        txt = unquote(m.group(2))
        new_txt = txt.replace(old_en, new_en).replace(old_zh, new_zh)
        if new_txt == txt:
            return m.group(0)
        n[0] += 1
        return m.group(1) + quote(new_txt, safe="")

    out = re.sub(r'(wa\.me/8615959029082\?text=)([^"&]*)', sub, html)
    return out, n[0]


def run(langs, check):
    report = []
    for L in langs:
        base = "products" if L == "" else "%s/products" % L
        for path in sorted(glob.glob(os.path.join(ROOT, base, "*.html"))):
            slug = os.path.basename(path)[:-5]
            src = open(path, encoding="utf-8").read()
            if slug not in S:
                report.append((L or "en", slug, "SKIP 不在数据表", 0))
                continue
            if L == "":
                fields = dict(S[slug])
                # 认证行：全站统一为「英文站 + 目录证书」可证实的 5 项
                fields["Compliance"] = CERT
            else:
                fields = lang_fields(src, slug, L)
            new, n = fix_table(src, fields, L or "en")
            if L == "":  # 文本修正只做 EN，语言站属阶段 2
                for s2 in RELATED_FIX:
                    if s2 == slug:
                        continue
                    blk, k = fix_related_cards(new, s2)
                    new, n = blk, n + k
                new, k = apply_pairs(new, PER_PAGE_TEXT.get(os.path.relpath(path, ROOT), []))
                n += k
                new, k = fix_wa_text(new, slug)
                n += k
                new, k = apply_pairs(new, GLOBAL_TEXT)
                n += k
            state = "OK" if new != src else "NOCHANGE"
            if not check and new != src:
                open(path, "w", encoding="utf-8").write(new)
            report.append((L or "en", slug, state, n))

    # EN 列表页/首页/其它根页：同一套全局文本修正
    if "" in langs:
        for fname in sorted(ROOT_EN_FILES):
            path = os.path.join(ROOT, fname)
            if not os.path.exists(path):
                continue
            src = open(path, encoding="utf-8").read()
            new, n = apply_pairs(src, GLOBAL_TEXT)
            for s2 in RELATED_FIX:
                new, k = fix_related_cards(new, s2)
                n += k
            state = "OK" if new != src else "NOCHANGE"
            if not check and new != src:
                open(path, "w", encoding="utf-8").write(new)
            report.append(("en", fname, state, n))
        # i18n 字典（改 JS 必须全站 bump ?v=）
        js = os.path.join(ROOT, "assets/js/main.js")
        before = open(js, encoding="utf-8").read()
        cnt = fix_i18n(js)
        if check:
            open(js, "w", encoding="utf-8").write(before)
        report.append(("en", "assets/js/main.js", "OK" if cnt else "NOCHANGE", cnt))

    # 博客文章：法规科普（Prop 65 / 6P/7P 作为美国法规被讨论）必须保留，
    # 只把「自称持有这些证书」的口径改为可证实的 5 项。
    for L in langs:
        bdir = os.path.join(ROOT, "blog") if L == "" else os.path.join(ROOT, L, "blog")
        for path in sorted(glob.glob(os.path.join(bdir, "*.html"))):
            src = open(path, encoding="utf-8").read()
            new, n = apply_pairs(src, BLOG_TEXT)
            if new != src and not check:
                open(path, "w", encoding="utf-8").write(new)
            report.append((L or "en", os.path.relpath(path, ROOT),
                           "OK" if new != src else "NOCHANGE", n))
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="en", choices=["en", "all"] + [x for x in LANGS if x])
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    langs = LANGS if a.lang == "all" else ["" if a.lang == "en" else a.lang]
    rep = run(langs, a.check)
    tot = sum(1 for r in rep if r[2] == "OK")
    print("%s  页面 %d  有改动 %d" % ("[CHECK]" if a.check else "[APPLY]", len(rep), tot))
    for L, slug, st, n in rep:
        if st != "NOCHANGE":
            print("  %-3s %-5s %-9s %d 处" % (L, slug, st, n))
    unchanged = [r for r in rep if r[2] == "NOCHANGE"]
    if unchanged:
        print("  未变化：", ", ".join("%s/%s" % (r[0], r[1]) for r in unchanged))


if __name__ == "__main__":
    main()
