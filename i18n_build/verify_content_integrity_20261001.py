#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""普拉提板块重构 —— 内容级完整性/专业性验收（换角度第二轮，v2）

与第一轮的区别：第一轮查「元素数量 + 渲染是否报错」（浏览器探针），
本轮查 **内容对不对** 与 **上线后会不会 404**。

五个角度：
  ① 大小写敏感性：Mac 不区分大小写、Vercel(Linux) 区分 →
     本地能开、线上 404 是本项目上线前最隐蔽的坑。逐段比对磁盘真实文件名。
  ② 字段级对账：把 HTML 渲染出的每台型号 材质/包装/毛重 与 OCR 源 JSON 逐条比。
     ⚠️ 第一轮只数了 model-card 个数（46 个），数量对 ≠ 数字对。
  ③ 页内序号：卡片副标题「Catalogue pNN · model i of j」的 i 必须等于画册
     自身的 seq_in_page，j 必须等于该画册页实印台数、且顺序随画册单调。
  ④ 跨页集合闭合：9 页型号并集必须恰好 = 69 台，无遗漏无重复。
  ⑤ 三份副本同步：同一台型号的数据在「规格表 / 型号卡片 / JSON-LD」各有一份，
     必须同集 —— 这是「同串同步」铁律在数据层的应用。

v2 修正（v1 把 4 类「脚本判据错」误报成缺陷）：
  - main.js 里 `href="' + ROOT + '..."` 这类 **JS 字符串拼接** 被当成路径 → 过滤
  - 源 weight 为 None 时页面渲染「—」是**对的**（caption 明确说 dash = 画册未印）
    → v1 期望值算成空串，凭空造出 13 条误报
  - ladder-barrel 的表格行是**多行写法**且 td 带 `class="size"` → 正则要容忍空白与属性
  - Tower 族的期望值必须**限定在 A/C 两线内**（Wall Tower 属 G 线 Specialty，
    画册 p40，归 specialty 页是对的）→ v1 用全站正则扫出 12 台，凭空多 1 条

用法：
    python3 i18n_build/verify_content_integrity_20261001.py
