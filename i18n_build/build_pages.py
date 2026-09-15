#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SANFAN 多语言静态页生成器 (T1: de/ja/ko)
- 读取现有英文静态页，做文本节点级翻译，产出纯单语静态 HTML
- 保留全部 SEO 结构: canonical / OG / hreflang / JSON-LD
- 移除 data-i18n，杜绝 JS 语言切换覆盖译文
"""
import os, re, json, html as H, posixpath, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import translator as T

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://fjsanfan.com"
# T1 = 德/日/韩（已上线）；T2 = 法/意/西（欧洲瑜伽垫进口大国）
# 注意：LANGS 是全局语言集合，update_seo.py 会据此生成 hreflang 互链与 sitemap，
#       所以新增语言只需加在这里；生成时用命令行参数过滤只跑指定语言：
#       python3 build_pages.py fr it es
LANGS = ["de", "ja", "ko", "fr", "it", "es"]

# ---------------------------------------------------------------- 页面发现
# 2026-09-12 改造：原 PAGES 是硬编码的 T1 试点清单（ym/pr/fr/rb/fi 老命名，
# 还含已下线的 ym8/rb3/rb4/pr2/pr5/fi1），与当前结构（147 产品页 + 10 分类页）
# 严重脱节；新增页面不在清单里会导致 rewrite_rel 不生成语言版链接。改为动态发现。
import glob as _glob


def cat_pages():
    """10 个分类页（位于站点根目录，如 tpe-yoga-mats.html）"""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from category_map import CATS
        return [c["key"] + ".html" for c in CATS]
    except Exception:
        return []


def apps_pages():
    """场景采购页（applications/ 下一层目录）+ 场景总览 applications/index.html。
    这些页是 B2B 采购方的决策路径页（瑜伽馆/酒店/健身房/经销商/贴牌），
    必须与产品页同等对待，否则语言站上的入口会全部回退英文。"""
    return sorted("applications/" + os.path.basename(p)
                  for p in _glob.glob(os.path.join(ROOT, "applications", "*.html")))


def discover_all_pages():
    """站上应有语言版的页面（blog/ 结构不同，单独处理）"""
    prods = sorted("products/" + os.path.basename(p)
                   for p in _glob.glob(os.path.join(ROOT, "products", "*.html")))
    return (["index.html", "about.html", "products.html", "faq.html",
             "contact.html", "blog.html", "materials.html"]
            + cat_pages() + prods + apps_pages() + pilates_pages())


def pilates_pages():
    """普拉提器械板块的 9 页（pilates/ 独立目录，与垫类物理分区）。

    2026-09-15 加入：板块的语言版没建之前不能列进来（hreflang 会指向 404）。
    一旦列入，三个下游同时生效 ——
      ① build_pages 的 T1_SET 会把语言页里的 /pilates/ 链接指到 /<lang>/pilates/；
      ② fix_site.fix_switcher 会给这 9 页 + 54 个语言页注入正确的切换器；
      ③ update_seo 的 hreflang 互链与 sitemap 会带上语言 URL。
    ⚠️ 别把 pilates 和 `meditation-pilates-mats.html` 搞混 —— 后者是垫类分类页，
    属 cat_pages()，一直在 ALL_PAGES 里（历史上的 "pilates in ALL_PAGES" 误判就来自它）。
    """
    return sorted("pilates/" + os.path.basename(p)
                  for p in _glob.glob(os.path.join(ROOT, "pilates", "*.html")))


ALL_PAGES = discover_all_pages()


def translated_set():
    """已存在语言版的页面路径 —— 取 6 语言**交集**，避免链接指向缺失页。
    os.walk 扫描，自动涵盖历史已生成的 21 个产品页与 9 篇 blog。"""
    sets = []
    for lg in LANGS:
        d = os.path.join(ROOT, lg)
        if not os.path.isdir(d):
            continue
        s = set()
        for dp, _, fs in os.walk(d):
            for f in fs:
                if f.endswith(".html"):
                    s.add(os.path.relpath(os.path.join(dp, f), d).replace(os.sep, "/"))
        sets.append(s)
    return set.intersection(*sets) if sets else set()


T1_SET = translated_set()

VOID = {"img", "br", "hr", "input", "meta", "link", "source", "area", "base",
        "col", "embed", "param", "track", "wbr", "path", "circle", "rect"}
TAG_RE = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)((?:\"[^\"]*\"|'[^']*'|[^>\"'])*?)(/?)>", re.S)
ATTR_RE = re.compile(r"([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*(\"[^\"]*\"|'[^']*'|[^>\s]+)")
# 需要翻译的属性
TRANS_ATTRS = {"alt", "placeholder", "title", "aria-label"}
# meta 里需要翻译 content 的键
TRANS_META = {"description", "og:title", "og:description", "twitter:title",
              "twitter:description", "og:site_name"}
# JSON-LD 里需要翻译的字段
LD_KEYS = {"name", "description", "headline", "abstract", "text", "caption",
           "alternateName", "slogan", "disambiguatingDescription"}
LD_SKIP_PARENTS = {"brand", "manufacturer"}

# 2026-09-12：新结构是 10 个独立分类页，products.html 已改成分类导航页，
# 不再有 #yoga / #props 之类的锚点，故下面的回退分支统一指向语言站 products.html。


# ------------------------------------------------------------------ 工具
def rel_from(cur_dir, target):
    c = cur_dir.split("/") if cur_dir else []
    t = target.split("/")
    i = 0
    while i < min(len(c), len(t)) and c[i] == t[i]:
        i += 1
    return "../" * (len(c) - i) + "/".join(t[i:])


def rewrite_rel(u, cur_dir, src_dir, lang):
    """重写相对链接：有语言版则指向语言版；
    无语言版的分类页仍指向当前语言产品列表（带锚点）；
    无语言版的产品详情页回退到当前语言产品列表对应分类。"""
    if not u:
        return u
    s = u.strip()
    if s.startswith(("#", "mailto:", "tel:", "http://", "https://", "//", "data:", "javascript:")):
        return u
    # 保留 #hash / ?query
    m = re.match(r'^([^#?]*)([?#].*)?$', s)
    base = m.group(1) or ''
    suffix = m.group(2) or ''

    # ⭐ 站内绝对路径（/about.html、/pilates/、/blog/x.html）单独处理。
    # 2026-09-15 新增。原实现把 '/about.html' 丢进 posixpath.join(src_dir, base)：
    # join 遇到绝对路径会**丢弃前一段**，A 变成 '/about.html' —— 与 T1_SET 里的
    # 'about.html' 不相等 → 落到 else 保持原样 → 再经 rel_from 拼成
    # '../..//about.html'（双斜杠）。后果有二：语言页上所有绝对链接仍留在英文站
    # （德语页的 About 点进去是英文页），且 URL 畸形。
    # 垫类页面用的是相对路径所以一直没暴露；pilates 板块整体使用绝对路径 → 集中爆发。
    # 这里直接产出绝对语言 URL，不再过 rel_from（避免 "..//"）。
    if base.startswith("/"):
        A = posixpath.normpath(base).lstrip("/")
        if A == ".":
            A = "index.html"
        elif base == "/":
            # ⭐ 站根：必须单独判，否则会一路走到末尾拼成 "//"
            # （2026-09-15 实测：pilates 语言页的 Home 链接全部变成 <a href="//">）
            return "/" + lang + "/" + suffix
        elif base.endswith("/"):
            # 目录形式：有语言版则补 index.html 落页，没有则保留目录形式
            A = (A + "/index.html") if (A + "/index.html") in T1_SET else (A + "/")
        if A in T1_SET:
            # 子目录首页用**目录形式**，与 canonical 一致：
            # /de/pilates/ 而不是 /de/pilates/index.html（同页两种 URL 会把
            # 内链权重拆到两个地址上）。
            if A.endswith("/index.html"):
                return "/" + lang + "/" + A[:-len("index.html")] + suffix
            return "/" + lang + "/" + A + suffix
        if A == "products.html":
            return "/" + lang + "/products.html" + suffix
        if A.startswith("products/") and A.endswith(".html"):
            return "/" + lang + "/products.html" + suffix
        return "/" + A + suffix          # 无语言版：保持绝对，指向英文原页

    A = posixpath.normpath(posixpath.join(src_dir, base)) if src_dir else posixpath.normpath(base)
    if A in ("/", "", "."):
        # 站点根 -> 语言站根（用绝对路径，避免 rel_from 对 "/" 产生 "..//"）
        return "/" + lang + "/" + suffix
    if A in T1_SET:
        target = lang + "/" + A + suffix
    elif A == "products.html":
        # 分类页始终在当前语言站点打开
        target = lang + "/products.html" + suffix
    elif A.startswith("products/") and A.endswith(".html"):
        # 走到这里说明该产品页尚无语言版（有则在上面的 T1_SET 分支命中）→ 回退总览页
        target = lang + "/products.html" + suffix
    else:
        target = A + suffix
    return rel_from(cur_dir, target)


def rewrite_abs(u, lang):
    """重写绝对站点 URL：T1 页加语言前缀

    ⚠️ 2026-09-15 修复：**目录形式**必须归一成 index.html 再去查 T1_SET。
    英文原页的 head 里 canonical/og:url/JSON-LD 的板块首页写的是目录形式
    `https://fjsanfan.com/pilates/`（这正是 EN 端 canonical 的写法），而
    T1_SET 里存的是 `pilates/index.html` → 查表必然落空 → 语言版首页的
    canonical / og:url / JSON-LD url+item 全部退回**英文地址**，
    等于 6 个语言版首页都在向 Google 声明英文页为规范版本（致命）。
    族页 `.../pilates/pilates-cadillac.html` 不含尾斜杠所以一直正常，
    只有板块首页中招 —— 与「只有 index 坏」的现象吻合。
    """
    if not u or not u.startswith(SITE):
        return u
    path = u[len(SITE):].lstrip("/")
    if path == "":
        path = "index.html"          # 根 URL 即首页
    elif path.endswith("/"):
        path = path + "index.html"   # 目录形式 -> 对齐 T1_SET 的 index.html
    if path in T1_SET:
        return norm_lang_url(SITE + "/" + lang + "/" + path)
    return u


def norm_lang_url(u):
    """把 /de/index.html 规范为 /de/（首页语言版用目录形式）

    2026-09-15 放宽：原正则要求 index.html **紧跟在两位语言码之后**，
    所以深一级的 /de/pilates/index.html 匹配不到 → 该页 canonical 写成
    ".../index.html"，而英文原页写的是目录形式 ".../pilates/"，
    同一页两种写法。改为允许语言码之后带任意一层子目录。
    """
    return re.sub(r"(https?://[^/]+/[a-z]{2}(?:/[^/]*)?)/index\.html$", r"\1/", u)


# ------------------------------------------------------------------ 语言块剥离
def strip_lang_zh(h):
    """删除 class 含 lang-zh 的整个元素块"""
    tokens = list(TAG_RE.finditer(h))
    stack, drops = [], []
    for m in tokens:
        close, name, attrs, selfclose = m.group(1), m.group(2).lower(), m.group(3), m.group(4)
        if close:
            for k in range(len(stack) - 1, -1, -1):
                if stack[k][0] == name:
                    top = stack[k]
                    if top[2]:  # zh 块
                        drops.append((top[1], m.end()))
                    del stack[k:]
                    break
        else:
            if name in VOID or selfclose:
                if "lang-zh" in attrs:
                    drops.append((m.start(), m.end()))
                continue
            stack.append((name, m.start(), "lang-zh" in attrs))
    for s, e in sorted(drops, reverse=True):
        h = h[:s] + h[e:]
    return h


def relax_lang_en(h):
    """去掉 lang-en 类包装（内容保留）"""
    def _fix(m):
        if "lang-en" not in m.group(0):
            return m.group(0)
        cls = re.search(r'class\s*=\s*("([^"]*)"|\'([^\']*)\'|([^\s>]+))', m.group(0))
        if not cls:
            return m.group(0)
        val = cls.group(2) or cls.group(3) or cls.group(4) or ""
        parts = [p for p in val.split() if p != "lang-en"]
        if not parts:
            return m.group(0).replace(cls.group(0), "")
        return m.group(0).replace(cls.group(0), 'class="%s"' % " ".join(parts))
    return TAG_RE.sub(_fix, h)


def remove_i18n_attrs(h):
    h = re.sub(r'\s+data-i18n(?:-ph)?="[^"]*"', "", h)
    return h


def drop_div_by_class(h, class_name):
    """整块删除 class 含 class_name 的 div —— 按 token 配对，正确处理嵌套。"""
    depth, start = 0, None
    for m in TAG_RE.finditer(h):
        close, name, attrs, selfclose = m.group(1), m.group(2).lower(), m.group(3), m.group(4)
        if name != "div":
            continue
        if not close:
            if selfclose:
                if start is None and class_name in attrs:      # 自闭合（罕见）
                    return h[:m.start()] + h[m.end():]
                continue
            if start is None:
                if class_name in attrs:
                    start = m.start()
                    depth = 1
            else:
                depth += 1
        else:
            if start is not None:
                depth -= 1
                if depth == 0:
                    # 连同前导空白一起删
                    s = start
                    while s > 0 and h[s - 1] in " \t\n":
                        s -= 1
                    return h[:s] + h[m.end():]
    return h      # 找不到配对则原样返回（保守）


# ------------------------------------------------------------------ 主流程
def collect_texts(h):
    """返回 (占位化后的html, 文本列表, ld占位映射)"""
    ph = {}

    def stash(m):
        k = "\x00P%d\x00" % len(ph)
        ph[k] = m.group(0)
        return k

    # 1) JSON-LD 单独抽出
    lds = []

    def stash_ld(m):
        try:
            obj = json.loads(m.group(1))
        except Exception:
            return stash(m)
        k = "\x00L%d\x00" % len(lds)
        lds.append((k, obj))
        return k

    h = re.sub(r'<script\s+type="application/ld\+json"[^>]*>(.*?)</script>',
               stash_ld, h, flags=re.S | re.I)
    # 2) 其余 script/style/注释
    h = re.sub(r"<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>|<!--.*?-->",
               stash, h, flags=re.S | re.I)

    # 3) 文本节点
    parts = TAG_RE.split(h)
    # split 后: [text, close, name, attrs, selfclose, text, ...] 奇偶复杂 -> 改用占位再切
    segs = re.split(r'(<[^>]+>)', h)
    texts = []
    for i, s in enumerate(segs):
        if i % 2 == 1:      # 标签
            continue
        if "\x00" in s:     # 含占位符片段里的非占位文本，仍可翻译但保守跳过
            continue
        raw = s
        body = raw.strip()
        if not body:
            continue
        if not re.search(r"[0-9A-Za-z\u00c0-\u024f]", H.unescape(body)):
            continue
        texts.append((i, raw))
    return h, segs, texts, ph, lds


def translate_ld(obj, lang, parent=None, cache_map=None):
    """递归翻译 JSON-LD 字符串字段，并把 url/@id/item 切到语言版路径"""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if isinstance(v, str) and k in ("url", "@id", "item"):
                out[k] = rewrite_abs(v, lang)
            elif isinstance(v, str) and k in LD_KEYS and parent not in LD_SKIP_PARENTS:
                out[k] = cache_map.setdefault(v, T.translate_one(v, lang))
            elif isinstance(v, (dict, list)):
                out[k] = translate_ld(v, lang, k, cache_map)
            else:
                out[k] = v
        return out
    if isinstance(obj, list):
        return [translate_ld(x, lang, parent, cache_map) for x in obj]
    return obj


def build_one(rel_path, lang, verbose=True):
    src_path = os.path.join(ROOT, rel_path)
    h = open(src_path, encoding="utf-8").read()

    # 1) 结构处理
    h = strip_lang_zh(h)
    h = relax_lang_en(h)
    h = remove_i18n_attrs(h)

    # 2) 抽出 script/JSON-LD，收集文本
    h, segs, texts, ph, lds = collect_texts(h)

    # 3) 批量翻译文本节点（保留首尾空白）
    plain = [H.unescape(t[1].strip()) for t in texts]
    if verbose:
        print("[%s/%s] 文本节点 %d 条" % (lang, rel_path, len(plain)), flush=True)
    trans = T.translate_lines(plain, lang, verbose=False)

    for (idx, raw), new in zip(texts, trans):
        lead = raw[:len(raw) - len(raw.lstrip())]
        tail = raw[len(raw.rstrip()):]
        segs[idx] = lead + H.escape(new, quote=False) + tail
    h = "".join(segs)

    # 4) 翻译标签属性 (alt/placeholder/title/aria-label)
    tag_pairs = []

    def _collect_tag(m):
        for am in ATTR_RE.finditer(m.group(0)):
            k, v = am.group(1).lower(), am.group(2)
            if k in TRANS_ATTRS and len(v) > 2:
                raw = v[1:-1] if v[0] in "\"'" else v
                if re.search(r"[A-Za-z]", H.unescape(raw)):
                    tag_pairs.append(H.unescape(raw))
        return m.group(0)

    TAG_RE.sub(_collect_tag, h)
    if tag_pairs:
        uniq = list(dict.fromkeys(tag_pairs))
        tr = dict(zip(uniq, T.translate_lines(uniq, lang)))

        def _apply_tag(m):
            tag = m.group(0)

            def _ra(am):
                k, v = am.group(1).lower(), am.group(2)
                if k not in TRANS_ATTRS or len(v) <= 2:
                    return am.group(0)
                q = v[0] if v[0] in "\"'" else ""
                raw = v[1:-1] if q else v
                dec = H.unescape(raw)
                if dec in tr:
                    # ⚠️ 必须 quote=True：译文里的裸 " 若不转义，写回双引号属性会
                    # 提前闭合属性值 → 畸形标签 → 属性重写器跳过该标签剩余属性
                    # （实测：de/fr/it/es 的 alt="…(10")" 导致图片 src 少一层 ../ 而 404）
                    nv = H.escape(tr[dec], quote=True)
                    return '%s=%s%s%s' % (am.group(1), q, nv, q)
                return am.group(0)

            return ATTR_RE.sub(_ra, tag)

        h = TAG_RE.sub(_apply_tag, h)

    # 5) 翻译 meta title / description / og:*
    def _meta(m):
        tag = m.group(0)
        nm = re.search(r'(?:name|property)\s*=\s*"?([^"\'\s>]+)"?', tag)
        key = nm.group(1) if nm else ""
        if key not in TRANS_META:
            return tag
        cm = re.search(r'content\s*=\s*"([^"]*)"', tag)
        if not cm:
            return tag
        val = H.unescape(cm.group(1))
        if not re.search(r"[A-Za-z]", val):
            return tag
        # 同属性转义问题：meta content 也是双引号属性，译文里的 " 必须转义
        nv = H.escape(T.translate_one(val, lang), quote=True)
        return tag.replace(cm.group(0), 'content="%s"' % nv)

    h = re.sub(r"<meta\b[^>]*>", _meta, h, flags=re.I)

    def _title(m):
        val = H.unescape(m.group(1))
        return "<title>%s</title>" % H.escape(T.translate_one(val, lang), quote=False)

    h = re.sub(r"<title>(.*?)</title>", _title, h, flags=re.S)

    # 6) 路径重写
    src_dir = posixpath.dirname(rel_path)
    cur_dir = lang + ("/" + src_dir if src_dir else "")
    out_rel = lang + "/" + rel_path

    def _rewrite_attrs(m):
        tag = m.group(0)

        def _ra(am):
            k, v = am.group(1).lower(), am.group(2)
            if k in ("href", "src", "action"):
                q = v[0] if v[0] in "\"'" else ""
                raw = v[1:-1] if q else v
                if raw.startswith("https://fjsanfan.com"):
                    nv = rewrite_abs(raw, lang)
                elif raw.startswith(("http", "//", "#", "mailto:", "tel:", "data:")):
                    nv = raw
                else:
                    nv = rewrite_rel(raw, cur_dir, src_dir, lang)
                return '%s=%s%s%s' % (am.group(1), q, nv, q)
            if k == "content" and "http" in v.lower():
                return am.group(0)
            return am.group(0)

        return ATTR_RE.sub(_ra, tag)

    h = TAG_RE.sub(_rewrite_attrs, h)

    # og:url 等 meta 内绝对 URL 加语言前缀
    def _meta_url_fix(m):
        tag = m.group(0)
        if "og:url" not in tag:
            return tag

        def _ra(am):
            if am.group(1).lower() != "content":
                return am.group(0)
            v = am.group(2)
            q = v[0] if v[0] in "\"'" else ""
            raw = v[1:-1] if q else v
            if raw.startswith(SITE):
                return "content=%s%s%s" % (q, rewrite_abs(raw, lang), q)
            return am.group(0)

        return ATTR_RE.sub(_ra, tag)

    h = re.sub(r"<meta\b[^>]*>", _meta_url_fix, h, flags=re.I)

    # canonical / og:url / hreflang 绝对 URL 加语言前缀
    def _abs_fix(m):
        tag = m.group(0)
        def _ra(am):
            v = am.group(2)
            q = v[0] if v[0] in "\"'" else ""
            raw = v[1:-1] if q else v
            if raw.startswith(SITE):
                return '%s=%s%s%s' % (am.group(1), q, rewrite_abs(raw, lang), q)
            return am.group(0)
        if 'rel="canonical"' in tag or 'og:url' in tag or 'hreflang' in tag:
            return ATTR_RE.sub(_ra, tag)
        return tag
    h = re.sub(r"<link\b[^>]*>", _abs_fix, h, flags=re.I)

    # 7) hreflang 集合：en/de/ja/ko + x-default 互链
    #    注意：不要声明 hreflang="zh"——站点没有独立 /zh/ 目录，
    #    把英文 URL 同时声明成 en 和 zh 是冲突信号。中文走页面内切换器，不是独立语言版本。
    def _u(lg):
        if lg is None:      # en / x-default -> 英文原页
            if rel_path == "index.html":
                return SITE + "/"
            if rel_path.endswith("/index.html"):
                # 子目录首页用目录形式（pilates/index.html -> /pilates/），
                # 否则英文原页与语言版会是两种写法（/pilates/ vs /de/pilates/）。
                return SITE + "/" + rel_path[:-len("index.html")]
            return SITE + "/" + rel_path
        return norm_lang_url(SITE + "/" + lg + "/" + rel_path)

    variants = [("en", _u(None))] + [(lg, _u(lg)) for lg in LANGS] + \
               [("x-default", _u(None))]
    hl_lines = "\n".join('  <link rel="alternate" hreflang="%s" href="%s" />' % (l, u)
                         for l, u in variants)
    h = re.sub(r'\s*<link rel="alternate" hreflang="[^"]*" href="[^"]*"\s*/?>', "", h)
    h = re.sub(r'(<link rel="canonical"[^>]*>)',
               r'\1\n' + hl_lines, h, count=1)

    # 8) html lang + 语言切换器
    h = re.sub(r'<html\s+lang="[^"]*"', '<html lang="%s"' % lang, h, count=1)
    h = re.sub(r'<html(?![^>]*lang=)', '<html lang="%s"' % lang, h, count=1)

    # 8.5) 修正 <script src> 的相对路径 —— 实际修正见文末第 10.5 步。
    # ⚠️ 不能写在这里：collect_texts 已把 <script>整块 stash 成占位符，
    #    此处 h 里只剩 \x00P…\x00，下面的正则永远匹配不到。
    #    （历史遗留失效点，2026-09-12 定位。原注释声称修过，实际从未生效。）

    # 切换器不在这里生成：由 fix_site.py 用「绝对路径」统一注入（幂等，覆盖英文原页+全部语言页）。
    # 原因：这里用相对路径容易算错层级（曾出现 ..// 这类错误），且旧 lang-btn 正则早已失效。
    # 翻译会把旧切换器的 "EN"/"DE" 等标签也翻掉，所以先整块摘掉，避免残留被译文污染的切换器。
    # ⚠️ 2026-09-13：旧写法 `.*?</div>` 只删到第一个 </div> —— 而 lang-switch 内嵌
    # lang-menu div，外层 </div> 成为孤儿闭合（每页多一个 </div>，de/index 等历史页同样中招）。
    # 改为按标签 token 配对的整块删除（正确处理嵌套）。
    h = drop_div_by_class(h, "lang-switch")
    h = re.sub(r'\s*<button class="lang-btn"[^>]*>.*?</button>', '', h, count=1, flags=re.S)

    # 9) 回填 JSON-LD（翻译内部字符串）
    ld_cache = {}
    for k, obj in lds:
        try:
            nobj = translate_ld(obj, lang, None, ld_cache)
            body = json.dumps(nobj, ensure_ascii=False, indent=2)
        except Exception:
            body = json.dumps(obj, ensure_ascii=False)
        h = h.replace(k, '<script type="application/ld+json">\n%s\n</script>' % body)

    # 10) 回填其余占位
    for k, v in ph.items():
        h = h.replace(k, v)

    # 10.5) 修正 <script src> 相对路径（必须在占位符回填**之后**执行）。
    # 语言页比英文原页深一级目录（de/ 或 de/products/），相对路径要相应加深，
    # 否则会指向 de/assets/js/main.js —— 该目录不存在 → main.js 404 →
    # 移动端菜单、语言切换器、FAQ 折叠全部失效（全站交互都依赖它）。
    h = re.sub(r'(<script[^>]*\ssrc=")((?:\.\./)*assets/[^"]+)(")',
               lambda m: m.group(1) + '../' + m.group(2) + m.group(3), h)

    # 11) 落地
    out_path = os.path.join(ROOT, out_rel)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    open(out_path, "w", encoding="utf-8").write(h)
    if verbose:
        print("   -> %s (%d bytes)" % (out_rel, len(h)), flush=True)
    return out_rel


USAGE = """
用法:
  python3 build_pages.py                            全部 ALL_PAGES × 全部语言（量大，慎用）
  python3 build_pages.py de ja                      只跑指定语言
  python3 build_pages.py de --batch batch.json      只跑清单里的页面
  python3 build_pages.py --dry --batch batch.json   只估算额度，不调 API
