# 8 个一级分类页补内容 —— 执行与验收报告（2026-09-25）

方案：`i18n_build/reports/category_content_plan_20260925.md`
状态：**英文侧已完成并验证通过**；语言版被 DeepL 配额阻塞（见第五节）

---

## 一、结论

| 项 | 结果 |
|---|---|
| 补了什么 | 每页「品类导语 3 段」+「买家 FAQ 5 条（可见块 + FAQPage）」+「正文内链 3 条」 |
| 英文页词数 | 685 → 862（原 177–356），**8 页全部落进 600–1200 带内** |
| H2 数 | 1 → **4**（导语 / FAQ / 内链 / 尾部 CTA） |
| 审计回归 | 未达标 **209 → 201**（正好清掉这 8 页）；**C1「词数不足」全站清零** |
| 浏览器验收 | 168 个「视口 × 语言 × 页面」组合，**异常 0** |
| 链接审计 | 61,386 个 `<a>`，404 / 跨语言 / 坏锚点 / 空 href **全 0** |
| 语言版 | ⛔ **未做** —— DeepL 免费额度已耗尽（500,000 / 500,000） |

---

## 二、改了哪些文件

| 类别 | 文件数 | 说明 |
|---|---:|---|
| 8 个分类页 × 7 个语言目录 | **56** | `foam-rollers` / `jump-ropes` / `resistance-bands` / `suede-cork-yoga-mats` / `meditation-pilates-mats` / `yoga-props-accessories` / `strength-training` / `massage-recovery` |
| 脚本 | 2 | 新增 `add_category_content_20260925.py`；扩写 `add_internal_links_20260925.py` |
| 验收脚本 | 1 | 新增 `verify_category_content_20260925.cjs` |

**页面最终结构**（导语在网格**之前**，这是移动端实测后的修订）：

```
<section class="hero">                       不动
<!-- catintro:v1 -->  导语 H2 + 3 段          ← 新增（≈230 词）
<section class="section">  H1 + 产品网格       不动
<!-- cfaq:v1 -->      FAQ H2 + 5 条 details   ← 新增（≈240 词）
<!-- ilink:v1 -->     Sourcing guides + 3 链   ← 新增（≈37 词）
<section class="section soft">  尾部 CTA      不动
<!-- cfaq-ld:v1 -->   FAQPage JSON-LD        ← 新增（插在 orgref 之前）
<!-- orgref:v1 -->  …                        不动（新内容绝不进这个区间）
```

---

## 三、逐页实测（审计口径，非估算）

| 页面 | 补前 | 补后 | 区间 | H2 | H3 | 失败项 | desc 宽 |
|---|---:|---:|:--:|---:|---:|---:|---:|
| foam-rollers | 230 | **782** | 600-1200 | 4 | 0 | 0 | 142 |
| jump-ropes | 177 | **685** | 600-1200 | 4 | 0 | 0 | 156 |
| resistance-bands | 195 | **701** | 600-1200 | 4 | 0 | 0 | 138 |
| suede-cork-yoga-mats | 235 | **749** | 600-1200 | 4 | 0 | 0 | 144 |
| meditation-pilates-mats | 192 | **708** | 600-1200 | 4 | 0 | 0 | 147 |
| yoga-props-accessories | 356 | **862** | 600-1200 | 4 | 0 | 0 | 152 |
| strength-training | 228 | **728** | 600-1200 | 4 | 0 | 0 | 150 |
| massage-recovery | 227 | **763** | 600-1200 | 4 | 0 | 0 | 150 |

新增正文合计 **3,883 英文词 / 21,826 字符**（导语 ≈230 词 + FAQ ≈240 词，每页）。

---

## 四、验证（12 项）

