// 页内视觉/健康验证：横向溢出 + 控制台 error + 资源 4xx + 卡片新体系是否生效
// 用法: NODE_PATH=<workspace>/node_modules node i18n_build/verify_pages.cjs
const { chromium } = require('playwright');
const path = require('path');

const ROOT = process.cwd();
const PAGES = [
  'index.html', 'products.html', 'tpe-yoga-mats.html',
  'products/ym1.html', 'de/index.html', 'de/products.html',
];
const VIEWPORTS = [
  { name: 'desktop', width: 1440, height: 900 },
  { name: 'mobile', width: 390, height: 844 },
];

// 期望值（与 styles.css 的 --paper / card 规则一致）
const PAPER = 'rgb(249, 247, 242)';   // --paper #f9f7f2
const PAPER2 = 'rgb(242, 238, 230)';  // --paper-2 #f2eee6

(async () => {
  const browser = await chromium.launch();
  for (const vp of VIEWPORTS) {
    const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
    console.log(`\n===== ${vp.name} ${vp.width}x${vp.height} =====`);
    for (const rel of PAGES) {
      const page = await ctx.newPage();
      const errors = [];
      const bad = [];
      page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text().slice(0, 120)); });
      page.on('pageerror', (e) => errors.push('pageerror: ' + String(e).slice(0, 120)));
      page.on('response', (r) => { if (r.status() >= 400) bad.push(`${r.status()} ${r.url().split('/').pop()}`); });

      await page.goto('file://' + path.join(ROOT, rel), { waitUntil: 'load' });
      await page.waitForTimeout(400);

      const info = await page.evaluate(() => {
        const de = document.documentElement;
        const over = de.scrollWidth - window.innerWidth;
        const offenders = [];
        if (over > 1) {
          for (const el of document.querySelectorAll('body *')) {
            const r = el.getBoundingClientRect();
            if (r.right > window.innerWidth + 1 && r.width > 30) {
              offenders.push(`${el.tagName.toLowerCase()}.${(el.className || '').toString().split(' ')[0]} right=${Math.round(r.right)}`);
              if (offenders.length >= 5) break;
            }
          }
        }
        const card = document.querySelector('.prod-card, .range-card, .cat-tile, .g-item');
        const cs = card ? getComputedStyle(card) : null;
        const img = card ? card.querySelector('img') : null;
        const ics = img ? getComputedStyle(img) : null;
        const ph = card ? card.querySelector('.ph, .rc-img, .ct-img') : null;
        const pcs = ph ? getComputedStyle(ph) : null;
        const h4 = document.querySelector('.prod-card .info h4, .range-card h3, .g-item .meta .n');
        const h4s = h4 ? getComputedStyle(h4) : null;
        return {
          over, offenders, sw: de.scrollWidth, iw: window.innerWidth,
          cards: document.querySelectorAll('.prod-card').length,
          cardBg: cs ? cs.backgroundColor : null,
          cardBorder: cs ? cs.borderTopWidth : null,
          cardRadius: cs ? cs.borderTopLeftRadius : null,
          blend: ics ? ics.mixBlendMode : null,
          fit: ics ? ics.objectFit : null,
          phBg: pcs ? pcs.backgroundColor : null,
          phLine: pcs ? pcs.boxShadow : null,
          h4Weight: h4s ? h4s.fontWeight : null,
          h4After: h4 ? getComputedStyle(h4, '::after').content : null,
        };
      });

      const okOver = info.over <= 1;
      const okPaper = !info.cardBg || info.cardBg === PAPER;
      const okBorder = !info.cardBorder || info.cardBorder === '0px';
      const okBlend = !info.blend || info.blend === 'multiply';
      const flags = [okOver, okPaper, okBorder, okBlend].every(Boolean) ? '✅' : '❌';
      console.log(`  ${flags} ${rel.padEnd(22)} 溢出=${info.over}px 产品卡${info.cards}`);
      console.log(`      卡片底=${info.cardBg}${okPaper ? '' : ' ❌期望' + PAPER}  描边=${info.cardBorder}  圆角=${info.cardRadius}`);
      console.log(`      图 blend=${info.blend}${okBlend ? '' : ' ❌'}  fit=${info.fit}  图区底=${info.phBg}  inset影=${info.phLine}`);
      console.log(`      品名字重=${info.h4Weight}  h4::after=${info.h4After}`);
      if (info.offenders.length) console.log(`      溢出元素: ${info.offenders.join(' | ')}`);
      if (errors.length) console.log(`      ⚠️ 控制台 error ${errors.length}: ${errors.slice(0, 3).join(' ;; ')}`);
      if (bad.length) console.log(`      ⚠️ 资源 4xx/5xx ${bad.length}: ${[...new Set(bad)].slice(0, 4).join(' ;; ')}`);
      await page.close();
    }

    // 中文态：品名字重应升到 600
    console.log(`  --- 中文态检查 (${vp.name}) ---`);
    for (const rel of ['tpe-yoga-mats.html', 'products.html']) {
      const page = await ctx.newPage();
      await page.goto('file://' + path.join(ROOT, rel), { waitUntil: 'load' });
      await page.evaluate(() => document.documentElement.classList.add('show-zh'));
      await page.waitForTimeout(350);
      const zh = await page.evaluate(() => {
        const el = document.querySelector('.prod-card .info h4, .cat-tile .ct-body h3');
        const cs = el ? getComputedStyle(el) : null;
        const over = document.documentElement.scrollWidth - window.innerWidth;
        return { w: cs ? cs.fontWeight : null, over, txt: el ? el.textContent.trim().slice(0, 20) : null };
      });
      console.log(`      ${zh.w === '600' ? '✅' : '⚠️'} ${rel.padEnd(22)} 品名字重=${zh.w} 溢出=${zh.over}px  示例「${zh.txt}」`);
      await page.close();
    }
    await ctx.close();
  }
  await browser.close();
  console.log('\n验证结束');
})();
