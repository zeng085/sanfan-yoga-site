#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补生成单个产品页（复用 build_batch1.py 的模板与文案函数）。

用途（2026-09-11 全面体检）：第一批清单里的
`two-tone-double-layer-tpe-yoga-mat`（英文站 tpe-double-yoga-mat）计划了但从未落地。

与 build_batch1.py 的差别：
  - 不截断图集（MAX_IMAGES 失效），用 assets/img/<slug>-<k>.webp 全部
  - 不复制图片（图已由 dl_batch_images.py 落盘）
  - 只生成指定的一页，不动其它页

用法：
    python3 i18n_build/build_one_page.py two-tone-double-layer-tpe-yoga-mat --dry-run
    python3 i18n_build/build_one_page.py two-tone-double-layer-tpe-yoga-mat
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "i18n_build"))
import build_batch1 as B                                        # noqa: E402

os.chdir(ROOT)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    if not args:
        print("用法: build_one_page.py <本地slug> [--dry-run]"); return
    target = args[0]

    recs = json.load(open("outputs/batch1_pages.json", encoding="utf-8"))
    it = next((x for x in recs if x["new"] == target), None)
    if not it:
        print(f"! batch1_pages.json 里没有 {target}"); return

    # 图：本地已下载的连续编号
    files, k = [], 1
    while True:
        n = f"{target}-{k}.webp"
        if not os.path.exists(os.path.join("assets/img", n)):
            break
        files.append(n); k += 1
    if not files:
        print(f"! assets/img 里没有 {target}-N.webp，先跑 dl_batch_images.py"); return

    fam = it["fam"]
    cp = B.copy_for(fam)
    specs, base = it["specs"], it.get("base")
    size = B.human_size(specs.get("Size"))
    thk = B.clean_thk(specs)
    fill = {"size": size, "thk": thk, "base": B.BASE_LABEL.get(fam, "rubber"),
            "mat": specs.get("Material", "")}

    desc_en, desc_zh = cp["desc_en"].format(**fill), cp["desc_zh"].format(**fill)
    ov_en, ov_zh = cp["ov_en"].format(**fill), cp["ov_zh"].format(**fill)
    ap_en, ap_zh = cp["ap_en"].format(**fill), cp["ap_zh"].format(**fill)
    f_en = "".join("<li>" + B.esc(B.esc(b)) + "</li>" for b in cp["f_en"])
    f_zh = "".join("<li>" + B.esc(b) + "</li>" for b in cp["f_zh"])

    url = "%s/products/%s.html" % (B.DOMAIN, target)
    ver = "20260911c"
    m = re.search(r"styles\.css\?v([A-Za-z0-9]+)",
                  open(os.path.join("products", "ym1.html"), encoding="utf-8").read())
    if m:
        ver = m.group(1)

    thumbs = []
    for n, nm in enumerate(files):
        cls = "pd-thumb active" if n == 0 else "pd-thumb"
        thumbs.append('<button type="button" class="%s"><img src="../assets/img/%s" width="800" '
                      'height="800" loading="lazy" alt="%s"></button>'
                      % (cls, nm, B.esc(it["title_en"])))

    # 相关产品：同族优先
    cat = {p["slug"]: p for p in json.load(open("outputs/sf_catalog_full.json", encoding="utf-8"))}
    same = []
    for x in recs:
        if x["new"] == target or x["fam"] != fam:
            continue
        if not os.path.exists(os.path.join("products", x["new"] + ".html")):
            continue
        same.append(x)
    same = same[:4]
    rel = []
    for r in same:
        rel.append(
            '<a class="prod-card" href="../products/%s.html"><div class="ph">'
            '<img src="../assets/img/%s-1.webp" width="800" height="800" loading="lazy" alt="%s"></div>'
            '<div class="info"><h4><span class="lang-en">%s</span><span class="lang-zh">%s</span></h4>'
            '<p><span class="lang-en">%s</span><span class="lang-zh">%s</span></p></div></a>'
            % (r["new"], r["new"], B.esc(r["title_en"]), B.esc(r["title_en"]), B.esc(r["title_zh"]),
               B.esc((r["specs"].get("Material") or "") + " · " + (r["specs"].get("Size") or "")),
               B.esc((r["specs"].get("Material") or "") + " · " + (r["specs"].get("Size") or ""))))

    wa_en = ("Hi%20SANFAN%2C%20I%20am%20interested%20in%20" +
             it["title_en"].replace(" ", "%20").replace("&", "%26").replace("/", "%2F"))
    wa_zh = ("%E4%BD%A0%E5%A5%BD%E4%B8%89%E6%A2%B5%EF%BC%8C%E6%88%91%E6%83%B3%E4%BA%86%E8%A7%A3%20" +
             it["title_zh"].replace(" ", "%20"))

    html = B.HEAD
    for k2, v in [
        ("@@VER@@", ver),
        ("@@TITLEZH@@", B.esc(it["title_zh"])),
        ("@@TITLE@@", B.esc(it["title_en"])),
        ("@@DESC@@", B.esc(desc_en[:300])),
        ("@@URL@@", url),
        ("@@OGIMG@@", B.DOMAIN + "/assets/img/" + files[0]),
        ("@@JSONLD@@", B.build_head_jsonld(it, it["title_en"], desc_en, url,
                                           [B.DOMAIN + "/assets/img/" + n for n in files], base)),
        ("@@IMG1@@", files[0]),
        ("@@THUMBS@@", "\n          ".join(thumbs)),
        ("@@DESCEN@@", B.esc(desc_en)),
        ("@@DESCZH@@", B.esc(desc_zh)),
        ("@@WA@@", wa_en),
        ("@@WAEN@@", wa_en),
        ("@@WAZH@@", wa_zh),
        ("@@SPECROWS@@", B.spec_rows(specs, fam)),
        ("@@OVEN@@", B.esc(ov_en)),
        ("@@OVZH@@", B.esc(ov_zh)),
        ("@@FEN@@", f_en),
        ("@@FZH@@", f_zh),
        ("@@APEN@@", B.esc(ap_en)),
        ("@@APZH@@", B.esc(ap_zh)),
        ("@@RELATED@@", "".join(rel)),
    ]:
        html = html.replace(k2, v)

    left = re.findall(r"@@[A-Z0-9]+@@", html)
    out = os.path.join("products", target + ".html")
    print(f"目标页 : {out}")
    print(f"图片   : {len(files)} 张（{files[0]} … {files[-1]}）")
    print(f"占位符 : {'全部替换完成' if not left else '未替换 ' + str(set(left))}")
    print(f"报价   : base={base}（{B.BASE_LABEL.get(fam)}）")
    if dry:
        print("[DRY-RUN] 未写入"); return
    open(out, "w", encoding="utf-8").write(html)
    print(f"已写出 {out}（{len(html)//1024} KB）")


if __name__ == "__main__":
    main()
