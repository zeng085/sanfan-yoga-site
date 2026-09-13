#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_listicle_20260913.py — 榜单页（top-12-china-yoga-mat-manufacturers）四类缺陷修复

背景与不修会出现什么：
  1. EN 页正文包在 <div class="lang-en"> 里却没有配套 .lang-zh 块 →
     html.show-zh .lang-en{display:none} 把 h1/封面/表格/正文全隐藏 = 整篇白页。
     两条触发路径：访客 siteLang=zh 直接白页；任意语言版菜单里的「中文」都 href 到本页。
  2. 8 篇旧博客页反过来：正文没有 .lang-en 包裹，且 .lang-zh 被放到了 .container
     外面（layout 无容器约束）→ 中文模式下英文全文与中文块并存、两个 h1、正文满幅。
  3. build_listicle.py 把 EN 的 meta description 原样送去 DeepL，源页那句本来就断了
     （少了最后一个词），于是 7 个语言版全断在半句；而且 de/fr/it/es 版本长到 200–243 字符。
  4. 机翻把规格表打烂：ja/ko 把 Capacity 译成「収容人数／수용 인원」、把 "4 lines" 译成
     「4 行／4줄」、把 "Studio-grade runs" 译成「スタジオ品質の録音／스튜디오급 녹음」；
     fr/it/es 出现 "10,000 ㎡e" / "22,354 ㎡ ans" / "TPEe" / "TPEPUo" 这类拼接错误；
     ja/ko 还把厂商名转写成了汉字/한글（「張家港華芸ゴム株式会社」「장쑤 YDB 산업 유한공사」），
     既凭空捏造了公司中文/日文名，又让买家无法按原名称检索。

本脚本做四件事（全部幂等，可重复运行）：
  A. 7 个语言页：整表重建（厂商名统一保留拉丁原文）+ 表头/脚注人工译文 + 描述重写
     + og:type=article + og:locale + 封面图写真实宽高。
  B. EN 页：补一份完整中文内容块（<h2 class="post-title"> 承接，保持 h1 唯一）。
  C. 8 篇旧博客页：包 .lang-en、把 .lang-zh 挪回 .container 内、补 </article>。
  D. 自检：div 平衡、h1 数量、表格 6 列 12 行、机翻坏词残留 = 0。

⚠️ 本脚本执行后，i18n_build/build_listicle.py 不应再重跑（会把人工译文和中文块冲掉），
   该脚本已加运行时护栏拦这种情况。
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SLUG = "top-12-china-yoga-mat-manufacturers"
LANGS = ["en", "de", "ja", "ko", "fr", "it", "es"]

DRY = "--dry" in sys.argv
errors = []


def path_of(lang):
    return os.path.join(ROOT, "blog", SLUG + ".html") if lang == "en" \
        else os.path.join(ROOT, lang, "blog", SLUG + ".html")


def rel_root(lang):
    """页面到站点根的前缀"""
    return ".." if lang == "en" else "../.."


# --------------------------------------------------------------- A1. meta description
# 全部 ≤160 字符、句子完整。EN 原句 173 字符且断了尾词；de/fr/it/es 原句 200–243 字符。
DESC = {
    "en": "Compare 12 established Chinese yoga mat manufacturers by cluster — Jiangsu, "
          "Zhejiang, Hubei, Shandong, Guangdong, Fujian — with MOQ, capacity and certifications.",
    "de": "12 Yogamatten-Hersteller aus China im Cluster-Vergleich: Jiangsu, Zhejiang, Hubei, "
          "Shandong, Guangdong, Fujian — mit MOQ, Kapazität und Zertifizierungen.",
    "ja": "中国のヨガマットメーカー12社を、江蘇・浙江・湖北・山東・広東・福建の6大産地別に比較。"
          "MOQ・生産能力・素材・認証の観点で整理しました。",
    "ko": "중국 요가 매트 제조업체 12곳을 장쑤·저장·후베이·산둥·광둥·푸젠 6대 클러스터별로 비교했습니다. "
          "MOQ, 생산 능력, 소재, 인증을 한눈에 정리.",
    "fr": "12 fabricants chinois de tapis de yoga comparés par pôle industriel — Jiangsu, "
          "Zhejiang, Hubei, Shandong, Guangdong, Fujian — MOQ, capacité et certifications.",
    "it": "12 produttori cinesi di tappetini yoga a confronto per distretto — Jiangsu, Zhejiang, "
          "Hubei, Shandong, Guangdong, Fujian — con MOQ, capacità e certificazioni.",
    "es": "12 fabricantes chinos de esterillas de yoga comparados por clúster — Jiangsu, Zhejiang, "
          "Hubei, Shandong, Guangdong, Fujian — con MOQ, capacidad y certificaciones.",
}

OG_LOCALE = {"en": "en_US", "de": "de_DE", "ja": "ja_JP", "ko": "ko_KR",
             "fr": "fr_FR", "it": "it_IT", "es": "es_ES"}


# --------------------------------------------------------------- A2. 对比表
# 厂商名 = 拉丁原文，7 个语言一律相同：买家是按拉丁名检索核对的，
# 翻成汉字/한글 既搜不到，还会凭空造出不存在的中文/日文公司名。
NAMES = [
    "Jiangsu YDB Industrial",
    "Zhangjiagang Huayi Rubber",
    "Yancheng Tianzhihui (TIANHUI)",
    "Jiangsu Huayang Sports",
    "Ningbo Healthmate",
    "Ningbo Virson",
    "Yiwu Yunhuan",
    "Wuhan FDM Eco Fitness (FDM Yoga / Uga Sport)",
    "Wuhan Ugasport",
    "Qingdao Kingking",
    "Dongguan GY Industrial",
    "FUJIAN SANFAN Sports Products",
]

# 产区列
CLUSTER_ORDER = ["Jiangsu", "Jiangsu", "Jiangsu", "Jiangsu", "Zhejiang", "Zhejiang",
                 "Zhejiang", "Hubei", "Hubei", "Shandong", "Guangdong", "Fujian"]
