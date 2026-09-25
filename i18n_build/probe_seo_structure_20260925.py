#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A1-A5 结构类改动的前置形态核查（只读，不写任何文件）。

用途：在动手改标签前，把 7 个语言版本的真实形态查清 —— 上一轮吃过
「用 EN x 7 推断语言版」的亏（三处全错），这次全部实测。

输出：
  A1 products/*.html 的 <div class="pd-specs"> 后紧跟标签分布
  A2 含 cat-head h3 的文件 + 层级顺序（判断哪些是真缺陷、哪些是反例）
  A3 faq.html 的 h2 / h3.faq-cat 计数
  A4 blog.html 的 h2 / h3 计数（剥中文块后）
  A5 blog/*.html 的无 href <a data-setlang>
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_en_seo_standard_20260925 import strip_zh  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["", "de", "ja", "ko", "fr", "it", "es"]

RE_SPECS = re.compile(r'<div class="pd-specs">\s*<(h[0-9])\b')
RE_CATHEAD = re.compile(r'<div class="cat-head">\s*<(h[0-9])\b')
RE_H2 = re.compile(r'<h2\b', re.I)
RE_H3 = re.compile(r'<h3\b', re.I)
RE_FAQ_CAT = re.compile(r'<h([0-9]) class="faq-cat"')
RE_SETLANG = re.compile(r'<a\b[^>]*data-setlang[^>]*>', re.I)


def read(path):
    with open(path, encoding="utf-8", errors="ignore") as fh:
        return fh.read()


def ls(lang, sub=""):
    """该语言下某目录的 .html 绝对路径列表（只扫一层，避免全站递归）。"""
    d = os.path.join(ROOT, lang, sub) if lang else os.path.join(ROOT, sub)
    if not os.path.isdir(d):
        return []
    return [os.path.join(d, n) for n in sorted(os.listdir(d)) if n.endswith(".html")]


def rel(p):
    return os.path.relpath(p, ROOT)


print("=" * 78)
print("A1  products/*.html —— <div class=\"pd-specs\"> 后紧跟的标签")
print("=" * 78)
print("%-4s %6s %6s %6s   %s" % ("lang", "<h3", "<h2", "无specs", "样本(前2个 h3 页)"))
a1_total = 0
for L in LANGS:
    fs = ls(L, "products")
    n3 = n2 = nn = 0
    samples = []
    for f in fs:
        m = RE_SPECS.search(read(f))
        if not m:
            nn += 1
        elif m.group(1) == "h3":
            n3 += 1
            if len(samples) < 2:
                samples.append(os.path.basename(f))
        else:
            n2 += 1
    a1_total += n3
    print("%-4s %6d %6d %6d   %s" % (L or "en", n3, n2, nn, ", ".join(samples)))
print("  合计 h3 页数 =", a1_total)

print()
print("=" * 78)
print('A2  <div class="cat-head"> 内的标题标签 + 层级顺序（剥中文块后判定）')
print("=" * 78)


def norm(relpath):
    """去掉语言前缀，用于跨语言聚合（de/foo.html -> foo.html）。"""
    parts = relpath.split("/")
    if parts[0] in ("de", "ja", "ko", "fr", "it", "es"):
        parts = parts[1:]
    return "/".join(parts)


a2_fix, a2_keep = {}, {}
for L in LANGS:
    # cat-head 只存在于顶层分类页与 applications/，不扫 products/（1029 个文件、且无 cat-head）
    for sub in ("", "applications"):
        for f in ls(L, sub):
            s = read(f)
            if '<div class="cat-head">' not in s:      # 快速预筛，避免无谓的 strip_zh
                continue
            m = RE_CATHEAD.search(s)
            if not m:
                continue
            t = strip_zh(s)
            h2, h3 = RE_H2.search(t), RE_H3.search(t)
            bad = bool(h3 and (not h2 or h3.start() < h2.start()))
            key = (norm(rel(f)), m.group(1))
            (a2_fix if bad else a2_keep).setdefault(key, []).append(L or "en")

print("-- 需改（H1 之后直接跟 cat-head，跳过了 H2）--")
for (k, tag), langs in sorted(a2_fix.items()):
    print("   %-46s <%s>  %d 语言" % (k, tag, len(langs)))
print("   小计 %d 个文件模式" % len(a2_fix))
print()
print("-- 保持（反例：前面已有 H2，层级正确，勿动）--")
for (k, tag), langs in sorted(a2_keep.items()):
    print("   %-46s <%s>  %d 语言 %s" % (k, tag, len(langs), ",".join(langs)))
print("   小计 %d 个文件模式" % len(a2_keep))

print()
print("=" * 78)
print("A3  faq.html —— 剥中文块后的 h2 / h3.faq-cat + 那个 h2 的文案")
print("=" * 78)
print("%-4s %6s %11s %11s   %s" % ("lang", "h2", "h3.faq-cat", "h2.faq-cat", "h2 文案"))
for L in LANGS:
    p = os.path.join(ROOT, L, "faq.html")
    if not os.path.exists(p):
        print("%-4s  (不存在)" % (L or "en"))
        continue
    t = strip_zh(read(p))
    n2 = len(RE_H2.findall(t))
    n3c = len(re.findall(r'<h3 class="faq-cat"', t))
    n2c = len(re.findall(r'<h2 class="faq-cat"', t))
    txt = []
    for m in re.finditer(r"<h2\b[^>]*>(.*?)</h2>", t, re.S | re.I):
        txt.append(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip()[:44])
    print("%-4s %6d %11d %11d   %s"
          % (L or "en", n2, n3c, n2c, " | ".join(txt) or "(无)"))

print()
print("=" * 78)
print("A4  blog.html —— 剥中文块后的 h2 / h3 计数 + 原始 h2 的标签原文")
print("=" * 78)
print("%-4s %6s %6s %6s %6s   %s" % ("lang", "h2", "h3", "原始h2", "原始h3", "备注"))
for L in LANGS:
    p = os.path.join(ROOT, L, "blog.html")
    if not os.path.exists(p):
        print("%-4s  (不存在)" % (L or "en"))
        continue
    s = read(p)
    t = strip_zh(s)
    n2, n3 = len(RE_H2.findall(t)), len(RE_H3.findall(t))
    o2, o3 = len(RE_H2.findall(s)), len(RE_H3.findall(s))
    note = "整页无 h2 ★需改" if n2 == 0 else ""
    print("%-4s %6d %6d %6d %6d   %s" % (L or "en", n2, n3, o2, o3, note))

print()
print("-- EN blog.html 的原始 h2 标签原文（看它是不是被 lang-zh 包住）--")
_s = read(os.path.join(ROOT, "blog.html"))
for m in re.finditer(r"<h2\b[^>]*>.*?</h2>", _s, re.S | re.I):
    print("   ..%s.." % re.sub(r"\s+", " ", _s[max(0, m.start() - 90):m.end() + 30]))
print()
print("-- EN blog.html 剥块后的 10 个 h3 文案（前 3 个）--")
_t = strip_zh(_s)
for i, m in enumerate(re.finditer(r"<h3\b[^>]*>(.*?)</h3>", _t, re.S | re.I)):
    if i >= 3:
        break
    print("   [%d] %s" % (i + 1, re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip()[:60]))

print()
print("=" * 78)
print("A5  blog/*.html —— 无 href 的 <a data-setlang>")
print("=" * 78)
print("%-4s %8s %8s   %s" % ("lang", "无href", "总a数", "命中文件"))
a5_total = 0
for L in LANGS:
    n_bad = n_all = 0
    hits = []
    for f in ls(L, "blog"):
        s = read(f)
        ms = RE_SETLANG.findall(s)
        n_all += len(ms)
        bad = [x for x in ms if "href" not in x]
        if bad:
            n_bad += len(bad)
            hits.append("%s(%d)" % (os.path.basename(f), len(bad)))
    a5_total += n_bad
    print("%-4s %8d %8d   %s" % (L or "en", n_bad, n_all, ", ".join(hits) or "-"))
print("  合计无 href =", a5_total)
