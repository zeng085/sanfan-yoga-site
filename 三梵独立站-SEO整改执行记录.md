# 三梵独立站 · SEO 整改执行记录

- 站点：https://fjsanfan.com
- 来源：ChatGPT 出具的《fjsanfan.com SEO 代码整改执行清单》9 条
- 执行日期：2026-08-30
- 提交：`2f42bfbf`（GitHub API 推送，Vercel 已部署）

---

## 一、先评审再执行（关键）

清单**没有照单全收**。逐条用站点真实数据核对后，9 条里：

- **5 条成立，已执行**（P0-1 / P0-2 / P0-3 / P0-4 / P1-5）
- **1 条药方不准，已按更合理方式处理**（P1-6）
- **1 条成立但做法调整**（P1-7）
- **1 条问题不存在，跳过**（P2-8）
- **1 条风险大于收益，不做**（P2-9）

### 被拦下的三个坑

| 坑 | 清单原话 | 照做会发生什么 |
|---|---|---|
| ① | 「全仓库搜索 `hreflang="zh"` 并删除」 | 站里有 **71 处 `<link rel="alternate">`**（该删）和 **31 处语言切换器 `<a>/<button>`**（不能删）。无差别删 = 中文切换功能直接挂掉 |
| ② | 给了 vercel.json 的完整替换版本 | 现有配置第一条是 `sanfan-yoga-site.vercel.app → fjsanfan.com` 的全站 308。直接替换 = 旧域名跳转失效，积累的外链权重全丢 |
| ③ | P2-9「清理隐藏双语内容」 | 会废掉 blog/FAQ 真在用的中英切换。Google 对同 URL 多语言内容**不处罚**，P0-1 已解决核心问题，成本高风险大 |

---

## 二、执行明细

| 项 | 内容 | 数量 |
|---|---|---|
| **P0-1** | 只删 `<link rel="alternate" hreflang="zh">`，切换器一个没动 | 删 70 / 留 31 |
| **P0-2** | 站内 index.html 链接按**目录语言上下文**替换为规范 URL | 140 处 |
| **P0-4** | JSON-LD / Breadcrumb 里 `fjsanfan.com/index.html` → `/` | 27 处 |
| **P0-3** | vercel.json **追加** index.html 301（旧域名规则保留在第一条） | +4 条规则 |
| **P1-5** | sitemap 移除 rss 节点（RSS 文件本身保留） | 70 → 69 条 |
| **P1-6** | 移除 27 个产品页缺 `price` 的无效 Offer | 27 处 |
| **P1-7** | 地址表述明确化（措辞对齐，不抹掉任一地址） | 5 处 |

### P0-2 的目录上下文映射（不能一刀切）

| 文件所在目录 | 原链接 | 替换后 |
|---|---|---|
| 根目录 | `index.html` | `/` |
| `blog/` `products/` | `../index.html` | `/` |
| `de/` `de/products/` | `index.html` / `../index.html` | **`/de/`** |
| `ja/` `ja/products/` | 同上 | **`/ja/`** |
| `ko/` `ko/products/` | 同上 | **`/ko/`** |

如果统一改成 `/`，德语用户点"首页"会被踢回英文站。

### P1-6：为什么删而不是补价格

产品页 `Offer` 有 `priceCurrency` + `availability`，但**缺 `price`**（schema.org 必填字段）。
这会在 Search Console 报 `Missing field "price"` 警告，且富媒体结果本来就因为缺 price 拿不到。

两个选择：
- 给 `AggregateOffer` + `lowPrice`/`highPrice` 真实区间 → 能拿富媒体
- 删掉 offers，保留 Product 基本信息 → 保守，但消除警告

OEM/ODM 没有公开价，**编造价格是违规的**，所以选了后者。Product 的 name/description/image/brand/category 全部保留。

### P1-7：地址其实不矛盾

