#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_listicle.py — 从英文榜单页生成 de/ja/ko/fr/it/es 6 个语言版

用法: python3 build_listicle.py
- 源: {ROOT}/blog/top-12-china-yoga-mat-manufacturers.html (EN, 手写)
- 模板(仅取 header/footer chrome): {ROOT}/{lang}/blog/tpe-vs-pu.html
- 翻译: DeepL API, tag_handling=html (保留 <strong>/<a href> 等标签)
- 缓存: cache/listicle_cache.json (幂等, 重跑不重复计费)
- 幂等: 输出文件已存在则重新生成覆盖
"""
import re, json, os, sys, time, hashlib, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import translator as T   # 复用 DEEPL_KEY / DEEPL_URL / 代理 opener

ROOT = os.path.dirname(HERE)
SLUG = "top-12-china-yoga-mat-manufacturers"
EN_PATH = os.path.join(ROOT, "blog", SLUG + ".html")
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
CACHE_PATH = os.path.join(HERE, "cache", "listicle_cache.json")

_cache = json.load(open(CACHE_PATH, encoding="utf-8")) if os.path.exists(CACHE_PATH) else {}


def _save_cache():
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    json.dump(_cache, open(CACHE_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=0)


def deepl_html(texts, lang, retries=3):
    """DeepL 批量翻译, html 模式保留内联标签"""
    body = {"text": texts, "source_lang": "EN", "target_lang": lang.upper(),
            "tag_handling": "html"}
    req = urllib.request.Request(
        T.DEEPL_URL, data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": "DeepL-Auth-Key " + T.DEEPL_KEY,
                 "Content-Type": "application/json"})
    for i in range(retries):
        try:
            raw = T._opener.open(req, timeout=60).read().decode("utf-8")
            d = json.loads(raw)
            return [x["text"] for x in d["translations"]]
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and i < retries - 1:
                time.sleep(3 * (i + 1))
                continue
            raise
        except Exception:
            if i < retries - 1:
                time.sleep(3 * (i + 1))
                continue
            raise


def tr_batch(texts, lang):
    """带缓存的批量翻译; 保持输入顺序"""
    keys = [lang + "|" + hashlib.md5(t.encode("utf-8")).hexdigest() for t in texts]
    miss, miss_idx = [], []
    for i, (t, k) in enumerate(zip(texts, keys)):
        if k in _cache:
            continue
        miss.append(t); miss_idx.append(i)
    if miss:
        print(f"  [{lang}] DeepL {len(miss)} segments...")
        done = False
        # 分批 ≤40 段
        for s in range(0, len(miss), 40):
            res = deepl_html(miss[s:s + 40], lang)
            for t, r, k in zip(miss[s:s + 40], res, [keys[j] for j in miss_idx[s:s + 40]]):
                _cache[k] = r
        _save_cache()
    return [_cache[k] for k in keys]


def read(p):
    return open(p, encoding="utf-8").read()


def write(p, s):
    open(p, "w", encoding="utf-8").write(s)
    print("  written", os.path.relpath(p, ROOT))


# ---------------------------------------------------------------- 解析 EN 页
en = read(EN_PATH)

def _re1(pat, s=en, flags=0):
    m = re.search(pat, s, flags)
    if not m:
        raise SystemExit("EN page parse FAIL: " + pat[:80])
    return m.group(1)

TITLE_EN = _re1(r"<title>(.*?)</title>")
TITLE_CORE_EN = TITLE_EN.replace(" | SANFAN", "")
DESC_EN = _re1(r'<meta name="description" content="(.*?)"')
HEADLINE_EN = _re1(r'"headline": "(.*?)"')
LISTNAME_EN = _re1(r'"name": "(Top 12.*?)"')

faq_m = re.search(r'"@type": "FAQPage",\s*"mainEntity": (\[.*?\])\s*\}\s*</script>', en, re.DOTALL)
FAQ = json.loads(faq_m.group(1))
faq_q_en = [q["name"] for q in FAQ]
faq_a_en = [q["acceptedAnswer"]["text"] for q in FAQ]

POSTMETA_EN = _re1(r'<div class="post-meta">(.*?)</div>')
H1_EN = _re1(r"<h1>(.*?)</h1>")
LEAD_EN = _re1(r'<p class="lead-p">(.*?)</p>')

# article-body 内容
body_m = re.search(r'<div class="article-body">(.*?)\n          </div>\n        </div>\n      </article>', en, re.DOTALL)
if not body_m:
    raise SystemExit("article-body parse FAIL")
BODY = body_m.group(1)

# 收集待翻译块: h2 / p / li / th / CTA box
BLOCK_RE = re.compile(r"(<h2>.*?</h2>|<p>.*?</p>|<p style=\"font-size:13\.5px[^\"]*\">.*?</p>|<li>.*?</li>|<th>.*?</th>"
                      r'|<div style="margin:28px.*?</div>)', re.DOTALL)
blocks = []
for m in BLOCK_RE.finditer(BODY):
    b = m.group(1)
    if b.startswith("<h3>"):
        continue
    blocks.append(b)
# h2/h3 里的 h3 不在 BLOCK_RE 内; 移除 h3(不译) — BLOCK_RE 本就不含 h3
# h1/lead/postmeta 单独译
seg_map = {}  # en_block -> placeholder id
segments = [TITLE_CORE_EN, DESC_EN, HEADLINE_EN, LISTNAME_EN, POSTMETA_EN, H1_EN, LEAD_EN]
segments += faq_q_en + faq_a_en
segments += blocks
# blog 卡片文案
CARD_H3_EN = "Top 12 Yoga Mat Manufacturers in China (2026): Cluster-by-Cluster Comparison"
CARD_P_EN = "12 established factories compared across China's six manufacturing clusters — MOQ, capacity, materials and certifications."
segments += [CARD_H3_EN, CARD_P_EN]

print("total segments:", len(segments))

# ---------------------------------------------------------------- 逐语言生成
LANG_NAMES = {"de": "Deutsch", "ja": "日本語", "ko": "한국어", "fr": "Français", "it": "Italiano", "es": "Español"}

for lang in LANGS:
    tpl_path = os.path.join(ROOT, lang, "blog", "tpe-vs-pu.html")
    tpl = read(tpl_path)
    print("==", lang, "==")
    outs = tr_batch(segments, lang)

    (t_title, t_desc, t_headline, t_listname, t_postmeta, t_h1, t_lead) = outs[:7]
    t_faq_q = outs[7:7 + len(faq_q_en)]
    t_faq_a = outs[7 + len(faq_q_en):7 + len(faq_q_en) + len(faq_a_en)]
    t_blocks = outs[7 + len(faq_q_en) + len(faq_a_en): 7 + len(faq_q_en) + len(faq_a_en) + len(blocks)]
    (t_card_h3, t_card_p) = outs[-2:]

    # --- head: 以 EN head 为基底 ---
    head = en[:en.index("</head>") + len("</head>")]

    # canonical / og:url / mainEntityOfPage → 语言版 URL (hreflang 列表保持不变)
    lang_url = f"https://fjsanfan.com/{lang}/blog/{SLUG}.html"
    head = head.replace(f'<link rel="canonical" href="https://fjsanfan.com/blog/{SLUG}.html" />',
                        f'<link rel="canonical" href="{lang_url}" />')
    head = head.replace(f'<meta property="og:url" content="https://fjsanfan.com/blog/{SLUG}.html" />',
                        f'<meta property="og:url" content="{lang_url}" />')
    head = head.replace(f'"mainEntityOfPage": "https://fjsanfan.com/blog/{SLUG}.html"',
                        f'"mainEntityOfPage": "{lang_url}"')
    head = head.replace('lang="en"', f'lang="{lang}"', 1)
    head = head.replace(f"<title>{TITLE_EN}</title>", f"<title>{t_title} | SANFAN</title>")
    head = head.replace(f'content="{DESC_EN}" />', f'content="{t_desc}" />')
    head = head.replace(f'content="{TITLE_EN}" />', f'content="{t_title} | SANFAN" />')
    head = head.replace(f'content="{DESC_EN}"', f'content="{t_desc}"')  # twitter desc (无自闭合的兜底)
    head = head.replace(f'"headline": "{HEADLINE_EN}"', f'"headline": {json.dumps(t_headline, ensure_ascii=False)}')
    head = head.replace(f'"name": "{LISTNAME_EN}"', f'"name": {json.dumps(t_listname, ensure_ascii=False)}')

    # FAQ JSON-LD 重建
    faq_new = []
    for q, a, tq, ta in zip(faq_q_en, faq_a_en, t_faq_q, t_faq_a):
        faq_new.append({"@type": "Question", "name": tq,
                        "acceptedAnswer": {"@type": "Answer", "text": ta}})
    faq_json = json.dumps({"@context": "https://schema.org", "@type": "FAQPage",
                           "mainEntity": faq_new}, ensure_ascii=False, indent=2)
    head = re.sub(r'("mainEntity": \[.*?\])\s*\}\s*</script>',
                  lambda m: f'"mainEntity": {json.dumps(faq_new, ensure_ascii=False, indent=2)}}}\n  </script>',
                  head, count=1, flags=re.DOTALL)

    # 资源路径 ../ → ../../ (仅 head 里的相对引用)
    head = head.replace('href="../assets/', 'href="../../assets/')
    head = head.replace('src="../assets/', 'src="../../assets/')

    # --- header/footer chrome 来自语言模板 ---
    hdr_m = re.search(r'<header class="site-header">.*?</header>', tpl, re.DOTALL)
    ftr_m = re.search(r'<footer class="site-footer">.*?</footer>\s*<script src=.*?</script>\s*</body>', tpl, re.DOTALL)
    header = hdr_m.group(0).replace("tpe-vs-pu.html", SLUG + ".html")
    footer = ftr_m.group(0)

    # --- article: EN 块替换为译块 ---
    art = en[en.index('<section class="section"'):en.index("</section>") + len("</section>")]
    # 去 lang-en 包裹
    art = art.replace('<div class="lang-en">\n', "").replace("\n          </div>\n        </div>\n      </article>", "\n        </div>\n      </article>")
    # back-link 用模板译法
    tbl_m = re.search(r'<a class="back-link" href="[^"]*">[^<]*</a>', tpl)
    art = re.sub(r'<a class="back-link" href="\.\./blog\.html">[^<]*</a>', tbl_m.group(0), art, count=1)
    # 文本替换
    art = art.replace(f"<title>{TITLE_EN}</title>", "")  # 无操作保险
    art = art.replace(POSTMETA_EN, t_postmeta)
    art = art.replace(f"<h1>{H1_EN}</h1>", f"<h1>{t_h1}</h1>")
    art = art.replace(f'<p class="lead-p">{LEAD_EN}</p>', f'<p class="lead-p">{t_lead}</p>')
    for en_b, tr_b in zip(blocks, t_blocks):
        if en_b not in art:
            raise SystemExit(f"[{lang}] block not found: {en_b[:80]}")
        art = art.replace(en_b, tr_b)

    page = head + "\n<body>\n\n  " + header + "\n\n  " + art + "\n\n  " + footer + "\n"
    out_path = os.path.join(ROOT, lang, "blog", SLUG + ".html")
    write(out_path, page)

    # --- 语言版 blog.html 索引加卡片 ---
    idx_path = os.path.join(ROOT, lang, "blog.html")
    idx = read(idx_path)
    if SLUG not in idx:
        anchor = re.search(r'<a class="post-card" href="/de/blog/tpe-vs-pu\.html">|<a class="post-card" href="[^"]*">', idx)
        first_card = re.search(r'<a class="post-card" href="[^"]*">\n', idx)
        card = (f'<a class="post-card" href="/{lang}/blog/{SLUG}.html">\n'
                f'          <div class="pc-img"><img src="../assets/img/factory-building.webp" width="480" height="480" loading="lazy" alt="Yoga mat manufacturers in China"></div>\n'
                f'          <div class="pc-body">\n'
                f'            <div class="pc-tag">Sourcing</div>\n'
                f'            <div><h3>{t_card_h3}</h3><p>{t_card_p}</p></div>\n'
                f'            <span class="pc-more">→</span>\n'
                f'</div>\n'
                f'        </a>\n')
        # pc-more 文案沿用各站惯例 — 取模板里现有 pc-more 文本
        more_txt = re.search(r'<span class="pc-more">([^<]*)</span>', idx)
        if more_txt:
            card = card.replace("<span class=\"pc-more\">→</span>", f"<span class=\"pc-more\">{more_txt.group(1)}</span>")
        idx = idx.replace(first_card.group(0), first_card.group(0) + "        " + card, 1)
        write(idx_path, idx)
    else:
        print("  blog.html already has card")

print("ALL DONE")
