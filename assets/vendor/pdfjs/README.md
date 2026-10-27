# PDF.js

[PDF.js](https://github.com/mozilla/pdf.js) 5.6.205, legacy build, Apache-2.0 (see `LICENSE`).

Source: the npm package `pdfjs-dist@5.6.205`, files `legacy/build/pdf.min.mjs` and `legacy/build/pdf.worker.min.mjs`.
They are renamed to `.js` so that every static host serves them with a JavaScript content type. The code is unchanged.

Used only by `assets/js/cv.js` to draw the CV PDF inside the page.
