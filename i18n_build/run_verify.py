#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SANFAN 翻译质量验证执行器
对已生成的 de/ja/ko 页面做多维度正确性校验，输出控制台摘要 + JSON + Markdown 报告
"""
import os, re, sys, json, html as H, random, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import translator as T
import verify as V
import build_pages as B

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["de", "ja", "ko"]
REPORT_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_report.json")
REPORT_MD = os.path.join(ROOT, "三梵多语言翻译质量验证报告.md")

# 抽样规模（控制 API 消耗）
DIM1_SAMPLE = 110      # 回译抽样条数 / 语言
DIM4_SAMPLE = 25       # 交叉一致性抽样 / 语言


def extract_pairs(rel_path, lang):
    """复现生成流程，取出 (英文原文, 译文) 配对 —— 全部命中缓存，零新增翻译开销"""
    h = open(os.path.join(ROOT, rel_path), encoding="utf-8").read()
    h = B.strip_lang_zh(h)
    h = B.relax_lang_en(h)
    h = B.remove_i18n_attrs(h)
    h, segs, texts, ph, lds = B.collect_texts(h)

    pairs = []
    plain = [H.unescape(t[1].strip()) for t in texts]
    trans = T.translate_lines(plain, lang)
    pairs += list(zip(plain, trans))

    # 属性
    attr_vals = []

    def _c(m):
        for am in B.ATTR_RE.finditer(m.group(0)):
            k, v = am.group(1).lower(), am.group(2)
            if k in B.TRANS_ATTRS and len(v) > 2:
                raw = v[1:-1] if v[0] in "\"'" else v
                if re.search(r"[A-Za-z]", H.unescape(raw)):
                    attr_vals.append(H.unescape(raw))
        return m.group(0)

    B.TAG_RE.sub(_c, h)
    if attr_vals:
        uniq = list(dict.fromkeys(attr_vals))
        tr = T.translate_lines(uniq, lang)
        pairs += list(zip(uniq, tr))

    # meta / title
    metas = []

    def _m(m):
        tag = m.group(0)
        nm = re.search(r'(?:name|property)\s*=\s*"?([^"\'\s>]+)"?', tag)
        key = nm.group(1) if nm else ""
        if key in B.TRANS_META:
            cm = re.search(r'content\s*=\s*"([^"]*)"', tag)
            if cm and re.search(r"[A-Za-z]", H.unescape(cm.group(1))):
                metas.append(H.unescape(cm.group(1)))
        return tag

    re.sub(r"<meta\b[^>]*>", _m, h, flags=re.I)
    tm = re.search(r"<title>(.*?)</title>", h, re.S)
    if tm:
        metas.append(H.unescape(tm.group(1)))
    if metas:
        uniq = list(dict.fromkeys(metas))
        tr = T.translate_lines(uniq, lang)
        pairs += list(zip(uniq, tr))

    # 去重（同一原文只验一次）
    seen, out = set(), []
    for s, d in pairs:
        if not s or not s.strip() or s in seen:
            continue
        seen.add(s)
        out.append((s, d))
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    offline = "--local" in sys.argv      # 跳过需要翻译 API 的维度（配额耗尽/离线时用）
    only = args or LANGS
    langs = [l for l in LANGS if l in only]
    report = {"generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "langs": {}}

    for lang in langs:
        print("\n" + "=" * 62)
        print("  语言: %s" % lang.upper())
        print("=" * 62)
        pairs = []
        for p in B.PAGES:
            fp = os.path.join(ROOT, lang, p)
            if not os.path.exists(fp):
                print("  !! 缺页 %s，跳过" % fp)
                continue
            try:
                pr = extract_pairs(p, lang)
                pairs += pr
                print("  %-24s 提取 %d 条" % (p, len(pr)))
            except Exception as e:
                print("  !! %s -> %s" % (p, e))

        # ---------- DIM-2 术语与结构（全量，本地）
        d2_bad = []
        for s, d in pairs:
            ok, iss = V.dim2_terms_structure(s, d, lang)
            if not ok:
                d2_bad.append((s, d, iss))
        # ---------- DIM-3 语言与长度（全量，本地）
        d3_bad = []
        for s, d in pairs:
            ok, iss = V.dim3_language(s, d, lang)
            if not ok:
                d3_bad.append((s, d, iss))

        print("\n  [DIM-2 术语锁定/结构完整性] 检查 %d 条 -> 异常 %d 条 (%.1f%%)"
              % (len(pairs), len(d2_bad), 100.0 * len(d2_bad) / max(1, len(pairs))))
        for s, d, iss in d2_bad[:6]:
            print("     - %s\n       %s\n       %s" % (iss, s[:70], d[:70]))
        print("  [DIM-3 语言正确性/长度比] 检查 %d 条 -> 异常 %d 条 (%.1f%%)"
              % (len(pairs), len(d3_bad), 100.0 * len(d3_bad) / max(1, len(pairs))))
        for s, d, iss in d3_bad[:6]:
            print("     - %s\n       %s\n       %s" % (iss, s[:70], d[:70]))

        # ---------- DIM-1 回译（抽样，需翻译 API）
        d1, d1_bad, avg = [], [], 0.0
        if not offline:
            cand = [(s, d) for s, d in pairs if len(V._toks(s)) >= 3]
            random.Random(7).shuffle(cand)
            sample = cand[:DIM1_SAMPLE]
            try:
                d1 = V.dim1_backtranslate(sample, lang)
            except Exception as e:
                print("  !! DIM-1 回译不可用: %s" % str(e)[:80])
            d1_bad = [x for x in d1 if not x[4]]
            avg = sum(x[3] for x in d1) / max(1, len(d1))
            print("\n  [DIM-1 回译语义一致性] 抽样 %d 条 -> 平均相似度 %.3f，低于阈值 %d 条 (%.1f%%)"
                  % (len(d1), avg, len(d1_bad), 100.0 * len(d1_bad) / max(1, len(d1))))
            for s, d, bk, sc, ok, thr in d1_bad[:6]:
                print("     - score=%.3f(阈值%.2f)" % (sc, thr))
                print("       EN  : %s" % s[:90])
                print("       %s : %s" % (lang.upper(), d[:90]))
                print("       回译: %s" % bk[:90])
        else:
            print("\n  [DIM-1 回译语义一致性] --local 模式跳过（需翻译 API 配额）")

        # ---------- DIM-4 批量 vs 单条 交叉（抽样，需翻译 API）
        d4, d4_bad, avg4 = [], [], 0.0
        if not offline:
            try:
                d4 = V.dim4_crosscheck(pairs, lang, sample=0.0, min_n=DIM4_SAMPLE, max_n=DIM4_SAMPLE)
            except Exception as e:
                print("  !! DIM-4 交叉校验不可用: %s" % str(e)[:80])
            d4_bad = [x for x in d4 if not x[4]]
            avg4 = sum(x[3] for x in d4) / max(1, len(d4))
            print("\n  [DIM-4 批量vs单条 交叉一致性] 抽样 %d 条 -> 平均一致度 %.3f，异常 %d 条 (%.1f%%)"
                  % (len(d4), avg4, len(d4_bad), 100.0 * len(d4_bad) / max(1, len(d4))))
            for s, b_, si, f, ok in d4_bad[:4]:
                print("     - 一致度=%.3f\n       EN: %s\n       批量: %s\n       单条: %s"
                      % (f, s[:80], b_[:80], si[:80]))
        else:
            print("  [DIM-4 批量vs单条 交叉一致性] --local 模式跳过（需翻译 API 配额）")

        report["langs"][lang] = {
            "pairs_total": len(pairs),
            "dim2": {"checked": len(pairs), "bad": len(d2_bad),
                     "samples": [{"src": s[:160], "dst": d[:160], "issues": i} for s, d, i in d2_bad[:20]]},
            "dim3": {"checked": len(pairs), "bad": len(d3_bad),
                     "samples": [{"src": s[:160], "dst": d[:160], "issues": i} for s, d, i in d3_bad[:20]]},
            "dim1": {"checked": len(d1), "avg_score": round(avg, 4), "bad": len(d1_bad),
                     "samples": [{"src": s[:160], "dst": d[:160], "back": bk[:160],
                                  "score": sc, "threshold": thr}
                                 for s, d, bk, sc, ok, thr in d1_bad[:20]]},
            "dim4": {"checked": len(d4), "avg_score": round(avg4, 4), "bad": len(d4_bad),
                     "samples": [{"src": s[:160], "batch": b_[:160], "single": si[:160], "score": f}
                                 for s, b_, si, f, ok in d4_bad[:20]]},
        }
        T.flush()

    json.dump(report, open(REPORT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    write_md(report)
    print("\n报告: %s" % REPORT_MD)
    return report


def write_md(r):
    L = {"de": "德语 DE", "ja": "日语 JA", "ko": "韩语 KO"}
    offline_any = any(d["dim1"]["checked"] == 0 for d in r["langs"].values())
    lines = ["# 三梵独立站 · 多语言翻译质量验证报告", "",
             "生成时间：%s" % r["generated_at"], "",
             "翻译引擎：MyMemory Public Translation API（本机环境唯一稳定可达的公开翻译 API）", ""]
    if offline_any:
        lines += ["> ⚠️ 本次为 `--local` 模式：DIM-1 回译与 DIM-4 交叉校验需要调用翻译 API，"
                  "因 MyMemory 免费配额当日耗尽而跳过；DIM-2 与 DIM-3 为**全量本地校验**，结果不受影响。"
                  "配额恢复后重跑（不带 `--local`）即可补齐另两个维度。", ""]
    lines += ["## 验证方法（4 个独立维度）", "",
             "| 维度 | 方法 | 检测什么 | 是否需要网络 |",
             "|---|---|---|---|",
             "| DIM-1 回译语义一致性 | 译文 → 回翻英文 → 与原文语义比对（token Jaccard 60% + 序列模糊匹配 40%） | 语义是否跑偏/漏译 | 是（抽样） |",
             "| DIM-2 术语锁定 + 结构完整性 | 行业术语必须原样保留；未翻译残留；HTML标签/数字/占位符完整性 | 术语被乱翻、标签被破坏、数字丢失 | 否（全量） |",
             "| DIM-3 语言正确性 + 长度比 | 目标语字符集校验（日文需假名/汉字、韩文需 Hangul、德文需拉丁）；译文/原文长度比合理区间 | 返回错语种、翻译截断 | 否（全量） |",
             "| DIM-4 批量 vs 单条 交叉一致性 | 抽样用单条独立请求重翻，与批量结果模糊比对 | 批量拼接导致串味/错位 | 是（抽样） |", ""]
    for lang, d in r["langs"].items():
        tot = d["pairs_total"]
        lines += ["## %s" % L.get(lang, lang), "",
                  "| 指标 | 结果 |", "|---|---|",
                  "| 校验文本条数 | %d |" % tot,
                  "| DIM-1 回译平均相似度 | %.3f（低于阈值 %d 条，占抽样 %.1f%%） |"
                  % (d["dim1"]["avg_score"], d["dim1"]["bad"],
                     100.0 * d["dim1"]["bad"] / max(1, d["dim1"]["checked"])),
                  "| DIM-2 术语/结构异常 | %d 条（%.2f%%） |"
                  % (d["dim2"]["bad"], 100.0 * d["dim2"]["bad"] / max(1, d["dim2"]["checked"])),
                  "| DIM-3 语言/长度异常 | %d 条（%.2f%%） |"
                  % (d["dim3"]["bad"], 100.0 * d["dim3"]["bad"] / max(1, d["dim3"]["checked"])),
                  "| DIM-4 交叉一致性 | %.3f（异常 %d 条，占抽样 %.1f%%） |"
                  % (d["dim4"]["avg_score"], d["dim4"]["bad"],
                     100.0 * d["dim4"]["bad"] / max(1, d["dim4"]["checked"])), ""]
        for dim, key in (("DIM-1 回译低于阈值", "dim1"), ("DIM-2 术语/结构异常", "dim2"),
                         ("DIM-3 语言/长度异常", "dim3"), ("DIM-4 交叉不一致", "dim4")):
            if d[key]["samples"]:
                lines += ["### %s（示例）" % dim, ""]
                for s in d[key]["samples"][:8]:
                    lines.append("- `%s`" % (s.get("src", "")[:100]))
                    if "dst" in s:
                        lines.append("  - 译文：%s" % s["dst"][:100])
                    if "back" in s:
                        lines.append("  - 回译：%s（score %s）" % (s["back"][:100], s.get("score")))
                    if "issues" in s:
                        lines.append("  - 问题：%s" % ", ".join(s["issues"]))
                    if "single" in s:
                        lines.append("  - 单条重翻：%s（一致度 %s）" % (s["single"][:100], s.get("score")))
                lines.append("")
    open(REPORT_MD, "w", encoding="utf-8").write("\n".join(lines))


if __name__ == "__main__":
    main()
