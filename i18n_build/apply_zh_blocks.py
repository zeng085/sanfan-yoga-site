#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 i18n_build/zhblocks/<page>.zh.html 的中文正文，替换进 blog/<page>.html 的 .lang-zh 块内层。

背景：blog 文章页采用「块级整块 div」语言机制（<div class="lang-en">整篇</div> +
<div class="lang-zh">…</div>）。2026-09-13 的 a038d76 把 8 篇的中文完整版覆盖成了 3 段摘要，
本脚本把人工重写的中文全文灌回去。

设计要点：
- 只改 .lang-zh 块内 <div class="article-body"> 的内层；头部（post-meta/h1/lead-p/封面图）保留。
- 幂等：重复执行结果一致。
- 不碰 .lang-en。
用法：python3 i18n_build/apply_zh_blocks.py [--check]
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOCKS = os.path.join(ROOT, 'i18n_build', 'zhblocks')

PAGES = [
    '7day-sampling',
    'compliance',
    'custom-sizes',
    'private-label-yoga-mats',
    'tpe-vs-pu',
    'vet-factory',
    'yoga-mat-materials',
    'yoga-mat-spec-guide',
]

DIV_RE = re.compile(r'<div\b|</div>')


def match_div(text, start):
    """start 指向 '<div' 的 '<'，返回配对的 '</div>' 结束下标（不含）。"""
    depth, k = 0, start
    while k < len(text):
        m = DIV_RE.search(text, k)
        if not m:
            raise ValueError('div 未配对')
        depth += 1 if m.group(0) != '</div>' else -1
        k = m.end()
        if depth == 0:
            return k
    raise ValueError('div 未闭合')


def span_lang_zh(text):
    """返回 .lang-zh 整块的 (start, end)。"""
    i = text.find('class="lang-zh"')
    if i < 0:
        raise ValueError('找不到 class="lang-zh"')
    j = text.rfind('<div', 0, i)
    if j < 0:
        raise ValueError('找不到 lang-zh 的 <div> 起点')
    return j, match_div(text, j)


def inner_body_span(block):
    """在 .lang-zh 块内定位 <div class="article-body"> 的内层区间 (start, end)。"""
    m = re.search(r'<div class="article-body">', block)
    if not m:
        raise ValueError('块内无 <div class="article-body">')
    return m.end(), match_div(block, m.start()) - len('</div>')


def apply(page, check_only=False):
    html_path = os.path.join(ROOT, 'blog', f'{page}.html')
    block_path = os.path.join(BLOCKS, f'{page}.zh.html')
    if not os.path.exists(block_path):
        return page, 'SKIP（无中文稿）', None, None

    html = open(html_path, encoding='utf-8').read()
    new_inner = open(block_path, encoding='utf-8').read()

    b0, b1 = span_lang_zh(html)
    block = html[b0:b1]
    i0, i1 = inner_body_span(block)

    old_inner = block[i0:i1]
    if old_inner.strip() == new_inner.strip():
        return page, 'UNCHANGED', len(old_inner), len(new_inner)

    new_block = block[:i0] + new_inner + block[i1:]
    new_html = html[:b0] + new_block + html[b1:]

    # 结构自检（写入前）
    opens, closes = len(re.findall(r'<div\b', new_html)), new_html.count('</div>')
    if opens != closes:
        raise SystemExit(f'{page}: div 失衡 {opens}/{closes}，已中止')
    if new_html.count('<h1') != html.count('<h1'):
        raise SystemExit(f'{page}: h1 数变化，已中止')

    if not check_only:
        open(html_path, 'w', encoding='utf-8').write(new_html)
    return page, 'DRY' if check_only else 'OK', len(old_inner), len(new_inner)


def main():
    check_only = '--check' in sys.argv
    print(f"{'页面':26} {'状态':10} {'旧正文':>8} {'新正文':>8}")
    for page in PAGES:
        p, st, a, b = apply(page, check_only)
        fa = f'{a}' if a is not None else '—'
        fb = f'{b}' if b is not None else '—'
        print(f'{p:26} {st:10} {fa:>8} {fb:>8}')


if __name__ == '__main__':
    main()
