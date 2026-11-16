// Home page: hovering a project tile with a mouse turns it over, then opens its pop-up.
// Touch screens have no hover, so there a tap opens the pop-up as before.
import { createHoverOpener } from "./hover-open.js";

const TURN_MS = 600; // matches the turn's transition in style.css

const canHover = window.matchMedia("(hover: hover) and (pointer: fine)");

// Where the pointer last was, so closing the pop-up can tell whether it is over the tile.
const pointer = { x: -1, y: -1 };
const track = (event) => { pointer.x = event.clientX; pointer.y = event.clientY; };
document.addEventListener("pointermove", track, { passive: true });
document.addEventListener("pointerdown", track, { passive: true });

const isUnderPointer = (element) => {
  const box = element.getBoundingClientRect();
  return pointer.x >= box.left && pointer.x <= box.right && pointer.y >= box.top && pointer.y <= box.bottom;
};

document.querySelectorAll(".tile-link").forEach((tile) => {
  const link = tile.querySelector("a[href^='#']");
  const dialog = link && document.getElementById(link.hash.slice(1));
  if (!(dialog instanceof HTMLDialogElement)) return;

  const opener = createHoverOpener({
    delay: TURN_MS,
    isOpen: () => dialog.open,
    // Same route as a click, so the URL names the project and Back closes it.
    open: () => { location.hash = dialog.id; },
    turn: (on) => tile.classList.toggle("is-turned", on),
  });

  const isMouse = (event) => canHover.matches && event.pointerType === "mouse";

  tile.addEventListener("pointerenter", (event) => { if (isMouse(event)) opener.enter(); });
  tile.addEventListener("pointerleave", (event) => { if (isMouse(event)) opener.leave(); });
  dialog.addEventListener("close", () => opener.closed(isUnderPointer(tile)));
  // After the pop-up closes, the first pointer move outside the tile lets hovering count again.
  document.addEventListener("pointermove", (event) => {
    if (!dialog.open && !tile.contains(event.target)) opener.rearm();
  }, { passive: true });
});
