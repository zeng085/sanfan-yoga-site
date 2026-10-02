# 三梵独立站 fjsanfan.com —— 规则细节全量版（归档 2026-09-27）

> 本文件是 `.workbuddy/memory/MEMORY.md` 的**细节展开版**。MEMORY.md 因注入体积限制已精简为
> 「高频必读 + 当前状态」，长期规则与历史结论全部归档在这里。
> **需要细节判据 / 具体脚本名 / 历史批次结论时读本文件。**

---

## 概况
- 仓库 zeng085/sanfan-yoga-site（**private**）→ Vercel；B2B OEM/ODM 瑜伽垫/健身器材厂站；1331 页
- EN 主站 + de/ja/ko/fr/it/es 子目录 + 中文同页切换（无 /zh/ URL）；sitemap 1330 条
- ⚠️ `.gitignore` 排除 `i18n_build/.deepl_key*`、`i18n_build/data/`（16M 报价表机密）
- ⭐ 全站脚本**一律后台跑**
- ⭐ 资源版本号演化：`20260925c` → P0 `20260927a` → P1 `20260927b`（**改 CSS/JS 必 bump，且与改动同一个 commit**）
  写法 `?v20260927b`（**没有等号**）

## 导航（2026-09-16 定稿，勿翻案）
- ⭐ `.container.nav` **不能锁 `--maxw`**（放不下会换行挤到 logo 上）；**汉堡断点 1279px**
  是实测标定（最宽的 es 需 1436），断点内必须还原 `nowrap/flex:none`
- ⭐ 下拉三件套：`::before` 补 12px 死缝 / `MEGA_CLOSE_DELAY=320ms` / 关闭路径 7 条
- ⭐ **目录索引 URL 一律用 `/x/`**，`/x/index.html` 会被 301

## 关键词口径：EVA≡TPE（2026-09-24，两轮才收口）
- ⚠️ 「EVA 独立板块」整版方案**已否决、全量回退**。真实意图只有一条：**行业口语里「EVA 瑜伽垫」
  就是同类 TPE 垫**，搜 EVA 落到 TPE 垫页。**不建 URL、不动页脚/实体层/sitemap**
- ✅ 落地：`tpe-yoga-mats.html`×7 加小节 + FAQPage + 描述补 EVA；`materials.html`×7 EVA 行改
  「EVA 名义下的垫按 TPE 供货」。**已推送（d0c4075213）**
- ⚠️ 措辞**不能**写「EVA 与 TPE 同一种材料」→ 只讲**叫法混用 + 按 TPE 报样 + EVA 专线做配件**

---

## 判据铁律（全量）

### 通用方法论
1. ⭐ **长度判据先问「对 CJK / 对译文成立吗」**：meta 按**显示宽度**（CJK×2，title 60 / desc 155）；
   「重复」须**按语言分组**
2. ⭐ **中英字符比中位 0.353（0.30–0.44）**，<0.25=残块 FAIL；比字数前先标定
3. ⭐ **EN 页的 `|`/`—` 常写成 HTML 实体**（`&#124;`）→ 只认字面会静默漏掉整个 EN 站
4. ⭐ **同一文件的多个 Edit 不能并行**：并行时只有最后一个落盘，另几处静默丢失
5. ⭐ **「同串同步」先数清有几份**：HTML 转义形态不同就不算同串 —— meta 与 JSON-LD 的
   description 天然是**两份串**（`&amp;` vs `&`）
6. ⭐ 替换式脚本：落盘前 `assert 'href="href="' not in out`；**先摘旧块再重插**；
   清洗规则**迭代到不动点**，错则先回滚再重跑
7. ⭐ **回退断言分插入/替换**：替换型必须 `replace(new, old, 1)==原文`；
   插入型要与摘块正则**严格互逆**（摘 `\n[ \t]*` 就得复用原位换行，否则每跑一次多一空行）
8. ⭐ **审计脚本先自审**：`url_path()` 漏映射裸 `index.html` → 首页误报；`noindex` 页不要求 hreflang
9. ⭐ **新内容别放进 `<!-- orgref:v1 -->` 标记区间**：`add_org_sameas_20260924.py` 会剥离整个
   区间再重建，区间内内容**静默丢失**；站内 328 个 FAQPage 都在标记之前
10. ⭐⭐ **源码审计归零 ≠ DOM 干净**：JS `createElement`/改属性产生的缺陷
    （`main.js:1140` 的 `menuItem.href='#'`、**JS 注入的 `.cbar`**、全 JS 的站内搜索）**不在 HTML 里**
    → 必须补浏览器级探针 `querySelectorAll('a[href="#"], a:not([href])')`，且**按视口分别查**
11. ⭐⭐ **「该改成什么」先搜同处现成写法，别推理**：`product.html` 的 wa 按钮 → 看
    `products/*.html` 的 `#pd-wa-en` 与 `build_batch1.py` 模板；`menuItem.href` → 看**同文件**
    `main.js:1058`。搜到即用，天然与全站一致
12. ⭐⭐ **说「惯例」前先量化，且只在同类元素内成立**：WhatsApp 外链里 `c-link`（文字链）
    1317 处**带** `target="_blank"`，而同类按钮 `btn btn-ghost` **1029 处全不带** → 跨类对比会得出
    相反结论。清理类改动**只修缺陷**，行为变更单列征询
13. ⭐⭐ **bump 版本号必须与改 CSS/JS 在同一个 commit**：`a7cc81bd` 扩了 3 处选择器却漏 bump
    → 线上 URL 仍是 `?v20260925b`，**用户命中缓存旧 CSS，新样式完全不生效**（HTML 改了但看着没变）。
    补救 = 单独一个 `chore(assets)` commit + 下次推送带上
14. ⭐⭐ **本地 `origin/main` 是陈旧缓存，不能用来判断「要推什么」**（见下方推送节）
15. ⭐⭐ **改 HTML 标签必须成对**：只 `subn` 开标签 → `<h2>…</h3>` 不匹配，
    **dry-run / 幂等自检 / computed style 三处都抓不到**；浏览器忽略 `</h3>` 后 h2 会
    **吞掉后面的 `<table>`**。落盘后必须断言 `<X` 与 `</X>` 的增减一致 + 看「结构守恒签名」
16. ⭐⭐ **「既有问题」必须 A/B 实证**：把 HEAD 版导出到**同目录**新文件（相对路径不变），
    同判据对比 → 一致才是既有。禁止用「我没改这里」推断
17. ⭐⭐ **CSS 是单文件共享 → 做不到「单页样本」**。替代三件套：① `--dry-run` 看影响面；
    ② 多页 × 多视口实测（**必含 844×390 横屏**）；③ A/B 截图用**路由拦截喂 `git show HEAD:` 版文件**（零文件改动）
18. ⭐⭐ **浮层加 `overscroll-behavior` 前先确认它自己会滚**：`overflow:visible` 的浮层加了无效
    （滚的是页面，实测穿透 600px）。必须**同时**给 `max-height + overflow-y:auto`。
    且查 `.site-header` 是否 `sticky` —— 是的话浮层 `absolute` 跟着固定 → **页面滚到底也够不着溢出部分**
19. ⭐⭐ **改后核查三件套**（用户问「有没有影响」时必跑）：
    `verify_changes_scope_*.py`（difflib 逐块证「无夹带」）/ `verify_tag_balance_*.py` /
    `scan_overflow_*.cjs --vp=390`（判「改动点是否溢出」，非「页面有无超宽元素」）
    ⭐ 更直接的等价核查：`git diff -U0 -- '*.html' | grep -E '^[+-][^+-]'` 计数 —— **`+`/− 行数必须配对**
20. ⭐ 工具坑：**`grep -r` 会扫 `.git`（338MB）→ SIGTERM**（查版本号残留用脚本 `--dry-run`）；
    **`bump_assets_ver.py` 被超时杀掉会静默停半途**（无「已完成」标记）→ 判定补完
    **只能看 `--dry-run` 分布是否单一项**
21. ⭐⭐ **推送前闸二（内容级扫描）不要自己逐文件读**：1370 文件逐个 open 会被 SIGTERM（exit 137）
    → 改用 `git grep -n -I -E '<形态正则>' HEAD -- .`（在仓库对象上跑，秒级完成）；
    另注意 `git grep … | head` 的 `$?` 是 **head 的退出码**，不能当判据
