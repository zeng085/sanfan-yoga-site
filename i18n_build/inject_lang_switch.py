#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
给缺语言切换器的语言版页面补回切换器（幂等）。

病灶：build_pages 翻译时按设计删掉 lang-switch（留给 fix_site 注入），但 fix_site
只覆盖了少数老页面 → 全站约半数语言页没有切换入口，用户切到 /ko/ 后被困死
（main.js followPreferredLang 还会把访问根站的请求弹回上次语言，雪上加霜）。

切换器结构：与 EN 页 lang-switch 一致，全部项带 data-setlang + href：
  - main.js 对 [data-setlang] 统一处理 = 记偏好 + 跳转
  - en/zh 均跳 EN 等价页（中文内容由 EN 页 show-zh 呈现）
  - 当前语言项标 active
注入位置：<div class="nav-actions"> 内、报价按钮之前。
"""
import os, re, glob, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
NAMES = {"de": "Deutsch", "ja": "日本語", "ko": "한국어", "fr": "Français",
         "it": "Italiano", "es": "Español", "en": "English", "zh": "中文"}
LABELS = {"de": "DE", "ja": "JA", "ko": "KO", "fr": "FR", "it": "IT",
          "es": "ES", "en": "EN", "zh": "中文"}


def switcher_html(cur, en_path):
    items = []
    for lg in ["en", "zh"] + LANGS:
        active = ' class="active"' if lg == cur else ""
        href = en_path if lg in ("en", "zh") else f"/{lg}/{en_path.lstrip('/')}"
        items.append(f'<a data-setlang="{lg}" href="{href}" hreflang="{lg}" '
                     f'title="{NAMES[lg]}"{active}>{LABELS[lg]}</a>')
    return (
        '<div class="lang-switch">'
        '<button aria-expanded="false" aria-haspopup="true" class="lang-current" type="button">'
        f'<span class="lang-cur-txt">{LABELS[cur]}</span>'
        '<span class="lang-caret">\u25be</span></button>'
        '<div class="lang-menu">' + "".join(items) + "</div></div>"
    )


def main():
    total = fixed = 0
    for L in LANGS:
        for p in glob.glob(os.path.join(ROOT, L, "**", "*.html"), recursive=True):
            total += 1
            s = open(p, encoding="utf-8").read()
            if "lang-switch" in s:
                continue
            # EN 等价路径 = 去掉 "{L}/" 前缀
            en_rel = os.path.relpath(p, os.path.join(ROOT, L)).replace(os.sep, "/")
            m = re.search(r'(<div class="nav-actions">)', s)
            if not m:
                print("!! 无 nav-actions:", p)
                continue
            sw = switcher_html(L, "/" + en_rel if en_rel != "index.html" else "/")
            s2 = s[:m.end()] + "\n        " + sw + s[m.end():]
            open(p, "w", encoding="utf-8").write(s2)
            fixed += 1
    print(f"共 {total} 个语言页，补回切换器 {fixed} 页")


if __name__ == "__main__":
    main()
