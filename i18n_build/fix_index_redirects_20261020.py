#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修正站内指向 index.html 的链接（会产生 308 重定向，浪费爬取预算）。

背景（2026-10-20 GSC 确诊）：
  GSC「未编入索引」里 17 页是 Page with redirect。
  线上实测 `/index.html` → 308 → `/`，同理 `/de/index.html` → 308 → `/de/`。
  站内 75 处写成 `../applications/index.html` / `../pilates/index.html` / `../index.html`，
  爬虫每次跟随都多一跳 308。

  对 52 天新站，爬取预算极度紧张（1202 页卡在「已发现-尚未抓取」），
  任何一次多余跳转都在烧预算。

用法：
    python i18n_build/fix_index_redirects_20261020.py --dry-run
    python i18n_build/fix_index_redirects_20261020.py --apply
    python i18n_build/fix_index_redirects_20261020.py --verify
判据铁律：
  · 只改 href 属性值，不碰正文里的 "index.html" 字样
  · 空集必须硬失败（一处都没改到=判据失效）
  · 用 Python re，不用 grep（BSD grep 对分组支持不可靠）
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# href="../a/b/index.html"  ->  href="../a/b/"
# href="../index.html"      ->  href="../"
FIX_RX = re.compile(r'(href="(?:\.\./)+(?:[a-z0-9-]+/)*)index\.html"')
CHECK_RX = re.compile(r'href="(?:\.\./)+(?:[a-z0-9-]+/)*index\.html"')


def iter_html():
    for dp, dn, fn in os.walk(ROOT):
        if ".git" in dp or "node_modules" in dp or os.sep + "outputs" in dp:
            continue
        for f in fn:
            if f.endswith(".html"):
                yield os.path.join(dp, f)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--dry-run"
    if mode not in ("--dry-run", "--apply", "--verify"):
        print(__doc__)
        sys.exit(2)

    files = list(iter_html())
    if not files:
        print("FAIL: 没扫到 HTML，路径有问题")
        sys.exit(1)

    if mode == "--verify":
        left = 0
        hits = []
        for p in files:
            with open(p, encoding="utf-8") as fh:
                h = fh.read()
            n = len(CHECK_RX.findall(h))
            if n:
                left += n
                hits.append((os.path.relpath(p, ROOT), n))
        if left:
            print(f"FAIL: 仍有 {left} 处 index.html 内链")
            for f, n in hits[:8]:
                print("  ", f, n)
            sys.exit(1)
        print("[verify] index.html 内链残留 = 0 ✓")
        return

    changed_files = 0
    changed_links = 0
    samples = []
    for p in files:
        with open(p, encoding="utf-8") as fh:
            h = fh.read()
        if "index.html" not in h:
            continue
        new, n = FIX_RX.subn(r'\1"', h)
        if n:
            changed_files += 1
            changed_links += n
            if len(samples) < 3:
                samples.append((os.path.relpath(p, ROOT), n))
            if mode == "--apply":
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(new)

    if changed_links == 0:
        print("FAIL: 一处都没匹配到，判据失效，硬失败")
        sys.exit(1)

    print(f"[{mode}] 改动文件 {changed_files} 个，修正链接 {changed_links} 处")
    for f, n in samples:
        print(f"   样例: {f} ({n} 处)")
    if mode == "--dry-run":
        print("\n演练，未落盘。确认后跑 --apply")


if __name__ == "__main__":
    main()