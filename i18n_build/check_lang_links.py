#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""语言站链接「语言归属」体检 —— 验证语言页上的站内链接指向的是**本语言**版本。

与 check_i18n_links.py 的分工：
  check_i18n_links.py  只验证「目标文件是否存在」（死链）
  本脚本               进一步验证「目标是不是该语言的版本」——本地化质量的核心指标

判定五类（只看 <a href> 导航链接；hreflang/canonical 是 SEO 互链，另行处理）：
  ok          目标就是本语言页
  SHOULD-FIX  目标落在英文页，但本语言版本**其实存在**  ← 真缺陷
              （典型成因：生成顺序 / T1_SET 不含目标 → rewrite_rel 走了英文回退分支）
  fallback    目标落在英文页，本语言版本确实不存在      ← 设计内回退，不算错
  dead        目标文件不存在                            ← 死链
  wrong-lang  目标落在第三种语言                        ← 异常

用法：
  python3 i18n_build/check_lang_links.py              # 汇总
  python3 i18n_build/check_lang_links.py --detail      # 附 SHOULD-FIX / dead 明细
"""
import os
import re
import sys
import collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
SKIP_RE = re.compile(r"^(https?://|//|mailto:|tel:|javascript:|data:|#|\?)", re.I)
A_RE = re.compile(r'<a\b[^>]*?\shref\s*=\s*"([^"]*)"', re.I)
ASSET_EXT = (".webp", ".jpg", ".jpeg", ".png", ".svg", ".gif", ".ico",
             ".css", ".js", ".xml", ".txt", ".pdf", ".json")


def html_set(lang):
    out = set()
    d = os.path.join(ROOT, lang)
    for dp, _, fs in os.walk(d):
        for f in fs:
            if f.endswith(".html"):
                out.add(os.path.relpath(os.path.join(dp, f), d).replace(os.sep, "/"))
    return out


EXIST = {lg: html_set(lg) for lg in LANGS}

EN = set()
for _dp, _, _fs in os.walk(ROOT):
    if any(s in _dp for s in ("/.git", "/node_modules", "/outputs", "/.workbuddy")):
        continue
    _r = os.path.relpath(_dp, ROOT)
    if _r.split(os.sep)[0] in LANGS:
        continue
    for _f in _fs:
        if _f.endswith(".html"):
            EN.add(os.path.relpath(os.path.join(_dp, _f), ROOT).replace(os.sep, "/"))


def parse(page_rel, href):
    """page_rel 形如 de/products/x.html。返回 (tlang|None, tpath) 或 None（跳过）"""
    h = href.strip()
    if not h or SKIP_RE.match(h):
        return None
    h = h.split("#")[0].split("?")[0]
    if not h:
        return None
    if h.startswith("/"):
        rel = h.lstrip("/")
    else:
        rel = os.path.normpath(os.path.join(os.path.dirname(page_rel), h)).replace(os.sep, "/")
    parts = rel.split("/")
    if parts and parts[0] in LANGS:
        tlang, tp = parts[0], "/".join(parts[1:])
    else:
        tlang, tp = None, rel
    if tp == "" or tp.endswith("/"):
        tp += "index.html"
    if not tp.endswith(".html"):
        return None                       # 资源链接（css/js/图片）不在语言归属范围内
    return tlang, tp


def classify(lang, page_rel, href):
    r = parse(page_rel, href)
    if r is None:
        return None
    tlang, tp = r
    if tlang == lang:
        return "ok" if tp in EXIST[lang] else "dead"
    if tlang is None:
        if tp not in EN:
            return "dead"
        return "SHOULD-FIX" if tp in EXIST[lang] else "fallback"
    if tp in EXIST.get(tlang, ()):
        return "wrong-lang"
    return "dead"


def strip_switcher(h):
    """挖掉语言切换器块。

    ⚠️ 必须排除：切换器里的 <a href="/about.html">EN</a>、<a href="/ja/about.html">JA</a>
    是**故意**指向别语言的跳转，属于设计内行为。若不排除，每页会固定产生
    2 条 SHOULD-FIX（EN / 中文）+ 5 条 wrong-lang（其他 5 种语言）的假阳性。
    （实测：76 页 × 2 = 152、76 页 × 5 = 380 —— 正好是误报的全部来源。）
    用 div 配平定位块边界，非贪婪 `.*?</div>` 会停在 lang-menu 的内层闭合上。
    """
    out, i = [], 0
    while True:
        s = h.find('<div class="lang-switch">', i)
        if s < 0:
            out.append(h[i:])
            break
        out.append(h[i:s])
        depth, e = 0, -1
        for m in re.finditer(r"<(/?)div\b[^>]*>", h[s:]):
            depth += -1 if m.group(1) else 1
            if depth == 0:
                e = s + m.end()
                break
        if e < 0:
            out.append(h[s:])
            break
        i = e
    return "".join(out)


def main():
    detail = "--detail" in sys.argv
    agg = collections.Counter()
    per_lang = collections.defaultdict(collections.Counter)
    bad = collections.defaultdict(list)
    fallback_pages = collections.defaultdict(collections.Counter)

    for lg in LANGS:
        files = sorted(
            "%s/%s" % (lg, p) for p in EXIST[lg]
        )
        for p in files:
            s = strip_switcher(open(p, encoding="utf-8", errors="replace").read())
            for m in A_RE.finditer(s):
                k = classify(lg, p, m.group(1))
                if k is None:
                    continue
                agg[k] += 1
                per_lang[lg][k] += 1
                if k in ("SHOULD-FIX", "dead", "wrong-lang"):
                    bad[k].append((p, m.group(1)))
                elif k == "fallback":
                    fallback_pages[lg][m.group(1).split("#")[0]] += 1

    print("=== 各语言页面链接归属 ===")
    print("%-4s %6s %8s %11s %9s %11s" % ("语言", "页数", "ok", "SHOULD-FIX", "fallback", "dead/wrong"))
    for lg in LANGS:
        c = per_lang[lg]
        print("%-4s %6d %8d %11d %9d %11d"
              % (lg, len(EXIST[lg]), c["ok"], c["SHOULD-FIX"], c["fallback"],
                 c["dead"] + c["wrong-lang"]))
    print("%-4s %6s %8d %11d %9d %11d" % ("合计", "", agg["ok"], agg["SHOULD-FIX"],
                                          agg["fallback"], agg["dead"] + agg["wrong-lang"]))
    print()

    fix_n, dead_n, wrong_n = agg["SHOULD-FIX"], agg["dead"], agg["wrong-lang"]
    if fix_n == 0 and dead_n == 0 and wrong_n == 0:
        print("✅ 链接语言归属全部正确：0 条该本地化却落英文、0 死链、0 跨语言")
    else:
        if fix_n:
            print("❌ %d 条「应指向语言版却落在英文」" % fix_n)
        if dead_n:
            print("❌ %d 条死链" % dead_n)
        if wrong_n:
            print("❌ %d 条指向第三种语言" % wrong_n)

    if detail and (bad or fallback_pages):
        for k in ("SHOULD-FIX", "dead", "wrong-lang"):
            if not bad[k]:
                continue
            print("\n--- %s 明细（最多 30 条）---" % k)
            for p, h in bad[k][:30]:
                print("  %s  ->  %s" % (p, h))

    print("\n=== 回退英文 top（设计内，仅作观察；若某页回退条数骤增说明该批漏生成）===")
    for lg in LANGS:
        top = fallback_pages[lg].most_common(4)
        if top:
            print("  %-3s %s" % (lg, ", ".join("%s×%d" % (t, n) for t, n in top)))
    return 1 if (fix_n or dead_n or wrong_n) else 0


if __name__ == "__main__":
    sys.exit(main())
