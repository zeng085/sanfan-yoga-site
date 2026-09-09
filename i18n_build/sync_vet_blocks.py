#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 blog/vet-factory.html（EN）新增的「验厂数字块 + 3 条 FAQ」同步到 de/ja/ko/fr/it/es 语言版。
- 新增正文块：插到该语言页最后一个 <h2>（即 FAQ 标题）之前
- 新增 FAQ：插到 article-body 结束 </div> 之前
- FAQPage JSON-LD：追加 3 条译文
- Article JSON-LD：补 dateModified
"""
import re, os, sys, json

HERE = "/Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16/i18n_build"
sys.path.insert(0, HERE)
import importlib.util
spec = importlib.util.spec_from_file_location("bl", os.path.join(HERE, "build_listicle.py"))

ROOT = "/Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16"
EN_PATH = os.path.join(ROOT, "blog", "vet-factory.html")
LANGS = ["de", "ja", "ko", "fr", "it", "es"]

# --- 复用 build_listicle 的 DeepL 封装（它会先读 translator 模块）---
sys.argv = ["x"]
src = open(os.path.join(HERE, "build_listicle.py"), encoding="utf-8").read()
src = src.split("# ---------------------------------------------------------------- 解析 EN 页")[0]
ns = {"__name__": "blmod", "__file__": os.path.join(HERE, "build_listicle.py")}
exec(compile(src, "build_listicle_head.py", "exec"), ns)
tr_batch = ns["tr_batch"]

en = open(EN_PATH, encoding="utf-8").read()

# 1) 新增正文块
m_start = re.search(r"<h2>The MOQ is a colour-change rule, not a policy</h2>", en)
m_end = re.search(r"\n          <h2>FAQ</h2>", en)
assert m_start and m_end, "EN new blocks not found"
NEW_BLOCKS = en[m_start.start():m_end.start()].rstrip()

# 拆成可翻译单元（保留标签交给 DeepL html 模式）
BLOCK_RE = re.compile(r"(<h2>.*?</h2>|<p>.*?</p>|<li>.*?</li>|<ul>.*?</ul>)", re.DOTALL)
new_items = [b for b in BLOCK_RE.findall(NEW_BLOCKS)]
assert len(new_items) >= 10, len(new_items)

# 2) 新增 FAQ（EN）
faq_start = re.search(r"<h3>Is 500 pcs really the minimum for a custom yoga mat\?</h3>", en)
faq_end = re.search(r"\n\n          </div>", en[faq_start.start():])
NEW_FAQ_HTML = en[faq_start.start():faq_start.start() + faq_end.start()].rstrip()
new_faq_q = re.findall(r"<h3>(.*?)</h3>", NEW_FAQ_HTML, re.DOTALL)
new_faq_a = re.findall(r"<p>(.*?)</p>", NEW_FAQ_HTML, re.DOTALL)
assert len(new_faq_q) == 3 and len(new_faq_a) == 3, (new_faq_q, new_faq_a)

segments = new_items + new_faq_q + new_faq_a
print("segments:", len(segments))

for lang in LANGS:
    path = os.path.join(ROOT, lang, "blog", "vet-factory.html")
    page = open(path, encoding="utf-8").read()
    if "colour-change rule" in page or "MOQ is a" in page:
        print(f"[{lang}] already patched, skip")
        continue
    print("==", lang, "==")
    outs = tr_batch(segments, lang)
    n = len(new_items)
    t_items = outs[:n]
    t_q = outs[n:n + 3]
    t_a = outs[n + 3:n + 6]

    # 组装译文正文块
    blocks_html = NEW_BLOCKS
    for src_b, tr_b in zip(new_items, t_items):
        blocks_html = blocks_html.replace(src_b, tr_b)
    # 组装译文 FAQ
    faq_html = NEW_FAQ_HTML
    for q, a, tq, ta in zip(new_faq_q, new_faq_a, t_q, t_a):
        faq_html = faq_html.replace(f"<h3>{q}</h3>", f"<h3>{tq}</h3>")
        faq_html = faq_html.replace(f"<p>{a}</p>", f"<p>{ta}</p>")
    # 去掉 JSON-LD 里不友好的连字符/引号（FAQ 纯文本）
    def plain(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # --- 插入正文块：最后一个 <h2> 之前 ---
    h2s = list(re.finditer(r"<h2>.*?</h2>", page, re.DOTALL))
    last_h2 = h2s[-1]
    page = page[:last_h2.start()] + "\n" + blocks_html + "\n" + page[last_h2.start():]

    # --- 插入 FAQ：FAQ 标题之后第一个 \n</div>\n</div> 之前 ---
    h2s = list(re.finditer(r"<h2>.*?</h2>", page, re.DOTALL))
    faq_pos = h2s[-1].end()
    close_m = re.search(r"\n</div>\n</div>", page[faq_pos:])
    assert close_m, f"[{lang}] article-body close not found"
    ins = faq_pos + close_m.start()
    page = page[:ins] + "\n" + faq_html + page[ins:]

    # --- JSON-LD: FAQPage 追加 ---
    def faq_sub(m):
        data = json.loads(m.group(1))
        for q, a in zip(t_q, t_a):
            data.append({"@type": "Question", "name": q,
                         "acceptedAnswer": {"@type": "Answer", "text": a}})
        return '"mainEntity": ' + json.dumps(data, ensure_ascii=False, indent=2)
    page, cnt = re.subn(r'"mainEntity": (\[.*?\])\s*\}\s*</script>',
                        lambda m: faq_sub(m) + "}\n  </script>", page, count=1, flags=re.DOTALL)
    assert cnt == 1, f"[{lang}] FAQPage JSON-LD not patched"

    # --- JSON-LD: dateModified ---
    if '"dateModified"' not in page:
        page, cnt2 = re.subn(r'("datePublished": "[0-9-]+",)',
                             r'\1\n  "dateModified": "2026-09-09",', page, count=1)
        print("  dateModified added:", cnt2)

    # --- post-meta 阅读时长 6 → 11 ---
    def meta_sub(m):
        return m.group(0).replace(re.sub(r"(?<!\d)6(?!\d)", "11", m.group(1), count=1),
                                  m.group(1)) if False else m.group(0).replace(
            m.group(1), re.sub(r"(?<!\d)6(?!\d)", "11", m.group(1), count=1))
    page = re.sub(r'(<div class="post-meta">)(.*?)(</div>)',
                  lambda m: m.group(1) + re.sub(r"(?<!\d)6(?!\d)", "11", m.group(2), count=1) + m.group(3),
                  page, count=1)

    open(path, "w", encoding="utf-8").write(page)
    print("  written", path)

print("DONE")
