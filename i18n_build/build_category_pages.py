# -*- coding: utf-8 -*-
"""把产品列表页拆成分类页 + 分类总览页（2026-09-12 改版：接公共模板）。

产出（全部在站点根目录，与 products.html 同级，相对路径基准一致）：
    <cat-key>.html   × 10    分类落地页（该类全部产品卡）
    products.html             分类总览（10 个分类大格 + 每格 6 个产品缩略图 + 场景入口区）

本次改版的三处变化：
    1. header/footer 改用 i18n_build/site_templates.py，与场景页、材质页共用一份模板；
    2. 分类切换条由「10 个 chip 平铺」改为「Mats / Training / Recovery & Props 三组」
       + 底部「按你卖给谁进场」场景快捷行（L2）；
    3. 每页尾部加材质对比引导，形成 分类页 → 材质页 → 场景页 的内链闭环。

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
from category_map import CATS, build  # noqa: E402
from site_templates import (SITE, VER, apps_section, bi, cat_nav, cta, footer, head,  # noqa: E402
                            nav)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THUMBS_PER_TILE = 6         # 总览页每个分类格显示的产品缩略图数量


def mat_callout():
    """分类页尾部的材质对比引导 —— 把「不知道选哪种材质」的流量接住。"""
    return ('      <div class="mat-note" style="max-width:820px;margin:34px auto 0;">'
            '<b>%s</b> %s <a href="materials.html" style="color:var(--brand);font-weight:600;">'
            '%s &rarr;</a></div>\n'
            % (bi("Not sure which material?", "不确定选哪种材质？"),
               bi("TPE, PVC, NBR, PU + rubber, suede, cork, EVA and EPP compared on grip, "
                  "durability, recyclability, thickness and price band.",
                  "TPE、PVC、NBR、PU 橡胶、麂皮、软木、EVA 与 EPP，"
                  "在防滑、耐用、可回收、厚度与价格带上逐项对比。"),
               bi("Compare materials", "查看材质对比")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--refresh", action="store_true",
                    help="忽略卡片池，从当前 products.html 重新提取（需列表页为完整版）")
    args = ap.parse_args()

    products_html = os.path.join(ROOT, "products.html")

    # --- 卡片池：首次从 products.html 提取后落盘，之后一直复用 ---
    # 脚本会把 products.html 重写成总览页（不再含全部卡片），所以卡片源必须
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
            print("!! 只提到 %d 张卡片 —— products.html 可能已是总览页。" % len(cards),
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
        # ⭐ 必须先摘掉中文配对 span（2026-09-16 修）：
        #    EN 页卡片用的是「行内配对 span」双语机制 ——
        #      <h4><span class="lang-en">Alignment Line TPE Yoga Mat</span>
        #          <span class="lang-zh">带体位线 TPE 瑜伽垫</span></h4>
        #    原先直接剥标签，于是得到双语串 `Alignment Line TPE Yoga Mat 带体位线 TPE 瑜伽垫`，
        #    它被写进 JSON-LD 的 ItemList name 和 products.html 缩略图的 title/alt；
        #    再经翻译管线 → EN 半被翻成 de/fr/…，中文半原样留着，
        #    7 个语言版本的结构化数据里都混进了中文（实测 de 分类页 23 条里 17 条中招）。
        h = re.sub(r'<span class="lang-zh">[\s\S]*?</span>', " ", m.group(1))
        t = re.sub(r"<[^>]+>", " ", h)
        return " ".join(t.split())

    written = []

    # ================= 1) 分类页 =================
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

        body = [head(title=title, desc=desc, canonical=canon,
                     og_img=SITE + "/" + cover.lstrip("/"), jsonld=jsonld)]
        body.append(nav())
        body.append(
            '  <section class="hero" style="background:linear-gradient(120deg,var(--brand-ink),var(--brand));">\n'
            '    <div class="container hero-inner" style="padding:44px 0 34px;">\n'
            '      <div class="breadcrumb"><a href="/">Home</a> / <a href="products.html">Products</a>'
            ' / <span>%s</span></div>\n'
            '      <h1>%s</h1>\n'
            '      <p class="lead">%s</p>\n'
            '    </div>\n'
            '  </section>\n\n' % (bi(c["en"], c["zh"]), bi(c["h1_en"], c["h1_zh"]),
                                  bi(c["desc_en"], c["desc_zh"])))
        body.append(cat_nav(c["key"]))
        grid = "\n".join("        " + cards[s] for s in slugs)
        body.append(
            '  <section class="section">\n'
            '    <div class="container">\n'
            '      <div class="cat-head"><h3>%s</h3>'
            '<span class="tag">%s</span>'
            '<span class="cat-count">%s</span></div>\n'
            '      <div class="prod-grid">\n%s\n      </div>\n%s'
            '    </div>\n'
            '  </section>\n\n'
            % (bi(c["en"], c["zh"]), bi(c["kw_en"], c["kw_zh"]),
               bi("%d products" % len(slugs), "%d 款" % len(slugs)), grid, mat_callout())
        )
        body.append(cta())
        body.append(footer())

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
                            "rollers, recovery tools, resistance bands, jump ropes, strength "
                            "and fitness equipment, aerial hammocks and yoga props."},
            {"@type": "ItemList", "name": "Product Categories",
             "numberOfItems": len(ov_items), "itemListElement": ov_items},
        ],
    }, ensure_ascii=False)

    ov = [head(
        title="Products by Category — SANFAN Yoga Mat &amp; Fitness OEM Manufacturer",
        desc="Browse the SANFAN catalogue by category: TPE / PU-rubber / suede &amp; cork yoga "
             "mats, meditation &amp; Pilates mats, foam rollers, recovery tools, resistance "
             "bands and yoga props. OEM/ODM, MOQ 100 pcs.",
        canonical=SITE + "/products.html",
        og_img=SITE + "/assets/img/tpe-mat-2.webp",
        jsonld=ov_jsonld)]
    ov.append(nav(cur=True))
    n_prod, n_cat = len(assign), len(CATS)
    ov.append(
        '  <section class="hero" style="background:linear-gradient(120deg,var(--brand-ink),var(--brand));">\n'
        '    <div class="container hero-inner" style="padding:56px 0 38px;">\n'
        '      <span class="eyebrow" data-i18n="prod.title">Our Products</span>\n'
        '      <h1 data-i18n="prod.title">Our Products</h1>\n'
        '      <p class="lead"><span class="lang-en">%d factory-direct products in %d categories. '
        'Pick a range to see full specifications, or tell us your target spec and we will build it.</span>'
        '<span class="lang-zh">%d 款工厂直供产品，分为 %d 大类。'
        '选择品类查看完整规格，或直接告诉我们目标参数 —— 我们来打样。</span></p>\n'
        '    </div>\n'
        '  </section>\n\n' % (n_prod, n_cat, n_prod, n_cat))
    ov.append(cat_nav(None))
    ov.append(apps_section("", head_en="Or shop by application — pick who you sell to",
                           head_zh="或者按用途选购 —— 选一个贴近你客户的方式"))
    ov.append(
        '  <section class="section soft">\n'
        '    <div class="container">\n'
        '      <div class="cat-head"><h3>%s</h3>'
        '<span class="cat-count">%s</span></div>\n'
        '      <div class="cat-tiles">\n%s\n      </div>\n'
        '    </div>\n'
        '  </section>\n\n'
        % (bi("All categories by product line", "全部分类（按产品线）"),
           bi("%d categories · %d products" % (n_cat, n_prod),
              "%d 个大类 · %d 款产品" % (n_cat, n_prod)),
           "\n".join(tiles)))
    ov.append(cta())
    ov.append(footer())

    if not args.dry_run:
        open(products_html, "w", encoding="utf-8").write("".join(ov))
    written.append(("products.html (总览重写)", len(CATS)))

    print("生成 %d 个文件：" % len(written))
    for name, n in written:
        print("  %-42s %d 款" % (name, n))
    print("\n分类分布：")
    for c in CATS:
        print("  %-26s %2d  %s" % (c["key"], len(groups[c["key"]]), c["en"]))


if __name__ == "__main__":
    main()
