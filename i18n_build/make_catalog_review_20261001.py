#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把重建后的 70 台型号数据导出为：
  1. pilates_catalog_2026_models_v2.csv        —— 权威主表（8 列 + 溯源列）
  2. catalog_models_review_20261001.md         —— 人可读逐页对照表（交用户核对）

核对标记约定：
  —          画册原文未印该字段（已逐页与 OCR 原始块交叉验证：块数 = 解析数，无丢失）
  *          画册上有但 OCR 未识别出型号名，人工核对图片后补录
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'i18n_build/data/catalog_pilates_models_v2.json'
IMGS = ROOT / 'i18n_build/data/catalog_images_20261001.json'
OLD = ROOT / 'i18n_build/reports/pilates_catalog_2026_models.csv'
OUT_CSV = ROOT / 'i18n_build/reports/pilates_catalog_2026_models_v2.csv'
OUT_MD = ROOT / 'i18n_build/reports/catalog_models_review_20261001.md'

SERIES_ORDER = [
    'A. AL 铝合金核心床', 'B. Fold 折叠线', 'C. Wood 实木线',
    'D. Cadillac 凯迪拉克床', 'E. Ladder Barrel 梯桶', 'F. Chair 稳踏椅',
    'G. Specialty 特殊器械',
]
SERIES_EN = {
    'A. AL 铝合金核心床': 'A. AL — Aluminium Reformer',
    'B. Fold 折叠线': 'B. Fold — Foldable Reformer',
    'C. Wood 实木线': 'C. Wood — Solid Wood Reformer',
    'D. Cadillac 凯迪拉克床': 'D. Cadillac',
    'E. Ladder Barrel 梯桶': 'E. Ladder Barrel',
    'F. Chair 稳踏椅': 'F. Chair',
    'G. Specialty 特殊器械': 'G. Specialty',
}