22. ⭐ **清理类判据收紧到「引号内侧只有术语本身」**：`„TPE-Matte, violett, 6 mm“` / `«MOQ 100»` /
    `“EVA yoga mat”` / `"ROHS"` 都是**合法引用**，宽判据（「术语附近有引号」）会误杀。
    全站实测：105 处该清 / 27+231 处**不动**
23. ⭐ **「某语言独有」的形态先跨语言对照再定性**：「德语给标准名加引号」看着合语法，
    但 7 语言只有 de 有 → 机翻产物。**一致性才是口径**，不是语法
24. ⭐ **该不该换标签 → 先搜 CSS 有没有为「目标形态」准备好的选择器**：`site.css` 里
    `.article h1, .article .lang-zh h2.post-title` 并列 → 中文块本就用 h2，是 HTML 误用。
    改后验 computed `font-size` 两态一致（40px/40px）
25. ⭐⭐ **标题跳级：先 A/B，再全站量化，别急着改**。全站实测 h2→h4 有 1166/1364 页（85%）
    （产品卡是 h4、网格节自身无标题）、h2→h5 1332 页 → 属**既有形态**，审计标准也**没有**
    跳级幅度规则（只有 B1 h1 / B2 泛化 h1 / B3 h2<2 / B4 反序 / B5 面包屑）

### Playwright
- ⭐ **别用 `networkidle`**（拦 GA + `domcontentloaded`）；中文态须 `localStorage.siteLang='zh'`
  后重载（**localStorage + cookie 双通道都设**）；折叠 `<details>` 展开前 `innerText` 为空；
  `evaluate` 必须**传函数引用+参数**（`f, x`）—— 写成 `f(x)` 会在 Node 端求值 →
  `localStorage is not defined`
- ⭐ 热区测法用 `elementFromPoint` 逐点扫（±34px 窗口，窗口窄会截断结果）；`rect.height` 只作参考
- ⚠️ 探测三陷阱：`html{scroll-behavior:smooth}` 让程序化滚动**异步** → 同步读 rect 拿到旧位置、
  逐点扫描**静默返回 0**；块内含 `<details>` 会骗过「.faq-list」特征判据 → **改用相对位置取块**

---

## 推送（细节见技能 `github-api-push`）
改 CSS/JS 先 `bump_assets_ver.py` → 干净 commit →
`GH_PAT=$(cat ~/.workbuddy/secrets/gh_pat) python3 push_api_v3.py zeng085/sanfan-yoga-site <abs_repo> --auto`
（顺序不能换）。diff 带 `--no-renames`；**不要 `reset --soft`**（v2 残留，照做=死局）

### ⭐ 推送起点判定三步法
1. 远程 HEAD 的 **message 匹配本地 commit**（sha 谱系不同，不能直接比）
2. **确定性验证**：远程 tree `?recursive=1` 与 `git ls-tree -r <起点>` **逐 blob sha 比对**，
   三类差异（仅远程/仅本地/内容不同）**必须全 0**
3. 推送清单用「远程树 vs 本地 HEAD 树」生成，与 `git diff --name-only --no-renames <起点>..HEAD`
   **交叉验证**（两法一致才推）
- 脚本：`i18n_build/verify_push_scope_20260927.py` ← 三步法自动化，跑完输出清单
- 脚本：`i18n_build/check_deploy_after_push_20260927.py` ← 推送后轮询 deployment + curl 线上复核
- **已推起点表**（下次推送用最新的）：
  | 本地 commit | 远程 commit | 内容 | 日期 |
  |---|---|---|---|
  | `0d10b7d9` | `b94f9879d5` | 8 分类页补内容 7 语言 + SEO 结构收口（1381 文件） | 2026-09-26 |
  | `41e1ff5a` | `ba4fa0cc52` | 移动端 P0+P1 + bump 20260927b（1370 文件） | 2026-09-27 |

### 推送后必须确认部署真跑了（Vercel 会漏）
- 三连查：`/deployments?per_page=3` / `/commits/<sha>/check-runs` / `/deployments?sha=<full-sha>`（count 0 = 实锤没触发）
- 救法：**用同一棵树发空提交**重触发（2 分钟内新 deployment 出现，已验证）
- 最后一定要 `curl` 线上实际资源复核（版本号 + CSS 关键声明），不能只看返回 200

---

## 内容层结构（两种语言机制勿混）
- 行内配对 span：products/applications/首页/blog 卡片；块级 `div.lang-zh` **只在 10 个 blog 文章页**
  且在 `.container` 内
- ⭐ `i18n_build/site_templates.py` 是唯一模板源；`build_listicle.py` 已冻结
- ⭐ 带 `data-i18n` 的元素**不能有子元素**（applyLang 走 textContent 会整个抹掉）
- ⚠️ ⭐ **改完 EN 源页别用批次重生成语言页**：实测附带漂移 + `mymemory` 配额降级；
  缓存命中不调 API，**投毒后重跑不自愈** → 语言版改动手写译文直接注入
- ⚠️ 机翻吃术语旁词尾（`alfombrTPEes`）→ 过 lint

## SEO / GEO 现状（2026-09-25 收口）
- 技术层已修平：404 / 跨语言 / 坏锚点 / canonical / hreflang / **h1>1 = 0** / title>60 宽 **0** /
  **空 href 0**（三项审计全归零）
- ⭐ **实体层铺满全站**：Organization + `@id=…/#organization` + sameAs 覆盖 1330 页；
  1085 个含 `Product` 的页补 `manufacturer`。sameAs 只放 `facebook.com/sanfanyoga`
- ✅ **GEO 端点齐全**：`llms.txt`（41 处裸 URL → markdown 链接，工具**只认 `[text](url)`**）+
  `llms-full.txt` + `.well-known/ai.txt` + `ai/{summary,faq,service}.json`；判分 **22/22**；
  线上实测 GEO **78**（Perplexity 43→50）
  ⚠️ **本地审不了**（geo 有反 SSRF 拒私网）→ 用 `verify_geo_endpoints_*.py` 抓响应喂解析函数
  ⚠️ **改 `faq.html` 后必须重跑** `geo_ai_endpoints_20260925.py`（`faq.json` 从它抽取）
  ⚠️ `geo audit` 展示层只打印 3 个 ai discovery 端点（漏 service.json），但判定层照样计分
- ⚠️ **`desc>155 宽` 最大存量缺口**（767 页 / 57%），根因是**译文膨胀**（EN 源多合格），
  主体 530 产品页；语言版更重（fr 最高 363 宽、it 349，照搬 EN 无解）
- ⚠️ 「答案块 134–167 词」是 **EN 专属**判据（fr/de/es/it 146–214、ja/ko 按字符），别跨语言套带宽
- ⚠️ 空 href 有 2 处**不在源码里**：`product.html` 的 `#pd-wa`（动态页兜底）/ `main.js:1140` 的 `menuItem.href`

## ⭐ 英文站 SEO 基线（2026-09-25，勿重复体检技术层）
- 191 英文页逐页审计：**技术层 10 项零未达标** → **别再报「技术 SEO 有问题」**
- 未达标 **397 → 209 处**；**结构类已清零**（H 层级 158 + 空 href 18 + blog 无 h2 1）
  → `fix_en_seo_structure_20260925.py --check` 必须 0 处
  ⚠️ **A2 反例 49 文件**（6 个 `applications/*` + `products.html` × 7 语言）：
  同样含 cat-head h3 但**前面已有 H2 → 勿动**
- 剩余：**产品页正文中位 469 词**（115/147 挤在 403–540=模板化）；
  ⭐ 同站 `pilates/*.html` **792–1119 词** → 短板在旧批次模板
- `desc>160 宽` **58 页**（EN 口径；已按内链权重修 11 个高权重页 → 138–152）
- ⭐ **内链数 = 站内权重标尺**（免外部数据）：内链 ≥70 的 20 页就是全站流量入口
- 工具：`audit_en_seo_standard_20260925.py` / `report_en_seo_20260925.py` /
  `fix_en_seo_structure_20260925.py` / `fix_high_weight_desc_20260925.py` /
  `audit_links_20260916.py`（61218 链接全 0）
