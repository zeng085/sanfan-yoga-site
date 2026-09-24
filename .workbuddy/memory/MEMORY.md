# 三梵独立站 fjsanfan.com 长期笔记（精简 2026-09-24）

> 细节全在技能：`sanfansport-catalog-sync`（产品/建页）、`fjsanfan-multilang-spec-sync`（多语言/博客）、`fjsanfan-pilates-section`（器械板块）。本文件只留**跨轮复用率最高**的判断。

## 概况
- 仓库 zeng085/sanfan-yoga-site → Vercel；B2B OEM/ODM 瑜伽垫/健身器材厂站
- EN 主站 + de/ja/ko/fr/it/es 子目录 + 中文同页 CSS 切换（无 /zh/ URL）
- 1331 页 = 147 产品页 ×7 + 10 分类页 + 10 博客 ×7 + 6 场景页 ×7 + `/pilates/` 63 页 + 门面页
- ⚠️ `.gitignore` 必须排除 `i18n_build/.deepl_key*`、`i18n_build/data/`（16M 报价表商业机密）
- ⭐ 全站脚本**一律后台跑**（前台 120s SIGTERM，单次约 4.5 分钟）

## 推送（git 直推失败）
`bump_assets_ver.py`（改 CSS/JS 必 bump，写法 `?v20260911f` 无等号）→ 干净 commit →
`GH_PAT` 从 `git config --get-regexp '^url\.'` 的 insteadOf 取 →
`push_api_v3.py zeng085/sanfan-yoga-site <abs_repo> --auto`（**参数顺序**，裸 `--auto` 会 404）。
⭐ 不要 `reset --soft`；diff 带 `--no-renames`。

## 导航（2026-09-16 定稿，勿翻案）
- ⭐ `.site-header > .container.nav` **不能锁 `--maxw`**：放不下时浏览器不滚动而是换行、把 `.nav-links` 挤到 logo 上（只有 en/zh 正常）。定稿 `max-width:100%` + `nowrap;flex:none` + 1580/1480/1360 三档收缩
- ⭐ **汉堡断点 1279px** 是实测标定（es 需求 1436 最宽）；断点内必须还原 nowrap/flex:none
- ⭐ 下拉三件套：`.nav-drop::before` 补 12px 死缝 / `MEGA_CLOSE_DELAY=320ms` / 关闭路径 7 条（只留 mouseleave 时 focus 打开的面板会永久卡开）
- ⭐ **目录索引 URL 一律用 `/x/`**（canonical/hreflang/og:url/sitemap/内链），`/x/index.html` 会被 301

## 判据铁律（错一次毁一批页）
1. ⭐ **长度/重复类判据先问「`len()` 对 CJK 成立吗」**：meta 一律按**显示宽度**（CJK×2），title 预算 60 宽 / desc 155 宽；按字符数双向失真。「重复」须**按语言分组**再比（跨语言同名靠 hreflang 区分）——曾 16 组假报 15 组。
2. ⭐ **中英字符比已标定：中位 0.353（四分位 0.30–0.44）**，<0.25=残块 FAIL、<0.30=偏薄。比字数前先标定，别拿错误直觉去「修」正常内容。
3. ⭐ **EN 页的 `|`/`—` 常写成 HTML 实体**（`&#124;`/`&#8212;`）→ 正则只认字面会静默漏掉整个 EN 站。
4. BSD grep `\|` 交替**静默失效** → 用 `grep -E` 或 Python；CJK 相邻 `\b` 也失效。
5. ⭐ 替换式脚本落盘前 `assert 'href="href="' not in out`（曾一次毁 1078 文件而计数正常）。
6. ⭐ **审计脚本自己要先被审计**：`url_path()` 漏映射裸 `index.html` → 首页被误报；`noindex` 孤立页不该要求 hreflang；`i18n_build/` 是构建产物应剔除。
7. ⭐ 全站注入脚本写**替换式**（先摘旧块再重插），不是「只补缺」；规则型清洗要**迭代到不动点**；落盘后发现规则错 → **先回滚再重跑**（`restore_desc_20260916.py` 是范例）。
8. Playwright：**别用 `networkidle`**（GA 挂住永久超时）→ 拦 GA + `domcontentloaded`；中文态必须 `localStorage.siteLang='zh'` 后重载。

## 内容层结构（两种语言机制勿混）
- 行内配对 span：products/applications/首页/blog 卡片（天然成对）
- 块级 `div.lang-zh`：**只在 10 个 blog 文章页**且必须在 `.container` 内 —— 单边页即故障
- ⭐ `i18n_build/site_templates.py` 是唯一模板源；`build_listicle.py` 已冻结（改写走 `fix_listicle_20260913.py`）
- ⭐ 带 `data-i18n` 的元素**不能有子元素**（applyLang 走 textContent 会抹掉）；nav 文案不用 lang span（会打散行）
- ⚠️ meta 的错会随翻译管线**原样传播**到 6 语言版 → 必须改 EN 源页再重生成
- ⚠️ 机翻会吃受保护术语旁的词尾（`alfombrTPEes`）；也会把品牌后缀展开成从句（判据须同时要求「含品牌名 + 制造商类词」）

## SEO/GEO 现状（2026-09-24 复核）
- 技术层已修平：404/跨语言/坏锚点/**结构全 0**；canonical 非自指 0、hreflang 目标不存在 0
- ⭐ **唯一阻塞 = sameAs 的 3 个 URL**（用户未给）。⚠️ 绝不能填 `sanfanyoga.com` / `SANFAN FITNESS`（厦门同名同业，正在截流 "SANFAN" 品牌词）→ 对外用全称 "FUJIAN SANFAN Sports Products"
- 已做：robots 11 个 AI UA / dateModified 70 页 / llms.txt / FAQ 覆盖已含 **147 产品页 + 9 pilates 页**
- 未做（拿分主力，GEO 46/100）：答案块 134–167 词（现中位 45 词，0% 命中）/ 一手来源外链（0）/ Person 作者 / 多模态 / 原创数据
- ⚠️ 每周 AI 曝光自检**从未执行**（清单已备 5 组词，日志 0 次）——唯一能证明动作真换来引用的环节
