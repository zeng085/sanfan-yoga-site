# -*- coding: utf-8 -*-
"""生成 /pilates/ 独立板块：版块首页 + 8 个器械族页（EN + 中文同页双语）。

数据源
    i18n_build/data/pilates_models.json  型号库（8 族 / 41 行 / 40 编号）
    i18n_build/data/pilates_images.json  型号 → 站内图
页面骨架
    i18n_build/site_templates.py         页头 / 页脚 / CTA（唯一模板源）

与垫类的隔离
    · URL 走 /pilates/，不进 /products/
    · 用 .pl-* 样式的深墨+木色版块卖相
    · 分类条换成器械自己的 8 族 chip（不出现垫类 10 分类）
    · 面包屑指向 /pilates/，与 /products/ 不交叉

⚠️ hreflang 2026-09-15 起声明全部 6 语言 + en + x-default：
   de/ja/ko/fr/it/es 的语言版已建成（9 页 ×6 = 54 页，落在 <lang>/pilates/），
   此前只声明 en + x-default 是因为语言版不存在、声明会指向 404。

用法
    python3 i18n_build/build_pilates_section.py --only index,pilates-reformer
    python3 i18n_build/build_pilates_section.py            # 全部 9 页
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from site_templates import SITE, bi, esc  # noqa: E402

OUTDIR = os.path.join(ROOT, "pilates")
MODELS = os.path.join(HERE, "data", "pilates_models.json")
IMAGES = os.path.join(HERE, "data", "pilates_images.json")

PILATES_URL = SITE + "/pilates/"

# 非英语语言版（<lang>/pilates/ 下的对应页）。切换器与 hreflang 共用一份。
LANGS_META = [("de", "Deutsch"), ("ja", "日本語"), ("ko", "한국어"),
              ("fr", "Français"), ("it", "Italiano"), ("es", "Español")]

# 当前正在渲染的页面文件名（由 build_index / build_family 赋值）。
# 语言版 URL 要跟着它走，所以 header/head 里必须能读到。
CUR_PAGE = "index.html"


def lang_url(lg):
    """本页在某语言下的 URL。

    板块首页落到**目录形式** /de/pilates/，与 canonical 写法一致
    （写 /de/pilates/index.html 会出现同页两种 URL）。
    族页照原名：/de/pilates/pilates-reformer.html
    """
    if CUR_PAGE == "index.html":
        return "/%s/pilates/" % lg
    return "/%s/pilates/%s" % (lg, CUR_PAGE)


def ver():
    m = re.search(r"styles\.css\?v([A-Za-z0-9]+)",
                  open(os.path.join(ROOT, "products", "ym1.html"), encoding="utf-8").read())
    return m.group(1) if m else "20260912g"


VER = ver()

# 型号标签的中文
TAG_ZH = {
    "Value line": "特价款", "Best seller": "爆款", "European geometry": "欧版几何",
    "Piano lacquer": "钢琴烤漆", "FAS grade": "FAS 级", "Full track": "全轨道",
    "Gen 1": "一代", "Gen 2": "二代", "M-series": "M 系列", "Foldable": "可折叠",
    "Compact": "紧凑款", "3-in-1": "三合一", "Imported original": "进口原版",
    "10 tower springs": "10 根高架弹簧", "4 springs": "4 根弹簧",
    "Adjustable rung": "梯级可调", "Dowel included": "含圆木杆",
    "5 pieces": "五件成套", "Rehab bed": "康复床", "Rotator + pulley tower": "回旋仪 + 滑轮塔",
}

NAV_PILATES = """        <div class="nav-drop">
          <a href="/pilates/"%s><span data-i18n="nav.pilates">Pilates</span><span class="nd-caret" aria-hidden="true"></span></a>
          <div class="nav-drop-menu">
%s            <a href="/pilates/" class="nd-all" data-i18n="nav.pl.all">All Pilates apparatus</a>
          </div>
        </div>
