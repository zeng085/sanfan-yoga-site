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
- ⭐ **收尾轮终检 6 件套（2026-09-16 定稿，可反复跑）**：
  `audit_links_20260916.py`（404/跨语言/坏锚点/空 href，全 0）·
  `audit_seo_20260916.py`（13 项，仅剩 10 页双语块双 h1）·
  `audit_structure_20260916.py`（div 失衡 / `<a>` 嵌套 / 重复 id，全 0）·
  `verify_round_20260916.py`（六项内容指标，全 0）·
  `audit_nav_layout.cjs`（140 组合，0 异常）·
  `verify_nav_hover.cjs`（7 语言 × 5 交互，35/35 PASS）。线上版加 `BASE=https://fjsanfan.com`

## 导航（2026-09-16 定稿，勿翻案）
- ⭐ **`.site-header > .container.nav` 不能锁 `--maxw`**：原来继承 1180px，flex 放不下时
  浏览器不滚动而是**换行并把 `.nav-links` 挤到 logo 上** → 只有 en/zh 看着正常。
  定稿：`max-width:100%` + `.nav-links > a,.nav-drop{white-space:nowrap;flex:none}` +
  1580/1480/1360 三档 gap/字号收缩
- ⭐ **汉堡断点 = 1279px**（实测标定，不是猜）：各语言最小需求 en 1093 / ko 1038 / fr 1216 /
  de 1299 / ja 1342 / it 1427 / **es 1436**；`measure_nav_need.cjs` 量需求、`probe_nav_fit.cjs` 标定断点。
  断点内**必须把 nowrap/flex:none 还原**（竖排面板长标签要能折行）
- ⭐ **下拉三件套**：①`.nav-drop::before` 隐形桥补 `top:calc(100%+12px)` 的 12px 死缝
  （汉堡态禁用）②`MEGA_CLOSE_DELAY=320ms`③mega 关闭路径 7 条（mouseover 落点判定 /
  mouseout 移出窗口 / html mouseleave / window blur / visibilitychange / scroll / Esc）——
  只有 mouseleave 时 **focus 打开的面板会永久卡开**
- ja mega 面板 944px > 900px 视口会被切 → `.mm-panel{max-height:calc(100vh-84px)}` + 两列 `overflow-y:auto`
- ⭐ **目录索引 URL 只用 `/x/` 形式**：canonical / hreflang / og:url / sitemap / 内链**一律**，
  `/x/index.html` 会被 vercel 301（本站 vercel.json 已补 7 条 applications 301，共 63 条重定向）。
  内链写法：根级 `href="./"`、子目录 `applications/`，`assets/data/navdata*.js` 里的 `"u"` 也要同步

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
9. ⭐ **meta 长度一律按「显示宽度」（CJK×2），不按字符数**：title 预算 **60 宽**、desc **155 宽**
   （Google 按像素截断）。按 `len()` 双向失真：ja 36 宽的标题被误判过短、ja/ko 158 宽的漏报。
   体检 `i18n_build/stats_meta.py`；清洗 `i18n_build/trim_meta_20260915.py`（幂等，--dry-run/--check/--desc）。
   - title 后缀：products 曾用长版 `— SANFAN Yoga & Fitness Manufacturer`，是**全站唯一**与
     og:title 及其余 5 个目录不一致的地方 → 09-16 统一为品牌后缀，**两级**（主体短用长档、主体长用 `— SANFAN`）
   - desc 截断先过 `KEEP_RE` 闸（MOQ / 打样 / OEM / 贴牌 / 认证 / 报价 / 联系方式各语言词干），
     且**只检查实际被丢弃的那一段**；缺这道闸时 32 处里 14 处切掉了转化信息
   - 09-16 成效：title>60宽 **979→163（-83%）**，products 目录 EN/ko 清零

## 坑清单
- ⭐ **替换式脚本的自伤写法要当场断言**：`'%shref="%s%s"' % (m.group(1),…)` 而 `m.group(1)`
  已含 `href="` → 产出 `href="href="../x.html"`（本站一次毁 1078 文件 / 10780 处，
  目录计数还正常）。落盘前 `assert 'href="href="' not in out`，并用 `repr()` 抽 3 个样本肉眼看
- ⭐ **审计脚本自己要先被审计**：`url_path()` 对**裸 `index.html`** 没映射成 `/` → 首页被误报
  「未进 sitemap / hreflang 互指不对称」；显式 `noindex` 的孤立页（`product.html` 是 JS 模板）
  不该要求 hreflang/JSON-LD/sitemap；`i18n_build/` 整目录（构建产物）应从链接审计里剔除
- ⭐ **导航里别用 `::after` 加装饰**：`.nav-links a::after` 是悬停下划线（`position:absolute; bottom:-6px`），
  且 `.nav-links a:hover::after{width:100%}` 优先级更高 → 伪元素装饰会被拉成一条贯穿文字的斜线。用真实元素。
- ⭐ **带 `data-i18n` 的元素不能有子元素**：main.js 的 `applyLang` 对无标签值走 `el.textContent = val`，
  子元素会被整个抹掉。文案挂内层 span，图标/箭头放外面。
