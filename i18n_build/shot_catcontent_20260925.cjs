#!/usr/bin/env node
/**
 * 本轮分类页「三块内容」可视验收截图（2026-09-25）
 *
 * 截图产出到 outputs/catcontent-preview/（已加 .gitignore，不入库）
 * 用法：node shot_catcontent_20260925.cjs
 */
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE = 'http://127.0.0.1:8851';
const OUT = path.resolve(__dirname, '..', 'outputs', 'catcontent-preview');
fs.mkdirSync(OUT, { recursive: true });

const CASES = [
  // [输出名, 路径, 视口宽, 是否展开 FAQ, 可选锚点滚动选择器]
  ['01-en-foam-rollers-1440', 'foam-rollers.html', 1440, false, null],
  ['02-en-foam-rollers-390', 'foam-rollers.html', 390, false, null],
  ['03-en-foam-rollers-faq-open', 'foam-rollers.html', 1440, true, 'details.faq-item'],
  ['04-de-resistance-bands-1440', 'de/resistance-bands.html', 1440, false, null],
  ['05-ja-massage-recovery-1440', 'ja/massage-recovery.html', 1440, false, null],
  ['06-ko-strength-training-1440', 'ko/strength-training.html', 1440, false, null],
  ['07-fr-yoga-props-1440', 'fr/yoga-props-accessories.html', 1440, false, null],
  ['08-es-suede-cork-390', 'es/suede-cork-yoga-mats.html', 390, false, null],
  ['09-en-zh-toggle-jump-ropes', 'jump-ropes.html', 1440, false, 'ZH'],
];

(async () => {
  const b = await chromium.launch();
  for (const [name, rel, vw, openFaq, anchor] of CASES) {
    const p = await b.newPage({ viewport: { width: vw, height: 1000 } });
    await p.goto(`${BASE}/${rel}`, { waitUntil: 'domcontentloaded' });
    await p.addStyleTag({ content: 'html{scroll-behavior:auto !important}' });
    if (anchor === 'ZH') {
      await p.evaluate(() => { localStorage.setItem('siteLang', 'zh'); document.cookie = 'siteLang=zh; path=/'; });
      await p.reload({ waitUntil: 'domcontentloaded' });
    }
    await p.waitForTimeout(260);
    if (openFaq) {
      await p.evaluate(() => { document.querySelectorAll('details.faq-item')[0].open = true; });
      await p.waitForTimeout(120);
    }
    // 定位：默认滚到导语块；展开 FAQ 的那张要滚到 FAQ 列表，否则拍出来和 01 同图
    await p.evaluate((toFaq) => {
      const s = toFaq
        ? (document.querySelector('.faq-list') || {}).closest?.('section')
        : document.querySelector('section .section-head');
      if (s) s.scrollIntoView({ block: 'start' });
    }, openFaq);
    await p.waitForTimeout(150);
    await p.screenshot({ path: path.join(OUT, name + '.png') });
    console.log('  ✓', name + '.png', `${vw}px`, rel);
    await p.close();
  }
  await b.close();
  console.log('\n截图目录：outputs/catcontent-preview/');
})();
