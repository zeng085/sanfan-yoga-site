#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全站「链接准确性」审计（2026-09-16）

判据（全部可机械判定，不掺主观）：
  A 目标文件存在性 —— 把站内 href（绝对 /xx/、相对 xxx.html、../xx）解析成磁盘路径，
    必须存在；目录型 href（/pilates/）解析成 <dir>/index.html。
  B 跨语言误链 —— 语言页（/de/ 等）里出现指向**其它语言或英文根区**的站内链接。
    英文根区是重点：语言页指向 /pilates/ 会让用户从德语页跳到英文页。
    白名单：语言切换器（.lang-menu 里的 <a data-setlang> / hreflang）、hreflang 标签。
  C 锚点存在性 —— href 带 #frag 时，目标页必须真实存在 id="frag"（# 与外部链接除外）。
  D 空 href / 占位 href（href=""、"#"）—— 只统计 <a> 正文链接，脚本内的 # 不算。
输出：控制台摘要 + i18n_build/reports/links_20260916.json（明细）
"""
import glob
import html
import json
import os
import re
import sys
from collections import Counter, defaultdict
from urllib.parse import unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
OUT = os.path.join(ROOT, "i18n_build", "reports")

# 非 HTML 资源目录（不会被当页面解析）
# i18n_build/ 是构建脚本与中间产物目录，不进 Vercel 产物，不参与站内链接审计
SKIP_DIRS = (".git", "node_modules", "outputs", "i18n_build", "__pycache__")

HREF_RX = re.compile(r'<a\b[^>]*?href="([^"]*)"[^>]*>', re.I)
ID_RX = re.compile(r'\bid="([^"]+)"')
TAG_LANG_RX = re.compile(r'<link[^>]+hreflang=', re.I)


def all_pages():
    for f in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True):
        rel = os.path.relpath(f, ROOT)
        if rel.startswith(SKIP_DIRS):
            continue
        yield f, rel


def page_lang(rel):
    seg = rel.split(os.sep)
    return seg[0] if seg[0] in LANGS else ""


def exists_target(rel_from, href):
    """把 href 解析成磁盘路径并判断是否存在。返回 (ok, 说明)"""
    path = unquote(href.split("#")[0].split("?")[0])
    if not path:
        return True, "anchor-only"
    if path.startswith("/"):
        disk = os.path.join(ROOT, path.lstrip("/"))
    else:
        disk = os.path.normpath(os.path.join(ROOT, os.path.dirname(rel_from), path))
    cand = [disk]
    if disk.endswith("/") or not os.path.splitext(disk)[1]:
        cand = [os.path.join(disk, "index.html"), disk + ".html"]
    for c in cand:
        if os.path.isfile(c):
            return True, os.path.relpath(c, ROOT)
    return False, os.path.relpath(disk, ROOT)


def main():
    os.makedirs(OUT, exist_ok=True)
    pages = list(all_pages())
    # 先建 id 索引，供锚点校验
    ids = {}
    text = {}
    for f, rel in pages:
        s = open(f, encoding="utf-8", errors="ignore").read()
        text[rel] = s
        ids[rel] = set(ID_RX.findall(s))

    miss = defaultdict(list)      # 目标不存在
    xlang = defaultdict(list)     # 跨语言误链
    frag = defaultdict(list)      # 锚点不存在
    empty = defaultdict(list)     # 空 href
    total_links = 0
    per_page = Counter()

    for f, rel in pages:
        s = text[rel]
        lg = page_lang(rel)
        body = re.sub(r'<div class="lang-menu">.*?</div>', "", s, flags=re.S)  # 语言菜单豁免
        for m in HREF_RX.finditer(body):
            href = html.unescape(m.group(1)).strip()
            total_links += 1
            per_page[rel] += 1
            if href in ("", "#"):
                empty[rel].append(href or "(空)")
                continue
            if re.match(r'^(?:https?:|mailto:|tel:|javascript:|data:|#)', href):
                if href.startswith("#") and len(href) > 1:
                    if href[1:] not in ids.get(rel, set()):
                        frag[rel].append(href)
                continue
            ok, info = exists_target(rel, href)
            if not ok:
                miss[rel].append((href, info))
                continue
            # 跨语言判定：语言页 → 链接目标不在该语言目录下（且不是同级资源）
            if lg:
                tgt = info if isinstance(info, str) else ""
                tgt_lang = tgt.split(os.sep)[0] if os.sep in tgt else ""
                if tgt and tgt_lang != lg and tgt_lang in LANGS + ["products", "applications", "blog", "pilates", "assets"] + [""]:
                    # 站内页面级链接（.html 或目录 index.html）才算
                    if tgt.endswith(".html"):
                        xlang[rel].append((href, tgt))
            if "#" in href and not href.startswith("#"):
                tgt, frag_id = href.split("#", 1)
                if frag_id:
                    ok2, info2 = exists_target(rel, tgt)
                    if ok2 and isinstance(info2, str) and info2.endswith(".html"):
                        if frag_id not in ids.get(info2, set()):
                            frag[rel].append(href)

    print("=" * 72)
    print("全站链接审计：%d 页 / %d 个 <a> 链接" % (len(pages), total_links))
    print("=" * 72)

    def summarise(name, d, fmt):
        tot = sum(len(v) for v in d.values())
        print("\n【%s】%d 处 / %d 页" % (name, tot, len(d)))
        for rel, v in sorted(d.items(), key=lambda kv: -len(kv[1]))[:12]:
            print("   %-56s %d" % (rel, len(v)))
            for item in v[:2]:
                print("        %s" % fmt(item))
        return tot

    t_miss = summarise("A 目标不存在（404）", miss,
                       lambda x: "%s → 解析为 %s" % x)
    t_x = summarise("B 跨语言误链", xlang, lambda x: "%s → %s" % x)
    t_f = summarise("C 锚点不存在", frag, lambda x: x)
    t_e = summarise("D 空/占位 href", empty, lambda x: repr(x))

    print("\n合计：404 %d · 跨语言 %d · 坏锚点 %d · 空 href %d" % (t_miss, t_x, t_f, t_e))

    json.dump({"miss": {k: v for k, v in miss.items()},
               "cross_lang": {k: v for k, v in xlang.items()},
               "bad_fragment": {k: v for k, v in frag.items()},
               "empty_href": {k: v for k, v in empty.items()},
               "totals": {"pages": len(pages), "links": total_links, "miss": t_miss,
                          "cross_lang": t_x, "bad_fragment": t_f, "empty_href": t_e}},
              open(os.path.join(OUT, "links_20260916.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("明细 → i18n_build/reports/links_20260916.json")


if __name__ == "__main__":
    main()
