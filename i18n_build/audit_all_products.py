#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全站产品页全面体检 (2026-09-11)
检查维度:
 A 图片同步    : 与英文站 sanfansport.com 图集比对 (数量 / 内容)
 B 图片资产    : 文件缺失(裂图) / 宽高比非 1:1 / 过小图
 C 图片重复    : 跨产品页共用同一张图 (列表页"两卡同图"根因)
 D 元数据一致  : og:image / twitter:image / JSON-LD image 与首图是否一致且存在
 E 结构化数据  : JSON-LD 合法性 / 必备字段 / offers
 F 规格表      : 行数 (<=3 视为薄)
 G 多语言      : 6 语言版是否存在 / 图集数是否一致 / EN 标题是否一致
 H 站点引用    : products.html 卡片覆盖 / 站内是否有指向不存在页的链接
用法:
  python3 i18n_build/audit_all_products.py            # 全量
  python3 i18n_build/audit_all_products.py -v         # 打印明细
输出: outputs/全站产品体检报告-YYYY-MM-DD.md  +  .json
"""
import os, re, sys, json, glob, hashlib, datetime, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
LANGS = ["de", "ja", "ko", "fr", "it", "es"]
TODAY = datetime.date.today().isoformat()

CAT = {c["slug"]: c for c in json.load(open("outputs/sf_catalog_full.json", encoding="utf-8"))}
MAP = {}          # 我们的 slug -> 英文站 slug
for f in ("outputs/batch1_pages.json", "outputs/batch2_pages.json"):
    if os.path.exists(f):
        for p in json.load(open(f, encoding="utf-8")):
            MAP[p["new"]] = p["src"]
# 老页手工对照（家族页 / 汇总页）
MANUAL = {"ym1": "tpe-yoga-mat", "ym2": "tpe-yoga-mat-4", "ym3": "tpe-double-yoga-mat",
          "ym4": "folding-mat", "ym5": "pu-rubber-yoga-mat", "ym6": "matte-pu-rubber-yoga-mat",
          "ym7": "pu-rubber-yoga-mat-test",
          # 汇总类老页（fi/fr/pr/rb），依据规格逐项核对，与 dl_batch_images.py 一致
          "fr1": "foam-roller-2", "fr2": "foam-roller", "fr3": "vibrating-yoga-roller",
          "fr4": "eva-foam-roller", "fr5": "fascial-sphere-1",
          "pr1": "yoga-hammock", "pr3": "yoga-bolster", "pr4": "eva-yoga-block",
          "rb1": "exercise-bands", "rb2": "yoga-ball",
          "fi2": "kettlebell-2", "fi3": "jump-rope-2", "fi5": "dumbbell-2",
          "fi4": "stair-climbers-3",
          # fi1（迷你踏步机）英文站无对应产品 —— 无源，走 retire
          }
# 英文站确实无对应、计划下掉的页：不参与"未映射"计数
NO_SOURCE = {"fi1"}
MAP.update(MANUAL)


# ---------- helpers ----------
def read(p):
    try:
        return open(p, encoding="utf-8").read()
    except Exception:
        return ""


def gallery(src, rel_depth):
    """抽取图集 img src (去重保序)"""
    g = re.search(r'class="pd-gallery"(.*?)(?:</section>|</div>\s*</div>)', src, re.S)
    seg = g.group(1) if g else ""
    out = []
    for m in re.finditer(r'<img[^>]*src="([^"]+)"', seg):
        u = m.group(1).split("?")[0]
        if u not in out:
            out.append(u)
    # 归一化成相对站点根的路径 assets/img/xxx.webp
    norm = []
    for u in out:
        b = os.path.basename(u)
        norm.append("assets/img/" + b)
    return norm


def local_path(u):
    return os.path.join(ROOT, u.replace("../", ""))


def _size_nopil(p):
    """无 PIL 时的轻量尺寸解析（WebP VP8/VP8L/VP8X + PNG + JPEG）"""
    try:
        with open(p, "rb") as fh:
            head = fh.read(64)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            import struct
            w, h = struct.unpack(">II", head[16:24])
            return w, h
        if head[:2] == b"\xff\xd8":
            with open(p, "rb") as fh:
                fh.seek(2)
                while True:
                    b = fh.read(1)
                    if not b:
                        return 0, 0
                    if b != b"\xff":
                        continue
                    while b == b"\xff":
                        b = fh.read(1)
                    m = b[0]
                    if m in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                             0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                        fh.seek(3, 1)
                        h, w = struct.unpack(">HH", fh.read(4))
                        return w, h
                    ln = struct.unpack(">H", fh.read(2))[0]
                    fh.seek(ln - 2, 1)
        if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
            import struct
            fmt = head[12:16]
            if fmt == b"VP8 ":
                w = struct.unpack("<H", head[26:28])[0] & 0x3FFF
                h = struct.unpack("<H", head[28:30])[0] & 0x3FFF
                return w, h
            if fmt == b"VP8L":
                b = head[21:26]
                bits = int.from_bytes(b, "little")
                return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
            if fmt == b"VP8X":
                w = int.from_bytes(head[24:27], "little") + 1
                h = int.from_bytes(head[27:30], "little") + 1
                return w, h
    except Exception:
        pass
    return 0, 0


_cache = {}


def pil_info(u):
    """返回 (exists, w, h)"""
    if u in _cache:
        return _cache[u]
    p = local_path(u)
    r = (False, 0, 0)
    if os.path.exists(p):
        ok = False
        w = h = 0
        try:
            from PIL import Image
            with Image.open(p) as im:
                w, h = im.size
                ok = True
        except Exception:
            w, h = _size_nopil(p)
            ok = bool(w and h)
        # 文件存在就算资产存在，尺寸拿不到不算裂图
        r = (True, w, h) if ok else (True, 0, 0)
    _cache[u] = r
    return r


def jsonld_blocks(src):
    out = []
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', src, re.S):
        try:
            out.append(json.loads(m.group(1).strip()))
        except Exception as e:
            out.append({"__error__": str(e)})
    return out


def spec_rows(src):
    m = re.search(r'class="spec-table"(.*?)</table>', src, re.S)
    if not m:
        m = re.search(r"<table(.*?)</table>", src, re.S)
    return len(re.findall(r"<tr", m.group(1))) if m else 0


def h1_en(src):
    m = re.search(r'<h1[^>]*>(.*?)</h1>', src, re.S)
    if not m:
        return ""
    e = re.search(r'class="lang-en"[^>]*>(.*?)</span>', m.group(1), re.S)
    return re.sub(r"\s+", " ", e.group(1)).strip() if e else ""


def meta_img(src, prop):
    m = re.search(r'<meta (?:property|name)="%s" content="([^"]+)"' % prop, src)
    return m.group(1).split("?")[0] if m else ""


issues = collections.defaultdict(list)   # page -> [issues]
audit = []

# ---------- 主循环 ----------
for f in sorted(glob.glob("products/*.html")):
    slug = os.path.basename(f)[:-5]
    s = read(f)
    row = {"slug": slug, "path": f, "src": MAP.get(slug, "")}
    imgs = gallery(s, rel_depth=1)
    row["imgs"] = imgs
    row["n_img"] = len(imgs)
    row["h1_en"] = h1_en(s)
    row["spec_rows"] = spec_rows(s)

    # A 图片同步
    en = CAT.get(row["src"], {})
    row["en_imgs"] = len(en.get("images", []))
    row["sync_state"] = "unknown"
    if slug in NO_SOURCE:
        row["sync_state"] = "no-source"
        issues[slug].append(("A-无源", "英文站无对应产品，计划下掉该页"))
    elif not row["src"]:
        row["sync_state"] = "unmapped"
        issues[slug].append(("A-未映射", "该页未建立英文站对照，图片/规格来源未知"))
    elif not en:
        row["sync_state"] = "src-missing"
        issues[slug].append(("A-源缺失", "对照的英文站 slug %s 已不存在" % row["src"]))
    else:
        gap = len(en.get("images", [])) - len(imgs)
        if len(imgs) == 0:
            row["sync_state"] = "empty"
            issues[slug].append(("A-无图", "图集为空"))
        elif gap > 0:
            row["sync_state"] = "partial(%d/%d)" % (len(imgs), len(en["images"]))
            issues[slug].append(("A-图集不全", "英文站 %d 张，本页仅 %d 张，缺 %d 张"
                                 % (len(en["images"]), len(imgs), gap)))
        else:
            row["sync_state"] = "ok"

    # B 图片资产
    missing = []
    odd_ratio = []
    small = []
    for u in imgs:
        ex, w, h = pil_info(u)
        if not ex:
            missing.append(u)
        else:
            if w and h and abs(w - h) / max(w, h) > 0.02:
                odd_ratio.append("%s (%dx%d)" % (os.path.basename(u), w, h))
            if max(w, h) < 500:
                small.append("%s (%dx%d)" % (os.path.basename(u), w, h))
    row["missing"] = missing
    row["odd_ratio"] = odd_ratio
    row["small"] = small
    if missing:
        issues[slug].append(("B-裂图", "图片文件缺失: " + ", ".join(os.path.basename(x) for x in missing)))
    if odd_ratio:
        issues[slug].append(("B-非方图", "图片非 1:1，若容器为 1/1 会留白/裁切: " + "; ".join(odd_ratio[:6])))
    if small:
        issues[slug].append(("B-小图", "图片短边 <500px: " + "; ".join(small[:6])))

    # D 元数据一致
    og = meta_img(s, "og:image")
    tw = meta_img(s, "twitter:image")
    row["og"] = og
    if imgs:
        first = imgs[0]
        if og and os.path.basename(og) != os.path.basename(first):
            issues[slug].append(("D-og不一致", "og:image=%s 与首图 %s 不一致" % (og, first)))
        if tw and og and os.path.basename(tw) != os.path.basename(og):
            issues[slug].append(("D-tw不一致", "twitter:image 与 og:image 不一致"))
        if og and not os.path.exists(local_path("assets/img/" + os.path.basename(og))):
            issues[slug].append(("D-og裂", "og:image 文件不存在: " + og))

    lds = jsonld_blocks(s)
    err = [b for b in lds if "__error__" in b]
    if err:
        issues[slug].append(("E-JSONLD非法", err[0]["__error__"]))
    prod = None
    for b in lds:
        if isinstance(b, dict) and b.get("@type") == "Product":
            prod = b
            break
        if isinstance(b, dict) and isinstance(b.get("@graph"), list):
            for x in b["@graph"]:
                if isinstance(x, dict) and x.get("@type") == "Product":
                    prod = x
    row["has_product_ld"] = bool(prod)
    if prod:
        row["ld_imgs"] = len(prod.get("image", []) or [])
        if isinstance(prod.get("image"), str):
            row["ld_imgs"] = 1
        if imgs and row["ld_imgs"] != len(imgs):
            issues[slug].append(("E-image不符", "JSON-LD image %d 条 vs 图集 %d 张" % (row["ld_imgs"], len(imgs))))
        of = prod.get("offers")
        if not of:
            issues[slug].append(("E-无offers", "Product 无 offers 字段"))
        else:
            lo, hi = of.get("lowPrice"), of.get("highPrice")
            row["price"] = (lo, hi, of.get("priceCurrency"))
            if not lo or not hi:
                issues[slug].append(("E-offers缺价", "AggregateOffer 缺 lowPrice/highPrice"))
        if not prod.get("name"):
            issues[slug].append(("E-无name", "Product 缺 name"))
        bc = None
        for b in lds:
            if isinstance(b, dict) and b.get("@type") == "BreadcrumbList":
                bc = b
            elif isinstance(b, dict) and isinstance(b.get("@graph"), list):
                for x in b["@graph"]:
                    if isinstance(x, dict) and x.get("@type") == "BreadcrumbList":
                        bc = x
        if not bc:
            issues[slug].append(("E-无面包屑", "缺 BreadcrumbList"))
    else:
        issues[slug].append(("E-无Product", "页面缺少 Product JSON-LD"))
    row["n_ld"] = len(lds)

    # F 规格
    if row["spec_rows"] <= 3 and row["spec_rows"] > 0:
        issues[slug].append(("F-规格薄", "规格表仅 %d 行" % row["spec_rows"]))
    elif row["spec_rows"] == 0:
        issues[slug].append(("F-无规格", "页面没有规格表"))

    # G 多语言
    lang_info = {}
    for L in LANGS:
        lf = "%s/products/%s.html" % (L, slug)
        if not os.path.exists(lf):
            lang_info[L] = "missing"
            continue
        ls = read(lf)
        lg = gallery(ls, rel_depth=2)
        lang_info[L] = len(lg)
        if lg and imgs and os.path.basename(lg[0]) != os.path.basename(imgs[0]):
            issues[slug].append(("G-首图不一致", "%s 版首图 %s != 根站 %s" % (L, os.path.basename(lg[0]), os.path.basename(imgs[0]))))
    row["langs"] = lang_info
    nmiss = [L for L, v in lang_info.items() if v == "missing"]
    if nmiss:
        issues[slug].append(("G-缺语言", "缺语言页: " + ",".join(nmiss)))
    nums = {v for v in lang_info.values() if isinstance(v, int)}
    if len(nums) > 1 and (max(nums) - min(nums)) > 0 and len(imgs) > 1:
        issues[slug].append(("G-图数不齐", "语言版图集数不一致: %s vs 根站 %d" % (lang_info, len(imgs))))

    audit.append(row)

# ---------- C 跨页重复图 ----------
first_map = collections.defaultdict(list)
all_map = collections.defaultdict(list)
for r in audit:
    if r["imgs"]:
        first_map[r["imgs"][0]].append(r["slug"])
    for u in set(r["imgs"]):
        all_map[u].append(r["slug"])
dup_first = {k: v for k, v in first_map.items() if len(v) > 1}
dup_any = {k: v for k, v in all_map.items() if len(v) > 1}
for k, v in dup_first.items():
    for s_ in v:
        issues[s_].append(("C-首图撞车", "首图 %s 被 %d 个产品页共用: %s" % (os.path.basename(k), len(v), ",".join(v))))

# ---------- H 站点引用 ----------
have = {r["slug"] for r in audit}


def scan_cards(page_path):
    """扫一个列表/首页里的所有产品卡，返回 {slug: 卡图文件名}"""
    if not os.path.exists(page_path):
        return {}
    h = read(page_path)
    out = {}
    for m in re.finditer(r'<a[^>]*href="((?:\.\./)*(?:products/)?)([a-z0-9-]+)\.html"[^>]*>([\s\S]*?)</a>', h):
        slug = m.group(2)
        if slug not in have:
            continue
        im = re.search(r'<img[^>]*src="([^"]+)"', m.group(3))
        if im and slug not in out:
            out[slug] = im.group(1).split("?")[0].split("/")[-1]
    return out


card_sources = {"(root) index.html": "index.html"}
# 8 个分类页：产品列表已从 products.html 拆出，卡片一致性要对分类页查
CAT_KEYS = ["tpe-yoga-mats", "pu-rubber-yoga-mats", "suede-cork-yoga-mats",
            "meditation-pilates-mats", "foam-rollers", "massage-recovery",
            "resistance-bands", "yoga-props-accessories"]
for k in CAT_KEYS:
    card_sources["(root) %s.html" % k] = "%s.html" % k
for L in LANGS:
    card_sources[f"{L}/index.html"] = "%s/index.html" % L
    card_sources[f"{L}/products.html"] = "%s/products.html" % L

for label, path in card_sources.items():
    cm = scan_cards(path)
    for slug, img in cm.items():
        r = next((x for x in audit if x["slug"] == slug), None)
        if r and r["imgs"] and os.path.basename(r["imgs"][0]) != img:
            issues[slug].append(("H-卡片图不一致", "%s 的卡片用 %s，产品页首图是 %s"
                                 % (label, img, os.path.basename(r["imgs"][0]))))

# 覆盖检查：每个产品页都必须出现在某个分类页里（否则就是从导航里掉了）
cards = set()
for k in CAT_KEYS:
    p = "%s.html" % k
    if os.path.exists(p):
        for m in re.finditer(r'href="(products/[^"#?]+\.html)"', read(p)):
            cards.add(os.path.basename(m.group(1))[:-5])
have = {r["slug"] for r in audit}
not_in_list = sorted(have - cards)
ghost_card = sorted(cards - have)
allhtml = [p for p in glob.glob("*.html") + glob.glob("*/*.html") + glob.glob("*/*/*.html")]
dead = set()
for p in allhtml:
    s = read(p)
    depth = p.count("/")
    for m in re.finditer(r'href="((?:\.\./)*products/[^"#?]+\.html)"', s):
        t = m.group(1)
        # 相对转绝对
        if depth >= 1 and t.startswith("products/"):
            t = "../" * depth + t
        tgt = os.path.normpath(os.path.join(os.path.dirname(p), t))
        if not os.path.exists(tgt):
            dead.add((p, m.group(1)))

# ---------- 输出 ----------
order = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4, "F": 5, "G": 6, "H": 7}
total_pages = len(audit)
bad_pages = {k: v for k, v in issues.items() if v}
cnt = collections.Counter()
for k, v in issues.items():
    for tag, _ in v:
        cnt[tag.split("-")[0]] += 1

lines = []
lines.append("# 全站产品页体检报告 %s\n" % TODAY)
lines.append("> 覆盖 %d 个产品页（根站 products/*.html），比对源：英文站 sanfansport.com REST 采集 167 个产品\n" % total_pages)
lines.append("## 一、总览\n")
lines.append("| 指标 | 数值 |")
lines.append("|---|---|")
lines.append("| 产品页总数 | %d |" % total_pages)
lines.append("| 有问题页数 | %d |" % len(bad_pages))
lines.append("| 完全通过页数 | %d |" % (total_pages - len(bad_pages)))
lines.append("| 图片完全同步(数量一致) | %d |" % sum(1 for r in audit if r["sync_state"] == "ok"))
lines.append("| 图集不全 | %d |" % sum(1 for r in audit if r["sync_state"].startswith("partial")))
lines.append("| 未映射英文站 | %d |" % sum(1 for r in audit if r["sync_state"] == "unmapped"))
lines.append("| 英文站无源（计划下掉） | %d |" % sum(1 for r in audit if r["sync_state"] == "no-source"))
lines.append("| 图片总计 | %d |" % sum(r["n_img"] for r in audit))
lines.append("| 首图撞车页数 | %d |" % sum(len(v) for v in dup_first.values()))
lines.append("| 卡片图与产品页首图不一致 | %d |" % cnt.get("H", 0))
lines.append("| 缺语言页(6语) | %d |" % sum(1 for r in audit if "missing" in r["langs"].values()))
lines.append("| 未出现在分类页 | %d |" % len(not_in_list))
lines.append("| 站内指向不存在产品页的链接 | %d |" % len(dead))
lines.append("")
lines.append("### 问题类别分布\n")
lines.append("| 类别 | 页次 |")
lines.append("|---|---|")
for k in sorted(cnt, key=lambda x: order[x]):
    lines.append("| %s | %d |" % (k, cnt[k]))
lines.append("")

# 明细按类别
lines.append("## 二、A 图片同步（vs 英文站）\n")
lines.append("| 产品页 | 状态 | 本页图数 | 英文站图数 | 英文站 slug |")
lines.append("|---|---|---|---|---|")
for r in sorted(audit, key=lambda x: -(x["en_imgs"] - x["n_img"])):
    if r["sync_state"] in ("ok",):
        continue
    lines.append("| %s | %s | %d | %s | %s |" % (
        r["slug"], r["sync_state"], r["n_img"],
        r["en_imgs"] if r["src"] else "-", r["src"] or "-"))
lines.append("")

lines.append("## 三、C 跨页重复图\n")
if dup_first:
    lines.append("### 首图撞车（列表页会显示两卡同图）\n")
    lines.append("| 图片 | 共用页数 | 产品页 |")
    lines.append("|---|---|---|")
    for k, v in sorted(dup_first.items(), key=lambda x: -len(x[1])):
        lines.append("| %s | %d | %s |" % (os.path.basename(k), len(v), ", ".join(v)))
    lines.append("")
else:
    lines.append("无\n")

lines.append("## 四、逐页问题明细\n")
for r in sorted(audit, key=lambda x: x["slug"]):
    v = issues.get(r["slug"], [])
    lines.append("### %s\n" % r["slug"])
    lines.append("- 英文站对照：`%s` ｜ 图集 %d 张 ｜ 规格 %d 行 ｜ 首图 `%s` ｜ 语言 %s\n" % (
        r["src"] or "—", r["n_img"], r["spec_rows"],
        os.path.basename(r["imgs"][0]) if r["imgs"] else "—",
        "".join((L[0].upper() + ("✓" if x != "missing" else "✗")) for L, x in r["langs"].items())))
    if not v:
        lines.append("- ✅ 无问题\n")
    else:
        for tag, msg in sorted(v, key=lambda x: (order.get(x[0][0], 9), x[0])):
            lines.append("- **%s** — %s" % (tag, msg))
    lines.append("")

lines.append("## 五、站点级问题\n")
lines.append("### 未出现在分类页的产品（导航漏项）\n")
lines.append(", ".join(not_in_list) if not_in_list else "无")
lines.append("\n### 分类页中指向不存在页面的卡片（幽灵卡）\n")
lines.append(", ".join(ghost_card) if ghost_card else "无")
lines.append("\n### 站内指向不存在产品页的链接\n")
if dead:
    byk = collections.defaultdict(list)
    for p, t in dead:
        byk[t].append(p)
    lines.append("| 目标 | 来源页 |")
    lines.append("|---|---|")
    for t, ps_ in sorted(byk.items()):
        lines.append("| `%s` | %s |" % (t, ", ".join(sorted(ps_)[:6])))
else:
    lines.append("无")
lines.append("")

md = "\n".join(lines)
out_md = "outputs/全站产品体检报告-%s.md" % TODAY
out_js = "outputs/全站产品体检报告-%s.json" % TODAY
open(out_md, "w", encoding="utf-8").write(md)
json.dump({"pages": audit, "issues": {k: v for k, v in issues.items()},
           "dup_first": {k: v for k, v in dup_first.items()},
           "dup_any": {k: v for k, v in dup_any.items()},
           "not_in_list": not_in_list, "ghost_card": ghost_card,
           "dead_links": sorted(list(dead))},
          open(out_js, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(md[:4000])
print("\n=== 写入 ===\n%s\n%s" % (out_md, out_js))
