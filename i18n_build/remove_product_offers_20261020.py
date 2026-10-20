#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""摘除Product 节点里的 offers 字段（方向二：私询报价站不挂 Google 商品卡片）。

为什么（Search Console 2026-10-20 两封告警）：
  Merchant listings: Missing field "price" / "shippingDetails" / "hasMerchantReturnPolicy"
  Product snippets : Missing "lowPrice" / "price" or "priceSpecification.price" / "highPrice"
  → 根因同一个：offers 里没有可被 Google 认可的价格。

为什么选「摘 offers」而不是「补价格」：
  本站是 B2B 工厂站，报价走私询（contact 表单）。挂公开价格会招来比价客户，
  且价格随时随规格/数量浮动，写死即失真。Product 实体层（name/image/description/
  brand/manufacturer/@id/sku）才是 GEO 真正需要的部分，**摘掉 offers 不影响它**。

⚠️ 本脚本只删 Product 节点内的 offers 键，其余字段一字不动。
用法：
    python i18n_build/remove_product_offers_20261020.py --dry-run   # 先看统计与样本
    python i18n_build/remove_product_offers_20261020.py --apply# 实际改写
    python i18n_build/remove_product_offers_20261020.py --verify    # 验收
判据铁律：
  · 空集必须硬失败——扫不到任何 offers 就报错退出，不许静默返回 0
  · 改完必须 JSON 仍可解析（只删键不碰结构）
  · 保留缩进与原格式，避免整文件 diff 噪声
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def iter_html():
    for dp, dn, fn in os.walk(ROOT):
        if ".git" in dp or "node_modules" in dp:
            continue
        for f in fn:
            if f.endswith(".html"):
                yield os.path.join(dp, f)


def find_product_blocks(text):
    """返回所有含 Product 的 JSON-LD 块（起止下标）。

    策略：先粗定位 <script type="application/ld+json">…</script>，
    再在块内判断是否含 Product。对每个块做括号配平，截出精确区间。
    """
    spans = []
    for m in re.finditer(
        r'(<script[^>]*type\s*=\s*["\']application/ld\+json["\'][^>]*>)(.*?)(</script>)',
        text, re.S | re.I):
        body = m.group(2)
        if '"Product"' not in body and "'Product'" not in body:
            continue
        bs = m.start(2)
        spans.append((bs, m.end(2)))
    return spans


def offers_span_in_block(block):
    """在单个 JSON-LD 块文本内定位 Product 节点的 offers 键区间（含尾随逗号）。

    返回 (start, end) 或 None。处理多行缩进，删除后不留空行。
    """
    # Product 节点起点（取最近的 "name" 之前的 @type）
    pm = None
    for m in re.finditer(r'"?@type"?\s*:\s*"Product"', block):
        pm = m
        break
    if pm is None:
        return None
    # 从 Product 起找 offers
    om = re.search(r'("offers"\s*:\s*)', block[pm.start():])
    if om is None:
        return None
    key_start = pm.start() + om.start()
    brace_start = pm.start() + om.end()
    # 跳过空白后应为 {
    i = brace_start
    while i < len(block) and block[i] in " \t\r\n":
        i += 1
    if i >= len(block) or block[i] != "{":
        return None
    depth = 0
    j = i
    in_str = False
    esc = False
    while j < len(block):
        ch = block[j]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    j += 1
                    break
        j += 1
    # 吃掉尾随逗号+空白
    k = j
    while k < len(block) and block[k] in " \t":
        k += 1
    has_comma = k < len(block) and block[k] == ","
    if has_comma:
        j = k + 1
        # 连同后面的换行缩进一起吃掉，避免留空白行
        while j < len(block) and block[j] in " \t":
            j += 1
        if j < len(block) and block[j] == "\n":
            j += 1
    # ⭐ 关键：若 offers 是对象里的最后一个键，直接删掉会让前一个键留下尾随逗号 → JSON 非法。
    #   此时要把「前一个键末尾的逗号」也一并摘掉。
    prefix = block[:key_start].rstrip()
    if prefix.endswith(","):
        # 定位 offers 键之前最近的那个逗号（它属于前一个键），从那里开始删。
        cpos = block.rfind(",", 0, key_start)
        if cpos != -1:
            start = cpos
            # 向前吃掉该逗号所在行前面的换行与缩进
            m = start
            while m > 0 and block[m - 1] in " \t":
                m -= 1
            if m > 0 and block[m - 1] == "\n":
                m -= 1
            key_start = m
    return key_start, j


def process(path, apply_changes):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if '"offers"' not in text:
        return None
    spans = find_product_blocks(text)
    if not spans:
        return None
    cuts = []
    for bs, be in spans:
        block = text[bs:be]
        sp = offers_span_in_block(block)
        if sp:
            cuts.append((bs + sp[0], bs + sp[1]))
    if not cuts:
        return None
    if apply_changes:
        for s, e in sorted(cuts, reverse=True):
            text = text[:s] + text[e:]
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
    return len(cuts)


def verify(path):
    """验收：所有 ld+json 块必须仍可解析，且 Product 节点不含 offers。"""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    bad_json = []
    stats = {"products": 0, "offers_left": 0}

    def walk(o):
        if isinstance(o, dict):
            if o.get("@type") == "Product":
                stats["products"] += 1
                if "offers" in o:
                    stats["offers_left"] += 1
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    for m in re.finditer(
        r'<script[^>]*type\s*=\s*["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        text, re.S | re.I):
        raw = m.group(1).strip()
        if not raw:
            continue
        try:
            d = json.loads(raw)
        except Exception as exc:
            bad_json.append(str(exc)[:70])
            continue
        walk(d)
    return bad_json, stats["products"], stats["offers_left"]


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--dry-run"
    if mode not in ("--dry-run", "--apply", "--verify"):
        print(__doc__)
        sys.exit(2)

    files = list(iter_html())
    if not files:
        print("FAIL: 没扫到任何 HTML，目录有问题")
        sys.exit(1)

    if mode in ("--dry-run", "--apply"):
        changed = 0
        cuts_total = 0
        samples = []
        for p in files:
            n = process(p, mode == "--apply")
            if n:
                changed += 1
                cuts_total += n
                if len(samples) < 3:
                    samples.append((p, n))
        if cuts_total == 0:
            print("FAIL: 一个 offers 都没摘到 —— 判据或格式有问题，硬失败")
            sys.exit(1)
        print(f"[{mode}] 处理页数={changed}摘除offers={cuts_total}")
        for p, n in samples:
            print(f"样例: {os.path.relpath(p, ROOT)} 摘除 {n} 处")
        if mode == "--dry-run":
            print("\n这是演练，未落盘。确认无误后跑 --apply")

    if mode == "--verify":
        bad_total = 0
        prod_total = 0
        offers_total = 0
        badfiles = []
        for p in files:
            b, prods, off = verify(p)
            bad_total += len(b)
            prod_total += prods
            offers_total += off
            if b:
                badfiles.append((os.path.relpath(p, ROOT), b))
        if bad_total:
            print(f"FAIL: {bad_total} 个 JSON 解析失败")
            for f, b in badfiles[:5]:
                print("  ", f, b)
            sys.exit(1)
        if prod_total == 0:
            print("FAIL: 一个 Product 节点都没扫到，判据失效，硬失败")
            sys.exit(1)
        if offers_total:
            print(f"FAIL: 仍有 {offers_total} 处 offers 残留")
            sys.exit(1)
        print(f"[verify] JSON 全部可解析 ✓ Product 节点={prod_total} offers 残留=0 ✓")


if __name__ == "__main__":
    main()