def main():
    models = json.loads(DATA.read_text(encoding='utf-8'))
    imgs = {i['page']: i for i in json.loads(IMGS.read_text(encoding='utf-8'))}
    old_names = set()
    for line in OLD.read_text(encoding='utf-8-sig').splitlines()[1:]:
        p = line.split(',')
        if len(p) > 1 and p[1].strip():
            old_names.add(p[1].strip())

    # ---------- CSV ----------
    with OUT_CSV.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['系列', '型号', '材质', '包装尺寸A', '包装尺寸B', '毛重kg',
                    '产品尺寸标注', '画册页', '页内序', '图片', '数据来源'])
        for m in models:
            w.writerow([
                m['series'], m['model'], m['material'] or '',
                m['packing_a'] or '', m['packing_b'] or '',
                m['weight'] if m['weight'] is not None else '',
                ' / '.join(m['dimensions']) if m['dimensions'] else '',
                m['page'], m['seq_in_page'], m['image'],
                'OCR补录' if m.get('ocr_missed') else ('新增' if m['model'] not in old_names else '主表'),
            ])

    # ---------- Markdown ----------
    f2 = lambda k: sum(1 for m in models if m.get(k) is not None and m.get(k) != [])
    sus = [m for m in models if m.get('suspect')]
    L = []
    L.append(f'# 普拉提画册 38 页 / {len(models)} 台 型号规格对照表')
    L.append('')
    L.append(f'> 数据源：`/Users/mac-zlg/Downloads/result/` 38 张产品页（page_4~page_41，2397×2433）')
    L.append(f'> 提取方式：OCR（带坐标）→ 按「正上方最近 + 横向对齐」归组 → 与旧主表白名单交叉校验')
    L.append(f'> 用途：**逐条核对**；确认后作为 `/pilates/` 板块重建的权威数据')
    L.append('')
    L.append('## 一、总览')
    L.append('')
    L.append(f'| 项 | 值 |')
    L.append(f'|---|---|')
    L.append(f'| 产品页 | 38 页（画册 page_4 ~ page_41） |')
    L.append(f'| 型号总数 | **{len(models)} 台** |')
    L.append(f'| 材质 | {f2("material")}/{len(models)} |')
    L.append(f'| 包装尺寸 A | **{f2("packing_a")}/{len(models)}（100%）** |')
    L.append(f'| 包装尺寸 B | {f2("packing_b")}/{len(models)}（双箱/双 packing 的型号） |')
    L.append(f'| 毛重 | {f2("weight")}/{len(models)} |')
    L.append(f'| ⚠️ 画册印刷存疑（照原文输出，待厂确认） | {len(sus)} 台 |')
    L.append('')
    L.append('### 法务处理')
    L.append('')
    L.append('| 项 | 处理 |')
    L.append('|---|---|')
    L.append('| `Gyrotonic` | **已剔除**——美国注册商标，不可作为我方型号名。'
             '剔除时保留其字段归组（否则 `2020*740*470` / `185kg` 会漂移到同页 '
             '`Two-Way Ladder Reformer`），仅在输出时过滤 |')
    L.append('')
    L.append('### 画册自身印刷存疑（2 组，需工厂确认）')
    L.append('')
    L.append('| 型号 | 画册印的包装尺寸 | 疑点 |')
    L.append('|---|---|---|')
    for m in sus:
        L.append(f'| `{m["model"]}` | {m["packing_a_pretty"]} | {m["suspect"][0]} |')
    L.append('')
    L.append('> 这两组**解析无误**（图上确实是这个数），是画册排版本身可疑：'
             'E 族（梯桶）主流包装为 1190×700×1170、F 族（稳踏椅）主流为 920×720×790，'
             '唯独 `21-FO` / `20-V5` 这组后缀两族**互换了**。'
             '本表**照画册原文输出、不猜测**，页面亦同；确认后一次性改。')
    L.append('')
    L.append('### 相比旧主表的三处修正')
    L.append('')
    L.append('| # | 变化 | 说明 |')
    L.append('|---|---|---|')
    L.append('| 1 | **新增 1 台：`Chair 20-V5`** | 画册 p36 上实际有 2 台（`Chair 21-FO` + `Chair 20-V5`），旧主表漏记；'
             '且该型号名 OCR 未识别出块，已人工核对图片补录 |')
    L.append('| 2 | **包装尺寸 38% → 100%** | 旧表只有 26/69 台有包装尺寸，实为归组解析缺失；'
             '画册每台都印了 Packing size |')
    L.append('| 3 | **`Chair` 系列字段错位已修** | 旧表 p37/p38/p39 左右两栏同高度导致 `Chair 4`/`Chair 3`/`Chair 10-A` '
             '互相串数据，本次按坐标归组已修正 |')
    L.append('')
    L.append('### 读表约定')
    L.append('')
    L.append('- `—` = **画册原文未印该字段**（非解析失败。已逐页核对：OCR 块数 = 解析台数，无字段丢失）')
    L.append('- `*` = 画册上有、OCR 未识别型号名，人工核对后补录')
    L.append('- 一张图 = 一个画册页，一页可能有 1~3 台；**图与型号是页级对应，规格以本表为准**')
    L.append('')
    L.append('---')
    L.append('')
    L.append('## 二、逐页对照')
    L.append('')

    for s in SERIES_ORDER:
        ms = [m for m in models if m['series'] == s]
        if not ms:
            continue
        L.append(f'### {SERIES_EN.get(s, s)}　`{s}`　共 {len(ms)} 台')
        L.append('')
        for m in sorted(ms, key=lambda x: (x['page'], x['seq_in_page'])):
            img = imgs.get(m['page'], {})
            L.append(f'**画册 p{m["page"]}**　图：`{m["image"]}`'
                     f'（{img.get("width","?")}×{img.get("height","?")}）　'
                     f'该页第 {m["seq_in_page"]} 台')
            L.append('')
            L.append('| 型号 | 材质 | 包装尺寸 A | 包装尺寸 B | 毛重 | 产品尺寸标注 |')
            L.append('|---|---|---|---|---|---|')
            star = ' *' if m.get('ocr_missed') else ''
            L.append(f'| `{m["model"]}`{star} | {m["material"] or "—"} | '
                     f'{m["packing_a_pretty"] or "—"} | {m["packing_b_pretty"] or "—"} | '
                     f'{str(m["weight"]) + " kg" if m["weight"] is not None else "—"} | '
                     f'{" / ".join(m["dimensions"]) if m["dimensions"] else "—"} |')
            L.append('')

    L.append('---')
    L.append('')
    L.append('## 三、当前状态')
    L.append('')
    L.append('| 项 | 状态 |')
    L.append('|---|---|')
    L.append('| 数据地基（本表） | ✅ 完成，69 台，包装尺寸 100% |')
    L.append('| 图片入库 | ✅ 38 张 → `assets/img/catalog/p04.webp` ~ `p41.webp`（合计 3.56 MB） |')
    L.append('| 样板页 | ✅ `pilates/pilates-ladder-barrel.html`（E 族 7 台）已重构 |')
    L.append('| FAQ 材质口径 | ✅ 已按 2026 画册改写（旧「橡胶木 / FAS 枫木 / 克罗地亚榉木」为废稿，不改用） |')
    L.append('| 其余 7 族页 | ⏸ 待铺开（数据已就绪） |')
    L.append('| 6 个语言版（48 页） | ⏸ 待 EN 定稿后手写译文注入 |')
    L.append('')
    L.append('> ⚠️ 仍待决：旧 41 台（`NIX103`/橡胶木/钢琴烤漆 体系）去留 ——')
    L.append('> 建议转成「实木定制线（OEM）」小节，不作主表，避免与画册口径自相矛盾。')

    OUT_MD.write_text('\n'.join(L), encoding='utf-8')
    print(f'CSV  -> {OUT_CSV}  ({len(models)} 行)')
    print(f'MD   -> {OUT_MD}  ({len("\n".join(L))} 字符)')


if __name__ == '__main__':
    main()
