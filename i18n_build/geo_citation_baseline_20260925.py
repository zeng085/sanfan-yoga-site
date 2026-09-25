#!/usr/bin/env python3
"""fjsanfan.com AI/检索引用基线（2026-09-25 首测）。

背景：站内 GEO 已做到 78/100（技术层 22/22、三项审计全 0），再修站内上不去，
瓶颈在站外。本脚本固化「基线采样结果 + 分析口径」，产出可比的数字，供下次复测对照。

采样方法（本机在墙内，故分两路，口径不可混用）：
  路 A 检索层（谁是 AI 的引用来源池）：governed by 全局 SERP，本机 DDG 被墙
        → 走 html.duckduckgo.com 的服务端抓取；补充用托管侧检索。
  路 B AI 答案层（真 AI 引擎答不答你）：秘塔 metaso.cn（可直连，带来源引用）
        → Playwright 提问采样。Perplexity/ChatGPT/Gemini/Google 本机不可达（见 LIMITS）。

复测方法：
  bash:  node <repo>/i18n_build/geo_citation_baseline_20260925.cjs   # 路 B 重采样
  手工:  对 SERP 逐条跑，把 URL 追加进下方 QUERIES，重跑本脚本
"""
from __future__ import annotations

import json
import pathlib
import re
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTDIR = ROOT / "i18n_build" / "reports"
STAMP = "2026-09-25"      # 报告内显示
FILE_STAMP = "20260925"   # 文件名用（与仓库既有命名一致）
RAW_AI = pathlib.Path("/tmp/metaso_raw.json")  # 路 B 的原始采样记录（可缺省）

# ---------------------------------------------------------------- 我们的域
OWNED = {"fjsanfan.com": "新站（独立站，本次主体）", "sanfanyoga.com": "老站（Xiamen Sanfan Fitness）"}

# ---------------------------------------------------------------- 域分类
TYPE_RULES = [
    ("marketplace", ("made-in-china.com", "alibaba.com", "globalsources.com",
                     "b2b.baidu.com", "b2bdata.baidu.com", "b2b168.org", "1688.com",
                     "baidu.com")),
    ("ai-aggregator", ("accio.com", "finalscout.com")),
    ("owned", tuple(OWNED)),
]
# 其余：竞品制造商官网

QUERY_TYPE_LABEL = {"serp": "路 A 检索层", "ai": "路 B AI 答案层"}

