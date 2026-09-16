#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""编辑项收尾（2026-09-17）：短描述补长 / 事实错误 / 名称内粘连 → 单文件表驱动。

【为什么是「表驱动 + 精确串」而不是正则批处理】
这几类是**编辑判断**，不是机器可判的规则：
  ① 描述只有 42–77 宽 → 要补成站内句式 `产品名+规格句. 定制句 — 价值句`
  ② de/products/fr2.html 描述 `EVA-Rolle aus Vollholz`（Vollholz=实木）→ 事实错误，
     Solid EVA 是「整体 EVA 发泡」，不是木头
  ③ de `Solid Faszienrollen` / `Elektrisches Faszienrollen` 形容词-名词数不一致
     （JSON-LD 里本来就是对的单数，说明是 h1 生成时串了）
  ④ `Alignment LineTPE` / `정렬 라인TPE` 术语被焊进单词（扫描器漏报的形态：
     词干是**专有名词大写开头**，GLUE_LOWER 要求小写词干 ≥3 字母，故抓不到）
  ⑤ `mit Widerstandsbänder` 应为第三格复数 `-bändern`（但正文里
     `enthalten zusätzlich „Widerstandsbänder“` 是第四格，**正确，不能一起改**）

所以每条都是「文件 × 原串 × 新串」，可逐条复核，不做全局正则。