"""


def nav(active_family=None, active_index=False):
    """导航文案走 data-i18n（main.js 字典），与全站注入的标记保持一模一样。
    别用 bi() 的 lang span：nav 里 .lang-zh 会拿到 display:block 而打散行。"""
    fams = []
    for f in DATA["families"]:
        cur = ""
        if f["key"] == active_family:
            cur = ""
        fams.append('            <a href="/pilates/%s.html"%s data-i18n="nav.pl.%s">%s</a>\n'
                    % (f["key"], cur, f["key"].replace("pilates-", ""), f["en"]))
    drop = NAV_PILATES % (
        ' aria-current="page"' if (active_family or active_index) else "",
        "".join(fams))
    return """  <header class="site-header">
    <div class="container nav">
      <a href="/" class="nav-brand"><img src="%(pf)sassets/img/logo.webp" width="500" height="500" alt="SANFAN" /><span>SAN<span class="accent">FAN</span></span></a>
      <nav class="nav-links">
        <a href="/" data-i18n="nav.home">Home</a>
%(drop)s        <a href="/products.html" data-i18n="nav.products">Products</a>
        <a href="/about.html" data-i18n="nav.about">About</a>
        <a href="/faq.html" data-i18n="nav.faq">FAQ</a>
        <a href="/blog.html" data-i18n="nav.blog">Blog</a>
        <a href="/contact.html" data-i18n="nav.contact">Contact</a>
      </nav>
      <div class="nav-actions"><div class="lang-switch"><button type="button" class="lang-current" aria-haspopup="true" aria-expanded="false"><span class="lang-cur-txt">EN</span><span class="lang-caret">&#9662;</span></button><div class="lang-menu"><button type="button" data-setlang="en" title="English" class="active">EN</button><button type="button" data-setlang="zh" title="中文">中文</button>%(langs)s</div></div>
        <a href="/contact.html" class="btn btn-primary" data-i18n="nav.quote">Get a Quote</a>
      </div>
      <button class="menu-toggle" aria-label="menu">☰</button>
    </div>
  </header>
""" % {"pf": "../",
       "drop": drop,
       # 语言版已建成（54 页），切换器直接指本页对应的语言版：
       # 族页 → /de/pilates/pilates-reformer.html，首页 → /de/pilates/
       "langs": "".join('<a href="%s" hreflang="%s" title="%s">%s</a>'
                        % (lang_url(l), l, t, l.upper())
                        for l, t in LANGS_META)}


def head(title, desc, url, og_img, jsonld):
    """声明 en + 6 语言 + x-default（语言版 54 页已建成，声明是实链接）。"""
    hl = "\n".join('  <link rel="alternate" hreflang="%s" href="%s" />' % (l, lang_url(l))
                   for l, _ in LANGS_META)
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>%s</title>
  <meta name="description" content="%s" />
  <link rel="canonical" href="%s" />
  <link rel="alternate" hreflang="en" href="%s" />
%s
  <link rel="alternate" hreflang="x-default" href="%s" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="%s" />
  <meta property="og:description" content="%s" />
  <meta property="og:image" content="%s" />
  <meta property="og:url" content="%s" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="%s" />
  <meta name="twitter:description" content="%s" />
  <meta name="twitter:image" content="%s" />
  <link rel="stylesheet" href="../assets/css/styles.css?v%s" />
  <link rel="icon" href="../assets/img/logo.webp" />
  <script type="application/ld+json">
%s
  </script>
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
""" % (esc(title), esc(desc), url, url, hl, url, esc(title), esc(desc), og_img, url,
       esc(title), esc(desc), og_img, VER, jsonld)


def chip_bar(active_key=None, note=None):
    chips = []
    for f in DATA["families"]:
        act = " pl-chip-active" if f["key"] == active_key else ""
        chips.append('<a href="/pilates/%s.html" class="pl-chip%s">%s</a>'
                     % (f["key"], act, bi(f["en"], f["zh"])))
    out = ('  <div class="pl-bar">\n    <div class="container">\n'
           '      <div class="pl-bar-inner">%s</div>\n' % "".join(chips))
    if note:
        out += '      <p class="pl-bar-note">%s</p>\n' % note
    out += "    </div>\n  </div>\n"
    return out


def cross_band():
    return """  <section class="section">
    <div class="container">
      <div class="pl-cross">
        <span>%s</span>
        <a href="/products.html">%s</a>
      </div>
    </div>
  </section>

""" % (bi("We also manufacture yoga mats, foam rollers and fitness small goods — "
          "147 SKUs on the same factory floor.",
          "我们同时生产瑜伽垫、泡沫轴与健身小件 —— 同一工厂，147 个 SKU。"),
       bi("Browse the mat &amp; fitness range", "看垫类与健身系列") + " &rarr;")


