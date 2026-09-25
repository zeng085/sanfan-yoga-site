#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""站内正文内链（Topic Cluster）注入 —— 2026-09-25

【病根】
页面上线后从没做过编辑内链。剔除 header/nav/footer 后实测：
  · 10 篇博客里 9 篇正文内链 = 0（只剩面包屑 blog.html）
  · 4 个主分类页正文到博客的链接 = 0
而 GSC 真实数据恰好相反：**排名最好的是博客**（de/blog/yoga-mat-materials 位置 6.8、
es 6.7、ko 6.7、fr/blog/yoga-mat-spec-guide 11.0），拿到曝光的却几乎不是商业页。
→ 用「教程页 → 分类页」和「分类页 → 教程页」的双向编辑内链，把已有的排名信号
  导向商业落地页。这是 Phase 2 里收益最高、风险最低的一项。

【做法】
在既有的稳定结构锚点上插入一段带标记的链接块（幂等、可整体回退）：
  · 博客页：插在语言块内最后一个 <p class="article-cta"> 之前
            （EN 页有两个语言块 → en 一份、zh 一份；语言页只有一个）
  · 分类页：插在**最后一个 <section>**（即居中 CTA 区）之前
锚文本一律人工拟定（不用 H1 自动提取 —— fr/it/es 的 H1 存在机翻语序残留，
且博客 H1 太长不适合当锚文本）。

【幂等 / 回退】
插入的是一整段**字面量**字符串（含首尾标记），回退断言就是把它原样去掉：
    assert t2.replace(block, '', 1) == t
不做 「插 \n + 插块」两段式 —— 那样摘除时换行不互逆，每跑一次多一个空行。

用法：
    python3 i18n_build/add_internal_links_20260925.py --check
    python3 i18n_build/add_internal_links_20260925.py --dry-run
    python3 i18n_build/add_internal_links_20260925.py            # 落盘
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

LANGS = ['en', 'zh', 'de', 'ja', 'ko', 'fr', 'it', 'es']
SUBDIRS = {'de': 'de', 'ja': 'ja', 'ko': 'ko', 'fr': 'fr', 'it': 'it', 'es': 'es'}

MARK_A = '<!-- ilink:v1 -->'
MARK_B = '<!-- /ilink:v1 -->'
ORG_A = '<!-- orgref:v1 -->'

# 博客里的「文章收尾 CTA」有两种既有写法，都要当锚点：
#   ① <p class="article-cta">…         —— 9 篇
#   ② <div style="margin:28px 0;padding:20px 22px…">…</div>  —— top-12 那一篇
# 每种在每个语言块里各出现一次，所以「出现次数 == 语言块数」可用来判定锚点是否齐全。
CTA_RE = re.compile(r'[ \t]*(?:<p class="article-cta"|<div style="margin:28px 0;padding:20px 22px)')

