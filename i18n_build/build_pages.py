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
LANGS = ["de", "ja", "ko"]

# T1 试点页面清单（相对站点根）
PAGES = [
    "index.html",
    "about.html",
    "products.html",
    "faq.html",
    "contact.html",
    "products/ym1.html",
    "products/ym2.html",
    "products/ym3.html",
    "products/fr1.html",
    "products/rb2.html",
]
T1_SET = set(PAGES)

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


# ------------------------------------------------------------------ 工具
def rel_from(cur_dir, target):
    c = cur_dir.split("/") if cur_dir else []
    t = target.split("/")
    i = 0
    while i < min(len(c), len(t)) and c[i] == t[i]:
        i += 1
    return "../" * (len(c) - i) + "/".join(t[i:])


def rewrite_rel(u, cur_dir, src_dir, lang):
    """重写相对链接：有语言版则指向语言版，否则回英文原页"""
    if not u:
        return u
    s = u.strip()
    if s.startswith(("#", "mailto:", "tel:", "http://", "https://", "//", "data:", "javascript:")):
        return u
    A = posixpath.normpath(posixpath.join(src_dir, s)) if src_dir else posixpath.normpath(s)
    target = (lang + "/" + A) if A in T1_SET else A
    return rel_from(cur_dir, target)


def rewrite_abs(u, lang):
    """重写绝对站点 URL：T1 页加语言前缀"""
    if not u or not u.startswith(SITE):
        return u
    path = u[len(SITE):].lstrip("/")
    if path == "":
        path = "index.html"          # 根 URL 即首页
    if path in T1_SET:
        return norm_lang_url(SITE + "/" + lang + "/" + path)
    return u


def norm_lang_url(u):
    """把 /de/index.html 规范为 /de/（首页语言版用目录形式）"""
    return re.sub(r"(https?://[^/]+/[a-z]{2})/index\.html$", r"\1/", u)


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
                    nv = H.escape(tr[dec], quote=False)
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
        nv = H.escape(T.translate_one(val, lang), quote=False)
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
            return SITE + "/" if rel_path == "index.html" else SITE + "/" + rel_path
        return norm_lang_url(SITE + "/" + lg + "/" + rel_path)

    variants = [("en", _u(None)),
                ("de", _u("de")), ("ja", _u("ja")), ("ko", _u("ko")),
                ("x-default", _u(None))]
    hl_lines = "\n".join('  <link rel="alternate" hreflang="%s" href="%s" />' % (l, u)
                         for l, u in variants)
    h = re.sub(r'\s*<link rel="alternate" hreflang="[^"]*" href="[^"]*"\s*/?>', "", h)
    h = re.sub(r'(<link rel="canonical"[^>]*>)',
               r'\1\n' + hl_lines, h, count=1)

    # 8) html lang + 语言切换器
    h = re.sub(r'<html\s+lang="[^"]*"', '<html lang="%s"' % lang, h, count=1)
    h = re.sub(r'<html(?![^>]*lang=)', '<html lang="%s"' % lang, h, count=1)

    def lang_url(lg):
        """lg=None -> 英文/中文原页；否则 -> /<lg>/<rel_path>"""
        target = rel_path if lg is None else (lg + "/" + rel_path)
        return rel_from(cur_dir, target)

    LBL = {"de": "DE", "ja": "JA", "ko": "KO"}
    links = ['<a href="%s" hreflang="en"%s>EN</a>' % (lang_url(None), ""),
             '<a href="%s" hreflang="zh" data-setlang="zh">中文</a>' % lang_url(None)]
    for lg in ("de", "ja", "ko"):
        act = ' class="active"' if lg == lang else ""
        links.append('<a href="%s" hreflang="%s"%s>%s</a>' % (lang_url(lg), lg, act, LBL[lg]))
    switch = '<div class="lang-switch">' + "".join(links) + '</div>'
    h = re.sub(r'<button class="lang-btn"[^>]*>.*?</button>', switch, h, count=1, flags=re.S)

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

    # 11) 落地
    out_path = os.path.join(ROOT, out_rel)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    open(out_path, "w", encoding="utf-8").write(h)
    if verbose:
        print("   -> %s (%d bytes)" % (out_rel, len(h)), flush=True)
    return out_rel


if __name__ == "__main__":
    only = sys.argv[1:] or None
    langs = [l for l in LANGS if (not only or l in only)]
    for lang in langs:
        for p in PAGES:
            t0 = time.time()
            try:
                build_one(p, lang)
                print("     [%.1fs]" % (time.time() - t0), flush=True)
            except SystemExit:
                T.flush()
                print("中断：配额问题，已缓存进度")
                sys.exit(1)
            except Exception as e:
                print("  !! %s %s -> %s" % (lang, p, e))
    T.flush()
    print("DONE")
