#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移动端 WIG 体检 —— 静态源码扫描（第 1 层）  2026-09-27
判据来源：i18n_build/reference/vercel_wig_AGENTS.md（vercel-labs 官方）

⚠️ 优化：**每个文件只读一次**，所有检测在同一次遍历内完成。
   （首版读两遍 → 全量 220s，被 SIGTERM；见 memory 铁律「全站脚本一律后台跑」）
⚠️ 自审：①排除 i18n_build/outputs/assets ②`...` 先剥离注释与 script/style
        ③语言版单独分组 ④检测写法要覆盖变体（0 / none / 小数）
"""
import os, re, json, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {'i18n_build', 'outputs', '__pycache__', '.git', 'node_modules', 'assets'}
LANGS = ['de', 'ja', 'ko', 'fr', 'it', 'es']

RE_VIEWPORT = re.compile(r'<meta[^>]+name=["\']viewport["\'][^>]*>', re.I)
RE_DEVDW    = re.compile(r'width\s*=\s*device-width', re.I)
RE_NOSCALE  = re.compile(r'user-scalable\s*=\s*no', re.I)
RE_MAXSCALE = re.compile(r'maximum-scale\s*=\s*1(?:\.0+)?(?![0-9])', re.I)
RE_THEMECOL = re.compile(r'<meta[^>]+name=["\']theme-color["\']', re.I)
RE_PRECON   = re.compile(r'rel=["\']preconnect["\']', re.I)
RE_TRANSNO  = re.compile(r'translate\s*=\s*["\']no["\']', re.I)
RE_COMMENT  = re.compile(r'<!--.*?-->', re.S)
RE_SCRIPT   = re.compile(r'<script\b.*?</script>', re.S | re.I)
RE_STYLE    = re.compile(r'<style\b.*?</style>', re.S | re.I)
RE_DOTS     = re.compile(r'(?<![\w./])\.{3}(?![\w.])')
RE_IMG      = re.compile(r'<img\b[^>]*>', re.I)
RE_IMG_W    = re.compile(r'\bwidth\s*=', re.I)
RE_IMG_H    = re.compile(r'\bheight\s*=', re.I)
RE_IMG_LZ   = re.compile(r'loading\s*=\s*["\']lazy["\']', re.I)
RE_ARIA     = re.compile(r'aria-label\s*=', re.I)
RE_ICONBTN  = re.compile(r'<(a|button)\b[^>]*>(?:(?!</\1>).){0,120}?</\1>', re.S | re.I)


def collect_html():
    out = []
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if f.endswith('.html'):
                out.append(os.path.join(dp, f))
    return sorted(out)


def lang_of(p):
    h = os.path.relpath(p, ROOT).split(os.sep)[0]
    return h if h in LANGS else 'en'


def main():
    t0 = time.time()
    files = collect_html()
    print(f'扫描 HTML：{len(files)} 个文件', flush=True)

    S = {k: [] for k in ['no_viewport', 'no_devwidth', 'zoom_disabled', 'theme_color',
                         'preconnect', 'trans_no', 'dots', 'nbsp']}
    img_total = img_no_dim = img_lazy = 0
    icon_btn = icon_btn_no_label = 0
    per_lang = {}

    for i, f in enumerate(files):
        h = open(f, encoding='utf-8', errors='replace').read()
        L = lang_of(f)
        pl = per_lang.setdefault(L, {'files': 0, 'zoom_disabled': 0, 'dots': 0, 'trans_no': 0})
        pl['files'] += 1

        # --- meta 组 ---
        m = RE_VIEWPORT.search(h)
        if not m:
            S['no_viewport'].append(f)
        else:
            tag = m.group(0)
            if not RE_DEVDW.search(tag):
                S['no_devwidth'].append(f)
            if RE_NOSCALE.search(tag) or RE_MAXSCALE.search(tag):
                S['zoom_disabled'].append(f); pl['zoom_disabled'] += 1
        if RE_THEMECOL.search(h):
            S['theme_color'].append(f)
        if RE_PRECON.search(h):
            S['preconnect'].append(f)
        if RE_TRANSNO.search(h):
            S['trans_no'].append(f); pl['trans_no'] += 1

        # --- 正文组（剥离注释/脚本/样式）---
        body = RE_SCRIPT.sub(' ', RE_STYLE.sub(' ', RE_COMMENT.sub(' ', h)))
        if RE_DOTS.search(body):
            S['dots'].append(f); pl['dots'] += 1
        if '&nbsp;' in body or '\u00a0' in body:
            S['nbsp'].append(f)

        # --- 图片组 ---
        for im in RE_IMG.finditer(body):
            img_total += 1
            t = im.group(0)
            if not (RE_IMG_W.search(t) and RE_IMG_H.search(t)):
                img_no_dim += 1
            if RE_IMG_LZ.search(t):
                img_lazy += 1

        # --- 图标按钮 aria-label ---
        for b in RE_ICONBTN.finditer(body):
            t = b.group(0)
            inner = re.sub(r'<[^>]+>', '', t).strip()
            if len(inner) == 0:            # 无可见文字 = 疑似图标按钮
                icon_btn += 1
                if not RE_ARIA.search(t):
                    icon_btn_no_label += 1

        if i % 300 == 0:
            print(f'  ... {i}/{len(files)}  ({time.time()-t0:.0f}s)', flush=True)

    print(f'读取完成，耗时 {time.time()-t0:.0f}s\n' + '=' * 78, flush=True)
    print('按语言目录：' + '  '.join(f'{k}={v["files"]}' for k, v in sorted(per_lang.items(), key=lambda x: -x[1]['files'])))

    css_path = os.path.join(ROOT, 'assets', 'css', 'styles.css')
    css = open(css_path, encoding='utf-8', errors='replace').read()
    print(f'CSS：assets/css/styles.css  {len(css.splitlines())} 行 / {len(css)} 字节')
    print('=' * 78)

    N = len(files)
    R = []
    def add(cid, desc, lvl, verdict, detail=''): R.append((cid, desc, lvl, verdict, detail))
    rel = lambda lst: ' '.join(os.path.relpath(x, ROOT) for x in lst[:6])

    add('WIG-01', 'NEVER 禁用浏览器缩放（user-scalable=no / maximum-scale=1）', 'NEVER',
        '✅ 通过' if not S['zoom_disabled'] else f'❌ 违反 {len(S["zoom_disabled"])} 页', rel(S['zoom_disabled']))
    add('WIG-02', 'MUST viewport 含 width=device-width', 'MUST',
        '✅ 通过' if not (S['no_viewport'] or S['no_devwidth']) else f'❌ 缺 viewport {len(S["no_viewport"])} / 无 device-width {len(S["no_devwidth"])}',
        rel(S['no_viewport'] + S['no_devwidth']))
    add('WIG-03', 'SHOULD <meta theme-color> 匹配页背景', 'SHOULD',
        f'{len(S["theme_color"])}/{N} 页有（{100*len(S["theme_color"])//N}%）')

    for cid, desc, lvl, pat in [
        ('WIG-04', 'MUST touch-action: manipulation', 'MUST',           r'touch-action\s*:\s*manipulation'),
        ('WIG-05', 'SHOULD -webkit-tap-highlight-color', 'SHOULD',      r'-webkit-tap-highlight-color'),
        ('WIG-06', 'MUST env(safe-area-inset-*) 安全区', 'MUST',        r'env\(\s*safe-area-inset'),
        ('WIG-08', 'MUST prefers-reduced-motion', 'MUST',               r'prefers-reduced-motion'),
        ('WIG-09', 'MUST :focus-visible 焦点环', 'MUST',                 r':focus-visible'),
        ('WIG-10', 'MUST scroll-margin-top（头部遮锚点）', 'MUST',        r'scroll-margin-top'),
        ('WIG-11', 'MUST tabular-nums（规格数字对比）', 'MUST',          r'font-variant-numeric\s*:[^;]*tabular-nums'),
        ('WIG-12', 'SHOULD text-wrap: balance', 'SHOULD',               r'text-wrap\s*:\s*balance'),
    ]:
        n = len(re.findall(pat, css, re.I))
        add(cid, desc, lvl, ('✅ 有' if n else '❌ 缺失') + f'（{n} 处）', '' if n else 'styles.css 0 命中')

    # WIG-07 自审修正：「有 overscroll-behavior」≠「用在了抽屉上」——须抓选择器定位
    osc = re.findall(r'([^{}]+)\{([^{}]*overscroll-behavior[^{}]*)\}', css)
    osc_sel = [re.sub(r'\s+', ' ', s).strip()[:46] for s, _ in osc]
    add('WIG-07', 'MUST overscroll-behavior: contain（抽屉/弹层）', 'MUST',
        f'⚠️ 仅 {len(osc)} 处（位置待核）' if osc else '❌ 缺失',
        ('; '.join(osc_sel[:3]) + '   ← 未见 .nav-links 移动抽屉') if osc else 'styles.css 0 命中')

    n = len(re.findall(r'transition\s*:\s*all\b', css, re.I))
    add('WIG-13', 'NEVER transition: all（须逐属性）', 'NEVER', '✅ 无' if not n else f'❌ {n} 处')
    # WIG-14 自审修正：不能只看 :focus-visible / box-shadow —— border-color/background 也是合法替代
    blocks = re.findall(r'([^{}]+)\{([^{}]*)\}', css)
    on = [(s.strip()[:48], b) for s, b in blocks if re.search(r'outline\s*:\s*(?:none|0)\b', b, re.I)]
    focus_on = [x for x in on if ':focus' in x[0]]
    no_alt = [x for x in focus_on if not re.search(r'border(-color|-width)?\s*:|box-shadow\s*:|background\s*:', x[1], re.I)]
    add('WIG-14', 'NEVER outline:none 无可见焦点替代', 'NEVER',
        '✅ 通过' if not no_alt else f'⚠️ {len(no_alt)}/{len(on)} 处无替代',
        ('; '.join(f'{s}' for s, _ in no_alt[:3])) or
        f'outline:none/0 共 {len(on)} 处（:focus 内 {len(focus_on)}），余为常驻控件去环')


    small = []
    for sel, val, unit in re.findall(r'([^{}]*?)\{[^{}]*?font-size\s*:\s*([0-9.]+)(px|rem|em)', css, re.I):
        try: v = float(val)
        except: continue
        px = v if unit == 'px' else v * 16
        if px < 16 and re.search(r'input|textarea|select', sel, re.I):
            small.append((sel.strip()[:50], f'{val}{unit}'))
    add('WIG-15', 'MUST 移动端 input font-size ≥16px（防 iOS 放大）', 'MUST',
        '✅ 通过' if not small else f'⚠️ {len(small)} 条 <16px',
        '; '.join(f'{s}={v}' for s, v in small[:5]) or '无 input 小字号规则')

    add('WIG-16', 'SHOULD 品牌名加 translate="no"（防机翻）', 'SHOULD',
        f'{len(S["trans_no"])}/{N} 页有',
        '⚠️ 8 语言站刚需' if len(S['trans_no']) < N * 0.1 else '')
    add('WIG-17', 'MUST 用 `…` 而非 `...`', 'MUST',
        '✅ 通过' if not S['dots'] else f'⚠️ {len(S["dots"])} 页含 `...`', rel(S['dots']))
    add('WIG-18', 'MUST 非断空格（10&nbsp;MB / 品牌名）', 'MUST',
        f'{len(S["nbsp"])}/{N} 页有 &nbsp;')
    add('WIG-19', 'MUST 图片显式尺寸（防 CLS）', 'MUST',
        f'✅ 全部合规' if not img_no_dim else f'⚠️ {img_no_dim}/{img_total} 张 img 缺 width+height',
        f'img 总数 {img_total}')
    add('WIG-20', 'MUST 首屏图 preload、其余 lazy-load', 'MUST',
        f'{img_lazy}/{img_total} 张 img 带 loading=lazy({100*img_lazy//max(img_total,1)}%)',
        f'{len(S["preconnect"])}/{N} 页有 preconnect')
    # WIG-21 自审修正：HTML 正则无法判定「元素内是否只有图标」——首版报 3550/3550 全缺，
    # 经浏览器实测证伪（76 个纯图标全部有 aria-label）→ 静态层不判定，交浏览器层
    add('WIG-21', 'MUST 纯图标按钮须有 aria-label', 'MUST',
        '⏭ 静态不可判 → 见浏览器层',
        f'（首版正则误报 {icon_btn_no_label}/{icon_btn}；浏览器实测 6 页 76 个纯图标 a/button，缺名 0）')

    R.sort(key=lambda r: r[0])

    print(f'{"编号":<8}{"级别":<8}{"条款":<50}{"判定"}')
    print('-' * 78)
    for cid, desc, lvl, verdict, detail in R:
        print(f'{cid:<8}{lvl:<8}{desc[:48]:<50}{verdict}')
        if detail: print(f'        └ {detail[:145]}')
    print('=' * 78)
    bad = [r for r in R if r[3].startswith('❌')]
    warn = [r for r in R if r[3].startswith('⚠️')]
    print(f'❌ 明确违反 {len(bad)} 项：{" ".join(r[0] for r in bad)}')
    print(f'⚠️ 部分/需确认 {len(warn)} 项：{" ".join(r[0] for r in warn)}')
    print(f'✅ 通过 {len([r for r in R if r[3].startswith("✅")])} 项   总耗时 {time.time()-t0:.0f}s')

    out = os.path.join(ROOT, 'i18n_build', 'reports', 'mobile_wig_static_20260927.json')
    json.dump({'per_lang': per_lang, 'img_total': img_total, 'files': N,
               'results': [{'id': r[0], 'clause': r[1], 'level': r[2], 'verdict': r[3], 'detail': r[4]} for r in R]},
              open(out, 'w'), ensure_ascii=False, indent=1)
    print(f'\n→ 明细 {out}')


if __name__ == '__main__':
    main()
