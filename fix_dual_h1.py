import re, glob, os

# ⚠️ 本文件是 2026-09 的一次性脚本，**已被取代**，请勿再直接用：
#    i18n_build/fix_blog_dual_h1_20260925.py
#    新脚本更严谨：限定只改 div.lang-zh 内的 h1、带结构断言（降级后 h1 必须==1、
#    中文块必须拿到 h2.post-title）、幂等复跑、--check 自检。本文件保留仅作历史记录。

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
