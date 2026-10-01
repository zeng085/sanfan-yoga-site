#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
材质口径统一 —— 第二批：**生成源与 AI 副驾文件**

第一批（fix_material_copy_20261001.py）改的是 8 个 HTML 产物。
但只改产物不改源，下次重新生成会把旧文案带回来，于是有了本脚本。

覆盖 8 类目标：
  A. llms.txt / llms-full.txt        —— ⭐ 线上可访问，AI 爬虫**直接读**，优先级最高
  B. pilates_faq_content.py          —— FAQ 文案源（Python 隐式拼接，跨行）
  C. pilates_faq_data.json           —— FAQ 数据（6 处，整串一行）
  D. build_pilates_section.py        —— ① 可定制列表 ② 板块首页 lead 的材质列表
  E. build_pilates_data.py           —— 核心床卡片描述（改后须同步 index.html 产物）
  F. geo_ai_endpoints_20260925.py    —— GEO 端点（同样是 AI 读的内容）

⚠️ 纪律：
  · 只替换「材质列表」片段，**不动** `%d models` 之类待决的结构数字
  · 落盘前验证：.py 过 py_compile、.json 过 json.loads
  · 落盘后核验：旧片段 0 残留

用法：
    python3 fix_material_copy_sources_20261001.py            # dry-run
    python3 fix_material_copy_sources_20261001.py --apply    # 落盘
