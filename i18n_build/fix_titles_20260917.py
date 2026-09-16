#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""超长 title 收口（2026-09-17）

【判据：Google 从尾部截断，所以看「主体宽度」而不是总宽度】
`title_split.py` 已把 143 条 >60 的分成三档：
  · A 主体 ≥60 —— 截断发生在**正文中段**，句子被砍断，必须重写
  · B 主体 52-59 —— 只有品牌后缀被砍成 `— SANF`，**半截品牌**比没有更糟
  · C/D 主体 <52 —— 后缀基本完整可见，不动

【本轮的两种修法，各自可审计】
  · A 档：**人工重写**（下表逐条给出），压到「主体 ≤51」→ 加上 `— SANFAN` 仍 ≤60。
    重写原则：保关键词 + 保品牌，先砍副标题/年份/形容词堆叠，**不做机械截断**。
  · B 档：**去掉品牌后缀**（主体 52-59 本身就 ≤59，全显）。
    为什么不是「再压几字」：B 档 61 条要压 1–8 字，逐条改会引入 61 处主观编辑；
    而 `— SANF` 这种半截品牌在 SERP 上既难看又不提供品牌信息，去掉是净收益。
    ⚠️ 主体 ≤51 的（本就 ≤60）**保留**品牌，不动。

⚠️ 只改 `<title>`：og:title / twitter:title 不受搜索结果长度限制，另有更短写法，
   动它们没有收益却会扩大改动面。

用法：
    python3 fix_titles_20260917.py            # 干跑 + 终检
    python3 fix_titles_20260917.py --apply
