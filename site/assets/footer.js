(function () {
  var c = window.RUNWAY_CONFIG || {};
  var $ = function (id) { return document.getElementById(id); };
  if ($("curator")) $("curator").textContent = c.curator || "";
  if ($("credentials")) $("credentials").textContent = c.credentials || "";
  (c.roles || []).forEach(function (r) {
    if (!$("roles")) return;
    var li = document.createElement("li");
    var label = document.createElement("span"); label.className = "role-label"; label.textContent = r.label;
    var institution = document.createElement("a"); institution.href = r.institutionUrl; institution.target = "_blank"; institution.rel = "noopener noreferrer"; institution.textContent = r.institution;
    li.appendChild(label); li.appendChild(institution);
    if (r.title) {
      var title = r.titleUrl ? document.createElement("a") : document.createElement("span");
      if (r.titleUrl) { title.href = r.titleUrl; title.target = "_blank"; title.rel = "noopener noreferrer"; }
      title.className = "role-title"; title.textContent = r.title;
      li.appendChild(title);
    }
    $("roles").appendChild(li);
  });
  (c.partners || []).forEach(function (p) {
    var a = document.createElement("a");
    a.href = p.href; a.target = "_blank"; a.rel = "noopener noreferrer"; a.className = "partner";
    var img = new Image(); img.alt = ""; img.height = 36;
    img.addEventListener("error", function () { img.remove(); });
    img.src = p.logo;
    var t = document.createElement("span"); t.textContent = p.name;
    a.appendChild(img); a.appendChild(t);
    $("partners") && $("partners").appendChild(a);
  });
  var mail = c.requestEmail || "";
  document.querySelectorAll("[data-request]").forEach(function (a) {
    a.href = "mailto:" + mail + "?subject=" + encodeURIComponent("APP Conference Runway request");
  });
  document.querySelectorAll("[data-request-address]").forEach(function (s) { s.textContent = mail; });
})();