批次清单 JSON: {"pages": ["products/ab-wheel.html", ...]}
"""


if __name__ == "__main__":
    args = sys.argv[1:]
    only, batch_file, dry = [], None, False
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--batch" and i + 1 < len(args):
            batch_file, i = args[i + 1], i + 2
        elif a == "--dry":
            dry, i = True, i + 1
        elif a in ("-h", "--help"):
            print(USAGE)
            sys.exit(0)
        else:
            only.append(a)
            i += 1

    langs = [l for l in LANGS if (not only or l in only)]
    pages = json.load(open(batch_file, encoding="utf-8"))["pages"] if batch_file else list(ALL_PAGES)

    # 本批页面视为「将有语言版」→ 链接直接指向语言版，避免生成完链接又指回英文
    T1_SET.update(pages)

    if dry:
        print("页面 %d 个 × 语言 %s\n" % (len(pages), ",".join(langs)))
        total = 0
        for lang in langs:
            chars = miss = hit = 0
            for p in pages:
                h = open(os.path.join(ROOT, p), encoding="utf-8").read()
                h = remove_i18n_attrs(relax_lang_en(strip_lang_zh(h)))
                _, _, texts, _, _ = collect_texts(h)
                for _, raw in texts:
                    s = H.unescape(raw.strip())
                    if not s:
                        continue
                    if T._ck(s, lang) in T._cache:
                        hit += 1
                    else:
                        miss += 1
                        chars += len(s)
            print("  %-3s 新增约 %8d 字符  (%d 条待译 / %d 条命中缓存)" % (lang, chars, miss, hit))
            total += chars
        u = T.usage()
        print("\n  合计约 %d 字符（下限：未含 alt/meta/JSON-LD 文本）" % total)
        if "character_count" in u:
            used, lim = u["character_count"], u["character_limit"]
            left = lim - used
            print("  额度 已用 %s / %s，剩余 %s" % (f"{used:,}", f"{lim:,}", f"{left:,}"))
            print("  %s" % ("✅ 在剩余额度内" if total <= left else
                            "⚠️ 超出 %s 字符 —— 需缩量或分批" % f"{total - left:,}"))
        else:
            print("  额度查询失败:", u)
        sys.exit(0)

    print("开始：%d 页 × %d 语言 = %d 个页面\n" % (len(pages), len(langs), len(pages) * len(langs)))
    ok = fail = 0
    for lang in langs:
        for p in pages:
            t0 = time.time()
            try:
                build_one(p, lang)
                ok += 1
                print("     [%.1fs]" % (time.time() - t0), flush=True)
            except SystemExit:
                T.flush()
                print("中断：配额问题，已缓存进度")
                sys.exit(1)
            except Exception as e:
                fail += 1
                print("  !! %s %s -> %s" % (lang, p, e))
    T.flush()
    print("DONE  ok=%d fail=%d  用量=%s" % (ok, fail, T.stats()))
