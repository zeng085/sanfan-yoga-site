#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""语言版博客索引卡片同步（2026-10-02）

背景：6 篇新普拉提博客已进 EN blog.html，但 6 个语言版 blog.html 仍只有 10 张卡
（缺这 6 篇）→ 语言站博客板块看不到新文，内链闭环断掉。

做法（铁律 6：先搜同处现成写法，别推理）：
  · 以**该语言页自己现有的第一张卡**为模板做字段替换 —— 格式天然与既有一致
    （语言版卡片是 `<div ><h2>…</h2><p>…</p></div>` + `Weiterlesen →` 这类本地写法，
     与 EN 的 `<h3>` + `Read →` 不同；不要跨语言抄 EN 的模板）
  · 文案（tag / 标题 / 摘要 / alt）走 translator 缓存；型号与品牌术语由术语表保护
  · 新卡按 EN 顺序插到 `.blog-grid` 顶部（最新在前），与 EN 索引一致
幂等：该语言页已含此 slug 则跳过。用法：
    python3 i18n_build/sync_blog_index_cards_20261002.py --dry
    python3 i18n_build/sync_blog_index_cards_20261002.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import translator as T  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
NEW_SLUGS = [
    "pilates-reformer-buyers-guide",
    "pilates-apparatus-differences",
    "pilates-studio-equipment-list",
    "oem-pilates-equipment-china",
    "pilates-studio-layout-guide",
    "pilates-equipment-commercial-use",
]
DRY = "--dry" in sys.argv

CARD_RE = re.compile(r'<a class="post-card"[^>]*href="([^"]+)">(.*?)</a>', re.S)
IMG_RE = re.compile(r'<img\b[^>]*>', re.S)
ATTR = re.compile(r'([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*"([^"]*)"')


def attrs(tag):
    return {k.lower(): v for k, v in ATTR.findall(tag)}


def parse_en_cards():
    h = open(os.path.join(ROOT, "blog.html"), encoding="utf-8").read()
    out = {}
    for href, body in CARD_RE.findall(h):
        slug = href.rsplit("/", 1)[-1].replace(".html", "")
        img = IMG_RE.search(body)
        tag = re.search(r'<div class="pc-tag">(.*?)</div>', body, re.S)
        en = re.search(r'<div class="lang-en">\s*<h[23]>(.*?)</h[23]>\s*<p>(.*?)</p>', body, re.S)
        out[slug] = {
            "img": attrs(img.group(0)) if img else {},
            "tag": tag.group(1).strip() if tag else "",
            "title": en.group(1).strip() if en else "",
            "desc": en.group(2).strip() if en else "",
        }
    return out


def lang_template(path):
    """取该语言页第一张卡：结构模板 + 本地化的 pc-more / pc-tag 容器写法。"""
    h = open(path, encoding="utf-8").read()
    m = CARD_RE.search(h)
    if not m:
        return None
    block = m.group(0)
    more = re.search(r'<span class="pc-more">(.*?)</span>', block, re.S)
    return {
        "block": block,
        "more": more.group(1) if more else "Read →",
        "indent": re.match(r"\s*", block).group(0),
    }


def build_card(tpl, en, lang, slug):
    """用语言页的卡片为模板，替换 href/img/tag/h2/p。"""
    b = tpl["block"]
    # href：语言索引页在 /<lang>/ 下，用相对路径 blog/<slug>.html（与既有卡一致）
    b = re.sub(r'(<a class="post-card"[^>]*href=")[^"]*(")', r"\1blog/%s.html\2" % slug, b, count=1)
    # 图片：src 加一层 ../（语言页比 EN 深一级）；alt 翻译
    img_old = IMG_RE.search(b)
    a = dict(en["img"])
    a["src"] = "../" + a.get("src", "").lstrip("./")
    if a.get("alt"):
        a["alt"] = T.translate_one(a["alt"], lang)
    new_img = "<img " + " ".join('%s="%s"' % (k, a[k]) for k in
                                 ("src", "width", "height", "loading", "alt") if k in a) + ">"
    b = b.replace(img_old.group(0), new_img)
    # tag / 标题 / 摘要
    b = re.sub(r'(<div class="pc-tag">).*?(</div>)',
               lambda m: m.group(1) + T.translate_one(en["tag"], lang) + m.group(2), b, count=1)
    b = re.sub(r'(<h[23]>).*?(</h[23]>)',
               lambda m: m.group(1) + T.translate_one(en["title"], lang) + m.group(2), b, count=1)
    b = re.sub(r'(<p>).*?(</p>)',
               lambda m: m.group(1) + T.translate_one(en["desc"], lang) + m.group(2), b, count=1)
    return b


def main():
    en_cards = parse_en_cards()
    missing = [s for s in NEW_SLUGS if s not in en_cards]
    if missing:
        raise SystemExit("EN blog.html 里找不到这些 slug：%s" % missing)
    total = 0
    for lang in LANGS:
        path = os.path.join(ROOT, lang, "blog.html")
        h = open(path, encoding="utf-8").read()
        tpl = lang_template(path)
        if not tpl:
            print("!! %s 找不到卡片模板，跳过" % lang)
            continue
        want = [s for s in NEW_SLUGS if ('%s.html"' % s) not in h]
        if not want:
            print("   %s 已齐，跳过" % lang)
            continue
        cards = "\n".join(tpl["indent"] + build_card(tpl, en_cards[s], lang, s).lstrip()
                          for s in want)
        anchor = '<div class="blog-grid">'
        n = h.count(anchor)
        assert n == 1, "%s 的 blog-grid 锚点出现 %d 次（期望 1）" % (lang, n)
        h2 = h.replace(anchor, anchor + "\n" + cards, 1)
        # 落盘前自检：卡片数必须精确增加 len(want)
        assert h2.count('class="post-card"') == h.count('class="post-card"') + len(want), \
            "%s 卡片数不符" % lang
        assert 'href="href="' not in h2
        if DRY:
            print("   [dry] %s 将插入 %d 张：" % (lang, len(want)))
            print(cards[:400])
        else:
            open(path, "w", encoding="utf-8").write(h2)
            print("   %s 插入 %d 张卡（总 %d）" % (lang, len(want),
                                                h2.count('class="post-card"')))
        total += len(want)
    T.flush()
    print("\n%s：共 %d 张卡；用量 %s" % ("DRY" if DRY else "DONE", total, T.stats()))


if __name__ == "__main__":
    main()
