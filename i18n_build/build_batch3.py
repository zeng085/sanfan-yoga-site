#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第三批上站：跳绳 + 力量健身 + 空中瑜伽吊床（24 个）。

数据源：outputs/sf_catalog_full.json（fetch_sf_catalog.py 全量采集）
页面骨架：复用 build_batch1.py 的 HEAD（exec 到 main 之前，不触发 main）
图片：/tmp/probe_b3_md5/<英文站slug>/<n>.webp → assets/img/<本地slug>-<n>.webp（全量，不截断）

⚠️ 为什么是 24 而不是 29：
   第三批候选 29 个（有真规格）里有 5 个的**全部图集**已 100% 命中站内已有文件，
   即已被 5 个「家族页」收录（fi2 壶铃 / fi3 跳绳 / fi4 踏步机 / fi5 哑铃杠铃 / pr1 吊床）：
       dumbbell-2→fi5   jump-rope-2→fi3   kettlebell-2→fi2
       stair-climbers-3→fi4   yoga-hammock→pr1
   判定方式见 i18n_build/probe_md5.py（md5 逐字节比对，非感知哈希）。
   这 5 个不重复建页，其余 24 个为全新素材。

分类：新增 2 个分类（jump-ropes / strength-training），吊床并入既有 yoga-props-accessories。

用法：
  python3 i18n_build/build_batch3.py --dry-run
  python3 i18n_build/build_batch3.py
"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STAGE = "/tmp/probe_b3_md5"          # probe_md5.py 已按「最长边900 + WebP q75」转好
IMGDIR = os.path.join(ROOT, "assets", "img")
CATALOG = os.path.join(ROOT, "outputs", "sf_catalog_full.json")
OUTJSON = os.path.join(ROOT, "outputs", "batch3_pages.json")

DOMAIN = "https://fjsanfan.com"
MOQ = "100 pcs"
CERT = "ROHS / CE / ISO 9001 / BSCI / REACH"

# 已在家族页里、不重复建的产品（md5 100% 命中站内已有文件）
SKIP = {
    "dumbbell-2": "fi5 哑铃与杠铃页",
    "jump-rope-2": "fi3 跳绳页",
    "kettlebell-2": "fi2 壶铃页",
    "stair-climbers-3": "fi4 家用踏步机页",
    "yoga-hammock": "pr1 空中瑜伽吊床页",
}

# ---------------------------------------------------------------- 复用第一批骨架
_core = open(os.path.join(HERE, "build_batch1.py"), encoding="utf-8").read().split("def main():")[0]
_ns = {"__file__": os.path.join(HERE, "build_batch1.py"), "__name__": "batch1_core"}
exec(compile(_core, "batch1_core", "exec"), _ns)          # noqa: S102
esc = _ns["esc"]
HEAD = (_ns["HEAD"]
        .replace("Yoga Mats", "@@CATEN@@")
        .replace("瑜伽垫", "@@CATZH@@"))

# 分类（key 必须与 category_map.py 的 CATS 一致）
SECT = {
    "jump-ropes": ("Jump Ropes", "跳绳"),
    "strength-training": ("Strength &amp; Fitness", "力量与健身"),
    "yoga-props-accessories": ("Yoga Props &amp; Accessories", "瑜伽辅具与配件"),
}

