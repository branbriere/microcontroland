// Microcontrôland : encadré « Contre-enquête » sous la date de l'édition (accueil FR et EN).
// Lit contre-enquete.json (action du soir) et annonce le dernier dossier publié, en dehors du journal :
// l'édition elle-même n'est jamais retouchée. Rien ne s'affiche si la rubrique est fermée ou vide.
(function () {
  var en = document.documentElement.lang === "en";
  var base = window.MCL_BASE || "";
  var cible = document.getElementById("edition");
  if (!cible || !window.fetch) return;
  fetch(base + "contre-enquete.json", { cache: "no-cache" })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (j) {
      if (!j || !j.ouvert || !j.dossiers || !j.dossiers.length) return;
      var d = j.dossiers[Math.floor(Math.random() * j.dossiers.length)];   // un dossier au hasard à chaque visite
      var lg = en ? "en" : "fr";
      var box = document.createElement("aside");
      box.className = "contre-enquete";
      box.style.cssText = "border:1px solid var(--rule);border-left:4px solid var(--ink);background:var(--sheet);padding:8px 12px;margin:10px 0 14px";
      var a = document.createElement("a");
      a.href = "contre-enquete.html#" + d.id;
      a.textContent = d.titre[lg];
      var k = document.createElement("b");
      k.textContent = (en ? "Counter-investigation" : "Contre-enquête") + " · ";
      k.style.cssText = "font:600 12px var(--f-data);text-transform:uppercase;letter-spacing:.06em";
      var p = document.createElement("p");
      p.style.cssText = "margin:4px 0 0;font-style:italic";
      p.textContent = d.accroche[lg];
      box.appendChild(k);
      box.appendChild(a);
      box.appendChild(p);
      cible.parentNode.insertBefore(box, cible);
    })
    .catch(function () {});
})();
