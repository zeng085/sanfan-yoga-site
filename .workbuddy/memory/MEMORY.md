# 三梵独立站 fjsanfan.com 长期笔记（2026-09-24）

> 细节见技能 `sanfansport-catalog-sync` / `fjsanfan-multilang-spec-sync` / `fjsanfan-pilates-section`。

## 概况
- 仓库 zeng085/sanfan-yoga-site → Vercel；B2B OEM/ODM 瑜伽垫/健身器材厂站；1331 页
- EN 主站 + de/ja/ko/fr/it/es 子目录 + 中文同页切换（无 /zh/ URL）；sitemap 1330 条
- ⚠️ `.gitignore` 排除 `i18n_build/.deepl_key*`、`i18n_build/data/`（16M 报价表机密）
- ⭐ 全站脚本**一律后台跑**

## 推送（细节见技能 github-api-push）
改 CSS/JS 先 `bump_assets_ver.py`（`?v20260911f` 无等号）→ 干净 commit →
`GH_PAT=$(cat ~/.workbuddy/secrets/gh_pat) python3 push_api_v3.py zeng085/sanfan-yoga-site <abs_repo> --auto`
（顺序不能换）。diff 带 `--no-renames`；**不要 `reset --soft`**（v2 残留，照做=死局）

## 导航（2026-09-16 定稿，勿翻案）
- ⭐ `.container.nav` **不能锁 `--maxw`**（放不下会换行挤到 logo 上）；
  **汉堡断点 1279px** 是实测标定（最宽的 es 需 1436），断点内必须还原 `nowrap/flex:none`
- ⭐ 下拉三件套：`::before` 补 12px 死缝 / `MEGA_CLOSE_DELAY=320ms` / 关闭路径 7 条
- ⭐ **目录索引 URL 一律用 `/x/`**，`/x/index.html` 会被 301

## 关键词口径：EVA≡TPE（2026-09-24，两轮才收口）
- ⚠️ 「EVA 独立板块」整版方案**已否决、全量回退**。真实意图只有一条：**行业口语里
  「EVA 瑜伽垫」就是同类 TPE 垫**，搜 EVA 落到 TPE 垫页。**不建 URL、不动页脚/实体层/sitemap**
- ✅ 落地：`tpe-yoga-mats.html`×7 加小节 + FAQPage + 描述补 EVA；`materials.html`×7 EVA 行改
  「EVA 名义下的垫按 TPE 供货」。**已推送（d0c4075213）**
- ⚠️ 措辞**不能**写「EVA 与 TPE 同一种材料」→ 只讲**叫法混用 + 按 TPE 报样 + EVA 专线做配件**

## 判据铁律
1. ⭐ **长度判据先问「对 CJK / 对译文成立吗」**：meta 按**显示宽度**（CJK×2，title 60 / desc 155）；
   「重复」须**按语言分组**
2. ⭐ **中英字符比中位 0.353（0.30–0.44）**，<0.25=残块 FAIL；比字数前先标定
3. ⭐ **EN 页的 `|`/`—` 常写成 HTML 实体**（`&#124;`）→ 只认字面会静默漏掉整个 EN 站
4. ⭐ **同一文件的多个 Edit 不能并行**：并行时只有最后一个落盘，另几处静默丢失
5. ⭐ **「同串同步」先数清有几份**：HTML 转义形态不同就不算同串 —— meta 与 JSON-LD 的
   description 天然是**两份串**（`&amp;` vs `&`）
6. ⭐ 替换式脚本：落盘前 `assert 'href="href="' not in out`；
   **先摘旧块再重插**；清洗规则**迭代到不动点**，错则先回滚再重跑
7. ⭐ **回退断言分插入/替换**：替换型必须 `replace(new, old, 1)==原文`；
   插入型要与摘块正则**严格互逆**（摘 `\n[ \t]*` 就得复用原位换行，否则每跑一次多一空行）
8. ⭐ **审计脚本先自审**：`url_path()` 漏映射裸 `index.html` → 首页误报；`noindex` 页不要求 hreflang
9. ⭐ **新内容别放进 `<!-- orgref:v1 -->` 标记区间**：`add_org_sameas_20260924.py` 会
   剥离整个区间再重建，区间内内容**静默丢失**；站内 328 个 FAQPage 都在标记之前