CTA_BAND = """  <section class="section pl-soft">
    <div class="container">
      <div class="cta-band">
        <h2 data-i18n="cta.title">Ready to Build Your Brand?</h2>
        <p data-i18n="cta.sub">Get a tailored quote and free samples today.</p>
        <a href="/contact.html" class="btn btn-light" data-i18n="cta.btn">Contact Our Team</a>
      </div>
    </div>
  </section>

"""


def footer():
    """⚠️ site_templates 的 ver 参数会被直接拼进 `main.js?%(ver)s`，而本站 URL 惯例是
    `?v<号>`（bump_assets_ver.py 只认 `\\?v(...)`）。本脚本的 VER 不含 v，必须补上 ——
    之前直接传 VER 生成了 `main.js?20260915e`，bump 永远匹配不到 → 改了 JS 老访客不更新。"""
    from site_templates import footer as tf
    vv = VER if VER.startswith("v") else "v" + VER
    return tf(prefix="../", ver=vv)


def jsonld_product_family(fam, url, img):
    """器械族页用 Product + ItemList（列出该族全部型号）+ BreadcrumbList。"""
    items = [{"@type": "ListItem", "position": i + 1,
              "name": "%s %s" % (m["code"], m["en"])}
             for i, m in enumerate(fam["models"])]
    return json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "Product",
             "name": fam["en"],
             "description": fam["lead_en"][:300],
             "image": [img] if img else [],
             "brand": {"@type": "Brand", "name": "SANFAN"},
             "category": "Pilates Equipment",
             "url": url,
             "material": sorted({m["wood_en"] for m in fam["models"]}),
             "offers": {"@type": "AggregateOffer", "priceCurrency": "USD",
                        "url": SITE + "/contact.html",
                        "availability": "https://schema.org/InStock",
                        "offerCount": len(fam["models"])}},
            {"@type": "ItemList", "name": fam["en"] + " — model range",
             "numberOfItems": len(items), "itemListElement": items},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2,
                 "name": "Pilates Apparatus", "item": PILATES_URL},
                {"@type": "ListItem", "position": 3, "name": fam["en"], "item": url}]},
        ]}, ensure_ascii=False, indent=2)


def jsonld_index():
    items = [{"@type": "ListItem", "position": i + 1, "name": f["en"],
              "url": PILATES_URL + f["key"] + ".html"}
             for i, f in enumerate(DATA["families"])]
    return json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "CollectionPage", "name": "Pilates Apparatus",
             "description": "OEM/ODM Pilates apparatus manufacturing — reformer, Cadillac, "
                            "Wunda chair, ladder barrel, spine corrector, studio sets.",
             "url": PILATES_URL},
            {"@type": "ItemList", "name": "Pilates apparatus lines",
             "numberOfItems": len(items), "itemListElement": items},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Pilates Apparatus",
                 "item": PILATES_URL}]},
        ]}, ensure_ascii=False, indent=2)


def alias_html(fam):
    """英文站 sanfansport.com 对同一器械用了另一套叫法（Reformer→Core Bed、
    Wunda Chair→Pilates Chair、Cadillac→Cadillac Bed）。主词保留国际通用名（Reformer
    是全球核心搜索词），这里把自家英文站的叫法括注出来，避免两个站看着像两种产品。
    刻意留空：Ladder Barrel —— 英文站写成 "Ladder Bucket" 是误译，不跟着错。"""
    a = fam.get("alias_en")
    if not a:
        return ""
    return ('      <p class="pl-alias">'
            '<span class="lang-en">Also called <strong>%s</strong> in our English catalogue</span>'
            '<span class="lang-zh">英文站也称作 <strong>%s</strong></span></p>\n'
            % (esc(a), esc(a)))


