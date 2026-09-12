#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""，把第三批差集输出成可读的 Markdown 清单。"""
import ast
import collections
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "i18n_build"))
from pending_batch3 import clean_slugs, FAMILY, BATCHES  # noqa: E402

CATALOG = ROOT / "outputs" / "sf_catalog_full.json"


def specs_of(c):
    s = c.get("specs")
    if isinstance(s, str):
        try:
            s = ast.literal_eval(s)
        except Exception:
            s = {}
    return s or {}


def main():
    secs = clean_slugs()
    cat = {c["slug"]: c for c in json.load(open(CATALOG, encoding="utf-8"))}

    mapping = {}
    for b in BATCHES:
        for it in json.load(open(ROOT / b, encoding="utf-8")):
            mapping[it["src"]] = it["new"]
    mapping.update(FAMILY)

    missing = [(n, s) for n, v in secs.items() for s in v if s not in mapping]

    rows = []
    for n, s in missing:
        c = cat.get(s, {})
        sp = specs_of(c)
        im = c.get("images") or []
        if isinstance(im, str):
            im = []
        rows.append({
            "cat": n, "slug": s, "title": c.get("title_en", ""),
            "shell": not sp, "spec": len(sp), "img": len(im),
            "link": c.get("link", ""),
        })

    # 建议顺序：先上有真实规格+图多的（转化率高），空壳页放最后
    solid = [r for r in rows if not r["shell"]]
    shell = [r for r in rows if r["shell"]]
    solid.sort(key=lambda r: (-r["spec"], -r["img"], r["cat"]))

    b3 = json.load(open(ROOT / "outputs" / "batch3_pages.json", encoding="utf-8"))
    fam_pages = sorted(set(FAMILY.values()))

    L = []
    L.append("# 待上线清单（截至 2026-09-12）\n")
    L.append("规则：产品以英文站 sanfansport.com 为准，分批推进，先 EN + 中文。\n")
    L.append("| 项 | 数量 |")
    L.append("|---|---|")
    L.append("| 英文站清洗后产品 | 147 |")
    L.append("| 第一批已上（垫类） | 56 |")
    L.append("| 第二批已上（放松按摩 + 配件） | 40 |")
    L.append("| 第三批已上（跳绳 + 力量健身 + 吊床） | %d |" % len(b3))
    L.append("| 老页就地更新（家族页，吞掉多个英文站 SKU） | %d（%s） |"
             % (len(FAMILY), " / ".join(fam_pages)))
    L.append(f"| **剩余未上线** | **{len(rows)}** |")
    L.append(f"| 　其中有真实规格（可直接上） | {len(solid)} |")
    L.append(f"| 　其中空壳页（仅兜底 3 行） | {len(shell)} |")
    L.append("")

    L.append("> ⚠️ **命名对应关系**：本站页 slug 是重命名过的，不能按 slug 直接比对。"
             "例如 `alignment-line-tpe-yoga-mat` 对应英文站 `tpe-yoga-mat-special-dual-color-body-line`。"
             "唯一权威映射在 `outputs/batch{1,2}_pages.json` 的 `src → new`。\n")

    L.append("## 一、可直接上的（有真实规格）\n")
    L.append("按「规格条数 → 图片数」降序，规格越全、图越多越优先。\n")
    bycat = collections.defaultdict(list)
    for r in solid:
        bycat[r["cat"]].append(r)
    for n in sorted(bycat, key=lambda x: -len(bycat[x])):
        rs = bycat[n]
        L.append(f"### {n}（{len(rs)} 个）\n")
        L.append("| # | 英文站 slug | 英文标题 | 规格 | 图 |")
        L.append("|---|---|---|---|---|")
        for i, r in enumerate(rs, 1):
            L.append(f"| {i} | `{r['slug']}` | {r['title']} | {r['spec']} 条 | {r['img']} |")
        L.append("")

    L.append("## 二、空壳页（content 为空，只有标题和图）\n")
    L.append("**规则：绝不编造数值**，只上兜底 3 行（Material / Size / MOQ），并在页面上标注待补。\n")
    L.append("| # | 英文站 slug | 英文标题 | 图 |")
    L.append("|---|---|---|---|")
    for i, r in enumerate(shell, 1):
        L.append(f"| {i} | `{r['slug']}` | {r['title']} | {r['img']} |")
    L.append("")

    out = ROOT / "outputs" / "第三批待上线清单-2026-09-12.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print("已写出", out)
    print(f"可直接上 {len(solid)} / 空壳 {len(shell)} / 合计 {len(rows)}")


if __name__ == "__main__":
    main()
