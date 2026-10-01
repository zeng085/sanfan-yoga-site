#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
普拉提板块 —— **生成源 ⇄ 站点产物 一致性审计**  2026-10-01

=====================================================================
为什么必须有这个脚本（本轮真实教训）
=====================================================================
本轮我在 **已经被截断的字符串内部** 做了替换，结果产物与生成器脱钩：

  `build_pilates_section.py` 生成首页卡片时写的是
      bi(f["lead_en"][:180] + "…", f["lead_zh"][:110] + "…")
  即「先取 180 字再补省略号」。

  卡片上原文（HEAD 版）181 字符，其中含
      `the Gyrotonic tower set (rotator + pulley tower)`
  我把它换成更短的 `the rotator + pulley tower set`（少 18 字），
  于是卡片变成 **163 字符** —— 但生成器重跑会得到 **181 字符**。
  产物与源从此不一致，而**任何只改产物的检查都发现不了**。

  （A/B 已实证：HEAD 版产物 == 源 `[:180]+"…"` ✅；改后 != ❌）

=====================================================================
本脚本做什么
=====================================================================
用**生成器自己的表达式**重建应该出现的片段，再去产物里找。
重建式直接抄 `build_pilates_section.py`，不自己另写一套 —— 否则又是「两套口径」。

覆盖：
  A 首页 8 张族卡片（h3 / alias / cnt / 截断 lead 整块）
  B 8 个族页的 pl-tags 组
  C 8 个族页的 hero lead（全文，不截断）
  D 8 个族页的 model 表行（型号名 EN/ZH）

**每铺开一族页、每改一次文案，都跑这个。** 返回码 0 = 源与产物一致。

用法：
    python3 verify_pilates_source_vs_product_20261001.py
    python3 verify_pilates_source_vs_product_20261001.py --fix   # 用源重建卡片/hero 并落盘
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'i18n_build'))

import build_pilates_data as B          # noqa: E402
import build_pilates_section as S       # noqa: E402


def bi(en, zh):
    return '<span class="lang-en">%s</span><span class="lang-zh">%s</span>' % (en, zh)


def esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def model_count(key):
    return len([m for m in B.MODELS if m[1] == key])


def expected_card_bd(f):
    """完全照抄 build_pilates_section.py:646-655 的卡片模板"""
    alias = ('<div class="alias">%s</div>'
             % bi("Also called %s" % f["alias_en"], "也叫 %s" % f["alias_en"])) \
        if f.get("alias_en") else ""
    cnt = bi("%d models · %s" % (model_count(f["key"]), f["tag_en"]),
             "%d 个型号 · %s" % (model_count(f["key"]), f["tag_zh"] or ""))
    lead = bi(f['lead_en'][:180] + "…", f['lead_zh'][:110] + "…")
    return ('<div class="bd"><h3>%s</h3>%s<div class="cnt">%s</div><p>%s</p></div>'
            % (bi(f["en"], f["zh"]), alias, cnt, lead))


def expected_card_p(f):
    """卡片里那段 <p> 的期望值（只重建这一小段，替换更安全）"""
    return '<p>%s</p>' % bi(f['lead_en'][:180] + "…", f['lead_zh'][:110] + "…")


# ⚠️ 已迁移到「2026 画册体系」的页面：不再由 legacy 生成器产出，故 B/C/D 三段豁免。
#    ladder-barrel 是**手工建的样板页**（cat-unit 画册图区 + 型号卡 + 2026 口径文案），
#    legacy 生成器没有对应的模板 —— 强行对齐没有意义，且**重跑生成器会直接抹掉样板页**。
#    它的正确核验入口是：
#      · verify_pilates_data_sync_20261001.py（HTML ⇄ 画册数据源逐项对账）
#      · probe_catalog_blocks_20261001.cjs（双视口渲染）
#    ⛔ 铺开其余族页前先看 build_pilates_section.py 顶部的迁移警告。
MIGRATED_TO_CATALOG = {
    'pilates-ladder-barrel': '2026 画册样板页（手工建，见 data-sync + render 探针两套核验）',
}


def expected_tags(f):
    """照抄 build_pilates_section.py:479 的 pl-tags 表达式"""
    return "".join('<span class="pl-tag">%s</span>' % bi(t, S.TAG_ZH.get(t, t))
                   for t in f["tag_en"].split(" · "))


def expected_hero_lead(f):
    """族页 hero 用**全文**，不截断"""
    return '<p class="lead">%s</p>' % bi(f['lead_en'], f['lead_zh'])


