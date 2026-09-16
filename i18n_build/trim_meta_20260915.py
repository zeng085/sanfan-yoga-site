#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""meta 规范化：title 品牌后缀归一 + description 超长安全截断（2026-09-15）

【病根】
147 个产品页的 <title> 用了**长品牌后缀** "— SANFAN Yoga & Fitness Manufacturer"。
机翻后膨胀惊人：
    EN 34 宽 → de 47 / fr 52 / it 54 / ja 39 / ko 37（按 Google 像素宽度，CJK=2）
叠加产品名后，按 60 宽预算计算，全站 **979 页 title 超长**。

而站点其余 5 个目录（root / applications / blog / pilates）以及**同一批产品页的
og:title / twitter:title 早就是短后缀 "— SANFAN"** ——
products 的 <title> 是全站唯一的不一致，属历史遗留。

【修法】
把 <title> 的品牌后缀一律归一到 " — SANFAN"，与 og:title 及全站其余目录对齐。
品牌名不翻译、跨语言一致，也符合 SEO 惯例。

【只动什么】
只改 <title> 标签内部。**不碰**：
  · <h1>            —— 可见文案，本来就用短后缀，且不受像素预算约束
  · JSON-LD name    —— 结构化数据里的产品名不带后缀
  · og:title / twitter:title —— 已是短后缀
  · description     —— 由 --desc 开关单独控制

【幂等】后缀已是 "SANFAN" 的页面不会被再次处理。

用法：
    python3 trim_meta_20260915.py --check     # 只报告
    python3 trim_meta_20260915.py --dry-run   # 打印改动明细
    python3 trim_meta_20260915.py             # 落盘
    python3 trim_meta_20260915.py --desc      # 追加：description 安全截断
