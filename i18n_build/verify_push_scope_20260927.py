#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""推送起点判定三步法（2026-09-27）

用途：推送前确定性确认「起点对齐」并生成准确推送清单。
  第1步 远程 HEAD message 匹配本地 commit（人工判读）
  第2步 远程 tree vs 本地起点 tree 逐 blob sha 比对 —— 三类差异必须全 0
  第3步 推送清单两法交叉验证：远程树 vs 本地 HEAD 树 / git diff --no-renames

不用 git fetch（github.com 直连不稳定），全程走 api.github.com。
"""
import os
import subprocess
import sys
import json
import urllib.request

REPO = "zeng085/sanfan-yoga-site"
ROOT = "/Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16"
START = "4f500138"          # 上次已推的本地 commit（起点）
# ⚠️ 起点表（本地 commit → 远程 sha），每次推送成功后更新这里 + MEMORY.md：
#   0d10b7d9 → b94f9879d5   （分类页 1381 文件，09-26）
#   41e1ff5a → ba4fa0cc52   （移动端 P0 五处 + P1 三项，1370 文件，09-27）
#   a19e4a0b → 7705a32b6d   （普拉提 9 页画册重构，1445 文件，10-01）
#   02d6e1ab → 1188a4c463   （灯箱标题修复 + ladder-barrel 接灯箱，1336 文件，10-01）
#   f53ca5a1 → b57d64c7ce   （排版修复 + 全站表格 + desc 改写 + CSV 转 LF，1339 文件，10-01）
#   1853d5a2 → 8b31f81a2a   （缩略图墙 + 规格表折叠，1340 文件，10-01）
#   f7760479 → 5556e3a39b   （画册墙改默认显示，1336 文件，10-01）
#   3179ac0e → 1e5773d15a   （6 篇普拉提博客 + GEO 改进 P1/P2/P3，26 文件，10-02）
#   7d293b52 → da405b305e   （GLM 翻译引擎链 + hero 海报裁剪 bump 20261002a + 拆批重试，1352 文件，10-02）
#   4f500138 → 72b57aa193   （90 页语言版 + 校验链加固：静默通过/locale 数字/三处一致，187 文件，10-03）
OUT = "i18n_build/reports/push_list_20260927.txt"

# ⚠️ 已知假警报（2026-10-02 实测，别被它拦住）：
#   第 2 步会稳定报 1 处「同名内容不同」= OUT 这个文件自己。
#   原因：本脚本每次运行都会重写 OUT，而起点 commit 里冻结的是**更早一次**运行的结果
#   （如 f7760479 存的是 1340 行版，而远程/HEAD 是 1336 行版，blob c97cc764 vs ac500b3a）。
#   判据（已闭环实证，三步都做）：
#     ① 两侧 blob 总数相等、「仅远程有」「仅本地有」全 0  → 无文件级遗漏
#     ② 取远程该 blob 反解文本，与起点版逐行 diff → 差异**全部是清单里的文件路径行**
#     ③ 那些「从清单消失」的文件去远程树里查 → **依然存在**（证明只是清单内容变了，不是文件丢了）
#   缓解：推送前把 OUT 恢复到 HEAD 版（`git checkout -- <OUT>`），
#   使「起点 tree 的 OUT」= 「远程 blob」，下一轮第 2 步即可三类差异全 0。
#   根因治理（未做）：OUT 是产物，不宜跟踪；或让它落在 .gitignore 覆盖处并不 force-add。

PAT = os.environ["GH_PAT"]
HDR = {"Authorization": f"Bearer {PAT}",
       "Accept": "application/vnd.github+json",
       "User-Agent": "verify-push"}


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers=HDR)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def ls_tree(rev):
    out = subprocess.run(["git", "ls-tree", "-r", rev],
                         cwd=ROOT, capture_output=True).stdout.decode()
    d = {}
    for line in out.splitlines():
        meta, path = line.split("\t", 1)
        d[path] = meta.split()[2]
    return d


def remote_blobs():
    ref = api(f"/repos/{REPO}/git/ref/heads/main")["object"]["sha"]
    c = api(f"/repos/{REPO}/git/commits/{ref}")
    t = api(f"/repos/{REPO}/git/trees/{c['tree']['sha']}?recursive=1")
    d = {e["path"]: e["sha"] for e in t["tree"] if e["type"] == "blob"}
    return ref, c, d, t.get("truncated", False)


rem_ref, rem_commit, rem, trunc = remote_blobs()
loc_start = ls_tree(START)
loc_head = ls_tree("HEAD")

print("=" * 68)
print("第1步  远程 HEAD")
print(f"  sha    {rem_ref[:12]}")
print(f"  msg    {rem_commit['message'].splitlines()[0]}")
print(f"  date   {rem_commit['committer']['date']}")
print(f"  tree   {rem_commit['tree']['sha'][:12]}  truncated={trunc}")

print("=" * 68)
print(f"第2步  起点对齐验证  本地起点 = {START}")
print(f"  本地起点 blob 数 {len(loc_start)}   远程 blob 数 {len(rem)}")
only_remote = sorted(set(rem) - set(loc_start))
only_local = sorted(set(loc_start) - set(rem))
diff = sorted(p for p in set(rem) & set(loc_start) if rem[p] != loc_start[p])
print(f"  仅远程有 {len(only_remote)} / 仅本地有 {len(only_local)} / 同名内容不同 {len(diff)}")
for tag, lst in (("仅远程", only_remote), ("仅本地", only_local), ("内容不同", diff)):
    for p in lst[:10]:
        print(f"    [{tag}] {p}")
    if len(lst) > 10:
        print(f"    [{tag}] ... 共 {len(lst)}")
START_OK = not (only_remote or only_local or diff)
print(f"  => 起点{'对齐 ✓' if START_OK else '未对齐 ✗ ——先查清再推'}")

print("=" * 68)
print("第3步  推送清单（远程树 vs 本地 HEAD 树）")
add = sorted(set(loc_head) - set(rem))
dele = sorted(set(rem) - set(loc_head))
mod = sorted(p for p in set(rem) & set(loc_head) if rem[p] != loc_head[p])
print(f"  新增 {len(add)} / 修改 {len(mod)} / 删除 {len(dele)}  (合计 {len(add)+len(mod)+len(dele)})")

diff_files = subprocess.run(
    ["git", "diff", "--name-only", "--no-renames", f"{START}..HEAD"],
    cwd=ROOT, capture_output=True).stdout.decode().split()
set_b = set(diff_files)
set_a = set(add) | set(mod) | set(dele)
print(f"  法二 git diff {START}..HEAD 文件数 {len(set_b)}")
print(f"  两法差异 {len(set_a ^ set_b)}")
for p in sorted(set_a ^ set_b)[:20]:
    print(f"    [差异] {p}")

changed = sorted(set_a)
os.makedirs(os.path.dirname(os.path.join(ROOT, OUT)), exist_ok=True)
with open(os.path.join(ROOT, OUT), "w") as f:
    f.write("\n".join(changed) + "\n")
print(f"  清单已写 {OUT}  ({len(changed)} 行)")

print("=" * 68)
print(f"结论: 起点{'OK' if START_OK else 'FAIL'} / 两法{'一致' if not (set_a ^ set_b) else '不一致'}")
if (only_remote or only_local or diff or (set_a ^ set_b)) and len(changed) > 2000:
    print("  ⚠ 差异过大，先别推")
sys.exit(0 if START_OK and not (set_a ^ set_b) else 2)