CLUSTER = {
    "en": {"Jiangsu": "Jiangsu", "Zhejiang": "Zhejiang", "Hubei": "Hubei",
           "Shandong": "Shandong", "Guangdong": "Guangdong", "Fujian": "Fujian"},
    "de": {"Jiangsu": "Jiangsu", "Zhejiang": "Zhejiang", "Hubei": "Hubei",
           "Shandong": "Shandong", "Guangdong": "Guangdong", "Fujian": "Fujian"},
    "ja": {"Jiangsu": "江蘇省", "Zhejiang": "浙江省", "Hubei": "湖北省",
           "Shandong": "山東省", "Guangdong": "広東省", "Fujian": "福建省"},
    "ko": {"Jiangsu": "장쑤", "Zhejiang": "저장", "Hubei": "후베이",
           "Shandong": "산둥", "Guangdong": "광둥", "Fujian": "푸젠"},
    "fr": {"Jiangsu": "Jiangsu", "Zhejiang": "Zhejiang", "Hubei": "Hubei",
           "Shandong": "Shandong", "Guangdong": "Guangdong", "Fujian": "Fujian"},
    "it": {"Jiangsu": "Jiangsu", "Zhejiang": "Zhejiang", "Hubei": "Hubei",
           "Shandong": "Shandong", "Guangdong": "Guangdong", "Fujian": "Fujian"},
    "es": {"Jiangsu": "Jiangsu", "Zhejiang": "Zhejiang", "Hubei": "Hubei",
           "Shandong": "Shandong", "Guangdong": "Guangdong", "Fujian": "Fujian"},
}

# 现成材料列（12 行）
MATS = {
    "en": ["PVC, TPE", "PVC, TPE, NBR, EVA", "PVC, TPE + judo/taekwondo mats",
           "TPE, NBR, PVC, rubber", "Premium TPE/rubber (tech grip)", "PVC, TPE, NBR",
           "TPE (closed-cell)", "TPE, PU, rubber, cork, suede", "TPE, PU, NBR",
           "PVC foam", "TPE, natural rubber, PU",
           "TPE dual-layer, PU, rubber, full fitness range"],
    "de": ["PVC, TPE", "PVC, TPE, NBR, EVA", "PVC, TPE + Judo-/Taekwondo-Matten",
           "TPE, NBR, PVC, Gummi", "Premium-TPE/Gummi (Tech-Grip)", "PVC, TPE, NBR",
           "TPE (geschlossenzellig)", "TPE, PU, Gummi, Kork, Wildleder", "TPE, PU, NBR",
           "PVC-Schaum", "TPE, Naturkautschuk, PU",
           "TPE zweischichtig, PU, Gummi, komplettes Fitness-Sortiment"],
    "ja": ["PVC、TPE", "PVC、TPE、NBR、EVA", "PVC、TPE ＋ 柔道・テコンドー用マット",
           "TPE、NBR、PVC、ゴム", "プレミアムTPE／ゴム（テックグリップ）", "PVC、TPE、NBR",
           "TPE（独立気泡）", "TPE、PU、ゴム、コルク、スエード", "TPE、PU、NBR",
           "PVCフォーム", "TPE、天然ゴム、PU",
           "TPE二層、PU、ゴム、フィットネス全般"],
    "ko": ["PVC, TPE", "PVC, TPE, NBR, EVA", "PVC, TPE + 유도·태권도 매트",
           "TPE, NBR, PVC, 고무", "프리미엄 TPE/고무 (테크 그립)", "PVC, TPE, NBR",
           "TPE (독립 기포)", "TPE, PU, 고무, 코르크, 스웨이드", "TPE, PU, NBR",
           "PVC 폼", "TPE, 천연고무, PU",
           "TPE 이중층, PU, 고무, 전 품목 피트니스"],
    "fr": ["PVC, TPE", "PVC, TPE, NBR, EVA", "PVC, TPE + tapis de judo/taekwondo",
           "TPE, NBR, PVC, caoutchouc", "TPE/caoutchouc haut de gamme (Tech Grip)", "PVC, TPE, NBR",
           "TPE (à cellules fermées)", "TPE, PU, caoutchouc, liège, daim", "TPE, PU, NBR",
           "mousse PVC", "TPE, caoutchouc naturel, PU",
           "TPE double couche, PU, caoutchouc, gamme fitness complète"],
    "it": ["PVC, TPE", "PVC, TPE, NBR, EVA", "PVC, TPE + tappetini judo/taekwondo",
           "TPE, NBR, PVC, gomma", "TPE/gomma premium (Tech Grip)", "PVC, TPE, NBR",
           "TPE (a celle chiuse)", "TPE, PU, gomma, sughero, camoscio", "TPE, PU, NBR",
           "schiuma PVC", "TPE, gomma naturale, PU",
           "TPE a doppio strato, PU, gomma, gamma fitness completa"],
    "es": ["PVC, TPE", "PVC, TPE, NBR, EVA", "PVC, TPE + esterillas de judo/taekwondo",
           "TPE, NBR, PVC, caucho", "TPE/goma premium (Tech Grip)", "PVC, TPE, NBR",
           "TPE (de célula cerrada)", "TPE, PU, caucho, corcho, ante", "TPE, PU, NBR",
           "espuma de PVC", "TPE, caucho natural, PU",
           "TPE de doble capa, PU, caucho, gama fitness completa"],
}

# 起订量列（12 行）；单位按语言，数值与 EN 源页完全一致
MOQ_UNIT = {"en": "pcs", "de": "Stück", "ja": "枚", "ko": "개",
            "fr": "pièces", "it": "pezzi", "es": "unidades"}
MOQ_VALUES = ["n/p", 500, "n/p", 1000, "2000+", "n/p", 500, 100, 100, "n/p", "n/p", 100]


