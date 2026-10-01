#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 pilates/pilates-ladder-barrel.html 同步到已定案的画册数据。

═══ 为什么要改（证据链，不是印象）═══
2026 画册的【实物图 + 箱规】块在印刷页 33 与印刷页 35 之间互换了，标题与所在分章各自正确。
（文件页码 = 纸上印的页码 + 1：印刷 33 = 文件 p34.webp，印刷 35 = 文件 p36.webp）

  · 印刷 33（梯桶章内）标题印 `Ladder Barre 21-FO / 20-V5`，但图上实物是**稳踏椅**，箱规 920×720×790
  · 印刷 35（稳踏椅章首页）标题印 `Chair 21-FO / 20-V5`，但图上实物是**梯桶**，箱规 1190×700×1170

三条判据（缺一不可）：
  ① 箱规物理量级 —— 1.17 m 高的梯桶装不进 0.79 m 高的箱子；梯桶线其余 5 台全是 1190×700×1170 / 1120×670×980
  ② 箱规归组 —— 920×720×790 与 Chair 族其余 4 台（10-A / 3 / 1-A / 2-A）**完全一致**
  ③ 后缀跨线复用 —— `Metal 20-V5`（印刷 08）/ `AL 21-FO`（印刷 09）也出现在**核心床章**
     → `21-FO` / `20-V5` 不是全局唯一编号，两个族**各自都有**这两个号（故不是"标题抄错"）

结论：Ladder Barre 21-FO / 20-V5 = Metal，1190×700×1170，85 kg，实物在**文件 p36.webp**。
站点页此前按「标题所在页」取值，于是把稳踏椅的箱规挂在了两台梯桶上，
并在梯桶族页面上放了一张**稳踏椅的照片**（p34.webp）。

═══ 改动四类（实测得出）═══
  1) 规格表：21-FO / 20-V5 两行 920×720×790 → 1190×700×1170；并移到 4-T 之后
     （原顺序按画册页升序排，32→33→34；页号更正后须为 32→34→35，否则表里页序倒挂）
  2) 画册区块：cat-p34 块换成 p36.webp（页 35）并整块移到 cat-p35 之后
  3) JSON-LD：p34.webp → p36.webp ×2；920*720*790 mm → 1190*700*1170 mm ×2；ListItem position 重排
  4) 卡片副标题 / 图注 / alt：页号 33 → 35

