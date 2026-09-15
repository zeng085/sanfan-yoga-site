# -*- coding: utf-8 -*-
"""普拉提板块：链接有效性与指向正确性审计

覆盖：本地资源存在性、页内锚点、导航下拉/分类条/卡片/面包屑/导流带的**指向正确性**
（不是"能打开"而是"指向对的那一页"）、canonical 自指、sitemap 一致性、图片 alt。
"""
import json
import os
import re
import sys
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# 跟踪/统计类外部域名，不算资源
EXT_OK = ("google-analytics.com", "googletagmanager.com", "google.com", "gstatic.com",
          "doubleclick.net", "clarity.ms", "bing.com", "facebook.net")
SKIP_DIRS = {"outputs", ".git", "node_modules", "i18n_build", ".workbuddy"}

fail, warn = [], []


def add(kind, msg):
    (fail if kind == "fail" else warn).append(msg)


def resolve(page, href):
    """返回 ('file', abs_path) / ('anchor', id) / ('ext', url) / ('skip', href)"""
    h = href.strip()
    if not h:
        return ("skip", href)
    if h.startswith("#"):
        return ("anchor", h[1:])
    if h.startswith(("mailto:", "tel:", "javascript:", "data:")):
        return ("skip", href)
    if h.startswith(("//", "http://", "https://")):
        return ("ext", href)
    path, _, frag = h.partition("#")
    path = path.split("?")[0]
    if not path:
        return ("anchor", frag)
    if path.startswith("/"):
        p = os.path.join(ROOT, path.lstrip("/"))
    else:
        p = os.path.normpath(os.path.join(os.path.dirname(page), path))
    if p.endswith("/") or os.path.isdir(p):
        p = os.path.join(p, "index.html")
    return ("file", p)


def anchors_of(path):
    t = open(path, encoding="utf-8").read()
    return set(re.findall(r'\sid="([^"]+)"', t)) | set(re.findall(r'\sname="([^"]+)"', t))


