#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量下载英文站产品图并转 WebP 入 assets/img（幂等）。

覆盖四类需求（2026-09-11 全面体检后）：
  1. 补齐新页图集：新页此前被 build_batchN.py 的 MAX_IMAGES=8 截断，
     英文站同款最多 39 张 → 取全量
  2. 老页图集同步：fr1-5 / pr1,3,4 / rb1,2 / fi1-5（fi1 无源，见下）
  3. two-tone 补页（计划内漏页）
  4. ym2 同步（用户拍板：用英文站 tpe-yoga-mat-4 的 8 张，含木林森水印）

命名：<本地页slug>-<k>.webp，k 从 1 起，顺序 = 英文站图库原序（第 1 张即主图）。
幂等：目标文件已存在且 >1KB 则跳过，可反复执行。

用法：
    python3 i18n_build/dl_batch_images.py --dry-run
    python3 i18n_build/dl_batch_images.py --only ym2,fr1
    python3 i18n_build/dl_batch_images.py
"""
import argparse
import concurrent.futures as cf
import hashlib
import io
import json
import os
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
MAX_EDGE = 900
Q = 75

CAT = {c["slug"]: c for c in json.load(open("outputs/sf_catalog_full.json", encoding="utf-8"))}

# ---- 新页：本地 slug -> 英文站 slug ----
NEW = {}
for f in ("outputs/batch1_pages.json", "outputs/batch2_pages.json"):
    for p in json.load(open(f, encoding="utf-8")):
        NEW[p["new"]] = p["src"]

# ---- 老页手工映射（依据规格逐项核对，见 outputs/老页英文站映射核对-2026-09-11.md）----
OLD = {
    "fr1": "foam-roller-2",         # EVA+PVC 狼牙面，30/33/45cm 命中
    "fr2": "foam-roller",           # Solid EVA，33/45cm 命中
    "fr3": "vibrating-yoga-roller",  # PU+ABS 31×10cm，Vibrating+Rechargeable 命中
    "fr4": "eva-foam-roller",       # EVA，34×12.5/33×13.5/52×12 命中
    "fr5": "fascial-sphere-1",      # EVA/TPE Ø6/7/7.5/10cm，Fascia Ball 命中
    "pr1": "yoga-hammock",          # Polyester 4–8m，5×2.7m 命中
    "pr3": "yoga-bolster",          # 550g bolster，64×24×13 命中
    "pr4": "eva-yoga-block",        # EVA 23×15×7.5cm 命中
    "rb1": "exercise-bands",        # TPE 1500×150×0.45mm 命中
    "rb2": "yoga-ball",             # Anti-burst PVC Ø25/55/65/75 命中
    "fi2": "kettlebell-2",          # silicone bag kettlebell 4500g 命中
    "fi3": "jump-rope-2",           # rope 3m / handle 命中
    "fi5": "dumbbell-2",            # Silicone 1–2.5kg 命中（同族 barbell 另见报告）
    "fi4": "stair-climbers-3",      # 白色立式踏步机，与 fi4 现图同款（目视核对）
    # fi1（迷你踏步机）英文站无对应产品 → 无源，不下载、建议下掉
}

# ---- 单独指定 ----
EXTRA = {
    "two-tone-double-layer-tpe-yoga-mat": "tpe-double-yoga-mat",   # 计划内漏页（9 张）
    "ym2": "tpe-yoga-mat-4",                                       # 用户拍板用带木林森水印图（8 张）
}

TASKS = {}
TASKS.update({k: v for k, v in NEW.items()})
TASKS.update(OLD)
TASKS.update(EXTRA)


def fetch_img(url):
    req = urllib.request.Request(urllib.parse.quote(url, safe="/:?=&%"),
                                 headers={"User-Agent": UA,
                                          "Referer": "https://www.sanfansport.com/"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def job(args):
    local, en_slug, k, url = args
    dst = os.path.join(ROOT, "assets/img", f"{local}-{k}.webp")
    if os.path.exists(dst) and os.path.getsize(dst) > 1024:
        return dst, "cached"
    try:
        raw = fetch_img(url)
        if len(raw) < 800:
            return dst, "too-small"
        from PIL import Image
        im = Image.open(io.BytesIO(raw))
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGB")
        if max(im.size) > MAX_EDGE:
            im.thumbnail((MAX_EDGE, MAX_EDGE), Image.LANCZOS)
        im.save(dst, "WEBP", quality=Q, method=5)
        return dst, f"{os.path.getsize(dst)//1024}KB {im.size[0]}x{im.size[1]}"
    except Exception as e:                                        # noqa: BLE001
        return dst, f"ERR {type(e).__name__} {str(e)[:60]}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", default="", help="逗号分隔的本地 slug，只处理这些")
    ap.add_argument("--local-first", action="store_true",
                    help="只下 NEW 里本地的图（不铺老页）")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()

    only = {x.strip() for x in a.only.split(",") if x.strip()}
    jobs = []
    print("=== 下载计划 ===")
    for local, en_slug in sorted(TASKS.items()):
        if only and local not in only:
            continue
        if local not in NEW and local not in OLD and local not in EXTRA:
            continue
        c = CAT.get(en_slug)
        if not c:
            print(f"  ! {local}: 英文站 slug `{en_slug}` 不存在，跳过"); continue
        imgs = c.get("images") or []
        if not imgs:
            print(f"  ! {local}: 英文站无图，跳过"); continue
        have = sum(1 for k in range(1, len(imgs) + 1)
                   if os.path.exists(os.path.join(ROOT, "assets/img", f"{local}-{k}.webp")))
        tag = "补齐" if local in NEW else ("老页" if local in OLD else "专项")
        print(f"  [{tag}] {local:44s} ← {en_slug:28s} 英文站 {len(imgs):2d} 张，已有 {have:2d} 张")
        for k, u in enumerate(imgs, 1):
            jobs.append((local, en_slug, k, u))

    print(f"\n共 {len(jobs)} 个下载任务")
    if a.dry_run:
        print("[DRY-RUN] 未执行"); return

    ok = cached = err = 0
    errs = []
    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        for dst, msg in ex.map(job, jobs):
            if msg == "cached":
                cached += 1
            elif msg.startswith("ERR") or msg == "too-small":
                err += 1
                errs.append((os.path.basename(dst), msg))
            else:
                ok += 1
    print(f"\n下载完成：新增 {ok}，已存在 {cached}，失败 {err}")
    for n, m in errs[:20]:
        print("  !", n, m)
    if err:
        print("  （失败项可重跑本脚本，已存在的会跳过）")


if __name__ == "__main__":
    main()