| 位置 | 原文 | 处理 |
|---|---|---|
| about.html（英） | "based in Xiamen, Fujian ... manufacturing base in Jinjiang" | `based in` → **`headquartered in`** |
| main.js i18n（中） | "总部位于福建厦门…制造基地坐落于泉州晋江" | 本来就对，未动 |
| contact 地址标签（英/中） | "Address" / "地址" | → **"Factory Address" / "工厂地址"** |
| Organization Schema | 工厂地址（晋江/泉州） | 保留不动（真实且可验证） |

中文版一直是对的，只有英文版措辞含糊。**英文对齐中文**即可，不需要抹掉任一地址。

---

## 三、额外查出的严重 bug（清单没有）

### 30 个语言页的 main.js 路径全部少一级 `../`

- 现象：`de/index.html` 引用 `de/assets/js/main.js` —— 该路径不存在，应为 `../assets/js/main.js`
- 影响：**de/ja/ko 全部 30 个语言页 JS 完全加载失败** → 移动端菜单、切换器交互、FAQ 折叠全废
- 根因：`build_pages.py` 生成语言页时重写路径，main.js 引用没跟着加深
- 修复：30 处全部补一级 `../`；全站 871 处 assets 引用复查 → **路径错误 0**

这类问题纯 SEO 清单查不出来（只查标签不查资源加载），但直接毁功能。

---

## 四、治理：把根因堵在生成脚本里

避免以后重跑脚本把问题带回来：

| 脚本 | 改动 |
|---|---|
| `add_hreflang.py` | 模板删掉 `hreflang="zh"` |
| `i18n_build/build_pages.py` | `variants` 删掉 `("zh", _u(None))` |
| `i18n_build/update_seo.py` | `variants()` 删掉 zh（sitemap 的 `xhtml:link` 共用此函数，自动生效） |
| `gen_product_pages.js` | 删 `hreflang="zh"`、Breadcrumb Home 改 `/`、旧版 `lang-btn` 改为留空容器（切换器由 `fix_site.py` 统一注入） |

---

## 五、上线验证结果

| 检查项 | 结果 |
|---|---|
| `/index.html` `/de/index.html` `/ja/index.html` `/ko/index.html` | **全部 308** 到对应规范 URL |
| 6 个页面 link 型 `hreflang="zh"` | **0**（已清空） |
| 6 个页面切换器 `data-setlang="zh"` | **1**（功能保留） |
| sitemap | 69 条，无 rss |
| 语言页 main.js | 200 |
| 浏览器实测 `/de/` `/ja/products/ym1.html` `/ko/` | **0 错误**，切换器可见 |
| 英文首页点中文切换 | Home → 首页 ✅ **功能完好** |
| 全站内部断裂链接 | **0** |
| 全站 JSON-LD 解析 | **0 失败** |

**唯一未能实测**：旧域名 `sanfan-yoga-site.vercel.app` 的跳转。
本机代理访问 `vercel.app` 返回 000（DNS 能解析但连不通），属环境限制。
配置层面已确认 host 规则完整保留在 `vercel.json` 的 redirects 第一条。

---

## 六、待办

1. **Google Search Console 提交**（约 10 分钟，只能你操作）
   - https://search.google.com/search-console → 网址前缀 `https://fjsanfan.com/`
   - Cloudflare 加 TXT 记录验证 → 提交 `sitemap.xml`
   - 用「网址检查」手动请求索引：首页、`/products.html`、`/faq.html`、`/products/ym1.html`、`/blog/tpe-vs-pu.html`
2. **本地 git 对齐**（网络恢复后）
   ```bash
   git fetch origin && git reset --hard origin/main
   ```
   本地 HEAD 是 `a02fbd2`，远程 `2f42bfbf`（两次 API 提交）。工作区内容不变。
3. **GitHub PAT 轮换** —— 仍建议尽快到 GitHub Settings 重新生成。
4. **可选**：blog 页（含 6 篇文章）目前没有多语言切换器——因为 blog 没有 de/ja/ko 版本，
   加了会导致点击跳 404，所以**故意不加**。若以后 blog 做多语言，再补切换器。
