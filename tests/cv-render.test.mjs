// The CV viewer must always end up with exactly one copy of each page, whatever the width does.
// Run from the repository root:  node --test tests/
import assert from "node:assert/strict";
import test from "node:test";
import { createRenderer } from "../assets/js/cv-render.js";

const NUM_PAGES = 2;

function fakeViewer() {
  const viewer = {
    children: [],
    append: (...nodes) => viewer.children.push(...nodes),
    replaceChildren: (...nodes) => { viewer.children = nodes; },
  };
  Object.defineProperty(viewer, "childElementCount", { get: () => viewer.children.length });
  return viewer;
}

// A page builder that finishes at once; every page records the width it was drawn at.
const instantBuilder = (number, width) => Promise.resolve({ number, width });

function setup({ widths, buildPage = instantBuilder }) {
  const state = { width: widths };
  const viewer = fakeViewer();
  const renderer = createRenderer({ viewer, numPages: NUM_PAGES, targetWidth: () => state.width, buildPage });
  return { state, viewer, renderer };
}

const shown = (viewer) => viewer.children.map(({ number, width }) => `${number}@${width}`);

test("draws each page once at the viewer's width", async () => {
  const { viewer, renderer } = setup({ widths: 800 });
  await renderer.render();
  assert.deepEqual(shown(viewer), ["1@800", "2@800"]);
});

test("a viewer with no width yet draws nothing, then draws once when it gets a width", async () => {
  const { state, viewer, renderer } = setup({ widths: 0 });
  await renderer.render();
  assert.deepEqual(shown(viewer), [], "nothing is drawn into a zero-width viewer");

  state.width = 800;
  assert.equal(renderer.needsRedraw(), true);
  await renderer.render();
  assert.deepEqual(shown(viewer), ["1@800", "2@800"]);
});

test("a resize swaps the pages instead of adding more", async () => {
  const { state, viewer, renderer } = setup({ widths: 800 });
  await renderer.render();
  state.width = 500;
  await renderer.render();
  assert.deepEqual(shown(viewer), ["1@500", "2@500"]);
});

test("a resize during the first draw leaves one copy of each page at the new width", async () => {
  const gates = [];
  const buildPage = (number, width) => new Promise((resolve) => gates.push(() => resolve({ number, width })));
  const { state, viewer, renderer } = setup({ widths: 800, buildPage });

  const first = renderer.render();
  gates.shift()(); // page 1 of the first draw is built and shown
  await new Promise((resolve) => setImmediate(resolve));
  assert.deepEqual(shown(viewer), ["1@800"], "early pages show while the rest are still drawing");

  state.width = 500;
  const second = renderer.render();
  gates.shift()(); // the first draw's page 2 finishes late and is dropped
  await new Promise((resolve) => setImmediate(resolve));
  gates.shift()(); // page 1 of the second draw
  await new Promise((resolve) => setImmediate(resolve));
  gates.shift()(); // page 2 of the second draw
  await Promise.all([first, second]);

  assert.deepEqual(shown(viewer), ["1@500", "2@500"]);
});

test("needsRedraw ignores changes of 2px or less", async () => {
  const { state, renderer } = setup({ widths: 800 });
  await renderer.render();
  state.width = 802;
  assert.equal(renderer.needsRedraw(), false);
  state.width = 803;
  assert.equal(renderer.needsRedraw(), true);
});
