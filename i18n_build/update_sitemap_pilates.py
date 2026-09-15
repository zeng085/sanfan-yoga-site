#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""把 /pilates/ 板块的 9 个 URL 补进 sitemap.xml（幂等，可反复跑）。

位置：紧跟 `products.html` 条目之后 —— sitemap 的顺序是「主栏目」聚在一起
（/ → about → products → faq → contact → blog → materials → 10 个分类页…），
Pilates 是新的主栏目，插在 products 后面最贴近它实际的导航位置（Home → Pilates → Products…）。

hreflang：器械页目前只有 EN，所以只声明 en + x-default，
与页面自身的 <link rel="alternate"> 完全一致。
（其余 7 语言条目在语言版铺完后由本脚本 --langs 补齐，别提前声明不存在的 URL。）

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

PAGES = [
    ("/pilates/", 1.0),
    ("/pilates/pilates-reformer.html", 0.9),
    ("/pilates/pilates-cadillac.html", 0.8),
    ("/pilates/pilates-wunda-chair.html", 0.8),
    ("/pilates/pilates-ladder-barrel.html", 0.8),
    ("/pilates/pilates-spine-corrector.html", 0.8),
    ("/pilates/pilates-reformer-tower.html", 0.8),
    ("/pilates/pilates-studio-set.html", 0.8),
    ("/pilates/pilates-specialty.html", 0.8),
]

ANCHOR = "    <loc>https://fjsanfan.com/products.html</loc>"


def entry(path, prio):
    u = SITE + path
    return ("  <url>\n"
            "    <loc>%s</loc>\n"
            '    <xhtml:link rel="alternate" hreflang="en" href="%s"/>\n'
            '    <xhtml:link rel="alternate" hreflang="x-default" href="%s"/>\n'
            "    <priority>%.1f</priority>\n"
            "  </url>\n" % (u, u, u, prio))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    t = SM.read_text(encoding="utf-8")
    before = len(re.findall(r"<loc>", t))

    have = [p for p, _ in PAGES if "<loc>%s%s</loc>" % (SITE, p) in t]
    if len(have) == len(PAGES):
        print("sitemap 已含全部 %d 个 /pilates/ URL，无需改动。" % len(PAGES))
        return 0

    # 先清理可能存在的旧块（重跑时避免重复）
    if have:
        for p, _ in PAGES:
            t = re.sub(r"  <url>\s*<loc>%s%s</loc>[\s\S]*?</url>\n" % (re.escape(SITE), re.escape(p)),
                       "", t)

    if ANCHOR not in t:
        print("!! 未找到锚点 products.html 条目，sitemap 结构可能已变，请人工确认。")
        return 1
    i = t.index(ANCHOR)
    j = t.index("</url>", i) + len("</url>") + 1     # 越过该条目的换行

    block = "".join(entry(p, prio) for p, prio in PAGES)
    new = t[:j] + block + t[j:]

    after = len(re.findall(r"<loc>", new))
    print("插入位置: products.html 之后")
    print("URL 数: %d → %d（+%d）" % (before - len(have), after, after - (before - len(have))))
    if a.dry_run:
        print("dry-run 未写盘")
        return 0
    SM.write_text(new, encoding="utf-8")

    # 复查
    t2 = SM.read_text(encoding="utf-8")
    missing = [p for p, _ in PAGES if "<loc>%s%s</loc>" % (SITE, p) not in t2]
    dup = [p for p, _ in PAGES if t2.count("<loc>%s%s</loc>" % (SITE, p)) > 1]
    print("复查: 缺失 %s | 重复 %s" % (missing or "无", dup or "无"))
    # 整份 sitemap 的 URL 对账（每条 loc 唯一）
    locs = re.findall(r"<loc>([^<]+)</loc>", t2)
    dup_all = {x for x in locs if locs.count(x) > 1}
    print("全站 loc 唯一性:", "有重复 %s" % list(dup_all)[:5] if dup_all else "唯一 ✓（共 %d 条）" % len(locs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
