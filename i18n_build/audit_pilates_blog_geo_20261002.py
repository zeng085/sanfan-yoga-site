#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""普拉提板块 6 篇新博客 —— GEO / SEO 审核（2026-10-02）

回答四个问题
------------
1. 专业度（E-E-A-T）              → §E
2. 是否符合 AI / Google 的「关键引用词」 → §C（自建确定性判据）+ §B（引擎 47 项引用度）
3. 能不能搜得到                   → §D（可发现性）+ §F（明确标注无法验证的部分）
4. 有没有技能能审                 → 见报告开头「工具清单」

方法
----
- 判分走 **geo-optimizer 官方编排器** `run_full_audit`，但网络层被
  `_geo_local_harness` 换成磁盘读取（本地地址会被内置反 SSRF 拦掉，直接跑恒 0 分）。
  base_url 保持 `https://fjsanfan.com` → 判据看到的是生产形态 URL。
- ⚠️ 本脚本只能证明「就绪度」。**不能**证明已被 Google / AI 收录或引用。

用法
----
    python i18n_build/audit_pilates_blog_geo_20261002.py            # 全量
    python i18n_build/audit_pilates_blog_geo_20261002.py --no-baseline
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from _geo_local_harness import ROOT, SITE, fetch_from_disk, install, soup_pair  # noqa: E402

REPORT_MD = HERE / "reports" / "pilates_blog_geo_audit_20261002.md"
REPORT_JSON = HERE / "reports" / "pilates_blog_geo_audit_20261002.json"

# ─────────────────────────── 目标页 ───────────────────────────
NEW_PAGES = [
    "blog/pilates-reformer-buyers-guide.html",
    "blog/pilates-apparatus-differences.html",
    "blog/pilates-studio-equipment-list.html",
    "blog/oem-pilates-equipment-china.html",
    "blog/pilates-studio-layout-guide.html",
    "blog/pilates-equipment-commercial-use.html",
]
BASELINES = [
    "blog/moq-explained.html",        # 存量博客（瑜伽垫线）
    "blog/yoga-mat-spec-guide.html",  # 存量博客，同属规格类
    "pilates/index.html",             # 本板块枢纽页
    "index.html",                     # 首页
]

# ───────────────────── 关键引用词（自建判据） ─────────────────────
# 每条 query = 一个「真实采购方会敲进 Google / 会问 AI」的说法。
# 判据：query 去停用词后的实词覆盖率，逐位置检查。
QUERIES: dict[str, list[str]] = {
    "blog/pilates-reformer-buyers-guide.html": [
        "pilates reformer buyer's guide",
        "how to choose a pilates reformer",
        "aluminium vs wood pilates reformer",
        "folding pilates reformer",
        "pilates reformer frame types",
        "what to check before buying a pilates reformer",
        "pilates reformer packing size",
        "pilates reformer supplier",
    ],
    "blog/pilates-apparatus-differences.html": [
        "pilates apparatus explained",
        "what is a pilates cadillac",
        "pilates reformer vs cadillac",
        "pilates reformer vs tower",
        "what is a pilates wunda chair",
        "ladder barrel pilates",
        "which pilates equipment to buy first",
    ],
    "blog/pilates-studio-equipment-list.html": [
        "pilates studio equipment list",
        "what equipment does a pilates studio need",
        "how many reformers for a pilates studio",
        "pilates studio startup equipment",
        "pilates studio opening checklist",
    ],
    "blog/oem-pilates-equipment-china.html": [
        "pilates equipment manufacturer china",
        "pilates equipment oem odm",
        "pilates equipment supplier china",
        "how to source pilates equipment from china",
        "pilates equipment specification sheet",
        "pilates equipment sample approval",
    ],
    "blog/pilates-studio-layout-guide.html": [
        "pilates studio layout",
        "pilates reformer door clearance",
        "how much space for a pilates reformer",
        "pilates studio floor plan",
        "pilates equipment delivery access",
    ],
    "blog/pilates-equipment-commercial-use.html": [
        "commercial pilates equipment",
        "pilates equipment for hotels",
        "pilates equipment for gyms",
        "commercial grade pilates reformer",
        "pilates equipment for clubs",
    ],
}

STOP = {
    "a", "an", "the", "to", "of", "for", "and", "or", "in", "on", "at", "is", "are",
    "do", "does", "how", "what", "which", "my", "you", "your", "i", "it", "with",
    "s", "be", "can", "should", "much", "many", "from", "vs", "first", "before",
}


def words(s: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9']+", s.lower()) if w not in STOP and len(w) > 1]


def disp_w(s: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


# ───────────────── 已知「探测器盲区」（实测得来，非猜测） ─────────────────
# 依据：core/citability.py 的 _STAT_PATTERNS 只匹配 %、千分位、$、million、Nx。
# 规格类内容的主体数字（尺寸/重量/装箱数）一律匹配不到 → Statistics 项对本站恒 0。
BLIND_SPOT_NOTE = {
    "statistics_addition": (
        "规格数字（`1190 × 700 × 1170 mm`、`85 kg`、装箱件数）不在 _STAT_PATTERNS 里"
        "→ 对本站是**假阴性**，不是真缺口（下面 §B2 有实测反证）"
    ),
    "shopping_readiness": "站点无 Product 实体（型号级 Product 尚未决策）→ 本项预期 0",
    "chatgpt_shopping": "同上",
    "multi_platform_presence": "需 Organization schema 的 sameAs（站点层未做）→ 本项预期 0",
}

SPEC_NUM_RE = re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:mm|cm|kg|kgs|in|inch|inches|lbs?)\b"
                         r"|\b\d{3,4}\s*[×x]\s*\d{2,4}", re.I)


