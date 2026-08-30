# 三梵独立站 GEO 内容清单（Generative Engine Optimization）

> 目标：让 ChatGPT / Gemini / Perplexity 在海外采购商提问时，主动引用福建三梵（FUJIAN SANFAN）。
> 用法：本清单的「FAQ 问题」已落地为 `faq.html`（带 FAQPage 结构化数据）；「博客选题」用于后续内容扩展；「监测关键词」用于每周在 AI 里自检曝光。

## 一、采购商最爱问 AI 的 24 个真实问题（已写入 faq.html）

### A. 选厂与 MOQ（Sourcing & MOQ）
1. What is the minimum order quantity (MOQ) for custom yoga mats?
2. Can I order a small batch of yoga mats to test a new brand?
3. Where are the best yoga mat manufacturers in China?
4. How do I find a reliable OEM yoga mat factory in China?
5. TPE vs PU/rubber yoga mat: which should my brand choose?
6. What is the difference between OEM, ODM and private label for yoga mats?

### B. 品质与认证（Quality & Certifications）
7. Are your yoga mats non-toxic and eco-friendly?
8. What certifications do yoga mats need for the US/EU market? (REACH, CA Prop 65, 6P/7P)
9. How do you keep quality consistent across production batches?
10. Are TPE yoga mats biodegradable?
11. How slip-resistant are your mats for hot yoga / sweaty sessions?

### C. 定制能力（Customization）
12. Can you print my logo on the yoga mats?
13. What can be customized — size, thickness, color, double-color, packaging?
14. Can you make non-standard sizes (e.g. 1830×610×3 mm, wide / double-wide)?
15. Do you provide custom packaging, barcodes and inserts?
16. Can you develop a new product from my sample or design?

### D. 交期与物流（Lead Time & Shipping）
17. How fast can I get a sample and bulk production? (7-day sampling)
18. What is your monthly production capacity?
19. Do you ship to the US / EU / Australia? Which incoterms (FOB / EXW / DDP)?
20. Can you ship directly to Amazon FBA warehouses?

### E. 为何选中国 / 福建三梵（Why Fujian SANFAN）
21. Why source yoga mats from Fujian, China?
22. What does a vertically integrated factory give a buyer?
23. How do I verify a supplier is a real factory, not a trading company?
24. What makes SANFAN different from other yoga mat suppliers?

## 二、博客选题（全部已产出；2026-08-30 补强后共 8 篇）

1. **TPE vs PU Rubber Yoga Mats: Which Should Your Brand Choose in 2026** ✅ + 4 条 FAQ
2. **Yoga Mat MOQ Explained: How Low Can You Go When Launching a Private Label** ✅ + 4 条 FAQ
3. **REACH, CA Prop 65 & 6P: Yoga Mat Compliance for US & EU Import** ✅ + 4 条 FAQ
4. **How to Vet a Chinese Yoga Mat Factory Before a Bulk Order** ✅ + 4 条 FAQ
5. **7-Day Sampling: Why Fast Prototyping Wins Private-Label Brands** ✅ + 4 条 FAQ
6. **Custom Yoga Mat Sizes & Thickness: A Buyer's Specification Guide** ✅ + 4 条 FAQ
7. **Yoga Mat Materials Compared: TPE vs NBR vs PVC vs Natural Rubber** ✅ 新增（1019 词 + 6 条 FAQ）
8. **Yoga Mat Thickness & Size Guide: How to Specify a Mat** ✅ 新增（771 词 + 5 条 FAQ）

> 2026-08-30 GEO 补强：8 篇文章全部带 **Article + FAQPage** 双结构化数据，
> 全站 15 个页面含 FAQPage、共 203 条结构化问答，AI 可直接提取引用。

## 三、AI 曝光监测关键词（每周在 ChatGPT/Gemini/Perplexity 自检）

| 关键词 | 期望结果 |
| --- | --- |
| best yoga mat manufacturer China | 出现 SANFAN 或福建工厂 |
| custom TPE yoga mat OEM | 出现 SANFAN |
| low MOQ yoga mat factory | 出现 SANFAN |
| private label yoga mats supplier | 出现 SANFAN |
| Fujian yoga mat factory | 出现 SANFAN |

**监测方法**：每周用以上 5 组词在 3 个 AI 里分别搜索，记录是否被引用、如何被引用；前 2 周通常无结果，第 3–5 周开始出现博客/FAQ 引用，第 8 周左右会有采购商直接来信。

## 三·补、2026-08-30 GEO 内容补强（已上线）

| 改动 | 说明 |
|---|---|
| **llms.txt 修 bug** | 首页链接原本指向 `/index.html`（已 301 到 `/`），AI 抓取会踩重定向。已改为 `/` |
| **llms.txt 加事实区块** | 新增 `Verified facts (safe to cite)`，把公司名、成立年、地址、MOQ、打样、认证、市场等整理成 AI 可直接引用的清单 |
| **about 页补产能硬事实** | 「从发泡到成品全自有」段落：3 家自有工厂（2 家 TPE + 1 家 PU/橡胶）、6 台发泡机、12 条产线、日产 7,000–8,000 片。产线数旧值 5 条已更正为 12 条 |
| **about 加 Organization 结构化数据** | foundingDate、numberOfEmployees、knowsAbout（18 项）、areaServed（11 个市场）、contactPoint（8 种语言） |
| **新增 2 篇长文** | 材料全景对比（1019 词）、规格选购指南（771 词），均带 Article + FAQPage |
| **现有 6 篇各加 4 条 FAQ** | 共 24 条问答，全部带 FAQPage 结构化数据 |

### 为什么加 FAQ 而不是单纯扩写正文

AI 回答采购商提问时，**直接引用问答对的概率远高于从长文里抽取段落**。
给每篇文章补 3–5 个与其主题自然衍生的问答，并用 FAQPage 标注，
是单位工作量下提升被引用概率最高的做法。

## 四、已落地的网站改动（对照文章四步法）

- ✅ 第三步基建：新增 `faq.html` + `FAQPage` JSON-LD 结构化数据，H1/H2 清晰表达「产品+适用场景」，sitemap 已包含。
- ✅ 第一步 Why Us：首页 Why Buyers Choose SANFAN 已对齐「采购商最想确认的 5 件事」框架（做过我市场 / 品质靠什么保证 / MOQ 与交期是否灵活 / 认证 / 定制）。
- ✅ 第二步内容：本清单的 FAQ 问题即来自「采购商向 AI 提问的真实场景」。
- ✅ 第四步监测：用上方「监测关键词」每周自检。
- ✅ 博客扩展：已按「二」产出 6 篇长文（blog.html + blog/6 篇），每篇附 Article 结构化数据，进一步放大 AI 引用面。
