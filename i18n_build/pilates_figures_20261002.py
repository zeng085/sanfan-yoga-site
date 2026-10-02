# -*- coding: utf-8 -*-
"""普拉提器械公布数据的单一事实来源（SSOT）。

为什么需要这个文件
──────────────────
2026-10-02 的 GEO 审计发现博客里有两处「最高级断言」可被证伪：
  · "the longest published packing length is 2570 mm"  ← 实际最长是 AL 13 MC 的 2800 mm
  · "the tallest is 860 mm"                           ← 860 只是 AL 12-CR 自身的高度，
                                                        塔架类木箱实际高达 2000 mm
两处都是**硬编码的断言**脱离了数据源。修一次不够 —— 只要文案里的极值还是手写的，
下次换画册/加型号就还会错。

所以极值一律从这里算出来，博客生成器 import 本模块取值，不手写数字。

基准是什么
──────────
已上线的族页 `pilates/*.html` 型号总表（`<tr><td class="model">` 行）。那是画册数据
已经发布出去的形态，也是与站点其他页面保持一致的口径来源。注意**不要**用
`i18n_build/reports/pilates_catalog_2026_models.csv` 当基准：那份报告缺行
（69 行 vs 族页 73 行），会误判 AL 19-F / AL 8-Y 这类型号「无据」。

用法
────
    from pilates_figures_20261002 import EXTREMES, TRIPLES, KGS, verify_page
    EXTREMES["longest"]   # {'value': 2800, 'unit': 'mm', 'model': 'AL 13 MC'}
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

_ROW_RE = re.compile(r'<tr><td class="model">([^<]+)</td>((?:(?!</tr>).)*)', re.S)
# ⚠️ 不能只抓型号总表：梯桶族页（pilates-ladder-barrel.html）**只有型号卡、没有总表**，
#    只抓 <tr> 会让该族的 1190×700×1170 / 90 kg 被判「无据」→ 假警报。
#    两种形态都要抓，按型号名去重。
_CARD_RE = re.compile(
    r'<article class="model-card"[^>]*>\s*<h3>([^<]+)</h3>((?:(?!</article>).)*)', re.S)
_TRIPLE_RE = re.compile(r"(\d{2,4})\s*×\s*(\d{2,4})\s*×\s*(\d{2,4})\s*mm")
_KG_RE = re.compile(r"(\d+(?:\.\d+)?)\s*kg")


def _family_pages():
    d = os.path.join(ROOT, "pilates")
    return sorted(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".html"))


def load():
    """→ (rows, triples, kgs)
    rows    : [(model, [triple…], [kg…], page)]   —— 按型号，用于算极值
    triples : {triple}                            —— 全站公布过的三级尺寸
    kgs     : {float}                             —— 全站公布过的毛重
    """
    rows, triples, kgs = [], set(), set()
    for path in _family_pages():
        with open(path, encoding="utf-8") as fh:
            html = fh.read()
        page = os.path.basename(path)
        seen = set()
        for rx in (_ROW_RE, _CARD_RE):
            for m in rx.finditer(html):
                model = m.group(1).strip()
                if model in seen:
                    continue
                seen.add(model)
                seg = m.group(2)
                tr = [(int(a), int(b), int(c)) for a, b, c in _TRIPLE_RE.findall(seg)]
                kg = [float(v) for v in _KG_RE.findall(seg)]
                if tr or kg:
                    rows.append((model, tr, kg, page))
                    triples.update(tr)
                    kgs.update(kg)
    return rows, triples, kgs


ROWS, TRIPLES, KGS = load()


def _extreme(needle, axis, unit):
    """axis 0/1/2 = 长/宽/高；返回取得该维度最大值的型号。"""
    best = None
    for model, tr, _kg, _page in ROWS:
        for t in tr:
            if best is None or t[axis] > best[0]:
                best = (t[axis], model, t)
    return {"value": best[0], "unit": unit, "model": best[1], "crate": best[2]}


def _heaviest():
    best = None
    for model, _tr, kg, _page in ROWS:
        for v in kg:
            if best is None or v > best[0]:
                best = (v, model)
    return {"value": int(best[0]) if float(best[0]).is_integer() else best[0],
            "unit": "kg", "model": best[1]}


EXTREMES = {
    "longest": _extreme("longest", 0, "mm"),
    "widest": _extreme("widest", 1, "mm"),
    "tallest": _extreme("tallest", 2, "mm"),
    "heaviest": _heaviest(),
}

# 通用净空/门洞尺寸 —— 属行业通用值，不是本厂公布数据，允许出现在文案里
GENERIC_MM = {600, 700, 800, 900, 1000, 1100, 1200, 1500, 2000, 2100, 2400}


def verify_numbers(html, page=""):
    """页面里的尺寸/重量数字必须能在族页公布数据里找到。
    返回 (ok, problems)。problems = [(kind, value, snippet)]"""
    problems = []
    flat = re.sub(r"\s+", " ", html)

    page_triples = {(int(a), int(b), int(c)) for a, b, c in _TRIPLE_RE.findall(flat)}
    for t in sorted(page_triples):
        if t not in TRIPLES:
            problems.append(("triple", "%d × %d × %d mm" % t, page))

    for v in sorted({float(x) for x in _KG_RE.findall(flat)}):
        if v not in KGS:
            problems.append(("kg", "%s kg" % (int(v) if v.is_integer() else v), page))

    return (not problems), problems


# 最高级断言的句式。⚠️ 正则必须「紧」：早先写成 [^.]{0,80} 会把
# "the longest side, so a standard 900 mm door" 也当成「最长=900」→ 假警报。
# 收紧到「同一分句内」（不容忍 , . ; :）后，实测 6 页零误报。
_SUPERLATIVE_EN = re.compile(
    r"\b(longest|widest|tallest)\b[^.,;:]{0,50}?\b(\d{3,4})\s*mm", re.I)
_SUPERLATIVE_EN2 = re.compile(
    r"\b(\d{3,4})\s*mm\b[^.,;:]{0,40}?\bis\s+the\s+(longest|widest|tallest)", re.I)
# "930 mm as the widest" 这类「数字在前 + as the」句式（并列列举常用）
_SUPERLATIVE_EN3 = re.compile(
    r"\b(\d{3,4})\s*mm\b[^.,;:]{0,40}?\bas\s+the\s+(longest|widest|tallest)", re.I)
_SUPERLATIVE_ZH = re.compile(r"最(长|宽|高|重)[^。，；]{0,30}?(\d{3,4})\s*(mm|kg)")


def verify_superlatives(html, page=""):
    """最高级断言必须等于从族页算出的极值。

    ⚠️ 必须先把三级尺寸整体剔除：否则「最长的 2800 × 680 × 450 mm」会被正则
       匹配到三元组末尾的 450 mm → 假警报（实测踩过）。
    """
    text = _TRIPLE_RE.sub(" 〔尺寸〕", html)
    axis_of = {"longest": "longest", "widest": "widest", "tallest": "tallest",
               "长": "longest", "宽": "widest", "高": "tallest", "重": "heaviest"}
    problems = []
    for m in _SUPERLATIVE_EN.finditer(text):
        word, num = m.group(1).lower(), int(m.group(2))
        want = EXTREMES[word]["value"]
        if num != want:
            problems.append((word, num, want, page, re.sub(r"\s+", " ", m.group(0))[:110]))
    for m in _SUPERLATIVE_EN2.finditer(text):
        word, num = m.group(2).lower(), int(m.group(1))
        want = EXTREMES[word]["value"]
        if num != want:
            problems.append((word, num, want, page, re.sub(r"\s+", " ", m.group(0))[:110]))
    for m in _SUPERLATIVE_EN3.finditer(text):
        word, num = m.group(2).lower(), int(m.group(1))
        want = EXTREMES[word]["value"]
        if num != want:
            problems.append((word, num, want, page, re.sub(r"\s+", " ", m.group(0))[:110]))
    for m in _SUPERLATIVE_ZH.finditer(text):
        key, num, unit = axis_of[m.group(1)], int(m.group(2)), m.group(3)
        want = EXTREMES[key]["value"]
        if int(want) != num:
            problems.append((key, num, want, page, re.sub(r"\s+", " ", m.group(0))[:110]))
    return (not problems), problems


if __name__ == "__main__":
    print("基准：pilates/*.html 型号总表 —— %d 个型号行 / %d 个公布尺寸 / %d 个毛重值"
          % (len(ROWS), len(TRIPLES), len(KGS)))
    for k, v in EXTREMES.items():
        print("  %-9s %5s %-4s  ← %s" % (k, v["value"], v["unit"], v["model"]))
