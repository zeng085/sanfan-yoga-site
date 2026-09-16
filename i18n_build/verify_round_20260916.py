#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本轮改动的统一验收（2026-09-16）：一次全站扫描出全部指标，避免反复等。

指标：
  ① 描述尾部断句（悬空）页数 —— 应为 0
  ② 术语粘连残留 —— 应为 0
  ③ Figure 8 误译残留 —— 应为 0
  ④ 非中日韩页面的汉字残留（剔除语言切换器 / WeChat 微信 / 中文预填）—— 应为 0
  ⑤ title / description 展示宽超限统计
  ⑥ 结构化数据里的双语串残留 —— 应为 0
"""
import glob
import html
import json
import os
import re
from collections import Counter

ROOT = "/Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16"
DIRS = ["", "products", "applications", "blog", "pilates"]
LANGS = ["", "de", "ja", "ko", "fr", "it", "es"]
OK_END = ".!?。！？：；:;…»\"')）"
CJK = re.compile(r"[\u4e00-\u9fff]")
FIG8 = re.compile(r"Abbildung 8|Figure 8\s*:|Figura 8:|図8\s*レジスタンス|그림 8\s*저항")
TERMS = "TPE|PVC|NBR|EVA|ROHS|REACH|MOQ|OEM|ODM|PU|PE|CA|ISO|SGS|PAHs"
# 撇号规则专用：排除元音开头的 EVA/OEM/ODM/ISO（`all'ODM` 本来就是对的意大利语）
TERMS_CONS = "TPE|PVC|NBR|ROHS|REACH|MOQ|PU|PE|CA|SGS|PAHs"
GLUE_PATS = [
    ("焊词", re.compile(r"\b[a-zà-ÿ]{3,}(?:%s)(?:[a-zà-ÿ]{1,4})?\b" % TERMS)),
    ("术语粘连", re.compile(r"\b(?:%s)(?:%s)\b" % (TERMS, TERMS))),
    ("术语粘词", re.compile(r"\b(?:%s)[A-Z][a-z]{2,}" % TERMS)),
    ("撇号语法", re.compile(r"\b(?:[ld]|all|nell|dell|sull)['’](?:%s)\b" % TERMS_CONS)),
    ("术语+小写", re.compile(r"\b(?:%s)[a-zà-ÿ]{1,9}\b" % TERMS)),
    # 2026-09-17 新增家族：词干是**大写开头的专有名词**或**谚文**（无大小写），
    # 原「焊词」规则要求小写词干 ≥3 字母，整族漏网（LineTPE / CorkTPE / 아치형PU）。
    # ⚠️ 右侧用 (?![A-Za-z]) 而不是 \b —— CJK 相邻时 \b 恒不成立。
    # ⚠️ 左侧 (?<![<!]) 是**必须的**：TERMS 里有 `PE`/`CA` 两个两字母短术语，
    #    而几乎每个 HTML 文件第一行都是 `<!DOCTYPE html>` —— `DOCT`+`PE` 恰好
    #    命中本规则，实测会把 1331 页全报成「专名+术语残留」。正文里不会有
    #    以 `<` 或 `<!` 起头的专名，加这个 lookbehind 只杀标签名，不伤正文覆盖。
    #    ⚠️ 写 `(?<!<)` 是**不够的** —— `<!DOCTYPE` 里 `D` 的前一个字符是 `!`
    #       不是 `<`，匹配照样成立（注意匹配起点是 `D` 不是 `T`，因为
    #       `OCTY`+`PE` 也能凑出形状，所以不能靠 `\b` 把它挡在词中间）。
    ("专名+术语", re.compile(r"(?<![<!])\b[A-ZÀ-Ý][A-Za-zÀ-ÿ]{2,}(?:%s)(?![A-Za-z])" % TERMS)),
    ("谚文+术语", re.compile(r"[가-힣](?:%s)(?![가-힣])" % TERMS)),
    ("术语+韩名词", re.compile(
        r"(?:%s)(?:폼롤러|매트|베이스|성분|코팅|무첨가|상단|소재|제품|시트|층|표면|커버|롤러|요가|패드|세트|프리|고무)" % TERMS)),
]
# 白名单与 scan_glued_terms 保持一致：TPEs/EVAs 是合法复数，宁可漏报不假报
TERMWORD_OK = {
    "TPEs", "EVAs", "PUAs", "PUs", "NBRs", "MOQs",
    "Pulver", "Puma", "Puerto", "Peak", "Peel", "Pegasus",
    "Isolation", "Isolierung", "SGSs",
}
# 本来就该含中文的字符串（设计如此），验收时排除，否则数字没意义
BY_DESIGN = ["中文", "日本語", "微信", "陰"]


def W(s):
    return sum(2 if ord(c) > 0x2E80 else 1 for c in s)


def pages():
    for lg in LANGS:
        for sub in DIRS:
            base = os.path.join(ROOT, lg, sub) if sub else (os.path.join(ROOT, lg) if lg else ROOT)
            for f in sorted(glob.glob(os.path.join(base, "*.html"))):
                yield lg, f


def strip_by_design(s):
    """剔除「本来就该是中文」的部分：语言切换器标签、WeChat 微信、中文模式预填文案。

    ⚠️ 不剔干净，这个指标就永远是「950 页命中」——数字失去意义，
       真出问题也看不出来。剔除后剩 0 才说明清理到位。
    """
    s = re.sub(r'<a[^>]*data-setlang="zh"[^>]*>[\s\S]{0,20}?</a>', "", s)
    s = re.sub(r'data-setlang="zh"[^>]*title="[^"]*"', "", s)
    s = re.sub(r'<a[^>]*hreflang="ja"[^>]*>JA</a>', "", s)
    # ⚠️ 中文模式专用的 WhatsApp 预填串：整条 JS 字符串里既有 URL 编码的中文
    #    （`%E4%B8%89%E6%A2%B5`=三梵），又有**未编码**的产品中文名（`健腹轮训练套装`）。
    #    它的开头不是固定的「你好」—— 实测 630 个产品页开头是「三梵」，
    #    只锚 `%E4%BD%A0%E5%A5%BD` 会整批漏掉。改判据：引号里有**连续两个**
    #    百分号编码字节，就整条丢掉（正常 URL 不会这么密）。
    s = re.sub(r'"[^"]*(?:%[0-9A-Fa-f]{2}){2}[^"]*"', '""', s)
    for lit in BY_DESIGN:
        s = s.replace(lit, "")
    return s


def main():
    c = Counter()
    dangling = []
    glue = []
    fig = []
    cjk = []
    dual = []
    twin = []
    dw = []
    for lg, f in pages():
        s = open(f, encoding="utf-8", errors="ignore").read()
        rel = os.path.relpath(f, ROOT)
        c["pages"] += 1

        m = re.search(r'<meta name="description" content="([^"]*)"', s)
        if m and m.group(1) and m.group(1)[-1] not in OK_END:
            dangling.append((rel, m.group(1)[-60:]))

        for label, grx in GLUE_PATS:
            for mm in grx.finditer(s):
                tok = mm.group(0)
                if label == "术语+小写" and tok in TERMWORD_OK:
                    continue
                # `무PVC`：韩语「无/免」前缀，与同句的 `무취`(无味) 并列，属**构词成分**，
                # 不是机翻粘连。把它算进来会让这个指标永远清不到 0。
                if label == "谚文+术语" and tok.startswith("무"):
                    continue
                glue.append((rel, label, tok))

        if FIG8.search(s):
            fig.append(rel)

        if lg and lg != "ja" and CJK.search(strip_by_design(s)):
            cjk.append(rel)

        for mm in re.finditer(r'"name":\s*"([^"]*)"', s):
            v = mm.group(1)
            if CJK.search(v) and lg not in ("", "ja", "ko"):
                dual.append((rel, v[:70]))

        for mm in re.finditer(r'<title>([^<]*)</title>', s):
            # ⚠️ 必须先 html.unescape 再量宽：`&amp;`(5 字符) 实际只占 1 格，
            #    `&#124;`(6 字符) 实际是 1 个 `|`。不还原就会把 `A &amp; B` 这种
            #    标题虚报超宽——实测 9 条「超 60」标题还原后**全部合规**。
            t = html.unescape(mm.group(1))
            w = W(t)
            c["title>60" if w > 60 else "title_ok"] += 1
            if w > 60:
                twin.append((w, rel, t))
        for mm in re.finditer(r'<meta name="description" content="([^"]*)"', s):
            w = W(html.unescape(mm.group(1)))
            c["desc>155" if w > 155 else "desc_ok"] += 1
            # ⚠️ 分层，别只报一个 806 —— 那个数字不构成缺陷清单：
            #    上一轮的「断头 description」正是**字数硬截断**造成的（364 页半句话），
            #    随后靠「完整句子优先」还原回来。160~220 是 Google 正常省略号截断的
            #    区间，属可接受；>220 才是「一半内容白写」，值得人工重写。
            if w > 220:
                c["desc>220"] += 1
                if lg in ("", "de", "fr", "it", "es"):
                    c["desc>220_欧语"] += 1
                dw.append((w, rel))

    print("页面总数 %d" % c["pages"])
    print("① 描述尾部悬空：%d 页  %s" % (len(dangling), dangling[:4]))
    print("② 术语粘连残留：%d 处  %s" % (len(glue), glue[:4]))
    print("③ Figure 8 误译残留：%d 页  %s" % (len(fig), fig[:4]))
    print("④ 非中日韩页面汉字残留：%d 页  %s" % (len(cjk), cjk[:4]))
    print("⑥ 结构化数据双语串残留：%d 处  %s" % (len(dual), dual[:3]))
    print("⑤ title 超 60 宽：%d" % c["title>60"])
    print("   desc 分层：合规(<=155) %d | 略长(156-220) %d | 严重超长(>220) %d （欧语 %d）"
          % (c["desc_ok"], c["desc>155"] - c["desc>220"], c["desc>220"], c["desc>220_欧语"]))
    if c["desc>220"]:
        print("   desc 最宽 5 条：%s" % ", ".join(
            "%d:%s" % (w, r) for w, r in sorted(dw, reverse=True)[:5]))
    print("   title 最宽 10 条：")
    for w, rel, t in sorted(twin, reverse=True)[:10]:
        print("     %3d  %-44s %s" % (w, rel, t))


if __name__ == "__main__":
    main()
