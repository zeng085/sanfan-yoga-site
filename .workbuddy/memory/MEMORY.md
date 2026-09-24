# 三梵独立站 fjsanfan.com 长期笔记（2026-09-24）

> 细节全在技能 `sanfansport-catalog-sync` / `fjsanfan-multilang-spec-sync` / `fjsanfan-pilates-section`；只留复用率最高的判断。

## 概况
- 仓库 zeng085/sanfan-yoga-site → Vercel；B2B OEM/ODM 瑜伽垫/健身器材厂站；全站 1331 页
- EN 主站 + de/ja/ko/fr/it/es 子目录 + 中文同页切换（无 /zh/ URL）；sitemap 1330 条
- ⚠️ `.gitignore` 排除 `i18n_build/.deepl_key*`、`i18n_build/data/`（16M 报价表机密）
- ⭐ 全站脚本**一律后台跑**（前台 120s SIGTERM）

## 推送（git 直推必败；细节见技能 github-api-push）
改 CSS/JS 先 `bump_assets_ver.py`（`?v20260911f` 无等号）→ 干净 commit →
`GH_PAT=$(cat ~/.workbuddy/secrets/gh_pat) python3 push_api_v3.py zeng085/sanfan-yoga-site <abs_repo> --auto`
（参数顺序不能换，裸 `--auto` 会 404）。diff 带 `--no-renames`。
- ⭐ PAT 在 `~/.workbuddy/secrets/gh_pat`（600）；旧 `git config url.*.insteadOf` 令牌已失效（REST 401）
- ⭐ 不要 `reset --soft`：v3 推完会**主动打印**这条 v2 遗留建议，照做=自造死局
- ⭐ 推完必查 Vercel 真跑了没：`/commits/<sha>/status` + curl 线上页找新标记

## 导航（2026-09-16 定稿，勿翻案；全细节见技能 §14）
- ⭐ `.container.nav` **不能锁 `--maxw`**（放不下会换行、把 `.nav-links` 挤到 logo 上）；
  **汉堡断点 1279px** 是实测标定不是猜（最宽的 es 需 1436），断点内必须还原 `nowrap/flex:none`
- ⭐ 下拉三件套：`::before` 补 12px 死缝 / `MEGA_CLOSE_DELAY=320ms` / 关闭路径 7 条（少一条则 focus 面板永久卡开）
- ⭐ **目录索引 URL 一律用 `/x/`**（canonical/hreflang/og:url/sitemap/内链），`/x/index.html` 会被 301

## 判据铁律（错一次毁一批页）
1. ⭐ **长度判据先问「这口径对 CJK / 对译文成立吗」**：meta 按**显示宽度**（CJK×2，title 60 / desc 155）；
   「重复」须**按语言分组**；「答案块 134–167 词」**只适用 EN**（见 SEO/GEO 段）
2. ⭐ **中英字符比已标定：中位 0.353（0.30–0.44）**，<0.25=残块 FAIL；比字数前先标定。
3. ⭐ **EN 页的 `|`/`—` 常写成 HTML 实体**（`&#124;`）→ 正则只认字面会静默漏掉整个 EN 站。
4. BSD grep `\|` 交替**静默失效** → 用 `grep -E` 或 Python；CJK 相邻 `\b` 也失效。
5. ⭐ 替换式脚本：落盘前 `assert 'href="href="' not in out`（曾毁 1078 文件）；**先摘旧块再重插**；规则清洗**迭代到不动点**，规则错**先回滚再重跑**。
6. ⭐ **审计脚本先自审**：`url_path()` 漏映射裸 `index.html` → 首页误报；`noindex` 页不要求 hreflang；`i18n_build/` 剔除。
7. ⭐ **判据现「恒定等差」先怀疑判据本身**（曾把剥 script 后残留的 8 个空白当成全站 DIFF）。
8. Playwright：**别用 `networkidle`** → 拦 GA + `domcontentloaded`；中文态须 `localStorage.siteLang='zh'` 后重载。

## 内容层结构（两种语言机制勿混）
- 行内配对 span：products/applications/首页/blog 卡片；块级 `div.lang-zh` **只在 10 个 blog 文章页**且须在 `.container` 内
- ⭐ `i18n_build/site_templates.py` 是唯一模板源；`build_listicle.py` 已冻结
- ⭐ 带 `data-i18n` 的元素**不能有子元素**（applyLang 走 textContent 会整个抹掉）
- ⚠️ meta 的错会随翻译管线**原样传播**到 6 语言版 → 必须改 EN 源页再重生成
- ⚠️ 机翻会吃受保护术语旁的词尾（`alfombrTPEes`/`gomm PVC`）→ 写入前过 lint（技能 §17.6）

## SEO/GEO 现状（2026-09-24 复核）
- 技术层已修平：404 / 跨语言 / 坏锚点 / 结构 / canonical / hreflang 全 0
- ⭐ **实体层铺满全站**：Organization + `@id=…/#organization` + sameAs 覆盖 **1330 页**；
  另给**全部 1085 个含 `Product` 的页**补 `manufacturer`（brand 只说牌子，manufacturer 才说谁做的）。
  脚本 `add_org_sameas_20260924.py` / `add_product_manufacturer_20260924.py`；黑名单闸 `sameas_guard.py`。sameAs=单条 `facebook.com/sanfanyoga`；阿里**不加**
- 已做：robots 11 AI UA / dateModified 70 页 / llms.txt / FAQ **1092 页** / 实体层 1330 / manufacturer 1085
- ⚠️ ⭐ **「答案块 134–167 词」是 EN 专属判据**（EN 中位 141 已达标；fr/de/es/it 146–214、ja/ko 按字符）
  ——曾套译文误判「0% 达标」已更正。**别跨语言套带宽**
- 未做：一手来源外链 / Person 作者 / 多模态 / 原创数据
- ⚠️ 每周 AI 曝光自检**从未执行**（清单已备，日志 0 次）——唯一能证明引用真来的环节
