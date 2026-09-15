# -*- coding: utf-8 -*-
"""
第一批上站：用英文站结构化数据生成 fjsanfan.com 产品页。

产出（默认写入，--dry-run 只打印清单不落盘）：
  1. assets/img/<newslug>-N.webp     从 /tmp/sf_img_stage 复制并改名
  2. products/<newslug>.html         新页（EN 根目录，中文同页切换）
  3. 控制台打印清单，供人工复核

约定（沿用站点既有规范，勿随意改）：
  - 双语用 <span class="lang-en"> / <span class="lang-zh">，语言切换器只留 EN + 中文
    （其他语种页面尚不存在，放链接就是死链）
  - 规格表 10 行顺序：Material/Size/Thickness/Weight/MOQ/Colors/Feature/Logo/Compliance/Packaging
    Weight 无值则整行不出，不编数据
  - MOQ 一律沿用本站原值 100 pcs（英文站无 MOQ 标签）
  - Compliance 固定 ROHS / CE / ISO 9001 / BSCI / REACH
  - 价格只进 JSON-LD 的 AggregateOffer，不出现在可见正文
    区间 = 报价表 FOB × 0.7 ~ × 1.3，币种 USD；报价表无对应行则整块 offers 不输出
"""
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGE = "/tmp/sf_img_stage"
IMGDIR = os.path.join(ROOT, "assets", "img")
CATALOG = os.path.join(ROOT, "outputs", "sf_catalog.json")
PLAN = os.path.join(ROOT, "outputs", "第一批上站清单-2026-09-11.md")

DOMAIN = "https://fjsanfan.com"
CATEGORY = "Yoga Mats"
MOQ = "100 pcs"
CERT = "ROHS / CE / ISO 9001 / BSCI / REACH"
MAX_IMAGES = 8

# 英文站产品已有本站对应页，这一轮不做新页（避免近重复），留待原地更新
# folding-mat 经图片核对＝ym4 同款折叠垫（粉/蓝/绿/紫），清单里「实物是软木」的注记有误
INPLACE = {
    "tpe-yoga-mat": "ym1",
    "folding-mat": "ym4",
    "pu-rubber-yoga-mat": "ym5",
    "matte-pu-rubber-yoga-mat": "ym6",
}

# 英文站自身记录自相矛盾，先挂起等你定，不出页
PARK = {
    "pu-rubber-yoga-mat-test",  # 标题 Camouflage / 材质 TPE / 实物粉白大理石，三者不一致
}

# 材质与清单命名打架时以这里为准
FAMILY_OVERRIDE = {
    "cork-suede-yoga-mat": "suede_cork",
    "oil-painting-style-yoga-mat": "pu",
    "meditation-mat": "meditation",
    "meditation-mat-2": "meditation",
    "pu-meditation-mat": "meditation",
    "tpe-meditation-mat": "meditation",
}

# 命名与材质表冲突时，去掉打架的材质词（不改事实）
TITLE_OVERRIDE = {
    "oil-painting-style-yoga-mat": ("Oil Painting Style Yoga Mat", "油画风瑜伽垫"),
    "suede-tpe-yoga-mat-2": ("Round Mandala Suede TPE Yoga Mat", "圆形曼陀罗绒面 TPE 垫"),
}

# 报价表（yoga and pilate accessories-SANFAN sports.xlsx / offer 页，FOB Xiamen, USD）
# 瑜伽垫类只有 5 行，按材质族归口。值 = 该族基准单价。
PRICE_BY_FAMILY = {
    "pu": 12.15,           # luxury YOGA mat, PU+rubber 1850*680*4.5mm
    "cork_rubber": 10.90,  # cork rubber yoga mat, cork+rubber 185x68x0.4cm
    "tpe": 5.89,           # yoga mat S1A12, TPE double layer 1830*610*6mm
    "pilates": 5.90,       # pilate mat, PU+rubber / cork+rubber 97*57*0.45cm
}

# 逐款覆盖：报价表里有更贴切的行时写在这里
PRICE_OVERRIDE = {
    "pu-rubber-yoga-mat-9": 10.90,  # cork rubber yoga mat，软木面款归到软木+橡胶行
}


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def slugify(s):
    s = s.replace("&", " and ")
    s = re.sub(r"[^0-9A-Za-z]+", "-", s).strip("-").lower()
    s = re.sub(r"-{2,}", "-", s)
    return s


def parse_plan():
    """从清单 markdown 里取出 slug -> 建议英文名/中文名。"""
    md = open(PLAN, encoding="utf-8").read()
    out = {}
    for line in md.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        m = re.match(r"^`([^`]+)`$", cells[1])
        if m:
            out[m.group(1)] = {"en": cells[2], "zh": cells[3]}
    return out


