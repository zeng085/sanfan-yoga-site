#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从画册「整页合成位图」中裁出单台产品图 —— 可行性验证。

背景（实测）：
  · 画册是纯位图 PDF：每页 1 张放置 raster（~2397x2433），drawings=0、text=0
  · 所以 pdfimages / PyMuPDF 的「内嵌图提取」只能拿到整页，拿不到单品
  · 但产品是**白底悬浮实拍**，因此可用「非白掩膜 + 连通域」定位并紧裁
  · 原生分辨率下紧裁 ≈ 1630x900 px（够网站用）

本脚本：下采样 → 非白掩膜 → 膨胀 → BFS 连通域 → 取面积最大的 N 个 → 回投原生坐标紧裁
输出：/tmp/pilates_crop_test/ 下的 overlay_*.png（人工核验）+ crop 图
"""
import fitz, io, os, sys, json
import numpy as np
from PIL import Image
from collections import deque

BASE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(BASE, 'data', 'catalog_pilates_2026_en.pdf')
OUT = '/tmp/pilates_crop_test'
os.makedirs(OUT, exist_ok=True)

SMALL_W = 700          # 下采样宽度（检测用）
DARK = 238             # 非白阈值：min(R,G,B) < DARK 视为前景
FILL = round(SMALL_W * 0.016)   # 膨胀核（占宽比），用于把弹簧/绳索连成一体


def load_page_img(doc, pi):
    pg = doc[pi]
    placed = [im for im in pg.get_images(full=True) if pg.get_image_rects(im[0])]
    if not placed:
        return None
    return Image.open(io.BytesIO(doc.extract_image(placed[0][0])['image'])).convert('RGB')


def largest_blobs(mask, n, min_area_frac=0.002):
    """纯 numpy+deque 的 BFS 连通域，返回面积最大的 n 个 bbox（小图坐标）。"""
    H, W = mask.shape
    lab = np.zeros((H, W), np.uint8)
    boxes = []
    min_area = int(H * W * min_area_frac)
    ys, xs = np.nonzero(mask)
    for sy, sx in zip(ys, xs):
        if lab[sy, sx]:
            continue
        q = deque([(sy, sx)])
        lab[sy, sx] = 1
        y0 = y1 = sy
        x0 = x1 = sx
        area = 0
        while q:
            y, x = q.popleft()
            area += 1
            if y < y0: y0 = y
            if y > y1: y1 = y
            if x < x0: x0 = x
            if x > x1: x1 = x
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not lab[ny, nx]:
                        lab[ny, nx] = 1
                        q.append((ny, nx))
        if area >= min_area:
            boxes.append((area, x0, y0, x1, y1))
    boxes.sort(reverse=True)
    return boxes[:n]


def dilate(mask, r):
    """用切片 max 实现方框膨胀。"""
    out = mask.copy()
    for k in range(1, r + 1):
        out[k:, :] |= mask[:-k, :]
        out[:-k, :] |= mask[k:, :]
        out[:, k:] |= mask[:, :-k]
        out[:, :-k] |= mask[:, k:]
    return out


def main():
    doc = fitz.open(PDF)
    models = json.load(open(os.path.join(BASE, 'data', 'catalog_pilates_models.json'),
                            encoding='utf-8'))
    per_page = {}
    for m in models:
        per_page.setdefault(m['page'], []).append(m['model'])

    pages = sorted(per_page)
    only = [int(a) for a in sys.argv[1:] if a.isdigit()] or pages
    report = []
    for p in only:
        im = load_page_img(doc, p - 1)
        if im is None:
            print(f'p{p}: ⚠️ 无放置 raster'); continue
        W, H = im.size
        scale = SMALL_W / W
        small = im.resize((SMALL_W, max(1, round(H * scale))), Image.BILINEAR)
        a = np.asarray(small).astype(np.int16)
        mask = (a.min(axis=2) < DARK)
        d = dilate(mask, FILL)
        n = len(per_page[p])
        blobs = largest_blobs(d, n)
        vis = small.copy()
        va = np.asarray(vis).copy()
        picks = []
        for i, (area, x0, y0, x1, y1) in enumerate(blobs):
            # 回投原生坐标（留 0.5% 出血）
            px0 = max(0, int(x0 / scale) - 8); py0 = max(0, int(y0 / scale) - 8)
            px1 = min(W, int(x1 / scale) + 8); py1 = min(H, int(y1 / scale) + 8)
            picks.append((area, px0, py0, px1, py1))
            va[y0:y1 + 1, x0] = [255, 0, 0]
            va[y0:y1 + 1, x1] = [255, 0, 0]
            va[y0, x0:x1 + 1] = [255, 0, 0]
            va[y1, x0:x1 + 1] = [255, 0, 0]
        Image.fromarray(va).save(f'{OUT}/overlay_p{p:02d}.png')
        for i, (area, px0, py0, px1, py1) in enumerate(picks):
            c = im.crop((px0, py0, px1, py1))
            c.save(f'{OUT}/p{p:02d}_{i}_{c.size[0]}x{c.size[1]}.png')
        line = (f'p{p:>2} 期望{n}台 检出{len(blobs)}   '
                + ' | '.join(f'{x1-x0}x{y1-y0}px' for _, x0, y0, x1, y1 in picks))
        print(line)
        report.append((p, n, len(blobs), picks))

    bad = [r for r in report if r[1] != r[2]]
    print(f'\n期望数≠检出数的页：{len(bad)} / {len(report)}')
    for p, n, k, _ in bad:
        print(f'  p{p}: 期望 {n} 检出 {k}')
    print(f'\n输出目录 {OUT}')


if __name__ == '__main__':
    main()
