#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
材质口径统一 —— 第三批：**板块首页（index.html 产物）+ 其剩余源**

为什么需要第三批：
  第二批只改了**源**（build_pilates_section.py / build_pilates_data.py），
  但 `pilates/index.html` 是**已完成生成的产物**，不会自动跟着变 ——
  于是出现「源已改、产物未改」的断层。本批把产物补齐，并处理漏掉的一处源。

覆盖 4 处 × 中英 = 7 个替换点：
  ① index.html lead 段材质列表       ← 对应 build_pilates_section.py:607
  ② index.html 核心床卡片描述         ← 对应 build_pilates_data.py:33
  ③ index.html 「为什么选我们」列表项  ← 对应 build_pilates_section.py:688（**第二批漏掉的源**）
  ④ build_pilates_section.py:688 源本身

⚠️ 只改材质片段，**不动** `41 models across 8 lines` / `Same factory as our yoga mat line`
   这两处（属结构性问题，待用户定）。

用法：
    python3 fix_material_copy_index_20261001.py            # dry-run
    python3 fix_material_copy_index_20261001.py --apply    # 落盘
"""
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

RULES = [
    # ---------- ① lead 段 ----------
    ('pilates/index.html',
     'in imported rubberwood, FAS-grade white maple, piano lacquer, Croatian beech, aluminium and 316 steel.',
     'in solid timber, aluminium and 316 steel.',
     1, 'index · lead 段 EN'),
    ('pilates/index.html',
     '材质覆盖进口橡胶木、FAS 级白枫木、钢琴烤漆、克罗地亚榉木、铝合金与 316 钢。',
     '材质覆盖实木、铝合金与 316 钢。',
     1, 'index · lead 段 ZH'),

    # ---------- ② 核心床卡片 ----------
    ('pilates/index.html',
     'We build it on imported rubberwood, piano-lacquer or FAS-grade white maple and Croatian beech, with',
     'We build it on solid timber or aluminium, with',
     1, 'index · 卡片 EN'),
    ('pilates/index.html',
     '我们用进口橡胶木、钢琴烤漆或 FAS 级白枫木、克罗地亚榉木做床身，',
     '我们用实木或铝合金做床身，',
     1, 'index · 卡片 ZH'),

    # ---------- ③ 列表项（产物）----------
    ('pilates/index.html',
     '<span class="lang-en">Imported rubberwood, FAS-grade white maple, piano lacquer, Croatian beech</span>',
     '<span class="lang-en">Solid timber, aluminium or steel</span>',
     1, 'index · 列表项 EN'),
    ('pilates/index.html',
     '<span class="lang-zh">进口橡胶木、FAS 级白枫木、钢琴烤漆、克罗地亚榉木</span>',
     '<span class="lang-zh">实木、铝合金或钢材</span>',
     1, 'index · 列表项 ZH'),

    # ---------- ④ 列表项（源，第二批漏掉）----------
    ('i18n_build/build_pilates_section.py',
     'bi("Imported rubberwood, FAS-grade white maple, piano lacquer, Croatian beech",\n'
     '          "进口橡胶木、FAS 级白枫木、钢琴烤漆、克罗地亚榉木"),',
     'bi("Solid timber, aluminium or steel",\n'
     '          "实木、铝合金或钢材"),',
     1, '区块源 · 列表项（补漏）'),
]


def main():
    apply = '--apply' in sys.argv
    print(f'{"模式":<6} {"目标":<26} {"命中":>4} {"期望":>4}  状态')
    print('-' * 62)
    ok = True
    touched = set()

    for rel, old, new, exp, label in RULES:
        p = ROOT / rel
        t = p.read_text(encoding='utf-8')
        n = t.count(old)
        good = (n == exp)
        ok &= good
        print(f'{"APPLY" if apply else "DRY":<6} {label:<26} {n:>4} {exp:>4}  '
              f'{"✅" if good else "⚠️ 不符"}')
        if good and apply:
            p.write_text(t.replace(old, new), encoding='utf-8')
            touched.add(p)

    if apply:
        print()
        print('=== 语法 / 结构验证 ===')
        for p in touched:
            if p.suffix == '.py':
                try:
                    py_compile.compile(str(p), doraise=True)
                    print(f'  ✅ {p.relative_to(ROOT)}  py_compile')
                except Exception as e:
                    print(f'  ⚠️ {p.relative_to(ROOT)}: {e}')
                    ok = False

        # HTML 结构
        h = ROOT / 'pilates/index.html'
        t = h.read_text(encoding='utf-8')
        import re
        bad = []
        for tag in ['html', 'head', 'body', 'section', 'div', 'ul', 'li', 'details', 'p', 'span']:
            o = len(re.findall(rf'<{tag}(?:\s[^>]*)?>', t))
            c = len(re.findall(rf'</{tag}>', t))
            if o != c:
                bad.append(f'{tag}:{o}/{c}')
        print('  ' + ('✅ index.html 标签配对 OK' if not bad else f'⚠️ index.html: {bad}'))
        ok &= (not bad)

        # 残留
        print()
        print('=== 残留核验（本批 4 处旧串）===')
        resid = sum((ROOT / r[0]).read_text(encoding='utf-8').count(r[1]) for r in RULES)
        print(f'  残留 {resid} 处 ' + ('✅' if resid == 0 else '⚠️'))
        ok &= (resid == 0)
    else:
        print()
        print('（dry-run：跳过验证）')

    print()
    print(('✅ 全部通过' if ok else '⚠️ 有不符项') + ('（已落盘）' if apply else '（未落盘）'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
