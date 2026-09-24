# -*- coding: utf-8 -*-
"""
EVA ≡ TPE「行业叫法」最小口径补充（2026-09-24）

背景：用户要的是「客户搜 EVA 瑜伽垫时，找的其实就是我们的 TPE 垫；行业里这两个叫法
指同一类产品」。不做新页、不动页脚、不动实体层、不动 sitemap。

落点（4 类，全部幂等）：
  ① tpe-yoga-mats.html（EN）+ 6 语言版：产品区之后、CTA 之前插入一小节
     （eyebrow + h2 + 两段正文 + 2 条 FAQ）  —— 标记 EVA-TPE-NOTE
  ② 同上 7 页：追加 FAQPage JSON-LD                          —— 标记 EVA-TPE-FAQ-LD
  ③ 同上 7 页：description 补 EVA 叫法（meta + og + JSON-LD 三处同步）
  ④ materials.html + 6 语言版：EVA 行「最适合」格改口径

为什么语言版手写译文而不走翻译管线：
  实测把改动后的 EN 源页丢进 run_i18n_batch，会让这批老页面产生附带漂移
  （de 标题破折号被换、JSON-LD 商品名被套引号），而且翻译缓存命中时不调 API、
  坏译文重跑不自愈。故这里直接注入手写译文。EN 页仍带 lang-zh 配对 span，
  将来若真跑管线，语言版会得到同一小节的机翻版本（届时需复核）。

幂等保证：所有插入块带 START/END 标记，先摘旧块再重插；
         每次插入都做「摘掉新块 == 摘干净的原文」回退断言。
"""
import os
import re
import sys
import json
import html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRY = '--dry-run' in sys.argv

LANGS = ['de', 'ja', 'ko', 'fr', 'it', 'es']
TPE = 'tpe-yoga-mats.html'
MAT = 'materials.html'

CTA = '<section class="section soft">'
CTA_ANCHOR = '\n  </section>\n\n  ' + CTA

MARK_A = '<!-- EVA-TPE-NOTE-START -->'
MARK_B = '<!-- EVA-TPE-NOTE-END -->'
LD_A = '<!-- EVA-TPE-FAQ-LD-START -->'
LD_B = '<!-- EVA-TPE-FAQ-LD-END -->'
# 实体层注入脚本（add_org_sameas_20260924.py）的区间起点。我们的 FAQPage 要放它**外面**。
ORG_MARK = '<!-- orgref:v1 -->'

RE_NOTE = re.compile(re.escape(MARK_A) + r'\n[\s\S]*?' + re.escape(MARK_B) + r'\n\n')
RE_LD = re.compile(r'\n[ \t]*' + re.escape(LD_A) + r'[\s\S]*?' + re.escape(LD_B))
RE_LDJSON = re.compile(r'<script type="application/ld\+json">[\s\S]*?</script>')

# ---------------------------------------------------------------- 文案

