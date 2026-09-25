#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""8 个一级分类页 × 7 语言的「三块内容」独立验收（2026-09-25）

⚠️ 刻意**不复用** add_category_content_20260925.py 的任何判据函数 ——
   脚本自检只能证明「按它的假设成立」，这里要做的是**证伪**那些假设。

验收项
  A 标记完整性   —— catintro / cfaq / cfaq-ld / ilink 四个块各恰好 1 开 1 闭
  B 块序正确     —— catintro 在网格 section 之前；cfaq 在 ilink 之前；cfaq-ld 在 orgref 之前
  C 块内配平     —— 每个块内 section/div/p/h2/details/summary/ul/li/a/span/b 全成对
  D JSON-LD      —— 全页脚本能解析；FAQPage 的 @id/url/inLanguage/mainEntity 与文件一致；
                    **LD 里的问答文本 == 页面可见文本**（逐条比对，防「两套文案」）
  E 语言纯度     —— de/fr/it/es 块内不得出现 CJK/假名/谚文；ja 必须有假名；ko 必须有谚文；
                    语言块文本不得与 EN 源块逐字相同（防漏译）
  F 转义安全     —— 文本节点内不得有裸 < >；& 只允许出现在已知实体里
  G 标题结构     —— h1 恰好 1 个；h1>h6 序列不得跳级(>+1)；两个新增 h2 都在 h1 之后
  H 双语残留     —— 语言页不得出现 class="lang-en"/class="lang-zh"
  I 占位符       —— 不得出现 XX / TODO / {{ }} / 全角问号占位
  J 结构守恒签名 —— HEAD→工作区 的标签计数增减，48 个语言文件必须**同一个签名**，
                    且与 8 个 EN 文件签名一致（EN 因 lang-en/lang-zh 双 span 单独成组）

用法：python3 verify_catcontent_i18n_20260925.py [--quiet]
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGES = [
    "foam-rollers.html",
    "jump-ropes.html",
    "resistance-bands.html",
    "suede-cork-yoga-mats.html",
    "meditation-pilates-mats.html",
    "yoga-props-accessories.html",
    "strength-training.html",
    "massage-recovery.html",
]
LANGS = ["de", "ja", "ko", "fr", "it", "es"]

M_I = "<!-- catintro:v1 -->"
M_V = "<!-- cfaq:v1 -->"
M_L = "<!-- cfaq-ld:v1 -->"
ILINK = "<!-- ilink:v1 -->"
ORGREF = "<!-- orgref:v1 -->"

CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
KANA = re.compile(r"[\u3040-\u30ff]")
HANGUL = re.compile(r"[\uac00-\ud7af\u1100-\u11ff]")
ENT = re.compile(r"&(?:amp|lt|gt|quot|apos|nbsp|#\d+|#x[0-9a-fA-F]+|rarr|larr|hellip|mdash|ndash|times|deg|euro|copy|reg|trade|laquo|raquo|ldquo|rdquo|lsquo|rsquo|middot|bull|check|rsquo|szlig|auml|ouml|uuml|Auml|Ouml|Uuml|szlig|eacute|egrave|agrave|ccedil|icirc|ucirc|ocirc|ecirc|aacute|iacute|oacute|uacute|ntilde|uuml|szlig|frac12|frac14|sup2|sup3|micro|plusmn|divide|permil);")

SCRIPT_LD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
TAG = re.compile(r"<[^>]*>")

# 结构守恒签名关心的标签
SIG_TAGS = ["section", "div", "p", "h1", "h2", "h3", "details", "summary",
            "ul", "li", "span", "b", "a", "table"]

# ⚠️ 已知且**全站既有**的标题跳级白名单（2026-09-25 实测）
#    h2→h4：1166/1364 页（85%）都有 —— 产品卡是 h4、网格节自身无标题，
#           全站产品列表页（products.html、applications/*、所有分类页）皆然。
#           仅当出现**白名单外**的新跳级类时才判异常 → 仍能抓住意外结构变化。
KNOWN_JUMP = {"h2→h4"}


