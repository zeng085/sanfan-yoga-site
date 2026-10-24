/* Lazy, muted, looping factory clips.
   Autoplay when allowed; otherwise (reduced-motion setting, autoplay blocked, old browser)
   show native controls so visitors can always tap play. */
(function () {
  var vids = document.querySelectorAll('video.fm-loop[data-src]');
  if (!vids.length) return;
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function load(v) {
    if (!v.getAttribute('src')) {
      v.setAttribute('src', v.getAttribute('data-src'));
      v.muted = true;
    }
  }
  function manual(v) {
    load(v);
    v.setAttribute('controls', '');
    v.setAttribute('preload', 'metadata');
  }
  function start(v) {
    if (v.hasAttribute('controls')) return;
    load(v);
    var p;
    try { p = v.play(); } catch (err) { manual(v); return; }
    if (p && p.catch) p.catch(function () { manual(v); });
  }
  for (var k = 0; k < vids.length; k++) {
    (function (v) {
      v.addEventListener('error', function () { manual(v); }, true);
      v.addEventListener('click', function () {
        if (v.hasAttribute('controls')) return;
        if (v.paused) start(v); else v.pause();
      });
    })(vids[k]);
  }
  if (reduce || !('IntersectionObserver' in window)) {
    for (var i = 0; i < vids.length; i++) manual(vids[i]);
    return;
  }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      var v = e.target;
      if (v.hasAttribute('controls')) return;
      if (e.isIntersecting) start(v);
      else if (v.getAttribute('src')) v.pause();
    });
  }, { rootMargin: '200px 0px', threshold: 0.01 });
  for (var j = 0; j < vids.length; j++) io.observe(vids[j]);
  /* safety net: if a clip in view still is not playing after 4s, give it controls */
  setTimeout(function () {
    for (var n = 0; n < vids.length; n++) {
      var v = vids[n], r = v.getBoundingClientRect();
      if (r.top < window.innerHeight && r.bottom > 0 && v.paused && !v.hasAttribute('controls')) manual(v);
    }
  }, 4000);
})();
