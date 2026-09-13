# -*- coding: utf-8 -*-
"""三梵独立站综合体检（2026-09-12）—— 一次跑完全部可静态判定的项。

覆盖 12 类：
  1  页面存在性（每个语言站必须和 EN 站同构）
  2  <html lang> 正确
  3  canonical 指向本语言绝对 URL
  4  hreflang 8 条且自指
  5  title 非空、且与 EN 不同（抓「整页没翻译」）
  6  meta description 存在且长度合理
  7  单 h1，且 h1 与 EN 不同
  8  规格表行数与 EN 页一致（抓「表格少翻了几行」）
  9  JSON-LD 可解析 + Product 节点 + name 已本地化
  10 图片 alt 覆盖率、og/twitter 标签
  11 viewport / robots / 语言站不应残留英文 UI 串
  12 sitemap 覆盖（每个 html 都在 sitemap 里）

用法
    python3 i18n_build/full_audit.py            # 全量
    python3 i18n_build/full_audit.py --langs de # 只看一个语言
    python3 i18n_build/full_audit.py --verbose  # 打印每条问题
"""
import argparse
import collections
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
SITE = "https://fjsanfan.com/"

# 语言站里不该出现的英文 UI 串（翻译漏网之鱼）。
# 品牌名 SANFAN、材质 TPE/PVC 等不在其列 —— 那是术语不是 UI。
EN_LEFTOVERS = [
    "Get a Quote", "Request a Quote", "Made to order", "View all",
    "Add to cart", "Buy now", "Add to wishlist", "Related products",
    "You may also like", "Search products", "Popular searches",
    "Compare materials", "Shop by category", "Shop by application",
    "Not sure which spec?", "Read more", "Learn more", "Back to top",
]

