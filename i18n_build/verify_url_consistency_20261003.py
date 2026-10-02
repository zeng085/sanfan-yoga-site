#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""三处 URL 一致性校验器（2026-10-03 新建；把 10-02 的内联检查固化为可复跑脚本）

背景：语言版页面最容易出的不是「翻译错」，而是 **URL 形态自相矛盾**——
同一个页面在 canonical 写文件形态、在 hreflang 写目录形态、在 sitemap 又换一种，
搜索引擎会当成三个不同 URL，等于白做多语言。10-02 就真踩到过
（`update_seo.py` 把 `/de/pilates/` 写成 `/de/pilates/index.html`）。

六道判据（全部针对**页面组**：同一页的 EN + 6 语言版本）：
  ① canonical 必须等于该页自己的规范 URL（目录页必须用目录形态 `/x/`，不带 index.html）
  ② og:url 必须等于 canonical
  ③ hreflang 块必须**八条齐全**（en/de/ja/ko/fr/it/es/x-default），x-default = EN
  ④ hreflang 块必须**组内完全一致**（同一页的 7 个语言版本必须指向同一组 URL）
  ⑤ hreflang 的每个目标必须在本地存在对应文件（缺文件 = 线上 404 的死链）
  ⑥ sitemap 必须含每个成员的 canonical，且形态与 canonical 逐字相同

用法：
    python3 i18n_build/verify_url_consistency_20261003.py                 # 全站多语言页面组
    python3 i18n_build/verify_url_consistency_20261003.py --only-changed  # 只查本次推送清单里的页
