#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SANFAN 多语言翻译引擎

主引擎 : GLM glm-5.3-flash（2026-10-02 起；行号锚定+完整性校验，见 translator_glm.py）
备引擎 : DeepL API（双 key 额度均已耗尽，仅作 GLM 失败时的备胎）→ MyMemory Public API
术语   : GLM 走 system prompt（GLOSSARY 原样交付）；DeepL 走 <xN> 标签 + ignore_tags

术语保护机制:
  把受保护内容包成 <x0>TPE</x0> 形式，配合 DeepL 的 ignore_tags 让引擎原样保留。
  相比字符串占位符(如 ZXQTM0QXZ)，标签方案不会干扰引擎对句子的理解。
  行业术语表同理：<x1>Faszienrollen</x1> 直接写入目标语译法，引擎不再改动。
"""
import os, re, json, time, hashlib, threading
import urllib.parse, urllib.request, urllib.error

CACHE_PATH = os.path.join(os.path.dirname(__file__), "cache", "translations.json")


def _load_deepl_key():
    """DeepL key 只从环境变量或 .deepl_key 读取，禁止硬编码进代码（会被 GitHub 密钥扫描拦截推送）"""
    k = os.environ.get("DEEPL_API_KEY", "").strip()
    if k:
        return k
    kf = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".deepl_key")
    if os.path.exists(kf):
        return open(kf, encoding="utf-8").read().strip()
    return ""


DEEPL_KEY = _load_deepl_key()
# DeepL Free key 以 :fx 结尾，必须走 api-free 域名
DEEPL_URL = ("https://api-free.deepl.com/v2/translate"
             if DEEPL_KEY.endswith(":fx") else "https://api.deepl.com/v2/translate")
DEEPL_BATCH = 50          # 单次请求最多 50 条 text
DEEPL_WORKERS = 4         # 并发
# GLM 主引擎的并发：思考模型单请求延迟高（10-20s/批），实测 4 并发下
# 90 页生成要数小时 → 提到 8。429 由 _glm_call 的退避重试兜住。
GLM_WORKERS = int(os.environ.get("GLM_WORKERS", "8"))
MYMEMORY_EMAIL = "zenglinggun@gmail.com"
MYMEMORY_API = "https://api.mymemory.translated.net/get"

_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or os.environ.get("https_proxy")
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({"http": _proxy, "https": _proxy})) \
    if _proxy else urllib.request.build_opener()

_lock = threading.Lock()
_cache = {}
_dirty = {"n": 0}
_stats = {"glm": 0, "deepl": 0, "mymemory": 0, "fail": 0, "chars": 0}
_quota_exhausted = False

# ---------------------------------------------------------------- 术语保护
# 只锁"译错会造成硬伤"的内容：品牌、认证、材料、数值+单位。
# MOQ/OEM/ODM/FOB 等通用商业缩写**不锁**——DeepL 会本地化处理得更好
# （Mindestbestellmenge / 最小注文数量（MOQ）/ 최소 주문 수량(MOQ)），
# 且锁太多会让引擎看不懂句子结构而误译（曾出现把逗号列表译成"符合…标准"）。
WORD_TERMS = [
    r"TPE", r"PVC", r"NBR", r"PU", r"EVA", r"SBR", r"TPEE", r"NR",
    r"REACH", r"CA\s?Prop\s?65", r"Prop\s?65", r"EN\s?71", r"OEKO-?TEX", r"SGS",
    r"BSCI", r"ISO\s?9001", r"RoHS", r"CPSIA", r"Intertek", r"TUV",
    r"SANFAN", r"三梵",
    # 只锁尺寸/重量单位；pcs/pieces 不锁，让引擎本地化为 Stück/個/개 更自然
    r"\d+(?:\.\d+)?\s?(?:mm|cm|m|kg|g)\b",
]
# 数值+单位整体（不能加 \b：㎡ 非 \w；曾导致 "12,000㎡" 被误译成 "12.000 €"）
PHRASE_TERMS = [
    r"\d[\d,.\s]*(?:㎡|m²|sqm|sq\.?m)",
    r"\d[\d,.\s]*(?:ft²|sqft|sq\.?ft)",
    r"\d+\s?[x×]\s?\d+(?:\s?[x×]\s?\d+)?(?:\s?(?:mm|cm))?",
]
_PROT_RE = re.compile(
    r"\b(?:" + "|".join("(?:%s)" % p for p in WORD_TERMS) + r")\b|(?:" +
    "|".join("(?:%s)" % p for p in PHRASE_TERMS) + r")", re.IGNORECASE)

# 行业术语表：避免机翻错译（如 aerial yoga hammock 被翻成普通"吊床"）
# ---------------------------------------------------------------- 行业术语表
# ⚠️ 2026-09-16 补 fr / it / es 三语（原先只有 de/ja/ko）：
#    同一批品类词在三语里没有背书，DeepL 各译各的，站内出现多种说法；
#    下列译法**取自站内已上线且正确的页面**（不是新造），目的是把它们固定下来。
# ⚠️ 同时补 `figure 8` —— 实测 de/fr/it/es/ja/ko 全把这个"8 字"理解成"插图 8"：
#    `Figure 8 Resistance Bands` → de「Abbildung 8: Widerstandsbänder」、
#    fr「Figure 8 : Bandes de résistance」、ja「図8 レジスタンスバンド」，
#    6 个语言版本全错。这是**形状**不是**图号**，必须锁住。
GLOSSARY = {
    "de": {
        r"aerial yoga hammocks?": "Aerial-Yoga-Tücher",
        r"yoga hammocks?": "Yoga-Tücher",
        r"foam rollers?": "Faszienrollen",
        r"yoga props?": "Yoga-Zubehör",
        r"resistance bands?": "Widerstandsbänder",
        r"7-day sampling": "Muster in 7 Tagen",
        r"free samples?": "kostenlose Muster",
        r"factory direct": "direkt ab Werk",
        r"figure[- ]?8 resistance bands?": "Widerstandsbänder in Achtform",
        r"resistance loop bands?": "Widerstandsschlaufe",
        r"resistance tubes?": "Widerstandsschlauch",
        r"power bands?": "Power Band",
        r"packing lists?": "Packliste",
    },
    "ja": {
        r"aerial yoga hammocks?": "エアリアルヨガハンモック",
        r"yoga hammocks?": "ヨガハンモック",
        r"foam rollers?": "フォームローラー",
        r"yoga props?": "ヨガプロップス",
        r"resistance bands?": "レジスタンスバンド",
        r"7-day sampling": "7日間サンプル作成",
        r"free samples?": "無料サンプル",
        r"factory direct": "工場直販",
        r"figure[- ]?8 resistance bands?": "8の字レジスタンスバンド",
        r"resistance loop bands?": "レジスタンスループバンド",
        r"resistance tubes?": "レジスタンスチューブ",
        r"power bands?": "パワーバンド",
        r"packing lists?": "パッキングリスト",
    },
    "ko": {
        r"aerial yoga hammocks?": "에어리얼 요가 해먹",
        r"yoga hammocks?": "요가 해먹",
        r"foam rollers?": "폼롤러",
        r"yoga props?": "요가 소품",
        r"resistance bands?": "저항 밴드",
        r"7-day sampling": "7일 샘플 제작",
        r"free samples?": "무료 샘플",
        r"factory direct": "공장 직거래",
        r"figure[- ]?8 resistance bands?": "8자 저항 밴드",
        r"resistance loop bands?": "저항 루프 밴드",
        r"resistance tubes?": "저항 튜브",
        r"power bands?": "파워 밴드",
        r"packing lists?": "패킹 리스트",
    },
    "fr": {
        r"aerial yoga hammocks?": "hamacs de yoga aérien",
        r"yoga hammocks?": "hamacs de yoga",
        r"foam rollers?": "rouleaux en mousse",
        r"yoga props?": "accessoires de yoga",
        r"resistance bands?": "bandes de résistance",
        r"7-day sampling": "échantillons en 7 jours",
        r"free samples?": "échantillons gratuits",
        r"factory direct": "direct d'usine",
        r"figure[- ]?8 resistance bands?": "bandes de résistance en huit",
        r"resistance loop bands?": "bande élastique de résistance",
        r"resistance tubes?": "tube de résistance",
        r"exercise bands?": "bandes d'entraînement",
        r"packing lists?": "liste de colisage",
        r"power bands?": "Power Band",
    },
    "it": {
        r"aerial yoga hammocks?": "amache da yoga aeree",
        r"yoga hammocks?": "amache da yoga",
        r"foam rollers?": "rulli in schiuma",
        r"yoga props?": "accessori yoga",
        r"resistance bands?": "fasce elastiche",
        r"7-day sampling": "campionatura in 7 giorni",
        r"free samples?": "campioni gratuiti",
        r"factory direct": "direttamente dalla fabbrica",
        r"figure[- ]?8 resistance bands?": "fasce elastiche a forma di 8",
        r"resistance loop bands?": "fascia elastica ad anello",
        r"resistance tubes?": "elastico di resistenza",
        r"exercise bands?": "fasce elastiche per esercizi",
        r"packing lists?": "lista di imballaggio",
        r"power bands?": "Power Band",
    },
    "es": {
        r"aerial yoga hammocks?": "hamacas de yoga aéreas",
        r"yoga hammocks?": "hamacas de yoga",
        r"foam rollers?": "rodillos de espuma",
        r"yoga props?": "accesorios de yoga",
        r"resistance bands?": "bandas elásticas de resistencia",
        r"7-day sampling": "muestras en 7 días",
        r"free samples?": "muestras gratuitas",
        r"factory direct": "directo de fábrica",
        r"figure[- ]?8 resistance bands?": "bandas de resistencia en forma de 8",
        r"resistance loop bands?": "banda elástica de resistencia",
        r"resistance tubes?": "tubo de resistencia",
        r"exercise bands?": "bandas elásticas para ejercicio",
        r"packing lists?": "lista de embalaje",
        r"power bands?": "Power Band",
    },
}

# ---------------------------------------------------------------- 普拉提器械专名
# 2026-09-15 实测：不加表时 DeepL 会按**字面**硬译器械名 ——
#   de: "Pilates Wunda Chair" → "Pilates-Wunda-Stuhl"（Wunda 是创始品牌名，不是"椅子"）
#       "Pilates Ladder Barrel" → "Pilates-Leiter-Fass"（Leiter-Fass = 梯子+桶，纯字面）
#   ja/ko 反而译得对（ワンダチェア / 래더 배럴），但同样要固定下来免得漂移。
# 这些是**行业内既有的叫法**，不是新造词：欧陆一律沿用英文原名（Deutsch 的采购
# 目录里就是 "Wunda Chair"/"Ladder Barrel"），日语、韩语用各自片假名/谚文表记。
# 走 GLOSSARY 通道 → 被包成 <xN> 保护标签，引擎原样保留，不做词形变化。
PILATES_TERMS = {}
_PL_LANGS = ("de", "fr", "it", "es", "ja", "ko")

# ⭐ 整族名必须**整体**保护，不能只护词根。
#   2026-09-15 实测：只护 "wunda chair" 时法语会把碎片当名词短语补介词 ——
#     "Pilates Wunda Chair" → "Pilates àWunda Chair"（à 直接粘在词上）
#     "Pilates Ladder Barrel" → "Pilates à l'Ladder Barrel"
#   把「Pilates + 器械名」当一整个受保护单元后，引擎没有插入介词的位置。
# ⚠️ 顺序即优先级：本表**全部**排在 _PL_SHORT 之前，长词先匹配。
_PL_FAMILY = [
    #                EN（全族名）                de                        fr                        it                        es                         ja                          ko
    ("pilates reformer",        "Pilates-Reformer",        "Pilates Reformer",        "Pilates Reformer",        "Pilates Reformer",        "ピラティス リフォーマー",     "필라테스 리포머"),
    ("pilates cadillac",        "Pilates-Cadillac",        "Pilates Cadillac",        "Pilates Cadillac",        "Pilates Cadillac",        "ピラティス キャデラック",     "필라테스 캐딜락"),
    ("pilates wunda chair",     "Pilates-Wunda Chair",     "Pilates Wunda Chair",     "Pilates Wunda Chair",     "Pilates Wunda Chair",     "ピラティス ワンダチェア",     "필라테스 원다 체어"),
    ("pilates ladder barrel",   "Pilates-Ladder Barrel",   "Pilates Ladder Barrel",   "Pilates Ladder Barrel",   "Pilates Ladder Barrel",   "ピラティス ラダーバレル",     "필라테스 래더 배럴"),
    ("pilates spine corrector", "Pilates-Spine Corrector", "Pilates Spine Corrector", "Pilates Spine Corrector", "Pilates Spine Corrector", "ピラティス スパインコレクター", "필라테스 스파인 코렉터"),
    ("pilates studio set",      "Pilates-Studio-Set",      "Pilates Studio Set",      "Pilates Studio Set",      "Pilates Studio Set",      "ピラティス スタジオセット",   "필라테스 스튜디오 세트"),
    # "Specialty" 是本族的产品线名（双向梯床 + 回旋仪塔架等非常规件）。
    # 直译会错：de 得到 "Spezialisierung"（专精化）、ja 得到 "専門コース"（专业课）。
    ("pilates specialty",       "Pilates-Spezialgeräte",   "Pilates Spécialités",     "Pilates Specialità",      "Pilates Especialidades",  "ピラティス スペシャルティ",   "필라테스 스페셜티"),
    ("reformer tower & 3-in-1", "Reformer Tower & 3-in-1", "Reformer Tower & 3-in-1", "Reformer Tower & 3-in-1", "Reformer Tower & 3-in-1", "リフォーマー タワー＆3-in-1", "리포머 타워 & 3-in-1"),
]
# 词根级：用于「Pilates Wunda Chair」以外的散用（如 "Rubberwood Cadillac"、"
# Trapeze Table" 旁注），以及导航/规格表里的单独出现。
_PL_SHORT = [
    ("wunda chair",     "Wunda Chair",     "Wunda Chair",     "Wunda Chair",     "Wunda Chair",     "ワンダチェア",       "원다 체어"),
    ("ladder barrel",   "Ladder Barrel",   "Ladder Barrel",   "Ladder Barrel",   "Ladder Barrel",   "ラダーバレル",       "래더 배럴"),
    ("spine corrector", "Spine Corrector", "Spine Corrector", "Spine Corrector", "Spine Corrector", "スパインコレクター", "스파인 코렉터"),
    ("ladder bed",      "Ladder Bed",      "Ladder Bed",      "Ladder Bed",      "Ladder Bed",      "ラダーベッド",       "래더 베드"),
    ("reformer",        "Reformer",        "Reformer",        "Reformer",        "Reformer",        "リフォーマー",       "리포머"),
    ("cadillac",        "Cadillac",        "Cadillac",        "Cadillac",        "Cadillac",        "キャデラック",       "캐딜락"),
    # ⛔ 2026-10-01 移除 "gyrotonic" 条：该词是美国注册商标，已全站剔除。
    #    术语保护表里留着它 = 「随时可能被翻译管线重新注入」。
    #    不再保护的词，才不会被带回来。
]
for _row in _PL_FAMILY + _PL_SHORT:
    for _i, _lg in enumerate(_PL_LANGS):
        PILATES_TERMS.setdefault(_lg, {})[_row[0]] = _row[_i + 1]

for _lg, _terms in PILATES_TERMS.items():
    GLOSSARY.setdefault(_lg, {}).update(_terms)
del _lg, _terms, _row, _i

_GLOSS_RE = {lg: re.compile("|".join("(?P<g%d>%s)" % (i, p) for i, p in enumerate(pats)), re.I)
             for lg, pats in GLOSSARY.items()}


def _xml_escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _xml_unescape(s):
    return s.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


def protect(text, lang=None):
    """把受保护术语/行业术语包成 <xN>...</xN>，返回 (新文本, 最大编号)"""
    if not text:
        return text, -1
    n = [0]

    def _mk(val):
        i = n[0]
        n[0] += 1
        return "<x%d>%s</x%d>" % (i, val, i)

    out = _xml_escape(text)
    out = _PROT_RE.sub(lambda m: _mk(m.group(0)), out)
    if lang in _GLOSS_RE:
        grx = _GLOSS_RE[lang]
        pats = list(GLOSSARY[lang].keys())

        def _grep(m):
            for i, p in enumerate(pats):
                if m.group("g%d" % i) is not None:
                    return _mk(GLOSSARY[lang][p])
            return m.group(0)

        out = grx.sub(_grep, out)
    return out, n[0] - 1


def restore(text, mapping=None):
    """剥离保护标签并还原 XML 实体"""
    if not text:
        return text
    text = re.sub(r"</?x\d+>", "", text)
    return _xml_unescape(text)


# ---------------------------------------------------------------- 缓存
def _load_cache():
    global _cache
    if os.path.exists(CACHE_PATH):
        try:
            _cache = json.load(open(CACHE_PATH, encoding="utf-8"))
        except Exception:
            _cache = {}


def _save_cache(force=False):
    _dirty["n"] += 1
    if force or _dirty["n"] >= 20:
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        json.dump(_cache, open(CACHE_PATH, "w", encoding="utf-8"), ensure_ascii=False)
        _dirty["n"] = 0


_load_cache()

ENGINE_TAG = "deepl"


def _ck(text, lang, src="EN"):
    """⚠️ lang/src 必须统一大小写：2026-09-12 曾因调用方一会儿传 'de' 一会儿传 'DE'，
    同一个句子在缓存里存成两套键（en>de 2411 条 vs en>DE 122 条），
    而写入 'de' 的那批正好是兜底引擎的回声（英文），导致重跑永远命中脏缓存。"""
    return "%s:%s>%s:%s" % (ENGINE_TAG, src.lower(), lang.lower(),
                            hashlib.md5(text.encode("utf-8")).hexdigest())


# ---------------------------------------------------------------- DeepL
# 不是实体的裸 & （后面不是 amp; / lt; / #123; 之类）
_BARE_AMP = re.compile(r"&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9A-Fa-f]+);)")


def _deepl_call(texts, lang, src="EN"):
    """texts: 原文列表 -> (译文列表, error)。lang: 目标语 de/ja/ko/en；src: 源语"""
    prepped, max_idx = [], -1
    for t in texts:
        p, mi = protect(t, lang)
        # ⭐ 裸 & 在 tag_handling=xml 下是非法 XML，DeepL 会**原样返回整句**
        # （不报错、不降级，静默回声）——2026-09-12 有 53 个产品页的标题/正文
        # 因为 "…Yoga & Fitness Manufacturer" 里的 & 全部没翻。
        # 只要 protect() 加了 <x0> 标签就会走 xml 模式，所以统一把裸 & 转义。
        if mi >= 0:
            p = _BARE_AMP.sub("&amp;", p)
        prepped.append(p)
        max_idx = max(max_idx, mi)
    body = {"text": prepped, "source_lang": src.upper(), "target_lang": lang.upper()}
    if max_idx >= 0:
        body["tag_handling"] = "xml"
        body["ignore_tags"] = ["x%d" % i for i in range(max_idx + 1)]
    req = urllib.request.Request(
        DEEPL_URL, data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": "DeepL-Auth-Key " + DEEPL_KEY,
                 "Content-Type": "application/json"})
    raw = _opener.open(req, timeout=45).read().decode("utf-8")
    d = json.loads(raw)
    return [restore(x["text"]) for x in d["translations"]], None


def _mymemory_call(texts, lang):
    """兜底引擎：逐条调用 MyMemory"""
    out = []
    for t in texts:
        params = urllib.parse.urlencode({"q": t, "langpair": "en|" + lang, "de": MYMEMORY_EMAIL})
        try:
            raw = _opener.open(MYMEMORY_API + "?" + params, timeout=30).read().decode("utf-8")
            d = json.loads(raw)
            out.append(d["responseData"]["translatedText"] if str(d.get("responseStatus")) == "200" else t)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                return None, "QUOTA"
            out.append(t)
        except Exception:
            out.append(t)
    return out, None


# 2026-10-02 起主引擎 = GLM（DeepL 免费额度双 key 均已耗尽）；GLM 内部自带
# 行号锚定 + 完整性校验 + 重试，校验不过返回 None 才轮到 DeepL/MyMemory。
from translator_glm import glm_call as _glm_call, GLM_KEY as _GLM_KEY, \
    _EN_MARK as _EN_MARK_SRC

# 型号 SKU 保护（10-02 全量跑批实测）：型号名任何语言都原样保留。
# "Chair 1-A" 被翻成 "Stuhl 1-A" 才是真错误——型号是编号不是词。
# 数据源 = pilates_figures（80 个已上线型号，与站点 SSOT 同源）。
try:
    from pilates_figures_20261002 import ROWS as _PF_ROWS
    _PF_IDENT = {m.strip(): m.strip() for m, _tr, _kg, _pg in _PF_ROWS
                 if 2 <= len(m.strip()) <= 40}
except Exception:
    _PF_IDENT = {}
_GLOSSARY_GLM = ({lg: {**d, **_PF_IDENT} for lg, d in GLOSSARY.items()}
                 if _PF_IDENT else GLOSSARY)


def _call_batch(texts, lang, src="EN"):
    """主引擎失败则降级备引擎（2026-10-02 起：GLM → DeepL → MyMemory）

    ⚠️ GLM 路线不走 protect()/`<xN>` 标签：术语以 system prompt 交付（见 translator_glm）。
    ⚠️ 缓存键 ENGINE_TAG 仍是历史值 "deepl"，**故意不改**——改了 = 全站缓存失效 =
       下次构建把几千个已上线页面全部重翻（回归风险）。标签名不代表引擎。
    """
    if _GLM_KEY:
        try:
            res, err = _glm_call(texts, lang, src=src, glossary=_GLOSSARY_GLM)
            if res is not None:
                with _lock:
                    _stats["glm"] += len(texts)
                    _stats["chars"] += sum(len(t) for t in texts)
                return res
            print("[GLM] 批次校验未过: %s" % err)
        except Exception as e:
            print("[GLM] %s: %s" % (type(e).__name__, str(e)[:100]))
        # ⭐ 拆分重试（10-02）：批校验不过/异常 → 对半拆各自重试，拆到单行为止。
        #   es 轮实测两种整批降级：25 行批输出截断（finish=length）、12 行批
        #   模型丢行（重喂 3 次仍缺 #12）。整批降级 = MyMemory 污染缓存；
        #   拆到单行后几乎不可能失败 → GLM 纯度 100%，备引擎只剩
        #   「单行仍失败」这一极窄路径。
        if len(texts) > 1:
            mid = len(texts) // 2
            a = _call_batch(texts[:mid], lang, src=src)
            b = _call_batch(texts[mid:], lang, src=src)
            if a is not None and b is not None:
                return a + b
            return None          # 某单行仍失败 → 整批按失败走（不写缓存）
    try:
        res, err = _deepl_call(texts, lang, src=src)
        if not err:
            with _lock:
                _stats["deepl"] += len(texts)
                _stats["chars"] += sum(len(t) for t in texts)
            return res
    except urllib.error.HTTPError as e:
        if e.code in (429, 456):          # 限流 / 额度耗尽
            print("[DeepL] HTTP %s，降级 MyMemory" % e.code)
        else:
            print("[DeepL] HTTP %s: %s" % (e.code, e.read().decode()[:120]))
    except Exception as e:
        print("[DeepL] %s: %s" % (type(e).__name__, str(e)[:100]))
    res, err = _mymemory_call(texts, lang)
    if err == "QUOTA":
        with _lock:
            _stats["fail"] += len(texts)
        return None
    with _lock:
        _stats["mymemory"] += len(texts)
    return res


# ---------------------------------------------------------------- 译文出口修复
# ⭐ 规则表在 term_repair.py（与 i18n_build/fix_glue_20260916.py 共用同一份）。
# 为什么病根在管线：受保护术语被包成 <xN>…</xN> 后交给 DeepL ignore_tags，
# 引擎**看不到术语首字母**，于是自己猜语法 ——
#   fr `Tapis de yoga « Lilac » d'TPE`（应 TPE «Lilac»；d' 是错的省音）
#   it `in gommPUe`（应 in gomma PU）、es `«Alignment Line»TPE`（漏空格）
#   es `No contiene bifeniloPVC`（EN 只是 contains no PVC，bifenilo「联苯」是凭空编的）
# 只修存量页面不够 —— 重生成会原样再犯，所以必须在译文出口拦一道。
from term_repair import repair as _repair_term


def _repair_out(values, lang):
    """对一批译文套用该语言的修复规则。

    ⚠️ 必须放在**出口**而不是入口：缓存里存的是历史译文，其中有大量未修的坏串。
       若只在「新翻译」上修，命中缓存的老页面依旧带病。放出口则
       「新翻 / 缓存命中 / 回退英文」三条路径一次覆盖。
    ⚠️ 必须先于缓存写入做，也不能改历史缓存键 —— repair() 幂等，重复套用无副作用。
    """
    return [_repair_term(v, lang) if v else v for v in values]


def _looks_translatable(s):
    """是否「应该被翻掉」——用于识别回声。

    品牌名/材质缩写（SANFAN、TPE、EVA、6 mm）本来就该原样保留，
    译文等于原文是正常的；只有「多词长句也原样返回」才是引擎失败。
    """
    s = (s or "").strip()
    if len(s) < 8:
        return False
    if not re.search(r"[A-Za-z]{3,}", s):
        return False
    return len(s.split()) >= 2 or len(s) >= 16


def translate_lines(lines, lang, verbose=False, src="EN"):
    """批量翻译 -> 同长度列表。src 为源语言（回译验证时需指定为目标语）"""
    if lang.lower() == src.lower():
        return list(lines)
    out = [None] * len(lines)
    todo = []
    for i, s in enumerate(lines):
        if not s or not s.strip():
            out[i] = s
            continue
        ck = _ck(s, lang, src)
        if ck in _cache:
            out[i] = _cache[ck]
        else:
            todo.append(i)
    if not todo:
        return _repair_out(out, lang)

    # GLM 主引擎时批次上限 12：25 行实测出现过 finish=length 截断
    # （长博客段落批，10-02 es 轮），截断 → 校验不过 → 降级污染缓存。
    # 50 行实测必超时降级（10-02）；小批次 × 4 并发吞吐反而更高。
    _batch = 12 if _GLM_KEY else DEEPL_BATCH
    _workers = GLM_WORKERS if _GLM_KEY else DEEPL_WORKERS
    batches = [todo[i:i + _batch] for i in range(0, len(todo), _batch)]

    def _do(batch):
        texts = [lines[i] for i in batch]
        res = _call_batch(texts, lang, src=src)
        if res is None:
            for i in batch:
                out[i] = lines[i]
            return 0
        with _lock:
            for i, v in zip(batch, res):
                if v is None:
                    v = lines[i]
                # ⭐ 防「回声污染缓存」：兜底引擎 MyMemory 失败时会原样返回英文，
                # 2026-09-12 第五批就是这样把 54 个产品页写成未翻译的 —— 而且一旦
                # 写进缓存，下次命中缓存连 API 都不调（deepl=0），错误永久固化。
                # 10-02 口径对齐：含英文功能词的回声 = 真失败（不写缓存）；
                # 不含的 = 良性回声（型号 SKU/国际术语，原样即正确）→ 照常写缓存。
                if _looks_translatable(lines[i]) and v.strip() == lines[i].strip():
                    if _EN_MARK_SRC.search(lines[i]):
                        out[i] = lines[i]
                        _stats["fail"] += 1     # 不写缓存，下次还能重翻
                        continue
                    out[i] = v
                    _cache[_ck(lines[i], lang, src)] = v
                    continue
                out[i] = v
                _cache[_ck(lines[i], lang, src)] = v
        return len(batch)

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=min(_workers, len(batches))) as ex:
        done = 0
        for n in ex.map(_do, batches):
            done += n
            if verbose:
                print("  translated %d / %d" % (done, len(todo)), flush=True)

    missing = sum(1 for i in range(len(out)) if out[i] is None)
    for i in range(len(out)):
        if out[i] is None:
            out[i] = lines[i]        # 回退英文，且**不写缓存**，便于后续补翻
    _save_cache(force=True)
    if missing:
        print("[WARN] %s: %d/%d 条未取得译文，已回退英文" % (lang, missing, len(lines)))
    return _repair_out(out, lang)


def translate_one(text, lang):
    return translate_lines([text], lang)[0]


def back_translate(text, lang):
    """把译文翻回英文，用于回译语义一致性验证（需显式指定源语言，否则 DeepL 会原样返回）"""
    return translate_lines([text], "en", src=lang.upper())[0] if text else text


def usage():
    try:
        req = urllib.request.Request(
            ("https://api-free.deepl.com/v2/usage" if DEEPL_KEY.endswith(":fx")
             else "https://api.deepl.com/v2/usage"),
            headers={"Authorization": "DeepL-Auth-Key " + DEEPL_KEY})
        return json.loads(_opener.open(req, timeout=25).read().decode())
    except Exception as e:
        return {"error": str(e)[:80]}


def stats():
    d = dict(_stats)
    try:
        from translator_glm import USAGE as _u
        d["glm_requests"] = _u["requests"]
        d["glm_prompt_tok"] = _u["prompt_tokens"]
        d["glm_completion_tok"] = _u["completion_tokens"]
        d["glm_reasoning_tok"] = _u["reasoning_tokens"]
        d["glm_retries"] = _u["retries"]
        d["glm_fallbacks"] = _u["fallbacks"]
    except Exception:
        pass
    return d


def flush():
    _save_cache(force=True)
