#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""机翻「术语粘连 / 错误省音」修复规则表 —— **单一来源**（2026-09-16）

【为什么单独成模块】
一次性脚本修好了站点，但**翻译管线重生成页面时会原样再犯**。
规则表只放在 dated 脚本里，等于把「已知的坑」留给了下一次重建。
所以把规则与 repair() 抽到这里，两处共用：
  · i18n_build/fix_glue_20260916.py —— 批量修复**已有** HTML 文件
  · i18n_build/translator.py        —— `repair()` 挂在译文出口，**防止复发**

【病根】翻译引擎把受保护术语包成 `<xN>TPE</xN>` 并交给 DeepL 的 `ignore_tags`，
引擎**看不到术语的首字母**，于是自己猜：猜错省音（fr `d'TPE`）、猜错词形
（it `in gommPUe`）、漏空格（es `«X»TPE`、`cmTPE`）、吞逗号（`REACHCA`），
甚至整词幻觉（es `bifeniloPVC`，EN 原文只是 `contains no PVC`）。

【三条铁律】
  1. 省音规则必须排除 EVA —— EVA 是元音开头，`d'EVAs` 本来就是对的。
  2. 撇号必须同时认字面与 HTML 实体 —— og:title 里的撇号写作 `&#x27;`。
  3. 规则必须幂等 —— 语序类规则要把 `d'`、`de`、重复术语一起吃掉。

用法：
    from term_repair import repair
    out = repair(text, "fr")
