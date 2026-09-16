#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""待办清单的集中体检（2026-09-16）：一次性把几件待办的数据取齐，避免反复全站扫描。

输出：
  ① 仍带长后缀「— SANFAN Yoga & Fitness OEM」的页面
  ② it/products/tpe-resistance-loop-band.html 的 title/h1
  ③ 偏短的 description（<120 展示宽）及其全文
  ④ 括号错位形态 `(10"))` 的范围
  ⑤ title/description 展示宽超限统计
"""
import glob
import os
import re
from collections import Counter

ROOT = "/Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16"
DIRS = ["", "products", "applications", "blog", "pilates"]
LANGS = ["", "de", "ja", "ko", "fr", "it", "es"]
LONG = "— SANFAN Yoga &amp; Fitness OEM"


def W(s):
    """展示宽度：CJK 记 2，其余记 1。"""
    return sum(2 if ord(c) > 0x2E80 else 1 for c in s)


def pages():
    for lg in LANGS:
        for sub in DIRS:
            base = os.path.join(ROOT, lg, sub) if sub else (os.path.join(ROOT, lg) if lg else ROOT)
            for f in sorted(glob.glob(os.path.join(base, "*.html"))):
                yield lg, f


def main():
    long_hits = []
    paren = []
    short = []
    wstat = Counter()
    wbad = []
    for lg, f in pages():
        s = open(f, encoding="utf-8", errors="ignore").read()
        rel = os.path.relpath(f, ROOT)
        n = s.count(LONG)
        if n:
            long_hits.append((n, rel))
        if '(10"))' in s:
            paren.append((rel, s.count('(10"))')))
        for m in re.finditer(r'<meta name="description" content="([^"]*)"', s):
            d = m.group(1)
            w = W(d)
            wstat["desc>155" if w > 155 else "desc_ok"] += 1
            if w < 120:
                short.append((w, rel, d))
        for m in re.finditer(r'<title>([^<]*)</title>', s):
            t = m.group(1)
            w = W(t)
            wstat["title>60" if w > 60 else "title_ok"] += 1
            if w > 60:
                wbad.append((w, rel, t))

    print("① 仍带长后缀的页面：%d 个" % len(long_hits))
    for n, rel in sorted(long_hits, reverse=True)[:15]:
        print("   %2d  %s" % (n, rel))

    print("\n② it 阻带页:")
    p = os.path.join(ROOT, "it/products/tpe-resistance-loop-band.html")
    if os.path.exists(p):
        s = open(p, encoding="utf-8").read()
        for m in re.finditer(r'<(title|h1)[^>]*>([\s\S]{0,160}?)</\1>', s):
            print("   <%s> %s" % (m.group(1), re.sub(r"\s+", " ", m.group(2))))

    print("\n③ description 偏短（<120 展示宽）：%d 处" % len(short))
    for w, rel, d in sorted(short)[:40]:
        print("   %3d  %-46s %s" % (w, rel, d))

    print("\n④ 括号错位 `(10\"))`：%d 处" % len(paren))
    for rel, n in paren:
        print("   %d  %s" % (n, rel))

    print("\n⑤ 展示宽统计: %s" % dict(wstat))
    print("   title 超 60 的前 25 条：")
    for w, rel, t in sorted(wbad, reverse=True)[:25]:
        print("   %3d  %-46s %s" % (w, rel, t))


if __name__ == "__main__":
    main()
