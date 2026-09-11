# -*- coding: utf-8 -*-
"""
把 117 个产品的平铺列表页，拆成 8 个分类页 + 1 个分类总览页。

产出（全部在站点根目录，与 products.html 同级，相对路径基准一致）：
    <cat-key>.html   × 8    分类落地页（该类全部产品卡）
    products.html            重写为「分类总览」（8 个分类大格 + 每格 6 个产品缩略图）

用法
    python3 i18n_build/build_category_pages.py --dry-run
    python3 i18n_build/build_category_pages.py
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from category_map import CATS, CAT_BY_KEY, build  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://fjsanfan.com"
VER = "v20260911e"          # 与 bump_assets_ver.py 同步
THUMBS_PER_TILE = 6         # 总览页每个分类格显示的产品缩略图数量

# ------------------------------------------------------------------ 模板
HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <meta name="description" content="{desc}" />
  <link rel="canonical" href="{canonical}" />
  <link rel="alternate" hreflang="en" href="{canonical}" />
  <link rel="alternate" hreflang="x-default" href="{canonical}" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{desc}" />
  <meta property="og:image" content="{og_img}" />
  <meta property="og:url" content="{canonical}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{title}" />
  <meta name="twitter:description" content="{desc}" />
  <meta name="twitter:image" content="{og_img}" />
  <link rel="stylesheet" href="assets/css/styles.css?{ver}" />
  <link rel="icon" href="assets/img/logo.webp" />

  <script type="application/ld+json">
  {jsonld}
  </script>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-RMSNDR5S06"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-RMSNDR5S06');
</script>
</head>
<body>
"""

NAV = """  <header class="site-header">
    <div class="container nav">
      <a href="/" class="nav-brand"><img src="assets/img/logo.webp" width="500" height="500" alt="SANFAN" /><span>SAN<span class="accent">FAN</span></span></a>
      <nav class="nav-links">
        <a href="/" data-i18n="nav.home">Home</a>
        <a href="products.html"{cur} data-i18n="nav.products">Products</a>
        <a href="about.html" data-i18n="nav.about">About</a>
        <a href="faq.html" data-i18n="nav.faq">FAQ</a>
        <a href="blog.html" data-i18n="nav.blog">Blog</a>
        <a href="contact.html" data-i18n="nav.contact">Contact</a>
      </nav>
      <div class="nav-actions"><div class="lang-switch"><button type="button" class="lang-current" aria-haspopup="true" aria-expanded="false"><span class="lang-cur-txt">EN</span><span class="lang-caret">&#9662;</span></button><div class="lang-menu"><button type="button" data-setlang="en" title="English" class="active">EN</button><button type="button" data-setlang="zh" title="中文">中文</button><a href="/de/products.html" hreflang="de" title="Deutsch">DE</a><a href="/ja/products.html" hreflang="ja" title="日本語">JA</a><a href="/ko/products.html" hreflang="ko" title="한국어">KO</a><a href="/fr/products.html" hreflang="fr" title="Français">FR</a><a href="/it/products.html" hreflang="it" title="Italiano">IT</a><a href="/es/products.html" hreflang="es" title="Español">ES</a></div></div>
        <a href="contact.html" class="btn btn-primary" data-i18n="nav.quote">Get a Quote</a>
      </div>
      <button class="menu-toggle" aria-label="menu">☰</button>
    </div>
  </header>
"""

FOOTER = """  <footer class="site-footer">
    <div class="container footer-grid">
      <div>
        <div class="brand"><img src="assets/img/logo.webp" width="500" height="500" loading="lazy" alt="SANFAN" /> <span>SAN<span style="color:var(--brand-2)">FAN</span></span></div>
        <p style="font-size:14px;max-width:300px" data-i18n="f.tag">OEM / ODM yoga &amp; fitness manufacturer.</p>
      </div>
      <div><h5 data-i18n="foot.products">Products</h5><ul>
{foot_cats}      </ul></div>
      <div><h5 data-i18n="foot.company">Company</h5><ul>
        <li><a href="about.html" data-i18n="nav.about">About</a></li>
        <li><a href="about.html" data-i18n="process.title">Production Process</a></li>
        <li><a href="contact.html" data-i18n="nav.contact">Contact</a></li>
      </ul></div>
      <div><h5 data-i18n="foot.contact">Contact</h5>
        <div class="contact-line"><span data-i18n="foot.addr">Address</span>: No. 8 Haiguang Road, Yuejin Industrial Zone, Xibin Town, Jinjiang, Quanzhou, Fujian, China</div>
        <div class="contact-line"><span data-i18n="foot.email">Email</span>: <a class="c-link" href="mailto:zenglinggun@gmail.com">zenglinggun@gmail.com</a></div>
        <div class="contact-line"><span data-i18n="foot.phone">WhatsApp</span>: <a class="c-link" href="https://wa.me/8615959029082" target="_blank" rel="noopener">+86 15959029082</a></div>
      </div>
    </div>
    <div class="container footer-bottom" data-i18n="foot.copyright">© 2026 FUJIAN SANFAN Sports Products Co., Ltd. All rights reserved.</div>
  </footer>

  <script src="assets/js/main.js?{ver}"></script>
</body>
</html>
"""