- ⚠️ 坑：hreflang 存在性字典必须**全站**铺（只装英文页 → 假报 1140 处）；页面类型**别靠目录名判**
  （`pilates/` 是产品页）；词数用**静态口径**（Google 索引 `<details>`）
- ⚠️ 既有缺陷待修（A/B 已证非改动引入）：48 个语言版文章页缺 `</article>`；
  17 处移动端横向溢出（宽表格，`body{overflow-x:clip}` 裁掉且不可滚）

---

## ✅ 已完成批次（结论，细节在报告）

### 8 个一级分类页补内容（2026-09-26 推 `b94f9879d5`，1381 文件）
- 7 语言 56 文件 768 条译文（de 3718 / ja 301 / ko 2768 / fr 4560 / it 4343 / es 4451 词）
- 词数 177–356 → **685–862**（全进 600–1200）；H2 1→**4**；审计未达标 397→**201**，8 页**各 0 项未达标**
- 块覆盖 catintro 56 / cfaq 70 / cfaq-ld 70 / ilink 154
- 方案/验收 = `i18n_build/reports/category_content_{plan,verification}_20260925.md`
- ⭐⭐ **配额解法 = 让生成脚本「没事可做」**：预填 `category_content_data.json` 使 `build_data()`
  的 `todo == []` → **完全绕过 `translate_lines`，零 API/配额/缓存污染**（实测配额仍 500000/500000）；
  手写译文放 `catcontent_i18n/<lang>.json`
- ⭐⭐ **数据文件格式必须镜像目标结构（位置无关）**：用 `{页名: {…}}` **而不是**「顺序数组」——
  顺序数组一旦 off-by-one 整页错位，而脚本自身的条数/JSON-LD/配平断言**全都抓不到**
- ⚠️ 顺序不能换：`add_internal_links` **先跑**（造 `<!-- ilink:v1 -->`）→ 再跑 `add_category_content`
  （cfaq 锚点写死就是它）
- ⭐ 导语块插在**网格之前**（实测 390×844 第 **1.06–1.58 屏**）；FAQ 在网格之后（3.9–8.6 屏）
- ⭐ 非垫类 6 页用 `cat_h2_gear`("Sourcing guides for buyers")，**不是** "choosing a mat"
- ⚠️ 内容纪律：8 页**都有** `MOQ 100 pcs`；页面自身**都没有** `ROHS/CE/ISO 9001` → 检测类不列标准号
- ⏸ `ilink` 热区修法（`inline-block + padding:6px 0` → 44px）**未做**：行为变更，需单列批准。
  ⚠️ 站内 12 个分类页热区**一致**（18–19px），不修反而无「两种尺寸并存」问题
- 脚本：`add_category_content_20260925.py`（`--langs` 分批）/
  `inject_category_content_i18n_20260925.py` / `verify_catcontent_i18n_20260925.py`

### 四条工具铁律（分类页那轮踩出来）
① **difflib 范围核查必须把「受管区块」在对比前整段抽出**（difflib 按公共行切分，插入的 FAQ 块
里满是与页面其它处相同的行 → 被切成碎片 → `norm()` 抽不掉 → 全误报）；
② **独立验收器不许复用被验脚本的判据函数**（脚本自检只能证明「按它的假设成立」）；
③ **「混入中文」不能用「含 CJK」判**（日语正文必须含汉字）→ 改用**简体特有字**集合；
④ 结构守恒用「白名单签名 + 配平不变量」，别用一串 `if`

### SEO 存量清理（2026-09-25 推 `e416d1bc10`）
引号紧贴术语 105 处已清（de/pilates 90 + 6 个 blog 15）；EN 博客 10 页双 h1 已降 h2.post-title；
空 href 2 处已清。`audit_seo` **0 处**。脚本：`fix_quote_wrap_20260925.py` / `fix_blog_dual_h1_20260925.py`

---

## ⭐ 移动端（2026-09-25 实测，2026-09-27 P0+P1 已修并上线）

### 已修（远程 `ba4fa0cc52`，线上 `?v20260927b` 实测 8/8 关键声明到位）
**P0 五处**（`styles.css` +36/−7）
1. `a, button, [role=button], input, select, textarea, label, summary { touch-action: manipulation }`
   （全站 2001 元素由 auto 归一）
2. 表单控件 15px → **16px**（防 iOS 聚焦自动放大）
3. `.nav-links` 抽屉 `max-height: calc(100dvh - 68px)` + `overflow-y:auto` +
   `overscroll-behavior:contain` + `-webkit-overflow-scrolling:touch`
4. `.menu-toggle` / `.nav-brand` / `.lang-current` 40px → **44px**
5. ⭐ **≤920px 抽屉再减 54px 让开 `.cbar`**（`.cbar` 是 JS 注入、HTML 里 0 命中，
   `z-index:60 > 抽屉 49`，是底部通栏 → 修法是让位而非改层级）

**P1 三项**（`styles.css` +49/−0，`main.js` +7/−1）
1. 统一 `:focus-visible` 焦点环（`outline: 2px solid var(--brand); outline-offset: 2px`）；
   ⚠️ 不能套 `:where()`（记 0 分）→ `.field` 组补**同特异性**规则，写在原 `:focus` 行之后，
   否则被 `.sr-input{outline:0}`（0,1,0）压过
2. `[id] { scroll-margin-top: 82px }`（紧跟 `.nav` 后）
3. 文件末尾整块 `@media (prefers-reduced-motion: reduce)` + `!important`；
   `main.js` 的 `okBox.scrollIntoView({behavior:'smooth'})` 改为先判 `prefers-reduced-motion`

**验收**：CSS 括号 650/650、`@media` 30→31、`main.js` 过 `node --check`；
抽屉 none→322px(390)/268px(≤920)、滚动穿透 600→0、横屏末项 bottom 461→319；
A/B 铁证 = 改前 `E-bottom_before.png` 与 `C-landscape_before.png` **字节完全相同**（`scrollTop=9999` 完全无效）

### ⏸ 未做
- **P1-4 `env(safe-area-inset-*)`**：三条实测证明**本地验证不了**（meta 无 `viewport-fit`
  → `env()` 恒为 0；CDP 刘海模拟无效）→ `styles.css` 里 `env(` = 0 行，单列决策。
  **`viewport-fit=cover` 要不要做** = 独立决策项：不做则安全区永远无效；做则 1331 页 meta 变更 + 真机验证
- **P2 清单**：`translate="no"`（**8 语言站刚需**，机翻会把 SANFAN 当普通词）、`theme-color`、
  `preconnect`、491/19,109 张图补 `width+height`、`tabular-nums`、`tap-highlight-color`、`text-wrap:balance`
- **`a.c-link` 17px 热区**（导航/页脚文字链，跨 12 页稳定）→ 属行为变更需单独点头

### 存量移动端实测结论
- ⭐⭐ **内容位置看「距页顶几屏」，不看「在第几个区块后面」**：390×844 下曾测出导语在第 6.5 屏、
  FAQ 第 7.5 屏（320px 下 12 屏）→ **已修订：导语上移到网格之前**（6.5→1.2 屏）
- ⭐⭐ **inline 元素热区 ≠ 行高**：`ilink` 的 `<a>` 真实可点区间仅 **18–19px**（WCAG 2.5.8 AA 下限 24px）；
  **把 `line-height` 挪到 a 上完全无效** —— inline 命中区 = 字形 content area。
  唯一修法 `display:inline-block; padding:6px 0` → **44px**
- ⚠️ **320px 下 `de/index.html` 溢出 57px**（既有问题）→ **必须同时跑 320 与 390**（译语膨胀，只测 390 看不到）
- 工具：`audit_mobile_wig_20260927.py`（静态全站 138s）/ `audit_mobile_wig_browser_20260927.cjs` /
  `verify_p0_fixes_20260927.cjs`（`--base=` 可切线上）/ `probe_*_20260927.cjs` / `ab_p0_p1_screenshots_*.cjs`
- 判据源归档：`i18n_build/reference/vercel_wig_{AGENTS,command}.md`

