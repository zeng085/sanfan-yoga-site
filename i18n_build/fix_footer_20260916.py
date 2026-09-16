#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""页脚「产品分类」列统一（2026-09-16）

问题（全站链接审计 audit_links_20260916.py 抓出）：
  站内存在**两代页脚**：
    新版（约 188 页：首页/关于/分类页/场景页）：10 个分类，直接指向分类页
        <a href="tpe-yoga-mats.html">TPE Yoga Mats</a> …
    旧版（**1079 页：全部产品详情页 + 全部博客页**）：5 个链接，指向
        products.html#yoga / #props / #rollers / #bands / #fitness
  旧版有两个硬伤：
    ① 5 个锚点在 products.html 里**根本不存在**（实测该页只有 id="applications"），
       点击只会落在页面顶部 —— 1079 × 5 = 5395 个死锚点；
    ② 锚点与文案对不上，且**同一 href 在不同页面上文案还不一样**：
       产品页 #yoga 写「Strength &amp; Fitness」、博客页 #yoga 写「Yoga Mats」。
  修法：把旧版这一列整块替换成**同语言新版页脚那一列**（文案与 href 一律照搬新版，
       相对前缀按页面层级补 ../），不新增任何新文案。

用法：
  python3 fix_footer_20260916.py            # 试运行（只报告）
  python3 fix_footer_20260916.py --apply    # 落盘
"""
import glob
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
ALL = [""] + LANGS

# 页脚里「产品分类」那一列（<div><h5>…</h5><ul>…</ul></div>）
COL_RX = re.compile(r"<div>\s*<h5[^>]*>[^<]*</h5>\s*<ul>.*?</ul>\s*</div>", re.S)


def lang_of(rel):
    seg = rel.split(os.sep)
    return seg[0] if seg[0] in LANGS else ""


def pick_source(lang):
    """挑一个「新版页脚」样本页：该语言下页脚产品列含 tpe-yoga-mats.html 的页。"""
    base = os.path.join(ROOT, lang) if lang else ROOT
    cands = []
    for name in ("index.html", "about.html", "products.html", "contact.html"):
        cands.append(os.path.join(base, name))
    cands += sorted(glob.glob(os.path.join(base, "*.html")))
    for f in cands:
        if not os.path.isfile(f):
            continue
        s = open(f, encoding="utf-8", errors="ignore").read()
        for m in COL_RX.finditer(s):
            if "tpe-yoga-mats.html" in m.group(0):
                return f, m.group(0)
    return None, None


def prefix_for(rel):
    """页面 → 语言根 的相对前缀"""
    lg = lang_of(rel)
    parts = rel.split(os.sep)
    depth = len(parts) - (1 if lg else 0)
    return "../" * (depth - 1)


def add_prefix(block, prefix):
    if not prefix:
        return block
    # 只给站内相对链接加前缀；http/mailto/tel/# 与非 href 属性不动
    def rep(m):
        href = m.group(2)
        if re.match(r"^(?:https?:|mailto:|tel:|#|/)", href):
            return m.group(0)
        # ⚠️ 这里踩过坑：group(1) 已经含 `href="` 本身，格式串里**不能再写一遍**，
        #    否则产出 `href="href="../x.html"` 这种双写属性（会静默毁掉全部 1078 页
        #    页脚链接，且目录计数看不出任何异常）。改完务必跑 render_one 断言。
        return '%s%s%s"' % (m.group(1), prefix, href)
    out = re.sub(r'(\shref=")([^"]*)"', rep, block)
    assert 'href="href="' not in out, "前缀展开把 href 写重了"
    return out


def main():
    apply = "--apply" in sys.argv
    for lang in ALL:
        src, block = pick_source(lang)
        tag = lang or "en"
        if not src:
            print("!! %s 找不到新版页脚样本，跳过" % tag)
            continue
        newblock = block.strip()
        print("\n=== %s 样本：%s（%d 条分类链接）" % (tag, os.path.relpath(src, ROOT), newblock.count("<li>")))
        pages = []
        for p in glob.glob(os.path.join(ROOT, lang, "**", "*.html"), recursive=True):
            rel = os.path.relpath(p, ROOT)
            if rel.startswith(("i18n_build", "outputs")):
                continue
            # lang="" 的 glob 会连 de/ ja/ … 一起捞进来 —— 剔掉，否则重复统计
            if lang == "" and rel.split(os.sep)[0] in LANGS:
                continue
            pages.append(p)
        n_old = n_new = 0
        touched = []
        for f in pages:
            rel = os.path.relpath(f, ROOT)
            s = open(f, encoding="utf-8").read()
            hits = [m for m in COL_RX.finditer(s) if "products.html#" in m.group(0)]
            if not hits:
                if "tpe-yoga-mats.html" in s:
                    n_new += 1
                continue
            n_old += 1
            if not apply:
                continue
            out, last = [], 0
            for m in hits:
                out.append(s[last:m.start()])
                out.append(add_prefix(newblock, prefix_for(rel)))
                last = m.end()
            out.append(s[last:])
            open(f, "w", encoding="utf-8").write("".join(out))
            touched.append(rel)
        print("    旧版 %d 页 → %s | 已是新版 %d 页" % (
            n_old, ("已替换 %d 页" % len(touched)) if apply else "（试运行未写）", n_new))


def rel_startswith_asset(p):
    return False


if __name__ == "__main__":
    main()