EN = dict(
    eyebrow='EVA or TPE?',
    h2='Searching for an EVA yoga mat?',
    p1='In this trade the two names are used for the same mat. Buyers, studios and importers '
       'routinely ask for an \u201cEVA yoga mat\u201d when what they need is the closed-cell foam mat '
       'we produce in TPE \u2014 the same product, quoted under either word. So when your enquiry '
       'arrives as EVA, we quote and sample it as a TPE mat: MOQ from 100 pcs, sampling in about '
       '7 days, the same printing, colour and packaging options.',
    p2='EVA on its own we run for the accessory half of the order \u2014 high-density blocks and '
       'softer rollers, colour-matched to the mats. If your brief specifies EVA and you also want '
       'the TPE technical sheet, just ask and we send both.',
    q1='Do you make EVA yoga mats?',
    a1='Yes. In this trade an EVA yoga mat is how many buyers and studios ask for the TPE mat, so '
       'that is what we quote and sample: closed-cell TPE, MOQ from 100 pcs, samples in about '
       '7 days. Our EVA-specific production is the accessory range \u2014 blocks and soft rollers.',
    q2='Is an EVA yoga mat the same as a TPE yoga mat?',
    a2='In this trade the two names are used for the same mat. EVA and TPE are different polymers, '
       'so our technical sheet states TPE \u2014 but an enquiry written as EVA yoga mat is quoted and '
       'sampled as our TPE mat, at the same MOQ and in the same price band.',
    zh_eyebrow='EVA 还是 TPE？',
    zh_h2='在找 EVA 瑜伽垫？',
    zh_p1='在这个行业里，这两个叫法指的就是同一张垫子。采购商、瑜伽馆和进口商常常开口就要'
          '\u201cEVA 瑜伽垫\u201d，而他们真正要的，正是我们用 TPE 生产的闭孔发泡垫——同一个产品，'
          '两个名字都能报。所以询盘以 EVA 名义进来时，我们就按 TPE 垫报价、打样：100 片起订、'
          '约 7 天出样，印刷、颜色和包装选项完全相同。',
    zh_p2='EVA 本身，我们用它做订单里配件的那一半——高密度瑜伽砖与偏软的泡沫轴，与垫子同色系。'
          '如果规格书上写的是 EVA，而你也想要 TPE 的技术资料，说一声，两份都发。',
    zh_q1='你们做 EVA 瑜伽垫吗？',
    zh_a1='做。这个行业里，很多采购商和瑜伽馆就是用\u201cEVA 瑜伽垫\u201d来指 TPE 垫，所以我们按 TPE '
           '报价、打样：闭孔 TPE，100 片起订，约 7 天出样。EVA 专线生产的是配件系列——瑜伽砖与'
           '软质泡沫轴。',
    zh_q2='EVA 瑜伽垫和 TPE 瑜伽垫是同一种吗？',
    zh_a2='在这个行业里，这两个叫法指的是同一张垫子。EVA 与 TPE 是两种不同的聚合物，所以我们的'
           '技术资料上写的是 TPE；但以 EVA 瑜伽垫名义发来的询盘，我们按 TPE 垫报价、打样，'
           '起订量与价格带完全一样。',
    desc_old='TPE Yoga Mats Eco TPE \u00b7 Single &amp; Double Layer \u00b7 61\u201390 cm. '
             'Factory-direct OEM/ODM from SANFAN: custom size, colour, logo and packaging, '
             'MOQ 100 pcs, sampling in 7 days.',
    desc_new='TPE Yoga Mats Eco closed-cell foam \u00b7 61\u201390 cm, also quoted as EVA yoga mats. '
             'OEM/ODM from SANFAN: custom size, colour, logo, packaging. MOQ 100 pcs.',
    # v2（2026-09-24 二轮）：整条重写为「目标值」模式，不再靠旧锚点插入子句。
    # 原因：语言版 v1 是在 "61–90 cm." 后插子句，宽度从 159–262 涨到 199–306，
    #     而 desc 预算只有 155 宽 —— v1 属于「修好一处、弄坏一处」。
    # v2 统一结构：主词 + EVA 叫法前置 + OEM/ODM 定制 + MOQ + 打样，全部 ≤155 宽。
    desc_target='TPE Yoga Mats closed-cell foam, also quoted as EVA yoga mats. OEM/ODM from SANFAN: '
                'custom size, colour, logo, packaging. MOQ 100 pcs, samples in 7 days.',
    mat_old='Blocks, soft rollers, props \u2014 the accessory half of the order',
    mat_new='Blocks, soft rollers, props \u2014 its own line. Mats ordered under the EVA name are '
            'supplied as TPE.',
    mat_zh_old='瑜伽砖、软质泡沫轴、辅具 —— 订单里的配件那一半',
    mat_zh_new='瑜伽砖、软质泡沫轴、辅具 —— 这是 EVA 自己的产线。以 EVA 名义下的垫，按 TPE 供货。',
)

