#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""把纯图片 PDF 逐页渲染成 PNG，供人工/多模态识别。

PDF 是 Adobe Image Conversion 生成的**无文字层**文件（42 页，全部信息在像素里），
所以只能渲染后看图。输出目录默认 /tmp（不进仓库）。

用法：
    $VENV/bin/python i18n_build/render_catalog_pages.py [--zoom 1.0] [--out /tmp/catalog-probe]
"""
import argparse
import pathlib
import sys

import fitz

ROOT = pathlib.Path(__file__).resolve().parent.parent
PDF = ROOT / "i18n_build" / "data" / "catalog_pilates_2026_en.pdf"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zoom", type=float, default=1.0, help="缩放（1.0 ≈ 2398px 宽）")
    ap.add_argument("--out", default="/tmp/catalog-probe")
    ap.add_argument("--pages", default="", help="如 1-8；空=全部")
    args = ap.parse_args()

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(PDF))
    total = len(doc)
    if args.pages:
        a, _, b = args.pages.partition("-")
        lo, hi = int(a), int(b or a)
    else:
        lo, hi = 1, total

    for i in range(lo, hi + 1):
        page = doc[i - 1]
        pix = page.get_pixmap(matrix=fitz.Matrix(args.zoom, args.zoom))
        f = out / ("p%02d.png" % i)
        pix.save(str(f))
        print("  p%-3d %dx%d  %.2f MB" % (i, pix.width, pix.height,
                                          f.stat().st_size / 1048576))
    print("\n→ 共 %d 页渲染到 %s" % (hi - lo + 1, out))


if __name__ == "__main__":
    sys.exit(main())
