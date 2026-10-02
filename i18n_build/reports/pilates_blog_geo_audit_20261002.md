# 普拉提板块 6 篇新博客 —— GEO / SEO 审核报告

日期 2026-10-02 · 站点 https://fjsanfan.com · 判分引擎 geo-optimizer v4.18.3（官方编排器 `run_full_audit`）

> ⚠️ **本报告是「就绪度」审计。** 6 个页面**尚未部署**，GSC 也未配置凭据
> （`seo-ops/gsc_auth.py` 需 `GOOGLE_CLIENT_ID`/`SECRET`，本机无 token 文件）
> → **无法验证真实收录、排名与 AI 引用**。可验证部分见 §B–§E，不可验证部分见 §F。

## 结论速览

| 问题 | 结论 |
|---|---|
| 文章专业度够不够 | **够**。新页 84–85，与站内存量页（基线 81–85）持平或更高，负面信号 0（仅 OEM 页 −1 分） |
| 符合 AI/Google 关键引用词吗 | **符合**。36 条目标 query **全部**在 H2/H3 或正文达 ≥0.75 覆盖（100% 可检索）；其中 15 条（42%）标题层已锚定 |
| 能不能搜索得到 | **本地就绪度全部达标**（sitemap / canonical / hreflang / llms / JSON-LD / 内链）。**但线上搜不搜得到现在无法验证——页面还没部署** |
| 有没有技能能审 | **有一个真引擎**：`geo-optimizer`（47 项 AI 引用度）。其余 seo-* 技能只有 rubric、无脚本 |

**最该知道的一件事**：85 这个总分里 **54 分（64%）是全站同值**（robots/llms/schema/signals/ai_discovery），页面级才是可变的部分 → **别把 85 当「这 6 页写得好」的证明**（详见 §A2）。

## 本轮已实施的改进（P1/P2/P3，2026-10-02）

| 项 | 动作 | 落地处 | 引擎项变化 |
|---|---|---|---|
| 🔴 P1 | robots.txt 补 `Claude-SearchBot` / `Applebot` / `Googlebot` 显式 `Allow: /` | `robots.txt` | `citation_bots_explicit` ❌→✅（站点级 +3） |
| 🔴 P1 | 每页加「这些数字是怎么来的」方法论段（标题固定 `Our methodology`，正文含 `We measured…`） | 生成器 → 6 页 | `First-Party Data` 0/4 → **4/4**（6/6 页满分） |
| 🟠 P2 | 句子级一手数字陈述（`We measured 930 mm as the widest…`，数字在句子里而非只在表里） | 同上（同一段） | 一并吃下 `_OWN_DATA_RE` |
| 🟠 P2 | 新增 `Sources` 小节 + 2 个 Wikipedia 权威外链（仅术语与出处，非产品主张） | 同上 | `Cite Sources` 1/6 → **6/6** |
| 🟡 P3 | 补 3 条只差同义词的 query（`startup` / `door clearance` / `commercial grade`） | 正文 | 关键词覆盖 |
| 🟡 P3 | 团队署名（可核验的团队名，未编造人名）+ Organization `@id` / `sameAs` | 同上 | E-E-A-T 的 Who 层 |

**顺带修掉两处硬编码的错误断言** —— 这是本轮最实质的发现，也是「专业度」审计真正的产出：

- `the longest published packing length is 2570 mm` → 实际最长是 **AL 13 MC 的 2800 mm**
- `the tallest is 860 mm` → 860 只是 AL 12-CR 自身的高度，塔架类木箱实际 **2000 mm**

两处都是**手写的极值脱离了数据源**。修一次不够，所以新增 `i18n_build/pilates_figures_20261002.py`：以已上线族页型号总表为单一事实来源，自动算出 `longest / widest / tallest / heaviest`；页面上每个尺寸与毛重都必须能溯源到公布数据，最高级断言必须等于算出的极值。已接入 `verify_pilates_blog_20261002.py`。

> ⚠️ 该检查器做过 **A/B 实证**：把旧错误（2570 冒充最长、860 冒充最高、捏造的 9999 mm / 777 kg）塞回临时副本，4/4 全部报出，且未改动的原件零误报。

## 工具清单（回答「有没有技能能审」）

