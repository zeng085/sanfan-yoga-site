#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-01 规格对比表默认折叠 + reformer 画册展开改缩略图墙（HTML 侧）
- 6 个族页：models-compared 区的 .pl-spec-wrap 加 cat-fold-body/#spec-all，其前插入控制条
- reformer：既有画册控制条补 data-fold="cat-all" data-fold-grid
- 渐进增强：HTML 默认完整可见，折叠由 main.js 施加 → 无 JS/爬虫读原文，SEO/GEO 零影响
用法：--dry-run 打印差异统计；--apply 落盘（备份到 ~/.workbuddy/backups/fjsanfan/）
"""
import re, sys, shutil, pathlib

ROOT = pathlib.Path('/Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16')
PAGES = ['pilates-reformer', 'pilates-reformer-tower', 'pilates-wunda-chair',
         'pilates-ladder-barrel', 'pilates-cadillac', 'pilates-specialty']
BACKUP = pathlib.Path.home() / '.workbuddy/backups/fjsanfan/spec_fold_20261001'

OLD_BAR = '<div class="cat-fold-bar" hidden>'
NEW_BAR = '<div class="cat-fold-bar" data-fold="cat-all" data-fold-grid hidden>'
WRAP_OLD = '      <div class="pl-spec-wrap">'
WRAP_NEW = '      <div class="pl-spec-wrap cat-fold-body" id="spec-all">'


def bar_html(n: str) -> str:
    return (
        '      <div class="cat-fold-bar" data-fold="spec-all" hidden>\n'
        '        <button type="button" class="btn btn-primary cat-fold-toggle" aria-expanded="false" aria-controls="spec-all">\n'
        f'          <span class="lang-en">Show the full spec table \u2014 {n} models</span>'
        f'<span class="lang-zh">\u5c55\u5f00\u89c4\u683c\u5bf9\u6bd4\u8868 \u2014\u2014 {n} \u4e2a\u578b\u53f7</span>\n'
        '        </button>\n'
        '      </div>\n'
    )


def transform(src: str, name: str) -> str:
    if 'data-fold="spec-all"' in src:
        raise SystemExit(f'{name}: 已应用过（守卫命中），如需重做请先回滚')
    out = src
    if name == 'pilates-reformer':
        assert out.count(OLD_BAR) == 1, f'{name}: 画册控制条定位失败'
        out = out.replace(OLD_BAR, NEW_BAR)

    m = re.search(r'(\d+) models, compared', out)
    assert m, f'{name}: 未找到 "N models, compared"'
    n = m.group(1)
    assert f'{n} 个型号对比' in out, f'{name}: 中文 h2 型号数与英文不匹配'

    assert out.count(WRAP_OLD) == 1, f'{name}: pl-spec-wrap 应恰 1 处，实得 {out.count(WRAP_OLD)}'
    out = out.replace(WRAP_OLD, bar_html(n) + WRAP_NEW)

    # 标签配平自检（铁律：改 HTML 标签必须成对）
    for tag in ('div', 'button', 'span'):
        a, b = len(re.findall(rf'<{tag}\b', out)), out.count(f'</{tag}>')
        assert a == b, f'{name}: <{tag}> 配平失败 {a} vs {b}'
    # id 不冲突
    assert out.count('id="spec-all"') == 1, f'{name}: spec-all 应恰 1 处'
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else '--dry-run'
    for name in PAGES:
        p = ROOT / 'pilates' / f'{name}.html'
        src = p.read_text(encoding='utf-8')
        out = transform(src, name)
        added = out.count('\n') - src.count('\n')
        print(f'{name}: +{added} 行（含控制条 5 行 × 1 + wrap 改写）')
        if mode == '--apply':
            BACKUP.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, BACKUP / p.name)
            p.write_text(out, encoding='utf-8')
            print(f'  -> 已落盘，备份 {BACKUP / p.name}')
    if mode != '--apply':
        print('（dry-run，未落盘；确认后加 --apply）')


if __name__ == '__main__':
    main()