# ---------------------------------------------------------------- 文案族
COPY = {
    "jump_rope": {
        "desc_en": "Speed and counting jump rope, {mat}, {size}. Handle shape, rope length and branding are configured to your order.",
        "desc_zh": "速度跳绳 / 计数跳绳，{mat}，{size}。握柄形态、绳长与品牌标识按订单定制。",
        "ov_en": "PVC-coated and steel-wire ropes with ABS, aluminium or EVA handles. Counting models carry an LCD or a mechanical counter, and cordless versions swap the rope for weighted balls so they can be used indoors without ceiling height. Rope length, grip colour and cable diameter are all set per order.",
        "ov_zh": "PVC 包覆绳与钢丝绳，配 ABS / 铝合金 / EVA 握柄。计数款带 LCD 或机械计数器；无绳款以配重球替代绳体，室内不受层高限制。绳长、握把颜色与绳径均可按订单设定。",
        "f_en": ["PVC-coated cable and steel-wire options", "LCD counting, mechanical counting and cordless builds",
                 "ABS / aluminium / EVA handles, tangle-free swivel", "Custom rope length, grip colour and logo"],
        "f_zh": ["PVC 包覆绳与钢丝绳可选", "LCD 计数 / 机械计数 / 无绳款齐备",
                 "ABS / 铝合金 / EVA 握柄，防缠绕轴承", "绳长、握把颜色与 logo 可定制"],
        "ap_en": "For fitness brands, home-workout retail, school and gym programmes, and promotional sets.",
        "ap_zh": "适合健身品牌、家用训练零售、学校与健身房项目，以及促销套装。",
    },
    "strength": {
        "desc_en": "Silicone-coated strength tool, {mat}, {size}. Weight, colour and branding are set to your programme.",
        "desc_zh": "硅胶包覆力量训练器材，{mat}，{size}。配重、颜色与品牌标识按你的项目定制。",
        "ov_en": "Silicone-skinned cast-iron weights with a soft matte finish that will not chip flooring or mark hands. The same colour system runs across balls, rings, dumbbells and barbells, so a full weighted set can ship as one branded collection.",
        "ov_zh": "硅胶包覆配重铁件，哑光软面，不刮地板、不脏手。球、环、哑铃、杠铃共用同一套配色，可作为一个品牌系列整体出货。",
        "f_en": ["Silicone-skinned cast iron — no floor damage, no marks", "Consistent colour system across the full range",
                 "Custom weight, colour and logo", "Retail box and set packaging available"],
        "f_zh": ["硅胶包覆配重铁件，不刮地板、不脏手", "全系列共用一套配色体系",
                 "配重、颜色与 logo 可定制", "可选零售盒与成套包装"],
        "ap_en": "For home-fitness brands, studio strength corners, rehab programmes and gift retail.",
        "ap_zh": "适合家用健身品牌、瑜伽馆力量区、康复训练项目与礼赠零售。",
    },
    "ab_roller": {
        "desc_en": "Ab roller, {mat}, {size}. Wheel count, grip and branding are made to your order.",
        "desc_zh": "健腹轮，{mat}，{size}。轮数、握把与品牌标识按订单定制。",
        "ov_en": "Single and twin-wheel ab rollers with textured grips and a wide tread for stability on the roll-out. Bundled versions add resistance bands, hand grips or skipping ropes, which makes them an easy set for retail and promotional programmes.",
        "ov_zh": "单轮与双轮健腹轮，握把带防滑纹，轮面加宽保证滚出时的稳定性。套装款可搭配阻力带、握力器或跳绳，适合零售与促销成套出货。",
        "f_en": ["Single and twin-wheel builds", "Wide non-slip tread, textured grips",
                 "Set options with bands, grips or rope", "Custom colour and logo"],
        "f_zh": ["单轮与双轮结构", "加宽防滑轮面，握把带防滑纹",
                 "可配套阻力带 / 握力器 / 跳绳", "颜色与 logo 可定制"],
        "ap_en": "For home-fitness retail, core-training programmes and promotional bundles.",
        "ap_zh": "适合家用健身零售、核心训练项目与促销套装。",
    },
    "fitness_board": {
        "desc_en": "Multi-function fitness board, {mat}, {size}. Colour, print and branding are set per order.",
        "desc_zh": "多功能健身板，{mat}，{size}。颜色、印刷与品牌标识按订单定制。",
        "ov_en": "A flat training board for push-up, plank and balance work, in PP with a foam or TPE grip surface. Light enough to ship in volume and flat enough to stack, with your print straight onto the deck.",
        "ov_zh": "用于俯卧撑、平板支撑与平衡训练的平板器械，PP 基材配泡棉或 TPE 防滑面。自重轻、体积小，可堆叠运输，板面可直接印你的图案。",
        "f_en": ["PP deck with foam or TPE grip surface", "Light and flat-packed for volume shipping",
                 "Full-surface print available", "Custom colour and logo"],
        "f_zh": ["PP 板体配泡棉或 TPE 防滑面", "自重轻、可平叠，适合批量运输",
                 "支持整面印刷", "颜色与 logo 可定制"],
        "ap_en": "For home-fitness brands, core and balance programmes, and retail lines.",
        "ap_zh": "适合家用健身品牌、核心与平衡训练项目，以及零售产品线。",
    },
    "stepper": {
        "desc_en": "Stair climber, {mat}, {size}. Resistance, colour and branding are configured to your market.",
        "desc_zh": "登山机，{mat}，{size}。阻力、颜色与品牌标识按目标市场定制。",
        "ov_en": "A compact hydraulic stepper for low-impact cardio — the piece that fits a small apartment and still carries a full-body load. Resistance is set by the hydraulic cylinders, and the frame ships with your colour and logo.",
        "ov_zh": "紧凑型液压登山机，低冲击有氧器械，占地小但全身参与。阻力由液压缸设定，机身可按你的要求做颜色与 logo。",
        "f_en": ["Hydraulic resistance, low-impact cardio", "Compact footprint for home use",
                 "LCD step counter on selected models", "Custom colour and logo"],
        "f_zh": ["液压阻力，低冲击有氧", "占地小，适合家用",
                 "部分型号带 LCD 计数", "颜色与 logo 可定制"],
        "ap_en": "For home-fitness retail, hotel and apartment gyms, and e-commerce brands.",
        "ap_zh": "适合家用健身零售、酒店与公寓健身房，以及电商品牌。",
    },
    "hammock": {
        "desc_en": "Aerial yoga hammock, {mat}, {size}. Fabric, colour and print are made to your order.",
        "desc_zh": "空中瑜伽吊床，{mat}，{size}。面料、颜色与印花按订单定制。",
        "ov_en": "Aerial hammocks in 210T nylon taffeta and polyester, load-tested for inversion work and finished with reinforced seams and daisy-chain rigging points. Gradient, solid and ombre dye lots take studio brand colours, and kits ship with straps and carabiners.",
        "ov_zh": "210T 尼龙塔夫绸与涤纶空中吊床，按倒立体位做载荷测试，接缝加固、配菊花链挂点。渐变、纯色与扎染批次可对上瑜伽馆品牌色，套装含绑带与锁扣。",
        "f_en": ["210T nylon taffeta and polyester builds", "Reinforced seams, daisy-chain rigging points",
                 "Gradient, solid and ombre colourways", "Kits with straps and carabiners"],
        "f_zh": ["210T 尼龙塔夫绸与涤纶两种面料", "接缝加固，配菊花链挂点",
                 "渐变 / 纯色 / 扎染多种配色", "套装含绑带与锁扣"],
        "ap_en": "For aerial studios, wellness brands, retreat kits and training-school supply.",
        "ap_zh": "适合空中瑜伽馆、健康品牌、静修套装与培训机构采购。",
    },
}