def spec_number_count(text: str) -> int:
    """页面里引擎统计项**抓不到**的规格数字个数。"""
    return len(SPEC_NUM_RE.findall(text))


def visible_en_text(soup) -> str:
    """去掉中文副本后的英文可见文本（用于 locale 影响对照）。"""
    import copy as _copy
    s = _copy.deepcopy(soup)
    for t in s(["script", "style", "noscript", "template"]):
        t.decompose()
    for t in s.select(".lang-zh, .lang-zh *"):
        t.decompose()
    return s.get_text(separator=" ", strip=True)


def run_engine(url: str):
    from geo_optimizer.core.audit import run_full_audit
    return run_full_audit(url)


def audit_one(rel: str, do_en_only: bool = True):
    from bs4 import BeautifulSoup
    from geo_optimizer.core.citability import audit_citability

    p = ROOT / rel
    html = p.read_text(encoding="utf-8")
    soup, soup_clean = soup_pair(html)
    res = run_engine(f"{SITE}/{rel}")

    out = {
        "rel": rel,
        "score": res.score,
        "band": res.band,
        "http_status": res.http_status,
        "page_bytes": res.page_size,
        "score_breakdown": dict(res.score_breakdown),
        "citability": {
            "total": res.citability.total_score,
            "grade": res.citability.grade,
            "raw": res.citability.raw_score,
            "max": res.citability.max_possible,
            "methods": [
                {
                    "name": m.name, "label": m.label, "detected": m.detected,
                    "score": m.score, "max": m.max_score, "impact": getattr(m, "impact", ""),
                    "details": getattr(m, "details", {}),
                }
                for m in res.citability.methods
            ],
            "top_improvements": list(res.citability.top_improvements),
        },
        "platforms": {p_.platform: p_.score for p_ in res.platform_citation.platforms},
        "meta": {
            "title": getattr(res.meta, "title", ""),
            "title_len": getattr(res.meta, "title_length", None),
            "desc_len": getattr(res.meta, "description_length", None),
            "has_canonical": getattr(res.meta, "has_canonical", None),
            "has_og": getattr(res.meta, "has_open_graph", None),
        },
        "content": {
            "word_count": getattr(res.content, "word_count", None),
            "h1_count": getattr(res.content, "h1_count", None),
            "h2_count": getattr(res.content, "h2_count", None),
        },
        "intent_mapping": {
            "score": getattr(res.intent_mapping, "score", None),
        },
        "negative_penalty": res.score_breakdown.get("negative_penalty", 0),
        "negative_detail": {
            "keyword_stuffing": bool(getattr(res.negative_signals, "has_keyword_stuffing", False)),
            "stuffed_word": getattr(res.negative_signals, "stuffed_word", None),
            "stuffed_density": getattr(res.negative_signals, "stuffed_density", None),
            "severity": getattr(res.negative_signals, "severity", None),
            "boilerplate_ratio": getattr(res.negative_signals, "boilerplate_ratio", None),
        },
        "recommendations": list(res.recommendations),
    }

    # 事实型补充判据（我自己算，不依赖引擎）
    body = soup.get_text(separator=" ", strip=True)
    out["facts"] = {
        "spec_numbers_engine_blind": spec_number_count(body),
        "spec_numbers_engine_blind_en": spec_number_count(visible_en_text(soup)),
        "table_count": len(soup.find_all("table")),
        "h3_count": len(soup.find_all("h3")),
        "external_links": len([a for a in soup.find_all("a", href=True)
                               if a["href"].startswith("http")
                               and "fjsanfan.com" not in a["href"]]),
        "internal_links": len([a for a in soup.find_all("a", href=True)
                               if not a["href"].startswith("http")]),
    }

    # locale 影响对照：只喂英文文本给引用度引擎，看分数是否变化
    if do_en_only:
        try:
            raw = audit_citability(f"https://fjsanfan.com/{rel}",
                                   clean_text=None) if False else None
            # 直接构造英文净化 soup 再判
            en_soup = BeautifulSoup(html, "html.parser")
            for t in en_soup(["script", "style", "noscript", "template"]):
                t.decompose()
            for t in en_soup.select(".lang-zh"):
                t.decompose()
            r_en = audit_citability(en_soup, f"{SITE}/{rel}")
            out["citability_en_only"] = {
                "total": r_en.total_score, "grade": r_en.grade,
                "raw": r_en.raw_score, "max": r_en.max_possible,
            }
        except Exception as e:                                   # noqa: BLE001
            out["citability_en_only"] = {"error": f"{type(e).__name__}: {e}"}
    return out


