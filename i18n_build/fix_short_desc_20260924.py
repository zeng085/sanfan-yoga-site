#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0-D：补 4 页偏短 meta description（显示宽 < 80）

背景：9/16 遗留清单记「13 处偏短 description」，复核后收窄至 4 页：
  products/ym3.html（EN 双语页）、ja/products/ym3.html、de/products/ym3.html、products/rb2.html
判据按**显示宽度**（CJK ×2），目标区间 100–155 宽（Google 按像素截断，155 为预算）。

写法：精确字符串替换（meta description / og:description / twitter:description 三处同文），
落盘前断言新宽度在区间内 + 旧串已清零；幂等（重跑 0 改动）。
"""
import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

LO, HI = 100, 155


def W(s):
    return sum(2 if ord(c) > 0x2E80 else 1 for c in s)


OLD = {
    "products/ym3.html":
        "Wide-format TPE mat for couples and family use; non-slip, easy to clean.",
    "ja/products/ym3.html":
        "カップルやご家族向けのワイドサイズのTPEマット。滑りにくく、お手入れも簡単です。",
    "de/products/ym3.html":
        "TPE-Matte im Großformat für Paare und Familien; rutschfest, leicht zu reinigen.",
    "products/rb2.html":
        'Anti-slip gymnastic ball (25 cm / 10&quot;) for pilates, rehab and core work.',
}

NEW = {
    "products/ym3.html":
        "Wide-format TPE double yoga mat, 185×122 cm in 6 or 8 mm, for couples and family "
        "yoga. Non-slip, easy to clean; from 100 pcs with your custom logo.",
    "ja/products/ym3.html":
        "カップルやご家族向けのワイドサイズTPEマット。185×122cm、厚さ6／8mm、2層構造で"
        "滑りにくくお手入れも簡単。100個からロゴ彫刻・プリント対応のOEM製造。",
    "de/products/ym3.html":
        "TPE-Matte im Großformat für Paare und Familien: 185×122 cm, 6 oder 8 mm, "
        "doppellagig, rutschfest und leicht zu reinigen. Ab 100 Stück mit Logo-Gravur.",
    "products/rb2.html":
        "Mini yoga ball 25 cm / 10 in, anti-burst anti-slip PVC for Pilates, rehab and "
        "core training. Also made in 55, 65 and 75 cm with custom colour and logo.",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true", help="只校验是否需要修（残余数）")
    args = ap.parse_args()

    problems = []
    for rel, new in NEW.items():
        w = W(new)
        if not (LO <= w <= HI):
            problems.append("%s 新描述 %d 宽，超出 %d–%d" % (rel, w, LO, HI))
    if problems:
        for p in problems:
            print("FAIL", p)
        sys.exit(1)

    total = 0
    for rel, old in OLD.items():
        p = ROOT / rel
        s = p.read_text(encoding="utf-8")
        new = NEW[rel]
        n = s.count(old)
        if n == 0:
            # 幂等：已经是新版？
            already = s.count(new)
            print("%-26s 无旧串（新版命中 %d 处）%s" % (rel, already, "✅ 已修" if already else "⚠️ 需人工核"))
            continue
        out = s.replace(old, new)
        assert old not in out, rel
        assert out.count(new) == n, rel
        total += n
        print("%-26s 旧串 %d 处 → %s（%d→%d 宽）" % (rel, n, "已替换" if args.apply else "待替换", W(old), W(new)))
        if args.apply:
            p.write_text(out, encoding="utf-8")

    print("\n合计替换处：%d %s" % (total, "（已落盘）" if args.apply else "（空跑，未落盘）"))

    # 复核：全站仍偏短的产品页
    short = []
    for p in sorted(list((ROOT / "products").glob("*.html")) +
                    [q for d in ("de", "ja", "ko", "fr", "it", "es")
                     for q in (ROOT / d / "products").glob("*.html")]):
        s = p.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r'<meta name="description" content="([^"]*)"', s)
        if m and W(m.group(1)) < 80:
            short.append((str(p.relative_to(ROOT)), W(m.group(1))))
    print("复核：全站产品页 description <80 宽 → %d 处" % len(short))
    for f, w in short:
        print("   %-46s %3d" % (f, w))


if __name__ == "__main__":
    main()
