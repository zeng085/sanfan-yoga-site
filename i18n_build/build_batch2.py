#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第二批上站：放松按摩 + 瑜伽配件（英文站 40 个产品，EN + 中文同页切换）。

数据源：outputs/sf_catalog_full.json（fetch_sf_catalog.py 全量采集）
页面骨架：复用 build_batch1.py 的 HEAD（exec 前 515 行，不触发 main）
图片：/tmp/sf_img_stage/<英文站slug>-<n>.webp → assets/img/<slug>-<n>.webp

用法：
  python3 i18n_build/build_batch2.py --dry-run
  python3 i18n_build/build_batch2.py
"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STAGE = "/tmp/sf_img_stage"
IMGDIR = os.path.join(ROOT, "assets", "img")
CATALOG = os.path.join(ROOT, "outputs", "sf_catalog_full.json")
OUTJSON = os.path.join(ROOT, "outputs", "batch2_pages.json")

DOMAIN = "https://fjsanfan.com"
MOQ = "100 pcs"
CERT = "ROHS / CE / ISO 9001 / BSCI / REACH"
MAX_IMAGES = 8

# ---------------------------------------------------------------- 复用第一批骨架
_core = open(os.path.join(HERE, "build_batch1.py"), encoding="utf-8").read().split("def main():")[0]
_ns = {"__file__": os.path.join(HERE, "build_batch1.py"), "__name__": "batch1_core"}
exec(compile(_core, "batch1_core", "exec"), _ns)          # noqa: S102
esc = _ns["esc"]
slugify = _ns["slugify"]
spec_rows = _ns["spec_rows"]
HEAD = _ns["HEAD"].replace("Yoga Mats", "@@CATEN@@").replace("瑜伽垫", "@@CATZH@@")

SECT = {
    "rollers": ("Recovery & Massage", "放松与按摩"),
    "bands": ("Resistance Bands", "弹力带"),
    "props": ("Yoga Accessories", "瑜伽配件"),
}

