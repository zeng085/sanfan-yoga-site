#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给 sitemap 补 lastmod（取每个页面文件的 git 最后提交时间），并删除已废弃的
changefreq / priority。

为什么（2026-10-20 诊断）：
  1386 条 URL 全部缺 <lastmod>，而 Google 靠它判断「哪些页真的更新了」。
  没有 lastmod → 默认极低频重抓 → 这是「一个月收录零增长」最直接的技术原因。
  另外 changefreq / priority 已被 Google 官方明确忽略，留着只增加体积与解析成本。

判据铁律：
  · lastmod 必须是**真实的 git 提交时间**，不能统一填今天（造假会被 Google 识破）
  · 空集必须硬失败：一条 lastmod 都没补上就报错
  · 补完后 <loc> 数量必须与原来完全一致（不能漏页）
用法：
    python i18n_build/sitemap_lastmod_20261020.py --dry-run
    python i18n_build/sitemap_lastmod_20261020.py --apply
    python i18n_build/sitemap_lastmod_20261020.py --verify
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITEMAP = os.path.join(ROOT, "sitemap.xml")


def sh(*args):
    return subprocess.run(list(args), capture_output=True, text=True).stdout


def url_to_path(url):
    """https://fjsanfan.com/de/products/ym3.html -> de/products/ym3.html"""
    p = url.replace("https://fjsanfan.com/", "", 1)
    if not p or p == "":
        return "index.html"
    if p.endswith("/"):
        p += "index.html"
    return p


def git_mtime(path):
    """该文件最后一次改动它的 commit 的作者时间（ISO 8601）。"""
    out = sh("git", "log", "-1", "--format=%cI", "--", path).strip()
    if out:
        return out
    # 文件若从未提交（或历史缺失），退回文件系统 mtime
    try:
        import datetime
        ts = os.path.getmtime(os.path.join(ROOT, path))
        return datetime.datetime.fromtimestamp(ts).astimezone().isoformat()
    except Exception:
        return None


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--dry-run"
    if mode not in ("--dry-run", "--apply", "--verify"):
        print(__doc__)
        sys.exit(2)

    with open(SITEMAP, encoding="utf-8") as fh:
        xml = fh.read()

    locs = re.findall(r"<loc>([^<]+)</loc>", xml)
    if not locs:
        print("FAIL: sitemap 里没有任何 <loc>，判据失效，硬失败")
        sys.exit(1)

    if mode == "--verify":
        lm = re.findall(r"<lastmod>([^<]+)</lastmod>", xml)
        freq = xml.count("<changefreq>")
        prio = xml.count("<priority>")
        locs2 = re.findall(r"<loc>([^<]+)</loc>", xml)
        print(f"[verify] loc={len(locs2)} lastmod={len(lm)} changefreq={freq} priority={prio}")
        ok = True
        if len(lm) != len(locs2):
            print(f"  ✗ lastmod 数量 {len(lm)} != loc 数量 {len(locs2)}")
            ok = False
        if freq or prio:
            print(f"  ✗ 仍有废弃字段：changefreq={freq} priority={prio}")
            ok = False
        # lastmod 不能全是同一天（造假判据）
        if lm and len(set(x[:10] for x in lm)) == 1:
            print(f"  ✗ 所有 lastmod 都是同一天 {lm[0][:10]}，疑似造假")
            ok = False
        if ok:
            print("  ✅ 通过：lastmod 全覆盖、废弃字段已清、时间有真实分布")
        else:
            sys.exit(1)
        return

    # 缓存 git 时间，避免重复调用
    cache = {}
    filled = 0
    missing = []
    out_parts = []
    pos = 0

    for m in re.finditer(r"(<loc>[^<]+</loc>)(.*?)(</url>)", xml, re.S):
        block_head, mid, tail = m.group(1), m.group(2), m.group(3)
        url = re.search(r"<loc>([^<]+)</loc>", block_head).group(1)
        path = url_to_path(url)

        # 清掉废弃字段（含其所在行的缩进换行）
        mid_clean = re.sub(r"\s*<changefreq>[^<]*</changefreq>", "", mid)
        mid_clean = re.sub(r"\s*<priority>[^<]*</priority>", "", mid_clean)
        # 若已有 lastmod 先去掉，统一重算
        mid_clean = re.sub(r"\s*<lastmod>[^<]*</lastmod>", "", mid_clean)

        if path not in cache:
            cache[path] = git_mtime(path)
        lm = cache[path]
        if lm:
            filled += 1
        else:
            missing.append(url)

        new_block = block_head + mid_clean + (
            f"\n    <lastmod>{lm}</lastmod>" if lm else "") + "\n  " + tail
        out_parts.append((m.start(), m.end(), new_block))

    if filled == 0:
        print("FAIL: 一条 lastmod 都没能取到，判据或路径映射有问题，硬失败")
        sys.exit(1)

    new_xml = xml
    for start, end, block in sorted(out_parts, reverse=True):
        new_xml = new_xml[:start] + block + new_xml[end:]

    print(f"处理 URL: {len(out_parts)}")
    print(f"补上 lastmod: {filled}")
    print(f"取不到时间: {len(missing)}")
    if missing[:5]:
        for u in missing[:5]:
            print("   ", u)
    # 时间分布抽样
    sample = sorted(set(cache.values()))[-3:]
    print(f"lastmod 时间范围（最近3个）: {sample}")

    if mode == "--apply":
        with open(SITEMAP, "w", encoding="utf-8") as fh:
            fh.write(new_xml)
        print("✅ 已写入 sitemap.xml")
    else:
        print("（演练，未落盘）")


if __name__ == "__main__":
    main()