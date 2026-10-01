# -*- coding: utf-8 -*-
"""把价格表原始行 → 站点用的结构化型号库（8 个器械族 / 41 行 / 40 个编号）。

输入：i18n_build/data/pilates_offer_raw.json（extract_pilates_offer.py 产出）
输出：i18n_build/data/pilates_models.json

⚠️ 价格政策：原始表里带「代理价」（内部价）。本脚本**显式丢弃** price 字段，
   产物中不含任何价格，页面一律走 "Request a quote"。

    python3 i18n_build/build_pilates_data.py
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "pilates_offer_raw.json")
OUT = os.path.join(HERE, "data", "pilates_models.json")

# ---------------------------------------------------------------- 8 个器械族
# key = URL slug（/pilates/<key>.html）
FAMILIES = [
    {
        "key": "pilates-reformer",
        "en": "Pilates Reformer",
        "zh": "普拉提核心床",
        "tag_en": "Wood & Aluminium · Full-Track · Foldable",
        "tag_zh": "实木与铝合金 · 全轨道 · 可折叠",
        # 自家英文站 sanfansport.com 的叫法（那边把 Reformer 叫 Core Bed）。
        # 主词仍用国际通用名保 SEO，括注英文站叫法让两边对得上。
        "alias_en": "Core Bed",
        "lead_en": "The reformer is the machine a studio is built around. We build it on solid "
                   "timber or aluminium, with "
                   "stainless-steel rails, silent bearing rollers and adjustable spring bars. "
                   "Australian and European geometries, full-track and foldable builds, and the "
                   "M-series for large commercial studios.",
        "lead_zh": "核心床是普拉提馆的立馆之本。我们用实木或铝合金做床身，"
                   "配不锈钢轨道、静音轴承滑轮与可调挂簧板。澳版、欧版两种几何，另有全轨道、可折叠与"
                   "适合大型商业馆的 M 系列。",
    },
    {
        "key": "pilates-cadillac",
        "en": "Pilates Cadillac",
        "zh": "普拉提凯迪拉克床",
        "tag_en": "Trapeze Table · Full Tower · 10 Springs",
        "tag_zh": "高架吊床 · 全塔架 · 10 根弹簧",
        "alias_en": "Cadillac Bed",
        "lead_en": "The Cadillac (trapeze table) carries the widest exercise vocabulary of any "
                   "Pilates apparatus. Our frames ship with a stainless-steel tower, ten tower "
                   "springs, push-through bar, trapeze, safety strap, footboard and wooden dowel — "
                   "so the studio can start teaching the day it is assembled.",
        "lead_zh": "凯迪拉克床（高架吊床）是普拉提动作谱系最宽的器械。我们的整机配不锈钢高架、10 根高架弹簧、"
                   "推动杆、悬挂、安全绳、脚踏板与圆木杆，馆里装好当天就能开课。",
    },
    {
        "key": "pilates-wunda-chair",
        "en": "Pilates Wunda Chair",
        "zh": "普拉提稳踏椅",
        "tag_en": "Pedal Chair · 4 Springs · Compact",
        "tag_zh": "踏板椅 · 4 根弹簧 · 占地小",
        "alias_en": "Pilates Chair",
        "lead_en": "A compact vertical spring column with a hinged pedal, built for one-to-one "
                   "sessions and small studios. Adjustable multi-position pedal, stainless "
                   "hardware and a frame that fits into a corner.",
        "lead_zh": "紧凑的垂直弹簧立柱加铰链踏板，适合一对一课程与小面积工作室。踏板多档可调，"
                   "五金件全不锈钢，一个墙角就能放下。",
    },
    {
        "key": "pilates-ladder-barrel",
        "en": "Pilates Ladder Barrel",
        "zh": "普拉提梯桶",
        "tag_en": "Adjustable Ladder · Solid Wood Arc",
        "tag_zh": "可调梯级 · 实木弧面",
        "lead_en": "A solid-wood arc with an adjustable ladder rung for spinal extension, "
                   "stretching and side-bending work. The rung moves through multiple positions so "
                   "one barrel serves every body in the studio.",
        "lead_zh": "实木弧面配可调梯级，用于脊柱伸展、拉伸与侧屈训练。梯级多档可调，"
                   "一个梯桶就能适配馆内所有身材的会员。",
    },
    {
        "key": "pilates-spine-corrector",
        "en": "Pilates Spine Corrector",
        "zh": "普拉提矫正器",
        "tag_en": "Barrel · Step · Dowel Included",
        "tag_zh": "弧桶 · 台阶 · 含圆木杆",
        "lead_en": "The small barrel with a step, used for spinal mobilisation, thoracic "
                   "extension and shoulder work. Light enough to move between the mat area and "
                   "the equipment floor, and the cheapest way to add apparatus to a group class.",
        "lead_zh": "带台阶的小弧桶，用于脊柱松动、胸椎伸展与肩部训练。轻便，垫上区与器械区可以随手挪，"
                   "也是团体课加器械最省成本的方案。",
    },
    {
        "key": "pilates-reformer-tower",
        "en": "Reformer Tower & 3-in-1",
        "zh": "半高架与三合一",
        "tag_en": "Half Tower · Reformer + Tower Combo",
        "tag_zh": "半高架 · 床塔一体",
        "lead_en": "A half tower bolts onto the end of a reformer to add tower springs and a "
                   "push-through bar without giving up floor space. The 3-in-1 build combines "
                   "reformer, half tower and full tower in a single frame.",
        "lead_zh": "半高架固定在核心床尾端，加上高架弹簧与推动杆，却不额外占地面。"
                   "三合一款把核心床、半高架与全塔架合到同一副床架上。",
    },
    {
        "key": "pilates-studio-set",
        "en": "Pilates Studio Set",
        "zh": "普拉提五件套",
        "tag_en": "5 Pieces · One Container · Matched Finish",
        "tag_zh": "五件成套 · 一柜出货 · 同色同木",
        "lead_en": "Reformer, ladder barrel, Wunda chair, spine corrector and Cadillac in one "
                   "matched order — same timber, same leather, same hardware finish. The fastest "
                   "way to equip a new studio, and the cleanest way to keep a showroom consistent.",
        "lead_zh": "核心床、梯桶、稳踏椅、矫正器与凯迪拉克床一次配齐 —— 同木种、同皮革、同五金表面处理。"
                   "新馆最快落地的方案，也是展厅配置最统一的方案。",
    },
    {
        "key": "pilates-specialty",
        "en": "Pilates Specialty",
        "zh": "普拉提特殊器械",
        "tag_en": "Bidirectional Bed · Rotator & Tower Set",
        "tag_zh": "双向梯床 · 回旋仪塔架",
        "lead_en": "Beyond the five classical pieces: the bidirectional ladder bed for high-volume "
                   "rehab and the rotator + pulley tower set for three-dimensional "
                   "spinal work. Built to order on the same timber platform as the rest of the range.",
        "lead_zh": "五件套之外的两件：面向高频康复的双向梯床，以及做三维脊柱训练的回旋仪 + 滑轮塔组合"
                   "。与其余器械共用同一套实木工艺，按单定制。",
    },
]

# ---------------------------------------------------------------- 木种词典
WOOD = {
    "橡胶木": ("Domestic rubberwood", "国产橡胶木"),
    "进口橡胶木": ("Imported rubberwood", "进口橡胶木"),
    "进口橡胶木三合一": ("Imported rubberwood", "进口橡胶木"),
    "泰国5A级橡胶木": ("Thai 5A-grade rubberwood", "泰国 5A 级橡胶木"),
    "钢琴烤漆白枫木": ("Piano-lacquer white maple", "钢琴烤漆白枫木"),
    "FAS白枫木": ("FAS-grade white maple", "FAS 级白枫木"),
    "FAS白枫木三合一": ("FAS-grade white maple", "FAS 级白枫木"),
    "克罗地亚榉木": ("Croatian beech", "克罗地亚榉木"),
    "铝合金": ("Aluminium alloy", "铝合金"),
    "高强度316钢料": ("High-strength 316 steel", "高强度 316 钢"),
    "白枫木+多层板": ("White maple + plywood", "白枫木 + 多层板"),
    "美款全进口": ("Fully imported M-series frame", "美款 M 系列全进口框架"),
    "韩国配件": ("M-series frame · Korean components", "M 系列框架 · 韩国配件"),
    "国际大牌": ("White maple", "白枫木"),
    "进口原版": ("High-strength 316 steel frame", "高强度 316 钢架"),
    "国产进口配件": ("High-strength 316 steel frame", "高强度 316 钢架"),
}

SPRING = {
    "德国瓦格纳弹簧": ("German Wagner springs", "德国瓦格纳弹簧"),
    "德国A级瓦格纳钢琴丝弹簧": ("German A-grade Wagner piano-wire springs", "德国 A 级瓦格纳琴钢丝弹簧"),
    "德国琴钢丝弹簧": ("German piano-wire springs", "德国琴钢丝弹簧"),
    "国产碳钢弹簧": ("Domestic carbon-steel springs", "国产碳钢弹簧"),
    "国产琴钢丝弹簧": ("Domestic piano-wire springs", "国产琴钢丝弹簧"),
    "韩国象牌钢弹簧": ("Korean Sangbo steel springs", "韩国象牌钢弹簧"),
}

# PDF 里尺寸带中文注解（床高/折叠尺寸），正则吃不干净，逐个写明中英
SIZE_OVERRIDE = {
    "NLH201": ("2.42 × 0.63 × 1.98 m (bed height 43 cm)", "2.42 × 0.63 × 1.98 m（床高 43 cm）"),
    "NLH202": ("2.42 × 0.63 × 1.98 m (bed height 43 cm)", "2.42 × 0.63 × 1.98 m（床高 43 cm）"),
    "NLH601": ("2.3 × 0.62 × 0.31 m · folded 1.25 × 0.62 × 0.42 m",
               "展开 2.3 × 0.62 × 0.31 m · 折叠 1.25 × 0.62 × 0.42 m"),
    "NLH602": ("2.3 × 0.62 × 0.31 m · folded 1.25 × 0.62 × 0.42 m",
               "展开 2.3 × 0.62 × 0.31 m · 折叠 1.25 × 0.62 × 0.42 m"),
    # PDF 原文把备注/弹簧描述写进了「尺寸：」行，需拆干净（英文列不得留中文）
    #   原文：尺寸：2.2*0.69*2m，木板到地面高度60CM
    "NIX101": ("2.2 × 0.69 × 2 m (mat platform height 60 cm)",
               "2.2 × 0.69 × 2 m（床面离地 60 cm）"),
    #   原文：尺寸：2.2*0.7*2m1   （国产琴钢丝弹簧）  ← 弹簧信息归 Springs 列，2m 后的 1 是 PDF 残留
    "NIK201": ("2.2 × 0.7 × 2 m", "2.2 × 0.7 × 2 m"),
}

# 编号 → (族 / 英文名 / 中文名 / 木种键 / 英文标签)
MODELS = [
    ("NIC101", "pilates-reformer", "Rubberwood Reformer — Australian Style (Value Line)",
     "橡胶木核心床（澳版·特价款）", "橡胶木", "Value line"),
    ("NIC102", "pilates-reformer", "Imported Rubberwood Reformer — Australian Style",
     "进口橡胶木核心床（澳版）", "进口橡胶木", "Best seller"),
    ("NIC103", "pilates-reformer", "Imported Rubberwood Reformer — European Style",
     "进口橡胶木核心床（欧版）", "进口橡胶木", "European geometry"),
    ("NIC201A", "pilates-reformer", "Piano-Lacquer White Maple Reformer — Australian Style",
     "钢琴烤漆白枫木核心床（澳版）", "钢琴烤漆白枫木", "Piano lacquer"),
    ("NIC301", "pilates-reformer", "FAS White Maple Reformer — Australian Style",
     "FAS 白枫木核心床（澳版）", "FAS白枫木", "FAS grade"),
    ("NIC302", "pilates-reformer", "FAS White Maple Full-Track Reformer",
     "FAS 白枫木全轨道核心床", "FAS白枫木", "Full track"),
    ("NIC201B", "pilates-reformer", "Croatian Beech Reformer — European Style",
     "克罗地亚榉木核心床（欧版）", "克罗地亚榉木", "European geometry"),
    ("NIC303", "pilates-reformer", "FAS White Maple Reformer — European Style",
     "FAS 白枫木核心床（欧版）", "FAS白枫木", "FAS grade"),
    ("NIC202", "pilates-reformer", "Piano-Lacquer White Maple Reformer — European Style",
     "钢琴烤漆白枫木核心床（欧版）", "钢琴烤漆白枫木", "Piano lacquer"),
    ("NLH101", "pilates-reformer", "Black Knight Reformer",
     "黑武士核心床", "国际大牌", "Best seller"),
    ("NLH102", "pilates-reformer", "Black Knight Reformer with Half Tower",
     "黑武士核心床 + 半高架", "国际大牌", "Best seller"),
    ("NLH201", "pilates-reformer", "Black Knight Reformer with Half Tower — Gen 1",
     "黑武士核心床 + 半高架（一代）", "国际大牌", "Gen 1"),
    ("NLH202", "pilates-reformer", "Black Knight Reformer with Half Tower — Gen 2",
     "黑武士核心床 + 半高架（二代）", "国际大牌", "Gen 2"),
    ("NIM101", "pilates-reformer", "M-Series Super Reformer — Fully Imported",
     "美款 M 系列超模机（全进口）", "美款全进口", "M-series"),
    ("NIM102", "pilates-reformer", "M-Series Super Core Machine — Fully Imported",
     "美款 M 系列超核机（全进口）", "美款全进口", "M-series"),
    ("NIM103", "pilates-reformer", "M-Series Super Reformer — Korean Components",
     "美款 M 系列超模机（韩国配件）", "韩国配件", "M-series"),
    ("NLH501", "pilates-reformer", "Aluminium Full-Track Reformer",
     "铝合金全轨道核心床", "铝合金", "Full track"),
    ("NLH601", "pilates-reformer", "Aluminium Foldable Reformer — White Frame",
     "铝合金折叠小白床", "铝合金", "Foldable"),
    ("NLH602", "pilates-reformer", "Aluminium Foldable Reformer — Black Frame",
     "铝合金折叠小黑床", "铝合金", "Foldable"),
    ("NLH801", "pilates-reformer", "Aluminium Compact Studio Reformer",
     "铝合金小白床", "铝合金", "Compact"),

    ("NIX105", "pilates-reformer-tower", "Rubberwood 3-in-1 Reformer with Tower",
     "进口橡胶木三合一核心床", "进口橡胶木三合一", "3-in-1"),
    ("NIK301", "pilates-reformer-tower", "FAS White Maple 3-in-1 Reformer with Tower",
     "FAS 白枫木三合一核心床", "FAS白枫木三合一", "3-in-1"),
    ("NLH302", "pilates-reformer-tower", "Steel Half Tower — Imported Original",
     "进口原版半高架（高强度 316 钢）", "高强度316钢料", "Imported original"),
    ("NLH301", "pilates-reformer-tower", "Steel Half Tower — Domestic / Imported Mix",
     "国产进口配件半高架（高强度 316 钢）", "高强度316钢料", "Value line"),

    ("NIX101", "pilates-cadillac", "Rubberwood Cadillac (Trapeze Table)",
     "进口橡胶木凯迪拉克床", "泰国5A级橡胶木", "10 tower springs"),
    ("NIK201", "pilates-cadillac", "Piano-Lacquer White Maple Cadillac",
     "钢琴烤漆白枫木凯迪拉克床", "钢琴烤漆白枫木", "10 tower springs"),
    ("NIK306", "pilates-cadillac", "FAS White Maple Cadillac",
     "FAS 白枫木凯迪拉克床", "FAS白枫木", "10 tower springs"),

    ("NIX102", "pilates-wunda-chair", "Rubberwood Wunda Chair",
     "进口橡胶木稳踏椅", "泰国5A级橡胶木", "4 springs"),
    ("NIK203", "pilates-wunda-chair", "Piano-Lacquer White Maple Wunda Chair",
     "钢琴烤漆白枫木稳踏椅", "钢琴烤漆白枫木", "4 springs"),
    ("NIK303", "pilates-wunda-chair", "FAS White Maple Wunda Chair",
     "FAS 白枫木稳踏椅", "FAS白枫木", "4 springs"),

    ("NIX103", "pilates-ladder-barrel", "Rubberwood Ladder Barrel",
     "进口橡胶木梯桶", "泰国5A级橡胶木", "Adjustable rung"),
    ("NIK202", "pilates-ladder-barrel", "Piano-Lacquer White Maple Ladder Barrel",
     "钢琴烤漆白枫木梯桶", "钢琴烤漆白枫木", "Adjustable rung"),
    ("NIK302", "pilates-ladder-barrel", "FAS White Maple Ladder Barrel",
     "FAS 白枫木梯桶", "FAS白枫木", "Adjustable rung"),

    ("NIX104", "pilates-spine-corrector", "Rubberwood Spine Corrector",
     "进口橡胶木矫正器", "泰国5A级橡胶木", "Dowel included"),
    ("NIK205", "pilates-spine-corrector", "Piano-Lacquer White Maple Spine Corrector",
     "钢琴烤漆白枫木矫正器", "钢琴烤漆白枫木", "Dowel included"),
    ("NIK305", "pilates-spine-corrector", "FAS White Maple Spine Corrector",
     "FAS 白枫木矫正器", "FAS白枫木", "Dowel included"),

    ("NIW101", "pilates-studio-set", "Rubberwood Studio Set — 5 Pieces",
     "橡胶木五件套", "橡胶木", "5 pieces"),
    ("NIW201", "pilates-studio-set", "Piano-Lacquer White Maple Studio Set — 5 Pieces",
     "钢琴烤漆白枫木五件套", "钢琴烤漆白枫木", "5 pieces"),
    ("NIW301", "pilates-studio-set", "FAS White Maple Studio Set — 5 Pieces",
     "FAS 白枫木五件套", "FAS白枫木", "5 pieces"),

    ("NIS101", "pilates-specialty", "FAS White Maple Bidirectional Ladder Bed",
     "FAS 白枫木双向梯床", "FAS白枫木", "Rehab bed"),
    ("NIS102", "pilates-specialty", "FAS White Maple Rotator & Tower Set (Classic)",
     "FAS 白枫木回旋仪 + 滑轮塔（经典款）", "白枫木+多层板", "Rotator + pulley tower"),
]

# 规格条目里的通用件（几乎每款都有）→ 英文标准描述
COMMON = {
    "脚踏板": ("Foot bar", "脚踏板"),
    "脚蹬板": ("Foot plate", "脚蹬板"),
    "带方盒": ("Box included", "含方盒"),
    "靜音磨砂滑轮": ("Silent frosted rollers", "静音磨砂滑轮"),
    "静音磨砂滑轮": ("Silent frosted rollers", "静音磨砂滑轮"),
    "内置轴承": ("Sealed bearings", "内置轴承"),
    "超纤皮革": ("Microfibre leather", "超纤皮革"),
    "加厚皮革": ("Thickened leather", "加厚皮革"),
    "PU皮革": ("PU leather", "PU 皮革"),
    "生态硅胶皮革": ("Eco silicone leather", "生态硅胶皮革"),
    "聚氨酯海绵": ("Polyurethane foam", "聚氨酯海绵"),
    "不锈钢轨道": ("Stainless-steel rails", "不锈钢轨道"),
    "不锈钢配件": ("Stainless-steel hardware", "不锈钢配件"),
    "不锈钢管": ("Stainless-steel tube", "不锈钢钢管"),
    "三档挂簧板": ("3-position spring bar", "三档挂簧板"),
    "木箱独立包装": ("Individually crated in a wooden case", "木箱独立包装"),
    "纸箱独立包装": ("Individually boxed", "纸箱独立包装"),
}


def pick_wood(head, bullets):
    for h in head:
        if h in WOOD:
            return h
    for b in bullets:
        for k in WOOD:
            if k in b:
                return k
    return None


COLOR_EN = {"红": "red", "绿": "green", "黄": "yellow", "白": "white", "蓝": "blue"}
COLOR_RE = re.compile(r"(\d+)\s*([红绿黄白蓝])")


def norm_size(raw):
    """2.35*0.68*0.38m → 2.35 × 0.68 × 0.38 m；双规格用 / 分隔。"""
    s = raw.strip()
    if "/" in s and re.match(r"^[0-9.\s\*×x/m]+$", s):
        return " / ".join(norm_size(x) for x in s.split("/") if x.strip())
    m = re.match(r"^([0-9.\s\*×x]+?)\s*(m|cm|mm)?$", s)
    if not m:
        return s
    dims = re.split(r"\s*[\*×x]\s*", m.group(1).strip())
    unit = m.group(2) or ""
    return " × ".join(d for d in dims if d) + (" " + unit if unit else "")


def size_of(bullets):
    for b in bullets:
        m = re.search(r"尺寸[：:]\s*(.+)$", b)
        if m:
            return norm_size(m.group(1))
    return None


def colors_en(zh):
    if not zh:
        return None
    parts = COLOR_RE.findall(zh)
    if parts:
        return " / ".join("%s %s" % (n, COLOR_EN[c]) for n, c in parts)
    return zh


SPRING_SEG = re.compile(r"[，,、；;]")
SPRING_COLOR = re.compile(r"[（(]([^）)]*[红绿黄白蓝][^）)]*)[）)]")
# 弹簧名称（PDF 会区分「核心床弹簧」「高架弹簧」）
SPRING_NAME = {
    "核心床弹簧": ("Reformer springs", "核心床弹簧"),
    "高架弹簧": ("Tower springs", "高架弹簧"),
    "稳踏弹簧": ("Wunda Chair springs", "稳踏椅弹簧"),
    "普拉提弹簧": ("Reformer springs", "普拉提弹簧"),
}


def _src_in(text):
    """取文本中位置最靠前的弹簧来源词 —— 同句并列两种说法时以先出现者为准
    （如 NIK203「国产碳钢弹簧4根 (2红2绿)   （国产琴钢丝弹簧）」是 PDF 自身矛盾）。"""
    hits = [(text.find(k), k) for k in SPRING if k in text]
    return min(hits)[1] if hits else None


def springs_of(bullets):
    """返回弹簧条目列表。PDF 的弹簧写法五花八门，且**一句里可能出现多种弹簧**：
       核心床弹簧6根（2红2绿2黄）  ，高架弹簧10根(2红4绿4黄)   ← 一条两句、两种弹簧（NIX105）
       4根稳踏弹簧（2红2绿）（德国瓦格纳弹簧）                 ← 根数在「弹簧」前
       高架弹簧10根，木箱独立包装（德国瓦格纳弹簧）            ← 根数与来源被逗号隔开（NIK306）
       加厚PU皮革…高架弹簧10根(2红4绿4黄)木箱独立包装          ← 来源写在另一句里（NIK201）
    ⚠️ 旧实现只 re.search 第一个匹配，导致 NIX105 漏掉「高架弹簧10根」、NIK306 漏掉根数。
    """
    items, pending = [], []
    for b in bullets:
        if "弹簧" not in b:
            continue
        for seg in SPRING_SEG.split(b):
            if "弹簧" not in seg:
                continue
            m = (re.search(r"弹簧\s*(\d+)\s*根", seg)
                 or re.search(r"(\d+)\s*根[^，,）)]{0,10}?弹簧", seg))
            if not m:
                s = _src_in(seg)          # 只写来源、不写根数 → 记为兜底来源
                if s:
                    pending.append(s)
                continue
            col = SPRING_COLOR.search(seg)
            nm = next((k for k in SPRING_NAME if k in seg), None)
            items.append({
                "name_en": SPRING_NAME[nm][0] if nm else None,
                "name_zh": SPRING_NAME[nm][1] if nm else None,
                "count": int(m.group(1)),
                "colors_zh": col.group(1) if col else None,
                "colors_en": colors_en(col.group(1)) if col else None,
                "source_zh": _src_in(seg),
            })
    fb = pending[0] if pending else None
    for i, it in enumerate(items):
        if not it["source_zh"]:
            it["source_zh"] = fb or next(
                (x["source_zh"] for x in reversed(items[:i]) if x["source_zh"]), None)
    if not items and fb:                  # 全篇只写来源不写根数（M 系列）
        items = [{"name_en": None, "name_zh": None, "count": None,
                  "colors_zh": None, "colors_en": None, "source_zh": fb}]
    for it in items:
        it["source_en"] = SPRING[it["source_zh"]][0] if it["source_zh"] else None
    seen, kept = set(), []
    for it in items:
        k = (it["name_zh"], it["count"], it["colors_zh"], it["source_zh"])
        if k in seen:
            continue
        seen.add(k)
        kept.append(it)
    return kept


# 五件套 / 回旋仪塔架：尺寸写在「1、核心床：…」这种分行里，或一组设备有两个尺寸
COMPONENTS = {
    "NIW101": [("Reformer", "核心床", "2.35 × 0.7 × 0.35 m"),
               ("Ladder Barrel", "梯桶", "1.13 × 0.69 × 1.03 m"),
               ("Wunda Chair", "稳踏椅", "0.7 × 0.56 × 1 m"),
               ("Spine Corrector", "矫正器", "0.9 × 0.4 × 0.3 m"),
               ("Cadillac", "凯迪拉克床", "2.2 × 0.69 × 2 m")],
    "NIS102": [("Rotator", "回旋仪", "1650 × 590 × 900 mm"),
               ("Pulley tower", "滑轮塔", "1980 × 1170 × 1990 mm")],
}
COMPONENTS["NIW201"] = COMPONENTS["NIW101"]
COMPONENTS["NIW301"] = COMPONENTS["NIW101"]


def features_of(bullets):
    """去重后的通用件清单（中英成对），供规格表「Included」行使用。"""
    out, seen = [], set()
    for b in bullets:
        for k, (en, zh) in COMMON.items():
            if k in b and zh not in seen:
                seen.add(zh)
                out.append((en, zh))
    return out


def main():
    raw = json.load(open(RAW, encoding="utf-8"))
    by_no = {}
    for r in raw:
        key = "%s#%d" % (r["code"], r["no"])
        by_no[key] = r

    models = []
    for i, (code, fam, en, zh, wood_key, tag) in enumerate(MODELS):
        # NIC201 出现两次（澳版序号 4 / 欧版序号 7），用 A/B 后缀区分
        if code == "NIC201A":
            r = by_no["NIC201#4"]
        elif code == "NIC201B":
            r = by_no["NIC201#7"]
        else:
            cands = [v for k, v in by_no.items() if k.startswith(code + "#")]
            r = cands[0]
        bullets = r["bullets"]
        w = WOOD[wood_key]
        sp = springs_of(bullets)
        wood_final = w
        if "316钢料" in "".join(bullets) and wood_key == "高强度316钢料":
            wood_final = WOOD["高强度316钢料"]
        comps = COMPONENTS.get(code.rstrip("AB") if code.startswith("NIC201") else code)
        sz = size_of(bullets)
        sz_en = sz_zh = sz
        plain = code.rstrip("AB") if code.startswith("NIC201") else code
        if plain in SIZE_OVERRIDE:
            sz_en, sz_zh = SIZE_OVERRIDE[plain]
        if comps:
            sz_en = sz_zh = None   # 尺寸已拆进 components，避免同一事实写两遍
        models.append({
            "code": code.rstrip("AB") if code.startswith("NIC201") else code,
            "variant": {"NIC201A": "A", "NIC201B": "B"}.get(code),
            "family": fam,
            "en": en, "zh": zh,
            "tag_en": tag, "tag_zh": None,
            "wood_en": wood_final[0], "wood_zh": wood_final[1],
            "size_en": sz_en, "size_zh": sz_zh,
            "components": ([{"en": a, "zh": b, "size": c} for a, b, c in comps]
                           if comps else None),
            "springs": sp,
            "features": [{"en": a, "zh": b} for a, b in features_of(bullets)],
            "spec_zh": bullets,
            "src_row": r["no"], "src_page": r["page"],
        })

    fam_out = []
    for f in FAMILIES:
        ms = [m for m in models if m["family"] == f["key"]]
        f2 = dict(f)
        f2["models"] = ms
        f2["count"] = len(ms)
        fam_out.append(f2)

    data = {"source": "2026年福建三梵普拉提大器械价格表（代理）",
            "price_policy": "报价表代理价不入站，页面统一 Request a quote",
            "total_models": len(models),
            "families": fam_out}
    json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("型号 %d 个 / 器械族 %d 个 → %s" % (len(models), len(fam_out), OUT))
    for f in fam_out:
        print("  %-24s %2d  %s" % (f["key"], f["count"], f["en"]))
    miss = [m["code"] for m in models if not m["size_en"] and not m["components"]]
    if miss:
        print("  ⚠️ 缺尺寸:", miss)
    nosize = [m["code"] for m in models if not m["springs"]]
    if nosize:
        print("  ⚠️ 缺弹簧信息:", nosize)


if __name__ == "__main__":
    main()
