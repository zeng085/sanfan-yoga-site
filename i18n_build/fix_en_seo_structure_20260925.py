#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""英文站 SEO 结构类修复 A1-A5 —— 纯标签替换，零文案改动（2026-09-25）

背景：audit_en_seo_standard_20260925.py 报出 7 类结构缺陷，本脚本一次修完其中的
5 类（H 层级 + 空 href）。全部是「标签用错」，不需要重写任何文案，因此 7 个语言
版本可同步脚本处理，**不需要重新翻译**。

  A1  {lang}/products/*.html  <div class="pd-specs"> 紧跟的 <h3> -> <h2>   7x147=1029
  A2  10 个一级分类页 x 7 语言 cat-head 内 <h3> -> <div class="cat-title">      70
  A3  {lang}/faq.html         <h3 class="faq-cat"> -> <h2 class="faq-cat">      7x5
  A4  {lang}/blog.html        卡片 <h3> -> <h2>（整页无 h2）                   7x10
  A5  blog/*.html（仅 EN）    无 href 的 <a data-setlang> -> <button>           18

CSS 同步（assets/css/styles.css）：
  * .pd-specs / .pc-body 补 h2 选择器（原规则限定 h3，不同步会套到全局 h2 样式）
  * 新增 .cat-head .cat-title，必须带 font-weight:700 —— h3 默认粗体，换成 div
    后默认 400，不补会变细
  * .faq-cat 是**类选择器**（定义在 faq.html 页内 style），不限定标签 -> 无需改

判据来源（都实测过，勿凭推断改）：
  * A2 只改「H1 之后直接跟 cat-head」的 10 个分类页。另有 7 个文件（6 个
    applications/*.html + products.html x 7 语言）同样含 cat-head h3，但它们前面
    已有 H2，层级正确 —— **反例，勿动**。
  * A5 只改「没有 href」的 <a data-setlang>。语言版 1140 页本来就带 href，
    实测 6 个语言版该缺陷为 0 处，所以 A5 是**纯 EN 问题**。

用法：
  python3 fix_en_seo_structure_20260925.py            # dry-run，只看会改什么
  python3 fix_en_seo_structure_20260925.py --apply    # 落盘
  python3 fix_en_seo_structure_20260925.py --check    # 验收（应全部 0 处）
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["", "de", "ja", "ko", "fr", "it", "es"]

# A2 的 10 个一级分类页（**不含** products.html：它前面已有 H2，层级正确）
CATEGORY_PAGES = [
    "foam-rollers.html",
    "jump-ropes.html",
    "massage-recovery.html",
    "meditation-pilates-mats.html",
    "pu-rubber-yoga-mats.html",
    "resistance-bands.html",
    "strength-training.html",
    "suede-cork-yoga-mats.html",
    "tpe-yoga-mats.html",
    "yoga-props-accessories.html",
]

# A1 正则是「pd-specs 容器后紧跟的 h3」——只匹配紧邻的那一个，不碰页面里其他 h3
RE_A1 = re.compile(r'(<div class="pd-specs">\s*)<h3\b([^>]*)>(.*?)</h3>', re.S)
RE_A2 = re.compile(r'(<div class="cat-head">\s*)<h3\b([^>]*)>(.*?)</h3>', re.S)
RE_A3 = re.compile(r'<h3\b([^>]*\bclass="faq-cat"[^>]*)>(.*?)</h3>', re.S)
RE_A4 = re.compile(r'<h/?3\b')          # 用于 check
RE_A5 = re.compile(r'<a\b([^>]*\bdata-setlang="[^"]*"[^>]*)>(.*?)</a>', re.S)


def read(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return fh.read()


def write(p, s):
    with open(p, "w", encoding="utf-8", newline="") as fh:
        fh.write(s)


def ls(lang, sub=""):
    d = os.path.join(ROOT, lang, sub) if lang else os.path.join(ROOT, sub)
    if not os.path.isdir(d):
        return []
    return [os.path.join(d, n) for n in sorted(os.listdir(d)) if n.endswith(".html")]


def one(lang, name):
    p = os.path.join(ROOT, lang, name) if lang else os.path.join(ROOT, name)
    return [p] if os.path.exists(p) else []


def rel(p):
    return os.path.relpath(p, ROOT)


# ---------- 各任务的 transform：返回 (新内容, 修改处数) ----------

def t_a1(s):
    def repl(m):
        return "%s<h2%s>%s</h2>" % (m.group(1), m.group(2), m.group(3))

    new, n = RE_A1.subn(repl, s)
    # 防护：h2 的开/闭标签必须同增，否则会留下 <h2>…</h3> 这种不匹配标记。
    # 第一版只替换了开标签 `subn(r"\1<h2", s)`，1029 个产品页全部变成
    # `<h2 …>Specifications</h3>` —— 浏览器会静默忽略 </h3>，h2 于是吞掉后面的
    # <table>（字号继承给表格）。静态审计与 dry-run 都看不出来。
    if (new.count("<h2") - new.count("</h2>")) != (s.count("<h2") - s.count("</h2>")):
        raise ValueError("h2 开/闭标签不配平，A1 替换越界")
    return new, n


def t_a2(s):
    def repl(m):
        attrs = m.group(2)
        if "class" in attrs:            # h3 自带 class 时不能直接套，会出双 class
            raise ValueError("cat-head 内的 h3 带 class 属性，需人工处理")
        # ⚠️ 必须把捕获组 1（<div class="cat-head"> 开标签）原样放回。
        # 第一版漏了它，直接把 cat-head 的开标签换成了 cat-title，
        # 导致容器丢失 + 多出一个 </div>（DOM 嵌套错乱）。
        return '%s<div class="cat-title"%s>%s</div>' % (m.group(1), attrs, m.group(3))

    new, n = RE_A2.subn(repl, s)
    # 防护：cat-head 容器数量与 div 配平数都必须保持不变
    if new.count('<div class="cat-head">') != s.count('<div class="cat-head">'):
        raise ValueError("cat-head 容器数量发生变化，替换越界")
    if (new.count("<div") - new.count("</div>")) != (s.count("<div") - s.count("</div>")):
        raise ValueError("div 标签配平数发生变化，替换越界")
    return new, n


def t_a3(s):
    return RE_A3.subn(r"<h2\1>\2</h2>", s)


def t_a4(s):
    # 处数按「标签数」计（</h3> 与 <h3 一一对应，不重复计数）
    new, n1 = re.subn(r"<h3\b", "<h2", s)
    new = new.replace("</h3>", "</h2>")
    return new, n1


def t_a5(s):
    changed = [0]

    def repl(m):
        if "href" in m.group(1):        # 语言版带 href，是好的，不动
            return m.group(0)
        changed[0] += 1
        return '<button type="button"%s>%s</button>' % (m.group(1), m.group(2))

    return RE_A5.sub(repl, s), changed[0]


# ---------- 约束自检：改完必须幂等 ----------

def is_idempotent(label, new):
    if label.startswith("A1"):
        return len(RE_A1.findall(new)) == 0
    if label.startswith("A2"):
        return not re.search(r'<div class="cat-head">\s*<h3\b', new)
    if label.startswith("A3"):
        return len(RE_A3.findall(new)) == 0
    if label.startswith("A4"):
        return len(re.findall(r"<h/?3\b", new)) == 0
    if label.startswith("A5"):
        return all("href" in m.group(1) for m in RE_A5.finditer(new))
    return True


def tasks():
    a1 = []
    for L in LANGS:
        a1 += ls(L, "products")
    a2 = []
    for L in LANGS:
        for n in CATEGORY_PAGES:
            a2 += one(L, n)
    a3 = []
    for L in LANGS:
        a3 += one(L, "faq.html")
    a4 = []
    for L in LANGS:
        a4 += one(L, "blog.html")
    a5 = ls("", "blog")
    return [
        ("A1 pd-specs 规格标题 h3->h2", a1, t_a1, 1029),
        ("A2 分类页 cat-head h3->div.cat-title", a2, t_a2, 70),
        ("A3 faq.html faq-cat h3->h2", a3, t_a3, 35),
        ("A4 blog.html 卡片 h3->h2", a4, t_a4, 80),
        ("A5 blog 空 href <a data-setlang>->button", a5, t_a5, 18),
    ]


# ---------- CSS 同步 ----------

CSS_EDITS = [
    (".pd-specs h3 { font-size: 19px; margin: 0 0 14px; }",
     ".pd-specs h2, .pd-specs h3 { font-size: 19px; margin: 0 0 14px; }"),
    (".cat-head h3 { font-size: 24px; margin: 0; }",
     ".cat-head .cat-title, .cat-head h3 "
     "{ font-size: 24px; margin: 0; font-weight: 700; }"),
    (".pc-body h3 { font-size: 18px; line-height: 1.4; margin: 0; color: var(--ink); }",
     ".pc-body h2, .pc-body h3 "
     "{ font-size: 18px; line-height: 1.4; margin: 0; color: var(--ink); }"),
]


def main():
    args = set(sys.argv[1:])
    apply = "--apply" in args
    check = "--check" in args
    mode = "APPLY" if apply else ("CHECK" if check else "DRY-RUN")
    print("=" * 74)
    print("模式：%s   （目录 %s）" % (mode, ROOT))
    print("=" * 74)

    total_places = 0
    total_files = 0
    bad = []
    for label, files, fn, expect in tasks():
        n_files = n_places = 0
        samples = []
        for p in files:
            s = read(p)
            try:
                new, cnt = fn(s)
            except ValueError as e:
                bad.append("%s | %s | %s" % (label, rel(p), e))
                continue
            if cnt == 0:
                continue
            if not is_idempotent(label, new):
                bad.append("%s | %s | 非幂等（再跑仍会命中）" % (label, rel(p)))
                continue
            n_files += 1
            n_places += cnt
            if len(samples) < 3:
                samples.append("%s(%d)" % (rel(p), cnt))
            if apply and not check:
                write(p, new)
        total_places += n_places
        total_files += n_files
        flag = "" if n_places == expect else "   <<< 预期 %d，实际 %d" % (expect, n_places)
        print("%-42s %4d 文件 / %4d 处%s" % (label, n_files, n_places, flag))
        if samples:
            print("     e.g. %s" % ", ".join(samples))

    print("-" * 74)
    print("合计：%d 文件 / %d 处" % (total_files, total_places))

    # CSS
    css = os.path.join(ROOT, "assets/css/styles.css")
    s = read(css)
    css_n = 0
    for old, new in CSS_EDITS:
        # ⚠️ 必须先判 new 再判 old：old 可能是 new 的子串
        # （`.pd-specs h3 {…}` 正是 `.pd-specs h2, .pd-specs h3 {…}` 的子串），
        # 反过来判会让每次重跑都再插一个选择器，越跑越脏。
        if new in s:
            pass                       # 已改过，幂等
        elif old in s:
            s = s.replace(old, new, 1)
            css_n += 1
        else:
            bad.append("CSS 未找到目标行：%s" % old[:50])
    if css_n:
        print("CSS 同步：%d 处%s" % (css_n, "（已写入）" if apply and not check else ""))
        if apply and not check:
            write(css, s)
    else:
        print("CSS 同步：0 处（已是目标形态）")

    if bad:
        print()
        print("!!! 需要人工处理 %d 项：" % len(bad))
        for b in bad:
            print("   -", b)
    if mode == "DRY-RUN":
        print()
        print("提示：加 --apply 落盘；改完必须跑 --check 与浏览器视觉验收。")


if __name__ == "__main__":
    main()
