#!/usr/bin/env python3
"""语言站内链体检：解析每页所有本地链接，验证目标文件存在。

覆盖三类容易被忽略的链接：
  1. 相对路径（../products/x.html）—— 深度算错会在语言子目录下 404
  2. 绝对路径（/de/products.html）—— rewrite_rel 对站点根返回的形式
  3. 语言站目录形式（/de/）—— 实际是 de/index.html

无语言版的页面会回退到英文原页（rel_from 会算足层级），这不算错误，
但会单独统计「跨语言回退」条数，便于判断回退比例是否过高。

用法：python3 i18n_build/check_i18n_links.py
"""
import glob
import os
import re
import collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

LANGS = ["de", "ja", "ko", "fr", "it", "es"]
HREF_RE = re.compile(r'<a\b[^>]*\shref="([^"]+)"', re.I)
LINK_RE = re.compile(r'<link\b[^>]*\shref="([^"]+)"', re.I)
SKIP_PREFIX = ("http://", "https://", "//", "mailto:", "tel:", "javascript:", "data:", "#")


def resolve(page, href):
    """把 href 解析成站点内相对路径；站外/锚点返回 None"""
    h = href.strip()
    if not h or h.startswith(SKIP_PREFIX):
        return None
    h = h.split("#")[0].split("?")[0]
    if not h:
        return None
    if h.startswith("/"):
        rel = h.lstrip("/")
        if rel == "" or rel.endswith("/"):
            rel += "index.html"
        return os.path.normpath(rel)
    return os.path.normpath(os.path.join(os.path.dirname(page), h))


def main():
    total = collections.Counter()
    broken = collections.defaultdict(list)
    for lg in LANGS:
        files = (sorted(glob.glob("%s/*.html" % lg))
                 + sorted(glob.glob("%s/products/*.html" % lg))
                 + sorted(glob.glob("%s/blog/*.html" % lg))
                 + sorted(glob.glob("%s/applications/*.html" % lg)))
        cross = 0
        for p in files:
            s = open(p, encoding="utf-8").read()
            for m in list(HREF_RE.finditer(s)) + list(LINK_RE.finditer(s)):
                tgt = resolve(p, m.group(1))
                if tgt is None:
                    continue
                total[lg] += 1
                if not os.path.exists(tgt):
                    broken[lg].append((p, m.group(1), tgt))
                elif not tgt.startswith(lg + os.sep):
                    cross += 1
        print("%-3s %3d 页 | 本地链接 %4d 条 | 死链 %3d | 回退英文 %3d"
              % (lg, len(files), total[lg], len(broken[lg]), cross))

    print()
    if broken:
        print("=== 死链明细 ===")
        for lg, items in broken.items():
            for p, h, t in items[:20]:
                print("  %s\n     href=%s\n     -> %s" % (p, h, t))
        print("\n  合计死链 %d 条" % sum(len(v) for v in broken.values()))
    else:
        print("  ✅ 语言站本地链接 0 死链")


if __name__ == "__main__":
    main()
