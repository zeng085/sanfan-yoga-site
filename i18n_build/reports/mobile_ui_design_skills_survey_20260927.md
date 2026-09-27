# 移动端 UI 界面设计方案 —— GitHub 技能调研

日期：2026-09-27
结论：**有一个权威源值得接（Vercel 官方，零依赖）；大批热门技能对本项目不适用。**
站点文件：**0 改动**（本轮纯调研）

---

## 0. 先明确「适用」的判据

本项目是 **纯静态 HTML/CSS 多语言站**（1331 页 / 8 语言 / 1279px 汉堡断点 / 无构建链 /
无框架 / 无 Tailwind）。这是筛选的第一道闸门：

| 闸门 | 判据 | 淘汰理由 |
|---|---|---|
| ① 框架假设 | 是否假定 React / Vue / Tailwind / shadcn / Astro / Next.js | 我们一条都不用 → 装进来只能读着玩 |
| ② 交付物 | 是「App 屏幕设计稿」还是「Web 页面规范」 | 我们做网站，不是原生 App |
| ③ 是否可执行 | 只给原则，还是给可跑的脚本 | 原则类我们能自己写；脚本类才有增量 |
| ④ 是否权威 / 会过期 | 官方源 or 个人转述；运行时 fetch or 静态快照 | 个人转述 + 快照 = 下一个坑 |

---

## 1. 本机已有盘点（先说省事的部分）

### 1.1 已装的 `ardot-ui-design`（即 `@skill:ardot-design-assistant`）—— 覆盖的是 App，不是响应式 Web

路径：`~/.workbuddy/plugins/cache/workbuddy-builtin/skill-ardot-ui-design/<ver>/references/`

| 文件 | 行数 | 内容 |
|---|---|---|
| `guidelines-mobile-app.md` | 116 | **「MOBILE APP SCREEN COMPOSITION」原生 App 屏幕构图** |
| `guidelines-landing-page.md` | 266 | 官网 / 落地页 |
| `guidelines-web-app.md` | 211 | Web App / 设计系统（默认） |
| `guidelines-table.md` | 26 | 表格 |

⚠️ **关键落差**：它的「移动端」= **App 界面**（62px 状态栏、SF Pro 字体、底部 Tab Bar、FAB），
**不是**「网站在手机上的响应式表现」。逐字查 `guidelines-web-app.md` 里的响应式内容：

```
144:# 12. Responsiveness Philosophy
146:Hierarchy must survive all breakpoints.
148:Mobile:
```

→ **只有 3 行**。所以本机在「移动端 Web」这个维度上**几乎是空白**：没有断点体系、
没有 fluid typography、没有触控热区、没有横向溢出治理、没有响应式表格。

### 1.2 本机躺着但**未启用**的设计插件

| 插件 | 内含技能 | 对本项目 |
|---|---|---|
| `frontend-design` | 单 SKILL.md | 可看 |
| `frontend-design-pro` | design-wizard / color-curator / typography-selector / **moodboard-creator** / **inspiration-analyzer** / trend-researcher | 偏「找视觉方向」，非响应式 |
| `frontend-mobile-development` | react-native-architecture / react-state-management / nextjs-app-router-patterns / **tailwind-design-system** | ⛔ **全框架**（RN/Next/Tailwind），不适用 |
| `canvas-design` | — | 非 Web |
| `skill-ardot-design-core` / `-design-to-code` / `-poster` / `-slides` | — | Ardot 画布系，另用 |

---

## 2. GitHub 候选择优（全部经 API 核实存在，非聚合站编造）

⭐⭐ **关键区分**：搜「mobile UI design」出来的**高星仓库几乎全是原生 App**。这是本次最大的陷阱。

### A 组 —— ⭐ 唯一强推：Vercel 官方 Web Interface Guidelines

| 项 | 值 |
|---|---|
| 仓库 | **`vercel-labs/web-interface-guidelines`** |
| 星 / 更新 / 体积 | **★907** / 2026-08-18 / **116KB** |
| 文件 | `AGENTS.md`（agent 入口）+ `command.md`（191 行规则）+ `README.md` + `install.sh` |
| 依赖 | **零**（纯 Markdown 规范） |
| 新鲜度 | **运行时 fetch**，非快照 → 永不过期 |

`AGENTS.md` 通篇用 **MUST / SHOULD / NEVER** 写，移动端专项条款**正中我们的痛点**：

