# sanfansport.com 对标摸底 & 产品信息版块改动方案

日期：2026-09-11 ｜ 对标站：https://www.sanfansport.com/
本方案只做规划，**未改动任何站点文件**。

---

## 一、先给结论（三句话）

1. **结构可以照它**：4 大板块（YOGA / FITNESS / PILATES / RECOVER）→ 50 子类 → 167 个产品页，分类逻辑清晰，比我们现在 5 个锚点分组更专业，**建议整体改用它的类目树**。
2. **字段可以照它**：它的规格表是 `Material / Size / Thickness / Weight / Color / Feature / Logo / Packing` 8 字段，比我们的 7 字段更能承接询盘；**但必须保留 MOQ 和认证两块**（它没有，而我们靠这两项赢单）。
3. **数值不能全照它**：它 **36% 的产品页（60/167）规格表是空的**，60 个页面是数字后缀的占位 slug，18 组重名（"PU Rubber Yoga Mat" 重复 13 次），单位 cm/mm 混用。直接抄数值会把它的错误一起搬进我们站。**建议：结构 + 字段照它，数值以它为准的只有 41 条，其余 12 项冲突必须回厂确认。**

---

## 二、目标站摸底

### 2.1 规模

| 项目 | 目标站 sanfansport.com | 我们 fjsanfan.com | 差距 |
|---|---|---|---|
| 产品页 | 167 | 27（×7 语言 = 189 文件） | 少 140 个 |
| 子分类 | 50 | 5 个锚点分组 | 少 45 |
| 顶级板块 | 4（YOGA/FITNESS/PILATES/RECOVER） | 无独立板块 | 缺 PILATES 板块 |
| 规格表字段 | 8 个 | 7 个 | 缺 Weight / Feature / Logo |
| 有规格数据的产品 | 107（64%） | 27（100%） | 我们的覆盖率反而更高 |
| 技术栈 | WordPress + WooCommerce（Yoast SEO） | 静态 HTML | — |
| 报价方式 | "Request for quote" 表单页 | 价格直接写进 JSON-LD | — |

### 2.2 类目树（4 板块）

| 板块 | 子类数 | 产品数 | 代表产品 |
|---|---|---|---|
| **YOGA** | Yoga Mat（8 子类：TPE/PU/Suede/Cork/Folding/Meditation/Economical/EVA平衡垫）、Yoga Accessories（12）、Resistance Bands（5）、Yoga Hammock、Yoga Wear | ~93 | TPE Yoga Mat、Matte PU Rubber Yoga Mat、Cork Rubber Yoga Mat |
| **FITNESS** | Fitness Accessories（21）、Free Weights（5）、Fitness Equipment（5）、Silicone Series（6） | ~37 | Jump Rope ×8、Silicone Dumbbell、Barbell |
| **PILATES** | Pilates Equipment（Reformer / Cadillac / Chair / Ladder Barrel / Spine Corrector）、Pilates Reformer Mat | 11 | Maple Core Bed、Oak Cadillac Bed |
| **RECOVER** | Foam Roller（EVA / Vibrating）、Fascia Gun、Fascia Ball、Massager | 20 | EVA Foam Roller、Fascial Sphere |

### 2.3 规格字段口径（实测覆盖度）

| 字段 | 覆盖数 | 示例 |
|---|---|---|
| Material | 107 | `PU+Rubber` / `Natural Rubber` / `Silicone + Cast Iron` |
| Color | 85 | `Milk Tea Color / Dark Gray / Jade Green` |
| Size | 83 | `183x68cm` / `Handle 19.3*3.1cm` |
| Logo | 78 | `Customization Available` |
| Feature | 70 | `Non-slip, Eco Friendly, Wear-Resistant` |
| Packing | 58 | `Poly Bag+Carton or customized` |
| Thickness | 51 | `4.5mm or Customized` |
| Weight | 17 | `2900g` / `800g/1050g` |
| Package | 11 | `Kraft Paper Box` |
| Applicable Users | 7 | `Children` |
| Rope Length | 6 | `3m` |
| Strength / Resistance / Ball Diameter | 4 | `15lbs, 25lbs, 35lbs` |

> 品类专属字段用法值得学：跳绳用 `Rope Length` + `Applicable Users`，弹力带用 `Strength / Resistance`，健身球用 `Ball Diameter`。我们现在这些信息全塞进 Size 一行。

