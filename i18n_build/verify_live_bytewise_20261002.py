#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""线上 ⇄ 本地 逐字节一致性复核（2026-10-02 新建）

为什么要它：
  推送后判「线上是否已更新」的常规判据是**资源版本号**（`styles.css?vNNNNNNNx`）。
  但只要本轮**没改 CSS/JS**（因而不 bump 版本号），该信号就是一个恒等值 ——
  线上新旧版本号相同，「已切换」这个结论**无法证明任何事**。

  逐字节比对没有这个前提依赖：它直接回答「线上这份文件，是否就是我刚推上去的那份」。

判据强度对比（同一批页面）：
  · 资源版本号        —— 只能证明 CSS/JS 切了；不改 CSS/JS 时失效      （弱，有前提）
  · 关键字符串断言    —— 依赖我手写对「正确的字符串」的假设           （中，我曾写错 → 假失败）
  · 本地⇄线上逐字节   —— 无假设，完全等价于「部署产物 == 本地产物」    （强，首选）

⚠️ 一个必须做、又最容易漏的归一化：**CRLF → LF**
  推送管道会把文本 CRLF 归一为 LF，所以线上比本地少 N 个字节。
  实测：全仓唯一 CRLF 文件曾被归一，导致 blob 永不一致。
  本脚本对两侧都做 `\\r\\n -> \\n` 再比，避免把它误报成「没更新」。

⚠️ 另一个坑：**相对路径必须按页面所在目录解析**
  博客页里写的是 `../assets/css/styles.css`，直接拼 `BASE + 该字符串` 会构出
  `/../assets/...` 这种无效 URL，HEAD 恒返回 0，看着像「资源 404」——
  实际是我的探针错了。本脚本只处理页面正文，不做资源解析（资源 404 体检另见
  `probe` 类脚本，那里务必用 `urljoin(页面URL, 相对路径)`）。

用法：
    python i18n_build/verify_live_bytewise_20261002.py                 # 取起点..HEAD 的变更集
    python i18n_build/verify_live_bytewise_20261002.py blog/a.html robots.txt
    python i18n_build/verify_live_bytewise_20261002.py --rev f7760479  # 自定起点

退出码：全一致 = 0；有不一致/取不到 = 1（可直接当闸用）。
"""
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

BASE = "https://fjsanfan.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
START_DEFAULT = "7d293b52"      # 与 verify_push_scope_20260927.py 的 START 同步
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 Chrome/120 Safari/537.36"}
TIMEOUT = 45
TRIES = 4


def changed_paths(start):
    """起点..HEAD 的变更集（--no-renames：rename 必须拆成 D+A）。"""
    out = subprocess.run(
        ["git", "diff", "--name-only", "--no-renames", f"{start}..HEAD"],
        cwd=ROOT, capture_output=True, text=True).stdout
    return [p for p in out.splitlines() if p.strip()]


def fetch(path):
    url = f"{BASE}/{path.lstrip('/')}"
    for i in range(TRIES):
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(url, headers=UA), timeout=TIMEOUT) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, b""
        except Exception:
            if i == TRIES - 1:
                return 0, b""
            time.sleep(3)
    return 0, b""


def norm(b):
    """CRLF → LF：推送管道会归一，两侧都归一再比才公平。"""
    return b.replace(b"\r\n", b"\n")


def main():
    argv = sys.argv[1:]
    start = START_DEFAULT
    if "--rev" in argv:
        i = argv.index("--rev")
        start = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]

    paths = argv or changed_paths(start)
    if not paths:
        print("没有待复核的文件。")
        return 0

    print(f"起点 {start} → HEAD；待复核 {len(paths)} 个文件")
    print(f"{'文件':52s} {'HTTP':>5s} {'线上':>9s} {'本地':>9s}  判定")
    bad = []
    for p in paths:
        local_path = os.path.join(ROOT, p)
        if not os.path.exists(local_path):
            print(f"{p:52s} {'—':>5s} {'':>9s} {'':>9s}  ⏭ 本地不存在（已删除文件，跳过）")
            continue
        st, body = fetch(p)
        lb = norm(open(local_path, "rb").read())
        rb = norm(body)
        ok = st == 200 and rb == lb
        if not ok:
            bad.append((p, st, len(rb), len(lb)))
        print(f"{p:52s} {st:>5} {len(rb):>9} {len(lb):>9}  {'✓ 一致' if ok else '✗ 不一致'}")

    print()
    if bad:
        print(f"✗ {len(bad)} 个文件不一致：")
        for p, st, a, b in bad:
            print(f"   {p}  HTTP {st}  线上 {a}B / 本地 {b}B")
        return 1
    print("★ 全部逐字节一致 —— 部署产物 == 本地产物")
    return 0


if __name__ == "__main__":
    sys.exit(main())