def main():
    fix = '--fix' in sys.argv
    idx_path = ROOT / 'pilates/index.html'
    idx = idx_path.read_text(encoding='utf-8')
    fails, fixed = [], []

    print('=== A. 首页 8 张族卡片（h3 + alias + cnt + 截断 lead 整块）===')
    for f in B.FAMILIES:
        want = expected_card_bd(f)
        if want in idx:
            print(f'  ✅ {f["key"]:<26} 整块一致')
            continue
        fails.append(f'首页卡片 {f["key"]}')
        print(f'  ❌ {f["key"]:<26} 与生成器不一致')
        # 先圈出该卡片块，再只比对块里的 <p>（lead 是唯一会因文案改动而失配的段）
        a = idx.find('class="pl-card" href="/pilates/%s.html"' % f['key'])
        b = idx.find('</a>', a)
        block = idx[a:b] if a >= 0 else ''
        m = re.search(r'<p>.*?</p>', block, re.S)
        got, want_p = (m.group(0) if m else ''), expected_card_p(f)
        for k in range(min(len(want_p), len(got))):
            if want_p[k] != got[k]:
                print(f'       <p> 首个差异 @{k}:')
                print(f'         源重建 = …{want_p[max(0,k-40):k+40]}…')
                print(f'         产物上 = …{got[max(0,k-40):k+40]}…')
                break
        else:
            print(f'       <p> 前缀相同，长度不同：源重建 {len(want_p)} / 产物 {len(got)}')
        if fix and got:
            idx = idx.replace(block, block.replace(got, want_p), 1)
            fixed.append(f'首页卡片 {f["key"]} <p>')

    print('\n=== B. 族页 pl-tags ===')
    for f in B.FAMILIES:
        if f['key'] in MIGRATED_TO_CATALOG:
            print(f'  ℹ️  {f["key"]:<32} 豁免 —— {MIGRATED_TO_CATALOG[f["key"]]}')
            continue
        p = ROOT / ('pilates/%s.html' % f['key'])
        t = p.read_text(encoding='utf-8')
        want = expected_tags(f)
        ok = want in t
        print(f'  {"✅" if ok else "❌"} {p.name:<34}{"一致" if ok else "不一致"}')
        if not ok:
            fails.append(f'{p.name} pl-tags')
            m = re.search(r'<div><span class="pl-tag">.*?</div>', t, re.S)
            print(f'       源重建 = {want[:170]}')
            print(f'       产物上 = {m.group(0)[:170] if m else "未找到"}')
            if fix and m:
                t = t.replace(m.group(0), '<div>' + want + '</div>')
                p.write_text(t, encoding='utf-8')
                fixed.append(f'{p.name} pl-tags')

    print('\n=== C. 族页 hero lead（全文）===')
    for f in B.FAMILIES:
        if f['key'] in MIGRATED_TO_CATALOG:
            print(f'  ℹ️  {f["key"]:<32} 豁免 —— {MIGRATED_TO_CATALOG[f["key"]]}')
            continue
        p = ROOT / ('pilates/%s.html' % f['key'])
        t = p.read_text(encoding='utf-8')
        want = expected_hero_lead(f)
        ok = want in t
        print(f'  {"✅" if ok else "❌"} {p.name:<34}{"一致" if ok else "不一致"}')
        if not ok:
            fails.append(f'{p.name} hero lead')
            m = re.search(r'<p class="lead">.*?</p>', t, re.S)
            got = m.group(0) if m else ''
            for k in range(min(len(want), len(got))):
                if want[k] != got[k]:
                    print(f'       首个差异 @{k}:')
                    print(f'         源重建 = …{want[max(0,k-45):k+45]}…')
                    print(f'         产物上 = …{got[max(0,k-45):k+45]}…')
                    break
            else:
                print(f'         前缀相同，长度不同：源重建 {len(want)} / 产物 {len(got)}')
            if fix and got:
                t = t.replace(got, want)
                p.write_text(t, encoding='utf-8')
                fixed.append(f'{p.name} hero lead')

    print('\n=== D. 族页 model 表行（型号名 EN/ZH）===')
    for f in B.FAMILIES:
        if f['key'] in MIGRATED_TO_CATALOG:
            print(f'  ℹ️  {f["key"]:<32} 豁免 —— 已从 legacy 41 台体系迁到画册 7 台'
                  f'（由 verify_pilates_data_sync 负责对账）')
            continue
        p = ROOT / ('pilates/%s.html' % f['key'])
        t = p.read_text(encoding='utf-8')
        bad = []
        for m in [m for m in B.MODELS if m[1] == f['key']]:
            if ('<span class="lang-en">%s</span>' % m[2]) not in t:
                bad.append(f'{m[0]} EN 「{m[2]}」')
            if ('<span class="lang-zh">%s</span>' % m[3]) not in t:
                bad.append(f'{m[0]} ZH 「{m[3]}」')
        n = model_count(f['key'])
        print(f'  {"✅" if not bad else "❌"} {p.name:<34}{n} 台，缺 {len(bad)} 项')
        for b in bad[:3]:
            print(f'       ⚠️ {b}')
        if bad:
            fails.append(f'{p.name} model 行 {len(bad)} 项')

    if fix and fixed:
        idx_path.write_text(idx, encoding='utf-8')
        print(f'\n💾 已用生成器表达式重建 {len(fixed)} 处：')
        for x in fixed:
            print('   ·', x)

    print()
    if fails:
        print(f'❌ {len(fails)} 处「源 ⇄ 产物」不一致：')
        for x in fails:
            print('   -', x)
        if not fix:
            print('\n（加 --fix 可用生成器表达式重建卡片/hero/tags）')
        return 1
    print('✅ 生成源与站点产物完全一致（8 族 × 4 类）')
    return 0


if __name__ == '__main__':
    sys.exit(main())
