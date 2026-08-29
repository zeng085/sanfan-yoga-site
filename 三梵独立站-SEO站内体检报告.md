# 三梵独立站 · SEO 站内体检报告

> 工具：marketing-skills / seo-audit 模块 + 自写解析脚本（seo_audit.py，已对全站 13 个页面逐页抓取）
> 站点：fjsanfan.com（Vercel + GitHub 静态站）
> 体检时间：2026-08-28

## 一、总评（健康度评分卡）

| 维度 | 评分 | 说明 |
|---|---|---|
| 抓取与索引（Crawlability/Indexation） | C | robots/sitemap 合格，但**全站缺 canonical**，参数页会稀释权重 |
| 技术基础（Technical） | B | HTTPS/Vercel 快、viewport 正常、移动端 OK；缺 OG 社交标签、缺 hreflang |
| 页面优化（On-Page） | B- | 大部分 title/desc 优质，少数超长被 SERP 截断；博客 H1 双标签 |
| 内容质量（Content） | B+ | FAQ 1081 词 / 博客 6 篇 / 产品页 842 词，深度足够；**product.html 静态仅 107 词（JS 渲染）** |
| 结构化数据（Schema） | B | FAQPage + 博客 Article 已做（利好 GEO）；首页/产品/联系页缺失 |
| **综合** | **B-** | 地基扎实，补 canonical + OG + 产品页静态化后可到 A- |

**顶部 5 个优先问题**
1. 全站无 canonical（高）
2. product.html 为 JS 渲染模板，静态内容几乎为空（高）
3. 缺 Open Graph / 社交分享标签（中高）
4. 首页/产品/联系页缺结构化数据（中）
5. 部分 title/desc 超长被 SERP 截断（中）

---

## 二、逐页 SEO 信号（实测）

| 页面 | Title长度 | Desc长度 | H1数 | 图片(缺alt) | 内链 | 结构化数据 | 词数(英/中) |
|---|---|---|---|---|---|---|---|
| index.html | 59 | 205 ⚠ | 1 | 35(0) | 24 | — | 637/2 |
| about.html | 47 | 149 | 1 | 5(0) | 17 | — | 413/2 |
| products.html | 60 | 242 ⚠ | 1 | 30(0) | 44 | — | 842/2 |
| product.html | 16 ⚠ | 75 ⚠ | 1 | 3(1⚠) | 17 | — | **107/2** ⚠ |
| contact.html | 54 | 138 | 1 | 2(0) | 16 | — | 151/2 |
| faq.html | 77 ⚠ | 206 ⚠ | 1 | 2(0) | 18 | FAQPage ✓ | 1081/2 |
| blog.html | 55 | 181 | **2** ⚠ | 8(0) | 23 | — | 257/264 |
| blog/tpe-vs-pu.html | 60 | 146 | **2** ⚠ | 4(0) | 19 | Article ✓ | — |
| blog/moq-explained.html | 51 | 143 | **2** ⚠ | 4(0) | 19 | Article ✓ | 313/329 |
| blog/compliance.html | 64 | 153 | **2** ⚠ | 4(0) | 19 | Article ✓ | 345/302 |
| blog/vet-factory.html | 66 ⚠ | 171 | **2** ⚠ | 4(0) | 19 | Article ✓ | 308/304 |
| blog/7day-sampling.html | 71 ⚠ | 160 | **2** ⚠ | 4(0) | 19 | Article ✓ | 297/302 |
| blog/custom-sizes.html | 73 ⚠ | 162 | **2** ⚠ | 4(0) | 19 | Article ✓ | — |

⚠ = 偏离最佳实践，详见第三节。

---

## 三、问题明细（Issue → Impact → Fix → 优先级）

### 🔴 高优先级

**1. 全站缺失 canonical 标签**
- 影响：高。Google 可能把 `product.html?id=ym1…ym8/pr1…` 等参数 URL 当作独立页面，权重分散、出现重复内容；未来加 UTM 外链也会制造副本。
- 证据：13 个页面 `canonical: None`（脚本实测）。
- 修复：每页 `<head>` 注入 self-referencing canonical（绝对 URL）。可按 Vercel 部署域 `https://fjsanfan.com/<page>` 统一；product.html 需按 `id` 动态生成。
- 优先级：P1

**2. product.html 是 JS 渲染模板，静态内容几乎为空**
- 影响：高。静态 HTML 仅 107 英文词、title 统一为 "Product — SANFAN"、无静态正文；所有内容靠 `?id=` 参数 + JS 注入。Googlebot 虽能渲染 JS，但慢且易漏，海外买家搜具体产品名（如 "TPE yoga mat manufacturer"）时该页竞争力弱。
- 证据：products.html 用 `product.html?id=ym1…` 链接了 17 个产品卡；product.html 正文词数 en107/zh2。
- 修复（二选一，推荐 A）：
  - A. 为每个核心产品生成**静态详情页**（如 `products/tpe-yoga-mat.html`），带独立 title/desc/H1/文案/Product 结构化数据 → 最利 SEO；
  - B. 保留模板，但预渲染（SSG/SSR）首屏内容 + 按 `id` 动态写入 `<title>`/`<meta description>`/`<canonical>`/`<link rel=canonical>`。
