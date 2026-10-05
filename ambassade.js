// Ambassade : situation actuelle, lue dans la dernière édition.
(function () {
  const LANG = document.documentElement.lang === 'en' ? 'en' : 'fr';
  const BASE = window.MCL_BASE || '';
  const ESSAI = /[?&]essai\b/.test(location.search);        // ?essai : lit les éditions de la répétition générale
  const DATA = BASE + (ESSAI ? 'repetition/' : /[?&]demo\b/.test(location.search) ? 'demo/' : '');   // ?demo : pays d'exemple déjà évolué
  const T = (v) => (v && typeof v === 'object') ? (v[LANG] ?? v.fr ?? '') : (v ?? '');
  const REGION = { Mines: 'Mines', Champs: 'Fields', Raffineries: 'Refineries', Barrage: 'Dam', Port: 'Harbour', Ville: 'City' };
  const $ = (id) => document.getElementById(id);
  // Diplomatie : les questions du mois, le vote, et les lettres de l'ambassadeur avec leur pierre de Rosette.
  function diplo(e) {
    const el = $('diplo'), M = window.MCL; if (!el || !M) return;
    if (M.ageOf(e) < 4) { M.wait(el, 4, e); return; }
    const esc = M.esc, en = LANG === 'en', R = window.MCL_REGLAGES || {};
    Promise.all([M.get('data/ambassade.json'), M.get('data/lettres.json').catch(() => [])]).then(([a, letters]) => {
      letters = letters.filter((l) => l.ere === a.ere).reverse();
      const total = a.questions.reduce((n, q) => n + q.voix, 0);
      el.innerHTML = `<p>${en ? `Ambassador ${esc(a.ambassadeur)} answers the three most requested questions at the end of each month, in Microcontrôlandais, with a word-for-word translation.`
                                 : `L'ambassadeur ${esc(a.ambassadeur)} répond à la fin de chaque mois aux trois questions les plus demandées, en microcontrôlandais, avec la traduction mot à mot.`}</p>
        <ol class="qlist">${a.questions.map((q) => `<li><span>${esc(q.q)}</span>${R.votes ? `<b>${q.voix}</b>` : ''}</li>`).join('')}</ol>
        ${R.votes ? `<p><a class="btn" href="${esc(R.votes)}" rel="noopener">${en ? 'Vote for a question' : 'Voter pour une question'}</a> <span class="note">${en ? `${total} vote${total === 1 ? '' : 's'} this month. The form is hosted by a third party.` : `${total} vote${total > 1 ? 's' : ''} ce mois-ci. Le formulaire est hébergé par un service tiers.`}</span></p>`
                  : `<p class="note">${en ? 'Voting is not open yet: for now the country chooses which questions it answers.' : 'Le vote n\'est pas encore ouvert : pour l\'instant, le pays choisit lui-même les questions auxquelles il répond.'}</p>`}
        ${letters.length ? letters.map((l, i) => `<details class="letter"${i ? '' : ' open'}><summary>${en ? 'Letter No.' : 'Lettre nº'} ${l.n} · ${esc(M.fmtDate(l.date))}</summary>
          ${l.lignes.map((x) => `<div class="qa"><div class="k2">${esc(x.question)}</div><p class="signal" lang="x-mcl">${esc(x.reponse) || '…'}</p><p class="note">${en ? 'Word for word: ' : 'Mot à mot : '}${esc(x.litteral)}</p></div>`).join('')}
          <p class="sign">— ${esc(l.signature)}, ${en ? 'ambassador' : 'ambassadeur'}</p>
          <table class="hist lex"><thead><tr><th>${en ? 'Rosetta stone' : 'Pierre de Rosette'}</th><th></th></tr></thead><tbody>${l.rosette.map((r) => `<tr><td><b class="mot">${esc(r.mot)}</b></td><td>${esc(r.sens)}</td></tr>`).join('')}</tbody></table></details>`).join('')
          : `<p class="note">${en ? 'The first letter will be published on the last day of the month.' : 'La première lettre paraîtra le dernier jour du mois.'}</p>`}`;
    }).catch(() => {});
  }

  fetch(DATA + 'data/latest.json', { cache: 'no-store' }).then((r) => { if (r.status === 404) return null; if (!r.ok) throw 0; return r.json(); }).then((e) => {
    if (!e) {   // avant la première édition : le pays n'a encore rien publié
      $('l-note').textContent = LANG === 'en' ? 'The country has not published anything yet. The situation will appear here after the first issue, at 8 pm.' : 'Le pays n\'a encore rien publié. La situation s\'affichera ici après la première édition, à 20 h.';
      return;
    }
    const s = e.etat, m = s.ministres;
    $('l-regime').textContent = T(s.regime);
    $('l-pres').textContent = e.president ? (e.presidentNom || (LANG === 'en' ? 'No. ' : 'nº ') + e.president) : (LANG === 'en' ? 'Election under way' : 'Élection en cours');
    $('l-cap').textContent = !s.capitale ? '—' : LANG === 'en' ? (REGION[s.capitale] || s.capitale) : s.capitale;
    const d = e.jourEre || e.day, f = s.foi;
    const era = e.ere ? (LANG === 'en' ? `, era ${e.ere}` : `, ère ${e.ere}`) : '';
    const faith = !f ? '' : LANG === 'en' ? ` Faith: ${f.croyants}% believers, ${f.agnostiques}% agnostics, ${f.athees}% atheists.` : ` Foi : ${f.croyants} % de croyants, ${f.agnostiques} % d'agnostiques, ${f.athees} % d'athées.`;
    $('l-note').textContent = LANG === 'en'
      ? `Situation on day ${d} of the Republic${era}: ${m ? m + ' minister' + (m > 1 ? 's' : '') : 'no ministers'}, president in power for ${T(s.auPouvoirDepuis)}.${faith} Updated every evening at 8 pm.`
      : `Situation au jour ${d} de la République${era} : ${m ? m + ' ministre' + (m > 1 ? 's' : '') : 'aucun ministre'}, président au pouvoir depuis ${T(s.auPouvoirDepuis)}.${faith} Mise à jour chaque soir à 20 h.`;
    diplo(e);
  }).catch(() => { $('l-note').textContent = LANG === 'en' ? 'Current situation temporarily unavailable.' : 'Situation actuelle momentanément indisponible.'; });
})();
