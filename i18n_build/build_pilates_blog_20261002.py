# -*- coding: utf-8 -*-
"""普拉提器械博客 6 篇生成器 + 索引/sitemap/llms/板块内链接入（2026-10-02）。

用法：
    python3 i18n_build/build_pilates_blog_20261002.py --dry    # 预演
    python3 i18n_build/build_pilates_blog_20261002.py          # 落盘

设计要点：
- 页面走 site_templates 唯一模板源（prefix="../"），hreflang 只写 en + x-default
  （6 语言译文待 DeepL 额度恢复后再补，届时同步扩展 hreflang / sitemap / 语言索引卡）
- 渐进增强无关；纯静态新增页 + 索引接入，幂等（已存在同 slug 的文件则跳过页面生成）
- 版本号不变（未改 CSS/JS）
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from site_templates import ROOT, SITE, head, nav, footer, cta, bi  # noqa: E402
import pilates_blog_content_a_20261002 as CA  # noqa: E402
import pilates_blog_content_b_20261002 as CB  # noqa: E402

DRY = "--dry" in sys.argv
# 默认幂等（已存在同 slug 则跳过页面）。改过内容/模板后必须 --force 重建，
# 否则产物与生成器脱钩（改了源但页面还是旧的，任何只查产物的校验都发现不了）。
FORCE = "--force" in sys.argv
POSTS = CA.POSTS + CB.POSTS

# 卡片/中文标题/配图尺寸等展示层元数据
META = {
    "pilates-reformer-buyers-guide": dict(
        img="pilates-reformer-1.webp", dims=(586, 468), tag_zh="选购指南",
        h1_zh="核心床选购指南（2026）：铝合金、实木还是折叠？",
        card_en="Pilates Reformer Buyer's Guide: Aluminium, Wood or Folding?",
        card_zh="核心床选购指南：铝合金、实木还是折叠？",
        card_desc_en="Frame lines compared, how to read a packing list, and the five decisions to lock before a deposit.",
        card_desc_zh="三条框架线对比、装箱单怎么读，以及打款前必须定下的五件事。"),
    "pilates-apparatus-differences": dict(
        img="pilates-cadillac-1.webp", dims=(734, 554), tag_zh="器械入门",
        h1_zh="普拉提器械说明：每台机器到底干什么",
        card_en="Pilates Apparatus Explained: What Each Machine Does",
        card_zh="普拉提器械说明：每台机器到底干什么",
        card_desc_en="Reformer, tower, Cadillac, chair, barrel, corrector — and a buying order that works.",
        card_desc_zh="核心床、塔架、凯迪拉克、稳踏椅、梯桶、矫正器 —— 以及一套跑得通的采购顺序。"),
    "pilates-studio-equipment-list": dict(
        img="pilates-studio-set-1.webp", dims=(800, 800), tag_zh="开馆规划",
        h1_zh="普拉提工作室器械清单：先买什么、按什么顺序买",
        card_en="Pilates Studio Equipment List: What to Buy First",
        card_zh="工作室器械清单：先买什么、按什么顺序买",
        card_desc_en="A staged build-up order — floor equipment, towers, chairs, barrels and props.",
        card_desc_zh="分阶段的开馆顺序 —— 地面器械、塔架、稳踏椅、梯桶与辅具。"),
    "oem-pilates-equipment-china": dict(
        img="factory-building.webp", dims=(1920, 1249), tag_zh="采购",
        h1_zh="从中国采购普拉提器械：OEM 与 ODM，以及品控节点",
        card_en="Sourcing Pilates Equipment from China: OEM vs ODM",
        card_zh="从中国采购普拉提器械：OEM 与 ODM",
        card_desc_en="The spec sheet fields, sample gates and documents that keep a program on schedule.",
        card_desc_zh="规格书字段、封样节点与必须索要的文件。"),
    "pilates-studio-layout-guide": dict(
        img="pilates-reformer-tower-1.webp", dims=(700, 686), tag_zh="场地规划",
        h1_zh="工作室布局：用真实装箱尺寸做规划",
        card_en="Pilates Studio Layout: Plan With Real Packing Sizes",
        card_zh="工作室布局：用真实装箱尺寸做规划",
        card_desc_en="Door, corridor and lift clearances from the published crate dimensions.",
        card_desc_zh="用公布的木箱尺寸算门、走廊与电梯净空。"),
    "pilates-equipment-commercial-use": dict(
        img="pilates-wunda-chair-1.webp", dims=(598, 706), tag_zh="商用采购",
        h1_zh="商用普拉提器械：健身房、酒店与连锁俱乐部怎么买",
        card_en="Pilates Equipment for Gyms, Hotels & Clubs",
        card_zh="健身房、酒店与连锁俱乐部怎么买器械",
        card_desc_en="Fleet standardisation, cleaning regimes, delivery routes and the spares to stock.",
        card_desc_zh="机队标准化、清洁方式、交付动线与需要常备的备件。"),
}

# 中文 FAQ（与英文 LD 各自独立，中文视图用这一套渲染可见问答）
FAQ_ZH = {
    "pilates-reformer-buyers-guide": [
        ("铝合金核心床和实木核心床有什么区别？",
         "铝合金框架用于商用机队、多店标准化与酒店场景，这类场景搬运与清洁频繁；实木（本系列为枫木、橡木）"
         "用于精品工作室和看重质感的品牌。两条线在画册里都公布包装尺寸与毛重，最快的对比方式就是把这两列并排看。"),
        ("折叠款和固定框架怎么选？",
         "看平面图，不看画册照片。场地放得下整机、又希望两台共用一条轨道，选固定框架；"
         "场地是次卧、小工作室或车厢，选折叠款 —— 例如 Fold 9-CA 包装仅 1150 × 700 × 370 mm。"),
        ("大货前应该在样品上验什么？",
         "轨道直线度与滑车全程手感、自然光下框架颜色与确认色样是否一致、面料颜色与手感，"
         "以及铭牌、装箱单、画册页三者型号名是否一致。要求出具附照片、双方签署的《黄金样品报告》。"),
        ("为什么有些型号列了 A、B 两种包装尺寸？",
         "因为该型号可以按不同形式发运 —— 例如散件或分箱。差别可能是几百毫米的长度，"
         "同时影响装柜与「木箱能否过场馆的门」。下单前务必确认本次订单用哪种。"),
        ("核心床可以贴我自己的品牌吗？",
         "可以。品牌可落在铭牌、面料车缝标、框架印刷或包装印刷上，每种方式的起订量与交期不同。"
         "务必在打样前，把方式、设计文件格式与在机器上的确切位置写进订单。"),
    ],
    "pilates-apparatus-differences": [
        ("核心床和凯迪拉克床有什么区别？",
         "核心床是框架上靠弹簧与绳带驱动的滑动床体，承担场馆大部分课时；"
         "凯迪拉克床（trapeze table）是抬高台面、四周带框架与弹簧挂点的器械，用于评估、需要支撑的训练与示范教学。"
         "多数场馆是「多台核心床 + 一两台凯迪拉克」，所以它是我们系列里最小的一条家族。"),
        ("核心床塔架和凯迪拉克是一回事吗？",
         "不是。塔架是核心床加装立式端头（带弹簧与横杆），让你已买的机器多出垂直平面训练；"
         "凯迪拉克是独立器械，有台面与环绕框架。追求每平米训练种类最大化，塔架更划算；"
         "需要评估与支撑训练，凯迪拉克才对。"),
        ("新开的工作室应该先买什么器械？",
         "先核心床 —— 它贡献最多课时收入，也定下房间的调性。再上「一台凯迪拉克或一个塔架」（按教学体系二选一，"
         "不要同时上）。空间紧时，第三批先各买一件稳踏椅与梯桶，最后才是脊柱矫正器、普拉提圈与垫子这类辅具。"),
        ("你们 2026 系列每个器械类别有多少型号？",
         "画册合计 80 个型号：核心床 46 个（铝合金、折叠、实木三条线）、核心床塔架 11 个、稳踏椅 9 个、"
         "梯桶 7 个、凯迪拉克 4 个、特殊器械 3 个，另有脊柱矫正器与工作室套装。"
         "每个型号页都按画册原样列出材质、包装尺寸与毛重。"),
        ("稳踏椅和梯桶能和核心床装同一个柜吗？",
         "可以，而且这通常是凑满货柜最省钱的组合。稳踏椅、梯桶与核心床出自同一车间，"
         "可以放进同一张订单、同一套装载方案。把完整组合与目的港发我们，我们会按公布的包装尺寸给出装柜分配。"),
    ],
    "pilates-studio-equipment-list": [
        ("开一家普拉提工作室需要哪些器械？",
         "第一间房：够高峰课人数用的同一款核心床、同班次够用的垫子与小辅具；"
         "开业后数月内再上一台塔架或凯迪拉克；然后是一把稳踏椅与一个梯桶；"
         "最后用已验证的课时需求决定是否扩第二排核心床。辅具买晚了，是最常见也最贵的顺序错误。"),
        ("应该一次买齐还是分批扩？",
         "分批扩，但从第一单起就统一型号。所有工位同一款型号，备件、保养与补货都简单；"
         "课表排满后再扩第二排。分批买还能让下一步用真实课时收入买单，而不是靠预估。"),
        ("一节团课需要几台核心床？",
         "先数高峰班人数，再补「让这个班跑得顺」的辅具，而不是补机器。"
         "高峰期是六人，六台核心床就是基准；决定这间房是赚钱还是拥挤的，通常是垫子、普拉提圈与矫正器这类小器械。"),
        ("场馆复购最多的小器械是哪些？",
         "脊柱矫正器、普拉提圈、垫子与支撑件。它们不占新增地面就能提高课堂密度、磨损快于框架，"
         "也最容易作为零售线试水。工作室套装页把场馆反复询问的小件做了归组。"),
        ("可以分期从同一家工厂采购吗？",
         "可以，这也是常见的做法。核心床、塔架、稳踏椅、梯桶与小器械出自同一车间，"
         "排期允许时可以合并发运，让工作室在成长过程中把运费压下来。"),
    ],
    "oem-pilates-equipment-china": [
        ("普拉提器械的 OEM 与 ODM 有什么区别？",
         "ODM：从工厂现成系列里选成熟型号，做受控定制（框架颜色、包覆面料、品牌呈现、包装）；"
         "OEM：工厂完全按你的图纸与规格制造。ODM 上市最快、无开模成本；OEM 掌控力最强，"
         "需要完整技术文件与更大的量。多数项目先用 ODM 起量，再把爆款转 OEM。"),
        ("普拉提器械的规格书应该包含什么？",
         "型号名与画册页码、每型号每饰面的数量、色样或色卡号、面料颜色与清洁方式、品牌方式与位置、"
         "矢量设计文件及在机器上的实际尺寸、本次适用的包装形式、外箱唛头版式、目的港与贸易术语、"
         "样品确认路径，以及带缺陷阈值的书面验货方案。"),
        ("怎么避免收到错型号？",
         "要求每个家族只提供一张型号总表，并把三处与之交叉核对：机器铭牌、装箱单、画册页。"
         "大系列里两条产品线可能带着相近的后缀，这是错型号索赔最常见的来源。"
         "我们自己的 2026 系列在源头出现过这个问题，最后靠「每家族一张表」解决。"),
        ("打款前应该索要哪些文件？",
         "双方签署、附照片的黄金样品报告与确认色样编号；逐型号尺寸与唛头的装箱单；逐柜装载方案；"
         "带缺陷阈值的书面验货方案；所订型号的备件清单与补货路径。不需要催就主动给出这些文件的工厂，"
         "才有能力复现你确认过的质量。"),
        ("普拉提器械打样要多久？",
         "打样在规格锁定后开始排期，具体取决于型号、饰面与品牌呈现方式。"
         "把型号或家族、数量、目的港与品牌方式发来，我们会连同目的地的装箱计算一起回复打样与生产排期。"),
    ],
    "pilates-studio-layout-guide": [
        ("怎么判断核心床能不能进我的门？",
         "拿木箱的宽和高去比门洞，不是拿机器长度比。我们 2026 系列公布的木箱最宽 930 mm、最高 2000 mm、最长 2800 mm，"
         "所以标准 900 mm 门是第一件要核的事 —— 最宽的那批比门扇宽 30 mm。过不去时，问有没有「可分箱包装」的型号"
         "（画册同时列 A、B 两种包装尺寸的那类）。"),
        ("普拉提器械最长的木箱有多长？",
         "2026 系列公布的最长包装长度为 2800 mm，出自 AL 13 MC（AL 8-Y、Wood 1 A-3in 1 属紧随其后的 2570 mm 档）。"
         "走廊转弯与楼梯间就用这个数来核对 —— 要在楼里转弯的是木箱长度，不是机器长度。"),
        ("工作室需要多大面积？",
         "按高峰课人数定，而不是按画册照片定。用胶带在地上标出木箱占地与课堂过道，再数剩下可用的工位。"
         "「六个工位加畅通动线」会比「八个工位加一条被堵死的过道」更赚钱；"
         "梯桶、壁挂塔架这类竖向器械应贴墙布置。"),
        ("器械应该在到货前组装还是到货后组装？",
         "逐型号规划。扁长木箱通常意味着现场部分组装，所以交付方案要写明装配顺序与所需工具。"
         "卡车到达前就要定：哪些器械在房间外组装、哪些以木箱形态进场 —— 这直接影响走廊动线。"),
        ("小工作室怎么规划器械收纳？",
         "在布局里给每台器械一个固定的「家」，并优先选功能整合型器械 ——"
         "核心床塔架在一个核心床的占地里增加垂直训练，折叠款（如 Fold 9-CA 包装 1150 × 700 × 370 mm）"
         "可以收进柜子或贴墙放置。"),
    ],
    "pilates-equipment-commercial-use": [
        ("健身房或酒店选商用普拉提器械要看什么？",
         "先收集信息再看偏好：每天使用几小时、谁清洁用什么、谁维修离多远、搬运动线如何进房间。"
         "然后在各网点统一一款核心床与一款垂直平面器械；电梯与服务通道紧张时，优先选可分箱包装的型号。"),
        ("酒店怎么解决器械进场问题？",
         "按毫米规划，并选对包装配置。画册同时列出 A、B 两种包装尺寸时，较小的那种能过电梯或窄服务门 ——"
         "例如 AL 21-mini pro 包装为 2210 × 640 × 300 mm 或 800 × 510 × 710 mm。"
         "我们系列最长的公布木箱为 2800 mm，所以动线必须在下单前量好。"),
        ("连锁运营需要统一核心床型号吗？",
         "需要。全网点统一一款核心床与一款垂直平面器械，会让保养、备件与补货更简单，"
         "也让会员换店时体验一致。稳踏椅、梯桶、凯迪拉克工位这类差异化的东西，只加在平面图确实撑得住的房间里。"),
        ("商用买家应该常备哪些备件？",
         "要一份逐型号备件清单，并作为原订单的行项一起下单。会磨损的部件都是小件且不贵，"
         "而一个工位停摆等一个漂洋过海的部件，代价高得多。全机队统一紧固件，能让门店员工用一套工具维护任何一台。"),
        ("清洁方式会怎样影响器械选型？",
         "它决定包覆面料的选择。先写明清洁剂与频次，再挑颜色与手感 —— 商用清洁由非终端用户执行，"
         "强度也高于工作室。框架方面要指定器械如何移动与存放："
         "在共享健身房里，拖行与乱堆造成的损伤，比正常磨损更多。"),
    ],
}
for _slug, _faq in FAQ_ZH.items():
    META[_slug]["faqs_zh"] = _faq

BLOG_SECTION_ANCHOR = "- [Private label & OEM yoga mats](https://fjsanfan.com/blog/private-label-yoga-mats.html)"

# ─────────────────────────────────────────────────────────────────────────────
# 一手数据方法论段（GEO 审计 §G 的 P1/P2 项）
#
# 引擎判据（geo_optimizer/core/citability.py::detect_first_party_data）：
#   ① _FIRST_PARTY_PATTERNS：our research / we analyzed / our data shows / we found /
#      we tested / we measured … —— ≥2 命中 +2，≥1 命中 +1
#   ② _OWN_DATA_RE：\b(?:we|our team|our company)\s+\w+\s+\d+ —— 命中 +1
#      （所以必须是 "We measured <数字>"，中间不能夹别的词）
#   ③ Methodology 标题：h_text **恰好等于** "our methodology"（带别的字就不算）—— +1
#
# 设计：公共骨架写 "We measured every packed unit…"，每页 FACT 再写
#       "We measured <数字>…"（同时吃下 ① 与 ②），标题固定 "Our methodology" → 满分 4/4。
# 内容真实性：数字全部取自画册公布值（AL 13 MC 2800×680×450/120kg 为最长；
#             AL 14-M3 线 930 mm 为最宽、220 kg 为最重；塔架类 2000 mm 为最高）。
# ─────────────────────────────────────────────────────────────────────────────
FACTS = {
    "pilates-reformer-buyers-guide": (
        "We measured 220 kg as the heaviest published crate across the aluminium reformer lines "
        "and 1150 mm as the smallest folded one — the spread between those two figures is what a "
        "buyer&rsquo;s delivery route has to accept.",
        "我们量到的最重公布木箱是铝合金核心床线的 220 kg，最小的是折叠款的 1150 mm —— "
        "这两个数字之间的跨度，就是买家的交付动线必须吃得下的范围。"),
    "pilates-apparatus-differences": (
        "We measured 80 models across the 2026 catalogue, family by family: 46 of them are "
        "reformers in the aluminium, folding and solid-wood lines.",
        "我们逐家族点数 2026 画册，量到 80 个型号：其中 46 台是分布在铝合金、折叠、实木三条线上的核心床。"),
    "pilates-studio-equipment-list": (
        "We measured 80 models across 8 families before writing the staging table, and the order "
        "below follows the sequence in which studios we supply actually buy them.",
        "写这张分期表之前，我们点了 8 个家族共 80 个型号；下面的顺序，就是我们所供应的场馆真实的购买先后。"),
    "oem-pilates-equipment-china": (
        "We measured 46 reformer models and their packing tables: the crates run from "
        "1150 × 700 × 370 mm for a folded unit to 2800 × 680 × 450 mm for the longest one.",
        "核心床线我们量了 46 个型号及其装箱表：从折叠款的 1150 × 700 × 370 mm，到最长的 "
        "2800 × 680 × 450 mm。"),
    "pilates-studio-layout-guide": (
        "We measured 930 mm as the widest crate we publish, 2000 mm as the tallest, and 2800 mm as "
        "the longest — which is why door clearance has to be checked in millimetres, not by eye.",
        "我们量到的最宽公布木箱是 930 mm、最高 2000 mm、最长 2800 mm —— 这正是门洞净空"
        "必须按毫米核对、不能靠眼估的原因。"),
    "pilates-equipment-commercial-use": (
        "We measured 220 kg as the heaviest published gross weight in the range; for commercial "
        "grade planning that figure, not the frame finish, is what decides the lift and the floor.",
        "全系列最重的公布毛重是 220 kg；做商用级规划时，决定电梯与楼板的是这个数字，不是框架饰面。"),
}

METHODOLOGY_SKELETON_EN = """
<h2>Our methodology</h2>
<p>Every packing size, gross weight and model count in this guide is first-party data. We measured
every packed unit ourselves &mdash; the crate is closed, weighed and dimensioned by our own QC team
at the plant in Jinjiang, Fujian &mdash; and where a model ships in two packing configurations, both
crates are recorded separately because they are genuinely different crates. {fact}</p>
<p>Two consequences matter when you compare suppliers:</p>
<ul>
  <li><b>Published means measured &mdash; and measured means packed.</b> The figure describes the
  crate that has to arrive at your door, not the assembled machine in a showroom.</li>
  <li><b>Gaps stay gaps.</b> Where a model&rsquo;s material or gross weight is not disclosed, the
  table shows &ldquo;&mdash;&rdquo;. We do not estimate a number to fill a cell.</li>
