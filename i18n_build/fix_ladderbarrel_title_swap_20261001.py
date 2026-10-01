#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""⚠️⚠️ 【本脚本结论已被推翻，请勿再执行】

  它把「Ladder Barre 21-FO / 20-V5」判给了稳踏椅、把印刷页 35 的两台梯桶摘进待确认池。
  2026-10-01 第二轮复核（逐页打开原件 + 画册分章结构 + 核心床章亦用 Metal 20-V5 / AL 21-FO
  证明后缀跨线复用）确认：**两个族各自都有 21-FO / 20-V5**，梯桶线共 7 台。
  正确结论与修正脚本见：fix_ladderbarrel_lineup_20261001.py
  本文件仅作留档，重跑会把数据改回错误状态。

---------------------------------------------------------------------
（以下是本文件原始说明，保留备查）

修正 21-FO / 20-V5 的族归属：它们是**稳踏椅**（Chair），不是梯桶。

## 坐标约定（先统一，否则会错一页）
    文件页码 = 印刷页码 + 1
    文件 p34.webp  -> 纸上印「33」，图上是两台稳踏椅
    文件 p36.webp  -> 纸上印「35」，图上是两台梯桶

## 事实（用户确认 + 画册原件实证）
- `p34.webp` 上两台是**稳踏椅**（左：米色踏板＋双立柱把手；右：深灰方凳＋高把手），
  箱规 920*720*790 / 85kg，图上标题印 `Ladder Barre 21-FO` / `Ladder Barre 20-V5`。
- `p36.webp` 上两台是**梯桶**（米色 / 深灰，桶身＋竖梯），
  箱规 1190*700*1170 / 85kg，图上标题印 `Chair 21-FO` / `Chair 20-V5`。

**21-FO / 20-V5 这两个型号属于稳踏椅（p34 那两台）。**
画册在梯桶页（p36）把稳踏椅的型号抄了过去，才造成「梯桶被标成 Chair 21-FO」。

## 因此
1. 数据里挂在梯桶族的 `Ladder Barre 21-FO` / `Ladder Barre 20-V5` 是**误命名**：
   它们的内容（p34.webp / 920*720*790 / 85kg / Metal）本来就是稳踏椅的，只是名字错了
   → 正名为 `Chair 21-FO` / `Chair 20-V5`，族改为 Chair，**内容一个字不动**。
2. 数据里挂在 Chair 族的 `Chair 21-FO` / `Chair 20-V5` 指向 p36.webp（那是梯桶实物），
   型号名已被第 1 步占用，且画册没给这两台梯桶真名
   → 移入待确认池，**型号待工厂给**，暂不参与任何族页筛选。
3. 结果：**梯桶族 = 5 台**（-3 / 19-F / 1-A / 2-A / 4-T）。

## 不做什么
- 不删任何记录（p36 那两条数据保留，规格 1190*700*1170 / 85kg 是画册实印值，将来补个名字即可）。
- 不动站点页面（`pilates/pilates-ladder-barrel.html`），等确认后再单独出方案。

用法：
    python3 fix_ladderbarrel_title_swap_20261001.py --dry-run
    python3 fix_ladderbarrel_title_swap_20261001.py --apply
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

# 第 1 步：正名。内容（image / packing / page / y / x）保持不变——它们本就属于这两台椅子。
RENAME = [
    dict(cur_model="Ladder Barre 21-FO", cur_series=SERIES_LB,
         cur_image="assets/img/catalog/p34.webp", cur_packing="920*720*790",
         new_model="Chair 21-FO", new_series=SERIES_CH),
    dict(cur_model="Ladder Barre 20-V5", cur_series=SERIES_LB,
         cur_image="assets/img/catalog/p34.webp", cur_packing="920*720*790",
         new_model="Chair 20-V5", new_series=SERIES_CH),
]

# 第 2 步：这两条当前指向 p36.webp（梯桶实物），型号名有误 → 摘出族页。
PARK = [
    ("Chair 21-FO", "assets/img/catalog/p36.webp", "[待确认] Ladder Barrel 印刷页35-1"),
    ("Chair 20-V5", "assets/img/catalog/p36.webp", "[待确认] Ladder Barrel 印刷页35-2"),
]
PARK_NOTE = ("该记录指向印刷页 35（文件 p36.webp）的梯桶实物；"
             "画册在该页误印了稳踏椅的型号 Chair 21-FO / 20-V5，真型号待工厂确认")