def spring_cell(m):
    """弹簧列。多条时先写「名称 N 根」；来源若各条一致就只在末尾写一次 ——
    旧版每条都带来源，NIX105（核心床6根 + 高架10根）会渲染成重复的
    「国产碳钢弹簧 · 6 根 · 10 根 · 国产碳钢弹簧」。"""
    ss = [s for s in m["springs"] if s["count"] or s["source_en"]]
    if not ss:
        return '<span class="lang-en">—</span><span class="lang-zh">—</span>'
    multi = len(ss) > 1
    srcs = [s["source_zh"] for s in ss]
    common = srcs[0] if srcs and srcs[0] and all(x == srcs[0] for x in srcs) else None
    parts = []
    for s in ss:
        seg = ""
        if s["count"]:
            if multi and s.get("name_en"):
                seg += ('<span class="lang-en">%s</span><span class="lang-zh">%s</span> · '
                        % (esc(s["name_en"]), esc(s["name_zh"])))
            seg += ('<span class="lang-en">%d springs</span><span class="lang-zh">%d 根</span>'
                    % (s["count"], s["count"]))
        if s["source_en"] and not common:
            seg += ((" · " if seg else "") +
                    '<span class="lang-en">%s</span><span class="lang-zh">%s</span>'
                    % (esc(s["source_en"]), esc(s["source_zh"] or "")))
        if seg:
            parts.append(seg)
    if common:
        src_en = next(s["source_en"] for s in ss if s["source_zh"] == common)
        parts.append('<span class="lang-en">%s</span><span class="lang-zh">%s</span>'
                     % (esc(src_en or ""), esc(common)))
    return " · ".join(parts)


def size_cell(m):
    if m["components"]:
        return "<br>".join(
            '<span class="lang-en">%s %s</span><span class="lang-zh">%s %s</span>'
            % (esc(c["en"]), esc(c["size"]), esc(c["zh"]), esc(c["size"]))
            for c in m["components"])
    return '<span class="lang-en">%s</span><span class="lang-zh">%s</span>' \
           % (esc(m["size_en"] or "—"), esc(m["size_zh"] or "—"))


def spec_table(fam):
    rows = []
    for m in fam["models"]:
        tag = m["tag_en"]
        tagzh = TAG_ZH.get(tag, tag)
        rows.append(
            '        <tr>\n'
            '          <td class="model">%s</td>\n'
            '          <td class="code">%s%s</td>\n'
            '          <td>%s</td>\n'
            '          <td class="size">%s</td>\n'
            '          <td>%s</td>\n'
            '          <td class="note">%s</td>\n'
            '        </tr>' % (
                bi(m["en"], m["zh"]),
                m["code"],
                (" / " + m["variant"]) if m["variant"] else "",
                bi(m["wood_en"], m["wood_zh"]),
                size_cell(m),
                spring_cell(m),
                bi(tag, tagzh) if tag else ""))
    return """      <div class="pl-spec-wrap">
      <table class="pl-spec">
        <thead>
          <tr>
            <th>%s</th><th>%s</th><th>%s</th><th>%s</th><th>%s</th><th>%s</th>
          </tr>
        </thead>
        <tbody>
%s
        </tbody>
      </table>
      </div>
""" % (bi("Model", "型号"), bi("Code", "编号"), bi("Frame / timber", "床架 / 木种"),
       bi("Size", "尺寸"), bi("Springs", "弹簧"), bi("Positioning", "定位"),
       "\n".join(rows))


CUSTOM = {
    "h_en": "What can be customized",
    "h_zh": "可以定制什么",
    "items": [
        ("Timber &amp; finish", "木种与表面",
         "Domestic or imported rubberwood, FAS-grade white maple, piano lacquer, "
         "Croatian beech, aluminium or 316 steel.",
         "国产或进口橡胶木、FAS 级白枫木、钢琴烤漆、克罗地亚榉木、铝合金或 316 钢。"),
        ("Upholstery", "皮革与坐垫",
         "Microfibre, thickened PU, eco silicone leather or PU leather, with "
         "polyurethane foam. Any Pantone colour.",
         "超纤皮革、加厚 PU、生态硅胶皮革或 PU 皮革，配聚氨酯海绵。颜色可按潘通色卡定制。"),
        ("Springs", "弹簧",
         "German Wagner springs, German piano-wire springs, Korean Sangbo steel or "
         "domestic carbon steel — set per model and resistance profile.",
         "德国瓦格纳弹簧、德国琴钢丝弹簧、韩国象牌钢或国产碳钢弹簧，按型号与阻力谱配比。"),
        ("Hardware &amp; rails", "五金与轨道",
         "Stainless-steel rails, hardware and tube; silent frosted rollers with sealed "
         "bearings; 3-position spring bars.",
         "不锈钢轨道、五金件与钢管；静音磨砂滑轮配内置轴承；三档挂簧板。"),
        ("Branding", "品牌要素",
         "Laser-engraved or branded plate on the frame, woven label on the upholstery, "
         "custom crate printing.",
         "床架可激光雕刻或做品牌铭牌，坐垫可缝织标，木箱可印定制标识。"),
        ("Packaging", "包装",
         "Individual wooden crate (or carton for the foldable and aluminium lines), "
         "FBA-ready labelling on request.",
         "整机木箱独立包装（折叠款与铝合金款走纸箱），可按需做 FBA 标签。"),
    ],
}


