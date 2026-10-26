// Microcontrolchess — Salle de la Relique : jouer contre l'IA et rejouer une partie de la galerie.
// Tout se passe dans le navigateur : rien n'est envoyé, aucun compte, aucun cookie. Licence MIT.
(function () {
  'use strict';
  const E = window.MCC, $ = id => document.getElementById(id);
  if (!E || !$('board')) return;
  const BASE = document.currentScript ? document.currentScript.src.replace(/[^/]*$/, '') : 'relique/';
  const EN = document.documentElement.lang === 'en';
  const T = EN ? {
    names: { K: 'king', Q: 'queen', R: 'rook', B: 'bishop', N: 'knight', P: 'pawn' }, white: 'white', black: 'black', empty: 'empty',
    reasons: { 'mat': 'checkmate', 'percée': 'breakthrough', 'pat': 'stalemate', 'triple répétition': 'threefold repetition', 'absence de progrès': 'no progress' },
    draw: r => 'Draw (' + r + '). The Ministry takes note.', win: r => 'Victory (' + r + ')! The Ministry formally denies it.',
    loss: r => 'Defeat (' + r + '). The Relic remains unbeaten.', resigned: 'Resigned. The Relic remains unbeaten.',
    choose: 'Choose your side, then “Begin”.', thinking: 'Your opponent is thinking…', check: 'Check! ', turn: 'Your move.',
    restart: 'Start again', start: 'Begin', play: 'Play', pause: 'Pause', initial: 'Starting position.',
    move: (k, n, s) => 'Move ' + k + ' of ' + n + ': ' + s, demo: 'Exhibition game', end: 'White wins by breakthrough'
  } : {
    names: { K: 'roi', Q: 'dame', R: 'tour', B: 'fou', N: 'cavalier', P: 'pion' }, white: 'blanc', black: 'noir', empty: 'vide',
    reasons: {},
    draw: r => 'Nulle (' + r + '). Le Ministère prend note.', win: r => 'Victoire (' + r + ') ! Le Ministère dément formellement.',
    loss: r => 'Défaite (' + r + '). La Relique reste invaincue.', resigned: 'Abandon. La Relique reste invaincue.',
    choose: 'Choisissez votre camp, puis « Commencer ».', thinking: 'L’adversaire réfléchit…', check: 'Échec ! ', turn: 'À vous de jouer.',
    restart: 'Recommencer', start: 'Commencer', play: 'Lecture', pause: 'Pause', initial: 'Position initiale.',
    move: (k, n, s) => 'Coup ' + k + ' sur ' + n + ' : ' + s, demo: 'Partie de démonstration', end: 'Les blancs gagnent par percée'
  };
  const why = r => T.reasons[r] || r;
  const GLYPH = { K: '♚', Q: '♛', R: '♜', B: '♝', N: '♞', P: '♟' };

  function drawBoard(el, board, o) {
    o = o || {};
    const rows = [...Array(E.H).keys()]; if (o.flip) rows.reverse();
    const frag = document.createDocumentFragment();
    for (const r of rows) {
      const l = document.createElement('div'); l.className = 'lbl'; l.textContent = r + 1; frag.appendChild(l);
      for (let c = 0; c < E.W; c++) {
        const i = r * E.W + c, p = board[i], off = E.OFFENSIVE.includes(i);
        const b = document.createElement(o.onClick ? 'button' : 'div');
        b.className = 'sq' + ((r + c) % 2 ? ' dark' : '') + (off ? ' off' : '');
        if (o.onClick) b.type = 'button';
        if (o.last && (o.last.from === i || o.last.to === i)) b.classList.add('last');
        if (o.sel === i) b.classList.add('sel');
        const t = o.targets && o.targets.find(m => m.to === i);
        if (t) { b.classList.add('tgt'); if (t.capture) b.classList.add('cap'); }
        b.setAttribute('aria-label', E.sq(i) + ' ' + (p === '.' ? T.empty : T.names[E.typeOf(p)] + ' ' + (E.sideOf(p) === 1 ? T.white : T.black)));
        if (off) { const s = document.createElement('span'); s.className = 'star'; s.textContent = '✶'; s.setAttribute('aria-hidden', 'true'); b.appendChild(s); }
        if (p !== '.') { const s = document.createElement('span'); s.className = 'pc ' + (E.sideOf(p) === 1 ? 'up' : 'down'); s.textContent = GLYPH[E.typeOf(p)] + '︎'; b.appendChild(s); }
        if (o.onClick) b.addEventListener('click', () => o.onClick(i));
        frag.appendChild(b);
      }
    }
    frag.appendChild(document.createElement('div'));
    for (let c = 0; c < E.W; c++) { const l = document.createElement('div'); l.className = 'lbl'; l.textContent = 'abcde'[c]; frag.appendChild(l); }
    el.replaceChildren(frag);
  }

  // ---- Jouer ----
  const newWorker = () => { try { return new Worker(BASE + 'ia.js'); } catch (e) { return null; } };
  let worker = newWorker();
  let game = new E.Game(), human = 1, depth = 2, started = false, busy = false, sel = -1, last = null, played = [];
  function render() {
    const legal = started && !busy && game.side === human ? game.legal() : [];
    drawBoard($('board'), game.board, { flip: human === 1, last, sel, targets: sel >= 0 ? legal.filter(m => m.from === sel) : [], onClick: i => {
      if (!legal.length) return;
      const m = legal.find(x => x.from === sel && x.to === i);
      if (m) return doMove(m);
      sel = legal.some(x => x.from === i) ? i : -1; render();
    } });
    const st = $('status');
    if (game.result !== null) st.textContent = game.result === 0 ? T.draw(why(game.reason)) : (game.result === human ? T.win(why(game.reason)) : T.loss(why(game.reason)));
    else if (!started) st.textContent = game.moves.length ? T.resigned : T.choose;
    else if (busy) st.textContent = T.thinking;
    else st.textContent = (E.inCheck(game.board, game.side) ? T.check : '') + T.turn;
    const mv = $('moves'); mv.replaceChildren();
    for (let k = 0; k < game.moves.length; k += 2) {
      const a = document.createElement('span'); a.className = 'n'; a.textContent = (k / 2 + 1) + '.';
      const b = document.createElement('span'); b.textContent = game.moves[k];
      const c = document.createElement('span'); c.textContent = game.moves[k + 1] || '';
      mv.append(a, b, c);
    }
    mv.scrollTop = mv.scrollHeight;
    $('resign').disabled = !started; $('side').disabled = $('depth').disabled = started;
    $('new').textContent = started ? T.restart : T.start;
  }
  function aiMove() {
    busy = true; render();
    const seed = (Date.now() ^ Math.imul(played.length, 2654435761)) >>> 0;
    const done = r => { busy = false; doMove(r); };
    const local = () => setTimeout(() => { const r = E.bestMove(game, depth, E.mulberry32(seed)); done({ from: r.move.from, to: r.move.to }); }, 30);
    if (worker) {
      worker.onmessage = e => done(e.data);
      worker.onerror = ev => { ev.preventDefault(); worker = null; local(); };
      worker.postMessage({ moves: played, depth, seed });
    } else local();
  }
  function doMove(m) {
    game.play(m); played.push({ from: m.from, to: m.to }); last = m; sel = -1;
    if (game.result !== null) { started = false; return render(); }
    render(); if (game.side !== human) aiMove();
  }
  $('new').addEventListener('click', () => {
    human = +$('side').value; depth = +$('depth').value;
    game = new E.Game(); played = []; last = null; sel = -1; started = true; busy = false;
    if (worker) { worker.terminate(); worker = newWorker(); }
    render(); if (game.side !== human) aiMove();
  });
  $('resign').addEventListener('click', () => { started = false; busy = false; if (worker) { worker.terminate(); worker = newWorker(); } render(); });
  render();

  // ---- Galerie ----
  let R; try { R = JSON.parse($('galerie-donnees').textContent); } catch (e) { return; }
  const boards = [E.START]; { const g = new E.Game(); for (const [f, t] of R.mv) { g.play({ from: f, to: t }); boards.push(g.board); } }
  let k = 0, timer = null;
  function rshow() {
    drawBoard($('rboard'), boards[k], { last: k ? { from: R.mv[k - 1][0], to: R.mv[k - 1][1] } : null });
    $('rmove').textContent = k ? T.move(k, R.mv.length, R.notes[k - 1]) : T.initial;
    $('rstatus').textContent = k === R.mv.length ? T.end : T.demo;
    $('rprev').disabled = $('rfirst').disabled = k === 0; $('rnext').disabled = $('rlast').disabled = k === R.mv.length;
  }
  const stop = () => { clearInterval(timer); timer = null; $('rplay').textContent = T.play; };
  $('rfirst').onclick = () => { stop(); k = 0; rshow(); };
  $('rprev').onclick = () => { stop(); k = Math.max(0, k - 1); rshow(); };
  $('rnext').onclick = () => { stop(); k = Math.min(R.mv.length, k + 1); rshow(); };
  $('rlast').onclick = () => { stop(); k = R.mv.length; rshow(); };
  $('rplay').onclick = () => {
    if (timer) return stop();
    if (k === R.mv.length) k = 0;
    $('rplay').textContent = T.pause;
    timer = setInterval(() => { k++; rshow(); if (k >= R.mv.length) stop(); }, 1100);
  };
  rshow();
})();
