// Qui fait quoi : l'organigramme du pays, redessiné chaque soir à partir de la dernière édition (data/latest.json).
// Chaque étage s'allume seulement quand son système existe dans l'édition : rien n'est inventé, rien n'est annoncé en avance.
//  · gouvernement : président, capitale, ministres (fonction déléguée quand l'édition publie « fonction », firmware 0.12) ;
//  · religion : foi du pays (en service), grand prêtre quand l'édition publie un bloc « temple » ouvert (MAJ 3) ;
//  · bords politiques : quand l'édition publie « partis » (0.12 ; la Tranche avec la MAJ 3) ;
//  · contre-pouvoirs : presse (en service), ministres délégués (0.12), Temple (MAJ 3), juge (MAJ 7).
// Changements du soir : comparaison avec l'édition de la veille (data/editions/<jour-1>.json), si elle existe.
(function () {
  const M = window.MCL; if (!M) return;
  const en = M.LANG === 'en', esc = M.esc, $ = (id) => document.getElementById(id);
  const no = (id) => (en ? 'No. ' : 'nº ') + id;
  const nameOf = (m) => esc(m && (m.nom || no(m.id)));
  const pct = (n) => en ? `${n}%` : `${n} %`;
  const W = {
    soon: en ? 'coming' : 'à venir', live: en ? 'in service' : 'en service', fresh: en ? 'new tonight' : 'nouveau ce soir',
    left: en ? 'left the government tonight' : 'a quitté le gouvernement ce soir',
    pres: en ? 'President' : 'Président', vacant: en ? 'Vacant' : 'Vacant', vacantSub: en ? 'the palace is empty: an election is coming' : 'le palais est vide : une élection approche',
    keeps: en ? 'keeps: censorship, repression, postponing the election, choosing ministers' : 'garde : censure, répression, report de l\'élection, choix des ministres',
    since: en ? 'in power for ' : 'au pouvoir depuis ',
    min: en ? 'Minister' : 'Ministre', noPort: en ? 'without portfolio' : 'sans portefeuille',
    noPortWhy: en ? 'portfolios arrive with firmware 0.12' : 'les portefeuilles arrivent avec le firmware 0.12',
    free: en ? 'Empty seat' : 'Siège libre', freeSub: en ? '3 ministers at most' : '3 ministres au plus',
    alone: en ? 'The president governs alone.' : 'Le président gouverne seul.',
  };
  const FONCTION = {   // fonctions prévues (délégation, firmware 0.12) ; une fonction inconnue s'affiche telle que l'édition la donne
    octets: en ? 'Minister for Public Bytes' : 'Ministre des Octets publics',
    ponts: en ? 'Minister for Bridges' : 'Ministre des Ponts',
    chance: en ? 'Minister for Luck' : 'Ministre de la Chance',
    etat: en ? 'Minister of State' : 'Ministre d\'État',
  };
  const tag = (t, cls) => `<span class="o-tag${cls ? ' ' + cls : ''}">${t}</span>`;

  function gouvernement(e, prev) {
    const s = e.etat || {};
    const pm = prev && prev.etat ? (prev.etat.ministresNoms || []).map((m) => m.id) : null;
    const presNew = prev && prev.president !== e.president;
    const top = e.president
      ? `<div class="o-node o-top"><span class="o-role">${W.pres}</span><span class="o-name">${esc(e.presidentNom || no(e.president))}</span>` +
        `<span class="o-sub">${en ? 'region' : 'région'} ${esc(M.rn(s.capitale))} · ${W.since}${esc(s.auPouvoirDepuis)}</span>` +
        `<span class="o-port">${W.keeps}</span>${presNew ? `<span>${tag(W.fresh, 'new')}</span>` : ''}</div>`
      : `<div class="o-node o-top o-empty"><span class="o-role">${W.pres}</span><span class="o-name">${W.vacant}</span><span class="o-sub">${W.vacantSub}</span></div>`;
    const mins = s.ministresNoms || [];
    const cells = mins.map((m) => {
      const f = m.fonction ? (FONCTION[m.fonction] || esc(m.fonction)) : `${W.min} ${W.noPort}`;
      const dom = m.portefeuilles ? esc(m.portefeuilles) : W.noPortWhy;
      const isNew = pm && !pm.includes(m.id) && !presNew;
      return `<div class="o-node"><span class="o-role">${f}</span><span class="o-name">${nameOf(m)}</span>` +
        `<span class="o-sub">${en ? 'region' : 'région'} ${esc(M.rn(m.region))}</span><span class="o-port">${dom}</span>${isNew ? `<span>${tag(W.fresh, 'new')}</span>` : ''}</div>`;
    });
    if (e.president) while (cells.length < 3) cells.push(`<div class="o-node o-empty"><span class="o-role">${W.free}</span><span class="o-sub">${W.freeSub}</span></div>`);
    const gone = pm && !presNew ? (prev.etat.ministresNoms || []).filter((m) => !mins.some((x) => x.id === m.id)) : [];
    const goneLine = gone.length ? `<p class="o-note">${gone.map(nameOf).join(', ')} ${W.left}.</p>` : '';
    const aloneLine = e.president && !mins.length ? `<p class="o-note">${W.alone}</p>` : '';
    return top + (e.president ? `<div class="o-stem"></div><div class="o-row">${cells.join('')}</div>` : '') + goneLine + aloneLine;
  }

  function religion(e) {
    const f = e.etat && e.etat.foi, t = e.temple && e.temple.ouvert ? e.temple : null;
    if (!f) return `<div class="o-wait">${en ? 'Faith is not published yet.' : 'La foi n\'est pas encore publiée.'}</div>`;
    const foi = `<p class="o-foi"><b>${pct(f.croyants)}</b> ${en ? 'believers' : 'de croyants'} · <b>${pct(f.agnostiques)}</b> ${en ? 'agnostics' : 'd\'agnostiques'} · <b>${pct(f.athees)}</b> ${en ? 'atheists' : 'd\'athées'}</p>`;
    if (!t) return foi + `<div class="o-wait"><b>${en ? 'The Temple has not been consecrated yet.' : 'Le Temple n\'est pas encore consacré.'}</b> ` +
      (en ? 'The high priest, elected by believers alone, will appear here, with the reach of his laws (the whole country or believers only).'
          : 'Ici viendra le grand prêtre, élu par les seuls croyants, avec la portée de ses lois (tout le pays ou les seuls croyants).') +
      ` <a href="temple.html">${en ? 'The Temple' : 'Le Temple'}</a></div>`;
    const gp = t.grandPretre;
    const tous = f.croyants > f.agnostiques + f.athees;
    return foi + `<div class="o-tree"><div class="o-node o-top"><span class="o-role">${en ? 'High priest' : 'Grand prêtre'}</span>` +
      `<span class="o-name">${gp ? nameOf(gp) : (en ? 'not elected yet' : 'pas encore élu')}</span>` +
      `<span class="o-port">${tous ? (en ? 'laws for the whole country' : 'lois pour tout le pays') : (en ? 'laws for believers only' : 'lois pour les seuls croyants')}</span></div></div>`;
  }

  function bords(e) {
    const p = e.partis;
    const side = (k, nom, qui, quand) => {
      const x = p && p[k];
      return `<div class="o-node${x ? '' : ' o-empty'}"><span class="o-side">${nom}</span><span class="o-sub">${qui}</span>` +
        (x ? `<span class="o-name">${x.chef ? nameOf(x.chef) : '—'}</span>${x.membres != null ? `<span class="o-sub">${x.membres} ${en ? 'known members' : 'membres connus'}</span>` : ''}`
           : `<span>${tag(quand, 'soon')}</span>`) + '</div>';
    };
    return `<div class="o-row">` +
      side('face', en ? 'Heads' : 'Face', en ? 'the president\'s party' : 'le parti du président', '0.12') +
      side('tranche', en ? 'Edge' : 'Tranche', en ? 'the Temple' : 'le Temple', en ? 'update 3' : 'MAJ 3') +
      side('pile', en ? 'Tails' : 'Pile', en ? 'the opposition' : 'l\'opposition', '0.12') + '</div>' +
      (p ? '' : `<p class="o-note">${en ? 'The two faces and the edge of the byte coin. Parties do not exist yet.' : 'Les deux côtés et la tranche de la pièce d\'octet. Les partis n\'existent pas encore.'}</p>`);
  }

  function contre(e) {
    const c = e.censure && e.censure.active, red = (e.redaction || []).length;
    const delegue = ((e.etat && e.etat.ministresNoms) || []).some((m) => m.fonction);
    const t = e.temple && e.temple.ouvert;
    const cell = (role, nom, sub, on, quand) => `<div class="o-node${on ? '' : ' o-empty'}"><span class="o-role">${role}</span>` +
      (nom ? `<span class="o-name">${nom}</span>` : '') + `<span class="o-sub">${sub}</span><span>${on ? tag(W.live) : tag(quand, 'soon')}</span></div>`;
    return `<div class="o-row o-row4">` +
      cell(en ? 'Press' : 'Presse', 'La Puce Libre',
        c ? (en ? `under censorship tonight; ${e.binai ? 'Binaï publishes anyway' : 'the palace rereads the articles'}` : `sous censure ce soir ; ${e.binai ? 'Binaï publie quand même' : 'le palais relit les articles'}`)
          : (en ? `free tonight · ${red} journalists, all citizens` : `libre ce soir · ${red} journalistes, tous citoyens`), true) +
      cell(en ? 'Delegated ministers' : 'Ministres délégués', '', en ? 'decide differently from the president in their field' : 'décident autrement que le président dans leur domaine', delegue, '0.12') +
      cell(en ? 'Temple' : 'Temple', '', en ? 'the high priest and his laws' : 'le grand prêtre et ses lois', t, en ? 'update 3' : 'MAJ 3') +
      cell(en ? 'Judge' : 'Juge', '', en ? 'corruption, smuggling, disputes' : 'corruption, contrebande, litiges', false, en ? 'update 7' : 'MAJ 7') + '</div>';
  }

  M.latest().then((e) => {
    if (!e || !e.date) { $('o-gouv').innerHTML = `<div class="o-wait">${M.L.noData}</div>`; return; }
    $('o-date').textContent = (en ? 'Issue of ' : 'Édition du ') + M.fmtDate(e.date) + (en ? ' · day ' : ' · jour ') + (e.jourEre || e.day);
    const draw = (prev) => {
      $('o-gouv').innerHTML = gouvernement(e, prev);
      $('o-rel').innerHTML = religion(e);
      $('o-bords').innerHTML = bords(e);
      $('o-contre').innerHTML = contre(e);
    };
    draw(null);
    if (e.day > 1) M.get(`data/editions/${e.day - 1}.json`).then(draw).catch(() => {});
  }).catch(() => { $('o-gouv').innerHTML = `<div class="o-wait">${M.L.noData}</div>`; });
})();
