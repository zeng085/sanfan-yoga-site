# 三梵独立站 fjsanfan.com 长期笔记

> ⭐ **细节全量版 = `i18n_build/reference/site_rules_full_20260927.md`**（含精简前全文归档，零丢失）。
> 技能：`github-api-push` / `fjsanfan-mobile-ui-audit`（**改 CSS/JS 前必读**）/ `sanfansport-catalog-sync` /
> `fjsanfan-multilang-spec-sync` / `fjsanfan-pilates-section`

## 概况
- 仓库 zeng085/sanfan-yoga-site（private）→ Vercel；B2B OEM/ODM 瑜伽垫/健身器材厂站；1331 页
- EN 主站 + de/ja/ko/fr/it/es 子目录 + 中文同页切换；⭐ 全站脚本**一律后台跑**（本地服务也要后台任务方式）
- ⭐ **资源版本号 = `20261002a`**（写法 `?v…` 无等号）；**改 CSS/JS 必 bump 且与改动同一 commit**
- ⚠️ `.gitignore` 排除 `.deepl_key*`/`.glm_key*`/`i18n_build/data/`

## 推送（细节见技能 `github-api-push`）
bump（先 --dry-run 看分布单一项）→ 干净 commit → `push_api_v3.py … --auto`；**不要 `reset --soft`**
- 起点判定三步法（`verify_push_scope_20260927.py`）；**当前 START = `3179ac0e`**；推送成功先更新 START+起点表+本文件
- ⚠️ 已知假警报：`push_list_20260927.txt` 自引用（推送前 `git checkout --`）；本地 `origin/main` 是陈旧缓存
- 不 bump 时版本号判据失效 → `verify_live_bytewise_20261002.py` 逐字节比对（逐字节>手写断言>版本号）
- 扫密钥：`git grep -n -I -E … HEAD -- .` + 真实 PAT 值 `git grep -F "$PAT"` 全树 0 命中
- ⚠️ 本机 DNS 污染：en.wikipedia.org 验不了；Vercel webhook 漏触发常是延迟（先轮询 2–3 轮）

## 翻译链（GLM 主引擎）
- **GLM(glm-5.3-flash) → DeepL(额度尽) → MyMemory**；`translator_glm.py`（行号锚定+校验+回喂重试）；
  key 在 `i18n_build/.glm_key`；**ENGINE_TAG 仍 "deepl" 故意不改**（改=全站缓存失效）
- ⭐ 良性回声判据（校验器=出口闸）：输出=源文且含 `_EN_MARK` 英文功能词=真失败；不含（型号 SKU）=放行
- ⭐ 型号 69 个以恒等映射注入术语表（`_GLOSSARY_GLM`）；"Chair 1-A"→"Stuhl 1-A" 才是真错误
- ⚠️ glm-5.3-flash 始终思考（~350 reasoning tok/请求）；**批次上限 12**（25 曾 finish=length 截断）、GLM_TIMEOUT=480s
- ⭐⭐ **降级链已加「对半拆分重试」**：批校验不过→拆两半各自重试到单行 → 备引擎只剩单行仍失败这一窄路径（10-02 es 轮实证：整批降级 25+12 行两次 → 拆分后 723/723 纯 GLM）
- 全量跑批 `run_full_translation_20261002.py`（15 页→723 行 ×6 语言；守卫遇降级当场 abort）；**✅ 6 语言全完成纯 GLM 零降级**，估总成本 ¥8–9；缓存 `cache/translations.json`（.bak_es_20261002 为 es 清污前备份）
- ⏳ 语言版页面生成链路（36 语言版博客页 + sitemap/hreflang/内链）**尚未建**——缓存在等它

## GEO / 买家审计要点
- 本地审计用 `_geo_local_harness.py`（引擎反 SSRF）；总分 64% 全站同值 → 判单页看 47 项引用度
- 数字溯源 SSOT：`pilates_figures_20261002.py`，改普拉提文案后必跑 `verify_numbers/verify_superlatives`
- 买家审计：✅ 首屏 5 秒答案齐、联系摩擦低；🔴 P0 hero 海报已修（CSS 裁剪 `bd76b542` 待推，理想解=无文字厂照）；🔴 P1 全站 0 客户证言；🟠 P2 内联询价框/价格带锚（待用户决策）

## 判据铁律速览（完整 35+ 条见 reference；高频：）
同文件多 Edit 不能并行｜改标签必须成对｜改文案必须生成器重建（截断串内别替换）｜源码归零≠DOM 干净｜
既有问题必须 A/B 实证｜对照工具白名单外必须报错｜极值断言从 SSOT 算｜素材先「看图」再用（hero 教训）｜
LLM 校验判据要正向英文证据｜伪元素探针 `getComputedStyle(el,'::after')`｜BSD grep `\|` 失效用 Grep 工具｜
资源未跟踪=线上 404｜备份禁落站点目录

## 当前状态
- ✅ 已上线至 `1e5773d15a`（博客+GEO）；📦 **待推（START=3179ac0e）**：GLM 引擎链 + hero 修复+bump 20261002a + 拆分重试 + 跑批工具
- ⏸ 待用户：无文字厂照 / 真实客户证言素材 / 价格带口径
- ⏸ 存量：13 台缺材质毛重；desc>155 共 767 页；`translator.cpython-313.pyc` 建议 `git rm --cached`
- ⚠️ 真实收录/排名验不了（GSC 无凭据）
