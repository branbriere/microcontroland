// Outils communs à toutes les pages : langue, lecture des données, âges de la civilisation.
// Une rubrique dont l'âge n'est pas encore atteint affiche « en attente d'évolution de la civilisation ».
(function () {
  const LANG = document.documentElement.lang === 'en' ? 'en' : 'fr';
  const BASE = window.MCL_BASE || '';
  const q = location.search;
  const MODE = /[?&]essai\b/.test(q) ? 'essai' : /[?&]demo\b/.test(q) ? 'demo' : '';   // ?essai : répétition générale · ?demo : pays d'exemple déjà évolué
  const DATA = BASE + (MODE === 'essai' ? 'repetition/' : MODE === 'demo' ? 'demo/' : '');
  const T = (v) => (v && typeof v === 'object' && !Array.isArray(v)) ? (v[LANG] ?? v.fr ?? '') : (v ?? '');
  const esc = (s) => String(T(s)).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  const get = (u) => fetch(DATA + u, { cache: 'no-store' }).then((r) => { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); });
  // Avant la première édition, le fichier n'existe pas : le pays est alors à l'âge de la Fondation, jour 0.
  const DAY0 = {"jour": 0, "ages": {"age": 0, "etapes": [{"nom": {"fr": "la Fondation", "en": "the Founding"}, "ouvre": {"fr": "La gazette paraît chaque soir.", "en": "The paper comes out every evening."}, "ouvert": true, "progres": {"fr": "", "en": ""}}, {"nom": {"fr": "la Parole", "en": "Speech"}, "ouvre": {"fr": "Les régions partagent leurs premiers mots : la page « La langue » s'ouvre.", "en": "The regions share their first words: the “Language” page opens."}, "ouvert": false, "progres": {"fr": "0/10 mots communs", "en": "0/10 shared words"}}, {"nom": {"fr": "la Mémoire", "en": "Memory"}, "ouvre": {"fr": "Le pays tient ses annales : records et passé des personnages, page « Histoire ».", "en": "The country keeps its annals: records and the characters' pasts, on the “History” page."}, "ouvert": false, "progres": {"fr": "jour 0/14, 0/3 règnes ou 0/6 élections", "en": "day 0/14, 0/3 reigns or 0/6 elections"}}, {"nom": {"fr": "l'État civil", "en": "the Civil Registry"}, "ouvre": {"fr": "Chaque citoyen est inscrit au registre : on peut en adopter un et le suivre.", "en": "Every citizen is entered in the registry: you can adopt one and follow them."}, "ouvert": false, "progres": {"fr": "jour 0/21, 0/20 mots communs", "en": "day 0/21, 0/20 shared words"}}, {"nom": {"fr": "la Diplomatie", "en": "Diplomacy"}, "ouvre": {"fr": "L'ambassade ouvre : questions du mois et lettre de l'ambassadeur.", "en": "The embassy opens: questions of the month and the ambassador's letter."}, "ouvert": false, "progres": {"fr": "jour 0/30, 0/28 mots communs", "en": "day 0/30, 0/28 shared words"}}, {"nom": {"fr": "la Curiosité", "en": "Curiosity"}, "ouvre": {"fr": "Le Centre de recherche émet un message vers l'extérieur et écoute.", "en": "The Research Centre sends a message to the outside and listens."}, "ouvert": false, "progres": {"fr": "jour 0/60, 0/34 mots communs, 0/5 jours de paix", "en": "day 0/60, 0/34 shared words, 0/5 peaceful days"}}]}};
  let latestP = null;
  const latest = () => latestP || (latestP = fetch(DATA + 'data/latest.json', { cache: 'no-store' }).then((r) => { if (r.status === 404) return DAY0; if (!r.ok) throw new Error('latest ' + r.status); return r.json(); }));
  const REGION = ['Mines', 'Champs', 'Raffineries', 'Barrage', 'Port', 'Ville'];
  const REGION_EN = { Mines: 'Mines', Champs: 'Fields', Raffineries: 'Refineries', Barrage: 'Dam', Port: 'Harbour', Ville: 'City' };
  const rn = (r) => { const name = typeof r === 'number' ? REGION[r] : r; return LANG === 'en' ? (REGION_EN[name] || name) : name; };
  const fmtDate = (iso, opts) => new Date(iso + 'T12:00:00').toLocaleDateString(LANG === 'en' ? 'en-GB' : 'fr-FR', opts || { day: 'numeric', month: 'long', year: 'numeric' });
  const L = LANG === 'en'
    ? { ages: 'The ages of the civilisation', open: 'reached', waitK: 'Waiting for the civilisation to evolve', waitT: (n) => `This section opens in the age of ${n}`,
        where: 'Where the country stands', locked: 'Not open yet: the civilisation has not reached this age', age: 'Age', noData: 'The country has not published anything yet.',
        demo: 'Demo: a sample country that has already lived 100 days. Nothing here comes from the real box.', essai: 'Dress rehearsal: these pages show gateway tests.' }
    : { ages: 'Les âges de la civilisation', open: 'atteint', waitK: 'En attente d\'évolution de la civilisation', waitT: (n) => `Cette rubrique s'ouvrira à l'âge de ${n}`,
        where: 'Où en est le pays', locked: 'Pas encore ouvert : la civilisation n\'a pas atteint cet âge', age: 'Âge', noData: 'Le pays n\'a encore rien publié.',
        demo: 'Démonstration : un pays d\'exemple qui a déjà vécu 100 jours. Rien ici ne vient de la vraie boîte.', essai: 'Répétition générale : ces pages montrent des essais de la passerelle.' };
  const ageOf = (e) => (e && e.ages ? e.ages.age : 0);

  // La frise des âges : étapes atteintes, et ce qui manque pour la suivante.
  function frise(e) {
    if (!e || !e.ages) return '';
    return `<ol class="frise">${e.ages.etapes.map((s, i) => `<li class="${s.ouvert ? 'ok' : i === e.ages.age + 1 ? 'soon' : 'later'}"><b>${esc(s.nom).replace(/^(la |l'|the )/i, (m) => m.charAt(0).toUpperCase() + m.slice(1))}</b>` +
      `<span>${s.ouvert ? L.open : esc(s.progres)}</span></li>`).join('')}</ol>`;
  }

  // Panneau d'attente d'une rubrique fermée.
  function wait(el, need, e) {
    const s = e && e.ages ? e.ages.etapes[need] : null;
    el.innerHTML = `<div class="wait"><div class="k2">${L.waitK}</div><h2>${s ? L.waitT(esc(s.nom)) : L.noData}</h2>` +
      (s ? `<p>${esc(s.ouvre)}</p><p class="prog"><b>${L.where}${LANG === 'en' ? ': ' : ' : '}</b>${esc(s.progres) || '—'}</p>` : '') + frise(e) + '</div>';
  }

  // Les liens gardent le mode (?essai ou ?demo) d'une page à l'autre.
  if (MODE) document.querySelectorAll('a[href]').forEach((a) => {
    const h = a.getAttribute('href');
    if (/^(\.\/|\.\.\/|[\w./-]+\.html)$/.test(h) && !/^https?:/.test(h)) a.setAttribute('href', h + '?' + MODE);
  });
  if (MODE) { const p = document.createElement('p'); p.className = 'stale'; p.setAttribute('role', 'status'); p.textContent = MODE === 'demo' ? L.demo : L.essai; const nav = document.querySelector('nav.main'); if (nav) nav.after(p); }

  // Dans le menu, les rubriques encore fermées sont marquées d'un sablier.
  const PAGE_AGE = { 'langue.html': 1, 'histoire.html': 2, 'citoyen.html': 3, 'recherche.html': 5 };
  latest().then((e) => {
    document.querySelectorAll('nav.main > a').forEach((a) => {
      const f = (a.getAttribute('href') || '').split('?')[0];
      if (PAGE_AGE[f] > ageOf(e)) { a.classList.add('locked'); a.title = L.locked; }
    });
  }).catch(() => {});

  window.MCL = { LANG, BASE, DATA, MODE, T, esc, get, latest, rn, fmtDate, frise, wait, ageOf, REGION, L };
})();
