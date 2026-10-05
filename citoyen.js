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
        down: 'The registry is temporarily unavailable.', no: 'No.' }
    : { intro: 'Chaque citoyen est inscrit au registre. Adoptez-en un : vous ne pourrez rien lui faire faire, seulement regarder sa vie se dérouler.', draw: 'En tirer un au sort', or: 'ou choisir', pick: 'Adopter', region: 'Région',
        sum: (n, r, d) => `Vous suivez ${n}, de la région ${r}, depuis ${d} jour${d > 1 ? 's' : ''}.`, sat: 'Satisfaction', anger: 'Colère', fear: 'Peur', faith: 'Foi',
        believer: 'croyant', agnostic: 'agnostique', atheist: 'athée', today: 'Aujourd\'hui', nothing: 'Une journée ordinaire : du travail, et rien à signaler.', life: 'Sa vie depuis que vous l\'avez adopté', day: (n) => `Jour ${n}`,
        change: 'Adopter un autre citoyen', gone: (n, e) => `${n}, votre citoyen de l'ère ${e}, a disparu avec son monde quand le Créateur a appuyé sur le bouton. Une nouvelle ère a commencé : vous pouvez adopter à nouveau.`,
        role: ['Citoyen', 'Ministre', 'Président'], f: { pres: 'est président du pays', min: 'siège au gouvernement', rebel: 'est en révolte ouverte', cens: 'est censuré : on lui dit que tout va mieux qu\'en réalité', voted: 'a voté pour le président en place',
        dRebel: 's\'est joint à la révolte aujourd\'hui', dCens: 'a été censuré aujourd\'hui', dIn: 'est entré au gouvernement', dOut: 'a quitté le gouvernement', dElected: 'a été élu président', dToppled: 'a été chassé du palais', dCand: 's\'est porté candidat' },
        down: 'Le registre est momentanément indisponible.', no: 'nº' };
  const load = () => { try { return JSON.parse(localStorage.getItem(KEY)); } catch (_) { return null; } };
  const save = (v) => { try { v ? localStorage.setItem(KEY, JSON.stringify(v)) : localStorage.removeItem(KEY); } catch (_) {} };
  // Une ligne du registre : [numéro, prénom, région, satisfaction, colère, peur, foi, état, faits du jour]
  const obj = (c) => ({ id: c[0], nom: c[1], region: c[2], sat: c[3], col: c[4], peur: c[5], foi: c[6], flags: c[7], day: c[8] });
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
      <section class="month"><h2>${L.life}</h2><ol class="tl">${st.journal.slice().reverse().map((j) => `<li><time>${L.day(j.jour)}</time><span>${L.sat} ${j.sat} %, ${L.anger.toLowerCase()} ${j.col} %${j.faits.length ? ' — ' + j.faits.map(esc).join(', ') : ''}</span></li>`).join('')}</ol></section>
      <p><button type="button" id="change" class="btn ghost">${L.change}</button></p>`;
    $('#change').addEventListener('click', () => { save(null); adopt(d); });
  }

  latest().then((e) => {
    if (ageOf(e) < 3) { $('#summary').textContent = ''; wait($('#citoyen'), 3, e); return; }
    return get('data/citoyens.json').then(show);
  }).catch(() => { $('#summary').textContent = L.down; });
})();
