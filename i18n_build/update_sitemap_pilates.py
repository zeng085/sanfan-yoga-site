#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""把 /pilates/ 板块的 URL 补进 sitemap.xml（幂等，可反复跑）。

结构：sitemap 是「EN 块（190 条）→ de 块 → ja 块 → …」（每块内页序相同），
所以器械条目要插两次位置 ——
    · EN 块：紧跟 `products.html` 之后
    · 各语言块：紧跟 `<lang>/products.html` 之后
每块插 9 条 = 1 个板块首页 + 8 个族页。

2026-09-15 变更：器械板块的 6 个语言版（<lang>/pilates/，各 9 页）建成，
所以 hreflang 从「只声明 en + x-default」升级为完整的 7 语言互链，
与页面自身的 <link rel="alternate"> 完全一致。

用法
    python3 i18n_build/update_sitemap_pilates.py --dry-run
    python3 i18n_build/update_sitemap_pilates.py
"""
import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SM = ROOT / "sitemap.xml"
SITE = "https://fjsanfan.com"
LANGS = ["de", "ja", "ko", "fr", "it", "es"]

# (站点相对路径, 英文优先级, 变更频率)
PAGES = [
    ("/pilates/", 1.0, "weekly"),
    ("/pilates/pilates-reformer.html", 0.9, "weekly"),
    ("/pilates/pilates-cadillac.html", 0.8, "weekly"),
    ("/pilates/pilates-wunda-chair.html", 0.8, "weekly"),
    ("/pilates/pilates-ladder-barrel.html", 0.8, "weekly"),
    ("/pilates/pilates-spine-corrector.html", 0.8, "weekly"),
    ("/pilates/pilates-reformer-tower.html", 0.8, "weekly"),
    ("/pilates/pilates-studio-set.html", 0.8, "weekly"),
    ("/pilates/pilates-specialty.html", 0.8, "weekly"),
]
# 语言版沿用站内惯例：priority 0.7、changefreq monthly（与 <lang>/products.html 一致）
LANG_PRIO = 0.7
LANG_FREQ = "monthly"


def lang_path(lg, path):
    """本页在某语言下的路径。板块首页落到目录形式 /de/pilates/。"""
    if path == "/pilates/":
        return "/%s/pilates/" % lg
    return "/%s%s" % (lg, path)


def hreflang_block(path):
    """7 语言 + x-default 互链（与页面 head 里的声明逐条一致）。"""
    en = SITE + path
    rows = ['    <xhtml:link rel="alternate" hreflang="en" href="%s"/>' % en]
    rows += ['    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>'
             % (lg, SITE + lang_path(lg, path)) for lg in LANGS]
    rows.append('    <xhtml:link rel="alternate" hreflang="x-default" href="%s"/>' % en)
    return "\n".join(rows) + "\n"


def entry(path, prio, freq, lg=None):
    u = SITE + (path if lg is None else lang_path(lg, path))
    return ("  <url>\n"
            "    <loc>%s</loc>\n"
            "%s"
            "    <changefreq>%s</changefreq>\n"
            "    <priority>%.1f</priority>\n"
            "  </url>\n" % (u, hreflang_block(path), freq, prio))


def strip_old(t):
    """重跑前先摘掉本脚本此前写入的全部器械条目（EN + 各语言），避免重复。"""
    n = 0
    for path, _, _ in PAGES:
        for p in [path] + [lang_path(lg, path) for lg in LANGS]:
            pat = r"  <url>\s*<loc>%s%s</loc>[\s\S]*?</url>\n" % (re.escape(SITE), re.escape(p))
            t, k = re.subn(pat, "", t)
            n += k
    return t, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    t = SM.read_text(encoding="utf-8")
    before = len(re.findall(r"<loc>", t))

    t, removed = strip_old(t)

    # 逐块插入：EN 用裸路径，语言块用 <lang>/products.html 作锚点
    total = 0
    for lg, anchor_path in [(None, "/products.html")] + [(l, "/%s/products.html" % l) for l in LANGS]:
        anchor = "    <loc>%s%s</loc>" % (SITE, anchor_path)
        if anchor not in t:
            print("!! 未找到锚点 %s，sitemap 结构可能已变，请人工确认。" % anchor_path)
            return 1
        i = t.index(anchor)
        j = t.index("</url>", i) + len("</url>") + 1     # 越过该条目的换行
        if lg is None:
            block = "".join(entry(p, prio, freq) for p, prio, freq in PAGES)
            total += len(PAGES)
        else:
            block = "".join(entry(p, LANG_PRIO, LANG_FREQ, lg) for p, _, _ in PAGES)
            total += len(PAGES)
        t = t[:j] + block + t[j:]

    after = len(re.findall(r"<loc>", t))
    print("清理旧器械条目: %d 条" % removed)
    print("插入位置: %s" % "、".join(["/products.html"] + ["/%s/products.html" % l for l in LANGS]))
    print("URL 数: %d → %d（净 +%d）" % (before, after, after - before))

    if a.dry_run:
        print("dry-run 未写盘")
        return 0
    SM.write_text(t, encoding="utf-8")

    # 复查
    t2 = SM.read_text(encoding="utf-8")
    missing, dup = [], []
    for path, _, _ in PAGES:
        for p in [path] + [lang_path(lg, path) for lg in LANGS]:
            u = "<loc>%s%s</loc>" % (SITE, p)
            if u not in t2:
                missing.append(p)
            elif t2.count(u) > 1:
                dup.append(p)
    print("复查: 缺失 %s | 重复 %s" % (missing or "无", dup or "无"))
    locs = re.findall(r"<loc>([^<]+)</loc>", t2)
    dup_all = {x for x in locs if locs.count(x) > 1}
    print("全站 loc 唯一性:", "有重复 %s" % list(dup_all)[:5] if dup_all else "唯一 ✓（共 %d 条）" % len(locs))
    pl = [u for u in locs if "/pilates/" in u]
    print("其中 /pilates/ 条目: %d 条（应为 %d）" % (len(pl), len(PAGES) * 7))
    return 0 if not (missing or dup or dup_all) else 1


if __name__ == "__main__":
    sys.exit(main())