def moq_cell(lang, v):
    if v == "n/p":
        return "n/p"
    u = MOQ_UNIT[lang]
    if isinstance(v, str) and v.endswith("+"):
        num = "{:,}".format(int(v[:-1])).replace(",", "." if lang in ("de", "it", "es") else
                                                              (" " if lang == "fr" else ","))
        plus = {"de": "+", "ja": "以上", "ko": " 이상", "fr": "+", "it": "+", "es": "+"}.get(lang, "+")
        return f"{num}{plus} {u}"
    num = "{:,}".format(int(v)).replace(",", "." if lang in ("de", "it", "es") else
                                                    (" " if lang == "fr" else ","))
    return f"{num} {u}"


# 产能列（12 行）—— 人工重写，修掉「4 行 / 4줄 / スタジオ品質の録音 / 10,000 ㎡e」这类机翻损伤
CAP = {
    "en": ["Volume export", "50,000 pcs/mo", "500,000 yoga mats/yr",
           "150,000–200,000 pcs/mo", "~700,000 units/yr (all fitness)",
           "10,000 ㎡, 4 lines", "50,000–80,000 pcs/mo", "6,000–10,000 pcs/day",
           "22,354 ㎡, 6 lines", "Mass production", "Studio-grade runs", "~8,000 mats/day"],
    "de": ["Exportorientierte Großserien", "50.000 Stück/Monat", "500.000 Yogamatten/Jahr",
           "150.000–200.000 Stück/Monat", "~700.000 Einheiten/Jahr (gesamtes Fitness-Sortiment)",
           "10.000 ㎡, 4 Produktionslinien", "50.000–80.000 Stück/Monat",
           "6.000–10.000 Stück/Tag", "22.354 ㎡, 6 Produktionslinien", "Massenproduktion",
           "Kleinserien in Studioqualität", "~8.000 Matten/Tag"],
    "ja": ["輸出向け大口生産", "月産50,000枚", "年産500,000枚（ヨガマット）",
           "月産150,000～200,000枚", "年産約700,000台（フィットネス全般）",
           "10,000㎡、4ライン", "月産50,000～80,000枚", "日産6,000～10,000枚",
           "22,354㎡、6ライン", "大量生産", "スタジオ向け小ロット生産", "日産約8,000枚"],
    "ko": ["수출용 대량 생산", "월 50,000개", "연 500,000장(요가 매트)",
           "월 150,000~200,000개", "연 약 700,000대 (피트니스 전 품목)",
           "10,000㎡, 4개 라인", "월 50,000~80,000개", "일 6,000~10,000개",
           "22,354㎡, 6개 라인", "대량 생산", "스튜디오급 소량 생산", "일 약 8,000장"],
    "fr": ["Production en gros volume pour l'export", "50 000 pièces/mois", "500 000 tapis/an",
           "150 000 à 200 000 pièces/mois", "~700 000 unités/an (gamme fitness complète)",
           "10 000 ㎡, 4 lignes de production", "50 000 à 80 000 pièces/mois",
           "6 000 à 10 000 pièces/jour", "22 354 ㎡, 6 lignes de production",
           "Production de masse", "Petites séries qualité studio", "~8 000 tapis/jour"],
    "it": ["Grandi volumi per l'export", "50.000 pezzi/mese", "500.000 tappetini/anno",
           "150.000–200.000 pezzi/mese", "~700.000 unità/anno (gamma fitness completa)",
           "10.000 ㎡, 4 linee di produzione", "50.000–80.000 pezzi/mese",
           "6.000–10.000 pezzi/giorno", "22.354 ㎡, 6 linee di produzione",
           "Produzione di massa", "Piccole serie di qualità professionale", "~8.000 tappetini/giorno"],
    "es": ["Grandes volúmenes para exportación", "50.000 unidades/mes", "500.000 esterillas/año",
           "150.000–200.000 unidades/mes", "~700.000 unidades/año (gama fitness completa)",
           "10.000 ㎡, 4 líneas de producción", "50.000–80.000 unidades/mes",
           "6.000–10.000 unidades/día", "22.354 ㎡, 6 líneas de producción",
           "Producción en serie", "Series pequeñas de calidad profesional",
           "~8.000 esterillas/día"],
}

# 认证列（12 行）：绝大多数是标准缩写，7 个语言原样保留
CERT_SAME = ["—", "EN71, 6P, REACH, RoHS", "ISO 9001, BSCI", "SGS", None, "EN71-3", None,
             "ISO 9001, BSCI, GRS, FSC, OEKO-TEX 100, REACH, RoHS", "REACH, OEKO-TEX 100",
             None, "—", "ROHS / CE / ISO 9001 / BSCI / REACH"]
CERT_DESC = {  # None 位置的文字型证书描述
    ("en", 4): "Patented grip systems",
    ("de", 4): "Patentierte Griffsysteme",
    ("ja", 4): "特許取得済みグリップシステム",
    ("ko", 4): "특허받은 그립 시스템",
    ("fr", 4): "Systèmes d'adhérence brevetés",
    ("it", 4): "Sistemi di presa brevettati",
    ("es", 4): "Sistemas de agarre patentados",
    ("en", 6): "ASTM D2047 slip tested",
    ("de", 6): "ASTM D2047 Rutschtest",
    ("ja", 6): "ASTM D2047 滑り試験済み",
    ("ko", 6): "ASTM D2047 미끄럼 시험 완료",
    ("fr", 6): "Test de glissement ASTM D2047",
    ("it", 6): "Test di scivolamento ASTM D2047",
    ("es", 6): "Ensayo de deslizamiento ASTM D2047",
    ("en", 9): "Private-label supply",
    ("de", 9): "Private-Label-Lieferung",
    ("ja", 9): "PB（自主ブランド）供給",
    ("ko", 9): "PB(자체 브랜드) 공급",
    ("fr", 9): "Fourniture en marque propre",
    ("it", 9): "Fornitura a marchio privato",
    ("es", 9): "Suministro de marca blanca",
}

