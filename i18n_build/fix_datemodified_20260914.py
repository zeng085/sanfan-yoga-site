#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0-2: 给所有 blog 文章的 Article JSON-LD 补/统一 dateModified。
P0-2b: 语言版 Article 的 mainEntityOfPage 原本错指 EN URL，改为自身 URL（与 canonical 对齐）。

幂等：重复执行不会叠加。
范围：blog/*.html 与 {de,ja,ko,fr,it,es}/blog/*.html 共 70 个文件。
"""
import re
import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE_MOD = "2026-09-14"

changed_dm = 0
changed_mp = 0
touched = []


def fix_article_jsonld(html: str, self_url: str):
    """只改 Article/BlogPosting 那个 ld+json 块里的 dateModified / mainEntityOfPage"""
    global changed_dm, changed_mp
    out = html

    def repl(m):
        global changed_dm, changed_mp
        block = m.group(1)
        if '"@type": "Article"' not in block and '"@type":"Article"' not in block \
           and '"@type": "BlogPosting"' not in block:
            return m.group(0)
        orig = block

        # --- dateModified ---
        if '"dateModified"' in block:
            new = re.sub(r'"dateModified":\s*"[^"]*"', f'"dateModified": "{DATE_MOD}"', block)
            if new != block:
                changed_dm += 1
        else:
            # 插到 datePublished 之后；没有 datePublished 就插到 headline 之后
            if '"datePublished"' in block:
                new = re.sub(
                    r'("datePublished":\s*"[^"]*",?)',
                    lambda mm: mm.group(1) + f'\n  "dateModified": "{DATE_MOD}",',
                    block, count=1)
                changed_dm += 1
            else:
                new = re.sub(
                    r'("headline":\s*"[^"]*",?)',
                    lambda mm: mm.group(1) + f'\n  "dateModified": "{DATE_MOD}",',
                    block, count=1)
                changed_dm += 1
        block = new

        # --- mainEntityOfPage ---
        if '"mainEntityOfPage"' in block:
            nb = re.sub(r'"mainEntityOfPage":\s*"[^"]*"',
                        f'"mainEntityOfPage": "{self_url}"', block)
            if nb != block:
                changed_mp += 1
            block = nb

        if block == orig:
            return m.group(0)
        return m.group(0).replace(orig, block)

    out = re.sub(r'<script type="application/ld\+json">(.*?)</script>',
                 repl, out, flags=re.S)
    return out


def main():
    files = sorted(glob.glob(os.path.join(ROOT, 'blog', '*.html')))
    for lang in ('de', 'ja', 'ko', 'fr', 'it', 'es'):
        files += sorted(glob.glob(os.path.join(ROOT, lang, 'blog', '*.html')))

    for f in files:
        rel = os.path.relpath(f, ROOT)
        self_url = 'https://fjsanfan.com/' + rel.replace(os.sep, '/')
        src = open(f, encoding='utf-8').read()
        dst = fix_article_jsonld(src, self_url)
        if dst != src:
            open(f, 'w', encoding='utf-8').write(dst)
            touched.append(rel)

    print(f'dateModified 改动: {changed_dm}')
    print(f'mainEntityOfPage 改动: {changed_mp}')
    print(f'写入文件: {len(touched)}')

    # 校验：所有文件都能被 json 解析 + 日期齐全
    import json
    bad = []
    for f in files:
        s = open(f, encoding='utf-8').read()
        for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
            t = m.group(1).strip()
            if '"Article"' not in t and '"BlogPosting"' not in t:
                continue
            try:
                d = json.loads(t)
            except Exception as e:
                bad.append((os.path.relpath(f, ROOT), f'JSON 解析失败: {e}'))
                continue
            if d.get('dateModified') != DATE_MOD:
                bad.append((os.path.relpath(f, ROOT), f"dateModified={d.get('dateModified')}"))
            if d.get('mainEntityOfPage') != 'https://fjsanfan.com/' + os.path.relpath(f, ROOT).replace(os.sep, '/'):
                bad.append((os.path.relpath(f, ROOT), f"mainEntityOfPage={d.get('mainEntityOfPage')}"))
    if bad:
        print('\n❌ 校验未通过:')
        for b in bad[:20]:
            print('  ', b)
        sys.exit(1)
    print('✅ 全部 70 个 blog 页 JSON-LD 校验通过')


if __name__ == '__main__':
    main()
