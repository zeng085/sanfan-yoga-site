#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""结构完整性审计（2026-09-16 收尾轮）

只查这三个「本站历史上真踩过」的结构坑，别的不管：

  1 <div> 开合失衡 —— 语言站曾出现 546 页 div 失衡（导航/页脚模板少一个 </div>），
    浏览器会把后面所有内容吞进嵌套层，肉眼看不出来但布局会塌。
  2 <a> 里套 <a> —— 分类页/博客索引历史坑：嵌套 <a> 会被浏览器提前闭合，
     后面的卡片变成空白。判据：<a ...> 与 </a> 之间的片段里还有 <a 。
  3 重复 id —— 同页两个相同 id，#frag 锚点与 JS querySelector 都会走偏。

用法：python3 audit_structure_20260916.py
"""
import glob
import os
import re
from collections import Counter, defaultdict

ROOT = "/Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16"
SKIP = ("/i18n_build", "/outputs", "/.git", "/__pycache__", "/assets")
DIV = re.compile(r"<div\b[^>]*>|</div\s*>", re.I)
A_OPEN = re.compile(r"<a\b[^>]*>", re.I)
A_CLOSE = re.compile(r"</a\s*>", re.I)
ID = re.compile(r'\bid="([^"]+)"')


def pages():
    for f in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True):
        if any(s in f for s in SKIP):
            continue
        yield f


def check_div(s):
    d = 0
    for m in DIV.finditer(s):
        d += -1 if m.group(0).lower().startswith("</") else 1
    return d


def check_nested_a(s):
    depth = 0
    bad = []
    pos = 0
    events = []
    for m in A_OPEN.finditer(s):
        events.append((m.start(), 1, m.group(0)[:60]))
    for m in A_CLOSE.finditer(s):
        events.append((m.start(), -1, "</a>"))
    events.sort()
    for p, k, tag in events:
        if k == 1:
            if depth >= 1:
                bad.append((p, tag))
            depth += 1
        else:
            depth = max(0, depth - 1)
    return bad


def main():
    bad_div = []
    bad_a = defaultdict(list)
    dup_id = defaultdict(list)
    n = 0
    for f in pages():
        s = open(f, encoding="utf-8", errors="ignore").read()
        rel = os.path.relpath(f, ROOT)
        n += 1
        d = check_div(s)
        if d:
            bad_div.append((rel, d))
        na = check_nested_a(s)
        if na:
            bad_a[rel] = na[:2]
        ids = Counter(ID.findall(s))
        dups = {k: v for k, v in ids.items() if v > 1 and not k.startswith("mm-")}
        if dups:
            dup_id[rel] = list(dups.items())[:3]
    print("=" * 68)
    print("结构完整性审计：%d 页" % n)
    print("=" * 68)
    print("\n【1 div 开合失衡】%d 页" % len(bad_div))
    for r, d in bad_div[:12]:
        print("   %-56s 差 %+d" % (r, d))
    print("\n【2 <a> 嵌套】%d 页" % len(bad_a))
    for r, v in list(bad_a.items())[:12]:
        print("   %-56s %s" % (r, v))
    print("\n【3 重复 id】%d 页" % len(dup_id))
    for r, v in list(dup_id.items())[:12]:
        print("   %-56s %s" % (r, v))
    print("\n合计异常：div %d · 嵌套a %d · 重复id %d"
          % (len(bad_div), len(bad_a), len(dup_id)))


if __name__ == "__main__":
    main()
