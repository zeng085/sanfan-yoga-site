#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把画册里**不存在**的两族页改成诚实的「按图打样」页
  · pilates/pilates-spine-corrector.html
  · pilates/pilates-studio-set.html

为什么要改
----------
这两页现在各挂着 3 个型号（NIX104/NIK205/NIK305、NIW101/NIW201/NIW301），
但把 2026 画册 38 页 OCR 全搜过 —— **Spine Corrector 与 Studio Set 两个词
一次都没出现**。也就是说这 3 个型号是旧体系残留，工厂画册里并不存在，
继续挂在线上等于对采购商虚报产品线。

处理（上一轮已与用户确认）
  ① 保留 URL（页面已收录，改地址等于丢索引权重）
  ② 正文去掉虚构型号表，换成「按图打样」的真实流程与资料清单
  ③ SEO meta / JSON-LD 同步：material、offers、ItemList 全部撤掉
     —— 没有固定型号，就不该有型号清单和报价区间结构化数据

⚠️ JSON-LD 走「解析 → 改结构 → 重新序列化」，不手写逗号。
   手写删除中间节点极易漏逗号 → 整个 LD 解析失败 → 结构化数据全废。

用法：
  python apply_custom_pages_20261001.py            # dry-run
  python apply_custom_pages_20261001.py --write
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
BACKUP_DIR = pathlib.Path.home() / ".workbuddy" / "backups" / "fjsanfan"

PAGES = {
    "spine-corrector": {
        "page": "pilates/pilates-spine-corrector.html",
        "hero": "pilates-spine-corrector-1.webp",
        "name_en": "Pilates Spine Corrector",
        "eyebrow_en": "Made to order · no fixed range",
        "eyebrow_zh": "按单制作 · 无固定系列",
        "h2_en": "No standard range — built to your drawing",
        "h2_zh": "没有标准型号表 —— 按图打样",
        "intro_en": ("Our 2026 catalogue does not carry a fixed spine corrector range, "
                     "so we do not print model numbers on this page. What we have is the "
                     "bench, the timber stock and the joinery that build every other piece "
                     "in the range. Send a drawing, a photo or a physical sample — we build "
                     "to it, and quote that build."),
        "intro_zh": ("2026 画册里没有固定的矫正器系列，所以这一页我们不编型号。"
                     "我们有的是和站上其他器械同一条产线、同一批木料、同一套榫接工艺。"
                     "发图纸、照片或实物样件过来，我们按它打样，并按这一件报价。"),
        "desc_en": ("Pilates Spine Corrector built to your drawing. The 2026 catalogue has no "
                    "fixed range, so we quote per build — send a drawing, photo or sample. "
                    "OEM/ODM with your logo, colour and material spec. Request a quote."),
    },
    "studio-set": {
        "page": "pilates/pilates-studio-set.html",
        "hero": "pilates-studio-set-1.webp",
        "name_en": "Pilates Studio Set",
        "eyebrow_en": "Configured per studio",
        "eyebrow_zh": "按馆配置",
        "h2_en": "No standard set — a studio configured to your floor",
        "h2_zh": "没有标准套装 —— 按你的场地配",
        "intro_en": ("Our 2026 catalogue lists 69 machines across seven series, not bundles. "
                     "A studio set is whatever combination of them fits your floor plan, your "
                     "class timetable and your budget — reformers, cadillac, chairs, ladder "
                     "barrels and wall units from the same factory, on one order, in one "
                     "container. Tell us the room and we come back with the list."),
        "intro_zh": ("2026 画册列的是 7 个系列 69 台单机，不是打包套餐。"
                     "所谓成套，就是按你的场地面积、课程表和预算，从这些单机里挑组合 —— "
                     "核心床、凯迪拉克床、稳踏椅、梯桶、壁挂器械，同一个工厂、一张订单、一个柜。"
                     "告诉我们场馆条件，我们给你配一张清单。"),
        "desc_en": ("Pilates studio set configured to your floor plan: reformers, cadillac, "
                    "chairs, ladder barrels and wall units from one factory, on one order. "
                    "OEM/ODM with your logo and colour spec. Request a quote."),
    },
}

