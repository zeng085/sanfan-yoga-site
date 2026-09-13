#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026-09-14  三件收尾：
  1) 博客文章页 og:type: website -> article（榜单页 7 语言版已是 article，不动）
  2) private-label-yoga-mats 的 EN 块与 ZH 块各补一段 article-cta（该页此前唯一没有 CTA 的）
  3) vet-factory 产线口径 5 -> 10 条，并补年产 1,000,000 片（EN + ZH + 6 语言）

全部幂等，可重复执行。
"""
import re, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SLUGS = ['7day-sampling', 'compliance', 'custom-sizes', 'moq-explained',
         'private-label-yoga-mats', 'tpe-vs-pu', 'vet-factory',
         'yoga-mat-materials', 'yoga-mat-spec-guide']
LANGS = ['', 'de/', 'ja/', 'ko/', 'fr/', 'it/', 'es/']


# ---------------------------------------------------------------- 1) og:type
def fix_ogtype(dry=False):
    changed = []
    for lg in LANGS:
        for slug in SLUGS:
            p = os.path.join(ROOT, f'{lg}blog/{slug}.html')
            if not os.path.exists(p):
                continue
            s = open(p, encoding='utf-8').read()
            new, n = re.subn(r'(og:type"\s+content=")website(")', r'\1article\2', s)
            if n and new != s:
                if not dry:
                    open(p, 'w', encoding='utf-8').write(new)
                changed.append((f'{lg}blog/{slug}.html', n))
    # 校验
    bad = []
    for lg in ([] if dry else LANGS):
        for slug in SLUGS:
            p = os.path.join(ROOT, f'{lg}blog/{slug}.html')
            if not os.path.exists(p):
                continue
            s = open(p, encoding='utf-8').read()
            m = re.search(r'og:type"\s+content="([^"]*)"', s)
            if not m or m.group(1) != 'article':
                bad.append((f'{lg}blog/{slug}.html', m.group(1) if m else 'NONE'))
    return changed, bad


# ------------------------------------------------------- 2) private-label CTA
EN_CTA = ('          <p class="article-cta"><strong>Building your own line?</strong> '
          'Send your target quantity, material and artwork — we will quote the full private-label '
          'package (spec sheet, golden sample, test reports) and sample it in 7 days. '
          '<a href="../contact.html">Get a quote</a>.</p>\n')
ZH_CTA = ('          <p class="article-cta"><strong>要做自己的产品线？</strong>'
          '把目标数量、材质和图案文件发过来——我们按整套自有品牌方案报价'
          '（规格书、金样、检测报告一并提供），并在 7 天内出样。'
          '<a href="../contact.html">获取报价</a>。</p>\n')


def _body_end(seg):
    """返回 article-body 那个 div 的闭合 </div> 起始下标（面向其内层最后一个字符之后）"""
    m = re.search(r'<div class="article-body">', seg)
    if not m:
        return None
    k = m.end(); d = 1
    while k < len(seg):
        mm = re.compile(r'<div\b|</div>').search(seg, k)
        if not mm:
            return None
        d += 1 if mm.group(0) != '</div>' else -1
        k = mm.end()
        if d == 0:
            return k - 6          # 指向该 </div> 的 '<'
    return None


def _block_span(text, cls):
    """返回 (该 div 起始下标, 结束下标)"""
    i = text.find(f'class="{cls}"')
    if i < 0:
        return None
    j = text.rfind('<div', 0, i); d = 0; k = j
    while k < len(text):
        mm = re.compile(r'<div\b|</div>').search(text, k)
        if not mm:
            break
        d += 1 if mm.group(0) != '</div>' else -1
        k = mm.end()
        if d == 0:
            break
    return j, k


def fix_cta(dry=False):
    p = os.path.join(ROOT, 'blog/private-label-yoga-mats.html')
    s = open(p, encoding='utf-8').read()
    if 'article-cta' in s:
        return 'already-present', s
    out = s
    for cls, cta in (('lang-zh', ZH_CTA), ('lang-en', EN_CTA)):
        span = _block_span(out, cls)
        if not span:
            continue
        a, b = span
        seg = out[a:b]
        e = _body_end(seg)
        if e is None:
            continue
        seg2 = seg[:e] + cta + seg[e:]
        out = out[:a] + seg2 + out[b:]
        # 重算（长度变了，但下次 find 会重新定位）
    if not dry:
        open(p, 'w', encoding='utf-8').write(out)
    return 'done', out


# ------------------------------------------------- 3) vet-factory 产线口径
# 各语言「5 条产线」→「10 条产线 + 年产 100 万片」。
# 每条规则都取足够长的唯一串；年产插在段末句号前，避免误伤同页其它句子。
LINE_FIX = {
    '': [  # EN（外加同页中文块）
        ('with 5 production lines covering foaming, cutting, printing and packing under one roof.',
         'with 10 production lines covering foaming, cutting, printing and packing under one roof '
         '— about 1,000,000 mats a year.'),
        ('12,000 平方米的垂直整合厂区，5 条产线，发泡、裁切、印刷、包装都在同一个屋顶下完成。',
         '12,000 平方米的垂直整合厂区，10 条产线，发泡、裁切、印刷、包装都在同一个屋顶下完成，'
         '年产约 100 万片。'),
    ],
    'de/': [
        ('mit fünf Produktionslinien', 'mit zehn Produktionslinien'),
        ('und Verpacken unter einem Dach vereinen. Die Auditberichte',
         'und Verpacken unter einem Dach vereinen – rund 1.000.000 Matten pro Jahr. '
         'Die Auditberichte'),
    ],
    'fr/': [
        ('avec 5 lignes de production', 'avec 10 lignes de production'),
        ('d’emballage. Les rapports d’audit',
         'd’emballage — soit environ 1 000 000 de tapis par an. Les rapports d’audit'),
    ],
    'it/': [
        ('con 5 linee di produzione', 'con 10 linee di produzione'),
        ('e imballaggio sotto lo stesso tetto. Gli audit',
         'e imballaggio sotto lo stesso tetto – circa 1.000.000 di tappetini all’anno. Gli audit'),
    ],
    'es/': [
        ('con 5 líneas de producción', 'con 10 líneas de producción'),
        ('y embalaje bajo un mismo techo. Disponemos',
         'y embalaje bajo un mismo techo — alrededor de 1.000.000 de esterillas al año. Disponemos'),
    ],
    'ja/': [
        ('各工程をカバーする5つの生産ラインを1つの屋根の下に集約しています。',
         '各工程をカバーする10の生産ラインを1つの屋根の下に集約し、年間約100万枚を生産しています。'),
    ],
    'ko/': [
        ('포장을 아우르는 5개의 생산 라인을 갖추고 있습니다.',
         '포장을 아우르는 10개의 생산 라인을 갖추고 있으며, 연간 약 100만 장을 생산합니다.'),
    ],
}


def fix_lines(dry=False):
    report = []
    for lg in LANGS:
        p = os.path.join(ROOT, f'{lg}blog/vet-factory.html')
        if not os.path.exists(p):
            continue
        s = open(p, encoding='utf-8').read()
        orig = s
        for a, b in LINE_FIX.get(lg, []):
            if a not in s:
                report.append(f'  !! 未命中 [{lg or "en"}] {a[:40]}')
                continue
            s = s.replace(a, b)
        if s != orig:
            if not dry:
                open(p, 'w', encoding='utf-8').write(s)
            report.append(f'  ✓ {lg}blog/vet-factory.html')
    return report


def selfcheck():
    errs = []
    p = os.path.join(ROOT, 'blog/private-label-yoga-mats.html')
    s = open(p, encoding='utf-8').read()
    if s.count('article-cta') != 2:
        errs.append(f'private-label CTA 数 {s.count("article-cta")}（应为 2）')
    if len(re.findall(r'<div\b', s)) != s.count('</div>'):
        errs.append(f'private-label div 失衡 {len(re.findall(r"<div\b", s))}/{s.count("</div>")}')
    if s.count('<h1') != 2:
        errs.append(f'private-label h1={s.count("<h1")}（应为 2）')
    # 全站产线残留
    for lg in LANGS:
        pp = os.path.join(ROOT, f'{lg}blog/vet-factory.html')
        if not os.path.exists(pp):
            continue
        t = open(pp, encoding='utf-8').read()
        if re.search(r'5 production lines|5 Produktionslinien|5 本の生産ライン|5 条产线|'
                     r'5 lignes de production|5 linee di produzione|5 líneas de producción|'
                     r'5개의 생산라인|5 개의 생산라인', t):
            errs.append(f'{pp} 仍有 5 条产线残留')
    return errs


if __name__ == '__main__':
    dry = '--check' in sys.argv
    ch, bad = fix_ogtype(dry)
    print(f'[og:type] 改动 {len(ch)} 个文件' + ('（dry-run）' if dry else ''))
    for f, n in ch[:5]:
        print(f'    {f}  x{n}')
    print(f'[og:type] 校验：非 article 残留 {len(bad)}')
    for f, v in bad:
        print(f'    ✗ {f} = {v}')

    st, _ = fix_cta(dry)
    print(f'[CTA] private-label: {st}')

    rep = fix_lines(dry)
    print('[产线]')
    for r in rep:
        print('    ' + r)

    if not dry:
        e = selfcheck()
        print('\n[自检]', '全过 ✅' if not e else '')
        for x in e:
            print('    ✗', x)
