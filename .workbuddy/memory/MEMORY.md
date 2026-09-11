# 三梵独立站 fjsanfan.com 长期笔记

> 完整工作流已固化到技能 **`sanfansport-catalog-sync`**（产品/图片同步·体检·改名落点）与
> **`fjsanfan-multilang-spec-sync`**（多语言）。本文件只留索引与坑。

## 概况
- 仓库 zeng085/sanfan-yoga-site，Vercel；B2B 瑜伽垫/健身器材 OEM/ODM 工厂站
- EN 主站 + de/ja/ko/fr/it/es 6 语言 + 中文同页切换（无 /zh/ URL）
- **页面结构**：117 产品页（`products/`）+ 8 分类页 + 总览 `products.html` + 首页
- 改动流程：bump ?v= → push（github-api-push/push_api_v2.py，变更集对比**远端 parent**）

## 产品分类（2026-09-11 拆页）
- 原 `products.html` 117 卡平铺 **28 屏 → 8 分类页 + 总览页（2.6 屏）**。分类名即采购搜索词
  （垫类 4 + foam-rollers/massage-recovery/resistance-bands/yoga-props-accessories）。
  生成脚本**幂等**（卡片池 `outputs/product_cards.json`）。
- ⚠️ 分类格**不能用 `<a>` 包住缩略图链接块**（HTML 不允许 a 嵌 a）→ 用 `<div class="cat-tile">`。

## 首页区块（2026-09-11）
- 上区 range-grid = **8 格分类导航**；下区原「Full Product Gallery」（20 张老页卡）与上区
  **撞图 7 张** + `pr1` 重复 → 改「Featured Products」**12 款跨分类主推**（`featured-grid` 4 列，
  取卡片池新页卡）。脚本 `build_featured_section.py`（幂等）。
- ⚠️ 两区**首图绝不能重复**（range 用的老页：ym1/ym5/pr3/fr1/fr5/rb1/fi2/aurora-gradient-suede-yoga-mat）。
- 孤儿键 `gallery.*`/`gN.*`/`rangeN.*` 已从 main.js 删，补 `featured.*`；`.gallery/.g-item` CSS
  **不能删**（6 语言站仍用）。
- ⚠️ 空壳页使卡片描述中英同为 "Made to order" → 中文 span 改「按单定制」（22 张）。

## 英文站 sanfansport.com（产品数据唯一权威源）
- WordPress+WooCommerce；REST 全开放 `/wp-json/wp/v2/product`（167）。规格在 `content.rendered`
  两列表格；**无 MOQ**；认证 = `ROHS / CE / ISO9001/ BSCI / REACH`。
- ⭐ **核心规则**：产品以英文站为准 —— **我们独有的 → 下掉**；**英文站有我们缺的 → 补上**；
  分批，**先 EN+中文**。⭐⭐ **41/167（25%）空壳页**（content 空、前端 0 table，Yoast schema
  的 "Specification" 是陷阱）→ **绝不编造数值**，只上兜底 3 行。
- 价格只认 `offer` 页（C=Spec / **D=FOB Xiamen USD**，`sanfan_offer.xlsx` 781 行仅 23 行有价）。
  offers = **基准×0.7~×1.3**，正文不出数字。❌ 别用代发客户表/成本表。

## 产品页现状（09-11 体检后）
- **117 页**；图片与英文站 **117/117 一致**（1000 张）；未进分类页 0、死链 0。
- 已下掉 ym8/rb3/rb4/pr2/pr5/fi1。⚠️ fi4 有源曾误判无源 → **下掉前先目视对图**。
- 待第三批 47 个（约 22 个空壳）。⭐ **ym1/ym2 是家族页非 1:1**（ym1↔14 个 TPE 垫），
  对齐用「同族并集」。非错误：96 页缺 6 语言／22 页规格薄／37 页无价。

## 图片规则
- ⭐ **容器必须 1:1**：`.pd-main img` = `1/1`+`contain`、`.prod-card .ph`、`.range-card .rc-img`。
- 命名 `<页slug>-<k>.webp`（k=1=英文站原序）；WebP q75、最大边 900（venv Pillow）。
- ⚠️ 下图前查同名（曾撞名 → 两卡同图）；旧图**不删不覆盖**。部分图带「MuLinSen 木林森」
  水印（已批复可上）；部分图**文件名与内容不符** → 复用前先目视。
