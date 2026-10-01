# 三梵独立站 fjsanfan.com 长期笔记

> ⭐ **细节全量版 = `i18n_build/reference/site_rules_full_20260927.md`**（判据铁律 25 条 / 已完成批次 /
> 移动端实测 / SEO-GEO 基线 / 工具清单，全在里面）。**MEMORY.md 只留高频必读 + 当前状态。**
> 技能：`github-api-push` / `fjsanfan-mobile-ui-audit`（**改 CSS/JS 前必读**）/ `sanfansport-catalog-sync` /
> `fjsanfan-multilang-spec-sync` / `fjsanfan-pilates-section`

## 概况
- 仓库 zeng085/sanfan-yoga-site（**private**）→ Vercel；B2B OEM/ODM 瑜伽垫/健身器材厂站；1331 页
- EN 主站 + de/ja/ko/fr/it/es 子目录 + 中文同页切换（无 /zh/ URL）；sitemap 1330 条
- ⚠️ `.gitignore` 排除 `i18n_build/.deepl_key*`、`i18n_build/data/`（16M 报价表机密）
- ⭐ 全站脚本**一律后台跑**
- ⭐ **资源版本号 = `20261001c`**；写法 `?v20261001c`（**没有等号**）；**改 CSS/JS 必 bump，且必须与改动同一个 commit**（漏 bump = 用户命中缓存旧 CSS，HTML 改了但看着没变）

## 推送（细节见技能 `github-api-push`）
改 CSS/JS 先 `bump_assets_ver.py` → 干净 commit →
`GH_PAT=$(cat ~/.workbuddy/secrets/gh_pat) python3 push_api_v3.py zeng085/sanfan-yoga-site <abs_repo> --auto`
（顺序不能换）。diff 带 `--no-renames`；**不要 `reset --soft`**（v2 残留，照做=死局）
- ⭐ **起点判定三步法**（脚本 `i18n_build/verify_push_scope_20260927.py` 已自动化）：
  ① 远程 HEAD 的 **message** 匹配本地 commit（sha 谱系不同）→ ② 远程 tree vs `git ls-tree -r <起点>`
  **逐 blob 比对**，三类差异必须全 0 → ③ 清单两法交叉验证（远程树 vs 本地 HEAD 树 / `git diff`）
- ⚠️ **本地 `origin/main` 是陈旧缓存**：API 建独立 commit，不更新本地 ref → `git log origin/main..HEAD`
  报「待推 65 个」**全是假象**
- **已推起点表**（下次用最新的）：`0d10b7d9`→`b94f9879d5`（分类页 1381 文件，09-26）；
  `41e1ff5a`→`ba4fa0cc52`（移动端 P0+P1，1370 文件，09-27）；
  ⭐ `a19e4a0b`→`7705a32b6d`（**普拉提 9 页画册重构，1445 文件，10-01**）；
  ⭐ `02d6e1ab`→`1188a4c463`（**灯箱标题修复，1336 文件，10-01**）
- ⚠️ 推送管道会把文本 **CRLF 归一为 LF**：全仓唯一 CRLF 文件
  `i18n_build/reports/pilates_catalog_2026_models.csv` 每次推送都成 **1 个假差异**
  （内容逐字节相同仅行尾不同，无害）→ 下次推送顺手转 LF 提交即可根除
- ⚠️ 推送成功日志末尾的「本地对齐：git reset --soft …」是 v2 残留提示，**照做=死局**
- 推送后必查：`i18n_build/check_deploy_after_push_20260927.py <sha> <版本号>`
  （轮询 deployment + curl 线上复核；已参数化）。⚠️ Vercel webhook 会漏触发 → 救法 = **同一棵树发空提交**
  ⭐ 脚本内版本号比对已改**通用正则提取**——别再建「候选版本号白名单」，
  漏掉本次版本 = 12 轮全返回 `[]`，会被误判成「部署没好」（实测踩过）
- ⚠️ 闸二（内容级扫密钥）**别自己逐文件读**（1370 文件 → SIGTERM）→ 用 `git grep -n -I -E … HEAD -- .`；
  且 `git grep …| head` 的 `$?` 是 head 的退出码，不能当判据

