#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
板块首页 pilates/index.html 按 2026 画册重构

为什么改
--------
首页现在说「8 lines, 41 models」—— 41 是那套 NIC/NLH/NIM 内部编码的总数，
画册里一个都对不上。首页是整个板块的门面，门面的数字错了，下面六族改得
再对也白搭。

改成：**按画册 7 系列陈列**，每张卡给出该系列的台数与画册页数，
点进去就是族页（族页里贴画册原页 + 同数据的文字版）。

改动面（7 层，与族页同一套判据）
  ① hero lead（41 models across 8 lines → 7 series / 69 machines）
  ② hero 按钮（See the 8 lines → See the 7 series）
  ③ hero 统计四项（8 线 / 41 型号 / 12 木种 → 7 系列 / 69 台 / 5 种框架材质）
  ④ #lines 区块（h2 + 8 张旧族卡 → 7 张画册系列卡 + 可定制族的小链接）
  ⑤ meta description ×3
  ⑥ FAQ 里的「all 8 models in this line」（JSON-LD + 可见正文各一处）
  ⑦ FAQ 中文「本线全部 8 个型号的规格书与实拍图」

⚠️ 页面里还有别的 "8"（`No. 8 Haiguang Road`、`"position": 8`），
   所以**只做精确串替换，不用宽泛正则** —— 否则街道号会被改成 7。

用法：
  python apply_index_rebuild_20261001.py            # dry-run
  python apply_index_rebuild_20261001.py --write
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
PAGE = ROOT / "pilates" / "index.html"
DATA = ROOT / "i18n_build" / "data" / "catalog_pilates_models_v2.json"
BACKUP_DIR = pathlib.Path.home() / ".workbuddy" / "backups" / "fjsanfan"

# 画册 7 系列 → 线上落点。A/B/C 三条核心床线共用 reformer 页（画册里就是
# 同一章下的三条线），卡片上用 alias 行标明，免得采购商点三次以为是三页。
SERIES = [
    ("A.", "/pilates/pilates-reformer.html", "pilates-reformer.html",
     "AL — aluminium reformer line", "AL — 铝合金核心床线",
     "Machined aluminium frame, stainless-steel rails — the workhorse for volume orders and studio fit-outs.",
     "铝合金床架、不锈钢轨道 —— 走量与整馆配套的主力线。",
     "On the Reformer page", "在核心床页"),
    ("B.", "/pilates/pilates-reformer.html", "pilates-reformer.html",
     "Fold — foldable reformer line", "Fold — 折叠核心床线",
     "Folds flat for storage and apartment delivery; the line home studios and DTC sellers ask for first.",
     "可折叠平放，便于存放与入户配送；家用馆与 DTC 卖家最先问的一条线。",
     "On the Reformer page", "在核心床页"),
    ("C.", "/pilates/pilates-reformer.html", "pilates-reformer.html",
     "Wood — solid timber reformer line", "Wood — 实木核心床线",
     "Maple and oak frames with traditional joinery, for studios that want the timber look.",
     "枫木与橡木床架、传统榫接工艺，面向要木质质感的馆。",
     "On the Reformer page", "在核心床页"),
    ("D.", "/pilates/pilates-cadillac.html", "pilates-cadillac.html",
     "Cadillac — trapeze table", "Cadillac — 凯迪拉克床（吊架床）",
     "Full trapeze table with tower, mat and spring set — the widest exercise vocabulary of any apparatus.",
     "带塔架、垫面与全套弹簧的吊架床，动作谱系最宽的一台。",
     None, None),
    ("E.", "/pilates/pilates-ladder-barrel.html", "pilates-ladder-barrel.html",
     "Ladder Barrel", "梯桶",
     "Solid-wood arc with an adjustable ladder rung, for spinal extension, stretching and side-bending.",
     "实木弧面配可调梯级，用于脊柱伸展、拉伸与侧屈训练。",
     None, None),
    ("F.", "/pilates/pilates-wunda-chair.html", "pilates-wunda-chair.html",
     "Chair — wunda and stability chairs", "Chair — 稳踏椅 / 平衡椅",
     "Pedal-and-spring chairs in maple, oak and metal; small footprint, high repeat-order rate.",
     "枫木、橡木与金属踏板的稳踏椅；占地小，回购率高。",
     None, None),
    ("G.", "/pilates/pilates-specialty.html", "pilates-specialty.html",
     "Specialty — wall and two-way units", "Specialty — 壁挂与双向器械",
     "Wall-mounted and two-way units for studios that need the function without the floor space.",
     "壁挂与双向器械，适合要功能但腾不出地面的空间。",
     None, None),
]

EXTRA_CHIPS = [
    ("/pilates/pilates-reformer-tower.html", "Reformer Tower & 3-in-1", "半高架与三合一"),
    ("/pilates/pilates-spine-corrector.html", "Pilates Spine Corrector", "普拉提矫正器"),
    ("/pilates/pilates-studio-set.html", "Pilates Studio Set", "普拉提五套件"),
]

NEW_DESC = ("Pilates apparatus built to order: 69 machines across 7 series — "
            "reformer, Cadillac, chair, ladder barrel, specialty. "
            "OEM/ODM with your logo and material spec.")

