import re, glob, os

# 全部页面：7 主页面 + 6 博客 + 27 产品页
pages = ['index.html','about.html','products.html','product.html','contact.html',
         'faq.html','blog.html'] + sorted(glob.glob('blog/*.html')) + sorted(glob.glob('products/*.html'))

block_tpl = ('\n  <link rel="alternate" hreflang="en" href="{u}" />'
            '\n  <link rel="alternate" hreflang="zh" href="{u}" />'
            '\n  <link rel="alternate" hreflang="x-default" href="{u}" />')

done = 0
for f in pages:
    h = open(f, encoding='utf-8').read()
    if 'hreflang="x-default"' in h:
        continue
    m = re.search(r'<link rel="canonical" href="([^"]+)"', h)
    if not m:
        print('NO CANONICAL, skip:', f); continue
    url = m.group(1)
    block = block_tpl.format(u=url)
    # 在 canonical link 整行之后插入
    h, n = re.subn(r'(<link rel="canonical" href="[^"]+"[^>]*>)', r'\1' + block, h, count=1)
    if n == 0:
        print('CANONICAL MATCH FAILED:', f); continue
    open(f, 'w', encoding='utf-8').write(h)
    done += 1

print(f'DONE: hreflang added to {done} pages')
