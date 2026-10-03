#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给产能表套上独立横向滚动容器（2026-10-03）

问题（客户视角实测）：`table.cap-table`（产能表「Das Werk auf einen Blick」）
在 ≤360px 视口下宽 377px，超出 57px。页面根上有 `html,body{overflow-x:clip}`，
所以客户**看不到横向滚动条，而是右侧的产能数字直接消失** ——
对一个「年产百万张垫」的工厂来说，这是信息丢失，不是观感问题。
根因：`td.val{white-space:nowrap}` 让 `1.000.000 Stück pro Jahr` 这类长串不换行。

修法（沿用本仓既有的 `.kit-wrap` / `.mat-wrap` 模式，不发明新写法）：
在表格外包一层 `<div class="cap-wrap">`，CSS 给它 `overflow-x:auto`
→ 表格可以横向滑动，数据完整可见；宽屏下 `overflow:auto` 不产生任何视觉变化。

为什么用脚本而不是手改：涉及 EN + 6 语言共 29 个页面，且语言页由 build_pages.py 生成 ——
按项目铁律「改标签必须成对 / 改文案必须生成器重建」，手改语言页会在下次重建时丢失。

用法：
    python3 i18n_build/wrap_cap_table_20261003.py --dry-run
    python3 i18n_build/wrap_cap_table_20261003.py
    python3 i18n_build/wrap_cap_table_20261003.py --verify
"""
import io
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {"i18n_build", "outputs", "__pycache__", ".git", "node_modules", "assets"}
RE_TABLE = re.compile(r'<table class="cap-table">.*?</table>', re.S)
RE_ALREADY = re.compile(r'<div class="cap-wrap">\s*(<table class="cap-table">.*?</table>)\s*</div>', re.S)
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "param", "source", "track", "wbr"}


def collect_html():
    out = []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if f.endswith(".html"):
                out.append(os.path.join(dp, f))
    return sorted(out)


def balance(text):
    from collections import Counter as C
    d = C()
    t = re.sub(r"<script\b.*?</script>", "", text, flags=re.S | re.I)
    t = re.sub(r"<style\b.*?</style>", "", t, flags=re.S | re.I)
    for m in re.finditer(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)\b[^>]*?(/?)>", t):
        closing, tag, selfclose = m.group(1), m.group(2).lower(), m.group(3)
        if tag in VOID or selfclose:
            continue
        d[tag] += -1 if closing else 1
    return {k: v for k, v in d.items() if v}


def wrap(h):
    """返回 (新 HTML, 包裹数量)。已包裹的块先摘出来避免二次包裹，处理完再放回。"""
    keep = []

    def stash(m):
        keep.append(m.group(0))
        return "\x00KEEP%d\x00" % (len(keep) - 1)

    h2 = RE_ALREADY.sub(stash, h)

    n = 0

    def repl(m):
        nonlocal n
        n += 1
        return ('<div class="cap-wrap">\n              ' + m.group(0)
                + "\n            </div>")

    h2 = RE_TABLE.sub(repl, h2)

    for i, blk in enumerate(keep):
        h2 = h2.replace("\x00KEEP%d\x00" % i, blk)
    return h2, n


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    files = collect_html()
    todo, done, unbal = [], [], []
    total = 0
    for p in files:
        h = io.open(p, encoding="utf-8").read()
        if 'class="cap-table"' not in h:
            continue
        rel = os.path.relpath(p, ROOT)
        n_exist = len(RE_ALREADY.findall(h))
        n_raw = len(RE_TABLE.findall(h))
        if n_exist and n_exist == n_raw:
            done.append(rel)
            continue
        h2, n = wrap(h)
        total += n
        if mode == "--verify":
            if n_raw != n_exist:
                unbal.append("%s: 表 %d / 已包裹 %d" % (rel, n_raw, n_exist))
            continue
        todo.append(rel)
        if mode != "--dry-run":
            b0, b1 = balance(h), balance(h2)
            if b0 != b1:
                unbal.append("%s: 标签配平变化 %s → %s" % (rel, b0, b1))
                io.open(p, "w", encoding="utf-8").write(h)   # 回滚，不留半成品
                todo.pop()
                continue
            io.open(p, "w", encoding="utf-8").write(h2)

    print("扫描页面 %d 个；含产能表 %d 个（已包裹 %d / 待包裹 %d）"
          % (len(files), len(done) + len(todo), len(done), len(todo)))
    print("本次包裹表格 %d 个" % total)
    if unbal:
        print("✗ 标签配平异常 %d 处：" % len(unbal))
        for x in unbal[:8]:
            print("   " + x)
        return 1
    if mode == "--verify":
        # 复核：包裹数与表格数一致，且 cap-wrap 内确实只有一张表
        bad = []
        for p in files:
            h = io.open(p, encoding="utf-8").read()
            if 'class="cap-table"' not in h:
                continue
            rel = os.path.relpath(p, ROOT)
            if len(RE_ALREADY.findall(h)) != len(RE_TABLE.findall(h)):
                bad.append(rel)
        print("包裹一致 =", "✓" if not bad else "✗ %s" % bad[:5])
        return 1 if bad else 0
    if mode != "--dry-run":
        for r in todo[:6]:
            print("   · %s" % r)
        if len(todo) > 6:
            print("   ... 共 %d 个" % len(todo))
    return 0


if __name__ == "__main__":
    sys.exit(main())
