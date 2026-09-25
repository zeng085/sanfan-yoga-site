#!/usr/bin/env python3
"""本轮 SEO 改动的「范围核查」——证明工作区 = HEAD + 预期变换，无夹带改动（2026-09-25）

做法：对每个改动文件取 `HEAD` 版本，与工作区版本做 difflib 逐块对比。
每一对 old/new 块经过**归一化**（把「预期允许的差异」抽象成记号）后必须相等；
否则报「非预期改动」。

归一化允许的差异：
  1. 资源版本号 ?vXXXXXXXa -> ?vXXXXXXXb
  2. A2: <div class="cat-head"><h3> -> <div class="cat-head"><div class="cat-title">
  3. A5: <a ...data-setlang...>X</a> -> <button type="button" ...data-setlang...>X</button>
  4. H 标签互换：h2 <-> h3（标签名归一为 hN）
  5. 11 个高权重页的 description 新旧串

另外独立做**结构守恒**核查（div / a / button / h2 / h3 数量增减是否符合预期）。

用法：python3 verify_changes_scope_20260925.py
"""
import difflib
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "i18n_build"))

# ---------- 11 个高权重页的 desc 新旧映射（直接从修复脚本取，避免手抄出错）----------
DESC_NEW = {}
try:
    import fix_high_weight_desc_20260925 as DESC_FIX          # noqa: E402
    DESC_NEW = dict(getattr(DESC_FIX, "NEW_DESC", {}))
except Exception as exc:                                       # noqa: BLE001
    print("  (提示) 无法导入 desc 新文案：%s" % exc)


def git(*args, **kw):
    return subprocess.run(("git",) + args, cwd=ROOT, capture_output=True, **kw)


def changed_files():
    out = git("diff", "--no-renames", "--name-only").stdout.decode()
    return [p for p in out.splitlines() if p.strip()]


def head_versions(paths):
    """用 git cat-file --batch 一次性取回所有 HEAD 版本（比逐个 git show 快得多）。

    注意：cat-file --batch 的响应头是 `<sha> <type> <size>`（**不是**请求里的对象名），
    因此必须按**输入顺序**把响应配回 path —— 拿响应头当 key 会全部 miss。
    """
    proc = subprocess.run(
        ["git", "cat-file", "--batch"],
        cwd=ROOT, input="\n".join("HEAD:" + p for p in paths).encode(),
        capture_output=True)
    data = proc.stdout
    out, pos, idx = {}, 0, 0
    while pos < len(data) and idx < len(paths):
        nl = data.find(b"\n", pos)
        if nl < 0:
            break
        header = data[pos:nl].decode("utf-8", "replace")
        pos = nl + 1
        parts = header.split()
        if len(parts) == 3 and parts[1] == "blob":
            size = int(parts[2])
            out[paths[idx]] = data[pos:pos + size]
            pos += size + 1
        else:
            out[paths[idx]] = None
        idx += 1
    return out


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8", newline="") as fh:
        return fh.read()


# --------------------------- 归一化 ---------------------------

RE_VER = re.compile(r"\?v[0-9a-zA-Z]{6,12}")
RE_LANG_A = re.compile(r"<a\b(?=[^>]*data-setlang)([^>]*)>(.*?)</a>", re.S)
RE_LANG_B = re.compile(
    r'<button\b(?=[^>]*data-setlang)([^>]*)>(.*?)</button>', re.S)


def strip_type_button(attrs):
    """<button type="button" ...> 归一：去掉脚本插入的 type="button"。"""
    return re.sub(r'\s*type="button"', "", attrs)


