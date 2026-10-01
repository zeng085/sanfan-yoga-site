#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
联动清理 Gyrotonic —— **第二批：生成源与词库**  2026-10-01

=====================================================================
为什么还要有第二批（第一批的教训）
=====================================================================
第一批 `remove_gyrotonic_20261001.py` 只清了**站点 HTML 产物**（10 个文件）。
于是留下一个隐形雷区：**生成源没同步**。

`i18n_build/build_pilates_data.py` 里那 7 处仍在，而它正是
`pilates-specialty.html` 的生成源 —— 只要有人重跑生成器，
美国注册商标 **Gyrotonic 就会原样回来**，而且没人会发现。

这正是本项目反复踩的「**产物 vs 源**」铁律：
  改产物不改源 = 埋了一颗定时炸弹。
（同类前科：`build_pilates_section.py:688` 的 `bi(...)` 列表项漏改。）

=====================================================================
第二批还顺手修掉一个「源与产物自相矛盾」
=====================================================================
`build_pilates_section.py` 里，族页的 pl-tag 与首页卡片的 cnt **共用同一个
`tag_en` 字段**（pl-tag 走 `tag_en.split(" · ")`，cnt 走整个 `tag_en`）。
我第一批替换时两处用了不同字面量：
  · 首页 cnt   → `Rotator & Tower Set`  ✅
  · 族页 pl-tag → `Rotator & Tower`     ❌ 少了个 "Set"
于是产物与生成器对不上（重跑会多出一个 "Set"）。本批统一为 `Rotator & Tower Set`。

=====================================================================
⚠️ 本批**不动** `ocr_catalog_pilates.py` 的匹配模式
=====================================================================
那里的 `Gyrotonic` 是**为了认出画册图上印的原词**（画册确实印了它）。
删掉会导致该页 OCR 归组错乱。只在旁边加注释说明，不动模式本身。

用法：
    python3 sync_gyrotonic_sources_20261001.py            # dry-run
    python3 sync_gyrotonic_sources_20261001.py --apply    # 落盘
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (相对路径, 旧串, 新串, 期望出现次数, 说明)
RULES = [
    # ---------- build_pilates_data.py：族页数据（tag/lead/型号名） ----------
    ('i18n_build/build_pilates_data.py',
     '"tag_en": "Bidirectional Bed · Gyrotonic Tower",',
     '"tag_en": "Bidirectional Bed · Rotator & Tower Set",', 1,
     '族页 tag_en（pl-tag 与首页 cnt 共用 → 必须含 Set）'),

    ('i18n_build/build_pilates_data.py',
     '"tag_zh": "双向梯床 · 禅柔塔架",',
     '"tag_zh": "双向梯床 · 回旋仪塔架",', 1,
     '族页 tag_zh（「禅柔」也是该商标的中文名）'),

    ('i18n_build/build_pilates_data.py',
     '"rehab and the Gyrotonic tower set (rotator + pulley tower) for three-dimensional "',
     '"rehab and the rotator + pulley tower set for three-dimensional "', 1,
     '族页 lead_en（跨行拼接，只替换不跨界的那一段）'),

    ('i18n_build/build_pilates_data.py',
     '做三维脊柱训练的禅柔组合"',
     '做三维脊柱训练的回旋仪 + 滑轮塔组合"', 1,
     '族页 lead_zh 前半'),

    ('i18n_build/build_pilates_data.py',
     '"（回旋仪 + 滑轮塔）。与其余器械共用同一套实木工艺，按单定制。"',
     '"。与其余器械共用同一套实木工艺，按单定制。"', 1,
     '族页 lead_zh 后半（去掉已并入前半的括注）'),

    ('i18n_build/build_pilates_data.py',
     '"FAS White Maple Gyrotonic Tower Set (Classic)"',
     '"FAS White Maple Rotator & Tower Set (Classic)"', 1,
     '型号名 NIS102（与站上型号表一致）'),

    ('i18n_build/build_pilates_data.py',
     '"FAS 白枫木经典款禅柔（回旋仪 + 滑轮塔）"',
     '"FAS 白枫木回旋仪 + 滑轮塔（经典款）"', 1,
     '型号中文名（与站上型号表一致）'),

    ('i18n_build/build_pilates_data.py',
     '# 五件套 / 禅柔：尺寸写在',
     '# 五件套 / 回旋仪塔架：尺寸写在', 1,
     '注释'),

    # ---------- translator.py：术语保护表 ----------
    ('i18n_build/translator.py',
     '    ("gyrotonic",       "Gyrotonic",       "Gyrotonic",       "Gyrotonic",'
     '       "Gyrotonic",       "ジャイロトニック",   "자이로토닉"),\n',
     '    # ⛔ 2026-10-01 移除 "gyrotonic" 条：该词是美国注册商标，已全站剔除。\n'
     '    #    术语保护表里留着它 = 「随时可能被翻译管线重新注入」。\n'
     '    #    不再保护的词，才不会被带回来。\n', 1,
     'PILATES_TERMS 词根表移除 gyrotonic（含 de/ja/ko 等 7 语写法）'),

    ('i18n_build/translator.py',
     '（双向梯床 + Gyrotonic 塔等非常规件）',
     '（双向梯床 + 回旋仪塔架等非常规件）', 1,
     'Specialty 族名注释'),

    # ---------- ocr_catalog_pilates.py：只加注释，不动模式 ----------
    ('i18n_build/ocr_catalog_pilates.py',
     '# 反例（不能当型号）：含冒号的都是规格行；含 mm 的是尺寸；纯数字是页码。',
     '# 反例（不能当型号）：含冒号的都是规格行；含 mm 的是尺寸；纯数字是页码。\n'
     '# ⚠️ 前缀里的 Gyrotonic 是**为了认出画册图上印的原词**（画册确实印了它），\n'
     '#    不代表我们要保留该型号：解析出的那台在 parse_catalog_models_v2_*.py 的\n'
     '#    EXCLUDE_MODELS 里被剔除。**不要因为「全站要清 Gyrotonic」而删掉这个匹配项**，\n'
     '#    删了会导致该页 OCR 归组错乱（它仍参与字段归组）。', 1,
     'OCR 前缀表加「保留原因」注释'),

    # ---------- 站点产物：补齐第一批漏掉的 "Set" ----------
    ('pilates/pilates-specialty.html',
     '<span class="lang-en">Rotator & Tower</span><span class="lang-zh">Rotator & Tower</span>',
     '<span class="lang-en">Rotator & Tower Set</span>'
     '<span class="lang-zh">Rotator & Tower Set</span>', 1,
     '族页 pl-tag（与生成器输出 + 首页 cnt 对齐）'),
]


