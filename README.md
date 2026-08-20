# SANFAN Yoga — 独立站（Vercel + GitHub）

面向海外 B 端采购（瑜伽品牌 / 零售连锁 / 瑜伽馆）的 TPE 瑜伽垫 & 瑜伽柱源头工厂独立站。
纯静态站点，零构建，推到 GitHub 后由 Vercel 自动部署到全球 CDN。

## 目录结构
```
index.html      首页（Hero + 卖点 + 产品 + 流程 + CTA）
products.html   产品页
about.html      关于我们
contact.html    询盘表单（接入 Formspree）
assets/css/styles.css   样式
assets/js/main.js       交互（中英切换 / 移动端菜单 / 表单提交）
robots.txt / sitemap.xml  SEO
```

## 本地预览
直接用浏览器打开 `index.html` 即可；或起一个本地服务：
```bash
python3 -m http.server 8080
# 打开 http://localhost:8080
```

## 你需要替换的占位内容
1. **品牌信息（已填真实值）**：邮箱 `zenglinggun@gmail.com`、WhatsApp `+86 15959029082`、地址 `No. 8 Haiguang Road, Yuejin Industrial Zone, Xibin Town, Jinjiang City, Quanzhou City, Fujian Province, China` 已写入 4 个 html。如变更，直接搜这些字符串批量替换即可。
2. **产品图（部分已替换）**：
   - 已放入真实图：`assets/img/tpe-mat.jpg`（TPE 双色垫）、`alignment-mat.jpg`（体位线垫）、`tpe-set.jpg`（三件套白底图）、`showroom.jpg`（展厅）。
   - NBR 瑜伽垫和瑜伽柱的实物图本地未找到，目前产品页仍用占位块。把真实图放进 `assets/img/` 后，把对应 `<div class="thumb" data-i18n="prod3.thumb">...</div>` 和 `prod4.thumb` 替换成 `<img src="assets/img/xxx.jpg" alt="...">` 即可。
3. **询盘表单**：注册 https://formspree.io （免费），拿到你的表单 ID，把 `contact.html` 里
   `action="https://formspree.io/f/YOUR_FORM_ID"` 的 `YOUR_FORM_ID` 替换掉。
   不填也能用，提交会提示失败并提示直接发邮件。
4. **域名**：把 `robots.txt` 和 `sitemap.xml` 里的 `sanfan-yoga.com` 换成你的真实域名。

## 部署流程（GitHub + Vercel）
1. 在 GitHub 网页端新建一个空仓库（如 `sanfan-yoga-site`）。
2. 本地推送（见下方命令），或用 GitHub Desktop 拖入提交。
3. 打开 https://vercel.com/new ，选 "Import Git Repository"，授权 GitHub，选中该仓库 → Deploy。
4. Vercel 会自动识别为静态站点并分配 `xxx.vercel.app` 域名。
5. 在 Vercel 控制台 "Domains" 里绑定你的自定义域名（免费 HTTPS）。
6. 之后每次 `git push`，Vercel 自动重新部署。

## Git 推送命令（首次）
```bash
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git branch -M main
git push -u origin main
```
> 注意：GitHub 已开启 2FA，HTTPS 推送需使用 **Personal Access Token**（不是登录密码）。
> 生成地址：GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → 勾选 `repo`。
> 或在本地生成 SSH key 并加到 GitHub（更省事，一次配置长期有效）。
