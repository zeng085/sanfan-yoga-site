#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 description 还原成 HEAD 版本，供 trim_meta 用新规则重跑。

背景：trim_meta_20260915.py 第一版描述截断只按「句末 + 宽度预算」判断，
32 处里有 14 处把 B2B 钩子（MOQ / 打样 / OEM 贴牌 / 认证 / 报价）切掉了。
KEEP_RE 补上后需要回到干净状态统一重跑，否则残留的旧截断无法被新规则修正。

只动 <meta name="description">，不碰 <title>（title 的改动本身是对的）。
"""
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DESC_RE = re.compile(r'(<meta name="description" content=")([^"]*)(")')


def head_text(rel):
    try:
        out = subprocess.run(
            ["git", "show", "HEAD:" + rel],
            cwd=ROOT, capture_output=True, timeout=30,
        )
    except Exception:
        return None
    if out.returncode != 0:
        return None
    return out.stdout.decode("utf-8", "ignore")


def main():
    ls = subprocess.run(
        ["git", "diff", "--name-only", "--no-renames", "--", "*.html"],
        cwd=ROOT, capture_output=True,
    ).stdout.decode("utf-8", "ignore").split("\n")
    ls = [x for x in ls if x.strip()]
    changed = 0
    for rel in ls:
        path = os.path.join(ROOT, rel)
        new = io.open(path, encoding="utf-8", errors="ignore").read()
        old = head_text(rel)
        if old is None:
            continue
        nm = DESC_RE.search(new)
        om = DESC_RE.search(old)
        if not nm or not om:
            continue
        if nm.group(2) == om.group(2):
            continue                       # description 本来就没改（只改了 title）
        new = new[: nm.start(2)] + om.group(2) + new[nm.end(2):]
        io.open(path, "w", encoding="utf-8").write(new)
        changed += 1
    print("已还原 description 的文件数: %d" % changed)


if __name__ == "__main__":
    sys.exit(main())
