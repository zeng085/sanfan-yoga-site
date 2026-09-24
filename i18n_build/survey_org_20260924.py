#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全站 Organization 节点现状普查：有多少页有/没有、现有节点的形状分布。"""
import collections
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LDS = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
SKIP = {'.git', 'i18n_build', 'outputs', '.workbuddy', 'node_modules'}


def orgs(s):
    out = []

    def walk(n):
        if isinstance(n, dict):
            if n.get('@type') == 'Organization':
                out.append(n)
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)
    for b in LDS.findall(s):
        try:
            walk(json.loads(b))
        except Exception:
            pass
    return out


files = []
for dp, dn, fn in os.walk(ROOT):
    dn[:] = [d for d in dn if d not in SKIP]
    for f in fn:
        if f.endswith('.html') and f != 'product.html':
            files.append(os.path.join(dp, f))
files.sort()

noorg, byshape = [], {}
for f in files:
    o = orgs(open(f, encoding='utf-8').read())
    if not o:
        noorg.append(f)
        continue
    for n in o:
        byshape.setdefault(('@id' in n, tuple(sorted(n.keys()))), []).append(os.path.relpath(f, ROOT))

print('总 HTML:', len(files), '| 含 Organization:', len(files) - len(noorg), '| 无:', len(noorg))
print()
print('=== 现有 Organization 的「形状」分布 ===')
for (hasid, keys), fs in sorted(byshape.items(), key=lambda kv: -len(kv[1])):
    print(f'  @id={hasid}  出现数={len(fs):5d}  keys={list(keys)}')
    print(f'      例: {fs[:3]}')
print()
print('=== 无 Organization 的页按目录分布 ===')
c = collections.Counter(os.path.dirname(f) or '.' for f in noorg)
for d, n in c.most_common(25):
    print(f'  {n:5d}  {d}')
print()
print('=== 无 Organization 的页（前 15 个）===')
for f in noorg[:15]:
    print('  ', os.path.relpath(f, ROOT))
