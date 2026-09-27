# 三梵独立站 fjsanfan.com 长期笔记

> 细节见技能：`sanfansport-catalog-sync` / `fjsanfan-multilang-spec-sync` / `fjsanfan-pilates-section` /
> `github-api-push` / `fjsanfan-mobile-ui-audit`。**改 CSS/JS 前必读 `fjsanfan-mobile-ui-audit`（含移动端基线）**。

## 概况
- 仓库 zeng085/sanfan-yoga-site → Vercel；B2B OEM/ODM 瑜伽垫/健身器材厂站；1331 页
- EN 主站 + de/ja/ko/fr/it/es 子目录 + 中文同页切换（无 /zh/ URL）；sitemap 1330 条
- ⚠️ `.gitignore` 排除 `i18n_build/.deepl_key*`、`i18n_build/data/`（16M 报价表机密）
- ⭐ 全站脚本**一律后台跑**；⭐ **资源版本号现为 `20260927a`**（改 CSS/JS 必 bump）

## 推送（细节见技能 github-api-push）
改 CSS/JS 先 `bump_assets_ver.py`（写法 `?v20260927a`，**没有等号**）→ 干净 commit →
`GH_PAT=$(cat ~/.workbuddy/secrets/gh_pat) python3 push_api_v3.py zeng085/sanfan-yoga-site <abs_repo> --auto`
（顺序不能换，bump 必须**与改 CSS 同一个 commit**）。diff 带 `--no-renames`；**不要 `reset --soft`**（v2 残留，照做=死局）

## 导航（2026-09-16 定稿，勿翻案）
- ⭐ `.container.nav` **不能锁 `--maxw`**；**汉堡断点 1279px**（实测标定，最宽 es 需 1436），断点内还原 `nowrap/flex:none`
- ⭐ 下拉三件套：`::before` 补 12px 死缝 / `MEGA_CLOSE_DELAY=320ms` / 关闭路径 7 条
- ⭐ **目录索引 URL 一律用 `/x/`**，`/x/index.html` 会被 301

## 关键词口径：EVA≡TPE（2026-09-24 两轮才收口）
- ⚠️ 「EVA 独立板块」整版方案**已否决、全量回退**。真实意图只有一条：**行业口语里「EVA 瑜伽垫」
  就是同类 TPE 垫** → 搜 EVA 落到 TPE 垫页。**不建 URL、不动页脚/实体层/sitemap**
- ✅ 落地：`tpe-yoga-mats.html`×7 加小节 + FAQPage + 描述补 EVA；`materials.html`×7 EVA 行改
  「EVA 名义下的垫按 TPE 供货」。已推送 `d0c4075213`
- ⚠️ 措辞**不能**写「EVA 与 TPE 同一种材料」→ 只讲**叫法混用 + 按 TPE 报样 + EVA 专线做配件**

