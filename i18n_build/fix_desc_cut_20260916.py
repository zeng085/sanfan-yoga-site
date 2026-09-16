#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修「断头 description」—— 把被字数硬截断的描述接回完整句子（2026-09-16）

【病根】
fix_desc_unique.py（2026-09-12）为了消重，把 >165 字符的描述用 fit() 硬截到
≤160 **字符**：在最后一个空格处切，既不认句末标点，也不看 B2B 钩子。
后果是全站 364 个页面（1331 页中）description 结尾是半句话：

    products/cork-surface-pu-rubber-yoga-mat.html
      …customizable thick. The premium grip specification for      ← 断头
    de/products/cork-surface-pu-rubber-yoga-mat.html
      …in individueller Stärke erhältlich. Die Premium-Grip-Spezifikation für
    ko/products/ym1.html
      …두께 6–12 mm(1/4"–1/2"). 솔리드, 이코노미 및

英文源页与 6 个语言页各自被切过一刀，切点还各不相同 —— 所以这不是「翻译问题」，
是**截断器缺陷**，且已由翻译管线原样传播到 7 个语言版本。

⚠️ 与 trim_meta_20260915.py 的分工：那个管「已知完整、只是太长」；
   本脚本管「根本就是半句话」，判断依据是结尾有没有句末标点。

【修法】三级，全部基于页面里**已有的文本**，不新写文案、不重新翻译：
  ⓪ 人工补完 MANUAL_RULES
     18 个页面对齐不上、也截不出完整句（博客索引/文章页根本没写 JSON-LD
     description），按尾巴逐个补完 —— 全部锚定末尾、补完即句末，天然幂等。
  ① 接续 splice
     JSON-LD 的 description 往往保留着截断前的完整原文 —— fix_desc_unique
     当时只裁了 meta 三处（description / og / twitter），**没碰结构化数据**。
     用 difflib 对齐 meta 与候选文本，取**最优公共块**：块之前的部分保留，
     块之后 v 的断头片段丢掉、接上候选文本块之后的续写。
        EN : "…customizable thick. The premium grip specification for"
             + " hot yoga and studio use."                    （块正好到 v 末尾）
        de : "…erhältlich. Die Premium-Grip-Spezifikation für"    ← 断头片段丢掉
             + "Premium-Grip-Ausführung für Hot Yoga und den Einsatz im Studio."
             （de 的 meta 与 JSON-LD 是两遍不同译法，句中"Specifikation/Ausführung"
               分叉 —— 纯追加接不上，必须换成替换式对齐）
     四道闸：
       · 公共块 ≥ 20 宽        （防止撞上短巧合短语接出乱码）
       · 丢掉的断头片段 ≤ 100 宽（丢太多说明不是同一句）
       · 接续部分 3–140 宽      （接一整个段落说明是两份不同文案，不是同一句续写）
       · 接完必须落在句末标点上（否则等于没修）
     同页另外两处 meta（og / twitter）也当候选 —— 实测有 6 页 meta 被裁、
     og 保留全文，可直接回灌。

  ② 兜底 trim
     对不齐时就在**最后一个句末标点**处收尾，断头片段整段丢掉。
     收尾后不足 DESC_MIN_KEEP 宽则放弃 —— 宁可保留长文让 Google 自己截，
     也不交给搜索引擎一句残句。

【只动什么】
· 只改 description / og:description / twitter:description 里**断头**的那些字段。
  结尾已是句末标点（含 » ） " 等收尾符）的字段一律不动。
· JSON-LD 不动（本轮只诊断：--check 会报出 JSON-LD 也断头的页数）。
· 幂等：修完的字段结尾必是句末标点，再跑一次不会命中。

用法：
    python3 fix_desc_cut_20260916.py --check              # 只报告（默认）
    python3 fix_desc_cut_20260916.py --dry-run            # 打印逐页改动明细
    python3 fix_desc_cut_20260916.py --apply              # 落盘
    python3 fix_desc_cut_20260916.py --check fr           # 只看某语言
