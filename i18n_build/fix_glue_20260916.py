#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复机翻造成的「术语粘连 / 错误省音」硬伤（2026-09-16）

【病根】
翻译引擎把受保护术语包成 `<xN>TPE</xN>` 并交给 DeepL 的 `ignore_tags`，
引擎**看不到术语的首字母**，于是自己猜：
  · 猜错省音 → fr `d'TPE`（应 `en TPE`）、it `dell'TPE`（应 `del TPE`）
  · 猜错词形 → it `in gommPUe`（应 `in gomma PU`）、es `ecoTPEe`（应 `eco TPE`）
  · 缺空格     → es `«Alignment Line»TPE`、`80/90 cmTPE`、fr `« WideTPE »`
  · 吞掉逗号   → es/fr/ko `REACHCA Prop 65`（应 `REACH, CA Prop 65`）
  · 整词幻觉   → es `No contiene bifeniloPVC`（EN 是 `contains no PVC`，
                 `bifenilo`（联苯）纯属编造）

同类问题 2026-09-15 已记录过一次形态：「Pilates Ladder Barrel」→「à l'Ladder Barrel」。

【为什么必须逐语言写规则，不能一条正则通吃】
  1. `l'X` 在**法语/意大利语**是错的（X 为辅音开头的术语），在意大利语 `L'OEM` /
     `all'ODM` 却是**对的**（O 是元音）——一刀切会改坏正确的文本。
  2. 法语 `de l'X` 缩合后是 `du X`，不是 `le X`；
     而 `« Marble Print » d'PU` 这种产品名后置的，用 `en PU` 更自然。
     → 必须短语级规则优先，通用规则兜底。
  3. 德语 `und PVC` 是**语义反了**（EN 原文 `no PVC`，应为 `kein PVC`），
     属内容错误，不是拼接错误 —— 只能整句替换。

【只动什么】只改文本节点里的这些坏串；不碰标签、class、URL、脚本逻辑。

用法：
    python3 fix_glue_20260916.py --check     # 只报告（幂等自检）
    python3 fix_glue_20260916.py --dry-run   # 打印改动明细
    python3 fix_glue_20260916.py             # 落盘
"""
import glob
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
DIRS = ["", "products", "applications", "blog", "pilates"]

# ---------------------------------------------------------------- 规则表
# ⭐ 规则表已抽到 i18n_build/term_repair.py —— **单一来源**，
#    翻译管线（translator.py）也 import 它做译文出口修复，避免重生成时复发。
from term_repair import COMPILED  # noqa: E402


def files():
    for lg in LANGS:
        for sub in DIRS:
            base = os.path.join(ROOT, lg)
            pat = os.path.join(base, sub, "*.html") if sub else os.path.join(base, "*.html")
            for f in sorted(glob.glob(pat)):
                yield lg, f


def main():
    check = "--check" in sys.argv
    dry = check or "--dry-run" in sys.argv
    stat = Counter()
    samples = []
    touched = set()

    for lg, path in files():
        s = open(path, encoding="utf-8").read()
        orig = s
        for rlg, rx, rep, why in COMPILED:
            if rlg and rlg != lg:
                continue
            # ⚠️ 不能用 rx.subn 的 n 当命中数：部分规则的 rep 是 lambda，会对
            #    特定匹配**原样返回**（例：ko `무PVC` 的 `무` 是「无/免」前缀，
            #    属构词成分，规则故意跳过）。subn 只数「匹配数」，会把这类
            #    故意豁免的匹配算成残留，导致 --check 永不归零。
            #    → 这里逐匹配对比「替换后是否真的变样」，只计**实际改动**。
            parts, last, n = [], 0, 0
            for m in rx.finditer(s):
                parts.append(s[last:m.start()])
                out = m.expand(rep) if isinstance(rep, str) else rep(m)
                if out != m.group(0):
                    n += 1
                parts.append(out)
                last = m.end()
            if n:
                parts.append(s[last:])
                s = "".join(parts)
            if n:
                stat[why] += n
                if len(samples) < 22:
                    # ⚠️ 必须在**改动前**的文本里找样本：前面的规则可能已经改写掉这处
                    m = rx.search(orig)
                    if m:
                        a = max(0, m.start() - 50)
                        samples.append((os.path.relpath(path, ROOT), why, n,
                                        orig[a:m.end() + 50].replace("\n", " ")))
        if s != orig:
            stat["_files"] += 1
            touched.add(os.path.relpath(path, ROOT))
            if not dry:
                open(path, "w", encoding="utf-8").write(s)

    print("模式: %s" % ("检查(dry)" if dry else "落盘"))
    print("改动文件 %d 个 | 改动处 %d 处\n" % (stat["_files"], sum(v for k, v in stat.items() if k != "_files")))
    print("%-52s %s" % ("规则", "命中"))
    print("-" * 66)
    for why, n in stat.most_common():
        if why != "_files":
            print("%-52s %d" % (why, n))
    if samples:
        print("\n示例：")
        for rel, why, n, ctx in samples:
            print("  %-46s [%s x%d]" % (rel, why, n))
            print("      …%s…" % ctx)


if __name__ == "__main__":
    main()
