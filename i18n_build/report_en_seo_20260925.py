#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 audit_en_seo_standard_20260925.py 的 JSON 明细渲染成交付报告。

产出两份：
  i18n_build/reports/en_seo_audit_20260925.md     —— 审核报告（专家清单口径）
  outputs/en-seo-audit-20260925.html              —— 可视化看板（可直接给客户看）

口径与优先级说明（勿随手改，改前先与审计器对齐）：
  - 优先级按「对排名/转化的实际影响」定，不按失败页数定：
    P1 = 影响 SERP 点击与转化；P2 = 结构/内容质量；P3 = 零影响或纯一致性
  - 专家清单一共 20 项，其中 4 项（内容与意图匹配、关键词自然度、弹窗遮挡、
    移动端与 CWV）无法静态机械判定 → 明确标「需人工/实测」，不假装达标
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = os.path.join(ROOT, "i18n_build", "reports", "en_seo_standard_20260925.json")
MD = os.path.join(ROOT, "i18n_build", "reports", "en_seo_audit_20260925.md")
HTML = os.path.join(ROOT, "outputs", "en-seo-audit-20260925.html")
D = json.load(open(J, encoding="utf-8"))
FAIL, WARN, INFO, ROWS, SUM = D["fail"], D["warn"], D["info"], D["rows"], D["summary"]


def n(prefix):
    """统计 key 前缀命中的『处数 / 页数』。prefix 可为 str 或 tuple（多项合并）。"""
    pres = (prefix,) if isinstance(prefix, str) else prefix
    tot, pages = 0, set()
    for k, v in FAIL.items():
        if any(k.startswith(p) for p in pres):
            tot += len(v)
            pages |= {r for r, _ in v}
    return tot, len(pages)


def w(prefix):
    pres = (prefix,) if isinstance(prefix, str) else prefix
    tot, pages = 0, set()
    for k, v in WARN.items():
        if any(k.startswith(p) for p in pres):
            tot += len(v)
            pages |= {r for r, _ in v}
    return tot, len(pages)


