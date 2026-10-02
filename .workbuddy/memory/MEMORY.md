# 三梵独立站 fjsanfan.com 长期笔记

> 细节全量版 = `i18n_build/reference/site_rules_full_20260927.md`（607 行）。
> 技能：`github-api-push` / `fjsanfan-mobile-ui-audit`（改 CSS/JS 前必读）/ `sanfansport-catalog-sync` /
> `fjsanfan-multilang-spec-sync` / `fjsanfan-pilates-section`

## 概况
- 仓库 zeng085/sanfan-yoga-site（private）→ Vercel；B2B OEM/ODM 瑜伽垫/器材站；1372 页
- EN 主站 + de/ja/ko/fr/it/es 子目录 + 中文同页切换；⭐ 全站脚本**一律后台跑**
- ⭐ 资源版本号 `20261002a`（写法 `?v…` 无等号）；改 CSS/JS 必 bump 且同一 commit
- ⚠️ `.gitignore` 排除 `.deepl_key*`/`.glm_key*`/`i18n_build/data/`

## 推送（细节见技能 github-api-push）
bump（先 `--dry-run` 看分布单一项）→ 干净 commit → `push_api_v3.py … --auto`；**不要 `reset --soft`**
- 起点判定三步法（`verify_push_scope_20260927.py`）；**当前 START = `7d293b52`**（远程 `da405b305e`）
- 推送成功后先更新 START（两个脚本）+ 起点表 + 本文件
- ⚠️ 假警报：`push_list_20260927.txt` 自引用（推送前 `git checkout --`）；本地 `origin/main` 是陈旧缓存
- ⚠️ `check_deploy_after_push` 会假阴性 → 直查 `deployments` + `commits/<sha>/status` 复核
- 不 bump 时版本号判据失效 → `verify_live_bytewise_20261002.py` 逐字节（逐字节 > 手写断言 > 版本号）
- 扫密钥：`git grep -n -I -E … HEAD -- .` + 真实 PAT/GLM key 值 `git grep -F` 全树 0 命中
- ⚠️ en.wikipedia.org DNS 污染验不了；Vercel webhook 漏触发常是延迟（先轮询 2–3 轮）

## 翻译链（GLM 主引擎）
- GLM(glm-5.3-flash) → DeepL(额度尽) → MyMemory；`translator_glm.py`（行号锚定+校验+回喂）；
  key `i18n_build/.glm_key`；**ENGINE_TAG 仍 "deepl" 故意不改**（改=全站缓存失效）
- ⭐⭐ **`reasoning_effort=low` 是最大提速旋钮**：该模型始终思考，`thinking` 参数任何写法全 400；
  顶层 `reasoning_effort` 才有效（单批 8268→0 reasoning tok，156s→4.2s，37×）
- ⭐⭐ 降级链已加「对半拆分重试」：批校验不过 → 拆两半递归到单行；备引擎只剩单行仍失败窄路径
  （es 实证：整批降级两次 → 拆分后 723/723 纯 GLM）。**批失败的正确处置是拆批，不是降级**
- 批次上限 12；超时三档（n>8:180s / 4<n≤8:120s / n≤4:90s）；**超时不重试**，直接交拆批器
- 良性回声判据：输出=源文且含 `_EN_MARK` 英文功能词=真失败；不含（型号 SKU）=放行；69 型号恒等映射进术语表
- 全量跑批 `run_full_translation_20261002.py`（15 页→723 行 ×6 语言）；✅ 6 语言纯 GLM 零降级，¥8–9
- 缓存 `cache/translations.json`；引擎标记不分家 → 脏键定点清 `purge_cache_by_term_20261002.py`
- ⭐ 生成链路：`build_pages.py`(节点级翻译+保 SEO 结构) → `fix_site.py`(语言切换器) →
  `update_seo.py`(hreflang 互链+sitemap，含 `norm_dir()` 目录形态归一)；
  校验 `verify_lang_pages_20261002.py`(5 判据) + `probe_lang_pages_20261002.cjs`(浏览器 4 项)

## GEO / 买家审计
- 本地审计用 `_geo_local_harness.py`（引擎反 SSRF 恒判本地 0 分）；总分 64% 全站同值 → 判单页看 47 项引用度
- 数字溯源 SSOT：`pilates_figures_20261002.py`，改普拉提文案后必跑 `verify_numbers/verify_superlatives`
- 买方视角：✅ 首屏 5 秒答案齐、联系摩擦低；🔴 P0 hero 海报已修（理想解=无文字厂照）；
  🔴 P1 全站 0 客户证言；🟠 P2 内联询价框/价格带锚（待用户决策）；P3 about 尽调素材薄

## 判据铁律速览（完整 35+ 条见 reference；高频）
同文件多 Edit 不能并行｜改标签必须成对｜改文案必须生成器重建（截断串内别替换）｜源码归零≠DOM 干净｜
既有问题必须 A/B 实证｜对照工具白名单外必须报错｜极值断言从 SSOT 算｜素材先「看图」再用｜
LLM 校验判据要正向英文证据｜伪元素探针 `getComputedStyle(el,'::after')`｜BSD grep `\|` 失效用 Grep 工具｜
资源未跟踪=线上 404｜备份禁落站点目录

## 当前状态
- ✅ 已上线至 **`da405b305e`**（GLM 引擎链 + hero 裁剪 bump 20261002a，1352 文件，逐字节 7/7 一致）
- ✅ **90 个语言版页面已生成并提交 `d62264f3`（未推送）**：6 篇普拉提博客 + 9 器械页 × 6 语言；
  语言版博客索引 10→16 卡；sitemap 1336→1372；90 页 5 判据 + 105 版本三处一致 + 浏览器 4/4 全通过
- ⏸ 待用户：**说「推送」**（起点 `7d293b52`；本轮无 CSS/JS 改动故不 bump）
- ⏸ 待用户素材：无文字厂照 / 真实客户证言 / 价格带口径
- ⏸ 存量：13 台缺材质毛重；desc>155 共 767 页；`translator.cpython-313.pyc` 宜 `git rm --cached`
- ⚠️ 真实收录/排名验不了（GSC 无凭据）
