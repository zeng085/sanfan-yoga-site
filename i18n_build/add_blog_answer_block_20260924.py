#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
给博客补「自足答案块」（GEO 计划里的 H 项）—— 只给真正缺的那一篇。

⚠️ 先纠正一个判据错误（2026-09-24 实测）：
   计划里写的「答案块 134–167 词、现中位 45 词、0 段达标」是**量错了对象**。
   实际量到的「顶部 blockquote」：EN 10 篇里有 8 篇**本来就在 134–167 区间**
   （中位 141，范围 128–160）。那个 45 词是正文段落的统计，不是答案块的。

   更要紧的是：**134–167 词是 EN 专属判据**，不能套到译文上——
   ja 341–426 / ko 307–381 是「字符数」口径（CJK 无空格分词），
   fr/de/es/it 146–214 是译文天然膨胀（罗曼语/德语 +10~30%）。
   拿 EN 的尺子去「修」译文会把健康内容改坏。

真实缺口（本次修的就是这个）：
   `top-12-china-yoga-mat-manufacturers.html` —— 7 个语言版**全都没有答案块**，
   开头是一段「How this list was compiled」方法说明。
   而这恰是 AI 最可能引用的采购向查询页（"top yoga mat manufacturers China"）。

做法：
  - EN 页两个语言块（.lang-en 的 article-body / .lang-zh 的 article-body）各插一处
  - 6 个语言版页面各插一处，文案由 translator.py(DeepL) 从 EN 译出
  - 标记 <!-- ansbox:v1 --> 包裹，替换式注入（幂等，可反复跑）

用法:
    python3 i18n_build/add_blog_answer_block_20260924.py            # 试跑
    python3 i18n_build/add_blog_answer_block_20260924.py --apply    # 写入
    python3 i18n_build/add_blog_answer_block_20260924.py --check    # 体检
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

APPLY = '--apply' in sys.argv
CHECK = '--check' in sys.argv

SLUG = 'top-12-china-yoga-mat-manufacturers.html'
EN_PAGE = f'blog/{SLUG}'
LANGS = ['de', 'ja', 'ko', 'fr', 'it', 'es']
DATA = os.path.join(HERE, 'blog_answer_data.json')
MARK_A, MARK_B = '<!-- ansbox:v1 -->', '<!-- /ansbox:v1 -->'

# 答案块文案：全部事实取自本页正文/FAQ，不引入新数字。
# 目标：EN 134–167 词（GEO 可引用性带宽），自足、可直接被引用。
EN = (
    "China's yoga mat industry is organised into five clusters, and the cluster usually "
    "matters more than the individual name. Jiangsu \u2014 Yancheng and Zhangjiagang \u2014 "
    "dominates PVC and foam volume. Zhejiang \u2014 Ningbo and Yiwu \u2014 leads in premium and "
    "tech-differentiated mats. Hubei's Wuhan is strongest in eco-certified, vertically "
    "integrated production. Guangdong's Dongguan excels at studio-grade rubber and PU. "
    "Fujian \u2014 Jinjiang and Quanzhou \u2014 competes on the lowest minimums and the fastest "
    "sampling. The twelve suppliers below are grouped by cluster rather than ranked, because "
    "every figure here is self-reported: a shortlist, not a verdict. For TPE mats, 100 to 500 "
    "pieces per colour is a realistic production MOQ; PU and natural rubber run higher because "
    "of lamination. Double-layer TPE typically prices around US$2.9\u20138 FOB, PU-rubber and "
    "cork composites roughly US$8\u201318. Always ask for the certificate number rather than "
    "the certificate image, and verify it with the issuing body."
)

