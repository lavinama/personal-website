// Decides when hovering a project tile turns it over and opens its pop-up. It knows nothing
// about the page: `turn(on)` flips the tile and `open()` shows the pop-up, so tests can fake them.
//
// The pop-up opens only once the turn has finished, so a pointer passing over the tile opens
// nothing. After the pop-up closes, the pointer has to leave the tile before hovering counts
// again; otherwise closing it over the tile would reopen it at once.
export function createHoverOpener({ open, turn, isOpen, delay, setTimer = setTimeout, clearTimer = clearTimeout }) {
  let timer = null;
  let armed = true;

  const cancel = () => {
    if (timer === null) return;
    clearTimer(timer);
    timer = null;
  };

  function enter() {
    if (!armed || isOpen()) return;
    cancel();
    turn(true);
    timer = setTimer(() => {
      timer = null;
      armed = false;
      if (!isOpen()) open();
    }, delay);
  }

  function leave() {
    cancel();
    armed = true;
    if (!isOpen()) turn(false);
  }

  // `pointerInside`: whether the pointer was over the tile when the pop-up closed.
  function closed(pointerInside) {
    cancel();
    armed = !pointerInside;
    turn(false);
  }

  const rearm = () => {
    armed = true;
  };

  return { enter, leave, closed, rearm };
}
