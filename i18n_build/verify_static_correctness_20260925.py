#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本轮改动的静态正确性校验（2026-09-25）

四组检查，全部可机械判定：
  1. 11 个高权重页的 description —— 宽度、4 处一致性、JSON-LD 可解析
  2. 70 个 A2 文件 —— cat-head 容器完整、cat-title 在其内、div 配平
  3. 9 个 A5 文件 —— button 属性和数量、无残留空 href 的 <a>
  4. 全站 JSON-LD —— 每块必须能 json.loads（desc 改动动了 JSON-LD 内容）
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["", "de", "ja", "ko", "fr", "it", "es"]
SUBS = ("*.html", "products/*.html", "applications/*.html", "blog/*.html",
        "pilates/*.html")


def files(lang=""):
    out = []
    for s in SUBS:
        out += glob.glob(os.path.join(ROOT, lang, s))
    return out


def width(s):
    return sum(2 if ord(c) > 0x2E80 else 1 for c in s)


def read(p):
    with open(p, encoding="utf-8", errors="ignore") as fh:
        return fh.read()


print("=" * 74)
print("① 11 个高权重页 description")
print("=" * 74)
DESC_PAGES = [
    "applications/index.html", "applications/recovery-physio.html",
    "applications/retail-private-label.html", "applications/gyms-fitness-clubs.html",
    "applications/yoga-pilates-studios.html", "applications/hotels-resorts-spas.html",
    "yoga-props-accessories.html", "strength-training.html", "massage-recovery.html",
    "foam-rollers.html", "resistance-bands.html",
]
RE_META = re.compile(r'<meta\s+name="description"\s+content="([^"]*)"', re.I)
RE_PROP = re.compile(r'<meta\s+property="og:description"\s+content="([^"]*)"', re.I)
RE_TW = re.compile(r'<meta\s+name="twitter:description"\s+content="([^"]*)"', re.I)
RE_JD = re.compile(r'"description"\s*:\s*"([^"]*)"')
bad1 = []
for rel in DESC_PAGES:
    p = os.path.join(ROOT, rel)
    s = read(p)
    meta = RE_META.search(s)
    og = RE_PROP.search(s)
    tw = RE_TW.search(s)
    jd = [m.group(1) for m in RE_JD.finditer(s)
          if "Vertically integrated OEM/ODM manufacturer" not in m.group(1)]
    if not meta:
        bad1.append((rel, "无 meta description"))
        continue
    w = width(meta.group(1))
    flags = []
    if w > 160:
        flags.append("超 160 宽(%d)" % w)
    if w < 120:
        flags.append("不足 120 宽(%d)" % w)
    for label, m in (("og", og), ("twitter", tw)):
        if not m:
            flags.append("缺 %s" % label)
        elif m.group(1).strip() != meta.group(1).strip():
            flags.append("%s 与 meta 不一致" % label)
    for d in jd:
        if d.strip() != meta.group(1).strip():
            flags.append("JSON-LD 与 meta 不一致: %s" % d[:40])
    if not jd:
        flags.append("无页面级 JSON-LD description")
    print("  %-44s %3d 宽  4处=%s  %s"
          % (rel, w, "一致" if not flags else "❌", "; ".join(flags)))
    if flags:
        bad1.append((rel, "; ".join(flags)))
print("  → 异常 %d 页" % len(bad1))

print()
print("=" * 74)
print("② 70 个 A2 文件（cat-head -> div.cat-title）")
print("=" * 74)
A2_PAGES = ["foam-rollers.html", "jump-ropes.html", "massage-recovery.html",
            "meditation-pilates-mats.html", "pu-rubber-yoga-mats.html",
            "resistance-bands.html", "strength-training.html",
            "suede-cork-yoga-mats.html", "tpe-yoga-mats.html",
            "yoga-props-accessories.html"]
bad2, n2 = [], 0
for L in LANGS:
    for name in A2_PAGES:
        p = os.path.join(ROOT, L, name) if L else os.path.join(ROOT, name)
        if not os.path.exists(p):
            bad2.append((p, "文件不存在"))
            continue
        s = read(p)
        n2 += 1
        ch = s.count('<div class="cat-head">')
        ct = s.count('<div class="cat-title">')
        if ch != 1:
            bad2.append((p, "cat-head 容器数 %d（应 1）" % ch))
        if ct != 1:
            bad2.append((p, "cat-title 数 %d（应 1）" % ct))
        if not re.search(r'<div class="cat-head">\s*<div class="cat-title"', s):
            bad2.append((p, "cat-title 不在 cat-head 内"))
        if s.count("<div") != s.count("</div>"):
            bad2.append((p, "div 不配平 %d/%d" % (s.count("<div"), s.count("</div>"))))
        if re.search(r'<div class="cat-head">\s*<h3\b', s):
            bad2.append((p, "cat-head 内仍有 h3"))
print("  检查 %d 个文件 → 异常 %d 项" % (n2, len(bad2)))
for b in bad2[:10]:
    print("   ❌", b[0].replace(ROOT + "/", ""), b[1])

print()
print("=" * 74)
print("③ A5 语言切换按钮（EN 9 篇 blog）")
print("=" * 74)
bad3, n3, btn_total = [], 0, 0
for f in sorted(glob.glob(os.path.join(ROOT, "blog", "*.html"))):
    s = read(f)
    n3 += 1
    a_nohref = [m.group(0) for m in re.finditer(r'<a\b[^>]*data-setlang[^>]*>', s)
                if "href" not in m.group(0)]
    btns = re.findall(r'<button\b[^>]*data-setlang[^>]*>', s)
    btn_total += len(btns)
    if a_nohref:
        bad3.append((f, "残留空 href <a data-setlang> %d 个" % len(a_nohref)))
    # 属性保留：原 <a> 上的 title 必须还在 button 上
    for b in btns:
        if 'data-setlang="en"' in b or 'data-setlang="zh"' in b:
            if "title=" not in b:
                bad3.append((f, "button 缺 title: %s" % b[:60]))
    if len(btns) != 2:
        bad3.append((f, "button 数 %d（应 2）" % len(btns)))
print("  检查 %d 篇 blog（剥前）→ 按钮 %d 个 / 异常 %d 项" % (n3, btn_total, len(bad3)))
for b in bad3[:10]:
    print("   ❌", os.path.basename(b[0]), b[1])

print()
print("=" * 74)
print("④ 全站 JSON-LD 可解析性")
print("=" * 74)
RE_LD = re.compile(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
                   re.S | re.I)
npage = nblock = 0
bad4 = []
for L in LANGS:
    for p in files(L):
        s = read(p)
        npage += 1
        for i, m in enumerate(RE_LD.finditer(s)):
            nblock += 1
            raw = m.group(1).strip()
            try:
                json.loads(raw)
            except Exception as e:                                # noqa: BLE001
                bad4.append((p.replace(ROOT + "/", ""), i, str(e)[:60]))
print("  检查 %d 页 / %d 个 JSON-LD 块 → 解析失败 %d 个" % (npage, nblock, len(bad4)))
for b in bad4[:10]:
    print("   ❌", b[0], "块#%d" % b[1], b[2])

total = len(bad1) + len(bad2) + len(bad3) + len(bad4)
print()
print("=" * 74)
print("合计异常：%d 项 %s" % (total, "✓" if total == 0 else "← 需处理"))
print("=" * 74)
sys.exit(1 if total else 0)
