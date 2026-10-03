// 客户视角 · 移动端实测探针（2026-10-03）
// 判据：① 320/390 横向溢出根因（定位到具体元素，不只报数字）
//       ② 询盘表单可用性：标签/必填/字号/按钮/错误与成功反馈（客户下单前的最后一关）
//       ③ 移动端首屏 CTA 可见性与点击路径深度
//       ④ 截图留证（桌面 1440 + 移动 390/320）
// 用法：node probe_customer_mobile_20261003.cjs --base=http://127.0.0.1:8873
const { chromium } = require('playwright');
const fs = require('fs');
const OUT = 'i18n_build/reports/';
const argv = process.argv.slice(2);
// ⚠️ 既支持 `--base URL` 也支持 `--base=URL`（2026-10-03 踩过：只认空格形式时，
// 传 `--base=...` 会静默回落到默认端口，表现为「整站 ERR_CONNECTION_REFUSED」——
// 看起来像服务器没起，其实是参数没进去）
const arg = (k, d) => {
  const i = argv.indexOf('--' + k);
  if (i >= 0) return argv[i + 1];
  const m = argv.find(a => a.startsWith('--' + k + '='));
  return m ? m.slice(('--' + k + '=').length) : d;
};
const BASE = arg('base', 'http://127.0.0.1:8873');

