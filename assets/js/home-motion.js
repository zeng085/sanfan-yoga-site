/* Homepage motion (index.html only). Everything here is decoration on top of
   content that is already complete in the HTML. With prefers-reduced-motion
   nothing moves: no slideshow, no reel video, no reveal, no counting. */
(function () {
  var d = document, root = d.documentElement;
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce) return;
  root.classList.add('hv-motion');
  var hasIO = 'IntersectionObserver' in window;

  /* ---------- scroll reveal (staggered) ---------- */
  var groups = [
    ['.hv-sec .hv-split-head > *, .hv-why-head > *, .hv-glance-body > h2, .hv-glance-body > p, .hv-end-grid > div > h2, .hv-end-sub', 0.08],
    ['.hv-bento > li', 0.07], ['.hv-prods > li', 0.06], ['.hv-vid', 0.12],
    ['.hv-footage .fm-item', 0.12], ['.hv-why-list > div', 0.1], ['.hv-facts > div', 0.08],
    ['.hv-cap', 0], ['.hv-app-list > li', 0.07], ['.hv-cert-list li', 0.07], ['.hv-how li', 0.09],
    ['.hv-cta', 0], ['.hv-note, .hv-after, .fm-more', 0]
  ];
  var rv = [];
  groups.forEach(function (g) {
    var parents = new Map();
    d.querySelectorAll(g[0]).forEach(function (el) {
      var p = el.parentNode, n = parents.get(p) || 0; parents.set(p, n + 1);
      el.classList.add('hv-rv'); el.style.setProperty('--d', Math.min(n * g[1], 0.6) + 's'); rv.push(el);
    });
  });
  d.querySelectorAll('.hv-why-media, .hv-glance-media, .hv-cert-wall').forEach(function (el) { el.classList.add('hv-rv-zoom'); rv.push(el); });
  if (hasIO) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); } });
    }, { rootMargin: '0px 0px 4% 0px', threshold: 0.08 });
    rv.forEach(function (el) { io.observe(el); });
  } else rv.forEach(function (el) { el.classList.add('is-in'); });

  /* ---------- count-up numbers (once, when visible) ---------- */
  function countUp(dd) {
    var full = dd.textContent, m = full.match(/^(\D*)([\d,]+)(.*)$/);
    if (!m) return;
    var target = parseInt(m[2].replace(/,/g, ''), 10);
    if (!target || (target >= 1900 && target <= 2100)) return; /* years stay as they are */
    var comma = m[2].indexOf(',') > -1, t0 = null, dur = target > 1000 ? 1600 : 1100;
    dd.setAttribute('aria-label', full);
    function fmt(v) { return comma ? v.toLocaleString('en-US') : String(v); }
    function step(ts) {
      if (!t0) t0 = ts;
      var k = Math.min((ts - t0) / dur, 1), e = 1 - Math.pow(1 - k, 3);
      dd.textContent = m[1] + fmt(Math.round(target * e)) + m[3];
      if (k < 1) requestAnimationFrame(step); else { dd.textContent = full; dd.removeAttribute('aria-label'); }
    }
    dd.textContent = m[1] + '0' + m[3];
    requestAnimationFrame(step);
  }
  var dds = d.querySelectorAll('.hv-tag dd, .hv-facts dd');
  if (hasIO) {
    var cio = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { countUp(e.target); cio.unobserve(e.target); } });
    }, { threshold: 0.6 });
    dds.forEach(function (x) { cio.observe(x); });
  }

  /* ---------- stacking process cards: the covered card recedes ---------- */
  var cards = [].slice.call(d.querySelectorAll('.hv-stack .hv-steps > li'));
  if (cards.length > 1) {
    var ticking = false;
    function stack() {
      ticking = false;
      if (getComputedStyle(cards[0]).position !== 'sticky') { /* phone: cards swipe sideways, nothing stacks */
        cards.forEach(function (c) { c.firstElementChild.style.removeProperty('--s'); c.firstElementChild.style.removeProperty('--dim'); });
        return;
      }
      for (var i = 0; i < cards.length - 1; i++) {
        var a = cards[i].getBoundingClientRect(), b = cards[i + 1].getBoundingClientRect();
        var p = 1 - Math.min(Math.max((b.top - a.top) / a.height, 0), 1); /* 0 = next card far, 1 = fully over */
        var f = cards[i].firstElementChild;
        f.style.setProperty('--s', (1 - p * 0.06).toFixed(4));
        f.style.setProperty('--dim', (p * 0.35).toFixed(3));
      }
    }
    addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(stack); } }, { passive: true });
    addEventListener('resize', stack); stack();
  }

  /* ---------- drag to scroll the product rail with a mouse ---------- */
  d.querySelectorAll('.hv-rail-products').forEach(function (rail) {
    var down = false, x0 = 0, s0 = 0, moved = false;
    rail.addEventListener('pointerdown', function (e) { if (e.pointerType !== 'mouse') return; down = true; moved = false; x0 = e.clientX; s0 = rail.scrollLeft; });
    addEventListener('pointermove', function (e) {
      if (!down) return; var dx = e.clientX - x0;
      if (Math.abs(dx) > 5) { moved = true; rail.style.scrollSnapType = 'none'; rail.scrollLeft = s0 - dx; }
    });
    addEventListener('pointerup', function () { if (!down) return; down = false; rail.style.scrollSnapType = ''; });
    rail.addEventListener('click', function (e) { if (moved) { e.preventDefault(); moved = false; } }, true);
    rail.addEventListener('dragstart', function (e) { e.preventDefault(); });
  });

  /* ---------- hero: crossfading photos + factory reel, started after load ---------- */
  var hero = d.querySelector('.hv-hero');
  if (!hero) return;
  var heroVisible = true;
  if (hasIO) new IntersectionObserver(function (es) { heroVisible = es[0].isIntersecting; toggleReel(); }).observe(hero);
  var reel = hero.querySelector('.hv-reel'), vid = reel && reel.querySelector('video');
  var clips = vid ? vid.getAttribute('data-clips').split('|') : [], ci = 0, reelOn = false;
  function toggleReel() {
    if (!reelOn || !vid) return;
    if (heroVisible) { var p = vid.play(); if (p && p.catch) p.catch(function () {}); } else vid.pause();
  }
  function startReel() {
    if (!vid || !reel.offsetParent && getComputedStyle(reel).display === 'none') return;
    if (getComputedStyle(reel).display === 'none') return;
    if (navigator.connection && navigator.connection.saveData) return;
    reelOn = true; vid.muted = true; vid.setAttribute('preload', 'auto');
    vid.addEventListener('playing', function () { reel.classList.add('is-playing'); });
    vid.addEventListener('ended', function () { ci = (ci + 1) % clips.length; vid.src = clips[ci]; toggleReel(); });
    vid.src = clips[0]; toggleReel();
  }
  function startSlides() {
    var box = hero.querySelector('.hv-hero-slides'), first = hero.querySelector('.hv-hero-img');
    if (!box || !first) return;
    var sets = box.getAttribute('data-slides').split('|'), imgs = [first];
    sets.forEach(function (ss) {
      var im = new Image(); im.alt = ''; im.decoding = 'async'; im.sizes = '100vw'; im.srcset = ss;
      im.src = ss.split(',').pop().trim().split(' ')[0]; box.appendChild(im); imgs.push(im);
    });
    var i = 0; first.classList.add('is-kb');
    setInterval(function () {
      if (!heroVisible || d.hidden) return;
      var next = (i + 1) % imgs.length;
      if (next === 0) { imgs.forEach(function (x, k) { if (k) x.classList.remove('is-on'); }); first.classList.remove('is-kb'); void first.offsetWidth; first.classList.add('is-kb'); }
      else { imgs[next].classList.remove('is-on'); void imgs[next].offsetWidth; imgs[next].classList.add('is-on'); }
      i = next;
    }, 5200);
  }
  function go() { setTimeout(function () { startSlides(); startReel(); }, 400); }
  if (d.readyState === 'complete') go(); else addEventListener('load', go);
})();