CTA = """  <section class="section soft">
    <div class="container" style="text-align:center;">
      <h2><span class="lang-en">Can't find the exact spec?</span><span class="lang-zh">没找到完全匹配的规格？</span></h2>
      <p class="lead" style="margin:12px auto 22px;max-width:640px;">
        <span class="lang-en">Send us your drawing, target price or a photo — we reply with a quote and a sampling plan within 24 hours. MOQ from 100 pcs.</span>
        <span class="lang-zh">把图纸、目标价或照片发给我们 —— 24 小时内回复报价与打样方案，100 片起订。</span>
      </p>
      <a href="contact.html" class="btn btn-primary"><span class="lang-en">Get a Quote</span><span class="lang-zh">获取报价</span></a>
    </div>
  </section>
"""


def bi(en, zh):
    """双语 span。.lang-zh 默认 display:none，中文态由 CSS 切换。"""
    return '<span class="lang-en">%s</span><span class="lang-zh">%s</span>' % (en, zh)


def cat_nav(cur_key):
    """横向分类切换条。"""
    chips = []
    for c in CATS:
        act = " cat-chip-active" if c["key"] == cur_key else ""
        chips.append(
            '      <a href="%s.html" class="cat-chip%s">%s</a>'
            % (c["key"], act, bi(c["en"], c["zh"]))
        )
    return ('  <div class="container cat-nav-wrap">\n'
            '    <nav class="cat-nav" aria-label="Product categories">\n'
            + "\n".join(chips) + "\n    </nav>\n  </div>\n")