# 规格表额外字段（英文站有、标准 10 字段之外的实质规格）
# (specs 键, 英文标签, 中文标签) —— 英文标签用可读写法，不直接吐驼峰键名
EXTRA = [
    ("RopeLength", "Rope length", "绳长"),
    ("BallDiameter", "Ball diameter", "球径"),
    ("FabricWeight", "Fabric weight", "面料克重"),
    ("Wheels", "Wheels", "轮数"),
    ("PackageSize", "Package size", "包装尺寸"),
    ("CartonSize", "Carton size", "外箱尺寸"),
    ("Style", "Style", "款式"),
    ("Resistance", "Resistance", "阻力"),
    ("RollerCount", "Rollers", "滚轮数"),
    ("MassageArea", "Massage area", "按摩区域"),
    ("MassageHeads", "Massage heads", "按摩头数"),
]

ZH = {"Material": "材质", "Size": "尺寸", "Thickness": "厚度", "Weight": "重量", "MOQ": "起订量",
      "Colors": "颜色与印花", "Feature": "特性", "Logo": "定制标识", "Compliance": "合规认证",
      "Packaging": "包装"}


def spec_rows3(specs):
    """标准 10 字段 + 额外实质规格；空值不出行，不编数据。"""
    order = [("Material", specs.get("Material")),
             ("Size", specs.get("Size")),
             ("Thickness", specs.get("Thickness")),
             ("Weight", specs.get("Weight")),
             ("MOQ", MOQ)]
    for k, _en, _zh in EXTRA:
        if specs.get(k):
            order.append((k, specs.get(k)))
    order += [("Colors", specs.get("Colors")),
              ("Feature", specs.get("Feature")),
              ("Logo", specs.get("Logo")),
              ("Compliance", CERT),
              ("Packaging", specs.get("Packaging"))]
    ex_en = {k: en for k, en, _zh in EXTRA}
    ex_zh = {k: zh for k, _en, zh in EXTRA}
    out = []
    for k, v in order:
        v = (v or "").strip()
        if not v:
            continue
        label_en = ex_en.get(k, k)           # 标准字段的键名本身就是英文标签
        label_zh = ZH.get(k) or ex_zh.get(k, k)
        out.append('<tr><th><span class="lang-en">' + esc(label_en) + '</span>'
                   '<span class="lang-zh">' + esc(label_zh) + '</span></th>'
                   '<td>' + esc(v) + '</td></tr>')
    return "".join(out)