ZH = (
    "\u4e2d\u56fd\u745c\u4f3d\u57ab\u4ea7\u4e1a\u6309\u4ea7\u533a\u96c6\u7fa4\u5206\u5e03\uff0c"
    "\u9009\u4ea7\u533a\u5f80\u5f80\u6bd4\u9009\u540d\u5b57\u66f4\u91cd\u8981\u3002\u6c5f\u82cf"
    "\uff08\u76d0\u57ce\u3001\u5f20\u5bb6\u6e2f\uff09\u4ee5 PVC \u4e0e\u53d1\u6ce1\u4ea7\u80fd"
    "\u4e3a\u4e3b\uff1b\u6d59\u6c5f\uff08\u5b81\u6ce2\u3001\u4e49\u4e4c\uff09\u5728\u9ad8\u7aef"
    "\u4e0e\u5de5\u827a\u5dee\u5f02\u5316\u4ea7\u54c1\u4e0a\u9886\u5148\uff1b\u6e56\u5317\u6b66"
    "\u6c49\u64c5\u957f\u73af\u4fdd\u8ba4\u8bc1\u4e0e\u5782\u76f4\u4e00\u4f53\u5316\u751f\u4ea7"
    "\uff1b\u5e7f\u4e1c\u4e1c\u839e\u5728\u9986\u7528\u7ea7\u6a61\u80f6\u4e0e PU \u4e0a\u6700"
    "\u5f3a\uff1b\u798f\u5efa\uff08\u664b\u6c5f\u3001\u6cc9\u5dde\uff09\u7684\u7ade\u4e89\u529b"
    "\u5728\u6700\u4f4e\u8d77\u8ba2\u91cf\u4e0e\u6700\u5feb\u6253\u6837\u3002\u4e0b\u9762 12 "
    "\u5bb6\u6309\u4ea7\u533a\u5f52\u7c7b\u800c\u975e\u6392\u540d\uff0c\u56e0\u4e3a\u6240\u6709"
    "\u6570\u5b57\u5747\u4e3a\u81ea\u6211\u7533\u62a5\u2014\u2014\u662f\u5019\u9009\u540d\u5355"
    "\uff0c\u4e0d\u662f\u7ed3\u8bba\u3002TPE \u745c\u4f3d\u57ab\u6bcf\u8272 100\u2013500 "
    "\u7247\u662f\u73b0\u5b9e\u7684\u91cf\u4ea7\u8d77\u8ba2\u91cf\uff1bPU \u4e0e\u5929\u7136"
    "\u6a61\u80f6\u56e0\u8d34\u5408\u5de5\u5e8f\u800c\u66f4\u9ad8\u3002\u53cc\u5c42 TPE \u7684 "
    "FOB \u4ef7\u901a\u5e38\u5728 2.9\u20138 \u7f8e\u5143\uff0cPU \u6a61\u80f6\u4e0e\u8f6f\u6728"
    "\u590d\u5408\u7ea6 8\u201318 \u7f8e\u5143\u3002\u6838\u9a8c\u8d44\u8d28\u8bf7\u7d22\u53d6"
    "\u8bc1\u4e66\u7f16\u53f7\uff0c\u800c\u4e0d\u662f\u8bc1\u4e66\u56fe\u7247\u3002"
)


def words(t):
    """EN 词数口径（与本项目既有判据一致）"""
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'\u2019\-\.%]*", re.sub(r'<[^>]+>', ' ', t)))


# ⭐ 译文 lint：本站在 protect() 包裹术语后，DeepL 会咬掉相邻词的词尾/吞掉空格。
# 既有体检脚本（verify_round 的「术语粘连」）只认「术语+小写」，测不出下面第 2 类。
# 2026-09-24 实测中招：it `in gomm PVC`（gomma→gomm）、`compositi PUa base`（PU 与 a 粘住）。
#
# ⚠️ 两条使用边界（都踩过）：
#   1) 只对**译文串**跑，别拿去扫整页 —— 全站扫会命中语言切换器的「中文 / 日本語」
#      标签和 contact 页的「微信」，190 处全是假阳性。
#   2) 术语后跟复数 `-s/-es` 是**合法英文/法文**（`MOQs` / `EVAs`），要白名单放行，
#      否则 16 处假阳性。真正的咬词尾长这样：`PUa`（应为 `PU a`）。
#   3) ⛔ **不要试图加规则去抓「带空格的咬词尾」**（如 `gomm PVC`）。已实测：
#      抽样 150 个语言页得 33 处命中，**全是假阳性**（vs / chez / oder / cual /
#      für / por / mejor / cuir / tapis 都是正常词）。无词典无法区分，
#      中文/日文/韩文页更是无从判断。→ 这类只能**人工通读译文**一遍，
#      脚本的职责是减少要看的量，不是代替判决。
TERM = r'(?:TPE|PVC|PU|EVA|NBR|MOQ)'
PLURAL_OK = {'s', 'es'}
LINT = [
    (re.compile(TERM + r'(?=([a-z\u00e0-\u00ff]{1,3})\b)'), '术语后紧跟小写词尾', PLURAL_OK),
    (re.compile(r'(?<![A-Za-z\u00e0-\u00ff])[a-z\u00e0-\u00ff]{2,6}(?=' + TERM + r')'),
     '术语前紧贴小写残词（词尾被咬）', None),
]
HAN = re.compile(r'[\u4e00-\u9fff]')


