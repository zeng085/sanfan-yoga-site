# -*- coding: utf-8 -*-
"""画册逐页视觉复核：按 OCR 坐标裁出「文字带」，拼图供人工核对
目的：确认「缺 material / weight」到底是画册原文没印，还是 OCR 漏识别
用法: python review_catalog_text_bands_20261001.py <批次号> [页...]
"""
import json, sys, re
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path('/Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16')
SRC  = Path('/Users/mac-zlg/Downloads/result')
OCR  = json.loads((ROOT / 'i18n_build/data/catalog_pilates_ocr.json').read_text(encoding='utf-8'))
OUT  = ROOT / 'i18n_build/reports/review_text_bands_20261001'
OUT.mkdir(parents=True, exist_ok=True)

# 页面上「非规格」的装饰性文字，复核时不必占据版面
SKIP_PAT = re.compile(r'^(Pilates|Reformer|Barrel|Chest|Wunda|Cadillac|Wall|Tower|Chair|Mat|Studio|Yoga)'
                      r'[A-Za-z &\-]*$')


def bands_for_page(pg):
    """把该页文字块按 y 聚成若干「文字带」，返回每段的 (y0, y1, 块列表)"""
    bs = [b for b in (OCR.get(str(pg)) or []) if b['text'].strip()]
    bs = [b for b in bs if not (re.fullmatch(r'\d{1,2}', b['text'].strip()) and b['y_top'] > 0.90)]
    bs.sort(key=lambda b: b['y_top'])
    if not bs:
        return []
    groups, cur = [], [bs[0]]
    for b in bs[1:]:
        if b['y_top'] - (cur[-1]['y_top'] + cur[-1].get('h', 0.03)) > 0.075:
            groups.append(cur); cur = [b]
        else:
            cur.append(b)
    groups.append(cur)
    out = []
    for g in groups:
        y0 = min(b['y_top'] for b in g) - 0.012
        y1 = max(b['y_top'] + b.get('h', 0.03) for b in g) + 0.012
        out.append((y0, y1, g))
    return out


def main():
    tag = sys.argv[1]
    pages = [int(x) for x in sys.argv[2:]] or list(range(4, 42))
    tiles = []
    for pg in pages:
        src = SRC / f'2026英文版电子图册_page_{pg}_2.png'
        if not src.exists():
            cands = sorted(SRC.glob(f'*page_{pg}_*.png'))
            if not cands:
                print(f'[跳过] p{pg} 无图'); continue
            src = cands[0]
        im = Image.open(src).convert('RGB')
        W, H = im.size
        for k, (y0, y1, blocks) in enumerate(bands_for_page(pg), 1):
            band = im.crop((0, max(0, int(y0 * H)), W, min(H, int(y1 * H))))
            # 宽度压到 1500 以内
            if band.width > 1500:
                s = 1500 / band.width
                band = band.resize((1500, int(band.height * s)), Image.LANCZOS)
            canvas = Image.new('RGB', (band.width, band.height + 34), (255, 255, 255))
            canvas.paste(band, (0, 34))
            d = ImageDraw.Draw(canvas)
            d.rectangle([0, 0, band.width, 33], fill=(255, 246, 214))
            d.text((8, 9), f'page_{pg} (画册印刷页 {pg-1:02d})  |  band {k}  |  '
                           f'{len(blocks)} 个 OCR 块', fill=(120, 60, 0))
            d.line([(0, 34), (band.width, 34)], fill=(220, 180, 90), width=2)
            tiles.append(canvas)
            print(f'  page_{pg:<3} band{k}  y={y0:.3f}~{y1:.3f}  {len(blocks)} 块')

    if not tiles:
        print('无内容'); return
    W = max(t.width for t in tiles)
    sheet = Image.new('RGB', (W, sum(t.height + 10 for t in tiles)), (245, 245, 245))
    y = 0
    for t in tiles:
        sheet.paste(t, (0, y)); y += t.height + 10
    out = OUT / f'bands_{tag}.png'
    sheet.save(out)
    print(f'\n→ {out}  ({sheet.width}x{sheet.height})  共 {len(tiles)} 段')


if __name__ == '__main__':
    main()
