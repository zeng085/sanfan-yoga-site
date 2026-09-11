#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把老页（ym1–ym7）的信息按「英文站为准」做补齐 + 校正。
口径（2026-09-11 用户拍板）：
  - 英文站有具体值的 → 补上 / 覆盖（冲突时英文站为准）
  - 英文站没有的字段（MOQ / 认证 / Logo 等站点标准字段）→ 保留
  - 范围：仅 EN + 中文同页（root）；6 语言版本本次不动
yml 家族页说明：ym1/ym2 对应英文站「同族多个产品」的并集，不是 1:1，
所以尺寸取同族出现过值的并集，不做单产品覆盖。

用法：
    python3 i18n_build/align_ym_pages.py --dry-run
    python3 i18n_build/align_ym_pages.py
"""
import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# ── 改动表 ────────────────────────────────────────────────────────────────
# name_en/name_zh 为 None 表示不改名；desc_en/desc_zh 为 None 表示改卡片描述
CHANGES = {
    "ym1": {
        # 名称与英文站一致，不改
        "specs": {
            "Size": "183×61 / 183×66 / 183×80 / 183×90 cm",
            "Weight": "700 / 800 / 950 / 1050 / 1100 / 1200 g/pc",
            "Colors & Print": "Purple / Blue / Black / Light Purple / Soft Pink / Matcha Green, dual-color combos &amp; custom prints",
            "Packaging": "Poly Bag + Carton or customized",
        },
        "desc_en": 'Eco TPE (single / double layer), non-slip textured surface, widths 61 / 66 / 80 / 90 cm (24" / 26" / 31.5" / 35.5"), thickness 6–12 mm (1/4"–1/2"). Solid, economy and special grades.',
        "desc_zh": "环保 TPE（单层/双层），防滑纹理表面，宽度 61 / 66 / 80 / 90 cm，厚度 6–12 mm。可选实重、经济、特供等级。",
    },
    "ym2": {
        "specs": {
            "Colors & Print": "Purple / Blue / Black, dual-color combos &amp; custom prints",
            "Packaging": "Poly Bag + Carton or customized",
        },
    },
    "ym3": {
        "name_en": "TPE Double Yoga Mat",
        "name_zh": "TPE 双人瑜伽垫",
        "specs": {
            "Packaging": "Poly Bag + Carton or customized",
        },
    },
    "ym4": {
        "name_en": "TPE Folding Yoga Mat",
        "name_zh": "TPE 折叠瑜伽垫",
        "specs": {
            "Colors & Print": "Green / Blue / Pink / Purple / Red or Customized",
            "Feature": "Non-slip, Eco Friendly, Foldable, Space-saving, Wear-Resistant",
            "Packaging": "Folded, poly bag + carton or customized",
        },
    },
    "ym5": {
        "name_en": "PU Rubber Yoga Mat",
        "name_zh": "PU 橡胶瑜伽垫",
        "specs": {
            "Material": "PU + Rubber (natural rubber base, PU top)",
            "Colors & Print": "Purple / Pink / Green / Black / Gray / Blue / Sky Blue / Orange / Mustard Green / Milk Tea / Soft Pink or Customized",
            "Packaging": "Poly Bag + Carton or customized",
        },
        "desc_en": "Natural rubber base + PU anti-slip top; premium grip for hot yoga and studios.",
        "desc_zh": "天然橡胶底 + PU 防滑面；高温瑜伽与瑜伽馆高端抓地（“土豪垫”）。",
    },
    "ym6": {
        "name_en": "Matte PU Rubber Yoga Mat",
        "name_zh": "磨砂 PU 橡胶瑜伽垫",
        "specs": {
            "Material": "Matte PU + Natural Rubber",
            "Colors & Print": "Milk Tea / Dark Gray / Soft Pink / Light Purple / Jade Green",
            "Packaging": "Poly Bag + Carton or customized",
        },
    },
    "ym7": {
        "name_en": "TPE Camouflage Yoga Mat",
        "name_zh": "TPE 迷彩瑜伽垫",
        "specs": {
            "Size": "183×68 cm",
            "Packaging": "Poly Bag + Carton or customized",
        },
    },
}

# 改名时同步替换的品牌后缀
EN_SUFFIX = " — SANFAN"
EN_SUFFIX_LONG = " — SANFAN Yoga & Fitness Manufacturer"
ZH_SUFFIX = " — 三梵"


def esc_amp(s):
    """规格标签在 HTML 里是 Colors &amp; Print"""
    return s


def update_page(slug, cfg, dry):
    """改 products/<slug>.html 的 head / h1 / JSON-LD / 规格表"""
    p = ROOT / "products" / f"{slug}.html"
    t = p.read_text(encoding="utf-8")
    orig = t
    notes = []

    name_en = cfg.get("name_en")
    name_zh = cfg.get("name_zh")

    # ⚠️ 必须锚定 <h1> 同时取中英两份——页面里第一个 .lang-zh 是**面包屑类目词**，
    #    用非锚定正则会改坏面包屑（`<span class="bc-cat">` 里的「瑜伽垫」）。
    h1m = re.search(
        r'<h1><span class="lang-en">([\s\S]*?)</span><span class="lang-zh">([\s\S]*?)</span></h1>', t)
    if not h1m:
        notes.append("✗ 未匹配到 <h1> 双 span 结构，改名跳过")
        return False, notes
    old_en_full, old_zh_full = h1m.group(1), h1m.group(2)
    old_en = old_en_full.replace(EN_SUFFIX, "")
    old_zh = old_zh_full.replace(ZH_SUFFIX, "")

    if name_en:
        t = t.replace(f"<title>{old_en}{EN_SUFFIX_LONG}</title>",
                      f"<title>{name_en}{EN_SUFFIX_LONG}</title>")
        t = t.replace(f'content="{old_en}{EN_SUFFIX}"', f'content="{name_en}{EN_SUFFIX}"')
        t = t.replace(
            f'<h1><span class="lang-en">{old_en_full}</span>',
            f'<h1><span class="lang-en">{name_en}{EN_SUFFIX}</span>')
        t = re.sub(r'("name":\s*")' + re.escape(old_en) + r'(")',
                   lambda m: m.group(1) + name_en + m.group(2), t, count=1)
        notes.append(f"改名 EN：{old_en} → {name_en}")

    if name_zh:
        t = t.replace(f'<span class="lang-zh">{old_zh_full}</span></h1>',
                      f'<span class="lang-zh">{name_zh}{ZH_SUFFIX}</span></h1>')
        notes.append(f"改名 ZH：{old_zh} → {name_zh}")

    # 规格表：按 lang-en 标签定位行，替换 <td>
    for key, val in (cfg.get("specs") or {}).items():
        lab = key.replace("&", "&amp;")
        pat = re.compile(
            r'(<tr><th><span class="lang-en">' + re.escape(lab) +
            r'</span>[\s\S]*?</th>)<td>([\s\S]*?)</td>')
        m = pat.search(t)
        if not m:
            notes.append(f"⚠ 规格行未找到：{key}")
            continue
        old = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', m.group(2))).strip()
        t = pat.sub(lambda mm: mm.group(1) + "<td>" + val + "</td>", t, count=1)
        notes.append(f"规格 {key}：{old[:52]} → {val[:52]}")

    if not dry and t != orig:
        p.write_text(t, encoding="utf-8")
    return t != orig, notes


def update_i18n(slug, cfg, dry):
    """改 assets/js/main.js 里 ymN.t / ymN.d 的中英文案"""
    p = ROOT / "assets" / "js" / "main.js"
    t = p.read_text(encoding="utf-8")
    orig = t
    notes = []

    def rep(key, new):
        nonlocal t
        pat = re.compile(r"('" + re.escape(key) + r"':\s*')((?:[^'\\]|\\.)*)(')")
        if not pat.search(t):
            notes.append(f"⚠ i18n 键未找到：{key}")
            return
        t = pat.sub(lambda m: m.group(1) + new.replace("'", r"\'") + m.group(3), t)

    # EN 块与 ZH 块各出现一次（同键两处），按出现顺序处理
    def rep_nth(key, new, n):
        nonlocal t
        pat = re.compile(r"('" + re.escape(key) + r"':\s*')((?:[^'\\]|\\.)*)(')")
        hits = list(pat.finditer(t))
        if len(hits) <= n:
            notes.append(f"⚠ i18n 键 {key} 第 {n+1} 处未找到")
            return
        m = hits[n]
        t = t[:m.start()] + m.group(1) + new.replace("'", r"\'") + m.group(3) + t[m.end():]

    if cfg.get("name_en"):
        rep_nth(f"{slug}.t", cfg["name_en"], 0)
        notes.append(f"i18n {slug}.t (EN) → {cfg['name_en']}")
    if cfg.get("name_zh"):
        rep_nth(f"{slug}.t", cfg["name_zh"], 1)
        notes.append(f"i18n {slug}.t (ZH) → {cfg['name_zh']}")
    if cfg.get("desc_en"):
        rep_nth(f"{slug}.d", cfg["desc_en"], 0)
        notes.append(f"i18n {slug}.d (EN) 已更新")
    if cfg.get("desc_zh"):
        rep_nth(f"{slug}.d", cfg["desc_zh"], 1)
        notes.append(f"i18n {slug}.d (ZH) 已更新")

    if not dry and t != orig:
        p.write_text(t, encoding="utf-8")
    return t != orig, notes


def update_listing(slug, cfg, dry):
    """改 products.html 卡片里的 fallback 文案（h4/p 内的静态文本）"""
    p = ROOT / "products.html"
    t = p.read_text(encoding="utf-8")
    orig = t
    notes = []
    m = re.search(r'<a class="prod-card" href="products/' + slug + r'\.html">([\s\S]*?)</a>', t)
    if not m:
        return False, [f"⚠ 列表页未找到 {slug} 卡片"]
    block = m.group(0)
    new_block = block
    if cfg.get("name_en"):
        new_block = re.sub(r'(<h4 data-i18n="' + slug + r'\.t">)([\s\S]*?)(</h4>)',
                           lambda mm: mm.group(1) + cfg["name_en"] + mm.group(3), new_block)
    if cfg.get("desc_en"):
        new_block = re.sub(r'(<p data-i18n="' + slug + r'\.d">)([\s\S]*?)(</p>)',
                           lambda mm: mm.group(1) + cfg["desc_en"] + mm.group(3), new_block)
    if new_block != block:
        t = t.replace(block, new_block)
        notes.append("列表页卡片 fallback 文案已同步")
    if not dry and t != orig:
        p.write_text(t, encoding="utf-8")
    return t != orig, notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", default="", help="只处理某个 slug，如 ym5")
    args = ap.parse_args()

    total = 0
    for slug, cfg in CHANGES.items():
        if args.only and slug != args.only:
            continue
        print("=" * 74)
        print(f"{slug}")
        for fn in (update_page, update_i18n, update_listing):
            changed, notes = fn(slug, cfg, args.dry_run)
            total += len(notes)
            for n in notes:
                print(f"   {n}")
        print(f"   → {'（dry-run，未写盘）' if args.dry_run else '已写盘'}")
    print("=" * 74)
    print(f"共 {total} 处改动")

    # 语法自检
    if not args.dry_run:
        import subprocess
        r = subprocess.run(
            ["/Users/mac-zlg/.workbuddy/binaries/node/versions/22.12.0/bin/node",
             "--check", str(ROOT / "assets" / "js" / "main.js")],
            capture_output=True, text=True,
            env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin"})
        print("main.js 语法自检:", "OK" if r.returncode == 0 else r.stderr[:400])
        if r.returncode != 0:
            sys.exit(1)


if __name__ == "__main__":
    main()
