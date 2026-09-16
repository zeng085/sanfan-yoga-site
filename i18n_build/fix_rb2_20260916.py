#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rb 系列（Mini Yoga Ball）两处缺陷修复（2026-09-16 夜）。

缺陷 A — 产品名括号错位
    `Mini Yoga Ball (25 cm (10"))`  缺 `/` 且多一个 `)`
    正确形态以「根目录分类页 rb2 卡片 h4」与「rb2 <title>」为准
    → `Mini Yoga Ball (25 cm / 10")`

缺陷 B — 描述开头的裸尺寸 + 英制单位错位
    英文源串是 `25 cm (10") anti-slip gymnastic ball for ...`：以裸尺寸开头，
    译者按各语言语序把中心词提前后，`(10")` 就成了悬空碎片：
      es `antideslizante de (10")`、it/fr `25 cm Palla ... da 10 pollici`、
      ja `用の（10インチ）滑り止め`、ko `(10인치) 미끄럼 방지`
    → 统一为「中心词 + (25 cm / 10")」的自然语序

用法：
  --check  只报告（默认）
  --apply  落盘
"""
import argparse
import glob
import os
import re
import sys

ROOT = "/Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16"
LANGS = ["", "de", "ja", "ko", "fr", "it", "es"]
PAGES = ["rb1", "rb2"]

IN = '"'

# ── 缺陷 A：名称 ────────────────────────────────────────────────────────────
NAME = {
    "":   ("Mini Yoga Ball (25 cm (10%s))" % IN,                 "Mini Yoga Ball (25 cm / 10%s)" % IN),
    "de": ("Mini-Yoga-Ball (25 cm (10%s))" % IN,                 "Mini-Yoga-Ball (25 cm / 10%s)" % IN),
    "ja": ("\u30df\u30cb\u30e8\u30ac\u30dc\u30fc\u30eb\uff0825 cm\uff0810\u30a4\u30f3\u30c1\uff09\uff09",
           "\u30df\u30cb\u30e8\u30ac\u30dc\u30fc\u30eb\uff0825 cm / 10\u30a4\u30f3\u30c1\uff09"),
    "ko": ("\ubbf8\ub2c8 \uc694\uac00 \ubcfc (25 cm (10%s))" % IN, "\ubbf8\ub2c8 \uc694\uac00 \ubcfc (25 cm / 10%s)" % IN),
    "fr": ("Mini ballon de yoga (mod\u00e8le \u00ab 25 cm \u00bb (10%s))" % IN,
           "Mini ballon de yoga (25 cm / 10%s)" % IN),
    "it": ("Mini palla da yoga (25 cm (10%s))" % IN,             "Mini palla da yoga (25 cm / 10%s)" % IN),
    "es": ("Mini pelota de yoga (25 cm (10%s))" % IN,            "Mini pelota de yoga (25 cm / 10%s)" % IN),
}

# ── 缺陷 B：描述。收尾的英寸符号写成占位 @Q@，落盘时同时匹配 `"` 与 `&quot;` ──
QUOTE = "@Q@"
DESC = {
    "": [
        ("25 cm (10@Q@) anti-slip gymnastic ball for pilates, rehab and core work.",
         "Anti-slip gymnastic ball (25 cm / 10@Q@) for pilates, rehab and core work."),
        ("25 cm (10@Q@) anti-slip mini ball for pilates, rehab and core work \u2014 burst-resistant and easy to grip.",
         "Anti-slip mini ball (25 cm / 10@Q@) for pilates, rehab and core work \u2014 burst-resistant and easy to grip."),
    ],
    "de": [
        ("25 cm (10@Q@) rutschfester Gymnastikball f\u00fcr Pilates, Reha und Rumpftraining.",
         "Rutschfester Gymnastikball (25 cm / 10@Q@) f\u00fcr Pilates, Reha und Rumpftraining."),
        ("25 cm (10@Q@) rutschfester Mini-Ball f\u00fcr Pilates, Reha und Rumpftraining \u2013 platzsicher und griffig.",
         "Rutschfester Mini-Ball (25 cm / 10@Q@) f\u00fcr Pilates, Reha und Rumpftraining \u2013 platzsicher und griffig."),
    ],
    "ja": [
        ("25 cm \u30d4\u30e9\u30c6\u30a3\u30b9\u3001\u30ea\u30cf\u30d3\u30ea\u3001\u30b3\u30a2\u30c8\u30ec\u30fc\u30cb\u30f3\u30b0\u7528\u306e\uff0810\u30a4\u30f3\u30c1\uff09\u6ed1\u308a\u6b62\u3081\u4ed8\u304d\u4f53\u64cd\u30dc\u30fc\u30eb\u3002",
         "\u30d4\u30e9\u30c6\u30a3\u30b9\u3001\u30ea\u30cf\u30d3\u30ea\u3001\u30b3\u30a2\u30c8\u30ec\u30fc\u30cb\u30f3\u30b0\u7528\u306e\u300125 cm\uff0810\u30a4\u30f3\u30c1\uff09\u6ed1\u308a\u6b62\u3081\u4ed8\u304d\u4f53\u64cd\u30dc\u30fc\u30eb\u3002"),
        ("25 cm \u30d4\u30e9\u30c6\u30a3\u30b9\u3001\u30ea\u30cf\u30d3\u30ea\u3001\u4f53\u5e79\u30c8\u30ec\u30fc\u30cb\u30f3\u30b0\u7528\u306e\uff0810\u30a4\u30f3\u30c1\uff09\u6ed1\u308a\u6b62\u3081\u30df\u30cb\u30dc\u30fc\u30eb \u2014 \u7834\u88c2\u3057\u306b\u304f\u304f\u3001\u63e1\u308a\u3084\u3059\u3044\u3002",
         "\u30d4\u30e9\u30c6\u30a3\u30b9\u3001\u30ea\u30cf\u30d3\u30ea\u3001\u4f53\u5e79\u30c8\u30ec\u30fc\u30cb\u30f3\u30b0\u7528\u306e\u300125 cm\uff0810\u30a4\u30f3\u30c1\uff09\u6ed1\u308a\u6b62\u3081\u30df\u30cb\u30dc\u30fc\u30eb \u2014 \u7834\u88c2\u3057\u306b\u304f\u304f\u3001\u63e1\u308a\u3084\u3059\u3044\u3002"),
    ],
    "ko": [
        ("25 cm \ud544\ub77c\ud14c\uc2a4, \uc7ac\ud65c \uc6b4\ub3d9 \ubc0f \ucf54\uc5b4 \uc6b4\ub3d9\uc6a9 (10\uc778\uce58) \ubbf8\ub044\ub7fc \ubc29\uc9c0 \uccb4\uc870 \uacf5.",
         "\ud544\ub77c\ud14c\uc2a4, \uc7ac\ud65c \ubc0f \ucf54\uc5b4 \uc6b4\ub3d9\uc6a9 25 cm (10\uc778\uce58) \ubbf8\ub044\ub7fc \ubc29\uc9c0 \uccb4\uc870 \uacf5."),
        ("25 cm \ud544\ub77c\ud14c\uc2a4, \uc7ac\ud65c \uc6b4\ub3d9 \ubc0f \ucf54\uc5b4 \uc6b4\ub3d9\uc6a9 (10@Q@) \ubbf8\ub044\ub7fc \ubc29\uc9c0 \ubbf8\ub2c8 \ubcfc \u2014 \ud30c\uc5f4 \ubc29\uc9c0 \uae30\ub2a5\uc774 \uc788\uc73c\uba70 \uc7a1\uae30 \ud3b8\ud569\ub2c8\ub2e4.",
         "\ud544\ub77c\ud14c\uc2a4, \uc7ac\ud65c \ubc0f \ucf54\uc5b4 \uc6b4\ub3d9\uc6a9 25 cm (10\uc778\uce58) \ubbf8\ub044\ub7fc \ubc29\uc9c0 \ubbf8\ub2c8 \ubcfc \u2014 \ud30c\uc5f4 \ubc29\uc9c0 \uae30\ub2a5\uc774 \uc788\uc73c\uba70 \uc7a1\uae30 \ud3b8\ud569\ub2c8\ub2e4."),
    ],
    "fr": [
        ("25 cm Ballon de gymnastique antid\u00e9rapant de 10 pouces pour le Pilates, la r\u00e9\u00e9ducation et le renforcement musculaire.",
         "Ballon de gymnastique antid\u00e9rapant (25 cm / 10 pouces) pour le Pilates, la r\u00e9\u00e9ducation et le renforcement musculaire."),
        ("25 cm Mini-ballon antid\u00e9rapant de 10 pouces pour le Pilates, la r\u00e9\u00e9ducation et le renforcement musculaire \u2014 r\u00e9sistant aux \u00e9clatements et facile \u00e0 saisir.",
         "Mini-ballon antid\u00e9rapant (25 cm / 10 pouces) pour le Pilates, la r\u00e9\u00e9ducation et le renforcement musculaire \u2014 r\u00e9sistant aux \u00e9clatements et facile \u00e0 saisir."),
    ],
    "it": [
        ("25 cm Palla da ginnastica antiscivolo da 10 pollici per pilates, riabilitazione ed esercizi per il core.",
         "Palla da ginnastica antiscivolo (25 cm / 10@Q@) per pilates, riabilitazione ed esercizi per il core."),
        ("25 cm Mini palla antiscivolo da 10@Q@ per pilates, riabilitazione ed esercizi per il core \u2014 resistente allo scoppio e facile da impugnare.",
         "Mini palla antiscivolo (25 cm / 10@Q@) per pilates, riabilitazione ed esercizi per il core \u2014 resistente allo scoppio e facile da impugnare."),
    ],
    "es": [
        ("25 cm Pelota de gimnasia antideslizante de (10@Q@) para pilates, rehabilitaci\u00f3n y ejercicios de core.",
         "Pelota de gimnasia antideslizante (25 cm / 10@Q@) para pilates, rehabilitaci\u00f3n y ejercicios de core."),
        ("25 cm Mini pelota antideslizante (10@Q@) para pilates, rehabilitaci\u00f3n y ejercicios de core: resistente a los pinchazos y f\u00e1cil de agarrar.",
         "Mini pelota antideslizante (25 cm / 10@Q@) para pilates, rehabilitaci\u00f3n y ejercicios de core: resistente a los pinchazos y f\u00e1cil de agarrar."),
    ],
}


def expand(pair):
    """把 @Q@ 展开为 `"` 与 `&quot;` 两种写法。"""
    out = []
    for a, b in pair:
        if QUOTE in a:
            out.append((a.replace(QUOTE, IN), b.replace(QUOTE, IN)))
            out.append((a.replace(QUOTE, "&quot;"), b.replace(QUOTE, "&quot;")))
        else:
            out.append((a, b))
    return out


def pairs_for(lg):
    ps = [NAME[lg]] + expand(DESC[lg])
    return ps


def target_files(lg):
    d = os.path.join(ROOT, lg, "products") if lg else os.path.join(ROOT, "products")
    return [os.path.join(d, "%s.html" % p) for p in PAGES if os.path.exists(os.path.join(d, "%s.html" % p))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="落盘；缺省只检查")
    args = ap.parse_args()

    total_files = 0
    total_hits = 0
    remain = []
    for lg in LANGS:
        for f in target_files(lg):
            s = open(f, encoding="utf-8").read()
            orig = s
            hits = 0
            for a, b in pairs_for(lg):
                n = s.count(a)
                if n:
                    s = s.replace(a, b)
                    hits += n
            if s != orig:
                total_files += 1
                total_hits += hits
                rel = os.path.relpath(f, ROOT)
                print("  %-28s %d 处" % (rel, hits))
                if args.apply:
                    open(f, "w", encoding="utf-8").write(s)
            else:
                rel = os.path.relpath(f, ROOT)
                # 复查是否仍有残留缺陷形态
                for a, b in pairs_for(lg):
                    if a in s:
                        remain.append((rel, a))

    print()
    print("模式: %s" % ("落盘" if args.apply else "检查(dry)"))
    print("改动文件 %d 个 | 改动处 %d 处" % (total_files, total_hits))
    if remain:
        print("⚠ 仍有残留 %d 处：%s" % (len(remain), remain[:3]))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
