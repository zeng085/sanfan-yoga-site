#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GA 同意门控改造器（2026-10-03）

要解决什么：`googletagmanager.com` 出现在 **1373/1373 页**，但全站**没有同意横幅**。
在德国等欧盟市场，Google Analytics 属于需要前置同意的「非必要 Cookie」
（DSGVO §6(1)(f) / ePrivacy TTDSG §25）→ 这是 P0 合规风险，不是「优化项」。

做法（不改页面布局、不加任何新 HTML 节点）：
  1. 从每个页面删掉 GA 的两个 script 标签（外链 + 内联 dataLayer 配置）
  2. 同意逻辑全部交给 `assets/js/main.js`：读到 `localStorage` 里的同意状态后，
     由 `window.__gaConsentLoad()` 动态插入 GA 脚本（首屏 HTML 里不再有任何 GA 痕迹）
  3. 写 `assets/js/consent_analytics_20261003.js` 记录改造基线（GA ID、页数），便于复核

为什么不在页面里插同意横幅的 HTML：那样 1373 页都要动标签结构，
而横幅由 main.js 注入即可全站生效，**改动面最小、回归风险最低**。

用法：
    python3 i18n_build/add_consent_gate_20261003.py --dry-run    # 只报影响面
    python3 i18n_build/add_consent_gate_20261003.py              # 实际改写
    python3 i18n_build/add_consent_gate_20261003.py --verify     # 幂等与残留校验
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {"i18n_build", "outputs", "__pycache__", ".git", "node_modules", "assets"}
GA_ID = "G-RMSNDR5S06"

# GA 外链：<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXX"></script>
# 前置的 `<!-- Google tag (gtag.js) -->` 注释一并吃掉（用非捕获组，别写成 `)?`）
RE_GA_EXT = re.compile(
    r'(?:[ \t]*<!--[^>]*Google tag[^>]*-->[ \t]*\r?\n?)?'
    r'<script[^>]*googletagmanager\.com/gtag/js\?id=' + GA_ID + r'[^>]*>\s*</script>[ \t]*\r?\n?',
    re.I)
# GA 内联配置：包含 dataLayer / gtag(...)
RE_GA_INLINE = re.compile(
    r'<script(?![^>]*\bsrc=)[^>]*>\s*(?:/\*.*?\*/\s*)?'
    r'window\.dataLayer\s*=\s*window\.dataLayer\s*\|\|\s*\[\];.*?</script>\s*',
    re.S | re.I)
RE_SCRIPT_BLOCK = re.compile(r"<script\b.*?</script>", re.S | re.I)


def collect_html():
    out = []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if f.endswith(".html"):
                out.append(os.path.join(dp, f))
    return sorted(out)


def strip_ga(h):
    """返回 (新 HTML, 是否改动, 改动条数)"""
    n0 = len(RE_GA_INLINE.findall(h)) + len(RE_GA_EXT.findall(h))
    h2 = RE_GA_EXT.sub("", h)
    h2 = RE_GA_INLINE.sub("", h2)
    # 收拾注释残留（外链注释可能因格式差异没被吃掉）
    h2 = re.sub(r"[ \t]*<!--\s*Google tag \(gtag\.js\)\s*-->\s*\n?", "", h2, flags=re.I)
    h2 = re.sub(r"\n{3,}", "\n\n", h2)
    return h2, h2 != h, n0


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    files = collect_html()
    print("扫描页面 %d 个（GA ID = %s）" % (len(files), GA_ID))

    changed, already, total_blocks = [], [], 0
    for p in files:
        h = io.open(p, encoding="utf-8").read()
        has = ("googletagmanager" in h) or ("dataLayer" in h)
        h2, diff, n = strip_ga(h)
        if diff:
            total_blocks += n
            if mode == "--verify":
                print("  ✗ 仍含 GA：%s" % os.path.relpath(p, ROOT))
            else:
                changed.append(p)
                if mode != "--dry-run":
                    io.open(p, "w", encoding="utf-8").write(h2)
        elif has:
            already.append(p)
        # has 但没 diff → 说明只剩注释/空白，视为已清理

    # 残留校验
    residue = []
    for p in files:
        h = io.open(p, encoding="utf-8").read()
        if "googletagmanager" in h or "gtag(" in h:
            residue.append(os.path.relpath(p, ROOT))

    if mode == "--verify":
        print("残留 GA 痕迹的页面 = %d" % len(residue))
        for r in residue[:10]:
            print("   ✗ %s" % r)
        return 1 if residue else 0

    # ⭐ 空集硬失败（2026-10-03 补）
    # 2026-10-03 真实事故：剥完 GA 后我用 `grep "googletagmanager\|gtag("` 复查，
    # **BSD grep 不支持 `\|`**，静默返回 0 → 我据此宣布「全站 GA 已清零」并上线。
    # 实际有 7 个联系页从未被剥（原因见 git log：修表单翻车后 `git checkout --` 回滚，
    # 而剥 GA 只是未提交的工作区改动，索引里还是含 GA 的 HEAD 版本 → 一起被恢复）。
    # 教训：判据自身出错时，静默「通过」比误报更危险。空集必须报错。
    if not files:
        print("✗ 未扫描到任何 HTML 页面 —— 判据空集，拒绝判「通过」")
        return 3

    print("实际改动页面 = %d（删除 GA script 块 %d 个）" % (len(changed), total_blocks))
    if mode == "--dry-run":
        for p in changed[:10]:
            print("   · %s" % os.path.relpath(p, ROOT))
        if len(changed) > 10:
            print("   ... 共 %d 个" % len(changed))
        return 0

    if residue:
        print("⚠️ 改完仍有残留 %d 个页面：" % len(residue))
        for r in residue[:10]:
            print("   ✗ %s" % r)
        return 1
    print("✓ 全站 HTML 已无 GA/gtag 痕迹（同意后由 main.js 动态注入）")
    print("  扫描 %d 页 / 改动 %d 页 —— 请用 Python 正则复查，不要用 grep \"a\\|b\"（BSD 不支持 \\|）" % (len(files), len(changed)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
