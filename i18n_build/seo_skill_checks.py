#!/usr/bin/env python3
"""吸收自 zeng085/claude-seo（MIT）的三项检查，接入 i18n_build 体检体系：

[A] Schema 政策级校验 —— vendor/claude_seo/schema_ecommerce_validate.validate()
    全部产品页（含 6 语言版）的 Product JSON-LD；B2B 询价模式下
    recommended-offer-price / member-program 记为设计内，只真报 Critical/High。
[B] 内容质量分（Google QRG §4.6 对齐）—— vendor/claude_seo/content_quality.analyse()
    EN 全站正文页；产出总分分布与 <threshold 页清单。
[C] GEO 可引用性 —— 自写启发式（依据 claude-seo 的 GEO 方法论）：
    问题式标题数、自包含段落（120-180 词）数、FAQPage 标记。
    只查内容型页面（applications/materials/blog/faq/index/分类页）。

用法：python3 i18n_build/seo_skill_checks.py [--threshold 70] [--json OUT]
退出码：0 = 无 Critical/High schema 问题且无低分页；1 = 有。
"""
from __future__ import annotations
import json, re, sys, os, html
from html.parser import HTMLParser
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'i18n_build', 'vendor', 'claude_seo'))
import schema_ecommerce_validate as sev
import content_quality as cq

# B2B 询价站设计内（不报）：
#   recommended-offer-price —— 无零售价，询价模式
#   missing-member-program  —— 无会员体系
#   merchant-listing-offer-type —— AggregateOffer(lowPrice/highPrice) 表达价格区间，
#     零售商家列表要求 Offer，但 B2B 不投 Google Shopping，改 Offer 无价反而语义错
B2B_ACCEPTED_RULES = {'recommended-offer-price', 'missing-member-program',
                      'merchant-listing-offer-type'}
PRODUCT_PAGE_RE = re.compile(r'/products/[^/]+\.html$')

