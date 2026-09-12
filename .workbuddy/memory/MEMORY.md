# 三梵独立站 fjsanfan.com 长期笔记

> 完整工作流已固化到技能 **`sanfansport-catalog-sync`**（产品/图片同步·体检·改名落点）与
> **`fjsanfan-multilang-spec-sync`**（多语言）。本文件只留索引与坑。

## 概况
- 仓库 zeng085/sanfan-yoga-site，Vercel；B2B 瑜伽垫/健身器材 OEM/ODM 工厂站
- EN 主站 + de/ja/ko/fr/it/es 6 语言 + 中文同页切换（无 /zh/ URL）
- **页面结构**：141 产品页（`products/`）+ 10 分类页 + 总览 `products.html` + 首页
  + **6 场景页 `applications/` + `materials.html` 材质对比页**（09-12 新增，见下节）
- 改动流程：bump `?v=` → 合并成一个干净 commit → `github-api-push/push_api_v3.py --auto`
  ⭐ **用 v3 就不要再 `reset --soft` 对齐**——那是自造死局：本地 HEAD 退回旧 commit，
  而 github.com 不通 fetch 不到新对象 → 下次 `git diff <远端parent> HEAD` 报 bad object。
  v3 已内置 **tree 逐 blob 比对**回退（本地 `ls-tree -r HEAD` vs 远程 recursive tree，
  git blob sha 与 GitHub 一致可直接比），精度等价、能识别删除、不依赖本地远程对象。
  diff 仍要带 `--no-renames`（否则 rename 不删旧路径）
- ⚠️ **推送前必查 `.gitignore`**：`i18n_build/data/`（报价表 16M）是商业机密，
  绝不可进公开仓库；`outputs/{_riskcheck,bgtest,card_bg_white}/`、`outputs/*.png|jpg`
  与 `__pycache__/` 已排除
- ⭐ 推送走 git remote 里的 token **不存在**，在 `url.*.insteadOf` 里：
  `git config --get-regexp '^url\.' | sed -n 's|.*https://\([^@]*\)@github.com.*|\1|p'`
  （api.github.com 401 = 网络通但令牌错；000 才是断网）

## 卡片视觉最终态（2026-09-11 定稿，?v20260911l）
- 方案：暖纸卡 `--paper:#f9f7f2` + 图 `mix-blend-mode:multiply` + `object-fit:contain`
  内缩 4%，**零描边零投影**；四类卡（prod-card / g-item / range-card / cat-tile）统一
- ⭐ **16 张首图全部回归英文站原始素材**（先回 4 张算法抠底，再回 12 张换白底原图）——
  结论：**multiply 已能兜住有色底，能换图就别抠图**，任何加工图都是多余
- ❌ 已被用户否掉的两条路线：①把底全抠成白（不明智）②图外加边框（很土、不高级）
- 工具：`swap_card_thumbs.py`（`--rollback` 反方向、`--only=关键词` 过滤 how）、
  `unify_card_bg.py scan|strip` 体检换底、`final_check.py` 推送前全站体检

## 缩略图网格 = 另一套规则（2026-09-12）
- ⭐ **大图用原始素材，`products.html` 的 `.ct-thumbs` 6 格缩略图用白底素材** ——
  两者要求不同：大图看质感（用户要"贴近原始素材"），3×2 密排小图看整齐（底色必须一致）
- ⚠️ `.ct-thumbs a` 用 `contain` + `padding:8%`、`grid` 是 **3 列**（6 列时桌面仅 43px 看不清）。
  图片若 `cover` 铺满，自带彩色底就会铺成方块，multiply 融不掉 → "有的有边框有的没有"
- ⚠️ **`swap_card_thumbs.py` 的 `THUMB_RE` 会误伤 ct-thumbs**（把缩略图当卡片首图一起换）。
  回滚/换图只针对大图时，别让它碰 `.ct-thumbs`
- 工具：`edge_bg_test.py`（按图片**边缘一圈**判 Δ=multiply 后与卡片色的通道差，比四角准）、
  `fix_ct_thumbs.py`（只改 ct-thumbs，且**只在 Δ 真的变小才换**——有的款换了反而更差）
- 已知残留：英文站素材本身就是"彩色背景板/场景照"的产品（ym2、circular-leg-clamps、
  pilates-reformer-mat-mandala、advanced-yoga-roller、figure-8-resistance-bands、fr3）无白底可换

## 产品分类（2026-09-11 拆页，09-12 扩至 10 类）
- 原 `products.html` 117 卡平铺 **28 屏 → 分类页 + 总览页**。分类名即采购搜索词
  （垫类 4 + foam-rollers/massage-recovery/resistance-bands/yoga-props-accessories；
  09-12 +**jump-ropes / strength-training**）。生成脚本**幂等**（卡片池 `outputs/product_cards.json`）。