def family_of(mat):
    m = (mat or "").lower()
    if not m:
        return "pilates"
    if "matte pu" in m:
        return "pu"
    if "pu" in m and "rubber" in m:
        return "pu"
    if "cork" in m and "rubber" in m:
        return "cork_rubber"
    if "cork" in m and "tpe" in m:
        return "cork_tpe"
    if "cork" in m:
        return "cork_rubber"
    if "suede" in m and "cork" in m:
        return "suede_cork"
    if "suede" in m and "tpe" in m:
        return "suede_tpe"
    if "suede" in m:
        return "suede"
    if "tpe" in m:
        return "tpe"
    if "natural rubber" in m:
        return "rubber"
    return "pu"


# ---------------------------------------------------------------- 文案族
COPY = {
    "tpe": {
        "desc_en": "Eco TPE {size}, {thk} thick. Double-layer non-slip texture, recyclable, PVC-free and odourless — the workhorse mat for studios, gyms and private-label programmes.",
        "desc_zh": "环保 TPE，{size}，厚度 {thk}。双层防滑纹理，可回收、无 PVC、无异味——瑜伽馆、健身房与贴牌项目的主力款。",
        "ov_en": "Made from double-layer eco TPE that is lightweight, recyclable and free of PVC and toxic odours. Both faces are textured for grip, and the range covers single-colour and dual-colour constructions so a full width and thickness ladder can sit under one brand.",
        "ov_zh": "采用双层环保 TPE，轻便可回收，不含 PVC、无异味。正反双面均有防滑纹理，单色与双色结构齐备，方便在同一品牌下铺齐宽度与厚度全系列。",
        "f_en": ["Eco TPE — no PVC and no odour", "Textured non-slip surface on both faces", "Widths 61–122 cm and thickness 3–20 mm, both customizable"],
        "f_zh": ["环保 TPE，无 PVC、无异味", "正反双面防滑纹理", "宽度 61–122 cm、厚度 3–20 mm 均可定制"],
        "ap_en": "Ideal for yoga studios, gyms, hot-yoga classes, private-label retail and promotional giveaways.",
        "ap_zh": "适用于瑜伽馆、健身房、高温瑜伽课程、贴牌零售与赠品促销。",
    },
    "pu": {
        "desc_en": "PU anti-slip top laminated to a natural rubber base, {size}, {thk} thick. The premium grip specification for hot yoga and studio use.",
        "desc_zh": "PU 防滑面复合天然橡胶底，{size}，厚度 {thk}。高温瑜伽与瑜伽馆场景的高端抓地规格。",
        "ov_en": "A PU surface layer bonded to a natural rubber base — the combination behind high sweat absorption and a stable, non-slip ride. It is the flagship mat of most studio and premium retail lines, and takes printed, embossed or solid finishes.",
        "ov_zh": "PU 面层复合天然橡胶底，兼顾高吸汗与稳定防滑，是瑜伽馆及高端零售线最常见的旗舰垫规格，可做印花、压纹或纯色面。",
        "f_en": ["PU top layer over a natural rubber base", "High sweat absorption — grip improves when damp", "Printed, embossed and solid-colour finishes available"],
        "f_zh": ["PU 面层 + 天然橡胶底", "吸汗性强，微湿状态下抓地更稳", "可做印花、压纹或纯色面"],
        "ap_en": "Built for hot yoga, vinyasa studios, premium retail lines and hotel or gym fit-outs.",
        "ap_zh": "适合高温瑜伽、流瑜伽馆、高端零售线，以及酒店与健身房的配套采购。",
    },
    "cork_rubber": {
        "desc_en": "Natural cork surface over a rubber base, {size}, {thk} thick. Grip increases as the cork gets damp, and the surface is naturally antimicrobial.",
        "desc_zh": "天然软木面复合橡胶底，{size}，厚度 {thk}。软木遇汗抓地更强，表面天然抑菌。",
        "ov_en": "A natural cork veneer bonded to a rubber base. Cork grips better the damper it gets, so it suits hot and sweaty practice, and it carries no plastic feel — the finish most often asked for by sustainability-led brands.",
        "ov_zh": "天然软木面层复合橡胶底。软木遇汗越湿越涩，适合高温出汗的练习场景，且没有塑料触感，是主打可持续定位的品牌最常点的面料。",
        "f_en": ["Natural cork surface — naturally antimicrobial", "Grip improves with moisture", "Rubber base keeps it flat and stable"],
        "f_zh": ["天然软木面，天然抑菌", "遇湿抓地更强", "橡胶底保证平整稳定"],
        "ap_en": "Suited to hot yoga, wellness and eco-positioned brands, and studio fit-outs.",
        "ap_zh": "适合高温瑜伽、健康与环保定位品牌，以及瑜伽馆配套采购。",
    },
    "cork_tpe": {
        "desc_en": "Natural cork surface over a TPE base, {size}, {thk} thick — a lighter cork option without the rubber weight.",
        "desc_zh": "天然软木面复合 TPE 底，{size}，厚度 {thk}——比橡胶底更轻的软木方案。",
        "ov_en": "Cork veneer on a TPE base: the grip and natural feel of cork, with a lighter mat underneath and no rubber smell. A good fit where shipping weight matters.",
        "ov_zh": "软木面复合 TPE 底：保留软木的抓地与天然触感，同时垫体更轻、无橡胶味。运费敏感的项目适合选它。",
        "f_en": ["Cork surface, TPE base — lighter than rubber", "Low odour, no plastic feel", "Naturally antimicrobial surface"],
        "f_zh": ["软木面 + TPE 底，比橡胶底更轻", "低气味，无塑料触感", "表面天然抑菌"],
        "ap_en": "For eco brands, light-travel lines, hot yoga and wellness programmes.",
        "ap_zh": "适合环保品牌、轻量出行产品线、高温瑜伽及健康类项目。",
    },
    "suede": {
        "desc_en": "Microfibre suede top with a {base} backing, {size}, {thk} thick. Soft to the touch and the best surface for full-bleed custom printing.",
        "desc_zh": "超细纤维绒面面层复合{base}底，{size}，厚度 {thk}。触感柔软，是全幅定制印花最合适的面料。",
        "ov_en": "A microfibre suede face over a {base} base. Suede takes edge-to-edge digital printing with no visible pattern seam, which makes it the standard choice for licensed artwork, seasonal collections and gift lines.",
        "ov_zh": "超细纤维绒面复合{base}底。绒面可整幅数码印花、无图案接缝，是做授权图案、季节系列与礼赠线最常用的面料。",
        "f_en": ["Microfibre suede face — soft, no plastic feel", "Full-bleed custom printing with no visible seam", "Wipe-clean and colourfast"],
        "f_zh": ["超细纤维绒面，柔软无塑料感", "整幅定制印花，无可见接缝", "可擦拭清洁，色牢度好"],
        "ap_en": "Ideal for licensed art, seasonal print collections, yoga studios and gift retail.",
        "ap_zh": "适合授权图案、季节印花系列、瑜伽馆及礼赠零售。",
    },
    "rubber": {
        "desc_en": "Natural rubber construction, {size}, {thk} thick. Dense, stable and built for repeated daily use.",
        "desc_zh": "天然橡胶结构，{size}，厚度 {thk}。密实稳定，经得起每日高频使用。",
        "ov_en": "A dense natural rubber build with no foam layer to compress. It stays flat on the floor, resists edge curl and takes repeated daily studio use.",
        "ov_zh": "密实天然橡胶结构，无泡棉压缩层。铺地平整、不易卷边，适合瑜伽馆每日高频使用。",
        "f_en": ["Dense natural rubber, no foam layer", "Stays flat, resists edge curl", "Built for daily studio use"],
        "f_zh": ["密实天然橡胶，无泡棉层", "铺地平整，不易卷边", "耐得住每日高频使用"],
        "ap_en": "For gyms, studios and heavy-duty daily programmes.",
        "ap_zh": "适合健身房、瑜伽馆及高频日常使用场景。",
    },
    "pilates": {
        "desc_en": "Custom-fit mat for Pilates reformers and apparatus, {size}. Cut and printed to your machine and brand.",
        "desc_zh": "适配普拉提器械的定制垫，{size}。按你的器械尺寸与品牌做裁切与印刷。",
        "ov_en": "A custom-cut mat for Pilates reformer and apparatus seating. We cut to your machine template and print or emboss your mark, so the mat can ship as part of a branded studio package.",
        "ov_zh": "为普拉提器械座椅定制的裁切垫。按你的器械模板裁切，可印花或压印品牌标识，适合作为品牌化工作室套装一起出货。",
        "f_en": ["Cut to your machine template", "Printed or embossed logo", "Wipe-clean, non-slip surface"],
        "f_zh": ["按器械模板定制裁切", "可印花或压印 logo", "表面防滑、易擦拭"],
        "ap_en": "For Pilates studios, reformer manufacturers and studio equipment distributors.",
        "ap_zh": "适合普拉提馆、器械厂商与器械经销商的配套采购。",
    },
    "meditation": {
        "desc_en": "Compact meditation and mindfulness mat, {size}, {thk} thick. Sized for seated practice, cushioning the knees and ankles in sukhasana.",
        "desc_zh": "冥想与正念练习用的小尺寸垫，{size}，厚度 {thk}。按坐姿练习规格开发，护膝护踝。",
        "ov_en": "A compact mat built for seated practice rather than a full-length flow. The smaller footprint makes it easy to carry to class, and it doubles as a kneeling or cushioning mat around the home and studio.",
        "ov_zh": "为坐姿练习而非全套流动序列开发的小尺寸垫。占地小、便于随身携带，也可作居家与馆内的跪姿垫、铺垫使用。",
        "f_en": ["Sized for seated meditation practice", "Compact and easy to carry to class", "Printed or plain surface, logo on request"],
        "f_zh": ["按坐姿冥想练习规格开发", "尺寸紧凑，便于随身携带", "可印花或纯色，支持加印 logo"],
        "ap_en": "For meditation studios, wellness brands, retreat kits and gift retail.",
        "ap_zh": "适合冥想馆、健康品牌、静修套装与礼赠零售。",
    },
}

