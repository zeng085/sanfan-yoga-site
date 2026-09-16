#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""meta 长度体检（可重复跑）：按 Google 像素宽度统计 title / description 超长。

为什么不用「字符数」判据：CJK 字符宽度约是拉丁字母的 2 倍，
按字符数统计会让日/韩版看起来"完全没问题"—— 实测 ja 产品页按字符数是 0 超长，
按显示宽度却是 112 页超长。**必须按宽度算。**

预算（近似）：
    title       ≤ 60 宽   （Google 桌面约 580px / 移动约 680px）
    description ≤ 155 宽  （Google 桌面约 920px）

用法：
    python3 stats_meta.py            # 汇总表
    python3 stats_meta.py --top 30   # 附超长明细 Top N
"""
import glob
import html
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LANGS = [("EN", "."), ("de", "de"), ("ja", "ja"), ("ko", "ko"),
         ("fr", "fr"), ("it", "it"), ("es", "es")]
DIRS = [("", "root"), ("products", "products"), ("applications", "applications"),
        ("blog", "blog"), ("pilates", "pilates")]
T_BUDGET, D_BUDGET = 60, 155
TITLE_RE = re.compile(r"<title>([\s\S]*?)</title>")
DESC_RE = re.compile(r'<meta name="description" content="([^"]*)"')


def W(s):
    return sum(2 if ord(c) > 0x2E80 else 1 for c in s)


def plain(h):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def main():
    top = 0
    if "--top" in sys.argv:
        top = int(sys.argv[sys.argv.index("--top") + 1])

    print("按显示宽度（CJK=2）· title 预算 %d / desc 预算 %d" % (T_BUDGET, D_BUDGET))
    print("%-4s %-13s %6s %8s %8s %8s %8s" %
          ("lang", "dir", "pages", "T>60", "T>70", "D>155", "D>175"))
    tot = Counter()
    over_t, over_d = [], []
    for lg, base in LANGS:
        for sub, label in DIRS:
            pat = os.path.join(ROOT, base, sub, "*.html") if sub else os.path.join(ROOT, base, "*.html")
            fs = sorted(glob.glob(pat))
            if not fs:
                continue
            c = Counter()
            for f in fs:
                s = open(f, encoding="utf-8", errors="ignore").read()
                mt = TITLE_RE.search(s)
                md = DESC_RE.search(s)
                t = plain(mt.group(1)) if mt else ""
                d = plain(md.group(1)) if md else ""
                wt, wd = W(t), W(d)
                c["n"] += 1
                if wt > T_BUDGET:
                    c["T60"] += 1
                    over_t.append((wt, lg, os.path.relpath(f, ROOT), t))
                if wt > 70:
                    c["T70"] += 1
                if wd > D_BUDGET:
                    c["D155"] += 1
                    over_d.append((wd, lg, os.path.relpath(f, ROOT), d))
                if wd > 175:
                    c["D175"] += 1
            tot.update(c)
            if c["T60"] or c["D155"]:
                print("%-4s %-13s %6d %8d %8d %8d %8d" %
                      (lg, label, c["n"], c["T60"], c["T70"], c["D155"], c["D175"]))
    print()
    print("全站: 页 %d | title>%d宽 %d | title>70宽 %d | desc>%d宽 %d | desc>175宽 %d"
          % (tot["n"], T_BUDGET, tot["T60"], tot["T70"], D_BUDGET, tot["D155"], tot["D175"]))

    if top:
        for name, arr in (("title", over_t), ("description", over_d)):
            arr.sort(reverse=True)
            print("\n=== %s 超长 Top %d ===" % (name, top))
            for w, lg, f, s in arr[:top]:
                print("  [%3d] %-4s %-44s %s" % (w, lg, f, s[:78]))


if __name__ == "__main__":
    main()
