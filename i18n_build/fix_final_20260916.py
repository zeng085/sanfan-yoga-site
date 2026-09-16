#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""收尾修复（2026-09-16）—— 全面排查后剩下的真实问题

来源：audit_links_20260916.py + audit_seo_20260916.py 复跑结果。

修复项：
  A) 目录索引的 index.html 形式 → 目录形式
     canonical / hreflang / og:url / sitemap / 导航内链 里全是
     `.../applications/index.html`，而 Vercel 把 `*.html` 按文件直出，
     目录索引正解是 `/applications/`。canonical 指向 index.html 形式 =
     canonical 指向一个「非正典」URL（且站内存在两套 URL 的重复风险）。
  B) 根级页面里 `href="index.html"`（84 处）→ `href="./"`，避免 /index.html 形式。
  C) ko/products/rb2.html description 过短（显示宽 65 < 70）→ 补足。
  D) 7 个博客索引页（blog.html + 6 语言）缺 JSON-LD → 补 Blog + ItemList。
  E) vercel.json 补 `/…/applications/index.html` → `/…/applications/` 301（与既有
     `/index.html` → `/` 规则一致）。

用法：python3 fix_final_20260916.py [--apply]
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPLY = "--apply" in sys.argv
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
SKIP = ("/.git", "/node_modules", "/outputs", "/__pycache__", "/i18n_build/reports")

W = lambda s: sum(2 if ord(c) > 0x2E80 else 1 for c in s)
stat = {}


def bump(k, n=1):
    stat[k] = stat.get(k, 0) + n


def html_files():
    for f in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True):
        rel = f.replace(ROOT, "")
        if any(s in rel for s in SKIP):
            continue
        yield f, rel.lstrip("/")


# ---------------------------------------------------------------- A
def fix_a(path, s):
    n = s.count("applications/index.html")
    if n:
        s = s.replace("applications/index.html", "applications/")
        bump("A index.html→目录形式", n)
    return s


# ---------------------------------------------------------------- B
def fix_b(path, rel, s):
    if rel.count("/") != 0:          # 只处理根级页面
        # 深层页面用 ../ 形式，同样有 index.html 形式
        pass
    n = s.count('href="index.html"')
    if n:
        s = s.replace('href="index.html"', 'href="./"')
        bump("B href=index.html→./", n)
    return s


# ---------------------------------------------------------------- C
KO_DESC = ("필라테스, 재활 및 코어 운동용 25 cm (10인치) 미끄럼 방지 미니 요가 볼. "
           "SANFAN 공장 직공급, OEM/ODM 맞춤 로고·색상, 100개부터 도매 견적 제공.")


def fix_c(path, s):
    if not path.endswith("ko/products/rb2.html"):
        return s
    m = re.search(r'<meta name="description" content="([^"]*)"', s)
    if not m or W(m.group(1)) >= 70:
        return s
    s = s[:m.start(1)] + KO_DESC + s[m.end(1):]
    bump("C ko rb2 描述补足")
    return s


# ---------------------------------------------------------------- D
BLOG_LD = """  <script type="application/ld+json">
%s
  </script>
"""


def fix_d(path, rel, s):
    if not (rel == "blog.html" or re.fullmatch(r"(de|ja|ko|fr|it|es)/blog\.html", rel)):
        return s
    if "application/ld+json" in s:
        return s
    base = "" if rel == "blog.html" else rel.split("/")[0] + "/"
    sub = {"blog.html": "", "de/blog.html": "/de", "ja/blog.html": "/ja",
           "ko/blog.html": "/ko", "fr/blog.html": "/fr", "it/blog.html": "/it",
           "es/blog.html": "/es"}[rel]
    m = re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S)
    h1 = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else "Blog"
    md = re.search(r'<meta name="description" content="([^"]*)"', s)
    desc = md.group(1) if md else h1
    titles = re.findall(r'<a[^>]+href="([^"]*blog/[^"]+\.html)"[^>]*>(.*?)</a>', s, re.S)
    items, seen = [], set()
    for href, txt in titles:
        t = re.sub(r"<[^>]+>", " ", txt)
        t = re.sub(r"\s+", " ", t).strip()
        if not t or href in seen:
            continue
        seen.add(href)
        u = "https://fjsanfan.com/%s%s" % (base, href.lstrip("./"))
        items.append({"@type": "ListItem", "position": len(items) + 1,
                      "url": u, "name": t})
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "Blog", "@id": "https://fjsanfan.com%s/blog.html#blog" % sub,
             "url": "https://fjsanfan.com%s/blog.html" % sub,
             "name": h1, "description": desc,
             "inLanguage": {"blog.html": "en", "de/blog.html": "de", "ja/blog.html": "ja",
                            "ko/blog.html": "ko", "fr/blog.html": "fr",
                            "it/blog.html": "it", "es/blog.html": "es"}[rel],
             "publisher": {"@type": "Organization",
                           "name": "FUJIAN SANFAN Sports Products",
                           "url": "https://fjsanfan.com/"}},
            {"@type": "ItemList", "@id": "https://fjsanfan.com%s/blog.html#list" % sub,
             "name": h1, "itemListElement": items},
        ],
    }
    block = BLOG_LD % json.dumps(data, ensure_ascii=False, indent=2)
    s = s.replace("</head>", block + "</head>", 1)
    bump("D 博客索引补 JSON-LD")
    return s


# ---------------------------------------------------------------- E
def fix_e():
    p = os.path.join(ROOT, "vercel.json")
    cfg = json.load(open(p, encoding="utf-8"))
    red = cfg.setdefault("redirects", [])
    have = {(r.get("source"), r.get("destination")) for r in red}
    add = []
    for pre in [""] + ["/%s" % l for l in LANGS]:
        src, dst = "%s/applications/index.html" % pre, "%s/applications/" % pre
        if (src, dst) not in have:
            add.append({"source": src, "destination": dst, "permanent": True})
    if add:
        # 插到 host 重定向之后
        idx = next((i for i, r in enumerate(red) if r.get("has")), -1) + 1
        cfg["redirects"] = red[:idx] + add + red[idx:]
        bump("E vercel.json 补 301", len(add))
        if APPLY:
            json.dump(cfg, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            open(p, "a", encoding="utf-8").write("\n")
    return len(add)


# ---------------------------------------------------------------- main
def main():
    n = 0
    for f, rel in html_files():
        s0 = open(f, encoding="utf-8").read()
        s = fix_a(f, s0)
        s = fix_b(f, rel, s)
        s = fix_c(f, s)
        s = fix_d(f, rel, s)
        if s != s0:
            n += 1
            if APPLY:
                open(f, "w", encoding="utf-8").write(s)
    # sitemap
    sp = os.path.join(ROOT, "sitemap.xml")
    sm = open(sp, encoding="utf-8").read()
    if "applications/index.html" in sm:
        bump("A sitemap", sm.count("applications/index.html"))
        if APPLY:
            open(sp, "w", encoding="utf-8").write(sm.replace("applications/index.html", "applications/"))
    nred = fix_e()
    print("=" * 60)
    print("模式：%s  改动页面：%d  vercel 新增：%d" % ("APPLY" if APPLY else "DRY-RUN", n, nred))
    for k, v in sorted(stat.items()):
        print("  %-28s %6d" % (k, v))
    print("=" * 60)


if __name__ == "__main__":
    main()