# ---------- 文本提取（stdlib，不依赖 bs4） ----------
class _TextExtract(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self._skip = [], 0
        self.headings, self.paragraphs = [], []
        self._in_p = False
        self._cur_h = self._cur_p = None
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self._skip += 1
        elif tag in ('h1', 'h2', 'h3', 'h4'):
            self._cur_h = []
        elif tag == 'p':
            self._in_p, self._cur_p = True, []
    def handle_endtag(self, tag):
        if tag in ('script', 'style') and self._skip:
            self._skip -= 1
        elif tag in ('h1', 'h2', 'h3', 'h4') and self._cur_h is not None:
            t = html.unescape(''.join(self._cur_h)).strip()
            if t: self.headings.append((tag, t))
            self._cur_h = None
        elif tag == 'p' and self._in_p:
            t = html.unescape(''.join(self._cur_p)).strip()
            if t: self.paragraphs.append(t)
            self._in_p = False
    def handle_data(self, data):
        if self._skip: return
        self.parts.append(data)
        if self._cur_h is not None: self._cur_h.append(data)
        if self._in_p: self._cur_p.append(data)

def extract(path):
    p = _TextExtract()
    p.feed(open(path, encoding='utf-8', errors='replace').read())
    text = re.sub(r'\s+', ' ', ' '.join(p.parts))
    return text, p.headings, p.paragraphs

LD_RE = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
def jsonld(path):
    out = []
    for b in LD_RE.findall(open(path, encoding='utf-8', errors='replace').read()):
        try: out.append(json.loads(b))
        except Exception: pass
    return out

# ---------- [A] Schema 政策校验 ----------
def check_schema():
    stats, real, accepted = Counter(), [], 0
    pages = []
    for L in ('', 'de/', 'ja/', 'ko/', 'fr/', 'it/', 'es/'):
        d = os.path.join(ROOT, L, 'products')
        if os.path.isdir(d):
            pages += [os.path.join(d, f) for f in os.listdir(d) if f.endswith('.html')]
    no_product = []
    for p in sorted(pages):
        blocks = jsonld(p)
        payload = {'@graph': blocks} if len(blocks) > 1 else (blocks[0] if blocks else {})
        r = sev.validate(payload)
        stats.update(r['summary'])
        rel = os.path.relpath(p, ROOT)
        has_prod = any(b for b in blocks if 'Product' in json.dumps(b))
        if not has_prod:
            no_product.append(rel)
        for f in r['findings']:
            if f['severity'] in ('Critical', 'High') and f['rule'] not in B2B_ACCEPTED_RULES:
                real.append((rel, f['severity'], f['rule'], f['message']))
            elif f['rule'] in B2B_ACCEPTED_RULES:
                accepted += 1
    return {'pages': len(pages), 'summary': dict(stats), 'real': real,
            'no_product': no_product, 'accepted_medium': accepted}

# ---------- [B] 内容质量分 ----------
CONTENT_GLOB = ['index.html', 'materials.html', 'faq.html', 'about.html', 'products.html',
                'blog/*.html', 'applications/*.html',
                'tpe-yoga-mats.html', 'suede-cork-yoga-mats.html', 'pu-rubber-yoga-mats.html',
                'meditation-pilates-mats.html', 'foam-rollers.html', 'massage-recovery.html',
                'resistance-bands.html', 'yoga-props-accessories.html', 'jump-ropes.html',
                'strength-training.html']

def check_content(threshold):
    import glob as g
    pages = []
    for pat in CONTENT_GLOB:
        pages += g.glob(os.path.join(ROOT, pat))
    scores = []
    for p in sorted(set(pages)):
        text, _, _ = extract(p)
        r = cq.analyse(text)
        scores.append((os.path.relpath(p, ROOT), r['overall_quality'], r['flags'], r['tokens']))
    low = [s for s in scores if s[1] < threshold]
    avg = round(sum(s[1] for s in scores) / max(1, len(scores)), 1)
    return {'pages': len(scores), 'avg': avg,
            'lowest': sorted(scores, key=lambda s: s[1])[:8], 'low': low, 'threshold': threshold}

# ---------- [C] GEO 可引用性 ----------
QWORD_RE = re.compile(r'^(what|how|why|which|when|who|where|can|do|does|is|are|should)\b|？|\?', re.I)
def check_geo():
    import glob as g
    pages = []
    for pat in ['index.html', 'materials.html', 'faq.html', 'blog/*.html', 'applications/*.html']:
        pages += g.glob(os.path.join(ROOT, pat))
    rows, weak = [], []
    for p in sorted(set(pages)):
        _, heads, paras = extract(p)
        q_heads = [t for _, t in heads if QWORD_RE.search(t)]
        lens = [len(t.split()) for t in paras]
        citable = sum(1 for n in lens if 120 <= n <= 180)
        longest = max(lens, default=0)
        has_faq = any('FAQPage' in json.dumps(b) for b in jsonld(p))
        rel = os.path.relpath(p, ROOT)
        rows.append((rel, len(q_heads), citable, longest, has_faq))
        if not q_heads and not has_faq:
            weak.append(rel)
    return {'pages': len(rows), 'rows': rows, 'no_q_no_faq': weak}

def main():
    threshold = 70
    if '--threshold' in sys.argv:
        threshold = int(sys.argv[sys.argv.index('--threshold') + 1])
    A = check_schema(); B = check_content(threshold); C = check_geo()

    print('=' * 62)
    print(f"[A] Schema 政策校验 —— {A['pages']} 个产品页（7 语言）")
    print(f"    Critical={A['summary'].get('critical',0)} High={A['summary'].get('high',0)}"
          f" Medium={A['summary'].get('medium',0)} Info={A['summary'].get('info',0)}")
    print(f"    真问题 {len(A['real'])} 条；B2B 设计内豁免（询价无价/无会员/AggregateOffer 价格区间）"
          f" {A['accepted_medium']} 条")
    for rel, sev_, rule, msg in A['real'][:10]:
        print(f"    [{sev_}] {rel}: {rule} — {msg}")
    if A['no_product']: print(f"    无 Product 标记: {A['no_product'][:5]}")

    print('=' * 62)
    print(f"[B] 内容质量分（QRG 对齐）—— {B['pages']} 个 EN 页面，均分 {B['avg']}/100，阈值 {B['threshold']}")
    for rel, sc, flags, tok in B['lowest']:
        print(f"    {sc:3d}/100  {rel}  {','.join(flags) or '-'}")
    print(f"    低于阈值: {len(B['low'])} 页")

    print('=' * 62)
    print(f"[C] GEO 可引用性 —— {C['pages']} 个内容页")
    nq = sum(1 for r in C['rows'] if r[1] > 0); nc = sum(1 for r in C['rows'] if r[2] > 0)
    nf = sum(1 for r in C['rows'] if r[4])
    print(f"    有问题式标题 {nq}/{C['pages']}  有 120-180 词可引用段 {nc}/{C['pages']}  有 FAQPage {nf}/{C['pages']}")
    for rel, qh, ct, lg, faq in C['rows']:
        mark = 'OK ' if (qh or faq) else '!! '
        print(f"    {mark} q标题={qh:<2} 可引段={ct:<2} 最长段={lg:<3} faq={'Y' if faq else '-'}  {rel}")
    if C['no_q_no_faq']: print(f"    ⚠ 无问题标题且无 FAQ: {len(C['no_q_no_faq'])} 页")

    ok = not A['real'] and not B['low']
    sys.exit(0 if ok else 1)

if __name__ == '__main__':
    main()