## 判据铁律（Top 16，全 25 条见全量版）
1. ⭐ **同一文件的多个 Edit 不能并行**：只有最后一个落盘，另几处静默丢失
2. ⭐ **「同串同步」先数清有几份**：HTML 转义形态不同就不算同串（meta 的 `&amp;` vs JSON-LD 的 `&`）
3. ⭐ 替换式脚本：落盘前 `assert 'href="href="' not in out`；**先摘旧块再重插**；错则先回滚再重跑
4. ⭐ **回退断言分插入/替换**：插入型要与摘块正则**严格互逆**（否则每跑一次多一空行）
5. ⭐⭐ **源码审计归零 ≠ DOM 干净**：JS `createElement`/改属性产生的缺陷
   （`main.js:1140 menuItem.href='#'`、JS 注入的 `.cbar`、全 JS 的站内搜索）**不在 HTML 里**
   → 必须补浏览器级探针，且**按视口分别查**
6. ⭐⭐ **「该改成什么」先搜同处现成写法，别推理**（搜到即用，天然与全站一致）
7. ⭐⭐ **说「惯例」前先量化，且只在同类元素内成立**（`c-link` 1317 处带 `target` / `btn-ghost` 1029 处全不带）
   → 清理类**只修缺陷**，行为变更单列征询
8. ⭐⭐ **改 HTML 标签必须成对**：只 `subn` 开标签 → dry-run / 幂等自检 / computed style **三处都抓不到**；
   浏览器忽略 `</h3>` 后 h2 会**吞掉后面的 `<table>`** → 落盘后断言 `<X`/`</X>` 增减一致
9. ⭐⭐ **「既有问题」必须 A/B 实证**（HEAD 版导出到同目录新文件对比）→ 禁止用「我没改这里」推断
10. ⭐⭐ **改后核查三件套**：`verify_changes_scope_*.py`（difflib 证无夹带）/ `verify_tag_balance_*.py` /
    `scan_overflow_*.cjs --vp=390`；等价简版 = `git diff -U0 -- '*.html'` 的 **`+`/− 行数必须配对**
11. ⭐ **长度判据先问「对 CJK / 对译文成立吗」**：meta 按**显示宽度**（CJK×2，title 60 / desc 155）；
    中英字符比中位 **0.353**（<0.25 = 残块）；「重复」须**按语言分组**
12. ⭐ 工具坑：**`grep -r` 会扫 `.git`（338MB）→ SIGTERM**；**`bump_assets_ver.py` 被超时杀掉会
    静默停半途** → 判定补完**只能看 `--dry-run` 分布是否单一项**
13. ⭐⭐ **分类统计先确认字段是「全串」还是「前缀」**：`series` 是 `"A. AL 铝合金核心床"`，
    用 `"A."` 直接 Counter → **每线 0 台却静默通过** → 断言闸必须含「每个类目计数 > 0」
14. ⭐⭐ **换数据源要换四层**（正文 / meta×3 / JSON-LD / hero）—— 只换正文表格，
    页面与 SEO 层会自相矛盾：★ 判「旧内容是否清干净」用 `git grep` 全串扫描，别看哪里改过
15. ⭐ **`:first-of-type` ≠ 第一个该类元素**：父容器第一个 `div` 若是 `.section-head`，
    `div.cat-unit:first-of-type` 匹配 **0 个** → Playwright 改用 `page.$()`（天然取第一个）
13. ⭐⭐ **对照工具的「静默跳过」比误报更危险**：白名单外的标签/字段必须**直接报错**，
    不能 `continue`。实战：对账脚本漏了 `Material / weight` 这个自定义合并标签，
    整条被跳过 → 与同页总表 `—` 自相矛盾的缺陷逃过检查。改完要 **A/B 实证**
    （把老写法塞回临时副本，确认新版真能报出来）
14. ⭐⭐ **截图与锚点两个必踩坑**：①`fullPage` 截图遇 `loading="lazy"` → 图是空白块，
    且探针 `naturalWidth=0` **假报 404**（curl 实测 200）→ 必须**先逐屏滚动预热 +
    `waitForFunction` 全部 img `complete` + 滚回顶部**再截；②sticky 横幅高度**随视口变**
    （导航换行：1280→92px / 390→192px）→ 锚点用固定 `scroll-margin-top` 必被压住 →
    **JS 写 `--pv-bh` 取实测高度**。判据 = 跳转后目标标题 `top > banner 高度`
15. ⭐ **「视口外元素」探针要认容器**：`pl-spec` 表在移动端是 `.pl-spec-wrap`
    `overflow-x:auto` **容器内横向滚动**（table 860px / wrap 350px），是**既有设计不是缺陷**；
    漏判 `el.closest('.pl-spec-wrap')` 会把合法滚动报成溢出
