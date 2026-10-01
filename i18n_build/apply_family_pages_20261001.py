#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
族页「画册重构」统一落盘器（配置驱动，覆盖 reformer / tower / chair / cadillac / specialty）

背景
----
线上普拉提板块跑的是 NIC/NLH/NIM 内部编码 + 旧材质口径，与 2026 画册
（7 系列 69 台）完全对不上。换数据源 ≠ 只换正文表格 —— 旧体系同时活在
**七层**里，只换一层会让页面自相矛盾、搜索引擎读到的仍是旧型号：

  ① 正文三区块   #catalog / #catalogue-pages / #models-compared（整块替换）
  ② meta description ×3（description / og:description / twitter:description）
  ③ JSON-LD Product.material 数组
  ④ JSON-LD AggregateOffer.offerCount
  ⑤ JSON-LD ItemList（numberOfItems + 全部 ListItem 条目）
  ⑥ FAQ 里的型号数（JSON-LD 英文 1 处 + 可见正文英文 1 处 + 中文 1 处）
  ⑦ hero eyebrow 的「N models · M timber options」

做法
----
把全部改动点算成 (start, end, new) 字符区间，**按 start 降序**依次替换
—— 这样前面的替换不会让后面的坐标漂移（用行号会）。

⚠️ reformer 页在上一步已落盘过 SEO 层（②–⑦ 的旧串已归零）。
   本脚本对它只重落正文区块（`skip_seo`），否则那几个 pattern 全部 miss。

安全
----
默认 dry-run；`--write` 才落盘。落盘前备份到 ~/.workbuddy/backups/fjsanfan/，
落盘后立刻复读校验 + 断言（旧串归零 / 标签配平 / 双语配对 / 关键计数）。

用法
----
  python apply_family_pages_20261001.py                    # 全部 dry-run
  python apply_family_pages_20261001.py --family chair      # 单族 dry-run
  python apply_family_pages_20261001.py --family chair --write