NEW_LEAD_EN = ("Seven series, 69 machines in the 2026 catalogue — reformer, Cadillac, ladder "
               "barrel, chair and the specialty pieces, in solid timber, aluminium and steel. "
               "Spine correctors and studio sets we build to your drawing. Same factory as our "
               "yoga mat line, different bench.")
NEW_LEAD_ZH = ("2026 画册 7 个系列、69 台 —— 核心床、凯迪拉克床、梯桶、稳踏椅与特殊器械，"
               "材质覆盖实木、铝合金与钢。矫正器与整馆成套按图打样。与瑜伽垫同厂，但走另一条产线。")

NEW_FAQ_EN = "Specification sheets and photos covering every model in the catalogue"
NEW_FAQ_ZH = "画册里全部型号的规格书与实拍图"


def bn(en, zh):
    return f'<span class="lang-en">{en}</span><span class="lang-zh">{zh}</span>'


def series_stats():
    data = json.loads(DATA.read_text("utf-8"))
    out = {}
    for key, *_ in SERIES:
        rows = [r for r in data if str(r["series"]).startswith(key)]
        out[key] = (len(rows), len({r["page"] for r in rows}),
                    sorted({r["page"] for r in rows}),
                    sorted({r["model"] for r in rows}))
    return out


def build_lines_block(stats):
    cards = []
    for key, url, _, en, zh, den, dzh, aen, azh in SERIES:
        n, pages, plist, models = stats[key]
        first = plist[0]
        alt = (f"2026 catalogue page {first - 1:02d} — "
               + " and ".join(models[:2]))
        alias = (f'<div class="alias">{bn(aen, azh)}</div>' if aen else "")
        cards.append(
            f"""        <a class="pl-card" href="{url}">
          <div class="ph"><img src="../assets/img/catalog/p{first:02d}.webp" width="1576" height="1600" loading="lazy" alt="{alt}" /></div>
          <div class="bd"><h3>{bn(en, zh)}</h3>{alias}<div class="cnt">{bn(f'{n} models · {pages} catalogue pages', f'{n} 个型号 · {pages} 张画册页')}</div><p>{bn(den, dzh)}</p></div>
        </a>""")
    chips = "".join(
        f'<a href="{u}" class="pl-chip">{bn(e, z)}</a>' for u, e, z in EXTRA_CHIPS)
    return f"""  <section class="section" id="lines">
    <div class="container">
      <div class="section-head">
        <div class="eyebrow">{bn('2026 catalogue', '2026 画册')}</div>
        <h2>{bn('7 series, 69 machines', '7 个系列 · 69 台')}</h2>
        <p>{bn('Every machine on this site is a page in our 2026 catalogue. Open a series to see the catalogue page itself, with the same specification written out as text underneath.', '本站每一台都出自 2026 画册。点开一个系列，就能看到画册原页，以及同一份规格的文字版。')}</p>
      </div>
      <div class="pl-grid">
{chr(10).join(cards)}
      </div>
      <p class="pl-bar-note">{bn('Also in this section, built to order:', '同样按单制作，另见：')}</p>
      <div class="pl-chips">{chips}</div>
    </div>
  </section>
"""


def collect(t, stats):
    edits, misses = [], []

    def sub_once(pattern, new, label, flags=0, count=1):
        found = list(re.finditer(pattern, t, flags))
        if len(found) != count:
            misses.append(f"{label}: 命中 {len(found)} 次，期望 {count}")
            return
        for m in found:
            edits.append((m.start(), m.end(), new, label))

    # ④ #lines 区块（先做，它是最大的一块）
    i = t.find('<section class="section" id="lines">')
    if i < 0:
        misses.append("④ #lines 区块: 找不到")
    else:
        j = t.find("</section>", i) + len("</section>\n")
        edits.append((i, j, build_lines_block(stats), "④ #lines 区块"))

    # ① hero lead
    sub_once(
        r'<span class="lang-en">Reformer, Cadillac, Wunda chair, ladder barrel, spine corrector, '
        r'studio sets and the special pieces.*?</span><span class="lang-zh">核心床、凯迪拉克、稳踏椅、'
        r'梯桶、矫正器、五件套与特殊器械.*?</span>',
        bn(NEW_LEAD_EN, NEW_LEAD_ZH), "① hero lead", flags=re.S)

    # ② hero 按钮
    sub_once(r'<span class="lang-en">See the 8 lines</span><span class="lang-zh">看 8 条器械线</span>',
             bn("See the 7 series", "看 7 个系列"), "② hero 按钮")

    # ③ hero 统计三项（第四项 Sampling 7 days 不变）
    sub_once(r'<div class="num">8</div><div class="lab"><span class="lang-en">Equipment lines</span>'
             r'<span class="lang-zh">条器械线</span></div>',
             '<div class="num">7</div><div class="lab">'
             + bn("Catalogue series", "个画册系列") + '</div>', "③ stats 系列数")
    sub_once(r'<div class="num">41</div><div class="lab"><span class="lang-en">Models to choose from</span>'
             r'<span class="lang-zh">个可选型号</span></div>',
             '<div class="num">69</div><div class="lab">'
             + bn("Machines in the catalogue", "台在画册里") + '</div>', "③ stats 台数")
    sub_once(r'<div class="num">12</div><div class="lab"><span class="lang-en">Timber / frame options</span>'
             r'<span class="lang-zh">种木材或框架</span></div>',
             '<div class="num">5</div><div class="lab">'
             + bn("Frame materials", "种框架材质") + '</div>', "③ stats 材质数")

    # ⑤ meta description ×3
    dm = re.search(r'<meta name="description" content="([^"]+)"', t)
    if not dm:
        misses.append("⑤ meta description: 找不到原串")
    else:
        sub_once(re.escape(dm.group(1)), NEW_DESC, "⑤ meta description", count=3)

    # ⑥ FAQ EN（JSON-LD + 可见正文各一处）
    sub_once(r'Specification sheets and photos covering all 8 models in this line',
             NEW_FAQ_EN, "⑥ FAQ EN", count=2)

    # ⑦ FAQ ZH
    sub_once(r'本线全部 8 个型号的规格书与实拍图', NEW_FAQ_ZH, "⑦ FAQ ZH")

    # ⑧ CollectionPage 描述（旧文案仍在列 spine corrector / studio sets 为系列）
    sub_once(r'"description": "OEM/ODM Pilates apparatus manufacturing — reformer, Cadillac, '
             r'Wunda chair, ladder barrel, spine corrector, studio sets\."',
             '"description": "OEM/ODM Pilates apparatus manufacturing — 69 machines across 7 series '
             'in the 2026 catalogue: reformer, Cadillac, chair, ladder barrel and specialty pieces."',
             "⑧ CollectionPage 描述")

    return edits, misses


