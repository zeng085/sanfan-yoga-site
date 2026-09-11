#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复"第二批产品图与老页共用文件名"导致的覆盖。

第二批（build_batch2.py）按英文站 slug 命名图片，其中有 5 个与老页重名并被覆盖：
  foam-roller-1 / foam-roller-3 / resistance-band-1 / yoga-ball-1 / yoga-ball-3

本脚本：
  1) 从 git HEAD 取回这 5 张老图，另存为 <page>-hero.webp
  2) 把老页的主图 / OG / Twitter / JSON-LD 引用切到 <page>-hero.webp
     （页面内"相关产品"格的小图保持不动）
  3) 第二批新页继续使用自己的 <slug>-N.webp，双方不再互串
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMGDIR = os.path.join(ROOT, "assets", "img")
LANGS = ["", "de", "ja", "ko", "fr", "it", "es"]

# 老页 → (被覆盖的文件, 恢复正常后的新名)
MAP = {
    "fr1": ("foam-roller-1.webp", "fr1-hero.webp"),
    "fr2": ("foam-roller-3.webp", "fr2-hero.webp"),
    "rb1": ("resistance-band-1.webp", "rb1-hero.webp"),
    "rb2": ("yoga-ball-1.webp", "rb2-hero.webp"),
    "rb3": ("yoga-ball-3.webp", "rb3-hero.webp"),   # 页面已下掉，仅留图备用
}


def main():
    dry = "--dry-run" in sys.argv

    # 1) 取回老图
    for page, (old, new) in MAP.items():
        dst = os.path.join(IMGDIR, new)
        if os.path.exists(dst):
            print("  [已有] %s" % new)
            continue
        try:
            data = subprocess.check_output(["git", "show", "HEAD:assets/img/" + old], cwd=ROOT)
        except subprocess.CalledProcessError:
            print("  [git 无此文件] %s" % old)
            continue
        print("  [恢复] %s → %s (%d KB)" % (old, new, len(data) // 1024))
        if not dry:
            open(dst, "wb").write(data)

    # 2) 切引用
    for lang in LANGS:
        base = ROOT if not lang else os.path.join(ROOT, lang)
        for page, (old, new) in MAP.items():
            if page == "rb3":
                continue                                    # 页面已删
            p = os.path.join(base, "products", page + ".html")
            if not os.path.exists(p):
                continue
            h = open(p, encoding="utf-8").read()
            n = 0
            for pat in [
                r'(id="pd-main-img" src="[^"]*)' + re.escape(old),
                r'(class="pd-thumb active"><img src="[^"]*)' + re.escape(old),
                r'(<meta property="og:image" content="[^"]*)' + re.escape(old),
                r'(<meta name="twitter:image" content="[^"]*)' + re.escape(old),
                r'("image":\s*\[\s*"[^"]*)' + re.escape(old),
            ]:
                h, k = re.subn(pat, lambda m: m.group(1) + new, h)
                n += k
            if n:
                print("  [切引用 %d] %s" % (n, os.path.relpath(p, ROOT)))
                if not dry:
                    open(p, "w", encoding="utf-8").write(h)

    print("\n%s" % ("预演完成" if dry else "完成"))


if __name__ == "__main__":
    main()
