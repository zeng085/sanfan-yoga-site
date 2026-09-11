#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
unify_card_bg.py —— 产品卡首图「底色统一」工具

问题：列表页卡片图用 object-fit:cover 铺满 1:1 容器，图片自带底色 → 卡片底色。
      白底单品图与彩色底/实景底图并排时视觉割裂。

两条治本路径：
  A. 换图：同一产品图集里若存在白底原图，优先用作首图（画质无损，首选）
  B. 换底：图集里没有白底原图时，用「边缘连通」算法把图片外圈的纯色背景抹成白色
     —— 只替换与图像边缘相连、且颜色接近边缘中位色的像素，产品内部同色部分不受影响

用法：
  python i18n_build/unify_card_bg.py scan             # 全站卡片底色体检，输出报告
  python i18n_build/unify_card_bg.py strip [--all]    # 换底：默认只处理「彩色块底」，
                                                      # --all 连「照片/实景底」一起试
  python i18n_build/unify_card_bg.py split <file>     # 单张对比图（原图 vs 换底）

产物：
  outputs/卡片底色体检-<日期>.json     分类明细
  outputs/card_bg_white/<原文件名>     换底后的白底图（不动原资产）
"""
import argparse, json, os, re, statistics, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS = os.path.join(ROOT, "outputs", "product_cards.json")
OUTDIR = os.path.join(ROOT, "outputs", "card_bg_white")


# ---------- 图像分析 ----------
def edge_stats(path, size=240, band=5):
    """返回 (边缘白像素占比, 边缘色标准差, 边缘中位色)。用于判定图片底色类型。"""
    import numpy as np
    from PIL import Image
    im = Image.open(path).convert("RGB").resize((size, size))
    px = im.load()
    W, H = im.size
    pts = [px[x, y] for x in range(W) for y in list(range(band)) + list(range(H - band, H))]
    pts += [px[x, y] for y in range(H) for x in list(range(band)) + list(range(W - band, W))]
    n = len(pts)
    wr = sum(1 for p in pts if min(p) >= 238) / n
    rs = [p[0] for p in pts]; gs = [p[1] for p in pts]; bs = [p[2] for p in pts]
    sd = max(statistics.pstdev(rs), statistics.pstdev(gs), statistics.pstdev(bs))
    med = (int(statistics.median(rs)), int(statistics.median(gs)), int(statistics.median(bs)))
    return round(wr, 3), round(sd, 1), med


def classify(wr, sd):
    if wr >= 0.35:
        return "白底"
    return "色块底" if sd < 14 else "照片/实景底"


def gallery(slug):
    """从产品页 pd-gallery 区块提取图集图片（相对仓库根）。"""
    p = os.path.join(ROOT, "products", f"{slug}.html")
    if not os.path.exists(p):
        return []
    h = open(p, encoding="utf-8").read()
    i = h.find("pd-gallery"); j = h.find("pd-info")
    seg = h[i:j] if (i >= 0 and j > i) else h
    out = []
    for s in re.findall(r'src="([^"]*assets/img/[^"]+)"', seg):
        s = s.replace("../", "")
        if s not in out:
            out.append(s)
    return out


# ---------- 换底 ----------
def strip_bg(src, dst, tol=32, feather=1.4, quality=90):
    """边缘连通换底：把与图像边缘相连、颜色接近边缘中位色的区域替换为纯白。
    返回被替换面积占比（覆盖率，越低说明背景越少/越复杂）。"""
    import numpy as np
    from PIL import Image, ImageFilter
    im = Image.open(src).convert("RGB")
    a = np.asarray(im).astype(np.int16)
    H, W, _ = a.shape
    b = max(2, min(H, W) // 200)
    edge = np.concatenate([a[:b].reshape(-1, 3), a[-b:].reshape(-1, 3),
                           a[:, :b].reshape(-1, 3), a[:, -b:].reshape(-1, 3)])
    bg = np.median(edge, axis=0)
    near = np.sqrt(((a - bg) ** 2).sum(axis=2)) < tol
    mask = np.zeros((H, W), bool)
    mask[:1] = near[:1]; mask[-1:] = near[-1:]
    mask[:, :1] = near[:, :1]; mask[:, -1:] = near[:, -1:]
    for _ in range(6000):                      # 从四边向内传播
        g = mask.copy()
        g[1:] |= mask[:-1]; g[:-1] |= mask[1:]
        g[:, 1:] |= mask[:, :-1]; g[:, :-1] |= mask[:, 1:]
        g &= near
        if g.sum() == mask.sum():
            break
        mask = g
    cov = float(mask.mean())
    al = np.asarray(Image.fromarray((mask * 255).astype(np.uint8))
                    .filter(ImageFilter.GaussianBlur(feather))).astype(np.float32) / 255.0
    white = np.full_like(a, 255, dtype=np.float32)
    out = (a * (1 - al[..., None]) + white * al[..., None]).clip(0, 255).astype(np.uint8)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    Image.fromarray(out).save(dst, quality=quality, method=6)
    return round(cov, 3)


# ---------- 命令 ----------
def load_cards():
    if not os.path.exists(CARDS):
        sys.exit(f"缺少卡片池 {CARDS}")
    return json.load(open(CARDS, encoding="utf-8"))


def cmd_scan(_):
    cards = load_cards()
    buckets = {"白底": [], "色块底": [], "照片/实景底": []}
    for slug, html in cards.items():
        m = re.search(r'<img src="([^"]+)"', html)
        if not m:
            continue
        src = m.group(1)
        path = os.path.join(ROOT, src)
        if not os.path.exists(path):
            buckets.setdefault("缺失", []).append(slug)
            continue
        wr, sd, med = edge_stats(path)
        rec = {"slug": slug, "img": os.path.basename(src), "wr": wr, "sd": sd, "bg": med}
        if wr < 0.35:                           # 非白底 → 找同族白底候选
            cands = []
            for g in gallery(slug):
                gp = os.path.join(ROOT, g)
                if not os.path.exists(gp) or g == src:
                    continue
                w2, s2, _ = edge_stats(gp)
                if w2 >= 0.45 and s2 < 30:      # 白底且非实景照（实景 sd 高）
                    cands.append({"file": os.path.basename(g), "wr": w2, "sd": s2})
            rec["white_candidates"] = cands
        buckets[classify(wr, sd)].append(rec)
    total = sum(len(v) for v in buckets.values())
    print(f"卡片首图 {total} 张 → " + " | ".join(f"{k} {len(v)}" for k, v in buckets.items() if v))
    for k in ("色块底", "照片/实景底"):
        for r in buckets.get(k, []):
            swap = ("可换白底原图：" + r["white_candidates"][0]["file"]) if r.get("white_candidates") else "无白底候选 → 需换底"
            print(f"  [{k}] {r['slug']:44s} bg={r['bg']} {swap}")
    out = os.path.join(ROOT, "outputs", f"卡片底色体检-{datetime.date.today()}.json")
    json.dump(buckets, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n报告 → {os.path.relpath(out, ROOT)}")


def cmd_strip(args):
    cards = load_cards()
    rows = []
    for slug, html in cards.items():
        m = re.search(r'<img src="([^"]+)"', html)
        if not m:
            continue
        src = m.group(1)
        path = os.path.join(ROOT, src)
        if not os.path.exists(path):
            continue
        wr, sd, med = edge_stats(path)
        cls = classify(wr, sd)
        if cls == "白底" or (cls != "色块底" and not args.all):
            continue
        dst = os.path.join(OUTDIR, os.path.basename(src))
        cov = strip_bg(path, dst)
        rows.append({"slug": slug, "file": os.path.basename(src), "cls": cls, "covered": cov})
        print(f"  ✓ {slug:44s} {cls} 抹白比例={cov}")
    ok = [r for r in rows if 0.12 <= r["covered"] <= 0.95]
    print(f"\n处理 {len(rows)} 张，其中覆盖率落在安全区间(12%~95%)的 {len(ok)} 张。")
    print(f"输出目录 → {os.path.relpath(OUTDIR, ROOT)}  （原资产未改动，人工目视后再落地）")
    json.dump(rows, open(os.path.join(ROOT, "outputs", "card_bg_strip_rows.json"), "w",
                         encoding="utf-8"), ensure_ascii=False, indent=1)


def cmd_split(args):
    from PIL import Image
    f = args.file
    path = f if os.path.isabs(f) else os.path.join(ROOT, f)
    tmp = "/tmp/_split_out.webp"
    strip_bg(path, tmp)
    a = Image.open(path).convert("RGB"); b = Image.open(tmp).convert("RGB")
    S = 460
    canvas = Image.new("RGB", (S * 2 + 12, S), "white")
    canvas.paste(a.resize((S, S)), (0, 0)); canvas.paste(b.resize((S, S)), (S + 12, 0))
    dst = os.path.join(ROOT, "outputs", "card_bg_split.png")
    canvas.save(dst)
    print(f"左=原图 右=换底后 → {os.path.relpath(dst, ROOT)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("scan").set_defaults(fn=cmd_scan)
    sp = sub.add_parser("strip"); sp.add_argument("--all", action="store_true"); sp.set_defaults(fn=cmd_strip)
    sq = sub.add_parser("split"); sq.add_argument("file"); sq.set_defaults(fn=cmd_split)
    ns = ap.parse_args()
    ns.fn(ns)
