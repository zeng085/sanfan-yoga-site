#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""8 个一级分类页补「品类导语 + 买家 FAQ」—— 2026-09-25

【背景】
`audit_en_seo_standard_20260925.py` 逐页审计 191 个英文页后，这 8 个一级分类页
（foam-rollers / jump-ropes / resistance-bands / suede-cork-yoga-mats /
meditation-pilates-mats / yoga-props-accessories / strength-training / massage-recovery）
是词数缺口最大的一档：177–356 词，而分类页建议带宽是 600–1200。

根因不是「内容没法写」，而是**这几页从来没做过编辑内容**：零正文、零 FAQ、
零正文内链，整页只有 1 个 H2（尾部那个通用 CTA 标题）。同站 `tpe-yoga-mats.html`
已经把这件事做对了 → 本脚本复刻它的结构，不发明新版式。

【三块内容与实测词数（取自 tpe 页同构区块）】
  ① 品类导语 `<!-- catintro:v1 -->`         ≈ 233 词（eyebrow + H2 + 3 段）
  ② 买家 FAQ  `<!-- cfaq:v1 -->`             ≈ 240 词（H2 + 5 条 details）
  ③ FAQPage   `<!-- cfaq-ld:v1 -->`          结构化数据，随 ② 同步
  ③ 内链块由 `add_internal_links_20260925.py` 负责（含 `<!-- ilink:v1 -->`）
→ 合计约 475 英文词/页。补后最薄的 `jump-ropes` 177 → ~652，最厚的 `yoga-props` 356 → ~830，
  8 页全部落进 600–1200 带内。
⚠️ 只做 ②+③（约 300 词）不够：jump-ropes 177+300=477 < 600。**导语块是必需的**。

【⭐ 执行顺序不能换】
FAQ 的插入锚点写死是 `<!-- ilink:v1 -->`，而这 8 页原本**没有**任何标记 →
必须先跑 `add_internal_links_20260925.py` 造出锚点，否则本脚本 `s.index()` 直接抛异常。

【⭐ 导语块插在「产品网格之前」，不是网格之后】
初版把三块全排在网格之后（跟样板页一致），移动端实测发现那等于埋在页面底部：
390×844 下 `yoga-props`（23 张卡）导语落在**第 6.5 屏**、FAQ 第 7.5 屏；320px 视口 FAQ
落到**第 12 屏**。根因是产品网格自身就占 5.2 屏（4426px）。
把导语上移到网格之前后：导语 6.5 屏 → **1.2 屏**，FAQ/内链绝对位置不变。
FAQ 不上移的理由：它的价值主要在收录与 AI 引用（爬虫不看视觉位置），
且「看产品 → 有疑问 → 看问答」才是正常动线；若 FAQ 也上移，网格会掉到第 3 屏伤转化。

【内容口径 —— 事实纪律】
所有数字取自**本页自己**的 hero / 产品卡名 / CTA，一处不新造：
  · 页内已有：`MOQ 100 pcs`（meta + og + twitter + JSON-LD + CTA 共 5 处）、`7-day sampling`（4 处）
  · 页内**没有**：ROHS / CE / ISO 9001 / BSCI / SGS
    → 检测类问题一律写「按目标市场确认」，**不列标准号**（否则页面自我矛盾）
    （`REACH` 在本页只出现在全站实体层 `knowsAbout` 的通用能力列表里，不是本页认证声明）
  · 电池 / 充电 / 承重 / 认证类：写「下单前按目标市场确认」，不编数字
防模板化的硬抓手 = 每页挂**本页独有**的卡名事实（33/45 cm、34/32 cm、25 cm/10"、
5 × 2.8 m、6 Colours 等）。8 页都是配件类，极易写成同一骨架。

【⛔ 站内去重】
不碰 `materials`（4 问）/ `tpe`（5 问）/ `pu`（5 问）已答过的题；8 页之间也不互抄。

【原文写法上的两个坑（源文已按此规避）】
  1. 受保护数字**不能做主语**：
     ❌ "6 mm and 8 mm are the volume thicknesses" → ja 只剩「6 mmおよび8 mmは厚みです」
     ✅ "The best-selling thicknesses are 6 mm and 8 mm."（表语位置安全，已上线验证）
  2. 多个受保护术语连成逗号清单会塌：`ROHS, CE and REACH` 在 de 变成 `ROHS (CE) und REACH`。
     本脚本的 5 问里刻意不含标准号清单。

用法：
    python3 i18n_build/add_category_content_20260925.py --dry-run
    python3 i18n_build/add_category_content_20260925.py --apply
    python3 i18n_build/add_category_content_20260925.py --apply --langs de,ja,ko
    python3 i18n_build/add_category_content_20260925.py --check
