#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清除「成对排版引号只包术语本身」的机翻残留（2026-09-25）。

背景
----
DeepL 在部分语言里会给受保护术语**单独加一对排版引号**：

    de  gemäß den Normen „REACH“, „CA Prop 65“ und „6P/7P“ geprüft
    de  dominiert den Bereich „PVC“ und den Schaumstoffmarkt
    es  domina el segmento «PVC»
    ja  「PU」の分野

判据（决定性）：**只有德语/零星语言有**。同一句话 en/ja/ko/fr/it/es 版本
**都不加引号**（已逐语言对照 de/pilates 同一段文字）。德语里给标准名加引号
语法上不算错，但全站 7 语言只有 de 加 → 是机翻产物而非人工排版意图，
且 `„6P/7P“`（化学配方代号）加引号更说不通。

严格边界（**不能误伤**）
----------------------
两个约束保证只清「引号内侧只有术语本身」的形态：

1. 正则要求引号**紧贴术语**（`Q \\s* TERM \\s* Q`）—— 引号跨更长短语的
   **语义正确引用**一律不匹配，项目里大量存在且必须保留：
       de  ein Bericht für „TPE-Matte, violett, 6 mm“ gilt nicht für …
       es  cuando un proveedor indica «MOQ 100», la pregunta …
       ja  当社は、TPEと「PU-on-rubber」の両方を製造しています
       en  …routinely ask for an “EVA yoga mat” when what they need is…
2. 左右引号必须是**已登记的成对组合**（PAIRS）—— 单侧引号（如 `„TPE-Matte…
   …6 mm“` 的左半）永远不会被单独清掉。

ASCII 直引号（`"TPE"`）同样**不动**：它是 HTML/JSON 里的语法字符，
且 it/applications 等页用它作产品名强调，属当地合法用法（231 处，已复核）。

用法
----
    python3 fix_quote_wrap_20260925.py             # 干跑：列出将改动的处数与预览
    python3 fix_quote_wrap_20260925.py --apply     # 落盘
    python3 fix_quote_wrap_20260925.py --check     # 自检：断言全站 0 残留
    python3 fix_quote_wrap_20260925.py --group 1   # 只处理第 1 组
    python3 fix_quote_wrap_20260925.py --scan-extra # 报告术语表外的疑似残留（不改）

