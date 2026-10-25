# -*- coding: utf-8 -*-
"""站点公共模板 —— 页头 / 导航 / 页脚 / CTA / 双语 span / 分组分类条。

为什么要抽出来：分类页（根目录）与场景页（applications/ 子目录）用的是同一套
header/footer，唯一差别是资源与内链的相对前缀（"" vs "../"）。各脚本各抄一份迟早漂移，
所以统一到这里，用 prefix 参数控制。

    from site_templates import head, nav, footer, cta, bi, cat_nav, apps_section

    head(..., prefix="")        # 根目录页
    head(..., prefix="../")     # applications/ 下的页
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from category_map import CATS, CAT_BY_KEY  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://fjsanfan.com"

# 分类展示分组：导航与分类条都按这三组呈现（L2）。
# key 必须能在 CATS 里找到；顺序即导航里的顺序。
GROUPS = [
    ("mats", "Mats", "垫类",
     ["tpe-yoga-mats", "pu-rubber-yoga-mats", "suede-cork-yoga-mats",
      "meditation-pilates-mats"]),
    ("training", "Training", "训练",
     ["strength-training", "jump-ropes", "resistance-bands", "foam-rollers"]),
    ("recovery", "Recovery & Props", "恢复与辅具",
     ["massage-recovery", "yoga-props-accessories"]),
]


def current_ver():
    """从既有产品页读版本号，避免脚本里硬编码后忘记同步。"""
    m = re.search(r"styles\.css\?v([A-Za-z0-9]+)",
                  open(os.path.join(ROOT, "products", "ym1.html"), encoding="utf-8").read())
    return m.group(1) if m else "20260912a"


VER = "v" + current_ver()


def bi(en, zh):
    """双语 span。.lang-zh 默认 display:none，中文态由 html.show-zh 切换。"""
    return '<span class="lang-en">%s</span><span class="lang-zh">%s</span>' % (en, zh)


def esc(t):
    return t.replace('"', "&quot;")


# ------------------------------------------------------------------ 页头
HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>%(title)s</title>
  <meta name="description" content="%(desc)s" />
  <link rel="canonical" href="%(canonical)s" />
  <link rel="alternate" hreflang="en" href="%(canonical)s" />
  <link rel="alternate" hreflang="x-default" href="%(canonical)s" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="%(title)s" />
  <meta property="og:description" content="%(desc)s" />
  <meta property="og:image" content="%(og_img)s" />
  <meta property="og:url" content="%(canonical)s" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="%(title)s" />
  <meta name="twitter:description" content="%(desc)s" />
  <meta name="twitter:image" content="%(og_img)s" />
  <link rel="stylesheet" href="%(pf)sassets/css/styles.css?%(ver)s" />
  <link rel="icon" href="%(pf)sassets/img/logo.webp" />

  <script type="application/ld+json">
  %(jsonld)s
  </script>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-RMSNDR5S06"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-RMSNDR5S06');
</script>
</head>
<body>
"""

NAV = """  <header class="site-header">
    <div class="container nav">
      <a href="/" class="nav-brand"><img src="%(pf)sassets/img/logo.webp" width="500" height="500" alt="SANFAN" /><span>SAN<span class="accent">FAN</span></span></a>
      <nav class="nav-links">
        <a href="/" data-i18n="nav.home">Home</a>
        <a href="%(pf)sproducts.html"%(cur)s data-i18n="nav.products">Yoga Mats &amp; Gear</a>
        <a href="%(pf)sabout.html" data-i18n="nav.about">About</a>
        <a href="%(pf)sfaq.html" data-i18n="nav.faq">FAQ</a>
        <a href="%(pf)sblog.html" data-i18n="nav.blog">Blog</a>
        <a href="%(pf)scontact.html" data-i18n="nav.contact">Contact</a>
      </nav>
      <div class="nav-actions"><div class="lang-switch"><button type="button" class="lang-current" aria-haspopup="true" aria-expanded="false"><span class="lang-cur-txt">EN</span><span class="lang-caret">&#9662;</span></button><div class="lang-menu"><button type="button" data-setlang="en" title="English" class="active">EN</button><button type="button" data-setlang="zh" title="中文">中文</button><a href="/de/products.html" hreflang="de" title="Deutsch">DE</a><a href="/ja/products.html" hreflang="ja" title="日本語">JA</a><a href="/ko/products.html" hreflang="ko" title="한국어">KO</a><a href="/fr/products.html" hreflang="fr" title="Français">FR</a><a href="/it/products.html" hreflang="it" title="Italiano">IT</a><a href="/es/products.html" hreflang="es" title="Español">ES</a></div></div>
        <a href="%(pf)scontact.html" class="btn btn-primary" data-i18n="nav.quote">Get a Quote</a>
      </div>
      <button class="menu-toggle" aria-label="menu">☰</button>
    </div>
  </header>
"""

