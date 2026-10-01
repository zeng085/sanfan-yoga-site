#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 2026 画册整页扫描图里，裁出「一台产品一张图」。

原理
----
画册页是白底产品 layout：产品是深色块，规格文字是深色小块，人形剪影是极浅的灰。

  1. 掩膜 = 「非接近白」像素（255 - min(r,g,b) > THRESH）
     阈值 40 恰好把浅灰人形剪影排除，保留产品与文字
  2. 用 OCR 文字块坐标把文字从掩膜里挖掉 → 只剩产品
  3. **XY-cut（递归投影切分）** 把版面切成块：
     找出足够宽/高的空白带切一刀，两侧各自递归；切不动就是一块
     —— 比「连通域 + 间距合并」稳，因为产品内部（梯子 vs 桶身）的
        间隙与产品之间的间隙量级接近，间距判据会误合
  4. 若切出的块数多于型号数，把距离最近的两块反复合并到数量相等
  5. **按阅读序配对**：型号标签与产品块各自按 (y, x) 排序后一一对应。
     距离最近法在画册页上会错配（产品常与标签呈对角摆放），阅读序才稳。

输出（默认 /tmp/crop_proto，不碰站点）：
  page{NN}_boxes.png   在原页画出块框 + 型号名 → 人工核对
  {model}.png          单台成品裁图

用法：
  python crop_catalog_products_20261001.py --pages 33,34,35
  python crop_catalog_products_20261001.py --family 梯桶 --outdir /tmp/x