def custom_block():
    lis_en = "".join("<li><strong>%s</strong> — %s</li>" % (a, c)
                     for a, b, c, d in CUSTOM["items"])
    lis_zh = "".join("<li><strong>%s</strong> — %s</li>" % (b, d)
                     for a, b, c, d in CUSTOM["items"])
    return """  <section class="section">
    <div class="container">
      <div class="section-head">
        <div class="eyebrow" data-i18n="pd.brand">OEM / ODM</div>
        <h2>%s</h2>
      </div>
      <div class="pd-lang-cols">
        <div class="lang-en"><ul class="pd-custom-list">%s</ul></div>
        <div class="lang-zh"><ul class="pd-custom-list">%s</ul></div>
      </div>
    </div>
  </section>

""" % (bi(CUSTOM["h_en"], CUSTOM["h_zh"]), lis_en, lis_zh)


APPLY = {
    "h_en": "Who buys these",
    "h_zh": "谁在采购",
    "items": [
        ("Pilates studios &amp; boutique gyms", "普拉提馆与精品健身工作室",
         "Opening or expanding a studio: matched 5-piece sets on one order and one freight.",
         "开馆或扩店：五件套一次配齐，一票运费。"),
        ("Distributors &amp; importers", "器械经销商与进口商",
         "Container-load programmes with your own model numbering and spec sheet.",
         "整柜项目，可用你自己的型号编号与规格书。"),
        ("Apparatus brands", "器械品牌方",
         "Private-label manufacturing: your logo on the frame, your colour and leather spec.",
         "贴牌生产：床架打你的 Logo，颜色与皮革按你的规格。"),
        ("Rehab &amp; physio clinics", "康复与理疗机构",
         "Ladder barrel, spine corrector and the bidirectional ladder bed for clinical use.",
         "梯桶、矫正器与双向梯床，面向临床康复场景。"),
        ("Hotels, resorts &amp; spas", "酒店、度假村与水疗",
         "Compact aluminium and foldable lines for space-constrained wellness rooms.",
         "紧凑铝合金与折叠款，适配面积有限的康体空间。"),
        ("Online &amp; DTC sellers", "线上与 DTC 卖家",
         "FBA-ready crating and labelling for home-use reformer and foldable SKUs.",
         "家用核心床与折叠款可做 FBA 包装与标签。"),
    ],
}


def apply_block():
    cards = "".join(
        '<div class="pl-card" style="cursor:default"><div class="bd">'
        '<h3>%s</h3><p>%s</p></div></div>' % (bi(a, b), bi(c, d))
        for a, b, c, d in APPLY["items"])
    return """  <section class="section pl-soft">
    <div class="container">
      <div class="section-head">
        <div class="eyebrow" data-i18n="pd.apply">Applications</div>
        <h2>%s</h2>
      </div>
      <div class="pl-grid">%s</div>
    </div>
  </section>

""" % (bi(APPLY["h_en"], APPLY["h_zh"]), cards)