```
### Targets & Input
- MUST:   Hit target ≥24px (mobile ≥44px); if visual <24px, expand hit area
- MUST:   Mobile <input> font-size ≥16px to prevent iOS zoom
- NEVER:  Disable browser zoom (user-scalable=no, maximum-scale=1)
- MUST:   touch-action: manipulation to prevent double-tap zoom
- SHOULD: Set -webkit-tap-highlight-color to match design

### Touch & Interaction
- Full-bleed layouts need env(safe-area-inset-*) for notches
- Avoid unwanted scrollbars: overflow-x-hidden on containers, fix content overflow
- color-scheme: dark on <html> for dark themes
```

⭐ **对照本项目已知缺陷，逐条命中**：
- 「热区 18–19px」→ 违反 `mobile ≥44px`
- 「17 处移动端横向溢出」→ 正是 `Avoid unwanted scrollbars / fix content overflow`
- 站上若用了 `user-scalable=no` → 违反 NEVER（**待查**）

> 附：`lotfb86/web-design-skills` 的 `03-web-design-guidelines/SKILL.md` **就是它的包装**
> （文件 meta 写着 `author: vercel`）——但那是 ★9 的转载仓，**应直接指原始源**。

### B 组 —— ✅ 可参考，但不必装

| 仓库 / 技能 | 星 | 体积 | 判断 |
|---|---|---|---|
| `ancoleman/ai-design-components` → `skills/designing-layouts` | ★521 | 全仓 8.3MB / 970 md | 纯 CSS 框架无关，讲 Grid/Flexbox/container queries/token。**偏「布局架构」**，移动端具体问题（触控/溢出）不如上面细 |
| `lotfb86/web-design-skills` → `02-responsive-design` | ★9 | 353 行 | 内容**最对口**（mobile-first 强制规则 / 断点 / srcset / clamp / 容器查询 / **触控 44px** / **响应式表格→卡片** / Hard Rules 表），但**星低、作者不明**，且混有 Astro `<Image>`、Tailwind 断点假设 |

### C 组 —— ⛔ 不对口（原生 App），别装

| 仓库 | 星 | 为什么不用 |
|---|---|---|
| `plugin87/ux-ui-agent-skills` | **★1478** | 251 个 md 的**React 设计系统全家桶**（design-tokens / figma-integration / token-build / migrate-design-system）。重，且我们无组件库可迁移 |
| `ceorkm/mobile-app-ui-design` | ★365 | 明写 "React Native / Flutter / SwiftUI style interfaces"，讲 onboarding / TabBar |
| `awesome-skills/mobile-app-design` | ★78 | iOS HIG / Android 平台规范，纯 App |
| `szilu/ux-designer-skill` ★68 / `phazurlabs/sumi` ★50 / `apexscaleai/claude-ui-design-system` ★27 | — | 同类（sumi 43 skills；apexscale 明写 React Native & Next.js） |
| `bergside/awesome-design-skills` | ★2942 | **TypeUI 商业产品的引流清单**（113 种视觉风格 DESIGN.md，如 Glassmorphism），是「审美风格」不是「移动端布局规范」 |
| `rohitg00/awesome-claude-design` ★1109 / `helloianneo/awesome-claude-code-skills` ★477 | — | 清单仓，逐条查后**无移动端/响应式专项条目** |

---

## 3. 意外收获：一个可搬运的检测维度

`plugin87/ux-ui-agent-skills` 里没有移动端技能，但有 `scripts/verify_responsive.mjs`
（Playwright 横向溢出**门禁**）。**项目已有同类**（`i18n_build/scan_overflow_20260925.cjs`），
逐项对比后发现**两边判据互补**：

| 维度 | 我方 `scan_overflow_20260925.cjs` | 它方 `verify_responsive.mjs` |
|---|---|---|
| 视口 | **单值** `--vp=390`（可传一个） | **多值** `--widths=280,320,414` |
| 字号缩放 | ❌ | ✅ **`--scale=1.25`** |
| 定位肇事元素 | ❌（只列 4 个关注点） | ✅ 返回 `tagName.className` |
| 判据严谨度 | ✅ **页面溢出 + 真能横向滚动 + 改动点超父容器**（收紧过，避免误报） | 仅 `scrollWidth - clientWidth > 1` |

