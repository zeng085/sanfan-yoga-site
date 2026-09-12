#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精确判定第三批候选是否已被本站收录 —— 用 md5 而非感知哈希。

原理：assets/img/ 下的图全部由 dl_batch_images.py 从英文站同一 URL 下载，
经 Pillow「最长边 900 + WebP q75 method=5」转码落盘。
用**完全相同的流程**重新下载候选图，若 md5 命中站内已有文件，即为同一张素材。

产出：outputs/第三批精确覆盖.json
  {slug: {"total": N, "hit": k, "hit_files": [...]}}
  hit/total 高 = 该单品的素材已在站上（被家族页或另一页用过）
"""
import concurrent.futures as cf
import hashlib
import io
import json
import os
import urllib.parse
import urllib.request

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
TMP = "/tmp/probe_b3_md5"
MAX_EDGE, Q = 900, 75

CAT = {c["slug"]: c for c in json.load(
    open(os.path.join(ROOT, "outputs", "sf_catalog_full.json"), encoding="utf-8"))}
CAND = json.load(open(os.path.join(ROOT, "outputs", "第三批待上线.json"), encoding="utf-8"))["missing"]
# 只处理有真规格的
SLUGS = [r["slug"] for r in CAND
         if any(v and not k.startswith("X:")
                for k, v in CAT.get(r["slug"], {}).get("specs", {}).items())]


def fetch(url):
    req = urllib.request.Request(urllib.parse.quote(url, safe="/:?=&%"),
                                 headers={"User-Agent": UA,
                                          "Referer": "https://www.sanfansport.com/"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def one(args):
    slug, k, url = args
    d = os.path.join(TMP, slug)
    os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, f"{k}.webp")
    if os.path.exists(dst) and os.path.getsize(dst) > 1024:
        return slug, k, open(dst, "rb").read()
    try:
        raw = fetch(url)
        im = Image.open(io.BytesIO(raw))
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGB")
        if max(im.size) > MAX_EDGE:
            im.thumbnail((MAX_EDGE, MAX_EDGE), Image.LANCZOS)
        im.save(dst, "WEBP", quality=Q, method=5)
        return slug, k, open(dst, "rb").read()
    except Exception as e:                                       # noqa: BLE001
        return slug, k, f"ERR {type(e).__name__}".encode()


def main():
    os.makedirs(TMP, exist_ok=True)
    jobs = [(s, k, u) for s in SLUGS
            for k, u in enumerate(CAT[s]["images"], 1)]
    print(f"候选 {len(SLUGS)} 个 / 待下载 {len(jobs)} 张")

    data = {}
    with cf.ThreadPoolExecutor(8) as ex:
        for slug, k, blob in ex.map(one, jobs):
            data.setdefault(slug, {})[k] = blob

    # 站内已有图 md5 索引
    imgdir = os.path.join(ROOT, "assets", "img")
    idx = {}
    for f in sorted(os.listdir(imgdir)):
        if f.endswith(".webp"):
            h = hashlib.md5(open(os.path.join(imgdir, f), "rb").read()).hexdigest()
            idx.setdefault(h, []).append(f)
    print(f"站内已索引 {len(idx)} 个唯一文件\n")

    out, rows = {}, []
    for s in SLUGS:
        tot = len(data.get(s, {}))
        hits = []
        for k, blob in sorted(data.get(s, {}).items()):
            if isinstance(blob, bytes) and not blob.startswith(b"ERR"):
                h = hashlib.md5(blob).hexdigest()
                if h in idx:
                    hits.append(idx[h][0])
        out[s] = {"total": tot, "hit": len(hits), "files": hits}
        rows.append((s, tot, len(hits), hits[:3]))

    print(f"  {'英文站 slug':36s} {'图':>4s} {'命中':>4s}  命中样例")
    for s, tot, n, ex_ in sorted(rows, key=lambda r: -(r[2] / max(r[1], 1))):
        ratio = n / max(tot, 1)
        flag = "🔴已收录" if ratio >= 0.5 else ("🟡部分" if n else "🟢全新")
        print(f"  {s:36s} {tot:4d} {n:4d}  {flag}  {', '.join(ex_)}")

    json.dump(out, open(os.path.join(ROOT, "outputs", "第三批精确覆盖.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    fresh = [s for s in SLUGS if out[s]["hit"] / max(out[s]["total"], 1) < 0.5]
    print(f"\n全新（命中率<50%）：{len(fresh)} 个")
    json.dump(fresh, open(os.path.join(ROOT, "outputs", "第三批全新清单.json"), "w",
                          encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
