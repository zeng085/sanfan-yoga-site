#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GLM 翻译引擎（glm-5.3-flash，智谱开放平台，OpenAI 兼容接口）

定位：DeepL 免费额度耗尽后的主引擎（2026-10-02）。
  引擎顺序：GLM（本模块）→ DeepL → MyMemory（在 translator._call_batch 里编排）

与 DeepL 引擎的本质差异（换引擎 ≠ 换 key）：
  DeepL: 逐条返回，条数天然一致；术语保护靠 <xN> 标签 + ignore_tags。
  LLM  : 会漏译 / 合并行 / 擅自润色 / 加解释 —— 所以必须：
    ① 行号锚定：<n>源文</n> → 要求 <n>译文</n>，解析后**校验编号序列完全一致**
    ② 完整性校验：空译文 / 整批回声 / 截断（finish=length）/ 日韩文字特征
    ③ 校验不过 → 重试（最多 2 次）→ 仍不过返回 None → 调用方降级 DeepL/MyMemory
    ④ 术语不走标签，直接写进 system prompt（LLM 天生照做），站内既有
       GLOSSARY（含 PILATES_TERMS）作为唯一术语来源，与 DeepL 路线同源

缓存注意：translate_lines 的缓存键含 ENGINE_TAG="deepl"（历史值），**故意不改**——
  改了 = 全站 4MB 缓存失效 = 下次构建把几千个已上线页面全部重翻（回归风险）。
  新行由 GLM 翻译后仍以 "deepl" 标签入库（标签名仅是历史键前缀，不代表引擎）。

接口要点（2026-10-02 实测）：
  POST https://open.bigmodel.cn/api/paas/v4/chat/completions
  Authorization: Bearer <key>；模型 glm-5.3-flash；temperature=0
  ⚠️ 该模型**始终思考**（thinking 参数传 disabled/low/high 均 400，code 1210），
     每请求约 300-400 reasoning token 按输出价计费 —— 大批次摊薄，全量任务约 ¥0.2，可忽略。
