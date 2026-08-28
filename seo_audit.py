#!/usr/bin/env python3
"""SEO 站内体检脚本：解析站点所有 HTML，提取 SEO 信号并生成结构摘要。"""
import os
import re
import json
from html.parser import HTMLParser
from urllib.parse import urljoin

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGES = ["index.html", "about.html", "products.html", "product.html",
         "contact.html", "faq.html", "blog.html"]
BLOG = ["blog/tpe-vs-pu.html", "blog/moq-explained.html", "blog/compliance.html",
        "blog/vet-factory.html", "blog/7day-sampling.html", "blog/custom-sizes.html"]
ALL = PAGES + BLOG

class Extractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.in_title = False
        self.metas = {}
        self.canonical = None
        self.h1 = []
        self.h2 = []
        self.h3 = []
        self.imgs = []          # (src, alt)
        self.links = []          # href
        self.jsonld = []
        self._buf = ""
        self._tag = None
        self._attrs_stack = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "title":
            self.in_title = True
            self._buf = ""
        elif tag == "meta":
            name = (d.get("name") or "").lower()
            prop = (d.get("property") or "").lower()
            content = d.get("content", "")
            if name in ("description", "keywords", "robots", "viewport"):
                self.metas[name] = content
            if prop in ("og:title", "og:description", "og:image", "og:type", "og:url"):
                self.metas[prop] = content
            if prop.startswith("article:"):
                self.metas[prop] = content
        elif tag == "link" and d.get("rel", "").lower() == "canonical":
            self.canonical = d.get("href")
        elif tag == "h1":
            self._tag = "h1"; self._buf = ""
        elif tag == "h2":
            self._tag = "h2"; self._buf = ""
        elif tag == "h3":
            self._tag = "h3"; self._buf = ""
        elif tag == "img":
            self.imgs.append((d.get("src"), d.get("alt")))
        elif tag == "a":
            href = d.get("href")
            if href:
                self.links.append(href)
        elif tag == "script" and d.get("type") == "application/ld+json":
            self._tag = "jsonld"; self._buf = ""
        self._attrs_stack.append(tag)

    def handle_endtag(self, tag):
        if tag == "title" and self.in_title:
            self.title = self._buf.strip()
            self.in_title = False
        elif tag == "h1" and self._tag == "h1":
            self.h1.append(self._buf.strip()); self._tag = None
        elif tag == "h2" and self._tag == "h2":
            self.h2.append(self._buf.strip()); self._tag = None
        elif tag == "h3" and self._tag == "h3":
            self.h3.append(self._buf.strip()); self._tag = None
        elif tag == "script" and self._tag == "jsonld":
            raw = self._buf.strip()
            try:
                self.jsonld.append(json.loads(raw))
            except Exception:
                self.jsonld.append({"__raw": raw[:200]})
            self._tag = None

    def handle_data(self, data):
        if self.in_title or self._tag in ("h1", "h2", "h3", "jsonld"):
            self._buf += data

def clean(t):
    return re.sub(r"\s+", " ", t).strip()

def main():
    report = {}
    for p in ALL:
        path = os.path.join(ROOT, p)
        if not os.path.exists(path):
            report[p] = {"__missing": True}
            continue
        with open(path, encoding="utf-8") as f:
            html = f.read()
        ex = Extractor()
        ex.feed(html)
        # word count of body text
        body_text = re.sub(r"<script[\s\S]*?</script>", "", html)
        body_text = re.sub(r"<style[\s\S]*?</style>", "", body_text)
        body_text = re.sub(r"<[^>]+>", " ", body_text)
        words_en = len(re.findall(r"[A-Za-z]+", body_text))
        words_zh = len(re.findall(r"[一-鿿]", body_text))
        # internal vs external links
        internal = [l for l in ex.links if l and not l.startswith(("http://", "https://", "mailto:", "tel:", "#"))]
        external = [l for l in ex.links if l and l.startswith(("http://", "https://"))]
        # images missing alt
        img_total = len(ex.imgs)
        img_no_alt = sum(1 for s, a in ex.imgs if not (a and a.strip()))
        jld_types = []
        for j in ex.jsonld:
            if isinstance(j, dict):
                if "@graph" in j:
                    jld_types += [n.get("@type") for n in j["@graph"] if isinstance(n, dict)]
                else:
                    jld_types.append(j.get("@type"))
        report[p] = {
            "title": clean(ex.title),
            "title_len": len(ex.title),
            "desc": clean(ex.metas.get("description", "")),
            "desc_len": len(ex.metas.get("description", "")),
            "canonical": ex.canonical,
            "h1": [clean(h) for h in ex.h1],
            "h1_count": len(ex.h1),
            "h2_count": len(ex.h2),
            "h3_count": len(ex.h3),
            "img_total": img_total,
            "img_no_alt": img_no_alt,
            "internal_links": len(internal),
            "external_links": len(external),
            "words_en": words_en,
            "words_zh": words_zh,
            "jsonld_types": jld_types,
            "has_og": any(k.startswith("og:") for k in ex.metas),
            "lang_attr": None,
        }
        m = re.search(r"<html[^>]*\blang=([\"'])([^\"']+)\1", html)
        if m:
            report[p]["lang_attr"] = m.group(2)
    # print compact
    for p, r in report.items():
        if r.get("__missing"):
            print(f"[MISSING] {p}")
            continue
        print(f"\n=== {p} ===")
        print(f"  <title> ({r['title_len']}): {r['title']}")
        print(f"  meta desc ({r['desc_len']}): {r['desc'][:90]}{'...' if len(r['desc'])>90 else ''}")
        print(f"  canonical: {r['canonical']}")
        print(f"  h1 x{r['h1_count']}: {r['h1']}")
        print(f"  h2 x{r['h2_count']}, h3 x{r['h3_count']}")
        print(f"  imgs {r['img_total']} (no-alt {r['img_no_alt']})")
        print(f"  links: internal {r['internal_links']}, external {r['external_links']}")
        print(f"  words: en {r['words_en']}, zh {r['words_zh']}")
        print(f"  JSON-LD: {r['jsonld_types']}")
        print(f"  OG tags: {r['has_og']}, <html lang>: {r['lang_attr']}")
    # summary of issues
    print("\n\n========== ISSUE SCAN ==========")
    for p, r in report.items():
        if r.get("__missing"):
            continue
        issues = []
        if r["h1_count"] != 1:
            issues.append(f"H1 数量={r['h1_count']}(应=1)")
        if not r["desc"]:
            issues.append("缺 meta description")
        elif not (120 <= r["desc_len"] <= 200):
            issues.append(f"meta desc 长度={r['desc_len']}(建议120-200)")
        if r["title_len"] < 30 or r["title_len"] > 65:
            issues.append(f"title 长度={r['title_len']}(建议30-65)")
        if r["img_no_alt"]:
            issues.append(f"{r['img_no_alt']}张图缺 alt")
        if not r["canonical"]:
            issues.append("缺 canonical")
        if not r["jsonld_types"]:
            issues.append("无结构化数据")
        if r["words_en"] < 200 and r["words_zh"] < 200:
            issues.append(f"正文偏薄(en{r['words_en']}/zh{r['words_zh']})")
        if issues:
            print(f"  [{p}] " + " | ".join(issues))

if __name__ == "__main__":
    main()
