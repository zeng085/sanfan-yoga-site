# 移动端 UI 现状体检报告 —— 按 Vercel Web Interface Guidelines 逐条比对

日期：2026-09-27
判据源：`i18n_build/reference/vercel_wig_AGENTS.md`（`vercel-labs/web-interface-guidelines`，★907，MUST/SHOULD/NEVER）
范围：**1331 个 HTML**（en 191 / de 190 / es 190 / fr 190 / it 190 / ja 190 / ko 190）+ `assets/css/styles.css`
**站点文件 0 改动**（纯体检）

---

## 0. 方法与口径

| 层 | 工具 | 回答什么 |
|---|---|---|
| 静态 | `i18n_build/audit_mobile_wig_20260927.py` | 全站 1331 页的 meta / CSS 条款 |
| 浏览器 | `i18n_build/audit_mobile_wig_browser_20260927.cjs` | 390 与 320 视口下 12 个代表页的**实测**（触控热区 / computed style / 抽屉 / 溢出） |
| 自审 | `i18n_build/probe_icon_a11y_20260927.cjs` | 证伪静态层误报 |

代表页：`index` / `products` / `products/ab-wheel` / `materials` / `faq` / `contact` /
`pilates/index` / `pilates-reformer` / `pilates-wunda-chair` / `blog` / `de/index` / `ja/index`

---

## 1. 结论总表（21 项）

### ✅ 已达标（6 项）

| 编号 | 条款 | 实测 |
|---|---|---|
| WIG-01 | **NEVER** 禁用浏览器缩放 | ✅ **0/1331 页**含 `user-scalable=no`/`maximum-scale=1` |
| WIG-02 | **MUST** `viewport` 含 `width=device-width` | ✅ 全部通过 |
| WIG-13 | **NEVER** `transition: all` | ✅ 0 处 |
| WIG-14 | **NEVER** `outline:none` 无可见焦点替代 | ✅ 2 处中 `:focus` 内那处**有 `border-color` 替代**（L440）；⚠️ 仅 L895 `.sr-input` 无补偿 |
| WIG-17 | **MUST** 用 `…` 而非 `...` | ✅ 通过 |
| WIG-21 | **MUST** 纯图标按钮有 `aria-label` | ✅ **76 个纯图标 a/button 全部有名字**（见 §4 纠错①） |

### ❌ 明确缺失（8 项，均为 CSS 单点补齐）

| 编号 | 级别 | 条款 | 实测 |
|---|---|---|---|
| WIG-04 | **MUST** | `touch-action: manipulation` | ❌ **styles.css 0 处**；浏览器实测 **656/656 个可点元素 computed 全为 `auto`** |
| WIG-06 | **MUST** | `env(safe-area-inset-*)` 安全区 | ❌ 0 处 |
| WIG-08 | **MUST** | `prefers-reduced-motion` | ❌ 0 处 |
| WIG-09 | **MUST** | `:focus-visible` 焦点环 | ❌ 0 处 |
| WIG-10 | **MUST** | `scroll-margin-top`（固定头部遮锚点） | ❌ 0 处 |
| WIG-11 | **MUST** | `font-variant-numeric: tabular-nums` | ❌ 0 处 |
| WIG-05 | **SHOULD** | `-webkit-tap-highlight-color` | ❌ 0 处（实测全为 Chrome 默认 `rgba(0,0,0,.18)`） |
| WIG-12 | **SHOULD** | `text-wrap: balance` | ❌ 0 处 |

### ⚠️ 部分达成 / 需处理（4 项）

| 编号 | 条款 | 实况 |
|---|---|---|
| WIG-07 | **MUST** 抽屉/弹层 `overscroll-behavior: contain` | ⚠️ 全站**仅 1 处**，在 `.mm-cats, .mm-apps`（**桌面 mega menu 子菜单**，styles.css L824）。**移动抽屉 `.nav-links` 实测 `overscroll=auto`、body 也 `auto`** → 滚动会穿透到页面 |
| WIG-15 | **MUST** 移动端 input `font-size ≥16px` | ⚠️ **真违规**：L437 `.field input/select/textarea = 15px` → **iOS 聚焦会自动放大页面**。（`.sr-input` 是 16px ✓） |
| WIG-16 | **SHOULD** 品牌名 `translate="no"` | ⚠️ **0/1331 页**。8 语言站刚需——机翻会把 SANFAN/三梵 当普通词处理 |
| WIG-03 | **SHOULD** `<meta name="theme-color">` | ⚠️ **0/1331 页**；实测 body 背景 `rgb(255,255,255)` |