- 改图集同步 **4 处**：pd-gallery + og/twitter + JSON-LD image + 全站卡片首图（按 href 匹配）。
- ⭐ **卡片底色问题的最终解法：暖纸卡 + `mix-blend-mode:multiply`**（2026-09-11 第 3 版定稿）
  问题本质 = 同一网格里素材底色不同源（白底/彩色块/实景），**不是"图太白"**。
  前两版被否：①全抠白图（成本高、丢素材）②白卡+浅底画框+描边（用户：「加边框很土，不够高级」）。
  定稿：卡片 `--paper:#f9f7f2` 暖纸色 + 图 `multiply` → 白×纸=纸（白底图融进纸面）、
  彩色×纸=印刷色块，四类底色自动同源，**一条 CSS 替代 12 张换图**。零描边零投影，
  层次靠「纸卡 vs 白页」+ 字体层级（品名 16px/500、说明 12.3px/降饱和），中文态升 600。
  ⚠️ **页底色必须回白**（与第 2 版结论相反）：纸卡落在冷绿 `section soft` 上会脏。
  ⚠️ 语言站 `<section class="section soft" id="xxx">` **带 id**，正则漏写会静默匹配 0 处。
  调色只改 `--paper` 一个值；对比页 `outputs/bgtest/premium.html`（机制）+`premium2.html`（纸色五档）。
  纸色深浅：`#fdfcfa` 看不出边界 / `#f9f7f2` 甜点 / `#f3efe7` 产品压暗发闷。
  工具 `i18n_build/swap_card_thumbs.py`（4 套卡片结构一次改完；`--dry` 预演 / `--rollback` 回滚）、
  `unify_card_bg.py scan|strip`（换底，**已非主路径**）、
  `shot.py`（Chrome 截图，规避带空格路径的 shell 引号坑）、`verify_pages.cjs`（双视口页内校验）。
  ⚠️ 「白底候选」判据要加 `sd<30`，否则会把白墙实景照当成白底图。
- ⭐ **能换图就别抠图**（2026-09-11 深夜定论）：用户要求"贴近原始素材"，4 张算法抠底图
  （ym2 / gray·pink-mandala / mulinsen-61cm）**已全部回滚**为原始素材，`*-1w.webp` 已移出
  （备份 `/tmp/bgcheck/rolled_back_thumbs/`）。原因：抠底留下"白框套色块"痕迹，原始素材是
  一张**完整的图**，在 multiply 纸卡上反而更自然。**「换白底原图」的 12 张保留**（用的是英文站
  本就有的另一张素材，非加工品；ym5 封面换白底后才干净）。
  ⚠️ `--rollback` 只反转 `how` 含「算法换底」的条目，**别改成全量反转**。
  ⚠️ 换图/回滚后必须重跑 `build_category_pages.py`（分类页从卡片池生成、会覆盖手改）→ 再 bump 版本。
- 🗑️ **已废弃（2026-09-11 第 2 版方案，勿照做）**：「section 铺浅底 + 白卡 + 图区内嵌画框
  `--ph-bg:#f7f9f8` + `inset 0 0 0 1px` 描边 + 品名下品牌色短线」。用户评：「在图片外面加
  个边框，看起来很土，不够高级」。教训：**分层不该靠加装饰**；正确解法见上一条（暖纸卡 +
  multiply）。这条留档只为避免把 `--ph-bg/--ph-line` 三个变量再加回来。
  ⚠️ file:// 下必报 `wechat-qr.webp` 加载失败 → main.js 按 pathname 层级拼路径，本地算爆，线上正常。

## 关键约定
1. 语言：localStorage+cookie 双写 `siteLang`；`.lang-zh` 默认 `display:none`，`html.show-zh` 切换。
2. 尺寸：英文公制+英制（`6 mm (1/4")`），欧/日韩纯公制；`"` 进 JSON-LD 转义。
3. **改 CSS/JS 必 bump `?v=`**（`bump_assets_ver.py`）；写法 `?v20260911f`**无等号**。
4. JSON-LD：@graph 包 Product+BreadcrumbList；offers 用 AggregateOffer（勿放 availability）。
   **hreflang 已健康勿动**；下掉页在 `vercel.json` 加 301。GA4 `G-RMSNDR5S06`。

## 最容易踩的坑
- ⭐ **下载英文站图片用 Python `urllib` + 浏览器 UA + Referer**：curl 全废（exit 35/52）。
- ⚠️ **BSD grep 的 `\|` 交替匹配静默失效**（假阴性）→ 多关键词/中文用 Python str.count()。
- ⚠️ **产品页没有 `<main>`**：选择器用 `.pd-gallery img` / `table.spec-table th`。

## DNS / GEO
- DNS 在 Cloudflare，主域**灰云直连 Vercel**（CF 规则不生效）；`www.` NXDOMAIN 待修。
- GEO 站内已及格（AI 爬虫 200、llms.txt、FAQPage）；胜负在**可被引用的榜单/对比表资产**。
