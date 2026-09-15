#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SANFAN 多语言翻译引擎

主引擎 : DeepL API (tag_handling=xml + ignore_tags 保护术语，质量最佳)
备引擎 : MyMemory Public API (无 key，质量一般且每日配额有限)

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
MYMEMORY_EMAIL = "zenglinggun@gmail.com"
MYMEMORY_API = "https://api.mymemory.translated.net/get"

_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or os.environ.get("https_proxy")
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({"http": _proxy, "https": _proxy})) \
    if _proxy else urllib.request.build_opener()

_lock = threading.Lock()
_cache = {}
_dirty = {"n": 0}
_stats = {"deepl": 0, "mymemory": 0, "fail": 0, "chars": 0}
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
    # "Specialty" 是本族的产品线名（双向梯床 + Gyrotonic 塔等非常规件）。
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
    ("gyrotonic",       "Gyrotonic",       "Gyrotonic",       "Gyrotonic",       "Gyrotonic",       "ジャイロトニック",   "자이로토닉"),
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


def _call_batch(texts, lang, src="EN"):
    """主引擎失败则降级备引擎"""
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
        return out

    batches = [todo[i:i + DEEPL_BATCH] for i in range(0, len(todo), DEEPL_BATCH)]

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
                if _looks_translatable(lines[i]) and v.strip() == lines[i].strip():
                    out[i] = lines[i]
                    _stats["fail"] += 1     # 不写缓存，下次还能重翻
                    continue
                out[i] = v
                _cache[_ck(lines[i], lang, src)] = v
        return len(batch)

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=min(DEEPL_WORKERS, len(batches))) as ex:
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
    return out


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
    return dict(_stats)


def flush():
    _save_cache(force=True)
