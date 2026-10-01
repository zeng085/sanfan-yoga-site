#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成「21-FO / 20-V5 归属」对照图 —— 画册第 33 页 vs 第 35 页。

=====================================================================
坐标约定（先统一，否则会错一页）
=====================================================================
    文件页码 = 印刷页码 + 1
    文件 p34.webp -> 纸上印「33」
    文件 p36.webp -> 纸上印「35」

=====================================================================
事实（逐页打开原件核对）
=====================================================================
    纸上印 33（p34）  标题印 Ladder Barre 21-FO / 20-V5（位置在梯桶章内）
                      实物却是两台【稳踏椅】，箱规 920*720*790
    纸上印 35（p36）  标题印 Chair 21-FO / 20-V5（位置在稳踏椅章首页）
                      实物却是两台【梯桶】，箱规 1190*700*1170

每页的「实物 + 箱规」各自自洽（椅子配椅子箱规、梯桶配梯桶箱规），
标题与所在分章也都自洽 —— **错的是两个「实物+箱规」块被贴到了对方页上**。

=====================================================================
三条判据
=====================================================================
1. 分章连续性：梯桶章 32→33→34 连续，稳踏椅章 35 起。
   按"型号名误抄"处理会让两章各夹进一台别族产品（两处错位）；
   按"图块放错页"处理只错 2 个图块。后者更省。
2. 箱规量级：920*720*790 与 Chair 10-A 完全相同；
   1190*700*1170 与 Ladder Barre -3 完全相同。
   梯桶线没有 0.79m 高的、稳踏椅线没有 1.17m 高的。
3. ⭐ 后缀跨线复用：核心床章亦用同样后缀 ——
   印刷 08（p9）Metal 20-V5 / 印刷 09（p10）AL 21-FO。
   故"梯桶不该有这两个号"不成立。

=====================================================================
结论
=====================================================================
两条线**各自都有** 21-FO / 20-V5：
    Ladder Barre 21-FO / 20-V5  金属梯桶    1190*700*1170mm / 85kg（实物在印 35 页）
    Chair 21-FO / 20-V5         金属稳踏椅   920*720*790mm / 85kg（实物在印 33 页）
→ 梯桶线共 7 台。

给工厂的一句话：画册这两页的「实物图 + 箱规」块需要对调归位。

用法：python3 make_catalog_compare_20261001.py
"""
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = os.path.join(ROOT, "assets", "img", "catalog")
OUT = os.path.join(ROOT, "outputs", "pilates_block_v2", "catalog-21fo-attribution.png")

INK = (28, 24, 20)
MUTED = (120, 110, 100)
RED = (176, 58, 42)
GREEN = (20, 96, 63)
BLUE = (32, 74, 130)
LINE = (226, 220, 212)
BG = (255, 255, 255)
SOFT = (247, 244, 240)

FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
]


def font(size, bold=False):
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size, index=1 if bold else 0)
            except Exception:
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    continue
    return ImageFont.load_default()


def main():
    pages = [
        dict(file="p34.webp", printed="33", chapter="梯桶章内",
             title="Ladder Barre 21-FO  ·  Ladder Barre 20-V5",
             real="稳踏椅（踏板＋双立柱把手 / 方凳＋高把手）",
             packing="920 × 720 × 790 mm  /  85 kg",
             ref="与 Chair 10-A 的箱规完全相同 → 这是椅子的箱规"),
        dict(file="p36.webp", printed="35", chapter="稳踏椅章首页",
             title="Chair 21-FO  ·  Chair 20-V5",
             real="梯桶（桶身＋竖梯，米色 / 深灰）",
             packing="1190 × 700 × 1170 mm  /  85 kg",
             ref="与 Ladder Barre -3 的箱规完全相同 → 这是梯桶的箱规"),
    ]

    COL_W = 940
    IMG_H = 900
    PAD = 40
    HEAD = 104
    FOOT = 300
    W = PAD * 3 + COL_W * 2
    H = HEAD + IMG_H + FOOT + PAD

    canvas = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(canvas)

    dr.text((PAD, 26), "2026 画册：第 33 页与第 35 页的「实物图 + 箱规」块被贴到了对方页上",
            font=font(34, True), fill=INK)
    dr.text((PAD, 70), "标题与所在分章都对，实物与箱规各自也自洽 —— 只有这两个图块互换了位置",
            font=font(22), fill=MUTED)

    for i, pg in enumerate(pages):
        x = PAD + i * (COL_W + PAD)
        y = HEAD

        img = Image.open(os.path.join(CAT, pg["file"])).convert("RGB")
        img.thumbnail((COL_W, IMG_H), Image.LANCZOS)
        canvas.paste(img, (x + (COL_W - img.width) // 2, y))
        dr.rectangle([x, y, x + COL_W - 1, y + IMG_H - 1], outline=LINE)

        dr.rectangle([x, y, x + 118, y + 44], fill=INK)
        dr.text((x + 14, y + 8), f"纸上印 {pg['printed']}", font=font(24, True), fill=(255, 255, 255))
        dr.rectangle([x + 126, y, x + 300, y + 44], fill=SOFT)
        dr.text((x + 140, y + 9), pg["chapter"], font=font(22), fill=MUTED)

        ty = y + IMG_H + 20
        for label, value, color in (("该页标题印：", pg["title"], BLUE),
                                    ("该页实物是：", pg["real"], GREEN),
                                    ("该页箱规是：", pg["packing"], INK)):
            dr.text((x, ty), label, font=font(21), fill=MUTED)
            dr.text((x + 132, ty), value, font=font(21, True), fill=color)
            ty += 34
        dr.text((x + 132, ty), pg["ref"], font=font(19), fill=RED)
        ty += 30
        dr.text((x, ty), "→ 图块贴错页，标题为准",
                font=font(21, True), fill=RED)

    # 底部结论
    by = HEAD + IMG_H + 190
    dr.rectangle([PAD, by - 14, W - PAD, by + 106], fill=SOFT)
    dr.rectangle([PAD, by - 14, PAD + 5, by + 106], fill=GREEN)
    dr.text((PAD + 24, by - 2),
            "结论：两条线各自都有 21-FO / 20-V5 —— 后缀是跨线复用的版型号。",
            font=font(24, True), fill=INK)
    dr.text((PAD + 24, by + 34),
            "Ladder Barre 21-FO / 20-V5　　金属梯桶　　1190×700×1170 mm / 85 kg　（实物见第 35 页）",
            font=font(23, True), fill=GREEN)
    dr.text((PAD + 24, by + 70),
            "Chair 21-FO / 20-V5　　　　　　金属稳踏椅　　920×720×790 mm / 85 kg　（实物见第 33 页）",
            font=font(23, True), fill=GREEN)

    dr.text((PAD, by + 124),
            "旁证：核心床章亦用同样后缀 —— 印刷 08 页 Metal 20-V5、印刷 09 页 AL 21-FO；"
            "故「梯桶不该有这两个号」不成立。",
            font=font(21), fill=MUTED)
    dr.text((PAD, by + 156),
            "给工厂的一句话：画册这两页的「实物图 + 箱规」块需要对调归位（型号名不用改）。",
            font=font(21, True), fill=RED)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    canvas.save(OUT, optimize=True)
    print("已写出", os.path.relpath(OUT, ROOT), canvas.size,
          f"{os.path.getsize(OUT)/1e6:.2f} MB")


if __name__ == "__main__":
    main()