| 工具 | 类型 | 可执行 | 本次是否用了 |
|---|---|---|---|
| `geo-optimizer` v4.18.3 | GEO/AEO 审计引擎（47 项 AI 引用度） | ✅ `geo` CLI + Python API | ✅ 主力 |
| `seo-content` | E-E-A-T / 内容质量 rubric | ❌ 仅 SKILL.md，无脚本 | ✅ 按其 rubric 手工判（§E） |
| `seo-page` / `seo-schema` / `seo-hreflang` / `seo-technical` | 单页/结构化/多语言 rubric | ❌ 同上 | ✅ 按其判据自查（§D） |
| `seo-agentic` | AI agent 可读性 | ❌ 仅 rubric | ⚪️ 未展开 |
| `seo-ops` | GSC 真实数据 | ⚠️ 有 `gsc_client.py` 但**未授权** | ❌ 无凭据 |

**结论**：唯一带可执行引擎的是 `geo-optimizer`；其余 seo-* 技能都是 rubric（其内文引用的
`${CLAUDE_PLUGIN_ROOT}/scripts/claude-seo` 在本机不存在）。

⚠️ **本地跑引擎有个坑**：`geo audit` 与所有 `audit_*` 都走 `utils.http.fetch_url`，
**内置反 SSRF 防护 → 对 `127.0.0.1` 恒判 0 分**。本报告用 `_geo_local_harness.py`
把 `fetch_url` 换成磁盘读取、base_url 保持 `https://fjsanfan.com`，判分与线上同构。

## A. 引擎总分

| 页面 | 总分 | 档位 | 引用度(47项) | ChatGPT | Perplexity | Google AI |
|---|---|---|---|---|---|---|
| `blog/pilates-reformer-buyers-guide.html` | **85** | good | 58/100 foundation | 73 | 77 | 73 |
| `blog/pilates-apparatus-differences.html` | **85** | good | 58/100 foundation | 73 | 77 | 73 |
| `blog/pilates-studio-equipment-list.html` | **85** | good | 55/100 foundation | 73 | 77 | 73 |
| `blog/oem-pilates-equipment-china.html` | **84** | good | 57/100 foundation | 73 | 77 | 73 |
| `blog/pilates-studio-layout-guide.html` | **85** | good | 60/100 foundation | 80 | 77 | 80 |
| `blog/pilates-equipment-commercial-use.html` | **85** | good | 56/100 foundation | 73 | 77 | 73 |
| `blog/moq-explained.html` *(基线)* | **85** | good | 56/100 foundation | 73 | 67 | 73 |
| `blog/yoga-mat-spec-guide.html` *(基线)* | **83** | good | 55/100 foundation | 73 | 67 | 70 |
| `pilates/index.html` *(基线)* | **83** | good | 46/100 foundation | 73 | 55 | 83 |
| `index.html` *(基线)* | **81** | good | 41/100 foundation | 58 | 50 | 79 |

档位：0–35 critical · 36–67 foundation · 68–85 good · 86–100 excellent

## A2. ⚠️ 分数构成拆解：总分里有 64% 与页面无关

引擎的 8 个类目里，有 5 个**全站同值**（robots / llms / ai_discovery / signals / schema），换任何一页都是同一批分。把它们剔掉，才看得到页面级的真实差异：

| 页面 | 总分 | 站点级（同值） | 页面级（可变） | 站点占比 |
|---|---|---|---|---|
| `blog/pilates-reformer-buyers-guide.html` | 85 | 54 | **31** | 64% |
| `blog/pilates-apparatus-differences.html` | 85 | 54 | **31** | 64% |
| `blog/pilates-studio-equipment-list.html` | 85 | 54 | **31** | 64% |
| `blog/oem-pilates-equipment-china.html` | 84 | 54 | **30** | 64% |
| `blog/pilates-studio-layout-guide.html` | 85 | 54 | **31** | 64% |
| `blog/pilates-equipment-commercial-use.html` | 85 | 54 | **31** | 64% |
| `blog/moq-explained.html` | 85 | 54 | **31** | 64% |
| `blog/yoga-mat-spec-guide.html` | 83 | 54 | **29** | 65% |
| `pilates/index.html` | 83 | 54 | **29** | 65% |
| `index.html` | 81 | 54 | **27** | 67% |

