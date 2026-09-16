#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""落盘前核查：把某条规则命中的**全部**上下文去重后列出来，逐条确认没改错。

698 处改动不能靠抽样就落盘。用法：
    python3 audit_rule_ctx.py "规则名关键字"            # 单个关键字
    python3 audit_rule_ctx.py "关键字A,关键字B,关键字C"  # 逗号分隔，批量核
输出 /tmp/rule_ctx.txt

⚠️ **必须按顺序模拟**（2026-09-16 修正）：
   第一版对**原始文件**逐条规则独立匹配，于是 `Es 连词被吞空格` 把
   `<li>TPEo ecológico</li>` 报成 `TPE o ecológico`（看着像严重误改）。
   但真实执行时 `Es 术语尾多余元音` 排在它**前面**，`TPEo` 早被吃成 `TPE` 了，
   后一条规则根本匹配不到。独立匹配会**系统性夸大**规则之间的冲突，
   反过来又会**系统性隐藏**规则顺序错导致的真冲突。
   现在的做法：边应用边匹配 —— 每条规则只在「前面规则已生效的文本」上找命中，
   再把这条规则**真正落盘**，继续下一条。这样看到的才等于 fix_glue 的落盘结果。
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
DIRS = ["", "products", "applications", "blog", "pilates"]

sys.path.insert(0, HERE)
from fix_glue_20260916 import COMPILED  # noqa: E402


def main():
    key = sys.argv[1] if len(sys.argv) > 1 else ""
    # 支持逗号分隔的多关键字批量核查
    keys = [k.strip() for k in key.split(",") if k.strip()]
    out = open("/tmp/rule_ctx.txt", "w", encoding="utf-8")
    total = 0
    for lg in LANGS:
        for sub in DIRS:
            base = os.path.join(ROOT, lg)
            pat = os.path.join(base, sub, "*.html") if sub else os.path.join(base, "*.html")
            for f in sorted(glob.glob(pat)):
                s = open(f, encoding="utf-8", errors="ignore").read()
                for rlg, rx, rep, why in COMPILED:
                    if rlg and rlg != lg:
                        continue
                    # ⚠️ 关键字只过滤「报不报」，不过滤「改不改」——
                    #    跳过的规则也必须照常落盘，否则后面规则看到的文本不是真实的。
                    if keys and not any(k in why for k in keys):
                        s = rx.sub(rep, s)
                        continue
                    # ⭐ 先看命中（此时文本已含前面规则的改动），再落盘这条规则
                    seen = set()
                    for m in list(rx.finditer(s)):
                        a, b = max(0, m.start() - 75), min(len(s), m.end() + 75)
                        ctx = re.sub(r"\s+", " ", s[a:b])
                        if ctx in seen:
                            continue
                        seen.add(ctx)
                        total += 1
                        # ⚠️ rep 可能是 lambda —— 必须**真正应用**才能看到成句，
                        #    直接打印会得到 "<function <lambda>>"（白排查一轮）
                        got = rep(m) if callable(rep) else m.expand(rep)
                        out.write("[%s] %s\n    匹配: %s\n    替换: %s\n    …%s…\n\n"
                                  % (os.path.relpath(f, ROOT), why,
                                     m.group(0)[:60], got[:70], ctx))
                    s = rx.sub(rep, s)
    out.close()
    print("规则「%s」共 %d 处（去重后）" % (key, total))


if __name__ == "__main__":
    main()