def main():
    apply = '--apply' in sys.argv
    print('=== 联动清理 Gyrotonic · 第二批（生成源与词库）===')
    print(f'模式：{"APPLY（落盘）" if apply else "DRY-RUN（只检查）"}\n')

    cur, ok_all, touched = {}, True, set()
    for rel, old, new, exp, label in RULES:
        p = ROOT / rel
        if rel not in cur:
            cur[rel] = p.read_text(encoding='utf-8')
        n = cur[rel].count(old)
        # 幂等：改过之后 old 为 0 且 new 已在 → 视为已应用，不算错
        already = (n == 0) and (new in cur[rel])
        good = already or (n == exp)
        ok_all &= good
        flag = '✅' if good else '❌'
        note = f'{n} 次（期望 {exp}）'
        if already:
            note = '已应用（幂等跳过）'
        print(f'  {flag} {label:<46} {rel}:{note}')
        if not good:
            continue
        if not already:
            cur[rel] = cur[rel].replace(old, new)
            touched.add(rel)

    print()
    if not ok_all:
        print('❌ 有规则不匹配，已中止（未落盘任何文件）')
        return 1

    # ---------- 落盘前断言：确认没造出畸形 HTML ----------
    for rel in touched:
        if rel.endswith('.html'):
            out = cur[rel]
            for bad in ('href="href="', 'class="class="', '></span></span></span></span></span>'):
                assert bad not in out, f'{rel} 落盘断言失败：出现 {bad}'
            assert out.count('<span') == out.count('</span>'), \
                f'{rel} span 标签不配对：{out.count("<span")} vs {out.count("</span>")}'

    if not apply:
        print('（dry-run 不落盘；确认无误后加 --apply）')
        return 0

    for rel in sorted(touched):
        (ROOT / rel).write_text(cur[rel], encoding='utf-8')
        print(f'  💾 已写入 {rel}')

    # ---------- 落盘后核验 ----------
    print('\n=== 落盘后核验 ===')
    fails = 0
    for rel in touched:
        t = (ROOT / rel).read_text(encoding='utf-8')
        if rel.endswith('.py'):
            try:
                compile(t, rel, 'exec')
                print(f'  ✅ {rel} 语法通过')
            except SyntaxError as e:
                print(f'  ❌ {rel} 语法错误：{e}')
                fails += 1
        if rel.endswith('.html'):
            a, b = t.count('<span'), t.count('</span>')
            print(f'  {"✅" if a == b else "❌"} {rel} span 配对 {a}/{b}')
            fails += (a != b)

    # 商标词应收敛到 0（排除「故意保留」的 OCR 匹配项与注释）
    print('\n=== 商标词残留（应只剩注释/OCR 匹配项）===')
    import subprocess
    r = subprocess.run(['git', 'grep', '-n', '-i', '-I', '-E', 'gyrotonic|禅柔',
                        '--', 'i18n_build/*.py'], capture_output=True, text=True).stdout
    for line in r.splitlines():
        good = ('#' in line.split(':', 2)[-1].split('\n')[0] or
                'RE_MODEL_HEAD' in line or '|Gyrotonic|' in line)
        print(f'  {"ℹ️ " if good else "❌"} {line[:150]}')
        if not good:
            fails += 1

    print(f'\n{"✅ 第二批完成" if not fails else f"❌ {fails} 项异常"}')
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
