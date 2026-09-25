#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P2-205：给 tpe-yoga-mats.html / pu-rubber-yoga-mats.html 两个分类页补 FAQ
（可见区块 + FAQPage 同步）× 7 语言 = 14 页。

为什么这两页？
  站内 12 个分类页里只有 materials.html 有 FAQ（4 问）；tpe 页仅有 EVA 段的 2 问，
  pu 页一问没有。而这两个页是 GSC 里少数已有曝光的商业页所在品类，
  补 FAQ 是最直接的 GEO（AI 引用）抓手。

内容口径：
  - 全部事实取自页面自身（hero 文案 + 产品卡规格），不新造数字。
     TPE：183 cm 长 / 宽 61·66·80·90 cm（更宽至 122）/ 4–12 mm / 6·8 mm 走量 /
          单双层 / 拼色·迷彩·体位线 / 100 pcs 起订 / 约 7 天出样 / 翻单 20–30 天 /
          ROHS·CE·REACH·ISO 9001·BSCI·SGS
     PU ：天然橡胶底 + 吸湿 PU 面层 / 1.5–5 mm / 183×68·185×68·181×66 /
          绒感·磨砂·可印花 / 100 pcs 起订 / 约 7 天出样 / 生产 25–35 天 / Pantone
  - ⚠️ 刻意**不与 materials.html 现有 FAQ 撞题**（那 4 问是"哪种材质最好""TPE 是否比 PVC 环保"
    "多厚""能否寄样"），这里只写各自品类的落地问题（材质构成 / 尺寸厚度 / 定制能力 /
    起订与交期 / 检测），避免站内重复内容。

⚠️ 为什么 tpe 页会出现**两个 FAQPage 节点**（#faq 与 #faq-cat）：
   #faq 是 2026-09-24 EVA 改动的产物，归属 `inject_eva_tpe_note_20260924.py`
   的 `EVA-TPE-FAQ-LD-START/END` 标记区间。本脚本**绝不碰别人标记区间内的内容**
   （否则该脚本重跑会静默抹掉本脚本的问答 —— 站内已踩过这个坑），
   因此另起 block，用独立的 `#faq-cat` 锚点。问答完全不重叠，AI 引擎两个节点都会读。

写法（与 add_internal_links / add_products_faq 一致）：
  剥块 → 重插，插入/剥除**严格互逆**（插 `block + "\n\n"`，剥 `block` + 紧随的两个换行），
  所以 `strip(insert(s)) == s` 恒成立、重跑零漂移。

⚠️ 译文的两个坑（实测，源文已按此改写）：
  1. **术语被加引号**：术语被包成保护标签后引擎看不见它，会补一对引号
     （de `„TPE“-Yogamatte`、fr `« TPE »`、it `“TPE”`、ja `「TPE」マット`）。
     已在 `term_repair.py` 加通用规则在译文出口清掉；ASCII 直引号在**纯文本上下文**
     里由本脚本的 `clean()` 一并清（不能在通用规则里清 —— 那是 HTML/JSON 的语法字符）。
  2. **引擎幻觉**：ko 把 "no phthalates, no latex and no PVC" 译成
     `프탈레이트, 라텍스, 포름알데히드(PVC)` —— 凭空多出一个「甲醛」。
     与站内 es `bifenilo`（联苯）是同一类病，规则化不了，走 OVERRIDES 手写。
  另外「ROHS, CE and REACH」这种三元素逗号清单**六语言都会塌**（de 变成 `ROHS (CE) und REACH`，
  CE 被吃掉），务必改成「for ROHS, CE and REACH」句式或用斜杠分隔；
  「6 mm and 8 mm are the volume/best-selling thicknesses」里受保护的数字会破坏句子结构
  （ja 只剩「6 mmおよび8 mmは厚みです」），必须改写成「The best-selling thicknesses are 6 mm and 8 mm.」。