"""
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "i18n_build/data/catalog_pilates_models_v2.json"
PAGES = sorted((ROOT / "pilates").glob("*.html"))

FAMILY_LINES = {
    "pilates-reformer.html": ["A.", "B.", "C."],
    "pilates-wunda-chair.html": ["F."],
    "pilates-cadillac.html": ["D."],
    "pilates-ladder-barrel.html": ["E."],
    "pilates-specialty.html": ["G."],
}
TOWER_PAGE = "pilates-reformer-tower.html"
TOWER_LINES = ["A.", "C."]
TOWER_RE = re.compile(r"tower|3\s*-?\s*in\s*-?\s*1", re.I)

problems = []


def norm(s):
    """归一化：去空白、统一乘号与破折号、大小写不敏感。"""
    if s is None:
        return ""
    s = str(s).strip()
    s = s.replace("\u00d7", "x").replace("\u2715", "x").replace("*", "x")
    s = s.replace("\u2014", "-").replace("\u2013", "-").replace("\u2015", "-")
    return re.sub(r"\s+", "", s).lower()


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)


def en_of(s):
    m = re.search(r'<span class="lang-en">(.*?)</span>', s, re.S)
    return strip_tags(m.group(1)).strip() if m else strip_tags(s).strip()


DASH = "\u2014"  # —


# ────────────────────────────────────────────────────────────────
# 角度① 大小写敏感性
# ────────────────────────────────────────────────────────────────
ATTR_RE = re.compile(r'(?:src|href|srcset|data-src)\s*=\s*"([^"]+)"')
CSSURL_RE = re.compile(r'url\(\s*[\'"]?([^\'")]+)')
# JS 里拼出来的路径（' + ROOT + BASE + x.k + '.html）不是静态路径，跳过
JS_JUNK_RE = re.compile(r"[+'\"`$\\]|\\u|\bROOT\b|\bBASE\b|\bHref\b|原图")


def case_check(ref, base, origin):
    ref = ref.split("?")[0].split("#")[0].strip()
    if not ref or ref.startswith(("http://", "https://", "//", "mailto:", "tel:", "data:", "#")):
        return None
    if JS_JUNK_RE.search(ref):
        return None          # JS 拼接 / 模板串，不是磁盘路径
    if ref.startswith("/"):
        cur, parts = ROOT, ref.lstrip("/").split("/")
    else:
        cur, parts = base, ref.split("/")
    for seg in parts:
        if seg in ("", "."):
            continue
        if seg == "..":
            cur = cur.parent
            continue
        try:
            entries = os.listdir(cur)
        except OSError:
            return f"{origin}: 路径不可达 {ref}（在 {cur} 处断）"
        if seg not in entries:
            near = [e for e in entries if e.lower() == seg.lower()]
            if near:
                return f"{origin}: 大小写不符 {ref}  →  磁盘实为 {near[0]}"
            return f"{origin}: 文件不存在 {ref}"
        cur = cur / seg
    return None


print("=" * 78)
print("① 大小写敏感性审计（Mac 可过 / Vercel Linux 会 404）")
print("=" * 78)
refs_checked = 0
case_hits = []
for p in PAGES:
    t = p.read_text(encoding="utf-8")
    for ref in ATTR_RE.findall(t) + CSSURL_RE.findall(t):
        refs_checked += 1
        r = case_check(ref, p.parent, p.name)
        if r:
            case_hits.append(r)
for extra in [ROOT / "assets/css/styles.css", ROOT / "assets/js/main.js"]:
    t = extra.read_text(encoding="utf-8")
    for ref in CSSURL_RE.findall(t) + ATTR_RE.findall(t):
        refs_checked += 1
        r = case_check(ref, extra.parent, extra.name)
        if r:
            case_hits.append(r)
print(f"  受检静态引用 {refs_checked} 条（9 页 + styles.css + main.js）")
if case_hits:
    problems += case_hits
    for h in case_hits[:20]:
        print(f"  ✗ {h}")
else:
    print("  ✓ 全部路径大小写与磁盘完全一致")

# ────────────────────────────────────────────────────────────────
src = json.loads(SRC.read_text(encoding="utf-8"))
BY_MODEL = {norm(r["model"]): r for r in src}
PAGE_TOTAL = {}
for r in src:
    PAGE_TOTAL[r["page"]] = PAGE_TOTAL.get(r["page"], 0) + 1


def exp_cell(r, key):
    """源值 → 页面应显示的文本。None 一律显示破折号（画册未印，按单确认）。"""
    if key == "packing_a":
        return r.get("packing_a_pretty") or DASH
    if key == "packing_b":
        return r.get("packing_b_pretty") or DASH
    if key == "weight":
        return f"{r['weight']:g} kg" if r.get("weight") is not None else DASH
    if key == "material":
        return r.get("material") or DASH
    raise KeyError(key)


# ────────────────────────────────────────────────────────────────
# ② 三份副本 + 字段级对账   ③ 页内序号
# ────────────────────────────────────────────────────────────────
print()
print("=" * 78)
print("② 三份副本同步 + 字段级对账（表 / 卡片 / JSON-LD vs OCR 源）")
print("=" * 78)

TABLE_ROW_RE = re.compile(r'<tr>\s*<td class="model">(.*?)</td>(.*?)</tr>', re.S)
TD_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
CARD_RE = re.compile(r'<article class="model-card" id="([^"]+)">(.*?)</article>', re.S)
CARD_DL_RE = re.compile(r"<dt>(.*?)</dt>\s*<dd>(.*?)</dd>", re.S)
SUB_RE = re.compile(r"Catalogue p(\d+)\s*·\s*model (\d+) of (\d+)")

all_page_models = {}
card_count_total = tbl_count_total = 0
field_mismatch, copy_mismatch, seq_mismatch = [], [], []
ld_depths = []

for p in PAGES:
    t = p.read_text(encoding="utf-8")
    if p.name == "index.html":
        continue

    tbl = {}
    for m in TABLE_ROW_RE.finditer(t):
        name = norm(strip_tags(m.group(1)))
        tds = TD_RE.findall(m.group(2))
        if len(tds) < 4:
            problems.append(f"{p.name}: 表格行字段数异常 {name} 只有 {len(tds)} 个 td")
            continue
        mat, pa, pb, wt = tds[-4:]     # 单线族 5 列 / 多线族 6 列，后 4 列固定
        tbl[name] = {"material": en_of(mat), "packing_a": strip_tags(pa).strip(),
                     "packing_b": strip_tags(pb).strip(), "weight": strip_tags(wt).strip()}

    cards = {}
    for m in CARD_RE.finditer(t):
        cid, body = m.group(1), m.group(2)
        h = re.search(r"<h3>(.*?)</h3>", body, re.S)
        name = norm(en_of(h.group(1)))
        d = {en_of(dt).strip().lower(): en_of(dd).strip()
             for dt, dd in CARD_DL_RE.findall(body)}
        s = SUB_RE.search(body)
        cards[name] = {"id": cid, "fields": d,
                       "page": int(s.group(1)) if s else None,
                       "idx": int(s.group(2)) if s else None,
                       "of": int(s.group(3)) if s else None}
    card_count_total += len(cards)
    tbl_count_total += len(tbl)
    all_page_models[p.name] = set(cards)

    ld_names = []
    for b in re.findall(r'<script type="application/ld\+json">\n(.*?)\n[ \t]*</script>', t, re.S):
        try:
            dd = json.loads(b)
        except Exception as e:
            problems.append(f"{p.name}: JSON-LD 解析失败 {e}")
            continue
        for n in dd.get("@graph", [dd]):
            if n.get("@type") == "ItemList":
                els = n.get("itemListElement", [])
                ld_depths.append((p.name, len(els),
                                  sum(1 for e in els if isinstance(e.get("item"), dict))))
                for el in els:
                    nm = el.get("name") or (el.get("item") or {}).get("name")
                    if nm:
                        ld_names.append(norm(nm))
    ldset = set(ld_names)

    if set(tbl) != set(cards):
        copy_mismatch.append(
            f"{p.name}: 表与卡片型号集不一致 | 仅表 {sorted(set(tbl)-set(cards))[:4]} "
            f"| 仅卡片 {sorted(set(cards)-set(tbl))[:4]}")
    if ldset and ldset != set(cards):
        copy_mismatch.append(
            f"{p.name}: 卡片与 JSON-LD 型号集不一致 | 仅卡片 {sorted(set(cards)-ldset)[:4]} "
            f"| 仅 LD {sorted(ldset-set(cards))[:4]}")

    # --- 字段级对账（表 + 卡片 两份副本都要对）---
    for name, got in tbl.items():
        r = BY_MODEL.get(name)
        if not r:
            field_mismatch.append(f"{p.name}[表]: {name} 不在 OCR 源")
            continue
        for k, g in (("material", got["material"]), ("packing_a", got["packing_a"]),
                     ("packing_b", got["packing_b"]), ("weight", got["weight"])):
            e = exp_cell(r, k)
            if norm(e) != norm(g):
                field_mismatch.append(f"{p.name}[表]: {name} {k} 页面={g!r} 源={e!r}")
    for name, c in cards.items():
        r = BY_MODEL.get(name)
        if not r:
            field_mismatch.append(f"{p.name}[卡]: {name} 不在 OCR 源")
            continue
        e = exp_cell(r, "packing_a")
        g = c["fields"].get("packing size", "")
        if norm(e) != norm(g):
            field_mismatch.append(f"{p.name}[卡]: {name} packing_a 页面={g!r} 源={e!r}")
        if r.get("packing_b"):     # 源有 B 才输出 B 行
            e = exp_cell(r, "packing_b")
            g = c["fields"].get("packing size b", "")
            if norm(e) != norm(g):
                field_mismatch.append(f"{p.name}[卡]: {name} packing_b 页面={g!r} 源={e!r}")
        e = exp_cell(r, "weight")
        g = c["fields"].get("gross weight", "")
        if norm(e) != norm(g):
            field_mismatch.append(f"{p.name}[卡]: {name} weight 页面={g!r} 源={e!r}")
        if r.get("material"):
            e = exp_cell(r, "material")
            g = c["fields"].get("material", "")
            if norm(e) != norm(g):
                field_mismatch.append(f"{p.name}[卡]: {name} material 页面={g!r} 源={e!r}")

    # --- ③ 页内序号 ---
    for name, c in cards.items():
        r = BY_MODEL.get(name)
        if not r or c["idx"] is None:
            continue
        if c["idx"] != r["seq_in_page"]:
            seq_mismatch.append(
                f"{p.name}: {name}  印 model {c['idx']}  画册实为 {r['seq_in_page']}")
        if c["page"] != r["catalog_page"]:
            seq_mismatch.append(
                f"{p.name}: {name}  印 p{c['page']}  画册实为 p{r['catalog_page']}")
        if c["of"] != PAGE_TOTAL[r["page"]]:
            seq_mismatch.append(
                f"{p.name}: {name}  分母 of {c['of']}  该画册页实印 {PAGE_TOTAL[r['page']]} 台")

    n_ok = set(tbl) == set(cards) and (not ldset or ldset == set(cards)) \
        and not any(x.startswith(p.name) for x in seq_mismatch)
    print(f"  {p.name:34s} 表 {len(tbl):2d} / 卡 {len(cards):2d} / LD {len(ldset):2d}"
          f"  {'✓' if n_ok else '✗'}")

print(f"\n  表行 {tbl_count_total} / 卡片 {card_count_total}（9 页累计，含跨页共用）")
if copy_mismatch:
    problems += copy_mismatch
    print("  ✗ 副本不同步：")
    for h in copy_mismatch:
        print(f"     {h}")
else:
    print("  ✓ 三份副本（表 / 卡片 / JSON-LD）型号集完全同步")
if seq_mismatch:
    problems += seq_mismatch
    print(f"  ✗ 页内序号错 {len(seq_mismatch)} 处：")
    for h in seq_mismatch[:15]:
        print(f"     {h}")
else:
    print("  ✓ 全部卡片页内序号 / 画册页码 / 分母 与画册原页一致")
if field_mismatch:
    problems += field_mismatch
    print(f"  ✗ 字段级差异 {len(field_mismatch)} 处：")
    for h in field_mismatch[:20]:
        print(f"     {h}")
else:
    print("  ✓ 逐台型号的材质/包装/毛重 与 OCR 源完全一致")

# ────────────────────────────────────────────────────────────────
# ⑤ JSON-LD 深度一致性（全板块应同构）
# ────────────────────────────────────────────────────────────────
print()
print("=" * 78)
print("④ JSON-LD ItemList 深度一致性（同板块应同构）")
print("=" * 78)
depths = {d for _, _, d in ld_depths}
for fn, n, rich in ld_depths:
    print(f"  {fn:34s} {n:>3} 项，其中带内嵌 Product 的 {rich} 项")
if len(depths) > 1:
    problems.append(f"ItemList 深度不一致：出现 {sorted(depths)} 种（0=平 / N=富）")
    print("  ✗ 板块内 ItemList 深度不一致")
else:
    print(f"  ✓ 板块内 {len(ld_depths)} 个 ItemList 深度完全一致（{'平' if depths == {0} else '富'}）")

# ────────────────────────────────────────────────────────────────
# ④ 跨页集合闭合
# ────────────────────────────────────────────────────────────────
print()
print("=" * 78)
print("⑤ 跨页型号集合闭合（并集必须恰好 = 69 台）")
print("=" * 78)

union = set()
for s in all_page_models.values():
    union |= s
src_models = {norm(r["model"]) for r in src}
print(f"  9 页型号并集：{len(union)} 台   源数据：{len(src)} 台")
missing = sorted(src_models - union)
extra = sorted(union - src_models)
if missing:
    problems.append(f"有 {len(missing)} 台型号未出现在任何页面：{missing[:8]}")
    print(f"  ✗ 漏掉 {len(missing)} 台：{missing[:8]}")
else:
    print("  ✓ 69 台全部落到页面上，无遗漏")
if extra:
    problems.append(f"页面出现源数据没有的型号：{extra[:8]}")
    print(f"  ✗ 多出 {len(extra)} 台：{extra[:8]}")
else:
    print("  ✓ 页面未出现源数据之外的型号")

for fn, lines in FAMILY_LINES.items():
    exp = {norm(r["model"]) for r in src
           if any(r["series"].startswith(l) for l in lines)}
    got = all_page_models.get(fn, set())
    if exp != got:
        problems.append(f"{fn}: 应覆盖 {len(exp)} 台，实际 {len(got)} 台；"
                        f"缺{sorted(exp-got)[:4]} 多{sorted(got-exp)[:4]}")
        print(f"  ✗ {fn:34s} 期望 {len(exp):2d} 实际 {len(got):2d}")
    else:
        print(f"  ✓ {fn:34s} {len(got):2d} 台，与画册线完全一致")

# Tower：期望值必须限定在 A/C 两线内（Wall Tower 属 G 线，归 specialty 页是对的）
exp_tw = {norm(r["model"]) for r in src
          if any(r["series"].startswith(l) for l in TOWER_LINES)
          and TOWER_RE.search(str(r["model"]))}
tw = all_page_models.get(TOWER_PAGE, set())
rf = all_page_models.get("pilates-reformer.html", set())
if tw != exp_tw:
    problems.append(f"{TOWER_PAGE}: 期望 {len(exp_tw)} 台塔架款，实际 {len(tw)} 台")
    print(f"  ✗ {TOWER_PAGE:31s} 期望 {len(exp_tw):2d} 实际 {len(tw):2d}")
else:
    print(f"  ✓ {TOWER_PAGE:31s} {len(tw):2d} 台，与 A/C 线内型号名筛选结果一致")
if not tw <= rf:
    problems.append(f"tower 页有 {len(tw-rf)} 台不在 reformer 页内（应为子集）")
    print(f"  ✗ tower 不是 reformer 的子集，多出 {sorted(tw-rf)[:5]}")
else:
    print(f"  ✓ tower 的 {len(tw)} 台全部含于 reformer 页（预期重叠，不重复计入 69）")

g_line = {norm(r["model"]) for r in src if r["series"].startswith("G.")}
if "walltower" in g_line and norm("Wall Tower") in all_page_models.get("pilates-specialty.html", set()):
    print("  ✓ Wall Tower（G 线，画册 p40）落在 specialty 页 —— 带 tower 字样但非核心床塔架")

idx = (ROOT / "pilates/index.html").read_text(encoding="utf-8")
for claim in ("7 series", "69 machines"):
    if claim in idx:
        print(f"  ✓ 板块首页声称 “{claim}” 与实际相符")
    else:
        near = re.findall(r"\b(\d+)\s+(?:series|lines|machines|models)\b", idx)
        problems.append(f"板块首页未找到预期声明 {claim!r}；实际出现 {near}")
        print(f"  ✗ 板块首页未找到 “{claim}”，实际出现 {near}")
for stale in ("41 models", "8 lines", "8 series", "41 台", "8 条产线"):
    if stale in idx:
        problems.append(f"板块首页残留旧数字 {stale!r}")
        print(f"  ✗ 残留旧数字 {stale!r}")

# ────────────────────────────────────────────────────────────────
print()
print("=" * 78)
if problems:
    print(f"结论：发现 {len(problems)} 个问题 ✗")
    print("=" * 78)
    for h in problems:
        print(" -", h)
    sys.exit(1)
print("结论：五个角度全部通过 ✓")
print("=" * 78)
