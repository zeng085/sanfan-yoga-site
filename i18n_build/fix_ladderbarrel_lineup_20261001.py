#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""梯桶线型号归属 —— **终审修正**（2026-10-01 第二轮）

=====================================================================
先看两个坐标系，别再混
=====================================================================
    文件页码 = 印刷页码 + 1
    文件 p34.webp -> 纸上印「33」
    文件 p36.webp -> 纸上印「35」

=====================================================================
画册事实（逐页打开原件核对）
=====================================================================
   印刷 32（p33）  标题 Ladder Barre -3 / Ladder Barre 19-F      梯桶章
   印刷 33（p34）  标题 Ladder Barre 21-FO / Ladder Barre 20-V5  梯桶章内
                   但实物照片是**两台稳踏椅**，箱规 920*720*790 / 85kg
   印刷 34（p35）  标题 Ladder Barre 1-A / 2-A / 4-T            梯桶章
   印刷 35（p36）  标题 Chair 21-FO / Chair 20-V5                稳踏椅章首页
                   但实物照片是**两台梯桶**，箱规 1190*700*1170 / 85kg
   印刷 36（p37）  标题 Chair 4 / 10-B / 10-A                    稳踏椅章

即：**两个页面上的「照片 + 箱规」块互换了位置**，标题与所在分章都对。

=====================================================================
三条判据（缺一条都定不了案）
=====================================================================
1. 分章连续性
   梯桶章 32→33→34 连续；稳踏椅章 35 起。若按「型号名是误抄」处理，
   则梯桶章中间会夹进一台稳踏椅、稳踏椅章首页会夹进一台梯桶 —— 两处错位。
   按「照片+箱规放错页」处理，两章各自连续，只错 2 个图块。后者是更省的假设。

2. 箱规物理量级
   920*720*790 与梯桶线（1190*700*1170 / 1120*670*980）差 0.4m 高度，
   却与 Chair 10-A 的 920*720*790 **完全相同**；
   1190*700*1170 与 Ladder Barre -3 的 1190*700*1170 **完全相同**，
   而稳踏椅线其余是 750*700*650 / 1020*720*850 / 920*720*790，没有 1.17m 高的椅子。
   → 规格跟着实物走，实物跟着分章走。

3. ⭐ 型号后缀是**跨产品线复用**的（决定性）
   画册核心床章也用同样的后缀：
       印刷 08（p9）  Metal 20-V5    Material:（未印）  2380*750*2000mm
       印刷 09（p10） AL 21-FO      Material: Carbon steel 2550*720*500mm
   所以「21-FO」「20-V5」不是全局唯一编号，而是版型后缀。
   → **梯桶线有 21-FO / 20-V5 完全正常**，不需要假设"画册误抄了椅子的号"。

=====================================================================
结论
=====================================================================
    梯桶线   Ladder Barre 21-FO / 20-V5  = 印刷 35 页那两台**梯桶**
             Metal / 1190*700*1170mm / 85kg
    稳踏椅线 Chair 21-FO / 20-V5         = 印刷 33 页那两台**稳踏椅**
             Metal / 920*720*790mm / 85kg
→ 两条线各自都叫 21-FO / 20-V5。**梯桶线共 7 台。**

=====================================================================
本脚本做什么
=====================================================================
把上一轮误挂到「Z. 待确认」池的两台梯桶恢复命名、回梯桶族（E），
并给四条记录补上判定依据。规格 / 图片 / 页码 / 坐标**一个字不动**
（它们本来就是对的，错的是我把名字判给了另一族）。

被本脚本推翻的是 fix_ladderbarrel_title_swap_20261001.py（它把梯桶那两条摘出）。

用法：
    python3 fix_ladderbarrel_lineup_20261001.py --dry-run
    python3 fix_ladderbarrel_lineup_20261001.py --apply
