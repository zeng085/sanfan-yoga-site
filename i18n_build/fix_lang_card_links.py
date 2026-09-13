#!/usr/bin/env python3
"""修复语言版页面中产品卡/缩略图回退到 products.html 的链接。
原理：英文站是权威源 —— 任何 <a href="...products/xxx.html"> 里出现的图片文件名
可以建立 「图片basename -> products/xxx.html」 映射；语言版同类锚点若 href 指向
products.html（回退），按其内层图片 basename 反查并改写为正确的详情页相对链接。
用法：python3 fix_lang_card_links.py [--dry]
"""
import re, os, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ['de', 'ja', 'ko', 'fr', 'it', 'es']
DRY = '--dry' in sys.argv

# ---------- 1. 从英文站建立 图片basename -> products/slug.html 映射 ----------
A_ANCHOR = re.compile(r'<a\b[^>]*href="([^"]*products/[^"/]+\.html)"[^>]*>(.*?)</a>', re.S)
IMG_SRC = re.compile(r'src="[^"]*/([^"/]+\.(?:webp|jpg|jpeg|png))"')

mapping = {}
conflicts = []
en_files = []
for dirpath, dirs, files in os.walk(ROOT):
    rel = os.path.relpath(dirpath, ROOT)
    if rel != '.' and (rel.startswith(('de/', 'ja/', 'ko/', 'fr/', 'it/', 'es/'))
                       or rel.startswith(('.git', 'i18n_build', 'outputs', '.workbuddy', 'node_modules'))):
        dirs[:] = []
        continue
    for fn in files:
        if fn.endswith('.html'):
            en_files.append(os.path.join(dirpath, fn))

for p in en_files:
    s = open(p, encoding='utf-8').read()
    for m in A_ANCHOR.finditer(s):
        href, inner = m.group(1), m.group(2)
        # 归一化：去掉 ../ 前缀，映射值统一为 products/slug.html
        href_n = re.sub(r'^(\.\./)+', '', href)
        for im in IMG_SRC.finditer(inner):
            base = im.group(1)
            if base in mapping and mapping[base] != href_n:
                conflicts.append((base, mapping[base], href_n))
            mapping[base] = href_n

print(f'EN 映射条目: {len(mapping)}, 冲突: {len(conflicts)}')
for c in conflicts[:10]:
    print('  冲突:', c)

# ---------- 2. 修复语言版 ----------
FALLBACK = re.compile(r'(<a\b[^>]*href=")([^"]*?)products\.html("[^>]*>)(.*?)(</a>)', re.S)
total_fixed = 0
per_file = collections.Counter()
unresolved = []

for L in LANGS:
    for dirpath, dirs, files in os.walk(os.path.join(ROOT, L)):
        dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules')]
        for fn in files:
            if not fn.endswith('.html'):
                continue
            p = os.path.join(dirpath, fn)
            s = open(p, encoding='utf-8').read()
            orig = s
            fixed_in_file = 0

            def repl(m):
                global fixed_in_file
                pre, inner = m.group(2), m.group(4)
                im = IMG_SRC.search(inner)
                if not im:
                    return m.group(0)
                base = im.group(1)
                target = mapping.get(base)
                if not target:
                    unresolved.append((os.path.relpath(p, ROOT), base))
                    return m.group(0)
                # group(2) 是 products.html 之前的前缀（'' 或 '../'）
                newhref = m.group(2) + target
                abs_target = os.path.normpath(os.path.join(os.path.dirname(p), newhref))
                if not os.path.isfile(abs_target):
                    unresolved.append((os.path.relpath(p, ROOT), base + ' -> 目标不存在 ' + newhref))
                    return m.group(0)
                if newhref != m.group(2) + '.html':
                    fixed_in_file += 1
                    return m.group(1) + newhref + m.group(3) + m.group(4) + m.group(5)
                return m.group(0)

            s = FALLBACK.sub(repl, s)
            if fixed_in_file and not DRY:
                open(p, 'w', encoding='utf-8').write(s)
            if fixed_in_file:
                per_file[os.path.relpath(p, ROOT)] = fixed_in_file
                total_fixed += fixed_in_file

print(f'\n修复链接总数: {total_fixed} ({"DRY" if DRY else "已写入"})，涉及文件 {len(per_file)} 个')
for p, n in sorted(per_file.items()):
    print(f'  {n:3d}  {p}')
if unresolved:
    print(f'\n未解决 {len(unresolved)} 条:')
    for u in unresolved[:20]:
        print('  ', u)
