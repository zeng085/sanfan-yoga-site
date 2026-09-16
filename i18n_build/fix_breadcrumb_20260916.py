#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""面包屑结构化数据修复（2026-09-16）

问题（由 audit_links / audit_seo 抓出，819 处）：
  117 个产品页/语言 的 BreadcrumbList 第 3 项指向**不存在的锚点**：
      EN 页：https://fjsanfan.com/products.html#rollers
      语言页：https://fjsanfan.com/products.html#rollers   ← 还漏成英文路径
  两个硬伤叠在一起：
    ① products.html 里没有 #rollers/#yoga/#props/#bands/#fit 任何一个 id（实测该页
       只有 id="applications"），item URL 指向空锚点；
    ② 语言页的第 3 项写成 `https://fjsanfan.com/products.html#…`（**英文区**），
       而同一条 BreadcrumbList 里的第 1/2/4 项都是 /de/… —— 自相矛盾，且把
       德语产品页的父级指给了英文页。
  同站另有 30 个产品页已经用「真实分类页 + 正确语言前缀」的写法，可作范式：
      https://fjsanfan.com/de/strength-training.html

修法：把锚点型 item 换成该产品**真实所属分类页**的语言正确 URL。
  产品→分类页的映射**不是猜的**：直接从 10 个分类页里反查 product 链接得到
  （实测 147 款产品全部落在唯一分类页，无重合）。

用法：
  python3 fix_breadcrumb_20260916.py            # 试运行
  python3 fix_breadcrumb_20260916.py --apply
"""
import glob
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
CATS = ["tpe-yoga-mats", "pu-rubber-yoga-mats", "suede-cork-yoga-mats",
        "meditation-pilates-mats", "foam-rollers", "massage-recovery",
        "resistance-bands", "yoga-props-accessories", "jump-ropes", "strength-training"]
LEGACY = ("yoga", "props", "rollers", "bands", "fit")


def build_prod2cat():
    m = {}
    for c in CATS:
        s = open(os.path.join(ROOT, c + ".html"), encoding="utf-8").read()
        for mm in re.finditer(r'href="products/([a-z0-9-]+)\.html"', s):
            m.setdefault(mm.group(1), c)
    return m


def main():
    apply = "--apply" in sys.argv
    prod2cat = build_prod2cat()
    print("产品→分类页映射：%d 款" % len(prod2cat))
    stat = Counter()
    nomap = []
    for lg in [""] + LANGS:
        base = os.path.join(ROOT, lg, "products") if lg else os.path.join(ROOT, "products")
        pre = "%s/" % lg if lg else ""
        for f in sorted(glob.glob(os.path.join(base, "*.html"))):
            slug = os.path.basename(f)[:-5]
            cat = prod2cat.get(slug)
            s = open(f, encoding="utf-8").read()
            hits = re.findall(r'https://fjsanfan\.com/products\.html#(%s)' % "|".join(LEGACY), s)
            if not hits:
                continue
            if not cat:
                nomap.append(os.path.relpath(f, ROOT))
                continue
            new_url = "https://fjsanfan.com/%s%s.html" % (pre, cat)
            out = s
            for fr in set(hits):
                out = out.replace("https://fjsanfan.com/products.html#%s" % fr, new_url)
                stat[(lg or "en", fr, cat)] += 1
            if apply and out != s:
                open(f, "w", encoding="utf-8").write(out)
    tot = sum(stat.values())
    print("\n待替换 %d 处（%s）:" % (tot, "已落盘" if apply else "试运行未写盘"))
    for (lg, fr, cat), n in sorted(stat.items(), key=lambda kv: (kv[0][0], -kv[1])):
        print("   %-4s #%-8s → %-26s %d" % (lg, fr, cat, n))
    if nomap:
        print("\n!! 无分类映射（未改）：", len(nomap), nomap[:5])
    if not apply:
        print("\n（试运行；加 --apply 落盘）")


if __name__ == "__main__":
    main()
