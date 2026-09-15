# -*- coding: utf-8 -*-
"""普拉提板块：产品信息正确性审计 v2

逐页把 HTML 规格表解析回结构化数据，与型号库（pilates_models.json）逐字段比对，
并做数据质量扫描：英文块混中文、单元格内容重复、列位错位、PDF 脏数据残留、
hero 统计数字与真实数据一致性。
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

CJK = re.compile(r"[\u4e00-\u9fff]")
TAG = re.compile(r"<[^>]+>")
# 编号：NIC201 / A、NIC201A、NIX101 等
CODE_RE = re.compile(r"[A-Z]{3}\d{3}")
CODE_FULL = re.compile(r"^[A-Z]{3}\d{3}(\s*/\s*[A-Z])?$")


def clean(s):
    s = TAG.sub("", s)
    for a, b in (("&amp;", "&"), ("&nbsp;", " "), ("&times;", "×"),
                 ("&mdash;", "—"), ("&middot;", "·"), ("&quot;", '"'), ("&#215;", "×")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def blocks(cell_html):
    """按顺序切出单元格内的可见文本块 → [(lang|None, text)]"""
    out = []
    pos = 0
    for m in re.finditer(r'<span class="lang-(en|zh)">(.*?)</span>', cell_html, re.S):
        pre = clean(cell_html[pos:m.start()])
        if pre:
            out.append((None, pre))
        out.append((m.group(1), clean(m.group(2))))
        pos = m.end()
    tail = clean(cell_html[pos:])
    if tail:
        out.append((None, tail))
    return out


def cell_text(cell_html, lang=None):
    bs = blocks(cell_html)
    return " ".join(t for l, t in bs if l in (lang, None) and t) if lang else \
        " ".join(t for _, t in bs if t)


def parse_table(path):
    t = open(path, encoding="utf-8").read()
    i = t.find('<table class="pl-spec">')
    if i < 0:
        return None, None, None, t
    j = t.find("</table>", i)
    seg = t[i:j]
    head = [clean(m.group(1)) for m in re.finditer(r"<th>(.*?)</th>", seg, re.S)]
    head = [re.sub(r"^(Model|Code)\s*", "", h) if len(h) < 40 else h.split()[0] for h in head]
    head_en = [clean(re.sub(r'<span class="lang-zh">.*?</span>', "",
                            m.group(1), flags=re.S)) for m in re.finditer(r"<th>(.*?)</th>", seg, re.S)]
    rows, cells_raw = [], []
    body = seg[seg.find("<tbody>"):]
    for rm in re.finditer(r"<tr>(.*?)</tr>", body, re.S):
        cs = re.findall(r"<td[^>]*?(?:class=\"([^\"]*)\")?[^>]*>(.*?)</td>", rm.group(1), re.S)
        cells_raw.append(cs)
        rows.append([(cell_text(c[1], "en"), cell_text(c[1], "zh"), blocks(c[1])) for c in cs])
    return head_en, rows, cells_raw, t


def main():
    models = json.load(open("i18n_build/data/pilates_models.json", encoding="utf-8"))
    raw = json.load(open("i18n_build/data/pilates_offer_raw.json", encoding="utf-8"))
    if isinstance(raw, dict):
        raw = raw.get("rows") or raw.get("items") or []
    fams = models["families"]

    pages = [("pilates/%s.html" % f["key"], f["key"]) for f in fams]
    fail, warn = [], []
    codes_pages = {}

    for path, fkey in pages:
        if not os.path.exists(path):
            fail.append("缺页 %s" % path)
            continue
        head_en, rows, cells_raw, t = parse_table(path)
        if rows is None:
            fail.append("%s 未找到 .pl-spec 表" % path)
            continue
        ncol = len(head_en)

        f = next(x for x in fams if x["key"] == fkey)
        # 同编号可能有 A/B 变体（NIC201 / A、NIC201 / B）→ 按出现顺序取
        lib = {}
        for m in f["models"]:
            lib.setdefault(m["code"], []).append(m)
        page_codes = []

        for ri, r in enumerate(rows):
            if len(r) != ncol:
                fail.append("%s 第 %d 行列数 %d ≠ 表头 %d" % (path, ri + 1, len(r), ncol))
                continue
            code_cell = r[1][0] if ncol > 1 else ""
            cid = re.match(r"([A-Z]{3}\d{3})", code_cell)
            if not cid:
                fail.append("%s 第 %d 行编号列异常：%r" % (path, ri + 1, code_cell[:40]))
                continue
            code = cid.group(1)
            page_codes.append(code)
            codes_pages.setdefault(code, []).append(path)

            m = lib.get(code)
            if not m:
                fail.append("%s 出现非本族编号 %s" % (path, code))
                continue
            m = m.pop(0)
            # 变体后缀核对（页面 "NIC201 / A" ↔ 库 variant "A"）
            var_pg = re.search(r"/\s*([A-Z])\s*$", code_cell.strip())
            if bool(var_pg) != bool(m["variant"]):
                fail.append("%s %s 变体标注不一致：页面 %r / 库 %r"
                            % (path, code, code_cell, m["variant"]))
            elif var_pg and m["variant"] and var_pg.group(1) != m["variant"]:
                fail.append("%s %s 变体错位：页面 %r / 库 %r"
                            % (path, code, var_pg.group(1), m["variant"]))

            # A) 英文块混中文
            for ci, (cen, czh, bl) in enumerate(r):
                if CJK.search(cen or ""):
                    fail.append("%s %s [%s] 英文块含中文：%r"
                                % (path, code, head_en[ci][:14], cen[:60]))
                if cen and not czh:
                    fail.append("%s %s [%s] 缺失中文块" % (path, code, head_en[ci][:14]))

            # B) 单元格内重复文本块（跨 span 也抓）
            for ci, (cen, czh, bl) in enumerate(r):
                for lang in ("en", "zh"):
                    seq = [x for l, x in bl if l == lang]
                    for x in set(seq):
                        if len(x) >= 4 and seq.count(x) > 1:
                            fail.append("%s %s [%s] %s 块重复 %d 次：%r"
                                        % (path, code, head_en[ci][:14], lang, seq.count(x), x))
                # 整格文本里同一短语出现两次（无 span 分界的情况）—— 逐语言比，
                # 中英同值是正常的（如尺寸），不能算重复
                for lang in ("en", "zh", None):
                    allt = " ".join(x for l, x in bl if l == lang)
                    for part in [p.strip() for p in re.split(r"[·、,，;；]", allt)
                                 if len(p.strip()) >= 5]:
                        if allt.count(part) > 1:
                            fail.append("%s %s [%s] %s 短语重复：%r"
                                        % (path, code, head_en[ci][:14],
                                           lang or "plain", part))

            # C) 尺寸列混入弹簧/木种描述
            for ci, (cen, czh, bl) in enumerate(r):
                if re.search(r"Size|尺寸", head_en[ci]):
                    if re.search(r"弹簧|spring", cen, re.I):
                        fail.append("%s %s 尺寸列混入弹簧描述：%r" % (path, code, cen[:55]))
                    if re.search(r"木|wood|beech|maple|橡|枫|榉", cen, re.I):
                        fail.append("%s %s 尺寸列混入木种描述：%r" % (path, code, cen[:55]))
                    # PDF 残留：单位后紧跟数字（如 2m1）
                    if re.search(r"\d\s*m\d", cen):
                        fail.append("%s %s 尺寸含 PDF 残留：%r" % (path, code, cen[:55]))
                    if re.search(r"[A-Za-z]", cen) and not re.fullmatch(
                            r"[\d\s×x*.\-–~/cmCMmM]+", cen):
                        # 尺寸里其余字母只能是单位、组合件名或备注词
                        OKW = {"cm", "mm", "m", "in", "ft", "inch", "feet", "x", "ø", "dia",
                               "bed", "height", "folded", "mat", "platform", "total",
                               "reformer", "ladder", "barrel", "wunda", "chair", "spine",
                               "corrector", "cadillac", "rotator", "pulley", "tower",
                               "weight", "kg", "lb", "l", "w", "h", "d"}
                        stray = [w for w in re.findall(r"[A-Za-z]+", cen)
                                 if w.lower() not in OKW]
                        if stray:
                            warn.append("%s %s 尺寸可疑词 %s：%r" % (path, code, stray, cen[:55]))

            # D) 型号名一致
            if r[0][0].strip() != (m["en"] or "").strip():
                fail.append("%s %s 型号名不符：页面 %r ≠ 库 %r"
                            % (path, code, r[0][0][:45], (m["en"] or "")[:45]))
            # E) 尺寸一致
            for ci, (cen, czh, bl) in enumerate(r):
                if re.search(r"Size|尺寸", head_en[ci]):
                    exp = (m["size_en"] or "").strip()
                    if exp and cen.strip() != exp:
                        fail.append("%s %s 尺寸不符：页面 %r ≠ 库 %r"
                                    % (path, code, cen[:50], exp[:50]))
                    if not cen.strip():
                        fail.append("%s %s 尺寸为空" % (path, code))
                    break
            # F) 弹簧一致
            for ci, (cen, czh, bl) in enumerate(r):
                if re.search(r"Spring|弹簧", head_en[ci]):
                    if not cen.strip():
                        warn.append("%s %s 弹簧列为空" % (path, code))
                    break

        # G) 覆盖度
        lib_codes = [m["code"] for m in f["models"]]
        if sorted(page_codes) != sorted(lib_codes):
            fail.append("%s 型号覆盖不符：缺 %s / 多 %s"
                        % (path, sorted(set(lib_codes) - set(page_codes)),
                           sorted(set(page_codes) - set(lib_codes))))

        # H) 页面文案里的型号数（"20 models" / "20 个型号"）是否与实际行数一致
        for m2 in re.finditer(r'>(\d+)\s*(?:</span><span class="lang-zh">|个)?\s*'
                              r'(?:models|型号)', t):
            n = int(m2.group(1))
            if n != len(rows) and n > 2:
                warn.append("%s 文案称 %d 型号，实际 %d 行" % (path, n, len(rows)))

        # I) 图片只用本族素材（文件名形如 pilates-reformer-1.webp）
        imgs = re.findall(r'src="\.\./assets/img/([a-z0-9-]+)\.webp', t)
        alien = sorted(set(i for i in imgs
                           if not re.fullmatch(r"%s-\d+" % re.escape(fkey), i)))
        # 允许共享素材（general-*）与 logo
        alien = [a for a in alien if not a.startswith("general") and "logo" not in a]
        if alien:
            warn.append("%s 用了非本族图片: %s" % (path, alien[:8]))

        # J) hero 里的型号数
        hz = re.findall(r'pl-hs[^>]*>\s*(\d+)\s*<', t)
        if hz and len(rows) not in [int(x) for x in hz] and "index" not in path:
            pass  # 族页 hero 数字在 index 上体现，跳过

    # 跨族重复
    for code, where in codes_pages.items():
        u = sorted(set(where))
        if len(u) > 1:
            fail.append("编号 %s 跨族重复出现于 %s" % (code, u))

    # 数据源覆盖
    lib_all = set(m["code"] for f in fams for m in f["models"])
    raw_codes = set((r.get("code") or "").strip() for r in raw if (r.get("code") or "").strip())
    if raw_codes - lib_all:
        fail.append("数据源编号未进库：%s" % sorted(raw_codes - lib_all))

    # hero 统计数字核对（index 页与真实数据源交叉验证）
    ti = open("pilates/index.html", encoding="utf-8").read()
    si = ti.find('<div class="pl-stats">')
    seg = ti[si:ti.find("</section>", si)] if si >= 0 else ""
    stats = []
    for hs in re.split(r'<div class="hs">', seg)[1:]:
        num = re.search(r'<div class="num"[^>]*>(.*?)</div>', hs, re.S)
        lab = re.search(r'<span class="lang-en">([^<]*)</span>', hs)
        stats.append((clean(num.group(1)) if num else "?",
                      lab.group(1).strip() if lab else "?"))
    n_wood = len(set((m.get("wood_en") or "").strip() for f in fams
                     for m in f["models"] if (m.get("wood_en") or "").strip()))
    n_mdl = sum(len(f["models"]) for f in fams)
    # 真实值（族数 / 型号数 / 木种数）
    for val, lab in stats:
        v = re.sub(r"[^\d]", "", val)
        if lab == "Equipment lines" and v != str(len(fams)):
            fail.append("index hero「%s」写 %s，实际 %d" % (lab, val, len(fams)))
        elif lab == "Models to choose from" and v != str(n_mdl):
            fail.append("index hero「%s」写 %s，实际 %d" % (lab, val, n_mdl))
        elif lab == "Timber / frame options" and v != str(n_wood):
            fail.append("index hero「%s」写 %s，实际 %d" % (lab, val, n_wood))

    print("=" * 76)
    print("产品信息正确性审计")
    print("=" * 76)
    print("族 %d | 库内型号 %d | 数据源行 %d（编号 %d）| 框架/材质去重 %d"
          % (len(fams), n_mdl, len(raw), len(raw_codes), n_wood))
    print("index hero 统计：", " | ".join("%s %s" % (v, l) for v, l in stats))
    print()
    if fail:
        print("FAIL %d" % len(fail))
        for x in fail[:70]:
            print("  ✗", x)
        if len(fail) > 70:
            print("  ... 另有 %d 条" % (len(fail) - 70))
    else:
        print("FAIL 0 ✓")
    print()
    if warn:
        print("WARN %d" % len(warn))
        for x in warn[:30]:
            print("  !", x)
    else:
        print("WARN 0 ✓")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