"""
import argparse
import glob
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BUDGET = 60
BRAND = " — SANFAN"
SEP = r"(?:[—–|]|&#124;|&vert;|&#x7c;|&brvbar;)"

TITLE_RE = re.compile(r"<title>([\s\S]*?)</title>")
TAIL_RE = re.compile(r"([\s\S]*)\s+" + SEP + r"\s+([^<>—–|]*)$")


def W(s):
    return sum(2 if ord(c) > 0x2E80 else 1 for c in s)


def norm(s):
    """比较用归一：NBSP / NNBSP → 普通空格。

    ⚠️ 法语排版在 `:` `?` 前用**不换行空格 U+00A0**，而本表用普通空格写。
    `fr/blog/yoga-mat-materials.html` 就是这么被判「原串不符」的 ——
    只差一个 U+00A0，肉眼看完全一样。
    """
    return s.replace("\u00a0", " ").replace("\u202f", " ").strip()


def split_brand(raw):
    """返回 (主体原始串, 后缀原始串)。识别不出品牌则后缀为 None。"""
    m = TAIL_RE.match(raw)
    if m and "SANFAN" in html.unescape(m.group(2)).upper():
        return m.group(1).strip(), m.group(2).strip()
    return raw, None


# A 档人工重写：文件 → (原 title 原始串, 新 title)
TITLES = {
    # ---------------- EN ----------------
    "applications/home-online-sellers.html": (
        "Amazon &amp; E-commerce Yoga Fitness Supplier &#124; Low MOQ — SANFAN",
        "Amazon &amp; E-commerce Yoga Supplier | Low MOQ — SANFAN"),
    "blog/top-12-china-yoga-mat-manufacturers.html": (
        "Top 12 Yoga Mat Manufacturers in China (2026): Cluster Comparison — SANFAN",
        "Top 12 Yoga Mat Manufacturers in China (2026) — SANFAN"),
    "blog/yoga-mat-spec-guide.html": (
        "Yoga Mat Thickness & Size Guide: How to Specify a Mat (2026) — SANFAN",
        "Yoga Mat Thickness & Size Guide (2026) — SANFAN"),

    # ---------------- DE ----------------
    "de/applications/home-online-sellers.html": (
        "Amazon- und E-Commerce-Anbieter für Yoga- und Fitnessartikel | Geringe Mindestbestellmenge — SANFAN",
        "Yoga-Anbieter für Amazon &amp; E-Commerce | MOQ — SANFAN"),
    "de/applications/hotels-resorts-spas.html": (
        "Anbieter von Yogamatten für Hotels und Resorts | OEM mit individuellem Logo — SANFAN",
        "Yogamatten für Hotels &amp; Resorts | Logo-OEM — SANFAN"),
    "de/blog/compliance.html": (
        "REACH, CA Prop 65 &amp; 6P: Konformität von Yogamatten in den USA und der EU — SANFAN",
        "REACH, CA Prop 65 &amp; 6P für Yogamatten in USA &amp; EU — SANFAN"),
    "de/blog/custom-sizes.html": (
        "Leitfaden zu individuellen Größen und Stärken von Yogamatten — SANFAN",
        "Individuelle Yogamatten-Größen und -Stärken — SANFAN"),
    "de/blog/moq-explained.html": (
        "Erläuterung zur Mindestbestellmenge für Yogamatten: Wie niedrig kann sie sein? — SANFAN",
        "Mindestbestellmenge für Yogamatten: Wie niedrig? — SANFAN"),
    "de/blog/private-label-yoga-mats.html": (
        "Yoga-Matten unter Eigenmarke: Der umfassende Leitfaden für die Markteinführung (2026) — SANFAN",
        "Yogamatten unter Eigenmarke: Leitfaden (2026) — SANFAN"),
    "de/blog/top-12-china-yoga-mat-manufacturers.html": (
        "Die 12 führenden Hersteller von Yogamatten in China (2026): Cluster-Vergleich — SANFAN",
        "12 führende Yogamatten-Hersteller in China (2026) — SANFAN"),
    "de/blog/tpe-vs-pu.html": (
        "TPE Vergleich: PU-Yogamatten aus Gummi – Welche sollte man 2026 wählen? — SANFAN",
        "TPE vs. PU: Yogamatten aus Gummi im Vergleich — SANFAN"),
    "de/blog/yoga-mat-materials.html": (
        "Materialien für Yogamatten: TPE vs. NBR vs. PVC vs. Rubber (2026) — SANFAN",
        "Materialien für Yogamatten: TPE vs. NBR vs. PVC — SANFAN"),
    "de/blog/yoga-mat-spec-guide.html": (
        "Leitfaden zu Dicke und Größe von Yogamatten: So wählen Sie die richtige Matte aus (2026) — SANFAN",
        "Yogamatten: Dicke und Größe richtig wählen (2026) — SANFAN"),
    "de/products/navy-botanical-suede-tpe-yoga-mat.html": (
        "Yogamatte TPE aus marineblauem, pflanzlich behandeltem Wildleder — SANFAN",
        "Yogamatte TPE aus marineblauem Wildleder — SANFAN"),

    # ---------------- ES ----------------
    "es/applications/gyms-fitness-clubs.html": (
        "Fabricante de equipamiento para gimnasios y centros de fitness — SANFAN",
        "Equipamiento para gimnasios y centros de fitness — SANFAN"),
    "es/applications/home-online-sellers.html": (
        "Proveedor de productos de yoga y fitness para Amazon y el comercio electrónico | Cantidad mínima de pedido reducida — SANFAN",
        "Proveedor de yoga y fitness para Amazon | MOQ bajo — SANFAN"),
    "es/applications/hotels-resorts-spas.html": (
        "Proveedor de esterillas de yoga para hoteles y complejos turísticos | Fabricación OEM con logotipo personalizado — SANFAN",
        "Esterillas de yoga para hoteles y resorts | OEM — SANFAN"),
    "es/blog/compliance.html": (
        "REACH, CA Prop 65 y 6P: Cumplimiento normativo de las esterillas de yoga en EE. UU. y la UE — SANFAN",
        "REACH, CA Prop 65 y 6P para esterillas de yoga — SANFAN"),
    "es/blog/custom-sizes.html": (
        "Guía de tamaños y grosores personalizados de esterillas de yoga — SANFAN",
        "Tamaños y grosores de esterillas personalizados — SANFAN"),
    "es/blog/moq-explained.html": (
        "Explicación del pedido mínimo (MOQ) de esterillas de yoga: ¿hasta qué punto se puede reducir? — SANFAN",
        "MOQ de esterillas de yoga: ¿cuánto reducir? — SANFAN"),
    "es/blog/private-label-yoga-mats.html": (
        "Esterillas de yoga de marca propia: la guía completa para su lanzamiento (2026) — SANFAN",
        "Esterillas de yoga de marca propia: guía (2026) — SANFAN"),
    "es/blog/top-12-china-yoga-mat-manufacturers.html": (
        "Los 12 principales fabricantes de esterillas de yoga en China (2026): comparación por clústeres — SANFAN",
        "12 fabricantes de esterillas de yoga en China — SANFAN"),
    "es/blog/yoga-mat-materials.html": (
        "Materiales de las esterillas de yoga: TPE frente a NBR frente a PVC frente al caucho (2026) — SANFAN",
        "Materiales de esterillas de yoga: TPE, NBR, PVC — SANFAN"),
    "es/blog/yoga-mat-spec-guide.html": (
        "Guía sobre el grosor y el tamaño de las esterillas de yoga: cómo elegir una esterilla (2026) — SANFAN",
        "Grosor y tamaño de las esterillas de yoga (2026) — SANFAN"),
    "es/products/monochrome-leaf-suede-tpe-yoga-mat.html": (
        "Esterilla de yoga TPE de ante monocromático con motivos de hojas — SANFAN",
        "Esterilla de yoga TPE de ante monocromático — SANFAN"),
    "es/products/mulinsen-widened-anti-slip-tpe-mat-90cm.html": (
        "Esterilla antideslizante TPE de MuLinSen, de mayor tamaño 90cm — SANFAN",
        "Esterilla antideslizante MuLinSen TPE 90cm — SANFAN"),

    # ---------------- FR ----------------
    "fr/applications/gyms-fitness-clubs.html": (
        "Fabricant d'équipements pour salles de sport et clubs de fitness — SANFAN",
        "Équipements pour salles de sport et fitness — SANFAN"),
    "fr/applications/home-online-sellers.html": (
        "Fournisseur de produits de yoga et de fitness sur Amazon et dans le commerce en ligne | Faible quantité minimale de commande — SANFAN",
        "Fournisseur yoga &amp; fitness pour Amazon | MOQ bas — SANFAN"),
    "fr/applications/hotels-resorts-spas.html": (
        "Fournisseur de tapis de yoga pour hôtels et complexes touristiques | Fabrication sur mesure avec logo personnalisé — SANFAN",
        "Tapis de yoga pour hôtels et resorts | logo OEM — SANFAN"),
    "fr/applications/retail-private-label.html": (
        "Fabricant de produits de yoga et de fitness sous marque de distributeur — SANFAN",
        "Fabricant yoga &amp; fitness en marque de distributeur — SANFAN"),
    "fr/blog/7day-sampling.html": (
        "Échantillons de 7 jours pour les marques de yoga en marque de distributeur — SANFAN",
        "Échantillons 7 jours pour marques de yoga — SANFAN"),
    "fr/blog/compliance.html": (
        "REACH, CA Prop 65 et 6P : conformité des tapis de yoga aux normes américaines et européennes — SANFAN",
        "REACH, CA Prop 65 et 6P\u00a0: conformité des tapis — SANFAN"),
    "fr/blog/custom-sizes.html": (
        "Guide des dimensions et épaisseurs personnalisées des tapis de yoga — SANFAN",
        "Dimensions et épaisseurs de tapis de yoga — SANFAN"),
    "fr/blog/moq-explained.html": (
        "Tout savoir sur la quantité minimale de commande (MOQ) pour les tapis de yoga : jusqu'où peut-on descendre ? — SANFAN",
        "MOQ des tapis de yoga : jusqu'où descendre ? — SANFAN"),
    "fr/blog/private-label-yoga-mats.html": (
        "Tapis de yoga de marque de distributeur : le guide complet du lancement (2026) — SANFAN",
        "Tapis de yoga en marque de distributeur : guide — SANFAN"),
    "fr/blog/top-12-china-yoga-mat-manufacturers.html": (
        "Les 12 principaux fabricants de tapis de yoga en Chine (2026) : comparaison par pôles — SANFAN",
        "12 fabricants de tapis de yoga en Chine (2026) — SANFAN"),
    "fr/blog/tpe-vs-pu.html": (
        "TPE Tapis de yoga en caoutchouc vs PU : lequel choisir en 2026 — SANFAN",
        "Tapis de yoga PU vs TPE\u00a0: lequel choisir (2026) — SANFAN"),
    "fr/blog/yoga-mat-materials.html": (
        "Matériaux des tapis de yoga : TPE vs NBR vs PVC vs caoutchouc (2026) — SANFAN",
        "Matériaux des tapis de yoga\u00a0: TPE, NBR, PVC — SANFAN"),    "fr/blog/yoga-mat-spec-guide.html": (
        "Guide sur l'épaisseur et les dimensions des tapis de yoga : comment choisir son tapis (2026) — SANFAN",
        "Épaisseur et dimensions des tapis de yoga (2026) — SANFAN"),
    "fr/products/flamingo-print-suede-rubber-yoga-mat.html": (
        "Tapis de yoga en daim et caoutchouc avec motif de flamant rose — SANFAN",
        "Tapis de yoga daim et caoutchouc motif flamant — SANFAN"),
    "fr/products/mulinsen-widened-anti-slip-tpe-mat-90cm.html": (
        "Tapis de yoga antidérapant MuLinSen TPE en version élargie 90cm — SANFAN",
        "Tapis de yoga antidérapant MuLinSen TPE 90cm — SANFAN"),

    # ---------------- IT ----------------
    "it/applications/home-online-sellers.html": (
        "Fornitore di articoli per lo yoga e il fitness su Amazon e nell'e-commerce | Quantità minima d'ordine (MOQ) ridotta — SANFAN",
        "Fornitore yoga e fitness per Amazon | MOQ basso — SANFAN"),
    "it/applications/hotels-resorts-spas.html": (
        "Fornitore di tappetini da yoga per hotel e resort | OEM con logo personalizzato — SANFAN",
        "Tappetini da yoga per hotel e resort | logo OEM — SANFAN"),
    "it/applications/retail-private-label.html": (
        "Produttore di articoli per lo yoga e il fitness con marchio privato — SANFAN",
        "Produttore yoga e fitness con marchio privato — SANFAN"),
    "it/blog/7day-sampling.html": (
        "Pacchetto di prova di 7 giorni per marchi di yoga con marchio proprio — SANFAN",
        "Campioni in 7 giorni per marchi yoga — SANFAN"),
    "it/blog/compliance.html": (
        "REACH, CA Prop 65 e 6P: Conformità dei tappetini da yoga per gli Stati Uniti e l'Unione Europea — SANFAN",
        "REACH, CA Prop 65 e 6P: conformità dei tappetini — SANFAN"),
    "it/blog/custom-sizes.html": (
        "Guida alle dimensioni e agli spessori personalizzati dei tappetini da yoga — SANFAN",
        "Dimensioni e spessori dei tappetini da yoga — SANFAN"),
    "it/blog/moq-explained.html": (
        "Spiegazione del MOQ dei tappetini da yoga: fino a che punto è possibile ridurlo? — SANFAN",
        "MOQ dei tappetini da yoga: quanto si può ridurre? — SANFAN"),
    "it/blog/private-label-yoga-mats.html": (
        "Tappetini da yoga con marchio privato: la guida completa al lancio (2026) — SANFAN",
        "Tappetini da yoga con marchio privato: guida — SANFAN"),
    "it/blog/top-12-china-yoga-mat-manufacturers.html": (
        "I 12 principali produttori di tappetini da yoga in Cina (2026): confronto tra cluster — SANFAN",
        "12 produttori di tappetini da yoga in Cina (2026) — SANFAN"),
    "it/blog/yoga-mat-materials.html": (
        "Materiali per tappetini da yoga: TPE vs NBR vs PVC vs gomma (2026) — SANFAN",
        "Materiali dei tappetini da yoga: TPE, NBR, PVC — SANFAN"),
    "it/blog/yoga-mat-spec-guide.html": (
        "Guida allo spessore e alle dimensioni dei tappetini da yoga: come scegliere il tappetino giusto (2026) — SANFAN",
        "Spessore e dimensioni dei tappetini da yoga (2026) — SANFAN"),
    "it/pilates/index.html": (
        "Attrezzature per Pilates OEM/ODM — Reformer, Cadillac, Sedia — SANFAN",
        "Attrezzature Pilates OEM/ODM — Reformer, Cadillac — SANFAN"),
    "it/products/aurora-gradient-suede-yoga-mat.html": (
        "Tappetino da yoga in pelle scamosciata con effetto sfumato Aurora — SANFAN",
        "Tappetino da yoga Aurora in pelle scamosciata — SANFAN"),
    "it/products/flamingo-print-suede-rubber-yoga-mat.html": (
        "Tappetino da yoga in gomma e pelle scamosciata con stampa fenicottero — SANFAN",
        "Tappetino da yoga in gomma con stampa fenicottero — SANFAN"),
    "it/products/galaxy-gradient-suede-yoga-mat.html": (
        "Tappetino da yoga in pelle scamosciata con effetto sfumato Galaxy — SANFAN",
        "Tappetino da yoga Galaxy in pelle scamosciata — SANFAN"),
    "it/products/geometric-print-suede-tpe-yoga-mat.html": (
        "Tappetino da yoga in pelle scamosciata con stampa geometrica TPE — SANFAN",
        "Tappetino yoga in pelle scamosciata geometrico TPE — SANFAN"),
    "it/products/monochrome-leaf-suede-tpe-yoga-mat.html": (
        "Tappetino da yoga in pelle scamosciata Leaf monocromatico di TPE — SANFAN",
        "Tappetino yoga in pelle scamosciata Leaf TPE — SANFAN"),
    "it/products/mulinsen-widened-anti-slip-tpe-mat-90cm.html": (
        "Tappetino antiscivolo MuLinSen TPE in versione allargata 90cm — SANFAN",
        "Tappetino antiscivolo MuLinSen TPE 90cm — SANFAN"),
    "it/products/navy-botanical-suede-tpe-yoga-mat.html": (
        "Tappetino da yoga in pelle scamosciata botanica blu navy TPE — SANFAN",
        "Tappetino yoga in pelle scamosciata blu navy TPE — SANFAN"),
    "it/products/pink-mandala-foldable-suede-tpe-mat.html": (
        "Tappetino pieghevole in pelle scamosciata Pink Mandala per il TPE — SANFAN",
        "Tappetino pieghevole in pelle scamosciata Mandala — SANFAN"),
    "it/products/round-mandala-suede-tpe-yoga-mat.html": (
        "Tappetino da yoga rotondo in pelle scamosciata con motivo mandala TPE — SANFAN",
        "Tappetino yoga rotondo mandala in pelle scamosciata — SANFAN"),
    "it/products/starry-night-print-suede-yoga-mat.html": (
        "Tappetino da yoga in pelle scamosciata con stampa Notte stellata — SANFAN",
        "Tappetino yoga in pelle scamosciata Notte stellata — SANFAN"),
    "it/products/watercolor-floral-suede-yoga-mat.html": (
        "Tappetino da yoga in pelle scamosciata con motivi floreali ad acquerello — SANFAN",
        "Tappetino yoga in pelle scamosciata ad acquerello — SANFAN"),

    # ---------------- JA ----------------
    "ja/applications/home-online-sellers.html": (
        "AmazonおよびEコマース向けヨガ・フィットネス用品のサプライヤー | 最小発注数量（MOQ）が低い — SANFAN",
        "Amazon・EC向けヨガ用品サプライヤー | 低MOQ — SANFAN"),
    "ja/applications/hotels-resorts-spas.html": (
        "ホテル・リゾート向けヨガマットサプライヤー | カスタムロゴOEM — SANFAN",
        "ホテル・リゾート向けヨガマット | ロゴOEM — SANFAN"),
    "ja/blog/compliance.html": (
        "REACH、CA Prop 65、6P：米国およびEUにおけるヨガマットの規制対応 — SANFAN",
        "REACH・CA Prop 65・6P：ヨガマット規制対応 — SANFAN"),
    "ja/blog/moq-explained.html": (
        "ヨガマットの最小注文数量（MOQ）について：最低でもどこまで下げられるのか — SANFAN",
        "ヨガマットのMOQ：どこまで下げられる？ — SANFAN"),
    "ja/blog/top-12-china-yoga-mat-manufacturers.html": (
        "中国におけるヨガマットメーカートップ12社（2026年）：クラスター比較 — SANFAN",
        "中国のヨガマットメーカー12社（2026年） — SANFAN"),
    "ja/pilates/index.html": (
        "ピラティス器具のOEM/ODM — リフォーマー、キャデラック、チェア — SANFAN",
        "ピラティス器具のOEM/ODM — リフォーマー他 — SANFAN"),

    # ---------------- KO ----------------
    "ko/applications/home-online-sellers.html": (
        "아마존 및 전자상거래용 요가·피트니스 용품 공급업체 | 소량 주문 가능 — SANFAN",
        "아마존·전자상거래용 요가용품 공급업체 | 소량 MOQ — SANFAN"),
    "ko/blog/moq-explained.html": (
        "요가 매트 최소 주문 수량(MOQ) 해설: 최저 주문 수량은 어느 정도까지 가능할까 — SANFAN",
        "요가 매트 MOQ: 어디까지 낮출 수 있을까? — SANFAN"),
    "ko/blog/tpe-vs-pu.html": (
        "TPE PU 고무 요가 매트 비교: 2026년에는 어떤 제품을 선택해야 할까? — SANFAN",
        "TPE vs PU 고무 요가 매트: 무엇을 고를까? — SANFAN"),
# ---------------- 品牌在开头 / 无后缀的页面（index / faq / materials / 分类索引）----
    # 这些页的 title 不是 `… — SANFAN` 形式，split_brand() 认不出后缀，
    # 所以必须逐条改写（干跑时被列为「未覆盖」）。
    "de/blog.html": (
        "Blog – Einblicke in die Beschaffung von Yoga- und Fitnessartikeln — SANFAN",
        "Blog: Beschaffung von Yoga- &amp; Fitnessartikeln — SANFAN"),
    "de/faq.html": (
        "Häufig gestellte Fragen zu Yogamatten (OEM/ODM): Mindestbestellmenge, Zertifizierungen — SANFAN",
        "FAQ zu Yogamatten (OEM/ODM): MOQ und Zertifikate — SANFAN"),
    "de/index.html": (
        "SANFAN — OEM-/ODM-Hersteller von Yoga- und Fitnessartikeln | Seit 2013",
        "SANFAN — OEM/ODM-Hersteller für Yoga &amp; Fitness"),
    "de/materials.html": (
        "Vergleich der Materialien für Yogamatten – TPE vs. PVC vs. PU vs. Kork — SANFAN",
        "Yogamatten-Materialien: TPE vs. PVC vs. PU vs. Kork — SANFAN"),
    "fr/blog.html": (
        "Blog — Perspectives sur l'approvisionnement dans le domaine du yoga et du fitness — SANFAN",
        "Blog — Sourcing yoga et fitness — SANFAN"),
    "fr/faq.html": (
        "FAQ sur les tapis de yoga OEM/ODM : quantité minimale de commande (MOQ), certifications — SANFAN",
        "FAQ tapis de yoga OEM/ODM\u00a0: MOQ et certifications — SANFAN"),
    "fr/index.html": (
        "SANFAN — Fabricant OEM/ODM d'équipements de yoga et de fitness | Depuis 2013",
        "SANFAN — Fabricant OEM/ODM yoga et fitness"),
    "fr/materials.html": (
        "Comparaison des matériaux des tapis de yoga — TPE vs PVC vs PU vs liège — SANFAN",
        "Matériaux des tapis de yoga — TPE, PVC, PU, liège — SANFAN"),
    "it/faq.html": (
        "Domande frequenti sui tappetini da yoga OEM/ODM: quantità minima ordinabile (MOQ), certificazioni — SANFAN",
        "FAQ tappetini da yoga OEM/ODM: MOQ e certificazioni — SANFAN"),
    "it/index.html": (
        "SANFAN — Produttore OEM/ODM di articoli per lo yoga e il fitness | Dal 2013",
        "SANFAN — Produttore OEM/ODM yoga e fitness"),
    "it/materials.html": (
        "Confronto tra i materiali dei tappetini da yoga — TPE vs PVC vs PU vs sughero — SANFAN",
        "Materiali dei tappetini da yoga — TPE, PVC, PU — SANFAN"),
    "it/strength-training.html": (
        "Produttore di attrezzature per il potenziamento muscolare e il fitness — SANFAN",
        "Attrezzature per potenziamento muscolare e fitness — SANFAN"),
    "it/suede-cork-yoga-mats.html": (
        "Produttore di tappetini da yoga in pelle scamosciata e sughero — SANFAN",
        "Tappetini da yoga in pelle scamosciata e sughero — SANFAN"),
    "es/blog.html": (
        "Blog — Perspectivas sobre el abastecimiento en el sector del yoga y el fitness — SANFAN",
        "Blog — Sourcing de yoga y fitness — SANFAN"),
    "es/faq.html": (
        "Preguntas frecuentes sobre esterillas de yoga OEM/ODM: cantidad mínima de pedido, certificaciones — SANFAN",
        "Preguntas frecuentes: esterillas OEM/ODM — SANFAN"),
    "es/index.html": (
        "SANFAN — Fabricante OEM/ODM de productos de yoga y fitness | Desde 2013",
        "SANFAN — Fabricante OEM/ODM yoga y fitness"),
    "es/materials.html": (
        "Comparativa de materiales para esterillas de yoga: TPE frente a PVC frente a PU frente al corcho — SANFAN",
        "Materiales de esterillas de yoga — TPE, PVC, PU — SANFAN"),
    "ja/faq.html": (
        "ヨガマットのOEM/ODMに関するよくある質問：最小発注数量（MOQ）、認証 — SANFAN",
        "ヨガマットOEM/ODMのよくある質問：MOQ・認証 — SANFAN"),
    "ja/index.html": (
        "SANFAN — ヨガ・フィットネス用品のOEM／ODMメーカー | 2013年創業",
        "SANFAN — ヨガ・フィットネス用品のOEM/ODMメーカー"),
    "ko/index.html": (
        "SANFAN — 요가 및 피트니스 용품 OEM/ODM 제조업체 | 2013년 설립",
        "SANFAN — 요가·피트니스 용품 OEM/ODM 제조업체"),

    "it/blog/tpe-vs-pu.html": (
        "TPE Tappetini da yoga in gomma PU: quale scegliere nel 2026 — SANFAN",
        "Tappetini yoga in gomma PU vs TPE: quale scegliere — SANFAN"),
    "es/blog/tpe-vs-pu.html": (
        "TPE Esterillas de yoga de goma vs PU: ¿cuál elegir en 2026? — SANFAN",
        "Esterillas de yoga de goma TPE vs PU: ¿cuál elegir? — SANFAN"),
    "ja/blog/tpe-vs-pu.html": (
        "TPE PUゴム製ヨガマットの比較：2026年に選ぶべきは？ — SANFAN",
        "ゴム製ヨガマットの比較：TPEとPU、2026年に選ぶなら — SANFAN"),
    # ⭐ 表外残留 1 条（A/B 档逻辑均漏网）：w=63 超预算 3。
    #    病根不是「太长」而是**页内自相矛盾**——<title> 写 `Bandas de resistencia`，
    #    同页 og:title / twitter:title / h1 三处都写 `Bandas elásticas`。
    #    对齐为 og/h1 的措辞后 w=57，且与 fr(56)/it(56)/de(57) 同页同式（长后缀仍保留）。
    "es/products/figure-8-resistance-bands.html": (
        "Bandas de resistencia en forma de 8 — SANFAN Yoga & Fitness OEM",
        "Bandas elásticas en forma de 8 — SANFAN Yoga & Fitness OEM"),
}


LANGS = ["", "de", "ja", "ko", "fr", "it", "es"]
DIRS = ["", "products", "applications", "blog", "pilates"]


def pages():
    for lg in LANGS:
        for sub in DIRS:
            base = os.path.join(ROOT, lg) if lg else ROOT
            pat = os.path.join(base, sub, "*.html") if sub else os.path.join(base, "*.html")
            for f in sorted(glob.glob(pat)):
                yield os.path.relpath(f, ROOT), f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    rewritten = 0
    dropped = 0
    notfound = []
    problems = []

    for rel, path in pages():
        s = open(path, encoding="utf-8").read()
        m = TITLE_RE.search(s)
        if not m:
            continue
        raw = m.group(1)
        if W(html.unescape(raw)) <= BUDGET:
            continue

        new = None
        if rel in TITLES:
            old_expect, new = TITLES[rel]
            if norm(raw) != norm(old_expect):
                problems.append((rel, "原串不符", raw.strip()))
                continue
            rewritten += 1
        else:
            body, suf = split_brand(raw)
            bw = W(html.unescape(body))
            if suf is not None and 43 <= bw <= 59:
                new = body.rstrip()
                dropped += 1
            elif suf is not None and bw < 43:
                new = None                 # 后缀完整可见，不动
            else:
                problems.append((rel, "未覆盖（主体 %d）" % bw, raw.strip()))
                continue

        if new is None:
            continue
        if W(html.unescape(new)) > BUDGET:
            problems.append((rel, "新标题仍超预算 %d" % W(html.unescape(new)), new))
            continue
        if args.apply:
            start, end = m.span(1)
            s = s[:start] + new + s[end:]
            open(path, "w", encoding="utf-8").write(s)

    print("模式：%s" % ("落盘" if args.apply else "干跑"))
    print("A 档重写 %d 条 | B 档去后缀 %d 条" % (rewritten, dropped))
    if problems:
        print("\n⚠️ 需要处理 %d 条：" % len(problems))
        for rel, why, t in problems:
            print("    [%s] %s\n        %s" % (why, rel, t))

    # 终检：全站 title 宽度复核
    over = []
    for rel, path in pages():
        s = open(path, encoding="utf-8").read()
        m = TITLE_RE.search(s)
        if m and W(html.unescape(m.group(1))) > BUDGET:
            over.append((W(html.unescape(m.group(1))), rel))
    print("\n=== 终检：title >60 共 %d 条 ===" % len(over))
    for w, rel in sorted(over, reverse=True)[:25]:
        print("    %3d  %s" % (w, rel))
    return 0


if __name__ == "__main__":
    sys.exit(main())