TH = {
    "en": ["Manufacturer", "Cluster", "Main materials", "MOQ",
           "Capacity (self-reported)", "Certifications on file"],
    "de": ["Hersteller", "Cluster", "Hauptmaterialien", "MOQ",
           "Kapazität (nach eigenen Angaben)", "Vorliegende Zertifikate"],
    "ja": ["メーカー", "産地クラスター", "主な素材", "MOQ",
           "生産能力（自己申告）", "保有認証"],
    "ko": ["제조사", "지역 클러스터", "주요 소재", "MOQ",
           "생산 능력(자체 발표)", "보유 인증"],
    "fr": ["Fabricant", "Pôle industriel", "Matériaux principaux", "MOQ",
           "Capacité (autodéclarée)", "Certifications disponibles"],
    "it": ["Produttore", "Distretto", "Materiali principali", "MOQ",
           "Capacità (autodichiarata)", "Certificazioni disponibili"],
    "es": ["Fabricante", "Clúster", "Materiales principales", "MOQ",
           "Capacidad (autodeclarada)", "Certificaciones disponibles"],
    "zh": ["制造商（保留英文原名）", "产区集群", "主要材质", "起订量 MOQ",
           "产能（自我申报）", "已提供认证"],
}

FOOTNOTE = {
    "en": "n/p = not published. Every figure above is the manufacturer's own claim — verify "
          "certificates and capacity before contracting (method below).",
    "de": "n/p = nicht veröffentlicht. Alle Angaben oben stammen vom Hersteller selbst – prüfen "
          "Sie Zertifikate und Kapazität vor Vertragsabschluss (Methode unten).",
    "ja": "n/p = 未公表。上記の数値はすべて各メーカーの自己申告です。契約前に認証書と生産能力を"
          "必ず確認してください（確認方法は後述）。",
    "ko": "n/p = 미공개. 위 수치는 모두 각 제조사의 자체 발표 자료입니다. 계약 전에 인증서와 "
          "생산 능력을 반드시 확인하세요(방법은 아래).",
    "fr": "n/p = non publié. Tous les chiffres ci-dessus sont déclarés par les fabricants "
          "eux-mêmes — vérifiez certificats et capacité avant de contracter (méthode ci-dessous).",
    "it": "n/p = non pubblicato. Tutti i dati sopra sono autodichiarati dai produttori — "
          "verificate certificati e capacità prima di firmare (metodo sotto).",
    "es": "n/p = no publicado. Todas las cifras anteriores son declaradas por los propios "
          "fabricantes: verifica certificados y capacidad antes de contratar (método abajo).",
}

# 机翻把 "between them"（12 家之间）译成"二者之间"，顺手改对（es/de 原文已正确）
H2_FIX = {
    "ja": [("どちらを選ぶべきか", "どの工場を選ぶか")],
    "ko": [("둘 중 하나를 고르는 방법", "어떻게 선택할까")],
    "fr": [("Comment faire son choix entre les deux ?", "Comment faire son choix")],
    "it": [("Come scegliere tra le due opzioni", "Come scegliere tra loro")],
}

# ja/ko 的 12 个 h3：厂商名回归拉丁原文，只把城市本地化（原版凭空造了「株式会社」）
H3_JA = [
    "1. Jiangsu YDB Industrial Co., Ltd. — 塩城",
    "2. Zhangjiagang Huayi Rubber Co., Ltd. — 張家港",
    "3. Yancheng Tianzhihui Sports Goods (TIANHUI) — 塩城",
    "4. Jiangsu Huayang Sports — 江蘇",
    "5. Ningbo Healthmate Science and Technology — 寧波・寧海",
    "6. Ningbo Virson Sporting Goods — 寧波",
    "7. Yiwu Yunhuan Trading — 義烏",
    "8. Wuhan FDM Eco Fitness Product Co., Ltd. (FDM Yoga / Uga Sport)",
    "9. Wuhan Ugasport Co., Ltd.",
    "10. Qingdao Kingking Applied Chemistry Co., Ltd.",
    "11. Dongguan GY Industrial Co., Ltd.",
    "12. FUJIAN SANFAN Sports Products Co., Ltd.",
]
H3_KO = [
    "1. Jiangsu YDB Industrial Co., Ltd. — 옌청",
    "2. Zhangjiagang Huayi Rubber Co., Ltd. — 장자강",
    "3. Yancheng Tianzhihui Sports Goods (TIANHUI) — 옌청",
    "4. Jiangsu Huayang Sports — 장쑤",
    "5. Ningbo Healthmate Science and Technology — 닝보·닝하이",
    "6. Ningbo Virson Sporting Goods — 닝보",
    "7. Yiwu Yunhuan Trading — 이우",
    "8. Wuhan FDM Eco Fitness Product Co., Ltd. (FDM Yoga / Uga Sport)",
    "9. Wuhan Ugasport Co., Ltd.",
    "10. Qingdao Kingking Applied Chemistry Co., Ltd.",
    "11. Dongguan GY Industrial Co., Ltd.",
    "12. FUJIAN SANFAN Sports Products Co., Ltd.",
]

# 中文表（EN 页 .lang-zh 块用）；厂商名同样保留拉丁原文，便于按原名检索
ZH_NAMES = [
    "江苏 YDB Industrial", "张家港 Huayi Rubber", "盐城 Tianzhihui（TIANHUI）",
    "江苏 Huayang Sports", "宁波 Healthmate", "宁波 Virson", "义乌 Yunhuan",
    "武汉 FDM Eco Fitness（FDM Yoga / Uga Sport）", "武汉 Ugasport",
    "青岛 Kingking", "东莞 GY Industrial", "福建三梵 FUJIAN SANFAN",
]
ZH_CLUSTER = ["江苏", "江苏", "江苏", "江苏", "浙江", "浙江", "浙江",
              "湖北", "湖北", "山东", "广东", "福建"]
ZH_MATS = ["PVC、TPE", "PVC、TPE、NBR、EVA", "PVC、TPE ＋ 柔道／跆拳道垫",
           "TPE、NBR、PVC、橡胶", "高端 TPE／橡胶（专利抓地）", "PVC、TPE、NBR",
           "TPE（闭孔）", "TPE、PU、橡胶、软木、麂皮", "TPE、PU、NBR",
           "PVC 发泡", "TPE、天然橡胶、PU", "TPE 双层、PU、橡胶、全品类健身"]