# ------------------------------------------------------------------ 页面
def build_family(fam, imgmap):
    global CUR_PAGE
    CUR_PAGE = fam["key"] + ".html"      # lang_url() 据此拼 /<lang>/pilates/<key>.html
    url = PILATES_URL + fam["key"] + ".html"
    hero_img = imgmap.get(fam["models"][0]["code"])
    og = SITE + "/assets/img/" + (hero_img or "logo.webp")
    title = "%s — OEM/ODM Manufacturer | SANFAN" % fam["en"]
    desc = ("%s made to order: %d models across %s, OEM/ODM with your logo, colour and "
            "timber spec. Request a quote."
            % (fam["en"], len(fam["models"]),
               " / ".join(sorted({m["wood_en"] for m in fam["models"]}))[:140]))
    woods = sorted({m["wood_zh"] for m in fam["models"]})
    tags = "".join('<span class="pl-tag">%s</span>' % bi(t, TAG_ZH.get(t, t))
                   for t in fam["tag_en"].split(" · "))

    body = head(title, desc, url, og, jsonld_product_family(fam, url, og))
    body += nav(active_family=fam["key"])
    body += """  <section class="pl-hero">
    <div class="container pl-hero-inner">
      <nav class="breadcrumb">
        <a href="/">%s</a><span class="bc-sep">/</span>
        <a href="/pilates/">%s</a><span class="bc-sep">/</span>
        <span class="bc-cat">%s</span>
      </nav>
      <div class="pl-eyebrow">%s</div>
      <h1>%s</h1>
%s      <p class="lead">%s</p>
      <div class="pl-hero-cta">
        <a href="/contact.html" class="btn btn-primary">%s</a>
        <a href="/products.html" class="btn btn-ghost">%s</a>
      </div>
    </div>
  </section>

""" % (bi("Home", "首页"), bi("Pilates Apparatus", "普拉提器械"),
       bi(fam["en"], fam["zh"]),
       bi("%d models · %d timber options" % (len(fam["models"]), len(woods)),
          "%d 个型号 · %d 种木种" % (len(fam["models"]), len(woods))),
       bi("%s — %s" % (fam["en"], "OEM/ODM manufacturer"),
          "%s — 源头工厂定制" % fam["zh"]),
       alias_html(fam),
       bi(fam["lead_en"], fam["lead_zh"]),
       bi("Request a quote", "获取报价"),
       bi("See the whole Pilates range", "看全部普拉提器械"))
    body += chip_bar(fam["key"], note=bi(
        "Other ranges on this site: yoga mats, foam rollers, fitness small goods — "
        "kept separate because they ship on a different line.",
        "本站其他品类：瑜伽垫、泡沫轴、健身小件 —— 分开陈列，因为走的是不同产线。"))

    # 图 + 规格表
    body += """  <section class="section">
    <div class="container">
      <div class="pl-block">
        <div class="im"><img src="../assets/img/%s" width="900" height="675" alt="%s" /></div>
        <div>
          <h2>%s</h2>
          <p>%s</p>
          <div>%s</div>
        </div>
      </div>
    </div>
  </section>

""" % (hero_img or "logo.webp", esc(fam["en"]),
       bi("Model range at a glance", "型号一览"),
       bi("Every model below is built to order on the same bench. Compare timber, size, "
          "spring set and positioning, then tell us the code — we quote that model.",
          "下面每个型号都在同一条产线上按单制作。对比木种、尺寸、弹簧配置与定位后，"
          "把编号给我们，我们按该型号报价。"),
       tags)

    body += """  <section class="section pl-soft">
    <div class="container">
      <div class="section-head">
        <div class="eyebrow">%s</div>
        <h2>%s</h2>
        <p>%s</p>
      </div>
%s      <p class="pl-spec-cap">%s</p>
    </div>
  </section>

""" % (bi("Specifications", "规格对比"),
       bi("%d models, compared" % len(fam["models"]), "%d 个型号对比" % len(fam["models"])),
       bi("Prices are quoted per order — agent pricing is not published. Send the codes "
          "you want and we reply with a quote and a sampling plan.",
          "价格按单报价，代理价不上站。把你想要的编号发给我们，我们回复报价与打样方案。"),
       spec_table(fam),
       bi("All models can be customized on timber, upholstery colour, spring source and "
          "packaging. Sizes are the standard build — other dimensions on request.",
          "全部型号均可定制木种、皮革颜色、弹簧来源与包装。表内为标准尺寸，其他尺寸可另议。"))

    body += custom_block()
    body += apply_block()
    body += cross_band()
    body += CTA_BAND
    body += footer()      # footer 自带 main.js 与 </body></html>，勿再补一遍
    return body


