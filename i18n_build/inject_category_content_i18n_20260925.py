#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把**手写译文**注入 `category_content_data.json`，绕开 DeepL —— 2026-09-25

【为什么不用 DeepL】
开工前实测 `translator.usage()` = 500000/500000（免费额度已耗尽），
备份 key `.deepl_key.bak_20260915` 也已失效（HTTP 403）。
而语言版需求 = EN 21,826 字符 × 6 = **130,956** 字符 > 当时剩余 98,408。
→ 走项目既有约定：**语言版改动手写译文直接注入**（见 MEMORY.md）。

【为什么单独一个脚本，而不是直接改 add_category_content】
`add_category_content_20260925.py` 的英文侧是**手写**的（PAGES 里成对存 en/zh），
语言侧走 `translator.translate_lines`。这里不改它的取数逻辑，只**预填数据文件**：
`build_data()` 读取已有 DATA 后 `todo = [lg for lg in langs if 该语言不是全部命中]`，
只要 128 条源串在 DATA 里全有 → `todo == []` → **零 API 调用**。

【数据源格式（镜像 PAGES 结构，位置无关 ⇒ 不可能错位）】
    i18n_build/catcontent_i18n/<lang>.json
    {
      "<page>.html": {
        "eyebrow": "…", "h2": "…",
        "paras":  ["…", "…", "…"],
        "faq_h2": "…",
        "qa":     [{"q": "…", "a": "…"} × 5]
      },  … 共 8 页
    }
⭐ 刻意**不用「128 条按顺序的数组」**：那种格式一个 off-by-one 就会把整页译文错位，
   而脚本自身的断言（条数、JSON-LD、标签配平）**都抓不到错位**（条数依然对）。
   镜像结构下，映射由 PAGES 的键决定，天然对齐。

用法：
    python3 i18n_build/inject_category_content_i18n_20260925.py            # 校验 + 写 data
    python3 i18n_build/inject_category_content_i18n_20260925.py --check    # 只校验不写
