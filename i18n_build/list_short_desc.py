#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""列出 description 过短（展示位浪费）的页面 —— stats_meta 的互补视图。

stats_meta.py 只报「超长」，本脚本报另一头：宽度不足的页面。
Google 桌面 description 展示位约 155 宽（CJK=2），低于 ~120 宽
基本等于把展示位空着，且缺少 B2B 钩子（起订量 / 打样 / OEM / 认证）。

用法：
    python3 list_short_desc.py            # 默认阈值 120
    python3 list_short_desc.py 72         # 自定义阈值
"""
import glob
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESC_RE = re.compile(r'<meta name="description" content="([^"]*)"')
HEAD_BYTES = 8000          # description 一定在 <head> 内，只读文件头，快且省内存


def W(s):
    """近似显示宽度：CJK/全角算 2，其余算 1。"""
    return sum(2 if ord(c) > 0x2E80 else 1 for c in s)


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    os.chdir(ROOT)
    rows = []
    total = 0
    for f in sorted(glob.glob("**/*.html", recursive=True)):
        with open(f, encoding="utf-8", errors="replace") as fh:
            head = fh.read(HEAD_BYTES)
        m = DESC_RE.search(head)
        if not m:
            continue
        total += 1
        w = W(html.unescape(m.group(1)))
        if w < limit:
            rows.append((w, f, html.unescape(m.group(1))))
    print("扫描 %d 页（有 description）| 宽度 < %d 的页面：%d 个" % (total, limit, len(rows)))
    print("-" * 100)
    for w, f, t in sorted(rows):
        print("%3d  %-52s %s" % (w, f, t))


if __name__ == "__main__":
    main()
