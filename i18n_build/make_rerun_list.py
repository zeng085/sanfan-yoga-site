#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从语言站反推「已翻译页面」清单 —— 用于零成本重跑（缓存全命中，消耗 0 字符）。

为什么需要它：
  改了 rewrite_rel 逻辑 / 新增了语言页之后，必须**重新生成引用方页面**，链接才会
  改指新的语言版。但直接跑 `build_pages.py`（不带 --batch）会遍历 ALL_PAGES，
  把 96 个**尚未翻译**的产品页也拿去调 API —— 额度会被吃掉。所以重跑必须精确
  限定为「磁盘上已有语言版的页面」。

清单来源 = build_pages.translated_set()（6 语言目录取交集），保证清单里的每一页
都确实已有 6 个语言版本，重跑时译文全部命中缓存。

输出：i18n_rerun.json（{"pages": [...]}），可直接喂给
      python3 i18n_build/run_i18n_batch.py --batch i18n_rerun.json --low-water 100000

用法：
  python3 i18n_build/make_rerun_list.py           # 生成清单
  python3 i18n_build/make_rerun_list.py --list    # 只打印，不写文件
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_pages as B          # noqa: E402


def main():
    pages = sorted(B.translated_set())
    miss = [p for p in pages if not os.path.exists(os.path.join(B.ROOT, p))]
    print("已翻译页面（6 语言交集）：%d 页" % len(pages))
    print("  其中英文原页缺失（会被跳过）：%d" % len(miss))
    for m in miss[:20]:
        print("    !! 缺失 ->", m)
    pages = [p for p in pages if p not in set(miss)]

    if "--list" in sys.argv:
        for p in pages:
            print(" ", p)
        return 0

    out = os.path.join(HERE, "i18n_rerun.json")
    json.dump({"_note": "重跑清单：磁盘上已有 6 语言版本的页面（缓存全命中，0 消耗）",
               "pages": pages},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("\n已写入 %s（%d 页）" % (os.path.relpath(out, B.ROOT), len(pages)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
