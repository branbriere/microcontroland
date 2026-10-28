// Ambassade : situation actuelle, lue dans la dernière édition.
(function () {
  const LANG = document.documentElement.lang === 'en' ? 'en' : 'fr';
  const BASE = window.MCL_BASE || '';
  const ESSAI = false;   // la répétition générale n'est plus publiée sur le site public (11 octobre 2026)        // ?essai : lit les éditions de la répétition générale
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

  // À l'âge de la Diplomatie, la vitrine du pays déménage à l'Office du tourisme ; la Relique et le guichet des visas ouvrent.
  function vitrine(e) {
    const M = window.MCL; if (!M) return;
    const ouvert = M.ageOf(e) >= 4, en = LANG === 'en';
    const v = $('vitrine'), d = $('demenage'), rq = $('rq-etat');
    if (ouvert && v && d) { v.hidden = true; d.hidden = false; }
    if (rq) {
      const s = e && e.ages ? e.ages.etapes[4] : null;
      rq.textContent = ouvert ? (en ? 'Open. Admission free, silence appreciated.' : 'Ouverte. Entrée libre, silence apprécié.')
        : (en ? 'The hall opens with the Embassy, in the age of Diplomacy.' : 'La salle ouvre avec l\'Ambassade, à l\'âge de la Diplomatie.') + (s && M.T(s.progres) ? (en ? ' Where the country stands: ' : ' Où en est le pays : ') + M.T(s.progres) + '.' : '');
    }
    visa(e, ouvert);
  }

  // Guichet des visas : un visa décoratif, dessiné dans le navigateur. Aucun champ, rien n'est envoyé ni enregistré.
  function visa(e, ouvert) {
    const el = $('visa'), M = window.MCL; if (!el || !M) return;
    const en = LANG === 'en', esc = M.esc;
    if (!ouvert) { el.innerHTML = `<p class="note">${en ? 'The visa desk opens with the Embassy, in the age of Diplomacy.' : 'Le guichet des visas ouvre avec l\'Ambassade, à l\'âge de la Diplomatie.'}</p>`; return; }
    el.innerHTML = `<p><button type="button" class="btn" id="visa-go">${en ? 'Stamp my visa' : 'Tamponner mon visa'}</button></p><div id="visa-out"></div>`;
    $('visa-go').addEventListener('click', () => {
      M.get('data/ambassade.json').catch(() => ({})).then((a) => {
        const now = new Date();
        const jour = now.toLocaleDateString(en ? 'en-GB' : 'fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });
        const regime = M.T(e.etat && e.etat.regime) || '—';
        const sign = a && a.ambassadeur ? (en ? `Signed: ${a.ambassadeur}, ambassador.` : `Signé : ${a.ambassadeur}, ambassadeur.`) : (en ? 'Signed: the Embassy.' : 'Signé : l\'Ambassade.');
        const rows = en
          ? [['Holder', 'Visitor'], ['Issued on', jour], ['Day of the Republic', String(e.jourEre || e.day || '?')], ['Regime of the day', regime], ['Valid until', 'the next power cut'], ['Border', 'closed (waterproof cable gland)']]
          : [['Titulaire', 'Visiteur'], ['Délivré le', jour], ['Jour de la République', String(e.jourEre || e.day || '?')], ['Régime du jour', regime], ['Valable jusqu\'à', 'la prochaine coupure de courant'], ['Frontière', 'fermée (passe-câble étanche)']];
        const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 560 320" role="img" aria-label="${en ? 'Visitor visa' : 'Visa de visiteur'}">
<rect x="4" y="4" width="552" height="312" rx="10" fill="#f4f6f2" stroke="#0d6a47" stroke-width="3"/>
<rect x="4" y="4" width="552" height="44" rx="10" fill="#0d6a47"/><rect x="4" y="38" width="552" height="10" fill="#0d6a47"/>
<text x="24" y="33" font-family="Arial Narrow,Arial,sans-serif" font-weight="700" font-size="15" letter-spacing="1" fill="#f4f6f2">${en ? 'REPUBLIC OF MICROCONTRÔLAND · VISITOR VISA' : 'RÉPUBLIQUE DE MICROCONTRÔLAND · VISA DE VISITEUR'}</text>
${rows.map((r, i) => `<text x="24" y="${82 + i * 30}" font-family="Courier New,monospace" font-size="12" fill="#56655c">${esc(r[0]).toUpperCase()}</text><text x="200" y="${82 + i * 30}" font-family="Georgia,serif" font-size="15" fill="#14201a">${esc(r[1])}</text>`).join('')}
<g transform="rotate(-14 480 150)"><circle cx="480" cy="150" r="50" fill="none" stroke="#b8352a" stroke-width="4" opacity=".85"/><circle cx="480" cy="150" r="41" fill="none" stroke="#b8352a" stroke-width="1.5" opacity=".85"/>
<text x="480" y="146" text-anchor="middle" font-family="Arial Narrow,Arial,sans-serif" font-weight="700" font-size="22" fill="#b8352a" opacity=".85">${en ? 'SEEN' : 'VU'}</text>
<text x="480" y="166" text-anchor="middle" font-family="Arial Narrow,Arial,sans-serif" font-weight="700" font-size="11" letter-spacing="1" fill="#b8352a" opacity=".85">${en ? 'EMBASSY' : 'AMBASSADE'}</text></g>
<text x="24" y="284" font-family="Georgia,serif" font-style="italic" font-size="13" fill="#56655c">${esc(sign)}</text>
<text x="24" y="303" font-family="Georgia,serif" font-style="italic" font-size="12" fill="#56655c">${en ? 'No value, no record, no border opened.' : 'Sans valeur, sans enregistrement, aucune frontière ouverte.'}</text>
</svg>`;
        const url = URL.createObjectURL(new Blob([svg], { type: 'image/svg+xml' }));
        $('visa-out').innerHTML = `<div class="amb-visa">${svg}</div><p><a class="btn ghost" href="${url}" download="${en ? 'visa-microcontroland.svg' : 'visa-microcontroland.svg'}">${en ? 'Save the visa (SVG)' : 'Enregistrer le visa (SVG)'}</a></p>`;
      });
    });
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
    vitrine(e);
  }).catch(() => { $('l-note').textContent = LANG === 'en' ? 'Current situation temporarily unavailable.' : 'Situation actuelle momentanément indisponible.'; });
})();
