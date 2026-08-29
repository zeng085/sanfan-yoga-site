#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SANFAN 多语言翻译引擎
- 数据源: MyMemory Public Translation API (本机环境唯一稳定可达的公开翻译 API)
- 特性: 批量拼接(500B 分块) / 术语保护 / 磁盘缓存 / 失败重试 / 限速
"""
import os, re, json, time, hashlib, urllib.parse, urllib.request, urllib.error, threading

CACHE_PATH = os.path.join(os.path.dirname(__file__), "cache", "translations.json")
CONTACT_EMAIL = "zenglinggun@gmail.com"   # MyMemory 官方 de= 参数，用于提升每日配额
API = "https://api.mymemory.translated.net/get"
MAX_BYTES = 480          # MyMemory 单次 q 上限 ~500 bytes
SLEEP = 0.25             # 礼貌间隔

_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or os.environ.get("https_proxy")
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({"http": _proxy, "https": _proxy})) \
    if _proxy else urllib.request.build_opener()

_lock = threading.Lock()
_cache = {}
_dirty = {"n": 0}
_quota_exhausted = False

# ---------------------------------------------------------------- 术语保护
# 这些词必须在译文中原样保留（B2B 通用缩写 / 认证 / 材料 / 品牌 / 单位）
# 加词边界：否则 PU 会误匹配 "output" 内部、NR 会误匹配 "Faszienrollen" 内部
WORD_TERMS = [
    r"TPE", r"PVC", r"NBR", r"PU", r"EVA", r"SBR", r"TPEE", r"NR",
    r"REACH", r"CA\s?Prop\s?65", r"Prop\s?65", r"EN\s?71", r"OEKO-?TEX", r"SGS",
    r"BSCI", r"ISO\s?9001", r"ISO", r"RoHS", r"CPSIA", r"Intertek", r"TUV",
    r"MOQ", r"OEM", r"ODM", r"FOB", r"CIF", r"EXW", r"DDP", r"B2B",
    r"SANFAN", r"三梵",
    r"\d+(?:\.\d+)?\s?(?:mm|cm|m|kg|g|pcs|pcs\.|pieces?)",
]
# 数值+单位整体（不能加 \b：㎡ 等非 ASCII 字符不构成 \w 边界，
# 且必须连同数字一起保护，否则 "12,000㎡" 会被误译成 "12.000 €"）
PHRASE_TERMS = [
    r"\d[\d,.\s]*(?:㎡|m²|sqm|sq\.?m)",
    r"\d[\d,.\s]*(?:ft²|sqft|sq\.?ft)",
    r"\d+\s?[x×]\s?\d+(?:\s?[x×]\s?\d+)?(?:\s?(?:mm|cm))?",
]
_PROT_RE = re.compile(
    r"\b(?:" + "|".join("(?:%s)" % p for p in WORD_TERMS) + r")\b|(?:" +
    "|".join("(?:%s)" % p for p in PHRASE_TERMS) + r")", re.IGNORECASE)
# 占位符必须用纯 ASCII 大写字母：翻译引擎对非 ASCII 罕见字符(如 ☁)会改写/吞字符
_PLACEHOLDER = "ZXQTM%dQXZ"

# ---------------------------------------------------------------- 行业术语表
# 这些短语按目标语强制映射，避免机翻错译（如 aerial yoga hammock -> "吊床"）
GLOSSARY = {
    "de": {
        r"aerial yoga hammocks?": "Aerial-Yoga-Tücher",
        r"yoga hammocks?": "Yoga-Tücher",
        r"foam rollers?": "Faszienrollen",
        r"yoga props?": "Yoga-Zubehör",
        r"resistance bands?": "Widerstandsbänder",
        r"yoga (?:columns?|pillars?)": "Yoga-Säulen",
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
        r"yoga (?:columns?|pillars?)": "ヨガポール",
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
        r"yoga (?:columns?|pillars?)": "요가 기둥",
        r"7-day sampling": "7일 샘플 제작",
        r"free samples?": "무료 샘플",
        r"factory direct": "공장 직거래",
    },
}
_GLOSS_RE = {lg: re.compile("|".join("(?P<g%d>%s)" % (i, p) for i, p in enumerate(pats)), re.I)
             for lg, pats in GLOSSARY.items()}


def protect(text, lang=None):
    """把受保护术语 + 行业术语替换为占位符，返回 (新文本, {占位符: 还原值})"""
    if not text:
        return text, {}
    mapping = {}

    def _mk(val):
        key = _PLACEHOLDER % len(mapping)
        mapping[key] = val
        return key

    def _rep(m):
        return _mk(m.group(0))

    out = _PROT_RE.sub(_rep, text)

    # 行业术语：占位符还原为目标语译法
    if lang in _GLOSS_RE:
        grx = _GLOSS_RE[lang]
        pats = list(GLOSSARY[lang].keys())

        def _grep(m):
            for i, p in enumerate(pats):
                if m.group("g%d" % i) is not None:
                    return _mk(GLOSSARY[lang][p])
            return m.group(0)

        out = grx.sub(_grep, out)
    return out, mapping


def restore(text, mapping):
    if not text:
        return text
    # 1) 精确还原
    for k, v in mapping.items():
        if k in text:
            text = text.replace(k, v)
    if not mapping:
        return text
    # 2) 宽松还原：翻译引擎可能在占位符内部插入空格（如 ZXQTM0QXZ -> "ZXQTM 0 QXZ"）
    #    要求 "ZX" 相邻开头，正常文本极罕见，避免误伤
    def _loose(m):
        return mapping.get(_PLACEHOLDER % int(m.group(1)), "")
    text = re.sub(r"ZX\s*Q?\s*T?\s*M?\s*(\d+)\s*Q?\s*X?\s*Z?", _loose, text, flags=re.I)
    # 3) 再宽松一档：只剩 "QTM0" / "TM0QXZ" 这类残片
    text = re.sub(r"Q\s*T\s*M\s*(\d+)\s*Q?\s*X?\s*Z?", _loose, text, flags=re.I)
    # 4) 兜底：任何仍残留的占位符直接抹掉，避免泄漏到页面
    text = re.sub(r"ZX\s*Q\s*T\s*M\s*\d+\s*Q\s*X\s*Z", "", text, flags=re.I)
    # 5) 最终兜底：删除被翻译引擎拆散后剩余的孤立残片（QXZ / QTM / ZXQ），
    #    这些三字母组合在正常文本中极罕见，删除安全
    text = re.sub(r"Q\s*X\s*Z|Q\s*T\s*M|Z\s*X\s*Q(?![A-Za-z])", "", text, flags=re.I)
    return text


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


def _ck(text, lang):
    return lang + ":" + hashlib.md5(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- HTTP
def _api_call(q, lp):
    """单次 API 调用，返回 (译文, error)"""
    params = urllib.parse.urlencode({"q": q, "langpair": lp, "de": CONTACT_EMAIL})
    for attempt in range(4):
        try:
            raw = _opener.open(API + "?" + params, timeout=30).read().decode("utf-8")
            d = json.loads(raw)
            if str(d.get("responseStatus")) == "200":
                return d["responseData"]["translatedText"], None
            if "MYMEMORY WARNING" in str(d.get("responseDetails", "")).upper():
                return None, "QUOTA"
            return None, "STATUS_" + str(d.get("responseStatus"))
        except urllib.error.HTTPError as e:
            # 429 = 配额/限流：重试无意义，立即返回，避免整批请求堆积超时
            if e.code == 429:
                return None, "QUOTA"
            if attempt == 3:
                return None, "HTTP_" + str(e.code)
            time.sleep(1.2 * (attempt + 1))
        except Exception as e:
            if attempt == 3:
                return None, "EXC_" + type(e).__name__
            time.sleep(1.2 * (attempt + 1))
    return None, "UNKNOWN"


def _pack(lines):
    """把若干行打包成 <=MAX_BYTES 的块；每行单独超限时按句子再切"""
    chunks, cur = [], []
    for ln in lines:
        cand = cur + [ln]
        if len("\n".join(cand).encode("utf-8")) > MAX_BYTES and cur:
            chunks.append(cur)
            cur = [ln]
        else:
            cur = cand
        # 极端长行：按句切
        if len("\n".join(cur).encode("utf-8")) > MAX_BYTES:
            last = cur.pop()
            chunks.append(cur) if cur else None
            parts = re.split(r"(?<=[.!?;:])\s+", last)
            buf = ""
            for p in parts:
                if len((buf + " " + p).encode("utf-8")) > MAX_BYTES and buf:
                    chunks.append([buf])
                    buf = p
                else:
                    buf = (buf + " " + p).strip()
            cur = [buf] if buf else []
    if cur:
        chunks.append(cur)
    return [c for c in chunks if c]


def translate_lines(lines, lang, verbose=False):
    """批量翻译字符串列表 -> 同长度列表。lang: de/ja/ko/en"""
    if lang == "en":
        return list(lines)
    out = [None] * len(lines)
    todo_idx = []
    for i, s in enumerate(lines):
        if not s or not s.strip():
            out[i] = s
            continue
        ck = _ck(s, lang)
        if ck in _cache:
            out[i] = _cache[ck]
        else:
            todo_idx.append(i)

    if not todo_idx:
        return out

    # 保护术语后按索引顺序打包
    prot_map = {}
    prepared = []
    for i in todo_idx:
        p, m = protect(lines[i], lang)
        prot_map[i] = m
        prepared.append((i, p))

    # 先贪心切块
    blocks, pos = [], 0
    while pos < len(prepared):
        block, blen = [], 0
        while pos < len(prepared):
            i, p = prepared[pos]
            add = len(p.encode("utf-8")) + (1 if block else 0)
            if blen + add > MAX_BYTES and block:
                break
            block.append((i, p))
            blen += add
            pos += 1
        blocks.append(block)

    def _fallback_single(block):
        """整块失败/行数不匹配 -> 逐条降级"""
        for i, p in block:
            t2, _ = _api_call(p, "en|" + lang)
            val = restore(t2, prot_map[i]) if t2 else lines[i]
            with _lock:
                out[i] = val
                if t2:
                    _cache[_ck(lines[i], lang)] = val
            time.sleep(SLEEP)

    def _do_block(block):
        q = "\n".join(b[1] for b in block)
        tr, err = _api_call(q, "en|" + lang)
        if err == "QUOTA":
            global _quota_exhausted
            _quota_exhausted = True
            return 0
        if err:
            _fallback_single(block)
            return len(block)
        parts = tr.split("\n")
        if len(parts) != len(block):
            _fallback_single(block)
            return len(block)
        with _lock:
            for (i, p), t in zip(block, parts):
                val = restore(t.strip(), prot_map[i])
                out[i] = val
                _cache[_ck(lines[i], lang)] = val
        return len(block)

    from concurrent.futures import ThreadPoolExecutor
    workers = min(6, max(1, len(blocks)))
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for n in ex.map(_do_block, blocks):
            done += n
            if verbose:
                print("  translated %d / %d" % (done, len(todo_idx)), flush=True)

    _save_cache(force=True)
    # 降级：任何未取到译文的条目回退为英文原文（保证页面可生成），且**不写缓存**，
    # 这样配额恢复后重跑会自动补翻，不会永久残留英文
    missing = sum(1 for i in range(len(out)) if out[i] is None)
    for i in range(len(out)):
        if out[i] is None:
            out[i] = lines[i]
    if _quota_exhausted or missing:
        print("[WARN] %s: %d/%d 条未取得译文(配额/网络)，已回退英文原文，稍后重跑可自动补翻"
              % (lang, missing, len(lines)))
    return out


def translate_one(text, lang):
    return translate_lines([text], lang)[0]


def back_translate(text, lang):
    """把译文翻回英文，用于维度1 回译验证"""
    return translate_lines([text], "en")[0] if text else text


def flush():
    _save_cache(force=True)
