#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
给全站 Product 节点补 `manufacturer` —— 明确指出"这东西是我们自己生产的"。

背景（2026-09-24 实测）：
  Product 节点有 `brand: {name: "SANFAN"}`，但 **manufacturer 全站为 null**。
  上一轮已把 Organization + @id 铺到 1330 页，所以现在只差"把产品挂到实体上"这一步。

为什么值得做：
  "谁生产的 / SANFAN 瑜伽垫哪家厂 / OEM factory for X" 这类采购查询，
  答案就是 manufacture 关系。brand 只说明"叫什么牌子"，
  manufacturer 才说明"谁做的"——AI 抽取"工厂↔产品"关系靠的是后者。

做法：
  1) 只在**含 Product 节点**的 ld+json 块里动手（别的块一个字不碰）
  2) 插入位置：该 Product 节点的 `brand` 对象之后（没有 brand 则跟在 @type 之后），
     用括号配平扫描定位，不对整块做 JSON 重新序列化 → 每页 diff 恰好 +7 行
  3) 幂等：块内已出现 `"manufacturer"` 即跳过

用法:
    python3 i18n_build/add_product_manufacturer_20260924.py            # 试跑
    python3 i18n_build/add_product_manufacturer_20260924.py --apply    # 写入
    python3 i18n_build/add_product_manufacturer_20260924.py --check    # 只体检
    ... --limit 8                                                      # 只处理前 8 个文件
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from sameas_guard import ORG_ID, ORG_NAME  # noqa: E402

APPLY = '--apply' in sys.argv
CHECK = '--check' in sys.argv
LIMIT = 0
for _i, _a in enumerate(sys.argv):
    if _a == '--limit' and _i + 1 < len(sys.argv):
        LIMIT = int(sys.argv[_i + 1])

SKIP_DIRS = {'.git', 'i18n_build', 'outputs', '.workbuddy', 'node_modules'}
SKIP_FILES = {'product.html'}          # JS 模板页
LDS = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
PRODUCT_RE = re.compile(r'"@type"\s*:\s*"Product"')
BRAND_RE = re.compile(r'"brand"\s*:\s*')

# 自描述 + 可引用：既给 @id（处理器合并实体时用），也自带 name/url
# （万一处理器不跨块合并，节点本身仍然完整可读）
MANUFACTURER = {
    '@type': 'Organization',
    '@id': ORG_ID,
    'name': ORG_NAME,
    'alternateName': 'SANFAN',
    'url': 'https://fjsanfan.com/',
}


def value_end(text, key_re, start=0):
    """找到 `"key":` 后面那个 {…}/[…] 值对象的结束位置（返回其后的下标）。

    用括号配平 + 字符串状态机，不依赖缩进/空白的具体写法。
    """
    m = key_re.search(text, start)
    if not m:
        return None
    i = m.end()
    if i >= len(text) or text[i] not in '{[':
        return None
    depth, in_str, esc = 0, False, False
    while i < len(text):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c in '{[':
                depth += 1
            elif c in '}]':
                depth -= 1
                if depth == 0:
                    return i + 1
        i += 1
    return None


def render_value(indent):
    """按目标缩进渲染 `"manufacturer": {…}`（不含前置逗号）"""
    lines = json.dumps(MANUFACTURER, ensure_ascii=False, indent=2).splitlines()
    # json.dumps 自己已带相对缩进，这里只需补「目标层级」的前缀，别再加一级
    body = '\n'.join(indent + ln for ln in lines[1:-1])
    return '"manufacturer": {\n' + body + '\n' + indent + '}'


def indent_of(text, pos):
    """pos 所在行的前导空白"""
    ls = text.rfind('\n', 0, pos) + 1
    seg = text[ls:pos]
    return seg[:len(seg) - len(seg.lstrip())] if seg.strip() == '' else ' ' * 6


