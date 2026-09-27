#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从画册整页合成位图中裁出单台产品图 v2 —— 引入 OCR 文字掩膜。

v1 失败原因（已实测）：产品与规格文字在 x 上相邻甚至重叠，
       单纯「非白掩膜 + 膨胀 + 最大连通域」会把文字和产品粘成一块（bbox 近整页）。

v2 思路：先用 ocrmac 拿到每行文字的 bbox → 从掩膜里挖掉（带 padding）
        → 再膨胀 + 连通域。这样剩下的最大块就是产品本体。

输出：/tmp/pilates_crop_test2/  overlay_*.png（人工核验）+ crop_*.png
"""
import fitz, io, os, sys, json, tempfile
import numpy as np
from PIL import Image
from collections import deque
from ocrmac import ocrmac

BASE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(BASE, 'data', 'catalog_pilates_2026_en.pdf')
OUT = '/tmp/pilates_crop_test2'
os.makedirs(OUT, exist_ok=True)

SMALL_W = 800
DARK = 236
PAD_FRAC = 0.012      # 文字框外扩（占页宽比）——把字周空白一并挖掉
FILL_FRAC = 0.010     # 膨胀核


def load_page_img(doc, pi):
    pg = doc[pi]
    placed = [im for im in pg.get_images(full=True) if pg.get_image_rects(im[0])]
    if not placed:
        return None
    return Image.open(io.BytesIO(doc.extract_image(placed[0][0])['image'])).convert('RGB')


def ocr_boxes(im):
    """返回像素坐标文字框 [(x0,y0,x1,y1)]（左上原点）。"""
    W, H = im.size
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        tmp = f.name
    im.save(tmp)
    try:
        res = ocrmac.OCR(tmp, language_preference=['en-US']).recognize()
    finally:
        os.unlink(tmp)
    out = []
    for item in res:
        txt, conf, (x, y, w, h) = item
        # Vision 用左下原点归一化坐标
        x0 = x * W
        x1 = (x + w) * W
        y1 = (1 - y) * H
        y0 = (1 - (y + h)) * H
        out.append((txt, x0, y0, x1, y1))
    return out


def dilate(mask, r):
    out = mask.copy()
    for k in range(1, r + 1):
        out[k:, :] |= mask[:-k, :]
        out[:-k, :] |= mask[k:, :]
        out[:, k:] |= mask[:, :-k]
        out[:, :-k] |= mask[:, k:]
    return out


def largest_blobs(mask, n, min_area_frac=0.004):
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
    return boxes[:n], lab


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
            print(f'p{p}: 无放置 raster'); continue
        W, H = im.size
        scale = SMALL_W / W
        small = im.resize((SMALL_W, max(1, round(H * scale))), Image.BILINEAR)
        a = np.asarray(small).astype(np.int16)
        mask = (a.min(axis=2) < DARK)

        boxes_txt = ocr_boxes(im)
        pad = PAD_FRAC * W
        keep_txt = []
        for txt, x0, y0, x1, y1 in boxes_txt:
            sx0 = max(0, int((x0 - pad) * scale)); sy0 = max(0, int((y0 - pad) * scale))
            sx1 = min(SMALL_W, int((x1 + pad) * scale)); sy1 = min(small.size[1], int((y1 + pad) * scale))
            mask[sy0:sy1, sx0:sx1] = False
            keep_txt.append((txt, x0, y0, x1, y1))

        d = dilate(mask, max(2, round(SMALL_W * FILL_FRAC)))
        n = len(per_page[p])
        blobs, lab = largest_blobs(d, n)

        va = np.asarray(small).copy()
        for txt, x0, y0, x1, y1 in keep_txt:      # 文字框标蓝
            sx0, sy0 = int(x0 * scale), int(y0 * scale)
            sx1, sy1 = int(x1 * scale), int(y1 * scale)
            va[sy0:sy1, sx0:sx0 + 1] = [0, 120, 255]
            va[sy0:sy1, sx1:sx1 + 1] = [0, 120, 255]
        picks = []
        for i, (area, x0, y0, x1, y1) in enumerate(blobs):
            px0 = max(0, int(x0 / scale) - 6); py0 = max(0, int(y0 / scale) - 6)
            px1 = min(W, int(x1 / scale) + 6); py1 = min(H, int(y1 / scale) + 6)
            picks.append((area, px0, py0, px1, py1))
            va[y0:y1 + 1, x0] = [255, 0, 0]
            va[y0:y1 + 1, x1] = [255, 0, 0]
            va[y0, x0:x1 + 1] = [255, 0, 0]
            va[y1, x0:x1 + 1] = [255, 0, 0]
        Image.fromarray(va).save(f'{OUT}/overlay_p{p:02d}.png')
        for i, (area, px0, py0, px1, py1) in enumerate(picks):
            im.crop((px0, py0, px1, py1)).save(
                f'{OUT}/crop_p{p:02d}_{i}_{px1-px0}x{py1-py0}.png')

        dims = ' | '.join(f'{x1-x0}x{y1-y0}' for _, x0, y0, x1, y1 in picks)
        # 与规格文字框重叠检查
        ovl = 0
        for _, px0, py0, px1, py1 in picks:
            for txt, tx0, ty0, tx1, ty1 in keep_txt:
                if tx0 < px1 and tx1 > px0 and ty0 < py1 and ty1 > py0:
                    ovl += 1
        print(f'p{p:>2} 期望{n} 检出{len(blobs)}  文字行{len(keep_txt):>2}  重叠{ovl}  {dims}')
        report.append((p, n, len(blobs), ovl, picks))

    print()
    bad = [r for r in report if r[1] != r[2]]
    print(f'台数不符页: {len(bad)}/{len(report)}   ' +
          ' '.join(f'p{p}(望{n}/得{k})' for p, n, k, _, _ in bad))
    ov = [r for r in report if r[3]]
    print(f'与文字重叠页: {len(ov)}/{len(report)}   ' +
          ' '.join(f'p{p}({o})' for p, _, _, o, _ in ov))
    allp = [b for r in report for b in r[4]]
    if allp:
        ws = sorted(x1 - x0 for _, x0, y0, x1, y1 in allp)
        hs = sorted(y1 - y0 for _, x0, y0, x1, y1 in allp)
        print(f'裁图宽度 中位 {ws[len(ws)//2]}  最小 {ws[0]}  最大 {ws[-1]}')
        print(f'裁图高度 中位 {hs[len(hs)//2]}  最小 {hs[0]}  最大 {hs[-1]}')
    print(f'输出 {OUT}')


if __name__ == '__main__':
    main()