规格数据来源：products/*.html 的 spec-table（MOQ 已核对：fr2=500 pcs，其余 On request
—— 因此新描述里**不写 MOQ**，避免与规格表冲突）。

用法：python3 fix_editorial_20260917.py [--apply]
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# (相对路径, 原串, 新串, 备注)
SUBS = [
    # ── ① 短描述补长（站内句式：产品名+规格. 定制句 — 价值句）────────────────
    ("products/fr2.html",
     "Solid EVA roller for deep-tissue massage and core training.",
     "Solid EVA foam roller, 33x13 / 45x13.5 cm. Density, colour and logo are set to your order — deep tissue and core work.",
     "En 描述补长"),
    ("products/fr3.html",
     "Rechargeable vibrating foam roller for professional recovery.",
     "Rechargeable vibrating foam roller, PU + ABS, 31x10 cm. Speed levels, colour and logo are set to your order — studio and clinic recovery.",
     "En 描述补长"),
    ("products/fr5.html",
     "Fascia massage ball for shoulders, back, waist and foot relief.",
     "EVA / TPE massage ball, Ø 6 / 7 / 7.5 / 10 cm. Hardness, colour and logo are set to your order — shoulders, back, waist and feet.",
     "En 描述补长"),
    ("products/ym7.html",
     "Camouflage-print TPE mat with a bold look, ideal for branded lines.",
     "Camouflage-print TPE yoga mat, 183x68 cm, 6 mm. Print, thickness and logo are made to your order — a bold line for brand programmes.",
     "En 描述补长"),

    # ② de fr2：事实错误 Vollholz（实木）→ massives EVA，顺带补长
    ("de/products/fr2.html",
     "EVA-Rolle aus Vollholz für Tiefenmassagen und Rumpftraining.",
     "Faszienrolle aus massivem EVA, 33x13 / 45x13.5 cm. Dichte, Farbe und Logo nach Ihren Vorgaben – Tiefenmassage und Rumpftraining.",
     "De fr2 事实错误：Vollholz→massives EVA + 补长"),

    ("ja/products/fr2.html",
     "深層組織マッサージやコアトレーニングに最適な、EVAのソリッドローラー。",
     "EVAソリッドフォームローラー、33×13 / 45×13.5 cm。硬さ・カラー・ロゴはご要望どおりに — 深層マッサージと体幹トレーニングに。",
     "Ja fr2 描述补长"),
    ("ja/products/fr3.html",
     "プロ仕様の回復ケア用、充電式振動マッサージ器「フォームローラー」。",
     "充電式振動フォームローラー、PU + ABS、31×10 cm。振動段階・カラー・ロゴはご要望どおりに — スタジオと治療院の回復ケアに。",
     "Ja fr3 描述补长（顺带去「」引号）"),
    ("ja/products/fr5.html",
     "肩、背中、腰、足の疲れを和らげるファシアマッサージボール。",
     "EVA / TPE マッサージボール、Ø 6 / 7 / 7.5 / 10 cm。硬さ・カラー・ロゴはご要望どおりに — 肩・背中・腰・足のケアに。",
     "Ja fr5 描述补长"),
    ("ja/products/ym7.html",
     "大胆なデザインが特徴のカモフラージュ柄のTPEマット。ブランドラインに最適です。",
     "カモフラージュ柄TPEヨガマット、183×68 cm、6 mm。柄・厚さ・ロゴはご要望どおりに — ブランドライン向けの硬派な一枚。",
     "Ja ym7 描述补长"),

    ("ko/products/fr2.html",
     "심부 조직 마사지와 코어 훈련을 위한 견고한 EVA 롤러.",
     "EVA 솔리드 폼롤러, 33×13 / 45×13.5 cm. 경도·색상·로고는 주문에 맞춰 제작 — 심부 마사지와 코어 운동용.",
     "Ko fr2 描述补长"),
    ("ko/products/fr3.html",
     "전문적인 회복을 위한 충전식 진동형 폼롤러.",
     "충전식 진동 폼롤러, PU + ABS, 31×10 cm. 진동 단계·색상·로고는 주문에 맞춰 제작 — 스튜디오·클리닉 회복 케어용.",
     "Ko fr3 描述补长"),
    ("ko/products/fr5.html",
     "어깨, 등, 허리, 발의 통증을 완화해 주는 근막 마사지 볼.",
     "EVA / TPE 마사지 볼, Ø 6 / 7 / 7.5 / 10 cm. 경도·색상·로고는 주문에 맞춰 제작 — 어깨·등·허리·발 케어용.",
     "Ko fr5 描述补长"),
    ("ko/products/ym7.html",
     "대담한 디자인의 위장무늬 TPE 매트로, 브랜드 라인에 이상적입니다.",
     "위장무늬 TPE 요가 매트, 183×68 cm, 6 mm. 패턴·두께·로고는 주문에 맞춰 제작 — 브랜드 라인용 강렬한 한 장.",
     "Ko ym7 描述补长"),

    ("fr/products/fr3.html",
     "Rouleau en mousse vibrant rechargeable pour une récupération professionnelle.",
     "Rouleau en mousse vibrant rechargeable, PU + ABS, 31x10 cm. Vitesse, couleur et logo selon vos besoins — récupération en studio et en cabinet.",
     "Fr fr3 描述补长"),
    ("it/products/fr3.html",
     "Rullo vibrante ricaricabile in schiuma per il recupero professionale.",
     "Rullo in schiuma vibrante ricaricabile, PU + ABS, 31x10 cm. Velocità, colore e logo secondo le vostre esigenze — recupero in studio e in clinica.",
     "It fr3 描述补长"),
    ("es/products/fr3.html",
     "Rodillo de espuma vibratorio recargable para la recuperación profesional.",
     "Rodillo de espuma vibratorio recargable, PU + ABS, 31x10 cm. Velocidad, color y logo según sus necesidades — recuperación en estudio y clínica.",
     "Es fr3 描述补长"),

    # ── ③ de fr2/fr3 名称：与 JSON-LD 的正确单数对齐，并去掉 title 里的假品牌 ──
    ("de/products/fr2.html",
     "Solid Faszienrollen — SANFAN",
     "Solide EVA-Faszienrolle — SANFAN",
     "De fr2 h1/og/tw：数一致 + 补 EVA"),
    ("de/products/fr2.html",
     "Solide Faszienrollen",
     "Solide EVA-Faszienrolle",
     "De fr2 JSON-LD 名称对齐"),
    ("de/products/fr2.html",
     "Faszienrollen von Solid — SANFAN Yoga &amp; Fitness OEM",
     "Solide EVA-Faszienrolle — SANFAN",
     "De fr2 <title>：「von Solid」读起来像品牌，改短后缀"),
    ("de/products/fr3.html",
     "Elektrisches Faszienrollen — SANFAN",
     "Elektrische Faszienrolle — SANFAN",
     "De fr3 h1/og/tw：形容词-名词数一致"),
    ("de/products/fr3.html",
     "Elektrische Faszienrollen",
     "Elektrische Vibrations-Faszienrolle",
     "De fr3 JSON-LD 名称补 Vibrations"),
    ("de/products/fr3.html",
     "<title>Elektrische Vibrations-Faszienrolle — SANFAN Yoga & Fitness OEM</title>",
     "<title>Elektrische Vibrations-Faszienrolle — SANFAN</title>",
     "De fr3 <title> 数一致 + 短后缀"),

    # ── ④ 名称内术语粘连（专有名词大写词干 + 术语，扫描器漏报形态）──────────
    ("de/products/alignment-line-tpe-yoga-mat.html",
     "<title>Alignment LineTPE– Yogamatte — SANFAN Yoga & Fitness OEM</title>",
     "<title>TPE-Yogamatte mit Ausrichtungslinien — SANFAN</title>",
     "De 对齐线页 title：粘连 + 名称与分类卡统一"),
    ("de/products/alignment-line-tpe-yoga-mat.html",
     "Alignment LineTPE-Yogamatte — SANFAN",
     "TPE-Yogamatte mit Ausrichtungslinien — SANFAN",
     "De 对齐线页 h1/og/tw：粘连 + 统一"),
    ("ko/products/alignment-line-tpe-yoga-mat.html",
     "얼라인먼트 라인TPE 요가 매트",
     "정렬 라인 TPE 요가 매트",
     "Ko 对齐线页 desc：名称与分类卡/JSON-LD 统一 + 补空格"),
    ("ko/products/alignment-line-tpe-yoga-mat.html",
     "라인TPE",
     "라인 TPE",
     "Ko 对齐线页剩余粘连（JSON-LD/alt/h2）"),
    ("ko/tpe-yoga-mats.html",
     "정렬 라인TPE 요가 매트",
     "정렬 라인 TPE 요가 매트",
     "Ko 分类卡：术语前补空格"),

    # ── ⑤ de 格位：名称里的 dative 复数（正文里的第四格不动）────────────────
    ("de/products/ab-roller-with-resistance-band.html",
     "Ab-Roller mit Widerstandsbänder",
     "Ab-Roller mit Widerstandsbändern",
     "De 名称 h1/alt/h2：mit 后应为第三格复数"),
    ("de/products/ab-roller-with-resistance-band.html",
     "Ab-Roller mit „Widerstandsbänder“",
     "Ab-Roller mit Widerstandsbändern",
     "De 名称 og/tw/JSON-LD：同上 + 去引号"),

    # ── ⑥ it 阻带页：同页两套译名 → 统一为站内多数形态（分类卡+JSON-LD+场景页）──
    ("it/products/tpe-resistance-loop-band.html",
     "TPE Fascia elastica per allenamento di resistenza — SANFAN",
     "TPE Fascia elastica per esercizi di resistenza — SANFAN",
     "It 阻带页 og/tw/h1：向多数形态对齐"),
    ("it/products/tpe-resistance-loop-band.html",
     "TPE Fascia elastica ad anello — SANFAN",
     "TPE Fascia elastica per esercizi di resistenza — SANFAN",
     "It 阻带页 <title>：同上"),
]


# 语言内全量替换（同一串可能散在多页，例如锚文本会出现在多篇博客）
# (语言, 原串, 新串, 备注)
GLOBAL_SUBS = [
    # ⑦ 锚文本 `TPE vs PU comparison`：EN 侧 "vs" 被当成普通词翻译，
    #    6 个语言全坏（fr/es 还把 vs 当名词加了引号，it 直接焊成 vsPU）
    ("de", "TPE Vergleich zwischen PU", "Vergleich TPE vs. PU", "De 锚文本"),
    ("ja", "TPE PUとの比較", "TPEとPUの比較", "Ja 锚文本"),
    ("ko", "TPE PU 비교", "TPE와 PU 비교", "Ko 锚文本"),
    ("fr", "TPE Comparaison entre le « vs » et PU", "Comparaison TPE et PU", "Fr 锚文本"),
    ("it", "TPE Confronto tra vsPU", "Confronto TPE e PU", "It 锚文本（粘连+乱序）"),
    ("es", "TPE Comparación entre «vs» y PU", "Comparación TPE y PU", "Es 锚文本"),

    # ⑧ ja 卡片名把 Cork 写成拉丁文并与 TPE 粘连 → 按日语习惯用片假名
    ("ja", "CorkTPEヨガマット", "コルクTPEヨガマット", "Ja 卡片名：Cork→コルク + 去粘连"),

    # ⑨ ⭐ 实心 EVA 被译成「实木」（第二轮·正文层）------------------------------
    #    上一轮只修了 fr2 的 meta 三处 + h2，**漏了正文**：产品卡 / pd-overview 里
    #    仍有 9 处 `EVA-Rolle aus Vollholz`。Vollholz=实木，产品是实心 EVA 泡棉，
    #    属**事实错误**，德语文案里最伤信任的一类。
    #    ⚠️ 只替换「EVA-Rolle aus Vollholz」这个完整短语 —— 不能对着
    #       `Vollholz|Massivholz` 全局替换：Pilates Ladder Barrel 的
    #       `Massivholz-Bogen`（实木弧形靠背）是**真的实木**，改了反而错。
    ("de", "EVA-Rolle aus Vollholz", "EVA-Faszienrolle", "De 事实错：实心EVA→「实木」"),

    # ⑩ ⭐⭐ `<title>` 与 og/h1 措辞分歧（第二例，独立信号）-----------------------
    #    de/fr2 的 <title> 是 `Faszienrollen von Solid` —— DeepL 把商品名 Solid
    #    当成品牌名译成「von Solid」（=由 Solid 出品）。而同页 og / twitter / h1 /
    #    JSON-LD / h2 **五处全是** `Solide EVA-Faszienrolle`。
    #    这与 es/figure-8 的 `Bandas de resistencia` vs `Bandas elásticas` 是**同一模式**：
    #    「页内 title 与 og/h1 分歧」应当作为**独立扫描项**，不要只当长度问题。
    ("de", "Faszienrollen von Solid", "Solide EVA-Faszienrolle", "De title：Solid 被当品牌名"),
]


def W(s):
    return sum(2 if ord(c) > 0x2E80 else 1 for c in s)


def sub_guarded(s, old, new):
    """右边界护栏替换：old 后面**不得紧跟拉丁字母**。

    ⚠️ 必要性的血证（2026-09-17 踩到）：`Ab-Roller mit Widerstandsbänder` → `…bändern`
       时，`…bänder` 正是 `…bändern` 的**前缀**，第二次运行会把已修好的文本
       再吃一次，产出 `Widerstandsbändernnn`（16 处）。凡是「新串以原串开头」的
       替换都必须带右边界，否则非幂等。
    """
    rx = re.compile(re.escape(old) + r"(?![A-Za-z\u00c0-\u00ff])")
    return rx.sub(lambda m: new, s), len(rx.findall(s))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true", help="只报告可改处，必须为 0")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    files_hit = 0
    total = 0
    missing = []
    applied = []
    by_note = {}

    # 按文件聚合，避免同一文件反复读写
    per_file = {}
    for rel, old, new, note in SUBS:
        per_file.setdefault(rel, []).append((old, new, note))

    for rel, items in per_file.items():
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            missing.append(rel)
            continue
        s = open(path, encoding="utf-8").read()
        orig = s
        for old, new, note in items:
            if old in s:
                pass
            elif new.replace("&amp;", "&") in s or new in s:
                applied.append("%s :: %s" % (rel, note))
                continue
            else:
                missing.append("%s :: %s" % (rel, old[:44]))
                continue
            s, n = sub_guarded(s, old, new)
            if not n:
                applied.append("%s :: %s" % (rel, note))
                continue
            by_note[note] = by_note.get(note, 0) + n
            total += n
        if s != orig:
            files_hit += 1
            if args.apply:
                open(path, "w", encoding="utf-8").write(s)

    # 语言内全量替换
    import glob
    for lang, old, new, note in GLOBAL_SUBS:
        base = os.path.join(ROOT, lang) if lang else ROOT
        pat = os.path.join(base, "**", "*.html")
        hit_files = 0
        for f in glob.glob(pat, recursive=True):
            if os.path.relpath(f, ROOT).split(os.sep)[0] in ("i18n_build", "outputs"):
                continue
            s = open(f, encoding="utf-8").read()
            if old not in s:
                continue
            s2, n = sub_guarded(s, old, new)
            if not n:
                continue
            hit_files += 1
            by_note[note] = by_note.get(note, 0) + n
            total += n
            if args.apply:
                open(f, "w", encoding="utf-8").write(s2)
        if hit_files == 0:
            applied.append("[全局 %s] %s" % (lang, note))
        else:
            files_hit += hit_files

    print("模式：%s" % ("落盘" if args.apply else "干跑"))
    print("改动文件 %d 个 | 命中 %d 处" % (files_hit, total))
    if not args.quiet:
        for k in sorted(by_note):
            print("    %-46s %d" % (k, by_note[k]))
    if missing:
        print("\n⚠️ 未命中 %d 条（原串已变或已修）：" % len(missing))
        for m in missing[:30]:
            print("    " + m)

    # 描述宽度体检：只报被要求补长的那些页
    print("\n=== 目标页描述宽度（应 80–155）===")
    targets = [
        "products/fr2.html", "products/fr3.html", "products/fr5.html", "products/ym7.html",
        "de/products/fr2.html",
        "ja/products/fr2.html", "ja/products/fr3.html", "ja/products/fr5.html", "ja/products/ym7.html",
        "ko/products/fr2.html", "ko/products/fr3.html", "ko/products/fr5.html", "ko/products/ym7.html",
        "fr/products/fr3.html", "it/products/fr3.html", "es/products/fr3.html",
    ]
    bad = 0
    for rel in targets:
        path = os.path.join(ROOT, rel)
        s = open(path, encoding="utf-8").read()
        m = re.search(r'<meta name="description" content="([^"]*)"', s)
        if not m:
            print("    %-30s 取不到描述" % rel)
            continue
        w = W(m.group(1))
        flag = ""
        if w > 155:
            flag = "  ← 超预算！"
            bad += 1
        elif w < 80:
            flag = "  ← 仍偏短"
            bad += 1
        print("    %-30s w=%3d%s" % (rel, w, flag))
    print("    超限/偏短 %d 条" % bad)
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
