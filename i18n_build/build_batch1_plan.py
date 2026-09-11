#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成《第一批上站清单》：把英文站 63 个垫类产品整理成可执行的建站清单。

命名依据（按优先级）：
  1. 已逐张目视核对产品首图（拼图见 /tmp/sf_first/_sheet*.png）
  2. 英文站规格表（Material / Size / Thickness / Weight）
  3. 图片文件名线索（如 EU-Standard-* / Gold-printed-* / with-Position-Lines）

产出：outputs/第一批上站清单-2026-09-11.md
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = os.path.join(ROOT, "outputs", "sf_catalog.json")

# sf slug -> (建议英文名, 建议中文名, 目视依据 / 备注)
# 括号内 "更新 ymX" 表示应原地更新现有页而非新建
NAMING = {
    # ── TPE 基础款 ──────────────────────────────────────────────
    "tpe-yoga-mat":            ("Standard TPE Yoga Mat", "标准 TPE 瑜伽垫", "紫色卷起，183×61/80cm 6/8mm"),
    "tpe-yoga-mat-2":          ("Purple TPE Yoga Mat", "紫色 TPE 瑜伽垫", "紫色卷起，183×61cm 6mm"),
    "tpe-yoga-mat-3":          ("Lilac TPE Yoga Mat", "淡紫 TPE 瑜伽垫", "淡紫色，170–183cm"),
    "tpe-eco-friendly-yoga-mat": ("Eco-Friendly TPE Yoga Mat", "环保 TPE 瑜伽垫", "绿色+黑色底，可回收 TPE"),
    "tpe-dual-color-yoga-mat": ("Dual-Color TPE Yoga Mat", "双色 TPE 瑜伽垫", "紫+灰双色"),
    "tpe-yoga-mat-dual-color": ("Multi-Color TPE Yoga Mat Bundle", "多色 TPE 瑜伽垫套装", "多色卷装堆叠"),
    "tpe-spliced-color-yoga-mat": ("Spliced Color TPE Yoga Mat", "拼色 TPE 瑜伽垫", "粉灰斜向拼色"),
    "tpe-yoga-mat-special-dual-color": ("Pink & Black Dual-Color TPE Yoga Mat", "粉黑双色 TPE 瑜伽垫", "粉+黑双面"),
    "tpe-yoga-mat-special-dual-color-body-line": ("Alignment Line TPE Yoga Mat", "带体位线 TPE 瑜伽垫", "粉色+中央体位线+绑带"),
    "tpe-double-yoga-mat":     ("Two-Tone Double Layer TPE Yoga Mat", "双层双色 TPE 瑜伽垫", "黑底+绿面双层"),
    "tpe-meditation-mat":      ("TPE Meditation Mat", "TPE 冥想垫", "绿色平面+曼陀罗暗纹"),
    # ── PU / 橡胶 ───────────────────────────────────────────────
    "pu-rubber-yoga-mat":      ("PU Rubber Yoga Mat", "PU 橡胶瑜伽垫", "多色立排，185×68cm 4.5mm"),
    "pu-rubber-yoga-mat-2":    ("Red PU Rubber Yoga Mat", "红色 PU 橡胶瑜伽垫", "红色+黑底卷起"),
    "pu-rubber-yoga-mat-3":    ("Purple Mandala PU Rubber Yoga Mat", "紫色曼陀罗 PU 橡胶垫", "紫色几何曼陀罗印花"),
    "pu-rubber-yoga-mat-4":    ("Gray Mandala PU Rubber Yoga Mat", "灰色曼陀罗 PU 橡胶垫", "深灰+曼陀罗"),
    "pu-rubber-yoga-mat-5":    ("Pink Mandala PU Rubber Yoga Mat", "粉色曼陀罗 PU 橡胶垫", "粉色+曼陀罗"),
    "pu-rubber-yoga-mat-6":    ("Solid Black PU Rubber Yoga Mat", "纯黑 PU 橡胶瑜伽垫", "厚实纯黑卷装"),
    "pu-rubber-yoga-mat-7":    ("Gold Printed PU Rubber Yoga Mat", "烫金印花 PU 橡胶垫", "黑底描金植物纹，185×68cm"),
    "pu-rubber-yoga-mat-8":    ("Ultra-Thin PU Rubber Travel Mat", "1.5 mm 超薄旅行 PU 垫", "珊瑚红薄垫，1.5mm 独有"),
    "pu-rubber-yoga-mat-9":    ("Cork Surface PU Rubber Yoga Mat", "软木面 PU 橡胶垫", "软木/木纹表面，5mm"),
    "pu-rubber-yoga-mat-10":   ("Marble Print PU Rubber Yoga Mat", "大理石纹 PU 橡胶垫", "绿白大理石纹+色卡"),
    "pu-rubber-yoga-mat-11":   ("Sage Green PU Rubber Yoga Mat", "鼠尾草绿 PU 橡胶垫", "素色鼠尾草绿，181×66cm 5mm"),
    "pu-rubber-yoga-mat-12":   ("Gradient Line Art PU Rubber Yoga Mat", "渐变线描 PU 橡胶垫", "淡紫+粉色线描渐变"),
    "pu-rubber-yoga-mat-test": ("Lilac PU Rubber Yoga Mat", "淡紫 PU 橡胶瑜伽垫", "亮面淡紫；原标题竟为 Camouflage，slug 误置"),
    "rubber-yoga-mat":         ("PU Rubber Yoga Mat with Alignment Lines", "带体位线 PU 橡胶垫", "鼠尾草绿+体位线，181×66cm 5mm"),
    "rubber-folding-yoga-mat": ("Olive Foldable Rubber Yoga Mat", "橄榄绿可折叠橡胶垫", "橄榄绿折叠款"),
    # ── 软木 ────────────────────────────────────────────────────
    "cork-rubber-yoga-mat":    ("Cork Rubber Yoga Mat", "软木橡胶瑜伽垫", "软木面+黑色橡胶底，4mm"),
    "cork-rubber-yoga-mat-2":  ("Botanical Print Cork Rubber Yoga Mat", "植物印花软木橡胶垫", "软木+植物印花，183×61cm 5mm"),
    "cork-tpe-yoga-mat":       ("Cork TPE Yoga Mat", "软木 TPE 瑜伽垫", "软木面+绿色 TPE 底，6mm"),
    "cork-tpe-yoga-mat-2":     ("Two-Tone Cork TPE Yoga Mat", "双色软木 TPE 瑜伽垫", "绿+软木双色"),
    "cork-suede-yoga-mat":     ("Cork Suede Yoga Mat", "软木绒面瑜伽垫", "软木面+灰色绒底"),
    # ── 绒面 (Suede) ────────────────────────────────────────────
    "suede-yoga-mat":          ("Watercolor Floral Suede Yoga Mat", "水彩花卉绒面瑜伽垫", "粉色水彩花卉，185×68cm 1.5mm"),
    "suede-yoga-mat-2":        ("Galaxy Gradient Suede Yoga Mat", "星空渐变绒面瑜伽垫", "紫粉渐变+星点"),
    "suede-yoga-mat-3":        ("Aurora Gradient Suede Yoga Mat", "极光渐变绒面瑜伽垫", "绿蓝极光渐变"),
    "suede-yoga-mat-4":        ("Starry Night Print Suede Yoga Mat", "星空（梵高）印花绒面垫", "梵高《星月夜》印花"),
    "suede-rubber-yoga-mat":   ("Flamingo Print Suede Rubber Yoga Mat", "火烈鸟印花绒面橡胶垫", "粉色火烈鸟印花，图库 39 张最全"),
    "suede-tpe-yoga-mat":      ("Geometric Print Suede TPE Yoga Mat", "几何印花绒面 TPE 垫", "粉蓝几何+绑带"),
    "sude-tpe-yoga-mat":       ("Navy Botanical Suede TPE Yoga Mat", "藏青植物绒面 TPE 垫", "藏青龟背竹印花；原 slug 拼写错误 sude→suede"),
    "suede-tpe-yoga-mat-2":    ("Round Suede TPE Yoga Mat (Mandala)", "圆形曼陀罗绒面 TPE 垫", "圆形+粉蓝曼陀罗"),
    "suede-tpe-yoga-mat-3":    ("Monochrome Leaf Suede TPE Yoga Mat", "黑白叶片绒面 TPE 垫", "白底黑白叶片"),
    "suede-foldable-yoga-mat": ("Gold Koi Foldable Suede Yoga Mat", "金锦鲤折叠绒面垫", "藏青+金色锦鲤，可折叠"),
    "suede-tpe-foldable-yoga-mat": ("Pink Mandala Foldable Suede TPE Mat", "粉色曼陀罗折叠绒面垫", "粉色曼陀罗+绑带可折"),
    # ── 折叠款 ──────────────────────────────────────────────────
    "folding-mat":             ("Foldable Cork Yoga Mat", "可折叠软木瑜伽垫", "软木折叠；原标题写 TPE，实物是软木"),
    "folding-yoga-mat":        ("Foldable Yoga Mat (Multi-Color)", "可折叠瑜伽垫（多色）", "多色折叠堆叠，183×61cm 4mm"),
    "folding-yoga-mat-2":      ("Pink Foldable Yoga Mat", "粉色可折叠瑜伽垫", "粉色折叠款"),
    "matte-pu-rubber-folding-yoga-mat": ("Matte PU Rubber Foldable Yoga Mat", "磨砂 PU 橡胶折叠垫", "鼠尾草绿折叠，磨砂面"),
    "matte-pu-rubber-yoga-mat": ("Matte PU Rubber Yoga Mat", "磨砂 PU 橡胶瑜伽垫", "粉色+白色线描"),
    # ── 冥想 / 艺术 / 普拉提 ─────────────────────────────────────
    "meditation-mat":          ("Round Mandala Meditation Mat", "圆形曼陀罗冥想垫", "圆形+Om 曼陀罗，180cm 圆"),
    "meditation-mat-2":        ("Mandala Meditation Mat", "曼陀罗冥想垫", "青蓝+曼陀罗方章"),
    "pu-meditation-mat":       ("PU Meditation Mat Set", "PU 冥想垫套装", "粉色垫+紫色抱枕组合"),
    "oil-painting-style-yoga-mat": ("Oil Painting Style Suede Yoga Mat", "油画风绒面瑜伽垫", "风景油画印花"),
    "pilates-reformer-mat":    ("Pilates Reformer Mat (Custom Logo)", "普拉提器械垫（可定制 Logo）", "黑+棕榈叶，图内含 LOGO 占位；无规格表"),
    "pilates-reformer-mat2":   ("Pilates Reformer Mat (Tropical Print)", "普拉提器械垫（热带印花）", "热带叶片+收纳包；无规格表"),
    "pilates-reformer-mat3":   ("Pilates Reformer Mat (Mandala)", "普拉提器械垫（曼陀罗）", "木材纹+曼陀罗；无规格表"),
    "arched-pu-rubber-yoga-mat": ("Arched PU Rubber Yoga Mat", "拱形 PU 橡胶瑜伽垫", "米白拱纹+全色卡"),
    "yoga-mat":                ("TPE Rubber Yoga Mat", "TPE 橡胶瑜伽垫", "灰色平面款"),
}