def main():
    models = json.load(open("i18n_build/data/pilates_models.json", encoding="utf-8"))
    fams = models["families"]
    fam_by_key = {f["key"]: f for f in fams}

    pages = ["pilates/index.html"] + ["pilates/%s.html" % f["key"] for f in fams]
    pages = [p for p in pages if os.path.exists(p)]
    missing = [p for p in (["pilates/index.html"] + ["pilates/%s.html" % f["key"] for f in fams])
               if not os.path.exists(p)]
    for p in missing:
        add("fail", "缺页 %s" % p)

    total_links = 0
    for page in pages:
        t = open(page, encoding="utf-8").read()
        anc = anchors_of(page)
        # 本页应对应的族
        my_fam = None
        mm = re.match(r"pilates/(pilates-[a-z-]+)\.html$", page)
        if mm:
            my_fam = fam_by_key.get(mm.group(1))

        # ---------- 1. 所有 href/src 的可达性 ----------
        for attr, val in re.findall(r'\s(href|src)="([^"]+)"', t):
            total_links += 1
            kind, target = resolve(page, val)
            if kind == "ext":
                host = urlparse(target if "//" in target else "https:" + target).netloc
                if not any(e in host for e in EXT_OK):
                    pass  # 真实外链，不判错（人工复核时再看）
                continue
            if kind == "skip":
                continue
            if kind == "anchor":
                if target and target not in anc:
                    add("fail", "%s 页内锚点 #%s 不存在" % (page, target))
                continue
            if not os.path.exists(target):
                add("fail", "%s 死链 %s → %s" % (page, val, os.path.relpath(target, ROOT)))
            elif target.endswith(".html"):
                # 指向了 HTML，检查是否自指到错误的族
                base = os.path.basename(target)
                if base.startswith("pilates-") and base in fam_by_key:
                    # 该页若在 chip/nav 里，文案需与目标族匹配（下面专项查）
                    pass

        # ---------- 2. 分类条 chip 指向与文案 ----------
        for m in re.finditer(r'<a href="/pilates/(pilates-[a-z-]+)\.html" class="pl-chip">'
                             r'<span class="lang-en">([^<]*)</span><span class="lang-zh">([^<]*)</span>', t):
            key, en, zh = m.group(1), m.group(2), m.group(3)
            f = fam_by_key.get(key)
            if not f:
                add("fail", "%s chip 指向不存在的族 %s" % (page, key))
            elif en.strip() != f["en"].strip():
                add("fail", "%s chip 文案与目标不符：%s → 「%s」≠「%s」"
                    % (page, key, en.strip(), f["en"].strip()))

        # ---------- 3. 导航下拉 8 项 ----------
        for m in re.finditer(r'<a href="/pilates/(pilates-[a-z-]+)\.html" data-i18n="nav\.pl\.([a-z-]+)">([^<]*)</a>', t):
            key, dk, txt = m.group(1), m.group(2), m.group(3)
            if key.replace("pilates-", "") != dk:
                add("fail", "%s 导航项 key 与 href 不符：%s vs nav.pl.%s" % (page, key, dk))
            f = fam_by_key.get(key)
            if f and txt.strip() != f["en"].strip():
                add("fail", "%s 导航项文案与目标不符：%s → 「%s」≠「%s」"
                    % (page, key, txt.strip(), f["en"].strip()))

        # ---------- 4. index 卡片：指向 + 文字 + 型号数 ----------
        if page == "pilates/index.html":
            for m in re.finditer(r'<a href="/pilates/(pilates-[a-z-]+)\.html" class="pl-card[^"]*">(.*?)</a>',
                                 t, re.S):
                key, blk = m.group(1), m.group(2)
                f = fam_by_key.get(key)
                if not f:
                    add("fail", "index 卡片指向不存在的族 %s" % key)
                    continue
                en = re.search(r'<h3><span class="lang-en">([^<]*)</span>', blk)
                if not en:
                    add("fail", "index 卡片 %s 缺英文标题" % key)
                elif f["en"].strip() not in en.group(1).strip():
                    add("fail", "index 卡片 %s 标题与目标不符：「%s」" % (key, en.group(1).strip()))
                # 型号数文案：卡片里出现的 "N models"/"N 个型号" 必须等于该族型号数
                nums = re.findall(r'(\d+)\s*(?:</span><span class="lang-zh">|\s)*(?:models|个型号)', blk)
                if nums and str(len(f["models"])) not in nums:
                    add("fail", "index 卡片 %s 型号数写 %s，实际 %d"
                        % (key, nums, len(f["models"])))

        # ---------- 5. 面包屑 ----------
        bc = re.search(r'"@type"\s*:\s*"BreadcrumbList".*?\](?=\s*\})', t, re.S)
        if bc:
            names = re.findall(r'"name"\s*:\s*"([^"]+)"', bc.group(0))
            if "Pilates Apparatus" not in names and my_fam:
                add("fail", "%s 面包屑缺 Pilates 层级：%s" % (page, names))
        # 可见面包屑链接
        vis = re.findall(r'<nav class="breadcrumb[^"]*"[^>]*>(.*?)</nav>', t, re.S)
        if not vis:
            vis = re.findall(r'<div class="breadcrumb[^"]*"[^>]*>(.*?)</div>', t, re.S)
        if vis:
            # 族页必须能从面包屑点回板块首页；板块首页自身是末级，不该有自指链接
            if page == "pilates/index.html":
                if 'href="/"' not in vis[0]:
                    add("fail", "%s 面包屑缺 Home 链接" % page)
                if 'href="/pilates/"' in vis[0]:
                    add("warn", "%s 首页面包屑出现自指链接 /pilates/" % page)
            elif "/pilates/" not in vis[0]:
                add("fail", "%s 可见面包屑没有指回 /pilates/" % page)
        else:
            add("warn", "%s 未见可见面包屑（仅 JSON-LD）" % page)

        # ---------- 6. canonical 自指 ----------
        can = re.search(r'<link rel="canonical" href="([^"]+)"', t)
        if not can:
            add("fail", "%s 缺 canonical" % page)
        else:
            slug = page.replace("pilates/", "").replace("index.html", "")
            want = "https://fjsanfan.com/pilates/" + ("" if slug == "" else slug)
            if want.rstrip("/") != can.group(1).rstrip("/"):
                add("fail", "%s canonical 不自指：%s（应为 %s）" % (page, can.group(1), want))

        # ---------- 7. hreflang 只许 en + x-default ----------
        for m in re.finditer(r'<link rel="alternate" hreflang="([^"]+)"', t):
            if m.group(1) not in ("en", "x-default"):
                add("fail", "%s 声明了未建的语言版 hreflang=%s" % (page, m.group(1)))

        # ---------- 8. 图片 alt 与路径 ----------
        for m in re.finditer(r'<img\s+([^>]+)>', t):
            tag = m.group(1)
            src = re.search(r'src="([^"]+)"', tag)
            if not src:
                add("fail", "%s 有 <img> 缺 src" % page)
                continue
            if 'alt="' not in tag:
                add("fail", "%s 图片缺 alt：%s" % (page, src.group(1)))
            kind, target = resolve(page, src.group(1))
            if kind == "file" and not os.path.exists(target):
                add("fail", "%s 图片不存在：%s" % (page, src.group(1)))
            # 图片必须属于本族（或共享素材）
            if kind == "file" and my_fam:
                bn = os.path.basename(target)
                if re.match(r"pilates-[a-z-]+-\d+\.webp$", bn) and not bn.startswith(my_fam["key"] + "-"):
                    add("fail", "%s 用了别族图片：%s（本页应 %s-*）"
                        % (page, bn, my_fam["key"]))

        # ---------- 9. 导流带与页脚互链 ----------
        if '/products/' not in t and '/products.html' not in t:
            add("warn", "%s 没有指回 Products 的互链（导流带）" % page)

        # ---------- 9b. 文档结构：单闭合标签 + 资源只引一次 ----------
        # 曾因为「site_templates.footer() 自带 </body></html> 和 main.js，build 脚本又补一遍」
        # 导致每页两个 </body>、main.js 加载两次 → 第二次执行 const toggle 重复声明报
        # SyntaxError。这类问题静态检查就能拦住，别等浏览器验收。
        for token, want in (("</body>", 1), ("</html>", 1)):
            n = t.count(token)
            if n != want:
                add("fail", "%s %s 出现 %d 次（应 %d 次）" % (page, token, n, want))
        for pat, label in ((r'<script[^>]+src="[^"]*main\.js', "main.js"),
                           (r'<link[^>]+href="[^"]*styles\.css', "styles.css")):
            n = len(re.findall(pat, t))
            if n > 1:
                add("fail", "%s %s 被引入 %d 次（会重复执行/重复请求）" % (page, label, n))
        for m in re.finditer(r'(?:main\.js|styles\.css)\?([^"\']*)', t):
            if not m.group(1).startswith("v"):
                add("fail", "%s 资源版本号缺 v 前缀：?%s（bump 脚本匹配不到会静默跳过）"
                    % (page, m.group(1)))

    # ---------- 10. sitemap 一致性 ----------
    sm = open("sitemap.xml", encoding="utf-8").read()
    locs = re.findall(r"<loc>([^<]+)</loc>", sm)
    dup = [l for l in set(locs) if locs.count(l) > 1]
    if dup:
        add("fail", "sitemap loc 重复：%s" % dup[:5])
    for page in pages:
        url = "https://fjsanfan.com/" + page
        if page == "pilates/index.html":
            url = "https://fjsanfan.com/pilates/"
        if url not in locs:
            add("fail", "sitemap 缺 %s" % url)
    for u in [x for x in locs if "/pilates/" in x]:
        rel = u.replace("https://fjsanfan.com/", "")
        p = os.path.join(ROOT, rel.lstrip("/"))
        if rel.endswith("/") or not os.path.exists(p):
            p = os.path.join(p, "index.html")
        if not os.path.exists(p):
            add("fail", "sitemap 里的 %s 无对应文件" % u)

    # ---------- 11. 全站注入的 /pilates/ 链接是否都有落点 ----------
    nav_hit, nav_bad = 0, []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for x in fn:
            if not x.endswith(".html"):
                continue
            p = os.path.join(dp, x)
            try:
                tt = open(p, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            for m in re.finditer(r'href="(/pilates/(?:pilates-[a-z-]+\.html)?)"', tt):
                nav_hit += 1
                rel = m.group(1).lstrip("/")
                tp = os.path.join(ROOT, rel)
                if rel.endswith("/") or not os.path.exists(tp):
                    tp = os.path.join(tp, "index.html")
                if not os.path.exists(tp):
                    nav_bad.append("%s → %s" % (os.path.relpath(p, ROOT), m.group(1)))
    if nav_bad:
        add("fail", "全站有 %d 处 /pilates/ 链接无落点：%s" % (len(nav_bad), nav_bad[:5]))

    print("=" * 78)
    print("链接有效性与指向正确性审计")
    print("=" * 78)
    print("审计页面 %d | 扫描链接 %d | 全站 /pilates/ 链接 %d 处" % (len(pages), total_links, nav_hit))
    print("sitemap 条目 %d（/pilates/ 相关 %d）" % (len(locs), len([u for u in locs if "pilates" in u])))
    print()
    if fail:
        print("FAIL %d" % len(fail))
        for x in fail[:60]:
            print("  ✗", x)
        if len(fail) > 60:
            print("  ... 另有 %d 条" % (len(fail) - 60))
    else:
        print("FAIL 0 ✓")
    print()
    if warn:
        print("WARN %d" % len(warn))
        for x in warn[:20]:
            print("  !", x)
    else:
        print("WARN 0 ✓")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
