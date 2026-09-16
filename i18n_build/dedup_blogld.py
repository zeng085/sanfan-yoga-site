#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""去掉 fix_final/fix_blogld 首版往博客索引里写重复的 JSON-LD 块，只保留精修版。"""
import json
import re

FILES = ['blog.html', 'de/blog.html', 'ja/blog.html', 'ko/blog.html',
         'fr/blog.html', 'it/blog.html', 'es/blog.html']
BLOCK = re.compile(r'[ \t]*<script type="application/ld\+json">\s*\{\s*"@context".*?</script>\n?', re.S)
FIND = re.compile(r'application/ld\+json">(.*?)</script>', re.S)

for f in FILES:
    s = open(f, encoding="utf-8").read()
    spans = [(m.start(), m.end(), m.group(0)) for m in BLOCK.finditer(s)]
    mine = [sp for sp in spans if "blog.html#blog" in sp[2]]
    if not mine:
        print("%-14s 无自建块，跳过" % f)
        continue
    keep = None
    for sp in mine:
        if "numberOfItems" in sp[2]:
            keep = sp
            break
    if keep is None:
        keep = mine[-1]
    # 重建：删除 mine 里除 keep 之外的所有块
    drop = [sp for sp in mine if sp is not keep]
    out, pos = [], 0
    for st, en, _ in drop:
        out.append(s[pos:st])
        pos = en
    out.append(s[pos:])
    s2 = "".join(out)
    m = FIND.search(s2)
    assert m, f + " ld+json 丢失"
    d = json.loads(m.group(1))
    il = d["@graph"][1]
    open(f, "w", encoding="utf-8").write(s2)
    print("%-14s 原%d块→保留1  total_ld=%d  lang=%s  n=%d  first=%s" % (
        f, len(mine), len(BLOCK.findall(s2)), d["@graph"][0]["inLanguage"],
        il.get("numberOfItems"), il["itemListElement"][0]["name"][:44]))