ZH_MOQ = ["未公布", "500 片", "未公布", "1,000 片", "2,000 片以上", "未公布", "500 片",
          "100 片", "100 片", "未公布", "未公布", "100 片"]
ZH_CAP = ["出口为主的大批量", "5 万片/月", "瑜伽垫 50 万片/年", "15 万–20 万片/月",
          "约 70 万台/年（含全部健身品类）", "10,000 ㎡、4 条线", "5 万–8 万片/月",
          "6,000–10,000 片/天", "22,354 ㎡、6 条线", "大批量生产", "工作室级小批量",
          "约 8,000 片/天"]
ZH_CERT = ["—", "EN71、6P、REACH、RoHS", "ISO 9001、BSCI", "SGS", "专利抓地系统", "EN71-3",
           "ASTM D2047 防滑测试", "ISO 9001、BSCI、GRS、FSC、OEKO-TEX 100、REACH、RoHS",
           "REACH、OEKO-TEX 100", "自主品牌供货",
           "—", "ROHS / CE / ISO 9001 / BSCI / REACH"]


def build_table(lang, ind="              "):
    """生成对比表（不含外层 overflow 容器）；缩进对齐 EN 页既有排版"""
    thead = ind + "<thead><tr>" + "".join(f"<th>{c}</th>" for c in TH[lang]) + "</tr></thead>"
    body = [ind + "  <tbody>"]
    for i in range(12):
        if lang == "zh":
            name, cl, mat, moq, cap, cert = (ZH_NAMES[i], ZH_CLUSTER[i], ZH_MATS[i],
                                             ZH_MOQ[i], ZH_CAP[i], ZH_CERT[i])
        else:
            mat = MATS[lang][i]
            moq = moq_cell(lang, MOQ_VALUES[i])
            cap = CAP[lang][i]
            cert = CERT_DESC.get((lang, i), CERT_SAME[i])
            name = NAMES[i]
            cl = CLUSTER[lang][CLUSTER_ORDER[i]]
        tds = "".join(f"<td>{v}</td>" for v in (name, cl, mat, moq, cap, cert))
        body.append(ind + "    <tr>" + tds + "</tr>")
    body.append(ind + "  </tbody>")
    return ('<table class="cap-table">\n' + thead + "\n" + "\n".join(body) + "\n"
            + ind[:-2] + "</table>")


