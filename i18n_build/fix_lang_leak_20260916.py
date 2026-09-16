#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清除渗进结构化数据/属性的「英中双语串」（2026-09-16）

【病根】EN 页卡片用「行内配对 span」双语机制：
    <h4><span class="lang-en">Alignment Line TPE Yoga Mat</span>
        <span class="lang-zh">带体位线 TPE 瑜伽垫</span></h4>
而 build_category_pages.py 的 title_of() 原先只做「剥标签 + 压空白」，
得到双语串 `Alignment Line TPE Yoga Mat 带体位线 TPE 瑜伽垫`，被写进两处：
  · JSON-LD  ItemList → itemListElement[].name
  · products.html 缩略图 → <a title="…"><img alt="…"></a>
随后翻译管线把 EN 那半翻成 de/fr/it/es/ja/ko，中文那半**原样保留**，于是
    de/tpe-yoga-mats.html: "name": "TPE-Yogamatte mit Ausrichtungslinien TPE 瑜伽垫"
7 个语言版本的结构化数据里混着中文（de 分类页 23 条里 17 条中招）。

【为什么不能「见中文就截尾」】德语页里 `Lila „TPE“-Yogamatte TPE`（原紫款）
已经**没有中文可截**了 —— 引擎把中文那半也当英文翻了一道，只剩一个残留 ` TPE`。
按字符判据修不干净，必须拿**该语言自己的干净标题**去重建。

【修法】干净标题的唯一可信来源 = 该语言卡片 `<h4>` 里**第一个非 .lang-zh 的 span**。
译版页面的卡片本来就是 `<h4><span >TPE Yogamatte</span></h4>`（干净），
所以能建出 slug → 该语言干净标题 的映射，再回填两处。

【为什么按 slug 锚定而不是按顺序】顺序虽一致（同源于 slugs 列表），
但按 slug 锚定可以在数量对不上时**什么都不改**，不会错位写坏。

用法：
    python3 fix_lang_leak_20260916.py --check     # 只报告
    python3 fix_lang_leak_20260916.py             # 落盘
