#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0-A：给 /pilates/ 板块 63 页补 GEO 三件套

  ① JSON-LD 增 WebPage 节点（datePublished / dateModified / inLanguage）
  ② JSON-LD 增 FAQPage 节点（6 问 6 答，本语言）
  ③ 页面可见 FAQ 区块（复用站内既有 .faq-list / .faq-item 样式，插在 CTA 之前）

内容来源：pilates_faq_content.py（EN 源 + ZH 手写），其余 5 语言经 translator.py(DeepL) 译出，
结果落盘 i18n_build/pilates_faq_data.json（**入库**，非 cache/，保证可复现、不重复烧额度）。

写法要点（踩过的坑）：
- **替换式 + 标记**：可见区块用 `<!-- plfaq:v1 -->`；JSON-LD 用独立 `<script>` 块 + 同名标记。
  重跑先摘旧块再重插 → 幂等，且改了文案能生效（"只补缺"式脚本会改不动存量页）。
- JSON-LD **不塞进原 @graph**，另起独立 script 块：blog 页本就是多块共存，
  且这样不必重排原块格式（避免整块 diff）。
- 落盘前断言：块内必备标记齐全、FAQPage 能被 json.loads 解析、问答条数 = 6。
- ⚠️ 可见 HTML 里的 `&` 必须转义为 `&amp;`（族名 "Reformer Tower & 3-in-1" 含 &）；
  JSON-LD 在 `<script>` 内属 raw text，`&` 保持字面。
