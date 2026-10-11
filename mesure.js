// Mesure d'audience anonyme (GoatCounter) : voir la page Mentions légales.
// Rien n'est compté si le navigateur demande « Ne pas suivre » (Do Not Track ou Global Privacy Control),
// ni pour les pages d'essai. Le script count.js est hébergé sur ce site ; seul le décompte part vers GoatCounter.
(function () {
  try {
    var n = navigator;
    if (n.doNotTrack === '1' || window.doNotTrack === '1' || n.msDoNotTrack === '1' || n.globalPrivacyControl === true) return;
    if (/[?&]essai\b/.test(location.search)) return;
    if (/(^localhost$|\.local$)/.test(location.hostname)) return;
    var me = document.currentScript, s = document.createElement('script');
    s.async = true;
    s.setAttribute('data-goatcounter', 'https://microcontroland.goatcounter.com/count');
    s.src = me ? me.src.replace(/mesure\.js(\?.*)?$/, 'count.js') : 'count.js';
    document.head.appendChild(s);
  } catch (e) {}
})();
