import re, glob, os

# 处理 blog.html 列表页 + 6 篇博客文章页
files = ['blog.html'] + sorted(glob.glob('blog/*.html'))

def downgrade_last_h1(html):
    opens = list(re.finditer(r'<h1([^>]*)>', html))
    if len(opens) < 2:
        return html, False
    m = opens[-1]          # ZH 块的 h1（每页最后那个）
    attrs = m.group(1)     # 列表页带 style，文章页为空
    s, e = m.span()
    new_open = '<h2 class="post-title"' + attrs + '>'
    html = html[:s] + new_open + html[e:]
    j = html.find('</h1>', e)
    if j == -1:
        return html, False
    html = html[:j] + '</h2>' + html[j + 5:]
    return html, True

for f in files:
    h = open(f, encoding='utf-8').read()
    h2, changed = downgrade_last_h1(h)
    if changed:
        open(f, 'w', encoding='utf-8').write(h2)
        print('fixed (ZH h1->h2.post-title):', f)
    else:
        print('skip (no dual h1):', f)
