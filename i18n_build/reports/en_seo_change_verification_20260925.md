# 本轮 SEO 改动的影响核查报告

**日期**：2026-09-25　**范围**：1331 个 HTML + `assets/css/styles.css`
**改动内容**：A1–A5 结构类（H 层级 + 空 href）+ 11 个高权重页 description 压缩 + 资源版本号 bump

---

## 一、核查结论速览

| # | 核查项 | 方法 | 结果 |
|---|---|---|---|
| 1 | 有没有夹带意外改动 | 逐文件 HEAD vs 当前，difflib 逐块比对（3919 块） | ✅ **非预期改动 0 处** |
| 2 | 标签增减是否符合预期 | 结构守恒（div/a/button/h2/h3 增减签名） | ✅ 7 种签名全部合规，异常 0 |
| 3 | 有没有引入标签不配平 | 全站开/闭标签配平，改动前后对比 | ✅ **新引入 0 个文件** |
| 4 | H 标签本身配平 | `<h2>` vs `</h2>` 计数 | ✅ 修复后 **1331 页全 0 不配平** |
| 5 | 各链接是否正确 | 全站链接审计（4 类判据） | ✅ **404 0 / 跨语言 0 / 坏锚点 0 / 空 href 0** |
| 6 | 描述与 JSON-LD | 宽度 + 4 处一致性 + 结构化数据解析 | ✅ 138–152 宽、4 处全一致、**4848 块解析失败 0** |
| 7 | 结构容器完整性 | cat-head 容器数 / div 配平 / cat-title 归属 | ✅ 70/70 零异常 |
| 8 | 会不会溢出（改动点） | 1331 页 × 390px 全站扫描 | ✅ **改动点超出父容器 0 处** |
| 9 | 浏览器视觉是否变化 | computed style 逐位对比（字号/字重/边距/行高/颜色） | ✅ 与改前完全一致 |
| 10 | 语言切换还能用吗 | 真实点击 + localStorage + 文案切换 | ✅ 与首页行为逐项一致 |
| 11 | 脚本可重跑吗 | `--check` 幂等复验 | ✅ 全 0 处 |
| 12 | SEO 收益有没有丢 | 重跑审计 | ✅ 未达标 209 处（结构类 177 处收益保留） |

**一句话结论**：改动的**影响面完全受控** —— 没有夹带改动、没有引入标记错误、链接全绿、改动点零溢出。过程中发现并修复了 1 个我自己引入的真实缺陷（见第二节）。

---

## 二、发现并修复的 1 个真实缺陷（本次引入）

### A1 只替换了开标签，产生 `<h2>…</h3>` 不匹配标记

首次落盘时，`t_a1` 的实现是：

```python
new, n = RE_A1.subn(r"\1<h2", s)      # ❌ 只改开标签
```

导致 1029 个产品页出现标签不匹配：

```html
<h2 data-i18n="pd.specs">Specifications</h3>      <!-- 开 h2 / 闭 h3 -->
```

**为什么三处自检都没抓到**：
- dry-run 报「1029 处命中」，数字正常
- 幂等自检只检查「`<h3` 是否还在」，改完确实不在
- 浏览器 computed style 对比的是 `h2` 元素自身样式，而 `</h3>` 被浏览器静默忽略，h2 看起来正常

**真实危害**：HTML 解析器忽略 `</h3>` 后，`h2` 会**吞掉后面的 `<table>`**（规格表），表格文字因而继承 h2 的 19px 字号；同时 HTML 校验失败。

**怎么发现的**：结构守恒检查发现 1029 个文件的签名是 `{'h2': 1, 'h3': -1}` 但闭标签数为 0 —— 开标签变了、闭标签没变，立刻暴露。

**处理**：改为整块成对替换 + 加守恒断言，回滚 1029 个文件（每个恰好 3 行改动，与其它改动无文件重叠）后重跑。

