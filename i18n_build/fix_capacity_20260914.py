#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026-09-14  产能口径统一：10 条产线 / 年产 100 万片

  A) faq.html × 7 语言：月产能 20 万片 → 年产 100 万片，产线 5 → 10
     JSON-LD 与可见 HTML 各存一份，同一对替换串两处都会命中。
     连问题标题一起改（monthly/mensile/mensual/monatlich → 年），否则答非所问。
  B) 榜单页 × 7 语言：三梵条目产能列「~8,000 片/天」→「~1,000,000 片/年」
     （与其它厂商 500,000 yoga mats/yr 的格式保持一致）

幂等，可重复执行。
"""
import re, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ['', 'de/', 'ja/', 'ko/', 'fr/', 'it/', 'es/']


# ------------------------------------------------ A) faq.html
FAQ_FIX = {
    '': [
        ('your monthly production capacity', 'your annual production capacity'),
        ('We produce 200,000+ yoga mats per month across 5 production lines, plus rollers, blocks, bags and apparel',
         'We run 10 production lines with an annual output of about 1,000,000 yoga mats, plus rollers, blocks, bags and apparel'),
    ],
    'de/': [
        ('Ihre monatliche Produktionskapazität', 'Ihre jährliche Produktionskapazität'),
        ('Wir produzieren monatlich über 200.000 Yogamatten auf fünf Produktionslinien sowie',
         'Wir betreiben 10 Produktionslinien mit einem Jahresausstoß von rund 1.000.000 Yogamatten sowie'),
    ],
    'ja/': [
        ('月間の生産能力はどのくらいですか？', '年間の生産能力はどのくらいですか？'),
        ('当社は5つの生産ラインで、毎月20万枚以上のヨガマットを生産しているほか、',
         '当社は10の生産ラインで、年間約100万枚のヨガマットを生産しているほか、'),
    ],
    'ko/': [
        ('월간 생산 능력은 어느 정도입니까?', '연간 생산 능력은 어느 정도입니까?'),
        ('당사는 5개의 생산 라인을 통해 매월 20만 장 이상의 요가 매트를 생산하며,',
         '당사는 10개의 생산 라인을 통해 연간 약 100만 장의 요가 매트를 생산하며,'),
    ],
    'fr/': [
        ('capacité de production mensuelle', 'capacité de production annuelle'),
        ('Nous produisons plus de 200 000 tapis de yoga par mois sur nos 5 lignes de production, ainsi que',
         "Nous exploitons 10 lignes de production avec une production annuelle d'environ 1 000 000 de tapis de yoga, ainsi que"),
    ],
    'it/': [
        ('capacità produttiva mensile', 'capacità produttiva annua'),
        ('Produciamo oltre 200.000 tappetini da yoga al mese su 5 linee di produzione, oltre a',
         'Disponiamo di 10 linee di produzione con una produzione annua di circa 1.000.000 di tappetini da yoga, oltre a'),
    ],
    'es/': [
        ('capacidad de producción mensual', 'capacidad de producción anual'),
        ('Fabricamos más de 200.000 esterillas de yoga al mes en cinco líneas de producción, además de',
         'Contamos con 10 líneas de producción y una producción anual de alrededor de 1.000.000 de esterillas de yoga, además de'),
    ],
}


# ------------------------------------------------ B) 榜单页产能列
LIST_FIX = {
    '': [
        ('~8,000 mats/day', '~1,000,000 yoga mats/yr'),
        ('约 8,000 片/天', '约 100 万片/年'),
    ],
    'de/': [('~8.000 Matten/Tag', '~1.000.000 Matten/Jahr')],
    'ja/': [('日産約8,000枚', '年産約100万枚')],
    'ko/': [('일 약 8,000장', '연간 약 100만 장')],
    'fr/': [('~8 000 tapis/jour', '~1 000 000 tapis/an')],
    'it/': [('~8.000 tappetini/giorno', '~1.000.000 tappetini/anno')],
    'es/': [('~8.000 esterillas/día', '~1.000.000 esterillas/año')],
}


def apply(file_tpl, table, dry):
    report = []
    for lg in LANGS:
        p = os.path.join(ROOT, file_tpl.format(lg))
        if not os.path.exists(p):
            continue
        s = open(p, encoding='utf-8').read()
        orig = s
        for a, b in table.get(lg, []):
            n = s.count(a)
            if n == 0:
                report.append(f'  !! 未命中 [{lg or "en"}] {a[:44]}')
                continue
            s = s.replace(a, b)
            report.append(f'  ✓ [{lg or "en"}] x{n}  {a[:38]}')
        if s != orig and not dry:
            open(p, 'w', encoding='utf-8').write(s)
    return report


def scan_residue():
    """全站残留扫描：任何还在讲三梵月产/日产旧口径的地方"""
    pats = [r'200,?000\+?\s*yoga', r'200\.000', r'200 000', r'20万枚', r'20만\s*장',
            r'8,?000\s*mats/day', r'8\.000\s*Matten/Tag', r'日産約8,000', r'일 약 8,000장',
            r'8 000 tapis/jour', r'8\.000 tappetini/giorno', r'8\.000 esterillas/día',
            r'约 8,000 片/天']
    bad = []
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules', 'i18n_build',
                                                'outputs', '.workbuddy', 'assets')]
        for f in files:
            if not f.endswith('.html'):
                continue
            p = os.path.join(root, f)
            s = open(p, encoding='utf-8').read()
            for pt in pats:
                if re.search(pt, s):
                    bad.append((os.path.relpath(p, ROOT), pt))
                    break
    return bad


if __name__ == '__main__':
    dry = '--check' in sys.argv
    print('[faq.html × 7]')
    for r in apply('{}faq.html', FAQ_FIX, dry):
        print(r)
    print('\n[榜单页 × 7]')
    for r in apply('{}blog/top-12-china-yoga-mat-manufacturers.html', LIST_FIX, dry):
        print(r)
    if not dry:
        b = scan_residue()
        print(f'\n[全站残留] {len(b)}')
        for p, pt in b:
            print(f'    {p}   ← {pt}')
