#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补 6 个「品类通用款」产品页 —— 英文站的空壳页（content 空、0 条规格）。

这 6 个是英文站 167 款里**从未建页**的品类基础词，也是唯一还被漏掉的有图产品：
  ab-wheel / adjustable-dumbbell / jump-rope / kettlebell / suspension-training / vibration-machine

⚠️ 两个 slug 做了改名，原因不是 SEO 而是**图片名撞车**：
  英文站 slug `jump-rope`  →  本站 `beaded-jump-rope`
  英文站 slug `kettlebell` →  本站 `color-kettlebell`
  因为站内 assets/img/ 已存在 `jump-rope-1.webp`（被 21 处卡片引用）与
  `kettlebell-1.webp`。若沿用原名，新页图集会以同名覆盖这两个文件
  （违反「旧图不删不覆盖」）。实测两图与英文站同名图不是同一张
  （32×32 平均通道差 MAD 25.5 / 67.2），确实是不同素材，不能顶替。
  改名后还能顺带跟分类页 `jump-ropes.html`（复数）区分开。

⚠️ 规格：这 6 个在英文站是空壳（specs 全空），**只出兜底 3 行**
  （Thickness customizable / MOQ 100 pcs / Compliance），绝不编造数值。

图片来源：/tmp/probe_b4_common/<英文站slug>/<k>.webp
  由 dl_common_products.py 经 images.weserv.nl 代理下载（英文站直连被 Cloudflare 限流）。

用法：
  python3 i18n_build/build_common_products.py --dry-run
  python3 i18n_build/build_common_products.py
"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
STAGE = "/tmp/probe_b4_common"
IMGDIR = os.path.join(ROOT, "assets", "img")
CATALOG = os.path.join(ROOT, "outputs", "sf_catalog_full.json")
CARDS = os.path.join(ROOT, "outputs", "product_cards.json")
OUTJSON = os.path.join(ROOT, "outputs", "batch4_common_pages.json")

DOMAIN = "https://fjsanfan.com"
MOQ = "100 pcs"
CERT = "ROHS / CE / ISO 9001 / BSCI / REACH"
STYLEVER = "20260912c"               # 兜底；实际从已有页面正则取

# ---------------------------------------------------------------- 复用第一批骨架
_core = open(os.path.join(HERE, "build_batch1.py"), encoding="utf-8").read().split("def main():")[0]
_ns = {"__file__": os.path.join(HERE, "build_batch1.py"), "__name__": "batch1_core"}
exec(compile(_core, "batch1_core", "exec"), _ns)          # noqa: S102
esc = _ns["esc"]
spec_rows = _ns["spec_rows"]                              # 空壳 → 3 行兜底（含 clean_thk）
HEAD = (_ns["HEAD"]
        .replace("Yoga Mats", "@@CATEN@@")
        .replace("瑜伽垫", "@@CATZH@@"))

# 分类（key 与 category_map.py 一致）
SECT = {
    "strength-training": ("Strength &amp; Fitness", "力量与健身"),
    "jump-ropes": ("Jump Ropes", "跳绳"),
    "massage-recovery": ("Massage &amp; Recovery", "按摩与放松恢复"),
}

