#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一 pilates-ladder-barrel.html 的画册放大链接（2026-10-01）

背景：
  该页的画册块是由 `fix_ladderbarrel_page_sync_20261001.py` 这类专属脚本写的，
  没吃到 `gen_family_catalog_block_20261001.py` 后来加的灯箱钩子。结果同板块 6 页里
  5 页是 `<a ... class="cat-zoom">view larger / 放大查看`，只有这一页是
  `<a ...>view full size / 查看原图`（无 class）→
    ① 点链接走原生新窗口，而不是就地灯箱（行为与另 5 页不一致）
    ② 全站同类元素文案不齐

  线上实测（probe_lightbox_caption_20261001.cjs）：
    reformer 页 .cat-zoom 数=27、点链接开灯箱=Y
    ladder-barrel 页 无 .cat-zoom、figcaption 链接 class=null → 原生新窗口

铁律遵守：
  - 替换式脚本：落盘前断言；模式带 `</figcaption>` 锚定，**绝不碰** 第 668 行的
    WhatsApp 链接（同为 target=_blank rel=noopener，但 class="c-link"）
  - 幂等：已改过则直接退出 0，不会重复插入
  - 落盘前断言 `<a` / `</a>` 增减一致、无 `href="href="`

用法：python3 sync_ladderbarrel_zoom_20261001.py [--dry-run]
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "pilates/pilates-ladder-barrel.html"
# ⚠️ 不要用 ~/.workbuddy/backups/ —— 该路径被文件策略拦截（mkdir 被拒）
BACKUP_DIR = ROOT / "outputs/pilates_rebuild_20261001/_backup"

OLD = ('rel="noopener"><span class="lang-en">view full size</span>'
       '<span class="lang-zh">查看原图</span></a></figcaption>')
NEW = ('rel="noopener" class="cat-zoom"><span class="lang-en">view larger</span>'
       '<span class="lang-zh">放大查看</span></a></figcaption>')
# 必须原样保留的无关链接（第 668 行 WhatsApp）
KEEP = 'href="https://wa.me/8615959029082" target="_blank" rel="noopener"'

DRY = "--dry-run" in sys.argv

html = TARGET.read_text(encoding="utf-8")
n_old, n_new = html.count(OLD), html.count(NEW)

if n_old == 0 and n_new == 3:
    print("已是目标状态（3 处均已统一），无需改动")
    sys.exit(0)

# ---- 落盘前断言 ----
assert n_old == 3, f"期望命中 3 处旧串，实际 {n_old} —— 结构已变，停手人工看"
assert n_new == 0, f"已有 {n_new} 处新串，说明非干净起点，停手"
assert html.count(KEEP) == 1, "WhatsApp 链接基准不符，停手"

a_before, a_end_before = html.count("<a "), html.count("</a>")
out = html.replace(OLD, NEW)

# ---- 落盘后自检 ----
assert out.count(NEW) == 3, "替换后新串数不为 3"
assert out.count(OLD) == 0, "替换后仍有旧串"
assert out.count('class="cat-zoom"') == 3, "cat-zoom 数不为 3"
assert out.count(KEEP) == 1, "WhatsApp 链接被误改"
assert 'href="href="' not in out, "出现重复 href"
assert out.count("<a ") == a_before and out.count("</a>") == a_end_before, \
    "a 标签增减不一致"
assert abs(len(out) - len(html)) < 400, "长度变化异常"

print(f"命中旧串 3 处 → 替换为带 cat-zoom 的新串")
print(f"  字节 {len(html)} → {len(out)}  ({len(out) - len(html):+d})")
print(f"  <a 标签 {a_before}/{a_end_before} 保持不变")

if DRY:
    print("\n--dry-run：未写盘")
    sys.exit(0)

BACKUP_DIR.mkdir(parents=True, exist_ok=True)
bak = BACKUP_DIR / (TARGET.name + ".zoomfix.bak")
shutil.copy2(TARGET, bak)
TARGET.write_text(out, encoding="utf-8")
print(f"\n已写盘；备份 → {bak.relative_to(ROOT)}")
