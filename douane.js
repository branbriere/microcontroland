// Douane numérique de l'Ambassade (16/11/2026) : refus de visa réels, lus dans /douane.json
// (Worker du relevé, version 1.4). Seulement jour × catégorie × nombre : ni chemin, ni robot, ni IP.
(function () {
  const el = document.getElementById('douane'); if (!el) return;
  const en = document.documentElement.lang === 'en';
  const NOMS = en
    ? { env: 'Undeclared luggage (.env)', cle: 'Embargoed items (keys)', terraform: 'Non-exportable documents (Terraform)', config: 'Restricted areas (configuration)', sonde: 'No such counter (admin tools)' }
    : { env: 'Bagages non déclarés (.env)', cle: 'Objets sous embargo (clés)', terraform: 'Documents non exportables (Terraform)', config: 'Zones protégées (configuration)', sonde: 'Guichets inexistants (outils d’administration)' };
  const nf = new Intl.NumberFormat(en ? 'en-GB' : 'fr-FR');
  const dt = (j) => new Date(j + 'T12:00:00Z').toLocaleDateString(en ? 'en-GB' : 'fr-FR', { day: 'numeric', month: 'long', timeZone: 'UTC' });
  const p = (t, cls) => { const x = document.createElement('p'); x.textContent = t; if (cls) x.className = cls; return x; };
  fetch('/douane.json', { cache: 'no-store' })
    .then((r) => r.ok ? r.json() : Promise.reject(r.status))
    .then((d) => {
      el.textContent = '';
      const tot = {}, parJour = {};
      let total = 0;
      for (const l of d.jours) { tot[l.categorie] = (tot[l.categorie] || 0) + l.n; parJour[l.jour] = (parJour[l.jour] || 0) + l.n; total += l.n; }
      const fort = document.createElement('p'); const b = document.createElement('b');
      b.textContent = nf.format(total) + (en ? (total === 1 ? ' visa refused' : ' visas refused') : (total > 1 ? ' refus de visa' : ' refus de visa'));
      fort.append(b, document.createTextNode(en ? ' since ' + dt(d.debut) + ' 2026.' : ' depuis le ' + dt(d.debut) + ' 2026.'));
      el.append(fort);
      const t = document.createElement('table');
      for (const c of d.categories) {
        const tr = t.insertRow(); tr.insertCell().textContent = NOMS[c] || c;
        const td = tr.insertCell(); td.textContent = nf.format(tot[c] || 0); td.style.textAlign = 'right';
      }
      el.append(t);
      const jours = Object.keys(parJour).sort().slice(-7);
      if (jours.length) el.append(p((en ? 'Last days: ' : 'Derniers jours : ') + jours.map((j) => dt(j) + (en ? ': ' : ' : ') + nf.format(parJour[j])).join(' · '), 'note'));
      el.append(p(en ? 'Counted by the site itself, every request included. The first day also includes our own commissioning tests. Updated every 5 minutes at most.'
                     : 'Compté par le site lui-même, toutes les demandes comprises. Le premier jour compte aussi nos essais de mise en service. Mis à jour toutes les 5 minutes au plus.', 'note'));
    })
    .catch(() => { el.textContent = ''; el.append(p(en ? 'The customs register is temporarily unreadable.' : 'Le registre de la douane est momentanément illisible.', 'note')); });
})();
