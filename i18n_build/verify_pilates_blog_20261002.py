#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""6 篇普拉提博客校验：标签配平 / JSON-LD / desc 宽度 / 内链存在 / 事实分级 / sitemap。
用法：python3 i18n_build/verify_pilates_blog_20261002.py
"""
import json
import os
import re
import sys
import html as H
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SLUGS = ["pilates-reformer-buyers-guide", "pilates-apparatus-differences",
         "pilates-studio-equipment-list", "oem-pilates-equipment-china",
         "pilates-studio-layout-guide", "pilates-equipment-commercial-use"]
TAGS = ["div", "span", "section", "article", "table", "thead", "tbody", "tr", "td", "th",
        "ul", "li", "p", "h1", "h2", "h3", "a", "nav", "header", "footer", "script", "figure"]
VOID = {"img", "br", "meta", "link", "input", "hr", "source"}

# E 级禁用词（价格 / MOQ 数额 / 弹簧参数 / 承重 / 器械认证 / 保修）
FORBIDDEN = [
    (r"\bUSD\b|\bUS\$\s?\d|\$\s?\d|\u00a5\s?\d|\bprice list\b|\bunit price\b|\bprice:\s*\d", "价格"),
    (r"\bMOQ\s*(of|is|:)?\s*\d", "MOQ 数额"),
    (r"\bspring (tension|count|force|rate)\b|\b\d+\s*springs?\b", "弹簧参数"),
    (r"\b(max(imum)? (user |)weight|load (capacity|rating)|weight capacity)\b", "承重"),
    (r"\b(warranty|guarantee|guaranteed)\b", "保修/保证"),
    # 大小写敏感：小写 reach/ce 是普通词（"crates reach 930 mm"），只有大写形态才是认证主张
    (r"\b(?:ISO 9001|BSCI|CE mark|REACH|Prop 65|EN 957)\b", "器械认证"),
    (r"\b(lifetime|10-year|5-year)\b", "寿命承诺"),
]


class Balance(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.errs = [], []

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errs.append("多余闭合 </%s>" % tag)
        elif self.stack[-1] != tag:
            self.errs.append("错配：栈顶 <%s> vs </%s>" % (self.stack[-1], tag))
            if tag in self.stack:
                while self.stack and self.stack.pop() != tag:
                    pass
        else:
            self.stack.pop()

    def close(self):
        super().close()
        if self.stack:
            self.errs.append("未闭合：" + ",".join(self.stack[-5:]))


def disp_width(s):
    return sum(2 if ord(c) > 0x2E7F else 1 for c in s)


def main():
    fail = 0

    def chk(name, ok, extra=""):
        nonlocal fail
        print(("%s %s%s" % ("\u2713" if ok else "\u2717", name, "  " + extra if extra else "")))
        if not ok:
            fail += 1

    all_internal = set()
    for slug in SLUGS:
        path = os.path.join(ROOT, "blog", slug + ".html")
        s = open(path, encoding="utf-8").read()
        print("\n===== %s =====" % slug)

        # 1) 标签配平（解析器级）
        b = Balance()
        b.feed(s)
        b.close()
        chk("HTML 嵌套配平", not b.errs, "; ".join(b.errs[:3]))
        for t in ("div", "section", "table", "ul", "li", "h2", "h3"):
            a = len(re.findall(r"<%s\b" % t, s))
            c = s.count("</%s>" % t)
            if a != c:
                chk("<%s> 计数配平" % t, False, "%d vs %d" % (a, c))
                break
        else:
            chk("主要标签计数配平", True, "div %d 对" % len(re.findall(r"<div\b", s)))

        # 2) JSON-LD
        lds = re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
        chk("JSON-LD 2 块且可解析", len(lds) == 2 and all(
            (lambda x: (json.loads(x) or True))(x) for x in lds), "%d 块" % len(lds))
        types = [json.loads(x).get("@type") for x in lds]
        chk("含 Article + FAQPage", types == ["Article", "FAQPage"], str(types))
        faq = json.loads(lds[1])
        chk("FAQ 5 条", len(faq["mainEntity"]) == 5)

        # FAQ LD 与可见正文对应
        visible = re.sub(r"<script.*?</script>", "", s, flags=re.S)
        vis_text = H.unescape(re.sub(r"<[^>]+>", " ", visible))
        vis_text = re.sub(r"\s+", " ", vis_text)
        hit = sum(1 for it in faq["mainEntity"]
                  if re.sub(r"\s+", " ", it["name"]).strip() in vis_text)
        chk("FAQ 题在可见正文中出现（结构化数据合规）", hit == 5, "%d/5" % hit)

        # 3) title / desc 显示宽度
        t = re.search(r"<title>(.*?)</title>", s, re.S).group(1)
        d = re.search(r'<meta name="description" content="(.*?)"', s, re.S).group(1)
        chk("title 显示宽 ≤60", disp_width(H.unescape(t)) <= 60,
            "%d「%s」" % (disp_width(H.unescape(t)), t[:44]))
        chk("desc 显示宽 ≤155", disp_width(H.unescape(d)) <= 155,
            "%d" % disp_width(H.unescape(d)))

        # 4) canonical / hreflang（本期只 en + x-default，不得指向未存在的语言页）
        can = re.search(r'<link rel="canonical" href="(.*?)"', s).group(1)
        chk("canonical 正确", can == "https://fjsanfan.com/blog/%s.html" % slug, can)
        hre = re.findall(r'<link rel="alternate" hreflang="([a-z\-]+)"', s)
        chk("hreflang 仅 en + x-default", sorted(set(hre)) == ["en", "x-default"], str(sorted(set(hre))))

        # 5) 内链存在性
        for href in set(re.findall(r'href="(\.\./[^"#]+\.html)(?:#[^"]*)?"', s)):
            target = os.path.normpath(os.path.join(ROOT, "blog", href))
            if not os.path.exists(target):
                chk("内链存在 %s" % href, False)
                break
            all_internal.add(href)
        else:
            chk("内链目标全部存在", True, "%d 个" % len(set(re.findall(r'href="(\.\./[^"#]+\.html)', s))))

        # 6) 事实分级：E 级禁用
        hits = []
        for pat, lab in FORBIDDEN:
            flags = 0 if lab == "器械认证" else re.I     # 认证项大小写敏感
            if re.search(pat, vis_text, flags):
                hits.append(lab)
        chk("无 E 级信息（价格/MOQ 数额/弹簧/承重/认证/保修）", not hits, str(hits))

        # 7) 图片均有 width/height + alt + lazy
        imgs = re.findall(r"<img [^>]*>", s)
        chk("img 全带 width/height/alt",
            all(("width=" in i and "height=" in i and 'alt="' in i) for i in imgs),
            "%d 张" % len(imgs))

    # 8) 索引 / sitemap / llms 接入
    blog = open(os.path.join(ROOT, "blog.html"), encoding="utf-8").read()
    chk("blog.html 6 张卡", all("blog/%s.html" % x in blog for x in SLUGS))
    sm = open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read()
    chk("sitemap 6 条 url", all(("<loc>https://fjsanfan.com/blog/%s.html</loc>" % x) in sm for x in SLUGS))
    chk("sitemap 结构完整", sm.count("</urlset>") == 1 and sm.count("<url>") == sm.count("</url>"))
    import xml.etree.ElementTree as ET
    ET.fromstring(sm)
    chk("sitemap XML 可解析", True)
    for fn in ("llms.txt", "llms-full.txt"):
        txt = open(os.path.join(ROOT, fn), encoding="utf-8").read()
        chk("%s 含 6 篇" % fn, all(("blog/%s.html" % x) in txt for x in SLUGS))
        chk("%s 型号数口径已更新（无 41 models 残留）" % fn, "41 wooden studio models" not in txt and "41 models, 8 families" not in txt)
    idx = open(os.path.join(ROOT, "pilates", "index.html"), encoding="utf-8").read()
    chk("pilates/index.html 指南区 6 卡", idx.count('href="../blog/') == 6, "%d" % idx.count('href="../blog/'))

    # 9) 数字溯源：页面里每个尺寸/毛重都必须能在「已上线族页公布数据」里找到，
    #    且「最长/最宽/最高/最重」这类最高级断言必须等于族页算出的极值。
    #    2026-10-02 实测抓出过两处硬编码断言（2570 冒充最长、860 冒充最高）。
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from pilates_figures_20261002 import (EXTREMES, verify_numbers,         # noqa: E402
                                          verify_superlatives)
    for x in SLUGS:
        s = open(os.path.join(ROOT, "blog", x + ".html"), encoding="utf-8").read()
        ok_n, prob_n = verify_numbers(s, x)
        chk("数字可溯源至族页公布数据", ok_n, str(prob_n[:3]) if prob_n else "全部命中")
        ok_s, prob_s = verify_superlatives(s, x)
        chk("最高级断言 = 族页极值", ok_s,
            str(prob_s[:2]) if prob_s else
            "longest %s / widest %s / tallest %s / heaviest %s"
            % (EXTREMES["longest"]["value"], EXTREMES["widest"]["value"],
               EXTREMES["tallest"]["value"], EXTREMES["heaviest"]["value"]))

    print("\n%s" % ("\u2713 全部通过" if fail == 0 else "\u2717 %d 项失败" % fail))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
