# 三梵独立站 fjsanfan.com 长期笔记（精简 2026-09-13）

> 细节详见技能 `sanfansport-catalog-sync`（产品数据/建页）与 `fjsanfan-multilang-spec-sync`（多语言/博客）。

## 概况
- 仓库 zeng085/sanfan-yoga-site（可改 private），Vercel；B2B OEM/ODM 瑜伽垫/健身器材厂站
- EN 主站 + de/ja/ko/fr/it/es 6 语言子目录 + 中文同页 CSS 切换（无 /zh/ URL）
- 结构：147 产品页 + 10 分类页（**根目录**）+ products.html + 6 场景页（applications/，只从既有 SKU 挑，
  永不新增）+ materials.html + 10 blog + 首页；多语言 100% 对齐（每语言 180 页），sitemap 1276 条
- ⭐ **`/pilates/` 普拉提大器械独立板块（2026-09-15 上线）**：9 页 = 版块首页 + 8 器械族页，
  8 族 / 41 型号（源自《2026年福建三梵普拉提大器械价格表（代理）》，**代理价不上站**）。
  与垫类五项隔离：URL 分区 / 分类条换 8 族 chip / 深墨+木色 `--pl-*` 配色 / 导航一级入口 / 面包屑。
  全站导航已注入一级入口 1268 页（EN 页带 8 族下拉，语言页只给裸入口）。
  ⚠️ 细节与流水线见技能 `fjsanfan-pilates-section`（含全部脚本与坑）
- ⚠️ `.gitignore` 必须排除 `i18n_build/.deepl_key*`、`i18n_build/data/`（报价表 16M 商业机密）
- 体检脚本 `final_check` / `seo_deep_audit` / `seo_skill_checks` / `bump_assets_ver` /
  `inject_pilates_nav` —— 页面上千后一律**后台跑**（前台 SIGTERM 137，单次约 4.5 分钟）

## 改动与推送
- 改 CSS/JS 必 bump `?v=`（`bump_assets_ver.py`，写法 `?v20260911f` 无等号）→ 一个干净 commit →
  `GH_PAT` 从 `git config --get-regexp '^url\.'` 的 insteadOf 取 token，再
  `push_api_v3.py zeng085/sanfan-yoga-site /abs/repo --auto`（参数顺序！裸 `--auto` 会 404）
  ⭐ 不要 `reset --soft`（自造死局）；diff 带 `--no-renames`

## 视觉定稿（勿翻案）
- 暖纸卡 `--paper:#f9f7f2` + `mix-blend-mode:multiply` + contain 内缩 4%，零描边零投影；能换图就别抠图
- ❌ 被否：全抠白 / 图外加边框 / 纸色更深。大图用原始素材；`.ct-thumbs` 缩略图用白底素材
- 图 WebP q75、最大边 900、`<slug>-<k>.webp`；下图前查同名撞车（32² 通道差 >20 即异图）

## 关键约定
1. 语言切换 `siteLang` 双写（localStorage+cookie）；`.lang-zh` 默认隐藏
2. EN 公制+英制，欧日韩纯公制；`"` 进 JSON-LD 转义
3. JSON-LD @graph Product+BreadcrumbList，offers=AggregateOffer（勿放 availability）
4. ⭐ `i18n_build/site_templates.py` 是唯一模板源，新页面必须走它
5. ⭐ 语言版页面易缺语言切换器 → 跑 `inject_lang_switch.py`（09-13 补 540 页，幂等）
6. ⭐ 博客页语言块结构固定 `article > (.lang-en | .lang-zh)`，**`.lang-zh` 必须在 `.container` 内**。
   单边页即故障：only-en → 切中文整篇白页（`html.show-zh .lang-en{display:none}`）；
   only-zh → 中文模式英文正文不隐藏、两个 h1 并列。09-13 修 10 篇，验收 `verify_listicle.cjs`
