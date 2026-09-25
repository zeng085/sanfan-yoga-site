#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""英文主站 SEO 达标审计（2026-09-25）

按「全球贸易通独立站 SEO 标准」的 20 项页面上线清单，对 fjsanfan.com **英文页**
做页面类型感知的机械审计。与旧脚本 audit_seo_20260916.py 的分工：
  - 旧脚本：全站 1331 页、13 项、纯标签层（不看内容形态）
  - 本脚本：仅英文页 191 个、22 项，新增「页面类型感知」判定
    （正文词数区间 / Schema 类型匹配 / 面包屑 / 内链锚文本 / CTA）

关键设计（踩过的坑，勿改）：
  1. H1 与 H2 是**中英内联配对**（`TPE Yoga Mats<span class="lang-zh">…</span>`），
     必须先用剥块器去掉 .lang-zh 元素再抽文本，否则词数与 H1 全部被中文污染。
  2. 剥块用**标签配平**而非 `.*?</tag>` 非贪婪 —— 块级 `div.lang-zh`（10 个 blog 页）
     内部有嵌套 div，非贪婪会在第一个 `</div>` 截断、留下中文残块。
  3. 图片缺 width/height **不计不达标**：styles.css 已在 .prod-card .ph / .pd-main img /
     .cat-tile .ct-img / .pc-img 等容器上设 aspect-ratio，CLS 已被兜底 → 记为提示。
  4. 描述长度按**显示宽度**判定且 EN 用 120–160，>65 title / >160 desc 才判未达标
     （专家口径允许 title 至 65、B2B desc 至 180）。

用法：
  python3 audit_en_seo_standard_20260925.py            # 控制台摘要 + JSON
  python3 audit_en_seo_standard_20260925.py --json     # 只出 JSON 路径
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
HOST = "fjsanfan.com"
HREFLANG_WANT = ["en", "de", "ja", "ko", "fr", "it", "es", "x-default"]

# 顶层一级产品分类页（人工标定，勿猜）
TOP_CATEGORY = {
    "tpe-yoga-mats.html", "pu-rubber-yoga-mats.html", "suede-cork-yoga-mats.html",
    "meditation-pilates-mats.html", "foam-rollers.html", "jump-ropes.html",
    "massage-recovery.html", "resistance-bands.html", "strength-training.html",
    "yoga-props-accessories.html",
}

# 专家清单的建议正文词数区间（下限把关判不达标，超上限仅提示）
WORD_RANGE = {
    "首页": (800, 1500),
    "产品中心": (400, 800),
    "一级分类": (600, 1200),
    "应用方案页": (600, 1200),
    "产品详情页": (500, 1000),
    "关于我们": (500, 1200),
    "联系我们": (300, 600),
    "FAQ页": (400, 1500),
    "支持/知识页": (500, 1200),
    "Blog列表": (200, 400),
    "Blog文章": (800, 2000),
}

# 页面类型 → 必需 Schema（any-of 集合）
SCHEMA_REQ = {
    "首页": [("Organization", {"Organization"}), ("WebSite", {"WebSite"})],
    "产品中心": [("CollectionPage", {"CollectionPage"}),
                 ("ItemList", {"ItemList"}), ("BreadcrumbList", {"BreadcrumbList"})],
    "一级分类": [("CollectionPage", {"CollectionPage"}),
                 ("ItemList", {"ItemList"}), ("BreadcrumbList", {"BreadcrumbList"})],
    "产品详情页": [("Product", {"Product"}), ("BreadcrumbList", {"BreadcrumbList"})],
    "Blog文章": [("Article/BlogPosting", {"Article", "BlogPosting"}),
                 ("BreadcrumbList", {"BreadcrumbList"})],
    "Blog列表": [("CollectionPage/Blog", {"CollectionPage", "Blog", "ItemList"})],
    "联系我们": [("ContactPage/Organization", {"ContactPage", "Organization"})],
    "关于我们": [("Organization/AboutPage", {"Organization", "AboutPage"})],
    "应用方案页": [("CollectionPage/WebPage", {"CollectionPage", "WebPage"})],
    "FAQ页": [("FAQPage", {"FAQPage"})],
}

