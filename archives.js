// Page Archives : liste de toutes les éditions, groupées par mois, avec recherche et filtre par rubrique.
(function () {
  const $ = (s) => document.querySelector(s);
  const LANG = document.documentElement.lang === 'en' ? 'en' : 'fr';
  const BASE = window.MCL_BASE || '';
  const ESSAI = /[?&]essai\b/.test(location.search);        // ?essai : lit les éditions de la répétition générale
  const DATA = BASE + (ESSAI ? 'repetition/' : /[?&]demo\b/.test(location.search) ? 'demo/' : '');   // ?demo : pays d'exemple déjà évolué
  const T = (v) => (v && typeof v === 'object') ? (v[LANG] ?? v.fr ?? '') : (v ?? '');
  const esc = (s) => String(T(s)).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const loc = LANG === 'en' ? 'en-GB' : 'fr-FR';
  const L = LANG === 'en'
    ? { all: 'All', none: 'No issue matches.', day: (n) => `Day ${n}`, issues: (n) => `${n} issue${n > 1 ? 's' : ''}`,
        sum: (n, d, b, c) => `${n} issue${n > 1 ? 's' : ''} since day ${d}: ${b} regime change${b > 1 ? 's' : ''} and ${c} overthrow${c > 1 ? 's' : ''} on the front page.`,
        empty: 'No archive yet: the first issue comes out tonight at 8 pm.', down: 'The archive is temporarily unavailable.',
        change: 'Regime change', coup: /Revolution|Palace coup/ }
    : { all: 'Toutes', none: 'Aucune édition ne correspond.', day: (n) => `Jour ${n}`, issues: (n) => `${n} édition${n > 1 ? 's' : ''}`,
        sum: (n, d, b, c) => `${n} édition${n > 1 ? 's' : ''} depuis le jour ${d} : ${b} changement${b > 1 ? 's' : ''} de régime et ${c} renversement${c > 1 ? 's' : ''} à la une.`,
        empty: 'Pas encore d\'archives : la première édition paraîtra ce soir à 20 h.', down: 'Les archives sont momentanément indisponibles.',
        change: 'Changement de régime', coup: /Révolution|Coup de palais/ };
  let all = [], rub = null, q = '';

  function draw() {
    const items = all.filter((a) => (!rub || T(a.rubrique) === rub) && (!q || (T(a.titre) + ' ' + T(a.rubrique)).toLowerCase().includes(q)));
    if (!items.length) { $('#list').innerHTML = `<p class="empty">${L.none}</p>`; return; }
    const groups = new Map();
    items.forEach((a) => { const k = new Date(a.date + 'T12:00:00').toLocaleDateString(loc, { month: 'long', year: 'numeric' }); if (!groups.has(k)) groups.set(k, []); groups.get(k).push(a); });
    $('#list').innerHTML = [...groups].map(([m, list]) => `<section class="month"><h2>${m.charAt(0).toUpperCase() + m.slice(1)} <span>${L.issues(list.length)}</span></h2>
      <ol class="arch-list">${list.map((a) => `<li><a href="./#jour-${a.day}"><span class="d">${L.day(a.day)}<br>${new Date(a.date + 'T12:00:00').toLocaleDateString(loc, { weekday: 'long', day: 'numeric', month: 'long' })}</span><span><span class="k2">${esc(a.rubrique)}</span><b>${esc(a.titre)}</b></span></a></li>`).join('')}</ol></section>`).join('');
  }

  function chips() {
    const counts = {}; all.forEach((a) => { const r = T(a.rubrique); counts[r] = (counts[r] || 0) + 1; });
    const names = [null, ...Object.keys(counts).sort((x, y) => counts[y] - counts[x])];
    $('#chips').innerHTML = names.map((n) => `<button type="button" aria-pressed="${n === rub}" data-r="${n === null ? '' : esc(n)}">${n === null ? L.all : esc(n) + ' · ' + counts[n]}</button>`).join('');
  }

  $('#chips').addEventListener('click', (e) => { const b = e.target.closest('button'); if (!b) return; rub = b.dataset.r || null; chips(); draw(); });
  $('#q').addEventListener('input', (e) => { q = e.target.value.trim().toLowerCase(); draw(); });

  // L'année en cours est dans data/archive.json ; chaque année terminée est rangée dans data/archive-AAAA.json.
  const years = []; for (let y = new Date().getFullYear() - 1; y >= 2026; y--) years.push(y);
  const old = Promise.all(years.map((y) => fetch(DATA + `data/archive-${y}.json`, { cache: 'no-store' }).then((r) => r.ok ? r.json() : []).catch(() => [])));
  fetch(DATA + 'data/archive.json', { cache: 'no-store' }).then((r) => { if (r.status === 404) return []; if (!r.ok) throw 0; return r.json(); }).then((cur) => old.then((lists) => cur.concat(...lists))).then((a) => {
    a.sort((x, y) => y.day - x.day);  // la plus récente en premier, quel que soit l'ordre du fichier
    all = a;
    const coups = a.filter((x) => L.coup.test(T(x.rubrique))).length;
    const changes = a.filter((x) => T(x.rubrique) === L.change).length;
    $('#summary').textContent = a.length ? L.sum(a.length, a[a.length - 1].day, changes, coups) : L.empty;
    chips(); draw();
  }).catch(() => { $('#summary').textContent = L.down; });
})();
