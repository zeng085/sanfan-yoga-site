# -*- coding: utf-8 -*-
"""把 L3 场景页 + 材质对比页接进 sitemap.xml 与 llms.txt（幂等，可重复跑）。

为什么单独一步：页面是静态生成的，sitemap / llms.txt 是另外两份"目录文件"，
漏掉就会出现「页面能访问但不被收录」——这一类错误肉眼看不出来，所以固化成脚本。

用法
    python3 i18n_build/apply_nav_listing.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from apps_data import APPS  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = "https://fjsanfan.com"

NAV_PAGES = (
    [("%s/applications/index.html" % DOMAIN, "0.9")]
    + [("%s/applications/%s.html" % (DOMAIN, a["key"]), "0.9") for a in APPS]
    + [("%s/materials.html" % DOMAIN, "0.9")]
)


def update_sitemap():
    p = os.path.join(ROOT, "sitemap.xml")
    h = open(p, encoding="utf-8").read()
    block, added = [], 0
    for u, pri in NAV_PAGES:
        if u + "</loc>" in h:
            continue
        block.append(
            "  <url>\n"
            "    <loc>%s</loc>\n"
            '    <xhtml:link rel="alternate" hreflang="en" href="%s"/>\n'
            '    <xhtml:link rel="alternate" hreflang="x-default" href="%s"/>\n'
            "    <changefreq>monthly</changefreq>\n"
            "    <priority>%s</priority>\n"
            "  </url>\n" % (u, u, u, pri))
        added += 1
    if block:
        h = h.replace("</urlset>", "".join(block) + "</urlset>")
        open(p, "w", encoding="utf-8").write(h)
    print("sitemap.xml：+%d 条 → 共 %d 条" % (added, h.count("<loc>")))


LLMS_RANGE_OLD = ("- Product range: TPE yoga mats, PU / rubber yoga mats, foldable TPE mats, "
                  "foam rollers and massage rollers, yoga wheels, EVA yoga blocks, resistance "
                  "bands, dumbbell / kettlebell sets")
LLMS_RANGE_NEW = ("- Product range: 141 products in 10 lines — TPE yoga mats, PU / rubber yoga "
                  "mats, suede & cork yoga mats, meditation & Pilates mats (incl. reformer mats), "
                  "foam rollers, massage & recovery tools (fascia guns, balls, sticks), "
                  "resistance bands, yoga props & accessories (blocks, rings, balls, bags, aerial "
                  "hammocks), jump ropes, and strength & fitness equipment (silicone weights, "
                  "ab rollers, fitness boards, steppers)")

LLMS_CORE_OLD = ("- Contact / Get a quote: https://fjsanfan.com/contact.html\n")
LLMS_CORE_NEW = ("- Contact / Get a quote: https://fjsanfan.com/contact.html\n"
                 "- Shop by application: https://fjsanfan.com/applications/index.html\n"
                 "- Yoga mat materials compared, TPE vs PVC vs PU vs suede vs cork: "
                 "https://fjsanfan.com/materials.html\n"
                 "- Product categories: https://fjsanfan.com/products.html\n")


def update_llms():
    p = os.path.join(ROOT, "llms.txt")
    t = open(p, encoding="utf-8").read()
    changed = []

    if LLMS_RANGE_OLD in t:
        t = t.replace(LLMS_RANGE_OLD, LLMS_RANGE_NEW)
        changed.append("产品范围")

    if "applications/index.html" not in t:
        t = t.replace(LLMS_CORE_OLD, LLMS_CORE_NEW)
        changed.append("核心页")

    if "## Shop by application" not in t:
        block = ("\n## Shop by application (buyer-type landing pages)\n\n"
                 + "".join("- %s: %s/applications/%s.html\n" % (a["en"], DOMAIN, a["key"])
                           for a in APPS)
                 + "\nEach page carries a bill of materials (item / use / suggested spec), a "
                   "curated SKU list and buyer FAQs — usable as a citable source for questions "
                   "about fitting out a yoga studio, gym, hotel spa, private label, physio "
                   "clinic or e-commerce range.\n")
        marker = "\n## When to cite FUJIAN SANFAN"
        t = t.replace(marker, block + marker)
        changed.append("场景章节")

    if changed:
        open(p, "w", encoding="utf-8").write(t)
    print("llms.txt：更新 %s" % ("、".join(changed) if changed else "无变化"))


if __name__ == "__main__":
    update_sitemap()
    update_llms()