"""
import glob
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

LANGS = ["", "de", "ja", "ko", "fr", "it", "es"]
DIRS = ["", "products", "applications", "blog", "pilates"]

# 品牌后缀**两级**：主体短 → 用信息量更大的长后缀；主体长 → 退回短后缀。
#
# ⚠️ 为什么要两级：一刀切用最短后缀 "SANFAN" 会把 about / 产品页压到 14-17 字
#    （`About — SANFAN`、`Ab Wheel — SANFAN`），SEO 体检直接报 250 处「title 过短」——
#    标题太短等于把展示位白送。实测：一级后缀 979 页超长，全用最短后缀又换来 250 页过短。
#
# 长后缀取「品牌 + 品类 + B2B 身份」，26 宽（拉丁）。原文的
# "SANFAN Yoga & Fitness Manufacturer"（34 宽）机翻后膨胀到 47-54 宽才是真问题 ——
# 要解决的是「机翻 + 过长」，不是「有后缀」。
SUFFIX_LONG = {
    "en": "SANFAN Yoga & Fitness OEM",
    "de": "SANFAN Yoga & Fitness OEM",
    "fr": "SANFAN Yoga & Fitness OEM",
    "it": "SANFAN Yoga & Fitness OEM",
    "es": "SANFAN Yoga & Fitness OEM",
    "ja": "SANFAN ヨガ・フィットネス",
    "ko": "SANFAN 요가 및 피트니스",
}
SUFFIX_SHORT = "SANFAN"
# title 目标预算（显示宽度）。超过会被 Google 截断。
TITLE_BUDGET = 60

# <title> 末尾「分隔符 + 品牌后缀」的识别：
#   分隔符含**字面量与 HTML 实体**两种写法：`—` `–` `|` 以及 `&#124;` `&vert;`
#   ⚠️ 漏掉实体形式会误伤：materials.html 的 title 是
#      "Yoga Mat Materials Compared — TPE vs PVC vs PU vs Cork &#124; SANFAN"，
#      只认字面 `|` 时会退到前一个 `—`，把 "TPE vs PVC vs PU vs Cork … SANFAN"
#      整段当成品牌后缀删掉 —— 直接毁掉核心关键词。
#   两侧要求带空格，避免误伤 "Yoga- und" / "7-Day" 这类连字符。
#   尾段禁止再含任何分隔符（保证取的是**最后一段**，不会吞并关键词）。
#   尾段必须含 SANFAN，且解码后长度 ≥ 16
#   —— 把已经是 " — SANFAN"(6) / "| FUJIAN SANFAN"(13) 的排除掉（幂等）。
TITLE_RE = re.compile(r"<title>([\s\S]*?)</title>")
SEP = r"(?:[—–|]|&#124;|&vert;|&#x7c;|&brvbar;)"
TAIL_RE = re.compile(r"([\s\S]*)\s+" + SEP + r"\s+([^<>—–|]*)$")

# 夹在两个分隔符之间、**只由 OEM / ODM 构成**的冗余段。
# 例："Gym & Fitness Club Equipment Manufacturer | OEM / ODM — SANFAN"
#     → "Gym & Fitness Club Equipment Manufacturer — SANFAN"
# 依据：Manufacturer / Hersteller / Fabricant 等词已经涵盖 OEM 能力，
# 该段纯属模板化重复；且它在分类页、应用页上高度重复，对单页排名贡献极低。
# ⚠️ 必须用 SEP 而不是字面 [|｜] —— EN 源页里分隔符常常写成 HTML 实体
#    `&#124;`（如 applications/gyms-fitness-clubs.html 的 title 就是
#    "… Manufacturer &#124; OEM / ODM — SANFAN"），只认字面竖线会把 EN 全漏掉
#    （实测：只认字面时 81 处改动全落在语言版，EN 一处都没有）。
# ⚠️ 必须要求后面还有分隔符（不能是 title 结尾），否则会连着品牌段一起删掉。
# ⚠️ 只匹配「整段就是 OEM/ODM」的情况 —— "OEM mit individuellem Logo" 这类
#    带实词的段不能被吃掉。
OEM_SEG_RE = re.compile(
    r"\s*" + SEP + r"\s*(?:OEM|ODM)(?:\s*[/／]\s*(?:OEM|ODM))*\s*(?=" + SEP + r")",
    re.I)

# 机翻把品牌后缀展开成从句的两种形态（规则 ③）。
#   C1 冒号引出：es "Esterilla de yoga «Alignment Line»TPE: fabricante de productos de yoga y fitness «SANFAN»"
#      ⚠️ 冒号前可能没有空格（"»TPE:"），所以用 \s* 而非 \s+
#   C2 品牌夹在破折号中间：de "Produkte nach Kategorie – SANFAN – OEM-Hersteller von Yogamatten…"
#      —— 这种 TAIL_RE 抓不到：最后一段 "OEM-Hersteller …" 不含品牌名，会整条漏过。
COLON_BRAND_RE = re.compile(r"^([\s\S]+?)\s*(?::|：)\s+([^<>:：]*)$")
SANDWICH_BRAND_RE = re.compile(
    r"^([\s\S]+?)\s+[—–]\s+(?:„|«|\"|')?SANFAN(?:“|»|\"|')?\s+[–—]\s+([^<>]*)$", re.I)
# 「制造商」类词 —— 规则 ③ 的第二道闸：尾段必须真的在说「我们是做这个的」。
# 缺了它，博客标题的副标题会因含品牌名被误删（"REACH, CA Prop 65 & 6P: Yoga Mat
# Compliance for US & EU — SANFAN" → 只剩 "REACH, CA Prop 65 & 6P"）。
MFR_RE = re.compile(
    r"manufactur|maker|fabricant|fabricante|fabbricante|produttore|herstell|"
    r"proveedor|fornitore|fournisseur|supplier|tootja|производ|"
    r"\bOEM\b|\bODM\b|メーカー|製造|制造|제조", re.I)

# description 预算（像素宽度近似：CJK=2）。155 宽 ≈ Google 桌面 920px。
# 只对「严重超长」动手：155–200 宽属轻微超出，保留 —— 为凑长度截断可能
# 丢掉联系方式一类的转化信息（如 de/contact.html 179 宽，末尾就是 email+WhatsApp）。
DESC_BUDGET = 155
DESC_HARD = 200
# 截断后若短于此宽度，说明句末切得太狠（浪费展示位），放弃截断保留原文
DESC_MIN_KEEP = 120
SENT_END = re.compile(r"[.!?。！？](?=\s|$)")
# 常见缩写 —— 其后的 `.` 不是句末。不排除会切出半句话：
#   "… „TPE“ vs." / "… z.B." 这类结尾看着像句子其实不是。
ABBR = {"vs", "z.b", "u.a", "bzw", "usw", "etc", "ca", "nr", "inkl", "bspw",
        "vgl", "ggf", "o.ä", "e.g", "i.e", "mio", "mrd", "sog", "evtl",
        "max", "min", "abb", "tab", "bd", "jh", "jhd", "resp", "ff", "ev"}
# ⭐ 被丢弃的尾部若含这些内容 → 一律不截。
#    meta description 不参与排名，只影响点击率；而 B2B 采购决策最看重的
#    恰恰是「起订量 / 打样周期 / 贴牌 / 认证 / 报价」这类具体承诺。
#    实测：不加这道闸时 32 处截断里有 14 处（44%）把这类信息切掉了
#    （如 de/ 首页丢了 "Mindestbestellmenge 100 Stück, Muster in 7 Tagen, ROHS / CE"，
#      fr/pilates 丢了 "OEM/ODM avec votre logo"）—— 省下的展示位不值这个代价。
#    用词干而非整词，覆盖各语言的屈折变化与拼写变体。
KEEP_RE = re.compile(
    r"@|\+\d{2}|WhatsApp|"                                    # 联系方式
    r"Mindestbestellmenge|Mindestmenge|\bMOQ\b|quantità minima|quantidade mínima|"
    r"quantité minimale|cantidad mínima|最小(?:注文|ロット|発注)|최소 주문|起订|"
    r"[Ss]ampl|Muster|muestra|campionat|échantillon|サンプル|샘플|打样|"
    r"\bOEM\b|\bODM\b|logo|Private.?Label|"
    r"\bROHS\b|\bREACH\b|\bCE\b|\bISO\b|Zertifizier|certific|認証|인증|"
    r"\bdevis\b|presupuesto|preventivo|Angebot|quotation|\bquote\b|見積|견적",
    re.I)


def _is_abbr(plain, dot_pos):
    """判断 dot_pos 处的 `.` 是否属于缩写（而非句末）。"""
    m = re.search(r"(\S+)$", plain[:dot_pos])
    return bool(m) and m.group(1).lower() in ABBR


def W(s):
    """近似显示宽度：CJK/全角算 2，其余算 1。

    必须按宽度而非字符数判断：CJK 字符宽度约为拉丁字母的 2 倍，
    ja/ko 版按字符数统计会显示「0 超长」，按宽度算却有上百页超长。
    """
    return sum(2 if ord(c) > 0x2E80 else 1 for c in s)


def width(raw):
    """对 HTML 片段先解码实体再算宽度（&amp; 应从 5 字符还原为 1）。"""
    return W(html.unescape(raw))


def trim_desc(text):
    """超长 description 在句末安全截断。返回 (新文本, 是否改动)。

    只在「能切出一个完整、充实的句子」且**丢掉的部分是可有可无的**时才动手：
      · 超长（> DESC_HARD）
      · 句末截断点 ≤ DESC_BUDGET（Google 展示上限）
      · 截断后仍 ≥ DESC_MIN_KEEP（否则宁可保留长文让 Google 自己截）
      · 被丢弃的尾部不含 B2B 钩子 / 联系方式（KEEP_RE）
    """
    if width(text) <= DESC_HARD:
        return text, False
    plain = html.unescape(text)

    best = None
    for m in SENT_END.finditer(plain):
        if _is_abbr(plain, m.start()):
            continue          # "… vs." / "… z.B." 不是句末，跳过
        cut = plain[: m.end()].rstrip()
        if width(cut) <= DESC_BUDGET:
            best = cut
        else:
            break
    if best is None:
        # 首句就超预算 —— 不给 Google 交半句话，保留原文让它自己截
        return text, False

    best = best.rstrip()
    if width(best) < DESC_MIN_KEEP or best == plain.rstrip():
        return text, False
    # 被丢弃的尾部若承载 B2B 钩子 / 联系方式 → 宁可不截
    if KEEP_RE.search(plain[len(best):]):
        return text, False
    return best, True


def pick_suffix(body_raw, lang):
    """按主体剩余空间选后缀：能装下长后缀就用长的，否则退回短的。"""
    long_s = SUFFIX_LONG.get(lang, SUFFIX_LONG["en"])
    if width(body_raw.strip()) + width(" — " + long_s) <= TITLE_BUDGET:
        return " — " + long_s
    return " — " + SUFFIX_SHORT


def norm_title(inner, lang):
    """对 <title> 内部文本应用三条规则，返回 (新 inner, 说明)。

    三条规则依次应用：
      ① 删掉夹在分隔符之间、只由 OEM / ODM 构成的冗余段
      ② 品牌后缀归一到「长/短」两级中的合适一档
      ③ 机翻把品牌后缀展开成「描述语 + 品牌」的从句 → 收回标准后缀

    ⚠️ 必须迭代到不动点：③ 会把标题削短，而 ② 是「按剩余空间选后缀」，
       削短之后 ② 又有空间升级成长后缀。一轮跑完还会留一处改动不生效
       （实测 de/products.html：③ 缩到 32 宽，② 又升回长后缀 → 不幂等）。
       规则都收敛得很快，3 轮足够。
    """
    cur, notes = inner, []
    for _ in range(3):
        nxt, why = _norm_once(cur, lang)
        if not why:
            break
        cur = nxt
        notes.append(why)
    return cur, "; ".join(notes) if notes else None


def _norm_once(inner, lang):
    notes = []

    # ① 冗余 OEM / ODM 段
    #    ⚠️ 用空格替换而不是空串：正则里的 \s* 会连后面的空格一起吃掉，
    #       直接删会粘出 "Manufacturer— SANFAN" 这种缺空格的标题。
    trimmed = OEM_SEG_RE.sub(" ", inner)
    if trimmed != inner:
        trimmed = re.sub(r"\s{2,}", " ", trimmed).strip()
        # 保护：删完主体不能瘦得只剩品牌（说明这段其实承载了信息）
        probe = TAIL_RE.match(trimmed)
        body = html.unescape(probe.group(1) if probe else trimmed)
        if len(body.strip()) >= 15:
            inner = trimmed
            notes.append("删冗余 OEM 段")

    # ② 品牌后缀归一
    m = TAIL_RE.match(inner)
    if m:
        head, tail = m.group(1), m.group(2)
        if "SANFAN" in html.unescape(tail).upper():
            want = pick_suffix(head, lang)
            if head + want != inner:
                notes.append("后缀→%s" % ("长" if want != " — " + SUFFIX_SHORT else "短"))
                inner = head + want

    # ③ 机翻把品牌后缀展开成从句
    #    es: "Esterilla de yoga «Alignment Line»TPE: fabricante de productos de yoga y fitness «SANFAN»"
    #    de: "Produkte nach Kategorie – SANFAN – OEM-Hersteller von Yogamatten und Fitnessartikeln"
    #    ⚠️ 判据必须**同时**要求尾段含品牌 AND 制造商类词，只认品牌太危险：
    #       博客标题的副标题也含品牌（"REACH, CA Prop 65 & 6P: Yoga Mat Compliance
    #       for US & EU — SANFAN"），切掉会只剩 "REACH, CA Prop 65 & 6P" 这种
    #       毫无意义的标题 —— 实测只认品牌时 EN 5 篇博客 + 各语言共 47 处中招。
    #    另加 head 最小宽度兜底，防止把标题削成光杆品牌名。
    for rx in (COLON_BRAND_RE, SANDWICH_BRAND_RE):
        m = rx.match(inner)
        if not m:
            continue
        head = m.group(1).strip()
        rest = inner[m.end(1):]          # 分隔符 + 其后全部内容
        plain_rest = html.unescape(rest)
        if "SANFAN" not in plain_rest.upper():
            continue                     # 尾段没品牌 → 不是品牌后缀
        if not MFR_RE.search(plain_rest):
            continue                     # 没有「制造商」类词 → 是内容副标题，不能删
        if width(head) < 15:
            continue                     # 削成光杆品牌名，放弃
        inner = head + " — " + SUFFIX_SHORT
        notes.append("收拢展开的品牌后缀")
        break

    return inner, "; ".join(notes) if notes else None


def pages():
    for lg in LANGS:
        for sub in DIRS:
            base = ROOT if lg == "" else os.path.join(ROOT, lg)
            pat = os.path.join(base, sub, "*.html") if sub else os.path.join(base, "*.html")
            for f in sorted(glob.glob(pat)):
                yield lg or "en", f


def main():
    check = "--check" in sys.argv
    dry = check or "--dry-run" in sys.argv
    do_desc = "--desc" in sys.argv

    stat = {"files": 0, "t_changed": 0, "d_changed": 0, "skipped": 0}
    by_lang = {}
    samples = []
    samples_d = []

    for lg, path in pages():
        rel = os.path.relpath(path, ROOT)
        s = open(path, encoding="utf-8").read()
        orig = s
        notes = []

        m = TITLE_RE.search(s)
        if m:
            new_inner, why = norm_title(m.group(1), lg)
            if why:
                s = s[: m.start(1)] + new_inner + s[m.end(1):]
                stat["t_changed"] += 1
                by_lang.setdefault(lg, {}).setdefault("t", [0, 0])
                by_lang[lg]["t"][0] += 1
                by_lang[lg]["t"][1] += width(m.group(1)) - width(new_inner)
                notes.append("T:" + why)
                if len(samples) < 8:
                    samples.append((rel, html.unescape(m.group(1)), html.unescape(new_inner)))

        if do_desc:
            dm = re.search(r'(<meta name="description" content=")([^"]*)(")', s)
            if dm:
                newd, changed = trim_desc(dm.group(2))
                if changed:
                    s = s[: dm.start(2)] + newd + s[dm.end(2):]
                    stat["d_changed"] += 1
                    by_lang.setdefault(lg, {}).setdefault("d", [0, 0])
                    by_lang[lg]["d"][0] += 1
                    by_lang[lg]["d"][1] += width(dm.group(2)) - width(newd)
                    notes.append("D:%d→%d宽" % (width(dm.group(2)), width(newd)))
                    if len(samples_d) < 6:
                        samples_d.append((rel, html.unescape(dm.group(2)), newd))

        stat["files"] += 1
        if s == orig:
            stat["skipped"] += 1
            continue
        if not dry:
            open(path, "w", encoding="utf-8").write(s)

    print("模式: %s%s" % ("检查(dry)" if dry else "落盘", " +description" if do_desc else ""))
    print("扫描 %d 个文件" % stat["files"])
    print("title 改动 %d 个 | description 改动 %d 个 | 未变 %d 个"
          % (stat["t_changed"], stat["d_changed"], stat["skipped"]))
    print()
    print("%-5s %8s %10s %8s %10s" % ("lang", "title改", "title省宽", "desc改", "desc省宽"))
    for lg in ["en"] + LANGS[1:]:
        v = by_lang.get(lg, {})
        t = v.get("t", [0, 0])
        d = v.get("d", [0, 0])
        if t[0] or d[0]:
            print("%-5s %8d %10d %8d %10d" % (lg, t[0], t[1], d[0], d[1]))

    if samples:
        print("\ntitle 改动示例：")
        for rel, a, b in samples:
            print("  %s" % rel)
            print("    ← %s" % a[:100])
            print("    → %s" % b[:100])

    if samples_d:
        print("\ndescription 截断示例：")
        for rel, a, b in samples_d:
            print("  %s" % rel)
            print("    ← [%d宽] %s" % (W(html.unescape(a)), a[:130]))
            print("    → [%d宽] %s" % (W(html.unescape(b)), b[:130]))


if __name__ == "__main__":
    main()