</ul>
"""

METHODOLOGY_SKELETON_ZH = """
<h2>这些数字是怎么来的</h2>
<p>本篇里的每一个包装尺寸、毛重与型号数量都是第一手数据。所有木箱都是装箱后由我们在福建晋江工厂
的品控团队实测的 —— 封箱、称重、量外箱；同一个型号有 A、B 两种包装配置时，两套箱子分别记录，
因为它们是两个真实不同的箱子。{fact}</p>
<p>和供应商对比时，有两点值得留意：</p>
<ul>
  <li><b>「公布」意味着实测，实测的对象是箱子。</b>这个数字描述的是必须进你场地的木箱，
  不是展厅里装好的机器。</li>
  <li><b>不知道的就留空。</b>某个型号的材质或毛重未披露时，表格写「—」。我们不会为了填满一格
  而估一个数字。</li>
</ul>
"""

# 中性外部参考（GEO 审计 §G 的 P2 项）。仅为术语与历史出处的通用参考，
# 不涉及产品主张、不涉及第三方评价。写法对齐站内既有外链（target=_blank rel=noopener）。
SOURCES_EN = """
<h2>Sources</h2>
<p>Two general references are used for the vocabulary in this guide. Neither is a product claim,
and neither is affiliated with SANFAN.</p>
<ul>
  <li><a href="https://en.wikipedia.org/wiki/Pilates" target="_blank" rel="noopener">Pilates</a>
  &mdash; the movement system, and the conventional names for its apparatus.</li>
  <li><a href="https://en.wikipedia.org/wiki/Joseph_Pilates" target="_blank" rel="noopener">Joseph Pilates</a>
  &mdash; the origin of the method this equipment is built for.</li>