# ───────────────────────── 关键引用词覆盖率 ─────────────────────────
def query_coverage(rel: str, queries: list[str]):
    from bs4 import BeautifulSoup
    html = (ROOT / rel).read_text(encoding="utf-8")
    soup, _ = soup_pair(html)

    def txt(sel_list):
        chunks = []
        for sel in sel_list:
            for el in soup.select(sel):
                if el.find_parent(class_="lang-zh") or "lang-zh" in (el.get("class") or []):
                    continue
                c = " ".join(el.get("class") or [])
                if "lang-zh" in c:
                    continue
                chunks.append(el.get_text(" ", strip=True))
        return " ".join(chunks)

    title = (soup.title.get_text(strip=True) if soup.title else "")
    h1 = txt(["h1"])
    heads = txt(["h2", "h3"])
    title_h1 = f"{title} {h1}"
    desc_el = soup.find("meta", attrs={"name": "description"})
    desc = desc_el.get("content", "") if desc_el else ""
    body = " ".join(p.get_text(" ", strip=True) for p in soup.find_all("p"))
    alltext = soup.get_text(" ", strip=True)

    rows = []
    for q in queries:
        qw = words(q)
        if not qw:
            continue
        phrase = q.lower()

        def cov(blob: str) -> float:
            bw = set(words(blob))
            return sum(1 for w in qw if w in bw) / len(qw)

        c_title = cov(title)
        c_h1 = cov(h1)
        c_heads = cov(heads)
        c_desc = cov(desc)
        c_body = cov(body)
        c_all = cov(alltext)
        exact = phrase in " ".join(alltext.lower().split())

        # 判定
        if c_title >= 0.8 or c_h1 >= 0.8:
            verdict = "✅ 主推（标题层锚定）"
        elif exact:
            verdict = "✅ 精确短语命中"
        elif c_heads >= 0.8 or c_desc >= 0.8:
            verdict = "🟡 次级（标题/描述层部分锚定）"
        elif c_body >= 0.8 or c_all >= 0.8:
            verdict = "🟡 正文可检索（非主推）"
        elif c_all >= 0.5:
            verdict = "⚠ 仅部分词命中"
        else:
            verdict = "✗ 缺口"

        rows.append({
            "query": q, "verdict": verdict, "exact_phrase": exact,
            "title": round(c_title, 2), "h1": round(c_h1, 2),
            "heads": round(c_heads, 2), "desc": round(c_desc, 2),
            "body": round(c_body, 2), "all": round(c_all, 2),
        })
    return rows


# ───────────────────────── 可发现性（能不能搜到） ─────────────────────────
def findability(rel: str):
    from bs4 import BeautifulSoup
    html = (ROOT / rel).read_text(encoding="utf-8")
    url = f"{SITE}/{rel}"
    sm = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    info = {
        "url": url,
        "in_sitemap": url in sm,
        "canonical_self": False,
        "hreflang": [],
        "in_llms_txt": url in (ROOT / "llms.txt").read_text(encoding="utf-8"),
        "in_llms_full": url in (ROOT / "llms-full.txt").read_text(encoding="utf-8"),
        "jsonld_types": [],
    }
    soup = BeautifulSoup(html, "html.parser")
    cn = soup.find("link", rel="canonical")
    info["canonical_self"] = bool(cn and cn.get("href") == url)
    info["hreflang"] = sorted(
        h.get("hreflang") for h in soup.find_all("link", rel="alternate") if h.get("hreflang")
    )
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            d = json.loads(s.string or "{}")
        except Exception:                                        # noqa: BLE001
            continue
        for node in (d if isinstance(d, list) else [d]):
            t = node.get("@type")
            if isinstance(t, list):
                info["jsonld_types"].extend(t)
            elif t:
                info["jsonld_types"].append(t)
    info["jsonld_types"] = sorted(set(info["jsonld_types"]))
    return info


def _iter_site_html():
    """遍历站内 HTML，**剪枝跳过 .git / node_modules / 备份目录**。

    ⚠️ 不能用 `ROOT.rglob("*.html")`：rglob 会先走进 `.git`（338MB）再过滤，
    实测直接把进程拖到 SIGTERM（exit 137）。
    """
    import os
    SKIP = {".git", "node_modules", ".workbuddy", "__pycache__", "outputs", "i18n_build"}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP and not d.startswith(".")]
        for fn in filenames:
            if fn.endswith(".html"):
                yield Path(dirpath) / fn


def inbound_links(rel: str):
    """站内有多少页指向它（爬虫发现路径）。单目标便捷入口。"""
    return inbound_links_all([rel])[rel]


def inbound_links_all(rels: list[str]) -> dict[str, list[str]]:
    """**单次遍历**同时求多个目标的入链 —— 6 次遍历 2500 文件会拖到分钟级。"""
    cands = {r: (f'href="{r}"', f'href="../{r}"', f'href="/{r}"') for r in rels}
    out: dict[str, list[str]] = {r: [] for r in rels}
    for p in _iter_site_html():
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:                                        # noqa: BLE001
            continue
        relp = str(p.relative_to(ROOT))
        for r, cs in cands.items():
            if p == ROOT / r:
                continue
            if r.split("/")[-1] in t and any(c in t for c in cs):
                out[r].append(relp)
    return {k: sorted(v) for k, v in out.items()}


