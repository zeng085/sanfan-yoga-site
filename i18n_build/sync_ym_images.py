#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把老页 ym1/ym3/ym4/ym5/ym6 的产品图同步成英文站对应产品的图库。

背景
----
老页 ym1~ym7 是早期自建的产品页，图集非常单薄（ym4/ym5/ym6 只有 1 张主图），
而英文站 sanfansport.com 同款产品各有 6~13 张实拍图。用户要求「我们之前上的品
的信息也要替换成英文站的」→ 图片一并同步。

图片源：outputs/ym_image_download.json（Playwright 同源 fetch 下载的英文站原图）
已有产物：assets/img/ym{N}-{k}.webp（已转 WebP q75，最大边 900）

本脚本做三件事（幂等）
--------------------
1. 重建 {lang}/products/ymN.html 的 `.pd-gallery` 图集段（主图 + 全部缩略图）
2. 同步同页的 og:image / twitter:image / JSON-LD `image` 数组
3. 全站所有指向该产品的卡片（`<a class="prod-card" href=".../products/ymN.html">`）
   的图换成 ymN-1.webp

注意
----
- **不覆盖任何现有图文件**（tpe-mat-1.webp 之类仍被 og:image / range-card /
  post-card 当通用图用，保留原样，避免误伤）
- 7 个语言版本一起改：图片是跨语言共用的，只改 EN 会导致语言站图集不一致
- ym2 不在范围内（英文站加宽 TPE 只有木林森客户品牌款，待用户拍板）
- ym7 的文件名不是 `ym7-N.webp` 而是 `camouflage-tpe-mat-N.webp`（改名时换的图），
  由 FILES_OVERRIDE 指定；alt 相应按语言覆盖（原 alt 还写着 PU/CamoPU 旧名）

用法
----
    python3 i18n_build/sync_ym_images.py --dry-run
    python3 i18n_build/sync_ym_images.py