FOOTER = """  <footer class="site-footer">
    <div class="container footer-grid">
      <div>
        <div class="brand"><img src="%(pf)sassets/img/logo.webp" width="500" height="500" loading="lazy" alt="SANFAN" /> <span>SAN<span style="color:var(--brand-2)">FAN</span></span></div>
        <p style="font-size:14px;max-width:300px" data-i18n="f.tag">OEM / ODM yoga &amp; fitness manufacturer.</p>
      </div>
      <div><h5 data-i18n="foot.products">Yoga Mats &amp; Gear</h5><ul>
%(foot_cats)s      </ul></div>
      <div><h5 data-i18n="foot.apps">Shop by Application</h5><ul>
%(foot_apps)s      </ul></div>
      <div><h5 data-i18n="foot.company">Company</h5><ul>
        <li><a href="%(pf)sabout.html" data-i18n="nav.about">About</a></li>
        <li><a href="%(pf)sabout.html" data-i18n="process.title">Production Process</a></li>
        <li><a href="%(pf)sfaq.html" data-i18n="nav.faq">FAQ</a></li>
        <li><a href="%(pf)sblog.html" data-i18n="nav.blog">Blog</a></li>
      </ul></div>
      <div><h5 data-i18n="foot.contact">Contact</h5>
        <div class="contact-line"><span data-i18n="foot.addr">Address</span>: No. 8 Haiguang Road, Yuejin Industrial Zone, Xibin Town, Jinjiang, Quanzhou, Fujian, China</div>
        <div class="contact-line"><span data-i18n="foot.email">Email</span>: <a class="c-link" href="mailto:zenglinggun@gmail.com">zenglinggun@gmail.com</a></div>
        <div class="contact-line"><span data-i18n="foot.phone">WhatsApp</span>: <a class="c-link" href="https://wa.me/8615959029082" target="_blank" rel="noopener">+86 15959029082</a></div>
      </div>
    </div>
    <div class="container footer-bottom" data-i18n="foot.copyright">© 2026 FUJIAN SANFAN Sports Products Co., Ltd. All rights reserved.</div>
  </footer>

  <script src="%(pf)sassets/js/main.js?%(ver)s"></script>
</body>
</html>
"""

CTA = """  <section class="section soft">
    <div class="container" style="text-align:center;">
      <h2>%s</h2>
      <p class="lead" style="margin:12px auto 22px;max-width:660px;">
        %s
      </p>
      <a href="%%(pf)scontact.html" class="btn btn-primary">%s</a>
    </div>
  </section>
"""


def head(title, desc, canonical, og_img, jsonld, prefix="", ver=None):
    return HEAD % {
        "title": title.replace("|", "&#124;"),
        "desc": esc(desc),
        "canonical": canonical,
        "og_img": og_img,
        "jsonld": jsonld,
        "pf": prefix,
        "ver": ver or VER,
    }


def nav(prefix="", cur=False):
    return NAV % {"pf": prefix, "cur": ' aria-current="page"' if cur else ""}


def footer(prefix="", ver=None):
    foot_cats = "".join(
        '        <li><a href="%s%s.html">%s</a></li>\n' % (prefix, c["key"], bi(c["en"], c["zh"]))
        for c in CATS
    )
    from apps_data import APPS  # 延迟导入，避免循环依赖
    foot_apps = ['        <li><a href="%sapplications/index.html">%s</a></li>\n'
                 % (prefix, bi("All Applications", "全部应用场景"))]
    foot_apps += ['        <li><a href="%sapplications/%s.html">%s</a></li>\n'
                  % (prefix, a["key"], bi(a["en"], a["zh"])) for a in APPS]
    foot_apps.append('        <li><a href="%smaterials.html">%s</a></li>\n'
                     % (prefix, bi("Materials Compared", "材质对比")))
    return FOOTER % {"pf": prefix, "ver": ver or VER,
                     "foot_cats": foot_cats, "foot_apps": "".join(foot_apps)}


def cta(prefix=""):
    return CTA % (
        bi("Can't find the exact spec?", "没找到完全匹配的规格？"),
        bi("Send us your drawing, target price or a photo — our sales team replies "
           "within 2 hours on working days (Mon–Sat, 09:00–22:00 China time). MOQ from 100 pcs.",
           "把图纸、目标价或照片发给我们 —— 销售团队工作日 2 小时内回复（周一至周六 09:00–22:00 北京时间），100 片起订。"),
        bi("Get a Quote", "获取报价"),
    ) % {"pf": prefix}