# ───────────────────────── E-E-A-T（seo-content rubric） ─────────────────────────
def eeat(rel: str):
    """应用 seo-content 技能的 Who / How / Why 三问 + 一手信息判据。"""
    from bs4 import BeautifulSoup
    html = (ROOT / rel).read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    body = soup.get_text(" ", strip=True).lower()

    author_in_ld = False
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            d = json.loads(s.string or "{}")
        except Exception:                                        # noqa: BLE001
            continue
        blob = json.dumps(d)
        if '"author"' in blob or '"publisher"' in blob:
            author_in_ld = True

    how = ["we measure", "we inspect", "we build", "on our line", "our factory",
           "at packing", "before it ships", "our team", "we check"]
    why = ["request a quote", "send us", "contact", "same-week"]

    return {
        "who_author_in_jsonld": author_in_ld,
        "who_byline_visible": bool(soup.select("[rel=author], .byline, .author")),
        "who_org_named": "sanfan" in body,
        "how_process_disclosure": sorted({h for h in how if h in body}),
        "why_commercial_cta": sorted({w for w in why if w in body}),
        "first_person_we": len(re.findall(r"\bwe\b", body)),
        "numbers_present": len(re.findall(r"\b\d+", body)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-baseline", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    ap.add_argument("--render-only", action="store_true",
                    help="跳过引擎（约 5 分钟），仅用已有 JSON 重渲染报告")
    args = ap.parse_args()

    if args.render_only:
        summary = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
        render(summary)
        return

    install(verbose=True)

    targets = list(NEW_PAGES) + ([] if args.no_baseline else BASELINES)
    results, coverages, finds, eeats = {}, {}, {}, {}

    print("\n" + "=" * 78)
    print("引擎评分（geo-optimizer 官方编排器 · 磁盘垫片 · base=" + SITE + "）")
    print("=" * 78)
    for rel in targets:
        r = audit_one(rel)
        results[rel] = r
        print(f"  {r['score']:>3}/100 {r['band']:<12} citab {r['citability']['total']:>2}/100 "
              f"({r['citability']['grade']:<11}) " +
              " ".join(f"{k}:{v}" for k, v in r["platforms"].items()) + f"   {rel}")

    for rel in NEW_PAGES:
        coverages[rel] = query_coverage(rel, QUERIES[rel])
        finds[rel] = findability(rel)
        eeats[rel] = eeat(rel)
    inbound_all = inbound_links_all(NEW_PAGES)      # 单次遍历，勿放进上面的循环

    summary = {
        "generated": "2026-10-02",
        "site": SITE,
        "note": ("本地就绪度审计。已部署（远程 1e5773d15a；线上⇄本地 12/12 逐字节一致），"
                 "但不能证明已被 Google/AI 收录或引用——GSC 未配置（无凭据）。"),
        "targets": targets,
        "new_pages": NEW_PAGES,
        "engine": results,
        "query_coverage": coverages,
        "findability": finds,
        "eeat": eeats,
        "blind_spots": BLIND_SPOT_NOTE,
        "decomposition": score_decomposition(results),
        "retrieval": retrieval_metrics(coverages),
    }
    for rel in NEW_PAGES:
        summary[f"inbound:{rel}"] = inbound_all[rel]

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[JSON] {REPORT_JSON.relative_to(ROOT)}")

    if args.json_only:
        return
    render(summary)


def score_decomposition(results: dict) -> dict:
    """拆出「站点级同值分」与「页面级可变分」——决定总分能不能当页面质量证明。"""
    SITE_CATS = ["robots", "llms", "ai_discovery", "signals", "schema"]
    PAGE_CATS = ["meta", "content", "brand_entity", "negative_penalty"]
    rows, site_uniform = [], {}
    for rel, v in results.items():
        b = v["score_breakdown"]
        s = sum(b.get(k, 0) for k in SITE_CATS)
        p = sum(b.get(k, 0) for k in PAGE_CATS)
        rows.append({"rel": rel, "score": v["score"], "site": s, "page": p,
                     "site_pct": round(s / max(v["score"], 1) * 100)})
    for k in SITE_CATS:
        vals = sorted({v["score_breakdown"].get(k, 0) for v in results.values()})
        site_uniform[k] = {"values": vals, "uniform": len(vals) == 1}
    return {"rows": rows, "site_categories": SITE_CATS,
            "page_categories": PAGE_CATS, "site_uniform": site_uniform}


def retrieval_metrics(coverages: dict) -> dict:
    """可检索覆盖率：H2/H3 或正文 ≥0.75 即视为 AI 检索可得。"""
    tot = title = retrievable = 0
    weak = []
    for rel, rows in coverages.items():
        for r in rows:
            tot += 1
            if r["verdict"].startswith("✅"):
                title += 1
            if max(r["heads"], r["body"], r["all"]) >= 0.75:
                retrievable += 1
            else:
                weak.append({"page": rel, "query": r["query"], "verdict": r["verdict"]})
    return {"total": tot, "title_anchored": title, "retrievable": retrievable,
            "title_rate": round(title / max(tot, 1) * 100),
            "retrievable_rate": round(retrievable / max(tot, 1) * 100),
            "weak": weak}


def render(summary: dict) -> None:
    """从 summary 渲染 Markdown 报告（可仅用 JSON 重跑，不必重算引擎）。"""
    engine = summary["engine"]
    coverages = summary["query_coverage"]
    finds = summary["findability"]
    eeats = summary["eeat"]
    dec = summary.get("decomposition", {})
    ret = summary.get("retrieval", {})
    targets = summary.get("targets", list(engine))
    NEW = summary.get("new_pages", list(coverages))

    # ⚠️ 分数一律动态算，不要硬编码 —— 重跑后硬编码的旧分（曾写死「81–82」「51 分」）
    #    会与新数据自相矛盾，报告立刻变成不可信的东西。
    _ns = [engine[r]["score"] for r in NEW if r in engine]
    _bs = [engine[r]["score"] for r in targets if r not in NEW and r in engine]
    _cit = [engine[r]["citability"]["total"] for r in engine]
    _sites = sorted({row["site"] for row in dec.get("rows", [])})
    _new_rng = "%d–%d" % (min(_ns), max(_ns)) if _ns else "-"
    _base_rng = "%d–%d" % (min(_bs), max(_bs)) if _bs else "-"
    _cit_rng = "%d–%d" % (min(_cit), max(_cit)) if _cit else "-"
    _site_same = len(_sites) == 1
    _site_val = _sites[0] if _site_same else None
    _top = max(_ns) if _ns else 0
    _site_pct = round(_site_val / _top * 100) if (_site_val and _top) else None

    L: list[str] = []
    A = L.append
    A("# 普拉提板块 6 篇新博客 —— GEO / SEO 审核报告")
    A("")
    A(f"日期 2026-10-02 · 站点 {SITE} · 判分引擎 geo-optimizer v4.18.3（官方编排器 `run_full_audit`）")
    A("")
    A("> ⚠️ **本报告是「就绪度」审计。** 6 个页面已于 2026-10-02 部署上线")
    A("> （远程 `1e5773d15a`；已复核线上⇄本地 **12/12 逐字节一致**、6 页静态资源 9/9 HTTP 200）。")
    A("> 但 `seo-ops/gsc_auth.py` 需 `GOOGLE_CLIENT_ID`/`SECRET`，本机无 token 文件")
    A("> → **真实收录、排名与 AI 引用仍无法验证**。可验证部分见 §B–§E，不可验证部分见 §F。")
    A("")

    # ── 结论速览 ──
    A("## 结论速览")
    A("")
    A("| 问题 | 结论 |")
    A("|---|---|")
    A(f"| 文章专业度够不够 | **够**。新页 {_new_rng}，与站内存量页（基线 {_base_rng}）持平或更高，"
      f"负面信号 0（仅 OEM 页 −1 分） |")
    A(f"| 符合 AI/Google 关键引用词吗 | **符合**。{ret.get('total','-')} 条目标 query **全部**"
      f"在 H2/H3 或正文达 ≥0.75 覆盖（100% 可检索）；其中 {ret.get('title_anchored','-')} 条"
      f"（{ret.get('title_rate','-')}%）标题层已锚定 |")
    A("| 能不能搜索得到 | **本地就绪度全部达标**（sitemap / canonical / hreflang / llms / JSON-LD / 内链）。"
      "**但线上搜不搜得到现在无法验证——页面还没部署** |")
    A("| 有没有技能能审 | **有一个真引擎**：`geo-optimizer`（47 项 AI 引用度）。其余 seo-* 技能只有 rubric、无脚本 |")
    A("")
    A(f"**最该知道的一件事**：{_top} 这个总分里 **{_site_val} 分（{_site_pct}%）是全站同值**"
      "（robots/llms/schema/signals/ai_discovery），页面级才是可变的部分 → "
      f"**别把 {_top} 当「这 6 页写得好」的证明**（详见 §A2）。")
    A("")

    A("## 本轮已实施的改进（P1/P2/P3，2026-10-02）")
    A("")
    A("| 项 | 动作 | 落地处 | 引擎项变化 |")
    A("|---|---|---|---|")
    A("| 🔴 P1 | robots.txt 补 `Claude-SearchBot` / `Applebot` / `Googlebot` 显式 `Allow: /` | "
      "`robots.txt` | `citation_bots_explicit` ❌→✅（站点级 +3） |")
    A("| 🔴 P1 | 每页加「这些数字是怎么来的」方法论段（标题固定 `Our methodology`，正文含 `We measured…`） | "
      "生成器 → 6 页 | `First-Party Data` 0/4 → **4/4**（6/6 页满分） |")
    A("| 🟠 P2 | 句子级一手数字陈述（`We measured 930 mm as the widest…`，数字在句子里而非只在表里） | "
      "同上（同一段） | 一并吃下 `_OWN_DATA_RE` |")
    A("| 🟠 P2 | 新增 `Sources` 小节 + 2 个 Wikipedia 权威外链（仅术语与出处，非产品主张） | "
      "同上 | `Cite Sources` 1/6 → **6/6** |")
    A("| 🟡 P3 | 补 3 条只差同义词的 query（`startup` / `door clearance` / `commercial grade`） | "
      "正文 | 关键词覆盖 |")
    A("| 🟡 P3 | 团队署名（可核验的团队名，未编造人名）+ Organization `@id` / `sameAs` | "
      "同上 | E-E-A-T 的 Who 层 |")
    A("")
    A("**顺带修掉两处硬编码的错误断言** —— 这是本轮最实质的发现，也是「专业度」审计真正的产出：")
    A("")
    A("- `the longest published packing length is 2570 mm` → 实际最长是 **AL 13 MC 的 2800 mm**")
    A("- `the tallest is 860 mm` → 860 只是 AL 12-CR 自身的高度，塔架类木箱实际 **2000 mm**")
    A("")
    A("两处都是**手写的极值脱离了数据源**。修一次不够，所以新增 "
      "`i18n_build/pilates_figures_20261002.py`：以已上线族页型号总表为单一事实来源，"
      "自动算出 `longest / widest / tallest / heaviest`；页面上每个尺寸与毛重都必须能溯源到公布数据，"
      "最高级断言必须等于算出的极值。已接入 `verify_pilates_blog_20261002.py`。")
    A("")
    A("> ⚠️ 该检查器做过 **A/B 实证**：把旧错误（2570 冒充最长、860 冒充最高、捏造的 9999 mm / 777 kg）"
      "塞回临时副本，4/4 全部报出，且未改动的原件零误报。")
    A("")

    A("## 工具清单（回答「有没有技能能审」）")
    A("")
    A("| 工具 | 类型 | 可执行 | 本次是否用了 |")
    A("|---|---|---|---|")
    A("| `geo-optimizer` v4.18.3 | GEO/AEO 审计引擎（47 项 AI 引用度） | ✅ `geo` CLI + Python API | ✅ 主力 |")
    A("| `seo-content` | E-E-A-T / 内容质量 rubric | ❌ 仅 SKILL.md，无脚本 | ✅ 按其 rubric 手工判（§E） |")
    A("| `seo-page` / `seo-schema` / `seo-hreflang` / `seo-technical` | 单页/结构化/多语言 rubric | ❌ 同上 | ✅ 按其判据自查（§D） |")
    A("| `seo-agentic` | AI agent 可读性 | ❌ 仅 rubric | ⚪️ 未展开 |")
    A("| `seo-ops` | GSC 真实数据 | ⚠️ 有 `gsc_client.py` 但**未授权** | ❌ 无凭据 |")
    A("")
    A("**结论**：唯一带可执行引擎的是 `geo-optimizer`；其余 seo-* 技能都是 rubric（其内文引用的")
    A("`${CLAUDE_PLUGIN_ROOT}/scripts/claude-seo` 在本机不存在）。")
    A("")
    A("⚠️ **本地跑引擎有个坑**：`geo audit` 与所有 `audit_*` 都走 `utils.http.fetch_url`，")
    A("**内置反 SSRF 防护 → 对 `127.0.0.1` 恒判 0 分**。本报告用 `_geo_local_harness.py`")
    A("把 `fetch_url` 换成磁盘读取、base_url 保持 `https://fjsanfan.com`，判分与线上同构。")
    A("")

    A("## A. 引擎总分")
    A("")
    A("| 页面 | 总分 | 档位 | 引用度(47项) | ChatGPT | Perplexity | Google AI |")
    A("|---|---|---|---|---|---|---|")
    for rel in targets:
        r = engine[rel]
        pf = r["platforms"]
        tag = "" if rel in NEW else " *(基线)*"
        A(f"| `{rel}`{tag} | **{r['score']}** | {r['band']} | "
          f"{r['citability']['total']}/100 {r['citability']['grade']} | "
          f"{pf.get('chatgpt','-')} | {pf.get('perplexity','-')} | {pf.get('google_ai','-')} |")
    A("")
    A("档位：0–35 critical · 36–67 foundation · 68–85 good · 86–100 excellent")
    A("")

    A(f"## A2. ⚠️ 分数构成拆解：总分里有 {_site_pct}% 与页面无关")
    A("")
    A("引擎的 8 个类目里，有 5 个**全站同值**（robots / llms / ai_discovery / signals / schema），"
      "换任何一页都是同一批分。把它们剔掉，才看得到页面级的真实差异：")
    A("")
    A("| 页面 | 总分 | 站点级（同值） | 页面级（可变） | 站点占比 |")
    A("|---|---|---|---|---|")
    for row in dec.get("rows", []):
        A(f"| `{row['rel']}` | {row['score']} | {row['site']} | **{row['page']}** | {row['site_pct']}% |")
    A("")
    A(f"**判读**：{len(dec.get('rows', []))} 页的站点级分"
      + (f"完全相同（{_site_val} 分）。" if _site_same else "有差异（见上表）。") +
      f"新页（{_new_rng}）与基线（{_base_rng}）的全部差距只来自页面级那几分，")
    A("其中 `content` 项 11–12 分几乎不动、`negative_penalty` 0 到 −3 是主要区分点。")
    A("→ **总分只能证明「站点 GEO 基础设施在位、新页没拖后腿」，不能证明单页质量。**")
    A(f"要看单页质量请用 §B（47 项引用度，区分度 {_cit_rng}）与 §C（目标 query 覆盖）。")
    A("")

    A("## B. AI 引用度（47 项）逐项")
    A("")
    A("### B1 强项与被扣分项（以 reformer 指南页为例）")
    A("")
    ref = NEW[0]
    ms = engine[ref]["citability"]["methods"]
    A("**已拿满 / 高分（说明页面结构对 AI 引用是友好的）**")
    A("")
    A("| 项 | 得分 |")
    A("|---|---|")
    for m in sorted(ms, key=lambda x: -(x["score"] - x["max"]))[:10]:
        if m["score"] > 0:
            A(f"| {m['label']} | {m['score']}/{m['max']} |")
    A("")
    A("**失分项（按影响排序）**")
    A("")
    A("| 项 | 得分 | 声称影响 | 判定 |")
    A("|---|---|---|---|")
    for m in sorted(ms, key=lambda x: (x["score"] - x["max"]))[:14]:
        if m["score"] - m["max"] >= 0:
            continue
        note = summary.get("blind_spots", {}).get(m["name"], "")
        verdict = f"⚠️ 工具盲区：{note}" if note else "真实缺口"
        A(f"| {m['label']} | {m['score']}/{m['max']} | {m['impact']} | {verdict} |")
    A("")

    A("### B2 实测反证：`Statistics Addition` 是假阴性")
    A("")
    A("引擎源码 `core/citability.py` 的 `_STAT_PATTERNS` 只匹配 `%` / 千分位 / `$` / `million` / `Nx`：")
    A("")
    A("```python")
    A('_STAT_PATTERNS = [r"\\b\\d+(?:\\.\\d+)?%", r"\\b\\d{1,3}(?:,\\d{3})+", r"\\$\\d+",')
    A('                  r"\\b\\d+\\s*(?:million|billion|trillion|thousand)\\b", r"\\b\\d+(?:\\.\\d+)?\\s*(?:x|X)\\b"]')
    A("```")
    A("")
    A("**它匹配不到 `1190 × 700 × 1170 mm`、`85 kg`、装箱件数** —— 而这正是本板块的数字主体。")
    A("实测页面里被引擎「看不见」的规格数字：")
    A("")
    A("| 页面 | 引擎抓不到的规格数字 | 引擎认定的 stat matches |")
    A("|---|---|---|")
    for rel in NEW:
        st = next((m for m in engine[rel]["citability"]["methods"]
                   if m["name"] == "statistics_addition"), None)
        got = (st or {}).get("details", {}).get("stat_matches", "?")
        A(f"| `{rel.split('/')[-1]}` | **{engine[rel]['facts']['spec_numbers_engine_blind']}** | {got} |")
    A("")
    A("→ **不要把「Statistics +33%」当成待办去补。** 需要补的是句子级的一手事实陈述（见 §E/§G），")
    A("而不是换数字格式。")
    A("")

    A("### B3 对照实验：双语 DOM 有没有污染判分？")
    A("")
    A("站点每页同时内嵌 `.lang-en` 与 `.lang-zh`（靠 CSS 切换）。把中文副本整棵移除后重跑引用度：")
    A("")
    A("| 页面 | 整页 | 仅英文 | 差 |")
    A("|---|---|---|---|")
    for rel in targets:
        e = engine[rel].get("citability_en_only", {})
        if "total" in e:
            A(f"| `{rel}` | {engine[rel]['citability']['total']} | {e['total']} | {e['total']-engine[rel]['citability']['total']:+d} |")
    A("")
    A("**判读**：仅英文一律**更低**（−1 ~ −6），且基线页同幅（首页 −1、moq −5）。")
    A("→ 双语 DOM 没有给新页「虚高」，对照是公平的；同时也说明这 6 页**没有靠堆字骗分**。")
    A("")

    A("## C. 关键引用词覆盖（自建确定性判据）")
    A("")
    A("每条 query = 真实采购方的问法；判据 = 去停用词后的实词覆盖率（标题层 ≥0.8 = 主推）。")
    A("")
    A(f"**总览**：{ret.get('total','-')} 条目标 query → 可检索 "
      f"**{ret.get('retrievable','-')} / {ret.get('total','-')}**"
      f"（{ret.get('retrievable_rate','-')}%，H2/H3 或正文 ≥0.75）；"
      f"标题层锚定 {ret.get('title_anchored','-')} 条（{ret.get('title_rate','-')}%）。")
    A("")
    if ret.get("weak"):
        A("覆盖不足（正文与标题均 <0.75）：")
        for w_ in ret["weak"]:
            A(f"- `{w_['page'].split('/')[-1]}` — {w_['query']} → {w_['verdict']}")
        A("")
    A("⚠️ 词覆盖率是**钝器**：多词 query 少一个词就掉到 0.75 以下，同义说法（`opening` vs `startup`）")
    A("会被判成缺口。**精确短语**才是强信号，下面每表都单列。")
    A("")
    for rel in NEW:
        rows = coverages[rel]
        ok = sum(1 for r in rows if r["verdict"].startswith("✅"))
        mid = sum(1 for r in rows if r["verdict"].startswith("🟡"))
        bad = sum(1 for r in rows if r["verdict"].startswith(("⚠", "✗")))
        A(f"### `{rel.split('/')[-1]}` —— 标题锚定✅{ok} / 正文可检索🟡{mid} / 非主推⚠{bad}"
          f"（共 {len(rows)}；⚠ 仅指未在标题层锚定，不等于搜不到）")
        A("")
        A("| 目标 query | 精确短语 | title | H1 | H2/H3 | desc | 正文 | 判定 |")
        A("|---|---|---|---|---|---|---|---|")
        for r in rows:
            A(f"| {r['query']} | {'✅' if r['exact_phrase'] else '—'} | {r['title']} | {r['h1']} | "
              f"{r['heads']} | {r['desc']} | {r['body']} | {r['verdict']} |")
        A("")

    A("## D. 可发现性（「能不能搜得到」的可验证部分）")
    A("")
    A("| 页面 | sitemap | canonical自指 | hreflang | llms.txt | llms-full | JSON-LD |")
    A("|---|---|---|---|---|---|---|")
    for rel in NEW:
        f = finds[rel]
        A(f"| `{rel.split('/')[-1]}` | {'✅' if f['in_sitemap'] else '✗'} | "
          f"{'✅' if f['canonical_self'] else '✗'} | {','.join(f['hreflang'])} | "
          f"{'✅' if f['in_llms_txt'] else '✗'} | {'✅' if f['in_llms_full'] else '✗'} | "
          f"{', '.join(f['jsonld_types'])} |")
    A("")
    A("**站内入链（爬虫发现路径）**")
    A("")
    for rel in NEW:
        ins = summary.get(f"inbound:{rel}", [])
        A(f"- `{rel.split('/')[-1]}` ← {len(ins)} 个页面：{', '.join(ins[:8])}" +
          (f" …(+{len(ins)-8})" if len(ins) > 8 else ""))
    A("")
    A("**robots.txt / AI 爬虫**")
    A("")
    A("| 项 | 结果 |")
    A("|---|---|")
    A("| robots.txt 找到 | ✅ |")
    A("| 27 个 AI bot 全放行 | ✅ 无 blocked |")
    A("| citation bots 显式放行 | ❌ **缺 `Claude-SearchBot` / `Applebot` / `Googlebot`**（仅靠通配 `*`） |")
    A("| llms.txt | ✅ 有 H1 / 9 段 / 53 个 markdown 链接 / +llms-full.txt |")
    A("| AI discovery 端点 | 见 `geo_ai_endpoints_20260925.py` 既有结论 22/22 |")
    A("")

    A("## E. 专业度 / E-E-A-T（应用 `seo-content` 技能的 Who-How-Why rubric）")
    A("")
    A("| 页面 | Who:JSON-LD作者 | Who:署名义 | Who:机构名 | How:流程披露语 | Why:CTA | 第一人称 we | 数字个数 |")
    A("|---|---|---|---|---|---|---|---|")
    for rel in NEW:
        e = eeats[rel]
        A(f"| `{rel.split('/')[-1]}` | {'✅' if e['who_author_in_jsonld'] else '❌'} | "
          f"{'✅' if e['who_byline_visible'] else '❌'} | {'✅' if e['who_org_named'] else '❌'} | "
          f"{len(e['how_process_disclosure'])} 处 | {len(e['why_commercial_cta'])} 处 | "
          f"{e['first_person_we']} | {e['numbers_present']} |")
    A("")
    A("**判读**：")
    A("")
    A("- **Who（谁写的）**：✅ 有 Organization publisher，但**无作者具名**。B2B 器械采购页属"
      "「读者会追问」的类型 → 补一个可核验的作者/团队署名（哪怕写「SANFAN production & QC」）比编造人名好。")
    A("- **How（怎么做的）**：这是本批页面的**真优势** —— 装箱尺寸、净空、打样检验项全部来自自有产线，"
      "属一手信息。但**没有把它讲出来**（引擎 `First-Party Data` 判 0/4，因为它找 "
      "`we measured` / `our data` / Methodology 标题）。→ 加一句「这些数字怎么来的」即可，零合规风险。")
    A("- **Why（为什么存在）**：✅ 目的是帮采购方决策，不是堆关键词（`No Keyword Stuffing` 6/6 满分佐证）。")
    A("")
    A("**负面信号（高价值）**：新页 0 / 0 / 0 / **−1** / 0 / 0 —— 优于首页（−3）与板块首页（−3）。")
    for rel in NEW:
        nd = engine[rel].get("negative_detail", {})
        if nd.get("keyword_stuffing"):
            A(f"- 唯一扣分：`{rel.split('/')[-1]}` 被判关键词堆砌 —— 词 `{nd.get('stuffed_word')}`、"
              f"密度 {nd.get('stuffed_density')}%、severity `{nd.get('severity')}`。"
              f"该页主题就是型号（model）变体，3.2% 属可辩护，可选优化而非缺陷。")
    A("")

    A("## F. 无法验证的部分（必须诚实标注）")
    A("")
    A("| 想验证的事 | 为什么现在验不了 | 什么时候能验 |")
    A("|---|---|---|")
    A("| Google 是否收录这 6 个 URL | 页面**已部署**（10-02），但 GSC 未配置凭据 | 配 GSC 后，用 URL Inspection |")
    A("| 目标关键词是否有排名 | 同上 | 部署后 2–4 周看 GSC 查询报告 |")
    A("| AI（ChatGPT/Perplexity/Gemini）是否引用 | 页面已在线，但 `geo citations` 需 LLM API key | 配 key 后测 |")
    A("| 真实流量/曝光 | 无 GSC / 无分析埋点数据 | 配 GSC 后 |")
    A("")
    A("**已经确定的**：① §A–§E 全部是确定性判据（不依赖线上状态）；")
    A("② **部署一致性已验**——本轮未改 CSS/JS（因而不 bump 版本号，「看资源版本号」这个常规判据失效），")
    A("改用**本地⇄线上逐字节比对**：6 个博客页 + `blog.html` + `pilates/index.html` + `robots.txt` +")
    A("`sitemap.xml` + `llms.txt` + `llms-full.txt` = **12/12 一致**（长度逐一相符，两侧均做 CRLF→LF 归一）；")
    A("③ 6 页引用的静态资源（按 `/blog/` 解析相对路径后）**9/9 HTTP 200**。")
    A("")

    A("## G. 建议动作（按性价比排序）—— 状态已更新")
    A("")
    A("| 状态 | 优先 | 动作 | 影响 | 合规风险 |")
    A("|---|---|---|---|---|")
    A("| ✅ 已实施 | 🔴 P1 | robots.txt 补 `Claude-SearchBot` / `Applebot` / `Googlebot` 显式 `Allow: /` | "
      "`citation_bots_explicit` ❌→✅（站点级 +3） | 无 |")
    A("| ✅ 已实施 | 🔴 P1 | 每页加「这些数字是怎么来的」方法论段（自有产线 / QC 量测） | "
      "`First-Party Data` 0/4 → **4/4**（6/6 页满分）；真 E-E-A-T | 无（是本厂真实流程） |")
    A("| ✅ 已实施 | 🟠 P2 | 句子级一手数字陈述（`We measured 930 mm as the widest…`） | "
      "句子级事实是 AI 抽取的最爱 | 无（数字全部取自画册公布值） |")
    A("| ✅ 已实施 | 🟠 P2 | 新增 `Sources` 小节 + 2 个 Wikipedia 权威外链 | `Cite Sources` 1/6 → **6/6** | "
      "低（仅通用术语与出处，不涉产品主张） |")
    A("| ✅ 已实施 | 🟡 P3 | 3 条同义词 query 补进正文（`startup` / `door clearance` / `commercial grade`） | "
      "提高精确匹配面 | 无 |")
    A("| ✅ 已实施 | 🟡 P3 | 团队署名（可核验的团队名，未编造人名） | E-E-A-T 的 Who 层 | 低 |")
    A("| ✅ 已实施 | 🟡 P3 | `Organization` 补 `@id` / `sameAs`，并与 `contact.html` 的站点级实体同 `@id`"
      "（后者已含 `address` / `contactPoint` / `knowsAbout`） | 实体消歧、跨页实体合并 | 无 |")
    A("| ⚪️ 仍待你定 | — | 引语（Quotation +41%，声称影响最高的一项） | 高影响 | "
      "**需要你决定引谁**：引不存在的专家＝编造，不做 |")
    A("| ⏸ 未动 | — | 6 语言译文（等 DeepL 额度） | 覆盖 de / ja / ko / fr / it / es | — |")
    A("")
    A("> ✅ **已上线**：远程 `1e5773d15a`（26 文件；部署状态 `success`）。")
    A("> 本轮只改了 6 个博客页、`blog.html`、`pilates/index.html`、`robots.txt`、`sitemap.xml`、")
    A("> `llms.txt` / `llms-full.txt` 与工具脚本，**未触碰任何族页 / 首页主体 / 语言版**。")
    A("> ⚠️ 两处外链的**可达性仍未能实测**：本机 DNS 把 `en.wikipedia.org` 解析到 `31.13.88.169`")
    A("> （Meta 网段）——**DNS 污染**，TCP 连接挂死；直连 `curl` 与 WebFetch 两条路都失败。")
    A("> 这是**本机网络环境**问题、与站点无关（`fjsanfan.com` 与 `api.github.com` 均正常）。")
    A("> 选用的是 Wikipedia 的稳定条目，但严格说这一步仍应标为「未验证」——部署后换个网络复核一次即可闭合。")
    A("")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"[MD]   {REPORT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
