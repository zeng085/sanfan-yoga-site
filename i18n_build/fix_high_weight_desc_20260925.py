#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""高权重页 description 压缩（EN 侧）—— 2026-09-25

为什么要改：audit 报「description 超 160 宽」69 页，其中**站内权重最高的 11 个页**
（内链 70–98，全站流量入口）desc 196–217 宽，SERP 里被截断的位置常常正好是
OEM / MOQ / private label 这些决定「点不点」的词。

站内权重标尺 = 内链数（现成、免外部数据），内链 >=70 的 20 页里 11 页 desc 超长。

改法：
  * 砍参数枚举（183x61cm, 183x80cm, 6mm/8mm…），保住商业词
    （factory-direct / OEM/ODM / private label / MOQ 100 pcs / 7-day sampling）
  * 一条 desc 在页面里出现 **4 个位置**，必须同步：
        <meta name="description">  /  og:description  /  twitter:description  /
        页面自身 JSON-LD 的 "description"
    ⚠️ 页面里还有**第二条** JSON-LD description，那是 Organization 的固定简介
       （Vertically integrated OEM/ODM manufacturer…），**不要动**。
  * ⚠️ HTML 转义形态可能不同：本批 `yoga-props-accessories.html` 的 meta 里是
    `&amp;`、JSON-LD 里是 `&` —— **同一句 desc 是两份不同串**，所以按形态分别替换，
    不能只 replace 一次。新文案一律不写 `&`，从源头避开这个坑。

用法：
  python3 fix_high_weight_desc_20260925.py            # dry-run：算宽度、报命中
  python3 fix_high_weight_desc_20260925.py --apply
  python3 fix_high_weight_desc_20260925.py --check
"""
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 新 description（<=160 显示宽，>=120 显示宽）。刻意不使用 & 以避免转义歧义。
NEW_DESC = {
    "applications/index.html":
        "Yoga mats and fitness gear by application: studio fit-outs, gyms, hotels, "
        "private label, recovery, e-commerce. Factory-direct OEM/ODM, MOQ 100 pcs.",
    "applications/recovery-physio.html":
        "Factory-direct foam rollers, fascia guns and massage balls for clinics, "
        "physio rooms and gyms. Custom density, EVA and EPP builds, MOQ 100 pcs.",
    "applications/retail-private-label.html":
        "Private-label yoga mats, rollers, bands and fitness gear from one factory. "
        "Custom colour, logo, retail packaging and barcodes. 147 SKUs, MOQ 100 pcs.",
    "applications/gyms-fitness-clubs.html":
        "Factory-direct gym equipment for clubs: dumbbells, barbells, rings, floor "
        "mats, bands, jump ropes, recovery tools. One colour system, MOQ 100 pcs.",
    "applications/yoga-pilates-studios.html":
        "Fit out a yoga or Pilates studio from one factory: TPE, PU, cork and suede "
        "mats, blocks, bolsters, reformer mats, hammocks. Logo ready, MOQ 100 pcs.",
    "applications/hotels-resorts-spas.html":
        "Hospitality-grade mats with your hotel logo: low-odour TPE and rubber for "
        "guest rooms, round meditation mats, cork spa retail ranges. MOQ 100 pcs.",
    "yoga-props-accessories.html":
        "Yoga props and accessories: blocks, balls, rings, bags and aerial hammocks. "
        "Factory-direct OEM/ODM, custom colour and logo, MOQ 100 pcs, 7-day sampling.",
    "strength-training.html":
        "Strength and fitness gear: silicone weights, ab rollers, balance boards, "
        "steppers. Factory-direct OEM/ODM, custom colour, MOQ 100 pcs, 7-day sampling.",
    "massage-recovery.html":
        "Massage and recovery tools: fascia guns, fascia balls and massage sticks. "
        "Factory-direct OEM/ODM, custom colour and logo, MOQ 100 pcs, 7-day sampling.",
    "foam-rollers.html":
        "Foam rollers in EVA and EPP: solid, hollow and vibrating builds. "
        "Factory-direct OEM/ODM, custom size and density, MOQ 100 pcs, 7-day sampling.",
    "resistance-bands.html":
        "Resistance bands: loop, tube, figure-8 and power bands. Factory-direct "
        "OEM/ODM, custom resistance and colour, MOQ 100 pcs, 7-day sampling.",
}

RE_META_DESC = re.compile(r'<meta\s+name="description"\s+content="([^"]*)"', re.I)
RE_JSONLD_DESC = re.compile(r'"description"\s*:\s*"([^"]*)"')
ORG_MARK = "Vertically integrated OEM/ODM manufacturer"   # Organization 固定简介，勿动


def W(s):
    """显示宽度：CJK 记 2（与审计器同一口径）。"""
    return sum(2 if ord(c) > 0x2E80 else 1 for c in s)


def read(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return fh.read()


def write(p, s):
    with open(p, "w", encoding="utf-8", newline="") as fh:
        fh.write(s)


def main():
    args = set(sys.argv[1:])
    apply = "--apply" in args
    check = "--check" in args
    print("=" * 74)
    print("模式：%s" % ("APPLY" if apply else ("CHECK" if check else "DRY-RUN")))
    print("=" * 74)
    print("%-44s %5s %5s %6s %s" % ("page", "旧宽", "新宽", "替换", "断言"))
    bad = []
    for rel, new in sorted(NEW_DESC.items()):
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            bad.append("%s 不存在" % rel)
            continue
        s = read(p)
        m = RE_META_DESC.search(s)
        if not m:
            bad.append("%s 找不到 meta description" % rel)
            continue
        old_raw = m.group(1)                          # HTML 形态（可能含 &amp;）
        old_txt = html.unescape(old_raw).strip()      # 文本形态（JSON-LD 用）
        nw = W(new)

        if check:
            hit = sum(1 for x in RE_JSONLD_DESC.finditer(s)
                      if ORG_MARK not in x.group(1) and x.group(1).strip() == new)
            print("%-44s %5d %5d %6s %s" % (rel, W(old_txt), nw,
                                            "已改" if hit else "未改",
                                            "" if hit else "待处理"))
            continue

        if not (120 <= nw <= 160):
            bad.append("%s 新 desc 宽度 %d 越界（须 120-160）" % (rel, nw))
            continue

        ns, n1 = s.replace(old_raw, new), s.count(old_raw)
        # JSON-LD 那份（形态可能不同）——只替换页面自身那条
        def repl_json(m2):
            if ORG_MARK in m2.group(1):
                return m2.group(0)
            if m2.group(1).strip() == old_txt:
                return '"description": "%s"' % new
            return m2.group(0)
        ns, n2 = RE_JSONLD_DESC.subn(repl_json, ns)
        n2 = 1 if n2 else 0
        # 旧串应完全消失
        left = ns.count(old_raw) + sum(
            1 for x in RE_JSONLD_DESC.finditer(ns)
            if ORG_MARK not in x.group(1) and x.group(1).strip() == old_txt)
        assert not left, "%s 仍有残留旧 desc" % rel
        ok = "%d 处" % (n1 + n2)
        print("%-44s %5d %5d %6s %s" % (rel, W(old_txt), nw, ok,
                                        "旧串已清" if not left else "残留!"))
        if apply:
            write(p, ns)
    print("-" * 74)
    print("共 %d 个文件；新 desc 宽度全部在 120-160 之间" % len(NEW_DESC))
    if bad:
        print("!!! 异常：")
        for b in bad:
            print("   -", b)
    if not apply and not check:
        print()
        print("提示：加 --apply 落盘。落盘后必须重跑 audit 确认 69 页降下来。")


if __name__ == "__main__":
    main()
