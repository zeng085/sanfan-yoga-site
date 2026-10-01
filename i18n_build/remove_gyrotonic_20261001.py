#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剔除 `Gyrotonic`（美国注册商标）—— 2026-10-01

背景：用户决策「Gyrotonic 的信息剔除掉」。上一步只在**画册数据层**剔除了 p40 那台，
      但站上旧型号表里还有 `NIS102` 这个型号名带商标，且已扩散到 6 个语言版。

范围实测（不是猜的）：
  · EN：pilates/index.html（2 处）、pilates/pilates-specialty.html（5 处）
  · 语言版：de/es/fr/it 用拉丁字母 `Gyrotonic`；**ja 用 ジャイロトニック、ko 用 자이로토닉**
    → 只 grep 英文会漏掉 ja/ko 两个语言版，必须按语言分别处理。

替换原则：**不造新名称**。各语言的替代词全部取自该页面**已有的产品描述词**
  （即正文里已经写着的「回旋仪 + 滑轮塔」对应说法），只是把商标词摘掉。

⚠️ 语言版按项目铁律**手工注入译文**，不用批次重生成（会带漂移 + 配额降级）。

用法：
    python3 remove_gyrotonic_20261001.py            # dry-run
    python3 remove_gyrotonic_20261001.py --apply    # 落盘
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

IDX = 'pilates/index.html'
SPC = 'pilates/pilates-specialty.html'

# (相对路径, 旧, 新, 期望次数)  —— 长的规则必须排在短的前面
RULES = [
    # ================= EN =================
    (SPC, 'FAS White Maple Gyrotonic Tower Set (Classic)', 'FAS White Maple Rotator & Tower Set (Classic)', 2),
    (SPC, 'the Gyrotonic tower set (rotator + pulley tower)', 'the rotator + pulley tower set', 2),
    (SPC, 'Gyrotonic Tower', 'Rotator & Tower', 2),          # tag EN + tag ZH，各 1
    (SPC, 'FAS 白枫木经典款禅柔（回旋仪 + 滑轮塔）', 'FAS 白枫木回旋仪 + 滑轮塔（经典款）', 1),
    (SPC, '禅柔组合（回旋仪 + 滑轮塔）', '回旋仪 + 滑轮塔组合', 1),
    (IDX, '· Gyrotonic Tower', '· Rotator & Tower Set', 1),
    (IDX, 'the Gyrotonic tower set (rotator + pulley tower)', 'the rotator + pulley tower set', 1),
    (IDX, '禅柔塔架', '回旋仪塔架', 1),
    (IDX, '禅柔组合（回旋仪 + 滑轮塔）', '回旋仪 + 滑轮塔组合', 1),

    # ================= DE =================
    ('de/pilates/pilates-specialty.html', 'FAS Weißahorn-Gyrotonic-Tower-Set (Classic)', 'FAS Weißahorn-Rotator-Tower-Set (Classic)', 2),
    ('de/pilates/pilates-specialty.html', '„Gyrotonic“-Turm-Set', 'Rotator-Turm-Set', 2),
    ('de/pilates/pilates-specialty.html', 'Gyrotonic Turm', 'Rotator-Turm', 1),
    ('de/pilates/index.html', '„Gyrotonic“-Tower-Set', 'Rotator-Tower-Set', 1),
    ('de/pilates/index.html', '„Gyrotonic“-Turm', 'Rotator-Turm', 1),

    # ================= ES =================
    ('es/pilates/pilates-specialty.html', 'Conjunto de torre FAS de arce blanco «Gyrotonic» (Clásico)', 'Conjunto de torre FAS de arce blanco (Clásico)', 1),
    # `«Gyrotonic» ` 连**尾随空格**一起删，否则会留双空格（`de torre  (torno…`）
    ('es/pilates/pilates-specialty.html', '«Gyrotonic» ', '', 3),
    ('es/pilates/pilates-specialty.html', 'Gyrotonic Torre', 'Torre del rotador', 1),
    ('es/pilates/index.html', 'Torre «Gyrotonic»', 'Torre del rotador', 1),
    ('es/pilates/index.html', 'conjunto de torres «Gyrotonic»', 'conjunto de torre del rotador', 1),

    # ================= FR =================
    ('fr/pilates/pilates-specialty.html', 'l’ensemble « Gyrotonic »', 'l’ensemble', 2),
    ('fr/pilates/pilates-specialty.html', '«Gyrotonic» ', '', 2),
    ('fr/pilates/pilates-specialty.html', 'Gyrotonic Tour', 'Tour de rotation', 1),
    ('fr/pilates/index.html', 'Tour «Gyrotonic»', 'Tour de rotation', 1),
    ('fr/pilates/index.html', 'le kit « Gyrotonic »', 'la tour de rotation', 1),

    # ================= IT =================
    ('it/pilates/pilates-specialty.html', 'il set a torre Gyrotonic', 'il set a torre', 2),
    # ⚠️ 引号形态不一致：schema 用**弯引号** “Gyrotonic”，HTML 表格用**直引号** "Gyrotonic"。
    #    只匹配一种会漏掉另一种（实测漏了表格那一处）。
    ('it/pilates/pilates-specialty.html', 'con finitura “Gyrotonic” ', '', 1),
    ('it/pilates/pilates-specialty.html', 'in acero bianco "Gyrotonic" (Classic)', 'in acero bianco (Classic)', 1),
    ('it/pilates/pilates-specialty.html', 'Gyrotonic Torre', 'Torre del rotatore', 1),
    ('it/pilates/index.html', 'Torre “Gyrotonic”', 'Torre del rotatore', 1),
    ('it/pilates/index.html', 'il set a torre Gyrotonic', 'il set a torre', 1),

    # ================= JA（片假名，grep 英文查不到）=================
    ('ja/pilates/pilates-specialty.html', '「ジャイロトニック」タワーセット', 'ローテータータワーセット', 2),
    ('ja/pilates/pilates-specialty.html', 'ホワイトメープルジャイロトニックタワーセット', 'ホワイトメープル ローテータータワーセット', 1),
    ('ja/pilates/pilates-specialty.html', 'ジャイロトニック タワー', 'ローテータータワー', 2),   # tag + 表格
    ('ja/pilates/index.html', '「ジャイロトニックタワーセット（ローテーター＋プーリータワー）」', '「ローテータータワーセット（プーリータワー付き）」', 1),
    ('ja/pilates/index.html', 'ジャイロトニックタワー', 'ローテータータワー', 1),

    # ================= KO（韩文，grep 英文查不到）=================
    ('ko/pilates/pilates-specialty.html', '메이플자이로토닉타워', '메이플 회전대 타워', 2),   # schema + 表格
    ('ko/pilates/pilates-specialty.html', '‘자이로토닉’ 타워 세트', '‘회전대’ 타워 세트', 2),
    ('ko/pilates/pilates-specialty.html', '자이로토닉 타워', '회전대 타워', 1),   # tag
    ('ko/pilates/index.html', '‘자이로토닉’ 타워', '‘회전대’ 타워', 2),   # 卡片 cnt + 正文
]

