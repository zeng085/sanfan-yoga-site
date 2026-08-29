#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
零 API 修复缓存中的占位符残留：
缓存里存的是翻译引擎原始输出（旧版 restore 还原失败、占位符留在了里面）。
protect() 是纯函数，可由源文本确定性重建映射，因此可以对缓存值重放新的 restore。
"""
import os, re, sys, json, html as H
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import translator as T
import build_pages as B

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLACEHOLDER_HINT = re.compile(r"ZX\s*Q?\s*T?\s*M?\s*\d+\s*Q?\s*X?\s*Z?", re.I)


def collect_srcs(rel_path, lang):
    """复现生成流程，收集所有被翻译的英文源文本"""
    h = open(os.path.join(ROOT, rel_path), encoding="utf-8").read()
    h = B.strip_lang_zh(h)
    h = B.relax_lang_en(h)
    h = B.remove_i18n_attrs(h)
    h, segs, texts, ph, lds = B.collect_texts(h)
    srcs = [H.unescape(t[1].strip()) for t in texts]

    def _c(m):
        for am in B.ATTR_RE.finditer(m.group(0)):
            k, v = am.group(1).lower(), am.group(2)
            if k in B.TRANS_ATTRS and len(v) > 2:
                raw = v[1:-1] if v[0] in "\"'" else v
                if re.search(r"[A-Za-z]", H.unescape(raw)):
                    srcs.append(H.unescape(raw))
        return m.group(0)

    B.TAG_RE.sub(_c, h)

    def _m(m):
        tag = m.group(0)
        nm = re.search(r'(?:name|property)\s*=\s*"?([^"\'\s>]+)"?', tag)
        key = nm.group(1) if nm else ""
        if key in B.TRANS_META:
            cm = re.search(r'content\s*=\s*"([^"]*)"', tag)
            if cm and re.search(r"[A-Za-z]", H.unescape(cm.group(1))):
                srcs.append(H.unescape(cm.group(1)))
        return tag

    re.sub(r"<meta\b[^>]*>", _m, h, flags=re.I)
    tm = re.search(r"<title>(.*?)</title>", h, re.S)
    if tm:
        srcs.append(H.unescape(tm.group(1)))

    # JSON-LD 中被翻译的字符串字段
    def walk(o, parent=None):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, str) and k in B.LD_KEYS and parent not in B.LD_SKIP_PARENTS:
                    srcs.append(v)
                elif isinstance(v, (dict, list)):
                    walk(v, k)
        elif isinstance(o, list):
            for x in o:
                walk(x, parent)

    for _, obj in lds:
        walk(obj)
    return srcs


def main(langs):
    fixed = total = 0
    per_lang = {}
    for lang in langs:
        srcs = []
        for p in B.PAGES:
            fp = os.path.join(ROOT, p)
            if os.path.exists(fp):
                srcs += collect_srcs(p, lang)
        srcs = list(dict.fromkeys([s for s in srcs if s and s.strip()]))
        cnt = 0
        for s in srcs:
            ck = T._ck(s, lang)
            cur = T._cache.get(ck)
            if not cur or not PLACEHOLDER_HINT.search(cur):
                continue
            _, mapping = T.protect(s, lang)
            new = T.restore(cur, mapping)
            if new != cur:
                T._cache[ck] = new
                cnt += 1
            total += 1
        fixed += cnt
        per_lang[lang] = cnt
        print("%s: 待修复 %d 条，成功修复 %d 条" % (lang, total, cnt))
    T.flush()
    print("共修复 %d 条缓存译文（零 API 消耗）" % fixed)


if __name__ == "__main__":
    main(sys.argv[1:] or ["de", "ja", "ko"])
