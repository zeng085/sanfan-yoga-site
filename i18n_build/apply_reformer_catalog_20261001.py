#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把「画册重构」落到 pilates/pilates-reformer.html（样板页）

换数据源 ≠ 只换正文表格。旧体系在**四个层面**都还活着，必须一起换，
否则页面自相矛盾、搜索引擎读到的仍是旧型号：
  ① 可见正文：规格表 20 行（NIC/NLH/NIM 编码 + 旧材质口径）
  ② SEO meta：description / og / twitter 三处「20 models across 8 种旧木种」
  ③ JSON-LD：material 数组、offerCount、ItemList 的 20 条旧型号、FAQ 里的「all 20 models」
  ④ hero 文案：「20 models · 9 timber options」与 lead 里的 M-series

做法：把全部改动点算成 (start, end, new) 字符区间，**按 start 降序**依次替换
—— 这样前面的替换不会让后面的坐标漂移（用行号会）。

安全：默认 dry-run；--write 才落盘，落盘前先备份到 ~/.workbuddy/backups/fjsanfan/，
      落盘后立刻跑断言（旧串归零 / 标签配平 / 双语配对 / 计数）。

用法：
  python apply_reformer_catalog_20261001.py                 # dry-run
  python apply_reformer_catalog_20261001.py --write         # 落盘
