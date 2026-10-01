#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从画册 OCR（带坐标）重建 69 台型号的完整规格数据 —— v2

相比 v1（parse_catalog_models_20261001.py）的改进：
  1. 只用 page 4..41（38 张产品页），跳过封面/公司页/封底
  2. 以旧主表 CSV 的 69 个型号名做**白名单**，OCR 里的噪音文本自动过滤
  3. 正确解析 `A: ... B: ...` 双包装尺寸（对应主表的「包装尺寸A/B」两列）
  4. 支持同一台有多个包装尺寸（如 p40 上 2020*/1740* 两行）
  5. 产品本体尺寸标注线（920mm 等）单独存为 dimensions，不污染 packing
  6. 法务排除表：Gyrotonic 是美国注册商标，不可作为我方型号名

输出：
  - i18n_build/data/catalog_pilates_models_v2.json
  - i18n_build/reports/catalog_models_20261001.txt
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OCR_PATH = ROOT / 'i18n_build/data/catalog_pilates_ocr.json'
CSV_PATH = ROOT / 'i18n_build/reports/pilates_catalog_2026_models.csv'
OUT_JSON = ROOT / 'i18n_build/data/catalog_pilates_models_v2.json'
OUT_LOG = ROOT / 'i18n_build/reports/catalog_models_20261001.txt'

PAGE_RANGE = range(4, 42)          # 38 张产品页
NAME_COL, SERIES_COL, PAGE_COL = 1, 0, 7

# ⚠️ OCR 漏识别的型号名（图上有、OCR 未出块；下方 Material/Packing/Weight 都在）。
# 由「字段组数 vs 识别台数」自检发现，逐条人工核对图片后补入。
# y 取该组 Material 行上方约 0.04（与其他页行距一致），仅供归组定位。
OCR_MISSED = {
    36: [{'name': 'Chair 20-V5', 'series': 'F. Chair 稳踏椅', 'y': 0.650, 'x': 0.635}],
}

# ⚠️ 法务排除（用户 2026-10-01 确认剔除）：Gyrotonic 是美国注册商标，不可用作我方型号名。
#    关键：被排除项**仍要参与字段归组**——若直接从 models 里删掉，它自己的
#    Material / Packing size / Gross weight 会向上漂移到同页邻台（实测 p40 会污染
#    Two-Way Ladder Reformer）。正确做法：保留在 models 里照常归组，只在最终输出时过滤。
EXCLUDE_MODELS = {'gyrotonic'}

FIELD_RE = re.compile(r'^(Material|Packing\s*size|Gross\s*weight|Net\s*weight)\s*:', re.I)
AB_RE = re.compile(r'^\s*([AB])\s*:', re.I)
DIM3_RE = re.compile(r'^\d{2,5}\s*[*x×]\s*\d{2,5}\s*[*x×]\s*\d{2,5}')
KG_RE = re.compile(r'^\d+(?:\.\d+)?\s*(?:kg|kgs)\b', re.I)
DIM1_RE = re.compile(r'^\d{3,5}\s*mm$', re.I)
NOTE_RE = re.compile(r'^\(\s*(.+?)\s*\)$')
PAGE_NO_RE = re.compile(r'^\d{1,2}$')


def norm_space(s: str) -> str:
    return re.sub(r'\s+', ' ', s.replace('\u00a0', ' ')).strip()


# ⚠️ 画册自身印刷存疑项（解析无误 —— 图上确实是这个数，但数值本身可疑，待工厂确认）
#   实测：E 族（梯桶）主流包装 1190×700×1170、F 族（稳踏椅）主流 920×720×790，
#   唯独 21-FO / 20-V5 这组后缀两族**互换**了；且梯桶本体高约 1.03–1.17 m，
#   装不进 790 mm 高的箱子。四台同为该后缀、重量也同为 85 kg，极可能排版复制串行。
#   处理原则：**照画册原文输出**（不改数、不猜测），只在数据里打标供页面/报告提示。
SUSPECT = {
    ('Ladder Barre 21-FO', 'packing_a'): '画册疑似与 Chair 21-FO 互换：梯桶本体高约 1.17 m，装不进 790 mm 箱高',
    ('Ladder Barre 20-V5', 'packing_a'): '画册疑似与 Chair 20-V5 互换：梯桶本体高约 1.17 m，装不进 790 mm 箱高',
    ('Chair 21-FO', 'packing_a'): '画册疑似与 Ladder Barre 21-FO 互换：同族其余稳踏椅均为 920×720×790',
    ('Chair 20-V5', 'packing_a'): '画册疑似与 Ladder Barre 20-V5 互换：同族其余稳踏椅均为 920×720×790',
    ('Chair 4', 'packing_a'): '全册唯一漏印 mm 的一条，且 750×700×650 小于本体，疑为印刷缺漏',
}


