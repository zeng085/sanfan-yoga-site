#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
族页「画册重构」区块生成器（数据驱动，可复用到全部 8 个族）

背景
----
线上普拉提板块原用一套 NIC/NLH/NIM 内部编码 + 旧材质口径，与 2026 画册
（7 系列 / 69 台 / 编码 AL·Fold·Wood·Chair·Ladder）完全对不上。
本生成器把画册数据渲染成族页内的三个区块：

  ① line-overview  三条线（或该族的线）概览卡
  ② catalogue-pages 画册原页图 + 该页型号卡（左图右卡，与梯桶页同构）
  ③ models-compared 规格表，按线分组

判据 / 约定（与项目铁律一致）
- 画册「文件序号 = 印刷页码 + 1」→ p33.webp 印的是 page 32。混用必错一页。
- 型号名是品牌型号，**不翻译**；材质等属性走双语 span。
- 缺失值一律输出 `—`，绝不编造。
- 只在 dry-run 通过（台数/页数/slug 唯一/图片存在）后才写盘。

用法
----
  python gen_family_catalog_block_20261001.py --family reformer --out <dir>
  python gen_family_catalog_block_20261001.py --family reformer --out <dir> --write
"""
import argparse
import json
import pathlib
import re
import sys
import collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "i18n_build" / "data" / "catalog_pilates_models_v2.json"
CATALOG_IMG_DIR = ROOT / "assets" / "img" / "catalog"

# ---------------------------------------------------------------- 族定义
# lines  : 该族收录的 series 前缀（画册章节号，非线上族名）
# filter : 可选正则，只收型号名命中的台（Tower 族用：塔架款散在 A/C 两线内）
# eyebrow: 区块顶部眉标；单线族不要写「3 lines」
# 台数/页数由数据算出并写进断言闸，**不写死**——画册若有增补，这里不用改
FAMILIES = {
    "reformer": {
        "lines": ["A.", "B.", "C."],
        "page_h2_en": "3 reformer lines, {n} models",
        "page_h2_zh": "3 条核心床线，{n} 个型号",
        "eyebrow_en": "3 lines, one factory",
        "eyebrow_zh": "三条线，同一个工厂",
        "hero_img": "pilates-reformer-1.webp",
        "hero_alt_en": "Pilates reformer — three production lines at the SANFAN factory",
        "hero_alt_zh": "普拉提核心床 —— 三梵工厂的三条产线",
    },
    "tower": {
        # 塔架款是 A/C 两线内带 Tower / 3-in-1 后缀的配置版，不是独立章节
        "lines": ["A.", "C."],
        "filter": r"tower|3\s*-?\s*in\s*-?\s*1",
        "page_h2_en": "{n} tower and 3-in-1 builds",
        "page_h2_zh": "{n} 款塔架与三合一配置",
        "eyebrow_en": "One bench, three builds",
        "eyebrow_zh": "同一张床，三种形态",
        "hero_img": "pilates-reformer-tower-1.webp",
        "hero_alt_en": "Reformer tower and 3-in-1 build at the SANFAN factory",
        "hero_alt_zh": "三梵工厂的半高架与三合一核心床",
    },
    "chair": {
        "lines": ["F."],
        "page_h2_en": "{n} chairs from one line",
        "page_h2_zh": "一条线，{n} 台稳踏椅",
        "eyebrow_en": "Chair line",
        "eyebrow_zh": "稳踏椅线",
        "hero_img": "pilates-wunda-chair-1.webp",
        "hero_alt_en": "Pilates wunda chair — nine builds from one production line",
        "hero_alt_zh": "普拉提稳踏椅 —— 同一条产线的九款",
    },
    "cadillac": {
        "lines": ["D."],
        "page_h2_en": "{n} Cadillac builds",
        "page_h2_zh": "{n} 款凯迪拉克床",
        "eyebrow_en": "Cadillac line",
        "eyebrow_zh": "凯迪拉克床线",
        "hero_img": "pilates-cadillac-1.webp",
        "hero_alt_en": "Pilates Cadillac — trapeze table builds at the SANFAN factory",
        "hero_alt_zh": "普拉提凯迪拉克床 —— 三梵工厂的吊架床",
    },
    "specialty": {
        "lines": ["G."],
        "page_h2_en": "{n} specialty units",
        "page_h2_zh": "{n} 款特殊器械",
        "eyebrow_en": "Specialty line",
        "eyebrow_zh": "特殊器械线",
        "hero_img": "pilates-specialty-1.webp",
        "hero_alt_en": "Pilates specialty — wall mounted and two-way units",
        "hero_alt_zh": "普拉提特殊器械 —— 壁挂与双向器械",
    },
}

LINE_META = {
    "A.": {
        "key": "al",
        "en": "AL — aluminium reformer line",
        "zh": "AL — 铝合金核心床线",
        "desc_en": "Machined aluminium frame, stainless-steel rails, the workhorse for volume orders and studio fit-outs.",
        "desc_zh": "铝合金床架，不锈钢轨道，走量与整馆配套的主力线。",
    },
    "B.": {
        "key": "fold",
        "en": "Fold — foldable reformer line",
        "zh": "Fold — 折叠核心床线",
        "desc_en": "Folds flat for storage and apartment delivery; the line most asked for by home studios and DTC sellers.",
        "desc_zh": "可折叠平放，便于存放与入户配送；家用馆和 DTC 卖家问得最多的一条线。",
    },
    "C.": {
        "key": "wood",
        "en": "Wood — solid timber reformer line",
        "zh": "Wood — 实木核心床线",
        "desc_en": "Maple and oak frames with traditional joinery, for boutique studios that want the timber look.",
        "desc_zh": "枫木与橡木床架、传统榫接工艺，面向要木质质感的精品馆。",
    },
    "D.": {
        "key": "cadillac",
        "en": "Cadillac — trapeze table",
        "zh": "Cadillac — 凯迪拉克床（吊架床）",
        "desc_en": "Full trapeze table with tower, mat and full spring set — the studio's centrepiece.",
        "desc_zh": "带塔架、垫面与全套弹簧的吊架床，通常是馆里的核心大件。",
    },
    "F.": {
        "key": "chair",
        "en": "Chair — wunda and stability chairs",
        "zh": "Chair — 稳踏椅 / 平衡椅",
        "desc_en": "Pedal-and-spring chairs in maple, oak and metal; small footprint, high repeat-order rate.",
        "desc_zh": "枫木、橡木与金属踏板的稳踏椅；占地小，回购率高。",
    },
    "G.": {
        "key": "specialty",
        "en": "Specialty — wall and two-way units",
        "zh": "Specialty — 壁挂与双向器械",
        "desc_en": "Wall-mounted and two-way units for studios that need the function without the floor space.",
        "desc_zh": "壁挂与双向器械，适合要功能但腾不出地面的空间。",
    },
}

MAT_ZH = {
    "Aluminum": "铝合金",
    "Carbon steel": "碳钢",
    "Metal": "金属",
    "Maple": "枫木",
    "Oak": "橡木",
    "Stainless steel": "不锈钢",
}

# ---------------------------------------------------------------- 工具


def esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def slugify(model: str) -> str:
    s = model.strip().lower()
    s = s.replace("×", "x")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def fmt_packing(v):
    """'2300*710*450' -> '2300 × 710 × 450 mm'；空 -> '—'"""
    if not v:
        return "—"
    s = str(v).strip()
    if not s or s in ("—", "-"):
        return "—"
    s = s.replace("*", "×").replace(" x ", " × ").replace("x", "×")
    s = re.sub(r"\s*×\s*", " × ", s)
    s = re.sub(r"\s+", " ", s).strip()
    # 已是 mm 结尾就不重复加
    if not re.search(r"mm\s*$", s, re.I):
        s = re.sub(r"^(\d)", r"\1", s)
        s = f"{s} mm"
    return s


def fmt_weight(v):
    if v in (None, "", "—", "-"):
        return "—"
    s = str(v).strip()
    if re.search(r"kg", s, re.I):
        return s
    try:
        f = float(s)
        return f"{f:g} kg"
    except ValueError:
        return s


def mat_pair(v):
    if not v:
        return None
    s = str(v).strip()
    zh = MAT_ZH.get(s)
    return (s, zh) if zh else (s, None)


def bn(en, zh):
    """双语 span，与全站结构一致"""
    return f'<span class="lang-en">{esc(en)}</span><span class="lang-zh">{esc(zh)}</span>'


# ---------------------------------------------------------------- 渲染

def render_model_card(r, printed, idx, total):
    mid = slugify(r["model"])
    mat = mat_pair(r.get("material"))
    rows = []
    if mat:
        en, zh = mat
        rows.append(
            "              <dt>" + bn("Material", "材质") + "</dt>"
            "<dd>" + bn(en, zh) + "</dd>"
        )
    rows.append(
        "              <dt>" + bn("Packing size", "包装尺寸") + "</dt>"
        f"<dd>{esc(fmt_packing(r.get('packing_a')))}</dd>"
    )
    if r.get("packing_b"):
        rows.append(
            "              <dt>" + bn("Packing size B", "包装尺寸 B") + "</dt>"
            f"<dd>{esc(fmt_packing(r.get('packing_b')))}</dd>"
        )
    rows.append(
        "              <dt>" + bn("Gross weight", "毛重") + "</dt>"
        f"<dd>{esc(fmt_weight(r.get('weight')))}</dd>"
    )
    dl = "\n".join(rows)
    return f"""          <article class="model-card" id="{mid}">
            <h3>{esc(r['model'])}</h3>
            <p class="model-card-sub">{bn(f'Catalogue p{printed:02d} · model {idx} of {total}', f'画册第 {printed:02d} 页 · 该页第 {idx} 台')}</p>
            <dl>
{dl}
            </dl>
            <a href="/contact.html" class="btn btn-ghost">{bn('Quote this model', '询价该型号')}</a>
          </article>"""


def render_cat_unit(page, rows, written_pages, page_total):
    printed = page - 1
    src = f"../assets/img/catalog/p{page:02d}.webp"
    names = " and ".join(r["model"] for r in rows)
    alt = (f"2026 catalogue page {printed:02d} — {names} "
           f"Pilates reformer, packed size and gross weight")
    # 该页涉及的画册线。双族页（如打印页 24 同页有 AL 4 CL Tower 与 Wood 4-KM）
    # 会产出一个以上标签；不要假设一页一线。
    # ⚠️ 顺序必须按 LINE_META 的规范线序（A→G）来定，**不能**跟着 rows 的遍历序
    #    —— rows 现在按页内序号排，多线页的标签顺序会随画册排版忽 AL 忽 WOOD 地漂移。
    present = {ln for r in rows for ln in LINE_META
               if str(r["series"]).startswith(ln)}
    page_line_keys = [LINE_META[ln]["key"] for ln in LINE_META if ln in present]
    tags = "".join(f'<span class="cat-line">{k.upper()}</span>' for k in page_line_keys)
    # ⚠️ 编号必须取画册自身的 seq_in_page，且分母取**该画册页实印台数**（全量口径），
    #    不能用族内筛选后的行号：tower 族在 p25 只留 2 台，而画册该页实印 3 台
    #    （AL 6-H / AL 6-H Tower / AL 6-H 3in 1）→ 用族内序号会产出
    #    「model 2 of 2 / model 3 of 2」这种自相矛盾的副标题。
    cards = "\n".join(
        render_model_card(r, printed, r["seq_in_page"], page_total[r["page"]])
        for r in rows
    )
    return f"""      <div class="cat-unit" id="cat-p{page:02d}">
        <figure class="cat-fig">
          <div class="cat-line-tags">{tags}</div>
          <img src="{src}" width="1576" height="1600" loading="lazy" decoding="async" alt="{esc(alt)}" />
          <figcaption>{bn(f'2026 catalogue · page {printed:02d}', f'2026 画册 · 第 {printed:02d} 页')}<span aria-hidden="true"> · </span><a href="{src}" target="_blank" rel="noopener" class="cat-zoom">{bn('view larger', '放大查看')}</a></figcaption>
        </figure>
        <div class="cat-models">
{cards}
        </div>
      </div>"""


def render_line_overview(lines, counts, pages):
    """单线族返回空串 —— 一张卡的「概览」没有信息量，只添高度。
    两块以上才值得做概览卡；此时函数自己带外层 div。"""
    if len(lines) < 2:
        return ""
    cards = []
    for ln in lines:
        m = LINE_META[ln]
        cards.append(f"""        <a class="line-card" href="#line-{m['key']}">
          <div class="line-card-n">{counts[ln]}</div>
          <h3>{bn(m['en'], m['zh'])}</h3>
          <p>{bn(m['desc_en'], m['desc_zh'])}</p>
          <span class="line-card-meta">{bn(f'{len(pages[ln])} catalogue pages', f'{len(pages[ln])} 张画册页')} · {bn('see table', '见下表')}</span>
        </a>""")
    return '      <div class="line-overview">\n' + "\n".join(cards) + "\n      </div>"


def render_table(rows_by_line, lines, multi=True):
    """multi=False（单线族）省略 Line 列与分组行 —— 整列同一个值纯占宽，
    分组行也只是重复页面标题。6 列 → 5 列，colspan 随之变。"""
    col = 6 if multi else 5
    cols = ["<th>" + bn("Model", "型号") + "</th>"]
    if multi:
        cols.append("<th>" + bn("Line", "产品线") + "</th>")
    cols += [
        "<th>" + bn("Material", "材质") + "</th>",
        "<th>" + bn("Packing size A", "包装尺寸 A") + "</th>",
        "<th>" + bn("Packing size B", "包装尺寸 B") + "</th>",
        "<th>" + bn("Gross weight", "毛重") + "</th>",
    ]
    head = ("        <thead>\n          <tr>\n            "
            + "\n            ".join(cols)
            + "\n          </tr>\n        </thead>")
    body = []
    for ln in lines:
        m = LINE_META[ln]
        n = len(rows_by_line[ln])
        if multi:
            body.append(
                f'          <tr class="line-row" id="line-{m["key"]}"><td colspan="{col}">'
                + bn(m["en"], m["zh"])
                + f' — {n}<span class="lang-en"> models</span><span class="lang-zh"> 个型号</span>'
                + "</td></tr>"
            )
        code = "AL" if m["key"] == "al" else m["key"].capitalize()
        # ⚠️ 按画册**自身的页内序号**排，不能按型号名字典序 —— 否则表格顺序
        #    与画册原页上下顺序相反（实测 p31：画册上 metal 在上、classics 在下，
        #    字典序却把 classics 排前面）
        for r in sorted(rows_by_line[ln], key=lambda x: (x["page"], x["seq_in_page"])):
            mat = mat_pair(r.get("material"))
            mat_cell = bn(mat[0], mat[1]) if mat else "—"
            tds = [f'<td class="model">{esc(r["model"])}</td>']
            if multi:
                tds.append(f"<td>{esc(code)}</td>")
            tds += [
                f"<td>{mat_cell}</td>",
                f'<td>{esc(fmt_packing(r.get("packing_a")))}</td>',
                f'<td>{esc(fmt_packing(r.get("packing_b")))}</td>',
                f'<td>{esc(fmt_weight(r.get("weight")))}</td>',
            ]
            body.append("          <tr>" + "".join(tds) + "</tr>")
    tbl_cls = "pl-spec" if multi else "pl-spec pl-spec-5"
    return (f"      <div class=\"pl-spec-wrap\">\n      <table class=\"{tbl_cls}\">\n"
            + head + "\n        <tbody>\n" + "\n".join(body)
            + "\n        </tbody>\n      </table>\n      </div>")


# ---------------------------------------------------------------- 主流程

def build(family, outdir):
    fam = FAMILIES[family]
    data = json.loads(DATA.read_text("utf-8"))
    rows = [r for r in data if r["series"].startswith(tuple(fam["lines"]))]
    # Tower 族：塔架款散在 A/C 两线内，按型号名筛（画册无独立章节号）
    if fam.get("filter"):
        _f = re.compile(fam["filter"], re.I)
        rows = [r for r in rows if _f.search(str(r["model"]))]
    # ⚠️ 必须按画册自身的页内序号排，不能按型号名字典序 —— 否则卡片副标题
    #    「Catalogue pNN · model i of j」的 i 会与画册实际印的顺序不符。
    #    实测（修正前）：80 张卡片里 29 张印错，买家按序号翻画册会翻到另一台。
    rows.sort(key=lambda r: (r["page"], r["seq_in_page"]))
    # 画册每页实印台数（**全量 69 台口径**，不受族筛选影响）→ 卡片分母用这个
    page_total = collections.Counter(r["page"] for r in data)

    lines = fam["lines"]

    def line_of(series):
        for ln in lines:
            if str(series).startswith(ln):
                return ln
        return None

    counts = collections.Counter(line_of(r["series"]) for r in rows)
    rows_by_line = {ln: [r for r in rows if line_of(r["series"]) == ln] for ln in lines}
    pages = {ln: sorted({r["page"] for r in rows_by_line[ln]}) for ln in lines}
    by_page = collections.OrderedDict()
    for r in rows:
        by_page.setdefault(r["page"], []).append(r)

    # ---- 断言闸（dry-run 判据）
    errs = []
    slugs = [slugify(r["model"]) for r in rows]
    dup = [s for s, c in collections.Counter(slugs).items() if c > 1]
    if dup:
        errs.append(f"slug 重复: {dup}")
    missing_img = [p for p in by_page if not (CATALOG_IMG_DIR / f"p{p:02d}.webp").exists()]
    if missing_img:
        errs.append(f"画册图缺失: {missing_img}")
    if sum(counts.values()) != len(rows):
        errs.append("线台数合计不符")
    no_pack = [r["model"] for r in rows if not r.get("packing_a")]
    if no_pack:
        errs.append(f"缺 packing_a: {no_pack}")
    zero = [ln for ln in lines if counts[ln] == 0]
    if zero:
        errs.append(f"线台数为 0（series 前缀匹配失败）: {zero}")
    if sum(counts.values()) != sum(len(v) for v in rows_by_line.values()):
        errs.append("counts 与 rows_by_line 不一致")
    in_table = sum(len(v) for v in rows_by_line.values())
    if in_table != len(rows):
        errs.append(f"入表台数 {in_table} ≠ 总台数 {len(rows)}")
    pages_in_units = len(by_page)
    if pages_in_units == 0:
        errs.append("画册页区块为空")
    # 页内序号必须在 1..该页实印台数 之间，且同页不得重复
    seq_out = [f"p{r['page']}:{r['model']}(seq={r['seq_in_page']})"
               for r in rows
               if not (1 <= r["seq_in_page"] <= page_total[r["page"]])]
    if seq_out:
        errs.append(f"seq_in_page 越界: {seq_out}")
    seq_dup = [k for k, c in collections.Counter(
        (r["page"], r["seq_in_page"]) for r in rows).items() if c > 1]
    if seq_dup:
        errs.append(f"同页序号重复: {seq_dup}")
    # 族内筛选可能让某页只露出部分型号 —— 分母仍取全量，此处只做提示
    partial = [p for p, rs in by_page.items() if len(rs) != page_total[p]]

    frag = []
    frag.append("""  <section class="section" id="catalog">
    <div class="container">
      <div class="pl-block">
        <div class="im"><img src="../assets/img/{heroimg}" width="900" height="675" alt="{heroalt}" /></div>
        <div>
          <div class="eyebrow">{eyebrow}</div>
          <h2>{h2}</h2>
          <p>{intro}</p>
          <div>{tags}</div>
        </div>
      </div>