⭐ **`--scale` 的洞察值得照搬**，脚本注释里是实战教训：

> macOS Chrome 与 Linux Chromium 上**同一个 label 宽 2px**，就能让页面在 280px 溢出。
> 并且真实用户会把默认字号调大。**「只在恰好 16px 时刚好放得下」= 靠运气放得下。**

→ 结论：**不要把我们的脚本换掉**（判据更严），只**补两个维度**：多宽度 + `--scale`。

---

## 4. 建议（按性价比排序）

**做法一（推荐，零成本）**：把 Vercel `AGENTS.md` 作为**审查基准**接进来
- 不装技能、不装依赖，运行时从 `raw.githubusercontent.com/vercel-labs/web-interface-guidelines` 取
- 先对**移动端专项条款**跑一遍现状体检，出「违反清单 + file:line」
- 预计立刻能确认三件事：视口 meta 是否禁缩放、热区是否 <44px、`touch-action` 是否缺

**做法二（小改动）**：给 `scan_overflow_20260925.cjs` 补 `--widths=280,320,414` 与 `--scale=1.25`
- 保留我们更严的判据，只扩检测面

**做法三（不建议）**：装 C 组任何技能 —— 我们不做原生 App，装完只有噪音。

**做法四（可选，见 §5）**：借 `google-labs-code/design.md` 的官方格式，为本站写一份
**属于三梵的 DESIGN.md**（把现有 29 个 `--var` + 断点收敛 + 组件形态固化成契约），
初稿可用 `dembrandt/dembrandt` 从本站自动提取。
⚠️ **不要**下载 VoltAgent 里任何品牌的 DESIGN.md 直接用（配色/调性完全不搭）。

---

## 5. 追加调研：`awesome-design-md` 系（DESIGN.md 格式）

### 5.1 仓库真实性与体检

| 仓库 | 星 / fork | 许可 | 建 / 最后 push | 是什么 |
|---|---|---|---|---|
| **`VoltAgent/awesome-design-md`** | **118,268 / 13,230**（比 8.9，正常） | MIT | 2026-03-31 / 2026-09-21 | 153 个文件的**品牌 DESIGN.md 模板库**（`design-md/<品牌>/DESIGN.md`） |
| **`google-labs-code/design.md`** | 28,122 / 2,283 | Apache-2.0 | 2026-04-10 / 2026-09-14 | ⭐ **DESIGN.md 格式的源头规范**（`docs/spec.md` 378 行 / 15,313 字符） |
| `kzhrknt/awesome-design-md-jp` | 980 / 74 | MIT | 2026-04-06 / 2026-09-27 | 日语 DESIGN.md 集，**扩展 Stitch 格式加 CJK 排版** |
| `dembrandt/dembrandt` | 3,575 / 319 | MIT | 2025-11-22 / 2026-09-26 | **一条命令从任意网站提取设计系统为 tokens** |
| `HU-UH/awesome-design-md` ★433 / `fchangjun/awesome-design-md-cn` ★144 | — | — | — | 中文搬运版 |
| `bergside/design-md-chrome` ★2914 / `bergside/typeui` ★1984 | — | — | — | TypeUI 系的 Chrome 扩展 + 商业产品 |

⚠️ **11.8 万星不是刷的**：fork 13,230、watch 461，比率在正常区间；MIT 许可，内容可自由使用。
⚠️ 但注意旁边那个 **`Meliwat/awesome-design-md-pre-paywall`**（★49，描述："Reverted snapshot …
**before getdesign.md links were introduced**"）+ 仓库内 `.github/FUNDING.yml` 与
`ISSUE_TEMPLATE/design-md-request.yml` → 该项目**后期引入了 `getdesign.md` 引流**。

### 5.2 ⛔ 自认一处判断错误（本轮我自己犯的）

我按目录树扫描，看到 `mobile/responsive` **文件名命中为 0**，就下了「DESIGN.md 与移动端无关」的结论。

**打开 `design-md/clay/DESIGN.md` 实测（25,531 字符），里面明确有**：

```markdown
## Responsive Behavior
### Breakpoints
| Mobile | < 768px | Hamburger nav; hero h1 72→36px; hero-illustration-card
                     stacks below; feature grids 1-up; pricing 1-up |
### Touch Targets
- Feature card grids: 3-up at desktop, 2-up at tablet, 1-up at mobile.
```

