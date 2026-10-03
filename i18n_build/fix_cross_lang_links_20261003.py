#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""语言串站修复器（2026-10-03）

客户视角的问题：在**德语页**上点某个链接，落地却是**英文页** —— 客户以为自己
还在德语站，读到的是英文法律条款/产品参数，信任直接打折。审计实测两类：

  ① 我上一轮插法律页入口时统一用了绝对路径 `/privacy.html`、`/impressum.html`
     → 1182 页 × 2 = **2364 处**（德/日/韩/法/意/西 页脚点「Datenschutz」到英文隐私政策）
  ② 存量：两层深的语言页（`/de/pilates/*`）页脚写成 `../../applications`
     → 浏览器从 `/de/pilates/` 往上退两级正好到根，落到英文 `/applications`
     → 9 页 × 6 语言 = **54 处**

修法：语言页里的每个站内链接，若它解析到**无语言前缀的英文页**、而该页存在
同语言版本，就改写成同语言地址。
  · 原来是绝对路径（`/x`）→ 写成 `/{lang}/x`
  · 原来是相对路径 → 按当前页目录重新算相对路径（`../../applications` → `../applications`）
  · 目标是 `index.html` 时用目录形态（`/de/applications/`），与站内其它链接风格一致
**不动**语言切换器里的链接（那里的跨语言链接是设计如此）与任何带 `hreflang` 的标签。

用法：
    python3 i18n_build/fix_cross_lang_links_20261003.py --dry-run
    python3 i18n_build/fix_cross_lang_links_20261003.py
    python3 i18n_build/fix_cross_lang_links_20261003.py --verify
"""
import io
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {"i18n_build", "outputs", "__pycache__", ".git", "node_modules", "assets"}
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
RE_MENU = re.compile(r'<div class="lang-menu">.*?</div>', re.S)
RE_HL_TAG = re.compile(r'<a\b[^>]*hreflang=[^>]*>', re.I)
RE_A_HREF = re.compile(r'(<a\b[^>]*?\bhref=")([^"]+)(")', re.I)


def lang_of(rel):
    if "/" in rel:
        top = rel.split("/")[0]
        if top in LANGS:
            return top
    return "en"


def collect():
    files = []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if f.endswith(".html"):
                files.append(os.path.relpath(os.path.join(dp, f), ROOT))
    return sorted(files)


def resolve(url, page_rel):
    u = url.split("#")[0].split("?")[0]
    if not u or u.startswith(("http://", "https://", "//", "mailto:", "tel:", "data:", "javascript:")):
        return None, False
    absolute = u.startswith("/")
    if absolute:
        cand = u.lstrip("/")
    else:
        cand = os.path.normpath(os.path.join(os.path.dirname(page_rel), u))
    if u.endswith("/") or os.path.isdir(os.path.join(ROOT, cand)):
        cand = os.path.join(cand, "index.html")
    return cand, absolute


def fix_page(h, page_rel, html_set, have):
    """返回 (新 HTML, 改写次数, 明细列表)"""
    lang = lang_of(page_rel)
    if lang == "en":
        return h, 0, []
    # 把切换器与 hreflang 标签挖掉，避免动到「设计上就该跨语言」的链接
    holes = []

    def stash(m):
        holes.append(m.group(0))
        return "\x00H%d\x00" % (len(holes) - 1)

    work = RE_MENU.sub(stash, h)
    work = RE_HL_TAG.sub(stash, work)

    changes = []

    def repl(m):
        raw = m.group(2)
        tgt, absolute = resolve(raw, page_rel)
        if not tgt or tgt not in html_set:
            return m.group(0)
        if lang_of(tgt) != "en":
            return m.group(0)
        if tgt not in have or lang not in have[tgt]:
            return m.group(0)          # 该页没有同语言版本 → 保持原样（而不是跳到不存在的地址）
        same = "%s/%s" % (lang, tgt)
        if same not in html_set:
            return m.group(0)
        # 目标用目录形态（index.html → 目录），与站内其它链接一致
        dir_form = same
        if dir_form.endswith("/index.html"):
            dir_form = dir_form[:-len("index.html")]
        if absolute:
            new = "/" + dir_form
        else:
            new = os.path.relpath(dir_form, os.path.dirname(page_rel) or ".")
        if new == raw:
            return m.group(0)
        changes.append((raw, new))
        return m.group(1) + new + m.group(3)

    work = RE_A_HREF.sub(repl, work)
    for i, blk in enumerate(holes):
        work = work.replace("\x00H%d\x00" % i, blk)
    return work, len(changes), changes


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    files = collect()
    html_set = set(files)
    have = defaultdict(set)
    for f in files:
        have[f if lang_of(f) == "en" else f.split("/", 1)[1]].add(lang_of(f))

    if mode == "--verify":
        bad = 0
        for rel in files:
            if lang_of(rel) == "en":
                continue
            h = io.open(os.path.join(ROOT, rel), encoding="utf-8").read()
            _, n, _ = fix_page(h, rel, html_set, have)
            if n:
                bad += n
                if bad <= 8:
                    _, _, ch = fix_page(h, rel, html_set, have)
                    print("   ✗ %s  %s" % (rel, ch[:3]))
        print("语言页里的跨语言链接 = %d" % bad)
        return 1 if bad else 0

    total = 0
    pages = 0
    kinds = Counter()
    for rel in files:
        if lang_of(rel) == "en":
            continue
        h = io.open(os.path.join(ROOT, rel), encoding="utf-8").read()
        h2, n, ch = fix_page(h, rel, html_set, have)
        if not n:
            continue
        pages += 1
        total += n
        for old, new in ch:
            kinds[old.split("/")[-1] or old] += 1
        if mode != "--dry-run":
            io.open(os.path.join(ROOT, rel), "w", encoding="utf-8").write(h2)
    print("改写页面 %d 个 / 链接 %d 条%s" % (pages, total, "（dry-run）" if mode == "--dry-run" else ""))
    print("  改前 → 改后 样例：")
    for rel in files:
        if lang_of(rel) == "en":
            continue
        h = io.open(os.path.join(ROOT, rel), encoding="utf-8").read()
        _, _, ch = fix_page(h, rel, html_set, have)
        if ch:
            for old, new in ch[:2]:
                print("    %-46s → %s" % (old, new))
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
