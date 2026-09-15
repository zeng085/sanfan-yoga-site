#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""把 Pilates 一级入口注入全站导航（幂等，可反复跑）。

注入位置：`<nav class="nav-links">` 内第一个 `</a>`（Home）之后，
即顺序固定为 Home → Pilates → Products → About → FAQ → Blog → Contact。

两种形态
    EN 页（根目录 / products / applications / blog / pilates）
        <div class="nav-drop"> …一级链接… + 8 族下拉 + All </div>
        文案走 data-i18n（字典在 assets/js/main.js），切中文自动变「普拉提器械」
    语言页（de/ja/ko/fr/it/es，共 6×181 页）
        只给裸链接 <a href="/pilates/">Pilates</a>
        理由：器械族的语言版还没建，下拉里 8 个 EN 目标对德语/日语读者更别扭；
        而「Pilates」在 6 个目标语言里都是同一个词，不需要翻译。
        等语言版铺完再换成带下拉的形态即可（本脚本重跑一次就替换）。

幂等：nav 块里已出现 href="/pilates/" 就跳过；因此会跳过已建好的 9 个 pilates 页。

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

# 已存在的旧块（用于替换升级）：EN 的 nav-drop + 语言页的裸链接
OLD_DROP = re.compile(
    r'\s*<div class="nav-drop">\s*<a href="/pilates/"[^>]*>[\s\S]*?</a>\s*'
    r'<div class="nav-drop-menu">[\s\S]*?</div>\s*</div>')
OLD_BARE = re.compile(r'\s*<a href="/pilates/">[\s\S]*?</a>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    stats = {"en": 0, "lang": 0, "skip_done": 0, "skip_nonav": 0, "upgraded": 0}
    touched, skipped_done = [], []

    files = sorted(p for p in ROOT.rglob("*.html")
                   if not any(s in p.parts for s in SKIP_DIRS))
    for p in files:
        rel = p.relative_to(ROOT)
        # pilates/ 目录由 build_pilates_section.py 生成，块内还带 aria-current，别在这里改
        if rel.parts[0] == "pilates":
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
        had = 'href="/pilates/"' in inner

        # 先摘掉旧块（无论形态），再按当前规范重插
        if had:
            new_inner_body = OLD_BARE.sub("", OLD_DROP.sub("", inner))
            if 'href="/pilates/"' in new_inner_body:      # 兜底：仍残留就别动
                stats["skip_nonav"] += 1
                continue
            inner = new_inner_body
            stats["upgraded"] += 1

        i = inner.find("</a>")
        if i < 0:
            stats["skip_nonav"] += 1
            continue
        at = i + len("</a>")
        ins = "\n" + (BARE if is_lang else full_drop())
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
        if rel.parts[0] == "pilates":
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        m = NAV_RE.search(t)
        if not m:
            continue
        if t.count('<nav class="nav-links">') != 1:
            bad.append((str(rel), "nav-links 不是 1 个"))
        inner = m.group(2)
        if 'href="/pilates/"' not in inner:
            bad.append((str(rel), "注入未生效"))
        elif inner.count('href="/pilates/"') > 11:
            bad.append((str(rel), "重复注入 %d 处" % inner.count('href="/pilates/"')))
        # 箭头必须是真实元素：伪元素会被站内悬停下划线规则拉成斜线
        if rel.parts[0] not in LANGS:
            if inner.count('class="nd-caret"') != 1:
                bad.append((str(rel), "nd-caret 数量 = %d（需 1）" % inner.count('class="nd-caret"')))
            if inner.count('<span data-i18n="nav.pilates">Pilates</span>') != 1:
                bad.append((str(rel), "入口文案 span 异常"))
        else:
            if 'class="nd-caret"' in inner:
                bad.append((str(rel), "语言页不该有下拉箭头"))
        # div 标签平衡
        if len(re.findall(r"<div[\s>]", t)) != len(re.findall(r"</div>", t)):
            bad.append((str(rel), "div 失衡"))
    print("复查:", bad[:10] if bad else "全部通过 ✓（注入生效 / 无重复 / 箭头为真实元素 / div 平衡）")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
