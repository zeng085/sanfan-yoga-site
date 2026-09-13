# -*- coding: utf-8 -*-
"""为 6 个语言站生成各自的搜索索引 assets/data/navdata.<lang>.js。

为什么不做成「一份英文索引 + 前端翻译」：
语言页是**静态**的，页面里没有 lang-en/lang-zh 双 span，main.js 的 I18N 字典也不介入
（见 build_pages 的语言守卫）。所以索引里的**名字必须是译好的**，否则德国客户搜
"Yogamatte" 只会搜到空结果 —— 索引里存的还是 "TPE Yoga Mat"。

数据来源（全部零翻译成本）：
  产品名 / 分类名 / 场景名 / 页面名  —— 直接读已生成的语言页 <h1>
  关键词 k                          —— 读语言页 <meta name="description">
只有 UI 文案（占位符、类型标签、热门词）才走 DeepL，约 15 条 × 6 语言。

输出全局变量 window.SANFAN_NAV_<LANG>（大写），避免与英文站的 SANFAN_NAV 混淆。

用法
    python3 i18n_build/build_navdata_i18n.py --dry-run   # 只打印，不写盘
    python3 i18n_build/build_navdata_i18n.py
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import translator as T  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
SUFFIX_RE = re.compile(r"\s+[—–-]\s+SANFAN.*$")

HOT_EN = ["TPE yoga mat", "hot yoga", "foam roller", "jump rope",
          "fascia gun", "studio", "materials", "private label"]

# UI 文案：{n} 产品总数、{q} 用户输入，DeepL 会原样保留占位符
UI_SRC = {
    "ph": "Search {n} products, categories, applications…",
    "aria": "Search",
    "menu": "Search products",
    "popular": "Popular searches",
    "empty": 'No match for "{q}". Tell us the spec and we will build it — '
             'or ask us directly on WhatsApp.',
    "t_product": "Product",
    "t_category": "Category",
    "t_application": "Solution",
    "t_page": "Page",
    "shop_cat": "Shop by category",
    "view_all": "View all {n} products",
    "compare": "Compare materials",
    "shop_app": "Shop by application",
    "not_sure": "Not sure which spec?",
    "send_price": "Send your target price — we quote in 24h",
}


def load_en():
    s = open(os.path.join(ROOT, "assets", "data", "navdata.js"), encoding="utf-8").read()
    i = s.find("{")
    return json.loads(s[i:s.rfind("}") + 1])


def h1_of(path):
    """读语言页的 <h1> 纯文本，去掉尾部 ' — SANFAN' 品牌后缀。"""
    p = os.path.join(ROOT, path)
    if not os.path.exists(p):
        return ""
    h = open(p, encoding="utf-8", errors="replace").read()
    m = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", h)
    if not m:
        return ""
    txt = " ".join(re.sub(r"<[^>]+>", " ", m.group(1)).split())
    return SUFFIX_RE.sub("", txt).strip()


def desc_of(path):
    p = os.path.join(ROOT, path)
    if not os.path.exists(p):
        return ""
    h = open(p, encoding="utf-8", errors="replace").read()
    m = re.search(r'<meta name="description" content="([^"]*)"', h)
    return m.group(1).strip() if m else ""


def build_lang(lang, en):
    L = lang.upper()
    miss = []

    # ---------- 分类 / 场景 / 页面 的译名（全部来自页面本身）
    cat_name = {}
    for c in en["cats"]:
        nm = h1_of("%s/%s.html" % (lang, c["k"])) or c["en"]
        if not h1_of("%s/%s.html" % (lang, c["k"])):
            miss.append("cat:" + c["k"])
        cat_name[c["k"]] = nm

    app_name, app_tag = {}, {}
    for a in en["apps"]:
        nm = h1_of("%s/applications/%s.html" % (lang, a["k"])) or a["en"]
        if not h1_of("%s/applications/%s.html" % (lang, a["k"])):
            miss.append("app:" + a["k"])
        app_name[a["k"]] = nm
        app_tag[a["k"]] = desc_of("%s/applications/%s.html" % (lang, a["k"]))[:90] or a["d"]

    # ---------- UI 文案 + 热门词（走 DeepL）
    keys = list(UI_SRC.keys())
    vals = T.translate_lines([UI_SRC[k] for k in keys], L, verbose=False)
    ui = dict(zip(keys, vals))
    ui["hot"] = T.translate_lines(HOT_EN, L, verbose=False)
    T.flush()

    # ---------- 索引
    idx = []
    for e in en["idx"]:
        u = e["u"]
        if e["y"] == "product":
            rel = "%s/%s" % (lang, u)
            t = h1_of(rel)
            if not t:
                t, miss = e["t"], miss + ["prod:" + u]
            ck = None
            for c in en["cats"]:
                if c["en"] == e["c"]:
                    ck = c["k"]
                    break
            idx.append({
                "y": "product", "t": t, "z": t, "u": u,
                "c": cat_name.get(ck, e["c"]), "cz": cat_name.get(ck, e["c"]),
                "img": e["img"],
                "k": (desc_of(rel) + " " + cat_name.get(ck, "")).lower(),
            })
        elif e["y"] == "category":
            k = u[:-5]
            t = cat_name.get(k, e["t"])
            idx.append({"y": "category", "t": t, "z": t, "u": u,
                        "c": e["c"], "cz": e["c"], "img": "",
                        "k": (desc_of("%s/%s.html" % (lang, k)) + " " + t).lower()})
        elif e["y"] == "application":
            k = u.replace("applications/", "").replace(".html", "")
            t = app_name.get(k, e["t"])
            idx.append({"y": "application", "t": t, "z": t, "u": u,
                        "c": app_tag.get(k, e["c"]), "cz": app_tag.get(k, e["c"]),
                        "img": "", "k": (app_tag.get(k, "") + " " + t).lower()})
        else:
            t = h1_of("%s/%s" % (lang, u)) or e["t"]
            idx.append({"y": "page", "t": t, "z": t, "u": u,
                        "c": e["c"], "cz": e["c"], "img": "",
                        "k": (desc_of("%s/%s" % (lang, u)) + " " + t).lower()})

    cats = [{"k": c["k"], "en": cat_name[c["k"]], "zh": cat_name[c["k"]],
             "n": c["n"], "kw": desc_of("%s/%s.html" % (lang, c["k"]))[:160]}
            for c in en["cats"]]

    gl = T.translate_lines([g["en"] for g in en["groups"]], L, verbose=False)
    T.flush()
    groups = [{"en": gl[i], "zh": gl[i], "items": g["items"]}
              for i, g in enumerate(en["groups"])]

    apps = [{"k": a["k"], "en": app_name[a["k"]], "zh": app_name[a["k"]],
             "d": app_tag[a["k"]], "dz": app_tag[a["k"]]} for a in en["apps"]]

    data = {"ver": 1, "total": en["total"], "cats": cats, "groups": groups,
            "apps": apps, "syn": {}, "idx": idx, "ui": ui}
    return data, miss


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--langs", default=",".join(LANGS))
    args = ap.parse_args()

    en = load_en()
    print("英文索引 %d 条（%d 产品）" % (len(en["idx"]), en["total"]))
    for lang in args.langs.split(","):
        lang = lang.strip()
        if not lang:
            continue
        data, miss = build_lang(lang, en)
        js = ("/* 自动生成，请勿手改 —— i18n_build/build_navdata_i18n.py */\n"
              "window.SANFAN_NAV_%s=%s;\n"
              % (lang.upper(), json.dumps(data, ensure_ascii=False, separators=(",", ":"))))
        out = os.path.join(ROOT, "assets", "data", "navdata.%s.js" % lang)
        if not args.dry_run:
            open(out, "w", encoding="utf-8").write(js)
        nprod = len([e for e in data["idx"] if e["y"] == "product"])
        print("%s navdata.%s.js  %d 条索引（产品 %d）  %.1f KB  %s"
              % ("[dry]" if args.dry_run else "生成", lang, len(data["idx"]), nprod,
                 len(js.encode("utf-8")) / 1024.0,
                 ("⚠ 缺 %d: %s" % (len(miss), miss[:3])) if miss else "✅"))
        if args.dry_run:
            p = [e for e in data["idx"] if e["y"] == "product"][:2]
            for e in p:
                print("    样例:", e["t"], "|", e["c"], "|", e["u"])
            print("    UI   :", data["ui"]["ph"][:60], "|", data["ui"]["hot"][:3])
    T.flush()


if __name__ == "__main__":
    main()