"""

import re


TERM = r"(?:TPE|PVC|PU|NBR|EVA|ROHS|REACH|MOQ)"
# ⚠️ 省音规则专用：**必须排除 EVA**。
#    法/意语的省音只发生在元音开头的词前，而 EVA 正是元音开头 ——
#    `d'EVAs haute densité`（fr）、`dell'EVA`（it）本来就是正确写法，
#    把 EVA 放进省音规则会「修好为错」。实测：fr 站点 6 处 `Blocs d'EVAs` 会被误改成 `du EVAs`。
#    其余术语（TPE/PVC/PU/NBR/ROHS/REACH/MOQ）都以辅音开头，缩合才是对的。
TERM_CONS = r"(?:TPE|PVC|PU|NBR|ROHS|REACH|MOQ)"
# ⚠️⚠️ 撇号必须同时认「字面」与「HTML 实体」两种写法 —— 这是本脚本第一版最大的漏网。
#    `og:title` / `twitter:title` 的撇号写在 HTML 属性值里，管线会转义成 `&#x27;`：
#        <meta property="og:title" content="Tapis de yoga ... « Cork Surface » d&#x27;PU — SANFAN" />
#    只认字面 `'` 时，**同一页的 h1（字面撇号）被改好、og:title 却整批漏掉**，
#    表现为「修完扫描器仍报 8 页残留」。与项目笔记里 `&#124;` 分隔符是同一类坑。
APOS = r"(?:['’]|&#x27;|&#39;|&rsquo;|&#8217;)"
# 捕获组版：用 m.group(1) 取术语。
# ⚠️ 不能沿用 m.group(0)[2:] 这种按位置切片 —— 实体写法 `&#x27;` 是 6 个字符，
#    按长度切会切出乱码（`d&#x27;TPE`[2:] 得到 `#x27;TPE`）。
TERM_CONS_C = r"(TPE|PVC|PU|NBR|ROHS|REACH|MOQ)"
# 需要取回术语本身时用这个（带捕获组的版本）
TERM_C = r"(TPE|PVC|PU|NBR|EVA)"
# 引号内容「本身就是术语」时不能用产品名语序规则 —— 那是术语引用，不是图案名。
# 实测反例：fr/suede-cork-yoga-mats.html 的 JSON-LD 原文已是
#   `Tapis de yoga en daim botanique bleu marine «TPE » TPE`
# 若不加守卫，会换位成 `… bleu marine TPE « TPE »`（术语重复且更乱）。
ONLY_TERM = re.compile(r"^(?:%s)$" % TERM[3:-1])
# ⚠️ 引号里是**连词/虚词**时同样不能当图案名换位（2026-09-17 踩到）：
#    fr  `Tapis de yoga en caoutchouc « vs » PU`  ← DeepL 把 EN 的 `vs` 当成名词加了书名号
#    不加守卫时语序规则会把它改成 `…caoutchouc PU « vs »` —— **把正确语序改坏**。
#    实测：这条假阳性出现在 fr/blog.html 与 fr/blog/tpe-vs-pu.html（og/tw/JSON-LD headline）。
STOP_WORD = re.compile(
    r"^(?:vs\.?|and|or|et|ou|und|oder|y|e|avec|with|de|of|en|in|le|la|les|des|du|the)$",
    re.IGNORECASE)


def _not_a_name(txt):
    t = txt.strip()
    return bool(ONLY_TERM.match(t)) or bool(STOP_WORD.match(t))


def reorder_fr(m):
    if _not_a_name(m.group(2)):
        return m.group(0)
    return "%s %s « %s »" % (m.group(1).strip(), m.group(3), m.group(2).strip())


def reorder_es(m):
    if _not_a_name(m.group(2)):
        return m.group(0)
    return "%s %s «%s»" % (m.group(1).strip(), m.group(3), m.group(2).strip())

# ---------------------------------------------------------------- 规则表
# 结构：(语言, 正则, 替换, 说明)。语言 "" = 全语言通用。
# ⚠️ 顺序即优先级 —— 短语级规则必须排在通用规则之前。
RULES = [
    # ============ 产品名语序（必须在通用「补空格」之前）============
    # 机翻把材料术语甩到书名号**后面**：`Tapis de yoga en caoutchouc « Gradient Line Art »PU`
    # 法语/西语的自然语序是「材料 + 品类 + 图案名」，术语应前置。
    # 只匹配 `产品前缀 ... « 图案名 » + 术语` 这一种紧贴形态，
    # 且图案名限长 45 字、前缀限长 30 字 —— 避免吞掉正常句子里的引号内容。
    # ⚠️ 尾部要把两种「残留」一起吃掉，否则不幂等（第一轮改完，第二轮还会再匹配一次）：
    #   · `(?:d['’])?` —— `«Marble Print» d'PU` 的缩合 de
    #   · `(?:\s+TERM)?` —— 原文本身就有重复术语的情况：
    #       fr/pu-rubber-yoga-mats.html 的 JSON-LD 原为
    #       `Tapis de yoga en caoutchouc « Marble Print » PU PU`
    #     只吃一个 PU 会留下 `… PU « Marble Print » PU`，第二轮被再匹配一次。
    ("fr", r"(Tapis de yoga[^«»]{0,30}?)\s*«\s*([^«»]{1,45}?)\s*»\s*(?:d" + APOS + r")?"
     + TERM_C + r"(?:\s+" + TERM_C + r")?",
     reorder_fr, "Fr 产品名语序：«图案»PU → PU «图案»"),
    # ⚠️ es 这里必须把 `de` 也吃掉：原文形态是 `«Gray Mandala» dePU`（de 与 PU 粘连）。
    #    若不吸收 de，第一轮正则停在 `» de` 上匹配失败，而排在后面的 `dePU→PU`
    #    规则又把它变成 `» PU`，于是第二轮才匹配 —— 非幂等（实测 4 处）。
    ("es", r"(Esterilla de yoga[^«»]{0,30}?)\s*«\s*([^«»]{1,45}?)\s*»\s*(?:de\s*)?"
     + TERM_C + r"(?:\s+" + TERM_C + r")?",
     reorder_es, "Es 产品名语序：«图案»TPE → TPE «图案»"),

    # 同一页的 JSON-LD 与产品卡写法不一致（全站仅此 1 处）：
    #   JSON-LD: "Tapis de yoga en daim botanique bleu marine «TPE » TPE"  ← 语序错 + 术语重复
    #   产品卡  : "Tapis de yoga «TPE» en daim botanique bleu marine"      ← 正确
    # 统一到产品卡的写法，保证结构化数据与页面上看到的一致。
    ("fr", r"Tapis de yoga en daim botanique bleu marine «TPE » TPE",
     "Tapis de yoga «TPE» en daim botanique bleu marine", "Fr JSON-LD 与产品卡产品名统一"),

    # ============ 通用：缺空格 ============
    ("", r"\b(cm|mm|CM|MM)(?=" + TERM + r"\b)", r"\1 ", "单位与术语之间补空格（80/90 cmTPE）"),
    ("", r"»(?=" + TERM + r"\b)", "» ", "右书名号后补空格（«Alignment Line»TPE）"),
    ("", r"\bEcoTPE(?:[oe])?\b", "Eco TPE", "Eco TPE 粘连"),
    ("", r"\becoTPE(?:[oe])?\b", "eco TPE", "eco TPE 粘连"),
    ("", r"\bWideTPE\b", "Wide TPE", "Wide TPE 粘连"),
    ("", r"\bLine ArtPU\b", "Line Art PU", "产品名后置术语粘连"),
    ("", r"\bMandalaPU\b", "Mandala PU", "产品名后置术语粘连"),
    ("", r"\bRedPU\b", "Red PU", "产品名后置术语粘连"),

    # ============ 意大利语 ============
    # ① 错误省音：术语以辅音开头，意大利语不缩合 → 用 il / del / al / nel / dal
    #    ⚠️ 不含 OEM/ODM —— 那两个字以元音开头，`L'OEM`/`all'ODM` 本来就对。
    ("it", r"\bL" + APOS + TERM_CONS_C, lambda m: "Il " + m.group(1), "It 句首省音还原"),
    ("it", r"\bdell" + APOS + TERM_CONS_C, lambda m: "del " + m.group(1), "It dell'→del（辅音不缩合）"),
    ("it", r"\ball" + APOS + TERM_CONS_C, lambda m: "al " + m.group(1), "It all'→al"),
    ("it", r"\bnell" + APOS + TERM_CONS_C, lambda m: "nel " + m.group(1), "It nell'→nel"),
    ("it", r"\bdall" + APOS + TERM_CONS_C, lambda m: "dal " + m.group(1), "It dall'→dal"),
    # ⚠️ `sull'` 原先漏了（09-16 实测 `soggetto a … sull’REACHe`）：辅音开头术语不缩合，
    #    正确形态是 `sul REACH`。省音家族必须**穷举介词**，漏一个就漏一类。
    ("it", r"\bsull" + APOS + TERM_CONS_C, lambda m: "sul " + m.group(1), "It sull'→sul"),
    ("it", r"\bl" + APOS + TERM_CONS_C, lambda m: "il " + m.group(1), "It l'→il"),
    # ② 词形粘连：gomma / schiuma / yoga 被术语吃掉词尾
    ("it", r"\bgommTPEa\b", "gomma TPE", "gomma TPE 粘连"),
    ("it", r"\bgommPVCa\b", "gomma PVC", "gomma PVC 粘连"),
    ("it", r"\bgommTPE\b", "gomma TPE", "gomma TPE 粘连"),
    ("it", r"\bgommPUe\b", "gomma PU", "gomma PU 粘连"),
    ("it", r"\bgommPU\b", "gomma PU", "gomma PU 粘连"),
    ("it", r"\bschiumaEVA\b", "schiuma EVA", "schiuma EVA 粘连"),
    ("it", r"\bschiumEVA\b", "schiuma EVA", "schiuma EVA 粘连"),
    ("it", r"\byogaEVA\b", "yoga EVA", "yoga EVA 粘连"),
    ("it", r"\byogTPEi\b", "yoga TPE", "yoga TPE 粘连"),
    ("it", r"\ballPVC\b", "al PVC", "al PVC 粘连"),
    ("it", r"\ballREACHe\b", "al REACH", "al REACH 粘连"),
    ("it", r"\bnormeROHS\b", "norme ROHS", "norme ROHS 粘连"),
    ("it", r"\bEco-TPEe\b", "Eco TPE", "特性条 Eco TPE 粘连"),

    # ============ 法语 ============
    # ① 缩合短语先行：`de l'X` → `du X`（不是 `le X`）
    ("fr", r"\bde l" + APOS + TERM_CONS_C, lambda m: "du " + m.group(1), "Fr de l'→du"),
    ("fr", r"\bau l" + APOS + TERM_CONS_C, lambda m: "au " + m.group(1), "Fr au l'→au"),
    # ② 产品名后置的 `» d'PU` → `» en PU`（EN 是 PU Rubber Yoga Mat，用 en 更自然）
    ("fr", r"»\s*d" + APOS + TERM_CONS_C, lambda m: "» en " + m.group(1),
     "Fr 产品名后置 d'X→en X"),
    # ③ `d'X` 兜底 → `du X`（忠于 de 的本义，语法必然正确）
    ("fr", r"\bd" + APOS + TERM_CONS_C, lambda m: "du " + m.group(1), "Fr 其余 d'X→du X"),
    # ④ 错误省音
    ("fr", r"\bL" + APOS + TERM_CONS_C, lambda m: "Le " + m.group(1), "Fr 句首 L'X→Le X"),
    ("fr", r"\bl" + APOS + TERM_CONS_C, lambda m: "le " + m.group(1), "Fr l'X→le X"),
    # ⑤ 粘连
    ("fr", r"\bsansPVC\b", "sans PVC", "sans PVC 粘连"),
    ("fr", r"\bpour laTPE\b", "TPE", "pour laTPE 粘连（EN: 3x anti-slip TPE mat）"),
    ("fr", r"\bdePU\b", "en PU", "Fr dePU 粘连"),
    ("fr", r"évaluation de l" + APOS + r"CA Prop 65",
     "évaluation de la Prop 65 californienne", "Fr l'CA Prop 65 → 正确法语表述"),

    # ============ 西班牙语 ============
    ("es", r"\balfombrillasTPE\b", "alfombrillas TPE", "alfombrillas TPE 粘连"),
    ("es", r"\balfombrillaTPE\b", "alfombrilla TPE", "alfombrilla TPE 粘连"),
    # ⚠️ 尾部 `(?:es|as|s)?` 不能省：实测原文是 `alfombrTPEes`
    #    （ill+as 被术语吃掉，只剩 `es`），只写 `\balfombrTPE\b` 匹配不到。
    ("es", r"\balfombrTPE(?:es|as|s)?\b", "alfombrillas TPE", "alfombrillas TPE 粘连"),
    ("es", r"\balfombrPU\b", "alfombra PU", "alfombra PU 粘连"),
    ("es", r"\byogTPE\b", "yoga TPE", "yoga TPE 粘连"),
    # ⚠️ 语义修复：EN 是 “contains no PVC”，机翻凭空造出 bifenilo（联苯）
    ("es", r"\bNo contiene bifeniloPVC\b", "No contiene PVC", "Es 幻觉词 bifenilo 清除"),
    ("es", r"\bdePU\b", "PU", "Es 产品名后置 dePU 粘连"),

    # ============ 德语 ============
    # ⚠️ 语义反了：EN 原文 “Eco TPE, no PVC, no odor”，德语译成 “und PVC”（和 PVC）
    ("de", r"\bUmweltfreundlichTPE und PVC und geruchsneutral\b",
     "Umweltfreundliches TPE, kein PVC, geruchsneutral", "De 「无 PVC」被译成「和 PVC」，语义纠正"),

    # ============ 术语粘连导致的逗号丢失（三语言）============
    ("es", r"\bREACHCA Prop 65\b", "REACH, CA Prop 65", "Es 逗号被吞"),
    ("ko", r"\bREACHCA Prop 65\b", "REACH, CA Prop 65", "Ko 逗号被吞"),
    ("fr", r"\bREACHCA Prop 65et 6P\b", "REACH, CA Prop 65 et 6P", "Fr 逗号+空格被吞"),
    ("fr", r"\bProp 65et 6P\b", "Prop 65 et 6P", "Fr 空格被吞"),

    # ---- ③ 术语尾黏小写词（2026-09-16 第二批） ------------------------------
    # 与①「焊词」方向相反：这次是术语**后面**直接粘上小写词，中间丢了空格。
    # 三种成因、三种修法，必须分语言：
    #   · 连词/冠词被吞掉空格  es PVCe/PVCy/PVC o、fr PVCet、de PVCund、es PVClibre
    #     → 补空格即可（e/y/o/et/und/libre 本身是词）
    #   · 引擎凭空多吐一个 e   de Öko-TPEe、fr le TPEe、it del PVCe ed
    #     → 删掉这个 e（注意 it 的 "PVCe ed" 里 ed 才是连词）
    #   · 判据：粘连尾巴本身是不是目标语言的词 —— 是就补空格，不是就删掉
    ("es", r"\bPVClibre\b", "PVC libre", "Es 补空格（libre）"),
    ("es", r"\bPVC([ey])\b(?=\s+\S)", r"PVC \1", "Es 连词被吞空格"),
    ("es", r"\bPVC[a-z]\b", "PVC", "Es 术语尾多余字母"),
    ("es", r"\bePVCo\b", "PVC", "Es 前后各黏一个字母"),
    ("es", r"\b(TPE|PU|EVA|NBR)[oa]\b", r"\1", "Es 术语尾多余元音"),
    ("es", r"\bEco(TPE|PU|PVC|EVA|NBR)[oa]?\b", r"Eco \1", "Es Eco 与术语粘连"),
    ("es", r"\bTPE([eyou])\b(?=\s)", r"TPE \1", "Es 连词被吞空格"),
    # ⚠️ `[oa]` 覆盖不到 `e`：`Material: PUe mate + caucho natural`（应为 `PU mate + caucho`）。
    #    TPE 除外 —— TPEe 有可能是西语连词 e（`TPE e inodoro`），由上面那条管。
    ("es", r"\b(PU|NBR|EVA)e\b", r"\1", "Es 术语尾多余 e"),
    # ⚠️ 语序类一次性修复：EN `PU-rubber hybrids suit …`，
    #    机翻把 PU 甩到句首并和 `Los` 焊在一起 → `PULos híbridos de caucho son …`。
    #    西语正确语序是 `Los híbridos de caucho PU son …`。按整短语替换（幂等）。
    ("es", r"\bPULos híbridos de caucho\b", "Los híbridos de caucho PU",
     "Es 语序：PU 被甩到句首并与 Los 粘连"),
    ("fr", r"\bPVCet\b", "PVC et", "Fr 连词被吞空格"),
    ("fr", r"\bPVCe\b", "PVC", "Fr 多余 e"),
    ("fr", r"\bTPEe\b", "TPE", "Fr 多余 e"),
    ("fr", r"\bPUe\b", "PU", "Fr 多余 e"),
    ("fr", r"\b(PVC|TPE)s\b", r"\1", "Fr 多余复数 s"),
    ("de", r"\bPVC(und|oder)\b", r"PVC \1", "De 连词被吞空格"),
    ("de", r"\bPUetwa\b", "PU etwa", "De 粘连 etwa"),
    ("de", r"\bMattPUn\b", "Matt PU", "De 形容词+术语粘连"),
    ("de", r"\bTPEe\b", "TPE", "De 多余 e"),
    ("it", r"\bPVCe\b(?=\s+inodor[oae])", "PVC e", "It 连词被吞空格"),
    ("it", r"\bPVC[ei]\b", "PVC", "It 多余 e/i"),
    ("it", r"\bTPEe\b", "TPE", "It 多余 e"),
    ("it", r"\bEVAe\b", "EVA", "It 多余 e"),
    ("it", r"\bPU[eo]\b", "PU", "It 多余 e/o"),
    # ---- ③e 术语被吞掉空格后黏上**真词**（不是多余字母）--------------------------
    #   判据同 ③：尾巴是目标语言的词 → 补空格；不是词 → 删掉。
    #   it 实测：`in gomma PUcome opzione premium`（应为 PU come）、
    #            `in gomma PUdi dimensioni simili`（应为 PU di）、
    #            `regolamento UE sull’REACHe`（应为 sul REACH —— 见上面的 sull' 规则）
    ("it", r"\bPUcome\b", "PU come", "It PUcome 粘连（应为 PU come）"),
    ("it", r"\bPUdi\b", "PU di", "It PUdi 粘连（应为 PU di）"),
    ("it", r"\bREACHe\b", "REACH", "It 术语尾多余 e（REACHe）"),
    ("de", r"\bPVCs(?=:)", "PVC", "De 术语尾多余 s（PVCs: → PVC:）"),
    # 短冠词/介词（2 字母）与术语粘连 —— GLUE_LOWER 要求词干 ≥3 字母，
    # 所以 `unEVA` 这类漏网；这里补一条窄规则（只在**没有空格**时才命中）
    ("es", r"\b(un|una|unos|unas|el|la|los|las|del|de)((?:TPE|PVC|PU|NBR|EVA))(?:[oae])?\b",
           r"\1 \2", "Es 短冠词粘连"),
    ("it", r"\b(un|una|il|lo|la|le|del|della|di)((?:TPE|PVC|PU|NBR|EVA))(?:[oae])?\b",
           r"\1 \2", "It 短冠词粘连"),
    ("fr", r"\b(un|une|le|la|les|du|des|de)((?:TPE|PVC|PU|NBR|EVA))(?:[oae])?\b",
           r"\1 \2", "Fr 短冠词粘连"),
    ("de", r"\b(ein|eine|der|die|das|von|aus|mit)((?:TPE|PVC|PU|NBR|EVA))(?:[oae])?\b",
           r"\1 \2", "De 短冠词粘连"),
    # ---- ③b 词内被插进空格（与粘连互为镜像）-------------------------------
    #   引擎有时把术语紧邻的词**切开**：it `priv a di PVCe`、es `sin PVCe inodor a`。
    #   与上面「吞掉空格」是同一处病灶的两个方向，一起修掉才成句。
    ("it", r"\bpriv ([ao])\b", r"priv\1", "It 词内被插空格（priv a→priva）"),
    ("es", r"\binodor ([ao])\b", r"inodor\1", "Es 词内被插空格（inodor a→inodora）"),
    # ---- ③c 法语形容词语序：ÉcologiqueTPEe → TPE écologique --------------------
    #   法语形容词后置，`Écologique TPE`（英语语序直译）读起来是名词短语错位。
    ("fr", r"\bÉcologique(TPE|PU|PVC|EVA|NBR)[a-z]?\b", r"\1 écologique",
     "Fr 形容词前置→后置（ÉcologiqueTPEe）"),
    # ---- ③d 「Figure 8」被当成「插图 8」（6 语言全错）-------------------------
    #   这里的 8 是**形状**（8 字形弹力带），不是图号。实测：
    #      de 「Abbildung 8 Widerstandsbänder」、fr「Figure 8 : Bandes de résistance」、
    #      it 「Figura 8: Fasce elastiche」、es「Figura 8: Bandas elásticas」、
    #      ja 「図8 レジスタンスバンド」、ko「그림 8 저항 밴드」
    #   ⚠️ es/it 必须**先长后短**：`…Bandas elásticas de resistencia` 排在 `…Bandas elásticas` 前，
    #      否则短规则先把前缀吃掉，长规则的锚点就没了（同一处会出现两条规则竞争）。
    #   ⚠️ 已在 translator.GLOSSARY 里加了 EN 侧保护，重译不会再犯；这几条是修**存量**页面。
    #   ⚠️ 短规则要把**已经正确**的尾巴一起吃掉（`(?:\s+a forma di 8)?`），
    #      否则第二遍会产出 `…a forma di 8 a forma di 8`（自测抓到过）。
    ("de", r"Abbildung 8:?\s*Widerstandsbänder", "Widerstandsbänder in Achtform",
     "De Figure 8 被误译为插图"),
    ("fr", r"Figure 8\s*:\s*Bandes de résistance", "Bandes de résistance en huit",
     "Fr Figure 8 被误译为插图"),
    ("it", r"Figura 8:\s*Fasce elastiche di resistenza", "Fasce elastiche a forma di 8",
     "It Figure 8 被误译为插图"),
    ("it", r"Figura 8:\s*Fasce elastiche(?:\s+a forma di 8)?", "Fasce elastiche a forma di 8",
     "It Figure 8 被误译为插图"),
    ("es", r"Figura 8:\s*Bandas elásticas(?:\s+de resistencia|\s+en forma de 8)?",
     "Bandas elásticas en forma de 8", "Es Figure 8 被误译为插图"),
    ("es", r"Figura 8:\s*Bandas de resistencia(?:\s+en forma de 8)?",
     "Bandas de resistencia en forma de 8", "Es Figure 8 被误译为插图"),
    ("ja", r"図8\s*レジスタンスバンド", "8の字レジスタンスバンド", "Ja Figure 8 被误译为插图"),
    ("ko", r"그림 8\s*저항 밴드", "8자 저항 밴드", "Ko Figure 8 被误译为插图"),
    # 大写开头词干 + 术语粘连（ÉcologiqueTPEe / Eco-TPEe 变体）
    ("", r"\b([A-Za-zÀ-ÿ]{3,})(TPE|PVC|PU|NBR|EVA|REACH|ROHS|MOQ|OEM|ODM)[a-z]?\b",
         r"\1 \2", "词干+术语粘连（大写开头）"),

    # ---- ③e 「拉丁词干/谚文 + 术语」粘连（2026-09-17 新增家族）------------------
    # 扫描器原先只认「**小写**词干 ≥3 字母」（GLUE_LOWER），于是这一族整批漏网：
    #   词干是**大写开头的专有名词**（Line / Cork / Color）或**韩文**（无大小写）。
    # 实测漏网清单（纯文本扫描 95 处）：
    #   de  Alignment LineTPE-Yogamatte      it  Tappetino Spliced ColorTPE
    #   ja  CorkTPEヨガマット                  ko  아치형PU / 스웨이드TPE / 에코TPE
    #
    # ⚠️ 旧规则 #95 的尾部用了 `\b` —— 在 CJK 相邻处**必然失效**
    #    （`CorkTPEヨ` 的 E 与 ヨ 都是 word char，中间没有词边界），
    #    这就是 `CorkTPEヨガマット` 扫不出来也修不掉的原因。改为 `(?![A-Za-z])`。
    ("", r"\b([A-Za-zÀ-ÿ]{3,})(TPE|PVC|PU|NBR|EVA|REACH|ROHS|MOQ|OEM|ODM)(?![A-Za-z])",
         r"\1 \2", "词干+术语粘连（大写/专有名词开头，CJK 相邻也算）"),

    # ⚠️ 韩语「术语 + 谚文」**绝不能**写通用规则 —— 那一侧绝大多数是**助词**，
    #    必须连写：TPE에서(130) / PU의(18) / NBR는(16) / TPE가(10) / EVA와(9) /
    #    TPE보다(7) / NBR를(7) / MOQ에(4) / TPE을(3) …
    #    通用加空格会把这 200 多处**正确的韩语**改坏（等于把句子切成病句）。
    #    所以右侧只认**名词白名单**（实测真粘连就这十几个）。
    ("ko", r"(TPE|PVC|PU|NBR|EVA|REACH|ROHS|MOQ)(폼롤러|매트|베이스|성분|코팅|무첨가|상단|소재|제품|시트|층|표면|커버|롤러|요가|패드|세트|프리|고무)",
     r"\1 \2", "Ko 术语+名词粘连（助词不动，只拆名词）"),

    # 韩语左侧加空格：**谚文词 + 术语**。左侧永远是前一个词（아치형+PU），无例外。
    # ⚠️ 排除「무」—— 韩语里 `무` 是「无/免」前缀（무PVC=无PVC，与 무취=无味 并列），
    #    属构词成分，拆开会与同句的 `무취` 写法自相矛盾。
    ("ko", r"([가-힣])(TPE|PVC|PU|NBR|EVA|REACH|ROHS|MOQ)(?![가-힣])",
     lambda m: m.group(0) if m.group(1) == "무" else "%s %s" % (m.group(1), m.group(2)),
     "Ko 谚文+术语粘连（무 前缀除外）"),

    # ---- ③f 短冠词/前缀被吞后与术语焊在一起（fr/es，2026-09-17）---------------
    #   fr  `Il ne contient ni éPVC`      ← `neither PVC nor` 的 ni 后多了个 é
    #   es  `al de lPVC` / `el de lTPE`   ← 西语 `el PVC` 的缩合是 `del PVC`，
    #                                        DeepL 把冠词拆成 `de l` 再与术语粘连
    ("fr", r"\bni éPVC\b", "ni PVC", "Fr 吞词：ni éPVC → ni PVC"),
    ("es", r"\bal de l(TPE|PVC|PU|NBR)\b", r"al del \1", "Es 缩合：al de lX → al del X"),
    ("es", r"\bel de l(TPE|PVC|PU|NBR)\b", r"el del \1", "Es 缩合：el de lX → el del X"),

    # ---- ③g 「TPE vs PU」被拆坏：术语甩到句首 + 把 `vs` 加书名号 ---------------
    #   EN 原文 `TPE vs PU Rubber Yoga Mats: Which to Choose in 2026`
    #   机翻把 `TPE` 单独甩到最前面，再把 `vs` 当名词套上书名号：
    #     fr  `TPE Tapis de yoga en caoutchouc « vs » PU : lequel choisir en 2026`
    #     es  `TPE Alfombrillas de yoga de goma «vs» PU: ¿cuál elegir en 2026?`
    #   ⚠️ 这条必须在「产品名语序」规则**之前**生效，否则后者会把
    #      `« vs » PU` 当成图案名换位成 `PU « vs »`（把正确语序改坏，实测撞到）。
    #      还要配合 STOP_WORD 守卫 —— 双保险。
    ("fr", r"TPE Tapis de yoga en caoutchouc « vs » PU",
     "Tapis de yoga en caoutchouc TPE vs PU", "Fr vs 被加书名号 + 术语甩句首"),
    ("es", r"TPE Alfombrillas de yoga de goma «vs» PU",
     "Alfombrillas de yoga de goma TPE vs PU", "Es vs 被加书名号 + 术语甩句首"),

    # ---- ③h 「术语清单」被压缩：逗号吞空格 + 西语连接词 y 被焊进术语 -----------
    #   EN 原文 `… MOQ 100 pcs, 7-day sampling, SGS/REACH/CA Prop 65 docs on request.`
    #   es 译成 `… SGS,REACHyCA Prop 65.`
    #     · 斜杠被改成逗号（另 5 个语言版本都保留了斜杠）
    #     · 逗号后又把空格吞了
    #     · 西语连接词 `y`（=and）整只焊进 `REACH` 与 `CA` 之间
    #   ⚠️ 逗号规则只锚「术语紧邻术语」的位置，**不能**写成通用的 `,(?=[A-Z])` ——
    #      正文里的缩写、编号、金额都会误伤；这个形状实测全站就 1 处。
    #   ⚠️ **顺序要紧**：`REACHyCA` 里 `y` 是字母，会让逗号规则的 `\b` 失效
    #      （`SGS,REACHyCA` 匹配不到 `SGS,`+`REACH\b`）。所以必须**先拆焊**
    #      再补逗号后的空格，两条顺序颠倒就白干（实测踩过）。
    ("es", r"\bREACHyCA\b", "REACH y CA", "Es 连接词 y 被焊入术语：REACHyCA → REACH y CA"),
    ("", r"\b(TPE|PVC|PU|NBR|EVA|REACH|ROHS|MOQ|OEM|ODM|SGS|ISO|PAHs|CA),(?=(?:TPE|PVC|PU|NBR|EVA|REACH|ROHS|MOQ|OEM|ODM|SGS|ISO|PAHs|CA)\b)",
     r"\1, ", "术语清单逗号后吞空格：X,Y → X, Y"),
]

COMPILED = [(lg, re.compile(rx), rep, why) for lg, rx, rep, why in RULES]

# ⭐ 自检：替换串里出现控制字符 = 忘了写 r"" 前缀，`\1` 被 Python 当成八进制转义
#    吃成 U+0001 了。这种错不会抛异常，只会把 `\1` 静默写进页面（实测踩过一次：
#    `"TPE \1"` → `TPE \x01`），所以在 import 时就炸掉。
for _i, (_lg, _rx, _rep, _why) in enumerate(COMPILED):
    if not callable(_rep) and any(ord(_c) < 32 for _c in _rep):
        raise ValueError(
            "term_repair RULES[%d]「%s」的替换串含控制字符 —— 多半是漏了 r 前缀" % (_i, _why))


# 语言别名：调用方可能传 "EN"/"en"/"" 等
_LANG_OK = {"de", "ja", "ko", "fr", "it", "es"}


def repair(text, lang):
    """对**一段已翻译文本**套用该语言的修复规则。返回修好的文本。

    ⚠️ 只按语言套用对应规则：`l'X` 在法/意语是错的，但意语 `L'OEM` 是对的
       （O 是元音），所以规则必须分语言，不能通吃。
    """
    if not text:
        return text
    lg = (lang or "").lower()
    if lg not in _LANG_OK:
        return text
    for rlg, rx, rep, _why in COMPILED:
        if rlg and rlg != lg:
            continue
        if rx.search(text):
            text = rx.sub(rep, text)
    return text