"""
import difflib
import glob
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ("de", "ja", "ko", "fr", "it", "es")

# 三处 meta：字段名 → 正则（捕获 content 值）
FIELDS = [
    ("desc", re.compile(r'(<meta name="description" content=")([^"]*)(")')),
    ("og", re.compile(r'(<meta property="og:description" content=")([^"]*)(")')),
    ("tw", re.compile(r'(<meta name="twitter:description" content=")([^"]*)(")')),
]
JSONLD_RE = re.compile(r'"description"\s*:\s*"((?:[^"\\]|\\.)*)"')
HEAD_BYTES = 60000

# 「已经收尾」的判定集合：句末标点 + 各种右引号/右括号
OK_END = ".!?。！？：；:;…»”\"')）"
SENT_END_CHARS = ".!?。！？"

MIN_OVERLAP_W = 20        # 公共块最小显示宽度
MAX_DROP_W = 100          # 允许丢掉的断头片段上限
MAX_SPLICE_W = 140        # 接续部分最大显示宽度
DESC_MIN_KEEP = 60        # 兜底截断后至少留这么宽，否则放弃

# ---------------------------------------------------------------- 人工补完规则
# 这 18 个页面的 JSON-LD 里没有可对齐的原文（博客索引/文章页根本没写
# JSON-LD description），对齐不上、也截不出完整句 —— 只能按尾巴逐个补完。
# 规则锚定在字段末尾，补完即句末标点，天然幂等。
# de 的两条同时修掉粘连硬伤「frei von PVCund」→「frei von PVC und」。
MANUAL_RULES = [
    # —— 博客索引页（列表型：末项被切断）——
    ("",   r"factory vetting, fast$",
           "factory vetting, fast delivery."),
    ("de", r"Überprüfung der Hersteller, schnelle Lieferung$",
           "Überprüfung der Hersteller, schnelle Lieferung."),
    ("fr", r"vérification des usines, rapidité$",
           "vérification des usines, rapidité de livraison."),
    ("it", r"verifica delle fabbriche, rapidità$",
           "verifica delle fabbriche, rapidità di consegna."),
    ("es", r"verificación de fábricas, rapidez$",
           "verificación de fábricas, rapidez de entrega."),
    ("ja", r"工場の審査、短納期$",
           "工場の審査、短納期。"),
    ("ko", r"공장 심사, 신속한$",
           "공장 심사, 신속한 납기."),
    # —— vet-factory 博客文章（末句被切断）——
    ("",   r"and what a transparent$",
           "and what a transparent factory quote should contain."),
    ("de", r"und was eine transparente$",
           "und was eine transparente Fabrikofferte enthalten sollte."),
    ("fr", r"et ce qu'est une$",
           "et ce qu'une offre d'usine transparente doit contenir."),
    ("ja", r"そして透明性のある$",
           "そして透明性のある工場見積もりに含まれるべき内容。"),
    ("ko", r"그리고 투명한$",
           "그리고 투명한 공장 견적에 포함되어야 할 내용."),
    # —— 列表型页面：末项其实是完整的，只缺句号 ——
    ("fr", r"conditionnement pour la vente au détail$",
           "conditionnement pour la vente au détail."),
    ("fr", r"gamme d'épaisseurs$", "gamme d'épaisseurs."),
    ("fr", r"gamme d&rsquo;épaisseurs$", "gamme d&rsquo;épaisseurs."),
    ("it", r"fasce elastiche$", "fasce elastiche."),
    # —— de 木林森系列：粘连硬伤 + 列表补完 ——
    ("de", r"frei von PVCund$", "frei von PVC und geruchlos."),
    ("de", r"frei von PVC und$", "frei von PVC und geruchlos."),
]
COMPILED_MANUAL = [(lg, re.compile(rx), rep) for lg, rx, rep in MANUAL_RULES]


def W(s):
    """近似显示宽度：CJK/全角算 2，其余算 1。"""
    return sum(2 if ord(c) > 0x2E80 else 1 for c in s)


def is_dangling(v):
    v = v.strip()
    return bool(v) and v[-1] not in OK_END


def esc_attr(v):
    """写回 HTML 属性：只转义必需的四个字符，撇号保持原样（站内两种写法并存，
    最小转义可避免把整段属性的撇号编码风格改掉，diff 更干净）。"""
    return (v.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def lang_of(rel):
    head = rel.split("/")[0]
    return head if head in LANGS else ""


def try_manual(v, lang):
    """按人工补完规则收尾。返回 (新文本, 命中说明) 或 None。"""
    for lg, rx, rep in COMPILED_MANUAL:
        if lg != lang:
            continue
        m = rx.search(v)
        if m:
            return rx.sub(rep, v), rep[-28:]
    return None


def join(left, right):
    """按两侧字符类型决定接续时要不要补空格。"""
    if not left or not right:
        return left + right
    a, b = left[-1], right[0]
    cjk = lambda c: ord(c) > 0x2E80
    if cjk(a) or cjk(b) or a.isspace() or b.isspace() or b in ".,;:!?)]»":
        return left + right
    return left + " " + right


def try_splice(v, cands):
    """用 difflib 对齐，取最优公共块：块前保留、块后换成候选文本的续写。

    返回新文本或 None。判据见文件头「四道闸」。
    """
    best = None                       # (score, 公共块宽, new, common)
    for cand in cands:
        if not cand or cand == v or len(cand) < 20:
            continue
        sm = difflib.SequenceMatcher(None, v, cand, autojunk=False)
        for i, j, size in sm.get_matching_blocks():
            if not size:
                continue
            common = v[i:i + size]
            v_tail = v[i + size:]
            cand_tail = cand[j + size:]
            if W(common) < MIN_OVERLAP_W:
                continue
            if W(v_tail) > MAX_DROP_W:
                continue
            if not (3 <= W(cand_tail) <= MAX_SPLICE_W):
                continue
            new = join(v[: i + size], cand_tail)
            if is_dangling(new):
                continue
            score = W(v_tail) + W(cand_tail)
            key = (score, -W(common))
            if best is None or key < best[0]:
                best = (key, W(common), new, common)
    return (best[2], best[3]) if best else None


def try_trim(v):
    """在最后一个句末标点处收尾。返回新文本或 None。"""
    plain = v.rstrip()
    cut = ""
    for m in re.finditer(r"[.!?。！？]", plain):
        cut = plain[: m.end()].rstrip()
    if not cut or cut == plain:
        return None
    if W(cut) < DESC_MIN_KEEP:
        return None
    # 末尾若是常见缩写（z.B. / vs.）不算句末
    if re.search(r"(?:^|\s)(?:vs|z\.b|u\.a|bzw|usw|etc|ca|inkl|e\.g|i\.e|max|min)\.$",
                 plain[: len(cut)], re.I):
        return None
    return cut


def fix_page(rel, content, write):
    """返回 (action_list, new_content)。"""
    actions = []
    lang = lang_of(rel)
    cands = [html.unescape(x).replace("\\/", "/").strip()
             for x in JSONLD_RE.findall(content)]
    metas = {}
    for name, rx in FIELDS:
        m = rx.search(content)
        if m:
            metas[name] = html.unescape(m.group(2)).strip()
    # 同页其余 meta 也当候选
    for name, val in metas.items():
        cands.append(val)

    new_content = content
    for name, rx in FIELDS:
        m = rx.search(new_content)
        if not m:
            continue
        raw, val = m.group(2), html.unescape(m.group(2)).strip()
        if not is_dangling(val):
            continue
        note = ""
        man = try_manual(val, lang)
        if man is not None:
            new_val, note = man
            how = "manual"
        else:
            res = try_splice(val, cands)
            if res is not None:
                new_val, common = res
                how, note = "splice", common[-40:]
            else:
                new_val = try_trim(val)
                how = "trim"
        if new_val is None or new_val == val:
            actions.append((name, "无法修复", W(val), W(val), val[-50:], ""))
            continue
        new_content = new_content[: m.start(2)] + esc_attr(new_val) + new_content[m.end(2):]
        actions.append((name, how, W(val), W(new_val), new_val[-50:], note))
    return actions, new_content


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    apply_ = "--apply" in sys.argv
    dry = "--dry-run" in sys.argv
    prefix = args[0] if args else ""
    os.chdir(ROOT)

    stat = {"pages": 0, "dangling_fields": 0, "splice": 0, "trim": 0,
            "manual": 0, "fail": 0, "written": 0}
    fails, details = [], []
    jsonld_dangling = 0
    for f in sorted(glob.glob("**/*.html", recursive=True)):
        if prefix and not f.startswith(prefix):
            continue
        with open(f, encoding="utf-8", errors="replace") as fh:
            content = fh.read(HEAD_BYTES)
        if content.count("\n") < 2:
            continue
        actions, new_content = fix_page(f, content, apply_)
        if not actions:
            continue
        stat["pages"] += 1
        stat["dangling_fields"] += len(actions)
        for name, how, w0, w1, tail, note in actions:
            if how == "splice":
                stat["splice"] += 1
            elif how == "trim":
                stat["trim"] += 1
            elif how == "manual":
                stat["manual"] += 1
            else:
                stat["fail"] += 1
                fails.append((f, name, tail))
            details.append((f, name, how, w0, w1, tail, note))
        if new_content != content:
            stat["written"] += 1
            if apply_:
                with open(f, "w", encoding="utf-8") as fh:
                    fh.write(new_content)
        # 诊断：JSON-LD 自身断头的页数
        for x in JSONLD_RE.findall(content):
            if is_dangling(html.unescape(x).replace("\\/", "/").strip()):
                jsonld_dangling += 1
                break

    mode = "落盘" if apply_ else ("预演" if dry else "检查")
    print("模式: %s%s" % (mode, " [%s]" % prefix if prefix else ""))
    print("断头页 %d | 断头字段 %d | 对齐接续 %d | 人工补完 %d | 截断收尾 %d | 无法修复 %d"
          % (stat["pages"], stat["dangling_fields"], stat["splice"],
             stat["manual"], stat["trim"], stat["fail"]))
    print("其中 JSON-LD 自身也断头的页: %d" % jsonld_dangling)
    if dry:
        print("-" * 110)
        for f, name, how, w0, w1, tail, note in details:
            print("%-58s %-5s %-7s %3d→%3d  …%s" % (f, name, how, w0, w1, tail))
            if note:
                print(" " * 72 + "对齐块尾: %s" % note)
    if fails:
        print("\n⚠️ 接不上也截不了（需人工）：")
        for f, name, tail in fails:
            print("  %-58s %-5s …%s" % (f, name, tail))


if __name__ == "__main__":
    main()
