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
  B. 页面级内容：版本号、灯箱钩子、型号卡数、序号自洽、JSON-LD ItemList 形态。

用法：python3 verify_live_assets_20261001.py [期望版本号]
      （缺省 v20261001c；⚠️ 本项目写法 ?v20261001c，没有等号）

v2 修正记录（v1 的判据错，别再犯）：
  ① cat-unit 是「画册页单元」，型号卡是它内部的 class="model-card" ——
     v1 数了页单元数，得到 45 ≠ 80 的假缺口
  ② 序号副标题的正则捕获组是 (页码, 第几台, 该页共几台)，
     越界判定必须用第 2、3 个组 —— v1 拿页码和第几台比，凭空报了一串越界
  ③ BreadcrumbList 也有 "itemListElement"，v1 把它算进 ItemList 计数
     （12 ≠ 6 的假富项）—— v2 改为 json.loads 解析后按类型过滤
  ④ 版本号别写死：每次上线都换，必须走参数
"""
import concurrent.futures as cf
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://fjsanfan.com"
VER = sys.argv[1] if len(sys.argv) > 1 else "v20261001c"
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
# 有画册卡片的 6 个族页：型号卡数应逐页精确相等
FAMILY_PAGES = PAGES[1:7]
EXPECT_CARDS = {
    "pilates/pilates-reformer.html": 46,
    "pilates/pilates-reformer-tower.html": 11,
    "pilates/pilates-wunda-chair.html": 9,
    "pilates/pilates-ladder-barrel.html": 7,
    "pilates/pilates-cadillac.html": 4,
    "pilates/pilates-specialty.html": 3,
}
EXPECT_TOTAL_CARDS = 80

# 只取真正的静态资源路径；JS 拼接出来的路径不是静态引用
REF_RE = re.compile(r'(?:src|href)="([^"?#]+\.(?:webp|jpg|jpeg|png|svg|css|js|pdf|ico))')
SRCSET_RE = re.compile(r'srcset="([^"]+)"')
JS_JUNK = re.compile(r"[+'\"`$\\]|\bROOT\b|\bBASE\b")
SEQ_RE = re.compile(r"Catalogue\s*p(\d+)\s*[·•]\s*model\s*(\d+)\s+of\s+(\d+)")
LD_RE = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)


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

cat_refs = [u for u in refs if "catalog" in u.lower() or re.search(r"p\d{2}\.webp$", u)]
cat_bad = [u for c, u in bad if u in set(cat_refs)]
print(f"其中画册图 {len(cat_refs)} 张：",
      "全部 200 ✓" if not cat_bad else f"✗ {cat_bad}")

print()
print("=" * 68)
print("B. 页面级内容复核")
print("=" * 68)


def itemlists(html):
    """解析页面所有 JSON-LD，返回 [(名称, items)]，只取 @type=ItemList 的块。

    ⚠️ 不能用正则数 "itemListElement"：BreadcrumbList 也有同名字段，
       会把计数翻倍（6 页数出 12 的假富项就是这么来的）。
    """
    out = []
    for m in LD_RE.finditer(html):
        try:
            data = json.loads(m.group(1))
        except Exception:
            continue
        nodes = data.get("@graph", [data])
        if isinstance(nodes, dict):
            nodes = [nodes]
        for n in nodes:
            if not isinstance(n, dict):
                continue
            if n.get("@type") == "ItemList":
                out.append((n.get("name", ""),
                            n.get("itemListElement", [])))
    return out


allok = True
total_cards = 0
for p in PAGES:
    html = curl_body(f"{BASE}/{p}")
    if not html:
        print(f"✗ {p:44s} 抓取失败")
        allok = False
        continue
    units = len(re.findall(r'class="cat-unit"', html))     # 画册页单元
    cards = len(re.findall(r'class="model-card"', html))   # 型号卡（真正的计数口径）
    total_cards += cards
    has_ver = f"?{VER}" in html
    has_zoom = 'class="cat-zoom"' in html
    # 序号自洽：捕获组 (页码, 第几台, 该页共几台) → 必须第几台 ∈ [1, 共几台]
    seqs = [(int(a), int(b), int(c)) for a, b, c in SEQ_RE.findall(html)]
    seq_bad = [s for s in seqs if not (1 <= s[1] <= s[2])]
    notes = ""
    if p in EXPECT_CARDS:
        if cards != EXPECT_CARDS[p]:
            notes += f"  ✗ 型号卡应为 {EXPECT_CARDS[p]}"
            allok = False
        if not has_ver:
            notes += "  ✗ 版本号未上线"
            allok = False
        if not has_zoom:
            notes += "  ✗ 缺 cat-zoom 钩子"
            allok = False
    if seq_bad:
        notes += f"  ✗ 序号越界 {seq_bad[:3]}"
        allok = False
    print(f"  {os.path.basename(p):38s} 单元 {units:3d}  卡 {cards:3d}  序号 {len(seqs):3d} "
          f"ver {'✓' if has_ver else '✗'} zoom {'✓' if has_zoom else '✗'}{notes}")

print(f"\n型号卡合计：{total_cards}（应 {EXPECT_TOTAL_CARDS}）"
      f"  {'✓' if total_cards == EXPECT_TOTAL_CARDS else '✗'}")
if total_cards != EXPECT_TOTAL_CARDS:
    allok = False

# JSON-LD 层：6 个族页的 ItemList 必须存在、且全部是「平」的（position+name，无嵌套 Product）
flat_ok, n_il = 0, 0
for p in FAMILY_PAGES:
    html = curl_body(f"{BASE}/{p}")
    ils = itemlists(html)
    n_il += len(ils)
    ok = bool(ils) and all(
        all(set(i) <= {"@type", "position", "name"} and i.get("@type") == "ListItem"
            for i in items if isinstance(i, dict))
        for _, items in ils)
    flat_ok += ok
    if not ok:
        print(f"  ✗ {os.path.basename(p)} ItemList 非平或缺："
              f"{[(nm, len(it)) for nm, it in ils]}")
print(f"\n6 个族页 ItemList（json 解析口径）：共 {n_il} 个，平的 {flat_ok}/6"
      f"  {'✓' if flat_ok == 6 and n_il == 6 else '✗'}")
if flat_ok != 6 or n_il != 6:
    allok = False

print()
print("=" * 68)
print("结论：" + ("全部通过 ✓" if allok and not bad else "存在失败项 ✗"))
print("=" * 68)
sys.exit(0 if (allok and not bad) else 5)