---

## ⚠️ 站内搜索存在（勿再说「没有」）
- 全 JS 注入（`main.js`，模态框 `.sr-results`），HTML 里 **0 处痕迹**；
  索引 `assets/data/navdata*.js` 的 `window.SANFAN_NAV`（`total:147`，7 语言各一份）
  → 又一例「JS 生成 ⇒ 源码审计看不见」
- 但**无 URL 深链**（无 pushState/query）→ `SearchAction` 仍不能加，加前得先做可深链搜索

## ⭐ AI 引用基线（首测 2026-09-25，`geo_citation_baseline_20260925.py`）
- **新站 fjsanfan.com 0 次**（9 查询/60 席位 + 4 次真 AI 提问）；老站 sanfanyoga.com 3 席位 +
  **被秘塔实名引用为来源** → 问题是「AI 把三梵归因老站/平台」，非「不认识」
- 通道：❌ Perplexity/ChatGPT/Gemini/Google **本机全不可达**（DNS 污染成 Facebook IP）；
  ✅ `html.duckduckgo.com`（走服务端）+ ✅ 秘塔 metaso.cn；❌ cn.bing.com 返中国区结果
- ⭐⭐ **秘塔来源域名只能抓 favicon**：`cdn.metaso.cn/favicon/<域名>.ico`（卡片无 href）
- ⭐⭐ **采样失败 ≠ 无提及**（秘塔 ~6 次后限流返空壳）；**别拿自写备注做匹配**（会假报 100%）

## 其他待办
- **69 台结构化型号主表**（画册 8 系列 × 8 族页，含材质/包装 A/B/毛重）→ 重建脚本
  `rebuild_pilates_models_from_ocr.py` 还有 4 处待修（p37/p38/p39 左右两栏同 y 交错致字段错位）；
  ⚠️ `i18n_build/data/catalog_pilates_models.json` **静默丢字段**（OCR 里 33 台有装箱尺寸、JSON 里空）
  → 主表须以 OCR 重建
- **画册配图**：能裁出、不能全自动定位（v3 全量：台数全对 26/38 页 68%、文字重叠 42/69 台 61%）
  → 报告 `pilates_catalog_image_extraction_20260926.md` + contact sheet（56 张，约一半可直接用）


---

# 归档：MEMORY.md 2026-10-02 精简前全文（33k → 精简版，原文零丢失）

# 三梵独立站 fjsanfan.com 长期笔记

> ⭐ **细节全量版 = `i18n_build/reference/site_rules_full_20260927.md`**（判据铁律 25 条 / 已完成批次 /
> 移动端实测 / SEO-GEO 基线 / 工具清单，全在里面）。**MEMORY.md 只留高频必读 + 当前状态。**
> 技能：`github-api-push` / `fjsanfan-mobile-ui-audit`（**改 CSS/JS 前必读**）/ `sanfansport-catalog-sync` /
> `fjsanfan-multilang-spec-sync` / `fjsanfan-pilates-section`

## 概况
- 仓库 zeng085/sanfan-yoga-site（**private**）→ Vercel；B2B OEM/ODM 瑜伽垫/健身器材厂站；1331 页
- EN 主站 + de/ja/ko/fr/it/es 子目录 + 中文同页切换（无 /zh/ URL）；sitemap 1330 条
- ⚠️ `.gitignore` 排除 `i18n_build/.deepl_key*`、`i18n_build/data/`（16M 报价表机密）
- ⭐ 全站脚本**一律后台跑**
- ⭐ **资源版本号 = `20261001e`**；写法 `?v20261001e`（**没有等号**）；**改 CSS/JS 必 bump，且必须与改动同一个 commit**（漏 bump = 用户命中缓存旧 CSS，HTML 改了但看着没变）

## 推送（细节见技能 `github-api-push`）
改 CSS/JS 先 `bump_assets_ver.py` → 干净 commit →
`GH_PAT=$(cat ~/.workbuddy/secrets/gh_pat) python3 push_api_v3.py zeng085/sanfan-yoga-site <abs_repo> --auto`
（顺序不能换）。diff 带 `--no-renames`；**不要 `reset --soft`**（v2 残留，照做=死局）
- ⭐ **起点判定三步法**（脚本 `i18n_build/verify_push_scope_20260927.py` 已自动化）：
  ① 远程 HEAD 的 **message** 匹配本地 commit（sha 谱系不同）→ ② 远程 tree vs `git ls-tree -r <起点>`
  **逐 blob 比对**，三类差异必须全 0 → ③ 清单两法交叉验证（远程树 vs 本地 HEAD 树 / `git diff`）
- ⚠️ **本地 `origin/main` 是陈旧缓存**：API 建独立 commit，不更新本地 ref → `git log origin/main..HEAD`
  报「待推 65 个」**全是假象**
- **已推起点表**（按时间序，下次取**最后一行**）：`0d10b7d9`→`b94f9879d5`（分类页 1381 文件，09-26）；
  `41e1ff5a`→`ba4fa0cc52`（移动端 P0+P1，1370 文件，09-27）；
  `a19e4a0b`→`7705a32b6d`（普拉提 9 页画册重构，1445 文件，10-01）；
  `02d6e1ab`→`1188a4c463`（灯箱标题修复，1336 文件，10-01）；
  `f53ca5a1`→`b57d64c7ce`（排版修复+全站表格+desc 改写+CSV 转 LF，1339 文件，10-01）；
  `1853d5a2`→`8b31f81a2a`（缩略图墙+规格表折叠，1340 文件，10-01）；
  `f7760479`→`5556e3a39b`（画册墙改默认显示，1336 文件，10-01）；
  ⭐ `3179ac0e`→`1e5773d15a`（**6 篇普拉提博客 + GEO 改进 P1/P2/P3，26 文件，10-02**）
  → **当前 START = `3179ac0e`**
  ⚠️ 起点脚本 `verify_push_scope_20260927.py` 的 `START` 曾忘更新（留在已推的 `1853d5a2`）
  → **推送成功后第一件事就是改 `START` + 补起点表注释 + 同步 MEMORY.md**（10-02 已修正）
- ⚠️⭐ **起点判定第 2 步有一个稳定假警报**（10-02 实测闭环）：报 1 处「同名内容不同」= 脚本自己的
  输出文件 `push_list_20260927.txt`。因脚本**每次运行都重写它**，而起点 commit 冻结的是更早一次结果
  （`f7760479` 存 1340 行版 blob `c97cc764`，远程/HEAD 是 1336 行版 `ac500b3a`）。
  判据三连（缺一不可）：① 两侧 blob 总数相等且「仅远程/仅本地」全 0 → 无文件级遗漏；
  ② 取远程 blob 反解文本与起点版 diff → 差异**全是清单里的路径行**；
  ③ 那些「消失」的文件去远程树查 → **依然在**。
  → 缓解：推送前 `git checkout -- <OUT>` 把该文件恢复成 HEAD 版（= 远程 blob），下一轮即可三类全 0。
- ⚠️ ~~推送管道会把文本 CRLF 归一为 LF~~（已根除 10-01：`pilates_catalog_2026_models.csv`
  本地转 LF 随 `f53ca5a1` 推送，此后不再产生假差异）
- ⚠️ 推送成功日志末尾的「本地对齐：git reset --soft …」是 v2 残留提示，**照做=死局**
- 推送后必查：`i18n_build/check_deploy_after_push_20260927.py <sha> <版本号>`
  （轮询 deployment + curl 线上复核；已参数化）。⚠️ Vercel webhook 会漏触发 → 救法 = **同一棵树发空提交**
  ⭐ 脚本内版本号比对已改**通用正则提取**——别再建「候选版本号白名单」，
  漏掉本次版本 = 12 轮全返回 `[]`，会被误判成「部署没好」（实测踩过）
  ⚠️ 漏触发也可能只是**延迟**：10-02 实测第 1 轮 count=0、第 2 轮（+15s）就有了 → 先轮询 2–3 轮再发空提交
