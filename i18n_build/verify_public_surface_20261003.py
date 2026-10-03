#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公开面闸门（2026-10-03 新建，配合 .vercelignore）

为什么必须有这个闸门：静态部署**没有服务端 ACL**，
「git 里跟踪的文件」=「互联网上任何人输入 URL 就能下载的文件」。
2026-10-03 实测：`/.workbuddy/memory/MEMORY.md`、`/outputs/*.md|pdf`、
`/i18n_build/translator_glm.py` 全部 HTTP 200 —— 内部工作笔记与源码可直接下载。

⚠️ 最危险的坑：**Vercel 只在 `.vercelignore` 不存在时回退使用 `.gitignore`**。
所以一旦新建 `.vercelignore`，`.gitignore` 里的密钥保护规则就**不再生效** ——
必须把那些规则合并进 `.vercelignore`，否则等于把密钥重新放开。
本脚本的第③道判据就是守这条不变量。

六道判据：
  ① 站点必需资产必须**留在**公开面（全部 HTML、assets/、robots/sitemap/rss/llms、ai/、vercel.json）
  ② 内部目录必须**不在**公开面（.workbuddy/、i18n_build/、outputs/、__pycache__/）
  ③ `.gitignore` 里的每个保护项必须也出现在 `.vercelignore`（防回退被关掉）
  ④ 根目录的工具脚本与内部文档不得公开
  ⑤ **交叉引用检查**：公开页面里引用的每个本地资源都必须在公开面
     —— 这条是「别把 CSS/JS 也排除掉」的安全网
  ⑥ 线上抽查（--online）：对内部路径发 HEAD/GET，必须全部 404

用法：
    python3 i18n_build/verify_public_surface_20261003.py
    python3 i18n_build/verify_public_surface_20261003.py --online