"""
import argparse
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import translator  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = pathlib.Path(__file__).resolve().parent / "category_content_data.json"

LANGS = ["de", "ja", "ko", "fr", "it", "es"]

M_I_OPEN = "<!-- catintro:v1 -->"
M_I_CLOSE = "<!-- /catintro:v1 -->"
M_V_OPEN = "<!-- cfaq:v1 -->"
M_V_CLOSE = "<!-- /cfaq:v1 -->"
M_L_OPEN = "<!-- cfaq-ld:v1 -->"
M_L_CLOSE = "<!-- /cfaq-ld:v1 -->"

ILINK = "<!-- ilink:v1 -->"
ORGREF = "<!-- orgref:v1 -->"

# ==================================================================== 内容
# 每页：(eyebrow, h2, [3 段导语], (faq_h2, [(q_en,q_zh,a_en,a_zh) × 5]))
PAGES = {
    "foam-rollers.html": {
        "eyebrow": ("Foam Roller Guide", "泡沫轴选型"),
        "h2": ("Choosing the right foam roller for your range",
               "怎么给你的产品线挑泡沫轴"),
        "paras": [
            ("EVA and EPP are the two foams most rollers are made from, and they suit different "
             "customers. EVA is denser and feels firmer under load, which is what a physio or a "
             "serious lifter wants for deep-tissue work. EPP is lighter, springs back faster and "
             "holds its shape after repeated compression, so it carries high-turnover gym and "
             "studio orders. We run both on the same line, so you can sample the two side by side "
             "before committing to a range.",
             "泡沫轴最常用的是 EVA 与 EPP 两种发泡材质，面向的客户也不一样。EVA 密度更高、"
             "承压更硬，物理治疗师或重度训练者做深层放松就认这个手感；EPP 更轻、回弹更快，"
             "反复压过还能保持形状，适合走量快的健身房与瑜伽馆订单。两条线我们都在跑，"
             "你可以两种都打样，对比过再定产品线。"),
            ("Structure matters as much as material. Solid rollers are the default for deep-tissue "
             "compression. Hollow cores cut weight and freight on the long 45 cm (18\") format, "
             "which is the size most export orders ask for. A vibrating build adds a rechargeable "
             "motor for recovery studios and sports teams, and wolf-tooth or grid textures sit on "
             "top of any of them when a customer wants a firmer, more targeted surface. Our EVA "
             "rollers run at 30 cm, 33 cm and 45 cm, all on a 12.5 cm diameter.",
             "结构与材质同样重要。实心款是深层按压的默认选择；长款 45 cm（18\"）做空心能压重量、"
             "省运费，而这个尺寸正是出口订单问得最多的。震动款加了可充电电机，"
             "面向恢复工作室与运动队；狼牙纹或浮点纹则可以在任意结构上再叠一层更硬、"
             "更聚焦的表面。我们的 EVA 泡沫轴有 30 cm、33 cm、45 cm 三种长度，全系直径 12.5 cm。"),
            ("Everything on the spec sheet is set per order: density and hardness, length, colour, "
             "logo and packaging. Colourways can be matched to the mats on the same shipment, so "
             "the range reads as one collection instead of a pile of odds and ends. Tell us the "
             "density you want to hit and we will sample it — MOQ is 100 pcs and sampling runs "
             "about 7 days.",
             "规格表上每一项都按订单定：密度与软硬、长度、颜色、Logo 与包装。配色可以和同一批的"
             "垫子对上，让整条线看起来像一个系列，而不是一堆杂货。把你想要达到的密度告诉我们，"
             "我们打样给你 —— 100 片起订，约 7 天出样。"),
        ],
        "faq_h2": ("Foam roller questions buyers ask", "买家会问的泡沫轴问题"),
        "qa": [
            ("What is the difference between EVA and EPP foam rollers?",
             "EVA 和 EPP 泡沫轴有什么区别？",
             "EVA is denser and firmer, so it holds up under deep-tissue pressure and feels solid in "
             "the hand. EPP is lighter, rebounds faster and keeps its shape after repeated "
             "compression, which suits high-volume gym and studio orders. Both compounds run on the "
             "same line, so density and hardness are set to your brief either way.",
             "EVA 密度更高、更硬，扛得住深层按压，握在手里也更实。EPP 更轻、回弹更快，"
             "反复压过还能保持形状，适合走量大的健身房与瑜伽馆订单。两种材质同一条线生产，"
             "密度与软硬都能按你的要求调。"),
            ("Which lengths and diameters can you run?",
             "你们能做哪些长度和直径？",
             "Our EVA rollers run at 30 cm, 33 cm and 45 cm, all on a 12.5 cm diameter, and the "
             "45 cm (18\") format is the one most export orders ask for. Longer formats and "
             "non-standard diameters come off the same tooling family, so they need a quotation "
             "but no new mould.",
             "我们的 EVA 泡沫轴有 30 cm、33 cm、45 cm 三种长度，直径统一 12.5 cm，"
             "其中 45 cm（18\"）是出口订单问得最多的规格。更长的尺寸与非标直径与常规款"
             "共用同一套模具，所以只需要报价，不需要重新开模。"),
            ("How does the vibrating build work, and how is it charged?",
             "震动款是怎么工作的？怎么充电？",
             "A rechargeable motor sits inside the core and is switched on at the end cap. Run time, "
             "charge time and battery certification are confirmed per order, because different "
             "markets accept different cells. Tell us the destination market and we quote the "
             "version that clears import there.",
             "可充电电机装在轴芯内部，在端盖处开关。续航时间、充电时长与电池认证都按订单确认 —— "
             "不同市场接受的电池不一样。告诉我们目标市场，我们报的是能通过那边进口的版本。"),
            ("Can we change the density and hardness?",
             "密度和软硬能改吗？",
             "Yes. Density and hardness are set at the foaming stage rather than picked from a "
             "catalogue, so a firmer roller for clinical work or a softer one for beginners is a "
             "production parameter, not a different product. Send a sample of what you sell today "
             "and we will match it.",
             "可以。密度与软硬在发泡环节就定下来，不是从目录里挑现成的，"
             "所以临床用的硬款或新手用的软款只是一个生产参数，不是两个产品。"
             "把你现在在卖的样品寄来，我们照着做。"),
            ("What is the MOQ, and can the colours match our mats?",
             "起订量多少？颜色能和我们的垫子对上吗？",
             "MOQ is 100 pcs per colour and design, with sampling in about 7 days. Colourways can be "
             "matched to the mats on the same shipment, and the logo plus retail packaging are "
             "handled in the same production run.",
             "起订量 100 片／颜色与款式，约 7 天出样。配色可以和同一批的垫子对上，"
             "Logo 与零售包装都在同一次生产里做完。"),
        ],
    },

    "jump-ropes.html": {
        "eyebrow": ("Jump Rope Guide", "跳绳选型"),
        "h2": ("Building a jump rope range that sells", "怎么配一条好卖的跳绳产品线"),
        "paras": [
            ("There are three rope constructions and they are not interchangeable. PVC-coated cord "
             "is the volume seller — comfortable if it clips your shins, and fine for schools and "
             "general retail. Steel-wire rope is faster and takes far more wear, which is what "
             "competitive and CrossFit customers pay for. Beaded rope holds a visible arc in the "
             "air, so a beginner can see the rhythm instead of guessing at it. Name the customer "
             "and we will put the right core in front of you first.",
             "跳绳有三种绳芯结构，互不替代。PVC 包覆绳是走量款 —— 打到小腿也不疼，"
             "学校与大众零售都合适；钢丝绳更快、耐用得多，竞技与 CrossFit 客户就买这个；"
             "珠节绳在空中能拉出可见的弧线，新手看得见节奏，不用靠猜。"
             "先说清楚卖给谁，我们就把对的那一种先推给你。"),
            ("Counting splits the range just as sharply. Mechanical counters survive drops and need "
             "no battery; LCD counters give a clean readout and are the default for retail gift "
             "boxes; cordless builds have no rope at all, so someone can train in a flat without "
             "hitting the ceiling or the furniture. Handles run from a 12 cm kids' grip to a 19.3 cm "
             "adult format, so the same rope can be built for a child or for a competition.",
             "计数方式同样把产品线分得很开。机械计数器摔不坏、不用电池；"
             "LCD 计数读数清楚，是零售礼盒的默认选择；无绳款干脆没有绳子，"
             "在公寓里练也不会打到天花板或家具。握柄从 12 cm 的儿童款到 19.3 cm 的成人款，"
             "同一根绳可以做成给小孩的，也可以做成给比赛的。"),
            ("Rope length, grip colour, print and packaging are all set per order, and the counter "
             "housing can carry your logo. Kids' and adult formats come off the same line, so a "
             "school or a gym chain can order a mixed box as long as each variant meets the "
             "minimum. MOQ is 100 pcs, with sampling in about 7 days.",
             "绳长、握把颜色、印刷与包装全部按订单定，计数器的外壳上可以放你的 Logo。"
             "儿童款与成人款同一条线生产，所以学校或连锁健身房可以订混装箱，"
             "只要每个款式各满起订量。100 片起订，约 7 天出样。"),
        ],
        "faq_h2": ("Jump rope questions buyers ask", "买家会问的跳绳问题"),
        "qa": [
            ("Which rope core should we choose?",
             "绳芯该怎么选？",
             "PVC-coated cord for general retail and schools, steel wire for speed and competition, "
             "and beaded cord for beginners who need to see the arc. If you sell to more than one of "
             "those groups, order a sample of each and let the sell-through decide which one "
             "deserves the shelf space.",
             "PVC 包覆绳面向大众零售与学校，钢丝绳面向速度与竞技，"
             "珠节绳给需要看见弧线的新手。如果这几类客户你都在做，就各打一份样，"
             "让实际动销决定哪一个值得占货架。"),
            ("How many counting options are there?",
             "有几种计数方式？",
             "Three: mechanical, LCD and smart. Mechanical counters take the knocks and never need "
             "charging. LCD models are the retail default because the readout sells itself on a "
             "shelf. Cordless models have no rope at all, so they work in a flat where a full-length "
             "rope would hit the ceiling.",
             "三种：机械、LCD 与智能。机械计数器经摔，永远不用充电；"
             "LCD 款是零售默认选择，因为读数在货架上自己会说话；"
             "无绳款完全没有绳子，所以在一根整绳会打到天花板的公寓里照样练。"),
            ("Who buys the cordless version?",
             "无绳款卖给谁？",
             "Apartment and hotel customers, and anyone rehabilitating a joint who has been told to "
             "avoid impact. Because there is no rope, length stops being a constraint. The handle "
             "we build for this format is 19.3 cm long and 3.1 cm across.",
             "公寓住户、酒店客户，以及被叮嘱避免冲击、正在做关节康复的人。"
             "因为没有绳子，绳长就不再是限制。这一款我们做的握柄长 19.3 cm、直径 3.1 cm。"),
            ("Can the rope length and the grips be customised?",
             "绳长和握把能定制吗？",
             "Yes. Rope length is cut per order, grips run from a 12 cm kids' handle to a 14.8 cm or "
             "19.3 cm adult format, and the grip colour plus printed logo are set with the rest of "
             "the order. The counter housing can carry a logo as well.",
             "可以。绳长按订单裁，握柄从 12 cm 儿童款到 14.8 cm、19.3 cm 成人款都有，"
             "握把颜色与印刷 Logo 随整单一起定。计数器的外壳上也能放 Logo。"),
            ("What is the MOQ and what packing do you offer?",
             "起订量和包装是什么情况？",
             "MOQ is 100 pcs per variant, sampling in about 7 days. Rope, handles and packaging are "
             "produced in one run, and retail boxes, pouches and colour-matched sets are all "
             "available.",
             "每个款式 100 片起订，约 7 天出样。绳子、握柄与包装一次生产完成，"
             "零售盒、收纳袋与配色套装都能做。"),
        ],
    },

    "resistance-bands.html": {
        "eyebrow": ("Resistance Band Guide", "弹力带选型"),
        "h2": ("Resistance bands: material, shape and tension",
               "弹力带：材质、形态与阻力"),
        "paras": [
            ("Three materials cover almost every brief. TPE has no latex proteins and no rubber "
             "smell, which is what sells into clinics, schools and any market where a latex allergy "
             "has to be designed out. Natural latex stretches further and costs less per band, so it "
             "is still the choice for heavy resistance work. Silicone keeps its colour and does not "
             "go tacky, which suits retail sets that have to look presentable after a year on a "
             "shelf.",
             "三种材质几乎能覆盖所有需求。TPE 不含乳胶蛋白、没有胶味，"
             "适合诊所、学校，以及任何必须回避乳胶过敏的市场；天然乳胶拉伸幅度更大、"
             "单条成本更低，大阻力训练还是选它；硅胶不褪色、不发粘，"
             "适合要在货架上放一年还要好看的零售套装。"),
            ("Shape decides the exercise. Loop bands go round the thighs and knees for warm-ups and "
             "glute work. Tubes with handles take a foot pedal or a door anchor for pulling "
             "movements. Figure-8 bands fit in a pocket and isolate one arm or one leg. Power bands "
             "are the heavy, long-format tool for assisted pull-ups and squats. Each format is cut "
             "in its own standard size, from a 60 cm loop up to a 150 cm standing set.",
             "形态决定练什么。环形带绕在大腿和膝盖上做热身与臀腿；"
             "带把手的拉力管接脚踏或门扣，做各种拉的动作；8 字带能塞进口袋，"
             "单独练一侧手臂或腿；力量带是重型长款，做助力引体与深蹲。"
             "每种形态各有自己的标准尺寸，从 60 cm 的环形带到 150 cm 的站姿套装。"),
            ("Tension is graded rather than guessed: every format is produced in light, medium and "
             "heavy, and the grade is coded by colour so a customer can read it without a chart. "
             "Sets, printed logos and retail packaging all come out of one production run, and "
             "colours can be matched across the whole set so it photographs as a kit. MOQ is "
             "100 pcs, sampling in about 7 days.",
             "阻力是分级做出来的，不是猜的：每种形态都分轻、中、重三档，用颜色区分，"
             "客户不用看对照表就认得出。套装、印刷 Logo 与零售包装一次生产完成，"
             "整套配色可以统一，拍出来是一整套。100 片起订，约 7 天出样。"),
        ],
        "faq_h2": ("Resistance band questions buyers ask", "买家会问的弹力带问题"),
        "qa": [
            ("Should we use TPE or natural latex?",
             "用 TPE 还是天然乳胶？",
             "TPE if the product has to be latex-free — it has no latex proteins and no rubber "
             "smell, which clears it for clinics, schools and allergy-aware retail. Natural latex if "
             "you need maximum stretch at the lowest cost per band. Silicone sits between the two "
             "and keeps its appearance longest in a retail set.",
             "产品必须无乳胶就用 TPE —— 它不含乳胶蛋白、没有胶味，"
             "诊所、学校和在意过敏问题的零售都能上；需要最大拉伸幅度、单条成本最低就选天然乳胶；"
             "硅胶介于两者之间，在零售套装里外观保持得最久。"),
            ("How is the resistance graded?",
             "阻力怎么分级？",
             "Every format is produced in light, medium and heavy, and the grade is coded by colour "
             "so a customer can read it without a chart. Loop bands are thickness-graded at 0.8 mm, "
             "1.0 mm and 1.2 mm; the standing tube sets are width-graded at 0.35 mm, 0.45 mm and "
             "0.55 mm.",
             "每种形态都做轻、中、重三档，用颜色区分档位，客户不用看对照表就认得。"
             "环形带按厚度分级：0.8 mm、1.0 mm、1.2 mm；站姿拉力管套装按宽度分级："
             "0.35 mm、0.45 mm、0.55 mm。"),
            ("Which shape suits which customer?",
             "哪种形态适合哪类客户？",
             "Loops for classes, physio and warm-ups. Tubes with handles for home gyms, because they "
             "anchor to a door or a foot. Figure-8 for travel and single-limb work. Power bands for "
             "assisted pull-ups and squats, where the load is the point.",
             "环形带用于团课、康复与热身；带把手的拉力管用于家庭健身，可以固定在门上或踩在脚下；"
             "8 字带用于出差与单侧训练；力量带用于助力引体与深蹲这类以负重为目的的动作。"),
            ("Can you build a retail set with our branding?",
             "能做带我们品牌的零售套装吗？",
             "Yes. A set of three or five grades in a printed pouch or box, colour-matched, with "
             "your logo on the band and on the packaging, is one production run. Send the layout and "
             "we will confirm what prints cleanly on an elastic surface before you commit.",
             "可以。三档或五档的套装，装进印刷袋或印刷盒，整套配色统一，"
             "带身和包装上都印你的 Logo，一次生产完成。把版面发来，"
             "我们会先告诉你哪些内容在弹性表面上印出来是干净的，再让你决定。"),
            ("What is the MOQ?",
             "起订量是多少？",
             "MOQ is 100 pcs per colour and grade, with sampling in about 7 days. Mixed sets count "
             "per grade, so a five-band kit with 100 pcs of each grade is a standard order.",
             "每个颜色、每个档位 100 片起订，约 7 天出样。混装套装按档位分别计数，"
             "所以五档套装、每档 100 片是一张很常规的订单。"),
        ],
    },

    "suede-cork-yoga-mats.html": {
        "eyebrow": ("Suede and Cork Guide", "麂皮与软木选型"),
        "h2": ("Suede or cork: two surfaces, two stories",
               "麂皮还是软木：两种面层，两个卖点"),
        "paras": [
            ("Suede microfibre and natural cork are the two surfaces behind almost every "
             "design-led mat on the market, and they behave differently. Suede feels dry and soft, "
             "takes a high-definition print with real depth of colour, and grips harder as it gets "
             "damp — which is why heated studios specify it. Cork feels firmer and more grounded "
             "underfoot and sells on the material story rather than on the artwork.",
             "麂皮（超细纤维）与天然软木是市面上几乎所有设计驱动型垫子背后的两种面层，"
             "手感差异很大。麂皮干爽柔软，能印出有色彩深度的高清图案，而且越湿越防滑 —— "
             "高温教室点名要它就是这个原因。软木踩上去更实、更稳，卖的是材质本身，不是图案。"),
            ("The surface is only half the specification, because either one bonds to either base. "
             "Suede over natural rubber is the premium studio build, and suede over TPE gives the "
             "same print quality at a lighter weight and a lower landed cost. Cork pairs with "
             "rubber for the firmest feel, and cork over TPE brings the weight down for folding and "
             "travel formats.",
             "面层只是规格的一半，因为这两种面层都能贴两种底。麂皮配天然橡胶是高端馆用结构；"
             "麂皮配 TPE 印花品质一样，但更轻、到岸成本更低。软木配橡胶踩感最实，"
             "软木配 TPE 则把重量压下来，适合折叠款与旅行款。"),
            ("Prints are where this family earns its margin: gradients, botanical and geometric "
             "artwork, florals, and licensed or collaborative designs, reproduced across the full "
             "face. Foldable builds pack into a smaller box without the mat curling at the edges, "
             "which is what mail-order and travel customers ask for. Send the artwork and we will "
             "sample it — MOQ is 100 pcs, samples in about 7 days.",
             "印花是这一族赚利润的地方：渐变、植物、几何、花卉，以及联名或授权图案，"
             "都能满版印制。折叠款能装进更小的箱子，垫子边缘也不会卷起来，"
             "这是邮购与旅行客户点名要的。把设计稿发来我们打样 —— 100 片起订，约 7 天出样。"),
        ],
        "faq_h2": ("Suede and cork mat questions buyers ask", "买家会问的麂皮与软木垫问题"),
        "qa": [
            ("Suede or cork — how do we choose?",
             "麂皮还是软木，怎么选？",
             "Suede if the range is sold on artwork and colour, because it holds a print far better "
             "and gets grippier as it gets damp. Cork if the range is sold on material and "
             "sustainability, because the surface itself is the story. Many customers run both: "
             "cork as the anchor line and suede for the seasonal prints.",
             "靠图案和颜色卖的系列选麂皮 —— 它印花表现好得多，而且越湿越防滑；"
             "靠材质与环保概念卖的系列选软木 —— 面层本身就是故事。"
             "很多客户两条都做：软木当基石款，麂皮做季节性印花款。"),
            ("Why do these surfaces grip better when wet?",
             "为什么这两种面层遇汗更防滑？",
             "Microfibre suede absorbs moisture into the fibre and the surface tension rises, so the "
             "hand holds harder as the mat gets damp. Cork does the same through its own cellular "
             "structure. It is the reason both are specified for heated and dynamic classes.",
             "超细纤维麂皮把水分吸进纤维里，表面张力上升，所以越湿手按得越牢；"
             "软木靠自身的细胞结构达到同样的效果。这就是高温课与动态课都指定这两种面层的原因。"),
            ("Which base layers can we pair with them?",
             "可以配哪几种底？",
             "Natural rubber for the firmest, most grounded build, or TPE for a lighter mat at a "
             "lower landed cost. Both surfaces bond to both bases, which is where the combinations "
             "come from. Tell us the retail price band and we will recommend one instead of quoting "
             "everything.",
             "天然橡胶做踩感最实的结构，TPE 做更轻、到岸成本更低的版本。"
             "两种面层都能贴这两种底，组合就是这么来的。把零售价带告诉我们，"
             "我们只推荐一种，不会全部报一遍。"),
            ("Can the mat carry our own artwork?",
             "能印我们自己的图案吗？",
             "Yes — that is what this family is for. Gradients, botanical, geometric and floral "
             "prints all reproduce on suede, across the full face. Send the file and we will confirm "
             "how it samples before you commit to a production run.",
             "能 —— 这一族就是为这个存在的。渐变、植物、几何与花卉图案在麂皮上都能表现，"
             "而且是满版印。把文件发来，我们会先把打样效果确认给你，再让你决定要不要量产。"),
            ("How should these mats be cared for?",
             "平时怎么保养？",
             "Wipe with water and a pH-neutral cleaner, dry flat and away from direct sun, and never "
             "put suede or cork through a machine. Cork can be refreshed with a dilute vinegar wipe. "
             "Looked after that way, both surfaces hold up for years of studio use.",
             "用清水加 pH 中性清洁剂擦拭，平摊阴干、避开直晒，麂皮与软木都绝对不能机洗。"
             "软木可以用稀释的白醋擦一遍焕新。这样保养，两种面层都能扛住多年馆用。"),
        ],
    },

    "meditation-pilates-mats.html": {
        "eyebrow": ("Meditation and Pilates Guide", "冥想与普拉提选型"),
        "h2": ("Meditation, mandala and reformer mat builds",
               "冥想垫、曼陀罗与器械垫怎么做"),
        "paras": [
            ("This family covers three jobs a standard yoga mat does not do. Round meditation mats "
             "give a defined seat for sitting practice, in a 68 cm round or a 40 × 60 cm rectangle "
             "rather than a 183 cm roll. Bolsters support the knees and spine in restorative work, "
             "and the ones we build are 64 × 24 × 13 cm at 550 g, so they ship in a normal parcel. "
             "Mandala and gradient prints are what turn a functional cushion into a retail gift.",
             "这一族做的是标准瑜伽垫做不了的三件事。圆形冥想垫给坐姿练习一个明确的落座区，"
             "尺寸是 68 cm 圆或 40 × 60 cm 方，而不是 183 cm 的长卷。"
             "瑜伽枕在修复练习里支撑膝盖与脊柱，我们做的规格是 64 × 24 × 13 cm、550 g，"
             "普通包裹就能发。曼陀罗与渐变印花则是把一块功能性坐垫变成零售礼品的关键。"),
            ("Pilates reformer mats are the technical part, and they are made to order. Every "
             "machine has a different carriage, shoulder pad and foot-bar layout, so we cut to your "
             "drawing and add your logo rather than forcing you into a stock shape. Send the machine "
             "model, or the dimensions and the position of the logo, and the first sample is the "
             "confirmation step.",
             "普拉提器械垫是这里技术含量最高的部分，按单定制。每台器械的滑床、肩垫与脚踏布局都不同，"
             "所以我们按你的图纸裁切、再放上你的 Logo，而不是拿一个现成形状套给你。"
             "把器械型号，或者尺寸加 Logo 位置发过来，第一版样品就是确认环节。"),
            ("Compared with a yoga mat these are shorter and denser, and the material follows the "
             "job. A firm PU surface over rubber suits seated practice. Where landed cost matters "
             "more, TPE brings the weight down. Suede comes in when the artwork carries the design. "
             "Colour and artwork are set per order across the whole set, so a programme ships as a "
             "matched kit. MOQ is 100 pcs, samples in about 7 days.",
             "和瑜伽垫相比，这类垫子更短、更密实，材质跟着用途走："
             "坐姿练习用偏硬的 PU 面配橡胶底；到岸成本更要紧的，用 TPE 把重量压下来；"
             "图案本身是卖点的，上麂皮。颜色与图案按订单定，整批可以统一，"
             "所以一个冥想项目发出去的是一套配好的东西而不是三样散件。100 片起订，约 7 天出样。"),
        ],
        "faq_h2": ("Meditation and pilates mat questions buyers ask",
                   "买家会问的冥想垫与普拉提垫问题"),
        "qa": [
            ("How is a meditation mat different from a yoga mat?",
             "冥想垫和瑜伽垫有什么区别？",
             "It is shorter and denser. A meditation mat is built to give a stable seat, so the "
             "formats are a 40 × 60 cm rectangle or a 68 cm round rather than a 183 cm roll, and the "
             "surface is firmer than a yoga mat of the same material. The cushioning is sized for "
             "sitting, not for standing poses.",
             "更短、更密实。冥想垫要的是一个稳的落座区，所以规格是 40 × 60 cm 方垫或 68 cm 圆垫，"
             "而不是 183 cm 的长卷；同样材质下，表面也比瑜伽垫更硬。"
             "它的缓冲是按坐姿设计的，不是按站姿体式。"),
            ("Which round sizes do you run?",
             "圆形有哪些尺寸？",
             "The round mandala build is 68 cm across, and the rectangular meditation mats run "
             "40 × 60 cm in both PU over rubber and TPE. Custom diameters and rectangles come off "
             "the same tooling, so a non-standard size needs a quotation rather than a new mould.",
             "圆形曼陀罗款直径 68 cm；方形冥想垫做 40 × 60 cm，PU 配橡胶和 TPE 两种都有。"
             "异形直径与尺寸共用同一套模具，所以非标只需要报价，不用重新开模。"),
            ("How do we specify a reformer mat?",
             "普拉提器械垫怎么定规格？",
             "Send the machine model, or a photo with the carriage, the shoulder pads and the foot "
             "bar measured, plus where the logo should sit. Reformer mats are cut to your drawing, "
             "so the first sample is the confirmation step and no stock shape is imposed on you.",
             "把器械型号发来，或者发一张照片并把滑床、肩垫、脚踏的尺寸量好，"
             "再标出 Logo 要放的位置。器械垫按你的图纸裁，所以第一版样品就是确认环节，"
             "不会有现成形状硬套在你身上。"),
            ("Can the mandala artwork be changed?",
             "曼陀罗图案能改吗？",
             "Yes. Mandala, tropical and gradient artwork are all printed to your file, and a custom "
             "logo can be combined with it. Send the artwork and we will confirm how it reproduces "
             "on the surface you have chosen before you commit.",
             "可以。曼陀罗、热带与渐变图案都按你的文件印，也可以叠加自己的 Logo。"
             "把设计稿发来，我们会先确认它在你选的那种面层上印出来是什么效果，再让你决定。"),
            ("What is the MOQ on a mixed programme?",
             "混装项目的起订量是多少？",
             "MOQ is 100 pcs per design, with sampling in about 7 days. Mats, bolsters and round "
             "cushions can be combined in one shipment, and because colour and artwork are set per "
             "order they can be matched across the whole set.",
             "每个设计 100 片起订，约 7 天出样。垫子、瑜伽枕与圆形坐垫可以并到同一批出货，"
             "而且颜色与图案都按订单定，所以整批能做成配套的。"),
        ],
    },

    "yoga-props-accessories.html": {
        "eyebrow": ("Props and Accessories Guide", "辅具与配件选型"),
        "h2": ("The add-on range that lifts every mat order",
               "提升每一张垫子订单的加购线"),
        "paras": [
            ("Props are the cheapest way to raise the value of a container that is already going "
             "out. A mat order is one line item; the same shipment with blocks, a ball, a ring and a "
             "bag behind it is a programme, at a fraction of the freight cost per unit. That is why "
             "this range is built to sit alongside the mat lines rather than compete with them.",
             "辅具是提升一个已经要发的货柜价值的最便宜办法。一张垫子订单只是一个单品；"
             "同一个柜里再放上瑜伽砖、球、环和背包，它就是一个产品项目，"
             "而摊到每件上的运费只是一小部分。这就是这条线是配着垫子卖、而不是跟垫子抢单的原因。"),
            ("Six groups do the work here. EVA blocks give support in restorative poses, and "
             "high-density blocks hold their shape instead of crushing under weight. Yoga balls run "
             "from a 25 cm (10\") mini for pilates and rehab up to full-size anti-burst builds. "
             "Pilates rings come as a 34 cm silicone and fibreglass build or a 40 cm foam-padded "
             "version. Aerial hammocks run from 1 × 2.6 m to 5 × 2.8 m. Stretch boards lock the foot "
             "for calf and hamstring work, and carry bags finish the set.",
             "这里主要有六个品类。EVA 瑜伽砖在修复体式里提供支撑，"
             "高密度砖受压不变形；瑜伽球从普拉提与康复用的 25 cm（10\"）迷你球，"
             "到全尺寸防爆球都有；普拉提环有 34 cm 硅胶加玻璃纤维款和 40 cm 泡棉包裹款；"
             "空中吊床从 1 × 2.6 m 做到 5 × 2.8 m；拉伸板固定脚掌练小腿与腘绳肌；"
             "最后用收纳背包把整套收齐。"),
            ("Everything here is priced to ship with the mats, in the same colours. Blocks, rings "
             "and bags can be matched to the mat body or to the print, so a retail buyer receives a "
             "coordinated range instead of loose accessories. Custom colours and logos are set per "
             "order across the whole list. MOQ is 100 pcs, sampling in about 7 days.",
             "这里所有东西都是按「和垫子一起发、同色系」来定价的。砖、环与背包都能对上垫身或印花的颜色，"
             "零售买家收到的是一个协调好的系列，而不是一堆散装辅具。"
             "整张清单的颜色与 Logo 都按订单定。100 片起订，约 7 天出样。"),
        ],
        "faq_h2": ("Yoga prop questions buyers ask", "买家会问的瑜伽辅具问题"),
        "qa": [
            ("Can props be added to a mat order?",
             "辅具能和垫子下在同一张单上吗？",
             "Yes, and that is what the range is for. Blocks, balls, rings, boards and bags are "
             "produced on their own lines but ship in the same container as the mats, so a buyer "
             "gets a coordinated programme and pays freight once. Each item still carries its own "
             "100 pcs minimum.",
             "可以，这条线就是为这个存在的。砖、球、环、板与背包各在自己的产线上生产，"
             "但和垫子装同一个柜发走，所以买家拿到的是一个配套项目，运费只付一次。"
             "每一项仍然各按 100 片起订。"),
            ("How are the aerial hammocks installed, and what do they hold?",
             "空中吊床怎么安装？承重多少？",
             "They hang from a ceiling or a frame using a mount kit, which we can supply with the "
             "hammock. Weight ratings depend on the fabric and the stitching pattern, so we confirm "
             "the rating for the specific build you order rather than quoting one figure across the "
             "range.",
             "用安装配件挂在天花板或架子上，配件可以随吊床一起供。"
             "承重取决于面料与缝线结构，所以我们是按你下单的那一款单独确认承重，"
             "而不是拿一个数字套整条线。"),
            ("Can the block density be specified?",
             "瑜伽砖的密度能指定吗？",
             "Yes. EVA blocks are produced at the density your brief calls for — a firmer block for "
             "weight-bearing support, a softer one for comfort in restorative work. Send a sample of "
             "what you stock now and we will match the feel.",
             "可以。EVA 砖按你要求的密度生产 —— 需要承重的做硬一点，"
             "修复练习追求舒适的就做软一点。把你现在在卖的样品寄来，我们照着调手感。"),
            ("Which yoga ball sizes do you make?",
             "瑜伽球有哪些尺寸？",
             "The mini ball is 25 cm (10\") across, which is the size pilates and rehab customers use "
             "for core and balance work. Full-size anti-burst balls come in the standard diameters, "
             "and custom colours and print are set per order.",
             "迷你球直径 25 cm（10\"），是普拉提与康复客户用来练核心和平衡的尺寸。"
             "全尺寸防爆球做常规直径，颜色与印刷按订单定制。"),
            ("What is the MOQ across a mixed prop order?",
             "混装辅具订单的起订量是多少？",
             "MOQ is 100 pcs per item, with sampling in about 7 days. A mixed order can combine "
             "blocks, balls, rings and bags as long as each item reaches its own minimum, and the "
             "colours can be matched across the whole shipment.",
             "每个单品 100 片起订，约 7 天出样。混装订单可以把砖、球、环和背包并在一起，"
             "只要每项各自满起订量；配色可以在整批里统一。"),
        ],
    },

    "strength-training.html": {
        "eyebrow": ("Strength and Fitness Guide", "力量器械选型"),
        "h2": ("Silicone-skinned weights and the case for one colour system",
               "硅胶包覆配重，以及统一配色为什么值钱"),
        "paras": [
            ("Cast iron is the core of every weight on this page, but the skin is what the customer "
             "pays for. A silicone coating deadens the noise when two pieces meet, protects wooden "
             "floors and studio walls, and feels warm rather than cold in the hand. That is why it "
             "has displaced dipped and painted iron in studio and boutique-gym fit-outs. Underneath, "
             "the same casting gives the same density and the same balance.",
             "这一页每一件配重的芯都是铸铁，但客户真正付钱买的是那层皮。"
             "硅胶包覆能在两件器材相碰时把声音闷住，保护木地板与墙面，"
             "握在手里是温的而不是冰的。这就是它在工作室与小而精的健身房采购里取代浸塑与喷漆铸铁的原因。"
             "而底下同一套铸造，密度与配重平衡完全一样。"),
            ("One colour system is the commercial argument. Dumbbells, barbells, kettlebells, "
             "weighted balls and rings can all be produced in the same palette, in six silicone "
             "colourways for the smaller formats. A gym that buys one coordinated set does not come "
             "back for a mismatched second order, and a retail buyer gets a shelf that reads as a "
             "single brand rather than a mixed pile.",
             "统一配色是这里的商业理由。哑铃、杠铃、壶铃、负重球与训练环都能做成同一套色系，"
             "小件有六种硅胶配色可选。健身房买了一套配套的，就不会再回头补一个颜色对不上的第二批；"
             "零售买家拿到的货架，看起来是一个品牌，而不是一堆杂牌。"),
            ("The light end of the range covers abs and cardio: ab rollers, a multi-function board "
             "at 106 × 41 × 7 cm, a compact training board, suspension kits, and hydraulic steppers. "
             "Weights run across silicone dumbbells, cast-iron dumbbells in a range of loads, and "
             "bars at 91 cm and 110 cm. Power supply and controls on the electronic items are "
             "confirmed per order, so tell us the destination market. MOQ is 100 pcs, sampling in "
             "about 7 days.",
             "轻器械一侧覆盖腹部与有氧：健腹轮、106 × 41 × 7 cm 的多功能健身板、紧凑型训练板、"
             "悬吊训练套装与液压登山机。配重这边有硅胶哑铃、多档位铸铁哑铃，"
             "以及 91 cm 与 110 cm 两种杠铃杆。电子类产品的供电与控制方式按订单确认，"
             "所以请告诉我们目标市场。100 片起订，约 7 天出样。"),
        ],
        "faq_h2": ("Strength equipment questions buyers ask", "买家会问的力量器械问题"),
        "qa": [
            ("What is the difference between a silicone skin and dipped iron?",
             "硅胶包覆和浸塑铸铁差在哪？",
             "A silicone skin is a thicker, softer coating. It muffles the clang when two pieces "
             "meet, it does not chip onto the floor the way a painted or dipped finish can, and it "
             "does not feel cold in the hand. The casting underneath is the same, so weight and "
             "balance are unchanged.",
             "硅胶包覆是更厚、更软的涂层。它能把两件相碰时的响声闷住；"
             "不像喷漆或浸塑那样会掉皮掉到地板上；握起来也不冰手。"
             "底下的铸件完全一样，所以重量与配重平衡不变。"),
            ("Are the dumbbells adjustable?",
             "哑铃是可调的吗？",
             "Both options exist. Fixed cast-iron dumbbells run across a range of loads in the "
             "standard increments, and an adjustable build takes plates so one pair covers several "
             "loads. Tell us which one your customer expects and we will quote that.",
             "两种都有。固定式铸铁哑铃覆盖常规档位的多个重量；"
             "可调款能加减配重片，一对顶好几对。告诉我们你的客户期待哪一种，我们就报哪一种。"),
            ("Can the whole range share one colour?",
             "全系列能统一配色吗？",
             "Yes — that is what the range is built around. Six silicone colourways are available "
             "across the smaller formats, and bars, rings, kettlebells and balls can all be produced "
             "in the same palette, so a gym fit-out arrives coordinated.",
             "可以 —— 这条线就是围着这件事搭的。小件有六种硅胶配色，"
             "杠铃、训练环、壶铃与负重球都能做成同一套色，所以健身房一次配齐，到货就是配套的。"),
            ("How are the steppers and training boards powered?",
             "登山机与训练板的供电方式是什么？",
             "The hydraulic steppers are self-contained and need no power. The electronic training "
             "boards run on a cell or a rechargeable pack, and the exact supply depends on the market "
             "you ship into. Confirm the destination and we will quote the compliant version.",
             "液压登山机自带阻力，不需要供电。电子训练板用电池或充电电池组，"
             "具体用哪种取决于你的目的市场。确认销往哪里，我们报的就是能合规进口的版本。"),
            ("What is the MOQ and the sampling time?",
             "起订量和打样时间是多少？",
             "MOQ is 100 pcs per item and colour, with sampling in about 7 days. Mixed orders that "
             "combine a board, a pair of dumbbells and a stepper are standard as long as each item "
             "meets its own minimum.",
             "每个单品、每个颜色 100 片起订，约 7 天出样。"
             "把训练板、一对哑铃和登山机并成一张单很常规，只要每项各满起订量。"),
        ],
    },

    "massage-recovery.html": {
        "eyebrow": ("Massage and Recovery Guide", "按摩与恢复选型"),
        "h2": ("Building a recovery range that pairs with every mat order",
               "搭一条能和每张垫子配对的恢复线"),
        "paras": [
            ("Recovery tools are not interchangeable, and the difference is how much force the "
             "customer wants to put in. Fascia guns deliver high-frequency percussion through a "
             "motor, so the tool does the work. Fascia balls and rollers are body-weight tools — the "
             "user leans into them, which makes them cheap, silent and hard to break. Massage sticks "
             "reach the back and calves where your own hands cannot, and leg clamps compress the "
             "calf with no effort from the user at all.",
             "恢复工具之间不能互相替代，差别在于客户愿意自己使多大劲。"
             "筋膜枪靠电机输出高频振动，是工具在出力；筋膜球与泡沫轴是自重工具 —— "
             "使用者把自己的体重压上去，所以便宜、安静、还不容易坏；"
             "按摩棒用来够自己的手够不到的背和小腿；腿部夹则完全不用使用者出力就能挤压小腿。"),
            ("The gun range covers four grip types, because hand size and target area decide the "
             "sale: a compact white build for general retail, a T-shape for reaching the back, a "
             "ring-grip version that can be held two ways, and a professional model for therapists "
             "who run it all day. All four share the same motor family, so the difference is "
             "ergonomics rather than performance.",
             "筋膜枪有四种握型，因为手的大小和要打的部位决定了客户买哪一支："
             "白色紧凑款走大众零售，T 型用来够背部，环形握把可以两种握法，"
             "专业款给整天不离手的理疗师。四种共用同一套电机，所以差别在人体工学，不在性能。"),
            ("This is the category that pairs most naturally with a mat order, because recovery is "
             "what happens the day after the class. A gym or a studio buying mats can take guns, "
             "balls and sticks on the same shipment, in the same colours, and hand out or sell a "
             "complete recovery kit. Fascia balls are produced as a six-colour set for exactly that "
             "purpose. MOQ is 100 pcs, sampling in about 7 days.",
             "这一类和垫子订单配对最自然，因为恢复就是上完课第二天的事。"
             "买垫子的健身房或馆，可以在同一批里带上筋膜枪、筋膜球和按摩棒，配色统一，"
             "成套作为恢复包发放或销售。筋膜球专门做了六色套装就是这个用途。"
             "100 片起订，约 7 天出样。"),
        ],
        "faq_h2": ("Massage and recovery questions buyers ask",
                   "买家会问的按摩与恢复问题"),
        "qa": [
            ("What is the difference between the fascia gun models?",
             "几种筋膜枪差在哪？",
             "They share a motor family; the difference is the grip. The white build is a compact "
             "all-rounder, the T-shape reaches the back and shoulders, the ring grip can be held two "
             "ways for different angles, and the professional model is built for all-day therapist "
             "use. Pick by who is holding it and where they need to reach.",
             "它们共用同一套电机，差别在握把。白色款是紧凑全能型；T 型够得到背和肩；"
             "环形握把有两种握法，方便换角度；专业款是给整天在用的理疗师做的。"
             "怎么选，看是谁用、要够到哪里。"),
            ("Should we stock textured or smooth fascia balls?",
             "该备浮点筋膜球还是光面筋膜球？",
             "Textured balls concentrate pressure into a smaller area and are the ones for trigger "
             "points. Smooth balls spread the load and work better over a broad area like the back or "
             "the thighs. The six-colour set is built for retail, so a customer can take one of each "
             "and find out which they prefer.",
             "浮点球把压力集中到更小的面积上，是打激痛点的；"
             "光面球把力摊开，在背部、大腿这种大面积上更好用。"
             "六色套装就是为零售做的，客户可以每样拿一个，自己试出偏好。"),
            ("Which massage stick length should we stock?",
             "按摩棒该备哪个长度？",
             "We build a 34 cm and a 32 cm stick, both on a PP and stainless-steel-pipe "
             "construction. The longer one gives more reach for calves and the lower back, and the "
             "shorter one fits a gym bag. Stocking both covers the two use cases from one order.",
             "我们做 34 cm 和 32 cm 两种，都是 PP 加不锈钢管的做法。"
             "长的一支够得到小腿和下背，短的能塞进健身包。两种都备，一张单就把两个场景覆盖了。"),
            ("How are the fascia guns charged?",
             "筋膜枪怎么充电？",
             "They take a rechargeable cell, and the exact type, run time and certification depend on "
             "the market you ship into. Confirm the destination and we will quote the version that "
             "clears import there, rather than a generic specification sheet.",
             "用可充电电池，具体型号、续航与认证取决于你的目的市场。"
             "确认销往哪里，我们报的是能在那边过关的版本，而不是发一份通用规格表。"),
            ("What is the MOQ on a recovery kit?",
             "恢复套装的起订量是多少？",
             "MOQ is 100 pcs per item and colour, with sampling in about 7 days. Guns, balls, sticks "
             "and clamps can be combined in one shipment in matched colours, which is how most "
             "studio and gym chains order a recovery kit.",
             "每个单品、每个颜色 100 片起订，约 7 天出样。"
             "筋膜枪、球、按摩棒与腿部夹可以并到同一批、配色统一，"
             "大多数瑜伽馆与连锁健身房订恢复包就是这么下的。"),
        ],
    },
}


def all_en_strings():
    """翻译单元 = 每条 EN 串。顺序稳定（供缓存键复用）。"""
    out = []
    for spec in PAGES.values():
        out.append(spec["eyebrow"][0])
        out.append(spec["h2"][0])
        for en, _zh in spec["paras"]:
            out.append(en)
        out.append(spec["faq_h2"][0])
        for q_en, _q_zh, a_en, _a_zh in spec["qa"]:
            out.extend([q_en, a_en])
    return out


# ------------------------------------------------------------------ 手写覆盖
# 规则化不了的语义错译走这里。键由 PAGES 反查，避免手抄源串。
OVERRIDES = {}


# ------------------------------------------------------------------ 引号清洗
# ⚠️ 与 add_category_faq_20260925.py 同一份字符集，必须**含日式「」『』**。
_Q = "[\u201e\u201c\u201d\u00ab\u00bb\u2039\u203a\u2018\u2019\u300c\u300d\u300e\u300f\"]"
_TERM_Q = (r"(?:TPEE|TPE|PVC|PU|NBR|EVA|SBR|EEP|EPP|ROHS|REACH|SGS|BSCI|MOQ|OEM|ODM|CE"
           r"|ISO\s?9001|CA\s?Prop\s?65|EN\s?71|OEKO-?TEX|CPSIA|LCD|ABS|PP)")
_QUOTE_RE = re.compile(_Q + r"\s*(" + _TERM_Q + r")\s*" + _Q + r"(?![A-Za-z])")


def clean(t):
    prev = None
    while prev != t:
        prev, t = t, _QUOTE_RE.sub(r"\1", t)
    return t


def build_data(force=False, langs=None):
    # ⚠️ 必须写成 `LANGS if langs is None`，不能写 `langs or LANGS` ——
    #    调用方传空列表（`--langs ""`，只要 en）时 `[] or LANGS` 会**悄悄退回全部 6 语言**，
    #    2026-09-25 实测踩过一次：本想只验证英文结构，结果触发了 768 次全语言翻译。
    langs = LANGS if langs is None else langs
    src = all_en_strings()
    d = {}
    if DATA.exists():
        d = json.loads(DATA.read_text(encoding="utf-8"))
    # 已有语言缓存：读取时跑 clean + 自检（缓存投毒不自愈，必须就地清洗回写）
    healed = 0
    for lg in list(d.keys()):
        for s in list(d[lg].keys()):
            t = clean(d[lg][s])
            if t != d[lg][s]:
                d[lg][s] = t
                healed += 1
    if healed:
        DATA.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        print("  [缓存自愈] 清洗 %d 条并回写" % healed)

    todo = [lg for lg in langs if not all(s in d.get(lg, {}) for s in src)]
    if todo:
        print("  待译 EN 串 %d 条 × %d 语言（%s）" % (len(src), len(todo), ",".join(todo)))
    for lg in todo:
        tr = translator.translate_lines(src, lg.upper())
        assert len(tr) == len(src), (lg, len(tr))
        d[lg] = {s: clean(t) for s, t in zip(src, tr)}
        for (olg, osrc), txt in OVERRIDES.items():
            if olg == lg and osrc in d[lg]:
                d[lg][osrc] = txt
        for s, t in d[lg].items():
            if len(s.split()) >= 3 and t.strip() == s.strip():
                raise SystemExit("[%s] 译文回声（未翻译）：%s" % (lg, s[:70]))
            assert not _QUOTE_RE.search(t), "[%s] 引号残留：%s" % (lg, t[:80])
        translator.flush()
    if todo:
        DATA.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        print("  已写 %s（%.1f KB）" % (DATA.name, DATA.stat().st_size / 1024))
    return d


# ------------------------------------------------------------------ 渲染
def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def pair(en, zh, lang):
    if lang == "en":
        return ('<span class="lang-en">%s</span><span class="lang-zh">%s</span>'
                % (esc(en), esc(zh)))
    return "<span >%s</span>" % esc(en)


def render_intro(lang, eyebrow, h2, paras):
    ps = "\n".join("        <p>%s</p>" % pair(a, b, lang) for a, b in paras)
    return (
        "%s\n"
        '  <section class="section soft">\n'
        '    <div class="container">\n'
        '      <div class="section-head">\n'
        '        <div class="eyebrow">%s</div>\n'
        "        <h2>%s</h2>\n"
        "      </div>\n"
        '      <div style="max-width:820px;margin:0 auto;">\n'
        "%s\n"
        "      </div>\n"
        "    </div>\n"
        "  </section>\n"
        "%s" % (M_I_OPEN, pair(eyebrow[0], eyebrow[1], lang), pair(h2[0], h2[1], lang),
                ps, M_I_CLOSE)
    )


def render_faq(lang, h2, qa):
    items = []
    for q0, q1, a0, a1 in qa:
        items.append(
            '        <details class="faq-item">\n'
            "          <summary>%s</summary>\n"
            '          <div class="faq-a">%s</div>\n'
            "        </details>" % (pair(q0, q1, lang), pair(a0, a1, lang))
        )
    return (
        "%s\n"
        '  <section class="section soft">\n'
        '    <div class="container">\n'
        '      <div class="section-head">\n'
        '        <div class="eyebrow">%s</div>\n'
        "        <h2>%s</h2>\n"
        "      </div>\n"
        '      <div class="faq-list">\n'
        "%s\n"
        "      </div>\n"
        "    </div>\n"
        "  </section>\n"
        "%s" % (M_V_OPEN, pair("FAQ", "常见问题", lang), pair(h2[0], h2[1], lang),
                "\n".join(items), M_V_CLOSE)
    )


def render_ld(lang, canonical, h2, qa):
    obj = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "@id": canonical + "#faq-cat",
        "url": canonical,
        "name": h2,
        "inLanguage": lang,
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa],
    }
    return (M_L_OPEN + "\n"
            + '<script type="application/ld+json">\n%s\n</script>\n' % json.dumps(
                obj, ensure_ascii=False, indent=2)
            + M_L_CLOSE)


# ------------------------------------------------------------------ 剥 / 插（严格互逆）
def strip(s, a, b):
    return re.sub(re.escape(a) + r".*?" + re.escape(b) + r"\n\n", "", s, flags=re.S)


def insert(s, anchor, block):
    i = s.index(anchor)
    j = s.rfind("\n", 0, i) + 1
    t2 = s[:j] + block + "\n\n" + s[j:]
    assert t2.replace(block + "\n\n", "", 1) == s, "回退断言不一致"
    return t2


def strip_all(s):
    t = strip(s, M_I_OPEN, M_I_CLOSE)
    t = strip(t, M_V_OPEN, M_V_CLOSE)
    t = strip(t, M_L_OPEN, M_L_CLOSE)
    return t


def grid_section_pos(s):
    """导语插入点：**产品网格所在** `<section>` 之前。

    ⚠️ 判据不能用「`<section class="section">` 唯一」—— 内链块（`add_internal_links`）
       插入的也正是 `<section class="section">`，所以网格 + ilink 一共 2 个，
       实测直接撞断言「精确 class 的 section 有 2 个（应 1）」。
    ⚠️ 也不用 element 特征判块身份，改用**位置推导**（技能 §50 第 3 条）：
       取「`.prod-grid` 之前最后一个 `<section>`」，即包含产品网格的那一节。
       `catintro` 自身也是 `<section>`，但它每次插入前都会被 strip 掉，
       所以在 strip 后的文本上计算位置不受影响、幂等成立。
    """
    k = s.find('class="prod-grid"')
    assert k > 0, "找不到 .prod-grid（产品网格），锚点判据失效"
    m = None
    for m2 in re.finditer(r'[ \t]*<section\b', s[:k]):
        m = m2
    assert m, "产品网格之前没有 <section>，结构可能变了"
    return m.start()


def canonical_of(s):
    m = re.search(r'<link rel="canonical" href="([^"]+)"', s)
    assert m, "无 canonical"
    return m.group(1)


def inject(path, lang, tr, apply_, stats):
    s = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT).as_posix()
    page = path.name
    spec = PAGES[page]
    canonical = canonical_of(s)

    if lang == "en":
        eyebrow = tuple(clean(x) for x in spec["eyebrow"])
        h2i = tuple(clean(x) for x in spec["h2"])
        paras = [(clean(a), clean(b)) for a, b in spec["paras"]]
        h2f = tuple(clean(x) for x in spec["faq_h2"])
        qa4 = [(clean(x[0]), clean(x[1]), clean(x[2]), clean(x[3])) for x in spec["qa"]]
    else:
        def T(en):
            v = tr[lang].get(en)
            assert v, "%s 缺译文：%s" % (lang, en[:60])
            return clean(v)
        eyebrow = (T(spec["eyebrow"][0]),) * 2
        h2i = (T(spec["h2"][0]),) * 2
        paras = [(T(a), T(a)) for a, _b in spec["paras"]]
        h2f = (T(spec["faq_h2"][0]),) * 2
        qa4 = [(T(x[0]), T(x[0]), T(x[2]), T(x[2])) for x in spec["qa"]]

    intro = render_intro(lang, eyebrow, h2i, paras)
    faq = render_faq(lang, h2f, qa4)
    ld = render_ld(lang, canonical, h2f[0], [(p[0], p[2]) for p in qa4])

    t = strip_all(s)
    assert M_I_OPEN not in t and M_V_OPEN not in t and M_L_OPEN not in t, rel

    # 导语：插在网格 section 之前（锚点位置在剥块之后重新计算）
    pos = grid_section_pos(t)
    assert t.find(ILINK) > pos, "%s：ilink 标记应在网格之后" % rel
    t2 = t[:pos] + intro + "\n\n" + t[pos:]
    assert t2.replace(intro + "\n\n", "", 1) == t, "%s 导语块回退断言失败" % rel

    assert ILINK in t2, "%s 缺 %s（必须**先跑 add_internal_links**）" % (rel, ILINK)
    t3 = insert(t2, ILINK, faq)
    assert ORGREF in t3, "%s 缺 orgref 标记" % rel
    t4 = insert(t3, ORGREF, ld)

    assert t4.count(M_I_OPEN) == 1 and t4.count(M_V_OPEN) == 1 and t4.count(M_L_OPEN) == 1, rel
    assert faq.count('class="faq-item"') == len(spec["qa"]), (rel, faq.count('class="faq-item"'))
    assert intro in t4 and faq in t4 and ld in t4, rel
    assert "XX" not in re.sub(r"<[^>]+>", "", intro + faq), rel
    assert 'href="href=' not in t4, rel
    for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', t4, re.S):
        json.loads(b)
    nodes = [json.loads(b) for b in
             re.findall(r'<script type="application/ld\+json">(.*?)</script>', t4, re.S)]
    mine = [n for n in nodes if n.get("@type") == "FAQPage" and n.get("@id", "").endswith("#faq-cat")]
    assert len(mine) == 1 and len(mine[0]["mainEntity"]) == len(spec["qa"]), rel
    assert mine[0]["inLanguage"] == lang, (rel, mine[0]["inLanguage"])
    # 标签配平：本脚本只新增 section/div/h2/p/details/summary，成对出现
    for tag in ("section", "div", "h2", "p", "details", "summary"):
        o = len(re.findall(r"<%s\b" % tag, t4))
        c = len(re.findall(r"</%s>" % tag, t4))
        assert o == c, "%s：<%s> %d 个但 </%s> %d 个（标签不配平）" % (rel, tag, o, tag, c)

    changed = t4 != s
    if changed and apply_:
        path.write_text(t4, encoding="utf-8")
    stats["changed" if changed else "same"] += 1
    stats["pages"] += 1
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--retranslate", action="store_true")
    ap.add_argument("--langs", default=",".join(LANGS),
                    help="逗号分隔的目标语言（默认全部 6 个）；en 恒被处理")
    args = ap.parse_args()

    langs = [x.strip() for x in args.langs.split(",") if x.strip()]

    if args.check:
        bad, n = [], 0
        for lg in [""] + [x + "/" for x in LANGS]:
            for page in PAGES:
                p = ROOT / (lg + page)
                n += 1
                s = p.read_text(encoding="utf-8")
                if M_I_OPEN not in s:
                    bad.append((str(p.relative_to(ROOT)), "缺导语块"))
                if M_V_OPEN not in s or M_L_OPEN not in s:
                    bad.append((str(p.relative_to(ROOT)), "缺 FAQ 块"))
                    continue
                if s.count('class="faq-item"') < len(PAGES[page]["qa"]):
                    bad.append((str(p.relative_to(ROOT)), "问答数不足"))
                if "#faq-cat" not in s:
                    bad.append((str(p.relative_to(ROOT)), "缺 #faq-cat"))
        print("检查 %d 页 | 异常 %d" % (n, len(bad)))
        for b in bad:
            print("  ", b)
        sys.exit(1 if bad else 0)

    print("=== 准备译文（en 用手写中文，不走 API）===")
    tr = build_data(force=args.retranslate, langs=langs)

    stats = {"pages": 0, "changed": 0, "same": 0}
    for lg in ["en"] + langs:
        for page in PAGES:
            p = ROOT / ((lg + "/" if lg != "en" else "") + page)
            inject(p, lg, tr, args.apply, stats)
        print("  %-3s %d 页 %s" % (lg, len(PAGES), "已更新" if args.apply else "待更新"))
    print("\n合计 %d 页 | 需改动 %d | 无需改动 %d %s"
          % (stats["pages"], stats["changed"], stats["same"],
             "（已落盘）" if args.apply else "（空跑）"))


if __name__ == "__main__":
    main()