- ⭐⭐ **不 bump 版本号时，「看资源版本号」判据失效**（10-02 新建脚本）：
  本轮只有 HTML/工具改动、无 CSS/JS → 版本号仍是 `20261001h`，线上新旧同号
  → **该信号无法证明部署已切换**。改用 `i18n_build/verify_live_bytewise_20261002.py`
  （本地⇄线上**逐字节**比对，两侧都做 CRLF→LF 归一；默认取 `START..HEAD` 变更集，可传路径/`--rev`；退出码即可当闸）。
  判据强度：逐字节 > 手写字符串断言（我本轮手写的断言就错了，见下）> 资源版本号。
  ⚠️ 手写断言的坑：我断言「2570 应已清除」，但 **2570 是 AL 8-Y/Wood 1 A-3in 1 的真实木箱长度**，
  合法留在对比表里；错的只是「2570 是最长」这个**断言**。→ 断言要针对**错误表述**，不是针对数字。
  ⚠️ 资源 404 体检必须 `urljoin(页面URL, 相对路径)`：博客页写的是 `../assets/...`，
  直接拼 BASE 会构出 `/../assets/...`、HEAD 返回 0，**像是资源 404，其实是我探针错了**。
- ⚠️ 闸二（内容级扫密钥）**别自己逐文件读**（1370 文件 → SIGTERM）→ 用 `git grep -n -I -E … HEAD -- .`；
  且 `git grep …| head` 的 `$?` 是 head 的退出码，不能当判据。
  10-02 加一道最直接的：用**真实 PAT 值本身**（`git grep -F "$PAT" HEAD -- .`）扫全树 → 0 命中才算过
- ⚠️ **本机 `en.wikipedia.org` 被 DNS 污染**（`31.13.88.169` = Meta 网段，TCP 挂死）→
  外链可达性本地**验不了**（直连 curl 与 WebFetch 均失败）。`fjsanfan.com` / `api.github.com` 正常。
  → 报告里这类外链必须继续标「未验证」，别因为「试过了」就当「验过了」
- ⚠️ 闸二（内容级扫密钥）**别自己逐文件读**（1370 文件 → SIGTERM）→ 用 `git grep -n -I -E … HEAD -- .`；
  且 `git grep …| head` 的 `$?` 是 head 的退出码，不能当判据

## GEO 审计工具链（2026-10-02 建立）
- ⭐ **唯一带可执行引擎的技能是 `geo-optimizer` v4.18.3**（`geo` CLI + Python API，47 项引用度）。
  **其余 `seo-*` 技能只有 SKILL.md、无脚本**（其内文引用的 `${CLAUDE_PLUGIN_ROOT}/scripts/claude-seo`
  本机不存在）→ 只能当 rubric 用，别期待能跑。`seo-ops` 带 `gsc_client.py`（真实收录数据唯一来源）
  但**未授权**（需 `GOOGLE_CLIENT_ID/SECRET`，本机无 token）→ 真实收录/排名**拿不到**。
- ⭐⭐ **引擎对本地地址恒判 0 分**：`geo audit` 与所有 `audit_*` 都走 `utils.http.fetch_url`，
  该函数**内置反 SSRF** → 传 `http://127.0.0.1:8866` 得 `None,"Unsafe URL"`
  （实测 `audit_robots_txt` 得 `found=False`，而 curl 同址 200）。
  **解法 = `i18n_build/_geo_local_harness.py`**：把 `sys.modules` 里所有 `geo_optimizer*`
  的 `fetch_url` 换成**磁盘垫片**（URL→仓库文件，返回带 `.status_code/.text/.headers` 的对象），
  但 **base_url 仍传 `https://fjsanfan.com`** → canonical/内链/hreflang 判据看到生产形态 URL
  → 可直接调官方编排器 `run_full_audit`，判分与线上同构，**无需起服务器**。
- ⭐⭐ **总分不能当单页质量证明**：8 类目里 5 个**全站同值**
  （robots / llms / ai_discovery / signals / schema = **54/85，占 64%**，补 robots 前是 51/82=62%），
  页面级只有 meta + content + brand_entity + negative_penalty ≈ 27–31 分。
  → 全站 81→85 的差距只来自页面级那几分。**判单页质量看 47 项引用度（区分度 41–60）与目标 query 覆盖。**
- ⭐⭐ **`Statistics Addition` 对本站是假阴性**：`_STAT_PATTERNS` 只匹配 `%`/千分位/`$`/`million`/`Nx`
  → **`1190 × 700 × 1170 mm`、`85 kg`、装箱件数全抓不到**（`tables_with_data` 复用同一正则，规格表也不计）。
  实测「看不见的规格数字」（补方法论段后）：layout 117 / reformers 67 / oem 51 / commercial 24。
  → **别改数字格式**；要补的是**句子级**一手事实陈述。
- ✅ **`citation_bots_explicit` 判据**：`CITATION_BOTS = {Googlebot, Claude-SearchBot, Applebot,
  PerplexityBot, OAI-SearchBot}`，**必须每个都有显式 `User-agent` 规则**（通配 `*` 兜着不算）。
  10-02 已补 3 个 → `True`（站点级 +3 分）。新增 bot 时记得同步这里。
- ⭐⭐ **一手数据 / 引用来源两项的判据（读源码确认，别凭猜）**——
  `core/citability.py::detect_first_party_data` 三项累加（上限 4）：
  ① `_FIRST_PARTY_PATTERNS`（`our research`/`we analyzed`/`our data shows`/`we found`/`we tested`/
     `we measured`…）**≥2 命中 +2、≥1 +1**；
  ② `_OWN_DATA_RE` = `\b(?:we|our team|our company)\s+\w+\s+\d+` —— **必须「we + 一个词 + 数字」紧邻**，
     中间夹别的词就不算（所以 `We measured 220 kg…` 行，`our team recorded the spread across…` 不行）；+1；
  ③ Methodology 标题：`h_text` **恰好等于** `our methodology`/`methodology` 等（带别的字不算）+1。
  `cite_sources`：`权威外链×2 + 外链×1 + <cite>×2 + References/Sources 标题×2`，上限 6；
  `wikipedia.org` 在 `_AUTHORITATIVE_DOMAINS` 内，`.org/.edu/.gov` 也算权威 TLD。
  → 实测：加 1 段 `Our methodology` + 2 个 Wikipedia 外链，`First-Party Data` 0/4→**4/4**、
  `Cite Sources` 1/6→**6/6**。总 +4 分，页面级得分 27→31。
- ⭐⭐ **数字溯源 SSOT：`i18n_build/pilates_figures_20261002.py`**（详见铁律 26–28）——
  基准是**已上线族页**（不是 reports 里的 CSV，那份缺行），两种形态（总表 `<tr>` + 型号卡）都要抓；
  提供 `verify_numbers`（尺寸/毛重集合归属）与 `verify_superlatives`（最高级断言 = 算出的极值）。
  已接入 `verify_pilates_blog_20261002.py`。**改普拉提文案后必跑。**
- ⭐ **双语 DOM 对照法**：站点每页内嵌 `.lang-en`+`.lang-zh`，判「中文副本有没有污染判分」
  = 移除 `.lang-zh` 后重跑引用度。实测**仅英文一律更低（−1~−6）且基线页同幅** → 对照公平、无虚高。
- 审计脚本：`i18n_build/audit_pilates_blog_geo_20261002.py`（支持 `--render-only` 免重算引擎；
  **入链扫描必须单次遍历**——6 次遍历 2500 文件让耗时从 1m07s 涨到 5m02s）

## 判据铁律（本表 33 条，⚠️ 编号 13/14/15 有重复，按内容判读；全量版见 reference）
1. ⭐ **同一文件的多个 Edit 不能并行**：只有最后一个落盘，另几处静默丢失
2. ⭐ **「同串同步」先数清有几份**：HTML 转义形态不同就不算同串（meta 的 `&amp;` vs JSON-LD 的 `&`）
3. ⭐ 替换式脚本：落盘前 `assert 'href="href="' not in out`；**先摘旧块再重插**；错则先回滚再重跑
4. ⭐ **回退断言分插入/替换**：插入型要与摘块正则**严格互逆**（否则每跑一次多一空行）
5. ⭐⭐ **源码审计归零 ≠ DOM 干净**：JS `createElement`/改属性产生的缺陷
   （`main.js:1140 menuItem.href='#'`、JS 注入的 `.cbar`、全 JS 的站内搜索）**不在 HTML 里**
   → 必须补浏览器级探针，且**按视口分别查**
