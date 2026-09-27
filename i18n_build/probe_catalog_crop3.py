#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从画册整页合成位图中裁出单台产品图 v3 —— 严格暗阈值 + 文字掩膜。

实测到的障碍（决定了为什么不能只靠阈值）：
  · 页面底色不是白：空白区 min 通道中位 246，75% 像素 <250（浅灰渐变）
  · 背景还有一层淡人物剪影：中位 241、p10 203 —— 宽松阈值会把它并进来
  · 产品本体是深色金属件（min 接近 0），所以用**严格阈值**只取产品暗核

v3 流程：
  1) ocrmac 取文字行 bbox → 从掩膜挖掉（带 padding）
  2) dark = min(R,G,B) < 120  ← 只留产品暗核，剪影与底色都排除
  3) 小半径膨胀把暗核连成一体 → 连通域 → 按面积取前 N
  4) 外扩 margin 补回产品的浅色部件（坐垫/踏板）
"""
import fitz, io, os, sys, json, tempfile
import numpy as np
from PIL import Image
from collections import deque
from ocrmac import ocrmac

BASE = os.path.dirname(os.path.abspath(__file__))
PDF = os.path.join(BASE, 'data', 'catalog_pilates_2026_en.pdf')
OUT = '/tmp/pilates_crop_test3'
os.makedirs(OUT, exist_ok=True)

SMALL_W = 900
DARK = int(os.environ.get('DARK', '120'))
PAD_FRAC = 0.010
GROW_FRAC = 0.008
MARGIN_FRAC = 0.022


def load_page_img(doc, pi):
    pg = doc[pi]
    placed = [im for im in pg.get_images(full=True) if pg.get_image_rects(im[0])]
    if not placed:
        return None
    return Image.open(io.BytesIO(doc.extract_image(placed[0][0])['image'])).convert('RGB')


def ocr_boxes(im):
    W, H = im.size
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        tmp = f.name
    im.save(tmp)
    try:
        res = ocrmac.OCR(tmp, language_preference=['en-US']).recognize()
    finally:
        os.unlink(tmp)
    out = []
    for txt, conf, (x, y, w, h) in res:
        out.append((txt, x * W, (1 - (y + h)) * H, (x + w) * W, (1 - y) * H))
    return out


def dilate(mask, r):
    out = mask.copy()
    for k in range(1, r + 1):
        out[k:, :] |= mask[:-k, :]
        out[:-k, :] |= mask[k:, :]
        out[:, k:] |= mask[:, :-k]
        out[:, :-k] |= mask[:, k:]
    return out


def blobs(mask, min_area):
    H, W = mask.shape
    lab = np.zeros((H, W), np.uint8)
    res = []
    for sy, sx in zip(*np.nonzero(mask)):
        if lab[sy, sx]:
            continue
        q = deque([(sy, sx)]); lab[sy, sx] = 1
        y0 = y1 = sy; x0 = x1 = sx; area = 0
        while q:
            y, x = q.popleft(); area += 1
            y0 = min(y0, y); y1 = max(y1, y); x0 = min(x0, x); x1 = max(x1, x)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not lab[ny, nx]:
                        lab[ny, nx] = 1; q.append((ny, nx))
        if area >= min_area:
            res.append((area, x0, y0, x1, y1))
    res.sort(reverse=True)
    return res


def main():
    doc = fitz.open(PDF)
    models = json.load(open(os.path.join(BASE, 'data', 'catalog_pilates_models.json'),
                            encoding='utf-8'))
    per_page = {}
    for m in models:
        per_page.setdefault(m['page'], []).append(m['model'])
    only = [int(a) for a in sys.argv[1:] if a.isdigit()] or sorted(per_page)

    report = []
    for p in only:
        im = load_page_img(doc, p - 1)
        if im is None:
            print(f'p{p}: 无 raster'); continue
        W, H = im.size
        sc = SMALL_W / W
        small = im.resize((SMALL_W, max(1, round(H * sc))), Image.BILINEAR)
        SH, SW = small.size[1], SMALL_W
        a = np.asarray(small).astype(np.int16)
        dark = a.min(axis=2) < DARK

        tb = ocr_boxes(im)
        pad = PAD_FRAC * W
        for txt, x0, y0, x1, y1 in tb:
            dark[max(0, int((y0 - pad) * sc)):min(SH, int((y1 + pad) * sc)),
                 max(0, int((x0 - pad) * sc)):min(SW, int((x1 + pad) * sc))] = False

        d = dilate(dark, max(2, round(SMALL_W * GROW_FRAC)))
        found = blobs(d, int(SH * SW * 0.0015))
        # 丢掉明显是横线/竖线的碎片
        found = [f for f in found if (f[3] - f[1]) > SW * 0.05 and (f[4] - f[2]) > SH * 0.05]
        n = len(per_page[p])
        picks = found[:n]
        mg = MARGIN_FRAC * min(SW, SH)

        va = np.asarray(small).copy()
        crops = []
        for i, (area, x0, y0, x1, y1) in enumerate(picks):
            gx0 = int(max(0, x0 - mg)); gy0 = int(max(0, y0 - mg))
            gx1 = int(min(SW, x1 + mg)); gy1 = int(min(SH, y1 + mg))
            va[gy0:gy1, gx0] = [255, 0, 0]; va[gy0:gy1, gx1 - 1] = [255, 0, 0]
            va[gy0, gx0:gx1] = [255, 0, 0]; va[gy1 - 1, gx0:gx1] = [255, 0, 0]
            # 暗核用绿框标出，便于看外扩是否合理
            va[y0:y1, x0] = [0, 170, 0]; va[y0:y1, x1 - 1] = [0, 170, 0]
            va[y0, x0:x1] = [0, 170, 0]; va[y1 - 1, x0:x1] = [0, 170, 0]
            px0 = int(gx0 / sc); py0 = int(gy0 / sc)
            px1 = min(W, int(gx1 / sc)); py1 = min(H, int(gy1 / sc))
            crops.append((px0, py0, px1, py1))
        Image.fromarray(va).save(f'{OUT}/overlay_p{p:02d}.png')
        for i, c in enumerate(crops):
            im.crop(c).save(f'{OUT}/crop_p{p:02d}_{i}_{c[2]-c[0]}x{c[3]-c[1]}.png')

        ovl = sum(1 for (px0, py0, px1, py1) in crops
                  for _, tx0, ty0, tx1, ty1 in tb
                  if tx0 < px1 and tx1 > px0 and ty0 < py1 and ty1 > py0)
        dims = ' | '.join(f'{c[2]-c[0]}x{c[3]-c[1]}' for c in crops)
        print(f'p{p:>2} 望{n} 得{len(found)} 文字{len(tb):>2} 重叠{ovl:>2}  {dims}')
        report.append((p, n, len(found), ovl, crops))

    print()
    bad = [r for r in report if r[1] != r[2]]
    print(f'① 台数不符: {len(bad)}/{len(report)}  ' +
          ' '.join(f'p{p}(望{n}/得{k})' for p, n, k, _, _ in bad))
    ov = [r for r in report if r[3]]
    print(f'② 与文字重叠: {len(ov)}/{len(report)}  ' +
          ' '.join(f'p{p}({o})' for p, _, _, o, _ in ov))
    allp = [c for r in report for c in r[4]]
    if allp:
        ws = sorted(c[2]-c[0] for c in allp); hs = sorted(c[3]-c[1] for c in allp)
        print(f'③ 裁图 {len(allp)} 张  宽 中位{ws[len(ws)//2]} [{ws[0]}..{ws[-1]}]  '
              f'高 中位{hs[len(hs)//2]} [{hs[0]}..{hs[-1]}]')
    print(f'输出 {OUT}')


if __name__ == '__main__':
    main()