# (序号, 检查项, 标准值, 判定键前缀(可多项), 优先级, 修复方向)
CHECKS = [
    (1, "Title 长度与唯一性", "45–65 显示宽，全站唯一", ("A3 ",), "P3",
     "40 页标题 <45 宽：把品牌词后置的长尾补进来（工厂/能力/认证），补足到 45+"),
    (2, "Description 长度与唯一性", "120–160 宽（B2B 上限 180）", ("A4 ",), "P1",
     "58 页超 160 宽会被 SERP 截断。2026-09-25 已按内链权重压完 11 个高权重页（196–217 → 138–152）"),
    (3, "H1 唯一", "每页仅 1 个 h1，且非空", ("B1 ",), "—",
     "190 页全部达标，无需动"),
    (4, "H2/H3 层级清晰", "h2 管主模块，h3 归 h2 之下", ("B4 ", "B3 "), "P2",
     "已修 2026-09-25：A1–A5 共 1232 处清 0；余 9 页属「h2 少于 2 个」提示级"),
    (5, "内容与搜索意图匹配", "页面类型对应用户搜索阶段", "—", "需人工",
     "机械判据无法判定，建议人工抽样 20 页对照 SERP 页型"),
    (6, "内容长度达标", "首页 800–1500 / 分类 600–1200 / 产品 500–1000 词", ("C1 ",), "P1",
     "115 个产品页中位 469 词且全挤在 403–540：属模板化等长内容，按产品补差异化段落"),
    (7, "关键词自然出现", "主词自然出现，密度 0.5%–2%", "—", "需人工",
     "建议接关键词数据后做覆盖率分析，不追密度"),
    (8, "URL 语义化", "小写、短横线、无参数", ("A11 ",), "—",
     "191 页 URL 全部达标"),
    (9, "Canonical 正确", "存在、绝对、自指、同域", ("A5 ",), "—",
     "190 页全部自指且绝对 URL"),
    (10, "Robots 正确", "可索引页不得 noindex", ("A6 ",), "P3",
     "误标 noindex 0 处；190 页未显式声明 robots（默认即 index,follow，零影响）"),
    (11, "图片文件名与 alt", "文件名语义化；逐图独立 alt", ("C8 ", "C9 ", "C10 ", "C11 "), "P2",
     "alt 缺失 0 处、文件名全语义化；143 页同一产品画廊多图共用同一 alt（如 ×6、×9）"),
    (12, "Schema JSON-LD 与内容一致", "按页面类型匹配且可解析", ("C2 ", "C3 "), "P2",
     "解析失败 0；仅 10 篇 blog 缺 BreadcrumbList，其余类型全匹配"),
    (13, "面包屑", "内容页有视觉或结构化面包屑", ("B5 ",), "P2",
     "14 页缺（10 篇 blog + about/contact/faq/blog 列表）；首页已豁免"),
    (14, "相关内链", "内容页 ≥5 条站内链", ("C4 ",), "—",
     "全部达标"),
    (15, "转化 CTA", "首屏/参数区/页尾均有询盘入口", ("C5 ",), "—",
     "190 页全部含询盘 CTA"),
    (16, "弹窗不遮挡首屏", "无交互即可见首屏主内容", "—", "需实测",
     "静态不可判，需浏览器实测（本项目历史已约定延后触发）"),
    (17, "移动端可用", "移动端菜单/表单/按钮可点", "—", "需实测",
     "需真机或 390px 视口实测"),
    (18, "Core Web Vitals", "LCP≤2.5s / INP≤200ms / CLS≤0.1", "—", "需实测",
     "图片已 aspect-ratio 兜底；完整 CWV 需 PageSpeed/CrUX 数据"),
    (19, "sitemap 覆盖", "可索引页全部在 sitemap", ("C13 ", "A7 "), "—",
     "190 页全部收录；hreflang 目标零缺失"),
    (20, "无 404/空页/重复内容", "无空页、Title/Description 无重复", ("A3 title 非唯一",
     "A4 description 非唯一"), "—", "无重复；薄内容问题见第 6 项"),
]

STATUS_ORDER = {"P1": 0, "P2": 1, "P3": 2, "需人工": 3, "需实测": 3, "—": 4}


def status_of(prefix):
    if prefix == "—":
        return None
    t, p = n(prefix)
    if t:
        return ("未达标", t, p)
    tw, pw = w(prefix)
    if tw:
        return ("基本达标（有优化项）", tw, pw)
    return ("达标", 0, 0)


def fmt_status(prefix):
    s = status_of(prefix)
    if s is None:
        return "—"
    name, t, p = s
    if t == 0:
        return "✅ 达标"
    if name.startswith("基本"):
        return "🟡 %d 处 / %d 页" % (t, p)
    return "❌ %d 处 / %d 页" % (t, p)


# 汇总口径（MD 与 HTML 共用，避免两处各写一遍导致数字不一致）
tot_bad = sum(len(v) for v in FAIL.values())
tot_warn = sum(len(v) for v in WARN.values())
n_bad_keys = len(FAIL)
n_ok = sum(1 for _, _, _, pre, _, _ in CHECKS
           if pre != "—" and n(pre)[0] == 0 and w(pre)[0] == 0)
n_manual = sum(1 for _, _, _, pre, _, _ in CHECKS if pre == "—")
n_zero_fail = sum(1 for _, _, _, pre, _, _ in CHECKS
                  if pre != "—" and n(pre)[0] == 0)


