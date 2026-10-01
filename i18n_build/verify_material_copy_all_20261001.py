#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
材质口径统一 —— **总验证（可复用回归脚本）**  2026-10-01

三批改动共用这一个入口核对。以后任何一次「以画册为准」的口径调整，
跑这个脚本就知道有没有漏改的副本。

为什么需要它（本次踩的坑）：
  同一句材质文案在仓库里有 **6 类副本**，改漏任何一类都会留下自相矛盾的页面：
    ① HTML 可见文本（`.lang-en` / `.lang-zh` 配对）
    ② HTML 里的 JSON-LD（FAQPage answer / Product description）—— 正则切标签切不到
    ③ 板块首页 pilates/index.html（是**产物**，不跟源自动同步）
    ④ 族页 hero（如 pilates-reformer.html 的 lead）—— 与首页卡片**同源不同份**
    ⑤ 生成源（pilates_faq_content.py / pilates_faq_data.json / build_pilates_*.py）
    ⑥ llms.txt / llms-full.txt —— ⭐ 线上可访问，AI 爬虫直接读

用法：
    python3 verify_material_copy_all_20261001.py
返回码 0 = 全部通过。

⚠️ 写判据时的坑（2026-10-01 踩过，务必遵守）：
  **判据是对「文件正文」成立的，不是对「渲染后字符串」成立的。**
  Python 会把相邻字符串字面量隐式拼接，源码被折行后「完整句」在文件里
  从不连续出现 —— 例：build_pilates_data.py 里
      "… We build it on solid "
      "timber or aluminium, with "
  于是检查 `'We build it on solid timber or aluminium'` 恒为 0，报假缺陷。
  正确做法：① 源码侧只查**不跨行**的片段；② 另加一条对**渲染产物**
  （pilates/index.html）的判据来覆盖真实可见文案。两者都要有。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (作用域 glob 或路径, 必须出现的串, 期望最少次数, 期望最多次数, 说明)
# 期望值均为 2026-10-01 实测值，不是估算。改动文案后请重新实测再改这里。
MUST_HAVE = [
    # —— 渲染产物（真实用户可见）——
    ('pilates/*.html', 'Material is set per model', 16, 16, '新 FAQ 口径句（7 页×2 + 首页×2）'),
    ('pilates/*.html', 'Solid timber, aluminium or steel; or we build to the material', 7, 7, '新可定制列表（7 页×1）'),
    ('pilates/pilates-ladder-barrel.html', 'Material is listed per model', 2, 2, '梯桶页专用口径句（schema+正文）'),
    ('pilates/index.html', 'in solid timber, aluminium and 316 steel.', 1, 1, '首页 lead 材质'),
    ('pilates/index.html', 'We build it on solid timber or aluminium', 1, 1, '首页卡片 · reformer（渲染后完整句）'),
    ('pilates/pilates-reformer.html', 'We build it on solid timber or aluminium, with', 2, 2, '核心床 leaf（schema+HTML 各 1）'),
    # —— 生成源（注意有的是跨行拼接，只能查片段）——
    ('i18n_build/pilates_faq_content.py', 'Material is set per model', 1, 1, 'FAQ 源 · 英文'),
    ('i18n_build/pilates_faq_content.py', '材质按型号确定', 1, 1, 'FAQ 源 · 中文'),
    ('i18n_build/pilates_faq_data.json', 'Material is set per model', 6, 6, 'FAQ 数据 · 6 条'),
    ('i18n_build/build_pilates_section.py', 'Solid timber, aluminium or steel', 2, 2, '区块源 · 可定制列表（2 处）'),
    ('i18n_build/build_pilates_data.py', 'timber or aluminium, with ', 1, 1, '卡片源 · reformer（跨行片段）'),
    # —— AI 爬虫直读文件（线上可访问）——
    ('llms.txt', 'material is set per model', 1, 1, 'llms.txt 新口径'),
    ('llms-full.txt', 'Materials: set per model', 1, 1, 'llms-full.txt 新口径'),
]

MUST_NOT_HAVE = [
    ('pilates/*.html', 'Frames are built in imported rubberwood', '旧 FAQ 句'),
    ('pilates/*.html', 'Domestic or imported rubberwood, FAS-grade white maple, piano lacquer', '旧可定制列表'),
    ('pilates/index.html', 'in imported rubberwood, FAS-grade white maple, piano lacquer', '首页旧 lead'),
    ('pilates/index.html', 'We build it on imported rubberwood', '首页卡片旧句 · reformer'),
    ('pilates/*.html', 'Material is listed per model in the 2026 catalogue', '梯桶页以外的旧专用句（不应存在）'),
    ('pilates/pilates-reformer.html', 'We build it on imported rubberwood', '核心床页旧 lead'),
    ('i18n_build/pilates_faq_content.py', 'Frames are built in imported rubberwood', 'FAQ 源旧句'),
    ('i18n_build/pilates_faq_data.json', 'Frames are built in imported rubberwood', 'FAQ 数据旧句'),
    ('i18n_build/build_pilates_section.py', 'Domestic or imported rubberwood', '区块源旧列表'),
    ('i18n_build/build_pilates_data.py', 'rubberwood, piano-lacquer or FAS-grade white maple', '卡片源旧 lead'),
    ('llms.txt', 'imported rubberwood, FAS white maple', 'llms.txt 旧口径'),
    ('llms-full.txt', 'imported rubberwood, FAS white maple', 'llms-full.txt 旧口径'),
    ('i18n_build/geo_ai_endpoints_20260925.py', 'imported rubberwood, FAS white maple', 'GEO 端点旧口径'),
]

