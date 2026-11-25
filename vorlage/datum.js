// Prüft Pausen und Termine noch einmal mit dem heutigen Datum des Besuchers.
// Die Seite wird ohnehin täglich neu gebaut; das hier fängt die Stunden dazwischen ab.
(function () {
  var d = new Date();
  var heute = d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  document.querySelectorAll(".pause").forEach(function (p) {
    p.hidden = !(p.dataset.ab <= heute && heute <= p.dataset.bis);
  });
  var offen = 0;
  document.querySelectorAll(".termin").forEach(function (t) {
    t.hidden = t.dataset.bis < heute;
    if (!t.hidden) offen++;
  });
  var leer = document.querySelector(".leer");
  if (leer) leer.hidden = offen > 0;
})();