"""
import json
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FAQ_OLD_EN = ('Frames are built in imported rubberwood, FAS-grade white maple, '
              'piano-lacquer white maple and Croatian beech, with rails, springs '
              'and bearings specified for studio duty.')
FAQ_NEW_EN = ('Material is set per model — see the material column in the model table '
              'above for the code you are considering; we machine in solid timber, '
              'aluminium and steel. For OEM and ODM programmes we build to the material '
              'and finish specification your own brand already uses. Rails, springs and '
              'bearings are specified for studio duty.')

# (相对路径, 旧片段, 新片段, 期望次数, 说明)
RULES = [
    # ---- A. AI 副驾文件（线上可访问）----
    ('llms.txt',
     'imported rubberwood, FAS white maple, Croatian beech, aluminium and 316 stainless hardware, piano lacquer finish',
     'solid timber, aluminium and 316 stainless hardware — material is set per model, and OEM/ODM builds follow your own brand\'s spec',
     1, 'llms.txt 材质列表'),
    ('llms-full.txt',
     'Materials: imported rubberwood, FAS white maple, Croatian beech, aluminium and 316 stainless hardware, piano lacquer finish.',
     "Materials: set per model — solid timber, aluminium and 316 stainless hardware. OEM and ODM programmes build to your own brand's material and finish spec.",
     1, 'llms-full.txt 材质列表'),

    # ---- B. FAQ 文案源（Python 隐式拼接，逐行匹配）----
    ('i18n_build/pilates_faq_content.py',
     '        "Frames are built in imported rubberwood, FAS-grade white maple, piano-lacquer white "\n'
     '        "maple and Croatian beech, with rails, springs and bearings specified for studio "\n'
     '        "duty. Products are tested against REACH, CA Prop 65 and 6P/7P, and the factory is "\n',
     '        "Material is set per model — see the material column in the model table above for "\n'
     '        "the code you are considering; we machine in solid timber, aluminium and steel. For "\n'
     '        "OEM and ODM programmes we build to the material and finish specification your own "\n'
     '        "brand already uses. Rails, springs and bearings are specified for studio duty. "\n'
     '        "Products are tested against REACH, CA Prop 65 and 6P/7P, and the factory is "\n',
     1, 'FAQ 源 · 英文答案'),
    ('i18n_build/pilates_faq_content.py',
     '        "床架采用进口橡胶木、FAS 级白枫木、钢琴漆白枫木与克罗地亚榉木，导轨、弹簧与轴承"\n'
     '        "按场馆级使用选型。产品按 REACH、加州 65 号提案与 6P/7P 送检，工厂通过 "\n',
     '        "材质按型号确定——请见上方型号表中该编号对应的材质列；我们的加工覆盖实木、"\n'
     '        "铝合金与钢材。OEM/ODM 项目可直接按你品牌现用的材质与表面工艺生产。导轨、弹簧"\n'
     '        "与轴承按场馆级使用选型。产品按 REACH、加州 65 号提案与 6P/7P 送检，工厂通过 "\n',
     1, 'FAQ 源 · 中文答案'),

    # ---- C. FAQ 数据 ----
    ('i18n_build/pilates_faq_data.json', FAQ_OLD_EN, FAQ_NEW_EN, 6, 'FAQ 数据 · 英文答案'),

    # ---- D. 区块生成源 ----
    ('i18n_build/build_pilates_section.py',
     '         "Domestic or imported rubberwood, FAS-grade white maple, piano lacquer, "\n'
     '         "Croatian beech, aluminium or 316 steel.",\n',
     '         "Solid timber, aluminium or steel; or we build to the material and finish "\n'
     '         "spec your own brand already uses.",\n',
     1, '区块源 · 可定制列表'),
    ('i18n_build/build_pilates_section.py',
     '"and the special pieces — %d models across %d lines, in imported rubberwood, "\n'
     '          "FAS-grade white maple, piano lacquer, Croatian beech, aluminium and 316 steel. "\n',
     '"and the special pieces — %d models across %d lines, in solid timber, "\n'
     '          "aluminium and 316 steel. "\n',
     1, '区块源 · 首页 lead 材质列表（保留 %d models 待决）'),

    # ---- E. 核心床卡片 ----
    # ⚠️ 这处是 Python 隐式拼接的**跨行**串，整段匹配对缩进极敏感（首次尝试就因
    #    把 19 空格写成 8 空格而 0 命中）。改用两个小片段分别替换，各自唯一且不依赖缩进。
    ('i18n_build/build_pilates_data.py',
     '"The reformer is the machine a studio is built around. We build it on imported "',
     '"The reformer is the machine a studio is built around. We build it on solid "',
     1, '卡片源 · reformer lead_en (前半)'),
    ('i18n_build/build_pilates_data.py',
     '"rubberwood, piano-lacquer or FAS-grade white maple and Croatian beech, with "',
     '"timber or aluminium, with "',
     1, '卡片源 · reformer lead_en (后半)'),
    ('i18n_build/build_pilates_data.py',
     '"lead_zh": "核心床是普拉提馆的立馆之本。我们用进口橡胶木、钢琴烤漆或 FAS 级白枫木、克罗地亚榉木做床身，"',
     '"lead_zh": "核心床是普拉提馆的立馆之本。我们用实木或铝合金做床身，"',
     1, '卡片源 · reformer lead_zh'),

    # ---- F. GEO 端点 ----
    ('i18n_build/geo_ai_endpoints_20260925.py',
     '"the yoga mats. Materials: imported rubberwood, FAS white maple, Croatian beech, "\n'
     '        "aluminium and 316 stainless hardware, piano lacquer finish."\n',
     '"the yoga mats. Materials: set per model — solid timber, aluminium and 316 "\n'
     '        "stainless hardware."\n',
     1, 'GEO 端点 · 材质列表'),
]

# 落盘后必须为 0 的旧片段（只查这些"口径句"，不查型号表数据）
LEGACY_SNIPPETS = [
    'imported rubberwood, FAS',
    'FAS-grade white maple, piano',
    'Croatian beech, aluminium',
]


def verify_syntax(p: Path):
    if p.suffix == '.py':
        py_compile.compile(str(p), doraise=True)
    elif p.suffix == '.json':
        json.loads(p.read_text(encoding='utf-8'))


def main():
    apply = '--apply' in sys.argv
    print(f'{"模式":<6} {"目标":<40} {"命中":>4} {"期望":>4}  {"语法":<6} 状态')
    print('-' * 84)
    ok = True
    per_file = {}

    for rel, old, new, exp, label in RULES:
        p = ROOT / rel
        if not p.exists():
            print(f'  ⚠️ 文件不存在: {rel}')
            ok = False
            continue
        t = p.read_text(encoding='utf-8')
        n = t.count(old)
        good = (n == exp)
        ok &= good
        per_file.setdefault(p, []).append((old, new))
        print(f'{"APPLY" if apply else "DRY":<6} {label:<40} {n:>4} {exp:>4}  {"—":<6} '
              f'{"✅" if good else "⚠️ 不符"}')
        if good and apply:
            p.write_text(t.replace(old, new), encoding='utf-8')

    # ---- 语法验证 ----
    if apply:
        print()
        print('=== 语法验证 ===')
        for p in per_file:
            try:
                verify_syntax(p)
                print(f'  ✅ {p.relative_to(ROOT)}')
            except Exception as e:
                print(f'  ⚠️ {p.relative_to(ROOT)}: {e}')
                ok = False

    # ---- 残留核验 ----
    print()
    if apply:
        print('=== 残留核验（口径句）===')
        resid = 0
        for rel in sorted({r[0] for r in RULES}):
            t = (ROOT / rel).read_text(encoding='utf-8')
            for s in LEGACY_SNIPPETS:
                c = t.count(s)
                if c:
                    print(f'  ⚠️ {rel}: 「{s}」× {c}')
                    resid += c
        print(f'  旧口径句残留 {resid} 处 ' + ('✅' if resid == 0 else '⚠️'))
        ok &= (resid == 0)
    else:
        print('（dry-run：跳过语法与残留核验）')

    print()
    print(('✅ 全部通过' if ok else '⚠️ 有不符项，见上') + ('（已落盘）' if apply else '（未落盘）'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
