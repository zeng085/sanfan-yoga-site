# 三梵独立站 fjsanfan.com 长期笔记

> 细节全量版 = `i18n_build/reference/site_rules_full_20260927.md`（607 行）。
> 技能：`github-api-push` / `fjsanfan-mobile-ui-audit`（改 CSS/JS 前必读）/ `sanfansport-catalog-sync` /
> `fjsanfan-multilang-spec-sync` / `fjsanfan-pilates-section`

## 概况
- 仓库 zeng085/sanfan-yoga-site（private）→ Vercel；B2B OEM/ODM 瑜伽垫/器材站；1387 页
- EN 主站 + de/ja/ko/fr/it/es 子目录 + 中文同页切换；⭐ 全站脚本**一律后台跑**
- ⭐ 资源版本号 `20261003e`（`?v…` 无等号）；改 CSS/JS 必 bump 且同一 commit
- ⭐⭐ **静态部署 = git 里每个跟踪文件都是公开 URL**；`.vercelignore` 已建（公开 2793 / 排除 591）
- ⚠️⭐ **Vercel 只在 `.vercelignore` 不存在时才回退用 `.gitignore`** → 新建它时
  必须把 .gitignore 的密钥保护规则**合并进去**，否则等于把密钥放开（33 条，已合并）

## 推送（细节见技能 github-api-push）
bump（先 `--dry-run`）→ 干净 commit → `push_api_v3.py … --auto`；**不要 `reset --soft`**
- 起点三步法（`verify_push_scope_20260927.py`）；**当前 START = `4f1334c1`**（远程 `d6f5131651`）；
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

## ⭐ 血泪铁律（今天四次踩出真事故，全文见日志）
- ⭐⭐ **判据跑在受限网络环境 → 先证伪环境再谈站点**。`generate_lead`「无请求」实为我这台机器
  Chromium 连不上 `google-analytics.com/g/collect`（curl 同端点 204 正常）→ 误判成站点缺陷、
  还改坏了 GA 桩。**判据说「无请求」时必须换通道对照**。
- ⭐⭐ **改第三方 SDK 胶水代码前先做变体 A/B**：2–4 种写法注入真实页面各跑一轮。
  官方写法 `push(arguments)` 是对的，我「优化」成 slice 反而连 page_view 都没了。
- ⭐⭐ **判据自身出错比站点缺陷更危险**：`grep "a\|b"` 静默返回 0（BSD 不支持 `\|`）→ 曾据此
  宣布「GA 已清零」并上线。跨模式一律 Python re；**空集必须硬失败**。
- ⭐⭐ **隔离环境不可信 / 同实验结论矛盾 = 先怀疑判据**：gtag.js 走沙箱，`eval` 注入无法复现；
  `en=([^&]+)` 会把 page_view 参数当事件名。
- **改动顺序**：`git checkout --` 会连带撤销同文件其它未提交改动 → 大改动先 commit 再批量改写。
  **浏览器 ERR_ABORTED ≠ 站点故障**（curl 打同 URL 对照）。
- 推送起点跑 `find_push_base_20261003.py --set` 自动定位，别手工改 START。

## 判据铁律速览
高频（全文 35+ 条见 `i18n_build/reference/site_rules_full_20260927.md`）：
同文件多 Edit 不能并行｜改标签成对｜**非自闭合元素（textarea/select）不能加 `/>`**｜
改文案必须生成器重建｜源码归零≠DOM 干净｜既有问题必须 A/B 实证｜**空清单/空集必须报错**｜
极值断言从 SSOT 算｜数字判据必须 locale-aware｜**BSD grep `\|` 不生效，用 Grep 工具**｜
**判据阈值必须匹配修复手法**｜素材先「看图」再用｜伪元素探针 `getComputedStyle(el,'::after')`｜
资源未跟踪=线上 404

## 当前状态
- ✅ **已上线至 `d6f5131651`**（本地 `4f1334c1`）：今日三轮审计全部修完并上线
  （公开面 / GA 前置同意 / 14 法律页 / 产能表 / 表单 / Organization.description 本地化 /
  安全头 / 语言串站归零 / 系统语言自动匹配 / 数字书写修复 / 起点自动定位工具）
- ✅ 线上实测：联系页 0 GA 请求（无同意不发）· 横幅 7 语言 · 资源版本 `20261003e` ·
  GA 桩 = 官方写法（arguments）· sitemap 1386 全唯一 · 密钥三闸 0 命中
- ✅ **GA 询盘数据链已闭环验证**（16:10 用户 GA4 实时页确认 `generate_lead`=1 已到达）；
  GA 桩 = 官方写法 `push(arguments)`（我的 slice 改动是误诊，已回退）
- ⏸ 需用户在 GA4 后台做一步：`Admin → Data display → Events → generate_lead` 标记为关键事件
  （否则概览页/转化报告不认它；实时页能看见）
- ⏸ **待用户 3 个法律事实**（法定代表人 / §18 MStV 内容负责人 / 管辖与仲裁）+ 厂照 +
  客户证言 + 价格带口径
- ⏸ 存量：48 页缺 `</article>`；`knowsAbout` 19 词英文；13 台缺材质毛重；desc>155 共 767 页
