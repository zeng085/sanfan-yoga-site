# -*- coding: utf-8 -*-
"""清掉「回声污染」的翻译缓存条目（译文 == 原文）。

背景：2026-09-12 第五批生成时，主引擎失败 → 兜底 MyMemory 原样返回英文，
而 translator 把它当成译文写进了缓存。结果是 54 个产品页 × 6 语言的
title / h1 / description / 正文全是英文；更糟的是**重跑也没用** ——
命中缓存后连 API 都不调（deepl=0），错误被永久固化。

做法：把每个 EN 页面的候选文本（正文文本节点 + title + meta + 属性 + JSON-LD 串）
按 translator 的键规则算出 md5，凡是缓存里 value == 原文的就删掉，
下次生成会真正走 API。术语缩写（TPE/EVA/SANFAN）不算污染，跳过。

用法
    python3 i18n_build/purge_bad_cache.py --dry-run
    python3 i18n_build/purge_bad_cache.py
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_pages as B  # noqa: E402
import translator as T  # noqa: E402

ROOT = B.ROOT
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
ATTR_RE = re.compile(r"([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*\"([^\"]*)\"")
TRANS_META = getattr(B, "TRANS_META", ("description", "og:title", "og:description",
                                       "twitter:title", "twitter:description"))


def candidates(rel):
    """一个 EN 页面里所有会被送去翻译的字符串。"""
    h = open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace").read()
    out = set()
    try:
        r = B.collect_texts(h)
        # 返回值个数随版本变化（3 / 5），取其中第一个 list 当文本列表
        texts = next((x for x in r if isinstance(x, list)), [])
        out.update(t.strip() for t in texts if isinstance(t, str) and t.strip())
    except Exception as e:
        print("  ⚠ collect_texts 失败 %s: %s" % (rel, str(e)[:60]))
    for m in re.finditer(r"<title>([\s\S]*?)</title>", h):
        out.add(m.group(1).strip())
    for m in re.finditer(r"<meta\b[^>]*>", h):
        nm = re.search(r'(?:name|property)=["\']([^"\']+)["\']', m.group(0))
        cm = re.search(r'content=["\']([^"\']*)["\']', m.group(0))
        if nm and cm and nm.group(1) in TRANS_META:
            out.add(cm.group(1).strip())
    for m in ATTR_RE.finditer(h):
        v = m.group(2).strip()
        if re.search(r"[A-Za-z]{4,}", v) and len(v) < 300:
            out.add(v)
    # 页面里是转义形态（&amp;），而 build_pages 送翻译前会 unescape 成裸 &，
    # 两种形态各自占一个缓存键 —— 都要当成候选，否则漏掉一半回声。
    import html as _html
    for s in list(out):
        u = _html.unescape(s)
        if u != s:
            out.add(u)
    for m in re.finditer(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
                         h, re.S | re.I):
        try:
            obj = json.loads(m.group(1))
        except Exception:
            continue
        def walk(o):
            if isinstance(o, dict):
                walk(o.get("name")), walk(o.get("description"))
            elif isinstance(o, list):
                for x in o:
                    walk(x)
            elif isinstance(o, str) and 3 < len(o) < 300:
                out.add(o.strip())
        walk(obj)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", default="", help="只处理这批页面（json 清单）")
    args = ap.parse_args()

    pages = B.ALL_PAGES
    if args.only:
        pages = json.load(open(args.only, encoding="utf-8"))["pages"]

    cache = T._cache
    before = len(cache)
    seen = set()
    purged = 0
    hit_pages = []
    for rel in pages:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        hit_here = 0
        affected = []
        for s in candidates(rel):
            if s in seen:
                continue
            seen.add(s)
            if not T._looks_translatable(s):
                continue
            for lg in LANGS:
                # 大小写两种键都要查：历史上一会儿写 en>de 一会儿写 en>DE
                for variant in (lg, lg.upper()):
                    k = T._ck(s, variant, "EN")
                    v = cache.get(k)
                    if v is not None and isinstance(v, str) and v.strip() == s.strip():
                        purged += 1
                        hit_here += 1
                        if not args.dry_run:
                            del cache[k]
                        break
        if hit_here:
            hit_pages.append(rel)
    if hit_pages:
        json.dump({"_note": "缓存回声清理后需要重新生成的页面",
                   "pages": sorted(set(hit_pages))},
                  open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "i18n_batch7_purge.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print("受影响页面 %d 个 -> i18n_batch7_purge.json" % len(set(hit_pages)))
    print("候选字符串 %d 条；缓存 %d → %d 条；回声条目 %d 个%s"
          % (len(seen), before, len(cache), purged, "（dry-run 未写盘）" if args.dry_run else ""))
    if not args.dry_run and purged:
        T._save_cache(force=True)
        print("✅ 已清理并写盘")


if __name__ == "__main__":
    main()