7. ⭐ `build_listicle.py` 已冻结（EN 页含 `.lang-zh` 即拒跑）；改榜单页走 `fix_listicle_20260913.py`
8. ⭐ 两种语言机制别混：products/applications/首页/blog 卡片用**行内配对 span**（天然成对，182 页 0 失衡）；
   **块级 `div.lang-zh` 只在 10 个 blog 文章页** —— 中文残块只会出在这。
   ⭐ 中/英字符比**已标定**：站内 1237 组人工忠实配对实测中位 **0.353**（四分位 0.30–0.44），
   即忠实中文译文本来就≈英文的 1/3（JA/EN 段级 0.54–0.67，CJK 天然密）。
   判定：**<0.25 = 残块 FAIL，<0.30 = 偏薄**。检查脚本 `i18n_build/check_zh_parity.py`（静态）+ `verify_listicle.cjs`（浏览器）。
   09-14 已把 9 篇博客中文块全量补齐（0.36–0.44，结构逐一相等），全站 158 页 0 FAIL。
   灌稿走 `i18n_build/apply_zh_blocks.py`（中文稿存 `i18n_build/zhblocks/`，只改 article-body 内层）
   ⚠️ 比字符数前必须先标定，别拿错误直觉去"修"正常内容

## 坑清单
- ⭐ **导航里别用 `::after` 加装饰**：`.nav-links a::after` 是悬停下划线（`position:absolute; bottom:-6px`），
  且 `.nav-links a:hover::after{width:100%}` 优先级更高 → 伪元素装饰会被拉成一条贯穿文字的斜线。用真实元素。
- ⭐ **带 `data-i18n` 的元素不能有子元素**：main.js 的 `applyLang` 对无标签值走 `el.textContent = val`，
  子元素会被整个抹掉。文案挂内层 span，图标/箭头放外面。
- ⭐ 导航文案在 EN 页走 `data-i18n` + main.js 字典（**不是** lang span）：
  nav 里 `.lang-zh` 会拿到 `display:block` 而打散行；lang span 只用于正文/chip。
- ⭐ 全站注入/替换脚本要写成**替换式**（先摘旧块再重插），别写成「只补缺」——否则改了标记后改不动存量页。
- BSD grep `\|` 交替静默失效 → 用 Python 或 `grep -E`；CJK 相邻 `\b` 失效，替换要枚举语言后缀
- Playwright 本机验收：**别用 `networkidle`**（GA 请求挂住永久超时）→ 拦 GA 路由 + `domcontentloaded`；
  中文态验收必须 `localStorage.siteLang='zh'` 后重载（`classList.add('show-zh')` 不触发 applyLang）
- 断言别写死导航下标：main.js 会往 `.nav-links` 最前面插 `.nav-search-item`（Home 是 1，Pilates 是 2）
- 产品页无 `<main>`：选择器用 `.pd-gallery img` / `table.spec-table th`
- 语言版标题→slug 匹配失败会静默回退 products.html → 重生成后跑 `fix_lang_card_links.py`
- EN 源页 `.container nav` 曾缺 `</div>`（147 页）已修，语言页 div 失衡随之清零
- ⚠️ `<a>` 嵌 `<a>`（分类页/博客索引历史坑）→ 浏览器提前闭合出空白卡，用 div 或重建
- padding 百分比包含块是父容器宽度 → `.sr-thumb` 用 `padding:4px`
- 计数文案（产品/SKU 数）散在**首页+6 场景页 ×7 语言**，改数要全局替换
- file:// 验收不可靠 → `python3 -m http.server 8848`（**后台**跑，前台会在调用结束时被杀）
- ⚠️ meta/description 的错会随翻译管线**原样传播**到 6 语言版 → 必须改 EN 源页再重生成
- ⚠️ 机翻会吃掉受保护术语旁的名词词尾：`alfombrillas→alfombrTPEes`、`tappetini→tappetTPE`、
  `schiuma→schiumPVCe`、`㎡e`。多语言页交付前用正则扫一遍

## 博客
- 10 篇 × 7 语言 = 70 页；重生成 `build_pages.py --batch`；索引卡 `blog_sync_index.py`（幂等）
- 8 篇旧文已重写去 AI 味并补答案块，老博客页补了 GA4
- ⚠️ CJK 答案块/字数检查按字符数（≥350），`split()` 词数失效

## SEO/GEO 现状
- canonical/hreflang/sitemap 健康；SEO 深检 0 问题；Schema 政策真问题 0（AggregateOffer = B2B 豁免）
- FAQPage 保留（富结果已退役，AI 引用仍有用）；榜单页仍零外链来源，待补
- 排名：8 核心词均未进前 5；**"SANFAN" 被 sanfanyoga.com（厦门同业）截流** → 对外用全称
  "FUJIAN SANFAN Sports Products"；对标 htsyoga.com（张家港浩通）的指南型长文路线
- 最高优先级数据 = 用户 GSC 截图（Indexed/not indexed）；CF 灰云直连 Vercel，`www.` NXDOMAIN 待修
