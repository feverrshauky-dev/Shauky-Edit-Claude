// Deterministic frame capture: pause all CSS animations and seek them to each frame time.
const { chromium } = require('playwright'); const path = require('path');
(async () => {
  const [,, file, outDir, secs, fps] = process.argv;
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await p.goto('file://' + path.resolve(file) + '?mode=video');
  await p.waitForTimeout(800);
  const n = (+secs) * (+fps);
  for (let i = 0; i < n; i++) {
    const t = i * 1000 / (+fps);
    await p.evaluate(t => document.getAnimations().forEach(a => { a.pause(); a.currentTime = t; }), t);
    await p.screenshot({ path: `${outDir}/f${String(i).padStart(4, '0')}.png` });
  }
  await b.close();
})();