6. ⭐⭐ **「该改成什么」先搜同处现成写法，别推理**（搜到即用，天然与全站一致）
7. ⭐⭐ **说「惯例」前先量化，且只在同类元素内成立**（`c-link` 1317 处带 `target` / `btn-ghost` 1029 处全不带）
   → 清理类**只修缺陷**，行为变更单列征询
8. ⭐⭐ **改 HTML 标签必须成对**：只 `subn` 开标签 → dry-run / 幂等自检 / computed style **三处都抓不到**；
   浏览器忽略 `</h3>` 后 h2 会**吞掉后面的 `<table>`** → 落盘后断言 `<X`/`</X>` 增减一致
9. ⭐⭐ **「既有问题」必须 A/B 实证**（HEAD 版导出到同目录新文件对比）→ 禁止用「我没改这里」推断
10. ⭐⭐ **改后核查三件套**：`verify_changes_scope_*.py`（difflib 证无夹带）/ `verify_tag_balance_*.py` /
    `scan_overflow_*.cjs --vp=390`；等价简版 = `git diff -U0 -- '*.html'` 的 **`+`/− 行数必须配对**
11. ⭐ **长度判据先问「对 CJK / 对译文成立吗」**：meta 按**显示宽度**（CJK×2，title 60 / desc 155）；
    中英字符比中位 **0.353**（<0.25 = 残块）；「重复」须**按语言分组**
12. ⭐ 工具坑：**`grep -r` 会扫 `.git`（338MB）→ SIGTERM**；**`bump_assets_ver.py` 被超时杀掉会
    静默停半途** → 判定补完**只能看 `--dry-run` 分布是否单一项**
13. ⭐⭐ **分类统计先确认字段是「全串」还是「前缀」**：`series` 是 `"A. AL 铝合金核心床"`，
    用 `"A."` 直接 Counter → **每线 0 台却静默通过** → 断言闸必须含「每个类目计数 > 0」
14. ⭐⭐ **换数据源要换四层**（正文 / meta×3 / JSON-LD / hero）—— 只换正文表格，
    页面与 SEO 层会自相矛盾：★ 判「旧内容是否清干净」用 `git grep` 全串扫描，别看哪里改过
15. ⭐ **`:first-of-type` ≠ 第一个该类元素**：父容器第一个 `div` 若是 `.section-head`，
    `div.cat-unit:first-of-type` 匹配 **0 个** → Playwright 改用 `page.$()`（天然取第一个）
13. ⭐⭐ **对照工具的「静默跳过」比误报更危险**：白名单外的标签/字段必须**直接报错**，
    不能 `continue`。实战：对账脚本漏了 `Material / weight` 这个自定义合并标签，
    整条被跳过 → 与同页总表 `—` 自相矛盾的缺陷逃过检查。改完要 **A/B 实证**
    （把老写法塞回临时副本，确认新版真能报出来）
14. ⭐⭐ **截图与锚点两个必踩坑**：①`fullPage` 截图遇 `loading="lazy"` → 图是空白块，
    且探针 `naturalWidth=0` **假报 404**（curl 实测 200）→ 必须**先逐屏滚动预热 +
    `waitForFunction` 全部 img `complete` + 滚回顶部**再截；②sticky 横幅高度**随视口变**
    （导航换行：1280→92px / 390→192px）→ 锚点用固定 `scroll-margin-top` 必被压住 →
    **JS 写 `--pv-bh` 取实测高度**。判据 = 跳转后目标标题 `top > banner 高度`
15. ⭐ **「视口外元素」探针要认容器**：`pl-spec` 表在移动端是 `.pl-spec-wrap`
    `overflow-x:auto` **容器内横向滚动**（table 860px / wrap 350px），是**既有设计不是缺陷**；
    漏判 `el.closest('.pl-spec-wrap')` 会把合法滚动报成溢出
14. ⭐⭐ **探针期望值必须实测，报假警的工具＝没人信的工具**（"狼来了"）：
    ① `loading="lazy"` 的图未进视口时 `naturalWidth=0` → **假"解码失败"**，测前先**分步滚到底**
    ② `file://` 会破 JS 按目录深度推算的相对路径（`main.js` 的 `wechat-qr.webp` 必 404）
      → 起**本地 HTTP 服务**加载，与线上同构
    ③ 第三方请求（GA）离线必失败 → **只判本域**请求
    ④ 写完先自问「这个数字是我测的还是我猜的」
15. ⭐⭐ **资源未跟踪 = 线上 404**：改 HTML 引用了新图片/新文件，落盘后必须核对
    `git status` 里该资源是否**已跟踪**（实测：全站 2503 个 HTML 引用里恰好 3 张画册图未跟踪，
    线上实测确为 404）。同类：**无 `.vercelignore` → 整仓公开**，新增脚本/报告前想清楚
    是否愿意全网可见（实测 `i18n_build/site_templates.py` 线上 200）
16. ⭐⭐ **别在「已被截断的字符串」内部替换**（本轮最贵的一课）：卡片写的是
    `lead_en[:180] + "…"`（**先截断再补省略号**）。在被截断到 181 字的文本里把
    长句换成短句 → 卡片变 163 字，而生成器重跑得 181 字 → **产物与源脱钩，
    只改产物的检查全发现不了**。→ 改完文案必须用**生成器表达式重建那段**，
    并跑 `i18n_build/verify_pilates_source_vs_product_20261001.py`（8 族 × 4 类源⇄产物审计）
17. ⭐⭐ **拼接串 `replace` 会静默空跑**：目标串在文件里**不连续**（如两个容器块之间隔着空行）
    → `h.replace(块A+块B+块C, 新序)` 命中 **0 次也不报错**，看着「已重排」其实没动。
    实战：表已换序、画册块没换 → 表↔卡错位，静态核验才发现。
    → 取「首块起点 ~ 末块终点」**整段重建**（分隔符原样带上），**落盘后再断言顺序**
18. ⭐⭐ **备份禁落站点目录**：无 `.vercelignore` → `pilates/x.html.bak_*` 会被 Vercel
    当静态文件**发布成公开重复页**。→ 备份写 `~/.workbuddy/backups/fjsanfan/`，
    且 `.gitignore` 补 `*.bak_*` 兜底（已加）
19. ⭐ **本地服务用多线程**：`python -m http.server` 是**单线程**，playwright 并发拉图会丢连接
    → 页尾大图 `naturalWidth=0`，**像真缺陷**。用 `socketserver.ThreadingTCPServer`。
    配套：lazy 预热用 `document.documentElement.scrollHeight`（`body.scrollHeight` 偏小 → 漏页尾）
20. ⭐⭐ **数「卡片」先分清层级**：`cat-unit`=画册页单元、`model-card`=型号卡
    （45 单元 / 80 卡）—— 数错层级 = 凭空 35 张的「假缺口」；同类：
    `itemListElement` 在 **BreadcrumbList 里也有** → 数 ItemList 必须
    **json.loads 解析后按 `@type` 过滤**（正则计数 6 页数出 12 的假富项）
21. ⭐ **双语 span 结构下 JS 取文本必须按 computed display 过滤**：`.lang-en/.lang-zh`
    并存、靠 CSS 切换，`figcaption.textContent` 会读出两套语言+链接文案粘连
    （线上实测 `"2026 catalogue · page 032026 画册 · 第 03 页 · view larger放大查看"`）
    → 修法 `main.js capText()`：`:scope > span.lang-*` + `getComputedStyle().display!=='none'`
22. ⭐⭐ **FAQPage 结构化数据必须有可见内容对应**：站内既有 10 篇博客**只放 LD、不放可见问答**
    → 属不合规（富结果会被判 spam）。新篇一律「题作 `<h3>`、答作 `<p>`」，
    校验断言「LD 里的题 N/N 在可见正文出现」；FAQ 内容要写**真实采购决策问句**（GEO 引用友好），
    不是关键词堆
