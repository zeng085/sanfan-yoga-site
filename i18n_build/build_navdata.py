# -*- coding: utf-8 -*-
"""生成 assets/data/navdata.js —— 导航下拉数据 + 全站搜索索引。

为什么落成 **JS 文件而不是 JSON**：
main.js 用 <script> 标签懒加载它（首次悬停/点击搜索时才加载）。JSON 走 fetch 在
file:// 预览下会被 CORS 拦掉，classic script 不会 —— 本地预览与线上都能用。

路径一律写**站点绝对路径**（/products/x.html），这样从任意目录层级引用都不算出错。

用法
    python3 i18n_build/build_navdata.py --dry-run
    python3 i18n_build/build_navdata.py
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from apps_data import APPS  # noqa: E402
from category_map import CATS, CAT_BY_KEY, build  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "data", "navdata.js")

GROUPS = [
    ("Mats", "垫类", ["tpe-yoga-mats", "pu-rubber-yoga-mats", "suede-cork-yoga-mats",
                      "meditation-pilates-mats"]),
    ("Training", "训练", ["strength-training", "jump-ropes", "resistance-bands", "foam-rollers"]),
    ("Recovery & Props", "恢复与辅具", ["massage-recovery", "yoga-props-accessories"]),
]


# ---------------------------------------------------------------- 取中文名
def zh_dict():
    """从 main.js 的 I18N zh 块里取出 'key': '值' 映射。

    老产品卡片的标题是 data-i18n="ym1.t"，中文只存在于 JS 字典里，
    所以搜索索引要拿到中文名就得把它解析出来。字典是扁平的字符串表，
    用花括号配平找到 zh 块的范围即可，不需要真的解析 JS。
    """
    src = open(os.path.join(ROOT, "assets", "js", "main.js"), encoding="utf-8").read()
    i = src.find("  zh: {")
    if i < 0:
        return {}
    j = src.find("{", i)
    depth, k = 0, j
    while k < len(src):
        if src[k] == "{":
            depth += 1
        elif src[k] == "}":
            depth -= 1
            if depth == 0:
                break
        k += 1
    body = src[j:k]
    out = {}
    for m in re.finditer(r"'([A-Za-z0-9_.\-]+)'\s*:\s*'((?:[^'\\]|\\.)*)'", body):
        out[m.group(1)] = m.group(2).replace("\\'", "'").replace("\\\\", "\\")
    return out


def split_card(card, zhmap):
    """从卡片 HTML 取 (英文名, 中文名, 英文描述, 中文描述, 首图)。"""
    def flat(s):
        return " ".join(re.sub(r"<[^>]+>", " ", s).split())

    m = re.search(r"<h4([^>]*)>([\s\S]*?)</h4>", card)
    attrs, inner = (m.group(1), m.group(2)) if m else ("", "")
    key = re.search(r'data-i18n="([^"]+)"', attrs)
    if key:
        en, zh = flat(inner), zhmap.get(key.group(1), "")
    else:
        me = re.search(r'<span class="lang-en">([\s\S]*?)</span>', inner)
        mz = re.search(r'<span class="lang-zh">([\s\S]*?)</span>', inner)
        # 双语 span 被剥标签后中英会连在一起，所以分别取再拼
        en = flat(me.group(1)) if me else flat(inner)
        zh = flat(mz.group(1)) if mz else ""

    m = re.search(r"<p([^>]*)>([\s\S]*?)</p>", card)
    pattrs, pinner = (m.group(1), m.group(2)) if m else ("", "")
    pkey = re.search(r'data-i18n="([^"]+)"', pattrs)
    if pkey:
        den, dzh = flat(pinner), zhmap.get(pkey.group(1), "")
    else:
        me = re.search(r'<span class="lang-en">([\s\S]*?)</span>', pinner)
        mz = re.search(r'<span class="lang-zh">([\s\S]*?)</span>', pinner)
        den = flat(me.group(1)) if me else flat(pinner)
        dzh = flat(mz.group(1)) if mz else ""

    # 路径**不带前导斜杠**：main.js 会用页面相对前缀拼（'' 或 '../'），
    # 这样 file:// 本地预览与线上都能取到图/页，写死 "/assets/..." 本地必 404。
    mi = re.search(r'<img src="([^"]+)"', card)
    img = mi.group(1).lstrip("/") if mi else ""
    return en, zh, den, dzh, img


# 让「按用途」「按材质」这类词也能命中分类/页面，而不是空结果
SYNONYMS = {
    "瑜伽垫": "yoga mat", "垫子": "mat", "地垫": "mat", "mat": "瑜伽垫",
    "泡沫轴": "foam roller", "瑜伽柱": "foam roller", "滚轴": "foam roller",
    "跳绳": "jump rope", "弹力带": "resistance band", "阻力带": "resistance band",
    "筋膜枪": "fascia gun", "筋膜球": "fascia ball", "按摩": "massage",
    "瑜伽砖": "yoga block", "瑜伽球": "yoga ball", "吊床": "aerial hammock",
    "空中瑜伽": "aerial hammock", "普拉提": "pilates", "冥想": "meditation",
    "软木": "cork", "麂皮": "suede", "绒面": "suede", "橡胶": "rubber",
    "双色": "dual color", "加宽": "wide", "折叠": "foldable", "旅行": "travel",
    "儿童": "kids", "计数": "counting", "哑铃": "dumbbell", "杠铃": "barbell",
    "配重": "weighted", "健腹轮": "ab roller", "登山机": "stair climber",
    "拉伸板": "stretch board", "普拉提圈": "pilates ring", "抱枕": "bolster",
    "瑜伽包": "yoga bag", "高温瑜伽": "hot yoga", "材质对比": "materials compared",
    "瑜伽馆": "studio", "健身房": "gym", "酒店": "hotel", "贴牌": "private label",
    "亚马逊": "amazon fba", "理疗": "physio clinic",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cards = json.load(open(os.path.join(ROOT, "outputs/product_cards.json"), encoding="utf-8"))
    assign, unmapped = build()
    zhmap = zh_dict()
    print("卡片池 %d 张；中文名字典 %d 条；未归类 %d" % (len(cards), len(zhmap), len(unmapped)))

    cat_count = {c["key"]: 0 for c in CATS}
    for s, k in assign.items():
        cat_count[k] += 1

    # ------------------------------------------------ 分类
    cats = [{"k": c["key"], "en": c["en"], "zh": c["zh"],
             "n": cat_count[c["key"]], "kw": c["kw_en"] + " " + c["kw_zh"]}
            for c in CATS]
    groups = [{"en": ge, "zh": gz,
               "items": [c["key"] for c in CATS if c["key"] in keys]}
              for ge, gz, keys in GROUPS]

    # ------------------------------------------------ 场景
    apps = [{"k": a["key"], "en": a["en"], "zh": a["zh"],
             "d": a["tag_en"], "dz": a["tag_zh"]} for a in APPS]

    # ------------------------------------------------ 搜索索引
    idx = []

    for slug, card in cards.items():
        en, zh, den, dzh, img = split_card(card, zhmap)
        ck = assign.get(slug)
        c = CAT_BY_KEY[ck] if ck else None
        idx.append({
            "y": "product", "t": en, "z": zh, "u": "products/%s.html" % slug,
            "c": c["en"] if c else "", "cz": c["zh"] if c else "",
            "img": img, "k": (" ".join([den[:140], dzh[:60], c["kw_en"] if c else "",
                                        c["kw_zh"] if c else ""])).lower(),
        })

    for c in CATS:
        idx.append({"y": "category", "t": c["en"], "z": c["zh"], "u": "%s.html" % c["key"],
                    "c": "%d products" % cat_count[c["key"]],
                    "cz": "%d 款产品" % cat_count[c["key"]], "img": "",
                    "k": (c["kw_en"] + " " + c["kw_zh"] + " " + c["desc_en"]).lower()})

    for a in APPS:
        idx.append({"y": "application", "t": a["en"], "z": a["zh"],
                    "u": "applications/%s.html" % a["key"], "c": a["tag_en"], "cz": a["tag_zh"],
                    "img": "",
                    "k": (a["card_en"] + " " + a["card_zh"] + " " + a["kit_en"] + " "
                          + a["hero_en"]).lower()})

    pages = [
        ("Materials compared — TPE, PVC, PU, cork, suede", "材质对比 — TPE / PVC / PU / 软木 / 麂皮",
         "materials.html", "Guide", "指南",
         "compare tpe pvc nbr pu rubber suede cork eva epp grip durability recyclable "
         "thickness price which material best 材质 对比 区别 选哪个 哪个好 防滑 厚度 回收"),
        ("All applications — buy by use case", "全部应用场景 — 按用途选购",
         "applications/index.html", "Guide", "指南",
         "application use case buyer studio gym hotel spa private label recovery ecommerce "
         "场景 用途 采购方案"),
        ("All 141 products by category", "全部 141 款产品",
         "products.html", "Guide", "指南", "catalog all products catalogue 目录 全部产品"),
        ("About SANFAN — factory, capacity, certifications",
         "关于三梵 — 工厂、产能与认证", "/about.html", "Page", "页面",
         "about factory capacity certification iso bsci sgs production process "
         "工厂 产能 认证 生产流程 验厂"),
        ("FAQ — MOQ, sampling, lead time, shipping, OEM",
         "常见问题 — 起订量、打样、交期、运输、定制", "/faq.html", "Page", "页面",
         "faq moq minimum order sampling lead time shipping payment oem odm private label "
         "常见问题 起订量 打样 交期 运费 付款 贴牌 定制"),
        ("Contact SANFAN — WhatsApp, WeChat, email",
         "联系三梵 — WhatsApp / 微信 / 邮件", "/contact.html", "Page", "页面",
         "contact whatsapp wechat email quote inquiry 联系 报价 咨询"),
    ]
    for en, zh, u, ce, cz, kw in pages:
        idx.append({"y": "page", "t": en, "z": zh, "u": u.lstrip("/"), "c": ce, "cz": cz,
                    "img": "", "k": kw.lower()})

    data = {
        "ver": 1,
        "total": len(assign),
        "cats": cats,
        "groups": groups,
        "apps": apps,
        "syn": SYNONYMS,
        "idx": idx,
    }
    js = ("/* 自动生成，请勿手改 —— 由 i18n_build/build_navdata.py 产出 */\n"
          "window.SANFAN_NAV=%s;\n" % json.dumps(data, ensure_ascii=False, separators=(",", ":")))

    if not args.dry_run:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        open(OUT, "w", encoding="utf-8").write(js)
    print("%s assets/data/navdata.js  %d 条索引（%d 产品 / %d 分类 / %d 场景 / %d 页面）  %.1f KB"
          % ("[dry]" if args.dry_run else "生成", len(idx), len(cards), len(CATS),
             len(APPS), len(pages), len(js.encode("utf-8")) / 1024.0))
    miss = [e["t"] for e in idx if e["y"] == "product" and not e["z"]]
    if miss:
        print("  ⚠ %d 个产品缺中文名（前 5）：%s" % (len(miss), miss[:5]))


if __name__ == "__main__":
    main()
