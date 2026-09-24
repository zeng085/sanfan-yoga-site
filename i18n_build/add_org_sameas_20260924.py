#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
让同一条实体身份（Organization + @id + sameAs）覆盖**全站**，而不只是那 98 页。

背景（2026-09-24 实测）：
  ✓ 首页/关于/材料/博客等 98 页有 Organization 节点 —— 但**都没有 @id**，
    没有 @id 就无法被别的页引用、多页之间的同一实体也难被合并
  ✗ 1029 个产品页 + 63 个 pilates 页**完全没有 Organization 节点**
    → sameAs 覆盖不到商业价值最高的那批页

做法（两步，都幂等）：
  1) 已有 Organization 的页：补 `@id = https://fjsanfan.com/#organization`
     （author/publisher 指向同一实体，同 @id 才会被合并；顺带把缩写名归一为全称）
  2) 没有 Organization 的页：在最后一个 ld+json 块后追加实体节点
     （带 @id/@context/name/url/logo/address/email/sameAs，模板取自 index.html，不手写副本）

用法:
    python3 i18n_build/add_org_sameas_20260924.py            # 试跑
    python3 i18n_build/add_org_sameas_20260924.py --apply    # 写入
    python3 i18n_build/add_org_sameas_20260924.py --check    # 只体检（不写）
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from sameas_guard import ORG_ID, ORG_NAME, load_sameas  # noqa: E402

APPLY = '--apply' in sys.argv
CHECK = '--check' in sys.argv
LIMIT = 0
for _i, _a in enumerate(sys.argv):
    if _a == '--limit' and _i + 1 < len(sys.argv):
        LIMIT = int(sys.argv[_i + 1])

SKIP_DIRS = {'.git', 'i18n_build', 'outputs', '.workbuddy', 'node_modules'}
SKIP_FILES = {'product.html'}          # JS 模板页（noindex，不是真实内容页）
LDS = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
MARK_A, MARK_B = '<!-- orgref:v1 -->', '<!-- /orgref:v1 -->'
# 摘块必须与追加的空白**严格互逆**，否则重跑会漂移（本项目踩过这个坑）
STRIP = re.compile(r'\n?[ \t]*' + re.escape(MARK_A) + r'.*?' + re.escape(MARK_B) + r'\n?', re.S)

NAME_ALIASES = {'fujian sanfan', 'fujian sanfan sports products',
                'fujian sanfan sports products industry co., ltd.'}

SAMEAS = load_sameas()
_ORG_CACHE = {}


def base_org():
    """实体身份的唯一模板。

    ⚠️ 不要手写副本。取「参考页里字段最全的那个 Organization 节点」——
    实测 `about.html` 的节点最全（15 个字段，已带 @id /
    alternateName / foundingDate / numberOfEmployees / contactPoint /
    knowsAbout / areaServed），首页那个是精简版（无 @id）。
    两处各写一份必然漂移，所以按字段数自动选。
    """
    if 'v' in _ORG_CACHE:
        return _ORG_CACHE['v']
    best = None
    for ref in ('about.html', 'index.html'):
        p = os.path.join(ROOT, ref)
        if not os.path.exists(p):
            continue
        for b in LDS.findall(open(p, encoding='utf-8').read()):
            try:
                d = json.loads(b)
            except Exception:
                continue
            node = find_org(d)
            if not node or not (node.get('name') or '').startswith('FUJIAN SANFAN'):
                continue
            if best is None or len(node) > len(best):
                best = dict(node)
    if best is None:
        raise SystemExit('⛔ 无法提取 Organization 模板 —— 检查 about.html / index.html')
    best.pop('sameAs', None)          # sameAs 一律来自 sameas.json（过黑名单闸）
    _ORG_CACHE['v'] = best
    return best


def find_org(node):
    """深度优先找第一个 Organization 节点，返回引用（可原地改）"""
    if isinstance(node, dict):
        if node.get('@type') == 'Organization':
            return node
        for v in node.values():
            r = find_org(v)
            if r is not None:
                return r
    elif isinstance(node, list):
        for v in node:
            r = find_org(v)
            if r is not None:
                return r
    return None


def find_all_orgs(node, out):
    if isinstance(node, dict):
        if node.get('@type') == 'Organization':
            out.append(node)
        for v in node.values():
            find_all_orgs(v, out)
    elif isinstance(node, list):
        for v in node:
            find_all_orgs(v, out)


def rendered_block():
    org = {'@context': 'https://schema.org', '@type': 'Organization'}
    org.update(base_org())
    org['@id'] = ORG_ID
    org['sameAs'] = list(SAMEAS)
    body = json.dumps(org, ensure_ascii=False, indent=2)
    body = '\n'.join('  ' + ln for ln in body.splitlines())
    return f'{MARK_A}\n  <script type="application/ld+json">\n{body}\n  </script>\n  {MARK_B}\n'


