// Microcontrôland : visite 3D du Musée national. Version 1.1, 5 novembre 2026 (fenêtres sur le garage). Licence MIT.
// Le plan n'est dessiné nulle part : les salles, leur longueur et leur hauteur sont calculées à partir de musee.json,
// lui-même construit chaque soir par .github/musee.py à partir des seules données publiées.
// Three.js r128 est hébergé sur le site (vendor/three-r128, licence MIT) : aucun appel extérieur.
// Style validé par Bran le 26/10/2026 (« galerie claire » v3.1) : murs blancs mats, sol sombre mat, plafond à fentes,
// poutres dans la longueur, raies de soleil rasantes, lumière qui ne cache jamais les œuvres.
// Lumière (Bran, 2/11/2026) : cycle jour, soir et nuit selon l'heure de l'ordinateur du visiteur, ou au choix.
// Fenêtres (Bran, 2/11 et 5/11/2026) : la dernière salle a 4 fenêtres sur l'intérieur du garage (vraies photos, vérifiées et floutées) ;
// le visiteur est dans la boîte. Ce ne sont pas des œuvres et elles suivent la lumière du musée.
(function () {
  'use strict';
  const zone = document.getElementById('m-entrer');
  const bouton = document.getElementById('m-bouton');
  const boite = document.getElementById('musee3d');
  if (!zone || !bouton || !boite) return;
  const toileTest = document.createElement('canvas');
  if (!(toileTest.getContext('webgl') || toileTest.getContext('experimental-webgl'))) return;
  zone.hidden = false;

  const LG = document.documentElement.lang === 'en' ? 'en' : 'fr';
  const BASE = window.MCL_BASE || '';
  const REGION_EN = { Mines: 'Mines', Champs: 'Fields', Raffineries: 'Refineries', Barrage: 'Dam', Port: 'Harbour', Ville: 'City' };
  const REGIONS = ['Mines', 'Champs', 'Raffineries', 'Barrage', 'Port', 'Ville'];
  const T = {
    fr: {
      chargement: 'Ouverture des portes du musée…', quitter: 'Sortir', plan: 'Plan', hall: "Hall d'accueil",
      lumiere: { auto: 'Lumière : votre heure', jour: 'Lumière : jour', soir: 'Lumière : soir', nuit: 'Lumière : nuit' },
      aide: 'Glisser pour regarder · flèches ou ZQSD pour marcher · toucher une œuvre pour lire son cartel',
      bienvenue: 'Musée national de Microcontrôland', bienvenue_txt: 'Tout ce qui est exposé ici est calculé à partir des données publiées.',
      seul: 'Visiteur, vous êtes le seul à pouvoir parcourir toutes les ères. Les Waïnas ne voient jamais que la leur.',
      compte: (c, n) => `${c.ailes} aile(s) · ${c.salles} salle(s) · ${c.oeuvres} œuvre(s) · après l'édition n° ${n}`,
      aile: (n) => `Aile de l'ère ${n}`, attente: "En attente d'évolution de la civilisation.",
      fermee: (n) => `Cette aile ouvre quand l'ère ${n} atteint l'âge de la Mémoire.`, figee: (n) => `L'ère ${n} est terminée : cette aile est figée.`,
      chantier: 'En chantier', ouverte: 'Ouverte',
      statue: (n) => `Statue du réseau du président ${n}`,
      statue_txt: 'Les 81 poids du cerveau de citoyen du président en fonction : 9 entrées (en bas), 6 neurones cachés, 3 sorties (en haut). Vert = connexion positive, ambre = négative ; plus le trait est épais, plus la connexion est forte ; la taille d’une sphère suit son biais. Le cerveau qui gouverne (75 poids) n’est pas encore publié.',
      artiste_soir: 'Artiste du soir', soir_du: (d, n) => `Soir du ${d} · édition n° ${n}`, cit: (n, r) => `Citoyen n° ${n} (${r})`,
      cases: (c) => `${c} case(s) changée(s) depuis la veille`, source: 'Source', voir: 'Voir la page',
      vers: 'Vérifier', donnee: 'Donnée réelle publiée', fermer: 'Fermer', reclame: 'Réclame du musée',
      echelle: "Changer d'échelle", retour: 'Revenir au musée',
      etapes: ['Une boîte de 7 cartes, au fond d\u2019un garage.', '120 citoyens, 6 régions : un point par case de leurs dessins.', (n) => `${n.toLocaleString('fr-FR')} cases, ${n.toLocaleString('fr-FR')} points : une galaxie. Tout est une question d\u2019échelle.`],
      sculpteur_soir: 'Sculpteur du soir', deplaces: (c) => c == null ? 'Premier soir : aucune sculpture de la veille pour comparer' : `${c} cube(s) déplacé(s) depuis la veille`,
      table: (r) => `${r} : 20 sculptures`, table_txt: 'Une sculpture par citoyen, 127 cubes sur une grille de 8 × 8 × 8, calculée à partir des 81 poids de son cerveau (règle S1). Le socle doré est celui du sculpteur du soir.',
      abc: "L'abécédaire", abc_txt: (k, m) => `${k} glyphes communs (écrits pareil par au moins 5 régions sur 6), sur ${m} idées écrites.`,
      frise: 'La frise des soirs', frise_txt: 'Chaque soir depuis l\u2019ouverture de l\u2019écriture, le mot de la dernière heure, tel que la plupart des régions l\u2019ont écrit. De gauche à droite :',
      noms: 'Les noms en cartouche', noms_txt: 'Les prénoms ne sont dans aucun lexique, mais ils sont faits des mêmes sons : une hampe par syllabe, dans un cadre.',
      pres_de: (a, b) => `Président du ${a} au ${b}`, pres_dep: (a) => `Président depuis le ${a}`,
      histoire: 'Histoire de l\u2019écriture', hist: (d, k) => `${d} : ${k} glyphe(s) commun(s)`, ouverte_le: (d) => `L\u2019écriture s\u2019est ouverte le ${d}, à l\u2019âge de l\u2019État civil.`,
      regle_g: 'Règle G1, la hampe : colonne du milieu toujours pleine ; 1re syllabe à gauche, 2e à droite ; un bit à 1 trace un trait. Chaque région écrit son propre mot.',
      vrai_u: (d) => `Ce qui est vrai : chaque point est une case d\u2019un dessin de l\u2019atelier publié le ${d} (case pleine = étoile claire) ; la place de chaque citoyen dépend seulement de son numéro et de sa région, rien n\u2019est tiré au hasard.`,
    },
    en: {
      chargement: 'Opening the museum doors…', quitter: 'Leave', plan: 'Map', hall: 'Entrance hall',
      lumiere: { auto: 'Light: your time', jour: 'Light: day', soir: 'Light: evening', nuit: 'Light: night' },
      aide: 'Drag to look · arrow keys or WASD to walk · tap a work to read its caption',
      bienvenue: 'National Museum of Microcontrôland', bienvenue_txt: 'Everything shown here is computed from the published data.',
      seul: 'Visitor, you are the only one who can walk through every era. The Waïnas only ever see their own.',
      compte: (c, n) => `${c.ailes} wing(s) · ${c.salles} room(s) · ${c.oeuvres} work(s) · after issue no. ${n}`,
      aile: (n) => `Wing of era ${n}`, attente: 'Waiting for the civilisation to evolve.',
      fermee: (n) => `This wing opens when era ${n} reaches the Age of Memory.`, figee: (n) => `Era ${n} is over: this wing is frozen.`,
      chantier: 'Under construction', ouverte: 'Open',
      statue: (n) => `Statue of the network of President ${n}`,
      statue_txt: 'The 81 weights of the citizen brain of the president in office: 9 inputs (bottom), 6 hidden neurons, 3 outputs (top). Green = positive connection, amber = negative; the thicker the line, the stronger the connection; the size of a sphere follows its bias. The brain that governs (75 weights) is not published yet.',
      artiste_soir: 'Artist of the evening', soir_du: (d, n) => `Evening of ${d} · issue no. ${n}`, cit: (n, r) => `Citizen No. ${n} (${r})`,
      cases: (c) => `${c} square(s) changed since the day before`, source: 'Source', voir: 'See the page',
      vers: 'Check', donnee: 'Real published data', fermer: 'Close', reclame: 'Museum advertising',
      echelle: 'Change the scale', retour: 'Back to the museum',
      etapes: ['A box of 7 boards, at the back of a garage.', '120 citizens, 6 regions: one point per square of their drawings.', (n) => `${n.toLocaleString('en-GB')} squares, ${n.toLocaleString('en-GB')} points: a galaxy. It is all a matter of scale.`],
      sculpteur_soir: 'Sculptor of the evening', deplaces: (c) => c == null ? 'First evening: no sculpture from the day before to compare with' : `${c} cube(s) moved since the day before`,
      table: (r) => `${r}: 20 sculptures`, table_txt: 'One sculpture per citizen, 127 cubes on an 8 × 8 × 8 grid, computed from the 81 weights of its brain (rule S1). The gilded base belongs to the sculptor of the evening.',
      abc: 'The alphabet book', abc_txt: (k, m) => `${k} common glyphs (written the same way by at least 5 regions out of 6), out of ${m} ideas written.`,
      frise: 'The frieze of evenings', frise_txt: 'Every evening since writing opened, the word of the last hour, as most regions wrote it. Left to right:',
      noms: 'Names in cartouches', noms_txt: 'First names are in no lexicon, but they are made of the same sounds: one stem per syllable, inside a frame.',
      pres_de: (a, b) => `President from ${a} to ${b}`, pres_dep: (a) => `President since ${a}`,
      histoire: 'History of writing', hist: (d, k) => `${d}: ${k} common glyph(s)`, ouverte_le: (d) => `Writing opened on ${d}, at the Age of the Civil Registry.`,
      regle_g: 'Rule G1, the stem: the middle column is always filled; 1st syllable on the left, 2nd on the right; a bit set to 1 draws a stroke. Each region writes its own word.',
      vrai_u: (d) => `What is true: each point is a square of a studio drawing published on ${d} (filled square = bright star); each citizen's place depends only on their number and region, nothing is random.`,
    },
  }[LG];
  const MOIS = {
    fr: ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'],
    en: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
  }[LG];
  const dateLongue = (iso) => { const [a, m, j] = String(iso).split('-').map(Number); return LG === 'fr' ? `${j}${j === 1 ? 'er' : ''} ${MOIS[m - 1]} ${a}` : `${j} ${MOIS[m - 1]} ${a}`; };
  const region = (r) => (LG === 'en' ? REGION_EN[r] || r : r);
  const regionDe = (id) => region(REGIONS[Math.floor((id - 1) / 20)]);

  function charger(src) {
    return new Promise((ok, ko) => { const s = document.createElement('script'); s.src = src; s.onload = ok; s.onerror = ko; document.head.appendChild(s); });
  }

  let ouvert = false;
  bouton.addEventListener('click', async () => {
    if (ouvert) return;
    ouvert = true;
    boite.hidden = false;
    boite.innerHTML = `<div class="m3-charge">${T.chargement}</div>`;
    document.documentElement.style.overflow = 'hidden';
    try {
      if (!window.THREE) await charger(BASE + 'vendor/three-r128/three.min.js');
      const r = await fetch(BASE + 'musee.json', { cache: 'no-cache' });
      const M = await r.json();
      visite(M);
    } catch (err) {
      boite.innerHTML = `<div class="m3-charge">${String(err)}</div>`;
      setTimeout(fermer, 2500);
    }
  });

  function fermer() {
    if (window.MCL_MUSEE && window.MCL_MUSEE.arreter) window.MCL_MUSEE.arreter();
    boite.hidden = true; boite.innerHTML = ''; ouvert = false;
    document.documentElement.style.overflow = '';
    bouton.focus();
  }

  const CSS = `
#musee3d{color:#e7ece9;font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
#musee3d canvas{position:absolute;inset:0;width:100%;height:100%;touch-action:none;cursor:grab;display:block}
#musee3d .m3-charge{position:absolute;inset:0;display:grid;place-items:center;font-family:ui-monospace,Menlo,monospace;color:#a7b3ae}
#musee3d .m3-hud{position:absolute;z-index:2}
#musee3d .m3-carte{background:rgba(28,34,38,.9);border:1px solid #36424a;border-radius:10px;padding:9px 12px}
#musee3d .m3-haut{top:calc(env(safe-area-inset-top,0px) + 10px);left:max(16px,env(safe-area-inset-left,0px));right:max(16px,env(safe-area-inset-right,0px));display:flex;gap:8px;justify-content:space-between;align-items:flex-start;flex-wrap:wrap}
#musee3d .m3-salle{font-family:ui-monospace,Menlo,monospace;font-size:12px;color:#5fe08f;text-transform:uppercase;letter-spacing:.04em}
#musee3d .m3-aide{font-size:12px;color:#a7b3ae;margin-top:3px}
#musee3d .m3-outils{display:flex;gap:6px;flex-wrap:wrap}
#musee3d button{font:600 13px system-ui,sans-serif;color:#e7ece9;background:#1c2226;border:1px solid #36424a;border-radius:8px;padding:8px 11px;cursor:pointer}
#musee3d button:hover{border-color:#5fe08f}
#musee3d button:focus-visible{outline:2px solid #5fe08f;outline-offset:2px}
#musee3d .m3-pave{bottom:calc(env(safe-area-inset-bottom,0px) + 12px);left:max(16px,env(safe-area-inset-left,0px));display:grid;grid-template-columns:repeat(3,52px);grid-template-rows:repeat(2,52px);gap:6px}
#musee3d .m3-pave button{font-size:18px;padding:0;touch-action:none;user-select:none;-webkit-user-select:none}
#musee3d .m3-pave [data-k=av]{grid-column:2;grid-row:1}#musee3d .m3-pave [data-k=g]{grid-column:1;grid-row:2}#musee3d .m3-pave [data-k=ar]{grid-column:2;grid-row:2}#musee3d .m3-pave [data-k=d]{grid-column:3;grid-row:2}
@media (hover:hover) and (pointer:fine){#musee3d .m3-pave{display:none}}
#musee3d .m3-cartel{left:50%;transform:translateX(-50%);bottom:calc(env(safe-area-inset-bottom,0px) + 128px);width:min(560px,calc(100% - 32px));max-height:55vh;overflow:auto}
@media (hover:hover) and (pointer:fine){#musee3d .m3-cartel{bottom:20px}}
#musee3d .m3-cartel h2{font-size:18px;margin:0 0 6px;padding-right:60px}
#musee3d .m3-cartel p{margin:.35em 0}
#musee3d .m3-cartel .m3-src{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;color:#a7b3ae;word-break:break-all}
#musee3d .m3-cartel a{color:#5fe08f}
#musee3d .m3-etiq{display:inline-block;font-family:ui-monospace,Menlo,monospace;font-size:11px;text-transform:uppercase;letter-spacing:.06em;background:#5fe08f;color:#062012;padding:2px 7px;border-radius:4px;margin-bottom:6px}
#musee3d .m3-etiq.c{background:#ffd23f;color:#111}
#musee3d .m3-etiq.r{background:#f0b44c;color:#1a1300}
#musee3d .m3-ferme{position:absolute;top:8px;right:8px}
#musee3d .m3-plan{top:0;right:0;bottom:0;width:min(330px,100%);padding:calc(env(safe-area-inset-top,0px) + 14px) max(16px,env(safe-area-inset-right,0px)) 16px 16px;background:#1c2226;border-left:1px solid #36424a;overflow:auto}
#musee3d .m3-plan ol{list-style:none;margin:36px 0 0;padding:0;display:grid;gap:6px}
#musee3d .m3-plan ol button{width:100%;text-align:left}
#musee3d [hidden]{display:none!important}
#musee3d .m3-univers{left:50%;transform:translateX(-50%);bottom:calc(env(safe-area-inset-bottom,0px) + 24px);width:min(560px,calc(100% - 32px));text-align:center}
#musee3d .m3-univers p{margin:.3em 0}
#musee3d .m3-univers .m3-src{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;color:#a7b3ae}
@media (max-width:640px){#musee3d .m3-aide{display:none}}`;

  // ================================================================ la visite
  function visite(M) {
    const THREE = window.THREE;
    boite.innerHTML = `<style>${CSS}</style><canvas aria-label="${T.bienvenue}"></canvas>
<div class="m3-hud m3-haut"><div class="m3-carte"><div class="m3-salle" id="m3-salle">${T.hall}</div><div class="m3-aide">${T.aide}</div></div>
<div class="m3-outils"><button type="button" id="m3-lum"></button><button type="button" id="m3-plan">${T.plan}</button><button type="button" id="m3-sortir">${T.quitter}</button></div></div>
<div class="m3-hud m3-pave" aria-label="Déplacement"><button class="h" data-k="av" aria-label="↑">▲</button><button data-k="g" aria-label="↶">↶</button><button data-k="ar" aria-label="↓">▼</button><button data-k="d" aria-label="↷">↷</button></div>
<aside class="m3-hud m3-plan" id="m3-liste" hidden><button class="m3-ferme" id="m3-fplan">✕</button><ol></ol></aside>
<div class="m3-hud m3-carte m3-cartel" id="m3-cartel" hidden role="dialog" aria-live="polite"></div>
<div class="m3-hud m3-carte m3-univers" id="m3-univers" hidden aria-live="polite"><p id="m3-etape"></p><p class="m3-src" id="m3-vrai-u"></p><p><button type="button" id="m3-retour">${T.retour}</button></p></div>`;
    const $ = (s) => boite.querySelector(s);
    const canvas = $('canvas');
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(70, 1, 0.05, 160);
    const W = 8;                 // demi-largeur des salles (16 m)
    const PORTE = 1.6;           // demi-largeur des passages
    const H_PORTE = 3.1;
    const obstacles = [], cliquables = [], salles = [], lumieresNuit = [], raies = [], plafonds = [], vitres = [];
    const DALLE = new THREE.MeshBasicMaterial({ color: 0xd4d6d2 });

    // ---------------------------------------------------------------- matières (faites sur place, aucun fichier extérieur)
    function toile(w, h, f) { const c = document.createElement('canvas'); c.width = w; c.height = h; f(c.getContext('2d'), w, h); return c; }
    function grain(g, w, h, n, a, clair) { for (let i = 0; i < n; i++) { g.fillStyle = `rgba(${clair ? '255,255,255' : '0,0,0'},${Math.random() * a})`; g.fillRect(Math.random() * w, Math.random() * h, 2, 2); } }
    const texMur = new THREE.CanvasTexture(toile(256, 256, (g, w, h) => { g.fillStyle = '#e8e9e5'; g.fillRect(0, 0, w, h); grain(g, w, h, 2500, 0.03, false); grain(g, w, h, 2000, 0.12, true); }));
    texMur.wrapS = texMur.wrapT = THREE.RepeatWrapping; texMur.repeat.set(4, 2);
    const texSol = new THREE.CanvasTexture(toile(256, 256, (g, w, h) => { g.fillStyle = '#3a3c3d'; g.fillRect(0, 0, w, h); grain(g, w, h, 6000, 0.14, false); grain(g, w, h, 1500, 0.05, true); g.fillStyle = '#2e3132'; g.fillRect(0, 0, w, 2); g.fillRect(0, 0, 2, h); }));
    texSol.wrapS = texSol.wrapT = THREE.RepeatWrapping;
    const MUR = new THREE.MeshLambertMaterial({ map: texMur });
    const SOCLE = new THREE.MeshLambertMaterial({ color: 0xf1f2ee });
    const POUTRE = new THREE.MeshLambertMaterial({ color: 0xdfe0dc });
    const CADRE = new THREE.MeshLambertMaterial({ color: 0x2b2f33 });
    const PORTE_MAT = new THREE.MeshLambertMaterial({ color: 0x101417 });
    const FENTE = new THREE.MeshBasicMaterial({ color: 0xffffff });
    const rayee = new THREE.CanvasTexture(toile(64, 64, (g) => { g.fillStyle = '#111'; g.fillRect(0, 0, 64, 64); g.fillStyle = '#ffd23f'; for (let i = -64; i < 128; i += 32) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i + 16, 0); g.lineTo(i - 48, 64); g.lineTo(i - 64, 64); g.fill(); } }));
    rayee.wrapS = rayee.wrapT = THREE.RepeatWrapping;
    const RUBAN = new THREE.MeshBasicMaterial({ map: rayee });
    // Sculptures (1.2) : une seule couleur, socle doré pour le sculpteur du soir
    const BRONZE = new THREE.MeshLambertMaterial({ color: 0xb59f78 });
    const OR = new THREE.MeshLambertMaterial({ color: 0xc9a447 });
    const tournants = [];
    const lent = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    const unCube = new THREE.BoxGeometry(1, 1, 1);

    function boiteM(w, h, d, x, y, z, mat, bloque = true) {
      const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); m.position.set(x, y, z); scene.add(m);
      if (bloque) obstacles.push({ x1: x - w / 2, x2: x + w / 2, z1: z - d / 2, z2: z + d / 2 });
      return m;
    }
    function sol(x1, z1, x2, z2) {
      const t = texSol.clone(); t.needsUpdate = true; t.repeat.set((x2 - x1) / 1.5, (z1 - z2) / 1.5);
      const m = new THREE.Mesh(new THREE.PlaneGeometry(x2 - x1, z1 - z2), new THREE.MeshLambertMaterial({ map: t }));
      m.rotation.x = -Math.PI / 2; m.position.set((x1 + x2) / 2, 0, (z1 + z2) / 2); scene.add(m);
    }
    // Plafond : fentes de lumière diffuse et poutres dans le sens de la longueur (demande de Bran du 26/10/2026).
    function plafond(x1, z1, x2, z2, H) {
      const L = z1 - z2, cx = (x1 + x2) / 2, cz = (z1 + z2) / 2;
      const fond = new THREE.Mesh(new THREE.PlaneGeometry(x2 - x1, L), FENTE); fond.rotation.x = Math.PI / 2; fond.position.set(cx, H + 0.02, cz); scene.add(fond);
      const pas = (x2 - x1) / 6;
      for (let i = 0; i < 6; i++) {
        const b = new THREE.Mesh(new THREE.BoxGeometry(pas * 0.62, 0.08, L), DALLE); b.position.set(x1 + pas * (i + 0.5), H, cz); scene.add(b);
        const p = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.34, L), POUTRE); p.position.set(x1 + pas * i, H - 0.17, cz); scene.add(p);
      }
      plafonds.push(fond);
    }
    // Raies de soleil rasantes sur un mur (visibles le jour, rougies le soir, absentes la nuit)
    const texRais = new THREE.CanvasTexture(toile(1024, 256, (g, w, h) => {
      for (let x = -200; x < w + 200; x += 120) { const d = g.createLinearGradient(x, 0, x + 50, 0); d.addColorStop(0, 'rgba(255,248,230,0)'); d.addColorStop(0.5, 'rgba(255,248,230,.9)'); d.addColorStop(1, 'rgba(255,248,230,0)'); g.save(); g.transform(1, 0, -0.55, 1, 0, 0); g.fillStyle = d; g.fillRect(x, 0, 50, h); g.restore(); }
      const f = g.createLinearGradient(0, 0, 0, h); f.addColorStop(0, 'rgba(0,0,0,1)'); f.addColorStop(0.75, 'rgba(0,0,0,.55)'); f.addColorStop(1, 'rgba(0,0,0,0)'); g.globalCompositeOperation = 'destination-in'; g.fillStyle = f; g.fillRect(0, 0, w, h);
    }));
    function rais(z1, z2, H) {
      const m = new THREE.Mesh(new THREE.PlaneGeometry(z1 - z2, Math.min(3.6, H - 0.6)), new THREE.MeshBasicMaterial({ map: texRais, transparent: true, opacity: 0.3, blending: THREE.AdditiveBlending, depthWrite: false }));
      m.position.set(W - 0.115, H - 0.3 - Math.min(3.6, H - 0.6) / 2, (z1 + z2) / 2); m.rotation.y = -Math.PI / 2; scene.add(m); raies.push(m);
    }
    // Halo au mur au-dessus d'une œuvre : la nuit, une petite tache de lumière sur chaque œuvre (aucune vraie lampe : léger sur téléphone)
    const texHalo = new THREE.CanvasTexture(toile(128, 128, (g) => { const d = g.createRadialGradient(64, 64, 0, 64, 64, 64); d.addColorStop(0, 'rgba(255,240,210,.9)'); d.addColorStop(1, 'rgba(255,240,210,0)'); g.fillStyle = d; g.fillRect(0, 0, 128, 128); }));
    function halo(x, y, z, ry, l, h) {
      const m = new THREE.Mesh(new THREE.PlaneGeometry(l, h), new THREE.MeshBasicMaterial({ map: texHalo, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false }));
      m.position.set(x, y, z); m.rotation.y = ry; m.translateZ(0.012); scene.add(m); lumieresNuit.push(m);
    }

    // Mur latéral plein, d'une salle (z1 > z2)
    function murs(z1, z2, H, trous = []) {
      for (const s of [-1, 1]) {
        let segs = [[z1, z2]];
        for (const t of trous.filter((t) => t.cote === s)) segs = segs.flatMap(([a, b]) => (t.z1 < a && t.z2 > b ? [[a, t.z1], [t.z2, b]] : [[a, b]]));
        for (const [a, b] of segs) if (a - b > 0.01) boiteM(0.2, H, a - b, s * W, H / 2, (a + b) / 2, MUR);
        for (const t of trous.filter((t) => t.cote === s)) boiteM(0.2, H - H_PORTE, t.z1 - t.z2, s * W, H_PORTE + (H - H_PORTE) / 2, (t.z1 + t.z2) / 2, MUR, false);
      }
    }
    // Cloison transversale avec passage au centre (ouvert ou fermé)
    function cloison(z, H, ferme = false) {
      boiteM(W - PORTE, H, 0.2, -(W + PORTE) / 2, H / 2, z, MUR);
      boiteM(W - PORTE, H, 0.2, (W + PORTE) / 2, H / 2, z, MUR);
      boiteM(PORTE * 2, H - H_PORTE, 0.2, 0, H_PORTE + (H - H_PORTE) / 2, z, MUR, false);
      if (ferme) {
        const p = boiteM(PORTE * 2, H_PORTE, 0.1, 0, H_PORTE / 2, z - 0.05, PORTE_MAT);
        return p;
      }
      return null;
    }
    function ruban(x1, z1, x2, z2) {
      const L = Math.hypot(x2 - x1, z2 - z1);
      for (const y of [0.55, 1.05]) { const m = new THREE.Mesh(new THREE.BoxGeometry(L, 0.12, 0.03), RUBAN); m.position.set((x1 + x2) / 2, y, (z1 + z2) / 2); m.rotation.y = -Math.atan2(z2 - z1, x2 - x1); scene.add(m); }
      obstacles.push({ x1: Math.min(x1, x2) - 0.1, x2: Math.max(x1, x2) + 0.1, z1: Math.min(z1, z2) - 0.1, z2: Math.max(z1, z2) + 0.1 });
    }

    // ---------------------------------------------------------------- textes et images dessinés sur toile
    function ecrire(g, txt, x, y, max, lh) {
      let li = '';
      for (const m of String(txt).split(' ')) { const e = li ? li + ' ' + m : m; if (g.measureText(e).width > max && li) { g.fillText(li, x, y); y += lh; li = m; } else li = e; }
      if (li) { g.fillText(li, x, y); y += lh; }
      return y;
    }
    function texte({ titre, lignes = [], etiq, fond = '#f7f8f5', encre = '#1b2124', accent = '#1f7a46', taille = 34 }, l, h) {
      const Wc = 1024, Hc = Math.round(Wc * h / l);
      return toile(Wc, Hc, (g) => {
        g.fillStyle = fond; g.fillRect(0, 0, Wc, Hc); let y = 64;
        if (etiq) { g.font = '600 26px ui-monospace, Menlo, monospace'; const lw = g.measureText(etiq.t).width + 28; g.fillStyle = etiq.c; g.fillRect(56, y - 34, lw, 44); g.fillStyle = '#111'; g.fillText(etiq.t, 70, y - 4); y += 56; }
        g.fillStyle = encre; g.font = `700 ${Math.round(taille * 1.6)}px Georgia, "Times New Roman", serif`;
        y = ecrire(g, titre, 56, y + 18, Wc - 112, taille * 1.8) + 14;
        g.fillStyle = accent; g.fillRect(56, y - 6, 90, 6); y += 34;
        g.font = `400 ${taille}px system-ui, sans-serif`; g.fillStyle = encre;
        for (const t of lignes) { if (y > Hc - 20) break; y = ecrire(g, t, 56, y, Wc - 112, taille * 1.35) + 8; }
      });
    }
    function plaque(contenu, l, h, x, y, z, ry, cartel) {
      const tex = new THREE.CanvasTexture(texte(contenu, l, h));
      const m = new THREE.Mesh(new THREE.PlaneGeometry(l, h), new THREE.MeshBasicMaterial({ map: tex, color: 0xf2f2f2 }));
      m.position.set(x, y, z); m.rotation.y = ry; m.translateZ(0.14); scene.add(m);
      if (cartel) { m.userData.cartel = cartel; cliquables.push(m); }
      return m;
    }
    // Un cadre au mur : bordure sombre, passe-partout clair, image dessinée sur toile
    function cadre(dessiner, l, h, x, y, z, ry, cartel, dore = false) {
      const grp = new THREE.Group(); grp.position.set(x, y, z); grp.rotation.y = ry; scene.add(grp);
      const b = new THREE.Mesh(new THREE.BoxGeometry(l + 0.16, h + 0.16, 0.06), dore ? new THREE.MeshLambertMaterial({ color: 0xc9a447 }) : CADRE); b.position.z = 0.13; grp.add(b);
      const c = document.createElement('canvas'); c.width = Math.round(512 * l / Math.max(l, h)); c.height = Math.round(512 * h / Math.max(l, h));
      const tex = new THREE.CanvasTexture(c);
      const im = new THREE.Mesh(new THREE.PlaneGeometry(l, h), new THREE.MeshBasicMaterial({ map: tex, color: 0xf2f2f2 })); im.position.z = 0.165; grp.add(im);
      Promise.resolve(dessiner(c.getContext('2d'), c.width, c.height)).then(() => { tex.needsUpdate = true; });
      if (cartel) { im.userData.cartel = cartel; b.userData.cartel = cartel; cliquables.push(im, b); }
      return grp;
    }
    function svgVersToile(svg) {
      return (g, w, h) => new Promise((ok) => {
        const im = new Image();
        im.onload = () => { g.fillStyle = '#fff'; g.fillRect(0, 0, w, h); g.drawImage(im, 0, 0, w, h); ok(); };
        im.onerror = () => ok();
        im.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" '));
      });
    }
    function cadreVide(titre, pourquoi) {
      return (g, w, h) => {
        g.fillStyle = '#eef0ec'; g.fillRect(0, 0, w, h); g.strokeStyle = '#b9bfba'; g.setLineDash([12, 9]); g.lineWidth = 3; g.strokeRect(18, 18, w - 36, h - 36); g.setLineDash([]);
        g.fillStyle = '#1b2124'; g.font = 'italic 700 34px Georgia, serif'; g.textAlign = 'center'; ecrire(g, titre, w / 2, h * 0.4, w - 60, 40);
        g.fillStyle = '#5b6560'; g.font = '20px system-ui, sans-serif'; ecrire(g, pourquoi, w / 2, h * 0.52, w - 70, 26); g.textAlign = 'left';
      };
    }
    function dessin5(bits, marge = 0.1) {
      return (g, w, h) => {
        const n = Math.round(Math.sqrt(bits.length)); g.fillStyle = '#ffffff'; g.fillRect(0, 0, w, h);
        const s = Math.min(w, h) * (1 - 2 * marge), px = s / n, ox = (w - s) / 2, oy = (h - s) / 2;
        g.fillStyle = '#1d2326'; for (let i = 0; i < bits.length; i++) if (bits[i] === '1') g.fillRect(ox + (i % n) * px, oy + Math.floor(i / n) * px, px + 0.5, px + 0.5);
      };
    }

    // ---------------------------------------------------------------- les cartels (fenêtre HTML)
    const boiteCartel = $('#m3-cartel');
    const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
    function lien(href, txt) { return `<a href="${esc(BASE + href)}">${esc(txt || href)}</a>`; }
    function montrer(c) {
      boiteCartel.innerHTML = `<button class="m3-ferme" type="button">${T.fermer}</button>${c.etiq === 'c' ? `<span class="m3-etiq c">${T.chantier}</span>` : `<span class="m3-etiq${c.etiq === T.reclame ? ' r' : ''}">${c.etiq || T.donnee}</span>`}<h2>${esc(c.titre)}</h2>${(c.lignes || []).map((l) => `<p>${esc(l)}</p>`).join('')}${c.html || ''}`;
      boiteCartel.hidden = false;
      boiteCartel.querySelector('.m3-ferme').onclick = () => { boiteCartel.hidden = true; };
      const be = boiteCartel.querySelector('#m3-echelle'); if (be) be.onclick = () => { boiteCartel.hidden = true; changerEchelle(); };
    }
    // Réclame (humour, Bran 2/11/2026) : affiche sombre, la blague puis « Ce qui est vrai » en dernière ligne
    function reclame(r, l, h, x, y, zz, ry) {
      if (!r) return;
      plaque({ titre: r.titre, lignes: [...r.lignes, r.vrai], fond: '#1b2124', encre: '#f2f4f1', accent: '#f0b44c', taille: 34 }, l, h, x, y, zz, ry,
        { titre: r.titre, lignes: r.lignes, html: `<p class="m3-src">${esc(r.vrai)}</p>`, etiq: T.reclame });
    }
    // Fenêtre sur le garage : embrasure claire, cadre alu, petit-bois, appui, reflet de vitre ; la photo suit la lumière (vitres)
    const ALU = new THREE.MeshLambertMaterial({ color: 0x9aa1a4 });
    const texReflet = new THREE.CanvasTexture(toile(256, 256, (g, w, h) => {
      const d = g.createLinearGradient(0, 0, w, h); d.addColorStop(0, 'rgba(255,255,255,.55)'); d.addColorStop(0.35, 'rgba(255,255,255,0)'); d.addColorStop(0.55, 'rgba(255,255,255,.18)'); d.addColorStop(0.62, 'rgba(255,255,255,0)'); g.fillStyle = d; g.fillRect(0, 0, w, h);
    }));
    function fenetre(f, l, h, x, y, zz, ry) {
      const grp = new THREE.Group(); grp.position.set(x, y, zz); grp.rotation.y = ry; scene.add(grp);
      const c = f.cartel[LG], cartel = { titre: c.titre, lignes: c.lignes, html: `<p class="m3-src">${esc(c.vrai)}</p>`, etiq: f.titre[LG] };
      const tex = new THREE.TextureLoader().load(BASE + f.image, () => {}, undefined, () => { grp.visible = false; });
      const photo = new THREE.Mesh(new THREE.PlaneGeometry(l, h), new THREE.MeshBasicMaterial({ map: tex, color: 0xffffff }));
      photo.position.z = 0.105; grp.add(photo); vitres.push(photo.material);
      const e = 0.09, p = 0.16, zc = 0.1 + p / 2;
      for (const [w, hh, px, py] of [[l + 2 * e, e, 0, h / 2 + e / 2], [l + 2 * e, e, 0, -h / 2 - e / 2], [e, h, -l / 2 - e / 2, 0], [e, h, l / 2 + e / 2, 0]]) {
        const b = new THREE.Mesh(new THREE.BoxGeometry(w, hh, p), ALU); b.position.set(px, py, zc); grp.add(b); b.userData.cartel = cartel; cliquables.push(b);
      }
      const v = new THREE.Mesh(new THREE.BoxGeometry(0.035, h, 0.03), ALU); v.position.set(0, 0, 0.13); grp.add(v);
      const hz = new THREE.Mesh(new THREE.BoxGeometry(l, 0.035, 0.03), ALU); hz.position.set(0, l < h ? h * 0.12 : 0, 0.13); grp.add(hz);
      const appui = new THREE.Mesh(new THREE.BoxGeometry(l + 0.36, 0.06, 0.3), SOCLE); appui.position.set(0, -h / 2 - e - 0.03, 0.25); grp.add(appui);
      const r = new THREE.Mesh(new THREE.PlaneGeometry(l, h), new THREE.MeshBasicMaterial({ map: texReflet, transparent: true, opacity: 0.22, blending: THREE.AdditiveBlending, depthWrite: false }));
      r.position.z = 0.12; grp.add(r);
      photo.userData.cartel = cartel; r.userData.cartel = cartel; cliquables.push(photo);
      return grp;
    }
    const verifier = (s) => [s.lien ? `<p>${T.voir} : ${lien(s.lien)}</p>` : '', (s.verifier || []).length ? `<p class="m3-src">${T.vers} : ${s.verifier.map((v) => lien(v)).join(', ')}</p>` : ''].join('');

    // ---------------------------------------------------------------- le plan, calculé
    let z = 0;
    const zones = [];   // pour le nom de la salle où l'on est
    // Hauteurs variables (Bran, 26/10 et 2/11/2026) : chaque genre de salle a sa hauteur, et deux salles voisines du même genre diffèrent.
    const HAUT = { hall: 5.0, portraits: 6.2, dessins: 4.4, artistes: 3.6, sculptures: 5.4, sculpteurs: 3.9, glyphes: 4.8, fermee: 4.2 };
    const hauteur = (type, k) => (HAUT[type] || 4.4) + (type === 'artistes' || type === 'sculpteurs' ? (k % 2) * 0.6 : 0);   // type inconnu : hauteur ordinaire, jamais NaN

    // L'écriture de l'ère en cours : annexe à droite du hall (demande de Bran, 7/11/2026), en attendant l'ascenseur (1.3)
    const aileCourante = (M.plan || []).filter((a) => a.etat !== 'fermee' && !a.figee).pop();
    const SG = aileCourante ? aileCourante.salles.find((s) => s.type === 'glyphes') : null;
    // Hall d'accueil
    {
      const H = HAUT.hall, L = 12, z1 = z, z2 = z - L;
      const annexe = (M.annexes || [])[0];
      murs(z1, z2, H, [...(annexe ? [{ cote: -1, z1: -3, z2: -9 }] : []), ...(SG ? [{ cote: 1, z1: -3, z2: -9 }] : [])]);
      boiteM(2 * W, H, 0.2, 0, H / 2, z1, MUR);
      sol(-W, z1, W, z2); plafond(-W, z1, W, z2, H); rais(z1 - 0.3, z2 + 0.3, H);
      plaque({ titre: T.bienvenue, lignes: [T.bienvenue_txt, T.compte(M, M.edition)], taille: 44 }, 4.2, 2.2, (W + PORTE) / 2, 2.2, z2, 0, { titre: T.bienvenue, lignes: [T.bienvenue_txt, T.compte(M, M.edition)], html: `<p class="m3-src">${lien('musee.json')}, ${lien('musee-catalogue.json')}</p>` });
      plaque({ titre: T.seul, lignes: [], taille: 30, fond: '#1b2124', encre: '#f2f4f1', accent: '#5fe08f' }, 3.4, 1.3, 4, 2.4, z1, Math.PI, { titre: T.seul, lignes: [] });
      if (M.reclame) reclame(M.reclame[LG], 3.0, 2.2, -(W + PORTE) / 2, 2.3, z2, 0);   // mur du fond, à gauche de la porte (Bran, 7/11/2026)
      if (M.architecte) reclame(M.architecte[LG], 3.2, 2.2, -4, 2.3, z1, Math.PI);
      if (annexe) {
        const X1 = -W - 6, ch = annexe.etat !== 'ouverte';
        sol(X1, -2.8, -W, -9.2); plafond(X1, -2.8, -W, -9.2, 3.6);
        boiteM(6, 3.6, 0.2, (X1 - W) / 2, 1.8, -2.8, MUR); boiteM(6, 3.6, 0.2, (X1 - W) / 2, 1.8, -9.2, MUR); boiteM(0.2, 3.6, 6.4, X1, 1.8, -6, MUR);
        const c = { titre: annexe.titre[LG], lignes: [ch ? T.chantier + '.' : T.ouverte + '.', annexe.texte[LG]], etiq: ch ? 'c' : undefined, html: annexe.lien ? `<p>${T.voir} : ${lien(annexe.lien)}</p>` : '' };
        plaque({ titre: annexe.titre[LG], lignes: [annexe.texte[LG]], etiq: ch ? { t: T.chantier.toUpperCase(), c: '#ffd23f' } : null, fond: ch ? '#1b1b17' : '#f7f8f5', encre: ch ? '#fff6cf' : '#1b2124', accent: '#ffd23f', taille: 34 }, 3.2, 1.9, X1, 2.0, -6, Math.PI / 2, c);
        if (ch) ruban(-W - 0.3, -3.1, -W - 0.3, -8.9);
      }
      zones.push({ z1, z2, nom: T.hall });
      salles.push({ nom: T.hall, z: z1 - 4 });
      if (SG) annexeEcriture(SG, aileCourante.ere);
      z = z2;
    }

    // Les ailes
    let k = 0, hPrec = HAUT.hall;
    for (const aile of M.plan || []) {
      if (aile.etat === 'fermee') {
        const H = HAUT.fermee, z1 = z, z2 = z - 4;
        cloison(z1, Math.max(H, hPrec));
        murs(z1, z2, H); sol(-W, z1, W, z2); plafond(-W, z1, W, z2, H);
        const porte = cloison(z2, H, true); ruban(-PORTE, z2 + 0.6, PORTE, z2 + 0.6);
        const c = { titre: T.aile(aile.ere), lignes: [T.attente, T.fermee(aile.ere)], etiq: 'c' };
        porte.userData.cartel = c; cliquables.push(porte);
        plaque({ titre: T.aile(aile.ere), lignes: [T.attente], etiq: { t: T.chantier.toUpperCase(), c: '#ffd23f' }, fond: '#1b1b17', encre: '#fff6cf', accent: '#ffd23f' }, 2.8, 1.1, 0, 3.6, z2, 0, c);
        zones.push({ z1, z2, nom: T.aile(aile.ere) });
        z = z2 - 0.2;
        break;   // rien au-delà d'une aile fermée
      }
      for (const s of aile.salles) {
        if (s === SG) continue;   // déjà dans l'annexe de droite du hall
        const H = hauteur(s.type, k++);
        let L = 12;
        if (s.type === 'portraits') L = Math.max(14, Math.ceil(s.oeuvres.length / 2) * 4.4 + 6);
        if (s.type === 'dessins') L = 17.4;
        if (s.type === 'artistes') L = Math.max(9, Math.ceil(s.oeuvres.length / 2) * 2.4 + 4);
        if (s.type === 'sculptures') L = 19;
        if (s.type === 'sculpteurs') L = Math.max(9, Math.ceil(s.oeuvres.length / 2) * 2.6 + 4);
        if (s.type === 'glyphes') L = Math.max(15, s.noms.length * 3.4 + 5);
        const z1 = z, z2 = z - L, nom = `${T.aile(aile.ere)} · ${s.titre[LG]}`;
        cloison(z1, Math.max(H, hPrec));
        murs(z1, z2, H); sol(-W, z1, W, z2); plafond(-W, z1, W, z2, H);
        if (k % 2) rais(z1 - 0.4, z2 + 0.4, H);
        const titreSalle = { titre: s.titre[LG], lignes: aile.figee ? [T.figee(aile.ere)] : [T.aile(aile.ere)], taille: 52 };
        plaque(titreSalle, 2.8, 1.2, -(W + PORTE) / 2, 2.2, z1, 0, { titre: s.titre[LG], lignes: titreSalle.lignes, html: verifier(s) });
        if (s.reclame) reclame(s.reclame[LG], 2.8, 2.0, (W + PORTE) / 2, 2.3, z2, 0);
        if (s.type === 'portraits') sallePortraits(s, z1, z2, H);
        if (s.type === 'dessins') salleDessins(s, z1, z2, H);
        if (s.type === 'artistes') salleArtistes(s, z1, z2, H);
        if (s.type === 'sculptures') salleSculptures(s, z1, z2, H);
        if (s.type === 'sculpteurs') salleSculpteurs(s, z1, z2, H);
        if (s.type === 'glyphes') salleGlyphes(s, z1, z2, H);
        zones.push({ z1, z2, nom });
        salles.push({ nom, z: z1 - 2 });
        z = z2; hPrec = H;
      }
    }
    // Fond : l'aile de l'ère suivante, fermée
    if (!(M.plan || []).some((a) => a.etat === 'fermee')) {
      const FEN = M.fenetres ? Object.fromEntries(M.fenetres.liste.map((f) => [f.id, f])) : {};
      const avecFen = Object.keys(FEN).length > 0;
      const H = 4.2, z1 = z, z2 = z - (avecFen ? 10 : 7);
      cloison(z1, Math.max(H, hPrec));
      // Cartel de sortie (idée de Bran, 2/11/2026) : tout un pays dans une boîte
      if (M.fin) {
        const f = M.fin[LG];
        plaque({ titre: f.titre, lignes: [...f.lignes, f.vrai], taille: 30 }, 3.6, 3.0, -(W - 0.1), 2.1, z1 - 3.5, Math.PI / 2,
          { titre: f.titre, lignes: f.lignes, html: `<p class="m3-src">${esc(f.vrai)}</p><p><button type="button" id="m3-echelle">${T.echelle}</button></p>` });
        halo(-(W - 0.1), 2.1, z1 - 3.5, Math.PI / 2, 5.4, 4.4);
      }
      murs(z1, z2, H); sol(-W, z1, W, z2); plafond(-W, z1, W, z2, H);
      const porte = cloison(z2, H, true); ruban(-PORTE, z2 + 0.6, PORTE, z2 + 0.6);
      // Les 4 fenêtres : nord = mur du fond (on marche vers le nord), est à droite, ouest à gauche, sud = mur d'entrée
      const pl = (f) => (f.largeur >= f.hauteur ? [3.0, 3.0 * f.hauteur / f.largeur] : [1.4, 1.4 * f.hauteur / f.largeur]);
      if (FEN.nord) { const [l, h] = pl(FEN.nord); fenetre(FEN.nord, l, h, -(W + PORTE) / 2, 2.1, z2, 0); }
      if (FEN.est) { const [l, h] = pl(FEN.est); fenetre(FEN.est, l, h, W, 0.85 + h / 2, z1 - 5, -Math.PI / 2); }
      if (FEN.ouest) { const [l, h] = pl(FEN.ouest); fenetre(FEN.ouest, l, h, -W, 0.85 + h / 2, z1 - 7.6, Math.PI / 2); }
      if (FEN.sud) { const [l, h] = pl(FEN.sud); fenetre(FEN.sud, l, h, (W + PORTE) / 2, 0.85 + h / 2, z1, Math.PI); }
      if (avecFen) { const nom = M.fenetres.salle[LG]; zones.push({ z1, z2: z2 + 1.2, nom }); salles.push({ nom, z: z1 - 5 }); }
      const n = M.suivante ? M.suivante.ere : '?';
      const c = { titre: T.aile(n), lignes: [T.attente], etiq: 'c' };
      porte.userData.cartel = c; cliquables.push(porte);
      plaque({ titre: T.aile(n), lignes: [T.attente], etiq: { t: T.chantier.toUpperCase(), c: '#ffd23f' }, fond: '#1b1b17', encre: '#fff6cf', accent: '#ffd23f' }, 2.8, 1.1, 0, 3.55, z2, 0, c);
      zones.push({ z1: avecFen ? z2 + 1.2 : z1, z2, nom: T.aile(n) });
      if (!avecFen) salles.push({ nom: T.aile(n), z: z1 - 1.5 });
    }

    // ---------------------------------------------------------------- salle des présidents
    function sallePortraits(s, z1, z2, H) {
      const n = s.oeuvres.length;
      s.oeuvres.forEach((o, i) => {
        const cote = i % 2 === 0 ? -1 : 1, rang = Math.floor(i / 2);
        const zc = z1 - 3.4 - rang * 4.4;
        const ry = cote < 0 ? Math.PI / 2 : -Math.PI / 2;
        const k = o.cartel[LG];
        const c = { titre: k.nom, lignes: [k.info, ...k.lignes, ...k.bas], html: (o.fichier ? `<p class="m3-src">${T.source} : <a href="https://donnees.microcontroland.org/${esc(o.fichier)}">${esc(o.fichier)}</a></p>` : '') + verifier(s) };
        const dessiner = o.svg ? svgVersToile(o.svg) : cadreVide(k.vide[0], k.vide[1]);
        // Le cartel est à côté du tableau, jamais dessous ni caché (demande de Bran du 26/10/2026) : 1,5 m de tableau, 0,4 m d'écart, 1 m de cartel.
        const dz = cote < 0 ? 1 : -1;
        cadre(dessiner, 1.5, 2.0, cote * (W - 0.1), 2.35, zc, ry, c);
        plaque({ titre: k.nom, lignes: [k.info, ...k.lignes].slice(0, 6), taille: 52 }, 1.0, 1.25, cote * (W - 0.1), 1.55, zc - dz * 1.45, ry, c);
        halo(cote * (W - 0.1), 2.4, zc, ry, 3.2, 3.6);
      });
      if (s.statue) statue(s.statue, (z1 + z2) / 2, s);
      void n;
    }
    function statue(st, zc, s) {
      const grp = new THREE.Group(); grp.position.set(0, 0, zc); scene.add(grp);
      boiteM(1.6, 0.5, 1.6, 0, 0.25, zc, SOCLE);
      const w = st.poids.map((x) => x * 5 / 127);
      const w1 = [...Array(6)].map((_, h) => w.slice(h * 10, h * 10 + 10));
      const w2 = [...Array(3)].map((_, o) => w.slice(60 + o * 7, 60 + o * 7 + 7));
      const couches = [9, 6, 3], ys = [0.95, 1.85, 2.75], rayons = [0.62, 0.46, 0.26];
      const pos = couches.map((n, c) => [...Array(n)].map((_, i) => { const a = (i / n) * Math.PI * 2 + c * 0.4; return new THREE.Vector3(Math.cos(a) * rayons[c], ys[c], Math.sin(a) * rayons[c]); }));
      const vert = new THREE.MeshBasicMaterial({ color: 0x3fbf6f }), ambre = new THREE.MeshBasicMaterial({ color: 0xd8962c });
      const lien3 = (a, b, v) => {
        const f = Math.min(1, Math.abs(v) / 2.5), r = 0.004 + 0.026 * f, d = a.distanceTo(b);
        const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, d, 6), v >= 0 ? vert : ambre);
        m.position.copy(a).add(b).multiplyScalar(0.5); m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), b.clone().sub(a).normalize()); grp.add(m);
      };
      for (let h = 0; h < 6; h++) for (let i = 0; i < 9; i++) lien3(pos[0][i], pos[1][h], w1[h][i]);
      for (let o = 0; o < 3; o++) for (let h = 0; h < 6; h++) lien3(pos[1][h], pos[2][o], w2[o][h]);
      const blanc = new THREE.MeshLambertMaterial({ color: 0xf4f6f2, emissive: 0x223328 });
      const noeud = (p, b) => { const m = new THREE.Mesh(new THREE.SphereGeometry(0.045 + 0.05 * Math.min(1, Math.abs(b) / 2.5), 14, 10), blanc); m.position.copy(p); grp.add(m); };
      pos[0].forEach((p) => noeud(p, 0)); pos[1].forEach((p, h) => noeud(p, w1[h][9])); pos[2].forEach((p, o) => noeud(p, w2[o][6]));
      const c = { titre: T.statue(st.nom), lignes: [T.statue_txt], html: `<p class="m3-src">${T.source} : <a href="https://donnees.microcontroland.org/${esc(st.fichier)}">${esc(st.fichier)}</a></p>` + verifier(s) };
      const zoneClic = new THREE.Mesh(new THREE.CylinderGeometry(0.8, 0.8, 2.6, 12), new THREE.MeshBasicMaterial({ visible: false })); zoneClic.position.set(0, 1.6, zc); scene.add(zoneClic);
      zoneClic.userData.cartel = c; cliquables.push(zoneClic);
      plaque({ titre: T.statue(st.nom), lignes: [], taille: 40 }, 1.5, 0.42, 0, 0.3, zc + 0.69, 0, c);
    }

    // ---------------------------------------------------------------- l'atelier (120 dessins du dernier soir)
    function salleDessins(s, z1, z2, H) {
      const art = s.artiste;
      const crit = ((s.critique || {})[LG]) || [];
      const cs = { titre: s.titre[LG], lignes: [T.soir_du(dateLongue(s.date), s.edition), T.artiste_soir + ' : ' + T.cit(art, regionDe(art)), ...crit], html: (s.source ? `<p class="m3-src">${T.source} : <a href="https://donnees.microcontroland.org/${esc(s.source)}">${esc(s.source)}</a></p>` : '') + verifier(s) };
      for (let r = 0; r < 6; r++) {
        const cote = r < 3 ? -1 : 1, i = r % 3, zc = z1 - 3.6 - i * 4.6, ry = cote < 0 ? Math.PI / 2 : -Math.PI / 2;
        const murRegion = (g, w, h) => {
          g.fillStyle = '#f4f5f1'; g.fillRect(0, 0, w, h); g.fillStyle = '#2a3034'; g.font = '700 30px Georgia, serif'; g.fillText(region(REGIONS[r]), 16, 38);
          const cw = w / 5, ch = (h - 54) / 4;
          for (let q = 0; q < 20; q++) {
            const id = r * 20 + q + 1, d = s.dessins[id - 1]; if (!d) continue;
            const t = Math.min(cw, ch) * 0.74, px = t / 5, ox = (q % 5) * cw + (cw - t) / 2, oy = 54 + Math.floor(q / 5) * ch + (ch - t) / 2;
            if (id === art) { g.fillStyle = '#c9a447'; g.fillRect(ox - 6, oy - 6, t + 12, t + 12); }
            g.fillStyle = '#fff'; g.fillRect(ox - 2, oy - 2, t + 4, t + 4); g.fillStyle = '#1d2326';
            for (let b = 0; b < 25; b++) if (d[b] === '1') g.fillRect(ox + (b % 5) * px, oy + Math.floor(b / 5) * px, px + 0.5, px + 0.5);
          }
        };
        cadre(murRegion, 3.4, 2.9, cote * (W - 0.1), 2.1, zc, ry, cs);
        halo(cote * (W - 0.1), 2.1, zc, ry, 5.5, 4.6);
      }
      // Au centre, l'artiste du soir en grand, sur une cimaise vue des deux côtés
      const zc = (z1 + z2) / 2;
      boiteM(2.6, 2.8, 0.25, 0, 1.4, zc, MUR);
      for (const sens of [1, -1]) {
        const g = cadre(dessin5(s.dessins[art - 1] || ''), 1.4, 1.4, 0, 1.75, zc, sens > 0 ? 0 : Math.PI, cs, true);
        void g;
        plaque({ titre: T.artiste_soir, lignes: [T.cit(art, regionDe(art))], taille: 46 }, 1.6, 0.5, 0, 0.62, zc, sens > 0 ? 0 : Math.PI, cs);
      }
    }

    // ---------------------------------------------------------------- l'écriture (glyphes 5 × 5 et cartouches, âge de l'État civil)
    // Glyphes et cartouches sont calculés par .github/ecriture.py et lus tels quels dans musee.json.
    function grille(rangs, marge = 0.1) {
      const R = typeof rangs === 'string' ? rangs.match(/.{5}/g) : rangs;
      return (g, w, h) => {
        g.fillStyle = '#ffffff'; g.fillRect(0, 0, w, h);
        const px = Math.min(w * (1 - 2 * marge) / R[0].length, h * (1 - 2 * marge) / R.length), ox = (w - px * R[0].length) / 2, oy = (h - px * R.length) / 2;
        g.fillStyle = '#1d2326'; R.forEach((l, y) => { for (let x = 0; x < l.length; x++) if (l[x] === '1') g.fillRect(ox + x * px, oy + y * px, px + 0.5, px + 0.5); });
      };
    }
    function salleGlyphes(s, z1, z2, H) {
      const src = (s.source ? `<p class="m3-src">${T.source} : <a href="https://donnees.microcontroland.org/${esc(s.source)}">${esc(s.source)}</a></p>` : '') + verifier(s);
      // Mur de gauche : l'abécédaire, un grand panneau de tous les glyphes communs avec leur mot
      const ca = { titre: T.abc, lignes: [T.abc_txt(s.oeuvres.length, s.idees), T.ouverte_le(dateLongue(s.ouverture)), T.regle_g, ...s.oeuvres.map((o) => `${o.ecrit} : ${o[LG]}`)], html: src };
      const abc = (g, w, h) => {
        g.fillStyle = '#f4f5f1'; g.fillRect(0, 0, w, h); g.fillStyle = '#2a3034'; g.font = '700 30px Georgia, serif'; g.fillText(T.abc, 18, 40);
        const nc = 8, nl = Math.max(1, Math.ceil(s.oeuvres.length / nc)), cw = w / nc, ch = (h - 60) / nl;
        s.oeuvres.forEach((o, i) => {
          const t = Math.min(cw, ch) * 0.58, px = t / 5, ox = (i % nc) * cw + (cw - t) / 2, oy = 60 + Math.floor(i / nc) * ch + 4;
          g.fillStyle = '#fff'; g.fillRect(ox - 3, oy - 3, t + 6, t + 6); g.fillStyle = '#1d2326';
          for (let b = 0; b < 25; b++) if (o.glyphe[b] === '1') g.fillRect(ox + (b % 5) * px, oy + Math.floor(b / 5) * px, px + 0.5, px + 0.5);
          g.font = `600 ${Math.max(11, Math.round(ch * 0.13))}px ui-monospace, Menlo, monospace`; g.textAlign = 'center';
          g.fillText(o.ecrit, (i % nc) * cw + cw / 2, oy + t + ch * 0.17); g.textAlign = 'left';
        });
      };
      const za = (z1 + z2) / 2;
      cadre(abc, Math.min(8, -(z2 - z1) - 4), 3.2, -(W - 0.1), 2.2, za, Math.PI / 2, ca);
      halo(-(W - 0.1), 2.2, za, Math.PI / 2, 9, 4.6);
      // Mur de droite : les noms en cartouche
      s.noms.forEach((n, i) => {
        const zc = z1 - 3 - i * 3.4, ry = -Math.PI / 2;
        const cap = n.fin ? T.pres_de(dateLongue(n.debut), dateLongue(n.fin)) : T.pres_dep(dateLongue(n.debut));
        const c = { titre: n.nom, lignes: [`${region(n.region)} · ${cap}`, T.noms_txt], html: verifier(s) };
        const l = 0.22 * n.rangs[0].length;
        cadre(grille(n.rangs, 0.08), l, 0.22 * 7, W - 0.1, 2.1, zc, ry, c, true);
        plaque({ titre: n.nom, lignes: [cap], taille: 46 }, 1.8, 0.6, W - 0.1, 0.95, zc, ry, c);
        halo(W - 0.1, 2.1, zc, ry, 3, 2.8);
      });
      // Au centre, la frise des soirs sur une cimaise vue des deux côtés
      if (s.frise.length) {
        const F = s.frise.slice(-24), zc = (z1 + z2) / 2, n = F.length, l = Math.min(5.6, 0.62 * n + 0.6);   // les 24 derniers soirs au mur, tous au cartel
        const cf = { titre: T.frise, lignes: [T.frise_txt, ...s.frise.map((f) => `${dateLongue(f.date)} : ${f.ecrit} (${f[LG]})`)], html: src };
        const frise = (g, w, h) => {
          g.fillStyle = '#ffffff'; g.fillRect(0, 0, w, h);
          const cw = w / n, t = Math.min(cw * 0.72, h * 0.62), px = t / 5;
          F.forEach((f, i) => {
            const ox = i * cw + (cw - t) / 2, oy = h * 0.1; g.fillStyle = '#1d2326';
            for (let b = 0; b < 25; b++) if (f.glyphe[b] === '1') g.fillRect(ox + (b % 5) * px, oy + Math.floor(b / 5) * px, px + 0.5, px + 0.5);
            g.fillStyle = '#5b6560'; g.font = `${Math.max(10, Math.round(cw * 0.16))}px ui-monospace, Menlo, monospace`; g.textAlign = 'center';
            g.fillText(f.date.slice(8).replace(/^0/, '') + '/' + f.date.slice(5, 7).replace(/^0/, ''), i * cw + cw / 2, h * 0.92); g.textAlign = 'left';
          });
        };
        boiteM(l + 0.6, 2.6, 0.25, 0, 1.3, zc, MUR);
        for (const sens of [1, -1]) {
          cadre(frise, l, Math.max(0.7, l / n * 1.2), 0, 1.9, zc, sens > 0 ? 0 : Math.PI, cf);
          plaque({ titre: T.frise, lignes: [], taille: 46 }, 1.8, 0.45, 0, 0.75, zc, sens > 0 ? 0 : Math.PI, cf);
        }
      }
      // Mur du fond : l'histoire de l'écriture
      const lignes = [T.ouverte_le(dateLongue(s.ouverture)), ...s.histoire.map(([d, k]) => T.hist(dateLongue(d), k))];
      plaque({ titre: T.histoire, lignes: lignes.slice(0, 12), taille: 30 }, 2.6, 2.4, -(W + PORTE) / 2, 2.2, z2, 0, { titre: T.histoire, lignes, html: src });
    }

    // L'écriture dans une annexe à droite du hall (Bran, 7/11/2026) : 12 m de profondeur, ouverture de 6 m dans le mur du hall.
    // Abécédaire au fond, cartouches au mur sud, frise et histoire au mur nord ; titre et réclame sur le mur du hall.
    function annexeEcriture(s, ere) {
      const X1 = W, X2 = W + 12, A1 = -1.6, A2 = -10.4, H = HAUT.glyphes, zm = (A1 + A2) / 2;
      sol(X1, A1, X2, A2); plafond(X1, A1, X2, A2, H);
      boiteM(X2 - X1, H, 0.2, (X1 + X2) / 2, H / 2, A1, MUR); boiteM(X2 - X1, H, 0.2, (X1 + X2) / 2, H / 2, A2, MUR); boiteM(0.2, H, A1 - A2 + 0.2, X2, H / 2, zm, MUR);
      const nom = `${T.aile(ere)} · ${s.titre[LG]}`;
      const src = (s.source ? `<p class="m3-src">${T.source} : <a href="https://donnees.microcontroland.org/${esc(s.source)}">${esc(s.source)}</a></p>` : '') + verifier(s);
      // Dans le hall, de part et d'autre de l'ouverture : le titre de la salle et sa réclame
      plaque({ titre: s.titre[LG], lignes: [T.aile(ere)], taille: 52 }, 2.4, 1.1, W - 0.1, 2.3, -10.5, -Math.PI / 2, { titre: s.titre[LG], lignes: [T.aile(ere)], html: verifier(s) });
      if (s.reclame) reclame(s.reclame[LG], 2.4, 1.8, W - 0.1, 2.3, -1.5, -Math.PI / 2);
      // Mur du fond : l'abécédaire
      const ca = { titre: T.abc, lignes: [T.abc_txt(s.oeuvres.length, s.idees), T.ouverte_le(dateLongue(s.ouverture)), T.regle_g, ...s.oeuvres.map((o) => `${o.ecrit} : ${o[LG]}`)], html: src };
      const abc = (g, w, h) => {
        g.fillStyle = '#f4f5f1'; g.fillRect(0, 0, w, h); g.fillStyle = '#2a3034'; g.font = '700 30px Georgia, serif'; g.fillText(T.abc, 18, 40);
        const nc = 8, nl = Math.max(1, Math.ceil(s.oeuvres.length / nc)), cw = w / nc, ch = (h - 60) / nl;
        s.oeuvres.forEach((o, i) => {
          const tt = Math.min(cw, ch) * 0.58, px = tt / 5, ox = (i % nc) * cw + (cw - tt) / 2, oy = 60 + Math.floor(i / nc) * ch + 4;
          g.fillStyle = '#fff'; g.fillRect(ox - 3, oy - 3, tt + 6, tt + 6); g.fillStyle = '#1d2326';
          for (let b = 0; b < 25; b++) if (o.glyphe[b] === '1') g.fillRect(ox + (b % 5) * px, oy + Math.floor(b / 5) * px, px + 0.5, px + 0.5);
          g.font = `600 ${Math.max(11, Math.round(ch * 0.13))}px ui-monospace, Menlo, monospace`; g.textAlign = 'center';
          g.fillText(o.ecrit, (i % nc) * cw + cw / 2, oy + tt + ch * 0.17); g.textAlign = 'left';
        });
      };
      cadre(abc, 7.4, 3.2, X2 - 0.1, 2.2, zm, -Math.PI / 2, ca);
      halo(X2 - 0.1, 2.2, zm, -Math.PI / 2, 8.6, 4.6);
      // Mur sud : les noms en cartouche (la place se partage si les présidents se multiplient)
      const n = s.noms.length, pas = n ? Math.min(3.2, 9.6 / n) : 0, ech = pas / 3.2;
      s.noms.forEach((no, i) => {
        const xc = X1 + 1.6 + pas * (i + 0.5), ry = Math.PI;
        const cap = no.fin ? T.pres_de(dateLongue(no.debut), dateLongue(no.fin)) : T.pres_dep(dateLongue(no.debut));
        const c = { titre: no.nom, lignes: [`${region(no.region)} · ${cap}`, T.noms_txt], html: verifier(s) };
        cadre(grille(no.rangs, 0.08), 0.22 * no.rangs[0].length * ech, 0.22 * 7 * ech, xc, 2.1, A1, ry, c, true);
        plaque({ titre: no.nom, lignes: [cap], taille: 46 }, 1.8 * ech, 0.6 * ech, xc, 1.0, A1, ry, c);
        halo(xc, 2.1, A1, ry, 3 * ech, 2.8);
      });
      // Mur nord : la frise des soirs (les 24 derniers au mur, tous au cartel) et l'histoire
      if (s.frise.length) {
        const F = s.frise.slice(-24), nf = F.length, l = Math.min(5.6, 0.62 * nf + 0.6), xc = X1 + 1.2 + l / 2;
        const cf = { titre: T.frise, lignes: [T.frise_txt, ...s.frise.map((f) => `${dateLongue(f.date)} : ${f.ecrit} (${f[LG]})`)], html: src };
        const frise = (g, w, h) => {
          g.fillStyle = '#ffffff'; g.fillRect(0, 0, w, h);
          const cw = w / nf, tt = Math.min(cw * 0.72, h * 0.62), px = tt / 5;
          F.forEach((f, i) => {
            const ox = i * cw + (cw - tt) / 2, oy = h * 0.1; g.fillStyle = '#1d2326';
            for (let b = 0; b < 25; b++) if (f.glyphe[b] === '1') g.fillRect(ox + (b % 5) * px, oy + Math.floor(b / 5) * px, px + 0.5, px + 0.5);
            g.fillStyle = '#5b6560'; g.font = `${Math.max(10, Math.round(cw * 0.16))}px ui-monospace, Menlo, monospace`; g.textAlign = 'center';
            g.fillText(f.date.slice(8).replace(/^0/, '') + '/' + f.date.slice(5, 7).replace(/^0/, ''), i * cw + cw / 2, h * 0.92); g.textAlign = 'left';
          });
        };
        cadre(frise, l, Math.max(0.7, l / nf * 1.2), xc, 2.0, A2, 0, cf);
        plaque({ titre: T.frise, lignes: [], taille: 46 }, 1.8, 0.45, xc, 1.15, A2, 0, cf);
        halo(xc, 2.0, A2, 0, l + 1, 2.4);
      }
      const lignes = [T.ouverte_le(dateLongue(s.ouverture)), ...s.histoire.map(([d, k]) => T.hist(dateLongue(d), k))];
      plaque({ titre: T.histoire, lignes: lignes.slice(0, 12), taille: 30 }, 2.6, 2.4, X2 - 2.0, 2.2, A2, 0, { titre: T.histoire, lignes, html: src });
      salles.push({ nom, z: zm, x: W + 3, yaw: -Math.PI / 2 });
    }

    // ---------------------------------------------------------------- les artistes du soir (un tableau par soir, une salle par mois)
    function salleArtistes(s, z1, z2, H) {
      s.oeuvres.forEach((o, i) => {
        const cote = i % 2 === 0 ? -1 : 1, rang = Math.floor(i / 2), zc = z1 - 2.6 - rang * 2.4, ry = cote < 0 ? Math.PI / 2 : -Math.PI / 2;
        const crit = ((o.critique || {})[LG]) || [];
        const c = { titre: T.cit(o.id, region(o.region)), lignes: [T.soir_du(dateLongue(o.date), o.edition), T.cases(o.cases), ...crit], html: (o.source ? `<p class="m3-src">${T.source} : <a href="https://donnees.microcontroland.org/${esc(o.source)}">${esc(o.source)}</a></p>` : '') + verifier(s) };
        cadre(dessin5(o.dessin), 1.0, 1.0, cote * (W - 0.1), 2.0, zc, ry, c);
        plaque({ titre: dateLongue(o.date), lignes: [T.cit(o.id, region(o.region))], taille: 52 }, 1.0, 0.5, cote * (W - 0.1), 1.05, zc, ry, c);
        halo(cote * (W - 0.1), 2.0, zc, ry, 2.2, 2.6);
      });
    }

    // ---------------------------------------------------------------- les sculptures (art secondaire, cubes 8 × 8 × 8, règle S1)
    // Les cubes sont calculés par .github/sculptures.py et lus tels quels (512 chiffres : 0 = vide, 1 à 9 = taille) :
    // la visite 3D ne recalcule rien. Une seule couleur (la couleur est réservée à l'art évolué de la Curiosité).
    // Pose les cubes de plusieurs sculptures dans un seul InstancedMesh : [{ s, x, y, z, taille }] (y = bas de la sculpture)
    function cubes(liste, parent) {
      const n = liste.reduce((t, o) => t + (o.s.match(/[1-9]/g) || []).length, 0);
      if (!n) return null;
      const im = new THREE.InstancedMesh(unCube, BRONZE, n), m = new THREE.Matrix4(), q = new THREE.Quaternion(), p = new THREE.Vector3(), e = new THREE.Vector3();
      let k = 0;
      for (const o of liste) {
        const c = o.taille / 8;
        for (let i = 0; i < 512; i++) {
          const v = +o.s[i]; if (!v) continue;
          const X = Math.floor(i / 64), Y = Math.floor(i / 8) % 8, Z = i % 8, t = c * (0.35 + 0.6 * (v - 1) / 8);
          p.set(o.x + (X - 3.5) * c, o.y + (Z + 0.5) * c, o.z + (Y - 3.5) * c); e.set(t, t, t);
          m.compose(p, q, e); im.setMatrixAt(k++, m);
        }
      }
      im.instanceMatrix.needsUpdate = true;
      (parent || scene).add(im);
      return im;
    }
    function zoneClic(x, y, zz, l, h, d, cartel) {
      const m = new THREE.Mesh(new THREE.BoxGeometry(l, h, d), new THREE.MeshBasicMaterial({ visible: false }));
      m.position.set(x, y, zz); scene.add(m); m.userData.cartel = cartel; cliquables.push(m);
    }
    function salleSculptures(s, z1, z2, H) {
      const sc = s.sculpteur, crit = ((s.critique || {})[LG]) || [];
      const src = s.source ? `<p class="m3-src">${T.source} : <a href="https://donnees.microcontroland.org/${esc(s.source)}">${esc(s.source)}</a></p>` : '';
      const cs = { titre: s.titre[LG], lignes: [T.soir_du(dateLongue(s.date), s.edition), T.sculpteur_soir + ' : ' + T.cit(sc, regionDe(sc)), ...crit], html: src + verifier(s) };
      const petites = [];
      for (let r = 0; r < 6; r++) {
        // Une table par région, 3 de chaque côté ; 20 sculptures en 2 rangs de 10
        const cote = r < 3 ? -1 : 1, i = r % 3, zc = z1 - 3.4 - i * 5.0, xt = cote * (W - 1.5), Lt = 3.6, D = 1.0, ht = 0.85;
        boiteM(D, ht, Lt, xt, ht / 2, zc, SOCLE);
        const ct = { titre: T.table(region(REGIONS[r])), lignes: [T.soir_du(dateLongue(s.date), s.edition), T.table_txt], html: src + verifier(s) };
        zoneClic(xt, ht + 0.25, zc, D, 0.6, Lt, ct);
        plaque({ titre: region(REGIONS[r]), lignes: [T.table(region(REGIONS[r]))], taille: 50 }, 1.6, 0.55, cote * (W - 0.1), 1.75, zc, cote < 0 ? Math.PI / 2 : -Math.PI / 2, ct);
        halo(cote * (W - 0.1), 1.6, zc, cote < 0 ? Math.PI / 2 : -Math.PI / 2, 4.4, 3.2);
        for (let q = 0; q < 20; q++) {
          const id = r * 20 + q + 1, sculpt = s.sculptures[id - 1]; if (!sculpt) continue;
          const x = xt + (q < 10 ? -0.22 : 0.22) * cote, zz = zc - Lt / 2 + 0.18 + (q % 10) * 0.36;
          if (id === sc) boiteM(0.3, 0.02, 0.3, x, ht + 0.01, zz, OR, false);
          petites.push({ s: sculpt, x, y: ht + 0.02, z: zz, taille: 0.24 });
        }
      }
      cubes(petites);
      // Au centre, le sculpteur du soir en grand, sur un socle ; il tourne lentement (sauf si le visiteur a demandé moins d'animations)
      const zc = (z1 + z2) / 2;
      boiteM(1.3, 0.9, 1.3, 0, 0.45, zc, SOCLE);
      if (sc && s.sculptures[sc - 1]) {
        const grp = new THREE.Group(); grp.position.set(0, 0, zc); scene.add(grp);
        cubes([{ s: s.sculptures[sc - 1], x: 0, y: 0.9, z: 0, taille: 1.15 }], grp);
        if (!lent) tournants.push(grp);
      }
      zoneClic(0, 1.4, zc, 1.4, 2.0, 1.4, cs);
      for (const sens of [1, -1]) plaque({ titre: T.sculpteur_soir, lignes: [T.cit(sc, regionDe(sc))], taille: 46 }, 1.2, 0.42, 0, 0.45, zc + sens * 0.66, sens > 0 ? 0 : Math.PI, cs);
    }
    function salleSculpteurs(s, z1, z2, H) {
      s.oeuvres.forEach((o, i) => {
        const cote = i % 2 === 0 ? -1 : 1, rang = Math.floor(i / 2), zc = z1 - 2.8 - rang * 2.6, ry = cote < 0 ? Math.PI / 2 : -Math.PI / 2, x = cote * (W - 1.3);
        const crit = ((o.critique || {})[LG]) || [];
        const c = { titre: T.cit(o.id, region(o.region)), lignes: [T.soir_du(dateLongue(o.date), o.edition), T.deplaces(o.deplaces), ...crit], html: (o.source ? `<p class="m3-src">${T.source} : <a href="https://donnees.microcontroland.org/${esc(o.source)}">${esc(o.source)}</a></p>` : '') + verifier(s) };
        boiteM(0.7, 1.0, 0.7, x, 0.5, zc, SOCLE);
        cubes([{ s: o.sculpture, x, y: 1.0, z: zc, taille: 0.55 }]);
        zoneClic(x, 1.25, zc, 0.8, 0.7, 0.8, c);
        plaque({ titre: dateLongue(o.date), lignes: [T.cit(o.id, region(o.region))], taille: 52 }, 1.0, 0.5, cote * (W - 0.1), 2.15, zc, ry, c);
        halo(cote * (W - 0.1), 1.9, zc, ry, 2.2, 2.6);
      });
    }

    // ---------------------------------------------------------------- lumière : cycle selon l'heure du visiteur (Bran, 2/11/2026)
    const ciel = new THREE.HemisphereLight(0xffffff, 0x4a4e4c, 0.7); scene.add(ciel);
    const fond = new THREE.AmbientLight(0xffffff, 0.15); scene.add(fond);
    const soleil = new THREE.DirectionalLight(0xfff3dc, 0.35); soleil.position.set(6, 10, 4); scene.add(soleil);
    const AMB = {   // a = jour plein (1), s = soir (couleur chaude), n = nuit
      jour: { vue: 0xffffff, ciel: 0.88, fond: 0.3, soleil: 0.35, c: 0xffffff, fente: 0xffffff, dalle: 0xd4d6d2, rais: 0.3, raisC: 0xfff8e6, halo: 0.0, bg: 0x121619 },
      soir: { vue: 0xd6b898, ciel: 0.7, fond: 0.22, soleil: 0.25, c: 0xffd9b0, fente: 0xf2b98a, dalle: 0xa89a8c, rais: 0.26, raisC: 0xffa868, halo: 0.25, bg: 0x1a1414 },
      nuit: { vue: 0x3a4252, ciel: 0.13, fond: 0.06, soleil: 0.0, c: 0x9fb0d0, fente: 0x27304a, dalle: 0x1a1d22, rais: 0.0, raisC: 0x000000, halo: 0.55, bg: 0x07090c },
    };
    const mel = (a, b, t) => a + (b - a) * t;
    const melC = (a, b, t) => new THREE.Color(a).lerp(new THREE.Color(b), t);
    // Heure locale → mélange : nuit avant 6 h et après 22 h ; aube de 6 h à 8 h ; jour de 8 h à 17 h 30 ; soir jusqu'à 20 h ; tombée de la nuit jusqu'à 22 h.
    function etatHeure(h) {
      if (h < 6 || h >= 22) return ['nuit', 'nuit', 0];
      if (h < 8) return ['nuit', 'jour', (h - 6) / 2];
      if (h < 17.5) return ['jour', 'jour', 0];
      if (h < 20) return ['jour', 'soir', (h - 17.5) / 2.5];
      return ['soir', 'nuit', (h - 20) / 2];
    }
    const MODES = ['auto', 'jour', 'soir', 'nuit'];
    let mode = 'auto';
    try { const m = localStorage.getItem('mcl-musee-lumiere'); if (MODES.includes(m)) mode = m; } catch (e) { /* stockage indisponible : mode auto */ }
    const bLum = $('#m3-lum');
    function eclairer() {
      const d = new Date(), h = d.getHours() + d.getMinutes() / 60;
      const [a, b, t] = mode === 'auto' ? etatHeure(h) : [mode, mode, 0];
      const A = AMB[a], B = AMB[b];
      ciel.intensity = mel(A.ciel, B.ciel, t); fond.intensity = mel(A.fond, B.fond, t); soleil.intensity = mel(A.soleil, B.soleil, t);
      ciel.color = melC(A.c, B.c, t);
      const fc = melC(A.fente, B.fente, t); plafonds.forEach((p) => p.material.color.copy(fc)); DALLE.color = melC(A.dalle, B.dalle, t);
      raies.forEach((r) => { r.material.opacity = mel(A.rais, B.rais, t); r.material.color = melC(A.raisC, B.raisC, t); r.visible = r.material.opacity > 0.01; });
      const vc = melC(A.vue, B.vue, t); vitres.forEach((m) => m.color.copy(vc));
      lumieresNuit.forEach((l) => { l.material.opacity = mel(A.halo, B.halo, t); l.visible = l.material.opacity > 0.01; });
      const bg = melC(A.bg, B.bg, t); scene.background = bg; scene.fog = new THREE.Fog(bg, 26, 70);
      bLum.textContent = T.lumiere[mode] + (mode === 'auto' ? ` (${String(d.getHours()).padStart(2, '0')} h ${String(d.getMinutes()).padStart(2, '0')})` : '');
    }
    bLum.onclick = () => { mode = MODES[(MODES.indexOf(mode) + 1) % MODES.length]; try { localStorage.setItem('mcl-musee-lumiere', mode); } catch (e) { /* rien */ } eclairer(); };
    eclairer();
    const minuteur = setInterval(eclairer, 60000);

    // ---------------------------------------------------------------- déplacement
    const joueur = { x: 0, z: -2.5, yaw: 0, pitch: -0.03 };
    const touches = {};
    function libre(x, zz) { const R = 0.32; return !obstacles.some((o) => x > o.x1 - R && x < o.x2 + R && zz > o.z1 - R && zz < o.z2 + R); }
    const clavier = (e, v) => {
      const k = { ArrowUp: 'av', KeyW: 'av', KeyZ: 'av', ArrowDown: 'ar', KeyS: 'ar', ArrowLeft: 'g', KeyA: 'g', KeyQ: 'g', ArrowRight: 'd', KeyD: 'd' }[e.code];
      if (k) { touches[k] = v; e.preventDefault(); }
      if (v && e.code === 'Escape') { if (!boiteCartel.hidden) boiteCartel.hidden = true; else fermer(); }
    };
    const kd = (e) => clavier(e, true), ku = (e) => clavier(e, false);
    window.addEventListener('keydown', kd); window.addEventListener('keyup', ku);
    boite.querySelectorAll('.m3-pave button').forEach((b) => {
      const k = b.dataset.k;
      b.addEventListener('pointerdown', (e) => { touches[k] = true; b.setPointerCapture(e.pointerId); });
      for (const ev of ['pointerup', 'pointercancel', 'lostpointercapture']) b.addEventListener(ev, () => { touches[k] = false; });
    });
    let glisse = null;
    const ray = new THREE.Raycaster();
    canvas.addEventListener('pointerdown', (e) => { glisse = { x: e.clientX, y: e.clientY, x0: e.clientX, y0: e.clientY }; canvas.setPointerCapture(e.pointerId); });
    canvas.addEventListener('pointermove', (e) => {
      if (!glisse) return;
      joueur.yaw -= (e.clientX - glisse.x) * 0.005; joueur.pitch = Math.max(-1.1, Math.min(1.1, joueur.pitch - (e.clientY - glisse.y) * 0.004));
      glisse.x = e.clientX; glisse.y = e.clientY;
    });
    canvas.addEventListener('pointerup', (e) => {
      if (glisse && Math.hypot(e.clientX - glisse.x0, e.clientY - glisse.y0) < 6) {
        const r = canvas.getBoundingClientRect();
        ray.setFromCamera({ x: ((e.clientX - r.left) / r.width) * 2 - 1, y: -((e.clientY - r.top) / r.height) * 2 + 1 }, camera);
        const t = ray.intersectObjects(cliquables, false).find((h) => h.distance < 14);
        if (t) montrer(t.object.userData.cartel); else boiteCartel.hidden = true;
      }
      glisse = null;
    });

    // Plan des salles : liste calculée, un toucher pour s'y rendre
    const liste = $('#m3-liste');
    liste.querySelector('ol').innerHTML = salles.map((s, i) => `<li><button type="button" data-i="${i}">${esc(s.nom)}</button></li>`).join('');
    liste.querySelectorAll('ol button').forEach((b) => { b.onclick = () => { const s = salles[+b.dataset.i]; joueur.x = s.x || 0; joueur.z = s.z; joueur.yaw = s.yaw || 0; joueur.pitch = -0.03; liste.hidden = true; }; });
    $('#m3-plan').onclick = () => { liste.hidden = !liste.hidden; };
    $('#m3-fplan').onclick = () => { liste.hidden = true; };
    $('#m3-sortir').onclick = fermer;
    const nomSalle = $('#m3-salle');

    function taille() { const w = boite.clientWidth, h = boite.clientHeight; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); }
    window.addEventListener('resize', taille); taille();

    // ---------------------------------------------------------------- changer d'échelle (idée de Bran, 2/11/2026)
    // Comme Elite (1984) recalculait ses galaxies à partir de quelques nombres, la galaxie est calculée à partir des
    // dessins publiés ce soir : un point par case, place fixée par le numéro du citoyen et sa région, aucun hasard.
    let univers = null, camU = null, echelle = null;
    const salleD = (M.plan || []).flatMap((a) => a.salles || []).filter((s) => s.type === 'dessins').pop();
    function construireUnivers() {
      const U = new THREE.Scene(); U.background = new THREE.Color(0x020306);
      const dessins = salleD ? salleD.dessins : [];
      const pos = [], col = [];
      dessins.forEach((d, i) => {
        const r = Math.floor(i / 20), k = i % 20;
        const rayon = 5 + k * 2.4, angle = r * Math.PI / 3 + k * 0.2;
        const cx = Math.cos(angle) * rayon, cz = Math.sin(angle) * rayon, cy = Math.sin(i * 1.7) * 0.8;
        for (let b = 0; b < d.length; b++) {
          const plein = d[b] === '1';
          pos.push(cx + ((b % 5) - 2) * 0.34, cy, cz + (Math.floor(b / 5) - 2) * 0.34);
          col.push(...(plein ? [0.72, 1, 0.82] : [0.16, 0.22, 0.27]));
        }
      });
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
      g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
      U.add(new THREE.Points(g, new THREE.PointsMaterial({ size: 0.22, vertexColors: true, sizeAttenuation: true })));
      // Au centre, la boîte en fil de fer (clin d'œil aux vaisseaux d'Elite) et ses 7 cartes
      const fil = new THREE.LineBasicMaterial({ color: 0x5fe08f });
      U.add(new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(0.6, 0.26, 0.4)), fil));
      for (let c = 0; c < 7; c++) { const e = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(0.05, 0.16, 0.3)), fil); e.position.set(-0.24 + c * 0.08, 0, 0); U.add(e); }
      camU = new THREE.PerspectiveCamera(60, camera.aspect, 0.02, 400);
      return U;
    }
    const boiteU = $('#m3-univers'), etape = $('#m3-etape');
    function changerEchelle() {
      if (!univers) univers = construireUnivers();
      const n = salleD ? salleD.dessins.reduce((t, d) => t + d.length, 0) : 0;
      $('#m3-vrai-u').textContent = salleD ? T.vrai_u(dateLongue(salleD.date)) : '';
      echelle = { t0: performance.now(), n, lent: window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches };
      boiteU.hidden = false; liste.hidden = true;
    }
    $('#m3-retour').onclick = () => { echelle = null; boiteU.hidden = true; };
    function dessinerUnivers(t) {
      const u = echelle.lent ? 1 : Math.min(1, (t - echelle.t0) / 9000);
      const e = u * u * (3 - 2 * u);
      const dist = 0.9 * Math.pow(80, e), ang = 0.6 + (t - echelle.t0) / 9000;
      camU.aspect = camera.aspect; camU.updateProjectionMatrix();
      camU.position.set(Math.sin(ang) * dist, dist * 0.45, Math.cos(ang) * dist); camU.lookAt(0, 0, 0);
      const txt = e < 0.25 ? T.etapes[0] : e < 0.75 ? T.etapes[1] : T.etapes[2](echelle.n);
      if (etape.textContent !== txt) etape.textContent = txt;
      renderer.render(univers, camU);
    }

    let avant = performance.now(), actif = true, derniere = '';
    function boucle(t) {
      if (!actif) return;
      if (echelle) { dessinerUnivers(t); requestAnimationFrame(boucle); return; }
      const dt = Math.min(0.05, (t - avant) / 1000); avant = t;
      if (touches.g) joueur.yaw += 1.8 * dt;
      if (touches.d) joueur.yaw -= 1.8 * dt;
      const v = (touches.av ? 1 : 0) - (touches.ar ? 1 : 0);
      if (v) {
        const nx = joueur.x - Math.sin(joueur.yaw) * v * 3.2 * dt, nz = joueur.z - Math.cos(joueur.yaw) * v * 3.2 * dt;
        if (libre(nx, joueur.z)) joueur.x = nx;
        if (libre(joueur.x, nz)) joueur.z = nz;
      }
      for (const g of tournants) g.rotation.y += 0.25 * dt;
      camera.position.set(joueur.x, 1.65, joueur.z);
      camera.rotation.set(joueur.pitch, joueur.yaw, 0, 'YXZ');
      const zoA = SG && joueur.x > W ? { nom: `${T.aile(aileCourante.ere)} · ${SG.titre[LG]}` } : null;
      const zo = zoA || zones.find((q) => joueur.z <= q.z1 && joueur.z > q.z2) || (joueur.x < -W ? { nom: (M.annexes[0] || {}).titre?.[LG] } : null);
      const nom = zo && zo.nom ? zo.nom : derniere;
      if (nom !== derniere) { nomSalle.textContent = nom; derniere = nom; }
      renderer.render(scene, camera);
      requestAnimationFrame(boucle);
    }
    requestAnimationFrame(boucle);

    window.MCL_MUSEE = {
      arreter() {
        actif = false; clearInterval(minuteur);
        window.removeEventListener('keydown', kd); window.removeEventListener('keyup', ku); window.removeEventListener('resize', taille);
        renderer.dispose();
      },
      // Pour les contrôles automatiques : plan calculé et obstacles
      controle: () => ({ zones: zones.map((q) => ({ ...q })), salles: salles.map((s) => ({ ...s })), cliquables: cliquables.length, lumiere: mode, fenetres: vitres.length }),
      aller: (i) => { const s = salles[i]; joueur.x = s.x || 0; joueur.z = s.z; joueur.yaw = s.yaw || 0; },
      echelle: () => changerEchelle(),
      regarder: (yaw, pitch = -0.03) => { joueur.yaw = yaw; joueur.pitch = pitch; },
      lumiere: (m) => { mode = m; eclairer(); },
      position: (x, zz) => { joueur.x = x; joueur.z = zz; },
    };
  }
})();