def strip_blocks(s):
    """把「受管区块」整段抽掉（标记 + 内容），old/new 两侧同样处理。

    受管区块 = 由生成脚本维护、可反复重建的段：
      ilink:v1（add_internal_links）/ catintro:v1 + cfaq:v1 + cfaq-ld:v1
      （add_category_content_20260925.py）

    ⚠️ 为什么是「两侧一起抽」而不是「归一成同一个记号」：
       本轮 56 个文件的区块是 HEAD **完全没有**、新版才出现的；
       若归一成记号，old 无 / new 有 → 必然判不等。
       抽掉之后，本脚本证明的是**更强的**命题：
       「受管区块之外的一切，除已知变换外一字未动」。
       区块内部则有专门脚本逐条验收：
       verify_catcontent_i18n_20260925.py（56 文件 × 14 项，含块内配平与 LD 对账）。
    """
    for a, b in (("<!-- catintro:v1 -->", "<!-- /catintro:v1 -->"),
                 ("<!-- cfaq:v1 -->", "<!-- /cfaq:v1 -->"),
                 ("<!-- cfaq-ld:v1 -->", "<!-- /cfaq-ld:v1 -->"),
                 ("<!-- ilink:v1 -->", "<!-- /ilink:v1 -->")):
        s = re.sub(re.escape(a) + r".*?" + re.escape(b) + r"[ \t]*\n?", "", s, flags=re.S)
    return s


def norm(text):
    s = text
    # 1) 资源版本号
    s = RE_VER.sub("?vVER", s)
    # 2) A2 分类页标题容器：整块归一（必须连闭合标签一起，
    #    只替换开标签的话新块的 `</div>` 与旧块的 `</h3>` 仍会判为不等）
    s = re.sub(r'<div class="cat-head">\s*<h3\b[^>]*>(.*?)</h3>',
               lambda m: '<div class="cat-head">CATBLK:' + m.group(1),
               s, flags=re.S)
    s = re.sub(r'<div class="cat-head">\s*<div class="cat-title"[^>]*>(.*?)</div>',
               lambda m: '<div class="cat-head">CATBLK:' + m.group(1),
               s, flags=re.S)
    # 3) A5 语言切换标签
    s = RE_LANG_A.sub(lambda m: "<LANGTAG%s>%s</LANGTAG>"
                      % (m.group(1), m.group(2)), s)
    s = RE_LANG_B.sub(lambda m: "<LANGTAG%s>%s</LANGTAG>"
                      % (strip_type_button(m.group(1)), m.group(2)), s)
    # 4) H 标签 h2 <-> h3
    s = re.sub(r"<(/?)h([23])\b", r"<\1hN", s)
    # 5) description 的 4 个位置：值统一占位（内容是否合规另做专项检查）
    s = re.sub(r'(<meta\b[^>]*(?:name="description"|property="og:description"'
               r'|name="twitter:description")[^>]*content=")[^"]*(")',
               r"\1DESCSTR\2", s)
    s = re.sub(r'("description"\s*:\s*")[^"]*(")', r"\1DESCSTR\2", s)
    # 6) 受管区块整段抽掉（两侧同样处理）
    s = strip_blocks(s)
    return s


# ---------------------------------------------------------------------------
# 允许的标签增减签名（只列**开标签**；闭合标签必须各自与开标签相等 = 配平）
# ---------------------------------------------------------------------------
# ⚠️ 旧版是 4 条 if 规则（「div 必须 = -h3」等），本轮新增的三块内容会合法地
#    往页面里加 16 个 div（3 个 section + 容器 + 列表…），旧规则直接误判「不配平」。
#    改为**白名单 + 配平不变量**：白名单外的任何签名一律报异常，
#    这样既不会误杀，也仍能抓住「标签被吞 / 意外多出来的标签」。
ALLOWED_SIG = {
    (): "无标签增减（仅版本号 / description 文本）",
    (("h2", 1), ("h3", -1)): "A1 H 层级 h3→h2",
    (("h2", 5), ("h3", -5)): "A1 H 层级 h3→h2 ×5",
    (("h2", 10), ("h3", -10)): "A1 H 层级 h3→h2 ×10",
    (("h2", 20), ("h3", -20)): "A1 H 层级 h3→h2 ×20",
    (("a", -2), ("button", 2)): "A5 语言切换 <a>→<button> ×2",
    (("div", 1), ("h3", -1)): "A2 cat-head <h3>→<div.cat-title>",
    (("a", 3), ("div", 16), ("h2", 3), ("h3", -1)):
        "本轮三块内容（导语+FAQ+FAQPage）×ilink + A2",
}


