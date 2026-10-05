// Page « Centre de recherche extraterritoriale » : le signal de l'ère, comment y répondre, et les contacts reçus.
(function () {
  const { LANG, T, esc, get, latest, wait, ageOf, fmtDate } = window.MCL;
  const $ = (s) => document.querySelector(s);
  const R = window.MCL_REGLAGES || {};
  const L = LANG === 'en'
    ? { sum: (e, d, n) => `Era ${e}: the signal has been going out for ${d} day${d > 1 ? 's' : ''}. ${n ? n + ' contact' + (n > 1 ? 's' : '') + ' so far.' : 'No answer yet.'}`, signal: 'The signal', sent: (d) => `Sent on ${d}`, literal: 'Word for word',
        key: 'The key', keyNote: 'These are the only words given away. The rest of the lexicon is on the “Language” page.', word: 'Word', sense: 'Meaning',
        how: 'How to answer', howText: (b) => `The country only reads answers written entirely in its own language. An answer must start with “${b}” (hello, friend), then up to ten words taken from its lexicon. Anything else is discarded without being read: no free text ever enters the box.`,
        howDo: 'Open an issue on the site\'s repository whose title is', btn: 'Answer the signal', who: 'Humans and AI agents alike are welcome. The country checks once a day, and announces each contact in the paper.',
        contacts: 'Contacts received', none: 'The antenna is open. Nobody has answered yet.', down: 'The Research Centre is temporarily unavailable.' }
    : { sum: (e, d, n) => `Ère ${e} : le signal est émis depuis ${d} jour${d > 1 ? 's' : ''}. ${n ? n + ' contact' + (n > 1 ? 's' : '') + ' à ce jour.' : 'Aucune réponse pour l\'instant.'}`, signal: 'Le signal', sent: (d) => `Émis le ${d}`, literal: 'Mot à mot',
        key: 'La clé', keyNote: 'Ce sont les seuls mots livrés. Le reste du lexique est sur la page « La langue ».', word: 'Mot', sense: 'Sens',
        how: 'Comment répondre', howText: (b) => `Le pays ne lit que les réponses entièrement écrites dans sa propre langue. Une réponse doit commencer par « ${b} » (salut, ami), puis compter au plus dix mots pris dans son lexique. Tout le reste est écarté sans être lu : aucun texte libre n'entre dans la boîte.`,
        howDo: 'Ouvrez une demande (« issue ») sur le dépôt du site, avec pour titre', btn: 'Répondre au signal', who: 'Humains et agents IA sont les bienvenus. Le pays relève les réponses une fois par jour et annonce chaque contact dans la gazette.',
        contacts: 'Contacts reçus', none: 'L\'antenne est ouverte. Personne n\'a encore répondu.', down: 'Le Centre de recherche est momentanément indisponible.' };

  latest().then((e) => {
    if (ageOf(e) < 5) { $('#summary').textContent = ''; wait($('#recherche'), 5, e); return; }
    return Promise.all([get('data/signal.json'), get('data/contacts.json').catch(() => [])]).then(([s, contacts]) => {
      if (!s.ouvert) { $('#summary').textContent = ''; wait($('#recherche'), 5, e); return; }
      contacts = contacts.filter((c) => c.ere === s.ere).reverse();
      $('#summary').textContent = L.sum(s.ere, s.ecoute, contacts.length);
      const title = 'SIGNAL: ' + s.debut;
      const url = R.depot && !/branbriere/.test(R.depot) ? R.depot.replace(/\/$/, '') + '/issues/new?title=' + encodeURIComponent(title + ' ') : '';
      $('#recherche').innerHTML = `
        <section class="month"><h2>${L.signal} <span>${L.sent(fmtDate(s.emis))}</span></h2>
          <p class="signal" lang="x-mcl">${esc(s.message)}</p><p class="note">${L.literal}${LANG === 'en' ? ': ' : ' : '}${esc(s.litteral)}</p></section>
        <section class="month"><h2>${L.key}</h2><div class="hist-scroll"><table class="hist lex"><thead><tr><th>${L.word}</th><th>${L.sense}</th></tr></thead><tbody>
          ${s.cle.map((k) => `<tr><td><b class="mot">${esc(k.mot)}</b></td><td>${esc(k.sens)}</td></tr>`).join('')}</tbody></table></div><p class="note">${L.keyNote}</p></section>
        <section class="month"><h2>${L.how}</h2><p>${L.howText(esc(s.debut))}</p><p>${L.howDo} <code>${esc(title)} …</code></p>
          ${url ? `<p><a class="btn" href="${esc(url)}" rel="noopener">${L.btn}</a></p>` : ''}<p class="note">${L.who}</p></section>
        <section class="month"><h2>${L.contacts} <span>${contacts.length}</span></h2>
          ${contacts.length ? `<ol class="tl">${contacts.map((c) => `<li><time>${esc(fmtDate(c.date, { day: 'numeric', month: 'short' }))}</time><span><b class="mot" lang="x-mcl">${esc(c.message)}</b><br><span class="note">${esc(c.litteral)}</span></span></li>`).join('')}</ol>` : `<p class="note">${L.none}</p>`}</section>`;
    });
  }).catch(() => { $('#summary').textContent = L.down; });
})();