# --------------------------------------------------------------- B. EN 页中文块
ZH_BLOCK = """        <div class="lang-zh">
          <div class="post-meta">采购 · 9 分钟 · 更新于 2026 年 9 月</div>
          <h1>2026 中国 12 大瑜伽垫制造商：六大产区集群横评</h1>
          <p class="lead-p">在中国找瑜伽垫工厂不难，难的是找到起订量、材质、认证都合得上的那一家。这篇按六大产区对比 12 家成熟制造商，资料全部取自各家公开发布的审核信息与官网。</p>
          <img class="article-cover" src="../assets/img/factory-building.webp" width="1920" height="1249" loading="lazy" alt="中国的瑜伽垫生产工厂" />
          <div class="article-body">
            <p><strong>资料说明：</strong>下表所有数字（起订量、产能、认证）都是各厂商在公开渠道的自我申报，来源为 Made-in-China／Alibaba 审核页、公司官网与第三方贸易名录，采集于 2026 年 9 月。这只是初筛起点，不能替代你自己验厂。厂商按产区归类，<strong>不分排名</strong>；公司名保留英文原名，方便你按原名称检索核对。</p>

            <h2>快速对比</h2>
            <div style="overflow-x:auto;-webkit-overflow-scrolling:touch">@@ZH_TABLE@@</div>
            <p style="font-size:13.5px;color:#666">n/p = 未公布。以上全部为厂商自述，签约前请自行核验证书与产能（核验方法见下文）。</p>

            <h2>江苏产区（盐城／张家港）——发泡与橡胶主带</h2>
            <p>江苏位于上海以北，是中国发泡垫与橡胶垫工厂最密集的地带。PVC／TPE 材质菜单最全、FOB 价格竞争性强，工厂习惯接大批量返单。</p>
            <h3>1. Jiangsu YDB Industrial — 盐城</h3>
            <p>被多方引用的出口型厂商，PVC、TPE 及各类体操垫产品线很宽，自有品牌定制能力强。适合：想用一家供应商整合 PVC＋TPE 出货量的大型零售商与经销商。</p>
            <h3>2. Zhangjiagang Huayi Rubber — 张家港</h3>
            <p>距上海约两小时车程的发泡材料专业厂，产 PVC、TPE、NBR、EVA、PU 五类发泡品。公开起订量 500 片、月产能约 5 万片，支持 EN71、6P、REACH、RoHS，生产历史 15 年以上。适合：第一天就要 REACH 文件、主攻欧盟的自有品牌项目。</p>
            <h3>3. Yancheng Tianzhihui（TIANHUI）— 盐城</h3>
            <p>江苏 Crosste 集团旗下运动板块，10 条线覆盖瑜伽垫、柔道垫、跆拳道垫与橡胶地垫。自报瑜伽垫年产约 50 万片、年产值 5,000 万–1 亿美元，通过 ISO 9001 与 BSCI 审核。适合：需要"瑜伽＋格斗垫"混合配货的买家。</p>
            <h3>4. Jiangsu Huayang Sports — 江苏</h3>
            <p>规模较大的专业垫厂之一：厂房 25,000 ㎡ 以上、月产能估计 15 万–20 万片、起订量 1,000 片、通过 SGS 审核，TPE／NBR／PVC／天然橡胶四条线，出口 40 多个国家。适合：成熟品牌需要大批量稳定交付，且 COA 与合规包能提前给齐。</p>

            <h2>浙江产区（宁波／义乌）——高端与配件齐备</h2>
            <p>浙江同时坐拥中国两个大港，供应商在研发型产品与品类宽度上更强 —— 垫子要和瑜伽砖、伸展带、泡沫轴同柜出货时特别方便。</p>
            <h3>5. Ningbo Healthmate — 宁波宁海</h3>
            <p>2007 年成立，厂房约 10 万㎡、员工 850 人，健身器材年产量约 70 万台。瑜伽垫靠专利"湿手防滑"涂层与抗菌表层做差异，定价落在高端 10–18 美元区间。适合：以抓地性能为卖点的高端科技型产品线。</p>
            <h3>6. Ningbo Virson — 宁波</h3>
            <p>2008 年成立，园区 10,000 ㎡，两条 PVC 线 ＋ 一条台湾产 NBR 线 ＋ 一条 TPE 线，通过 EN71-3。适合：要在同一采购流程里把垫子和健身配件一起打包的欧美经销商。</p>
            <h3>7. Yiwu Yunhuan — 义乌</h3>
            <p>TPE 防滑专业厂，月产 5 万–8 万片、起订量 500 片，闭孔 TPE 不易吸潮，FOB 报价约 4.5–8 美元。适合：以小批量试水、控制初期风险的中小品牌。</p>

            <h2>湖北产区（武汉）——垂直一体化</h2>
            <p>武汉这一代工厂比的是垂直供应链（从自有发泡到包装）和环保认证密度，而不是港口距离。</p>
            <h3>8. Wuhan FDM Eco Fitness（FDM Yoga / Uga Sport）</h3>
            <p>2015 年成立于湖北自由集团（Hubei Freedom Group）体系内，多处厂区合计 3 万–4 万㎡，产 TPE、PU、天然橡胶、软木、麂皮垫，持有 ISO 9001、BSCI、GRS、FSC、OEKO-TEX 100、REACH、RoHS。起订量最低 100 片；据公开资料为欧洲超市渠道（含 Aldi、Rossmann）供货，出口 30 多个国家。适合：需要 GRS／FSC 这类环保资质作为准入门槛、而非加分项的商超项目。</p>
            <h3>9. Wuhan Ugasport</h3>
            <p>厂房 22,354 ㎡、6 条生产线、88 台设备，持有 REACH 与 OEKO-TEX 100。公开 TPE 垫报价约 2.88–3.78 美元（100 片起）；主要市场为北美（约 25%）、北欧与东欧。适合：价格优先、但仍需要低起订量与主流环保认证的 TPE 项目。</p>

            <h2>山东产区（青岛）——PVC 发泡老基地</h2>
            <h3>10. Qingdao Kingking</h3>
            <p>青岛厂商，以 PVC 发泡及同类垫材见长，具备大批量生产经验，为国际市场做自主品牌供货。适合：单价权重高于材质新奇度的经济型 PVC 大货。</p>

            <h2>广东产区（东莞）——馆级高抓地</h2>
            <h3>11. Dongguan GY Industrial</h3>
            <p>专注瑜伽的工厂，提供天然橡胶、PU 与 TPE 配置，走更高抓地的构建，面向瑜伽馆与高端零售定位。适合：抓地手感比单价更重要的瑜伽馆与高端 DTC 品牌。</p>

            <h2>福建产区（晋江／泉州）——运动用品走廊</h2>
            <h3>12. 福建三梵 FUJIAN SANFAN Sports Products</h3>
            <p>位于晋江，正处中国运动服装与运动用品走廊，直连厦门港。2013 年成立；厂房 12,000 ㎡；员工 600+；双色 TPE 双层线日产约 8,000 片，另有 PU／橡胶垫、泡沫轴、弹力带与健身器材。公开起订量 100 片、7 天打样，通过 ISO 9001 与 BSCI 审核，具备 ROHS、CE、REACH 合规。适合：需要低起订量、快速打样，且想用一家供应商覆盖"瑜伽＋健身"全目录的初创品牌、亚马逊卖家与精品品牌。</p>

            <h2>怎么在这 12 家里做选择</h2>
            <ul>
              <li><strong>材质跟着市场走。</strong> TPE 赢在电商经济性（6mm 垫约 1.1kg，PU 橡胶约 2.4kg）；橡胶／PU 赢在高温瑜伽的抓地。<a href="tpe-vs-pu.html">TPE 与 PU 对比 →</a></li>
              <li><strong>起订量跟着现金流走。</strong> 100 片起的工厂确实存在（FDM、Ugasport、SANFAN）；1,000 片以上能换到更好的单价。<a href="moq-explained.html">起订量到底怎么算 →</a></li>
              <li><strong>认证跟着目的地走。</strong> 欧盟要 REACH；美国零售常要 CA Prop 65；商超渠道再加 BSCI／GRS。<a href="compliance.html">分市场合规要求 →</a></li>
              <li><strong>签约前先核验。</strong> 样品、自制还是外发工序、证书编号、小批量试单 —— 完整清单见<a href="vet-factory.html">如何验厂 →</a></li>
            </ul>

            <div style="margin:28px 0;padding:20px 22px;border:1px solid var(--line);border-radius:12px;background:var(--bg-soft,#f7f7f5)">
              <strong>2026 年要上 TPE 或橡胶线？</strong><br />
              三梵把数字直接公开 —— 100 片起订、7 天打样，SGS／REACH／CA Prop 65 文件按要求提供。
              <a class="btn btn-primary" style="display:inline-flex;margin-top:12px" href="../contact.html">获取报价</a>
            </div>
          </div>
        </div>
"""