# ------------------------------------------------------------------ 锚文本
# 短名词短语：既是锚文本，也是给 Google 的主题信号。翻译按各语言习惯语序。
ANCHOR = {
    'tpe': {
        'en': 'TPE yoga mats', 'zh': 'TPE 瑜伽垫',
        'de': 'TPE-Yogamatten', 'ja': 'TPE ヨガマット', 'ko': 'TPE 요가 매트',
        'fr': 'tapis de yoga en TPE', 'it': 'tappetini da yoga in TPE',
        'es': 'esterillas de yoga de TPE',
    },
    'purubber': {
        'en': 'PU &amp; rubber yoga mats', 'zh': 'PU 橡胶瑜伽垫',
        'de': 'PU- und Naturkautschukmatten', 'ja': 'PU・天然ゴムヨガマット',
        'ko': 'PU·천연고무 요가 매트', 'fr': 'tapis en PU et caoutchouc naturel',
        'it': 'tappetini in PU e gomma naturale', 'es': 'esterillas de PU y caucho natural',
    },
    'materials': {
        'en': 'yoga mat materials guide', 'zh': '瑜伽垫材质指南',
        'de': 'Yogamatten-Materialguide', 'ja': 'ヨガマット素材ガイド',
        'ko': '요가 매트 소재 가이드', 'fr': 'guide des matériaux',
        'it': 'guida ai materiali', 'es': 'guía de materiales',
    },
    'products': {
        'en': 'full product range', 'zh': '全部产品',
        'de': 'das komplette Sortiment', 'ja': '製品一覧', 'ko': '전체 제품 라인업',
        'fr': 'toute la gamme', 'it': 'tutta la gamma', 'es': 'toda la gama',
    },
    'bmats': {
        'en': 'Yoga Mat Materials Compared', 'zh': '瑜伽垫材质横评',
        'de': 'Materialvergleich für Yogamatten', 'ja': 'ヨガマット素材比較',
        'ko': '요가 매트 소재 비교', 'fr': 'comparaison des matériaux',
        'it': 'confronto dei materiali', 'es': 'comparativa de materiales',
    },
    'bspec': {
        'en': 'Yoga Mat Thickness &amp; Size Guide', 'zh': '厚度与尺寸指南',
        'de': 'Dicken- und Größenguide', 'ja': '厚さ・サイズガイド',
        'ko': '두께·사이즈 가이드', 'fr': 'guide des épaisseurs et tailles',
        'it': 'guida a spessori e misure', 'es': 'guía de grosores y tamaños',
    },
    'btpepu': {
        'en': 'TPE vs PU rubber: which to choose', 'zh': 'TPE 与 PU 橡胶怎么选',
        'de': 'TPE oder PU: der Vergleich', 'ja': 'TPE と PU の比較',
        'ko': 'TPE와 PU 비교', 'fr': 'TPE ou PU : la comparaison',
        'it': 'TPE o PU: il confronto', 'es': 'TPE o PU: la comparación',
    },
    'bcustom': {
        'en': 'custom size and thickness guide', 'zh': '定制尺寸与厚度指南',
        'de': 'Sondergrößen und Dicken', 'ja': 'カスタムサイズ・厚さ',
        'ko': '맞춤 사이즈와 두께', 'fr': 'tailles et épaisseurs sur mesure',
        'it': 'misure e spessori su misura', 'es': 'medidas y grosores a medida',
    },
    'bmoq': {
        'en': 'MOQ explained', 'zh': '起订量说明',
        'de': 'Mindestbestellmenge erklärt', 'ja': '最小注文数の解説',
        'ko': '최소 주문 수량 안내', 'fr': 'quantité minimale expliquée',
        'it': 'quantità minima spiegata', 'es': 'pedido mínimo explicado',
    },
    'bcompl': {
        'en': 'REACH &amp; Prop 65 compliance guide', 'zh': 'REACH 与 65 号提案合规指南',
        'de': 'REACH- und Prop-65-Leitfaden', 'ja': 'REACH・プロップ65 ガイド',
        'ko': 'REACH·Prop 65 가이드', 'fr': 'guide REACH et Prop 65',
        'it': 'guida REACH e Prop 65', 'es': 'guía REACH y Prop 65',
    },
    'bprivate': {
        'en': 'private label launch guide', 'zh': '自有品牌上市指南',
        'de': 'Private-Label-Leitfaden', 'ja': 'プライベートブランド立ち上げガイド',
        'ko': '자체 브랜드 출시 가이드', 'fr': 'guide de lancement en marque propre',
        'it': 'guida al lancio private label', 'es': 'guía para lanzar tu marca',
    },
}

# ------------------------------------------------------------------ 目标页
TARGET = {
    'tpe': 'tpe-yoga-mats.html',
    'purubber': 'pu-rubber-yoga-mats.html',
    'materials': 'materials.html',
    'products': 'products.html',
    'bmats': 'blog/yoga-mat-materials.html',
    'bspec': 'blog/yoga-mat-spec-guide.html',
    'btpepu': 'blog/tpe-vs-pu.html',
    'bcustom': 'blog/custom-sizes.html',
    'bmoq': 'blog/moq-explained.html',
    'bcompl': 'blog/compliance.html',
    'bprivate': 'blog/private-label-yoga-mats.html',
}