def jsonlD_has_org(src):
    for b in LDS.findall(src):
        if '"Organization"' in b:
            return True
    return False


def patch_orgs(src):
    """给已有 Organization 补 @id / sameAs / 归一名称。返回 (新文本, 改动节点数)"""
    n = 0

    def repl(m):
        nonlocal n
        body = m.group(1).strip()
        if '"Organization"' not in body:
            return m.group(0)
        try:
            data = json.loads(body)
        except Exception:
            return m.group(0)
        orgs = []
        find_all_orgs(data, orgs)
        if not orgs:
            return m.group(0)
        changed = False
        for o in orgs:
            if '@id' not in o:
                o['@id'] = ORG_ID
                changed = True
            if 'sameAs' not in o:
                o['sameAs'] = list(SAMEAS)
                changed = True
            nm = (o.get('name') or '').strip()
            if nm.lower() in NAME_ALIASES and nm != ORG_NAME:
                o['name'] = ORG_NAME
                changed = True
        if not changed:
            return m.group(0)
        n += 1
        new = json.dumps(data, ensure_ascii=False, indent=2)
        lead = m.group(0)[:len(m.group(0)) - len(m.group(0).lstrip())]
        if not lead:
            new = '\n' + '\n'.join('  ' + ln for ln in new.splitlines()) + '\n  '
        return '<script type="application/ld+json">' + new + '</script>'

    return LDS.sub(repl, src), n


def process(path):
    """返回 (处理方式, 是否真的会有改动)"""
    orig = open(path, encoding='utf-8').read()
    src = STRIP.sub('', orig) if MARK_A in orig else orig

    if jsonlD_has_org(src):
        out, n = patch_orgs(src)
        mode = '补 @id/sameAs' if n else '已完整(不改)'
    else:
        blocks = list(LDS.finditer(src))
        if not blocks:
            mode = '跳过(无 JSON-LD)'
            out = src
        else:
            tail = blocks[-1].end()
            out = src[:tail] + '\n' + rendered_block() + src[tail:]
            mode = '追加实体节点'

    return mode, out != orig, out


def collect():
    files = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith('.html') and fn not in SKIP_FILES:
                files.append(os.path.join(dirpath, fn))
    return sorted(files)


def audit(files):
    no_org, no_id, no_sameas, parse_fail = [], [], [], []
    for f in files:
        src = open(f, encoding='utf-8').read()
        orgs = []
        for b in LDS.findall(src):
            try:
                d = json.loads(b)
            except Exception:
                parse_fail.append(f)
                continue
            find_all_orgs(d, orgs)
        if not orgs:
            no_org.append(f)
            continue
        if not any(o.get('@id') for o in orgs):
            no_id.append(f)
        if not any(o.get('sameAs') for o in orgs):
            no_sameas.append(f)
    return no_org, no_id, no_sameas, parse_fail


def rel(paths, n=6):
    if not paths:
        return ''
    return ', '.join(os.path.relpath(p, ROOT) for p in paths[:n]) + (' …' if len(paths) > n else '')


def main():
    files = collect()
    print(f'扫描 {len(files)} 个 HTML（排除 {", ".join(sorted(SKIP_FILES))} 与构建目录）')
    print(f'sameAs: {SAMEAS}\n@id   : {ORG_ID}\n')

    if CHECK:
        no_org, no_id, no_sameas, parse_fail = audit(files)
        print(f'JSON-LD 解析失败      : {len(parse_fail)}  {rel(parse_fail)}')
        print(f'无 Organization 节点  : {len(no_org)}  {rel(no_org)}')
        print(f'有 Org 但缺 @id       : {len(no_id)}  {rel(no_id)}')
        print(f'有 Org 但缺 sameAs    : {len(no_sameas)}  {rel(no_sameas)}')
        bad = len(no_org) + len(no_id) + len(no_sameas) + len(parse_fail)
        print('\n结论:', '✅ 全站实体声明完整' if bad == 0 else f'❌ 仍有 {bad} 页待处理')
        return

    stats, samples = {}, {}
    todo = files[:LIMIT] if LIMIT else files
    for f in todo:
        mode, changed, out = process(f)
        if changed:
            stats[mode] = stats.get(mode, 0) + 1
            samples.setdefault(mode, []).append(f)
            if APPLY:
                open(f, 'w', encoding='utf-8').write(out)

    print('改动统计:')
    for k in sorted(stats):
        print(f'  {k:16s} {stats[k]:5d}  {rel(samples[k], 4)}')
    print(f'  {"合计":16s} {sum(stats.values()):5d}')
    print('\n模式:', '已写入' if APPLY else '试跑（加 --apply 才写入）',
          f'| 限定前 {LIMIT} 个文件' if LIMIT else '')


if __name__ == '__main__':
    main()