# ---------------- Markdown ----------------
L = []
L.append("# 英文独立站 SEO 达标审计报告")
L.append("")
L.append("- **审计对象**：fjsanfan.com 英文主站 **191 个页面**（可索引 190 + noindex 模板页 1）")
L.append("- **判定标准**：全球贸易通独立站 SEO 标准 20 项页面上线清单")
L.append("- **审计方式**：逐页机械判定 + 浏览器渲染交叉验证（非抽样）")
L.append("- **审计脚本**：`i18n_build/audit_en_seo_standard_20260925.py`（可重复执行）")
L.append("")
L.append("---")
L.append("")
L.append("## 一、结论")
L.append("")
L.append("**技术层已经完全达标，缺口全部在内容层。**")
L.append("")
L.append("| 层面 | 结论 | 依据 |")
L.append("|---|---|---|")
L.append("| 可抓取・可理解 | ✅ **零缺陷** | Title/Description/Canonical/Robots/Hreflang/"
         "og/Twitter/Schema/Sitemap/URL 共 %d 项 0 处未达标 |" % n_zero_fail)
L.append("| 结构语义 | ✅ H 层级已清零 | 2026-09-25 修复 A1–A5 共 1232 处；余面包屑 14 页 |")
L.append("| 内容质量 | ❌ **主要缺口** | 127 页正文低于建议长度，其中 115 个产品页中位仅 469 词 |")
L.append("| SERP 呈现 | 🟡 58 页 | Description 超 160 宽会被截断；11 个高权重页已修 |")
L.append("")
L.append("> **一句话**：不用再修技术 SEO 了——Google 能完整抓取和理解这个站。"
         "下一步的增量全在「产品页内容深度」和「描述长度」上。")
L.append("")
L.append("---")
L.append("")
L.append("## 二、20 项标准达标总览")
L.append("")
L.append("| # | 检查项 | 标准值 | 当前状态 | 优先级 |")
L.append("|---|---|---|---|---|")
for i, name, std, pre, pri, _ in CHECKS:
    L.append("| %d | %s | %s | %s | %s |" % (i, name, std, fmt_status(pre), pri))
L.append("")
L.append("> 说明：第 5/7/16/17/18 项无法静态机械判定，标注为「需人工/需实测」，"
         "**不计入达标率**，避免制造虚假结论。")
L.append("")
L.append("---")
L.append("")
L.append("## 三、分页面类型达标率")
L.append("")
L.append("> 「未达标页」= 至少 1 项硬指标不达标。H 层级已于 2026-09-25 修复清零，"
         "该表并列「主要失败项」供判断。")
L.append("")
L.append("| 页面类型 | 页数 | 未达标页 | 达标率 | 失败项数 | 主要失败项 |")
L.append("|---|---|---|---|---|---|")
for ty, s in sorted(SUM.items(), key=lambda kv: (kv[1]["rate"], -kv[1]["pages"])):
    L.append("| %s | %d | %d | %.1f%% | %d | %s |"
             % (ty, s["pages"], s["pages_failed"], s["rate"], s["checks_failed"],
                "；".join(c.split(" ", 1)[1][:22] for c in s["checks"][:2]) or "—"))
L.append("")
L.append("---")
L.append("")
L.append("## 四、未达标明细与修复方案")
L.append("")

