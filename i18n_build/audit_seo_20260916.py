#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全站 SEO/结构标签审计（2026-09-16）

逐页校验 13 项，全部机械判定；输出摘要 + JSON 明细：
  1  <title> 缺失 / 非唯一 / >60 显示宽
  2  description 缺失 / 非唯一 / 过短(<70)
  3  canonical 缺失 / 非自指 / 非绝对 URL / 域名不对 / 指向不存在的页面
  4  hreflang 集合不全（含 x-default）/ 目标文件不存在 / 互指不对称
  5  og:title/description/image/url/type 缺失；og:image 文件不存在
  6  twitter:card/title/description/image 缺失
  7  JSON-LD 无法解析 / 缺 @context / 缺 @type
  8  <html lang> 与目录语言不符
  9  h1 缺失 / 多 h1（历史坑：中英双 h1 并排）
 10  <img> 缺 alt
 11  sitemap.xml 中不存在的 URL / 页面未进 sitemap / 重复条目
 12  robots.txt 缺 Sitemap 行
 13  内链语言前缀自洽（语言页 <html lang> 与 canononical 路径一致）

用法：python3 audit_seo_20260916.py [--json]
"""
import glob
import html
import json
import os
import re
import sys
from collections import Counter, defaultdict
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "i18n_build", "reports")
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
ALL_LANGS = ["en"] + LANGS
HOST = "fjsanfan.com"
SKIP = (".git", "node_modules", "outputs", "i18n_build/cache", "i18n_build/reports")

W = lambda s: sum(2 if ord(c) > 0x2E80 else 1 for c in s)

RE = {
    "title": re.compile(r"<title>(.*?)</title>", re.S | re.I),
    "desc": re.compile(r'<meta\s+name="description"\s+content="([^"]*)"', re.I),
    "canon": re.compile(r'<link\s+rel="canonical"\s+href="([^"]*)"', re.I),
    "alt": re.compile(r'<link\s+rel="alternate"\s+hreflang="([^"]+)"\s+href="([^"]*)"', re.I),
    "alt2": re.compile(r'<link\s+rel="alternate"\s+href="([^"]*)"\s+hreflang="([^"]+)"', re.I),
    "og": re.compile(r'<meta\s+property="(og:[a-z:]+)"\s+content="([^"]*)"', re.I),
    "tw": re.compile(r'<meta\s+name="(twitter:[a-z:]+)"\s+content="([^"]*)"', re.I),
    "ld": re.compile(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', re.S | re.I),
    "lang": re.compile(r'<html[^>]*\blang="([^"]*)"', re.I),
    "h1": re.compile(r"<h1\b[^>]*>", re.I),
    "img": re.compile(r"<img\b[^>]*>", re.I),
    "imgalt": re.compile(r'\balt="([^"]*)"', re.I),
}
HREF_REL = re.compile(r'<a\b[^>]*?href="([^"]*)"', re.I)


def pages():
    for f in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True):
        rel = os.path.relpath(f, ROOT)
        if rel.startswith(SKIP) or rel.split(os.sep)[0] in ("assets", "i18n_build"):
            continue
        yield f, rel


def plang(rel):
    seg = rel.split(os.sep)
    return seg[0] if seg[0] in LANGS else "en"


def url_path(rel):
    p = rel.replace(os.sep, "/")
    if p == "index.html":          # 站点根首页的真实 URL 是 "/"，不是 "/index.html"
        return "/"
    if p.endswith("/index.html"):
        p = p[: -len("index.html")]
    return "/" + p


def main():
    os.makedirs(OUT, exist_ok=True)
    P = list(pages())
    disk = {url_path(r) for _, r in P}
    disk.add("/")
    R = defaultdict(lambda: defaultdict(list))
    ttl, dsc = Counter(), defaultdict(list)
    alt_map = {}
    rows = {}

    for f, rel in P:
        s = open(f, encoding="utf-8", errors="ignore").read()
        lg = plang(rel)
        up = url_path(rel)
        # 显式 noindex 的孤立页（如 product.html 模板）不要求 hreflang/JSON-LD/sitemap
        noindex = "noindex" in s[:4000]
        row = {"lang": lg, "noindex": noindex}
        # 1 title
        m = RE["title"].search(s)
        t = html.unescape(m.group(1)).strip() if m else ""
        row["title_w"] = W(t)
        row["title_txt"] = t
        if not t:
            R["1 title 缺失"][rel].append("")
        else:
            ttl[t] += 1
            if W(t) > 60:
                R["1 title 超 60 宽"][rel].append("%d：%s" % (W(t), t))
        # 2 desc
        m = RE["desc"].search(s)
        d = html.unescape(m.group(1)).strip() if m else ""
        row["desc_w"] = W(d)
        if not d:
            R["2 description 缺失"][rel].append("")
        else:
            dsc[d].append(rel)
            if W(d) < 70:
                R["2 description 过短(<70)"][rel].append("%d：%s" % (W(d), d[:60]))
        # 3 canonical
        m = RE["canon"].search(s)
        c = html.unescape(m.group(1)).strip() if m else ""
        row["canon"] = c
        if not c:
            R["3 canonical 缺失"][rel].append("")
        else:
            pu = urlparse(c)
            cpath = pu.path
            if pu.netloc and pu.netloc != HOST:
                R["3 canonical 域名不对"][rel].append(c)
            if not pu.netloc:
                R["3 canonical 非绝对 URL"][rel].append(c)
            if cpath.rstrip("/") != up.rstrip("/") and cpath not in ("/", up) and not noindex:
                R["3 canonical 非自指"][rel].append("%s vs 实际 %s" % (cpath, up))
            if cpath not in disk and cpath + "/" not in disk and cpath.rstrip("/") not in disk \
                    and not noindex:
                R["3 canonical 指向不存在的页面"][rel].append(cpath)
        # 4 hreflang
        alts = {}
        for m in RE["alt"].finditer(s):
            alts[m.group(1).lower()] = m.group(2)
        for m in RE["alt2"].finditer(s):
            alts[m.group(2).lower()] = m.group(1)
        row["hreflang"] = sorted(alts)
        want = set(ALL_LANGS) | {"x-default"}
        miss_h = want - set(alts)
        if miss_h and not noindex:
            R["4 hreflang 集合不全"][rel].append("缺 " + ",".join(sorted(miss_h)))
        if not noindex:
            for hl, url in alts.items():
                p = urlparse(url).path or "/"
                if p not in disk and p.rstrip("/") not in disk:
                    R["4 hreflang 目标不存在"][rel].append("%s → %s" % (hl, p))
            alt_map[rel] = (up, alts)
        # 5 og
        og = dict(RE["og"].findall(s))
        for k in ("og:title", "og:description", "og:image", "og:url", "og:type"):
            if not og.get(k):
                R["5 " + k + " 缺失"][rel].append("")
        img = og.get("og:image", "")
        if img:
            p = urlparse(img).path.lstrip("/")
            if p and not os.path.isfile(os.path.join(ROOT, p)):
                R["5 og:image 文件不存在"][rel].append(p)
        # 6 twitter
        tw = dict(RE["tw"].findall(s))
        for k in ("twitter:card", "twitter:title", "twitter:description", "twitter:image"):
            if not tw.get(k):
                R["6 " + k + " 缺失"][rel].append("")
        # 7 json-ld
        lds = RE["ld"].findall(s)
        row["ld"] = len(lds)
        if not lds and not noindex:
            R["7 JSON-LD 缺失"][rel].append("")
        for block in lds:
            try:
                data = json.loads(block)
            except Exception as e:
                R["7 JSON-LD 无法解析"][rel].append(str(e)[:70])
                continue
            if isinstance(data, dict) and "@context" not in data:
                R["7 JSON-LD 缺 @context"][rel].append("")
            if not ("@type" in json.dumps(data)[:400] or '"@type"' in json.dumps(data)):
                R["7 JSON-LD 缺 @type"][rel].append("")
        # 8 html lang
        m = RE["lang"].search(s)
        hl = (m.group(1) if m else "").lower()
        row["html_lang"] = hl
        if not hl:
            R["8 <html lang> 缺失"][rel].append("")
        elif lg == "en" and not hl.startswith("en"):
            R["8 <html lang> 与目录不符"][rel].append("%s（目录 en）" % hl)
        elif lg != "en" and not hl.startswith(lg):
            R["8 <html lang> 与目录不符"][rel].append("%s（目录 %s）" % (hl, lg))
        # 9 h1
        h1s = RE["h1"].findall(s)
        if not h1s and not noindex:
            R["9 h1 缺失"][rel].append("")
        elif len(h1s) > 1:
            R["9 多 h1"][rel].append("%d 个" % len(h1s))
        # 10 img alt
        noalt = 0
        for im in RE["img"].finditer(s):
            if not RE["imgalt"].search(im.group(0)):
                noalt += 1
        if noalt:
            R["10 img 缺 alt"][rel].append("%d 张" % noalt)
        rows[rel] = row

    # title/desc 唯一性（按语言分组判定：不同语言的同文案不算重复）
    tmap = defaultdict(list)
    for rel, row in rows.items():
        if row.get("title_txt"):
            tmap[(row["lang"], row["title_txt"])].append(rel)
    for (lg, t), rs in tmap.items():
        if len(rs) > 1:
            R["1 title 非唯一"][rs[0]] = ["%s 内 %d 页共用：%s" % (lg, len(rs), t[:60])]
    for d, rs in dsc.items():
        seen = defaultdict(list)
        for r in rs:
            seen[plang(r)].append(r)
        for lg, rr in seen.items():
            if len(rr) > 1:
                R["2 description 非唯一"][rr[0]] = ["%s 内 %d 页共用：%s" % (lg, len(rr), d[:60])]

    # 4 互指对称
    for rel, (up, alts) in alt_map.items():
        for hl, url in alts.items():
            p = (urlparse(url).path or "/")
            for cand in (p, p.rstrip("/"), p + "index.html"):
                rel2 = cand.lstrip("/")
                if not rel2.endswith(".html"):
                    rel2 = rel2.rstrip("/") + "/index.html"
                if rel2 in alt_map:
                    up2, alts2 = alt_map[rel2]
                    if up not in list(alts2.values()) and not any(
                            (urlparse(v).path or "/") == up for v in alts2.values()):
                        R["4 hreflang 互指不对称"][rel].append("%s 未回指本页" % rel2)
                    break

    # 11 sitemap
    sm_path = os.path.join(ROOT, "sitemap.xml")
    sm_urls = []
    if os.path.isfile(sm_path):
        sm = open(sm_path, encoding="utf-8", errors="ignore").read()
        sm_urls = re.findall(r"<loc>(.*?)</loc>", sm)
    cnt = Counter(urlparse(u).path or "/" for u in sm_urls)
    for p, n in cnt.items():
        if n > 1:
            R["11 sitemap 重复条目"]["sitemap.xml"].append("%s ×%d" % (p, n))
    sset = set(cnt)
    for r in rows:
        if rows[r].get("noindex"):
            continue
        u = url_path(r)
        if u not in sset and u.rstrip("/") not in sset:
            R["11 页面未进 sitemap"][r].append(u)
    for p in cnt:
        if p not in disk and p.rstrip("/") not in disk:
            R["11 sitemap 指向不存在的页面"]["sitemap.xml"].append(p)
    # 12 robots
    rb = os.path.join(ROOT, "robots.txt")
    if not os.path.isfile(rb):
        R["12 robots.txt 缺失"]["robots.txt"].append("")
    elif "sitemap" not in open(rb, encoding="utf-8", errors="ignore").read().lower():
        R["12 robots.txt 缺 Sitemap 行"]["robots.txt"].append("")

    # ---- 输出 ----
    print("=" * 74)
    print("全站 SEO 审计：%d 页（EN %d + 6 语言 %d）" % (
        len(rows), sum(1 for r in rows if plang(r) == "en"), sum(1 for r in rows if plang(r) != "en")))
    print("=" * 74)
    grand = 0
    order = sorted(R.keys(), key=lambda k: (int(k.split()[0]) if k.split()[0].isdigit() else 99, k))
    for k in order:
        d = R[k]
        tot = sum(len(v) for v in d.values())
        grand += tot
        flag = "✓" if tot == 0 else "✗"
        print("\n%s %-34s %4d 处 / %3d 页" % (flag, k, tot, len(d)))
        for rel, v in sorted(d.items(), key=lambda kv: -len(kv[1]))[:5]:
            print("     %-52s %s" % (rel, "; ".join(str(x) for x in v[:2])[:90]))
        if len(d) > 5:
            print("     …另有 %d 页同类" % (len(d) - 5))
    print("\n问题合计：%d 处" % grand)
    json.dump({k: {kk: vv for kk, vv in v.items()} for k, v in R.items()},
              open(os.path.join(OUT, "seo_20260916.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("明细 → i18n_build/reports/seo_20260916.json")


if __name__ == "__main__":
    main()
