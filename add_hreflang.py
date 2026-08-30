import re, glob, os

# 全部页面：7 主页面 + 6 博客 + 27 产品页
pages = ['index.html','about.html','products.html','product.html','contact.html',
         'faq.html','blog.html'] + sorted(glob.glob('blog/*.html')) + sorted(glob.glob('products/*.html'))

# 注意：不要再声明 hreflang="zh"。站点没有独立的 /zh/ 目录，
# 把英文 URL 同时声明成 en 和 zh 是冲突信号（Google 会认为同一 URL 有两种语言）。
# 中文仍可通过页面内的语言切换器访问，但那不是独立语言版本，不应写进 hreflang。
block_tpl = ('\n  <link rel="alternate" hreflang="en" href="{u}" />'
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