"""
import argparse
import json
import os
import re

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
SRC_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "result")

# 阈值实测依据（2026 画册实页采样）：
#   人形剪影/淡灰水印最暗约 208 级 → 255-208 = 47
#   产品轮廓最暗 119 级（木色）、37 级（黑皮）→ 255-119 = 136
# 取 70 作分界：剪影（47）被排除，产品轮廓（136）保留。
# 用 40 会把剪影算成内容，从而把上下两台产品「桥接」成一块，切不开。
THRESH = 70           # 非白判据：255 - min(r,g,b) 超过此值算内容
MASK_SCALE = 600      # 掩膜工作宽度
TEXT_PAD = 0.012      # 挖文字块时外扩（归一化）
SPLIT_BLANK = 0.012   # 切分所需空白带宽度（占页面相应边比例）
MIN_LEAF_AREA = 0.010  # 叶子块最小面积（占页面面积比）
CROP_PAD = 0.012      # 最终裁图四周留白


def erase_strays(img: "Image.Image", gap: float = 0.012, rel: float = 0.05,
                 border: float = 0.10, scale: int = 300):
    """擦掉贴边的孤立小块（页码、残留文字）。

    为什么不能只靠 OCR 擦字：第 35 页的页码「34」OCR 根本没识别出来，
    没有框可擦。所以改成图像判据——
      在裁图上重新取内容掩膜 → 连通域 → 按间距聚成簇 → 保留最大的一簇，
      其余小簇涂白。

    两条保险，避免误伤产品：
      · gap 取得小（1.2%）：产品自身的「梯子 + 桶身」几乎挨着，仍会并成一簇；
      · 只擦**贴边**的小簇（border=10%）：页码总在页角，而产品不会长到边角上。
        —— 实测 gap=3.5% 时页码与产品自成一簇，擦不掉；必须靠「贴边」这条。
    """
    w, h = img.size
    sc = scale / w
    small = np.asarray(img.resize((scale, max(1, int(h * sc))), Image.BILINEAR)).astype(np.int16)
    mask = (255 - small.min(axis=2)) > THRESH
    comps = connected_boxes(mask)
    clusters = cluster_boxes(comps, mask.shape[1], mask.shape[0], gap_ratio=gap)
    if len(clusters) <= 1:
        return img, 0
    clusters.sort(key=lambda c: -c[4])
    main = clusters[0][4]
    sw, sh = mask.shape[1], mask.shape[0]
    out = img.copy()
    dr = ImageDraw.Draw(out)
    n = 0
    for c in clusters[1:]:
        if c[4] > rel * main:
            continue
        near_edge = (min(c[0], sw - c[2]) <= border * sw or
                     min(c[1], sh - c[3]) <= border * sh)
        if not near_edge:
            continue
        x0 = max(0, int(c[0] / sc) - 2)
        y0 = max(0, int(c[1] / sc) - 2)
        x1 = min(w, int((c[2] + 1) / sc) + 2)
        y1 = min(h, int((c[3] + 1) / sc) + 2)
        dr.rectangle([x0, y0, x1, y1], fill=(255, 255, 255))
        n += 1
    return out, n
    w, h = img.size
    sc = scale / w
    small = np.asarray(img.resize((scale, max(1, int(h * sc))), Image.BILINEAR)).astype(np.int16)
    mask = (255 - small.min(axis=2)) > THRESH
    comps = connected_boxes(mask)
    clusters = cluster_boxes(comps, mask.shape[1], mask.shape[0], gap_ratio=gap)
    if len(clusters) <= 1:
        return img, 0
    clusters.sort(key=lambda c: -c[4])
    main = clusters[0][4]
    out = img.copy()
    dr = ImageDraw.Draw(out)
    n = 0
    for c in clusters[1:]:
        if c[4] > rel * main:
            continue
        x0 = max(0, int(c[0] / sc) - 2)
        y0 = max(0, int(c[1] / sc) - 2)
        x1 = min(w, int((c[2] + 1) / sc) + 2)
        y1 = min(h, int((c[3] + 1) / sc) + 2)
        dr.rectangle([x0, y0, x1, y1], fill=(255, 255, 255))
        n += 1
    return out, n


def connected_boxes(mask, min_px=4):
    """8 连通域 → [[x0,y0,x1,y1,面积]]，用行内游程 + 并查集，比逐像素 BFS 快。"""
    sh, sw = mask.shape
    parent = {}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    runs_by_row = []
    idx = 0
    for y in range(sh):
        row = mask[y]
        xs = np.where(row)[0]
        runs = []
        if len(xs):
            start = prev = xs[0]
            for x in xs[1:]:
                if x == prev + 1:
                    prev = x
                else:
                    runs.append((start, prev))
                    start = prev = x
            runs.append((start, prev))
        cur = []
        for (a, b) in runs:
            parent[idx] = idx
            cur.append((a, b, idx))
            idx += 1
        for (a, b, i2) in cur:
            for (a2, b2, j2) in runs_by_row[-1] if runs_by_row else []:
                if a <= b2 + 1 and a2 <= b + 1:
                    union(i2, j2)
        runs_by_row.append(cur)

    agg = {}
    for y, cur in enumerate(runs_by_row):
        for (a, b, i2) in cur:
            r = find(i2)
            e = agg.get(r)
            if e is None:
                agg[r] = [a, y, b, y, b - a + 1]
            else:
                e[0] = min(e[0], a)
                e[1] = min(e[1], y)
                e[2] = max(e[2], b)
                e[3] = max(e[3], y)
                e[4] += b - a + 1
    return [v for v in agg.values() if v[4] >= min_px]


def cluster_boxes(boxes, sw, sh, gap_ratio=0.035):
    """把邻近的连通域并成簇（同一台产品可能由梯子、桶身等几块组成）。"""
    out = [list(b) for b in boxes]
    gapx, gapy = gap_ratio * sw, gap_ratio * sh
    changed = True
    while changed:
        changed = False
        for i in range(len(out)):
            for j in range(i + 1, len(out)):
                a, b = out[i], out[j]
                if (a[0] - gapx <= b[2] and b[0] - gapx <= a[2] and
                        a[1] - gapy <= b[3] and b[1] - gapy <= a[3]):
                    out[i] = [min(a[0], b[0]), min(a[1], b[1]),
                              max(a[2], b[2]), max(a[3], b[3]), a[4] + b[4]]
                    out.pop(j)
                    changed = True
                    break
            if changed:
                break
    return out


def slug(model: str) -> str:
    s = model.lower().replace(" ", "-")
    s = re.sub(r"[^a-z0-9\-]+", "", s)
    return re.sub(r"-{2,}", "-", s).strip("-")


def erase_text(img: "Image.Image", crop_box, texts: list, pad: float = 0.004):
    """把与裁图区域相交的 OCR 文字块涂白。

    掩膜阶段虽然挖掉了文字，但裁图矩形 = 掩膜包围盒 + 留白，
    留白会把邻行的规格文字、页码重新圈进来（实测：4-T 带进页码「3」、
    2-A 带进上一行「Gross weight: 90kg」）。
    所以必须在成品图上再擦一次，这是最后一道保险。
    """
    w, h = img.size
    x0, y0, x1, y1 = crop_box
    out = img.copy()
    dr = ImageDraw.Draw(out)
    n = 0
    for t in texts:
        tx0 = (t["x"] - pad) * w
        ty0 = (t["y_top"] - pad) * h
        tx1 = (t["x"] + t["w"] + pad) * w
        ty1 = (t["y_top"] + t["h"] + pad) * h
        if tx1 <= x0 or tx0 >= x1 or ty1 <= y0 or ty0 >= y1:
            continue
        dr.rectangle([tx0 - x0, ty0 - y0, tx1 - x0, ty1 - y0], fill=(255, 255, 255))
        n += 1
    return out, n


def build_mask(img: Image.Image, texts: list):
    w, h = img.size
    scale = MASK_SCALE / w
    small = img.resize((int(w * scale), int(h * scale)), Image.BILINEAR)
    arr = np.asarray(small).astype(np.int16)
    mask = (255 - arr.min(axis=2)) > THRESH
    sh, sw = mask.shape
    for t in texts:
        x0 = int((t["x"] - TEXT_PAD) * sw)
        x1 = int((t["x"] + t["w"] + TEXT_PAD) * sw)
        y0 = int((t["y_top"] - TEXT_PAD) * sh)
        y1 = int((t["y_top"] + t["h"] + TEXT_PAD) * sh)
        mask[max(0, y0):min(sh, y1), max(0, x0):min(sw, x1)] = False
    return mask


def _gaps(profile, blank_len, thresh_frac):
    """返回 [(start, end, length)]，profile 低于阈值且长度达标的连续段。"""
    lim = max(1, thresh_frac * (profile.max() if profile.size else 1))
    low = profile <= lim
    out, s = [], None
    for i, v in enumerate(low):
        if v and s is None:
            s = i
        elif not v and s is not None:
            if i - s >= blank_len:
                out.append((s, i, i - s))
            s = None
    if s is not None and len(low) - s >= blank_len:
        out.append((s, len(low), len(low) - s))
    return out


def xy_cut(mask, rect, sw, sh, depth=0):
    x0, y0, x1, y1 = rect
    if depth > 8 or (x1 - x0) < 0.05 * sw or (y1 - y0) < 0.05 * sh:
        return [rect]
    sub = mask[y0:y1, x0:x1]
    if not sub.any():
        return []
    rowp = sub.sum(axis=1)
    colp = sub.sum(axis=0)
    rband = max(2, int(SPLIT_BLANK * sh))
    cband = max(2, int(SPLIT_BLANK * sw))

    best = None  # (gap_len, axis, pos)
    for s, e, ln in _gaps(rowp, rband, 0.02):
        # 切点取空白带中点，且两侧都要有足够内容
        if s >= 0.02 * sh and (y1 - y0) - e >= 0.02 * sh:
            if best is None or ln > best[0]:
                best = (ln, "h", (s + e) // 2)
    for s, e, ln in _gaps(colp, cband, 0.02):
        if s >= 0.02 * sw and (x1 - x0) - e >= 0.02 * sw:
            if best is None or ln > best[0]:
                best = (ln, "v", (s + e) // 2)

    if best is None:
        return [rect]
    _, axis, pos = best
    if axis == "h":
        a = [x0, y0, x1, y0 + pos]
        b = [x0, y0 + pos, x1, y1]
    else:
        a = [x0, y0, x0 + pos, y1]
        b = [x0 + pos, y0, x1, y1]
    return xy_cut(mask, a, sw, sh, depth + 1) + xy_cut(mask, b, sw, sh, depth + 1)


def tighten(mask, rect):
    """把块收到真正的内容包围盒（去掉切分留下的空白）。"""
    x0, y0, x1, y1 = rect
    sub = mask[y0:y1, x0:x1]
    if not sub.any():
        return None
    rows = np.where(sub.any(axis=1))[0]
    cols = np.where(sub.any(axis=0))[0]
    return [x0 + int(cols[0]), y0 + int(rows[0]),
            x0 + int(cols[-1]) + 1, y0 + int(rows[-1]) + 1]


def box_dist(a, b):
    ax, ay = (a[0] + a[2]) / 2, (a[1] + a[3]) / 2
    bx, by = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5


def _merge_same_product(boxes, min_ov=0.5):
    """只把「同一台产品的零件」并起来：要求两块在某一轴上**显著重叠**。

    ⚠️ 这里不能用 cluster_boxes 的「包围盒相碰就并」——
      实测印刷页 35 两台梯桶的包围盒在 y 上有 11px（2.4%）重叠，
      按"相碰即并"会被重新并成一块（area=0.57 又回来了）。
      同一台产品的零件（梯子+桶身、桶身+底座）在某一轴上重叠通常 >50%，
      两台对角摆放的产品则两个轴都几乎不重叠 —— 用重叠率就能区分。
    """
    out = [list(b) for b in boxes]
    changed = True
    while changed:
        changed = False
        for i in range(len(out)):
            for j in range(i + 1, len(out)):
                a, b = out[i], out[j]
                ow = min(a[2], b[2]) - max(a[0], b[0])
                oh = min(a[3], b[3]) - max(a[1], b[1])
                xov = ow / max(1, min(a[2] - a[0], b[2] - b[0])) if ow > 0 else 0.0
                yov = oh / max(1, min(a[3] - a[1], b[3] - b[1])) if oh > 0 else 0.0
                if xov >= min_ov or yov >= min_ov:
                    out[i] = [min(a[0], b[0]), min(a[1], b[1]),
                              max(a[2], b[2]), max(a[3], b[3]), a[4] + b[4]]
                    out.pop(j)
                    changed = True
                    break
            if changed:
                break
    return out


def split_leaf_by_components(mask, rect, sw, sh, min_frac=0.03):
    """XY-cut 切不开时的兜底：块内连通域 + 显著重叠聚簇。

    ⭐ 为什么必须有这个函数（实测踩到）：
      画册存在**对角摆放**的两台产品 —— 印刷页 35（文件 p36.webp）的两台金属梯桶，
      一台在右上、一台在左下。两块之间既没有整行空白带、也没有整列空白带，
      XY-cut 按定义就切不开，必然返回整块（实测 area=0.570，被质量闸拦下）。
      连通域不受「整行/整列」的限制，天然能分开对角两块。

    min_frac 用来滤掉残留文字块（该页第二台的标题 OCR 没识别到，没框可擦）。
    """
    x0, y0, x1, y1 = rect
    sub = mask[y0:y1, x0:x1]
    if not sub.any():
        return [rect]
    h, w = sub.shape
    boxes = [b for b in connected_boxes(sub, min_px=6)
             if (b[2] - b[0]) * (b[3] - b[1]) >= min_frac * w * h]
    if len(boxes) <= 1:
        return [rect]
    cl = _merge_same_product(boxes)
    if len(cl) <= 1:
        return [rect]
    parts = [[x0 + int(c[0]), y0 + int(c[1]), x0 + int(c[2]) + 1, y0 + int(c[3]) + 1]
             for c in cl]
    return sorted(parts, key=lambda r: (round(r[1] / sh, 2), r[0]))


def merge_to_count(rects, n, sw, sh, mask=None):
    """把块数调整到 n：多了靠合并；**少了靠连通域拆**（mask 必须传才能拆）。"""
    rects = list(rects)

    # ① 先补足：XY-cut 少给时，挑最大的块尝试按连通域拆开
    guard = 0
    while mask is not None and len(rects) < n and guard < 40:
        guard += 1
        order = sorted(range(len(rects)),
                       key=lambda i: -((rects[i][2] - rects[i][0]) *
                                       (rects[i][3] - rects[i][1])))
        for i in order:
            parts = split_leaf_by_components(mask, rects[i], sw, sh)
            if len(parts) > 1:
                rects[i:i + 1] = parts
                break
        else:
            break

    # ② 再合并
    while len(rects) > n:
        bi = bj = None
        bd = None
        for i in range(len(rects)):
            for j in range(i + 1, len(rects)):
                # 只合并水平/垂直相邻的，避免把对角两块并成一个巨框
                d = box_dist(rects[i], rects[j])
                a, b = rects[i], rects[j]
                overlap_x = min(a[2], b[2]) - max(a[0], b[0])
                overlap_y = min(a[3], b[3]) - max(a[1], b[1])
                if max(overlap_x, overlap_y) <= 0:
                    d *= 3.0          # 对角：重罚
                if bd is None or d < bd:
                    bd, bi, bj = d, i, j
        a, b = rects[bi], rects[bj]
        rects[bi] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
        rects.pop(bj)
    return rects


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", default="33,34,35")
    ap.add_argument("--family", default="")
    ap.add_argument("--outdir", default="/tmp/crop_proto")
    ap.add_argument("--all", action="store_true", help="处理所有有型号记录的页")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    images = json.load(open(os.path.join(DATA, "catalog_images_20261001.json")))
    by_page = {i["page"]: i for i in images}
    ocr = json.load(open(os.path.join(DATA, "catalog_pilates_ocr.json")))
    models = json.load(open(os.path.join(DATA, "catalog_pilates_models_v2.json")))
    if args.family:
        models = [m for m in models if args.family in m["series"]]
    m_by_page = {}
    for m in models:
        m_by_page.setdefault(m["page"], []).append(m)

    pages = sorted(m_by_page) if args.all else [int(x) for x in args.pages.split(",") if x.strip()]
    report = {}
    for pg in pages:
        if pg not in m_by_page or pg not in by_page:
            print(f"page {pg}: 跳过（无型号记录或缺图）")
            continue
        info = by_page[pg]
        src = os.path.join(SRC_DIR, info["src"])
        if not os.path.exists(src):
            print(f"page {pg}: 源图缺失 {src}")
            continue
        img = Image.open(src).convert("RGB")
        pw, ph = img.size
        texts = ocr.get(str(pg), [])
        mask = build_mask(img, texts)
        leaves = xy_cut(mask, [0, 0, mask.shape[1], mask.shape[0]], mask.shape[1], mask.shape[0])
        total = mask.shape[0] * mask.shape[1]
        leaves = [t for t in (tighten(mask, r) for r in leaves) if t]
        leaves = [r for r in leaves if (r[2] - r[0]) * (r[3] - r[1]) >= MIN_LEAF_AREA * total]

        ms = sorted(m_by_page[pg], key=lambda m: (round(m["y"], 2), m["x"]))
        leaves = merge_to_count(leaves, len(ms), mask.shape[1], mask.shape[0], mask=mask)
        leaves = sorted(leaves, key=lambda r: (round((r[1] + r[3]) / 2 / mask.shape[0], 2),
                                               (r[0] + r[2]) / 2 / mask.shape[1]))

        vis = img.copy()
        dr = ImageDraw.Draw(vis)
        sx, sy = pw / mask.shape[1], ph / mask.shape[0]
        print(f"--- page {pg}  ({len(leaves)} 块 / {len(ms)} 型号)")
        for m, r in zip(ms, leaves):
            px0 = max(0, int(r[0] * sx - CROP_PAD * pw))
            py0 = max(0, int(r[1] * sy - CROP_PAD * ph))
            px1 = min(pw, int(r[2] * sx + CROP_PAD * pw))
            py1 = min(ph, int(r[3] * sy + CROP_PAD * ph))
            dr.rectangle([px0, py0, px1, py1], outline=(0, 140, 255), width=6)
            dr.text((px0 + 10, py0 + 10), m["model"], fill=(200, 0, 0))
            name = f"{slug(m['model'])}.png"
            img.crop((px0, py0, px1, py1)).save(os.path.join(args.outdir, name))
            print(f"    {m['model']:<22} -> {name:<28} {px1-px0}x{py1-py0}")
            report[slug(m["model"])] = name
        vis.resize((pw // 2, ph // 2)).save(os.path.join(args.outdir, f"page{pg}_boxes.png"))
    json.dump(report, open(os.path.join(args.outdir, "_map.json"), "w"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
