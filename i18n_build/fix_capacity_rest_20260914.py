#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026-09-14  产能口径统一 —— 补漏轮

上一轮 fix_capacity_site_20260914.py 未覆盖的三类：
  1) index.html × 7：og:description 里的「月产 20 万」
  2) about.html (en)：og:description + 正文里的「12 lines / 12 production lines」
  3) 页脚工厂简介段「6 foaming machines, 12 production lines」
     （blog/yoga-mat-spec-guide.html 与 blog/yoga-mat-materials.html × 7 语言）

限定文件列表执行，不做全站 walk（全站扫描会超时）。
"""
import re, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ['', 'de/', 'ja/', 'ko/', 'fr/', 'it/', 'es/']
TARGETS = ['index.html', 'about.html',
           'blog/yoga-mat-spec-guide.html', 'blog/yoga-mat-materials.html']

RULES = {
    '': [
        # index og
        ('200K+ mats/month', '1M+ mats/year'),
        # about og
        ('3 owned plants, 6 foaming machines, 12 lines, 7,000–8,000 mats/day',
         '3 owned plants, 6 foaming machines, 10 lines, about 1,000,000 mats/year'),
        # about 正文
        ('running 6 foaming machines and 12 production lines',
         'running 6 foaming machines and 10 production lines'),
        # 页脚工厂简介
        ('Three owned plants, 6 foaming machines, 12 production lines.',
         'Three owned plants, 6 foaming machines, 10 production lines.'),
    ],
    'de/': [
        ('über 200.000 Matten pro Monat', 'über 1.000.000 Matten pro Jahr'),
        ('200.000+ Matten / Monat', '1.000.000+ Matten / Jahr'),
        (', 6 Schäummaschinen, 12 Produktionslinien.', ', 6 Schäummaschinen, 10 Produktionslinien.'),
        ('6 Schäummaschinen und 12 Produktionslinien', '6 Schäummaschinen und 10 Produktionslinien'),
    ],
    'ja/': [
        ('月産20万枚以上', '年間100万枚以上'),
        ('発泡機6台、生産ライン12本', '発泡機6台、生産ライン10本'),
        ('6台の発泡機と12本の生産ライン', '6台の発泡機と10本の生産ライン'),
    ],
    'ko/': [
        ('월 생산량 20만 장 이상', '연간 생산량 100만 장 이상'),
        ('발포 기계 6대, 생산 라인 12개', '발포 기계 6대, 생산 라인 10개'),
        ('6대의 발포기와 12개의 생산 라인', '6대의 발포기와 10개의 생산 라인'),
    ],
    'fr/': [
        ('plus de 200 000 tapis par mois', 'plus de 1 000 000 tapis par an'),
        ('6 machines à mousse, 12 lignes de production.', '6 machines à mousse, 10 lignes de production.'),
        ('6 machines à mousser et de 12 lignes de production', '6 machines à mousser et de 10 lignes de production'),
    ],
    'it/': [
        ('oltre 200.000 tappetini al mese', 'oltre 1.000.000 tappetini all’anno'),
        ('6 macchine per la schiumatura, 12 linee di produzione.', '6 macchine per la schiumatura, 10 linee di produzione.'),
        ('6 macchine per la schiumatura e 12 linee di produzione', '6 macchine per la schiumatura e 10 linee di produzione'),
    ],
    'es/': [
        ('más de 200 000 esterillas al mes', 'más de 1 000 000 esterillas al año'),
        ('6 máquinas de espumado y 12 líneas de producción.', '6 máquinas de espumado y 10 líneas de producción.'),
        ('6 máquinas de espumado y 12 líneas de producción', '6 máquinas de espumado y 10 líneas de producción'),
    ],
}

if __name__ == '__main__':
    dry = '--check' in sys.argv
    hit = miss = 0
    for lg in LANGS:
        for tg in TARGETS:
            p = os.path.join(ROOT, lg + tg)
            if not os.path.exists(p):
                continue
            s = open(p, encoding='utf-8').read()
            orig = s
            for a, b in RULES.get(lg, []):
                if a in s:
                    n = s.count(a)
                    s = s.replace(a, b)
                    hit += n
                # 未命中不报：规则按语言共用，跨页缺失属正常
            if s != orig:
                if not dry:
                    open(p, 'w', encoding='utf-8').write(s)
                print(f'  ✓ {lg + tg}')
    print(f'\n替换 {hit} 处' + ('（dry-run）' if dry else ''))
