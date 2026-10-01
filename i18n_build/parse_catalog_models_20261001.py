#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从画册 OCR（带坐标）重建 69 台型号的完整规格数据。

为什么要重做：现有 catalog_pilates_models.json 的归组是「按行序猜」的，
在「左右两栏同高度」或「一页三台」的页上会把字段错配到隔壁型号 ——
表现为 packing 只有 38%、material 只有 78%。

本脚本改用 OCR 的 x / y_top 坐标归组：
  每个字段块（Material / Packing size / Gross weight / 尺寸 / 重量）
  归给它「正上方最近、且横向对齐」的那个型号名。

输出：
  - i18n_build/data/catalog_pilates_models_v2.json   结构化 69 台
  - i18n_build/reports/catalog_models_20261001.txt   校验日志（逐页逐台）
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OCR_PATH = ROOT / 'i18n_build/data/catalog_pilates_ocr.json'
CSV_PATH = ROOT / 'i18n_build/reports/pilates_catalog_2026_models.csv'
OUT_JSON = ROOT / 'i18n_build/data/catalog_pilates_models_v2.json'
OUT_LOG = ROOT / 'i18n_build/reports/catalog_models_20261001.txt'

# ---------- 文本分类 ----------
FIELD_RE = re.compile(
    r'^(Material|Packing\s*size|Gross\s*weight|Net\s*weight|N\.?\s*W\.?|G\.?\s*W\.?)\s*:?',
    re.I)
DIM_RE = re.compile(r'^\d{2,5}\s*[*x×]\s*\d{2,5}\s*[*x×]\s*\d{2,5}')
KG_RE = re.compile(r'^\d+(?:\.\d+)?\s*(?:kg|kgs|KGS)\b', re.I)
PAGE_NO_RE = re.compile(r'^\d{1,2}$')


def norm_space(s: str) -> str:
    s = s.replace('\u00a0', ' ')
    return re.sub(r'\s+', ' ', s).strip()


def is_page_number(t: str, y: float) -> bool:
    """页码：纯 1-2 位数字，且在页面底部 8%"""
    return bool(PAGE_NO_RE.match(t)) and y > 0.90


def is_field(t: str) -> bool:
    return bool(FIELD_RE.match(t))


def is_dim(t: str) -> bool:
    return bool(DIM_RE.match(t))


def is_kg(t: str) -> bool:
    return bool(KG_RE.match(t))


def is_value_like(t: str, y: float) -> bool:
    """值块：尺寸 / 重量 / 字段前缀 / 页码"""
    return is_field(t) or is_dim(t) or is_kg(t) or is_page_number(t, y)


