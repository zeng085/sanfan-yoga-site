# -*- coding: utf-8 -*-
"""fix_desc_unique.py —— 消灭重复 / 过长的 meta description（2026-09-12）

背景：深度体检发现 125 组、362 个页面共用同一段 description。
原因是同族产品（6 款麂皮垫、3 款筋膜枪…）用的是「族级兜底描述」，
英文站空壳页没有差异化数据，所以整族一模一样 → Google 会判近似重复。

修法：**把各页自己的产品名（h1）前置**，让每段描述天然唯一，
同时把超长的裁到 ≤158 字符（SERP 不会被截断）。og/twitter 三处同步改。

    de/products/fascia-gun-1.html
    旧: Akku-Perkussionsmassagegerät, speziell auf Ihre Größe zugeschnitten…
    新: Fascia Gun (T-Form): Akku-Perkussionsmassagegerät, speziell auf Ihre…

⚠️ 只改「重复组」和「>165 字符」的页面，写得好的描述不动。
⚠️ 拼接前先 unescape 再 escape，否则产品名里的 & 会破坏 HTML 属性。
⚠️ 三个 meta 只在 content 与旧 desc **完全相同**时才替换（避免误改 og 特有文案）。

用法：
    python3 i18n_build/fix_desc_unique.py --dry      # 预演，打印样例
    python3 i18n_build/fix_desc_unique.py            # 落盘
"""
import argparse
import collections
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
MAXLEN = 160          # 目标上限（Google 桌面 ~155-160 字符）
TOOLONG = 165         # 超过这个长度才处理（非重复页只做温和截断）
NAME_MAX = 70         # h1 超过这个长度就是口号不是产品名，不前置
                      # ⚠️ 别调小：德语/西语产品名 45~60 字符很常见，按 45 截会切出
                      #    "…rutschfeste:" / "…aus Gummi mit:" 这种缺半个形容词的前缀。
                      #    产品名长就让描述正文给它让位（fit 会截正文），不要截产品名。
META_RE = re.compile(r"<meta\b[^>]*>", re.I)
CONT_RE = re.compile(r'content="([^"]*)"')
H1_RE = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.S | re.I)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.S | re.I)
BRAND_TAIL = re.compile(r"\s*[—–\-|:]\s*SANFAN.*$", re.I)
CJK_RE = re.compile(r"[\u3000-\u303f\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"
                    r"\u3040-\u30ff\uac00-\ud7af]+")


def _squash(s):
    return re.sub(r"\s+", "", s)


def walk_html():
    out = []
    for dp, dns, fs in os.walk(ROOT):
        rel = os.path.relpath(dp, ROOT)
        if rel == ".":
            rel = ""
        if any(s in rel for s in (".git", "node_modules", "outputs", ".workbuddy", "i18n_build")):
            dns[:] = []
            continue
        for f in fs:
            if f.endswith(".html"):
                out.append(os.path.join(rel, f).replace(os.sep, "/").lstrip("/"))
    return sorted(out)


def meta_get(h, key):
    """按 name/property 精确取 content（属性顺序不敏感）。"""
    for tag in META_RE.findall(h):
        if re.search(r'(?:name|property)=["\']%s["\']' % re.escape(key), tag, re.I):
            m = CONT_RE.search(tag)
            if m:
                return m.group(1)
    return None


def lang_of(rel):
    return rel.split("/")[0] if rel.split("/")[0] in LANGS else "en"


def replace_meta(h, key, old_txt, new_esc):
    """替换指定 meta 的 content。
    ⚠️ 属性顺序不固定：英文站是 <meta name="description" content="…">，
       语言站是 <meta content="…" name="description"/>。
       用「先抓整个 <meta> 标签、再在标签内改 content」的写法，别写
       `name="x"[^>]*content="…"` 这种顺序敏感的正则 —— 那会静默漏掉一半页面。"""
    out = h
    for tag in META_RE.findall(h):
        if not re.search(r'(?:name|property)=["\']%s["\']' % re.escape(key), tag, re.I):
            continue
        m = CONT_RE.search(tag)
        if not m or html.unescape(m.group(1)) != old_txt:
            continue
        newtag = tag[: m.start(1)] + new_esc + tag[m.end(1):]
        out = out.replace(tag, newtag, 1)
    return out


def _clean(t):
    """去标签 → 去实体 → 剥中文（双语 h1 里的中文不能进西文描述）→ 去品牌尾巴。
    ⚠️ 剥 CJK 前必须先看剩不剩得下东西：日语 h1 是**纯假名+汉字**，
       一把全剥就剩空串 → 产品名取不到 → 日语页整页跳过、描述继续重复。
       所以「剥完太短」就当它是 CJK 单语页，原样保留。"""
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = " ".join(t.split())
    # ⚠️ 必须先砍品牌尾巴再判断 CJK 占比：带着 "— SANFAN" 一起算，
    #    「グレー…「PU」…ヨガマット — SANFAN」剥完还剩 "PU — SANFAN" 11 字符，
    #    会误判成「西文产品名够长」，砍完品牌就只剩材质缩写 "PU"。
    t = BRAND_TAIL.sub("", t).strip(" —–-|·")
    # 判据看**占比**：日语 h1 剥掉假名汉字只剩材质缩写 "PU"（2 字），
    # 拿它当产品名会拼出 "PU：PU 天然ゴム製…"。剥完仍占 45% 以上（或 ≥10 字符）
    # 才算西文产品名，否则整串保留。
    stripped = " ".join(CJK_RE.sub("", t).split())
    if len(stripped) >= 10 or len(stripped) >= 0.45 * len(t):
        t = stripped
    return t
    # 双语 h1 里中文被剥掉后，**右引号**会直接贴上后面的西文（„Alignment Line“TPE-Yogamatte）。
    # ⚠️ 只补右引号（“ 和 "）：德语 „ 是**左**引号，紧贴后面的词才是正确写法，
    #    给它补空格会变成 „ TPE“ —— 既难看，又会让下面的 startswith 判断失配而重复加前缀。
    t = re.sub(r'(["“])(?=[A-Za-z0-9])', r"\1 ", t)
    t = re.sub(r'„\s+', "„", t)
    t = " ".join(t.split())
    return BRAND_TAIL.sub("", t).strip(" —–-|·")