10. Playwright：**别用 `networkidle`**（拦 GA + `domcontentloaded`）；中文态须 `localStorage.siteLang='zh'` 后重载（**localStorage + cookie 双通道都设**）；折叠 `<details>` 展开前 `innerText` 为空；`evaluate` 必须**传函数引用+参数**（`f, x`）—— 写成 `f(x)` 会在 Node 端求值 → `localStorage is not defined`
11. ⭐ **清理类判据收紧到「引号内侧只有术语本身」**：`„TPE-Matte, violett, 6 mm“` / `«MOQ 100»` / `“EVA yoga mat”` / `"ROHS"` 都是**合法引用**，宽判据（"术语附近有引号"）会误杀。全站实测：105 处该清 / 27+231 处**不动**
12. ⭐ **「某语言独有」的形态先跨语言对照再定性**：「德语给标准名加引号」看着合语法，但 7 语言只有 de 有 → 机翻产物。**一致性才是口径**，不是语法
13. ⭐ **该不该换标签 → 先搜 CSS 有没有为「目标形态」准备好的选择器**：`site.css` 里 `.article h1, .article .lang-zh h2.post-title` 并列 → 中文块本就用 h2，是 HTML 误用。改后验 computed `font-size` 两态一致（40px/40px）
14. ⭐⭐ **源码审计归零 ≠ DOM 干净**：JS `createElement`/改属性产生的缺陷（如 `main.js:1140` 的 `menuItem.href='#'`）**不在 HTML 里**，`audit_links` 结构上不可能看到 → 必须补浏览器级探针 `querySelectorAll('a[href="#"], a:not([href])')`，且**按视口分别查**（1279px 断点内的元素桌面态不可见）
15. ⭐⭐ **「该改成什么」先搜同处现成写法，别推理**：`product.html` 的 wa 按钮 → 看 `products/*.html` 的 `#pd-wa-en` 与 `build_batch1.py` 模板；`menuItem.href` → 看**同文件** `main.js:1058`。搜到即用，天然与全站一致
16. ⭐⭐ **说「惯例」前先量化，且只在同类元素内成立**：WhatsApp 外链里 `c-link`（文字链）1317 处**带** `target="_blank"`，而同类按钮 `btn btn-ghost` **1029 处全不带** → 跨类对比会得出相反结论。清理类改动**只修缺陷**，行为变更单列征询

## 内容层结构（两种语言机制勿混）
- 行内配对 span：products/applications/首页/blog 卡片；块级 `div.lang-zh` **只在 10 个 blog 文章页**且在 `.container` 内
- ⭐ `i18n_build/site_templates.py` 是唯一模板源；`build_listicle.py` 已冻结
- ⭐ 带 `data-i18n` 的元素**不能有子元素**（applyLang 走 textContent 会整个抹掉）
- ⚠️ ⭐ **改完 EN 源页别用批次重生成语言页**：实测附带漂移 + `mymemory` 配额降级；
  缓存命中不调 API，投毒后重跑不自愈 → 语言版改动手写译文直接注入
- ⚠️ 机翻吃术语旁词尾（`alfombrTPEes`）→ 过 lint

## SEO/GEO 现状（2026-09-25 收口）
- 技术层已修平：404 / 跨语言 / 坏锚点 / 结构 / canonical / hreflang / **h1>1 全 0**；
  title>60 宽 **0**；**空 href 0**（三项审计全归零）
- ✅ 存量清理（2026-09-25 **已推送 `e416d1bc10`**）：
  「引号紧贴术语」**105 处已清**（de/pilates 90 + 6 个 blog 15）；
  EN 博客 **10 页双 h1 已降 h2.post-title**；**空 href 2 处已清**（见下）
  `audit_seo` **0 处**。脚本：`fix_quote_wrap_20260925.py` / `fix_blog_dual_h1_20260925.py`
- ⭐ 资源版本号现为 **`20260925a`**（改 JS 必 bump）
- ⚠️ 空 href 那 2 处**不在源码里**（一层是动态页兜底、一层是 JS `createElement`）：
  `product.html` 的 `#pd-wa` / `main.js:1140` 的 `menuItem.href`
- ⭐ **实体层铺满全站**：Organization + `@id=…/#organization` + sameAs 覆盖 1330 页；
  1085 个含 `Product` 的页补 `manufacturer`。sameAs 只放 `facebook.com/sanfanyoga`