"""
import argparse
import collections
import datetime
import difflib
import json
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "i18n_build" / "data" / "catalog_pilates_models_v2.json"
FRAG_DIR = ROOT / "outputs" / "pilates_family_catalog_20261001"
BACKUP_DIR = pathlib.Path.home() / ".workbuddy" / "backups" / "fjsanfan"

# ---------------------------------------------------------------- 每族配置
# series : 画册章节号；filter 用于 Tower 族（塔架款散在 A/C 两线内）
# skip_seo: 该页 SEO 层已是新值（reformer 上一步落过），只重落正文区块
CFG = {
    "reformer": {
        "page": "pilates/pilates-reformer.html",
        "series": ["A.", "B.", "C."],
        "display_en": "Pilates Reformer",
        "skip_seo": True,
    },
    "tower": {
        "page": "pilates/pilates-reformer-tower.html",
        "series": ["A.", "C."],
        "filter": r"tower|3\s*-?\s*in\s*-?\s*1",
        "display_en": "Reformer Tower & 3-in-1",
        # 塔架款跨 A/C 两线，FAQ 措辞不能再说 in this line
        "eyebrow_en": "{n} tower builds · {p} catalogue pages",
        "eyebrow_zh": "{n} 款塔架配置 · {p} 张画册页",
        "faq_en_new": "Specification sheets and photos covering all {n} tower and 3-in-1 builds",
        "faq_zh_new": "全部 {n} 款塔架与三合一配置的规格书与实拍图",
    },
    "chair": {
        "page": "pilates/pilates-wunda-chair.html",
        "series": ["F."],
        "display_en": "Pilates Wunda Chair",
    },
    "cadillac": {
        "page": "pilates/pilates-cadillac.html",
        "series": ["D."],
        "display_en": "Pilates Cadillac",
    },
    "specialty": {
        "page": "pilates/pilates-specialty.html",
        "series": ["G."],
        "display_en": "Pilates Specialty",
    },
}

DEF_EYEBROW_EN = "{n} models · {p} catalogue pages"
DEF_EYEBROW_ZH = "{n} 个型号 · {p} 张画册页"
DEF_FAQ_EN = "Specification sheets and photos covering all {n} models in this line"
DEF_FAQ_ZH = "本线全部 {n} 个型号的规格书与实拍图"

MAT_ZH = {
    "Aluminum": "铝合金", "Carbon steel": "碳钢", "Metal": "金属",
    "Maple": "枫木", "Oak": "橡木", "Stainless steel": "不锈钢",
}

# ---------------------------------------------------------- 区块定位（两态）
# 新态：脚本落盘后的 id 化三连区块（reformer 走这条）
NEW_BLOCK_RE = re.compile(
    r'  <section class="section" id="catalog">.*?'
    r'  <section class="section pl-soft" id="catalogue-pages">.*?'
    r'  <section class="section" id="models-compared">.*?</section>\n',
    re.S)
# 旧态：站点原有模板区块（其余四族走这条）
OLD_BLOCK_RE = re.compile(
    r'  <section class="section">\n'
    r'    <div class="container">\n'
    r'      <div class="pl-block">\n'
    r'        <div class="im"><img src="\.\./assets/img/[^"]+"[^>]*/>'
    r'.*?<p class="pl-spec-cap">.*?</p>\n'
    r'    </div>\n'
    r'  </section>\n',
    re.S)


def load_rows(cfg):
    rows = json.loads(DATA.read_text("utf-8"))
    rows = [r for r in rows if r["series"].startswith(tuple(cfg["series"]))]
    if cfg.get("filter"):
        f = re.compile(cfg["filter"], re.I)
        rows = [r for r in rows if f.search(str(r["model"]))]
    return sorted(rows, key=lambda r: (r["series"], r["page"], str(r["model"])))


def build_itemlist(rows, display_en):
    items = []
    for i, r in enumerate(rows, 1):
        items.append('        {\n          "@type": "ListItem",\n'
                     f'          "position": {i},\n'
                     f'          "name": "{r["model"]}"\n        }}')
    return ('      "@type": "ItemList",\n'
            f'      "name": "{display_en} — model range",\n'
            f'      "numberOfItems": {len(rows)},\n'
            '      "itemListElement": [\n'
            + ",\n".join(items) + '\n      ]\n    }')


def build_material(rows):
    seen = []
    for r in rows:
        m = r.get("material")
        if m and m not in seen:
            seen.append(m)
    body = ",\n".join(f'        "{m}"' for m in seen)
    return '      "material": [\n' + body + '\n      ],'


def collect(t, frag_text, rows, cfg):
    """返回 (edits, misses)；edits 为 [(start, end, new, label), ...]"""
    edits, misses = [], []

    def sub_once(pattern, new, label, flags=0, count=1, required=True):
        found = list(re.finditer(pattern, t, flags))
        if len(found) != count:
            misses.append(f"{label}: 命中 {len(found)} 次，期望 {count}")
            return
        for m in found:
            edits.append((m.start(), m.end(), new, label))

    # ① 正文三区块（新态优先，否则旧态）
    m = NEW_BLOCK_RE.search(t)
    tag = "① 正文区块(new)"
    if not m:
        m = OLD_BLOCK_RE.search(t)
        tag = "① 正文区块(old)"
    if not m:
        misses.append("① 正文区块: 新旧两种 pattern 都没命中")
    else:
        edits.append((m.start(), m.end(), frag_text, tag))

    if cfg.get("skip_seo"):
        return edits, misses

    n, p = len(rows), len({r["page"] for r in rows})

    # ② meta description ×3
    dm = re.search(r'<meta name="description" content="([^"]+)"', t)
    if not dm:
        misses.append("② meta description: 找不到原串")
    else:
        mats = " / ".join(
            dict.fromkeys(r["material"] for r in rows if r.get("material")))
        new_desc = (f"{cfg['display_en']} made to order: {n} models across {mats}. "
                    "Packed size and gross weight for every model. "
                    "OEM/ODM with your logo, colour and material spec. Request a quote.")
        sub_once(re.escape(dm.group(1)), new_desc, "② meta description", count=3)

    # ③ JSON-LD material 数组
    sub_once(r'      "material": \[\n(?:        "[^"]+",?\n)+      \],',
             build_material(rows), "③ JSON-LD material")

    # ④ offerCount
    om = re.search(r'"offerCount": (\d+)', t)
    if not om:
        misses.append("④ offerCount: 找不到")
    else:
        sub_once(r'"offerCount": \d+', f'"offerCount": {n}', "④ offerCount")

    # ⑤ ItemList 整块
    sub_once(r'      "@type": "ItemList",\n      "name": "[^"]+",\n'
             r'      "numberOfItems": \d+,\n      "itemListElement": \[\n.*?\n      \]\n    \}',
             build_itemlist(rows, cfg["display_en"]), "⑤ ItemList", flags=re.S)

    # ⑥ FAQ 型号数：英文（JSON-LD + 正文各一处）、中文一处
    em = re.search(r'Specification sheets and photos covering all \d+ models in this line', t)
    if not em:
        misses.append("⑥ FAQ EN: 找不到原串")
    else:
        new_en = cfg.get("faq_en_new", DEF_FAQ_EN).format(n=n, p=p)
        sub_once(re.escape(em.group(0)), new_en, "⑥ FAQ EN", count=2)
    zm = re.search(r'本线全部 \d+ 个型号的规格书与实拍图', t)
    if zm:
        sub_once(re.escape(zm.group(0)),
                 cfg.get("faq_zh_new", DEF_FAQ_ZH).format(n=n, p=p), "⑥ FAQ ZH")
    else:
        misses.append("⑥ FAQ ZH: 找不到原串")

    # ⑦ hero eyebrow
    sub_once(r'<div class="pl-eyebrow"><span class="lang-en">[^<]*</span>'
             r'<span class="lang-zh">[^<]*</span></div>',
             '<div class="pl-eyebrow">'
             + f'<span class="lang-en">{cfg.get("eyebrow_en", DEF_EYEBROW_EN).format(n=n, p=p)}</span>'
             + f'<span class="lang-zh">{cfg.get("eyebrow_zh", DEF_EYEBROW_ZH).format(n=n, p=p)}</span>'
             + '</div>',
             "⑦ hero eyebrow")

    return edits, misses


OLD_PER_FAMILY = {
    "tower": [r"N[ILKWX][A-Z]?[0-9]{3}", r"FAS-grade white maple",
              r"Imported rubberwood", r"High-strength 316 steel",
              r"4 models", r"4 个型号"],
    "chair": [r"N[ILKWX][A-Z]?[0-9]{3}", r"FAS-grade white maple",
              r"Piano-[Ll]acquer", r"Thai 5A-grade rubberwood",
              r"3 models", r"3 个型号"],
    "cadillac": [r"N[ILKWX][A-Z]?[0-9]{3}", r"FAS-grade white maple",
                 r"Piano-[Ll]acquer", r"Thai 5A-grade rubberwood",
                 r"3 models", r"3 个型号"],
    "specialty": [r"N[ILKWX][A-Z]?[0-9]{3}", r"FAS-grade white maple",
                  r"White maple \+ plywood", r"2 models", r"2 个型号"],
}


def check(t, label, rows, cfg, family):
    problems = []
    for pat in OLD_PER_FAMILY.get(family, []):
        hit = len(re.findall(pat, t))
        if hit:
            problems.append(f"{label} 残留旧串 {pat!r} ×{hit}")
    void = {"img", "br", "hr", "input", "meta", "link", "source", "area", "col"}
    c = collections.Counter()
    for m in re.finditer(r"<(/?)([a-zA-Z][\w-]*)", t):
        tg = m.group(2).lower()
        if tg in void:
            continue
        c[tg] += -1 if m.group(1) else 1
    bad = {k: v for k, v in c.items() if v != 0}
    if bad:
        problems.append(f"{label} 标签不配平: {bad}")
    en, zh = t.count('class="lang-en"'), t.count('class="lang-zh"')
    if en != zh:
        problems.append(f"{label} 双语不配对 en={en} zh={zh}")
    exp_units = len({r["page"] for r in rows})
    if t.count('class="cat-unit"') != exp_units:
        problems.append(f"{label} cat-unit 应 {exp_units}，实 "
                        f"{t.count('class=\"cat-unit\"')}")
    if t.count('class="model-card"') != len(rows):
        problems.append(f"{label} model-card 应 {len(rows)}，实 "
                        f"{t.count('class=\"model-card\"')}")
    return problems


def run(family, write):
    cfg = CFG[family]
    page = ROOT / cfg["page"]
    frag = FRAG_DIR / f"block_{family}.html"
    if not frag.exists():
        print(f"✗ 片段不存在: {frag}")
        return 1

    t = page.read_text("utf-8")
    frag_text = frag.read_text("utf-8")
    rows = load_rows(cfg)

    print(f"\n{'='*74}\n### {family}  →  {cfg['page']}")
    print(f"    数据: {len(rows)} 台 / {len({r['page'] for r in rows})} 张画册页"
          f"  |  页面 {len(t):,} 字节  |  片段 {len(frag_text):,} 字节")

    edits, misses = collect(t, frag_text, rows, cfg)
    if misses:
        print("✗ 定位失败（未写盘）：")
        for m in misses:
            print(f"    · {m}")
        return 1

    ordered = sorted(edits, key=lambda x: x[0])
    for i in range(1, len(ordered)):
        if ordered[i][0] < ordered[i - 1][1]:
            print(f"✗ 区间重叠: {ordered[i-1][3]} 与 {ordered[i][3]}")
            return 1

    print(f"    改动点 {len(edits)} 处：")
    for s, e, new, label in ordered:
        print(f"      · {label:22s} @{s:>7}–{e:<7} ({e-s:>6} → {len(new):>6} 字节)")

    out = t
    for s, e, new, _ in sorted(edits, key=lambda x: x[0], reverse=True):
        out = out[:s] + new + out[e:]

    problems = check(out, "[改后]", rows, cfg, family)
    d = list(difflib.unified_diff(t.split("\n"), out.split("\n"), lineterm="", n=0))
    plus = sum(1 for l in d if l.startswith("+") and not l.startswith("+++"))
    minus = sum(1 for l in d if l.startswith("-") and not l.startswith("---"))
    print(f"    体格 {len(t):,} → {len(out):,} 字节 | 差量 +{plus} / −{minus} 行")
    print(f"    改后断言: {problems if problems else '全部通过 ✅'}")
    if problems:
        print("✗ 改后断言未通过，不写盘")
        return 1

    if not write:
        print("    ✓ dry-run 通过（未写盘）")
        return 0

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = BACKUP_DIR / f"{page.name}.bak_{stamp}"
    shutil.copy2(page, bak)
    page.write_text(out, "utf-8")
    again = page.read_text("utf-8")
    if again != out:
        print("✗ 落盘后复读不一致")
        return 1
    print(f"    ✓ 已备份 {bak.name}")
    print(f"    ✓ 已落盘 {page}（复读一致 {len(again):,} 字节）")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", choices=sorted(CFG), help="只处理该族；省略=全部")
    ap.add_argument("--write", action="store_true", help="真正落盘（默认 dry-run）")
    a = ap.parse_args()
    fams = [a.family] if a.family else sorted(CFG)
    rc = 0
    for f in fams:
        rc |= run(f, a.write)
    print()
    print("✓ 全部完成" if rc == 0 else "✗ 有族未通过，见上")
    return rc


if __name__ == "__main__":
    sys.exit(main())