STEPS = [
    ("Send the shape", "发形状",
     "A drawing, a photo of the piece you want copied, or a physical sample.",
     "图纸、想照做的实物照片，或直接寄样件。"),
    ("Quote and spec sheet", "报价与规格书",
     "We confirm what is buildable, and return the price with a written spec sheet.",
     "我们先确认能不能做，连同书面规格书一起给报价。"),
    ("Sample", "打样",
     "A physical sample takes 7 working days, so you sign off geometry and finish first.",
     "实物样件 7 个工作日，先确认几何与表面处理再量产。"),
    ("Production", "量产",
     "Built on the same bench as the catalogue range, packed and labelled to your artwork.",
     "与画册机型同一条产线，按你的包装稿件装箱贴标。"),
]

CHECKLIST = [
    ("Shape", "形状", "drawing, photo or physical sample", "图纸 / 照片 / 实物样件"),
    ("Size", "尺寸", "length × width × height", "长 × 宽 × 高"),
    ("Timber and finish", "木种与表面", "species and finish you need", "需要的木种与表面处理"),
    ("Upholstery", "皮革", "colour and material", "颜色与材质"),
    ("Branding", "品牌", "logo artwork", "logo 稿件"),
    ("Packaging", "包装", "carton artwork and barcode", "外箱稿件与条码"),
]

OLD_BLOCK_RE = re.compile(
    r'  <section class="section">\n'
    r'    <div class="container">\n'
    r'      <div class="pl-block">\n'
    r'        <div class="im"><img src="\.\./assets/img/[^"]+"[^>]*/>'
    r'.*?<p class="pl-spec-cap">.*?</p>\n'
    r'    </div>\n'
    r'  </section>\n',
    re.S)


def bn(en, zh):
    return f'<span class="lang-en">{en}</span><span class="lang-zh">{zh}</span>'


def build_block(cfg, others):
    tags = "".join(
        f'<span class="pl-tag">{bn(e, z)}</span>' for e, z in [
            ("Built to drawing", "按图定制"),
            ("Sample in 7 days", "7 天打样"),
            ("Your logo", "你的 logo"),
            ("Your packaging", "你的包装"),
        ])
    chips = "".join(
        f'<a href="{u}" class="pl-chip">{bn(en, zh)}</a>'
        for u, en, zh in others)
    steps = "\n".join(
        f"""        <div class="line-card">
          <div class="line-card-n">{i}</div>
          <h3>{bn(e, z)}</h3>
          <p>{bn(de, dz)}</p>
        </div>""" for i, (e, z, de, dz) in enumerate(STEPS, 1))
    rows = "\n".join(
        "          <tr>"
        f"<td>{bn(a, b)}</td>"
        f"<td>{bn(c, d)}</td>"
        "</tr>" for a, b, c, d in CHECKLIST)

    return f"""  <section class="section" id="catalog">
    <div class="container">
      <div class="pl-block">
        <div class="im"><img src="../assets/img/{cfg['hero']}" width="900" height="675" alt="{cfg['name_en']} built to order at the SANFAN factory" /></div>
        <div>
          <div class="eyebrow">{bn(cfg['eyebrow_en'], cfg['eyebrow_zh'])}</div>
          <h2>{bn(cfg['h2_en'], cfg['h2_zh'])}</h2>
          <p>{bn(cfg['intro_en'], cfg['intro_zh'])}</p>
          <div>{tags}</div>
        </div>
      </div>
      <p class="pl-bar-note">{bn('Built to order alongside:', '同样按单制作的还有：')}</p>
      <div class="pl-chips">{chips}</div>
    </div>
  </section>

  <section class="section pl-soft" id="how-it-works">
    <div class="container">
      <div class="section-head">
        <div class="eyebrow">{bn('How a custom build works', '定制怎么走')}</div>
        <h2>{bn('Four steps from your drawing to your carton', '从你的图纸到你的包装箱，四步')}</h2>
        <p>{bn('No model number to pick, so the order starts with the shape. These four steps are the same whether it is one piece or a full studio.', '因为没有型号可选，订单从「形状」开始。无论一件还是一整馆，都走这四步。')}</p>
      </div>
      <div class="line-overview">
{steps}
      </div>
    </div>
  </section>

  <section class="section" id="what-we-need">
    <div class="container">
      <div class="section-head">
        <div class="eyebrow">{bn('What to send us', '需要你提供什么')}</div>
        <h2>{bn('Six things and we can quote', '这六项齐了就能报价')}</h2>
        <p>{bn('Send whatever you already have — a hand sketch is enough to start. We come back with what is missing.', '手上有多少发多少，手绘草图也够开工，缺什么我们再问。')}</p>
      </div>
      <div class="pl-spec-wrap">
      <table class="pl-spec pl-spec-3">
        <thead>
          <tr>
            <th>{bn('To confirm', '确认项')}</th>
            <th>{bn('What we need', '需要什么')}</th>
          </tr>
        </thead>
        <tbody>
{rows}
        </tbody>
      </table>
      </div>
      <p class="pl-spec-cap">{bn('Nothing here is fixed in advance — timber, size, upholstery, branding and packaging are all set by your spec, not ours.', '以上没有一项是提前固定的 —— 木种、尺寸、皮革、品牌与包装都按你的规格定，不按我们的。')}</p>
    </div>
  </section>
"""