def norm_key(s: str) -> str:
    """型号名比对键：统一连字符/空格/大小写"""
    s = norm_space(s)
    s = re.sub(r'\(\s*(?:No\s+)?Moving\s+Footb\w*r\s*\)', '', s, flags=re.I)
    s = re.sub(r'\s*-\s*', '-', s)
    s = re.sub(r'\s*([*x×])\s*', r'\1', s)
    return re.sub(r'\s+', ' ', s).strip().lower().replace(' ', '')


def clean_model(s: str) -> str:
    """展示用型号名"""
    s = norm_space(s)
    s = re.sub(r'\(\s*(?:No\s+)?Moving\s+Footb\w*r\s*\)', '', s, flags=re.I)
    s = re.sub(r'\s*-\s*', '-', s)
    return re.sub(r'\s+', ' ', s).strip()


def is_field(t):  return bool(FIELD_RE.match(t))
def is_ab(t):     return bool(AB_RE.match(t))
def is_dim3(t):   return bool(DIM3_RE.match(t))
def is_kg(t):     return bool(KG_RE.match(t))
def is_dim1(t):   return bool(DIM1_RE.match(t))
def is_note(t):   return bool(NOTE_RE.match(t))
def is_noise(t):  return bool(PAGE_NO_RE.match(t)) and len(t) <= 2


# ⚠️ 坑：页内排序不能直接用 (y, x)。
#   同一行横排的两台，OCR 给出的 y 会有 0.001~0.003 的抖动
#   （实测 p38：Chair 3 y=0.748 / Chair 19-F y=0.749，直接按 y 排会把左右顺序排反）。
#   正确做法：先把 y 相差 < ROW_TOL 的视为同一行，行内再按 x 从左到右。
ROW_TOL = 0.02


def sort_models(models):
    ms = sorted(models, key=lambda m: (m['y'], m['x']))
    out, row, base = [], [], None
    for m in ms:
        if base is None or m['y'] - base < ROW_TOL:
            if base is None:
                base = m['y']
            row.append(m)
        else:
            out.extend(sorted(row, key=lambda d: d['x']))
            row, base = [m], m['y']
    out.extend(sorted(row, key=lambda d: d['x']))
    return out


def to_pretty(raw: str) -> str:
    """2300*710*450mm -> 2300×710×450 mm"""
    if not raw:
        return None
    m = re.search(r'(\d+)\s*[*x×]\s*(\d+)\s*[*x×]\s*(\d+)', raw)
    return f'{m.group(1)}×{m.group(2)}×{m.group(3)} mm' if m else raw


def norm_dim(raw: str) -> str:
    if not raw:
        return None
    m = re.search(r'(\d+)\s*[*x×]\s*(\d+)\s*[*x×]\s*(\d+)', raw)
    return f'{m.group(1)}*{m.group(2)}*{m.group(3)}' if m else raw


# 画册原文的材质写法大小写不一致（Maple / OAK / aluminum / metal 混用），
# 数据源按统一写法归档，页面展示与 schema 都从这里取。
MAT_CANON = {
    'maple': 'Maple', 'oak': 'Oak', 'metal': 'Metal',
    'aluminum': 'Aluminum', 'aluminium': 'Aluminum',
    'carbon steel': 'Carbon steel', 'carbonsteel': 'Carbon steel',
    'steel': 'Steel', 'wood': 'Wood',
}


def canon_material(s):
    if not s:
        return None
    k = norm_space(s).lower()
    return MAT_CANON.get(k, norm_space(s).title())


def load_whitelist():
    """主表 CSV -> {norm_key: [series, 官方名, page]}"""
    wl = {}
    lines = CSV_PATH.read_text(encoding='utf-8-sig').splitlines()
    for line in lines[1:]:
        p = line.split(',')
        if len(p) <= PAGE_COL or not p[NAME_COL].strip():
            continue
        name = p[NAME_COL].strip()
        try:
            pg = int(p[PAGE_COL].strip())
        except ValueError:
            continue
        wl[norm_key(name)] = {'series': p[SERIES_COL].strip(), 'name': name, 'page': pg}
    return wl


