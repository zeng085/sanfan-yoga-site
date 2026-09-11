#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用「边缘一圈」判定缩略图能否融入卡片（比只看四角准）。

渲染条件：.ct-thumbs a 底色 = --paper #f9f7f2，img object-fit:contain + multiply。
contain 会完整显示整张图，所以只需判断**图片四条边的颜色**：
  · 有透明像素        → 露出格子底色 → 融入
  · 边缘 multiply 后与米色差 ≤8 → 融入
  · 否则              → 显示为色块（不融入）

同时给出每张问题图在同款图集里的最佳替代。
用法: python i18n_build/edge_bg_test.py
"""
import glob, json, os, re, statistics, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "assets", "img")
PAPER = (249, 247, 242)
TOL = 8          # multiply 后与米色的可接受通道差


def edge_stats(path):
    """返回 (中位边缘色, 透明像素占比, multiply 后与米色的最大通道差)"""
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    b = max(2, int(min(w, h) * 0.035))
    x0, x1 = int(w * 0.10), int(w * 0.90)
    y0, y1 = int(h * 0.10), int(h * 0.90)
    strips = [im.crop((x0, 0, x1, b)), im.crop((x0, h - b, x1, h)),
              im.crop((0, y0, b, y1)), im.crop((w - b, y0, w, y1))]
    px = []
    for s in strips:
        px += list(s.getdata())
    alphas = [p[3] for p in px]
    trans = sum(1 for a in alphas if a < 250) / len(alphas)
    op = [p for p in px if p[3] >= 250]
    if not op:
        return (255, 255, 255), trans, 0
    med = tuple(round(statistics.median(p[c] for p in op)) for c in range(3))
    diff = max(abs(med[c] * PAPER[c] / 255 - PAPER[c]) for c in range(3))
    return med, trans, diff


def verdict(path):
    med, trans, diff = edge_stats(path)
    if trans > 0.5:
        return True, f"透明底 {trans*100:.0f}%", med, diff
    ok = diff <= TOL
    return ok, ("融入" if ok else f"色块 Δ{diff:.0f}"), med, diff


def best_alt(cur_name):
    slug = re.sub(r"-\d+[a-z]?\.webp$", "", cur_name)
    cands = [os.path.basename(p) for p in glob.glob(os.path.join(IMG, slug + "-*.webp"))]
    scored = []
    for f in cands:
        if f == cur_name or re.search(r"-\d+w\.webp$", f):
            continue
        ok, note, med, diff = verdict(os.path.join(IMG, f))
        scored.append((diff, f, ok, note))
    scored.sort(key=lambda x: x[0])
    return scored


def main():
    html = open(os.path.join(ROOT, "products.html"), encoding="utf-8").read()
    bad = []
    print("按分类卡逐格判定（边缘一圈）：\n")
    for t in re.split(r'<div class="cat-tile">', html)[1:]:
        name = re.search(r'<h3>.*?lang-en">([^<]+)<', t, re.S)
        name = name.group(1) if name else "?"
        tb = re.search(r'<div class="ct-thumbs">(.*?)</div>', t, re.S)
        if not tb:
            continue
        srcs = [os.path.basename(s) for s in re.findall(r'<img src="([^"]+)"', tb.group(1))]
        print(f"■ {name}")
        for i, f in enumerate(srcs, 1):
            ok, note, med, diff = verdict(os.path.join(IMG, f))
            print(f"   {'OK ' if ok else 'BAD'} {i}. {f:44s} 边缘中位色={str(med):18s} {note}")
            if not ok:
                bad.append({"tile": name, "idx": i, "file": f, "diff": round(diff, 1)})
        print()

    print("=" * 72)
    print(f"不融入的 {len(bad)} 张，逐张找替代：\n")
    plan = []
    for b in bad:
        print(f"■ {b['tile']} #{b['idx']} {b['file']}  (Δ{b['diff']})")
        alts = best_alt(b["file"])
        good = [a for a in alts if a[2]]
        for diff, f, ok, note in alts[:4]:
            print(f"     {'✔' if ok else '✘'} {f:44s} Δ{diff:5.1f}  {note}")
        if good:
            # 选 Δ 最小且产品主体最大的（用文件序号靠前优先）
            pick = sorted(good, key=lambda x: (x[0], x[1]))[0][1]
            print(f"   → 选 {pick}\n")
            plan.append({"tile": b["tile"], "idx": b["idx"], "cur": b["file"], "new": pick,
                         "oldDiff": b["diff"]})
        else:
            print(f"   → ⚠️ 同款无更优候选\n")

    json.dump(plan, open(os.path.join(ROOT, "outputs", "plan", "缩略图换图计划.json"),
                         "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"可替换 {len(plan)}/{len(bad)} 张 → outputs/plan/缩略图换图计划.json")


if __name__ == "__main__":
    main()