- 优先级：P1

### 🟠 中高优先级

**3. 全站缺失 Open Graph / Twitter Card 社交标签**
- 影响：中高。此前投的 LinkedIn / PR / TikTok 外链，分享时只会显示裸 URL，无标题图与描述，点击率打折。
- 证据：13 页 `OG tags: False`（脚本实测）。
- 修复：每个页面加 `og:title / og:description / og:image / og:type / og:url` + `twitter:card=summary_large_image`。可复用 meta description 文案，图片用各页首图。
- 优先级：P2

### 🟡 中优先级

**4. 首页 / 产品 / 联系 / 博客列表页缺结构化数据**
- 影响：中。FAQ 与博客已做（很好，利好 GEO），但首页应加 `Organization` + `WebSite`（含 Sitelinks Search），products 加 `ItemList`/`Product`，contact 加 `LocalBusiness`（地址/电话/邮箱）。
- 修复：补 JSON-LD 三块。
- 优先级：P2

**5. 部分 Title 超长被 SERP 截断**
- 影响：中。faq(77)、vet-factory(66)、7day-sampling(71)、custom-sizes(73) 超出 ~60 字符，移动端会截断，首屏关键词前移优势丢失。
- 修复：压到 50–60 字符，品牌词 " | SANFAN" 保留在末尾。
- 优先级：P2（快赢）

**6. 部分 Meta Description 超长**
- 影响：中。index(205)、products(242)、faq(206) 超出 155–160 建议，SERP 截断。
- 修复：压到 150–160 字符，保留核心卖点 + CTA。
- 优先级：P2（快赢）

### 🟢 低优先级

**7. 博客页与 6 篇博客出现双 H1**
- 影响：低。因中英双语块（show-zh/show-en）各含一个 H1，DOM 中存在 2 个 H1。Google 通常能容忍（同页双语），但非最优。
- 修复：让每个语言块各自包裹，确保「同屏仅 1 个可见 H1」，或把副语言 H1 降为 H2 区块标题。当前可接受，列为可选优化。
- 优先级：P3

**8. 缺 hreflang 标注**
- 影响：低。中英双语但未声明语言/地区关系，国际搜索可能错配语言版本。
- 修复：在 `<head>` 加 `hreflang="en"` / `hreflang="zh"` / `hreflang="x-default"` 互链。
- 优先级：P3

**9. product.html 1 张图缺 alt**
- 影响：低。JS 模板内图片无 alt。
- 修复：按产品动态写入 alt。
- 优先级：P3

---

## 四、已做对的（保持）

- ✅ 图片 alt 覆盖 99%（仅 product.html 模板 1 张缺失）
- ✅ FAQPage + 6 篇博客 Article 结构化数据已就位（GEO 关键资产）
- ✅ robots.txt 引用 sitemap + llms.txt；sitemap 覆盖全部 13 页 + rss.xml
- ✅ 内链健康（每页 16–44 条内部链接，无孤立页）
- ✅ 核心内容页词数充足（FAQ 1081 / products 842 / about 413）
- ✅ 关键词前置的 title 策略良好（index/products/contact 均含 OEM/ODM + 产品词）
- ✅ Vercel HTTPS + viewport + 移动端响应正常

---

## 五、优先级行动清单

| 顺序 | 动作 | 优先级 | 预计工作量 |
|---|---|---|---|
| 1 | 全站加 self-referencing canonical（模板注入，product.html 按 id 动态） | P1 | 低 |
| 2 | product.html 静态化 / 预渲染 + 动态 title/desc | P1 | 高 |
| 3 | 全站加 OG + Twitter Card 社交标签 | P2 | 中 |
| 4 | 首页/产品/联系页补 Organization/ItemList/LocalBusiness JSON-LD | P2 | 中 |
| 5 | 修剪超长 title（4 篇博客 + faq）与 desc（index/products/faq） | P2 | 低（快赢） |
| 6 | 加 hreflang 中英互链 | P3 | 低 |
| 7 | product.html 模板图补 alt；博客双 H1 收口 | P3 | 低 |

---

## 六、下一步建议

- 本体检为**站内**维度。要查「能否被搜到 / 排名」，需用 **seo-ops** 的 GSC 模块跑关键词体检（需你提供 Google Search Console OAuth 凭据）。
- 若确认，我可**直接动手**把第 1、3、5 项（canonical + OG + 描述修剪）一次性改完并提交，属低风险快赢；第 2 项（产品页静态化）工作量较大，建议单独确认方案后再做。
