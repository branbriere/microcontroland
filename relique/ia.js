// Microcontrolchess — l'adversaire réfléchit ici, hors de la page (Web Worker). Licence MIT.
importScripts('engine.js');
self.onmessage = e => {
  const E = self.MCC, g = new E.Game();
  for (const m of e.data.moves) g.play(m);
  const r = E.bestMove(g, e.data.depth, E.mulberry32(e.data.seed));
  self.postMessage({ from: r.move.from, to: r.move.to });
};
