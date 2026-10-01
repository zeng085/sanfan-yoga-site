#!/usr/bin/env python3
"""改写 7 个普拉提页的超长 meta description（≤155 显示宽，纯 ASCII 即字符数）。

同一字符串在页面里出现 3 处：name=description / property=og:description /
name=twitter:description → 每页断言恰好命中 3 次，不多不少。
HTML-only 改动：不 bump 版本号（CSS/JS 未变）。
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REWRITES = {
    "pilates/pilates-reformer.html": (
        "Pilates Reformer made to order: 46 models across three lines — aluminium, foldable and solid timber. Packed size and gross weight for every model. OEM/ODM with your logo, colour and material spec. Request a quote.",
        "Custom Pilates Reformer OEM/ODM: 46 models in aluminium, foldable & solid wood, with packed size and gross weight for every model. Request a quote.",
    ),
    "pilates/pilates-spine-corrector.html": (
        "Pilates Spine Corrector built to your drawing. The 2026 catalogue has no fixed range, so we quote per build — send a drawing, photo or sample. OEM/ODM with your logo, colour and material spec. Request a quote.",
        "Custom Pilates Spine Corrector OEM/ODM: built to your drawing — send a drawing, photo or sample for a per-build quote. Request a quote.",
    ),
    "pilates/pilates-reformer-tower.html": (
        "Reformer Tower & 3-in-1 made to order: 11 models across Aluminum / Maple / Oak. Packed size and gross weight for every model. OEM/ODM with your logo, colour and material spec. Request a quote.",
        "Custom Reformer Tower & 3-in-1 OEM/ODM: 11 models in aluminium, maple & oak, packed size and gross weight listed for each. Request a quote.",
    ),
    "pilates/pilates-studio-set.html": (
        "Pilates studio set configured to your floor plan: reformers, cadillac, chairs, ladder barrels and wall units from one factory, on one order. OEM/ODM with your logo and colour spec. Request a quote.",
        "Custom pilates studio set OEM/ODM: reformers, cadillac, chairs, ladder barrels & wall units from one factory on one order. Request a quote.",
    ),
    "pilates/pilates-wunda-chair.html": (
        "Pilates Wunda Chair made to order: 9 models across Metal / Maple / Oak. Packed size and gross weight for every model. OEM/ODM with your logo, colour and material spec. Request a quote.",
        "Custom Pilates Wunda Chair OEM/ODM: 9 models in metal, maple & oak with packed size and gross weight for each. Request a quote.",
    ),
    "pilates/pilates-cadillac.html": (
        "Pilates Cadillac made to order: 4 models across Maple / Oak / Metal. Packed size and gross weight for every model. OEM/ODM with your logo, colour and material spec. Request a quote.",
        "Custom Pilates Cadillac OEM/ODM: 4 models in maple, oak & metal with packed size and gross weight for each. Request a quote.",
    ),
    "pilates/pilates-specialty.html": (
        "Pilates Specialty made to order: 3 models across Maple. Packed size and gross weight for every model. OEM/ODM with your logo, colour and material spec. Request a quote.",
        "Custom Pilates Specialty OEM/ODM: 3 maple models with packed size and gross weight for each. Request a quote.",
    ),
}


def disp_w(s: str) -> int:
    """显示宽度：CJK 全角 ×2，其余 ×1。"""
    return sum(2 if ord(c) > 0x2E80 else 1 for c in s)


def main() -> None:
    dry = "--dry-run" in sys_argv()
    fail = False
    for rel, (old, new) in REWRITES.items():
        p = ROOT / rel
        h = p.read_text(encoding="utf-8")
        n = h.count(old)
        wn, wo = disp_w(new), disp_w(old)
        tag = "DRY " if dry else "OK  "
        print(f"{tag}{rel:44s} {wo} -> {wn}  命中 {n}")
        if wn > 155:
            print(f"     ✗ 新串仍超 155：{wn}")
            fail = True
        if n != 3:
            print(f"     ✗ 预期命中 3 处（name/og/twitter），实际 {n}，不动盘")
            fail = True
            continue
        if not dry:
            p.write_text(h.replace(old, new), encoding="utf-8")
    if fail:
        raise SystemExit(1)
    print("\n全部通过" + ("（dry-run 未落盘）" if dry else "，已落盘"))


def sys_argv():
    import sys
    return sys.argv[1:]


if __name__ == "__main__":
    main()
