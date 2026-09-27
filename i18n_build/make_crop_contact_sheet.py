#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把裁出的候选产品图拼成一张联系表（人工核验用）。"""
import os, glob
from PIL import Image, ImageDraw

SRC = '/tmp/pilates_final'
OUT = '/tmp/pilates_final/_contact_sheet.png'
CELL = 240
COLS = 8
PAD = 6
LBL = 16

files = sorted(glob.glob(f'{SRC}/p*.png'))
ims = []
for f in files:
    im = Image.open(f).convert('RGB')
    im.thumbnail((CELL, CELL), Image.LANCZOS)
    ims.append((os.path.basename(f)[:-4], im))

rows = (len(ims) + COLS - 1) // COLS
W = COLS * (CELL + PAD) + PAD
H = rows * (CELL + LBL + PAD) + PAD
sheet = Image.new('RGB', (W, H), (250, 250, 250))
d = ImageDraw.Draw(sheet)
for i, (name, im) in enumerate(ims):
    r, c = divmod(i, COLS)
    x = PAD + c * (CELL + PAD)
    y = PAD + r * (CELL + LBL + PAD)
    sheet.paste(im, (x + (CELL - im.size[0]) // 2, y + (CELL - im.size[1]) // 2))
    d.rectangle([x, y, x + CELL, y + CELL], outline=(210, 210, 210))
    d.text((x + 2, y + CELL + 2), name, fill=(60, 60, 60))
sheet.save(OUT)
print(f'{len(ims)} 张 → {OUT}  {sheet.size}')