def patch_jsonld(t, cfg, misses):
    # ⚠️ 闭标签前有 2 空格缩进（'}\n  </script>'），正则必须容忍 ——
    #    写死 '\n</script>' 会一路匹配到**下一个** LD 块的闭标签，
    #    把两个 JSON 拼成一块 → "Extra data" 解析失败。
    m = re.search(r'(<script type="application/ld\+json">\n)(.*?)(\n[ \t]*</script>)', t, re.S)
    if not m:
        misses.append("JSON-LD: 找不到 @graph 块")
        return None
    d = json.loads(m.group(2))
    graph = d.get("@graph", [])
    before = [n.get("@type") for n in graph]
    dropped = []
    keep = []
    for n in graph:
        tp = n.get("@type")
        if tp == "ItemList":
            dropped.append("ItemList（型号清单：画册无此族，已撤）")
            continue
        if tp == "Product":
            for f in ("material", "offers"):
                if f in n:
                    n.pop(f)
                    dropped.append(f"Product.{f}")
        keep.append(n)
    d["@graph"] = keep
    body = json.dumps(d, ensure_ascii=False, indent=2)
    return m.start(1), m.end(3), m.group(1) + body + m.group(3), before, dropped


def run(key, write):
    cfg = PAGES[key]
    page = ROOT / cfg["page"]
    t = page.read_text("utf-8")
    edits, misses = [], []

    print(f"\n{'='*74}\n### {key}  →  {cfg['page']}")
    print(f"    页面 {len(t):,} 字节")

    # ① 正文区块
    mb = OLD_BLOCK_RE.search(t)
    if not mb:
        misses.append("① 正文区块: pattern 未命中")
    else:
        others = [("/pilates/pilates-reformer.html", "Pilates Reformer", "核心床"),
                  ("/pilates/pilates-cadillac.html", "Pilates Cadillac", "凯迪拉克床"),
                  ("/pilates/pilates-wunda-chair.html", "Pilates Wunda Chair", "稳踏椅"),
                  ("/pilates/pilates-ladder-barrel.html", "Pilates Ladder Barrel", "梯桶"),
                  ("/pilates/pilates-specialty.html", "Pilates Specialty", "特殊器械")]
        edits.append((mb.start(), mb.end(), build_block(cfg, others), "① 正文区块"))

    # ② meta description ×3
    dm = re.search(r'<meta name="description" content="([^"]+)"', t)
    if not dm:
        misses.append("② meta description: 找不到原串")
    else:
        found = list(re.finditer(re.escape(dm.group(1)), t))
        if len(found) != 3:
            misses.append(f"② meta description: 命中 {len(found)} 次，期望 3")
        for m in found:
            edits.append((m.start(), m.end(), cfg["desc_en"], "② meta description"))

    # ③ JSON-LD（整块重序列化）
    j = patch_jsonld(t, cfg, misses)
    if j:
        s, e, new, before, dropped = j
        edits.append((s, e, new, "③ JSON-LD 整块"))
        print(f"    LD 改前节点: {before}")
        print(f"    LD 撤下: {dropped}")

    # ④ hero eyebrow
    em = re.search(r'<div class="pl-eyebrow"><span class="lang-en">[^<]*</span>'
                   r'<span class="lang-zh">[^<]*</span></div>', t)
    if not em:
        misses.append("④ hero eyebrow: 找不到")
    else:
        edits.append((em.start(), em.end(),
                      '<div class="pl-eyebrow">'
                      + bn(cfg["eyebrow_en"], cfg["eyebrow_zh"]) + '</div>',
                      "④ hero eyebrow"))

    # ⑤ FAQ 里的型号数（JSON-LD 英文 + 可见正文英文各一处、中文一处）
    #    撤掉型号表与 ItemList 后，这两句是最后残留的「3 models」来源。
    NEW_FAQ_EN = "Drawings, spec sheets and photos from previous builds in this range"
    NEW_FAQ_ZH = "这一范围以往做过的图纸、规格书与实拍图"
    fq = re.search(r'Specification sheets and photos covering all \d+ models in this line', t)
    if not fq:
        misses.append("⑤ FAQ EN: 找不到原串")
    else:
        for m in re.finditer(re.escape(fq.group(0)), t):
            edits.append((m.start(), m.end(), NEW_FAQ_EN, "⑤ FAQ EN"))
    fz = re.search(r'本线全部 \d+ 个型号的规格书与实拍图', t)
    if fz:
        edits.append((fz.start(), fz.end(), NEW_FAQ_ZH, "⑤ FAQ ZH"))
    else:
        misses.append("⑤ FAQ ZH: 找不到原串")

    if misses:
        print("✗ 定位失败（未写盘）：")
        for x in misses:
            print(f"    · {x}")
        return 1

    ordered = sorted(edits, key=lambda x: x[0])
    for i in range(1, len(ordered)):
        if ordered[i][0] < ordered[i - 1][1]:
            print(f"✗ 区间重叠: {ordered[i-1][3]} 与 {ordered[i][3]}")
            return 1
    print(f"    改动点 {len(edits)} 处：" + "、".join(l for _, _, _, l in ordered))

    out = t
    for s, e, new, _ in sorted(edits, key=lambda x: x[0], reverse=True):
        out = out[:s] + new + out[e:]

    problems = []
    for pat in [r"N[ILKWX][A-Z]?[0-9]{3}", r"FAS-grade white maple",
                r"Piano-[Ll]acquer", r"Thai 5A-grade rubberwood",
                r"Domestic rubberwood", r"White maple \+ plywood", r"3 models", r"3 个型号"]:
        n = len(re.findall(pat, out))
        if n:
            problems.append(f"残留旧串 {pat!r} ×{n}")
    void = {"img", "br", "hr", "input", "meta", "link", "source", "area", "col"}
    c = collections.Counter()
    for m in re.finditer(r"<(/?)([a-zA-Z][\w-]*)", out):
        tg = m.group(2).lower()
        if tg in void:
            continue
        c[tg] += -1 if m.group(1) else 1
    bad = {k: v for k, v in c.items() if v != 0}
    if bad:
        problems.append(f"标签不配平: {bad}")
    en, zh = out.count('class="lang-en"'), out.count('class="lang-zh"')
    if en != zh:
        problems.append(f"双语不配对 en={en} zh={zh}")
    jm = re.search(r'<script type="application/ld\+json">\n(.*?)\n[ \t]*</script>', out, re.S)
    try:
        dd = json.loads(jm.group(1))
        types = [n.get("@type") for n in dd.get("@graph", [])]
        if "ItemList" in types:
            problems.append("JSON-LD 仍含 ItemList")
        print(f"    LD 改后节点: {types}（解析通过 ✅）")
    except Exception as ex:
        problems.append(f"JSON-LD 解析失败: {ex}")

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
    shutil.copy2(page, BACKUP_DIR / f"{page.name}.bak_{stamp}")
    page.write_text(out, "utf-8")
    if page.read_text("utf-8") != out:
        print("✗ 落盘后复读不一致")
        return 1
    print(f"    ✓ 已落盘（复读一致 {len(out):,} 字节）")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", choices=sorted(PAGES))
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    keys = [a.page] if a.page else sorted(PAGES)
    rc = 0
    for k in keys:
        rc |= run(k, a.write)
    print("\n✓ 全部完成" if rc == 0 else "\n✗ 有页未通过")
    return rc


if __name__ == "__main__":
    sys.exit(main())