### 2.4 它的数据问题（**别抄进去**）

| 问题 | 数量 | 实例 |
|---|---|---|
| 规格表为空 | 60 页（36%） | Stair Climbers、Ab Roller、Massager-1/2/3、Fascia Gun-1/2/3、Pilates 全系 11 页 |
| 占位 slug（数字后缀） | 60 个 | `tpe-yoga-mat-5/6/7/8`、`pu-rubber-yoga-mat-2…12`、`fascia-gun-1/2/3` |
| 产品重名 | 18 组 / 66 页 | `PU Rubber Yoga Mat` ×13、`TPE Yoga Mat` ×8、`Yoga Hammock` ×5 |
| 单位混用 | — | `183cm*61cm` vs `185x68cm` vs `183×61/80/90cm`；厚度 `0.45cm` 与 `4.5mm` 混写 |
| 字段自相矛盾 | 多页 | `tpe-yoga-mat-5`：Size 写 `183*80*0.6/0.8/1/1.2cm`，Thickness 又写 `6mm` |
| 类目错放 | — | `pilates-reformer-mat2` 标题是 Pilates Reformer Mat，类目挂在 **Adjustable Dumbbell** 下 |
| 拼写错 | 2 处 | 页面 `/fithess/`（Fitness 拼错）、类目 `dumbbel` |
| 测试页残留 | 2 页 | `pu-rubber-yoga-mat-test`（实为 TPE 迷彩垫）、`pu-rubber-yoga-mat-test` 类目归类为 PU |
| 博客 Lorem ipsum | 3 篇 | 首页 LATEST NEWS 展示假文 |
| 无 MOQ / 无认证 | 全站 | 无 MOQ、无 REACH/ISO/BSCI 信息 |

---

## 三、能不能"以它为准"——分三层判断

| 层级 | 判断 | 说明 |
|---|---|---|
| **① 类目结构** | ✅ 可以照抄 | 4 板块 + 50 子类逻辑专业，是它的最大资产 |
| **② 字段口径** | ✅ 照它，但补 2 个 | 用它的 8 字段 + 保留我们的 MOQ、认证 → 变 10 字段 |
| **③ 规格数值** | ⚠️ 41 条可用，12 条需回厂确认 | 它有数据的产品里，瑜伽垫/瑜伽柱/弹力带数值可信；健身器械、Pilates 全空 |

---

## 四、字段口径改造方案

### 4.1 现状 → 目标

| 我们现行 7 字段 | 目标站 8 字段 | 建议最终 10 字段 | 动作 |
|---|---|---|---|
| Material 材质 | Material | Material | 保持，改写法（`TPE (eco double-layer)` → `TPE`） |
| Size 尺寸 | Size | Size | 保持，细分 |
| Thickness 厚度 | Thickness | Thickness | **拆出去**（现在全站 27 页有 20 页写 `—`） |
| — | **Weight** | **Weight** | 🆕 新增（27 页里 26 页缺） |
| Colors & Print | Color | Color | 保持，**它列具体色名，我们只写 "Custom colors"** |
| — | **Feature** | **Feature** | 🆕 新增（可复用它现成的三连词 `Non-slip, Eco Friendly, Wear-Resistant`） |
| — | **Logo** | **Logo** | 🆕 新增（写成 `Customization Available` 降低询盘门槛） |
| Packaging | Packing | Packing | 保持 |
| MOQ 起订量 | ❌ 无 | **MOQ** | **保留**——我们的核心优势，不能丢 |
| Compliance 合规认证 | ❌ 无 | **Compliance** | **保留**——REACH/BSCI 是它没有的护城河 |

**最终建议顺序**：`Material → Size → Thickness → Weight → Color → Feature → Logo → MOQ → Compliance → Packing`

### 4.2 关键写法差异（照它的写法改）

| 项目 | 我们现在 | 它 | 建议 |
|---|---|---|---|
| 尺寸单位 | `1830×610 / 1850×900 mm` | `183x61cm` | 跟它用 cm（`183×61cm`），英文站保留英制括号 |
| 厚度 | `4–12 mm` | `6mm or Customized` | 跟它写 `6mm (or customized)` |
| 颜色 | `Custom colors & prints` | `Purple, Blue, Black` | **必须列具体色名**，它是 85 个产品的卖点 |
| 表面特征 | 无 | `Non-slip, Eco Friendly, Wear-Resistant` | 照抄这组词（行业通用，无风险） |
| 包装 | `Shrink wrap + carton` | `Poly Bag+Carton or customized` | 统一成 `Poly bag + carton (customizable)` |