{overview}
    </div>
  </section>


  <section class="section pl-soft" id="catalogue-pages">
    <div class="container">
      <div class="section-head">
        <div class="eyebrow">{ceyebrow}</div>
        <h2>{ch2}</h2>
        <p>{cintro}</p>
      </div>

{units}
    </div>
  </section>

  <section class="section" id="models-compared">
    <div class="container">
      <div class="section-head">
        <div class="eyebrow">{seyebrow}</div>
        <h2>{sh2}</h2>
        <p>{sintro}</p>
      </div>
{table}
      <p class="pl-spec-cap">{cap}</p>
    </div>
  </section>
""".format(
        tags="".join(
            f'<span class="pl-tag">{bn(m["key"].upper() if m["key"] == "al" else m["key"].capitalize(), m["key"].upper() if m["key"] == "al" else m["key"].capitalize())}</span>'
            for m in (LINE_META[ln] for ln in lines)
        ),
        heroimg=fam["hero_img"],
        heroalt=esc(fam["hero_alt_en"]),
        eyebrow=bn(fam["eyebrow_en"], fam["eyebrow_zh"]),
        h2=bn(fam["page_h2_en"].format(n=len(rows)), fam["page_h2_zh"].format(n=len(rows))),
        intro=bn(
            "Every machine below is in our 2026 catalogue. Pick the model — we quote that exact code.",
            "下面每台都出自 2026 画册。选中型号 —— 我们按该编号报价。",
        ),
        overview=render_line_overview(lines, counts, pages),
        ceyebrow=bn("2026 catalogue", "2026 画册"),
        ch2=bn(f"{len(by_page)} catalogue pages, {len(rows)} models",
               f"{len(by_page)} 张画册页，{len(rows)} 个型号"),
        cintro=bn(
            "Each image is a catalogue page exactly as printed. The specification burned into the picture is repeated as text underneath — so it can be searched, translated and pasted straight into a purchase order.",
            "下面每张图都是画册原页。印在图上的规格，我们在下方以文字重写一遍 —— 便于搜索、翻译，也可直接复制进采购单。",
        ),
        units="\n".join(render_cat_unit(p, rs, by_page, page_total)
                        for p, rs in by_page.items()),
        seyebrow=bn("Specifications", "规格对比"),
        sh2=bn(f"{len(rows)} models, compared", f"{len(rows)} 个型号对比"),
        sintro=bn(
            "Grouped by line, in catalogue order. Dashes mean the catalogue does not print that figure — we confirm per order.",
            "按产品线分组，依画册顺序。空白即画册上未印该数据 —— 按单确认。",
        ),
        cap=bn(
            "All models can be customised on material, upholstery colour, spring source and packaging. A dash means the 2026 catalogue does not print that figure — we confirm it per order.",
            "全部型号均可定制材质、皮革颜色、弹簧来源与包装。空白即画册未印该数据，按单确认。",
        ),
        table=render_table(rows_by_line, lines, multi=len(lines) > 1),
    ))

    frag_text = "".join(frag)
    outdir.mkdir(parents=True, exist_ok=True)
    fragfile = outdir / f"block_{family}.html"
    report = {
        "family": family,
        "models": len(rows),
        "pages": len(by_page),
        "by_line": {ln: counts[ln] for ln in lines},
        "pages_by_line": {ln: pages[ln] for ln in lines},
        "missing_images": missing_img,
        "partial_pages": {str(p): f"{len(by_page[p])}/{page_total[p]}" for p in partial},
        "missing_weight": [r["model"] for r in rows if not r.get("weight")],
        "missing_material": [r["model"] for r in rows if not r.get("material")],
        "slug_dupes": dup,
        "errors": errs,
        "bytes": len(frag_text.encode("utf-8")),
    }
    (outdir / f"report_{family}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), "utf-8")

    print(f"族: {family}")
    print(f"  型号 {len(rows)} 台 / 画册页 {len(by_page)} 张")
    for ln in lines:
        print(f"    {LINE_META[ln]['en']:38s} {counts[ln]:>3} 台 / {len(pages[ln])} 页")
    print(f"  缺毛重 {len(report['missing_weight'])} 台 | 缺材质 {len(report['missing_material'])} 台")
    print(f"  缺图 {len(missing_img)} | slug 重复 {len(dup)}")
    print(f"  错误: {errs if errs else '无'}")
    print(f"  区块字节: {len(frag_text.encode('utf-8'))}")
    if errs:
        print("✗ dry-run 未通过，不写盘")
        return 1
    fragfile.write_text(frag_text, "utf-8")
    print(f"✓ 片段已写出（未落盘到站点）: {fragfile}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", required=True, choices=sorted(FAMILIES))
    ap.add_argument("--out", required=True)
    ap.add_argument("--write", action="store_true", help="（预留）写回到站点页")
    a = ap.parse_args()
    return build(a.family, pathlib.Path(a.out).resolve())


if __name__ == "__main__":
    sys.exit(main())