TAG_RE = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)((?:[^>\"']|\"[^\"]*\"|'[^']*')*?)(/?)>", re.S)
ATTR_RE = re.compile(r"([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*(\"[^\"]*\"|'[^']*'|[^>\s]+)")


def walk_html(base=""):
    """站点 HTML 相对路径集合（排除构建目录）。"""
    out = set()
    root = os.path.join(ROOT, base) if base else ROOT
    for dp, dns, fs in os.walk(root):
        rel = os.path.relpath(dp, ROOT)
        if rel == ".":
            rel = ""
        if any(s in rel for s in (".git", "node_modules", "outputs", ".workbuddy", "i18n_build")):
            dns[:] = []
            continue
        for f in fs:
            if f.endswith(".html"):
                out.add(os.path.join(rel, f).replace(os.sep, "/").lstrip("/"))
    return out


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace") as fh:
        return fh.read()


def text_of(s):
    # 长度统计必须先反转义：`&amp;` 原始 5 字符、渲染后 1 字符，
    # 否则大量 71~79 字的正常标题被凭空算成 75+ 而误报「过长」。
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())


def meta(h, name):
    """按 name/property 取 content。⚠️ 属性顺序不固定：语言站的 meta 是
    <meta content=\"…\" name=\"description\"/>（content 在前），英文站相反。
    先抓整个 <meta> 标签再在里面找 content，别用顺序敏感的单条正则。"""
    for tag in re.findall(r'<meta\b[^>]*>', h):
        if re.search(r'(?:name|property)=["\']%s["\']' % re.escape(name), tag):
            # ⚠️ 引号要配对：content 里常出现撇号（法语 d'SANFAN），
            # 用 [^"']* 会在撇号处截断，把 283 字的描述误判成 24 字。
            m = re.search(r'content="([^"]*)"', tag) or re.search(r"content='([^']*)'", tag)
            if m:
                return m.group(1).strip()
    return ""


def jsonld_blocks(h):
    out = []
    for m in re.finditer(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', h, re.S | re.I):
        try:
            out.append(json.loads(m.group(1).strip()))
        except Exception:
            out.append(None)
    return out


def product_node(blocks):
    for b in blocks:
        if not isinstance(b, dict):
            continue
        for n in (b.get("@graph") or [b]):
            if isinstance(n, dict) and n.get("@type") == "Product":
                return n
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", default=",".join(LANGS))
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    langs = [x for x in args.langs.split(",") if x]

    # EN 页面 = 所有不以语言目录开头的 html（含 products/ blog/ applications/ 子目录）
    # ⚠️ 第一版写成「顶层 .html 且不在语言目录」，结果只识别到 18 个，
    #    体检覆盖率只有 10% —— 假绿就是这么来的。
    LGRE = re.compile(r"^(?:%s)/" % "|".join(LANGS))
    all_html = walk_html()
    en_pages = sorted(p for p in all_html if not LGRE.match(p))
    # product.html 是 noindex 孤立页，按设计没有语言版
    en_pages = [p for p in en_pages if p != "product.html"]
    print("EN 页面 %d 个（语言站 %d 个文件夹）" % (len(en_pages), len(langs)))

    problems = collections.defaultdict(list)
    counts = collections.Counter()

    # sitemap
    sm = set()
    if os.path.exists(os.path.join(ROOT, "sitemap.xml")):
        sm = set(re.findall(r"<loc>([^<]+)</loc>", read("sitemap.xml")))

    def note(kind, rel, detail):
        problems[kind].append((rel, detail))
        counts[kind] += 1

    for lg in langs:
        lg_pages = sorted(p for p in walk_html(lg))
        en_rel = set(en_pages)
        lg_rel = set(p[len(lg) + 1:] for p in lg_pages)

        # 1 存在性
        for miss in sorted(en_rel - lg_rel):
            note("1.缺语言页", "%s/%s" % (lg, miss), "EN 有而语言站没有")
        for extra in sorted(lg_rel - en_rel):
            note("1.多出页面", "%s/%s" % (lg, extra), "语言站有而 EN 没有")

        for rel in sorted(en_rel & lg_rel):
            lp = "%s/%s" % (lg, rel)
            try:
                h = read(lp)
            except Exception as e:
                note("0.读取失败", lp, str(e)[:60])
                continue
            eh = read(rel) if rel in en_rel else ""

            # 2 lang 属性
            m = re.search(r'<html[^>]*lang="([^"]+)"', h)
            if not m or m.group(1).lower() != lg:
                note("2.lang错", lp, (m.group(1) if m else "缺失"))

            # 3 canonical（语言首页规范到 /de/ 也是对的，别误报）
            m = None
            for tag in re.findall(r'<link\b[^>]*>', h):
                if re.search(r'rel=["\']canonical["\']', tag):
                    mm = re.search(r'href=["\']([^"\']+)["\']', tag)
                    if mm:
                        m = mm
                        break
            want = SITE + lp
            alt = SITE + lg + "/" if rel == "index.html" else None
            if not m:
                note("3.canonical缺失", lp, "")
            elif m.group(1) != want and m.group(1) != alt:
                note("3.canonical错", lp, m.group(1))

            # 4 hreflang
            hl = []
            for tag in re.findall(r'<link\b[^>]*>', h):
                if re.search(r'rel=["\']alternate["\']', tag):
                    mm = re.search(r'href=["\']([^"\']+)["\']', tag)
                    hm = re.search(r'hreflang=["\']([^"\']+)["\']', tag)
                    if mm and hm:
                        hl.append(hm.group(1))
            if len(hl) != 8:
                note("4.hreflang条数", lp, str(len(hl)))
            elif "x-default" not in hl or lg not in hl:
                note("4.hreflang缺自指", lp, ",".join(hl))

            # 5 title
            t = re.search(r"<title>([\s\S]*?)</title>", h)
            t = text_of(t.group(1)) if t else ""
            te = re.search(r"<title>([\s\S]*?)</title>", eh)
            te = text_of(te.group(1)) if te else ""
            if not t:
                note("5.title空", lp, "")
            elif te and t == te:
                note("5.title未翻译", lp, t[:50])
            elif len(t) > 80:
                # 80 而非 70：Google 按像素截断，70~80 字西文标题通常显示得全
                # （与 seo_deep_audit.py 口径一致，避免同一页两套工具结论打架）。
                note("5.title过长", lp, "%d 字" % len(t))

            # 6 description
            d = meta(h, "description")
            if not d:
                note("6.缺description", lp, "")
            elif len(d) < 40:
                note("6.description过短", lp, "%d 字" % len(d))

            # 7 h1
            h1s = re.findall(r"<h1[^>]*>([\s\S]*?)</h1>", h)
            if len(h1s) != 1:
                note("7.h1数量", lp, str(len(h1s)))
            else:
                ht = text_of(h1s[0])
                he = re.findall(r"<h1[^>]*>([\s\S]*?)</h1>", eh)
                het = text_of(he[0]) if he else ""
                # EN 的 h1 是「英文名 + 中文名」连写，剥掉 CJK 只留英文部分再比
                het_en = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+", "", het).strip(" —–-")
                if het_en and ht == het_en and len(ht) > 12:
                    note("7.h1未翻译", lp, ht[:50])

            # 8 规格表行数（仅产品页）
            if rel.startswith("products/"):
                rows = len(re.findall(r"<tr[^>]*>\s*<th", h))
                erows = len(re.findall(r"<tr[^>]*>\s*<th", eh)) if eh else -1
                if erows >= 0 and rows != erows:
                    note("8.规格行数不符", lp, "语言 %d vs EN %d" % (rows, erows))

                # 9 JSON-LD
                blocks = jsonld_blocks(h)
                if any(b is None for b in blocks):
                    note("9.JSON-LD解析失败", lp, "")
                pn = product_node([b for b in blocks if b])
                if not pn:
                    note("9.无Product节点", lp, "")
                else:
                    eb = [b for b in jsonld_blocks(eh) if b] if eh else []
                    epn = product_node(eb)
                    if not pn.get("name"):
                        note("9.Product无name", lp, "")
                    elif epn and pn.get("name") == epn.get("name") and len(pn["name"]) > 10:
                        note("9.name未翻译", lp, str(pn["name"])[:40])
                    offers = pn.get("offers")
                    if not offers:
                        note("9.缺offers", lp, "")
                    elif isinstance(offers, dict):
                        # 有 offers 但无价格 = 「询价型」（无报价依据，按用户决策不编造价格），
                        # 记为提示而非硬错：GSC 只会给「缺少 price」软警告。
                        has_price = ("lowPrice" in offers or "highPrice" in offers or
                                     "price" in offers)
                        if not has_price:
                            note("9.offers无价格(询价型·设计内)", lp, offers.get("@type", ""))

            # 10 图片 alt / og
            imgs = re.findall(r"<img\b[^>]*>", h)
            if imgs:
                noalt = [i for i in imgs if not re.search(r'\salt="[^"]+"', i)]
                if noalt:
                    note("10.图片缺alt", lp, "%d/%d" % (len(noalt), len(imgs)))
            if not meta(h, "og:title") or not meta(h, "og:image"):
                note("10.缺og标签", lp, "")

            # 11 viewport / 英文残留
            if 'name="viewport"' not in h:
                note("11.缺viewport", lp, "")
            hits = [s for s in EN_LEFTOVERS if s in h]
            if hits:
                note("11.英文UI残留", lp, ",".join(hits[:3]))

            # 12 sitemap（语言首页可能登记成 /de/ 形式）
            if sm and (SITE + lp) not in sm and (SITE + lg + "/") not in sm:
                note("12.sitemap漏收", lp, "")

    print("\n================ 体检结果 ================")
    if not counts:
        print("✅ 全部通过，无问题")
    for k in sorted(counts):
        items = problems[k]
        print("\n❌ %s：%d 处" % (k, counts[k]))
        if args.verbose:
            for rel, d in items[:40]:
                print("    %-46s %s" % (rel, d))
        else:
            for rel, d in items[:8]:
                print("    %-46s %s" % (rel, d))
            if len(items) > 8:
                print("    … 还有 %d 条（--verbose 展开）" % (len(items) - 8))
    print("\n合计问题 %d 处" % sum(counts.values()))


if __name__ == "__main__":
    main()