# ---------------------------------------------------------------- 文案族
COPY = {
    "roller": {
        "desc_en": "EVA foam roller, {size}. Density, surface pattern and colour are set to your order — a staple of gym, studio and recovery programmes.",
        "desc_zh": "EVA 泡沫轴，{size}。密度、表面纹路与颜色按你的订单定制——健身房、瑜伽馆与恢复类项目的常备品。",
        "ov_en": "High-density EVA roller for myofascial release and post-training recovery. Surface patterns run from smooth to studded and wolf-tooth, and both length and density can be fixed per order. Logo printing and retail packaging are available.",
        "ov_zh": "高密度 EVA 泡沫轴，用于筋膜放松与训练后恢复。表面可做光面、浮点、狼牙等纹路，长度与密度可按订单设定。可印 logo、配套零售包装。",
        "f_en": ["High-density EVA, holds shape under load", "Smooth / studded / wolf-tooth surface options", "Custom length, density, colour and logo"],
        "f_zh": ["高密度 EVA，承压不易变形", "光面 / 浮点 / 狼牙多种纹路", "长度、密度、颜色与 logo 均可定制"],
        "ap_en": "For gyms, physio and recovery studios, sports brands and private-label fitness ranges.",
        "ap_zh": "适合健身房、理疗与恢复工作室、运动品牌及贴牌健身产品线。",
    },
    "fascia_gun": {
        "desc_en": "Cordless percussion massage gun, {size}. Speed levels, head set, colour and branding are configured to your market.",
        "desc_zh": "充电式筋膜枪，{size}。档位、按摩头配置、颜色与品牌标识按目标市场定制。",
        "ov_en": "A rechargeable percussion massager for pre-workout activation and post-workout recovery. Multiple speed levels and interchangeable heads come as standard, and the unit ships with your logo, colour and retail box.",
        "ov_zh": "充电式筋膜枪，用于训练前激活与训练后恢复。多档位、可换按摩头为标准配置，机身可印 logo，颜色与零售包装按你的要求做。",
        "f_en": ["Multiple speed levels, interchangeable heads", "Rechargeable cordless body", "Custom colour, logo and retail packaging"],
        "f_zh": ["多档位、可更换按摩头", "充电无绳机身", "颜色、logo 与零售包装可定制"],
        "ap_en": "For sports recovery brands, gym chains and consumer-electronics private label.",
        "ap_zh": "适合运动恢复品牌、连锁健身房与消费电子贴牌。",
    },
    "fascia_ball": {
        "desc_en": "Massage and fascial release ball, {size}. Surface texture, hardness and colour are set per order.",
        "desc_zh": "筋膜放松球，{size}。表面纹路、硬度与颜色按订单定制。",
        "ov_en": "Small-format release balls for trigger-point work on feet, shoulders and hips. Smooth and textured versions are available, packed as single units or colour sets.",
        "ov_zh": "用于足底、肩背与髋部激痛点放松的小型按摩球。可选光面或浮点，单颗或成套出货。",
        "f_en": ["Smooth and textured surfaces", "Single units or multi-colour sets", "Custom density and colour"],
        "f_zh": ["光面与浮点两种表面", "可单颗或成套出货", "密度与颜色可定制"],
        "ap_en": "For studios, physio clinics, sports brands and set-based retail.",
        "ap_zh": "适合工作室、理疗机构、运动品牌及套装类零售。",
    },
    "massage": {
        "desc_en": "Handheld massage roller, {size}. Handle, roller geometry and branding are made to your spec.",
        "desc_zh": "手持按摩棒，{size}。握柄、滚轮结构与品牌标识按你的规格定制。",
        "ov_en": "Handheld rollers and sticks for self-myofascial release on legs, back and shoulders. Spiral, beaded and dual-head geometries cover a range of pressure preferences.",
        "ov_zh": "用于腿部、背部与肩部自我筋膜放松的手持按摩棒。螺旋、串珠、双头等不同滚轮结构，覆盖不同力度偏好。",
        "f_en": ["Spiral, beaded and dual-head geometries", "PP handle with stainless-steel or silicone roller", "Custom colour and logo"],
        "f_zh": ["螺旋 / 串珠 / 双头多种结构", "PP 握柄配不锈钢或硅胶滚轮", "颜色与 logo 可定制"],
        "ap_en": "For recovery brands, gym retail walls and physio supply.",
        "ap_zh": "适合恢复类品牌、健身房零售区与理疗供应。",
    },
    "band": {
        "desc_en": "Resistance band, {size}, {mat}. Resistance level, colour coding and logo print are set per order.",
        "desc_zh": "弹力带，{size}，{mat}。阻力档位、颜色编码与 logo 印刷按订单定制。",
        "ov_en": "TPE, silicone and latex resistance bands and tubes, colour-coded by resistance level. Supplied as single bands, sets, or with handles and door anchors.",
        "ov_zh": "TPE、硅胶与乳胶材质的弹力带与阻力管，按阻力档位做颜色编码。可单条、成套，或配把手与门扣出货。",
        "f_en": ["TPE, silicone and latex options", "Colour-coded resistance levels", "Single bands, sets, handles and door anchors"],
        "f_zh": ["TPE / 硅胶 / 乳胶可选", "按阻力档做颜色编码", "可单条、成套，或配把手与门扣"],
        "ap_en": "For fitness brands, home-gym retail, rehab supply and promotional sets.",
        "ap_zh": "适合健身品牌、家用健身零售、康复供应与促销套装。",
    },
    "yoga_ball": {
        "desc_en": "Anti-burst yoga ball, {size}. Diameter, colour and print are made to your order.",
        "desc_zh": "防爆瑜伽球，{size}。直径、颜色与印刷按订单定制。",
        "ov_en": "PVC anti-burst ball for balance, core and pre-natal work. Supplied with a hand pump, in a range of diameters with your logo printed.",
        "ov_zh": "PVC 防爆瑜伽球，用于平衡、核心与孕产训练。配手打气筒，多种直径可选，可印 logo。",
        "f_en": ["Anti-burst PVC construction", "Multiple diameters available", "Hand pump included, logo printable"],
        "f_zh": ["防爆 PVC 结构", "多种直径可选", "配手打气筒，可印 logo"],
        "ap_en": "For studios, gyms, rehab clinics and retail.",
        "ap_zh": "适合瑜伽馆、健身房、康复机构与零售。",
    },
    "yoga_bag": {
        "desc_en": "Yoga mat and kit bag, {size}. Fabric, size and branding are made to your spec.",
        "desc_zh": "瑜伽垫与装备收纳包，{size}。面料、尺寸与品牌标识按你的要求定制。",
        "ov_en": "Carry bags for mats, blocks and small props, in cotton, canvas or Oxford fabric. Size, colour and logo method are set per order.",
        "ov_zh": "用于装瑜伽垫、瑜伽砖与小型配件的收纳包，可做棉、帆布或牛津布。尺寸、颜色与 logo 工艺按订单定制。",
        "f_en": ["Cotton, canvas or Oxford fabric", "Fits mats, blocks and small props", "Custom size, colour and logo"],
        "f_zh": ["棉 / 帆布 / 牛津布可选", "可装瑜伽垫、瑜伽砖与小配件", "尺寸、颜色与 logo 可定制"],
        "ap_en": "For studios, retail lines and branded kit programmes.",
        "ap_zh": "适合瑜伽馆、零售线与品牌套装项目。",
    },
    "yoga_bolster": {
        "desc_en": "Yoga bolster, {size}. Filling firmness, fabric and branding are set per order.",
        "desc_zh": "瑜伽抱枕，{size}。填充硬度、面料与品牌标识按订单定制。",
        "ov_en": "Rectangular bolster for restorative and yin practice, filled for firm support and covered in washable fabric with a hidden zip.",
        "ov_zh": "用于修复瑜伽与阴瑜伽的矩形抱枕，填充支撑稳，外套可拆洗，配隐藏式拉链。",
        "f_en": ["Firm support filling, removable washable cover", "Hidden zip, custom fabric and colour", "Logo embroidery or print available"],
        "f_zh": ["填充支撑稳，外套可拆洗", "隐藏式拉链，面料与颜色可定制", "可刺绣或印刷 logo"],
        "ap_en": "For studios, wellness retail and hospitality supply.",
        "ap_zh": "适合瑜伽馆、健康生活零售与酒店配套。",
    },
    "block": {
        "desc_en": "EVA yoga block and cover, {size}, {mat}. Colour, logo and packaging are made to your order.",
        "desc_zh": "EVA 瑜伽砖及砖套，{size}，{mat}。颜色、logo 与包装按订单定制。",
        "ov_en": "EVA foam blocks for support and alignment work, with silicone covers sold separately or as a set. Both take your colour and logo.",
        "ov_zh": "辅助与正位练习用的 EVA 瑜伽砖，可单售或配硅胶砖套成套出货。两者都可做颜色与 logo。",
        "f_en": ["Lightweight EVA, no sharp edges", "Matching silicone covers available", "Custom colour, logo and packaging"],
        "f_zh": ["轻质 EVA，边缘无毛刺", "可配同色硅胶砖套", "颜色、logo 与包装可定制"],
        "ap_en": "For studios, retail and branded prop sets.",
        "ap_zh": "适合瑜伽馆、零售与品牌辅具套装。",
    },
    "ring": {
        "desc_en": "Pilates and yoga ring, {size}, {mat}. Resistance, colour and branding are set per order.",
        "desc_zh": "普拉提圈与瑜伽圈，{size}，{mat}。阻力、颜色与品牌标识按订单定制。",
        "ov_en": "Magic-circle style rings for inner-thigh, arm and core work. Rigid or flexible construction, with padded grips and your colour and logo.",
        "ov_zh": "用于大腿内侧、手臂与核心训练的魔力圈。硬质或弹性结构可选，配软握把，可做颜色与 logo。",
        "f_en": ["Rigid and flexible constructions", "Padded grips, 22–40 cm sizes", "Custom resistance, colour and logo"],
        "f_zh": ["硬质与弹性结构可选", "软握把，22–40 cm 规格", "阻力、颜色与 logo 可定制"],
        "ap_en": "For Pilates studios, gyms and equipment distributors.",
        "ap_zh": "适合普拉提馆、健身房与器械经销商。",
    },
    "stretch_board": {
        "desc_en": "Stretch board, {size}, {mat}. Angle positions, colour and branding are made to your spec.",
        "desc_zh": "拉伸板，{size}，{mat}。角度档位、颜色与品牌标识按你的规格定制。",
        "ov_en": "An inclined stretch board for calf, hamstring and ankle mobility work, with a non-slip surface and multiple angle positions.",
        "ov_zh": "用于小腿、腘绳肌与踝关节灵活度训练的斜向拉伸板，表面防滑，多档角度。",
        "f_en": ["Multiple angle positions", "Non-slip surface", "Custom colour and logo"],
        "f_zh": ["多档角度可选", "表面防滑", "颜色与 logo 可定制"],
        "ap_en": "For gyms, physio use and home-fitness retail.",
        "ap_zh": "适合健身房、理疗使用与家用健身零售。",
    },
}

