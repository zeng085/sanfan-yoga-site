#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""列出所有 title 超预算的页面，并排显示其 EN 源页 title —— 用于判断
「超长是机翻膨胀」还是「EN 源本身就超长」。

输出 /tmp/over_titles.txt（人读）与 /tmp/over_titles.tsv（机读）。
"""
import glob
import html
import os
import re
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
DIRS = ["", "products", "applications", "blog", "pilates"]
T_BUDGET = 60
TITLE_RE = re.compile(r"<title>([\s\S]*?)</title>")


def W(s):
    return sum(2 if ord(c) > 0x2E80 else 1 for c in s)


def plain(h):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def get_title(path):
    try:
        s = open(path, encoding="utf-8", errors="ignore").read()
    except OSError:
        return None
    m = TITLE_RE.search(s)
    return plain(m.group(1)) if m else None


def all_pages():
    out = []
    for lg in [""] + LANGS:
        for sub in DIRS:
            base = ROOT if lg == "" else os.path.join(ROOT, lg)
            pat = os.path.join(base, sub, "*.html") if sub else os.path.join(base, "*.html")
            for f in sorted(glob.glob(pat)):
                out.append((lg or "en", f))
    return out


def main():
    pages = all_pages()
    with ThreadPoolExecutor(max_workers=16) as ex:
        titles = list(ex.map(lambda p: get_title(p[1]), pages))

    en_by_rel = {}
    for (lg, f), t in zip(pages, titles):
        if lg == "en":
            en_by_rel[os.path.relpath(f, ROOT)] = t

    rows = []
    for (lg, f), t in zip(pages, titles):
        if t is None:
            continue
        rel = os.path.relpath(f, ROOT)
        if W(t) <= T_BUDGET:
            continue
        # EN 对照：去掉语言前缀
        en_rel = rel if lg == "en" else "/".join(rel.split("/")[1:])
        en_t = en_by_rel.get(en_rel)
        rows.append((W(t), lg, rel, t, W(en_t) if en_t else -1, en_t or ""))

    rows.sort(key=lambda r: (-r[0], r[1]))
    by_lang = {}
    for w, lg, rel, t, we, en_t in rows:
        by_lang.setdefault(lg, []).append(w)

    with open("/tmp/over_titles.txt", "w", encoding="utf-8") as fo:
        fo.write("title 超 %d 宽：共 %d 页\n" % (T_BUDGET, len(rows)))
        for lg in sorted(by_lang):
            ws = by_lang[lg]
            fo.write("  %-3s %3d 页  最宽 %d\n" % (lg, len(ws), max(ws)))
        fo.write("\n")
        for w, lg, rel, t, we, en_t in rows:
            fo.write("[%3d] %-3s %s\n" % (w, lg, rel))
            fo.write("      T: %s\n" % t)
            if lg != "en":
                fo.write("   EN[%3d]: %s\n" % (we, en_t))
            fo.write("\n")

    with open("/tmp/over_titles.tsv", "w", encoding="utf-8") as fo:
        for w, lg, rel, t, we, en_t in rows:
            fo.write("%d\t%s\t%s\t%s\t%d\t%s\n" % (w, lg, rel, t, we, en_t))
    print("dumped %d rows" % len(rows))


if __name__ == "__main__":
    main()
