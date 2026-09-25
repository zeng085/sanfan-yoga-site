# fjsanfan.com AI 引用基线（首测 2026-09-25）

> 站内 GEO 已 78/100（技术层 22/22、三项站点审计全 0）。再修站内上不去 —— 瓶颈在**站外**。
> 本文件给出第一份可复测的站外数字。

## 一、结论（三句话）

1. **新站 `fjsanfan.com`：9 组检索查询（60 个席位）+ 4 次 AI 提问，出现 **0** 次。**
2. 品牌实体本身**已被 AI 认识**：老站 `sanfanyoga.com` 拿到 3 个检索席位，并在 AI 答案里被**实名引用为来源**（favicon 铁证）。
3. 所以问题不是「AI 不知道三梵」，而是**「AI 把三梵归因到老站和平台，而不是新站」**。站内已经把该做的做完了，接下来要解决的是**外部信号的指向**。

## 二、路 A：检索层引用槽位（谁占着 AI 的来源池）

样本：9 组查询、60 个结果席位。

### 引擎：ddg（30 个席位）

| 域 | 席位 | 占比 | 类型 |
|---|---:|---:|---|
| `pureasanayoga.com` | 5 | 16% | competitor-site |
| `alibaba.com` | 4 | 13% | marketplace |
| `yewayoga.com` | 3 | 10% | competitor-site |
| `made-in-china.com` | 3 | 10% | marketplace |
| `htsyoga.com` | 3 | 10% | competitor-site |
| `theyogamats.com` | 2 | 6% | competitor-site |
| `yanrefitness.com` | 1 | 3% | competitor-site |
| `chinahappyfitness.com` | 1 | 3% | competitor-site |
| `mingyogamat.com` | 1 | 3% | competitor-site |
| `torquepilates.com` | 1 | 3% | competitor-site |
| `fdmyoga.com` | 1 | 3% | competitor-site |
| `aurayogamat.com` | 1 | 3% | competitor-site |
| `wavar.com` | 1 | 3% | competitor-site |
| `thelunayoga.com` | 1 | 3% | competitor-site |

### 引擎：hosted（30 个席位）

| 域 | 席位 | 占比 | 类型 |
|---|---:|---:|---|
| `yogamatmanufacturers.com` | 3 | 10% | competitor-site |
| `made-in-china.com` | 3 | 10% | marketplace |
| `sanfanyoga.com` | 3 | 10% | owned |
| `baidu.com` | 3 | 10% | marketplace |
| `fdmsport.com` | 2 | 6% | competitor-site |
| `ecocorker.com` | 2 | 6% | competitor-site |
| `accio.com` | 2 | 6% | ai-aggregator |
| `b2b168.org` | 2 | 6% | marketplace |
| `yoga-supplies.com` | 1 | 3% | competitor-site |
| `yogamatcustom.com` | 1 | 3% | competitor-site |
| `pureasanayoga.com` | 1 | 3% | competitor-site |
| `wellfitsource.com` | 1 | 3% | competitor-site |
| `htsyoga.com` | 1 | 3% | competitor-site |
| `bsmyogamats.com` | 1 | 3% | competitor-site |

### 席位按来源类型

| 类型 | 席位 | 占比 |
|---|---:|---:|
| 竞品制造商官网 | 39 | 65% |
| B2B 平台（阿里/中国制造网/百度B2B） | 15 | 25% |
| **我方站点** | 3 | 5% |
| AI 供应商聚合/目录 | 3 | 5% |

**读法**：竞品**自有官网**占了 65%（39 席），平台占 25%（15 席），我方仅 3 席。这说明两件事：① 平台是 AI 取供应商的高频来源，不能丢；② 但**席位大头给了竞品官网** —— 也就是说「自有站进引用池」这条路是通的，竞品正在走，只是新站还没拿到入场资格。

### 我方席位明细

| 域 | 席位 | 命中的查询数 |
|---|---:|---:|
| `sanfanyoga.com` | 3 | 2 |
| `fjsanfan.com` | **0** | **0** |

## 三、路 B：AI 答案层（真 AI 引擎答不答你）

样本：秘塔 AI 搜索**成功采样 4 次**（另有 3 次被限流作废，不计入分母 —— 失败 ≠ 无提及）。

| 指标 | 命中 | 命中率 |
|---|---:|---:|
| 答案正文提到品牌 SANFAN | 2 | 50% |
| 来源列表含新站 fjsanfan.com | **0** | 0% |
| 来源列表含老站 sanfanyoga.com | 1 | 25% |

逐次采样：

- run A｜`OEM yoga mat manufacturer in China private label`
  - 结论：提到品牌（归因：阿里巴巴（说成「在阿里巴巴上提供 TPE 瑜伽垫定制，MOQ 10 件起」））
  - 来源域：（该次未采集来源域）
  - 备注：答案正文点名 Xiamen Sanfan，但叙事完全来自平台页
- run B｜`OEM yoga mat manufacturer in China private label`
  - 结论：无我方信号
  - 来源域：`alibaba.com`、`china.cn`、`goldsupplier.com`、`made-in-china.com`、`shengde.net.cn`
  - 备注：同一问题两次采样，来源池已不同 → AI 答案非确定性，需多次采样