L = {
    'de': dict(
        eyebrow='EVA oder TPE?',
        h2='Sie suchen eine EVA-Yogamatte?',
        p1='In dieser Branche stehen beide Namen f\u00fcr dieselbe Matte. Eink\u00e4ufer, Studios und '
           'Importeure fragen routinem\u00e4\u00dfig nach einer \u201eEVA-Yogamatte\u201c, wenn sie die '
           'gesch\u00e4umte Matte mit geschlossenen Zellen meinen, die wir aus TPE fertigen \u2013 '
           'dasselbe Produkt, unter beiden Bezeichnungen angeboten. Kommt Ihre Anfrage also als EVA '
           'herein, kalkulieren und bemustern wir sie als TPE-Matte: Mindestbestellmenge ab 100 '
           'St\u00fcck, Muster in rund 7 Tagen, dieselben Druck-, Farb- und Verpackungsoptionen.',
        p2='EVA selbst setzen wir f\u00fcr die Zubeh\u00f6rh\u00e4lfte der Bestellung ein \u2013 dichtere '
           'Bl\u00f6cke und weichere Rollen, farblich auf die Matten abgestimmt. Wenn in Ihrer Anfrage '
           'EVA steht und Sie zus\u00e4tzlich das TPE-Datenblatt brauchen, sagen Sie einfach Bescheid '
           '\u2013 wir schicken beides.',
        q1='Stellen Sie auch EVA-Yogamatten her?',
        a1='Ja. In dieser Branche fragen viele Eink\u00e4ufer und Studios mit \u201eEVA-Yogamatte\u201c genau '
           'die TPE-Matte an, und die kalkulieren und bemustern wir dann: TPE mit geschlossenen '
           'Zellen, Mindestbestellmenge ab 100 St\u00fcck, Muster in rund 7 Tagen. Unsere EVA-eigene '
           'Produktion ist die Zubeh\u00f6rreihe \u2013 Bl\u00f6cke und weiche Rollen.',
        q2='Ist eine EVA-Yogamatte dasselbe wie eine TPE-Yogamatte?',
        a2='In dieser Branche stehen beide Namen f\u00fcr dieselbe Matte. EVA und TPE sind '
           'unterschiedliche Polymere, deshalb steht im technischen Datenblatt TPE \u2013 eine als '
           'EVA-Yogamatte formulierte Anfrage wird aber als unsere TPE-Matte kalkuliert und '
           'bemustert, bei gleicher Mindestbestellmenge und in derselben Preisklasse.',
        desc_sep_old='61\u201390 cm.',
        desc_sep_new='61\u201390 cm, auch als EVA-Yogamatten angefragt.',
        desc_target='TPE Yoga-Matten, auch als EVA-Yogamatten angefragt. OEM/ODM ab Werk bei SANFAN: '
                    'Größe, Farbe, Logo, Verpackung. MOQ 100 Stück, Muster in 7 Tagen.',
        mat_old='Bl\u00f6cke, weiche Rollen, St\u00fctzen \u2013 die Zubeh\u00f6rh\u00e4lfte der Bestellung',
        mat_new='Bl\u00f6cke, weiche Rollen, St\u00fctzen \u2013 eine eigene Reihe. Unter dem Namen EVA '
                'bestellte Matten werden als TPE geliefert.',
    ),
    'ja': dict(
        eyebrow='EVA か TPE か',
        h2='EVA ヨガマットをお探しですか？',
        p1='この業界では、この二つの呼び名は同じマットを指します。バイヤー、スタジオ、輸入業者が'
           '「EVA ヨガマット」と発注するとき、実際に必要としているのは当社が TPE で製造している'
           '独立気泡の発泡マットです。同じ製品を、どちらの呼び名でもお見積りします。ですから '
           'EVA としてお問い合わせが届いた場合も、TPE マットとしてお見積り・サンプル制作いたします。'
           'MOQ 100 枚から、サンプルは約 7 日、印刷・カラー・包装のオプションも同一です。',
        p2='EVA そのものは、ご注文のうち付属品側に使用しています。高密度のヨガブロックと、'
           'やや柔らかいフォームローラーで、マットと同系色に仕上げます。仕様書が EVA 表記で、'
           'TPE の技術資料も必要な場合はお申し付けください。両方お送りします。',
        q1='EVA ヨガマットは作っていますか？',
        a1='はい。この業界では、多くのバイヤーやスタジオが TPE マットを指して「EVA ヨガマット」と'
           '発注します。当社はそれを TPE マットとしてお見積り・サンプル制作します。独立気泡 TPE、'
           'MOQ 100 枚から、サンプルは約 7 日です。EVA 専用の生産は付属品シリーズ、すなわち'
           'ヨガブロックと柔らかいフォームローラーです。',
        q2='EVA ヨガマットと TPE ヨガマットは同じものですか？',
        a2='この業界では、この二つの呼び名は同じマットを指します。EVA と TPE は異なるポリマーですので、'
           '技術資料には TPE と記載します。ただし EVA ヨガマットとして届いたお問い合わせは、'
           '当社の TPE マットとして、同じ MOQ・同じ価格帯でお見積り・サンプル制作いたします。',
        desc_sep_old='61\u201390 cm\u3002',
        desc_sep_new='61\u201390 cm\u3002EVA ヨガマットとしてもお問い合わせいただけます\u3002',
        desc_target='TPE ヨガマット、EVA ヨガマットとしてもお問い合わせ可。'
                    'SANFAN 工場直販 OEM/ODM：サイズ・色・ロゴ・梱包はカスタム対応、'
                    'MOQ 100 個、7 日でサンプル提供。',
        mat_old='ブロック、ソフトローラー、小道具\u2015\u2015注文の半分を占める付属品',
        mat_new='ブロック、ソフトローラー、小道具――EVA 独自のライン。EVA 名義で発注されたマットは '
                'TPE として供給されます。',
    ),
    'ko': dict(
        eyebrow='EVA일까 TPE일까',
        h2='EVA 요가 매트를 찾고 계신가요?',
        p1='이 업계에서 두 이름은 같은 매트를 가리킵니다. 바이어, 스튜디오, 수입업체는 \u201cEVA 요가 '
           '매트\u201d를 요청하지만, 실제로 필요한 것은 저희가 TPE로 생산하는 독립 기포 발포 매트입니다. '
           '같은 제품을 어느 이름으로든 견적 드립니다. 따라서 문의가 EVA로 들어와도 TPE 매트로 '
           '견적하고 샘플을 제작합니다. MOQ 100개부터, 샘플은 약 7일, 인쇄·색상·포장 옵션도 '
           '동일합니다.',
        p2='EVA 자체는 주문의 액세서리 절반에 사용합니다. 고밀도 요가 블록과 조금 더 부드러운 '
           '폼롤러이며, 매트와 같은 색 계열로 맞춥니다. 사양서에 EVA로 적혀 있고 TPE 기술 자료도 '
           '필요하시면 말씀해 주세요. 두 가지 모두 보내드립니다.',
        q1='EVA 요가 매트도 만드나요?',
        a1='네. 이 업계에서는 많은 바이어와 스튜디오가 TPE 매트를 가리켜 \u201cEVA 요가 매트\u201d로 '
           '문의합니다. 저희는 이를 TPE 매트로 견적하고 샘플을 제작합니다. 독립 기포 TPE, '
           'MOQ 100개부터, 샘플은 약 7일입니다. EVA 전용 생산은 액세서리 라인인 요가 블록과 '
           '부드러운 폼롤러입니다.',
        q2='EVA 요가 매트와 TPE 요가 매트는 같은 것인가요?',
        a2='이 업계에서 두 이름은 같은 매트를 가리킵니다. EVA와 TPE는 서로 다른 폴리머이므로 '
           '기술 자료에는 TPE로 표기합니다. 다만 EVA 요가 매트로 들어온 문의는 저희 TPE 매트로, '
           '같은 MOQ와 같은 가격대에서 견적하고 샘플을 제작합니다.',
        desc_sep_old='61\u201390 cm.',
        desc_sep_new='61\u201390 cm. EVA 요가 매트로도 문의하실 수 있습니다.',
        desc_target='TPE 요가 매트, EVA 요가 매트로도 문의 가능. '
                    'SANFAN 공장 직판 OEM/ODM: 크기·색상·로고·포장 맞춤, MOQ 100개, 7일 내 샘플 제공.',
        mat_old='블록, 부드러운 롤러, 소품 등 \u2014 주문의 액세서리 부분',
        mat_new='블록, 부드러운 롤러, 소품 등 \u2014 EVA 자체 라인. EVA 명의로 주문된 매트는 TPE로 '
                '공급됩니다.',
    ),
    'fr': dict(
        eyebrow='EVA ou TPE ?',
        h2='Vous cherchez un tapis de yoga EVA ?',
        p1='Dans ce m\u00e9tier, les deux noms d\u00e9signent le m\u00eame tapis. Les acheteurs, les studios '
           'et les importateurs demandent couramment un \u00ab tapis de yoga EVA \u00bb alors que ce dont '
           'ils ont besoin est le tapis en mousse \u00e0 cellules ferm\u00e9es que nous produisons en TPE '
           '\u2014 le m\u00eame produit, chiffr\u00e9 sous l\u2019un ou l\u2019autre terme. Quand votre demande '
           'arrive sous l\u2019appellation EVA, nous la chiffrons et la proposons en \u00e9chantillon comme '
           'un tapis TPE : \u00e0 partir de 100 pi\u00e8ces, \u00e9chantillons en 7 jours environ, avec les '
           'm\u00eames options d\u2019impression, de couleur et d\u2019emballage.',
        p2='L\u2019EVA proprement dit, nous l\u2019utilisons pour la moiti\u00e9 accessoires de la commande : '
           'briques haute densit\u00e9 et rouleaux plus souples, assortis aux couleurs des tapis. Si votre '
           'cahier des charges mentionne l\u2019EVA et que vous souhaitez aussi la fiche technique TPE, '
           'demandez-la : nous envoyons les deux.',
        q1='Fabriquez-vous aussi des tapis de yoga EVA ?',
        a1='Oui. Dans ce m\u00e9tier, beaucoup d\u2019acheteurs et de studios d\u00e9signent le tapis TPE en '
           'demandant un \u00ab tapis de yoga EVA \u00bb ; c\u2019est donc ce que nous chiffrons et '
           '\u00e9chantillonnons : TPE \u00e0 cellules ferm\u00e9es, \u00e0 partir de 100 pi\u00e8ces, '
           '\u00e9chantillons en 7 jours environ. Notre production sp\u00e9cifiquement EVA, ce sont les '
           'accessoires : briques et rouleaux souples.',
        q2='Un tapis de yoga EVA est-il identique \u00e0 un tapis de yoga TPE ?',
        a2='Dans ce m\u00e9tier, les deux noms d\u00e9signent le m\u00eame tapis. L\u2019EVA et le TPE sont '
           'deux polym\u00e8res diff\u00e9rents : notre fiche technique indique donc TPE. Mais une demande '
           'formul\u00e9e comme tapis de yoga EVA est chiffr\u00e9e et propos\u00e9e en \u00e9chantillon '
           'comme notre tapis TPE, \u00e0 quantit\u00e9 minimale et dans la m\u00eame gamme de prix.',
        desc_sep_old='61\u201390 cm.',
        desc_sep_new='61\u201390 cm, \u00e9galement demand\u00e9s comme tapis de yoga EVA.',
        desc_target="Tapis de yoga TPE, aussi demandés comme tapis EVA. OEM/ODM d'usine : "
                    'couleurs, logo, emballage sur mesure, QMC 100 pièces, échantillons sous 7 jours.',
        mat_old='Blocs, rouleaux souples, supports\u2026 la partie \u00ab accessoires \u00bb de la commande',
        mat_new='Blocs, rouleaux souples, supports\u2026 une gamme \u00e0 part. Les tapis command\u00e9s '
                'sous le nom EVA sont fournis en TPE.',
    ),
    'it': dict(
        eyebrow='EVA o TPE?',
        h2='Cerchi un tappetino da yoga EVA?',
        p1='In questo settore i due nomi indicano lo stesso tappetino. Acquirenti, studi e importatori '
           'chiedono abitualmente un \u201ctappetino da yoga EVA\u201d quando ci\u00f2 di cui hanno bisogno '
           '\u00e8 il tappetino in schiuma a celle chiuse che produciamo in TPE: lo stesso prodotto, '
           'quotato con l\u2019una o l\u2019altra parola. Quando quindi la richiesta arriva come EVA, la '
           'quotiamo e la campioniamo come tappetino TPE: da 100 pezzi, campioni in circa 7 giorni, con '
           'le stesse opzioni di stampa, colore e imballaggio.',
        p2='L\u2019EVA in s\u00e9 lo usiamo per la met\u00e0 accessori dell\u2019ordine: blocchi ad alta '
           'densit\u00e0 e rulli pi\u00f9 morbidi, abbinati ai colori dei tappetini. Se il capitolato '
           'indica EVA e serve anche la scheda tecnica TPE, basta chiedere: inviamo entrambe.',
        q1='Producete anche tappetini da yoga EVA?',
        a1='S\u00ec. In questo settore molti acquirenti e studi indicano il tappetino TPE chiedendo un '
           '\u201ctappetino da yoga EVA\u201d: \u00e8 quindi quello che quotiamo e campioniamo. TPE a '
           'celle chiuse, da 100 pezzi, campioni in circa 7 giorni. La nostra produzione specifica in '
           'EVA \u00e8 la linea accessori: blocchi e rulli morbidi.',
        q2='Un tappetino da yoga EVA \u00e8 uguale a un tappetino da yoga TPE?',
        a2='In questo settore i due nomi indicano lo stesso tappetino. EVA e TPE sono polimeri diversi, '
           'perci\u00f2 la scheda tecnica riporta TPE. Una richiesta formulata come tappetino da yoga EVA '
           'viene per\u00f2 quotata e campionata come il nostro tappetino TPE, con lo stesso MOQ e nella '
           'stessa fascia di prezzo.',
        desc_sep_old='61\u201390 cm.',
        desc_sep_new='61\u201390 cm, richiesti anche come tappetini da yoga EVA.',
        desc_target='Tappetini da yoga TPE, richiesti anche come tappetini EVA. '
                    'OEM/ODM di fabbrica: colori, logo, confezione su misura, '
                    'MOQ 100 pezzi, campioni in 7 giorni.',
        mat_old='Blocchi, rulli morbidi, puntelli: la parte degli accessori dell\u2019ordine',
        mat_new='Blocchi, rulli morbidi, puntelli: una linea a s\u00e9. I tappetini ordinati con il nome '
                'EVA vengono forniti in TPE.',
    ),
    'es': dict(
        eyebrow='\u00bfEVA o TPE?',
        h2='\u00bfBusca una esterilla de yoga EVA?',
        p1='En este sector los dos nombres designan la misma esterilla. Los compradores, los estudios y '
           'los importadores piden habitualmente una \u00abesterilla de yoga EVA\u00bb cuando lo que '
           'necesitan es la esterilla de espuma de c\u00e9lula cerrada que producimos en TPE: el mismo '
           'producto, cotizado con cualquiera de las dos palabras. As\u00ed que cuando su consulta llega '
           'como EVA, la cotizamos y preparamos muestras como esterilla TPE: desde 100 unidades, '
           'muestras en unos 7 d\u00edas, con las mismas opciones de impresi\u00f3n, color y embalaje.',
        p2='El EVA en s\u00ed lo usamos para la mitad de accesorios del pedido: bloques de alta densidad '
           'y rodillos m\u00e1s blandos, a juego con los colores de las esterillas. Si su pliego '
           'especifica EVA y adem\u00e1s necesita la ficha t\u00e9cnica del TPE, solo tiene que pedirla: '
           'le enviamos las dos.',
        q1='\u00bfTambi\u00e9n fabrican esterillas de yoga EVA?',
        a1='S\u00ed. En este sector muchos compradores y estudios se refieren a la esterilla de TPE '
           'pidiendo una \u00abesterilla de yoga EVA\u00bb, as\u00ed que eso es lo que cotizamos y para lo '
           'que preparamos muestras: TPE de c\u00e9lula cerrada, desde 100 unidades, muestras en unos '
           '7 d\u00edas. Nuestra producci\u00f3n espec\u00edfica en EVA es la l\u00ednea de accesorios: '
           'bloques y rodillos blandos.',
        q2='\u00bfUna esterilla de yoga EVA es lo mismo que una esterilla de yoga TPE?',
        a2='En este sector los dos nombres designan la misma esterilla. El EVA y el TPE son pol\u00edmeros '
           'distintos, por eso nuestra ficha t\u00e9cnica indica TPE; pero una consulta redactada como '
           'esterilla de yoga EVA se cotiza y se atiende con muestras como nuestra esterilla TPE, con '
           'el mismo pedido m\u00ednimo y en la misma franja de precio.',
        desc_sep_old='61\u201390 cm.',
        desc_sep_new='61\u201390 cm, tambi\u00e9n solicitadas como esterillas de yoga EVA.',
        desc_target='Esterillas de yoga TPE, también solicitadas como esterillas EVA. '
                    'OEM/ODM de fábrica: color, logo y embalaje a medida, '
                    'MOQ 100 uds., muestras en 7 días.',
        mat_old='Bloques, rodillos blandos, puntales\u2026 la parte de los accesorios del pedido',
        mat_new='Bloques, rodillos blandos, puntales\u2026 una l\u00ednea propia. Las esterillas pedidas '
                'con el nombre EVA se suministran en TPE.',
    ),
}

