// Hovering a project tile turns it over and opens the pop-up once the turn has finished.
// Run from the repository root:  node --test tests/
import assert from "node:assert/strict";
import test from "node:test";
import { createHoverOpener } from "../assets/js/hover-open.js";

const DELAY = 600;

// Fake clock and a fake pop-up, so each test controls exactly when time passes.
function setup() {
  const timers = new Map();
  let nextId = 1;
  const state = { open: false, opens: 0, turned: false };
  const opener = createHoverOpener({
    delay: DELAY,
    isOpen: () => state.open,
    open: () => { state.open = true; state.opens += 1; },
    turn: (on) => { state.turned = on; },
    setTimer: (fn, ms) => { const id = nextId++; timers.set(id, { fn, ms }); return id; },
    clearTimer: (id) => timers.delete(id),
  });
  const elapse = () => {
    const due = [...timers.entries()];
    timers.clear();
    due.forEach(([, { fn, ms }]) => { assert.equal(ms, DELAY); fn(); });
  };
  // `pointerInside`: whether the pointer was over the tile when the pop-up closed.
  const close = (pointerInside = true) => { state.open = false; opener.closed(pointerInside); };
  return { opener, state, elapse, close, timers };
}

test("hovering turns the tile at once and opens the pop-up when the turn ends", () => {
  const { opener, state, elapse } = setup();
  opener.enter();
  assert.equal(state.turned, true);
  assert.equal(state.opens, 0);
  elapse();
  assert.equal(state.opens, 1);
});

test("leaving before the turn ends turns the tile back and opens nothing", () => {
  const { opener, state, elapse, timers } = setup();
  opener.enter();
  opener.leave();
  assert.equal(timers.size, 0);
  elapse();
  assert.equal(state.opens, 0);
  assert.equal(state.turned, false);
});

test("closing the pop-up turns the tile back", () => {
  const { opener, state, elapse, close } = setup();
  opener.enter();
  elapse();
  close();
  assert.equal(state.turned, false);
});

test("a pointer still on the tile after closing does not reopen the pop-up", () => {
  const { opener, state, elapse, close } = setup();
  opener.enter();
  elapse();
  close();
  opener.enter(); // the browser reports the pointer over the tile again
  elapse();
  assert.equal(state.opens, 1);
  assert.equal(state.turned, false);
});

test("leaving and coming back after closing opens it again", () => {
  const { opener, state, elapse, close } = setup();
  opener.enter();
  elapse();
  close();
  opener.leave();
  opener.enter();
  elapse();
  assert.equal(state.opens, 2);
});

test("a pointer that was elsewhere when the pop-up closed can hover straight back in", () => {
  const { opener, state, elapse, close } = setup();
  opener.enter();
  elapse();
  close(false); // e.g. closed by clicking the backdrop away from the tile
  opener.enter(); // no pointer move outside the tile is reported first
  elapse();
  assert.equal(state.opens, 2);
});

test("a pointer move outside the tile after closing lets hovering count again", () => {
  const { opener, state, elapse, close } = setup();
  opener.enter();
  elapse();
  close();
  opener.rearm();
  opener.enter();
  elapse();
  assert.equal(state.opens, 2);
});

test("a click that opened the pop-up first is not followed by a second open", () => {
  const { opener, state, elapse } = setup();
  opener.enter();
  state.open = true; // the click's hash change opened it before the turn ended
  elapse();
  assert.equal(state.opens, 0);
});

test("hovering while the pop-up is open does nothing", () => {
  const { opener, state, timers } = setup();
  state.open = true;
  opener.enter();
  assert.equal(timers.size, 0);
  assert.equal(state.turned, false);
});