---

## 五、27 页逐页改动清单（核心）

标注：✅ 数值可直接用 ｜ ⚠️ 有冲突需确认 ｜ 🆕 目标站无对应（我们不能删，只能自己补数据）

### 5.1 瑜伽垫（ym1–ym8）

| 我们的页 | 目标站对应 | 现行写法 | 目标站写法 | 判断 |
|---|---|---|---|---|
| **ym1** TPE 垫 | `tpe-yoga-mat` 等 11 个 SKU | Size: 1830×610 / 1830×800 / **1850×900** / **2000×1000** / **1850×1220** mm<br>Thickness: 4–12 mm | Size: `183x61cm 6/8mm`、`183x80cm 6/8mm`、`183×61/80/90cm`、`183*90*0.6/0.8cm`<br>Thickness: `6mm / 8mm / 10mm / 12mm`<br>Weight: `800g/1050g`、`1100g/1200g`<br>Color: `Purple, Blue, Black` | ⚠️ **它长度固定 183cm，我们却有 1850/2000**；它宽 61/80/90，我们有 900/1000/1220。需统一。Weight 可直接补 |
| **ym2** 加宽 TPE | `tpe-yoga-mat-5/6/7/8`、`tpe-eco-friendly-yoga-mat` | Size: 80 / 122 cm width; 1830–2000 mm length | `183*80*0.6/0.8/1/1.2cm`、`183*90*0.6/0.8cm` | ⚠️ 它把 80/90cm 当独立 SKU，不设"加宽"概念。建议 **ym2 并入 ym1**，避免自己跟自己竞争 |
| **ym3** 双人加宽 | `tpe-double-yoga-mat` | 122 cm width; 1830–2000 mm | Size: `185x122cm`，Thickness `6mm/8mm`，Color `Matcha Green + Dark Gray` | ✅ 长度改成 185cm，补双色配色 |
| **ym4** 折叠 TPE | `folding-mat`、`folding-yoga-mat`、`folding-yoga-mat-2` | Tri-fold, 1830×610 mm, 6 mm | `183*61cm, 14*61cm (Folded Size)` 6mm<br>`183*61cm, 30*37*7cm (Folded Size)` 4mm | ✅ **可补"折叠后尺寸"**——这是我们完全没有的高价值参数 |
| **ym5** PU/橡胶高端 | `pu-rubber-yoga-mat` 等 12 个 | Size: **1830×610 / 1850×800**，Thickness 4–6 mm | Size: **185x68cm**（PU 全是 68cm 宽）<br>Thickness `4.5mm`<br>Weight: `2900g`（磨砂款） | ⚠️ **宽 800 是错的，它是 680**（与 9/11 SKU 表结论一致）。补 Weight 2900g |
| **ym6** 磨砂 PU | `matte-pu-rubber-yoga-mat` | 1830×610 / 1850×800，4–6 mm | `185cm*68cm*0.45cm`，Weight `2900g`，Color `Milk Tea / Dark Gray / Soft Pink / Light Purple / Jade Green` | ⚠️ 同上改 680 + 补 5 个具体色名 |
| **ym7** 迷彩 PU | `pu-rubber-yoga-mat-test`（实为 **TPE Camouflage Yoga Mat**） | Material: Natural rubber base + PU top | Material: **TPE**，`183x68cm`，`6mm`，Color `Camouflage Pink/Blue/Purple/Green` | ⚠️⚠️ **材质冲突**：目标站说迷彩是 TPE，我们写 PU。必须回厂确认（与 9/11 目录 PDF 结论也冲突） |
| **ym8** 平衡训练器 | 🆕 无对应 | Diameter 63 cm; platform 58 cm | — | 🆕 目标站无此品类，保留我们的数据（63cm），但**别按它的 58cm 改** |

### 5.2 瑜伽配件（pr1–pr5）

