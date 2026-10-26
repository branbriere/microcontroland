// Bouton Français | English : les pages françaises sont à la racine, les pages anglaises dans en/ avec les mêmes noms de fichiers.
// Première visite avec un navigateur en anglais : envoi vers l'édition anglaise, avec un bandeau qui rappelle que le journal
// est écrit en français et propose d'y revenir. Les robots ne sont jamais redirigés (les balises hreflang leur suffisent).
(function () {
  const lang = document.documentElement.lang === 'en' ? 'en' : 'fr';
  const file = location.pathname.split('/').pop() || 'index.html';
  const target = (l) => (l === lang ? file : (lang === 'en' ? '../' + file : 'en/' + file)) + location.search + location.hash;  // garde ?essai et les autres paramètres
  const store = (k, v) => { try { v === undefined ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch (_) {} };
  let saved = null;
  try { saved = localStorage.getItem('mcl-lang'); } catch (_) {}
  const robot = navigator.webdriver || /bot|crawl|spider|slurp|preview|headless/i.test(navigator.userAgent || '');
  if (!saved && !robot && lang === 'fr' && /^en\b/i.test(navigator.language || '')) {
    try { sessionStorage.setItem('mcl-auto', '1'); } catch (_) {}
    location.replace(target('en')); return;
  }
  if (saved && saved !== lang) { location.replace(target(saved)); return; }
  const nav = document.querySelector('nav.main');
  if (!nav) return;
  const box = document.createElement('span');
  box.className = 'lang';
  box.setAttribute('role', 'group');
  box.setAttribute('aria-label', 'Langue / Language');
  box.innerHTML = [['fr', 'Français'], ['en', 'English']].map(([l, nom]) => `<a href="${target(l)}" lang="${l}" hreflang="${l}"${l === lang ? ' aria-current="true"' : ''}>${nom}</a>`).join('');
  box.addEventListener('click', (e) => {
    const a = e.target.closest('a'); if (!a) return;
    store('mcl-lang', a.lang);
  });
  nav.insertBefore(box, nav.firstChild);
  // Bandeau après un envoi automatique vers l'anglais ; fermé, il ne revient plus et l'anglais est retenu.
  let auto = false;
  try { auto = sessionStorage.getItem('mcl-auto') === '1'; } catch (_) {}
  if (lang !== 'en' || !auto || saved) return;
  const b = document.createElement('p');
  b.className = 'lang-note';
  b.innerHTML = 'La Puce Libre is written in Normandy, in French. You are reading its English edition, chosen from your browser\'s language. '
    + `<a href="${target('fr')}" lang="fr" hreflang="fr">Lire en français</a> <button type="button" aria-label="Close">×</button>`;
  b.querySelector('a').addEventListener('click', () => store('mcl-lang', 'fr'));
  b.querySelector('button').addEventListener('click', () => {
    store('mcl-lang', 'en');
    try { sessionStorage.removeItem('mcl-auto'); } catch (_) {}
    b.remove();
  });
  nav.after(b);
})();
