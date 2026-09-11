#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按英文站图库重写产品页的 .pd-gallery（主图 + 全部缩略图），并同步
og:image / twitter:image / JSON-LD image，再把全站指向该页的卡片首图换成新主图。

背景（2026-09-11 全面体检）
---------------------------
- 新页（第一批 56 + 第二批 40）由 build_batchN.py 生成时被 `MAX_IMAGES = 8` 截断，
  英文站同款最多 39 张 → 本脚本按英文站全量补齐。
- 老页 fi/fr/pr/rb 图集只有 1 张 → 一并按英文站对应产品同步。
- two-tone-double-layer-tpe-yoga-mat（计划内漏页）、ym2（用户拍板用英文站图）同批处理。

图片文件命名：`<本地页slug>-<k>.webp`，k=1..N，顺序 = 英文站图库原序。
（由 i18n_build/dl_batch_images.py 下载并转 WebP）

幂等：重复执行结果一致。

用法：
    python3 i18n_build/sync_page_images.py --dry-run
    python3 i18n_build/sync_page_images.py --only foam-roller,fr1
    python3 i18n_build/sync_page_images.py --all
"""
import argparse
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
LANGS = ["", "de", "ja", "ko", "fr", "it", "es"]
SITE = "https://fjsanfan.com"

CAT = {c["slug"]: c for c in json.load(open("outputs/sf_catalog_full.json", encoding="utf-8"))}

# 本地 slug -> 英文站 slug（与 dl_batch_images.py 保持一致）
MAP = {}
for f in ("outputs/batch1_pages.json", "outputs/batch2_pages.json"):
    for p in json.load(open(f, encoding="utf-8")):
        MAP[p["new"]] = p["src"]
MAP.update({
    "fr1": "foam-roller-2", "fr2": "foam-roller", "fr3": "vibrating-yoga-roller",
    "fr4": "eva-foam-roller", "fr5": "fascial-sphere-1",
    "pr1": "yoga-hammock", "pr3": "yoga-bolster", "pr4": "eva-yoga-block",
    "rb1": "exercise-bands", "rb2": "yoga-ball",
    "fi2": "kettlebell-2", "fi3": "jump-rope-2", "fi5": "dumbbell-2",
    "fi4": "stair-climbers-3",
    "ym2": "tpe-yoga-mat-4",
})

try:
    from PIL import Image
except Exception:                                  # noqa: BLE001
    Image = None


def _size_nopil(p):
    try:
        with open(p, "rb") as fh:
            head = fh.read(40)
        if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
            fmt = head[12:16]
            if fmt == b"VP8 ":
                return (int.from_bytes(head[26:28], "little") & 0x3FFF,
                        int.from_bytes(head[28:30], "little") & 0x3FFF)
            if fmt == b"VP8L":
                bits = int.from_bytes(head[21:26], "little")
                return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
            if fmt == b"VP8X":
                return (int.from_bytes(head[24:27], "little") + 1,
                        int.from_bytes(head[27:30], "little") + 1)
    except Exception:                              # noqa: BLE001
        pass
    return 0, 0


def dims(p):
    if Image:
        try:
            return Image.open(p).size
        except Exception:                          # noqa: BLE001
            pass
    return _size_nopil(p)


def files_for(local):
    """按 assets/img/<local>-<k>.webp 连续取（直到断号）"""
    out = []
    k = 1
    while True:
        p = os.path.join(ROOT, "assets/img", f"{local}-{k}.webp")
        if not os.path.exists(p):
            break
        out.append(f"{local}-{k}.webp")
        k += 1
        if k > 60:
            break
    return out


def build_gallery(files, depth, alt, sizes):
    thumbs = "\n".join(
        '<button type="button" class="pd-thumb%s"><img src="%sassets/img/%s" width="%d" height="%d" '
        'loading="lazy" alt="%s"></button>' % (" active" if i == 0 else "", depth, f,
                                               sizes[i][0] or 800, sizes[i][1] or 800, alt)
        for i, f in enumerate(files))
    return (
        '<div class="pd-gallery">\n'
        '<div class="pd-main"><img id="pd-main-img" src="%sassets/img/%s" width="%d" height="%d" alt="%s" /></div>\n'
        '<div class="pd-thumbs" id="pd-thumbs">\n%s\n</div>\n'
        '</div>\n' % (depth, files[0], sizes[0][0] or 800, sizes[0][1] or 800, alt, thumbs))


def patch_page(p, files, sizes, dry):
    t = open(p, encoding="utf-8").read()
    rel = os.path.relpath(p, ROOT)
    depth = "../../" if rel.count(os.sep) == 2 else "../"
    notes = []

    m = re.search(r'<div class="pd-gallery">[\s\S]*?(?=<div class="pd-info">)', t)
    if not m:
        # 老页可能是 <section class="pd-gallery"> 之外的结构
        m = re.search(r'<div class="pd-gallery">[\s\S]*?</div>\s*</div>\s*</div>', t)
    if not m:
        return t, ["!! 未找到 pd-gallery 段"]
    alt_m = re.search(r'id="pd-main-img"[^>]*alt="([^"]*)"', m.group(0))
    alt = alt_m.group(1) if alt_m else ""
    new = build_gallery(files, depth, alt, sizes)
    if new.strip() == m.group(0).strip():
        return t, ["图集已是目标状态"]
    t = t[:m.start()] + new + t[m.end():]
    notes.append(f"图集 → {len(files)} 张")

    n = [0]

    def _og(mm):
        n[0] += 1
        return f'{mm.group(1)}{SITE}/assets/img/{files[0]}"'
    t = re.sub(r'(<meta (?:property="og:image"|name="twitter:image") content=")'
               + re.escape(SITE) + r'/assets/img/[^"]+"', _og, t)
    if n[0]:
        notes.append(f"og/twitter → {files[0]}（{n[0]} 处）")

    def _ld(mm):
        inner = ",\n    ".join(json.dumps(f"{SITE}/assets/img/{f}") for f in files)
        return re.sub(r'"image":\s*\[[\s\S]*?\]', '"image": [\n    ' + inner + "\n   ]", mm.group(0), count=1)
    t2 = re.sub(r'<script type="application/ld\+json">[\s\S]*?</script>', _ld, t)
    if t2 != t:
        notes.append(f"JSON-LD image → {len(files)} 张")
        t = t2
    return t, notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", default="", help="逗号分隔本地 slug")
    ap.add_argument("--all", action="store_true", help="处理 MAP 里全部页面")
    ap.add_argument("--no-cards", action="store_true", help="不改列表/首页卡片图")
    a = ap.parse_args()

    only = {x.strip() for x in a.only.split(",") if x.strip()}
    targets = sorted(only) if only else (sorted(MAP) if a.all else [])

    print("=== 1/2 产品页图集 + OG + JSON-LD ===")
    changed = 0
    plan = {}
    for local in targets:
        en = MAP.get(local)
        c = CAT.get(en or "")
        if not c:
            print(f"  ! {local}: 映射缺失（{en}），跳过"); continue
        files = files_for(local)
        need = len(c.get("images") or [])
        if not files:
            print(f"  ! {local}: assets/img 无 {local}-N.webp，跳过"); continue
        if len(files) < need:
            print(f"  ~ {local}: 英文站 {need} 张，本地只有 {len(files)} 张（按本地已有的处理）")
        sizes = [dims(os.path.join(ROOT, "assets/img", f)) for f in files]
        plan[local] = {"files": files, "sizes": sizes}
        hit = 0
        for lang in LANGS:
            p = os.path.join(ROOT, f"{lang}/products/{local}.html" if lang else f"products/{local}.html")
            if not os.path.exists(p):
                continue
            t, notes = patch_page(p, files, sizes, a.dry_run)
            cur = open(p, encoding="utf-8").read()
            if t != cur:
                hit += 1
                if not a.dry_run:
                    open(p, "w", encoding="utf-8").write(t)
                print(f"  [{lang or 'root':4s}] {local:44s} " + " | ".join(notes))
        if hit == 0:
            print(f"  [ --  ] {local:44s} 已是目标状态（{len(files)} 张）")
        changed += hit
    print(f"  → 改动页面 {changed} 个")

    if a.no_cards or not plan:
        if a.dry_run:
            print("\n[DRY-RUN] 未写入任何文件")
        return

    print("\n=== 2/2 全站卡片首图 ===")
    pages = [p for p in glob.glob("**/*.html", recursive=True)
             if not p.startswith(("outputs/", "i18n_build/", ".git/"))]
    card_re = re.compile(r'<a [^>]*href="((?:\.\./)*(?:products/)?)([a-z0-9-]+)\.html"[^>]*>([\s\S]*?)</a>')
    total, touched = 0, set()
    for p in pages:
        t = open(p, encoding="utf-8").read()
        orig = t
        cnt = [0]

        def _card(mm):
            pre, slug, body = mm.group(1), mm.group(2), mm.group(3)
            if slug not in plan:
                return mm.group(0)
            new = plan[slug]["files"][0]
            w, h = plan[slug]["sizes"][0]
            nb, k = re.subn(
                r'(src="(?:\.\./)*assets/img/)[^"]+(")([^>]*?)(width=")\d+(")([^>]*?)(height=")\d+(")',
                lambda g: f'{g.group(1)}{new}{g.group(2)}{g.group(3)}{g.group(4)}{w or 800}{g.group(5)}{g.group(6)}{g.group(7)}{h or 800}{g.group(8)}',
                body, count=1)
            if k == 0:
                nb, k = re.subn(r'(src="(?:\.\./)*assets/img/)[^"]+(")',
                                lambda g: f'{g.group(1)}{new}{g.group(2)}', body, count=1)
            if k:
                cnt[0] += 1
                return mm.group(0)[:mm.start(3) - mm.start(0)] + nb + mm.group(0)[mm.end(3) - mm.start(0):]
            return mm.group(0)

        t = card_re.sub(_card, t)
        if t != orig:
            if not a.dry_run:
                open(p, "w", encoding="utf-8").write(t)
            total += cnt[0]
            touched.add(p)
    print(f"  → 替换卡片图 {total} 处，涉及 {len(touched)} 个文件")
    for f in sorted(touched)[:14]:
        print("     ", f)
    if a.dry_run:
        print("\n[DRY-RUN] 未写入任何文件")


if __name__ == "__main__":
    main()