# slug, EN title, ZH title, family, section, base price (FOB Xiamen USD；None = 不放价)
ROWS = [
    # --- 跳绳（新分类 jump-ropes）---
    ("speed-jump-rope", "speed-jump-rope", "Speed Jump Rope", "速度跳绳",
     "jump_rope", "jump-ropes", None),
    ("jump-rope-3", "two-tone-kids-jump-rope", "Two-Tone Kids Jump Rope", "双色儿童跳绳",
     "jump_rope", "jump-ropes", None),
    ("jump-rope-kids", "kids-jump-rope", "Kids Jump Rope", "儿童跳绳",
     "jump_rope", "jump-ropes", None),
    ("cordless-jump-rope", "cordless-jump-rope", "Cordless Jump Rope", "无绳跳绳",
     "jump_rope", "jump-ropes", None),
    ("electronic-counting-skip-rope", "electronic-counting-jump-rope", "Electronic Counting Jump Rope",
     "电子计数跳绳", "jump_rope", "jump-ropes", None),
    ("smart-counting-jump-rope", "smart-counting-jump-rope", "Smart Counting Jump Rope", "智能计数跳绳",
     "jump_rope", "jump-ropes", None),
    # --- 力量与健身（新分类 strength-training）---
    ("ab-roller", "ab-roller-with-resistance-band", "Ab Roller with Resistance Band", "带阻力带健腹轮",
     "ab_roller", "strength-training", None),
    ("ab-roller-2", "giant-ab-roller", "Giant Ab Roller", "加大轮健腹轮",
     "ab_roller", "strength-training", None),
    ("ab-roller-set", "ab-roller-training-set", "AB Roller Training Set", "健腹轮训练套装",
     "ab_roller", "strength-training", None),
    # 报价表行 15「beam dumbbell 15LB/pc length 91cm」= 27.5，与本款 91cm/15lbs 精确吻合
    ("barbell", "wave-silicone-barbell", "Wave Silicone Barbell", "波浪形硅胶杠铃",
     "strength", "strength-training", 27.5),
    ("dumbbell", "triangular-silicone-dumbbell", "Triangular Silicone Dumbbell", "三角硅胶哑铃",
     "strength", "strength-training", None),
    ("weighted-ball", "weighted-training-ball", "Weighted Training Ball", "负重训练球",
     "strength", "strength-training", None),
    ("weighted-ring", "weighted-training-ring", "Weighted Training Ring", "负重训练环",
     "strength", "strength-training", None),
    # 报价表行 13「silicone bangles 2LB/pair product size 29*7cm」= 7.15，与本款 29*7cm/900g(2LB) 吻合
    ("wrist-weights", "silicone-wrist-ankle-weights", "Silicone Wrist & Ankle Weights", "硅胶腕部与踝部沙袋",
     "strength", "strength-training", 7.15),
    ("fitness-board", "multi-function-fitness-board", "Multi-Function Fitness Board", "多功能健身板",
     "fitness_board", "strength-training", None),
    ("p3-fitness-board", "p3-smart-fitness-board", "P3 Smart Fitness Board", "P3 智能健身板",
     "fitness_board", "strength-training", None),
    ("stair-climbers", "adjustable-stair-climber", "Adjustable Stair Climber", "可调式登山机",
     "stepper", "strength-training", None),
    ("stair-climbers-2", "compact-stair-climber", "Compact Stair Climber", "紧凑型登山机",
     "stepper", "strength-training", None),
    # --- 空中瑜伽吊床（并入既有 yoga-props-accessories）---
    ("gradient-color-yoga-hammock", "gradient-aerial-yoga-hammock", "Gradient Aerial Yoga Hammock",
     "渐变色空中瑜伽吊床", "hammock", "yoga-props-accessories", None),
    ("solid-color-yoga-hammock", "solid-color-aerial-yoga-hammock", "Solid Color Aerial Yoga Hammock",
     "纯色空中瑜伽吊床", "hammock", "yoga-props-accessories", None),
    ("yoga-hammock-3", "colorful-aerial-yoga-hammock", "Colorful Aerial Yoga Hammock",
     "彩虹色空中瑜伽吊床", "hammock", "yoga-props-accessories", None),
    ("yoga-hammock-4", "ombre-aerial-yoga-hammock", "Ombre Aerial Yoga Hammock",
     "渐变拼色空中瑜伽吊床", "hammock", "yoga-props-accessories", None),
    ("yoga-hammock-5", "large-aerial-yoga-hammock", "Large Aerial Yoga Hammock 5 × 2.8 m",
     "大尺寸空中瑜伽吊床 5×2.8 m", "hammock", "yoga-props-accessories", None),
    ("yoga-hammock-with-handles", "aerial-yoga-hammock-with-handles", "Aerial Yoga Hammock with Handles",
     "带手柄空中瑜伽吊床", "hammock", "yoga-props-accessories", None),
]


