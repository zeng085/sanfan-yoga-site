#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按人工/目视确定的 bbox 批量裁剪画册页 → 单品图（2026-10-01）

与 probe_catalog_crop_20261001.py 的区别：那个是**自动**投影法（已证不可行）；
这个是**人在回路**：bbox 由目视逐台确定（存 JSON），脚本只负责裁+缩放+导出。
本文件先用 page_4 做可行性验证。
"""
import json
import os
from PIL import Image

SRC = "/Users/mac-zlg/Downloads/result"
OUT = "/Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16/i18n_build/reports/crop_manual_20261001"

# 原图 2397x2433；目视于 1063 宽缩略图上定框，×2.2549 换算回原图
S = 2397 / 1063.0
def cv(x, y):
    return int(x * S), int(y * S)

SPEC = [
    # (页, 序号, 型号, 缩略坐标 x0,y0,x1,y1)
    ("4_2", 1, "AL 19-F", (85, 95, 885, 515)),
    ("4_2", 2, "AL 8-Y", (140, 635, 1063, 1025)),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    for page, idx, model, (x0, y0, x1, y1) in SPEC:
        p = os.path.join(SRC, f"2026英文版电子图册_page_{page}.png")
        im = Image.open(p).convert("RGB")
        X0, Y0 = cv(x0, y0)
        X1, Y1 = cv(x1, y1)
        X0 = max(0, X0); Y0 = max(0, Y0)
        X1 = min(im.width, X1); Y1 = min(im.height, Y1)
        c = im.crop((X0, Y0, X1, Y1))
        name = model.lower().replace(" ", "-") + ".webp"
        c.save(os.path.join(OUT, name), quality=88, method=6)
        # 同时导一张 png 便于目视
        c.save(os.path.join(OUT, model.lower().replace(" ", "-") + ".png"))
        print(f"  {model:10s} bbox=({X0},{Y0},{X1},{Y1})  {c.width}x{c.height}  -> {name}")

    # 拼版对比（左侧原页缩略、右侧两张裁图）
    im = Image.open(os.path.join(SRC, "2026英文版电子图册_page_4_2.png")).convert("RGB")
    im.thumbnail((700, 700), Image.LANCZOS)
    crops = []
    for page, idx, model, _ in SPEC:
        f = os.path.join(OUT, model.lower().replace(" ", "-") + ".png")
        t = Image.open(f)
        t.thumbnail((700, 320), Image.LANCZOS)
        crops.append(t)
    W = 700 + 20 + max(t.width for t in crops) + 20
    H = max(im.height, sum(t.height for t in crops) + 10 * (len(crops) - 1)) + 20
    sheet = Image.new("RGB", (W, H), (235, 235, 238))
    sheet.paste(im, (10, 10))
    y = 10
    for t in crops:
        sheet.paste(t, (720, y))
        y += t.height + 10
    sheet.save(os.path.join(OUT, "_compare.png"))
    print(f"对比版 {os.path.join(OUT, '_compare.png')}  {sheet.size[0]}x{sheet.size[1]}")


if __name__ == "__main__":
    main()