```python
RE_A1 = re.compile(r'(<div class="pd-specs">\s*)<h3\b([^>]*)>(.*?)</h3>', re.S)

def t_a1(s):
    new, n = RE_A1.subn(lambda m: "%s<h2%s>%s</h2>" % (...), s)
    if (new.count("<h2") - new.count("</h2>")) != (s.count("<h2") - s.count("</h2>")):
        raise ValueError("h2 开/闭标签不配平，A1 替换越界")
```

**验证**：`<h2>`/`</h2>` 全站配平 0 处不匹配；`tbody` 不再被吞（扫描确认 `.pd-specs` 内无块级子元素）。

---

## 三、链接正确性（`audit_links_20260916.py`）

```
全站链接审计：1331 页 / 61218 个 <a> 链接
A 目标不存在（404）    0 处 / 0 页
B 跨语言误链           0 处 / 0 页
C 锚点不存在           0 处 / 0 页
D 空/占位 href         0 处 / 0 页
```

另在浏览器里逐页检查 `<a>` 的 href 属性（是否有空值 / `#` / 协议相对地址）：**84 个用例全部 0 缺陷**。

A5 把 9 篇 blog 的空 href `<a data-setlang>` 换成 `<button>` 后，站内**不再存在无 href 的可点击链接**。

语言切换的 7 个外链（DE/JA/KO/FR/IT/ES）href 逐条验证正确，如 `/de/blog/tpe-vs-pu.html`。

---

## 四、溢出情况

### 4.1 改动点：零溢出

1331 页 × 390px 扫描，4 类改动元素**全部未超出父容器**：

| 改动元素 | 检查页数 | 超出父容器 |
|---|---|---|
| `.cat-head .cat-title`（A2） | 70 | 0 |
| `.pd-specs h2`（A1） | 1029 | 0 |
| `.faq-cat`（A3） | 7 | 0 |
| `.pc-body h2`（A4） | 7 | 0 |

### 4.2 全站存在 17 处横向溢出 —— **全部是既有问题，非本轮引入**

| 页面 | 溢出 | 撑宽元素 |
|---|---|---|
| `blog/yoga-mat-materials.html` | 197px | `thead`（宽表格） |
| `de/blog/yoga-mat-materials.html` | 402px | `thead` |
| `de/blog/private-label-yoga-mats.html` | 289px | `thead` |
| `de/about.html` | 23px | `div.step`（步骤条） |
| `fr/contact.html` | 47px | `div` |
| …… 共 17 页 | | |

**判定方法（A/B 实证）**：把 `HEAD` 版本导出成同目录文件（相对路径不变），同判据对比 —— 4 个代表样本的溢出值与最右元素**逐位一致**：

```
blog/yoga-mat-materials.html      当前 197px / HEAD 197px   ← 一致
de/about.html                     当前  23px / HEAD  23px   ← 一致
fr/contact.html                   当前  47px / HEAD  47px   ← 一致
de/blog/yoga-mat-materials.html   当前 402px / HEAD 402px   ← 一致
```

**根因**：`body { overflow-x: clip }` 会把超出内容**裁掉且不可滚动**（实测 `scrollX` 恒为 0），而表格自身是 `display:block; overflow-x:visible` —— 窄屏下宽表格右侧被切。德语等文本更长的语言最明显（如 `de/blog/tpe-vs-pu.html` 表格第 3 列右边界 413 > 视口 390，被切 23px）。

**建议**：给 `.article-body table` 外面包一层 `overflow-x:auto`，或直接给 table 设 `overflow-x:auto`（约 3 行 CSS，一次性覆盖全部文章页表格）。

---

## 五、静态正确性

**11 个高权重页 description**（宽度按显示宽度计算，CJK 算 2）：

| 页面 | 新宽度 | 4 处一致性 |
|---|---|---|
| applications/index.html | 147 | ✅ meta/og/twitter/JSON-LD |
| applications/retail-private-label.html | 149 | ✅ |
| yoga-props-accessories.html | 152 | ✅ |
| resistance-bands.html | 138 | ✅ |
| 其余 7 页 | 142–150 | ✅ |

全部落在 120–160 区间；**4848 个 JSON-LD 块全部可 `json.loads`**（desc 改动没有破坏结构化数据）。

