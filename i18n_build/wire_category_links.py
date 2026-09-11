# -*- coding: utf-8 -*-
"""
把根站页面里指向旧的「products.html#锚点」的分类链接，换成 8 个新分类页的真实链接。

处理两处：
  1) index.html 的「Our Product Range」区（.range-grid）：5 格 → 8 格
  2) 根站所有页面的 footer「Products」列：5 项 → 8 项

语言站（de/ja/ko/fr/it/es）不动 —— 它们的 products.html 仍是完整列表页，
内部锚点 `products.html#yoga` 在各自目录下依然有效。

用法
    python3 i18n_build/wire_category_links.py --dry-run
    python3 i18n_build/wire_category_links.py
"""
import argparse
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from category_map import CATS, build  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ("de", "ja", "ko", "fr", "it", "es")


def bi(en, zh):
    return '<span class="lang-en">%s</span><span class="lang-zh">%s</span>' % (en, zh)


def covers():
    """每个分类的封面图（= 该类首个产品的首图，与总览页一致）。"""
    cards = json.load(open(os.path.join(ROOT, "outputs/product_cards.json"), encoding="utf-8"))
    assign, _ = build()

    def order_key(s):
        m = re.match(r"([a-z]+)(\d+)$", s)
        return (0, m.group(1), int(m.group(2))) if m else (1, s, 0)

    groups = {c["key"]: [] for c in CATS}
    for slug, k in assign.items():
        groups[k].append(slug)
    out = {}
    for k in groups:
        groups[k].sort(key=order_key)
        m = re.search(r'<img src="([^"]+)"', cards[groups[k][0]])
        out[k] = (m.group(1).split("?")[0], len(groups[k]))
    return out, groups


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cov, groups = covers()
    changed = []

    # ---------- 1) 首页 range-grid ----------
    range_cards = []
    for c in CATS:
        img, n = cov[c["key"]]
        range_cards.append(
            '        <a href="%s.html" class="range-card">\n'
            '          <div class="rc-img"><img src="%s" width="480" height="480" '
            'loading="lazy" alt="%s"></div>\n'
            '          <div class="rc-body"><h3>%s</h3><p>%s</p>'
            '<span class="rc-more"><span class="lang-en">View %d products &rarr;</span>'
            '<span class="lang-zh">%d 款产品 &rarr;</span></span></div>\n'
            '        </a>' % (c["key"], img, c["en"], bi(c["en"], c["zh"]),
                              bi(c["kw_en"], c["kw_zh"]), n, n)
        )
    range_block = "\n".join(range_cards)

    # ---------- 2) footer Products 列 ----------
    foot_block = "".join(
        '        <li><a href="%s.html">%s</a></li>\n' % (c["key"], bi(c["en"], c["zh"]))
        for c in CATS
    )

    idx = os.path.join(ROOT, "index.html")
    s = open(idx, encoding="utf-8").read()

    # 2a. range-grid：换掉其中所有 range-card 链接
    if '<div class="range-grid">' in s:
        i = s.index('<div class="range-grid">')
        j = s.index("</section>", i)
        block = s[i:j]
        a0 = block.index("<a href=")
        a1 = block.rindex("</a>") + len("</a>")
        new_block = block[:a0] + range_block + block[a1:]
        s = s[:i] + new_block + s[j:]
        changed.append(("index.html range-grid", "8 格"))
    else:
        print("! index.html 未找到 range-grid", file=sys.stderr)

    if not args.dry_run:
        open(idx, "w", encoding="utf-8").write(s)

    # ---------- 3) 所有根站页面的 footer ----------
    FOOT = re.compile(
        r'(<h5 data-i18n="foot\.products">Products</h5>\s*<ul>\s*)(.*?)(\s*</ul>)', re.S
    )
    for p in sorted(glob.glob(os.path.join(ROOT, "*.html"))):
        if os.path.basename(p) in ("product.html",):   # 孤儿页，不参与导航
            continue
        s = open(p, encoding="utf-8").read()
        m = FOOT.search(s)
        if not m:
            print("! %s 未匹配 footer" % os.path.basename(p), file=sys.stderr)
            continue
        if m.group(2).strip() == foot_block.strip():
            continue
        s = s[:m.start(2)] + "\n" + foot_block + "      " + s[m.end(2):]
        if not args.dry_run:
            open(p, "w", encoding="utf-8").write(s)
        changed.append((os.path.basename(p) + " footer", "8 项"))

    print("改动 %d 处：" % len(changed))
    for a, b in changed:
        print("  %-38s %s" % (a, b))

    # ---------- 4) 残留检查 ----------
    print("\n残留 products.html#锚点：")
    left = 0
    for p in sorted(glob.glob(os.path.join(ROOT, "*.html"))):
        t = open(p, encoding="utf-8").read()
        n = len(re.findall(r"products\.html#(?:yoga|props|rollers|bands|fitness)", t))
        if n:
            print("  %-30s %d" % (os.path.basename(p), n))
            left += n
    print("  合计 %d" % left)


if __name__ == "__main__":
    main()
