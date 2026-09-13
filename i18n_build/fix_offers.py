# -*- coding: utf-8 -*-
"""给缺 offers 的产品页补结构化数据价格（2026-09-12）。

规则（用户 2026-09-12 拍板）：**只补有真实报价依据的，其余不编造数字**。
  有依据 → AggregateOffer，区间 = 材质族基准价 ×0.7 ~ ×1.3（与站内既有 82 页同一套口径）
  无依据 → Offer，只声明 priceCurrency / availability / 询价入口，不写 price。
          这样 GSC 的「应指定 offers、review 或 aggregateRating 之一」硬错误消失，
          只剩「缺少 price」软警告 —— 比编造一个工厂无法兑现的价格安全。

价格依据全部来自 i18n_build/data/sanfan_offer.xlsx 的 offer 页（FOB Xiamen, USD）。

用法
    python3 i18n_build/fix_offers.py --dry-run
    python3 i18n_build/fix_offers.py
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["de", "ja", "ko", "fr", "it", "es"]

# 材质族基准价（报价表 offer 页实价）
FAMILY = {
    "pu": 12.15,            # luxury YOGA mat, PU+rubber
    "cork_rubber": 10.90,   # cork rubber yoga mat
    "tpe": 5.89,            # yoga mat S1A12, TPE double layer
    "pilates": 5.90,        # pilate mat
}
# 配件类（报价表里有明确行）
ACC = [
    ("bosu", 14.87), ("dumbbell", 9.74), ("kettlebell", None),
    ("stocking", 1.70), ("yoga-ball", 3.70), ("pilates-ball", 0.90),
    ("ball", 3.70), ("cork-block", 3.85), ("block", 1.42),
    ("resistance-band", 3.50), ("band", 3.50), ("ring", 1.90),
    ("roller", 2.52),
]
# 无报价依据 → 保持询价
NO_PRICE = ("ab-wheel", "ab-roller", "stair-climber", "hammock", "jump-rope",
            "fascia-gun", "fascial-sphere", "massager", "massage-stick",
            "suspension", "vibration", "stretch-board", "fitness-board",
            "yoga-bag", "bolster", "leg-clamps")


def price_for(slug):
    """返回 (基准价 or None, 依据说明)"""
    s = slug.lower()
    for kw in NO_PRICE:
        if kw in s:
            return None, "无报价依据"
    # 垫类：按材质族归口（与 build_batch1 的 PRICE_BY_FAMILY 同源）
    if "meditation" in s or "mandala" in s or "reformer" in s:
        return FAMILY["pilates"], "pilate mat 5.90"
    if "cork" in s:
        return FAMILY["cork_rubber"], "cork rubber 10.90"
    if "suede" in s and "rubber" in s:
        return FAMILY["pu"], "PU+rubber 12.15"
    if "suede" in s and "tpe" in s:
        return FAMILY["tpe"], "TPE 5.89"
    if "rubber" in s:
        return FAMILY["pu"], "rubber/PU 12.15"
    if "pu" in s:
        return FAMILY["pu"], "PU 12.15"
    if "tpe" in s:
        return FAMILY["tpe"], "TPE 5.89"
    if "mat" in s:
        return None, "垫类但材质不明"
    for kw, v in ACC:
        if kw in s:
            return v, ("报价表 %s" % v if v else "无报价依据")
    return None, "无法归类"


def product_node(d):
    for n in (d.get("@graph") or [d]):
        if isinstance(n, dict) and n.get("@type") == "Product":
            return n
    return None


def process(path, dry):
    h = open(path, encoding="utf-8").read()
    out = h
    changed = 0
    for m in list(re.finditer(r'(<script[^>]+type="application/ld\+json"[^>]*>)(.*?)(</script>)',
                              h, re.S | re.I)):
        try:
            d = json.loads(m.group(2))
        except Exception:
            continue
        pn = product_node(d)
        if not pn or pn.get("offers"):
            continue
        lang = path.split("/")[0] if "/" in path and path.split("/")[0] in LANGS else ""
        base, why = price_for(os.path.basename(path)[:-5])
        contact = "https://fjsanfan.com/%scontact.html" % (lang + "/" if lang else "")
        if base:
            offers = {"@type": "AggregateOffer",
                      "lowPrice": round(base * 0.7, 2),
                      "highPrice": round(base * 1.3, 2),
                      "priceCurrency": "USD",
                      "url": contact}
        else:
            offers = {"@type": "Offer",
                      "priceCurrency": "USD",
                      "availability": "https://schema.org/InStock",
                      "url": contact}
        pn["offers"] = offers
        new = json.dumps(d, ensure_ascii=False, indent=2)
        out = out.replace(m.group(2), "\n" + new + "\n", 1)
        changed += 1
        if dry:
            print("  [dry] %-46s %s -> %s" % (path, why, offers.get("lowPrice", "询价")))
    if changed and not dry:
        open(path, "w", encoding="utf-8").write(out)
    return changed, why if changed else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    total = 0
    withprice = 0
    for base in [""] + LANGS:
        for f in sorted(os.listdir(os.path.join(ROOT, base, "products") if base
                                  else os.path.join(ROOT, "products"))):
            if not f.endswith(".html"):
                continue
            rel = os.path.join(base, "products", f) if base else os.path.join("products", f)
            n, why = process(rel, args.dry_run)
            total += n
            if n and "报价" in why or (n and why and why != "无报价依据" and why != "无法归类"
                                      and why != "垫类但材质不明"):
                withprice += 1
    print("%s 共处理 %d 个页面的 JSON-LD（其中带真实价格区间 %d）"
          % ("[dry]" if args.dry_run else "写入", total, withprice))


if __name__ == "__main__":
    main()
