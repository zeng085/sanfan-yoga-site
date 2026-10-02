#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地资源引用体检（2026-10-03 新建）

两条判据（都是「源码看不出来、线上才发现」的类型）：
  ① 引用指向的文件**不存在** → 线上 404（macOS 不区分大小写、Vercel 区分，本地能开线上也能 404）
  ② 引用指向的文件**存在但 git 未跟踪** → 不会被推送，同样线上 404
     （10-01 实测过：全站 2503 个 HTML 引用里恰好 3 张画册图未跟踪，线上确为 404）

用法：
    python3 i18n_build/verify_local_refs_20261003.py --rev 7d293b52..HEAD
    python3 i18n_build/verify_local_refs_20261003.py --rev 7d293b52..HEAD --debug 5
退出码：有问题 = 1；无任何 HTML 可查 = 3（拒绝判定为通过）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINK = re.compile(r'(?:href|src)="([^"]+)"')
SKIP_PREFIX = ("http", "//", "mailto:", "tel:", "data:", "javascript:", "blob:", "#")


def changed_files(rev):
    out = subprocess.run(["git", "diff", "--name-only", "--no-renames", rev],
                         cwd=ROOT, capture_output=True, text=True).stdout
    return [x for x in out.split("\n") if x.strip()]


def tracked_files():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT,
                         capture_output=True, text=True).stdout
    return set(x for x in out.split("\n") if x)


def resolve(page_rel, u):
    """把页面里的引用解析成仓库内相对路径（目录形式补 index.html）。

    ⚠️ 绝对路径分支必须显式处理空串：`href="/"` → lstrip("/") 得 ''，
    若再 undergo normpath 会变成 '.'，拼出 './index.html' —— 与 tracked 集合里的
    'index.html' **字符串不相等**，于是把根链接误报成「未跟踪资源」。
    （2026-10-03 实测：一次临时探针就这样报了 32 处假警报，全部是 16 个博客页的
     logo 和首页链接。判据本身没错，是探针的路径归一错了。）
    """
    u = u.split("#")[0].split("?")[0]
    if not u:
        return None
    if u.startswith("/"):
        cand = u.lstrip("/")
        if cand == "" or u.endswith("/"):
            cand = os.path.normpath(os.path.join(cand, "index.html"))
    else:
        cand = os.path.normpath(os.path.join(os.path.dirname(page_rel), u))
        if u.endswith("/") or os.path.isdir(os.path.join(ROOT, cand)):
            cand = os.path.join(cand, "index.html")
    return cand


def main():
    rev = None
    debug = 0
    a = sys.argv[1:]
    for i, x in enumerate(a):
        if x == "--rev":
            rev = a[i + 1]
        if x == "--debug":
            debug = int(a[i + 1])
    if not rev:
        print("需要 --rev <起点>..<终点>")
        return 2
    files = [f for f in changed_files(rev) if f.endswith(".html")]
    if not files:
        print("✗ 变更集里没有 HTML —— 拒绝判定为通过（退出码 3）")
        return 3
    tracked = tracked_files()
    missing, untracked = [], []
    n_ref = 0
    for rel in files:
        abs_p = os.path.join(ROOT, rel)
        if not os.path.isfile(abs_p):
            continue
        h = io.open(abs_p, encoding="utf-8").read()
        for raw in LINK.findall(h):
            if raw.startswith(SKIP_PREFIX):
                continue
            cand = resolve(rel, raw)
            if cand is None:
                continue
            n_ref += 1
            if not os.path.exists(os.path.join(ROOT, cand)):
                missing.append((rel, raw, cand))
            elif os.path.isfile(os.path.join(ROOT, cand)) and cand not in tracked:
                untracked.append((rel, raw, cand))
    print("变更集 HTML %d 个 / 本地引用 %d 条（rev=%s）" % (len(files), n_ref, rev))
    print("① 引用不存在的文件      = %d" % len(missing))
    for rel, raw, cand in missing[:10]:
        print("     %s  →  %r  (解析为 %s)" % (rel, raw, cand))
    print("② 存在但 git 未跟踪     = %d" % len(untracked))
    for rel, raw, cand in untracked[:10]:
        print("     %s  →  %r  (解析为 %s)" % (rel, raw, cand))
    if debug:
        print("   debug 抽样（前 %d 条解析）:" % debug)
        shown = 0
        for rel in files:
            abs_p = os.path.join(ROOT, rel)
            if not os.path.isfile(abs_p):
                continue
            for raw in LINK.findall(io.open(abs_p, encoding="utf-8").read()):
                if raw.startswith(SKIP_PREFIX):
                    continue
                print("     %s | %r → %s" % (rel, raw, resolve(rel, raw)))
                shown += 1
                if shown >= debug:
                    break
            if shown >= debug:
                break
    bad = len(missing) + len(untracked)
    print("结论：%s" % ("本地引用全部落地且已跟踪 ✓" if not bad else "有 %d 条风险引用 ✗" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
