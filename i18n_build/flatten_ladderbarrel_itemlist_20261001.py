#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""把 EN 梯桶页的 JSON-LD ItemList 由「富」拉回全站惯例的「平」结构。

背景
----
第二轮换角度验证发现：全站 201 个 ItemList 里 **200 个是「平」的**
（ListItem 只有 position + name），唯独 `pilates/pilates-ladder-barrel.html`
是「富」的（每台型号包一个完整 Product：sku / material / weight / image /
url / additionalProperty / brand / offers）。200:1，梯桶页是孤例。

用户裁定：**统一为平，跟全站惯例**。（理由：改动面最小、与 200 页一致、
且型号的材质/毛重/包装在 HTML 表格里照样能被爬虫读到；富版里的 offers
没有 price，Google 会对每台型号报一个缺 price 的提醒。）

顺带修正两处：
- ItemList 的 `name` 由「Pilates Ladder Barrel — 7 models」改成全站惯例的
  「… — model range」（其余 6 个族页都是这个写法）
- 条目顺序改为画册顺序（与页面上新排好的卡片/表格顺序一致）

安全：默认 dry-run；`--write` 才落盘；落盘前备份；落盘后重新解析 LD 校验。

用法：
    python3 i18n_build/flatten_ladderbarrel_itemlist_20261001.py
    python3 i18n_build/flatten_ladderbarrel_itemlist_20261001.py --write
"""
import argparse
import datetime
import json
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "pilates/pilates-ladder-barrel.html"
DATA = ROOT / "i18n_build/data/catalog_pilates_models_v2.json"
# ⚠️ 不要用 ~/.workbuddy/backups/ —— 该路径被文件策略拦截（mkdir 被拒）。
#    改放工作区内已被 .gitignore 覆盖的目录。
BACKUP_DIR = ROOT / "outputs/pilates_rebuild_20261001/_backup"

DISPLAY_EN = "Pilates Ladder Barrel"
LD_RE = re.compile(r'<script type="application/ld\+json">\n(.*?)\n[ \t]*</script>', re.S)
# 富 ItemList 整节点（到该 @graph 节点的闭合括号为止）
ITEMLIST_RE = re.compile(
    r'      "@type": "ItemList",\n      "name": "[^"]+",\n'
    r'      "numberOfItems": \d+,\n      "itemListElement": \[\n.*?\n      \]\n    \}',
    re.S)


def flat_itemlist(rows, display_en):
    """与其余 6 个族页逐字节同构的「平」ItemList。"""
    items = []
    for i, r in enumerate(rows, 1):
        items.append('        {\n          "@type": "ListItem",\n'
                     f'          "position": {i},\n'
                     f'          "name": "{r["model"]}"\n        }}')
    return ('      "@type": "ItemList",\n'
            f'      "name": "{display_en} — model range",\n'
            f'      "numberOfItems": {len(rows)},\n'
            '      "itemListElement": [\n'
            + ",\n".join(items) + '\n      ]\n    }')


def shape(t):
    """返回所有 ItemList 的形状签名，用于前后比对。"""
    out = []
    for b in LD_RE.findall(t):
        try:
            d = json.loads(b)
        except Exception as e:
            return [f"PARSE-ERR: {e}"]
        for n in d.get("@graph", [d]):
            if n.get("@type") == "ItemList":
                els = n.get("itemListElement", [])
                out.append((n.get("name"), len(els),
                            sum(1 for e in els if isinstance(e.get("item"), dict)),
                            sorted(els[0].keys()) if els else []))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    src = json.loads(DATA.read_text("utf-8"))
    rows = sorted([r for r in src if r["series"].startswith("E.")],
                  key=lambda r: (r["page"], r["seq_in_page"]))
    t0 = PAGE.read_text("utf-8")

    before = shape(t0)
    print(f"改前 ItemList 形状: {before}")

    m = ITEMLIST_RE.search(t0)
    if not m:
        print("✗ ItemList pattern 未命中")
        return 1
    n_prod = t0[m.start():m.end()].count('"@type": "Product"')
    print(f"  命中富 ItemList，{m.end() - m.start()} 字节（含 {n_prod} 个 Product 节点）")

    new = flat_itemlist(rows, DISPLAY_EN)
    t1 = t0[:m.start()] + new + t0[m.end():]

    after = shape(t1)
    print(f"改后 ItemList 形状: {after}")

    bad = []
    if len(after) != 1:
        bad.append(f"改后 ItemList 数量 {len(after)} ≠ 1")
    else:
        nm, n, rich, keys = after[0]
        if n != len(rows):
            bad.append(f"改后项数 {n} ≠ {len(rows)}")
        if rich != 0:
            bad.append(f"改后仍有 {rich} 个富项")
        if nm != f"{DISPLAY_EN} — model range":
            bad.append(f"改后 name 为 {nm!r}")
        if keys != ["@type", "name", "position"]:
            bad.append(f"改后 ListItem 键为 {keys}")
    if "Product" in t1[t1.find('"@type": "ItemList"'):
                      t1.find('"@type": "ItemList"') + 4000]:
        bad.append("ItemList 区间内仍有 Product")
    # @graph 其余节点不得变动（逐块列表比对，别跨块用同一个变量）
    graphs = []
    for t in (t0, t1):
        graphs.append([[n.get("@type") for n in json.loads(b).get("@graph", [])]
                       for b in LD_RE.findall(t)])
    if graphs[0] != graphs[1]:
        bad.append(f"@graph 节点变化: {graphs[0]} → {graphs[1]}")
    if len(re.findall(r"</?(?:section|table|article|dl|figure)\b", t1)) != \
       len(re.findall(r"</?(?:section|table|article|dl|figure)\b", t0)):
        bad.append("HTML 结构计数变化")

    d = len(t1.encode()) - len(t0.encode())
    print(f"  字节 {d:+d}")

    if bad:
        print("✗ 自检失败：")
        for b in bad:
            print("   -", b)
        return 1

    if a.write:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(PAGE, BACKUP_DIR / f"{PAGE.name}.{stamp}.flatld.bak")
        PAGE.write_text(t1, "utf-8")
        rt = PAGE.read_text("utf-8")
        if rt != t1 or shape(rt) != after:
            print("✗ 落盘后复读校验失败")
            return 1
        print("✓ 已写盘 + 复读校验通过")
    else:
        print("✓ 自检通过（dry-run 未写盘）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