分组
----
  GROUP 1 = 散文里的裸材质名（6 文件）
  GROUP 2 = de/pilates/* 的标准名列表（9 文件）

回滚：git checkout -- <目标文件>
"""

import argparse
import collections
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# 排版引号（**不含 ASCII `"`** —— 见模块注释）
Q = "\u201e\u201c\u201d\u00ab\u00bb\u2039\u203a\u2018\u2019\u300c\u300d\u300e\u300f"

# 合法的 (左, 右) 组合白名单；不成对则一律不动
PAIRS = {
    ("\u201e", "\u201c"),  # „ … “   德语
    ("\u201c", "\u201d"),  # “ … ”
    ("\u00ab", "\u00bb"),  # « … »   法语/西语/意语
    ("\u2039", "\u203a"),  # ‹ … ›
    ("\u2018", "\u2019"),  # ‘ … ’
    ("\u300c", "\u300d"),  # 「 … 」  日语
    ("\u300e", "\u300f"),  # 『 … 』
}

# 材质 / 认证 / 标准 / 化学配方代号
TERMS = (
    r"(?:TPEE|TPE|PVC|PU|NBR|EVA|SBR|EEP"
    r"|ROHS|REACH|SGS|BSCI|Intertek|TUV"
    r"|MOQ|OEM|ODM|ISO\s?9001|CA\s?Prop\s?65|EN\s?71|OEKO-?TEX|CPSIA"
    r"|6P/7P|PAHs?)"
)

# 术语表之外，用来「报告但不改」的探测：成对引号紧贴全大写缩写/标准号
EXTRA = r"(?:[A-Z][A-Za-z]*[\s/-]?[A-Z0-9][A-Za-z0-9\s/.-]{0,14})"

PAT = re.compile(r"([" + Q + r"])\s*(" + TERMS + r")\s*([" + Q + r"])(?![A-Za-z])")
EXTRA_PAT = re.compile(r"([" + Q + r"])\s*(" + EXTRA + r")\s*([" + Q + r"])(?![A-Za-z])")

SKIP_DIRS = ("i18n_build", "node_modules", ".git", "outputs", "_pending")
DATE = "20260925"

GROUPS = {
    1: [
        "de/blog/top-12-china-yoga-mat-manufacturers.html",
        "es/blog/top-12-china-yoga-mat-manufacturers.html",
        "fr/blog/top-12-china-yoga-mat-manufacturers.html",
        "it/blog/top-12-china-yoga-mat-manufacturers.html",
        "ja/blog/top-12-china-yoga-mat-manufacturers.html",
        "ko/blog/private-label-yoga-mats.html",
    ],
    2: [
        "de/pilates/index.html",
        "de/pilates/pilates-cadillac.html",
        "de/pilates/pilates-ladder-barrel.html",
        "de/pilates/pilates-reformer.html",
        "de/pilates/pilates-reformer-tower.html",
        "de/pilates/pilates-specialty.html",
        "de/pilates/pilates-spine-corrector.html",
        "de/pilates/pilates-studio-set.html",
        "de/pilates/pilates-wunda-chair.html",
    ],
}


def strip_quotes(text):
    """清掉「成对引号只包术语本身」的引号；返回 (新文本, 命中数)。"""
    n = [0]

    def repl(m):
        if (m.group(1), m.group(3)) not in PAIRS:
            return m.group(0)  # 不成对 → 不动
        n[0] += 1
        return m.group(2)

    return PAT.sub(repl, text), n[0]


def all_html():
    for p in sorted(ROOT.rglob("*.html")):
        ps = str(p)
        if any(s in ps for s in SKIP_DIRS):
            continue
        yield p


def contexts(text, pat):
    """统计命中落在可见文本 / JSON-LD / meta / title / attr 的分布。"""
    agg = collections.Counter()
    for m in pat.finditer(text):
        i = m.start()
        kind = "可见文本"
        for sm in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', text, re.S):
            if sm.start() < i < sm.end():
                kind = "JSON-LD"
                break
        else:
            for mm in re.finditer(r'<meta[^>]*content="([^"]*)"', text):
                if mm.start(1) <= i < mm.end(1):
                    kind = "meta"
                    break
            else:
                for tm in re.finditer(r"<title>(.*?)</title>", text, re.S):
                    if tm.start() < i < tm.end():
                        kind = "title"
                        break
                else:
                    for am in re.finditer(r'="([^"]{0,6000})"', text):
                        if am.start(1) <= i < am.end(1):
                            kind = "attr"
                            break
        agg[kind] += 1
    return agg


def targets(groups):
    out = []
    for g in groups:
        out.extend(GROUPS[g])
    return out


def do_scan_extra():
    print("=== 术语表之外的「成对引号紧贴大写串」疑似残留（**不改**，仅供人工判断）===")
    total = 0
    for p in all_html():
        s = p.read_text(encoding="utf-8", errors="replace")
        for m in EXTRA_PAT.finditer(s):
            if (m.group(1), m.group(3)) not in PAIRS:
                continue
            if re.fullmatch(TERMS, m.group(2)):
                continue  # 已在主表内
            total += 1
            a = max(0, m.start() - 70)
            b = min(len(s), m.end() + 50)
            print(f"  {p.relative_to(ROOT)}: {m.group(0)!r}")
            print(f"      …{re.sub(r'[ \t]+', ' ', s[a:b])}…")
    print(f"\n共 {total} 处")


def do_check():
    print("=== 自检：全站「成对引号只包术语」残留（应为 0）===")
    bad = 0
    for p in all_html():
        s = p.read_text(encoding="utf-8", errors="replace")
        _, n = strip_quotes(s)
        if n:
            bad += 1
            print(f"  ✗ {p.relative_to(ROOT)}  ×{n}")
    print(f"\n{'全部通过' if bad == 0 else str(bad) + ' 个文件仍有残留'}")
    return 1 if bad else 0


def do_run(apply_, groups):
    files = targets(groups)
    print(f"=== 目标 {len(files)} 文件（组 {groups}）===")
    total = 0
    touched = []
    agg = collections.Counter()
    for rel in files:
        p = ROOT / rel
        if not p.exists():
            print(f"  ✗ 缺文件 {rel}")
            return 1
        s = p.read_text(encoding="utf-8")
        new, n = strip_quotes(s)
        if n:
            total += n
            touched.append(rel)
            agg.update(contexts(s, PAT))
            if apply_:
                p.write_text(new, encoding="utf-8")
        print(f"  {'改' if n else '—'} {rel:<58} ×{n}")
    print(f"\n命中 {total} 处 / {len(touched)} 文件")
    if agg:
        print("上下文分布: " + ", ".join(f"{k}={v}" for k, v in agg.most_common()))
    if apply_:
        print("已落盘。")
    else:
        print("（干跑，未落盘；加 --apply 生效）")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="落盘")
    ap.add_argument("--check", action="store_true", help="自检：断言 0 残留")
    ap.add_argument("--scan-extra", action="store_true", help="报告术语表外疑似残留（不改）")
    ap.add_argument("--group", type=int, choices=[1, 2], action="append", help="只处理指定组，可重复")
    args = ap.parse_args()

    if args.scan_extra:
        do_scan_extra()
        return 0
    if args.check:
        return do_check()
    groups = args.group or [1, 2]
    return do_run(args.apply, groups)


if __name__ == "__main__":
    sys.exit(main())