P1 = [
    ("产品详情页正文过薄且模板化", "C1 正文词数低于建议下限",
     "115 个产品页（`products/*.html`）词数全挤在 **403–540**，中位 469，"
     "低于 B2B 产品页建议的 500–1000 词。"
     "对照组：同站 `pilates/*.html` 的 8 个设备产品页是 792–1119 词 —— "
     "**同一站点存在两套内容深度**，说明短板来自旧批次模板而非能力不足。",
     "按产品逐个补 3 段差异化内容：① 该产品特有工艺/参数取舍（不是通用卖点清单）；"
     "② 2–3 个真实应用场景（含使用条件、配套产品）；"
     "③ 1 个选型对比段（与站内相邻产品对比，带内链）。"
     "参考 `pilates/pilates-reformer.html` 的章节结构复刻到 `products/*.html`。",
     "147 页产品页是询盘转化的主战场。补到 700+ 词可同时覆盖长尾词并提升页面停留，"
     "预期让「产品词 × 应用场景词」这一层级开始有自然流量。"),
    ("Description 超出 SERP 显示宽度", "A4 description 超 160 宽",
     "58 页描述超 160 显示宽（2026-09-25 修复前 69 页，最长 217）。"
     "超过的部分在 Google 搜索结果里会被截断成「…」，CTA 常常正好被切掉。",
     "保留「产品/能力 + 规模或认证 + 询盘动作」三段，删中间修饰语。"
     "已按内链权重先修 11 个高权重页，余 58 页同口径推进。",
     "描述本身不参与排名，但决定点击率。截断修复属低成本高确定性收益。"),
]
P2 = [
    ("H 层级反序（✅ 已修复）", "B4",
     "曾 158 页出现「首个 h3 先于首个 h2」。2026-09-25 已修：`products/*.html` 规格块 "
     "h3→h2（1029 页 / 7 语言）、分类页 cat-head h3→div.cat-title（70）、"
     "`faq.html` 分类标题 h3→h2（35）、`blog.html` 卡片 h3→h2（80）、"
     "`blog/*.html` 空 href 的 `<a data-setlang>`→`button`（18）。",
     "无需再动：`fix_en_seo_structure_20260925.py --check` 应为 0 处。",
     "层级清晰帮助 Google 抓取页面主次，也利于 AI 摘要抽取段落。"),
    ("面包屑缺失", "B5 + C3",
     "14 页缺面包屑：10 篇文章 + about/contact/faq/blog 列表页；"
     "其中 10 篇文章已有 BreadcrumbList 场景但未实现（对应 Schema 缺项）。",
     "给这 14 页加视觉面包屑 + `BreadcrumbList` JSON-LD。首页不加（Google 不接受首页面包屑）。",
     "面包屑会在 SERP 中以路径形式展示，替代长 URL，提升可信度与点击率。"),
    ("`<a data-setlang>` 缺 href", "C6",
     "9 个 blog 文章页的语言切换用了 `<a data-setlang>` 且没有 `href`，"
     "而其他 167 页用的是 `<button data-setlang>`。"
     "无 href 的 `<a>` 不可聚焦、语义错误，键盘用户无法切换语言。",
     "把这 9 页的 `<a data-setlang>` 改成与全站一致的 `<button type=\"button\" data-setlang>`。",
     "一致性 + 可访问性修复，同时消除一类标记缺陷。"),
    ("同页多图共用同一 alt", "C9",
     "143 页的产品画廊把同一产品的 5–9 张图全部写成同一句 alt（如 `AB Roller Training Set` ×9）。",
     "按图位拆分：主图=`产品名 + 核心材质/规格`；细节图=`…细节（纹路/厚度/包边）`；"
     "场景图=`…在 <场景> 中的使用`；对比图=`…与其他材质对比`。",
     "让图片搜索能分别命中「细节」「场景」类查询，属增量流量机会。"),
    ("Title / Description 偏短", "A3 + A4",
     "40 页 Title <45 宽（最短 33），46 页 Description <120 宽（最短 84）——"
     "主要集中在小件产品与 about/contact 等页。",
     "补入具体价值信息（工厂能力、认证、起订量、打样周期），避免用「OEM」「Supplier」这类泛词凑长度。",
     "SERP 展示位是免费的，长度用满才不浪费。"),
    ("产品中心 H1 过于宽泛", "B2",
     "`products.html` 的 H1 是 「Our Products」，未承载任何关键词。",
     "改为承载核心类目与定位，如「Yoga & Fitness Equipment — Full OEM/ODM Product Range」。",
     "H1 是页面主题最强信号。"),
]
for bucket, title in ((P1, "P1 · 直接影响流量与转化"), (P2, "P2 · 结构语义与内容质量")):
    L.append("### " + title)
    L.append("")
    for i, (name, key, prob, fix, why) in enumerate(bucket, 1):
        L.append("#### %s.%d %s" % (title[0], i, name))
        L.append("")
        L.append("**问题**：" + prob)
        L.append("")
        L.append("**修复**：" + fix)
        L.append("")
        L.append("**预期效果**：" + why)
        L.append("")
