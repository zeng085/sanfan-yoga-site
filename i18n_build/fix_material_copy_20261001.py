#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
普拉提板块「材质口径」文案统一 —— 2026-10-01

背景（用户决策）：
  1. 画册未印材质 → 按 `—` 描述（不变）
  2. FAQ 以 **2026 画册** 为准；旧的「进口橡胶木 / FAS 级白枫木 / 钢琴烤漆 / 克罗地亚榉木」
     是**废稿**，不再作为口径
  3. `Gyrotonic` 剔除（美国注册商标）
  4. 以 **客户定制品牌** 为方向引导

为什么不是「把 A 词换成 B 词」：
  旧写法的毛病是**在 FAQ 里罗列具体木种**，一旦产品线换代（旧 41 台 → 画册 69 台）
  就必然与型号表打架。新写法改为两件事：
    · 「材质按型号确定 → 见型号表该编号的材质列」——把口径交回数据源，永不冲突
    · 「也可按你品牌现用的材质与表面工艺生产」——导向客户定制品牌（用户要的方向）

⚠️ 与型号表的关系：本脚本**只改文案，不动型号数据**。旧 7 个族页的型号表仍为旧体系
   （NIX/NIK/NIC…），但新表述对两套体系都成立（它不列举具体木种）。

用法：
    python3 fix_material_copy_20261001.py            # dry-run，只统计
    python3 fix_material_copy_20261001.py --apply    # 落盘
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GLOB = sorted((ROOT / 'pilates').glob('*.html'))

# (名称, 旧串, 新串, 期望全局替换数, 期望文件数)
EN_FAQ_OLD = ('Frames are built in imported rubberwood, FAS-grade white maple, '
              'piano-lacquer white maple and Croatian beech, with rails, springs '
              'and bearings specified for studio duty.')
EN_FAQ_NEW = ('Material is set per model — see the material column in the model table '
              'above for the code you are considering; we machine in solid timber, '
              'aluminium and steel. For OEM and ODM programmes we build to the material '
              'and finish specification your own brand already uses. Rails, springs and '
              'bearings are specified for studio duty.')

ZH_FAQ_OLD = '床架采用进口橡胶木、FAS 级白枫木、钢琴漆白枫木与克罗地亚榉木，导轨、弹簧与轴承按场馆级使用选型。'
ZH_FAQ_NEW = ('材质按型号确定——请见上方型号表中该编号对应的材质列；我们的加工覆盖实木、铝合金与钢材。'
              'OEM/ODM 项目可直接按你品牌现用的材质与表面工艺生产。导轨、弹簧与轴承按场馆级使用选型。')

EN_CUST_OLD = ('<strong>Timber &amp; finish</strong> — Domestic or imported rubberwood, '
               'FAS-grade white maple, piano lacquer, Croatian beech, aluminium or 316 steel.')
EN_CUST_NEW = ('<strong>Timber &amp; finish</strong> — Solid timber, aluminium or steel; '
               'or we build to the material and finish spec your own brand already uses.')

ZH_CUST_OLD = '<strong>木种与表面</strong> — 国产或进口橡胶木、FAS 级白枫木、钢琴烤漆、克罗地亚榉木、铝合金或 316 钢。'
ZH_CUST_NEW = '<strong>木种与表面</strong> — 实木、铝合金或钢材；也可直接按你品牌现用的材质与表面工艺生产。'

RULES = [
    ('EN FAQ 答案', EN_FAQ_OLD, EN_FAQ_NEW, 16, 8),
    ('ZH FAQ 答案', ZH_FAQ_OLD, ZH_FAQ_NEW, 8, 8),
    ('EN 可定制·木种', EN_CUST_OLD, EN_CUST_NEW, 7, 7),
    ('ZH 可定制·木种', ZH_CUST_OLD, ZH_CUST_NEW, 7, 7),
]

# 必须消失的旧词（仅在「被判废稿」的这几句范围内核验，不是全站扫词）
LEGACY_RE = re.compile(r'(rubberwood|white maple|Croatian beech|piano.?lacquer)', re.I)


def main():
    apply = '--apply' in sys.argv
    print(f'{"模式":<6} {"文件数":>6}  {"规则":<16} {"命中":>5} {"期望":>5}  状态')
    print('-' * 66)

    grand_old = {}
    stats = []
    total_by_rule = [0] * len(RULES)
    files_by_rule = [set() for _ in RULES]

    for f in GLOB:
        t = f.read_text(encoding='utf-8')
        for ri, (name, old, new, exp_n, exp_f) in enumerate(RULES):
            n = t.count(old)
            if not n:
                continue
            total_by_rule[ri] += n
            files_by_rule[ri].add(f.name)
            if apply:
                t = t.replace(old, new)
        if apply:
            # ★ 落盘前断言：不得出现替换事故（新旧串相撞 / 结构破损）
            assert 'href="href="' not in t, f'{f.name}: href 重复'
            assert t.count('<html') == 1 and t.count('</html>') == 1, f'{f.name}: html 标签异常'
            f.write_text(t, encoding='utf-8')

    ok = True
    for ri, (name, old, new, exp_n, exp_f) in enumerate(RULES):
        got_n, got_f = total_by_rule[ri], len(files_by_rule[ri])
        good = (got_n == exp_n and got_f == exp_f)
        ok &= good
        print(f'{"APPLY" if apply else "DRY":<6} {got_f:>6}  {name:<16} {got_n:>5} {exp_n:>5}  '
              f'{"✅" if good else f"⚠️ 不符（期望 {exp_n} 处 / {exp_f} 文件）"}')

    # ---- 替换后核验：旧词是否仍残留在这些句子里（只在落盘后做）----
    if apply:
        print()
        print('=== 替换后残留核验（按规则串计）===')
        resid = 0
        for f in GLOB:
            t = f.read_text(encoding='utf-8')
            for name, old, new, _, _ in RULES:
                if t.count(old):
                    print(f'  ⚠️ {f.name}: 仍存在旧串「{name}」× {t.count(old)}')
                    resid += t.count(old)
        print(f'  旧串残留 {resid} 处 ' + ('✅' if resid == 0 else '⚠️'))
        ok &= (resid == 0)
    else:
        print()
        print('（dry-run：跳过残留核验——未落盘，必然仍存在旧串）')

    # ---- 旧材质词的全局残留（含型号表，仅作报告，不判定失败）----
    print()
    print('=== 旧材质词全局残留（含型号表 —— 型号表本轮不动，故 >0 属预期）===')
    for f in GLOB:
        t = f.read_text(encoding='utf-8')
        hits = LEGACY_RE.findall(t)
        if hits:
            from collections import Counter
            print(f'  {f.name:<34} {dict(Counter(h.lower() for h in hits))}')

    print()
    print(('✅ 全部规则核对通过' if ok else '⚠️ 有规则不符，见上') +
          ('（已落盘）' if apply else '（dry-run 未落盘）'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
