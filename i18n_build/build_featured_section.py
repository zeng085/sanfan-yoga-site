"""把首页「Full Product Gallery」（20 张老页卡，与上区 8 格分类导航撞图 7 张）
改造成「Featured Products」（12 款跨分类主推新品，全部来自新批次页面）。

- 卡片直接取卡片池 `outputs/product_cards.json`（新页卡自带 lang-en/lang-zh 双语）
- 修正空壳页残留的 "Made to order" 中文未翻译问题
- 幂等：可重复运行

用法
    python3 i18n_build/build_featured_section.py [--dry-run]
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOL = os.path.join(ROOT, "outputs/product_cards.json")
INDEX = os.path.join(ROOT, "index.html")

# 12 款主推：8 个分类各 1–2 款。刻意避开上区 8 格分类导航用到的老页
# （ym1 / ym5 / pr3 / fr1 / fr5 / rb1 / fi2 / aurora-gradient-suede-yoga-mat），
# 否则首图会与分类卡重复。
FEATURED = [
    "two-tone-double-layer-tpe-yoga-mat",   # TPE
    "cork-tpe-yoga-mat",                    # TPE
    "red-pu-rubber-yoga-mat",               # PU
    "marble-print-pu-rubber-yoga-mat",      # PU
    "flamingo-print-suede-rubber-yoga-mat", # 麂皮软木
    "starry-night-print-suede-yoga-mat",    # 麂皮软木
    "round-mandala-meditation-mat",         # 冥想普拉提
    "pilates-reformer-mat-custom-logo",     # 冥想普拉提
    "vibrating-foam-roller",                # 泡沫轴
    "fascia-gun",                           # 按摩康复
    "figure-8-resistance-bands",            # 弹力带
    "eva-yoga-block",                       # 辅具配件
]

# 英文站空壳页导致描述只有 "Made to order"，中英同文 —— 补中文
FIX_ZH = [("Made to order", "按单定制")]


def fix_card(html):
    for en, zh in FIX_ZH:
        html = html.replace(
            '<span class="lang-zh">%s</span>' % en,
            '<span class="lang-zh">%s</span>' % zh,
        )
    return html


def build_grid():
    pool = json.load(open(POOL, encoding="utf-8"))
    cards = []
    for slug in FEATURED:
        if slug not in pool:
            print("  ! 卡片池缺 %s" % slug, file=sys.stderr)
            continue
        cards.append("        " + fix_card(pool[slug]))
    return "\n".join(cards)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = open(INDEX, encoding="utf-8").read()
    m = re.search(
        r'  <!-- ===== Full gallery ===== -->\n'
        r'  <section class="section soft">[\s\S]*?\n  </section>\n',
        src,
    )
    if not m:
        print("! 未找到 Full gallery 区块（已改过？）", file=sys.stderr)
        return 1

    grid = build_grid()
    new = (
        '  <!-- ===== Featured products ===== -->\n'
        '  <section class="section soft">\n'
        '    <div class="container">\n'
        '      <div class="section-head">\n'
        '        <div class="eyebrow" data-i18n="featured.title">Featured Products</div>\n'
        '        <h2 data-i18n="featured.title">Featured Products</h2>\n'
        '        <p data-i18n="featured.sub">A hand-picked selection across our 8 product lines'
        ' — every one customizable with your logo, size, thickness and packaging.</p>\n'
        '      </div>\n'
        '      <div class="featured-grid">\n'
        '%s\n'
        '      </div>\n'
        '      <div class="featured-cta">\n'
        '        <a class="btn btn-primary" href="products.html" data-i18n="featured.cta">'
        'Browse all 117 products</a>\n'
        '      </div>\n'
        '    </div>\n'
        '  </section>\n' % grid
    )

    print("  区块字符数: %d → %d" % (len(m.group(0)), len(new)))
    print("  卡片数: %d" % len(FEATURED))
    if args.dry_run:
        print("\n--- 预演，未写入 ---")
        print(new[:600])
        return 0

    open(INDEX, "w", encoding="utf-8").write(src[:m.start()] + new + src[m.end():])
    print("✅ index.html 已更新")
    return 0


if __name__ == "__main__":
    sys.exit(main())
