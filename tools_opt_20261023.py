#!/usr/bin/env python3
"""2026-10-23 优化：缓存头、工厂视频嵌入、GA 仅欧洲弹窗、精简过长 meta description。"""
import re, os, json, html
ROOT = os.path.dirname(os.path.abspath(__file__))
def rd(p): return open(os.path.join(ROOT, p), encoding='utf-8').read()
def wr(p, s): open(os.path.join(ROOT, p), 'w', encoding='utf-8').write(s)

# 1) vercel.json：/assets 缓存 + CSP 允许 youtube-nocookie 与 ytimg
v = json.loads(rd('vercel.json'))
hdrs = v.setdefault('headers', [])
if not any(h.get('source') == '/assets/(.*)' for h in hdrs):
    hdrs.append({"source": "/assets/(.*)", "headers": [
        {"key": "Cache-Control", "value": "public, max-age=604800, stale-while-revalidate=86400"}]})
for h in hdrs:
    for kv in h['headers']:
        if kv['key'] == 'Content-Security-Policy':
            c = kv['value']
            if 'youtube-nocookie' not in c:
                c = c.replace('frame-src https://www.googletagmanager.com', 'frame-src https://www.googletagmanager.com https://www.youtube-nocookie.com')
                c = c.replace("img-src 'self' data:", "img-src 'self' data: https://i.ytimg.com")
            kv['value'] = c
wr('vercel.json', json.dumps(v, ensure_ascii=False, indent=2) + '\n')

# 2) 视频区块
VIDS = [
    ("tpGydYxcliM", "Yoga Mat Factory Tour | Fujian Sanfan Sports - OEM/ODM Yoga Mat Manufacturer in China", "2026-10-20", "16/9"),
    ("q-A42m3paSY", "Inside our rubber yoga mat foaming line", "2026-10-20", "9/16"),
    ("vXn33p42aBY", "Custom printed yoga & Pilates mats - printing and curing", "2026-10-20", "9/16"),
]
def frame(vid, title, ratio):
    return (f'<div class="vid" style="aspect-ratio:{ratio};"><iframe src="https://www.youtube-nocookie.com/embed/{vid}" '
            f'title="{html.escape(title)}" loading="lazy" allow="encrypted-media; picture-in-picture; fullscreen" '
            f'allowfullscreen style="width:100%;height:100%;border:0;border-radius:12px;"></iframe></div>')
schema = {"@context": "https://schema.org", "@graph": [{
    "@type": "VideoObject", "name": t, "description": t + " — filmed at the SANFAN factory in Jinjiang, Fujian, China.",
    "thumbnailUrl": f"https://i.ytimg.com/vi/{i}/hqdefault.jpg", "uploadDate": d,
    "embedUrl": f"https://www.youtube-nocookie.com/embed/{i}", "contentUrl": f"https://www.youtube.com/watch?v={i}"}
    for i, t, d, r in VIDS]}
BLOCK = f'''
  <!-- ===== Factory video (2026-10-23) ===== -->
  <section class="section" id="factory-video">
    <div class="container">
      <div class="section-head">
        <div class="eyebrow">Inside the Factory</div>
        <h2>See Our Factory on Video</h2>
        <p>Real footage from our Jinjiang workshop: foaming, slicing, printing and the sample room.</p>
      </div>
      <div style="display:grid;grid-template-columns:2fr 1fr 1fr;gap:16px;align-items:start;" class="vid-grid">
        {frame(*VIDS[0][:2], VIDS[0][3])}
        {frame(*VIDS[1][:2], VIDS[1][3])}
        {frame(*VIDS[2][:2], VIDS[2][3])}
      </div>
      <p style="margin-top:12px;"><a href="https://www.youtube.com/@sanfanyoga-h7n" rel="noopener">More videos on our YouTube channel →</a></p>
    </div>
    <style>@media (max-width:760px){{.vid-grid{{grid-template-columns:1fr 1fr !important}}.vid-grid .vid:first-child{{grid-column:1/-1}}}}</style>
    <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
  </section>
'''
for p, anchor in [('index.html', '\n  <!-- ===== Product range ===== -->'), ('about.html', '\n  <!-- OEM / ODM -->')]:
    s = rd(p)
    if 'id="factory-video"' not in s:
        assert anchor in s, p
        s = s.replace(anchor, BLOCK + anchor, 1)
        wr(p, s)

# 3) GA：欧洲时区才弹同意横幅，其他地区直接加载
js = rd('assets/js/main.js')
old = "  if (state === 'denied') return;      // 已拒绝：不再打扰（GDPR 允许不再询问）\n"
new = old + ("  // 2026-10-23：只有欧洲（GDPR/英国）访客需要先同意；其他地区直接统计，否则几乎收不到数据\n"
             "  var tz = ''; try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ''; } catch (e) {}\n"
             "  if (tz && !/^(Europe\\/|Atlantic\\/(Reykjavik|Canary|Madeira|Azores|Faroe))/.test(tz)) { loadGA(); return; }\n")
if 'Intl.DateTimeFormat().resolvedOptions().timeZone' not in js:
    assert old in js
    js = js.replace(old, new, 1)
js = js.replace("main.js?v", "main.js?v")
wr('assets/js/main.js', js)

# bump asset version (缓存一周，需改版本号让新 JS 生效)
import glob
n = 0
for f in glob.glob(os.path.join(ROOT, '**/*.html'), recursive=True):
    s = open(f, encoding='utf-8').read()
    s2 = re.sub(r'(assets/(?:js/main\.js|css/styles\.css))\?v[0-9a-z]+', r'\1?v20261023a', s)
    if s2 != s:
        open(f, 'w', encoding='utf-8').write(s2); n += 1
print('version bumped', n)

# 4) EN meta description > 160：在句子/分句边界截到 ≤160
def shorten(d):
    if len(d) <= 160: return d
    parts = re.split(r'(?<=[.!?])\s+', d)
    out = ''
    for p in parts:
        if len((out + ' ' + p).strip()) <= 160: out = (out + ' ' + p).strip()
        else: break
    if len(out) >= 90: return out
    cut = d[:157]
    cut = cut[:max(cut.rfind(','), cut.rfind(' '))].rstrip(' ,;—-')
    return cut + '.'
sm = rd('sitemap.xml')
en = [l.replace('https://fjsanfan.com/', '') for l in re.findall(r'<loc>([^<]+)</loc>', sm)
      if not re.match(r'https://fjsanfan.com/(de|ja|ko|fr|it|es)/', l)]
changed = []
for e in en:
    p = (e or '') + ('index.html' if (e == '' or e.endswith('/')) else '')
    s = rd(p)
    m = re.search(r'<meta name="description" content="([^"]*)"', s)
    if not m: continue
    raw = html.unescape(m.group(1))
    if len(raw) <= 160: continue
    nd = shorten(raw)
    s = s.replace(m.group(0), '<meta name="description" content="%s"' % html.escape(nd, quote=True), 1)
    wr(p, s); changed.append((p, len(raw), len(nd), nd))
for c in changed: print(c)
print('desc changed', len(changed))
