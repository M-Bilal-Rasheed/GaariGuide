/* GaariGuide motion layer - runs in the main Streamlit page.
 *
 * Exit animations: Streamlit re-renders as soon as a button is clicked, so
 * there is no time to animate the old question away. We catch clicks on
 * buttons whose key starts with "go_", play the exit animation (CSS class
 * "gg-out"), then replay the click so Python receives it as usual.
 * If this script fails to load, every button still works - just without
 * the exit animation.
 */
(function () {
  if (window.__ggMotion) return;
  window.__ggMotion = true;

  var EXIT_MS = 520;
  var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  document.addEventListener('click', function (e) {
    var btn = e.target && e.target.closest && e.target.closest('[class*="st-key-go_"] button');
    if (!btn || btn.disabled) return;
    if (btn.dataset.ggPass === '1') { btn.dataset.ggPass = ''; return; }   // replayed click -> let it through
    if (reduced) return;

    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();

    var stages = document.querySelectorAll('[class*="st-key-stage_"]');
    stages.forEach(function (el) { el.classList.add('gg-out'); });
    document.querySelectorAll('.gg-meta').forEach(function (el) { el.classList.add('gg-meta-out'); });
    window.scrollTo({ top: 0, behavior: 'smooth' });

    setTimeout(function () {
      btn.dataset.ggPass = '1';
      btn.click();
      // safety net: if Streamlit keeps the same elements, show them again
      setTimeout(function () {
        stages.forEach(function (el) { if (el.isConnected) el.classList.remove('gg-out'); });
      }, 4000);
    }, EXIT_MS);
  }, true);

  /* ---------------- confetti (canvas, no library) ---------------- */
  window.ggConfetti = function (token) {
    if (reduced || window.__ggConfettiToken === token) return;
    window.__ggConfettiToken = token;

    var c = document.createElement('canvas');
    c.style.cssText = 'position:fixed;inset:0;width:100vw;height:100vh;pointer-events:none;z-index:99999';
    document.body.appendChild(c);
    var ctx = c.getContext('2d');
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    function size() { c.width = innerWidth * dpr; c.height = innerHeight * dpr; }
    size();
    var colors = ['#ff4d5e', '#ff8a4c', '#ffd166', '#ffffff', '#7c5cff'];
    var parts = [];
    function burst(x, dir, n) {
      for (var i = 0; i < n; i++) {
        var a = (-Math.PI / 2) + dir * (Math.random() * 0.9 + 0.15);
        var v = (9 + Math.random() * 11) * dpr;
        parts.push({
          x: x, y: c.height * 0.72, vx: Math.cos(a) * v, vy: Math.sin(a) * v,
          w: (6 + Math.random() * 6) * dpr, h: (8 + Math.random() * 10) * dpr,
          r: Math.random() * Math.PI, vr: (Math.random() - 0.5) * 0.3,
          col: colors[(Math.random() * colors.length) | 0], life: 0
        });
      }
    }
    burst(c.width * 0.08, 1, 90);
    burst(c.width * 0.92, -1, 90);
    setTimeout(function () { burst(c.width * 0.5, (Math.random() < .5 ? 1 : -1) * 0.4, 60); }, 350);

    var start = performance.now();
    (function frame(t) {
      ctx.clearRect(0, 0, c.width, c.height);
      parts.forEach(function (p) {
        p.vy += 0.32 * dpr; p.vx *= 0.99; p.vy *= 0.99;
        p.x += p.vx; p.y += p.vy; p.r += p.vr; p.life++;
        ctx.save();
        ctx.globalAlpha = Math.max(0, 1 - (t - start) / 4200);
        ctx.translate(p.x, p.y); ctx.rotate(p.r);
        ctx.fillStyle = p.col;
        ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h * Math.abs(Math.cos(p.life / 9)));
        ctx.restore();
      });
      if (t - start < 4200) requestAnimationFrame(frame); else c.remove();
    })(start);
  };
})();
