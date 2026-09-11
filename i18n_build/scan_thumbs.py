#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描 products.html 全部分类卡的缩略图，判定每张图的底色类型。

原因：.ct-thumbs 用 object-fit:cover 铺满，图片自带什么底色就显示什么底色。
白底/透明底会被 mix-blend-mode:multiply 融进卡片米色(--paper #f9f7f2)，
但**彩色底**融不掉 → 网格里出现绿块/粉块，与融入的格子不一致，看起来"有的有边框有的没有"。

判定口径（取 cover 裁切后可见区域的四角）：
  · alpha 透明           → TRANSPARENT（会露出容器色，OK）
  · 四角接近纯白/非常亮   → WHITE（multiply 后 = 容器色，OK）
  · 四角偏某一彩色        → COLORED（融不掉，需处理）
  · 四角互不相同且不亮    → PHOTO（实景照，需处理）
用法: python i18n_build/scan_thumbs.py
"""
import json, os, re, statistics, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPER = (249, 247, 242)


def corner_colors(path, n=4):
    """取 cover 裁切后可见区域的四个角（各 n×n 均值），带 alpha 判定。"""
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    side = min(w, h)                      # cover → 中心正方形
    box = ((w - side) // 2, (h - side) // 2, (w - side) // 2 + side, (h - side) // 2 + side)
    im = im.crop(box)
    side = im.size[0]
    corn, alpha_min = [], 255
    for (x0, y0) in [(0, 0), (side - n, 0), (0, side - n), (side - n, side - n)]:
        px = [im.getpixel((x0 + i, y0 + j)) for i in range(n) for j in range(n)]
        alpha_min = min(alpha_min, min(p[3] for p in px))
        corn.append(tuple(round(statistics.mean(p[c] for p in px)) for c in range(3)))
    return corn, alpha_min


def classify(corn, alpha_min):
    if alpha_min < 250:
        return "TRANSPARENT", "透明底，露出容器色"
    avg = tuple(round(statistics.mean(c[i] for c in corn)) for i in range(3))
    spread = max(max(c[i] for c in corn) - min(c[i] for c in corn) for i in range(3))
    lum = 0.299 * avg[0] + 0.587 * avg[1] + 0.114 * avg[2]
    # 彩色度：最大通道 - 最小通道
    chroma = max(avg) - min(avg)
    if lum > 236 and chroma < 14:
        return "WHITE", f"白底 avg={avg} 会融进卡片色"
    if lum > 214 and chroma < 12:
        return "NEARWHITE", f"近白底 avg={avg} 基本能融"
    if spread > 42 and chroma < 26:
        return "PHOTO", f"实景照 spread={spread}"
    return "COLORED", f"彩色底 avg={avg} 色度={chroma}"


def main():
    html = open(os.path.join(ROOT, "products.html"), encoding="utf-8").read()
    tiles = re.findall(r'<div class="cat-tile">(.*?)</div>\s*</div>', html, re.S)
    if not tiles:
        tiles = re.split(r'<div class="cat-tile">', html)[1:]

    rows, bad = [], []
    for t in tiles:
        name = re.search(r'<h3>.*?lang-en">([^<]+)<', t, re.S)
        name = name.group(1) if name else "?"
        thumb_block = re.search(r'<div class="ct-thumbs">(.*?)</div>', t, re.S)
        if not thumb_block:
            continue
        srcs = re.findall(r'<img src="([^"]+)"', thumb_block.group(1))
        for i, src in enumerate(srcs, 1):
            p = os.path.join(ROOT, src)
            if not os.path.exists(p):
                rows.append((name, i, src.split("/")[-1], "MISSING", ""))
                continue
            corn, amin = corner_colors(p)
            kind, note = classify(corn, amin)
            rows.append((name, i, src.split("/")[-1], kind, note))
            if kind in ("COLORED", "PHOTO"):
                bad.append((name, i, src.split("/")[-1], kind, note))

    print(f"分类卡缩略图共 {len(rows)} 张\n")
    cur = None
    for name, i, fn, kind, note in rows:
        if name != cur:
            cur = name
            print(f"\n■ {name}")
        mark = {"WHITE": "OK  ", "NEARWHITE": "OK~ ", "TRANSPARENT": "OK  ",
                "COLORED": "BAD ", "PHOTO": "BAD ", "MISSING": "MISS"}[kind]
        print(f"   {mark} {i}. {fn:44s} {kind:12s} {note}")

    print(f"\n{'='*70}")
    from collections import Counter
    print("分布:", dict(Counter(r[3] for r in rows)))
    print(f"\n需处理（彩色底/实景底）{len(bad)} 张：")
    for name, i, fn, kind, note in bad:
        print(f"   {name} #{i}  {fn}  ({kind})")

    json.dump([{"tile": n, "idx": i, "file": f, "kind": k, "note": nt} for n, i, f, k, nt in rows],
              open(os.path.join(ROOT, "outputs/缩略图底色扫描.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n明细已写入 outputs/缩略图底色扫描.json")


if __name__ == "__main__":
    main()