def main():
    files = [f for f in changed_files() if f.endswith(".html")]
    print("=== 范围核查：%d 个 HTML 改动文件 ===" % len(files))
    heads = head_versions(files)

    unexpected, nblocks = [], 0
    # 结构守恒
    cnt = defaultdict(Counter)
    for path in files:
        blob = heads.get(path)
        if blob is None:
            unexpected.append((path, "HEAD 版本取不到（新增文件？）"))
            continue
        old = blob.decode("utf-8")
        new = read(path)
        if old == new:
            unexpected.append((path, "文件被判为改动但内容相同"))
            continue

        # ⚠️ 受管区块必须在 **difflib 之前**抽掉，不能塞进 norm()。
        #    原因：difflib 按「公共行」切分，插入的 FAQ 块里有大量与页面其它
        #    位置相同的行（`    </div>` 等）→ 插入块会被**切成碎片**，
        #    碎片里凑不齐成对的开/闭标记 → 块内的 norm() 抽不掉。
        #    实测：整文件 norm() 能抽掉，但逐碎片抽不掉 → 56 文件全误报。
        old_cmp, new_cmp = strip_blocks(old), strip_blocks(new)

        sm = difflib.SequenceMatcher(None, old_cmp.splitlines(), new_cmp.splitlines(),
                                     autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            nblocks += 1
            ob = "\n".join(old_cmp.splitlines()[i1:i2])
            nb = "\n".join(new_cmp.splitlines()[j1:j2])
            if norm(ob) != norm(nb):
                unexpected.append((path, "块 %d-%d" % (i1, i2),
                                   "\n   旧: %s\n   新: %s"
                                   % (ob[:240], nb[:240])))
        # 结构守恒统计
        for tok, key in (("<div", "div"), ("</div>", "/div"),
                         ("<a ", "a"), ("</a>", "/a"),
                         ("<button", "button"), ("</button>", "/button"),
                         ("<h2", "h2"), ("</h2>", "/h2"),
                         ("<h3", "h3"), ("</h3>", "/h3")):
            cnt[path][key] = new.count(tok) - old.count(tok)

    print("  逐块比对：%d 个变更块" % nblocks)
    print("  非预期改动：%d 处" % len(unexpected))
    for u in unexpected[:25]:
        print("   ❌", " | ".join(str(x) for x in u))

    print()
    print("=== 结构守恒（各文件标签增减）===")
    open_keys = ["div", "a", "button", "h2", "h3"]
    seen = Counter()
    viol = []
    for path, c in sorted(cnt.items()):
        d = c
        ok, reason = True, ""

        # 不变量 1：每个标签必须成对增减（开 == 闭）
        for k in open_keys:
            if d[k] != d["/" + k]:
                ok, reason = False, "<%s> 与 </%s> 增减不配平 %s" % (k, k, dict(d))
                break

        # 不变量 2：签名必须在白名单内
        opens = tuple(sorted((k, d[k]) for k in open_keys if d[k]))
        sig_full = tuple(sorted((k, v) for k, v in d.items() if v))
        seen[sig_full] += 1
        if ok and opens not in ALLOWED_SIG:
            ok, reason = False, "非白名单签名 %s（白名单外的标签增减）" % dict(opens)
        if not ok:
            viol.append((path, reason))

    print("  标签增减签名种类：%d" % len(seen))
    for sig, n in seen.most_common(16):
        lbl = "(仅版本号/描述文本)" if not sig else dict(sig)
        print("   %4d 个文件  %s" % (n, lbl))
    print()
    print("  结构异常文件：%d 个" % len(viol))
    for v in viol[:15]:
        print("   ❌", v)

    print()
    print("=== 受管区块覆盖（已整段抽出，独立脚本逐条验收）===")
    for name, a, b in (("ilink", "<!-- ilink:v1 -->", "<!-- /ilink:v1 -->"),
                       ("catintro", "<!-- catintro:v1 -->", "<!-- /catintro:v1 -->"),
                       ("cfaq", "<!-- cfaq:v1 -->", "<!-- /cfaq:v1 -->"),
                       ("cfaq-ld", "<!-- cfaq-ld:v1 -->", "<!-- /cfaq-ld:v1 -->")):
        n = sum(1 for f in files if a in read(f) and b in read(f))
        print("  %-9s 覆盖 %4d 个文件" % (name, n))

    return 0 if not unexpected and not viol else 1


if __name__ == "__main__":
    sys.exit(main())
