const {chromium} = require('playwright');
const path = require('path');

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({viewport: {width: 1440, height: 960}, deviceScaleFactor: 2});
  const url = 'file://' + path.join(process.cwd(), 'outputs/nav-guide/导航引导方案.html');
  await p.goto(url, {waitUntil: 'load'});
  await p.waitForTimeout(600);

  await p.screenshot({path: 'outputs/nav-guide/01-mega-menu.png', clip: {x: 0, y: 0, width: 1440, height: 900}});
  console.log('01 ok');

  async function shootStage(idx, out) {
    const y = await p.evaluate(i => {
      const h = [...document.querySelectorAll('.demohead')][i];
      const st = h.nextElementSibling.nextElementSibling;
      return st ? Math.round(st.getBoundingClientRect().top + window.scrollY) : 0;
    }, idx);
    await p.evaluate(v => window.scrollTo(0, v - 20), y);
    await p.waitForTimeout(450);
    const hh = await p.evaluate(() => document.documentElement.scrollHeight);
    const left = Math.max(0, Math.min(860, hh));
    await p.screenshot({path: out, clip: {x: 0, y: 0, width: 1440, height: left}});
    console.log(out, 'y=', y);
  }

  await shootStage(1, 'outputs/nav-guide/02-cat-bar.png');
  await shootStage(2, 'outputs/nav-guide/03-apps.png');

  await p.evaluate(() => window.scrollTo(0, 0));
  await p.waitForTimeout(300);
  await p.screenshot({path: 'outputs/nav-guide/00-full.png', fullPage: true});
  console.log('full ok');

  await b.close();
})();