# 散文/JSON-LD 层的机翻损伤（表格之外）——逐条人工重写，replace 精确匹配，幂等
# 病灶：某次管线把受保护术语回填时把名词词尾一起吃掉了
# （alfombrillas → alfombrTPEes / tappetini → tappetTPE），以及 ㎡ 被粘上词尾（㎡e）
PROSE_FIX = {
    "it": [
        ("Per i tappetTPE,", "Per i tappetini in TPE,"),
        ("I tappet e in gomma naturale", "I tappetini in PU e in gomma naturale"),
        ("i tappetini PUin composito di gomma e sughero",
         "i tappetini in PU-gomma e in composito di sughero"),
        ("la documentazionREACHa", "la documentazione REACH"),
        ("noto per la schiumPVCe", "noto per la schiuma di PVC"),
        ("30.000–40,000 ㎡e", "30.000–40.000 ㎡"),
        ("circa1.1 kg", "circa 1,1 kg"),
        ("circa2.4 kg", "circa 2,4 kg"),
    ],
    "es": [
        ("las alfombrTPEes", "las esterillas de TPE"),
        ("Las alfombrPUes y de caucho natural", "Las esterillas de PU y de caucho natural"),
    ],
    "fr": [
        ("environ1.1 kg", "environ 1,1 kg"),
        ("environ2.4 kg", "environ 2,4 kg"),
    ],
    "de": [
        ("„EN71“ und „-3“ wurden getestet", "EN71-3 wurde getestet"),
    ],
}

# 统一保留拉丁厂商名后，ja/ko 也一起用；下面这两张表供 zh 之外的写法复核用


# =============================================================== 执行
def fix_listicle_page(lang):
    p = path_of(lang)
    s0 = s = open(p, encoding="utf-8").read()

    def sub_once(pat, repl, label, required=True):
        nonlocal s
        new, n = re.subn(pat, repl, s, count=1, flags=re.S)
        if n == 0 and required:
            errors.append(f"[{lang}] 未匹配: {label}")
        s = new

    # --- 对比表整表重建 ---
    sub_once(r'<table class="cap-table">.*?</table>',
             lambda m: build_table(lang), "cap-table")

    # --- 脚注 ---
    sub_once(r'<p style="font-size:13\.5px[^"]*">.*?</p>',
             lambda m: '<p style="font-size:13.5px;color:#666">' + FOOTNOTE[lang] + "</p>",
             "footnote")

    # --- meta description（og/twitter 的完整长句保留不动）---
    sub_once(r'(<meta name="description" content=").*?(" />)',
             lambda m: m.group(1) + DESC[lang] + m.group(2), "description")

    # --- og:type website → article ---
    sub_once(r'<meta property="og:type" content="(?:website|article)" />',
             '<meta property="og:type" content="article" />', "og:type")

    # --- og:locale（缺失时才补）---
    if 'property="og:locale"' not in s:
        sub_once(r'(<meta property="og:url" content="[^"]+" />)',
                 lambda m: m.group(1) + '\n  <meta property="og:locale" content="'
                           + OG_LOCALE[lang] + '" />', "og:locale")

    # --- 封面图写真实宽高（1920×1249），消 CLS ---
    sub_once(r'(class="article-cover" src="%s/assets/img/factory-building\.webp" )width="480" height="480"'
             % rel_root(lang),
             lambda m: m.group(1) + 'width="1920" height="1249"', "cover-dims", required=False)

    # --- 散文/JSON-LD 机翻损伤 ---
    for old, new in PROSE_FIX.get(lang, []):
        if old in s:
            s = s.replace(old, new)

    # --- 语言页专属：h2 措辞 + ja/ko 的 12 个 h3 ---
    for old, new in H2_FIX.get(lang, []):
        if old in s:
            s = s.replace(old, new, 1)
    if lang in ("ja", "ko"):
        new3 = H3_JA if lang == "ja" else H3_KO
        h3s = re.findall(r'<h3>.*?</h3>', s, re.S)
        if len(h3s) != 12:
            errors.append(f"[{lang}] h3 数量异常 {len(h3s)}")
        else:
            for old_h, new_h in zip(h3s, new3):
                s = s.replace(old_h, "<h3>" + new_h + "</h3>", 1)

    # --- EN 页专属：补中文内容块 ---
    if lang == "en":
        if '<div class="lang-zh">' not in s:
            anchor = '          </div>\n        </div>\n      </article>'
            if anchor not in s:
                errors.append("[en] 找不到中文块插入锚点")
            else:
                zh = ZH_BLOCK.replace("@@ZH_TABLE@@", build_table("zh"))
                s = s.replace(anchor, '          </div>\n        </div>\n' + zh + '      </article>', 1)
        # 中文标题用 <h1>，与站内另外 9 篇博客的中文块写法保持一致
        # （每个语言模式下各有一个可见 h1；DOM 里两个 h1 是本站既有约定）
        s = s.replace('<h2 class="post-title">2026 中国 12 大瑜伽垫制造商：六大产区集群横评</h2>',
                      '<h1>2026 中国 12 大瑜伽垫制造商：六大产区集群横评</h1>')

    if s != s0:
        open(p, "w", encoding="utf-8").write(s)
        print(f"  [{lang}] 已更新")
    else:
        print(f"  [{lang}] 无变化（已是最新）")


def wrap_en_and_move_zh(p, label):
    """把 EN 正文包进 .lang-en，并把 .lang-zh 挪回 .container 内、补齐 </article>。

    这些页面的原始结构是：.container 在 <div class="lang-zh"> 之前就闭合了，
    于是中文版渲染时完全没有容器约束（无 max-width、无左右留白），
    而英文正文又因为没有 .lang-en 包裹在中文模式下不会隐藏 —— 两个 h1、中英并列。
    """
    s0 = s = open(p, encoding="utf-8").read()
    if '<div class="lang-zh">' not in s:
        errors.append(f"[{label}] 缺 lang-zh，跳过")
        return
    if '<div class="lang-en">' in s.split('<div class="lang-zh">')[0]:
        print(f"  [{label}] 已处理，跳过")
        return

    zi = s.index('<div class="lang-zh">')
    head, tail = s[:zi], s[zi:]

    m = re.search(r'<a class="back-link" href="\.\./blog\.html">.*?</a>\n', head, re.S)
    if not m:
        errors.append(f"[{label}] 找不到 back-link")
        return
    head = head[:m.end()] + '        <div class="lang-en">\n' + head[m.end():]

    # 收紧头部尾部：统一成「article-body 闭合 + lang-en 闭合」，把提前闭合 .container
    # 的那一层摘掉，改由 lang-zh 之后再关
    m2 = re.search(r'\n\s*</div>\n(?:\s*</article>\n)?\s*</div>\n(?:\s*\n)*$', head)
    if not m2:
        errors.append(f"[{label}] 尾部结构不匹配: {head[-70:]!r}")
        return
    head = head[:m2.start()] + '\n          </div>\n        </div>\n'

    tail = re.sub(r'(\n\s*</div>\n)(\s*</section>)',
                  r'\1      </article>\n    </div>\n\2', tail, count=1)

    s = head + tail
    if s != s0:
        open(p, "w", encoding="utf-8").write(s)
        print(f"  [{label}] 已修")