# ---------------------------------------------------------------- 采样结果
# 每条：query / channel / 结果 URL 列表（按出现顺序）/ 备注
QUERIES = [
    # ---- 路 A：检索层（DDG 全球结果，服务端抓取）----
    dict(q="OEM yoga mat manufacturer China private label", ch="serp", via="ddg", urls=[
        "https://pureasanayoga.com/",
        "https://yewayoga.com/",
        "https://yewayoga.com/custom-yoga-mat/",
        "https://pureasanayoga.com/yoga-mat-manufacturer-in-china/",
        "https://www.made-in-china.com/factory/yoga-mats.html",
        "https://www.alibaba.com/private-label-yoga-mat-suppliers.html",
        "https://www.alibaba.com/showroom/yoga-mat-private-label.html",
        "https://www.yanrefitness.com/yoga-mat-factories-china/",
        "https://www.chinahappyfitness.com/private-label-yoga-mat.html",
        "https://htsyoga.com/",
    ]),
    dict(q="yoga mat factory China MOQ 100 private label", ch="serp", via="ddg", urls=[
        "https://pureasanayoga.com/",
        "https://www.alibaba.com/private-label-yoga-mat-suppliers.html",
        "https://mingyogamat.com/wholesale-custom-yoga-mats/",
        "https://www.torquepilates.com/",
        "https://www.fdmyoga.com/",
        "https://www.made-in-china.com/products-search/hot-china-products/Private_Label_Yoga_Mat.html",
        "https://www.made-in-china.com/factory/yogamat.html",
        "https://www.alibaba.com/showroom/yoga-mat-private-label.html",
        "https://yewayoga.com/",
        "https://www.aurayogamat.com/blog/private-label-yoga-mat-manufacturing",
    ]),
    dict(q="PU rubber yoga mat supplier wholesale private label", ch="serp", via="ddg", urls=[
        "https://www.wavar.com/yoga-mats/",
        "https://htsyoga.com/yoga-mats/pu-yoga-mats/",
        "https://thelunayoga.com/",
        "https://pureasanayoga.com/products/pu-yoga-mats/",
        "https://theyogamats.com/rubber-yoga-mats/",
        "https://htsyoga.com/yoga-mats/rubber-yoga-mats/",
        "https://theyogamats.com/yoga-mats/",
        "https://pureasanayoga.com/products/",
        "https://www.tcyogamat.com/products",
        "https://www.nicegoodyoga.com/yoga-and-pilates-mats/",
    ]),
    # ---- 路 A：检索层（托管侧检索，同口径但引擎不同，单独标注）----
    dict(q="OEM yoga mat manufacturer China private label wholesale", ch="serp", via="hosted", urls=[
        "https://www.yoga-supplies.com/?p=771/",
        "https://www.yogamatmanufacturers.com/",
        "https://yogamatcustom.com/our-factory/",
        "https://pureasanayoga.com/",
        "https://wellfitsource.com/es/about",
    ]),
    dict(q="wholesale TPE yoga mat supplier bulk MOQ custom logo", ch="serp", via="hosted", urls=[
        "https://dghunlon.en.made-in-china.com/product/oOwxcbzPLIkh/x.html",
        "https://htsyoga.com/yoga-mats/tpe-yoga-mats/silk-screen-printing-tpe-yoga-mat/",
        "https://sansd-eva.en.made-in-china.com/product/MFIArRPEJTiC/x.html",
        "https://www.bsmyogamats.com/wholesale-foldable-custom-printed-tpe-yoga-mat_p130.html",
        "https://juliachouli.en.made-in-china.com/product/MvRQoeBGfbVX/x.html",
    ]),
    dict(q="custom printed yoga mats manufacturer factory bulk order", ch="serp", via="hosted", urls=[
        "https://www.yogamatmanufacturers.com/",
        "https://fdmsport.com/custom-yoga-mats",
        "https://www.fdmsport.com/",
        "https://www.sanfanyoga.com/Custom-Print-Soft-Natural-Eco-Friendly-Exercise-Yoga-Mats-pd72800777.html",
        "https://www.archiyoga.com/product/personalized-tpe-yoga-mats-with-full-surface-printing",
    ], note="发现老站 sanfanyoga.com 出现在结果中"),
    dict(q="cork yoga mat manufacturer OEM factory China supplier", ch="serp", via="hosted", urls=[
        "https://www.yogamatmanufacturers.com/",
        "https://www.ecocorker.com/product/cork-for-yoga-sports/cork-yoga-mat/",
        "https://www.ecocorker.com/custom-cork-yoga-mat-manufacturer-fsc-oem-wholesale-supplier",
        "https://www.tianleicork.com/info/cork-yoga-fitness-gear-revolution-how-a-chi-103375495.html",
        "https://www.realcorkwood.com/aboutus.html",
    ]),
    dict(q="best yoga mat manufacturers in China list suppliers", ch="serp", via="hosted", urls=[
        "https://b2bdata.baidu.com/rank/all-area/sports-gear/yoga-supplies/yoga-mat",
        "https://b2b.baidu.com/land/f513e25cc0aa133959e0c7c426d20e64",
        "https://b2bdata.baidu.com/rank/all-area/sports-gear/yoga-supplies/yoga-mat?rankType=all",
        "https://www.accio.com/supplier/yoga-mat-china-manufacturer",
        "https://www.accio.com/supplier/china-yoga-mat-factory",
    ], note="accio.com 对比表里已收录 Xiamen Sanfan Fitness（4.7 分/MOQ 1）"),
    dict(q="yoga mat manufacturer Fujian Xiamen OEM factory direct", ch="serp", via="hosted", urls=[
        "https://www.sanfanyoga.com/about-us.html",
        "https://finalscout.com/company/sanfan_fitness",
        "https://m.b2b168.org/huangye/8715728",
        "https://m.b2b168.org/card/meireneryoga",
        "https://www.sanfanyoga.com/company-profile.html",
    ], note="老站 3/5 席位 + 第三方目录 finalscout 收录品牌"),
    # （AI 答案层样本见下方 AI_SAMPLES，口径不同，不混入本列表）
]

