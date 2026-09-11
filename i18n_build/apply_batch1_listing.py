# -*- coding: utf-8 -*-
"""把第一批生成的产品页接进 products.html 列表页与 sitemap.xml（幂等，可重复跑）。"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = "https://fjsanfan.com"
ITEMS = json.load(open(os.path.join(ROOT, "outputs", "batch1_pages.json"), encoding="utf-8"))


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def card(it):
    img = it["new"] + "-1.webp"
    s = it["specs"]
    mat = (s.get("Material") or "").strip()
    size = (s.get("Size") or "").strip()
    en = " · ".join([x for x in [mat, size] if x]) or "Made to order"
    zh = ("材质 " + mat + " · 尺寸 " + size) if (mat and size) else en
    return ('<a class="prod-card" href="products/%s.html"><div class="ph"><img src="assets/img/%s" '
            'width="480" height="480" loading="lazy" alt="%s"></div><div class="info">'
            '<h4><span class="lang-en">%s</span><span class="lang-zh">%s</span></h4>'
            '<p><span class="lang-en">%s</span><span class="lang-zh">%s</span></p></div></a>'
            % (it["new"], img, esc(it["title_en"]), esc(it["title_en"]), esc(it["title_zh"]),
               esc(en), esc(zh)))


def update_products_html():
    p = os.path.join(ROOT, "products.html")
    h = open(p, encoding="utf-8").read()
    i = h.find('id="yoga"')
    j = h.find("<!-- =====", i + 5)
    if i < 0 or j < 0:
        raise SystemExit("找不到瑜伽分类区块")
    seg, added = h[i:j], 0
    cards = []
    for it in ITEMS:
        if ('products/%s.html"' % it["new"]) in h:
            continue
        if not os.path.exists(os.path.join(ROOT, "assets", "img", it["new"] + "-1.webp")):
            print("  [缺图]", it["new"])
            continue
        cards.append("        " + card(it))
        added += 1
    if not cards:
        print("products.html：无新增")
        return
    anchor = seg.rstrip()
    tail = seg[len(anchor):]
    # 在分类区块最后一个 </div> 之前插入（即卡片栅格收口前）
    k = anchor.rfind("      </div>")
    newseg = anchor[:k] + "\n".join(cards) + "\n" + anchor[k:] + tail
    h = h[:i] + newseg + h[j:]
    open(p, "w", encoding="utf-8").write(h)
    print("products.html：新增 %d 张卡片" % added)


def update_sitemap():
    p = os.path.join(ROOT, "sitemap.xml")
    h = open(p, encoding="utf-8").read()
    block, added = [], 0
    for it in ITEMS:
        u = "%s/products/%s.html" % (DOMAIN, it["new"])
        if u + "</loc>" in h:
            continue
        block.append(
            "  <url>\n"
            "    <loc>%s</loc>\n"
            '    <xhtml:link rel="alternate" hreflang="en" href="%s"/>\n'
            '    <xhtml:link rel="alternate" hreflang="x-default" href="%s"/>\n'
            "    <changefreq>weekly</changefreq>\n"
            "    <priority>0.8</priority>\n"
            "  </url>\n" % (u, u, u)
        )
        added += 1
    if not block:
        print("sitemap.xml：无新增")
        return
    h = h.replace("</urlset>", "".join(block) + "</urlset>")
    open(p, "w", encoding="utf-8").write(h)
    print("sitemap.xml：新增 %d 条" % added)


if __name__ == "__main__":
    update_products_html()
    update_sitemap()