"""
import argparse
import html
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import translator  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = pathlib.Path(__file__).resolve().parent / "category_faq_data.json"

LANGS = ["de", "ja", "ko", "fr", "it", "es"]

M_V_OPEN = "<!-- cfaq:v1 -->"
M_V_CLOSE = "<!-- /cfaq:v1 -->"
M_L_OPEN = "<!-- cfaq-ld:v1 -->"
M_L_CLOSE = "<!-- /cfaq-ld:v1 -->"

V_ANCHOR = "<!-- ilink:v1 -->"
L_ANCHOR = "<!-- orgref:v1 -->"

# ------------------------------------------------------------------ 内容（EN 源 + 中文手写）
PAGES = {
    "tpe-yoga-mats.html": {
        "h2": (
            "TPE yoga mat questions buyers ask",
            "买家会问的 TPE 瑜伽垫问题",
        ),
        "qa": [
            (
                "What is a TPE yoga mat made of?",
                "TPE 瑜伽垫是什么材质做的？",
                "Closed-cell thermoplastic elastomer foam — no phthalates, no latex and no PVC, "
                "and no rubber or plastic smell when the mat is unrolled. We compound and foam it "
                "in-house, so density and firmness are set to your brief rather than taken off a "
                "generic sheet.",
                "闭孔热塑性弹性体发泡材质 —— 不含邻苯类增塑剂、不含乳胶、不含 PVC，"
                "拆卷后也没有橡胶味或塑料味。发泡是我们自己车间做的，"
                "密度与软硬度按你的要求调，不是拿通用板材切。",
            ),
            (
                "Which sizes and thicknesses can you run?",
                "你们能做哪些尺寸和厚度？",
                "Standard length is 183 cm, in widths of 61 cm, 66 cm, 80 cm and 90 cm, from "
                "4 mm to 12 mm. The best-selling thicknesses are 6 mm and 8 mm. Wider formats up "
                "to 122 cm, and non-standard sizes, come off the same mould family, so they need a "
                "quotation but no new tooling.",
                "标准长度 183 cm，宽度 61 cm、66 cm、80 cm、90 cm，厚度 4 mm 到 12 mm，"
                "其中最好卖的是 6 mm 与 8 mm。最宽可做到 122 cm；"
                "非标尺寸与常规规格共用同一套模具，所以只需要报价，不需要重新开模。",
            ),
            (
                "Can the mat carry our own print, embossed logo and packaging?",
                "能印我们自己的图案、压印 Logo 和包装吗？",
                "Yes. Solid, dual-colour, spliced and camouflage surfaces, alignment lines, "
                "embossed or printed logos, printed carry straps, and retail packaging with your "
                "barcode — all in one production run. Send us the artwork and we confirm which "
                "effects survive repeated folding and cleaning before you commit.",
                "可以。纯色、双色、拼色与迷彩表面，体位线，压印或印刷 Logo，印花背带，"
                "带条码的零售包装 —— 一次生产就能全做完。把设计稿发来，"
                "我们会先告诉你哪些效果经得起反复折叠和清洁，再让你决定。",
            ),
            (
                "What is the MOQ and lead time for a private-label TPE mat?",
                "贴牌 TPE 垫的起订量和交期是多少？",
                "MOQ is 100 pcs per colour and design; samples with your logo take about 7 days, "
                "and repeat production runs 20 to 30 days from artwork sign-off. Colourways can be "
                "combined in a single order as long as each one meets the 100 pcs minimum.",
                "起订量 100 片／颜色与款式；带 Logo 的样品约 7 天；"
                "翻单生产在确认设计稿后 20 到 30 天。多个颜色可以并到一张订单，"
                "只要每个颜色各满 100 片。",
            ),
            (
                "What testing comes with a TPE mat order?",
                "下单会附哪些检测？",
                "Testing is issued per material and colour for ROHS, CE and REACH, backed by "
                "ISO 9001 and BSCI audits at the plant and SGS third-party testing on request. We "
                "tell you which tests your market actually requires instead of sending a generic "
                "pack.",
                "按材质与颜色出具 ROHS、CE 与 REACH 检测报告，工厂有 ISO 9001 与 BSCI 审核背书，"
                "可按需做 SGS 第三方检测。我们会告诉你你的目标市场到底需要哪些测试，"
                "而不是发一份通用资料包了事。",
            ),
        ],
    },
    "pu-rubber-yoga-mats.html": {
        "h2": (
            "PU rubber yoga mat questions buyers ask",
            "买家会问的 PU 橡胶瑜伽垫问题",
        ),
        "qa": [
            (
                "How is a PU rubber yoga mat built?",
                "PU 橡胶瑜伽垫是怎么做成的？",
                "A natural rubber base bonded to a moisture-absorbing PU top layer. The rubber "
                "stops the mat sliding on the floor and provides the cushioning; the PU gives the "
                "dry, matte hand-feel and the grip. It is the construction behind most premium "
                "studio and hot-yoga mats.",
                "天然橡胶底贴合吸湿 PU 面层。橡胶负责不在地上打滑、提供缓冲；"
                "PU 负责干爽磨砂的手感与防滑。绝大多数高端馆用垫与高温瑜伽垫都是这个结构。",
            ),
            (
                "Why choose PU rubber over TPE for hot yoga?",
                "高温瑜伽为什么选 PU 橡胶而不是 TPE？",
                "Because PU grips better once it is wet, which is exactly the problem in a heated "
                "class — TPE gets slippery. For general retail at a lower price point, TPE is "
                "usually the better value. Tell us the class type and the retail price band and we "
                "recommend one rather than quote both.",
                "因为 PU 越湿越防滑，而这正好是高温教室的核心问题 —— TPE 出汗后会打滑。"
                "如果是一般零售、价格带更低，TPE 通常性价比更好。"
                "告诉我们课程类型与零售价带，我们只推荐一种，不会两份都报。",
            ),
            (
                "What thickness and size options are there?",
                "厚度和尺寸有哪些选择？",
                "Thickness options start at 1.5 mm for travel and ultra-thin studio mats, and go "
                "up to 5 mm with cushioning. The common formats are 183 × 68 cm, 185 × 68 cm and "
                "181 × 66 cm, and size, shape and corners are customizable. Suede-feel, matte and "
                "print-ready surfaces are all available.",
                "最薄 1.5 mm，用于旅行与超薄馆用垫；带缓冲可做到 5 mm。"
                "常用规格为 183 × 68 cm、185 × 68 cm、181 × 66 cm，尺寸、形状与圆角均可定制。"
                "绒感、磨砂与可印花表面都能做。",
            ),
            (
                "How do we look after a PU rubber mat?",
                "PU 橡胶垫平时怎么保养？",
                "Wipe it with water and a pH-neutral cleaner, dry it flat, and keep it out of a hot "
                "car. Heat and detergent are what break the PU layer down; practice does not. "
                "Looked after properly, expect two to three years of daily studio use.",
                "用清水加 pH 中性的清洁剂擦拭，平摊晾干，别放在暴晒的车里。"
                "让 PU 面层老化的是高温和洗涤剂，不是练习。"
                "保养得当，天天上课的馆用垫可以用两到三年。",
            ),
            (
                "What is the MOQ, and can you match our Pantone colour?",
                "起订量多少？能匹配我们的 Pantone 色号吗？",
                "MOQ is 100 pcs per colour and design, samples in about 7 days, and production 25 "
                "to 35 days after sign-off. PU rubber needs a longer cure than TPE, so book the "
                "launch window accordingly. Pantone matching on the PU top layer, debossed or "
                "printed logos and custom packaging are all standard.",
                "起订量 100 片／颜色与款式，约 7 天出样，确认设计稿后 25 到 35 天生产 —— "
                "PU 橡胶的固化时间比 TPE 长，排上市档期要留出这段。"
                "PU 面层可对 Pantone 色号，压印或印刷 Logo、定制包装都是标准配置。",
            ),
        ],
    },
}


def all_en_strings():
    out = []
    for spec in PAGES.values():
        out.append(spec["h2"][0])
        for q_en, _q_zh, a_en, _a_zh in spec["qa"]:
            out.extend([q_en, a_en])
    return out


# ------------------------------------------------------------------ 手写覆盖
# 引擎在下面几处**语义出错**（不是措辞问题），规则化不了，按 (语言, EN 源串) 覆盖。
# 键由 PAGES 反查，避免手抄源串对不上。
def _src(page, idx, part):
    item = PAGES[page]["qa"][idx]
    return item[0] if part == "q" else item[2]


OVERRIDES = {
    # ⚠️ 幻觉：EN 是 "no phthalates, no latex and no PVC"，
    #    ko 译成 `프탈레이트, 라텍스, 포름알데히드(PVC)` —— 凭空多出「甲醛」。
    ("ko", _src("tpe-yoga-mats.html", 0, "a")):
        "폐쇄 기공 구조의 열가소성 엘라스토머 폼으로, 프탈레이트·라텍스·PVC가 전혀 들어 있지 않고 "
        "매트를 펼쳤을 때 고무나 플라스틱 냄새도 나지 않습니다. 배합과 발포를 당사 공장에서 직접 "
        "하기 때문에, 밀도와 경도는 일반 규격표가 아니라 고객님의 요구에 맞춰 설정합니다.",

    # ⚠️ EN "…backed by ISO 9001 and BSCI audits at the plant and SGS third-party testing
    #    on request." 被译成「gemäß SGS」（按照 SGS）—— SGS 是执行方，不是标准。
    ("de", _src("tpe-yoga-mats.html", 4, "a")):
        "ROHS, CE und REACH weisen wir je Material und Farbe nach, belegt durch ISO 9001- und "
        "BSCI-Audits im Werk und auf Wunsch durch eine Prüfung beim unabhängigen Dienstleister "
        "SGS. Wir sagen Ihnen, welche Tests Ihr Markt wirklich verlangt, statt ein pauschales "
        "Paket zu schicken.",

    # ⚠️ fr 同样把执行方 SGS / ISO 说成标准：「audits menés par ISO 9001」。
    ("fr", _src("tpe-yoga-mats.html", 4, "a")):
        "Les essais sont réalisés par matériau et par couleur pour les normes ROHS, CE et REACH, "
        "et s'appuient sur les audits ISO 9001 et BSCI de l'usine ainsi que, sur demande, sur des "
        "essais SGS réalisés par un organisme tiers. Nous vous indiquons les essais réellement "
        "exigés par votre marché, plutôt que de vous envoyer un dossier générique.",

    # ⚠️ it：本站 it 页面统一用复数称呼（voi），这句却落了单数 tu（Ti indichiamo）。
    ("it", _src("tpe-yoga-mats.html", 4, "a")):
        "I test vengono emessi per materiale e colore per le norme ROHS, CE e REACH, con il "
        "supporto delle certificazioni ISO 9001 e BSCI dello stabilimento e, su richiesta, di "
        "test SGS effettuati da organismi terzi. Vi indichiamo quali test richiede davvero il "
        "vostro mercato, invece di inviare un pacchetto generico.",

    # ⚠️ fr 把 "Why choose PU rubber over TPE" 译成「préférer le caoutchouc PU à celui de TPE」——
    #    「à celui de」指代错位，读起来是「比 TPE 的那个」。改为直白的「plutôt que」。
    ("fr", _src("pu-rubber-yoga-mats.html", 1, "q")):
        "Pourquoi choisir le caoutchouc PU plutôt que le TPE pour le yoga chaud ?",
}


# ------------------------------------------------------------------ 引号清洗
# ⚠️ 通用规则（term_repair）只清**排版引号**，因为 ASCII 直引号在 HTML 属性
#    （`content="TPE"`）与 JSON-LD（`"material": "TPE"`）里是语法字符，那里清会改坏页面。
#    本脚本处理的是**纯文本**（译文 / 手写串），所以直引号可以一起清。
# ⚠️⚠️ 字符集必须与 term_repair.Q 对齐，**含日式「」『』**（2026-09-25 补齐）。
#    踩坑：这里最初照抄了 term_repair 的旧版 Q，漏掉日文引号；而写入时的自检用的是
#    **同一份残缺字符集**，于是 ja 的 `「TPE」マット` / `「PU」のゴムマット` 双双漏网——
#    清洗、自检两处同时失明，跑多少遍都不会报错。日文引号在日文译文里是**最常用**的一对，
#    漏它等于 ja 全语言裸奔。
_Q = "[\u201e\u201c\u201d\u00ab\u00bb\u2039\u203a\u2018\u2019\u300c\u300d\u300e\u300f\"]"
_TERM_Q = (r"(?:TPEE|TPE|PVC|PU|NBR|EVA|SBR|EEP|ROHS|REACH|SGS|BSCI|MOQ|OEM|ODM|CE"
           r"|ISO\s?9001|CA\s?Prop\s?65|EN\s?71|OEKO-?TEX|CPSIA)")
_QUOTE_RE = re.compile(_Q + r"\s*(" + _TERM_Q + r")\s*" + _Q + r"(?![A-Za-z])")


def clean(t):
    """剥掉紧贴术语的多余引号（迭代到不动点）。"""
    prev = None
    while prev != t:
        prev, t = t, _QUOTE_RE.sub(r"\1", t)
    return t


def build_data(force=False):
    src = all_en_strings()
    if DATA.exists() and not force:
        d = json.loads(DATA.read_text(encoding="utf-8"))
        if all(all(s in d.get(lg, {}) for s in src) for lg in LANGS):
            # ⚠️⚠️ 缓存必须在**读取时**跑 clean + 自检，不能只在写入时跑（2026-09-25 修）。
            #    踩坑：清洗字符集后来才补全日文引号（见 _Q 注释），而旧缓存里已经写死了
            #    `「TPE」マット…`。缓存命中不调 API、也不重跑编码路径 → 脏译文**永不自愈**，
            #    重跑多少遍页面都不变。这是项目笔记里「投毒后重跑不自愈」的又一实例。
            #    这里就地清洗并回写，让缓存能自我修复。
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
                print("  已回写 %s" % DATA.name)
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
        # 手写覆盖
        for (olg, osrc), txt in OVERRIDES.items():
            if olg == lg and osrc in d[lg]:
                d[lg][osrc] = txt
        # 回声检测：多词长句原样返回 = 引擎失败
        for s, t in d[lg].items():
            if len(s.split()) >= 3 and t.strip() == s.strip():
                raise SystemExit("[%s] 译文回声（未翻译）：%s" % (lg, s[:70]))
        # 引号残留自检
        for s, t in d[lg].items():
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


def render_section(lang, h2, qa):
    items = []
    for q0, q1, a0, a1 in qa:
        items.append(
            '        <details class="faq-item">\n'
            "          <summary>%s</summary>\n"
            '          <div class="faq-a">%s</div>\n'
            "        </details>" % (pair(q0, q1, lang), pair(a0, a1, lang))
        )
    return (
        "%s\n"
        '  <section class="section soft">\n'
        '    <div class="container">\n'
        '      <div class="section-head">\n'
        '        <div class="eyebrow">%s</div>\n'
        "        <h2>%s</h2>\n"
        "      </div>\n"
        '      <div class="faq-list">\n'
        "%s\n"
        "      </div>\n"
        "    </div>\n"
        "  </section>\n"
        "%s" % (M_V_OPEN, pair("FAQ", "常见问题", lang), pair(h2[0], h2[1], lang),
                "\n".join(items), M_V_CLOSE)
    )


def render_ld(lang, canonical, h2, qa):
    obj = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "@id": canonical + "#faq-cat",
        "url": canonical,
        "name": h2,
        "inLanguage": lang,
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa],
    }
    return (M_L_OPEN + "\n"
            + '<script type="application/ld+json">\n%s\n</script>\n' % json.dumps(
                obj, ensure_ascii=False, indent=2)
            + M_L_CLOSE)


# ------------------------------------------------------------------ 剥 / 插（严格互逆）
def strip_vis(s):
    return re.sub(re.escape(M_V_OPEN) + r".*?" + re.escape(M_V_CLOSE) + r"\n\n",
                  "", s, flags=re.S)


def insert_vis(s, block):
    i = s.index(V_ANCHOR)
    j = s.rfind("\n", 0, i) + 1
    return s[:j] + block + "\n\n" + s[j:]


def strip_ld(s):
    return re.sub(re.escape(M_L_OPEN) + r".*?" + re.escape(M_L_CLOSE) + r"\n",
                  "", s, flags=re.S)


def insert_ld(s, block):
    i = s.index(L_ANCHOR)
    j = s.rfind("\n", 0, i) + 1
    return s[:j] + block + "\n" + s[j:]


# ------------------------------------------------------------------ 主流程
def canonical_of(s):
    m = re.search(r'<link rel="canonical" href="([^"]+)"', s)
    assert m, "无 canonical"
    return m.group(1)


def inject(path, lang, tr, apply_, stats):
    s = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT).as_posix()
    page = path.name
    spec = PAGES[page]
    canonical = canonical_of(s)

    if lang == "en":
        # EN 页：每个问答自带 (EN, ZH) 配对，可见区双语、结构化数据取英文
        h2 = tuple(clean(x) for x in spec["h2"])
        qa4 = [(clean(x[0]), clean(x[1]), clean(x[2]), clean(x[3])) for x in spec["qa"]]
    else:
        def T(en):
            v = tr[lang].get(en)
            assert v, "%s 缺译文：%s" % (lang, en[:60])
            return clean(v)
        h2 = (T(spec["h2"][0]),) * 2   # 第二项被 pair() 忽略（语言页不出现中文）
        qa4 = [(T(x[0]), T(x[0]), T(x[2]), T(x[2])) for x in spec["qa"]]
    ld_qa = [(p[0], p[2]) for p in qa4]

    sec = render_section(lang, h2, qa4)
    ld = render_ld(lang, canonical, h2[0], ld_qa)

    t = strip_vis(strip_ld(s))
    # 剥除断言：剥完必须不含任何本脚本标记
    assert M_V_OPEN not in t and M_L_OPEN not in t, rel
    t2 = insert_vis(t, sec)
    assert t2.replace(sec + "\n\n", "", 1) == t, "%s 可见块回退断言失败" % rel
    t3 = insert_ld(t2, ld)
    assert t3.replace(ld + "\n", "", 1) == t2, "%s JSON-LD 回退断言失败" % rel

    assert t3.count(M_V_OPEN) == 1 and t3.count(M_L_OPEN) == 1, rel
    # ⚠️ 只能数**本块内**的问答 —— tpe 页的 EVA 段本来就带 2 条 faq-item
    assert sec.count('class="faq-item"') == len(spec["qa"]), (rel, sec.count('class="faq-item"'))
    assert sec in t3, rel
    assert "XX" not in re.sub(r"<[^>]+>", "", sec), rel
    assert 'href="href=' not in t3 and "为 。" not in sec, rel
    for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', t3, re.S):
        json.loads(b)
    nodes = [json.loads(b) for b in
             re.findall(r'<script type="application/ld\+json">(.*?)</script>', t3, re.S)]
    mine = [n for n in nodes if n.get("@type") == "FAQPage" and n.get("@id", "").endswith("#faq-cat")]
    assert len(mine) == 1 and len(mine[0]["mainEntity"]) == len(spec["qa"]), rel
    assert mine[0]["inLanguage"] == lang, (rel, mine[0]["inLanguage"])

    changed = t3 != s
    if changed and apply_:
        path.write_text(t3, encoding="utf-8")
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
        bad = []
        n = 0
        for lg in [""] + [x + "/" for x in LANGS]:
            for page in PAGES:
                p = ROOT / (lg + page)
                n += 1
                s = p.read_text(encoding="utf-8")
                if M_V_OPEN not in s or M_L_OPEN not in s:
                    bad.append((str(p.relative_to(ROOT)), "缺块"))
                    continue
                if s.count('class="faq-item"') < len(PAGES[page]["qa"]):
                    bad.append((str(p.relative_to(ROOT)), "问答数不足"))
                # ⚠️ 不能查 `"#faq-cat"`（带引号）—— @id 是拼在 canonical 后面的，
                #    json.dumps 出来的形态是 `"…tpe-yoga-mats.html#faq-cat"`
                if "#faq-cat" not in s:
                    bad.append((str(p.relative_to(ROOT)), "缺 #faq-cat"))
        print("检查 %d 页 | 异常 %d" % (n, len(bad)))
        for b in bad:
            print("  ", b)
        sys.exit(1 if bad else 0)

    print("=== 准备译文 ===")
    tr = build_data(force=args.retranslate)

    stats = {"pages": 0, "changed": 0, "same": 0}
    for lg in ["en"] + LANGS:
        for page in PAGES:
            p = ROOT / ((lg + "/" if lg != "en" else "") + page)
            inject(p, lg, tr, args.apply, stats)
        print("  %-3s 2 页 %s" % (lg, "已更新" if args.apply else "待更新"))
    print("\n合计 %d 页 | 需改动 %d | 无需改动 %d %s"
          % (stats["pages"], stats["changed"], stats["same"],
             "（已落盘）" if args.apply else "（空跑）"))


if __name__ == "__main__":
    main()
