#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""定点清缓存：把「源文命中某术语、但译文没按术语表走」的缓存键清掉，供重生成时按新术语重译。

为什么需要它（铁律 16 的同类问题）：
  术语表改动**只影响新翻译**，命中缓存的旧译文照旧 —— 不点掉脏键就永远修不了。
  而盲目清整语言（几千条）会让全站重翻，代价大；所以按「源文正则」精确定位。

做法：
  · 用 build_pages 的抽取管线拿到源文本节点（与生成时**同一套键**，不会错位）
  · 源文匹配 --match 正则，且译文**不含** --must-contain 列表里的任一串 → 删键
用法：
    python3 i18n_build/purge_cache_by_term_20261002.py --batch /tmp/batch15.json \
        --match "packing list" --must-contain "패킹|Packliste|パッキング|colisage|imballaggio|embalaje" --dry
"""
import os
import re
import sys
import json
import html as H

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import translator as T  # noqa: E402
import build_pages as B  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def nodes_of(rel_path):
    """与 build_pages.build_one 完全同源的文本节点（同样的清洗 → 同样的缓存键）"""
    h = open(os.path.join(ROOT, rel_path), encoding="utf-8").read()
    h = B.remove_i18n_attrs(B.relax_lang_en(B.strip_lang_zh(h)))
    _, _, texts, _, _ = B.collect_texts(h)
    out = []
    for _, raw in texts:
        s = H.unescape(raw.strip())
        if s:
            out.append(s)
    return out


def main():
    a = sys.argv[1:]
    batch, match, must, dry = None, None, None, "--dry" in a
    for i, x in enumerate(a):
        if x == "--batch":
            batch = json.load(open(a[i + 1], encoding="utf-8"))["pages"]
        if x == "--match":
            match = re.compile(a[i + 1], re.I)
        if x == "--must-contain":
            must = re.compile(a[i + 1], re.I)
    assert batch and match and must, "需要 --batch / --match / --must-contain"
    langs = T.__dict__.get("LANGS") or ["de", "ja", "ko", "fr", "it", "es"]

    srcs = set()
    for p in batch:
        for s in nodes_of(p):
            if match.search(s):
                srcs.add(s)
    print("源文命中 %d 条（去重后）" % len(srcs))

    removed = {}
    for lg in langs:
        for s in srcs:
            k = T._ck(s, lg)
            v = T._cache.get(k)
            if v is None:
                continue
            if not must.search(v):
                if not dry:
                    del T._cache[k]
                removed.setdefault(lg, []).append(s[:80])
    for lg, items in removed.items():
        print("  %s 待清 %d 条；例：%s" % (lg, len(items), items[0]))
        if dry:
            for s in items[:3]:
                print("      · %s" % s)
    print("\n%s：共清 %d 条" % ("DRY" if dry else "DONE", sum(len(v) for v in removed.values())))
    if not dry:
        T.flush()


if __name__ == "__main__":
    main()