"""
import os
import re
import json
import time
import socket
import urllib.request
import urllib.error

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load_key():
    """key 只从环境变量或 .glm_key 读取，禁止硬编码（.gitignore 已排除 .glm_key*）"""
    for env in ("ZHIPU_API_KEY", "GLM_API_KEY"):
        k = os.environ.get(env, "").strip()
        if k:
            return k
    for name in (".glm_key", ".zhipu_key"):
        p = os.path.join(_HERE, name)
        if os.path.exists(p):
            return open(p, encoding="utf-8").read().strip()
    return ""


GLM_KEY = _load_key()
GLM_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
GLM_MODEL = os.environ.get("GLM_MODEL", "glm-5.3-flash")
GLM_TIMEOUT = int(os.environ.get("GLM_TIMEOUT", "480"))
# ⚠️ 480 不是拍脑袋：glm-5.3-flash「始终思考」，实测 42 行大批次（~7k tok 输入）
# 单请求要 2–6 分钟；120s 必超时 → 降级链会拿 MyMemory 顶上并污染缓存（10-02 实测踩坑）。
GLM_RETRIES = 2            # 校验失败后的重试次数（首次 + 2 = 最多 3 次请求）
GLM_MAX_TOKENS = int(os.environ.get("GLM_MAX_TOKENS", "16384"))
# 思考强度（顶层 reasoning_effort）：low / medium / high。默认 low —— 见 _http_call 注释。
REASONING_EFFORT = os.environ.get("GLM_REASONING_EFFORT", "low")

_LANG_NAME = {"de": "German", "ja": "Japanese", "ko": "Korean",
              "fr": "French", "it": "Italian", "es": "Spanish",
              "zh": "Simplified Chinese", "en": "English"}

# 无需翻译直接保留的内容（写进 system prompt；与 DeepL 的 WORD_TERMS 同口径但用字面量）
_KEEP_AS_IS = (
    "brand SANFAN / 三梵, model codes (e.g. AL 13 MC, 21-FO), material abbreviations "
    "(TPE, PVC, NBR, PU, EVA, SBR, TPEE, NR), certifications (REACH, CA Prop 65, EN 71, "
    "OEKO-TEX, SGS, BSCI, ISO 9001, RoHS, CPSIA, Intertek, TUV), OEM / ODM / B2B, "
    "all measurements (1830 x 610 x 6 mm, 85 kg, 40 ft) and counts"

    "Do NOT invent any information absent from the source: no prices, no MOQ, "
    "no certifications, no weight-bearing claims, no warranty statements."
)

# 译文语言特征（强信号：ja 必须有假名、ko 必须有谚文；欧语用高频词，弱信号只告警）
_SIG_STRONG = {"ja": re.compile(r"[\u3040-\u30ff]"), "ko": re.compile(r"[\uac00-\ud7af]")}
# 「输出像英文」标记：判「没翻」用正向证据（含英文高频词），而非反向（缺目标语特征）——
# 品牌句「Reformateur Pilates — fabricant OEM/ODM」两种语都无特征词，反向判必误杀（10-02 实测）。
_EN_MARK = re.compile(r"\b(the|and|with|for|of|is|are|our|your|we|an|or|from|this|that|these)\b", re.I)
_SIG_WEAK = {
    "de": re.compile(r"[äöüßÄÖÜ]|\b(der|die|das|und|mit|für|von|ist|werden|ein|eine|im|im|nicht|auch|auf|zu|den|dem)\b", re.I),
    "fr": re.compile(r"[àâçéèêëîïôûüœ]|\b(le|la|les|des|de|du|une|un|et|pour|avec|est|en|au|aux|dans|sur|sont|vous|votre|nos|nous|par|plus|qui|que)\b", re.I),
    "it": re.compile(r"[àèéìíòóùú]|\b(il|lo|la|le|di|per|con|sono|e|che|un|una|del|della|dei|gli|non|con|alla|nel)\b", re.I),
    "es": re.compile(r"[áéíóúñ¿¡]|\b(el|los|las|de|del|una|un|para|con|son|y|es|en|por|su|sus|más|para|está)\b", re.I),
}

# ---------------------------------------------------------------- usage 统计
USAGE = {"requests": 0, "prompt_tokens": 0, "completion_tokens": 0,
         "reasoning_tokens": 0, "retries": 0, "fallbacks": 0}


# ---------------------------------------------------------------- prompt
def _glossary_block(glossary, lang):
    """GLOSSARY[lang] -> 提示词用术语清单（源模式含正则量词，展示时去掉 ?/[- ]？等修饰）"""
    terms = glossary.get(lang) or {}
    lines = []
    for pat, fixed in terms.items():
        src = re.sub(r"\(\?:([- '])\)\?", r"\1", pat)     # (?:[- ])? -> "-"
        src = re.sub(r"s\?$", "s", src)                   # hammocks? -> hammocks
        src = re.sub(r"\?$", "", src)
        lines.append("%s -> %s" % (src.rstrip("?"), fixed))
    return "\n".join(lines)


def _system_prompt(lang, src, glossary_block=""):
    tgt = _LANG_NAME.get(lang.lower(), lang)
    srcl = _LANG_NAME.get(src.lower(), src)
    p = (
        "You are the senior translator for SANFAN (FUJIAN SANFAN Sports Products), a B2B "
        "yoga & pilates equipment manufacturer's website. Translate %s source text into "
        "natural, professional %s for B2B buyers (distributors, studio owners, brands).\n"
        "Rules:\n"
        "1. Translate faithfully. Do NOT paraphrase, shorten, expand, or add any "
        "information not in the source (especially no prices, MOQ, certifications, "
        "claims).\n"
        "2. Keep exactly, never translate: %s\n"
        "3. Marketing tone stays natural %s prose - not word-by-word.\n"
        "4. Output format is strict: one block per segment, exactly "
        "<n>translation</n> with the SAME numbers in the SAME order as the input. "
        "No numbering of your own, no explanations, no code fences, no blank "
        "blocks. If a segment is a brand/model/measurement, output it unchanged."
    ) % (srcl, tgt, _KEEP_AS_IS, tgt)
    if glossary_block:
        p += "\n5. Use these exact product terms:\n" + glossary_block
    return p


def _user_prompt(texts):
    parts = ["Segments:"]
    for i, t in enumerate(texts, 1):
        parts.append("<%d>%s</%d>" % (i, t, i))
    return "\n".join(parts)


# ---------------------------------------------------------------- 解析与校验
_SEG_RE = re.compile(r"<(\d+)>(.*?)</\1>", re.S)
_LEN_MIN = 0.35          # 译文/源文长度比下限（低于视为截断或摘要；仅对「可翻译」行）


def _looks_translatable(s):
    s = (s or "").strip()
    if len(s) < 8:
        return False
    if not re.search(r"[A-Za-z]{3,}", s):
        return False
    return len(s.split()) >= 2 or len(s) >= 16


def parse_response(content, n_expected):
    """解析 <n>...</n> 序列 -> (translations 或 None, 问题列表)"""
    problems = []
    segs = _SEG_RE.findall(content or "")
    ids = [int(i) for i, _ in segs]
    if ids != list(range(1, n_expected + 1)):
        missing = sorted(set(range(1, n_expected + 1)) - set(ids))
        extra = sorted(set(ids) - set(range(1, n_expected + 1)))
        problems.append("编号不一致: 缺%s 多%s（收到 %d 段，期望 %d）"
                        % (missing[:6], extra[:6], len(ids), n_expected))
        return None, problems
    vals = [v.strip() for _, v in segs]
    # 残留未闭合的锚（模型输出了一半）——按数量再兜一道
    if len(segs) != n_expected:
        problems.append("段数不符 %d != %d" % (len(segs), n_expected))
        return None, problems
    return vals, problems


def validate_batch(sources, vals, lang):
    """逐条完整性校验 -> 问题列表（空列表 = 通过）

    ⚠️ 特征信号是**整批级**判据（10-02 修正）：短标题/品牌句天然可合法地不含
    特征词（如 h1「Fabricant OEM/ODM de reformers Pilates」逐词都不命中旧 fr 表），
    逐行判 = 误杀 → 3 次重试全灭 → 降级污染缓存（实测踩坑）。
    整批无一行命中 strong/weak 才判「疑似没翻」。
    """
    problems = []
    n_echo = 0
    n_short = 0
    n_benign = 0
    strong_sig = _SIG_STRONG.get(lang)
    weak_sig = _SIG_WEAK.get(lang)
    n_translatable = 0
    n_any_sig = 0
    n_enish = 0
    for i, (src, out) in enumerate(zip(sources, vals), 1):
        if not out:
            problems.append("#%d 空译文" % i)
            continue
        if _looks_translatable(src):
            n_translatable += 1
            if out.strip() == src.strip():
                if _EN_MARK.search(src):
                    n_echo += 1
                    problems.append("#%d 回声（原样返回英文）" % i)
                else:
                    # 良性回声：型号 SKU / 国际术语（AL 8-Y、Pilates Reformer）在
                    # 目标语里本来就这么写，原样返回 = 正确行为。
                    # 10-02 全量跑批实测：把它当失败 → 重试 3 次全灭 → 降级污染缓存。
                    n_benign += 1
                continue
            ratio = len(out) / max(len(src), 1)
            if ratio < _LEN_MIN:
                n_short += 1
                problems.append("#%d 疑似截断/摘要（长度比 %.2f）" % (i, ratio))
            if (strong_sig and strong_sig.search(out)) or (weak_sig and weak_sig.search(out)):
                n_any_sig += 1
            if _EN_MARK.search(out):
                n_enish += 1
    # 「疑似没翻」= 整批无目标语特征 **且** 有英文正向证据；品牌句两者皆无 → 放行
    if n_translatable and n_any_sig == 0 and n_enish and n_benign == 0:
        problems.append("整批疑似没翻（无 %s 特征 + 含英文词）" % lang)
    if n_echo == n_translatable and n_echo:
        problems.append("整批回声 —— 引擎失败")
    return problems


# ---------------------------------------------------------------- 调用
def _http_call(messages, n_lines):
    body = {"model": GLM_MODEL, "temperature": 0, "max_tokens": GLM_MAX_TOKENS,
            "messages": messages}
    # ⭐⭐ 思考强度：glm-5.3-flash **始终思考**，`thinking` 参数各种写法全 400
    #   （code 1210，错误信息还误导人）。真正的旋钮是顶层 `reasoning_effort`。
    #   实测同一批 12 行：默认 → 8268 reasoning tok / 156s（偶尔撞 max_tokens 截断）；
    #   reasoning_effort=low → **0 reasoning tok / 4.2s**。这是本链路的最大提速点。
    if REASONING_EFFORT:
        body["reasoning_effort"] = REASONING_EFFORT
    req = urllib.request.Request(
        GLM_URL, data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": "Bearer " + GLM_KEY, "Content-Type": "application/json"})
    last_err = None
    # 超时按批量三档缩放（10-02 实测：一条挂死请求会把整页拖住 577s）：
    #   n>8 → 180s ／ 4<n≤8 → 120s ／ n≤4 → 90s
    # 拆批后的每一级都比上一级更快失败，级联总代价有界。
    _timeout = GLM_TIMEOUT if n_lines > 8 else (120 if n_lines > 4 else 90)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=_timeout) as r:
                d = json.loads(r.read().decode("utf-8"))
            USAGE["requests"] += 1
            u = d.get("usage") or {}
            USAGE["prompt_tokens"] += u.get("prompt_tokens", 0) or 0
            USAGE["completion_tokens"] += u.get("completion_tokens", 0) or 0
            USAGE["reasoning_tokens"] += (u.get("completion_tokens_details") or {}).get(
                "reasoning_tokens", 0) or 0
            choice = (d.get("choices") or [{}])[0]
            if choice.get("finish_reason") == "length":
                return None, "输出被截断（finish=length），需减小批次"
            content = (choice.get("message") or {}).get("content") or ""
            return content, None
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode("utf-8")[:160]
            except Exception:
                pass
            if e.code == 429:                       # 限流：退避重试
                last_err = "HTTP 429 限流"
                time.sleep(3 * (attempt + 1))
                continue
            return None, "HTTP %s %s" % (e.code, detail)
        except Exception as e:
            last_err = "%s: %s" % (type(e).__name__, str(e)[:100])
            # ⭐ 超时**不在本层重试**：同批同超时重试只会把墙钟时间翻 3 倍
            #   （实测 3×180s = 577s 卡死整页）。交给上层拆批器 —— 拆小后
            #   单请求更快，且小批次超时只有 90s。
            if isinstance(e, (TimeoutError, socket.timeout)) or "timed out" in str(e).lower():
                return None, "超时（%ds，n=%d）→ 拆批" % (_timeout, n_lines)
            time.sleep(2 * (attempt + 1))
    return None, last_err


def glm_call(texts, lang, src="EN", glossary=None):
    """翻译一批文本 -> (译文列表 或 None, 错误串 或 None)。

    校验不过会重试（最多 GLM_RETRIES 次）；仍不过返回 (None, 原因)，由调用方降级。
    glossary: translator.GLOSSARY（dict: lang -> {源模式: 固定译法}）
    """
    if not GLM_KEY:
        return None, "无 GLM key"
    if lang.lower() == src.lower():
        return list(texts), None
    gb = _glossary_block(glossary or {}, lang)
    sys_p = _system_prompt(lang, src, gb)
    sources = list(texts)
    messages = [{"role": "system", "content": sys_p},
                {"role": "user", "content": _user_prompt(sources)}]
    last_problems = []
    for attempt in range(1 + GLM_RETRIES):
        content, err = _http_call(messages, len(sources))
        if err:
            return None, err
        vals, problems = parse_response(content, len(sources))
        if vals is None:
            last_problems = problems
        else:
            problems = validate_batch(sources, vals, lang)
            if not problems:
                return vals, None
            last_problems = problems
        USAGE["retries"] += 1
        # ⭐ 结构性问题（模型丢行/编号不齐）**重试同批次命中率极低**：10-02 实测
        #    es 轮同一 12 行批重喂 3 次仍缺同一行，而拆半后必然成功（译文里没有
        #    该行可丢）。所以结构性问题只重试 1 次就交给拆批器，省下约 60s/批。
        #    截断（finish=length）更早：_http_call 直接返回 err，不走重试。
        structural = any(("编号" in p or "缺[" in p or "段，" in p) for p in last_problems)
        if attempt < GLM_RETRIES and not (structural and attempt >= 1):
            # 第二次起把失败原因回喂，并加严措辞
            messages = messages[:2] + [
                {"role": "assistant", "content": content or ""},
                {"role": "user",
                 "content": "Your previous output failed validation:\n- %s\n"
                            "Return EXACTLY %d blocks <n>translation</n>, same numbers, "
                            "same order, nothing else. Re-translate from the original "
                            "segments above." % (";\n- ".join(last_problems[:8]),
                                                 len(sources))}]
    USAGE["fallbacks"] += 1
    return None, "校验 %d 次未过: %s" % (1 + GLM_RETRIES, "; ".join(last_problems[:5]))


# ---------------------------------------------------------------- 离线自检
def _selftest():
    """不联网：验证解析器与校验器对好/坏输出的判定（A/B：坏的必须报出）"""
    srcs = ["SANFAN TPE yoga mat with REACH certification for wholesale buyers.",
            "The 2026 catalogue covers 80 pilates models across six families.",
            "Contact our QC team for factory audit reports and test data."]
    ok = []

    # ① 良好输出 -> 通过
    good = "<1>SANFAN TPE Yogamatte mit REACH-Zertifizierung für Großabnehmer.</1>\n" \
           "<2>Der Katalog 2026 umfasst 80 Pilates-Modelle in sechs Familien.</1\n".replace("</1\n", "</2>") \
           + "\n<3>Kontaktieren Sie unser QC-Team für Werksaudits und Prüfdaten.</3>"
    vals, probs = parse_response(good, 3)
    assert vals is not None, "良好输出被误判: %s" % probs
    ok.append("良好输出 3/3 通过")

    # ② 缺一段（漏译）-> 必须报出
    miss = "<1>SANFAN TPE Yogamatte.</1>\n<3>Kontaktieren Sie unser QC-Team.</3>"
    vals, probs = parse_response(miss, 3)
    assert vals is None and any("编号不一致" in p for p in probs), "漏译没被抓到: %s" % probs
    ok.append("漏译（缺 #2）被抓到")

    # ③ 合并（两段变一段）-> 必须报出
    merged = "<1>第一段</1>"
    vals, probs = parse_response(merged, 2)
    assert vals is None, "合并没被抓到"
    ok.append("合并（2 段变 1 段）被抓到")

    # ④ 加了解释 / 代码围栏 -> 编号外的内容不进译文
    noisy = "Sure! Here is the translation:\n```\n<1>Yogamatte</1>\n```\nHope this helps!"
    vals, probs = parse_response(noisy, 1)
    assert vals == ["Yogamatte"], "噪声解析错: %s" % vals
    ok.append("围栏/客套话被剥掉，只取锚内内容")

    # ⑤ 整批回声 -> 必须报出
    echo_vals = list(srcs)
    probs = validate_batch(srcs, echo_vals, "de")
    assert any("整批回声" in p for p in probs), "整批回声没被抓到: %s" % probs
    ok.append("整批回声被抓到")

    # ⑥ ja 译文没翻 -> 必须报出（两种形态分别测：
    #    ⑥a 完全相同的回声 -> 命中「回声」分支；⑥b 英文改写（不同串但仍是英文）-> 命中「缺假名」分支）
    probs = validate_batch(["Pilates reformer with aluminum frame."],
                           ["Pilates reformer with aluminum frame."], "ja")
    assert any("回声" in p for p in probs), "ja 回声没被抓到: %s" % probs
    ok.append("ja 完全回声被抓到（回声分支优先）")
    # ⑥b ja 英文改写（含英文词 + 缺假名）-> 必须报出
    probs = validate_batch(["Pilates reformer with aluminum frame."],
                           ["Pilates reformer featuring an aluminum frame."], "ja")
    assert any("疑似没翻" in p for p in probs), "ja 英文改写没被抓到: %s" % probs
    ok.append("ja 英文改写（非回声）被「英文词+缺假名」抓到")

    # ⑥c fr 品牌句（10-02 实测误杀回归）：合法 fr 译文无特征词也无英文词 -> 必须放行
    probs = validate_batch(["Pilates Reformer — OEM/ODM manufacturer"],
                           ["Reformateur Pilates — fabricant OEM/ODM"], "fr")
    assert not probs, "fr 品牌句被特征词误杀: %s" % probs
    ok.append("fr 无特征词的品牌句放行（误杀回归）")

    # ⑥d fr 批：一行品牌句 + 一行正常句 -> 整批放行（批级判据）
    probs = validate_batch(
        ["Pilates Reformer — OEM/ODM manufacturer", "Contact our QC team for audit reports."],
        ["Reformateur Pilates — fabricant OEM/ODM", "Contactez notre équipe QC pour les rapports d'audit."],
        "fr")
    assert not probs, "fr 混合批被误杀: %s" % probs
    ok.append("fr 混合批（品牌句+正常句）放行")

    # ⑥e 型号 SKU 原样返回 = 正确行为（10-02 全量跑批实测：整批因 5 个型号码
    #    回声被误杀 → 降级 MyMemory 污染缓存 → 守卫 abort）
    probs = validate_batch(["AL 8-Y", "Packing size A", "Chair 1-A"],
                           ["AL 8-Y", "Packmaß A", "Chair 1-A"], "de")
    assert not probs, "型号 SKU 良性回声被误杀: %s" % probs
    ok.append("型号 SKU 良性回声放行（全量跑批回归）")

    # ⑥f 真回声（含英文功能词的句子原样返回）仍必须抓到
    probs = validate_batch(["We deliver worldwide with DDP terms."],
                           ["We deliver worldwide with DDP terms."], "de")
    assert any("回声" in p for p in probs), "真回声没被抓到: %s" % probs
    ok.append("含功能词的真回声仍被抓到")

    # ⑦ ja 正常译文 -> 通过
    probs = validate_batch(["Pilates reformer with aluminum frame."],
                           ["アルミフレーム搭載のピラティス リフォーマー。"], "ja")
    assert not probs, "正常 ja 被误判: %s" % probs
    ok.append("正常 ja 译文通过")

    # ⑧ 截断/摘要（长度比过低）-> 必须报出
    probs = validate_batch([srcs[0]], ["Yogamatte."], "de")
    assert any("截断" in p or "长度比" in p for p in probs), "截断没被抓到: %s" % probs
    ok.append("疑似截断（长度比 %.2f）被抓到" % _LEN_MIN)

    # ⑨ 短非翻译段（品牌/尺寸）-> 不应触发回声误报
    probs = validate_batch(["TPE", "1830 x 610 x 6 mm"], ["TPE", "1830 x 610 x 6 mm"], "de")
    assert not probs, "短段被误判: %s" % probs
    ok.append("品牌/尺寸短段不误报")

    print("自检 %d 项：" % len(ok))
    for x in ok:
        print("  ✓ " + x)
    print("✓ 全部通过")


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        _selftest()
    elif "--ping" in sys.argv:
        vals, err = glm_call(["Free samples are available for qualified distributors."],
                             "de", glossary={})
        print("err =", err)
        print("out =", vals)
        print("usage =", USAGE)
    else:
        print("用法: --selftest(离线自检) | --ping(联网最小实测)")