- ⚠️ 重新生成顺序：`build_category_pages.py` → `fix_ct_thumbs.py`（缩略图会被前者覆盖）。
- ⚠️ 分类格**不能用 `<a>` 包住缩略图链接块**（HTML 不允许 a 嵌 a）→ 用 `<div class="cat-tile">`。

## 导航引导三层 + 搜索 + 材质页（2026-09-12 落地，`?v20260912c`）
- **问题**：原导航只有一条找货路径（懂规格的人），不懂规格的买方（"我开瑜伽馆要配齐"）无入口。
- **L1** Mega Menu：Products 下拉左「Shop by category」10 分类分 3 组带计数、右深绿「Shop by application」6 场景、底部报价 CTA
- **L2** 分组分类条 `.cat-nav-grouped`（Mats / Training / Recovery & Props 三组）+ `.needrow` 场景快捷行
- **L3** ⭐ `applications/` 6 个按生意类型的采购方案页：`yoga-pilates-studios`(20款) /
  `gyms-fitness-clubs`(23) / `hotels-resorts-spas`(18) / `retail-private-label`(24) /
  `recovery-physio`(25) / `home-online-sellers`(26) —— **只从既有 141 SKU 里挑，永不新增产品**
- **搜索**：头部放大镜 → 浮层；索引 `assets/data/navdata.js`（**classic script 非 JSON**，
  规避 file:// 的 fetch CORS）163 条；`SYNONYMS` 做中英互通（搜"泡沫轴"出 foam roller）；
  `main.js` 懒加载 + `requestIdleCallback` 预热；**跳过非 en/zh 页**（`documentElement.lang`）
- **材质对比**：`materials.html` 8 材质（TPE/PVC/NBR/PU橡胶/麂皮/软木/EVA/EPP）× 9 维度静态表 + FAQ
- ⭐ **`i18n_build/site_templates.py` 是全站唯一模板源**（`prefix` 参数控相对路径
  `""`(根) vs `"../"`(子目录)）：HEAD/NAV/FOOTER/CTA/分类条/场景卡/信任条。新建页面**必须走它**，
  否则模板漂移。生成器全幂等：`build_application_pages.py` / `build_materials_page.py` /
  `build_navdata.py` / `apply_nav_listing.py`（接 sitemap+llms.txt）
- ⚠️ **百分比 padding 的包含块是父容器宽度不是自身** → `.sr-thumb{padding:8%}`(容器 584px)
  单边 46.7px 把 44px 框撑成 93px、`img` 实际 `width:0px`（缩略图全空白）→ **改 `padding:4px`**
- ⚠️ **file:// 验收不可靠**：classic script 带 `?v` 被拒、预取误报 →
  用 `python3 -m http.server 8848` 起本地 http；navdata 路径**去前导 `/`**，JS 用 `ROOT` 拼
  （`ROOT` 从 `link[href*="styles.css"]` 反推，别数 pathname 层级）
- ⚠️ footer 5 列会让老页（4 列）右侧空轨 → `.footer-grid:has(> div:nth-child(5))` 条件切换
- 验收：`final_check.py` 5 项全过（含新增第[5]项**站内 .html 内链死链**，5038 条 0 死链）；
  截图脚本 `shot_nav_live.cjs` → `outputs/nav-preview/`（已 .gitignore）

## 首页区块（2026-09-11）
- 上区 range-grid = **分类导航**（09-11 是 8 格，09-12 扩到 **10 格**）；下区原「Full Product Gallery」（20 张老页卡）与上区
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

## 产品页现状（09-12 第三批后）
- ✅ 缩略图修复版已推（`ed8ff43645`，线上 `v20260912a`）
- **141 页 / 10 分类页**（今 +24 页 +2 分类）；图片引用 2903 条 0 缺失；未进分类页 0、死链 0。
- 已下掉 ym8/rb3/rb4/pr2/pr5/fi1。⚠️ fi4 有源曾误判无源 → **下掉前先目视对图**。
- 第三批 24 款（跳绳 6 + 力量训练 12 + 吊床 6）**本地已建好、未推送**（`v20260912b`）。
- 剩 18 个未上，**全是空壳页** → 有真规格的已 100% 上线。
- ⭐ **ym1/ym2 是家族页非 1:1**（ym1↔14 个 TPE 垫），另有 12 个家族页映射见
  `pending_batch3.py` 的 `FAMILY`；对齐用「同族并集」。
  非错误：96 页缺 6 语言／22 页规格薄／37 页无价。
- ⭐⭐ **判「是否已上线」别用规格数或 slug，用 `probe_md5.py` 的 md5 精确比对**：
  本次 29 个有规格的产品里 5 个其实已被老页吞掉（`yoga-hammock→pr1`、`kettlebell-2→fi2`、
  `jump-rope-2→fi3`、`stair-climbers-3→fi4`、`dumbbell-2→fi5`），**多算了 5 个**。
  dHash 感知哈希会误判（球类匹配到瑜伽垫），必须 md5。

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
