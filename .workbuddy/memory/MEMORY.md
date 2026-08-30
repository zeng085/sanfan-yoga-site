# 三梵独立站（fjsanfan.com）项目长期笔记

## 站点概况
- 仓库：`zeng085/sanfan-yoga-site`，部署在 Vercel，域名 https://fjsanfan.com
- 定位：**面向海外采购商的 B2B 瑜伽垫/健身器材 OEM/ODM 工厂站**（不是零售站）
- 语言：英文为主 + 德/日/韩/法/意/西 6 种分语言 URL（`/de/` `/fr/` 等）+ 中文同页预览
- 页面规模：约 102 个 HTML，sitemap 101 条

## 重要约定（改动前必读）

### 1. 语言策略：记住访客选择，一直沿用，直到他手动改
用户于 2026-08-30 明确要求（中途我曾误解成"永远默认英文"，已纠正）。
- 访客选了中文 → 整个站点一路中文（首页、产品页、关于页…），直到他改回 EN
- 访客选了 EN → 一路英文
- 没选过（或存储不可用）→ 默认英文
- 存储：**localStorage + cookie 双写**（隐私模式下 localStorage 可能静默失败，cookie 兜底）
- 语言页（/de/ /fr/ 等）是各自语言的独立 URL，**不受中英偏好影响**
- 关键前提：切换器的 EN 项必须带 `data-setlang="en"`，
  否则点了不写入偏好，跳页会回到旧值（曾导致"点 EN 后跳产品又变中文"）

### 2. 尺寸表达：英文内容必须带英制
采购商是美国市场，尺寸要同时给出公制与英制：
`6 mm (1/4")`、`61–122 cm (24"–48")`、`183 cm (72")`
- 厚度用美国惯用**分数**（1/8"、1/4"、3/8"、1/2"、5/8"），不用小数
- 欧洲/日韩页面保持公制，不加英制
- **注意**：英寸符号 `"` 写进 JSON-LD 必须转义，否则破坏 JSON
- 产品页的规格文本在 **main.js 的 I18N** 里（data-i18n 渲染），不在 HTML

### 3. 语言集合统一在 `i18n_build/build_pages.py` 的 `LANGS`
`update_seo.py` / `fix_site.py` / `run_verify.py` 都引用它，不要各自硬编码。
新增语言只需改这一处，再跑 `build_pages.py <lang>` 生成。

### 4. 切换器由 `fix_site.py` 统一注入（幂等）
- `build_pages.py` 只管翻译，不生成切换器
- 切换器是**下拉式**（8 种语言横排会挤爆导航栏）
- EN 项必须带 `data-setlang="en"`；英文页用 `<button>`（同页切换），语言页用 `<a href>`

### 5. 多语言页未翻译产品不得跳回英文
- 6 种语言站（/de/ /ja/ /ko/ /fr/ /it/ /es/）各只翻译了 5 个核心产品（ym1/ym2/ym3/fr1/rb2），其余 22 个产品无翻译。
- 未翻译产品在语言页中的链接必须指向当前语言的 `products.html#<category>`，而不是英文 `/products/xxx.html`。
- `build_pages.py` 的 `rewrite_rel` 已处理该回退逻辑：
  - 有语言版 → `/{lang}/products/xxx.html`
  - 无语言版 → `/{lang}/products.html#{category}`
  - 分类导航 `products.html#xxx` → `/{lang}/products.html#xxx`
- 分类锚点：yoga / props / rollers / bands / fitness

### 6. 语言页「回站点根」的链接必须是绝对路径 `/{lang}/`
`rel_from` 对根目标 `'/'` 做 `split('/')` 会得到 `['','']`，拼出 `'..//'`；
浏览器解析后落到英文站根 `/`，再套用访客存的 `siteLang` → 出现「点 logo 回首页变中文」。
`rewrite_rel` 里已对 `A in ('/', '', '.')` 提前返回 `/{lang}/`。
新增任何「回到首页 / 站点根」的链接时，务必用绝对路径。

### 7. GA4 与分析
- 衡量 ID：**G-RMSNDR5S06**（2026-08-30 全站接入，102 页 head 内 gtag.js）
- 转化事件 `generate_lead` 埋在 `main.js` 表单成功回调，带 product_interest / page_language / page_path
- 用户需在 GA4 后台把 `generate_lead` 手动标记为「关键事件」才进转化报表
- Formspree 表单**暂不更换**（用户 2026-08-30 明确：现在一个询盘都没有，换了也没意义）

### 8. 图片规范（2026-08-30 全量改造）
- 33 张图已转 **WebP 质量 75**（2.6MB → 1.2MB，省 53%）。HTML/CSS/JSON-LD/og:image 共 1400+ 处引用已统一为 `.webp`
- **新增图片必须先转 WebP 再入站**，不要直接放 jpg
- 每个 `<img>` 都要带 `width`/`height`（防 CLS）；**header 内首屏 logo 不加 `loading="lazy"`**（会拖慢 LCP）
- CSS 有 `img{height:auto}` 兜底，保证 width/height 属性不会把图拉变形
- 转换用隔离 venv 的 Pillow：`/Users/mac-zlg/.workbuddy/binaries/python/envs/default/bin/python`（系统 Python 无 Pillow，macOS `sips` **不支持** WebP 输出）
- 原 jpg 暂时保留在 `assets/img/`，确认线上稳定后可清理

## 已知的坑

- **不要执行生成脚本来验证语法**：`node -e "require('gen_product_pages.js')"` 会真的执行并覆盖页面。
  用 `node --check` 只做语法检查。
- **`node --check` 会因 NODE_OPTIONS 报 `--use-system-ca is not allowed`**：
  先 `unset NODE_OPTIONS` 再执行。
- **git push 走 github.com，API 走 api.github.com，代理策略不同**：
  push 反复失败时先分别探测（返回 000 即连接失败）；`api` 通而 `github` 不通就走 REST API 四步提交。
  103 个文件单批也能成功，不必硬拆。API 提交后必须 `git fetch && git reset --hard origin/main` 对齐本地。
- **git 报错会把 remote URL 里的 PAT 打印出来**：日志会泄露 PAT 前缀，轮换待办优先级高。
- **中文文件名**用 `git diff --name-only` 会输出八进制转义，push 脚本会 skip。
  先 `git config core.quotepath false`，或手工传真实文件名。
- **localStorage 写入可能被静默吞掉**（隐私模式）：涉及跨页面状态的写入要考虑降级。
- **Playwright 的 `add_init_script` 每个页面都会执行**：预设 localStorage 会反复重置，
  导致误判。只在第一个页面用 `evaluate` 设一次再 `reload`。
- **i18n 值含 HTML 标签**：`applyLang` 会按内容是否匹配 `/<[a-z]/` 决定用 innerHTML 还是
  textContent；改 i18n 键必须 HTML 与 main.js 同步改。

## 待办
- GitHub PAT 轮换（现用的已被 GitHub 提示过）
