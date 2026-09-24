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
  「EVA 名义下的垫按 TPE 供货」。**本地两个 commit 已改，均未推送**
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
10. Playwright：**别用 `networkidle`**（拦 GA + `domcontentloaded`）；中文态须 `localStorage.siteLang='zh'` 后重载；折叠 `<details>` 的 `innerText` 展开前为空

## 内容层结构（两种语言机制勿混）
- 行内配对 span：products/applications/首页/blog 卡片；块级 `div.lang-zh` **只在 10 个 blog 文章页**且在 `.container` 内
- ⭐ `i18n_build/site_templates.py` 是唯一模板源；`build_listicle.py` 已冻结
- ⭐ 带 `data-i18n` 的元素**不能有子元素**（applyLang 走 textContent 会整个抹掉）
- ⚠️ ⭐ **改完 EN 源页别用批次重生成语言页**：实测附带漂移 + `mymemory` 配额降级；
  缓存命中不调 API，投毒后重跑不自愈 → 语言版改动手写译文直接注入
- ⚠️ 机翻吃术语旁词尾（`alfombrTPEes`）→ 过 lint

## SEO/GEO 现状（2026-09-24 复查）
- 技术层已修平：404 / 跨语言 / 坏锚点 / 结构 / canonical / hreflang 全 0；title>60 宽 **0**
- ⭐ **实体层铺满全站**：Organization + `@id=…/#organization` + sameAs 覆盖 1330 页；
  1085 个含 `Product` 的页补 `manufacturer`。sameAs 只放 `facebook.com/sanfanyoga`
- 已做：robots 11 AI UA / dateModified 70 页 / llms.txt / FAQ 1092 页
- ⚠️ **`desc>155 宽` 仍有 799 页（占 60%）** ← 全站最大存量缺口，尚未处理
- ⚠️ 「答案块 134–167 词」是 EN 专属判据（fr/de/es/it 146–214、ja/ko 按字符），别跨语言套带宽