BASE_LABEL = {
    "suede": "rubber or TPE",
    "suede_tpe": "TPE",
    "suede_cork": "cork",
}


def copy_for(fam, base_target=None):
    key = fam
    if fam in ("suede_tpe", "suede_cork"):
        key = "suede"
    if fam not in COPY:
        key = "pu"
    return COPY[key]


def is_full_size(size):
    """判断是否常规整垫尺寸（>=150cm）。小件（冥想垫 40x60、圆垫 68cm）不该套整垫报价。"""
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", size or "")]
    nums = [n for n in nums if n > 3]
    return (max(nums) if nums else 0) >= 150


def human_size(s):
    """把 183x66cm 之类写得更规整一点；原值照抄优先。"""
    s = (s or "").strip()
    return s or "made to order"


def clean_thk(specs):
    t = (specs.get("Thickness") or "").strip()
    t = t.replace(" or Customized", ", customizable").replace("or Customized", "customizable")
    if t:
        return t
    size = specs.get("Size") or ""
    m = re.search(r"(\d+(?:\.\d+)?)\s*mm", size, re.I)
    return f"{m.group(1)} mm" if m else "customizable"


# ---------------------------------------------------------------- 页面骨架
HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>@@TITLE@@ — SANFAN Yoga &amp; Fitness Manufacturer</title>
  <meta name="description" content="@@DESC@@" />
  <link rel="canonical" href="@@URL@@" />
  <link rel="alternate" hreflang="en" href="@@URL@@" />
  <link rel="alternate" hreflang="x-default" href="@@URL@@" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="@@TITLE@@ — SANFAN" />
  <meta property="og:description" content="@@DESC@@" />
  <meta property="og:image" content="@@OGIMG@@" />
  <meta property="og:url" content="@@URL@@" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="@@TITLE@@ — SANFAN" />
  <meta name="twitter:description" content="@@DESC@@" />
  <meta name="twitter:image" content="@@OGIMG@@" />
  <link rel="stylesheet" href="../assets/css/styles.css?v@@VER@@" />
  <link rel="icon" href="../assets/img/logo.webp" />
  <script type="application/ld+json">@@JSONLD@@</script>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-RMSNDR5S06"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-RMSNDR5S06');
