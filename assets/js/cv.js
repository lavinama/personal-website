// CV page: draws each page of the PDF into the document with PDF.js, so the CV shows up
// in every browser, phones included, with selectable text and clickable links.
import * as pdfjs from "../vendor/pdfjs/pdf.min.js";

pdfjs.GlobalWorkerOptions.workerSrc = new URL("../vendor/pdfjs/pdf.worker.min.js", import.meta.url).href;

const MAX_PAGE_WIDTH = 960;
const MIN_PIXEL_RATIO = 2; // keeps text sharp when the reader zooms in
const MAX_PIXEL_RATIO = 3;
const SAFE_LINK = /^(https?:|mailto:)/i;

const viewer = document.querySelector("[data-pdf]");
const pdfUrl = new URL(viewer.dataset.pdf, document.baseURI).href;

let latestRun = 0;
let renderedWidth = 0;

const targetWidth = () => Math.floor(Math.min(viewer.clientWidth, MAX_PAGE_WIDTH));

function showFallback() {
  const link = document.createElement("a");
  link.href = pdfUrl;
  link.textContent = "Open the CV (PDF) ↗";
  const note = document.createElement("p");
  note.className = "cv-fallback";
  note.append(link);
  viewer.replaceChildren(note);
}

async function buildLinks(page, viewport) {
  const annotations = await page.getAnnotations({ intent: "display" });
  return annotations
    .filter((annotation) => annotation.subtype === "Link" && SAFE_LINK.test(annotation.url ?? ""))
    .map((annotation) => {
      const [x1, y1, x2, y2] = viewport.convertToViewportRectangle(annotation.rect);
      const link = document.createElement("a");
      link.className = "pdf-link";
      link.href = annotation.url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.title = annotation.url;
      link.setAttribute("aria-label", annotation.url);
      link.style.cssText =
        `left:${Math.min(x1, x2)}px;top:${Math.min(y1, y2)}px;` +
        `width:${Math.abs(x2 - x1)}px;height:${Math.abs(y2 - y1)}px`;
      return link;
    });
}

async function buildPage(pdf, number, width) {
  const page = await pdf.getPage(number);
  const scale = width / page.getViewport({ scale: 1 }).width;
  const cssViewport = page.getViewport({ scale });
  const ratio = Math.min(Math.max(window.devicePixelRatio || 1, MIN_PIXEL_RATIO), MAX_PIXEL_RATIO);
  const pixelViewport = page.getViewport({ scale: scale * ratio });

  const wrapper = document.createElement("div");
  wrapper.className = "pdf-page";
  wrapper.style.width = `${cssViewport.width}px`;
  wrapper.style.height = `${cssViewport.height}px`;
  wrapper.style.setProperty("--scale-factor", scale);

  const canvas = document.createElement("canvas");
  canvas.width = Math.floor(pixelViewport.width);
  canvas.height = Math.floor(pixelViewport.height);

  const textLayer = document.createElement("div");
  textLayer.className = "textLayer";
  wrapper.append(canvas, textLayer);

  await page.render({ canvas, viewport: pixelViewport }).promise;
  await new pdfjs.TextLayer({
    textContentSource: page.streamTextContent(),
    container: textLayer,
    viewport: cssViewport,
  }).render();
  wrapper.append(...(await buildLinks(page, cssViewport)));
  return wrapper;
}

async function render(pdf) {
  const run = ++latestRun;
  const width = targetWidth();
  const firstDraw = renderedWidth === 0;
  const pages = [];
  for (let number = 1; number <= pdf.numPages; number += 1) {
    const page = await buildPage(pdf, number, width);
    if (run !== latestRun) return; // the window was resized again; a newer render takes over
    pages.push(page);
    if (firstDraw) viewer.append(page); // show early pages while the rest are still drawing
  }
  if (!firstDraw) viewer.replaceChildren(...pages); // after a resize, swap everything at once
  renderedWidth = width;
}

function redrawOnResize(pdf) {
  let timer;
  new ResizeObserver(() => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      if (Math.abs(targetWidth() - renderedWidth) > 2) render(pdf).catch(showFallback);
    }, 200);
  }).observe(viewer);
}

async function main() {
  const pdf = await pdfjs.getDocument({ url: pdfUrl, isEvalSupported: false }).promise;
  await render(pdf);
  redrawOnResize(pdf);
}

main().catch((error) => {
  console.error("CV viewer failed", error);
  showFallback();
});