- ⭐ 导航文案在 EN 页走 `data-i18n` + main.js 字典（**不是** lang span）：
  nav 里 `.lang-zh` 会拿到 `display:block` 而打散行；lang span 只用于正文/chip。
- ⭐ 全站注入/替换脚本要写成**替换式**（先摘旧块再重插），别写成「只补缺」——否则改了标记后改不动存量页。
- BSD grep `\|` 交替静默失效 → 用 Python 或 `grep -E`；CJK 相邻 `\b` 失效，替换要枚举语言后缀
- ⭐ **长度/数量类判据先自问「`len()` 对 CJK 成立吗」**（见约定 9）；
  「重复」类判据必须**按语言分组**再比 —— 跨语言同名靠 hreflang 区分，不是重复
  （审计脚本里 titles/descs 曾是全局字典 → 16 组重复里 15 组假报）
- ⭐ **EN 页的 `|` / `—` 常写成 HTML 实体**（`&#124;`、`&#8212;`）。正则只认字面字符时
  会静默漏掉整个 EN 站（删 OEM 段时 81 处改动全落语言版，EN 一处没动）
- ⭐ 机翻会把品牌后缀**展开成从句**：冒号引出（es `… «X»TPE: fabricante … «SANFAN»`）、
  夹在两个破折号之间（de `– SANFAN – OEM-Hersteller …`）。判据须**同时**要求
  「含品牌名 + 制造商类词」，只认品牌名会切掉博客副标题（实测 47 处中招）
- ⭐ 规则型清洗脚本要**迭代到不动点**：多规则互相影响（一条削短后另一条又填回去 → 不幂等）
- ⭐ 清洗脚本落盘后发现规则有误 → **必须回滚错误改动再重跑**，新规则改不了已落盘的
  （`i18n_build/restore_desc_20260916.py` 是范例：只还原 description、保留正确的 title 改动）
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

## 器械板块 /pilates/（2026-09-15 起 63 页）
- 9 页 EN（`pilates/`）+ 6 语言各 9 页（`<lang>/pilates/`）；sitemap 共 63 条器械 URL（全站 1330 条）
- ⭐ 板块**首页**用目录形式 `/<lang>/pilates/`（= canonical）；族页照原名。导航一级入口恒指 `/<lang>/pilates/`
- ⭐ `build_pages.rewrite_abs()` 必须把目录形式补成 `index.html` 再查 `T1_SET`，
  否则语言版首页 canonical/og:url/JSON-LD 会退回英文地址（等于声明英文为规范版）→ 只有首页中招
- ⭐ hreflang 双向对等：EN 页也要声明 6 语言（建早了的 EN 页只声明 en+x-default 是缺陷，GSC 报 no return tag）
- ⭐ **改管线脚本要等落盘再启动构建**（抢 11 秒就用上旧代码，产出 54 页错误链接）
- 体检：`check_pilates_langs.py`（54 语言页）/ `check_pilates.py`（9 EN 页）/ `audit_pilates_links.py` /
  `audit_pilates_langs_render.cjs`（6 语言多视口）；URL 修补 `fix_pilates_lang_urls.py`（幂等）
- ⚠️ 假失败三件套：切换器 EN/中文项本就指英文（扫内链前剔 `lang-menu`）；
  lazy 图不滚到视口 `naturalWidth=0`（滚到底+等 `complete`）；写死「某页还没建」的断言会过期 → 改查文件是否存在

## SEO/GEO 现状
- canonical/hreflang/sitemap 健康（09-16 收尾：applications 索引统一 `/x/` 形式后，
  canonical 非自指 7→0、hreflang 目标不存在 56→0）；Schema 政策真问题 0（AggregateOffer = B2B 豁免）
- ⭐ **页脚两代模板并存**是历史病根：老版 5 条 `products.html#yoga|props|rollers|bands|fit`
  是死锚点（`products.html` 只有 `id="applications"`）；面包屑 `item3` 曾用同一批死锚点且语言页写 EN 路径。
  09-16 已统一为 10 分类目录链（语言正确相对前缀）+ 真实分类页 URL（819 处）
- ⭐ 语言版 title>60 宽 / desc>155 宽属**自觉取舍**（译文天然更长，Google 省略号截断），
  不是缺陷；desc>220 宽的 302 页同理，批量回切会丢转化信息
- 10 篇博客「多个 h1」（EN 与中文块各一，`.lang-zh` 默认 `display:none`，浏览器互斥显示）——
  **设计如此，审计据此说明，不为清零改结构**；博客索引页（7 语言）09-16 已补 `Blog`+`ItemList` JSON-LD
- FAQPage 保留（富结果已退役，AI 引用仍有用）；榜单页仍零外链来源，待补
- 排名：8 核心词均未进前 5；**"SANFAN" 被 sanfanyoga.com（厦门同业）截流** → 对外用全称
  "FUJIAN SANFAN Sports Products"；对标 htsyoga.com（张家港浩通）的指南型长文路线
- 最高优先级数据 = 用户 GSC 截图（Indexed/not indexed）；CF 灰云直连 Vercel，`www.` NXDOMAIN 待修
