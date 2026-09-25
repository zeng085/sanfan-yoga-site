#!/usr/bin/env python3
"""GEO 端点验收（2026-09-25）

为什么不用 `geo audit --url http://127.0.0.1:...`：
    geo-optimizer 的 fetch_url() 带三重反 SSRF 保护（DNS pinning + 重定向复检 +
    resolve_and_validate_url），**拒绝私网/本地地址**，本地起服务也审不了。
    因此这里改为「自己抓响应 → 直接喂 geo 的纯解析函数」，判分口径与线上完全一致：
        _audit_ai_discovery_from_responses()
        _audit_llms_from_response()

用法：
  python3 i18n_build/verify_geo_endpoints_20260925.py http://127.0.0.1:8899
  python3 i18n_build/verify_geo_endpoints_20260925.py https://fjsanfan.com
"""

from __future__ import annotations

import json
import sys

import requests
from geo_optimizer.core.audit_ai_discovery import _audit_ai_discovery_from_responses
from geo_optimizer.core.audit_llms import _audit_llms_from_response
from geo_optimizer.core.scoring import _score_ai_discovery, _score_llms

ENDPOINTS = [
    "llms.txt",
    "llms-full.txt",
    ".well-known/ai.txt",
    "ai/summary.json",
    "ai/faq.json",
    "ai/service.json",
]


def grab(base: str, path: str) -> requests.Response | None:
    """抓取并转成 requests.Response（geo 解析函数只读 .status_code / .text）。"""
    try:
        r = requests.get(f"{base.rstrip('/')}/{path}", timeout=20)
    except Exception as e:
        print(f"  ✗ {path}: {e}")
        return None
    resp = requests.Response()
    resp.status_code = r.status_code
    resp._content = r.content
    resp.encoding = r.encoding or "utf-8"
    resp.url = r.url
    return resp


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8899"
    print(f"验收目标：{base}\n")

    print("── 端点可达性 ──")
    resp = {p: grab(base, p) for p in ENDPOINTS}
    for p, r in resp.items():
        code = r.status_code if r else "ERR"
        size = len(r.content) if r else 0
        print(f"  {code}  {p:<24} {size:>7} bytes")

    print("\n── AI Discovery（geo 判分口径）──")
    a = _audit_ai_discovery_from_responses(
        resp[".well-known/ai.txt"],
        resp["ai/summary.json"],
        resp["ai/faq.json"],
        resp["ai/service.json"],
    )
    rows = [
        ("/.well-known/ai.txt", a.has_well_known_ai, "非空即可"),
        ("/ai/summary.json", a.has_summary and a.summary_valid, "name>=3 且 description>=20"),
        ("/ai/faq.json", a.has_faq, f"q>=10 / a>=20，合规 {a.faq_count} 条"),
        ("/ai/service.json", a.has_service, "name>=3 且 capabilities 非空"),
    ]
    for name, ok, note in rows:
        print(f"  {'✓' if ok else '✗'} {name:<22} {note}")
    sc_a = _score_ai_discovery(a)
    print(f"  >>> ai_discovery 得分 {sc_a} / 6   （端点数 {a.endpoints_found}/4）")

    print("\n── llms.txt（geo 判分口径）──")
    l = _audit_llms_from_response(resp["llms.txt"], r_full=resp["llms-full.txt"])
    rows = [
        ("found", l.found, "文件存在"),
        ("has_h1", l.has_h1, "首个非空行是 # H1"),
        ("has_blockquote", l.has_blockquote, "> 摘要"),
        ("has_sections", l.has_sections, f"## 小节 {l.sections_count} 个"),
        ("has_links", l.has_links, f"markdown 链接 {l.links_count} 条（阈值 3）"),
        ("word_count>=1000", l.word_count >= 1000, f"当前 {l.word_count} 词"),
        ("has_full", l.has_full, "/llms-full.txt 存在"),
    ]
    for name, ok, note in rows:
        print(f"  {'✓' if ok else '✗'} {name:<20} {note}")
    if l.validation_warnings:
        print(f"  ⚠ 规范告警：{l.validation_warnings}")
    else:
        print("  ✓ 规范告警：无")
    sc_l = _score_llms(l)
    print(f"  >>> llms 得分 {sc_l} / 16")

    total = sc_a + sc_l
    print(f"\n══ 本轮合计 {total} / 22 分 ══")

    # 与站点既有事实的一致性抽查
    print("\n── 与站上事实一致性抽查 ──")
    try:
        faq = json.loads(resp["ai/faq.json"].text)
        svc = json.loads(resp["ai/service.json"].text)
        print(f"  FAQ 条数：{len(faq['faqs'])}  （站上 faq.html 的 FAQPage 同源）")
        print(f"  MOQ 声明：{svc['service']['moq']['tpeYogaMats']}")
        print(f"  认证声明：{', '.join(svc['service']['certifications'])}")
        print(f"  联系：WhatsApp {svc['service']['contact']['whatsapp']} / {svc['service']['contact']['email']}")
    except Exception as e:
        print(f"  ✗ {e}")
        return 1

    return 0 if sc_a == 6 and sc_l >= 14 else 1


if __name__ == "__main__":
    sys.exit(main())
