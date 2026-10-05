// Page « La langue » : le lexique commun, les sons de l'ère et qui comprend qui.
(function () {
  const { LANG, T, esc, get, latest, rn, wait, ageOf, REGION } = window.MCL;
  const $ = (s) => document.querySelector(s);
  const L = LANG === 'en'
    ? { sum: (p, i, e) => `Era ${e}: ${p} shared word${p > 1 ? 's' : ''} out of ${i} ideas the country has lived through.`, idea: 'Idea', word: 'Word', agree: 'Regions that say it', shared: 'Shared words', forming: 'Still being settled',
        sounds: 'The sounds of this era', cons: 'Consonants', vow: 'Vowels', soundsNote: 'Every era draws its own sounds. Names and words are built from them, so each era sounds different.',
        comp: 'Who understands whom', compNote: 'Share of ideas for which two regions use the same word. A region in revolt stops listening and drifts away.', none: 'No word is settled yet.',
        how: 'How a word is born', howText: 'Each hour the gateway names an idea. Every region says its word; one of them is picked as the speaker and the others learn from it. An idea only enters the language once the country has lived it: no word for “revolt” before the first revolt.', down: 'The lexicon is temporarily unavailable.' }
    : { sum: (p, i, e) => `Ère ${e} : ${p} mot${p > 1 ? 's' : ''} commun${p > 1 ? 's' : ''} sur ${i} idées que le pays a vécues.`, idea: 'Idée', word: 'Mot', agree: 'Régions qui le disent', shared: 'Mots communs', forming: 'Encore en discussion',
        sounds: 'Les sons de cette ère', cons: 'Consonnes', vow: 'Voyelles', soundsNote: 'Chaque ère tire au sort ses propres sons. Les prénoms et les mots en sont faits : chaque ère a donc sa musique.',
        comp: 'Qui comprend qui', compNote: 'Part des idées pour lesquelles deux régions emploient le même mot. Une région en révolte n\'écoute plus et s\'éloigne.', none: 'Aucun mot n\'est encore fixé.',
        how: 'Comment naît un mot', howText: 'Chaque heure, la passerelle propose une idée. Toutes les régions disent leur mot ; l\'une d\'elles est tirée au sort comme oratrice et les autres apprennent d\'elle. Une idée n\'entre dans la langue que lorsque le pays l\'a vécue : pas de mot pour « révolte » avant la première révolte.', down: 'Le lexique est momentanément indisponible.' };
  const dots = (n) => `<span class="dots" aria-label="${n}/6">${'●'.repeat(n)}${'○'.repeat(6 - n)}</span>`;
  const table = (rows) => rows.length ? `<table class="hist lex"><thead><tr><th>${L.idea}</th><th>${L.word}</th><th>${L.agree}</th></tr></thead><tbody>` +
    rows.map((m) => `<tr><td>${esc(m.idee)}</td><td><b class="mot">${esc(m.mot)}</b></td><td>${dots(m.accord)}</td></tr>`).join('') + '</tbody></table>' : `<p class="note">${L.none}</p>`;

  latest().then((e) => {
    if (ageOf(e) < 1) { $('#summary').textContent = ''; wait($('#langue'), 1, e); return; }
    return get('data/langue.json').then((d) => {
      $('#summary').textContent = L.sum(d.partages, d.idees, d.ere);
      const by = (a, b) => b.accord - a.accord || T(a.idee).localeCompare(T(b.idee));
      const shared = d.mots.filter((m) => m.accord >= 5).sort(by), forming = d.mots.filter((m) => m.accord < 5).sort(by);
      const c = d.comprehension;
      $('#langue').innerHTML = `
        <section class="month"><h2>${L.shared} <span>${shared.length}</span></h2><div class="hist-scroll">${table(shared)}</div></section>
        ${forming.length ? `<section class="month"><h2>${L.forming} <span>${forming.length}</span></h2><div class="hist-scroll">${table(forming)}</div></section>` : ''}
        <section class="month"><h2>${L.sounds}</h2><p><b>${L.cons}</b> <span class="sons">${d.sons.consonnes.map(esc).join(' · ')}</span><br><b>${L.vow}</b> <span class="sons">${d.sons.voyelles.map(esc).join(' · ')}</span></p><p class="note">${L.soundsNote}</p></section>
        <section class="month"><h2>${L.comp}</h2><div class="hist-scroll"><table class="matrix"><thead><tr><th></th>${REGION.map((r) => `<th>${esc(rn(r))}</th>`).join('')}</tr></thead><tbody>
          ${c.map((row, i) => `<tr><th>${esc(rn(i))}</th>${row.map((v, j) => i === j ? '<td class="self">—</td>' : `<td style="background:color-mix(in srgb,var(--mask) ${Math.round(v * 0.55)}%,transparent)">${v} %</td>`).join('')}</tr>`).join('')}
        </tbody></table></div><p class="note">${L.compNote}</p></section>
        <section class="month"><h2>${L.how}</h2><p>${L.howText}</p></section>`;
    });
  }).catch(() => { $('#summary').textContent = L.down; });
})();
