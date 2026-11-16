# personal-website

Mario Lavina's personal site: a one-screen grid of images on the home page, plus **Projects**, **About** and **CV** pages. Plain HTML, CSS and a little JavaScript. There is no build step.

The layout is modelled on a gallery-style artist site: a wordmark top left, three links top right, and a sparse grid of image tiles that rise in on load. Only tiles with a project behind them are shown: today that is the robot arm. Hovering it with a mouse turns it over to the project's name, then opens the AutoWelder pop-up; a click or tap opens it straight away.

## Run it

```bash
python3 -m http.server 8000
```

Open http://localhost:8000. Any static file server works.

## Layout

| Path | What it is |
| --- | --- |
| `index.html` | Home: 40 grid cells (1 holds an image, the rest are empty). Which cells exist at which width is set by the `v-*` classes. |
| `projects/index.html` | Projects: one row per project, its video first (it plays only when pressed), the date above the name, then what it is and where. The name opens the project's pop-up, a copy of the one on the home page (the tests check the two match). |
| `about/index.html` | About page |
| `cv/index.html` | CV page: the PDF drawn into the page, with a download link |
| `assets/css/style.css` | All styles |
| `assets/js/home.js` | Tile reveal animation (respects reduced motion) |
| `assets/js/project.js` | Opens and closes the project pop-up from the URL hash (`#autowelder`) |
| `assets/js/tile-hover.js` | Turns a project tile over on mouse hover and opens its pop-up when the turn ends |
| `assets/js/hover-open.js` | Decides when hovering opens the pop-up (no DOM in it, so Node can test it) |
| `assets/projects/autowelder/` | The project's video, poster and photo, with location data removed |
| `assets/js/cv.js` | Draws the CV PDF page by page with PDF.js, so it shows in any browser, with selectable text and clickable links |
| `assets/js/cv-render.js` | Decides when the pages are drawn and swapped (no PDF.js in it, so Node can test it) |
| `assets/vendor/pdfjs/` | PDF.js 5.6.205, self-hosted (Apache-2.0, see its README) |
| `assets/img/tile-NN.svg` | Home-page artwork. Only `tile-17.svg` is on the home page; the rest are kept for future projects |
| `assets/Mario_Lavina_CV.pdf` | The CV |
| `assets/fonts/` | Inter Tight (SIL Open Font License, see `OFL.txt`) |
| `tests/test_site.py` | Smoke tests: navigation, tile grid, local links, PDF |
| `tests/hover-open.test.mjs` | Hover tests: a passing pointer opens nothing, and closing the pop-up over the tile does not reopen it |
| `tests/cv-render.test.mjs` | Viewer tests: one copy of each page, whatever the width does (run by `test_site.py` when Node is installed) |

## Common changes

**Add a project tile.** Every tile on the home page must open a project (the tests check this). Turn an empty cell into `<div class="cell tile tile-link"><a href="#project-id" aria-label="Open project: ..."><img ...><span class="tile-back" aria-hidden="true">...</span></a></div>`, keeping its `v-*` class, and add a matching `<dialog>` like `#autowelder`. The `tile-back` span is what the card shows when it turns over on hover. Cells with no `v-*` class show at every width.

**Swap a tile image.** Replace `assets/img/tile-NN.svg` with your own file, or point the `<img>` in `index.html` at a new one (keep the `alt` text meaningful). Images are cropped to fill their tile, so any aspect ratio works; portrait around 3:4 crops least.

**Regenerate the placeholder art.** `python3 scripts/generate_art.py` rewrites all 17 SVGs. They are drawn in code from fixed seeds, so the output is repeatable. Only `tile-17.svg`, the robot arm, is on the home page.

**Add project media.** Phone photos and videos carry GPS coordinates, and this repository is public, so strip metadata first and keep videos under 50 MB.

**Update the CV.** Compile the résumé and overwrite `assets/Mario_Lavina_CV.pdf`. This is a public site, so the PDF in this repo has the phone number and email removed from its header. Check that again after every rebuild.

**Edit the About text.** It is plain HTML in `about/index.html`.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

The viewer tests need Node 18 or newer. To run only those: `node --test tests/`.

## Hosting

The site is served by GitHub Pages from the root of `main`, at https://lavinama.github.io/personal-website/. Every push to `main` redeploys it. On the free plan Pages needs a public repository, so everything here, including the CV PDF and the git history, is public. All links are relative, so the site also works under a sub-path or on a custom domain.