## 判据铁律
1. ⭐ **长度判据先问「对 CJK / 对译文成立吗」**：meta 按**显示宽度**（CJK×2，title 60 / desc 155）；「重复」须**按语言分组**
2. ⭐ **中英字符比中位 0.353（0.30–0.44）**，<0.25=残块 FAIL；比字数前先标定
3. ⭐ **EN 页的 `|`/`—` 常写成 HTML 实体**（`&#124;`）→ 只认字面会静默漏掉整个 EN 站
4. ⭐ **同一文件的多个 Edit 不能并行**：并行时只有最后一个落盘，另几处静默丢失
5. ⭐ **「同串同步」先数清有几份**：meta 与 JSON-LD 的 description 天然是**两份串**（`&amp;` vs `&`）
6. ⭐ 替换式脚本：落盘前 `assert 'href="href="' not in out`；**先摘旧块再重插**；清洗规则**迭代到不动点**，错则先回滚再重跑
7. ⭐ **回退断言分插入/替换**：替换型必须 `replace(new, old, 1)==原文`；插入型要与摘块正则**严格互逆**
8. ⭐ **审计脚本先自审**：`url_path()` 漏映射裸 `index.html` → 首页误报；`noindex` 页不要求 hreflang
9. ⭐ **新内容别放进 `<!-- orgref:v1 -->` 标记区间**：org 脚本会剥离整个区间再重建，区间内内容**静默丢失**
10. Playwright：**别用 `networkidle`**（拦 GA + `domcontentloaded`）；中文态须 `localStorage.siteLang='zh'` 后重载（**localStorage + cookie 双通道**）；折叠 `<details>` 展开前 `innerText` 为空；`evaluate` 必须**传函数引用+参数**（`f, x`）—— 写成 `f(x)` 会在 Node 端求值
11. ⭐ **清理类判据收紧到「引号内侧只有术语本身」**：`„TPE-Matte, violett, 6 mm“` / `«MOQ 100»` 都是**合法引用**，宽判据会误杀（全站实测 105 处该清 / 258 处**不动**）
12. ⭐ **「某语言独有」的形态先跨语言对照再定性**：7 语言只有 de 有的形态 = 机翻产物。**一致性才是口径**，不是语法
13. ⭐ **该不该换标签 → 先搜 CSS 有没有为「目标形态」准备好的选择器**；改后验 computed `font-size` 两态一致
14. ⭐⭐ **源码审计归零 ≠ DOM 干净**：JS `createElement`/改属性产生的缺陷（`main.js:1140` 的 `menuItem.href='#'`、**JS 注入的 `.cbar`**、全 JS 的站内搜索）**不在 HTML 里** → 必须补浏览器级探针，且**按视口分别查**
15. ⭐⭐ **「该改成什么」先搜同处现成写法，别推理**：搜到即用，天然与全站一致
16. ⭐⭐ **说「惯例」前先量化，且只在同类元素内成立**：`c-link`（文字链）1317 处**带** `target="_blank"`，同类按钮 `btn btn-ghost` **1029 处全不带** → 跨类对比会得出相反结论。清理类**只修缺陷**，行为变更单列征询
17. ⭐⭐ **bump 必须与改 CSS/JS 同一个 commit**：`a7cc81bd` 扩了选择器却漏 bump → 线上仍是旧号，**用户命中缓存旧 CSS，新样式完全不生效**（HTML 改了但看着没变）
18. ⭐⭐ **本地 `origin/main` 是陈旧缓存**：推送走 REST API 建独立 commit，**不更新本地 ref** → `git log origin/main..HEAD` 报「待推 65 个」全是假象。正确：① 远程 HEAD message 匹配本地 commit；② **逐 blob sha 比对**远程 tree vs `git ls-tree -r`；③ 推送清单两法交叉验证
19. ⭐⭐ **浮层加 `overscroll-behavior` 前先确认它自己会滚**：`overflow:visible` 的浮层加了无效（滚的是页面，实测穿透 600px）。必须**同时**给 `max-height + overflow-y:auto`。且查 `.site-header` 是否 `sticky` —— 是的话浮层 `absolute` 跟着固定 → **页面滚到底也够不着溢出部分**
20. ⭐⭐ **CSS 是单文件共享 → 做不到「单页样本」**。替代三件套：① `--dry-run` 看影响面；② 多页 × 多视口实测（**必含 844×390 横屏**）；③ A/B 截图用**路由拦截喂 `git show HEAD:` 版文件**（零文件改动）
21. ⭐ 工具坑：**`grep -r` 会扫 `.git`（338MB）→ SIGTERM**（查版本号残留用脚本 `--dry-run`）；**`bump_assets_ver.py` 被超时杀掉会静默停半途**（无「已完成」标记）→ 判定补完**只能看 `--dry-run` 分布是否单一项**

## 内容层结构（两种语言机制勿混）
- 行内配对 span：products/applications/首页/blog 卡片；块级 `div.lang-zh` **只在 10 个 blog 文章页**且在 `.container` 内
- ⭐ `i18n_build/site_templates.py` 是唯一模板源；`build_listicle.py` 已冻结
- ⭐ 带 `data-i18n` 的元素**不能有子元素**（applyLang 走 textContent 会整个抹掉）
- ⚠️ ⭐ **改完 EN 源页别用批次重生成语言页**：实测附带漂移 + `mymemory` 配额降级；缓存命中不调 API，**投毒后重跑不自愈** → 语言版改动手写译文直接注入
- ⚠️ 机翻吃术语旁词尾（`alfombrTPEes`）→ 过 lint

## SEO / GEO 现状（2026-09-25 收口）
- 技术层已修平：404 / 跨语言 / 坏锚点 / canonical / hreflang / **h1>1 = 0** / title>60 宽 **0** / **空 href 0**
- ⭐ **实体层铺满全站**：Organization + `@id=…/#organization` + sameAs 覆盖 1330 页；1085 个含 `Product` 的页补 `manufacturer`。sameAs 只放 `facebook.com/sanfanyoga`
- ✅ **GEO 端点齐全**：`llms.txt`（41 处裸 URL → markdown 链接，工具**只认 `[text](url)`**）+ `llms-full.txt` + `.well-known/ai.txt` + `ai/{summary,faq,service}.json`；判分 **22/22**；线上实测 GEO **78**
  ⚠️ **本地审不了**（geo 有反 SSRF 拒私网）→ 用 `verify_geo_endpoints_*.py` 抓响应喂解析函数
  ⚠️ **改 `faq.html` 后必须重跑** `geo_ai_endpoints_20260925.py`（`faq.json` 从它抽取）
