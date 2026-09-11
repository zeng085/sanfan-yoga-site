#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""缩略图网格三态对比预览：现状(cover铺满) / contain内缩 / contain内缩+换图。

核心判断：色块来自图片素材本身，只要图片铺满格子，色块就铺满 → 必然"有的有边框有的没有"。
把图片改成 contain + 内缩，色块会缩到格子中央、四周统一露出卡片底色 → 形状统一。
"""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPER = "#f9f7f2"

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


def row(srcs, mode):
    h = ""
    for s in srcs:
        f = SWAP.get(s, s) if mode == "swap" else s
        cls = "th"
        if mode == "cover":
            cls += " cover"
        if mode == "swap" and SWAP.get(s, s) != s:
            cls += " sw"
        h += f'<a class="{cls}"><img src="file://{ROOT}/assets/img/{f}" alt="{f}"></a>'
    return h


def main():
    body = ""
    for name, srcs in tiles():
        body += f'''<div class="tile"><h3>{name}</h3>
<div class="col"><p class="kw">① 现状：cover 铺满</p><div class="thumbs">{row(srcs, "cover")}</div></div>
<div class="col"><p class="kw">② contain + 内缩 10%</p><div class="thumbs contain">{row(srcs, "contain")}</div></div>
<div class="col"><p class="kw">③ contain + 内缩 + 换图 <span class="hint">(绿框=已换)</span></p><div class="thumbs contain">{row(srcs, "swap")}</div></div>
</div>'''

    html = f'''<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8"><title>缩略图三态对比</title>
<style>
 body {{ background:#e8e6e0; font:13px -apple-system,"PingFang SC",sans-serif; margin:0; padding:20px; }}
 .wrap {{ max-width:860px; margin:0 auto; }}
 h1 {{ font-size:18px; margin:0 0 4px; color:#1d2b26; }}
 .lead {{ color:#5a6b64; margin:0 0 18px; font-size:12px; line-height:1.6; }}
 .tile {{ background:{PAPER}; border-radius:6px; padding:14px 16px; margin-bottom:16px; }}
 .tile h3 {{ margin:0 0 10px; font-size:15px; font-weight:600; color:#1d2b26; }}
 .kw {{ margin:0 0 6px; color:#0f6b52; font-size:12px; font-weight:600; }}
 .hint {{ color:#8a978f; font-weight:400; }}
 .thumbs {{ display:grid; grid-template-columns:repeat(6,1fr); gap:8px; margin-bottom:12px; }}
 /* 现状：铺满 */
 .th {{ display:block; aspect-ratio:1/1; border-radius:6px; overflow:hidden;
        background:{PAPER}; isolation:isolate; position:relative; }}
 .th img {{ width:100%; height:100%; display:block; mix-blend-mode:multiply; }}
 .th.cover img {{ object-fit:cover; }}
 .th.contain img {{ object-fit:contain; padding:10%; }}
 .th.sw {{ outline:1.5px solid #0f6b52; }}
</style></head><body><div class="wrap">
<h1>缩略图网格：三种处理方式</h1>
<p class="lead">同一个分类卡在三种条件下的真实渲染（卡片色 #f9f7f2 + multiply）。<br>
① 现状：图片 cover 铺满，图片自带什么底色就铺满整格 → 绿块/白卡/粉块与融入的格子混在一起。<br>
② contain + 内缩：图片缩到格子 80% 居中，色块不再铺满，四周统一露出卡片底色。<br>
③ 在 ② 基础上，把有白底/中性候选的图换掉。</p>
{body}
</div></body></html>'''
    open("/tmp/缩略图三态.html", "w", encoding="utf-8").write(html)
    print("已生成 /tmp/缩略图三态.html")


if __name__ == "__main__":
    main()
