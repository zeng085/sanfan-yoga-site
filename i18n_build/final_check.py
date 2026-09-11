#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""final_check.py —— 推送前最终体检

1. 无 -1w.webp（加工图）残留引用
2. 换图计划里 16 条全部回到 cur
3. ?v= 版本号统一、无 ?vv 双写
4. 引用的图片文件真实存在（无死图）
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAN = os.path.join(ROOT, "outputs", "plan", "换图计划.json")
CARDS = os.path.join(ROOT, "outputs", "product_cards.json")
IMG_RE = re.compile(r'<img[^>]+src="([^"]+)"')


def all_html():
    out = []
    for f in sorted(os.listdir(ROOT)):
        if f.endswith(".html"):
            out.append(f)
    for d in ("products", "blog", "de", "ja", "ko", "fr", "it", "es"):
        p = os.path.join(ROOT, d)
        if os.path.isdir(p):
            out += [f"{d}/{f}" for f in sorted(os.listdir(p)) if f.endswith(".html")]
    return out


def main():
    files = all_html()
    htmls = {r: open(os.path.join(ROOT, r), encoding="utf-8").read() for r in files}
    print(f"扫描 {len(files)} 个 HTML\n")

    # 1. 加工图残留
    bad1 = {r: len(re.findall(r"-1w\.webp", h)) for r, h in htmls.items() if "-1w.webp" in h}
    print(f"[1] -1w.webp 加工图残留引用：{sum(bad1.values())} 处 " +
          ("✅" if not bad1 else f"❌ {list(bad1)[:5]}"))

    # 2. 计划 16 条是否回到 cur
    plan = json.load(open(PLAN, encoding="utf-8"))
    bad2 = []
    for it in plan:
        # new 图在 HTML 里仍可能出现是合法的（图集里有它），只查「卡片首图」
        pass
    pool = json.load(open(CARDS, encoding="utf-8"))
    for it in plan:
        slug, cur, new = it["slug"], it["cur"], it["new"]
        if slug not in pool:
            bad2.append(f"{slug}(不在卡片池)")
            continue
        first = IMG_RE.search(pool[slug])
        if not first:
            bad2.append(f"{slug}(无img)")
            continue
        src = first.group(1)
        if new in src:
            bad2.append(f"{slug} 仍指向 {new}")
        elif cur not in src:
            bad2.append(f"{slug} 指向异常 {src}")
    print(f"[2] 卡片池 16 条是否已回到原始 cur 图：" +
          ("✅ 全部回滚" if not bad2 else f"❌ {bad2}"))

    # 3. 版本号
    vers = {}
    for r, h in htmls.items():
        for v in re.findall(r'\?v([0-9a-zA-Z]+)', h):
            vers[v] = vers.get(v, 0) + 1
    top = sorted(vers.items(), key=lambda x: -x[1])[:5]
    bad3 = [v for v in vers if v.startswith("v")]
    print(f"[3] ?v= 版本分布 top5：{top}" + ("  ✅ 单一" if len(vers) <= 1 else "  ⚠️ 多版本并存"))
    print(f"    ?vv 双写：{'❌ ' + str(bad3) if bad3 else '✅ 无'}")

    # 4. 死图检查（相对路径归一化后校验存在性）
    missing = {}
    checked = 0
    for r, h in htmls.items():
        base = os.path.dirname(os.path.join(ROOT, r))
        for src in IMG_RE.findall(h):
            if src.startswith(("http", "//", "data:")):
                continue
            checked += 1
            p = os.path.normpath(os.path.join(base, src.split("?")[0]))
            if not os.path.exists(p):
                missing.setdefault(src, []).append(r)
    print(f"[4] 图片引用 {checked} 条，缺失 {len(missing)} 个不同文件 " +
          ("✅" if not missing else "❌"))
    for src, rs in list(missing.items())[:10]:
        print(f"      {src}  ← {rs[0]} ({len(rs)}处)")

    print("\n" + ("✅ 全部通过，可以推送" if not bad1 and not bad2 and not missing and not bad3
                  else "⚠️ 存在未通过项，见上"))


if __name__ == "__main__":
    main()
