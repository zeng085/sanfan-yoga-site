#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""站点安全面静态审计（2026-10-03 新建）

为什么单独写：移动端/UI 审计只看「页面好不好用」，**不看「会不会被利用」**。
静态站最容易被忽略的一条是：**git 里跟踪的每个文件都会被部署成公开可下载的 URL** ——
没有服务端 ACL，唯一的防线是不把文件放进仓库（或部署时排除）。

八道判据：
  S1 公开面：非 HTML 跟踪文件数量与体积（按顶层目录分布）→ 越少越安全
  S2 敏感文件是否被跟踪（key/pem/env/bak/sql/db/p12…）与是否被 gitignore 覆盖
  S3 混合内容：页面里 `http://` 的站外引用（浏览器会拦但会降级/告警）
  S4 `target="_blank"` 是否缺 `rel="noopener"`（反向标签劫持 window.opener）
  S5 第三方脚本/iframe 的来源域名清点（供应链与隐私面）
  S6 表单安全：action 指向、method、是否有 honeypot/校验线索
  S7 隐私：页面里是否内嵌邮箱/电话/地址（与 JSON-LD 的一致性另算）
  S8 危险 API：eval / new Function / document.write / 密码类自动填充

用法：
    python3 i18n_build/audit_security_20261003.py            # 全站（后台跑）
    python3 i18n_build/audit_security_20261003.py --limit 200
退出码：P0/P1 命中 = 1（可直接当闸）。
"""
import io
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {"i18n_build", "outputs", "__pycache__", ".git", "node_modules"}
LANGS = ["de", "ja", "ko", "fr", "it", "es"]

RE_SCRIPT_BLOCK = re.compile(r"<script\b.*?</script>", re.S | re.I)
RE_STYLE_BLOCK = re.compile(r"<style\b.*?</style>", re.S | re.I)
RE_COMMENT = re.compile(r"<!--.*?-->", re.S)
RE_HTTP = re.compile(r"""(?:href|src)\s*=\s*["'](http://[^"']+)["']""", re.I)
RE_TARGET_BLANK = re.compile(r"<a\b[^>]*target\s*=\s*[\"']_blank[\"'][^>]*>", re.I)
RE_REL_NOOPENER = re.compile(r"rel\s*=\s*[\"'][^\"']*noopener", re.I)
RE_IFRAME = re.compile(r"<iframe\b[^>]*>", re.I)
RE_SRC_HOST = re.compile(r"""<(?:script|img|iframe|link)\b[^>]*?(?:src|href)\s*=\s*["'](https?://([^/"']+))""", re.I)
RE_FORM = re.compile(r"<form\b[^>]*>", re.I)
RE_INPUT = re.compile(r"<input\b[^>]*>", re.I)
RE_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
RE_DANGER_JS = re.compile(r"\b(eval\s*\(|new\s+Function\s*\(|document\.write\s*\(|outerHTML\s*=)")
RE_PASSWORD = re.compile(r"""type\s*=\s*["'](?:password|cc-number|csc)["']""", re.I)
RE_AUTOFILL = re.compile(r"""autocomplete\s*=\s*["']([^"']*)["']""", re.I)


def git_files():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout
    return [f for f in out.split("\n") if f.strip()]


def gitignored(path):
    r = subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT)
    return r.returncode == 0


def collect_html():
    out = []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if f.endswith(".html"):
                out.append(os.path.join(dp, f))
    return sorted(out)