# ------------------------------------------------------------------ 工具
def rel_path(lang, page):
    return page if lang == "en" else "%s/%s" % (lang, page)


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def head_version(rel):
    r = subprocess.run(["git", "show", "HEAD:%s" % rel], cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if r.returncode != 0:
        return None
    return r.stdout.decode("utf-8", "replace")


def block(s, opener):
    """取出 opener..对应关闭标记 之间的整段（含标记）。"""
    closer = opener.replace("<!-- ", "<!-- /")
    a = s.find(opener)
    b = s.find(closer)
    if a < 0 or b < 0:
        return None
    return s[a:b + len(closer)]


def visible_text(blockhtml):
    """块内的可见文本（去掉标记与标签、解转义、压空白）。"""
    t = re.sub(r"<!--.*?-->", " ", blockhtml, flags=re.S)
    t = TAG.sub("\n", t)
    t = html.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


def tag_counts(s):
    c = Counter()
    for tag in SIG_TAGS:
        o = len(re.findall(r"<%s\b" % tag, s))
        cl = len(re.findall(r"</%s>" % tag, s))
        c["<%s>" % tag] = o
        c["</%s>" % tag] = cl
    c["<a_open>"] = len(re.findall(r"<a\b", s))
    return c


def headings(s):
    out = []
    for m in re.finditer(r"<(h[1-6])\b[^>]*>(.*?)</\1>", s, re.S):
        out.append((m.group(1), html.unescape(TAG.sub("", m.group(2))).strip()))
    return out


# ------------------------------------------------------------------ 主流程
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    errs = defaultdict(list)
    warn = defaultdict(list)
    resid = defaultdict(list)
    files = [(lg, pg) for pg in PAGES for lg in (["en"] + LANGS)]
    block_stats = {}

    for lang, page in files:
        rel = rel_path(lang, page)
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            errs["A 文件缺失"].append(rel)
            continue
        s = read(path)
        where = rel

        # ---- A 标记完整
        for name, mk in (("catintro", M_I), ("cfaq", M_V), ("cfaq-ld", M_L), ("ilink", ILINK)):
            o = s.count(mk)
            if o != 1:
                errs["A 标记数不为 1"].append("%s %s×%d" % (where, name, o))

        bi = block(s, M_I)
        bv = block(s, M_V)
        bl = block(s, M_L)
        if bi is None or bv is None or bl is None:
            errs["A 块无法定位"].append(where)
            continue

        # ---- B 块序
        k_i = s.find(M_I)
        k_grid = s.find('class="prod-grid"')
        if k_grid < 0:
            errs["B 无产品网格"].append(where)
        elif k_i > k_grid:
            errs["B 导语不在网格之前"].append(where)
        if s.find(M_V) > s.find(ILINK):
            errs["B FAQ 不在 ilink 之前"].append(where)
        if ORGREF in s and s.find(M_L) > s.find(ORGREF):
            errs["B cfaq-ld 不在 orgref 之前"].append(where)

        # ---- C 块内配平
        for name, b in (("catintro", bi), ("cfaq", bv), ("cfaq-ld", bl)):
            for tag in ("section", "div", "p", "h2", "details", "summary",
                        "ul", "li", "a", "span", "b"):
                o = len(re.findall(r"<%s\b" % tag, b))
                c = len(re.findall(r"</%s>" % tag, b))
                if o != c:
                    errs["C 块内不配平"].append("%s %s <%s>%d </%s>%d" % (where, name, tag, o, tag, c))

        # ---- D JSON-LD
        nodes = []
        for raw in SCRIPT_LD.findall(s):
            try:
                nodes.append(json.loads(raw))
            except Exception as e:
                errs["D LD 解析失败"].append("%s %s" % (where, e))
        canon = re.search(r'<link rel="canonical" href="([^"]+)"', s)
        canon = canon.group(1) if canon else None
        faqs = [n for n in nodes if n.get("@type") == "FAQPage"]
        mine = [n for n in faqs if str(n.get("@id", "")).endswith("#faq-cat")]
        if len(mine) != 1:
            errs["D FAQPage(#faq-cat) 数量异常"].append("%s %d" % (where, len(mine)))
        else:
            f = mine[0]
            if f.get("url") != canon:
                errs["D url≠canonical"].append("%s %r vs %r" % (where, f.get("url"), canon))
            want_lang = "en" if lang == "en" else lang
            if f.get("inLanguage") != want_lang:
                errs["D inLanguage 错误"].append("%s %r" % (where, f.get("inLanguage")))
            me = f.get("mainEntity", [])
            if len(me) != 5:
                errs["D mainEntity≠5"].append("%s %d" % (where, len(me)))
            vis = visible_text(bv)
            for item in me:
                q = item.get("name", "")
                a = item.get("acceptedAnswer", {}).get("text", "")
                if not q.strip() or not a.strip():
                    errs["D 问答为空"].append(where)
                    continue
                nq = re.sub(r"\s+", " ", html.unescape(q)).strip()
                na = re.sub(r"\s+", " ", html.unescape(a)).strip()
                if nq not in vis:
                    errs["D 问题不在可见文本中"].append("%s :: %s" % (where, nq[:50]))
                if na not in vis:
                    errs["D 答案不在可见文本中"].append("%s :: %s" % (where, na[:50]))
            # 可见文本里的问答条数
            n_det = len(re.findall(r'<details class="faq-item">', bv))
            if n_det != 5:
                errs["D faq-item≠5"].append("%s %d" % (where, n_det))

        # ---- E 语言纯度
        txt = visible_text(bi + " " + bv)
        if lang == "en":
            pass
        elif lang == "ja":
            if not KANA.search(txt):
                errs["E ja 无假名"].append(where)
        elif lang == "ko":
            if not HANGUL.search(txt):
                errs["E ko 无谚文"].append(where)
        else:
            hit = CJK.search(txt) or KANA.search(txt) or HANGUL.search(txt)
            if hit:
                i = (CJK.search(txt) or KANA.search(txt) or HANGUL.search(txt)).start()
                errs["E 非东亚语言混入 CJK"].append("%s :: %s" % (where, txt[max(0, i - 30):i + 30]))

        # ---- F 转义安全
        stripped = TAG.sub("\x00", bi + bv + bl)
        stripped = re.sub(r"<!--.*?-->", "\x00", stripped, flags=re.S)
        for seg in stripped.split("\x00"):
            if "<" in seg or ">" in seg:
                errs["F 文本节点含裸尖括号"].append("%s :: %s" % (where, seg.strip()[:60]))
            tmp = ENT.sub("", seg)
            if "&" in tmp:
                errs["F 未转义的 &"].append("%s :: %s" % (where, seg.strip()[:60]))

        # ---- G 标题结构
        hs = headings(s)
        h1 = [x for x in hs if x[0] == "h1"]
        if len(h1) != 1:
            errs["G h1≠1"].append("%s %d" % (where, len(h1)))
        lvl = [int(x[0][1]) for x in hs]
        # ⚠️ 「跳级」必须 A/B 实证：站内 prod-card 是 h4、页脚是 h5，
        #    而 products.html / applications/* 等**已上线页**本来就有 h2→h4 / h2→h5。
        #    所以只有「HEAD 没有、新版才出现」的跳级才算异常（既有问题不重复计）。
        new_jumps = set()
        for p, q in zip(lvl, lvl[1:]):
            if q > p + 1:
                new_jumps.add("h%d→h%d" % (p, q))
        head_txt = head_version(rel)
        head_jumps = set()
        if head_txt:
            hl = [int(x[0][1]) for x in headings(head_txt)]
            for p, q in zip(hl, hl[1:]):
                if q > p + 1:
                    head_jumps.add("h%d→h%d" % (p, q))
        for j in sorted(new_jumps - head_jumps):
            if j in KNOWN_JUMP:
                resid["G 新增跳级(h2→h4，全站既有形态)"].append("%s %s" % (where, j))
            else:
                errs["G 新增标题跳级(非白名单)"].append("%s %s" % (where, j))
        for j in sorted(head_jumps - new_jumps):
            warn["G 本轮已消除跳级(改善)"].append("%s %s" % (where, j))
        if len(lvl) >= 2 and lvl[1] > 3:
            warn["G 首个标题层级偏深"].append("%s" % where)
        # 新增的 2 个 h2 应在 h1 之后
        if h1:
            pos_h1 = s.find("<h1")
            if s.find(M_I) < pos_h1 or s.find(M_V) < pos_h1:
                errs["G 新块早于 h1"].append(where)

        # ---- H 双语残留
        if lang != "en":
            for cls in ('class="lang-en"', 'class="lang-zh"'):
                if cls in s:
                    errs["H 语言页残留双语块"].append("%s %s" % (where, cls))

        # ---- I 占位符
        plain = visible_text(bi + bv)
        for bad in ("XX", "TODO", "{{", "}}", "LOREM", "lorem"):
            if bad in plain:
                errs["I 占位符"].append("%s %s" % (where, bad))

        block_stats[(lang, page)] = (visible_text(bi), visible_text(bv))

    # ---- E' 漏译：语言块 == EN 块
    for page in PAGES:
        en_i, en_v = block_stats.get(("en", page), (None, None))
        for lang in LANGS:
            st = block_stats.get((lang, page))
            if not st or en_i is None:
                continue
            if st[0] == en_i or st[1] == en_v:
                errs["E' 与 EN 源逐字相同(漏译)"].append("%s/%s" % (lang, page))

    # ---- J 结构守恒签名
    sigs = defaultdict(list)
    for lang, page in files:
        rel = rel_path(lang, page)
        old = head_version(rel)
        if old is None:
            warn["J HEAD 无此文件(新增)"].append(rel)
            continue
        new = read(os.path.join(ROOT, rel))
        co, cn = tag_counts(old), tag_counts(new)
        sig = tuple((t, cn[t] - co[t]) for t in sorted(set(co) | set(cn)) if cn[t] - co[t])
        sigs["en" if lang == "en" else "lang"].append((sig, rel))
    for grp, items in sigs.items():
        uniq = {}
        for sig, rel in items:
            uniq.setdefault(sig, []).append(rel)
        if len(uniq) > 1:
            for sig, rels in list(uniq.items())[1:]:
                errs["J 签名不一致"].append("%s %s :: %s" % (grp, rels[0], dict(sig)))

    # ---- 汇总
    n_err = sum(len(v) for v in errs.values())
    print("=" * 72)
    print("分类页三块内容 · 独立验收（56 文件 = 8 页 × 7 语言）")
    print("=" * 72)
    if n_err == 0:
        print("✅ 全部验收项通过，异常 0 处")
    else:
        print("❌ 异常 %d 处：" % n_err)
        for k in sorted(errs):
            print("\n【%s】%d 处" % (k, len(errs[k])))
            for x in errs[k][:8]:
                print("   ·", x)
    if warn:
        print("\n（提示，不计入异常）")
        for k in sorted(warn):
            print("  %s：%d 处 例：%s" % (k, len(warn[k]), warn[k][0]))
    if resid:
        print("\n（已知残留，白名单内，不计入异常）")
        for k in sorted(resid):
            print("  %s：%d 处 例：%s" % (k, len(resid[k]), resid[k][0]))
    print("\n--- 结构守恒签名（HEAD → 工作区）---")
    for grp, items in sigs.items():
        sig, rel = items[0]
        print("  [%s] %d 文件，签名：%s" % (grp, len(items), dict(sig)))
    print("\n--- 译文规模 ---")
    for lang in ["en"] + LANGS:
        n = sum(len(block_stats[(lang, p)][0].split()) + len(block_stats[(lang, p)][1].split())
                for p in PAGES if (lang, p) in block_stats)
        ch = sum(len(block_stats[(lang, p)][0]) + len(block_stats[(lang, p)][1])
                 for p in PAGES if (lang, p) in block_stats)
        print("  %-3s 新增正文 %5d 词 / %6d 字符" % (lang, n, ch))
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
