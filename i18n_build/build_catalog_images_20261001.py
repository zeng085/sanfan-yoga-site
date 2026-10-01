#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 38 张画册产品页（page_4 ~ page_41）转成 webp，入库 assets/img/catalog/。

为什么不裁页码：
  实测页码 y≈0.930~0.955，而规格文字（Gross weight 行）延伸到 y=0.95 ——
  两者在同一高度带，按比例裁底部一定会切掉文字。页码本身是画册页号，
  与「按画册页组织产品」的结构一致，保留反而有用（页面文案可写 Catalog page N）。

输出：
  - assets/img/catalog/p04.webp ... p41.webp
  - i18n_build/data/catalog_images_20261001.json（含真实 width/height）
"""
import json
import os
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = Path('/Users/mac-zlg/Downloads/result')
DST_DIR = ROOT / 'assets/img/catalog'
OUT_JSON = ROOT / 'i18n_build/data/catalog_images_20261001.json'

PAGE_RANGE = range(4, 42)
LONG_EDGE = 1600
QUALITY = 84

# page_N_M.png，封面/公司页的 M 不同，产品页统一是 _2
def find_src(pg: int) -> Path:
    cands = sorted(SRC_DIR.glob(f'*page_{pg}_*.png'))
    if not cands:
        raise FileNotFoundError(f'page {pg} 无源图')
    # 优先 _2
    for c in cands:
        if c.stem.endswith('_2'):
            return c
    return cands[0]


def main():
    DST_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    total = 0
    for pg in PAGE_RANGE:
        src = find_src(pg)
        im = Image.open(src).convert('RGB')
        w0, h0 = im.size
        scale = LONG_EDGE / max(w0, h0)
        if scale < 1:
            im = im.resize((round(w0 * scale), round(h0 * scale)), Image.LANCZOS)
        out = DST_DIR / f'p{pg:02d}.webp'
        im.save(out, 'WEBP', quality=QUALITY, method=6)
        size = out.stat().st_size
        total += size
        manifest.append({
            'page': pg,
            'file': f'assets/img/catalog/p{pg:02d}.webp',
            'width': im.size[0],
            'height': im.size[1],
            'src': src.name,
            'src_size': [w0, h0],
            'bytes': size,
        })
        print(f'  p{pg:02d}  {w0}x{h0} -> {im.size[0]}x{im.size[1]}  {size/1024:6.1f} KB  ({src.name})')

    OUT_JSON.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'\n共 {len(manifest)} 张，合计 {total/1024/1024:.2f} MB，'
          f'平均 {total/len(manifest)/1024:.1f} KB')
    print(f'-> {DST_DIR}')
    print(f'-> {OUT_JSON}')


if __name__ == '__main__':
    main()
