#!/usr/bin/env python3
"""2026-11-06 收录聚焦第二步（用户 00:38 同意）：
de/es 的产品页 (de|es/products/*.html) 加 noindex,follow 并移除其 hreflang；
EN 产品页移除指向 de/es 的 hreflang（保留 en + x-default）；
sitemap.xml 删掉 de/es 产品 URL，EN 产品条目去掉 de/es alternate。
de/es 首页、分类页、博客不动。URL 不变、原文不删，可回滚。
"""
import re, os
DROP = ['de', 'es']
ROOT = os.path.dirname(os.path.abspath(__file__))
st = {'noindex': 0, 'en_hreflang': 0, 'sitemap_removed': 0}
rd = lambda p: open(os.path.join(ROOT, p), encoding='utf-8').read()
def wr(p, s): open(os.path.join(ROOT, p), 'w', encoding='utf-8').write(s)
def hl(langs):
    return re.compile(r'[ \t]*<link rel="alternate" hreflang="(?:%s)" href="[^"]*"\s*/?>\n?' % '|'.join(langs))
ALL = hl(['en', 'de', 'es', 'ja', 'ko', 'fr', 'it', 'x-default'])
prod = sorted(f for f in os.listdir(os.path.join(ROOT, 'products')) if f.endswith('.html'))
for f in prod:
    p = f'products/{f}'; s = rd(p); o = s
    s = hl(DROP).sub('', s)
    if s != o: wr(p, s); st['en_hreflang'] += 1
    for l in DROP:
        p = f'{l}/products/{f}'
        if not os.path.exists(os.path.join(ROOT, p)): continue
        s = ALL.sub('', rd(p))
        if 'name="robots"' in s:
            s = re.sub(r'<meta name="robots" content="[^"]*"\s*/?>', '<meta name="robots" content="noindex,follow" />', s)
        else:
            s = re.sub(r'(<meta name="viewport"[^>]*>)', r'\1\n  <meta name="robots" content="noindex,follow" />', s, count=1)
        assert 'noindex,follow' in s, p
        wr(p, s); st['noindex'] += 1
sm = rd('sitemap.xml')
def fix(m):
    b = m.group(0); loc = re.search(r'<loc>([^<]+)</loc>', b).group(1)
    if re.match(r'https://fjsanfan.com/(de|es)/products/', loc):
        st['sitemap_removed'] += 1; return ''
    if '/products/' in loc:
        b = re.sub(r'[ \t]*<xhtml:link rel="alternate" hreflang="(?:de|es)" href="https://fjsanfan.com/(?:de|es)/products/[^"]*"/>\n', '', b)
    return b
sm = re.sub(r'[ \t]*<url>.*?</url>\n?', fix, sm, flags=re.S)
wr('sitemap.xml', sm)
print(st, 'sitemap urls', sm.count('<loc>'))