- ⚠️ **`desc>155 宽` 最大存量缺口**（767 页 / 57%），根因是**译文膨胀**（EN 源多合格）；语言版更重（fr 最高 363 宽、it 349，照搬 EN 无解）
- ⚠️ 「答案块 134–167 词」是 **EN 专属**判据（fr/de/es/it 146–214、ja/ko 按字符），别跨语言套带宽
- ⚠️ 空 href 有 2 处**不在源码里**：`product.html` 的 `#pd-wa`（动态页兜底）/ `main.js:1140` 的 `menuItem.href`

## ⭐ 英文站 SEO 基线（2026-09-25，勿重复体检技术层）
- 191 英文页逐页审计：**技术层 10 项零未达标** → **别再报「技术 SEO 有问题」**
- 未达标 **397 → 209 处**；**结构类已清零**（H 层级 158 + 空 href 18 + blog 无 h2 1）→ `fix_en_seo_structure_20260925.py --check` 必须 0 处
  ⚠️ **A2 反例 49 文件**（6 个 `applications/*` + `products.html` × 7 语言）：同样含 cat-head h3 但**前面已有 H2 → 勿动**
- 剩余：**产品页正文中位 469 词**（115/147 挤在 403–540=模板化）；⭐ 同站 `pilates/*.html` **792–1119 词** → 短板在旧批次模板
- ⭐ **内链数 = 站内权重标尺**（免外部数据）：内链 ≥70 的 20 页就是全站流量入口
- ⭐⭐ **改 HTML 标签必须成对**：只 `subn` 开标签 → `<h2>…</h3>` 不匹配，**dry-run / 幂等自检 / computed style 三处都抓不到**；浏览器忽略 `</h3>` 后 h2 会**吞掉后面的 `<table>`**。落盘后断言 `<X` 与 `</X>` 增减一致
- ⭐⭐ **改后核查三件套**：`verify_changes_scope_*.py`（difflib 证「无夹带」）/ `verify_tag_balance_*.py` / `scan_overflow_*.cjs --vp=390`
  ⭐ 更直接的等价核查：`git diff -U0 -- '*.html' | grep -E '^[+-][^+-]'` 计数——**`+`/− 行数必须配对**，且归一化后只剩预期模式
- ⭐⭐ **「既有问题」必须 A/B 实证**：把 HEAD 版导出到**同目录**新文件，同判据对比 → 一致才是既有。禁止用「我没改这里」推断
- 工具：`audit_en_seo_standard_20260925.py` / `fix_en_seo_structure_20260925.py` / `fix_high_weight_desc_20260925.py` / `audit_links_20260916.py`（61218 链接全 0）
- ⚠️ 坑：hreflang 存在性字典必须**全站**铺（只装英文页 → 假报 1140 处）；页面类型**别靠目录名判**（`pilates/` 是产品页）；词数用**静态口径**（Google 索引 `<details>`）
- ⚠️ 既有缺陷待修（A/B 已证非改动引入）：48 个语言版文章页缺 `</article>`；17 处移动端横向溢出（宽表格，`body{overflow-x:clip}` 裁掉且不可滚）

## ✅ 已完成的批次（结论，细节在报告）
- **8 个一级分类页补内容**（2026-09-26 推 `b94f9879d5`，1381 文件）：7 语言 56 文件 768 条译文；词数 177–356 → **685–862**；H2 1→**4**；审计未达标 397→**201**，8 页**各 0 项未达标**
  方案/验收 = `i18n_build/reports/category_content_{plan,verification}_20260925.md`
  ⭐⭐ **配额解法 = 让生成脚本「没事可做」**：预填 `category_content_data.json` 使 `todo == []` → **完全绕过 `translate_lines`，零 API/配额/缓存污染**；手写译文放 `catcontent_i18n/<lang>.json`
  ⭐⭐ **数据文件格式必须镜像目标结构（位置无关）**：用 `{页名:{…}}` 而非「顺序数组」—— off-by-one 整页错位时，**脚本自身的条数/JSON-LD/配平断言全都抓不到**
  ⚠️ 顺序不能换：`add_internal_links` **先跑**（造 `<!-- ilink:v1 -->`）→ 再跑 `add_category_content`（cfaq 锚点写死就是它）
  ⭐ 非垫类 6 页用 `cat_h2_gear`("Sourcing guides for buyers")，**不是** "choosing a mat"；8 页**都有** `MOQ 100 pcs`、**都没有** `ROHS/CE/ISO 9001`
  ⏸ `ilink` 热区修法**未做**（行为变更需单列批准）；⚠️ 站内 12 个分类页热区**一致**（18–19px），不修反而无「两种尺寸并存」
