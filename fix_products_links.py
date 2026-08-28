import re

p = 'products.html'
h = open(p, encoding='utf-8').read()
before = h.count('product.html?id=')

# 1) map phantom ids (only present in JSON-LD) to real products
h = h.replace('product.html?id=roller1', 'product.html?id=fr1')
h = h.replace('product.html?id=bands1', 'product.html?id=rb1')
h = h.replace('product.html?id=ball1', 'product.html?id=rb2')
h = h.replace('product.html?id=db1', 'product.html?id=fi5')

# 2) global rewrite ?id= -> static path
h2 = re.sub(r'product\.html\?id=([a-z0-9]+)', r'products/\1.html', h)
after = h2.count('product.html?id=')
leftover = re.findall(r'products/(roller1|bands1|ball1|db1)\.html', h2)
open(p, 'w', encoding='utf-8').write(h2)
print('before links:', before, '| after ?id= remaining:', after, '| phantom leftover:', leftover)
