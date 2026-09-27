# 普拉提器械板块方案 v3 —— 改为「以画册为主」的方向

- 日期：2026-09-26
- 方向来源：user 提出「以画册为主，先不管报价表；画册产品＝器械厂产品，归为一类；
  瑜伽垫板块里有冲突的归过来」→ 本节回答「是否可行」并给出落地结构
- 关系：**取代 v2 的 §5.3（三选一）与 §6-Q1（主键阻塞）**；v2 的合规红线（§3）、配图实测（§4）、
  数据源盘点（§1）继续有效
- 状态：**只出方案，站点文件 0 改动**

---

## 一、结论：可行，且是三条路里最干净的一条

| 理由 | 说明 |
|---|---|
| ① 画册本来就是**出口物料** | 型号名（`AL 19-F` / `Fold 9-CA`）、材质、包装 A/B、毛重全都有，可直接上站 |
| ② 一次绕开 v2 的两个坑 | 「两份资料无共同主键」不再需要（只用一份）；报价表的第三方商标/内部价/国内话术**天然不进站** |
| ③ 结构天然 1:1 | 画册 **8 个系列** ↔ 站内 **8 个族页**，且每页都有内容（详见 §3） |
| ④ 与既有 SEO 结构兼容 | 8 个族页 URL 全部保留，不丢已积累的内链与收录 |

**「归为一类」这个说法要落成具体形态**：画册内容 = **Pilates 大器械**（不含垫类、不含力量/有氧），
所以「一类」＝现有的 `/pilates/` 一级入口板块本身。**不需要新建大类**，是把现有板块的**内容源换掉**。

---

## 二、⚠️ 先纠正一个预期：瑜伽垫板块里**没有器械产品可以搬过来**

对瑜伽垫侧 **182 个 EN 页面**（根目录 + `products/` + `applications/` + `blog/`，已排除 `/pilates/` 与语言版）
做了全量器械关键词扫描：

| 关键词 | 命中页面 | 实际情况 |
|---|---|---|
| reformer / cadillac / wunda / barrel / tower / spine corrector | **182 / 182** | ⚠️ 全部只出现在**全站导航下拉**（`data-i18n="nav.pl.*"` → `/pilates/*.html`） |
| gyrotonic | **0** | 站内从未提及 |
| wall-mounted / stall bar / wall tower | **0** | 站内从未提及 |

**上下文抽样**（`products/pilates-reformer-mat-mandala.html`）：
```
… Pilates Reformer  Pilates Cadillac  <a href="/pilates/pilates-wunda-chair.html" …
… Pilates Spine Corrector  Reformer Tower & 3-in-1  <a href="/pilates/pilates-studio-set.html" …
```
→ 这些是**导航菜单项**，不是正文产品展示。

**所以：产品层没有任何东西需要「搬过来」。** 瑜伽垫侧的 147 个
`products/pilates-reformer-mat-*.html` 是**普拉提垫**（垫类产品），按两厂分工**本就属于瑜伽垫板块，
不能搬**。真正需要处理的是**叙事层的四处冲突**（见下）。

---

## 三、真正要处理的四处冲突（全部有原文证据）

### 冲突 1 ⛔ 同厂叙事（最实质的一处）
`pilates/index.html` 现文：
> "…41 models across 8 lines, in imported rubberwood, FAS-grade white maple, piano lacquer,
> Croatian beech, aluminium and 316 steel. **Same factory as our yoga mat line, different bench.**
> …与瑜伽垫同厂，但走另一条产线。"

→ 与「**两厂分工**」（福建三梵垫厂 / 山东 Comerocky 器械厂）**直接矛盾**。
**处理**：改为「自有器械厂」叙事，并把画册的工厂事实写进来
（41,000㎡ / 300+ 员工 / 10+ 工程师 / 50+ 专利 / 已产 30 万台核心床 / 钣金+木工全产线）。
⚠️ 画册 p3 英文是机翻残文（`We uses…` / `andsustainable` / `equipmentrigorously`）→ **只取事实，重写句子**。

### 冲突 2 `h1` 锁死了材质
`pilates/index.html` 现 h1：**"Wooden Pilates apparatus, built to order / 实木普拉提大器械 · 按单定制"**
→ 画册 **铝合金 22 台 + 碳钢 1 + 金属 4 = 27 台非木质**（占 39%）。**"Wooden" 必须去掉。**

### 冲突 3 统计数字全部来自旧源
`.pl-stats` 现文：`8 Equipment lines / **41 Models** / **12 Timber-frame options** / 7 days sampling`
→ 换源后：型号 **41 → 69**；材质种类旧说 12 种，**画册实际 5 种**
（Aluminum 22 · Maple 20 · OAK 6 · Metal 3 · Carbon steel 1；另 15 台未标材质）
→ 三个数字都要重算，`7 days` 打样需向器械厂确认（旧数字来自垫类口径，**不是画册里的**）。

### 冲突 4 型号清单与木种体系整体不同
| | 旧（站内） | 画册 |
|---|---|---|
| 台数 | 41 | 69 |
| 编号 | NIC / NLH / NIM / NIX / NIK / NIW / NIS | AL / Wood / Fold / Chair / Ladder / Metal |
| 材质 | 橡胶木 · FAS 白枫木 · 钢琴烤漆 · 克罗地亚榉木 · 铝合金 · 316 钢 | Maple · OAK · Aluminum · Metal · Carbon steel |
| 重叠 | **0** | |

