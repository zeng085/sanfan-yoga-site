#!/usr/bin/env python3
"""语言站内链纠偏：把「落到英文页、但语言版其实存在」的相对链接纠回语言版。

## 现象与根因
语言页里出现 `../suede-cork-yoga-mats.html` 这类链接 —— 从 `de/tpe-yoga-mats.html`
出发会落到**英文**页，而 `de/suede-cork-yoga-mats.html` 明明存在。

根因是 `build_pages.rewrite_rel` 的判定依赖 `T1_SET`（"哪些页面已有语言版"）。
批量脚本 `run_i18n_batch.py` 是在应用 `--limit` **之后**才
`T1_SET.update(pages)` 的，所以试跑/分批跑时 T1_SET 被截断：
当时还不存在的语言页被判定为"无语言版" → 走 else 分支 → `rel_from` 把
同层目标算成 `../目标`（本意是回退英文），于是永久固化在产物里。
后续其他批次补齐了这些页面，但先前的产物没有再生成过。

同理，语言站 blog 页（生成于英文 `blog/index.html` 改名之前）也整体多算了一层。

## 修复规则（保守、幂等、零翻译成本）
只处理**相对路径的 `<a href>`**，且同时满足：
  1. 解析后的目标落在语言目录之外（即当前会跳到英文页）
  2. 对应的语言版文件真实存在（`{lang}/{目标}`）
绝对路径（`/...`，语言切换器用的形式）一律不碰；
语言版确实不存在的目标（场景页 / 材质页 / 未翻译产品页）保持回退英文的设计。

用法：python3 i18n_build/fix_i18n_links.py          # 体检
      python3 i18n_build/fix_i18n_links.py --fix    # 就地修复
"""
import collections
import glob
import os
import posixpath
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

LANGS = ["de", "ja", "ko", "fr", "it", "es"]
A_RE = re.compile(r'(<a\b[^>]*?\shref=")([^"]+)(")', re.I)
SKIP = ("http://", "https://", "//", "mailto:", "tel:", "javascript:", "data:", "#")


def targets():
    out = []
    for lg in LANGS:
        out += sorted(glob.glob("%s/*.html" % lg))
        out += sorted(glob.glob("%s/products/*.html" % lg))
        out += sorted(glob.glob("%s/blog/*.html" % lg))
    return out


def fix_page(path, fix):
    """返回 (改动条数, [(原 href, 新 href)])"""
    lang = path.split(os.sep)[0]
    page_dir = posixpath.dirname(path)
    src = open(path, encoding="utf-8").read()
    changed = []
    key = lang + "/"

    def _r(m):
        href = m.group(2).strip()
        if not href or href.startswith(SKIP) or href.startswith("/"):
            return m.group(0)
        base, sep, tail = href.partition("#")
        qs = ""
        if "?" in base:
            base, _, qs = base.partition("?")
            qs = "?" + qs
        if not base:
            return m.group(0)
        tgt = posixpath.normpath(posixpath.join(page_dir, base))
        # 已经指向语言版 / 不该出现 .. 逃逸的极端情况 -> 不动
        if tgt.startswith(key) or tgt.startswith("../"):
            return m.group(0)
        cand = key + tgt
        if not os.path.exists(cand):
            return m.group(0)
        new = posixpath.relpath(cand, page_dir) + qs + (sep + tail if sep else "")
        if new == href:
            return m.group(0)
        changed.append((href, new))
        return m.group(1) + new + m.group(3)

    out = A_RE.sub(_r, src)
    if fix and changed:
        open(path, "w", encoding="utf-8").write(out)
    return len(changed), changed


def main(fix=False):
    per_lang = collections.Counter()
    samples = collections.defaultdict(list)
    total = 0
    for p in targets():
        n, ch = fix_page(p, fix)
        if not n:
            continue
        total += n
        per_lang[p.split(os.sep)[0]] += n
        if len(samples[p.split(os.sep)[0]]) < 3:
            samples[p.split(os.sep)[0]].append((p, ch[0]))

    print("=== 语言站链接纠偏 ===")
    if not total:
        print("  ✅ 无待纠偏链接（所有落到英文的相对链接都符合回退设计）")
        return
    for lg, n in sorted(per_lang.items()):
        p, (a, b) = samples[lg][0]
        print("  %-3s %4d 条   例: %s" % (lg, n, p))
        print("             %s  →  %s" % (a, b))
    print("\n  合计 %d 条%s" % (total, "（已修复）" if fix else "（加 --fix 生效）"))


if __name__ == "__main__":
    main(fix="--fix" in sys.argv)
