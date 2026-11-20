// Le générateur quantique (v1.0, 20 novembre 2026) : l'Œil du Centre de recherche et son atelier de chiffres.
// Deux modes, choisis tout seuls :
//  · « vacances » (aujourd'hui) : OEIL_URL est vide, ou l'Œil n'a rien envoyé depuis 20 minutes. Le ruban imprime
//    du hasard ordinaire, tiré par le navigateur du visiteur (crypto.getRandomValues), et la page le dit.
//  · « en service » : OEIL_URL donne oeil.json, écrit par le Worker de l'Œil :
//      {"maj":"2026-12-01T10:05:00Z","blocs":[{"n":1234,"t":"2026-12-01T10:05:00Z","bits":"<64 caractères hex>","ok":true}, …]}
//    Le ruban imprime alors les vrais blocs (6 chiffres tirés de chaque bloc), et un copiste recopie le dernier.
//    Copiste = un citoyen sans pouvoir (ni président ni ministre) de data/citoyens.json, choisi par le jour de l'ère.
// Aucun chiffre de cette page n'entre dans la boîte du pays.
(function () {
  const OEIL_URL = '';   // à remplir quand l'Œil enverra ses chiffres (adresse du Worker « oeil »)
  const FRAIS_MS = 20 * 60 * 1000, PAS_MS = 4000;
  const M = window.MCL || {};
  const en = document.documentElement.lang === 'en';
  const $ = (id) => document.getElementById(id);
  const ruban = $('g-ruban'), recopie = $('g-recopie'), flux = $('g-flux'), boite = $('g-oeil'),
        ardoise = $('g-ardoise'), cpt = $('g-compteur'), voyants = $('g-voyants'), copiste = $('g-copiste');
  if (!ruban) return;
  const T = en
    ? { vac: ['Eye: asleep', 'Copyist: on holiday', 'Tape: ordinary chance'], srv: ['Eye: in service', 'Photons: plenty', 'Check: passed'],
        tape: (n) => `tape No. ${n}`, torn: '— rrrip! tape torn —', flux: 'ordinary chance from your browser, not from the Eye',
        cop: 'Copyist of the day: ', none: 'nobody yet' }
    : { vac: ['Œil : en sommeil', 'Copiste : en vacances', 'Ruban : hasard ordinaire'], srv: ['Œil : en service', 'Photons : nombreux', 'Contrôle : réussi'],
        tape: (n) => `ruban n° ${n}`, torn: '— crrrac ! ruban déchiré —', flux: 'hasard ordinaire de votre navigateur, pas de l\'Œil',
        cop: 'Copiste du jour : ', none: 'personne pour l\'instant' };
  const reduit = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  let numRuban = 1, lignes = 0, enService = false, dernierN = -1;

  const hex = (a) => Array.from(a, (b) => b.toString(16).padStart(2, '0')).join('');
  const six = (h) => (parseInt(h.slice(0, 6), 16) % 1000000).toString().padStart(6, '0');
  const heure = (d) => d.toLocaleTimeString(en ? 'en-GB' : 'fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  function setVoyants(liste, panne) {
    voyants.innerHTML = liste.map((t, i) => `<span class="g-voyant${panne && i < 2 ? ' panne' : ''}"><i></i>${t}</span>`).join('');
  }

  function dechirer() {
    ruban.innerHTML = `<div class="g-dechire">${T.torn}</div>`;
    numRuban++; lignes = 0; cpt.textContent = T.tape(numRuban);
  }

  function imprimer(h, quand) {
    const v = six(h);
    const l = document.createElement('div'); l.className = 'g-ligne' + (reduit ? '' : ' neuve');
    l.innerHTML = Array.from(v, (c) => {
      const r = (Math.random() * 10 - 5).toFixed(1), y = (Math.random() * 4 - 2).toFixed(1), o = (0.55 + Math.random() * 0.45).toFixed(2);
      return `<span style="transform:rotate(${r}deg) translateY(${y}px);opacity:${o}${Math.random() < 0.18 ? ';filter:blur(.6px)' : ''}">${c}</span>`;
    }).join('') + `<span class="g-h">${heure(quand)}</span>`;
    ruban.prepend(l); lignes++;
    while (ruban.children.length > 9) ruban.lastChild.remove();
    if (lignes >= 14) dechirer();
    return v;
  }

  // Mode vacances : hasard ordinaire du navigateur.
  function tourVacances() {
    if (enService) return;
    const a = new Uint8Array(32); crypto.getRandomValues(a);
    const h = hex(a);
    flux.textContent = h.slice(0, 48) + '… · ' + T.flux;
    imprimer(h, new Date());
  }

  // Mode en service : vrais blocs de l'Œil, lus sur le Worker.
  function copisteDuJour() {
    if (!M.get) return;
    M.get('data/citoyens.json').then((d) => {
      const libres = (d.citoyens || []).filter((c) => !(c[7] & 24));
      if (!libres.length) return;
      const c = libres[(d.jour || 0) % libres.length];
      copiste.innerHTML = T.cop + '<b>' + (M.esc ? M.esc(c[1]) : c[1]) + '</b>' + (M.rn ? ' (' + M.rn(c[2]) + ')' : '');
    }).catch(() => {});
  }

  function lireOeil() {
    if (!OEIL_URL) return;
    fetch(OEIL_URL, { cache: 'no-store' }).then((r) => r.ok ? r.json() : null).then((j) => {
      const blocs = j && Array.isArray(j.blocs) ? j.blocs.filter((b) => b && b.ok && /^[0-9a-f]{64}$/.test(b.bits)) : [];
      const der = blocs.length ? blocs[blocs.length - 1] : null;
      const frais = der && (Date.now() - Date.parse(der.t)) < FRAIS_MS;
      if (!frais) { if (enService) passer(false); return; }
      if (!enService) { passer(true); ruban.innerHTML = ''; }
      blocs.filter((b) => b.n > dernierN).slice(-8).forEach((b) => {
        const v = imprimer(b.bits, new Date(b.t));
        flux.textContent = b.bits;
        dernierN = b.n;
        setTimeout(() => { recopie.textContent = v; }, reduit ? 0 : 900);
      });
    }).catch(() => { if (enService) passer(false); });
  }

  function passer(service) {
    enService = service;
    document.querySelector('.generateur').classList.toggle('vacances', !service);
    setVoyants(service ? T.srv : T.vac, !service);
    if (service) copisteDuJour(); else { recopie.textContent = '······'; copiste.innerHTML = T.cop + T.none; }
  }

  $('g-dechirer').addEventListener('click', dechirer);
  passer(false);
  for (let i = 0; i < 5; i++) tourVacances();
  setInterval(tourVacances, PAS_MS);
  if (OEIL_URL) { lireOeil(); setInterval(lireOeil, 60000); }
})();
