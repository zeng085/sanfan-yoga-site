#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_i18n_batch.py — 受控的多语言批量生成（带 DeepL 额度保护）

为什么需要它：translator._call_batch 在 DeepL 配额耗尽（HTTP 429/456）时会
**降级到 MyMemory 并把结果写进缓存**。MyMemory 质量明显更差，一旦写进缓存，
后续重跑命中缓存也不会修正。所以批量时必须主动监控额度、留出安全水位。

用法:
  python3 run_i18n_batch.py --batch i18n_batch1a.json                  # 全部语言
  python3 run_i18n_batch.py --batch i18n_batch1a.json --langs de ja    # 指定语言
  python3 run_i18n_batch.py --batch x.json --low-water 80000           # 自定义安全水位
  python3 run_i18n_batch.py --batch x.json --limit 2                   # 只跑前 N 页（试跑）

额度检查粒度：每跑完一个页面的全部语言查一次 /v2/usage。
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_pages as B          # noqa: E402
import translator as T           # noqa: E402

ROOT = B.ROOT


def remain():
    u = T.usage()
    if "character_count" not in u:
        print("  [WARN] 额度查询失败: %s" % u)
        return None
    return u["character_limit"] - u["character_count"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True, help="批次清单 JSON（{\"pages\": [...]}）")
    ap.add_argument("--langs", nargs="*", default=None, help="只跑指定语言，默认全部")
    ap.add_argument("--low-water", type=int, default=80000, help="剩余额度低于此值则停止")
    ap.add_argument("--limit", type=int, default=0, help="只跑前 N 页（0=全部）")
    args = ap.parse_args()

    all_pages = json.load(open(args.batch, encoding="utf-8"))["pages"]
    pages = all_pages[:args.limit] if args.limit else all_pages
    langs = [l for l in B.LANGS if (not args.langs or l in args.langs)]

    # ⚠️ 必须用「未截断」的完整清单更新 T1_SET。
    # rewrite_rel 依赖 T1_SET 判断目标页是否已有语言版；若这里只登记被 --limit
    # 截断后的子集，本批产物会把「同批但尚未生成」的页面当成无语言版，
    # 链接退化成 `../目标`（回退英文）并永久固化。
    # 实测后果：tpe-yoga-mats / pu-rubber-yoga-mats 的 9 个分类互链全部指向英文页，
    # 补齐后需用 fix_i18n_links.py 纠回（192 条）。
    B.T1_SET.update(all_pages)

    start_remain = remain()
    print("批次 %s：%d 页 × %d 语言 = %d 个页面" % (
        os.path.basename(args.batch), len(pages), len(langs), len(pages) * len(langs)))
    print("起始剩余额度 %s，安全水位 %s\n" % (f"{start_remain:,}" if start_remain else "?", f"{args.low_water:,}"))

    ok = fail = skipped_lang = 0
    stopped_at = None
    t_all = time.time()

    for idx, p in enumerate(pages, 1):
        t0 = time.time()
        for lg in langs:
            try:
                B.build_one(p, lg, verbose=False)
                ok += 1
            except SystemExit:
                print("  !! 被 SystemExit 中断（配额）")
                stopped_at = (p, lg)
                break
            except Exception as e:
                fail += 1
                print("  !! %s/%s -> %s" % (lg, p, e))
        print("  [%2d/%2d] %-44s %5.1fs  已生成 %d" % (
            idx, len(pages), p, time.time() - t0, ok), flush=True)
        if stopped_at:
            break

        r = remain()
        if r is not None and r < args.low_water:
            print("\n⚠️ 剩余额度 %s < 安全水位 %s，主动停止（避免降级到 MyMemory 污染缓存）"
                  % (f"{r:,}", f"{args.low_water:,}"))
            stopped_at = (p, "额度")
            break

    T.flush()
    end_remain = remain()
    print("\n完成：ok=%d fail=%d，用时 %.1f 分钟" % (ok, fail, (time.time() - t_all) / 60))
    if start_remain is not None and end_remain is not None:
        print("额度消耗 %s，剩余 %s" % (f"{start_remain - end_remain:,}", f"{end_remain:,}"))
    print("翻译引擎用量: %s" % T.stats())
    if stopped_at:
        print("⚠️ 在 %s 处停止，后续页面未处理" % (stopped_at,))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
