#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把超长 title 拆成「主体 + 品牌后缀」，按主体宽度分档 —— 决定修法。

Google 截断是**从尾部砍**：
  · 主体自身 ≥60 宽 → 截断后只剩主体，观感正常（品牌不可见，但无残字）
  · 主体 52–59 宽 → 后缀被砍成 "— SANF" / "— S"，**难看的半截品牌**
  · 主体 <52 宽 → 后缀几乎完整可见，属于「长度轻微超出」，优先级最低

所以真正该动手的是中间那档。输出 /tmp/title_split.txt
"""
import html
import os
import re
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LANGS = ["", "de", "ja", "ko", "fr", "it", "es"]
DIRS = ["", "products", "applications", "blog", "pilates"]
BUDGET = 60
TITLE_RE = re.compile(r"<title>([\s\S]*?)</title>")
SEP = r"(?:[—–|]|&#124;|&vert;|&#x7c;|&brvbar;)"
TAIL_RE = re.compile(r"([\s\S]*)\s+" + SEP + r"\s+([^<>—–|]*)$")


def W(s):
    return sum(2 if ord(c) > 0x2E80 else 1 for c in s)


def plain(h):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def load(path):
    try:
        s = open(path, encoding="utf-8", errors="ignore").read()
    except OSError:
        return None
    m = TITLE_RE.search(s)
    return plain(m.group(1)) if m else None


def main():
    pages = []
    for lg in LANGS:
        for sub in DIRS:
            base = ROOT if lg == "" else os.path.join(ROOT, lg)
            pat = os.path.join(base, sub, "*.html") if sub else os.path.join(base, "*.html")
            for f in sorted(__import__("glob").glob(pat)):
                pages.append((lg or "en", f))
    with ThreadPoolExecutor(max_workers=16) as ex:
        titles = list(ex.map(lambda p: load(p[1]), pages))

    bands = {"A 主体≥60（优雅截断）": [], "B 主体52-59（半截品牌）": [],
             "C 主体43-51（轻微超出）": [], "D 主体<43（后缀完整）": []}
    for (lg, f), t in zip(pages, titles):
        if t is None or W(t) <= BUDGET:
            continue
        rel = os.path.relpath(f, ROOT)
        m = TAIL_RE.match(t)
        if m and "SANFAN" in html.unescape(m.group(2)).upper():
            body, suffix = m.group(1).strip(), m.group(2).strip()
        else:
            body, suffix = t, ""
        bw, sw = W(body), W(" — " + suffix) if suffix else 0
        rec = (bw, sw, lg, rel, t, body, suffix)
        if bw >= 60:
            bands["A 主体≥60（优雅截断）"].append(rec)
        elif bw >= 52:
            bands["B 主体52-59（半截品牌）"].append(rec)
        elif bw >= 43:
            bands["C 主体43-51（轻微超出）"].append(rec)
        else:
            bands["D 主体<43（后缀完整）"].append(rec)

    with open("/tmp/title_split.txt", "w", encoding="utf-8") as fo:
        fo.write("超长 title 按「主体宽度」分档（预算 %d）\n\n" % BUDGET)
        for k in ["A 主体≥60（优雅截断）", "B 主体52-59（半截品牌）",
                  "C 主体43-51（轻微超出）", "D 主体<43（后缀完整）"]:
            v = bands[k]
            fo.write("%s：%d 条\n" % (k, len(v)))
        fo.write("\n" + "=" * 100 + "\n\n")
        for k in ["B 主体52-59（半截品牌）", "A 主体≥60（优雅截断）",
                  "C 主体43-51（轻微超出）", "D 主体<43（后缀完整）"]:
            v = sorted(bands[k])
            fo.write("\n### %s（%d）\n" % (k, len(v)))
            for bw, sw, lg, rel, t, body, suffix in v:
                fo.write("  主体[%3d] 后缀[%2d] %-3s %s\n" % (bw, sw, lg, rel))
                fo.write("      %s\n" % t)
            fo.write("\n")
    for k, v in bands.items():
        print("%-24s %d" % (k, len(v)))


if __name__ == "__main__":
    main()
