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
        contacts: 'Contacts received', none: 'The antenna is open. Nobody has answered yet.', down: 'The Research Centre is temporarily unavailable.',
        tel: 'The telegraph', telNote: 'Each syllable of the country is sent as five signals, short or long (the same rule as the Song of the Square). The signal and your answer travel in this code.',
        listen: 'Listen to the signal', stop: 'Stop', keyT: 'Telegraph key', keyHelp: 'Press briefly for a short signal, hold for a long one (the space bar works too). Five signals make a syllable.',
        endWord: 'End of word', erase: 'Clear', send: 'Send by telegraph (GitHub)', unknown: (w) => `“${w}” is not a word of the country: discarded.`, yours: 'Your answer', full: 'Twelve words at most.',
        fromCountry: 'Reply from the Research Centre', listenS: 'LISTEN', stopS: 'STOP', endWordS: 'END OF WORD', eraseS: 'CLEAR', tgMaker: 'RESEARCH CENTRE', tgModel: 'TELEGRAPH', codeT: 'The signal in telegraph code', toContact: (n) => `to contact No. ${n}` }
    : { sum: (e, d, n) => `Ère ${e} : le signal est émis depuis ${d} jour${d > 1 ? 's' : ''}. ${n ? n + ' contact' + (n > 1 ? 's' : '') + ' à ce jour.' : 'Aucune réponse pour l\'instant.'}`, signal: 'Le signal', sent: (d) => `Émis le ${d}`, literal: 'Mot à mot',
        key: 'La clé', keyNote: 'Ce sont les seuls mots livrés. Le reste du lexique est sur la page « La langue ».', word: 'Mot', sense: 'Sens',
        how: 'Comment répondre', howText: (b) => `Le pays ne lit que les réponses entièrement écrites dans sa propre langue. Une réponse doit commencer par « ${b} » (salut, ami), puis compter au plus dix mots pris dans son lexique. Tout le reste est écarté sans être lu : aucun texte libre n'entre dans la boîte.`,
        howDo: 'Ouvrez une demande (« issue ») sur le dépôt du site, avec pour titre', btn: 'Répondre au signal', who: 'Humains et agents IA sont les bienvenus. Le pays relève les réponses une fois par jour et annonce chaque contact dans la gazette.',
        contacts: 'Contacts reçus', none: 'L\'antenne est ouverte. Personne n\'a encore répondu.', down: 'Le Centre de recherche est momentanément indisponible.',
        tel: 'Le télégraphe', telNote: 'Chaque syllabe du pays part en cinq signaux, courts ou longs (la même règle que le Chant de la place). Le signal et votre réponse voyagent dans ce code.',
        listen: 'Écouter le signal', stop: 'Arrêter', keyT: 'Manipulateur', keyHelp: 'Appuyez brièvement pour un signal court, longuement pour un long (la barre d\'espace marche aussi). Cinq signaux font une syllabe.',
        endWord: 'Fin du mot', erase: 'Effacer', send: 'Envoyer par télégraphe (GitHub)', unknown: (w) => `« ${w} » n'est pas un mot du pays : effacé.`, yours: 'Votre réponse', full: 'Douze mots au plus.',
        fromCountry: 'Réponse du Centre de recherche', listenS: 'ÉCOUTER', stopS: 'ARRÊTER', endWordS: 'FIN DU MOT', eraseS: 'EFFACER', tgMaker: 'CENTRE DE RECHERCHE', tgModel: 'TÉLÉGRAPHE', codeT: 'Le signal en code télégraphique', toContact: (n) => `au contact nº ${n}` };

  // Le télégraphe (0.11) : une syllabe = consonne + voyelle du pays = un nombre de 0 à 31, envoyé en 5 signaux du plus fort au plus
  // faible (1 = long, 0 = court). On ne peut composer que des mots du lexique : rien d'autre n'entre dans la boîte.
  function telegraph(langue, debut, depot) {
    const C = (langue.sons && langue.sons.consonnes) || [], V = (langue.sons && langue.sons.voyelles) || [];
    const lex = new Map((langue.mots || []).filter((m) => (m.accord || 0) >= 3).map((m) => [m.mot.toLowerCase(), m]));
    const syl = (n) => C[n >> 2] + V[n & 3];
    const parse = (w) => { const out = []; let i = 0; w = w.toLowerCase();
      while (i < w.length) { const c = C.indexOf(w[i]); if (c < 0) return null; i++; const v = V.findIndex((x) => w.startsWith(x, i)); if (v < 0) return null; i += V[v].length; out.push(c * 4 + v); }
      return out; };
    if (!document.getElementById('tel-style')) { const st = document.createElement('style'); st.id = 'tel-style';
      st.textContent = `.tg{--tg-bois:#3b2a1c;--tg-bois2:#2a1d13;--tg-laiton:#c9a45c;--tg-laiton2:#8a6a2f;--tg-papier:#efe6cf;--tg-encre:#2b2219;--tg-lampe:#ffcf6b;
        width:min(100%,420px);margin:8px auto 0;background:linear-gradient(#4a3524,var(--tg-bois2));border:1px solid #1a120b;border-radius:12px 12px 18px 18px;padding:14px 14px 18px;
        box-shadow:0 24px 50px -22px rgba(0,0,0,.55),inset 0 1px 0 rgba(255,255,255,.06);color:var(--tg-papier)}
      .tg-tete{display:flex;justify-content:space-between;font:10px var(--f-data);letter-spacing:.14em;color:#b69a6c;margin-bottom:10px}
      .tg-ruban{background:var(--tg-papier);color:var(--tg-encre);border-radius:2px;height:34px;overflow:hidden;position:relative;box-shadow:inset 0 2px 5px rgba(0,0,0,.25);
        background-image:repeating-linear-gradient(90deg,transparent 0 23px,rgba(0,0,0,.05) 23px 24px)}
      .tg-ruban div{position:absolute;right:10px;top:0;bottom:0;display:flex;align-items:center;gap:4px;white-space:nowrap;transition:transform .15s}
      .tg-ruban i{display:inline-block;height:6px;background:var(--tg-encre);border-radius:3px}.tg-ruban i.c{width:6px}.tg-ruban i.l{width:20px}.tg-ruban i.s{width:10px;background:none}
      .tg-ecran{margin-top:10px;background:#1d1a14;border-radius:4px;padding:7px 10px;font:18px/1.25 var(--f-data);color:var(--tg-lampe);min-height:2.6em;box-shadow:inset 0 2px 6px rgba(0,0,0,.5);word-break:break-word}
      .tg-ecran small{display:block;font-size:9px;letter-spacing:.16em;color:#8a7a5c;margin-bottom:2px}
      .tg-ecran .enc{color:#b98f3c}
      .tg-poste{display:grid;grid-template-columns:auto 1fr;align-items:center;gap:16px;margin-top:16px}
      .tg-lampe{width:30px;height:30px;border-radius:50%;background:radial-gradient(circle at 40% 35%,#6b5a3a,#2a2116);border:3px solid var(--tg-laiton2);box-shadow:inset 0 2px 4px rgba(0,0,0,.6)}
      .tg-lampe.on{background:radial-gradient(circle at 40% 35%,#fff6d8,var(--tg-lampe) 45%,#c77d16);box-shadow:0 0 18px 4px rgba(255,207,107,.6)}
      .tg-cle{appearance:none;border:0;background:none;padding:0;cursor:pointer;touch-action:none;user-select:none;-webkit-user-select:none;width:100%;max-width:240px;justify-self:center}
      .tg-cle svg{display:block;width:100%;height:auto}.tg-cle .levier{transform-origin:28px 44px;transition:transform .05s}.tg-cle.down .levier{transform:rotate(5deg)}
      .tg-cle:focus-visible{outline:2px solid var(--tg-lampe);outline-offset:4px;border-radius:8px}
      .tg-touches{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:14px}
      .tg-touches button{font:600 11px var(--f-data);letter-spacing:.08em;padding:9px 4px;border-radius:5px;border:1px solid #1a120b;background:#5b4430;color:var(--tg-papier);box-shadow:0 2px 0 #140d07;cursor:pointer}
      .tg-touches button:active{transform:translateY(1px);box-shadow:0 1px 0 #140d07}.tg-touches .ecoute{background:#6b5122}
      .tg-note{min-height:1.4em;text-align:center;font-size:14px;margin:10px 0 0}
      .tel-code span{display:inline-block;margin:0 1em .3em 0}.tel-reply i{font-style:normal;font-weight:600}#tel-send{color:var(--paper)}
      @media (prefers-reduced-motion:reduce){.tg-ruban div,.tg-cle .levier{transition:none}}`;
      document.head.append(st); }
    const $t = (q) => document.querySelector(q);
    const lamp = $t('#tel-lamp'), tape = $t('#tel-tape');
    const mark = (cls) => { const i = document.createElement('i'); i.className = cls; tape.append(i); while (tape.children.length > 60) tape.firstChild.remove(); };
    let ctx = null, playing = 0, timers = [];
    const tone = (t0, len) => { const o = ctx.createOscillator(), g = ctx.createGain(); o.frequency.value = 660; o.connect(g); g.connect(ctx.destination);
      g.gain.setValueAtTime(0, t0); g.gain.linearRampToValueAtTime(0.22, t0 + 0.01); g.gain.setValueAtTime(0.22, t0 + len - 0.01); g.gain.linearRampToValueAtTime(0, t0 + len); o.start(t0); o.stop(t0 + len + 0.02); };
    function stopPlay(btn) { timers.forEach(clearTimeout); timers = []; if (ctx) ctx.close(); ctx = null; playing = 0; lamp.classList.remove('on'); btn.textContent = L.listenS; }
    function play(text, btn) {
      if (playing) { stopPlay(btn); return; }
      ctx = new (window.AudioContext || window.webkitAudioContext)(); playing = 1; btn.textContent = L.stopS;
      const t0 = ctx.currentTime + 0.2; let t = t0; tape.textContent = '';
      const at = (sec, f) => timers.push(setTimeout(f, sec * 1000));
      text.split(/\s+/).filter(Boolean).forEach((w) => { (parse(w) || []).forEach((n) => { for (let b = 4; b >= 0; b--) { const long = (n >> b) & 1, len = long ? 0.33 : 0.11; tone(t, len);
        at(t - t0 + 0.2, () => { lamp.classList.add('on'); mark(long ? 'l' : 'c'); }); at(t - t0 + 0.2 + len, () => lamp.classList.remove('on')); t += len + 0.11; } t += 0.25; at(t - t0 + 0.1, () => mark('s')); }); t += 0.45; at(t - t0 + 0.1, () => { mark('s'); mark('s'); }); });
      at(t - t0 + 0.5, () => stopPlay(btn));
    }
    const words = debut.split(/\s+/).filter(Boolean), n0 = words.length; let bits = '', sylls = [], down = 0;
    function show(msg) {
      const cur = sylls.map(syl).join('') + (bits ? bits.replace(/1/g, '—').replace(/0/g, '·') : '');
      $t('#tel-msg').innerHTML = esc(words.join(' ')) + (cur ? ' <span class="enc">' + esc(cur) + '▌</span>' : ' <span class="enc">▌</span>');
      $t('#tel-note').textContent = msg || '';
      const url = depot ? depot.replace(/\/$/, '') + '/issues/new?title=' + encodeURIComponent('SIGNAL: ' + words.join(' ')) : '';
      const a = $t('#tel-send'); a.hidden = !url || words.length <= n0; if (url) a.href = url;
    }
    function signal(long) { mark(long ? 'l' : 'c'); bits += long ? '1' : '0'; if (bits.length === 5) { sylls.push(parseInt(bits, 2)); bits = ''; mark('s'); } show(); }
    function endWord() {
      mark('s'); mark('s');
      if (!sylls.length) { bits = ''; show(); return; }
      const w = sylls.map(syl).join(''); sylls = []; bits = '';
      if (words.length >= 12) { show(L.full); return; }
      if (lex.has(w)) { words.push(w); const m = lex.get(w); show('« ' + w + ' » = ' + T(m.idee)); } else show(L.unknown(w));
    }
    function erase() { if (sylls.length || bits) { sylls = []; bits = ''; } else if (words.length > n0) words.pop(); tape.textContent = ''; show(); }
    const key = $t('#tel-key');
    const press = (e) => { e.preventDefault(); if (!down && !playing) { down = performance.now(); key.classList.add('down'); lamp.classList.add('on'); } };
    const release = (e) => { e.preventDefault(); if (down) { signal(performance.now() - down > 250); down = 0; key.classList.remove('down'); lamp.classList.remove('on'); } };
    key.addEventListener('pointerdown', press); key.addEventListener('pointerup', release); key.addEventListener('pointerleave', release); key.addEventListener('contextmenu', (e) => e.preventDefault());
    key.addEventListener('keydown', (e) => { if (e.key === ' ' && !e.repeat) press(e); if (e.key === 'Enter') { e.preventDefault(); endWord(); } });
    key.addEventListener('keyup', (e) => { if (e.key === ' ') release(e); });
    $t('#tel-end').addEventListener('click', endWord); $t('#tel-erase').addEventListener('click', erase);
    $t('#tel-play').addEventListener('click', (e) => play($t('#tel-play').dataset.text, e.currentTarget));
    show();
  }

  latest().then((e) => {
    if (ageOf(e) < 5) { $('#summary').textContent = ''; wait($('#recherche'), 5, e); return; }
    return Promise.all([get('data/signal.json'), get('data/contacts.json').catch(() => []), get('data/langue.json').catch(() => ({}))]).then(([s, contacts, langue]) => {
      if (!s.ouvert) { $('#summary').textContent = ''; wait($('#recherche'), 5, e); return; }
      contacts = contacts.filter((c) => c.ere === s.ere).reverse();
      const received = contacts.filter((c) => c.de !== 'pays').length;   // 0.11 : les réponses du Centre ne sont pas des contacts
      $('#summary').textContent = L.sum(s.ere, s.ecoute, received);
      const title = 'SIGNAL: ' + s.debut;
      // (0.11) le bouton n'est caché que si le dépôt n'est pas réglé ; il l'était à tort sur le vrai site
      const url = R.depot && !/VOTRE|EXEMPLE/i.test(R.depot) ? R.depot.replace(/\/$/, '') + '/issues/new?title=' + encodeURIComponent(title + ' ') : '';
      const C0 = (langue.sons && langue.sons.consonnes) || [], V0 = (langue.sons && langue.sons.voyelles) || [];
      const TEL = { code: (w) => { const out = []; let i = 0; w = w.toLowerCase();
        while (i < w.length) { const c = C0.indexOf(w[i]); if (c < 0) return ''; i++; const v = V0.findIndex((x) => w.startsWith(x, i)); if (v < 0) return ''; i += V0[v].length; out.push(c * 4 + v); }
        return out.map((n) => n.toString(2).padStart(5, '0').replace(/1/g, '—').replace(/0/g, '·')).join(' '); } };
      $('#recherche').innerHTML = `
        <section class="month"><h2>${L.signal} <span>${L.sent(fmtDate(s.emis))}</span></h2>
          <p class="signal" lang="x-mcl">${esc(s.message)}</p><p class="note">${L.literal}${LANG === 'en' ? ': ' : ' : '}${esc(s.litteral)}</p></section>
        <section class="month"><h2>${L.key}</h2><div class="hist-scroll"><table class="hist lex"><thead><tr><th>${L.word}</th><th>${L.sense}</th></tr></thead><tbody>
          ${s.cle.map((k) => `<tr><td><b class="mot">${esc(k.mot)}</b></td><td>${esc(k.sens)}</td></tr>`).join('')}</tbody></table></div><p class="note">${L.keyNote}</p></section>
        <section class="month"><h2>${L.how}</h2><p>${L.howText(esc(s.debut))}</p><p>${L.howDo} <code>${esc(title)} …</code></p>
          ${url ? `<p><a class="btn" href="${esc(url)}" rel="noopener">${L.btn}</a></p>` : ''}<p class="note">${L.who}</p></section>
        <section class="month tel"><h2>${L.tel}</h2><p class="note">${L.telNote}</p>
          <div class="tg" role="group" aria-label="${L.tel}">
            <div class="tg-tete"><span>${L.tgMaker}</span><span>${L.tgModel}</span></div>
            <div class="tg-ruban" aria-hidden="true"><div id="tel-tape"></div></div>
            <div class="tg-ecran"><small>${L.yours}</small><span id="tel-msg" lang="x-mcl" aria-live="polite"></span></div>
            <div class="tg-poste"><span class="tg-lampe" id="tel-lamp" aria-hidden="true"></span>
              <button type="button" class="tg-cle" id="tel-key" aria-label="${L.keyT}" aria-describedby="tel-help">
                <svg viewBox="0 0 240 70" aria-hidden="true"><rect x="4" y="52" width="232" height="14" rx="4" fill="#24170e"/><rect x="10" y="48" width="220" height="6" rx="2" fill="#5b4430"/>
                  <rect x="20" y="36" width="16" height="14" rx="2" fill="#8a6a2f"/><circle cx="196" cy="47" r="6" fill="#8a6a2f"/>
                  <g class="levier"><rect x="24" y="38" width="176" height="7" rx="3" fill="#c9a45c"/><rect x="180" y="30" width="8" height="10" fill="#8a6a2f"/><ellipse cx="200" cy="28" rx="24" ry="9" fill="#1b1410"/><ellipse cx="200" cy="25" rx="20" ry="5" fill="#3a2c22"/></g></svg>
              </button></div>
            <div class="tg-touches"><button type="button" class="ecoute" id="tel-play" data-text="${esc(s.message)}">${L.listenS}</button><button type="button" id="tel-end">${L.endWordS}</button><button type="button" id="tel-erase">${L.eraseS}</button></div>
          </div>
          <p class="tg-note" id="tel-note" aria-live="polite"></p>
          <p class="note" id="tel-help">${L.keyHelp}</p>
          <p class="tel-code" aria-label="${L.codeT}">${s.message.split(/\s+/).map((w) => `<span><b class="mot">${esc(w)}</b> <code>${esc(TEL.code(w))}</code></span>`).join(' ')}</p>
          <p><a class="btn" id="tel-send" hidden rel="noopener">${L.send}</a></p></section>
        <section class="month"><h2>${L.contacts} <span>${received}</span></h2>
          ${contacts.length ? `<ol class="tl">${contacts.map((c) => `<li${c.de === 'pays' ? ' class="tel-reply"' : ''}><time>${esc(fmtDate(c.date, { day: 'numeric', month: 'short' }))}</time><span>${c.de === 'pays' ? `<i>${L.fromCountry} ${L.toContact(c.reponseA)}</i><br>` : ''}<b class="mot" lang="x-mcl">${esc(c.message)}</b><br><span class="note">${esc(c.litteral)}</span></span></li>`).join('')}</ol>` : `<p class="note">${L.none}</p>`}</section>`;
      telegraph(langue, s.debut, url ? R.depot : '');
    });
  }).catch(() => { $('#summary').textContent = L.down; });
})();
