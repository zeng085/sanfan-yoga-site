#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""关键入口页 description 压缩重写 —— 2026-09-25

【病根】
GSC 真实数据：28 天 99 次曝光、0 点击、平均位置 26.8。要让它变成点击，
description 是点击率的直接变量。而全站 799 页（60%）description 超
155 显示宽（CJK 按 2 宽），**入口页全在超标里**：
    products.html 233 / materials.html 232 / pu-rubber 172 /
    suede-cork 168 / meditation-pilates 167（EN）
语言版更夸张：fr/materials 318、es/materials 308、de/products 271。

【为什么不用 trim_meta_20260915.py --desc】
那个脚本的截断逻辑设计得很克制：只在能切出完整句子、且被丢弃的尾部
**不含** MOQ / 打样 / 认证 等 B2B 钩子时才切。实测拿它跑这 5 个页面，
4 个被它**正确地拒绝**（尾巴正好是钩子）—— 因为这几页的病根不是「多写了
废话」，而是「一句话太长」。所以必须整条重写到目标宽度，并**把钩子留在
155 宽之内**，而不是把钩子切掉。

【同步几份】
站内实测：meta / og:description / twitter:description 三处**同串**（HTML 转义形态一致）；
JSON-LD 的 CollectionPage.description 是**同一文案的另一种转义**（`&` vs `&amp;`）。
所以整页要改 4 处：3 处 HTML + 1 处 JSON。
⚠️ 绝不动 Organization.description（全站共用的实体描述，208 宽，与本页无关）。

