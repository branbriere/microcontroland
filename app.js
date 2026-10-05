// La Puce Libre : affiche une édition à partir des fichiers JSON envoyés chaque soir par la passerelle.
// Les textes des éditions sont bilingues : { "fr": "…", "en": "…" }.
// data/latest.json      → l'édition du jour
// data/editions/N.json  → l'édition du jour N (lien #jour-N)
// data/archive.json     → la liste des éditions, la plus récente en premier
(function () {
  const $ = (s) => document.querySelector(s);
  const LANG = document.documentElement.lang === 'en' ? 'en' : 'fr';
  const BASE = window.MCL_BASE || '';
  const ESSAI = /[?&]essai\b/.test(location.search);        // ?essai : lit les éditions de la répétition générale
  const DATA = BASE + (ESSAI ? 'repetition/' : /[?&]demo\b/.test(location.search) ? 'demo/' : '');   // ?demo : pays d'exemple déjà évolué
  const T = (v) => (v && typeof v === 'object' && !Array.isArray(v)) ? (v[LANG] ?? v.fr ?? '') : (v ?? '');
  const esc = (s) => String(T(s)).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const cap = (s) => s ? s.charAt(0).toUpperCase() + s.slice(1) : '';
  const pct = (p) => {
    const v = Math.abs(p).toFixed(1);
    const sign = p > 0 ? '+' : p < 0 ? '−' : '';
    return LANG === 'en' ? `${sign}${v}%` : `${sign}${v.replace('.', ',')} %`;
  };
  const fmtDate = (iso, opts) => new Date(iso + 'T12:00:00').toLocaleDateString(LANG === 'en' ? 'en-GB' : 'fr-FR', opts || { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });

  const L = {
    fr: {
      issue: (n) => `Édition nº ${n}`, day: (n) => `Jour ${n}`, ofRep: 'de la République', era: (n) => `ère ${n}`, capital: 'Capitale', president: (n, nom) => n ? `Le président ${nom || 'nº ' + n}` : 'Le gouvernement provisoire',
      next: 'À suivre', agesT: 'Âges de la civilisation', breaking: 'Dernière minute',
      prono: 'Votre pronostic', pronoAsk: 'Qui va gagner ?', pronoSaid: (n) => `Vous avez misé sur ${n}. Résultat dans la prochaine édition.`,
      pronoWin: (n) => `Pronostic réussi : ${n} a gagné.`, pronoLose: (p, w) => `Pronostic manqué : vous aviez misé sur ${p}, c'est ${w} qui l'emporte.`, pronoVoid: 'Le scrutin que vous aviez pronostiqué n\'a pas eu lieu.',
      pronoScore: (ok, n) => `Votre score : ${ok} sur ${n}.`, outgoing: 'sortant',
      essai: 'Répétition générale : ces éditions sont des essais de la passerelle, pas la vraie gazette.',
      stale: (d) => `La passerelle n'a rien publié depuis ${d} jours. Le pays est peut-être en panne de courant ou d'Internet ; voici la dernière édition connue.`, vacant: 'en cours d\'élection',
      faith: 'Foi', faithLine: (f) => `${f.croyants} % croyants · ${f.agnostiques} % agnostiques · ${f.athees} % athées`,
      others: 'Autres nouvelles', dayTitle: 'La journée heure par heure', nothing: 'Aucun événement notable.',
      state: 'État du pays', pres: 'Président', since: 'Au pouvoir depuis', gov: 'Gouvernement', none: 'aucun',
      ministers: (n) => `${n} ministre${n > 1 ? 's' : ''}`, goal: 'Objectif atteint', res: 'Ressources',
      sat: 'Satisfaction', fear: 'Peur', anger: 'Colère', satN: (n) => `Satisfaction, ${n} dernières éditions.`,
      market: 'Cours du jour', closed: 'Bourse mondiale fermée aujourd\'hui.', commodity: 'Matière', region: 'Région', close: 'Clôture',
      real: 'Cours réels.', sim: 'Cours simulés.', regions: 'Les régions', mood: 'Humeur', rebels: 'Rebelles',
      system: 'État du système', internet: 'Internet', mkt: 'Bourse du jour', pub: 'Publication', regAnswer: (a, b) => `Régions : ${a}/${b} répondent`,
      checked: (h) => `Vérifié à ${h}.`, archives: 'Archives', allArch: 'Toutes les archives →', noArch: 'Pas encore d\'archives.',
      sub: 'S\'abonner', subNote: 'Colle cette adresse dans un lecteur RSS pour recevoir chaque édition.', copy: 'Copier', copied: 'Copié', selected: 'Sélectionné',
      notFound: 'Édition introuvable', noIssue: 'Cette édition n\'existe pas. <a href="./">Lire la dernière édition</a>.', first: 'La première édition sera publiée ce soir à 20 h.',
      feed: 'feed.xml', inh: 'hab'
    },
    en: {
      issue: (n) => `Issue No. ${n}`, day: (n) => `Day ${n}`, ofRep: 'of the Republic', era: (n) => `era ${n}`, capital: 'Capital', president: (n, nom) => n ? `President ${nom || 'No. ' + n}` : 'The caretaker government',
      next: 'Coming up', agesT: 'Ages of the civilisation', breaking: 'Breaking',
      prono: 'Your forecast', pronoAsk: 'Who will win?', pronoSaid: (n) => `You backed ${n}. Result in the next issue.`,
      pronoWin: (n) => `Good call: ${n} won.`, pronoLose: (p, w) => `Missed: you backed ${p}, ${w} won.`, pronoVoid: 'The vote you forecast did not take place.',
      pronoScore: (ok, n) => `Your score: ${ok} out of ${n}.`, outgoing: 'incumbent',
      essai: 'Dress rehearsal: these issues are gateway tests, not the real paper.',
      stale: (d) => `The gateway has published nothing for ${d} days. The country may have lost power or Internet; this is the last known issue.`, vacant: 'election under way',
      faith: 'Faith', faithLine: (f) => `${f.croyants}% believers · ${f.agnostiques}% agnostics · ${f.athees}% atheists`,
      others: 'Other news', dayTitle: 'The day, hour by hour', nothing: 'Nothing worth reporting.',
      state: 'State of the nation', pres: 'President', since: 'In power for', gov: 'Government', none: 'none',
      ministers: (n) => `${n} minister${n > 1 ? 's' : ''}`, goal: 'Target reached', res: 'Resources',
      sat: 'Satisfaction', fear: 'Fear', anger: 'Anger', satN: (n) => `Satisfaction, last ${n} issues.`,
      market: 'Today\'s markets', closed: 'World markets were closed today.', commodity: 'Commodity', region: 'Region', close: 'Close',
      real: 'Real prices.', sim: 'Simulated prices.', regions: 'The regions', mood: 'Mood', rebels: 'Rebels',
      system: 'System status', internet: 'Internet', mkt: 'Today\'s market data', pub: 'Publishing', regAnswer: (a, b) => `Regions: ${a}/${b} responding`,
      checked: (h) => `Checked at ${h}.`, archives: 'Archive', allArch: 'Full archive →', noArch: 'No archive yet.',
      sub: 'Subscribe', subNote: 'Paste this address into any RSS reader to get every issue.', copy: 'Copy', copied: 'Copied', selected: 'Selected',
      notFound: 'Issue not found', noIssue: 'This issue does not exist. <a href="./">Read the latest issue</a>.', first: 'The first issue will be published tonight at 8 pm.',
      feed: 'feed-en.xml', inh: 'inh.'
    }
  }[LANG];
  const REGION = { Mines: 'Mines', Champs: 'Fields', Raffineries: 'Refineries', Barrage: 'Dam', Port: 'Harbour', Ville: 'City' };
  const COMMO = { 'Cuivre': 'Copper', 'Blé': 'Wheat', 'Pétrole': 'Oil', 'Électricité': 'Electricity' };
  const rn = (r) => LANG === 'en' ? (REGION[r] || r) : r;
  const cn = (c) => LANG === 'en' ? (COMMO[c] || c) : c;
  const MOOD = {
    colere: [{ fr: 'Colère', en: 'Angry' }, 'var(--down)'], peur: [{ fr: 'Peur', en: 'Afraid' }, 'var(--warn)'],
    satisfaite: [{ fr: 'Satisfaite', en: 'Satisfied' }, 'var(--up)'], indifferente: [{ fr: 'Indifférente', en: 'Indifferent' }, 'var(--neutral)']
  };
  const PILL = { ok: ['OK', 'ok'], ferme: [{ fr: 'FERMÉE', en: 'CLOSED' }, 'wait'], attente: [{ fr: 'ATTENTE', en: 'PENDING' }, 'wait'], echec: [{ fr: 'ÉCHEC', en: 'FAILED' }, 'ko'] };
  let archive = [];

  async function getJSON(url) {
    const r = await fetch(DATA + url, { cache: 'no-store' });
    if (!r.ok) throw new Error(url + ' : ' + r.status);
    return r.json();
  }

  function pill(v) { const p = PILL[v] || PILL.attente; return `<span class="pill ${p[1]}">${esc(p[0])}</span>`; }

  function spark(vals) {
    if (!vals || vals.length < 2) return '';
    const pts = vals.map((v, i) => `${(i / (vals.length - 1) * 300).toFixed(1)},${(50 - v / 100 * 44).toFixed(1)}`).join(' ');
    const last = vals[vals.length - 1];
    return `<svg class="spark" viewBox="0 0 300 50" preserveAspectRatio="none" role="img" aria-label="${L.satN(vals.length)} ${last} %">
      <polyline fill="none" stroke="var(--rule)" stroke-width="1" points="0,28 300,28"/>
      <polyline fill="none" stroke="var(--mask)" stroke-width="2.5" points="${pts}"/>
      <circle cx="300" cy="${(50 - last / 100 * 44).toFixed(1)}" r="4" fill="var(--mask)"/></svg>
      <p class="note">${L.satN(vals.length)}</p>`;
  }

  function render(e, isLatest) {
    const s = e.etat, b = e.bourse, sys = e.systeme || {};
    document.title = `${T(e.title)} — La Puce Libre`;
    $('#edno').textContent = L.issue(e.day);
    $('#dateline').innerHTML = `${esc(cap(fmtDate(e.date)))} · <b>${L.day(e.jourEre || e.day)}</b> ${L.ofRep}${e.ere ? ', ' + L.era(e.ere) : ''}`;
    $('#capline').textContent = `${L.capital}${LANG === 'en' ? ': ' : ' : '}${s.capitale ? rn(s.capitale) : '—'} · ${T(s.population)}`;
    const regimeChanged = s.regimePrecedent && T(s.regimePrecedent) !== T(s.regime);
    const late = isLatest ? Math.floor((Date.now() - new Date(e.date + 'T20:00:00').getTime()) / 864e5) : 0;
    $('#edition').innerHTML = `${ESSAI ? `<p class="stale" role="status">${L.essai}</p>` : ''}${late >= 2 && !ESSAI ? `<p class="stale" role="status">${L.stale(late)}</p>` : ''}
    <div class="grid">
      <main>
        <article>
          <div class="kicker">${esc(e.kicker)}</div>
          <h1 class="lead">${esc(e.title)}</h1>
          <p class="chapo">${esc(e.chapo)}</p>
          <div class="body">${(e.body || []).map((p) => `<p>${esc(p)}</p>`).join('')}</div>
          <blockquote class="quote">${LANG === 'en' ? '“' + esc(e.quote) + '”' : '« ' + esc(e.quote) + ' »'}<cite>${esc(L.president(e.president, e.presidentNom))}</cite></blockquote>
        </article>
        ${nextBox(e, isLatest)}
        <section class="briefs" aria-label="${L.others}">
          ${(e.briefs || []).map((x) => `<div><span class="k2">${esc(x.rubrique)}</span><h3>${esc(x.titre)}</h3><p>${esc(x.texte)}</p></div>`).join('')}
        </section>
        <section class="section">
          <h2>${L.dayTitle}</h2>
          <ol class="tl">${(e.journee || []).length
            ? e.journee.map((t) => `<li><time>${String(t.heure).padStart(2, '0')} h</time><span>${esc(t.texte)}</span></li>`).join('')
            : `<li><time>–</time><span>${L.nothing}</span></li>`}</ol>
        </section>
      </main>
      <aside>
        <section class="box state">
          <h2>${L.state}</h2>
          <div class="regime">${regimeChanged ? `<s>${esc(s.regimePrecedent)}</s> →` : ''}<span class="now">${esc(s.regime)}</span></div>
          <dl>
            <dt>${L.pres}</dt><dd>${e.president ? `${e.presidentNom ? esc(e.presidentNom) + ', ' : ''}${LANG === 'en' ? 'No.' : 'nº'} ${e.president} (${esc(rn(s.capitale))})` : L.vacant}</dd>
            <dt>${L.since}</dt><dd>${esc(s.auPouvoirDepuis)}</dd>
            <dt>${L.gov}</dt><dd>${s.ministres ? L.ministers(s.ministres) : L.none}</dd>
            <dt>${L.goal}</dt><dd>${s.objectif} %</dd>
            <dt>${L.res}</dt><dd>${s.ressources} %</dd>
            ${s.foi ? `<dt>${L.faith}</dt><dd>${L.faithLine(s.foi)}</dd>` : ''}
          </dl>
          <div class="meter"><span>${L.sat}</span><span class="t"><i style="width:${s.satisfaction}%;background:var(--up)"></i></span><b>${s.satisfaction} %</b></div>
          <div class="meter"><span>${L.fear}</span><span class="t"><i style="width:${s.peur}%;background:var(--warn)"></i></span><b>${s.peur} %</b></div>
          <div class="meter"><span>${L.anger}</span><span class="t"><i style="width:${s.colere}%;background:var(--down)"></i></span><b>${s.colere} %</b></div>
          ${spark(e.satisfaction7j)}
        </section>
        ${e.ages && window.MCL ? `<section class="box"><h2>${L.agesT}</h2>${window.MCL.frise(e)}</section>` : ''}
        <section class="box">
          <h2>${L.market}</h2>
          ${b.fermee ? `<p class="note" style="margin:0">${L.closed}</p>` : `
          <table><thead><tr><th>${L.commodity}</th><th>${L.region}</th><th class="num">${L.close}</th></tr></thead><tbody>
          ${b.lignes.map((r) => `<tr><td>${esc(cn(r.matiere))}</td><td>${esc(rn(r.region))}</td><td class="num ${r.variation > 0 ? 'up' : r.variation < 0 ? 'down' : ''}">${pct(r.variation)}</td></tr>`).join('')}
          </tbody></table><p class="note">${b.coursReels ? L.real : L.sim}</p>`}
        </section>
        <section class="box">
          <h2>${L.regions}</h2>
          <table><thead><tr><th>${L.region}</th><th>${L.mood}</th><th class="num">${L.rebels}</th></tr></thead><tbody>
          ${e.regions.map((r) => { const m = MOOD[r.humeur] || MOOD.indifferente; return `<tr><td>${esc(rn(r.nom))}${r.nom === s.capitale ? ' ♛' : ''}</td><td><span class="dot" style="background:${m[1]}"></span>${esc(m[0])}</td><td class="num">${r.rebelles}/${r.cerveaux}</td></tr>`; }).join('')}
          </tbody></table>
        </section>
        <section class="box status">
          <h2>${L.system}</h2>
          <ul>
            <li>${pill(sys.internet)}<span>${L.internet}</span></li>
            <li>${pill(sys.bourse)}<span>${L.mkt}</span></li>
            <li>${pill(sys.journal)}<span>${L.pub}</span></li>
            <li>${pill(sys.regions === sys.regionsTotal ? 'ok' : 'echec')}<span>${L.regAnswer(sys.regions, sys.regionsTotal)}</span></li>
          </ul>
          <p class="note">${L.checked(esc(sys.verifieA || '20:00'))}</p>
        </section>
        <section class="box archive" id="archives">
          <h2>${L.archives}</h2>
          <ul id="archlist"></ul>
          <a class="more" href="archives.html">${L.allArch}</a>
        </section>
        <section class="box">
          <h2>${L.sub}</h2>
          <div class="rss"><code id="feedurl"></code><button id="copy" type="button">${L.copy}</button></div>
          <p class="note">${L.subNote}</p>
        </section>
      </aside>
    </div>`;
    $('#feedurl').textContent = new URL(BASE + L.feed, location.href).href.split('#')[0];
    $('#copy').addEventListener('click', copyFeed);
    document.querySelectorAll('[data-prono]').forEach((b) => b.addEventListener('click', () => { lsSet('mcl-prono', { ere: e.ere, edition: e.day, pick: +b.dataset.prono, nom: b.dataset.nom }); render(e, isLatest); }));
    if (isLatest) breaking(e);
    renderArchive(e.day);
  }

  // Petit stockage local (pronostics) : rien ne quitte le navigateur.
  const PKEY = (k) => k + (ESSAI ? '-essai' : /[?&]demo\b/.test(location.search) ? '-demo' : '');
  function lsGet(k) { try { return JSON.parse(localStorage.getItem(PKEY(k))); } catch (_) { return null; } }
  function lsSet(k, v) { try { v ? localStorage.setItem(PKEY(k), JSON.stringify(v)) : localStorage.removeItem(PKEY(k)); } catch (_) {} }

  // « À suivre » : ce qui se prépare, et le pronostic du lecteur quand une élection approche.
  function nextBox(e, isLatest) {
    const a = e.aSuivre;
    if (!a || !a.lignes) return '';
    let prono = '';
    if (isLatest) {
      let p = lsGet('mcl-prono'); const score = lsGet('mcl-prono-score') || { ok: 0, n: 0 };
      if (p && (p.ere !== e.ere || p.edition < e.day)) {   // un pronostic d'une édition passée : on le dépouille
        if (p.ere === e.ere && e.election) { const win = e.election.vainqueur === p.pick; score.n++; if (win) score.ok++; lsSet('mcl-prono-score', score); prono = `<p class="prono-res ${win ? 'ok' : 'ko'}">${win ? L.pronoWin(esc(p.nom)) : L.pronoLose(esc(p.nom), esc(e.election.nom))} ${L.pronoScore(score.ok, score.n)}</p>`; }
        else prono = `<p class="prono-res">${L.pronoVoid}</p>`;
        lsSet('mcl-prono', null); p = null;
      }
      if (a.election) {
        prono += p ? `<p class="prono-res">${L.pronoSaid(esc(p.nom))}</p>`
          : `<div class="prono"><b>${L.prono}</b> <span>${L.pronoAsk}</span><div class="chips">${a.election.candidats.map((c) => `<button type="button" data-prono="${c.id}" data-nom="${esc(c.nom)}">${esc(c.nom)} · ${esc(rn(c.region))}${c.sortant ? ' · ' + L.outgoing : ''}</button>`).join('')}</div></div>`;
      } else if (!prono && score.n) prono = `<p class="note">${L.pronoScore(score.ok, score.n)}</p>`;
    }
    if (!a.lignes.length && !prono) return '';
    return `<section class="next"><h2>${L.next}</h2><ul>${a.lignes.map((l) => `<li>${esc(l)}</li>`).join('')}</ul>${prono}</section>`;
  }

  // « Dernière minute » : une dépêche plus récente que l'édition affichée (coup de palais, révolte, contact…).
  function breaking(e) {
    getJSON('data/depeches.json').then((list) => {
      const d = list.find((x) => x.ere === e.ere && new Date(x.date + 'T' + String(x.heure).padStart(2, '0') + ':00:00') > new Date(e.date + 'T20:00:00'));
      if (!d || document.querySelector('.breaking')) return;
      const p = document.createElement('p');
      p.className = 'breaking'; p.setAttribute('role', 'status');
      p.innerHTML = `<b>${L.breaking} · ${String(d.heure).padStart(2, '0')} h</b> ${esc(d.texte)}`;
      $('#edition').prepend(p);
    }).catch(() => {});
  }

  function renderArchive(day) {
    const el = $('#archlist'); if (!el) return;
    el.innerHTML = archive.length
      ? archive.slice(0, 7).map((a) => `<li${a.day === day ? ' class="cur"' : ''}><a href="#jour-${a.day}"><time>${L.day(a.day)} · ${esc(fmtDate(a.date, { weekday: 'long', day: 'numeric', month: 'long' }))}</time>${esc(a.titre)}</a></li>`).join('')
      : `<li class="note">${L.noArch}</li>`;
  }

  function copyFeed() {
    const b = this, t = $('#feedurl').textContent;
    const sel = () => { const r = document.createRange(); r.selectNodeContents($('#feedurl')); const s = getSelection(); s.removeAllRanges(); s.addRange(r); b.textContent = L.selected; };
    try { navigator.clipboard.writeText(t).then(() => { b.textContent = L.copied; }, sel); } catch (_) { sel(); }
  }

  async function load() {
    const m = location.hash.match(/^#jour-(\d+)$/);
    try { archive = (await getJSON('data/archive.json')).sort((a, b) => b.day - a.day); } catch (_) { archive = []; }
    let e;
    try { e = await getJSON(m ? `data/editions/${m[1]}.json` : 'data/latest.json'); }
    catch (_) {
      $('#dateline').textContent = L.notFound;
      $('#edition').innerHTML = `<p class="empty">${m ? L.noIssue : L.first}</p>`;
      return;
    }
    render(e, !m);
    if (m) window.scrollTo({ top: 0 });
  }

  window.addEventListener('hashchange', () => { if (location.hash !== '#archives') load(); });
  load();
})();
