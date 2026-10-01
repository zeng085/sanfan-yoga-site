#!/usr/bin/env python3
"""普拉提板块 SEO+GEO 审计（2026-10-01）
判据全部来自站点既有惯例与铁律（meta 按显示宽度：CJK×2，title 60 / desc 155）。
只审计、不修改。输出分两类：✗=确定性缺陷；⚠=改进建议（GEO/内容层）。
"""
import json, re, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = sorted((ROOT / "pilates").glob("*.html"))
LANGS = ["en", "de", "ja", "ko", "fr", "it", "es"]

fails, warns = [], []

def w(page, msg):
    pname = page if isinstance(page, str) else page.name
    (fails if msg.startswith("✗") else warns).append(f"{pname}: {msg}")

def disp_w(s):
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)

def text_of(html):
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    html = re.sub(r"\s+", " ", html)
    # 去掉被 CSS 隐藏的另一种语言副本（粗略：中文页按双份算会虚高，这里按单语言估）
    return html

print(f"审计 {len(PAGES)} 页\n" + "=" * 72)

titles, descs = {}, {}
for p in PAGES:
    h = p.read_text(encoding="utf-8")
    rel = f"pilates/{p.name}"

    # ---- A1. title ----
    m = re.search(r"<title>(.*?)</title>", h, re.S)
    if not m:
        w(rel, "✗ 缺 <title>")
    else:
        t = m.group(1).strip()
        titles[rel] = t
        dw = disp_w(t)
        if dw > 60:
            w(rel, f"✗ title 显示宽度 {dw} > 60（{t[:60]}…）")
        if not re.search(r"OEM|ODM|Manufacturer|Supplier", t):
            w(rel, "⚠ title 无商业意图词（OEM/ODM/Manufacturer）")

    # ---- A2. meta description ----
    m = re.search(r'<meta name="description" content="([^"]*)"', h)
    if not m:
        w(rel, "✗ 缺 meta description")
    else:
        d = m.group(1)
        descs[rel] = d
        dw = disp_w(d)
        if dw > 155:
            w(rel, f"✗ description 显示宽度 {dw} > 155（会截断）")
        elif dw < 70:
            w(rel, f"⚠ description 偏短 {dw}（<70）")

    # ---- A3. canonical ----
    m = re.search(r'<link rel="canonical" href="([^"]+)"', h)
    if not m:
        w(rel, "✗ 缺 canonical")
    elif m.group(1) != f"https://fjsanfan.com/{rel}":
        w(rel, f"✗ canonical 不指向自身：{m.group(1)}")

    # ---- A4. hreflang 完整性与目标页存在性 ----
    hreflangs = dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', h))
    miss = [l for l in LANGS + ["x-default"] if l not in hreflangs]
    if miss:
        w(rel, f"✗ hreflang 缺 {miss}")
    else:
        for l, u in hreflangs.items():
            path = u.replace("https://fjsanfan.com/", "")
            if l == "x-default":
                continue
            # en 指向自身路径
            if not (ROOT / path).exists():
                w(rel, f"✗ hreflang {l} 目标不存在（本地无该文件）: {path}")

    # ---- A5. OG / Twitter ----
    for tag in ["og:title", "og:description", "og:image", "og:url"]:
        if f'property="{tag}"' not in h:
            w(rel, f"✗ 缺 {tag}")
    if 'name="twitter:card"' not in h:
        w(rel, "✗ 缺 twitter:card")
    m = re.search(r'property="og:image" content="([^"]+)"', h)
    if m:
        img = m.group(1).replace("https://fjsanfan.com/", "")
        if not (ROOT / img).exists():
            w(rel, f"✗ og:image 文件不存在: {img}")
    if 'name="robots" content="noindex' in h:
        w(rel, "✗ 被 noindex")

    # ---- B. 结构化数据 ----
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S)
    graphs = []
    for b in blocks:
        try:
            graphs.append(json.loads(b))
        except Exception as e:
            w(rel, f"✗ JSON-LD 解析失败: {e}")
    types = []
    for g in graphs:
        t = g.get("@type", "?")
        types.append(t if isinstance(t, str) else ",".join(t))
    # 展开嵌套
    flat_types = list(types)
    for g in graphs:
        for k in ("mainEntity", "itemListElement", "hasPart", "@graph"):
            pass
    def walk(node, acc):
        if isinstance(node, dict):
            t = node.get("@type")
            if t: acc.append(t if isinstance(t, str) else ",".join(t))
            for v in node.values(): walk(v, acc)
        elif isinstance(node, list):
            for v in node: walk(v, acc)
    for g in graphs:
        walk(g, flat_types)

    faq_n = sum(1 for t in flat_types if t == "Question")
    prod_n = sum(1 for t in flat_types if t == "Product")
    itemlist = [g for g in graphs if g.get("@type") == "ItemList"]
    cards = len(re.findall(r'class="model-card"', h))
    breadcrumb = any(t == "BreadcrumbList" for t in flat_types)
    if not breadcrumb:
        w(rel, "✗ 缺 BreadcrumbList")
    if itemlist:
        for il in itemlist:
            n_decl = il.get("numberOfItems")
            n_real = len(il.get("itemListElement", []))
            if n_decl != n_real:
                w(rel, f"✗ ItemList numberOfItems={n_decl} ≠ 实际 {n_real}")
            if cards and n_real != cards:
                w(rel, f"✗ ItemList {n_real} 项 ≠ 型号卡 {cards} 张")
    if cards and prod_n == 0:
        w(rel, f"⚠ {cards} 张型号卡但 JSON-LD 无 Product 实体（AI 无法逐型号引用）")
    # FAQ DOM vs JSON
    faq_dom = len(re.findall(r'class="faq-a"', h))
    if faq_dom and faq_dom != faq_n:
        w(rel, f"✗ FAQ 页面 {faq_dom} 条 vs JSON-LD Question {faq_n} 条")

    # ---- C1. H1 / 标题层级 ----
    h1s = re.findall(r"<h1[ >]", h)
    if len(h1s) != 1:
        w(rel, f"✗ H1 数量 {len(h1s)}（应 1）")
    hs = re.findall(r"<h([1-6])", h)
    lv = [int(x) for x in hs]
    for i in range(1, len(lv)):
        if lv[i] - lv[i - 1] > 1:
            w(rel, f"⚠ 标题层级跳级 h{lv[i-1]}→h{lv[i]}（第 {i} 处）")
            break

    # ---- C2. 图片 alt ----
    imgs = re.findall(r"<img [^>]*>", h)
    noalt = [g for g in imgs if 'alt="' not in g]
    emptyalt = [g for g in imgs if re.search(r'alt="\s*"', g)]
    if noalt:
        w(rel, f"✗ {len(noalt)} 张 img 无 alt 属性")
    if emptyalt:
        w(rel, f"⚠ {len(emptyalt)} 张 img alt 为空（装饰图可接受，内容图不可）")

    # ---- C3. 字数（EN 视角粗估：取 lang-en 主导时全文的一半作下限参考） ----
    words = len(re.findall(r"[A-Za-z][A-Za-z'-]*", text_of(h)))
    if words / 2 < 400:
        w(rel, f"⚠ 正文字数偏低（单语言约 {words // 2} 词 < 400）")