# ---------------------------------------------------------------- 文案族（对着实拍图写）
COPY = {
    "ab_wheel": {
        "desc_en": "Double-wheel ab roller with padded grips and a foam knee mat. Wheel colour, "
                   "grip and branding are set to your order.",
        "desc_zh": "双轮健腹轮，配防滑握把与发泡训练膝垫。轮体颜色、握把与品牌标识按订单定制。",
        "ov_en": "A twin-wheel roller keeps the track straight through the roll-out — the spacing "
                 "between the two wheels is what stops the sideways wobble beginners fight with. "
                 "Padded grips, wide tread, and the set ships with a knee mat so it can go straight "
                 "onto a retail shelf.",
        "ov_zh": "双轮结构让滚出轨迹保持笔直——两轮间距正是抑制侧向晃动、让新手也能稳住的关键。"
                 "加宽轮面配包胶握把，成套附发泡膝垫，可直接上零售货架。",
        "f_en": ["Twin wheels — straighter track, less wobble", "Wide tread with padded grips",
                 "Knee mat included", "Wheel colour and logo customisable"],
        "f_zh": ["双轮结构，轨迹更直、晃动更小", "加宽轮面，包胶握把",
                 "随附训练膝垫", "轮体颜色与 logo 可定制"],
        "ap_en": "For core-training programmes, home-fitness retail and promotional bundles.",
        "ap_zh": "适合核心训练项目、家用健身零售与促销套装。",
    },
    "adj_dumbbell": {
        "desc_en": "Dial-adjustable dumbbell with a moulded cradle and colour-coded locking plates. "
                   "Load range, plate colour and branding are configured to your market.",
        "desc_zh": "旋钮式可调哑铃，配成型底座与撞色锁定片。重量区间、配重片颜色与品牌标识按目标市场定制。",
        "ov_en": "One dumbbell replaces a whole rack. The dial selects the load and the plates stay "
                 "seated in the cradle, so changing weight between sets is a single turn rather than "
                 "a walk to the rack. The red locking collar doubles as a visual indicator that the "
                 "plate is fully engaged. Ships singly or as a pair on a branded cradle.",
        "ov_zh": "一只替代一整排。旋钮选重，配重片固定在底座内，组间换重只需转一下、不用走去换铃。"
                 "红色锁扣同时是「已锁定到位」的视觉标识。可单只出货，或配品牌底座成对出货。",
        "f_en": ["Dial selection — no loose plates to load", "Locking collar shows the plate is engaged",
                 "Moulded cradle holds the plates between sets", "Plate colour and logo customisable"],
        "f_zh": ["旋钮选重，无需手工装卸配重片", "锁扣可见，确认配重片已到位",
                 "成型底座固定配重片，便于收纳", "配重片颜色与 logo 可定制"],
        "ap_en": "For home-gym retail, apartment training and e-commerce lines.",
        "ap_zh": "适合家用健身零售、公寓场景训练与电商产品线。",
    },
    "beaded_rope": {
        "desc_en": "Beaded jump rope with moulded character handles. Bead colour, rope length and "
                   "branding are made to your order.",
        "desc_zh": "珠节跳绳，配造型握把头。珠节颜色、绳长与品牌标识按订单定制。",
        "ov_en": "Segmented plastic beads hold the rope in an even arc in the air, which makes it far "
                 "more forgiving for beginners than a wire speed rope — and it will not kink when a "
                 "child drops it. The moulded handles take a character head, so this is the version "
                 "that sells to schools, kids' programmes and gift retail.",
        "ov_zh": "分段塑料珠节让绳体在空中保持稳定弧度，比钢丝速度绳宽容得多，孩子脱手掉在地上也不打结。"
                 "握把可做造型头，是适合学校、儿童课程与礼赠零售渠道的款式。",
        "f_en": ["Segmented beads keep a stable arc", "Moulded character handles",
                 "Beginner-friendly and kink-resistant", "Bead colour, length and logo customisable"],
        "f_zh": ["分段珠节，弧度稳定", "造型握把头",
                 "初学者友好，落地不易打结", "珠节颜色、绳长与 logo 可定制"],
        "ap_en": "For schools, kids' programmes, gift retail and family fitness lines.",
        "ap_zh": "适合学校、儿童课程、礼赠零售与家庭健身产品线。",
    },
    "kettlebell": {
        "desc_en": "Color-coated kettlebell with a wide chamfered handle and contrast weight print. "
                   "Weight, colour and branding are set to your programme.",
        "desc_zh": "彩色包覆壶铃，加宽倒角握把，铃面撞色重量印字。重量、颜色与品牌标识按你的项目定制。",
        "ov_en": "A cast-iron bell with a smooth color coating and a wide, chamfered handle that stays "
                 "easy on the forearm through cleans and snatches. Weight is printed on the face in a "
                 "contrast colour so a full set stays readable on the rack, and colour can be used to "
                 "code weight bands across a studio floor.",
        "ov_zh": "铸铁铃体配顺滑彩色包覆，握把加宽并做倒角，做翻铃与抓举时不硌前臂。重量以撞色印在铃面，"
                 "成套陈列一眼可辨；也可用颜色区分重量档，方便馆内分区管理。",
        "f_en": ["Color-coated cast iron, smooth finish", "Wide chamfered handle",
                 "Contrast weight print on the face", "Color-coded weight bands, logo available"],
        "f_zh": ["彩色包覆铸铁，表面顺滑", "加宽倒角握把",
                 "铃面撞色重量印字", "可用颜色区分重量档，支持 logo"],
        "ap_en": "For studio strength corners, home-fitness retail and functional-training programmes.",
        "ap_zh": "适合瑜伽馆力量区、家用健身零售与功能性训练项目。",
    },
    "suspension": {
        "desc_en": "Suspension training kit with door anchor, padded handles, foot cradles and carry "
                   "bag. Strap colour and branding are set per order.",
        "desc_zh": "悬吊训练套装，含门锚、包胶握把、足环与收纳袋。织带颜色与品牌标识按订单定制。",
        "ov_en": "Anchors to a door, a beam or a tree branch, and turns bodyweight into a fully "
                 "adjustable load — no rack, no plates, no floor space. The kit ships complete: main "
                 "straps with stitched adjustment marks, padded handles, foot cradles, door anchor, "
                 "mesh carry bag, printed workout guide and a branded color box.",
        "ov_zh": "可固定在门、横梁或树枝上，把自重变成可无级调节的负荷——不需要器械架、不需要配重片、"
                 "几乎不占地。整套发货：主带带缝线刻度、包胶握把、足环、门锚、网眼收纳袋、"
                 "纸质训练指南与品牌彩盒。",
        "f_en": ["Anchors to door, beam or tree branch", "Main straps with stitched adjustment marks",
                 "Padded handles and foot cradles included", "Complete kit: bag, guide and color box"],
        "f_zh": ["可固定于门 / 横梁 / 树枝", "主带带缝线刻度，长度可无级调节",
                 "含包胶握把与足环", "整套含收纳袋、训练指南与彩盒"],
        "ap_en": "For home-gym retail, personal-training studios, hotel gyms and e-commerce lines.",
        "ap_zh": "适合家用健身零售、私教工作室、酒店健身房与电商产品线。",
    },
    "vibration": {
        "desc_en": "Vibration plate with remote control and LCD programme display. Colour and branding "
                   "are configured to your market.",
        "desc_zh": "振动踏板，配遥控器与 LCD 程序显示。颜色与品牌标识按目标市场定制。",
        "ov_en": "Standing vibration for circulation, balance work and light toning — a low-impact "
                 "piece for the home audience that will not use a treadmill. Anti-slip moulded deck, "
                 "LCD programme and speed display, and a remote so settings can be changed without "
                 "stepping off.",
        "ov_zh": "站立式振动用于循环、平衡与轻度塑形，属低冲击器械，适合不跑步、不上跑步机的家庭用户。"
                 "防滑立体纹踏板、LCD 程序与速度显示，配遥控器，不必下机即可调档。",
        "f_en": ["Anti-slip moulded deck", "LCD programme and speed display",
                 "Remote control included", "Low-impact, compact footprint"],
        "f_zh": ["防滑立体纹踏板", "LCD 程序与速度显示",
                 "随附遥控器", "低冲击、占地小"],
        "ap_en": "For home-fitness retail, wellness and recovery lines, and e-commerce brands.",
        "ap_zh": "适合家用健身零售、健康与恢复产品线，以及电商品牌。",
    },
}

