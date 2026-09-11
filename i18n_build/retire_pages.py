#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下掉"我们有、英文站没有"的产品页（规则：以英文站为准）。

本轮判定下掉 5 个：
  ym8  Balance Trainer      英文站无 balance/bosu/dome 任何产品；且与 rb3 规格描述完全相同（重复页）
  rb3  Balance Dome         同上（BOSU 半球 Ø58cm）
  rb4  Balance Board        木质平衡板，英文站无（fitness-board 是 PP+Foam 长条板，非同类）
  pr2  Yoga Wheel           英文站无瑜伽轮（只有 yoga-ring / pilates-ring）
  pr5  Knee Pad             英文站无膝盖垫

动作（幂等）：
  1) 删除 <lang>/products/<slug>.html（根 + de/ja/ko/fr/it/es）
  2) 从所有页面移除指向这些页的 <a> 块与 hreflang <link>
  3) sitemap.xml 移除对应 <url> 块
  4) vercel.json 追加 301 → 同级 /products.html（避免 404，保留权重）

用法：python3 i18n_build/retire_pages.py --dry-run | （无参数=执行）
      python3 i18n_build/retire_pages.py fi1          # 只下掉指定页（可多个）
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 第一轮（2026-09-11）：我们有、英文站没有
TARGETS = ["ym8", "rb3", "rb4", "pr2", "pr5"]
# 第二轮（2026-09-11 全面体检）：fi1 = 迷你踏步机，英文站踏步类只有 3 款立式
# Stair Climbers（116–145cm 带扶手），无袖珍踏板款 → 无源，下掉。
# 注：fi4（Home Stepper）经目视核对 = stair-climbers-3（同款白色立式），保留。
_fi = [a for a in sys.argv[1:] if not a.startswith("--")]
if _fi:
    TARGETS = _fi
LANGS = ["", "de", "ja", "ko", "fr", "it", "es"]


def base_of(lang):
    return ROOT if not lang else os.path.join(ROOT, lang)


def strip_refs(html, targets):
    """移除指向 targets 的 <a> 块与 hreflang link。"""
    n = 0
    for t in targets:
        pat = re.compile(r'<a\b[^>]*href="[^"]*%s\.html"[^>]*>.*?</a>' % t, re.S)
        html, k = pat.subn("", html)
        n += k
        pat2 = re.compile(r'<link\b[^>]*href="[^"]*%s\.html"[^>]*>\s*' % t)
        html, k2 = pat2.subn("", html)
        n += k2
    return html, n


def main():
    dry = "--dry-run" in sys.argv
    total_del = total_ref = total_sm = 0

    # 1) 页面文件 + 2) 引用
    for lang in LANGS:
        base = base_of(lang)
        for t in TARGETS:
            p = os.path.join(base, "products", t + ".html")
            if os.path.exists(p):
                total_del += 1
                print("  [删页] %s" % os.path.relpath(p, ROOT))
                if not dry:
                    os.remove(p)
        files = (glob.glob(os.path.join(base, "products", "*.html"))
                 + [os.path.join(base, "products.html"), os.path.join(base, "index.html")]
                 + [os.path.join(base, f) for f in ("about.html", "faq.html", "blog.html", "contact.html")])
        for f in files:
            if not os.path.exists(f):
                continue
            c = open(f, encoding="utf-8").read()
            new, n = strip_refs(c, TARGETS)
            if n:
                total_ref += n
                print("  [清引用 %2d] %s" % (n, os.path.relpath(f, ROOT)))
                if not dry:
                    open(f, "w", encoding="utf-8").write(new)

    # 3) sitemap
    sp = os.path.join(ROOT, "sitemap.xml")
    s = open(sp, encoding="utf-8").read()
    for t in TARGETS:
        pat = re.compile(r"\s*<url>\s*<loc>[^<]*/%s\.html</loc>.*?</url>" % t, re.S)
        s, k = pat.subn("", s)
        total_sm += k
    print("  [sitemap] 移除 %d 条" % total_sm)
    if not dry:
        open(sp, "w", encoding="utf-8").write(s)

    # 4) vercel.json 301
    vp = os.path.join(ROOT, "vercel.json")
    cfg = json.load(open(vp, encoding="utf-8"))
    rules = cfg.setdefault("redirects", [])
    existing = {(r.get("source"), r.get("destination")) for r in rules}
    added = 0
    for lang in LANGS:
        pre = "/" if not lang else "/%s/" % lang
        for t in TARGETS:
            src, dst = "%sproducts/%s.html" % (pre, t), "%sproducts.html" % pre
            if (src, dst) in existing:
                continue
            rules.append({"source": src, "destination": dst, "permanent": True})
            added += 1
    print("  [vercel] 追加 %d 条 301" % added)
    if not dry and added:
        json.dump(cfg, open(vp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        open(vp, "a", encoding="utf-8").write("\n")

    print("\n%s：删页 %d 个 / 清引用 %d 处 / sitemap %d 条 / 301 %d 条"
          % ("预演" if dry else "完成", total_del, total_ref, total_sm, added))


if __name__ == "__main__":
    main()