退出码：有问题 = 1（可直接当闸）；未发现任何页面组 = 3（拒绝判定为通过）。
"""
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
BASE = "https://fjsanfan.com"
SITEMAP = os.path.join(ROOT, "sitemap.xml")
PUSH_LIST = os.path.join(ROOT, "i18n_build/reports/push_list_20260927.txt")

LINK = re.compile(r"<link\b[^>]*>", re.I)
META = re.compile(r"<meta\b[^>]*>", re.I)
ATTR = re.compile(r'([a-zA-Z:-]+)\s*=\s*"([^"]*)"')
LOC = re.compile(r"<loc>\s*([^<]+?)\s*</loc>")


def attrs(tag):
    return {k.lower(): v for k, v in ATTR.findall(tag)}


def head_of(path):
    """只取 <head>…</head>（避免正文里同名属性污染判据）。"""
    h = open(path, encoding="utf-8").read()
    m = re.search(r"<head\b[^>]*>(.*?)</head>", h, re.S | re.I)
    return m.group(1) if m else h


def parse(path):
    h = head_of(path)
    canonical = ogurl = None
    for t in LINK.findall(h):
        a = attrs(t)
        if a.get("rel", "").lower() == "canonical" and canonical is None:
            canonical = a.get("href")
    for t in META.findall(h):
        a = attrs(t)
        if a.get("property", "").lower() == "og:url" and ogurl is None:
            ogurl = a.get("content")
    alts = {}
    for t in LINK.findall(h):
        a = attrs(t)
        if a.get("rel", "").lower() == "alternate" and a.get("hreflang"):
            alts[a["hreflang"].lower()] = a.get("href")
    return canonical, ogurl, alts


def norm_dir(u):
    """目录形态归一：`.../index.html` → `.../`（与 update_seo.norm_dir 同口径）。"""
    if u.endswith("/index.html"):
        return u[: -len("index.html")]
    return u


def url_of(rel):
    """本地相对路径 → 规范 URL。目录页必须用目录形态。"""
    u = "%s/%s" % (BASE, rel.replace(os.sep, "/"))
    return norm_dir(u)


def discover(changed_only=False):
    """页面组：EN 文件存在，且至少一个语言版本存在。"""
    changed = set()
    if changed_only:
        with open(PUSH_LIST, encoding="utf-8") as f:
            changed = {l.strip() for l in f if l.strip()}
    groups = []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn
                 if d not in (".git", ".workbuddy", "node_modules", "__pycache__",
                              "i18n_build", "outputs", "assets") and d not in LANGS]
        for f in sorted(fn):
            if not f.endswith(".html"):
                continue
            abs_p = os.path.join(dp, f)
            rel = os.path.relpath(abs_p, ROOT)
            if rel.startswith(tuple(x + os.sep for x in LANGS)):
                continue
            members = [rel] + ["%s/%s" % (l, rel) for l in LANGS]
            present = [m for m in members if os.path.isfile(os.path.join(ROOT, m))]
            if len(present) < 2:            # 纯英文页不参与多语言一致性判据
                continue
            if changed_only and not (set(present) & changed):
                continue
            groups.append((rel, present))
    return groups


def main():
    changed_only = "--only-changed" in sys.argv
    groups = discover(changed_only)
    if not groups:
        print("✗ 未发现任何多语言页面组 —— 拒绝判定为通过（退出码 3）")
        return 3
    locs = set(LOC.findall(open(SITEMAP, encoding="utf-8").read()))
    print("多语言页面组 %d 个 / 页面版本 %d 个 / sitemap 条目 %d"
          % (len(groups), sum(len(m) for _, m in groups), len(locs)))
    bad = []
    checked = 0
    for en_rel, members in groups:
        expected_alts = {("en" if m == en_rel else m.split("/")[0]): url_of(m) for m in members}
        expected_alts["x-default"] = url_of(en_rel)
        ref_block = None
        for rel in members:
            checked += 1
            problems = []
            canonical, ogurl, alts = parse(os.path.join(ROOT, rel))
            want = url_of(rel)
            if canonical != want:
                problems.append("canonical 不一致: 实=%s 期=%s" % (canonical, want))
            if ogurl != canonical:
                problems.append("og:url ≠ canonical: %s vs %s" % (ogurl, canonical))
            miss = [k for k in ("en", "de", "ja", "ko", "fr", "it", "es", "x-default")
                    if k not in alts]
            if miss:
                problems.append("hreflang 缺条: %s" % ", ".join(miss))
            xd = alts.get("x-default")
            if xd and xd != url_of(en_rel):
                problems.append("x-default 未指向 EN: %s" % xd)
            if ref_block is None:
                ref_block = alts
            elif alts != ref_block:
                d = {k: (ref_block.get(k), alts.get(k))
                     for k in set(ref_block) | set(alts) if ref_block.get(k) != alts.get(k)}
                problems.append("hreflang 组内不一致: %s" % d)
            # ⑤ hreflang 目标必须落地成文件
            for k, u in alts.items():
                if not u or not u.startswith(BASE):
                    problems.append("hreflang[%s] 非本站: %s" % (k, u))
                    continue
                target = u[len(BASE):].lstrip("/")
                if target == "":
                    target = "index.html"
                cand = os.path.join(ROOT, target)
                if os.path.isdir(cand):
                    cand = os.path.join(cand, "index.html")
                if not os.path.isfile(cand):
                    problems.append("hreflang[%s] 目标不存在: %s" % (k, target))
            # ⑥ sitemap 形态必须与 canonical 逐字相同
            if canonical and canonical not in locs:
                problems.append("sitemap 缺 canonical 原样条目: %s" % canonical)
            if problems:
                bad.append((rel, problems))
    for rel, problems in bad[:40]:
        print("  ✗ %s" % rel)
        for x in problems:
            print("      - %s" % x)
    if len(bad) > 40:
        print("  ... 另有 %d 个" % (len(bad) - 40))
    c = Counter("/".join(r.split("/")[:2]) for r, _ in bad)
    if c:
        print("\n问题分布: " + "  ".join("%s=%d" % (k, v) for k, v in c.most_common(10)))
    print("\n检查 %d 个页面版本，问题 %d 处" % (checked, len(bad)))
    print("结论：%s" % ("三处一致 ✓（canonical / og:url / hreflang / sitemap）"
                       if not bad else "有不一致 ✗"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