</script>
</head>
<body>

  <header class="site-header">
    <div class="container nav">
      <a href="/" class="nav-brand"><img src="../assets/img/logo.webp" width="500" height="500" alt="SANFAN" /><span>SAN<span class="accent">FAN</span></span></a>
      <nav class="nav-links">
        <a href="/" data-i18n="nav.home">Home</a>
        <a href="../products.html" data-i18n="nav.products">Yoga Mats &amp; Gear</a>
        <a href="../about.html" data-i18n="nav.about">About</a>
        <a href="../faq.html" data-i18n="nav.faq">FAQ</a>
        <a href="../blog.html" data-i18n="nav.blog">Blog</a>
        <a href="../contact.html" data-i18n="nav.contact">Contact</a>
      </nav>
      <div class="nav-actions"><div class="lang-switch"><button type="button" class="lang-current" aria-haspopup="true" aria-expanded="false"><span class="lang-cur-txt">EN</span><span class="lang-caret">&#9662;</span></button><div class="lang-menu"><button type="button" data-setlang="en" title="English" class="active">EN</button><button type="button" data-setlang="zh" title="中文">中文</button></div>
        </div>
        <a href="../contact.html" class="btn btn-primary" data-i18n="nav.quote">Get a Quote</a>
      </div>
      <button class="menu-toggle" aria-label="menu">☰</button>
  </header>

  <section class="hero" style="background:linear-gradient(120deg,var(--brand-ink),var(--brand));">
    <div class="container hero-inner" style="padding:52px 0 30px;">
      <nav class="breadcrumb">
        <a href="../products.html" data-i18n="pd.back">Back to Products</a>
        <span class="bc-sep">/</span>
        <span class="bc-cat"><span class="lang-en">Yoga Mats</span><span class="lang-zh">瑜伽垫</span></span>
      </nav>
      <h1><span class="lang-en">@@TITLE@@ — SANFAN</span><span class="lang-zh">@@TITLEZH@@ — 三梵</span></h1>
    </div>
  </section>

  <section class="section">
    <div class="container product-detail">
      <div class="pd-gallery">
        <div class="pd-main"><img id="pd-main-img" src="../assets/img/@@IMG1@@" width="480" height="480" alt="@@TITLE@@" /></div>
        <div class="pd-thumbs" id="pd-thumbs">
