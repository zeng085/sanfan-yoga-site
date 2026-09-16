#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对照「meta description」与「JSON-LD description」，判断被截断的描述能否从结构化数据里恢复。

背景：fix_desc_unique.py（09-12）只裁了 meta 三处（description / og / twitter），
**没碰 JSON-LD**，所以结构化数据里往往还留着截断前的完整原文 ——
如果能逐页对上，修断头句就不用重写文案，直接回灌 JSON-LD 原文即可。

用法：
    python3 probe_desc_jsonld.py            # 全站，只看「meta 断头」的页
    python3 probe_desc_jsonld.py --all      # 所有页
"""
import glob
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESC_RE = re.compile(r'<meta name="description" content="([^"]*)"')
JSONLD_RE = re.compile(r'"description"\s*:\s*"((?:[^"\\]|\\.)*)"')
OK_END = ".!?。！？：；:;…»”\"')）"
LANGS = ("de", "ja", "ko", "fr", "it", "es")


def W(s):
    return sum(2 if ord(c) > 0x2E80 else 1 for c in s)


def main():
    only_dangling = "--all" not in sys.argv
    os.chdir(ROOT)
    stat = {"same": 0, "longer": 0, "shorter": 0, "prefix": 0}
    rows = []
    for f in sorted(glob.glob("**/*.html", recursive=True)):
        with open(f, encoding="utf-8", errors="replace") as fh:
            s = fh.read(60000)
        m = DESC_RE.search(s)
        if not m:
            continue
        meta = html.unescape(m.group(1)).strip()
        if only_dangling and meta and meta[-1] in OK_END:
            continue
        jl = [html.unescape(x).replace("\\/", "/").strip() for x in JSONLD_RE.findall(s)]
        # 取最长的 JSON-LD 描述作候选原文
        cand = max(jl, key=len) if jl else ""
        flag = ""
        if not cand:
            flag = "无JSON-LD"
        elif cand == meta:
            flag = "=同文"
            stat["same"] += 1
        elif cand.startswith(meta):
            flag = "meta是前缀"
            stat["prefix"] += 1
        elif meta.endswith(cand) or cand in meta:
            flag = "json在meta内"
        elif len(cand) > len(meta):
            flag = "json更长"
            stat["longer"] += 1
        else:
            flag = "json更短"
            stat["shorter"] += 1
        rows.append((flag, f, meta, cand))
    print("统计:", stat)
    for flag, f, m, c in sorted(rows):
        print("%-10s %-56s meta[%3d] json[%3d]" % (flag, f, W(m), W(c)))
        if flag.startswith("json更长") or flag.startswith("meta是前缀"):
            print("      meta: …%s" % m[-70:])
            print("      json: …%s" % c[-70:])


if __name__ == "__main__":
    main()
