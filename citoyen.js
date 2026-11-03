// Page « Mon citoyen » : on adopte l'un des 120 citoyens et on suit sa vie. Le choix reste dans le navigateur.
(function () {
  const { LANG, T, esc, get, latest, rn, wait, ageOf, MODE } = window.MCL;
  const $ = (s) => document.querySelector(s);
  const KEY = 'mcl-citoyen' + (MODE ? '-' + MODE : '');
  const L = LANG === 'en'
    ? { intro: 'Every citizen is in the registry. Adopt one: you cannot make them do anything, only watch their life unfold.', draw: 'Draw one at random', or: 'or choose', pick: 'Adopt', region: 'Region',
        sum: (n, r, d) => `You have followed ${n}, from the ${r} region, for ${d} day${d > 1 ? 's' : ''}.`, sat: 'Satisfaction', anger: 'Anger', fear: 'Fear', faith: 'Faith',
        believer: 'believer', agnostic: 'agnostic', atheist: 'atheist', today: 'Today', nothing: 'An ordinary day: work, and nothing to report.', life: 'Their life since you adopted them', day: (n) => `Day ${n}`,
        change: 'Adopt another citizen', gone: (n, e) => `${n}, your citizen of era ${e}, disappeared with their world when the Creator pressed the button. A new era has begun: you can adopt again.`,
        role: ['Citizen', 'Minister', 'President'], f: { pres: 'is president of the country', min: 'sits in the government', rebel: 'is in open revolt', cens: 'is censored: they are told things are going better than they are', voted: 'voted for the president in office',
        dRebel: 'took part in the revolt today', dCens: 'was censored today', dIn: 'joined the government', dOut: 'left the government', dElected: 'was elected president', dToppled: 'was thrown out of the palace', dCand: 'stood as a candidate' },
        down: 'The registry is temporarily unavailable.', no: 'No.',
        bio: 'Biography', bioSince: (d, a) => `Kept by the paper since ${d}${a ? ', starting from what the Archives knew' : ''}. Each step records the fact, the hour and the mood of the moment, never the reason.`, at: (j, h) => `Day ${j}${h == null ? '' : ', ' + String(h).padStart(2, '0') + ':00'}` }
    : { intro: 'Chaque citoyen est inscrit au registre. Adoptez-en un : vous ne pourrez rien lui faire faire, seulement regarder sa vie se dérouler.', draw: 'En tirer un au sort', or: 'ou choisir', pick: 'Adopter', region: 'Région',
        sum: (n, r, d) => `Vous suivez ${n}, de la région ${r}, depuis ${d} jour${d > 1 ? 's' : ''}.`, sat: 'Satisfaction', anger: 'Colère', fear: 'Peur', faith: 'Foi',
        believer: 'croyant', agnostic: 'agnostique', atheist: 'athée', today: 'Aujourd\'hui', nothing: 'Une journée ordinaire : du travail, et rien à signaler.', life: 'Sa vie depuis que vous l\'avez adopté', day: (n) => `Jour ${n}`,
        change: 'Adopter un autre citoyen', gone: (n, e) => `${n}, votre citoyen de l'ère ${e}, a disparu avec son monde quand le Créateur a appuyé sur le bouton. Une nouvelle ère a commencé : vous pouvez adopter à nouveau.`,
        role: ['Citoyen', 'Ministre', 'Président'], f: { pres: 'est président du pays', min: 'siège au gouvernement', rebel: 'est en révolte ouverte', cens: 'est censuré : on lui dit que tout va mieux qu\'en réalité', voted: 'a voté pour le président en place',
        dRebel: 's\'est joint à la révolte aujourd\'hui', dCens: 'a été censuré aujourd\'hui', dIn: 'est entré au gouvernement', dOut: 'a quitté le gouvernement', dElected: 'a été élu président', dToppled: 'a été chassé du palais', dCand: 's\'est porté candidat' },
        down: 'Le registre est momentanément indisponible.', no: 'nº',
        bio: 'Biographie', bioSince: (d, a) => `Tenue par le journal depuis le ${d}${a ? ', à partir de ce que savaient les Archives' : ''}. Chaque étape note le fait, l'heure et l'humeur du moment, jamais la raison.`, at: (j, h) => `Jour ${j}${h == null ? '' : ', ' + h + ' h'}` };
  const load = () => { try { return JSON.parse(localStorage.getItem(KEY)); } catch (_) { return null; } };
  const save = (v) => { try { v ? localStorage.setItem(KEY, JSON.stringify(v)) : localStorage.removeItem(KEY); } catch (_) {} };
  // Une ligne du registre : [numéro, prénom, région, satisfaction, colère, peur, foi, état, faits du jour]
  const obj = (c) => ({ id: c[0], nom: c[1], region: c[2], sat: c[3], col: c[4], peur: c[5], foi: c[6], flags: c[7], day: c[8], bio: c[9] || null });
  // Biographie (MAJ 1b-4) : étape = [jour, heure|null, type, fois, contexte, satisfaction|null, colère|null, peur|null, a].
  // Même mise en phrase que le portrait du dimanche (mcl_press.cpp, pressBioText).
  const EN = LANG === 'en';
  const ord = (n) => EN ? n + ([, 'st', 'nd', 'rd'][(n % 100 >= 11 && n % 100 <= 13) ? 0 : n % 10] || 'th') : n + 'e';
  function bioText(st, names) {
    const [, , kind, n, x, sat, col, peur, a] = st;
    const again = n > 1 ? (EN ? ` for the ${ord(n)} time` : ` pour la ${ord(n)} fois`) : '';
    const nm = (id) => names[id] || (EN ? 'No. ' : 'nº ') + id;
    let t = '';
    switch (kind) {
      case 1: t = EN ? `is born in the ${rn(a % 6)} region` : `naît dans la région ${rn(a % 6)}`; break;
      case 2: {
        const l = [];
        if (a & 1) l.push(EN ? 'former president' + (n > 1 ? ` (${n} times)` : '') : 'ancien président' + (n > 1 ? ` (${n} fois)` : ''));
        if (a & 2) l.push(EN ? 'toppled by a revolution' : 'renversé par une révolution');
        if (a & 4) l.push(EN ? 'betrayed by a minister' : 'trahi par un ministre');
        if (a & 8) l.push(EN ? 'leader of a palace coup' : 'auteur d\'un coup de palais');
        if (a & 32) l.push(EN ? 'voted out' : 'battu dans les urnes');
        if (a & 64) l.push(a & 16 ? (EN ? 'sacked minister' : 'ministre limogé') : (EN ? 'former minister' : 'ancien ministre'));
        else if (a & 16) l.push(EN ? 'sacked minister' : 'ministre limogé');
        t = (EN ? 'is already in the Archives: ' : 'figure déjà aux Archives : ') + l.join(', '); break;
      }
      case 3: t = (EN ? 'joins the rebellion' : 'rejoint la rébellion') + again; break;
      case 4: t = (EN ? 'leaves the rebellion' : 'quitte la rébellion') + again; break;
      case 5: t = (EN ? 'is silenced by the palace' : 'est réduit au silence par le palais') + again; break;
      case 6: t = (EN ? 'stands for president' : 'se porte candidat à la présidence') + again; break;
      case 7: { const p = a & 255, re = a & 256; t = EN ? (re ? 'is re-elected president' : 'is elected president') + (p ? ` with ${p}% of the vote` : '') : (re ? 'est réélu président' : 'est élu président') + (p ? ` avec ${p} % des voix` : ''); break; }
      case 8: t = a === 2 ? (EN ? 'is overthrown in a palace coup' : 'est renversé par un coup de palais') : (EN ? 'is toppled by a revolution' : 'est renversé par une révolution'); break;
      case 9: t = EN ? 'seizes the palace in a coup' : 'prend le palais par un coup d\'État'; break;
      case 10: t = EN ? 'loses the palace at the ballot box' : 'perd le palais dans les urnes'; break;
      case 11: t = a ? (EN ? `joins President ${nm(a)}'s government` : `entre au gouvernement du président ${nm(a)}`) : (EN ? 'joins the government' : 'entre au gouvernement'); break;
      case 12: t = a === 1 ? (EN ? 'is sacked from the government' : 'est limogé du gouvernement') : (EN ? 'leaves the government' : 'quitte le gouvernement'); break;
      case 13: t = (EN ? 'joins La Puce Libre (' : 'entre à La Puce Libre (') + (EN ? ['politics', 'economy', 'society', 'humour column'] : ['politique', 'économie', 'société', 'billet d\'humour'])[a % 4] + ')'; break;
      case 14: { const w = (a & 255) % 5; t = (EN ? 'leaves the paper' : 'quitte la rédaction') + ((EN ? ['', ' for the government', ' for the palace', ' for the rebellion', ''] : ['', ' pour le gouvernement', ' pour le palais', ' pour la rébellion', ''])[w]); break; }
      case 15: t = EN ? 'breaks the record for the longest reign' : 'bat le record du plus long règne'; break;
      default: return '';
    }
    if ([3, 4, 5, 6, 12, 9].includes(kind) && col != null) {
      if (col >= peur && col >= 40) t += EN ? ` (anger ${col}%)` : ` (colère ${col} %)`;
      else if (peur >= 40) t += EN ? ` (fear ${peur}%)` : ` (peur ${peur} %)`;
      else t += EN ? ` (satisfaction ${sat}%)` : ` (satisfaction ${sat} %)`;
    }
    const c = (x & 16) && kind !== 8 && kind !== 9 ? (EN ? ', amid the upheaval' : ', en pleine révolution')
      : (x & 4) && kind !== 5 ? (EN ? ', under censorship' : ', alors que la censure pèse sur le pays')
      : (x & 1) ? (EN ? ', during the storm' : ', pendant la tempête')
      : (x & 2) ? (EN ? ', during the epidemic' : ', pendant l\'épidémie')
      : (x & 32) ? (EN ? ', in hard times' : ', en pleine pénurie')
      : (x & 8) && kind !== 7 && kind !== 10 ? (EN ? ', on polling day' : ', un jour de scrutin') : '';
    return t + c;
  }
  function bioHtml(d, c) {
    if (!c.bio || !c.bio.length) return '';
    const names = {}; d.citoyens.forEach((r) => { names[r[0]] = r[1]; });
    const b = d.biographies || {};
    const since = b.depuis ? new Date(b.depuis + 'T12:00:00').toLocaleDateString(EN ? 'en-GB' : 'fr-FR', { day: 'numeric', month: 'long', year: 'numeric' }) : '';
    return `<section class="month bio"><h2>${L.bio}</h2><ol class="tl">${c.bio.slice().reverse().map((st) => `<li><time>${L.at(st[0], st[1])}</time><span>${esc(c.nom)} ${esc(bioText(st, names))}.</span></li>`).join('')}</ol>
      ${since ? `<p class="note">${esc(L.bioSince(since, b.amorce === 'archives'))}</p>` : ''}</section>`;
  }
  // Historique (data/historique.json, recalculé chaque soir depuis les fichiers bruts publiés) : ce qui précède la biographie.
  const H = EN
    ? { title: 'Their story, from the published data', none: 'Nothing notable in the published data: a working life.',
        note: (a, b, c) => `Rebuilt from the published raw data, ${a} to ${b}. Candidacies, revolt and censorship are recorded from ${c}.`,
        why: { normale: '', fondatrice: ' in the founding election', 'post-revolution': ' after the revolution', anticipee: ' in a snap election' } }
    : { title: 'Son histoire, d\'après les données publiées', none: 'Rien de notable dans les données publiées : une vie de travail.',
        note: (a, b, c) => `Reconstituée à partir des fichiers bruts publiés, du ${a} au ${b}. Candidatures, révolte et censure sont relevées depuis le ${c}.`,
        why: { normale: '', fondatrice: ' lors de l\'élection fondatrice', 'post-revolution': ' après la révolution', anticipee: ' lors d\'une élection anticipée' } };
  const dl = (iso, m) => iso ? new Date(iso + 'T12:00:00').toLocaleDateString(EN ? 'en-GB' : 'fr-FR', { day: 'numeric', month: m || 'long' }) : '';
  function histText(x, names, first) {
    const nm = (id) => names[id] || (EN ? 'No. ' : 'nº ') + id;
    // Une période qui commence au premier relevé des états a pu commencer avant : on l'écrit « au moins depuis ».
    const from = x.d === first ? (EN ? `at least ${dl(x.d)}` : `au moins le ${dl(x.d)}`) : (EN ? dl(x.d) : `le ${dl(x.d)}`);
    const span = x.fin === x.d ? (EN ? ` (${dl(x.d)})` : ` (le ${dl(x.d)})`) : x.fin ? (EN ? ` (from ${from} to ${dl(x.fin)})` : ` (depuis ${from}, jusqu'au ${dl(x.fin)})`) : (EN ? ` (since ${from})` : ` (depuis ${from})`);
    switch (x.t) {
      case 'elu': return (EN ? `is elected president with ${x.p}% of the vote` : `est élu président avec ${x.p} % des voix`) + (H.why[x.r] || '');
      case 'reelu': return EN ? `is re-elected president with ${x.p}% of the vote` : `est réélu président avec ${x.p} % des voix`;
      case 'battu': return EN ? `loses the palace at the ballot box, defeated by ${nm(x.par)}` : `perd le palais dans les urnes, battu par ${nm(x.par)}`;
      case 'renverse': return EN ? `is toppled by a revolution of ${x.n} rebel brains` : `est renversé par une révolution de ${x.n} cerveaux rebelles`;
      case 'coup': return EN ? `seizes the palace in a coup against President ${nm(x.contre)}` : `prend le palais par un coup d'État contre le président ${nm(x.contre)}`;
      case 'trahi': return EN ? `is overthrown in a palace coup by Minister ${nm(x.par)}` : `est renversé par un coup de palais du ministre ${nm(x.par)}`;
      case 'entre': return EN ? `joins President ${nm(x.pres)}'s government` : `entre au gouvernement du président ${nm(x.pres)}`;
      case 'quitte': return x.chute ? (EN ? 'leaves the government as it falls with its president' : 'quitte le gouvernement, tombé avec son président') : (EN ? 'leaves the government' : 'quitte le gouvernement');
      case 'limoge': return EN ? 'is sacked from the government' : 'est limogé du gouvernement';
      case 'candidat': return EN ? 'stands for president' : 'se porte candidat à la présidence';
      case 'injoignable': return EN ? 'goes silent: their region is unreachable' : 'ne répond plus : sa région est injoignable';
      case 'rebelle': return (EN ? 'is in revolt' : 'est en révolte') + span;
      case 'censure': return (EN ? 'is censored' : 'est censuré') + span;
      default: return '';
    }
  }
  function histHtml(d, c, hist) {
    if (!hist || hist.ere !== d.ere) return '';
    const names = {}; d.citoyens.forEach((r) => { names[r[0]] = r[1]; });
    const until = (d.biographies || {}).depuis || '9999';   // la biographie prend le relais à sa date de début
    const list = (hist.citoyens[c.id] || []).filter((x) => x.d < until && histText(x, names, hist.etatsDepuis));
    const when = (x) => dl(x.d, 'short') + (x.fin !== undefined || x.h == null ? '' : EN ? ', ' + String(x.h).padStart(2, '0') + ':00' : ', ' + x.h + ' h');
    return `<section class="month bio histcit"><h2>${H.title}</h2>${list.length
      ? `<ol class="tl">${list.slice().reverse().map((x) => `<li><time>${esc(when(x))}</time><span>${esc(c.nom)} ${esc(histText(x, names, hist.etatsDepuis))}.</span></li>`).join('')}</ol>`
      : `<p>${H.none}</p>`}
      <p class="note">${esc(H.note(dl(hist.du), dl(hist.au), dl(hist.etatsDepuis)))} <a href="${(window.MCL_BASE || '') + 'data/historique.json'}">historique.json</a></p></section>`;
  }
  const faith = (v) => v > 66 ? L.believer : v < 33 ? L.atheist : L.agnostic;
  const facts = (c) => {
    const o = [];
    if (c.day & 16) o.push(L.f.dElected); if (c.day & 32) o.push(L.f.dToppled); if (c.day & 4) o.push(L.f.dIn); if (c.day & 8) o.push(L.f.dOut); if (c.day & 64) o.push(L.f.dCand);
    if (c.flags & 16) o.push(L.f.pres); else if (c.flags & 8) o.push(L.f.min);
    if (c.flags & 1) o.push(L.f.rebel); else if (c.day & 1) o.push(L.f.dRebel);
    if (c.flags & 2) o.push(L.f.cens); else if (c.day & 2) o.push(L.f.dCens);
    if ((c.flags & 4) && !(c.flags & 16)) o.push(L.f.voted);
    return o;
  };
  const meter = (label, v, color) => `<div class="meter"><span>${label}</span><span class="t"><i style="width:${v}%;background:${color}"></i></span><b>${v} %</b></div>`;

  function adopt(d, gone) {
    const byReg = [0, 1, 2, 3, 4, 5].map((r) => d.citoyens.map(obj).filter((c) => c.region === r));
    $('#summary').textContent = L.intro;
    $('#citoyen').innerHTML = (gone ? `<p class="stale">${esc(gone)}</p>` : '') + `<div class="adopt"><button type="button" id="draw" class="btn">${L.draw}</button>
      <span class="note">${L.or}</span>
      <label class="sr" for="who">${L.pick}</label><select id="who">${byReg.map((list, r) => `<optgroup label="${esc(rn(r))}">${list.map((c) => `<option value="${c.id}">${esc(c.nom)}</option>`).join('')}</optgroup>`).join('')}</select>
      <button type="button" id="pick" class="btn ghost">${L.pick}</button></div>`;
    const go = (id) => { save({ ere: d.ere, id, depuis: d.jour, journal: [] }); show(d); };
    $('#draw').addEventListener('click', () => go(1 + Math.floor(Math.random() * d.citoyens.length)));
    $('#pick').addEventListener('click', () => go(+$('#who').value));
  }

  function show(d) {
    const st = load();
    const row = st && d.citoyens.find((c) => c[0] === st.id);
    if (!st || st.ere !== d.ere || !row) { const lost = st && st.ere !== d.ere && st.nom ? L.gone(st.nom, st.ere) : null; save(null); adopt(d, lost); return; }
    const c = obj(row), f = facts(c);
    st.nom = c.nom;
    if (!st.journal.length || st.journal[st.journal.length - 1].jour !== d.jour) st.journal.push({ jour: d.jour, sat: c.sat, col: c.col, faits: f });
    if (st.journal.length > 60) st.journal = st.journal.slice(-60);
    save(st);
    const role = c.flags & 16 ? 2 : c.flags & 8 ? 1 : 0;
    $('#summary').textContent = L.sum(c.nom, rn(c.region), Math.max(1, d.jour - st.depuis + 1));
    $('#citoyen').innerHTML = `<div class="card"><div class="k2">${L.role[role]} · ${esc(rn(c.region))} · ${L.no} ${c.id}</div><h2 class="who">${esc(c.nom)}</h2>
        ${meter(L.sat, c.sat, 'var(--up)')}${meter(L.anger, c.col, 'var(--down)')}${meter(L.fear, c.peur, 'var(--warn)')}
        <p class="note">${L.faith}${LANG === 'en' ? ': ' : ' : '}${faith(c.foi)} (${c.foi} %)</p>
        <h3>${L.today}</h3>${f.length ? `<ul>${f.map((x) => `<li>${esc(c.nom)} ${x}.</li>`).join('')}</ul>` : `<p>${L.nothing}</p>`}</div>
      ${bioHtml(d, c)}
      ${histHtml(d, c, d.hist)}
      <section class="month"><h2>${L.life}</h2><ol class="tl">${st.journal.slice().reverse().map((j) => `<li><time>${L.day(j.jour)}</time><span>${L.sat} ${j.sat} %, ${L.anger.toLowerCase()} ${j.col} %${j.faits.length ? ' — ' + j.faits.map(esc).join(', ') : ''}</span></li>`).join('')}</ol></section>
      <p><button type="button" id="change" class="btn ghost">${L.change}</button></p>`;
    $('#change').addEventListener('click', () => { save(null); adopt(d); });
  }

  latest().then((e) => {
    if (ageOf(e) < 3) { $('#summary').textContent = ''; wait($('#citoyen'), 3, e); return; }
    return Promise.all([get('data/citoyens.json'), get('data/historique.json').catch(() => null)]).then(([d, h]) => { d.hist = h; show(d); });
  }).catch(() => { $('#summary').textContent = L.down; });
})();
