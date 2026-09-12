#!/usr/bin/env python3
"""扫描 HTML 里「引号不配平」的标签（属性值含未转义引号）。

判定方式：先剔除 <script>/<style>/注释，再逐个标签数 `"` 的个数；
奇数即为畸形（属性值被提前截断）。比按 `")"` 字面量匹配准确 ——
后者会把 JSON-LD 里合法的 `\\"` 转义误报成问题。

畸形属性的实际危害：
  · 浏览器把后续属性当垃圾丢弃
  · build_pages.py 的属性重写器解析到畸形标签时跳过剩余属性
    → 实测导致 ja/yoga-props-accessories.html 图片 src 少一层 ../ 而 404

用法：python3 i18n_build/scan_bad_attrs.py
"""
import collections
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

TAG_RE = re.compile(r"<[a-zA-Z][^>]*>")
SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>|<!--.*?-->",
                       re.S | re.I)


def targets():
    out = []
    for pat in ("*.html", "products/*.html", "applications/*.html", "blog/*.html"):
        out += glob.glob(pat)
    for lg in ("de", "ja", "ko", "fr", "it", "es"):
        for pat in ("%s/*.html", "%s/products/*.html", "%s/blog/*.html"):
            out += glob.glob(pat % lg)
    return out


def main():
    bad = collections.Counter()
    samples = []
    for p in targets():
        try:
            s = open(p, encoding="utf-8").read()
        except OSError:
            continue
        s = SCRIPT_RE.sub(" ", s)
        for m in TAG_RE.finditer(s):
            t = m.group(0)
            if t.count('"') % 2:
                bad[p] += 1
                if len(samples) < 8:
                    samples.append((p, t[:150]))

    print("=== 引号不配平的标签 ===")
    if not bad:
        print("  ✅ 无（全站 HTML 属性全部配平）")
    for p, n in bad.most_common(40):
        print("  %2d 处  %s" % (n, p))
    if bad:
        print("\n  合计 %d 页 / %d 处" % (len(bad), sum(bad.values())))
    if samples:
        print("\n=== 样本 ===")
        for p, t in samples:
            print("  %s\n     %s" % (p, t))


if __name__ == "__main__":
    main()