# ------------------------------------------------------------------ 链出map
# 依据 GSC 实测排名：教程页（排名好）→ 商业页（要排名）。
# 每页 3 条，互不重复，且不与页面已有的正文链接重复。
BLOG_OUT = {
    'blog/yoga-mat-materials.html': ['tpe', 'purubber', 'products'],
    'blog/yoga-mat-spec-guide.html': ['tpe', 'purubber', 'products'],
    'blog/tpe-vs-pu.html': ['tpe', 'purubber', 'materials'],
    'blog/custom-sizes.html': ['tpe', 'products', 'bspec'],
    'blog/moq-explained.html': ['products', 'tpe', 'bcustom'],
    'blog/compliance.html': ['materials', 'products', 'bmats'],
    'blog/private-label-yoga-mats.html': ['materials', 'bmoq', 'products'],
    'blog/7day-sampling.html': ['products', 'bmoq', 'bprivate'],
    'blog/vet-factory.html': ['products', 'bcompl', 'bmats'],
    'blog/top-12-china-yoga-mat-manufacturers.html': ['products', 'bcompl', 'bprivate'],
}
CAT_OUT = {
    'tpe-yoga-mats.html': ['bmats', 'bspec', 'btpepu'],
    'pu-rubber-yoga-mats.html': ['btpepu', 'bmats', 'bspec'],
    'materials.html': ['bmats', 'btpepu', 'bcompl'],
    'products.html': ['bcustom', 'bmoq', 'bspec', 'bprivate'],
    # 2026-09-25：8 个一级分类页补正文内链（与 add_category_content 同批）。
    # ⚠️ 这 8 页此前**一处标记都没有**，所以必须**先跑本脚本**再跑 contents 脚本 ——
    #    cfaq 的插入锚点写死就是 `<!-- ilink:v1 -->`。
    'foam-rollers.html': ['bmoq', 'bcustom', 'bprivate'],
    'massage-recovery.html': ['bmoq', 'bcustom', 'bprivate'],
    'strength-training.html': ['bmoq', 'bcustom', 'bprivate'],
    'jump-ropes.html': ['bmoq', 'bcustom', 'products'],
    'resistance-bands.html': ['bmoq', 'bcustom', 'products'],
    'yoga-props-accessories.html': ['bmoq', 'bcustom', 'products'],
    'suede-cork-yoga-mats.html': ['bmats', 'bspec', 'btpepu'],
    'meditation-pilates-mats.html': ['bcustom', 'bspec', 'bmoq'],
}

# ⚠️ `cat_h2` 的原文案是「Further reading on choosing a mat / 选垫子之前…」——
#    对垫类分类页正确，但**泡沫轴 / 跳绳 / 弹力带 / 辅具 / 力量 / 恢复**这 6 页
#    并不是垫，标题会读成「怎么选垫子」，页面自我矛盾。
#    故按页面族分两组文案；下列 6 页走 gear 组，其余（含已上线的 tpe/pu/materials/products）
#    保持原 `cat_h2` 不变，避免动到已上线页面。
CAT_GEAR_PAGES = {
    'foam-rollers.html', 'jump-ropes.html', 'resistance-bands.html',
    'yoga-props-accessories.html', 'strength-training.html', 'massage-recovery.html',
}

# ------------------------------------------------------------------ 结构文案
TXT = {
    'blog_h2': {
        'en': 'Related reading', 'zh': '相关阅读',
        'de': 'Passend dazu', 'ja': '関連ガイド', 'ko': '관련 자료',
        'fr': 'Pour aller plus loin', 'it': 'Approfondimenti', 'es': 'Para profundizar',
    },
    'blog_intro': {
        'en': 'Where this fits in our own catalogue:',
        'zh': '这些正是我们自己产品线上的对应页面：',
        'de': 'Die passenden Seiten aus unserem eigenen Katalog:',
        'ja': '当社カタログの該当ページはこちらです：',
        'ko': '당사 카탈로그의 해당 페이지:',
        'fr': 'Les pages correspondantes de notre catalogue :',
        'it': 'Le pagine corrispondenti del nostro catalogo:',
        'es': 'Las páginas correspondientes de nuestro catálogo:',
    },
    'cat_h2': {
        'en': 'Further reading on choosing a mat',
        'zh': '选垫子之前，建议先读这几篇',
        'de': 'Weiterlesen: die passende Matte auswählen',
        'ja': 'マット選びの前に読みたい記事',
        'ko': '매트 선택 전에 읽어볼 글',
        'fr': 'Pour aller plus loin dans le choix du tapis',
        'it': 'Per approfondire la scelta del tappetino',
        'es': 'Para profundizar en la elección de la esterilla',
    },
    # 非垫类分类页（泡沫轴 / 跳绳 / 弹力带 / 辅具 / 力量 / 恢复）用这组。
    'cat_h2_gear': {
        'en': 'Sourcing guides for buyers',
        'zh': '采购环节最常问的问题，都写在这里',
        'de': 'Leitfäden für Einkäufer',
        'ja': '購買担当者向けガイド',
        'ko': '구매 담당자를 위한 가이드',
        'fr': 'Guides pour les acheteurs',
        'it': 'Guide per gli acquirenti',
        'es': 'Guías para compradores',
    },
    'cat_intro': {
        'en': 'The buyer guides we get the most questions about, written from our own production lines:',
        'zh': '被问得最多的采购问题都写在这里，全部来自我们自己的产线：',
        'de': 'Die Fragen, die uns Einkäufer am häufigsten stellen – aus unserer eigenen Produktion:',
        'ja': '購買担当者から最も多く寄せられる疑問を、自社工場の視点でまとめました：',
        'ko': '구매 담당자가 가장 많이 묻는 질문을 자체 생산라인 기준으로 정리했습니다:',
        'fr': 'Les questions que les acheteurs nous posent le plus, vues de nos propres lignes :',
        'it': 'Le domande che riceviamo più spesso dagli acquirenti, dalle nostre linee di produzione:',
        'es': 'Las preguntas que más nos hacen los compradores, desde nuestras propias líneas:',
    },
}


