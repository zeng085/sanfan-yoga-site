#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""审计 description 尾部是否「断在半句」—— 机翻/截断留下的断头描述。

背景：fr/products/navy-botanical-suede-tpe-yoga-mat.html 的 description 以
"... Les caractéristiques d'adhérence haut de gamme pour" 结尾 —— 一个悬空的
介词短语。这类断头描述在 SERP 上会显示成半句话，比「稍长被 Google 截断」
难看得多，且必属缺陷（正常写的描述不会以介词收尾）。

判据：去掉结尾的引号/空格后，最后一个字符不是句末标点 . ! ? 。 ！ ？ ： ；
      也不是右括号/右引号（"…（SANFAN）" / "…MOQ »" 算正常收尾）。
      同时排除本身就是短语型（长度很短）的描述。

用法：
    python3 audit_desc_tail.py            # 全站
    python3 audit_desc_tail.py fr         # 只看某语言目录前缀
    python3 audit_desc_tail.py --full     # 打印整条描述（默认只打尾部 60 字）
"""
import glob
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESC_RE = re.compile(r'<meta name="description" content="([^"]*)"')
OK_END = ".!?。！？：；:;…»”\"')）"
LANGS = ("de", "ja", "ko", "fr", "it", "es")


def W(s):
    return sum(2 if ord(c) > 0x2E80 else 1 for c in s)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    full = "--full" in sys.argv
    only_en = "--en" in sys.argv
    prefix = args[0] if args else ""
    os.chdir(ROOT)
    rows = []
    total = 0
    for f in sorted(glob.glob("**/*.html", recursive=True)):
        if prefix and not f.startswith(prefix):
            continue
        if only_en and f.split("/")[0] in LANGS:
            continue
        with open(f, encoding="utf-8", errors="replace") as fh:
            head = fh.read(8000)
        m = DESC_RE.search(head)
        if not m:
            continue
        total += 1
        d = html.unescape(m.group(1)).rstrip()
        if not d:
            continue
        if d[-1] not in OK_END:
            rows.append((W(d), f, d if full else "…" + d[-60:]))
    print("审计 %d 页 | 尾部断句 %d 页" % (total, len(rows)))
    print("-" * 100)
    for w, f, tail in sorted(rows):
        print("%3d  %-58s %s" % (w, f, tail))


if __name__ == "__main__":
    main()
