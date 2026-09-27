#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从画册原始 OCR 重建 69 台型号主表（取代 catalog_pilates_models.json 的派生结果）。

为什么重做：catalog_pilates_models.json 是二次派生的，实测**静默丢字段**
（OCR 里有 Packing size，JSON 里是空）+ 至少 1 处错值（Ladder Barre 21-FO）。
本脚本改为直接从 OCR 抽，并加两道自审：
  ① 每个 OCR 行的去向必须记账（模型字段 / 白名单噪声 / 未消费→报错）
  ② 与旧 JSON 逐字段对账，打印全部差异

归属算法（二维，非单一 y 序）：
  · 先合并「换行型号名」（最多 3 行拼接后命中已知型号名）
  · 字段行归属 = 候选锚点中 (y_上方最近, 再 x_最近) 的那个 —— 解决左右两栏同 y 交错
"""
import json, re, sys, os
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
OCR = os.path.join(BASE, 'data', 'catalog_pilates_ocr.json')
OLD = os.path.join(BASE, 'data', 'catalog_pilates_models.json')
OUT = os.path.join(BASE, 'data', 'pilates_models_master.json')

WRITE = '--write' in sys.argv


def norm(s):
    return re.sub(r'[^0-9a-z]', '', (s or '').lower())


def strip_note(s):
    """去掉名字行尾部的 (note)，但不吃掉型号里的括号（本画册无此情况）。"""
    return re.sub(r'[\s]*[（(][^)）]*[)）]\s*$', '', s or '').strip()


def main():
    ocr = json.load(open(OCR, encoding='utf-8'))
    old = json.load(open(OLD, encoding='utf-8'))
    names = [m['model'] for m in old]
    assert len(names) == 69, f'期望 69 台，实际 {len(names)}'
    name_by_norm = {}
    for n in names:
        assert norm(n) not in name_by_norm, f'归一冲突：{n}'
        name_by_norm[norm(n)] = n

    # ---------- 1. 逐页收集行，做换行名合并 + 锚点识别 ----------
    anchors = []   # {model,page,y,x}
    fields = []    # {page,y,x,text}
    noise = []     # (page,y,text,reason)
    PAGENO = re.compile(r'^\d{1,3}$')
    JUNK = re.compile(r'^[>*#=_\-\s]+$')
    CALLOUT = re.compile(r'^\d{3,4}\s*mm$')          # 图纸尺寸标注（引线）
    PURE_NUM = re.compile(r'^\d+(\.\d+)?$')

    for p in range(4, 42):
        ls = [r for r in sorted(ocr[str(p)], key=lambda r: r.get('y_top', 0))
              if (r.get('text') or '').strip()]
        i = 0
        joined = []      # [(text, x, y)] —— 合并后的逻辑行
        while i < len(ls):
            t = ls[i]['text'].strip()
            hit = None
            # 尝试 1~3 行拼接命中型号名（仅当本行单独不是锚点）
            if norm(strip_note(t)) not in name_by_norm:
                for n in (2, 3):
                    if i + n > len(ls):
                        break
                    cand = ' '.join(ls[i + k]['text'].strip() for k in range(n))
                    if norm(strip_note(cand)) in name_by_norm:
                        hit = (cand, n)
                        break
            if hit:
                joined.append((hit[0], ls[i]['x'], ls[i]['y_top']))
                i += hit[1]
            else:
                joined.append((t, ls[i]['x'], ls[i]['y_top']))
                i += 1

        page_anchors = []
        for (t, x, y) in joined:
            k = norm(strip_note(t))
            if k in name_by_norm:
                a = {'model': name_by_norm[k], 'page': p, 'x': x, 'y': y,
                     'raw': t}
                anchors.append(a)
                page_anchors.append(a)
        for (t, x, y) in joined:
            if any(a['raw'] == t and a['y'] == y for a in page_anchors):
                continue
            if PAGENO.match(t):
                noise.append((p, y, t, '页码'))
            elif JUNK.match(t):
                noise.append((p, y, t, '版式杂线'))
            elif CALLOUT.match(t):
                noise.append((p, y, t, '图纸尺寸标注'))
            elif norm(t) in name_by_norm:
                noise.append((p, y, t, '重复出现的型号名'))   # 极少见
            else:
                fields.append({'page': p, 'y': y, 'x': x, 'text': t})

    print(f'锚点 {len(anchors)} 个 / 字段行 {len(fields)} 行 / 噪声 {len(noise)} 行')
    got = sorted(a['model'] for a in anchors)
    assert got == sorted(names), (
        f'型号集合不一致\n  多: {sorted(set(got)-set(names))}\n  缺: {sorted(set(names)-set(got))}')

    # ---------- 2. 二维归属：字段 → 锚点 ----------
    bypage = defaultdict(list)
    for a in anchors:
        bypage[a['page']].append(a)

    blocks = {a['model']: {'model': a['model'], 'page': a['page'],
                           'material': None, 'packing': [], 'weight': None,
                           'note': None, 'lines': []} for a in anchors}
    unassigned = []
    for f in fields:
        cands = [a for a in bypage[f['page']] if a['y'] <= f['y'] + 1e-9]
        if not cands:
            unassigned.append(f)
            continue
        # (y_gap, x_gap) 字典序 —— 先取上方最近的，同 y 再取 x 最近的
        best = min(cands, key=lambda a: (round(f['y'] - a['y'], 4), abs(f['x'] - a['x'])))
        blocks[best['model']]['lines'].append((f['text'], f['y'], f['x']))

    print(f'\n=== 无法归属的字段行（必须为 0）=== {len(unassigned)}')
    for f in unassigned:
        print(f"  p{f['page']} y={f['y']} :: {f['text']!r}")

    # ---------- 3. 白名单噪声逐条列出（人工过目） ----------
    print(f'\n=== 噪声行全量（{len(noise)} 条，逐条列出以便过目）===')
    for p, y, t, why in sorted(noise):
        print(f'  p{p:>2} y={y:<7} [{why}] {t!r}')

    # ---------- 4. 解析块内字段 ----------
    MAT_RE = re.compile(r'^material\s*:?\s*(.+)$', re.I)
    W_RE = re.compile(r'^gross\s*weight\s*:?\s*([\d.]+)\s*kg?', re.I)
    PK_RE = re.compile(r'^packing\s*size\s*:?\s*(.*)$', re.I)
    NOTE_RE = re.compile(r'[（(]([^)）]{2,40})[)）]')
    DIM_RE = re.compile(r'([A-Ba-b])?\s*:?\s*(\d{3,4}\s*[*x×]\s*\d{3,4}\s*[*x×]\s*\d{2,4})\s*(mm)?')
    BARE = re.compile(r'^(\d{3,4}\s*[*x×]\s*\d{3,4}\s*[*x×]\s*\d{2,4})\s*(mm)?$')

    for model, b in blocks.items():
        b['lines'].sort(key=lambda t: t[1])
        pending = False
        used = [False] * len(b['lines'])
        for i, (t, y, x) in enumerate(b['lines']):
            m = NOTE_RE.search(t)
            if m and not b['note']:
                b['note'] = m.group(1).strip()
            t0 = t.strip()
            m = MAT_RE.match(t0)
            if m:
                b['material'] = m.group(1).strip()
                used[i] = True
                continue
            m = W_RE.match(t0)
            if m:
                b['weight'] = float(m.group(1))
                used[i] = True
                pending = False
                continue
            m = PK_RE.match(t0)
            if m:
                rest = m.group(1).strip()
                used[i] = True
                if rest:
                    for lab, dim, _u in DIM_RE.findall(rest):
                        b['packing'].append([(lab or '-').upper(), dim.replace(' ', '') + 'mm'])
                    pending = not DIM_RE.search(rest)
                else:
                    pending = True
                continue
            mm = BARE.match(t0)
            if mm:
                lab = None
                # 裸尺寸：若首字符是 B: 形式已在上分支处理
                b['packing'].append(['-', mm.group(1).replace(' ', '') + 'mm'])
                used[i] = True
                pending = False
                continue
            m = DIM_RE.match(t0)
            if m:
                for lab, dim, _u in DIM_RE.findall(t0):
                    b['packing'].append([(lab or '-').upper(), dim.replace(' ', '') + 'mm'])
                used[i] = True
                pending = False
                continue
        left = [(t, y) for i, (t, y, x) in enumerate(b['lines']) if not used[i]]
        b['_leftover'] = left

    print('\n=== 块内未消费行（必须为 0）===')
    lv = 0
    for model, b in sorted(blocks.items()):
        for t, y in b['_leftover']:
            lv += 1
            print(f'  p{b["page"]} [{model}] y={y} :: {t!r}')
    if not lv:
        print('  0 行')

    # ---------- 5. 与旧 JSON 对账 ----------
    oldmap = {m['model']: m for m in old}

    def pk(rec):
        return '|'.join(f'{k}:{v}' for k, v in rec['packing'])

    diffs = []
    for model in sorted(blocks):
        r, o = blocks[model], oldmap[model]
        pairs = [('packing', '|'.join(f'{k}:{v}' for k, v in (o.get('packing') or [])), pk(r)),
                 ('material', o.get('material') or '', r['material'] or ''),
                 ('weight', str(o.get('weight')), str(r['weight'])),
                 ('note', o.get('note') or '', r['note'] or '')]
        for fld, ov, nv in pairs:
            if ov != nv:
                diffs.append((fld, model, r['page'], ov or '(空)', nv or '(空)'))
    print(f'\n=== 新旧对账：{len(diffs)} 处差异 ===')
    bf = defaultdict(int)
    for d in diffs:
        bf[d[0]] += 1
    print('  按字段:', dict(bf))
    for fld, model, page, ov, nv in diffs:
        print(f'  [{fld:9}] p{page:>2} {model:<26} 旧={ov!r:<26} 新={nv!r}')

    # ---------- 6. 完整度 ----------
    n = len(blocks)
    print(f'\n=== 字段完整度（{n} 台）===')
    print(f"  材质 {sum(1 for b in blocks.values() if b['material']):>2}/{n}"
          f"   装箱 {sum(1 for b in blocks.values() if b['packing']):>2}/{n}"
          f"（A/B 双箱 {sum(1 for b in blocks.values() if len(b['packing']) == 2)}）"
          f"   毛重 {sum(1 for b in blocks.values() if b['weight']):>2}/{n}"
          f"   note {sum(1 for b in blocks.values() if b['note']):>2}/{n}")
    miss = [(b['page'], m, '材质' if not b['material'] else '',
             '装箱' if not b['packing'] else '', '毛重' if not b['weight'] else '')
            for m, b in sorted(blocks.items(), key=lambda kv: (kv[1]['page'], kv[1]['y_top'] if 'y_top' in kv[1] else 0))]
    print('\n  缺项清单：')
    for page, m, a, c, w in sorted(miss):
        lack = ' '.join(x for x in (a, c, w) if x)
        if lack:
            print(f'    p{page:>2} {m:<28} 缺 {lack}')

    if WRITE:
        payload = [{'model': b['model'], 'page': b['page'], 'material': b['material'],
                    'packing': b['packing'], 'weight': b['weight'], 'note': b['note']}
                   for b in sorted(blocks.values(), key=lambda b: (b['page'],))]
        json.dump(payload, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f'\n已写入 {OUT}')
    else:
        print('\n（未落盘；加 --write 落盘）')


if __name__ == '__main__':
    main()
