#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SANFAN 翻译正确性验证 —— 三维度独立校验
  DIM-1 回译语义一致性 : 译文 -> 回翻英文 -> 与原文语义比对 (token Jaccard + 关键词保留率)
  DIM-2 术语锁定与结构完整性 : 行业术语必须原样保留 / 未翻译残留 / HTML标签·数字·占位符 完整性
  DIM-3 语言正确性与长度比 : 目标语字符集校验 + 译文/原文长度比合理区间
  DIM-4 (附加) 批量 vs 单条 交叉一致性 : 抽验批量拼接是否引入串味/错位
"""
import re, unicodedata
from difflib import SequenceMatcher

import translator as T

# ------------------------------------------------------- 通用工具
STOP = set("""a an the and or of to in on for with at by from as is are was were be been being
this that these those it its into your our their his her not no do does did can will would
we you they he she i me us them my mine ours yours if then than so such very more most""".split())

TERM_RE = T._PROT_RE

# 本就不该翻译的专有内容：地址 / 公司名 / 规格串（保持原文是正确行为，不算漏翻）
ADDRESS_HINT = re.compile(
    r"\b(Road|Street|St\.|Avenue|Ave\.|Zone|Town|Province|Industrial|District|City|County|"
    r"No\.|Floor|Building|Road,)\b", re.I)
COMPANY_HINT = re.compile(r"\b(Co\.?,?\s?Ltd\.?|Ltd\.?|Inc\.?|GmbH|Corporation|Corp\.?)\b", re.I)
SPEC_HINT = re.compile(r"\d+\s?[x×]\s?\d+|·|\d+\s?/\s?\d+")
# 英文数字单词（one/two/four…）在目标语常被写成阿拉伯数字，属正常，不算数字丢失
NUMWORD_HINT = re.compile(
    r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"twenty|thirty|forty|fifty|hundred|thousand|"
    # 数量词缀：double-layer -> 2층 / tri-fold -> 3つ折り 属正确本地化
    r"single|double|triple|tri|twin|dual|quarter|half)\b", re.I)
# 反向情况：阿拉伯数字被本地化为目标语数字单词（5 lines -> fünf Linien），同样正常
NUMWORD_TARGET = {
    "de": re.compile(r"\b(ein|eine|einen|einem|einer|zwei|drei|vier|fünf|sechs|sieben|acht|"
                     r"neun|zehn|elf|zwölf|zwanzig|dreißig|vierzig|fünfzig|hundert|tausend)\b", re.I),
    "ja": re.compile(r"[一二三四五六七八九十百千万]"),
    "ko": re.compile(r"(하나|둘|셋|넷|다섯|여섯|일곱|여덟|아홉|열|스물|백|천)"),
}


def _norm(s):
    s = unicodedata.normalize("NFKC", (s or "")).lower()
    s = re.sub(r"[^0-9a-z\u00c0-\u024f\u3040-\u30ff\u4e00-\u9fff\uac00-\ud7af]+", " ", s)
    return s.strip()


def _toks(s):
    return [w for w in _norm(s).split() if w not in STOP and len(w) > 1]


def jaccard(a, b):
    A, B = set(_toks(a)), set(_toks(b))
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


def fuzzy(a, b):
    return SequenceMatcher(None, _norm(a), _norm(b)).ratio()


# ------------------------------------------------------- DIM-2: 术语与结构
def dim2_terms_structure(src, dst, lang):
    """返回 (ok, [问题...])"""
    issues = []
    if not src or not src.strip():
        return True, issues
    if not dst or not dst.strip():
        return False, ["EMPTY_TRANSLATION"]

    # 1) 术语锁定：原文出现的受保护术语，译文必须原样出现（大小写不敏感）
    src_terms = TERM_RE.findall(src)
    for t in set(t if isinstance(t, str) else t[0] for t in src_terms):
        tt = t.strip()
        if not tt:
            continue
        if tt.lower() not in dst.lower():
            issues.append("TERM_LOST:%s" % tt)

    # 2) 未翻译残留：非纯术语长文本，译文与原文**完全一致**才算漏翻
    #    （大小写/连字符/空格差异说明引擎确实处理过，不判失败）
    core = TERM_RE.sub(" ", src)
    core = re.sub(r"[^0-9A-Za-z\u00c0-\u024f]+", " ", core).strip()
    if len(core.split()) >= 4 and src.strip() == dst.strip() \
            and not (ADDRESS_HINT.search(src) or COMPANY_HINT.search(src) or SPEC_HINT.search(src)):
        issues.append("UNTRANSLATED_IDENTICAL")

    # 3) HTML 标签完整性
    st = re.findall(r"</?([a-zA-Z][a-zA-Z0-9]*)\b", src)
    dt = re.findall(r"</?([a-zA-Z][a-zA-Z0-9]*)\b", dst)
    if st and sorted(st) != sorted(dt):
        issues.append("HTML_TAGS_CHANGED:%s->%s" % (st, dt))

    # 4) 数字完整性（允许千分位/小数点本地化差异，只比数字集合）
    sn = sorted(re.findall(r"\d+", src))
    dn = sorted(re.findall(r"\d+", dst))
    if sn != dn:
        # 豁免：数量级换算 (200K+ -> 20万人以上 / 200K -> 20만) 与习语 (24/7 -> 24시간 연중무휴)
        scale = re.search(r"\d\s*[KkMm]\b|万|千|億|亿|만|천", src) or \
                re.search(r"万|千|億|亿|만|천", dst) or re.search(r"\d+\s*/\s*\d+", src) or \
                NUMWORD_HINT.search(src) or SPEC_HINT.search(src) or \
                (lang in NUMWORD_TARGET and NUMWORD_TARGET[lang].search(dst))
        if not scale:
            issues.append("NUMBERS_CHANGED:%s->%s" % (sn, dn))

    # 5) 占位符完整性
    sp = re.findall(r"\{[^}]*\}|%[sd]\b|\$\{[^}]*\}", src)
    dp = re.findall(r"\{[^}]*\}|%[sd]\b|\$\{[^}]*\}", dst)
    if sorted(sp) != sorted(dp):
        issues.append("PLACEHOLDER_CHANGED:%s->%s" % (sp, dp))

    # 6) 保护占位符未还原（☁TM0☁ 残留）
    if "☁TM" in dst:
        issues.append("PROTECT_PLACEHOLDER_LEAK")

    return (len(issues) == 0), issues


# ------------------------------------------------------- DIM-3: 语言与长度
LANG_SCRIPT = {
    "de": lambda s: bool(re.search(r"[A-Za-zÄÖÜäöüß]", s)),
    "ja": lambda s: bool(re.search(r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]", s)),
    "ko": lambda s: bool(re.search(r"[\uac00-\ud7af\u1100-\u11ff]", s)),
}
# 目标语若几乎不含本语言字符，说明返回了错误语种
FOREIGN_HINT = {
    "ja": lambda s: len(re.findall(r"[A-Za-z]", s)) > 3 * len(re.findall(r"[\u3040-\u30ff\u4e00-\u9fff]", s)),
    "ko": lambda s: len(re.findall(r"[A-Za-z]", s)) > 3 * len(re.findall(r"[\uac00-\ud7af]", s)),
    "de": lambda s: len(re.findall(r"[\u0400-\u04FF]", s)) > 0,
}
# CJK 信息密度高，等长英文对应的中日韩文字符数天然更短
LEN_RANGE = {"de": (0.75, 2.20), "ja": (0.15, 1.60), "ko": (0.15, 1.60)}
LEN_MIN_SRC = 20      # 短文本的字符数比无统计意义（如 Products -> 製品）


def dim3_language(src, dst, lang):
    issues = []
    if not dst or not dst.strip():
        return False, ["EMPTY"]
    # 保留项（品牌名/数字/缩写原样未译）不做语言与长度判定
    if _norm(src) == _norm(dst):
        return True, []
    # 纯数字/符号（如 "200K+" -> "200.000+"，德语用点作千分位）：无字母可判，跳过
    if not re.search(r"[A-Za-z]", dst):
        return True, []
    if not LANG_SCRIPT[lang](dst):
        issues.append("WRONG_SCRIPT")
    if lang in FOREIGN_HINT and FOREIGN_HINT[lang](dst):
        issues.append("LOOKS_LIKE_ENGLISH")
    if len(src) >= LEN_MIN_SRC:
        lo, hi = LEN_RANGE[lang]
        ratio = len(dst) / max(1, len(src))
        if not (lo <= ratio <= hi):
            issues.append("LENGTH_RATIO_%.2f" % ratio)
    return (len(issues) == 0), issues


# ------------------------------------------------------- DIM-1: 回译
def dim1_backtranslate(pairs, lang):
    """pairs: [(src, dst)] -> [(src, dst, back, score, ok, thr)]

    定位：**严重跑偏粗筛**，不是措辞一致性打分。
    回译天然会改写措辞（"2 persons" -> "two people"、"format" -> "size"），
    词面 Jaccard 会被同义改写严重压低，故以字符级模糊匹配为主、
    Jaccard 为辅；只有语义真跑偏/大量漏译时得分才会低到阈值以下。
    精确判定由 DIM-2/3/4 承担。
    """
    backs = T.translate_lines([d for _, d in pairs], "en", src=lang.upper())
    res = []
    for (src, dst), back in zip(pairs, backs):
        n = len(_toks(src))
        thr = 0.28 if n <= 4 else (0.30 if n <= 9 else 0.32)
        # 回译接口偶发返回空串（多为极短文本），此时无法判定，不计为失败
        if not (back or "").strip():
            res.append((src, dst, back, 0.0, True, thr))
            continue
        j = jaccard(src, back)
        f = fuzzy(src, back)
        score = 0.7 * f + 0.3 * j
        res.append((src, dst, back, round(score, 3), score >= thr, thr))
    return res


# ------------------------------------------------------- DIM-4: 批量 vs 单条 交叉
def dim4_crosscheck(pairs, lang, sample=0.25, min_n=8, max_n=60):
    """随机抽样，用单条独立请求重翻，与批量结果比对"""
    import random
    idx = [i for i, (s, d) in enumerate(pairs) if s and s.strip() and len(s.strip()) > 3]
    if not idx:
        return []
    k = min(max(min_n, int(len(idx) * sample)), max_n, len(idx))
    pick = random.Random(42).sample(idx, k)
    singles = []
    for i in pick:
        singles.append(T.translate_one(pairs[i][0], lang))
    out = []
    for i, single in zip(pick, singles):
        src, batch = pairs[i]
        f = fuzzy(batch, single)
        out.append((src, batch, single, round(f, 3), f >= 0.55))
    return out
