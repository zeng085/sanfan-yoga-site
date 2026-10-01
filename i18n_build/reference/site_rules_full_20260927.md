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
