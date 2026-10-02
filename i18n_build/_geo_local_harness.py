#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GEO 本地审计 harness（2026-10-02）

为什么需要它
------------
`geo audit` 与 geo_optimizer 内所有 `audit_*` 函数都经过 `utils.http.fetch_url`，
而该函数**内置反 SSRF 防护**（skill 实测口径第 1 条）：
  - 传 `http://127.0.0.1:8866` → `return None, "Unsafe URL: ..."` → 所有判据凭空变 0/False
    （实测 `audit_robots_txt("http://127.0.0.1:8866")` 返回 `found=False`，而 curl 该地址是 200）

于是本 harness 做两件事：
  1. **把 `fetch_url` 换成磁盘垫片** —— URL 路径映射到仓库根目录下的真实文件，
     返回带 `.status_code` / `.text` / `.headers` 的响应对象。不碰网络 → 确定性。
  2. **base_url 仍用 `https://fjsanfan.com`** —— 这样 canonical / 内链 / hreflang /
     实体一致性等判据看到的是**生产形态的 URL**，判分与线上同构。

用法
----
    from _geo_local_harness import install, local_root, ROOT
    install()                      # 幂等，可重复调用
    res = run_full_audit("https://fjsanfan.com/blog/xxx.html")

⚠️ 本 harness 只做「就绪度」审计。它**不能**证明页面已被 Google / AI 收录或引用
    ——那些必须等部署后用真实抓取验证。
"""
from __future__ import annotations

import copy
import mimetypes
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://fjsanfan.com"

# 与 audit.py 一致的「干净 DOM」构造
_CLEAN_TAGS = ("script", "style", "noscript", "template")


def local_root() -> Path:
    return ROOT


class _Resp:
    """最小响应对象：只有 audit 函数真正读的字段。"""

    __slots__ = ("status_code", "text", "headers", "url", "content", "reason")

    def __init__(self, status_code: int, text: str = "", url: str = "",
                 ctype: str = "text/html; charset=utf-8") -> None:
        self.status_code = status_code
        self.text = text
        self.headers = {"content-type": ctype}
        self.url = url
        self.content = text.encode("utf-8", "replace")
        self.reason = "OK" if status_code == 200 else "Not Found"

    def json(self):
        import json as _json
        return _json.loads(self.text)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def url_to_path(url: str) -> Path | None:
    """`https://fjsanfan.com/a/b.html` → `<ROOT>/a/b.html`（越界返回 None）。"""
    from urllib.parse import urlparse
    p = urlparse(url)
    raw = p.path or "/"
    # 查询串/片段不属于文件系统
    rel = raw.lstrip("/")
    if rel == "" or raw.endswith("/"):
        rel = rel + "index.html"
    cand = (ROOT / rel).resolve()
    try:
        cand.relative_to(ROOT.resolve())
    except ValueError:
        return None          # 路径穿越 → 拒绝
    return cand


def _ctype_for(p: Path) -> str:
    if p.suffix == ".txt":
        return "text/plain; charset=utf-8"
    if p.suffix == ".xml":
        return "application/xml; charset=utf-8"
    if p.suffix == ".json":
        return "application/json; charset=utf-8"
    if p.suffix in (".js",):
        return "application/javascript; charset=utf-8"
    if p.suffix in (".css",):
        return "text/css; charset=utf-8"
    guessed = mimetypes.guess_type(p.name)[0]
    return (guessed or "application/octet-stream") + (
        "; charset=utf-8" if not guessed or guessed.startswith(("text", "application/json", "application/xml")) else ""
    )


def fetch_from_disk(url: str, *_a, **_kw):
    """fetch_url 的磁盘替身，签名容忍 (url, ...) 任意附加参数。

    返回契约与真 fetch_url 一致：`(response, None)` 或 `(None, err_str)`。
    """
    p = url_to_path(url)
    if p is None:
        return None, f"Unsafe/out-of-root URL: {url}"
    if not p.exists() or not p.is_file():
        return None, f"404 Not Found (disk): {p.relative_to(ROOT)}"
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:                                   # noqa: BLE001
        return None, f"read error: {type(e).__name__}: {e}"
    # 二进制资源（图片等）：audit 只关心状态码，文本置空避免解码噪声
    if p.suffix.lower() in (".webp", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2"):
        return _Resp(200, "", url, _ctype_for(p)), None
    return _Resp(200, text, url, _ctype_for(p)), None


_INSTALLED = False


def install(verbose: bool = False) -> int:
    """把 geo_optimizer 各个模块里的 `fetch_url` 全换成磁盘垫片。返回替换处数。"""
    global _INSTALLED
    import geo_optimizer.utils.http as _http           # noqa: F401
    import geo_optimizer.core.audit as _audit          # 触发全部子模块导入

    n = 0
    _http.fetch_url = fetch_from_disk
    n += 1
    for name, mod in list(sys.modules.items()):
        if not name.startswith("geo_optimizer"):
            continue
        if getattr(mod, "fetch_url", None) is not None and mod is not _http:
            try:
                mod.fetch_url = fetch_from_disk
                n += 1
            except Exception:                            # noqa: BLE001
                pass
    _INSTALLED = True
    if verbose:
        print(f"[harness] fetch_url 已垫为磁盘读取，共替换 {n} 处；SITE={SITE}；ROOT={ROOT}")
    return n


def soup_pair(html: str):
    """返回 (soup, soup_clean)，与 audit.py 内部构造完全一致。"""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    soup_clean = copy.deepcopy(soup)
    for tag in soup_clean(_CLEAN_TAGS):
        tag.decompose()
    return soup, soup_clean


def page_path(rel: str) -> Path:
    return ROOT / rel.lstrip("/")