def norm_model(name: str) -> str:
    """型号名归一化，对齐主表口径"""
    s = norm_space(name)
    s = re.sub(r'\(\s*(Moving|No\s+Moving)\s+Footba?r\s*\)', '', s, flags=re.I)  # 去掉脚注
    s = re.sub(r'\s*-\s*', '-', s)          # 'AL 19 -F' -> 'AL 19-F' ; 'Ladder Barre -3' -> 'Ladder Barre-3'
    s = re.sub(r'\s*([*x×])\s*', r'\1', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


# ---------- 主流程 ----------
def parse_page(page_key: str, blocks: list) -> tuple:
    """返回 (models, orphans)；models = [{name, y, x, material, packing_raw, weight_raw, extra}]"""
    # 1) 过滤 + 排序（y 升序 = 从上到下）
    items = []
    for b in blocks:
        t = norm_space(b.get('text', ''))
        if not t:
            continue
        y = float(b.get('y_top', 0))
        x = float(b.get('x', 0))
        if is_page_number(t, y):
            continue
        items.append({'text': t, 'y': y, 'x': x, 'conf': b.get('conf', 1.0)})
    items.sort(key=lambda d: (d['y'], d['x']))

    # 2) 合并「字段名单独一行」的情况：`Packing size:` + 下一行 `1190*700*1170mm`
    merged = []
    i = 0
    while i < len(items):
        cur = dict(items[i])
        if is_field(cur['text']) and cur['text'].rstrip().endswith(':'):
            # 向后找同栏、紧邻的值块
            for j in range(i + 1, min(i + 3, len(items))):
                nxt = items[j]
                if abs(nxt['x'] - cur['x']) < 0.12 and (nxt['y'] - cur['y']) < 0.06:
                    if is_dim(nxt['text']) or is_kg(nxt['text']) or is_field(nxt['text']):
                        cur['text'] = cur['text'] + ' ' + nxt['text']
                        i = j
                        break
                else:
                    break
        merged.append(cur)
        i += 1

    # 3) 识别型号名块（含跨行型号名合并）
    names = []
    k = 0
    while k < len(merged):
        b = merged[k]
        if is_value_like(b['text'], b['y']):
            k += 1
            continue
        name = b['text']
        y, x = b['y'], b['x']
        # 跨行型号名：下一行也是「非字段、非值」且横向对齐、纵向贴近
        while k + 1 < len(merged):
            nb = merged[k + 1]
            if is_value_like(nb['text'], nb['y']):
                break
            if abs(nb['x'] - x) < 0.06 and 0 < (nb['y'] - y) < 0.065:
                name = name + ' ' + nb['text']
                y = nb['y']
                k += 1
            else:
                break
        names.append({'raw': name, 'name': norm_model(name), 'y': y, 'x': x})
        k += 1

    # 4) 字段归组：每个字段块 → 正上方最近且横向对齐的型号
    fields = [b for b in merged if is_value_like(b['text'], b['y'])]
    orphans = []
    for f in fields:
        cands = [n for n in names if n['y'] < f['y'] - 0.004]
        if not cands:
            orphans.append(f)
            continue
        # 先取 x 最近的（同栏），同栏内取 y 最大（最近上方）
        best = min(cands, key=lambda n: (round(abs(n['x'] - f['x']), 2), -n['y']))
        f['_to'] = best['name']

    # 5) 组装
    models = []
    for n in names:
        rec = {
            'model': n['name'],
            'model_raw': n['raw'],
            'page': int(page_key),
            'y_top': round(n['y'], 4),
            'x': round(n['x'], 4),
            'material': None,
            'packing_raw': None,
            'weight_raw': None,
            'extra': [],
        }
        for f in fields:
            if f.get('_to') != n['name'] or f.get('_used'):
                continue
            t = f['text']
            if re.match(r'^Material', t, re.I):
                m = re.match(r'^Material\s*:\s*(.+)$', t, re.I)
                rec['material'] = norm_space(m.group(1)) if m else None
                f['_used'] = True
            elif re.match(r'^Packing', t, re.I):
                m = re.match(r'^Packing\s*size\s*:\s*(.+)$', t, re.I)
                rec['packing_raw'] = norm_space(m.group(1)) if m else None
                f['_used'] = True
            elif re.match(r'^(Gross|Net|N\.?W|G\.?W)', t, re.I):
                rec['weight_raw'] = norm_space(t)
                f['_used'] = True
            elif is_dim(t):
                rec['packing_raw'] = norm_space(t)
                f['_used'] = True
            elif is_kg(t):
                rec['weight_raw'] = norm_space(t)
                f['_used'] = True
            else:
                rec['extra'].append(norm_space(t))
                f['_used'] = True
        models.append(rec)
    return models, orphans


def clean_packing(raw):
    """'2300*710*450mm' -> ('2300*710*450 mm', '2300×710×450 mm')"""
    if not raw:
        return None, None
    s = raw.replace('×', '*').replace('x', '*')
    m = re.search(r'(\d+)\s*\*\s*(\d+)\s*\*\s*(\d+)', s)
    if not m:
        return raw, raw
    a, b, c = m.groups()
    return f'{a}*{b}*{c}', f'{a}×{b}×{c}'


def clean_weight(raw):
    if not raw:
        return None
    m = re.search(r'(\d+(?:\.\d+)?)', raw)
    return float(m.group(1)) if m else None


def main():
    ocr = json.loads(OCR_PATH.read_text(encoding='utf-8'))
    all_models, log_lines = [], []
    for pk in sorted(ocr.keys(), key=lambda s: int(s)):
        blocks = ocr[pk]
        if not blocks:
            log_lines.append(f'--- page {pk}: (空页)')
            continue
        models, orphans = parse_page(pk, blocks)
        log_lines.append(f'--- page {pk}: {len(models)} 台, 未归属 {len(orphans)} 块')
        for m in models:
            pk_a, pk_b = clean_packing(m['packing_raw'])
            m['packing'] = pk_a
            m['packing_pretty'] = pk_b
            m['weight'] = clean_weight(m['weight_raw'])
            all_models.append(m)
            log_lines.append(
                f"    {m['model']:<26} mat={str(m['material']):<14} "
                f"pack={str(m['packing']):<22} wt={m['weight_raw']}")
        for o in orphans:
            log_lines.append(f"    [未归属] y={o['y']:.3f} x={o['x']:.3f}  {o['text']}")

    # 交叉校验：与旧主表 CSV 比型号名集合
    csv_models = []
    for line in CSV_PATH.read_text(encoding='utf-8-sig').splitlines()[1:]:
        parts = line.split(',')
        if len(parts) >= 2 and parts[1].strip():
            csv_models.append(parts[1].strip())
    got = {m['model'] for m in all_models}
    want = set(csv_models)
    log_lines.append('')
    log_lines.append('=' * 70)
    log_lines.append(f'OCR 重建: {len(all_models)} 台   |   旧主表 CSV: {len(csv_models)} 个型号名')
    log_lines.append(f'两表都有: {len(got & want)}')
    log_lines.append(f'仅 OCR 有 ({len(got - want)}): {sorted(got - want)}')
    log_lines.append(f'仅 CSV 有 ({len(want - got)}): {sorted(want - got)}')
    log_lines.append('')
    filled = lambda k: sum(1 for m in all_models if m.get(k))
    log_lines.append(f'字段完整度: material {filled("material")}/{len(all_models)}  '
                     f'packing {filled("packing")}/{len(all_models)}  '
                     f'weight {filled("weight")}/{len(all_models)}')

    OUT_JSON.write_text(json.dumps(all_models, ensure_ascii=False, indent=1), encoding='utf-8')
    OUT_LOG.write_text('\n'.join(log_lines), encoding='utf-8')
    print('\n'.join(log_lines))
    print(f'\n-> {OUT_JSON}')
    print(f'-> {OUT_LOG}')


if __name__ == '__main__':
    main()