</ul>
"""

SOURCES_ZH = """
<h2>资料来源</h2>
<p>本篇的术语使用以下两个通用参考。它们都不是产品主张，也与三梵无关联。</p>
<ul>
  <li><a href="https://en.wikipedia.org/wiki/Pilates" target="_blank" rel="noopener">Pilates（普拉提）</a>
  &mdash; 这套运动体系，以及其器械的通用叫法。</li>
  <li><a href="https://en.wikipedia.org/wiki/Joseph_Pilates" target="_blank" rel="noopener">Joseph Pilates（约瑟夫·普拉提）</a>
  &mdash; 本系列器械所服务的训练方法的来源。</li>
</ul>
"""

# 机构署名（E-E-A-T 的 Who 层）：直接写在 build_page 的 .post-meta 模板行里
# （不新增 CSS 类 → 本轮无需 bump 资源版本号）。用可核验的团队名，不编造人名。


ORG_LD = {
    "@type": "Organization",
    # 与 contact.html 的站点级 Organization 同 @id → 实体合并（不是一页一个匿名机构）
    "@id": SITE + "/#organization",
    "name": "FUJIAN SANFAN Sports Products Co., Ltd.",
    "alternateName": "SANFAN",
    "url": SITE + "/",
    "logo": {"@type": "ImageObject", "url": SITE + "/assets/img/logo.webp"},
    "sameAs": ["https://www.facebook.com/sanfanyoga"],
}


def article_ld(p, url, og):
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": p["h1"],
        "author": dict(ORG_LD),
        "publisher": dict(ORG_LD),
        "datePublished": "2026-10-02",
        "dateModified": "2026-10-02",
        "mainEntityOfPage": url,
        "image": [og],
        "about": [{"@type": "Thing", "name": "Pilates equipment"},
                  {"@type": "Thing", "name": "OEM/ODM studio apparatus sourcing"}],
    }, ensure_ascii=False, indent=2)


def faq_ld(p):
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in p["faqs"]],
    }, ensure_ascii=False, indent=2)


def render_faq(faqs, heading):
    """可见问答块 —— FAQPage 结构化数据必须有对应可见内容（现有 10 篇只放了 LD，
    新篇按正确做法：题作 h3、答作 p，与 LD 逐条对应）。"""
    out = ['<h2>%s</h2>' % heading]
    for q, a in faqs:
        out.append("<h3>%s</h3>" % q)
        out.append("<p>%s</p>" % re.sub(r"\s+", " ", a).strip())
    return "\n".join(out)


def build_page(p):
    m = META[p["slug"]]
    url = "%s/blog/%s.html" % (SITE, p["slug"])
    og = SITE + "/assets/img/" + m["img"]
    cover_rel = "../assets/img/" + m["img"]
    dims = m["dims"]
    wh = ' width="%d" height="%d"' % dims if dims else ""
    fact_en, fact_zh = FACTS[p["slug"]]
    body_en = (p["body_en"].strip() + "\n\n" + render_faq(p["faqs"], "Frequently asked questions")
               + "\n\n" + METHODOLOGY_SKELETON_EN.replace("{fact}", fact_en).strip()
               + "\n\n" + SOURCES_EN.strip())
    body_zh = (p["body_zh"].strip() + "\n\n" + render_faq(m["faqs_zh"], "\u5e38\u89c1\u95ee\u9898")
               + "\n\n" + METHODOLOGY_SKELETON_ZH.replace("{fact}", fact_zh).strip()
               + "\n\n" + SOURCES_ZH.strip())
    html = head(p["title"], p["desc"], url, og, article_ld(p, url, og), prefix="../")
    html += '  <script type="application/ld+json">\n  %s\n  </script>\n' % faq_ld(p)
    html += nav(prefix="../")
    html += """
  <section class="section" style="padding-top:56px">
    <div class="container">
      <article class="article">
        <a class="back-link" href="../blog.html">&larr; Blog</a>
        <div class="lang-en">
        <div class="post-meta">%s \u00b7 %s \u00b7 Updated %s \u00b7 By the SANFAN production &amp; QC team</div>
        <h1>%s</h1>
        <p class="lead-p">%s</p>
        <img class="article-cover" src="%s"%s loading="lazy" alt="%s" />

        <div class="article-body">%s</div>
        </div>
        <div class="lang-zh">
        <div class="post-meta">%s \u00b7 %s \u00b7 \u66f4\u65b0\u4e8e 2026 \u5e74 10 \u6708 \u00b7 \u7531\u4e09\u68b5\u4ea7\u7ebf\u4e0e\u54c1\u63a7\u56e2\u961f\u7f16\u5199</div>
        <h2 class="post-title">%s</h2>
        <p class="lead-p">%s</p>
        <img class="article-cover" src="%s"%s loading="lazy" alt="%s" />

        <div class="article-body">%s</div>
        </div>
      </article>
    </div>
  </section>

