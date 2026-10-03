#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把页脚法律链接改成语言感知（2026-10-03）

缺陷：上一轮插法律入口时统一用了绝对路径 `/privacy.html`、`/impressum.html`。
在**德语页**上，客户点「Datenschutz」会落到**英文**隐私政策页 —— 恰好在
最需要信任的地方（法律文本）把客户甩出目标语言。语言页的其它链接都是
相对路径或带语言前缀的，只有这两个是例外，属于明显的破口。

修法：对每个页面按其语言重写这两个链接
  EN  → /privacy.html      /impressum.html
  de  → /de/privacy.html   /de/impressum.html
  …
做法是「先删掉页脚里的旧项，再按语言插入」，所以**天然幂等**，
也不会像上一版那样因为语言切换器里已有 `/privacy.html` 就误判「已存在」而跳过
（上一版正是被这个假阳性坑掉了 14 个法律页自己）。

用法：
    python3 i18n_build/fix_legal_links_lang_20261003.py --dry-run
    python3 i18n_build/fix_legal_links_lang_20261003.py
    python3 i18n_build/fix_legal_links_lang_20261003.py --verify
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
LANGS = ["de", "ja", "ko", "fr", "it", "es"]

RE_FOOTER = re.compile(r"<footer\b.*?</footer>", re.S)
RE_FIRST_UL = re.compile(r"<ul\b[^>]*>.*?</ul>", re.S)
# 页脚里指向法律页的 <li>（任意语言前缀都算，先删后插）
RE_LEGAL_LI = re.compile(
    r'\s*<li>\s*<a href="(?:/[a-z]{2})?/(?:privacy|impressum)\.html"[^>]*>.*?</a>\s*</li>',
    re.S)


def lang_of(rel):
    if "/" in rel:
        top = rel.split("/")[0]
        if top in LANGS:
            return top
    return "en"


def href_for(page, lang):
    return "/%s%s.html" % (lang + "/" if lang != "en" else "", page)


def fix(h, lang):
    priv, imp = LABEL.get(lang, LABEL["en"])
    fm = RE_FOOTER.search(h)
    if not fm:
        return h, 0, "no-footer"
    foot = fm.group(0)
    um = RE_FIRST_UL.search(foot)
    if not um:
        return h, 0, "no-ul"
    ul = um.group(0)
    ul2, n_removed = RE_LEGAL_LI.subn("", ul)
    block = ('\n        <li><a href="%s">%s</a></li>'
             '\n        <li><a href="%s">%s</a></li>'
             % (href_for("privacy", lang), priv, href_for("impressum", lang), imp))
    ul2 = ul2.replace("</ul>", block + "\n      </ul>")
    foot2 = foot[: um.start()] + ul2 + foot[um.end():]
    h2 = h[: fm.start()] + foot2 + h[fm.end():]
    return h2, n_removed, "ok"


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    files = []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if f.endswith(".html"):
                files.append(os.path.relpath(os.path.join(dp, f), ROOT))
    files.sort()

    if mode == "--verify":
        bad = []
        for rel in files:
            lang = lang_of(rel)
            h = io.open(os.path.join(ROOT, rel), encoding="utf-8").read()
            fm = RE_FOOTER.search(h)
            if not fm:
                continue
            want_p, want_i = href_for("privacy", lang), href_for("impressum", lang)
            foot = fm.group(0)
            if ('href="%s"' % want_p) not in foot or ('href="%s"' % want_i) not in foot:
                bad.append(rel)
        print("页脚法律链接语言正确的页面 = %d / %d" % (len(files) - len(bad), len(files)))
        for b in bad[:8]:
            print("   ✗ %s" % b)
        return 1 if bad else 0

    changed = 0
    issues = []
    for rel in files:
        h = io.open(os.path.join(ROOT, rel), encoding="utf-8").read()
        h2, n, st = fix(h, lang_of(rel))
        if st != "ok":
            issues.append((rel, st))
            continue
        if h2 != h:
            changed += 1
            if mode != "--dry-run":
                io.open(os.path.join(ROOT, rel), "w", encoding="utf-8").write(h2)
    print("扫描 %d 页，改写 %d 页%s" % (len(files), changed, "（dry-run）" if mode == "--dry-run" else ""))
    if issues:
        print("⚠️ 无法处理的页面 %d 个：%s" % (len(issues), issues[:5]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
