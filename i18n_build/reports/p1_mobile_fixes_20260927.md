# 移动端 P1 修复落地报告（Vercel WIG）

- 日期：2026-09-27
- 判据源：`vercel-labs/web-interface-guidelines`（`i18n_build/reference/vercel_wig_AGENTS.md`，156 行 MUST/SHOULD/NEVER）
- 改动范围：`assets/css/styles.css`（**+49/−0**）、`assets/js/main.js`（**+7/−1**）、资源版本号 `20260927a → 20260927b`
- 站点 HTML：**仅资源版本号变化**（1331 文件 / 2662 处）

---

## 1. 四条计划项的执行结果

| # | 项 | 状态 | 备注 |
|---|---|---|---|
| P1-1 | `:focus-visible` 键盘焦点环 | ✅ **已落地** | 从「几乎无指示」变实心品牌色环 |
| P1-2 | `scroll-margin-top` 锚点避让固定头部 | ✅ **已落地（性质更正，见 §3）** | 属规范对齐 + 健壮性，**不是**修正在发生的缺陷 |
| P1-3 | `prefers-reduced-motion` | ✅ **已落地（CSS + 1 处 JS）** | 改前该偏好被完全无视 |
| P1-4 | `env(safe-area-inset-*)` 安全区 | ⏸ **实测后暂缓，单列决策（见 §4）** | 需先改 1331 页 meta 的 `viewport-fit=cover` 才有意义，且**本地无法验证** |

---

## 2. 实测证据（改前 → 改后）

探针：`i18n_build/probe_p1_baseline_20260927.cjs`（主）/ `probe_p1_extra_20260927.cjs`（补充）

### P1-1 焦点可见性

| 对象 | 改前 | 改后 |
|---|---|---|
| `.field input/select/textarea`（6 个） | `outline: none/0px`，仅 1px 边框变色 | **`outline: solid 2px rgb(14,107,92)`** + 边框变色 |
| `.sr-input`（JS 注入的搜索框） | **outline / border / background / box-shadow 四项全无变化**，键盘用户完全看不出焦点 | **实心 2px 品牌色环** |
| 键盘 Tab 前 30 个元素 × 3 页（90 个） | 匹配 `:focus-visible` 90/90，但样式是**浏览器默认环** | 统一为品牌色环（见 A/B 图 ③） |

> ⚠️ **测法必须用真实键盘 Tab**：`el.focus()` 是脚本聚焦，Chrome 判定为非键盘交互 →
> 按钮/链接**不会**匹配 `:focus-visible`，用脚本 focus() 测会得出完全相反的结论。
> 文本框例外（属「需要键盘输入」的元素，永远匹配），故 `.field` / `.sr-input` 可用 focus() 定点验。

### P1-2 锚点落点（**数字已更正**）

| | 改前 | 改后 |
|---|---|---|
| `#lines`（`section.section`，自带 `padding-top:78px`）视口内 top | **0** | **82** |
| `scroll-margin-top` computed | `0px` | `82px` |
| 头部 `bottom` / 高度 | 69 / 69（sticky） | 69 / 69（未变） |
| **被头部那条带子覆盖的文字节点数** | **0 个** | **0 个** |
| 头部与 section 内容之间**实际留白** | **9px**（78−69，贴得很紧） | **91px**（section 自身 78px 留白完整保留在头部之下） |

### P1-3 减弱动态效果

| | 改前 | 改后 |
|---|---|---|
| `html` computed `scroll-behavior`（`prefers-reduced-motion: reduce` 上下文） | **`smooth`**（偏好被无视） | **`auto`** |
| 带过渡元素中「仍在动（≥50ms）」 | **106 / 106**（0.15–0.9s 照旧） | **0 / 762**，全站最长单值 **0.00001s** |
| `main.js` 里 `behavior:'smooth'` 的 `scrollIntoView` | 无视偏好 | 改判 `matchMedia('(prefers-reduced-motion: reduce)')` → `auto` |

### 站点无回归

- CSS 括号 **650/650** 平衡；`@media` **30 → 31**（仅新增减弱动效块）
- `main.js` 通过 `node --check`
- 头部高度 69px 未变；P0 的 5 处效果未受影响

---

## 3. ⛔ 自认错误：锚点那条我先前**夸大了**

本轮初判写的是「**标题被头部盖住 69px**」。**这是错的。**

- 判定依据用的是 `#lines` **包裹层**的 `getBoundingClientRect().top`
- 但 `#lines` 是 `<section class="section">`，**自带 `padding-top: 78px`**
- 于是头部的 69px 只吃掉了这段内边距 → **实测被遮挡的文字节点 = 0 个**（改前改后都是 0）

