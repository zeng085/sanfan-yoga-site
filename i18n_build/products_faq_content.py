#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0-C 数据源：147 个产品页的 FAQ 模板（EN 源 + ZH 手写）+ 规格表字段的多语言标签表。

设计要点
1. **答案里必须带该产品自己的真实规格值**（MOQ / 材质 / 尺寸 / 厚度 / 配色 / Logo / 包装 / 认证）。
   否则 147 页会出现同一段模板文字 → 重复内容，GEO 反而扣分。值从页面自身的 spec table 里读，
   语言页读到的是已翻译好的值，**不需要重新翻译规格**。
2. 字段标签按"**长标签优先**"匹配（`Colors & Print` 必须先于 `Colors`、`パッケージサイズ` 先于 `パッケージ`），
   EN 页的 `<th>` 里 EN/ZH 两个 span 连在一起，故一律用 `startswith` 且按标签长度倒序试。
3. 模板里的占位符只放在语法安全的位置（句首名词位 / 系表结构），且都是全大写 token —— DeepL 会原样保留。
4. ⚠️ 不写价格、不写任何站上没有的数字。
"""

# ---------------------------------------------------------------- 字段标签表
LABELS = {
    "MOQ": {
        "en": ["MOQ", "Minimum Order Quantity"],
        "de": ["Mindestbestellmenge"],
        "ja": ["最小発注数量"],
        "ko": ["최소 주문 수량"],
        "fr": ["Quantité minimale de commande"],
        "it": ["Quantità minima ordinabile"],
        "es": ["Cantidad mínima de pedido"],
    },
    "MATERIAL": {
        "en": ["Material"], "de": ["Material"], "ja": ["素材"], "ko": ["재료"],
        "fr": ["Matériau"], "it": ["Materiale"], "es": ["Material"],
    },
    "SIZE": {
        "en": ["Size", "Dimensions"], "de": ["Größe"], "ja": ["サイズ"], "ko": ["크기"],
        "fr": ["Taille"], "it": ["Dimensioni"], "es": ["Tamaño"],
    },
    "THICK": {
        "en": ["Thickness"], "de": ["Dicke"], "ja": ["厚さ"], "ko": ["두께"],
        "fr": ["Épaisseur"], "it": ["Spessore"], "es": ["Espesor"],
    },
    "COLORS": {
        "en": ["Colors & Print", "Colors"], "de": ["Farben & Druck", "Farben"],
        "ja": ["カラー＆プリント", "色"], "ko": ["색상 및 프린트", "색상"],
        "fr": ["Couleurs et imprimés", "Couleurs"], "it": ["Colori e stampe", "Colori"],
        "es": ["Colores y estampados", "Colores"],
    },
    "LOGO": {
        "en": ["Logo"], "de": ["Logo"], "ja": ["ロゴ"], "ko": ["로고"],
        "fr": ["Logo"], "it": ["Logo"], "es": ["Logotipo"],
    },
    "FEATURE": {
        "en": ["Feature"], "de": ["Funktion"], "ja": ["特集"], "ko": ["특집"],
        "fr": ["Fonctionnalité"], "it": ["Caratteristica"], "es": ["Característica"],
    },
    "PACKAGING": {
        "en": ["Packaging"], "de": ["Verpackung"], "ja": ["パッケージ"], "ko": ["포장"],
        "fr": ["Emballage"], "it": ["Confezione"], "es": ["Embalaje"],
    },
    "COMPLIANCE": {
        "en": ["Compliance"], "de": ["Einhaltung der Vorschriften"], "ja": ["コンプライアンス"],
        "ko": ["규정 준수"], "fr": ["Conformité"], "it": ["Conformità"],
        "es": ["Cumplimiento normativo"],
    },
}

LANGS = ["de", "ja", "ko", "fr", "it", "es"]
ALL_LANGS = ["en"] + LANGS

# ---------------------------------------------------------------- 模板
# 需要翻译的 EN 串（占位符：XXNAMEXX / XXMOQXX / XXSIZEXX / XXTHICKXX / XXCOMPXX）
EN_STRINGS = {
    "title": "XXNAMEXX — buyer questions",
    "q1": "What is the minimum order quantity?",
    "a1": "Minimum order quantity for XXNAMEXX is XXMOQXX. A first order at that quantity is "
          "enough to test a market, with your own logo, colour and packaging set on the same run.",
    "a1f": "The minimum order quantity for XXNAMEXX is quoted per specification and finish. "
           "Tell us the quantity you have in mind and we return the exact minimum for that build.",
    "q2": "Can this be manufactured under our own brand?",
    "a2": "Yes — OEM and ODM are the default mode for XXNAMEXX. Send your logo artwork, target "
          "colour and packaging, and we produce a physical sample in 7 days so you can approve "
          "it before the bulk run.",
    "q3": "What can be customized?",
    "lead3": "All of the following are made to order on this item:",
    "a3f": "Material, size, thickness, colour, logo and packaging are all produced to your "
           "specification — send the spec you want and we build to it.",
    "q4": "Can the size and thickness be changed?",
    "a4": "Standard build is XXSIZEXX, XXTHICKXX thick. Non-standard sizes and thicknesses are "
          "produced to order — send your target specification and we confirm feasibility, "
          "tooling (if any) and the minimum for that build.",
    "a4f": "Standard build is XXSIZEXX. Other sizes and thicknesses are produced to order — send "
           "your target specification and we confirm feasibility and the minimum for that build.",
    "a4g": "Sizes, thicknesses and colours are all produced to order on this item — send your "
           "target specification and we confirm feasibility, tooling (if any) and the minimum "
           "for that build.",
    "q5": "Is it compliant for the US and EU?",
    "a5": "XXNAMEXX is tested to XXCOMPXX. Test reports and the full documentation pack ship "
          "with the order, so your importer or marketplace has the paperwork on file.",
}

ZH = {
    "title": "XXNAMEXX —— 买家常问",
    "q1": "起订量是多少？",
    "a1": "XXNAMEXX的起订量是 XXMOQXX。按此数量首单即可试市场，Logo、配色与包装可在同一批次完成。",
    "a1f": "XXNAMEXX的起订量按规格与工艺单独核算。告诉我们您的意向数量，我们给出该配置的准确起订量。",
    "q2": "可以用我们自己的品牌生产吗？",
    "a2": "可以 —— OEM 与 ODM 是 XXNAMEXX的默认模式。把 Logo 稿件、目标配色与包装发来，"
          "我们 7 个工作日交付实物样品，确认后再批量生产。",
    "q3": "可以定制哪些内容？",
    "lead3": "本产品的以下内容均可按单定制：",
    "a3f": "材质、尺寸、厚度、配色、Logo 与包装均可按您的规格执行 —— 把想要的规格发来，我们照着做。",
    "q4": "尺寸与厚度可以改吗？",
    "a4": "标准规格为 XXSIZEXX，厚度 XXTHICKXX。非标尺寸与厚度可按单定制 —— 把目标规格发来，"
          "我们确认可行性、是否需要开模，以及该配置的起订量。",
    "a4f": "标准规格为 XXSIZEXX。其他尺寸与厚度可按单定制 —— 把目标规格发来，"
           "我们确认可行性与该配置的起订量。",
    "a4g": "本产品的尺寸、厚度与配色均可按单定制 —— 把目标规格发来，我们确认可行性、"
           "是否需要开模，以及该配置的起订量。",
    "q5": "符合美国与欧盟的合规要求吗？",
    "a5": "XXNAMEXX按 XXCOMPXX 送检。检测报告与完整文件包随货提供，您的进口商或平台可直接归档。",
}

# 字段顺序（A3 里列出的顺序）
FIELDS3 = ["LOGO", "COLORS", "PACKAGING", "MATERIAL"]