def href_for(target_id, from_file):
    """从 from_file 指向 target_id 的相对链接。同语言目录结构镜像根目录。"""
    tgt = TARGET[target_id]
    in_blog = from_file.split('/')[-2] == 'blog' if '/' in from_file else False
    if tgt.startswith('blog/'):
        leaf = tgt.split('/')[-1]
        return leaf if in_blog else tgt
    return ('../' + tgt) if in_blog else tgt


def lang_file(page, lang):
    """逻辑语言 → 实际文件路径"""
    if lang in ('en', 'zh'):
        return page
    return '%s/%s' % (SUBDIRS[lang], page)


def pair(en, zh):
    """分类页是行内 span 双语切换 —— 每个可见文本都要成对出现。"""
    return '<span class="lang-en">%s</span><span class="lang-zh">%s</span>' % (en, zh)


def build_block(page, lang, kind, out_ids, indent):
    """一整段字面量（含标记），回退时原样摘除即可。

    kind == 'blog'：lang 是该语言块的**实际语言**（en / zh / de …），单语输出。
    kind == 'cat' ：EN 页（lang=='en'）输出 en+zh 配对 span；语言页输出单语。
    """
    L = [indent + MARK_A]
    if kind == 'blog':
        L.append(indent + '<h2>%s</h2>' % TXT['blog_h2'][lang])
        L.append(indent + '<p>%s</p>' % TXT['blog_intro'][lang])
        L.append(indent + '<ul>')
        for tid in out_ids:
            L.append(indent + '  <li><a href="%s">%s</a></li>'
                     % (href_for(tid, page), ANCHOR[tid][lang]))
        L.append(indent + '</ul>')
    else:
        bi = (lang == 'en')
        h2_key = 'cat_h2_gear' if page in CAT_GEAR_PAGES else 'cat_h2'
        h2 = pair(TXT[h2_key]['en'], TXT[h2_key]['zh']) if bi else TXT[h2_key][lang]
        intro = pair(TXT['cat_intro']['en'], TXT['cat_intro']['zh']) if bi else TXT['cat_intro'][lang]
        L.append(indent + '<section class="section">')
        L.append(indent + '  <div class="container">')
        L.append(indent + '    <div class="section-head">')
        L.append(indent + '      <h2>%s</h2>' % h2)
        L.append(indent + '      <p>%s</p>' % intro)
        L.append(indent + '    </div>')
        L.append(indent + '    <ul style="max-width:760px;margin:0 auto;padding-left:22px;'
                          'line-height:2;font-size:16px;">')
        for tid in out_ids:
            a = pair(ANCHOR[tid]['en'], ANCHOR[tid]['zh']) if bi else ANCHOR[tid][lang]
            L.append(indent + '      <li><a href="%s">%s</a></li>' % (href_for(tid, page), a))
        L.append(indent + '    </ul>')
        L.append(indent + '  </div>')
        L.append(indent + '</section>')
    L.append(indent + MARK_B + '\n')
    return '\n'.join(L)


def indent_at(t, pos):
    ls = t.rfind('\n', 0, pos) + 1
    return re.match(r'[ \t]*', t[ls:pos]).group(0)


def inject_at(t, pos, block):
    t2 = t[:pos] + block + t[pos:]
    assert t2.replace(block, '', 1) == t, '回退断言不一致（插入型）'
    return t2


def blog_insert_points(t, lang):
    """返回 [(插入位置, 语言)]，从后往前插。

    首选锚点：语言块内最后一个 <p class="article-cta"> 之前。
    兜底锚点：文章正文容器末尾 —— 个别语言页（de/…/private-label）没有 article-cta，
              此时退到 </article> 前最后一个 </div> 之前（即 .article-body 的最后一个子节点位）。
    """
    want = 2 if lang in ('en', 'zh') else 1
    blocks = list(CTA_RE.finditer(t))
    if len(blocks) == want:
        if want == 2:
            pos_en = t.index('<div class="lang-en">')
            pos_zh = t.index('<div class="lang-zh">')
            assert pos_en < blocks[0].start() < pos_zh < blocks[1].start(), \
                'article-cta 与语言块顺序不符'
            order = ['en', 'zh']
        else:
            order = [lang]
        return [(b.start(), order[i]) for i, b in enumerate(blocks)]

    assert len(blocks) == 0 and want == 1, \
        'article-cta %d 个（应 %d）' % (len(blocks), want)
    end = t.rindex('</article>')
    pos = t.rindex('</div>', 0, end)
    assert end - pos < 200, '</article> 前的 </div> 距离异常（%d 字符），结构可能变了' % (end - pos)
    return [(pos, lang)]