def build_index(imgmap):
    global CUR_PAGE
    CUR_PAGE = "index.html"          # lang_url() 据此拼 /<lang>/pilates/
    url = PILATES_URL
    og = SITE + "/assets/img/" + (imgmap.get("NIC102") or "logo.webp")
    total = DATA["total_models"]
    title = "Pilates Apparatus OEM/ODM — Reformer, Cadillac, Chair | SANFAN"
    desc = ("Pilates apparatus built to order: %d models across %d lines — reformer, "
            "Cadillac, Wunda chair, ladder barrel, spine corrector and studio sets. "
            "OEM/ODM with your logo and timber spec."
            % (total, len(DATA["families"])))
    body = head(title, desc, url, og, jsonld_index())
    body += nav(active_index=True)
    body += """  <section class="pl-hero">
    <div class="container pl-hero-inner">
      <nav class="breadcrumb">
        <a href="/">%s</a><span class="bc-sep">/</span>
        <span class="bc-cat">%s</span>
      </nav>
      <div class="pl-eyebrow">%s</div>
      <h1>%s</h1>
      <p class="lead">%s</p>
      <div class="pl-hero-cta">
        <a href="/contact.html" class="btn btn-primary">%s</a>
        <a href="#lines" class="btn btn-ghost">%s</a>
      </div>
      <div class="pl-stats">
        <div class="hs"><div class="num">%d</div><div class="lab">%s</div></div>
        <div class="hs"><div class="num">%d</div><div class="lab">%s</div></div>
        <div class="hs"><div class="num">%d</div><div class="lab">%s</div></div>
        <div class="hs"><div class="num" style="white-space:nowrap">%s</div><div class="lab">%s</div></div>
      </div>
    </div>
  </section>

""" % (bi("Home", "首页"), bi("Pilates Apparatus", "普拉提器械"),
       bi("Pilates Apparatus", "普拉提大器械"),
       bi("Wooden Pilates apparatus, built to order",
          "实木普拉提大器械 · 按单定制"),
       bi("Reformer, Cadillac, Wunda chair, ladder barrel, spine corrector, studio sets "
          "and the special pieces — %d models across %d lines, in imported rubberwood, "
          "FAS-grade white maple, piano lacquer, Croatian beech, aluminium and 316 steel. "
          "Same factory as our yoga mat line, different bench." % (total, len(DATA["families"])),
          "核心床、凯迪拉克、稳踏椅、梯桶、矫正器、五件套与特殊器械 —— %d 个型号、%d 条器械线，"
          "材质覆盖进口橡胶木、FAS 级白枫木、钢琴烤漆、克罗地亚榉木、铝合金与 316 钢。"
          "与瑜伽垫同厂，但走另一条产线。" % (total, len(DATA["families"]))),
       bi("Request a quote", "获取报价"),
       bi("See the 8 lines", "看 8 条器械线"),
       len(DATA["families"]), bi("Equipment lines", "条器械线"),
       total, bi("Models to choose from", "个可选型号"),
       wood_count(), bi("Timber / frame options", "种木材或框架"),
       bi("7 days", "7 天"), bi("Sampling", "打样"))
    body += chip_bar(None, note=bi(
        "This is the apparatus section. Yoga mats, rollers and fitness small goods live "
        "under Products.",
        "这里是器械板块。瑜伽垫、泡沫轴与健身小件在 Products 下。"))

    body += """  <section class="section" id="lines">
    <div class="container">
      <div class="section-head">
        <div class="eyebrow">%s</div>
        <h2>%s</h2>
        <p>%s</p>
      </div>
      <div class="pl-grid">
%s      </div>
    </div>
  </section>

""" % (bi("The lines", "器械线"),
       bi("8 lines, %d models" % total, "8 条器械线 · %d 个型号" % total),
       bi("Pick a line to see every model compared side by side by timber, size, spring "
          "set and positioning — then quote by code.",
          "选一条器械线，逐型号对比木种、尺寸、弹簧配置与定位，然后按编号报价。"),
       "".join(
           '        <a class="pl-card" href="/pilates/%s.html">\n'
           '          <div class="ph"><img src="../assets/img/%s" width="900" height="675" '
           'loading="lazy" alt="%s"></div>\n'
           '          <div class="bd"><h3>%s</h3>%s<div class="cnt">%s</div><p>%s</p></div>\n'
           '        </a>\n' % (
               f["key"], imgmap.get(f["models"][0]["code"], "logo.webp"), esc(f["en"]),
               bi(f["en"], f["zh"]),
               ('<div class="alias">%s</div>'
                % bi("Also called %s" % f["alias_en"], "也叫 %s" % f["alias_en"]))
               if f.get("alias_en") else "",
               bi("%d models · %s" % (len(f["models"]), f["tag_en"]),
                  "%d 个型号 · %s" % (len(f["models"]), f["tag_zh"] or "")),
               bi(f["lead_en"][:180] + "…", f["lead_zh"][:110] + "…"))
           for f in DATA["families"]))

    body += """  <section class="section pl-soft">
    <div class="container">
      <div class="section-head">
        <div class="eyebrow">%s</div>
        <h2>%s</h2>
      </div>
      <div class="pl-block">
        <div class="im"><img src="../assets/img/%s" width="900" height="675" loading="lazy" alt="Pilates apparatus factory" /></div>
        <div>
          <h2>%s</h2>
          <p>%s</p>
          <ul>
            <li>%s</li>
            <li>%s</li>
            <li>%s</li>
            <li>%s</li>
          </ul>
        </div>
      </div>
    </div>
  </section>

""" % (bi("Why us", "为什么是我们"),
       bi("Same factory, second bench", "同一工厂，第二条产线"),
       imgmap.get("NIC301") or "logo.webp",
       bi("We already build mats at volume", "我们本来就是做垫类的"),
       bi("FUJIAN SANFAN has been making yoga and fitness products for over a decade. The "
          "apparatus line grew out of the same timber and upholstery supply chain — so a "
          "studio order and a mat order can be consolidated, and one QC team signs off both.",
          "福建三梵做瑜伽与健身产品已十余年。器械线是从同一套木材与皮革供应链里长出来的 —— "
          "所以开馆订单与垫类订单可以并柜，同一支品控团队签字放行。"),
       bi("Imported rubberwood, FAS-grade white maple, piano lacquer, Croatian beech",
          "进口橡胶木、FAS 级白枫木、钢琴烤漆、克罗地亚榉木"),
       bi("German Wagner / Korean Sangbo / domestic carbon-steel spring options",
          "德国瓦格纳 / 韩国象牌 / 国产碳钢弹簧可选"),
       bi("Stainless-steel rails, sealed-bearing silent rollers, 3-position spring bars",
          "不锈钢轨道、内置轴承静音滑轮、三档挂簧板"),
       bi("Individually crated, FBA-ready labelling on request",
          "整机木箱独立包装，可按需做 FBA 标签"))

    body += cross_band()
    body += CTA_BAND
    body += footer()      # footer 自带 main.js 与 </body></html>，勿再补一遍
    return body


