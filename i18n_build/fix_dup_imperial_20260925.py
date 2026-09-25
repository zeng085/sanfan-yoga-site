#!/usr/bin/env python3
"""修复 faq.html ×7 的「英制换算重复 + 值不一致」（2026-09-25）

缺陷（全站 1331 文件扫描，仅 7 个 faq.html 命中，共 14 处）：
  同一 FAQ（faq.a13「What can be customized」）里，厚度标注重复且两份串不一致：

  ┌ JSON-LD  : (6–12 mm (5/32\"–1/2\") (5/32\"–1/2\"))   ← 重复 + 值错
  └ 可见文本 : (6–12 mm (1/4"–1/2") (1/4"–1/2"))          ← 重复，值对

两个问题：
  1. 重复 —— 历史上「英制换算」脚本被跑了两次（插入型脚本未做幂等）
  2. 5/32" 值错 —— 6 mm ≈ 0.236"，即 1/4"；5/32" = 0.156" 实为 4 mm。
     全站惯例佐证：6 mm 后标 `1/4"` 共 185 处；`5/32"` 只作 4 mm 范围起点
     （`5/32"–1/4"`，blog 8 处）

修法：
  1. 相邻重复括号组 → 保留一个
  2. JSON-LD 侧的 `5/32"–1/2"` → `1/4"–1/2"`，与可见文本及全站惯例统一
     （只匹配以 –1/2 结尾的形态，不碰 blog 里合法的 `5/32"–1/4"`）

范围：仅 faq.html 及 6 个语言子目录版本；不含 CSS/JS，无需 bump 资源版本号。

用法：
  python3 i18n_build/fix_dup_imperial_20260925.py --dry-run
  python3 i18n_build/fix_dup_imperial_20260925.py --apply
  python3 i18n_build/fix_dup_imperial_20260925.py --check
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

LANGS = ["", "de", "ja", "ko", "fr", "it", "es"]


def targets() -> list[pathlib.Path]:
    out = []
    for lang in LANGS:
        p = ROOT / lang / "faq.html" if lang else ROOT / "faq.html"
        if p.exists():
            out.append(p)
    return out


# 相邻重复的括号组：( X ) ( X ) —— X 不含括号，2–60 字符
DUP_RE = re.compile(r"([（(][^()（）]{2,60}[）)])\s{0,2}\1")

# 只改以 –1/2" 结尾的 5/32" 形态。用 lookahead 只替换数字部分，保留 `"–1/2"` 原样
# —— 若把整段捕获进替换串，会连 `–1/2"` 一起吃掉（首版就犯了这个错）。
# 注意英寸符号紧跟数字（`5/32"`），JSON-LD 里写成 `5/32\"`，故 lookahead 必须含引号。
WRONG_VALUE_RE = re.compile(r'5/32(?=\\?"–1/2\\?")')

DUP_COUNT = 0
VAL_COUNT = 0


def fix(text: str) -> tuple[str, int, int]:
    text, n_dup = DUP_RE.subn(r"\1", text)
    text, n_val = WRONG_VALUE_RE.subn("1/4", text)
    return text, n_dup, n_val


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    g.add_argument("--check", action="store_true")
    args = ap.parse_args()

    files = targets()
    print(f"目标文件 {len(files)} 个\n")

    total_dup = total_val = 0
    plan = []
    for p in files:
        old = p.read_text(encoding="utf-8")
        new, nd, nv = fix(old)
        rel = p.relative_to(ROOT)
        mark = "—" if old == new else "改"
        print(f"  [{mark}] {str(rel):<16} 去重 {nd} 处 | 换算修正 {nv} 处")
        total_dup += nd
        total_val += nv
        plan.append((p, old, new, nd, nv))

    print(f"\n合计：去重 {total_dup} 处，换算修正 {total_val} 处")

    if args.check:
        bad = [str(p.relative_to(ROOT)) for p, old, new, _, _ in plan if old != new]
        if bad:
            print("✗ 未就绪：" + ", ".join(bad))
            return 1
        print("✓ 全部已修复且幂等（重跑零改动）")
        return 0

    if args.dry_run:
        # 展示修好后的串
        for p, old, new, nd, nv in plan:
            if nd or nv:
                for m in re.finditer(r".{60}1/4.{60}", new):
                    print(f"\n  {p.relative_to(ROOT)} 修复后：… {m.group(0)} …")
                break
        print("\n（dry-run，未写盘）")
        return 0

    for p, old, new, _, _ in plan:
        if old != new:
            p.write_text(new, encoding="utf-8")
    print("\n已写盘。")

    # 落盘自检
    left = 0
    for p in files:
        s = p.read_text(encoding="utf-8")
        left += len(DUP_RE.findall(s))
        left += len(WRONG_VALUE_RE.findall(s))
    print(f"复扫残留：{left} 处 {'✓' if left == 0 else '✗'}")
    return 1 if left else 0


if __name__ == "__main__":
    sys.exit(main())
