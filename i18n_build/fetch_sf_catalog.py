#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 sanfansport.com（英文站，WordPress + WooCommerce）REST API 采集完整产品主数据。

产出：
  outputs/sf_catalog.json   结构化产品目录（规格已解析、图片已归集、类目已标注）
  outputs/sf_catalog.md     人可读主表

用法：
  python3 i18n_build/fetch_sf_catalog.py                # 全量 167
  python3 i18n_build/fetch_sf_catalog.py --batch mats   # 仅垫类家族（第一批 63）
  python3 i18n_build/fetch_sf_catalog.py --no-images    # 跳过图片页抓取（快）
  python3 i18n_build/fetch_sf_catalog.py --from-cache   # 用 /tmp 缓存不做网络请求

英文站曾因 Cloudflare IP 级限流返回 000；恢复后 REST API 完全开放：
  /wp-json/wp/v2/product?per_page=100&page=N
  /wp-json/wp/v2/product_cat?per_page=100
  /wp-json/wp/v2/media?per_page=100&page=N     （parent 字段为空，媒体不按产品关联，图片须从产品页 HTML 提取）
"""
import argparse
import glob
import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://www.sanfansport.com"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
OUTDIR = os.path.join(ROOT, "outputs")

# ── 垫类家族类目 id（第一批） ────────────────────────────────────────────────
MAT_CATS = {45, 71, 74, 125, 127, 126, 128, 131, 35}

# ── 英文站规格标签 → 本站 10 字段 的映射 ─────────────────────────────────────
LABEL_MAP = {
    "material": "Material",
    "size": "Size",
    "thickness": "Thickness",
    "weight": "Weight",
    "color": "Colors",
    "colours": "Colors",
    "feature": "Feature",
    "features": "Feature",
    "logo": "Logo",
    "packing": "Packaging",
    "package": "Packaging",
    "package size": "PackageSize",
    "carton size": "CartonSize",
    "certificate": "Compliance",
    "certification": "Compliance",
    "gender": "Gender",
    "application": "Application",
    "applicable users": "ApplicableUsers",
    "oem/odm": "OEM",
    "oem": "OEM",
    "service": "Service",
    "good for": "GoodFor",
    "rope length": "RopeLength",
    "fabric weight": "FabricWeight",
    "massage area": "MassageArea",
    "massage heads": "MassageHeads",
    "strength": "Strength",
    "wheels": "Wheels",
    "ball diameter": "BallDiameter",
    "number of rollers": "RollerCount",
    "style": "Style",
    "resistance": "Resistance",
}

# 本站规格表字段顺序（与 products/*.html 的 spec-table 一致）
SITE_ORDER = ["Material", "Size", "Thickness", "Weight", "MOQ",
              "Colors", "Feature", "Logo", "Compliance", "Packaging"]

# 图片过滤：WP 缩放变体 + 站点 logo + 装饰图
RESIZE_RE = re.compile(r"-\d{2,4}x\d{2,4}\.(?:jpg|jpeg|png|webp)$", re.I)
SKIP_RE = re.compile(r"(logo|favicon|placeholder|banner-default|loading|icon-)", re.I)


def fetch(url, tries=3, timeout=60):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA,
                "Accept": "application/json,text/html,*/*",
                "Accept-Language": "en-US,en;q=0.9",
            })
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception as e:            # noqa: BLE001
            last = e
            time.sleep(1.5 * (i + 1))
    print(f"    ! 失败 {url} : {last}")
    return None


def strip_tags(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


# ── 规格表解析 ───────────────────────────────────────────────────────────────
def parse_specs(content_html):
    """从 content.rendered 的两列表格里解析 {字段: 值}。多行值保留 <br> 语义为 ' / ' 分隔。"""
    tables = re.findall(r"<table.*?</table>", content_html or "", re.S)
    if not tables:
        return {}, []
    rows = re.findall(r"<tr>(.*?)</tr>", tables[0], re.S)
    specs, unknown = {}, []
    for r in rows:
        tds = re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)
        if len(tds) < 2:
            continue
        lab = strip_tags(tds[0]).rstrip(":").strip()
        if not lab:
            continue
        # 值：<br> 转 ' / '，去掉 nbsp
        val = re.sub(r"<br\s*/?>", " / ", tds[1])
        val = strip_tags(val).replace("\xa0", " ").strip()
        val = re.sub(r"\s*/\s*", " / ", val)
        val = re.sub(r"\s{2,}", " ", val).strip(" /")
        if not val:
            continue
        key = LABEL_MAP.get(lab.lower())
        if key is None:
            unknown.append((lab, val))
            key = "X:" + lab
        if key in specs and specs[key]:
            specs[key] += " / " + val
        else:
            specs[key] = val
    return specs, unknown


# ── 产品页图片提取 ───────────────────────────────────────────────────────────
# 关键：整页抓图会混入「页头产品下拉菜单」和「相关产品」的图。
# 真正的产品图库只存在于 div.product-gallery → div.product-info 之间。
_GALLERY_MARKERS = ('class="product-info', 'class="product-summary',
                    'product-footer', 'woocommerce-tabs')


def parse_images(page_html):
    """只取产品图库区（product-gallery → product-info）的原图。"""
    if not page_html:
        return []
    i = page_html.find('class="product-gallery')
    if i < 0:
        return []
    j = len(page_html)
    for mk in _GALLERY_MARKERS:
        k = page_html.find(mk, i)
        if k > 0:
            j = min(j, k)
    seg = page_html[i:j]
    urls = re.findall(
        r"https://www\.sanfansport\.com/wp-content/uploads/[^\"'()\s]+?\.(?:webp|jpg|jpeg|png)",
        seg)
    out = []
    for u in dict.fromkeys(urls):
        b = os.path.basename(u)
        if RESIZE_RE.search(b) or SKIP_RE.search(b):
            continue
        out.append(u)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", choices=["all", "mats"], default="all")
    ap.add_argument("--no-images", action="store_true")
    ap.add_argument("--from-cache", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default="sf_catalog")
    args = ap.parse_args()

    os.makedirs(OUTDIR, exist_ok=True)

    # 1) 产品列表
    if args.from_cache and os.path.exists("/tmp/sf_products.json"):
        prods = json.load(open("/tmp/sf_products.json", encoding="utf-8"))
        print(f"[缓存] 产品 {len(prods)} 个")
    else:
        prods = []
        for pg in (1, 2, 3):
            raw = fetch(f"{BASE}/wp-json/wp/v2/product?per_page=100&page={pg}"
                        "&_fields=id,slug,date,modified,link,title,content,excerpt,"
                        "featured_media,product_cat,product_tag")
            if not raw:
                break
            try:
                page = json.loads(raw)
            except Exception:                                   # noqa: BLE001
                break
            if not isinstance(page, list) or not page:
                break
            prods += page
        json.dump(prods, open("/tmp/sf_products.json", "w", encoding="utf-8"),
                  ensure_ascii=False)
        print(f"[抓取] 产品 {len(prods)} 个")

    # 2) 类目表
    if args.from_cache and os.path.exists("/tmp/sf_cats.json"):
        cats = json.load(open("/tmp/sf_cats.json", encoding="utf-8"))
    else:
        raw = fetch(f"{BASE}/wp-json/wp/v2/product_cat?per_page=100")
        cats = json.loads(raw) if raw else []
        json.dump(cats, open("/tmp/sf_cats.json", "w", encoding="utf-8"),
                  ensure_ascii=False)
    catname = {c["id"]: c["name"] for c in cats}
    print(f"[类目] {len(cats)} 个")

    # 3) 筛选
    if args.batch == "mats":
        prods = [p for p in prods if set(p.get("product_cat") or []) & MAT_CATS]
    prods.sort(key=lambda p: p["slug"])
    if args.limit:
        prods = prods[:args.limit]
    print(f"[范围] {args.batch} → {len(prods)} 个产品")

    # 4) 页面级抓取（图片）
    PAGEDIR = "/tmp/sf_pages"
    os.makedirs(PAGEDIR, exist_ok=True)
    imgcache_path = "/tmp/sf_page_images.json"
    imgcache = {}
    if os.path.exists(imgcache_path):
        try:
            imgcache = json.load(open(imgcache_path, encoding="utf-8"))
        except Exception:                                       # noqa: BLE001
            imgcache = {}

    items, unknown_all = [], {}
    for i, p in enumerate(prods, 1):
        slug = p["slug"]
        specs, unknown = parse_specs(p["content"]["rendered"])
        for k, v in unknown:
            unknown_all.setdefault(k, []).append(slug)

        if args.no_images:
            imgs = imgcache.get(slug, [])
        elif slug in imgcache and imgcache[slug]:
            imgs = imgcache[slug]
        else:
            # 页面 HTML 落盘缓存，便于反复重解析而不重复请求英文站
            cached_page = os.path.join(PAGEDIR, slug + ".html")
            if os.path.exists(cached_page) and os.path.getsize(cached_page) > 5000:
                page = open(cached_page, encoding="utf-8", errors="ignore").read()
            else:
                page = fetch(f"{BASE}/product/{slug}/", tries=2, timeout=45)
                if page:
                    open(cached_page, "w", encoding="utf-8").write(page)
            imgs = parse_images(page)
            imgcache[slug] = imgs
            json.dump(imgcache, open(imgcache_path, "w", encoding="utf-8"),
                      ensure_ascii=False)

        items.append({
            "slug": slug,
            "wp_id": p["id"],
            "title_en": strip_tags(p["title"]["rendered"]),
            "link": p["link"],
            "modified": p.get("modified"),
            "cats": [catname.get(c, str(c)) for c in (p.get("product_cat") or [])],
            "specs": specs,
            "images": imgs,
        })
        if i % 10 == 0 or i == len(prods):
            print(f"    … {i}/{len(prods)}", flush=True)

    json.dump(items, open(os.path.join(OUTDIR, f"{args.out}.json"), "w",
                          encoding="utf-8"), ensure_ascii=False, indent=1)

    # 5) 人可读主表
    L = ["# 英文站产品主数据（自动采集）\n",
         f"来源：`{BASE}/wp-json/wp/v2/product`　采集脚本：`i18n_build/fetch_sf_catalog.py`\n",
         f"范围：**{args.batch}**　产品数：**{len(items)}**\n",
         "## 字段覆盖\n",
         "| 字段 | 有值产品数 |", "|---|---|"]
    from collections import Counter
    cov = Counter()
    for it in items:
        for k, v in it["specs"].items():
            if v:
                cov[k] += 1
    for k in SITE_ORDER + sorted(k for k in cov if k not in SITE_ORDER):
        if k in cov:
            L.append(f"| {k} | {cov[k]} / {len(items)} |")
    L += ["", "## 产品清单\n",
          "| # | slug | 标题(EN) | 类目 | 图 | " + " | ".join(SITE_ORDER[:6]) + " |",
          "|---|---|---|---|---|" + "---|" * 6]
    for i, it in enumerate(items, 1):
        s = it["specs"]
        cells = [str(s.get(k, ""))[:40] for k in SITE_ORDER[:6]]
        L.append(f"| {i} | `{it['slug']}` | {it['title_en'][:34]} | "
                 f"{'、'.join(it['cats'])[:26]} | {len(it['images'])} | "
                 + " | ".join(cells) + " |")
    if unknown_all:
        L += ["", "## 未映射标签（需人工归类）\n"]
        for k, v in sorted(unknown_all.items(), key=lambda x: -len(x[1])):
            L.append(f"- `{k}` × {len(v)}：{', '.join(v[:6])}")
    open(os.path.join(OUTDIR, f"{args.out}.md"), "w", encoding="utf-8").write(
        "\n".join(L))

    print(f"\n✅ outputs/sf_catalog.json  ({len(items)} 产品)")
    print(f"✅ outputs/sf_catalog.md")
    print("\n字段覆盖：")
    for k in SITE_ORDER:
        print(f"   {k:<14}{cov.get(k,0):>4} / {len(items)}")
    if unknown_all:
        print("\n未映射标签：", {k: len(v) for k, v in unknown_all.items()})


if __name__ == "__main__":
    main()