DATA = None


def wood_count():
    """首页 hero 的「木材 / 框架选项」数。与型号库去重口径一致 —— 数字必须实算，
    写死会因为后期加型号而失真（曾写死 5，实际 12）。"""
    return len(set((m.get("wood_en") or "").strip()
                   for f in DATA["families"] for m in f["models"]
                   if (m.get("wood_en") or "").strip()))


def main():
    global DATA
    DATA = json.load(open(MODELS, encoding="utf-8"))
    imgs = json.load(open(IMAGES, encoding="utf-8"))
    imgmap = {}
    for x in imgs:
        key = x["code"] + (("|" + x["variant"]) if x["variant"] else "")
        imgmap[x["code"]] = imgmap.get(x["code"]) or x["file"]
        imgmap[key] = x["file"]

    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))

    os.makedirs(OUTDIR, exist_ok=True)
    written = []
    if not only or "index" in only:
        p = os.path.join(OUTDIR, "index.html")
        open(p, "w", encoding="utf-8").write(build_index(imgmap))
        written.append(p)
    for f in DATA["families"]:
        if only and f["key"] not in only:
            continue
        p = os.path.join(OUTDIR, f["key"] + ".html")
        open(p, "w", encoding="utf-8").write(build_family(f, imgmap))
        written.append(p)

    for p in written:
        print("  %-52s %6.1f KB" % (p.replace(ROOT + "/", ""),
                                    os.path.getsize(p) / 1024))
    print("生成 %d 页" % len(written))

    # GEO 三件套（WebPage dateModified + FAQPage + 可见 FAQ 区块）
    # ⚠️ 本脚本重建页面会覆盖 GEO 内容，故构建后自动重注入（幂等，替换式）。
    # 语言版（<lang>/pilates/）由多语言管线单独产出，重跑后需自行执行：
    #   python3 i18n_build/add_pilates_geo_20260924.py --apply
    import subprocess
    r = subprocess.run([sys.executable, os.path.join(HERE, "add_pilates_geo_20260924.py"),
                        "--langs", "en", "--apply"], cwd=ROOT)
    print("  GEO 重注入退出码：%d" % r.returncode)


if __name__ == "__main__":
    main()
