#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P2-206：强化现有页去吃 `pvc vs tpe yoga mat`（不新建页）× 7 语言。

判据（GSC 2026-09-13 导出，28 天）：
  · `pvc vs tpe yoga mat`   1 曝光 / 位置 67.0
  · `pvc in yoga mats`      2 曝光 / 位置 94.5
  两个词都进了展现，但站内 —— **全站任何页面都没有出现过「PVC vs TPE」这个短语**
  （实测 grep 0 命中）。materials.html 提了 PVC 28 次，却只有「八种材质九维表」里
  一行 + 一张卡片，没有正面对比的标题与结论。这正是 query 要的东西。

落地：
  1. materials.html：在 #compare 与 #detail 之间插一节 `id="pvc-vs-tpe"`，
     H2 写「Yoga mats: PVC vs TPE compared」+ 五点对照表 + 结论段 + 2 条内链。
     ⚠️ **只放九维表里没有的东西**（增塑剂气味 / 重量 / 采购接受度 / 供给能力 /
        价格带），防滑·耐用·厚度·定制·最适合都已在正上方那张表里，不重复。
     表格事实来源：本页九维表（PVC 4–8 mm、3–4 年最耐磨、不可回收、价格带 ●○○○、
     「有增塑剂气味且不可回收，在零售与酒店采购越来越难过关」）+ blog/tpe-vs-pu.html
     自己的表（TPE 6 mm 183 × 61 cm ≈ 1.1 kg）。不新造数字。
  2. blog/tpe-vs-pu.html：在每个语言块最后一条 h2（FAQ 标题）之前插一小节，
     把上游问题引到 materials.html#pvc-vs-tpe。

锚点（跨语言稳定，不依赖译文文本）：
  · materials：插在 `<section class="section" id="detail">` 之前（该串 7 语言一致）
  · blog：对每个 `<!-- ilink:v1 -->`，回退到它之前**最近的 `<h2>`** 插入
    （每个语言块里 ilink 前最后一个 h2 就是 FAQ 标题），**从后往前**处理防索引漂移

⭐ 本轮踩到的两个机翻硬规律（源文已按此改写，写在这里免得下次再踩）：
  ① **绝不能让待译串以受保护术语开头**。`PVC vs TPE: how …` 这类串，
     六语言会把 `vs` 吃掉（de `PVC TPE-Yogamatten`）、或把术语甩到句首
     （fr `PVC Le TPE, ou… : c'est la question`）。换个词打头就全好：
     `Yoga mats: PVC vs TPE compared` → de "Yogamatten: PVC vs. TPE im Vergleich"。
  ② **短单元格必须写成完整小句**，否则引擎按字面猜领域：
     `Good dry, fair wet` → de "Gut bei trockener **Fahrbahn**"（路面）、
     ja "乾燥**路面**"；`About 1.1 kg` → fr "**Informazioni su** 1.1 kg"；
     `Can you make it?` → fr "Tu vas pouvoir **venir** ?"（你能来吗）。
     改写成完整从句后六语言全部正常。
  另有 `cleaner` 一词被 fr/es/ja 读成「防滑更好」，改写成
  「the one that contains no plasticisers」即解。