退出码：有问题 = 1（可直接当推送前的闸）。
"""
import io
import os
import re
import subprocess
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IGNORE_FILE = os.path.join(ROOT, ".vercelignore")
GITIGNORE = os.path.join(ROOT, ".gitignore")
BASE = "https://fjsanfan.com"

MUST_BE_PUBLIC_EXACT = [
    "robots.txt", "sitemap.xml", "rss.xml", "llms.txt", "llms-full.txt", "vercel.json",
]
MUST_BE_PUBLIC_DIRS = ["assets", "ai", ".well-known"]
MUST_BE_PRIVATE_DIRS = [".workbuddy", "i18n_build", "outputs", "__pycache__"]
ONLINE_PROBES = [
    "/.workbuddy/memory/MEMORY.md",
    "/.workbuddy/memory/2026-10-03.md",
    "/i18n_build/translator_glm.py",
    "/i18n_build/reference/site_rules_full_20260927.md",
    "/i18n_build/reports/pilates_catalog_2026_models.csv",
    "/outputs/GEO%E6%89%A7%E8%A1%8C%E7%8A%B6%E6%80%81%E4%B8%8E%E4%B8%8B%E4%B8%80%E8%BD%AE%E8%AE%A1%E5%88%92-2026-09-24.md",
    "/outputs/9-Point-Factory-Vetting-Checklist.pdf",
    "/i18n_build/enblocks/7day-sampling.en.html",
    "/i18n_build/zhblocks/7day-sampling.zh.html",
    "/outputs/en-seo-audit-20260925.html",
    "/92c62d163567679a15cfefe662a3eb43.txt",
    "/GEO-Content-Plan.md",
    "/seo_audit.py",
    "/README.md",
    "/i18n_build/.glm_key",
]


def read_lines(path):
    if not os.path.isfile(path):
        return []
    out = []
    for raw in io.open(path, encoding="utf-8").read().splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        out.append(s)
    return out


def ignored(path, patterns):
    """极简 gitignore 匹配：只支持本仓实际用到的形态（前导 / 、结尾 / 、尾部 * 、** 前缀）。

    刻意不追求完整 gitignore 语义 —— 因为本文件刻意只用简单形态，
    规则复杂到需要完整实现时，闸门本身就不可信了。
    """
    segs = path.split("/")
    for pat in patterns:
        anchored = pat.startswith("/")
        p = pat.lstrip("/")
        dir_only = p.endswith("/")
        p = p.rstrip("/")
        if dir_only:
            # 目录模式：任一层级完全相等
            if p in segs:
                return True
            continue
        if "/" in p:
            # 含斜杠：根锚定匹配整条路径（允许前缀式目录匹配）
            if path == p or path.startswith(p + "/"):
                return True
            if anchored:
                continue
            if any(seg == p for seg in segs[:-1]):
                return True
            continue
        # 无斜杠：任意层级 basename 匹配（gitignore 语义）；带前导 / 则只匹配根级
        base = segs[-1]
        if p.startswith("*") or p.endswith("*"):
            if anchored:
                # 根锚定 + 通配：只比根级文件名
                if fnmatch_seg(base, p) and "/" not in path:
                    return True
            elif fnmatch_seg(base, p):
                return True
        else:
            if base == p:
                return True
        if not anchored and any(seg == p for seg in segs):
            return True
    return False


def fnmatch_seg(name, pat):
    if pat.startswith("*"):
        return name.endswith(pat[1:])
    if pat.endswith("*"):
        return name.startswith(pat[:-1])
    return name == pat


def tracked():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout
    return [f for f in out.split("\n") if f.strip()]


def main():
    online = "--online" in sys.argv
    pats = read_lines(IGNORE_FILE)
    if not pats:
        print("✗ 没有 .vercelignore（或全被注释）—— 静态部署下所有跟踪文件都公开")
        return 1
    files = tracked()
    pub = [f for f in files if not ignored(f, pats)]
    priv = [f for f in files if ignored(f, pats)]
    print("跟踪文件 %d → 公开 %d / 排除 %d" % (len(files), len(pub), len(priv)))
    c = Counter((f.split("/")[0] if "/" in f else "(root)") for f in pub)
    print("公开面构成：" + "  ".join("%s=%d" % (k, v) for k, v in c.most_common(12)))
    cp = Counter((f.split("/")[0] if "/" in f else "(root)") for f in priv)
    print("已排除：" + "  ".join("%s=%d" % (k, v) for k, v in cp.most_common(12)))

    bad = []

    # ① 站点必需资产必须在公开面
    for f in MUST_BE_PUBLIC_EXACT:
        if f not in pub and f in files:
            bad.append("① 必需文件被排除：%s" % f)
    for d in MUST_BE_PUBLIC_DIRS:
        n_pub = sum(1 for f in pub if f.split("/")[0] == d)
        n_all = sum(1 for f in files if f.split("/")[0] == d)
        if n_all and n_pub != n_all:
            bad.append("① 必需目录 %s/ 有文件被排除（%d/%d 公开）" % (d, n_pub, n_all))
    # 全部**站点** HTML 必须在公开面（内部目录里的 HTML 本就该排除）
    # ⚠️ 别用 startswith(("", "de/", ...))：空串前缀恒真，等于没判别根级文件
    page_dirs = ("de/", "ja/", "ko/", "fr/", "it/", "es/", "blog/", "products/",
                 "pilates/", "applications/")
    site_html = [f for f in files if f.endswith(".html")
                 and ("/" not in f or f.startswith(page_dirs))]
    n_html_pub = sum(1 for f in pub if f.endswith(".html"))
    missing = [f for f in site_html if f not in pub]
    if missing:
        bad.append("① 有站点 HTML 被排除：%d 个，例：%s" % (len(missing), missing[:8]))
    else:
        print("① 站点 HTML 全部在公开面：%d 个 ✓（另有 %d 个内部 HTML 已排除）"
              % (len(site_html), sum(1 for f in files if f.endswith(".html")) - len(site_html)))

    # ② 内部目录必须不在公开面
    for d in MUST_BE_PRIVATE_DIRS:
        n = sum(1 for f in pub if f.split("/")[0] == d)
        if n:
            ex = [f for f in pub if f.split("/")[0] == d][:5]
            bad.append("② 内部目录 %s/ 仍有 %d 个文件在公开面：%s" % (d, n, ex))
    if not any(b.startswith("②") for b in bad):
        print("② 内部目录全部排除 ✓（.workbuddy / i18n_build / outputs / __pycache__）")

    # ③ .gitignore 的保护项必须也在 .vercelignore
    gi = read_lines(GITIGNORE)
    gi_norm = {p.rstrip("/") for p in gi}
    vi_norm = {p.rstrip("/") for p in pats}
    vi_has_dir = {p.rstrip("/") for p in pats}
    lost = []
    for p in gi:
        key = p.rstrip("/")
        if key in vi_norm or key in vi_has_dir:
            continue
        # 目录类：被某个更宽的规则覆盖也算（如 i18n_build/data/ ⊂ i18n_build/）
        if any(key.startswith(k + "/") or key == k for k in vi_norm if k):
            continue
        lost.append(p)
    if lost:
        bad.append("③ .gitignore 的保护项未出现在 .vercelignore：%s" % lost)
    else:
        print("③ .gitignore 的 %d 条保护项全部被继承 ✓" % len(gi))

    # ④ 根目录工具脚本/内部文档不得公开
    leak = [f for f in pub if "/" not in f and re.search(r"\.(py|js|md|csv)$", f)]
    if leak:
        bad.append("④ 根目录内部文件仍公开：%s" % leak[:8])
    else:
        print("④ 根目录 .py/.js/.md/.csv 全部排除 ✓")

    # ⑤ 交叉引用：公开页面引用的本地资源必须也在公开面
    LINK = re.compile(r'(?:href|src)="([^"]+)"')
    ref_bad = {}
    n_ref = 0
    for rel in [f for f in pub if f.endswith(".html")]:
        try:
            h = io.open(os.path.join(ROOT, rel), encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        base = os.path.dirname(rel)
        for raw in LINK.findall(h):
            u = raw.split("#")[0].split("?")[0]
            if not u or u.startswith(("http", "//", "mailto:", "tel:", "data:", "javascript:", "#")):
                continue
            n_ref += 1
            cand = u.lstrip("/") if u.startswith("/") else os.path.normpath(os.path.join(base, u))
            if u.endswith("/") or os.path.isdir(os.path.join(ROOT, cand)):
                cand = os.path.join(cand, "index.html")
            if os.path.isfile(os.path.join(ROOT, cand)) and cand not in pub:
                ref_bad.setdefault(cand, []).append(rel)
    if ref_bad:
        for tgt, srcs in list(ref_bad.items())[:8]:
            bad.append("⑤ 公开页面引用了被排除的资源（会上 404）：%s ← %s" % (tgt, srcs[0]))
    else:
        print("⑤ 公开页面的 %d 条本地引用全部仍在公开面 ✓" % n_ref)

    # ⑥ 线上抽查
    if online:
        import urllib.request
        import urllib.error
        for p in ONLINE_PROBES:
            req = urllib.request.Request(BASE + p, method="GET",
                                         headers={"User-Agent": "Mozilla/5.0"})
            try:
                with urllib.request.urlopen(req, timeout=25) as r:
                    code = r.status
            except urllib.error.HTTPError as e:
                code = e.code
            except Exception:
                code = 0
            mark = "✓" if code in (403, 404, 401) else "✗"
            if mark == "✗":
                bad.append("⑥ 线上仍可下载：%s（HTTP %s）" % (p, code))
            print("   %s %-72s HTTP %s" % (mark, p[:72], code))

    print("\n" + "=" * 72)
    if bad:
        for b in bad:
            print("✗ " + b)
        print("结论：公开面不合格 ✗（%d 项）" % len(bad))
        return 1
    print("结论：公开面合格 ✓（公开 %d / 排除 %d）" % (len(pub), len(priv)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
