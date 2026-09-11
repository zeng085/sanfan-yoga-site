#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成缩略图网格的「现状 vs 换图后」对比预览页（还原真实 CSS：米色卡 + multiply + cover）。"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPER, PAPER2 = "#f9f7f2", "#f2eee6"

# 候选替换（来自 scan_alternatives.py 的自动挑选 + 人工复核的最接近中性候选）
SWAP = {
    "ym3-1.webp": "ym3-9.webp",
    "alignment-line-tpe-yoga-mat-1.webp": "alignment-line-tpe-yoga-mat-2.webp",
    "ym5-1.webp": "ym5-3.webp",
    "arched-pu-rubber-yoga-mat-1.webp": "arched-pu-rubber-yoga-mat-2.webp",
    "gold-printed-pu-rubber-yoga-mat-1.webp": "gold-printed-pu-rubber-yoga-mat-2.webp",
    "pu-meditation-mat-set-1.webp": "pu-meditation-mat-set-2.webp",
    "fr3-1.webp": "fr3-3.webp",
    "circular-leg-clamps-1.webp": "circular-leg-clamps-5.webp",
    "figure-8-resistance-bands-1.webp": "figure-8-resistance-bands-2.webp",
    # 这两款同款图集里没有任何白底/中性候选，保持原图待定
    "advanced-yoga-roller-1.webp": "advanced-yoga-roller-1.webp",
    "pilates-reformer-mat-mandala-1.webp": "pilates-reformer-mat-mandala-1.webp",
}


def tiles():
    html = open(os.path.join(ROOT, "products.html"), encoding="utf-8").read()
    out = []
    for t in re.split(r'<div class="cat-tile">', html)[1:]:
        name = re.search(r'<h3>.*?lang-en">([^<]+)<', t, re.S)
        tb = re.search(r'<div class="ct-thumbs">(.*?)</div>', t, re.S)
        if not tb:
            continue
        srcs = [s.split("/")[-1] for s in re.findall(r'<img src="([^"]+)"', tb.group(1))]
        out.append((name.group(1) if name else "?", srcs))
    return out


def block(srcs, use_swap):
    h = ""
    for s in srcs:
        f = SWAP.get(s, s) if use_swap else s
        mark = " swap" if (use_swap and SWAP.get(s, s) != s) else ""
        h += f'<a class="th{mark}" href="#"><img src="file://{ROOT}/assets/img/{f}" alt="{f}"></a>\n'
    return h


def main():
    rows = ""
    for name, srcs in tiles():
        rows += f'''
<div class="tile">
  <h3>{name}</h3>
  <p class="kw">现状（原素材）</p>
  <div class="thumbs">{block(srcs, False)}</div>
  <p class="kw">换图后（白底/中性候选）</p>
  <div class="thumbs">{block(srcs, True)}</div>
</div>'''

    html = f'''<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>缩略图底色对比</title>
<style>
  body {{ background:#e8e6e0; font: 14px -apple-system, "PingFang SC", sans-serif; margin:0; padding:24px; }}
  .wrap {{ max-width:1180px; margin:0 auto; }}
  h1 {{ font-size:20px; margin:0 0 6px; color:#1d2b26; }}
  .lead {{ color:#5a6b64; margin:0 0 22px; font-size:13px; }}
  .grid {{ display:grid; grid-template-columns:1fr; gap:18px; }}
  .tile {{ background:{PAPER}; border-radius:6px; padding:16px 18px; }}
  .tile h3 {{ margin:0 0 10px; font-size:16px; font-weight:600; color:#1d2b26; }}
  .kw {{ margin:0 0 8px; color:#0f6b52; font-size:12px; font-weight:600; }}
  .thumbs {{ display:grid; grid-template-columns:repeat(6,1fr); gap:10px; margin-bottom:18px; max-width:760px; }}
  .thumbs a {{ display:block; aspect-ratio:1/1; border-radius:6px; overflow:hidden;
               background:{PAPER}; isolation:isolate; outline:1px dashed rgba(0,0,0,.10); }}
  .thumbs img {{ width:100%; height:100%; object-fit:cover; display:block; mix-blend-mode:multiply; }}
  .th.swap {{ outline:1px solid #0f6b52; }}
</style></head><body><div class="wrap">
<h1>缩略图底色：现状 vs 换图后</h1>
<p class="lead">橙色虚线 = 格子边界（仅预览用，实际页面没有）。绿框 = 该格换了图。真实渲染条件：卡片底色 #f9f7f2 + 图片 mix-blend-mode:multiply + object-fit:cover。</p>
<div class="grid">{rows}</div>
</div></body></html>'''
    p = "/tmp/缩略图对比.html"
    open(p, "w", encoding="utf-8").write(html)
    print("已生成", p)


if __name__ == "__main__":
    main()