"""
import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LANGS = ["", "de", "ja", "ko", "fr", "it", "es"]
SITE = "https://fjsanfan.com"

# ym → 英文站 slug（与 outputs/ym_image_download.json 一致）
MAP = {
    "ym1": "tpe-yoga-mat",
    "ym3": "tpe-double-yoga-mat",
    "ym4": "folding-mat",
    "ym5": "pu-rubber-yoga-mat",
    "ym6": "matte-pu-rubber-yoga-mat",
    "ym7": "pu-rubber-yoga-mat-test",
}

# 文件名不走 ymN-K 规律的页（ym7 改名时换成了迷彩图，图文件是 camouflage-tpe-mat-N）
FILES_OVERRIDE = {
    "ym7": ["camouflage-tpe-mat-%d.webp" % i for i in range(1, 7)],
}

# alt 覆盖：仅对指定页生效。ym7 改名换图后，语言站 alt 仍残留 PU / CamoPU 旧名，需按语言覆盖
ALT = {
    "ym7": {
        "": "TPE Camouflage Yoga Mat",
        "de": "TPE-Yogamatte mit Tarnmuster",
        "ja": "TPE迷彩柄ヨガマット",
        "ko": "TPE 카모 요가 매트",
        "fr": "Tapis de yoga TPE camouflage",
        "it": "Tappetino da yoga TPE mimetico",
        "es": "Esterilla de yoga TPE de camuflaje",
    },
}


def load_plan(dry):
    """从 outputs/ym_image_download.json + assets/img 实际文件算出每页的图清单。"""
    rec = json.loads((ROOT / "outputs/ym_image_download.json").read_text(encoding="utf-8"))
    from PIL import Image
    plan = {}
    for ym, slug in MAP.items():
        if ym in FILES_OVERRIDE:
            names = FILES_OVERRIDE[ym]
            missing = [n for n in names if not (ROOT / "assets/img" / n).exists()]
            if missing:
                print(f"  ! {ym}: 缺图 {missing}", file=sys.stderr)
                names = [n for n in names if n not in missing]
        else:
            names = [p.name for p in sorted(
                (ROOT / "assets/img").glob(f"{ym}-*.webp"),
                key=lambda p: int(re.search(r"-(\d+)\.webp$", p.name).group(1)),
            )]
            src_n = len([f for f in rec[ym]["files"] if f])
            if len(names) != src_n:
                print(f"  ! {ym}: 已入站 {len(names)} 张，下载记录 {src_n} 张 — 不一致", file=sys.stderr)
        size = Image.open(ROOT / "assets/img" / names[0]).size
        sizes = [Image.open(ROOT / "assets/img" / n).size for n in names]
        plan[ym] = {"slug": slug, "files": names, "size": size, "sizes": sizes}
        print(f"  {ym} ← {slug:26s} {len(names):2d} 张  首图 {size[0]}x{size[1]}")
    return plan


def build_gallery(files, depth, alt, sizes):
    """重建 .pd-gallery 段。主图不 lazy（首屏），缩略图 lazy。每张图用各自真实尺寸。"""
    thumbs = "\n".join(
        '<button type="button" class="pd-thumb%s"><img src="%sassets/img/%s" width="%d" height="%d" '
        'loading="lazy" alt="%s"></button>' % (" active" if i == 0 else "", depth, f, sizes[i][0], sizes[i][1], alt)
        for i, f in enumerate(files)
    )
    return (
        '<div class="pd-gallery">\n'
        '<div class="pd-main"><img id="pd-main-img" src="%sassets/img/%s" width="%d" height="%d" alt="%s" /></div>\n'
        '<div class="pd-thumbs" id="pd-thumbs">\n%s\n</div>\n'
        '</div>\n' % (depth, files[0], sizes[0][0], sizes[0][1], alt, thumbs)
    )


def patch_page(p, ym, spec, dry):
    """改一个页面的图集 + OG/Twitter + JSON-LD。返回 (改动说明列表)"""
    t = p.read_text(encoding="utf-8")
    orig = t
    notes = []
    rel = p.relative_to(ROOT)
    depth = "../../" if len(rel.parts) == 3 else "../"
    lang = "" if len(rel.parts) == 2 else rel.parts[0]

    files = spec["files"]
    sizes = spec.get("sizes") or [spec["size"]] * len(files)

    # ---- 1) 图集段重建 ----
    m = re.search(r'<div class="pd-gallery">[\s\S]*?(?=<div class="pd-info">)', t)
    if not m:
        notes.append("!! 未找到 pd-gallery 段")
        return t, notes
    alt_m = re.search(r'id="pd-main-img"[^>]*alt="([^"]*)"', m.group(0))
    alt = ALT.get(ym, {}).get(lang) or (alt_m.group(1) if alt_m else "")
    t = t[:m.start()] + build_gallery(files, depth, alt, sizes) + t[m.end():]
    notes.append(f"图集 → {len(files)} 张" + (f", alt→'{alt}'" if ym in ALT else ""))

    # ---- 2) OG / Twitter ----
    n = 0
    def _og(mm):
        nonlocal n
        n += 1
        return f'{mm.group(1)}{SITE}/assets/img/{files[0]}"'
    t = re.sub(r'(<meta (?:property="og:image"|name="twitter:image") content=")' + re.escape(SITE) + r'/assets/img/[^"]+"', _og, t)
    if n:
        notes.append(f"og/twitter → {files[0]}（{n} 处）")

    # ---- 3) JSON-LD image ----
    def _ld(mm):
        body = mm.group(0)
        inner = ",\n    ".join(json.dumps(f"{SITE}/assets/img/{f}") for f in files)
        return re.sub(r'"image":\s*\[[\s\S]*?\]', '"image": [\n    ' + inner + "\n   ]", body, count=1)
    t2 = re.sub(r'<script type="application/ld\+json">[\s\S]*?</script>', _ld, t)
    if t2 != t:
        notes.append(f"JSON-LD image → {len(files)} 张")
        t = t2

    return t, notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print("图片清单：")
    plan = load_plan(args.dry_run)

    print("\n=== 1/2 老页自身（图集 + OG + JSON-LD）===")
    changed_pages = 0
    for ym, spec in plan.items():
        for lang in LANGS:
            p = ROOT / (f"{lang}/products/{ym}.html" if lang else f"products/{ym}.html")
            if not p.exists():
                print(f"  ! 缺失 {p.relative_to(ROOT)}")
                continue
            t, notes = patch_page(p, ym, spec, args.dry_run)
            if t != p.read_text(encoding="utf-8"):
                changed_pages += 1
                if not args.dry_run:
                    p.write_text(t, encoding="utf-8")
                print(f"  [{lang or 'root':4s}] {ym} : " + " | ".join(notes))
    print(f"  → 改页面 {changed_pages} 个")

    print("\n=== 2/2 全站指向这些产品的卡片图 ===")
    pages = [
        p for p in ROOT.rglob("*.html")
        if not any(x in p.parts for x in ("outputs", ".git", "i18n_build", "node_modules"))
    ]
    # 通用：所有指向 ymN 的链接块。站内有 3 套卡片结构（products.html 的
    # `prod-card`、首页的 `g-item`、老页「相关产品」的 `prod-card`），
    # 且根站写 `products/ym1.html`、语言站写同目录的 `ym1.html` —— 统一按 href 匹配。
    card_re = re.compile(r'<a [^>]*href="((?:\.\./)*(?:products/)?)(ym\d)\.html"[^>]*>([\s\S]*?)</a>')
    total = 0
    touched = set()
    for p in pages:
        t = p.read_text(encoding="utf-8")
        orig = t
        cnt = [0]

        def _card(mm):
            pre, ym, body = mm.group(1), mm.group(2), mm.group(3)
            if ym not in plan:
                return mm.group(0)
            new = plan[ym]["files"][0]
            w, h = plan[ym]["size"]
            nb, k = re.subn(
                r'(src="(?:\.\./)*assets/img/)[^"]+(")([^>]*?)(width=")\d+(")([^>]*?)(height=")\d+(")',
                lambda g: f'{g.group(1)}{new}{g.group(2)}{g.group(3)}{g.group(4)}{w}{g.group(5)}{g.group(6)}{g.group(7)}{h}{g.group(8)}',
                body, count=1,
            )
            if k == 0:
                nb, k = re.subn(r'(src="(?:\.\./)*assets/img/)[^"]+(")', lambda g: f'{g.group(1)}{new}{g.group(2)}', body, count=1)
            if k:
                cnt[0] += 1
                return f'{mm.group(0)[:mm.start(3)-mm.start(0)]}{nb}{mm.group(0)[mm.end(3)-mm.start(0):]}'
            return mm.group(0)

        t = card_re.sub(_card, t)
        if t != orig:
            if not args.dry_run:
                p.write_text(t, encoding="utf-8")
            total += cnt[0]
            touched.add(str(p.relative_to(ROOT)))
    print(f"  → 替换卡片图 {total} 处，涉及 {len(touched)} 个文件")
    for f in sorted(touched)[:12]:
        print("     ", f)
    if len(touched) > 12:
        print(f"      ... 另 {len(touched)-12} 个")

    if args.dry_run:
        print("\n[DRY-RUN] 未写入任何文件")


if __name__ == "__main__":
    main()