| 我们的页 | 目标站对应 | 现行写法 | 目标站写法 | 判断 |
|---|---|---|---|---|
| **pr1** 空中吊床 | `yoga-hammock` 等 8 个 | Material: High-strength **aerial silk (nylon)**；Size: Custom length (**4–8 m**) | Material: **Polyester**（普通款）/ **210T Nylon Taffeta**（带手柄款）；**无长度字段** | ⚠️ 材质口径不同：它分涤纶/尼龙塔夫绸两档。建议按它的分法拆成"涤纶款 / 210T 尼龙款"，长度保留我们的 4–8m（比它全） |
| **pr2** 瑜伽轮 | 🆕 有类目 `yoga-wheel` 但**无产品页** | Diameter 33 / 38 cm | — | 🆕 目标站类目空着，无法对标。保留我们的 33/38cm |
| **pr3** 冥想坐垫 Zafu | `yoga-bolster`（是抱枕不是 Zafu） | Buckwheat fill + cotton cover；Round / rectangular | Material: `100% Polyester + Sponge`；Size `64*24*13CM`；Weight `550g`；Color `Beige, Gray, Pink, Purple` | ⚠️ 品类不同（Zafu vs Bolster）。**建议新增 Yoga Bolster 页**照抄它的数值，Zafu 保留 |
| **pr4** EVA 瑜伽砖 | `eva-yoga-block`（无规格）、`yoga-block-cover`（硅胶） | 9×15×23 cm (standard) | 无数据 | ✅ 保留我们的，它反而没数据 |
| **pr5** 膝盖垫 | 🆕 有类目 `yoga-knee-pads` 无产品页 | Custom | — | 🆕 保留我们的，建议补具体尺寸 |

### 5.3 瑜伽柱 / 按摩（fr1–fr5）

| 我们的页 | 目标站对应 | 现行写法 | 目标站写法 | 判断 |
|---|---|---|---|---|
| **fr1** 狼牙柱 | `foam-roller`、`eva-foam-roller-2` | Size: **45×14 cm** | Size: `33cm/45cm`、`45*12.5CM/33*12.5CM` | ⚠️ **直径冲突**：14 vs 12.5。回厂确认（与 SKU 表冲突项一致） |
| **fr2** 实心柱 | `foam-roller-2`、`foam-roller-3` | 25×7.5 to 45×14 cm | `30cm/33cm/45cm`、`33cm/45cm` | ⚠️ 同样 14 vs 12.5；它只给长度不给直径 |
| **fr3** 电动柱 | `vibrating-foam-roller`、`vibrating-yoga-roller` | EVA + rechargeable motor；33×13 cm | 无数据 | ✅ 保留我们的（它 2 页都空） |
| **fr4** EVA 按摩柱 | `eva-foam-roller`、`advanced-yoga-roller` | Smooth / grid / half-roller | 无数据 | ✅ 保留，建议补具体尺寸 |
| **fr5** 按摩球 | `fascial-sphere-1/2/3` | TPE / EVA；Ø 6–10 cm | 无数据 | ✅ 保留（它 3 页全空） |

### 5.4 弹力带 / 球（rb1–rb4）

| 我们的页 | 目标站对应 | 现行写法 | 目标站写法 | 判断 |
|---|---|---|---|---|
| **rb1** 弹力带 | 9 个 SKU：`exercise-bands`、`figure-8-resistance-bands`、`resistance-band`、`tpe-resistance-loop-band` 等 | Material: **Latex / fabric**；Size: Loops / tubes / figure-8 | Material: **TPE** / **Silicone**<br>`1500*150*0.35mm`、`600*50*0.8mm`、`42*14cm`、`44cm*9.9cm*5mm`<br>Strength: `15lbs, 25lbs, 35lbs`<br>Resistance: `10-50 LBS` | ⚠️ **材质冲突**：我们写 Latex/fabric，它全系 TPE/Silicone。需确认我们是否真做乳胶款。它的 Strength/Resistance 字段值得直接引入 |
| **rb2** 迷你瑜伽球 25cm | `yoga-ball`（无规格） | Ø 25 cm | 无数据 | ✅ 保留 |
| **rb3** 平衡半球 | 🆕 无对应 | Ø 60 cm | — | 🆕 保留（它无此品类） |
| **rb4** 平衡板 | `fitness-board`（PP+Foam）、`p3-fitness-board`（PP+TPE） | Plywood + TPE surface | Material: `PP + Foam` / `PP+TPE` | ⚠️ 材质口径不同（它的是腹肌板）。保留我们的，但可借它的材料表述 |

### 5.5 健身器械（fi1–fi5）