# 商标词的全部书写形态（落盘后必须全为 0）
TRADEMARK = re.compile(r'(Gyrotonic|禅柔|ジャイロトニック|자이로토닉|자이로토닉)', re.I)


def main():
    apply = '--apply' in sys.argv
    print(f'{"模式":<6} {"文件":<34} {"命中":>4} {"期望":>4}  状态')
    print('-' * 64)
    ok = True
    touched = set()

    # ⚠️ 必须**按顺序在内存里模拟替换**：规则有前后依赖
    #   （如 EN 的 `Gyrotonic Tower Set (Classic)` 必须先于 tag 的 `Gyrotonic Tower`）。
    #   否则 dry-run 报的 count 是「未替换前」的原始值，会一连串假告警。
    cur = {}

    for rel, old, new, exp in RULES:
        p = ROOT / rel
        if not p.exists():
            print(f'  ⚠️ 缺文件 {rel}')
            ok = False
            continue
        if rel not in cur:
            cur[rel] = p.read_text(encoding='utf-8')
        n = cur[rel].count(old)
        # 幂等：已跑过一轮的规则（旧串已消失、新串已在位）视为已完成，而不是报"不符"
        already = (n == 0) and (new == '' or new in cur[rel])
        good = already or (n == exp)
        ok &= good
        short = (old[:26] + '…') if len(old) > 27 else old
        mark = '✅ 已完成' if already else ('✅' if good else '⚠️')
        print(f'{"APPLY" if apply else "DRY":<6} {rel.split("/")[-1][:16]:<34} {n:>4} {exp:>4}  '
              f'{mark}  {short}')
        if good:
            cur[rel] = cur[rel].replace(old, new)
            touched.add(p)

    if apply:
        for rel, t in cur.items():
            (ROOT / rel).write_text(t, encoding='utf-8')

    # ---- 商标词残留核验（全部 10 个文件）----
    if apply:
        print()
        print('=== 商标词残留核验（10 个文件）===')
        files = [IDX, SPC] + [f'{L}/pilates/{n}' for L in ('de', 'es', 'fr', 'it', 'ja', 'ko')
                              for n in ('index.html', 'pilates-specialty.html')]
        resid = 0
        for rel in files:
            t = (ROOT / rel).read_text(encoding='utf-8')
            hits = TRADEMARK.findall(t)
            if hits:
                print(f'  ⚠️ {rel}: {hits}')
                resid += len(hits)
        print(f'  商标词残留 {resid} 处 ' + ('✅ 已彻底剔除' if resid == 0 else '⚠️'))
        ok &= (resid == 0)

        # 结构完整性
        print()
        print('=== HTML 结构 ===')
        for p in sorted(touched):
            t = p.read_text(encoding='utf-8')
            bad = []
            for tag in ['html', 'head', 'body', 'section', 'div', 'table', 'tr', 'td', 'ul', 'li', 'p', 'span', 'script']:
                o = len(re.findall(rf'<{tag}(?:\s[^>]*)?>', t))
                c = len(re.findall(rf'</{tag}>', t))
                if o != c:
                    bad.append(f'{tag}:{o}/{c}')
            print(f'  {"✅" if not bad else "⚠️ "} {p.relative_to(ROOT)}' + (f'  {bad}' if bad else ''))
            ok &= (not bad)
    else:
        print()
        print('（dry-run：跳过残留核验）')

    print()
    print(('✅ 全部通过' if ok else '⚠️ 有不符项') + ('（已落盘）' if apply else '（未落盘）'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