→ **DESIGN.md 是含响应式与触控规范的**。这是「**别靠目录名/文件名判断内容**」的同型错误
（项目里已有一条同教训：「页面类型别靠目录名判，`pilates/` 是产品页」）。

### 5.3 DESIGN.md 到底是什么（据 Google `docs/spec.md`）

- **两段式**：`---` 包裹的 **YAML frontmatter（机器可读 token）** + **markdown body（人类可读设计理由）**
- token 组：`colors` / `typography` / `rounded` / `spacing` / `components`
- 采用 **W3C Design Token JSON spec** 概念，支持 `{path.to.token}` 跨引用
- 可互相转换：`tokens.json` / Figma variables / Tailwind theme configs
- ⚠️ 规范自身标 `version: alpha`（尚未稳定）

### 5.4 结论：能用，但**不是**「下载一个抄」

- ❌ `clay` 是「黏土动画风的 GTM 数据平台」，配色 hot pink / 深青 / 薰衣草
  —— 与 B2B 工业垫厂**完全不搭**。抄它等于自伤。
- ✅ 正确用法是**借格式、写自己的**：以 `google-labs-code/design.md` 的官方格式，
  为 fjsanfan.com 写一份属于三梵的 DESIGN.md。
- ⭐ 更省事的路径：用 **`dembrandt/dembrandt`** 从**本站**自动提取 tokens，得到初稿，再人工收敛。

### 5.5 顺手把本站 CSS 量了一遍（缺口很具体）

`assets/css/styles.css`（`index.html` 引用 `?v20260925c`）实测：

| 项 | 实测值 |
|---|---|
| 规模 | **1,310 行 / 69,257 字节** |
| CSS 自定义属性 `--var` | **29 个** |
| `@media` 总数 | **30 个** |
| `min-width` 断点 | **只有 1 个**（921px） |
| `max-width` 断点 | ⚠️ **18 种不同值**（640×6、1279×3、920×3、980×3、560×2、420/480/520/720/820/860/1000/1080/1100/1360/1480/1580 各 1） |
| `touch-action` | **0** |
| `env(safe-area-inset-*)` | **0** |
| `user-scalable` | **0**（✅ 好事：没有禁用缩放） |
| `-webkit-tap-highlight-color` | **0** |

→ 两个结论：
1. **断点杂乱**（18 种不同的 `max-width`）= 典型的「没有断点体系」症状；
   对照 §2-A 的 Vercel 断点口径（640/768/1024/1280/1536），偏差很大。
2. Vercel WIG 中 4 条移动端 MUST/NEVER，**我们没有一条落地**
   （`touch-action: manipulation` 缺 / `safe-area` 缺 / `-webkit-tap-highlight` 缺）。

### 5.6 ⭐⭐ 三层结构（本题的最终答案）

DESIGN.md 与 Vercel WIG **不是二选一，而是互补的三层**：

| 层 | 该用什么 | 干什么 | 依赖 |
|---|---|---|---|
| **判据**（该长什么样） | **Vercel WIG**（★907） | MUST/SHOULD/NEVER 清单：mobile ≥44px 热区、输入框 ≥16px、`touch-action` | 零 |
| **契约**（本站长什么样） | **`google-labs-code/design.md` 格式** | 把 29 个 var + 断点 + 组件写成一份契约，供后续页面一致 | 零 |
| **检测**（哪里不合规） | 已有 `scan_overflow_20260925.cjs` | 找溢出 | 需 Playwright |

---

## 附录：本轮核实方法（可复用）

```
1. gh 未安装 → 改 curl + GitHub REST API（token: ~/.workbuddy/secrets/gh_pat）
2. 仓库体检：   /repos/{r}                     → 星数 / pushed_at / size
3. 目录树：     /repos/{r}/git/trees/HEAD?recursive=1
4. 读原文：     raw.githubusercontent.com/{r}/HEAD/{path}  ← 必读，别看搜索摘要
5. 淘汰链：     框架假设 → 交付物形态 → 可否执行 → 权威性/新鲜度
```

⚠️ 教训：**搜索引擎摘要会编造细节**。本轮搜索摘要把 `lotfb86/web-design-skills`
归给「Jesse Anglen at Ruh AI」，但该仓库 README 并无此署名；摘要里的
`skillselion.com` / `infrasity.com` 均为第三方聚合站，**数据只能当线索，必须回源核实**。
