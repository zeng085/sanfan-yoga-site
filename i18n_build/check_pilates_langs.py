#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""普拉提板块 6 语言版专项体检（54 页 = 9 页 × de/ja/ko/fr/it/es）。

EN 那 9 页由 check_pilates.py 管；本脚本只管语言版，因为语言版的失败模式完全不同：
    · 双语残留（语言版必须是**纯单语**，出现 .lang-zh 块或 lang-en span 就是管线出错）
    · 英文残留（该翻没翻：译文回退英文、meta/JSON-LD 漏翻、导航没本地化）
    · 链接没落到语言版（仍是 /pilates/… 而不是 /<lang>/pilates/…）
    · hreflang 互链不全 / canonical 写成 index.html 形式
    · 结构残缺（切换器被摘走后没补回、main.js 重复、版本号缺 v）

用法
    $PY i18n_build/check_pilates_langs.py
    $PY i18n_build/check_pilates_langs.py --lang de        # 只查一门
"""
import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = "https://fjsanfan.com"
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
SLUGS = [os.path.basename(p) for p in sorted(glob.glob(os.path.join(ROOT, "pilates", "*.html")))]

# 语言版里**不该**出现的英文 UI 词（逐条都是「能翻而没翻」的硬信号）。
# 只用多词/强特征短语，避免误报：单字母、型号、材料码（TPE/FAS/SANFAN）不在此列。
# ⚠️ 不要把 "Home" / "Contact" / "Blog" 列进来 —— it/es 的规范网页导航就用 "Home"，
#    "Contact" 在 fr/it 同样成立（2026-09-15 实测 it 版导航首项即 "Home"）。
EN_RESIDUE = [
    "Request a quote", "Get a Quote", "Learn more", "See the", "Why us",
    "What can be customized", "Who buys these", "All Pilates apparatus",
    "About us", "Read more", "View all",
    "Pilates Equipment", "Yoga Mats & Gear",
    "OEM & ODM", "Get in touch",
]


def text_of(h):
    """去标签后的可见文本（去 script/style）"""
    h = re.sub(r"<script[\s\S]*?</script>", " ", h)
    h = re.sub(r"<style[\s\S]*?</style>", " ", h)
    return re.sub(r"<[^>]+>", " ", h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang")
    a = ap.parse_args()
    langs = [a.lang] if a.lang else LANGS

    fails, warns, checked = [], [], 0
    for lg in langs:
        for slug in SLUGS:
            p = os.path.join(ROOT, lg, "pilates", slug)
            rel = "%s/pilates/%s" % (lg, slug)
            if not os.path.exists(p):
                fails.append((rel, "文件缺失"))
                continue
            checked += 1
            h = open(p, encoding="utf-8").read()
            txt = text_of(h)

            def bad(msg):
                fails.append((rel, msg))

            def warn(msg):
                warns.append((rel, msg))

            # ---- 结构 ----
            if h.count("</body>") != 1:
                bad("</body> 出现 %d 次（需 1）" % h.count("</body>"))
            if h.count("</html>") != 1:
                bad("</html> 出现 %d 次（需 1）" % h.count("</html>"))
            for asset in ("assets/js/main.js", "assets/css/styles.css"):
                n = len(re.findall(re.escape(asset), h))
                if n != 1:
                    bad("%s 引用 %d 次（需 1）" % (asset, n))
            for m in re.finditer(r'(?:main\.js|styles\.css)\?([^"\']*)', h):
                if not m.group(1).startswith("v"):
                    bad("资源版本号缺 v 前缀: %s" % m.group(1))
            if len(re.findall(r"<div[\s>]", h)) != len(re.findall(r"</div>", h)):
                bad("div 标签失衡")

            # ---- 纯单语 ----
            if re.search(r'class="[^"]*\blang-zh\b', h):
                bad("残留 .lang-zh 块（语言版必须纯单语）")
            if re.search(r'class="[^"]*\blang-en\b', h):
                bad("残留 .lang-en span（未被 relax_lang_en 展开）")
            if "data-i18n" in h:
                bad("残留 data-i18n 属性（语言页会被 main.js 字典覆盖）")
            m = re.search(r"<html[^>]*\blang=\"([^\"]+)\"", h)
            if not m or m.group(1) != lg:
                bad("<html lang> 应为 %s，实际 %s" % (lg, m.group(1) if m else "无"))

            # ---- hreflang / canonical ----
            hl = dict(re.findall(r'hreflang="([^"]+)"\s+href="([^"]+)"', h))
            want = ["en"] + LANGS + ["x-default"]
            for w in want:
                if w not in hl:
                    bad("缺 hreflang=%s" % w)
            self_url = SITE + "/" + rel
            if slug == "index.html":
                self_url = SITE + "/" + lg + "/pilates/"
            if hl.get(lg) != self_url:
                bad("hreflang=%s 不是自指（实际 %s）" % (lg, hl.get(lg)))
            can = re.search(r'<link rel="canonical" href="([^"]+)"', h)
            if not can:
                bad("缺 canonical")
            elif can.group(1) != self_url:
                bad("canonical 应为 %s，实际 %s" % (self_url, can.group(1)))
            # 互链必须条条存在，不能指向 404
            for k, v in hl.items():
                if k == "x-default":
                    continue
                path = v[len(SITE):].lstrip("/")
                fp = os.path.join(ROOT, path if path.endswith(".html")
                                  else os.path.join(path, "index.html"))
                if not os.path.exists(fp):
                    bad("hreflang=%s 指向不存在的文件: %s" % (k, v))

            # ---- 链接落到语言版 ----
            # ⚠️ 必须先剔除语言切换器再扫 —— 切换器的 EN / 中文 两项**本来就应该**
            #    指向英文 /pilates/…（这是「切回英文」的唯一入口）。
            #    2026-09-15 实测：不剔除会给每页误报 2 处（EN + 中文），54 页共 108 处。
            body_wo_sw = re.sub(r'<div class="lang-menu">[\s\S]*?</div>', ' ', h)
            n_bad_link = len(re.findall(r'href="/pilates/', body_wo_sw))
            if n_bad_link:
                bad("有 %d 处内链仍指向英文 /pilates/（应 /%s/pilates/）" % (n_bad_link, lg))

            # ---- 导航 ----
            nav = re.search(r'<nav class="nav-links">([\s\S]*?)</nav>', h)
            if not nav:
                bad("缺 nav-links")
            else:
                inner = nav.group(1)
                if ('href="/%s/pilates/"' % lg) not in inner:
                    bad("导航器械入口未指向 /%s/pilates/" % lg)
                if inner.count('<div class="nav-drop">') != 1:
                    bad("导航 nav-drop 数量 = %d（需 1）" % inner.count('<div class="nav-drop">'))

            # ---- 语言切换器 ----
            if 'class="lang-switch"' not in h:
                bad("缺语言切换器（fix_site 未跑？）")
            else:
                sw = re.search(r'<div class="lang-switch">[\s\S]*?<div class="lang-menu">([\s\S]*?)</div>', h)
                if sw:
                    for tg in ["en"] + LANGS:
                        if ('hreflang="%s"' % tg) not in sw.group(1):
                            bad("切换器缺 %s 项" % tg)
                    if 'class="active"' not in sw.group(1):
                        bad("切换器没有高亮当前语言")

            # ---- 英文残留 ----
            for w in EN_RESIDUE:
                if w in txt:
                    bad("英文残留: 「%s」" % w)

            # ---- JSON-LD ----
            lds = re.findall(r'<script type="application/ld\+json">([\s\S]*?)</script>', h)
            if not lds:
                bad("缺 JSON-LD")
            for ld in lds:
                try:
                    json.loads(ld)
                except Exception as e:
                    bad("JSON-LD 解析失败: %s" % str(e)[:60])

    print("检查页数: %d（%s）" % (checked, ",".join(langs)))
    print("FAIL %d / WARN %d" % (len(fails), len(warns)))
    if fails:
        print()
        print("=== FAIL（前 40）===")
        for r, m in fails[:40]:
            print("  %-44s %s" % (r, m))
    if warns:
        print()
        print("=== WARN（前 15）===")
        for r, m in warns[:15]:
            print("  %-44s %s" % (r, m))
    if not fails:
        print("\n全部通过 ✓")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
