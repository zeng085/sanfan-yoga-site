#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 products.html 分类卡缩略图（.ct-thumbs）里的「有色底」素材换成同款的白底素材。

背景：
  · 大图卡（.ct-img / .prod-card / .range-card）按用户要求保留英文站原始素材（含有色底）
  · 但 .ct-thumbs 是 3×2 密排小图网格，对底色一致性极敏感：
    白底图会被 mix-blend-mode:multiply 融进卡片米色，有色底图则显示为色块 → "有的有边框有的没有"
  · 所以只对缩略图这一处，换用同款图集里边缘最干净的那张（Δ = 边缘 multiply 后与卡片色的最大通道差）

判定与选图见 edge_bg_test.py。本脚本只改 .ct-thumbs 内部的 <img src>，绝不碰大图。

用法: python i18n_build/fix_ct_thumbs.py [--dry]
"""
import glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from edge_bg_test import IMG, TOL, verdict  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXTRA = ["de", "ja", "ko", "fr", "it", "es"]
# 只改缩略图网格，且 a 标签直接包 img（ct-thumbs 的形态）
CT_RE = re.compile(r'(<div class="ct-thumbs">)(.*?)(</div>)', re.S)
IMG_RE = re.compile(r'(<img src=")([^"]+)(")')


def best_for(fname):
    """同款图集里 Δ 最小的那张（不设阈值：即使达不到完美也取最优，改善总是好的）。"""
    slug = re.sub(r"-\d+[a-z]?\.webp$", "", fname)
    cands = [os.path.basename(p) for p in glob.glob(os.path.join(IMG, slug + "-*.webp"))]
    scored = []
    for f in cands:
        if f == fname or re.search(r"-\d+w\.webp$", f):
            continue
        _, _, _, diff = verdict(os.path.join(IMG, f))
        scored.append((diff, f))
    if not scored:
        return None, None
    scored.sort()
    return scored[0][1], scored[0][0]


def build_map():
    """{旧文件: (新文件, 旧Δ, 新Δ)}"""
    html = open(os.path.join(ROOT, "products.html"), encoding="utf-8").read()
    m = {}
    for block in CT_RE.findall(html):
        for _, src, _ in IMG_RE.findall(block[1]):
            f = os.path.basename(src)
            if f in m:
                continue
            ok, _, _, diff = verdict(os.path.join(IMG, f))
            if ok or diff <= TOL:
                continue
            new, newdiff = best_for(f)
            # 只在确实更优时才换：有的款同款图集里全是场景照，换了反而更差
            if new and newdiff < diff:
                m[f] = (new, round(diff, 1), round(newdiff, 1))
    return m


def main():
    dry = "--dry" in sys.argv
    m = build_map()
    print(f"需要处理的缩略图 {len(m)} 张\n")
    print(f"{'旧素材':46s} {'Δ旧':>6s} → {'新素材':46s} {'Δ新':>6s}")
    for old, (new, d0, d1) in sorted(m.items(), key=lambda x: -x[1][1]):
        flag = "✔" if d1 <= TOL else ("~" if d1 < d0 * 0.7 else "✘")
        print(f"{old:46s} {d0:6.1f} → {new:46s} {d1:6.1f} {flag}")

    if dry:
        print("\n[dry] 未写入")
        return

    total = 0
    for rel in ["products.html"] + [f"{d}/products.html" for d in EXTRA]:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            print(f"  跳过 {rel}（不存在）")
            continue
        html = open(p, encoding="utf-8").read()
        hits = [0]

        def fix_block(mo):
            head, inner, tail = mo.groups()

            def fix_img(im):
                pre, src, post = im.groups()
                f = os.path.basename(src)
                if f in m:
                    hits[0] += 1
                    return pre + src.replace(f, m[f][0]) + post
                return im.group(0)

            return head + IMG_RE.sub(fix_img, inner) + tail

        new = CT_RE.sub(fix_block, html)
        if hits[0]:
            open(p, "w", encoding="utf-8").write(new)
            total += hits[0]
        print(f"  {rel:26s} {hits[0]:>3d} 处")

    print(f"\n共替换 {total} 处缩略图（大图未动）")


if __name__ == "__main__":
    main()
