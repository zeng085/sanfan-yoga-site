#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第一批收尾补丁（2026-09-11 用户拍板后）：
  1) ym7 = 迷彩 TPE 瑜伽垫 ← 英文站 pu-rubber-yoga-mat-test（同一款，Colors 含 Camouflage Pink/Blue/Purple/Green）
     换真图 6 张、补 Colors、报价区间按 TPE 族
  2) ym3 = Double-wide TPE Mat ← 英文站 tpe-double-yoga-mat（185x122cm 双层 TPE，同比对确认同款）
     换真图 8 张（现有图是儿童独角兽垫/紫色垫，完全不是加宽垫）、补 Colors
     同时删除重复新页 products/two-tone-double-layer-tpe-yoga-mat.html 及其 15 处引用
  3) ym1/ym2/ym4/ym5/ym6 的占位报价 2.5-18.0 按 ±30% 口径归一
用法: python fix_ym3_ym7.py [--check]
"""
import os, re, sys, shutil, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "assets", "img")
STAGE = "/tmp/sf_img_stage"
CHECK = "--check" in sys.argv

# 报价基准（FOB Xiamen, USD）→ 区间 = 基准×0.7 ~ ×1.3
TPE = (4.12, 7.66)      # yoga mat S1A12  $5.89
PU = (8.51, 15.80)      # luxury YOGA mat $12.15

JOBS = {
    "ym3": dict(
        src="tpe-double-yoga-mat", n=8, dst="double-wide-tpe-mat",
        alt="Double-wide TPE Mat",
        colors_old="Custom colors &amp; prints",
        colors_new="Matcha Green + Dark Gray or Customized",
        price=TPE,
    ),
    "ym7": dict(
        src="pu-rubber-yoga-mat-test", n=6, dst="camouflage-tpe-mat",
        alt="Camouflage TPE Yoga Mat",
        colors_old="Custom colors",
        colors_new="Camouflage Pink / Camouflage Blue / Camouflage Purple / Camouflage Green or Customized",
        price=TPE,
    ),
}
# 占位报价归一（不改内容，只改 lowPrice/highPrice）
NORMALIZE = {"ym1": TPE, "ym2": TPE, "ym4": TPE, "ym5": PU, "ym6": PU}

DEAD_SLUG = "two-tone-double-layer-tpe-yoga-mat"


def copy_imgs(src_pre, n, dst_pre):
    out = []
    for i in range(1, n + 1):
        s = f"{STAGE}/{src_pre}-{i}.webp"
        d = f"{IMG}/{dst_pre}-{i}.webp"
        if not os.path.exists(s):
            raise SystemExit(f"缺源图 {s}")
        if not CHECK:
            shutil.copy2(s, d)
        out.append(f"{dst_pre}-{i}.webp")
    return out


def gallery_html(files, alt):
    thumbs = "\n".join(
        '          <button type="button" class="pd-thumb%s"><img src="../assets/img/%s" '
        'width="480" height="480" loading="lazy" alt="%s"></button>' % (" active" if i == 0 else "", f, alt)
        for i, f in enumerate(files)
    )
    return (
        '<div class="pd-gallery">\n'
        '        <div class="pd-main"><img id="pd-main-img" src="../assets/img/%s" '
        'width="480" height="480" alt="%s" /></div>\n'
        '        <div class="pd-thumbs" id="pd-thumbs">\n%s\n        </div>\n      </div>' % (files[0], alt, thumbs)
    )


def patch_page(page, files, alt, colors_old, colors_new, price):
    p = os.path.join(ROOT, "products", f"{page}.html")
    h = open(p, encoding="utf-8").read()
    orig = h

    # 1. 图集（主图 + 缩略图）
    new_gal = gallery_html(files, alt)
    h2 = re.sub(r'<div class="pd-gallery">.*?\n      </div>', lambda m: new_gal, h, count=1, flags=re.S)
    assert h2 != h, f"{page}: 图集未替换"
    h = h2

    # 2. og:image / twitter:image
    h = re.sub(r'(<meta property="og:image" content="https://fjsanfan\.com/)assets/img/[^"]+(")',
               r'\1assets/img/' + files[0] + r'\2', h, count=1)
    h = re.sub(r'(<meta name="twitter:image" content="https://fjsanfan\.com/)assets/img/[^"]+(")',
               r'\1assets/img/' + files[0] + r'\2', h, count=1)

    # 3. JSON-LD image 数组
    arr = '[\n' + ",\n".join('        "https://fjsanfan.com/assets/img/%s"' % f for f in files) + '\n      ]'
    h2 = re.sub(r'"image":\s*\[.*?\]', lambda m: '"image": ' + arr, h, count=1, flags=re.S)
    assert h2 != h, f"{page}: JSON-LD image 未替换"
    h = h2

    # 4. offers 区间
    h = re.sub(r'"lowPrice":\s*[\d.]+', '"lowPrice": %s' % price[0], h, count=1)
    h = re.sub(r'"highPrice":\s*[\d.]+', '"highPrice": %s' % price[1], h, count=1)

    # 5. Colors 行
    if colors_old:
        h2 = h.replace("</th><td>%s</td></tr>" % colors_old,
                       "</th><td>%s</td></tr>" % colors_new, 1)
        assert h2 != h, f"{page}: Colors 行未替换"
        h = h2

    if h == orig:
        print(f"  [{page}] 无变化")
        return
    if not CHECK:
        open(p, "w", encoding="utf-8").write(h)
    print(f"  [{page}] 已更新 图{len(files)}张 / 区间 {price[0]}-{price[1]} / Colors 已补")


def normalize_offers():
    for page, price in NORMALIZE.items():
        p = os.path.join(ROOT, "products", f"{page}.html")
        h = open(p, encoding="utf-8").read()
        h2 = re.sub(r'"lowPrice":\s*[\d.]+', '"lowPrice": %s' % price[0], h, count=1)
        h2 = re.sub(r'"highPrice":\s*[\d.]+', '"highPrice": %s' % price[1], h2, count=1)
        if h2 != h:
            if not CHECK:
                open(p, "w", encoding="utf-8").write(h2)
            print(f"  [{page}] 占位报价 2.5-18.0 → {price[0]}-{price[1]}")


def update_listing(files_map):
    p = os.path.join(ROOT, "products.html")
    h = open(p, encoding="utf-8").read()
    orig = h
    for page, jobs in files_map.items():
        f0 = jobs["files"][0]
        alt = jobs["alt"]
        # 卡片首图替换（同页卡片唯一）
        pat = re.compile(r'(<a class="prod-card" href="products/%s\.html"><div class="ph"><img src=")assets/img/[^"]+(")' % page)
        h2 = pat.sub(lambda m: m.group(1) + "assets/img/" + f0 + m.group(2), h, count=1)
        if h2 != h:
            # 同步 width/height 与 alt
            h2 = re.sub(r'(<a class="prod-card" href="products/%s\.html"><div class="ph"><img [^>]*?)width="\d+" height="\d+"' % page,
                        r'\1width="480" height="480"', h2, count=1)
            h = h2
            print(f"  [products.html] {page} 卡片首图 → {f0}")
    # 删除重复页卡片
    card = re.compile(r'<a class="prod-card" href="products/' + DEAD_SLUG + r'\.html">.*?</a>', re.S)
    h2, n = card.subn("", h)
    if n:
        h = h2
        print(f"  [products.html] 删除重复卡片 {DEAD_SLUG}（{n} 处）")
    if h != orig and not CHECK:
        open(p, "w", encoding="utf-8").write(h)


def clean_refs():
    """清掉其它页面相关产品格里指向重复页的卡片"""
    import glob
    pat = re.compile(r'<a class="prod-card" href="(?:\.\./)?products/' + DEAD_SLUG + r'\.html">.*?</a>', re.S)
    total = 0
    for f in glob.glob(os.path.join(ROOT, "products", "*.html")) + [os.path.join(ROOT, "products.html")]:
        h = open(f, encoding="utf-8").read()
        h2, n = pat.subn("", h)
        if n:
            total += n
            if not CHECK:
                open(f, "w", encoding="utf-8").write(h2)
            print(f"  [{os.path.relpath(f, ROOT)}] 移除引用卡片 {n}")
    print(f"  合计清理引用 {total} 处")


def update_sitemap():
    p = os.path.join(ROOT, "sitemap.xml")
    h = open(p, encoding="utf-8").read()
    h2, n = re.subn(r'\s*<url>\s*<loc>[^<]*/' + DEAD_SLUG + r'\.html</loc>.*?</url>', "", h, flags=re.S)
    if n:
        if not CHECK:
            open(p, "w", encoding="utf-8").write(h2)
        print(f"  [sitemap.xml] 移除 {DEAD_SLUG}（{n} 条）")


def remove_dupe():
    page = os.path.join(ROOT, "products", DEAD_SLUG + ".html")
    if os.path.exists(page):
        if not CHECK:
            os.remove(page)
        print(f"  [删除] products/{DEAD_SLUG}.html")
    import glob
    imgs = glob.glob(os.path.join(IMG, DEAD_SLUG + "-*.webp"))
    for f in imgs:
        if not CHECK:
            os.remove(f)
    if imgs:
        print(f"  [删除] 孤儿图 {len(imgs)} 张")


def main():
    print("== 1. 入库新图 ==")
    files_map = {}
    for page, j in JOBS.items():
        fs = copy_imgs(j["src"], j["n"], j["dst"])
        files_map[page] = dict(files=fs, alt=j["alt"])
        print(f"  {j['src']} → assets/img/{j['dst']}-1..{j['n']}.webp")
    print("== 2. 原地更新 ym3 / ym7 ==")
    for page, j in JOBS.items():
        patch_page(page, files_map[page]["files"], j["alt"], j["colors_old"], j["colors_new"], j["price"])
    print("== 3. 归一其余 ym 页占位报价 ==")
    normalize_offers()
    print("== 4. 列表页 ==")
    update_listing(files_map)
    print("== 5. 清理重复页引用 ==")
    clean_refs()
    print("== 6. sitemap ==")
    update_sitemap()
    print("== 7. 删除重复页与孤儿图 ==")
    remove_dupe()
    print("[CHECK 模式，未写盘]" if CHECK else "[完成]")


if __name__ == "__main__":
    main()