用法：先 `--dry-run`（默认）看清单，确认后 `--apply`。
"""
import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

PAGE = Path("pilates/pilates-ladder-barrel.html")

# 新顺序（画册页升序：32 → 34 → 35）
ROW_ORDER = ["ladder-barre-3", "ladder-barre-19-f",
             "ladder-barre-1-a", "ladder-barre-2-a", "ladder-barre-4-t",
             "ladder-barre-21-fo", "ladder-barre-20-v5"]
# ⚠️ 区块用**原始 id** 表达目标顺序：id 要等到重排之后才改，否则重排判据自己就失效了
BLOCK_ORDER = ["cat-p33", "cat-p35", "cat-p34"]
# ⚠️ 区块 id 里的页号是**内容互换前**的：cat-p34 那块换成 p36.webp 后，显示的是印刷页 35
BLOCK_DISPLAY_PAGE = {"cat-p33": 32, "cat-p35": 34, "cat-p34": 35}
BLOCK_RENAME = {"cat-p34": "cat-p36"}

SKU_ORDER = ["Ladder Barre-3", "Ladder Barre 19-F",
             "Ladder Barre 1-A", "Ladder Barre 2-A", "Ladder Barre 4-T",
             "Ladder Barre 21-FO", "Ladder Barre 20-V5"]

OLD_SPEC_TABLE = ">920×720×790 mm<"
NEW_SPEC_TABLE = ">1190×700×1170 mm<"
OLD_SPEC_CARD = ">920 × 720 × 790 mm<"
NEW_SPEC_CARD = ">1190 × 700 × 1170 mm<"


def sub_n(text, old, new, n, label, log):
    """替换且**严格校验命中次数**——多一处少一处都算失败，避免静默漏改。"""
    found = text.count(old)
    if found != n:
        raise SystemExit(f"✗ [{label}] 期望命中 {n} 处，实际 {found} 处 —— 中止，不改动任何字节")
    log.append(f"  · {label}: {found} 处")
    return text.replace(old, new)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--page", default=str(PAGE))
    args = ap.parse_args()
    page = Path(args.page)
    if not page.exists():
        raise SystemExit(f"✗ 找不到 {page}")

    src = page.read_text(encoding="utf-8")
    h = src
    log = []

    # ── 0) 先记录改动前的标签计数，供落盘后比对 ─────────────────────
    def tag_counts(s):
        return {t: (len(re.findall(rf"<{t}\b", s)), len(re.findall(rf"</{t}>", s)))
                for t in ("div", "article", "figure", "table", "tr", "td", "dl", "section")}
    before_tags = tag_counts(h)

    # ── 1) 全局：p34.webp → p36.webp（本页全部 4 处都应改）──────────
    h = sub_n(h, "catalog/p34.webp", "catalog/p36.webp", 4, "画册图 p34→p36 (src/链接/JSON-LD×2)", log)

    # ── 2) 页号 33 → 35 ─────────────────────────────────────────────
    h = sub_n(h, "2026 catalogue · page 33", "2026 catalogue · page 35", 1, "图注英文页号", log)
    h = sub_n(h, "2026 画册 · 第 33 页", "2026 画册 · 第 35 页", 1, "图注中文页号", log)
    h = sub_n(h, "画册第 33 页", "画册第 35 页", 2, "卡片副标题中文页号", log)
    h = sub_n(h, "catalogue page 33 — ", "catalogue page 35 — ", 1, "img alt 页号", log)
    h = sub_n(h, "Catalogue p33 · model", "Catalogue p35 · model", 2, "卡片副标题页号", log)

    # ── 3) 规格数值 ─────────────────────────────────────────────────
    h = sub_n(h, OLD_SPEC_TABLE, NEW_SPEC_TABLE, 2, "规格表 920×720×790", log)
    h = sub_n(h, OLD_SPEC_CARD, NEW_SPEC_CARD, 2, "卡片 920 × 720 × 790", log)
    h = sub_n(h, "920*720*790 mm", "1190*700*1170 mm", 2, "JSON-LD 920*720*790", log)

    # ── 4) 规格表行序 ──────────────────────────────────────────────
    tb = re.search(r"        <tbody>\n(.*?)        </tbody>\n", h, re.S)
    if not tb:
        raise SystemExit("✗ 找不到规格表 tbody")
    rows = re.findall(r"        <tr>\n.*?        </tr>\n", tb.group(1), re.S)
    if len(rows) != 7:
        raise SystemExit(f"✗ 规格表期望 7 行，实际 {len(rows)} 行")
    byrow = {}
    for r in rows:
        m = re.search(r'href="#([^"]+)"', r)
        if not m:
            raise SystemExit("✗ 有一行取不到锚点")
        byrow[m.group(1)] = r
    if sorted(byrow) != sorted(ROW_ORDER):
        raise SystemExit(f"✗ 表格锚点集合不符：{sorted(byrow)}")
    old_row_order = [re.search(r'href="#([^"]+)"', r).group(1) for r in rows]
    if old_row_order != ROW_ORDER:
        log.append(f"  · 表格行序重排：{' → '.join(s.replace('ladder-barre-','') for s in old_row_order)}")
        h = h.replace(tb.group(0), "        <tbody>\n" + "".join(byrow[s] for s in ROW_ORDER) + "        </tbody>\n")

    # ── 5) 画册区块（figure + 卡片）整块重排 ────────────────────────
    block_re = re.compile(r'      <div class="cat-unit" id="(cat-p\d+)">\n.*?\n      </div>\n', re.S)
    spans = [(m.start(), m.end(), m.group(1)) for m in block_re.finditer(h)]
    blocks = {pid: h[s:e] for s, e, pid in spans}
    if sorted(blocks) != sorted(BLOCK_ORDER):
        raise SystemExit(f"✗ 画册区块集合不符：{sorted(blocks)}")
    old_block_order = [pid for _, _, pid in spans]
    if old_block_order != BLOCK_ORDER:
        log.append(f"  · 画册区块重排：{' → '.join(old_block_order)}  ⇒  {' → '.join(BLOCK_ORDER)}")
        # ⚠️ 区块之间**隔着一个空行**，所以「把三块直接拼起来」的那个串在文件里根本不存在
        #    —— h.replace(...) 会静默空跑（本轮实测踩到）。必须取「首块起点 ~ 末块终点」整段重建，
        #    并把分隔符原样带上，最后断言结果真的变了。
        first, last = spans[0][0], spans[-1][1]
        seps = [h[spans[i][1]:spans[i + 1][0]] for i in range(len(spans) - 1)]
        if len(set(seps)) != 1:
            raise SystemExit(f"✗ 区块间分隔符不一致，不敢自动重排：{seps!r}")
        region = h[first:last]
        new_region = seps[0].join(blocks[k] for k in BLOCK_ORDER)
        if new_region == region:
            raise SystemExit("✗ 重排后内容与原文相同 —— 说明重排没生效，中止")
        h = h[:first] + new_region + h[last:]
        got = [m.group(1) for m in block_re.finditer(h)]
        if got != BLOCK_ORDER:
            raise SystemExit(f"✗ 重排后校验失败：期望 {BLOCK_ORDER}，实际 {got}")

    # ── 6) 区块 id 正名（必须在重排之后：否则重排判据自己失效）──────
    for old_id, new_id in BLOCK_RENAME.items():
        h = sub_n(h, f'id="{old_id}"', f'id="{new_id}"', 1, f"区块 id {old_id}→{new_id}", log)

    # ── 7) JSON-LD ListItem 顺序 + position 重编号 ──────────────────
    # ⚠️ 本页 JSON-LD 里有 **两个** 带 ListItem 的结构：产品 ItemList（7 条）与
    #    BreadcrumbList（3 条）。必须把范围**限定在 ItemList 内**，否则会去动面包屑。
    i_list = h.find('"@type": "ItemList"')
    i_crumb = h.find('"@type": "BreadcrumbList"')
    if i_list < 0:
        raise SystemExit("✗ 找不到 ItemList")
    region_end = i_crumb if i_crumb > i_list else len(h)
    region = h[i_list:region_end]
    items = re.findall(r'        \{\n          "@type": "ListItem",\n.*?\n        \},?\n', region, re.S)
    if len(items) != 7:
        raise SystemExit(f"✗ ItemList 内期望 7 个 ListItem，实际 {len(items)}")
    by_sku = {}
    for it in items:
        m = re.search(r'"sku": "([^"]+)"', it)
        if not m:
            raise SystemExit("✗ 有 ListItem 取不到 sku")
        by_sku[m.group(1)] = it
    if sorted(by_sku) != sorted(SKU_ORDER):
        raise SystemExit(f"✗ JSON-LD sku 集合不符：{sorted(by_sku)}")
    old_sku_order = [re.search(r'"sku": "([^"]+)"', it).group(1) for it in items]
    if old_sku_order != SKU_ORDER:
        log.append("  · JSON-LD 产品 ItemList 顺序重排 + position 重编号（1–7，面包屑不动）")
        rebuilt = []
        for i, sku in enumerate(SKU_ORDER, 1):
            body = re.sub(r'"position": \d+', f'"position": {i}', by_sku[sku], count=1)
            rebuilt.append(body.rstrip(",\n").rstrip())
        new_region = region.replace("".join(items), ",\n".join(rebuilt) + "\n")
        h = h[:i_list] + new_region + h[region_end:]

    # ── 落盘前自检 ─────────────────────────────────────────────────
    problems = []
    for bad in ("920×720×790", "920 × 720 × 790", "920*720*790", "p34.webp", "page 33", "第 33 页", "cat-p34"):
        if bad in h:
            problems.append(bad)
    if problems:
        raise SystemExit(f"✗ 自检失败，仍有残留：{problems}")
    if 'href="href="' in h:
        raise SystemExit('✗ 自检失败：出现 href="href="（替换式脚本经典事故）')

    after_tags = tag_counts(h)
    difftags = {t: (before_tags[t], after_tags[t]) for t in before_tags if before_tags[t] != after_tags[t]}

    # JSON-LD 结构改过，必须验它还是合法 JSON，且面包屑段**逐字节未动**
    import json as _json
    ld_blocks = re.findall(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', h, re.S)
    for i, blk in enumerate(ld_blocks, 1):
        try:
            _json.loads(blk)
        except Exception as e:
            raise SystemExit(f"✗ JSON-LD 第 {i} 块解析失败：{e}")
    crumb_mark = '"@type": "BreadcrumbList"'
    if crumb_mark in src and crumb_mark in h:
        i0 = src.find(crumb_mark); j0 = h.find(crumb_mark)
        a = src[i0:src.find("</script>", i0)]
        b = h[j0:h.find("</script>", j0)]
        if a != b:
            raise SystemExit("✗ 面包屑段被改动了 —— 不该发生，中止")

    print("═══ 改动清单 ═══")
    for line in log:
        print(line)
    print()
    print("═══ 落盘前自检 ═══")
    print(f"  残留旧值扫描       : 0 处 ✓（920×720×790 / p34.webp / page 33 / cat-p34 全部清零）")
    print(f"  href 双写          : 无 ✓")
    print(f"  标签计数变化       : {difftags if difftags else '全部一致 ✓'}")
    for t, (o, c) in before_tags.items():
        if o != c:
            print(f"    ⚠️ 改动前 {t} 就开闭不等：{o} / {c}")
    print(f"  画册区块页序(印刷) : {' → '.join(str(BLOCK_DISPLAY_PAGE[k]) for k in BLOCK_ORDER)}")
    print(f"  表格行序(锚点)     : {', '.join(s.replace('ladder-barre-','') for s in ROW_ORDER)}")
    print(f"  JSON-LD position   : 1–7 已按上表顺序重编")
    print(f"  字节               : {len(src)} → {len(h)}")

    if not args.apply:
        print("\n【DRY-RUN】未写入任何字节。确认无误后加 --apply。")
        return

    # ⚠️ 备份必须写到**仓库外**：本仓无 .vercelignore，`pilates/*.bak_*.html` 会被 Vercel
    #    当普通静态文件发布成公开页（等于凭空多一个重复内容页）。
    bakdir = Path.home() / ".workbuddy" / "backups" / "fjsanfan"
    bakdir.mkdir(parents=True, exist_ok=True)
    bak = bakdir / f"{page.name}.bak_{datetime.now():%Y%m%d_%H%M%S}"
    shutil.copy2(page, bak)
    page.write_text(h, encoding="utf-8")
    print(f"\n✅ 已落盘：{page}")
    print(f"   备份  ：{bak}（仓库外，不会被部署）")


if __name__ == "__main__":
    main()
