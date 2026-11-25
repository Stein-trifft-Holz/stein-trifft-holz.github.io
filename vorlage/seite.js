// Stein trifft Holz – kleines Skript ohne fremde Dienste.
// 1. Prüft Pausen und Termine mit dem heutigen Datum des Besuchers (die Seite wird zusätzlich
//    jede Nacht neu gebaut; das hier fängt die Stunden dazwischen ab).
// 2. Vergrößert Fotos der Galerie beim Antippen.
(function () {
  var d = new Date();
  var heute = d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");

  document.querySelectorAll(".pause").forEach(function (p) {
    var sichtbar = p.dataset.ab <= heute && heute <= p.dataset.bis;
    p.hidden = !sichtbar;
    p.classList.toggle("jetzt", heute >= p.dataset.von);
    p.classList.toggle("bald", heute < p.dataset.von);
  });

  var erster = null;
  document.querySelectorAll(".termin").forEach(function (t) {
    t.hidden = t.dataset.bis < heute;
    t.classList.remove("naechster");
    if (!t.hidden && !erster) erster = t;
  });
  if (erster) erster.classList.add("naechster");
  var leer = document.querySelector(".leer");
  if (leer) leer.hidden = !!erster;

  var fenster = document.querySelector("dialog.gross");
  var knoepfe = Array.prototype.slice.call(document.querySelectorAll(".galerie button"));
  if (!fenster || !knoepfe.length || !fenster.showModal) return;
  var bild = fenster.querySelector("img");
  var text = fenster.querySelector(".gross-text");
  var stelle = 0;
  function zeige(i) {
    stelle = (i + knoepfe.length) % knoepfe.length;
    var k = knoepfe[stelle];
    bild.src = k.dataset.gross;
    bild.alt = k.dataset.titel || "Arbeit aus der Werkstatt";
    text.textContent = (k.dataset.titel ? k.dataset.titel + " · " : "") + (stelle + 1) + " von " + knoepfe.length;
  }
  knoepfe.forEach(function (k, i) {
    k.addEventListener("click", function () { zeige(i); fenster.showModal(); });
  });
  fenster.querySelector(".schliessen").addEventListener("click", function () { fenster.close(); });
  fenster.querySelector(".zurueck").addEventListener("click", function () { zeige(stelle - 1); });
  fenster.querySelector(".weiter").addEventListener("click", function () { zeige(stelle + 1); });
  fenster.addEventListener("click", function (e) { if (e.target === fenster) fenster.close(); });
  fenster.addEventListener("keydown", function (e) {
    if (e.key === "ArrowLeft") zeige(stelle - 1);
    if (e.key === "ArrowRight") zeige(stelle + 1);
  });
})();
