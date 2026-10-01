#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
族页「数据一致性」核查：HTML 里写的规格 vs 数据源 JSON。

为什么必须做：规格是手工填进 HTML 的，很容易和邻行串数据
（本项目实际发生过：`Ladder Barre 19-F` 的材质被误写成邻台的 `Metal`，
而画册原文该字段根本没印 —— 表格与卡片自相矛盾）。
结构校验（verify_pilates_page_*.py）查不出这类错，必须逐项对账。

空值口径（用户 2026-10-01 决策）：**画册未印的字段一律写 `—`**，
总表与卡片同此口径。禁止写「Not listed on this page」这类句子说明，
也禁止把两个空字段合并成 `Material / weight` 一行 —— 那会与总表自相矛盾。

⚠️ 本脚本自身踩过的坑（2026-10-01，已修）：
  旧版只在 `lbl in LBL` 时校验，白名单外的标签 `continue` 静默跳过。
  于是 `Material / weight` 这个自定义合并标签**整条被跳过**，缺陷逃过对账。
  → 现在：未知标签直接报错；三项字段必须各自成行；空值必须是 `—`。
  教训：对照排查里「静默跳过」永远比「误报」更危险。

用法: python3 verify_pilates_data_sync_20261001.py <html> <series前缀>
     例: python3 verify_pilates_data_sync_20261001.py pilates/pilates-ladder-barrel.html "E. Ladder"
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'i18n_build/data/catalog_pilates_models_v2.json'
DASH = '—'


def strip_tags(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s)).strip()


def en_text(h):
    """取该片段里默认显示（英文）的那一份；没有 lang 包装就整段剥标签"""
    m = re.search(r'<span class="lang-en">(.*?)</span>', h, re.S)
    return strip_tags(m.group(1)) if m else strip_tags(h)


def canon(s):
    """规范化后再比：忽略空格 / 乘号写法 / 尾随 .0 / 大小写。
    —— 这些是展示层排版差异（卡片写 `1190 × 700 mm` 更好读，表格写 `1190×700 mm` 更紧凑），
       不是数据错误。真正要抓的是「值不同」「不该有却有」「该有却没有」。"""
    s = re.sub(r'\s+', '', s or '')
    s = s.replace('×', '*').replace('X', '*')
    s = re.sub(r'\.0+(?=\D|$)', '', s)
    return s.lower()


