// 验证预览页锚点导航：导航条是否在视口内、跳转后标题是否被 sticky 横幅遮挡
const { chromium } = require('playwright');
(async () => {
  const url = process.argv[2];
  const b = await chromium.launch();
  for (const W of [1280, 390]) {
    const p = await b.newPage({ viewport: { width: W, height: 900 } });
    await p.goto(url, { waitUntil: 'load' });
    await p.waitForTimeout(300);
    const nav = await p.evaluate(() => {
      const n = document.querySelector('.pv-nav');
      const r = n.getBoundingClientRect();
      return {
        w: Math.round(r.width), h: Math.round(r.height), right: Math.round(r.right),
        vw: document.documentElement.clientWidth,
        links: [...n.querySelectorAll('a')].map((a) => a.textContent.trim()),
      };
    });
    const ok = nav.right <= nav.vw + 1 ? '(在视口内 OK)' : '<<< 超出视口';
    console.log('W=' + W + ' nav ' + nav.w + 'x' + nav.h + ' right=' + nav.right +
                ' vw=' + nav.vw + ' ' + ok + ' links=' + nav.links.join('/'));
    for (const id of ['diag', 'a', 'b', 'c', 'todo']) {
      await p.evaluate((i) => { location.hash = ''; location.hash = '#' + i; }, id);
      await p.waitForTimeout(220);
      const r = await p.evaluate((i) => {
        const sec = document.getElementById(i);
        const bh = document.querySelector('.pv-banner').getBoundingClientRect().height;
        const top = sec.querySelector('.eyebrow').getBoundingClientRect().top;
        return { bh: Math.round(bh), top: Math.round(top) };
      }, id);
      console.log('   #' + id + ': banner=' + r.bh + ' eyebrowTop=' + r.top +
                  ' -> ' + (r.top < r.bh ? '*** 被遮挡' : '可见 OK'));
    }
    await p.close();
  }
  await b.close();
})();
