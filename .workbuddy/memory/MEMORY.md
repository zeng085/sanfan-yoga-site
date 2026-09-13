# 三梵独立站 fjsanfan.com 长期笔记（精简 2026-09-13）

> 详见技能 `sanfansport-catalog-sync` / `fjsanfan-multilang-spec-sync`。

## 概况
- 仓库 zeng085/sanfan-yoga-site（可改 private），Vercel；B2B OEM/ODM 瑜伽垫/健身器材厂站
- EN 主站 + de/ja/ko/fr/it/es 6 语言子目录 + 中文同页 CSS 切换（无 /zh/ URL）
- 结构：147 产品页（products/）+ 10 分类页（**根目录**）+ products.html 总览 + 6 场景页（applications/，
  只从既有 SKU 挑，永不新增）+ materials.html + 10 blog + 首页
- 多语言 100% 对齐（每语言 180 页）；sitemap 1267 条；DeepL 第二 key 月余约 29 万字符
- 翻译缓存按文本命中，换 key 不丢缓存
- ⚠️ `.gitignore` 必须排除 `i18n_build/.deepl_key*`、`i18n_build/data/`（报价表 16M 商业机密）
- 体检脚本：`final_check` / `seo_deep_audit` / `seo_skill_checks`（Schema政策+内容质量+GEO）
  —— 页面上千后一律**后台跑**（前台超时 137）

## 改动与推送
- 改 CSS/JS 必 bump `?v=`（`bump_assets_ver.py`，写法 `?v20260911f` 无等号）→ 一个干净 commit
  → `GH_PAT` 从 `git config --get-regexp '^url\.'` 的 insteadOf 取 token，再
  `push_api_v3.py zeng085/sanfan-yoga-site /abs/repo --auto`（参数顺序！裸 --auto 会 404）
  ⭐ 不要 `reset --soft`（自造死局）；diff 带 `--no-renames`
- 建页固定顺序：`apply_batchN_listing` → `build_category_pages` → **`fix_ct_thumbs`** →
  `build_navdata` → `bump_assets_ver` → `final_check`

## 英文站 sanfansport.com（产品数据唯一权威源）
- WP+WooCommerce，REST `/wp-json/wp/v2/product`；规格在 content.rendered 两列表格
- ⭐⭐ 41/167 空壳页（content 空、0 规格）→ 绝不编造数值，只上兜底 3 行；剩 12 未建页全是空壳，**暂停堆产品**
- 价格只认 offer 页（FOB Xiamen USD）；offers = 基准×0.7~1.3，正文不出数字
- 判「已上线」用 `probe_md5.py` md5 比对，别用 slug 差集（会假报未上线）
- 图不可达时用 `images.weserv.nl/?url=`（不带参数才透传原图字节）

## 视觉定稿（勿翻案）
- 暖纸卡 `--paper:#f9f7f2` + `mix-blend-mode:multiply` + contain 内缩 4%，零描边零投影；能换图就别抠图
- ❌ 被否：全抠白 / 图外加边框 / 纸色更深。大图用原始素材；`.ct-thumbs` 缩略图用白底素材
- 图片 WebP q75、最大边 900、`<slug>-<k>.webp`；下图前查同名撞车（32×32 通道差 >20 即异图）

## 关键约定
1. 语言切换 `siteLang` 双写；`.lang-zh` 默认隐藏
2. EN 公制+英制，欧日韩纯公制；`"` 进 JSON-LD 转义
3. JSON-LD @graph Product+BreadcrumbList，offers=AggregateOffer（勿放 availability）
4. ⭐ `i18n_build/site_templates.py` 是唯一模板源，新页面必须走它
5. ⭐ 语言版页面易缺语言切换器 → 跑 `inject_lang_switch.py`（09-13 补 540 页，幂等）

## 坑清单
- BSD grep `\|` 交替静默失效 → 用 Python；CJK 相邻 `\b` 失效，替换要枚举语言后缀
- 产品页无 `<main>`：选择器用 `.pd-gallery img` / `table.spec-table th`
- 语言版标题→slug 匹配失败会静默回退 products.html → 重生成后跑 `fix_lang_card_links.py`
- **EN 源页头部 `<div class="container nav">` 曾缺 `</div>`（147 页）**，已修；语言页失衡随之清零
- ⚠️ `<a>` 嵌 `<a>`（分类页/博客索引历史坑）→ 浏览器提前闭合出空白卡，用 div 或重建
- padding 百分比包含块是父容器宽度 → `.sr-thumb` 用 `padding:4px`
- 计数文案（产品/SKU 数）散在**首页+6 场景页 ×7 语言**，改数要全局替换
- file:// 验收不可靠 → 用 `python3 -m http.server 8848`

## 博客（09-13 全语言同步）
- 10 篇 × 7 语言 = 70 页；重生成 `build_pages.py --batch`；索引卡 `blog_sync_index.py`（幂等）
- 8 篇旧文已专业化重写（去 AI 味、每篇补 128–147 词答案块）；老博客页补了 GA4
- ⚠️ CJK 答案块/字数检查按字符数（≥350），`split()` 词数失效

## SEO/GEO 现状
- canonical/hreflang/sitemap 健康；SEO 深检 0 问题；Schema 政策真问题 0（AggregateOffer 714 条 = B2B 豁免）；
  内容质量 89.8 分
- GEO 短板已由新博客的答案块补齐；FAQPage 保留（富结果 2026-05 退役，但 AI 引用仍有用）
- 排名：8 核心词均未进前 5；**"SANFAN" 被 sanfanyoga.com（厦门同业）截流** → 对外用全称
  "FUJIAN SANFAN Sports Products"
- 对标 htsyoga.com（张家港浩通）：指南型长文路线已验证，是我们的内容模板
- 最高优先级数据 = 用户 GSC 截图（Indexed / not indexed）；DNS 走 CF 灰云直连 Vercel，`www.` NXDOMAIN 待修
