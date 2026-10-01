#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""修正族页型号卡片「Catalogue pNN · model i of j」的页内序号 + 表格/卡片顺序。

问题（第二轮换角度验证发现）
--------------------------
生成器原按 `(page, 型号名字典序)` 排序，卡片编号取的是**该顺序里的位次**，
而不是画册自身的页内序号。后果：买家按「Catalogue p31 · model 1」去翻画册，
翻到的是另一台。

实测（修正前）：80 张卡片里 **29 张印错（36%）**。已用画册原页 p32.webp 核实——
画册上 metal 19 Cadillac-F 在上（应为 model 1）、classics Maple Cadillac 在下
（应为 model 2），而页面把两者编号写反了。源 JSON 的 `seq_in_page` 是可信的：
它与按 y 坐标算出的视觉顺序在 69 台里只差 1 处（p37 两台 y 相差 0.0004，实为并列）。

修正内容
--------
① 正文三区块（#catalog / #catalogue-pages / #models-compared）：用重新生成的片段替换
   —— 排序改为 `(page, seq_in_page)`，卡片编号取 `seq_in_page`，
   分母取**该画册页全量实印台数**（tower 族在 p25 只露 2 台，画册该页实印 3 台，
   用族内行号会产出「model 2 of 2 / model 3 of 2」这种自相矛盾的副标题）。
② JSON-LD ItemList：条目顺序同步为画册顺序，使 `position` 与文档顺序一致。

不动 SEO 层（meta / material / offerCount / FAQ / eyebrow）—— 那些与本问题无关，
且旧锚点串已归零，重跑会全部 miss。

安全：默认 dry-run；`--write` 才落盘；落盘前备份；落盘后复读校验 + 断言。

用法：
    python3 i18n_build/fix_model_seq_20261001.py            # dry-run
    python3 i18n_build/fix_model_seq_20261001.py --write
"""
import argparse
import datetime
import json
import pathlib
import re
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import apply_family_pages_20261001 as AF  # noqa: E402
import gen_family_catalog_block_20261001 as GEN  # noqa: E402

ROOT = HERE.parent
DATA = ROOT / "i18n_build" / "data" / "catalog_pilates_models_v2.json"
FRAG_DIR = ROOT / "outputs" / "pilates_family_catalog_20261001"
BACKUP_DIR = pathlib.Path.home() / ".workbuddy" / "backups" / "fjsanfan"

ITEMLIST_RE = re.compile(
    r'      "@type": "ItemList",\n      "name": "[^"]+",\n'
    r'      "numberOfItems": \d+,\n      "itemListElement": \[\n.*?\n      \]\n    \}',
    re.S)

CARD_SUB = re.compile(r'Catalogue p(\d+)\s*·\s*model (\d+) of (\d+)')


def norm(s):
    return re.sub(r"\s+", "", str(s)).lower()


def rows_for(cfg):
    rows = json.loads(DATA.read_text("utf-8"))
    rows = [r for r in rows if r["series"].startswith(tuple(cfg["series"]))]
    if cfg.get("filter"):
        f = re.compile(cfg["filter"], re.I)
        rows = [r for r in rows if f.search(str(r["model"]))]
    # 画册顺序：先画册页，再页内序号
    return sorted(rows, key=lambda r: (r["page"], r["seq_in_page"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--family", default=None)
    a = ap.parse_args()

    fams = [a.family] if a.family else list(AF.CFG)
    src = json.loads(DATA.read_text("utf-8"))
    page_total_full = {}
    for r in src:
        page_total_full[r["page"]] = page_total_full.get(r["page"], 0) + 1
    by_model = {norm(r["model"]): r for r in src}

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    all_bad = []

    for fam in fams:
        cfg = AF.CFG[fam]
        page = ROOT / cfg["page"]
        t0 = page.read_text("utf-8")
        rows = rows_for(cfg)

        # ---- ① 重新生成片段
        rc = GEN.build(fam, FRAG_DIR)
        if rc != 0:
            all_bad.append(f"{fam}: 生成器断言闸未通过，跳过")
            print(f"  ✗ {fam}: 生成器未通过")
            continue
        frag = (FRAG_DIR / f"block_{fam}.html").read_text("utf-8")

        # ---- 定位与替换
        m = AF.NEW_BLOCK_RE.search(t0)
        if not m:
            all_bad.append(f"{fam}: 正文区块 pattern 未命中")
            print(f"  ✗ {fam}: 正文区块未命中")
            continue
        t1 = t0[:m.start()] + frag + t0[m.end():]

        ilm = ITEMLIST_RE.search(t1)
        if not ilm:
            all_bad.append(f"{fam}: ItemList pattern 未命中")
            print(f"  ✗ {fam}: ItemList 未命中")
            continue
        t1 = t1[:ilm.start()] + AF.build_itemlist(rows, cfg["display_en"]) + t1[ilm.end():]

        # ---- 落盘前自检
        cards = re.findall(
            r'<article class="model-card" id="[^"]+">\s*<h3>(.*?)</h3>\s*'
            r'<p class="model-card-sub">(.*?)</p>', frag, re.S)
        exp_cards = len(rows)
        bad = []
        if len(cards) != exp_cards:
            bad.append(f"卡片数 {len(cards)} ≠ {exp_cards}")
        for name_html, sub in cards:
            name = re.sub(r"<[^>]+>", "", name_html).strip()
            sm = CARD_SUB.search(sub)
            if not sm:
                bad.append(f"{name}: 无副标题")
                continue
            pg, i = int(sm.group(1)), int(sm.group(2))
            r = by_model.get(norm(name))
            if not r:
                bad.append(f"{name}: 不在源数据")
                continue
            if pg != r["catalog_page"]:
                bad.append(f"{name}: 页码 {pg} ≠ {r['catalog_page']}")
            if i != r["seq_in_page"]:
                bad.append(f"{name}: 序号 {i} ≠ {r['seq_in_page']}")
        if bad:
            all_bad += [f"{fam}: {b}" for b in bad]
            print(f"  ✗ {fam}: 落盘前自检失败 {bad[:4]}")
            continue

        n_before = len(CARD_SUB.findall(t0))
        n_after = len(CARD_SUB.findall(t1))
        d = len(t1.encode("utf-8")) - len(t0.encode("utf-8"))
        print(f"  {fam:10s} 卡片 {n_before} → {n_after}  字节 {d:+d}"
              f"  ItemList {len(rows)} 项   {'（dry-run 未写盘）' if not a.write else '已写盘'}")

        if a.write:
            bak = BACKUP_DIR / f"{page.name}.{stamp}.seqfix.bak"
            shutil.copy2(page, bak)
            page.write_text(t1, "utf-8")
            # 复读校验
            rt = page.read_text("utf-8")
            if rt != t1:
                all_bad.append(f"{fam}: 落盘后复读不一致")
            if not AF.NEW_BLOCK_RE.search(rt):
                all_bad.append(f"{fam}: 落盘后正文区块 pattern 失效")
            n_rt = len(CARD_SUB.findall(rt))
            if n_rt != exp_cards:
                all_bad.append(f"{fam}: 落盘后卡片数 {n_rt} ≠ {exp_cards}")

    print()
    if all_bad:
        print(f"✗ 发现 {len(all_bad)} 个问题：")
        for b in all_bad:
            print("  -", b)
        return 1
    print("✓ 全部通过" + ("（已写盘）" if a.write else "（dry-run）"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