# ------------------------------------------------------------------ 分类条（L2 分组）
def cat_nav(cur_key=None, prefix="", apps_row=True):
    """分组分类条 + 场景快捷行。

    现状是一条 10 个 chip 的平铺，没有层级；分组后客户知道自己站在哪个大类里，
    底部的场景行再给一条「按生意入口」的捷径。
    """
    cols = []
    for gkey, gen, gzh, keys in GROUPS:
        chips = []
        for k in keys:
            c = CAT_BY_KEY[k]
            act = " cat-chip-active" if k == cur_key else ""
            chips.append('        <a href="%s%s.html" class="cat-chip%s">%s</a>'
                         % (prefix, k, act, bi(c["en"], c["zh"])))
        cols.append(
            '      <div class="cg-col">\n'
            '        <p class="cg-cap">%s</p>\n'
            '        <div class="cg-list">\n%s\n        </div>\n'
            '      </div>' % (bi(gen, gzh), "\n".join(chips)))
    out = ('  <div class="container cat-nav-wrap">\n'
           '    <nav class="cat-nav cat-nav-grouped" aria-label="Product categories">\n'
           + "\n".join(cols) + "\n    </nav>\n")
    if apps_row:
        from apps_data import APPS
        row = "".join('<a href="%sapplications/%s.html">%s</a>' % (prefix, a["key"], bi(a["en"], a["zh"]))
                      for a in APPS)
        out += ('    <div class="needrow">\n'
                '      <b>%s</b>\n      %s\n    </div>\n'
                % (bi("Or start from what you sell:", "或者，按你卖给谁进场："), row))
    out += "  </div>\n"
    return out


# ------------------------------------------------------------------ 场景入口区（L3 前置）
def apps_section(prefix="", head_en=None, head_zh=None, cls="section"):
    """6 张场景卡的静态区块 —— 放在总览页与首页，提供可抓取的场景内链。"""
    from apps_data import APPS
    cards = []
    for a in APPS:
        cards.append(
            '        <a class="app-card" href="%sapplications/%s.html">\n'
            '          <span class="ac-icon">%s</span>\n'
            '          <h4>%s</h4>\n'
            '          <p>%s</p>\n'
            '          <div class="ac-kit">%s</div>\n'
            '          <div class="ac-go">%s</div>\n'
            '        </a>' % (prefix, a["key"], a["icon"], bi(a["en"], a["zh"]),
                             bi(a["card_en"], a["card_zh"]), bi(a["kit_en"], a["kit_zh"]),
                             bi("See the range", "查看方案") + " &rarr;"))
    return (
        '  <section class="%s" id="applications">\n'
        '    <div class="container">\n'
        '      <div class="section-head">\n'
        '        <div class="eyebrow">%s</div>\n'
        '        <h2>%s</h2>\n'
        '        <p>%s</p>\n'
        '      </div>\n'
        '      <div class="apps-grid">\n%s\n      </div>\n'
        '    </div>\n'
        '  </section>\n\n'
        % (cls,
           bi("Applications", "应用场景"),
           bi(head_en or "Shop by application — pick your buyer",
              head_zh or "按用途选购 —— 选你的客户类型"),
           bi("Every range below is the same factory, the same colour system and one PO. "
              "Pick the one that matches your buyer and we will spec the whole kit.",
              "下面每个场景都是同一家工厂、同一套配色、一张订单。选一个贴近你客户的入口，"
              "我们把整套配置给你配齐。"),
           "\n".join(cards))
    )


def trust_strip():
    """四格信任条，场景页/材质页复用。"""
    items = [
        ("MOQ 100 pcs", "100 片起订", "Low entry for a first order", "首批就能试单"),
        ("7-day sampling", "7 天打样", "Physical sample with your logo", "带 Logo 的实物样品"),
        ("ISO 9001 / BSCI", "ISO 9001 / BSCI", "Audited & traceable batches", "审核通过、批次可追溯"),
        ("FOB Xiamen / FBA-ready", "厦门 FOB / 可直发 FBA", "Export docs handled", "出口单证代办"),
    ]
    cells = "".join(
        '      <div class="ts-cell"><div class="ts-n">%s</div><div class="ts-d">%s</div></div>\n'
        % (bi(n, z), bi(d, dz)) for n, z, d, dz in items)
    return '  <section class="trust-strip"><div class="container"><div class="ts-grid">\n%s</div></div></section>\n' % cells


if __name__ == "__main__":
    print("VER =", VER)
    print("分类数 =", len(CATS), "分组数 =", len(GROUPS))