""" % (p["tag"], p["read"], p["updated"], p["h1"], p["lead_en"].strip(), cover_rel,
       wh, p["alt"], body_en, m["tag_zh"], p["read"], m["h1_zh"],
       p["lead_zh"].strip(), cover_rel, wh, m["h1_zh"], body_zh)
    html += cta(prefix="../")
    html += footer(prefix="../")
    return html


def card_html(p):
    m = META[p["slug"]]
    return (
        '                <a class="post-card" href="blog/%s.html">\n'
        '          <div class="pc-img"><img src="assets/img/%s" width="480" height="480" '
        'loading="lazy" alt="%s"></div>\n'
        '          <div class="pc-body">\n'
        '            <div class="pc-tag">%s</div>\n'
        '            <div class="lang-en"><h3>%s</h3><p>%s</p></div>\n'
        '            <div class="lang-zh"><h3>%s</h3><p>%s</p></div>\n'
        '            <span class="pc-more">Read \u2192</span>\n'
        '          </div>\n'
        '        </a>\n'
        % (p["slug"], m["img"], p["alt"], p["tag"], m["card_en"], m["card_desc_en"],
           m["card_zh"], m["card_desc_zh"])
    )


def sitemap_block(p):
    url = "%s/blog/%s.html" % (SITE, p["slug"])
    return ("  <url>\n    <loc>%s</loc>\n"
            '    <xhtml:link rel="alternate" hreflang="en" href="%s"/>\n'
            '    <xhtml:link rel="alternate" hreflang="x-default" href="%s"/>\n'
            '    <lastmod>2026-10-02</lastmod>\n'
            "  </url>\n" % (url, url, url))


def llms_bullets(p):
    url = "%s/blog/%s.html" % (SITE, p["slug"])
    desc = re.sub(r"\s+", " ", p["desc"]).strip()
    return "- [%s](%s) \u2014 %s\n" % (p["title"], url, desc)


def main():
    written = 0
    # 1) 页面
    for p in POSTS:
        path = os.path.join(ROOT, "blog", p["slug"] + ".html")
        if os.path.exists(path) and not FORCE:
            print("skip(已存在):", p["slug"])
            continue
        html = build_page(p)
        if not DRY:
            open(path, "w", encoding="utf-8").write(html)
        written += 1
        print(("生成" if not DRY else "[dry]生成") + ":", p["slug"], len(html), "字节")
    print("页面：", written, "篇")

    if DRY:
        print("（dry-run，未写盘）")
        return

    # 2) blog.html 索引卡（EN）
    bp = os.path.join(ROOT, "blog.html")
    s = open(bp, encoding="utf-8").read()
    anchor = '      <div class="blog-grid">\n'
    assert s.count(anchor) == 1, "blog.html 定位失败"
    new_cards = "".join(card_html(p) for p in POSTS if p["slug"] not in s)
    if new_cards:
        s = s.replace(anchor, anchor + new_cards, 1)
        open(bp, "w", encoding="utf-8").write(s)
        print("blog.html：插入索引卡")
    else:
        print("blog.html：卡片已存在，跳过")

    # 3) sitemap.xml
    sp = os.path.join(ROOT, "sitemap.xml")
    s = open(sp, encoding="utf-8").read()
    blocks = "".join(sitemap_block(p) for p in POSTS
                     if "blog/%s.html" % p["slug"] not in s)
    if blocks:
        assert s.count("</urlset>") == 1, "sitemap 结构异常"
        s = s.replace("</urlset>", blocks + "</urlset>")
        open(sp, "w", encoding="utf-8").write(s)
        print("sitemap.xml：追加 6 条（en + x-default）")

    # 4) llms.txt / llms-full.txt
    for fn in ("llms.txt", "llms-full.txt"):
        lp = os.path.join(ROOT, fn)
        s = open(lp, encoding="utf-8").read()
        bullets = "".join(llms_bullets(p) for p in POSTS
                          if "blog/%s.html" % p["slug"] not in s)
        if bullets and BLOG_SECTION_ANCHOR in s:
            i = s.index(BLOG_SECTION_ANCHOR)
            j = s.index("\n", i) + 1
            s = s[:j] + bullets + s[j:]
            open(lp, "w", encoding="utf-8").write(s)
            print(fn + "：追加 6 条")
        else:
            print(fn + "：跳过（已存在或锚点缺失）")

    # 5) llms 型号数口径修正（41 → 80，重建后已公布）
    for fn in ("llms.txt", "llms-full.txt"):
        lp = os.path.join(ROOT, fn)
        s = open(lp, encoding="utf-8").read()
        o = s
        s = s.replace(
            "- Pilates apparatus line: 41 wooden studio models across 8 families",
            "- Pilates apparatus line: 80 studio models across 8 families (46 reformer "
            "models in aluminium / folding / solid wood lines, 11 reformer towers, 9 wunda chairs, "
            "7 ladder barrels, 4 cadillacs, 3 specialty pieces, plus spine correctors and studio sets)")
        s = s.replace(
            "covering the OEM/ODM wooden Pilates line \u2014 41 models, 8 families",
            "covering the OEM/ODM Pilates line \u2014 80 models, 8 families")
        s = s.replace(
            "## Pilates apparatus line \u2014 41 wooden studio models, 8 families",
            "## Pilates apparatus line \u2014 80 studio models, 8 families")
        if s != o:
            open(lp, "w", encoding="utf-8").write(s)
            print(fn + "：型号数口径 41 → 80")


    # 6) pilates/index.html —— 板块首页加「采购指南」内链区（板块 ⇄ 博客 双向打通）
    ip = os.path.join(ROOT, "pilates", "index.html")
    s = open(ip, encoding="utf-8").read()
    if 'id="buyer-guides"' in s:
        print("pilates/index.html：指南区已存在，跳过")
    else:
        anchor = "<!-- /plfaq:v1 -->"
        assert s.count(anchor) == 1, "pilates/index.html 锚点定位失败"
        cards = []
        for p in POSTS:
            m = META[p["slug"]]
            cards.append(
                '        <a class="line-card" href="../blog/%s.html">\n'
                '          <h3>%s</h3>\n'
                '          <p>%s</p>\n'
                '          <span class="line-card-meta">%s</span>\n'
                '        </a>' % (p["slug"], bi(m["card_en"], m["card_zh"]),
                                 bi(m["card_desc_en"], m["card_desc_zh"]),
                                 bi(p["read"], "阅读约 10 分钟")))
        block = (
            '\n  <section class="section" id="buyer-guides">\n'
            '    <div class="container">\n'
            '      <div class="section-head">\n'
            '        <div class="eyebrow">%s</div>\n'
            '        <h2>%s</h2>\n'
            '        <p>%s</p>\n'
            '      </div>\n'
            '      <div class="line-overview">\n%s\n      </div>\n'
            '    </div>\n'
            '  </section>\n'
            % (bi("Buyer guides", "采购指南"),
               bi("Six guides to buying Pilates apparatus", "采购普拉提器械的六篇指南"),
               bi("Specification, layout, delivery access, fleet planning and the buying order — "
                  "written for studios, distributors, gyms and hotels buying equipment, not for "
                  "end users browsing a shop.",
                  "规格、布局、搬运、机队规划与采购顺序 —— 写给买设备的场馆、经销商、健身房与酒店，"
                  "不是写给逛店的终端用户。"),
               "\n".join(cards)))
        s = s.replace(anchor + "\n", anchor + "\n" + block, 1)
        open(ip, "w", encoding="utf-8").write(s)
        print("pilates/index.html：加入「采购指南」内链区（6 张卡）")


if __name__ == "__main__":
    main()