| 我们的页 | 目标站对应 | 现行写法 | 目标站写法 | 判断 |
|---|---|---|---|---|
| **fi1** Mini Stepper | `stair-climbers` | Steel + ABS；Size "Compact footprint" | 无数据 | 🔴 **先修 bug**：H1 显示 `Mini Stepper — SANFAN硅胶哑铃`（标题与产品不符）。数值需自己补 |
| **fi2** 壶铃 | `kettlebell`（无规格）、`kettlebell-2` Bag Kettlebell | Coated cast iron；4–24 kg | Bag Kettlebell：`Silicone + Cast Iron`，`20x18cm`，`4500g`，`Pink, Green, Beige`，`Kraft Paper Box` | ⚠️ 我们的 4–24kg 是铁壶铃，它的是硅胶内胆袋式壶铃（不同 SKU）。**建议按它的拆成"硅胶系列 + 铸铁系列"两页** |
| **fi3** 跳绳 | 8 个 SKU | PVC rope + foam/ABS handles；"Adjustable length" | 每款有：Handle 尺寸、`Rope Length 2.2/2.8/3m`、颜色、`Applicable Users: Children`、`Packing: Customized Package` | ⚠️ 它一个跳绳拆 8 页。**建议我们拆 3 页**（成人/儿童/智能计数），补 Handle 尺寸与绳长 |
| **fi4** Home Stepper | `stair-climbers-2/3` | Steel + hydraulic；"Compact" | 无数据 | ✅ 保留，补具体尺寸 |
| **fi5** 哑铃/壶铃套装 | `adjustable-dumbbell`、`dumbbel`、`dumbbell`、`dumbbell-2` | Coated cast iron + TPE；6kg/2kg set | Silicone Dumbbell：`Silicone + Cast Iron`，`1-2.5kg`，`Kraft Paper Box`<br>Barbell：`91cm/110cm`，`15lbs/25lbs` | ⚠️ 它有完整"硅胶系列"（14 个 SKU，2025 新品），我们完全没有 |

---

## 六、品类结构重构方案

### 6.1 建议的新导航（对齐 4 板块）

```
YOGA     → Yoga Mats | Yoga Props & Accessories | Resistance Bands | Yoga Hammock | Yoga Wear
FITNESS  → Fitness Accessories | Free Weights | Fitness Equipment | Silicone Series
PILATES  → Pilates Equipment | Pilates Reformer Mat        ← 我们目前完全没有
RECOVER  → Foam Roller | Fascia Gun | Fascia Ball | Massager
```

### 6.2 我们现有 5 组 → 新 4 板块映射

| 现分组 | 归入 |
|---|---|
| Yoga Mats（#yoga） | YOGA > Yoga Mats |
| Yoga Props & Accessories（#props） | YOGA > Yoga Accessories |
| Foam Rollers & Massage（#rollers） | **RECOVER** |
| Resistance Bands & Pilates（#bands） | 拆开：Resistance Bands → YOGA；Pilates 部分 → **PILATES** |
| Fitness Equipment（#fitness） | **FITNESS** |

> 关键改动：把 "Resistance Bands & Pilates" 这个混合组拆开，**PILATES 独立成板块**——这是它结构上最值得学的一步。

### 6.3 目标有、我们没有的品类（补页清单）

| 优先级 | 品类 | 产品数 | 理由 |
|---|---|---|---|
| 🥇 P1 | **Silicone Series**（硅胶哑铃/杠铃/壶铃/普拉提圈） | 14 | 2025 主推新品，高溢价，我们有产能 |
| 🥇 P1 | **Pilates Equipment**（核心床/凯迪拉克床/椅子/梯桶） | 11 | 客单价最高，B2B 最想要，直接拉高站点档次 |
| 🥈 P2 | **Yoga Wear**（瑜伽裤/短裤/背心） | 18 | 单量品类，但需供应链确认 |
| 🥈 P2 | **Fascia Gun / Fascia Ball / Massager** | 13 | RECOVER 板块必须丰满 |
| 🥈 P2 | **Jump Rope 细分**（智能计数/无绳/儿童/竞速） | 8 | 现有 1 页拆成 3–8 页 |
| 🥉 P3 | **Cork / Suede 系列垫** | 20+ | 高溢价材质，欧洲市场吃香 |
| 🥉 P3 | Yoga Bolster / Bag / Ball / Block Cover | 4 | 补齐配件闭环 |

---