"""
import argparse
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import translator  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = pathlib.Path(__file__).resolve().parent / "pvc_vs_tpe_data.json"

LANGS = ["de", "ja", "ko", "fr", "it", "es"]

M_OPEN = "<!-- pvctpe:v1 -->"
M_CLOSE = "<!-- /pvctpe:v1 -->"

DOTS = ("●○○○", "●●○○")

# ------------------------------------------------------------------ 内容
# rows: (label, pvc, tpe) —— 每项都是 (EN, ZH)，raw 行不翻译
ROWS = [
    (
        ("Plasticisers, and odour when the mat is unrolled",
         "增塑剂，以及垫子展开时的气味"),
        ("Contains plasticisers unless you specify otherwise, and the smell fades but rarely disappears.",
         "除非特别指定，否则含增塑剂；气味会变淡，但很少彻底散尽。"),
        ("Contains no plasticisers and no phthalates, and the mat has no smell when it is unrolled.",
         "不含增塑剂、不含邻苯类物质，垫子展开时也没有气味。"),
    ),
    (
        ("Weight for the same mat size", "同尺寸的重量"),
        ("The denser compound, so a mat of the same size weighs more.",
         "料本身密度更高，所以同尺寸更重。"),
        ("A 6 mm 183 × 61 cm mat weighs about 1.1 kg, which keeps freight per unit down.",
         "6 mm、183 × 61 cm 约 1.1 kg，单件运费更省。"),
    ),
    (
        ("Retail and hotel procurement", "零售与酒店采购"),
        ("Procurement teams increasingly refuse it on sustainability grounds.",
         "采购方越来越常以可持续性为由拒收。"),
        ("Procurement teams accept it without discussion.",
         "采购方直接接受，不需要额外解释。"),
    ),
    (
        ("Price band at factory gate", "出厂价带"),
        (DOTS[0], DOTS[0]),
        (DOTS[1], DOTS[1]),
    ),
    (
        ("Availability from our factory", "我们工厂能否供应"),
        ("Yes, on request — and we will tell you when it is the wrong call.",
         "可以，按需生产 —— 但如果这是错的选择，我们会直说。"),
        ("Yes, it is our highest-volume line, running on five dedicated production lines.",
         "可以 —— 这是我们产能最大的产品线，专设 5 条产线在跑。"),
    ),
]

MAT = {
    "h2": ("Yoga mats: PVC vs TPE compared", "瑜伽垫：PVC 与 TPE 对比"),
    "lead": ("The table above covers both materials. These are the five points that actually "
             "decide it, and the answer we would give you on a call.",
             "两种材质都在上面的总表里。下面这五点才是真正决定选择的地方，"
             "也是你在电话里会从我们口中得到的答复。"),
    "th": ("Point", "对比项"),
    "foot": ("Price band: ●○ least expensive → ●●●● most expensive. Grip, durability, thickness "
             "and customisation for both materials are in the table above.",
             "价格带：●○ 最经济 → ●●●● 最高。两种材质的防滑、耐用、厚度与定制能力"
             "都在上面的总表里。"),
    "verdict": (
        "Short version: PVC is the cheaper and more abrasion-resistant material, and TPE is the "
        "one that contains no plasticisers. Both are dry-grip products, so neither of them is a "
        "hot-yoga answer — that is PU on rubber. The only reason to choose PVC in 2026 is a price "
        "point that leaves no room for TPE, and TPE is the only one of the two that can be "
        "recycled at end of life. We make both, so we quote whichever you ask for; and we will "
        "tell you when PVC is going to fail your buyer's procurement, because a refused shipment "
        "costs more than the material saving.",
        "一句话：PVC 更便宜、更耐磨，TPE 是不含增塑剂的那个。两者都是干手产品，"
        "所以都不是高温瑜伽的答案 —— 那是 PU 橡胶。到了 2026 年，选 PVC 的唯一理由"
        "就是那个价格带容不下 TPE；而两者中只有 TPE 能在报废后回收。"
        "两种我们都做，你要哪种我们就报哪种；但如果 PVC 会卡在你买家的采购环节上，"
        "我们也会直说，因为一批被拒收的货，比省下的料钱贵得多。"),
}

BLOG = {
    "h2": ("The question before this one: PVC vs TPE", "更靠前的一个问题：PVC 还是 TPE"),
    "p": ("Half the buyers who land on this page are really asking a question one step earlier: "
          "PVC or TPE? It matters because in most mat ranges, TPE has already replaced PVC. A "
          "PVC mat is cheaper and very abrasion-resistant, but it carries plasticiser odour and "
          "cannot be recycled in practice, so it increasingly fails retail and hospitality "
          "procurement. TPE is closed-cell, phthalate-free, recyclable and lighter to ship. If "
          "your brief is the cheapest mat that still sells, PVC is the honest answer and we will "
          "quote it; if your brief is a mat your buyer's compliance team will accept, start at "
          "TPE.",
          "找到这一页的买家里，有一半其实问的是更靠前一步：PVC 还是 TPE？"
          "这个问题重要，是因为在大多数项目里，TPE 换掉的就是 PVC。"
          "PVC 垫更便宜、极耐磨，但有增塑剂气味、实际上不可回收，"
          "在零售与酒店采购环节越来越难过关。TPE 闭孔、不含邻苯类物质、可回收，"
          "而且同尺寸下更轻、运费更省。如果你的目标是「还能卖得动的最便宜那张垫」，"
          "PVC 是诚实答案，我们照样报价；如果是「我买家那边的合规团队能过」，就从 TPE 起步。"),
}

# blog 那条例行链接**不翻译**，直接用站内既有译法（各语言 materials.html 里
# 指向 blog/yoga-mat-materials.html 的锚文本，实测抓取）
BLOG_LINK = {
    "en": "Yoga Mat Materials Compared", "de": "Materialvergleich für Yogamatten",
    "ja": "ヨガマット素材比較", "ko": "요가 매트 소재 비교",
    "fr": "comparaison des matériaux", "it": "confronto dei materiali",
    "es": "comparativa de materiales",
}
BLOG_LINK_ZH = "瑜伽垫材质横评"

# ⭐ 链接文案**直接取站内既有译法**，不重新翻译：
#   LINK1_PAGE = 各语言 TPE 分类页的 h1（实测抓取）
#   LINK2_PAGE = 各语言 materials.html 里指向 blog/tpe-vs-pu.html 的既有锚文本
LINK1 = {
    "en": "TPE yoga mats", "de": "TPE Yogamatten", "ja": "TPE ヨガマット", "ko": "TPE 요가 매트",
    "fr": "TPE Tapis de yoga", "it": "TPE Tappetini da yoga", "es": "TPE Esterillas de yoga",
}
LINK2 = {
    "en": "TPE vs PU rubber: which to choose", "de": "TPE oder PU: der Vergleich",
    "ja": "TPE と PU の比較", "ko": "TPE와 PU 비교", "fr": "TPE ou PU : la comparaison",
    "it": "TPE o PU: il confronto", "es": "TPE o PU: la comparación",
}
LINK2_ZH = "TPE 与 PU 橡胶怎么选"
LINK1_ZH = "TPE 瑜伽垫"


def price_dots(cell):
    return cell in DOTS


def en_strings():
    out = [MAT["h2"][0], MAT["lead"][0], MAT["th"][0], MAT["foot"][0], MAT["verdict"][0],
           BLOG["h2"][0], BLOG["p"][0]]
    for lab, pvc, tpe in ROWS:
        out.append(lab[0])
        if not price_dots(pvc[0]):
            out.append(pvc[0])
            out.append(tpe[0])
    return out


# ------------------------------------------------------------------ 译文出口修补
# ⚠️ 通用规则（term_repair）只清**排版引号**（含日式「」），因为 ASCII 直引号
#    在 HTML 属性与 JSON-LD 里是语法字符。本脚本处理纯文本，可一并清。
_Q = "[\u201e\u201c\u201d\u00ab\u00bb\u2039\u203a\u2018\u2019\u300c\u300d\u300e\u300f\"]"
_TERM_Q = (r"(?:TPEE|TPE|PVC|PU|NBR|EVA|SBR|EEP|ROHS|REACH|SGS|BSCI|MOQ|OEM|ODM|CE"
           r"|ISO\s?9001|CA\s?Prop\s?65|EN\s?71|OEKO-?TEX|CPSIA"
           r"|\d+(?:\.\d+)?\s?(?:mm|cm|kg|g)\b)")
_QUOTE_RE = re.compile(_Q + r"\s*(" + _TERM_Q + r")\s*" + _Q + r"(?![A-Za-z])")

POST = [
    (r"\bkgs\b", "kg"),                     # fr/es「1.1 kgs」——kg 不随数变化
    # ko 助词：PVC / TPE 读作 피브이씨 / 티피이，**都以元音结尾** → 主语 가、宾语 를、와
    # 只改**错的那几个**（对的不动）：term_repair 那边有专门的说明，谚文侧不能写通用规则。
    (r"\bPVC과(?![가-힣])", "PVC와"),
    (r"\bPVC을(?![가-힣])", "PVC를"),
    (r"\bTPE이(?![가-힣])", "TPE가"),
    (r"\bTPE을(?![가-힣])", "TPE를"),
]


def clean(t):
    prev = None
    while prev != t:
        prev, t = t, _QUOTE_RE.sub(r"\1", t)
    for rx, rep in POST:
        t = re.sub(rx, rep, t)
    return t


def build_data(force=False):
    src = en_strings()
    if DATA.exists() and not force:
        d = json.loads(DATA.read_text(encoding="utf-8"))
        if all(all(s in d.get(lg, {}) for s in src) for lg in LANGS):
            # ⚠️ 缓存必须在**读取时**也跑 clean + 自检：写入时干净 ≠ 读出来还干净。
            #    一旦清洗规则（字符集/术语表）事后扩过，旧缓存会带着脏译文一直命中，
            #    且缓存命中不调 API、不重跑编码路径 → 永不自愈。就地清洗并回写。
            healed = []
            for lg in LANGS:
                for s in list(d.get(lg, {})):
                    t = clean(d[lg][s])
                    if t != d[lg][s]:
                        healed.append((lg, d[lg][s][:38], t[:38]))
                        d[lg][s] = t
            if healed:
                DATA.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
                for lg, a, b in healed:
                    print("  [缓存自愈] %s: %s … → %s …" % (lg, a, b))
            for lg in LANGS:
                for s, t in d[lg].items():
                    assert not _QUOTE_RE.search(t), "[%s] 引号残留：%s" % (lg, t[:80])
            return d
    print("  待译 EN 串 %d 条 × %d 语言" % (len(src), len(LANGS)))
    d = {}
    for lg in LANGS:
        tr = translator.translate_lines(src, lg.upper())
        assert len(tr) == len(src), (lg, len(tr))
        d[lg] = {s: clean(t) for s, t in zip(src, tr)}
        for s, t in d[lg].items():
            if len(s.split()) >= 3 and t.strip() == s.strip():
                raise SystemExit("[%s] 译文回声：%s" % (lg, s[:70]))
            assert not _QUOTE_RE.search(t), "[%s] 引号残留：%s" % (lg, t[:80])
    DATA.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print("  已写 %s（%.1f KB）" % (DATA.name, DATA.stat().st_size / 1024))
    translator.flush()
    return d


# ------------------------------------------------------------------ 渲染
def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def pair(en, zh, lang):
    if lang == "en":
        return ('<span class="lang-en">%s</span><span class="lang-zh">%s</span>'
                % (esc(en), esc(zh)))
    return "<span >%s</span>" % esc(en)


def mkT(lang, tr):
    def T(s):
        return s if lang == "en" else clean(tr[lang][s])
    return T


def render_mat(lang, tr):
    T = mkT(lang, tr)
    rows = []
    for lab, pvc, tpe in ROWS:
        if price_dots(pvc[0]):
            c2 = '<span class="price-dots">%s</span>' % DOTS[0]
            c3 = '<span class="price-dots">%s</span>' % DOTS[1]
        else:
            c2 = pair(T(pvc[0]), pvc[1], lang)
            c3 = pair(T(tpe[0]), tpe[1], lang)
        rows.append(
            '            <tr>\n'
            '              <th scope="row">%s</th>\n'
            '              <td>%s</td>\n'
            '              <td>%s</td>\n'
            '            </tr>' % (pair(T(lab[0]), lab[1], lang), c2, c3))
    l1 = pair(LINK1[lang], LINK1_ZH, lang)
    l2 = pair(LINK2[lang], LINK2_ZH, lang)
    return (
        "%s\n"
        '  <section class="section" id="pvc-vs-tpe">\n'
        '    <div class="container">\n'
        '      <div class="section-head">\n'
        '        <div class="eyebrow">%s</div>\n'
        "        <h2>%s</h2>\n"
        "        <p>%s</p>\n"
        "      </div>\n"
        '      <div class="mat-wrap">\n'
        '        <table class="mat-table">\n'
        '          <thead><tr><th scope="col">%s</th>'
        '<th scope="col">PVC</th><th scope="col">TPE</th></tr></thead>\n'
        "          <tbody>\n%s\n          </tbody>\n"
        "        </table>\n"
        "      </div>\n"
        '      <p style="font-size:12.5px;color:var(--muted);margin:12px 2px 0;">%s</p>\n'
        '      <p style="max-width:820px;margin:18px auto 0;line-height:1.75;">%s</p>\n'
        '      <p style="max-width:820px;margin:10px auto 0;line-height:1.75;">'
        '<a href="tpe-yoga-mats.html">%s &rarr;</a></p>\n'
        '      <p style="max-width:820px;margin:4px auto 0;line-height:1.75;">'
        '<a href="blog/tpe-vs-pu.html">%s &rarr;</a></p>\n'
        "    </div>\n"
        "  </section>\n"
        "%s"
        % (M_OPEN,
           pair("PVC vs TPE", "PVC 与 TPE", lang),
           pair(T(MAT["h2"][0]), MAT["h2"][1], lang),
           pair(T(MAT["lead"][0]), MAT["lead"][1], lang),
           pair(T(MAT["th"][0]), MAT["th"][1], lang),
           "\n".join(rows),
           pair(T(MAT["foot"][0]), MAT["foot"][1], lang),
           pair(T(MAT["verdict"][0]), MAT["verdict"][1], lang),
           l1, l2, M_CLOSE)
    )


def render_blog(lang, tr):
    T = mkT(lang, tr)
    ind = " " * 12
    return (
        "%s\n"
        "%s<h2>%s</h2>\n"
        "%s<p>%s</p>\n"
        "%s<p><a href=\"../materials.html#pvc-vs-tpe\">%s &rarr;</a></p>\n"
        "%s"
        % (M_OPEN, ind, pair(T(BLOG["h2"][0]), BLOG["h2"][1], lang), ind,
           pair(T(BLOG["p"][0]), BLOG["p"][1], lang), ind,
           pair(BLOG_LINK[lang], BLOG_LINK_ZH, lang), M_CLOSE)
    )


# ------------------------------------------------------------------ 剥 / 插（严格互逆）
def _block_re(tail):
    return re.compile(re.escape(M_OPEN) + r".*?" + re.escape(M_CLOSE) + re.escape(tail), re.S)


def strip_mat(s):
    return _block_re("\n").sub("", s)


def strip_blog(s):
    return _block_re("\n\n").sub("", s)


def insert_mat(s, block):
    i = s.index('<section class="section" id="detail">')
    j = s.rfind("\n", 0, i) + 1
    return s[:j] + block + "\n" + s[j:]


def insert_blog_all(s, block):
    """在每个 `<!-- ilink:v1 -->` 之前最近的 `<h2>` 处插入（**从后往前**，防索引漂移）"""
    out = s
    idxs = sorted((m.start() for m in re.finditer(re.escape("<!-- ilink:v1 -->"), out)),
                  reverse=True)
    for i in idxs:
        h = out.rindex("<h2", 0, i)
        j = out.rfind("\n", 0, h) + 1
        out = out[:j] + block + "\n\n" + out[j:]
    return out


# ------------------------------------------------------------------ 主流程
def process(path, lang, tr, apply_, stats, kind):
    s = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT).as_posix()
    if kind == "mat":
        block = render_mat(lang, tr)
        t = strip_mat(s)
        assert M_OPEN not in t, rel
        t2 = insert_mat(t, block)
        assert t2.replace(block + "\n", "", 1) == t, "%s 回退断言失败" % rel
        expect = 1
    else:
        block = render_blog(lang, tr)
        t = strip_blog(s)
        assert M_OPEN not in t, rel
        t2 = insert_blog_all(t, block)
        expect = 2 if lang == "en" else 1
        chk = t2
        for _ in range(expect):
            assert block + "\n\n" in chk, "%s 回退断言失败" % rel
            chk = chk.replace(block + "\n\n", "", 1)
        assert chk == t, "%s 回退断言不严格" % rel

    assert t2.count(M_OPEN) == expect and t2.count(M_CLOSE) == expect, (rel, t2.count(M_OPEN))
    assert "XX" not in re.sub(r"<[^>]+>", "", block), rel
    assert 'href="href=' not in t2, rel
    for href in re.findall(r'href="([^"]+)"', block):
        # block 里的 href 一律是**相对页面所在目录**的路径（语言页结构与根镜像，写法相同）
        assert (path.parent / href.split("#")[0]).exists(), "%s 坏链 %s" % (rel, href)
    changed = t2 != s
    if changed and apply_:
        path.write_text(t2, encoding="utf-8")
    stats["changed" if changed else "same"] += 1
    stats["pages"] += 1
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--retranslate", action="store_true")
    args = ap.parse_args()

    if args.check:
        bad, n = [], 0
        for lg in [""] + [x + "/" for x in LANGS]:
            for f, k in (("materials.html", "mat"), ("blog/tpe-vs-pu.html", "blog")):
                p = ROOT / (lg + f)
                n += 1
                s = p.read_text(encoding="utf-8")
                want = 2 if (k == "blog" and lg == "") else 1
                if s.count(M_OPEN) != want:
                    bad.append((str(p.relative_to(ROOT)), "块数 %d≠%d" % (s.count(M_OPEN), want)))
                if k == "mat" and 'id="pvc-vs-tpe"' not in s:
                    bad.append((str(p.relative_to(ROOT)), "缺 #pvc-vs-tpe"))
        print("检查 %d 页 | 异常 %d" % (n, len(bad)))
        for b in bad:
            print("  ", b)
        sys.exit(1 if bad else 0)

    print("=== 准备译文 ===")
    tr = build_data(force=args.retranslate)

    stats = {"pages": 0, "changed": 0, "same": 0}
    for lg in ["en"] + LANGS:
        d = "" if lg == "en" else lg + "/"
        process(ROOT / (d + "materials.html"), lg, tr, args.apply, stats, "mat")
        process(ROOT / (d + "blog/tpe-vs-pu.html"), lg, tr, args.apply, stats, "blog")
        print("  %-3s 2 页 %s" % (lg, "已更新" if args.apply else "待更新"))
    print("\n合计 %d 页 | 需改动 %d | 无需改动 %d %s"
          % (stats["pages"], stats["changed"], stats["same"],
             "（已落盘）" if args.apply else "（空跑）"))


if __name__ == "__main__":
    main()
