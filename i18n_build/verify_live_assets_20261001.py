#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""线上资源 404 体检 + 页面级内容复核（2026-10-01，普拉提板块重构上线）

为什么必须单独做这一层：
  ⭐ macOS 文件系统**不区分大小写**，Vercel(Linux) **区分**。
     本地 `open xxx.webp` 能开、线上 404 —— 这是最隐蔽的上线坑，
     任何只跑本地的检查（HTML 解析、浏览器实测）都抓不到。

检查两类东西：
  A. 静态资源可达性：把 pilates 9 页里所有本地引用（img/srcset/a/link/script）
     逐个 HEAD 线上，非 200 一律列出。
  B. 页面级内容：版本号 ?v20261001b、灯箱钩子 cat-zoom、画册卡片数、表格行数。

用法：python3 verify_live_assets_20261001.py
"""
import concurrent.futures as cf
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://fjsanfan.com"
VER = "v20261001b"
PAGES = [
    "pilates/index.html",
    "pilates/pilates-reformer.html",
    "pilates/pilates-reformer-tower.html",
    "pilates/pilates-wunda-chair.html",
    "pilates/pilates-cadillac.html",
    "pilates/pilates-specialty.html",
    "pilates/pilates-ladder-barrel.html",
    "pilates/pilates-spine-corrector.html",
    "pilates/pilates-studio-set.html",
]
# 有画册卡片的 6 个族页（其中 ladder-barrel 只有 ItemList 被扁平化，卡片是原有 7 张）
FAMILY_PAGES = PAGES[1:7]

# 只取真正的静态资源路径；JS 拼接出来的路径（main.js 里 ' + ROOT + ...）不是静态引用
REF_RE = re.compile(r'(?:src|href)="([^"?#]+\.(?:webp|jpg|jpeg|png|svg|css|js|pdf|ico))')
# srcset 里是 "a.webp 1x, b.webp 2x" 形式
SRCSET_RE = re.compile(r'srcset="([^"]+)"')
# main.js 之类的 JS 拼接路径特征，出现即跳过
JS_JUNK = re.compile(r"[+'\"`$\\]|\bROOT\b|\bBASE\b")


def curl(url, method="HEAD"):
    r = subprocess.run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-X", method,
         "-L", "--max-time", "25", url],
        capture_output=True, text=True)
    return (r.stdout or "000").strip()


def curl_body(url):
    r = subprocess.run(["curl", "-s", "-L", "--max-time", "30",
                        f"{url}?cb={os.urandom(3).hex()}"],
                       capture_output=True, text=True)
    return r.stdout


print("=" * 68)
print("A. 线上静态资源可达性（大小写敏感）")
print("=" * 68)

refs = set()
for p in PAGES:
    html = (ROOT / p).read_text(encoding="utf-8")
    for m in REF_RE.finditer(html):
        u = m.group(1).strip()
        if JS_JUNK.search(u):
            continue
        if u.startswith(("http://", "https://", "//", "data:")):
            continue
        refs.add(u.lstrip("./"))
    for m in SRCSET_RE.finditer(html):
        for part in m.group(1).split(","):
            u = part.strip().split()[0]
            if u.startswith(("http", "//", "data:")) or JS_JUNK.search(u):
                continue
            if re.search(r"\.(webp|jpg|jpeg|png|svg)$", u, re.I):
                refs.add(u.lstrip("./"))

refs = sorted(refs)
print(f"9 页共提取到 {len(refs)} 个本地静态引用，逐个 HEAD 线上…\n")

bad = []
with cf.ThreadPoolExecutor(max_workers=8) as ex:
    fut = {ex.submit(curl, f"{BASE}/{u}"): u for u in refs}
    for f in cf.as_completed(fut):
        u = fut[f]
        code = f.result()
        if code != "200":
            bad.append((code, u))

if bad:
    print(f"✗ 非 200 共 {len(bad)} 个：")
    for code, u in sorted(bad):
        print(f"    [{code}] {u}")
else:
    print(f"✓ 全部 {len(refs)} 个资源线上 200，无一 404")

# 单独确认 38 张画册图（本轮新增二进制，最容易踩大小写）
cat_refs = [u for u in refs if "catalog" in u.lower() or re.search(r"p\d{2}\.webp$", u)]
print(f"\n其中画册图 {len(cat_refs)} 张：", "全部 200 ✓" if not any(
    u in dict((x[1], x[0]) for x in bad) for u in cat_refs) else "见上方 ✗")

print()
print("=" * 68)
print("B. 页面级内容复核")
print("=" * 68)

# 每页画册卡片：<article class="cat-unit">…，序号副标题 "Catalogue pNN · model i of j"
CARD_RE = re.compile(r'class="cat-unit')
SEQ_RE = re.compile(r"Catalogue\s*p(\d+)\s*[·•]\s*model\s*(\d+)\s+of\s+(\d+)")
ROW_RE = re.compile(r'<td class="size"')
FLAT_RE = re.compile(r'"itemListElement":\s*\[\s*\{\s*"@type":\s*"ListItem",\s*"position"')

expect_cards = {
    "pilates/pilates-reformer.html": 46,
    "pilates/pilates-reformer-tower.html": 11,
    "pilates/pilates-wunda-chair.html": 9,
    "pilates/pilates-ladder-barrel.html": 7,
    "pilates/pilates-cadillac.html": 4,
    "pilates/pilates-specialty.html": 3,
}
EXPECT_TOTAL_CARDS = 80

allok = True
total_cards = 0
for p in PAGES:
    html = curl_body(f"{BASE}/{p}")
    if not html:
        print(f"✗ {p:44s} 抓取失败")
        allok = False
        continue
    cards = len(CARD_RE.findall(html))
    total_cards += cards
    has_ver = f"?{VER}" in html
    has_zoom = "cat-zoom" in html
    # 序号自洽：model i of j 必须 1<=i<=j
    seqs = [(int(a), int(b), int(c)) for a, b, c in SEQ_RE.findall(html)]
    seq_bad = [s for s in seqs if not (1 <= s[0] <= s[1])]
    note = ""
    if p in expect_cards and cards != expect_cards[p]:
        note = f"  ✗ 卡片数应为 {expect_cards[p]}"
        allok = False
    if not has_ver:
        note += "  ✗ 版本号未上线"
        allok = False
    if not has_zoom and p in expect_cards:
        note += "  ✗ 缺 cat-zoom 钩子"
        allok = False
    if seq_bad:
        note += f"  ✗ 序号越界 {seq_bad[:3]}"
        allok = False
    print(f"  {os.path.basename(p):38s} 卡 {cards:3d}  序号 {len(seqs):3d} "
          f"ver {'✓' if has_ver else '✗'} zoom {'✓' if has_zoom else '✗'}{note}")

print(f"\n画册卡片合计：{total_cards}（应 {EXPECT_TOTAL_CARDS}）"
      f"  {'✓' if total_cards == EXPECT_TOTAL_CARDS else '✗'}")

# 全站 ItemList 深度：本轮把梯桶页扁平化，6 个族页应全部是「平」的
flat = sum(len(FLAT_RE.findall(curl_body(f"{BASE}/{p}"))) for p in FAMILY_PAGES)
print(f"\n6 个族页「平」ItemList 计数：{flat}（期望 6）"
      f"  {'✓' if flat == 6 else '✗ 仍有富项'}")

if total_cards != EXPECT_TOTAL_CARDS or flat != 6:
    allok = False

print()
print("=" * 68)
print("结论：" + ("全部通过 ✓" if allok and not bad else "存在失败项 ✗"))
print("=" * 68)
sys.exit(0 if (allok and not bad) else 5)
