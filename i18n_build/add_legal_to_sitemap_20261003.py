#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把新增的 Impressum / Privacy Policy 14 个页面写进 sitemap.xml（2026-10-03）

为什么手写而不跑 update_seo.py：update_seo 会重算全站 hreflang 互链，
而本轮 HTML 侧刚做过大规模改动（GA 剥除 / cap-table 包裹 / 页脚插入），
再让它重写一遍会引入不必要的变更面。这里只做**追加**：14 条 <url>，
结构与既有条目完全一致（loc + 8 条 xhtml:link + changefreq + priority）。

法律页的优先级给 0.3（低于产品/分类页）—— 它们是合规必备，不是获客入口。

用法：
    python3 i18n_build/add_legal_to_sitemap_20261003.py --dry-run
    python3 i18n_build/add_legal_to_sitemap_20261003.py
    python3 i18n_build/add_legal_to_sitemap_20261003.py --verify
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIRS = ["", "de", "ja", "ko", "fr", "it", "es"]
BASE = "https://fjsanfan.com"
SITEMAP = os.path.join(ROOT, "sitemap.xml")


def url_for(page, d):
    return "%s/%s%s.html" % (BASE, (d + "/") if d else "", page)


def block(page, d):
    """一条 <url>：loc = 该语言的实际 URL，alternates 覆盖 7 语言 + x-default。

    ⚠️ 每个语言 URL 都要**各自一条** <url>（sitemap 是按 URL 枚举的，
    不是按「页面」枚举）—— 第一版只按 page 生成 1 条，7 个语言里只有 EN 进得去。
    """
    home = url_for(page, "")
    out = ["  <url>", "    <loc>%s</loc>" % url_for(page, d)]
    for dd in DIRS:
        out.append('    <xhtml:link rel="alternate" hreflang="%s" href="%s" />'
                   % (dd if dd else "en", url_for(page, dd)))
    out.append('    <xhtml:link rel="alternate" hreflang="x-default" href="%s" />' % home)
    out.append("    <changefreq>yearly</changefreq>")
    out.append("    <priority>0.3</priority>")
    out.append("  </url>")
    return "\n".join(out)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    s = io.open(SITEMAP, encoding="utf-8").read()
    before = s.count("<url>")

    todo = []
    for page in ("impressum", "privacy"):
        for d in DIRS:
            rel = ("%s/%s.html" % (d, page)) if d else ("%s.html" % page)
            if not os.path.isfile(os.path.join(ROOT, rel)):
                print("✗ 页面不存在：%s" % rel)
                return 1
            u = url_for(page, d)
            if "<loc>%s</loc>" % u in s:
                continue
            todo.append((page, d))

    if mode == "--verify":
        locs = re.findall(r"<loc>([^<]+)</loc>", s)
        legal = [l for l in locs if "/impressum.html" in l or "/privacy.html" in l
                 or l.endswith("/impressum.html") or l.endswith("/privacy.html")]
        uniq = len(locs) == len(set(locs))
        print("sitemap 条目 = %d；法律页条目 = %d/14；loc 唯一 = %s"
              % (len(locs), len(legal), "是" if uniq else "否"))
        return 0 if (len(legal) == 14 and uniq) else 1

    if not todo:
        print("14 条法律页 URL 均已在 sitemap 中，无需改动")
        return 0
    if mode == "--dry-run":
        print("待追加 %d 条：%s ..." % (len(todo), [url_for(p, d) for p, d in todo[:4]]))
        return 0

    # ⚠️ 只为「缺失的」那些 URL 生成条目 —— 早先若已追加过部分语言，
    #    这里再按 14 条全量生成就会产生重复 loc（第一版就是这么写错的）
    add = "\n".join(block(p, d) for p, d in todo)
    s = s.replace("</urlset>", add + "\n</urlset>")
    io.open(SITEMAP, "w", encoding="utf-8").write(s)
    after = io.open(SITEMAP, encoding="utf-8").read().count("<url>")
    locs = re.findall(r"<loc>([^<]+)</loc>", s)
    print("sitemap：%d → %d 条（追加 %d）；loc 唯一数 = %d"
          % (before, after, after - before, len(set(locs))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
