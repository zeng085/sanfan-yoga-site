# -*- coding: utf-8 -*-
"""把《2026年福建三梵普拉提大器械价格表（代理）》PDF 解析成结构化行。

只做解析，不做翻译、不落站。产物：i18n_build/data/pilates_offer_raw.json

    python3 i18n_build/extract_pilates_offer.py [pdf路径]

解析规则（对着 PDF 实际排版写的，改动前先看 raw 输出）：
    每行形如   序号 编号 [材质] 名称 [（备注）] *规格条目... 代理价
    序号会重复（NIC201 出现两次，是不同木种），所以主键用 编号+序号。
    规格条目以 * 开头，pypdf 会把长句折成多行，需要把不以 * 开头且不是价格的续行接回去。
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "data", "pilates_offer_raw.json")

DEFAULT_PDF = "/tmp/pilates_big.pdf"

# 页眉/页脚噪声
NOISE = re.compile(r"^(序号\s+编号|承诺：|）$|所有木头床架|2026年福建三梵普拉提大器械价格表)")

CODE = re.compile(r"^(NI[A-Z]\d{3}|NLH\d{3})$")
ROWSTART = re.compile(r"^(\d{1,2})\s+(NI[A-Z]\d{3}|NLH\d{3})\s*(.*)$")
PRICE = re.compile(r"^\d{3,6}$")


def pdf_text(path):
    from pypdf import PdfReader
    r = PdfReader(path)
    pages = []
    for p in r.pages:
        t = p.extract_text() or ""
        pages.append([ln.rstrip() for ln in t.splitlines()])
    return pages


def parse(pages):
    rows, cur = [], None

    def flush():
        if cur and (cur["code"] or cur["bullets"]):
            rows.append(cur)

    for pi, lines in enumerate(pages, 1):
        for raw in lines:
            ln = raw.strip()
            if not ln or NOISE.match(ln):
                continue

            m = ROWSTART.match(ln)
            if m:
                flush()
                cur = {"page": pi, "no": int(m.group(1)), "code": m.group(2),
                       "head": [x for x in [m.group(3).strip()] if x.strip()],
                       "bullets": [], "price": None}
                continue

            if cur is None:
                continue

            if ln.startswith("*"):
                cur["bullets"].append(ln.lstrip("*").strip())
                continue
            if PRICE.match(ln):
                cur["price"] = int(ln)
                continue
            # 续行：接在上一条 bullet 后面，否则算 head
            if cur["bullets"]:
                cur["bullets"][-1] += ln
            elif len(cur["head"]) < 4:
                cur["head"].append(ln)
    flush()
    return rows


def main():
    pdf = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PDF
    if not os.path.exists(pdf):
        print("找不到 PDF：", pdf)
        sys.exit(1)
    rows = parse(pdf_text(pdf))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(rows, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("解析 %d 行 → %s" % (len(rows), OUT))
    for r in rows:
        print("  #%-2d %-7s p%d price=%-6s head=%s bullets=%d"
              % (r["no"], r["code"], r["page"], r["price"],
                 "/".join(r["head"])[:34], len(r["bullets"])))


if __name__ == "__main__":
    main()
