#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
博客旗舰文《Private Label Yoga Mats》卡片 → 6 语言 blog.html 索引页
- 幂等：已含该卡的索引页跳过
- 卡片 h3/p 按 EN 文案经 DeepL 翻译（走 translator 缓存）
- 链接用绝对路径 /{L}/blog/...（与语言索引页现有卡片一致）
"""
import os, re, sys, html as H
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import translator as T

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
SLUG = "private-label-yoga-mats"
TITLE_EN = "Private Label Yoga Mats: The Complete Launch Guide"
DESC_EN = ("Positioning, construction, spec sheet, golden sample, packaging — "
           "the full deposit-to-shelf workflow.")
ALT_EN = "Private label yoga mats launch guide"
TAG = "Private Label"          # 品牌术语，不翻
IMG = "../assets/img/tpe-mat-1.webp"

CARD = ('<a class="post-card" href="/{L}/blog/{slug}.html">\n'
        '<div class="pc-img"><img alt="{alt}" height="480" loading="lazy" src="{img}" width="480"/></div>\n'
        '<div class="pc-body">\n'
        '<div class="pc-tag">{tag}</div>\n'
        '<div><h3>{title}</h3><p>{desc}</p></div>\n'
        '\n'
        '<span class="pc-more">Read \u2192</span>\n'
        '</div>\n'
        '</a>\n')


def main():
    # 每语言一次批量翻译（title/desc/alt 3 条 × 6 语言），走缓存
    tr = {}
    for L in LANGS:
        t, d, a = T.translate_lines([TITLE_EN, DESC_EN, ALT_EN], L)
        tr[L] = (t, d, a)
    T.flush()

    n = 0
    for L in LANGS:
        p = os.path.join(ROOT, L, "blog.html")
        s = open(p, encoding="utf-8").read()
        if SLUG in s:
            print("skip(已有):", p)
            continue
        anchor = '<div class="blog-grid">'
        i = s.find(anchor)
        if i < 0:
            print("!! 找不到 blog-grid:", p)
            continue
        t, d, a = tr[L]
        card = CARD.format(L=L, slug=SLUG, tag=TAG, img=IMG,
                           title=H.escape(t, quote=False),
                           desc=H.escape(d, quote=False),
                           alt=H.escape(a, quote=True))
        s = s[:i + len(anchor)] + "\n" + card.rstrip("\n") + s[i + len(anchor):]
        open(p, "w", encoding="utf-8").write(s)
        n += 1
        print("inserted:", p)
    print("done, %d pages" % n)


if __name__ == "__main__":
    main()
