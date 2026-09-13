#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中英语言块「内容对等性」检查 —— 补上结构类检查查不出的那一层。

背景：blog 文章页用块级 <div class="lang-en"> + <div class="lang-zh">。
结构检查（成对/白页/div 配平/容器归属）全过，但中文块可能只是 400 字摘要
（2026-09-13 发现：a038d76 重写英文时把完整中文版覆盖成 3 段摘要）。

标定：站内 1237 组行内人工忠实配对（products 的 span.lang-en/lang-zh）实测
中/英字符比 中位 0.353、四分位 0.30–0.44 —— 中文天然比英文密，忠实译文
本来就该是英文的 1/3 左右。故阈值不能按 1.0 设。

用法：
  python3 i18n_build/check_zh_parity.py            # 全站扫
  python3 i18n_build/check_zh_parity.py blog/xxx.html  # 指定页
退出码：0 = 全过；1 = 有 FAIL
"""
import os
import re
import sys
import html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 中/英字符比阈值（标定：忠实配对中位 0.353）
RATIO_FAIL = 0.25      # 低于此值 = 残块
RATIO_WARN = 0.30      # 低于此值 = 偏薄
SKIP_DIRS = {'.git', 'node_modules', 'i18n_build', 'outputs', '.workbuddy', 'assets', '__pycache__'}


def block(text, cls):
    """从 class="<cls>" 所在 div 起做 <div> 配对，返回整段 HTML。"""
    i = text.find('class="%s"' % cls)
    if i < 0:
        return None
    j = text.rfind('<div', 0, i)
    if j < 0:
        return None
    depth, k = 0, j
    while k < len(text):
        m = re.compile(r'<div\b|</div>').search(text, k)
        if not m:
            break
        depth += 1 if m.group(0) != '</div>' else -1
        k = m.end()
        if depth == 0:
            break
    return text[j:k]


def plain(seg):
    if not seg:
        return ''
    t = re.sub(r'<script.*?</script>', '', seg, flags=re.S)
    t = re.sub(r'<style.*?</style>', '', t, flags=re.S)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', t))).strip()


def body_of(seg):
    """只取 .article-body 内部（排除 lead/封面/CTA 干扰），拿不到就退回整段。"""
    m = re.search(r'<div class="article-body">(.*?)(?=<p class="article-cta"|</div>\s*</div>\s*$)', seg, flags=re.S)
    return m.group(1) if m else seg


def stats(seg):
    """返回 (正文字符数, h2 数, h3 数, 表格单元格数, li 数)"""
    if not seg:
        return (0, 0, 0, 0, 0)
    b = body_of(seg)
    return (
        len(plain(b)),
        len(re.findall(r'<h2\b', b)),
        len(re.findall(r'<h3\b', b)),
        b.count('<th') + b.count('<td'),
        len(re.findall(r'<li\b', b)),
    )


def main():
    targets = sys.argv[1:]
    if not targets:
        targets = []
        for root, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for f in sorted(files):
                if f.endswith('.html'):
                    targets.append(os.path.join(root, f))
    else:
        targets = [t if os.path.isabs(t) else os.path.join(ROOT, t) for t in targets]

    fails, warns, rows = [], [], []
    for p in sorted(targets):
        try:
            s = open(p, encoding='utf-8').read()
        except Exception:
            continue
        # 只查「块级」双语页：行内 span 配对是天然同步的，不用查
        if '<div class="lang-en">' not in s or '<div class="lang-zh">' not in s:
            continue
        en, zh = block(s, 'lang-en'), block(s, 'lang-zh')
        se, sz = stats(en), stats(zh)
        if se[0] == 0:
            continue
        ratio = sz[0] / se[0]
        rel = os.path.relpath(p, ROOT)
        struct_ok = (se[1] == sz[1] and se[2] == sz[2] and se[3] == sz[3])
        rows.append((rel, se, sz, ratio, struct_ok))
        if ratio < RATIO_FAIL:
            fails.append(rel)
        elif ratio < RATIO_WARN:
            warns.append(rel)

    if not rows:
        print('没有块级双语页（<div class="lang-en"> + <div class="lang-zh">）')
        return 0

    print('%-46s %8s %8s %6s  %-18s %s' % ('页面', 'EN正文', 'ZH正文', '比', '结构(h2/h3/单元格)', '判定'))
    print('-' * 106)
    for rel, se, sz, ratio, struct_ok in rows:
        if ratio < RATIO_FAIL:
            verdict = 'FAIL 残块'
        elif ratio < RATIO_WARN:
            verdict = 'WARN 偏薄'
        elif not struct_ok:
            verdict = 'FAIL 结构不对等'
        else:
            verdict = 'OK'
        print('%-46s %8d %8d %6.2f  %-18s %s' % (
            rel[:46], se[0], sz[0], ratio,
            '%d/%d/%d vs %d/%d/%d' % (se[1], se[2], se[3], sz[1], sz[2], sz[3]),
            verdict))

    print()
    print('阈值：比 <%.2f = 残块(FAIL)；<%.2f = 偏薄(WARN)；结构 h2/h3/表格单元格 必须相等' % (RATIO_FAIL, RATIO_WARN))
    print('标定依据：站内 1237 组人工忠实配对实测中/英字符比 中位 0.353（四分位 0.30–0.44）')
    print('结论：%d 页 FAIL，%d 页 WARN，共 %d 个块级双语页' % (len(fails), len(warns), len(rows)))
    if fails:
        print('\nFAIL 明细：')
        for f in fails:
            print('  -', f)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