"""
import argparse
import importlib.util
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

_spec = importlib.util.spec_from_file_location("acc", HERE / "add_category_content_20260925.py")
acc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(acc)          # 只定义 PAGES/LANGS，不执行 main()

I18N = HERE / "catcontent_i18n"
DATA = HERE / "category_content_data.json"

CJK = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]")


def build_lang(lg):
    """把 <lang>.json 摊平成 {EN 源串: 译文}。"""
    f = I18N / ("%s.json" % lg)
    assert f.exists(), "缺译文文件 %s" % f
    src = json.loads(f.read_text(encoding="utf-8"))
    mapping = {}

    for page, spec in acc.PAGES.items():
        d = src.get(page)
        assert d, "[%s] 缺页面 %s" % (lg, page)

        pairs = []
        pairs.append((spec["eyebrow"][0], d["eyebrow"], "eyebrow"))
        pairs.append((spec["h2"][0], d["h2"], "h2"))
        assert len(d["paras"]) == len(spec["paras"]), \
            "[%s] %s 段落数 %d ≠ %d" % (lg, page, len(d["paras"]), len(spec["paras"]))
        for i, ((en, _zh), t) in enumerate(zip(spec["paras"], d["paras"])):
            pairs.append((en, t, "para%d" % (i + 1)))
        pairs.append((spec["faq_h2"][0], d["faq_h2"], "faq_h2"))
        assert len(d["qa"]) == len(spec["qa"]), \
            "[%s] %s 问答数 %d ≠ %d" % (lg, page, len(d["qa"]), len(spec["qa"]))
        for i, ((q_en, _qz, a_en, _az), x) in enumerate(zip(spec["qa"], d["qa"])):
            pairs.append((q_en, x["q"], "q%d" % (i + 1)))
            pairs.append((a_en, x["a"], "a%d" % (i + 1)))

        for en, t, tag in pairs:
            assert isinstance(t, str) and t.strip(), "[%s] %s/%s 空译文" % (lg, page, tag)
            assert en not in mapping, "[%s] EN 源串重复：%s" % (lg, en[:60])
            mapping[en] = t.strip()

    # 完整性：不得多、不得少
    allsrc = acc.all_en_strings()
    miss = [s for s in allsrc if s not in mapping]
    extra = [s for s in mapping if s not in allsrc]
    assert not miss, "[%s] 缺 %d 条：%s" % (lg, len(miss), miss[:2])
    assert not extra, "[%s] 多 %d 条：%s" % (lg, len(extra), extra[:2])
    assert len(mapping) == len(allsrc), (lg, len(mapping), len(allsrc))
    return mapping


def validate(lg, mapping):
    """逐条质检 —— 这些断言在 `build_data` 里**只在真正调 API 时才跑**，
    DATA 预填路径不会被它检查，所以必须在这里自己查。"""
    bad = []
    for en, t in mapping.items():
        # ① 回声：整条没翻译
        if len(en.split()) >= 3 and t.strip() == en.strip():
            bad.append(("回声", en[:54]))
        # ② 占位符残留
        if "XX" in t or "TODO" in t or "…" + "…" in t:
            bad.append(("占位符", en[:54]))
        # ③ 引号紧贴术语（与 add_category_content 同一份正则口径）
        if acc._QUOTE_RE.search(t):
            bad.append(("引号紧贴术语", t[:54]))
        # ④ 长度比异常（译文 / 原文）
        # ⚠️ 判据必须**按源串长度分级**：短串膨胀得离谱是正常语言现象。
        #    · EN "What is the MOQ?"（17 字符）→ de "Wie hoch ist die
        #      Mindestbestellmenge?"（37）= 2.18；→ fr "Quelle est la quantité
        #      minimale de commande (MOQ) ?"（48）= 2.82。
        #      根因是 **EN 用缩写、目标语言须展开全称**（MOQ → quantité minimale
        #      de commande / Mindestbestellmenge / quantità minima ordinabile）。
        #    · 长段落反而稳定在 1.0–1.4，不该给宽上界（宽了会漏掉截断/漏译）。
        n = len(en)
        r = len(t) / max(1, n)
        if CJK.search(t):
            lo, hi = 0.22, 1.30
        else:
            lo, hi = 0.60, (3.00 if n < 30 else 2.10)
        if not (lo <= r <= hi):
            bad.append(("长度比 %.2f 越界[%.2f,%.2f]" % (r, lo, hi), "%s || %s" % (en[:40], t[:40])))
        # ⑤ 未转义的裸尖括号（会被 esc() 转掉，但出现说明源文有 HTML 混入）
        if re.search(r"[<>]", t):
            bad.append(("含尖括号", t[:54]))
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只校验，不写 data 文件")
    ap.add_argument("--langs", default=",".join(acc.LANGS))
    args = ap.parse_args()
    langs = [x.strip() for x in args.langs.split(",") if x.strip()]

    d = {}
    if DATA.exists():
        d = json.loads(DATA.read_text(encoding="utf-8"))
        print("已存在 data：%s（保留其余语言条目）" % DATA.name)

    total_bad = 0
    for lg in langs:
        m = build_lang(lg)
        bad = validate(lg, m)
        total_bad += len(bad)
        nw = sum(len(v.split()) for v in m.values())
        nch = sum(len(v) for v in m.values())
        print("  %-3s %3d 条 | %5d 词 | %6d 字符 | 质检异常 %d"
              % (lg, len(m), nw, nch, len(bad)))
        for kind, sample in bad[:6]:
            print("        ✗ %-22s %s" % (kind, sample))
        d[lg] = m

    if total_bad:
        raise SystemExit("\n质检未通过（%d 处），未写文件。" % total_bad)

    if args.check:
        print("\n[--check] 校验通过，未写文件。")
        return
    DATA.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n已写 %s（%.1f KB，语言：%s）" % (DATA.name, DATA.stat().st_size / 1024,
                                          ",".join(sorted(d))))
    print("下一步：python3 i18n_build/add_category_content_20260925.py --apply "
          "--langs %s" % ",".join(langs))


if __name__ == "__main__":
    main()
