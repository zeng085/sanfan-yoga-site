#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
老页改名后的第二遍收尾：清掉散落在 alt / JSON-LD / 相关产品格 / 首页 g-grid / i18n g 键里的旧名。

第一遍 align_ym_pages.py 只改了「页面自身」的 title / h1 / JSON-LD Product.name / ymN.t 键；
旧名还有 5 个落点需要一起清：
  1) <img alt="旧名">
  2) breadcrumb JSON-LD 里的 "name": "旧名"
  3) 老页「相关产品」格的 <h4><span class="lang-en">旧名</span><span class="lang-zh">旧中文名</span></h4>
  4) 首页 index.html 的 g-grid（<div class="n" data-i18n="gN.n">旧名</div>）
  5) main.js 的 'gN.n' 键（EN + ZH 两处）

用法：
    python3 i18n_build/align_ym_pages_p2.py --dry-run
    python3 i18n_build/align_ym_pages_p2.py
"""
import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

RENAME = {
    "Double-wide TPE Mat": "TPE Double Yoga Mat",
    "Foldable TPE Yoga Mat": "TPE Folding Yoga Mat",
    "PU / Rubber Premium Mat": "PU Rubber Yoga Mat",
    "Frosted PU Yoga Mat": "Matte PU Rubber Yoga Mat",
    "Camouflage TPE Yoga Mat": "TPE Camouflage Yoga Mat",
    "双人加宽 TPE 垫": "TPE 双人瑜伽垫",
    "折叠 TPE 瑜伽垫": "TPE 折叠瑜伽垫",
    "PU / 橡胶高端垫": "PU 橡胶瑜伽垫",
    "磨砂 PU 瑜伽垫": "磨砂 PU 橡胶瑜伽垫",
    "迷彩 TPE 瑜伽垫": "TPE 迷彩瑜伽垫",
}

# g1.s 要补 90cm（ym1 尺寸已补 90）
GS_FIX = {
    "widths 61 / 66 / 80 cm": "widths 61 / 66 / 80 / 90 cm",
    "宽度 61 / 66 / 80 cm": "宽度 61 / 66 / 80 / 90 cm",
}

TARGETS = []  # 动态收集


def collect():
    out = []
    for p in ROOT.rglob("*"):
        if p.suffix not in (".html", ".js", ".json", ".xml"):
            continue
        parts = set(p.parts)
        if "outputs" in parts or ".git" in parts or "i18n_build" in parts or "__pycache__" in parts:
            continue
        out.append(p)
    return sorted(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = collect()
    touched = {}
    for p in files:
        t0 = p.read_text(encoding="utf-8", errors="ignore")
        t = t0
        cnt = {}

        # 1) 裸名替换（覆盖 alt=""、JSON-LD name、>旧名<、i18n 值）
        #    这些旧名极具体，不与其它文案撞车，直接按名替换即可
        for old, new in RENAME.items():
            n = t.count(old)
            if not n:
                continue
            t = t.replace(old, new)
            cnt[old] = n

        # 2) g1.s 补 90cm
        for old, new in GS_FIX.items():
            n = t.count(old)
            if not n:
                continue
            t = t.replace(old, new)
            cnt[f"g1.s 尺寸补 90cm ({old[:22]}…)"] = n

        # 3) 保险：检查替换后是否把品牌后缀搞重复（如 "X — SANFAN" 变体）
        t = t.replace("TPE Double Yoga Mat — SANFAN — SANFAN", "TPE Double Yoga Mat — SANFAN")

        if t != t0:
            touched[str(p.relative_to(ROOT))] = cnt
            if not args.dry_run:
                p.write_text(t, encoding="utf-8")

    for f, cnt in touched.items():
        print(f"── {f}")
        for k, n in cnt.items():
            print(f"     {n}× {k}")
    print("=" * 74)
    print(f"共 {len(touched)} 个文件受影响；{'dry-run 未写盘' if args.dry_run else '已写盘'}")

    # 残留复查
    left = []
    for p in collect():
        t = p.read_text(encoding="utf-8", errors="ignore")
        for old in list(RENAME) + list(GS_FIX):
            if old in t:
                left.append((str(p.relative_to(ROOT)), old))
    print("残留:", left if left else "无 ✓")

    if not args.dry_run and left:
        sys.exit(1)


if __name__ == "__main__":
    main()