def find(recs, model, series):
    hits = [r for r in recs if r["model"] == model and r["series"] == series]
    if len(hits) != 1:
        raise SystemExit(f"!! 期望唯一命中 {model!r} / {series!r}，实际 {len(hits)} 条")
    return hits[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if not (a.apply or a.dry_run):
        ap.error("必须指定 --dry-run 或 --apply")

    recs = json.load(open(DATA, encoding="utf-8"))
    print(f"读入 {len(recs)} 条记录：{os.path.relpath(DATA, ROOT)}\n")

    # ---------- 前置断言：现状必须与预期一致 ----------
    print("=== 前置核对 ===")
    rename_pairs = []
    for fx in RENAME:
        r = find(recs, fx["cur_model"], fx["cur_series"])
        assert r["image"] == fx["cur_image"], \
            f"{fx['cur_model']}: image 期望 {fx['cur_image']}，实际 {r['image']}"
        assert r["packing_a"] == fx["cur_packing"], \
            f"{fx['cur_model']}: packing_a 期望 {fx['cur_packing']}，实际 {r['packing_a']}"
        r["_role"] = "RENAME"
        rename_pairs.append((r, fx))
        print(f"  正名 {fx['cur_model']:<22} -> {fx['new_model']:<22} "
              f"族 {fx['cur_series'][:1]}->{fx['new_series'][:1]}  "
              f"(内容保持 {r['image'].split('/')[-1]} / {r['packing_a']})")

    parked = []
    for model, img, newname in PARK:
        hits = [r for r in recs if r["model"] == model and r["image"] == img]
        if len(hits) != 1:
            raise SystemExit(f"!! 期望唯一命中 {model!r} @ {img}，实际 {len(hits)} 条")
        hits[0]["_role"] = "PARK"
        parked.append((hits[0], newname))
        print(f"  摘出 {model:<22} -> {newname:<34} "
              f"(保持 {img.split('/')[-1]} / {hits[0]['packing_a']})")

    # 重名检查
    staying = [r["model"] for r in recs if "_role" not in r]
    newnames = [fx["new_model"] for _, fx in rename_pairs] + [n for _, n in parked]
    dup = set(newnames) & set(staying)
    if dup:
        raise SystemExit(f"!! 新名字与未改动记录冲突：{dup}")
    if len(set(newnames)) != len(newnames):
        raise SystemExit("!! 新名字有重复")

    if a.dry_run:
        print("\n--dry-run：未落盘。")
        return

    # ---------- 备份 ----------
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = DATA + f".bak_{stamp}"
    shutil.copy2(DATA, bak)
    print(f"\n已备份 -> {os.path.relpath(bak, ROOT)}")

    # ---------- 落盘 ----------
    for r, fx in rename_pairs:
        r["model"] = fx["new_model"]
        r["series"] = fx["new_series"]
        r["suspect"] = []
        r.pop("_role", None)
    for r, newname in parked:
        r["model"] = newname
        r["series"] = PARK_SERIES
        r["suspect"] = [PARK_NOTE]
        r["notes"] = list(r.get("notes") or []) + [PARK_NOTE]
        r.pop("_role", None)

    out = json.dumps(recs, ensure_ascii=False, indent=1)
    assert '"model": "Chair 21-FO"' in out, "落盘自检：正名未写入"
    assert '"series": "Z. 待确认（画册标题贴错页）"' in out, "落盘自检：待确认池未写入"
    assert '"model": "Ladder Barre 21-FO"' not in out, "落盘自检：旧误命名仍存在"
    with open(DATA, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"已写回 {os.path.relpath(DATA, ROOT)}")

    # ---------- 复核 ----------
    chk = json.load(open(DATA, encoding="utf-8"))
    print("\n=== 落盘后复核 ===")
    for fam in (SERIES_LB, SERIES_CH, PARK_SERIES):
        rows = [m for m in chk if m["series"] == fam]
        print(f"\n{fam}（{len(rows)} 台）")
        for m in rows:
            star = "*" if any(k in m["model"] for k in ("21-FO", "20-V5")) else " "
            print(f" {star} {m['model']:<34} {str(m['material']):<8} "
                  f"{str(m['packing_a']):<16} {str(m['weight']):<7} "
                  f"img={m['image'].split('/')[-1]}")


if __name__ == "__main__":
    main()
