#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量裁剪（含邻框合并）——产出 69 张候选产品图 + 指标。"""
import fitz, io, os, json, time
import numpy as np
from PIL import Image
import probe_catalog_crop3 as v3

DOC = fitz.open('data/catalog_pilates_2026_en.pdf')
MODELS = json.load(open('data/catalog_pilates_models.json'))
PER = {}
for _m in MODELS:
    PER.setdefault(_m['page'], []).append(_m['model'])


def merge(boxes, gap):
    items = [list(b) for b in boxes]
    changed = True
    while changed:
        changed = False
        out = []
        while items:
            a = items.pop()
            done = False
            for b in out:
                if not (a[3] + gap < b[1] or a[1] > b[3] + gap
                        or a[4] + gap < b[2] or a[2] > b[4] + gap):
                    b[0] += a[0]
                    b[1] = min(b[1], a[1]); b[2] = min(b[2], a[2])
                    b[3] = max(b[3], a[3]); b[4] = max(b[4], a[4])
                    done = True; changed = True; break
            if not done:
                out.append(a)
        items = out
    items.sort(reverse=True)
    return items


def main():
    os.makedirs('/tmp/pilates_final', exist_ok=True)
    ok = ov = tot = 0
    bad, sizes = [], []
    t0 = time.time()
    for p in sorted(PER):
        im = v3.load_page_img(DOC, p - 1)
        W, H = im.size
        sc = 900 / W
        small = im.resize((900, round(H * sc)), Image.BILINEAR)
        SH = small.size[1]
        a = np.asarray(small).astype(np.int16)
        dark = a.min(axis=2) < 120
        tb = v3.ocr_boxes(im)
        pad = 0.010 * W
        for t, x0, y0, x1, y1 in tb:
            dark[max(0, int((y0 - pad) * sc)):min(SH, int((y1 + pad) * sc)),
                 max(0, int((x0 - pad) * sc)):min(900, int((x1 + pad) * sc))] = False
        d = v3.dilate(dark, 7)
        cs = v3.blobs(d, int(SH * 900 * 0.0012))
        cs = [c for c in cs if (c[3] - c[1]) > 900 * 0.04 and (c[4] - c[2]) > SH * 0.04]
        m = merge(cs, int(min(900, SH) * 0.05))
        n = len(PER[p]); tot += n
        pick = m[:n]
        if len(pick) == n:
            ok += 1
        else:
            bad.append(f'p{p}(望{n}/得{len(pick)})')
        mg = int(min(900, SH) * 0.022)
        boxs = []
        for i, (area, x0, y0, x1, y1) in enumerate(pick):
            gx0 = max(0, x0 - mg) / sc; gy0 = max(0, y0 - mg) / sc
            gx1 = min(900, x1 + mg) / sc; gy1 = min(SH, y1 + mg) / sc
            sizes.append((gx1 - gx0, gy1 - gy0))
            boxs.append(f'{int(gx1 - gx0)}x{int(gy1 - gy0)}')
            for t, tx0, ty0, tx1, ty1 in tb:
                if tx0 < gx1 and tx1 > gx0 and ty0 < gy1 and ty1 > gy0:
                    ov += 1; break
            im.crop((int(gx0), int(gy0), int(gx1), int(gy1))).save(
                f'/tmp/pilates_final/p{p:02d}_{i}.png')
        print(f'p{p:>2} 望{n} 得{len(pick)}  {" ".join(boxs)}', flush=True)

    ws = sorted(int(s[0]) for s in sizes)
    hs = sorted(int(s[1]) for s in sizes)
    print()
    print('=== 合并后（DARK=120, gap=5%页宽）===')
    print(f'① 台数全对页 {ok}/38   不符 {len(bad)}: {" ".join(bad)}')
    print(f'② 与规格文字重叠 {ov}/{tot} 台')
    print(f'③ 裁图 {len(sizes)} 张  宽中位 {ws[len(ws)//2]} [{ws[0]}..{ws[-1]}]  '
          f'高中位 {hs[len(hs)//2]} [{hs[0]}..{hs[-1]}]')
    print(f'   长边≥1500 {sum(1 for w,h in sizes if max(w,h)>=1500)}/{len(sizes)}'
          f'   长边≥1000 {sum(1 for w,h in sizes if max(w,h)>=1000)}/{len(sizes)}')
    print(f'耗时 {time.time()-t0:.0f}s')


if __name__ == '__main__':
    main()