def patch_block(body):
    """在单个 ld+json 块内给 Product 节点补 manufacturer。

    返回 (新块文本, 改动数)。已含 manufacturer 直接原样返回。
    """
    pm = PRODUCT_RE.search(body)
    if not pm:
        return body, 0
    if '"manufacturer"' in body[pm.start():]:
        return body, 0

    # 优先挂在 brand 之后；brand 缺失则挂在 @type 之后
    after = value_end(body, BRAND_RE, pm.start())
    if after is not None:
        anchor = after
        ind = indent_of(body, BRAND_RE.search(body, pm.start()).start())
    else:
        anchor = pm.end()
        ind = indent_of(body, pm.start())

    ins = ',\n' + ind + render_value(ind)
    return body[:anchor] + ins + body[anchor:], 1


def process(path):
    orig = open(path, encoding='utf-8').read()
    hits = [0]

    def repl(m):
        new, n = patch_block(m.group(1))
        hits[0] += n
        return '<script type="application/ld+json">' + new + '</script>' if n else m.group(0)

    out = LDS.sub(repl, orig)
    return hits[0], out != orig, out


def collect():
    files = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith('.html') and fn not in SKIP_FILES:
                files.append(os.path.join(dirpath, fn))
    return sorted(files)


def products(node, out):
    """递归收集所有 Product 节点（返回引用）"""
    if isinstance(node, dict):
        if node.get('@type') == 'Product':
            out.append(node)
        for v in node.values():
            products(v, out)
    elif isinstance(node, list):
        for v in node:
            products(v, out)


def audit(files):
    """体检：有 Product 的页 / 其中缺 manufacturer 的页 / JSON 解析失败"""
    with_p, missing, parse_fail = [], [], []
    for f in files:
        src = open(f, encoding='utf-8').read()
        found, bad = False, False
        for b in LDS.findall(src):
            try:
                d = json.loads(b)
            except Exception:
                parse_fail.append(f)
                continue
            ps = []
            products(d, ps)
            for p in ps:
                found = True
                mf = p.get('manufacturer')
                if not (isinstance(mf, dict) and mf.get('@id') == ORG_ID):
                    bad = True
        if found:
            with_p.append(f)
            if bad:
                missing.append(f)
    return with_p, missing, parse_fail


def rel(paths, n=5):
    if not paths:
        return ''
    return ', '.join(os.path.relpath(p, ROOT) for p in paths[:n]) + (' …' if len(paths) > n else '')


def main():
    files = collect()
    print(f'扫描 {len(files)} 个 HTML（排除 {", ".join(sorted(SKIP_FILES))} 与构建目录）')
    print(f'manufacturer -> @id: {ORG_ID}\n')

    if CHECK:
        with_p, missing, parse_fail = audit(files)
        print(f'含 Product 节点的页        : {len(with_p)}')
        print(f'  └─ 其中缺 manufacturer   : {len(missing)}  {rel(missing)}')
        print(f'JSON-LD 解析失败           : {len(parse_fail)}  {rel(parse_fail)}')
        bad = len(missing) + len(parse_fail)
        print('\n结论:', '✅ 全站 Product 均已声明制造方' if bad == 0 else f'❌ 仍有 {bad} 处待处理')
        return

    todo = files[:LIMIT] if LIMIT else files
    changed, touched, nodes, samples = 0, [], 0, []
    for f in todo:
        n, ch, out = process(f)
        if ch:
            changed += 1
            nodes += n
            if len(samples) < 4:
                samples.append(f)
            if APPLY:
                open(f, 'w', encoding='utf-8').write(out)

    print(f'含 Product 且被补 manufacturer 的页: {changed}   (Product 节点数 {nodes})')
    if samples:
        print('  例:', rel(samples, 4))
    print('\n模式:', '已写入' if APPLY else '试跑（加 --apply 才写入）',
          f'| 限定前 {LIMIT} 个文件' if LIMIT else '')


if __name__ == '__main__':
    main()
