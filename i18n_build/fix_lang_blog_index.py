#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 6 语言 blog.html 索引页：
  病灶：历史插入 top-12 卡时造成 <a> 嵌 <a>（非法 HTML），浏览器提前闭合外层卡
        → 空白卡 + 卡片内容/href 错位 + tpe-vs-pu 卡从索引消失。
  修法：以 EN blog.html 卡片顺序（10 篇）为基准，整格重建 blog-grid：
        标题/摘要从各语言文章页 h1 / lead-p 提取（零翻译成本），图与 tag 沿用 EN 卡。
  幂等：可重复跑。
"""
import os, re, sys, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["de", "ja", "ko", "fr", "it", "es"]

# ---------------------------------------------------------------- div 配对工具
def grid_span(s, start):
    """返回 blog-grid 开 div 的 (inner_start, inner_end)（不含两端标签）"""
    m = re.compile(r'<div class="blog-grid">').search(s, start)
    if not m:
        return None
    depth, i = 1, m.end()
    for t in re.finditer(r'<(/?)div\b', s[m.end():]):
        depth += -1 if t.group(1) == "/" else 1
        if depth == 0:
            return m.end(), m.end() + t.start()
    return None


def extract(page, lang):
    """从语言文章页提取 h1 与 lead-p 文本"""
    s = open(page, encoding="utf-8").read()
    h1 = re.search(r"<h1>(.*?)</h1>", s, re.S)
    lead = re.search(r'<p class="lead-p">(.*?)</p>', s, re.S)
    if not h1 or not lead:
        return None
    clean = lambda x: re.sub(r"\s+", " ", x).strip()
    return clean(h1.group(1)), clean(lead.group(1))


def build_card(lang, slug, img, tag, title, desc):
    return (
        f'<a class="post-card" href="/{lang}/blog/{slug}.html">\n'
        f'<div class="pc-img"><img alt="{H.escape(title, quote=True)}" height="480" '
        f'loading="lazy" src="../assets/img/{img}" width="480"/></div>\n'
        f'<div class="pc-body">\n'
        f'<div class="pc-tag">{tag}</div>\n'
        f'<div><h3>{H.escape(title, quote=False)}</h3><p>{H.escape(desc, quote=False)}</p></div>\n'
        f'\n'
        f'<span class="pc-more">Read \u2192</span>\n'
        f'</div>\n'
        f'</a>'
    )


def main():
    en = open(os.path.join(ROOT, "blog.html"), encoding="utf-8").read()
    span = grid_span(en, 0)
    cards_en = re.findall(
        r'<a class="post-card" href="blog/([a-z0-9-]+)\.html">((?:(?!</a>).)*)</a>',
        en[span[0]:span[1]], re.S)
    meta = []
    for slug, inner in cards_en:
        img = re.search(r'src="[^"]*/([^"/]+\.webp)"', inner).group(1)
        tag = re.search(r'pc-tag">([^<]*)', inner).group(1)
        meta.append((slug, img, tag))
    print("EN 卡序:", [m[0] for m in meta])

    for L in LANGS:
        p = os.path.join(ROOT, L, "blog.html")
        s = open(p, encoding="utf-8").read()
        sp = grid_span(s, 0)
        if not sp:
            print("!! 找不到 blog-grid:", p)
            continue
        new_cards = []
        miss = []
        for slug, img, tag in meta:
            info = extract(os.path.join(ROOT, L, "blog", slug + ".html"), L)
            if not info:
                miss.append(slug)
                continue
            new_cards.append(build_card(L, slug, img, tag, info[0], info[1]))
        if miss:
            print(f"!! {L} 缺 h1/lead: {miss} —— 该语言跳过")
            continue
        new_inner = "\n\n" + "\n\n".join(new_cards) + "\n\n"
        s2 = s[:sp[0]] + new_inner + s[sp[1]:]
        # 校验：不允许 a 嵌 a
        if re.search(r'<a class="post-card"[^>]*>\s*<a\b', s2):
            print("!! 仍有嵌套 a:", p)
            continue
        open(p, "w", encoding="utf-8").write(s2)
        print(f"rebuilt {L}/blog.html: {len(new_cards)} 卡")


if __name__ == "__main__":
    main()
