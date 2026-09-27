#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""探测 2026 英文版普拉提电子图册 PDF 的结构。

输出：页数、每页文本长度/前 120 字符、图片数、页面尺寸。
只读，不改任何站点文件。
用法：
    $VENV/bin/python i18n_build/probe_catalog_pdf.py
"""
import json
import pathlib
import sys

import pypdf

ROOT = pathlib.Path(__file__).resolve().parent.parent
PDF = ROOT / "i18n_build" / "data" / "catalog_pilates_2026_en.pdf"


def main():
    if not PDF.exists():
        sys.exit("找不到 PDF：%s" % PDF)
    r = pypdf.PdfReader(str(PDF))
    n = len(r.pages)
    print("文件: %s" % PDF.name)
    print("大小: %.1f MB" % (PDF.stat().st_size / 1048576))
    print("页数: %d" % n)
    md = r.metadata or {}
    for k in ("/Title", "/Author", "/Subject", "/Creator", "/Producer"):
        if md.get(k):
            print("  %-10s %s" % (k, md[k]))
    print()

    rows = []
    for i, page in enumerate(r.pages, 1):
        try:
            txt = page.extract_text() or ""
        except Exception as e:                      # noqa: BLE001
            txt = ""
            print("  第 %d 页取文本失败: %s" % (i, e))
        try:
            box = page.mediabox
            w, h = float(box.width), float(box.height)
        except Exception:                           # noqa: BLE001
            w = h = 0.0
        try:
            nimg = len(page.images)
        except Exception:                           # noqa: BLE001
            nimg = -1
        flat = " ".join(txt.split())
        rows.append({"page": i, "chars": len(flat), "img": nimg,
                     "w": round(w), "h": round(h), "head": flat[:120]})
        print("  p%-3d 字数=%-5d 图=%-3d 页面=%.0fx%.0f  %s"
              % (i, len(flat), nimg, w, h, flat[:90]))

    out = ROOT / "i18n_build" / "data" / "catalog_pdf_probe.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n→ 明细已写 %s" % out.relative_to(ROOT))
    print("合计文本字符: %d | 合计图片: %d"
          % (sum(x["chars"] for x in rows), sum(max(0, x["img"]) for x in rows)))


if __name__ == "__main__":
    main()