### 📊 资源与非断空格（3 项）

| 编号 | 条款 | 实测 |
|---|---|---|
| WIG-18 | **MUST** 非断空格（品牌名 / `10&nbsp;MB`） | ⚠️ 仅 **11/1331 页**含 `&nbsp;` → 品牌名与数字单位基本未做防断行 |
| WIG-19 | **MUST** 图片显式尺寸（防 CLS） | ⚠️ **491/19,109 张 img** 缺 `width+height`（2.6%） |
| WIG-20 | **MUST** 首屏 preload、其余 lazy | ✅ **16,692/19,109（87%）** 带 `loading="lazy"`；⚠️ **`preconnect` 0/1331 页** |

---

## 2. ⭐ 触控热区实测（浏览器层，390 视口，12 页）

| 类型 | 数量 | 中位边长 | `<24px` | `<44px` |
|---|---|---|---|---|
| `icon`（图标按钮） | 70 | 96.7 | **0** | **0** ✅ |
| `form`（表单控件） | 6 | 44.0 | 0 | 0 ✅ |
| `btn`（按钮） | 95 | 52.8 | **0** | 38 |
| `nav`（导航/页脚链） | 62 | 34.0 | **30** | 62 |
| `other` | 205 | 241.6 | **24** | 63 |
| `inline`（正文内联链） | 218 | 31.1 | 12 | 218 — **按 WIG 精神豁免** |

**最严重的违规**（共 54 个 `<24px` 交互控件，前 10 全是同一个）：

```
17px  a.c-link   nav   index.html / products.html / products/ab-wheel.html
                 materials.html / faq.html / contact.html / pilates/index.html
```

⭐ **`a.c-link` = 17px 高**，跨 12 页稳定复现。这是导航/页脚里的文字链，**视觉正常但热区只有行高**。
WIG 原文对这类有明确出路：`if visual <24px, expand hit area` —— **扩热区、视觉不变**（padding 或伪元素），不是把文字改大。

**汉堡按钮：12/12 页一律 40×40** —— 距 `mobile ≥44px` 只差 4px，且全站一致（改一处即可）。

**320 视口对照**：`icon` 中位边长 73.3（390 时 96.7），`<44px` 仍为 **0** ✓ —— 说明图标按钮的弹性做法是对的。

---

## 3. ⚠️ 320 视口暴露一个新问题（390 看不到）

| 视口 | 溢出页数 | 详情 |
|---|---|---|
| 390 | **0/12** ✅ | — |
| 320 | **1/12** | ⚠️ **`de/index.html` 溢出 57px** |

同样的 12 页，`ja/index.html` 在 320 下 **0 溢出**，只有德语版溢出。

→ 这是**译文膨胀**在极端窄屏的表现（德语复合词天然更长）。390 视口查不出来，**必须单独跑 320**。
（项目既有的 `scan_overflow_20260925.cjs` 默认只测 390，故此前未暴露。）

---

## 4. ⛔ 本轮自审纠错（3 处，均由实测证伪）

### ① WIG-21「3550/3550 图标按钮无 aria-label」= **完全误报**

首版静态脚本用 HTML 正则 `<(a|button)…>` 判定「元素内是否只有图标」——
**HTML 正则做不到这件事**（无法区分 `<a>` 里是图标还是被截断的文字）。

浏览器严谨实测（6 页，检查 `aria-label` / `aria-labelledby` / `title` / `img[alt]` / `.sr-only`）：

```
index.html                     纯图标   1   缺可访问名 0
products.html                  纯图标  71   缺可访问名 0
...
合计：纯图标 a/button 76 个，其中缺可访问名 0 个
```

→ **真实情况：76 个纯图标全部合格（0 缺）**。静态层已改为「不判定」，交浏览器层。
（样本量差异本身也是警报：3550 vs 76 —— 100% 的统计数字应先怀疑自己。）

### ② WIG-14「outline:none 无替代」= **误报**

首版只把 `:focus-visible` 或 `box-shadow` 认作替代，漏了 **`border-color`** 也是合法替代：
`styles.css:440` `.field input:focus{outline:none;border-color:var(--brand)}` → **有替代** ✓。
修正后判据：规则块内含 `border*` / `box-shadow` / `background` 任一即视为有替代。
真正无补偿的只剩 `.sr-input`（L895）。

### ③ WIG-07「overscroll-behavior ✅ 有」= **不精确**

名称命中 ≠ 用对了地方。抓选择器后定位到唯一那处在 `.mm-cats, .mm-apps`
（桌面 mega menu），**移动抽屉根本没吃到**。已改为输出选择器而非计数。