**判读**：10 页的站点级分完全相同（54 分）。新页（84–85）与基线（81–85）的全部差距只来自页面级那几分，
其中 `content` 项 11–12 分几乎不动、`negative_penalty` 0 到 −3 是主要区分点。
→ **总分只能证明「站点 GEO 基础设施在位、新页没拖后腿」，不能证明单页质量。**
要看单页质量请用 §B（47 项引用度，区分度 41–60）与 §C（目标 query 覆盖）。

## B. AI 引用度（47 项）逐项

### B1 强项与被扣分项（以 reformer 指南页为例）

**已拿满 / 高分（说明页面结构对 AI 引用是友好的）**

| 项 | 得分 |
|---|---|
| Cite Sources | 6/6 |
| Answer-First Structure | 5/5 |
| Technical Terms | 5/5 |
| Easy-to-Understand | 5/5 |
| Unique Words | 3/3 |
| No Keyword Stuffing | 6/6 |
| FAQ-in-Content | 6/6 |
| Content Freshness | 6/6 |
| No Content Decay | 5/5 |
| Content-to-Boilerplate Ratio | 4/4 |

**失分项（按影响排序）**

| 项 | 得分 | 声称影响 | 判定 |
|---|---|---|---|
| Readability Score | 1/8 | +15% | 真实缺口 |
| Citability Density | 0/7 | +15% | 真实缺口 |
| Quotation Addition | 0/6 | +41% | 真实缺口 |
| Statistics Addition | 0/6 | +33% | ⚠️ 工具盲区：规格数字（`1190 × 700 × 1170 mm`、`85 kg`、装箱件数）不在 _STAT_PATTERNS 里→ 对本站是**假阴性**，不是真缺口（下面 §B2 有实测反证） |
| Authoritative Tone | 0/5 | +16% | 真实缺口 |
| Attribution Completeness | 0/5 | +12% | 真实缺口 |
| Fluency Optimization | 2/6 | +29% | 真实缺口 |
| E-E-A-T Signals | 3/7 | +15% | 真实缺口 |
| Multi-Platform Presence | 0/4 | +10% | 真实缺口 |
| Passage Density | 2/5 | +23% | 真实缺口 |
| Nuance/Honesty Signals | 0/3 | +5% | 真实缺口 |
| AI Shopping Readiness | 0/3 | +8% | ⚠️ 工具盲区：站点无 Product 实体（型号级 Product 尚未决策）→ 本项预期 0 |
| ChatGPT Shopping Feed | 0/3 | +8% | ⚠️ 工具盲区：同上 |
| Social Proof | 0/3 | +8% | 真实缺口 |

### B2 实测反证：`Statistics Addition` 是假阴性

引擎源码 `core/citability.py` 的 `_STAT_PATTERNS` 只匹配 `%` / 千分位 / `$` / `million` / `Nx`：

```python
_STAT_PATTERNS = [r"\b\d+(?:\.\d+)?%", r"\b\d{1,3}(?:,\d{3})+", r"\$\d+",
                  r"\b\d+\s*(?:million|billion|trillion|thousand)\b", r"\b\d+(?:\.\d+)?\s*(?:x|X)\b"]
```

**它匹配不到 `1190 × 700 × 1170 mm`、`85 kg`、装箱件数** —— 而这正是本板块的数字主体。
实测页面里被引擎「看不见」的规格数字：

| 页面 | 引擎抓不到的规格数字 | 引擎认定的 stat matches |
|---|---|---|
| `pilates-reformer-buyers-guide.html` | **67** | 0 |
| `pilates-apparatus-differences.html` | **0** | 0 |
| `pilates-studio-equipment-list.html` | **1** | 0 |
| `oem-pilates-equipment-china.html` | **51** | 0 |
| `pilates-studio-layout-guide.html` | **117** | 0 |
| `pilates-equipment-commercial-use.html` | **24** | 0 |

→ **不要把「Statistics +33%」当成待办去补。** 需要补的是句子级的一手事实陈述（见 §E/§G），
而不是换数字格式。

### B3 对照实验：双语 DOM 有没有污染判分？

站点每页同时内嵌 `.lang-en` 与 `.lang-zh`（靠 CSS 切换）。把中文副本整棵移除后重跑引用度：