| # | 项 | 判据 | 结果 |
|---|---|---|---|
| 1 | 标签配平 | `<section>/<div>/<h2>/<p>/<details>/<summary>/<ul>/<li>/<a>/<span>` 开闭相等 | 56 文件 **0 处不配平** |
| 2 | 结构守恒签名 | 相对 HEAD 的标签增减 | 每页 **+40 开 / +40 闭**（8 页完全一致） |
| 3 | 文案未泄漏 | 新文案不得出现在标记块之外 | **0 处泄漏** |
| 4 | 标记成对 | 4 组标记各 1 对 | **0 处不配对** |
| 5 | 幂等 | 重跑 changed == 0 | ✅ 两脚本均 0 |
| 6 | 互逆 | `剥离(插入(s)) == s` | ✅ 内置断言全过 |
| 7 | JSON-LD | 每页 FAQPage 1 个 / 5 问答 / inLanguage 正确 | 8/8 ✅；全站 899 块解析失败 **0** |
| 8 | `#faq-cat` 唯一 | 全站计数 | **22**（tpe/pu 14 + 本轮 8）✅ |
| 9 | 链接 | 404 / 跨语言 / 坏锚点 / 空 href | 61,386 链接 **全 0** |
| 10 | 浏览器渲染 | 168 组合：溢出 / JS 错误 / details 展开有内容 / h1=1 / h2=4 | **异常 0** |
| 11 | 折叠行为 | 首条 `<details>` 展开后正文长度 | 全部 > 40 字符 ✅ |
| 12 | 审计回归 | `audit_en_seo_standard` | 未达标 209 → **201**；C1 词数不足 **0 页** |

### 移动端位置实测（390×844）

| 页面 | 文档高 | 导语位置 | FAQ 位置 |
|---|---:|---|---|
| foam-rollers | 7,319px | **第 1.19 屏** | 第 5.2 屏 |
| jump-ropes | 6,560px | **第 1.22 屏** | 第 4.3 屏 |
| yoga-props-accessories | 9,318px | **第 1.22 屏** | 第 7.6 屏 |
| massage-recovery | 7,753px | **第 1.19 屏** | 第 5.7 屏 |

→ 方案 B（导语上移到网格之前）生效：**6.5 屏 → 1.2 屏**，与预期一致。
320×568 最窄视口：导语落在第 **2.1–2.2 屏**（原方案为 6.5 屏）。

---

## 五、⛔ 阻塞项：DeepL 免费额度已耗尽

| 项 | 值 |
|---|---|
| 额度上限 | 500,000 字符/月 |
| **已用** | **500,000（100%）** |
| 语言版实际需要 | **130,956 字符**（= 21,826 × 6 语言，无缓存命中） |
| 可用的备引擎 | MyMemory —— **质量不可用** |
| HTTP 症状 | `456`（Quota exceeded）→ 自动降级 MyMemory |

### 时间线（如实记录）

1. 开工前探配额：**401,592 / 500,000（剩 98,408）**
2. 试跑英文结构验证时，脚本 `--langs ""` 触发了一个自身 bug
   （`langs or LANGS` 对**空列表**回退成全部 6 语言）→ 意外发起 768 次全语言翻译
3. 98,408 字符在这一次被耗尽；剩余请求降级 MyMemory，产出的是**错误译文**
   （例：`EVA and EPP…` → de `EVA EPP und EVA sind die beiden Schaumstoffe…`，EPP 被译成 EVA）
4. 已处置：
   - 删除被污染的 `category_content_data.json`
   - **精确删除**翻译缓存里本次新增的 **768 个键**（`26,369 → 27,137 → 26,369`，已回到污染前状态）
   - 备份留在 `/tmp/translations_backup_20260925.json`
   - 修复 bug（改为 `LANGS if langs is None else langs`）

⚠️ **即使没有这次误触发，语言版也做不成** —— 剩余 98,408 字符 < 需要的 130,956 字符。
误触发的实际代价是：这 98,408 字符被浪费在了不可用的降级译文上，而本来它也只能覆盖 4 个语言。

### 三条出路（需决策）

| 方案 | 成本 | 说明 |
|---|---|---|
| **A. 等额度重置** | ¥0 | DeepL Free 每月重置。语言版 6 页 × 8 = **48 文件**可一次补完 |
| **B. 换 / 增加 key** | ¥0 | 若手上有第二个 DeepL Free 账号，写入 `i18n_build/.deepl_key` 即可继续 |
| **C. DeepL Pro** | 付费 | 额度更大，但不必要（只需 13 万字符） |

