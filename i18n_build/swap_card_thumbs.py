#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
swap_card_thumbs.py —— 按 href 匹配，把全站「产品卡首图」换成白底版

卡片图与产品详情页图集用的是同一批文件，但两者语义不同：
  · 产品详情页图集 → 保留英文站原图（完整、未处理）
  · 列表/首页卡片首图 → 换成白底版（视觉统一）
所以**不能全局替换文件名**，必须限定在卡片上下文内改。

匹配规则：`<a class="prod-card|g-item" href="…">` 块内的**第一个** <img> 就是首图。
href 末段即 slug，与换图计划对齐。

用法：python i18n_build/swap_card_thumbs.py [--dry]
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAN = os.path.join(ROOT, "outputs", "plan", "换图计划.json")
CARDS = os.path.join(ROOT, "outputs", "product_cards.json")
CARD_RE = re.compile(r'<a class="(?:prod-card|g-item)" href="([^"]+)"[^>]*>(.*?)</a>', re.S)
IMG_RE = re.compile(r'<img[^>]+src="([^"]+)"')
THUMB_RE = re.compile(r'<a href="(?:\.\./)?products/([\w-]+)\.html"[^>]*>\s*<img[^>]*?src="([^"]+)"')


def load_map(rollback=False, only=None):
    """返回 {slug: (旧名, 新名)}。

    rollback=True 时方向反转（新名 → 旧名），并可只处理指定来源：
    only=("算法换底",) 表示只回滚算法抠底生成的图，保留「换白底原图」的那些。
    """
    plan = json.load(open(PLAN, encoding="utf-8"))
    m = {}
    for it in plan:
        if it["cur"] == it["new"]:
            continue
        if only and not any(k in it.get("how", "") for k in only):
            continue
        m[it["slug"]] = (it["new"], it["cur"]) if rollback else (it["cur"], it["new"])
    return m


def target_files():
    out = []
    for f in sorted(os.listdir(ROOT)):
        if f.endswith(".html"):
            out.append(f)
    for d in ("products", "blog", "de", "ja", "ko", "fr", "it", "es"):
        p = os.path.join(ROOT, d)
        if os.path.isdir(p):
            out += [f"{d}/{f}" for f in sorted(os.listdir(p)) if f.endswith(".html")]
    return out


def swap_in_html(html, m):
    """在单个文件的 HTML 里替换卡片首图，返回 (新HTML, [命中 slug])。

    覆盖两套结构：
      1. `<a class="prod-card|g-item" href="products/x.html">` 块内的首图
      2. products.html 总览页 ct-thumbs 的纯图片卡：`<a href="products/x.html" title="…"><img …>`
         （a 标签直接跟 img，没有中间的 <div class="ph">）
    """
    hits = []

    def repl(mo):
        href, inner = mo.group(1), mo.group(2)
        slug = href.rstrip("/").rsplit("/", 1)[-1].replace(".html", "")
        if slug not in m:
            return mo.group(0)
        old, new = m[slug]
        if old not in inner:
            return mo.group(0)
        im = IMG_RE.search(inner)
        if not im or old not in im.group(1):
            return mo.group(0)
        hits.append(slug)
        return mo.group(0).replace(im.group(0), im.group(0).replace(old, new), 1)

    out = CARD_RE.sub(repl, html)

    def repl_thumb(mo):
        slug, src = mo.group(1), mo.group(2)
        if slug not in m:
            return mo.group(0)
        old, new = m[slug]
        if old not in src:
            return mo.group(0)
        hits.append(slug)
        return mo.group(0).replace(src, src.replace(old, new), 1)

    out = THUMB_RE.sub(repl_thumb, out)
    return out, hits


def main():
    dry = "--dry" in sys.argv
    roll = "--rollback" in sys.argv
    # 默认：换图走全部计划；回滚默认也走全部（含「算法换底」与「换白底原图」）。
    # 需要分批处理时用 --only=关键词,关键词（对 it["how"] 做子串匹配）。
    only = None
    for a in sys.argv[1:]:
        if a.startswith("--only="):
            only = tuple(k for k in a.split("=", 1)[1].split(",") if k)
            print(f"  过滤 how 含 {only}")
    m = load_map(rollback=roll, only=only)
    tag = "回滚计划" if roll else "换图计划"
    print(f"{tag} {len(m)} 条\n")

    total = {}
    changed_files = []
    for rel in target_files():
        p = os.path.join(ROOT, rel)
        html = open(p, encoding="utf-8").read()
        new, hits = swap_in_html(html, m)
        if not hits:
            continue
        for s in hits:
            total[s] = total.get(s, 0) + 1
        changed_files.append((rel, len(hits)))
        if not dry:
            open(p, "w", encoding="utf-8").write(new)
        print(f"  {rel:28s} {len(hits):>3d} 处")

    # 卡片池（幂等源）同步
    pool = json.load(open(CARDS, encoding="utf-8"))
    pool_hits = 0
    for slug, html in list(pool.items()):
        if slug not in m:
            continue
        old, new = m[slug]
        if old in html:
            im = IMG_RE.search(html)
            if im and old in im.group(1):
                pool[slug] = html.replace(im.group(0), im.group(0).replace(old, new), 1)
                pool_hits += 1
    if not dry:
        json.dump(pool, open(CARDS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n  卡片池 product_cards.json  {pool_hits} 处")

    print(f"\n共改 {len(changed_files)} 个文件、{sum(total.values())} 处卡片首图 + 卡片池 {pool_hits} 处")
    missing = sorted(set(m) - set(total))
    if missing:
        print(f"⚠️ 以下 slug 在任何 HTML 里都没命中（可能不是卡片、或 href 写法不同）：{missing}")


if __name__ == "__main__":
    main()
