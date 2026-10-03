#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给全站页脚插入 Impressum / Privacy Policy 入口（2026-10-03）

为什么必须做：法律页就算生成了，**客户找不到等于没有** —— 而德国采购商
（尤其是大厂合规部门）是「按 Impressum 找供应商」的，不会在站内搜索里翻。
入口必须在**每一页**的页脚，而不是只在联系页。

做法：以页脚里最后一项「Contact」的 `<li>` 为锚点，在其后插入两项；
文案按该页的语言取对应译文（不做 data-i18n：那套机制只在 en/zh 之间切，
而语言页的静态文案本身就是正确语言，加了反而会在切换时错位）。
链接用**绝对路径** `/privacy.html`，这样 de/ ja/ 等子目录页面也能正确跳转。

用法：
    python3 i18n_build/add_legal_footer_links_20261003.py --dry-run
    python3 i18n_build/add_legal_footer_links_20261003.py
    python3 i18n_build/add_legal_footer_links_20261003.py --verify
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {"i18n_build", "outputs", "__pycache__", ".git", "node_modules", "assets"}

LABEL = {
    "en": ("Privacy Policy", "Imprint"),
    "de": ("Datenschutz", "Impressum"),
    "ja": ("プライバシーポリシー", "運営者情報"),
    "ko": ("개인정보처리방침", "운영자 정보"),
    "fr": ("Confidentialité", "Mentions légales"),
    "it": ("Privacy", "Note legali"),
    "es": ("Privacidad", "Aviso legal"),
    "zh": ("隐私政策", "运营者信息"),
}

# 插入锚点：**页脚里第一个 `<ul>` 的 `</ul>` 之前**。
#
# 为什么不锚「Contact 那一项」：本仓页脚有两种形态 ——
#   A) Company 列表含 About / 生产流程 / FAQ / Contact  ← 根页、部分内页
#   B) Company 列表只到 FAQ / Blog，Contact 是**独立的 contact-line 区块** ← 245 个页面
# 锚 Contact 只能在 A 上生效（B 会整批失败：首版 1387 页只成 50 页）。
# 而两种形态都必有「页脚第一个 <ul>」，所以锚它。
RE_FOOTER = re.compile(r"<footer\b.*?</footer>", re.S)
RE_FIRST_UL = re.compile(r"<ul\b[^>]*>.*?</ul>", re.S)
RE_HAS_LEGAL = re.compile(r'href="/(?:[a-z]{2}/)?privacy\.html"')


def lang_of(rel):
    if "/" in rel:
        top = rel.split("/")[0]
        if len(top) == 2 and top.isalpha():
            return top
    return "en"


def add(h, lang):
    if RE_HAS_LEGAL.search(h):
        return h, 0
    priv, imp = LABEL.get(lang, LABEL["en"])
    block = ('\n        <li><a href="/privacy.html">%s</a></li>'
             '\n        <li><a href="/impressum.html">%s</a></li>' % (priv, imp))
    fm = RE_FOOTER.search(h)
    if not fm:
        return h, -1
    foot = fm.group(0)
    um = RE_FIRST_UL.search(foot)
    if not um:
        return h, -1
    newfoot = foot[: um.end() - len("</ul>")] + block + "\n      </ul>" + foot[um.end():]
    return h[: fm.start()] + newfoot + h[fm.end():], 1


def collect():
    out = []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if f.endswith(".html"):
                out.append(os.path.join(dp, f))
    return sorted(out)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    files = collect()
    done, skipped, failed = 0, 0, []
    for p in files:
        rel = os.path.relpath(p, ROOT)
        h = io.open(p, encoding="utf-8").read()
        lang = lang_of(rel)
        h2, n = add(h, lang)
        if n == 0:
            done += 1
        elif n < 0:
            skipped += 1
            failed.append(rel)
            continue
        else:
            if mode == "--verify":
                continue
            if mode != "--dry-run":
                io.open(p, "w", encoding="utf-8").write(h2)
    if mode == "--verify":
        miss = []
        for p in files:
            rel = os.path.relpath(p, ROOT)
            h = io.open(p, encoding="utf-8").read()
            if not RE_HAS_LEGAL.search(h):
                miss.append(rel)
        print("页脚含法律入口的页面 = %d / %d" % (len(files) - len(miss), len(files)))
        if miss:
            print("缺失示例:", miss[:8])
        return 1 if miss else 0
    print("扫描 %d 页：已存在 %d / 新增 %d / 找不到锚点 %d"
          % (len(files), done, len(files) - done - skipped, skipped))
    if failed:
        print("找不到 Contact 锚点的页面（前 10）：")
        for f in failed[:10]:
            print("   ✗ %s" % f)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
