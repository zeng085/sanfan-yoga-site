#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多语言「术语被无谓加引号」清理（2026-09-16 夜）。

背景
----
de/fr/it/es 页面里存在大量形如 `„TPE“` `« TPE »` `“PU”` 的引号，共约 6600 处。
比对英文源页：正文里 TPE 出现 1740 次，仅 2 次带引号（`"TPE"`），
而 de 一处 `„TPE“` 就有 621 处。结论：这不是源串带引号，而是
DeepL 在处理「术语/复合名词」时**自行添加的引号**，属机翻痕迹。
典型病句：
    de  unsere umweltfreundliche Yoga-Matte „TPE“ besteht aus …   （应为 Matte aus TPE）
    de  unsere „TPE“-Matten                                        （应为 TPE-Matten）
    de  frei von „PVC“                                             （应为 frei von PVC）

策略（保守）
----------
只去掉「引号内正好是一个术语/标准号/尺寸/品牌」的引号 —— 这类场景
在任何语言里都几乎没有真正加引号的必要；而 FAQ 里引用客户原话的
整句式引号（如 „Überall keine Mindestbestellmenge!“）一律**不动**。

用法
----
  （默认）只统计
  --list   列出全部命中的原始片段
  --apply  落盘
"""
import argparse
import glob
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = "/Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16"
DIRS = ["", "products", "applications", "blog", "pilates"]

# 各语言的本地化引号对
QUOTES = {
    "de": ("\u201e", "\u201c"),   # „ … “
    "fr": ("\u00ab", "\u00bb"),   # « … »
    "es": ("\u00ab", "\u00bb"),   # « … »
    "it": ("\u201c", "\u201d"),   # “ … ”
    "ko": ("\u2018", "\u2019"),   # ‘ … ’
    "ja": ("\u300c", "\u300d"),   # 「 … 」
    # 注意：it 也用 «»
}
EXTRA = {"it": [("\u00ab", "\u00bb")]}

# 允许出现在引号内的「术语」原子
ATOMS = [
    r"TPE", r"PU", r"PVC", r"NBR", r"EVA", r"SBR", r"TPR", r"ABS", r"PP", r"PE",
    r"ROHS", r"REACH", r"SGS", r"CE", r"ISO(?:\s*9001)?", r"BSCI", r"Intertek",
    r"OEKO-?TEX", r"GRS", r"CA\s*Prop\s*65", r"Prop\s*65", r"EN\s*71(?:-3)?",
    r"6P", r"7P", r"MOQ", r"OEM(?:/ODM)?", r"ODM", r"FOB", r"EXW",
    r"SANFAN", r"FUJIANSANFAN", r"TPE-?Matte", r"PVC-?Matte",
    r"\d+(?:[.,]\d+)?\s*(?:cm|mm|kg|g|St\u00fcck|pcs|\u33a1|m\u00b2)",
    r"\d+\s*[\u00d7x*]\s*\d+(?:\s*[\u00d7x*]\s*\d+)?(?:\s*(?:cm|mm))?",
]
TERM = "(?:" + "|".join(ATOMS) + ")"


# 名称语境：产品名/页面名里出现的引号一律属机翻痕迹（英文源从不这么写）。
# 只在这些标签内动手，绝不动正文（正文里可能有正当的客户原话引用）。
NAME_CTX = [
    re.compile(r"<title>([\s\S]*?)</title>", re.I),
    re.compile(r"<h1[^>]*>([\s\S]*?)</h1>", re.I),
    re.compile(r"<h2[^>]*>([\s\S]*?)</h2>", re.I),
    re.compile(r"<h4[^>]*>([\s\S]*?)</h4>", re.I),
    re.compile(r'\balt="([^"]*)"'),
    re.compile(r'\btitle="([^"]*)"'),
]


def build_names(open_q, close_q):
    """名称语境里：引号内 ≤4 词且不以句末标点结尾 → 去掉引号。"""
    return re.compile(re.escape(open_q) + r"([^" + re.escape(close_q) + r"]{1,70}?)" + re.escape(close_q))


def name_pass(s, pairs):
    """名称语境去引号。返回 (新文本, 命中数)。"""
    hits = 0

    def fix_inner(inner):
        nonlocal hits
        for a, b in pairs:
            rx = build_names(a, b)

            def repl(mm):
                nonlocal hits
                span = mm.group(1)
                # ⚠️ CJK（ja/ko）无空格，按词数判会「长句=1 词」而误伤正当引用
                #    → 再加字符长度护栏
                if len(span) > 28 or len(span.split()) > 4:
                    return mm.group(0)
                if span.rstrip().endswith((".", "!", "?", "\u2026", "\u3002", "\uff01", "\uff1f")):
                    return mm.group(0)
                hits += 1
                return span.strip()
            inner = rx.sub(repl, inner)
        return inner

    for rx_ctx in NAME_CTX:
        out, pos = [], 0
        for m in rx_ctx.finditer(s):
            out.append(s[pos:m.start()])
            head = m.group(0)[:m.start(1) - m.start(0)]
            tail = m.group(0)[m.end(1) - m.start(0):]
            out.append(head + fix_inner(m.group(1)) + tail)
            pos = m.end()
        out.append(s[pos:])
        s = "".join(out)
    return s, hits


def build(open_q, close_q):
    # 引号内允许前后各有一个空格（fr/es 的 « X » 写法）
    return re.compile(re.escape(open_q) + r"[ \u00a0]*(" + TERM + r")[ \u00a0]*" + re.escape(close_q))


def pages(lg):
    for sub in DIRS:
        base = os.path.join(ROOT, lg, sub) if sub else os.path.join(ROOT, lg)
        for f in sorted(glob.glob(os.path.join(base, "*.html"))):
            yield f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--names", action="store_true", help="额外在名称语境（title/h1/h2/h4/alt/title 属性）去引号")
    args = ap.parse_args()

    grand = Counter()
    files_hit = defaultdict(int)
    samples = []
    for lg, q in QUOTES.items():
        pairs = [q] + EXTRA.get(lg, [])
        rxs = [build(a, b) for a, b in pairs]
        for f in pages(lg):
            s = open(f, encoding="utf-8", errors="ignore").read()
            orig = s
            hit = False
            for rx in rxs:
                for m in rx.finditer(s):
                    grand[m.group(1)] += 1
                    hit = True
                    if args.list and len(samples) < 200:
                        samples.append((os.path.relpath(f, ROOT), m.group(0)))
                s = rx.sub(lambda m: m.group(1), s)
            if args.names:
                s, nh = name_pass(s, pairs)
                if nh:
                    grand["<名称语境>"] += nh
                    hit = True
            if hit and s != orig:
                files_hit[lg] += 1
                if args.apply:
                    open(f, "w", encoding="utf-8").write(s)
            elif hit:
                files_hit[lg] += 1

    print("命中术语引号：%d 处，涉及 %d 个文件" % (sum(grand.values()), sum(files_hit.values())))
    print("按语言:", dict(files_hit))
    print("Top 30：")
    for k, v in grand.most_common(30):
        print("   %5d  %s" % (v, k))
    if args.list:
        print("\n样例：")
        for rel, frag in samples[:40]:
            print("   %-46s %s" % (rel, frag))
    if args.apply:
        print("\n模式: 落盘")
    return 0


if __name__ == "__main__":
    sys.exit(main())
