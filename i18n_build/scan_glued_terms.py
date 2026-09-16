#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全站扫「机翻把受保护术语焊进单词」的硬伤（2026-09-16）

【为什么单开一个扫描】
已知坑（见项目笔记）：机翻会吃掉受保护术语旁的名词词尾 ——
    alfombrillas → alfombrTPEes
    tappetini    → tappetTPE
    schiuma      → schiumPVCe
    ㎡            → ㎡e
这一次又撞到同族的新形态（出现在 <title> 里，会直接显示在搜索结果）：
    REACH, CA Prop 65  →  REACHCA Prop 65      （REACH + CA 粘连，es/fr/ko 合规博客）
    REACH, CA Prop 65  →  REACHCA Prop 65et 6P （fr 版还漏了空格）

判据：一个「词」里嵌了全大写术语，且两侧有拉丁字母 —— 正常英文/德文/罗曼语
不会这么拼。**扫 title / description / h1 三个会外显的字段。**

用法：python3 scan_glued_terms.py [--all]     # --all 连正文一起扫
"""
import glob
import html
import os
import re
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LANGS = ["", "de", "ja", "ko", "fr", "it", "es"]
DIRS = ["", "products", "applications", "blog", "pilates"]

TERMS = "TPE|PVC|NBR|EVA|ROHS|REACH|MOQ|OEM|ODM|PU|PE|CA|ISO|SGS|PAHs"
# 撇号规则专用：**必须排除 EVA / OEM / ODM / ISO**（元音开头，缩合本来就是对的）
TERM_CONS = "TPE|PVC|NBR|ROHS|REACH|MOQ|PU|PE|CA|SGS|PAHs"

# ① 小写词干 + 大写术语 + 可选小写尾巴   alfombrTPEes / tappetTPE / schiumPVCe
GLUE_LOWER = re.compile(r"\b[a-zà-ÿ]{3,}(?:%s)(?:[a-zà-ÿ]{1,4})?\b" % TERMS)
# ② 大写术语 + 大写术语/词 粘连（无分隔）  REACHCA / CAProp
GLUE_UPPER = re.compile(r"\b(?:%s)(?:%s)\b" % (TERMS, TERMS))
# ③ 大写术语紧跟另一个大写词且中间无空格（REACHCA 已在②，这里管 REACHT）
GLUE_MIX = re.compile(r"\b(?:%s)[A-Z][a-z]{2,}" % TERMS)
# ④ 撇号 + 辅音开头术语（意大利语 l'TPE / all'TPE 是语法错误）
#    ⚠️ 必须排除 OEM / ODM —— 它们以**元音**开头，`all'ODM` / `L'OEM` / `dell'ODM`
#       是正确的意大利语缩合。不排除会得到永久假报（自测撞到过 all’ODM）。
GLUE_APOS = re.compile(r"\b(?:[ld]|all|nell|dell|sull)['’](?:%s)\b" % TERM_CONS)
# ⑤ 大写术语 + 小写词尾粘连（无空格无连字符）
#    PVCund / frei von PVCund  → 应是 "PVC und"
#    le PVCe / del TPEe / il PUe / L'REACHe → 应是 "PVC" / "TPE" / "PU" / "REACH"（法/意冠词后多吐一个 e）
#    sin PVCe inodora → 实际是西语连词 e，该写成 "PVC e inodora"（少一个空格）
#    TPEs / EVAs 是合法的英文复数，必须白名单放行
GLUE_TERMWORD = re.compile(r"\b(?:%s)[a-zà-ÿ]{1,9}\b" % TERMS)
# ⑥ 专有名词 / 谚文 + 术语粘连（2026-09-17 新增家族）
#    GLUE_LOWER 要求**小写**词干 ≥3 字母，于是这一族整批漏网：
#      de  Alignment LineTPE-Yogamatte      it  Tappetino Spliced ColorTPE
#      ja  CorkTPEヨガマット                  ko  아치형PU / 스웨이드TPE / 에코TPE
#    ⚠️ 右侧必须是 `(?![A-Za-z])` 而**不是** `\b`：
#       `CorkTPEヨ` 的 E 与 ヨ 都是 word char，中间没有词边界，用 \b 恒不匹配。
#    ⚠️ 左侧 `(?<![<!])` 也不能省：TERMS 含两字母短术语 `PE`/`CA`，而每页第一行
#       都是 `<!DOCTYPE html>` —— `DOCT`+`PE` 正好凑成形状，会把 1331 页全报成命中。
#       注意只写 `(?<!<)` 不够：`<!DOCTYPE` 里 `D` 前面是 `!` 不是 `<`。
GLUE_PROPER = re.compile(r"(?<![<!])\b[A-ZÀ-Ý][A-Za-zÀ-ÿ]{2,}(?:%s)(?![A-Za-z])" % TERMS)
# ⑦ 谚文 + 术语（左侧永远是前一个词，无例外；`무PVC` 由 TERMWORD_OK 放行）
GLUE_HANGUL_L = re.compile(r"([가-힣])(?:%s)(?![가-힣])" % TERMS)
# ⑧ 术语 + 韩语名词
#    ⚠️ 不能写成「术语 + 任意谚文」—— 那一侧绝大多数是**助词**，必须连写：
#       TPE에서(130) / PU의(18) / NBR는(16) / TPE가(10) / EVA와(9) / MOQ에(4)
#       通用规则会把这 200 多处正确的韩语切成病句。
GLUE_HANGUL_R = re.compile(
    r"(?:%s)(?:폼롤러|매트|베이스|성분|코팅|무첨가|상단|소재|제품|시트|층|표면|커버|롤러|요가|패드|세트|프리|고무)" % TERMS)
# 白名单：真词，不算粘连。宁可漏报也不要假报（假报会把正常文案改坏）。
TERMWORD_OK = {
    "TPEs", "EVAs", "PUAs", "PUs", "NBRs",       # 英文复数
    "Pulver", "Puma", "Puerto",                   # 与 PU 撞头的真词
    "Peak", "Peel", "Pegasus",                    # 与 PE 撞头的真词
    "Isolation", "Isolierung",                    # 与 ISO 撞头的真词
    "SGSs",
}

FIELD_RE = [
    ("title", re.compile(r"<title>([\s\S]*?)</title>")),
    ("desc", re.compile(r'<meta name="description" content="([^"]*)"')),
    ("h1", re.compile(r"<h1[^>]*>([\s\S]*?)</h1>")),
    ("ogtitle", re.compile(r'<meta property="og:title" content="([^"]*)"')),
]


def plain(h):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def scan(path):
    try:
        s = open(path, encoding="utf-8", errors="ignore").read()
    except OSError:
        return []
    hits = []
    for name, rx in FIELD_RE:
        for m in rx.finditer(s):
            txt = plain(m.group(1))
            for label, grx in (("焊词", GLUE_LOWER), ("术语粘连", GLUE_UPPER),
                               ("术语粘词", GLUE_MIX), ("撇号语法", GLUE_APOS),
                               ("术语+小写", GLUE_TERMWORD), ("专名+术语", GLUE_PROPER),
                               ("谚文+术语", GLUE_HANGUL_L), ("术语+韩名词", GLUE_HANGUL_R)):
                for g in grx.finditer(txt):
                    if label == "术语+小写" and g.group(0) in TERMWORD_OK:
                        continue
                    # `무PVC` 是韩语「无/免」前缀（与同句 무취 并列），属构词成分
                    if label == "谚文+术语" and g.group(0).startswith("무"):
                        continue
                    hits.append((name, label, g.group(0), txt[:120]))
    return hits


def main():
    include_body = "--all" in sys.argv
    files = []
    for lg in LANGS:
        for sub in DIRS:
            base = ROOT if lg == "" else os.path.join(ROOT, lg)
            pat = os.path.join(base, sub, "*.html") if sub else os.path.join(base, "*.html")
            files += sorted(glob.glob(pat))
    with ThreadPoolExecutor(max_workers=16) as ex:
        res = list(ex.map(scan, files))

    agg = defaultdict(list)
    for f, hits in zip(files, res):
        if hits:
            agg[os.path.relpath(f, ROOT)] = hits

    print("扫描 %d 页，命中 %d 页" % (len(files), len(agg)))
    print("%-56s %-10s %-9s %s" % ("file", "field", "type", "token"))
    print("-" * 110)
    for rel in sorted(agg):
        for name, label, tok, txt in agg[rel]:
            print("%-56s %-10s %-9s %-22s | %s" % (rel, name, label, tok, txt[:60]))


if __name__ == "__main__":
    main()