14. ⭐⭐ **探针期望值必须实测，报假警的工具＝没人信的工具**（"狼来了"）：
    ① `loading="lazy"` 的图未进视口时 `naturalWidth=0` → **假"解码失败"**，测前先**分步滚到底**
    ② `file://` 会破 JS 按目录深度推算的相对路径（`main.js` 的 `wechat-qr.webp` 必 404）
      → 起**本地 HTTP 服务**加载，与线上同构
    ③ 第三方请求（GA）离线必失败 → **只判本域**请求
    ④ 写完先自问「这个数字是我测的还是我猜的」
15. ⭐⭐ **资源未跟踪 = 线上 404**：改 HTML 引用了新图片/新文件，落盘后必须核对
    `git status` 里该资源是否**已跟踪**（实测：全站 2503 个 HTML 引用里恰好 3 张画册图未跟踪，
    线上实测确为 404）。同类：**无 `.vercelignore` → 整仓公开**，新增脚本/报告前想清楚
    是否愿意全网可见（实测 `i18n_build/site_templates.py` 线上 200）
16. ⭐⭐ **别在「已被截断的字符串」内部替换**（本轮最贵的一课）：卡片写的是
    `lead_en[:180] + "…"`（**先截断再补省略号**）。在被截断到 181 字的文本里把
    长句换成短句 → 卡片变 163 字，而生成器重跑得 181 字 → **产物与源脱钩，
    只改产物的检查全发现不了**。→ 改完文案必须用**生成器表达式重建那段**，
    并跑 `i18n_build/verify_pilates_source_vs_product_20261001.py`（8 族 × 4 类源⇄产物审计）
17. ⭐⭐ **拼接串 `replace` 会静默空跑**：目标串在文件里**不连续**（如两个容器块之间隔着空行）
    → `h.replace(块A+块B+块C, 新序)` 命中 **0 次也不报错**，看着「已重排」其实没动。
    实战：表已换序、画册块没换 → 表↔卡错位，静态核验才发现。
    → 取「首块起点 ~ 末块终点」**整段重建**（分隔符原样带上），**落盘后再断言顺序**
18. ⭐⭐ **备份禁落站点目录**：无 `.vercelignore` → `pilates/x.html.bak_*` 会被 Vercel
    当静态文件**发布成公开重复页**。→ 备份写 `~/.workbuddy/backups/fjsanfan/`，
    且 `.gitignore` 补 `*.bak_*` 兜底（已加）
19. ⭐ **本地服务用多线程**：`python -m http.server` 是**单线程**，playwright 并发拉图会丢连接
    → 页尾大图 `naturalWidth=0`，**像真缺陷**。用 `socketserver.ThreadingTCPServer`。
    配套：lazy 预热用 `document.documentElement.scrollHeight`（`body.scrollHeight` 偏小 → 漏页尾）
20. ⭐⭐ **数「卡片」先分清层级**：`cat-unit`=画册页单元、`model-card`=型号卡
    （45 单元 / 80 卡）—— 数错层级 = 凭空 35 张的「假缺口」；同类：
    `itemListElement` 在 **BreadcrumbList 里也有** → 数 ItemList 必须
    **json.loads 解析后按 `@type` 过滤**（正则计数 6 页数出 12 的假富项）
21. ⭐ **双语 span 结构下 JS 取文本必须按 computed display 过滤**：`.lang-en/.lang-zh`
    并存、靠 CSS 切换，`figcaption.textContent` 会读出两套语言+链接文案粘连
    （线上实测 `"2026 catalogue · page 032026 画册 · 第 03 页 · view larger放大查看"`）
    → 修法 `main.js capText()`：`:scope > span.lang-*` + `getComputedStyle().display!=='none'`

## 内容层结构（两种语言机制勿混）
- 行内配对 span：products/applications/首页/blog 卡片；块级 `div.lang-zh` **只在 10 个 blog 文章页**
- ⭐ `i18n_build/site_templates.py` 是唯一模板源；`build_listicle.py` 已冻结
- ⭐ 带 `data-i18n` 的元素**不能有子元素**（applyLang 走 textContent 会整个抹掉）
- ⚠️ ⭐ **改完 EN 源页别用批次重生成语言页**（附带漂移 + 配额降级；缓存投毒后重跑不自愈）
  → 语言版改动**手写译文直接注入**

## 当前状态
- ✅ **普拉提板块 9 页已按 2026 画册重构并上线**（远程 `7705a32b6d`，1445 文件；
  线上 `?v20261001c`）。两级结构别数混：`cat-unit`=**画册页单元**（45 个）、
  `model-card`=**型号卡**（80 张：46/11/9/4/3/7）；`.cat-zoom` 灯箱 45/45 全覆盖。
  线上体检（`verify_live_assets_20261001.py`）：50/50 资源 200（38 画册图无一 404）、
  序号 0 错、ItemList 6/6 平、版本号 6/6 页已切
