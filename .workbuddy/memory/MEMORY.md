# 三梵独立站 fjsanfan.com 长期笔记（精简版 2026-09-13）

> 完整工作流已固化到技能 **`sanfansport-catalog-sync`** 与 **`fjsanfan-multilang-spec-sync`**。
> 详细历史见 `memory/` 日志（2026-09-11/12/13.md）。

## 概况
- 仓库 zeng085/sanfan-yoga-site（可改 private，已核查），Vercel 部署；B2B OEM/ODM 瑜伽垫/健身器材厂站
- EN 主站 + de/ja/ko/fr/it/es 6 语言子目录 + 中文同页 CSS 切换（无 /zh/ URL）
- 结构：147 产品页（products/）+ 10 分类页（**根目录**非 products/）+ products.html 总览
  + 6 场景页（applications/，只从既有 SKU 挑，永不新增产品）+ materials.html + 9 blog + 首页
- 多语言 100% 对齐：每语言 180 页，sitemap 1260 条 0 重复
- DeepL 第二个 key 已启用（约 91 万字符/月余量）；翻译缓存按文本命中，换 key 不丢缓存
- ⚠️ `.gitignore` 已排除 `i18n_build/.deepl_key*`、`i18n_build/data/`（报价表 16M 商业机密）
- 体检工具：`final_check.py`（5 项）、`seo_deep_audit.py`（13 类）、`seo_skill_checks.py`
  （Schema 政策+内容质量+GEO 可引用性，vendor 自 claude-seo MIT）——页面上千后一律**后台跑**（超时 137）

## 改动与推送流程
- bump `?v=`（`bump_assets_ver.py`，写法 `?v20260911f` 无等号；改 CSS/JS 必 bump）→ 一个干净 commit
  → `GH_PAT=$(git config --get-regexp '^url\.' | sed -n 's|.*https://\([^@]*\)@github.com.*|\1|p' | head -1)`
  → `push_api_v3.py zeng085/sanfan-yoga-site /abs/repo --auto`（参数顺序！裸 --auto 会 404）
  ⭐ v3 有 tree 逐 blob 比对回退，**不要再 `reset --soft`**（自造死局）；diff 带 `--no-renames`
- 每批建页固定顺序：`apply_batchN_listing` → `build_category_pages` → **`fix_ct_thumbs`** →
  `build_navdata` → `bump_assets_ver` → `final_check`

## 英文站 sanfansport.com（产品数据唯一权威源）
- WordPress+WooCommerce，REST `/wp-json/wp/v2/product`（167）；规格在 content.rendered 两列表格
- ⭐⭐ **41/167 空壳页**（content 空、0 规格）→ 绝不编造数值，只上兜底 3 行
- 剩 12 个未建页全是空壳（普拉提器械 11 + yoga-hammock-2），**暂停堆产品**
- 价格只认 offer 页（FOB Xiamen USD），offers = 基准×0.7~1.3，正文不出数字
- 判「是否已上线」用 `probe_md5.py` md5 精确比对，**别用 slug 差集**（对不上会假报 118 个未上线）

## 视觉定稿（2026-09-11，勿翻案）
- 暖纸卡 `--paper:#f9f7f2` + 图 `mix-blend-mode:multiply` + contain 内缩 4%，零描边零投影
- ⭐ **能换图就别抠图**（算法抠底 4 张已全部回滚）；「换白底原图」12 张保留
- ❌ 被用户否掉：①全抠白 ②图外加边框（「很土，不高级」）③纸色更深 `#f3efe7`（发闷）
- 大图用原始素材；`products.html` 的 `.ct-thumbs` 6 格缩略图用白底素材（另一套规则）
- 图片：WebP q75、最大边 900、命名 `<slug>-<k>.webp`；下图前必查**同名撞车**（同名≠同图，
  用 32×32 通道差判，>20 即不同图；实例 jump-rope-1/kettlebell-1）
- 英文站图片不可达时用 `images.weserv.nl/?url=`（**不带任何参数**才透传原图字节，md5 可比）

## 关键约定
1. 语言切换：`siteLang` 双写；`.lang-zh` 默认隐藏
2. 英文公制+英制，欧日韩纯公制；`"` 进 JSON-LD 转义
3. JSON-LD @graph Product+BreadcrumbList，offers=AggregateOffer（勿放 availability）
4. hreflang 已健康勿动；GA4 G-RMSNDR5S06
5. ⭐ `i18n_build/site_templates.py` 是全站唯一模板源，新页面必须走它

## ⭐ 坑清单（高频踩）
- BSD grep `\|` 交替静默失效 → 多关键词/中文用 Python；CJK 相邻 `\b` 失效，替换要枚举语言后缀
- 产品页无 `<main>`：选择器用 `.pd-gallery img` / `table.spec-table th`
- **语言版生成标题→slug 匹配失败静默回退 products.html**（09-13 修 1086 条/204 文件）；
  再生成语言页后必跑 `fix_lang_card_links.py` 复扫
- file:// 验收不可靠（classic script + ?v 被拒）→ 用 `python3 -m http.server 8848`
- 百分比 padding 包含块是父容器宽度 → `.sr-thumb` 用 `padding:4px`
- 页面上千后前台脚本超时 137 → 一律后台跑（幂等）
- 全站计数文案（products/SKU 数）分散在首页+6 场景页 7 语言 ≈ 57 文件，改产品数要全局替换

## SEO/GEO 现状（2026-09-13）
- 站内：canonical/hreflang/sitemap 全部健康；SEO 深检 0 问题；Schema 政策真问题 0
  （AggregateOffer 714 条为 B2B 设计内豁免）；内容质量 89.8 分
- **GEO 短板：全站 0 个 120–180 词自包含答案块（最长段 97 词）** → 指南型长文补
- FAQPage 保留不动（富结果 2026-05 退役，但对 AI 引用仍有用）；llms.txt 别指望起排名
- 排名抽查：8 个核心词全部未进前 5；**品牌词 "SANFAN" 被 sanfanyoga.com（厦门同业）截流**
  → 对外统一用全称 "FUJIAN SANFAN Sports Products"
- **对标站 htsyoga.com**（张家港浩通）：private label 指南长文排 "private label yoga mats" 第 3
  → 指南型长文路线已验证，是我们的内容迭代模板
- 第一优先级数据 = 用户 GSC 截图（Indexed/not indexed 状态）

## DNS
- Cloudflare 灰云直连 Vercel；`www.` NXDOMAIN 待修
