#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""博客索引 JSON-LD 精修 + 导航数据文件目录化（2026-09-16）

fix_final_20260916.py 首版把整张卡片文本塞进了 ListItem.name（含徽标、中文块、
"Read →"），这里改成从卡片内的 <h3>/<p> 精确取；顺便把 assets/data/navdata*.js
里的 applications/index.html 也改成目录形式（与 HTML 保持一致）。

用法：python3 fix_blogld_20260916.py [--apply]
"""
import glob
import html as H
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPLY = "--apply" in sys.argv
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
LANGNAME = {"blog.html": "en", "de/blog.html": "de", "ja/blog.html": "ja",
            "ko/blog.html": "ko", "fr/blog.html": "fr", "it/blog.html": "it",
            "es/blog.html": "es"}
SKIP = ("/.git", "/node_modules", "/outputs", "/__pycache__", "/i18n_build")


def clean(t):
    return re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", t))).strip()


def build(rel, s):
    sub = "" if rel == "blog.html" else "/" + rel.split("/")[0]
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S)
    name = clean(h1.group(1)) if h1 else "Blog"
    md = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', s)
    desc = H.unescape(md.group(1)) if md else name
    items, seen = [], set()
    for m in re.finditer(r'<a class="post-card"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', s, re.S):
        href, inner = m.group(1), m.group(2)
        if href in seen:
            continue
        seen.add(href)
        # 优先 .lang-en 块的 h3（EN 页双语块），否则第一个 h3
        en = re.search(r'<div class="lang-en">(.*?)</div>', inner, re.S)
        scope = en.group(1) if en else inner
        h3 = re.search(r"<h3[^>]*>(.*?)</h3>", scope, re.S)
        if not h3:
            h3 = re.search(r"<h3[^>]*>(.*?)</h3>", inner, re.S)
        p = re.search(r"<p[^>]*>(.*?)</p>", scope, re.S) or \
            re.search(r"<p[^>]*>(.*?)</p>", inner, re.S)
        if not h3:
            continue
        items.append({"@type": "ListItem", "position": len(items) + 1,
                      "url": "https://fjsanfan.com/%s%s" % (rel.rsplit("/", 1)[0] + "/" if "/" in rel else "", href),
                      "name": clean(h3.group(1)),
                      "description": clean(p.group(1)) if p else None})
    data = {"@context": "https://schema.org", "@graph": [
        {"@type": "Blog", "@id": "https://fjsanfan.com%s/blog.html#blog" % sub,
         "url": "https://fjsanfan.com%s/blog.html" % sub,
         "name": name, "description": desc, "inLanguage": LANGNAME[rel],
         "publisher": {"@type": "Organization", "name": "FUJIAN SANFAN Sports Products",
                       "url": "https://fjsanfan.com/"}},
        {"@type": "ItemList", "@id": "https://fjsanfan.com%s/blog.html#list" % sub,
         "name": name, "numberOfItems": len(items), "itemListElement": items}]}
    for it in data["@graph"][1]["itemListElement"]:
        if it.get("description") is None:
            it.pop("description")
    pretty = json.dumps(data, ensure_ascii=False, indent=2)
    return ('  <script type="application/ld+json">\n'
            + "\n".join("  " + ln for ln in pretty.splitlines()) + "\n  </script>\n")


def main():
    n = 0
    files = ["blog.html"] + ["%s/blog.html" % l for l in LANGS]
    for rel in files:
        p = os.path.join(ROOT, rel)
        if not os.path.isfile(p):
            print("MISS", rel)
            continue
        s = open(p, encoding="utf-8").read()
        s = re.sub(r'  <script type="application/ld\+json">\s*\{[^<]*"blog\.html#blog".*?</script>\n',
                   "", s, flags=re.S)
        block = build(rel, s)
        s = s.replace("</head>", block + "</head>", 1)
        json.loads(re.search(r"application/ld\+json\">(.*?)</script>", s, re.S).group(1))
        if APPLY:
            open(p, "w", encoding="utf-8").write(s)
        n += 1
        print("%-16s items=%d" % (rel, s.count('"position"')))
    # navdata
    for f in sorted(glob.glob(os.path.join(ROOT, "assets", "data", "navdata*.js"))):
        js = open(f, encoding="utf-8").read()
        if "applications/index.html" in js:
            if APPLY:
                open(f, "w", encoding="utf-8").write(js.replace("applications/index.html", "applications/"))
            print("navdata fixed:", os.path.basename(f))
    print("模式：%s，博客索引 %d 页" % ("APPLY" if APPLY else "DRY-RUN", n))


if __name__ == "__main__":
    main()