def build_jsonld(title_en, desc_en, url, imgs, base, sect_key):
    cat_en = SECT[sect_key][0].replace("&amp;", "&")
    g = [{
        "@type": "Product",
        "name": title_en,
        "description": desc_en,
        "image": imgs,
        "brand": {"@type": "Brand", "name": "SANFAN"},
        "category": cat_en,
        "url": url,
    }]
    if base:
        g[0]["offers"] = {
            "@type": "AggregateOffer",
            "lowPrice": round(base * 0.7, 2),
            "highPrice": round(base * 1.3, 2),
            "priceCurrency": "USD",
            "url": DOMAIN + "/contact.html",
        }
    g.append({
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": DOMAIN + "/"},
            {"@type": "ListItem", "position": 2, "name": "Products", "item": DOMAIN + "/products.html"},
            {"@type": "ListItem", "position": 3, "name": cat_en, "item": DOMAIN + "/" + sect_key + ".html"},
            {"@type": "ListItem", "position": 4, "name": title_en, "item": url},
        ],
    })
    return json.dumps({"@context": "https://schema.org", "@graph": g}, ensure_ascii=False, indent=2)


def main():
    dry = "--dry-run" in sys.argv
    ver = "20260912a"
    m = re.search(r"styles\.css\?v([A-Za-z0-9]+)",
                  open(os.path.join(ROOT, "products", "ym1.html"), encoding="utf-8").read())
    if m:
        ver = m.group(1)

    cat = {p["slug"]: p for p in json.load(open(CATALOG, encoding="utf-8"))}
    items = []
    for slug, new, t_en, t_zh, fam, sect, base in ROWS:
        p = cat.get(slug)
        if not p:
            print("  [缺数据]", slug)
            continue
        items.append({
            "src": slug, "new": new, "title_en": t_en, "title_zh": t_zh,
            "fam": fam, "sect": sect, "base": base,
            "specs": p["specs"], "imgs": p["images"],
        })

    print("第三批待生成：%d 页" % len(items))
    print("  跳过（已被家族页收录，md5 100% 命中）：")
    for k, v in SKIP.items():
        print("    %-20s ← %s" % (k, v))
    print("  带报价 %d / 不带报价 %d"
          % (sum(1 for i in items if i["base"]), sum(1 for i in items if not i["base"])))
    if dry:
        for i in items:
            print("  %-40s %-46s %-13s %s"
                  % (i["new"], i["title_en"][:44], i["sect"], i["base"] or "-"))
        return

    # 同名页 / 同名图冲突检查
    clash = [i["new"] for i in items
             if os.path.exists(os.path.join(ROOT, "products", i["new"] + ".html"))]
    if clash:
        print("  ⚠ 已存在同名页，将被覆盖：", clash)

    # 1) 图片入库
    idmap, ok_img, noimg, imgclash = {}, 0, [], []
    for it in items:
        srcdir = os.path.join(STAGE, it["src"])
        srcs = sorted((f for f in os.listdir(srcdir) if f.endswith(".webp")),
                      key=lambda x: int(x[:-5])) if os.path.isdir(srcdir) else []
        if not srcs:
            noimg.append(it["src"])
        names = []
        for n, f in enumerate(srcs, 1):
            d = "%s-%d.webp" % (it["new"], n)
            tgt = os.path.join(IMGDIR, d)
            if os.path.exists(tgt):
                imgclash.append(d)
            shutil.copyfile(os.path.join(srcdir, f), tgt)
            names.append(d)
            ok_img += 1
        idmap[it["src"]] = names
    print("图片入库：%d 张" % ok_img)
    if noimg:
        print("  ⚠ 无图：" + ", ".join(noimg))
    if imgclash:
        print("  ⚠ 覆盖同名图 %d 张：%s" % (len(imgclash), ", ".join(imgclash[:6])))

    # 2) 写出页面
    by_fam = {}
    for it in items:
        by_fam.setdefault(it["fam"], []).append(it)

    written = 0
    for it in items:
        names = idmap.get(it["src"]) or []
        if not names:
            continue
        fam, specs, sect = it["fam"], it["specs"], it["sect"]
        cp = COPY[fam]
        size = (specs.get("Size") or "").strip()
        mat = (specs.get("Material") or "").strip()
        fill_en = {"size": size or "made to your size", "thk": (specs.get("Thickness") or "").strip(),
                   "mat": mat or "made to order"}
        fill_zh = {"size": size or "尺寸按需定制", "thk": (specs.get("Thickness") or "").strip(),
                   "mat": mat or "按需定制"}
        desc_en = cp["desc_en"].format(**fill_en)
        desc_zh = cp["desc_zh"].format(**fill_zh)
        f_en = "".join("<li>" + esc(esc(b)) + "</li>" for b in cp["f_en"])
        f_zh = "".join("<li>" + esc(b) + "</li>" for b in cp["f_zh"])

        url = "%s/products/%s.html" % (DOMAIN, it["new"])
        thumbs = []
        for n, nm in enumerate(names):
            cls = "pd-thumb active" if n == 0 else "pd-thumb"
            thumbs.append('<button type="button" class="%s"><img src="../assets/img/%s" '
                          'width="480" height="480" loading="lazy" alt="%s"></button>'
                          % (cls, nm, esc(it["title_en"])))

        pool = [x for x in by_fam.get(fam, []) if x["src"] != it["src"]]
        if len(pool) < 4:
            pool += [x for x in items if x["src"] != it["src"] and x not in pool]
        rel = []
        for r in pool[:4]:
            rn = idmap.get(r["src"]) or []
            if not rn:
                continue
            meta = " · ".join([x for x in [(r["specs"].get("Material") or "").strip(),
                                           (r["specs"].get("Size") or "").strip()] if x])
            rel.append(
                '<a class="prod-card" href="../products/%s.html">'
                '<div class="ph"><img src="../assets/img/%s" width="480" height="480" '
                'loading="lazy" alt="%s"></div>'
                '<div class="info"><h4><span class="lang-en">%s</span><span class="lang-zh">%s</span></h4>'
                '<p><span class="lang-en">%s</span><span class="lang-zh">%s</span></p></div></a>'
                % (r["new"], rn[0], esc(r["title_en"]), esc(r["title_en"]), esc(r["title_zh"]),
                   esc(meta), esc(meta)))

        wa_en = ("Hi%20SANFAN%2C%20I%20am%20interested%20in%20" +
                 it["title_en"].replace(" ", "%20").replace("&", "%26").replace("/", "%2F"))
        wa_zh = ("%E4%BD%A0%E5%A5%BD%E4%B8%89%E6%A2%B5%EF%BC%8C%E6%88%91%E6%83%B3%E4%BA%86%E8%A7%A3%20" +
                 it["title_zh"].replace(" ", "%20"))

        html = HEAD
        for k, v in [
            ("@@VER@@", ver),
            ("@@TITLEZH@@", esc(it["title_zh"])),
            ("@@TITLE@@", esc(it["title_en"])),
            ("@@DESC@@", esc(desc_en[:300])),
            ("@@URL@@", url),
            ("@@OGIMG@@", DOMAIN + "/assets/img/" + names[0]),
            ("@@JSONLD@@", build_jsonld(it["title_en"], desc_en, url,
                                        [DOMAIN + "/assets/img/" + n for n in names],
                                        it["base"], sect)),
            ("@@IMG1@@", names[0]),
            ("@@THUMBS@@", "\n          ".join(thumbs)),
            ("@@DESCEN@@", esc(desc_en)),
            ("@@DESCZH@@", esc(desc_zh)),
            ("@@WA@@", wa_en),
            ("@@WAEN@@", wa_en),
            ("@@WAZH@@", wa_zh),
            ("@@SPECROWS@@", spec_rows3(specs)),
            ("@@OVEN@@", esc(cp["ov_en"].format(**fill_en))),
            ("@@OVZH@@", esc(cp["ov_zh"].format(**fill_zh))),
            ("@@FEN@@", f_en),
            ("@@FZH@@", f_zh),
            ("@@APEN@@", esc(cp["ap_en"].format(**fill_en))),
            ("@@APZH@@", esc(cp["ap_zh"].format(**fill_zh))),
            ("@@RELATED@@", "".join(rel)),
            ("@@CATEN@@", SECT[sect][0]),
            ("@@CATZH@@", SECT[sect][1]),
        ]:
            html = html.replace(k, v)
        left = re.findall(r"@@[A-Z]+@@", html)
        if left:
            print("  ⚠ 未替换占位符 %s ← %s" % (sorted(set(left)), it["new"]))
        with open(os.path.join(ROOT, "products", it["new"] + ".html"), "w", encoding="utf-8") as fh:
            fh.write(html)
        written += 1

    print("写出页面：%d 个" % written)
    json.dump(items, open(OUTJSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("✅ %s" % os.path.relpath(OUTJSON, ROOT))


if __name__ == "__main__":
    main()
