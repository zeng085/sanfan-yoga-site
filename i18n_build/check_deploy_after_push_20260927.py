#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""推送后部署触发判定 + 线上实测复核（2026-09-27）

背景：Vercel 的 GitHub webhook 实测会漏触发（2026-09-14 实测过一次）。
本脚本轮询 GitHub deployments，若 5 分钟内无对应 sha 的 deployment，
给出「需发空提交重触发」的明确结论；有则继续 curl 线上资源复核版本号。
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

REPO = "zeng085/sanfan-yoga-site"
# 用法：GH_PAT=... python3 check_deploy_after_push_20260927.py <sha> <期望版本号>
#   例：... a19e4a0b... v20261001b
# 不传则回落到 2026-09-27 那轮的默认值（保持向后可用）。
SHA = sys.argv[1] if len(sys.argv) > 1 else \
    "ba4fa0cc525f6cb624ecd61d92d7c624dee2837f"
WANT_VER = sys.argv[2] if len(sys.argv) > 2 else "v20260927b"
PAT = os.environ["GH_PAT"]
HDR = {"Authorization": f"Bearer {PAT}",
       "Accept": "application/vnd.github+json",
       "User-Agent": "deploy-check"}


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers=HDR)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


print(f"目标 sha {SHA[:10]}   轮询 deployments（每 20s，最多 15 次）")
found = None
for i in range(1, 16):
    d = api(f"/repos/{REPO}/deployments?sha={SHA}")
    print(f"  [{i:2d}] count={len(d)}" + (f"  env={d[0].get('environment')}" if d else ""))
    if d:
        found = d[0]
        break
    time.sleep(20)

if not found:
    print("\n结论：5 分钟内无 deployment —— Vercel webhook 漏触发，需要发空提交重触发")
    sys.exit(3)

print(f"\n✅ deployment 已创建  {found['created_at']}  env={found.get('environment')}")

print("\n--- 线上资源版本号复核 ---")
want = WANT_VER
# ⚠️ 本项目的版本号写法是 ?v20261001b —— **没有等号**，别按直觉写 ?v=
CAND = ["v20260925c", "v20260927a", "v20260927b", "v20261001a", "v20261001b"]
for i in range(1, 13):
    out = subprocess.run(
        ["curl", "-s", f"https://fjsanfan.com/?cb={os.urandom(4).hex()}",
         "--max-time", "25"], capture_output=True).stdout.decode("utf-8", "ignore")
    vers = sorted({t for t in (("styles.css?" + p) for p in CAND) if t in out}
                  | {t for t in (("main.js?" + p) for p in CAND) if t in out})
    print(f"  [{i:2d}] {vers}")
    if any(want in v for v in vers):
        print(f"\n✅ 线上已切到 {want}")
        html = out
        break
    time.sleep(20)
else:
    print(f"\n⚠ 线上仍未切到 {want}（部署可能仍在 build）")
    sys.exit(4)

# 线上 CSS 内容级复核：P0/P1 关键声明是否真的到了 CDN
css = subprocess.run(
    ["curl", "-s", f"https://fjsanfan.com/assets/css/styles.css?v={want}&cb={os.urandom(4).hex()}",
     "--max-time", "30"], capture_output=True).stdout.decode("utf-8", "ignore")
print(f"\n--- 线上 styles.css 内容复核（{len(css)} 字节）---")
checks = [
    # —— 2026-09-27 移动端 P0/P1（回归，必须仍然在）——
    ("P0-1 touch-action: manipulation", "touch-action: manipulation" in css),
    ("P0-2 表单 16px", "font-size: 16px" in css),
    ("P0-3 抽屉 max-height 100dvh", "calc(100dvh - 68px)" in css),
    ("P0-4 44px 触控区", "min-height: 44px" in css or "44px" in css),
    ("P0-5 <=920px 让位 .cbar", "calc(100dvh - 68px - 54px)" in css),
    ("P1-1 focus-visible 焦点环", ":focus-visible" in css),
    ("P1-2 scroll-margin-top 82px", "scroll-margin-top: 82px" in css),
    ("P1-3 prefers-reduced-motion", "prefers-reduced-motion" in css),
    # —— 2026-10-01 画册灯箱（本轮新增，必须已上线）——
    ("NEW-1 灯箱遮罩 .lb", ".lb" in css),
    ("NEW-2 灯箱开启态 .lb.is-open", ".lb.is-open" in css),
    ("NEW-3 灯箱图片样式", ".lb img" in css),
]

# 本轮新增的 HTML/JS 侧钩子：只能从 HTML 与 main.js 里查
html_checks = [
    ("NEW-4 卡片可放大钩子 cat-zoom", "cat-zoom" in html),
    ("NEW-5 画册图 lazy 加载", 'loading="lazy"' in html),
    ("NEW-6 资源版本号已切", f"?{want}" in html),
]
for name, ok in checks:
    print(f"  {'✓' if ok else '✗'} {name}")
print(f"  （HTML 侧）")
for name, ok in html_checks:
    print(f"  {'✓' if ok else '✗'} {name}")

allok = all(o for _, o in checks) and all(o for _, o in html_checks)
n = sum(1 for _, o in checks if o) + sum(1 for _, o in html_checks if o)
tot = len(checks) + len(html_checks)
print(f"\n结果 {n}/{tot}")
sys.exit(0 if allok else 5)
