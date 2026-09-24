# 三梵独立站 fjsanfan.com 长期笔记（2026-09-24）

> 细节全在技能 `sanfansport-catalog-sync` / `fjsanfan-multilang-spec-sync` / `fjsanfan-pilates-section`；只留**复用率最高**的判断。

## 概况
- 仓库 zeng085/sanfan-yoga-site → Vercel；B2B OEM/ODM 瑜伽垫/健身器材厂站；全站 1331 页
- EN 主站 + de/ja/ko/fr/it/es 子目录 + 中文同页 CSS 切换（无 /zh/ URL）；sitemap 1330 条
- ⚠️ `.gitignore` 排除 `i18n_build/.deepl_key*`、`i18n_build/data/`（16M 报价表机密）
- ⭐ 全站脚本**一律后台跑**（前台 120s SIGTERM）

## 推送（git 直推必败；细节见技能 github-api-push）
改 CSS/JS 先 `bump_assets_ver.py`（`?v20260911f` 无等号）→ 干净 commit →
`GH_PAT=$(cat ~/.workbuddy/secrets/gh_pat) python3 push_api_v3.py zeng085/sanfan-yoga-site <abs_repo> --auto`
（**命令前缀式**；参数顺序不能换，裸 `--auto` 会 404）。diff 带 `--no-renames`。
- ⭐ PAT 在 `~/.workbuddy/secrets/gh_pat`（600）；旧 `git config url.*.insteadOf` 的令牌 09-24 已失效（REST 401）
- ⭐ 不要 `reset --soft`：v3 推完会**主动打印**这条 v2 遗留建议，照做=自造死局；本地 HEAD 与远程 sha 不一致属正常
- ⭐ 推完必查 Vercel 真跑了没：`/commits/<sha>/status` + curl 线上页找新标记

## 导航（2026-09-16 定稿，勿翻案；全细节见技能 §14）
- ⭐ `.container.nav` **不能锁 `--maxw`**（放不下会换行、把 `.nav-links` 挤到 logo 上）；
  **汉堡断点 1279px** 是实测标定不是猜（最宽的 es 需 1436），断点内必须还原 `nowrap/flex:none`
- ⭐ 下拉三件套：`::before` 补 12px 死缝 / `MEGA_CLOSE_DELAY=320ms` / 关闭路径 7 条（少一条则 focus 面板永久卡开）
- ⭐ **目录索引 URL 一律用 `/x/`**（canonical/hreflang/og:url/sitemap/内链），`/x/index.html` 会被 301

## 判据铁律（错一次毁一批页）
1. ⭐ **长度/重复判据先问「`len()` 对 CJK 成立吗」**：meta 按**显示宽度**（CJK×2），title 60 宽 / desc 155 宽；「重复」须**按语言分组**（跨语言同名靠 hreflang 区分）——曾 16 组假报 15 组。
2. ⭐ **中英字符比已标定：中位 0.353（四分位 0.30–0.44）**，<0.25=残块 FAIL、<0.30=偏薄。比字数前先标定。
3. ⭐ **EN 页的 `|`/`—` 常写成 HTML 实体**（`&#124;`/`&#8212;`）→ 正则只认字面会静默漏掉整个 EN 站。
4. BSD grep `\|` 交替**静默失效** → 用 `grep -E` 或 Python；CJK 相邻 `\b` 也失效。
5. ⭐ 替换式脚本：落盘前 `assert 'href="href="' not in out`（曾毁 1078 文件）；写**先摘旧块再重插**；规则清洗**迭代到不动点**，规则错**先回滚再重跑**。
6. ⭐ **审计脚本先自审**：`url_path()` 漏映射裸 `index.html` → 首页误报；`noindex` 页不该要求 hreflang；`i18n_build/` 是构建产物应剔除。
7. ⭐ **判据现「恒定等差」先怀疑判据本身**（曾把剥 script 后残留的 8 个空白当成全站 DIFF）。
8. Playwright：**别用 `networkidle`**（GA 挂住超时）→ 拦 GA + `domcontentloaded`；中文态须 `localStorage.siteLang='zh'` 后重载。

## 内容层结构（两种语言机制勿混）
- 行内配对 span：products/applications/首页/blog 卡片（天然成对）；块级 `div.lang-zh` **只在 10 个 blog 文章页**且须在 `.container` 内 —— 单边页即故障
- ⭐ `i18n_build/site_templates.py` 是唯一模板源；`build_listicle.py` 已冻结
- ⭐ 带 `data-i18n` 的元素**不能有子元素**（applyLang 走 textContent 会整个抹掉）
- ⚠️ meta 的错会随翻译管线**原样传播**到 6 语言版 → 必须改 EN 源页再重生成
- ⚠️ 机翻会吃受保护术语旁的词尾（`alfombrTPEes`），也会把品牌后缀展开成从句

## SEO/GEO 现状（2026-09-24 复核）
- 技术层已修平：404 / 跨语言 / 坏锚点 / 结构 / canonical / hreflang 全 0
- ⭐ **实体层铺满全站**：Organization + `@id=…/#organization` + sameAs 覆盖 **1330 页**（改前仅 103 页有 Org）。
  脚本 `add_org_sameas_20260924.py`；模板**自动取字段最全节点**（实测 about.html 而非首页）；黑名单闸唯一源 `sameas_guard.py`。
  sameAs=单条 `facebook.com/sanfanyoga`（用户确认）；阿里**不加**；对外用全称 "FUJIAN SANFAN Sports Products"
- 已做（均已上线）：robots 11 AI UA / dateModified 70 页 / llms.txt / FAQ **1092 页** / 实体层 1330 页
- 未做（拿分主力，GEO 46/100）：答案块 134–167 词 / 一手来源外链 / Person 作者 / 多模态 / 原创数据 / Product 缺 `manufacturer`
- ⚠️ 每周 AI 曝光自检**从未执行**（清单已备，日志 0 次）——唯一能证明引用真来的环节