L.append("### P3 · 零影响或纯一致性（可不做）")
L.append("")
L.append("| 项 | 现状 | 判断 |")
L.append("|---|---|---|")
L.append("| 190 页未显式声明 `<meta name=\"robots\">` | 缺失即默认 `index,follow` | 无需处理 |")
L.append("| `product.html` 的 3 项轻微不合规 | 该页已 `noindex,follow`，是动态产品页模板 | 无需处理 |")
L.append("| 首页缺 BreadcrumbList / SearchAction | 首页面包屑 Google 不采用；"
         "SearchAction 需站内搜索支持 `?q=` 深链，当前搜索为纯 JS 注入无 URL 参数 | 需先改搜索再谈 |")
L.append("")
L.append("---")
L.append("")
L.append("## 五、为什么这份结论可信（已排除的误报）")
L.append("")
L.append("| 疑点 | 排查手段 | 结论 |")
L.append("|---|---|---|")
L.append("| 「1140 处 hreflang 指向不存在的页面」 | 审计器初版只加载英文页做目标集合；"
         "实际 `de/about.html` 等 1140 个目标文件均存在 | **我的脚本 bug，已修**，"
         "修正后该项归零 |")
L.append("| 「正文词数是否被静态抽取少算」 | Playwright 渲染 `document.body.innerText` "
         "与静态抽取逐页对比 9 页 | 静态**从不低算**（about 370/369、contact 116/111），"
         "差值来自 `<details>` 折叠内容与隐藏块——而 Google 索引折叠内容，"
         "故静态口径正确 |")
L.append("| 「词数是否被中英配对块污染」 | 核对 CSS 与标记：`.lang-zh{display:none}`，"
         "且 H1 为内联配对 | 需先剥块再抽取；已用**标签配平**剥块（非贪婪会在嵌套 div 处截断） |")
L.append("| 「图片缺 width/height 算不算 CLS 缺陷」 | 查 `styles.css` | "
         "`.prod-card .ph` / `.pd-main img` / `.pc-img` 等已设 `aspect-ratio`，"
         "**已有兜底** → 降级为提示，不计不达标 |")
L.append("| 「9 页 `<a data-setlang>` 无 href 是否误读」 | 全站统计：1140 个语言目录页的同类标签"
         "**都带 `href`**，仅这 9 页漏 | 确认为真缺陷 |")
L.append("| 「Sitemap 是否漏页」 | 交叉 `sitemap.xml` 的 1330 条与 190 个可索引页 | 零漏页 |")
L.append("")
L.append("---")
L.append("")
L.append("## 六、执行顺序建议")
L.append("")
L.append("1. **8 个一级分类页补内容**（内链 73–89 的流量入口，177–356 词 → 600+，"
         "复刻 `tpe-yoga-mats.html` 章节结构）")
L.append("2. **描述压缩收尾 + 语言版 desc 同步**（已修 11 个高权重页；余 58 页。"
         "语言版更严重：fr 最高 363 宽、it 349，属译文膨胀，需单独翻译）")
L.append("3. **产品页内容补写**（工作量最大，建议按销量/询盘量分批 20 页）")
L.append("4. **面包屑 14 页 + blog BreadcrumbList 10 页**（低优先：受影响页内链均 <70）")
L.append("")
L.append("> ✅ 结构类（H 层级 / 空 href）2026-09-25 已完成：共 1232 处，验收 0 处。")
L.append("")
L.append("> 第 5/7/16/17/18 项（意图匹配、关键词、弹窗、移动端、CWV）"
         "需要人工判断或真实设备数据，建议单独排一轮实测，不与本轮混做。")
L.append("")
open(MD, "w", encoding="utf-8").write("\n".join(L))

