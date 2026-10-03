#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""链接语言一致性审计（2026-10-03 新建）

要回答客户视角的三个问题：
  ① 同一语言页内的链接，会不会把人带到**另一种语言**的页面？
  ② 客户从搜索/直接输入进来，**看到的是什么语言**？
  ③ 页面上给「换语言」的入口，指向的页面**是否真实存在**？

四道判据：
  L1 **语言串站**：语言页（/de/ 等）里的站内链接若解析到**无语言前缀**的页面，
     而该页面又存在对应语言版本 → 判为串站（客户点一下就掉回英文站）。
     例外：hreflang 链接、语言切换器、legal/canonical 引用不算串站。
  L2 **死链**：所有站内链接（含切换器）必须能映射回本地真实文件。
  L3 **切换器完整性**：每页的语言切换器必须同时提供 7 个入口
     （en / de / ja / ko / fr / it / es，EN 页的中文用按钮而非链接），且指向存在。
  L4 **入口语言**：`<html lang>` 与所在目录一致（EN 目录=en，语言目录=对应语）。

用法：
    python3 i18n_build/audit_link_lang_20261003.py
    python3 i18n_build/audit_link_lang_20261003.py --only-lang=de
退出码：L1/L2/L3 任一命中 = 1（可直接当推送前的闸）。
"""
import io
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {"i18n_build", "outputs", "__pycache__", ".git", "node_modules", "assets"}
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
PAGE_DIRS = ["blog", "products", "pilates", "applications"]
BASE = "https://fjsanfan.com"
# 设计例外：`product.html` 是全站唯一没有语言版本、也不进 sitemap 的孤立页
# （文件头注释写明：内容由 JS 动态填充、禁止索引）。它没有语言版不是缺陷，
# 强行要求「切换器 7 个入口」只会逼着人造假链接。
NO_SWITCHER_OK = {"product.html"}

LINK = re.compile(r'(?:href|src)="([^"]+)"')
RE_LANG = re.compile(r'<html[^>]*\blang="([^"]+)"', re.I)
RE_MENU = re.compile(r'<div class="lang-menu">.*?</div>', re.S)
RE_ALT_ATTR = re.compile(r'hreflang="([^"]+)"')
# 带 hreflang 属性的单个标签（切换器之外的 hreflang 链接也应豁免 L1）
RE_HREFLANG_TAG = re.compile(r'<a\b[^>]*hreflang=[^>]*>', re.I)


def collect_html():
    out = []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if f.endswith(".html"):
                out.append(os.path.join(dp, f))
    return sorted(out)


def lang_of(rel):
    """返回页面语言（en 表示英文主站）。"""
    if "/" in rel:
        top = rel.split("/")[0]
        if top in LANGS:
            return top
    return "en"


def rel_of_url(url, page_rel):
    """把 href 解析成仓库内相对路径；不是站内页面的返回 None。"""
    # ⚠️ 必须先剥掉 #片段 与 ?查询串：`styles.css?v20261003a` 是本项目所有 CSS/JS 的
    #    固定写法，不剥就会被判成「文件不存在」→ 首版虚报 2782 条死链。
    u = url.split("#")[0].split("?")[0]
    if not u:
        return None
    if u.startswith(("http://", "https://", "//", "mailto:", "tel:", "data:", "javascript:")):
        return None
    if u.startswith("/"):
        cand = u.lstrip("/")
    else:
        cand = os.path.normpath(os.path.join(os.path.dirname(page_rel), u))
    if u.endswith("/") or os.path.isdir(os.path.join(ROOT, cand)):
        cand = os.path.join(cand, "index.html")
    return cand


def main():
    only = None
    if "--only-lang" in sys.argv:
        only = sys.argv[sys.argv.index("--only-lang") + 1]
    files = [os.path.relpath(p, ROOT) for p in collect_html()]
    if only:
        files = [f for f in files if lang_of(f) == only]

    # ⚠️ exist 必须收**全部**文件，不只是 .html —— 首版只收 HTML，
    #    结果 24118 条 assets/*.css|js|webp 引用全被报成「死链」，纯工具 bug。
    #    （同类教训：先怀疑探针，再怀疑站点）
    # exist 必须收**全部**文件（不是只有 .html），否则 assets/*.css|js|webp 全被报成死链。
    # ⚠️ 这里**不能沿用 SKIP_DIRS**：assets 目录要跳过的是「HTML 收集」，
    #    但判断资源是否存在时必须把它算进去（首版两处都踩了，报出 2.4 万条假死链）。
    exist = set()
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in (".git", "node_modules", "__pycache__")]
        for f in fn:
            exist.add(os.path.relpath(os.path.join(dp, f), ROOT))
    html_set = {f for f in exist if f.endswith(".html")}

    cross, dead, menu_bad, lang_bad = [], [], [], []
    stats = Counter()
    # 语言版本存在性：去掉语言前缀后的相对路径 -> {已有语言}
    # ⚠️ EN 根级页面路径里没有 "/"，`split("/", 1)[1]` 会越界（首版踩到）
    have = defaultdict(set)
    for f in html_set:
        if lang_of(f) == "en":
            key = f
        else:
            key = f.split("/", 1)[1]
        have[key].add(lang_of(f))

    for rel in files:
        lang = lang_of(rel)
        h = io.open(os.path.join(ROOT, rel), encoding="utf-8", errors="ignore").read()
        # L4 html lang 与目录一致
        m = RE_LANG.search(h)
        declared = (m.group(1).lower() if m else "")
        want = "en" if lang == "en" else lang
        if declared and not declared.startswith(want):
            lang_bad.append((rel, declared, want))

        # L3 切换器完整性
        mm = RE_MENU.search(h)
        if mm:
            entries = re.findall(r'(?:hreflang="([a-z-]+)"|data-setlang="([a-z]+)")', mm.group(0))
            got = {a or b for a, b in entries}
            for need in ["en"] + LANGS:
                if need not in got:
                    menu_bad.append((rel, "缺入口 " + need))
            for url in re.findall(r'href="([^"]+)"', mm.group(0)):
                t = rel_of_url(url, rel)
                if t and t not in exist:
                    menu_bad.append((rel, "切换器死链 " + url))
        else:
            if rel not in NO_SWITCHER_OK:
                menu_bad.append((rel, "没有语言切换器"))

        # L1/L2 站内链接。
        # ⚠️ 必须先把「语言切换器」整块抠掉再扫：切换器里指向**其它语言**的链接
        #   （德语页上的「EN」入口 href="/about.html"）是设计如此，判成串站就是假阳性。
        #   首版没实现这个例外 → 4794 条里绝大多数是切换器，真问题只剩个位数。
        scan_src = RE_MENU.sub(" ", h)
        scan_src = RE_HREFLANG_TAG.sub(" ", scan_src)   # 任何带 hreflang 的标签都跳过
        for raw in LINK.findall(scan_src):
            tgt = rel_of_url(raw, rel)
            if tgt is None:
                continue
            if tgt not in exist:
                dead.append((rel, raw))
                continue
            stats["refs"] += 1
            t_lang = lang_of(tgt)
            if t_lang == lang:
                continue
            if lang == "en" or t_lang != "en":
                # EN 页链到语言页：可能是切换器（合法），不判
                continue
            # 这里是「语言页 → 落到无语言前缀的英文页」。只要该页存在同语言版本就算串站。
            # ⚠️ 首版只判相对路径同构的情况（`tgt.startswith(lang+'/')`），
            #    于是德语页上的绝对链接 `/privacy.html` 全被判成「不是串站」——L1 假阴性，
            #    而这恰恰是客户点「Datenschutz」会掉回英文页的真实缺陷。
            if tgt in have and lang in have[tgt]:
                cross.append((rel, raw, tgt))

    print("扫描页面 %d 个 | 站内链接引用 %d 条" % (len(files), stats["refs"]))
    print()
    print("L1 语言串站（语言页里链到无前缀的英文页，而该页有对应语言版）= %d" % len(cross))
    by = Counter()
    for rel, raw, tgt in cross:
        by[(lang_of(rel), os.path.dirname(tgt) or "(root)")] += 1
    for (lg, d), n in by.most_common(10):
        print("   %-4s → 英文根  %-16s %d 处" % (lg, d, n))
    for rel, raw, tgt in cross[:8]:
        print("     ✗ %s  →  %r" % (rel, raw))

    print("\nL2 站内死链 = %d" % len(dead))
    for rel, raw in dead[:10]:
        print("     ✗ %s  →  %r" % (rel, raw))

    print("\nL3 切换器问题 = %d" % len(menu_bad))
    c = Counter(s for _, s in menu_bad)
    for k, v in c.most_common(8):
        print("     %-24s %d 页" % (k, v))
    for rel, s in menu_bad[:6]:
        print("     ✗ %s  %s" % (rel, s))

    print("\nL4 html lang 与目录不一致 = %d" % len(lang_bad))
    for rel, got, want in lang_bad[:8]:
        print("     ✗ %s  声明 %s / 应为 %s" % (rel, got, want))

    bad = len(cross) + len(dead) + len(menu_bad) + len(lang_bad)
    print("\n" + "=" * 68)
    print("结论：%s" % ("语言与链接一致性合格 ✓" if not bad else "有问题 ✗（%d 项）" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
