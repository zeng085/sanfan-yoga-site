#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0-3: 给全站 Organization JSON-LD 节点补 sameAs（实体关联，AI 判断"你是谁"的核心依据）。

用法:
    1) 编辑 i18n_build/sameas.json，填入官方对外主页 URL（只填真实属于 FUJIAN SANFAN 的）
    2) python3 i18n_build/add_sameas.py           # 试跑，只打印将要改动的文件数
    3) python3 i18n_build/add_sameas.py --apply   # 真正写入

幂等：已有 sameAs 的节点不会重复添加。
覆盖：@graph 里的 Organization（首页/关于/材料页等）+ 博客页 author/publisher 的 Organization。

⚠️ 警告：sameAs 用于建立"实体同一性"。填错（例如填成同名同业 sanfanyoga.com 的 LinkedIn）
   会让 AI 把两家公司的身份混为一谈。只填自己控制的官方主页。
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = os.path.join(ROOT, 'i18n_build', 'sameas.json')
APPLY = '--apply' in sys.argv

SAMEAS = json.load(open(CFG, encoding='utf-8'))['sameAs'] if os.path.exists(CFG) else []
if not SAMEAS:
    print('sameas.json 为空 —— 先填入 URL 再跑。')
    sys.exit(1)


def inject(node):
    """递归：给 Organization 节点加 sameAs，返回是否改动"""
    changed = False
    if isinstance(node, dict):
        if node.get('@type') == 'Organization' and 'sameAs' not in node:
            node['sameAs'] = list(SAMEAS)
            changed = True
        for v in node.values():
            if inject(v):
                changed = True
    elif isinstance(node, list):
        for v in node:
            if inject(v):
                changed = True
    return changed


def process(path):
    src = open(path, encoding='utf-8').read()
    out = src
    n = 0

    def repl(m):
        global n
        body = m.group(1).strip()
        if '"Organization"' not in body:
            return m.group(0)
        try:
            data = json.loads(body)
        except Exception:
            return m.group(0)
        if not inject(data):
            return m.group(0)
        n += 1
        new = json.dumps(data, ensure_ascii=False, indent=2)
        # 保持原有缩进风格：原块以空格开头则整体缩进 2
        lead = m.group(0)[:len(m.group(0)) - len(m.group(0).lstrip())]
        if not lead:
            new = '\n' + '\n'.join('  ' + ln for ln in new.splitlines()) + '\n  '
        return '<script type="application/ld+json">' + new + '</script>'

    out = re.sub(r'<script type="application/ld\+json">(.*?)</script>', repl, src, flags=re.S)
    if out != src and APPLY:
        open(path, 'w', encoding='utf-8').write(out)
    return n, out != src


def main():
    files = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in ('.git', 'i18n_build', 'node_modules', 'outputs', '.workbuddy')]
        for fn in filenames:
            if fn.endswith('.html'):
                files.append(os.path.join(dirpath, fn))
    total = 0
    touched = 0
    for f in sorted(files):
        n, ch = process(f)
        if n:
            total += n
            touched += 1
    print(f'sameAs 条目: {len(SAMEAS)}')
    print(f'注入的 JSON-LD 块: {total}   文件: {touched}')
    print('模式:', '已写入' if APPLY else '试跑（加 --apply 才写入）')
    for u in SAMEAS:
        print('  -', u)


if __name__ == '__main__':
    main()