@@THUMBS@@
        </div>
      </div>
      <div class="pd-info">
        <p class="pd-desc"><span class="lang-en">@@DESCEN@@</span><span class="lang-zh">@@DESCZH@@</span></p>
        <div class="pd-actions">
          <a class="btn btn-primary" href="../contact.html" data-i18n="pd.quote">Request a Quote</a>
          <a class="btn btn-ghost" id="pd-wa-en" href="https://wa.me/8615959029082?text=@@WA@@" data-i18n="pd.whatsapp">Chat on WhatsApp</a>
        </div>
        <div class="pd-specs">
          <h3 data-i18n="pd.specs">Specifications</h3>
          <table class="spec-table"><tbody>@@SPECROWS@@</tbody></table>
        </div>
      </div>
    </div>
  </section>

  <section class="section soft">
    <div class="container">
      <div class="section-head">
        <div class="eyebrow" data-i18n="pd.overview">Product Overview</div>
        <h2><span class="lang-en">@@TITLE@@</span><span class="lang-zh">@@TITLEZH@@</span></h2>
      </div>
      <p class="pd-overview"><span class="lang-en">@@OVEN@@</span><span class="lang-zh">@@OVZH@@</span></p>
      <div class="pd-lang-cols">
        <div class="lang-en"><h3 class="pd-features-title" data-i18n="pd.features">Key Features</h3><ul class="pd-features">@@FEN@@</ul></div>
        <div class="lang-zh"><h3 class="pd-features-title">核心特点</h3><ul class="pd-features">@@FZH@@</ul></div>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="container">
      <div class="section-head">
        <div class="eyebrow" data-i18n="pd.brand">Branding</div>
        <h2 data-i18n="pd.custom">Customization &amp; OEM/ODM</h2>
      </div>
      <p class="pd-custom"><span class="lang-en">Full OEM/ODM support: material, size, thickness, colour, dual colour, logo printing, embossing and packaging. Physical samples ready in 7 days against your specification.</span><span class="lang-zh">全面支持 OEM/ODM：材质、尺寸、厚度、颜色、双色、logo 印刷、压印及包装均可定制。7 天按你的规格出实物样品。</span></p>
      <div class="pd-lang-cols">
        <div class="lang-en"><ul class="pd-custom-list"><li><strong>Custom logo printing</strong> — Silk-screen, heat transfer or laser engraving, on the mat or on the packaging.</li><li><strong>Size &amp; thickness</strong> — Made to your spec; length, width and thickness all adjustable.</li><li><strong>Colour &amp; material</strong> — Pantone colour matching across TPE, PU/rubber, cork and suede.</li><li><strong>Packaging</strong> — Custom inner box, carton, barcode and hang-tag for retail-ready shipping.</li></ul></div>
        <div class="lang-zh"><ul class="pd-custom-list"><li><strong>定制 logo 印刷</strong> — 丝印、热转印或激光雕刻，可做在垫面或包装上。</li><li><strong>尺寸与厚度</strong> — 按你的规格定制；长度、宽度、厚度均可调。</li><li><strong>颜色与材质</strong> — 潘通色卡配色，覆盖 TPE、PU/橡胶、软木与绒面。</li><li><strong>包装</strong> — 定制内盒、外箱、条码与吊牌，达成零售级出货。</li></ul></div>
      </div>
    </div>
  </section>

  <section class="section soft">
    <div class="container">
      <div class="section-head">
        <div class="eyebrow" data-i18n="pd.apply">Applications</div>
        <h2 data-i18n="pd.apply.t">Where It Is Used</h2>
      </div>
      <p class="pd-overview"><span class="lang-en">@@APEN@@</span><span class="lang-zh">@@APZH@@</span></p>
    </div>
  </section>

  <section class="section soft">
    <div class="container">
      <div class="section-head">
        <h2 data-i18n="pd.related">Related Products</h2>
      </div>
      <div class="prod-grid">@@RELATED@@</div>
    </div>
  </section>

  <section class="section">
    <div class="container">
      <div class="cta-band">
        <h2 data-i18n="cta.title">Ready to Build Your Brand?</h2>
        <p data-i18n="cta.sub">Get a tailored quote and free samples today.</p>
        <a href="../contact.html" class="btn btn-light" data-i18n="cta.btn">Contact Our Team</a>
      </div>
    </div>
  </section>

  <footer class="site-footer">
    <div class="container footer-grid">
      <div>
        <div class="brand"><img src="../assets/img/logo.webp" width="500" height="500" loading="lazy" alt="SANFAN" /> <span>SAN<span style="color:var(--brand-2)">FAN</span></span></div>
        <p style="font-size:14px;max-width:300px" data-i18n="f.tag">OEM / ODM yoga &amp; fitness manufacturer.</p>
      </div>
      <div><h5 data-i18n="foot.products">Products</h5><ul>
        <li><a href="../products.html#yoga" data-i18n="cat.yoga.title">Yoga Mats</a></li>
        <li><a href="../products.html#props" data-i18n="cat.props.title">Yoga Props &amp; Accessories</a></li>
        <li><a href="../products.html#rollers" data-i18n="cat.rollers.title">Foam Rollers &amp; Massage</a></li>
        <li><a href="../products.html#bands" data-i18n="cat.bands.title">Resistance Bands &amp; Pilates</a></li>
        <li><a href="../products.html#fitness" data-i18n="cat.fit.title">Fitness Equipment</a></li>
      </ul></div>
      <div><h5 data-i18n="foot.company">Company</h5><ul>
        <li><a href="../about.html" data-i18n="nav.about">About</a></li>
        <li><a href="../about.html" data-i18n="process.title">Production Process</a></li>
        <li><a href="../contact.html" data-i18n="nav.contact">Contact</a></li>
      </ul></div>
      <div><h5 data-i18n="foot.contact">Contact</h5>
        <div class="contact-line"><span data-i18n="foot.addr">Address</span>: No. 8 Haiguang Road, Yuejin Industrial Zone, Xibin Town, Jinjiang, Quanzhou, Fujian, China</div>
        <div class="contact-line"><span data-i18n="foot.email">Email</span>: <a class="c-link" href="mailto:zenglinggun@gmail.com">zenglinggun@gmail.com</a></div>
        <div class="contact-line"><span data-i18n="foot.phone">WhatsApp</span>: <a class="c-link" href="https://wa.me/8615959029082" target="_blank" rel="noopener">+86 15959029082</a></div>
      </div>
    </div>
    <div class="container footer-bottom" data-i18n="foot.copyright">© 2026 FUJIAN SANFAN Sports Products Co., Ltd. All rights reserved.</div>
  </footer>

  <script src="../assets/js/main.js?v@@VER@@"></script>
  <script>
    (function () {
      var thumbs = document.getElementById('pd-thumbs');
      var main = document.getElementById('pd-main-img');
      if (thumbs && main) {
        thumbs.addEventListener('click', function (e) {
          var btn = e.target.closest('.pd-thumb');
          if (!btn) return;
          var img = btn.querySelector('img');
          main.src = img.getAttribute('src');
          main.alt = img.getAttribute('alt');
          thumbs.querySelectorAll('.pd-thumb').forEach(function (x) { x.classList.remove('active'); });
          btn.classList.add('active');
        });
      }
      function syncWa() {
        var zh = document.documentElement.classList.contains('show-zh');
        var a = document.getElementById('pd-wa-en');
        if (a) a.href = zh ? "@@WAZH@@" : "@@WAEN@@";
      }
      syncWa();
      document.addEventListener('sanfan-langchange', syncWa);
    })();
  </script>