"""
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LANGS = ["", "de", "ja", "ko", "fr", "it", "es"]
DIRS = ["", "products", "applications", "blog", "pilates"]

CARD_RE = re.compile(r'<a class="prod-card" href="[^"]*?([^/"#?]+)\.html">([\s\S]*?)</a>')
H4_RE = re.compile(r'<h4[^>]*>([\s\S]*?)</h4>')
ZH_SPAN_RE = re.compile(r'<span class="lang-zh">[\s\S]*?</span>')
TAG_RE = re.compile(r"<[^>]+>")
CJK_RE = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]")

# JSON-LD：以 url 里的 slug 锚定，避免误伤同页别的 name
JSONLD_NAME_RE = re.compile(
    r'("url":\s*"https?://[^"]*?/products/([A-Za-z0-9._-]+)\.html",\s*"name":\s*)'
    r'("(?:[^"\\]|\\.)*")')
# products.html 缩略图
THUMB_RE = re.compile(
    r'(<a href="(?:\.\./)?products/([A-Za-z0-9._-]+)\.html" title=")([^"]*)(">'
    r'<img src="[^"]*" loading="lazy" alt=")([^"]*)(")')


def pages():
    for lg in LANGS:
        for sub in DIRS:
            base = os.path.join(ROOT, lg) if lg else ROOT
            pat = os.path.join(base, sub, "*.html") if sub else os.path.join(base, "*.html")
            for f in sorted(glob.glob(pat)):
                yield lg, f


def clean_title(h4_inner):
    """剥掉中文配对 span 与所有标签 —— 与 build_category_pages.title_of 同口径。"""
    h = ZH_SPAN_RE.sub(" ", h4_inner)
    return " ".join(TAG_RE.sub(" ", h).split())


def build_map():
    """语言 → slug → 该语言的干净标题。

    ⚠️ `DIRS` 的顺序**就是优先级**：根目录（分类页）先扫，`products/` 里的
       「相关产品」卡片后扫。实测 `rb2` 在根目录分类页写作 `Mini Yoga Ball (25 cm / 10")`，
       而 `products/rb1.html` 的相关卡写作 `(25 cm (10"))`（h1 自带一个括号错），
       根目录优先才能取到与 `<title>` 一致的正确形态。
    """
    m = defaultdict(dict)
    conflict = []
    for lg, f in pages():
        s = open(f, encoding="utf-8", errors="ignore").read()
        for slug, body in CARD_RE.findall(s):
            h = H4_RE.search(body)
            if not h:
                continue
            t = clean_title(h.group(1))
            if not t:
                continue
            old = m[lg].get(slug)
            if old is not None and old != t:
                conflict.append((lg, slug, old, t))
            else:
                m[lg][slug] = t
    return m, conflict


def main():
    check = "--check" in sys.argv
    cmap, conflict = build_map()
    print("干净标题映射：%s" % "  ".join(
        "%s=%d" % (lg or "en", len(v)) for lg, v in sorted(cmap.items())))
    if conflict:
        print("⚠️ 同语言内同 slug 标题不一致 %d 处（取首个）：" % len(conflict))
        for lg, slug, a, b in conflict[:6]:
            print("   [%s] %s\n        %s\n        %s" % (lg or "en", slug, a, b))

    stat = Counter()
    unresolved = []
    samples = []
    for lg, f in pages():
        s = open(f, encoding="utf-8", errors="ignore").read()
        orig = s
        rel = os.path.relpath(f, ROOT)
        m = cmap.get(lg, {})
        is_products_list = os.path.basename(f) == "products.html"

        if '"ItemList"' in s:
            def sub_jsonld(mo):
                pre, slug, old_json = mo.group(1), mo.group(2), mo.group(3)
                clean = m.get(slug)
                if clean is None:
                    unresolved.append((rel, "jsonld", slug))
                    return mo.group(0)
                new_json = json.dumps(clean, ensure_ascii=False)
                if new_json == old_json:
                    return mo.group(0)
                try:
                    old_val = json.loads(old_json)
                except Exception:
                    old_val = old_json
                if CJK_RE.search(old_val) or len(old_val) > len(clean) + 4:
                    stat["jsonld"] += 1
                    if len(samples) < 10:
                        samples.append((rel, old_val, clean))
                    return pre + new_json
                return mo.group(0)
            s = JSONLD_NAME_RE.sub(sub_jsonld, s)

        if is_products_list:
            def sub_thumb(mo):
                head, slug, old_title, mid, old_alt, tail = mo.groups()
                clean = m.get(slug)
                if clean is None:
                    unresolved.append((rel, "thumb", slug))
                    return mo.group(0)
                esc = clean.replace('"', "&quot;")
                if esc == old_title and esc == old_alt:
                    return mo.group(0)
                stat["thumb"] += 1
                return head + esc + mid + esc + tail
            s = THUMB_RE.sub(sub_thumb, s)

        if s != orig:
            stat["_files"] += 1
            if not check:
                open(f, "w", encoding="utf-8").write(s)

    print("\n模式: %s" % ("检查(dry)" if check else "落盘"))
    print("改动文件 %d 个 | JSON-LD 条目 %d 处 | 缩略图 title/alt %d 处"
          % (stat["_files"], stat["jsonld"], stat["thumb"]))
    if unresolved:
        print("未被映射覆盖 %d 处（未改动）：" % len(unresolved))
        for rel, kind, slug in unresolved[:8]:
            print("   [%s] %s %s" % (kind, rel, slug))
    if samples:
        print("\n示例：")
        for rel, old, new in samples:
            print("  %-44s\n     旧: %s\n     新: %s" % (rel, old, new))


if __name__ == "__main__":
    main()
