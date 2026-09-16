#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""term_repair 规则表回归自测（2026-09-16）

为什么需要它：规则表已经 80 条，靠肉眼看正则无法判断
  · 新加的规则会不会被**更早**的规则抢走（顺序即优先级）
  · 规则是否**幂等**（第二遍不再改）
  · 替换串有没有把 `\\1` 写成控制字符（import 期断言已挡，但这里再验一次成句）
所以每个用例写「输入 → 期望输出」，跑 repair() 两遍（第二遍必须等于第一遍）。

用法：
    python3 test_term_repair.py          # 全部用例
    python3 test_term_repair.py fr       # 只看某语言
"""
import sys

from term_repair import repair

# (语言, 输入, 期望)
CASES = [
    # ---- 意大利语：错误省音（术语以辅音开头，不缩合）----
    ("it", "in gomma. L'TPE è riciclabile.", "in gomma. Il TPE è riciclabile."),
    ("it", "privo dell'PVC e di odori", "privo del PVC e di odori"),
    ("it", "all'TPE si aggiunge", "al TPE si aggiunge"),
    ("it", "nel PVC e nel TPE", "nel PVC e nel TPE"),
    ("it", "dall'PU al TPE", "dal PU al TPE"),
    ("it", "ai sensi del regolamento UE sull'REACHe", "ai sensi del regolamento UE sul REACH"),
    ("it", "in gomma PUcome opzione premium", "in gomma PU come opzione premium"),
    ("it", "in gomma PUdi dimensioni simili", "in gomma PU di dimensioni simili"),
    ("it", "l'EVA è una schiuma", "l'EVA è una schiuma"),          # EVA 元音开头 → 不动
    ("it", "L'OEM resta L'OEM", "L'OEM resta L'OEM"),              # OEM 元音开头 → 不动
    # ---- 意大利语：词形粘连 / 词内插空格 ----
    ("it", "in gommPUe opaca", "in gomma PU opaca"),
    ("it", "schiumEVA a celle chiuse", "schiuma EVA a celle chiuse"),
    ("it", "yogTPEi antiscivolo", "yoga TPE antiscivolo"),
    ("it", "riciclabile, priv a di PVCe inodore", "riciclabile, priva di PVC e inodore"),
    ("it", "senza PVCe inodore", "senza PVC e inodore"),
    ("it", "del PVCe ed è riciclabile", "del PVC ed è riciclabile"),
    ("it", "sostanze PVCi e odori", "sostanze PVC e odori"),
    ("it", "più pesante del TPEe", "più pesante del TPE"),
    ("it", "vi invieremo unEVAe ed EPP", "vi invieremo un EVA ed EPP"),
    # ---- 法语：缩合 / 省音 ----
    ("fr", "fabriqué à partir d'TPE", "fabriqué à partir du TPE"),
    ("fr", "de l'TPE recyclable", "du TPE recyclable"),
    ("fr", "L'TPE est recyclable", "Le TPE est recyclable"),
    ("fr", "l'PVC dégage une odeur", "le PVC dégage une odeur"),
    ("fr", "les blocs d'EVAs haute densité", "les blocs d'EVAs haute densité"),  # EVA 不动
    ("fr", "au l'TPE", "au TPE"),
    # ---- 法语：粘连 / 词形 / 词内插空格 ----
    ("fr", "exempt du PVCs et d'odeurs", "exempt du PVC et d'odeurs"),
    ("fr", "des gammes du TPEs recyclables", "des gammes du TPE recyclables"),
    ("fr", "le PVCe et est recyclable", "le PVC et est recyclable"),
    ("fr", "le TPEe pour la plupart", "le TPE pour la plupart"),
    ("fr", "PUe mat + caoutchouc", "PU mat + caoutchouc"),
    ("fr", "Éco-TPEe · Simple et double couche", "Éco-TPE · Simple et double couche"),
    ("fr", "ÉcologiqueTPEe, sans PVC, sans odeur", "TPE écologique, sans PVC, sans odeur"),
    ("fr", "sans PVCet inodore", "sans PVC et inodore"),
    # ---- 西班牙语：粘连 / 词形 ----
    ("es", "alfombrTPEes de yoga", "alfombrillas TPE de yoga"),
    ("es", "sin PVCe inodora", "sin PVC e inodora"),
    ("es", "reciclable, PVCy sin olor", "reciclable, PVC y sin olor"),
    ("es", "reciclable, PVClibre de sustancias", "reciclable, PVC libre de sustancias"),
    ("es", "sin PVCe inodor a", "sin PVC e inodora"),
    ("es", "REACHCA Prop 65", "REACH, CA Prop 65"),
    ("es", "tabla PP+TPEo, 59 cm", "tabla PP+TPE, 59 cm"),
    ("es", "el TPEo y el caucho natural", "el TPE y el caucho natural"),
    ("es", "TPE ¿PUo o esterilla de goma?", "TPE ¿PU o esterilla de goma?"),
    ("es", "no contiene ePVCo ni ftalatos", "no contiene PVC ni ftalatos"),
    ("es", "le enviaremos unEVAo y un EPP", "le enviaremos un EVA y un EPP"),
    ("es", "EcoTPEa, de una o dos capas", "Eco TPE, de una o dos capas"),
    ("es", "Material: PUe mate + caucho natural", "Material: PU mate + caucho natural"),
    ("es", "PULos híbridos de caucho son adecuados",
           "Los híbridos de caucho PU son adecuados"),
    # ---- 德语 ----
    ("de", "frei von PVCund geruchsneutral", "frei von PVC und geruchsneutral"),
    ("de", "Öko-TPEe, ein- oder zweilagig", "Öko-TPE, ein- oder zweilagig"),
    ("de", "Material: MattPUn + Gummi", "Material: Matt PU + Gummi"),
    ("de", "eine Matte von PUetwa 2.4 kg", "eine Matte von PU etwa 2.4 kg"),
    ("de", "<h2>PVCs: günstig, langlebig</h2>", "<h2>PVC: günstig, langlebig</h2>"),
    # ---- 通用：缺空格 / 幻觉词（语义纠正）----
    ("it", "80/90 cmTPE", "80/90 cm TPE"),
    ("es", "«Alignment Line»TPE", "«Alignment Line» TPE"),
    ("de", "UmweltfreundlichTPE und PVC und geruchsneutral",
           "Umweltfreundliches TPE, kein PVC, geruchsneutral"),
    ("fr", "évaluation de l'CA Prop 65", "évaluation de la Prop 65 californienne"),
    # ---- Figure 8 被当成「插图 8」（6 语言）----
    ("de", "<title>Abbildung 8: Widerstandsbänder — SANFAN</title>",
           "<title>Widerstandsbänder in Achtform — SANFAN</title>"),
    ("de", "alt=\"Abbildung 8 Widerstandsbänder\"", "alt=\"Widerstandsbänder in Achtform\""),
    ("fr", "Figure 8 : Bandes de résistance", "Bandes de résistance en huit"),
    ("it", "Figura 8: Fasce elastiche di resistenza", "Fasce elastiche a forma di 8"),
    ("it", "Figura 8: Fasce elastiche a forma di 8", "Fasce elastiche a forma di 8"),
    ("es", "Figura 8: Bandas elásticas de resistencia", "Bandas elásticas en forma de 8"),
    ("es", "Figura 8: Bandas elásticas en forma de 8", "Bandas elásticas en forma de 8"),
    ("es", "Figura 8: Bandas de resistencia", "Bandas de resistencia en forma de 8"),
    ("ja", "図8 レジスタンスバンド", "8の字レジスタンスバンド"),
    ("ko", "그림 8 저항 밴드", "8자 저항 밴드"),

    # ---- ③e 专有名词/谚文 + 术语粘连（2026-09-17 新增家族）----
    # 词干是大写开头的专有名词：旧规则尾部 `\b` 在 CJK 相邻处失效，整族漏网
    ("de", "Alignment LineTPE-Yogamatte", "Alignment Line TPE-Yogamatte"),
    ("de", "Alignment LineTPE– Yogamatte", "Alignment Line TPE– Yogamatte"),
    ("it", "Tappetino yoga Spliced ColorTPE", "Tappetino yoga Spliced Color TPE"),
    ("ja", "CorkTPEヨガマット", "Cork TPEヨガマット"),        # CJK 相邻也要断开
    ("de", "EcoTPE Matte", "Eco TPE Matte"),
    # 韩语：左侧谚文词 + 术语
    ("ko", "아치형PU 고무 요가 매트", "아치형 PU 고무 요가 매트"),
    ("ko", "스웨이드TPE 요가 매트", "스웨이드 TPE 요가 매트"),
    ("ko", "정렬 라인TPE 요가 매트", "정렬 라인 TPE 요가 매트"),
    ("ko", "에코TPE 소재", "에코 TPE 소재"),
    ("ko", "초광폭TPE 매트", "초광폭 TPE 매트"),
    ("ko", "무광PU + 고무", "무광 PU + 고무"),
    ("ko", "무광 마감PU + 천연 고무", "무광 마감 PU + 천연 고무"),
    ("ko", "초슬림형PU고무 여행용 매트", "초슬림형 PU 고무 여행용 매트"),
    # 韩语：术语 + 名词（真粘连）
    ("ko", "EVA폼롤러는 맞춤 제작됩니다", "EVA 폼롤러는 맞춤 제작됩니다"),
    ("ko", "미끄럼 방지TPE매트 90cm", "미끄럼 방지 TPE 매트 90cm"),
    ("ko", "재활용 가능, PVC무첨가 및 무취", "재활용 가능, PVC 무첨가 및 무취"),
    ("ko", "고무 또는TPE베이스에 적층", "고무 또는 TPE 베이스에 적층"),
    ("ko", "PVC성분이 없고", "PVC 성분이 없고"),
    ("ko", "알루미늄 합금 + PVC코팅 와이어", "알루미늄 합금 + PVC 코팅 와이어"),
    # ⚠️ 韩语助词必须连写 —— 这几条是「不能改」的反例，防止有人以后写通用规则
    ("ko", "TPE에서 제공되는 고무, 코르크", "TPE에서 제공되는 고무, 코르크"),
    ("ko", "무광 PU 고무 요가 매트 PU의 표면", "무광 PU 고무 요가 매트 PU의 표면"),
    ("ko", "PVC 저급 제품은 단단한 반면, NBR는 두껍다", "PVC 저급 제품은 단단한 반면, NBR는 두껍다"),
    ("ko", "TPE가 PVC보다 더 친환경적인가요", "TPE가 PVC보다 더 친환경적인가요"),
    ("ko", "EVA와 크기가 동일하므로", "EVA와 크기가 동일하므로"),
    ("ko", "그립감보다 두꺼운 쿠션에는 NBR를 추천", "그립감보다 두꺼운 쿠션에는 NBR를 추천"),
    ("ko", "금전적 손실을 초래하는 MOQ에 관한", "금전적 손실을 초래하는 MOQ에 관한"),
    ("ko", "Eco TPE, 무PVC, 무취", "Eco TPE, 무PVC, 무취"),   # 무 前缀不拆

    # ---- ③f 短冠词/前缀被吞（fr/es）----
    ("fr", "Il ne contient ni éPVC, ni plastifiants", "Il ne contient ni PVC, ni plastifiants"),
    ("es", "un comportamiento opuesto al de lPVC", "un comportamiento opuesto al del PVC"),
    ("es", "duplica aproximadamente el de lTPE", "duplica aproximadamente el del TPE"),

    # ---- 语序规则的**假阳性护栏**：引号里是虚词时不换位 ----
    # DeepL 把 EN 的 `vs` 当名词加了书名号：`caoutchouc « vs » PU`。
    # 不加守卫时语序规则会改成 `caoutchouc PU « vs »` —— 把正确语序改坏。
    ("fr", "Tapis de yoga en caoutchouc « vs » PU", "Tapis de yoga en caoutchouc « vs » PU"),
    ("fr", "Tapis de yoga en caoutchouc « Marble Print »PU",
           "Tapis de yoga en caoutchouc PU « Marble Print »"),
    ("es", "Esterilla de yoga « vs » TPE", "Esterilla de yoga « vs » TPE"),
    ("es", "Esterilla de yoga «Gray Mandala» deTPE",
           "Esterilla de yoga TPE «Gray Mandala»"),

    # ---- ③g 「TPE vs PU」术语甩句首 + vs 加书名号（fr/es）----
    ("fr", "TPE Tapis de yoga en caoutchouc « vs » PU : lequel choisir en 2026",
           "Tapis de yoga en caoutchouc TPE vs PU : lequel choisir en 2026"),
    ("es", "TPE Alfombrillas de yoga de goma «vs» PU: ¿cuál elegir en 2026?",
           "Alfombrillas de yoga de goma TPE vs PU: ¿cuál elegir en 2026?"),

    # ---- ③h 术语清单被压缩：逗号吞空格 / es 连接词 y 被焊进术语 ----------------
    ("es", "documentación disponible previa solicitud en SGS,REACHyCA Prop 65.",
           "documentación disponible previa solicitud en SGS, REACH y CA Prop 65."),
    ("de", "MOQ 100 Stück, SGS,REACH/CA Prop 65", "MOQ 100 Stück, SGS, REACH/CA Prop 65"),
    ("it", "TPE,PVC e NBR", "TPE, PVC e NBR"),
    # 反例：逗号后本来就有空格 → 必须原样不动（规则不能把正确文本改坏）
    ("es", "SGS, REACH y CA Prop 65", "SGS, REACH y CA Prop 65"),
    ("fr", "TPE, PVC et NBR", "TPE, PVC et NBR"),
    # 反例：`y` 作为普通单词出现在术语之间时，只有 es 那条规则能动它
    ("fr", "REACH y CA", "REACH y CA"),
]


def main():
    only = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    bad = 0
    n = 0
    for lg, src, want in CASES:
        if only and lg != only:
            continue
        n += 1
        got = repair(src, lg)
        if got != want:
            bad += 1
            print("✗ [%s] 输入: %s\n  期望: %s\n  实得: %s" % (lg, src, want, got))
            continue
        again = repair(got, lg)
        if again != got:
            bad += 1
            print("✗ [%s] **非幂等**\n  第一遍: %s\n  第二遍: %s" % (lg, got, again))
    print("用例 %d 个 | 失败 %d 个" % (n, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
