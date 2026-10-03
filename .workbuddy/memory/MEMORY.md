# 三梵独立站 fjsanfan.com 长期笔记

> 细节全量版 = `i18n_build/reference/site_rules_full_20260927.md`（607 行）。
> 技能：`github-api-push` / `fjsanfan-mobile-ui-audit`（改 CSS/JS 前必读）/ `sanfansport-catalog-sync` /
> `fjsanfan-multilang-spec-sync` / `fjsanfan-pilates-section`

## 概况
- 仓库 zeng085/sanfan-yoga-site（private）→ Vercel；B2B OEM/ODM 瑜伽垫/器材站；1387 页
- EN 主站 + de/ja/ko/fr/it/es 子目录 + 中文同页切换；⭐ 全站脚本**一律后台跑**
- ⭐ 资源版本号 `20261003c`（`?v…` 无等号）；改 CSS/JS 必 bump 且同一 commit
- ⭐⭐ **静态部署 = git 里每个跟踪文件都是公开 URL**；`.vercelignore` 已建（公开 2793 / 排除 591）
- ⚠️⭐ **Vercel 只在 `.vercelignore` 不存在时才回退用 `.gitignore`** → 新建它时
  必须把 .gitignore 的密钥保护规则**合并进去**，否则等于把密钥放开（33 条，已合并）

## 推送（细节见技能 github-api-push）
bump（先 `--dry-run`）→ 干净 commit → `push_api_v3.py … --auto`；**不要 `reset --soft`**
- 起点三步法（`verify_push_scope_20260927.py`）；**当前 START = `58f42c92`**（远程 `580f850aca`）；
  成功后先更新 START（两脚本）+ 起点表 + 本文件
- ⚠️ 假警报：`push_list_20260927.txt` 自引用（推送前 `git checkout --`）；`origin/main` 陈旧；
  `check_deploy_after_push` 假阴性 → 直查 `deployments` + `commits/<sha>/status`
- 不 bump 时版本号判据失效 → `verify_live_bytewise_20261002.py` 逐字节（逐字节 > 手写断言 > 版本号）
- 扫密钥：`git grep -n -I -E … HEAD -- .` + 真实 PAT/GLM key 值 `git grep -F` 全树 0 命中
- **推送前必跑四道闸**：`verify_public_surface`（公开面）/ `verify_url_consistency`（三处一致）/
  `verify_local_refs`（引用落地+已跟踪）/ `verify_lang_pages`（五判据，空集必须报错）

## 翻译链（GLM 主引擎）
- GLM(glm-5.3-flash) → DeepL(额度尽) → MyMemory；`translator_glm.py`（行号锚定+校验+回喂）；
  key `i18n_build/.glm_key`；**ENGINE_TAG 仍 "deepl" 故意不改**（改=全站缓存失效）
- ⭐⭐ **`reasoning_effort=low` 是最大提速旋钮**（该模型始终思考，`thinking` 参数任何写法全 400）：
  顶层 `reasoning_effort` 才有效（单批 8268→0 reasoning tok，156s→4.2s，37×）
- ⭐⭐ 降级链「对半拆分重试」：批校验不过 → 拆两半递归到单行（es：整批降级两次 → 拆分后 723/723 纯 GLM）。
  **批失败的处置是拆批，不是降级**；批次上限 12；超时不重试直接交拆批器
- 生成链路：`build_pages.py`(节点级翻译+保 SEO) → `fix_site.py`(切换器) →
  `update_seo.py`(hreflang+sitemap，`norm_dir()` 归一)；缓存 `cache/translations.json`

## 合规 / 移动（10-03 三轮审计后；明细见 2026-10-03.md）
- ✅ 公开面：`.vercelignore` + `verify_public_surface_*.py`（六道闸门；Vercel 只在它
  **不存在**时回退用 `.gitignore` → 必须合并全部密钥规则）
- ✅ GA 门控：`add_consent_gate_*.py` 剥 1373 页；`main.js` 同意后才动态加载
- ✅ 法律页 14 页 + 全站页脚入口 + sitemap 1386；Organization.description 全站本地化
- ✅ 产能表 `.cap-wrap`（320px 整表放得下）；表单 6/6 label + 诱饵 + aria-live + 7 语言提示
- ✅ 安全头 CSP 等 6 项；语言串站 0；系统语言自动匹配；数字书写修复
- ⚠️ **待用户 3 个法律事实**（页面用 ［…］ 标出）+ 无文字厂照 / 客户证言 / 价格带口径
- ⚠️ 存量：48 页缺 `</article>`；`knowsAbout` 19 词仍英文；13 台缺材质毛重；desc>155 共 767 页

## 判据铁律速览（完整 35+ 条见 reference；高频）
同文件多 Edit 不能并行｜改标签必须成对｜**非自闭合元素（textarea/select）不能加 `/>`**｜
改文案必须生成器重建｜源码归零≠DOM 干净｜既有问题必须 A/B 实证｜**空清单/空集合必须报错**｜
极值断言从 SSOT 算｜数字判据必须 locale-aware｜**BSD grep `\|` 不生效，用 Grep 工具**｜
**判据阈值必须匹配修复手法**（修好了可能被自己的判据报成没修）｜素材先「看图」再用｜
伪元素探针 `getComputedStyle(el,'::after')`｜资源未跟踪=线上 404

## 当前状态
- ✅ **已上线至 `217b42a4`**（本地 `cb482b8f`，1417 文件）：公开面收口 / GA 同意门控 /
  14 个法律页 / 产能表 / 表单 / Organization.description 本地化 / 安全头 /
  语言串站归零 / 系统语言自动匹配 / 数字书写修复，资源版本 `20261003c`
- ✅ 线上实测：内部 7 条路径全 404 · 法律页 200 · GA 0 引用 · 安全头 7 项全在 ·
  **客户语言旅程（真实域名）26/26** · 部署 success
- ⏸ 存量待排期：① 48 个旧语言版博客页缺 `</article>`（起点版既有）
  ② `knowsAbout` 19 个产品词仍英文 ③ 13 台缺材质毛重 ④ desc>155 共 767 页
  ⑤ 数字判据对「写法差异」（EN `5,000 万` vs 德 `50 Millionen`）无法对齐，非缺陷
- ⏸ 待用户：**3 个法律事实**（法定代表人 / §18 MStV 内容负责人 / 管辖与仲裁）+ 无文字厂照 +
  真实客户证言 + 价格带口径；⏸ 真实排名验不了（GSC 无凭据）
