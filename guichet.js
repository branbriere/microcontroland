// Le guichet de l'Ambassadeur (20/11/2026) : une question, une réponse en langue de bois.
// Worker « ambassade-guichet » sur /guichet/ : il ne garde ni la question, ni l'IP, ni cookie.
(function () {
  const el = document.getElementById('guichet'); if (!el) return;
  const en = document.documentElement.lang === 'en';
  const T = en ? {
    place: 'Your question to the Republic (280 characters at most)', bouton: 'Submit my question', attente: 'The Ambassador is consulting the files…',
    titre: 'Reply from the Ambassador', reste: (n) => n + ' characters left',
    ferme: 'The counter is closed for the moment.', quota: 'The counter is closed for today. Please come back tomorrow.',
    budget: 'The counter is closed until next month, for budgetary reasons the Ministry does not comment on.',
    vite: 'The Ambassador receives one delegation at a time. Please try again in a minute.', longueur: 'Between 3 and 280 characters, please.',
    panne: 'The counter is not answering. Please try again later.', bientot: 'The counter will open soon.'
  } : {
    place: 'Votre question à la République (280 caractères au plus)', bouton: 'Déposer ma question', attente: 'L’Ambassadeur consulte ses dossiers…',
    titre: 'Réponse de l’Ambassadeur', reste: (n) => n + ' caractères restants',
    ferme: 'Le guichet est momentanément fermé.', quota: 'Le guichet est fermé pour aujourd’hui. Revenez demain.',
    budget: 'Le guichet est fermé jusqu’au mois prochain, pour des raisons budgétaires que le Ministère ne commente pas.',
    vite: 'L’Ambassadeur reçoit une délégation à la fois. Réessayez dans une minute.', longueur: 'Entre 3 et 280 caractères, s’il vous plaît.',
    panne: 'Le guichet ne répond pas. Réessayez plus tard.', bientot: 'Le guichet ouvrira bientôt.'
  };
  const MSG = { ferme: T.ferme, quota: T.quota, budget: T.budget, 'trop-vite': T.vite, longueur: T.longueur };
  const p = (t, cls) => { const x = document.createElement('p'); x.textContent = t; if (cls) x.className = cls; return x; };

  const form = document.createElement('form');
  const zone = document.createElement('textarea');
  zone.maxLength = 280; zone.rows = 3; zone.placeholder = T.place; zone.setAttribute('aria-label', T.place);
  zone.style.cssText = 'width:100%;box-sizing:border-box;font:inherit;padding:8px;border:1px solid var(--rule);background:var(--sheet);color:var(--ink);resize:vertical';
  const bas = document.createElement('div'); bas.style.cssText = 'display:flex;gap:12px;align-items:center;justify-content:space-between;flex-wrap:wrap;margin-top:6px';
  const compte = p(T.reste(280), 'note'); compte.style.margin = '0';
  const bouton = document.createElement('button'); bouton.type = 'submit'; bouton.textContent = T.bouton;
  bouton.style.cssText = 'font:600 13px var(--f-data);background:var(--mask);color:var(--sheet);border:0;padding:8px 12px;cursor:pointer';
  bas.append(compte, bouton); form.append(zone, bas);
  const sortie = document.createElement('div'); sortie.setAttribute('aria-live', 'polite');
  zone.addEventListener('input', () => { compte.textContent = T.reste(280 - zone.value.length); });

  const montrer = (raison) => { sortie.textContent = ''; sortie.append(p(MSG[raison] || T.panne, 'note')); };
  form.addEventListener('submit', (ev) => {
    ev.preventDefault();
    const question = zone.value.trim();
    if (question.length < 3) return montrer('longueur');
    bouton.disabled = true; sortie.textContent = ''; sortie.append(p(T.attente, 'note'));
    fetch('/guichet/question', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question }) })
      .then((r) => r.json().catch(() => ({ ok: false })))
      .then((d) => {
        sortie.textContent = '';
        if (!d.ok) { montrer(d.raison); if (['quota', 'budget', 'ferme'].includes(d.raison)) form.hidden = true; return; }
        const bloc = document.createElement('div');
        bloc.style.cssText = 'border-left:3px solid var(--mask);padding:6px 12px;margin-top:10px';
        const b = document.createElement('b'); b.textContent = T.titre;
        bloc.append(b, p(d.reponse));
        sortie.append(bloc);
      })
      .catch(() => montrer(''))
      .finally(() => { bouton.disabled = false; });
  });

  fetch('/guichet/etat', { cache: 'no-store' })
    .then((r) => r.ok ? r.json() : Promise.reject(r.status))
    .then((e) => { el.textContent = ''; if (e.ouvert) el.append(form, sortie); else el.append(p(MSG[e.raison] || T.ferme, 'note')); })
    .catch(() => { el.textContent = ''; el.append(p(T.bientot, 'note')); });
})();