- run B｜`best yoga mat manufacturers in China`
  - 结论：无我方信号
  - 来源域：`china.cn`、`goldsupplier.com`、`jd.com`、`mouldsnet.com`、`smzdm.com`、`taobao.com`
  - 备注：答案列举厦门瑞盛/安徽Camper/苏州ProCircle 等，来源多为中文站
- run A｜`cork yoga mat manufacturer OEM factory`
  - 结论：提到品牌（归因：自有站（来源即 sanfanyoga.com））、**引老站**
  - 来源域：`sanfanyoga.com`、`made-in-china.com`
  - 备注：★ 铁证：来源 favicon 请求 cdn.metaso.cn/favicon/sanfanyoga.com.ico；答案正文写「厦门桑凡体育用品有限公司（Xiamen Sanfan）」

### 被引用的来源域排行

| 来源域 | 出现次数 |
|---|---:|
| `china.cn` | 2 |
| `goldsupplier.com` | 2 |
| `made-in-china.com` | 2 |
| `alibaba.com` | 1 |
| `shengde.net.cn` | 1 |
| `jd.com` | 1 |
| `mouldsnet.com` | 1 |
| `smzdm.com` | 1 |
| `taobao.com` | 1 |
| `sanfanyoga.com` | 1 |

**关键个案**：`cork yoga mat manufacturer OEM factory` 一条，秘塔把 `www.sanfanyoga.com` 列为来源，答案正文写「厦门桑凡体育用品有限公司（Xiamen Sanfan）」——证明**品牌的 AI 可引用性已经存在**，只是全部落在老站。

另一条同样值得记：`OEM yoga mat manufacturer in China private label` 里，AI 把 SANFAN 描述成「在阿里巴巴上提供 TPE 瑜伽垫定制，MOQ 10 件起」——**品牌信息被平台页重塑**，买家看到的是平台叙事，不是工厂自己的口径。

还暴露一个工具事实：**AI 答案是非确定性的**——同一个问题在两次采样里，一次把 SANFAN 说成「阿里巴巴上的供应商」，另一次答案里根本没有 SANFAN。所以单次采样不能当结论，复测必须多次采样取比率。

### 口径自审

```
  ✓ 全部声明与来源域一致（引用的域名都出现在 favicon 采集结果里）
```

## 四、本次采样的限制（影响解读，须一并看）

- Perplexity / ChatGPT / Gemini / Google AI Overviews **本机不可达**（DNS 被污染：chatgpt.com→31.13.94.36、google.com→31.13.92.37，均为 Facebook IP；TCP 也不通），本轮无直采数据。**这是本基线最大的盲区**——目标客群用的正是这几家。
- 路 A 的 `ddg` 与 `hosted` 是**两个引擎**，域频次不可直接相加，需分列。
- 路 B 用秘塔（中文 AI 引擎），答案语言与来源池偏向中文站/平台页，与海外买家的 ChatGPT/Perplexity 不完全同分布 —— 只作**趋势基线**，不能当绝对值。
- 路 B 的 AI 答案**非确定性**：同一问题两次采样来源池不同。单次采样不足以定性，复测须多次采样。
- 秘塔连续提问约 6 次后开始限流（返回 130 字符空壳）。**限流样本必须剔除，不能当「无提及」计入**，否则基线被系统性压低。
- DDG 有速率限制，连续请求会返回 BLOCKED；复测需间隔 ≥60s。
- 秘塔来源域名**只能从 favicon 请求采集**（`cdn.metaso.cn/favicon/<域名>.ico`）：来源卡片 innerText 只有标题、锚点无 href。靠标题里的公司名推断域名 = 不严谨。
- `geo citations` 需 API key（推荐 `PERPLEXITY_API_KEY`，另有 serpbase 可选 Google SERP + AI Overview），本机无该凭证。

## 五、下一轮该盯什么

| 指标 | 当前基线 | 复测目标 |
|---|---|---|
| fjsanfan.com 检索席位 | **0** / 60 | ≥1（进任一榜即算突破） |
| fjsanfan.com AI 引用 | **0** / 4 | ≥1 |
| 品牌 AI 提及率 | 2/4，且归因老站/平台 | 提及率升 + **归因转向新站** |
| 第三方目录收录 | 2（finalscout、accio），均指向老站 | 累加，且**至少 1 条指向新站** |

**优先动作（按性价比排序）**

1. **把老站的引用权重导到新站** —— 老站已被 AI 实名引用，这是现成资产。在 sanfanyoga.com 上给出指向 fjsanfan.com 的明确实体关联（同组织 → 新站为官方站点），比从零建信号快得多。
2. **补齐第三方目录实体**（finalscout/accio 已收录品牌，但指向老站）：统一 NAP + 站点字段，把新站作为主站写入。
3. **内容是给「被引用」用的，不是给「排名」用的**：竞品官网占 65% 席位靠的是成篇的规格/认证/FAQ 可引用文本，新站的 1331 页结构已达标，接下来拼的是**外部指向新站的链接与提及**。

> 复测方式见脚本头部注释。数字口径固定后即可逐月对照。
