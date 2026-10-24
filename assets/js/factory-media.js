/* Lazy, muted, looping factory clips. Poster only for reduced-motion users or without JS. */
(function () {
  var vids = document.querySelectorAll('video.fm-loop[data-src]');
  if (!vids.length) return;
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce) return; // keep poster frames only
  function start(v) {
    if (!v.getAttribute('src')) {
      v.setAttribute('src', v.getAttribute('data-src'));
      v.muted = true;
      v.setAttribute('autoplay', '');
    }
    var p = v.play();
    if (p && p.catch) p.catch(function () {});
  }
  if (!('IntersectionObserver' in window)) {
    for (var i = 0; i < vids.length; i++) start(vids[i]);
    return;
  }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      var v = e.target;
      if (e.isIntersecting) start(v);
      else if (v.getAttribute('src')) v.pause();
    });
  }, { rootMargin: '200px 0px', threshold: 0.01 });
  for (var j = 0; j < vids.length; j++) io.observe(vids[j]);
})();
