#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为「缩略图底色不一致」的那几张，在同款图集里找白底替代素材。

背景：products.html 的 .ct-thumbs 是 3×2 密排小图，对底色一致性极敏感。
白底图会被 multiply 融进卡片米色，彩色底/实景底则显示为色块 → 看起来"有的有边框有的没有"。
本站每个产品的完整图集（<slug>-1..N.webp）都在本地，直接在同款里挑白底的那张即可。

用法: python i18n_build/scan_alternatives.py            # 只报告
      python i18n_build/scan_alternatives.py --apply    # 报告并写入替换计划
"""
import glob
import json
import os
import re
import statistics
import sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "assets", "img")
SCAN = os.path.join(ROOT, "outputs", "缩略图底色扫描.json")
OUT = os.path.join(ROOT, "outputs", "plan", "缩略图换图计划.json")


def corners(path, n=4):
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    side = min(w, h)
    im = im.crop(((w - side) // 2, (h - side) // 2,
                  (w - side) // 2 + side, (h - side) // 2 + side))
    side = im.size[0]
    res, amin = [], 255
    for (x0, y0) in [(0, 0), (side - n, 0), (0, side - n), (side - n, side - n)]:
        px = [im.getpixel((x0 + i, y0 + j)) for i in range(n) for j in range(n)]
        amin = min(amin, min(p[3] for p in px))
        res.append(tuple(round(statistics.mean(p[c] for p in px)) for c in range(3)))
    return res, amin


def white_score(path):
    """返回 (是否白底/透明, 分数)。分数越大 = 底色越干净（越接近容器米色）。"""
    corn, amin = corners(path)
    if amin < 250:
        return True, 500.0
    avg = [statistics.mean(c[i] for c in corn) for i in range(3)]
    lum = 0.299 * avg[0] + 0.587 * avg[1] + 0.114 * avg[2]
    chroma = max(avg) - min(avg)
    # 白底：亮度高、色度低
    if lum >= 238 and chroma <= 12:
        return True, 400 + (255 - min(avg))
    return False, -1


def main():
    rows = json.load(open(SCAN, encoding="utf-8"))
    bad = [r for r in rows if r["kind"] in ("COLORED", "PHOTO")]
    if not bad:
        print("没有需要处理的缩略图")
        return

    plan = []
    print(f"待处理 {len(bad)} 张，逐张在同款图集里找白底替代\n")
    for r in bad:
        cur = r["file"]
        slug = re.sub(r"-\d+[a-z]?\.webp$", "", cur)
        # 同款图集：slug-<k>.webp （含 -1w 之类已废弃的不取）
        cands = sorted(
            [os.path.basename(p) for p in glob.glob(os.path.join(IMG, slug + "-*.webp"))
             if not re.search(r"-\d+w\.webp$", p)],
            key=lambda f: int(re.search(r"-(\d+)\.webp$", f).group(1))
            if re.search(r"-(\d+)\.webp$", f) else 999)
        found = []
        for f in cands:
            if f == cur:
                continue
            ok, sc = white_score(os.path.join(IMG, f))
            if ok:
                found.append((f, sc))
        found.sort(key=lambda x: -x[1])
        pick = found[0][0] if found else None
        print(f"■ {r['tile']} #{r['idx']}  {cur}  ({r['kind']})")
        print(f"   同款图集 {len(cands)} 张：{', '.join(cands[:12])}")
        if pick:
            print(f"   → 选 {pick}（白底候选 {len(found)} 张）")
            plan.append({"tile": r["tile"], "idx": r["idx"], "cur": cur,
                         "new": pick, "kind": r["kind"]})
        else:
            print("   → ⚠️ 同款无白底候选，需从英文站另抓")
        print()

    print(f"可自动替换 {len(plan)}/{len(bad)} 张")
    if "--apply" in sys.argv:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        json.dump(plan, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("计划已写入", OUT)


if __name__ == "__main__":
    main()
