#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""GLM-5.3-flash vs DeepL 旧译文 A/B 对比（2026-10-02）。

背景：DeepL 双 key 额度耗尽，主翻译引擎已切换 GLM（translator.py 引擎链 GLM→DeepL→MyMemory）。
本脚本产出给用户过目的对比证据：

  Part A  族页抽样句对比 —— pilates/pilates-reformer.html 的 8 个锚定句
          （h1 + 首段 + 定制项 6 个 li），EN 源文 × 6 语言：
          线上 DeepL 旧译文（de/ja/ko/fr/it/es 族页已是旧体系翻译）vs GLM 新译文。
          对齐方式 = 锚点定位（Wagner / ワーグナー / 와그너… 跨语言存活的品牌专名），
          因为 EN 族页后来大改（138 块 vs 语言版 32 块），整页顺序对齐不可行。

  Part B  整页试跑 —— blog/pilates-reformer-buyers-guide.html 的 lang-en 正文
          全量行 × 6 语言走 translator.translate_lines 完整管道
          （缓存 → GLM → 行号锚定校验 → 失败回喂 → 降级链），
          记录请求数 / token / 估算成本 / 校验重试 / 降级次数。

输出：i18n_build/reports/glm_vs_deepl_ab_20261002.html
"""
import os
import re
import sys
import html as H

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import translator as T          # noqa: E402
import translator_glm as G      # noqa: E402

LANGS = ["de", "ja", "ko", "fr", "it", "es"]
REPORT = os.path.join(ROOT, "i18n_build", "reports", "glm_vs_deepl_ab_20261002.html")

# 每语言「弹簧 li」的锚点（品牌专名跨语言存活；ja/ko 为音译）
SPRING_ANCHOR = {
    "de": "Wagner", "fr": "Wagner", "it": "Wagner", "es": "Wagner",
    "ja": "ワーグナー", "ko": "바그너",
}


def vis(h):
    h = re.sub(r"<script[\s\S]*?</script>", " ", h)
    h = re.sub(r"<style[\s\S]*?</style>", " ", h)
    t = re.sub(r"<[^>]+>", " ", h)
    t = re.sub(r"\s+", " ", t).strip()
    for a, b in (("&amp;", "&"), ("&#39;", "'"), ("&quot;", '"'), ("&lt;", "<"), ("&gt;", ">")):
        t = t.replace(a, b)
    return t


def blocks(path, strip_zh=False):
    """</nav>..<footer> 之间的 h1/h2/h3/p/li 可见文本（有序）。"""
    s = open(path, encoding="utf-8").read()
    s = re.sub(r"<script[\s\S]*?</script>", " ", s)
    s = re.sub(r"<style[\s\S]*?</style>", " ", s)
    a, b = s.find("</nav>"), s.find("<footer")
    s = s[a:b]
    if strip_zh:
        s = re.sub(r'<span class="lang-zh">.*?</span>', " ", s, flags=re.S)
        s = s.replace('<span class="lang-en">', "<span>")
    out = []
    for m in re.finditer(r"<(h1|h2|h3|p|li)\b[^>]*>(.*?)</\1>", s, re.S):
        t = vis(m.group(2))
        if t:
            out.append((m.group(1), t))
    return out


def li_run(blks, anchor):
    """含 anchor 的 li（弹簧项，定制列表固定第 3 条）→ 窗口取整组 6 条。"""
    idx = [i for i, (tg, t) in enumerate(blks) if tg == "li" and anchor in t]
    if not idx:
        return []
    i = idx[0]
    window = blks[max(0, i - 2): i + 4]
    li = [t for tg, t in window if tg == "li"]
    return li if len(li) == 6 else []


def second_p_after_h1(blks):
    """h1 之后第 2 个 p（跳过 pl-alias 别名行）。"""
    for i, (tg, _) in enumerate(blks):
        if tg == "h1":
            ps = [t for tg2, t in blks[i + 1:] if tg2 == "p"]
            return ps[1] if len(ps) >= 2 else None
    return None


def blog_en_lines():
    """博客页 lang-en 容器内的正文字行（栈式配对 div，h2/h3/p/li ≥15 字符）。"""
    path = os.path.join(ROOT, "blog", "pilates-reformer-buyers-guide.html")
    s = open(path, encoding="utf-8").read()
    lines, pos = [], 0
    pat = re.compile(r'<div class="lang-en">')
    while m := pat.search(s, pos):
        # 栈式找配对 </div>
        depth, j = 1, m.end()
        tag = re.compile(r"<div\b|</div>")
        while depth:
            t = tag.search(s, j)
            depth += 1 if t.group(0) == "<div" else -1
            j = t.end()
        seg = s[m.end():j - 6]
        for mm in re.finditer(r"<(h2|h3|p|li)\b[^>]*>(.*?)</\1>", seg, re.S):
            t = vis(mm.group(2))
            if len(t) >= 15:
                lines.append(t)
        pos = j
    # 去重保序
    seen, out = set(), []
    for t in lines:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def strict_translate(lines, lang, tag):
    """A/B 专用：GLM 之外任何引擎接手 = 静默污染，当场报错而非带病出报告。"""
    s0 = dict(T.stats())
    out = T.translate_lines(lines, lang, verbose=False)
    s1 = T.stats()
    for k in ("deepl", "mymemory", "fail"):
        d = s1[k] - s0[k]
        assert d == 0, f"[{tag}/{lang}] {k} 接手 {d} 句 —— GLM 降级被守卫拦截，先修引擎再跑"
    assert all(x.strip() for x in out), f"[{tag}/{lang}] 有空译文"
    print(f"  [{tag}] {lang}: GLM {s1['glm'] - s0['glm']} 句 ✓", flush=True)
    return out


def main():
    # ---------- Part A: 抽取锚定对 ----------
    en_blks = blocks(os.path.join(ROOT, "pilates", "pilates-reformer.html"), strip_zh=True)
    p2 = second_p_after_h1(en_blks)
    en_li = li_run(en_blks, "Wagner")
    en_h1 = [t for tg, t in en_blks if tg == "h1"][0]
    assert len(en_li) == 6, f"EN 定制 li 应 6 条，得 {len(en_li)}"
    en_lines = [en_h1, p2] + en_li

    ref = {}   # ref[lang] = [h1, p2, li*6]（DeepL 旧译文）
    for lg in LANGS:
        blks = blocks(os.path.join(ROOT, lg, "pilates", "pilates-reformer.html"))
        h1 = [t for tg, t in blks if tg == "h1"][0]
        pp = second_p_after_h1(blks)
        li = li_run(blks, SPRING_ANCHOR[lg])
        assert len(li) == 6, f"{lg} 定制 li 应 6 条，得 {len(li)}"
        ref[lg] = [h1, pp] + li
    print(f"[A] 锚定对齐完成：{len(en_lines)} 句 × {len(LANGS)} 语言（DeepL 参照已就位）")

    # ---------- Part A: GLM 翻译 ----------
    labels = ["H1 主标题", "首段"] + [f"定制项 li{i+1}" for i in range(6)]
    glm = {}
    for lg in LANGS:
        glm[lg] = strict_translate(en_lines, lg, "A")
    print(f"[A] GLM 翻译完成：{len(LANGS)}×{len(en_lines)} 句 | stats={T.stats()}")

    # ---------- Part B: 整页试跑 ----------
    blines = blog_en_lines()
    print(f"[B] 博客整页正文行数 = {len(blines)}，合计 {sum(len(x) for x in blines):,} 字符")
    st0 = dict(T.stats())
    blog_out = {}
    for lg in LANGS:
        blog_out[lg] = strict_translate(blines, lg, "B")
    st = T.stats()
    print(f"[B] 整页 6 语言完成 | glm={st['glm'] - st0['glm']} deepl={st['deepl'] - st0['deepl']} "
          f"fail={st['fail'] - st0['fail']} retries={st.get('glm_retries', 0)} "
          f"fallbacks={st.get('glm_fallbacks', 0)}")

    # ---------- 成本核算 ----------
    u = dict(G.USAGE)
    pin, pout = 0.8 / 1e6, 2.8 / 1e6     # GLM-5.3-flash 官方价 ¥/token
    reasoning = u.get("reasoning_tokens", 0)
    cost_in = u.get("prompt_tokens", 0) * pin
    cost_out = (u.get("completion_tokens", 0)) * pout
    print(f"[¥] prompt={u.get('prompt_tokens', 0):,} completion={u.get('completion_tokens', 0):,} "
          f"(推理 {reasoning:,}) 估算 ¥{cost_in + cost_out:.3f}")

    # ---------- 渲染报告 ----------
    def esc(x):
        return H.escape(x, quote=False)

    rows = []
    for i, lab in enumerate(labels):
        trs = []
        for lg in LANGS:
            trs.append(
                f"<tr><td class='lang'>{lg}</td>"
                f"<td class='ref'>{esc(ref[lg][i])}</td>"
                f"<td class='glm'>{esc(glm[lg][i])}</td></tr>")
        rows.append(
            f"<section><h3>{esc(lab)}</h3>"
            f"<p class='src'><b>EN 源文：</b>{esc(en_lines[i])}</p>"
            f"<table><thead><tr><th>语</th><th>DeepL 旧译文（线上现行）</th>"
            f"<th>GLM-5.3-flash 新译文</th></tr></thead>"
            f"<tbody>{''.join(trs)}</tbody></table></section>")

    samples = []
    for lg in LANGS:
        pick = [3, 12, len(blines) // 2, len(blines) - 2]
        lis = "".join(
            f"<li><i>EN:</i> {esc(blines[k][:130])}…<br><b>{lg}:</b> {esc(blog_out[lg][k][:170])}</li>"
            for k in pick)
        samples.append(f"<div class='card'><h4>{lg}（4 条抽样）</h4><ul>{lis}</ul></div>")

    doc = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>GLM-5.3-flash vs DeepL 旧译文 A/B 对比</title><style>
body{{font:15px/1.75 -apple-system,'PingFang SC','Hiragino Sans GB',sans-serif;
margin:0;background:#f6f7f9;color:#1c2430}}
.wrap{{max-width:1120px;margin:0 auto;padding:32px 24px 64px}}
h1{{font-size:24px;margin:8px 0 4px}} h2{{font-size:19px;margin:44px 0 12px;
border-left:4px solid #2563eb;padding-left:10px}} h3{{font-size:16px;margin:26px 0 8px}}
.meta{{color:#5b6572;font-size:13px}} .src{{background:#eef3fb;border-radius:8px;
padding:10px 14px;font-size:14px}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;
box-shadow:0 1px 3px rgba(0,0,0,.07);font-size:14px}}
th,td{{border-bottom:1px solid #e8ecf1;padding:9px 12px;vertical-align:top;text-align:left}}
th{{background:#f0f3f7;font-size:13px}}
td.lang{{width:36px;font-weight:700;color:#2563eb;text-transform:uppercase}}
td.ref{{width:38%;color:#444}} td.glm{{color:#0b3d1c;background:#f4faf5}}
.stats{{display:flex;gap:14px;flex-wrap:wrap;margin:14px 0}}
.stats div{{background:#fff;border-radius:10px;padding:12px 18px;box-shadow:0 1px 3px rgba(0,0,0,.07)}}
.stats b{{display:block;font-size:22px}} .stats span{{color:#5b6572;font-size:12px}}
.card{{background:#fff;border-radius:10px;padding:14px 18px;margin:10px 0;
box-shadow:0 1px 3px rgba(0,0,0,.07);font-size:14px}} .card ul{{margin:6px 0;padding-left:18px}}
.card i{{color:#5b6572}} .card b{{color:#0b3d1c}}
.note{{background:#fff8e6;border-radius:8px;padding:10px 14px;font-size:13px;margin:12px 0}}
</style></head><body><div class="wrap">
<h1>GLM-5.3-flash vs DeepL 旧译文 —— A/B 对比</h1>
<p class="meta">fjsanfan.com 普拉提板块 · 2026-10-02 · 抽样页 = pilates/pilates-reformer.html
（6 语言版族页为 DeepL 旧译，仍在线上）· GLM 走与生产管道完全相同的 translate_lines
（行号锚定 + 完整性校验 + 术语表 system prompt）</p>
<div class="note">⚠️ DeepL 旧译文对的是<b>旧版族页</b>；EN 族页此后大改过，故整页无法逐句对齐，
本对比取两边都存在的 8 个锚定句（品牌专名 Wagner / ワーグナー 定位），逐句人工可核。</div>

<h2>A · 锚定句逐句对比（8 句 × 6 语言）</h2>
{''.join(rows)}

<h2>B · 整页试跑（pilates-reformer-buyers-guide 全文 × 6 语言）</h2>
<div class="stats">
<div><b>{len(blines)}</b><span>正文行数</span></div>
<div><b>{sum(len(x) for x in blines):,}</b><span>EN 源文字符</span></div>
<div><b>{st['glm'] - st0['glm']}</b><span>GLM 成功句数</span></div>
<div><b>{st['deepl'] - st0['deepl']}</b><span>降级 DeepL（应=0）</span></div>
<div><b>{st.get('glm_retries', 0)}</b><span>校验回喂重试</span></div>
<div><b>¥{cost_in + cost_out:.2f}</b><span>本轮估算成本</span></div>
</div>
<p class="meta">token：prompt {u.get('prompt_tokens', 0):,} · completion {u.get('completion_tokens', 0):,}
（其中推理 {reasoning:,}，glm-5.3-flash「始终思考」不可关）· 价格 ¥0.8/M 输入 + ¥2.8/M 输出</p>
{''.join(samples)}
</div></body></html>"""
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    open(REPORT, "w", encoding="utf-8").write(doc)
    print(f"\n报告已写: {REPORT}")


if __name__ == "__main__":
    main()