- **SEO 存量清理**（2026-09-25 推 `e416d1bc10`）：引号紧贴术语 105 处已清；EN 博客 10 页双 h1 已降 h2.post-title；空 href 2 处已清
- ⭐⭐ 三条工具铁律（分类页那轮踩出来）：① **difflib 范围核查必须把「受管区块」在对比前整段抽出**（否则插入块被切成碎片 → 全误报）；② **独立验收器不许复用被验脚本的判据函数**（脚本自检只能证明「按它的假设成立」）；③ **「混入中文」不能用「含 CJK」判**（日语正文必须含汉字）→ 改用**简体特有字**集合；④ 结构守恒用「白名单签名 + 配平不变量」，别用一串 `if`

## ⭐ 移动端（2026-09-25 实测得出，2026-09-27 P0 已修）
- ✅ **P0 五处已修并提交 `f9f4b3dc`**（`styles.css` 单文件 +36/−7，随 bump `20260927a`）：
  `touch-action:manipulation`（2001 元素全覆盖）/ 汉堡·logo·语言切换 **40→44px** / 表单 input **15→16px** /
  抽屉 `max-height:calc(100dvh-68px)` + `overflow-y:auto` + `overscroll-behavior:contain` /
  ≤920px 抽屉再减 **54px 让开 `.cbar`**。无回归：header 仍 69px、横向溢出全 0
  ⏭ 未做 P1/P2（`:focus-visible` / `scroll-margin-top` / `prefers-reduced-motion` / `safe-area` /
  `tabular-nums` / `tap-highlight-color` / `text-wrap:balance` / `translate="no"` / `theme-color` /
  `preconnect` / 491 张图补尺寸 / `a.c-link` 17px 扩热区）→ 见 `reports/p0_mobile_fixes_20260927.md` §6
- ⭐⭐ **内容位置看「距页顶几屏」，不看「在第几个区块后面」**：390×844 下曾测出导语在第 6.5 屏、FAQ 第 7.5 屏（320px 下 12 屏）→ **已修订：导语上移到网格之前**（6.5→1.2 屏）
- ⭐⭐ **inline 元素热区 ≠ 行高**：`ilink` 的 `<a>` 真实可点区间仅 **18–19px**（WCAG 2.5.8 AA 下限 24px）；**把 `line-height` 挪到 a 上完全无效** —— inline 命中区 = 字形 content area。唯一修法 `display:inline-block; padding:6px 0` → **44px**
- ⭐ 测法用 `elementFromPoint` 逐点扫（±34px 窗口，窗口窄会截断结果）；`rect.height` 只作参考
- ⚠️ 探测三陷阱：`html{scroll-behavior:smooth}` 让程序化滚动**异步** → 同步读 rect 拿到旧位置、逐点扫描**静默返回 0**；块内含 `<details>` 会骗过「.faq-list」特征判据 → **改用相对位置取块**
- ⚠️ **320px 下 `de/index.html` 溢出 57px**（既有问题）→ **必须同时跑 320 与 390**（译语膨胀，只测 390 看不到）

## ⚠️ 站内搜索存在（勿再说「没有」）
- 全 JS 注入（`main.js`，模态框 `.sr-results`），HTML 里 **0 处痕迹**；索引 `assets/data/navdata*.js` 的 `window.SANFAN_NAV`（`total:147`，7 语言各一份）→ 又一例「JS 生成 ⇒ 源码审计看不见」
- 但**无 URL 深链**（无 pushState/query）→ `SearchAction` 仍不能加，加前得先做可深链搜索

## ⭐ AI 引用基线（首测 2026-09-25，`geo_citation_baseline_20260925.py`）
- **新站 fjsanfan.com 0 次**（9 查询/60 席位 + 4 次真 AI 提问）；老站 sanfanyoga.com 3 席位 + **被秘塔实名引用为来源** → 问题是「AI 把三梵归因老站/平台」，非「不认识」
- 通道：❌ Perplexity/ChatGPT/Gemini/Google **本机全不可达**（DNS 污染成 Facebook IP）；✅ `html.duckduckgo.com`（走服务端）+ ✅ 秘塔 metaso.cn；❌ cn.bing.com 返中国区结果
- ⭐⭐ **秘塔来源域名只能抓 favicon**：`cdn.metaso.cn/favicon/<域名>.ico`（卡片无 href）
- ⭐⭐ **采样失败 ≠ 无提及**（秘塔 ~6 次后限流返空壳）；**别拿自写备注做匹配**（会假报 100%）
