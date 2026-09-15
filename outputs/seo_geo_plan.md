# fjsanfan.com SEO / GEO 优化方案

生成日期：2026-09-14
评估框架：AgriciDaniel/codex-seo `seo-geo` v1.9.6（已安装到 `~/.workbuddy/skills/seo-geo/`）
评估对象：1268 个 HTML 页（EN 根 + de/ja/ko/fr/it/es 6 语言 + 中文同页切换）

---

## 一、技能调研结果

| 来源 | 候选 | 星级 | 最后更新 | 结论 |
|---|---|---|---|---|
| GitHub | `AgriciDaniel/codex-seo` → `skills/seo-geo` | 710★ | 2026-09-11 | ✅ **已安装**。纯 Markdown、零依赖、MIT |
| GitHub | `curiositech/some_claude_skills` → `ultimate-seo-geo-skill` | 211★ | 2026-09-06 | 备选。CORE-EEAT 80 项 + CITE 40 项，24 个诊断脚本需装 Python 依赖 |
| GitHub | `osvaldoabel/geo-skill` | 2★ | 2026-04-11 | ❌ 停更 5 个月，作者已弃 |
| GitHub | `zubair-trabzada/geo-seo-claude` | — | — | ❌ 16 子技能偏 agency 获客/报价，与本站无关 |
| SkillHub 市场 | 语义搜索 "seo geo" / "SEO优化" | — | — | ❌ 最高相关度 0.050，全是无关技能（self-improving-agent 等） |

**安全审计**（安装前已执行）：`seo-geo` 目录仅 2 个文件（SKILL.md 9837 字节 + LICENSE.txt 142 字节）。
扫描 `curl` / `wget` / `bash -c` / `eval(` / `os.system` / `subprocess` / `rm -rf` / `sudo` / `API_KEY` /
`TOKEN` / `.env` / `base64` / `requests.post` 等 18 个危险模式 —— **全部 0 命中**。
不读凭据、不发网络请求、不需要任何 API key。判定 **P2（安全）**。

**为什么没有全量装 codex-seo**：它的 `seo-audit` 依赖仓库内 50 个 `scripts/*.py`（`fetch_page.py`、
`analyze_geo.py` 等）与 DataForSEO/Gemini 付费 API。只拷 SKILL.md 会指向不存在的路径，反而变成坏技能。
本站已有 `i18n_build/seo_skill_checks.py` 承担同类职责，因此只取方法论层的 `seo-geo`。

---

## 二、现状评分：46 / 100（Needs Work）

| 维度 | 权重 | 实得 | 实测依据 |
|---|---|---|---|
| 可引用性 Citability | 25% | **8** | 129 个小节首段，中位 47 词，**最大 131 词**，落在最优区间 134–167 的为 **0 段** |
| 结构可读性 | 20% | 14 | H1→H2→H3 层级完整；问答式标题 5–9 个/篇；有表格与列表 |
| 多模态 | 15% | **3** | 全站 1268 页：**0 个 `<video>`、0 个 `<iframe>`、0 个 `<canvas>`**，每篇博客仅 1 张封面图 |
| 权威与品牌信号 | 20% | **6** | 有 Organization / Article / FAQPage schema；但 **sameAs 全站 0 处、社媒外链 0 处、一手来源引用 0 处**（外链仅 2290 个 WhatsApp 按钮） |
| 技术可达性 | 20% | 15 | 静态站天然 SSR ✅、llms.txt 存在（5194 字节） ✅、sitemap 1267 条 ✅、HSTS ✅；**robots.txt 未显式放行 AI 爬虫** |

判定含义（框架原文）：*AI 可能找得到，但不会引用你的内容。*

### 已经做对的（不要动）
- `llms.txt` 质量很好 —— 有 "Verified facts (safe to cite)" 段，公司/成立年/地址/商业模式/MOQ/合规/联系方式齐全，是 AI 直接可引用的结构化事实块
- 10 篇博客均有 `Article` + `FAQPage` + `Organization` + `ImageObject` JSON-LD
- 可见更新日期（post-meta）10 篇全有
- 静态站无 JS 依赖 —— AI 爬虫不执行 JS，这条是硬优势

---

## 三、优化方案（按 ROI 排序）

### P0 — 零风险纯增量（预估 1–2 小时）

> **执行状态（2026-09-14 更新）**：1、2、4 已完成并推送（`eb608a3ec`）；3 已写好脚本，等官方主页 URL 后一键执行。

| # | 动作 | 影响维度 | 状态 / 具体做法 |
|---|---|---|---|
| 1 | **robots.txt 显式放行 AI 爬虫** | 技术 20% | ✅ **已完成**。11 个 UA 段：GPTBot / OAI-SearchBot / ChatGPT-User / ClaudeBot / anthropic-ai / Claude-User / PerplexityBot / Google-Extended / Meta-ExternalAgent / CCBot / *。CCBot 默认放行（与改动前行为一致），文件内已注释如何切 Disallow |
| 2 | **补 `dateModified`** | 权威 20% | ✅ **已完成**。70 个 blog 页（10 篇 × 7 语言）全部 `dateModified: 2026-09-14`，与可见的 "Updated Sep 2026" 对齐。**额外修掉一个老 bug**：60 个语言版 Article 的 `mainEntityOfPage` 原本错指 EN URL，已改为自身 URL（与 canonical 一致） |
| 3 | **Organization 补 `sameAs`** | 权威 20% | ⏳ **等 URL**。脚本 `i18n_build/add_sameas.py` + 配置 `i18n_build/sameas.json` 已就位，填入后 `--apply` 即可，幂等。**全站 0 处社媒外链，必须外部提供，不能猜** |
| 4 | **llms.txt 补全** | 技术 20% | ✅ **已完成**。blog 条目 9 → 10（补 `private-label-yoga-mats`），每条加一句"该页能回答什么"的 AI 摘要；新增 `Last updated: 2026-09-14` 与产能事实（10 条产线 / 年产 100 万片）；"9 sourcing guides" 更正为 10。文件 5194 → 6170 字节 |