23. ⭐⭐ **`git grep` 不覆盖未跟踪文件** → 新增文件的密钥闸必须换**直接检索**（否则闸二假绿）。
    配套三条 grep 坑（本轮又各踩一次）：
    ① BSD grep 的 `\|` 交替**失效** → 一律 `grep -E`（曾误判「MEMORY.md 起点表没更新」）
    ② `grep -c` 数的是**行数**不是次数 → 精确计数用 `-o … | wc -l`
    ③ 增删行配对自检时 `grep -vE '^---'` 会**漏掉内容本身以 `-` 开头的行**（如 `.md` 列表项
       `-- Pilates apparatus line: …`）→ 差额要人工复核，别用计数当判据
24. ⭐⭐ **「自己的旧文案是错的」也要修，但要修成可验证的分项口径**：站点既有
    「41 wooden studio models」与实况（80 型号，含铝合金线）矛盾 → 改写为
    「80 models（46 reformer / 11 tower / 9 chair / 7 barrel / 4 cadillac / 3 specialty）」
    → **数字要能对上 `model-card` 实测计数**，别只换一个更大的数
25. ⭐ **推送成功后第一件事：更新起点脚本 `START` + 起点表注释 + MEMORY.md**（三处同步）。
    实测漏更新（留在已推的 `1853d5a2`）→ 下一轮三步法会从**已推点**开始比对，
    表现为「三类差异=0 但清单多出一整批」的诡异结论
26. ⭐⭐ **极值/统计类断言必须从 SSOT 算，不能手写**（本轮最贵的一课，代价是两处已发布文案出错）：
    手写的「最长 2570 mm」「最高 860 mm」都脱离了数据源 —— 真值 **2800 mm（AL 13 MC）**、
    塔架类 **2000 mm**（860 只是 AL 12-CR 自身高度）。→ 建立
    `i18n_build/pilates_figures_20261002.py`：从已上线族页算 `longest/widest/tallest/heaviest`，
    页面里**每个尺寸/毛重必须能溯源**（集合归属），**最高级断言必须等于算出的极值**。
    校验器写完必须 **A/B 实证**（把旧错误塞回临时副本，确认真能报出且原件零误报）——
    实测 4/4 抓到、零误报
27. ⭐⭐ **选基准先问「这份数据完整吗」**（两个坑都在本轮踩过）：
    ① 别用 `reports/pilates_catalog_2026_models.csv` —— 缺行（69 vs 真 80），
       会把 AL 19-F / AL 8-Y 这类**合法数字判成「无据」**（假警报）；
    ② 别只用型号总表 `<tr><td class="model">` —— **梯桶族页只有型号卡没有总表**，
       必须两种形态都抓（`_ROW_RE` + `_CARD_RE`），按型号名去重后才得 80 个型号。
    → 「页面上有这个数字」≠「数据源里有」，反之亦然；**基准错 = 整个闸门没有意义**
28. ⭐ **正则式探针必须先把「不该匹配的形态」剔除，并先测再定阈值**：
    「最长的 2800 × 680 × 450 mm」会被匹配到三元组末尾的 `450 mm`（假警报）
    → 跑最高级检查前先 `_TRIPLE_RE.sub()` 剔除三级尺寸；
    且间隔符要**紧**（`[^.,;:]` 不容逗号），否则「the longest side, so a standard 900 mm door」
    被读成「最长=900」。**先跑一遍看误报清单，逐个判完再定稿**

## 内容层结构（两种语言机制勿混）
- 行内配对 span：products/applications/首页/blog 卡片；块级 `div.lang-zh` **只在 10 个 blog 文章页**
- ⭐ `i18n_build/site_templates.py` 是唯一模板源；`build_listicle.py` 已冻结
- ⭐ 带 `data-i18n` 的元素**不能有子元素**（applyLang 走 textContent 会整个抹掉）
- ⚠️ ⭐ **改完 EN 源页别用批次重生成语言页**（附带漂移 + 配额降级；缓存投毒后重跑不自愈）
  → 语言版改动**手写译文直接注入**

## 当前状态
- ✅ **普拉提板块 9 页已按 2026 画册重构并上线**（远程 `7705a32b6d`，1445 文件；
  线上 `?v20261001c`）。两级结构别数混：`cat-unit`=**画册页单元**（45 个）、
  `model-card`=**型号卡**（80 张：46/11/9/4/3/7）；`.cat-zoom` 灯箱 45/45 全覆盖。
  线上体检（`verify_live_assets_20261001.py`）：50/50 资源 200（38 画册图无一 404）、
  序号 0 错、ItemList 6/6 平、版本号 6/6 页已切
- ✅ **灯箱标题缺陷已修并上线**（远程 `1188a4c463`）：figcaption 里 `.lang-en`/`.lang-zh`
  并存靠 CSS display 切换，`textContent` 会读出「两套语言+链接文案」粘连
  → `main.js capText()` 按 computed display 取当前语言、排除 `<a>` 内文案；
  ladder-barrel 3 处放大链接补 `cat-zoom`（此前走原生新窗口，与另 5 页不一致）
  ⭐ `cat-zoom` 只存在于 pilates 6 页 —— 别在首页查页面级钩子（假 ✗）
- ✅ **折叠方案 v3 已上线（5556e3a39b）**：画册展开=缩略图墙（cat-grid-mode，
  点图复用灯箱）、6 个 EN 族页规格对比表默认折叠（#spec-all）、
  main.js 折叠泛化 + 锚点代理自动展开；版本号 `20261001h`；
  **画册墙默认直接显示**（data-fold-grid 初始即 GRID，按钮文案随状态切换「收起/Collapse」）
  ⚠️ 探针：**父级 display:none 时子元素 computed display 不变**（查容器不查卡片）
  ⏸ **6 语言版 pilates 页仍是旧体系**（用户：先做好英文，不急）