# ---------------------------------------------------------------- 构造


def esc(s):
    return html.escape(s, quote=False)


def sp(en, zh):
    return '<span class="lang-en">%s</span><span class="lang-zh">%s</span>' % (esc(en), esc(zh))


def build_section(lg):
    """lg='en' 走配对 span；其余语言用纯文本。"""
    c = EN if lg == 'en' else L[lg]
    if lg == 'en':
        eb, h2 = sp(EN['eyebrow'], EN['zh_eyebrow']), sp(EN['h2'], EN['zh_h2'])
        p1, p2 = sp(EN['p1'], EN['zh_p1']), sp(EN['p2'], EN['zh_p2'])
        items = [(sp(EN['q1'], EN['zh_q1']), sp(EN['a1'], EN['zh_a1'])),
                 (sp(EN['q2'], EN['zh_q2']), sp(EN['a2'], EN['zh_a2']))]
    else:
        eb, h2 = esc(c['eyebrow']), esc(c['h2'])
        p1, p2 = esc(c['p1']), esc(c['p2'])
        items = [(esc(c['q1']), esc(c['a1'])), (esc(c['q2']), esc(c['a2']))]

    out = ['  <section class="section">\n',
           '    <div class="container">\n',
           '      <div class="section-head">\n',
           '        <div class="eyebrow">%s</div>\n' % eb,
           '        <h2>%s</h2>\n' % h2,
           '      </div>\n',
           '      <div style="max-width:820px;margin:0 auto;">\n',
           '        <p>%s</p>\n' % p1,
           '        <p>%s</p>\n' % p2,
           '      </div>\n',
           '      <div class="faq-list" style="margin-top:30px;">\n']
    for q, a in items:
        out.append('        <details class="faq-item">\n')
        out.append('          <summary>%s</summary>\n' % q)
        out.append('          <div class="faq-a">%s</div>\n' % a)
        out.append('        </details>\n')
    out.append('      </div>\n')
    out.append('    </div>\n')
    out.append('  </section>\n')
    return ''.join(out)


