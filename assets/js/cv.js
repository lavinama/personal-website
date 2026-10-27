// CV page: draws each page of the PDF into the document with PDF.js, so the CV shows up
// in every browser, phones included, with selectable text and clickable links.
import * as pdfjs from "../vendor/pdfjs/pdf.min.js";
import { createRenderer } from "./cv-render.js";

pdfjs.GlobalWorkerOptions.workerSrc = new URL("../vendor/pdfjs/pdf.worker.min.js", import.meta.url).href;

const MAX_PAGE_WIDTH = 960;
const MIN_PIXEL_RATIO = 2; // keeps text sharp when the reader zooms in
const MAX_PIXEL_RATIO = 3;
const SAFE_LINK = /^(https?:|mailto:)/i;

const viewer = document.querySelector("[data-pdf]");
const pdfUrl = new URL(viewer.dataset.pdf, document.baseURI).href;

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

function redrawOnResize(renderer) {
  let timer;
  new ResizeObserver(() => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      if (renderer.needsRedraw()) renderer.render().catch(showFallback);
    }, 200);
  }).observe(viewer);
}

async function main() {
  const pdf = await pdfjs.getDocument({ url: pdfUrl, isEvalSupported: false }).promise;
  const renderer = createRenderer({
    viewer,
    numPages: pdf.numPages,
    targetWidth,
    buildPage: (number, width) => buildPage(pdf, number, width),
  });
  await renderer.render();
  redrawOnResize(renderer);
}

main().catch((error) => {
  console.error("CV viewer failed", error);
  showFallback();
});