def parse_page(page: int, blocks: list, wl: dict):
    """返回 (models, skipped)"""
    items = []
    for b in blocks:
        t = norm_space(b.get('text', ''))
        if not t:
            continue
        y, x = float(b.get('y_top', 0)), float(b.get('x', 0))
        if is_noise(t) and y > 0.90:      # 页码
            continue
        items.append({'text': t, 'y': y, 'x': x})
    items.sort(key=lambda d: (d['y'], d['x']))

    # --- 1) 合并「字段名独占一行」的情况 ---
    # ⚠️ 坑：连续合并时必须用「上一次合并到的块」的 y 做基准，否则 `Gross weight`
    #    会跟着 `A: ... B: ...` 一起被吞掉（实测 p5/p6/p7/p11 六台毛重丢失）。
    dim_ok = lambda t: is_dim3(t) or is_dim1(t)
    field_ok = lambda t: is_ab(t) or is_dim3(t) or is_dim1(t) or is_kg(t)   # Packing size: 后可接 A:/尺寸
    ab_ok = lambda t: is_ab(t) or is_dim3(t) or is_dim1(t)                  # A:/B: 后只接尺寸，绝不接 Gross weight

    merged, i = [], 0
    while i < len(items):
        cur = dict(items[i])
        t0 = cur['text']
        is_tail_field = is_field(t0) and t0.rstrip().endswith(':')
        is_ab_head = is_ab(t0) and not is_dim3(t0)
        if is_tail_field or is_ab_head:
            allow = field_ok if is_tail_field else ab_ok
            last_y = cur['y']
            for j in range(i + 1, min(i + 3, len(items))):
                nxt = items[j]
                if abs(nxt['x'] - cur['x']) < 0.15 and (nxt['y'] - last_y) < 0.055 and allow(nxt['text']):
                    cur['text'] = cur['text'] + ' ' + nxt['text']
                    last_y = nxt['y']
                    i = j
                    continue
                break
        merged.append(cur)
        i += 1

    # --- 2) 识别型号名（白名单约束 + 跨行拼接）---
    def is_value_block(t):
        return (is_field(t) or is_ab(t) or is_dim3(t) or is_kg(t)
                or is_dim1(t) or is_noise(t))

    models, skipped, consumed = [], [], set()
    for ib, b in enumerate(merged):
        if ib in consumed:
            continue
        t = b['text']
        if is_value_block(t):
            continue
        # 先单块匹配；失败则与下方紧邻块拼接（型号名跨两行印，如 'Ladder Barre' + '19-F'）
        hit, span, cand = wl.get(norm_key(t)), [ib], t
        if not hit:
            for jb in range(ib + 1, min(ib + 3, len(merged))):
                nb = merged[jb]
                if is_value_block(nb['text']):
                    break
                if abs(nb['x'] - b['x']) > 0.10 or (nb['y'] - b['y']) > 0.07:
                    break
                cand = cand + ' ' + nb['text']
                span.append(jb)
                hit = wl.get(norm_key(cand))
                if hit:
                    break
        if not hit:
            skipped.append(b)
            continue
        consumed.update(span)
        # 画册把「区分性说明」印在型号名后的括号里（如 AL1-B01 (Moving Footbar) /
        # AL 2-B03 (No Moving Footbar)），这是同页两台唯一的区别，必须保留。
        notes = [norm_space(x) for x in re.findall(r'\(([^)]+)\)', cand)]
        # 括号若单独占一行（实测 p17 / p21），单块匹配不会把它拼进来，需单独吸收
        for jb in range(ib + 1, min(ib + 3, len(merged))):
            nb = merged[jb]
            if (is_note(nb['text']) and abs(nb['x'] - b['x']) < 0.10
                    and (nb['y'] - b['y']) < 0.07):
                notes += [norm_space(x) for x in re.findall(r'\(([^)]+)\)', nb['text'])]
                consumed.add(jb)
            else:
                break
        models.append({'model': hit['name'], 'series': hit['series'],
                       'y': b['y'], 'x': b['x'],
                       'material': None, 'packing_a': None, 'packing_b': None,
                       'weight': None, 'dimensions': [], 'notes': notes})
    models = sort_models(models)

    # --- 2b) 补 OCR 漏识别的型号名 ---
    for om in OCR_MISSED.get(page, []):
        if any(norm_key(om['name']) == norm_key(m['model']) for m in models):
            continue
        models.append({'model': om['name'], 'series': om['series'],
                       'y': om['y'], 'x': om['x'],
                       'material': None, 'packing_a': None, 'packing_b': None,
                       'weight': None, 'dimensions': [], 'notes': [],
                       'ocr_missed': True})
    models = sort_models(models)

    # --- 2c) 自检：字段组数 > 识别台数 → 疑似漏台 ---
    n_mat = sum(1 for b in merged if re.match(r'^Material', b['text'], re.I))
    n_gw = sum(1 for b in merged if re.match(r'^Gross', b['text'], re.I))
    lower_bound = max(n_mat, n_gw)
    warnings = []
    if lower_bound > len(models):
        warnings.append(f'疑似漏台：字段组 {lower_bound} 组（Material {n_mat} / Gross {n_gw}）'
                        f'但只识别出 {len(models)} 台')

    # --- 3) 字段归组：正上方最近 + 横向对齐 ---
    def nearest(fy, fx):
        cands = [m for m in models if m['y'] < fy - 0.004]
        if not cands:
            return None
        return min(cands, key=lambda m: (round(abs(m['x'] - fx), 2), -m['y']))

    # ⚠️ 本体尺寸标注（920mm 这类画在器械上的尺寸线）不能按「正上方最近」归属：
    #   实测 p40 的 1400mm 画在 Two-Way Ladder Reformer 上方、却离 Gyrotonic 更近，
    #   会把下页器械的尺寸算到上一台头上。改用「与型号文字块纵向中心的距离」归属。
    dim1_blocks = []
    for b in merged:
        t, y, x = b['text'], b['y'], b['x']
        if not (is_field(t) or is_ab(t) or is_dim3(t) or is_kg(t)
                or is_dim1(t) or is_note(t)):
            continue
        if is_dim1(t):
            dim1_blocks.append(b)
            continue
        tgt = nearest(y, x)
        if tgt is None:
            skipped.append(b)
            continue
        if re.match(r'^Material', t, re.I):
            m = re.match(r'^Material\s*:\s*(.+)$', t, re.I)
            if m:
                tgt['material_raw'] = norm_space(m.group(1))
                tgt['material'] = canon_material(m.group(1))
        elif re.match(r'^Packing', t, re.I):
            m = re.match(r'^Packing\s*size\s*:\s*(.+)$', t, re.I)
            if m:
                parts = re.findall(r'\d+\s*[*x×]\s*\d+\s*[*x×]\s*\d+', m.group(1))
                if parts:
                    tgt['packing_a'] = norm_dim(parts[0])
                    if len(parts) > 1:
                        tgt['packing_b'] = norm_dim(parts[1])
        elif re.match(r'^Gross', t, re.I):
            m = re.search(r'(\d+(?:\.\d+)?)', t)
            if m:
                tgt['weight'] = float(m.group(1))
        elif is_ab(t):
            a = re.search(r'A\s*:\s*([^B]*)', t, re.I)
            bb = re.search(r'B\s*:\s*(.+)$', t, re.I)
            if a and a.group(1).strip():
                tgt['packing_a'] = norm_dim(a.group(1))
            if bb:
                tgt['packing_b'] = norm_dim(bb.group(1))
        elif is_dim3(t):
            if not tgt['packing_a']:
                tgt['packing_a'] = norm_dim(t)
            elif not tgt['packing_b']:
                tgt['packing_b'] = norm_dim(t)
            else:
                tgt['dimensions'].append(norm_dim(t))
        elif is_kg(t):
            m = re.search(r'(\d+(?:\.\d+)?)', t)
            if m:
                tgt['weight'] = float(m.group(1))
        elif is_note(t):
            for x2 in re.findall(r'\(([^)]+)\)', t):
                n = norm_space(x2)
                if n not in tgt['notes']:
                    tgt['notes'].append(n)

    # --- 3b) 本体尺寸标注：归到「纵向中心」最接近的型号 ---
    if dim1_blocks and models:
        spans = {}
        for m in models:
            ys = [f['y'] for f in merged
                  if (is_field(f['text']) or is_ab(f['text']) or is_dim3(f['text'])
                      or is_kg(f['text']))
                  and f['y'] > m['y'] and f['y'] - m['y'] < 0.55
                  and nearest(f['y'], f['x']) is m]
            lo = m['y']
            hi = max([lo] + ys)
            spans[id(m)] = (lo + hi) / 2
        for b in dim1_blocks:
            tgt = min(models, key=lambda m: abs(spans[id(m)] - b['y']))
            tgt['dimensions'].append(norm_space(b['text']))
    return models, skipped, warnings