**真实状况**：改前留白只剩 **9px**（78−69），锚点落点贴得很紧；加 `scroll-margin-top: 82px` 后，
section 的 78px 留白完整出现在头部下方。

所以 P1-2 的准确定性是 **「规范对齐 + 健壮性」**（保证任何无内边距的锚点目标也不会被盖，
外部深链同理），**不是**修复一个正在发生的缺陷。已按此更正报告与技能。
新增独立探针 `probe_anchor_text_coverage_20260927.cjs` 做**文字级**判定，不再用包裹层坐标下结论。

### 同批第二处自认：我自己的探针判据写错了

减弱动效首测报「**仍有非零 transition-duration：762 / 762**」——看着像没修好，其实是我判据的 bug：
`.01ms` = `1e-05s`，数值上 `> 0` 于是被计入。判据改为 **≥50ms 才算仍在动**，复测 **0 / 762** ✓。
（教训：**判据的阈值必须匹配修复手法**，否则「修好了」会被自己的脚本报成「没修」。）

---

## 4. ⏸ P1-4 安全区：实测后判定「本地无法验证」，故不做无证据的改动

三条实测：

1. **meta 无 `viewport-fit`**：全站是 `width=device-width, initial-scale=1.0`
   → 按规范，**没有 `viewport-fit=cover` 时 `env(safe-area-inset-*)` 恒为 0**，
   **光加 CSS 等于什么都没做**（我因此**没有**写入任何 `env()` 规则，避免留下「看似已处理」的死代码 —— 实测 `env(` 在 styles.css 里 0 处）。
2. **CDP 刘海模拟无效**：`Emulation.setDisplayFeaturesOverride` 调用成功，
   但 `env()` 解析值仍是 **`0px`**（桌面 Chromium 不产安全区）→ **本地拿不到任何可验证信号**。
3. 浏览器支持 `CSS.supports('padding-bottom','env(safe-area-inset-bottom)')` = `true`，
   `.cbar` 当前 `padding-bottom: 0px`。

**要真正生效必须**：① 1331 个 HTML 的 meta 加 `viewport-fit=cover`；
② `.cbar` 与移动抽屉补 `env()` 内边距，避免横屏刘海裁字。
**风险**：这是**只能在真机（带刘海 iPhone 横屏）上验证**的行为变更，改动面 1331 文件。
按项目纪律（行为变更单列征询 / 不做无证据改动），**列为待你决策项**，未擅自改。

---

## 5. 交付物

| 类型 | 文件 |
|---|---|
| 报告 | `i18n_build/reports/p1_mobile_fixes_20260927.md`（本文） |
| A/B 对照图 | `i18n_build/reports/p1_fixes_ab_20260927.png`（4 组：表单环 / 搜索环 / 键盘 Tab / 锚点落点） |
| 主探针 | `i18n_build/probe_p1_baseline_20260927.cjs`（A 焦点 / A3 定点 / B 锚点 / C 减弱动效 / D 安全区） |
| 补充探针 | `i18n_build/probe_p1_extra_20260927.cjs`（滚停判定 / 搜索弹层 / CDP 刘海） |
| 文字级遮挡判定 | `i18n_build/probe_anchor_text_coverage_20260927.cjs` |
| A/B 截图 | `i18n_build/ab_p1_screenshots_20260927.cjs`（路由拦截喂 HEAD 版 CSS，零文件改动） |

---

## 6. 剩余未做（P2，来自 `mobile_wig_audit_20260927.md`）

| 项 | 现状 | 说明 |
|---|---|---|
| `translate="no"` | **0 / 1331 页** | 8 语言站刚需：机翻会把 SANFAN / 型号当普通词翻译 |
| `theme-color` | **0 / 1331 页** | 移动端地址栏配色 |
| `preconnect` | **0 / 1331 页** | 首屏连接预热 |
| 图片 `width`+`height` | **491 / 19,109 张缺** | 防 CLS |
| `a.c-link` 热区 **17px** | 导航/页脚文字链，跨 12 页稳定复现 | 属**行为变更**（扩热区、视觉不变），需单列批准 |
| `ilink` 热区 18–19px | 12 个分类页一致 | 同上，与 `a.c-link` 同族，可一并处理 |

## 7. 附：为什么这次 bump 到 `20260927b` 而不是沿用 `20260927a`

P0 提交（`f9f4b3dc`）已把全站标到 `20260927a` 但**尚未推送**。本轮又改了 CSS/JS：
若沿用 `20260927a`，一旦你先单独推送了 P0、之后才推 P1，线上就会出现
「HTML 版本号没变、CSS 内容变了」→ **用户命中旧缓存 CSS**（历史上踩过）。
故保持不变量「**任何一次 CSS/JS 改动都换新版本号**」，本轮推到 `20260927b`。
