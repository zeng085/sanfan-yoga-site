# -*- coding: utf-8 -*-
"""
117 个产品页 → 8 个分类的映射表。

规则：一个产品只归一类，先按「手工例外表」，再按「英文站分类 → 大类」规则，
最后按 slug 关键词兜底。改动产品后重跑本脚本即可重新归类。

    python3 i18n_build/category_map.py          # 打印归类结果与覆盖校验
"""
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- 分类定义
# key: 分类 slug / en: 英文标题 / zh: 中文标题
# desc: 分类页导语文案 / kw: 副标题关键词（材质、工艺）
CATS = [
    {
        "key": "tpe-yoga-mats",
        "en": "TPE Yoga Mats",
        "zh": "TPE 瑜伽垫",
        "kw_en": "Eco TPE · Single & Double Layer · 61–90 cm",
        "kw_zh": "环保 TPE · 单层/双层 · 61–90 cm",
        "desc_en": "Closed-cell TPE foam — the workhorse of any yoga mat range. Light, recyclable, "
                   "odor-free and available in single or double-layer constructions with widths from "
                   "61 to 90 cm and 4–12 mm thickness. Full OEM: colour, size, embossed logo, "
                   "printed carry strap and retail packaging.",
        "desc_zh": "闭孔 TPE 发泡材质，瑜伽垫品类的主力款。轻量化、可回收、无异味，"
                   "可选单层或双层结构，宽度 61–90 cm、厚度 4–12 mm。"
                   "支持颜色、尺寸、压印 Logo、印花背带与零售包装全套定制。",
        "h1_en": "TPE Yoga Mats",
        "h1_zh": "TPE 瑜伽垫",
    },
    {
        "key": "pu-rubber-yoga-mats",
        "en": "PU & Rubber Yoga Mats",
        "zh": "PU 橡胶瑜伽垫",
        "kw_en": "PU Top · Natural Rubber Base · Hot Yoga",
        "kw_zh": "PU 面层 · 天然橡胶底 · 高温瑜伽",
        "desc_en": "Natural rubber base bonded to a moisture-absorbing PU top layer — the grip "
                   "standard for hot yoga and studio use. Suede-feel, matte and print-ready "
                   "surfaces, 1.5–5 mm, customizable size and logo.",
        "desc_zh": "天然橡胶底贴合吸湿 PU 面层，是高温瑜伽与专业瑜伽馆的防滑标杆。"
                   "可选绒感、磨砂与可印花表面，厚度 1.5–5 mm，尺寸与 Logo 均可定制。",
        "h1_en": "PU & Rubber Yoga Mats",
        "h1_zh": "PU 橡胶瑜伽垫",
    },
    {
        "key": "suede-cork-yoga-mats",
        "en": "Suede & Cork Yoga Mats",
        "zh": "麂皮与软木瑜伽垫",
        "kw_en": "Suede / Cork Surface · Print-Ready",
        "kw_zh": "麂皮 / 软木面层 · 可印花",
        "desc_en": "Suede microfibre and natural cork surfaces take high-definition prints and get "
                   "grippier with sweat. The go-to family for branded, design-led collections and "
                   "eco-positioned ranges.",
        "desc_zh": "超细纤维麂皮与天然软木面层可做高清印花，遇汗更防滑，"
                   "是品牌联名款、设计驱动系列与环保定位产品线的首选。",
        "h1_en": "Suede & Cork Yoga Mats",
        "h1_zh": "麂皮与软木瑜伽垫",
    },
    {
        "key": "meditation-pilates-mats",
        "en": "Meditation & Pilates Mats",
        "zh": "冥想垫与普拉提垫",
        "kw_en": "Round · Mandala · Reformer Mat",
        "kw_zh": "圆形 · 曼陀罗 · 器械垫",
        "desc_en": "Round meditation mats, mandala prints, bolsters and made-to-order Pilates "
                   "reformer mats cut to your machine's dimensions with your own logo.",
        "desc_zh": "圆形冥想垫、曼陀罗印花、瑜伽枕，以及按器械尺寸定制、可加自有 Logo 的普拉提器械垫。",
        "h1_en": "Meditation & Pilates Mats",
        "h1_zh": "冥想垫与普拉提垫",
    },
    {
        "key": "foam-rollers",
        "en": "Foam Rollers",
        "zh": "瑜伽柱 / 泡沫轴",
        "kw_en": "EVA / EPP · Solid & Hollow · Vibrating",
        "kw_zh": "EVA / EPP · 实心与空心 · 震动款",
        "desc_en": "EVA and EPP foam rollers in solid, hollow and vibrating builds, plus "
                   "wolf-tooth textured models. Custom density, length, colour, logo and packaging.",
        "desc_zh": "EVA 与 EPP 材质泡沫轴，含实心、空心与震动款，另有狼牙纹理款。"
                   "密度、长度、颜色、Logo 与包装均可定制。",
        "h1_en": "Foam Rollers",
        "h1_zh": "瑜伽柱 / 泡沫轴",
    },
    {
        "key": "massage-recovery",
        "en": "Massage & Recovery",
        "zh": "按摩与放松恢复",
        "kw_en": "Fascia Gun · Fascia Ball · Massage Tools",
        "kw_zh": "筋膜枪 · 筋膜球 · 按摩工具",
        "desc_en": "Fascia guns, fascia balls, massage sticks, massagers and leg clamps — the "
                   "recovery category that pairs with every mat order. Private-label ready.",
        "desc_zh": "筋膜枪、筋膜球、按摩棒、按摩器与腿部夹等恢复类工具，"
                   "可与任意垫类订单搭配出货，支持贴牌。",
        "h1_en": "Massage & Recovery",
        "h1_zh": "按摩与放松恢复",
    },
    {
        "key": "resistance-bands",
        "en": "Resistance Bands",
        "zh": "弹力带 / 阻力带",
        "kw_en": "Loop · Tube · Figure-8 · Power Band",
        "kw_zh": "环形 · 拉力管 · 8 字 · 力量带",
        "desc_en": "TPE and latex resistance bands in loop, tube, figure-8 and power-band formats "
                   "with graded resistance levels. Custom colour sets, printed logo and retail sets.",
        "desc_zh": "TPE 与乳胶材质阻力带，含环形、拉力管、8 字与力量带等形态，"
                   "阻力分级齐全。支持配色套装、印制 Logo 与零售装。",
        "h1_en": "Resistance Bands",
        "h1_zh": "弹力带 / 阻力带",
    },
    {
        "key": "yoga-props-accessories",
        "en": "Yoga Props & Accessories",
        "zh": "瑜伽辅具与配件",
        "kw_en": "Blocks · Balls · Rings · Bags · Hammock",
        "kw_zh": "瑜伽砖 · 瑜伽球 · 瑜伽环 · 背包 · 吊床",
        "desc_en": "EVA blocks, yoga balls, Pilates rings, aerial hammocks, stretch boards and "
                   "carry bags — the add-on items that raise average order value on every mat shipment.",
        "desc_zh": "EVA 瑜伽砖、瑜伽球、普拉提环、空中吊床、拉伸板与收纳背包等辅具，"
                   "可与垫类同柜出货、有效提升客单价。",
        "h1_en": "Yoga Props & Accessories",
        "h1_zh": "瑜伽辅具与配件",
    },
]