| 页面 | 整页 | 仅英文 | 差 |
|---|---|---|---|
| `blog/pilates-reformer-buyers-guide.html` | 58 | 54 | -4 |
| `blog/pilates-apparatus-differences.html` | 58 | 54 | -4 |
| `blog/pilates-studio-equipment-list.html` | 55 | 51 | -4 |
| `blog/oem-pilates-equipment-china.html` | 57 | 55 | -2 |
| `blog/pilates-studio-layout-guide.html` | 60 | 56 | -4 |
| `blog/pilates-equipment-commercial-use.html` | 56 | 52 | -4 |
| `blog/moq-explained.html` | 56 | 51 | -5 |
| `blog/yoga-mat-spec-guide.html` | 55 | 51 | -4 |
| `pilates/index.html` | 46 | 42 | -4 |
| `index.html` | 41 | 40 | -1 |

**判读**：仅英文一律**更低**（−1 ~ −6），且基线页同幅（首页 −1、moq −5）。
→ 双语 DOM 没有给新页「虚高」，对照是公平的；同时也说明这 6 页**没有靠堆字骗分**。

## C. 关键引用词覆盖（自建确定性判据）

每条 query = 真实采购方的问法；判据 = 去停用词后的实词覆盖率（标题层 ≥0.8 = 主推）。

**总览**：36 条目标 query → 可检索 **36 / 36**（100%，H2/H3 或正文 ≥0.75）；标题层锚定 15 条（42%）。

⚠️ 词覆盖率是**钝器**：多词 query 少一个词就掉到 0.75 以下，同义说法（`opening` vs `startup`）
会被判成缺口。**精确短语**才是强信号，下面每表都单列。

### `pilates-reformer-buyers-guide.html` —— 标题锚定✅4 / 正文可检索🟡4 / 非主推⚠0（共 8；⚠ 仅指未在标题层锚定，不等于搜不到）

| 目标 query | 精确短语 | title | H1 | H2/H3 | desc | 正文 | 判定 |
|---|---|---|---|---|---|---|---|
| pilates reformer buyer's guide | ✅ | 1.0 | 1.0 | 0.5 | 0.5 | 1.0 | ✅ 主推（标题层锚定） |
| how to choose a pilates reformer | — | 0.67 | 0.67 | 1.0 | 1.0 | 0.67 | 🟡 次级（标题/描述层部分锚定） |
| aluminium vs wood pilates reformer | — | 0.5 | 1.0 | 1.0 | 1.0 | 1.0 | ✅ 主推（标题层锚定） |
| folding pilates reformer | — | 0.67 | 1.0 | 1.0 | 1.0 | 1.0 | ✅ 主推（标题层锚定） |
| pilates reformer frame types | — | 1.0 | 0.5 | 0.75 | 0.5 | 0.75 | ✅ 主推（标题层锚定） |
| what to check before buying a pilates reformer | — | 0.5 | 0.5 | 0.75 | 0.5 | 0.5 | 🟡 正文可检索（非主推） |
| pilates reformer packing size | — | 0.5 | 0.5 | 0.75 | 0.75 | 1.0 | 🟡 正文可检索（非主推） |
| pilates reformer supplier | — | 0.67 | 0.67 | 0.67 | 0.67 | 1.0 | 🟡 正文可检索（非主推） |

### `pilates-apparatus-differences.html` —— 标题锚定✅3 / 正文可检索🟡4 / 非主推⚠0（共 7；⚠ 仅指未在标题层锚定，不等于搜不到）

| 目标 query | 精确短语 | title | H1 | H2/H3 | desc | 正文 | 判定 |
|---|---|---|---|---|---|---|---|
| pilates apparatus explained | ✅ | 1.0 | 1.0 | 0.67 | 0.67 | 0.33 | ✅ 主推（标题层锚定） |
| what is a pilates cadillac | — | 1.0 | 0.5 | 1.0 | 0.5 | 0.5 | ✅ 主推（标题层锚定） |
| pilates reformer vs cadillac | — | 1.0 | 0.33 | 1.0 | 0.67 | 0.67 | ✅ 主推（标题层锚定） |
| pilates reformer vs tower | — | 0.67 | 0.33 | 1.0 | 0.67 | 0.67 | 🟡 次级（标题/描述层部分锚定） |
| what is a pilates wunda chair | — | 0.67 | 0.33 | 0.33 | 0.67 | 0.67 | 🟡 正文可检索（非主推） |
| ladder barrel pilates | — | 0.33 | 0.33 | 0.33 | 0.67 | 0.67 | 🟡 正文可检索（非主推） |
| which pilates equipment to buy first | — | 0.33 | 0.33 | 1.0 | 0.33 | 0.67 | 🟡 次级（标题/描述层部分锚定） |

