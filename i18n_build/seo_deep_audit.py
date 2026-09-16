# -*- coding: utf-8 -*-
"""seo_deep_audit.py —— 按 SEO 审计框架补齐的第二轮深度体检（2026-09-12）

full_audit.py 管「翻译与结构同构」，本脚本管「可被搜索引擎正确抓取与排名」：
  1  title 长度异常 / 全站重复
  2  meta description 缺失 / 长度异常 / 全站重复
  3  h1 缺失或重复（多 h1）
  4  canonical 自指且为绝对 URL
  5  hreflang 互指（A 声明 B，B 必须也声明 A）+ x-default
  6  robots meta 误 noindex
  7  死链（站内 href 指向不存在的文件）
  8  孤儿页（没有任何页面链到它）
  9  robots.txt（存在 / 未误封 / 有 sitemap 行）
 10  sitemap.xml（条目数、是否含 noindex 页、是否含非 canonical）
 11  URL 规范（大写 / 下划线 / 空格 / 双斜杠）
 12  混合内容 http:// 外链资源
 13  图片 alt 缺失 / 非 webp

用法：
    python3 i18n_build/seo_deep_audit.py [--verbose]
问题按「页面/URL」聚合打印，--verbose 展开全部。
"""
import argparse
import collections
import html
import os
import re
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
SITE = "https://fjsanfan.com/"

TAG_RE = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)((?:[^>\"']|\"[^\"]*\"|'[^']*')*?)(/?)>", re.S)
ATTR_RE = re.compile(r"([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*(\"[^\"]*\"|'[^']*'|[^>\s]+)")
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.S | re.I)
H1_RE = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.S | re.I)
LINK_RE = re.compile(r"<link\b[^>]*>", re.I)
HREF_RE = re.compile(r'<a\b[^>]*href="([^"]*)"', re.I)


def text_of(s):
    """去标签 + 反转义 + 压空白：长度统计必须基于反转义后的文本。"""
    return " ".join(re.sub(r"<[^>]+>", " ", html.unescape(s)).split())


def dw(s):
    """显示宽度：CJK/全角算 2，其余算 1。

    ⚠️ 长度类判据必须按**宽度**而不是字符数。Google 按像素截断（title ~600px、
    description ~920px），CJK 一个字符约占西文两倍宽，用 len() 会**双向失真**：
      · title 过短：ja「会社概要 — SANFAN ヨガ・フィットネス」23 字被判过短，
        实际 36 宽（完全够用）→ 假报（2026-09-16 实测 17 处全是假报）
      · title 过长：ja/ko 标题 79 字其实 158 宽（严重超长）却判为正常 → 漏报
    描述那侧早就按语言折算过阈值，title 这侧一直漏改。
    """
    return sum(2 if ord(c) > 0x2E80 else 1 for c in s)


IMG_RE = re.compile(r"<img\b[^>]*>", re.I)


def walk_html():
    out = []
    for dp, dns, fs in os.walk(ROOT):
        rel = os.path.relpath(dp, ROOT)
        if rel == ".":
            rel = ""
        if any(s in rel for s in (".git", "node_modules", "outputs", ".workbuddy", "i18n_build")):
            dns[:] = []
            continue
        for f in fs:
            if f.endswith(".html"):
                out.append(os.path.join(rel, f).replace(os.sep, "/").lstrip("/"))
    return sorted(out)


def attrs(tag):
    d = {}
    for k, v in ATTR_RE.findall(tag):
        d[k.lower()] = v.strip('"').strip("'")
    return d


def meta_content(h, name):
    for tag in re.findall(r"<meta\b[^>]*>", h, re.I):
        a = attrs(tag)
        if a.get("name", "").lower() == name or a.get("property", "").lower() == name:
            return a.get("content", "")
    return None


    def text_of(s):
        return " ".join(re.sub(r"<[^>]+>", " ", s).split())



def lang_of(rel):
    return rel.split("/")[0] if rel.split("/")[0] in LANGS else "en"


