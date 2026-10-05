// Bouton FR | EN : les pages françaises sont à la racine, les pages anglaises dans en/ avec les mêmes noms de fichiers.
(function () {
  const lang = document.documentElement.lang === 'en' ? 'en' : 'fr';
  const file = location.pathname.split('/').pop() || 'index.html';
  const target = (l) => (l === lang ? file : (lang === 'en' ? '../' + file : 'en/' + file)) + location.hash;
  let saved = null;
  try { saved = localStorage.getItem('mcl-lang'); } catch (_) {}
  if (!saved && lang === 'fr' && /^en\b/i.test(navigator.language || '')) saved = 'en';
  if (saved && saved !== lang) { location.replace(target(saved)); return; }
  const nav = document.querySelector('nav.main');
  if (!nav) return;
  const box = document.createElement('span');
  box.className = 'lang';
  box.setAttribute('role', 'group');
  box.setAttribute('aria-label', 'Langue / Language');
  box.innerHTML = ['fr', 'en'].map((l) => `<a href="${target(l)}" lang="${l}" hreflang="${l}"${l === lang ? ' aria-current="true"' : ''}>${l.toUpperCase()}</a>`).join('');
  box.addEventListener('click', (e) => {
    const a = e.target.closest('a'); if (!a) return;
    try { localStorage.setItem('mcl-lang', a.lang); } catch (_) {}
  });
  nav.appendChild(box);
})();