def lint_translations(data):
    """返回 [(lang, 问题描述)]；ko 出现汉字视为硬错误（该站韩文页不用汉字）"""
    issues = []
    for lg in LANGS:
        t = data.get(lg) or ''
        for rx, desc, allow in LINT:
            for m in rx.finditer(t):
                sfx = m.group(1) if m.groups() else None
                if allow and sfx and sfx.lower() in allow:
                    continue
                issues.append((lg, f'{desc}: …{t[max(0, m.start()-24):m.end()+14]}…'))
        if lg == 'ko':
            han = HAN.findall(t)
            if han:
                issues.append((lg, f'韩文页出现汉字（应转写为谚文）：{"".join(han)}'))
    return issues


def build_data(retranslate=False):
    """EN + ZH 手写，6 语言经 DeepL；结果落盘复用"""
    data = {}
    if os.path.exists(DATA) and not retranslate:
        data = json.load(open(DATA, encoding='utf-8'))
    data['en'] = EN
    data['zh'] = ZH
    need = [lg for lg in LANGS if not data.get(lg)]
    if need:
        import translator
        for lg in need:
            tr = translator.translate_lines([EN], lg.upper())
            v = (tr[0] or '').strip()
            if not v or v == EN.strip():
                raise SystemExit(f'\u26d4 {lg} 未取得译文（引擎回声），中止')
            data[lg] = v
            print(f'  {lg}: {v[:70]}\u2026')
        translator.flush()
        json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print(f'\u5df2\u5199\u5165 {os.path.relpath(DATA, ROOT)}')
    return data


STRIP = re.compile(r'[ \t]*' + re.escape(MARK_A) + r'.*?' + re.escape(MARK_B) + r'\n?', re.S)
ABODY = re.compile(r'<div class="article-body">\n')


def block(text, indent):
    return f'{indent}{MARK_A}\n{indent}<blockquote>{text}</blockquote>\n{indent}{MARK_B}\n'


def insert_into(segment, text):
    """把答案块插到 segment 里第一个 article-body 的开头；返回 (新段, 是否改动)"""
    m = ABODY.search(segment)
    if not m:
        return segment, False
    after = segment[m.end():]
    ind = re.match(r'[ \t]*', after).group(0) or '            '
    return segment[:m.end()] + block(text, ind) + after, True


def inject(src, data):
    """EN 页：分离 .lang-en / .lang-zh 两段分别插；语言版：整页插一处"""
    hit = [0]
    if '<div class="lang-zh">' in src:
        cut = src.index('<div class="lang-zh">')
        head, tail = src[:cut], src[cut:]
        head, c1 = insert_into(head, data['en'])
        tail, c2 = insert_into(tail, data['zh'])
        hit[0] = int(c1) + int(c2)
        src = head + tail
    else:
        # 语言版：内容语言由调用方决定，这里只插一次
        src, c = insert_into(src, data['_lang_text'])
        hit[0] = int(c)
    return src, hit[0]


def main():
    data = build_data('--retranslate' in sys.argv)
    n = words(EN)
    print(f'\nEN 答案块词数: {n}  (目标 134\u2013167)')
    if not (134 <= n <= 167):
        raise SystemExit('\u26d4 EN 词数不在 134\u2013167 区间')
    print(f'ZH 字符数: {len(ZH)}')

    issues = lint_translations(data)
    if issues:
        print('\n\u26a0\ufe0f  译文 lint 命中（需人工确认，确认无误后可从 data 里改掉再重跑）:')
        for lg, d in issues:
            print(f'   [{lg}] {d}')
    else:
        print('译文 lint: 无命中')

    targets = [(EN_PAGE, None)]
    for lg in LANGS:
        targets.append((f'{lg}/{EN_PAGE}', data[lg]))

    print()
    changed = []
    for rel, langtext in targets:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            print(f'  \u26a0 缺文件 {rel}')
            continue
        orig = open(p, encoding='utf-8').read()
        src = STRIP.sub('', orig) if MARK_A in orig else orig
        d = dict(data)
        d['_lang_text'] = langtext or data['en']
        out, k = inject(src, d)
        if CHECK:
            print(f'  {rel:52s} 答案块 {k} 处  已有标记={MARK_A in orig}')
            continue
        if out != orig:
            changed.append(rel)
            if APPLY:
                open(p, 'w', encoding='utf-8').write(out)
        print(f'  {rel:52s} 插入 {k} 处')

    print(f'\n模式: {"已写入" if APPLY else "试跑（加 --apply 才写入）"} | 改动 {len(changed)} 个文件')


if __name__ == '__main__':
    main()
