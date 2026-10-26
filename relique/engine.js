// Microcontrolchess — arbitre et IA, règles v1.1 (moteur 0.2, 25 oct. 2026). Licence MIT. https://www.microcontroland.org/relique.html
// Plateau 5 colonnes (a-e) × 6 rangées (1-6), rangée 1 en haut.
// Index = (rangée-1)*5 + colonne. Majuscules : camp « haut », jouent en premier, avancent vers la rangée 6.
(function (root) {
  'use strict';
  const W = 5, H = 6, N = W * H;
  const OFFENSIVE = [11, 18]; // b3, d4
  const START_V1 = 'RNKBQ' + 'PPPP.' + '.....' + '.....' + '.pppp' + 'qbknr';
  // Options de règles à l'essai (toutes désactivées = règles v1.0)
  // Règles v1.1 (25 oct. 2026) = v1.0 + percée seulement tout droit + pas de pion en diagonale au premier coup
  // + nulle après 80 demi-coups sans prise ni coup de pion. setRules({}) revient aux règles v1.0.
  const V11 = { straightBreak: true, noDiagFirst: true, noProgress: 80 };
  const RULES = Object.assign({ start: START_V1 }, V11);
  function setRules(o) { Object.assign(RULES, { start: START_V1, straightBreak: false, noDiagFirst: false, noProgress: 0 }, o || {}); }
  const VALUE = { P: 100, N: 300, B: 320, R: 480, Q: 900, K: 0 };

  const col = i => i % W, row = i => (i / W) | 0;
  const sq = i => 'abcde'[col(i)] + (row(i) + 1);
  const parseSq = s => (parseInt(s[1], 10) - 1) * W + 'abcde'.indexOf(s[0]);
  const isUpper = c => c >= 'A' && c <= 'Z';
  const sideOf = c => (c === '.' ? 0 : isUpper(c) ? 1 : -1); // 1 = haut (majuscules), -1 = bas
  const typeOf = c => c.toUpperCase();
  const step = (i, dc, dr) => {
    const c = col(i) + dc, r = row(i) + dr;
    return c < 0 || c >= W || r < 0 || r >= H ? -1 : r * W + c;
  };
  const KING_D = [[1,0],[-1,0],[0,1],[0,-1],[1,1],[1,-1],[-1,1],[-1,-1]];
  const KNIGHT_D = [[1,2],[2,1],[-1,2],[-2,1],[1,-2],[2,-1],[-1,-2],[-2,-1]];
  const ROOK_D = KING_D.slice(0, 4), BISHOP_D = KING_D.slice(4);
  const fwd = side => (side === 1 ? 1 : -1);
  const lastRow = side => (side === 1 ? H - 1 : 0);

  // Cases attaquées (capacité de capture) par une pièce en i.
  function attacksFrom(b, i, out) {
    const p = b[i], side = sideOf(p), t = typeOf(p);
    const add = j => { if (j >= 0) out.push(j); };
    if (t === 'K') KING_D.forEach(([dc, dr]) => add(step(i, dc, dr)));
    else if (t === 'N') KNIGHT_D.forEach(([dc, dr]) => add(step(i, dc, dr)));
    else if (t === 'P') { add(step(i, 1, fwd(side))); add(step(i, -1, fwd(side))); }
    else {
      const dirs = t === 'R' ? ROOK_D : t === 'B' ? BISHOP_D : KING_D;
      for (const [dc, dr] of dirs) {
        let j = step(i, dc, dr);
        while (j >= 0) { out.push(j); if (b[j] !== '.') break; j = step(j, dc, dr); }
      }
    }
    if (OFFENSIVE.includes(i)) KING_D.forEach(([dc, dr]) => add(step(i, dc, dr))); // règle 3.3
    return out;
  }

  // Recherche inverse depuis la case s (rapide) ; équivalente à attacksFrom sur toutes les pièces.
  function attacked(b, s, bySide) {
    const own = p => p !== '.' && sideOf(p) === bySide;
    for (const [dc, dr] of KING_D) {
      const j = step(s, dc, dr);
      if (j < 0 || !own(b[j])) continue;
      if (typeOf(b[j]) === 'K' || OFFENSIVE.includes(j)) return true;
    }
    for (const [dc, dr] of KNIGHT_D) { const j = step(s, dc, dr); if (j >= 0 && own(b[j]) && typeOf(b[j]) === 'N') return true; }
    // pion de bySide en j attaque j + (±1, fwd) ; donc il se trouve en s - (±1, fwd)
    for (const dc of [1, -1]) { const j = step(s, dc, -fwd(bySide)); if (j >= 0 && own(b[j]) && typeOf(b[j]) === 'P') return true; }
    for (const [dc, dr] of KING_D) {
      const diag = dc !== 0 && dr !== 0;
      let j = step(s, dc, dr);
      while (j >= 0) {
        if (b[j] !== '.') {
          if (own(b[j])) { const t = typeOf(b[j]); if (t === 'Q' || (diag ? t === 'B' : t === 'R')) return true; }
          break;
        }
        j = step(j, dc, dr);
      }
    }
    return false;
  }
  // Version de référence (lente), gardée pour les tests.
  function attackedRef(b, s, bySide) {
    const tmp = [];
    for (let i = 0; i < N; i++) {
      if (sideOf(b[i]) !== bySide) continue;
      tmp.length = 0;
      if (attacksFrom(b, i, tmp).includes(s)) return true;
    }
    return false;
  }

  const kingSq = (b, side) => b.indexOf(side === 1 ? 'K' : 'k');
  const inCheck = (b, side) => attacked(b, kingSq(b, side), -side);

  // Coups pseudo-légaux : {from, to, capture, special}
  function pseudoMoves(b, side) {
    const moves = [], seen = new Set();
    const push = (from, to, special) => {
      const k = from * 64 + to;
      if (seen.has(k)) return;
      seen.add(k);
      moves.push({ from, to, capture: b[to] !== '.', special: !!special });
    };
    const tmp = [];
    for (let i = 0; i < N; i++) {
      const p = b[i];
      if (sideOf(p) !== side) continue;
      const t = typeOf(p);
      if (t === 'P') {
        const f = fwd(side);
        const a = step(i, 0, f); if (a >= 0 && b[a] === '.') push(i, a);
        for (const dc of [1, -1]) {
          const d = step(i, dc, f);
          if (d < 0) continue;
          if (RULES.straightBreak && row(d) === lastRow(side)) continue;
          if (b[d] === '.' || (sideOf(b[d]) === -side && typeOf(b[d]) !== 'K')) push(i, d); // 3.2
        }
      } else {
        // déplacements normaux (sans la faculté offensive)
        tmp.length = 0;
        const off = OFFENSIVE.includes(i);
        const dests = normalTargets(b, i);
        for (const j of dests) {
          if (b[j] === '.' || (sideOf(b[j]) === -side && typeOf(b[j]) !== 'K')) push(i, j);
        }
      }
      if (OFFENSIVE.includes(i)) {
        for (const [dc, dr] of KING_D) {
          const j = step(i, dc, dr);
          if (j >= 0 && sideOf(b[j]) === -side && typeOf(b[j]) !== 'K') push(i, j, true); // capture seulement
        }
      }
    }
    return moves;
  }

  function normalTargets(b, i) {
    const p = b[i], t = typeOf(p), out = [];
    const add = j => { if (j >= 0) out.push(j); };
    if (t === 'K') KING_D.forEach(([dc, dr]) => add(step(i, dc, dr)));
    else if (t === 'N') KNIGHT_D.forEach(([dc, dr]) => add(step(i, dc, dr)));
    else {
      const dirs = t === 'R' ? ROOK_D : t === 'B' ? BISHOP_D : KING_D;
      for (const [dc, dr] of dirs) {
        let j = step(i, dc, dr);
        while (j >= 0) { out.push(j); if (b[j] !== '.') break; j = step(j, dc, dr); }
      }
    }
    return out;
  }

  const apply = (b, m) => {
    const a = b.split('');
    a[m.to] = a[m.from]; a[m.from] = '.';
    return a.join('');
  };

  function legalMoves(b, side) {
    return pseudoMoves(b, side).filter(m => !inCheck(apply(b, m), side));
  }

  // straightBreak : la percée n'est valable que par un pas tout droit (sinon, coup interdit vers la dernière rangée)
  const isBreakthrough = (b, m, side) => typeOf(b[m.from]) === 'P' && row(m.to) === lastRow(side) && (!RULES.straightBreak || col(m.to) === col(m.from));

  // Partie : état + historique, règles terminales 3.5 / 3.6
  class Game {
    constructor() { this.reset(); }
    reset() {
      this.board = RULES.start; this.side = 1; this.moves = []; this.result = null; this.reason = null;
      this.reps = new Map([[this.key(), 1]]);
      this.quiet = 0;
    }
    key() { return this.board + this.side; }
    legal() {
      if (this.result !== null) return [];
      let l = legalMoves(this.board, this.side);
      // noDiagFirst : le tout premier coup de la partie ne peut pas être un pas de pion en diagonale
      if (RULES.noDiagFirst && this.moves.length === 0) l = l.filter(m => !(typeOf(this.board[m.from]) === 'P' && col(m.to) !== col(m.from)));
      return l;
    }
    play(m) {
      const legal = this.legal().find(x => x.from === m.from && x.to === m.to);
      if (!legal) throw new Error('coup illégal ' + sq(m.from) + '-' + sq(m.to));
      const mover = this.side, before = this.board;
      const brk = isBreakthrough(before, legal, mover);
      this.quiet = legal.capture || typeOf(before[legal.from]) === 'P' ? 0 : this.quiet + 1;
      this.board = apply(before, legal);
      this.side = -mover;
      let note = notation(before, legal);
      if (brk) { this.result = mover; this.reason = 'percée'; note += '!'; }
      else {
        const k = this.key(); this.reps.set(k, (this.reps.get(k) || 0) + 1);
        const reply = legalMoves(this.board, this.side);
        const chk = inCheck(this.board, this.side);
        if (reply.length === 0) {
          if (chk) { this.result = mover; this.reason = 'mat'; note += '#'; }
          else { this.result = 0; this.reason = 'pat'; }
        } else if (this.reps.get(k) >= 3) { this.result = 0; this.reason = 'triple répétition'; if (chk) note += '+'; }
        else if (RULES.noProgress && this.quiet >= RULES.noProgress) { this.result = 0; this.reason = 'absence de progrès'; if (chk) note += '+'; }
        else if (chk) note += '+';
      }
      this.moves.push(note);
      return legal;
    }
  }

  function notation(b, m) {
    const t = typeOf(b[m.from]);
    return (t === 'P' ? '' : t) + sq(m.from) + (m.capture ? 'x' : '-') + sq(m.to) + (m.special && !normalCaptures(b, m) ? '*' : '');
  }
  // vrai si la capture était aussi possible sans la case offensive
  function normalCaptures(b, m) {
    const t = typeOf(b[m.from]);
    if (t === 'P') return Math.abs(col(m.to) - col(m.from)) === 1 && row(m.to) - row(m.from) === fwd(sideOf(b[m.from]));
    return normalTargets(b, m.from).includes(m.to);
  }

  // ---- IA : negamax alpha-bêta ----
  function evaluate(b, side) {
    // du point de vue de « side »
    let s = 0;
    for (let i = 0; i < N; i++) {
      const p = b[i]; if (p === '.') continue;
      const sd = sideOf(p), t = typeOf(p);
      let v = VALUE[t];
      if (t === 'P') { const adv = sd === 1 ? row(i) - 1 : (H - 2) - row(i); v += [0, 10, 30, 80][Math.max(0, Math.min(3, adv))]; }
      if (OFFENSIVE.includes(i) && t !== 'K') v += 25;
      s += sd === side ? v : -v;
    }
    return s;
  }

  const WIN = 100000;
  function search(b, side, depth, alpha, beta, ply, stats) {
    stats.nodes++;
    const moves = legalMoves(b, side);
    if (moves.length === 0) return inCheck(b, side) ? -WIN + ply : 0;
    if (depth === 0) return evaluate(b, side);
    order(b, moves);
    let best = -Infinity;
    for (const m of moves) {
      let v;
      if (isBreakthrough(b, m, side)) v = WIN - ply - 1;
      else v = -search(apply(b, m), -side, depth - 1, -beta, -alpha, ply + 1, stats);
      if (v > best) best = v;
      if (v > alpha) alpha = v;
      if (alpha >= beta) break;
    }
    return best;
  }
  function order(b, moves) {
    const score = m => (m.capture ? 10 * VALUE[typeOf(b[m.to])] - VALUE[typeOf(b[m.from])] / 10 : 0) + (typeOf(b[m.from]) === 'P' ? 5 : 0);
    moves.sort((x, y) => score(y) - score(x));
  }

  // rng : fonction () => [0,1) ; départage aléatoire entre coups ex aequo
  function bestMove(game, depth, rng) {
    const b = game.board, side = game.side, moves = game.legal();
    const stats = { nodes: 0 };
    let best = -Infinity, cands = [];
    for (const m of moves) {
      let v;
      if (isBreakthrough(b, m, side)) v = WIN;
      else {
        const nb = apply(b, m);
        // éviter de provoquer une triple répétition quand on est devant
        v = -search(nb, -side, depth - 1, -Infinity, Infinity, 1, stats);
        const rep = (game.reps.get(nb + (-side)) || 0) + 1;
        if (rep >= 3) v = 0;
      }
      if (v > best) { best = v; cands = [m]; } else if (v === best) cands.push(m);
    }
    const m = cands[Math.floor((rng || Math.random)() * cands.length)];
    return { move: m, score: best, nodes: stats.nodes };
  }

  function mulberry32(a) {
    return function () {
      a |= 0; a = a + 0x6D2B79F5 | 0;
      let t = Math.imul(a ^ a >>> 15, 1 | a);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }

  const api = { W, H, N, get START() { return RULES.start; }, START_V1, V11, RULES, setRules, OFFENSIVE, sq, parseSq, sideOf, typeOf, col, row, legalMoves, pseudoMoves, inCheck, attacked, attackedRef, apply, Game, bestMove, evaluate, mulberry32, isBreakthrough };
  if (typeof module !== 'undefined') module.exports = api; else root.MCC = api;
})(typeof window !== 'undefined' ? window : this);