"""
import argparse
import collections
import datetime
import json
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE_PAGE = ROOT / "pilates" / "pilates-reformer.html"
FRAG = ROOT / "outputs" / "pilates_family_reformer_20261001" / "block_reformer.html"
DATA = ROOT / "i18n_build" / "data" / "catalog_pilates_models_v2.json"
BACKUP_DIR = pathlib.Path.home() / ".workbuddy" / "backups" / "fjsanfan"

NEW_DESC = ("Pilates Reformer made to order: 46 models across three lines — "
            "aluminium, foldable and solid timber. Packed size and gross weight for every model. "
            "OEM/ODM with your logo, colour and material spec. Request a quote.")

NEW_MATERIAL = """      "material": [
        "Aluminium",
        "Carbon steel",
        "Metal",
        "Maple",
        "Oak"
      ],"""

NEW_LEAD_EN = ("The reformer is the machine a studio is built around. Our 2026 catalogue carries "
               "three reformer lines — aluminium, foldable and solid timber — 46 models in total, "
               "from compact home builds to full-track studio machines. Australian and European "
               "geometries, stainless-steel rails, silent bearing rollers and adjustable spring bars.")
NEW_LEAD_ZH = ("核心床是普拉提馆的立馆之本。2026 画册共三条核心床线 —— 铝合金、折叠、实木，"
               "合计 46 个型号，从紧凑家用款到全轨道商用款。澳版、欧版两种几何，"
               "配不锈钢轨道、静音轴承滑轮与可调挂簧板。")

# 旧体系串（落盘后必须全部归零）
OLD_PATTERNS = [
    r"N[ILKWX][A-Z]?[0-9]{3}",          # 旧内部编码 NIC/NLH/NIM/NI K/NIW/NIX
    r"Croatian [Bb]eech",
    r"(?:Imported|Domestic) rubberwood",
    r"FAS-grade white maple",
    r"Piano-[Ll]acquer",
    r"M-series",
    r"20 models",
    r"9 timber options",
    r"9 种木种",
    r"20 个型号",
]


def build_itemlist(rows):
    items = []
    for i, r in enumerate(sorted(rows, key=lambda x: (x["series"], x["page"], str(x["model"]))), 1):
        items.append('        {\n          "@type": "ListItem",\n'
                     f'          "position": {i},\n'
                     f'          "name": "{r["model"]}"\n        }}')
    body = ",\n".join(items)
    return ('      "@type": "ItemList",\n'
            '      "name": "Pilates Reformer — model range",\n'
            f'      "numberOfItems": {len(rows)},\n'
            '      "itemListElement": [\n'
            f'{body}\n'
            '      ]\n    }')


def collect(t, frag_text, rows):
    """返回 [(start, end, new_text, label), ...]，未命中的记 None"""
    edits = []
    misses = []

    def sub_once(pattern, new, label, flags=0, count=1):
        found = list(re.finditer(pattern, t, flags))
        if len(found) != count:
            misses.append(f"{label}: 命中 {len(found)} 次，期望 {count}")
            return
        for m in found:
            edits.append((m.start(), m.end(), new, label))

    # ① 规格表区块（Model range + Specifications 两段一起换）
    sub_once(
        r'  <section class="section">\n    <div class="container">\n      <div class="pl-block">\n'
        r'        <div class="im"><img src="\.\./assets/img/pilates-reformer-1\.webp".*?'
        r'      <p class="pl-spec-cap">.*?</p>\n    </div>\n  </section>\n',
        frag_text, "① 正文区块", flags=re.S)

    # ② meta description ×3（description / og / twitter）
    old_desc = re.search(r'<meta name="description" content="([^"]+)"', t).group(1)
    sub_once(re.escape(old_desc), NEW_DESC, "② meta description", count=3)

    # ③ JSON-LD material 数组
    sub_once(
        r'      "material": \[\n(?:        "[^"]+",?\n)+      \],',
        NEW_MATERIAL, "③ JSON-LD material")

    # ③b offerCount
    sub_once(r'"offerCount": 20', '"offerCount": 46', "③ offerCount")

    # ③c ItemList 整块
    sub_once(
        r'      "@type": "ItemList",\n      "name": "Pilates Reformer — model range",\n'
        r'      "numberOfItems": 20,\n      "itemListElement": \[\n.*?\n      \]\n    \}',
        build_itemlist(rows), "③ ItemList", flags=re.S)

    # ③d FAQ 里的 20 models（JSON-LD + 可见正文，英文各一处）
    sub_once(
        r'Specification sheets and photos covering all 20 models in this line',
        'Specification sheets and photos covering all 46 models across the three lines',
        "③d FAQ EN", count=2)
    sub_once(r'本线全部 20 个型号的规格书与实拍图',
             '本线全部 46 个型号的规格书与实拍图', "③d FAQ ZH")

    # ④ hero eyebrow / lead
    sub_once(
        r'<div class="pl-eyebrow"><span class="lang-en">20 models · 9 timber options</span>'
        r'<span class="lang-zh">20 个型号 · 9 种木种</span></div>',
        '<div class="pl-eyebrow"><span class="lang-en">46 models · 3 reformer lines</span>'
        '<span class="lang-zh">46 个型号 · 3 条核心床线</span></div>',
        "④ hero eyebrow")
    sub_once(
        r'<span class="lang-en">The reformer is the machine a studio is built around\..*?</span>'
        r'<span class="lang-zh">核心床是普拉提馆的立馆之本。.*?</span>',
        f'<span class="lang-en">{NEW_LEAD_EN}</span><span class="lang-zh">{NEW_LEAD_ZH}</span>',
        "④ hero lead", flags=re.S)

    return edits, misses


def check(t, label):
    problems = []
    for pat in OLD_PATTERNS:
        n = len(re.findall(pat, t))
        if n:
            problems.append(f"{label} 残留旧串 {pat!r} ×{n}")
    # 标签配平
    void = {"img", "br", "hr", "input", "meta", "link", "source", "area", "col"}
    c = collections.Counter()
    for m in re.finditer(r"<(/?)([a-zA-Z][\w-]*)", t):
        tag = m.group(2).lower()
        if tag in void:
            continue
        c[tag] += -1 if m.group(1) else 1
    bad = {k: v for k, v in c.items() if v != 0}
    if bad:
        problems.append(f"{label} 标签不配平: {bad}")
    # 双语配对
    en, zh = t.count('class="lang-en"'), t.count('class="lang-zh"')
    if en != zh:
        problems.append(f"{label} 双语不配对 en={en} zh={zh}")
    # 关键计数
    if t.count('class="cat-unit"') != 27:
        problems.append(f"{label} cat-unit 应为 27，实为 {t.count('class=\"cat-unit\"')}")
    if t.count('class="model-card"') != 46:
        problems.append(f"{label} model-card 应为 46，实为 {t.count('class=\"model-card\"')}")
    if '"numberOfItems": 46' not in t:
        problems.append(f"{label} ItemList 未更新为 46")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    t = SITE_PAGE.read_text("utf-8")
    frag_text = FRAG.read_text("utf-8")
    rows = json.loads(DATA.read_text("utf-8"))
    rows = [r for r in rows if r["series"].startswith(("A.", "B.", "C."))]

    before = check(t, "[改前]")
    print(f"改前体格: {len(t)} 字节 / {t.count(chr(10)) + 1} 行")
    print(f"改前问题（预期含旧串）: {len(before)} 条")
    for p in before:
        print(f"    · {p}")
    print()

    edits, misses = collect(t, frag_text, rows)
    if misses:
        print("✗ 定位失败，未写盘：")
        for m in misses:
            print(f"    · {m}")
        return 1

    print(f"改动点 {len(edits)} 处：")
    for s, e, _, label in sorted(edits, key=lambda x: x[0]):
        print(f"    · {label}  @{s}–{e}  ({e - s} → {len(_)} 字节)")
    print()

    # 断言：区间不重叠
    ordered = sorted(edits, key=lambda x: x[0])
    for i in range(1, len(ordered)):
        if ordered[i][0] < ordered[i - 1][1]:
            print(f"✗ 区间重叠: {ordered[i-1][3]} 与 {ordered[i][3]}")
            return 1

    out = t
    for s, e, new, _ in sorted(edits, key=lambda x: x[0], reverse=True):
        out = out[:s] + new + out[e:]

    after = check(out, "[改后]")
    print(f"改后体格: {len(out)} 字节 / {out.count(chr(10)) + 1} 行")
    print(f"改后问题: {len(after)} 条")
    for p in after:
        print(f"    · {p}")
    print()
    if after:
        print("✗ 改后断言未通过，不写盘")
        return 1

    # 内联差量对账：+行数 与 −行数 应配对
    import difflib
    d = list(difflib.unified_diff(t.split("\n"), out.split("\n"), lineterm="", n=0))
    plus = sum(1 for l in d if l.startswith("+") and not l.startswith("+++"))
    minus = sum(1 for l in d if l.startswith("-") and not l.startswith("---"))
    print(f"差量: +{plus} 行 / −{minus} 行")

    if not a.write:
        print("✓ dry-run 通过（未写盘）。加 --write 落盘。")
        return 0

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = BACKUP_DIR / f"pilates-reformer.html.bak_{stamp}"
    shutil.copy2(SITE_PAGE, bak)
    SITE_PAGE.write_text(out, "utf-8")
    print(f"✓ 已备份: {bak}")
    print(f"✓ 已落盘: {SITE_PAGE}")

    # 落盘后复读校验
    again = SITE_PAGE.read_text("utf-8")
    if again != out:
        print("✗ 落盘后复读不一致")
        return 1
    print(f"✓ 复读一致（{len(again)} 字节）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
