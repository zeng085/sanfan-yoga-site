# 移动端 P0 修复落地报告（2026-09-27）

> 判据源：`vercel-labs/web-interface-guidelines`（★907）→ 归档 `i18n_build/reference/vercel_wig_AGENTS.md`（156 行 MUST/SHOULD/NEVER）
> 体检基线：`i18n_build/reports/mobile_wig_audit_20260927.md`（21 项 / ✅6 ❌8 ⚠️4 📊3）
> 本轮范围：**只做 P0 四条 + 实测暴露的第 5 条**，P1/P2 未动

---

## 1. 改了什么（5 处，全在 `assets/css/styles.css`）

| # | 位置 | 改动 | 对应条款 |
|---|---|---|---|
| ① | reset 区 `* {}` 之后（新增 10 行） | `a, button, [role=button], input, select, textarea, label, summary { touch-action: manipulation }` | WIG-04 **MUST** |
| ② | L444 `.field input/select/textarea` | `font-size: 15px` → **`16px`** | WIG-15 **MUST** |
| ③ | L512 `@media(max-width:1279px) .nav-links` | 加 `max-height: calc(100dvh - 68px)` + `overflow-y:auto` + `overscroll-behavior:contain` + `-webkit-overflow-scrolling:touch` | WIG-07 **MUST** |
| ④ | L534 同媒体查询 `.menu-toggle` / `.nav-brand` / `.lang-current` | `40px` → **`44px`** | WIG 触控热区 **MUST** |
| ⑤ | L643 `@media(max-width:920px)` | `.nav-links { max-height: calc(100dvh - 68px - 54px) }` | ③ 的必要补完（见 §3） |

规模：`+36 / −7` 行（含注释），**单文件**；CSS 括号 **642/642 平衡**、`@media` 仍 **30 个**（未新增）。

---

## 2. A/B 实测（改前 vs 改后，浏览器层）

方法：`verify_p0_fixes_20260927.cjs`，6 个代表页 × 3 个视口（390×844 / 320×568 / 844×390）。

| 指标 | 改前 | 改后 | 判定 |
|---|---|---|---|
| 可点元素 `touch-action` | `{auto: 2001}` | `{manipulation: 2001}` | ✅ 100% 覆盖 |
| 汉堡按钮 | `40x40`（6/6 页） | **`44x44`**（6/6 页） | ✅ 达 WIG 44px |
| 表单 `input` 字号 | `15px` | **`16px`** | ✅ 不再触发 iOS 聚焦放大 |
| 抽屉 `max-height` | `none` | **`322px`**（390 高）/ **`268px`**（≤920 宽） | ✅ |
| 抽屉 `overflow-y` | `visible` | **`auto`** | ✅ |
| 抽屉 `overscroll-behavior` | `auto` | **`contain`** | ✅ |
| 抽屉内滚动 600px → 页面 `scrollTop` | **0 → 600**（穿透） | **0 → 0**（不穿透） | ✅ |
| 横屏 844×390 滚到底·最后一项 bottom | **461**（纹丝不动） | **319** | ✅ |
| header 高度 | 69px | **69px** | ✅ 无回归 |
| 横向溢出（3 视口 × 6 页） | 全 0 | **全 0** | ✅ 无回归 |

### ★ 核心证据（截图可证）

`E-bottom_before.png` 与 `C-landscape_before.png` **字节完全相同** —— 因为改前版本 `scrollTop = 9999` **完全无效，抽屉根本滚不动**（`overflow-y: visible`）。
改后同一操作滚到底，**完整显示到最后一项 `Contact`**。

对比图：`i18n_build/reports/p0_fixes_ab_20260927.png`（4 组左右对照）

---

## 3. ⚠️ 实测暴露的第 5 条：`.cbar` 会盖住抽屉底部

**这不是原计划的一部分，是验证③时发现的。**

- 现象：给抽屉加 `max-height` 后确实能滚了，但滚到底最后一项仍被遮 → 等于没修好
- 根因：`.cbar`（浮动联系条）`position:fixed`、**`z-index: 60` > 抽屉 `49`**，≤920px 时变**底部通栏 54px**
- ⭐ `.cbar` 是 **JS 注入**的 —— `grep 'class="cbar"' *.html` **0 命中**（同项目铁律：源码审计归零 ≠ DOM 干净）
- 实测：改后横屏最后一项 bottom=373、`.cbar` top=336 → **重叠 37px**
- 修法：≤920px 时抽屉再减 54px → 改后最后一项 bottom=**319** < cbar top=**336** ✅
- ⚠️ 921~1279px **不适用**：那区间 `.cbar` 仍是右下角竖排浮动按钮，不横跨全宽