### `pilates-studio-equipment-list.html` —— 标题锚定✅2 / 正文可检索🟡2 / 非主推⚠1（共 5；⚠ 仅指未在标题层锚定，不等于搜不到）

| 目标 query | 精确短语 | title | H1 | H2/H3 | desc | 正文 | 判定 |
|---|---|---|---|---|---|---|---|
| pilates studio equipment list | ✅ | 1.0 | 1.0 | 0.75 | 0.75 | 1.0 | ✅ 主推（标题层锚定） |
| what equipment does a pilates studio need | ✅ | 0.75 | 0.75 | 1.0 | 0.75 | 1.0 | ✅ 精确短语命中 |
| how many reformers for a pilates studio | — | 0.67 | 0.67 | 1.0 | 0.67 | 1.0 | 🟡 次级（标题/描述层部分锚定） |
| pilates studio startup equipment | — | 0.75 | 0.75 | 0.75 | 0.75 | 0.75 | ⚠ 仅部分词命中 |
| pilates studio opening checklist | — | 0.5 | 0.5 | 1.0 | 0.75 | 0.75 | 🟡 次级（标题/描述层部分锚定） |

### `oem-pilates-equipment-china.html` —— 标题锚定✅1 / 正文可检索🟡5 / 非主推⚠0（共 6；⚠ 仅指未在标题层锚定，不等于搜不到）

| 目标 query | 精确短语 | title | H1 | H2/H3 | desc | 正文 | 判定 |
|---|---|---|---|---|---|---|---|
| pilates equipment manufacturer china | — | 0.75 | 0.75 | 0.5 | 0.5 | 0.75 | 🟡 正文可检索（非主推） |
| pilates equipment oem odm | — | 1.0 | 1.0 | 1.0 | 0.5 | 1.0 | ✅ 主推（标题层锚定） |
| pilates equipment supplier china | — | 0.75 | 0.75 | 0.5 | 0.5 | 0.75 | 🟡 正文可检索（非主推） |
| how to source pilates equipment from china | — | 0.75 | 0.75 | 0.5 | 0.5 | 0.75 | 🟡 正文可检索（非主推） |
| pilates equipment specification sheet | — | 0.5 | 0.5 | 1.0 | 0.75 | 0.75 | 🟡 次级（标题/描述层部分锚定） |
| pilates equipment sample approval | — | 0.5 | 0.5 | 0.75 | 1.0 | 1.0 | 🟡 次级（标题/描述层部分锚定） |

### `pilates-studio-layout-guide.html` —— 标题锚定✅1 / 正文可检索🟡4 / 非主推⚠0（共 5；⚠ 仅指未在标题层锚定，不等于搜不到）

| 目标 query | 精确短语 | title | H1 | H2/H3 | desc | 正文 | 判定 |
|---|---|---|---|---|---|---|---|
| pilates studio layout | ✅ | 1.0 | 1.0 | 0.67 | 0.67 | 0.67 | ✅ 主推（标题层锚定） |
| pilates reformer door clearance | — | 0.25 | 0.25 | 0.75 | 0.75 | 0.75 | 🟡 正文可检索（非主推） |
| how much space for a pilates reformer | — | 0.33 | 0.33 | 1.0 | 0.33 | 0.33 | 🟡 次级（标题/描述层部分锚定） |
| pilates studio floor plan | — | 0.75 | 0.5 | 1.0 | 0.75 | 0.75 | 🟡 次级（标题/描述层部分锚定） |
| pilates equipment delivery access | — | 0.25 | 0.25 | 0.75 | 0.75 | 0.75 | 🟡 正文可检索（非主推） |

### `pilates-equipment-commercial-use.html` —— 标题锚定✅4 / 正文可检索🟡1 / 非主推⚠0（共 5；⚠ 仅指未在标题层锚定，不等于搜不到）