- 已做：robots 11 AI UA / dateModified 70 页 / llms.txt / FAQ 1092 页
- ✅ **GEO 端点已补齐（2026-09-25）**：llms.txt 41 处裸 URL → markdown 链接（工具只认
  `[text](url)`，裸 URL 计 0）、新建 `llms-full.txt` + `.well-known/ai.txt` +
  `ai/{summary,faq,service}.json`；geo 判分 **22/22**（ai_discovery 6/6 + llms 16/16）
  ⚠️ **本地审不了**（geo 有反 SSRF，拒私网）→ 用 `verify_geo_endpoints_*.py` 抓响应喂解析函数
  ⚠️ **改 `faq.html` 后必须重跑** `geo_ai_endpoints_20260925.py`（faq.json 从它抽取）
- ⭐ **GEO 68 → 78**（2026-09-25 推 `d267a2b0d8` 后线上实测；Perplexity 43→50）。⚠️ `geo audit`
  展示层只打印 3 个 ai discovery 端点（漏 service.json），但判定层照样计分 →
  别以「没打印」判失败，用 `verify_geo_endpoints_*.py` 打线上复核
- ⚠️ **`desc>155 宽` 767 页（57%）** ← 最大存量缺口；根因是**译文膨胀**（EN 源多合格），主体 530 产品页
- ⚠️ 「答案块 134–167 词」是 EN 专属判据（fr/de/es/it 146–214、ja/ko 按字符），别跨语言套带宽

## ⭐ 英文站 SEO 达标基线（2026-09-25，勿重复体检技术层）
- 191 英文页逐页审计：**技术层 10 项零未达标** → **别再报「技术 SEO 有问题」**
- **进度：未达标 397 → 209 处**（结构类 A1–A5 清 177、desc 清 11）
  ⭐ 结构类已清零（H 层级 158 + 空 href 18 + blog 无 h2 1）→ `fix_en_seo_structure_20260925.py`
  （A1 1029 页 / A2 70 / A3 35 / A4 80 / A5 18，`--check` 必须 0 处）
  ⚠️ **A2 反例 49 文件**（6 个 `applications/*` + `products.html` × 7 语言）
     同样含 cat-head h3 但**前面已有 H2，层级正确 → 勿动**
- 剩余：**产品页正文中位 469 词**（115/147，全挤 403–540=模板化）；
  ⭐ 同站 `pilates/*.html` **792–1119 词** → 两套内容深度，短板在旧批次模板
- `desc>160 宽` **58 页**（EN 口径；已按内链权重修 11 个高权重页 → 138–152）；
  ⚠️ 语言版更重：fr 最高 **363** 宽、it **349**（译文膨胀，照搬 EN 无解）
- ⭐ **内链数 = 站内权重标尺**（免外部数据）：内链 ≥70 的 20 页就是全站流量入口
- ⭐ 资源版本号 **`20260925b`**（改 CSS/JS 必 bump）
- ⭐⭐ **改 HTML 标签必须成对**：只 `subn` 开标签 → `<h2>…</h3>` 不匹配，
  **dry-run / 幂等自检 / computed style 三处都抓不到**；浏览器忽略 `</h3>` 后 h2 会
  **吞掉后面的 `<table>`**。落盘后必须断言 `<X` 与 `</X>` 的增减一致 + 看「结构守恒签名」
- ⭐⭐ **改后核查三件套**（用户问「有没有影响」时必跑）：
  `verify_changes_scope_*.py`（difflib 逐块证「无夹带」）/ `verify_tag_balance_*.py` /
  `scan_overflow_*.cjs --vp=390`（判「改动点是否溢出」，非「页面有无超宽元素」）
- ⭐⭐ **「既有问题」必须 A/B 实证**：把 HEAD 版导出到**同目录**新文件（相对路径不变），
  同判据对比 → 一致才是既有。禁止用「我没改这里」推断
- 工具：`audit_en_seo_standard_20260925.py` / `report_en_seo_20260925.py` /
  `fix_en_seo_structure_20260925.py` / `fix_high_weight_desc_20260925.py` /
  `verify_multilang_headings_20260925.cjs` / `audit_links_20260916.py`（61218 链接全 0）
- ⚠️ 坑：hreflang 存在性字典必须**全站**铺（只装英文页 → 假报 1140 处）；
  页面类型**别靠目录名判**（pilates/ 是产品页）；词数用**静态口径**（Google 索引 `<details>`）