</body>
</html>
"""


def build_head_jsonld(p, title, desc, url, imgs, base_price):
    g = [{
        "@type": "Product",
        "name": title,
        "description": desc,
        "image": imgs,
        "brand": {"@type": "Brand", "name": "SANFAN"},
        "category": CATEGORY,
        "url": url,
    }]
    if base_price:
        lo = round(base_price * 0.7, 2)
        hi = round(base_price * 1.3, 2)
        g[0]["offers"] = {
            "@type": "AggregateOffer",
            "lowPrice": lo,
            "highPrice": hi,
            "priceCurrency": "USD",
            "url": DOMAIN + "/contact.html",
        }
    g.append({
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": DOMAIN + "/"},
            {"@type": "ListItem", "position": 2, "name": "Products", "item": DOMAIN + "/products.html"},
            {"@type": "ListItem", "position": 3, "name": "Yoga Mats", "item": DOMAIN + "/products.html#yoga"},
            {"@type": "ListItem", "position": 4, "name": title, "item": url},
        ],
    })
    return json.dumps({"@context": "https://schema.org", "@graph": g}, ensure_ascii=False, indent=2)


def spec_rows(specs, fam):
    order = [("Material", specs.get("Material")),
             ("Size", specs.get("Size")),
             ("Thickness", clean_thk(specs)),
             ("Weight", specs.get("Weight")),
             ("MOQ", MOQ),
             ("Colors", specs.get("Colors")),
             ("Feature", specs.get("Feature")),
             ("Logo", specs.get("Logo")),
             ("Compliance", CERT),
             ("Packaging", specs.get("Packaging"))]
    zh = {"Material": "材质", "Size": "尺寸", "Thickness": "厚度", "Weight": "重量", "MOQ": "起订量",
          "Colors": "颜色与印花", "Feature": "特性", "Logo": "定制标识", "Compliance": "合规认证", "Packaging": "包装"}
    out = []
    for k, v in order:
        v = (v or "").strip()
        if not v:
            continue
        out.append(
            '<tr><th><span class="lang-en">' + k + '</span><span class="lang-zh">' + zh[k] +
            '</span></th><td>' + esc(v) + '</td></tr>'
        )
    return "".join(out)


def main():
    dry = "--dry-run" in sys.argv
    # 站点写法是 ?v20260909c（没有等号），正则必须按这个形状取，否则会回落成 ?vv...
    ver = "20260909c"
    m = re.search(r"styles\.css\?v([A-Za-z0-9]+)",
                  open(os.path.join(ROOT, "products", "ym1.html"), encoding="utf-8").read())
    if m:
        ver = m.group(1)

    plan = parse_plan()
    cat = {p["slug"]: p for p in json.load(open(CATALOG, encoding="utf-8"))}

    items = []
    for slug, p in cat.items():
        if slug in INPLACE or slug in PARK:
            continue
        if slug not in plan:
            print("  [skip] 清单无命名:", slug)
            continue
        fam = FAMILY_OVERRIDE.get(slug) or family_of(p["specs"].get("Material"))
        base = PRICE_OVERRIDE.get(slug, PRICE_BY_FAMILY.get(fam))
        if base and fam != "pilates" and not is_full_size(p["specs"].get("Size")):
            base = None
        t_en, t_zh = TITLE_OVERRIDE.get(slug, (plan[slug]["en"], plan[slug]["zh"]))
        items.append({
            "src": slug,
            "new": slugify(t_en),
            "title_en": t_en,
            "title_zh": t_zh,
            "fam": fam,
            "base": base,
            "specs": p["specs"],
            "imgs": p["images"],
        })

    # slug 唯一性
    seen = {}
    for it in items:
        if it["new"] in seen:
            print("  [冲突] %s ← %s / %s" % (it["new"], seen[it["new"]], it["src"]))
        seen[it["new"]] = it["src"]

    print("待生成新页：%d 个（跳过已有对应页 %d 个）" % (len(items), len(INPLACE)))
    priced = [i for i in items if i["base"]]
    print("其中带报价区间：%d 个；无报价：%d 个" % (len(priced), len(items) - len(priced)))
    if dry:
        for i in items:
            print("  %-52s <- %-40s %-12s %s" % (i["new"], i["src"], i["fam"], i["base"] or "-"))
        return

    by_fam = {}
    for it in items:
        by_fam.setdefault(it["fam"], []).append(it)

    idmap = {}
    ok_img = 0
    for it in items:
        srcs = []
        for n, u in enumerate(it["imgs"][:MAX_IMAGES], 1):
            s = os.path.join(STAGE, "%s-%d.webp" % (it["src"], n))
            if os.path.exists(s):
                srcs.append(s)
        if not srcs:
            print("  [无图]", it["src"])
        names = []
        for n, s in enumerate(srcs, 1):
            d = "%s-%d.webp" % (it["new"], n)
            shutil.copyfile(s, os.path.join(IMGDIR, d))
            names.append(d)
            ok_img += 1
        idmap[it["src"]] = names

    print("复制图片：%d 张 -> assets/img/" % ok_img)

    written = 0
    for it in items:
        names = idmap.get(it["src"]) or []
        if not names:
            continue
        fam, specs = it["fam"], it["specs"]
        cp = copy_for(fam)
        base_label = BASE_LABEL.get(fam, "rubber")
        size = human_size(specs.get("Size"))
        thk = clean_thk(specs)
        fill = {"size": size, "thk": thk, "base": base_label, "mat": specs.get("Material", "")}

        desc_en = cp["desc_en"].format(**fill)
        desc_zh = cp["desc_zh"].format(**fill)
        ov_en = cp["ov_en"].format(**fill)
        ov_zh = cp["ov_zh"].format(**fill)
        f_en = "".join("<li>" + esc(esc(b)) + "</li>" for b in cp["f_en"])
        f_zh = "".join("<li>" + esc(b) + "</li>" for b in cp["f_zh"])
        ap_en = cp["ap_en"].format(**fill)
        ap_zh = cp["ap_zh"].format(**fill)

        url = "%s/products/%s.html" % (DOMAIN, it["new"])
        meta_desc = desc_en[:300]

        thumbs = []
        for n, nm in enumerate(names):
            cls = "pd-thumb active" if n == 0 else "pd-thumb"
            thumbs.append('<button type="button" class="%s"><img src="../assets/img/%s" width="480" height="480" loading="lazy" alt="%s"></button>'
                          % (cls, nm, esc(it["title_en"])))

        # 相关产品：同材质族优先，取 4 个
        pool = [x for x in by_fam.get(fam, []) if x["src"] != it["src"]]
        if len(pool) < 4:
            pool += [x for x in items if x["src"] != it["src"] and x not in pool]
        rel = []
        for r in pool[:4]:
            rn = idmap.get(r["src"]) or []
            if not rn:
                continue
            rel.append(
                '<a class="prod-card" href="../products/%s.html"><div class="ph"><img src="../assets/img/%s" width="480" height="480" loading="lazy" alt="%s"></div>'
                '<div class="info"><h4><span class="lang-en">%s</span><span class="lang-zh">%s</span></h4>'
                '<p><span class="lang-en">%s</span><span class="lang-zh">%s</span></p></div></a>'
                % (r["new"], rn[0], esc(r["title_en"]), esc(r["title_en"]), esc(r["title_zh"]),
                   esc(r["specs"].get("Material", "") + " · " + (r["specs"].get("Size") or "")),
                   esc((r["specs"].get("Material", "") + " · " + (r["specs"].get("Size") or ""))))
            )

        wa_en = ("Hi%20SANFAN%2C%20I%20am%20interested%20in%20" +
                 it["title_en"].replace(" ", "%20").replace("&", "%26").replace("/", "%2F"))
        wa_zh = ("%E4%BD%A0%E5%A5%BD%E4%B8%89%E6%A2%B5%EF%BC%8C%E6%88%91%E6%83%B3%E4%BA%86%E8%A7%A3%20" +
                 it["title_zh"].replace(" ", "%20"))

        html = HEAD
        for k, v in [
            ("@@VER@@", ver),
            ("@@TITLEZH@@", esc(it["title_zh"])),
            ("@@TITLE@@", esc(it["title_en"])),
            ("@@DESC@@", esc(meta_desc)),
            ("@@URL@@", url),
            ("@@OGIMG@@", DOMAIN + "/assets/img/" + names[0]),
            ("@@JSONLD@@", build_head_jsonld(it, it["title_en"], desc_en, url,
                                             [DOMAIN + "/assets/img/" + n for n in names], it["base"])),
            ("@@IMG1@@", names[0]),
            ("@@THUMBS@@", "\n          ".join(thumbs)),
            ("@@DESCEN@@", esc(desc_en)),
            ("@@DESCZH@@", esc(desc_zh)),
            ("@@WA@@", wa_en),
            ("@@WAEN@@", wa_en),
            ("@@WAZH@@", wa_zh),
            ("@@SPECROWS@@", spec_rows(specs, fam)),
            ("@@OVEN@@", esc(ov_en)),
            ("@@OVZH@@", esc(ov_zh)),
            ("@@FEN@@", f_en),
            ("@@FZH@@", f_zh),
            ("@@APEN@@", esc(ap_en)),
            ("@@APZH@@", esc(ap_zh)),
            ("@@RELATED@@", "".join(rel)),
        ]:
            html = html.replace(k, v)

        with open(os.path.join(ROOT, "products", it["new"] + ".html"), "w", encoding="utf-8") as fh:
            fh.write(html)
        written += 1

    print("写出页面：%d 个" % written)
    with open(os.path.join(ROOT, "outputs", "batch1_pages.json"), "w", encoding="utf-8") as fh:
        json.dump(items, fh, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