---

## 5. 建议修复清单（按「用户可感知 ÷ 成本」排序）

### P0 —— 一行 CSS / 用户直接可感

| # | 修什么 | 依据 | 预期效果 |
|---|---|---|---|
| 1 | 全局加 `touch-action: manipulation` | WIG-04 **MUST**；实测 656/656 全 `auto` | 消除移动端双击缩放延迟（点击响应变快） |
| 2 | 汉堡 `.menu-toggle` 40→44px | WIG 触控 ≥44px；12/12 页一致 | 拇指命中率提升 |
| 3 | `.nav-links`（抽屉）加 `overscroll-behavior: contain` | WIG-07 **MUST**；实测 `auto` | 抽屉滚到底不再带动整页 |
| 4 | `.field input/select/textarea` 15px → **16px** | WIG-15 **MUST** | 修掉 iOS 聚焦自动放大（L437） |

### P1 —— 可访问性（键盘/无障碍用户）

| # | 修什么 | 依据 |
|---|---|---|
| 5 | 加 `:focus-visible` 焦点环；补 `.sr-input` 的 `:focus` 补偿 | WIG-09 **MUST** / WIG-14 |
| 6 | 加 `scroll-margin-top` | WIG-10 **MUST**（固定头部会遮住 FAQ / ilink 锚点） |
| 7 | 加 `@media (prefers-reduced-motion: reduce)` | WIG-08 **MUST** |

### P2 —— 细节与国际化

| # | 修什么 | 依据 |
|---|---|---|
| 8 | 品牌名加 `translate="no"` | WIG-16 **SHOULD**；8 语言站刚需 |
| 9 | `<meta name="theme-color">` | WIG-03 **SHOULD**（目前 0/1331，body 纯白） |
| 10 | 规格表数字加 `tabular-nums` | WIG-11 **MUST**（我们有大量规格表） |
| 11 | 491 张 img 补 `width`/`height` | WIG-19 **MUST**（防 CLS） |
| 12 | `a.c-link` 扩热区（padding/伪元素，视觉不变） | WIG 触控 ≥24px；现 17px |
| 13 | 加 `<link rel="preconnect">` | WIG-20 SHOULD；现 0/1331 |
| 14 | **`de/index.html` 320px 溢出 57px** 单独排查 | §3 |

⚠️ **修复纪律提醒**（沿用项目既有铁律）：
- 改 CSS **必须与 bump 资源版本号同一个 commit**（现为 `?v20260925c`），否则线上命中旧缓存、看起来「改了没生效」
- 改前先出**单页样本** → 独立验收 → 再铺开
- 触控热区类改动属**行为变更**，与「只修缺陷」的清理类改动**分开征询**

---

## 6. 与已有工作的关系

| 已有 | 关系 |
|---|---|
| `scan_overflow_20260925.cjs`（判据更严：页面溢出 + **真能横滚** + 改动点超父容器） | **不替换**。本轮 320 视口溢出的发现，建议把它的「单视口」扩成多视口 |
| 记忆中的「ilink 热区 18–19px，修法未做」 | 与本轮 `a.c-link` 17px **同族问题**，可一并处理 |
| 记忆中的「17 处移动端横向溢出（宽表格，`body{overflow-x:clip}`）」 | 本轮 390 视口 0/12 未复现 → 该问题**集中在含宽表格的页面**，代表页未覆盖，非结论冲突 |

---

## 附录：复现方式

```bash
P=/Users/mac-zlg/.workbuddy/binaries/python/versions/3.13.12/bin/python3
N=/Users/mac-zlg/.workbuddy/binaries/node/versions/22.12.0/bin/node
export NODE_PATH=/Users/mac-zlg/.workbuddy/binaries/node/workspace/node_modules
BASE=file:///Users/mac-zlg/WorkBuddy/2026-08-20-16-43-16

# 静态层（约 150s，务必后台跑 —— 全站脚本铁律）
$P i18n_build/audit_mobile_wig_20260927.py

# 浏览器层（file:// 协议，免起服务器）
$N i18n_build/audit_mobile_wig_browser_20260927.cjs --vp=390 --base=$BASE
$N i18n_build/audit_mobile_wig_browser_20260927.cjs --vp=320 --base=$BASE
```

⚠️ 教训：本地静态服务器**不能**用 `(python3 -m http.server &)` 起 —— 命令结束即被回收，
浏览器会全部 `ERR_CONNECTION_REFUSED`。用 `file://` 或「起服务+跑脚本+kill」写在同一条命令里。
