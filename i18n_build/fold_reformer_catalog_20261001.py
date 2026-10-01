#!/usr/bin/env python3
"""pilates-reformer.html 画册长列表折叠改造（渐进增强）。

设计（2026-10-01，用户批准的「①+②」按数据修正版）：
- 27 个画册单元的三条线（AL/FOLD/WOOD）在画册里交错排列，且 p25 是混合页
  → 不按线分组重排，改为**整区折叠 + 线别跳转 chips**：
  · HTML 里画册区包进 <div class="cat-fold-body" id="cat-all">（默认可见）
  · 控制条 .cat-fold-bar 带 hidden 属性（无 JS 不可见、不挡路）
  · main.js 加载后才加 .is-folded 折叠 —— 无 JS/爬虫看到完整内容，SEO/GEO 零影响
- chips：AL→cat-p04 / Fold→cat-p11 / Wood→cat-p19（各线第一个单元），点击自动展开再滚动

用法：python fold_reformer_catalog_20261001.py [--restore]
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "pilates/pilates-reformer.html"
BACKUP = ROOT / "outputs/pilates_rebuild_20261001/_backup/pilates-reformer.fold.bak"

FIRST_UNIT = '      <div class="cat-unit" id="cat-p04">'
LAST_TAIL = '      </div>\n    </div>\n  </section>\n\n  <section class="section" id="models-compared">'

BAR = '''      <div class="cat-fold-bar" hidden>
        <button type="button" id="cat-fold-toggle" class="btn btn-primary cat-fold-toggle" aria-expanded="false" aria-controls="cat-all">
          <span class="lang-en">Browse the catalogue — 27 pages, 46 models</span><span class="lang-zh">浏览画册 —— 27 页 · 46 台</span>
        </button>
        <nav class="cat-fold-chips" aria-label="Jump to a product line">
          <a href="#cat-p04" class="cat-chip" data-jump><span class="lang-en">AL aluminium</span><span class="lang-zh">AL 铝合金</span></a>
          <a href="#cat-p11" class="cat-chip" data-jump><span class="lang-en">Foldable</span><span class="lang-zh">可折叠</span></a>
          <a href="#cat-p19" class="cat-chip" data-jump><span class="lang-en">Solid wood</span><span class="lang-zh">实木</span></a>
          <a href="#models-compared" class="cat-chip"><span class="lang-en">Spec table</span><span class="lang-zh">规格对比表</span></a>
        </nav>
      </div>

'''

FOLD_BODY_OPEN = '      <div class="cat-fold-body" id="cat-all">\n'
FOLD_BODY_CLOSE = '      </div><!-- /cat-fold-body -->\n'


def counts(h: str):
    return (h.count('class="cat-unit"'), h.count('class="model-card"'),
            h.count("<div"), h.count("</div>"))


def apply(h: str) -> str:
    assert 'cat-fold-bar' not in h, "已应用过（发现 cat-fold-bar），勿重复运行"
    assert h.count(FIRST_UNIT) == 1, "cat-p04 开头定位失败"
    assert h.count(LAST_TAIL) == 1, "section 收尾定位失败"
    c0 = counts(h)

    # ① 控制条：插在第一个画册单元前
    h = h.replace(FIRST_UNIT, BAR + FOLD_BODY_OPEN + FIRST_UNIT, 1)
    # ② 折叠体收口：最后一个单元的 </div> 之后补折叠体闭合
    h = h.replace(LAST_TAIL, '      </div>\n' + FOLD_BODY_CLOSE + '    </div>\n  </section>\n\n  <section class="section" id="models-compared">', 1)

    c1 = counts(h)
    # 断言：单元/卡数不变；div 开闭增量配平（bar 的 div + fold body 各 1 对 = 开闭各 +2）
    assert c1[0] == c0[0] == 27, f"cat-unit {c0[0]}→{c1[0]}"
    assert c1[1] == c0[1] == 46, f"model-card {c0[1]}→{c1[1]}"
    assert c1[2] - c0[2] == c1[3] - c0[3], \
        f"div 不配平：开 {c0[2]}→{c1[2]}，闭 {c0[3]}→{c1[3]}"
    return h


def main():
    if "--restore" in sys.argv:
        assert BACKUP.exists(), f"无备份：{BACKUP}"
        shutil.copy(BACKUP, PAGE)
        print(f"已从备份还原：{BACKUP}")
        return
    h = PAGE.read_text(encoding="utf-8")
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    if not BACKUP.exists():
        shutil.copy(PAGE, BACKUP)
        print(f"备份：{BACKUP}")
    out = apply(h)
    PAGE.write_text(out, encoding="utf-8")
    print(f"落盘：{PAGE}")
    # 复核：再次读取应能检测到已应用（重跑守卫生效）且结构计数正确
    done = PAGE.read_text(encoding="utf-8")
    assert 'cat-fold-bar' in done and 'cat-fold-body' in done
    assert counts(done)[0] == 27 and counts(done)[1] == 46
    print("复核 ✓（重跑会被守卫拦截，不产生重复结构）")


if __name__ == "__main__":
    main()
