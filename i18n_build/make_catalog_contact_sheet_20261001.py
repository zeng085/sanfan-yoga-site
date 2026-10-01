#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 result/ 下 40 张画册整页图拼成 contact sheet，用于一次性目视清点。
输出：i18n_build/reports/catalog_contact_sheet_20261001.png（5 列）
"""
import os
import re
import glob
from PIL import Image, ImageDraw

SRC = "/Users/mac-zlg/Downloads/result"
OUT = "/Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16/i18n_build/reports/catalog_contact_sheet_20261001.png"

files = glob.glob(os.path.join(SRC, "*.png"))


def key(p):
    m = re.search(r"page_(\d+)_(\d+)", os.path.basename(p))
    return (int(m.group(1)), int(m.group(2))) if m else (999, 0)


files.sort(key=key)
print(f"共 {len(files)} 张")

COLS = 5
THUMB_W = 430
pad = 8
label_h = 26
rows = (len(files) + COLS - 1) // COLS

# 先统一缩略图高度（横竖比例一致：2397x2433 ≈ 0.985）
th = int(THUMB_W * 2433 / 2397)
W = COLS * THUMB_W + (COLS + 1) * pad
H = rows * (th + label_h) + (rows + 1) * pad

sheet = Image.new("RGB", (W, H), (245, 245, 247))
d = ImageDraw.Draw(sheet)

for i, f in enumerate(files):
    r, c = divmod(i, COLS)
    x = pad + c * (THUMB_W + pad)
    y = pad + r * (th + label_h + pad)
    try:
        im = Image.open(f).convert("RGB")
    except Exception as e:
        print(f"  跳过 {f}: {e}")
        continue
    im.thumbnail((THUMB_W, th), Image.LANCZOS)
    sheet.paste(im, (x, y + label_h))
    m = re.search(r"page_(\d+)_(\d+)", os.path.basename(f))
    tag = f"p{m.group(1)} (idx{m.group(2)})" if m else os.path.basename(f)
    d.rectangle([x, y, x + THUMB_W, y + label_h - 2], fill=(30, 30, 34))
    d.text((x + 6, y + 6), tag, fill=(255, 255, 255))

sheet.save(OUT, quality=88)
print(f"输出 {OUT}  {sheet.size[0]}x{sheet.size[1]}  {os.path.getsize(OUT)//1024}KB")