def main():
    html_path, prefix = Path(sys.argv[1]), sys.argv[2]
    t = html_path.read_text(encoding='utf-8')
    models = [m for m in json.loads(DATA.read_text(encoding='utf-8')) if m['series'].startswith(prefix)]
    by_name = {m['model']: m for m in models}
    print(f'数据源：{len(models)} 台（{prefix}*）')
    errs = []

    def expect(got, want, where):
        if canon(got) != canon(want):
            errs.append(f'{where}: HTML="{got}" ≠ 数据源="{want}"')

    # ---------- 1) 规格总表 ----------
    print('\n=== 1. 规格总表 ===')
    rows = re.findall(
        r'<tr>\s*<td class="model"><a href="#([^"]+)">([^<]+)</a></td>\s*'
        r'<td>(.*?)</td>\s*<td class="size">(.*?)</td>\s*'
        r'<td class="size">(.*?)</td>\s*<td class="size">(.*?)</td>\s*</tr>', t, re.S)
    print(f'   表格行数 {len(rows)}（数据源 {len(models)}）')
    if len(rows) != len(models):
        errs.append(f'表格行数 {len(rows)} ≠ 数据源 {len(models)}')
    for anchor, name, mat, pa, pb, wt in rows:
        m = by_name.get(name.strip())
        if not m:
            errs.append(f'表格出现未知型号 {name}'); continue
        expect(en_text(mat), m['material'] or DASH, f'表 {name} 材质')
        expect(strip_tags(pa), m['packing_a_pretty'] or DASH, f'表 {name} 包装A')
        expect(strip_tags(pb), m['packing_b_pretty'] or DASH, f'表 {name} 包装B')
        expect(strip_tags(wt), f"{m['weight']} kg" if m['weight'] is not None else DASH, f'表 {name} 毛重')
        print(f'   · {name:<22} → {anchor}')

    # ---------- 2) 型号卡片 ----------
    print('\n=== 2. 型号卡片 ===')
    cards = re.findall(r'<article class="model-card" id="([^"]+)">(.*?)</article>', t, re.S)
    print(f'   卡片数 {len(cards)}（数据源 {len(models)}）')
    if len(cards) != len(models):
        errs.append(f'卡片数 {len(cards)} ≠ 数据源 {len(models)}')
    LBL = {'Material': 'material', 'Packing size': 'packing_a_pretty', 'Gross weight': 'weight'}
    for cid, body in cards:
        hm = re.search(r'<h3>(.*?)</h3>', body, re.S)
        name = strip_tags(hm.group(1)) if hm else '?'
        m = by_name.get(name)
        if not m:
            errs.append(f'卡片出现未知型号 {name}');
            continue
        pairs = re.findall(r'<dt>(.*?)</dt>\s*<dd>(.*?)</dd>', body, re.S)
        seen = {}
        for dt, dd in pairs:
            lbl, val = en_text(dt), en_text(dd)
            # ⚠️ 白名单之外的标签**必须报错，不能静默跳过**。
            #    实战教训（2026-10-01）：样板页把 19-F 的两个空字段合并成
            #    `Material / weight → Not listed on this page`。因为该标签不在 LBL 里，
            #    整条被 continue 掉 → 缺陷逃过对账，且与同页总表的 `—` 自相矛盾。
            #    对照排查时"静默跳过"永远比"误报"更危险。
            if lbl not in LBL:
                errs.append(f'卡片 {name} 标签「{lbl}」不在允许集 {sorted(LBL)} 内'
                            f'（疑似自定义合并标签；应与总表一致用标准字段名）')
                continue
            key = LBL[lbl]
            seen[key] = val
            want = m.get(key)
            if key == 'weight':
                want = f'{want} kg' if want is not None else None
            if want is None:
                # 数据源为空 → 唯一允许的写法是破折号 '—'（用户 2026-10-01 决策：
                # 「材质空的就按 — 来描述」）。写成句子说明 = 与总表口径不一致。
                if val != DASH:
                    errs.append(f'卡片 {name}「{lbl}」数据源为空，应写 {DASH}，实写「{val}」')
            elif val == DASH:
                errs.append(f'卡片 {name}「{lbl}」写了 {DASH}，但数据源有值 {want}')
            else:
                expect(val, want, f'卡片 {name} {lbl}')
        # 三项都必须成行出现（空的也得写成 '—'，不能省略整行）
        for k in ('material', 'packing_a_pretty', 'weight'):
            if k not in seen:
                errs.append(f'卡片 {name} 缺 {k} 行（空值也须以 {DASH} 成行，不可省略）')
        print(f'   · {name:<22} 写了 {len(pairs)} 项  id={cid}')

    # ---------- 3) JSON-LD 里的 Product ----------
    print('\n=== 3. JSON-LD ItemList 的 Product ===')
    ld = re.search(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', t, re.S)
    hits = []
    for m2 in re.finditer(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', t, re.S):
        try:
            d = json.loads(m2.group(1))
        except Exception:
            continue
        for o in (d if isinstance(d, list) else [d]):
            for x in o.get('@graph', [o]):
                if x.get('@type') == 'ItemList':
                    for it in x.get('itemListElement', []):
                        hits.append(it.get('item'))
    print(f'   Product 数 {len(hits)}')
    if len(hits) != len(models):
        errs.append(f'ItemList Product 数 {len(hits)} ≠ 数据源 {len(models)}')
    for p in hits:
        if not p:
            errs.append('ItemList 里有 ListItem 未带 item'); continue
        sku = p.get('sku')
        m = by_name.get(sku)
        if not m:
            errs.append(f'JSON-LD 出现未知 sku {sku}'); continue
        if m.get('material'):
            expect(p.get('material'), m['material'], f'schema {sku} material')
        elif p.get('material'):
            errs.append(f'schema {sku} 写了 material={p["material"]}，但数据源为空')
        if m.get('weight') is not None:
            expect(str((p.get('weight') or {}).get('value')), str(m['weight']), f'schema {sku} weight')
        else:
            if p.get('weight'):
                errs.append(f'schema {sku} 写了 weight，但数据源为空')
        pk = next((a.get('value') for a in p.get('additionalProperty', []) if a.get('name') == 'Packing size'), None)
        expect((pk or '').replace(' mm', ''), m['packing_a'], f'schema {sku} packing')
    print(f'   校验 sku: {[p.get("sku") for p in hits if p]}')

    print()
    if errs:
        print(f'❌ {len(errs)} 处不一致：')
        for e in errs:
            print('   -', e)
        return 1
    print('✅ HTML 与数据源逐项一致')
    return 0


if __name__ == '__main__':
    sys.exit(main())
