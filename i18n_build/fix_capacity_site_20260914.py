#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026-09-14  全站产能口径统一：10 条产线 / 年产 1,000,000 片

背景：站内关于三梵自己的产能有多个互相打架的版本
    index.html                 5 条产线 / 200,000 pcs per month
    about.html                12 条产线 / 7,000–8,000 片每天（约 200,000/月）
    gyms-fitness-clubs.html   12 条产线 / 200,000 mats per month
    faq.html / vet-factory     5 条产线 / 200,000+ per month（上一脚本已改）
用户确认的真实口径：**10 条产线，年产 1,000,000 片**。本脚本把 index / about / gyms
（各 7 语言）统一到该口径。

设计要点：
  * 品类产能表只改「瑜伽垫」一行 + 表头（表头去掉「月」改中性「产能」，
    因为其余品类仍是月产口径，混在同一张表里需要中性表头）。
  * 产线数字在 <div class="num"> 里独立成节点，用 lab 文本锚定后替换，
    同一正则同时覆盖 index 的 5 与 about 的 12。
  * 幂等；未命中的规则会单独列出，便于补齐。
"""
import re, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ['', 'de/', 'ja/', 'ko/', 'fr/', 'it/', 'es/']
PAGES = ['index.html', 'about.html', 'applications/gyms-fitness-clubs.html']

# 产线 lab 的各语言写法（用于锚定 <div class="num">N</div>）
LAB = (r'Production Lines|Produktionslinien|produktionslinien|生産ライン|생산 라인|'
       r'lignes de production|linee di produzione|líneas de producción|产线')

RULES = {
    '': [  # EN（含同页中文块）
        # —— 表头 / 瑜伽垫行（index + about 同文）
        ('Monthly Production Capacity', 'Production Capacity'),
        ('Yoga Mats</td><td class="val" data-i18n="cap1.d">200,000 pcs / month',
         'Yoga Mats</td><td class="val" data-i18n="cap1.d">1,000,000 pcs / year'),
        # —— index hero / 统计条
        ('monthly capacity of 200,000+ yoga mats', 'annual capacity of 1,000,000+ yoga mats'),
        ('200K+ Mats / Month', '1M+ Mats / Year'),
        # —— about 正文 / og:description
        ('3 owned plants, 6 foaming machines and 12 production lines',
         '3 owned plants, 6 foaming machines and 10 production lines'),
        ('we hold a steady output of 7,000–8,000 mats per day (about 200,000 per month)',
         'we hold a steady annual output of about 1,000,000 mats'),
        # —— gyms
        ('we run 12 production lines with 200,000 mats/month capacity',
         'we run 10 production lines with 1,000,000 mats/year capacity'),
        ('我们有 12 条产线、月产 20 万张垫的产能',
         '我们有 10 条产线、年产 100 万张垫的产能'),
    ],
    'de/': [
        ('Monatliche Produktionskapazität', 'Produktionskapazität'),
        ('<td>Yogamatten</td><td class="val">200.000 Stück pro Monat',
         '<td>Yogamatten</td><td class="val">1.000.000 Stück pro Jahr'),
        ('eine monatliche Produktionskapazität von über 200.000 Yogamatten',
         'eine jährliche Produktionskapazität von über 1.000.000 Yogamatten'),
        ('200.000+ Matten / Monat', '1.000.000+ Matten / Jahr'),
        ('3 eigene Werke, 6 Schäummaschinen, 12 Produktionslinien, 7.000–8.000 Matten/Tag.',
         '3 eigene Werke, 6 Schäummaschinen, 10 Produktionslinien, etwa 1.000.000 Matten/Jahr.'),
        ('6 Schäummaschinen und 12 Produktionslinien', '6 Schäummaschinen und 10 Produktionslinien'),
        ('Produktionsleistung von 7.000–8.000 Matten pro Tag (etwa 200.000 pro Monat)',
         'Produktionsleistung von etwa 1.000.000 Matten pro Jahr'),
        ('Wir betreiben 12 Produktionslinien mit einer Kapazität von 200.000 Matten pro Monat',
         'Wir betreiben 10 Produktionslinien mit einer Kapazität von 1.000.000 Matten pro Jahr'),
    ],
    'ja/': [
        ('月間生産能力', '生産能力'),
        ('<td>ヨガマット</td><td class="val">月間20万個',
         '<td>ヨガマット</td><td class="val">年間100万個'),
        ('月間生産能力は20万枚以上のヨガマット', '年間生産能力は100万枚以上のヨガマット'),
        ('マット / 月', 'マット / 年'),
        ('生産ライン12本、1日あたり7,000～8,000枚のマット',
         '生産ライン10本、年間約100万枚のマット'),
        ('6台の発泡機と12本の生産ラインを稼働させています', '6台の発泡機と10本の生産ラインを稼働させています'),
        ('1日あたり7,000～8,000枚（月間約20万枚）の安定した生産量を維持し',
         '年間約100万枚の安定した生産量を維持し'),
        ('当社は12の生産ラインを稼働させており、月間20万枚のマットを生産できる能力',
         '当社は10の生産ラインを稼働させており、年間100万枚のマットを生産できる能力'),
    ],
    'ko/': [
        ('월간 생산 능력', '생산 능력'),
        ('<td>요가 매트</td><td class="val">월 200,000개',
         '<td>요가 매트</td><td class="val">연 1,000,000개'),
        ('월간 200,000개 이상의 요가 매트를 생산할 수 있는 능력',
         '연간 1,000,000개 이상의 요가 매트를 생산할 수 있는 능력'),
        ('매트 / 월', '매트 / 연'),
        ('생산 라인 12개, 일일 생산량 7,000~8,000매',
         '생산 라인 10개, 연간 생산량 약 1,000,000매'),
        ('6대의 발포기와 12개의 생산 라인을 가동하고 있습니다', '6대의 발포기와 10개의 생산 라인을 가동하고 있습니다'),
        ('하루 7,000~8,000장(월 약 200,000장)의 안정적인 생산량을 유지하며',
         '연간 약 1,000,000장의 안정적인 생산량을 유지하며'),
        ('월 20만 장의 생산 능력을 갖춘 12개의 생산 라인을 운영하고 있으므로',
         '연 100만 장의 생산 능력을 갖춘 10개의 생산 라인을 운영하고 있으므로'),
    ],
    'fr/': [
        ('Capacité de production mensuelle', 'Capacité de production'),
        ('<td>Tapis de yoga</td><td class="val">200 000 pièces par mois',
         '<td>Tapis de yoga</td><td class="val">1 000 000 pièces par an'),
        ('une capacité de production mensuelle de plus de 200 000 tapis de yoga',
         'une capacité de production annuelle de plus de 1 000 000 de tapis de yoga'),
        ('Plus de 200 000 Tapis / Mois', 'Plus de 1 000 000 Tapis / An'),
        ('6 machines à mousser, 12 lignes de production, 7 000 à 8 000 tapis par jour',
         '6 machines à mousser, 10 lignes de production, environ 1 000 000 tapis par an'),
        ('équipées de 6 machines à mousser et de 12 lignes de production',
         'équipées de 6 machines à mousser et de 10 lignes de production'),
        ('production constante de 7 000 à 8 000 tapis par jour (environ 200 000 par mois)',
         "production constante d'environ 1 000 000 de tapis par an"),
        ("Nous disposons de 12 lignes de production d'une capacité de 200 000 tapis par mois",
         "Nous disposons de 10 lignes de production d'une capacité de 1 000 000 tapis par an"),
    ],
    'it/': [
        ('Capacità produttiva mensile', 'Capacità produttiva'),
        ('<td>Tappetini da yoga</td><td class="val">200.000 pezzi al mese',
         '<td>Tappetini da yoga</td><td class="val">1.000.000 pezzi all’anno'),
        ('capacità produttiva mensile di oltre 200.000 tappetini da yoga',
         'capacità produttiva annua di oltre 1.000.000 tappetini da yoga'),
        ('Oltre 200.000 Tappetini / Mese', 'Oltre 1.000.000 Tappetini / Anno'),
        ('6 macchine per la schiumatura, 12 linee di produzione, 7.000–8.000 tappetini al giorno',
         '6 macchine per la schiumatura, 10 linee di produzione, circa 1.000.000 tappetini all’anno'),
        ('con 6 macchine per la schiumatura e 12 linee di produzione',
         'con 6 macchine per la schiumatura e 10 linee di produzione'),
        ('produzione costante di 7.000–8.000 tappetini al giorno (circa 200.000 al mese)',
         'produzione costante di circa 1.000.000 tappetini all’anno'),
        ('disponiamo di 12 linee di produzione con una capacità di 200.000 tappetini al mese',
         'disponiamo di 10 linee di produzione con una capacità di 1.000.000 tappetini all’anno'),
    ],
    'es/': [
        ('Capacidad de producción mensual', 'Capacidad de producción'),
        ('<td>Esterillas de yoga</td><td class="val">200 000 unidades al mes',
         '<td>Esterillas de yoga</td><td class="val">1 000 000 unidades al año'),
        ('una capacidad mensual de más de 200 000 esterillas de yoga',
         'una capacidad anual de más de 1 000 000 esterillas de yoga'),
        ('Más de 200 000 Alfombras / Mes', 'Más de 1 000 000 Alfombras / Año'),
        ('6 máquinas de espumado, 12 líneas de producción, 7.000-8.000 esterillas al día',
         '6 máquinas de espumado, 10 líneas de producción, alrededor de 1.000.000 esterillas al año'),
        ('funcionan 6 máquinas de espumado y 12 líneas de producción',
         'funcionan 6 máquinas de espumado y 10 líneas de producción'),
        ('producción constante de entre 7.000 y 8.000 colchonetas al día (unas 200.000 al mes)',
         'producción constante de alrededor de 1.000.000 de colchonetas al año'),
        ('contamos con 12 líneas de producción con una capacidad de 200 000 alfombrillas al mes',
         'contamos con 10 líneas de producción con una capacidad de 1 000 000 alfombrillas al año'),
    ],
}

# 产线数字节点：把 <div class="num">5|12</div> 且后面紧跟产线 lab 的，统一改成 10
NUM_RE = re.compile(r'(<div class="num">)\s*(?:5|12)\s*(</div>\s*<div class="lab"[^>]*>[^<]*(?:' + LAB + r')[^<]*</div>)')


def apply(dry):
    miss = []
    done = 0
    for lg in LANGS:
        for pg in PAGES:
            p = os.path.join(ROOT, lg + pg)
            if not os.path.exists(p):
                continue
            s = open(p, encoding='utf-8').read()
            orig = s
            for a, b in RULES.get(lg, []):
                if a in s:
                    s = s.replace(a, b)
                else:
                    miss.append(f'{lg or "en"}{pg}  ✗ {a[:56]}')
            s, n = NUM_RE.subn(r'\g<1>10\g<2>', s)
            if n:
                done += n
            if s != orig and not dry:
                open(p, 'w', encoding='utf-8').write(s)
    return miss, done


BAD = [r'200,000', r'200\.000', r'200 000', r'20万', r'20만',
       r'7,?000[–~～\-]8,?000', r'7\.000[–\-]8\.000', r'7 000 à 8 000',
       r'12 (?:production|Produktions|lignes|linee|líneas)', r'12개의 생산 라인',
       r'12本の生産ライン', r'12 条产线']


def residue():
    out = []
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules', 'i18n_build',
                                                'outputs', '.workbuddy', 'assets')]
        for f in files:
            if not f.endswith('.html'):
                continue
            p = os.path.join(root, f)
            s = open(p, encoding='utf-8').read()
            for pt in BAD:
                m = re.search(pt, s)
                if m:
                    a = max(0, m.start() - 60)
                    out.append(f'{os.path.relpath(p, ROOT)}: …{re.sub(chr(10), " ", s[a:m.end()+60])[:150]}…')
                    break
    return out


if __name__ == '__main__':
    dry = '--check' in sys.argv
    miss, n = apply(dry)
    print(f'产线数字节点改写：{n} 处' + ('（dry-run）' if dry else ''))
    if miss:
        print(f'\n未命中 {len(miss)} 条：')
        for m in miss:
            print('   ', m)
    else:
        print('全部规则命中 ✅')
    if not dry:
        r = residue()
        print(f'\n[残留可疑数字] {len(r)} 个文件')
        for x in r[:30]:
            print('   ', x)