# slug, EN title, ZH title, family, section, base price (FOB Xiamen USD, None = 不放价)
ROWS = [
    # --- 泡沫轴 / 瑜伽柱 ---
    ("foam-roller", "EVA Foam Roller Set", "EVA 泡沫轴套装", "roller", "rollers", 2.52),
    ("foam-roller-2", "EVA Foam Roller — Pink", "EVA 浮点泡沫轴（粉色）", "roller", "rollers", 2.52),
    ("foam-roller-3", "EVA Foam Roller — Purple", "EVA 浮点泡沫轴（紫色）", "roller", "rollers", 2.52),
    ("eva-foam-roller", "EVA Wave Foam Roller", "EVA 波浪纹泡沫轴", "roller", "rollers", 2.52),
    ("eva-foam-roller-2", "EVA Foam Roller 33 / 45 cm", "EVA 泡沫轴 33 / 45 cm", "roller", "rollers", 2.52),
    ("vibrating-foam-roller", "Vibrating Foam Roller", "震动泡沫轴", "roller", "rollers", 2.52),
    ("vibrating-yoga-roller", "Vibrating Yoga Roller", "震动瑜伽柱", "roller", "rollers", 2.52),
    ("advanced-yoga-roller", "Advanced Yoga Roller", "升级款瑜伽柱", "roller", "rollers", 2.52),
    # --- 筋膜枪 ---
    ("fascia-gun", "Fascia Gun (White)", "筋膜枪（白色）", "fascia_gun", "rollers", None),
    ("fascia-gun-1", "Fascia Gun (T-Shape)", "筋膜枪 T 型", "fascia_gun", "rollers", None),
    ("fascia-gun-2", "Fascia Gun (Ring Grip)", "环形握把筋膜枪", "fascia_gun", "rollers", None),
    ("fascia-gun-3", "Fascia Gun (Pro)", "专业款筋膜枪", "fascia_gun", "rollers", None),
    # --- 筋膜球 ---
    ("fascial-sphere-1", "Fascial Sphere (Textured)", "浮点筋膜球", "fascia_ball", "rollers", None),
    ("fascial-sphere-2", "Fascial Sphere (Smooth)", "光面筋膜球", "fascia_ball", "rollers", None),
    ("fascial-sphere-3", "Fascial Sphere Set (6 Colours)", "筋膜球套装（6 色）", "fascia_ball", "rollers", None),
    # --- 按摩棒 / 按摩器 ---
    ("massage-stick", "Massage Stick 34 cm", "按摩棒 34 cm", "massage", "rollers", None),
    ("massage-stick-2", "Massage Stick 32 cm", "按摩棒 32 cm", "massage", "rollers", None),
    ("massager-1", "Spiral Massage Roller", "螺旋按摩棒", "massage", "rollers", None),
    ("massager-2", "Dual-Head Massage Stick", "双头按摩棒", "massage", "rollers", None),
    ("massager-3", "Beaded Massage Roller", "串珠按摩棒", "massage", "rollers", None),
    ("circular-leg-clamps", "Circular Leg Massager", "环形腿部按摩器", "massage", "rollers", None),
    # --- 弹力带 / 阻力带 ---
    ("resistance-band", "Silicone Resistance Band", "硅胶弹力带", "band", "bands", None),
    ("resistance-band-2", "TPE Resistance Band", "TPE 弹力带", "band", "bands", 3.50),
    ("resistance-tube", "Resistance Tube", "阻力管", "band", "bands", 3.50),
    ("resistance-tube-2", "Resistance Tube — With Handles", "阻力管（带把手）", "band", "bands", 3.50),
    ("power-band", "Power Band", "力量带", "band", "bands", 3.50),
    ("exercise-bands", "Exercise Bands Set", "训练弹力带套装", "band", "bands", 5.80),
    ("tpe-resistance-loop-band", "TPE Resistance Loop Band", "TPE 环形弹力带", "band", "bands", 3.50),
    ("figure-8-resistance-bands", "Figure 8 Resistance Bands", "8 字弹力带", "band", "bands", 3.50),
    ("foot-pedal-resistance-band", "Foot Pedal Resistance Band", "脚踏式弹力带", "band", "bands", 3.50),
    # --- 瑜伽配件 ---
    ("yoga-ball", "Anti-Burst Yoga Ball", "防爆瑜伽球", "yoga_ball", "props", 3.70),
    ("yoga-bag", "Yoga Bag", "瑜伽包", "yoga_bag", "props", None),
    ("yoga-bolster", "Yoga Bolster", "瑜伽抱枕", "yoga_bolster", "props", None),
    ("eva-yoga-block", "EVA Yoga Block", "EVA 瑜伽砖", "block", "props", 1.42),
    ("yoga-block-cover", "Yoga Block Cover", "瑜伽砖套", "block", "props", None),
    # --- 普拉提圈 / 瑜伽圈 ---
    ("pilates-ring", "Silicone Pilates Ring", "硅胶普拉提圈", "ring", "props", 6.40),
    ("pilates-ring-2", "Pilates Ring 40 cm", "普拉提圈 40 cm", "ring", "props", 1.90),
    ("abs-yoga-ring", "ABS Yoga Ring", "ABS 瑜伽圈", "ring", "props", 1.90),
    ("yoga-ring", "TPE Yoga Ring", "TPE 瑜伽圈", "ring", "props", 1.90),
    # --- 拉伸 ---
    ("stretch-board", "Stretch Board", "拉伸板", "stretch_board", "props", None),
]