# 预期**仍存在**（型号表产品数据，本轮不动），仅作报告
EXPECTED_LEGACY = re.compile(r'(rubberwood|white maple|Croatian beech|piano.?lacquer)', re.I)


def expand(scope: str):
    if '*' in scope:
        return sorted(ROOT.glob(scope))
    return [ROOT / scope]


def main():
    ok = True

    print('=== A. 必须存在（新口径已落位）===')
    for scope, needle, lo, hi, label in MUST_HAVE:
        files = expand(scope)
        actual = sum(f.read_text(encoding='utf-8').count(needle) for f in files if f.exists())
        good = lo <= actual <= hi
        ok &= good
        print(f'  {"✅" if good else "⚠️ "} {label:<28} {scope:<42} {actual} 次'
              f'{"" if good else f"（期望 {lo}~{hi}）"}')

    print()
    print('=== B. 必须不存在（旧口径已清）===')
    for scope, needle, label in MUST_NOT_HAVE:
        files = expand(scope)
        actual = sum(f.read_text(encoding='utf-8').count(needle) for f in files if f.exists())
        good = (actual == 0)
        ok &= good
        print(f'  {"✅" if good else "⚠️ "} {label:<28} {scope:<42} {actual} 处')

    print()
    print('=== C. 语法/格式完整性 ===')
    for rel, kind in [('i18n_build/pilates_faq_data.json', 'json'),
                      ('i18n_build/pilates_faq_content.py', 'py'),
                      ('i18n_build/build_pilates_section.py', 'py'),
                      ('i18n_build/build_pilates_data.py', 'py')]:
        p = ROOT / rel
        try:
            if kind == 'json':
                json.loads(p.read_text(encoding='utf-8'))
            else:
                compile(p.read_text(encoding='utf-8'), str(p), 'exec')
            print(f'  ✅ {rel}')
        except Exception as e:
            print(f'  ⚠️ {rel}: {e}')
            ok = False

    print()
    print('=== D. 仍存在的旧材质词（预期：**仅型号表产品数据**，本轮不动）===')
    # 分类器：型号名 vs 真·文案句。
    # 为什么要分类：早先只按「长度 ≥20 且含材质词」标记，结果把 15 个**型号名**
    # 和 12 个**型号表材质列词条**全报成「疑似文案句」，看的人会以为改漏了
    # → 工具报假警 ＝ 下次没人信它。三桶判据（全部实测校准）：
    #   ① 型号名     = 含产品名词（Reformer/Cadillac/…）且 ≤9 词
    #   ② 材质词条   = ≤4 词（型号表 Material 列的值，如 "Thai 5A-grade rubberwood"）
    #   ③ 其余       = 疑似文案句（真·散文句，才是需要人工看的）
    MODEL_NOUN = re.compile(
        r'\b(Reformer|Cadillac|Wunda|Chair|Barrel|Corrector|Ladder|Bed|Studio|'
        r'Tower|Trapeze|Table|Set|Combo|Mat|Pole)\b', re.I)
    for f in sorted((ROOT / 'pilates').glob('*.html')):
        t = f.read_text(encoding='utf-8')
        hits = EXPECTED_LEGACY.findall(t)
        if not hits:
            continue
        modelish, vocab, risky = [], [], []
        for m in re.finditer(r'>([^<>]{20,})<', t):
            seg = m.group(1).strip()
            if not EXPECTED_LEGACY.search(seg) or seg.startswith('{'):
                continue
            words = seg.split()
            if MODEL_NOUN.search(seg) and len(words) <= 9:
                modelish.append(seg[:60])
            elif len(words) <= 4:
                vocab.append(seg[:60])
            else:
                risky.append(seg[:60])
        tag = f'   型号名 {len(modelish)} / 材质词条 {len(vocab)}（均预期保留）'
        if risky:
            tag += f'   ⚠️ 疑似散文句 {len(risky)} 条'
        print(f'  {f.name:<34} {len(hits):>3} 处{tag}')
        for s in risky[:5]:
            print(f'      ⚠️ → {s}')

    print()
    print('✅ 全部通过' if ok else '⚠️ 有不符项，见上')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