# 不在垫类本批的（需移出）
MOVE_OUT = {
    "weighted-ring": "瑜伽圈 / 配重环 — 英文站误归类到 Yoga Mat，应移到瑜伽配件",
    "stretch-board": "拉伸板（拉筋板）— 应移到健身器械",
}

# 客户品牌露出（需用户决定是否上站）
BRAND_FLAG = {
    "tpe-yoga-mat-4": ("MuLinSen Branded TPE Yoga Mat 61cm", "木林森品牌 TPE 瑜伽垫 61cm", "图内含「木林森 MuLinSen」品牌与营销文案"),
    "tpe-yoga-mat-5": ("MuLinSen Branded TPE Yoga Mat 183cm", "木林森品牌 TPE 瑜伽垫 183cm", "同上，粉色调，183cm"),
    "tpe-yoga-mat-6": ("MuLinSen Dual-Sided Non-Slip TPE Mat", "木林森双面防滑 TPE 垫", "同上，主打双面防滑"),
    "tpe-yoga-mat-7": ("MuLinSen Widened Anti-Slip TPE Mat 90cm", "木林森加宽防滑 TPE 垫 90cm", "同上，加宽 90cm"),
    "tpe-yoga-mat-8": ("MuLinSen 3x Anti-Slip TPE Mat 90cm", "木林森三倍防滑 TPE 垫 90cm", "同上，90cm"),
}

