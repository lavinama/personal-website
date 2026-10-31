// Home page: the project pop-up follows the URL hash, so it can be linked to and Back closes it.
(() => {
  const dialog = document.querySelector("dialog.project");
  if (!dialog) return;

  const sync = () => {
    const wanted = location.hash === `#${dialog.id}`;
    if (wanted && !dialog.open) dialog.showModal();
    if (!wanted && dialog.open) dialog.close();
  };

  dialog.addEventListener("close", () => {
    dialog.querySelector("video").pause();
    // Esc and the backdrop close the dialog without touching the URL, so tidy it here.
    if (location.href.includes("#")) history.replaceState(null, "", location.pathname + location.search);
  });

  // Only the backdrop reports the dialog itself: its contents fill it edge to edge.
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });

  window.addEventListener("hashchange", sync);
  sync();
})();