const PAGES = [
  { name: 'home-de',   url: '/de/index.html',                    vp: [390, 844] },
  { name: 'home-de-320', url: '/de/index.html',                  vp: [320, 568] },
  { name: 'home-en',   url: '/index.html',                       vp: [390, 844] },
  { name: 'contact',   url: '/contact.html',                     vp: [390, 844] },
  { name: 'product',   url: '/products/alignment-line-tpe-yoga-mat.html', vp: [390, 844] },
  { name: 'blog-de',   url: '/de/blog.html',                     vp: [390, 844] },
  { name: 'pilates',   url: '/pilates/pilates-reformer.html',    vp: [390, 844] },
];

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const report = [];

  for (const p of PAGES) {
    const page = await browser.newPage({ viewport: { width: p.vp[0], height: p.vp[1] }, deviceScaleFactor: 2 });
    let resp = null, navErr = null;
    try {
      resp = await page.goto(BASE + p.url, { waitUntil: 'networkidle', timeout: 45000 });
    } catch (e) {
      navErr = String(e).split('\n')[0];
    }
    if (navErr) console.log(`   ⚠ 导航失败: ${navErr}`);
    await page.waitForTimeout(700);

    const data = await page.evaluate(() => {
      const de = document.documentElement;
      const vw = de.clientWidth;
      const overflow = de.scrollWidth - vw;
      // ① 溢出根因：找出右边界超出视口的元素
      const offenders = [];
      if (overflow > 0) {
        document.querySelectorAll('body *').forEach(el => {
          const r = el.getBoundingClientRect();
          if (r.width === 0 || r.height === 0) return;
          if (r.right > vw + 1) {
            const cs = getComputedStyle(el);
            if (cs.position === 'fixed') return;
            offenders.push({
              sel: el.tagName.toLowerCase() + (el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : ''),
              right: Math.round(r.right), width: Math.round(r.width),
              text: (el.textContent || '').trim().slice(0, 40),
            });
          }
        });
      }
      // ② 首屏 CTA 与首屏信息量
      const ctas = Array.from(document.querySelectorAll('a.btn, button.btn, .btn, a[href*="contact"], .cbar a, .cbar button'));
      const firstScreen = ctas.filter(el => el.getBoundingClientRect().top < window.innerHeight);
      // ③ 固定/浮动元素（可能被遮挡）
      const fixedEls = Array.from(document.querySelectorAll('body *')).filter(el => {
        const cs = getComputedStyle(el);
        return (cs.position === 'fixed' || cs.position === 'sticky') && el.getBoundingClientRect().height > 0;
      }).map(el => {
        const r = el.getBoundingClientRect();
        return { sel: el.tagName.toLowerCase() + (typeof el.className === 'string' && el.className ? '.' + el.className.trim().split(/\s+/)[0] : ''),
                 z: getComputedStyle(el).zIndex, bottom: Math.round(r.bottom), h: Math.round(r.height) };
      });
      // ④ 字号过小（客户在手机上读不读得清）
      const tiny = [];
      document.querySelectorAll('p, li, td, th, dd, dt, span, a, button, label, figcaption').forEach(el => {
        if (!el.textContent || !el.textContent.trim()) return;
        if (el.children.length > 2) return;
        const fs2 = parseFloat(getComputedStyle(el).fontSize);
        if (fs2 > 0 && fs2 < 12) tiny.push({ sel: el.tagName.toLowerCase() + (typeof el.className === 'string' && el.className ? '.' + el.className.trim().split(/\s+/)[0] : ''), fs: fs2, text: el.textContent.trim().slice(0, 30) });
      });
      // ⑤ 图片缺 alt（客户看不到图 = 少了信息）
      const noAlt = Array.from(document.images).filter(i => !i.hasAttribute('alt')).length;
      return { vw, overflow, offenders: offenders.slice(0, 12), ctaTotal: ctas.length, ctaFirstScreen: firstScreen.length,
               fixedEls, tiny: tiny.slice(0, 10), tinyCount: tiny.length, imgTotal: document.images.length, noAlt };
    });

    // 表单专项（只在 contact 页做）
    let form = null;
    if (p.name === 'contact') {
      form = await page.evaluate(() => {
        const f = document.querySelector('form');
        if (!f) return { has: false };
        const fields = Array.from(f.querySelectorAll('input, textarea, select')).map(el => {
          const lab = el.labels && el.labels[0] ? el.labels[0].textContent.trim().slice(0, 40) : null;
          return { tag: el.tagName.toLowerCase(), type: el.type, name: el.name, required: el.required,
                   label: lab, placeholder: el.placeholder || null,
                   fontSize: parseFloat(getComputedStyle(el).fontSize),
                   ariaLabel: el.getAttribute('aria-label') };
        });
        const btn = f.querySelector('button[type=submit], input[type=submit]');
        return { has: true, action: f.action, method: f.method, fields,
                 submitText: btn ? btn.textContent.trim() : null,
                 submitRect: btn ? btn.getBoundingClientRect().height : null,
                 hasHoneypot: !!f.querySelector('input[name*=hp], .hp, [aria-hidden=true] input') };
      });
    }

    const line = `│ ${p.name.padEnd(13)} ${String(p.vp[0]).padStart(3)}px  HTTP ${resp ? resp.status() : 'ERR'}  溢出 ${String(data.overflow).padStart(3)}px  首屏CTA ${data.ctaFirstScreen}/${data.ctaTotal}  小字(<12px) ${data.tinyCount}  图缺alt ${data.noAlt}/${data.imgTotal}`;
    console.log(line);
    if (data.offenders.length) {
      console.log(`   └ 溢出元素: ${data.offenders.map(o => `${o.sel}(right=${o.right},w=${o.width})`).join('  ')}`);
    }
    if (data.tiny.length) console.log(`   └ 小字: ${data.tiny.map(t => `${t.sel}=${t.fs}px"${t.text}"`).slice(0,5).join('  ')}`);
    if (data.fixedEls.length) console.log(`   └ 固定层: ${data.fixedEls.map(f => `${f.sel}(z=${f.z},bottom=${f.bottom})`).join('  ')}`);
    if (form) {
      console.log(`   └ 表单 action=${form.action} method=${form.method} honeypot=${form.hasHoneypot}`);
      console.log(`   └ 提交按钮「${form.submitText}」高度 ${form.submitRect}px`);
      for (const fld of (form.fields || [])) {
        console.log(`     · ${fld.tag}/${fld.type}${fld.required ? '*' : ' '} 字号${fld.fontSize}px  label=${fld.label ? '「' + fld.label + '」' : (fld.ariaLabel ? 'aria「' + fld.ariaLabel + '」' : '❌ 无')}`);
      }
    }
    report.push({ page: p.name, vp: p.vp, status: resp ? resp.status() : null, ...data, form });

    await page.screenshot({ path: OUT + `cust_${p.name}_${p.vp[0]}_20261003.png`, fullPage: false });
    await page.close();
  }
  await browser.close();
  fs.writeFileSync(OUT + 'customer_mobile_20261003.json', JSON.stringify(report, null, 1));
  console.log('\n报告已写 ' + OUT + 'customer_mobile_20261003.json');
})();
