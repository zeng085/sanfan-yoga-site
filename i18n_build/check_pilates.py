#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pilates 板块静态体检（不依赖网络、不依赖浏览器，可对任意页数复用）。

检查项
    1. div / section / article 标签配对
    2. .lang-en / .lang-zh 块配对（块级）+ 行内配对 span（bi() 产出）
    3. JSON-LD 每条能否 json.loads，@type 是否齐全
    4. canonical / og:url / hreflang 是否自洽（hreflang 只允许 en + x-default）
    5. 本地资源引用（../assets/...）是否真实存在
    6. 资源版本号是否与全站一致
    7. 是否混进垫类分类条 / /products/ 面包屑（隔离性回归）
    8. 双语文本比（中/英字符比，参考站内标定中位 0.353，<0.25 判 FAIL）

用法
    python3 i18n_build/check_pilates.py                # 检查 pilates/*.html
    python3 i18n_build/check_pilates.py --quiet
"""
import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

FAMILY_CHIPS = [
    "pilates-reformer", "pilates-cadillac", "pilates-wunda-chair",
    "pilates-ladder-barrel", "pilates-spine-corrector", "pilates-reformer-tower",
    "pilates-studio-set", "pilates-specialty",
]
MAT_CLASSES = [
    "tpe-yoga-mats", "pu-rubber-yoga-mats", "suede-cork-yoga-mats",
    "meditation-pilates-mats", "foam-rollers", "massage-recovery",
    "resistance-bands", "jump-ropes", "strength-training", "yoga-props-accessories",
]

OK, WARN, FAIL = "ok", "warn", "fail"
ROWS = []

# 器械板块的语言版语言码（顺序与 build_pilates_section.LANGS_META 一致）
LANGS_ORDER = ["de", "ja", "ko", "fr", "it", "es"]


def add(page, level, item, detail=""):
    ROWS.append((page, level, item, detail))


def check_pair_tags(t, page):
    for tag in ("div", "section", "article"):
        o = len(re.findall(r"<%s[\s>]" % tag, t))
        c = len(re.findall(r"</%s>" % tag, t))
        if o != c:
            add(page, FAIL, "%s 标签配对" % tag, "open=%d close=%d" % (o, c))
    if not any(r[0] == page and r[1] == FAIL for r in ROWS):
        add(page, OK, "标签配对", "div/section/article 均平衡")


def check_lang(t, page):
    """块级 div.lang-zh 与行内配对 span 都要成对。"""
    for cls in ("lang-en", "lang-zh"):
        n_div = len(re.findall(r'<div[^>]*class="[^"]*\b%s\b' % cls, t))
        add(page, OK, "块级 .%s" % cls, "%d 个" % n_div)
    # 行内配对：bi() 产出 en 在前、zh 紧随（class 可带后缀）
    en = len(re.findall(r'class="[^"]*\blang-en\b[^"]*"', t))
    zh = len(re.findall(r'class="[^"]*\blang-zh\b[^"]*"', t))
    en_blk = len(re.findall(r'<div[^>]*class="[^"]*\blang-en\b', t))
    zh_blk = len(re.findall(r'<div[^>]*class="[^"]*\blang-zh\b', t))
    en_i, zh_i = en - en_blk, zh - zh_blk
    if en_i != zh_i:
        add(page, FAIL, "行内双语配对", "en=%d zh=%d 失衡" % (en_i, zh_i))
    else:
        add(page, OK, "行内双语配对", "%d 对" % en_i)
    if en_blk != zh_blk:
        add(page, FAIL, "块级双语配对", "en=%d zh=%d 失衡" % (en_blk, zh_blk))
    else:
        add(page, OK, "块级双语配对", "%d 对" % en_blk)
    # 双语块内不应空
    for m in re.finditer(r'class="[^"]*\blang-zh\b[^"]*"[^>]*>\s*</', t):
        add(page, WARN, "空双语块", t[max(0, m.start() - 60):m.start() + 40].replace("\n", " "))
        break


def check_jsonld(t, page):
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', t, re.S)
    if not blocks:
        add(page, FAIL, "JSON-LD", "缺失")
        return
    types = []
    for i, b in enumerate(blocks):
        try:
            d = json.loads(b)
        except Exception as e:
            add(page, FAIL, "JSON-LD #%d 解析" % i, str(e)[:90])
            continue
        for node in d.get("@graph", [d]):
            types.append(node.get("@type"))
    add(page, OK, "JSON-LD", "%d 段，@type=%s" % (len(blocks), ", ".join(str(x) for x in types)))
    if page.endswith("index.html") and "ItemList" not in types:
        add(page, WARN, "JSON-LD ItemList", "版块首页建议带 ItemList")
    if not page.endswith("index.html") and "Product" not in types:
        add(page, WARN, "JSON-LD Product", "族页建议带 Product")


def check_meta(t, page, full):
    can = re.search(r'<link rel="canonical" href="([^"]+)"', t)
    og = re.search(r'<meta property="og:url" content="([^"]+)"', t)
    if not can:
        add(page, FAIL, "canonical", "缺失")
    elif can.group(1) != og.group(1) if og else False:
        add(page, FAIL, "canonical vs og:url", "%s / %s" % (can.group(1), og.group(1)))
    else:
        add(page, OK, "canonical", can.group(1))
    if can and "/pilates/" not in can.group(1):
        add(page, FAIL, "canonical 分区", "未落在 /pilates/")
    hl = re.findall(r'<link rel="alternate" hreflang="([^"]+)"', t)
    # 2026-09-15 起：6 语言版已建成，EN 原页**必须**声明全部 7 语言 + x-default。
    # 只声明 en + x-default 会让语言页单向指向 EN（hreflang 非对称，
    # GSC 报「no return tag」）—— 旧实现把「多声明」判 FAIL，正好反了。
    want = ["en"] + sorted(LANGS_ORDER) + ["x-default"]
    miss_hl = [h for h in want if h not in hl]
    extra = [h for h in hl if h not in want]
    if miss_hl:
        add(page, FAIL, "hreflang", "缺 %s（语言版已建成，需 7 语言互链）" % miss_hl)
    elif extra:
        add(page, WARN, "hreflang", "多出 %s" % extra)
    else:
        add(page, OK, "hreflang", "7 语言 + x-default")
    # 声明的语言 URL 必须与语言版页面的自指 hreflang 完全一致（互链对称）
    for lg in LANGS_ORDER:
        m2 = re.search(r'<link rel="alternate" hreflang="%s" href="([^"]+)"' % lg, t)
        # ⚠️ page 形如 "pilates/pilates-wunda-chair.html"，而**位置参数**是
        #    <lang>/pilates/<basename> —— 直接 join(ROOT, lg, "pilates", page)
        #    会变成 <lang>/pilates/pilates/… 永远查不到（2026-09-15 踩过）。
        fp = os.path.join(ROOT, lg, "pilates", os.path.basename(page))
        if not m2:
            continue
        if not os.path.exists(fp):
            add(page, FAIL, "hreflang=%s" % lg, "语言版文件不存在（404）")
        else:
            self_url = re.search(r'<link rel="canonical" href="([^"]+)"',
                                 open(fp, encoding="utf-8").read())
            if self_url and self_url.group(1) != m2.group(1):
                add(page, FAIL, "hreflang=%s 不对称" % lg,
                    "EN 声明 %s，语言版 canonical %s" % (m2.group(1), self_url.group(1)))
    # 语言切换器的 <a hreflang> 指向的语言版页面**必须真实存在**。
    # 2026-09-15 变更：器械板块的 6 语言版已建成（<lang>/pilates/，各 9 页），
    # 切换器指向 /<lang>/pilates/… 现在是**正确**行为；旧实现在此把正确写法判成
    # FAIL（当时语言版确实没有，指向即 404）。改为逐个查文件是否存在 ——
    # 既能放过已建成的语言版，又仍能抓住「指向 404」的真问题。
    sw = re.findall(r'<a href="([^"]+)" hreflang="(de|ja|ko|fr|it|es)"', t)
    swbad = []
    for u, _ in sw:
        rel = u.lstrip("/")
        fp = os.path.join(ROOT, rel if rel.endswith(".html")
                          else os.path.join(rel, "index.html"))
        if not os.path.exists(fp):
            swbad.append(u)
    if swbad:
        add(page, FAIL, "语言切换器", "指向不存在的语言版页面（404）：%s" % swbad)
    elif sw:
        add(page, OK, "语言切换器", "%d 个语言入口均指向已建页面" % len(sw))
    ti = re.search(r"<title>(.*?)</title>", t, re.S)
    if not ti:
        add(page, FAIL, "title", "缺失")
    elif len(ti.group(1)) > 65:
        add(page, WARN, "title 长度", "%d 字符（>65 可能被截断）" % len(ti.group(1)))
    else:
        add(page, OK, "title", "%d 字符" % len(ti.group(1)))
    de = re.search(r'<meta name="description" content="([^"]*)"', t)
    if not de:
        add(page, FAIL, "description", "缺失")
    elif len(de.group(1)) < 80:
        add(page, WARN, "description 长度", "%d 字符（偏短）" % len(de.group(1)))
    else:
        add(page, OK, "description", "%d 字符" % len(de.group(1)))


def check_assets(t, page, full):
    miss = []
    base = os.path.dirname(full)
    for m in re.findall(r'(?:href|src)="(\.\./[^"#?]+)', t):
        if m.startswith("http"):
            continue
        p = os.path.normpath(os.path.join(base, m))
        if not os.path.exists(p):
            miss.append(m)
    if miss:
        add(page, FAIL, "本地资源缺失", "; ".join(sorted(set(miss))[:6]))
    else:
        add(page, OK, "本地资源", "全部存在")
    vers = set(re.findall(r'\?v([0-9a-z]+)', t))
    skel = open(os.path.join(ROOT, "products", "ym1.html"), encoding="utf-8").read()
    site_ver = set(re.findall(r'\?v([0-9a-z]+)', skel))
    if vers - site_ver:
        add(page, FAIL, "资源版本号", "%s 与全站 %s 不一致" % (vers, site_ver))
    else:
        add(page, OK, "资源版本号", ",".join(vers))


def check_isolation(t, page):
    """隔离性只看版块自己的东西：分类条 chip、面包屑、正文。
    全站导航下拉与页脚里的垫类链接是共用的，不算混入。"""
    bar = re.search(r'<div class="pl-bar">.*?</div>\s*</div>', t, re.S)
    scope = bar.group(0) if bar else ""
    hit = [c for c in MAT_CLASSES if re.search(r'href="[^"]*/%s\.html"' % c, scope)]
    if hit:
        add(page, FAIL, "分类条隔离", "器械 chip 里混入垫类分类 %s" % hit)
    else:
        n_chip = len(re.findall(r'class="pl-chip"', scope))
        add(page, OK, "分类条隔离", "%d 个 chip，全为器械族" % n_chip)
    # 正文主干（去掉 nav / footer）不应出现垫类分类链接
    core = re.sub(r'<nav\b.*?</nav>', "", t, flags=re.S)
    core = re.sub(r'<footer\b.*?</footer>', "", core, flags=re.S)
    core = re.sub(r'<div class="pl-bar">.*?</div>\s*</div>', "", core, flags=re.S)
    hit2 = [c for c in MAT_CLASSES if re.search(r'href="[^"]*/%s\.html"' % c, core)]
    if hit2:
        add(page, WARN, "正文隔离", "正文出现垫类分类链接 %s" % hit2)
    else:
        add(page, OK, "正文隔离", "正文无垫类分类链接")
    bc = re.findall(r'BreadcrumbList', t)
    if bc:
        seg = t.split("BreadcrumbList")[-1][:700]
        crumbs = re.findall(r'"name"\s*:\s*"([^"]+)"', seg)
        add(page, OK, "面包屑", " → ".join(crumbs[:4]) or "无")
    if re.search(r'href="/products/"', t):
        add(page, OK, "导流带", "有指向 /products/ 的互链（cross-band）")


def check_ratio(t, page):
    """中/英字符比：站内标定中位 0.353（忠实译文本来≈1/3），<0.25 判 FAIL。"""
    zh_all, en_all = 0, 0
    for m in re.finditer(r'<span class="lang-zh[^"]*">(.*?)</span>', t, re.S):
        zh_all += len(re.sub(r"<[^>]+>", "", m.group(1)))
    for m in re.finditer(r'<span class="lang-en[^"]*">(.*?)</span>', t, re.S):
        en_all += len(re.sub(r"<[^>]+>", "", m.group(1)))
    if en_all == 0:
        add(page, WARN, "双语字符比", "未取到行内双语样本")
        return
    r = zh_all / en_all
    lvl = OK if r >= 0.30 else (WARN if r >= 0.25 else FAIL)
    add(page, lvl, "双语字符比", "zh/en=%.3f (zh=%d en=%d，标定中位 0.353)" % (r, zh_all, en_all))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    files = sorted(glob.glob(os.path.join(ROOT, "pilates", "*.html")))
    if not files:
        print("没有找到 pilates/*.html")
        return 1
    for full in files:
        page = "pilates/" + os.path.basename(full)
        t = open(full, encoding="utf-8").read()
        check_pair_tags(t, page)
        check_lang(t, page)
        check_jsonld(t, page)
        check_meta(t, page, full)
        check_assets(t, page, full)
        check_isolation(t, page)
        check_ratio(t, page)

    n_fail = sum(1 for r in ROWS if r[1] == FAIL)
    n_warn = sum(1 for r in ROWS if r[1] == WARN)
    cur = None
    for page, level, item, detail in ROWS:
        if page != cur:
            print("\n=== %s ===" % page)
            cur = page
        if a.quiet and level == OK:
            continue
        mark = {"ok": "  ✓", "warn": "  !", "fail": "  ✗"}[level]
        print("%s %-18s %s" % (mark, item, detail))
    print("\n共 %d 页 | FAIL %d | WARN %d" % (len(files), n_fail, n_warn))
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