---

## 4. 验证方法（可复跑）

```bash
# 改前基线 / 改后对比（会打印 §2 全表）
node i18n_build/verify_p0_fixes_20260927.cjs --tag=before   # 用 git show HEAD:版本
node i18n_build/verify_p0_fixes_20260927.cjs --tag=after

# 抽屉真实滚动行为（含 header sticky 判定、穿透实测）
node i18n_build/probe_drawer_behavior_20260927.cjs --vp=844 --h=390

# A/B 截图（路由拦截喂 HEAD 版 CSS，不改任何文件）
node i18n_build/ab_p0_screenshots_20260927.cjs
```

环境：`NODE_PATH=/Users/mac-zlg/.workbuddy/binaries/node/workspace/node_modules`，
node 用 `/Users/mac-zlg/.workbuddy/binaries/node/versions/22.12.0/bin/node`。

---

## 5. 范围核查

| 项 | 结果 |
|---|---|
| 改动文件类型 | `styles.css` ×1 + `*.html` ×1044（**仅版本号字符串**） |
| bump 版本号 | `20260925c` → **`20260927a`**（1331/1355 文件，2662 处引用） |
| CSS 语法 | 括号 642/642 平衡；浏览器 computed 值全部生效 |
| 横向溢出 | 3 视口 × 6 页全 0（改前也全 0，无回归） |
| header 高度 | 69px 不变（44 < 68，`min-height` 未撑高） |

⚠️ **bump 必须与 CSS 改动同一个 commit** —— 这是踩过的坑（`a7cc81bd` 扩了选择器却漏 bump，线上 URL 仍是旧号，用户命中缓存旧 CSS，看着「改了没变」）。

---

## 6. 未做（P1 / P2，待定）

### P1（MUST 但需设计决策）
| 条款 | 现状 | 为什么没顺手做 |
|---|---|---|
| WIG-09 `:focus-visible` 焦点环 | 0 处 | 需定品牌色焦点环样式，属视觉设计决策 |
| WIG-10 `scroll-margin-top` | 0 处 | 固定头部 68px，锚点跳转会被遮；需确认影响哪些锚点 |
| WIG-08 `prefers-reduced-motion` | 0 处 | 站内有 `scroll-behavior:smooth` 与多处 `transition`，需逐一梳理 |
| WIG-06 `env(safe-area-inset-*)` | 0 处 | 刘海屏适配：抽屉/`.cbar`/hero 的左右内边距 |
| WIG-11 `tabular-nums` | 0 处 | 仅价格/参数表需要，属局部优化 |
| WIG-14 `.sr-input{outline:0}` | 搜索框聚焦无可视指示 | 同上，属焦点环设计 |

### P2（SHOULD）
- WIG-05 `-webkit-tap-highlight-color`（现为 Chrome 默认灰块）
- WIG-12 `text-wrap: balance`（标题断行更均衡）
- WIG-03 `theme-color`（0/1331 页）
- WIG-16 品牌名 `translate="no"`（**8 语言站刚需**，机翻会把 SANFAN 当普通词）
- WIG-18 `&nbsp;`（仅 11/1331 页有，品牌名与数字单位未防断行）
- WIG-19 491/19,109 张 img 缺 `width+height`
- WIG-20 `preconnect` 0/1331 页

### 遗留既有问题（非本轮引入，A/B 已证）
- **320px 下 `de/index.html` 溢出 57px**（德语复合词）；本项目溢出扫描默认只测 390 → **以后必须同时跑 320 与 390**
- `.nav-links` 与 `.cbar` 的 `z-index` 关系（60 > 49）未改；本轮靠「让位」解决遮挡，未动层级

---

## 7. 工具坑（本轮新增 2 条）

1. **`grep -r` 会扫 `.git`（338MB）→ 被 SIGTERM**。查版本号残留应走脚本自身 dry-run，或显式排除 `.git`。
2. **`bump_assets_ver.py` 跑不完整会静默半途**：首次前台执行被超时杀掉，写盘停在 2088/2662（**且脚本无「已完成」标记可查**）。
   → 判定补完与否只能用 **`--dry-run` 复看版本号分布**：`[('20260927a', N)]` 单一项才算完。
   → 全站脚本一律后台跑（项目铁律）。