**英文侧不受影响** —— 它用**手写中文**，完全不走 API，已落盘并验证通过。

---

## 六、未决项（按项目纪律单列，本轮未擅自改）

### 1. 内链点击热区 18px（触屏不达标）

`ilink` 块的 `<a>` 是 `inline`、纵向 padding 0，实测真实可点区间 **18px**（WCAG 2.5.8 AA 下限 24px）。

| 形态 | 真实热区 | li 高 | ul 高 |
|---|---:|---:|---:|
| 现状（本轮 8 页也是这个） | **18px** ❌ | 32px | 96px |
| `display:inline-block; padding:6px 0` | **44px** ✅ | 44px | 132px |

⚠️ 为什么没顺手改：
1. 这是**行为/样式变更**（不是修缺陷），且要**同时改 CSS + 已上线的 tpe / pu / materials / products 四页及其语言版**，否则站内两种热区尺寸并存；
2. 改 CSS 必须 bump 资源版本号（`20260925b` → `c`），会牵动全站缓存失效。

**建议**：单独一批做，改动范围 = `styles.css` + 12 个分类页 × 7 语言。

### 2. 语言版内容缺失（由第五节的配额问题派生）

EN 页现在有 4 个 H2、685–862 词；语言版仍是 1 个 H2、177–356 词。
hreflang 关系正常，不构成错误，但**语言版内容比英文源薄**，不理想。

---

## 七、内容纪律（防模板化）

8 页都是配件类，极易写成同一骨架。硬抓手 = 每页导语挂**本页独有的卡名事实**：

| 页面 | 独有事实（全部来自本页 hero / 卡名） |
|---|---|
| foam-rollers | 30 / 33 / 45 cm、12.5 cm 直径、45 cm(18") 空心省运费、狼牙纹 |
| jump-ropes | 握柄 12 / 14.8 / 19.3 cm、无绳 19.3×3.1 cm、珠节弧线 |
| resistance-bands | 环形 60 cm、站姿套装 150 cm、厚度 0.8/1.0/1.2 mm、宽度 0.35/0.45/0.55 mm |
| suede-cork | 68 cm 圆、40×60 cm 方、183/185×68 cm 满版、折叠款不卷边 |
| meditation-pilates | 瑜伽枕 64×24×13 cm / 550 g、68 cm 圆、器械垫按图纸裁 |
| yoga-props | 迷你球 25 cm(10")、吊床 1×2.6 m → 5×2.8 m、普拉提环 34 / 40 cm |
| strength-training | 健身板 106×41×7 cm、杠铃 91 / 110 cm、六种硅胶配色、液压登山机免供电 |
| massage-recovery | 按摩棒 34 / 32 cm、筋膜枪四种握型、六色筋膜球套装 |

**站内去重**：未碰 `materials`（4 问）/ `tpe`（5 问）/ `pu`（5 问）已答过的题；8 页之间无重题。
**检测类不写标准号**：这 8 页页面自身**没有** ROHS / CE / ISO 9001 / BSCI / SGS
（`REACH` 只出现在全站实体层 `knowsAbout` 的能力列表里）→ FAQ 一律写「按目标市场确认」。

---

## 八、复现命令

```bash
# 步骤 1（必须在前，它造出 cfaq 需要的 <!-- ilink:v1 --> 锚点）
python3 i18n_build/add_internal_links_20260925.py --dry-run
python3 i18n_build/add_internal_links_20260925.py

# 步骤 2  英文（零 API 消耗）
python3 i18n_build/add_category_content_20260925.py --dry-run --langs ""
python3 i18n_build/add_category_content_20260925.py --apply  --langs ""

# 步骤 3  语言版（等 DeepL 额度恢复后再跑）
python3 i18n_build/add_category_content_20260925.py --apply --langs de,ja,ko,fr,it,es
python3 i18n_build/add_category_content_20260925.py --check

# 验收
python3 i18n_build/audit_en_seo_standard_20260925.py
python3 i18n_build/audit_links_20260916.py
node i18n_build/verify_category_content_20260925.cjs
```

---

生成：2026-09-25 · 英文侧完成，语言版待 DeepL 配额恢复
