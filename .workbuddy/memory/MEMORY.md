# 三梵独立站 fjsanfan.com 长期笔记（精简 2026-09-13）

> 细节详见技能 `sanfansport-catalog-sync`（产品数据/建页）与 `fjsanfan-multilang-spec-sync`（多语言/博客）。

## 概况
- 仓库 zeng085/sanfan-yoga-site（可改 private），Vercel；B2B OEM/ODM 瑜伽垫/健身器材厂站
- EN 主站 + de/ja/ko/fr/it/es 6 语言子目录 + 中文同页 CSS 切换（无 /zh/ URL）
- 结构：147 产品页 + 10 分类页（**根目录**）+ products.html + 6 场景页（applications/，只从既有 SKU 挑，
  永不新增）+ materials.html + 10 blog + 首页；多语言 100% 对齐（每语言 180 页），sitemap 1267 条
- ⚠️ `.gitignore` 必须排除 `i18n_build/.deepl_key*`、`i18n_build/data/`（报价表 16M 商业机密）
- 体检脚本 `final_check` / `seo_deep_audit` / `seo_skill_checks` —— 页面上千后一律**后台跑**（前台超时 137）

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

## 坑清单
- BSD grep `\|` 交替静默失效 → 用 Python；CJK 相邻 `\b` 失效，替换要枚举语言后缀
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
