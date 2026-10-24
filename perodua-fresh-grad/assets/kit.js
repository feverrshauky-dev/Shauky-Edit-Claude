// Shared pieces for every scene: generic side-view cars (no brand marks) and
// tween helpers that take film seconds and place them on a scene's own clock.
(function () {
  const BODY = {
    hatch: {
      body: "M44 140 L44 104 Q46 84 60 72 Q74 60 100 58 L226 54 Q246 54 258 64 L300 98 L354 104 Q376 108 377 126 L377 140 Q377 150 367 150 L54 150 Q44 150 44 140 Z",
      win: ["M76 100 L86 78 Q92 66 108 65 L168 63 L168 100 Z", "M180 63 L224 63 Q238 63 248 72 L278 100 L180 100 Z"],
      tail: 40,
    },
    myvi: {
      body: "M44 140 L44 100 Q46 78 60 62 Q74 46 104 44 L228 42 Q250 42 263 54 L306 96 L356 102 Q378 106 379 126 L379 140 Q379 150 369 150 L54 150 Q44 150 44 140 Z",
      win: ["M74 94 L84 68 Q92 54 110 53 L170 51 L170 94 Z", "M182 51 L226 51 Q242 51 252 62 L284 94 L182 94 Z"],
      tail: 40,
    },
    sedan: {
      body: "M34 140 L34 106 Q36 94 52 92 L104 90 L140 58 Q148 50 162 50 L244 50 Q258 50 268 60 L304 94 L358 100 Q380 104 381 124 L381 140 Q381 150 371 150 L44 150 Q34 150 34 140 Z",
      win: ["M116 90 L146 62 Q151 57 160 57 L200 57 L200 90 Z", "M212 57 L242 57 Q254 57 262 66 L288 90 L212 90 Z"],
      tail: 30,
    },
  };

  function wheel(cx) {
    let spokes = "";
    for (let i = 0; i < 5; i++) {
      const a = (i * 72 * Math.PI) / 180;
      spokes += `<line x1="${cx}" y1="150" x2="${(cx + Math.cos(a) * 15).toFixed(1)}" y2="${(150 + Math.sin(a) * 15).toFixed(1)}" stroke="#7d8794" stroke-width="4" stroke-linecap="round"/>`;
    }
    return `<g class="wheel"><circle cx="${cx}" cy="150" r="30" fill="#1a1d22"/><circle cx="${cx}" cy="150" r="18" fill="#d3d9e1"/>${spokes}<circle cx="${cx}" cy="150" r="5" fill="#5b6470"/></g>`;
  }

  function carSvg(kind, color) {
    const b = BODY[kind];
    return `<svg viewBox="0 0 420 190" style="display:block;width:100%;height:auto;overflow:visible">
      <ellipse cx="212" cy="182" rx="186" ry="8" fill="rgba(0,0,0,0.4)"/>
      <path d="${b.body}" fill="${color}"/>
      <path d="M${b.tail + 4} 126 H376" stroke="rgba(0,0,0,0.18)" stroke-width="6"/>
      ${b.win.map((d) => `<path d="${d}" fill="#1d2b3b"/>`).join("")}
      <path d="${b.win[1]}" fill="rgba(255,255,255,0.12)" transform="translate(6 0) scale(0.97 1)"/>
      <line x1="175" y1="104" x2="175" y2="146" stroke="rgba(0,0,0,0.25)" stroke-width="3"/>
      <rect x="196" y="108" width="20" height="5" rx="2.5" fill="rgba(0,0,0,0.3)"/>
      <rect x="360" y="110" width="16" height="11" rx="4" fill="#fff4b8"/>
      <rect x="${b.tail}" y="104" width="9" height="17" rx="3" fill="#ff4d4d"/>
      ${wheel(118)}${wheel(310)}
    </svg>`;
  }

  // Fill every [data-car] slot inside `scope` with its car.
  function cars(scope) {
    scope.querySelectorAll("[data-car]").forEach((el) => {
      el.innerHTML = carSvg(el.dataset.car, el.dataset.color);
    });
  }

  // Helpers for one scene. `t0` is the film second the scene starts at, so the
  // times written in each scene read the same as the film timeline.
  function scene(tl, t0) {
    const at = (t) => Math.max(0, t - t0);
    const pop = { duration: 0.45, ease: "back.out(1.6)" };
    return {
      at,
      pop,
      fadeUp: (sel, t, y = 40) => tl.fromTo(sel, { opacity: 0, y }, { opacity: 1, y: 0, duration: 0.45, ease: "expo.out" }, at(t)),
      zoomIn: (sel, t, from = 1.2) => tl.fromTo(sel, { opacity: 0, scale: from }, { opacity: 1, scale: 1, duration: 0.4, ease: "expo.out" }, at(t)),
      spin: (sel, t, dur, turns) =>
        tl.fromTo(`${sel} .wheel`, { rotation: 0 }, { rotation: 360 * turns, duration: dur, ease: "power2.out", transformOrigin: "50% 50%", immediateRender: false }, at(t)),
      counter: (sel, to, t, dur, fmt) => {
        const o = { v: 0 };
        tl.to(o, { v: to, duration: dur, ease: "power2.out", onUpdate: () => { document.querySelector(sel).textContent = fmt(o.v); } }, at(t));
      },
      out: (sels, t) => tl.to(sels, { opacity: 0, y: -30, duration: 0.22, ease: "power3.in", stagger: 0.02 }, at(t)),
    };
  }

  window.kit = { carSvg, cars, scene };
})();