def build_ld(lg, canonical):
    """站内主流 FAQPage 形态：@id + inLanguage（328 个既有块都带，本轮 v1 漏了）。

    ⚠️ 不加 isPartOf —— 产品页的 FAQPage 指向 `<canonical>#webpage`，但分类页的
       @graph 里没有 WebPage 节点（只有 BreadcrumbList / CollectionPage / ItemList /
       Organization），照抄会得到一个指向不存在节点的悬空引用，比不写更糟。
    """
    c = EN if lg == 'en' else L[lg]
    if lg == 'en':
        qs = [(EN['q1'], EN['a1']), (EN['q2'], EN['a2'])]
    else:
        qs = [(c['q1'], c['a1']), (c['q2'], c['a2'])]
    doc = {
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        '@id': canonical + '#faq',
        'inLanguage': lg,
        'mainEntity': [
            {'@type': 'Question', 'name': q,
             'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in qs
        ],
    }
    body = json.dumps(doc, ensure_ascii=False, indent=2)
    body = '\n'.join('  ' + ln if ln.strip() else ln for ln in body.split('\n'))
    return ('\n  %s\n  <script type="application/ld+json">\n%s\n  </script>\n  %s' % (LD_A, body, LD_B))


# ---------------------------------------------------------------- 各页补丁


def strip_all(t):
    t = RE_NOTE.sub('', t)
    t = RE_LD.sub('', t)
    return t


def patch_tpe(t, lg):
    """返回 (新文本, 说明列表)。"""
    notes = []
    t = strip_all(t)
    clean = t

    # ① 新增小节
    assert t.count(CTA_ANCHOR) == 1, '%s：CTA 锚点不唯一(%d)' % (lg, t.count(CTA_ANCHOR))
    i = t.index(CTA_ANCHOR)
    ins = MARK_A + '\n' + build_section(lg) + MARK_B + '\n\n'
    # ⚠️ CTA 前面的两个空格属于它的缩进，必须一起还原，否则回退断言与页面缩进都会错。
    t2 = t[:i] + '\n  </section>\n\n' + ins + '  ' + CTA + t[i + len(CTA_ANCHOR):]
    assert t2.replace(ins, '', 1) == clean, '%s：小节回退不一致' % lg
    notes.append('小节')
    t = t2

    # ② 追加 FAQPage JSON-LD
    # ⚠️ 位置必须在 `<!-- orgref:v1 -->` **之前**（= 实体层标记之外）：
    #    ① 站内 328 个既有 FAQPage（产品页/pilates）实测都在标记之前，跟随惯例；
    #    ② `add_org_sameas_20260924.py` 是「先 STRIP 剥离整个标记区间、再重新追加」的写法，
    #       落在区间内的内容会被静默丢掉（v1 就放错了，跑一次实体脚本这 7 个 FAQPage 就没了）；
    #    ③ 放标记之前还能让那个脚本完全幂等 —— 剥离后我们的块成为「最后一个 ld+json」，
    #       重建时区间正好追加回它后面，位置不漂移。
    cm = re.search(r'<link rel="canonical" href="([^"]+)"', t)
    assert cm, '%s：找不到 canonical，无法拼 FAQPage @id' % lg
    canonical = cm.group(1)
    if ORG_MARK in t:
        # ⚠️ 插入点是标记**前面那个换行**处，不是标记本身处 —— 摘块正则吃的是
        #    `\n[ \t]*LD_A…LD_B`（一个换行 + 缩进），所以插入必须复用原位换行，
        #    自己再加一个 `\n` 就会每跑一次多一行空行（不幂等，实测踩过）。
        i = t.index(ORG_MARK)
        j = t.rindex('\n', 0, i)
        assert t[j + 1:i].strip() == '', '%s：实体标记前不是干净的换行' % lg
        pos = j
        ins2 = build_ld(lg, canonical)
    else:
        blocks = list(RE_LDJSON.finditer(t))
        assert blocks, '%s：找不到 ld+json 块' % lg
        pos = blocks[-1].end()
        ins2 = build_ld(lg, canonical)
    t2 = t[:pos] + ins2 + t[pos:]
    assert t2.replace(ins2, '', 1) == t, '%s：JSON-LD 回退不一致' % lg
    notes.append('FAQPage')
    t = t2

    # ③ description：整条重写为目标值（meta + og + twitter 三处同串）
    # ⚠️ v1 是「在 61–90 cm. 后插子句」，锚点补过后仍是子串 → 二次跑判断会失准；
    #    而 v1 的子句插入把语言版宽度推到 199–306（预算 155），所以 v2 直接换整条，
    #    幂等判据也简化成「当前串 == 目标串」。
    target = EN['desc_target'] if lg == 'en' else L[lg]['desc_target']
    m = re.search(r'<meta name="description" content="([^"]*)"', t)
    assert m, '%s：找不到 description' % lg
    old = m.group(1)
    if old == target:
        notes.append('描述已是目标')
    else:
        cnt = t.count(old)
        assert cnt == 3, '%s：描述串出现 %d 次（应 3，meta/og/twitter 应同串）' % (lg, cnt)
        t = t.replace(old, target)
        notes.append('描述×3 重写')

    # ④ JSON-LD 里还有第 4 份描述：@graph 的 CollectionPage.description
    # ⚠️ 它跟 meta 那份**不是同一个串**（HTML 里 `&amp;` 是转义的、JSON-LD 里是裸 `&`），
    #    所以 ③ 的「三处同串」替换碰不到它 —— 漏掉就会出现「页面有两套描述」，
    #    而 Google/AI 取结构化数据时拿到的正是没带 EVA 的那份（v1 就漏了）。
    i = t.find('"@type": "CollectionPage"')
    if i >= 0:
        md = re.compile(r'"description":\s*"([^"]*)"').search(t, i)
        assert md, '%s：CollectionPage 里找不到 description' % lg
        cur = md.group(1)
        if cur == target:
            notes.append('LD 描述已是目标')
        else:
            t = t[:md.start(1)] + target + t[md.end(1):]
            notes.append('LD 描述')
    return t, notes


def patch_materials(t, lg):
    """只改 EVA 行「最适合」格（第 6 个 td）的文字，标签结构不动。"""
    rows = list(re.finditer(r'<tr>[\s\S]*?</tr>', t))
    row = None
    for r in rows:
        if re.match(r'<tr>\s*<th[^>]*>\s*<span[^>]*>EVA<', r.group(0)):
            row = r
            break
    assert row is not None, '%s：找不到 EVA 行' % lg
    tds = list(re.finditer(r'<td>([\s\S]*?)</td>', row.group(0)))
    assert len(tds) == 8, '%s：EVA 行 td 数 %d（应 8）' % (lg, len(tds))
    cell = tds[5]
    inner = cell.group(1)

    def text_of(h):
        return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', h)).strip()

    if lg == 'en':
        # EN 页该格是双 span（lang-en + lang-zh），必须**逐 span** 比对：
        # 把标签剥掉后整格比对，会得到「英文+中文」拼接出来的假现状。
        spans = list(re.finditer(r'<span[^>]*>([\s\S]*?)</span>', inner))
        cur = [text_of(s.group(1)) for s in spans]
        olds = [EN['mat_old'], EN['mat_zh_old']]
        news = [EN['mat_new'], EN['mat_zh_new']]
    else:
        cur = [text_of(inner)]
        olds = [L[lg]['mat_old']]
        news = [L[lg]['mat_new']]

    if cur == news:
        return t, ['材质行已是目标']
    assert cur == olds, '%s：材质行现状与预期不符\n  实际 %r\n  预期 %r' % (lg, cur, olds)

    new_td = inner
    for o, n in zip(olds, news):
        assert o in new_td, '%s：格内找不到 %r' % (lg, o[:40])
        new_td = new_td.replace(o, n, 1)
    t2 = t[:row.start() + cell.start(1)] + new_td + t[row.start() + cell.end(1):]
    # ⚠️ 这里是「替换」不是「插入」：回退断言必须用旧值还原，写成 replace(new,'') 会把整格删空，
    #    断言恒假（踩过一次）。
    assert t2.replace(new_td, inner, 1) == t, '%s：材质行回退不一致' % lg
    return t2, ['材质行']


# ---------------------------------------------------------------- 主流程


def disp_w(s):
    """Google 按像素截断 ≈ 显示宽度：CJK 记 2、其余记 1。"""
    return sum(2 if ord(c) > 0x2E80 else 1 for c in s.replace('&amp;', '&'))


def check_desc_widths():
    """把「description ≤ 155 显示宽」+「转化信息齐全」写进脚本自检。

    v1 的教训：肉眼看着不长，按宽度语言版已到 199–306（预算 155），
    而「描述是否超长」跟「是否有 EVA 关键词」是两个独立目标 —— 只顾后者会弄坏前者。
    ⚠️ 起订量在各语言里不必都是 MOQ 字面（法语版全站惯用 QMC），所以按语言校验词干，
       不能写死 'MOQ' —— 写死会把合法的本地化写法判成缺陷。
    """
    keep = {
        'en': ('MOQ', 'samples'),
        'de': ('MOQ', 'Muster'),
        'ja': ('MOQ', 'サンプル'),
        'ko': ('MOQ', '샘플'),
        'fr': ('QMC', 'échantillon'),
        'it': ('MOQ', 'campioni'),
        'es': ('MOQ', 'muestra'),
    }
    items = [('en', EN['desc_target'])] + [(k, L[k]['desc_target']) for k in LANGS]
    out = []
    for lg, tgt in items:
        for need in ('EVA', 'OEM/ODM') + keep[lg]:
            assert need in tgt, '%s：描述缺 %s' % (lg, need)
        out.append((lg, disp_w(tgt)))
    bad = ['%s=%d' % (lg, n) for lg, n in out if n > 155]
    assert not bad, '描述超 155 显示宽：' + ', '.join(bad)
    return out


def main():
    widths = check_desc_widths()
    print('描述宽度自检（预算 155）：' + '  '.join('%s %d' % (lg, n) for lg, n in widths))
    print()
    plan = [(TPE, 'en', patch_tpe)]
    for lg in LANGS:
        plan.append((lg + '/' + TPE, lg, patch_tpe))
    plan.append((MAT, 'en', patch_materials))
    for lg in LANGS:
        plan.append((lg + '/' + MAT, lg, patch_materials))

    changed = skipped = 0
    for rel, lg, fn in plan:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            print('  缺文件 %s' % rel)
            continue
        t = open(p, encoding='utf-8').read()
        new, notes = fn(t, lg)
        if new == t:
            print('  %-46s 已是目标状态' % rel)
            skipped += 1
            continue
        # 幂等自检：再跑一次必须等于本次结果
        again, _ = fn(new, lg)
        assert again == new, '%s：不幂等' % rel
        if not DRY:
            open(p, 'w', encoding='utf-8').write(new)
        print('  %-46s +%d 字节  [%s]' % (rel, len(new) - len(t), '/'.join(notes)))
        changed += 1

    print('\n%s：改动 %d 个文件，已达标 %d 个' % ('干跑' if DRY else '落盘', changed, skipped))


if __name__ == '__main__':
    main()
