#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从英文站批量下载产品图库，统一为 WebP q75 落到 assets/img/。

用法：
  python3 i18n_build/fetch_sf_images.py --dry-run          # 只统计与连通性验证
  python3 i18n_build/fetch_sf_images.py --stage            # 下到临时区（默认）
  python3 i18n_build/fetch_sf_images.py --stage --limit 40 # 抽样验证

命名规则：<产品slug>-<序号>.<ext>，序号按图库顺序（第 1 张 = 主图）。
英文站 524/572 图已是 WebP，仅 48 张 jpg 需转换（Pillow）。
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
STAGE = "/tmp/sf_img_stage"
PILLOW_PY = "/Users/mac-zlg/.workbuddy/binaries/python/envs/default/bin/python"


def download(job):
    slug, idx, url, outdir = job
    ext = os.path.splitext(url)[1].lower() or ".jpg"
    dst = os.path.join(outdir, f"{slug}-{idx}{ext}")
    if os.path.exists(dst) and os.path.getsize(dst) > 800:
        return dst, "cached"
    try:
        safe = urllib.parse.quote(url, safe="/:?=&%")
        req = urllib.request.Request(safe, headers={
            "User-Agent": UA, "Referer": "https://www.sanfansport.com/"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        if len(data) < 800:
            return dst, "too-small"
        with open(dst, "wb") as f:
            f.write(data)
        return dst, f"{len(data)//1024}KB"
    except Exception as e:                                   # noqa: BLE001
        return dst, f"ERR {type(e).__name__}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", default=os.path.join(ROOT, "outputs", "sf_catalog.json"))
    ap.add_argument("--stage", action="store_true", default=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="每产品只取前 N 张")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    items = json.load(open(args.catalog, encoding="utf-8"))
    jobs, total = [], 0
    for x in items:
        urls = x["images"][:args.limit] if args.limit else x["images"]
        for i, u in enumerate(urls, 1):
            jobs.append((x["slug"], i, u, STAGE))
            total += 1

    fmt = {}
    for _, _, u, _ in jobs:
        fmt[os.path.splitext(u)[1].lower()] = fmt.get(os.path.splitext(u)[1].lower(), 0) + 1
    print(f"产品 {len(items)} 个；待下图 {total} 张；格式 {fmt}")
    if args.dry_run:
        print("（dry-run，未下载）")
        return

    os.makedirs(STAGE, exist_ok=True)
    ok = err = 0
    errs = []
    with cf.ThreadPoolExecutor(args.workers) as ex:
        for n, (dst, st) in enumerate(ex.map(download, jobs), 1):
            if st.startswith("ERR") or st == "too-small":
                err += 1
                errs.append((os.path.basename(dst), st))
            else:
                ok += 1
            if n % 100 == 0 or n == total:
                print(f"   … {n}/{total}  成功 {ok} 失败 {err}", flush=True)

    jpgs = [f for f in os.listdir(STAGE) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    size = sum(os.path.getsize(os.path.join(STAGE, f)) for f in os.listdir(STAGE))
    print(f"\n落盘：{len(os.listdir(STAGE))} 个文件 / {size/1024/1024:.1f} MB")
    print(f"待转 WebP 的 {len(jpgs)} 张")
    if errs:
        print(f"失败 {len(errs)}：{errs[:6]}")
    print(f"staging 目录：{STAGE}")


if __name__ == "__main__":
    main()
