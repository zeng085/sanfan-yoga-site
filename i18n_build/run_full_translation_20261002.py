#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全量翻译跑批（10-02）：6 篇博客 + pilates 9 页 的 EN 源文本 × 6 语言 → GLM。
产物 = 翻译缓存（供后续语言版页面生成链路查询复用），本脚本不改任何页面。

用法：
    python run_full_translation_20261002.py --dry     # 只提取统计，不调 API
    python run_full_translation_20261002.py           # 全量跑
    python run_full_translation_20261002.py --langs de,ja   # 只跑部分语言

守卫（铁律「对照工具的静默跳过比误报更危险」）：
  - 任何一步 stats 出现 mymemory/fail 增量 → 当场 abort（降级译文绝不允许混入）
  - 结束后 flush() 强制落盘
"""
import os
import re
import sys
import glob
import time
import html as _html

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import translator as T  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANGS = ["de", "ja", "ko", "fr", "it", "es"]

BLOGS = sorted(set(glob.glob(os.path.join(ROOT, "blog", "pilates-*.html")))
               | {os.path.join(ROOT, "blog", "oem-pilates-equipment-china.html")})
PILATES = sorted(glob.glob(os.path.join(ROOT, "pilates", "*.html")))
PAGES = BLOGS + PILATES

_BLOCK_RE = re.compile(r"<(h1|h2|h3|h4|p|li|td|th|figcaption)\b[^>]*>(.*?)</\1>", re.S)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def div_balance_cut(s, cls):
    """删掉 <div class="cls">...</div> 整块（div 配平扫描，容忍嵌套）。"""
    out, pos = [], 0
    pat = re.compile(r'<div class="' + cls + r'">')
    while True:
        m = pat.search(s, pos)
        if not m:
            out.append(s[pos:])
            break
        out.append(s[pos:m.start()])
        depth = 1
        end = len(s)
        for t in re.finditer(r"<div\b|</div>", s[m.end():]):
            if t.group(0) == "<div":
                depth += 1
            else:
                depth -= 1
                if depth == 0:
                    end = m.end() + t.end()
                    break
        else:
            end = len(s)
        pos = end
    return "".join(out)


def _clean_text(h):
    t = _TAG_RE.sub(" ", h)
    t = _html.unescape(t)
    t = _WS_RE.sub(" ", t).strip()
    # 实体二次出现（双层转义）兜底
    if "&" in t:
        t = _html.unescape(t)
    # span 边界残留的「  .」（提取侧与后续生成链路共用本函数 → 键一致）
    t = re.sub(r"\s+([.,;:!?])", r"\1", t)
    return t


def _keep(t):
    """可翻译判据：非空、含字母、非纯数字/符号、长度 >= 2。"""
    if not t or len(t) < 2:
        return False
    if not re.search(r"[A-Za-z\u00c0-\u024f]", t):
        return False
    # 纯型号/数字/尺寸（如 "1830 x 610 x 6 mm" / "AL 13 MC"）不值得进引擎：
    # 型号保留原样是术语表行为，纯尺寸无词可翻
    stripped = re.sub(r"[\d\s.,×xX/+\-()mm%kg°\"']+", "", t)
    if not stripped:
        return False
    return True


def extract_page(path):
    """单页提取：title + meta description + 内容区块级文本（顺序保持）。"""
    s = open(path, encoding="utf-8").read()
    # 内容区：nav 结束 → footer（缺则整页）
    a = s.find("</nav>")
    b = s.find("<footer")
    if a != -1 and b != -1 and a < b:
        chrome = s[:a] + s[b:]      # nav+footer 单独收（供后续模板链路）
        s = s[a:b]
    else:
        chrome = ""

    s = re.sub(r"<script[\s\S]*?</script>", " ", s)
    s = re.sub(r"<style[\s\S]*?</style>", " ", s)
    chrome = re.sub(r"<script[\s\S]*?</script>", " ", chrome)
    chrome = re.sub(r"<style[\s\S]*?</style>", " ", chrome)

    lines = []
    title = re.search(r"<title>(.*?)</title>", chrome, re.S)
    if title:
        lines.append(_clean_text(title.group(1)))
    md = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', chrome)
    if md:
        lines.append(_clean_text(md.group(1)))

    for src in (s, chrome):
        # 中文副本清除：大 div（配平）→ 行内 span（非嵌套）
        src = div_balance_cut(src, "lang-zh")
        src = re.sub(r'<span class="lang-zh">.*?</span>', " ", src, flags=re.S)
        for m in _BLOCK_RE.finditer(src):
            t = _clean_text(m.group(2))
            if _keep(t):
                lines.append(t)
    return lines


def collect():
    """全局收集：页序保持、全局去重。返回 [(text, [来源页...]), ...]"""
    seen = {}
    order = []
    per_page = {}
    for p in PAGES:
        ls = extract_page(p)
        per_page[os.path.relpath(p, ROOT)] = ls
        for t in ls:
            if t not in seen:
                seen[t] = []
                order.append(t)
            seen[t].append(os.path.relpath(p, ROOT))
    return order, seen, per_page


def main():
    dry = "--dry" in sys.argv
    langs = LANGS
    for a in sys.argv:
        if a.startswith("--langs"):
            langs = a.split("=", 1)[1].split(",") if "=" in a else LANGS
    if "--langs" in sys.argv:
        i = sys.argv.index("--langs")
        if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("-"):
            langs = sys.argv[i + 1].split(",")

    order, seen, per_page = collect()
    chars = sum(len(t) for t in order)

    print("=" * 72)
    print("① 提取统计（%d 页）" % len(PAGES))
    for f, ls in sorted(per_page.items()):
        print(f"   {f:52s} {len(ls):>4} 行  {sum(map(len, ls)):>7,} 字符")
    print(f"   {'合计（去重前）':52s} {sum(len(v) for v in per_page.values()):>4} 行")
    print(f"   {'全局去重后':52s} {len(order):>4} 行  {chars:>7,} 字符 × {len(langs)} 语言")

    if dry:
        print("\n② dry-run 抽样（前 12 条 + 表格类 6 条）：")
        for t in order[:12]:
            print("   ·", t[:100])
        tds = [t for t in order if len(t) < 30]
        print("   ……短行（多为表格单元格）示例：")
        for t in tds[:6]:
            print("   ·", t)
        print("\nDRY-RUN 结束，未调 API。")
        return

    # ---- 正式跑 ----
    s0 = T.stats()
    print("\n② 起始 stats:", s0)
    t_start = time.time()
    for lg in langs:
        st_before = T.stats()
        t0 = time.time()
        out = T.translate_lines(order, lg, verbose=True)
        st = T.stats()
        dd = st["mymemory"] - st_before.get("mymemory", 0)
        df = st["fail"] - st_before.get("fail", 0)
        new = st["glm"] - st_before.get("glm", 0)
        print(f"[{lg}] 完成 {len(out)} 行 | glm新增={new} mymemory+{dd} fail+{df} "
              f"| 耗时 {time.time()-t0:.0f}s | 累计 {time.time()-t_start:.0f}s", flush=True)
        if dd or df:
            T.flush()
            raise SystemExit(f"ABORT：{lg} 出现降级（mymemory+{dd} fail+{df}），"
                             f"缓存已落盘，清污后重跑。绝不允许降级译文混入全量缓存。")
    T.flush()
    st = T.stats()
    print("=" * 72)
    print("③ 全部完成。最终 stats:", st)
    print(f"   总耗时 {(time.time()-t_start)/60:.1f} min")
    print("   flush 已落盘。")


if __name__ == "__main__":
    main()