# ------------------------------------------------------------------ 主流程
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--refresh", action="store_true",
                    help="忽略卡片池，从当前 products.html 重新提取（需列表页为完整版）")
    args = ap.parse_args()

    products_html = os.path.join(ROOT, "products.html")

    # --- 卡片池：首次从 products.html 提取后落盘，之后一直复用 ---
    # 脚本会把 products.html 重写成总览页（不再含 117 张卡），所以卡片源必须
    # 独立持久化，否则第二次运行就"无卡可提"。产物增删产品后用 --refresh 重建。
    pool_path = os.path.join(ROOT, "outputs/product_cards.json")
    if os.path.exists(pool_path) and not args.refresh:
        cards = json.load(open(pool_path, encoding="utf-8"))
        print("卡片池：%s（%d 张）" % (os.path.relpath(pool_path, ROOT), len(cards)))
    else:
        src = open(products_html, encoding="utf-8").read()
        cards = {}
        for m in re.finditer(
            r'<a class="prod-card" href="products/([a-z0-9-]+)\.html">[\s\S]*?</a>', src
        ):
            cards[m.group(1)] = m.group(0)
        if len(cards) < 100:
            print("!! 只提到 %d 张卡片 —— products.html 可能已是总览页。"
                  "请先用备份恢复，或执行 --refresh 前确认列表页是完整版。" % len(cards),
                  file=sys.stderr)
        else:
            json.dump(cards, open(pool_path, "w", encoding="utf-8"), ensure_ascii=False)
            print("卡片池重建：%d 张 → %s" % (len(cards), os.path.relpath(pool_path, ROOT)))

    assign, unmapped = build()
    if unmapped:
        print("!! 未归类：", unmapped, file=sys.stderr)
    missing = [s for s in assign if s not in cards]
    if missing:
        print("!! 列表页缺卡片：", missing, file=sys.stderr)

    # 分类内排序：把带编号的老页(ym1-7/fr1-5/...)排前面（它们是主推款），其余按 slug
    def order_key(slug):
        m = re.match(r"([a-z]+)(\d+)$", slug)
        return (0, m.group(1), int(m.group(2))) if m else (1, slug, 0)

    groups = {c["key"]: [] for c in CATS}
    for slug, key in assign.items():
        groups[key].append(slug)
    for k in groups:
        groups[k].sort(key=order_key)

    def first_img(slug):
        m = re.search(r'<img src="([^"]+)"', cards[slug])
        return m.group(1).split("?")[0] if m else "assets/img/logo.webp"

    def title_of(slug):
        m = re.search(r'<h4[^>]*>([\s\S]*?)</h4>', cards[slug])
        if not m:
            return slug
        t = re.sub(r"<[^>]+>", " ", m.group(1))
        return " ".join(t.split())

    foot_cats = "".join(
        '        <li><a href="%s.html">%s</a></li>\n' % (c["key"], bi(c["en"], c["zh"]))
        for c in CATS
    )

    written = []

    # ================= 1) 8 个分类页 =================
    for c in CATS:
        slugs = groups[c["key"]]
        if not slugs:
            continue
        cover = first_img(slugs[0])
        title = "%s Manufacturer | OEM / ODM — SANFAN" % c["en"]
        desc = ("%s %s. Factory-direct OEM/ODM from SANFAN: custom size, colour, logo and "
                "packaging, MOQ 100 pcs, sampling in 7 days." % (c["en"], c["kw_en"]))
        canon = "%s/%s.html" % (SITE, c["key"])

        items = [
            {"@type": "ListItem", "position": i + 1,
             "url": "%s/products/%s.html" % (SITE, s), "name": title_of(s)}
            for i, s in enumerate(slugs)
        ]
        jsonld = json.dumps({
            "@context": "https://schema.org",
            "@graph": [
                {"@type": "BreadcrumbList", "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Products",
                     "item": SITE + "/products.html"},
                    {"@type": "ListItem", "position": 3, "name": c["en"], "item": canon},
                ]},
                {"@type": "CollectionPage", "name": "%s — SANFAN" % c["en"],
                 "url": canon, "description": desc},
                {"@type": "ItemList", "name": c["en"], "numberOfItems": len(items),
                 "itemListElement": items},
            ],
        }, ensure_ascii=False)

        body = [HEAD.format(title=title.replace("|", "&#124;"),
                            desc=desc.replace('"', "&quot;"),
                            canonical=canon, og_img=SITE + "/" + cover.lstrip("/"),
                            jsonld=jsonld, ver=VER)]
        body.append(NAV.format(cur=' aria-current="page"'))

        # hero（比列表页矮一档）
        body.append(
            '  <section class="hero" style="background:linear-gradient(120deg,var(--brand-ink),var(--brand));">\n'
            '    <div class="container hero-inner" style="padding:44px 0 34px;">\n'
            '      <div class="breadcrumb"><a href="/">Home</a> / <a href="products.html">Products</a>'
            ' / <span>%s</span></div>\n'
            '      <h1>%s</h1>\n'
            '      <p class="lead">%s</p>\n'
            '    </div>\n'
            '  </section>\n\n' % (bi(c["en"], c["zh"]), bi(c["h1_en"], c["h1_zh"]),
                                  bi(c["desc_en"], c["desc_zh"]))
        )
        body.append(cat_nav(c["key"]))

        grid = "\n".join("        " + cards[s] for s in slugs)
        body.append(
            '  <section class="section">\n'
            '    <div class="container">\n'
            '      <div class="cat-head"><h3>%s</h3>'
            '<span class="tag">%s</span>'
            '<span class="cat-count">%d products</span></div>\n'
            '      <div class="prod-grid">\n%s\n      </div>\n'
            '    </div>\n'
            '  </section>\n\n'
            % (bi(c["en"], c["zh"]), bi(c["kw_en"], c["kw_zh"]), len(slugs), grid)
        )
        body.append(CTA)
        body.append(FOOTER.format(foot_cats=foot_cats, ver=VER))

        path = os.path.join(ROOT, c["key"] + ".html")
        if not args.dry_run:
            open(path, "w", encoding="utf-8").write("".join(body))
        written.append((c["key"] + ".html", len(slugs)))

    # ================= 2) 重写总览页 products.html =================
    tiles = []
    for c in CATS:
        slugs = groups[c["key"]]
        if not slugs:
            continue
        cover = first_img(slugs[0])
        thumbs = "\n".join(
            '            <a href="products/%s.html" title="%s">'
            '<img src="%s" loading="lazy" alt="%s"></a>'
            % (s, title_of(s).replace('"', "&quot;"), first_img(s),
               title_of(s).replace('"', "&quot;"))
            for s in slugs[:THUMBS_PER_TILE]
        )
        # 注意：外层容器必须是 <div>，不能用 <a> 包住整块 —— 里面的产品缩略图也是
        # <a>，HTML 解析器遇到嵌套 <a> 会强制闭合外层，.ct-body 会被甩出卡片。
        tiles.append(
            '        <div class="cat-tile">\n'
            '          <a class="ct-img" href="%s.html"><img src="%s" loading="lazy" alt="%s" /></a>\n'
            '          <div class="ct-body">\n'
            '            <h3><a href="%s.html">%s</a></h3>\n'
            '            <p class="ct-kw">%s</p>\n'
            '            <div class="ct-thumbs">\n%s\n            </div>\n'
            '            <a class="ct-more" href="%s.html">'
            '<span class="lang-en">View all %d products</span>'
            '<span class="lang-zh">查看全部 %d 款</span> &rarr;</a>\n'
            '          </div>\n'
            '        </div>'
            % (c["key"], cover, c["en"], c["key"], bi(c["en"], c["zh"]),
               bi(c["kw_en"], c["kw_zh"]), thumbs, c["key"], len(slugs), len(slugs))
        )

    ov_items = [
        {"@type": "ListItem", "position": i + 1,
         "url": "%s/%s.html" % (SITE, c["key"]), "name": c["en"]}
        for i, c in enumerate(CATS)
    ]
    ov_jsonld = json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Products",
                 "item": SITE + "/products.html"},
            ]},
            {"@type": "CollectionPage",
             "name": "SANFAN Yoga & Fitness Product Catalog",
             "url": SITE + "/products.html",
             "description": "Browse SANFAN's OEM/ODM catalogue by category: TPE, PU-rubber, "
                            "suede and cork yoga mats, meditation and Pilates mats, foam "
                            "rollers, recovery tools, resistance bands and yoga props."},
            {"@type": "ItemList", "name": "Product Categories",
             "numberOfItems": len(ov_items), "itemListElement": ov_items},
        ],
    }, ensure_ascii=False)

    ov = [HEAD.format(
        title="Products by Category — SANFAN Yoga Mat &amp; Fitness OEM Manufacturer",
        desc="Browse the SANFAN catalogue by category: TPE / PU-rubber / suede &amp; cork yoga "
             "mats, meditation &amp; Pilates mats, foam rollers, recovery tools, resistance "
             "bands and yoga props. OEM/ODM, MOQ 100 pcs.",
        canonical=SITE + "/products.html",
        og_img=SITE + "/assets/img/tpe-mat-2.webp",
        jsonld=ov_jsonld, ver=VER)]
    ov.append(NAV.format(cur=' aria-current="page"'))
    ov.append(
        '  <section class="hero" style="background:linear-gradient(120deg,var(--brand-ink),var(--brand));">\n'
        '    <div class="container hero-inner" style="padding:56px 0 38px;">\n'
        '      <span class="eyebrow" data-i18n="prod.title">Our Products</span>\n'
        '      <h1 data-i18n="prod.title">Our Products</h1>\n'
        '      <p class="lead"><span class="lang-en">117 factory-direct products in 8 categories. '
        'Pick a range to see full specifications, or tell us your target spec and we will build it.</span>'
        '<span class="lang-zh">117 款工厂直供产品，分为 8 大类。'
        '选择品类查看完整规格，或直接告诉我们目标参数 —— 我们来打样。</span></p>\n'
        '    </div>\n'
        '  </section>\n\n'
    )
    ov.append(cat_nav(None))
    ov.append(
        '  <section class="section">\n'
        '    <div class="container">\n'
        '      <div class="cat-tiles">\n' + "\n".join(tiles) + "\n      </div>\n"
        '    </div>\n'
        '  </section>\n\n'
    )
    ov.append(CTA)
    ov.append(FOOTER.format(foot_cats=foot_cats, ver=VER))

    if not args.dry_run:
        open(products_html, "w", encoding="utf-8").write("".join(ov))
    written.append(("products.html (总览重写)", len(CATS)))

    # ================= 输出 =================
    print("生成 %d 个文件：" % len(written))
    for name, n in written:
        print("  %-42s %s" % (name, ("%d 个产品" % n) if n > 8 else ("%d 个分类" % n)))
    print("\n分类分布：")
    for c in CATS:
        print("  %-26s %2d  %s" % (c["key"], len(groups[c["key"]]), c["en"]))


if __name__ == "__main__":
    main()