def product_name(h):
    """产品名：优先 h1 里的 .lang-en（双语页），否则整个 h1；都拿不到就退回 title。
    ⚠️ 太长（>NAME_MAX）说明是口号型 h1（如场景页「按用途采购，而不是按规格表」），
       拿它当前缀会把描述变成一句口号，直接返回空让调用方跳过。"""
    m = H1_RE.search(h)
    if m:
        spans = re.findall(r'<span class="lang-en">(.*?)</span>', m.group(1), re.S)
        t = _clean(spans[0]) if spans else _clean(m.group(1))
        if t:
            return shorten(t)
    mt = TITLE_RE.search(h)
    if mt:
        t = _clean(mt.group(1).split("—")[0].split("–")[0].split("|")[0])
        return shorten(t)
    return ""


def shorten(t):
    """h1 太长（西/意语产品名 50+ 字符很常见）时按词边界截断，别整页放弃 ——
    放弃的后果就是这个页面继续和同族共用描述，去重做不干净。"""
    if len(t) <= NAME_MAX:
        return t
    cut = t[:NAME_MAX]
    sp = cut.rfind(" ")
    if sp > NAME_MAX * 0.5:
        cut = cut[:sp]
    # 截断面不能停在半个引号/破折号上（"rutschfeste „:" 这种）
    cut = re.sub(r'[\s,;:·\-—–„“"]+$', "", cut)
    return cut


def fit(s, maxlen):
    """截到 maxlen：西文按最后一个空格断词，CJK/无空格直接按字符截。
    不加省略号 —— Google 自己会在 SERP 上加，加了反而占字符。"""
    if len(s) <= maxlen:
        return s
    cut = s[:maxlen]
    sp = cut.rfind(" ")
    if sp > maxlen * 0.55:
        cut = cut[:sp]
    return cut.rstrip(" ,;:·-—–")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    pages = walk_html()
    descs = collections.defaultdict(list)
    raw = {}
    for rel in pages:
        h = open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace").read()
        raw[rel] = h
        d = meta_get(h, "description")
        if d:
            descs[d].append(rel)
    dup_pages = set()
    for d, rs in descs.items():
        if len(rs) > 1:
            dup_pages |= set(rs)
    print("页面 %d；重复描述组 %d，涉及 %d 页"
          % (len(pages), sum(1 for v in descs.values() if len(v) > 1), len(dup_pages)))

    changed = 0
    samples = []
    for rel in pages:
        h = raw[rel]
        old = meta_get(h, "description")
        if not old:
            continue
        old_txt = html.unescape(old)
        lg = lang_of(rel)
        # CJK 单字信息量≈西文 2~3 字符，阈值按语言折算（日语 30 字 ≈ 西文 70 字）
        minlen = 30 if lg in ("ja", "ko") else 55
        if rel in dup_pages or len(old_txt) < minlen:
            # ① 重复组 / 太单薄：前置本页产品名，既唯一又补足长度
            name = product_name(h)
            # 用「去掉所有空白」的形式比较：页面里的 „TPE“ 与 _clean 后的 „ TPE“
            # 只是空格差异，直接 startswith 会失配 → 前缀被加第二次。
            if not name or _squash(old_txt).startswith(_squash(name)):
                continue
            sep = "：" if lg in ("ja", "ko") else ": "
            new = fit(name + sep + old_txt, MAXLEN)
        elif len(old_txt) > TOOLONG:
            # ② 只是太长：温和处理，只截到 160，不动结构与信息
            new = fit(old_txt, 160)
            if len(new) >= len(old_txt):
                continue
        else:
            continue
        if new == old_txt:
            continue
        new_esc = html.escape(new, quote=True)
        nh = h
        for key in ("description", "og:description", "twitter:description"):
            nh = replace_meta(nh, key, old_txt, new_esc)
        if nh == h:
            add_fail = True
            continue
        if len(samples) < 8 and (rel.startswith("ja/") or rel.startswith("ko/") or len(samples) < 3):
            samples.append((rel, old_txt, new))
        if not args.dry:
            with open(os.path.join(ROOT, rel), "w", encoding="utf-8") as fh:
                fh.write(nh)
        changed += 1
        if args.limit and changed >= args.limit:
            break

    for rel, o, n in samples:
        print("\n--- %s" % rel)
        print("  旧(%d): %s" % (len(o), o[:110]))
        print("  新(%d): %s" % (len(n), n[:110]))
    print("\n%s %d 个页面" % ("预演将改" if args.dry else "已写入", changed))


if __name__ == "__main__":
    main()
