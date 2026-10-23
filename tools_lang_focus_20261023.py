#!/usr/bin/env python3
"""2026-10-23 收录聚焦：
1) ja/ko/fr/it 的产品页 (products/*.html) 加 noindex,follow，并移除其全部 hreflang；
   en/de/es 产品页移除指向 ja/ko/fr/it 的 hreflang。
2) sitemap.xml 删掉这 588 个 URL，产品条目里去掉 ja/ko/fr/it alternate，lastmod 改 ISO 日期。
3) 英文页（sitemap 中 EN URL）删除隐藏中文 .lang-zh 元素和“中文”切换按钮。
"""
import re, os, sys

DROP = ['ja', 'ko', 'fr', 'it']
ROOT = os.path.dirname(os.path.abspath(__file__))
stats = {'noindex': 0, 'hreflang_pages': 0, 'zh_removed': 0, 'zh_pages': 0}

def rd(p): return open(os.path.join(ROOT, p), encoding='utf-8').read()
def wr(p, s): open(os.path.join(ROOT, p), 'w', encoding='utf-8').write(s)

def hreflang_re(langs):
    alt = '|'.join(langs)
    return re.compile(r'[ \t]*<link rel="alternate" hreflang="(?:%s)" href="[^"]*"\s*/?>\n?' % alt)

prod = sorted(f for f in os.listdir(os.path.join(ROOT, 'products')) if f.endswith('.html'))

# 1) product pages
for f in prod:
    for lang in ['en', 'de', 'es'] + DROP:
        p = f'products/{f}' if lang == 'en' else f'{lang}/products/{f}'
        if not os.path.exists(os.path.join(ROOT, p)):
            continue
        s = rd(p); o = s
        if lang in DROP:
            s = hreflang_re(['en', 'de', 'ja', 'ko', 'fr', 'it', 'es', 'x-default']).sub('', s)
            if 'name="robots"' in s:
                s = re.sub(r'<meta name="robots" content="[^"]*"\s*/?>', '<meta name="robots" content="noindex,follow" />', s)
            else:
                s = re.sub(r'(<meta name="viewport"[^>]*>)', r'\1\n  <meta name="robots" content="noindex,follow" />', s, count=1)
            if 'noindex,follow' in s: stats['noindex'] += 1
            else: print('NO VIEWPORT', p)
        else:
            s = hreflang_re(DROP).sub('', s)
        if s != o:
            stats['hreflang_pages'] += 1
            wr(p, s)

# 2) sitemap
sm = rd('sitemap.xml')
drop_locs = {f'https://fjsanfan.com/{l}/products/{f}' for l in DROP for f in prod}
def fix_url(m):
    block = m.group(0)
    loc = re.search(r'<loc>([^<]+)</loc>', block).group(1)
    if loc in drop_locs:
        return ''
    if '/products/' in loc:
        block = re.sub(r'[ \t]*<xhtml:link rel="alternate" hreflang="(?:%s)" href="[^"]*"/>\n' % '|'.join(DROP), '', block)
    return block
sm = re.sub(r'[ \t]*<url>.*?</url>\n?', fix_url, sm, flags=re.S)
sm = re.sub(r'<lastmod>[A-Za-z]{3} (\d{4}-\d{2}-\d{2})[^<]*</lastmod>', r'<lastmod>\1</lastmod>', sm)
wr('sitemap.xml', sm)
en_locs = [l for l in re.findall(r'<loc>([^<]+)</loc>', sm)
           if not re.match(r'https://fjsanfan.com/(de|ja|ko|fr|it|es)/', l)]
print('sitemap urls', len(re.findall('<loc>', sm)), 'en', len(en_locs))

# 3) strip .lang-zh from EN pages
TAG = re.compile(r'<(/?)([a-zA-Z][a-zA-Z0-9]*)\b[^>]*?(/?)>')
START = re.compile(r'<([a-zA-Z][a-zA-Z0-9]*)\b[^>]*\bclass="(?:[^"]*\s)?lang-zh(?:\s[^"]*)?"[^>]*>')
VOID = {'br', 'img', 'hr', 'input', 'meta', 'link', 'wbr', 'source'}

def strip_zh(s):
    out = []; i = 0; n = 0
    while True:
        m = START.search(s, i)
        if not m:
            out.append(s[i:]); break
        name = m.group(1).lower()
        out.append(s[i:m.start()])
        depth = 1; j = m.end()
        while depth:
            t = TAG.search(s, j)
            if not t: raise ValueError('unbalanced ' + name)
            if t.group(2).lower() == name and name not in VOID and not t.group(3):
                depth += -1 if t.group(1) else 1
            j = t.end()
        i = j; n += 1
    return ''.join(out), n

ZH_BTN = '<button type="button" data-setlang="zh" title="中文">中文</button>'
for loc in en_locs:
    path = loc.replace('https://fjsanfan.com/', '')
    if path == '' or path.endswith('/'): path += 'index.html'
    if not os.path.exists(os.path.join(ROOT, path)):
        print('missing', path); continue
    s = rd(path)
    s2, n = strip_zh(s)
    s2 = s2.replace(ZH_BTN, '')
    if s2 != s:
        stats['zh_removed'] += n; stats['zh_pages'] += 1
        wr(path, s2)

# JS: 不再切换到中文（老访客存的 zh 偏好会让英文内容被隐藏）
js = rd('assets/js/main.js')
guard = "function applyLang(lang) {\n  if (lang === 'zh') lang = 'en'; // 2026-10-23 英文页已移除隐藏中文\n"
if guard not in js:
    js = js.replace("function applyLang(lang) {\n", guard, 1)
    wr('assets/js/main.js', js)
print(stats)
