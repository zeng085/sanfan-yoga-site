#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把「一台产品一张图」的裁切结果导出成站点可用的 webp。

依赖 crop_catalog_products_20261001 的分割逻辑，额外做三件事：
  1. 导出两种尺寸：正文图（最长边 880）与方形缩略图（320×320，白底居中留白）
  2. **质量闸**：裁图长宽比异常 / 面积占比异常 的，直接标红，不静默通过
     （画册各页版式不一，自动切块必然有失手；宁可少出图，不可出错图）
  3. 输出 _report.json，供后续注入 HTML 时读

用法：
  python export_pilates_model_images_20261001.py --family 梯桶 --out assets/img/pilates-models
  python export_pilates_model_images_20261001.py --all --out /tmp/x --dry-run
"""
import argparse
import json
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crop_catalog_products_20261001 as CR  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

# 质量闸阈值
MIN_AREA, MAX_AREA = 0.015, 0.30     # 占页面面积比
MIN_AR, MAX_AR = 0.40, 2.20          # 长宽比
BODY_MAX = 880
SQ = 320
SQ_PAD = 0.10


def square_pad(im: Image.Image, size: int, pad: float) -> Image.Image:
    canvas = Image.new("RGB", (size, size), (255, 255, 255))
    inner = int(size * (1 - 2 * pad))
    w, h = im.size
    s = min(inner / w, inner / h)
    im2 = im.resize((max(1, int(w * s)), max(1, int(h * s))), Image.LANCZOS)
    canvas.paste(im2, ((size - im2.width) // 2, (size - im2.height) // 2))
    return canvas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", default="")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--out", default="/tmp/pilates_model_imgs")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    images = json.load(open(os.path.join(DATA, "catalog_images_20261001.json")))
    by_page = {i["page"]: i for i in images}
    ocr = json.load(open(os.path.join(DATA, "catalog_pilates_ocr.json")))
    models = json.load(open(os.path.join(DATA, "catalog_pilates_models_v2.json")))
    if args.family:
        models = [m for m in models if args.family in m["series"]]

    m_by_page = {}
    for m in models:
        m_by_page.setdefault(m["page"], []).append(m)

    if not args.dry_run:
        os.makedirs(args.out, exist_ok=True)

    report, flagged = {}, []
    for pg in sorted(m_by_page):
        info = by_page.get(pg)
        if not info:
            continue
        src = os.path.join(CR.SRC_DIR, info["src"])
        if not os.path.exists(src):
            print(f"page {pg}: 源图缺失，跳过")
            continue
        img = Image.open(src).convert("RGB")
        pw, ph = img.size
        mask = CR.build_mask(img, ocr.get(str(pg), []))
        sh, sw = mask.shape
        total = sh * sw
        leaves = CR.xy_cut(mask, [0, 0, sw, sh], sw, sh)
        leaves = [t for t in (CR.tighten(mask, r) for r in leaves) if t]
        leaves = [r for r in leaves if (r[2] - r[0]) * (r[3] - r[1]) >= CR.MIN_LEAF_AREA * total]
        ms = sorted(m_by_page[pg], key=lambda m: (round(m["y"], 2), m["x"]))
        leaves = CR.merge_to_count(leaves, len(ms), sw, sh, mask=mask)
        leaves = sorted(leaves, key=lambda r: (round((r[1] + r[3]) / 2 / sh, 2),
                                               (r[0] + r[2]) / 2 / sw))
        for m, r in zip(ms, leaves):
            area = (r[2] - r[0]) * (r[3] - r[1]) / total
            ar = (r[2] - r[0]) / max(1, (r[3] - r[1]))
            slug = CR.slug(m["model"])
            ok = MIN_AREA <= area <= MAX_AREA and MIN_AR <= ar <= MAX_AR
            tag = "OK " if ok else "!! "
            print(f"{tag}p{pg:<3} {m['model']:<24} area={area:.3f} ar={ar:.2f}")
            if not ok:
                flagged.append({"page": pg, "model": m["model"],
                                "area": round(area, 4), "ar": round(ar, 2)})
            sx, sy = pw / sw, ph / sh
            x0 = max(0, int(r[0] * sx - CR.CROP_PAD * pw))
            y0 = max(0, int(r[1] * sy - CR.CROP_PAD * ph))
            x1 = min(pw, int(r[2] * sx + CR.CROP_PAD * pw))
            y1 = min(ph, int(r[3] * sy + CR.CROP_PAD * ph))
            crop = img.crop((x0, y0, x1, y1))
            crop, n_erased = CR.erase_text(crop, (x0, y0, x1, y1),
                                           ocr.get(str(pg), []))
            crop, n_stray = CR.erase_strays(crop)
            n_erased += n_stray
            body = crop.copy()
            if body.width > BODY_MAX:
                body = body.resize((BODY_MAX, int(body.height * BODY_MAX / body.width)),
                                   Image.LANCZOS)
            sq = square_pad(crop, SQ, SQ_PAD)
            report[slug] = {
                "model": m["model"], "page": pg, "suspect": m.get("suspect") or [],
                "source": info["file"], "box": [x0, y0, x1, y1],
                "body": f"{slug}.webp", "thumb": f"{slug}-sq.webp",
                "size": [body.width, body.height], "ok": ok,
                "text_erased": n_erased,
            }
            if not args.dry_run:
                body.save(os.path.join(args.out, f"{slug}.webp"),
                          "WEBP", quality=84, method=6)
                sq.save(os.path.join(args.out, f"{slug}-sq.webp"),
                        "WEBP", quality=86, method=6)

    print(f"\n共 {len(report)} 台；质量闸拦下 {len(flagged)} 台需要人工核对：")
    for f in flagged:
        print(f"   p{f['page']} {f['model']}  area={f['area']} ar={f['ar']}")
    if not args.dry_run:
        json.dump({"report": report, "flagged": flagged},
                  open(os.path.join(args.out, "_crop_report.json"), "w"),
                  ensure_ascii=False, indent=1)
        print("已写入", args.out)


if __name__ == "__main__":
    main()
