#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 sanfansport.com（英文站，权威源）批量下载产品图，转 WebP 后落到 assets/img/。

用法：
    python3 fetch_sf_images.py --list              # 只看有哪些产品、各多少张图
    python3 fetch_sf_images.py --slug tpe-yoga-mat # 只下某个产品
    python3 fetch_sf_images.py --all               # 全量（1586 张，约 40–60 分钟）
    python3 fetch_sf_images.py --check             # 只做连通性体检，不下图

前置：
    /tmp/sf_images.json  —— 由抓取脚本产出的 {slug: [图片URL, ...]}

注意：
    1. sanfansport.com 在 Cloudflare 后面。短时间大批量请求会被限流，
       表现为 curl 返回 000 / SSL UNEXPECTED_EOF。此时等待 10–30 分钟再跑。
    2. 本脚本默认 1.2 秒/张 + 失败退避重试，避免再次触发限流。
    3. 图片按 产品slug_序号.webp 命名；同名已存在则跳过（可断点续传）。
"""
import argparse, json, os, re, sys, time, urllib.request, urllib.error, ssl, io

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
HOST = "https://www.sanfansport.com"
MANIFEST = "/tmp/sf_images.json"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "img")
DELAY = 1.2          # 每张之间等待秒数
RETRY = 3            # 单张最多重试次数
MAX_W = 1200         # 最大宽度（原图多为 600–1000px，超过才缩）


def http_get(url, timeout=30, referer=None):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "image/avif,image/webp,image/png,image/jpeg,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": referer or (HOST + "/"),
    })
    ctx = ssl.create_default_context()
    return urllib.request.urlopen(req, timeout=timeout, context=ctx).read()


def check_connectivity():
    try:
        d = http_get(HOST + "/", timeout=20)
        print(f"连通正常（首页 {len(d)} 字节）")
        return True
    except Exception as e:
        print(f"连通失败：{type(e).__name__}: {str(e)[:120]}")
        print("→ 多为 Cloudflare 限流。等待 10–30 分钟后再试。")
        return False


def load_manifest():
    if not os.path.exists(MANIFEST):
        sys.exit(f"缺少清单文件 {MANIFEST}\n"
                 f"先跑抓取脚本生成，或用 --help 看说明。")
    return json.load(open(MANIFEST, encoding="utf-8"))


def target_name(slug, idx, url):
    ext = os.path.splitext(url)[1].lower().lstrip(".") or "jpg"
    base = re.sub(r"[^a-z0-9]+", "-", slug.lower()).strip("-")
    return f"{base}-{idx:02d}"


def save_webp(raw, out_path):
    try:
        from PIL import Image
    except ImportError:
        sys.exit("缺少 Pillow。请用托管 venv：\n"
                 "  /Users/mac-zlg/.workbuddy/binaries/python/envs/default/bin/python "
                 "fetch_sf_images.py ...")
    im = Image.open(io.BytesIO(raw))
    if im.mode in ("P", "RGBA", "LA"):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[-1])
        im = bg
    elif im.mode != "RGB":
        im = im.convert("RGB")
    if im.width > MAX_W:
        h = round(im.height * MAX_W / im.width)
        im = im.resize((MAX_W, h), Image.LANCZOS)
    im.save(out_path, "WEBP", quality=75, method=6)
    return im.size, os.path.getsize(out_path)


def fetch_one(slug, idx, url, out_dir, dry=False):
    name = target_name(slug, idx, url)
    if os.path.exists(os.path.join(out_dir, name)) and \
       os.path.exists(os.path.join(out_dir, name + ".webp")):
        return "skip", name, 0
    if dry:
        return "dry", name, 0
    last = None
    for attempt in range(RETRY):
        try:
            raw = http_get(url, referer=f"{HOST}/product/{slug}/")
            orig = os.path.join(out_dir, name + os.path.splitext(url)[1].lower())
            with open(orig, "wb") as f:
                f.write(raw)
            size, nbytes = save_webp(raw, os.path.join(out_dir, name + ".webp"))
            return "ok", f"{name}.webp {size[0]}x{size[1]} {nbytes // 1024}KB", nbytes
        except Exception as e:
            last = e
            time.sleep(3 * (attempt + 1))
    return "fail", f"{name} :: {type(last).__name__}: {str(last)[:80]}", 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--out", default=OUT_DIR)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.check:
        sys.exit(0 if check_connectivity() else 1)

    man = load_manifest()

    if args.list:
        tot = 0
        for slug in sorted(man):
            n = len(man[slug])
            tot += n
            print(f"  {slug:<45} {n:>3} 张")
        print(f"\n合计 {len(man)} 个产品 / {tot} 张图")
        return

    if args.slug:
        if args.slug not in man:
            sys.exit(f"清单里没有 {args.slug}")
        items = [(args.slug, man[args.slug])]
    elif args.all:
        items = [(s, man[s]) for s in sorted(man)]
    else:
        ap.print_help()
        return

    if not args.dry_run and not check_connectivity():
        sys.exit(1)

    os.makedirs(args.out, exist_ok=True)
    stats = {"ok": 0, "skip": 0, "fail": 0, "dry": 0}
    bytes_total = 0
    fails = []
    for slug, urls in items:
        print(f"\n=== {slug} ({len(urls)} 张) ===")
        for i, u in enumerate(urls, 1):
            status, msg, nb = fetch_one(slug, i, u, args.out, dry=args.dry_run)
            stats[status] += 1
            bytes_total += nb
            if status == "fail":
                fails.append(msg)
            print(f"  [{status}] {msg}")
            if status == "ok":
                time.sleep(DELAY)
    print(f"\n完成：成功 {stats['ok']} / 跳过 {stats['skip']} / 失败 {stats['fail']}")
    if bytes_total:
        print(f"新增体积：{bytes_total / 1e6:.1f} MB")
    if fails:
        print("\n失败清单：")
        for f in fails:
            print("  ", f)


if __name__ == "__main__":
    main()
