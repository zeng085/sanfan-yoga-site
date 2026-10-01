#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""画册整页图 → 单品图 裁剪可行性试探（2026-10-01）

思路：投影法（不依赖 scipy/cv2）
  1. 估背景色（灰度直方图众数）→ 前景 = |px - bg| > 阈值
  2. 行投影找「器械带」：连续前景行段，高度 > 最小器械高
  3. 每个器械带内做列投影 → 找横向分离的多台
  4. 过滤：面积/宽高比过小的是文字块与页码

输出：i18n_build/reports/crop_probe_20261001/{page}_{n}.png + 一张拼版
"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw

SRC = "/Users/mac-zlg/Downloads/result"
OUT = "/Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16/i18n_build/reports/crop_probe_20261001"

MIN_H = 150          # 器械带最小高度（px，原图 2433 高）
MIN_W = 150          # 器械最小宽度
MIN_FILL = 0.02      # 带内前景占比下限（低于此判为文字行）
GAP_ROWS = 12        # 行段间允许的空隙
GAP_COLS = 18        # 列段间允许的空隙


def segments(profile, thresh, gap):
    """把 1D 投影切成连续段 [(start, end), ...]"""
    idx = np.where(profile > thresh)[0]
    if len(idx) == 0:
        return []
    segs = []
    s = prev = idx[0]
    for i in idx[1:]:
        if i - prev > gap:
            segs.append((s, prev))
            s = i
        prev = i
    segs.append((s, prev))
    return segs


def crop_page(path, verbose=True):
    im = Image.open(path).convert("L")
    a = np.asarray(im).astype(np.int16)
    H, W = a.shape

    hist = np.bincount(a.ravel(), minlength=256)
    bg = int(hist.argmax())
    fg = np.abs(a - bg) > 30

    # 行投影
    rowp = fg.sum(axis=1)
    rsegs = segments(rowp, max(3, W * 0.005), GAP_ROWS)

    boxes = []
    for (r0, r1) in rsegs:
        h = r1 - r0 + 1
        band = fg[r0:r1 + 1]
        fill = band.mean()
        if h < MIN_H or fill < MIN_FILL:
            continue                      # 太矮 / 太空 → 文字行或噪声
        colp = band.sum(axis=0)
        for (c0, c1) in segments(colp, max(3, h * 0.02), GAP_COLS):
            w = c1 - c0 + 1
            if w < MIN_W:
                continue
            sub = fg[r0:r1 + 1, c0:c1 + 1]
            if sub.mean() < MIN_FILL:
                continue
            # 真正的前景包围盒（去掉边缘空白）
            ys, xs = np.where(sub)
            if len(ys) < 400:
                continue
            y0 = r0 + ys.min(); y1 = r0 + ys.max()
            x0 = c0 + xs.min(); x1 = c0 + xs.max()
            boxes.append((x0, y0, x1, y1))

    boxes.sort(key=lambda b: (b[1] // 200, b[0]))
    if verbose:
        print(f"  {os.path.basename(path)}: bg={bg} 行段={len(rsegs)} → 候选 {len(boxes)} 台")
    return im, boxes, bg


def main():
    pages = sys.argv[1:] or ["10_2", "17_2", "4_2"]
    os.makedirs(OUT, exist_ok=True)

    tiles = []
    for tag in pages:
        p = os.path.join(SRC, f"2026英文版电子图册_page_{tag}.png")
        if not os.path.exists(p):
            print(f"缺文件 {p}")
            continue
        im, boxes, bg = crop_page(p)
        rgb = im.convert("RGB")
        for i, (x0, y0, x1, y1) in enumerate(boxes, 1):
            pad = 14
            c = rgb.crop((max(0, x0 - pad), max(0, y0 - pad),
                          min(rgb.width, x1 + pad), min(rgb.height, y1 + pad)))
            c.save(os.path.join(OUT, f"p{tag}_{i}.png"))
            print(f"    -> p{tag}_{i}.png  {c.size[0]}x{c.size[1]}   bbox=({x0},{y0},{x1},{y1})")
            tiles.append((f"p{tag}_{i}", c))

    if not tiles:
        return
    # 拼版（统一高 360）
    TH = 360
    scaled = []
    for name, t in tiles:
        w = int(t.width * TH / t.height)
        scaled.append((name, t.resize((w, TH), Image.LANCZOS)))
    cols = min(6, len(scaled))
    rows = (len(scaled) + cols - 1) // cols
    cellw = max(s[1].width for s in scaled) + 10
    sheet = Image.new("RGB", (cols * cellw + 10, rows * (TH + 26) + 10), (240, 240, 243))
    d = ImageDraw.Draw(sheet)
    for i, (name, t) in enumerate(scaled):
        r, c = divmod(i, cols)
        x = 10 + c * cellw
        y = 10 + r * (TH + 26)
        sheet.paste(t, (x, y + 22))
        d.text((x + 2, y + 4), name, fill=(20, 20, 20))
    out = os.path.join(OUT, "_sheet.png")
    sheet.save(out)
    print(f"拼版 {out}  {sheet.size[0]}x{sheet.size[1]}")


if __name__ == "__main__":
    main()