## 七、必须回厂确认的 12 项冲突

| # | 项目 | 我们写的 | 目标站写的 | 影响 |
|---|---|---|---|---|
| 1 | TPE 垫长度 | 1850 / 2000 mm | 固定 183cm（或 181/185） | ym1/ym2 全页尺寸 |
| 2 | TPE 垫最大宽度 | 1220 mm | 900 mm（双人款才 1220） | ym1/ym2 |
| 3 | PU 垫宽度 | **800 mm** | **680 mm** | ym5/ym6/ym7 |
| 4 | 迷彩垫材质 | PU | **TPE** | ym7 整页重写与否 |
| 5 | 瑜伽柱直径 | 14 cm | **12.5 cm** | fr1/fr2 |
| 6 | 弹力带材质 | Latex / fabric | **TPE / Silicone** | rb1 整页 |
| 7 | 吊床材质 | aerial silk (nylon) | Polyester / 210T Nylon Taffeta | pr1 |
| 8 | 瑜伽砖尺寸 | 9×15×23 cm | 无数据 | 保持 |
| 9 | 平衡训练器 | 63 cm | 无此品类 | 保持（**不要照它改 58**） |
| 10 | 磨砂 PU 重量 | 无 | 2900g | ym6 可直接补 |
| 11 | TPE 垫重量 | 无 | 800g/1050g（61cm）、1100g/1200g（80cm） | ym1 可直接补 |
| 12 | 折叠垫折叠后尺寸 | 无 | 14×61cm / 30×37×7cm | ym4 可直接补 |

**其中 #1–#7 必须回厂拿实物确认**，不能靠任一网站口径定案。#10–#12 可直接照目标站补。

---

## 八、执行方案

### 8.1 影响范围

| 类型 | 文件数 |
|---|---|
| 产品详情页（27 页 × 7 语言） | 189 |
| 产品列表页（products.html × 7 语言） | 7 |
| 首页/导航（改类目树） | 7 |
| JSON-LD（Price / Size / Material 同步） | 27（EN 内） |
| sitemap.xml / hreflang | 1 |
| **合计触及** | **约 231 个文件** |

### 8.2 分三阶段推进

| 阶段 | 内容 | 交付 | 风险 |
|---|---|---|---|
| **阶段一（低风险，先做）** | ① 字段口径改造：27 页规格表统一成 10 字段，补 Weight / Feature / Logo<br>② 填报可直接用的 41 条数值<br>③ 修 fi1 标题 bug | 27 页 EN 版上新 | 低 |
| **阶段二（结构）** | ① 类目重构：5 组 → 4 板块<br>② 导航/首页/列表页同步<br>③ 6 语言版本跟进 | 231 文件 | 中（需全站 bump `?v=` + hreflang 复核） |
| **阶段三（扩品类）** | 按 P1 → P2 → P3 补页（Silicone 14 → Pilates 11 → 其余） | 新增 60+ 页 × 7 语言 | 高（工作量大，建议分批） |

> ⚠️ 阶段一、二建议在**回厂确认 7 项冲突之后**再动数值；结构重构可先做。

### 8.3 不建议照抄的 5 件事

1. **不要抄它的"无 MOQ"**——我们的 100 片起订是核心卖点。
2. **不要抄它的"无认证字段"**——REACH / BSCI / ISO 是我们区别于它的武器。
3. **不要抄占位 slug 命名**（`xxx-2`、`xxx-3`）——我们站是静态 SEO 站，重名会直接毁掉关键词排名。
4. **不要抄它的"无价格"**——我们 JSON-LD 已有价格区间（2.5–18 USD），对 AI 搜索(GEO)是加分项，保留。
5. **不要抄它的页面拼写错误**（`fithess`、`dumbbel`）。

---

## 九、一句话行动建议

> **结构照它、字段照它 + 补 MOQ/认证、数值只信 41 条、7 项冲突回厂。**
> 先做阶段一（字段口径 + 已确认数值），成本最低、询盘质量提升最直接；类目重构等冲突项确认后一次性做完，避免返工 7 个语言版本。

---

### 附：原始数据

- 目标站全量产品规格：`/tmp/sf_products.json`（167 条）
- 目标站规格报告（按类目）：`/tmp/sf_report.txt`
- 我们站现行规格：`/tmp/ours_products.json`（27 条）
- 逐页差异明细：`/tmp/diff_report.txt`
