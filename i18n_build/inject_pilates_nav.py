#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""把 Pilates 一级入口注入全站导航（幂等，可反复跑）。

注入位置：`<nav class="nav-links">` 内第一个 `</a>`（Home）之后，
即顺序固定为 Home → Pilates → Products → About → FAQ → Blog → Contact。

两种形态
    EN 页（根目录 / products / applications / blog / pilates）
        <div class="nav-drop"> …一级链接… + 8 族下拉 + All </div>
        文案走 data-i18n（字典在 assets/js/main.js），切中文自动变「普拉提器械」
    语言页（de/ja/ko/fr/it/es）
        2026-09-15 起同样是带 8 族下拉的 nav-drop，但**链接指向本语言版**
        （/de/pilates/…），文案是从该语言板块首页的 nav 里**抄**来的本地化族名。
        语言页不能用 data-i18n —— main.js 的 applyLang() 对语言页直接 return
        （isLocalizedPage()），字典根本不会生效，所以必须是静态译好的文案。

幂等：nav 块里已出现入口 href（EN 页 `/pilates/`、语言页 `/<lang>/pilates/`）就摘掉重插，
所以改标记后重跑一次即可全站升级。

⚠️ 会跳过 `pilates/` 与 `<lang>/pilates/` 目录自身的页面（由建页脚本生成，带 aria-current）。

用法
    python3 i18n_build/inject_pilates_nav.py --dry-run
    python3 i18n_build/inject_pilates_nav.py