def main():
    ocr = json.loads(OCR_PATH.read_text(encoding='utf-8'))
    wl = load_whitelist()
    print(f'白名单: {len(wl)} 个型号')

    all_models, log = [], []
    for pg in PAGE_RANGE:
        blocks = ocr.get(str(pg)) or []
        if not blocks:
            log.append(f'--- page {pg}: (OCR 无数据)')
            continue
        models, skipped, warnings = parse_page(pg, blocks, wl)
        # 法务排除：保留归组结果后再筛掉（见 EXCLUDE_MODELS 注释）
        kept = [m for m in models if norm_key(m['model']) not in EXCLUDE_MODELS]
        dropped = [m for m in models if norm_key(m['model']) in EXCLUDE_MODELS]
        log.append(f'--- page {pg}: {len(kept)} 台' +
                   (f'   [白名单外 {len(skipped)} 块]' if skipped else '') +
                   (f'   [法务排除 {len(dropped)} 台: '
                    + ', '.join(m["model"] for m in dropped) + ']' if dropped else ''))
        for w in warnings:
            log.append(f'  ⚠️ {w}')
        for idx, m in enumerate(kept, 1):
            m['page'] = pg
            # 画册印刷页码 = 文件名 - 1（实测 38/38 页成立），页面上标注须用它
            m['catalog_page'] = pg - 1
            m['seq_in_page'] = idx
            m.setdefault('material_raw', None)
            m['suspect'] = [note for (nm, fld), note in SUSPECT.items()
                            if nm == m['model'] and m.get(fld)]
            m['packing_a_pretty'] = to_pretty(m['packing_a'])
            m['packing_b_pretty'] = to_pretty(m['packing_b'])
            m['image'] = f'assets/img/catalog/p{pg:02d}.webp'
            all_models.append(m)
            log.append(
                f"  {m['seq_in_page']}. {m['model']:<24} {str(m['material'] or '-'):<14} "
                f"A={str(m['packing_a'] or '-'):<18} B={str(m['packing_b'] or '-'):<18} "
                f"W={str(m['weight'] or '-'):<6} dim={m['dimensions']} notes={m['notes']}"
                + ('  ⚠️ 存疑待厂确认' if m['suspect'] else ''))
        for s in skipped:
            log.append(f"     [过滤] y={s['y']:.3f} x={s['x']:.3f}  {s['text'][:70]}")

    got = {m['model'] for m in all_models}
    # 白名单里被法务排除的项（Gyrotonic）不计入「未覆盖」
    want = {v['name'] for v in wl.values() if norm_key(v['name']) not in EXCLUDE_MODELS}
    excl = sorted(v['name'] for v in wl.values() if norm_key(v['name']) in EXCLUDE_MODELS)
    log += ['', '=' * 74,
            f'重建 {len(all_models)} 台 | 白名单 {len(want) + len(excl)} 个 '
            f'(含法务排除 {len(excl)} 个: {excl})']
    log.append(f'未覆盖 ({len(want - got)}): {sorted(want - got)}')
    log.append(f'多余 ({len(got - want)}): {sorted(got - want)}')
    f2 = lambda k: sum(1 for m in all_models if m.get(k))
    log.append(f'material {f2("material")}/{len(all_models)} | '
               f'packingA {f2("packing_a")}/{len(all_models)} | '
               f'packingB {f2("packing_b")}/{len(all_models)} | '
               f'weight {f2("weight")}/{len(all_models)}')
    miss = [(m['model'], m['page']) for m in all_models if not m['packing_a'] and not m['weight']]
    log.append(f'两者皆缺 ({len(miss)}): {miss}')
    sus = [m for m in all_models if m['suspect']]
    log.append(f'⚠️ 画册印刷存疑 ({len(sus)} 台，照原文输出，待工厂确认):')
    for m in sus:
        log.append(f'    p{m["page"]} {m["model"]:<22} {m["packing_a_pretty"]:<20} {m["suspect"][0]}')

    OUT_JSON.write_text(json.dumps(all_models, ensure_ascii=False, indent=1), encoding='utf-8')
    OUT_LOG.write_text('\n'.join(log), encoding='utf-8')
    print('\n'.join(log))


if __name__ == '__main__':
    main()
