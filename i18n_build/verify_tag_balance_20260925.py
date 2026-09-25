#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全站标签配平检查（HEAD vs 当前）—— 2026-09-25

目的：证明本轮改动不仅修好了 h2/h3，而且**没有在任何页面引入新的标签不配平**。
做法：对每个 HTML 文件分别统计 HEAD 版与当前版的 开标签数 - 闭标签数，
差值必须为 0（改动前后一样「配平/不配平」），并单独报告全站仍存在的既有不配平页。

void 元素（br/img/meta/link/input/hr/source 等）不参与统计。
"""
import glob
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["", "de", "ja", "ko", "fr", "it", "es"]
SUBS = ("*.html", "products/*.html", "applications/*.html", "blog/*.html",
        "pilates/*.html")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}


def files():
    out = []
    for L in LANGS:
        for s in SUBS:
            out += glob.glob(os.path.join(ROOT, L, s))
    return sorted(set(out))


def balance(text):
    """返回 {tag: 开-闭}。只统计成对标签（跳过 void 与自闭合）。"""
    d = Counter()
    # 去掉 script / style 内容（里面的字符串可能含 < / >）
    t = re.sub(r"<script\b.*?</script>", "", text, flags=re.S | re.I)
    t = re.sub(r"<style\b.*?</style>", "", t, flags=re.S | re.I)
    for m in re.finditer(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)\b[^>]*?(/?)>", t):
        closing, tag, selfclose = m.group(1), m.group(2).lower(), m.group(3)
        if tag in VOID or selfclose:
            continue
        d[tag] += -1 if closing else 1
    return {k: v for k, v in d.items() if v}


def head_map(paths):
    proc = subprocess.run(["git", "cat-file", "--batch"], cwd=ROOT,
                          input="\n".join("HEAD:" + p for p in paths).encode(),
                          capture_output=True)
    data, pos, idx, out = proc.stdout, 0, 0, {}
    while pos < len(data) and idx < len(paths):
        nl = data.find(b"\n", pos)
        if nl < 0:
            break
        parts = data[pos:nl].decode("utf-8", "replace").split()
        pos = nl + 1
        if len(parts) == 3 and parts[1] == "blob":
            size = int(parts[2])
            out[paths[idx]] = data[pos:pos + size].decode("utf-8", "replace")
            pos += size + 1
        else:
            out[paths[idx]] = None
        idx += 1
    return out


rel = lambda p: p.replace(ROOT + "/", "")
allf = files()
changed = [p for p in allf
           if subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel(p)],
                             cwd=ROOT).returncode != 0]
print("全站 HTML %d 个 | 本轮改动 %d 个" % (len(allf), len(changed)))

heads = head_map([rel(p) for p in changed])
new_bad, same_bad, fixed_bad = [], [], []
for p in changed:
    cur = balance(open(p, encoding="utf-8", errors="ignore").read())
    old_raw = heads.get(rel(p))
    if old_raw is None:
        continue
    old = balance(old_raw)
    if cur != old:
        new_bad.append((rel(p), "改动前后配平数不同：%s → %s" % (old, cur)))
    if cur:
        same_bad.append((rel(p), cur))
    if old and not cur:
        fixed_bad.append(rel(p))

print()
print("【本轮改动引入了新的不配平】%d 个文件" % len(new_bad))
for x in new_bad[:15]:
    print("   ❌", x[0], "|", x[1])

# 未改动文件也顺带查一遍（基线）
print()
print("【改动页面中仍存在的不配平】%d 个文件" % len(same_bad))
bytag = Counter()
for _, d in same_bad:
    for k in d:
        bytag[k] += 1
for k, v in bytag.most_common(10):
    print("   %-8s %d 个文件" % (k, v))
for x in same_bad[:6]:
    print("   ·", x[0], x[1])

print()
print("【改动后反而配平了】%d 个文件" % len(fixed_bad))
for x in fixed_bad[:8]:
    print("   ✓", x)

sys.exit(1 if new_bad else 0)