| 目标 query | 精确短语 | title | H1 | H2/H3 | desc | 正文 | 判定 |
|---|---|---|---|---|---|---|---|
| commercial pilates equipment | ✅ | 0.67 | 1.0 | 1.0 | 1.0 | 1.0 | ✅ 主推（标题层锚定） |
| pilates equipment for hotels | — | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | ✅ 主推（标题层锚定） |
| pilates equipment for gyms | ✅ | 1.0 | 1.0 | 0.67 | 1.0 | 1.0 | ✅ 主推（标题层锚定） |
| commercial grade pilates reformer | — | 0.25 | 0.5 | 0.75 | 0.5 | 1.0 | 🟡 正文可检索（非主推） |
| pilates equipment for clubs | — | 1.0 | 1.0 | 0.67 | 1.0 | 0.67 | ✅ 主推（标题层锚定） |

## D. 可发现性（「能不能搜得到」的可验证部分）

| 页面 | sitemap | canonical自指 | hreflang | llms.txt | llms-full | JSON-LD |
|---|---|---|---|---|---|---|
| `pilates-reformer-buyers-guide.html` | ✅ | ✅ | en,x-default | ✅ | ✅ | Article, FAQPage |
| `pilates-apparatus-differences.html` | ✅ | ✅ | en,x-default | ✅ | ✅ | Article, FAQPage |
| `pilates-studio-equipment-list.html` | ✅ | ✅ | en,x-default | ✅ | ✅ | Article, FAQPage |
| `oem-pilates-equipment-china.html` | ✅ | ✅ | en,x-default | ✅ | ✅ | Article, FAQPage |
| `pilates-studio-layout-guide.html` | ✅ | ✅ | en,x-default | ✅ | ✅ | Article, FAQPage |
| `pilates-equipment-commercial-use.html` | ✅ | ✅ | en,x-default | ✅ | ✅ | Article, FAQPage |

**站内入链（爬虫发现路径）**

- `pilates-reformer-buyers-guide.html` ← 2 个页面：blog.html, pilates/index.html
- `pilates-apparatus-differences.html` ← 2 个页面：blog.html, pilates/index.html
- `pilates-studio-equipment-list.html` ← 2 个页面：blog.html, pilates/index.html
- `oem-pilates-equipment-china.html` ← 2 个页面：blog.html, pilates/index.html
- `pilates-studio-layout-guide.html` ← 2 个页面：blog.html, pilates/index.html
- `pilates-equipment-commercial-use.html` ← 2 个页面：blog.html, pilates/index.html

**robots.txt / AI 爬虫**

| 项 | 结果 |
|---|---|
| robots.txt 找到 | ✅ |
| 27 个 AI bot 全放行 | ✅ 无 blocked |
| citation bots 显式放行 | ❌ **缺 `Claude-SearchBot` / `Applebot` / `Googlebot`**（仅靠通配 `*`） |
| llms.txt | ✅ 有 H1 / 9 段 / 53 个 markdown 链接 / +llms-full.txt |
| AI discovery 端点 | 见 `geo_ai_endpoints_20260925.py` 既有结论 22/22 |

## E. 专业度 / E-E-A-T（应用 `seo-content` 技能的 Who-How-Why rubric）

| 页面 | Who:JSON-LD作者 | Who:署名义 | Who:机构名 | How:流程披露语 | Why:CTA | 第一人称 we | 数字个数 |
|---|---|---|---|---|---|---|---|
| `pilates-reformer-buyers-guide.html` | ✅ | ❌ | ✅ | 1 处 | 2 处 | 6 | 148 |
| `pilates-apparatus-differences.html` | ✅ | ❌ | ✅ | 2 处 | 2 处 | 7 | 59 |
| `pilates-studio-equipment-list.html` | ✅ | ❌ | ✅ | 1 处 | 2 处 | 7 | 47 |
| `oem-pilates-equipment-china.html` | ✅ | ❌ | ✅ | 2 处 | 3 处 | 9 | 103 |
| `pilates-studio-layout-guide.html` | ✅ | ❌ | ✅ | 1 处 | 2 处 | 6 | 209 |
| `pilates-equipment-commercial-use.html` | ✅ | ❌ | ✅ | 1 处 | 2 处 | 6 | 54 |

**判读**：