### P1 — 本周（需要写内容）

| # | 动作 | 影响维度 | 说明 |
|---|---|---|---|
| 5 | **段落合并成 134–167 词答案块** | **可引用性 25%（最大提升项）** | 不是重写，是把现有 2–4 个相邻短段合并成自足块：开头 40–60 词直接给答案，后接数据支撑。当前中位 47 词太碎，AI 只能拆成碎片引用 |
| 6 | **补一手来源外链** | 权威 20% | 全站内容型外链为 0。compliance 篇应引用 ECHA（REACH）、OEHHA（CA Prop 65）、EN 71 官方；vet-factory 篇引用 ISO/BSCI 官方。这是"claims attributed with specific sources" |
| 7 | **加 Person 作者 schema** | 权威 20% | 现在 `author` 是 Organization。补一个真实的人（工厂/技术负责人）+ 资历 + LinkedIn。E-E-A-T 的 Experience 维度 |

### P2 — 本月（高投入高回报）

| # | 动作 | 影响维度 | 说明 |
|---|---|---|---|
| 8 | **多模态补图表** | 多模态 15% | 全站 0 视频 0 图表。先做零 JS 的 SVG 数据图（MOQ 阶梯价格曲线、TPE/PU/橡胶性能对比矩阵），既提 GEO 也不拖 CWV |
| 9 | **原创数据** | 可引用性 25% | 12 年工厂经验 = 独有的、别处没有的数据。例：「2026 年 TPE 瑜伽垫成本结构拆解」「100 片小单的真实溢价构成」。Unique data points 是 AI 最爱引用的 |
| 10 | **品牌提及建设** | 权威 20% | Ahrefs 2025 研究（7.5 万品牌）：YouTube 提及与 AI 引用的相关性 **0.737**，远高于外链的 0.266。你本来就在做短视频，可复用。Reddit（r/yoga、r/supplychain）次之 |

---

## 四、两个需要你拍板的点

### 0. P0-3 `sameAs` 需要你给 3 个 URL（阻塞中）

`sameAs` 是"实体同一性"声明，填错 = 主动把别家公司的身份挂到自己名下。搜索时发现一个**高危同名干扰**：

| 实体 | URL | 与本站关系 |
|---|---|---|
| FUJIAN SANFAN（本尊） | fjsanfan.com | — |
| **SANFAN FITNESS / 厦门三梵健身** | sanfanyoga.com、linkedin.com/company/sanfan-fitness-co-ltd、linkedin.com/showcase/sanfanyogamat、facebook.com/Xiamen-sanfan-fitness-327305177989829 | ❌ **厦门同业，2013 年成立，同名**。就是一直在抢 "SANFAN" 关键词那家。**绝对不能填** |
| Fujian Sanfan Sports Products Industry Co., Ltd. | yogasanfan.en.alibaba.com | ⚠️ **疑似本尊**（公司名/成立 2013/福建/主营瑜伽垫全对上），**需你确认** |

需要你确认/补充的（有几个填几个，1 个也行）：
1. **阿里国际站店铺** —— 是 `https://yogasanfan.en.alibaba.com` 吗？
2. **LinkedIn 公司页** —— FUJIAN SANFAN 官方的（不是上面那两个）？
3. **YouTube / 独立站外的任一官方主页** —— 有吗？

确认后我填进 `i18n_build/sameas.json`，一条命令注入全站（约 91 页含 Organization 节点 + 70 个 blog 页的 author/publisher）。

---

**1. 段落合并（第 5 项）要不要做？**
这是提升最大的一项（25% 权重，当前只拿到 8/25），但也改动最大。有两种做法：
- **保守**：只给每篇的 h2 首段补写 40–60 词的直接答案句，不动其余结构。快，但只拿回部分分。
- **彻底**：按 134–167 词重构答案块。慢，且要同步 7 个语言版。

**2. robots.txt 要不要屏蔽 CCBot？**
CCBot 是 Common Crawl 的训练爬虫，不影响 AI 搜索可见性，但会把内容喂给模型训练。
放它进来 = 内容被学习；屏蔽 = 内容只在 AI 搜索时被引用。两种策略都合理，看你倾向。

---

## 五、验收方式

方案落地后应可复测。建议把 GEO 五项纳入既有验收链：
```
i18n_build/check_zh_parity.py      # 中英内容对等（已有）
i18n_build/seo_skill_checks.py     # Schema/内容质量/GEO（已有，需扩 GEO 五项）
i18n_build/verify_listicle.cjs     # 浏览器级（已有）
```
新增断言建议：`dateModified` 覆盖率、`sameAs` 存在性、答案块词数落在 134–167 的比例。