print()
print("== 结构化数据类型分布（全板块） ==")
allt = {}
for p in PAGES:
    h = p.read_text(encoding="utf-8")
    for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        try:
            acc = []
            def walk(n, a):
                if isinstance(n, dict):
                    t = n.get("@type")
                    if t: a.append(t if isinstance(t, str) else ",".join(t))
                    for v in n.values(): walk(v, a)
                elif isinstance(n, list):
                    for v in n: walk(v, a)
            walk(json.loads(b), acc)
            for t in acc: allt[t] = allt.get(t, 0) + 1
        except Exception: pass
for t, n in sorted(allt.items(), key=lambda x: -x[1]):
    print(f"  {t:24s} {n}")

print()
print("== title/description 重复检查 ==")
for name, pool in [("title", titles), ("description", descs)]:
    seen = {}
    for k, v in pool.items():
        seen.setdefault(v, []).append(k)
    for v, ks in seen.items():
        if len(ks) > 1:
            w("（跨页）", f"✗ {name} 重复 ×{len(ks)}: {ks}")

print()
print("== sitemap / llms.txt 覆盖 ==")
sm = (ROOT / "sitemap.xml")
if sm.exists():
    smt = sm.read_text(encoding="utf-8", errors="ignore")
    for p in PAGES:
        u = f"https://fjsanfan.com/pilates/{p.name}"
        if u not in smt:
            w("sitemap.xml", f"✗ 缺 {u}")
    print(f"  sitemap.xml 共 {smt.count('<loc>')} 条 URL")
else:
    w("sitemap.xml", "✗ 文件不存在")
for f in ["llms.txt", "llms-full.txt"]:
    fp = ROOT / f
    if fp.exists():
        txt = fp.read_text(encoding="utf-8", errors="ignore")
        n = sum(1 for p in PAGES if p.name in txt)
        print(f"  {f}: 提及 pilates 页面 {n}/9")
    else:
        w(f, "✗ 不存在")

print()
print("=" * 72)
print(f"✗ 确定性缺陷 {len(fails)} 项")
for x in fails: print("  " + x)
print(f"\n⚠ 改进建议 {len(warns)} 项")
for x in warns: print("  " + x)
