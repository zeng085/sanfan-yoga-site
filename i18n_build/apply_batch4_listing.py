# -*- coding: utf-8 -*-
"""把第四批 6 个「品类通用款」页面接进卡片池、sitemap.xml 与 llms.txt（幂等）。

- 卡片池 outputs/product_cards.json：分类页 / 总览页 / 首页卡片的唯一来源
- sitemap.xml：追加 6 个产品页
- llms.txt：产品数 141 → 147，并把新增品类补进 product range 描述
  （llms.txt 是 AI 爬虫的事实来源，数量写错等于对外发布错误事实）

跑完本脚本后依次执行：
    python3 i18n_build/build_category_pages.py     # 分类页 + products.html 总览
    python3 i18n_build/build_navdata.py            # 搜索索引
    python3 i18n_build/bump_assets_ver.py          # 资源版本号
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = "https://fjsanfan.com"
POOL = os.path.join(ROOT, "outputs", "product_cards.json")
ITEMS = json.load(open(os.path.join(ROOT, "outputs", "batch4_common_pages.json"), encoding="utf-8"))


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def card(it):
    img = it["new"] + "-1.webp"
    s = it["specs"] or {}
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
            "  </url>\n" % (u, u, u))
        added += 1
    if block:
        h = h.replace("</urlset>", "".join(block) + "</urlset>")
        open(p, "w", encoding="utf-8").write(h)
    print("sitemap.xml：+%d 条 → 共 %d 条" % (added, h.count("<loc>")))


def update_llms():
    p = os.path.join(ROOT, "llms.txt")
    s = open(p, encoding="utf-8").read()
    orig = s
    n_pages = len([f for f in os.listdir(os.path.join(ROOT, "products")) if f.endswith(".html")])

    s = re.sub(r"Product range: \d+ products in \d+ lines",
               "Product range: %d products in 10 lines" % n_pages, s)
    s = s.replace(
        "fitness boards, steppers)",
        "fitness boards, steppers), plus vibration plates for massage & recovery")
    s = s.replace(
        "silicone weights, ab rollers,",
        "silicone weights, ab rollers, ab wheels, adjustable dumbbells, kettlebells, suspension trainers,")

    if s != orig:
        open(p, "w", encoding="utf-8").write(s)
        print("llms.txt：产品数 → %d，并补充新增品类" % n_pages)
    else:
        print("llms.txt：无需修改")


if __name__ == "__main__":
    update_pool()
    update_sitemap()
    update_llms()
