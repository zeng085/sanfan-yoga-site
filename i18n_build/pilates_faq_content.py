#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0-A 数据源：/pilates/ 板块 9 页的 FAQ 内容（EN 源 + ZH 手写），
其余 5 语言（de/ja/ko/fr/it/es）由 i18n_build/translator.py（DeepL）从 EN 译出并落盘缓存。

设计约束（踩过的坑，勿改）：
1. **占位符只用两个**：XXFAMILYXX（族名，取自各语言页自身的 Product name）与 XXMODELSXX（型号数）。
   经实测 DeepL 会原样保留全大写 token。占位符只放在**同位语位置**（h2 标题 / 从句），
   不塞进德语介词短语之类的位置 —— 否则代入后语法会崩。
2. 问题句尽量**不带族名**，用 "this line" / "these models" 指代，跨语言语法才安全。
3. 只用站内已有事实：7 个工作日实物打样、澳式/欧式两种结构、木料选项、REACH/CA Prop 65/6P-7P、
   ISO 9001/BSCI、木箱与纸箱包装、FOB/EXW/DDP、FBA 标签。
   ⚠️ **不写任何 MOQ 数字与价格** —— 普拉提代理价表属商业机密，不上站。
"""

# (EN_Q, EN_A, ZH_Q, ZH_A)
CORE = [
    (
        "What is the minimum order quantity for a private-label run?",
        "MOQ is quoted per model and finish, because frame timber, spring set and upholstery "
        "each change the run length. Tell us the model number and the quantity you have in "
        "mind and we return the exact minimum for that build — starting with a single model "
        "is normal, you do not have to take the whole line.",
        "私标订单的最小起订量是多少？",
        "起订量按型号与工艺单独核算 —— 木料、弹簧组、皮革包覆各自都会改变单次生产批量。"
        "告诉我们型号与意向数量，我们给出该配置的准确起订量；从单一型号起步是常态，"
        "不必整条产品线一起下单。",
    ),
    (
        "How fast can I get a sample?",
        "A physical sample takes 7 working days, so you can sign off the geometry, timber "
        "finish and upholstery before committing. Specification sheets and photos covering "
        "all XXMODELSXX models in this line are available immediately if you want to "
        "shortlist first.",
        "样品多久能拿到？",
        "实物样品 7 个工作日交付，便于在下单前确认结构尺寸、木作工艺与皮革包覆。"
        "若想先筛选，本线全部 XXMODELSXX 个型号的规格书与实拍图可立即提供。",
    ),
    (
        "What can be customized?",
        "Your logo on the frame, your colour and upholstery spec, your own model numbering "
        "and spec sheet, and the geometry itself — Australian and European builds are both "
        "in production. Cartons and crates can carry your artwork, and we can work to a "
        "specification you already have.",
        "可以定制哪些内容？",
        "床架打您的 Logo、按您的配色与皮革规格、用您的型号编号与规格书，结构本身也可调整 "
        "—— 澳式与欧式两种结构均在产。纸箱与木箱可印您的品牌画面，也可按您现有的规格书执行。",
    ),
    (
        "Are the materials and compliance documents suitable for the US and EU?",
        "Material is set per model — see the material column in the model table above for "
        "the code you are considering; we machine in solid timber, aluminium and steel. For "
        "OEM and ODM programmes we build to the material and finish specification your own "
        "brand already uses. Rails, springs and bearings are specified for studio duty. "
        "Products are tested against REACH, CA Prop 65 and 6P/7P, and the factory is "
        "ISO 9001 and BSCI audited. Test reports ship with the order.",
        "材料与合规文件能满足美国与欧盟要求吗？",
        "材质按型号确定——请见上方型号表中该编号对应的材质列；我们的加工覆盖实木、"
        "铝合金与钢材。OEM/ODM 项目可直接按你品牌现用的材质与表面工艺生产。导轨、弹簧"
        "与轴承按场馆级使用选型。产品按 REACH、加州 65 号提案与 6P/7P 送检，工厂通过 "
        "ISO 9001 与 BSCI 审核，检测报告随货提供。",
    ),
    (
        "How is it packed and shipped?",
        "Complete apparatus ships in an individual wooden crate; foldable and aluminium "
        "models travel in cartons. We quote FOB, EXW or DDP, can label cartons for Amazon "
        "FBA, and a single container can mix models from this line, so a first order can be "
        "spread across your best-selling pieces.",
        "包装与运输怎么走？",
        "整机木箱独立包装，折叠款与铝合金款走纸箱。可按 FOB / EXW / DDP 报价，"
        "可按需贴亚马逊 FBA 标签；一个柜子可以混装本线的多个型号，"
        "首单可以铺在您最好卖的几款上。",
    ),
]

# 每页第 6 问（族专属），键 = 页面相对路径
FAMILY_QA = {
    "pilates/pilates-reformer.html": (
        "Australian or European geometry — which should my studio order?",
        "Both are in production. Australian builds favour a longer, flatter carriage travel "
        "and are the default in Australia, New Zealand and much of Asia; European builds "
        "tighten the frame and change the footbar and riser geometry to the EU studio "
        "standard. If you supply one market, match that market's incumbent machines so "
        "clients feel at home; if you sell across regions, carry one of each.",
        "澳式与欧式结构，我的馆该订哪种？",
        "两种都在产。澳式行程更长、床面更平，是澳新与亚洲多数市场的默认选择；"
        "欧式收紧了框架，并调整脚踏杆与升降柱结构，贴合欧洲场馆的通用标准。"
        "只供单一市场就跟着当地主流机型走，客户上手无障碍；若同时供多个区域，两种各备一台。",
    ),
    "pilates/pilates-reformer-tower.html": (
        "Can I add the tower later to a reformer I already own?",
        "Yes — the half tower bolts to the end of the reformer, which is why the tower and "
        "3-in-1 versions share the same frame families. Ordering the reformer first and the "
        "tower later is a normal pattern; the mounting points are standard, so the two "
        "orders stay compatible.",
        "已有的核心床，以后能加装塔架吗？",
        "可以 —— 半塔架通过螺栓固定在床尾，这正是塔架款、三合一款与核心床共用床架的原因。"
        "先订核心床、后补塔架是常见做法，安装孔位是标准化的，两次订货互相兼容。",
    ),
    "pilates/pilates-cadillac.html": (
        "Does a Cadillac ship assembled?",
        "No — it ships knocked down in a crate, with the frame, trapeze and spring bars "
        "packed separately, and it reassembles with basic hand tools. Allow a few hours for "
        "two people. We supply the assembly drawing and can walk your installer through it "
        "on a call.",
        "凯迪拉克床是整机发货吗？",
        "不是 —— 拆散木箱包装，床架、吊架与弹簧杆分开放置，用常规手工具即可组装。"
        "两人组装数小时可完成，我们提供装配图，也可以电话指导您的安装师傅。",
    ),
    "pilates/pilates-ladder-barrel.html": (
        "Is the ladder barrel adjustable for different body sizes?",
        "Yes — the ladder rung slides and locks along its track, so one unit serves a wide "
        "range of students. That adjustability is what lets the same barrel work in a group "
        "class and in one-to-one rehab, where the machine has to fit both a 1.5 m and a "
        "1.9 m client.",
        "梯桶能适配不同身材的学员吗？",
        "能 —— 梯档沿轨道滑动并锁定，一台设备可覆盖身材跨度很大的学员。"
        "这种可调性正是梯桶既能上团课、又能做一对一康复的原因 —— "
        "同一台机器要同时适配 1.5 米与 1.9 米的客户。",
    ),
    "pilates/pilates-wunda-chair.html": (
        "How much floor space does a Wunda chair need?",
        "It is the smallest piece in the classical set — roughly the footprint of a dining "
        "chair plus clearance for the pedal to swing. That is why it is the usual first "
        "purchase for a small studio or a home practice room, and why clinics pair it with a "
        "reformer rather than starting from a Cadillac.",
        "稳踏椅需要多大场地？",
        "它是古典器械中占地最小的一件 —— 大致是一把餐椅的投影面积，再加踏板摆动的活动量。"
        "这也是小馆或家庭练习室通常先买它的原因；康复机构则常把它与核心床搭配，"
        "而不是一开始就上凯迪拉克床。",
    ),
    "pilates/pilates-spine-corrector.html": (
        "Is the spine corrector suitable for a home studio?",
        "Yes — it is a mat and a barrel in one, takes about the space of a large yoga mat, "
        "and needs no springs or frame assembly. Studios buy it alongside a reformer; home "
        "and small-class buyers often start with it alone because it covers much of the mat "
        "repertoire.",
        "矫正器适合家用工作室吗？",
        "适合 —— 它等于垫上器械与桶的结合，占地约一张大瑜伽垫，不需要弹簧，也不需要拼装框架。"
        "场馆通常与核心床一起采购；家庭与小班客户常从它单独起步，"
        "因为垫上动作库的大部分都能覆盖。",
    ),
    "pilates/pilates-studio-set.html": (
        "Can I order a studio set in stages?",
        "Yes. The matched set is a freight and colour-consistency play, not a single "
        "mandatory order — many buyers start with the reformer and chair, add the barrel and "
        "corrector as class bookings fill, and take the Cadillac once advanced classes run. "
        "Every piece comes from the same finish range, so later deliveries still match.",
        "五件套能否分批下单？",
        "可以。配套下单主要是为了省运费与保证同色号，并非必须一次买齐 —— "
        "很多采购方先买核心床与稳踏椅，等排课满了再加桶类与矫正器，"
        "进阶课程跑起来后再上凯迪拉克床。因为全部来自同一套表面工艺，后续批次的颜色仍能对上。",
    ),
    "pilates/pilates-specialty.html": (
        "What is the bidirectional ladder bed used for?",
        "It is built for high-volume rehab and clinical work: the bed runs both ways so a "
        "practitioner can reposition a client without turning the machine around, and the "
        "ladder rungs give progressive resistance for spine and shoulders. It is the piece "
        "physio clinics order when a Cadillac is too tall or too fixed for the room.",
        "双向梯床是做什么用的？",
        "它面向高频康复与临床场景：床面可双向运行，理疗师无需掉转机身即可调整客户体位；"
        "梯档提供脊柱与肩部的渐进阻力。当场地放不下凯迪拉克床（太高或太固定）时，"
        "康复机构通常会选它。",
    ),
    "pilates/index.html": (
        "Where should a new studio start when buying Pilates apparatus?",
        "Start with the reformer — it carries the largest share of the classical repertoire "
        "and most of your class revenue. Add a Wunda chair for one-to-one sessions, a ladder "
        "barrel and spine corrector for mat and mobility work, and a Cadillac once you run "
        "advanced or rehab classes. All eight lines here are built in the same finish range, "
        "so pieces bought a year apart still match.",
        "新开馆采购普拉提器械，应该从哪里开始？",
        "从核心床开始 —— 它承载古典动作库中最大的份额，也是课程收入的主力。"
        "做一对一再加稳踏椅；垫上与灵活性训练加梯桶与矫正器；"
        "开进阶或康复课再上凯迪拉克床。这里的八条产品线采用同一套表面工艺，"
        "隔一年补货颜色依然一致。",
    ),
}

# 区块标题（XXFAMILYXX 代入各语言页自身的族名）
TITLE_EN = "XXFAMILYXX — buyer questions"
TITLE_ZH = "XXFAMILYXX —— 买家常问"

LANGS = ["de", "ja", "ko", "fr", "it", "es"]
FAQFILES = list(FAMILY_QA.keys())