- ✅ **普拉提板块 6 篇 SEO/GEO 博客已上线（10-02，远程 `1e5773d15a`）**：此前板块页挂的博客引用位
  **目标页根本不存在（死链）**，现补齐 6 篇（`blog/pilates-reformer-buyers-guide|apparatus-differences|
  studio-equipment-list|oem-pilates-equipment-china|studio-layout-guide|equipment-commercial-use`）。
  双语同页；9 类校验全绿（含 **FAQ 题 5/5 在可见正文出现**——站内旧 10 篇只放 LD 不放可见问答=不合规）；
  E 级信息零命中；接入 blog.html 索引卡 / sitemap / llms.txt+llms-full.txt / pilates 首页 `#buyer-guides`。
  ⭐ **型号数口径修正 41 → 80**（旧文案「41 wooden models」不实，新文案带分项 46/11/9/7/4/3）
  ⭐ **未引用商标/认证/价格/MOQ/弹簧/承重**（延续器械页无主张口径）
  ⏸ **6 语言译文被额度阻塞（10-02 实测确认；DeepL 路线已判定不可行，换腾讯云 TMT）**
  · `/v2/usage` 实测：主 key 已用 **500,000/500,000**（剩 0）；备份 key 已用 **960,268/1,000,000**（剩 39,732）
    → **两个 key 全满**。⚠️ 已知坑：**DeepL API Free 已于 2026-07 停售新注册**（老 key 按官方说法可续用，
    是否仍每月重置只能 11-01 实测）；即使重置，500k/月也只够 6 篇博客 ×6 语言（416,400），不含 pilates/ 9 页
  · **工作量实测**（剥 script/style/标签后正文）：6 篇博客 **69,400** ×6 = **416,400**；
    `pilates/*.html` 9 页 **100,924** ×6 = **605,544**
  · ⭐ **选定替代 = 腾讯云机器翻译 TMT**：官方文档确认**每月 500 万字符免费**（实名后每月 1 日发资源包，
    永久；超出自 58 元/百万，且**后付费默认关闭 → 用完自动停服，零扣费风险**）；
    `en` 源语言原生支持 **de/ja/ko/fr/it/es 全部 6 个**（官方语言对表已核）；国内直连无 DNS 污染问题
  · ⚠️ **迁移三坑**：① TMT 文档明说「含 HTML 标签等非常规文本可能翻译失败」→ 现有 `<x0>` XML
    术语保护方案**不能直接搬**，要换**私有区字符哨兵**（`\uE000…`）或建 TMT 术语库（`TermRepoIDList`）；
    ② `TextTranslate` 是**单条**接口、单次 <6000 字符、默认 **5 QPS** → 批次要拆细（59 万字符约 6000 次调用）；
    ③ `UntranslatedText` **每次只支持一个词** → 不能靠它做术语保护
  · ✅ **10-02 已接好 GLM 引擎并实测通过**：新增 `i18n_build/translator_glm.py`
    （行号锚定+完整性校验+重试，`--selftest` 10/10），`translator.py` 引擎链改 **GLM → DeepL → MyMemory**；
    key 在 `i18n_build/.glm_key`（600，已 gitignore）；端到端实测 12/12 句一次全过、零降级、
    缓存复用生效；⚠️ 模型**始终思考**（thinking 参数全 400），~350 reasoning tok/请求，
    大批次摊薄后可忽略；⚠️ **ENGINE_TAG 仍为 "deepl" 故意不改**（改=全站缓存失效全量重翻）
  · **下一步**：1 整页 6 语言 A/B → 全量 6 篇 ×6 语言（~¥0.5）→ 36 个语言版页面的
    生成/部署链路（sitemap/hreflang）尚未建
  · ⭐ **成本实算（15 页 ×6 语言，含 token 比例假设）**：GLM-5.3-Flash **≈¥1.25**；
    旗舰 GLM-5.3 ≈¥12.5；GLM-4.7-Flash **¥0**
    （6 篇博客：输入 104,100 + 输出 151,666 tok；pilates 9 页：输入 151,386 + 输出 220,558 tok）
  · ⚠️ **GLM-5.3-Flash 不是免费模型**（付费 ¥0.8/¥2.8）；免费的是 **GLM-4.7-Flash**。别记混
  · ⭐ **换 LLM 引擎的架构差异（不是换 key）**：① 从「50 条/请求逐行批量」改为
    「分块整段翻译 + 行号锚定」；② **必须新增译文完整性校验层**（NMT 条数天然一致、LLM 会漏译/合并/加解释）；
    ③ 数字与 E 级信息回归校验（复用 `pilates_figures_20261002.py` 的 `verify_numbers()`）；④ temperature=0
  · ✅ **LLM 相对 NMT 的实质优势**：1M 上下文可**整页一次性翻译**（单页 12,861 字符 ≈3,200 tok），
    上下文连贯性远超逐行；术语表直接写进 system prompt，**不需要 DeepL 的 `<x0>` 标签或哨兵 hack**
  · ❌ 不走的路：Google Cloud（需代理+卡）、等 DeepL 重置（要等 30 天且只够一半工作量）
- ✅ **6 篇博客已过 GEO/SEO 审核 + P1/P2/P3 全部实施并上线（10-02）**：
  · 改进后总分 **84–85**（good；基线 81–85）；47 项引用度 **55–60**（原 41–56）；
    `First-Party Data` 0/4→**4/4**（6/6 页满分）、`Cite Sources` 1/6→**6/6**（加 `Our methodology` 段 +
    2 个 Wikipedia 外链）；站点级 54（补 robots 后 +3）
  · 负面信号 0（仅 oem 页 −1：`model` 密度 3.2%/severity low，可辩护）；
    **36/36 目标 query 可检索**（H2/H3 或正文 ≥0.75），标题层锚定 15 条（42%）；
    可发现性 6/6 全绿（sitemap/canonical/hreflang/llms/JSON-LD/各 2 入链）
  · ⚠️ **总分 64% 是全站同值 → 不能当单页质量证明**（详见「GEO 审计工具链」节）
  · ⚠️ **部署后已验**：12 个站点文件线上⇄本地**逐字节一致**、6 页 9 个静态资源 HEAD 全 200；
    但**真实收录 / 排名 / AI 引用仍验不了**（GSC 无凭据 → 需配 `GOOGLE_CLIENT_ID/SECRET`）
  · ⚠️ **2 个 Wikipedia 外链可达性仍未实测**（本机 DNS 污染，非站点问题）
  · ⚠️ 2 个 Wikipedia 外链**可达性未实测**（沙箱无外网）→ 部署后复核
  · ⚪️ 仍待用户定：**引语（Quotation +41%，影响最高）**——引不存在的专家=编造，不做
  · 本轮只改 6 个博客页 + `robots.txt`，**未 bump 版本号**（新段落全用既有 `.article-body` 样式）
- ⏸ 13 台缺材质/毛重（画册未印）→ 等工厂；`i18n_build/__pycache__/translator.cpython-313.pyc`
  已被跟踪，建议 `git rm --cached`
- ✅ **移动端 P0 五处 + P1 三项已上线**（远程 `ba4fa0cc52`，线上 `?v20260927b`；
  线上实测：touch-action `manipulation` 1811/1811、汉堡 44×44、表单 16px、
  抽屉 268px/auto/contain、header 仍 69px、横屏末项 ✅ 在视口内且未被 `.cbar` 遮挡）
- ⏸ **P1-4 `env(safe-area-inset-*)` 未做**：本地验证不了（meta 无 `viewport-fit` → `env()` 恒 0）
  → **`viewport-fit=cover` 是否要做 = 独立决策项**（不做则安全区永远无效；做则 1331 页 meta 变更 + 真机验证）
- ⏸ **P2**：`translate="no"`（**8 语言站刚需**，机翻会把 SANFAN 当普通词）、`theme-color`、
  `preconnect`、491/19,109 张图补 `width+height`
- ⏸ **`a.c-link` 17px 热区**（跨 12 页稳定，行为变更需单独点头）
- ⏸ **SEO/GEO 存量**：`desc>155 宽` 767 页（57%，根因译文膨胀，主体 530 产品页）；
  产品页正文中位 469 词（同站 `pilates/*.html` 792–1119 词可参照）
- ⏸ **既有缺陷（A/B 已证非改动引入）**：48 个语言版文章页缺 `</article>`；17 处移动端横向溢出
- 📌 **普拉提数据源定案（历史决策存档，防翻案）**：
  · 画册两套页码：**文件序号 = 纸上印的页码 + 1**（`p36.webp` 印「35」）→ 混用必错一页
  · ⭐⭐⭐ **21-FO/20-V5 后缀跨产品线复用**（画册把两页的「实物图+箱规」块贴到了对方页）：
    梯桶 Ladder Barre 21-FO/20-V5 = Metal 1190×700×1170/85kg（实物见印35）；
    稳踏椅 Chair 21-FO/20-V5 = Metal 920×720×790/85kg（实物见印33）。
    定案三条判据缺一不可：分章连续性 / 箱规物理量级 / 后缀跨线复用。
    用户口头两个结论互相矛盾时**不要二选一**，去找能同时满足两者的读法（真解=两边都对）
  · 材质空写 `—`；FAQ 以 2026 画册为准；文案导向**客户定制品牌**（不把 A 词换 B 词：
    「材质按型号确定 → 见型号表材质列」+「也可按你品牌现用的材质与表面工艺生产」）
  · `Gyrotonic` 已剔除且是**两批**（站点 10 文件 + 生成源/词库——只改产物不改源=埋定时炸弹）；
    数据层「参与归组+输出过滤」；扫商标词含 ja 片假名/ko 谚文/「禅柔」+ 弯直引号两种形态
  · ⭐ 补信息 **A/C/D/E 许可分级**：A 画册原文可写、C 推导须标注、D 行业通用写「这类器械…」、
    **E 级禁止**（价格/MOQ/弹簧/承重/认证/保修/本体尺寸；抄竞品参数最危险）
  · ⛔ 重跑 `build_pilates_section.py` 会整段删除画册块（生成器无 `.cat-*` 模板）
  · 改文案必跑源⇄产物审计 `verify_pilates_source_vs_product_20261001.py`
  · OCR 分块：XY-cut 对对角摆放必失手 → 连通域兜底 `split_leaf_by_components()`，
    命中 37/38（仅文件 p25 手工标框）；复核报告存
    `i18n_build/reports/pilates_data_review_and_expand_plan_20261001.md`
- ✅ 已完成批次（8 分类页补内容 / SEO 存量清理 / GEO 端点 22/22、线上 GEO 78）见全量版
