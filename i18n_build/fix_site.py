#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复两处站点问题：
  1) 首页"Full Product Gallery"的 26 个图库项原本是纯 <div>，没有链接 —— 改为 <a> 并指向对应产品页
  2) 英文原页只有"中文"按钮，看不到 DE/JA/KO —— 补上完整语言切换器
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_pages as B

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["de", "ja", "ko"]
# 语言版只生成了这 5 个产品页，其余图库项在语言页上回链到英文原页
T1_PRODUCTS = {"ym1", "ym2", "ym3", "fr1", "rb2"}

# 图库 26 项 -> 产品 id（按名称匹配 products-data.js）
GALLERY_MAP = [
    "ym1", "ym2", "ym3", "ym4", "ym5", "ym6", "ym7", "ym8",          # 1-8  瑜伽垫
    "pr1", "pr1", "pr2", "pr3", "pr4", "pr5",                        # 9-14 瑜伽道具
    "fr1", "fr2", "fr3", "fr5",                                      # 15-18 瑜伽柱/按摩
    "rb1", "rb2", "rb3", "rb4",                                      # 19-22 弹力带/球类
    "fi1", "fi2", "fi3", "fi4",                                      # 23-26 健身器材
]
# 图库中图片与名称错位（第 6 项 Frosted 用了 Camo 的图，第 7 项反之）—— 按名称换回正确配图
SWAP_IMG = {5: ("pu-rubber-mat-2.jpg", "pu-rubber-mat-4.jpg"),
            6: ("pu-rubber-mat-4.jpg", "pu-rubber-mat-2.jpg")}

DIV_TAG = re.compile(r"<(/?)(div)\b[^>]*>")


def find_gitems(h):
    """定位每个 <div class="g-item"> 的起止（按 div 标签配平）"""
    out = []
    for m in re.finditer(r'<div class="g-item">', h):
        depth, end = 0, None
        for tm in DIV_TAG.finditer(h, m.start()):
            if tm.group(1):
                depth -= 1
                if depth == 0:
                    end = tm.end()
                    break
            else:
                depth += 1
        if end:
            out.append((m.start(), m.end(), end))
    return out


def fix_gallery(path, lang=None):
    h = open(path, encoding="utf-8").read()
    items = find_gitems(h)
    if not items:
        return 0
    if len(items) != len(GALLERY_MAP):
        print("  !! %s 图库项 %d 个，与映射 %d 项不符，跳过" % (path, len(items), len(GALLERY_MAP)))
        return 0
    out = []
    prev = 0
    for idx, (s, body_start, e) in enumerate(items):
        inner = h[body_start:e - len("</div>")]      # 去掉外层闭合 </div>
        pid = GALLERY_MAP[idx]
        # 修正错位配图
        if idx in SWAP_IMG:
            old, new = SWAP_IMG[idx]
            inner = re.sub(r'([^"\'/]*/)?' + re.escape(old),
                           lambda m: (m.group(1) or "") + new, inner)
        # 链接目标
        if lang is None:                              # 英文原页
            href = "products/%s.html" % pid
        elif pid in T1_PRODUCTS:                      # 语言页：有语言版则同目录
            href = "products/%s.html" % pid
        else:                                         # 否则回英文原页
            href = "../../products/%s.html" % pid
        out.append(h[prev:s])
        out.append('<a class="g-item" href="%s">%s</a>' % (href, inner))
        prev = e
    out.append(h[prev:])
    open(path, "w", encoding="utf-8").write("".join(out))
    return len(items)


def lang_switcher(rel, lang=None, has_lang=True):
    """生成切换器 HTML。lang=None 表示英文原页。首页统一用目录形式(/de/)与 canonical 一致。
    has_lang=False 表示该页没有语言版，DE/JA/KO 退回到对应语言的产品列表页。"""
    def url(lg):
        if lg is None:
            return "/" if rel == "index.html" else "/" + rel
        if rel == "index.html":
            return "/%s/" % lg
        if not has_lang:                      # 无语言版 -> 指向该语言的产品列表
            return "/%s/products.html" % lg
        return "/%s/%s" % (lg, rel)

    if lang is None:      # 英文原页：EN 高亮，中文用同页切换按钮
        links = ['<a href="%s" hreflang="en" class="active">EN</a>' % url(None)]
        links.append('<button type="button" data-setlang="zh">中文</button>')
        for lg, lbl in (("de", "DE"), ("ja", "JA"), ("ko", "KO")):
            links.append('<a href="%s" hreflang="%s">%s</a>' % (url(lg), lg, lbl))
    else:                 # 语言页：中文跳英文页同时写入偏好
        en = url(None)
        links = ['<a href="%s" hreflang="en">EN</a>' % en]
        links.append('<a href="%s" hreflang="zh" data-setlang="zh">中文</a>' % en)
        for lg, lbl in (("de", "DE"), ("ja", "JA"), ("ko", "KO")):
            act = ' class="active"' if (lg == lang and has_lang) else ""
            links.append('<a href="%s" hreflang="%s"%s>%s</a>' % (url(lg), lg, act, lbl))
    return '<div class="lang-switch">' + "".join(links) + "</div>"


def all_pages():
    """需要切换器的全部页面：T1 页(有语言版) + 其余产品页(无语言版)"""
    pages = [(rel, True) for rel in B.PAGES]
    import glob
    for p in sorted(glob.glob(os.path.join(ROOT, "products", "*.html"))):
        rel = "products/" + os.path.basename(p)
        if rel not in B.PAGES:
            pages.append((rel, False))
    return pages


def fix_switcher():
    """在 nav-actions 区插入/替换语言切换器（英文原页 + 产品页 + 三种语言页）"""
    n = m = 0
    for lang in [None] + LANGS:
        for rel, has_lang in all_pages():
            if lang is not None and not has_lang:
                continue                      # 语言页只处理有语言版的
            p = os.path.join(ROOT, (lang + "/" if lang else "") + rel)
            if not os.path.exists(p):
                continue
            h = open(p, encoding="utf-8").read()
            sw = lang_switcher(rel, lang, has_lang)
            if 'class="lang-switch"' in h:
                # 已存在则整体替换，保持绝对路径版本一致
                new = re.sub(r'<div class="lang-switch">.*?</div>',
                             lambda _m: sw, h, count=1, flags=re.S)
            else:
                # 不存在则插入到导航操作区开头（英文页原有的 lang-btn 可能已被替换掉）
                new = re.sub(r'(<div class="nav-actions">)',
                             lambda _m: _m.group(1) + sw, h, count=1)
            if new != h:
                open(p, "w", encoding="utf-8").write(new)
                if lang is None:
                    n += 1
                else:
                    m += 1
    return n, m


if __name__ == "__main__":
    total = 0
    n = fix_gallery(os.path.join(ROOT, "index.html"))
    print("英文首页图库链接: %d 项" % n)
    total += n
    for lang in LANGS:
        p = os.path.join(ROOT, lang, "index.html")
        if os.path.exists(p):
            c = fix_gallery(p, lang)
            print("%s 首页图库链接: %d 项" % (lang.upper(), c))
            total += c
    a, b = fix_switcher()
    print("英文原页补切换器: %d 页 | 语言页切换器统一为绝对路径: %d 页" % (a, b))
    print("图库链接合计: %d" % total)
