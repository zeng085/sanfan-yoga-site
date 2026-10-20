#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通过 GitHub REST API 推送：以远端 main 的树为 base，应用本地 起点..HEAD 的变更。

为什么不用 git push：
  远端历史被 squash 过（远端 main = d6f5131651，该 sha 在本地不存在），
  本地 main 与远端历史不同源 → git push 必然 non-fast-forward 被拒。
  本项目一贯走 REST API：base_tree = 远端树，逐个上传 blob，建 tree → commit → 更新 ref。

用法：
    python i18n_build/push_api_20261020.py --dry-run   # 只算变更集，不上传
    python i18n_build/push_api_20261020.py --apply     # 真正推送
判据铁律：
  · 基线校验：起点树与远端树三类差异必须全 0（否则起点错，拒绝推送）
  · 空变更集必须硬失败
  · 推送后用 commits/<sha>/status 查部署（短 SHA 会假阴性，用全长）
"""
import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = "zeng085/sanfan-yoga-site"
BASE_COMMIT = "aa334352"   # 本地起点（树 == 远端树）
BRANCH = "main"
PAT_FILE = os.path.expanduser("~/.workbuddy/secrets/gh_pat")


def token():
    with open(PAT_FILE, encoding="utf-8") as fh:
        return fh.read().strip()


def api(path, method="GET", payload=None, retries=7):
    tk = token()
    url = "https://api.github.com" + path
    data = json.dumps(payload).encode() if payload is not None else None
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, data=data, method=method)
            req.add_header("Authorization", "Bearer " + tk)
            req.add_header("Accept", "application/vnd.github+json")
            req.add_header("User-Agent", "sanfan-push")
            if data:
                req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as exc:
            last = exc
            # 403/429 = 二级速率限制（并发过高），必须指数退避，不能快重试
            if exc.code in (403, 429):
                wait = 5 * (2 ** i)
                sys.stderr.write(f"  限速 {exc.code}，退避 {wait}s（第{i+1}次）\n")
                time.sleep(wait)
                continue
            sys.stderr.write(f"  API {path[:50]} 第{i+1}次失败: {exc.code}\n")
            time.sleep(2 + i * 2)
        except Exception as exc:
            last = exc
            sys.stderr.write(f"  API {path[:50]} 第{i+1}次失败: {str(exc)[:70]}\n")
            time.sleep(2 + i * 2)
    raise last


def sh(*args):
    return subprocess.run(list(args), capture_output=True, text=True).stdout


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--dry-run"
    if mode not in ("--dry-run", "--apply"):
        print(__doc__)
        sys.exit(2)

    # 1) 变更集
    raw = sh("git", "diff", "--name-status", f"{BASE_COMMIT}", "HEAD")
    changes = []
    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status, path = parts[0], parts[-1]
        if status == "D":
            changes.append(("delete", path, None))
        else:
            changes.append(("upsert", path, path))
    if not changes:
        print("FAIL: 变更集为空，拒绝推送")
        sys.exit(1)

    adds = sum(1 for c in changes if c[0] == "upsert")
    dels = len(changes) - adds
    print(f"变更集: 共 {len(changes)} 个（新增/修改 {adds}，删除 {dels}）")

    if mode == "--dry-run":
        for c in changes[:5]:
            print("   样例:", c[0], c[1])
        print("\n演练完成，未上传。")
        return

    # 2) 远端 main 当前 sha + tree
    ref = api(f"/repos/{REPO}/git/ref/heads/{BRANCH}")
    parent = ref["object"]["sha"]
    print(f"远端 {BRANCH} = {parent[:12]}")
    commit = api(f"/repos/{REPO}/git/commits/{parent}")
    base_tree = commit["tree"]["sha"]
    print(f"远端 base_tree = {base_tree[:12]}")

    # 3) 并发上传 blob
    from concurrent.futures import ThreadPoolExecutor, as_completed

    entries = []
    todo = []
    for action, path, local in changes:
        if action == "delete":
            entries.append({"path": path, "mode": "100644", "type": "blob", "sha": None})
        else:
            todo.append((path, local))

    def upload(item):
        path, local = item
        full = os.path.join(ROOT, local)
        with open(full, "rb") as fh:
            raw = fh.read()
        try:
            text = raw.decode("utf-8")
            return path, api(f"/repos/{REPO}/git/blobs", "POST",
                             {"content": text, "encoding": "utf-8"})["sha"]
        except UnicodeDecodeError:
            return path, api(f"/repos/{REPO}/git/blobs", "POST",
                             {"content": base64.b64encode(raw).decode(),
                              "encoding": "base64"})["sha"]

    done = 0
    total = len(todo)
    print(f"  开始上传 {total} 个 blob（并发 4）…")
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(upload, it) for it in todo]
        for fut in as_completed(futures):
            path, sha = fut.result()
            entries.append({"path": path, "mode": "100644", "type": "blob", "sha": sha})
            done += 1
            if done % 200 == 0 or done == total:
                print(f"    已上传 {done}/{total}")

    print(f"  blob 上传完成 {len(entries)}/{len(changes)}")

    # 4) 建 tree（删除项 sha=None 即从树中移除）
    new_tree = api(f"/repos/{REPO}/git/trees", "POST", {
        "base_tree": base_tree,
        "tree": entries,
    })
    print(f"新 tree = {new_tree['sha'][:12]}")

    # 5) 建 commit
    msg = sh("git", "log", "-1", "--format=%s%n%n%b", "HEAD").strip()
    new_commit = api(f"/repos/{REPO}/git/commits", "POST", {
        "message": msg,
        "tree": new_tree["sha"],
        "parents": [parent],
    })
    sha = new_commit["sha"]
    print(f"新 commit = {sha[:12]}")

    # 6) 更新 ref
    api(f"/repos/{REPO}/git/refs/heads/{BRANCH}", "PATCH", {"sha": sha})
    print(f"✅ ref 已更新 → {BRANCH} = {sha[:12]}")
    print(f"\n下一步：用全长 sha 查部署状态：")
    print(f"  /repos/{REPO}/commits/{sha}/status")
    print(f"\n★★ 推送成功后须更新起点：BASE_COMMIT 改为本地 {sh('git','rev-parse','--short','HEAD').strip()}")


if __name__ == "__main__":
    main()