def build_jsonld(title_en, desc_en, url, imgs, base, sect_key):
    cat_en = SECT[sect_key][0]
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
            {"@type": "ListItem", "position": 3, "name": cat_en, "item": DOMAIN + "/products.html#" + sect_key},
            {"@type": "ListItem", "position": 4, "name": title_en, "item": url},
        ],
    })
    return json.dumps({"@context": "https://schema.org", "@graph": g}, ensure_ascii=False, indent=2)


def main():
    dry = "--dry-run" in sys.argv
    ver = "20260911a"
    m = re.search(r"styles\.css\?v([A-Za-z0-9]+)",
                  open(os.path.join(ROOT, "products", "ym1.html"), encoding="utf-8").read())
    if m:
        ver = m.group(1)

    cat = {p["slug"]: p for p in json.load(open(CATALOG, encoding="utf-8"))}
    items = []
    for slug, t_en, t_zh, fam, sect, base in ROWS:
        p = cat.get(slug)
        if not p:
            print("  [缺数据]", slug)
            continue
        items.append({
            "src": slug, "new": slug, "title_en": t_en, "title_zh": t_zh,
            "fam": fam, "sect": sect, "base": base,
            "specs": p["specs"], "imgs": p["images"],
        })

    print("第二批待生成：%d 页（带报价 %d / 不带 %d）"
          % (len(items), sum(1 for i in items if i["base"]), sum(1 for i in items if not i["base"])))
    if dry:
        for i in items:
            print("  %-36s %-34s %-12s %-9s %s"
                  % (i["new"], i["title_en"][:34], i["fam"], i["sect"], i["base"] or "-"))
        return

    # slug 冲突（与现有页）
    clash = [i["new"] for i in items
             if os.path.exists(os.path.join(ROOT, "products", i["new"] + ".html"))]
    if clash:
        print("  ⚠ 已存在同名页，将被覆盖：", clash)

    # 1) 图片入库
    idmap, ok_img, noimg, imgclash = {}, 0, [], []
    for it in items:
        srcs = []
        for n, _u in enumerate(it["imgs"][:MAX_IMAGES], 1):
            s = os.path.join(STAGE, "%s-%d.webp" % (it["src"], n))
            if os.path.exists(s):
                srcs.append(s)
        if not srcs:
            noimg.append(it["src"])
        names = []
        for n, s in enumerate(srcs, 1):
            d = "%s-%d.webp" % (it["new"], n)
            tgt = os.path.join(IMGDIR, d)
            if os.path.exists(tgt):
                imgclash.append(d)
            shutil.copyfile(s, tgt)
            names.append(d)
            ok_img += 1
        idmap[it["src"]] = names
    print("图片入库：%d 张" % ok_img)
    if noimg:
        print("  无图：" + ", ".join(noimg))
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
        fill_en = {"size": size or "made to your size", "thk": (specs.get("Thickness") or "").strip(),
                   "mat": (specs.get("Material") or "").strip() or "made to order"}
        fill_zh = {"size": size or "尺寸按需定制", "thk": (specs.get("Thickness") or "").strip(),
                   "mat": (specs.get("Material") or "").strip() or "按需定制"}
        f_en = "".join("<li>" + esc(esc(b)) + "</li>" for b in cp["f_en"])
        f_zh = "".join("<li>" + esc(b) + "</li>" for b in cp["f_zh"])
        desc_en = cp["desc_en"].format(**fill_en)
        desc_zh = cp["desc_zh"].format(**fill_zh)

        url = "%s/products/%s.html" % (DOMAIN, it["new"])
        thumbs = []
        for n, nm in enumerate(names):
            cls = "pd-thumb active" if n == 0 else "pd-thumb"
            thumbs.append('<button type="button" class="%s"><img src="../assets/img/%s" width="480" height="480" loading="lazy" alt="%s"></button>'
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
                '<a class="prod-card" href="../products/%s.html"><div class="ph"><img src="../assets/img/%s" width="480" height="480" loading="lazy" alt="%s"></div>'
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
            ("@@SPECROWS@@", spec_rows(specs, fam)),
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


if __name__ == "__main__":
    main()
