#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导航栏标记修复（2026-09-16 第二轮）

背景（浏览器实测 + 静态普查）：
  1) 1086 个语言页（de/ja/ko/fr/it/es 各 181 页）的 `<nav class="nav-links">` 里
     多出一个**扁平**的「Pilates」项：
         <a href="/pilates/"><span data-i18n="nav.pilates">Pilates</span></a>
     它有两个问题：
       · 与前面已翻译的下拉项「Pilates-Geräte / ピラティス用器具 / …」重复；
       · href 是 /pilates/（**英文区**），德语页点进去直接跨语言跳走。
     成因：给语言页注入「Pilates 下拉」时只在前插入了新项，忘了删掉旧的英文项。
  2) 54 个器械板块页（每语言 9 页）的 products 文案与主站不一致：
       de「Yogamatten & Zubehör」 vs 主站「Yogamatten & Fitness」…（其余 5 语言同理）
     同一目标同一层级出现两种写法，统一为主站口径（181:9 → 主站为准）。

只改 `<nav class="nav-links">` 内部，绝不碰正文/页脚。
用法：
  python3 fix_nav_20260916.py            # 试运行
  python3 fix_nav_20260916.py --apply    # 落盘
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["de", "ja", "ko", "fr", "it", "es"]

NAV_RX = re.compile(r'(<nav class="nav-links">)(.*?)(</nav>)', re.S)

# ① 要删除的重复项（含其后的空白）
DUP_RX = re.compile(
    r'\s*<a href="/pilates/"><span data-i18n="nav\.pilates">\s*Pilates\s*</span></a>')

# ② 器械板块页 → 主站口径
LABEL = {
    "de": ("Yogamatten &amp; Zubehör", "Yogamatten &amp; Fitness"),
    "ja": ("ヨガマット＆用品", "ヨガマット＆フィットネス"),
    "ko": ("요가 매트 및 용품", "요가 매트 &amp; 피트니스"),
    "fr": ("Tapis et accessoires de yoga", "Tapis de yoga &amp; fitness"),
    "it": ("Tappetini e attrezzatura per lo yoga", "Tappetini yoga &amp; fitness"),
    "es": ("Esterillas y material de yoga", "Esterillas de yoga &amp; fitness"),
}


def rel(p):
    return os.path.relpath(p, ROOT)


def main():
    apply = "--apply" in sys.argv
    dup_files = dup_hits = 0
    lbl_files = lbl_hits = 0
    lbl_detail = {}
    for lg in LANGS:
        for f in sorted(glob.glob(os.path.join(ROOT, lg, "**", "*.html"), recursive=True)):
            s = open(f, encoding="utf-8").read()
            m = NAV_RX.search(s)
            if not m:
                continue
            nav = m.group(2)
            orig = nav

            nav, n1 = DUP_RX.subn("", nav)
            if n1:
                dup_files += 1
                dup_hits += n1

            old, new = LABEL[lg]
            if old in nav:
                n2 = nav.count(old)
                nav = nav.replace(old, new)
                lbl_files += 1
                lbl_hits += n2
                lbl_detail.setdefault(lg, []).append(rel(f))

            if nav != orig:
                if apply:
                    s = s[:m.start(2)] + nav + s[m.end(2):]
                    open(f, "w", encoding="utf-8").write(s)

    print("① 重复「Pilates」项：删除 %d 处 / %d 文件" % (dup_hits, dup_files))
    print("② 器械板块 products 文案统一：%d 处 / %d 文件" % (lbl_hits, lbl_files))
    for lg, fs in lbl_detail.items():
        print("     %s: %d 页  %s" % (lg, len(fs), ", ".join(os.path.basename(x) for x in fs[:4])))
    if not apply:
        print("\n（试运行，未写盘；加 --apply 落盘）")


if __name__ == "__main__":
    main()
