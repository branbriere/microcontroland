// Page Histoire : la liste des présidents, ère par ère.
// data/histoire.json → les règnes terminés (une ligne ajoutée par la passerelle à chaque changement de président)
// data/latest.json   → le président en place
(function () {
  const $ = (s) => document.querySelector(s);
  const LANG = document.documentElement.lang === 'en' ? 'en' : 'fr';
  const BASE = window.MCL_BASE || '';
  const ESSAI = /[?&]essai\b/.test(location.search);        // ?essai : lit les éditions de la répétition générale
  const DATA = BASE + (ESSAI ? 'repetition/' : /[?&]demo\b/.test(location.search) ? 'demo/' : '');   // ?demo : pays d'exemple déjà évolué
  const T = (v) => (v && typeof v === 'object') ? (v[LANG] ?? v.fr ?? '') : (v ?? '');
  const esc = (s) => String(T(s)).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const loc = LANG === 'en' ? 'en-GB' : 'fr-FR';
  const REGION = { Mines: 'Mines', Champs: 'Fields', Raffineries: 'Refineries', Barrage: 'Dam', Port: 'Harbour', Ville: 'City' };
  const rn = (r) => LANG === 'en' ? (REGION[r] || r) : r;
  const date = (iso) => new Date(iso + 'T12:00:00').toLocaleDateString(loc, { day: 'numeric', month: 'short', year: 'numeric' });
  const dur = (h) => { const d = Math.floor(h / 24), r = h % 24; return LANG === 'en' ? (d ? `${d} d ${r} h` : `${r} h`) : (d ? `${d} j ${r} h` : `${r} h`); };
  const L = LANG === 'en'
    ? { era: (n) => `Era ${n}`, pres: 'President', from: 'Region', when: 'In power', len: 'Lasted', end: 'How it ended', regime: 'Main regime', now: 'In office', cur: 'still in power',
        terms: (n) => `${n} election${n > 1 ? 's' : ''} won`, none: 'History has not started yet: the first president will appear here.', down: 'History is temporarily unavailable.',
        sum: (p, e, r, c) => `${p} reign${p > 1 ? 's' : ''} over ${e} era${e > 1 ? 's' : ''}: ${r} toppled by the street, ${c} betrayed by a minister.`, longest: 'Longest reign', eraSum: (n) => `${n} reign${n > 1 ? 's' : ''}` }
    : { era: (n) => `Ère ${n}`, pres: 'Président', from: 'Région', when: 'Au pouvoir', len: 'Durée', end: 'Fin du règne', regime: 'Régime dominant', now: 'En fonction', cur: 'toujours au pouvoir',
        terms: (n) => `${n} élection${n > 1 ? 's' : ''} gagnée${n > 1 ? 's' : ''}`, none: 'L\'histoire n\'a pas encore commencé : le premier président apparaîtra ici.', down: 'L\'histoire est momentanément indisponible.',
        sum: (p, e, r, c) => `${p} règne${p > 1 ? 's' : ''} en ${e} ère${e > 1 ? 's' : ''} : ${r} renversé${r > 1 ? 's' : ''} par la rue, ${c} trahi${c > 1 ? 's' : ''} par un ministre.`, longest: 'Plus long règne', eraSum: (n) => `${n} règne${n > 1 ? 's' : ''}` };
  const get = (u) => fetch(DATA + u, { cache: 'no-store' }).then((r) => { if (!r.ok) throw 0; return r.json(); });

  Promise.all([get('data/histoire.json').catch(() => []), get('data/latest.json').catch(() => null)]).then(([rows, latest]) => {
    if (latest && latest.ages && latest.ages.age < 2 && window.MCL) { $('#summary').textContent = ''; window.MCL.wait($('#eras'), 2, latest); return; }
    rows = rows.slice();
    if (latest && latest.president) rows.push({ ere: latest.ere || 1, id: latest.president, nom: latest.presidentNom || '', region: latest.etat.capitale, current: true, since: T(latest.etat.auPouvoirDepuis), regime: latest.etat.regime });
    if (!rows.length) { $('#summary').textContent = L.none; return; }
    const done = rows.filter((r) => !r.current);
    const eras = [...new Set(rows.map((r) => r.ere))].sort((a, b) => b - a);
    const longest = done.slice().sort((a, b) => b.heures - a.heures)[0];
    $('#summary').textContent = L.sum(rows.length, eras.length, done.filter((r) => /rue|street/.test(T(r.finPar))).length, done.filter((r) => /ministre|minister/.test(T(r.finPar))).length)
      + (longest ? ` ${L.longest}${LANG === 'en' ? ': ' : ' : '}${longest.nom || 'nº ' + longest.id} (${dur(longest.heures)}).` : '');
    const rec = latest && latest.records && latest.records.length
      ? `<section class="month"><h2>${LANG === 'en' ? 'Records of the era' : 'Records de l\'ère'}</h2><div class="hist-scroll"><table class="hist"><tbody>${latest.records.map((r) =>
          `<tr><td><b>${esc(r.titre)}</b></td><td class="num">${esc(r.valeur)}</td><td>${esc(r.qui)}</td><td class="num">${LANG === 'en' ? 'day' : 'jour'} ${r.jour}</td></tr>`).join('')}</tbody></table></div></section>` : '';
    $('#eras').innerHTML = rec + eras.map((e) => {
      const list = rows.filter((r) => r.ere === e).reverse();
      return `<section class="month"><h2>${L.era(e)} <span>${L.eraSum(list.length)}</span></h2>
      <div class="hist-scroll"><table class="hist"><thead><tr><th>${L.pres}</th><th>${L.from}</th><th>${L.when}</th><th class="num">${L.len}</th><th>${L.end}</th><th>${L.regime}</th></tr></thead><tbody>
      ${list.map((r) => `<tr${r.current ? ' class="cur"' : ''}><td><b>${esc(r.nom || 'nº ' + r.id)}</b><small>nº ${r.id}${r.mandats > 1 ? ' · ' + L.terms(r.mandats) : ''}</small></td><td>${esc(rn(r.region))}</td>
        <td>${r.current ? L.now : date(r.debut) + (r.fin !== r.debut ? ' – ' + date(r.fin) : '')}</td><td class="num">${r.current ? esc(r.since) : dur(r.heures)}</td>
        <td>${r.current ? L.cur : esc(r.finPar)}</td><td>${esc(r.regime)}</td></tr>`).join('')}
      </tbody></table></div></section>`;
    }).join('');
  }).catch(() => { $('#summary').textContent = L.down; });
})();
