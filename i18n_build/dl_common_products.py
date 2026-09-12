#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""下载 6 个「品类通用款」的图片，并与站内已有素材做 md5 查重。

为什么单独跑一遍 md5：
  这 6 个是英文站的**空壳页**（content 空、0 条规格），不在此前 probe_md5.py 的候选里
  （那份只跑有真规格的 29 个）。所以「图集是否已被站内收录」没有历史结论，
  上线前必须自己验一次 —— 若 100% 命中，说明已被家族页吞掉，不该重复建页。

转码参数必须与站内素材完全一致（最长边 900 + WebP q75 method=5），
否则 md5 不可比。

产出：
  /tmp/probe_b4_common/<slug>/<k>.webp   转好的图（k=1 为英文站原序第一张）
  outputs/通用款图片查重.json             {slug: {total, hit, files, new}}
"""
import concurrent.futures as cf
import hashlib
import io
import json
import os
import time
import urllib.parse
import urllib.request

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
TMP = "/tmp/probe_b4_common"
MAX_EDGE, Q = 900, 75
PROXY = "https://images.weserv.nl/?url="
WORKERS = 4                      # weserv 有软限速，8 并发会吃 429

SLUGS = ["ab-wheel", "adjustable-dumbbell", "jump-rope",
         "kettlebell", "suspension-training", "vibration-machine"]

CAT = {c["slug"]: c for c in json.load(
    open(os.path.join(ROOT, "outputs", "sf_catalog_full.json"), encoding="utf-8"))}


def fetch(url):
    """英文站直连已被 Cloudflare IP 级限流（首页/图片全 HTTP 000，2026-09-12 起）。

    绕过方式：images.weserv.nl 图片代理。它在境外，能正常回源 sanfansport.com。
    ⚠️ 关键：**不传 w/h/output/q 等参数时该代理透传原图字节**，不做重编码 ——
    所以「Pillow 最长边900 + WebP q75」转码后的 md5 与站内素材依然可比（查重有效）。
    如果哪天加了 output=webp 之类的参数，md5 立刻失去可比性，别加。
    """
    host_path = url.split("://", 1)[1]
    req = urllib.request.Request(
        PROXY + urllib.parse.quote(host_path, safe="/:?=&%"),
        headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def one(args):
    slug, k, url = args
    d = os.path.join(TMP, slug)
    os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, f"{k}.webp")
    if os.path.exists(dst) and os.path.getsize(dst) > 1024:
        return slug, k, open(dst, "rb").read()
    last = ""
    for attempt in range(3):
        try:
            raw = fetch(url)
            im = Image.open(io.BytesIO(raw))
            if im.mode not in ("RGB", "RGBA"):
                im = im.convert("RGB")
            if max(im.size) > MAX_EDGE:
                im.thumbnail((MAX_EDGE, MAX_EDGE), Image.LANCZOS)
            im.save(dst, "WEBP", quality=Q, method=5)
            return slug, k, open(dst, "rb").read()
        except Exception as e:                                   # noqa: BLE001
            last = f"{type(e).__name__}: {e}"
            time.sleep(1.5 * (attempt + 1))
    return slug, k, f"ERR {last}".encode()


def main():
    os.makedirs(TMP, exist_ok=True)
    jobs = [(s, k, u) for s in SLUGS for k, u in enumerate(CAT[s]["images"], 1)]
    print(f"待下载 {len(jobs)} 张（{len(SLUGS)} 款）")

    data = {}
    with cf.ThreadPoolExecutor(WORKERS) as ex:
        for slug, k, blob in ex.map(one, jobs):
            data.setdefault(slug, {})[k] = blob

    err = [(s, k, b[:60]) for s in data for k, b in data[s].items()
           if isinstance(b, bytes) and b.startswith(b"ERR")]
    if err:
        for s, k, b in err:
            print("  ✗", s, k, b)
    print(f"成功 {len(jobs) - len(err)} / {len(jobs)}")

    imgdir = os.path.join(ROOT, "assets", "img")
    idx = {}
    for f in sorted(os.listdir(imgdir)):
        if f.endswith(".webp"):
            h = hashlib.md5(open(os.path.join(imgdir, f), "rb").read()).hexdigest()
            idx.setdefault(h, []).append(f)
    print(f"站内已索引 {len(idx)} 个唯一文件\n")

    out = {}
    for s in SLUGS:
        tot = len(data.get(s, {}))
        hits, fresh = [], []
        for k, blob in sorted(data.get(s, {}).items()):
            if not isinstance(blob, bytes) or blob.startswith(b"ERR"):
                continue
            h = hashlib.md5(blob).hexdigest()
            (hits if h in idx else fresh).append((k, idx[h][0] if h in idx else ""))
        ratio = len(hits) / max(tot, 1)
        out[s] = {"total": tot, "hit": len(hits),
                  "hit_files": [f for _, f in hits],
                  "fresh_k": [k for k, _ in fresh]}
        flag = "🔴已被收录" if ratio >= 0.5 else ("🟡部分重复" if hits else "🟢全新素材")
        print(f"  {s:24s} 共{tot:2d}张  重复{len(hits):2d}  新增{len(fresh):2d}  {flag}")
        for k, f in hits:
            print(f"       k={k} 撞 {f}")

    json.dump(out, open(os.path.join(ROOT, "outputs", "通用款图片查重.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    tot_new = sum(len(v["fresh_k"]) for v in out.values())
    print(f"\n可新增图片 {tot_new} 张 → outputs/通用款图片查重.json")


if __name__ == "__main__":
    main()
