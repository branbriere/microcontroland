// Le Temple : foi du pays lue dans la dernière édition. Le Temple, le grand prêtre et la Calculette sont prévus (MAJ 3) :
// tant que l'édition ne publie pas de bloc « temple », la page reste en attente et le conseil ne siège pas.
(function () {
  const M = window.MCL; if (!M) return;
  const en = M.LANG === 'en', $ = (id) => document.getElementById(id), box = $('temple');
  const pct = (n) => en ? `${n}%` : `${n} %`;
  const PRES = { croyant: en ? 'believer' : 'croyant', agnostique: en ? 'agnostic' : 'agnostique', athee: en ? 'atheist' : 'athée', 'athée': en ? 'atheist' : 'athée' };
  M.latest().then((e) => {
    const f = e && e.etat && e.etat.foi;
    if (!f) return;
    $('t-foi').innerHTML = en
      ? `<b>${pct(f.croyants)}</b> believers · <b>${pct(f.agnostiques)}</b> agnostics · <b>${pct(f.athees)}</b> atheists<br>Day ${M.esc(e.jourEre || e.day)} of the Republic, figures from the ${M.esc(M.fmtDate(e.date))} issue.`
      : `<b>${pct(f.croyants)}</b> de croyants · <b>${pct(f.agnostiques)}</b> d'agnostiques · <b>${pct(f.athees)}</b> d'athées<br>Jour ${M.esc(e.jourEre || e.day)} de la République, chiffres de l'édition du ${M.esc(M.fmtDate(e.date))}.`;
    if (f.croyants === 0) { box.classList.add('sans-croyants'); return; }
    const t = e.temple && e.temple.ouvert ? e.temple : null;
    const set = (k, v) => { const el = document.querySelector(`[data-v="${k}"]`); if (el) el.textContent = v; };
    const sub = (k, v) => { const el = document.querySelector(`[data-s="${k}"]`); if (el) el.textContent = v; };
    sub('croyants', en ? `${pct(f.croyants)} of the country` : `${pct(f.croyants)} du pays`);
    sub('agnostiques', en ? `${pct(f.agnostiques)} of the country` : `${pct(f.agnostiques)} du pays`);
    sub('athees', en ? `${pct(f.athees)} of the country` : `${pct(f.athees)} du pays`);
    const nom = e.presidentNom || (e.president ? (en ? 'No. ' : 'nº ') + e.president : '');
    if (nom) sub('pres', (en ? 'head of state: ' : 'chef de l\'État : ') + nom + (f.president ? ` (${PRES[f.president] || f.president})` : ''));
    const absent = en ? 'does not sit yet' : 'ne siège pas';
    ['gp', 'pres', 'croyants', 'agnostiques', 'athees'].forEach((k) => set(k, t ? (en ? 'deliberating' : 'délibère') : absent));
    if (!t) { set('gp', en ? 'not elected yet' : 'pas encore élu'); return; }
    $('t-etat').hidden = true;
    const loi = $('t-loi'), pourTous = f.croyants > f.agnostiques + f.athees;
    loi.innerHTML = pourTous
      ? (en ? `<b>Religious laws: the whole country.</b> Believers (${pct(f.croyants)}) outnumber non-believers.` : `<b>Lois religieuses : tout le pays.</b> Les croyants (${pct(f.croyants)}) sont plus nombreux que les non-croyants.`)
      : (en ? `<b>Religious laws: believers only.</b> Believers (${pct(f.croyants)}) are fewer than non-believers (${pct(f.agnostiques + f.athees)}).` : `<b>Lois religieuses : croyants seulement.</b> Les croyants (${pct(f.croyants)}) sont moins nombreux que les non-croyants (${pct(f.agnostiques + f.athees)}).`);
    loi.hidden = false;
  }).catch(() => {});
})();