# ---------------------------------------------------------------- 路 B 原始样本
# 只登记**成功取到答案**的采样；失败/限流的须单列，绝不能当「无提及」计入分母
# —— 否则基线会被系统性压低（首版差点犯这个错）。
AI_SAMPLES = [
    dict(q="OEM yoga mat manufacturer in China private label", run="A",
         brand=True, brand_attrib="阿里巴巴（说成「在阿里巴巴上提供 TPE 瑜伽垫定制，MOQ 10 件起」）",
         cited_old=False, cited_new=False, src_domains=[],
         note="答案正文点名 Xiamen Sanfan，但叙事完全来自平台页"),
    dict(q="OEM yoga mat manufacturer in China private label", run="B",
         brand=False, brand_attrib="", cited_old=False, cited_new=False,
         src_domains=["alibaba.com", "china.cn", "goldsupplier.com",
                      "made-in-china.com", "shengde.net.cn"],
         note="同一问题两次采样，来源池已不同 → AI 答案非确定性，需多次采样"),
    dict(q="best yoga mat manufacturers in China", run="B",
         brand=False, brand_attrib="", cited_old=False, cited_new=False,
         src_domains=["china.cn", "goldsupplier.com", "jd.com", "mouldsnet.com",
                      "smzdm.com", "taobao.com"],
         note="答案列举厦门瑞盛/安徽Camper/苏州ProCircle 等，来源多为中文站"),
    dict(q="cork yoga mat manufacturer OEM factory", run="A",
         brand=True, brand_attrib="自有站（来源即 sanfanyoga.com）",
         cited_old=True, cited_new=False,
         src_domains=["sanfanyoga.com", "made-in-china.com"],
         note="★ 铁证：来源 favicon 请求 cdn.metaso.cn/favicon/sanfanyoga.com.ico；"
              "答案正文写「厦门桑凡体育用品有限公司（Xiamen Sanfan）」"),
]

# 采样失败（限流）：必须登记，但不计入分母
AI_FAILED = [
    dict(q="wholesale TPE yoga mat supplier private label", reason="返回 137 字符空壳（限流）"),
    dict(q="custom printed yoga mats factory MOQ 100", reason="返回 132 字符空壳（限流）"),
    dict(q="cork yoga mat manufacturer OEM factory", reason="第二次采样被限流（仅 run A 有效）"),
]

LIMITS = [
    "Perplexity / ChatGPT / Gemini / Google AI Overviews **本机不可达**（DNS 被污染：chatgpt.com→31.13.94.36、google.com→31.13.92.37，均为 Facebook IP；TCP 也不通），本轮无直采数据。**这是本基线最大的盲区**——目标客群用的正是这几家。",
    "路 A 的 `ddg` 与 `hosted` 是**两个引擎**，域频次不可直接相加，需分列。",
    "路 B 用秘塔（中文 AI 引擎），答案语言与来源池偏向中文站/平台页，与海外买家的 ChatGPT/Perplexity 不完全同分布 —— 只作**趋势基线**，不能当绝对值。",
    "路 B 的 AI 答案**非确定性**：同一问题两次采样来源池不同。单次采样不足以定性，复测须多次采样。",
    "秘塔连续提问约 6 次后开始限流（返回 130 字符空壳）。**限流样本必须剔除，不能当「无提及」计入**，否则基线被系统性压低。",
    "DDG 有速率限制，连续请求会返回 BLOCKED；复测需间隔 ≥60s。",
    "秘塔来源域名**只能从 favicon 请求采集**（`cdn.metaso.cn/favicon/<域名>.ico`）：来源卡片 innerText 只有标题、锚点无 href。靠标题里的公司名推断域名 = 不严谨。",
    "`geo citations` 需 API key（推荐 `PERPLEXITY_API_KEY`，另有 serpbase 可选 Google SERP + AI Overview），本机无该凭证。",
]


def domain_of(url: str) -> str:
    d = re.sub(r"^https?://", "", url).split("/")[0].lower()
    return d[4:] if d.startswith("www.") else d


