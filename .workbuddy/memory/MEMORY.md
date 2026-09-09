# 三梵独立站 fjsanfan.com 长期笔记（精简版 2026-09-05）

## 概况
- 仓库 zeng085/sanfan-yoga-site，Vercel 部署，B2B 瑜伽垫/健身器材 OEM/ODM 工厂站（非零售）
- EN 主站 + de/ja/ko/fr/it/es 6 语言 URL + 中文同页切换（无 /zh/ URL）；288 个 HTML
- 改动标准流程：bump ?v= → commit → push（git push 不稳，用 REST API：
  `~/.workbuddy/skills/github-api-push/push_api_v2.py`，GH_PAT 走环境变量，
  变更集对比**远端 parent** 而非 HEAD）→ `git fetch --depth=1` 对齐 → curl 验线上 ?v=

## 关键约定
1. **语言策略**：记住访客选择（localStorage+cookie 双写 siteLang）一路沿用直到手动改；未选默认 EN。切换器 EN 项必须 `data-setlang="en"`。语言页不受中英偏好影响。
2. **尺寸**：英文内容公制+英制（`6 mm (1/4")`，厚度用分数英寸）；欧/日韩页纯公制。`"` 写进 JSON-LD 必须转义。
3. **LANGS** 统一在 `i18n_build/build_pages.py`；标准生成流程：build_pages.py → fix_site.py（切换器）→ inject_ga4.py → update_seo.py（hreflang+sitemap）。
4. **header 结构**：`.container.nav` 下 = nav-brand + nav-links + nav-actions（内含 lang-switch、btn.btn-primary **移动端常驻**）+ 同级 `.menu-toggle`。CSS `.nav-actions .btn` 是**后代选择器**（btn 在 lang-switch 内也命中，勿被「必须直接子级」误导）。nav 断点 920px（勿用 640）；≤920px `.nav-actions{margin-left:auto}`；≤560px 缩 logo 字号；≤420px 隐藏 logo 文字。语言站 blog.html 报价按钮用相对路径 `contact.html`（勿 `../contact.html`）。
5. 语言页「回站点根」必须绝对路径 `/{lang}/`。
6. **GA4**：G-RMSNDR5S06；转化事件 `generate_lead` 在 main.js 表单回调。Formspree 暂不换。
7. **图片**：一律 WebP q75（venv Pillow：`/Users/mac-zlg/.workbuddy/binaries/python/envs/default/bin/python`），img 带 width/height，header logo 不 lazy。
8. **?v= 强制**：改 CSS/JS 必 bump 全站版本号（`/tmp/bump_assets_ver.py` 改 VER 后跑）。
9. **产品页 JSON-LD**：@graph 包 Product+BreadcrumbList；offers 用 AggregateOffer（lowPrice/highPrice 数字+priceCurrency，勿放 availability/priceValidUntil）。审计：`~/.workbuddy/skills/fjsanfan-product-schema/scripts/`。
10. **URL 规范化**：vercel.json 已覆盖 /index.html 与无斜杠重定向；勿开 trailingSlash；**hreflang 已健康勿动**（zh 是同页切换，head 无 hreflang=zh 是正确的）。product.html（单数）孤儿页可删。

## 已知的坑
- `node --check` 前 `unset NODE_OPTIONS`；勿执行生成脚本验证语法。
- 语言页 JS 完全不介入，多行必须真 `<br>`（生成脚本的 `\n` 是字面量反斜杠n，踩过坑）。
- i18n 值含 HTML 标签时 applyLang 用 innerHTML；改 i18n 键 HTML 与 main.js 同步改。
- 中文文件名：`git config core.quotepath false`。
- localStorage 隐私模式可能静默失败；Playwright `add_init_script` 每页都执行（用 evaluate 设一次+reload）。
- 批量修 HTML 用最小 regex 替换（BS4 decode 会重排全文件）；glob 子目录要**递归 rglob**（曾漏 210 文件）。

## DNS/部署
- DNS 在 Cloudflare，主域**灰云直连 Vercel**（A 216.198.79.1/64.29.17.1，无 cf-ray）→ CF 对主域的规则不生效，别白配。
- `www.fjsanfan.com` NXDOMAIN，待用户在 CF 加 CNAME 开橙云 + 301 到主域。
- 待办：GitHub PAT 轮换。

## GEO 方向（2026-09-05 定）
- 站内已及格（AI 爬虫全 200、llms.txt、FAQPage）；胜负在「可被 AI 引用的资产」：榜单/对比表类内容，官网自述权重低。
- 第一步：写 `blog/top-12-china-yoga-mat-manufacturers.html` 榜单页（EN+6 语言，Article+FAQPage，真实竞品+对比表）。
- 其他方向：Reddit r/sourcing、Quora、行业目录等第三方曝光；YouTube 工厂视频（Perplexity/Gemini 会引用 YT，用户已有 AI 短视频产能）。
- **Reddit 实测（2026-09-08）**：全站归档扫 23 版块，带采购意图的瑜伽垫帖仅 7 条、同行工厂 0 下场 → 竞争真空，但容量只有 6–8 条，量要靠主动发帖+邻近品类（瑜伽服/工作室采购）。作战表见 `outputs/Reddit-GEO作战表-2026-09-08.md`。
- **Reddit 主动发帖包（2026-09-09）**：`outputs/Reddit-主动发帖包-2026-09-09.md` —— 《How to vet a yoga mat factory in China》英文主帖全文+5 版块标题+占楼首评+发布 SOP+四次分发。**主帖不提品牌不放链接**，品牌只放 Reddit 简介。
- **站内已对齐**：`blog/vet-factory.html`（EN+ZH+6 语）补齐数字型内容（MOQ 换色规则、密度克重、样品 5 测试、AQL 2.5/4.0、60–90 天时间线、EXW/FOB/DDP），新增 3 条 FAQ+JSON-LD。**Reddit 话术与站内措辞必须逐句一致**，AI 才会判定独立信源互相印证。
- **增量翻译脚本**：`i18n_build/sync_vet_blocks.py` —— 把 EN 文章页新增块/FAQ 同步到 6 语言版（DeepL，自动补 dateModified）。改 SLUG 与标记即可复用。注意 DeepL 会把 "timeline nobody quotes you" 误译成「引用」，德日文必查。
- Reddit 国内直连不通（HTTP 000）；可用的归档检索：`arctic-shift.photon-reddit.com/api/posts/search?subreddit=X&title=yoga&limit=N`（本地 curl 直连，部分组合会 Timeout 换版块即可），评论 `/api/comments/search?link_id=t3_<id>`，原文 `/api/posts/ids?ids=t3_<id>`。归档 score 失真，只看评论数与时间。
