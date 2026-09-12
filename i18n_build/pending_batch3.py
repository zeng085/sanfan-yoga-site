#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""算「第三批还没上」的产品差集。

⚠️ 关键：本站页 slug 是重命名过的（alignment-line-tpe-yoga-mat ← 英文站
   tpe-yoga-mat-special-dual-color-body-line），**slug 比对和标题比对都会错**。
   唯一权威来源是 outputs/batch{1,2}_pages.json 里的 `src`（英文站 slug）→ `new`（本站页 slug）。

口径：
  清洗后保留 = outputs/英文站产品清洗清单-2026-09-11.md 的「保留清单」147 个
  已覆盖     = batch1.src ∪ batch2.src（含被家族页合并的那些）
  未上线     = 保留清单 - 已覆盖

用法: python3 i18n_build/pending_batch3.py
"""
import collections
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
CLEAN_MD = ROOT / "outputs" / "英文站产品清洗清单-2026-09-11.md"
CATALOG = ROOT / "outputs" / "sf_catalog_full.json"
# 每上一批就把它加进来 —— 否则重跑会把已上线的又算成未上线（第三批就踩过）
BATCHES = ["outputs/batch1_pages.json", "outputs/batch2_pages.json",
           "outputs/batch3_pages.json"]

# 第二批报告：4 个老页是「就地更新」而非新建，它们各自吞掉了多个英文站 slug。
# 这批 slug 不在 batch{1,2}_pages.json 里，但内容已被家族页覆盖，不算未上线。
# 依据：outputs/sanfansport对标-产品信息版块改动方案-2026-09-11.md  §5.1（ym1 = tpe-yoga-mat 等 11 个 SKU）
#        + 逐个核对 Material/Size/Thickness/Weight 与本站页吻合。
FAMILY = {
    "tpe-yoga-mat":            "ym1",
    "folding-mat":             "ym4",
    "pu-rubber-yoga-mat":      "ym5",
    "matte-pu-rubber-yoga-mat": "ym6",
    # 第三批补登：这 5 个的**全部图集**已 100% 命中站内已有文件（md5 逐字节，见 probe_md5.py），
    # 即已被这 5 个家族页收录 —— 判定依据不同（图集而非规格），结论一样：不重复建页。
    "dumbbell-2":              "fi5",
    "jump-rope-2":             "fi3",
    "kettlebell-2":            "fi2",
    "stair-climbers-3":        "fi4",
    "yoga-hammock":            "pr1",
}


def clean_slugs():
    """从清洗清单「保留清单」区间按品类抽 slug（避开后面的「待处理命名问题」段）。"""
    lines = CLEAN_MD.read_text(encoding="utf-8").splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("## 保留清单"))
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## "):
            end = i
            break
    secs = collections.OrderedDict()
    cur = None
    for line in lines[start + 1:end]:
        m = re.match(r"^###\s+(.+)", line)
        if m:
            cur = re.sub(r"（\d+）", "", m.group(1)).strip()
            secs[cur] = []
            continue
        if cur is None:
            continue
        for s in re.findall(r"`([a-z0-9\-]+)`", line):
            if s not in secs[cur]:
                secs[cur].append(s)
    return secs


def main():
    secs = clean_slugs()
    total = sum(len(v) for v in secs.values())
    cat = {c["slug"]: c for c in json.load(open(CATALOG, encoding="utf-8"))}
    local = {p.stem for p in (ROOT / "products").glob("*.html")}

    mapping = {}                                  # src(sf slug) -> [new 本站页]
    for b in BATCHES:
        for it in json.load(open(ROOT / b, encoding="utf-8")):
            mapping.setdefault(it["src"], []).append(it["new"])

    for k, v in FAMILY.items():                   # 家族页覆盖的也算已上
        mapping.setdefault(k, []).append(v)

    covered = {s: mapping[s] for s in mapping if s in {x for v in secs.values() for x in v}}
    missing = [(n, s) for n, v in secs.items() for s in v if s not in mapping]

    print(f"清洗后英文站产品      {total}")
    print(f"batch1+2 新建        {len(mapping) - len(FAMILY)} 个来源")
    print(f"老页家族合并         {len(FAMILY)} 个来源 → {sorted(set(FAMILY.values()))}")
    print(f"本站 products/ 页面  {len(local)}")
    print(f"→ 第三批未上线       {len(missing)}")
    print()

    print("— 未上线按品类 —")
    for n, v in collections.Counter(x[0] for x in missing).most_common():
        print(f"  {n:12s} {v:3d} / {len(secs[n]):3d}")

    print()
    print("— 未上线明细 —")
    for n, s in missing:
        c = cat.get(s, {})
        sp, im = c.get("specs") or {}, c.get("images") or []
        if isinstance(sp, str):
            sp = {}
        if isinstance(im, str):
            im = []
        flag = "空壳" if not sp else f"spec{len(sp)}"
        print(f"  [{n:11s}] {s:44s} {flag:6s} img={len(im):2d}  {c.get('title_en','')[:42]}")

    ns = sum(1 for _, s in missing if not (cat.get(s, {}).get("specs") or {}))
    print()
    print(f"其中空壳页 {ns} 个（content 空 → 只上兜底 3 行，禁止编造数值）")

    # 每条带上 spec/img/shell，让清单文件自包含 ——
    # 否则下游只能看到 slug，得回 sf_catalog_full.json 重查规格，容易误判成空壳。
    def row(a, b):
        c = cat.get(b, {})
        sp, im = c.get("specs") or {}, c.get("images") or []
        if isinstance(sp, str):
            sp = {}
        if isinstance(im, str):
            im = []
        return {"cat": a, "slug": b, "title": c.get("title_en", ""),
                "spec": len(sp), "img": len(im), "shell": not sp}

    out = ROOT / "outputs" / "第三批待上线.json"
    json.dump({"missing": [row(a, b) for a, b in missing],
               "covered": [{"slug": a, "pages": b} for a, b in covered.items()],
               "total_clean": total},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"已写出 {out}")


if __name__ == "__main__":
    main()