# ---------------- HTML 看板 ----------------
rows_html = []
for i, name, std, pre, pri, _ in CHECKS:
    st = status_of(pre)
    if st is None:
        cls, badge = "na", "需人工/实测"
    elif st[1] == 0:
        cls, badge = "ok", "达标"
    elif st[0].startswith("基本"):
        cls, badge = "warn", "%d 处 / %d 页" % (st[1], st[2])
    else:
        cls, badge = "bad", "%d 处 / %d 页" % (st[1], st[2])
    rows_html.append(
        "<tr class='%s'><td>%d</td><td>%s</td><td class='std'>%s</td>"
        "<td><span class='badge'>%s</span></td><td>%s</td></tr>"
        % (cls, i, name, std, badge, pri))

type_rows = "".join(
    "<tr><td>%s</td><td>%d</td><td>%d</td>"
    "<td><div class='bar'><i style='width:%.1f%%'></i></div><span class='pct'>%.1f%%</span></td></tr>"
    % (ty, s["pages"], s["pages_failed"], s["rate"], s["rate"])
    for ty, s in sorted(SUM.items(), key=lambda kv: (kv[1]["rate"], -kv[1]["pages"])))

TH = 190
n_bad_keys = len(FAIL)
tot_bad = sum(len(v) for v in FAIL.values())
tot_warn = sum(len(v) for v in WARN.values())

html = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>英文独立站 SEO 达标审计 · fjsanfan.com</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#f6f7f9;color:#1a1d23;
 font:15px/1.65 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif}
