# personal-website

Mario Lavina's personal site: a one-screen grid of images on the home page, plus **About** and **CV** pages. Plain HTML, CSS and a little JavaScript. There is no build step.

The layout is modelled on a gallery-style artist site: a wordmark top left, two links top right, and a sparse grid of image tiles that rise in on load. The robot arm tile opens a project pop-up; the other tiles are not clickable.

## Run it

```bash
python3 -m http.server 8000
```

Open http://localhost:8000. Any static file server works.

## Layout

| Path | What it is |
| --- | --- |
| `index.html` | Home: 40 grid cells (16 hold images). Which cells exist at which width is set by the `v-*` classes. |
| `about/index.html` | About page |
| `cv/index.html` | CV page: the PDF drawn into the page, with a download link |
| `assets/css/style.css` | All styles |
| `assets/js/home.js` | Tile reveal animation (respects reduced motion) |
| `assets/js/project.js` | Opens and closes the project pop-up from the URL hash (`#autowelder`) |
| `assets/projects/autowelder/` | The project's video, poster and photo, with location data removed |
| `assets/js/cv.js` | Draws the CV PDF page by page with PDF.js, so it shows in any browser, with selectable text and clickable links |
| `assets/js/cv-render.js` | Decides when the pages are drawn and swapped (no PDF.js in it, so Node can test it) |
| `assets/vendor/pdfjs/` | PDF.js 5.6.205, self-hosted (Apache-2.0, see its README) |
| `assets/img/tile-NN.svg` | Home-page artwork |
| `assets/Mario_Lavina_CV.pdf` | The CV |
| `assets/fonts/` | Inter Tight (SIL Open Font License, see `OFL.txt`) |
| `tests/test_site.py` | Smoke tests: navigation, tile grid, local links, PDF |
| `tests/cv-render.test.mjs` | Viewer tests: one copy of each page, whatever the width does (run by `test_site.py` when Node is installed) |

## Common changes

**Swap a tile image.** Replace `assets/img/tile-NN.svg` with your own file, or point the `<img>` in `index.html` at a new one (keep the `alt` text meaningful). Images are cropped to fill their tile, so any aspect ratio works; portrait around 3:4 crops least.

**Regenerate the placeholder art.** `python3 scripts/generate_art.py` rewrites all 17 SVGs. They are drawn in code from fixed seeds, so the output is repeatable. `tile-10.svg`, the ridgeline, is generated but not on the home page.

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
