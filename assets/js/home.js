// Home page: tiles rise into place in a random order once their images have decoded.
(() => {
  const tiles = [...document.querySelectorAll(".tile")];
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (!tiles.length || reducedMotion) {
    tiles.forEach((tile) => tile.classList.add("is-in"));
    return;
  }

  const shuffled = tiles
    .map((tile) => [Math.random(), tile])
    .sort((a, b) => a[0] - b[0])
    .map(([, tile]) => tile);

  const reveal = () =>
    shuffled.forEach((tile, index) => {
      tile.style.setProperty("--delay", `${index * 70}ms`);
      tile.classList.add("is-in");
    });

  const decoded = Promise.all(tiles.map((tile) => tile.querySelector("img").decode().catch(() => {})));
  const timeout = new Promise((resolve) => setTimeout(resolve, 1500));

  Promise.race([decoded, timeout]).then(() => requestAnimationFrame(reveal));
})();