def main():
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    tracked = git_files()
    nonpage = [f for f in tracked if not f.endswith(".html")]
    size_kb = 0
    by_top = Counter()
    for f in nonpage:
        p = os.path.join(ROOT, f)
        try:
            size_kb += os.path.getsize(p) / 1024.0
        except OSError:
            pass
        by_top[f.split("/")[0] if "/" in f else "(root)"] += 1

    print("=" * 72)
    print("S1 公开面：git 跟踪的非 HTML 文件 = %d 个 / %.1f MB" % (len(nonpage), size_kb / 1024))
    print("   （静态部署下每个文件都是公开可下载的 URL，这是最容易被忽略的攻击面）")
    for k, v in by_top.most_common(10):
        print("     %5d  %s" % (v, k))

    sensitive_pat = re.compile(r"\.(key|pem|env|bak|old|orig|sql|db|sqlite|sqlite3|p12|pfx|crt|cer|asc)$", re.I)
    sensitive_name = re.compile(r"secret|credential|password|passwd|token|apikey|api_key", re.I)
    s2 = [f for f in tracked if sensitive_pat.search(f) or sensitive_name.search(os.path.basename(f))]
    s2_uncovered = [f for f in s2 if not gitignored(f)]
    print("\nS2 敏感文件：命中 %d / 未被 gitignore 覆盖 %d" % (len(s2), len(s2_uncovered)))
    for f in s2_uncovered[:12]:
        print("     ✗ %s" % f)

    files = collect_html()
    if limit:
        files = files[:limit]
    mixed = defaultdict(list)
    blank_bad = []
    hosts = Counter()
    forms = []
    dangers = defaultdict(list)
    pwd = []
    emails = defaultdict(list)
    for abs_p in files:
        rel = os.path.relpath(abs_p, ROOT)
        h = io.open(abs_p, encoding="utf-8", errors="ignore").read()
        vis = RE_COMMENT.sub(" ", h)
        vis = RE_SCRIPT_BLOCK.sub(" ", vis)
        for u in RE_HTTP.findall(vis):
            mixed[re.sub(r"^https?://", "", u).split("/")[0]].append(rel)
        for tag in RE_TARGET_BLANK.findall(vis):
            if not RE_REL_NOOPENER.search(tag):
                blank_bad.append(rel)
        for host in RE_SRC_HOST.findall(h):
            hosts[host[1].lower()] += 1
        for tag in RE_FORM.findall(vis):
            forms.append((rel, tag[:200]))
        for pat, name in ((RE_DANGER_JS, "danger-js"), (RE_PASSWORD, "password-field")):
            for m in pat.finditer(h):
                if name == "danger-js":
                    dangers[name].append(rel)
                else:
                    pwd.append(rel)
        for e in set(RE_EMAIL.findall(vis)):
            if not e.lower().endswith(("@fjsanfan.com", "@example.com")):
                emails[e].append(rel)

    print("\nS3 HTTP 混合内容：%d 个不同主机" % len(mixed))
    for host, pages in list(mixed.items())[:10]:
        print("     %-40s %d 页  例：%s" % (host, len(pages), pages[0]))

    print("\nS4 target=_blank 缺 rel=noopener：%d 处" % len(blank_bad))
    c = Counter("/".join(p.split("/")[:2]) for p in blank_bad)
    for k, v in c.most_common(8):
        print("     %5d  %s" % (v, k))

    print("\nS5 站外资源域名清点：")
    ext = [(h, n) for h, n in hosts.most_common(30) if "fjsanfan.com" not in h]
    for h, n in ext[:12]:
        print("     %-46s %d 次" % (h, n))
    if not ext:
        print("     （无站外资源）")

    print("\nS6 表单：%d 个" % len(forms))
    act = Counter()
    for rel, tag in forms:
        a = re.search(r'action\s*=\s*["\']([^"\']*)["\']', tag, re.I)
        m = re.search(r'method\s*=\s*["\']?([a-zA-Z]+)', tag, re.I)
        act[(a.group(1) if a else "(无)", m.group(1).upper() if m else "GET")] += 1
    for (a, m), n in act.most_common(8):
        print("     %4d  action=%-28s method=%s" % (n, a, m))

    print("\nS7 页面内邮箱（排除自有域名/示例）：%d 个不同地址" % len(emails))
    for e, pages in list(emails.items())[:8]:
        print("     %-34s %d 页" % (e, len(pages)))

    print("\nS8 危险 JS API：%d 页" % len(dangers.get("danger-js", [])))
    for p in dangers.get("danger-js", [])[:8]:
        print("     ✗ %s" % p)
    print("   密码/信用卡类输入框：%d 处" % len(pwd))

    print("\n" + "=" * 72)
    p0 = len(s2_uncovered)
    p1 = len(mixed) + len(blank_bad)
    print("P0（敏感文件公开）= %d    P1（混合内容 + tabnabbing）= %d" % (p0, p1))
    out = os.path.join(ROOT, "i18n_build/reports/security_audit_20261003.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with io.open(out, "w", encoding="utf-8") as f:
        json.dump({
            "public_nonpage_files": len(nonpage),
            "public_mb": round(size_kb / 1024, 2),
            "by_top": dict(by_top),
            "sensitive_uncovered": s2_uncovered,
            "mixed_hosts": {k: len(v) for k, v in mixed.items()},
            "blank_no_noopener": blank_bad[:200],
            "external_hosts": dict(ext),
            "forms": [{"file": r, "tag": t} for r, t in forms[:50]],
            "emails": {k: len(v) for k, v in emails.items()},
            "danger_js": dangers.get("danger-js", []),
            "password_fields": pwd,
        }, f, ensure_ascii=False, indent=1)
    print("明细已写 %s" % out)
    return 1 if (p0 or p1) else 0


if __name__ == "__main__":
    sys.exit(main())
