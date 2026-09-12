# -*- coding: utf-8 -*-
"""把第三批 24 个页面接进卡片池与 sitemap.xml（幂等，可重复跑）。

- 卡片池 outputs/product_cards.json：分类页/总览页/首页的卡片唯一来源
- sitemap.xml：追加 24 个产品页 + 2 个新分类页

跑完本脚本后依次执行：
    python3 i18n_build/build_category_pages.py     # 分类页 + products.html 总览
    python3 i18n_build/wire_category_links.py      # 首页 range-grid + footer
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = "https://fjsanfan.com"
POOL = os.path.join(ROOT, "outputs", "product_cards.json")
ITEMS = json.load(open(os.path.join(ROOT, "outputs", "batch3_pages.json"), encoding="utf-8"))
NEW_CATS = ["jump-ropes", "strength-training"]


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def card(it):
    img = it["new"] + "-1.webp"
    s = it["specs"]
    mat = (s.get("Material") or "").strip()
    size = (s.get("Size") or "").strip()
    en = " · ".join([x for x in [mat, size] if x]) or "Made to order"
    zh = ("材质 " + mat + " · 尺寸 " + size) if (mat and size) else "按单定制"
    return ('<a class="prod-card" href="products/%s.html"><div class="ph"><img src="assets/img/%s" '
            'width="480" height="480" loading="lazy" alt="%s"></div><div class="info">'
            '<h4><span class="lang-en">%s</span><span class="lang-zh">%s</span></h4>'
            '<p><span class="lang-en">%s</span><span class="lang-zh">%s</span></p></div></a>'
            % (it["new"], img, esc(it["title_en"]), esc(it["title_en"]), esc(it["title_zh"]),
               esc(en), esc(zh)))


def update_pool():
    pool = json.load(open(POOL, encoding="utf-8"))
    added, skipped = 0, []
    for it in ITEMS:
        slug = it["new"]
        if slug in pool:
            skipped.append(slug)
            continue
        if not os.path.exists(os.path.join(ROOT, "assets", "img", slug + "-1.webp")):
            print("  [缺首图]", slug)
            continue
        pool[slug] = card(it)
        added += 1
    if added:
        json.dump(pool, open(POOL, "w", encoding="utf-8"), ensure_ascii=False)
    print("卡片池：+%d 张 → 共 %d 张%s"
          % (added, len(pool), ("（已存在 %d 张跳过）" % len(skipped)) if skipped else ""))


def update_sitemap():
    p = os.path.join(ROOT, "sitemap.xml")
    h = open(p, encoding="utf-8").read()
    urls = ["%s/products/%s.html" % (DOMAIN, it["new"]) for it in ITEMS]
    urls += ["%s/%s.html" % (DOMAIN, k) for k in NEW_CATS]
    block, added = [], 0
    for u in urls:
        if u + "</loc>" in h:
            continue
        block.append(
            "  <url>\n"
            "    <loc>%s</loc>\n"
            '    <xhtml:link rel="alternate" hreflang="en" href="%s"/>\n'
            '    <xhtml:link rel="alternate" hreflang="x-default" href="%s"/>\n'
            "    <changefreq>weekly</changefreq>\n"
            "    <priority>%s</priority>\n"
            "  </url>\n" % (u, u, u, "0.8" if "/products/" in u else "0.9"))
        added += 1
    if block:
        h = h.replace("</urlset>", "".join(block) + "</urlset>")
        open(p, "w", encoding="utf-8").write(h)
    print("sitemap.xml：+%d 条 → 共 %d 条" % (added, h.count("<loc>")))


if __name__ == "__main__":
    update_pool()
    update_sitemap()
