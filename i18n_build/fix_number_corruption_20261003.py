#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修翻译阶段把数字写坏的地方（2026-10-03 新建）

审计「数字守恒」时挖出 3 类**真实内容缺陷**（不是判据问题，客户看得见）：

  ① 日语把小数点写成全角句号：`19。3×3。1 cm`、`7。5 cm`、`2。8 m`
     —— 4 个页面 9 处。日语读者会看到「19。3」这种断句，尺寸完全读不出来。
     同一个页面里还并存正确写法（pr4 的 `7.5 cm` 出现在另一处），自相矛盾。

  ② 日语把「handles（把手尺寸）」译成「対応グレード（对应等级）」
     —— 语义错：等级 ≠ 尺寸。改为「ハンドル寸法」。

  ③ 韩语把文字**插进了数字中间**：`12×2~19 구간을 다룹니다.3×3.1 cm`
     —— 「구간을 다룹니다（覆盖该区间）」本该是整句的一部分，
     却被塞到 `19` 和 `.3` 之间，尺寸直接读不出来。这是翻译链的典型坏产物。

EN 原文（SSOT）：`Standard build is Rope 2.2 / 2.4 / 2.8 / 3 m; handles 12×2 – 19.3×3.1 cm.`
所以正确译文应为：
  ja: `標準仕様はロープ 2.2 / 2.4 / 2.8 / 3 m；ハンドル寸法：12×2～19.3×3.1 cmです。…`
  ko: `표준 규격은 로프 2.2 / 2.4 / 2.8 / 3 m; 핸들 12×2~19.3×3.1 cm입니다. …`

这些字符串在**正文与 JSON-LD 里各出现一次**，所以按页做全局替换即可（结构化数据是
Google 搜索结果里直接显示的 FAQ 答案，坏了比正文更致命）。

用法：
    python3 i18n_build/fix_number_corruption_20261003.py --dry-run
    python3 i18n_build/fix_number_corruption_20261003.py
    python3 i18n_build/fix_number_corruption_20261003.py --verify
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 精确替换表：(相对路径, 旧串, 新串, 说明)
FIXES = [
    ("ja/products/fi3.html", "19。3×3。1", "19.3×3.1", "① 全角小数点"),
    ("ja/products/fi3.html", "対応グレード：", "ハンドル寸法：", "② handles 误译为「等级」"),
    ("ja/products/pr4.html", "7。5", "7.5", "① 全角小数点"),
    ("ja/products/large-aerial-yoga-hammock.html", "2。8", "2.8", "① 全角小数点"),
    ("ja/applications/yoga-pilates-studios.html", "2。8", "2.8", "① 全角小数点"),
    ("ko/products/fi3.html", "12×2~19 구간을 다룹니다.3×3.1", "핸들 12×2~19.3×3.1", "③ 文字被插进数字中间"),
]
# 兜底：任何「数字。数字」都该是「数字.数字」
RE_ANY_FULLWIDTH = re.compile(r"(\d)。(\d)")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    total = 0
    for rel, old, new, why in FIXES:
        p = os.path.join(ROOT, rel)
        if not os.path.isfile(p):
            print("✗ 文件不存在：%s" % rel)
            return 1
        h = io.open(p, encoding="utf-8").read()
        n = h.count(old)
        if n == 0:
            if mode == "--verify":
                print("  ✓ %-46s 已无「%s」" % (rel, why))
            else:
                print("  · %-46s 未命中「%s」（可能已修）" % (rel, why))
            continue
        if mode == "--verify":
            print("  ✗ %-46s 仍有 %d 处「%s」" % (rel, n, why))
            total += n
            continue
        print("  %s %-46s %d 处 ← %s" % ("✓" if mode != "--dry-run" else "·", rel, n, why))
        total += n
        if mode != "--dry-run":
            io.open(p, "w", encoding="utf-8").write(h.replace(old, new))

    # 兜底扫描：整站不应再有「数字。数字」
    print("\n兜底扫描「数字。数字」（全角句号当小数点）：")
    SKIP = {"i18n_build", "outputs", "__pycache__", ".git", "node_modules"}
    bad = 0
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP]
        for f in fn:
            if not f.endswith(".html"):
                continue
            p = os.path.join(dp, f)
            try:
                h = io.open(p, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            for m in RE_ANY_FULLWIDTH.finditer(h):
                rel = os.path.relpath(p, ROOT)
                print("  ✗ %-44s 「%s」" % (rel, m.group(0)))
                bad += 1
    print("  剩余 = %d" % bad)

    if mode == "--verify":
        print("\n结论：%s" % ("数字书写已干净 ✓" if (bad == 0 and total == 0) else "仍有问题 ✗"))
        return 0 if (bad == 0 and total == 0) else 1
    print("\n合计替换 %d 处" % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
