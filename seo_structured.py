#!/usr/bin/env python3
"""SEO 快赢补充：给首页/产品页/联系页注入结构化数据（JSON-LD）。幂等。"""
import os
import json

ROOT = os.path.dirname(os.path.abspath(__file__))
D = "https://sanfan-yoga-site.vercel.app"

INDEX_JSON = {
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": "Organization",
            "name": "FUJIAN SANFAN Sports Products Co., Ltd.",
            "url": D + "/",
            "logo": D + "/assets/img/logo.jpg",
            "description": "OEM/ODM manufacturer of yoga mats, aerial yoga hammocks and fitness equipment since 2013.",
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "No. 8 Haiguang Road, Yuejin Industrial Zone, Xibin Town, Jinjiang",
                "addressLocality": "Quanzhou",
                "addressRegion": "Fujian",
                "addressCountry": "CN"
            },
            "email": "zenglinggun@gmail.com"
        },
        {
            "@type": "WebSite",
            "name": "FUJIAN SANFAN",
            "url": D + "/"
        }
    ]
}

PRODUCTS_JSON = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    "name": "SANFAN Yoga & Fitness Product Catalog",
    "itemListElement": [
        {"@type": "ListItem", "position": 1, "url": D + "/product.html?id=ym1", "name": "TPE Yoga Mat"},
        {"@type": "ListItem", "position": 2, "url": D + "/product.html?id=ym5", "name": "PU / Rubber Premium Mat"},
        {"@type": "ListItem", "position": 3, "url": D + "/product.html?id=pr1", "name": "Aerial Yoga Hammock"},
        {"@type": "ListItem", "position": 4, "url": D + "/product.html?id=pr2", "name": "Yoga Wheel"},
        {"@type": "ListItem", "position": 5, "url": D + "/product.html?id=roller1", "name": "Foam Roller"},
        {"@type": "ListItem", "position": 6, "url": D + "/product.html?id=bands1", "name": "Resistance Bands"},
        {"@type": "ListItem", "position": 7, "url": D + "/product.html?id=ball1", "name": "Yoga Ball"},
        {"@type": "ListItem", "position": 8, "url": D + "/product.html?id=db1", "name": "Dumbbell Set"}
    ]
}

CONTACT_JSON = {
    "@context": "https://schema.org",
    "@type": "LocalBusiness",
    "name": "FUJIAN SANFAN Sports Products Co., Ltd.",
    "url": D + "/contact.html",
    "email": "zenglinggun@gmail.com",
    "telephone": "+86 15959029082",
    "address": {
        "@type": "PostalAddress",
        "streetAddress": "No. 8 Haiguang Road, Yuejin Industrial Zone, Xibin Town, Jinjiang",
        "addressLocality": "Quanzhou",
        "addressRegion": "Fujian",
        "addressCountry": "CN"
    }
}

MAP = {
    "index.html": INDEX_JSON,
    "products.html": PRODUCTS_JSON,
    "contact.html": CONTACT_JSON,
}

def main():
    for rel, data in MAP.items():
        path = os.path.join(ROOT, rel)
        html = open(path, encoding="utf-8").read()
        if 'application/ld+json' in html and ('"Organization"' in html or '"ItemList"' in html or '"LocalBusiness"' in html):
            print("[%s] 已存在结构化数据，跳过" % rel)
            continue
        block = '\n  <script type="application/ld+json">\n  %s\n  </script>' % json.dumps(data, ensure_ascii=False)
        if "</head>" in html:
            html = html.replace("</head>", block + "\n</head>", 1)
        else:
            html = html + block
        open(path, "w", encoding="utf-8").write(html)
        print("[%s] 注入结构化数据: %s" % (rel, data["@type"] if "@type" in data else "graph(%s)" % ",".join(n.get("@type") for n in data.get("@graph", []))))

if __name__ == "__main__":
    main()
