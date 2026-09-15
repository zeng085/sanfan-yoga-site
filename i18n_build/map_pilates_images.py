# -*- coding: utf-8 -*-
"""按版面上图片的实际坐标，把价格表里的图自动归到对应型号行。

为什么不用 pypdf 的 page.images 顺序：那是资源字典序，不是视觉顺序；
也不能按「下一个编号的 y」划行，因为**图片在单元格里顶对齐、编号文字垂直居中**，
直接拿编号 y 当行边界会系统性错位一行。

做法：行边界取**相邻编号 y 的中点**，再把图片的纵向中心投进去。
另有两类噪声要剔除：
  1. 页码外残块（Excel 复制粘贴留下的，yc<0 或 >页高）
  2. 底图残留 —— 同一格里有 2 张图，偏上那张是旧的粘贴底图

    python3 i18n_build/map_pilates_images.py          # 生成映射并打印核对表
    python3 i18n_build/map_pilates_images.py --check  # 只看，不写文件
    python3 i18n_build/map_pilates_images.py --mark   # 出标注图到 /tmp/pl_marked/ 人工复核
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PDF = "/tmp/pilates_big.pdf"
OUT = os.path.join(HERE, "data", "pilates_image_map.json")
RAWDIR = "/tmp/pl_raw"
MARKDIR = "/tmp/pl_marked"

CODE_RE = re.compile(r"\b(NI[A-Z]\d{3}|NLH\d{3})\b")
MIN_SIDE = 40        # 版面上小于这个宽/高的图块是图标、条码，不算产品图（NIC202 在版面上只有 133x69pt，不能设太大）
DECOR_PAGES = 3      # 同一张图出现在 >=3 页 = 跨页复制粘贴的底图


def collect(doc, report):
    """返回 {key: {code,file,...}}，并把判定过程写进 report 供人工核对。"""
    xref_pages = {}
    for pi in range(len(doc)):
        for info in doc[pi].get_image_info(xrefs=True):
            x0, y0, x1, y1 = info["bbox"]
            if x1 - x0 < MIN_SIDE or y1 - y0 < MIN_SIDE:
                continue
            xref_pages.setdefault(info["xref"], set()).add(pi + 1)

    mapping = {}
    for pi in range(len(doc)):
        page = doc[pi]
        page_h = page.rect.height

        cands = []
        for info in page.get_image_info(xrefs=True):
            x0, y0, x1, y1 = info["bbox"]
            if x1 - x0 < MIN_SIDE or y1 - y0 < MIN_SIDE:
                continue
            yc = (y0 + y1) / 2
            if yc < 0 or yc > page_h:
                report.append({"page": pi + 1, "xref": info["xref"], "code": None,
                               "reason": "页面外残块", "y": round(yc)})
                continue
            cands.append({"xref": info["xref"], "bbox": (x0, y0, x1, y1),
                          "yc": yc, "w": info["width"], "h": info["height"]})

        anchors = []
        for blk in page.get_text("dict")["blocks"]:
            if blk.get("type") != 0:
                continue
            for line in blk["lines"]:
                for span in line["spans"]:
                    m = CODE_RE.search(span["text"])
                    if m:
                        anchors.append({"code": m.group(1),
                                        "y": (span["bbox"][1] + span["bbox"][3]) / 2})
        anchors.sort(key=lambda a: a["y"])
        if not anchors:
            for c in cands:
                report.append({"page": pi + 1, "xref": c["xref"], "code": None,
                               "reason": "本页无行锚点", "y": round(c["yc"])})
            continue

        for i, a in enumerate(anchors):
            a["lo"] = (-1e9 if i == 0
                       else (anchors[i - 1]["y"] + a["y"]) / 2)
            a["hi"] = ((a["y"] + anchors[i + 1]["y"]) / 2
                       if i + 1 < len(anchors) else 1e9)
            a["n"] = 0
        for c in cands:
            c["anchor"] = next((a for a in anchors if a["lo"] <= c["yc"] < a["hi"]), None)
            if c["anchor"]:
                c["anchor"]["n"] += 1

        for c in sorted(cands, key=lambda x: x["yc"]):
            a = c["anchor"]
            if not a:
                report.append({"page": pi + 1, "xref": c["xref"], "code": None,
                               "reason": "落在所有行之外", "y": round(c["yc"])})
                continue
            if a["n"] > 1 and len(xref_pages.get(c["xref"], ())) >= DECOR_PAGES:
                report.append({"page": pi + 1, "xref": c["xref"], "code": None,
                               "reason": "底图残留（同格已有真图）", "y": round(c["yc"])})
                continue
            ext = doc.extract_image(c["xref"])
            fn = "p%d_x%d.%s" % (pi + 1, c["xref"], ext["ext"])
            os.makedirs(RAWDIR, exist_ok=True)
            open(os.path.join(RAWDIR, fn), "wb").write(ext["image"])
            key = "p%d_x%d" % (pi + 1, c["xref"])
            mapping[key] = {"code": a["code"], "file": fn,
                            "w": ext["width"], "h": ext["height"],
                            "page": pi + 1, "y": round(c["yc"])}
            report.append({"page": pi + 1, "xref": c["xref"], "code": a["code"],
                           "file": fn, "y": round(c["yc"]),
                           "size": "%dx%d" % (ext["width"], ext["height"])})

    # ---- 跨页重复粘贴：同一张图出现在多页时，只保留最后一页那次 ----
    # Excel 分页会把下一行首图印在上一页页脚（例如 p4 底部混进稳踏椅、p5 底部混进梯桶），
    # 真身始终在「行真正所在的那一页」= 页码更大的那次。
    by_xref = {}
    for k, v in mapping.items():
        by_xref.setdefault(v["file"].split(".")[0].split("_x")[1], []).append(k)
    for xref, keys in by_xref.items():
        if len(keys) < 2:
            continue
        keys.sort(key=lambda k: mapping[k]["page"])
        for k in keys[:-1]:
            report.append({"page": mapping[k]["page"], "xref": int(xref), "code": None,
                           "reason": "跨页重复粘贴（真身在第 %d 页）"
                                     % mapping[keys[-1]]["page"],
                           "y": mapping[k]["y"]})
            del mapping[k]
    return mapping, report


def mark(doc, mapping):
    """在渲染页上把归属的型号编号画在每张图左上角，用于人工复核。"""
    import fitz
    os.makedirs(MARKDIR, exist_ok=True)
    bypage = {}
    for k, v in mapping.items():
        bypage.setdefault(v["page"], {})["x%d" % int(k.split("x")[1])] = v["code"]
    made = []
    for pi in range(len(doc)):
        page = doc[pi]
        for info in page.get_image_info(xrefs=True):
            x0, y0, x1, y1 = info["bbox"]
            tag = bypage.get(pi + 1, {}).get("x%d" % info["xref"])
            if not tag:
                continue
            page.draw_rect(fitz.Rect(x0, y0, x1, y1), color=(1, 0, 0), width=1.2)
            page.insert_text((x0 + 2, max(y0 - 2, 10)), tag,
                             fontsize=9, color=(1, 0, 0))
        out = os.path.join(MARKDIR, "p%d.png" % (pi + 1))
        page.get_pixmap(dpi=100).save(out)
        made.append(out)
        print("  %s" % out)
    return made


def main():
    import fitz
    doc = fitz.open(PDF)
    report = []
    mapping, report = collect(doc, report)

    print("图片归行结果（共 %d 张）" % len(mapping))
    for r in sorted(report, key=lambda x: (x["page"], x["y"])):
        print("  p%d y=%-5s %-12s %s" % (r["page"], r["y"], r["code"] or "—",
                                         r.get("size", r.get("reason", ""))))

    bycode = {}
    for k, v in mapping.items():
        bycode.setdefault(v["code"], []).append(k)
    print("\n按型号汇总（%d 款有图）：" % len(bycode))
    for c in sorted(bycode):
        print("  %-8s %d 张  %s" % (c, len(bycode[c]), sorted(bycode[c])))

    if "--mark" in sys.argv:
        print("\n标注图：")
        mark(doc, mapping)
    if "--check" not in sys.argv:
        json.dump(mapping, open(OUT, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print("\n已写 %s" % OUT)


if __name__ == "__main__":
    main()