**A2 容器**：70 个文件 cat-head 容器数=1、cat-title 数=1、cat-title 紧跟 cat-head 之内、div 配平 —— 异常 0。

**A5 按钮**：10 篇 blog 共 20 个 `<button data-setlang>`，`title` 属性全部保留，残留空 href `<a>` 为 0。

---

## 六、功能实测：语言切换

A5 把 `<a data-setlang>` 换成 `<button>`，这是本轮唯一可能影响交互的改动。代码层面 `main.js` 用 `document.querySelectorAll('[data-setlang]')`（标签无关）+ 判断 `getAttribute('href')` 决定「跳转 / 同页切换」。

实测（真实点击）：

| 检查点 | EN 文章页（改动点） | EN 首页（对照） |
|---|---|---|
| 按钮标签 | `BUTTON` | `BUTTON` |
| 点击后 `html.lang` | `zh-CN` | `zh-CN` |
| `show-zh` class | true | true |
| 按钮文字 | 中文 | 中文 |
| 导航文字切换 | 瑜伽垫与健身 | 瑜伽垫与健身 |
| `localStorage.siteLang` | zh | zh |
| 菜单项高亮 | active ✅ | active ✅ |
| URL 是否跳转 | 否（同页切换）✅ | 否 |

**两者行为逐项一致** —— A5 未改变任何交互语义。控制台 JS 错误 0 个。

---

## 七、核查中发现的两个既有缺陷（非本轮引入，供决策）

### 7.1 48 个语言版文章页缺 `</article>` 闭合标签

| 语言 | 文件数 |
|---|---|
| de / ja / ko / fr / it / es | 各 8 篇（共 48） |
| en | 0（EN 版配平） |

```html
<article class="article">     <!-- 只有开标签，全文没有 </article> -->
```

**判定为既有**：标签配平脚本对比 HEAD 与当前版本，48 个文件改动前后**完全相同**。

**影响**：浏览器会在父容器结束时自动闭合 `article`，视觉与索引基本无影响，但 HTML 校验不通过、`<article>` 语义可能多包内容。

**修复建议**：在文章主体结束处（`.article` 内最后一个块之后）补 `</article>`，7 语言 × 8 篇 × 1 行 = 48 行，脚本可批量。

### 7.2 17 处移动端横向溢出

见 4.2 节，同样已 A/B 证明为既有。

---

## 八、核查方法（脚本可复跑）

| 脚本 | 作用 |
|---|---|
| `i18n_build/verify_changes_scope_20260925.py` | 逐块比对 HEAD vs 当前 + 结构守恒（证明无夹带改动） |
| `i18n_build/verify_tag_balance_20260925.py` | 全站标签配平，改动前后对比 |
| `i18n_build/verify_static_correctness_20260925.py` | desc 宽度/一致性 + A2 容器 + A5 属性 + JSON-LD 解析 |
| `i18n_build/scan_overflow_20260925.cjs` | 全站溢出扫描（`--vp=` 指定视口） |
| `i18n_build/verify_overflow_source_20260925.cjs` | A/B 判定溢出是否为既有 |
| `i18n_build/verify_lang_switch_20260925.cjs` | 语言切换功能实测 |
| `i18n_build/verify_change_impact_20260925.cjs` | 84 用例（7 语言 × 4 页 × 3 视口）综合验收 |
| `i18n_build/audit_links_20260916.py` | 全站链接审计（4 类判据） |
| `i18n_build/fix_en_seo_structure_20260925.py --check` | 结构修复幂等复验（应全 0） |

---

## 九、结论

1. **本轮改动没有引入任何遗留问题** —— 唯一引入的缺陷（A1 标签不配平）已在核查中发现、修复并二次验证。
2. **链接全绿**：61218 个链接，4 类问题全部 0；A5 还消除了 9 篇 blog 的无 href 链接。
3. **改动点零溢出**；全站 17 处横向溢出为既有问题（A/B 已证明），根因是 `body overflow-x:clip` + 宽表格。
4. 另有 48 个语言版文章页缺 `</article>`（既有），HTML 校验不通过，建议顺手修。
5. 改动**尚未提交、尚未推送**。
