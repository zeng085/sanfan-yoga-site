# -*- coding: utf-8 -*-
"""把已核对好的型号映射转成站内 WebP 素材。

输入：i18n_build/data/pilates_image_map.json（map_pilates_images.py 产出，已人工核对）
      i18n_build/data/pilates_models.json（型号库）
输出：assets/img/<family>-<n>.webp  +  i18n_build/data/pilates_images.json（型号→文件）

规格：最长边 900px、WebP q75、method=6（与站内既有约定一致）。

    python3 i18n_build/pilates_images.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IMG = os.path.join(ROOT, "assets", "img")
RAWDIR = "/tmp/pl_raw"
MAP = os.path.join(HERE, "data", "pilates_image_map.json")
MODELS = os.path.join(HERE, "data", "pilates_models.json")
OUT = os.path.join(HERE, "data", "pilates_images.json")

MAX_EDGE = 900
QUALITY = 75


def main():
    from PIL import Image
    mp = json.load(open(MAP, encoding="utf-8"))
    data = json.load(open(MODELS, encoding="utf-8"))

    # 型号 → 它在 PDF 里的页码（NIC201 有两个变体，靠页码区分澳版/欧版）
    def find_key(code, page):
        hits = [k for k, v in mp.items()
                if v["code"] == code and (page is None or v["page"] == page)]
        if hits:
            return hits[0]
        hits = [k for k, v in mp.items() if v["code"] == code]
        return hits[0] if hits else None

    written, missing = [], []
    for f in data["families"]:
        n = 0
        for m in f["models"]:
            key = find_key(m["code"], m["src_page"])
            if not key:
                missing.append(m["code"])
                continue
            n += 1
            dst_name = "%s-%d.webp" % (f["key"], n)
            dst = os.path.join(IMG, dst_name)
            im = Image.open(os.path.join(RAWDIR, mp[key]["file"])).convert("RGB")
            w, h = im.size
            if max(w, h) > MAX_EDGE:
                s = MAX_EDGE / max(w, h)
                im = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
            im.save(dst, "WEBP", quality=QUALITY, method=6)
            written.append({"code": m["code"], "variant": m["variant"],
                            "family": f["key"], "file": dst_name,
                            "src": key, "size": list(im.size),
                            "kb": os.path.getsize(dst) // 1024})
        print("  %-24s %2d 张" % (f["key"], n))

    json.dump(written, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n落站 %d 张 → assets/img/" % len(written))
    if missing:
        print("⚠️ 无图型号:", missing)
    tot = sum(w["kb"] for w in written)
    print("合计 %.1f MB | 单张均 %.0f KB" % (tot / 1024, tot / max(len(written), 1)))


if __name__ == "__main__":
    main()