# src(英文站 slug), new(本站页 slug), EN title, ZH title, COPY 族, 分类
ROWS = [
    ("ab-wheel", "ab-wheel", "Ab Wheel", "健腹轮",
     "ab_wheel", "strength-training"),
    ("adjustable-dumbbell", "adjustable-dumbbell", "Adjustable Dumbbell", "可调式哑铃",
     "adj_dumbbell", "strength-training"),
    ("jump-rope", "beaded-jump-rope", "Beaded Jump Rope", "珠节跳绳",
     "beaded_rope", "jump-ropes"),
    ("kettlebell", "color-kettlebell", "Color Kettlebell", "彩色壶铃",
     "kettlebell", "strength-training"),
    ("suspension-training", "suspension-training", "Suspension Training Kit", "悬吊训练套装",
     "suspension", "strength-training"),
    ("vibration-machine", "vibration-machine", "Vibration Plate", "振动踏板",
     "vibration", "massage-recovery"),
]

SECT_PAGE = {                       # 分类页文件 → 用于抓同分类的 related 卡片
    "strength-training": "strength-training.html",
    "jump-ropes": "jump-ropes.html",
    "massage-recovery": "massage-recovery.html",
}


def build_jsonld(title_en, desc_en, url, imgs, sect_key):
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


def related_cards(sect_key, exclude, n=4):
    """从该分类页现成的卡片里挑 related —— 用 product_cards.json 的片段，只改相对路径。"""
    page = os.path.join(ROOT, SECT_PAGE[sect_key])
    if not os.path.exists(page):
        return ""
    html = open(page, encoding="utf-8").read()
    pool = []
    for m in re.finditer(r'<a class="prod-card" href="products/([a-z0-9\-]+)\.html"', html):
        s = m.group(1)
        if s not in exclude and s not in pool:
            pool.append(s)
    cards = json.load(open(CARDS, encoding="utf-8"))
    out = []
    for s in pool[:n]:
        c = cards.get(s)
        if not c:
            continue
        out.append(c.replace('href="products/', 'href="../products/')
                    .replace('src="assets/img/', 'src="../assets/img/'))
    return "".join(out)