BAD_ANCHORS = {"click here", "here", "read more", "learn more", "more",
               "view more", "see more", "link", "this page", "详情"}
BAD_ALT_RE = re.compile(r"^(image|img|photo|picture|pic|untitled)[\s_\-]?\d*$", re.I)
BAD_FNAME_RE = re.compile(r"(^|/)(img_|dsc_|dscn|image\d|photo\d|screenshot)|"
                          r"\d{8,}|[\u4e00-\u9fff]")
GENERIC_H1 = {"our products", "products", "home", "welcome", "shop", "index"}
STOP = {"the", "a", "an", "and", "or", "for", "to", "of", "in", "on", "with", "your",
        "our", "we", "is", "are", "at", "by", "from", "as", "be", "it", "that", "this",
        "&", "-", "|", ",", "—"}
CTA_RE = re.compile(r'href="(?:\.\./)?contact\.html(?:[?#][^"]*)?"|wa\.me/|'
                    r'href="#[^"]*quote[^"]*"|Request a Quote|Get a Quote|Send Inquiry|'
                    r'Request Quote|Get Quote|Inquiry', re.I)

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
    "robots": re.compile(r'<meta\s+name="robots"\s+content="([^"]*)"', re.I),
    "charset": re.compile(r'<meta\s+charset="?([\w\-]+)"?', re.I),
    "viewport": re.compile(r'<meta\s+name="viewport"\s+content="([^"]*)"', re.I),
    "h1": re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.S | re.I),
    "h1tag": re.compile(r"<h1\b[^>]*>", re.I),
    "h2tag": re.compile(r"<h2\b[^>]*>", re.I),
    "h3tag": re.compile(r"<h3\b[^>]*>", re.I),
    "img": re.compile(r"<img\b[^>]*>", re.I),
    "imgalt": re.compile(r'\balt="([^"]*)"', re.I),
    "imgw": re.compile(r'\bwidth="', re.I),
    "a": re.compile(r'<a\b([^>]*)>(.*?)</a>', re.S | re.I),
    "breadcrumb": re.compile(r'BreadcrumbList|class="[^"]*breadcrumb', re.I),
    "aria": re.compile(r'aria-label="[^"]*[Bb]readcrumb', re.I),
}

W = lambda s: sum(2 if ord(c) > 0x2E80 else 1 for c in s)


# ---------- 剥块：标签配平，勿退化成非贪婪 ----------
def _drop_element(s, tag, marker):
    open_re = re.compile(r"<%s\b[^>]*>" % tag, re.I)
    close_re = re.compile(r"</%s\s*>" % tag, re.I)
    out, i = [], 0
    while True:
        m = open_re.search(s, i)
        if not m:
            out.append(s[i:])
            return "".join(out)
        if marker not in m.group(0):          # 不是目标块，原样保留
            out.append(s[i:m.end()])
            i = m.end()
            continue
        out.append(s[i:m.start()])            # 丢掉整个块（配平到对应 </tag>）
        depth, j = 1, m.end()
        while depth > 0:
            mo, mc = open_re.search(s, j), close_re.search(s, j)
            if not mc:
                j = len(s)
                break
            if mo and mo.start() < mc.start():
                depth += 1
                j = mo.end()
            else:
                depth -= 1
                j = mc.end()
        i = j


def strip_zh(s):
    """剥掉中英配对块（行内 span.lang-zh + 块级 div/p.lang-zh）。"""
    for tag in ("span", "div", "p", "li", "td"):
        s = _drop_element(s, tag, "lang-zh")
    return s


