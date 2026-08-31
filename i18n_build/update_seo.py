#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1) 给英文原页（T1 页）补 de/ja/ko 的 hreflang 回链（形成完整互链闭环）
2) 更新 sitemap.xml：新增 30 个语言页 + 为 T1 页写入 xhtml:link hreflang
"""
import os, re, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_pages as B

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://fjsanfan.com"
T1 = B.PAGES
# 2026-08-31: blog 列表页 + 8 篇文章是后来生成的，不在 build_pages.PAGES 中，
# 需要单独纳入 hreflang/sitemap，否则 Google 不会索引这些语言版页面。
EXTRA_PAGES = [
    "blog.html",
    "blog/7day-sampling.html",
    "blog/compliance.html",
    "blog/custom-sizes.html",
    "blog/moq-explained.html",
    "blog/tpe-vs-pu.html",
    "blog/vet-factory.html",
    "blog/yoga-mat-materials.html",
    "blog/yoga-mat-spec-guide.html",
]
PAGES = T1 + EXTRA_PAGES
# 统一引用 build_pages 的语言集合，避免两处硬编码不一致导致 hreflang/sitemap 漏语言
LANGS = B.LANGS


def exists(rel, lg):
    """语言页是否真实存在（避免 hreflang 指向 404）"""
    p = os.path.join(ROOT, lg, rel) if lg else os.path.join(ROOT, rel)
    return os.path.exists(p)


def variants(rel):
    """只列出真实存在的语言版本。
    注意：不再声明 hreflang="zh"——站点没有独立 /zh/ 目录，
    把英文 URL 同时声明成 en 和 zh 是冲突信号。中文走页面内切换器，不是独立语言版本。"""
    def u(lg):
        if lg is None:
            return SITE + "/" if rel == "index.html" else SITE + "/" + rel
        return (SITE + "/" + lg + "/") if rel == "index.html" else (SITE + "/" + lg + "/" + rel)
    out = [("en", u(None))]
    for lg in LANGS:
        if exists(rel, lg):
            out.append((lg, u(lg)))
    out.append(("x-default", u(None)))
    return out


def available_langs(rel):
    return [lg for lg in LANGS if exists(rel, lg)]


def fix_en_pages():
    n = 0
    for rel in PAGES:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            print("  缺页", rel); continue
        h = open(p, encoding="utf-8").read()
        hl = "\n".join('  <link rel="alternate" hreflang="%s" href="%s" />' % (l, u)
                       for l, u in variants(rel))
        h2 = re.sub(r'\s*<link rel="alternate" hreflang="[^"]*" href="[^"]*"\s*/?>', "", h)
        h2 = re.sub(r'(<link rel="canonical"[^>]*>)', r'\1\n' + hl, h2, count=1)
        if h2 != h:
            open(p, "w", encoding="utf-8").write(h2)
            n += 1
    print("英文原页 hreflang 更新: %d 页" % n)


def fix_lang_pages():
    """语言页的 hreflang 也需剔除尚未生成的语言，避免指向 404"""
    n = 0
    for rel in PAGES:
        for lg in LANGS:
            p = os.path.join(ROOT, lg, rel)
            if not os.path.exists(p):
                continue
            h = open(p, encoding="utf-8").read()
            hl = "\n".join('  <link rel="alternate" hreflang="%s" href="%s" />' % (l, u)
                           for l, u in variants(rel))
            h2 = re.sub(r'\s*<link rel="alternate" hreflang="[^"]*" href="[^"]*"\s*/?>', "", h)
            h2 = re.sub(r'(<link rel="canonical"[^>]*>)', r'\1\n' + hl, h2, count=1)
            if h2 != h:
                open(p, "w", encoding="utf-8").write(h2)
                n += 1
    print("语言页 hreflang 同步: %d 页" % n)


def update_sitemap():
    sm = os.path.join(ROOT, "sitemap.xml")
    s = open(sm, encoding="utf-8").read()
    if 'xmlns:xhtml' not in s:
        s = s.replace('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
                      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
                      '        xmlns:xhtml="http://www.w3.org/1999/xhtml">')
    # 移除旧的 T1 相关条目，重建
    entries = re.findall(r"\s*<url>.*?</url>", s, re.S)
    keep = []
    for e in entries:
        loc = re.search(r"<loc>(.*?)</loc>", e).group(1)
        path = loc[len(SITE):].lstrip("/") or "index.html"
        if path in PAGES or re.match(r"^(de|ja|ko|fr|it|es)/", path):
            continue
        keep.append(e)
    head = s.split("<url>")[0]
    out = [head.rstrip()]
    # 英文原页 + hreflang
    for rel in PAGES:
        loc = SITE + "/" if rel == "index.html" else SITE + "/" + rel
        links = "\n".join('    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>' % (l, u)
                          for l, u in variants(rel))
        out.append("  <url>\n    <loc>%s</loc>\n%s\n    <changefreq>weekly</changefreq>\n"
                   "    <priority>0.8</priority>\n  </url>" % (loc, links))
    # 语言页（只收录真实存在的）
    cnt_lang = 0
    for lg in LANGS:
        for rel in PAGES:
            if not exists(rel, lg):
                continue
            loc = (SITE + "/" + lg + "/") if rel == "index.html" else (SITE + "/" + lg + "/" + rel)
            links = "\n".join('    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>' % (l, u)
                              for l, u in variants(rel))
            out.append("  <url>\n    <loc>%s</loc>\n%s\n    <changefreq>monthly</changefreq>\n"
                       "    <priority>0.7</priority>\n  </url>" % (loc, links))
            cnt_lang += 1
    out += [e.strip("\n") for e in keep]
    out.append("</urlset>")
    open(sm, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("sitemap 更新: 英文 %d 页 + 语言页 %d 条，保留其他 %d 条" % (len(PAGES), cnt_lang, len(keep)))


if __name__ == "__main__":
    fix_en_pages()
    fix_lang_pages()
    update_sitemap()
