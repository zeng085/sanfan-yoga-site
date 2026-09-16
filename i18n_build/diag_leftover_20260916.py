#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""遗留编辑项取数（2026-09-16 夜）：括号错位 / 德语多余引号 / it 阻带页 / 超长 title 分型。

只读，不改盘。输出用于决定改动方案。
"""
import glob
import os
import re
from collections import Counter

ROOT = "/Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16"
LANGS = ["", "de", "ja", "ko", "fr", "it", "es"]
DIRS = ["", "products", "applications", "blog", "pilates"]


def W(s):
    return sum(2 if ord(c) > 0x2E80 else 1 for c in s)


def pages():
    for lg in LANGS:
        for sub in DIRS:
            if sub:
                base = os.path.join(ROOT, lg, sub) if lg else os.path.join(ROOT, sub)
            else:
                base = os.path.join(ROOT, lg) if lg else ROOT
            for f in sorted(glob.glob(os.path.join(base, "*.html"))):
                yield lg, f


def sec1_paren():
    print("=" * 78)
    print("① 括号错位 (10\")) 全部上下文")
    print("=" * 78)
    rx = re.compile(r'.{0,70}\(10"\).{0,50}', re.S)
    for lg, f in pages():
        s = open(f, encoding="utf-8", errors="ignore").read()
        if '(10"))' not in s:
            continue
        rel = os.path.relpath(f, ROOT)
        for m in rx.finditer(s):
            ctx = re.sub(r"\s+", " ", m.group(0)).strip()
            print("  %-42s %s" % (rel, ctx))


def sec2_degquote():
    print()
    print("=" * 78)
    print("② 德语多余引号 „…“ 全部上下文（仅 de/）")
    print("=" * 78)
    rx = re.compile(r"\u201e[^\u201c\u201d]{1,80}?\u201c")
    cnt = Counter()
    for f in sorted(glob.glob(os.path.join(ROOT, "de", "**", "*.html"), recursive=True)):
        s = open(f, encoding="utf-8", errors="ignore").read()
        for m in rx.finditer(s):
            cnt[m.group(0)] += 1
    for k, v in cnt.most_common():
        print("  %3d  %s" % (v, k))
    # 同一形态在 it/es 里的法/西引号，供对比
    print("  --- 其他语言同类引号（只计数）---")
    for lg, pat, name in (("fr", r"\u00ab[^\u00bb]{1,60}?\u00bb", "fr «»"),
                          ("it", r"\u201c[^\u201d]{1,60}?\u201d", "it “”"),
                          ("es", r"\u00ab[^\u00bb]{1,60}?\u00bb", "es «»")):
        c = Counter()
        for f in sorted(glob.glob(os.path.join(ROOT, lg, "**", "*.html"), recursive=True)):
            s = open(f, encoding="utf-8", errors="ignore").read()
            for m in re.finditer(pat, s):
                c[m.group(0)] += 1
        print("  %s 共 %d 种 / %d 次" % (name, len(c), sum(c.values())))
        for k, v in c.most_common(8):
            print("        %3d  %s" % (v, k))


def sec3_itband():
    print()
    print("=" * 78)
    print("③ tpe-resistance-loop-band 各语言 title / h1")
    print("=" * 78)
    for lg in LANGS:
        p = os.path.join(ROOT, lg, "products", "tpe-resistance-loop-band.html") if lg \
            else os.path.join(ROOT, "products", "tpe-resistance-loop-band.html")
        if not os.path.exists(p):
            print("  %-4s (缺失)" % (lg or "en"))
            continue
        s = open(p, encoding="utf-8").read()
        t = re.search(r"<title>([^<]*)</title>", s)
        h = re.search(r"<h1[^>]*>([\s\S]{0,240}?)</h1>", s)
        print("  %-4s title: %s" % (lg or "en", t.group(1) if t else "?"))
        print("       h1   : %s" % re.sub(r"\s+", " ", h.group(1)) if h else "?")


def sec4_title_shape():
    print()
    print("=" * 78)
    print("④ 超长 title（>60）分型")
    print("=" * 78)
    shape = Counter()
    rows = []
    for lg, f in pages():
        s = open(f, encoding="utf-8", errors="ignore").read()
        for m in re.finditer(r"<title>([^<]*)</title>", s):
            t = m.group(1)
            w = W(t)
            if w <= 60:
                continue
            if " | " in t:
                k = "含竖线 |"
            elif re.search(r":\s", t):
                k = "含冒号列表"
            elif " \u2014 SANFAN" in t or " | " in t:
                k = "含破折号"
            else:
                k = "其他"
            shape[k] += 1
            rows.append((w, lg or "en", os.path.relpath(f, ROOT), t))
    print("  分型：", dict(shape))
    # 按语言统计
    bylang = Counter(r[1] for r in rows)
    print("  按语言：", dict(bylang))
    # 竖线型单独列全
    print("  --- 竖线型（可安全砍后半段）---")
    for w, lg, rel, t in sorted(rows, reverse=True):
        if " | " in t:
            print("   %3d %-6s %s" % (w, lg, t))
    # 骨架 = 去掉 — SANFAN 后的宽度
    print("  --- 非竖线型 ---")
    for w, lg, rel, t in sorted(rows, reverse=True):
        if " | " not in t:
            body = t.replace(" \u2014 SANFAN", "")
            print("   %3d %-6s bodyW=%3d  %s  [%s]" % (w, lg, W(body), t, rel))


if __name__ == "__main__":
    sec1_paren()
    sec2_degquote()
    sec3_itband()
    sec4_title_shape()