→ 按新方向：**以画册为准整体替换**（见 §5-Q2 的代价提示）。

> 另一处**非冲突但要对齐**：`about.html` 自述 "A yoga & fitness equipment source factory"。
> 两厂分工下这句话不算错（三梵确实是设备源厂），但可在器械板块里明确「器械由自有器械厂生产」以呼应。

---

## 四、新结构：画册 8 系列 → 8 个族页（1:1，每页非空）

| # | 画册系列 | 台数 | 对应站内页面 | 处置 |
|---|---|---|---|---|
| 1 | Wood | 11 | `pilates-reformer.html` | 表数据替换 |
| 2 | **AL / Metal** | **21** | `pilates-aluminium-reformer.html` | **新增族页** |
| 3 | **Fold** | **8** | `pilates-foldable-reformer.html` | **新增族页** |
| 4 | Tower / 3-in-1 | 7 | `pilates-reformer-tower.html` | 表数据替换 |
| 5 | Cadillac | 4 | `pilates-cadillac.html` | 表数据替换 |
| 6 | Chair | 8 | `pilates-wunda-chair.html` | 表数据替换 |
| 7 | Ladder | 7 | `pilates-ladder-barrel.html` | 表数据替换 |
| 8 | Specialty（Gyrotonic · Two-Way Ladder Reformer · Wall-mounted） | 3 | `pilates-specialty.html` | 表数据替换 |
| — | **合计** | **69** | 10 页（1 板块首页 + 8 族页 + 新页） | — |

**画册覆盖不到的两页（必须单独处置，见 §5-Q3）**

| 页面 | 画册型号数 | 备注 |
|---|---|---|
| `pilates-spine-corrector.html` 矫正器 | **0** | 但报价表证明器械厂**确实做矫正器**（五件套里「矫正器 280 元」「泡沫矫正器 129」）→ **建议保留页面**，标注 available on request |
| `pilates-studio-set.html` 五件套 | **0** | 同理，报价表有 4 行五件套（橡木 / 白枫木 / 实木烤漆白色 / 胡桃木）→ **建议保留页面** |

> 这两页恰好是「画册 + 报价表」互补的地方：**画册决定主表，报价表证明这两类在做**。
> 若要给它们型号，只需向器械厂索要这两族的出口编号即可。

**规格表列**：6 列 → **8 列**，新增 `Packing size A/B`、`Gross weight`（画册 69 台全带）。

---

## 五、三个必须一起定的问题

**Q1 ⛔ 配图——换思路并不能解决（唯一硬阻塞）**
画册是整页合成位图，**提不出独立产品图**（`get_image_rects()` 全整页、`drawings=0`）；
报价表内嵌 141 张实测**无一可用**（车间实拍 / 中文海报 / ZHAIKER 水印）。
→ 69 台要配图，**只能向器械厂要出口图包**（每型号 ≥3 张、白底棚拍、无水印、长边 ≥2000px、可商用）。
→ 过渡期可先只上表与文案、图片位留空（但不建议长期留空，器械页没有图转化率会很难看）。

**Q2 旧 41 台是否真的全撤？**（有代价，需你点头）
- 好处：口径统一、木种体系不再打架
- 代价：① 8 个族页 × 7 语言的型号表**整表重写**；② 旧型号词（rubberwood reformer /
  piano lacquer reformer 等）已积累的排名会回落，新词（Oak / Maple / Aluminium）需重新养
- 备选：**保留一小段「实木定制线（橡胶木 / 钢琴烤漆 / 榉木）」作为 OEM 定制选项**，
  不作为主表 → 既不丢老询盘，也不与画册口径冲突。**我倾向这个折中。**

**Q3 两个落空页怎么办？**
(a) 保留页面 + 标 `available on request`（**推荐**）｜(b) 并入 `pilates-specialty`（301）
｜(c) 向器械厂索要这两族的出口编号，补进画册口径

---

## 六、建议执行顺序

1. 你确认 Q2（旧 41 台去留）→ 这是唯一要你拍板的
2. 同时向器械厂索要：**出口图包**（Q1）+ 矫正器/五件套两族的出口编号（Q3）+ 打样周期与 MOQ 口径
3. 我按画册产出**结构化型号主表**（69 台 × 8 系列，含包装 A/B 与毛重）交你逐条确认
4. 确认后按既有纪律推进：**先单页样本 → 独立验收 → 铺开 → bump 资源版本号 → 后台推送**
   （推送前走「远程树 vs 本地树逐 blob 比对」，**推送需你明确许可**）

---

## 附：v3 对 v2 的取代关系

| v2 章节 | 状态 |
|---|---|
| §1 两份资料盘点 | ✅ 继续有效（作为事实记录） |
| §2 三方对账 | ✅ 继续有效（解释了为何不能合并） |
| §3 合规红线 | ✅ 继续有效（报价表相关；本方向下**不再进站**，红线自然规避） |
| §4 配图实测 | ✅ 继续有效，且升为**唯一硬阻塞** |
| §5.3 三选一 | ❌ **作废**，由本文件 §4 取代 |
| §6-Q1（主键阻塞） | ❌ **解除**（单源不需要主键对齐） |