def root_domain(d: str) -> str:
    """把子域归并到根域（xxx.en.made-in-china.com → made-in-china.com）。"""
    parts = d.split(".")
    for i in range(len(parts) - 1):
        cand = ".".join(parts[i:])
        if cand.count(".") <= 1:
            return cand
    return d


def classify(root: str) -> str:
    for name, keys in TYPE_RULES:
        if any(root == k or root.endswith("." + k) for k in keys):
            return name
    return "competitor-site"


def analyse() -> dict:
    serp = [x for x in QUERIES if x["ch"] == "serp"]
    ai = AI_SAMPLES

    freq_by_engine = defaultdict(Counter)
    type_counter = Counter()
    owned_slots = Counter()
    q_with_owned = Counter()
    dom_examples = {}

    for rec in serp:
        engine = rec["via"]
        seen_this_q = set()
        for u in rec["urls"]:
            root = root_domain(domain_of(u))
            freq_by_engine[engine][root] += 1
            type_counter[classify(root)] += 1
            dom_examples.setdefault(root, u)
            if root in OWNED:
                owned_slots[root] += 1
                seen_this_q.add(root)
        for root in seen_this_q:
            q_with_owned[root] += 1

    total_slots = sum(type_counter.values())
    owned_total = sum(owned_slots.values())

    # 路 B：AI 答案层（分母只含成功采样）
    ai_mention = {"sanfan": 0, "fjsanfan": 0, "sanfanyoga": 0}
    ai_detail = []
    src_domain_freq = Counter()
    for rec in ai:
        ai_mention["sanfan"] += int(rec["brand"])
        ai_mention["fjsanfan"] += int(rec["cited_new"])
        ai_mention["sanfanyoga"] += int(rec["cited_old"])
        for d in rec["src_domains"]:
            src_domain_freq[d] += 1
        ai_detail.append({k: rec[k] for k in
                          ("q", "run", "brand", "brand_attrib", "cited_old", "cited_new",
                           "src_domains", "note")})

    # 自审：声明的引用必须能在来源域里找到（避免再犯「靠标题推断域名」的错）
    audit = []
    for rec in ai:
        for flag, dom in (("cited_old", "sanfanyoga.com"), ("cited_new", "fjsanfan.com")):
            if rec[flag] and not any(d == dom or d.endswith("." + dom) for d in rec["src_domains"]):
                audit.append(f"  ✗ {rec['q']}（run {rec['run']}）声明 {flag}=True，但来源域里没有 {dom}")
        if any(d == "sanfanyoga.com" for d in rec["src_domains"]) and not rec["cited_old"]:
            audit.append(f"  ✗ {rec['q']}（run {rec['run']}）来源域含 sanfanyoga.com 但未标记 cited_old")
    if not audit:
        audit.append("  ✓ 全部声明与来源域一致（引用的域名都出现在 favicon 采集结果里）")

    return {
        "stamp": STAMP,
        "counts": {
            "serp_queries": len(serp),
            "ai_samples": len(ai),
            "ai_failed": len(AI_FAILED),
            "serp_result_slots": total_slots,
            "owned_slots": owned_total,
        },
        "freq_by_engine": {k: dict(v.most_common()) for k, v in freq_by_engine.items()},
        "types": dict(type_counter.most_common()),
        "owned": {"slots": dict(owned_slots), "queries_hit": dict(q_with_owned)},
        "ai": {"mentions": ai_mention, "detail": ai_detail,
               "src_domain_freq": dict(src_domain_freq.most_common())},
        "ai_failed": AI_FAILED,
        "audit": audit,
        "examples": dom_examples,
    }


