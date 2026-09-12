#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
判断第三批候选是否被本站已有页（尤其是家族页 pr1/fi2/fi3/fi4/fi5）覆盖。

做法：下载候选英文站 slug 的**首图**，与 assets/img/ 下全部已有图片做 dHash 比对。
命中 = 该单品的素材已在本站某页上 → 视为已覆盖，不再新建页。

用法：
  python3 i18n_build/probe_coverage.py --dry     # 只下载首图并列出 URL
  python3 i18n_build/probe_coverage.py           # 下载 + 比对
"""
import argparse
import concurrent.futures as cf
import io
import json
import os
import urllib.parse
import urllib.request

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
TMP = "/tmp/probe_b3"
CAT = {c["slug"]: c for c in json.load(
    open(os.path.join(ROOT, "outputs", "sf_catalog_full.json"), encoding="utf-8"))}

# 第三批里有真规格的 29 个 + 需要一并判定的家族相关 slug
CANDIDATES = [
    "ab-roller", "ab-roller-2", "ab-roller-set", "fitness-board", "p3-fitness-board",
    "barbell", "cordless-jump-rope", "dumbbell", "dumbbell-2",
    "electronic-counting-skip-rope", "jump-rope-2", "jump-rope-3", "jump-rope-kids",
    "kettlebell-2", "smart-counting-jump-rope", "speed-jump-rope", "weighted-ball",
    "weighted-ring", "wrist-weights", "stair-climbers", "stair-climbers-2",
    "stair-climbers-3", "gradient-color-yoga-hammock", "solid-color-yoga-hammock",
    "yoga-hammock", "yoga-hammock-3", "yoga-hammock-4", "yoga-hammock-5",
    "yoga-hammock-with-handles",
]


def dhash(path_or_bytes, size=8):
    im = Image.open(path_or_bytes if hasattr(path_or_bytes, "read") else io.BytesIO(path_or_bytes))
    im = im.convert("L").resize((size + 1, size), Image.LANCZOS)
    px = list(im.getdata())
    bits = 0
    for r in range(size):
        for c in range(size):
            bits = (bits << 1) | (1 if px[r * (size + 1) + c] < px[r * (size + 1) + c + 1] else 0)
    return bits


def ham(a, b):
    return bin(a ^ b).count("1")


def fetch(url):
    req = urllib.request.Request(urllib.parse.quote(url, safe="/:?=&%"),
                                 headers={"User-Agent": UA,
                                          "Referer": "https://www.sanfansport.com/"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def job(slug):
    dst = os.path.join(TMP, slug + ".img")
    if os.path.exists(dst) and os.path.getsize(dst) > 800:
        return slug, "cached"
    imgs = CAT.get(slug, {}).get("images") or []
    if not imgs:
        return slug, "no-image"
    try:
        raw = fetch(imgs[0])
        open(dst, "wb").write(raw)
        return slug, f"{len(raw)//1024}KB"
    except Exception as e:                                       # noqa: BLE001
        return slug, f"ERR {type(e).__name__}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    os.makedirs(TMP, exist_ok=True)

    print("=== 1) 下载候选首图 ===")
    with cf.ThreadPoolExecutor(8) as ex:
        for slug, st in ex.map(job, CANDIDATES):
            print(f"  {slug:36s} {st}")

    if a.dry:
        return

    print("\n=== 2) 建立本站已有图片 dHash 索引 ===")
    imgdir = os.path.join(ROOT, "assets", "img")
    index = []
    for f in sorted(os.listdir(imgdir)):
        if not f.endswith(".webp"):
            continue
        try:
            index.append((dhash(open(os.path.join(imgdir, f), "rb").read()), f))
        except Exception:                                        # noqa: BLE001
            pass
    print(f"  已索引 {len(index)} 张本地图")

    print("\n=== 3) 比对：候选首图 vs 本站已有图 ===")
    print(f"  {'英文站 slug':36s} {'最相似本站图':44s} 距离")
    result = {}
    for slug in CANDIDATES:
        p = os.path.join(TMP, slug + ".img")
        if not os.path.exists(p):
            print(f"  {slug:36s} (无首图)")
            result[slug] = None
            continue
        try:
            h = dhash(open(p, "rb").read())
        except Exception as e:                                   # noqa: BLE001
            print(f"  {slug:36s} 解析失败 {e}")
            result[slug] = None
            continue
        best = min(index, key=lambda x: ham(h, x[0]))
        d = ham(h, best[0])
        result[slug] = (best[1], d)
        flag = "✅已覆盖" if d <= 12 else ("⚠️接近" if d <= 20 else "🆕全新")
        print(f"  {slug:36s} {best[1]:44s} {d:3d}  {flag}")

    json.dump({k: v for k, v in result.items()},
              open(os.path.join(ROOT, "outputs", "第三批覆盖探测.json"), "w",
                   encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n✅ outputs/第三批覆盖探测.json")


if __name__ == "__main__":
    main()