【幂等】四处都已是目标文案 → 跳过。
用法：--check / --dry-run / 直接跑
"""
import argparse
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LANGS = ['en', 'de', 'ja', 'ko', 'fr', 'it', 'es']
DESC_BUDGET = 155
MIN_KEEP = 110

PAGES = ['products.html', 'materials.html', 'pu-rubber-yoga-mats.html',
         'suede-cork-yoga-mats.html', 'meditation-pilates-mats.html']

# 目标文案：四处同源（HTML 侧自动转义 &，JSON 侧保留 &）。不含双引号（脚本会断言）。
D = {
    'products.html': {
        'en': 'Browse the SANFAN catalogue: TPE, PU-rubber and suede & cork yoga mats, '
              'meditation mats, foam rollers and props. OEM/ODM, MOQ 100 pcs, samples in 7 days.',
        'de': 'SANFAN-Katalog: TPE-, PU-Gummi-, Wildleder- und Korkmatten, Meditationsmatten, '
              'Faszienrollen, Zubehör. OEM/ODM ab Werk, ab 100 Stück, Muster in 7 Tagen.',
        'ja': 'SANFAN カタログ：TPE・PUゴム・スエード・コルクのヨガマット、瞑想マット、'
              'フォームローラー、アクセサリー。工場直販 OEM/ODM、100 個から、7 日でサンプル。',
        'ko': 'SANFAN 카탈로그: TPE, PU 고무, 스웨이드, 코르크 요가 매트, 명상 매트, '
              '폼롤러, 액세서리. 공장 직판 OEM/ODM, 100개부터, 7일 샘플.',
        'fr': 'Catalogue SANFAN : tapis de yoga TPE, PU-caoutchouc, daim, liège, tapis de '
              'méditation, rouleaux. OEM/ODM d\u2019usine, dès 100 pièces, échantillons en 7 jours.',
        'it': 'Catalogo SANFAN: tappetini TPE, PU-gomma, suede e sughero, meditazione, '
              'foam roller. OEM/ODM di fabbrica, da 100 pezzi, campioni in 7 giorni.',
        'es': 'Catálogo SANFAN: esterillas TPE, PU-caucho, ante y corcho, meditación, '
              'foam rollers. OEM/ODM de fábrica, desde 100 uds., muestras en 7 días.',
    },
    'materials.html': {
        'en': 'TPE vs PVC vs PU vs natural rubber: cost, grip, weight, durability and '
              'compliance. OEM/ODM, MOQ 100 pcs, samples in 7 days.',
        'de': 'TPE, PVC, PU und Naturkautschuk im Vergleich: Kosten, Grip, Gewicht, '
              'Haltbarkeit und Compliance. OEM/ODM ab Werk, ab 100 Stück, Muster in 7 Tagen.',
        'ja': 'TPE・PVC・PU・天然ゴムの比較：コスト、グリップ、重さ、耐久性、法令対応。'
              '工場直販 OEM/ODM、100 個から、7 日でサンプル。',
        'ko': 'TPE, PVC, PU, 천연 고무 요가 매트 비교: 비용, 그립, 무게, 내구성, 규정 준수. '
              '공장 직판 OEM/ODM, 100개부터, 7일 샘플.',
        'fr': 'TPE, PVC, PU et caoutchouc naturel comparés : coût, adhérence, poids, '
              'durabilité, conformité. OEM/ODM d\u2019usine, dès 100 pièces, échantillons en 7 jours.',
        'it': 'TPE, PVC, PU e gomma naturale a confronto: costo, grip, peso, durata, '
              'conformità. OEM/ODM di fabbrica, da 100 pezzi, campioni in 7 giorni.',
        'es': 'TPE, PVC, PU y caucho natural comparados: coste, agarre, peso, durabilidad, '
              'normativa. OEM/ODM de fábrica, desde 100 uds., muestras en 7 días.',
    },
    'pu-rubber-yoga-mats.html': {
        'en': 'PU top on a natural rubber base for hot yoga: dry and wet grip, 4.5-5 mm, '
              'custom size, colour, logo and packaging. OEM/ODM, MOQ 100 pcs, samples 7 days.',
        'de': 'PU auf Naturkautschuk für Hot Yoga: Grip trocken und nass, 4,5-5 mm, Größe, '
              'Farbe, Logo nach Maß. OEM/ODM ab Werk, ab 100 Stück, Muster in 7 Tagen.',
        'ja': 'ホットヨガ向け PU＋天然ゴム：乾湿両方のグリップ、4.5-5 mm、サイズ・色・ロゴは'
              'オーダー対応。工場直販 OEM/ODM、100 個から、7 日サンプル。',
        'ko': '핫요가용 PU+천연고무 매트: 건식·습식 그립, 4.5-5 mm, 사이즈·색상·로고 맞춤. '
              '공장 직판 OEM/ODM, 100개부터, 7일 샘플.',
        'fr': 'Dessus PU sur caoutchouc naturel pour hot yoga : adhérence sèche et humide, '
              '4,5-5 mm, sur mesure. OEM/ODM d\u2019usine, dès 100 pièces, échantillons en 7 jours.',
        'it': 'Top in PU su gomma naturale per hot yoga: grip asciutto e bagnato, 4,5-5 mm, '
              'su misura. OEM/ODM di fabbrica, da 100 pezzi, campioni in 7 giorni.',
        'es': 'Superficie de PU sobre caucho natural para hot yoga: agarre seco y húmedo, '
              '4,5-5 mm, a medida. OEM/ODM de fábrica, desde 100 uds., muestras en 7 días.',
    },
    'suede-cork-yoga-mats.html': {
        'en': 'Suede and cork mats for hot yoga and premium retail: natural grip, 3-5 mm, '
              'custom print, size and logo. OEM/ODM, MOQ 100 pcs, samples in 7 days.',
        'de': 'Wildleder- und Korkmatten für Hot Yoga und Premium: Naturgrip, 3-5 mm, Druck, '
              'Größe und Logo nach Maß. OEM/ODM ab Werk, ab 100 Stück, Muster in 7 Tagen.',
        'ja': 'ホットヨガ・高級向けのスエード＆コルクマット：天然グリップ、3-5 mm、'
              'プリント・サイズ・ロゴ対応。工場直販 OEM/ODM、100 個から、7 日でサンプル。',
        'ko': '핫요가·프리미엄용 스웨이드·코르크 매트: 천연 그립, 3-5 mm, 인쇄·사이즈·로고 맞춤. '
              '공장 직판 OEM/ODM, 100개부터, 7일 샘플.',
        'fr': 'Tapis en daim et liège pour hot yoga : adhérence naturelle, 3-5 mm, impression, '
              'taille et logo. OEM/ODM d\u2019usine, dès 100 pièces, échantillons en 7 jours.',
        'it': 'Tappetini in suede e sughero per hot yoga: grip naturale, 3-5 mm, stampa, '
              'misura e logo su misura. OEM/ODM di fabbrica, da 100 pezzi, campioni in 7 giorni.',
        'es': 'Esterillas de ante y corcho para hot yoga: agarre natural, 3-5 mm, impresión, '
              'medida a medida. OEM/ODM de fábrica, desde 100 uds., muestras en 7 días.',
    },
    'meditation-pilates-mats.html': {
        'en': 'Round, mandala and reformer mats for meditation, Pilates and studio floors: '
              '6-15 mm, custom size and logo. OEM/ODM, MOQ 100 pcs, samples in 7 days.',
        'de': 'Runde, Mandala- und Reformer-Matten für Meditation und Pilates: 6-15 mm, '
              'Größe und Logo nach Maß. OEM/ODM ab Werk, ab 100 Stück, Muster in 7 Tagen.',
        'ja': '瞑想・ピラティス・スタジオ向けのラウンド・マンダラ・リフォーマーマット：'
              '6-15 mm、サイズとロゴはオーダー対応。工場直販 OEM/ODM、100 個から、7 日サンプル。',
        'ko': '명상·필라테스·스튜디오용 라운드·만달라·리포머 매트: 6-15 mm, 사이즈와 로고 맞춤. '
              '공장 직판 OEM/ODM, 100개부터, 7일 샘플.',
        'fr': 'Tapis ronds, mandala et reformer pour méditation et Pilates : 6-15 mm, sur '
              'mesure. OEM/ODM d\u2019usine, dès 100 pièces, échantillons en 7 jours.',
        'it': 'Tappetini rotondi, mandala e reformer per meditazione e Pilates: 6-15 mm su '
              'misura. OEM/ODM di fabbrica, da 100 pezzi, campioni in 7 giorni.',
        'es': 'Esterillas redondas, mandala y reformer para meditación y Pilates: 6-15 mm a '
              'medida. OEM/ODM de fábrica, desde 100 uds., muestras en 7 días.',
    },
}

# 各语言必须留住的「转化信息」词干
HOOK = {
    'en': ('OEM', 'ODM', 'MOQ', 'sampl'),
    'de': ('OEM', 'ODM', 'Stück', 'Muster'),
    'ja': ('OEM', 'ODM', '個', 'サンプル'),
    'ko': ('OEM', 'ODM', '개', '샘플'),
    'fr': ('OEM', 'ODM', 'pièces', 'chantillons'),
    'it': ('OEM', 'ODM', 'pezzi', 'campioni'),
    'es': ('OEM', 'ODM', 'uds', 'muestras'),
}


def W(s):
    return sum(2 if ord(c) > 0x2E80 else 1 for c in s)


def check_text(lg, txt):
    assert '"' not in txt, '%s：文案不能含双引号' % lg
    n = W(txt)
    assert n <= DESC_BUDGET, '%s：宽度 %d 超 %d' % (lg, n, DESC_BUDGET)
    assert n >= MIN_KEEP, '%s：宽度 %d 太短（< %d）' % (lg, n, MIN_KEEP)
    for h in HOOK[lg]:
        assert h.lower() in txt.lower(), '%s：缺转化钩子 %r' % (lg, h)
    return n


def lang_path(page, lg):
    return page if lg == 'en' else '%s/%s' % (lg, page)


def patch_jsonld(t, new_json):
    """按 @type 定位「页面级」节点的 description 并替换。

    必须按 @type 定位而不是「第一处 description」：同一块 @graph 里
    Organization 也有 description（全站共用的实体描述），改它等于污染全站实体层。
    站点用过的页面级类型实测有三种：CollectionPage（分类页）、WebPage、Article
    （materials.html 这种指南页就是一个 @type=Article 的节点承载页面描述）。
    """
    PAGE_TYPES = ('"CollectionPage"', '"WebPage"', '"Article"')
    done = 0

    def repl(m):
        nonlocal done
        blk = m.group(1)
        tp = -1
        for t_ in PAGE_TYPES:
            i = blk.find(t_)
            if i >= 0 and (tp < 0 or i < tp):
                tp = i
        if tp < 0:
            return m.group(0)
        head, tail = blk[:tp], blk[tp:]
        mm = re.search(r'("description"\s*:\s*")((?:[^"\\]|\\.)*)(")', tail)
        if not mm:
            return m.group(0)
        if mm.group(2) == new_json:
            done += 1
            return m.group(0)
        done += 1
        newtail = tail[:mm.start(2)] + new_json + tail[mm.end(2):]
        return '<script type="application/ld+json">' + head + newtail + '</script>'

    t2 = re.sub(r'<script type="application/ld\+json">(.*?)</script>', repl, t, flags=re.S)
    return t2, done


def patch(t, page, lg, new_plain):
    new_html = html.escape(new_plain, quote=False)
    new_json = new_plain.replace('\\', '\\\\').replace('"', '\\"')
    notes = []

    # ① meta / og / twitter：三处同串
    m = re.search(r'<meta name="description" content="([^"]*)"', t)
    assert m, '%s：找不到 meta description' % lang_path(page, lg)
    old_meta = m.group(1)
    if old_meta == new_html:
        notes.append('HTML已是目标')
    else:
        cnt = t.count('content="%s"' % old_meta)
        assert cnt == 3, '%s：旧描述串出现 %d 次（应 3）' % (lang_path(page, lg), cnt)
        t = t.replace('content="%s"' % old_meta, 'content="%s"' % new_html)
        assert t.count('content="%s"' % new_html) == 3, '替换后计数异常'
        notes.append('HTML×3')

    # ② JSON-LD
    t, done = patch_jsonld(t, new_json)
    notes.append('JSON-LD已是目标' if done and old_meta != new_html and 'JSON-LD已是目标' in notes
                 else ('JSON-LD×%d' % done if done else 'JSON-LD 未命中'))
    if done == 0:
        notes[-1] = '⚠️ JSON-LD 未命中'
    return t, notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    print('=== 目标文案宽度自检（预算 %d，下限 %d）===' % (DESC_BUDGET, MIN_KEEP))
    print('  %-32s%s' % ('page', ''.join('%6s' % lg for lg in LANGS)))
    bad = []
    for page in PAGES:
        row = []
        for lg in LANGS:
            try:
                row.append(check_text(lg, D[page][lg]))
            except AssertionError as e:
                bad.append(str(e))
                row.append(-1)
        print('  %-32s%s' % (page, ''.join('%6d' % n for n in row)))
    if bad:
        print('\n文案自检未过：')
        for b in bad:
            print('   ✗', b)
        sys.exit(1)

    print('\n=== 处理 ===')
    changed = 0
    warn = 0
    for page in PAGES:
        for lg in LANGS:
            f = lang_path(page, lg)
            p = os.path.join(ROOT, f)
            assert os.path.exists(p), '缺文件 ' + f
            t = open(p, encoding='utf-8').read()
            t2, notes = patch(t, page, lg, D[page][lg])
            if '⚠️' in ' '.join(notes):
                warn += 1
            if t2 != t:
                changed += 1
            print('  %s %-34s %s' % ('·' if (a.check or a.dry_run) else '✓', f, ' '.join(notes)))
            if t2 != t and not (a.check or a.dry_run):
                with open(p, 'w', encoding='utf-8') as fh:
                    fh.write(t2)
    print('\n共 %d 个文件，改动 %d 个，JSON-LD 未命中 %d 个%s'
          % (len(PAGES) * len(LANGS), changed, warn,
             '（干跑，未落盘）' if (a.check or a.dry_run) else ''))


if __name__ == '__main__':
    main()