"""
import argparse
import datetime
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import pilates_faq_content as C  # noqa: E402
import translator  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = pathlib.Path(__file__).resolve().parent / "pilates_faq_data.json"

TODAY = "2026-09-24"
PUBLISHED = "2026-09-15"

M_VIS_OPEN = "<!-- plfaq:v1 -->"
M_VIS_CLOSE = "<!-- /plfaq:v1 -->"
M_LD_OPEN = "<!-- plfaq-ld:v1 -->"
M_LD_CLOSE = "<!-- /plfaq-ld:v1 -->"

ALL_LANGS = ["en", "de", "ja", "ko", "fr", "it", "es"]


# ------------------------------------------------------------------ 文案准备
def en_strings():
    """所有需要翻译的 EN 串（去重、稳定顺序）"""
    out = [C.TITLE_EN, "Pilates apparatus — buyer questions"]
    for q, a, _, _ in C.CORE:
        out += [q, a]
    for k in C.FAQFILES:
        q, a, _, _ = C.FAMILY_QA[k]
        out += [q, a]
    seen, uniq = set(), []
    for s in out:
        if s not in seen:
            seen.add(s)
            uniq.append(s)
    return uniq


def build_data(force=False):
    """翻译并落盘；已存在且完整则直接复用"""
    if DATA.exists() and not force:
        d = json.loads(DATA.read_text(encoding="utf-8"))
        need = set(en_strings())
        missing = [lg for lg in C.LANGS if len(set(d.get(lg, {})) & need) != len(need)]
        if not missing:
            return d
        print("  数据文件缺语言：%s → 补译" % missing)

    src = en_strings()
    print("  待译 EN 串 %d 条 × %d 语言 = %d 条" % (len(src), len(C.LANGS), len(src) * len(C.LANGS)))
    d = {}
    for lg in C.LANGS:
        tr = translator.translate_lines(src, lg.upper())
        assert len(tr) == len(src), (lg, len(tr), len(src))
        d[lg] = dict(zip(src, tr))
        for s, t in d[lg].items():
            for ph in ("XXFAMILYXX", "XXMODELSXX"):
                if ph in s:
                    assert ph in t, "占位符 %s 在 %s 译文里丢了：%s" % (ph, lg, t)
    DATA.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print("  已写 %s（%.1f KB）" % (DATA.name, DATA.stat().st_size / 1024))
    translator.flush()
    return d


# ------------------------------------------------------------------ 取页内事实
def page_facts(path):
    s = path.read_text(encoding="utf-8")
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
    g = json.loads(m.group(1)).get("@graph", [])
    prod = next((n for n in g if n.get("@type") == "Product"), {})
    il = next((n for n in g if n.get("@type") == "ItemList"), {})
    family = (prod.get("name") or "").strip()
    h1m = re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S)
    h1 = h1m.group(1) if h1m else ""
    if not family:
        family = re.split(r"\s+[—–-]\s+", re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h1)).strip())[0]
    # ZH 族名：EN 页 h1 里的 .lang-zh span
    zh = ""
    zm = re.search(r'<span class="lang-zh">(.*?)</span>', h1, re.S)
    if zm:
        zh = re.split(r"\s+[—–-]\s+", re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", zm.group(1))).strip())[0]
    return s, family, int(il.get("numberOfItems") or 0), zh


# ------------------------------------------------------------------ 渲染
def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def pair(en, zh, lang):
    """EN 页 = 行内配对 span（与站内 body 写法一致）；语言页 = 单语空 class span"""
    if lang == "en":
        return '<span class="lang-en">%s</span><span class="lang-zh">%s</span>' % (esc(en), esc(zh))
    return "<span >%s</span>" % esc(en)


def render_section(lang, title, qa_pairs):
    """qa_pairs: [(q_en, q_zh, a_en, a_zh), ...]"""
    items = []
    for q_en, q_zh, a_en, a_zh in qa_pairs:
        items.append(
            '        <details class="faq-item">\n'
            "          <summary>%s</summary>\n"
            '          <div class="faq-a">%s</div>\n'
            "        </details>" % (pair(q_en, q_zh, lang), pair(a_en, a_zh, lang))
        )
    return (
        "%s\n"
        '  <section class="section pl-soft">\n'
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
        "%s" % (M_VIS_OPEN, pair("FAQ", "常见问题", lang), pair(title[0], title[1], lang),
                "\n".join(items), M_VIS_CLOSE)
    )


def render_ld(lang, url, title, qa_pairs):
    """qa_pairs: [(q, a), ...] 已是本语言"""
    web = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "@id": url + "#webpage",
        "url": url,
        "name": title,
        "inLanguage": lang,
        "datePublished": PUBLISHED,
        "dateModified": TODAY,
        "isPartOf": {"@type": "WebSite", "name": "SANFAN", "url": "https://fjsanfan.com/"},
    }
    faq = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "@id": url + "#faq",
        "inLanguage": lang,
        "isPartOf": {"@id": url + "#webpage"},
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in qa_pairs
        ],
    }
    body = ""
    for obj in (web, faq):
        body += ('<script type="application/ld+json">\n%s\n</script>\n'
                 % json.dumps(obj, ensure_ascii=False, indent=2))
    return M_LD_OPEN + "\n" + body + M_LD_CLOSE + "\n"


# ------------------------------------------------------------------ 注入
def strip_blocks(s):
    """摘旧块 + 把块前空白归一化到规范形态 → 反复重跑不漂移（曾因只吃 '\\n' 留下 2 空格，
    每跑一次块前就多 2 个空格，导致脚本永远"需改动"）。"""
    for o, c, tail in ((M_VIS_OPEN, M_VIS_CLOSE, "\n\n  "),
                       (M_LD_OPEN, M_LD_CLOSE, "\n")):
        while True:
            i, j = s.find(o), s.find(c)
            if i < 0 or j < 0:
                break
            end = j + len(c)
            if s[end:end + len(tail)] == tail:
                end += len(tail)
            else:
                while end < len(s) and s[end] == "\n":
                    end += 1
            s = s[:i] + s[end:]
    s = re.sub(r"\n[ \t]*\n[ \t]*<!-- plfaq:v1 -->", "\n\n  <!-- plfaq:v1 -->", s)
    s = re.sub(r"\n[ \t]*<!-- plfaq-ld:v1 -->", "\n<!-- plfaq-ld:v1 -->", s)
    return s


def inject(path, lang, fam_name, models, tr, dry, stats):
    s, family, n, zh_family = page_facts(path)
    if models:
        n = models
    base = ROOT / path.relative_to(ROOT)
    url = "https://fjsanfan.com/" + str(path.relative_to(ROOT)).replace("index.html", "").replace("\\", "/")
    is_index = path.name == "index.html"

    # 文案组装
    if lang == "en":
        fam = family
        qa_pairs = [(q, qzh, a, azh) for q, a, qzh, azh in C.CORE]
        fq, fa, fqz, faz = C.FAMILY_QA["pilates/" + path.name]
        qa_pairs.append((fq, fqz, fa, faz))
        title = (C.TITLE_EN.replace("XXFAMILYXX", fam),
                 C.TITLE_ZH.replace("XXFAMILYXX", zh_family or fam))
        if is_index:
            title = "Pilates apparatus — buyer questions", "普拉提器械 —— 买家常问"
        # ⚠️ qa_pairs 每项是 (q_en, q_zh, a_en, a_zh) —— 取 LD 时必须取 [0] 与 [2]，
        #    写成 `for q, a, _, _ in qa_pairs` 会把 **中文问题** 当成答案塞进 acceptedAnswer（实测踩过）
        qa_ld = [(p[0], p[2]) for p in qa_pairs]
    else:
        T = tr[lang]
        fam = family
        qa_pairs = [(T[q], T[q], T[a], T[a]) for q, a, _, _ in C.CORE]
        fq, fa, fqz, faz = C.FAMILY_QA["pilates/" + path.name]
        qa_pairs.append((T[fq], T[fq], T[fa], T[fa]))
        tpl = "Pilates apparatus — buyer questions" if is_index else C.TITLE_EN
        t = T[tpl].replace("XXFAMILYXX", fam)
        title = (t, t)
        qa_ld = [(T[q], T[a]) for q, a, _, _ in C.CORE] + [(T[fq], T[fa])]

    # 数值占位
    def sub(x):
        return x.replace("XXMODELSXX", str(n)).replace("XXFAMILYXX", fam)

    qa_pairs = [(sub(a), sub(b), sub(c), sub(d)) for a, b, c, d in qa_pairs]
    qa_ld = [(sub(a), sub(b)) for a, b in qa_ld]
    title = (sub(title[0]), sub(title[1]))
    # 落盘前先卡住"问题被当成答案"这类错位（答案必须明显长于问题且不相同）
    for q, a in qa_ld:
        assert a != q and len(a) >= 80, "%s 答案异常（疑似错位）：Q=%r A=%r" % (path.name, q[:40], a[:40])

    sec = render_section(lang, title, qa_pairs)
    ld = render_ld(lang, url, title[0], qa_ld)

    out = strip_blocks(s)
    # 可见区块：插在 CTA section 之前
    i = out.find('<div class="cta-band">')
    assert i > 0, "%s 找不到 cta-band" % path
    j = out.rfind("<section", 0, i)
    assert j > 0, "%s 找不到 CTA section 起点" % path
    out = out[:j] + sec + "\n\n  " + out[j:]
    # JSON-LD：插在原 ld+json 块之后
    k = out.find("</script>", out.find('type="application/ld+json"'))
    assert k > 0, "%s 找不到原 JSON-LD 块" % path
    k += len("</script>\n")
    out = out[:k] + ld + out[k:]

    # 落盘前断言
    assert out.count(M_VIS_OPEN) == 1 and out.count(M_LD_OPEN) == 1, path
    for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', out, re.S):
        json.loads(b)
    faq = [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', out, re.S)]
    fp = [x for x in faq if x.get("@type") == "FAQPage"]
    assert fp and len(fp[0]["mainEntity"]) == 6, (path, len(fp))
    assert out.count('class="faq-item"') == 6, (path, out.count('class="faq-item"'))
    assert "href=\"href=" not in out

    changed = out != s
    if changed and not dry:
        base.write_text(out, encoding="utf-8")
    stats["changed" if changed else "same"] += 1
    stats["pages"] += 1
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true", help="只统计覆盖情况")
    ap.add_argument("--retranslate", action="store_true", help="强制重译")
    ap.add_argument("--langs", default="", help="只处理指定语言，逗号分隔，如 de,ja")
    args = ap.parse_args()

    langs = [x for x in args.langs.split(",") if x] or ALL_LANGS

    if args.check:
        miss = {"vis": [], "ld": [], "faq": [], "pages": 0}
        for lg in langs:
            d = ROOT / ("pilates" if lg == "en" else lg + "/pilates")
            for p in sorted(d.glob("*.html")):
                miss["pages"] += 1
                s = p.read_text(encoding="utf-8")
                if M_VIS_OPEN not in s:
                    miss["vis"].append(str(p.relative_to(ROOT)))
                if M_LD_OPEN not in s:
                    miss["ld"].append(str(p.relative_to(ROOT)))
                if "FAQPage" not in s:
                    miss["faq"].append(str(p.relative_to(ROOT)))
        print("检查页数 %d | 缺可见区块 %d | 缺 JSON-LD %d | 缺 FAQPage %d"
              % (miss["pages"], len(miss["vis"]), len(miss["ld"]), len(miss["faq"])))
        for k in ("vis", "ld", "faq"):
            if miss[k]:
                print("  缺 %s: %s" % (k, miss[k][:8]))
        sys.exit(1 if (miss["vis"] or miss["ld"] or miss["faq"]) else 0)

    print("=== 准备译文 ===")
    tr = build_data(force=args.retranslate)

    stats = {"pages": 0, "changed": 0, "same": 0}
    for lg in langs:
        d = ROOT / ("pilates" if lg == "en" else lg + "/pilates")
        files = sorted(d.glob("*.html"))
        assert len(files) == 9, (lg, len(files))
        for p in files:
            ch = inject(p, lg, None, None, tr, not args.apply, stats)
        print("  %-3s 9 页 %s" % (lg, "已更新" if args.apply else "待更新"))

    print("\n合计 %d 页 | 需改动 %d | 无需改动 %d %s"
          % (stats["pages"], stats["changed"], stats["same"],
             "（已落盘）" if args.apply else "（空跑）"))


if __name__ == "__main__":
    main()
