#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""改动页链接体检 —— 2026-10-01

对 `git diff --name-only` 里的每个 HTML 文件：
  1. 抽出全部 <a href> / <img src> / <link href> / <script src>
  2. 内部链接（非 http/data/mailto/tel/#）解析为磁盘路径，检查目标是否存在
     · 以 / 开头 → 相对仓库根
     · 否则 → 相对该文件所在目录
     · 目录型（/pilates/）→ 找 index.html
     · 带 #anchor → 去掉锚点后判文件，并单独校验锚点 id 是否存在于目标文件
  3. 形式异常：href="href="、空 href、纯 "#"、href="javascript:;"、双斜杠
  4. 重复 id（页面内），因为画册块新增了 7 个 id 锚点

只做只读检查，不改任何文件。
"""
import os
import pathlib
import re
import subprocess
import sys
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
PRUNE = {".git", "outputs", "node_modules", "__pycache__"}


def changed_html():
    out = subprocess.run(["git", "diff", "--no-renames", "--name-only"],
                         cwd=ROOT, capture_output=True, text=True).stdout
    return [p for p in out.split() if p.endswith(".html")]


A_RE = re.compile(r'<a\b[^>]*?\bhref="([^"]*)"', re.I)
IMG_RE = re.compile(r'<img\b[^>]*?\bsrc="([^"]*)"', re.I)
LINK_RE = re.compile(r'<link\b[^>]*?\bhref="([^"]*)"', re.I)
SRC_RE = re.compile(r'<script\b[^>]*?\bsrc="([^"]*)"', re.I)
ID_RE = re.compile(r'\bid="([^"]+)"')

SKIP_SCHEME = ("http://", "https://", "data:", "mailto:", "tel:", "javascript:",
               "//", "whatsapp:", "sms:")


def resolve(raw, page):
    """返回 (磁盘路径 或 None, 锚点 或 None, 是否为内部)"""
    if raw == "":
        return None, None, True
    low = raw.lower()
    if low.startswith(SKIP_SCHEME):
        return None, None, False
    anchor = None
    body = raw
    if "#" in raw:
        body, anchor = raw.split("#", 1)
    if body == "":
        return page, anchor, True           # 纯锚点 → 指向本页
    # ⚠️ 必须先剥离 query（?v20260927b）—— 否则磁盘路径带 ?query 必然不存在，
    #    会把全站每个资源引用都报成断链（探针自身误报，实测 42 条全是这个）
    if "?" in body:
        body = body.split("?", 1)[0]
    if body == "":
        return None, anchor, False          # 只剩 query，不可解析
    if body.startswith("/"):
        p = ROOT / body.lstrip("/")
    else:
        p = (page.parent / body)
    p = pathlib.Path(os.path.normpath(str(p)))
    if str(p).endswith("/") or p.is_dir():
        p = p / "index.html"
    return p, anchor, True


def main():
    files = changed_html()
    print("改动 HTML 文件：%d 个\n" % len(files))
    missing = []
    malformed = []
    anchor_bad = []
    dup_ids = []
    check_counts = Counter()
    out_of_scope = []

    # 允许链接到工作区外（比如站点根以外的绝对路径）——只报确实不存在的
    for rel in files:
        page = ROOT / rel
        if not page.exists():
            print("  !! 文件不存在：%s" % rel)
            continue
        text = page.read_text("utf-8", "ignore")

        # 4. 页面内重复 id
        ids = ID_RE.findall(text)
        for k, v in Counter(ids).items():
            if v > 1:
                dup_ids.append((rel, k, v))

        for rx, kind in ((A_RE, "a[href]"), (IMG_RE, "img[src]"),
                         (LINK_RE, "link[href]"), (SRC_RE, "script[src]")):
            for m in rx.finditer(text):
                raw = m.group(1).strip()
                check_counts[kind] += 1
                # 3. 形式异常
                if raw.startswith("href=") or raw.startswith("src="):
                    malformed.append((rel, kind, raw[:80], "重复前缀"))
                    continue
                if raw == "" and kind != "a[href]":
                    malformed.append((rel, kind, raw, "空值"))
                    continue
                if raw == "#" and kind == "a[href]":
                    malformed.append((rel, kind, raw, '纯 "#" 死链'))
                    continue
                if raw.startswith("/") and raw.startswith("//"):
                    malformed.append((rel, kind, raw[:80], "协议相对，可能非本意"))

                target, anchor, internal = resolve(raw, page)
                if not internal:
                    continue
                if target is None:
                    continue
                if not target.exists():
                    # 目标在仓库外 → 单独归类
                    try:
                        target.relative_to(ROOT)
                        inrepo = True
                    except ValueError:
                        inrepo = False
                    missing.append((rel, kind, raw, str(target), "仓内缺失" if inrepo else "仓外路径"))
                    continue
                if anchor and target.suffix == ".html":
                    ttext = target.read_text("utf-8", "ignore")
                    if ('id="%s"' % anchor) not in ttext and ("name=\"%s\"" % anchor) not in ttext:
                        anchor_bad.append((rel, raw, anchor, str(target.relative_to(ROOT))))

    print("=== 1. 引用总数 ===")
    for k, v in check_counts.items():
        print("   %-12s %d" % (k, v))

    print("\n=== 2. 断链（目标文件不存在） ===")
    if missing:
        for rel, kind, raw, tgt, tag in missing:
            print("   [%s] %s  %s\n         → %s  <%s>" % (tag, rel, kind, raw[:90], tgt))
    else:
        print("   无 ✅")

    print("\n=== 3. 形式异常链接 ===")
    if malformed:
        for rel, kind, raw, why in malformed:
            print("   %s  %s  %r  (%s)" % (rel, kind, raw, why))
    else:
        print("   无 ✅")

    print("\n=== 4. 锚点指向的 id 不存在 ===")
    if anchor_bad:
        for rel, raw, a, tgt in anchor_bad:
            print("   %s → %s  (#%s 不在 %s)" % (rel, raw, a, tgt))
    else:
        print("   无 ✅")

    print("\n=== 5. 页面内重复 id ===")
    if dup_ids:
        for rel, k, v in dup_ids:
            print("   %s  id=%r  出现 %d 次" % (rel, k, v))
    else:
        print("   无 ✅")

    bad = len(missing) + len(malformed) + len(anchor_bad) + len(dup_ids)
    print("\n结论：%s（问题合计 %d）" % ("全部通过 ✅" if bad == 0 else "存在问题 ⚠️", bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
