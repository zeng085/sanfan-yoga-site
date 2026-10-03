#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自动定位「与远端树逐 blob 完全一致」的本地提交，用作推送起点。

为什么需要（2026-10-03 实战教训）：
  `verify_push_scope_20260927.py` 的第 2 步要求「远端树 vs 本地起点树 三类差异全 0」。
  起点必须是**上一次真正推上去的那个 commit**。手工维护 START 出了三次错：
    ① 推送后只改了 MEMORY.md，忘了改脚本里的 START → 下轮直接 FAIL
    ② 起点表被 Edit 工具插成重复行
    ③ 拿「远端 sha」当起点（远端 sha 在本地不存在，`git ls-tree` 会失败）
  本脚本把这件事自动化：拉一次远端树，遍历本地近期提交，逐 blob 比对，
  打印第一个完全一致的提交 —— 那就是起点。

用法：
    python i18n_build/find_push_base_20261003.py            # 打印结果
    python i18n_build/find_push_base_20261003.py --set      # 自动改写脚本里的 START
    python i18n_build/find_push_base_20261003.py --cache /tmp/rt.json  # 复用已拉取的树

判据铁律：
  · 远端树 >8MB，单次请求容易 IncompleteRead → 本脚本带重试 + 落盘缓存
  · 「同名内容不同」必须为 0；记忆文件（.workbuddy/memory/*）也算内容，
    所以「差几个记忆文件」= 那些是待推内容，**不是起点错**，别硬凑
"""
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

REPO = "zeng085/sanfan-yoga-site"
SELF = "i18n_build/verify_push_scope_20260927.py"
DEPTH = 20


def sh(*args):
    return subprocess.run(list(args), capture_output=True, text=True).stdout


def fetch_remote_tree(cache="/tmp/remote_tree_cache.json"):
    """拉远端 main 的 tree（带重试；大响应易 IncompleteRead）。"""
    if cache and os.path.isfile(cache):
        try:
            d = json.load(open(cache, encoding="utf-8"))
            if "tree" in d:
                return d
        except Exception:
            pass
    pat = os.path.expanduser("~/.workbuddy/secrets/gh_pat")
    token = io.open(pat, encoding="utf-8").read().strip() if os.path.isfile(pat) else ""
    hdr = {"Accept": "application/vnd.github+json", "User-Agent": "findbase"}
    if token:
        hdr["Authorization"] = "Bearer " + token
    last = None
    for i in range(4):
        try:
            url = f"https://api.github.com/repos/{REPO}/git/trees/main?recursive=1"
            r = urllib.request.Request(url, headers=hdr)
            data = json.loads(urllib.request.urlopen(r, timeout=180).read().decode())
            if cache:
                json.dump(data, open(cache, "w", encoding="utf-8"))
            return data
        except Exception as e:                      # 网络抖动 / 响应不完整
            last = e
            sys.stderr.write("  拉树第 %d 次失败：%s\n" % (i + 1, str(e)[:60]))
            time.sleep(3)
    raise last


def main():
    args = sys.argv[1:]
    cache = None
    if "--cache" in args:
        cache = args[args.index("--cache") + 1]

    print("拉取远端树…")
    d = fetch_remote_tree(cache)
    rem = {e["path"]: e["sha"] for e in d["tree"] if e["type"] == "blob"}
    if d.get("truncated"):
        print("⚠️ 远端树被截断（truncated=True），比对结果不可信 —— 改用逐文件核对")
        return 2
    print("远端 blob = %d" % len(rem))

    log = sh("git", "log", "--format=%H %s", "-%d" % DEPTH).strip()
    rows, best = [], None
    for line in log.split("\n"):
        if not line.strip():
            continue
        sha, subj = line.split(" ", 1)
        out = sh("git", "ls-tree", "-r", sha)
        loc = {}
        for l in out.splitlines():
            if "\t" in l:
                parts = l.split()
                if len(parts) >= 3:
                    loc[l.split("\t", 1)[1]] = parts[2]
        only_r = len(set(rem) - set(loc))
        only_l = len(set(loc) - set(rem))
        diff = len([p for p in set(rem) & set(loc) if rem[p] != loc[p]])
        ok = (only_r == 0 and only_l == 0 and diff == 0)
        rows.append((sha, subj, only_r, only_l, diff, ok))
        if ok and best is None:
            best = (sha, subj)
        if ok and best is not None and len(rows) > 3:
            break                                   # 找到最近的即可，不必全扫

    print("\n%-10s %5s %5s %6s  %s" % ("commit", "仅远", "仅本", "异", "说明"))
    for sha, subj, a, b, c, ok in rows:
        print("%-10s %5d %5d %6d  %-44s %s" % (sha[:9], a, b, c, subj[:42],
                                              "✅ 可作起点" if ok else ""))

    if not best:
        print("\n❌ 本地没有与远端树完全一致的提交 —— 需人工核对（是否漏推或误 reset）")
        return 1

    print("\n★ 起点 = %s  %s" % (best[0][:9], best[1][:50]))
    if "--set" in args:
        s = io.open(SELF, encoding="utf-8").read()
        s2, n = re.subn(r'^START = "[0-9a-f]+"', 'START = "%s"' % best[0][:8],
                        s, count=1, flags=re.M)
        if n != 1:
            print("✗ 未找到 START 行，未改动")
            return 1
        io.open(SELF, "w", encoding="utf-8").write(s2)
        print("  已把 %s 的 START 改为 %s" % (SELF, best[0][:8]))
        print("  ⚠️ 起点表（注释里的历史行）仍需手工补一条：")
        print("     #   %s → <远端 sha>   （本次推送内容，文件数，日期）" % best[0][:8])
    return 0


if __name__ == "__main__":
    sys.exit(main())