- **Who（谁写的）**：✅ 有 Organization publisher，但**无作者具名**。B2B 器械采购页属「读者会追问」的类型 → 补一个可核验的作者/团队署名（哪怕写「SANFAN production & QC」）比编造人名好。
- **How（怎么做的）**：这是本批页面的**真优势** —— 装箱尺寸、净空、打样检验项全部来自自有产线，属一手信息。但**没有把它讲出来**（引擎 `First-Party Data` 判 0/4，因为它找 `we measured` / `our data` / Methodology 标题）。→ 加一句「这些数字怎么来的」即可，零合规风险。
- **Why（为什么存在）**：✅ 目的是帮采购方决策，不是堆关键词（`No Keyword Stuffing` 6/6 满分佐证）。

**负面信号（高价值）**：新页 0 / 0 / 0 / **−1** / 0 / 0 —— 优于首页（−3）与板块首页（−3）。
- 唯一扣分：`oem-pilates-equipment-china.html` 被判关键词堆砌 —— 词 `model`、密度 3.1%、severity `low`。该页主题就是型号（model）变体，3.2% 属可辩护，可选优化而非缺陷。

## F. 无法验证的部分（必须诚实标注）

| 想验证的事 | 为什么现在验不了 | 什么时候能验 |
|---|---|---|
| Google 是否收录这 6 个 URL | 页面**尚未部署**；GSC 未配置凭据 | 推送 + 部署后，用 GSC URL Inspection |
| 目标关键词是否有排名 | 同上 | 部署后 2–4 周看 GSC 查询报告 |
| AI（ChatGPT/Perplexity/Gemini）是否引用 | 页面不在线上，AI 检索不到 | 部署后测；`geo citations` 需 LLM API key |
| 真实流量/曝光 | 无 GSC / 无分析埋点数据 | 配 GSC 后 |

**可以现在就确定的**：§A–§E 全部是确定性判据（不依赖线上状态）。

## G. 建议动作（按性价比排序）—— 状态已更新

| 状态 | 优先 | 动作 | 影响 | 合规风险 |
|---|---|---|---|---|
| ✅ 已实施 | 🔴 P1 | robots.txt 补 `Claude-SearchBot` / `Applebot` / `Googlebot` 显式 `Allow: /` | `citation_bots_explicit` ❌→✅（站点级 +3） | 无 |
| ✅ 已实施 | 🔴 P1 | 每页加「这些数字是怎么来的」方法论段（自有产线 / QC 量测） | `First-Party Data` 0/4 → **4/4**（6/6 页满分）；真 E-E-A-T | 无（是本厂真实流程） |
| ✅ 已实施 | 🟠 P2 | 句子级一手数字陈述（`We measured 930 mm as the widest…`） | 句子级事实是 AI 抽取的最爱 | 无（数字全部取自画册公布值） |
| ✅ 已实施 | 🟠 P2 | 新增 `Sources` 小节 + 2 个 Wikipedia 权威外链 | `Cite Sources` 1/6 → **6/6** | 低（仅通用术语与出处，不涉产品主张） |
| ✅ 已实施 | 🟡 P3 | 3 条同义词 query 补进正文（`startup` / `door clearance` / `commercial grade`） | 提高精确匹配面 | 无 |
| ✅ 已实施 | 🟡 P3 | 团队署名（可核验的团队名，未编造人名） | E-E-A-T 的 Who 层 | 低 |
| ✅ 已实施 | 🟡 P3 | `Organization` 补 `@id` / `sameAs`，并与 `contact.html` 的站点级实体同 `@id`（后者已含 `address` / `contactPoint` / `knowsAbout`） | 实体消歧、跨页实体合并 | 无 |
| ⚪️ 仍待你定 | — | 引语（Quotation +41%，声称影响最高的一项） | 高影响 | **需要你决定引谁**：引不存在的专家＝编造，不做 |
| ⏸ 未动 | — | 6 语言译文（等 DeepL 额度） | 覆盖 de / ja / ko / fr / it / es | — |

> 本轮只改了 6 个博客页与 `robots.txt`，未触碰任何族页 / 首页 / 语言版。
> ⚠️ 两处外链的**可达性未能在本地实测**（沙箱无外网：`curl` 与 WebFetch 均超时）——选用的是 Wikipedia 的稳定条目，但严格说这一步是「未验证」，部署后应复核一次。

