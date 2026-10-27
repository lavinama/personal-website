// Decides when the CV's pages are drawn into the viewer and what stays in it. It knows nothing
// about PDF.js: `buildPage(number, width)` gives it one finished page element, so tests can fake it.
export function createRenderer({ viewer, numPages, targetWidth, buildPage }) {
  let latestRun = 0;
  let renderedWidth = 0;

  async function render() {
    const width = targetWidth();
    if (width < 1) return; // hidden for now; the resize observer calls back once it has a width
    const run = ++latestRun;
    const showEarly = viewer.childElementCount === 0;
    const pages = [];
    for (let number = 1; number <= numPages; number += 1) {
      const page = await buildPage(number, width);
      if (run !== latestRun) return; // the window was resized again; a newer render takes over
      pages.push(page);
      if (showEarly) viewer.append(page); // show early pages while the rest are still drawing
    }
    viewer.replaceChildren(...pages); // the newest render's pages are the only ones left
    renderedWidth = width;
  }

  const needsRedraw = () => Math.abs(targetWidth() - renderedWidth) > 2;

  return { render, needsRedraw };
}