# 现有站页 -> 英文站产品的对应（应原地更新，不新建）
EXISTING_MAP = {
    "ym1": ("tpe-yoga-mat", "TPE Yoga Mat", "标准 TPE 瑜伽垫"),
    "ym2": ("tpe-yoga-mat-5", "Wide TPE Yoga Mat", "加宽 TPE 瑜伽垫"),
    "ym3": ("tpe-yoga-mat-7", "Double-wide TPE Mat", "双人加宽 TPE 垫"),
    "ym4": ("folding-mat", "Foldable Yoga Mat", "可折叠瑜伽垫"),
    "ym5": ("pu-rubber-yoga-mat", "PU / Rubber Premium Mat", "PU / 橡胶高端垫"),
    "ym6": ("matte-pu-rubber-yoga-mat", "Matte PU Rubber Yoga Mat", "磨砂 PU 瑜伽垫"),
    "ym7": ("pu-rubber-yoga-mat-test", "Camouflage TPE Yoga Mat", "迷彩 TPE 瑜伽垫"),
}


def main():
    items = json.load(open(CAT, encoding="utf-8"))
    by = {x["slug"]: x for x in items}

    L = []
    A = L.append
    A("# 第一批上站清单（瑜伽垫类）\n")
    A("生成日期：2026-09-11　来源：`www.sanfansport.com` REST API + 逐张目视核对产品图\n")
    A("> 英文站已恢复访问，且 **WordPress REST API 完全开放**（167 个产品、92 个类目、2009 项媒体）。")
    A("> 本清单不再依赖图片快照，全部字段来自 API 结构化数据。\n")

    A("## 一、批次构成\n")
    A("| 项 | 数量 |")
    A("|---|---|")
    A(f"| 英文站 Yoga Mat 家族产品 | {len(items)} |")
    A(f"| 其中：需移出（非垫类） | {len(MOVE_OUT)} |")
    A(f"| 其中：客户品牌露出款（待你定） | {len(BRAND_FLAG)} |")
    A(f"| 其中：已有规格表 | {sum(1 for x in items if x['specs'])} |")
    A(f"| **可上站产品** | **{len(items) - len(MOVE_OUT)}** |")
    A(f"| 图库图片总数 | {sum(len(x['images']) for x in items)} 张 |")
    A(f"| 对应现有站产品页 | {len(EXISTING_MAP)} 个（原地更新） |")
    A(f"| **净新增页面（EN 根目录）** | **{len(items) - len(MOVE_OUT) - len(EXISTING_MAP)}** |")
    A("")
    A("## 二、必须移出的（英文站自身分类有误）\n")
    for s, why in MOVE_OUT.items():
        A(f"- `{s}` — {why}")
    A("")

    A("## 三、需你决定的：客户品牌露出款\n")
    A("这 5 款的实拍图里带有 **「木林森 MuLinSen」品牌 logo 与营销文案**（产品主体上就印着客户品牌）。")
    A("放到你的 B2B 独立站有两种解读：既可作为「我们代工过这个品牌」的能力证明，也可能涉及客户品牌保密。\n")
    A("| 建议英文名 | 建议中文名 | 说明 |")
    A("|---|---|---|")
    for s, (en, zh, note) in BRAND_FLAG.items():
        A(f"| {en} | {zh} | {note} |")
    A("")

    A("## 四、现有 7 个页面的对应关系（原地更新，不新建）\n")
    A("| 现页 | 英文站 slug | 现页标题 | 建议标题 |")
    A("|---|---|---|---|")
    for k, (sf, cur, new) in EXISTING_MAP.items():
        A(f"| `{k}.html` | `{sf}` | {cur} | {new} |")
    A("")
    A("> `ym7` 现为「迷彩 TPE 瑜伽垫 / Camouflage TPE Yoga Mat」，英文站对应 `pu-rubber-yoga-mat-test`；")
    A("> 该 slug 是英文站的误置（`-test` 后缀），**实物是淡紫 PU 垫**，不是迷彩。命名待你定。\n")

    A("## 五、完整清单（建议命名）\n")
    groups = [
        ("TPE 系列", ["tpe-yoga-mat", "tpe-yoga-mat-2", "tpe-yoga-mat-3",
                      "tpe-eco-friendly-yoga-mat", "tpe-dual-color-yoga-mat",
                      "tpe-yoga-mat-dual-color", "tpe-spliced-color-yoga-mat",
                      "tpe-yoga-mat-special-dual-color",
                      "tpe-yoga-mat-special-dual-color-body-line",
                      "tpe-double-yoga-mat", "tpe-meditation-mat"]),
        ("PU / 橡胶系列", ["pu-rubber-yoga-mat", "pu-rubber-yoga-mat-2", "pu-rubber-yoga-mat-3",
                          "pu-rubber-yoga-mat-4", "pu-rubber-yoga-mat-5", "pu-rubber-yoga-mat-6",
                          "pu-rubber-yoga-mat-7", "pu-rubber-yoga-mat-8", "pu-rubber-yoga-mat-9",
                          "pu-rubber-yoga-mat-10", "pu-rubber-yoga-mat-11", "pu-rubber-yoga-mat-12",
                          "pu-rubber-yoga-mat-test", "rubber-yoga-mat", "rubber-folding-yoga-mat",
                          "arched-pu-rubber-yoga-mat", "matte-pu-rubber-yoga-mat",
                          "matte-pu-rubber-folding-yoga-mat", "yoga-mat"]),
        ("软木系列", ["cork-rubber-yoga-mat", "cork-rubber-yoga-mat-2", "cork-tpe-yoga-mat",
                     "cork-tpe-yoga-mat-2", "cork-suede-yoga-mat", "folding-mat"]),
        ("绒面 Suede 系列", ["suede-yoga-mat", "suede-yoga-mat-2", "suede-yoga-mat-3",
                           "suede-yoga-mat-4", "suede-rubber-yoga-mat", "suede-tpe-yoga-mat",
                           "sude-tpe-yoga-mat", "suede-tpe-yoga-mat-2", "suede-tpe-yoga-mat-3",
                           "suede-foldable-yoga-mat", "suede-tpe-foldable-yoga-mat",
                           "folding-yoga-mat", "folding-yoga-mat-2", "oil-painting-style-yoga-mat"]),
        ("冥想 / 普拉提", ["meditation-mat", "meditation-mat-2", "pu-meditation-mat",
                        "pilates-reformer-mat", "pilates-reformer-mat2", "pilates-reformer-mat3"]),
        ("木林森品牌款（待定）", list(BRAND_FLAG)),
    ]
    seen = set()
    for gname, slugs in groups:
        rows = []
        for s in slugs:
            x = by.get(s)
            if not x or s in seen:
                continue
            seen.add(s)
            nm = BRAND_FLAG.get(s) or NAMING.get(s)
            if not nm:
                nm = (x["title_en"], "（待定）", "")
            en, zh, note = nm
            sp = x["specs"]
            rows.append((s, en, zh, sp.get("Size", "—"), sp.get("Thickness", "—"),
                         len(x["images"]), note))
        if not rows:
            continue
        A(f"### {gname}（{len(rows)}）\n")
        A("| # | 英文站 slug | 建议英文名 | 建议中文名 | Size | 厚度 | 图 | 依据 |")
        A("|---|---|---|---|---|---|---|---|")
        for i, (s, en, zh, size, thk, n, note) in enumerate(rows, 1):
            size = re.sub(r"\s+", " ", size)[:30]
            thk = re.sub(r"\s+", " ", thk)[:14]
            A(f"| {i} | `{s}` | {en} | {zh} | {size} | {thk} | {n} | {note} |")
        A("")

    missing = [s for s in by if s not in seen]
    if missing:
        A("### 未归类\n")
        for s in missing:
            A(f"- `{s}` — {by[s]['title_en']}")
        A("")

    A("## 六、字段来源与处理规则\n")
    A("| 本站字段 | 英文站来源 | 处理 |")
    A("|---|---|---|")
    A("| Material | `Material` 标签 | 直接采用 |")
    A("| Size | `Size` 标签 | 采用；欧/日韩页去英制 |")
    A("| Thickness | `Thickness` 标签 | 采用；部分产品厚度写在 Size 内，需拆 |")
    A("| Weight | `Weight` 标签 | 仅 8/63 有值，其余留空不编 |")
    A("| MOQ | **英文站无此标签** | **沿用本站原值，逐字不动** |")
    A("| Colors | `Color` 标签 | 采用 |")
    A("| Feature | `Feature` 标签 | 采用 |")
    A("| Logo | `Logo` 标签 | 采用 |")
    A("| Compliance | 英文站 `Certificate` 标签（仅 4 个瑜伽柱页有） | **`ROHS / CE / ISO9001 / BSCI / REACH`** — 英文站原文直证 |")
    A("| Packaging | `Packing` / `Package` 标签 | 采用 |")
    A("")
    A("## 七、阻塞项\n")
    A("1. **客户品牌款 5 个**是否上站，需你定。")
    A("2. **`ym7` 的命名**需你定（英文站实物是淡紫 PU 垫，现站叫迷彩垫）。")
    A("3. **3 个普拉提器械垫无规格表**，规格需另行确认或留空。")
    A("4. **5 个产品缺 Weight**，不编数据、留空。")
    A("5. 英文站图片为 jpg/webp 混合，需统一转 WebP q75 后再入库。")
    A("")

    out = os.path.join(ROOT, "outputs", "第一批上站清单-2026-09-11.md")
    open(out, "w", encoding="utf-8").write("\n".join(L))
    print(f"✅ {out}  ({len(L)} 行)")
    print(f"统计：清单内 {len(seen)} 个，未归类 {len(missing)}")


if __name__ == "__main__":
    main()
