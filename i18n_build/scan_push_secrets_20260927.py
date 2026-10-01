#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""推送前闸二：内容级敏感形态扫描（2026-09-27）

⭐ 关键教训：**不要在 Python 里逐个 open() 扫全站**。
初版这么写（1370 文件含 1331 个 HTML）→ 被 SIGTERM **静默杀掉（exit 137）**，
一行输出都没有，极易误读成「干净」。改用 `git grep` 在**仓库对象**上扫，秒级完成。

用法：
    python3 scan_push_secrets_20260927.py            # 扫 HEAD 全树
    python3 scan_push_secrets_20260927.py --list <清单文件>   # 只扫清单内的文件（更贴题）

输出命中行 + 需人工过目的笔记类文件 + 仓库 visibility。
退出码：0 无命中 / 1 有命中。
"""
import os
import subprocess
import sys
import json
import urllib.request

ROOT = "/Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16"
REPO = "zeng085/sanfan-yoga-site"

# key 形态（合并为一条 ERE 交给 git grep；-I 跳过二进制）
PATTERN = (
    r"ghp_[A-Za-z0-9]{20,}"
    r"|github_pat_[A-Za-z0-9_]{20,}"
    r"|[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}:fx"
    r"|sk-[A-Za-z0-9]{20,}"
    r"|[0-9]{8,12}:AA[A-Za-z0-9_-]{30,}"
    r"|AKIA[0-9A-Z]{16}"
    r"|BEGIN [A-Z ]*PRIVATE KEY"
)

# 闸一：按文件名（清单模式用得上）
NAME_PATTERN = r"deepl|secret|\.key|token|password|\.env|credential"


def git_grep(pattern, paths=None):
    cmd = ["git", "grep", "-n", "-I", "-E", pattern, "HEAD"]
    cmd += ["--"] + (paths if paths else ["."])
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True)
    return r.stdout.decode("utf-8", "ignore").splitlines()


def main():
    paths = None
    if len(sys.argv) >= 3 and sys.argv[1] == "--list":
        with open(sys.argv[2]) as f:
            paths = [l.strip() for l in f if l.strip()]
        print(f"模式：只扫清单 {len(paths)} 个文件")

    print("=" * 68)
    print("闸一  按文件名")
    hits_name = git_grep(NAME_PATTERN, paths)
    print(f"  {len(hits_name)} 命中（仅为「名字含关键词」，多数是路径/文档用词）")
    for l in hits_name[:20]:
        print(f"    {l[:150]}")

    print("=" * 68)
    print("闸二  按内容（key 形态）")
    hits = git_grep(PATTERN, paths)
    print(f"  {len(hits)} 命中")
    for l in hits[:40]:
        print(f"    {l[:150]}")
    if len(hits) > 40:
        print(f"    ... 共 {len(hits)}")
    if not hits:
        print("  ✓ 全树无凭据形态")

    print("=" * 68)
    print("需人工过目的笔记类文件（最容易出现凭据明文）")
    r = subprocess.run(["git", "ls-tree", "-r", "--name-only", "HEAD", "--",
                        ".workbuddy/memory/"], cwd=ROOT, capture_output=True)
    notes = [l for l in r.stdout.decode().splitlines() if l.endswith(".md")]
    print(f"  .workbuddy/memory/ 下 {len(notes)} 个 md，最新 3 个：")
    for n in notes[-3:]:
        sz = len(subprocess.run(["git", "show", f"HEAD:{n}"], cwd=ROOT,
                                capture_output=True).stdout)
        print(f"    {n}  {sz} bytes")
    print("  ⚠️ 逐个过目是否有密码 / IP+凭据 / token 明文（方法论文like「token」不算）")

    print("=" * 68)
    try:
        pat = os.environ.get("GH_PAT") or open(
            os.path.expanduser("~/.workbuddy/secrets/gh_pat")).read().strip()
        req = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}",
            headers={"Authorization": f"Bearer {pat}",
                     "Accept": "application/vnd.github+json",
                     "User-Agent": "sec-scan"})
        with urllib.request.urlopen(req, timeout=30) as x:
            d = json.loads(x.read().decode())
        print(f"仓库 visibility = {d.get('visibility')}  (private = {d.get('private')})")
    except Exception as e:
        print(f"仓库可见性查询失败：{e}")

    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
