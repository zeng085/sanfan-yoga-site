# -*- coding: utf-8 -*-
"""生成 L3 场景落地页：applications/index.html + applications/<key>.html × 6。

每页 = 一份采购方案（配置表 + 推荐型号 + 选品指南 + FAQ），而不是产品清单。
全部输出到 applications/ 子目录，因此模板统一用 prefix="../"。

用法
    python3 i18n_build/build_application_pages.py --dry-run
    python3 i18n_build/build_application_pages.py
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from apps_data import APPS  # noqa: E402
from site_templates import (SITE, VER, apps_section, bi, cat_nav, cta, esc, footer,  # noqa: E402
                            head, nav, trust_strip)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "applications")
PF = "../"


def cards():
    return json.load(open(os.path.join(ROOT, "outputs/product_cards.json"), encoding="utf-8"))


def en_title(card_html, slug):
    """从卡片 HTML 取英文名（batch3 卡片是双语 span，老卡片是纯文本）。"""
    m = re.search(r'<h4[^>]*>([\s\S]*?)</h4>', card_html)
    if not m:
        return slug
    h = m.group(1)
    m2 = re.search(r'<span class="lang-en">([\s\S]*?)</span>', h)
    t = m2.group(1) if m2 else re.sub(r"<[^>]+>", " ", h)
    return " ".join(t.split())


def rel_card(card_html):
    """卡片里的相对路径改为 applications/ 视角。"""
    return (card_html
            .replace('href="products/', 'href="../products/')
            .replace('src="assets/', 'src="../assets/'))


def app_jsonld(a, prod_names):
    canon = "%s/applications/%s.html" % (SITE, a["key"])
    items = [
        {"@type": "ListItem", "position": i + 1,
         "url": "%s/products/%s.html" % (SITE, s), "name": n}
        for i, (s, n) in enumerate(prod_names)
    ]
    faq = [
        {"@type": "Question", "name": q_en,
         "acceptedAnswer": {"@type": "Answer", "text": a_en}}
        for (q_en, _q_zh, a_en, _a_zh) in a["faq"]
    ]
    return json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Products",
                 "item": SITE + "/products.html"},
                {"@type": "ListItem", "position": 3, "name": "Applications",
                 "item": SITE + "/applications/index.html"},
                {"@type": "ListItem", "position": 4, "name": a["en"], "item": canon},
            ]},
            {"@type": "CollectionPage", "name": "%s — SANFAN" % a["en"],
             "url": canon, "description": a["desc_seo"],
             "about": {"@type": "Thing", "name": a["en"]},
             "audience": {"@type": "BusinessAudience", "name": a["en"]}},
            {"@type": "ItemList", "name": "%s — recommended range" % a["en"],
             "numberOfItems": len(items), "itemListElement": items},
            {"@type": "FAQPage", "mainEntity": faq},
        ],
    }, ensure_ascii=False)


def kit_table(a):
    rows = []
    for i, (ie, iz, ue, uz, se, sz) in enumerate(a["kit"], 1):
        rows.append(
            '        <tr>\n'
            '          <th scope="row"><span class="kt-i">%02d</span> %s</th>\n'
            '          <td>%s</td>\n'
            '          <td>%s</td>\n'
            '        </tr>' % (i, bi(ie, iz), bi(ue, uz), bi(se, sz)))
    return (
        '  <section class="section" id="kit">\n'
        '    <div class="container">\n'
        '      <div class="section-head">\n'
        '        <div class="eyebrow">%s</div>\n'
        '        <h2>%s</h2>\n'
        '        <p>%s</p>\n'
        '      </div>\n'
        '      <div class="kit-wrap">\n'
        '        <table class="kit-table">\n'
        '          <thead><tr>\n'
        '            <th>%s</th><th>%s</th><th>%s</th>\n'
        '          </tr></thead>\n'
        '          <tbody>\n%s\n          </tbody>\n'
        '        </table>\n'
        '      </div>\n'
        '    </div>\n'
        '  </section>\n\n'
        % (bi("What goes into the order", "这份订单里有什么"),
           bi("A %s order, item by item" % a["en"], "%s 订单构成，逐项拆开" % a["zh"]),
           bi("Read this as a bill of materials. Tell us which rows you want and we will quote "
              "them as one shipment.",
              "把这张表当成一份配置清单。告诉我们你要哪几行，我们按一票货报价。"),
           bi("Item", "品项"), bi("Where it is used", "用在哪个环节"),
           bi("Suggested spec", "建议规格"), "\n".join(rows))
    )


def product_grid(a, pool):
    picks = [s for s in a["products"] if s in pool]
    missing = [s for s in a["products"] if s not in pool]
    if missing:
        print("  !! %s 选品缺失：%s" % (a["key"], missing), file=sys.stderr)
    grid = "\n".join("        " + rel_card(pool[s]) for s in picks)
    return ('  <section class="section soft" id="range">\n'
            '    <div class="container">\n'
            '      <div class="cat-head"><h3>%s</h3>'
            '<span class="tag">%s</span>'
            '<span class="cat-count">%d products</span></div>\n'
            '      <div class="prod-grid">\n%s\n      </div>\n'
            '      <div class="range-more">%s <a href="../products.html">%s &rarr;</a></div>\n'
            '    </div>\n'
            '  </section>\n\n'
            % (bi("Recommended for %s" % a["en"], "%s 推荐型号" % a["zh"]),
               bi(a["kit_en"], a["kit_zh"]), len(picks), grid,
               bi("Need something not listed here?", "需要这里没列到的款？"),
               bi("Browse all 141 products", "查看全部 141 款"))), picks


def guide_section(a):
    return ('  <section class="section">\n'
            '    <div class="container">\n'
            '      <div class="guide-wrap">\n'
            '        <div class="gw-head">\n'
            '          <div class="eyebrow">%s</div>\n'
            '          <h2>%s</h2>\n'
            '        </div>\n'
            '        <div class="gw-body">\n'
            '          <p>%s</p>\n'
            '        </div>\n'
            '      </div>\n'
            '    </div>\n'
            '  </section>\n\n'
            % (bi("How to buy", "采购建议"),
               bi("How experienced buyers order this range",
                  "有经验的买家是怎么下这单的"),
               bi(a["guide_en"], a["guide_zh"])))


def faq_section(a):
    items = "".join(
        '        <details class="faq-item">\n'
        '          <summary>%s</summary>\n'
        '          <div class="faq-a">%s</div>\n'
        '        </details>\n' % (bi(qe, qz), bi(ae, az))
        for (qe, qz, ae, az) in a["faq"])
    return ('  <section class="section soft">\n'
            '    <div class="container">\n'
            '      <div class="section-head">\n'
            '        <div class="eyebrow">%s</div>\n'
            '        <h2>%s</h2>\n'
            '      </div>\n'
            '      <div class="faq-list">\n%s      </div>\n'
            '    </div>\n'
            '  </section>\n\n'
            % (bi("FAQ", "常见问题"),
               bi("%s — buyer questions" % a["en"], "%s —— 买家常问" % a["zh"]),
               items))


def related_section(cur_key):
    cards_ = []
    for a in APPS:
        if a["key"] == cur_key:
            continue
        cards_.append(
            '        <a class="app-card app-card-sm" href="%s.html">\n'
            '          <span class="ac-icon">%s</span>\n'
            '          <h4>%s</h4>\n'
            '          <div class="ac-kit">%s</div>\n'
            '        </a>' % (a["key"], a["icon"], bi(a["en"], a["zh"]),
                           bi(a["kit_en"], a["kit_zh"])))
    return ('  <section class="section">\n'
            '    <div class="container">\n'
            '      <div class="section-head">\n'
            '        <div class="eyebrow">%s</div>\n'
            '        <h2>%s</h2>\n'
            '      </div>\n'
            '      <div class="apps-grid">\n%s\n      </div>\n'
            '    </div>\n'
            '  </section>\n\n'
            % (bi("Other applications", "其他应用场景"),
               bi("Not your channel? Try one of these", "不是你的渠道？看看这几个"),
               "\n".join(cards_)))


def build_hub(pool):
    canon = SITE + "/applications/index.html"
    items = [{"@type": "ListItem", "position": i + 1,
              "url": "%s/applications/%s.html" % (SITE, a["key"]), "name": a["en"]}
             for i, a in enumerate(APPS)]
    jsonld = json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Products",
                 "item": SITE + "/products.html"},
                {"@type": "ListItem", "position": 3, "name": "Applications", "item": canon},
            ]},
            {"@type": "CollectionPage",
             "name": "Yoga & Fitness Equipment by Application — SANFAN",
             "url": canon,
             "description": "Buy yoga and fitness equipment by application: studio fit-outs, "
                            "gyms and fitness clubs, hotels and spas, private label, recovery "
                            "and physio, and e-commerce sellers."},
            {"@type": "ItemList", "name": "Applications",
             "numberOfItems": len(items), "itemListElement": items},
        ],
    }, ensure_ascii=False)

    body = [head(
        title="Yoga &amp; Fitness Equipment by Application | OEM / ODM — SANFAN",
        desc="Shop the SANFAN range by application: yoga and Pilates studio fit-outs, gyms and "
             "fitness clubs, hotels and spas, private label, recovery and physio, and online "
             "sellers. One factory, one PO, MOQ 100 pcs.",
        canonical=canon,
        og_img=SITE + "/assets/img/factory-building.webp",
        jsonld=jsonld, prefix=PF)]
    body.append(nav(PF))
    body.append(
        '  <section class="hero" style="background:linear-gradient(120deg,var(--brand-ink),var(--brand));">\n'
        '    <div class="container hero-inner" style="padding:52px 0 40px;">\n'
        '      <div class="breadcrumb"><a href="/">Home</a> / <a href="../products.html">Products</a>'
        ' / <span>%s</span></div>\n'
        '      <h1>%s</h1>\n'
        '      <p class="lead">%s</p>\n'
        '    </div>\n'
        '  </section>\n\n'
        % (bi("Applications", "应用场景"),
           bi("Buy by application, not by spec sheet",
              "按用途采购，而不是按规格表"),
           bi("Six ways buyers actually order from us. Pick the one that matches your business "
              "and you get a configured kit — items, suggested specs and a quote for the whole "
              "shipment, rather than 141 SKUs to sort through.",
              "买家实际下单的六种方式。选一个贴近你生意的入口，你拿到的是一份配好的方案 —— "
              "品项、建议规格与整票报价，而不是 141 个 SKU 让你自己挑。")))
    body.append(cat_nav(None, PF))
    body.append(trust_strip())
    body.append(apps_section(PF))
    body.append(cta(PF))
    body.append(footer(PF))
    return "".join(body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    pool = cards()
    print("卡片池 %d 张；VER=%s" % (len(pool), VER))

    if not args.dry_run and not os.path.isdir(OUT):
        os.makedirs(OUT)

    written = []
    for a in APPS:
        canon = "%s/applications/%s.html" % (SITE, a["key"])
        prod_names = [(s, en_title(pool[s], s)) for s in a["products"] if s in pool]
        body = [head(title=a["title_seo"], desc=a["desc_seo"], canonical=canon,
                     og_img=SITE + "/assets/img/%s" % re.search(
                         r'src="assets/img/([^"]+)"', pool[a["products"][0]]).group(1),
                     jsonld=app_jsonld(a, prod_names), prefix=PF)]
        body.append(nav(PF))
        body.append(
            '  <section class="hero" style="background:linear-gradient(120deg,var(--brand-ink),var(--brand));">\n'
            '    <div class="container hero-inner" style="padding:48px 0 38px;">\n'
            '      <div class="breadcrumb"><a href="/">Home</a> / <a href="../products.html">Products</a>'
            ' / <a href="index.html">Applications</a> / <span>%s</span></div>\n'
            '      <span class="eyebrow">%s</span>\n'
            '      <h1>%s</h1>\n'
            '      <p class="lead">%s</p>\n'
            '    </div>\n'
            '  </section>\n\n'
            % (bi(a["en"], a["zh"]), bi(a["tag_en"], a["tag_zh"]),
               bi(a["en"], a["zh"]), bi(a["hero_en"], a["hero_zh"])))
        body.append(cat_nav(None, PF))
        body.append(trust_strip())
        body.append(kit_table(a))
        grid_html, picks = product_grid(a, pool)
        body.append(grid_html)
        body.append(guide_section(a))
        body.append(faq_section(a))
        body.append(related_section(a["key"]))
        body.append(cta(PF))
        body.append(footer(PF))

        path = os.path.join(OUT, a["key"] + ".html")
        if not args.dry_run:
            open(path, "w", encoding="utf-8").write("".join(body))
        written.append(("applications/%s.html" % a["key"], len(picks)))

    hub = build_hub(pool)
    if not args.dry_run:
        open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(hub)
    written.append(("applications/index.html", len(APPS)))

    print("生成 %d 个文件：" % len(written))
    for name, n in written:
        print("  %-46s %d 款" % (name, n))


if __name__ == "__main__":
    main()