"""
import argparse
import json
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
LANGS = ("de", "ja", "ko", "fr", "it", "es")
# 不是站点内容目录，别碰
SKIP_DIRS = {"outputs", ".git", ".workbuddy", "__pycache__", "i18n_build",
             "assets", "zhblocks", "enblocks", "_pending"}

NAV_RE = re.compile(r'(<nav class="nav-links">)([\s\S]*?)(</nav>)')

FAMILIES = ["pilates-reformer", "pilates-cadillac", "pilates-wunda-chair",
            "pilates-ladder-barrel", "pilates-spine-corrector",
            "pilates-reformer-tower", "pilates-studio-set", "pilates-specialty"]
FAM_EN = {
    "pilates-reformer": "Pilates Reformer",
    "pilates-cadillac": "Pilates Cadillac",
    "pilates-wunda-chair": "Pilates Wunda Chair",
    "pilates-ladder-barrel": "Pilates Ladder Barrel",
    "pilates-spine-corrector": "Pilates Spine Corrector",
    "pilates-reformer-tower": "Reformer Tower & 3-in-1",
    "pilates-studio-set": "Pilates Studio Set",
    "pilates-specialty": "Pilates Specialty",
}


def full_drop():
    rows = "".join(
        '            <a href="/pilates/%s.html" data-i18n="nav.pl.%s">%s</a>\n'
        % (k, k.replace("pilates-", ""), FAM_EN[k]) for k in FAMILIES)
    return ('        <div class="nav-drop">\n'
            '          <a href="/pilates/"><span data-i18n="nav.pilates">Pilates</span>'
            '<span class="nd-caret" aria-hidden="true"></span></a>\n'
            '          <div class="nav-drop-menu">\n'
            + rows +
            '            <a href="/pilates/" class="nd-all" data-i18n="nav.pl.all">All Pilates apparatus</a>\n'
            '          </div>\n'
            '        </div>\n')


BARE = '        <a href="/pilates/"><span data-i18n="nav.pilates">Pilates</span></a>\n'

# ---------------------------------------------------------------- 语言页下拉
# 2026-09-15：器械板块的 6 个语言版（<lang>/pilates/，各 9 页）建成后，
# 语言页的「裸入口」升级为完整下拉 —— 8 个目标都有真实语言版可落，
# 不再是「8 个 EN 目标对德语读者更别扭」的状态。
# 文案不另起一套：直接**抄**该语言板块首页 nav 里已经生成好的那个 nav-drop 块
# （build_pages 翻好的本地化族名 + /<lang>/pilates/... 链接），去掉 aria-current
# （那只在板块首页本身成立）。这样语言页与板块页的导航文案永远同源，不会漂移。
NAV_DROP_RE = re.compile(r'<div class="nav-drop">[\s\S]*?</div>\s*</div>')
_LANG_DROP = {}


def lang_drop(lang):
    if lang in _LANG_DROP:
        return _LANG_DROP[lang]
    src = ROOT / lang / "pilates" / "index.html"
    if not src.exists():
        return None
    t = src.read_text(encoding="utf-8", errors="ignore")
    m = NAV_RE.search(t)
    if not m:
        return None
    d = NAV_DROP_RE.search(m.group(2))
    if not d:
        return None
    blk = d.group(0)
    blk = blk.replace(' aria-current="page"', "")
    # 缩进对齐其它一级项（原块在板块页里缩进 8 空格）
    _LANG_DROP[lang] = "\n".join("        " + ln.strip() if ln.strip() else ln
                                 for ln in blk.splitlines()) + "\n"
    return _LANG_DROP[lang]

# 已存在的旧块（用于替换升级）：
#   ① EN 页的 nav-drop（入口 href="/pilates/"）
#   ② 语言页的裸链接（href="/pilates/"）
#   ③ 语言页升级后的新式下拉（入口 href="/<lang>/pilates/"）
# 三态都要能摘掉，脚本才是「替换式」而非「只补缺」。
OLD_DROP = re.compile(
    r'\s*<div class="nav-drop">\s*<a href="(?:/[a-z]{2})?/pilates/"[^>]*>[\s\S]*?</a>\s*'
    r'<div class="nav-drop-menu">[\s\S]*?</div>\s*</div>')
OLD_BARE = re.compile(r'\s*<a href="(?:/[a-z]{2})?/pilates/">[\s\S]*?</a>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    stats = {"en": 0, "lang": 0, "skip_done": 0, "skip_nonav": 0, "upgraded": 0}
    touched, skipped_done = [], []

    files = sorted(p for p in ROOT.rglob("*.html")
                   if not any(s in p.parts for s in SKIP_DIRS))

    def is_pilates_own(rel):
        """pilates/ 目录自身的页面（英语原页 + 6 个语言版）。
        这些由 build_pilates_section.py / build_pages.py 生成，块内带 aria-current，
        而且语言版导航文案是从这里**抄**出去的 —— 在这里改会把源头改坏。"""
        return (rel.parts[0] == "pilates"
                or (rel.parts[0] in LANGS and len(rel.parts) > 1 and rel.parts[1] == "pilates"))

    for p in files:
        rel = p.relative_to(ROOT)
        if is_pilates_own(rel):
            stats["skip_done"] += 1
            skipped_done.append(str(rel))
            continue
        is_lang = rel.parts[0] in LANGS
        t = p.read_text(encoding="utf-8", errors="ignore")
        m = NAV_RE.search(t)
        if not m:
            stats["skip_nonav"] += 1
            continue

        inner = m.group(2)
        nav_href = ("/%s/pilates/" % rel.parts[0]) if is_lang else "/pilates/"
        had = ('href="%s"' % nav_href) in inner

        # 先摘掉旧块（无论形态），再按当前规范重插
        if had:
            new_inner_body = OLD_BARE.sub("", OLD_DROP.sub("", inner))
            if ('href="%s"' % nav_href) in new_inner_body:   # 兜底：仍残留就别动
                stats["skip_nonav"] += 1
                continue
            inner = new_inner_body
            stats["upgraded"] += 1

        i = inner.find("</a>")
        if i < 0:
            stats["skip_nonav"] += 1
            continue
        at = i + len("</a>")
        if is_lang:
            ins = "\n" + (lang_drop(rel.parts[0]) or BARE)
        else:
            ins = "\n" + full_drop()
        new_inner = inner[:at] + ins + inner[at:].lstrip("\n")
        new_t = t[:m.start(2)] + new_inner + t[m.end(2):]
        if new_t == t:
            stats["skip_nonav"] += 1
            continue

        if not a.dry_run:
            p.write_text(new_t, encoding="utf-8")
        stats["lang" if is_lang else "en"] += 1
        touched.append(str(rel))

    print("命中文件总数:", len(files))
    if a.dry_run:
        print("将注入/升级 EN 页 :", stats["en"])
        print("将注入/升级 语言页:", stats["lang"])
    else:
        print("已注入/升级 EN 页 :", stats["en"])
        print("已注入/升级 语言页:", stats["lang"])
    print("其中替换旧块升级:", stats["upgraded"])
    print("跳过（pilates/ 目录，由建页脚本负责）:", stats["skip_done"])
    print("跳过（无 nav-links 或无需改动）:", stats["skip_nonav"])

    # 复查
    bad = []
    for p in files:
        rel = p.relative_to(ROOT)
        if is_pilates_own(rel):
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        m = NAV_RE.search(t)
        if not m:
            continue
        if t.count('<nav class="nav-links">') != 1:
            bad.append((str(rel), "nav-links 不是 1 个"))
        inner = m.group(2)
        nav_href = ("/%s/pilates/" % rel.parts[0]) if rel.parts[0] in LANGS else "/pilates/"
        if ('href="%s"' % nav_href) not in inner:
            bad.append((str(rel), "注入未生效"))
        # 无论 EN 页还是语言页，现在都应是「一个 nav-drop」而不是裸链接：
        # 2026-09-15 语言页升级为完整下拉（语言版已建，8 个目标都有真实落点）。
        if inner.count('<div class="nav-drop">') != 1:
            bad.append((str(rel), "nav-drop 数量 = %d（需 1）" % inner.count('<div class="nav-drop">')))
        # 箭头必须是真实元素：伪元素会被站内悬停下划线规则拉成斜线
        if inner.count('class="nd-caret"') != 1:
            bad.append((str(rel), "nd-caret 数量 = %d（需 1）" % inner.count('class="nd-caret"')))
        if rel.parts[0] not in LANGS:
            if inner.count('<span data-i18n="nav.pilates">Pilates</span>') != 1:
                bad.append((str(rel), "入口文案 span 异常"))
        # div 标签平衡
        if len(re.findall(r"<div[\s>]", t)) != len(re.findall(r"</div>", t)):
            bad.append((str(rel), "div 失衡"))
    print("复查:", bad[:10] if bad else "全部通过 ✓（注入生效 / 无重复 / 箭头为真实元素 / div 平衡）")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