"""
import argparse
import json
import os
import shutil
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "i18n_build", "data", "catalog_pilates_models_v2.json")

SERIES_LB = "E. Ladder Barrel 梯桶"
SERIES_CH = "F. Chair 稳踏椅"
PARK_SERIES = "Z. 待确认（画册标题贴错页）"

LB_NOTE = (
    "型号名见画册印刷页 33 的标题（Ladder Barre 21-FO / 20-V5）；"
    "实物照片与箱规（Metal / 1190*700*1170mm / 85kg）印在印刷页 35。"
    "画册把这两页的「照片+箱规」块互换了位置，标题与分章位置为准。"
    "旁证：核心床章亦用 Metal 20-V5 / AL 21-FO，后缀为跨线复用。"
)
CH_NOTE = (
    "型号名见画册印刷页 35 的标题（Chair 21-FO / 20-V5）；"
    "实物照片与箱规（Metal / 920*720*790mm / 85kg，与 Chair 10-A 同规格）印在印刷页 33。"
)

# 恢复命名：把 Z 池里那两条放回 E 族
RESTORE = [
    dict(cur_model="[待确认] Ladder Barrel 印刷页35-1",
         new_model="Ladder Barre 21-FO"),
    dict(cur_model="[待确认] Ladder Barrel 印刷页35-2",
         new_model="Ladder Barre 20-V5"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="默认行为，显式写出以便对照")
    args = ap.parse_args()

    data = json.load(open(DATA, encoding="utf-8"))
    print(f"读入 {len(data)} 条")
    print(f"改动前：E 梯桶 {sum(1 for m in data if m['series'] == SERIES_LB)} 台 / "
          f"F 稳踏椅 {sum(1 for m in data if m['series'] == SERIES_CH)} 台 / "
          f"Z 待确认 {sum(1 for m in data if m['series'] == PARK_SERIES)} 台")

    # --- 前置校验：两条待恢复记录必须存在，且页码/箱规符合预期 ---
    for r in RESTORE:
        hit = [m for m in data if m["model"] == r["cur_model"]]
        if len(hit) != 1:
            raise SystemExit(f"❌ 前置校验失败：{r['cur_model']} 命中 {len(hit)} 条，应为 1")
        m = hit[0]
        assert m["series"] == PARK_SERIES, f"{r['cur_model']} 不在 Z 池"
        assert m["page"] == 36 and m["catalog_page"] == 35, f"{r['cur_model']} 页码异常"
        assert m["packing_a"] == "1190*700*1170", f"{r['cur_model']} 箱规异常 {m['packing_a']}"
        assert m["material"] == "Metal" and m["weight"] == 85.0, f"{r['cur_model']} 材质/毛重异常"
        print(f"  ✓ 待恢复 {r['cur_model']} → {r['new_model']}  "
              f"p{m['page']}(印{m['catalog_page']}) {m['packing_a']} {m['material']} {m['weight']}kg")

    # --- 前置校验：新名字不能与现有记录撞 ---
    for r in RESTORE:
        dup = [m for m in data if m["model"] == r["new_model"]]
        if dup:
            raise SystemExit(f"❌ 命名冲突：已存在 {r['new_model']}（族={dup[0]['series']}）")
        print(f"  ✓ 新名 {r['new_model']} 无冲突")

    # --- 前置校验：稳踏椅那两条必须仍是 920*720*790 ---
    for name in ("Chair 21-FO", "Chair 20-V5"):
        hit = [m for m in data if m["model"] == name and m["series"] == SERIES_CH]
        if len(hit) != 1:
            raise SystemExit(f"❌ {name} 在 F 族命中 {len(hit)} 条，应为 1")
        if hit[0]["packing_a"] != "920*720*790" or hit[0]["page"] != 34:
            raise SystemExit(f"❌ {name} 规格/页码异常：{hit[0]['packing_a']} p{hit[0]['page']}")
    print("  ✓ Chair 21-FO / 20-V5 仍为 p34 · 920*720*790")

    # --- 执行 ---
    changed = []
    for r in RESTORE:
        m = next(m for m in data if m["model"] == r["cur_model"])
        old = dict(m)
        m["model"] = r["new_model"]
        m["series"] = SERIES_LB
        m["notes"] = [LB_NOTE]
        m["suspect"] = []
        m.pop("ocr_missed", None)
        changed.append((old, dict(m)))

    for m in data:
        if m["series"] == SERIES_CH and m["model"] in ("Chair 21-FO", "Chair 20-V5"):
            m["notes"] = [CH_NOTE]

    print("\n=== 变更明细 ===")
    for old, new in changed:
        print(f"  {old['model']:<34} [{old['series']}]")
        print(f"   → {new['model']:<32} [{new['series']}]")

    # --- 后置校验 ---
    e = sum(1 for m in data if m["series"] == SERIES_LB)
    f = sum(1 for m in data if m["series"] == SERIES_CH)
    z = sum(1 for m in data if m["series"] == PARK_SERIES)
    print(f"\n改动后：E 梯桶 {e} 台 / F 稳踏椅 {f} 台 / Z 待确认 {z} 台")
    assert e == 7 and f == 9 and z == 0, f"❌ 台数不符：E={e} F={f} Z={z}"
    seen = set()
    for m in data:
        k = (m["model"], m["series"])
        assert k not in seen, f"❌ 重复记录 {k}"
        seen.add(k)
    print("  ✓ 无重复 (model, series)，E=7 / F=9 / Z=0")

    if not args.apply:
        print("\n[dry-run] 未落盘。加 --apply 执行。")
        return

    bak = DATA + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(DATA, bak)
    json.dump(data, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n💾 已落盘（备份 {os.path.basename(bak)}）")


if __name__ == "__main__":
    main()