def render_md(a: dict) -> str:
    c = a["counts"]
    L = []
    A = L.append

    A(f"# fjsanfan.com AI 引用基线（首测 {a['stamp']}）")
    A("")
    A("> 站内 GEO 已 78/100（技术层 22/22、三项站点审计全 0）。再修站内上不去 —— 瓶颈在**站外**。")
    A("> 本文件给出第一份可复测的站外数字。")
    A("")

    A("## 一、结论（三句话）")
    A("")
    A(f"1. **新站 `fjsanfan.com`：{c['serp_queries']} 组检索查询（{c['serp_result_slots']} 个席位）"
      f"+ {c['ai_samples']} 次 AI 提问，出现 **0** 次。**")
    A(f"2. 品牌实体本身**已被 AI 认识**：老站 `sanfanyoga.com` 拿到 {c['owned_slots']} 个检索席位，"
      f"并在 AI 答案里被**实名引用为来源**（favicon 铁证）。")
    A("3. 所以问题不是「AI 不知道三梵」，而是**「AI 把三梵归因到老站和平台，而不是新站」**。"
      "站内已经把该做的做完了，接下来要解决的是**外部信号的指向**。")
    A("")

    A("## 二、路 A：检索层引用槽位（谁占着 AI 的来源池）")
    A("")
    A(f"样本：{c['serp_queries']} 组查询、{c['serp_result_slots']} 个结果席位。")
    A("")
    for engine in ("ddg", "hosted"):
        f = a["freq_by_engine"].get(engine) or {}
        if not f:
            continue
        n = sum(f.values())
        A(f"### 引擎：{engine}（{n} 个席位）")
        A("")
        A("| 域 | 席位 | 占比 | 类型 |")
        A("|---|---:|---:|---|")
        for dom, cnt in list(f.items())[:14]:
            A(f"| `{dom}` | {cnt} | {cnt*100//max(n,1)}% | {classify(dom)} |")
        A("")

    A("### 席位按来源类型")
    A("")
    t = a["types"]
    tot = sum(t.values())
    A("| 类型 | 席位 | 占比 |")
    A("|---|---:|---:|")
    label = {"marketplace": "B2B 平台（阿里/中国制造网/百度B2B）",
             "competitor-site": "竞品制造商官网",
             "owned": "**我方站点**",
             "ai-aggregator": "AI 供应商聚合/目录"}
    for k, v in t.items():
        A(f"| {label.get(k, k)} | {v} | {v*100//max(tot,1)}% |")
    A("")
    comp = t.get("competitor-site", 0)
    mk = t.get("marketplace", 0)
    own = t.get("owned", 0)
    A(f"**读法**：竞品**自有官网**占了 {comp*100//max(tot,1)}%（{comp} 席），平台占 {mk*100//max(tot,1)}%（{mk} 席），"
      f"我方仅 {own} 席。这说明两件事：① 平台是 AI 取供应商的高频来源，不能丢；"
      f"② 但**席位大头给了竞品官网** —— 也就是说「自有站进引用池」这条路是通的，"
      f"竞品正在走，只是新站还没拿到入场资格。")
    A("")

    A("### 我方席位明细")
    A("")
    A("| 域 | 席位 | 命中的查询数 |")
    A("|---|---:|---:|")
    for dom, cnt in a["owned"]["slots"].items():
        A(f"| `{dom}` | {cnt} | {a['owned']['queries_hit'].get(dom, 0)} |")
    A(f"| `fjsanfan.com` | **0** | **0** |")
    A("")

    A("## 三、路 B：AI 答案层（真 AI 引擎答不答你）")
    A("")
    A(f"样本：秘塔 AI 搜索**成功采样 {c['ai_samples']} 次**"
      f"（另有 {c['ai_failed']} 次被限流作废，不计入分母 —— 失败 ≠ 无提及）。")
    A("")
    A("| 指标 | 命中 | 命中率 |")
    A("|---|---:|---:|")
    m = a["ai"]["mentions"]
    nq = max(c["ai_samples"], 1)
    A(f"| 答案正文提到品牌 SANFAN | {m['sanfan']} | {m['sanfan']*100//nq}% |")
    A(f"| 来源列表含新站 fjsanfan.com | **{m['fjsanfan']}** | {m['fjsanfan']*100//nq}% |")
    A(f"| 来源列表含老站 sanfanyoga.com | {m['sanfanyoga']} | {m['sanfanyoga']*100//nq}% |")
    A("")
    A("逐次采样：")
    A("")
    for d in a["ai"]["detail"]:
        flags = []
        if d["brand"]:
            flags.append(f"提到品牌（归因：{d['brand_attrib'] or '未注明'}）")
        if d["cited_old"]:
            flags.append("**引老站**")
        if d["cited_new"]:
            flags.append("**引新站**")
        src = "、".join(f"`{x}`" for x in d["src_domains"][:6]) if d["src_domains"] else "（该次未采集来源域）"
        A(f"- run {d['run']}｜`{d['q']}`")
        A(f"  - 结论：{'、'.join(flags) if flags else '无我方信号'}")
        A(f"  - 来源域：{src}")
        if d.get("note"):
            A(f"  - 备注：{d['note']}")
    A("")
    A("### 被引用的来源域排行")
    A("")
    sf = a["ai"]["src_domain_freq"]
    if sf:
        A("| 来源域 | 出现次数 |")
        A("|---|---:|")
        for d, n in list(sf.items())[:12]:
            A(f"| `{d}` | {n} |")
        A("")
    A("**关键个案**：`cork yoga mat manufacturer OEM factory` 一条，秘塔把 "
      "`www.sanfanyoga.com` 列为来源，答案正文写「厦门桑凡体育用品有限公司（Xiamen Sanfan）」——"
      "证明**品牌的 AI 可引用性已经存在**，只是全部落在老站。")
    A("")
    A("另一条同样值得记：`OEM yoga mat manufacturer in China private label` 里，"
      "AI 把 SANFAN 描述成「在阿里巴巴上提供 TPE 瑜伽垫定制，MOQ 10 件起」——"
      "**品牌信息被平台页重塑**，买家看到的是平台叙事，不是工厂自己的口径。")
    A("")
    A("还暴露一个工具事实：**AI 答案是非确定性的**——同一个问题在两次采样里，"
      "一次把 SANFAN 说成「阿里巴巴上的供应商」，另一次答案里根本没有 SANFAN。"
      "所以单次采样不能当结论，复测必须多次采样取比率。")
    A("")
    A("### 口径自审")
    A("")
    A("```")
    for l in a["audit"]:
        A(l)
    A("```")
    A("")

    A("## 四、本次采样的限制（影响解读，须一并看）")
    A("")
    for x in LIMITS:
        A(f"- {x}")
    A("")

    A("## 五、下一轮该盯什么")
    A("")
    A("| 指标 | 当前基线 | 复测目标 |")
    A("|---|---|---|")
    A("| fjsanfan.com 检索席位 | **0** / 60 | ≥1（进任一榜即算突破） |")
    A("| fjsanfan.com AI 引用 | **0** / 4 | ≥1 |")
    A(f"| 品牌 AI 提及率 | {a['ai']['mentions']['sanfan']}/{c['ai_samples']}，且归因老站/平台 | 提及率升 + **归因转向新站** |")
    A("| 第三方目录收录 | 2（finalscout、accio），均指向老站 | 累加，且**至少 1 条指向新站** |")
    A("")
    A("**优先动作（按性价比排序）**")
    A("")
    A("1. **把老站的引用权重导到新站** —— 老站已被 AI 实名引用，这是现成资产。"
      "在 sanfanyoga.com 上给出指向 fjsanfan.com 的明确实体关联（同组织 → 新站为官方站点），"
      "比从零建信号快得多。")
    A("2. **补齐第三方目录实体**（finalscout/accio 已收录品牌，但指向老站）："
      "统一 NAP + 站点字段，把新站作为主站写入。")
    A("3. **内容是给「被引用」用的，不是给「排名」用的**："
      "竞品官网占 65% 席位靠的是成篇的规格/认证/FAQ 可引用文本，新站的 1331 页结构已达标，"
      "接下来拼的是**外部指向新站的链接与提及**。")
    A("")
    A("> 复测方式见脚本头部注释。数字口径固定后即可逐月对照。")
    A("")
    return "\n".join(L)


def main() -> None:
    a = analyse()
    OUTDIR.mkdir(parents=True, exist_ok=True)
    jf = OUTDIR / f"geo_citation_baseline_{FILE_STAMP}.json"
    mf = OUTDIR / f"geo_citation_baseline_{FILE_STAMP}.md"
    jf.write_text(json.dumps(a, ensure_ascii=False, indent=1), encoding="utf-8")
    md = render_md(a)
    mf.write_text(md, encoding="utf-8")
    print(md)
    print(f"\n已写出：\n  {jf}\n  {mf}")


if __name__ == "__main__":
    main()
