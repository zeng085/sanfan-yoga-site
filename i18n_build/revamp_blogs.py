# -*- coding: utf-8 -*-
"""博客专业化重写执行器。
- 用 blog_rewrite_a/b 的新 EN 正文替换 8 篇博客的 lang-en 块
- 同步刷新 zh 摘要（原 zh 本就是 150-270 字摘要版）
- 老页面 head 补 GA4 统计（老博客页之前没有 GA，流量一直没被度量）
幂等可重跑；用法：python3 i18n_build/revamp_blogs.py [--dry]"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blog_rewrite_a import POSTS_A  # noqa: E402
from blog_rewrite_b import POSTS_B  # noqa: E402

DRY = "--dry" in sys.argv
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = {**POSTS_A, **POSTS_B}

GA = """<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-RMSNDR5S06"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-RMSNDR5S06');
</script>
"""

ZH = {
"moq-explained": """<div class="post-meta">MOQ · 8 分钟 · 更新于 2026 年 9 月</div>
          <h1>瑜伽垫起订量详解：到底能做多低</h1>
          <p class="lead-p">起订量决定你在验证一款产品卖不卖得动之前要压多少现金。这篇讲清 MOQ 到底贵在哪、工厂为什么定在这个数，以及怎么用好 100 片的小单，不掉进高单价的坑。</p>
          <img class="article-cover" src="../assets/img/tpe-mat-3.webp" width="480" height="480" loading="lazy" alt="小起订量自有品牌瑜伽垫" />
          <div class="article-body">
            <p>三梵 TPE 瑜伽垫 100 片起（按设计+颜色计），PU/橡胶垫 300 片，EVA 砖、泡沫轴 500 片，弹力带 1000 片。FOB 报价体系下：100 片的单价比 3000 片档高出约 30–40%，500 片档收窄到 10–15%。</p>
            <p>MOQ 的本质是固定摊销：调色、生产线升温、模具校准、换色清机，这些成本摊到多少片上，单价才算得过来。我们能做 100 片，靠的是常备色母库存、自制裁切模具、小单插单排产——不是让价，是排产方式。</p>
            <p>健康品牌的路径几乎一样：100 片试销 → 卖动后补 500 片 → 爆款补 3000 片拉低单价。100 片首单不是妥协，是最便宜的试错。文章含完整价格梯度表、常见误区（"零 MOQ"多半是贸易商清库存）、多品类拼柜规则，以及什么时候该主动放弃小单。</p>
          </div>""",
"tpe-vs-pu": """<div class="post-meta">材质 · 9 分钟 · 更新于 2026 年 9 月</div>
          <h1>TPE 对比 PU 橡胶瑜伽垫：2026 年怎么选</h1>
          <p class="lead-p">材质决定单价、运费、防滑和品牌定位。两条线我们自己工厂都在做，这篇给你的是每周都在报价的真实对比。</p>
          <img class="article-cover" src="../assets/img/tpe-mat-1.webp" width="480" height="480" loading="lazy" alt="TPE 瑜伽垫" />
          <div class="article-body">
            <p>核心数据：同为 6mm、183×61cm，TPE 双层垫约 1.1 kg，PU+天然橡胶垫约 2.4 kg；TPE 单价约为 PU 的一半，100 片起订，PU 300 片起。TPE 干态防滑可靠、湿态打滑；PU 遇汗愈抓——湿防滑是两种材料真正的分水岭，做高温瑜伽线就必须上 PU。</p>
            <p>耐久方面：TPE 家用 2–3 年、馆用 12–18 个月；PU 更耐用但表面会留使用痕迹，需要正确的清洁说明（温和清洗、晾干、湿态不折叠）。市场偏好：北美澳洲走 TPE（轻、性价比、开箱无味），西欧馆 demand PU，日韩偏好薄款高精度 TPE 配细腻压印。</p>
            <p>常见打法是一个系列做两层：TPE 走量、PU 旗舰拉利润，同一工厂同一品牌语言，同窗口打样、同柜出货。文内含完整对比表、价格梯度与按市场选材建议。</p>
          </div>""",
"yoga-mat-materials": """<div class="post-meta">材质 · 10 分钟 · 更新于 2026 年 9 月</div>
          <h1>瑜伽垫材质横评：TPE / NBR / PVC / 天然橡胶（2026）</h1>
          <p class="lead-p">材质选择决定单价、运重、防滑、寿命，以及能不能过欧美化学品合规。这是我们自己产线上的实操对比。</p>
          <img class="article-cover" src="../assets/img/tpe-mat-1.webp" width="480" height="480" loading="lazy" alt="TPE 瑜伽垫" />
          <div class="article-body">
            <p>六毫米标准垫的排序：TPE 是自有品牌默认解——约 1.1 kg、可回收、无 PVC、干态防滑可靠，100 片起订；NBR 是健身房的性价比主力——便宜耐用但 1.6 kg 偏重、难回收；PVC 最便宜最耐用，但塑化剂正是欧盟 REACH 和加州 65 号提案限制的东西，欧美消费品牌基本已弃用；天然橡胶抓地最好、环保故事最扎实，代价是重量翻倍和乳胶标注义务；PU+橡胶湿态抓地最强，高温瑜伽标配，价格最高。</p>
            <p>选材跟着渠道走：预算首发选 TPE，高端/高温线选 PU，馆用大采购选 NBR 或厚 TPE，环保主张选天然橡胶并配认证，促销赠品在合规允许下才考虑 PVC。文内含五材质横向数据表、按场景选材表和下单前合规清单。</p>
          </div>""",
"vet-factory": """<div class="post-meta">验厂 · 12 分钟 · 更新于 2026 年 9 月</div>
          <h1>大货下单前，如何甄别中国瑜伽垫工厂</h1>
          <p class="lead-p">下单前先确认对方是真工厂还是转手贸易商。这篇是我们替你跑一遍的验厂流程，包括让贸易商不舒服的那些问题。</p>
          <img class="article-cover" src="../assets/img/factory-building.webp" width="1920" height="1249" loading="lazy" alt="三梵晋江工厂" />
          <div class="article-body">
            <p>三个快测：①要求视频直播看发泡线——贸易商能给你看展厅，不敢把镜头对准产线；②问"接受现成色的话 MOQ 能降多少"——数字纹丝不动的不是工厂；③要一份带日期、带实验室名字、对应你材料的检测报告。</p>
            <p>真正该锁的规格不是"6mm TPE"：同厚度材料量可以差 30%，照片看不出来，退货看得出来。要求白纸黑字写克重和公差（我们：长宽 ±1mm、厚度 ±0.3mm），量产样上秤。样品做五项测试：干/湿防滑、48 小时密封闻味、24 小时卷边回弹、称重、对折查压痕。付款 30% 定金 + 70% 见提单，首单花 200–300 美元请第三方验货（AQL 2.5/4.0）。EXW/FOB/DDP 三种条款并排比落地成本。真实时间线：打样 7–12 天 + 大货 15–25 天 + 海运 25–40 天，承诺 20 天门到门的在发别人的库存。以三梵为例：晋江 12,000 ㎡ 自有厂房、5 条产线、ISO 9001 与 BSCI 在档，随时可视频看厂或到访。</p>
          </div>""",
"custom-sizes": """<div class="post-meta">定制 · 8 分钟 · 更新于 2026 年 9 月</div>
          <h1>瑜伽垫定制尺寸与厚度：采购指南</h1>
          <p class="lead-p">标准款不一定是你的市场要的。这篇讲清瑜伽垫上哪些东西真正可定制、每项改动在模具和起订量上的代价，以及哪些要求工厂不该接。</p>
          <img class="article-cover" src="../assets/img/tpe-mat-5.webp" width="480" height="480" loading="lazy" alt="加宽 TPE 瑜伽垫" />
          <div class="article-body">
            <p>可定制清单：长度 173–200cm，宽度 61 / 80 / 122cm（加宽和双人宽是差异化利器，多数竞品只有 61cm），厚度 3–15mm，潘通对色，双色双层，Logo 印刷/压印/激光雕刻。裁切公差长宽 ±1mm、厚度 ±0.3mm，模具自制，非常规尺寸打样一般只多几天。</p>
            <p>定制品翻车最多的环节是颜色。正确流程：潘通或实物参考 → 在真实基材上出小色片（TPE 和 PU 显色不同，绝不用屏幕稿确认）→ 确认后锁进封样，量产逐站比对。三条诚实的限制：3mm 以下附着力和缓冲都受损；122cm 以上宽度需要专线；照片级满版印花适合 PU 不适合 TPE。</p>
            <p>一页纸规格书发过来，7 天内给到报价 + 实物样品，样品确认即封样，大货对标封样。</p>
          </div>""",
"7day-sampling": """<div class="post-meta">速度 · 7 分钟 · 更新于 2026 年 9 月</div>
          <h1>7 天打样：快，为什么是自有品牌的核心优势</h1>
          <p class="lead-p">一周一轮的打样周期，决定你能多快上市、能测几版设计、以及带着多少风险进大货。这篇拆解 7 天样品里到底有什么、每天在做什么、什么会拖慢它。</p>
          <img class="article-cover" src="../assets/img/tpe-foldable-1.webp" width="480" height="480" loading="lazy" alt="可折叠 TPE 瑜伽垫样品" />
          <div class="article-body">
            <p>7 天样品是量产代表性样品：你的颜色、你的 Logo（压印/印刷/激光）、你的包装选项，确认规格后一周内寄出。能做到，是因为材料当天从库存调拨、样品在量产线上跑而不是实验室压机、模具自制。</p>
            <p>时间线：D1 锁规格调材料 → D2–3 产线发泡裁切 → D4 Logo 工艺+QC → D5 包装稿+照片集提前反馈 → D6–7 打包发快递。快的价值在复利：一轮一周，你才测得起三个配色方向；7 月打样的品牌 9 月上架，9 月才打样的直接错过季度。</p>
            <p>首样免费或在大货订单中抵扣。拖慢打样的三件事：色样不明确、Logo 不是矢量稿、包装方案悬而不决。反馈要给数字（厚度毫米数、色号、Logo 距边距），工厂执行得了数字，执行不了"再高级一点"。</p>
          </div>""",
"yoga-mat-spec-guide": """<div class="post-meta">规格 · 8 分钟 · 更新于 2026 年 9 月</div>
          <h1>瑜伽垫厚度与尺寸指南：怎么写一张垫子的规格（2026）</h1>
          <p class="lead-p">厚度、长度、宽度、密度是定义一张瑜伽垫的四个数字，也是采购后悔最集中的四个地方。这篇把每个规格对应到它真正适合的练习方式。</p>
          <img class="article-cover" src="../assets/img/tpe-mat-1.webp" width="480" height="480" loading="lazy" alt="不同厚度的瑜伽垫" />
          <div class="article-body">
            <p>厚度：3mm 旅行/平衡，4–5mm 通用标准，6mm 新手和敏感关节，8–15mm 普拉提/康复/儿童垫。8mm 以上站姿平衡明显变难——垫子在脚下压缩，不是越厚越好。长度：183cm 适合身高 180cm 以下，公式是身高 + 约 10cm 余量；北欧、荷兰这类高个市场，标准长目录在悄悄排除你最高的客户。</p>
            <p>宽度：61cm 标准、80cm 加宽、122cm 双人宽。密度是最常被漏写的规格：同标 6mm 的两张垫，材料量可以差 30%。双层 6mm TPE（183×61cm）基准克重约 1.1kg——规格书里写死克重和公差（我们厚度 ±0.3mm、长宽 ±1mm），量产样上秤复核。文内含厚度选择表、按用途规格表和公制英制对照表。</p>
          </div>""",
"compliance": """<div class="post-meta">合规 · 8 分钟 · 更新于 2026 年 9 月</div>
          <h1>REACH、加州 65 号提案与 6P：欧美瑜伽垫合规规则</h1>
          <p class="lead-p">进美国或欧盟市场，就要过化学品安全这一关——而多数采购是在零售商或海关要文件时才第一次面对它。这篇讲清真正会被要求检测什么、有效报告长什么样、合规怎么一批一批守得住。</p>
          <img class="article-cover" src="../assets/img/certification-wall.webp" width="1429" height="2004" loading="lazy" alt="瑜伽垫认证墙：ISO 9001、BSCI、SGS、REACH" />
          <div class="article-body">
            <p>美国：加州 65 号提案是警告标签制度（不是禁令），采购实操是按 6P/7P 邻苯清单筛查——DEHP、DBP、BBP、DINP、DIDP、DNOP（7P 加 DnHP）。需要塑化剂的正是 PVC，这就是欧美消费品牌撤离 PVC 的化学原因。欧盟：REACH 管的是 SVHC 高关注物质清单，每年更新两次左右，两年前的申报不等于今年的申报。</p>
            <p>有效报告 60 秒核查三件事：品名对应你的 SKU、检测样品对应你的材质和颜色（颜料正是受限物常见来源）、日期在 12 个月有效期内。合规出问题都出在配方悄悄漂移：我们配方上锁、批次可追溯，SVHC 清单更新影响到的批次在出货前就标红。三梵随单提供第三方检测报告、符合性声明、MSDS 和批次追溯记录，要全套文件不发摘要。</p>
          </div>""",
}


def stats(html):
    txt = re.sub(r"&\w+;", " ", re.sub(r"<[^>]+>", " ", html))
    return len(txt.split())


def fix_one(slug, meta, en):
    p = os.path.join(ROOT, "blog", slug + ".html")
    s = open(p, encoding="utf-8").read()
    orig = s

    # 1) 替换 lang-en 块
    i = s.find('<div class="lang-en">')
    j = s.find('<div class="lang-zh">')
    assert 0 < i < j, slug + " 结构异常"
    s = s[:i] + en.strip("\n") + "\n        \n" + s[j:]

    # 2) 替换 zh 摘要
    z = ZH[slug]
    s = re.sub(r'(<div class="lang-zh">).*?(</div>\s*</section>)',
               lambda m: m.group(1) + "\n          " + z.strip("\n") + "\n        " + m.group(2),
               s, count=1, flags=re.S)

    # 3) 老 head 补 GA
    if "googletagmanager" not in s:
        s = s.replace("</head>", GA + "</head>", 1)

    if not DRY:
        open(p, "w", encoding="utf-8").write(s)
    print("%-28s EN %4d -> %4d 词 | div平衡 %s | GA %s" % (
        slug, stats(orig), stats(s),
        "OK" if s.count("<div") == s.count("</div>") else "❌ 不平衡",
        "有" if "googletagmanager" in s else "无"))


def main():
    for slug, (meta, en) in POSTS.items():
        fix_one(slug, meta, en)
    # blog.html 索引页补 GA（同样无统计）
    p = os.path.join(ROOT, "blog.html")
    s = open(p, encoding="utf-8").read()
    if "googletagmanager" not in s:
        if not DRY:
            open(p, "w", encoding="utf-8").write(s.replace("</head>", GA + "</head>", 1))
        print("blog.html: +GA")


if __name__ == "__main__":
    main()