- ✅ **灯箱标题缺陷已修并上线**（远程 `1188a4c463`）：figcaption 里 `.lang-en`/`.lang-zh`
  并存靠 CSS display 切换，`textContent` 会读出「两套语言+链接文案」粘连
  → `main.js capText()` 按 computed display 取当前语言、排除 `<a>` 内文案；
  ladder-barrel 3 处放大链接补 `cat-zoom`（此前走原生新窗口，与另 5 页不一致）
  ⭐ `cat-zoom` 只存在于 pilates 6 页 —— 别在首页查页面级钩子（假 ✗）
- ⏸ **6 语言版 pilates 页仍是旧体系**（用户：先做好英文，不急）
- ⏸ 13 台缺材质/毛重（画册未印）→ 等工厂；`i18n_build/__pycache__/translator.cpython-313.pyc`
  已被跟踪，建议 `git rm --cached`
- ✅ **移动端 P0 五处 + P1 三项已上线**（远程 `ba4fa0cc52`，线上 `?v20260927b`；
  线上实测：touch-action `manipulation` 1811/1811、汉堡 44×44、表单 16px、
  抽屉 268px/auto/contain、header 仍 69px、横屏末项 ✅ 在视口内且未被 `.cbar` 遮挡）
- ⏸ **P1-4 `env(safe-area-inset-*)` 未做**：本地验证不了（meta 无 `viewport-fit` → `env()` 恒 0）
  → **`viewport-fit=cover` 是否要做 = 独立决策项**（不做则安全区永远无效；做则 1331 页 meta 变更 + 真机验证）
- ⏸ **P2**：`translate="no"`（**8 语言站刚需**，机翻会把 SANFAN 当普通词）、`theme-color`、
  `preconnect`、491/19,109 张图补 `width+height`
- ⏸ **`a.c-link` 17px 热区**（跨 12 页稳定，行为变更需单独点头）
- ⏸ **SEO/GEO 存量**：`desc>155 宽` 767 页（57%，根因译文膨胀，主体 530 产品页）；
  产品页正文中位 469 词（同站 `pilates/*.html` 792–1119 词可参照）
- ⏸ **既有缺陷（A/B 已证非改动引入）**：48 个语言版文章页缺 `</article>`；17 处移动端横向溢出
- 📌 **普拉提数据源定案（历史决策存档，防翻案）**：
  · 画册两套页码：**文件序号 = 纸上印的页码 + 1**（`p36.webp` 印「35」）→ 混用必错一页
  · ⭐⭐⭐ **21-FO/20-V5 后缀跨产品线复用**（画册把两页的「实物图+箱规」块贴到了对方页）：
    梯桶 Ladder Barre 21-FO/20-V5 = Metal 1190×700×1170/85kg（实物见印35）；
    稳踏椅 Chair 21-FO/20-V5 = Metal 920×720×790/85kg（实物见印33）。
    定案三条判据缺一不可：分章连续性 / 箱规物理量级 / 后缀跨线复用。
    用户口头两个结论互相矛盾时**不要二选一**，去找能同时满足两者的读法（真解=两边都对）
  · 材质空写 `—`；FAQ 以 2026 画册为准；文案导向**客户定制品牌**（不把 A 词换 B 词：
    「材质按型号确定 → 见型号表材质列」+「也可按你品牌现用的材质与表面工艺生产」）
  · `Gyrotonic` 已剔除且是**两批**（站点 10 文件 + 生成源/词库——只改产物不改源=埋定时炸弹）；
    数据层「参与归组+输出过滤」；扫商标词含 ja 片假名/ko 谚文/「禅柔」+ 弯直引号两种形态
  · ⭐ 补信息 **A/C/D/E 许可分级**：A 画册原文可写、C 推导须标注、D 行业通用写「这类器械…」、
    **E 级禁止**（价格/MOQ/弹簧/承重/认证/保修/本体尺寸；抄竞品参数最危险）
  · ⛔ 重跑 `build_pilates_section.py` 会整段删除画册块（生成器无 `.cat-*` 模板）
  · 改文案必跑源⇄产物审计 `verify_pilates_source_vs_product_20261001.py`
  · OCR 分块：XY-cut 对对角摆放必失手 → 连通域兜底 `split_leaf_by_components()`，
    命中 37/38（仅文件 p25 手工标框）；复核报告存
    `i18n_build/reports/pilates_data_review_and_expand_plan_20261001.md`
- ✅ 已完成批次（8 分类页补内容 / SEO 存量清理 / GEO 端点 22/22、线上 GEO 78）见全量版