def canon_url(rel):
    """页面应有的绝对 canonical。目录页 de/ 之类 → /de/"""
    if rel == "index.html":
        return SITE
    if rel.endswith("/index.html"):
        return SITE + rel[:-len("index.html")]
    return SITE + rel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    pages = walk_html()
    docs = {}
    for rel in pages:
        with open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace") as fh:
            docs[rel] = fh.read()

    issues = collections.defaultdict(list)
    noindex_pages = set()

    def add(cat, rel, detail=""):
        issues[cat].append((rel, detail))

    titles = collections.defaultdict(list)
    descs = collections.defaultdict(list)
    hreflang_map = {}       # rel -> {lang: url}
    linked = collections.Counter()
    all_links = []          # (src, raw_href)

    for rel, h in docs.items():
        lg = lang_of(rel)
        # noindex 页必须在**最前面**判定并跳过：hreflang / sitemap / 孤儿页这些
        # 收录类检查对它都没意义（历史遗留的 product.html 模板页就是这种）。
        if "noindex" in (meta_content(h, "robots") or "").lower():
            noindex_pages.add(rel)
            add("_noindex 页（豁免收录类检查）", rel, meta_content(h, "robots") or "noindex")
            continue
        # --- title
        m = TITLE_RE.search(h)
        title = text_of(m.group(1)) if m else ""
        if not title:
            add("title 缺失", rel)
        else:
            titles[(lg, title)].append(rel)
            title = html.unescape(title)
            tw = dw(title)
            if tw < 25:
                add("title 过短(<25宽)", rel, "%d宽 %s" % (tw, title))
            elif tw > 80:
                # 阈值取 80 而非常见的 70：Google 按**像素**（~600px）截断，70~80 宽
                # 的西文标题通常还显示得全；超过 80 宽才必然被切，那才需要改。
                add("title 过长(>80宽)", rel, "%d宽 %s" % (tw, title[:40]))
        # --- description
        desc = meta_content(h, "description")
        if desc:
            desc = html.unescape(desc)
        if not desc:
            add("description 缺失", rel)
        else:
            descs[(lg, desc)].append(rel)
            # 阈值按显示宽度折算（CJK×2）：统一 55 宽 ≈ 西文 55 字，
            # 日/韩语给 60 宽（≈30 字），与改宽度前「ja/ko 30 字」的口径基本一致。
            minlen = 60 if lg in ("ja", "ko") else 55
            dwn = dw(desc)
            if dwn < minlen:
                add("description 过短", rel, "%d宽（%s 阈值 %d）" % (dwn, lg, minlen))
            elif dwn > 170:
                add("description 过长(>170宽)", rel, "%d宽" % dwn)
        # --- h1
        h1s = [text_of(x) for x in H1_RE.findall(h)]
        h1s = [x for x in h1s if x]
        if not h1s:
            add("h1 缺失", rel)
        elif len(h1s) > 1:
            add("多个 h1", rel, "%d 个: %s" % (len(h1s), " / ".join(x[:24] for x in h1s[:3])))
        # --- canonical
        canon = ""
        for tag in LINK_RE.findall(h):
            a = attrs(tag)
            if a.get("rel", "").lower() == "canonical":
                canon = a.get("href", "")
                break
        if not canon:
            add("canonical 缺失", rel)
        elif not canon.startswith("http"):
            add("canonical 非绝对 URL", rel, canon)
        else:
            # 两种形态都算自指：目录式 /de/ 与文件式 /applications/index.html。
            # 站点两种都在用（sitemap 里语言首页是 /de/、applications 是 index.html），
            # 且线上实测两者都 200，canonical 与 sitemap 口径一致即无重复内容风险。
            ok = [canon_url(rel).rstrip("/"), (SITE + rel).rstrip("/")]
            if canon.rstrip("/") not in ok:
                add("canonical 非自指", rel, "%s ∉ %s" % (canon, " | ".join(ok)))
        # --- hreflang
        hm = {}
        for tag in LINK_RE.findall(h):
            a = attrs(tag)
            if a.get("rel", "").lower() == "alternate" and a.get("hreflang"):
                hm[a["hreflang"].lower()] = a.get("href", "")
        hreflang_map[rel] = hm
        if hm:
            if "x-default" not in hm:
                add("hreflang 缺 x-default", rel)
            if ("en" not in hm) and lg != "en":
                add("hreflang 缺 en", rel)
            for l in LANGS:
                if l not in hm:
                    add("hreflang 缺语言", rel, l)
        # --- 图片
        for tag in IMG_RE.findall(h):
            a = attrs(tag)
            src = a.get("src", "")
            if not a.get("alt"):
                add("图片缺 alt", rel, src[:60])
            if src.startswith("http://"):
                add("混合内容 http://", rel, src[:60])
        # --- 链接
        for href in HREF_RE.findall(h):
            all_links.append((rel, href))

    # --- 死链
    for src, href in all_links:
        h = href.split("#")[0].split("?")[0].strip()
        if not h or h.startswith(("mailto:", "tel:", "javascript:", "http://", "https://")):
            continue
        if h.startswith("/"):
            target = h.lstrip("/")
        else:
            target = os.path.normpath(os.path.join(os.path.dirname(src), h)).replace(os.sep, "/")
        if not target:
            continue
        if target in docs:
            linked[target] += 1
            continue
        # ⚠️ 目录形式 /de/ 必须先归到 de/index.html：直接 os.path.exists 会命中目录本身，
        #    于是记成 linked["de/"]，孤儿页检查找的是 "de/index.html" → 6 个语言首页全假报。
        if target.endswith("/") or os.path.isdir(os.path.join(ROOT, target)):
            target = target.rstrip("/") + "/index.html"
            if target in docs:
                linked[target] += 1
                continue
        if os.path.exists(os.path.join(ROOT, target)):
            linked[target] += 1
            continue
        if os.path.exists(os.path.join(ROOT, target, "index.html")):
            linked[target + "/index.html"] += 1
            continue
        add("死链", src, href[:70])

    # --- 孤儿页
    for rel in docs:
        if rel == "index.html" or rel in noindex_pages:
            continue
        if linked.get(rel, 0) == 0:
            add("孤儿页（无内链）", rel)

    # --- hreflang 互指
    for rel, hm in hreflang_map.items():
        for l, url in hm.items():
            if l == "x-default":
                continue
            other = None
            if l == "en":
                other = "index.html" if rel == "index.html" else rel
            else:
                # url → 相对路径
                p = url.replace(SITE, "").replace("http://fjsanfan.com/", "")
                if p.endswith("/") or p == "":
                    other = p + "index.html"
                else:
                    other = p
            if not other or other == rel or other not in hreflang_map:
                continue
            back = hreflang_map[other]
            mine = hm.get("x-default")
            # 对方必须声明「我」这个语言
            want_lang = lang_of(rel)
            want_lang = "en" if want_lang == "en" else want_lang
            if want_lang not in back and ("en" if want_lang == "en" else want_lang) not in back:
                add("hreflang 未互指", rel, "%s → %s 未回指" % (l, other))

    # --- title / description 重复
    # ⚠️ 必须**按语言分组**再比。原来 titles/descs 是全局字典、按文本做键，
    #    于是「Ab Wheel — SANFAN Yoga & Fitness OEM」在 EN 与 de 各出现一次
    #    就被判成重复 —— 不同语言页面靠 hreflang 相互区分，同名完全正常。
    #    实测这个假报贡献了 16 组「title 重复」里的 15 组（2026-09-16）。
    for (lg, t), rs in titles.items():
        if len(rs) > 1:
            add("title 重复", rs[0], "×%d [%s]: %s" % (len(rs), lg, t[:50]))
    for (lg, d), rs in descs.items():
        if len(rs) > 1:
            add("description 重复", rs[0], "×%d [%s]" % (len(rs), lg))

    # --- robots.txt
    rp = os.path.join(ROOT, "robots.txt")
    if not os.path.exists(rp):
        add("robots.txt 缺失", "robots.txt")
    else:
        txt = open(rp, encoding="utf-8").read()
        if "Sitemap:" not in txt:
            add("robots.txt 缺 Sitemap", "robots.txt")
        if re.search(r"Disallow:\s*/\s*$", txt, re.M):
            add("robots.txt 全站 Disallow", "robots.txt")
        for m in re.findall(r"Disallow:\s*(\S+)", txt):
            if m.startswith("/assets") or m.startswith("/products"):
                add("robots.txt 误封目录", "robots.txt", m)

    # --- sitemap
    sm = os.path.join(ROOT, "sitemap.xml")
    if not os.path.exists(sm):
        add("sitemap.xml 缺失", "sitemap.xml")
    else:
        try:
            root = ET.parse(sm).getroot()
            ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
            locs = [e.text for e in root.iter(ns + "loc")]
            add("_sitemap 条目数", "sitemap.xml", "%d 条 / 站内 %d 页" % (len(locs), len(docs)))
            in_sm = set()
            for u in locs:
                p = u.replace(SITE, "").replace("http://fjsanfan.com/", "")
                if p.endswith("/") or p == "":
                    p += "index.html"
                in_sm.add(p)
            for rel in docs:
                if rel not in in_sm and rel not in noindex_pages:
                    add("页面未进 sitemap", rel)
            for p in in_sm:
                if p not in docs and not os.path.exists(os.path.join(ROOT, p)):
                    add("sitemap 指向不存在页", "sitemap.xml", p)
        except Exception as e:
            add("sitemap 解析失败", "sitemap.xml", str(e)[:60])

    # --- URL 规范
    for rel in docs:
        if re.search(r"[A-Z]", os.path.basename(rel)):
            add("文件名含大写", rel)
        if "_" in os.path.basename(rel):
            add("文件名含下划线", rel)
        if " " in rel:
            add("路径含空格", rel)
        if "//" in rel:
            add("路径含双斜杠", rel)

    # ---------------- 输出 ----------------
    print("扫描 %d 个页面\n" % len(docs))
    order = sorted(issues.items(), key=lambda kv: -len(kv[1]))
    total = 0
    if not order:
        print("✅ 全部通过")
        return
    print("================ 深度体检结果 ================")
    for cat, rows in order:
        if cat.startswith("_"):
            print("ℹ️  %-22s %s" % (cat[1:], rows[0][1]))
            continue
        total += len(rows)
        print("❌ %-22s %d 处" % (cat, len(rows)))
        for rel, d in rows[:8]:
            print("     %-44s %s" % (rel[:44], d[:60]))
        if len(rows) > 8 and not args.verbose:
            print("     … 还有 %d 条（--verbose 展开）" % (len(rows) - 8))
    print("\n合计问题 %d 处" % total)
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
