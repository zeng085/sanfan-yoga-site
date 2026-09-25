#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 EN 博客文章页「中文正文块」里的误用 `<h1>` 降级为 `<h2 class="post-title">`（2026-09-25）。

背景
----
EN 的 10 篇博客文章页是**双正文结构**：
    <h1>TPE vs PU Rubber Yoga Mats: …</h1>      ← 英文正文的标题
    …
    <div class="lang-zh">                        ← 中文正文（块级，默认 display:none）
      <div class="post-meta">…</div>
      <h1>TPE 对比 PU 橡胶瑜伽垫：2026 年怎么选</h1>   ← ❌ 一页两个 h1
      …
    </div>

一个页面出现两个 `<h1>` 属结构缺陷（`audit_seo_20260916.py` 的 `h1>1` 判据）。

判据（决定性）：`assets/css/site.css` 第 572–574 行**已经**为中文块准备好了
同款样式：

    .article h1,
    .article .lang-zh h2.post-title { font-size: clamp(28px, 4vw, 40px); … }

说明设计意图本就是 `h2.post-title`，是 HTML 误用了 `h1`。降级后中文态视觉
**零变化**（同一条 CSS 规则命中），英文态不受影响（块本身 display:none）。

范围
----
只处理 `blog/*.html`（EN 10 篇）。子语言目录（de/ja/ko/fr/it/es）只有单正文，
早已是单 `h1`；`blog.html` 列表页也是单 `h1` —— 均不动。

用法
----
    python3 fix_blog_dual_h1_20260925.py           # 干跑
    python3 fix_blog_dual_h1_20260925.py --apply   # 落盘
    python3 fix_blog_dual_h1_20260925.py --check   # 自检：断言每页 h1 == 1

回滚：git checkout -- blog/*.html
"""

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BLOG_DIR = ROOT / "blog"


def downgrade_zh_h1(html):
    """
    把 `div.lang-zh` 之后那个 `<h1>` 降级为 `<h2 class="post-title">`。
    返回 (新 html, 是否改动)。幂等：已是 h2 时返回 (原样, False)。
    """
    opens = list(re.finditer(r"<h1([^>]*)>", html))
    if len(opens) < 2:
        return html, False

    zh = html.find('<div class="lang-zh"')
    if zh == -1:
        return html, False

    m = opens[-1]  # 中文块的那个 h1（实测每页最后）
    if m.start() < zh:
        return html, False  # 不在中文块之后 → 不动，交由自检报错

    attrs = m.group(1)
    if "class=" in attrs:
        # 已有 class：合并而非覆盖（当前 10 页 attrs 均为空，属防御性分支）
        new_open = '<h2 class="post-title ' + re.search(r'class="([^"]*)"', attrs).group(1) + '">'
    else:
        new_open = '<h2 class="post-title"' + attrs + ">"

    s, e = m.span()
    out = html[:s] + new_open + html[e:]

    j = out.find("</h1>", s + len(new_open))
    if j == -1:
        return html, False
    out = out[:j] + "</h2>" + out[j + 5:]
    return out, True


def pages():
    return sorted(BLOG_DIR.glob("*.html"))


def do_run(apply_):
    print("=== EN 博客文章页：中文块 h1 → h2.post-title ===")
    changed = []
    for p in pages():
        s = p.read_text(encoding="utf-8")
        new, ch = downgrade_zh_h1(s)
        before = len(re.findall(r"<h1[\s>]", s))
        after = len(re.findall(r"<h1[\s>]", new))
        assert after <= before, f"{p.name}: h1 数反而变多"
        if ch:
            # 结构断言：降级后整页恰 1 个 h1，且中文块拿到 h2.post-title
            assert after == 1, f"{p.name}: 降级后 h1={after}（应=1）"
            assert new.count('<h2 class="post-title"') == 1, f"{p.name}: 未拿到 h2.post-title"
            zh = new.find('<div class="lang-zh"')
            assert new.find("<h1", zh) == -1, f"{p.name}: 中文块之后仍有 h1"
            changed.append(p.name)
            if apply_:
                p.write_text(new, encoding="utf-8")
        print(f"  {'改' if ch else '—'} {p.name:<48} h1: {before} → {after}")
    print(f"\n{'已落盘' if apply_ else '干跑未落盘'}：{len(changed)} 页需改动")
    if changed and not apply_:
        print("  " + ", ".join(changed))
    return 0


def do_check():
    print("=== 自检：blog/*.html 每页 h1 数（应为 1）===")
    bad = 0
    for p in pages():
        s = p.read_text(encoding="utf-8")
        n = len(re.findall(r"<h1[\s>]", s))
        zh = s.find('<div class="lang-zh"')
        stray_zh = zh != -1 and s.find("<h1", zh) != -1
        ok = n == 1 and not stray_zh
        if not ok:
            bad += 1
        print(f"  {'✓' if ok else '✗'} {p.name:<48} h1={n}  中文块内残留 h1={stray_zh}")
        # 幂等断言：再跑一遍不应有改动
        _, ch = downgrade_zh_h1(s)
        if ch:
            bad += 1
            print(f"      ✗ 非幂等：脚本仍会改动 {p.name}")
    print(f"\n{'全部通过' if bad == 0 else str(bad) + ' 项异常'}")
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.check:
        return do_check()
    return do_run(args.apply)


if __name__ == "__main__":
    sys.exit(main())
