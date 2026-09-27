#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""OCR 提取 2026 英文版普拉提电子画册的型号与规格。

背景：该 PDF 由 Adobe Acrobat Image Conversion 生成，**无文字层**（42 页全 0 字符），
只能用 OCR 或视觉识别。本脚本走 macOS 原生 Vision（ocrmac），印刷体置信度实测 1.00。

做法：
  1) 逐页 OCR，拿到 (文本, 置信度, bbox)
  2) 按 bbox 的 y 坐标把「型号块」聚类成一台器械（型号行 + 其后的 Material/Packing/Weight 行）
  3) 输出结构化 JSON + 摘要表

用法：
    $VENV/bin/python i18n_build/ocr_catalog_pilates.py
输出：
    i18n_build/data/catalog_pilates_ocr.json   每页原始行（含 bbox）
    i18n_build/data/catalog_pilates_models.json 结构化型号
"""
import json
import pathlib
import re
import sys

from ocrmac import ocrmac

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = pathlib.Path("/tmp/catalog-probe")
OUT_RAW = ROOT / "i18n_build" / "data" / "catalog_pilates_ocr.json"
OUT_MODELS = ROOT / "i18n_build" / "data" / "catalog_pilates_models.json"

RE_MATERIAL = re.compile(r"material\s*[:：]\s*(.+)", re.I)
RE_PACK = re.compile(r"packing\s*size\s*[:：]\s*(.*)", re.I)
RE_WEIGHT = re.compile(r"gross\s*weight\s*[:：]\s*(.+)", re.I)
RE_SIZE = re.compile(r"^\s*([A-D])\s*[:：]\s*(\d[\d\s*×x.,]*mm)", re.I)
RE_SIZE_BARE = re.compile(r"^\s*(\d[\d\s*×x.,]*mm)\s*$", re.I)

# 型号行判据（2026-09-26 修正）：画册用「系列名 + 编号 + 后缀」体系，不止 AL 一个前缀。
#   实测出现的前缀：AL / AL1 / Fold / Wood / Chair / Ladder Barre / Maple / OAK / metal
#                   / classics / Gyrotonic / Two-Way / Wall(-mounted) / Pilates
# 反例（不能当型号）：含冒号的都是规格行；含 mm 的是尺寸；纯数字是页码。
RE_MODEL_HEAD = re.compile(
    r"^(AL\d?|Fold|Wood|Chair|Ladder|Maple|OAK|Oak|metal|Metal|classics|Classics"
    r"|Gyrotonic|Two-Way|Wall|Pilates|Reformer|Cadillac)\b", re.I)
# ⚠️ 曾经把 `footbar\)$` 也列为反例 → 把 `AL1-B01 (Moving Footbar)` 整行误排除，
#    结果 p20 的两台（AL1-B01 / AL 2-B03）整条丢失。只有**纯括注行**才该排除。
RE_NOT_MODEL = re.compile(r"material|packing|gross|weight|^\(|mm\b", re.I)
# 「型号 (括注)」写法：AL1-B01 (Moving Footbar) / AL 2-B03 (No Moving Footbar)
RE_MODEL_NOTE = re.compile(r"^(?P<name>.+?)\s*\((?P<note>[^)]+)\)\s*$")


def ocr_page(img: pathlib.Path):
    res = ocrmac.OCR(str(img), language_preference=["en-US"]).recognize()
    rows = []
    for text, conf, box in res:
        # ocrmac 的 box 是 (x, y, w, h)，原点左下；转成「从上往下」的 y
        x, y, w, h = box
        rows.append({"text": text.strip(), "conf": round(float(conf), 3),
                     "x": round(x, 4), "y_top": round(1 - y - h, 4),
                     "w": round(w, 4), "h": round(h, 4)})
    rows.sort(key=lambda r: (r["y_top"], r["x"]))
    return rows


def _clean(name: str) -> str:
    """归一型号名：去掉 OCR 在连字符两侧多吃的空格，压掉重复空格。"""
    s = re.sub(r"\s*-\s*", "-", name)
    s = re.sub(r"\s+", " ", s).strip()
    return s


RE_PURE_CODE = re.compile(r"^\d{1,2}\s*(-\s*[A-Za-z0-9]+)?$")
RE_HAS_DIGIT = re.compile(r"\d")


def _split_bands(rows, gap=0.030):
    """按 y_top 切「行带」：相邻 y 差 > gap 即断带。"""
    bands, cur = [], []
    for r in rows:
        if cur and abs(r["y_top"] - cur[-1]["y_top"]) > gap:
            bands.append(cur)
            cur = []
        cur.append(r)
    if cur:
        bands.append(cur)
    return bands


def _split_columns(rows, gap=0.20):
    """整页按 x 聚类分「栏」：x 差 > gap 视为另一栏。

    页面排版实测是「上下两栏」与「左右并排」混用：
      · 左右并排：p35 `Ladder Barre 1-A`(x=.025) / `2-A`(x=.498)；p41 `Wall Tower`(.147) / `Wall-mounted`(.617)
      · 上下两栏：p28 `Wood 1-A`(y=.147) / `Wood 2-A`(y=.584)，两台文字 x 都在 .06 附近
    两种都能被「按 x 分栏 + 栏内按 y 顺序扫」正确处理；
    ⚠️ 反过来「先按 y 切行带」会失败 —— 型号行与它的 Material/Packing 行落在不同带，
       而带内只剩一栏的残行，会被挂到**另一栏**的块上（实测 p35 的 1-A 拿不到自己的规格）。
    """
    cols, cur = [], []
    for r in sorted(rows, key=lambda r: r["x"]):
        if cur and (r["x"] - cur[-1]["x"]) > gap:
            cols.append(cur)
            cur = []
        cur.append(r)
    if cur:
        cols.append(cur)
    return cols


def group_models(rows):
    """把 OCR 行聚成器械块：整页按 x 分栏 → 每栏内按 y 顺序扫 → 顺序开块。

    ⚠️ 一页常排 2 台（上下或左右），必须**每栏独立**扫描，
       否则右栏的型号行会挂到左栏那台下面（实测 p35/p36/p37/p39/p41 都会串）。
    """
    out = []
    cols = _split_columns(rows)
    for col in cols:
        col = sorted(col, key=lambda r: r["y_top"])
        # ⚠️ 「图上尺寸标注」必须先剔除：Gyrotonic 那页 (p40) 把 920mm / 1900mm / 1130mm
        #    / 2050mm / 1400mm 这些**标注线尺寸**散在图上，OCR 会当成裸尺寸行收进来。
        #    判据：同栏内若其后（y 更大）还存在 `Packing size:` 行，则该裸尺寸行是标注、丢弃。
        pack_y = [r["y_top"] for r in col if RE_PACK.match(r["text"])]
        first_pack = min(pack_y) if pack_y else 9.9

        for r in col:
            t = r["text"]
            if not t or re.fullmatch(r"\d{1,2}", t):
                continue
            is_model = (bool(RE_MODEL_HEAD.match(t)) and ":" not in t
                        and not RE_NOT_MODEL.search(t) and len(t) < 46)
            if is_model:
                # 型号名跨两行（"Two-Way" + "Ladder Reformer"）→ 合并同一块。
                # 条件：同栏、y 紧邻、且前一块型号里还没有数字（说明首行只是系列词）。
                if out and (r["y_top"] - out[-1]["y_top"]) < 0.075 \
                        and abs(r["x"] - out[-1]["x"]) < 0.15 \
                        and not RE_HAS_DIGIT.search(out[-1]["model"]):
                    out[-1]["model"] = _clean(out[-1]["model"] + " " + t)
                    out[-1]["lines"].append(t)
                    continue
                name, note = t, None
                mnote = RE_MODEL_NOTE.match(t)          # 「型号 (括注)」→ 拆开
                if mnote and not mnote.group("name").startswith("("):
                    name, note = mnote.group("name"), mnote.group("note")
                out.append({"model": _clean(name), "material": None, "packing": [],
                            "weight": None, "packing_raw": None, "weight_raw": None,
                            "note": note, "y_top": r["y_top"], "x": r["x"],
                            "conf": r["conf"], "lines": [t]})
                continue
            if not out:
                continue
            target = out[-1]
            target["lines"].append(t)
            # 纯编号续行（"Ladder Barre" + "19-F"）→ 补进型号名
            if RE_PURE_CODE.match(t) and not RE_HAS_DIGIT.search(target["model"]):
                target["model"] = _clean(target["model"] + " " + t)
                continue
            if re.match(r"^\(.*\)$", t):        # 括注 = 变体说明
                target["note"] = t.strip("()")
                continue
            m = RE_MATERIAL.match(t)
            if m:
                target["material"] = _clean(m.group(1)); continue
            m = RE_WEIGHT.match(t)
            if m:
                target["weight_raw"] = m.group(1).strip()
                w = re.search(r"([\d.]+)\s*kg", m.group(1), re.I)
                target["weight"] = float(w.group(1)) if w else None
                continue
            m = RE_PACK.match(t)
            if m:
                target["packing_raw"] = m.group(1).strip()
                s = RE_SIZE.match(m.group(1).strip())
                if s:
                    target["packing"].append([s.group(1).upper(),
                                              s.group(2).replace(" ", "")])
                continue
            s = RE_SIZE.match(t)
            if s:                               # 多行 A:/B: 写法
                target["packing"].append([s.group(1).upper(),
                                          s.group(2).replace(" ", "")])
                continue
            s = RE_SIZE_BARE.match(t)           # 裸尺寸行（无 Packing 标签）
            if s and not target["packing"] and r["y_top"] > first_pack:
                target["packing"].append(["-", s.group(1).replace(" ", "")])
    return out


def main():
    files = sorted(PAGES.glob("p*.png"))
    if not files:
        sys.exit("先跑 i18n_build/render_catalog_pages.py 生成 /tmp/catalog-probe/p*.png")
    raw, models = {}, []
    for img in files:
        n = int(img.stem[1:])
        rows = ocr_page(img)
        raw[str(n)] = rows
        ms = group_models(rows)
        for m in ms:
            m["page"] = n
        models.extend(ms)
        print("  p%-3d 行=%-3d 型号=%d  %s" % (n, len(rows), len(ms),
              " | ".join(m["model"] for m in ms)))

    OUT_RAW.write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")
    OUT_MODELS.write_text(json.dumps(models, ensure_ascii=False, indent=1), encoding="utf-8")

    print("\n=== 合计 %d 台器械 ===" % len(models))
    print("%-20s %-10s %-34s %s" % ("型号", "材质", "包装尺寸", "毛重kg"))
    for m in models:
        pk = " / ".join("%s:%s" % (a, b) for a, b in m["packing"]) or (m["packing_raw"] or "")
        print("%-20s %-10s %-34s %s" % (m["model"], m["material"] or "", pk[:34],
                                        m["weight"] if m["weight"] else ""))
    print("\n→ %s\n→ %s" % (OUT_RAW.relative_to(ROOT), OUT_MODELS.relative_to(ROOT)))


if __name__ == "__main__":
    main()