- ⚠️ **2 个既有缺陷待修**（A/B 已证非改动引入）：48 个语言版文章页缺 `</article>`；
  17 处移动端横向溢出（宽表格，根因 `body{overflow-x:clip}` 裁掉且不可滚）
- ⚠️ 改标签前**先搜 CSS 有没有为目标形态准备的选择器**；
  `.faq-cat` 的样式写在 `faq.html` **页内 style** 里（类选择器，不限定标签 → 改标签零影响）

## ✅ 8 个一级分类页补内容 —— 7 语言全部完成，已提交（2026-09-25，`a7cc81bd`）

方案 = `i18n_build/reports/category_content_plan_20260925.md`（第十一节＝执行记录）
验收 = `i18n_build/reports/category_content_verification_20260925.md`

- ✅ **7 语言全部落盘**：56 文件（8 页 × 7 语言目录），共 **768 条译文**
  （de 3718 / ja 301 / ko 2768 / fr 4560 / it 4343 / es 4451 词）
- ✅ 词数 177–356 → **685–862**（全进 600–1200）；H2 1 → **4**；
  审计未达标 **397 → 201**；8 页**各 0 项未达标**；块覆盖 catintro 56 / cfaq 70 / cfaq-ld 70 / ilink 154
- ⭐⭐ **配额的解法 = 让生成脚本自己「没事可做」**：预填 `category_content_data.json`
  使 `build_data()` 的 `todo == []` → **完全绕过 `translate_lines`，零 API、零配额、零缓存污染**
  （实测配额仍 500000/500000、缓存仍 26369）。手写译文放 `catcontent_i18n/<lang>.json`
- ⭐⭐ **数据文件格式必须镜像目标结构（位置无关）**：用 `{页名: {…}}` **而不是**「128 条顺序数组」——
  顺序数组一旦 off-by-one 整页错位，而脚本自身的条数/JSON-LD/配平断言**全都抓不到**
- 脚本：`add_category_content_20260925.py`（`--langs` 分批）／`inject_category_content_i18n_20260925.py`
  （手写译文 → data json，含回声/占位符/引号/长度比/尖括号质检）／
  `verify_catcontent_i18n_20260925.py`（独立验收，见下）
- ⚠️ 执行顺序**不能换**：`add_internal_links` **先跑**（造 `<!-- ilink:v1 -->`）→
  再跑 `add_category_content`（cfaq 锚点写死就是它）
- ⭐ 导语块插在**网格之前**（实测 390×844 第 **1.06–1.58 屏**）；FAQ 在网格之后（3.9–8.6 屏）
- ⭐ 非垫类 6 页用 `cat_h2_gear`("Sourcing guides for buyers")，**不是** "choosing a mat"
- ⚠️ 内容纪律：8 页**都有** `MOQ 100 pcs`；页面自身**都没有** `ROHS/CE/ISO 9001` → 检测类不列标准号
- ⏸ `ilink` 热区修法（`inline-block + padding:6px 0` → 44px）**未做**：行为变更，需单列批准。
  ⚠️ 站内 12 个分类页热区**一致**（18–19px），不修反而无「两种尺寸并存」问题

### ⭐⭐ 本轮新增工具铁律（三条，都是踩过才写的）

1. **范围核查（difflib）必须把「受管区块」在 difflib 之前整段抽出**，不能塞进 `norm()`：
   difflib 按**公共行**切分，插入的 FAQ 块里满是与页面其它处相同的行（`    </div>` 等）
   → 插入块被**切成碎片**，碎片里凑不齐成对开/闭标记 → `norm()` 抽不掉 → 全误报。
   （实测：整文件 `norm()` 能抽掉，逐碎片抽不掉。）抽出后本脚本证明的命题**更强**：
   「受管区块之外的一切，除已知变换外一字未动」
2. **独立验收器不许复用被验脚本的判据函数** —— 脚本自检只能证明「按它的假设成立」。
   `verify_catcontent_i18n` 重写了 14 项判据（含 **JSON-LD 问答文本 == 页面可见文本**逐条对账，
   防「两套文案」），并做「同一文件 HEAD→工作区 标签增减签名必须**全组同一个**」
3. **「混入中文」不能用「含 CJK」判** —— 日语正文**必须**含汉字（kanji 属 CJK 区）。
   起初用 `cjk>0` 判日语 → 168 组合里 24 个 ja 全误报。改用**简体特有字**集合
   （长/车/东/业/产/质/价/单/类…，标准日语不用）
