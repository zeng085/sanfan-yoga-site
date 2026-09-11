#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为「产品规格表 10 字段化」生成 6 语言本地化值表。

背景
----
阶段 1 已把 EN 27 个产品页规格表改成 10 行（Material/Size/Thickness/Weight/
MOQ/Colors/Feature/Logo/Compliance/Packaging）。阶段 2 要把同一套修正同步到
de/ja/ko/fr/it/es 各 27 页。

本脚本只做一件事：算出「EN 侧发生变化的值」在 6 语言里应该长什么样，
输出 i18n_build/spec_values.json 供 patch_product_specs.py --lang all 读取。

三条硬约束（来自用户指令）
--------------------------
1. 证书以英文站 + 上传文件为准  ->  Compliance 六语统一为同一串（认证名/标准号不译）
2. MOQ 以站点现有值为准        ->  本脚本完全不产出 MOQ，语言页 MOQ 原样保留
3. 价格不上站                  ->  不产出任何价格字段

免翻判定
--------
尺寸/厚度/重量大多是纯数字+单位（185×68 cm、4.5 mm、2900 g/pc），跨语言通用，
直接沿用；只有含实词（Rope、bag、folded、iron…）的才送翻译。

英制处理
--------
欧/日/韩页按站点约定纯公制：去掉 (9" × 6" × 3") 这类英制括注，lb 折算成 kg。
"""
import os, re, json, subprocess, glob, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

CANON = ["Material", "Size", "Thickness", "Weight", "MOQ", "Colors",
         "Feature", "Logo", "Compliance", "Packaging"]
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
METRIC_FIELDS = ("Size", "Thickness", "Weight")

CERT = "ROHS / CE / ISO 9001 / BSCI / REACH"

# ---------------------------------------------------------------- 译审修正表
# DeepL 在这几条上稳定出错，人工定稿覆盖。键 = "<字段>|<EN 原值>"。
_R = "Rope 2.2 / 2.4 / 2.8 / 3 m; handles 12×2 – 19.3×3.1 cm"
_SOLID = "Solid EVA / EVA + PVC"
_CORK = "EVA / POE / Cork"
_FROST = "Frosted PU + Natural Rubber"
_LATEX = "Latex / TPE / Rubber / Polyester Cotton + Latex / Silicone"
_WIRE = "Steel Wire + PVC / ABS + PVC / Aluminium Alloy + PVC-coated wire / PP + PVC + EVA"
_PURUB = "TPE + PP / PU Rubber + PP / Cork + PP / PVC + PP"
_WOLF = "EVA + PVC (wolf-tooth surface)"
_PLY = "Plywood / Eucalyptus Multilayer Board / PP + TPE"
_MINI = "Ø 25 cm (mini) / Ø 55 / 65 / 75 cm"
_BAR = "1–2.5 kg (silicone) / 15 / 25 lb (barbell)"

OVERRIDES = {
    "de": {
        f"Size|{_R}": "Seil 2,2 / 2,4 / 2,8 / 3 m; Griffe 12×2 – 19,3×3,1 cm",
        f"Material|{_SOLID}": "Voll-EVA / EVA + PVC",
        f"Material|{_CORK}": "EVA / POE / Kork",
        f"Material|{_FROST}": "Mattiertes PU + Naturkautschuk",
        f"Material|{_LATEX}": "Latex / TPE / Gummi / Polyester-Baumwolle + Latex / Silikon",
        f"Material|{_WIRE}": "Stahldraht + PVC / ABS + PVC / Aluminiumlegierung + PVC-beschichteter Draht / PP + PVC + EVA",
        f"Material|{_PURUB}": "TPE + PP / PU-Gummi + PP / Kork + PP / PVC + PP",
        f"Material|{_WOLF}": "EVA + PVC (Wolfszahn-Oberfläche)",
        f"Material|{_PLY}": "Sperrholz / Eukalyptus-Mehrschichtplatte / PP + TPE",
        f"Weight|{_BAR}": "1–2.5 kg (Silikon) / 6.8 / 11.3 kg (Langhantel)",
        f"Size|{_MINI}": "Ø 25 cm (mini) / Ø 55 / 65 / 75 cm",
    },
    "ja": {
        f"Size|{_R}": "ロープ 2.2 / 2.4 / 2.8 / 3 m；ハンドル 12×2 – 19.3×3.1 cm",
        f"Material|{_SOLID}": "ソリッドEVA／EVA + PVC",
        f"Material|{_CORK}": "EVA／POE／コルク",
        f"Material|{_FROST}": "つや消しPU＋天然ゴム",
        f"Material|{_LATEX}": "ラテックス／TPE／ゴム／ポリエステル・コットン＋ラテックス／シリコーン",
        f"Material|{_WIRE}": "スチールワイヤー＋PVC／ABS＋PVC／アルミニウム合金＋PVC被覆ワイヤー／PP＋PVC＋EVA",
        f"Material|{_PURUB}": "TPE＋PP／PUゴム＋PP／コルク＋PP／PVC＋PP",
        f"Material|{_WOLF}": "EVA＋PVC（ウルフ歯加工）",
        f"Material|{_PLY}": "合板／ユーカリ多層板／PP＋TPE",
        f"Weight|{_BAR}": "1–2.5 kg（シリコン）／6.8 / 11.3 kg（バーベル）",
        f"Size|{_MINI}": "Ø 25 cm（ミニ）／Ø 55 / 65 / 75 cm",
    },
    "ko": {
        f"Size|{_R}": "로프 2.2 / 2.4 / 2.8 / 3 m; 손잡이 12×2 – 19.3×3.1 cm",
        f"Material|{_SOLID}": "솔리드 EVA / EVA + PVC",
        f"Material|{_CORK}": "EVA / POE / 코르크",
        f"Material|{_FROST}": "무광 PU + 천연 고무",
        f"Material|{_LATEX}": "라텍스 / TPE / 고무 / 폴리에스터·면 혼방 + 라텍스 / 실리콘",
        f"Material|{_WIRE}": "강선 + PVC / ABS + PVC / 알루미늄 합금 + PVC 코팅 와이어 / PP + PVC + EVA",
        f"Material|{_PURUB}": "TPE + PP / PU 고무 + PP / 코르크 + PP / PVC + PP",
        f"Material|{_WOLF}": "EVA + PVC (울프투스 표면)",
        f"Material|{_PLY}": "합판 / 유칼립투스 다층판 / PP + TPE",
        f"Weight|{_BAR}": "1–2.5 kg (실리콘) / 6.8 / 11.3 kg (바벨)",
        f"Size|{_MINI}": "Ø 25 cm (미니) / Ø 55 / 65 / 75 cm",
    },
    "fr": {
        f"Size|{_R}": "Corde 2,2 / 2,4 / 2,8 / 3 m ; poignées 12×2 – 19,3×3,1 cm",
        f"Material|{_SOLID}": "EVA massif / EVA + PVC",
        f"Material|{_CORK}": "EVA / POE / Liège",
        f"Material|{_FROST}": "PU mat + caoutchouc naturel",
        f"Material|{_LATEX}": "Latex / TPE / Caoutchouc / Polyester-coton + latex / Silicone",
        f"Material|{_WIRE}": "Fil d'acier + PVC / ABS + PVC / Alliage d'aluminium + fil revêtu de PVC / PP + PVC + EVA",
        f"Material|{_PURUB}": "TPE + PP / Caoutchouc PU + PP / Liège + PP / PVC + PP",
        f"Material|{_WOLF}": "EVA + PVC (surface en dents de loup)",
        f"Material|{_PLY}": "Contreplaqué / Panneau multicouche en eucalyptus / PP + TPE",
        f"Weight|{_BAR}": "1–2.5 kg (silicone) / 6.8 / 11.3 kg (haltère)",
        f"Size|{_MINI}": "Ø 25 cm (mini) / Ø 55 / 65 / 75 cm",
    },
    "it": {
        f"Size|{_R}": "Corda 2,2 / 2,4 / 2,8 / 3 m; maniglie 12×2 – 19,3×3,1 cm",
        f"Material|{_SOLID}": "EVA compatto / EVA + PVC",
        f"Material|{_CORK}": "EVA / POE / Sughero",
        f"Material|{_FROST}": "PU opaco + gomma naturale",
        f"Material|{_LATEX}": "Lattice / TPE / Gomma / Poliestere-cotone + lattice / Silicone",
        f"Material|{_WIRE}": "Filo d'acciaio + PVC / ABS + PVC / Lega di alluminio + filo rivestito in PVC / PP + PVC + EVA",
        f"Material|{_PURUB}": "TPE + PP / Gomma PU + PP / Sughero + PP / PVC + PP",
        f"Material|{_WOLF}": "EVA + PVC (superficie a denti di lupo)",
        f"Material|{_PLY}": "Compensato / Pannello multistrato di eucalipto / PP + TPE",
        f"Weight|{_BAR}": "1–2.5 kg (silicone) / 6.8 / 11.3 kg (bilanciere)",
        f"Size|{_MINI}": "Ø 25 cm (mini) / Ø 55 / 65 / 75 cm",
    },
    "es": {
        f"Size|{_R}": "Cuerda 2,2 / 2,4 / 2,8 / 3 m; asas 12×2 – 19,3×3,1 cm",
        f"Material|{_SOLID}": "EVA macizo / EVA + PVC",
        f"Material|{_CORK}": "EVA / POE / Corcho",
        f"Material|{_FROST}": "PU mate + caucho natural",
        f"Material|{_LATEX}": "Látex / TPE / Caucho / Algodón con poliéster + látex / Silicona",
        f"Material|{_WIRE}": "Alambre de acero + PVC / ABS + PVC / Aleación de aluminio + alambre recubierto de PVC / PP + PVC + EVA",
        f"Material|{_PURUB}": "TPE + PP / Caucho PU + PP / Corcho + PP / PVC + PP",
        f"Material|{_WOLF}": "EVA + PVC (superficie de diente de lobo)",
        f"Material|{_PLY}": "Contrachapado / Tablero multicapa de eucalipto / PP + TPE",
        f"Weight|{_BAR}": "1–2.5 kg (silicona) / 6.8 / 11.3 kg (barra)",
        f"Size|{_MINI}": "Ø 25 cm (mini) / Ø 55 / 65 / 75 cm",
    },
}

UNIT_ONLY = re.compile(r"^[0-9\s.,×xXØø\-–—/~²³°\"'()\[\]+]*$")
UNIT_TOKEN = re.compile(r"^(?:mm|cm|m|kg|g|lb|W|T|pcs|pc)$", re.I)


def fields(html):
    """取规格表 {canonical_field: value}"""
    m = re.search(r'<table class="spec-table".*?</table>', html, re.S)
    if not m:
        return {}
    t = m.group(0)
    ths = [re.sub(r"<[^>]+>", "", x).strip() for x in re.findall(r"<th>(.*?)</th>", t, re.S)]
    tds = [re.sub(r"<[^>]+>", "", x).strip() for x in re.findall(r"<td>(.*?)</td>", t, re.S)]
    out = {}
    for th, td in zip(ths, tds):
        for c in CANON:
            if th.startswith(c):
                out[c] = td
                break
    return out


def head_html(slug):
    r = subprocess.run(["git", "show", f"HEAD:products/{slug}.html"],
                       capture_output=True, text=True, cwd=ROOT)
    return r.stdout


# pr4 重量里的 Cork 是 DeepL 的稳定漏译点：de/fr/it/es 直接原样返回，ja/ko 译成"焦炭"
_CORKW = "200 g/pc (EVA) / 750 g/pc (Cork)"
for _lg, _v in {
    "de": "200 g/pc (EVA) / 750 g/pc (Kork)",
    "ja": "200 g/pc (EVA) / 750 g/pc (コルク)",
    "ko": "200 g/pc (EVA) / 750 g/pc (코르크)",
    "fr": "200 g/pc (EVA) / 750 g/pc (Liège)",
    "it": "200 g/pc (EVA) / 750 g/pc (Sughero)",
    "es": "200 g/pc (EVA) / 750 g/pc (Corcho)",
}.items():
    OVERRIDES[_lg]["Weight|%s" % _CORKW] = _v


def _lb(x):
    return round(float(x) * 0.45359237, 1)


def to_metric(v):
    """欧/日/韩页：去英制括注 + lb 折算 kg"""
    v = re.sub(r'\s*\(\s*[\d./\s×x]*"\s*(?:×\s*[\d./\s]*"\s*)*\)', "", v)
    v = re.sub(r'\s*\([\d./]+\s*"\)', "", v)
    # "15 / 25 lb" 这类分子分母共用单位，必须先处理（否则只折算后一个数）
    v = re.sub(r"(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)\s*lb",
               lambda m: "%g / %g kg" % (_lb(m.group(1)), _lb(m.group(2))), v, flags=re.I)
    v = re.sub(r"(\d+(?:\.\d+)?)\s*lb",
               lambda m: "%g kg" % _lb(m.group(1)), v, flags=re.I)
    return re.sub(r"\s{2,}", " ", v).strip()


def clean(v):
    """DeepL 译文常见污染的统一清洗"""
    v = re.sub(r"(\d)。(\d)", r"\1.\2", v)        # ja/ko 小数点被写成句号
    v = re.sub(r"[„“”«»]", "", v)                 # 引擎自行添加的书名/引号
    v = re.sub(r"(?<=[A-Za-z])\+(?=[A-Za-z])", " + ", v)
    v = re.sub(r"\s+([（）、。，])", r"\1", v)
    return re.sub(r"\s{2,}", " ", v).strip()


def needs_translation(v):
    if UNIT_ONLY.match(v):
        return False
    letters = re.findall(r"[A-Za-z]+", v)
    return not (letters and all(UNIT_TOKEN.match(w) for w in letters))


def collect():
    """-> changed{slug:{field:en_value}}, base{field:{base_value}}, pairs[(field,en,base)]"""
    slugs = sorted(os.path.basename(p)[:-5]
                   for p in glob.glob(os.path.join(ROOT, "products/*.html")))
    changed = collections.OrderedDict()
    for s in slugs:
        new = fields(open(os.path.join(ROOT, f"products/{s}.html"), encoding="utf-8").read())
        old = fields(head_html(s))
        d = {}
        for f in CANON:
            if f == "MOQ":                     # 约束 2：MOQ 冻结
                continue
            nv = new.get(f)
            if nv is not None and old.get(f) != nv:
                d[f] = nv
        if d:
            changed[s] = d

    seen, pairs = set(), []
    for s, d in changed.items():
        for f, v in d.items():
            base = CERT if f == "Compliance" else (to_metric(v) if f in METRIC_FIELDS else v)
            if (f, base) not in seen:
                seen.add((f, base))
                pairs.append((f, v, base))
    return slugs, changed, pairs


def translate_all(pairs):
    """-> out[lang][field][base] = 本地化值"""
    import translator as T
    out = {}
    for lg in LANGS:
        table = collections.defaultdict(dict)
        batch, keys = [], []
        for f, en, base in pairs:
            if f == "Compliance" or not needs_translation(base):
                table[f][base] = base          # 免翻：认证串 / 纯数字单位
            else:
                batch.append(base)
                keys.append((f, base))
        if batch:
            print(f"  [{lg}] DeepL 翻译 {len(batch)} 条 ...", flush=True)
            for (f, base), r in zip(keys, T.translate_lines(batch, lg)):
                table[f][base] = clean(r)
        out[lg] = {f: dict(d) for f, d in table.items()}
        print(f"  [{lg}] 免翻 {len(pairs)-len(batch)} 条 / 送翻 {len(batch)} 条")
    return out, T


def main():
    slugs, changed, pairs = collect()
    print(f"产品页 {len(slugs)} 个，字段有变化的 {len(changed)} 个")
    cnt = collections.Counter(f for f, _, _ in pairs)
    print("去重后待处理：", ", ".join(f"{f}={n}" for f, n in cnt.items()))
    print(f"总计 {len(pairs)} 条（已去掉证书串 27 次重复等）\n")

    out, T = translate_all(pairs)

    # EN 原值 -> 本地化值（同一 EN 值可能被多处复用；人工定稿优先）
    conv = {lg: {} for lg in LANGS}
    n_ov = 0
    for lg in LANGS:
        ov = OVERRIDES.get(lg, {})
        for f, en, base in pairs:
            key = f"{f}|{en}"
            tgt = ov.get(key) or out[lg].get(f, {}).get(base)
            if not tgt:
                continue
            if key in ov:
                out[lg].setdefault(f, {})[base] = tgt
                n_ov += 1
            conv[lg][key] = tgt
    print(f"译审修正覆盖 {n_ov} 处")

    doc = {"_meta": {"cert": CERT,
                     "pairs": [{"field": f, "en": e, "base": b} for f, e, b in pairs],
                     "langs": LANGS},
           "rows": out,
           "map": conv}
    dst = os.path.join(HERE, "spec_values.json")
    json.dump(doc, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n已写出 {dst}")
    print("翻译统计：", T.stats())


if __name__ == "__main__":
    main()
