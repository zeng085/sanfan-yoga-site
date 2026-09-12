#!/usr/bin/env python3
"""修复卡片池 HTML 串里「属性值中的未转义英寸符号」。

背景：`outputs/product_cards.json` 存的是成品 HTML 串，某几张卡的 `alt` 属性里
产品名带英寸符号（`Mini Yoga Ball 25cm (10")`），直接写进 `alt="…"` 就变成畸形属性：

    alt="Mini Yoga Ball 25cm (10")"     ← 浏览器解析到 (10 就截断

后果不只是 alt 错：`build_pages.py` 的属性重写器 ATTR_RE 解析到畸形标签时，
会跳过该标签剩余属性 —— 实测导致 `ja/yoga-props-accessories.html` 的图片
`src` 少了一层 `../`，在语言站下 404。

用法：
    python3 i18n_build/fix_card_alt_quotes.py            # 体检，不改
    python3 i18n_build/fix_card_alt_quotes.py --fix      # 就地修复卡片池
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOL = os.path.join(ROOT, "outputs", "product_cards.json")

TAG_RE = re.compile(r"<[a-zA-Z][^>]*>")
# 畸形形状：="值")"  —— 值里那个 " 是英寸符号，紧跟 ) 和真正的闭合引号。
# 三个引号：开引号、英寸符号、闭合引号（畸形）。
BAD_RE = re.compile(r'=("[^"<>]*)"\)"')


def repair_tag(tag):
    """把 ="...")" 修成 ="...&quot;)"；返回 (新标签, 修了几处)"""
    n = 0

    def _r(m):
        nonlocal n
        n += 1
        return '=%s&quot;)"' % m.group(1)

    new = BAD_RE.sub(_r, tag)
    return new, n


def main(fix=False):
    pool = json.load(open(POOL, encoding="utf-8"))
    total_fixed = 0
    touched = []

    for key, html in pool.items():
        if not isinstance(html, str):
            continue
        changed = False
        out = []
        last = 0
        for m in TAG_RE.finditer(html):
            tag = m.group(0)
            if tag.count('"') % 2 == 0:
                continue
            new, n = repair_tag(tag)
            if n:
                out.append(html[last:m.start()])
                out.append(new)
                last = m.end()
                total_fixed += n
                changed = True
        if changed:
            out.append(html[last:])
            newhtml = "".join(out)
            touched.append((key, total_fixed))
            if fix:
                pool[key] = newhtml

    print("=== 卡片池引号配平 ===")
    print("  卡片总数:", len(pool))
    if touched:
        for key, _ in touched:
            print("  ⚠️  需修:", key)
    else:
        print("  ✅ 全部标签引号配平正常")

    # 修复后复查
    if fix:
        left = 0
        for key, html in pool.items():
            if not isinstance(html, str):
                continue
            for m in TAG_RE.finditer(html):
                if m.group(0).count('"') % 2:
                    left += 1
                    print("  ❌ 仍畸形:", key, m.group(0)[:120])
        json.dump(pool, open(POOL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("\n  已写回 %s（修 %d 处，残留畸形 %d 处）" % (POOL, total_fixed, left))
    else:
        print("\n  修法预览（加 --fix 生效）：")
        for key, html in pool.items():
            if not isinstance(html, str):
                continue
            for m in TAG_RE.finditer(html):
                t = m.group(0)
                if t.count('"') % 2:
                    new, _ = repair_tag(t)
                    a = t[:150]
                    b = new[:150]
                    if a != b:
                        print("   %-8s 前: %s" % (key, a))
                        print("   %-8s 后: %s" % ("", b))


if __name__ == "__main__":
    main(fix="--fix" in sys.argv)
