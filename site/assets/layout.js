/* Phone layout choice. Runs in <head>, before the page is laid out.
   A phone gets the mobile layout; its visitor can switch to the desktop layout, and the choice is kept in
   that browser only (localStorage, no cookie). A phone is a screen whose shorter side is 700 px or less. */
(function () {
  var root = document.documentElement, phone = Math.min(screen.width, screen.height) <= 700, want = null;
  try { want = localStorage.getItem("runway-layout"); } catch (e) { /* storage blocked: mobile layout */ }
  if (phone) root.classList.add("is-phone");
  if (phone && want === "desktop") {
    var m = document.querySelector('meta[name="viewport"]');
    // initial-scale fits the 1280 px layout to the screen, also when a zoomed page is reloaded
    var fit = Math.min(1, Math.round(((window.innerWidth || screen.width) / 1280) * 1000) / 1000);
    if (m) m.setAttribute("content", "width=1280, initial-scale=" + fit + ", minimum-scale=" + fit);
    root.classList.add("force-desktop");
  }
})();
