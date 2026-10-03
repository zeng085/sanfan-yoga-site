#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修 JSON-LD Organization.description 的英文残留（2026-10-03）

问题：全站每页都有一个 `Organization` 的 ld+json 块，其中 `description` 一直是英文
"Vertically integrated OEM/ODM manufacturer of TPE, PU and rubber yoga mats…" ——
**搜索结果里显示的就是这句**。语言页（de/ja/ko/fr/it/es）也用英文，
等于告诉 Google「这页是给英语用户看的」。审计实测 835 个页面版本命中。

为什么单独写脚本而不是丢进翻译链：
  · 这是**结构化数据里的固定一句**，不是正文；混进 723 行正文翻译里会打乱行号锚定
  · 译文必须一次到位、长期稳定，不适合每次跑批都重译
  · 只改 `description` 一个键，不能整块重写（同一块里 logo/address/contactPoint/
    knowsAbout/areaServed 都是正确的，动了就引入新风险）

`knowsAbout`（19 个产品关键词）仍是英文 —— 那是给搜索引擎的实体词，留在
「另案处理」清单里，本轮不动。

用法：
    python3 i18n_build/fix_org_description_20261003.py --dry-run
    python3 i18n_build/fix_org_description_20261003.py
    python3 i18n_build/fix_org_description_20261003.py --verify
"""
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {"i18n_build", "outputs", "__pycache__", ".git", "node_modules", "assets"}

DESC = {
 "en": "Vertically integrated OEM/ODM manufacturer of TPE, PU and rubber yoga mats plus yoga and fitness accessories. Founded 2013 in Jinjiang, Fujian, China. In-house foaming and finishing across three owned plants.",
 "de": "Vertikal integrierter OEM/ODM-Hersteller für TPE-, PU- und Naturgummi-Yogamatten sowie Yogazubehör und Fitnessgeräte. Gegründet 2013 in Jinjiang, Fujian, China. Eigenes Schäumen und Finishen in drei eigenen Werken.",
 "ja": "TPE・PU・天然ゴム製ヨガマット、ヨガ用品・フィットネス用品の垂直統合型OEM/ODMメーカー。2013年に中国福建省晋江市で設立。3つの自社工場で発泡から仕上げまで一貫生産。",
 "ko": "TPE·PU·천연 고무 요가매트와 요가·피트니스용품을 수직 통합하는 OEM/ODM 제조업체. 2013년 중국 푸젠성 진강시에 설립. 3개 자사 공장에서 발泡부터 마감까지 내재화.",
 "fr": "Fabricant OEM/ODM intégré verticalement de tapis de yoga en TPE, PU et caoutchouc naturel, ainsi que d’accessoires de yoga et de fitness. Fondé en 2013 à Jinjiang, Fujian, Chine. Mousse et finition réalisées en interne dans trois usines.",
 "it": "Produttore OEM/ODM verticalmente integrato di tappetini yoga in TPE, PU e gomma naturale, oltre ad accessori yoga e fitness. Fondato nel 2013 a Jinjiang, Fujian, Cina. Schiumatura e finitura realizzate internamente in tre stabilimenti di proprietà.",
 "es": "Fabricante OEM/ODM verticalmente integrado de esterillas de yoga de TPE, PU y caucho natural, además de accesorios de yoga y fitness. Fundado en 2013 en Jinjiang, Fujian, China. Espumación y acabado realizados internamente en tres plantas propias.",
}
EN_MARK = ("Vertically integrated", "manufacturer of TPE", "Founded 2013 in Jinjiang")
RE_LD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
RE_DESC = re.compile(r'("description"\s*:\s*")((?:[^"\\]|\\.)*)(")')


def lang_of(rel):
    if "/" in rel:
        top = rel.split("/")[0]
        if len(top) == 2 and top.isalpha() and top in DESC:
            return top
    return "en"


def fix(h, lang):
    want = DESC[lang]
    n = 0
    out = []
    pos = 0
    for m in RE_LD.finditer(h):
        blk = m.group(1)
        if '"Organization"' not in blk or '"@type": "Organization"' not in blk:
            continue
        if EN_MARK[0] not in blk:
            continue
        nb, k = RE_DESC.subn(lambda mm: mm.group(1) + want.replace('"', '\\"') + mm.group(3), blk, count=1)
        if k:
            out.append(h[pos:m.start(1)])
            out.append(nb)
            pos = m.end(1)
            n += k
    if not n:
        return h, 0
    out.append(h[pos:])
    return "".join(out), n


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    files = []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if f.endswith(".html"):
                files.append(os.path.join(dp, f))
    files.sort()

    if mode == "--verify":
        # ⚠️ EN 页的 description **本来就该是英文** —— 首版 verify 没区分语言，
        #    把 179 个 EN 页全报成"未修"，实际 6 个语言版 0 残留（自己把自己吓一跳）。
        bad = []
        en_ok = 0
        for p in files:
            rel = os.path.relpath(p, ROOT)
            lang = lang_of(rel)
            h = io.open(p, encoding="utf-8").read()
            for m in RE_LD.finditer(h):
                blk = m.group(1)
                if '"Organization"' in blk and any(k in blk for k in EN_MARK):
                    if lang == "en":
                        en_ok += 1          # 英文是正确形态，不算问题
                    else:
                        bad.append(rel)
                    break
            for m in RE_LD.finditer(h):
                try:
                    json.loads(m.group(1))
                except Exception:
                    bad.append(rel + " (JSON 解析失败)")
                    break
        print("非 EN 页面仍含英文 description = %d（EN 页 %d 个保留英文，正确）"
              % (len(bad), en_ok))
        for b in bad[:8]:
            print("   ✗ %s" % b)
        return 1 if bad else 0

    changed = 0
    for p in files:
        rel = os.path.relpath(p, ROOT)
        h = io.open(p, encoding="utf-8").read()
        h2, n = fix(h, lang_of(rel))
        if not n:
            continue
        try:
            for m in RE_LD.finditer(h2):
                json.loads(m.group(1))
        except Exception as e:
            print("✗ %s 生成后 JSON 不可解析，已跳过：%s" % (rel, e))
            continue
        changed += 1
        if mode != "--dry-run":
            io.open(p, "w", encoding="utf-8").write(h2)
    print("扫描 %d 页，需改 %d 页%s" % (len(files), changed, "（dry-run）" if mode == "--dry-run" else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
