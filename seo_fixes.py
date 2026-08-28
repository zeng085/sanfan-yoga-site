#!/usr/bin/env python3
"""SEO 快赢：全站注入 canonical + Open Graph/Twitter Card，并修剪超长 title/desc。
幂等：已存在则跳过；按精确旧串替换 title/desc。"""
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
DOMAIN = "https://sanfan-yoga-site.vercel.app"

# 文件 -> (canonical 路径后缀, og:image 文件名)
PAGES = {
    "index.html":              ("/", "tpe-mat-1.jpg"),
    "about.html":             ("/about.html", "factory-building.jpg"),
    "products.html":          ("/products.html", "tpe-mat-2.jpg"),
    "product.html":           ("/product.html", "tpe-mat-1.jpg"),
    "contact.html":           ("/contact.html", "showroom.jpg"),
    "faq.html":               ("/faq.html", "tpe-mat-1.jpg"),
    "blog.html":              ("/blog.html", "tpe-mat-1.jpg"),
    "blog/tpe-vs-pu.html":    ("/blog/tpe-vs-pu.html", "pu-rubber-mat-1.jpg"),
    "blog/moq-explained.html":("/blog/moq-explained.html", "tpe-mat-1.jpg"),
    "blog/compliance.html":   ("/blog/compliance.html", "certification-wall.jpg"),
    "blog/vet-factory.html":  ("/blog/vet-factory.html", "factory-building.jpg"),
    "blog/7day-sampling.html":("/blog/7day-sampling.html", "tpe-foldable-1.jpg"),
    "blog/custom-sizes.html": ("/blog/custom-sizes.html", "tpe-mat-5.jpg"),
}

# 精确 title 替换（旧 -> 新）
TITLE_FIX = {
    "faq.html": (
        "FAQ — Yoga Mat OEM/ODM Factory | MOQ, Certifications & Customization | SANFAN",
        "Yoga Mat OEM/ODM FAQ: MOQ, Certifications | SANFAN",
    ),
    "blog/vet-factory.html": (
        "How to Vet a Chinese Yoga Mat Factory Before a Bulk Order | SANFAN",
        "How to Vet a Chinese Yoga Mat Factory | SANFAN",
    ),
    "blog/7day-sampling.html": (
        "7-Day Sampling: Why Fast Prototyping Wins Private-Label Brands | SANFAN",
        "7-Day Sampling for Private-Label Yoga Brands | SANFAN",
    ),
    "blog/custom-sizes.html": (
        "Custom Yoga Mat Sizes & Thickness: A Buyer's Specification Guide | SANFAN",
        "Custom Yoga Mat Sizes & Thickness Guide | SANFAN",
    ),
}

# 精确 desc 替换（旧 -> 新）
DESC_FIX = {
    "index.html": (
        "FUJIAN SANFAN — leading OEM/ODM manufacturer of yoga mats, aerial yoga hammocks, yoga props, foam rollers, resistance bands & fitness equipment. 600+ workers, 200K+ mats/month, MOQ 100 pcs, 7-day sampling.",
        "FUJIAN SANFAN — OEM/ODM factory for yoga mats, hammocks, foam rollers & fitness gear. 600+ workers, 200K+ mats/month, MOQ 100 pcs, 7-day sampling.",
    ),
    "products.html": (
        "SANFAN full catalog: TPE / PU-Rubber yoga mats, aerial yoga hammocks, yoga wheels, yoga blocks, foam rollers, resistance bands, yoga balls, balance boards, dumbbells, kettlebells, jump ropes and steppers. OEM/ODM customizable, factory-direct.",
        "SANFAN catalog: TPE/PU yoga mats, aerial hammocks, foam rollers, resistance bands, yoga balls & more. OEM/ODM customizable, factory-direct pricing, MOQ 100 pcs.",
    ),
    "faq.html": (
        "Answers to the questions overseas buyers ask when sourcing yoga mats from China: MOQ, REACH/CA Prop 65 certification, customization, lead time, Amazon FBA shipping and why Fujian SANFAN is a direct factory.",
        "Overseas buyer FAQ for sourcing yoga mats from China: MOQ, REACH/CA Prop 65 certification, customization, sampling & Amazon FBA shipping — direct from Fujian SANFAN.",
    ),
}

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def get_title(html):
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    return m.group(1).strip() if m else ""

def get_desc(html):
    m = re.search(r'<meta name="description" content="(.*?)"', html, re.S)
    return m.group(1) if m else ""

def main():
    log = []
    for rel, (canon_path, og_img) in PAGES.items():
        path = os.path.join(ROOT, rel)
        with open(path, encoding="utf-8") as f:
            html = f.read()
        canon_url = DOMAIN + canon_path
        img_url = DOMAIN + "/assets/img/" + og_img
        title = get_title(html)
        desc = get_desc(html)
        changed = []

        # 1) canonical
        if 'rel="canonical"' not in html:
            block = '  <link rel="canonical" href="%s" />\n' % canon_url
            # 插入到 meta description 之后
            html = re.sub(r'(<meta name="description" content="[^"]*" ?/?>)',
                          lambda m: m.group(1) + "\n" + block.rstrip("\n"), html, count=1)
            changed.append("canonical")

        # 2) OG + Twitter
        if 'property="og:title"' not in html:
            og = (
                '  <meta property="og:type" content="website" />\n'
                '  <meta property="og:title" content="%s" />\n'
                '  <meta property="og:description" content="%s" />\n'
                '  <meta property="og:image" content="%s" />\n'
                '  <meta property="og:url" content="%s" />\n'
                '  <meta name="twitter:card" content="summary_large_image" />\n'
                '  <meta name="twitter:title" content="%s" />\n'
                '  <meta name="twitter:description" content="%s" />\n'
                '  <meta name="twitter:image" content="%s" />\n'
            ) % (esc(title), esc(desc), img_url, canon_url, esc(title), esc(desc), img_url)
            # 插入到 canonical 之后（或 description 之后若没有 canonical）
            if 'rel="canonical"' in html:
                html = html.replace('  <link rel="canonical" href="%s" />' % canon_url,
                                    '  <link rel="canonical" href="%s" />\n%s' % (canon_url, og.rstrip("\n")), 1)
            else:
                html = re.sub(r'(<meta name="description" content="[^"]*" ?/?>)',
                              lambda m: m.group(1) + "\n" + og.rstrip("\n"), html, count=1)
            changed.append("og/twitter")

        # 3) title 修剪
        if rel in TITLE_FIX:
            old, new = TITLE_FIX[rel]
            if old in html:
                html = html.replace("<title>%s</title>" % old, "<title>%s</title>" % new, 1)
                changed.append("title trimmed")
            else:
                log.append("  [WARN] %s title 旧串不匹配，跳过" % rel)

        # 4) desc 修剪
        if rel in DESC_FIX:
            old, new = DESC_FIX[rel]
            needle = 'content="%s"' % old
            if needle in html:
                html = html.replace(needle, 'content="%s"' % new, 1)
                changed.append("desc trimmed")
            else:
                log.append("  [WARN] %s desc 旧串不匹配，跳过" % rel)

        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        log.append("[%s] 注入: %s" % (rel, ", ".join(changed) if changed else "无变更"))

    print("\n".join(log))

if __name__ == "__main__":
    main()