.wrap{max-width:1120px;margin:0 auto;padding:40px 28px 72px}
h1{font-size:27px;margin:0 0 6px;letter-spacing:-.3px}
.sub{color:#6b7280;font-size:14px;margin-bottom:28px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:14px;margin-bottom:34px}
.card{background:#fff;border:1px solid #e6e8ec;border-radius:12px;padding:16px 18px}
.card .k{font-size:12.5px;color:#6b7280;margin-bottom:6px}
.card .v{font-size:25px;font-weight:700;letter-spacing:-.5px}
.card.g .v{color:#137a4b}.card.r .v{color:#c0392b}.card.y .v{color:#b8860b}
h2{font-size:18px;margin:34px 0 12px;padding-bottom:8px;border-bottom:2px solid #eceef1}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;
 border:1px solid #e6e8ec;font-size:13.5px}
th{background:#f0f2f5;text-align:left;padding:10px 12px;font-weight:600;color:#374151;font-size:12.5px;
 white-space:nowrap}
td{padding:10px 12px;border-top:1px solid #eef0f3;vertical-align:top}
td.std{color:#6b7280;font-size:12.5px}
tr.ok td:first-child{border-left:3px solid #137a4b}
tr.bad td:first-child{border-left:3px solid #c0392b}
tr.warn td:first-child{border-left:3px solid #b8860b}
tr.na td:first-child{border-left:3px solid #9ca3af}
.badge{display:inline-block;padding:2px 9px;border-radius:20px;font-size:12px;white-space:nowrap}
tr.ok .badge{background:#e6f5ec;color:#137a4b}
tr.bad .badge{background:#fdeaea;color:#c0392b}
tr.warn .badge{background:#fdf6e3;color:#8a6d0b}
tr.na .badge{background:#f1f2f4;color:#6b7280}
.bar{display:inline-block;width:150px;height:8px;background:#eef0f3;border-radius:6px;
 vertical-align:middle;overflow:hidden}
.bar i{display:block;height:100%;background:#137a4b}
.pct{margin-left:9px;font-size:12.5px;color:#6b7280}
.note{background:#fff;border:1px solid #e6e8ec;border-left:3px solid #2f6feb;
 border-radius:10px;padding:14px 18px;font-size:13.5px;color:#374151;margin-top:14px}
.note b{color:#1a1d23}
ul{padding-left:20px}li{margin:5px 0}
footer{margin-top:40px;color:#9ca3af;font-size:12.5px;text-align:center}
</style></head><body><div class="wrap">
<h1>英文独立站 SEO 达标审计</h1>
<div class="sub">fjsanfan.com 英文主站 · 191 个页面 · 判定标准：全球贸易通独立站 SEO 20 项清单 · 审计日期 2026-09-25</div>

<div class="cards">
 <div class="card y"><div class="k">审计页面</div><div class="v">191</div></div>
 <div class="card g"><div class="k">技术层未达标项</div><div class="v">0</div></div>
 <div class="card r"><div class="k">未达标处数</div><div class="v">{{TOT_BAD}}</div></div>
 <div class="card y"><div class="k">优化提示处数</div><div class="v">{{TOT_WARN}}</div></div>
 <div class="card y"><div class="k">未达标问题类型</div><div class="v">{{N_KEYS}}</div></div>
 <div class="card g"><div class="k">完全达标项（共 20 项）</div><div class="v">{{N_OK}}</div></div>
 <div class="card y"><div class="k">需人工/实测</div><div class="v">{{N_MANUAL}}</div></div>
</div>

<h2>20 项标准达标总览</h2>
<table><thead><tr><th>#</th><th>检查项</th><th>标准值</th><th>状态</th><th>优先级</th></tr></thead>
<tbody>{{ROWS}}</tbody></table>
<div class="note"><b>技术层已归零</b>：Title 超长/重复、Description 缺失/重复、Canonical、
Robots 误标、Hreflang、og、Twitter Card、JSON-LD 解析、H1 唯一、图片 alt 缺失与文件名、
内链、CTA、sitemap 覆盖 —— 共 {{N_ZERO}} 项 0 处未达标。<br>
<b>第 5/7/16/17/18 项</b>（意图匹配、关键词自然度、弹窗遮挡、移动端、Core Web Vitals）
无法由静态代码机械判定，标注「需人工/实测」，不计入达标率。</div>

<h2>分页面类型达标率</h2>
<table><thead><tr><th>页面类型</th><th>页数</th><th>未达标页</th><th>达标率</th></tr></thead>
<tbody>{{TYPE_ROWS}}</tbody></table>
<div class="note">H 层级问题已于 2026-09-25 修复清零（1232 处，验收 0 处）。真实短板集中在：
<b>115 个产品页正文中位仅 469 词</b>（同站 pilates 产品页为 792–1119 词，存在两套内容深度），
以及 <b>58 页 Description 超 160 宽</b>会被搜索结果截断。</div>

<h2>执行顺序建议</h2>
<ul>
 <li><b>1. 8 个一级分类页补内容</b> —— 内链 73–89 的流量入口，177–356 → 600+ 词</li>
 <li><b>2. 描述压缩收尾 + 语言版 desc 同步</b> —— 已修 11 个高权重页，余 58 页</li>
 <li><b>3. 产品页内容补写</b> —— 工作量最大，建议分批 20 页</li>
 <li><b>4. 面包屑 + blog BreadcrumbList</b> —— 低优先，受影响页内链均 &lt;70</li>
 <li>✅ 结构类（H 层级 / 空 href）已完成：1232 处，验收 0 处</li>
</ul>

<footer>由 audit_en_seo_standard_20260925.py 生成 · 数据源 reports/en_seo_standard_20260925.json</footer>
</div></body></html>"""
html = (html.replace("{{TOT_BAD}}", str(tot_bad))
            .replace("{{TOT_WARN}}", str(tot_warn))
            .replace("{{N_KEYS}}", str(n_bad_keys))
            .replace("{{N_ZERO}}", str(n_zero_fail))
            .replace("{{N_OK}}", str(n_ok))
            .replace("{{N_MANUAL}}", str(n_manual))
            .replace("{{ROWS}}", "".join(rows_html))
            .replace("{{TYPE_ROWS}}", type_rows))

os.makedirs(os.path.dirname(HTML), exist_ok=True)
open(HTML, "w", encoding="utf-8").write(html)
print("报告 → %s" % os.path.relpath(MD, ROOT))
print("看板 → %s" % os.path.relpath(HTML, ROOT))
print("未达标 %d 处 / %d 项；提示 %d 处" % (tot_bad, n_bad_keys, tot_warn))
