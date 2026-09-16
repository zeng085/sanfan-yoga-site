#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""描述长度分析（2026-09-17）：desc >155 展示宽的有多少、其中多少能**在句末安全裁剪**。

【背景】
335 之前的验收脚本 ⑤ 用**未解码**的原始串量宽，实体被算成多字符，
加上 ② 的 DOCTYPE 误报，两个数字都失真。修好度量后露出真实问题：
1331 页里有 806 页 description 超过 155 展示宽（Google 截断线），
fr/it 中位数已到 196/198 —— 这是典型的**译文膨胀**（法/意比英语长 15~30%）。

【判据】
· 只在**句末**裁：`.!?。！？` 后接 空格+大写/假名/汉字/谚文/引号/括号。
  绝不在词中硬切 —— 硬切会让末字符变成字母，直接违反验收指标 ①
  （描述尾部悬空：末字符必须在 `.!?。！？：；:;…»"')）` 里）。
· 裁完至少留 90 宽，避免把 200 宽的句子砍成 100 宽的残句。
· 小数（`45x13.5 cm`）不会误判：`.` 后必须跟空格+大写才算句末。

用法：
    python3 analyze_desc_len.py            # 只统计
    python3 analyze_desc_len.py --show 5   # 多打几条例样
"""
import collections
import glob
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["", "de", "ja", "ko", "fr", "it", "es"]
DIRS = ["", "products", "applications", "blog", "pilates"]
BUDGET = 155
MIN_KEEP = 90

# 句末断点：标点后可以有空白，再跟「像是新句开头」的字符。
# 不以「小写字母」为界，是为了避开 `e.g.` / `i.e.` / `45x13.5 cm` 这类。
SENT = re.compile(
    r"(?<=[.!?\u3002\uff01\uff1f])\s*"
    r"(?=[A-Z\u00c0-\u00de\u3040-\u30ff\u4e00-\u9fff\uac00-\ud7af\u300c\u300e\u201c(])"
)

W = lambda s: sum(2 if ord(c) > 0x2E80 else 1 for c in s)


def pages():
    for lg in LANGS:
        for sub in DIRS:
            base = os.path.join(ROOT, lg, sub) if sub else (os.path.join(ROOT, lg) if lg else ROOT)
            for f in sorted(glob.glob(os.path.join(base, "*.html"))):
                yield lg or "EN", f


def main():
    show = 5
    if "--show" in sys.argv:
        show = int(sys.argv[sys.argv.index("--show") + 1])

    over = collections.Counter()
    safe, nosafe, ok = [], [], 0
    for lg, f in pages():
        s = open(f, encoding="utf-8", errors="ignore").read()
        m = re.search(r'<meta name="description" content="([^"]*)"', s)
        if not m:
            continue
        dec = html.unescape(m.group(1))
        w = W(dec)
        if w <= BUDGET:
            ok += 1
            continue
        over[lg] += 1

        cut = None
        for mm in SENT.finditer(dec):
            if W(dec[:mm.start()]) <= BUDGET:
                cut = mm.start()
        if cut is None or W(dec[:cut]) < MIN_KEEP:
            nosafe.append((lg, w, os.path.relpath(f, ROOT), dec))
        else:
            safe.append((lg, w, W(dec[:cut]), os.path.relpath(f, ROOT), dec, cut))

    print("description 展示宽（解码后）：合规 %d | 超 %d 宽 %d" % (ok, BUDGET, sum(over.values())))
    print("  超限分布 %s" % dict(over))
    print("  可句末安全裁剪 %d 页 | 无断点或会剪太短 %d 页" % (len(safe), len(nosafe)))
    if safe:
        print("  可裁剪分布 %s" % dict(collections.Counter(x[0] for x in safe)))
        print("\n--- 裁剪样例（原宽 → 新宽）---")
        for lg, w0, w1, rel, dec, cut in sorted(safe, key=lambda x: -x[1])[:show]:
            print("  [%s] %d → %d  %s" % (lg, w0, w1, rel))
            print("     原: %s" % dec[:190])
            print("     新: %s" % dec[:cut])
    if nosafe:
        print("\n--- 无法安全裁剪样例 ---")
        for lg, w, rel, dec in nosafe[:show]:
            print("  [%s] w=%d  %s\n     %s" % (lg, w, rel, dec[:150]))


if __name__ == "__main__":
    main()