def check(t, stats):
    problems = []
    for pat in [r"41 models", r"8 lines", r"all 8 models", r"本线全部 8 个型号",
                r"Equipment lines", r"条器械线", r"12\b(?=[^0-9]*种木材)"]:
        n = len(re.findall(pat, t))
        if n:
            problems.append(f"残留旧串 {pat!r} ×{n}")
    # 街道号 / ItemList position 不能被误伤
    if "No. 8 Haiguang Road" not in t:
        problems.append("街道号 No. 8 Haiguang Road 被误改")
    if '"position": 8' not in t:
        problems.append("ItemList 的 position 8 被误改")
    void = {"img", "br", "hr", "input", "meta", "link", "source", "area", "col"}
    c = collections.Counter()
    for m in re.finditer(r"<(/?)([a-zA-Z][\w-]*)", t):
        tg = m.group(2).lower()
        if tg in void:
            continue
        c[tg] += -1 if m.group(1) else 1
    bad = {k: v for k, v in c.items() if v != 0}
    if bad:
        problems.append(f"标签不配平: {bad}")
    en, zh = t.count('class="lang-en"'), t.count('class="lang-zh"')
    if en != zh:
        problems.append(f"双语不配对 en={en} zh={zh}")
    exp = len(SERIES)
    if t.count('class="pl-card"') != exp:
        problems.append(f"pl-card 应 {exp}，实 {t.count('class=\"pl-card\"')}")
    for key, *_ in SERIES:
        n, pages, _, _ = stats[key]
        if f"{n} models · {pages} catalogue pages" not in t:
            problems.append(f"卡片统计缺: {key} {n} models · {pages} pages")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    t = PAGE.read_text("utf-8")
    stats = series_stats()
    print(f"### pilates/index.html  ({len(t):,} 字节)")
    print("    画册系列统计：")
    for key, url, *_ in SERIES:
        n, pages, plist, _ = stats[key]
        print(f"      {key} {n:>3} 台 / {pages} 页  p{plist[0]:02d}-p{plist[-1]:02d}  → {url}")

    edits, misses = collect(t, stats)
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
        print(f"      · {label:18s} @{s:>7}–{e:<7} ({e-s:>6} → {len(new):>6} 字节)")

    out = t
    for s, e, new, _ in sorted(edits, key=lambda x: x[0], reverse=True):
        out = out[:s] + new + out[e:]

    problems = check(out, stats)
    d = list(difflib.unified_diff(t.split("\n"), out.split("\n"), lineterm="", n=0))
    plus = sum(1 for l in d if l.startswith("+") and not l.startswith("+++"))
    minus = sum(1 for l in d if l.startswith("-") and not l.startswith("---"))
    print(f"    体格 {len(t):,} → {len(out):,} 字节 | 差量 +{plus} / −{minus} 行")
    print(f"    改后断言: {problems if problems else '全部通过 ✅'}")
    if problems:
        return 1
    if not a.write:
        print("    ✓ dry-run 通过（未写盘）")
        return 0

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(PAGE, BACKUP_DIR / f"{PAGE.name}.bak_{stamp}")
    PAGE.write_text(out, "utf-8")
    if PAGE.read_text("utf-8") != out:
        print("✗ 落盘后复读不一致")
        return 1
    print(f"    ✓ 已落盘（复读一致 {len(out):,} 字节）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