CAT_BY_KEY = {c["key"]: c for c in CATS}

# ---------------------------------------------------------------- 手工例外
# 老页 / 英文站分类明显错分的产品，逐个指定
MANUAL = {
    # --- TPE 垫 ---
    "ym1": "tpe-yoga-mats", "ym2": "tpe-yoga-mats", "ym3": "tpe-yoga-mats",
    "ym4": "tpe-yoga-mats", "ym7": "tpe-yoga-mats",
    "foldable-yoga-mat-multi-color": "tpe-yoga-mats",
    "pink-foldable-yoga-mat": "tpe-yoga-mats",
    # --- PU / 橡胶 ---
    "ym5": "pu-rubber-yoga-mats", "ym6": "pu-rubber-yoga-mats",
    "olive-foldable-rubber-yoga-mat": "pu-rubber-yoga-mats",
    # --- 麂皮 / 软木（英文站 Folding Mat 里的麂皮款）---
    "flamingo-print-suede-rubber-yoga-mat": "suede-cork-yoga-mats",
    "gold-koi-foldable-suede-yoga-mat": "suede-cork-yoga-mats",
    # --- 冥想 / 普拉提 ---
    "pr3": "meditation-pilates-mats",
    "pilates-reformer-mat-mandala": "meditation-pilates-mats",
    "pilates-reformer-mat-tropical-print": "meditation-pilates-mats",
    "pilates-reformer-mat-custom-logo": "meditation-pilates-mats",
    # --- 泡沫轴 ---
    "fr1": "foam-rollers", "fr2": "foam-rollers", "fr3": "foam-rollers", "fr4": "foam-rollers",
    # --- 按摩 ---
    "fr5": "massage-recovery",
    # --- 弹力带 ---
    "rb1": "resistance-bands",
    # --- 辅具 ---
    "pr1": "yoga-props-accessories", "pr4": "yoga-props-accessories",
    "rb2": "yoga-props-accessories", "yoga-block-cover": "yoga-props-accessories",
    "stretch-board": "yoga-props-accessories",
    # --- 健身小件 ---
    "fi2": "yoga-props-accessories", "fi3": "yoga-props-accessories",
    "fi4": "yoga-props-accessories", "fi5": "yoga-props-accessories",
}

