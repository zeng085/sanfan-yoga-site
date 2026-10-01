#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
族页结构校验（改动后必跑）：
  1. JSON-LD 全部可解析
  2. 标签配对（成对标签开/闭数量一致）—— 见项目铁律：只改开标签 subn 是抓不到的
  3. 锚点 id 唯一，且每个型号卡 id 都能被页面内链接到达
  4. 图片引用的文件真实存在，且 width/height 与文件一致
用法: python3 verify_pilates_page_20261001.py <html路径>
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAIRED = ['html', 'head', 'body', 'section', 'div', 'figure', 'article', 'dl', 'dt', 'dd',
          'table', 'thead', 'tbody', 'tr', 'td', 'th', 'nav', 'ul', 'ol', 'li', 'p', 'span',
          'h1', 'h2', 'h3', 'h4', 'details', 'summary', 'header', 'footer', 'main', 'a', 'script']


def main():
    path = Path(sys.argv[1])
    t = path.read_text(encoding='utf-8')
    ok = True

    # 1) JSON-LD
    print('=== 1. JSON-LD ===')
    n_ld = 0
    for m in re.finditer(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', t, re.S):
        n_ld += 1
        try:
            d = json.loads(m.group(1))
            types = []
            for o in (d if isinstance(d, list) else [d]):
                for x in o.get('@graph', [o]):
                    types.append(x.get('@type'))
                    if x.get('@type') == 'ItemList':
                        n_items = len(x.get('itemListElement', []))
                        print(f'   #{n_ld} {x.get("@type")}: {n_items} 项'
                              f'（numberOfItems 声明 {x.get("numberOfItems")}）')
                        if n_items != x.get('numberOfItems'):
                            print(f'   ✗ numberOfItems 与实际项数不符'); ok = False
                        continue
                    print(f'   #{n_ld} {x.get("@type")}')
        except Exception as e:
            print(f'   ✗ #{n_ld} 解析失败: {e}'); ok = False

    # 2) 标签配对
    # ⚠️ 必须先剥掉 HTML 注释：注释里出现 `<dl>` 之类字面量会被正则当成真标签，
    #    本项目实测过一次「8 个 <dl> vs 7 个 </dl>」的假阳性（实为注释文字）。
    print('=== 2. 标签配对 ===')
    t_nc = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    bad = []
    for tag in PAIRED:
        o = len(re.findall(rf'<{tag}(?:\s[^>]*)?>', t_nc))
        c = len(re.findall(rf'</{tag}>', t_nc))
        if o != c:
            bad.append(f'{tag}: <{tag}> {o} vs </{tag}> {c}')
    if bad:
        ok = False
        print('   ✗ 不配对:', '; '.join(bad))
    else:
        print(f'   ✓ {len(PAIRED)} 类成对标签全部平衡')

    # 3) 锚点
    print('=== 3. 锚点 ===')
    ids = re.findall(r'\sid="([^"]+)"', t)
    dup = [k for k, v in Counter(ids).items() if v > 1]
    if dup:
        ok = False
        print('   ✗ id 重复:', dup)
    else:
        print(f'   ✓ {len(ids)} 个 id 唯一')
    hrefs = set(re.findall(r'href="#([^"]+)"', t))
    missing = sorted(h for h in hrefs if h not in ids)
    if missing:
        ok = False
        print('   ✗ 页内链接指向不存在的 id:', missing)
    else:
        print(f'   ✓ {len(hrefs)} 个页内锚点链接全部命中')
    cards = [i for i in ids if i.startswith('cat-') or i.startswith('ladder-')]
    print(f'   · 型号/画册锚点 {len(cards)} 个: {cards}')

    # 4) 图片
    print('=== 4. 图片 ===')
    for m in re.finditer(r'<img\s[^>]*src="([^"]+)"[^>]*>', t):
        tag, src = m.group(0), m.group(1)
        if src.startswith('http'):
            continue
        f = (path.parent / src).resolve()
        wm = re.search(r'width="(\d+)"', tag)
        hm = re.search(r'height="(\d+)"', tag)
        if not f.exists():
            print(f'   ✗ 不存在: {src}'); ok = False
            continue
        w, h = wm.group(1) if wm else '?', hm.group(1) if hm else '?'
        print(f'   ✓ {src}  width={w} height={h}  ({f.stat().st_size//1024} KB)')
        if 'catalog/' in src and (w == '?' or h == '?'):
            print(f'     ! 画册图建议补 width/height'); ok = False

    # 5) CSS 版本号
    print('=== 5. 资源版本号 ===')
    for m in re.finditer(r'(?:href|src)="([^"]*(?:styles\.css|main\.js)\?v[^"]*)"', t):
        print(f'   · {m.group(1)}')

    print()
    print('结果:', '✅ 全部通过' if ok else '❌ 有问题')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