def fix_old_blog_pages():
    files = ["7day-sampling.html", "compliance.html", "custom-sizes.html", "moq-explained.html",
             "tpe-vs-pu.html", "vet-factory.html", "yoga-mat-materials.html",
             "yoga-mat-spec-guide.html", "private-label-yoga-mats.html"]
    for f in files:
        wrap_en_and_move_zh(os.path.join(ROOT, "blog", f), "blog/" + f)


print("== 1) 榜单页 7 语言 ==")
for L in LANGS:
    fix_listicle_page(L)

print("== 2) 8 篇旧博客语言块 ==")
fix_old_blog_pages()

# =============================================================== 自检
print("== 3) 自检 ==")
BAD_WORDS = ["収容人数", "수용 인원", "スタジオ品質の録音", "스튜디오급 녹음",
             "Aufnahmen in Studioqualität", "Enregistrements de qualité studio",
             "Grabaciones con calidad de estudio", "Corsette da livello",
             "TPEe", "TPEo", "TPEPUo", "4 Zeilen", "㎡e", "㎡o", "㎡ ans", "4行", "4줄",
             "alfombrTPE", "alfombrPU", "tappetTPE", "schiumPVC", "documentazionREACH",
             "circa1.1", "circa2.4", "environ1.1", "environ2.4", "„EN71“"]
VOID = {"img", "br", "meta", "link", "input", "hr", "source"}
OLD_BLOG = ["7day-sampling.html", "compliance.html", "custom-sizes.html", "moq-explained.html",
            "tpe-vs-pu.html", "vet-factory.html", "yoga-mat-materials.html",
            "yoga-mat-spec-guide.html", "private-label-yoga-mats.html"]


def parent_chain(html):
    """返回首个 .lang-zh 的祖先链 [(tag, class)]，用于确认它没被放到 .container 外面"""
    from html.parser import HTMLParser

    class P(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.stack = []
            self.found = None

        def handle_starttag(self, t, a):
            cls = dict(a).get("class", "")
            if "lang-zh" in cls and self.found is None:
                self.found = list(self.stack)
            if t not in VOID:
                self.stack.append((t, cls))

        def handle_endtag(self, t):
            if any(x[0] == t for x in self.stack):
                while self.stack and self.stack[-1][0] != t:
                    self.stack.pop()
                if self.stack:
                    self.stack.pop()

    q = P()
    q.feed(html)
    return q.found


def check(label, p, is_listicle):
    s = open(p, encoding="utf-8").read()
    no = len(re.findall(r'<div[\s>]', s))
    nc = len(re.findall(r'</div>', s))
    h1 = len(re.findall(r'<h1[\s>]', s))
    th = len(re.findall(r'<th>', s))
    td = len(re.findall(r'<td>', s))
    flag = []
    if no != nc:
        flag.append(f"div 失衡 {no}/{nc}")
    if is_listicle:
        # EN 页含中英两张表；语言页一张
        want_th, want_td = (12, 144) if label.startswith("blog/") else (6, 72)
        want_h1 = 2 if label.startswith("blog/") else 1
        if h1 != want_h1:
            flag.append(f"h1={h1}(期望{want_h1})")
        if th != want_th:
            flag.append(f"th={th}(期望{want_th})")
        if td != want_td:
            flag.append(f"td={td}(期望{want_td})")
    else:
        if h1 > 2:
            flag.append(f"h1={h1}")
        if '<div class="lang-en">' not in s:
            flag.append("缺 lang-en")
        chain = parent_chain(s) or []
        if not any("container" in c for _, c in chain):
            flag.append("lang-zh 在 .container 外: " + str([t for t, _ in chain]))
    bad = [w for w in BAD_WORDS if w in s]
    if bad:
        flag.append("坏词残留:" + ",".join(bad))
    print(("  ✅ " if not flag else "  ❌ ")
          + f"{label:44} div={no}/{nc} h1={h1} th={th} td={td}"
          + ("  " + "; ".join(flag) if flag else ""))
    if flag:
        errors.append(f"{label}: " + "; ".join(flag))


for L in LANGS:
    lbl = ("blog/" if L == "en" else L + "/blog/") + SLUG + ".html"
    check(lbl, path_of(L), True)

for f in OLD_BLOG:
    check("blog/" + f, os.path.join(ROOT, "blog", f), False)

# 全站扫一遍：正文页不允许出现「语言块单边」（切中文白页 / 中文模式中英重复）
others = []
for root, dirs, files in os.walk(ROOT):
    if any(x in root for x in (".git", "node_modules", "i18n_build", "outputs", "__pycache__",
                               ".workbuddy")):
        continue
    for f in files:
        if f.endswith(".html"):
            others.append(os.path.join(root, f))
only_en, only_zh = [], []
for p in others:
    s = open(p, encoding="utf-8").read()
    if "article-body" not in s and "pd-wrap" not in s:
        continue
    he = '<div class="lang-en">' in s
    hz = '<div class="lang-zh">' in s
    if he and not hz:
        only_en.append(os.path.relpath(p, ROOT))
    elif hz and not he:
        only_zh.append(os.path.relpath(p, ROOT))
print()
print("  全站 only-en 正文页:", only_en or "（无）")
print("  全站 only-zh 正文页:", only_zh or "（无）")
if only_en or only_zh:
    errors.append("仍有语言块单边页: %s %s" % (only_en, only_zh))

print()
if errors:
    print("❌ 有 %d 项未通过：" % len(errors))
    for e in errors:
        print("   -", e)
    sys.exit(1)
print("✅ 全部通过")