# ---------------------------------------------------------------- 规则
# 英文站分类 → 我们的大类
RULE = {
    "TPE Mat": "tpe-yoga-mats",
    "Economical Yoga Mat": "tpe-yoga-mats",
    "Folding Mat": "tpe-yoga-mats",
    "PU Mat": "pu-rubber-yoga-mats",
    "Suede Mat": "suede-cork-yoga-mats",
    "Cork Mat": "suede-cork-yoga-mats",
    "Meditation Mat": "meditation-pilates-mats",
    "Pilates Reformer Mat": "meditation-pilates-mats",
    "EVA Foam Roller": "foam-rollers",
    "Foam Roller": "foam-rollers",
    "Fascia Gun": "massage-recovery",
    "Fascia Ball": "massage-recovery",
    "Massage Accessories": "massage-recovery",
    "Resistance Bands": "resistance-bands",
    "Loop Bands": "resistance-bands",
    "Figure 8 Bands": "resistance-bands",
    "Pilates Ring": "yoga-props-accessories",
    "Yoga Accessories": "yoga-props-accessories",
    "Yoga Mat": "yoga-props-accessories",
    "Silicone Series": "yoga-props-accessories",
    "Adjustable Dumbbell": "yoga-props-accessories",
}

# slug 关键词兜底
FALLBACK = [
    ("tpe", "tpe-yoga-mats"),
    ("pu-", "pu-rubber-yoga-mats"),
    ("suede", "suede-cork-yoga-mats"),
    ("cork", "suede-cork-yoga-mats"),
    ("meditation", "meditation-pilates-mats"),
    ("reformer", "meditation-pilates-mats"),
    ("roller", "foam-rollers"),
    ("fascia", "massage-recovery"),
    ("massag", "massage-recovery"),
    ("band", "resistance-bands"),
    ("ring", "yoga-props-accessories"),
    ("block", "yoga-props-accessories"),
    ("ball", "yoga-props-accessories"),
    ("bag", "yoga-props-accessories"),
]


def build():
    """返回 {slug: cat_key}，并把英文站标题一并返回。"""
    b1 = json.load(open(os.path.join(ROOT, "outputs/batch1_pages.json"), encoding="utf-8"))
    b2 = json.load(open(os.path.join(ROOT, "outputs/batch2_pages.json"), encoding="utf-8"))
    m = {p["new"]: p["src"] for p in b1 + b2}
    cat = {c["slug"]: c for c in json.load(
        open(os.path.join(ROOT, "outputs/sf_catalog_full.json"), encoding="utf-8"))}

    slugs = sorted(os.path.basename(p)[:-5]
                   for p in glob.glob(os.path.join(ROOT, "products/*.html")))
    out, unmapped = {}, []
    for s in slugs:
        if s in MANUAL:
            out[s] = MANUAL[s]
            continue
        src = m.get(s)
        cats = cat.get(src, {}).get("cats") if src else None
        hit = None
        if cats:
            for c in cats:
                if c in RULE:
                    hit = RULE[c]
                    break
        if not hit:
            for kw, k in FALLBACK:
                if kw in s:
                    hit = k
                    break
        if hit:
            out[s] = hit
        else:
            unmapped.append(s)
    return out, unmapped


if __name__ == "__main__":
    import collections
    res, unmapped = build()
    g = collections.defaultdict(list)
    for s, k in res.items():
        g[k].append(s)
    print("分类覆盖：%d 页" % len(res))
    for c in CATS:
        print("  %-26s %2d  %s" % (c["key"], len(g[c["key"]]), c["en"]))
    if unmapped:
        print("\n!! 未归类：", unmapped)
    else:
        print("\n✅ 全部归类完成")