4. **结构守恒判据用「白名单签名 + 配平不变量」**，别用一串 `if` 规则：
   新内容会合法地加 16 个 div，旧规则「div 必须 = -h3」直接误杀 56 文件

### ⭐ 标题跳级：先 A/B，再全站量化，别急着改

- 全站实测：**h2→h4 有 1166/1364 页（85%）**（产品卡是 h4、网格节自身无标题）、h2→h5 1332 页
  → 属**既有形态**，审计标准也**没有**跳级幅度规则（只有 B1 h1 / B2 泛化 h1 / B3 h2<2 / B4 反序 / B5 面包屑）
- tpe/pu ×7 语言 14 文件变成 **h1→h4**：A2 去掉 cat-title 标题后的直接结果。
  ⭐ 三选一里最优：保留 h3（层级反序，B4 挂）/ 升为 h2（**与 h1 逐字重复**）/ 去掉标题（当前）
- 8 个分类页 h1→h3 **消失**（A2 修好），换来 h2→h4（全站既有形态）→ 记为**改善 + 已知残留**

## ⭐ 移动端判据（2026-09-25 实测得出，勿再靠推断）

- ⭐⭐ **内容位置看「距页顶几屏」，不看「在第几个区块后面」**：390×844 下
  `yoga-props`（23 卡）导语在第 **6.5 屏**、FAQ 第 **7.5 屏**（320px 下 FAQ 第 **12 屏**）；
  根因是产品网格自身 5.2 屏。**已修订：导语上移到网格之前**（6.5→**1.2** 屏，代价网格 1.2→2.2 屏）
- ⭐⭐ **inline 元素热区 ≠ 行高**：`ilink` 的 `<a>` 真实可点区间仅 **18–19px**
  （WCAG 2.5.8 AA 下限 24px；tpe 页实测 19px，2026-09-25 补的 8 页实测 18px）；
  **把 `line-height` 挪到 a 上完全无效**（实测仍 19px）——inline 命中区 = 字形 content area。
  唯一修法 `display:inline-block; padding:6px 0` → **44px**（代价 ul 96→132px）。
  ⚠️ 这是**样板页 tpe/pu 的既有缺陷**，8 页补内容时原样继承了 → 站内 12 个分类页**都是 18–19px**，
  **没有两种尺寸并存**；要修就 12 页 + `styles.css` 一起改 + bump 版本号到 `c`
- ⭐ 测法用 `elementFromPoint` 逐点扫（±34px 窗口，窗口窄会截断结果）；
  `rect.height` 只作参考
- ⚠️ 探测三陷阱：`html{scroll-behavior:smooth}` 让程序化滚动**异步** → 同步读 rect 拿到旧位置，
  逐点扫描**静默返回 0**；块内含 `<details>` 会骗过「.faq-list」特征判据 → **改用相对位置取块**
- 资源版本号现为 **`20260925b`**（再改 CSS/JS 要 bump 到 c）

## ⚠️ 站内搜索存在（勿再说「没有」）

- 全 JS 注入（`main.js`，模态框 `.sr-results`），HTML 里 **0 处痕迹**；索引 `assets/data/navdata*.js`
  的 `window.SANFAN_NAV`（`total:147`，7 语言各一份）→ **又一处「JS 生成 ⇒ 源码审计看不见」**
- 但**无 URL 深链**（无 pushState/query）→ `SearchAction` 仍不能加，加前得先做可深链搜索

## ⭐ AI 引用基线（首测 2026-09-25，`geo_citation_baseline_20260925.py`）
- **新站 fjsanfan.com 0 次**（9 查询/60 席位 + 4 次真 AI 提问）；老站 sanfanyoga.com
  3 检索席位 + **被秘塔实名引用为来源** → 问题是「AI 把三梵归因老站/平台」，非「不认识」
- 通道：❌ Perplexity/ChatGPT/Gemini/Google **本机全不可达**（DNS 污染成 Facebook IP）；
  ✅ `html.duckduckgo.com`（走服务端）+ ✅ 秘塔 metaso.cn；❌ cn.bing.com 返中国区结果
- ⭐⭐ **秘塔来源域名只能抓 favicon**：`cdn.metaso.cn/favicon/<域名>.ico`（卡片无 href）
- ⭐⭐ **采样失败 ≠ 无提及**（秘塔 ~6 次后限流返空壳）；**别拿自写备注做匹配**（会假报 100%）
