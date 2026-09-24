#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0-C：147 个产品页 × 7 语言 = 1029 页批量补 FAQ

每页 5 问 5 答，答案内嵌**该页规格表里的真实值**（MOQ / 材质 / 尺寸 / 厚度 / 配色 / Logo / 包装 / 认证），
因此每页文案互不相同 —— 避免 147 页同一段模板文字被当成重复内容。

模板见 products_faq_content.py（EN 源 + ZH 手写），de/ja/ko/fr/it/es 经 translator.py(DeepL) 译出，
落盘 i18n_build/products_faq_data.json（入库）。

注入：可见区块复用站内 .faq-list/.faq-item 样式，插在 CTA 之前；JSON-LD 另起独立块（FAQPage）。
写法：标记 + 替换式 → 幂等；落盘前断言块数、JSON 可解析、问答数 = 5。
"""
import argparse
import html
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import products_faq_content as C  # noqa: E402
import translator  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = pathlib.Path(__file__).resolve().parent / "products_faq_data.json"

TODAY = "2026-09-24"
PUBLISHED = "2026-09-15"

M_VIS_OPEN = "<!-- pfaq:v1 -->"
M_VIS_CLOSE = "<!-- /pfaq:v1 -->"
M_LD_OPEN = "<!-- pfaq-ld:v1 -->"
M_LD_CLOSE = "<!-- /pfaq-ld:v1 -->"

# 长标签优先
LABEL_ORDER = sorted(
    ((k, lg, lab) for k, m in C.LABELS.items() for lg, labs in m.items() for lab in labs),
    key=lambda t: -len(t[2]),
)


def build_data(force=False):
    if DATA.exists() and not force:
        d = json.loads(DATA.read_text(encoding="utf-8"))
        if all(len(set(d.get(lg, {})) & set(C.EN_STRINGS.values())) == len(C.EN_STRINGS)
               for lg in C.LANGS):
            return d
    src = list(C.EN_STRINGS.values())
    print("  待译 EN 串 %d 条 × %d 语言" % (len(src), len(C.LANGS)))
    d = {}
    for lg in C.LANGS:
        tr = translator.translate_lines(src, lg.upper())
        assert len(tr) == len(src), (lg, len(tr))
        d[lg] = dict(zip(src, tr))
        for s, t in d[lg].items():
            for ph in re.findall(r"XX[A-Z]+XX", s):
                assert ph in t, "%s 译文丢占位符 %s：%s" % (lg, ph, t)
    DATA.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print("  已写 %s（%.1f KB）" % (DATA.name, DATA.stat().st_size / 1024))
    translator.flush()
    return d


# ------------------------------------------------------------------ 页内事实
def parse_spec(s, lang):
    k = s.find("<table")
    if k < 0:
        return {}, {}
    seg = s[k:s.find("</table>", k)]
    vals, labels = {}, {}
    for th_raw, td_raw in re.findall(r"<tr>\s*<th>(.*?)</th>\s*<td>(.*?)</td>", seg, re.S):
        # EN 页 th 里是 <span class="lang-en">…</span><span class="lang-zh">…</span>
        m = re.search(r'<span class="lang-en">(.*?)</span>', th_raw, re.S)
        # ⚠️ 必须 html.unescape：站内 th/td 里有 `&amp;`（如 "Colors &amp; Print"），
        #    不反转义再 esc() 会产出 `&amp;amp;`（实测踩过）
        th = html.unescape(re.sub(r"<[^>]+>", "", m.group(1) if m else th_raw)).strip()
        td = html.unescape(re.sub(r"<[^>]+>", "", td_raw)).strip()
        for key, lg, lab in LABEL_ORDER:
            if lg != lang:
                continue
            if th == lab or th.startswith(lab):
                if key not in vals and td and td not in ("—", "-", "–"):
                    vals[key] = td
                    labels[key] = th
                break
    return vals, labels


def page_facts(path, lang):
    s = path.read_text(encoding="utf-8")
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
    g = json.loads(m.group(1)).get("@graph", [])
    prod = next((n for n in g if n.get("@type") == "Product"), {})
    # ⚠️ 站内 JSON-LD 的商品名里也有 HTML 实体（如 "Dumbbell &amp; Barbell"），
    #    不反转义会被 esc() 二次转义成 `&amp;amp;`（实测 fi5）
    name = html.unescape((prod.get("name") or "").strip())
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S)
    h1s = h1.group(1) if h1 else ""
    zh = ""
    zm = re.search(r'<span class="lang-zh">(.*?)</span>', h1s, re.S)
    if zm:
        zh = html.unescape(
            re.split(r"\s+[—–]\s+", re.sub(r"<[^>]+>", "", zm.group(1)).strip())[0].strip())
    if not name:
        name = html.unescape(
            re.split(r"\s+[—–]\s+", re.sub(r"<[^>]+>", "", h1s).strip())[0])
    vals, labels = parse_spec(s, lang)
    return s, name, zh, vals, labels


# ------------------------------------------------------------------ 渲染
def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def pair(en, zh, lang):
    if lang == "en":
        return '<span class="lang-en">%s</span><span class="lang-zh">%s</span>' % (esc(en), esc(zh))
    return "<span >%s</span>" % esc(en)


def sub(t, **kw):
    for k, v in kw.items():
        t = t.replace("XX%sXX" % k, v)
    return t


def render_section(lang, title, qa):
    items = []
    for q, a in qa:
        items.append(
            '        <details class="faq-item">\n'
            "          <summary>%s</summary>\n"
            '          <div class="faq-a">%s</div>\n'
            "        </details>" % (pair(q[0], q[1], lang), pair(a[0], a[1], lang))
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
        "%s" % (M_VIS_OPEN, pair("FAQ", "常见问题", lang), pair(title[0], title[1], lang),
                "\n".join(items), M_VIS_CLOSE)
    )


def render_ld(lang, url, title, qa):
    web = {
        "@context": "https://schema.org", "@type": "WebPage", "@id": url + "#webpage",
        "url": url, "name": title, "inLanguage": lang,
        "datePublished": PUBLISHED, "dateModified": TODAY,
        "isPartOf": {"@type": "WebSite", "name": "SANFAN", "url": "https://fjsanfan.com/"},
    }
    faq = {
        "@context": "https://schema.org", "@type": "FAQPage", "@id": url + "#faq",
        "inLanguage": lang, "isPartOf": {"@id": url + "#webpage"},
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa],
    }
    out = ""
    for obj in (web, faq):
        out += ('<script type="application/ld+json">\n%s\n</script>\n'
                % json.dumps(obj, ensure_ascii=False, indent=2))
    return M_LD_OPEN + "\n" + out + M_LD_CLOSE + "\n"


def strip_blocks(s):
    for o, c, tail in ((M_VIS_OPEN, M_VIS_CLOSE, "\n\n  "), (M_LD_OPEN, M_LD_CLOSE, "\n")):
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
    s = re.sub(r"\n[ \t]*\n[ \t]*<!-- pfaq:v1 -->", "\n\n  <!-- pfaq:v1 -->", s)
    s = re.sub(r"\n[ \t]*<!-- pfaq-ld:v1 -->", "\n<!-- pfaq-ld:v1 -->", s)
    return s


def build_qa(lang, name, zh_name, vals, labels, tr):
    """返回 [(q_en,q_zh, a_en,a_zh), ...]"""
    def nz(n):
        """中文模板里名字后是否补空格：CJK 结尾不补，拉丁字母结尾补一个"""
        return n if re.search(r"[\u4e00-\u9fff]$", n) else n + " "

    if lang == "en":
        T, Z = C.EN_STRINGS, C.ZH
        nm, nmz = name, nz(zh_name or name)
    else:
        T = Z = {k: tr[lang][v] for k, v in C.EN_STRINGS.items()}
        nm = nmz = name

    def g(key, default=""):
        return vals.get(key, default)

    # A1：MOQ 有数字才用带数值的版本
    moq = g("MOQ")
    a1k = "a1" if (moq and re.search(r"\d", moq)) else "a1f"
    a1 = (sub(T[a1k], NAME=nm, MOQ=moq), sub(Z[a1k], NAME=nmz, MOQ=moq))
    # A3：字段清单（用页面自身的本地化标签）；一个字段都没有时走兜底句
    frags = []
    for key in C.FIELDS3:
        if key in vals:
            frags.append("%s: %s." % (labels[key], vals[key]))
    if frags:
        a3 = (T["lead3"] + " " + " ".join(frags), Z["lead3"] + " " + " ".join(frags))
    else:
        a3 = (T["a3f"], Z["a3f"])
    # A4：三档 —— 尺寸+厚度齐 / 只有尺寸 / 都没有
    if "SIZE" in vals and "THICK" in vals:
        a4 = (sub(T["a4"], SIZE=vals["SIZE"], THICK=vals["THICK"]),
              sub(Z["a4"], SIZE=vals["SIZE"], THICK=vals["THICK"]))
    elif "SIZE" in vals:
        a4 = (sub(T["a4f"], SIZE=vals["SIZE"]), sub(Z["a4f"], SIZE=vals["SIZE"]))
    else:
        a4 = (T["a4g"], Z["a4g"])
    comp = g("COMPLIANCE", "REACH / CA Prop 65 / ISO 9001 / BSCI")
    a5 = (sub(T["a5"], NAME=nm, COMP=comp), sub(Z["a5"], NAME=nmz, COMP=comp))
    a2 = (sub(T["a2"], NAME=nm), sub(Z["a2"], NAME=nmz))

    if lang == "en":
        return [
            ((T["q1"], Z["q1"]), a1),
            ((T["q2"], Z["q2"]), a2),
            ((T["q3"], Z["q3"]), a3),
            ((T["q4"], Z["q4"]), a4),
            ((T["q5"], Z["q5"]), a5),
        ]
    return [
        ((T["q1"], T["q1"]), a1),
        ((T["q2"], T["q2"]), (a2[0],) * 2),
        ((T["q3"], T["q3"]), a3),
        ((T["q4"], T["q4"]), a4),
        ((T["q5"], T["q5"]), (a5[0],) * 2),
    ]


def inject(path, lang, tr, dry, stats):
    s, name, zh, vals, labels = page_facts(path, lang)
    rel = path.relative_to(ROOT).as_posix()
    url = "https://fjsanfan.com/" + rel
    qa = build_qa(lang, name, zh, vals, labels, tr)
    title = (sub(C.EN_STRINGS["title"], NAME=name),
             sub(C.ZH["title"], NAME=zh or name))
    if lang != "en":
        title = (sub(tr[lang][C.EN_STRINGS["title"]], NAME=name),) * 2
    sec = render_section(lang, title, qa)
    ld = render_ld(lang, url, title[0], [(q[0], a[0]) for q, a in qa])

    out = strip_blocks(s)
    i = out.find('<div class="cta-band">')
    assert i > 0, "%s 无 cta-band" % rel
    j = out.rfind("<section", 0, i)
    assert j > 0, rel
    out = out[:j] + sec + "\n\n  " + out[j:]
    k = out.find("</script>", out.find('type="application/ld+json"')) + len("</script>\n")
    out = out[:k] + ld + out[k:]

    assert out.count(M_VIS_OPEN) == 1 and out.count(M_LD_OPEN) == 1, rel
    assert out.count('class="faq-item"') == 5, (rel, out.count('class="faq-item"'))
    left = re.findall(r"XX[A-Z]+XX", sec + ld)
    assert not left, "%s 残留未替换占位符 %s" % (rel, left)
    assert "is ." not in sec and "为 。" not in sec, "%s 出现空值句" % rel
    for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', out, re.S):
        json.loads(b)
    fp = [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', out, re.S)]
    assert any(x.get("@type") == "FAQPage" and len(x["mainEntity"]) == 5 for x in fp), rel
    assert 'href="href=' not in out

    changed = out != s
    if changed and not dry:
        path.write_text(out, encoding="utf-8")
    stats["changed" if changed else "same"] += 1
    stats["pages"] += 1
    stats["missing"] += sum(1 for f in ("MOQ", "SIZE", "COMPLIANCE") if f not in vals)
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--retranslate", action="store_true")
    ap.add_argument("--langs", default="")
    ap.add_argument("--limit", type=int, default=0, help="每语言只处理前 N 页（测试用）")
    args = ap.parse_args()
    langs = [x for x in args.langs.split(",") if x] or ["en"] + C.LANGS

    if args.check:
        bad = {"vis": [], "ld": [], "faq": [], "n": 0}
        for lg in langs:
            d = ROOT / ("products" if lg == "en" else lg + "/products")
            for p in sorted(d.glob("*.html")):
                bad["n"] += 1
                s = p.read_text(encoding="utf-8")
                if M_VIS_OPEN not in s:
                    bad["vis"].append(str(p.relative_to(ROOT)))
                if M_LD_OPEN not in s:
                    bad["ld"].append(str(p.relative_to(ROOT)))
                if "FAQPage" not in s:
                    bad["faq"].append(str(p.relative_to(ROOT)))
        print("检查 %d 页 | 缺可见 %d | 缺 JSON-LD %d | 缺 FAQPage %d"
              % (bad["n"], len(bad["vis"]), len(bad["ld"]), len(bad["faq"])))
        for k in ("vis", "ld", "faq"):
            if bad[k]:
                print("  %s: %s" % (k, bad[k][:6]))
        sys.exit(1 if (bad["vis"] or bad["ld"] or bad["faq"]) else 0)

    print("=== 准备译文 ===")
    tr = build_data(force=args.retranslate)

    stats = {"pages": 0, "changed": 0, "same": 0, "missing": 0}
    for lg in langs:
        d = ROOT / ("products" if lg == "en" else lg + "/products")
        files = sorted(d.glob("*.html"))
        if args.limit:
            files = files[:args.limit]
        for p in files:
            inject(p, lg, tr, not args.apply, stats)
        print("  %-3s %3d 页 %s" % (lg, len(files), "已更新" if args.apply else "待更新"))
    print("\n合计 %d 页 | 需改动 %d | 无需改动 %d | 缺关键字段次数 %d %s"
          % (stats["pages"], stats["changed"], stats["same"], stats["missing"],
             "（已落盘）" if args.apply else "（空跑）"))


if __name__ == "__main__":
    main()
