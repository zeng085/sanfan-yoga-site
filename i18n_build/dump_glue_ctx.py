#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导出 54 页 110 处机翻语法损坏的**上下文**，供逐条确定正确译法。

为什么不能直接正则替换：命中只是线索，正确写法取决于语言的介词/冠词规则，
必须看上下文才能定。例：
  it  "dell’TPE"    → 应为 "del TPE"（TPE 以辅音开头，不缩合）
  it  "in gommPU"   → 应为 "in gomma PU"
  fr  "d’PU"        → 应为 "en PU"
  fr  "sansPVC"     → 应为 "sans PVC"
输出 /tmp/glue_ctx.txt
"""
import glob
import os
import re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
DIRS = ["", "products", "applications", "blog", "pilates"]
TERMS = "TPE|PVC|NBR|EVA|ROHS|REACH|MOQ|OEM|ODM|PU"

RULES = [
    ("apos", re.compile(r"(?:[a-zA-Zà-ÿ]+)?['’](?:%s)\b" % TERMS)),
    ("glue", re.compile(r"\b[a-zà-ÿ]{3,}(?:%s)(?:[a-zà-ÿ]{0,4})?\b" % TERMS)),
    ("upper", re.compile(r"\b(?:(?:REACH|ROHS|MOQ|OEM|ODM)(?:CA|Prop))\b")),
]
FIELD = [
    ("title", re.compile(r"<title>([\s\S]*?)</title>")),
    ("desc", re.compile(r'<meta name="description" content="([^"]*)"')),
    ("h1", re.compile(r"<h1[^>]*>([\s\S]*?)</h1>")),
    ("og", re.compile(r'<meta property="og:title" content="([^"]*)"')),
]
# ⚠️ 大头在**正文**：54 页 110 处里只有 23 处在 meta/h1 字段，其余 87 处在正文。
# 正文才是真实访客看到的（it/pink-mandala 一页正文就有 18 处 dell'TPE）。
SCRIPT_STYLE = re.compile(r"<(script|style)\b[\s\S]*?</\1>", re.I)
HEAD = re.compile(r"<head\b[\s\S]*?</head>", re.I)
TAG = re.compile(r"<[^>]+>")


def body_text(s):
    s = HEAD.sub(" ", s)
    s = SCRIPT_STYLE.sub(" ", s)
    s = TAG.sub(" ", s)
    return re.sub(r"\s+", " ", s)


def main():
    files = []
    for lg in LANGS:
        for sub in DIRS:
            base = os.path.join(ROOT, lg)
            pat = os.path.join(base, sub, "*.html") if sub else os.path.join(base, "*.html")
            files += sorted(glob.glob(pat))

    out = open("/tmp/glue_ctx.txt", "w", encoding="utf-8")
    n = 0
    for f in files:
        try:
            s = open(f, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        rel = os.path.relpath(f, ROOT)
        rows = []
        for fname, rx in FIELD:
            for m in rx.finditer(s):
                txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(1)))
                for label, r in RULES:
                    for g in r.finditer(txt):
                        a, b = max(0, g.start() - 70), min(len(txt), g.end() + 70)
                        rows.append((fname, label, g.group(0), txt[a:b]))
        # 正文：同一 token 只保留首个上下文，避免同一句在整页重复时刷屏
        txt = body_text(s)
        seen = set()
        for label, r in RULES:
            for g in r.finditer(txt):
                key = (label, g.group(0))
                if key in seen:
                    continue
                seen.add(key)
                a, b = max(0, g.start() - 70), min(len(txt), g.end() + 70)
                rows.append(("body", label, g.group(0), txt[a:b]))
        if rows:
            out.write("### %s\n" % rel)
            for fname, label, tok, ctx in rows:
                n += 1
                out.write("  [%s/%s] %-16s …%s…\n" % (fname, label, tok, ctx))
            out.write("\n")
    out.close()
    print("导出 %d 处" % n)


if __name__ == "__main__":
    main()
