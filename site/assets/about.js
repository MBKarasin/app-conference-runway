/* "What am I looking at?" orientation dialog. Static text in index.html; this file only opens and closes it.
   No data, no network, no storage. Added 2026-10-06 at the curator's instruction. */
(function () {
  var dlg = document.getElementById("about");
  if (!dlg) return;
  function open() {
    if (typeof dlg.showModal === "function") dlg.showModal(); else dlg.setAttribute("open", "");
    var x = dlg.querySelector("[data-about-close]"); if (x) x.focus();
  }
  function close() { if (dlg.open) dlg.close(); else dlg.removeAttribute("open"); }
  document.querySelectorAll("[data-about-open]").forEach(function (b) { b.addEventListener("click", open); });
  dlg.querySelectorAll("[data-about-close]").forEach(function (b) { b.addEventListener("click", close); });
  dlg.addEventListener("click", function (e) { if (e.target === dlg) close(); });   // a click on the backdrop closes
})();
