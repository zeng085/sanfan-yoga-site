# -*- coding: utf-8 -*-
"""普拉提器械博客内容（第 4–6 篇）。事实口径同 a 模块。
⚠️ 数据源 CSV 里含「Gyrotonic」一行（站点已按商标要求剔除）——本模块禁止引用。
⚠️ 梯桶 21-FO / 20-V5 属跨线复用后缀（画册贴错页，已定案），博客表格不使用该两行。
"""

POSTS = [
    # ------------------------------------------------------------------ 4
    dict(
        slug="oem-pilates-equipment-china",
        tag="Sourcing",
        read="13 min read",
        updated="Oct 2026",
        cover="../assets/img/factory-building.webp",
        alt="SANFAN factory building in Jinjiang, Fujian",
        title="Sourcing Pilates Equipment from China: OEM vs ODM",
        desc="How to brief a Chinese Pilates equipment factory: spec sheet fields, sample approval, packing checks, documents and the mistakes that cause disputes.",
        h1="Sourcing Pilates Equipment from China: OEM vs ODM and the QC Gates",
        lead_en="""The difference between a smooth Pilates equipment programme and an expensive one
        is rarely the factory's capability — it is the quality of the brief and the gates you set.
        This is the specification and inspection workflow we run, written so you can demand the
        same from any supplier.""",
        lead_zh="""普拉提器械项目顺不顺，很少取决于工厂能力，而取决于需求书写得好不好、
        以及你设了几个关卡。这篇是我们自己跑的规格与验货流程，写给采购方 ——
        你可以用同一套标准去要求任何供应商。""",
        body_en="""
<h2>OEM vs ODM — the practical difference</h2>
<p><b>ODM</b> means you take a proven model from a factory's range and apply controlled
customisation: frame colour, upholstery, branding, packaging. <b>OEM</b> means the factory builds
to your own drawing and specification. ODM gets you to market fastest and keeps tooling costs at
zero; OEM gives full control and usually needs a complete technical brief plus larger volumes.
Most equipment programmes start ODM and switch to OEM on the hero model — the one that sells.</p>

<h2>The spec sheet: the eleven fields that prevent disputes</h2>
<p>A one-line email is not a specification. The brief that survives production contains:</p>
<ul>
  <li>Model name and catalogue page, taken from the <a href="../pilates/index.html">range</a>.</li>
  <li>Quantity per model and per finish.</li>
  <li>Frame colour, by swatch or pantone reference.</li>
  <li>Upholstery colour and texture, plus the cleaning regime the end user will apply.</li>
  <li>Branding method and position (plate, stitched label, frame print, packaging print).</li>
  <li>Artwork files, in vector, with the exact size on the machine in millimetres.</li>
  <li>Packing configuration: which packing size applies (A or B where the catalogue lists both).</li>
  <li>Carton marking layout, including model name and destination port marks.</li>
  <li>Destination port and Incoterm, so freight and documents are planned from the start.</li>
  <li>Sample approval route: who signs, and on what date.</li>
  <li>Inspection plan: what gets checked, and the defect thresholds that trigger a rework.</li>
</ul>

<h2>Read the packing list like a logistics plan</h2>
<p>Equipment crates are long and flat, and the numbers are published per model — use them before
you commit. A few entries from the 2026 catalogue, exactly as printed:</p>
<table class="cap-table">
  <thead><tr><th>Model</th><th>Packing size A</th><th>Packing size B</th><th>Gross weight</th></tr></thead>
  <tbody>
    <tr><td>AL 8-Y</td><td>2570 × 750 × 470 mm</td><td>—</td><td>140 kg</td></tr>
    <tr><td>AL 12-CR</td><td>2400 × 690 × 860 mm</td><td>—</td><td>—</td></tr>
    <tr><td>AL 21-mini pro</td><td>2210 × 640 × 300 mm</td><td>800 × 510 × 710 mm</td><td>120 kg</td></tr>
    <tr><td>Fold 9-CA</td><td>1150 × 700 × 370 mm</td><td>720 × 450 × 270 mm</td><td>65 kg</td></tr>
    <tr><td>Maple Cadillac</td><td>2470 × 860 × 330 mm</td><td>—</td><td>135 kg</td></tr>
    <tr><td>Chair 1-A</td><td>920 × 720 × 790 mm</td><td>—</td><td>65 kg</td></tr>
  </tbody>
</table>
<p>Three checks worth doing at quotation stage: <b>container maths</b> (how many crates per
loading plan, and whether the long boxes stack without crushing the short ones),
<b>access maths</b> (does the longest crate pass the buyer's door and corridor), and
<b>weight maths</b> (a 220 kg case needs a route and equipment, not just a courier). These are
the three things that turn a good quote into a bad delivery.</p>

<h2>Sampling: what a sample is for</h2>
<p>A sample is not a gift — it is the contract in physical form. Approve it in writing with
photos, and specify what happens if bulk differs. On equipment samples we check, at minimum:</p>
<ul>
  <li>Rail straightness and carriage travel over the full range, by hand.</li>
  <li>Colour match to the approved swatch in daylight.</li>
  <li>Upholstery seam quality and how the cover meets the frame.</li>
  <li>Label and carton marking against the written model list.</li>
  <li>Packing: does it match the configuration in the specification?</li>
</ul>
<p>Model-name discipline deserves its own line. In a large range, two product lines can carry
similar model suffixes — if the label, the packing list and the catalogue page are not checked
against each other, a container can arrive with the right quantity of the wrong model. Our own
2026 range had exactly this issue between two lines at source, and we resolved it by publishing a
single model table per family; ask your supplier for the same single source of truth.</p>

<h2>Documents to require before the deposit leaves</h2>
<p>Ask for the documents in the same message as the quotation — the answer tells you a lot about
the factory:</p>
<ul>
  <li>Signed golden-sample report with photos and the approved swatch reference.</li>
  <li>Packing list with per-model dimensions, gross weight and carton marks.</li>
  <li>Loading plan, container by container.</li>
  <li>Inspection plan with defect thresholds and who signs off.</li>
  <li>Spare-part list for the models ordered, with a reorder path.</li>
</ul>
<p>The <a href="vet-factory.html">factory vetting checklist</a> covers the audit side, and
<a href="custom-sizes.html">custom sizes and specifications</a> covers the drawing side.</p>

<h2>Common failure modes, ranked</h2>
<table class="cap-table">
  <thead><tr><th>Failure</th><th>Root cause</th><th>Prevention</th></tr></thead>
  <tbody>
    <tr><td>Wrong model in one carton</td><td>Similar suffixes across lines</td><td>Single model table + carton mark check against it</td></tr>
    <tr><td>Colour drift between batches</td><td>Swatch never physically approved</td><td>Signed swatch in daylight, kept by both sides</td></tr>
    <tr><td>Crates that cannot be delivered</td><td>Longest box never measured against access</td><td>Access maths at quotation stage</td></tr>
    <tr><td>Missing spares after six months</td><td>No spare list in the PO</td><td>Spare-part list as a PO line item</td></tr>
    <tr><td>Disputed quality at arrival</td><td>No defect thresholds agreed</td><td>Written inspection plan with thresholds</td></tr>
  </tbody>
</table>

<h2>What to send us for a same-week answer</h2>
<p>Model name or family, quantity per model, destination port and the branding method. With
those four items we can answer with the packing maths, the container plan and the sampling
schedule — and you get comparable numbers from every supplier you ask, which is the real point
of a specification. Start from the <a href="../pilates/index.html">Pilates range overview</a> or
<a href="../contact.html">send the brief</a>.</p>
""",
        body_zh="""
<h2>OEM 与 ODM 的实际区别</h2>
<p><b>ODM</b>：你从工厂现有系列里选一款成熟型号，做受控的定制 —— 框架颜色、包覆面料、
品牌呈现、包装。<b>OEM</b>：工厂完全按你的图纸与规格制造。ODM 上市最快、没有开模成本；
OEM 掌控力最强，通常需要完整技术文件与更大的量。
多数器械项目的做法是：先用 ODM 起量，再把卖得最好的那款转成 OEM。</p>

<h2>规格书：能避免争议的十一个字段</h2>
<p>一封只有一句话的邮件不叫规格。能顺利走完生产的清单包括：</p>
<ul>
  <li>型号名与画册页码，取自<a href="../pilates/index.html">系列总览</a>。</li>
  <li>每个型号、每种饰面的数量。</li>
  <li>框架颜色：色样或色卡号。</li>
  <li>包覆面料颜色与手感，以及终端用户实际会用的清洁方式。</li>
  <li>品牌呈现方式与位置（铭牌、车缝标、框架印刷、包装印刷）。</li>
  <li>设计文件：矢量格式，并写明在机器上的实际尺寸（毫米）。</li>
  <li>包装形式：画册同时列出 A、B 两种尺寸时，注明用哪一种。</li>
  <li>外箱唛头版式，含型号名与目的港唛。</li>
  <li>目的港与贸易术语 —— 运费与单证从第一步就要一起规划。</li>
  <li>样品确认路径：谁签字、哪一天签。</li>
  <li>验货方案：查什么，以及触发返工的缺陷阈值。</li>
</ul>

<h2>把装箱单当成物流方案来读</h2>
<p>器械木箱又长又扁，而每个型号的数据都是公布的 —— 在定稿前先用起来。
以下直接摘自 2026 画册：</p>
<table class="cap-table">
  <thead><tr><th>型号</th><th>包装尺寸 A</th><th>包装尺寸 B</th><th>毛重</th></tr></thead>
  <tbody>
    <tr><td>AL 8-Y</td><td>2570 × 750 × 470 mm</td><td>—</td><td>140 kg</td></tr>
    <tr><td>AL 12-CR</td><td>2400 × 690 × 860 mm</td><td>—</td><td>—</td></tr>
    <tr><td>AL 21-mini pro</td><td>2210 × 640 × 300 mm</td><td>800 × 510 × 710 mm</td><td>120 kg</td></tr>
    <tr><td>Fold 9-CA</td><td>1150 × 700 × 370 mm</td><td>720 × 450 × 270 mm</td><td>65 kg</td></tr>
    <tr><td>Maple Cadillac</td><td>2470 × 860 × 330 mm</td><td>—</td><td>135 kg</td></tr>
    <tr><td>Chair 1-A</td><td>920 × 720 × 790 mm</td><td>—</td><td>65 kg</td></tr>
  </tbody>
</table>
<p>报价阶段就该做的三道计算：<b>柜量</b>（一个装载方案能装多少箱，长箱压短箱会不会压坏）、
<b>通道</b>（最长的箱子能不能过买家的门与走廊）、<b>重量</b>（220 公斤的箱子需要的是
搬运路线与设备，不是快递员）。这三件事决定了报价是好报价还是烂交付。</p>

<h2>打样：样品到底是干什么用的</h2>
<p>样品不是赠品，它是实体化的合同。要用书面 + 照片确认，并写明大货与样品不一致时怎么办。
器械样品至少查这几项：</p>
<ul>
  <li>轨道直线度与滑车全程手感。</li>
  <li>自然光下的颜色与确认色样是否一致。</li>
  <li>面料缝线质量、包覆与框架的衔接。</li>
  <li>铭牌与外箱唛头是否与书面型号清单一致。</li>
  <li>包装是否与规格书里的包装形式一致。</li>
</ul>
<p>型号命名这件事值得单列一条。大系列里，两条产品线可能带着相近的型号后缀 ——
如果铭牌、装箱单和画册页三者不交叉核对，一柜货就可能「数量对、型号错」。
我们自己的 2026 系列在源头就出现过这种问题，解决办法是每个家族只发布一张型号总表；
你也可以要求供应商提供同样的唯一数据源。</p>

<h2>打款前必须索要的文件</h2>
<p>把资料清单和询价放在同一封邮件里 —— 对方的回复本身就能说明很多：</p>
<ul>
  <li>双方签署、附照片的《黄金样品报告》与确认色样编号。</li>
  <li>装箱单：逐型号尺寸、毛重、外箱唛头。</li>
  <li>装柜方案：逐柜列明。</li>
  <li>验货方案：缺陷阈值与签核人。</li>
  <li>所订型号的备件清单与补货路径。</li>
</ul>
<p>工厂审核侧见<a href="vet-factory.html">验厂清单</a>，
图纸与规格侧见<a href="custom-sizes.html">定制尺寸与规格</a>。</p>

<h2>最常见的失败模式（按频次）</h2>
<table class="cap-table">
  <thead><tr><th>问题</th><th>根因</th><th>预防</th></tr></thead>
  <tbody>
    <tr><td>某一箱型号错</td><td>不同产品线后缀相近</td><td>唯一型号总表 + 唛头与总表交叉核对</td></tr>
    <tr><td>批次之间颜色漂移</td><td>色样从未实物确认</td><td>自然光下确认色样，双方各留一份</td></tr>
    <tr><td>箱子运不进场地</td><td>最长边从未与通道比对</td><td>报价阶段先做通道计算</td></tr>
    <tr><td>半年后没有备件</td><td>订单里没有备件行</td><td>备件清单作为独立订单行</td></tr>
    <tr><td>到货后质量争议</td><td>没有约定缺陷阈值</td><td>书面验货方案 + 阈值</td></tr>
  </tbody>
</table>

<h2>想当周拿到答复，发这几项就够</h2>
<p>型号名或家族、每型号数量、目的港、品牌呈现方式。有这四项，我们就能给出装箱计算、
装柜方案与打样排期 —— 你也能从所有供应商那里拿到可比的数字，这才是规格书的真正意义。
从<a href="../pilates/index.html">普拉提系列总览</a>开始，或直接
<a href="../contact.html">把需求发给我们</a>。</p>
""",
        faqs=[
            ("What is the difference between OEM and ODM for Pilates equipment?",
             "ODM means you choose a proven model from a factory's range and apply controlled "
             "customisation such as frame colour, upholstery, branding and packaging. OEM means the "
             "factory builds to your own drawing and specification. ODM gets you to market fastest with "
             "no tooling cost; OEM gives maximum control and needs a complete technical brief plus larger "
             "volumes. Many programmes run ODM first and convert the best-selling model to OEM."),
            ("What should a Pilates equipment specification include?",
             "Model name and catalogue page, quantity per model and finish, frame colour by swatch, "
             "upholstery colour and texture with the cleaning regime, branding method and position, vector "
             "artwork with exact placement size, the packing configuration that applies, carton marking "
             "layout, destination port and Incoterm, the sample approval route, and a written inspection "
             "plan with defect thresholds."),
            ("How do I avoid receiving the wrong model in a shipment?",
             "Insist on a single model table per family and check three places against it: the machine "
             "label, the packing list and the catalogue page. In large ranges two product lines can carry "
             "similar model suffixes, and that is the most common source of a wrong-model claim. Our own "
             "2026 range had this issue at source and was resolved by publishing one table per family."),
            ("Which documents should a factory provide before I pay a deposit?",
             "A signed golden-sample report with photos and the approved swatch reference, a packing list "
             "with per-model dimensions and carton marks, a container loading plan, a written inspection "
             "plan with defect thresholds, and a spare-part list for the models ordered with a reorder "
             "path. A factory that provides these without being pushed is a factory that can repeat the "
             "quality you approved."),
            ("How long does sampling take for Pilates equipment?",
             "Sampling is agreed against the locked specification, and the schedule depends on the model, "
             "the finish and the branding method. Send the model or family, the quantity, the destination "
             "port and the branding method and we will return a sampling and production schedule with the "
             "packing maths for your destination."),
        ],
    ),
    # ------------------------------------------------------------------ 5
    dict(
        slug="pilates-studio-layout-guide",
        tag="Studio Planning",
        read="10 min read",
        updated="Oct 2026",
        cover="../assets/img/pilates-reformer-tower-1.webp",
        alt="Pilates reformer tower in a training room",
        title="Pilates Studio Layout: Plan With Real Packing Sizes",
        desc="Plan a Pilates studio with published packing sizes: door and corridor clearance, storage, delivery access and a room sizing table.",
        h1="Pilates Studio Layout: Planning From the Packing List, Not the Photo",
        lead_en="""Almost every studio layout problem is really a delivery problem discovered late.
        Crates are longer than the machines look, doorways are narrower than anyone remembers, and
        220 kg does not negotiate stairs. Here is how to plan a room using the numbers that are
        already published for every model.""",
        lead_zh="""几乎所有的工作室布局问题，本质上都是「发现得太晚」的搬运问题。
        木箱比机器看上去更长，门比谁记得的都窄，而 220 公斤不会跟楼梯商量。
        这篇讲怎么用每个型号已经公布的装箱数据来做房间规划。""",
        body_en="""
<h2>Start with the crate, not the machine</h2>
<p>Every model in the 2026 catalogue carries a published packing size and gross weight. Those
two columns are the real planning data, because the crate is what has to arrive. Entries from the
published table, as printed:</p>
<table class="cap-table">
  <thead><tr><th>Model</th><th>Packing size A</th><th>Packing size B</th><th>Gross weight</th><th>Planning note</th></tr></thead>
  <tbody>
    <tr><td>AL 13 MC</td><td>2800 × 680 × 450 mm</td><td>—</td><td>120 kg</td><td>Longest crate in the range</td></tr>
    <tr><td>AL 8-Y</td><td>2570 × 750 × 470 mm</td><td>—</td><td>140 kg</td><td>The 2570 mm class — long and narrow</td></tr>
    <tr><td>Wood 1 A-3in 1</td><td>2570 × 810 × 740 mm</td><td>—</td><td>200 kg</td><td>Long and tall — needs height at the turn</td></tr>
    <tr><td>AL 12-CR</td><td>2400 × 690 × 860 mm</td><td>—</td><td>—</td><td>Deep crate at 860 mm — check door height, not only width</td></tr>
    <tr><td>AL 21-mini pro</td><td>2210 × 640 × 300 mm</td><td>800 × 510 × 710 mm</td><td>120 kg</td><td>Split packing option — small access friendly</td></tr>
    <tr><td>Fold 9-CA</td><td>1150 × 700 × 370 mm</td><td>720 × 450 × 270 mm</td><td>65 kg</td><td>Fits a lift or a small doorway</td></tr>
    <tr><td>AL 14-M3</td><td>1870 × 930 × 590 mm</td><td>1670 × 930 × 480 mm</td><td>220 kg</td><td>Widest crate — 930 mm is the binding dimension</td></tr>
    <tr><td>Maple Cadillac</td><td>2470 × 860 × 330 mm</td><td>—</td><td>135 kg</td><td>Long and flat — stacks well</td></tr>
    <tr><td>Chair 1-A</td><td>920 × 720 × 790 mm</td><td>—</td><td>65 kg</td><td>Palletised cube, not a long crate</td></tr>
    <tr><td>Ladder Barre 3</td><td>1190 × 700 × 1170 mm</td><td>—</td><td>90 kg</td><td>Tall at 1170 mm — plan vertical storage</td></tr>
    <tr><td>Wall Tower</td><td>2110 × 630 × 280 mm</td><td>—</td><td>100 kg</td><td>Wall-mounted option frees floor space</td></tr>
  </tbody>
</table>

<h2>The four clearances that decide whether the job runs</h2>
<ul>
  <li><b>Door width and height.</b> Compare against the crate's width and height, not its length.
  The widest crates in our range reach 930 mm.</li>
  <li><b>Corridor and stair turns.</b> The binding figure is the crate's longest side — up to
  2800 mm (AL 13 MC). A 2.8 m crate does not turn in a 1.2 m corridor.</li>
  <li><b>Lift capacity and internal dimensions.</b> Hotel and office floors are where split
  packing (a model with an A and a B configuration) earns its place.</li>
  <li><b>Floor loading and route protection.</b> Heavy flat crates concentrate load at the
  corners; plan protection for finished floors and lift thresholds.</li>
</ul>

<h2>Turn the floor plan into a station count</h2>
<p>Do this with tape on the floor, not with software. Mark the crate footprints where the units
will stand, mark the aisles your class actually uses, then count how many stations survive.
Three planning rules from rooms we have seen work:</p>
<ul>
  <li><b>Design for the class, not the room.</b> If your peak class is six, six stations plus
  clear access beats eight stations and a blocked aisle.</li>
  <li><b>Keep the vertical pieces against walls.</b> Ladder barrels and wall towers are tall —
  give them a wall and keep the middle of the room for floor equipment.</li>
  <li><b>Plan storage as part of the layout.</b> A machine with no home becomes an obstacle by
  month three. Folding models such as Fold 9-CA exist precisely to make that home possible.</li>
</ul>

<h2>Delivery day: a two-page plan that removes most surprises</h2>
<ul>
  <li>Per-model crate list with dimensions and weights, in the order they come off the truck.</li>
  <li>The route inside the building, marked with the narrowest point recorded in millimetres.</li>
  <li>Where empty crates go, and who removes them — this is the most common forgotten line.</li>
  <li>Assembly sequence: which units are assembled in the room rather than before delivery.</li>
  <li>Who signs for condition on arrival, with photos of any crate damage before opening.</li>
</ul>

<h2>Matching the equipment to the space</h2>
<p>Small rooms get the most out of equipment that integrates: a
<a href="../pilates/pilates-reformer-tower.html">reformer tower</a> carries vertical work in a
reformer footprint, and a <a href="../pilates/pilates-wunda-chair.html">Wunda chair</a> or
<a href="../pilates/pilates-ladder-barrel.html">ladder barrel</a> fills corners that no reformer
can use. Large rooms can afford a <a href="../pilates/pilates-cadillac.html">Cadillac</a>
station; the per-model packing data for the reformer lines is on the
<a href="../pilates/pilates-reformer.html">reformer page</a> under the specification table.</p>
<p>Two other guides pick up where this one stops: the
<a href="pilates-studio-equipment-list.html">opening equipment list</a> for what to buy, and
<a href="oem-pilates-equipment-china.html">sourcing guide</a> for how to specify the order so the
crates match the plan you just made.</p>
""",
        body_zh="""
<h2>先看木箱，再看机器</h2>
<p>2026 画册里每个型号都带公布的包装尺寸与毛重。这两列才是真正的规划数据 ——
因为必须先进场地的是箱子。以下直接摘自公布数据表：</p>
<table class="cap-table">
  <thead><tr><th>型号</th><th>包装尺寸 A</th><th>包装尺寸 B</th><th>毛重</th><th>规划提示</th></tr></thead>
  <tbody>
    <tr><td>AL 13 MC</td><td>2800 × 680 × 450 mm</td><td>—</td><td>120 kg</td><td>全系列最长的木箱</td></tr>
    <tr><td>AL 8-Y</td><td>2570 × 750 × 470 mm</td><td>—</td><td>140 kg</td><td>2570 mm 档 —— 长而窄</td></tr>
    <tr><td>Wood 1 A-3in 1</td><td>2570 × 810 × 740 mm</td><td>—</td><td>200 kg</td><td>又长又高 —— 转弯处要留高度</td></tr>
    <tr><td>AL 12-CR</td><td>2400 × 690 × 860 mm</td><td>—</td><td>—</td><td>860 mm 的深箱 —— 除宽度外还要看门高</td></tr>
    <tr><td>AL 21-mini pro</td><td>2210 × 640 × 300 mm</td><td>800 × 510 × 710 mm</td><td>120 kg</td><td>可分箱 —— 小通道友好</td></tr>
    <tr><td>Fold 9-CA</td><td>1150 × 700 × 370 mm</td><td>720 × 450 × 270 mm</td><td>65 kg</td><td>能进电梯或小门</td></tr>
    <tr><td>AL 14-M3</td><td>1870 × 930 × 590 mm</td><td>1670 × 930 × 480 mm</td><td>220 kg</td><td>最宽的箱 —— 930 mm 是卡点</td></tr>
    <tr><td>Maple Cadillac</td><td>2470 × 860 × 330 mm</td><td>—</td><td>135 kg</td><td>长而扁 —— 好码放</td></tr>
    <tr><td>Chair 1-A</td><td>920 × 720 × 790 mm</td><td>—</td><td>65 kg</td><td>托盘立方体，不是长箱</td></tr>
    <tr><td>Ladder Barre 3</td><td>1190 × 700 × 1170 mm</td><td>—</td><td>90 kg</td><td>1170 mm 的高箱 —— 规划竖向存放</td></tr>
    <tr><td>Wall Tower</td><td>2110 × 630 × 280 mm</td><td>—</td><td>100 kg</td><td>壁挂方案可释放地面</td></tr>
  </tbody>
</table>

<h2>决定项目顺不顺的四个净空</h2>
<ul>
  <li><b>门宽与门高。</b>和箱子的宽、高比，不是和长度比。我们系列里最宽的箱子达到 930 mm。</li>
  <li><b>走廊与楼梯转角。</b>卡点是箱子的最长边 —— 最长到 2800 mm（AL 13 MC）。
  2.8 米的箱子在 1.2 米走廊里转不过弯。</li>
  <li><b>电梯载重与内厢尺寸。</b>酒店与写字楼楼层，正是「可分箱包装（A/B 两种配置）」
  发挥价值的地方。</li>
  <li><b>楼板承重与动线保护。</b>重型扁箱把荷载集中在四角；
  成品地面与电梯门槛要提前做保护方案。</li>
</ul>

<h2>把平面图换算成工位数</h2>
<p>用胶带在地上比，不要用软件比。把器械木箱的占地标在它将要摆放的位置，
标出课堂实际使用的过道，然后数还剩几个工位。三条来自真实场馆的规划原则：</p>
<ul>
  <li><b>为课程设计，不为房间设计。</b>高峰班六人，六个工位加畅通动线，胜过八个工位加一条被堵死的过道。</li>
  <li><b>竖向器械贴墙放。</b>梯桶与壁挂塔架都很高 —— 给它们一面墙，
  把房间中间留给地面器械。</li>
  <li><b>把收纳算进布局。</b>没有「家」的器械，第三个月就会变成障碍物。
  折叠型号（如 Fold 9-CA）存在的意义，就是让这个「家」成为可能。</li>
</ul>

<h2>交付当天：两页纸的方案能消掉大部分意外</h2>
<ul>
  <li>逐型号木箱清单（尺寸、重量），按卸车顺序排列。</li>
  <li>楼内动线图，标出最窄处在多少毫米。</li>
  <li>空箱放哪、谁清运 —— 这是最常被忘掉的一条。</li>
  <li>装配顺序：哪些器械在房间内组装，而不是到货前组装。</li>
  <li>到货状态由谁签收，开箱前先拍木箱损伤照片。</li>
</ul>

<h2>按空间选器械</h2>
<p>小房间最划算的是「能整合功能」的器械：
<a href="../pilates/pilates-reformer-tower.html">核心床塔架</a>在一个核心床的占地里
提供垂直训练；<a href="../pilates/pilates-wunda-chair.html">稳踏椅</a>、
<a href="../pilates/pilates-ladder-barrel.html">梯桶</a>填的是核心床用不了的角落。
大房间才放得下<a href="../pilates/pilates-cadillac.html">凯迪拉克床</a>工位；
核心床线的逐型号装箱数据在<a href="../pilates/pilates-reformer.html">核心床页</a>的规格表里。</p>
<p>另外两篇接着本篇往下走：<a href="pilates-studio-equipment-list.html">开馆器械清单</a>
讲买什么，<a href="oem-pilates-equipment-china.html">采购指南</a>讲怎么把订单写清楚，
让你刚做的搬运方案与到货的木箱对得上。</p>
""",
        faqs=[
            ("How do I check whether a Pilates reformer will fit through my door?",
             "Compare the crate's cross-section — its width and height — against the doorway, not the machine's "
             "length. In our 2026 range the published crates reach 930 mm wide and 2000 mm tall, and run "
             "to 2800 mm on the longest side, so a standard 900 mm door is the first thing to verify: the "
             "widest crates are 30 mm wider than the door leaf. A crate that will not pass is not always a "
             "dead end — models listing both an A and a B packing size ship in a smaller second "
             "configuration."),
            ("What is the longest Pilates equipment crate?",
             "In our 2026 range the longest published packing length is 2800 mm — carried by AL 13 MC, with "
             "the 2570 mm class (AL 8-Y, Wood 1 A-3in 1) just behind it. That is the figure to use when checking corridor turns and "
             "stairwells. Crate length, not machine length, is what has to make the turn inside a building."),
            ("How much floor space does a Pilates studio need?",
             "Size the room by peak class, not by catalogue photos. Mark the crate footprints and the "
             "class aisles on the floor with tape and count the stations that remain usable. Six stations "
             "with clear access will out-earn eight stations with a blocked aisle, and vertical pieces "
             "such as ladder barrels and wall towers should be placed against walls."),
            ("Should Pilates equipment be assembled before or after delivery?",
             "Plan this per model. Flat, long crates usually mean partial assembly on site, which is why "
             "the delivery plan should list the assembly sequence and the tools required. Decide before "
             "the truck arrives which units are assembled outside the room and which go in as crates, "
             "because the answer changes the corridor route."),
            ("How do I plan storage for Pilates equipment in a small studio?",
             "Give every unit a defined home in the layout and prefer equipment that integrates functions "
             "— a reformer tower adds vertical work without a second footprint, and folding models such as "
             "Fold 9-CA pack to 1150 × 700 × 370 mm so they can live in a cupboard or against a wall."),
        ],
    ),
    # ------------------------------------------------------------------ 6
    dict(
        slug="pilates-equipment-commercial-use",
        tag="Commercial",
        read="11 min read",
        updated="Oct 2026",
        cover="../assets/img/pilates-wunda-chair-1.webp",
        alt="Wunda chair and Pilates apparatus in a commercial fitness room",
        title="Pilates Equipment for Gyms, Hotels & Clubs: Checklist",
        desc="Commercial Pilates equipment for gyms, hotels and clubs: selection criteria, fleet standardisation, cleaning, service access and spare parts to stock.",
        h1="Commercial Pilates Equipment: Buying for Gyms, Hotels and Clubs",
        lead_en="""A hotel does not buy the same way as a boutique studio, and a multi-site gym
        should not buy the way either of them does. In commercial settings the machine is the easy
        part — cleaning regimes, delivery routes, standardisation and spares decide whether the
        rollout works.""",
        lead_zh="""酒店买器械的方式和精品工作室不同，连锁健身房也不该照抄这两者。
        在商用场景里，机器是最简单的部分 —— 清洁方式、搬运动线、标准化与备件，
        才决定铺开能不能成。""",
        body_en="""
<h2>Start from usage, not from preference</h2>
<p>Three questions separate a commercial brief from a private one:</p>
<ul>
  <li><b>How many hours a day</b> will the unit be in use, and by trained staff or by members?</li>
  <li><b>Who cleans it</b>, with what, and how often? This decides upholstery specification more
  than aesthetics ever will.</li>
  <li><b>Who fixes it</b>, and how far away are they? Service access is a specification item, not
  a support-ticket afterthought.</li>
</ul>

<h2>Standardise the fleet, then vary the mix</h2>
<p>Multi-site operators should pick one reformer model and one vertical unit for the whole
estate, then add variety only where the room justifies it. A member moving between branches
should find the same machine under them — that consistency is worth more than a per-site optimum.
In our 2026 range the aluminium line (27 reformer models) is the usual base for this pattern,
because it is designed for shared, frequently moved equipment; the
<a href="../pilates/pilates-reformer.html">reformer page</a> lists every model with its published
packing size and gross weight so fleet planners can work from one table.</p>

<h2>Small rooms, tall crates: the hotel problem</h2>
<p>Hotels and office gyms are the hardest delivery environments: lifts, service corridors and
finished floors. Two things solve most of it at quotation stage:</p>
<ul>
  <li><b>Choose models with split packing.</b> Where the catalogue lists both an A and a B
  packing size, the smaller configuration is what gets a unit through a lift or a narrow service
  door. AL 21-mini pro, for example, packs at 2210 × 640 × 300 mm or 800 × 510 × 710 mm.</li>
  <li><b>Plan the route in millimetres.</b> The longest published crate in our range is
  2800 mm, and the widest 930 mm. Those two numbers decide the delivery plan before anyone
  negotiates price. The <a href="pilates-studio-layout-guide.html">layout guide</a> has the
  clearance checklist.</li>
</ul>

<h2>Cleaning and wear: specify for the regime, not the showroom</h2>
<p>Commercial cleaning is harsher than studio cleaning, and it is applied by people who are not
the end user. When you specify upholstery, state the cleaning product and frequency first, then
choose the colour and texture. On the frame side, remember that in multi-purpose fitness rooms
the most common damage is not wear — it is people leaning equipment against radiators, stacking
it badly, or dragging it. Specify how units are moved and stored, and who is allowed to move
them.</p>

<h2>Spares, service and the standardisation dividend</h2>
<table class="cap-table">
  <thead><tr><th>Item</th><th>Why commercial buyers order it at roll-out</th></tr></thead>
  <tbody>
    <tr><td>Spare-part list per model</td><td>One part failure should not sideline a station for a container cycle</td></tr>
    <tr><td>Consistent fasteners across the fleet</td><td>Site staff can service any unit with one toolkit</td></tr>
    <tr><td>Model table per family</td><td>Reorders and replacements match without photos by WhatsApp</td></tr>
    <tr><td>Packing list and loading plan</td><td>Site-by-site delivery without re-measuring each building</td></tr>
  </tbody>
</table>

<h2>Which apparatus, by venue type</h2>
<ul>
  <li><b>Gyms and fitness clubs:</b> reformer rows plus towers, with chairs and barrels in corner
  zones. See <a href="../applications/gyms-fitness-clubs.html">gyms &amp; fitness clubs</a>.</li>
  <li><b>Hotels, resorts and spas:</b> fewer units, better finish, tighter delivery constraints —
  choose split-packing models and plan lift access. See
  <a href="../applications/hotels-resorts-spas.html">hotels, resorts &amp; spas</a>.</li>
  <li><b>Boutique studios and franchises:</b> standardise one reformer plus one tower across all
  sites, then differentiate with chairs and barrels. See
  <a href="../applications/retail-private-label.html">retail &amp; private label</a>.</li>
</ul>

<h2>The commercial brief we answer fastest</h2>
<p>Send: venue type and number of sites, units per site, reformer model or family, destination
cities or ports, and the cleaning regime. With those five items we return a loading plan, a
delivery sequence and a spare-part list — the three documents that decide whether a rollout
opens on time. Start from the <a href="../pilates/index.html">Pilates range overview</a> or
<a href="../contact.html">send the brief</a>.</p>
""",
        body_zh="""
<h2>从使用出发，而不是从偏好出发</h2>
<p>三个问题把商用需求与私人需求分开：</p>
<ul>
  <li><b>每天用几小时</b>，使用者是受训员工还是会员？</li>
  <li><b>谁来清洁</b>、用什么清洁、多久一次？这比审美更能决定包覆面料的选型。</li>
  <li><b>谁来维修</b>，离得多远？服务可达性是规格项，不是出了工单才想的事。</li>
</ul>

<h2>先统一机队，再丰富组合</h2>
<p>连锁运营应在整个物业组合里选定同一款核心床和同一款垂直平面器械，
只在场地确实支撑得住时才做差异化。会员换一家店，脚下应该是同一台机器 ——
这种一致性比单店最优更值钱。我们 2026 系列里，铝合金线（27 个核心床型号）通常作为这种
模式的基座，因为它就是为「共用、频繁搬运」设计的；
<a href="../pilates/pilates-reformer.html">核心床页</a>列出每个型号公布的包装尺寸与毛重，
机队规划只需要看一张表。</p>

<h2>小房间、高箱子：酒店难题</h2>
<p>酒店与写字楼健身房是最难的交付环境：电梯、服务通道、成品地面。
两件事在报价阶段就能解决大半：</p>
<ul>
  <li><b>选可分箱包装的型号。</b>画册同时列出 A、B 两种包装尺寸时，
  较小的那种配置正是能把器械送进电梯或窄服务门的方案。例如 AL 21-mini pro
  包装为 2210 × 640 × 300 mm 或 800 × 510 × 710 mm。</li>
  <li><b>动线按毫米算。</b>我们系列里最长的木箱 2800 mm（AL 13 MC）、最宽的 930 mm。
  这两个数在谈价之前就决定了交付方案。清空清单见
  <a href="pilates-studio-layout-guide.html">布局与搬运指南</a>。</li>
</ul>

<h2>清洁与损耗：按实际清洁方式来选，而不是按展厅效果选</h2>
<p>商用清洁比工作室更「重」，而且操作的人往往不是终端用户。指定面料时，
先写明清洁剂与频次，再挑颜色与手感。框架方面要记住：
在多用途健身房里，最常见的损伤不是磨损 —— 而是把器械靠在暖气片上、乱码乱堆、或者拖行。
要同时指定器械怎么移动、怎么存放，以及谁有权移动它们。</p>

<h2>备件、服务与「标准化红利」</h2>
<table class="cap-table">
  <thead><tr><th>项目</th><th>为什么商用买家在铺开时就一起订</th></tr></thead>
  <tbody>
    <tr><td>逐型号备件清单</td><td>坏一个部件，不该让一个工位停一整个货柜周期</td></tr>
    <tr><td>全机队统一紧固件</td><td>门店员工用一套工具就能维护任何一台</td></tr>
    <tr><td>每家族一张型号总表</td><td>补货与替换不用靠微信发照片确认</td></tr>
    <tr><td>装箱单与装柜方案</td><td>逐店交付，不必为每栋楼重新量尺寸</td></tr>
  </tbody>
</table>

<h2>按业态选器械</h2>
<ul>
  <li><b>健身房与团课俱乐部：</b>核心床排加塔架，稳踏椅与梯桶放在角落区。
  见<a href="../applications/gyms-fitness-clubs.html">健身房与团课俱乐部</a>。</li>
  <li><b>酒店、度假村与 SPA：</b>数量少、质感高、交付限制多 ——
  选可分箱包装的型号，并预先规划电梯动线。见
  <a href="../applications/hotels-resorts-spas.html">酒店、度假村与 SPA</a>。</li>
  <li><b>精品工作室与加盟：</b>所有网点统一一款核心床加一款塔架，
  再用稳踏椅与梯桶做差异。见
  <a href="../applications/retail-private-label.html">零售与贴牌</a>。</li>
</ul>

<h2>我们回复最快的商用需求长什么样</h2>
<p>发来这五项：业态与网点数量、每店台数、核心床型号或家族、目的城市或港口、清洁方式。
有这五项，我们能给出装柜方案、交付顺序与备件清单 ——
这三份文件决定铺开能不能按时开业。从<a href="../pilates/index.html">普拉提系列总览</a>开始，
或直接<a href="../contact.html">把需求发给我们</a>。</p>
""",
        faqs=[
            ("What should a gym or hotel look for in commercial Pilates equipment?",
             "Gather information before preferences. How many hours a day the unit will run, who cleans "
             "it and with what, who services it and how far away they are, and how the delivery route "
             "reaches the room. Then standardise one reformer model and one vertical unit across sites, "
             "and choose split-packing models where lift and service corridors are tight."),
            ("How do hotels handle Pilates equipment delivery?",
             "By planning in millimetres and choosing the right packing configuration. Where the "
             "catalogue lists both an A and a B packing size, the smaller configuration is the one that "
             "passes a lift or narrow service door — AL 21-mini pro, for example, packs at 2210 × 640 × "
             "300 mm or 800 × 510 × 710 mm. The longest published crate in our range is 2800 mm, so the "
             "route must be measured before the order is placed."),
            ("Should a multi-site operator standardise on one reformer model?",
             "Yes. One reformer model and one vertical unit across all sites makes servicing, spares and "
             "reorders simpler, and it gives members a consistent experience when they switch branches. "
             "Add variety — chairs, barrels, a Cadillac station — only in rooms where the floor plan "
             "genuinely supports it."),
            ("What spare parts should a commercial buyer stock?",
             "Ask for a spare-part list per model and order it as a line item in the original purchase "
             "order. The parts that wear are small and inexpensive compared with a station sitting idle "
             "while a replacement crosses an ocean. Consistent fasteners across the fleet also let site "
             "staff service any unit with a single toolkit."),
            ("How do cleaning regimes affect Pilates equipment specification?",
             "They decide upholstery choice. State the cleaning product and frequency before choosing "
             "colour and texture, because commercial cleaning is applied by people who are not the end "
             "user and is harsher than studio cleaning. On the frame side, specify how units are moved "
             "and stored, since dragging and bad stacking cause more damage in shared fitness rooms than "
             "ordinary wear."),
        ],
    ),
]
