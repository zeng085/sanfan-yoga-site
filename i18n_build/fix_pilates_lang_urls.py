#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修补 pilates 语言页的两类 URL 缺陷（2026-09-15）。

背景
----
批量构建 pilates 语言版时，build_pages.py 有两处历史 bug，导致已落地的
54 个语言页里留下了错误 URL：

① 导航板块入口写成 `/<lang>/pilates/index.html`（带 index.html），
   而 canonical 用目录形式 `/<lang>/pilates/` → 同一页两种 URL。
   根因：批构建启动（16:18:21）与 rewrite_rel 的目录形式修复
   （build_pages.py mtime 16:18:32）差 11 秒，Python 已 import 旧代码。

② 板块首页（index.html）的 canonical / og:url / JSON-LD `url` / JSON-LD
   面包屑 `item` 仍指向**英文地址** `https://fjsanfan.com/pilates/`。
   根因：rewrite_abs() 未把目录形式归一成 index.html 再查 T1_SET。
   族页（pilates-cadillac.html 等）不含尾斜杠，故只有 index 中招。

⚠️ 不能无脑全局替换 `https://fjsanfan.com/pilates/`：
   hreflang="en" 与 x-default 两行**必须**指向英文地址，替换即错。
   所以只在三类容器内替换 —— canonical 标签、og:url 标签、ld+json 块。

幂等：可反复执行，第二次起 0 改动。

用法：python3 i18n_build/fix_pilates_lang_urls.py [--check]
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
SITE = "https://fjsanfan.com"

LD_RE = re.compile(r'(<script[^>]*type="application/ld\+json"[^>]*>)(.*?)(</script>)', re.S)

# 语言码 -> hreflang 用值（与 check_pilates_langs 的 want 列表一致）
LANGS_ORDER = ["de", "ja", "ko", "fr", "it", "es"]


def en_rel(lg, slug):
    """EN 某页在语言 lg 下的路径。板块首页用目录形式（/de/pilates/）。"""
    if slug == "index.html":
        return "/%s/pilates/" % lg
    return "/%s/pilates/%s" % (lg, slug)


def patch_en_hreflang(text, slug):
    """EN 原页补齐 6 语言 hreflang（与语言版的 hreflang="en" 互链对称）。

    背景：9 个 EN 器械页建得比 54 个语言版早，当时语言版不存在，模板只声明
    en + x-default。语言版建成后 head 模板已改为声明 7 语言，但**已落地的 EN
    文件是旧的** → 语言页单向指向 EN、EN 不回指，Google 会报
    「no return tag」（hreflang 非对称），是实打实的 SEO 缺陷。
    这里按模板同一套规则把 6 行补进去，幂等。
    """
    # ⚠️ 只能数 head 里的 <link rel="alternate">；语言切换器里也有
    #    href="..." hreflang="de" 这类属性（属性顺序相反），用裸 hreflang 正则
    #    会把切换器的 6 项当成已声明 → 永远算出 0 补 0（2026-09-15 踩过）。
    have = set(re.findall(r'<link rel="alternate" hreflang="([^"]+)"', text))
    miss = [lg for lg in LANGS_ORDER if lg not in have]
    if not miss:
        return text, 0
    lines = "\n".join('  <link rel="alternate" hreflang="%s" href="%s" />'
                      % (lg, SITE + en_rel(lg, slug)) for lg in miss)
    # 插在 hreflang="en" 那行之后（模板顺序：canonical → en → 6 语言 → x-default）
    m = re.search(r'([ \t]*<link rel="alternate" hreflang="en"[^>]*>\n)', text)
    if not m:
        return text, 0
    return text[:m.end()] + lines + "\n" + text[m.end():], len(miss)


def patch(text, lang):
    """返回 (新文本, 修补计数字典)"""
    n = {"nav": 0, "canonical": 0, "ogurl": 0, "ld": 0}

    # ① 导航 / 内链：/<lang>/pilates/index.html -> /<lang>/pilates/
    old = '"/%s/pilates/index.html"' % lang
    if old in text:
        n["nav"] = text.count(old)
        text = text.replace(old, '"/%s/pilates/"' % lang)

    # ② canonical / og:url：仅改自己的页（英文目录 URL -> 本语言目录 URL）
    def _link(m):
        tag = m.group(0)
        if '%s/pilates/' % lang in tag:
            return tag
        new = tag.replace(SITE + "/pilates/", "%s/%s/pilates/" % (SITE, lang))
        if new != tag:
            n["canonical" if "canonical" in tag else "ogurl"] += 1
        return new

    text = re.sub(r'<link rel="canonical"[^>]*>', _link, text)
    text = re.sub(r'<meta property="og:url"[^>]*>', _link, text)

    # ③ JSON-LD 块内：url / item / @id 等绝对地址
    def _ld(m):
        body = m.group(2)
        target = "%s/%s/pilates/" % (SITE, lang)
        cnt = body.count(SITE + "/pilates/")
        if cnt:
            body = body.replace(SITE + "/pilates/", target)
            n["ld"] += cnt
        return m.group(1) + body + m.group(3)

    text = LD_RE.sub(_ld, text)
    return text, n


def main():
    check = "--check" in sys.argv
    total = {"nav": 0, "canonical": 0, "ogurl": 0, "ld": 0, "files": 0}

    # ---- EN 原页：补齐 6 语言 hreflang ----
    en_d = os.path.join(ROOT, "pilates")
    en_fixed = 0
    if os.path.isdir(en_d):
        for f in sorted(x for x in os.listdir(en_d) if x.endswith(".html")):
            p = os.path.join(en_d, f)
            s = io.open(p, encoding="utf-8").read()
            new, n = patch_en_hreflang(s, f)
            if n and not check:
                io.open(p, "w", encoding="utf-8").write(new)
            en_fixed += n
    print("EN 原页补 hreflang：%d 行%s" % (en_fixed, "  [--check]" if check else ""))

    for lang in LANGS:
        d = os.path.join(ROOT, lang, "pilates")
        if not os.path.isdir(d):
            print("跳过 %-3s（目录不存在）" % lang)
            continue
        files = sorted(f for f in os.listdir(d) if f.endswith(".html"))
        lang_hit = {"nav": 0, "canonical": 0, "ogurl": 0, "ld": 0}
        for f in files:
            p = os.path.join(d, f)
            s = io.open(p, encoding="utf-8").read()
            new, n = patch(s, lang)
            if new != s and not check:
                io.open(p, "w", encoding="utf-8").write(new)
            for k in lang_hit:
                lang_hit[k] += n[k]
            if any(n.values()):
                total["files"] += 1
        for k in lang_hit:
            total[k] += lang_hit[k]
        print("%-3s  %d 页  nav=%-3d canonical=%-2d og:url=%-2d ld+json=%-3d"
              % (lang, len(files), lang_hit["nav"], lang_hit["canonical"],
                 lang_hit["ogurl"], lang_hit["ld"]))
    print("\n合计：改动 %d 个文件  nav=%d  canonical=%d  og:url=%d  ld+json=%d%s"
          % (total["files"], total["nav"], total["canonical"],
             total["ogurl"], total["ld"], "  [--check 未写盘]" if check else ""))


if __name__ == "__main__":
    main()