def main():
    dry = "--dry-run" in sys.argv
    ver = STYLEVER
    m = re.search(r"styles\.css\?v([A-Za-z0-9]+)",
                  open(os.path.join(ROOT, "products", "ym1.html"), encoding="utf-8").read())
    if m:
        ver = m.group(1)

    cat = {p["slug"]: p for p in json.load(open(CATALOG, encoding="utf-8"))}
    items = []
    for src, new, t_en, t_zh, fam, sect in ROWS:
        p = cat.get(src)
        if not p:
            print("  [缺数据]", src)
            continue
        items.append({"src": src, "new": new, "title_en": t_en, "title_zh": t_zh,
                      "fam": fam, "sect": sect, "specs": p.get("specs") or {},
                      "imgs": p.get("images") or []})

    print("待生成：%d 页（版本 %s）" % (len(items), ver))
    for it in items:
        nsp = sum(1 for k, v in it["specs"].items() if v and not k.startswith("X:"))
        print("  %-24s %-30s %-18s 英文站规格 %d 条"
              % (it["new"], it["title_en"], it["sect"], nsp))

    if dry:
        return

    clash = [i["new"] for i in items
             if os.path.exists(os.path.join(ROOT, "products", i["new"] + ".html"))]
    if clash:
        print("  ⚠ 已存在同名页，将被覆盖：", clash)

    # 1) 图片入库（同名即冲突，必须报出来 —— 这批最容易踩的就是这个）
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
        print("  ⚠⚠ 覆盖了同名旧图（本该为 0，请检查）：", imgclash)

    # 2) 写出页面
    written = 0
    for it in items:
        names = idmap.get(it["src"]) or []
        if not names:
            print("  [跳过，无图]", it["new"])
            continue
        cp, sect, specs = COPY[it["fam"]], it["sect"], it["specs"]
        url = "%s/products/%s.html" % (DOMAIN, it["new"])

        thumbs = []
        for n, nm in enumerate(names):
            cls = "pd-thumb active" if n == 0 else "pd-thumb"
            thumbs.append('<button type="button" class="%s"><img src="../assets/img/%s" '
                          'width="480" height="480" loading="lazy" alt="%s"></button>'
                          % (cls, nm, esc(it["title_en"])))

        wa_en = ("Hi%20SANFAN%2C%20I%20am%20interested%20in%20" +
                 it["title_en"].replace(" ", "%20").replace("&", "%26").replace("/", "%2F"))
        wa_zh = ("%E4%BD%A0%E5%A5%BD%E4%B8%89%E6%A2%B5%EF%BC%8C%E6%88%91%E6%83%B3%E4%BA%86%E8%A7%A3%20" +
                 it["title_zh"].replace(" ", "%20"))

        html = HEAD
        for k, v in [
            ("@@VER@@", ver),
            ("@@TITLEZH@@", esc(it["title_zh"])),
            ("@@TITLE@@", esc(it["title_en"])),
            ("@@DESC@@", esc(cp["desc_en"][:300])),
            ("@@URL@@", url),
            ("@@OGIMG@@", DOMAIN + "/assets/img/" + names[0]),
            ("@@JSONLD@@", build_jsonld(it["title_en"], cp["desc_en"], url,
                                        [DOMAIN + "/assets/img/" + n for n in names], sect)),
            ("@@IMG1@@", names[0]),
            ("@@THUMBS@@", "\n          ".join(thumbs)),
            ("@@DESCEN@@", esc(cp["desc_en"])),
            ("@@DESCZH@@", esc(cp["desc_zh"])),
            ("@@WA@@", wa_en),
            ("@@WAEN@@", wa_en),
            ("@@WAZH@@", wa_zh),
            ("@@SPECROWS@@", spec_rows(specs, it["fam"])),
            ("@@OVEN@@", esc(cp["ov_en"])),
            ("@@OVZH@@", esc(cp["ov_zh"])),
            ("@@FEN@@", "".join("<li>" + esc(b) + "</li>" for b in cp["f_en"])),
            ("@@FZH@@", "".join("<li>" + esc(b) + "</li>" for b in cp["f_zh"])),
            ("@@APEN@@", esc(cp["ap_en"])),
            ("@@APZH@@", esc(cp["ap_zh"])),
            ("@@RELATED@@", related_cards(sect, {i["new"] for i in items})),
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
