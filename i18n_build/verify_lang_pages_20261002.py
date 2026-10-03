#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""语言版页面校验器（2026-10-02 新建，配合 build_pages.py 的 90 页生成）

四道判据（全部实测，不靠推断）：
  ① 标签配对：每个文件的开/闭标签计数必须相等（铁律 8：漏 </x> 会吞掉后续块）
  ② 英文残留：长文本节点里「像英文」的（≥3 个英文功能词 且 无目标语特征）→ 报出
     —— 判据沿用 translator_glm 的反向证据法（不要求像目标语，只测像不像英文）
  ③ 内链可达：href/src 指向站内的，逐条映射回本地文件；缺文件 = 线上 404 预告
  ④ 数字守恒：EN 源页里的数字 token 必须**全部**出现在语言版里（尺寸/箱规/重量不能被翻掉）

用法：
    python3 i18n_build/verify_lang_pages_20261002.py --batch /tmp/batch15.json --langs de,ja
    python3 i18n_build/verify_lang_pages_20261002.py --batch /tmp/batch15.json          # 6 语言
退出码：有问题 = 1（可直接当闸）。
"""
import os
import re
import sys
import json
import html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from translator_glm import _EN_MARK, _SIG_WEAK  # noqa: E402  与引擎共用同一份判据

TAG = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)((?:\"[^\"]*\"|'[^']*'|[^>\"'])*?)(/?)>", re.S)
VOID = {"img", "br", "hr", "input", "meta", "link", "source", "area", "base",
        "col", "embed", "param", "track", "wbr", "path", "circle", "rect"}
SIG = {"ja": re.compile(r"[\u3040-\u30ff]"), "ko": re.compile(r"[\uac00-\ud7af]")}
NUM = re.compile(r"\d{1,3}(?:[.,\u00a0\u202f ]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?")
CJK_MULT = {"万": 10 ** 4, "萬": 10 ** 4, "億": 10 ** 8, "亿": 10 ** 8,
            "만": 10 ** 4, "억": 10 ** 8}
# 英文量级缩写：200K / 1.2M / 3B
MAG = {"K": 10 ** 3, "M": 10 ** 6, "B": 10 ** 9}


def canon_nums(text):
    """把数字归一到「纯数字串」集合 —— ⭐ 必须 locale-aware。

    2026-10-03 实测教训：原实现用字面 token 比对，把**合法本地化**判成「数字丢失」
    （`de/about.html` 报 1,000,000 / 100,000 / 120,000 / 150,000 全丢，实际写成
    `1.000.000` —— 德/意用点、法/西用空格、日语直接换 `100万`）。
    同一事实四种写法，字面比对必然假警报；而假警报的工具＝没人信的工具。

    归一规则：
      ① 千分位分组（分隔符后**恰好 3 位数字**）整体吸收 —— `1,000,000` / `1.000.000` / `1 000 000` → `1000000`
         （必须要求「恰好 3 位」，否则 EN 的 `since 2013. 3 owned plants` 会跨句拼成假 token `20133`）
      ② CJK / 韩文计数单位换算 —— `100万`（中/日）、`100만`（韩）→ `1000000`
         ⚠️ 2026-10-03 补韩文：ko/faq.html 把 1,000,000 写成「100만」，此前漏了만
         → 误报「数字丢失 1000000」
      ③ 英文量级缩写 K/M/B —— `200K+` → `200000`，**同时保留原样 `200`**
         （缩写与全写必须能互认，否则 EN 的 `200K+` 会把德语页的 `200.000+`
          判成「丢了 200」——2026-10-03 实测 de/index.html 因此误报）
      ④ 其余非数字字符剔除；仅保留 ≥3 位（1–2 位是样式/层级噪声）
    """
    text = re.sub(r"&#x?[0-9a-fA-F]+;", " ", text)
    out = set()
    for m in NUM.finditer(text):
        tok = m.group(0)
        mult = CJK_MULT.get(text[m.end():m.end() + 1])
        digits = re.sub(r"\D", "", tok)
        if not digits:
            continue
        if mult:
            out.add(str(int(digits) * mult))
            continue
        mm = re.match(r"\s*([KkMmBb])(?![A-Za-z])", text[m.end():])
        if mm:
            out.add(digits)                    # 原样保留，缩写 ↔ 全写互认
            try:
                out.add(str(int(float(tok.replace(",", "")) * MAG[mm.group(1).upper()])))
            except ValueError:
                pass
            continue
        if len(digits) >= 3:
            out.add(digits)
    return out


def text_nodes(h):
    h = re.sub(r"<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>|<!--.*?-->",
               " ", h, flags=re.S)
    segs = re.split(r"<[^>]+>", h)
    out = []
    for s in segs:
        t = H.unescape(s).strip()
        if len(t) >= 40:
            out.append(t)
    return out


def check_tag_balance(path):
    h = open(path, encoding="utf-8").read()
    h = re.sub(r"<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>|<!--.*?-->",
               " ", h, flags=re.S)
    open_c, close_c = {}, {}
    for m in TAG.finditer(h):
        name = m.group(2).lower()
        if name in VOID:
            continue
        (close_c if m.group(1) else open_c)[name] = \
            (close_c if m.group(1) else open_c).get(name, 0) + 1
    bad = []
    for name in set(open_c) | set(close_c):
        if open_c.get(name, 0) != close_c.get(name, 0):
            bad.append("%s<%d</%d" % (name, open_c.get(name, 0), close_c.get(name, 0)))
    return bad


def check_english(path, lang):
    """长文本节点里「像英文」的条目。

    判据与引擎同源（铁律 35：反向证据法）——不要求「像目标语」，只测「像英文」：
      英文功能词（_EN_MARK）命中 ≥3 且密度 ≥12%，同时**没有**目标语特征（_SIG_WEAK /
      日韩字符集）→ 判为疑似未翻。品牌句/型号两向皆无 → 放行。
    """
    h = open(path, encoding="utf-8").read()
    sig_re = SIG.get(lang) or _SIG_WEAK.get(lang)
    bad = []
    for t in text_nodes(h):
        words = re.findall(r"[A-Za-z']+", t)
        if len(words) < 6:
            continue
        marks = len(_EN_MARK.findall(t))
        has_sig = bool(sig_re.search(t)) if sig_re else False
        if marks >= 3 and marks / len(words) >= 0.12 and not has_sig:
            bad.append(t[:110])
    return bad


LINK = re.compile(r'(?:href|src)="([^"]+)"')


def check_links(path):
    """站内链接映射回本地文件；返回缺失清单。"""
    h = open(path, encoding="utf-8").read()
    rel_dir = os.path.dirname(path)
    miss = []
    for raw in LINK.findall(h):
        u = raw.split("#")[0].split("?")[0]
        if not u or u.startswith(("http", "//", "mailto:", "tel:", "data:", "javascript:")):
            continue
        if u.startswith("/"):
            cand = os.path.join(ROOT, u.lstrip("/"))
        else:
            cand = os.path.normpath(os.path.join(rel_dir, u))
        if u.endswith("/") or os.path.isdir(cand):
            cand = os.path.join(cand, "index.html")
        if not os.path.isfile(cand):
            miss.append((raw, os.path.relpath(cand, ROOT)))
    return miss


def _clean_for_numbers(path):
    """取数字前先洗掉四类噪声（否则误报）：
    ① script/style/注释 —— 生成器会整块重写，不是内容
    ② HTML 实体 `&#9662;`（切换器 ▾）—— 该块被生成器有意丢弃（fix_site 重新注入）
    ③ 十六进制实体
    ④ **HTML 标签本身**（2026-10-03 补）—— 只剩正文文本。
       为什么必须剥：属性里的数字全是噪声，且各语言页的文件名/属性天然不同：
       `hero-1.webp`、`width="500"`、`data-i18n="hero.stat1.n"` …
       实测 EN 首页因此凭空多出数字 `1`（来自图片名与 `width="1"`），
       而语言页的图片名不一样 → 误报「数字丢失 1」。
       判据要的是「**客户能看到的正文数字**不能被翻译丢掉」，属性不属于正文。
    """
    h = open(path, encoding="utf-8").read()
    h = re.sub(r"<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>|<!--.*?-->",
               " ", h, flags=re.S)
    h = re.sub(r"&#x?[0-9a-fA-F]+;", " ", h)
    h = re.sub(r"<[^>]+>", " ", h)          # ← 只保留正文文本
    return h


def check_numbers(src, out):
    """EN 源页数字集合必须被语言版覆盖（数字被翻译/丢弃 = 事实错误）。

    比对用 canon_nums 归一后的集合（locale-aware，见 canon_nums 的注释）。
    """
    return sorted(canon_nums(_clean_for_numbers(src)) - canon_nums(_clean_for_numbers(out)))


def check_ld(path, lang):
    """JSON-LD 里的英文残留：name/description/headline 等可翻字段不该是长英文句。

    为什么要单列：正文翻了、schema 没翻 = 搜索结果里显示英文摘要，是实打实的缺陷；
    而这一块不在 <body> 的文本节点里，逐文本节点的判据覆盖不到。
    """
    import json as _json
    h = open(path, encoding="utf-8").read()
    sig_re = SIG.get(lang) or _SIG_WEAK.get(lang)
    bad = []
    for m in re.finditer(r'<script\s+type="application/ld\+json"[^>]*>(.*?)</script>',
                         h, flags=re.S):
        try:
            obj = _json.loads(m.group(1))
        except Exception:
            bad.append("(JSON-LD 解析失败)")
            continue

        def walk(o, parent=None):
            if isinstance(o, dict):
                for k, v in o.items():
                    if isinstance(v, str) and k in ("name", "description", "headline",
                                                    "abstract", "text", "caption"):
                        words = re.findall(r"[A-Za-z']+", v)
                        if len(words) >= 8:
                            marks = len(_EN_MARK.findall(v))
                            has = bool(sig_re.search(v)) if sig_re else False
                            if marks >= 3 and marks / len(words) >= 0.12 and not has:
                                bad.append("%s: %s" % (k, v[:90]))
                    elif isinstance(v, (dict, list)):
                        walk(v, k)
            elif isinstance(o, list):
                for x in o:
                    walk(x, parent)
        walk(obj)
    return bad


def discover(langs):
    """⭐ 自发现应校验页面：语言目录下所有「存在 EN 同名源页」的 html。

    为什么必须自发现（2026-10-03 血的教训）：原实现只在给了 `--batch` 时才有清单，
    不传参 → pages=[] → 打印「校验 0 页」却给出「结论：全部通过」。
    这是**静默通过**，比误报危险得多（符合铁律：白名单外/空集必须报错，不能 continue）。
    现在默认自发现，空集直接退出码 3 拒绝判定。
    """
    jobs = []
    for lang in langs:
        base = os.path.join(ROOT, lang)
        if not os.path.isdir(base):
            continue
        for dp, _dn, fn in os.walk(base):
            for f in sorted(fn):
                if not f.endswith(".html"):
                    continue
                abs_p = os.path.join(dp, f)
                en_rel = os.path.relpath(abs_p, base)      # 语言目录内的相对路径
                if os.path.isfile(os.path.join(ROOT, en_rel)):
                    jobs.append((lang, en_rel))
    return jobs


def main():
    batch = None
    langs = LANGS
    limit = None
    a = sys.argv[1:]
    for i, x in enumerate(a):
        if x == "--batch":
            batch = json.load(open(a[i + 1], encoding="utf-8"))["pages"]
        if x == "--langs":
            langs = a[i + 1].split(",")
        if x == "--limit":
            limit = int(a[i + 1])
    if batch:
        jobs = [(lang, p) for lang in langs for p in batch]
        src = "batch 清单 %d 页 × %d 语言" % (len(batch), len(langs))
    else:
        jobs = discover(langs)
        src = "自发现（%d 语言 × 有 EN 同源页）" % len(langs)
    print("页面来源：%s" % src)
    if not jobs:
        print("✗ 未发现任何待校验页面 —— 拒绝判定为通过（退出码 3）")
        return 3
    print("校验 %d 个页面版本（%s）" % (len(jobs), src))
    bad_total = 0
    bad_list = []
    results = []
    for lang, p in (jobs[:limit] if limit else jobs):
        if True:
            out_rel = "%s/%s" % (lang, p)
            out_abs = os.path.join(ROOT, out_rel)
            if not os.path.isfile(out_abs):
                print("  ✗ %s 缺失" % out_rel)
                bad_total += 1
                continue
            problems = []
            tb = check_tag_balance(out_abs)
            if tb:
                problems.append("标签不配对: %s" % ", ".join(tb[:6]))
            en = check_english(out_abs, lang)
            if en:
                problems.append("疑似英文残留 %d 条: %s" % (len(en), " | ".join(en[:2])))
            ms = check_links(out_abs)
            if ms:
                problems.append("内链缺失 %d: %s" % (len(ms), ", ".join(x[1] for x in ms[:3])))
            num = check_numbers(os.path.join(ROOT, p), out_abs)
            if num:
                problems.append("数字丢失: %s" % ", ".join(num[:8]))
            ld = check_ld(out_abs, lang)
            if ld:
                problems.append("JSON-LD 英文残留 %d: %s" % (len(ld), " | ".join(ld[:2])))
            zh = open(out_abs, encoding="utf-8").read().count('class="lang-zh"')
            if zh:
                problems.append("残留 lang-zh 块 %d 处" % zh)
            if problems:
                bad_total += 1
                bad_list.append((out_rel, problems))
                results.append((out_rel, problems))
                if len(jobs) <= 200:
                    print("  ✗ %s" % out_rel)
                    for x in problems:
                        print("      - %s" % x)
            else:
                results.append((out_rel, []))
                if len(jobs) <= 200:
                    print("  ✓ %s" % out_rel)
    if len(jobs) > 200:
        print("\n—— 问题明细（共 %d 页）——" % bad_total)
        for rel, problems in bad_list[:60]:
            print("  ✗ %s" % rel)
            for x in problems:
                print("      - %s" % x)
        if len(bad_list) > 60:
            print("  ... 另有 %d 页，见报告文件" % (len(bad_list) - 60))
    # 分类小结：按目录（便于区分「本推送涉及」与「存量」）
    from collections import Counter
    cb = Counter()
    for rel, _ in bad_list:
        parts = rel.split("/")
        cb["/".join(parts[:2]) if len(parts) >= 2 else rel] += 1
    if cb:
        print("\n问题分布：" + "  ".join("%s=%d" % (k, v) for k, v in cb.most_common(10)))
    print("\n结论：%s（校验 %d 页，问题页面 %d 个）"
          % ("全部通过" if bad_total == 0 else "有问题", len(jobs), bad_total))
    return 1 if bad_total else 0


if __name__ == "__main__":
    sys.exit(main())
