#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""全站资源版本号 bump。改过 CSS/JS 后必跑。

⚠️ 站点写法是 `styles.css?v20260909c` —— **没有等号**。
   用 `re.search(r"\?v=(...)", ...)` 会匹配不到，静默回落成 `?vv...`（资源 404）。
   正确写法：`re.search(r"styles\.css\?v([A-Za-z0-9]+)", ...)`，且默认值不要带 v。

用法：
    python3 i18n_build/bump_assets_ver.py --to 20260911a --dry-run
    python3 i18n_build/bump_assets_ver.py --to 20260911a
"""
import argparse
import collections
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAT = re.compile(r'\?v([A-Za-z0-9]+)')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", required=True, help="新版本号，如 20260911a")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    new = args.to.lstrip("v")
    before = collections.Counter()
    changed = 0
    files = [p for p in ROOT.rglob("*.html")
             if "outputs" not in p.parts and ".git" not in p.parts]

    for p in files:
        t0 = p.read_text(encoding="utf-8", errors="ignore")
        for m in PAT.findall(t0):
            before[m] += 1
        t = PAT.sub(f"?v{new}", t0)
        if t != t0:
            changed += 1
            if not args.dry_run:
                p.write_text(t, encoding="utf-8")

    print("bump 前版本号分布:", before.most_common())
    print(f"命中文件: {changed}/{len(files)}")
    print(f"→ 统一为 ?v{new}；{'dry-run 未写盘' if args.dry_run else '已写盘'}")

    # 复查：不应再出现旧号，也不应出现 ?vv
    if not args.dry_run:
        bad = []
        for p in files:
            t = p.read_text(encoding="utf-8", errors="ignore")
            if "?vv" in t:
                bad.append((str(p.relative_to(ROOT)), "?vv 双写"))
            for m in PAT.findall(t):
                if m != new:
                    bad.append((str(p.relative_to(ROOT)), f"残留 ?v{m}"))
        print("复查:", bad if bad else "全站版本号一致 ✓")


if __name__ == "__main__":
    main()