def content_text(s):
    """去脚本/样式/页头/页脚/导航后取正文纯文本。"""
    t = re.sub(r"<script\b.*?</script>", " ", s, flags=re.S | re.I)
    t = re.sub(r"<style\b.*?</style>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
    for tag in ("header", "footer", "nav"):
        t = _drop_element(t, tag, "")
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def words(t):
    return [w for w in t.split(" ") if re.search(r"[A-Za-z]", w)]


def txt(frag):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", frag))).strip()


def ptype(rel):
    if rel == "index.html":
        return "首页"
    if rel == "products.html":
        return "产品中心"
    if rel == "blog.html":
        return "Blog列表"
    if rel == "about.html":
        return "关于我们"
    if rel == "contact.html":
        return "联系我们"
    if rel == "faq.html":
        return "FAQ页"
    if rel == "materials.html":
        return "支持/知识页"
    if rel == "product.html":
        return "模板页(noindex)"
    if rel in TOP_CATEGORY:
        return "一级分类"
    if rel.startswith("products/"):
        return "产品详情页"
    if rel.startswith("blog/"):
        return "Blog文章"
    if rel.startswith("applications/"):
        return "应用方案页"
    if rel.startswith("pilates/"):
        # ⚠️ 除 index 外，pilates/*.html 带 Product + AggregateOffer + Brand、单 h1，
        #    实为**设备产品详情页**，不是分类页（第一版误判为一级分类）
        return "一级分类" if rel == "pilates/index.html" else "产品详情页"
    return "其他"


def url_path(rel):
    p = rel.replace(os.sep, "/")
    if p == "index.html":
        return "/"
    if p.endswith("/index.html"):
        p = p[: -len("index.html")]
    return "/" + p


def en_pages():
    """仅英文主站页：顶层 + products/applications/blog/pilates。"""
    seen = []
    for pat in ("*.html", "products/*.html", "applications/*.html",
                "blog/*.html", "pilates/*.html"):
        for f in sorted(glob.glob(os.path.join(ROOT, pat))):
            seen.append((f, os.path.relpath(f, ROOT)))
    return seen


def main():
    os.makedirs(OUT, exist_ok=True)
    pages = en_pages()
    # ⚠️ hreflang 目标跨语言目录 → disk 必须是**全站**页面集合，不能只用英文页
    #    （第一版只装英文页，导致 1140 处 de/ja/ko 目标被误判「不存在」）
    disk = set()
    for f in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True):
        r = os.path.relpath(f, ROOT)
        if r.split(os.sep)[0] in ("assets", "i18n_build", "outputs", ".git", "node_modules"):
            continue
        disk.add(url_path(r))
    disk.add("/")
    sm = os.path.join(ROOT, "sitemap.xml")
    sm_paths = set()
    if os.path.isfile(sm):
        sm_paths = {urlparse(u).path or "/"
                    for u in re.findall(r"<loc>(.*?)</loc>",
                                        open(sm, encoding="utf-8", errors="ignore").read())}

    F = defaultdict(list)      # 不达标：check -> [(rel, 说明)]
    WARN = defaultdict(list)   # 提示/轻微
    INFO = defaultdict(list)   # 仅记录
    rows = {}

    for f, rel in pages:
        raw = open(f, encoding="utf-8", errors="ignore").read()
        s = strip_zh(raw)                       # ← 先剥中文块，后续全部基于 s
        t = ptype(rel)
        noindex = "noindex" in (RE["robots"].search(s).group(1).lower()
                               if RE["robots"].search(s) else "")
        row = {"type": t, "noindex": noindex}
        idx = not noindex                       # 是否要求达标（noindex 模板页跳过）

        # ---------- A. Meta 层 ----------
        if not RE["charset"].search(s):
            F["A1 charset 缺失"].append((rel, ""))
        vp = RE["viewport"].search(s)
        if not vp:
            F["A2 viewport 缺失"].append((rel, ""))
        elif "width=device-width" not in vp.group(1):
            WARN["A2 viewport 未含 width=device-width"].append((rel, vp.group(1)))

        # A11 URL 语义化：全小写、短横线分词、无空格/下划线/中文
        u = url_path(rel)
        hit = re.search(r"[A-Z_\s\u4e00-\u9fff]", u)
        if hit:
            F["A11 URL 非语义化"].append((rel, "含 %r：%s" % (hit.group(0), u)))

        m = RE["title"].search(s)
        ti = html.unescape(m.group(1)).strip() if m else ""
        row["title"], row["title_w"] = ti, W(ti)
        if not ti:
            F["A3 title 缺失"].append((rel, ""))
        elif W(ti) > 65:
            F["A3 title 超 65 宽"].append((rel, "%d：%s" % (W(ti), ti)))
        elif W(ti) > 60:
            WARN["A3 title 61-65 宽（允许但偏长）"].append((rel, "%d：%s" % (W(ti), ti)))
        elif W(ti) < 45:
            WARN["A3 title <45 宽（偏短）"].append((rel, "%d：%s" % (W(ti), ti)))

        m = RE["desc"].search(s)
        de = html.unescape(m.group(1)).strip() if m else ""
        row["desc"], row["desc_w"] = de, W(de)
        if not de:
            F["A4 description 缺失"].append((rel, ""))
        elif idx and W(de) > 160:
            F["A4 description 超 160 宽"].append((rel, "%d：%s…" % (W(de), de[:50])))
        elif idx and W(de) < 120:
            WARN["A4 description <120 宽（偏短）"].append((rel, "%d" % W(de)))

        m = RE["canon"].search(s)
        c = html.unescape(m.group(1)).strip() if m else ""
        row["canon"] = c
        if not c:
            F["A5 canonical 缺失"].append((rel, ""))
        else:
            pu = urlparse(c)
            if not pu.netloc:
                F["A5 canonical 非绝对 URL"].append((rel, c))
            elif pu.netloc not in (HOST, "www." + HOST):
                F["A5 canonical 域名不符"].append((rel, c))
            if idx and pu.path.rstrip("/") != url_path(rel).rstrip("/"):
                F["A5 canonical 非自指"].append((rel, "%s vs 实际 %s" % (pu.path, url_path(rel))))

        mr = RE["robots"].search(s)
        row["robots"] = mr.group(1) if mr else "(未声明)"
        if idx and mr and "noindex" in mr.group(1).lower():
            F["A6 可索引页误标 noindex"].append((rel, mr.group(1)))
        if idx and not mr:
            WARN["A6 未显式声明 robots"].append((rel, ""))

        alts = {}
        for mm in RE["alt"].finditer(s):
            alts[mm.group(1).lower()] = mm.group(2)
        for mm in RE["alt2"].finditer(s):
            alts[mm.group(2).lower()] = mm.group(1)
        row["hreflang"] = sorted(alts)
        if idx:
            miss = set(HREFLANG_WANT) - set(alts)
            if miss:
                F["A7 hreflang 不全"].append((rel, "缺 " + ",".join(sorted(miss))))
            for hl, u in alts.items():
                p = urlparse(u).path or "/"
                if p not in disk and p.rstrip("/") not in disk:
                    F["A7 hreflang 指向不存在的页"].append((rel, "%s → %s" % (hl, p)))

        ml = RE["lang"].search(s)
        row["lang"] = ml.group(1) if ml else ""
        if not row["lang"]:
            F["A8 <html lang> 缺失"].append((rel, ""))
        elif not row["lang"].lower().startswith("en"):
            F["A8 <html lang> 非 en"].append((rel, row["lang"]))

        og = dict(RE["og"].findall(s))
        for k in ("og:title", "og:description", "og:image", "og:url", "og:type"):
            if not og.get(k):
                F["A9 og 标签缺 " + k].append((rel, ""))
        if og.get("og:url") and urlparse(og["og:url"]).path.rstrip("/") != url_path(rel).rstrip("/"):
            F["A9 og:url 非自指"].append((rel, og["og:url"]))
        oi = og.get("og:image", "")
        if oi:
            p = urlparse(oi).path.lstrip("/")
            if p and not os.path.isfile(os.path.join(ROOT, html.unescape(p))):
                F["A9 og:image 文件不存在"].append((rel, p))

        tw = dict(RE["tw"].findall(s))
        for k in ("twitter:card", "twitter:title", "twitter:description", "twitter:image"):
            if not tw.get(k):
                F["A10 twitter 缺 " + k].append((rel, ""))

        # ---------- B. 结构层 ----------
        h1s = RE["h1"].findall(s)
        h1t = txt(h1s[0]) if h1s else ""
        row["h1"], row["n_h1"] = h1t, len(h1s)
        if idx and not h1s:
            F["B1 h1 缺失"].append((rel, ""))
        elif len(h1s) > 1:
            F["B1 多 h1"].append((rel, "%d 个" % len(h1s)))
        if idx and h1s and not h1t:
            F["B1 h1 为空"].append((rel, ""))
        if h1t.lower().strip(" .!:-") in GENERIC_H1:
            WARN["B2 h1 过于宽泛"].append((rel, h1t))

        n2, n3 = len(RE["h2tag"].findall(s)), len(RE["h3tag"].findall(s))
        row["n_h2"], row["n_h3"] = n2, n3
        if idx and n2 < 2:
            WARN["B3 h2 少于 2 个"].append((rel, "%d 个" % n2))
        if n3 and not n2:
            F["B4 H 层级跳跃：有 h3 但整页无 h2"].append((rel, "h3×%d" % n3))
        else:
            first_h2 = RE["h2tag"].search(s)
            first_h3 = RE["h3tag"].search(s)
            if first_h3 and first_h2 and first_h3.start() < first_h2.start():
                # 真实缺陷：H1 之后先出现 h3 再出现 h2，层级反序
                F["B4 H 层级反序：首个 h3 先于首个 h2"].append((rel, ""))

        if idx and not (RE["breadcrumb"].search(s) or RE["aria"].search(s)):
            # 首页面包屑非必需（Google 不接受首页 breadcrumb），豁免
            if t != "首页":
                F["B5 面包屑缺失"].append((rel, ""))

        # ---------- C. 内容层 ----------
        ct = content_text(s)
        nw = len(words(ct))
        row["words"] = nw
        rng = WORD_RANGE.get(t)
        if idx and rng:
            row["word_range"] = "%d-%d" % rng
            if nw < rng[0]:
                F["C1 正文词数低于建议下限"].append(
                    (rel, "%d 词 < %s 建议 %d-%d" % (nw, t, rng[0], rng[1])))
            elif nw > rng[1]:
                INFO["C1 正文词数超上限（非缺陷）"].append(
                    (rel, "%d 词 > 建议 %d" % (nw, rng[1])))

        lds, types = [], set()
        ok_ld = True
        for blk in RE["ld"].findall(s):
            try:
                data = json.loads(blk)
            except Exception as e:
                ok_ld = False
                F["C2 JSON-LD 无法解析"].append((rel, str(e)[:60]))
                continue
            for x in (data if isinstance(data, list) else [data]):
                for ty in re.findall(r'"@type"\s*:\s*"([^"]+)"', json.dumps(x)):
                    types.add(ty)
        row["ld_types"] = sorted(types)
        if idx and not types:
            F["C2 JSON-LD 缺失"].append((rel, ""))
        for label, need in SCHEMA_REQ.get(t, []):
            if idx and not (types & need):
                F["C3 Schema 不匹配：缺 " + label].append(
                    (rel, "现有 " + ",".join(sorted(types))[:60]))
        if t == "首页" and idx:
            miss = [x for x, need in (("BreadcrumbList", {"BreadcrumbList"}),
                                      ("SearchAction", {"SearchAction"}))
                    if not (types & need)]
            if miss:
                INFO["H2 首页 Schema 建议项（专家模板列出，非硬性）"].append(
                    (rel, "缺 " + "/".join(miss) +
                     "；SearchAction 需站内搜索可深链，当前搜索为纯 JS 无 ?q= 参数"))

        if idx:
            rels = [u for u in re.findall(r'<a\b[^>]*href="([^"]*)"', s)
                    if u and not u.startswith(("http", "mailto:", "tel:", "#", "//"))]
            row["inlinks"] = len(rels)
            if len(set(rels)) < 5:
                WARN["C4 站内内链少于 5 条"].append((rel, "%d 条" % len(set(rels))))
            if not CTA_RE.search(s):
                F["C5 缺询盘 CTA"].append((rel, ""))

        bad_anchor = Counter()
        for mm in RE["a"].finditer(s):
            attrs, inner = mm.group(1), mm.group(2)
            if not re.search(r'href="([^"]*)"', attrs):
                F["C6 a 标签缺 href"].append((rel, ""))
                continue
            hv = re.search(r'href="([^"]*)"', attrs).group(1)
            if hv.strip() in ("#", ""):
                F["C6 空 href / href=#"].append((rel, hv or "(空)"))
            if "<img" in inner or "<svg" in inner:
                continue
            at = txt(inner).lower().strip(" .!:-→")
            if at in BAD_ANCHORS:
                bad_anchor[at] += 1
            elif not at:
                bad_anchor["(锚文本为空)"] += 1
        for k, v in bad_anchor.items():
            WARN["C7 锚文本不合格：" + k].append((rel, "%d 处" % v))

        imgs = RE["img"].finditer(s)
        noalt, alts_seen, nowh, badf, badalt = 0, Counter(), 0, [], []
        for im in imgs:
            tag = im.group(0)
            ma = RE["imgalt"].search(tag)
            if not ma or not ma.group(1).strip():
                noalt += 1
            else:
                alts_seen[ma.group(1).strip()] += 1
                if BAD_ALT_RE.match(ma.group(1).strip()):
                    badalt.append(ma.group(1).strip()[:40])
            if not RE["imgw"].search(tag):
                nowh += 1
            ms = re.search(r'src="([^"]+)"', tag)
            if ms and BAD_FNAME_RE.search(ms.group(1)):
                badf.append(ms.group(1).split("/")[-1][:40])
        row["n_img"], row["no_alt"], row["no_wh"] = (len(RE["img"].findall(s)), noalt, nowh)
        if noalt:
            F["C8 图片缺 alt"].append((rel, "%d/%d 张" % (noalt, row["n_img"])))
        dup = [(a, n) for a, n in alts_seen.items() if n >= 3]
        if dup:
            WARN["C9 同页 alt 重复 ≥3 次"].append(
                (rel, "; ".join("%s×%d" % (a[:24], n) for a, n in dup[:3])))
        if badalt:
            F["C10 alt 为占位/无意义"].append((rel, "; ".join(badalt[:3])))
        if badf:
            WARN["C11 图片文件名不语义化"].append((rel, "; ".join(badf[:3])))
        if nowh:
            INFO["C12 图片未声明 width/height（CSS aspect-ratio 已兜底）"].append(
                (rel, "%d/%d 张" % (nowh, row["n_img"])))

        if idx and url_path(rel) not in sm_paths and url_path(rel).rstrip("/") not in sm_paths:
            F["C13 页面未进 sitemap"].append((rel, url_path(rel)))
        rows[rel] = row

    # ---------- 唯一性（仅英文站内部判定） ----------
    for key, lab in (("title", "A3 title 非唯一"), ("desc", "A4 description 非唯一")):
        d = defaultdict(list)
        for rel, row in rows.items():
            if row.get("noindex"):
                continue
            if row.get(key):
                d[row[key]].append(rel)
        for v, rs in d.items():
            if len(rs) > 1:
                F[lab].append((rs[0], "%d 页共用：%s" % (len(rs), v[:55])))

    # ---------- noindex 页（product.html 模板）移出达标判定，单列记录 ----------
    ni = {rel for rel, row in rows.items() if row["noindex"]}
    moved = defaultdict(list)
    for bucket in (F, WARN):
        for k in list(bucket):
            hit = [(r, m) for r, m in bucket[k] if r in ni]
            keep = [(r, m) for r, m in bucket[k] if r not in ni]
            if hit:
                moved["noindex 模板页不合规（不影响索引）：" + k] = hit
            if keep:
                bucket[k] = keep
            else:
                del bucket[k]
    for k, v in moved.items():
        INFO[k] = v

    # ---------- 按页面类型的达标率汇总（报告主表） ----------
    types_all = Counter(r["type"] for r in rows.values() if not r["noindex"])
    type_fail = defaultdict(lambda: defaultdict(list))
    for k, v in F.items():
        for rel, msg in v:
            type_fail[rows[rel]["type"]][k].append(rel)
    summary = {}
    for ty, tot in types_all.items():
        bad_pages = {r for k in type_fail[ty] for r in type_fail[ty][k]}
        summary[ty] = {"pages": tot, "checks_failed": len(type_fail[ty]),
                       "pages_failed": len(bad_pages),
                       "rate": round(100.0 * (tot - len(bad_pages)) / tot, 1),
                       "checks": sorted(type_fail[ty])}
    print("\n" + "=" * 78)
    print("【分页面类型达标率】（未达标页 = 至少 1 项不达标）")
    print("=" * 78)
    print("  %-14s %5s %8s %9s %8s" % ("页面类型", "页数", "未达标页", "达标率", "失败项"))
    for ty, s in sorted(summary.items(), key=lambda kv: kv[1]["rate"]):
        print("  %-14s %5d %8d %8.1f%% %8d"
              % (ty, s["pages"], s["pages_failed"], s["rate"], s["checks_failed"]))

    # ---------- 输出 ----------
    print("=" * 78)
    print("英文站 SEO 达标审计 · %d 页（可索引 %d / noindex %d）"
          % (len(rows), sum(1 for r in rows.values() if not r["noindex"]),
             sum(1 for r in rows.values() if r["noindex"])))
    print("=" * 78)
    print("\n【页面类型分布】")
    for ty, n in sorted(Counter(r["type"] for r in rows.values()).items(),
                        key=lambda kv: -kv[1]):
        print("  %-14s %3d 页" % (ty, n))

    for title, bucket in (("未达标（必须修）", F), ("提示（建议优化）", WARN),
                          ("仅供记录（非缺陷）", INFO)):
        print("\n" + "─" * 78)
        print("◆ %s：%d 项 / %d 处" % (title, len(bucket), sum(len(v) for v in bucket.values())))
        print("─" * 78)
        if not bucket:
            print("  无")
        for k in sorted(bucket, key=lambda k: -len(bucket[k])):
            v = bucket[k]
            print("\n  [%s] %d 处 / %d 页" % (k, len(v), len({r for r, _ in v})))
            for rel, msg in v[:3]:
                print("      %-46s %s" % (rel, str(msg)[:100]))
            if len(v) > 3:
                print("      …另有 %d 处" % (len(v) - 3))

    dump = {"total": len(rows), "summary": summary,
            "fail": {k: [list(x) for x in v] for k, v in F.items()},
            "warn": {k: [list(x) for x in v] for k, v in WARN.items()},
            "info": {k: [list(x) for x in v] for k, v in INFO.items()},
            "rows": rows}
    p = os.path.join(OUT, "en_seo_standard_20260925.json")
    json.dump(dump, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n明细 → %s" % os.path.relpath(p, ROOT))
    print("未达标 %d 处 / 提示 %d 处"
          % (sum(len(v) for v in F.values()), sum(len(v) for v in WARN.values())))


if __name__ == "__main__":
    main()