def patch_blog(t, page, out_ids, lang):
    """博客：按 blog_insert_points 给出的位置插入，从后往前避免位移。"""
    pts = blog_insert_points(t, lang)
    for pos, lg in reversed(pts):
        block = build_block(page, lg, 'blog', out_ids, indent_at(t, pos))
        t = inject_at(t, pos, block)
    return t


def patch_cat(t, page, out_ids, lang):
    """分类页：在最后一个 <section>（居中 CTA）之前插入。"""
    secs = list(re.finditer(r'[ \t]*<section\b', t))
    assert secs, '%s：找不到 section' % page
    pos = secs[-1].start()
    tail = t[pos:pos + 400]
    assert 'text-align:center' in tail, '%s：最后一个 section 不是居中 CTA 区' % page
    block = build_block(page, lang, 'cat', out_ids, indent_at(t, pos))
    return inject_at(t, pos, block)


def expected_markers(lang, kind):
    """一个文件里应出现几段 ilink 块。

    只有**博客 EN 页**是 2 段（lang-en 一个语言块、lang-zh 一个语言块）；
    分类页虽是双语，但用行内 span 切换，整个文件只插 1 段（块内自带 en/zh 两种锚文本）。
    """
    return 2 if (kind == 'blog' and lang in ('en', 'zh')) else 1


def process(page, lang, kind, out_ids, dry=False):
    f = lang_file(page, lang)
    path = os.path.join(ROOT, f)
    t = open(path, encoding='utf-8').read()

    # 安全检查：插入点必须在实体层标记之外
    if ORG_A in t:
        assert t.index(ORG_A) < t.index('</head>'), '%s：orgref 标记位置异常' % f

    want = expected_markers(lang, kind)
    got = t.count(MARK_A)
    assert got in (0, want), '%s：ilink 标记 %d 个（既非 0 也非 %d），疑似半完成状态' % (f, got, want)
    if got == want:
        return t, ['已是目标状态'] * want

    # 链接目标文件必须存在
    for tid in out_ids:
        tt = lang_file(TARGET[tid], lang)
        assert os.path.exists(os.path.join(ROOT, tt)), '%s：链接目标不存在 %s' % (f, tt)

    t2 = patch_blog(t, page, out_ids, lang) if kind == 'blog' else patch_cat(t, page, out_ids, lang)
    assert t2.count(MARK_A) == want, '%s：插入后标记 %d 个（应 %d）' % (f, t2.count(MARK_A), want)
    return t2, ['+内链×%d' % len(out_ids)] * want


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true', help='只报告')
    ap.add_argument('--dry-run', action='store_true', help='不落盘')
    a = ap.parse_args()

    jobs = []
    for page, ids in BLOG_OUT.items():
        for lang in LANGS:
            jobs.append((page, lang, 'blog', ids))
    for page, ids in CAT_OUT.items():
        for lang in LANGS:
            jobs.append((page, lang, 'cat', ids))

    changed = 0
    for page, lang, kind, ids in jobs:
        f = lang_file(page, lang)
        try:
            t2, notes = process(page, lang, kind, ids)
        except AssertionError as e:
            print('  ✗ %-46s %s' % (f, e))
            if not a.check:
                sys.exit(1)
            continue
        if '已是目标状态' not in notes[0]:
            changed += 1
            print('  %s %-46s %s' % ('·' if (a.check or a.dry_run) else '✓',
                                     f, ' '.join(notes)))
            if not (a.check or a.dry_run):
                with open(os.path.join(ROOT, f), 'w', encoding='utf-8') as fh:
                    fh.write(t2)

    print('\n页面 %d 个（%d 篇博客 + %d 个分类页）× %d 语言 = %d 个文件；本次改动 %d 个%s'
          % (len(BLOG_OUT) + len(CAT_OUT), len(BLOG_OUT), len(CAT_OUT), len(LANGS),
             len(jobs), changed,
             '（干跑，未落盘）' if (a.check or a.dry_run) else ''))


if __name__ == '__main__':
    main()
