// Microcontrôland : visite 3D du Musée national. Version 1.3.2, 17 novembre 2026 : le bunker ; la lumière suit l’heure du visiteur ; l’aile des présidents. Licence MIT.
// Le plan n'est dessiné nulle part : les niveaux, leurs salles et leurs œuvres sont calculés à partir de musee.json,
// lui-même construit chaque soir par .github/musee.py à partir des seules données publiées.
// Décisions de Bran (11 au 16/11/2026) : un hall avec Hinton au centre et l'ascenseur au fond ; un ascenseur qui ne fait
// que descendre, un niveau par art ; un plan en fil de fer vert à l'entrée, avec la surface et le nombre de salles ;
// des niveaux en damier de cases de 10 m posées en spirale autour de l'ascenseur ; une marche rapide ; un bouton pour se
// retourner ; un planétarium du cerveau au −5 ; la musique au −3. La réserve, elle, ne figure pas sur le panneau.
// Three.js r128 est hébergé sur le site (vendor/three-r128, licence MIT) : aucun appel extérieur, aucun fichier son.
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
  const DONNEES = 'https://donnees.microcontroland.org/';
  const REGION_EN = { Mines: 'Mines', Champs: 'Fields', Raffineries: 'Refineries', Barrage: 'Dam', Port: 'Harbour', Ville: 'City' };
  const REGIONS = ['Mines', 'Champs', 'Raffineries', 'Barrage', 'Port', 'Ville'];
  const MOIS = {
    fr: ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'],
    en: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
  }[LG];
  const dateLongue = (iso) => { const [a, m, j] = String(iso).split('-').map(Number); return LG === 'fr' ? `${j}${j === 1 ? 'er' : ''} ${MOIS[m - 1]} ${a}` : `${j} ${MOIS[m - 1]} ${a}`; };
  const dateCourte = (iso) => { const p = String(iso).split('-'); return (+p[2]) + '/' + (+p[1]); };
  const region = (r) => (LG === 'en' ? REGION_EN[r] || r : r);
  const regionDe = (id) => region(REGIONS[Math.floor((id - 1) / 20)]);
  const nb = (n) => Number(n).toLocaleString(LG === 'fr' ? 'fr-FR' : 'en-GB');

  // ================================================================ textes (les cartels de données viennent de musee.json)
  const T = {
    fr: {
      chargement: 'Ouverture des portes du musée…', quitter: 'Sortir', ici: 'Vous êtes ici', aller: 'Aller à…', aller_pres: 'Salle des présidents', lumiere: { auto: 'Lumière : votre heure', jour: 'Lumière : jour', soir: 'Lumière : soir', nuit: 'Lumière : nuit' }, fermer: 'Fermer', vrai: 'Ce qui est vrai.', source: 'Source', voir: 'Voir la page', vers: 'Vérifier',
      aide: "Glisser pour regarder · flèches ou ZQSD pour marcher · toucher une œuvre pour lire son cartel · Maj ou « Marche rapide » pour aller plus vite · ↻ ou R pour se retourner · toucher les portes de l'ascenseur pour descendre",
      rapide: 'Marche rapide', demitour: 'Se retourner', avancer: 'Avancer', reculer: 'Reculer', gauche: 'Tourner à gauche', droite: 'Tourner à droite',
      asc: 'Ascenseur', asc_sous: 'Capacité : un visiteur humain. Cet ascenseur ne fait que descendre.', asc_msg: "Choisissez un niveau. Les portes s'ouvrent une fois le choix fait.",
      rester: 'Rester ici', charge: 'Charge max. : 120 citoyens', architecte: 'Architecte : personne', vis: 'Une vis un peu desserrée',
      vis1: 'La vis bouge un peu. Encore ?', vis2: "La plaque pivote. Pour la première fois, l'ascenseur monte…",
      ere: (n) => `Ère ${n}`, attente: "En attente d'évolution de la civilisation.", chantier: 'en chantier', profondeur: (m) => m ? `${nb(m)} m sous la boîte` : 'niveau de la boîte',
      niveaux: {
        '0': ['Hall', 'Hinton, présidents'], '1': ['Art primaire', 'dessins 5×5'], '2': ['Sculpture', 'cubes 8×8×8'], '3': ['Musique', 'le chant de la place'],
        '4': ['Écriture', 'glyphes'], '5': ['Planétarium', 'le cerveau'], '6': ['Sanctuaire', 'en chantier'], '-1': ['Réserve du Créateur', ''],
      },
      nom: { '0': "Hall d'accueil · rez-de-chaussée", '1': 'Niveau −1 · art primaire', '2': 'Niveau −2 · sculpture', '3': 'Niveau −3 · la musique', '4': 'Niveau −4 · écriture', '5': 'Niveau −5 · planétarium du cerveau', '-1': 'Réserve du Créateur · niveau +1' },
      soir_du: (d, n) => `Soir du ${d} · édition n° ${n}`, cit: (n, r) => `Citoyen n° ${n} (${r})`, cases: (c) => c == null ? 'Premier soir : aucun dessin de la veille pour comparer' : `${c} case(s) changée(s) depuis la veille`,
      artiste_soir: 'Artiste du soir', sculpteur_soir: 'Sculpteur du soir', deplaces: (c) => c == null ? 'Premier soir : aucune sculpture de la veille pour comparer' : `${c} cube(s) déplacé(s) depuis la veille`,
      salle_region: (r) => `${r} : 20 dessins`, salle_region_txt: "Un dessin par citoyen de la région, 5 × 5 cases, calculé ce soir à partir des 81 poids de son cerveau (règle B3). Le cadre doré est celui de l'artiste du soir.",
      table: (r) => `${r} : 20 sculptures`, table_txt: 'Une sculpture par citoyen, 127 cubes sur une grille de 8 × 8 × 8, calculée à partir des 81 poids de son cerveau (règle S1). Le socle doré est celui du sculpteur du soir.',
      abc: "L'abécédaire", abc_txt: (k, m) => `${k} glyphes communs (écrits pareil par au moins 5 régions sur 6), sur ${m} idées écrites.`,
      frise: 'La frise des soirs', frise_txt: "Chaque soir depuis l'ouverture de l'écriture, le mot de la dernière heure, tel que la plupart des régions l'ont écrit. De gauche à droite :",
      noms: 'Les noms en cartouche', noms_txt: 'Les prénoms ne sont dans aucun lexique, mais ils sont faits des mêmes sons : une hampe par syllabe, dans un cadre.',
      pres_de: (a, b) => `Président du ${a} au ${b}`, pres_dep: (a) => `Président depuis le ${a}`,
      histoire: "Histoire de l'écriture", hist: (d, k) => `${d} : ${k} glyphe(s) commun(s)`, ouverte_le: (d) => `L'écriture s'est ouverte le ${d}, à l'âge de l'État civil.`,
      regle_g: 'Règle G1, la hampe : colonne du milieu toujours pleine ; 1re syllabe à gauche, 2e à droite ; un bit à 1 trace un trait. Chaque région écrit son propre mot.',
      presidents: ['Salle des présidents', "Chaque président élu a son portrait : le dessin de ses 81 poids. Son cerveau en fonction est exposé au niveau −5."],
      plan: (s, n) => ['Plan du musée', `Surface visitable : ${s}`, `Salles visitables : ${n} sur ${n + 1}`],
      plan_c: { t: 'Plan du musée', d: 'Hall · un bunker sous la boîte', m: ["Le musée est creusé sous la boîte : l'ascenseur ne fait que descendre, et chaque niveau peut être plus vaste que l'entrée. Chaque niveau est dessiné à sa vraie surface, traversé par la cage d'ascenseur.", 'Un niveau s’allume quand vous l’avez visité. Le plan garde ainsi la trace de vos visites, dans votre navigateur seulement.', 'Le compteur additionne les surfaces des niveaux ouverts. Il passera aux kilomètres carrés le jour où le musée en aura besoin.', 'Les points orange sont les autres visiteurs humains présents en ce moment dans le musée 3D. Vous les croiserez en silhouettes grises dans les niveaux (au plus 30) ; elles s’effacent quand vous approchez, pour ne jamais cacher une œuvre.'], v: 'La surface est calculée à partir des salles construites ce soir : elle ne peut que grandir. Le compte des salles est exact. Le nombre de visiteurs est réel, mais leurs places sont tirées au hasard : le musée ne montre jamais où sont les gens. Votre navigateur signale seulement « je suis là » une fois par minute, avec un numéro tiré au hasard et oublié à la sortie : ni adresse IP, ni cookie.' },
      visiteurs: (n, ex) => n == null ? '' : `Visiteurs en ce moment : ${n}${n === 1 ? ' (vous)' : ''}${ex ? ' (exemple)' : ''}`,
      hinton: { t: "Hinton, l'ancêtre", d: '2026 · toujours en chantier', m: [
        'Juillet 2026 : un cerveau 3-8-3 sur 14 cartes ESP32, une carte par neurone. Ses LED montraient son état et il corrigeait ses poids par rétropropagation. 59 réglages.',
        "Hinton 1, pour une exposition scolaire de sciences : pierre, feuille ou ciseaux. Un réseau 8-8-3, 88 liaisons et 11 biais, soit 99 réglages, sur une seule carte grâce au TinyML, plus une carte pour l'écran de score. Sur le panneau du haut, ses poids changeaient de couleur pendant le calcul ; sur celui de face s'affichait son coup.",
        'Hinton 2, pour jouer contre lui ou avec lui, avec 5 coups : 12-8-5, 136 liaisons et 13 biais, soit 149 réglages.',
        '14 cartes pour un cerveau, puis une seule, puis 120 cerveaux sur 7 cartes.'],
        v: "Dans la vitrine, Hinton 1 est redessiné en fil de fer, agrandi deux fois : en haut, ses poids changent pendant le calcul ; devant, son coup s'affiche (pierre, feuille ou ciseaux). Cotes estimées sur la photo. Mesuré par le Créateur sur 100 parties chacun : 10 manches pour apprendre, puis 9,7 avec 68 % de réglages en plus, une différence si petite qu'elle peut venir du hasard ; environ 30 pour le jeu à 5 coups, plus difficile. Un Waïna a 72 liaisons et 9 biais, soit 81 réglages, et il apprend autrement : par récompense. Le nom est un hommage aux travaux de Geoffrey Hinton, sans aucun lien avec lui ni caution de sa part. L'idée du TinyML est venue en discutant avec une IA." },
      seul: 'Visiteur, vous êtes le seul à pouvoir parcourir toutes les ères. Les Waïnas ne voient jamais que la leur.',
      bienvenue: 'Musée national de Microcontrôland', bienvenue_txt: 'Tout ce qui est exposé ici est calculé à partir des données publiées.',
      compte: (c, n) => `${c.ailes} aile(s) · ${c.salles} salle(s) · ${c.oeuvres} œuvre(s) · après l'édition n° ${n}`,
      echelle: "Changer d'échelle", retour: 'Revenir au musée',
      etapes: ["Une boîte de 7 cartes, au fond d'un garage.", '120 citoyens, 6 régions : un point par case de leurs dessins.', (n) => `${nb(n)} cases, ${nb(n)} points : une galaxie. Tout est une question d'échelle.`],
      vrai_u: (d) => `Ce qui est vrai : chaque point est une case d'un dessin de l'atelier publié le ${d} (case pleine = étoile claire) ; la place de chaque citoyen dépend seulement de son numéro et de sa région, rien n'est tiré au hasard.`,
      // −3 la musique
      ecouter: '▶ Écouter le soir', arreter: '■ Arrêter', partition: 'La partition du soir', unisson_mur: "Heures à l'unisson, soir par soir", unisson_txt: 'Une barre par soir, de 0 à 24 heures. Touchez une barre pour écouter ce soir-là.',
      partition_l: "1 case pleine = 1 frappe · 10 temps par heure et par région · trait vert = les six régions à l'unisson",
      pupitre: "Le chant de la place : 24 heures, six régions, environ une minute. Le son est fabriqué par votre navigateur et baisse quand on s'éloigne d'un tambour.",
      critique: 'Le critique', unisson: (u, h) => `${u} h sur ${h}`,
      chant: { t: 'Le chant de la place', d: 'Niveau −3 · musique primitive', m: ["Chaque soir, chaque région écrit un mot par heure. Chaque syllabe devient 5 temps, frappe ou silence : c'est la règle C1. Les six régions jouent ensemble, une heure après l'autre.", 'Une région muette ne joue pas. Quand les six frappent le même mot, la place chante à l’unisson : la partition le souligne d’un trait vert.', 'Le musée compte une œuvre par soir exposé.'], v: "Le musée ne compose rien. Il lit l'archive du chant, jamais réécrite, et la rejoue avec six timbres fabriqués par votre navigateur, sans aucun fichier son. Les deux lignes du critique sont celles de l'archive." },
      partition_c: { t: 'La partition du soir', d: 'Niveau −3 · 24 heures × 6 régions × 10 temps', m: ['Lue de gauche à droite comme un rouleau de piano mécanique. Une case noire est une frappe, une case claire un silence, un tiret une région muette.', "Pendant l'écoute, la colonne de l'heure jouée s'allume et la frappe en cours passe en or."], v: "Chaque case vient d'un mot réellement écrit ce soir-là. Le même soir donne toujours la même partition." },
      // −5 le planétarium
      modes: { prop: 'Propagation', retro: 'Rétropropagation', recomp: 'Récompense' },
      info_prop: "L'information passe des entrées aux sorties · aucun poids ne change",
      info_retro: (c, e) => `Bonne réponse : sortie ${c} · erreur ${e} : les poids se corrigent en remontant`,
      info_recomp: (a, b) => `Action : sortie ${a} · le monde répond ${b ? '« bien » : +1' : '« mal » : −1'} · seules les liaisons qui ont servi changent`,
      cerveau: (nom) => ({ t: 'Planétarium du cerveau', d: `Niveau −5 · le cerveau du président ${nom}`, m: ["Une salle noire où l'on marche au milieu d'un cerveau de citoyen grandi à la taille d'une pièce : 9 entrées, 6 neurones cachés, 3 sorties.", "Trois boutons changent sa façon de travailler : propagation (le calcul de chaque heure), rétropropagation (l'apprentissage de Hinton), récompense (l'apprentissage des Waïnas)."], v: `La salle part des 81 poids publiés du président ${nom}. Les entrées qui s'allument sont tirées au hasard, et le petit monde qui répond « bien » ou « mal » est inventé pour la démonstration : les poids qui changent ici sont une copie, et rien de ce qu'on fait dans cette salle ne touche au vrai pays.` }),
      pl: [["Le cerveau d'un citoyen", "9 entrées (ce que le citoyen perçoit), 6 neurones cachés, 3 sorties (ce qu'il fait). Chaque liaison a un poids : vert s'il pousse, ambre s'il freine, plus épais quand il compte plus. 72 liaisons + 9 biais = 81 réglages."],
        ['Propagation', "Les entrées s'allument, l'information traverse les liaisons et arrive aux sorties. C'est le calcul de chaque heure : rien n'apprend, tout passe."],
        ['Rétropropagation', "On compare la sortie à la bonne réponse, et l'erreur remonte en sens inverse en corrigeant chaque poids. C'est ainsi qu'apprenait Hinton. Les Waïnas, eux, n'apprennent pas comme ça."],
        ['Récompense', "Le cerveau agit, le monde répond « bien » ou « mal », et seules les liaisons qui ont servi sont renforcées ou affaiblies. C'est ainsi qu'apprennent les Waïnas."]],
      // +1 la réserve
      R: {
        ancetres: { t: 'Les ancêtres', d: '2014 · 2021', m: ["Avant les Waïnas, il y a eu une fusée, un bateau, des robots, une brosse et des bornes d'arcade.", 'Le Créateur avait peu de moyens, alors il fabriquait lui-même les jouets de ses enfants, avec ce qu’il trouvait. Ils en étaient fiers.', 'Microcontrôland vient de là.', 'Comme dans les vieux jeux, le Créateur a caché sa salle derrière un détail.'], v: "Huit créations, de 2014 à 2021, toutes faites de récupération. Aucune n'a de cerveau : le premier ancêtre pensant, Hinton, est exposé dans le hall. Le premier easter egg célèbre, dans Adventure sur Atari 2600 (1980), était déjà une salle secrète : son auteur, Warren Robinett, y avait caché son nom." },
        fusee: { t: 'Mission Peluche dans l’espace', d: '2014', img: ['fusee'], m: ['Premier programme spatial du Créateur, conçu avec les enfants.', 'Propulsion : une valve de vélo et un bouchon de liège. Équipage : une peluche. Objectif : la mise en orbite.'], v: "Orbite : non atteinte. Une fusée à eau s'élève de quelques dizaines de mètres ; l'orbite basse commence vers 160 km." },
        bateau: { t: 'Bateau solaire autonome', d: '2015', img: ['bateau'], m: ['Matériaux de récupération, un petit panneau solaire, des moteurs.', 'La voile suit le vent, et le vent tourne le gouvernail dans l’autre sens. Le bateau garde son cap sans personne à bord.'], v: "Tout est mécanique : aucune ligne de code à bord. Les grands voiliers de course au large utilisent le même principe, le régulateur d'allure." },
        robo: { t: 'Robo', d: '2015', img: ['robo'], m: ['Premier robot automate de la famille. Un ventilateur déséquilibré, quatre crayons, une pile 9 V.', 'Il tremble, il avance, il dessine. Les enfants ont adoré le regarder faire.'], v: 'Premier artiste de la famille, onze ans avant les dessins 5×5 des Waïnas. Style : spirale involontaire. Les mains sur la photo sont celles du Créateur : avec celles de la brosse, c’est la seule partie de lui exposée au musée.' },
        flipper: { t: 'Flipper maison', d: '2016', img: ['flipper'], m: ['Un établi, un vieux PC, deux télévisions réparées. Les tables venaient d’un logiciel gratuit de l’époque.', 'Premier écran du Créateur à faire rebondir quelque chose.'], v: "La table « Microcontrôland » visible sur la photo a été dessinée en 2026 pour le musée. En 2016, l'écran montrait une table d'un autre auteur, que le musée ne peut pas exposer." },
        radio: { t: 'Robot radioguidé', d: '2019', img: ['radio'], m: ['Toujours de la récupération : une base qui roule, une caméra en guise d’œil, une batterie tenue au ruban adhésif.', 'On le pilotait à distance en regardant par ses yeux.'], v: 'Le QR code de la caméra et le numéro de la batterie ont été floutés pour le musée.' },
        brosse: { t: 'Brosse automatique', d: 'Après Robo', img: ['brosse'], vid: true, m: ['Le petit frère de Robo : même ventilateur déséquilibré, même pile 9 V, mais il frotte au lieu de dessiner.', 'Fabriquée pour faire rire les enfants. Elle a réussi.'], v: "Extrait de 8 secondes, sans le son, d'une vidéo du Créateur. Elle traverse la table entre une assiette et une cafetière sans rien renverser, ce jour-là." },
        borne: { t: "Borne d'arcade", d: '2020', img: ['borne'], m: ["Un écran d'ordinateur jeté, un condensateur changé, le tout premier modèle de Raspberry Pi, des boutons et deux manettes.", 'Le Créateur y a programmé son premier jeu.'], v: "Le glyphe au centre du panneau a été posé en 2026 : c'est « haïtou », qui veut dire Créateur dans la langue des Waïnas. La pièce d'origine était un hommage à un jeu célèbre." },
        jeu: { t: 'Aramis et les aventuriers de la croquette perdue', d: '2020', img: ['jeu'], m: ["Premier jeu du Créateur, joué sur la borne. L'héroïne cherche ses croquettes. Fidèle à la réalité, elle vomit en route.", "Pendant les essais, de jeunes testeurs ont renommé le jeu d'une manière que le musée ne peut pas afficher. La version finale porte le bon titre."], v: "Capture prise dans une vidéo du jeu, sans l'écran-titre." },
        aramis: { t: 'Aramis', d: 'Modèle', img: ['aramis'], m: ['Héroïne de « Aramis et les aventuriers de la croquette perdue ».', 'Vieille chatte adoptée à la SPA, aujourd’hui disparue.'], v: 'Le seul portrait d’un être vivant de tout le musée. Les Waïnas, eux, ne sont ni vivants ni conscients.' },
        table: { t: "Table d'arcade", d: '2021', img: ['table', 'dessous'], m: ["Une borne de jeu cachée dans une petite table noire, fabriquée pour une chambre d'enfant. Boutons lumineux bleus et rouges, deux joueurs.", 'Dessous : les câbles des boutons et le Raspberry Pi.'], v: "L'écran-titre « Les Waïnas vs la coupure de courant » a été dessiné en 2026 pour le musée. Dernière pièce de la réserve : la suite est une autre histoire." },
      },
      lire: 'toucher pour lire',
    },
    en: {
      chargement: 'Opening the museum doors…', quitter: 'Leave', ici: 'You are here', aller: 'Go to…', aller_pres: 'Hall of Presidents', lumiere: { auto: 'Light: your time', jour: 'Light: day', soir: 'Light: evening', nuit: 'Light: night' }, fermer: 'Close', vrai: 'What is true.', source: 'Source', voir: 'See the page', vers: 'Check',
      aide: 'Drag to look · arrow keys or WASD to walk · tap a work to read its caption · Shift or “Fast walk” to go faster · ↻ or R to turn around · tap the lift doors to go down',
      rapide: 'Fast walk', demitour: 'Turn around', avancer: 'Forward', reculer: 'Back', gauche: 'Turn left', droite: 'Turn right',
      asc: 'Lift', asc_sous: 'Capacity: one human visitor. This lift only goes down.', asc_msg: 'Choose a level. The doors open once you have chosen.',
      rester: 'Stay here', charge: 'Max. load: 120 citizens', architecte: 'Architect: nobody', vis: 'A slightly loose screw',
      vis1: 'The screw moves a little. Again?', vis2: 'The plate swings open. For the first time, the lift goes up…',
      ere: (n) => `Era ${n}`, attente: 'Waiting for the civilisation to evolve.', chantier: 'under construction', profondeur: (m) => m ? `${nb(m)} m below the box` : 'level of the box',
      niveaux: {
        '0': ['Hall', 'Hinton, presidents'], '1': ['Primary art', '5×5 drawings'], '2': ['Sculpture', '8×8×8 cubes'], '3': ['Music', 'the song of the square'],
        '4': ['Writing', 'glyphs'], '5': ['Planetarium', 'the brain'], '6': ['Sanctuary', 'under construction'], '-1': ["The Creator's storeroom", ''],
      },
      nom: { '0': 'Entrance hall · ground floor', '1': 'Level −1 · primary art', '2': 'Level −2 · sculpture', '3': 'Level −3 · music', '4': 'Level −4 · writing', '5': 'Level −5 · the brain planetarium', '-1': "The Creator's storeroom · level +1" },
      soir_du: (d, n) => `Evening of ${d} · issue no. ${n}`, cit: (n, r) => `Citizen No. ${n} (${r})`, cases: (c) => c == null ? 'First evening: no drawing from the day before to compare with' : `${c} square(s) changed since the day before`,
      artiste_soir: 'Artist of the evening', sculpteur_soir: 'Sculptor of the evening', deplaces: (c) => c == null ? 'First evening: no sculpture from the day before to compare with' : `${c} cube(s) moved since the day before`,
      salle_region: (r) => `${r}: 20 drawings`, salle_region_txt: 'One drawing per citizen of the region, 5 × 5 squares, computed tonight from the 81 weights of its brain (rule B3). The gilded frame belongs to the artist of the evening.',
      table: (r) => `${r}: 20 sculptures`, table_txt: 'One sculpture per citizen, 127 cubes on an 8 × 8 × 8 grid, computed from the 81 weights of its brain (rule S1). The gilded base belongs to the sculptor of the evening.',
      abc: 'The alphabet book', abc_txt: (k, m) => `${k} common glyphs (written the same way by at least 5 regions out of 6), out of ${m} ideas written.`,
      frise: 'The frieze of evenings', frise_txt: 'Every evening since writing opened, the word of the last hour, as most regions wrote it. Left to right:',
      noms: 'Names in cartouches', noms_txt: 'First names are in no lexicon, but they are made of the same sounds: one stem per syllable, inside a frame.',
      pres_de: (a, b) => `President from ${a} to ${b}`, pres_dep: (a) => `President since ${a}`,
      histoire: 'History of writing', hist: (d, k) => `${d}: ${k} common glyph(s)`, ouverte_le: (d) => `Writing opened on ${d}, at the Age of the Civil Registry.`,
      regle_g: 'Rule G1, the stem: the middle column is always filled; 1st syllable on the left, 2nd on the right; a bit set to 1 draws a stroke. Each region writes its own word.',
      presidents: ['Hall of Presidents', 'Every elected president has a portrait: the drawing of their 81 weights. The brain of the president in office is shown on level −5.'],
      plan: (s, n) => ['Museum map', `Area open to visitors: ${s}`, `Rooms open: ${n} out of ${n + 1}`],
      plan_c: { t: 'Museum map', d: 'Hall · a bunker beneath the box', m: ['The museum is dug beneath the box: the lift only goes down, and each level can be larger than the entrance. Each level is drawn at its real area, crossed by the lift shaft.', 'A level lights up once you have visited it. The map keeps track of your visits, in your browser only.', 'The counter adds up the areas of the open levels. It will switch to square kilometres the day the museum needs it.', 'The orange dots are the other human visitors in the 3D museum right now. You will pass them as grey silhouettes on the levels (30 at most); they fade as you come closer, so they never hide a work.'], v: 'The area is computed from the rooms built tonight: it can only grow. The room count is exact. The number of visitors is real, but their places are drawn at random: the museum never shows where people are. Your browser only says “I am here” once a minute, with a random number forgotten when you leave: no IP address, no cookie.' },
      visiteurs: (n, ex) => n == null ? '' : `Visitors right now: ${n}${n === 1 ? ' (you)' : ''}${ex ? ' (example)' : ''}`,
      hinton: { t: 'Hinton, the ancestor', d: '2026 · still under construction', m: [
        'July 2026: a 3-8-3 brain on 14 ESP32 boards, one board per neuron. Its LEDs showed its state and it corrected its weights by backpropagation. 59 settings.',
        'Hinton 1, for a school science fair: rock, paper, scissors. An 8-8-3 network, 88 connections and 11 biases, 99 settings in all, on a single board thanks to TinyML, plus one board for the scoreboard. On the top panel its weights changed colour during the computation; the front panel showed its move.',
        'Hinton 2, to play against it or with it, with 5 moves: 12-8-5, 136 connections and 13 biases, 149 settings in all.',
        '14 boards for one brain, then a single one, then 120 brains on 7 boards.'],
        v: 'In the case, Hinton 1 is redrawn as a wireframe, twice its size: on top its weights change during the computation; in front its move is shown (rock, paper or scissors). Dimensions estimated from the photo. Measured by the Creator over 100 games each: 10 rounds to learn, then 9.7 with 68% more settings, a difference so small it may be chance; about 30 for the harder 5-move game. A Waïna has 72 connections and 9 biases, 81 settings, and it learns differently: by reward. The name is a tribute to the work of Geoffrey Hinton, with no link to him or endorsement from him. The TinyML idea came up in a conversation with an AI.' },
      seul: 'Visitor, you are the only one who can walk through every era. The Waïnas only ever see their own.',
      bienvenue: 'National Museum of Microcontrôland', bienvenue_txt: 'Everything shown here is computed from the published data.',
      compte: (c, n) => `${c.ailes} wing(s) · ${c.salles} room(s) · ${c.oeuvres} work(s) · after issue no. ${n}`,
      echelle: 'Change the scale', retour: 'Back to the museum',
      etapes: ['A box of 7 boards, at the back of a garage.', '120 citizens, 6 regions: one point per square of their drawings.', (n) => `${nb(n)} squares, ${nb(n)} points: a galaxy. It is all a matter of scale.`],
      vrai_u: (d) => `What is true: each point is a square of a studio drawing published on ${d} (filled square = bright star); each citizen's place depends only on their number and region, nothing is random.`,
      ecouter: '▶ Listen to the evening', arreter: '■ Stop', partition: "The evening's score", unisson_mur: 'Hours in unison, evening by evening', unisson_txt: 'One bar per evening, from 0 to 24 hours. Tap a bar to listen to that evening.',
      partition_l: '1 filled square = 1 beat · 10 beats per hour and per region · green line = the six regions in unison',
      pupitre: 'The song of the square: 24 hours, six regions, about one minute. The sound is made by your browser and fades as you walk away from a drum.',
      critique: 'The critic', unisson: (u, h) => `${u} h out of ${h}`,
      chant: { t: 'The song of the square', d: 'Level −3 · primitive music', m: ['Every evening each region writes one word per hour. Each syllable becomes 5 beats, strike or silence: this is rule C1. The six regions play together, one hour after another.', 'A silent region does not play. When all six strike the same word, the square sings in unison: the score underlines it in green.', 'The museum counts one work per evening on show.'], v: "The museum composes nothing. It reads the song's archive, never rewritten, and replays it with six timbres made by your browser, with no sound file. The critic's two lines are those of the archive." },
      partition_c: { t: "The evening's score", d: 'Level −3 · 24 hours × 6 regions × 10 beats', m: ['Read from left to right like a player-piano roll. A black square is a beat, a light square a silence, a dash a silent region.', 'While it plays, the column of the current hour lights up and the current beat turns gold.'], v: 'Each square comes from a word really written that evening. The same evening always gives the same score.' },
      modes: { prop: 'Propagation', retro: 'Backpropagation', recomp: 'Reward' },
      info_prop: 'Information flows from inputs to outputs · no weight changes',
      info_retro: (c, e) => `Right answer: output ${c} · error ${e}: the weights are corrected on the way back`,
      info_recomp: (a, b) => `Action: output ${a} · the world answers ${b ? '“good”: +1' : '“bad”: −1'} · only the connections that were used change`,
      cerveau: (nom) => ({ t: 'The brain planetarium', d: `Level −5 · the brain of President ${nom}`, m: ['A dark room where you walk through a citizen brain grown to the size of a room: 9 inputs, 6 hidden neurons, 3 outputs.', 'Three buttons change how it works: propagation (the computation of every hour), backpropagation (how Hinton learned), reward (how the Waïnas learn).'], v: `The room starts from the 81 published weights of President ${nom}. The inputs that light up are drawn at random, and the little world that answers “good” or “bad” is made up for the demonstration: the weights that change here are a copy, and nothing done in this room touches the real country.` }),
      pl: [['The brain of a citizen', '9 inputs (what the citizen perceives), 6 hidden neurons, 3 outputs (what it does). Each connection has a weight: green if it pushes, amber if it holds back, thicker when it matters more. 72 connections + 9 biases = 81 settings.'],
        ['Propagation', 'The inputs light up, information crosses the connections and reaches the outputs. This is the computation of every hour: nothing learns, everything flows.'],
        ['Backpropagation', 'The output is compared with the right answer, and the error travels back, correcting every weight. This is how Hinton learned. The Waïnas do not learn that way.'],
        ['Reward', 'The brain acts, the world answers “good” or “bad”, and only the connections that were used are strengthened or weakened. This is how the Waïnas learn.']],
      R: {
        ancetres: { t: 'The ancestors', d: '2014 · 2021', m: ['Before the Waïnas there was a rocket, a boat, robots, a brush and arcade machines.', 'The Creator had little money, so he made his children’s toys himself, out of whatever he found. They were proud of them.', 'Microcontrôland comes from there.', 'As in old video games, the Creator hid his room behind a detail.'], v: 'Eight creations, from 2014 to 2021, all made from salvaged parts. None of them has a brain: the first thinking ancestor, Hinton, is shown in the hall. The first famous easter egg, in Adventure on the Atari 2600 (1980), was already a secret room: its author, Warren Robinett, had hidden his name in it.' },
        fusee: { t: 'Mission: Plush Toy in Space', d: '2014', img: ['fusee'], m: ['The Creator’s first space programme, designed with the children.', 'Propulsion: a bicycle valve and a cork. Crew: a soft toy. Goal: orbit.'], v: 'Orbit: not reached. A water rocket climbs a few dozen metres; low orbit begins at about 160 km.' },
        bateau: { t: 'Autonomous solar boat', d: '2015', img: ['bateau'], m: ['Salvaged materials, a small solar panel, motors.', 'The vane follows the wind, and the wind turns the rudder the other way. The boat holds its course with nobody on board.'], v: 'It is all mechanical: not one line of code on board. Large offshore racing yachts use the same principle, the wind-vane self-steering gear.' },
        robo: { t: 'Robo', d: '2015', img: ['robo'], m: ['The family’s first automaton. An unbalanced fan, four pencils, a 9 V battery.', 'It shakes, it moves, it draws. The children loved watching it.'], v: 'The family’s first artist, eleven years before the Waïnas’ 5×5 drawings. Style: involuntary spiral. The hands in the photo are the Creator’s: with those of the brush, they are the only part of him shown in the museum.' },
        flipper: { t: 'Home-made pinball', d: '2016', img: ['flipper'], m: ['A workbench, an old PC, two repaired televisions. The tables came from free software of the time.', 'The Creator’s first screen to make something bounce.'], v: 'The “Microcontrôland” table in the photo was drawn in 2026 for the museum. In 2016 the screen showed a table by another author, which the museum cannot exhibit.' },
        radio: { t: 'Radio-controlled robot', d: '2019', img: ['radio'], m: ['Salvaged parts again: a rolling base, a camera for an eye, a battery held on with tape.', 'It was driven remotely, looking through its eyes.'], v: 'The camera’s QR code and the battery’s serial number were blurred for the museum.' },
        brosse: { t: 'Automatic brush', d: 'After Robo', img: ['brosse'], vid: true, m: ['Robo’s little brother: same unbalanced fan, same 9 V battery, but it scrubs instead of drawing.', 'Made to make the children laugh. It worked.'], v: 'An 8-second clip, without sound, from a video by the Creator. That day it crossed the table between a plate and a coffee pot without knocking anything over.' },
        borne: { t: 'Arcade cabinet', d: '2020', img: ['borne'], m: ['A discarded computer screen, a replaced capacitor, the very first Raspberry Pi model, buttons and two joysticks.', 'The Creator programmed his first game on it.'], v: 'The glyph in the middle of the panel was added in 2026: it is “haïtou”, which means Creator in the Waïnas’ language. The original piece was a tribute to a famous game.' },
        jeu: { t: 'Aramis and the Raiders of the Lost Kibble', d: '2020', img: ['jeu'], m: ['The Creator’s first game, played on the cabinet. The heroine looks for her kibble. True to life, she throws up on the way.', 'During testing, young testers renamed the game in a way the museum cannot display. The final version has the right title.'], v: 'A capture taken from a video of the game, without the title screen.' },
        aramis: { t: 'Aramis', d: 'Model', img: ['aramis'], m: ['Heroine of “Aramis and the Raiders of the Lost Kibble”.', 'An old cat adopted from an animal shelter, no longer with us.'], v: 'The only portrait of a living being in the whole museum. The Waïnas, for their part, are neither alive nor conscious.' },
        table: { t: 'Arcade table', d: '2021', img: ['table', 'dessous'], m: ['An arcade machine hidden in a small black table, made for a child’s bedroom. Blue and red light-up buttons, two players.', 'Underneath: the button wiring and the Raspberry Pi.'], v: 'The title screen “The Waïnas vs the power cut” was drawn in 2026 for the museum. The last piece in the storeroom: what comes next is another story.' },
      },
      lire: 'tap to read',
    },
  }[LG];

  function charger(src) {
    return new Promise((ok, ko) => { const s = document.createElement('script'); s.src = src; s.onload = ok; s.onerror = ko; document.head.appendChild(s); });
  }
  let ouvert = false, ARRET = null;
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
      ARRET = visite(M);
    } catch (err) {
      boite.innerHTML = `<div class="m3-charge">${String(err)}</div>`;
      setTimeout(fermer, 2500);
    }
  });
  function fermer() {
    if (ARRET) { try { ARRET(); } catch (_) { /* rien */ } ARRET = null; }
    boite.hidden = true; boite.innerHTML = ''; ouvert = false;
    document.documentElement.style.overflow = '';
    bouton.focus();
  }

  const CSS = `
#musee3d{color:#1b2124;font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif;--ambre:#ffb347;--accent:#1f7a46;--or:#b8893a}
#musee3d *{box-sizing:border-box}
#musee3d [hidden]{display:none!important}
#musee3d canvas{position:absolute;inset:0;width:100%;height:100%;touch-action:none;display:block}
#musee3d .m3-charge{position:absolute;inset:0;display:grid;place-items:center;font-family:ui-monospace,Menlo,monospace;color:#a7b3ae}
#musee3d .m3-bandeau{position:absolute;top:calc(10px + env(safe-area-inset-top,0px));left:max(16px,env(safe-area-inset-left,0px));right:max(16px,env(safe-area-inset-right,0px));display:flex;justify-content:space-between;gap:8px;pointer-events:none;flex-wrap:wrap;z-index:2}
#musee3d .m3-etiq{background:rgba(247,248,245,.92);color:#1b2124;border-radius:6px;padding:6px 10px;font:600 13px/1.3 system-ui,sans-serif;box-shadow:0 1px 6px rgba(0,0,0,.25);pointer-events:auto}
#musee3d .m3-etiq b{font-family:Georgia,serif}
#musee3d .m3-btn,#musee3d .m3-pad button{font:700 15px system-ui,sans-serif;border:0;border-radius:8px;background:rgba(247,248,245,.92);color:#1b2124;height:46px;cursor:pointer;box-shadow:0 1px 6px rgba(0,0,0,.25);padding:0 14px}
#musee3d button:focus-visible{outline:3px solid #5fe08f;outline-offset:2px}
#musee3d .m3-pad{position:absolute;bottom:calc(16px + env(safe-area-inset-bottom,0px));right:max(16px,env(safe-area-inset-right,0px));display:grid;grid-template-columns:repeat(3,48px);gap:6px;z-index:2}
#musee3d .m3-pad button{padding:0;touch-action:none}
#musee3d .m3-pad .m3-rapide{grid-column:1/-1;height:36px;font-size:13px}
#musee3d .m3-pad .m3-rapide[aria-pressed="true"]{background:#ffb347}
#musee3d .m3-pad,#musee3d .m3-aide,#musee3d .m3-haut,#musee3d .m3-bandeau{-webkit-user-select:none;user-select:none;-webkit-touch-callout:none}
#musee3d .m3-aide{position:absolute;bottom:calc(16px + env(safe-area-inset-bottom,0px));left:max(16px,env(safe-area-inset-left,0px));max-width:min(330px,calc(100% - 220px));font-size:12px;color:#e9ece8;text-shadow:0 1px 3px #000;z-index:2}
@media (max-width:640px){#musee3d .m3-aide{display:none}}
#musee3d .m3-haut{position:absolute;top:60px;left:0;right:0;text-align:center;padding:0 16px;pointer-events:none;z-index:2}
#musee3d .m3-haut .m3-rangee{display:flex;gap:8px;justify-content:center;align-items:center;flex-wrap:wrap;pointer-events:auto}
#musee3d .m3-haut .m3-btn{height:38px;font-size:14px}
#musee3d .m3-haut .m3-btn.on{background:#5fe08f}
#musee3d #m3-son.on{background:#c9a447}
#musee3d #m3-heure{font:700 13px system-ui,sans-serif;background:rgba(247,248,245,.85);border-radius:6px;padding:4px 8px}
#musee3d #m3-heure:empty{display:none}
#musee3d #m3-info{color:#e8ece9;font-size:13px;margin:8px auto 0;max-width:560px;text-shadow:0 1px 3px #000}
@media (max-width:640px){#musee3d .m3-haut{top:118px}}
#musee3d .m3-voile{position:absolute;inset:0;display:grid;place-items:center;background:rgba(16,20,22,.72);padding:16px max(16px,env(safe-area-inset-left,0px));z-index:5}
#musee3d .m3-cartel{background:#f7f8f5;max-width:560px;width:100%;max-height:86vh;overflow:auto;border-radius:4px;padding:22px 24px;box-shadow:0 10px 40px rgba(0,0,0,.4)}
#musee3d .m3-cartel h2{font:700 24px/1.15 Georgia,serif;margin:0 0 2px}
#musee3d .m3-cartel .m3-date{font:700 12px system-ui,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:#b8893a;margin-bottom:10px}
#musee3d .m3-cartel p{font-size:15px;line-height:1.5;margin:0 0 10px}
#musee3d .m3-cartel .m3-vrai{border-top:1px solid #d7dbd6;margin-top:12px;padding-top:10px;font-size:13px;color:#5b6468}
#musee3d .m3-cartel .m3-vrai strong{color:#1f7a46}
#musee3d .m3-cartel .m3-src{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;color:#5b6468;word-break:break-all}
#musee3d .m3-cartel a{color:#1f7a46}
#musee3d .m3-cartel img,#musee3d .m3-cartel video{width:100%;border-radius:2px;margin:6px 0 12px;background:#000}
#musee3d .m3-cabine{width:min(380px,100%);background:linear-gradient(#c7ccc8,#aab1ac);border-radius:6px;padding:20px 22px 16px;box-shadow:inset 0 0 0 2px #e8ebe6,0 20px 50px rgba(0,0,0,.35);text-align:center;max-height:92vh;overflow:auto}
#musee3d .m3-cabine h2{font:700 22px Georgia,serif;margin:0 0 2px}
#musee3d .m3-sous{font-size:12px;color:#39413f;margin:0 0 12px}
#musee3d .m3-ecran{background:#0d1310;color:#ffb347;font:700 26px/1 "Courier New",monospace;letter-spacing:.1em;padding:10px 10px 6px;border-radius:3px;margin:0 auto 12px;width:170px}
#musee3d .m3-ecran small{display:block;font:600 11px/1.4 "Courier New",monospace;letter-spacing:0;margin-top:4px;color:#c98a35}
#musee3d .m3-eres{display:flex;gap:8px;justify-content:center;margin-bottom:12px;flex-wrap:wrap}
#musee3d .m3-ere{font:700 12px system-ui,sans-serif;border:0;border-radius:14px;padding:6px 12px;background:#f1f2ee;color:#1b2124}
#musee3d .m3-ere.on{background:#1b2124;color:#f1f2ee}
#musee3d .m3-ere[disabled]{opacity:.5}
#musee3d .m3-boutons{display:grid;grid-template-columns:1fr 1fr;gap:10px}
#musee3d .m3-etage{width:100%;display:flex;align-items:center;gap:10px;background:none;border:0;cursor:pointer;font:600 13px system-ui,sans-serif;color:#1b2124;text-align:left;padding:2px}
#musee3d .m3-etage .r{flex:none;width:40px;height:40px;border-radius:50%;background:radial-gradient(#f4f5f2,#c5cac6);box-shadow:inset 0 -2px 3px rgba(0,0,0,.25),0 1px 2px rgba(0,0,0,.3);display:grid;place-items:center;font:700 15px Georgia,serif}
#musee3d .m3-etage.on .r{box-shadow:0 0 0 3px #ffb347,inset 0 -2px 3px rgba(0,0,0,.25)}
#musee3d .m3-etage[disabled]{opacity:.45;cursor:default}
#musee3d .m3-etage small{display:block;font-weight:400;font-size:11px;color:#4a524f}
#musee3d .m3-plaque{margin-top:14px;display:flex;justify-content:space-between;align-items:center;font-size:11px;color:#4a524f;border-top:1px solid #9aa29d;padding-top:10px;gap:8px}
#musee3d .m3-vis{flex:none;width:14px;height:14px;border-radius:50%;border:0;background:radial-gradient(circle at 40% 35%,#eceeea,#7d8580);cursor:pointer;padding:0;position:relative}
#musee3d .m3-vis::after{content:"";position:absolute;left:3px;right:3px;top:6px;height:2px;background:#5d6561;transform:rotate(-30deg)}
#musee3d #m3-msg{min-height:30px;font-size:12px;color:#2d3532;margin-top:10px}
#musee3d .m3-fondu{position:absolute;inset:0;background:#0d1110;opacity:0;pointer-events:none;transition:opacity .35s;z-index:4}
#musee3d .m3-fondu.on{opacity:1}
#musee3d .m3-univ{position:absolute;left:0;right:0;bottom:0;padding:16px 16px calc(20px + env(safe-area-inset-bottom,0px));text-align:center;color:#e8ece9;background:linear-gradient(transparent,rgba(2,3,6,.85));z-index:3}
#musee3d .m3-univ #m3-etape{font:700 20px/1.3 Georgia,serif;margin:0 auto 8px;max-width:640px}
#musee3d .m3-univ #m3-vraiU{font-size:12.5px;opacity:.75;margin:0 auto 12px;max-width:640px}
@media (prefers-reduced-motion: reduce){#musee3d *{transition:none!important}}`;

  function html() {
    const N = T.niveaux;
    return `<style>${CSS}</style><canvas aria-label="${T.bienvenue}"></canvas>
<div class="m3-bandeau"><div class="m3-etiq" id="m3-ou"></div><span style="display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end"><select class="m3-etiq" id="m3-aller" aria-label="${T.aller}" style="border:0;cursor:pointer;max-width:46vw"></select><button type="button" class="m3-etiq" id="m3-lum" style="border:0;cursor:pointer"></button><button type="button" class="m3-etiq" id="m3-sortir" style="border:0;cursor:pointer">${T.quitter}</button></span></div>
<div class="m3-aide">${T.aide}</div>
<div class="m3-pad">
  <button type="button" id="m3-rapide" class="m3-rapide" aria-pressed="false">${T.rapide}</button>
  <button type="button" id="m3-demitour" aria-label="${T.demitour}" title="${T.demitour} (R)">↻</button><button type="button" data-k="av" aria-label="${T.avancer}">▲</button><span></span>
  <button type="button" data-k="g" aria-label="${T.gauche}">◀</button><button type="button" data-k="ar" aria-label="${T.reculer}">▼</button><button type="button" data-k="d" aria-label="${T.droite}">▶</button>
</div>
<div class="m3-haut" id="m3-musique" hidden><div class="m3-rangee"><button type="button" class="m3-btn" id="m3-son">${T.ecouter}</button><span id="m3-heure"></span></div></div>
<div class="m3-haut" id="m3-modes" hidden><div class="m3-rangee">${Object.entries(T.modes).map(([k, v], i) => `<button type="button" class="m3-btn m3-mode${i ? '' : ' on'}" data-m="${k}">${v}</button>`).join('')}</div><p id="m3-info"></p></div>
<div class="m3-univ" id="m3-univ" hidden><p id="m3-etape"></p><p id="m3-vraiU"></p><button type="button" class="m3-btn" id="m3-retour">${T.retour}</button></div>
<div class="m3-fondu" id="m3-fondu"></div>
<div class="m3-voile" id="m3-cartel" hidden><div class="m3-cartel" role="dialog" aria-modal="true" aria-labelledby="m3-ct"><h2 id="m3-ct"></h2><div class="m3-date" id="m3-cd"></div><div id="m3-cm"></div><div id="m3-cx"></div><div class="m3-vrai" id="m3-cv"></div><button type="button" class="m3-btn" id="m3-fermer" style="margin-top:8px">${T.fermer}</button></div></div>
<div class="m3-voile" id="m3-asc" hidden style="background:rgba(40,46,44,.55)">
  <div class="m3-cabine" role="dialog" aria-label="${T.asc}">
    <h2>${T.asc}</h2><p class="m3-sous">${T.asc_sous}</p>
    <div class="m3-ecran" id="m3-ecran">0</div>
    <div class="m3-eres" id="m3-eres"></div>
    <div class="m3-boutons">${['0', '1', '2', '3', '4', '5', '6'].map((id) => `<button type="button" class="m3-etage" data-e="${id}"><span class="r">${id === '0' ? '0' : '−' + id}</span><span>${N[id][0]}<small>${N[id][1]}</small></span></button>`).join('')}</div>
    <div class="m3-plaque"><span>${T.charge}</span><button type="button" class="m3-vis" id="m3-vis" aria-label="${T.vis}"></button><span>${T.architecte}</span></div>
    <div id="m3-msg"></div>
    <div><button type="button" class="m3-btn" id="m3-rester" style="height:40px;font-size:14px">${T.rester}</button></div>
  </div>
</div>`;
  }

  // ================================================================ la visite
  function visite(M) {
    const THREE = window.THREE;
    boite.innerHTML = html();
    const $ = (s) => boite.querySelector(s);
    const canvas = $('canvas');
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
    renderer.outputEncoding = THREE.sRGBEncoding; renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
    const scene = new THREE.Scene(); scene.background = new THREE.Color(0xdfe2dd); scene.fog = new THREE.Fog(0xdfe2dd, 20, 38);
    const camera = new THREE.PerspectiveCamera(68, 1, 0.05, 120);
    const H = 3.8, CASE = 10, lent = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
    const lien = (href, txt) => `<a href="${esc(BASE + href)}">${esc(txt || href)}</a>`;
    const SEP = LG === 'fr' ? ' : ' : ': ';
    const srcDe = (f) => f ? `<p class="m3-src">${T.source}${SEP}<a href="${DONNEES}${esc(f)}">${esc(f)}</a></p>` : '';
    const verifier = (s) => [s.lien ? `<p>${T.voir}${SEP}${lien(s.lien)}</p>` : '', (s.verifier || []).length ? `<p class="m3-src">${T.vers}${SEP}${s.verifier.map((v) => lien(v)).join(', ')}</p>` : ''].join('');
    const mul = (a) => () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };

    function toile(w, h, f) { const c = document.createElement('canvas'); c.width = w; c.height = h; f(c.getContext('2d'), w, h); return c; }
    function bruit(g, w, h, n, a, clair) { for (let i = 0; i < n; i++) { g.fillStyle = `rgba(${clair ? '255,255,255' : '0,0,0'},${Math.random() * a})`; const s = 1 + Math.random() * 2.5; g.fillRect(Math.random() * w, Math.random() * h, s, s); } }
    function tex(c, rx, ry) { const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rx, ry); t.encoding = THREE.sRGBEncoding; return t; }
    const cSol = toile(512, 512, (g, w, h) => { g.fillStyle = '#3a3b3c'; g.fillRect(0, 0, w, h); bruit(g, w, h, 9000, 0.12, false); bruit(g, w, h, 4000, 0.05, true); g.strokeStyle = 'rgba(0,0,0,.35)'; g.lineWidth = 2; g.strokeRect(0, 0, w, h); });
    const cMur = toile(256, 256, (g, w, h) => { g.fillStyle = '#e9ebe6'; g.fillRect(0, 0, w, h); bruit(g, w, h, 3000, 0.025, false); bruit(g, w, h, 2500, 0.15, true); });
    const MUR = new THREE.MeshStandardMaterial({ map: tex(cMur, 6, 2), roughness: 0.93 });
    const SOCLE = new THREE.MeshStandardMaterial({ color: 0xf1f2ee, roughness: 0.5 });
    const CADRE = new THREE.MeshStandardMaterial({ color: 0x1f2326, roughness: 0.5 });
    const DORE = new THREE.MeshStandardMaterial({ color: 0xc9a447, roughness: 0.4, metalness: 0.4 });
    const INOX = new THREE.MeshStandardMaterial({ color: 0xa9b0ab, metalness: 0.6, roughness: 0.35 });
    const POUTRE = new THREE.MeshStandardMaterial({ color: 0xdfe0dc, roughness: 0.9 });
    const BRONZE = new THREE.MeshLambertMaterial({ color: 0xb59f78 });
    const HEMI = new THREE.HemisphereLight(0xfffbf0, 0x3a3d3f, 0.75); scene.add(HEMI);
    const soleil = new THREE.DirectionalLight(0xfff1d8, 0.5); soleil.position.set(-3, 8, 4); scene.add(soleil);
    const loader = new THREE.TextureLoader();
    const unCube = new THREE.BoxGeometry(1, 1, 1);
    const invisible = new THREE.MeshBasicMaterial({ visible: false });

    // ---------------------------------------------------------------- cartels (fenêtre HTML)
    // c = { t: titre, d: sous-titre, m: [paragraphes], v: « ce qui est vrai », img: [noms], vid, html, echelle }
    const voile = $('#m3-cartel');
    // sur téléphone, le toucher qui ouvre la cabine ou un cartel « retombe » parfois sur le bouton qui vient d'apparaître sous le doigt
    // (Bran, 17/11/2026) : la fenêtre ignore les touchers pendant 450 ms après son ouverture
    function bouclier(el) { el.style.pointerEvents = 'none'; clearTimeout(el._bouclier); el._bouclier = setTimeout(() => { el.style.pointerEvents = ''; }, 450); }
    function ouvrir(c) {
      if (!c) return;
      $('#m3-ct').textContent = c.t; $('#m3-cd').textContent = c.d || '';
      $('#m3-cm').innerHTML = (c.m || []).map((p) => `<p>${esc(p)}</p>`).join('') + (c.html || '');
      let x = '';
      for (const n of c.img || []) x += `<img alt="${esc(c.t)}" src="${esc(BASE + 'musee-reserve/' + n + '.jpg')}">`;
      if (c.vid) x += `<video src="${esc(BASE + 'musee-reserve/brosse.mp4')}" muted loop autoplay playsinline></video>`;
      $('#m3-cx').innerHTML = x;
      $('#m3-cv').innerHTML = c.v ? `<strong>${T.vrai}</strong> ${esc(c.v)}` + (c.echelle ? `<p style="margin-top:10px"><button type="button" class="m3-btn" id="m3-ech">${T.echelle}</button></p>` : '') : '';
      $('#m3-cv').hidden = !c.v;
      if (c.echelle) $('#m3-ech').onclick = () => { fermerCartel(); changerEchelle(); };
      voile.hidden = false; bouclier(voile); $('#m3-fermer').focus();
    }
    function fermerCartel() { voile.hidden = true; $('#m3-cx').innerHTML = ''; }
    $('#m3-fermer').onclick = fermerCartel;
    voile.addEventListener('click', (e) => { if (e.target === voile) fermerCartel(); });
    // cartel d'une donnée publiée (format de musee.json : titre + lignes)
    const C = (t, d, m, v, html) => ({ t, d, m, v, html });
    // une réclame du musée (humour, Bran 2/11/2026) : la blague, puis « ce qui est vrai »
    const Creclame = (r) => r && { t: r.titre, d: '', m: r.lignes, v: r.vrai.replace(/^(Ce qui est vrai|What is true) ?: ?/, '') };

    // ---------------------------------------------------------------- niveaux : un groupe par niveau, un seul visible
    const ETAGES = {}; let courant = null;
    function base(id) { const g = new THREE.Group(); g.visible = false; scene.add(g); const e = { id, nom: T.nom[id], g, obs: [], cibles: [], anim: [] }; ETAGES[id] = e; return e; }
    function boiteE(e, w, h, d, x, y, z, mat, bloque = true) {
      const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat); m.position.set(x, y, z); e.g.add(m);
      if (bloque) e.obs.push({ x1: x - w / 2, x2: x + w / 2, z1: z - d / 2, z2: z + d / 2 });
      return m;
    }
    function cible(e, m, c) { m.userData.cartel = c; e.cibles.push(m); return m; }
    function ecrire(g, txt, x, y, max, lh) {
      let li = '';
      for (const m of String(txt).split(' ')) { const t = li ? li + ' ' + m : m; if (g.measureText(t).width > max && li) { g.fillText(li, x, y); y += lh; li = m; } else li = t; }
      if (li) { g.fillText(li, x, y); y += lh; }
      return y;
    }
    function texte(lignes, { l = 1, h = 0.42, fond = '#f7f8f5', encre = '#1b2124', doux = '#4c5558', titre = 48, corps = 28 } = {}) {
      const W = 768, Hp = Math.round(W * h / l);
      const t = new THREE.CanvasTexture(toile(W, Hp, (g, w, hh) => {
        g.fillStyle = fond; g.fillRect(0, 0, w, hh); g.fillStyle = encre; let y = titre + 16;
        g.font = `700 ${titre}px Georgia, "Times New Roman", serif`; y = ecrire(g, lignes[0], 28, y, w - 56, titre * 1.1) - titre * 1.1 + corps + 22;
        g.font = `400 ${corps}px system-ui, sans-serif`; g.fillStyle = doux;
        for (const li of lignes.slice(1)) { if (y > hh - 8) break; y = ecrire(g, li, 28, y, w - 56, corps * 1.35) + 8; }
      }));
      t.encoding = THREE.sRGBEncoding; return t;
    }
    function panneau(e, c, lignes, l, h, x, y, z, ry, opt = {}) {
      const m = new THREE.Mesh(new THREE.PlaneGeometry(l, h), new THREE.MeshBasicMaterial({ map: texte(lignes, { l, h, ...opt }), toneMapped: false }));
      m.position.set(x, y, z); m.rotation.y = ry; e.g.add(m); if (c) cible(e, m, c); return m;
    }
    // un cadre au mur ou sur une cimaise ; dessiner(g, w, h) peut rendre une promesse (image SVG)
    // une lumière douce sur chaque œuvre accrochée, comme les halos du musée d'avant (Bran, 17/11/2026) : à peine 10 % le jour,
    // plus présente le soir et la nuit (la force est réglée par le cycle de lumière, 9c-lumiere.js)
    const texHalo = new THREE.CanvasTexture(toile(128, 128, (g) => { const d = g.createRadialGradient(64, 64, 0, 64, 64, 64); d.addColorStop(0, 'rgba(255,240,210,.9)'); d.addColorStop(1, 'rgba(255,240,210,0)'); g.fillStyle = d; g.fillRect(0, 0, 128, 128); }));
    function halo(grp, l, h) {
      const m = new THREE.Mesh(new THREE.PlaneGeometry(l * 1.9 + 0.5, h * 1.7 + 0.5), new THREE.MeshBasicMaterial({ map: texHalo, transparent: true, opacity: 0.1, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false }));
      m.position.set(0, h * 0.08, 0.004); m.userData.halo = true; grp.add(m); return m;
    }
    function cadre(e, c, dessiner, l, h, x, y, z, ry, dore = false, res = 256) {
      const grp = new THREE.Group(); grp.position.set(x, y, z); grp.rotation.y = ry; e.g.add(grp);
      const b = new THREE.Mesh(new THREE.BoxGeometry(l + 0.1, h + 0.1, 0.05), dore ? DORE : CADRE); b.position.z = 0.025; grp.add(b); if (l * h < 12) halo(grp, l, h);
      const cv = document.createElement('canvas'); const k = res / Math.max(l, h); cv.width = Math.max(16, Math.round(l * k)); cv.height = Math.max(16, Math.round(h * k));
      const t = new THREE.CanvasTexture(cv); t.encoding = THREE.sRGBEncoding;
      const p = new THREE.Mesh(new THREE.PlaneGeometry(l, h), new THREE.MeshBasicMaterial({ map: t, toneMapped: false })); p.position.z = 0.052; grp.add(p);
      Promise.resolve(dessiner(cv.getContext('2d'), cv.width, cv.height)).then(() => { t.needsUpdate = true; });
      if (c) { cible(e, p, c); cible(e, b, c); }
      return grp;
    }
    function photo(e, c, nom, larg, x, y, z, ry) {
      const grp = new THREE.Group(); grp.position.set(x, y, z); grp.rotation.y = ry; e.g.add(grp);
      const t = loader.load(BASE + 'musee-reserve/' + nom + '.jpg', (tx) => {
        const h = larg * tx.image.height / tx.image.width;
        const cad = new THREE.Mesh(new THREE.BoxGeometry(larg + 0.12, h + 0.12, 0.05), CADRE); cad.position.z = 0.025; grp.add(cad); const ha = halo(grp, larg, h); if (LUM && LUM.ajouter) LUM.ajouter(ha);
        const p = new THREE.Mesh(new THREE.PlaneGeometry(larg, h), new THREE.MeshBasicMaterial({ map: tx, toneMapped: false })); p.position.z = 0.052; grp.add(p); cible(e, p, c);
      });
      t.encoding = THREE.sRGBEncoding; return grp;
    }
    const svgImage = (svg) => (g, w, h) => new Promise((ok) => {
      const im = new Image();
      im.onload = () => { g.fillStyle = '#fff'; g.fillRect(0, 0, w, h); g.drawImage(im, 0, 0, w, h); ok(); };
      im.onerror = () => ok();
      im.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg.includes('xmlns=') ? svg : svg.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" '));
    });
    const cadreVide = (titre, pourquoi) => (g, w, h) => {
      g.fillStyle = '#eef0ec'; g.fillRect(0, 0, w, h); g.strokeStyle = '#b9bfba'; g.setLineDash([8, 6]); g.lineWidth = 2; g.strokeRect(10, 10, w - 20, h - 20); g.setLineDash([]);
      g.fillStyle = '#1b2124'; g.font = 'italic 700 20px Georgia, serif'; g.textAlign = 'center'; const y = ecrire(g, titre, w / 2, h * 0.38, w - 30, 24);
      g.fillStyle = '#5b6560'; g.font = '13px system-ui, sans-serif'; ecrire(g, pourquoi, w / 2, y + 8, w - 34, 16); g.textAlign = 'left';
    };
    const grille = (rangs, marge = 0.1, fond = '#ffffff') => {
      const R = typeof rangs === 'string' ? rangs.match(new RegExp(`.{${Math.round(Math.sqrt(rangs.length))}}`, 'g')) : rangs;
      return (g, w, h) => {
        g.fillStyle = fond; g.fillRect(0, 0, w, h);
        const px = Math.min(w * (1 - 2 * marge) / R[0].length, h * (1 - 2 * marge) / R.length), ox = (w - px * R[0].length) / 2, oy = (h - px * R.length) / 2;
        g.fillStyle = '#1d2326'; R.forEach((li, y) => { for (let x = 0; x < li.length; x++) if (li[x] === '1') g.fillRect(ox + x * px, oy + y * px, px + 0.5, px + 0.5); });
      };
    };
    // cubes de plusieurs sculptures dans un seul InstancedMesh : [{ s, x, y, z, taille }] ; 512 chiffres, case i*64 + j*8 + k (k = hauteur)
    function cubes(e, liste, parent) {
      const n = liste.reduce((t, o) => t + ((o.s || '').match(/[1-9]/g) || []).length, 0);
      if (!n) return null;
      const im = new THREE.InstancedMesh(unCube, BRONZE, n), m = new THREE.Matrix4(), q = new THREE.Quaternion(), p = new THREE.Vector3(), s = new THREE.Vector3();
      let k = 0;
      for (const o of liste) {
        const c = o.taille / 8;
        for (let i = 0; i < 512; i++) {
          const v = +o.s[i]; if (!v) continue;
          const X = Math.floor(i / 64), Y = Math.floor(i / 8) % 8, Z = i % 8, t = c * (0.35 + 0.6 * (v - 1) / 8);
          p.set(o.x + (X - 3.5) * c, o.y + (Z + 0.5) * c, o.z + (Y - 3.5) * c); s.set(t, t, t);
          m.compose(p, q, s); im.setMatrixAt(k++, m);
        }
      }
      im.instanceMatrix.needsUpdate = true; (parent || e.g).add(im); return im;
    }
    function zone3(e, c, x, y, z, l, h, d) { const m = new THREE.Mesh(new THREE.BoxGeometry(l, h, d), invisible); m.position.set(x, y, z); e.g.add(m); return cible(e, m, c); }
    // un totem dans le coin d'une salle du damier : réclame ou titre, lisible des deux côtés
    function totem(e, c, lignes, X, Z, coin, opt = {}) {
      const [sx, sz] = coin, x = X + sx * 3.4, z = Z + sz * 3.4, ry = Math.atan2(-sx, -sz);
      boiteE(e, 1.5, 2.1, 0.12, x, 1.05, z, SOCLE, false).rotation.y = ry;
      e.obs.push({ x1: x - 0.55, x2: x + 0.55, z1: z - 0.55, z2: z + 0.55 });
      for (const f of [1, -1]) {
        const p = panneau(e, c, lignes, 1.36, 1.86, x + Math.sin(ry) * 0.065 * f, 1.08, z + Math.cos(ry) * 0.065 * f, ry + (f < 0 ? Math.PI : 0), { titre: 40, corps: 26, ...opt });
        void p;
      }
    }

    // une salle simple (hall, musique, planétarium, réserve) : sol, plafond, poutres, 4 murs, lampes
    function salleSimple(e, X, Z1, Z2, Hs = H, lampes = true, porteEst = null) {
      Object.assign(e, { X, Z1, Z2 });
      const sol = new THREE.Mesh(new THREE.PlaneGeometry(2 * X, Z1 - Z2), new THREE.MeshStandardMaterial({ map: tex(cSol, 2 * X / 2.5, (Z1 - Z2) / 2.5), roughness: 0.55 }));
      sol.rotation.x = -Math.PI / 2; sol.position.set(0, 0, (Z1 + Z2) / 2); e.g.add(sol);
      const pl = new THREE.Mesh(new THREE.PlaneGeometry(2 * X, Z1 - Z2), new THREE.MeshStandardMaterial({ color: 0xd8dad6, roughness: 1 }));
      pl.rotation.x = Math.PI / 2; pl.position.set(0, Hs, (Z1 + Z2) / 2); e.g.add(pl);
      for (let z = Z1 - 1; z > Z2; z -= 2.2) boiteE(e, 2 * X, 0.22, 0.18, 0, Hs - 0.11, z, POUTRE, false);
      boiteE(e, 0.2, Hs, Z1 - Z2, -X, Hs / 2, (Z1 + Z2) / 2, MUR);
      if (porteEst) {   // une ouverture dans le mur de droite (aile des présidents, Bran 17/11/2026) : deux pans et un linteau
        const [za, zb] = porteEst, hp = 2.9;
        boiteE(e, 0.2, Hs, Z1 - zb, X, Hs / 2, (Z1 + zb) / 2, MUR); boiteE(e, 0.2, Hs, za - Z2, X, Hs / 2, (za + Z2) / 2, MUR);
        boiteE(e, 0.2, Hs - hp, zb - za, X, (Hs + hp) / 2, (za + zb) / 2, MUR, false);
      } else boiteE(e, 0.2, Hs, Z1 - Z2, X, Hs / 2, (Z1 + Z2) / 2, MUR);
      boiteE(e, 2 * X, Hs, 0.2, 0, Hs / 2, Z2, MUR); boiteE(e, 2 * X, Hs, 0.2, 0, Hs / 2, Z1, MUR);
      if (lampes) for (let z = Z1 - 2; z > Z2; z -= 5) { const l = new THREE.PointLight(0xfff3df, 0.45, 13, 1.6); l.position.set(0, Hs - 0.4, z); e.g.add(l); }
    }
    // le damier (Bran, 13/11/2026) : cases de 10 m posées en spirale autour de l'ascenseur ; la salle n prend toujours la case n,
    // une nouvelle salle prend la case suivante, et chaque salle a une porte vers chacune de ses voisines
    function spirale(n) { const out = [[0, 0]]; let x = 0, z = 0, dx = 0, dz = -1, len = 1; while (out.length < n) { for (let r = 0; r < 2; r++) { for (let q = 0; q < len && out.length < n; q++) { x += dx; z += dz; out.push([x, z]); } [dx, dz] = [-dz, dx]; } len++; } return out; }
    function damier(e, nSalles) {
      e.damier = spirale(nSalles + 1);
      const cle = (x, z) => x + ',' + z, ordre = new Map(e.damier.map((c, k) => [cle(...c), k])), Hc = CASE / 2, PORTE = 2.6;
      const matSol = new THREE.MeshStandardMaterial({ map: tex(cSol, 4, 4), roughness: 0.55 }), matPl = new THREE.MeshStandardMaterial({ color: 0xd8dad6, roughness: 1 });
      for (const [cx, cz] of e.damier) {
        const X = cx * CASE, Z = cz * CASE;
        const sol = new THREE.Mesh(new THREE.PlaneGeometry(CASE, CASE), matSol); sol.rotation.x = -Math.PI / 2; sol.position.set(X, 0, Z); e.g.add(sol);
        const pl = new THREE.Mesh(new THREE.PlaneGeometry(CASE, CASE), matPl); pl.rotation.x = Math.PI / 2; pl.position.set(X, H, Z); e.g.add(pl);
        for (let q = -1; q <= 1; q++) boiteE(e, CASE, 0.22, 0.18, X, H - 0.11, Z + q * 3, POUTRE, false);
        const l = new THREE.PointLight(0xfff3df, 0.5, 12, 1.6); l.position.set(X, H - 0.4, Z); e.g.add(l);
        const k0 = ordre.get(cle(cx, cz));
        for (const [dx, dz] of [[0, -1], [1, 0], [0, 1], [-1, 0]]) {
          const kn = ordre.get(cle(cx + dx, cz + dz)); if (kn !== undefined && kn < k0) continue;
          const wx = X + dx * Hc, wz = Z + dz * Hc, ouvert = kn !== undefined, long = dz ? 'x' : 'z';
          const piece = (a, b) => { const L = b - a, m = (a + b) / 2; if (long === 'x') boiteE(e, L, H, 0.2, wx + m, H / 2, wz, MUR); else boiteE(e, 0.2, H, L, wx, H / 2, wz + m, MUR); };
          if (ouvert) { piece(-Hc, -PORTE / 2); piece(PORTE / 2, Hc); if (long === 'x') boiteE(e, PORTE, H - 2.6, 0.2, wx, 2.6 + (H - 2.6) / 2, wz, MUR, false); else boiteE(e, 0.2, H - 2.6, PORTE, wx, 2.6 + (H - 2.6) / 2, wz, MUR, false); }
          else piece(-Hc, Hc);
        }
      }
      return e.damier.map(([cx, cz]) => [cx * CASE, cz * CASE]);
    }
    // la cage d'ascenseur ; sur un niveau en damier, des portes devant et derrière (Bran, 13/11/2026)
    function cage(e, x, z, sens = 1, double = false) {
      const w = 2.6, d = 2.4; e.sens = sens; e.cage = { x, z };
      boiteE(e, w, H, d, x, H / 2, z, MUR);
      const portes = (sg) => {
        const f = z + sg * d / 2, ry = sg > 0 ? 0 : Math.PI;
        const plan = (geo, mat, dx, y, o) => { const m = new THREE.Mesh(geo, mat); m.position.set(x + dx * sg, y, f + sg * o); m.rotation.y = ry; e.g.add(m); return m; };
        const porte = plan(new THREE.PlaneGeometry(1.5, 2.3), INOX, 0, 1.15, 0.011); porte.userData.asc = true; e.cibles.push(porte);
        plan(new THREE.PlaneGeometry(0.015, 2.3), new THREE.MeshBasicMaterial({ color: 0x50575a }), 0, 1.15, 0.013);
        boiteE(e, 1.7, 0.08, 0.06, x, 2.34, f + sg * 0.03, CADRE, false);
        const ens = plan(new THREE.PlaneGeometry(1.7, 0.34), new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(toile(512, 102, (g, w2, h) => { g.fillStyle = '#1b2124'; g.fillRect(0, 0, w2, h); g.fillStyle = '#ffb347'; g.font = '700 58px system-ui, sans-serif'; g.textAlign = 'center'; g.fillText(T.asc.toUpperCase(), w2 / 2, 72); })), toneMapped: false }), 0, 2.62, 0.012);
        ens.userData.asc = true; e.cibles.push(ens);
        const bt = plan(new THREE.CircleGeometry(0.05, 20), new THREE.MeshBasicMaterial({ color: 0xffb347 }), 1.0, 1.15, 0.012); bt.userData.asc = true; e.cibles.push(bt);
      };
      portes(sens); if (double) portes(-sens);
      miniPlan(e, x, z, sens); if (double) miniPlan(e, x, z, -sens);
      const f = z + sens * d / 2; e.depart = { x, z: f + sens * 1.3, yaw: sens > 0 ? Math.PI : 0 };
    }
    // « Vous êtes ici » (finition validée par Bran le 13/11/2026) : le plan du niveau en fil de fer vert sur un pupitre, à gauche de
    // chaque porte d'ascenseur. Il est tourné comme le visiteur qui le lit (le haut du plan = devant lui) ; un point ambre le suit.
    function miniPlan(e, x, z, sg) {
      const R = [];   // rectangles du niveau [x1, z1, x2, z2]
      if (e.damier) for (const [cx, cz] of e.damier) R.push([cx * CASE - CASE / 2, cz * CASE - CASE / 2, cx * CASE + CASE / 2, cz * CASE + CASE / 2]);
      else { R.push([-e.X, e.Z2, e.X, e.Z1]); const A = e.id === '0' && DEF['0'].aile; if (A) R.push([8, A.z2, A.x2, A.z1]); }
      let x1 = Infinity, z1 = Infinity, x2 = -Infinity, z2 = -Infinity;
      for (const r of R) { x1 = Math.min(x1, r[0]); z1 = Math.min(z1, r[1]); x2 = Math.max(x2, r[2]); z2 = Math.max(z2, r[3]); }
      const W = 640, Hc = 480, m = 46, top = 64, k = Math.min((W - 2 * m) / (x2 - x1), (Hc - top - m) / (z2 - z1));
      const ox = (W - (x2 - x1) * k) / 2, oy = top + (Hc - top - m - (z2 - z1) * k) / 2;
      // sg > 0 : le lecteur regarde vers −z, la droite est +x ; sg < 0 : tout tourne d'un demi-tour
      const P = (px, pz) => sg > 0 ? [ox + (px - x1) * k, oy + (pz - z1) * k] : [ox + (x2 - px) * k, oy + (z2 - pz) * k];
      const cv = toile(W, Hc, (g) => {
        g.fillStyle = '#030807'; g.fillRect(0, 0, W, Hc); g.strokeStyle = '#2c5a3c'; g.lineWidth = 4; g.strokeRect(2, 2, W - 4, Hc - 4);
        g.fillStyle = '#5fe08f'; g.font = '700 30px system-ui, sans-serif'; g.fillText(`${T.ici} · ${e.nom.split(' · ')[0]}`, 22, 42);
        g.strokeStyle = '#5fe08f'; g.lineWidth = 2;
        for (const r of R) { const [a, b] = P(r[0], r[1]), [c, d] = P(r[2], r[3]); g.strokeRect(Math.min(a, c), Math.min(b, d), Math.abs(c - a), Math.abs(d - b)); }
        const [a, b] = P(x - 1.3, z - 1.2), [c, d] = P(x + 1.3, z + 1.2); g.fillStyle = '#ffb347'; g.fillRect(Math.min(a, c), Math.min(b, d), Math.abs(c - a), Math.abs(d - b));
      });
      const l = 0.84, h = l * Hc / W, f = z + sg * 1.2, px = x - 1.95 * sg, pz = f + sg * 0.55, ry = sg > 0 ? 0 : Math.PI;
      boiteE(e, 0.5, 0.95, 0.3, px, 0.475, pz, SOCLE);
      const grp = new THREE.Group(); grp.position.set(px, 1.24, pz); grp.rotation.y = ry; e.g.add(grp);
      const pan = new THREE.Group(); pan.rotation.x = -0.75; grp.add(pan);
      const t = new THREE.CanvasTexture(cv); t.encoding = THREE.sRGBEncoding;
      pan.add(new THREE.Mesh(new THREE.PlaneGeometry(l, h), new THREE.MeshBasicMaterial({ map: t, toneMapped: false })));
      const point = new THREE.Mesh(new THREE.CircleGeometry(0.016, 16), new THREE.MeshBasicMaterial({ color: 0xffb347, toneMapped: false })); point.position.z = 0.004; pan.add(point);
      e.anim.push((tt) => {
        if (courant !== e) return;
        const [u, v] = P(joueur.x, joueur.z); point.position.x = (u / W - 0.5) * l; point.position.y = (0.5 - v / Hc) * h;
        point.visible = Math.floor(tt / 500) % 2 === 0 || lent;   // il clignote, comme sur les vrais plans
      });
    }
    // fenêtre sur le garage (musée 1.1 : vraies photos, vérifiées et floutées) ; ce n'est pas une œuvre
    function fenetre(e, f, l, h, x, y, z, ry) {
      const k = f.cartel[LG], c = { t: k.titre, d: f.titre[LG], m: k.lignes, v: k.vrai.replace(/^(Ce qui est vrai|What is true) ?: ?/, '') };
      const grp = new THREE.Group(); grp.position.set(x, y, z); grp.rotation.y = ry; e.g.add(grp);
      const tx = loader.load(BASE + f.image, () => {}, undefined, () => { grp.visible = false; }); tx.encoding = THREE.sRGBEncoding;
      const p = new THREE.Mesh(new THREE.PlaneGeometry(l, h), new THREE.MeshBasicMaterial({ map: tx, toneMapped: false })); p.position.z = 0.105; p.userData.vitre = true; grp.add(p); cible(e, p, c);
      const ALU = new THREE.MeshLambertMaterial({ color: 0x9aa1a4 }), b = 0.09, q = 0.16;
      for (const [w, hh, px, py] of [[l + 2 * b, b, 0, h / 2 + b / 2], [l + 2 * b, b, 0, -h / 2 - b / 2], [b, h, -l / 2 - b / 2, 0], [b, h, l / 2 + b / 2, 0]]) { const m = new THREE.Mesh(new THREE.BoxGeometry(w, hh, q), ALU); m.position.set(px, py, 0.1 + q / 2); grp.add(m); cible(e, m, c); }
      const v = new THREE.Mesh(new THREE.BoxGeometry(0.035, h, 0.03), ALU); v.position.set(0, 0, 0.13); grp.add(v);
      const a = new THREE.Mesh(new THREE.BoxGeometry(l + 0.36, 0.06, 0.3), SOCLE); a.position.set(0, -h / 2 - b - 0.03, 0.25); grp.add(a);
    }

    // ---------------------------------------------------------------- les données : quelles salles, à quel niveau
    // L'aile montrée est celle de l'ère en cours ; une aile d'ère finie reste dans musee.json et dans la visite en texte.
    const aile = (M.plan || []).filter((a) => a.etat !== 'fermee' && (a.salles || []).length).pop() || { ere: M.ere || 1, salles: [] };
    const PAR_TYPE = { portraits: 0, dessins: 1, artistes: 1, sculptures: 2, sculpteurs: 2, chant: 3, glyphes: 4 };
    const niveauDe = (s) => String(s.niveau != null ? s.niveau : PAR_TYPE[s.type]);
    const S = (type) => aile.salles.filter((s) => s.type === type);
    const S1 = (type) => S(type)[0];
    const pres = S1('portraits'), atelier = S1('dessins'), sculpt = S1('sculptures'), chant = S1('chant'), ecr = S1('glyphes');
    const statue = pres && pres.statue && pres.statue.poids ? pres.statue : null;
    const parNiveau = {}; for (const s of aile.salles) (parNiveau[niveauDe(s)] = parNiveau[niveauDe(s)] || []).push(s);
    // nombre de salles de chaque niveau en damier (case 0 = l'ascenseur)
    const nSculpteurs = S('sculpteurs').reduce((t, s) => t + Math.max(1, Math.ceil(s.oeuvres.length / 16)), 0);
    const PAS_P = 3.0;   // aile des présidents : un portrait et son cartel tous les 3 m, sur les deux grands murs
    const DEF = {
      '0': { X: 8, Z1: 6, Z2: -14, cz: -12.7, build: hall, aile: pres && pres.oeuvres.length ? { x2: 8 + Math.max(10, Math.ceil(pres.oeuvres.length / 2) * PAS_P + 4), z1: 2, z2: -6, porte: [-3.4, -0.6] } : null },
      '1': (atelier || S('artistes').length) && { n: (atelier ? 7 : 0) + S('artistes').length, build: niveauArt },
      '2': (sculpt || S('sculpteurs').length) && { n: (sculpt ? 7 : 0) + nSculpteurs, build: niveauSculpture },
      '3': chant && { X: 8, Z1: 3, Z2: -21, cz: 1.7, build: niveauMusique },
      '4': ecr && { n: 3, build: niveauEcriture },
      '5': statue && { X: 8, Z1: 3, Z2: -21, cz: 1.7, build: niveauCerveau },
      '-1': { X: 5, Z1: 3, Z2: -19, cz: 1.7, build: reserve },
    };
    for (const id of Object.keys(DEF)) if (!DEF[id]) delete DEF[id];
    const surfaceDe = (d) => d.n != null ? (d.n + 1) * CASE * CASE : 2 * d.X * (d.Z1 - d.Z2) + (d.aile ? (d.aile.x2 - d.X) * (d.aile.z1 - d.aile.z2) : 0);
    function obtenir(id) {
      if (ETAGES[id]) return ETAGES[id];
      const e = base(id); DEF[id].build(e); return e;   // chargement par niveau : seul un niveau visité est construit
    }

    // ---------------------------------------------------------------- Hinton 1 en fil de fer vert (Bran, 11/11/2026 ; cotes estimées sur la photo, en cm)
    let HINTON = null, PLAN = null;
    function hintonFil(e,x,y,z){const k=.02,grp=new THREE.Group();grp.position.set(x,y,z);e.g.add(grp);
      const VERT=0x5fe08f,fil=new THREE.LineBasicMaterial({color:VERT,transparent:true,toneMapped:false});
      // vitrine noire, comme un vieil écran
      const verre=new THREE.Mesh(new THREE.BoxGeometry(1.24,.78,.78),new THREE.MeshBasicMaterial({color:0x010302,transparent:true,opacity:.94,depthWrite:false}));verre.position.y=.39;verre.renderOrder=1;grp.add(verre);
      const bord=new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(1.24,.78,.78)),new THREE.LineBasicMaterial({color:0x2c5a3c,transparent:true,toneMapped:false}));bord.position.y=.39;bord.renderOrder=2;grp.add(bord);
      verre.userData.id='hinton';e.cibles.push(verre);
      const m=new THREE.Group();m.position.y=.12;grp.add(m);m.scale.setScalar(.02);// 1 unité = 1 cm ; ×2
      const L=(pts,ferme)=>{const g=new THREE.BufferGeometry().setFromPoints(pts.map(p=>new THREE.Vector3(...p)));const l=new (ferme?THREE.LineLoop:THREE.Line)(g,fil);l.renderOrder=3;m.add(l);return l;};
      // profil relevé sur les photos du 11/11 (cm, estimé) : dos droit, dessus plat, pente des LED, petit nez, chanfrein vers le bas
      const W=20,prof=[[-14.5,0],[8.8,0],[14.5,9],[14.5,11],[4.7,24],[-14.5,24]];
      for(const sx of [-W,W])L(prof.map(([zz,yy])=>[sx,yy,zz]),true);
      for(const [zz,yy] of prof)L([[-W,yy,zz],[W,yy,zz]]);
      // dessus : plaque gauche (bouton rouge), matrice au centre, plaque droite, charnière au dos
      L([[-6.8,24,-14.5],[-6.8,24,4.7]]);L([[9.8,24,-14.5],[9.8,24,4.7]]);L([[-1.5,24.01,-14.5],[1.5,24.01,-14.5],[1.5,22.5,-14.5],[-1.5,22.5,-14.5]],true);
      const cercle=(c,r,n=20)=>{const pts=[];for(let i=0;i<n;i++){const a=i/n*Math.PI*2;pts.push(c(Math.cos(a)*r,Math.sin(a)*r));}return L(pts,true);};
      cercle((a,b)=>[-14+a,24.3,-5+b],1.5);cercle((a,b)=>[-14+a,24.7,-5+b],1.0);
      // pente : u en x, s de 0 (nez) à 1 (dessus) ; longueur 16,3 cm
      const SL=16.3,pente=(u,s2,h=0)=>[u,11+13*s2+h*.8,14.5-9.8*s2+h*.6];
      const rect=(x1,x2,s1,s2,h=0)=>L([pente(x1,s1,h),pente(x2,s1,h),pente(x2,s2,h),pente(x1,s2,h)],true);
      rect(-1,16.5,.02,.99);               // panneau LED de face
      rect(-11.5,-3.5,.62,.95,.4);rect(-10.8,-4.2,.66,.91,.4); // écran de score sous sa vitre
      rect(-19.5,-1.5,.02,.55,1);          // plaque des boutons, posée devant
      for(const [u,s2] of [[-15,.36],[-10.5,.17],[-6,.36]]){cercle((a,b)=>pente(u+a,s2+b/SL,1.3),1.7);cercle((a,b)=>pente(u+a,s2+b/SL,1.7),1.15);}
      // chanfrein du bas avec son trou de câble
      cercle((a,b)=>[-12+a,4.5+b*.85,11.6+b*.55],1.3);
      // deux matrices 16×16 de LED : points carrés dont la lumière change
      const mat=(f)=>{const pos=[],col=[];for(let j=0;j<16;j++)for(let i=0;i<16;i++){pos.push(...f(i,j));col.push(.1,.3,.15);}
        const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));g.setAttribute('color',new THREE.Float32BufferAttribute(col,3));
        const p=new THREE.Points(g,new THREE.PointsMaterial({size:.022,vertexColors:true,transparent:true,toneMapped:false}));p.renderOrder=3;m.add(p);return g;};
      const face=mat((i,j)=>pente(-.2+i*1.05,.05+(15-j)*.06,.1));
      const dessus=mat((i,j)=>[-6+i*1.0,24.1,3.9-j*1.0]);
      // pierre, feuille, ciseaux en 16×16
      const SYM=[(i,j)=>((i-7.5)**2/30+(j-8)**2/26)<1,(i,j)=>i>3&&i<12&&j>1&&j<14&&!(i>8&&j<5&&i-8>4-j),(i,j)=>Math.abs((i-7.5)-(j-7.5))<1.3&&j<10||Math.abs((i-7.5)+(j-7.5))<1.3&&j<10||((i-4)**2+(j-12)**2<5)||((i-11)**2+(j-12)**2<5)];
      return {face,dessus,SYM};}

    function animerHinton(t) {
      if (!HINTON || courant.id !== '0') return;
      if (PLAN && !lent) PLAN.tour.rotation.y = t / 9000;
      const cycle = t / 1000 % 4.5, coup = Math.floor(t / 4500) % 3;
      const cd = HINTON.dessus.attributes.color, cf = HINTON.face.attributes.color;
      for (let n = 0; n < 256; n++) {
        const calc = cycle < 2.5; const v = calc ? 0.25 + 0.75 * Math.abs(Math.sin(n * 12.9898 + Math.floor(t / 180) * 0.37 * (n % 7 + 1))) : 0.18 + 0.2 * ((n * 7) % 5) / 5; cd.setXYZ(n, 0.25 * v, v, 0.55 * v);
        const i = n % 16, j = Math.floor(n / 16), on = !calc && HINTON.SYM[coup](i, j); cf.setXYZ(n, on ? 0.6 : 0.06, on ? 1 : 0.16, on ? 0.7 : 0.09);
      }
      cd.needsUpdate = true; cf.needsUpdate = true;
    }
    const CARTELS = { hinton: T.hinton, plan: T.plan_c };
    const vus = () => { try { return JSON.parse(localStorage.getItem('mcl-musee-vus') || '[]'); } catch (_) { return []; } };
    const noterVu = (id) => { try { const v = new Set(vus()); v.add(id); localStorage.setItem('mcl-musee-vus', JSON.stringify([...v])); } catch (_) { /* navigation privée */ } };

    // ---------------------------------------------------------------- rez-de-chaussée : le hall
    function hall(e) {
      salleSimple(e, 8, 6, -14, H, true, DEF['0'].aile && DEF['0'].aile.porte);
      cage(e, 0, -12.7);
      e.depart = { x: 0, z: 4.8, yaw: 0 };
      const O = -8 + 0.11, E = 8 - 0.11, N = -14 + 0.11, Sd = 6 - 0.11;
      // Hinton au centre, le plan à sa gauche, l'ascenseur au fond entre les deux (Bran, 11 et 13/11/2026)
      boiteE(e, 1.3, 1.0, 0.8, 1.9, 0.5, -3, SOCLE);
      HINTON = hintonFil(e, 1.9, 1.0, -3);
      panneau(e, 'hinton', [T.hinton.t, '2026 · ' + T.lire], 0.62, 0.28, 1.9, 0.75, -2.59, 0, { titre: 44, corps: 30 });
      planDuMusee(e, -1.9, -3);
      // bienvenue et compte (mur du fond), réclames
      const compte = T.compte(M, M.edition);
      panneau(e, C(T.bienvenue, '', [T.bienvenue_txt, compte], null, `<p class="m3-src">${lien('musee.json')}, ${lien('musee-catalogue.json')}</p>`), [T.bienvenue, T.bienvenue_txt, compte], 2.8, 1.3, 4.4, 2.0, N, 0, { titre: 46, corps: 28 });
      if (M.reclame) panneau(e, Creclame(M.reclame[LG]), [M.reclame[LG].titre, ...M.reclame[LG].lignes, M.reclame[LG].vrai], 2.6, 1.6, O, 1.9, 1.5, Math.PI / 2, { titre: 44, corps: 26, fond: '#1b2124', encre: '#f2f4f1', doux: '#c9cfcb' });
      if (M.architecte) panneau(e, Creclame(M.architecte[LG]), [M.architecte[LG].titre, ...M.architecte[LG].lignes, M.architecte[LG].vrai], 2.4, 1.6, -4.2, 1.9, Sd, Math.PI, { titre: 44, corps: 26, fond: '#1b2124', encre: '#f2f4f1', doux: '#c9cfcb' });
      panneau(e, C(T.seul, '', []), [T.seul], 1.8, 0.8, 0.4, 2.0, Sd, Math.PI, { titre: 34, corps: 24, fond: '#1b2124', encre: '#f2f4f1' });
      // tout un pays dans une boîte, et son bouton « changer d'échelle »
      if (M.fin) { const f = M.fin[LG], c = { ...Creclame(f), echelle: true }; panneau(e, c, [f.titre, ...f.lignes], 2.4, 1.9, O, 1.9, -10.4, Math.PI / 2, { titre: 48, corps: 24 }); }
      // l'annexe du Temple (en chantier tant que l'institution n'est pas en service)
      for (const a of M.annexes || []) {
        const ch = a.etat !== 'ouverte';
        panneau(e, C(a.titre[LG], ch ? T.chantier : '', [a.texte[LG]], null, a.lien ? `<p>${T.voir}${SEP}${lien(a.lien)}</p>` : ''), [a.titre[LG], (ch ? T.chantier.toUpperCase() + ' · ' : '') + a.texte[LG]], 1.6, 1.2, E, 1.9, 4.2, -Math.PI / 2, { titre: 40, corps: 24, fond: ch ? '#1b1b17' : '#f7f8f5', encre: ch ? '#fff6cf' : '#1b2124', doux: ch ? '#e9dfae' : '#4c5558' });
        break;
      }
      // les fenêtres sur le garage : on est dans la boîte dès l'entrée
      const FEN = Object.fromEntries(((M.fenetres || {}).liste || []).map((f) => [f.id, f]));
      if (FEN.nord) fenetre(e, FEN.nord, 3.0, 3.0 * FEN.nord.hauteur / FEN.nord.largeur, -4.6, 1.95, N, 0);
      if (FEN.est) fenetre(e, FEN.est, 0.95, 0.95 * FEN.est.hauteur / FEN.est.largeur, E, 1.95, 1.6, -Math.PI / 2);
      if (FEN.ouest) fenetre(e, FEN.ouest, 0.95, 0.95 * FEN.ouest.hauteur / FEN.ouest.largeur, O, 1.95, -5.2, Math.PI / 2);
      if (FEN.sud) fenetre(e, FEN.sud, 0.95, 0.95 * FEN.sud.hauteur / FEN.sud.largeur, 3.6, 1.95, Sd, Math.PI);
      // les présidents : leur aile s'ouvre à droite de l'entrée (Bran, 17/11/2026) ; la statue est devenue le planétarium du −5
      if (pres && DEF['0'].aile) aileDesPresidents(e, DEF['0'].aile);
    }

    // ---------------------------------------------------------------- l'aile des présidents (Bran, 17/11/2026)
    // Une galerie de 8 m de large et 6,2 m sous plafond (les egos présidentiels, comme dans le musée d'avant) derrière le mur de droite du hall. Chaque portrait a son cartel À CÔTÉ, à sa droite, jamais
    // dessous : le cartel ne mange plus le tableau. Ordre des mandats : mur de gauche en entrant, puis retour par le mur d'en face.
    // L'aile s'allonge seule de 2,7 m tous les deux présidents.
    function aileDesPresidents(e, A) {
      const HP = 6.2, X1 = 8, X2 = A.x2, Z1 = A.z1, Z2 = A.z2, L = X2 - X1, xm = (X1 + X2) / 2, zm = (Z1 + Z2) / 2;
      const sol = new THREE.Mesh(new THREE.PlaneGeometry(L, Z1 - Z2), new THREE.MeshStandardMaterial({ map: tex(cSol, L / 2.5, (Z1 - Z2) / 2.5), roughness: 0.55 }));
      sol.rotation.x = -Math.PI / 2; sol.position.set(xm, 0.001, zm); e.g.add(sol);
      const pl = new THREE.Mesh(new THREE.PlaneGeometry(L, Z1 - Z2), new THREE.MeshStandardMaterial({ color: 0xd8dad6, roughness: 1 }));
      pl.rotation.x = Math.PI / 2; pl.position.set(xm, HP, zm); e.g.add(pl);
      for (let x = X1 + 1.2; x < X2; x += 2.2) boiteE(e, 0.18, 0.22, Z1 - Z2, x, HP - 0.11, zm, POUTRE, false);
      boiteE(e, L + 0.2, HP, 0.2, xm, HP / 2, Z2, MUR); boiteE(e, L + 0.2, HP, 0.2, xm, HP / 2, Z1, MUR); boiteE(e, 0.2, HP, Z1 - Z2, X2, HP / 2, zm, MUR);
      boiteE(e, 0.2, HP - H, Z1 - Z2, X1 + 0.1, (H + HP) / 2, zm, MUR, false);   // au-dessus du mur du hall, côté aile
      for (let x = X1 + 2.5; x < X2; x += 4.5) { const l = new THREE.PointLight(0xfff3df, 0.6, 15, 1.6); l.position.set(x, HP - 0.5, zm); e.g.add(l); }
      // au-dessus de la porte, côté hall, et au fond de l'aile : le titre ; la réclame sur le mur du fond
      const [za, zb] = A.porte, cs = C(pres.titre[LG], T.nom['0'], [T.presidents[1]], null, verifier(pres));
      panneau(e, cs, [pres.titre[LG]], 2.4, 0.42, X1 - 0.12, 3.3, (za + zb) / 2, -Math.PI / 2, { titre: 64, corps: 24, l: 2.4, h: 0.42 });
      panneau(e, cs, [pres.titre[LG], T.presidents[1]], 1.8, 0.9, X2 - 0.11, 2.6, zm + 1.6, -Math.PI / 2, { titre: 46, corps: 24 });
      if (pres.reclame) panneau(e, Creclame(pres.reclame[LG]), [pres.reclame[LG].titre, ...pres.reclame[LG].lignes], 1.8, 1.2, X2 - 0.11, 1.9, zm - 1.6, -Math.PI / 2, { titre: 34, corps: 24, fond: '#1b2124', encre: '#f2f4f1', doux: '#c9cfcb' });
      const nN = Math.ceil(pres.oeuvres.length / 2);
      pres.oeuvres.forEach((o, i) => {
        const k = o.cartel[LG], c = C(k.nom, k.info, [...k.lignes, ...k.bas], null, srcDe(o.fichier) + verifier(pres));
        // mur nord (on le regarde vers −z : la droite est +x) puis mur sud (on le regarde vers +z : la droite est −x)
        const nord = i < nN, r = nord ? i : pres.oeuvres.length - 1 - i, xc = X1 + 2.2 + r * PAS_P, z = nord ? Z2 + 0.11 : Z1 - 0.11, ry = nord ? 0 : Math.PI, d = nord ? 1 : -1;
        cadre(e, c, o.svg ? svgImage(o.svg) : cadreVide(k.vide[0], k.vide[1]), 1.3, 1.62, xc - 0.55 * d, 2.15, z, ry);
        panneau(e, c, [k.nom, k.info, ...k.lignes], 0.95, 0.9, xc + 0.82 * d, 1.6, z + 0.01 * (nord ? 1 : -1), ry, { titre: 68, corps: 42 });
      });
    }

    // ---------------------------------------------------------------- le plan du musée en fil de fer vert (Bran, 13/11/2026)
    // un volume par niveau, ses salles découpées ; un niveau s'allume quand on l'a visité ; la réserve n'y paraît qu'après
    function planDuMusee(e, px, pz) {
      const k = 0.012;
      boiteE(e, 1.3, 1.0, 0.8, px, 0.5, pz, SOCLE);
      const grp = new THREE.Group(); grp.position.set(px, 1.0, pz); e.g.add(grp);
      const verre = new THREE.Mesh(new THREE.BoxGeometry(1.24, 0.86, 0.78), new THREE.MeshBasicMaterial({ color: 0x010302, transparent: true, opacity: 0.94, depthWrite: false })); verre.position.y = 0.43; verre.renderOrder = 1; grp.add(verre); cible(e, verre, 'plan');
      const bord = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(1.24, 0.86, 0.78)), new THREE.LineBasicMaterial({ color: 0x2c5a3c, transparent: true, toneMapped: false })); bord.position.y = 0.43; bord.renderOrder = 2; grp.add(bord);
      const tour = new THREE.Group(); tour.position.y = 0.02; grp.add(tour); const dec = new THREE.Group(); dec.position.z = 0.08; tour.add(dec);
      const ordre = ['-1', '0', '1', '2', '3', '4', '5', '6'], hN = 0.075, mats = {}, blocs = {};
      ordre.forEach((id, r) => {
        const y = 0.74 - r * 0.1, D = DEF[id], pointille = !D;
        const mat = pointille ? new THREE.LineDashedMaterial({ color: 0x5fe08f, dashSize: 0.015, gapSize: 0.015, transparent: true, opacity: 0.35, toneMapped: false }) : new THREE.LineBasicMaterial({ color: 0x5fe08f, transparent: true, opacity: 0.35, toneMapped: false });
        mats[id] = mat;
        const seg = [], B = (a, b) => seg.push(...a, ...b);
        const boiteFil = (x1, z1, x2, z2) => { const c = [[x1, z1], [x2, z1], [x2, z2], [x1, z2]]; for (let q = 0; q < 4; q++) { const [ax, az] = c[q], [bx, bz] = c[(q + 1) % 4]; B([ax, y, az], [bx, y, bz]); B([ax, y + hN, az], [bx, y + hN, bz]); B([ax, y, az], [ax, y + hN, az]); } };
        if (D && D.n != null) { const h = CASE / 2 * k; for (const [cx, cz] of spirale(D.n + 1)) { const X0 = cx * CASE * k, Z0 = (cz * CASE - 1.0) * k; boiteFil(X0 - h, Z0 - h, X0 + h, Z0 + h); } }
        else { const X = D ? D.X : 7.5, Z1 = D ? D.Z1 : 3, Z2 = D ? D.Z2 : -23, cz = D ? D.cz : 1.7; boiteFil(-X * k, (Z1 - cz) * k, X * k, (Z2 - cz) * k); if (D && D.aile) boiteFil(X * k, (D.aile.z1 - cz) * k, D.aile.x2 * k, (D.aile.z2 - cz) * k); const zc = ((Z1 + Z2) / 2 - cz) * k; B([-X * k, y, zc], [X * k, y, zc]); B([-X * k, y + hN, zc], [X * k, y + hN, zc]); }
        const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(seg, 3));
        const l = new THREE.LineSegments(g, mat); l.renderOrder = 3; if (pointille) l.computeLineDistances();
        const bloc = new THREE.Group(); bloc.add(l); dec.add(bloc); blocs[id] = bloc;
      });
      // la cage d'ascenseur traverse tous les niveaux
      const fut = new THREE.LineBasicMaterial({ color: 0xffb347, toneMapped: false });
      for (const [dx, dz] of [[-1.3, -1.2], [1.3, -1.2], [1.3, 1.2], [-1.3, 1.2]]) { const g = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(dx * k, 0.04, dz * k), new THREE.Vector3(dx * k, 0.64 + hN, dz * k)]); const l = new THREE.Line(g, fut); l.renderOrder = 3; dec.add(l); }
      const ouverts = Object.keys(DEF).filter((id) => id !== '-1');
      const surf = ouverts.reduce((t, id) => t + surfaceDe(DEF[id]), 0);
      const aff = surf >= 1e6 ? `${(surf / 1e6).toLocaleString(LG === 'fr' ? 'fr-FR' : 'en-GB', { maximumFractionDigits: 2 })} km²` : `${nb(surf)} m²`;
      panneau(e, 'plan', T.plan(aff, ouverts.length), 0.62, 0.34, px, 0.72, pz + 0.41, 0, { titre: 44, corps: 32 });
      PLAN = { tour, dec, k, hN, Y: Object.fromEntries(ordre.map((id, r) => [id, 0.74 - r * 0.1])), compteur: VIS.compteur(e, px, 0.5, pz + 0.411), maj: () => { const v = new Set(vus()); for (const id of ordre) mats[id].opacity = v.has(id) ? 1 : 0.35; blocs['-1'].visible = v.has('-1'); } };
      PLAN.maj();
    }

    // une cimaise au centre d'une salle, vue des deux côtés ; grille de cadres (ncol × nlig) par face
    function cimaise(e, X, Z, titre, cTitre) {
      boiteE(e, 4.6, 2.3, 0.3, X, 1.15, Z, SOCLE);
      for (const f of [1, -1]) panneau(e, cTitre, titre, 1.5, 0.36, X, 2.55, Z + 0.16 * f, f > 0 ? 0 : Math.PI, { titre: 40, corps: 24 });
    }
    function placer(i, nParFace, ncol, pas, ytop, dy) {
      const f = i < nParFace ? 1 : -1, q = i % nParFace, col = q % ncol, lig = Math.floor(q / ncol);
      return { f, x: (col - (ncol - 1) / 2) * pas * f, y: ytop - lig * dy };
    }
    // titres du niveau sur les flancs de la cage (le seul mur jamais percé d'une porte)
    function flancs(e, gauche, droite) {
      const { x, z } = e.cage;
      if (gauche) panneau(e, gauche[0], gauche[1], 2.0, 1.2, x - 1.31, 1.8, z, -Math.PI / 2, gauche[2] || { titre: 44, corps: 24 });
      if (droite) panneau(e, droite[0], droite[1], 2.0, 1.2, x + 1.31, 1.8, z, Math.PI / 2, droite[2] || { titre: 44, corps: 24 });
    }
    const optReclame = { titre: 36, corps: 24, fond: '#1b2124', encre: '#f2f4f1', doux: '#c9cfcb' };
    const lignesReclame = (r) => [r.titre, ...r.lignes, r.vrai];

    // ---------------------------------------------------------------- −1 : art primaire (l'atelier et les artistes du soir)
    function niveauArt(e) {
      const ART = S('artistes'), cases = damier(e, DEF['1'].n); cage(e, 0, 1.0, -1, true);
      let k = 1;
      if (atelier) {
        const a = atelier.artiste, crit = ((atelier.critique || {})[LG]) || [], src = srcDe(atelier.source) + verifier(atelier);
        const cs = C(atelier.titre[LG], T.soir_du(dateLongue(atelier.date), atelier.edition), [T.artiste_soir + SEP + T.cit(a, regionDe(a)), ...crit], null, src);
        flancs(e, [cs, [atelier.titre[LG], T.soir_du(dateLongue(atelier.date), atelier.edition), T.artiste_soir + SEP + T.cit(a, regionDe(a))]], atelier.reclame && [Creclame(atelier.reclame[LG]), lignesReclame(atelier.reclame[LG]), optReclame]);
        // salle 1 : l'artiste du soir en grand
        const [X1, Z1] = cases[k++];
        cimaise(e, X1, Z1, [T.artiste_soir, T.cit(a, regionDe(a))], cs);
        for (const f of [1, -1]) cadre(e, cs, grille(atelier.dessins[a - 1] || ''), 1.3, 1.3, X1, 1.35, Z1 + 0.16 * f, f > 0 ? 0 : Math.PI, true);
        totem(e, cs, [T.critique, ...crit], X1, Z1, [1, -1]);
        // salles 2 à 7 : une par région, 20 dessins
        for (let r = 0; r < 6; r++) {
          const [X, Z] = cases[k++], nomR = region(REGIONS[r]);
          const cr = C(T.salle_region(nomR), T.soir_du(dateLongue(atelier.date), atelier.edition), [T.salle_region_txt], null, src);
          cimaise(e, X, Z, [nomR, T.salle_region(nomR)], cr);
          for (let q = 0; q < 20; q++) {
            const id = r * 20 + q + 1, bits = atelier.dessins[id - 1]; if (!bits) continue;
            const p = placer(q, 10, 5, 0.9, 1.6, 0.7);
            cadre(e, C(T.cit(id, nomR), T.soir_du(dateLongue(atelier.date), atelier.edition), [T.salle_region_txt], null, src), grille(bits), 0.5, 0.5, X + p.x, p.y, Z + 0.16 * p.f, p.f > 0 ? 0 : Math.PI, id === a);
          }
        }
      }
      // une salle par mois des artistes du soir, un tableau par soir
      for (const s of ART) {
        const [X, Z] = cases[k++];
        const cm = C(s.titre[LG], T.nom['1'], [], null, verifier(s));
        cimaise(e, X, Z, [s.titre[LG], `${s.oeuvres.length} · ${T.artiste_soir}`], cm);
        s.oeuvres.slice(0, 32).forEach((o, i) => {
          const p = placer(i, 16, 8, 0.56, 1.7, 0.75), crit = ((o.critique || {})[LG]) || [];
          const c = C(T.cit(o.id, region(o.region)), T.soir_du(dateLongue(o.date), o.edition), [T.cases(o.cases), ...crit], null, srcDe(o.source) + verifier(s));
          cadre(e, c, grille(o.dessin), 0.42, 0.42, X + p.x, p.y, Z + 0.16 * p.f, p.f > 0 ? 0 : Math.PI);
        });
        if (s.reclame) totem(e, Creclame(s.reclame[LG]), lignesReclame(s.reclame[LG]), X, Z, [-1, 1], optReclame);
      }
    }

    // ---------------------------------------------------------------- −2 : sculpture (cubes 8 × 8 × 8, règle S1)
    function niveauSculpture(e) {
      const cases = damier(e, DEF['2'].n); cage(e, 0, 1.0, -1, true);
      let k = 1;
      if (sculpt) {
        const sc = sculpt.sculpteur, crit = ((sculpt.critique || {})[LG]) || [], src = srcDe(sculpt.source) + verifier(sculpt);
        const cs = C(sculpt.titre[LG], T.soir_du(dateLongue(sculpt.date), sculpt.edition), [T.sculpteur_soir + SEP + T.cit(sc, regionDe(sc)), ...crit], null, src);
        flancs(e, [cs, [sculpt.titre[LG], T.soir_du(dateLongue(sculpt.date), sculpt.edition), T.sculpteur_soir + SEP + T.cit(sc, regionDe(sc))]], sculpt.reclame && [Creclame(sculpt.reclame[LG]), lignesReclame(sculpt.reclame[LG]), optReclame]);
        // salle 1 : le sculpteur du soir en grand, qui tourne lentement
        const [X1, Z1] = cases[k++];
        boiteE(e, 1.3, 0.9, 1.3, X1, 0.45, Z1, SOCLE);
        if (sc && sculpt.sculptures[sc - 1]) { const grp = new THREE.Group(); grp.position.set(X1, 0, Z1); e.g.add(grp); cubes(e, [{ s: sculpt.sculptures[sc - 1], x: 0, y: 0.9, z: 0, taille: 1.15 }], grp); if (!lent) e.anim.push((t, dt) => { grp.rotation.y += dt * 0.25; }); }
        zone3(e, cs, X1, 1.4, Z1, 1.4, 2.0, 1.4);
        for (const f of [1, -1]) panneau(e, cs, [T.sculpteur_soir, T.cit(sc, regionDe(sc))], 1.2, 0.42, X1, 0.45, Z1 + 0.66 * f, f > 0 ? 0 : Math.PI, { titre: 40, corps: 26 });
        totem(e, cs, [T.critique, ...crit], X1, Z1, [1, -1]);
        // salles 2 à 7 : une table par région, 20 sculptures en 2 rangs de 10 ; socle doré pour le sculpteur du soir
        const petites = [];
        for (let r = 0; r < 6; r++) {
          const [X, Z] = cases[k++], nomR = region(REGIONS[r]), Lt = 3.6, D = 1.0, ht = 0.85;
          const ct = C(T.table(nomR), T.soir_du(dateLongue(sculpt.date), sculpt.edition), [T.table_txt], null, src);
          boiteE(e, Lt, ht, D, X, ht / 2, Z, SOCLE);
          zone3(e, ct, X, ht + 0.25, Z, Lt, 0.6, D);
          for (const f of [1, -1]) panneau(e, ct, [nomR, T.table(nomR)], 1.4, 0.34, X, 0.45, Z + (D / 2 + 0.01) * f, f > 0 ? 0 : Math.PI, { titre: 40, corps: 24 });
          for (let q = 0; q < 20; q++) {
            const id = r * 20 + q + 1, s = sculpt.sculptures[id - 1]; if (!s) continue;
            const x = X - Lt / 2 + 0.18 + (q % 10) * 0.36, z = Z + (q < 10 ? -0.22 : 0.22);
            if (id === sc) boiteE(e, 0.3, 0.02, 0.3, x, ht + 0.01, z, DORE, false);
            petites.push({ s, x, y: ht + 0.02, z, taille: 0.24 });
          }
        }
        cubes(e, petites);
      }
      // les sculpteurs du soir : un socle par soir, 16 par salle au plus
      for (const s of S('sculpteurs')) {
        for (let part = 0; part * 16 < Math.max(1, s.oeuvres.length); part++) {
          const [X, Z] = cases[k++], liste = s.oeuvres.slice(part * 16, part * 16 + 16), pieces = [];
          liste.forEach((o, i) => {
            const x = X + ((i % 4) - 1.5) * 1.9, z = Z + (Math.floor(i / 4) - 1.5) * 1.9, crit = ((o.critique || {})[LG]) || [];
            const c = C(T.cit(o.id, region(o.region)), T.soir_du(dateLongue(o.date), o.edition), [T.deplaces(o.deplaces), ...crit], null, srcDe(o.source) + verifier(s));
            boiteE(e, 0.6, 0.95, 0.6, x, 0.475, z, SOCLE);
            pieces.push({ s: o.sculpture, x, y: 0.95, z, taille: 0.5 });
            zone3(e, c, x, 1.2, z, 0.7, 0.6, 0.7);
            panneau(e, c, [dateCourte(o.date), `n° ${o.id}`], 0.5, 0.2, x, 0.6, z + 0.31, 0, { titre: 52, corps: 36 });
          });
          cubes(e, pieces);
          if (part === 0) totem(e, Creclame((s.reclame || {})[LG]) || C(s.titre[LG], '', []), s.reclame ? lignesReclame(s.reclame[LG]) : [s.titre[LG]], X, Z, [-1, 1], s.reclame ? optReclame : {});
        }
      }
    }

    // ---------------------------------------------------------------- −4 : écriture (glyphes 5 × 5, règle G1)
    function niveauEcriture(e) {
      const s = ecr, cases = damier(e, 3); cage(e, 0, 1.0, -1, true);
      const src = srcDe(s.source) + verifier(s);
      const ca = C(T.abc, s.titre[LG], [T.abc_txt(s.oeuvres.length, s.idees), T.ouverte_le(dateLongue(s.ouverture)), T.regle_g, ...s.oeuvres.map((o) => `${o.ecrit}${SEP}${o[LG]}`)], null, src);
      flancs(e, [ca, [s.titre[LG], T.abc_txt(s.oeuvres.length, s.idees)]], s.reclame && [Creclame(s.reclame[LG]), lignesReclame(s.reclame[LG]), optReclame]);
      // salle 1 : l'abécédaire, un glyphe par mot commun
      const [X1, Z1] = cases[1];
      cimaise(e, X1, Z1, [T.abc, T.abc_txt(s.oeuvres.length, s.idees)], ca);
      const nPF = Math.ceil(s.oeuvres.length / 2), ncol = Math.min(8, Math.max(4, Math.ceil(nPF / 3))), pas = 4.2 / ncol, t = Math.min(0.42, pas * 0.75);
      s.oeuvres.forEach((o, i) => {
        const p = placer(i, nPF, ncol, pas, 1.85, (1.7 / Math.max(1, Math.ceil(nPF / ncol))));
        const c = C(o.ecrit, `${o[LG]} · ${T.abc}`, [T.regle_g], null, src);
        cadre(e, c, (g, w, h) => { grille(o.glyphe, 0.18)(g, w, h); g.fillStyle = '#1d2326'; g.font = `600 ${Math.round(h * 0.13)}px system-ui, sans-serif`; g.textAlign = 'center'; g.fillText(o.ecrit, w / 2, h - 6); }, t, t, X1 + p.x, p.y, Z1 + 0.16 * p.f, p.f > 0 ? 0 : Math.PI);
      });
      // salle 2 : la frise des soirs et l'histoire de l'écriture
      const [X2, Z2] = cases[2];
      if (s.frise.length) {
        const F = s.frise.slice(-24), n = F.length;
        const cf = C(T.frise, s.titre[LG], [T.frise_txt, ...s.frise.map((f) => `${dateLongue(f.date)}${SEP}${f.ecrit} (${f[LG]})`)], null, src);
        cimaise(e, X2, Z2, [T.frise, T.frise_txt], cf);
        const dessin = (g, w, h) => {
          g.fillStyle = '#ffffff'; g.fillRect(0, 0, w, h);
          const cw = w / n, tt = Math.min(cw * 0.72, h * 0.62), px = tt / 5;
          F.forEach((f, i) => {
            const ox = i * cw + (cw - tt) / 2, oy = h * 0.1; g.fillStyle = '#1d2326';
            for (let b = 0; b < 25; b++) if (f.glyphe[b] === '1') g.fillRect(ox + (b % 5) * px, oy + Math.floor(b / 5) * px, px + 0.5, px + 0.5);
            g.fillStyle = '#5b6560'; g.textAlign = 'center'; const dt = dateCourte(f.date); let fs = Math.round(Math.min(cw * 0.26, h * 0.2)); do { g.font = `${fs}px system-ui, sans-serif`; } while (g.measureText(dt).width > cw * 0.86 && --fs > 5); g.fillText(dt, i * cw + cw / 2, h * 0.92);
          });
        };
        const l = Math.min(4.3, 0.36 * n + 0.4);
        for (const f of [1, -1]) cadre(e, cf, dessin, l, Math.max(0.5, l / n * 1.25), X2, 1.5, Z2 + 0.16 * f, f > 0 ? 0 : Math.PI, false, 2048);
      }
      const lh = [T.ouverte_le(dateLongue(s.ouverture)), ...s.histoire.map(([d, k]) => T.hist(dateLongue(d), k))];
      totem(e, C(T.histoire, s.titre[LG], lh, null, src), [T.histoire, ...lh.slice(-9)], X2, Z2, [1, -1], { titre: 40, corps: 22 });
      // salle 3 : les noms des présidents en cartouche
      const [X3, Z3] = cases[3];
      const cn = C(T.noms, s.titre[LG], [T.noms_txt], null, src);
      cimaise(e, X3, Z3, [T.noms, T.noms_txt], cn);
      const nn = s.noms.length, nPF3 = Math.ceil(nn / 2), pas3 = Math.min(2.1, 4.2 / Math.max(1, nPF3));
      s.noms.forEach((o, i) => {
        const f = i < nPF3 ? 1 : -1, q = i % nPF3, x = X3 + (q - (nPF3 - 1) / 2) * pas3 * f;
        const cap = o.fin ? T.pres_de(dateLongue(o.debut), dateLongue(o.fin)) : T.pres_dep(dateLongue(o.debut));
        const c = C(o.nom, `${region(o.region)} · ${cap}`, [T.noms_txt], null, verifier(s));
        const L = Math.min(pas3 * 0.85, 0.12 * o.rangs[0].length);
        cadre(e, c, grille(o.rangs, 0.08), L, L * 7 / o.rangs[0].length, x, 1.6, Z3 + 0.16 * f, f > 0 ? 0 : Math.PI, true);
        panneau(e, c, [o.nom, cap], Math.min(1.6, pas3 * 0.9), 0.34, x, 0.85, Z3 + 0.165 * f, f > 0 ? 0 : Math.PI, { titre: 40, corps: 22 });
      });
    }

    // ---------------------------------------------------------------- −3 : la musique (le chant de la place, règle C1 ; Bran, 16/11/2026)
    // Six tambours en cercle, un par région ; la partition du soir au fond ; le mur des soirs à droite ; le critique à gauche.
    // Lit seulement les soirs de chant.json recopiés dans musee.json : rien n'est recalculé, aucun fichier son.
    let SON = null;
    function niveauMusique(e) {
      const X = 8, Z1 = 3, Z2 = -21, CZ = -9, HM = 5.2, D = chant.oeuvres, n = D.length;
      salleSimple(e, X, Z1, Z2, HM, false); cage(e, 0, 1.7, -1);
      for (const [x, z] of [[0, CZ], [0, -17], [-X + 2, -9], [X - 2, -9], [0, -2]]) { const l = new THREE.PointLight(0xfff3df, 0.4, 13, 1.6); l.position.set(x, HM - 0.4, z); e.g.add(l); }
      CARTELS.chant = { ...T.chant, html: verifier(chant) }; CARTELS.partition = { ...T.partition_c, html: verifier(chant) };
      const bits = (a, b) => [...a.toString(2).padStart(5, '0'), ...b.toString(2).padStart(5, '0')].map(Number);
      const uni = (h) => h.r.every((x) => x) && h.r.every((x) => x[0] === h.r[0][0] && x[1] === h.r[0][1]);
      let jour = n - 1, joue = false, colJ = -1, tempsJ = -1;
      const vive = (w, h, f) => { const c = document.createElement('canvas'); c.width = w; c.height = h; const t = new THREE.CanvasTexture(c); t.encoding = THREE.sRGBEncoding; t.anisotropy = 4; const maj = () => { f(c.getContext('2d'), w, h); t.needsUpdate = true; }; maj(); return { t, maj }; };
      const MB = (t) => new THREE.MeshBasicMaterial({ map: t, toneMapped: false });
      const BOIS = new THREE.MeshStandardMaterial({ color: 0x7b4a2c, roughness: 0.7, side: THREE.DoubleSide }), LAITON = new THREE.MeshStandardMaterial({ color: 0xb08d57, metalness: 0.5, roughness: 0.4 });
      if (chant.reclame) panneau(e, Creclame(chant.reclame[LG]), lignesReclame(chant.reclame[LG]), 2.4, 1.6, -X + 0.13, 1.9, -1.6, Math.PI / 2, optReclame);
      // la place et ses six tambours
      const tapis = new THREE.Mesh(new THREE.CircleGeometry(3.6, 64), new THREE.MeshStandardMaterial({ color: 0x3b403d, roughness: 1 })); tapis.rotation.x = -Math.PI / 2; tapis.position.set(0, 0.006, CZ); e.g.add(tapis);
      const tamb = [];
      REGIONS.forEach((nom, r) => {
        const a = -Math.PI / 2 + r * Math.PI / 3 + Math.PI / 6, x = Math.cos(a) * 2.6, z = CZ + Math.sin(a) * 2.6;
        const gr = new THREE.Group(); gr.position.set(x, 0, z); e.g.add(gr);
        const corps = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.44, 0.82, 28, 1, true), BOIS); corps.position.y = 0.41; gr.add(corps);
        for (const y of [0.06, 0.78]) { const c = new THREE.Mesh(new THREE.TorusGeometry(y < 0.5 ? 0.445 : 0.505, 0.022, 8, 32), LAITON); c.rotation.x = Math.PI / 2; c.position.y = y; gr.add(c); }
        const peau = new THREE.Mesh(new THREE.CylinderGeometry(0.49, 0.49, 0.03, 32), new THREE.MeshStandardMaterial({ color: 0xe8dfc8, roughness: 0.8, emissive: 0xc9a447, emissiveIntensity: 0 })); peau.position.y = 0.83; gr.add(peau);
        const pq = new THREE.Mesh(new THREE.PlaneGeometry(0.62, 0.155), MB(new THREE.CanvasTexture(toile(256, 64, (g, w, h) => { g.fillStyle = '#1b2124'; g.fillRect(0, 0, w, h); g.fillStyle = '#f6f6f2'; g.font = '700 30px system-ui, sans-serif'; g.textAlign = 'center'; g.fillText(region(nom), w / 2, 42); }))));
        const pg = new THREE.Group(); pg.rotation.y = Math.atan2(-x, -(z - CZ)) + Math.PI; pq.position.set(0, 0.45, 0.52); pg.add(pq); gr.add(pg);
        peau.userData.son = 'ecouter'; corps.userData.son = 'ecouter'; e.cibles.push(peau, corps);
        e.obs.push({ x1: x - 0.5, x2: x + 0.5, z1: z - 0.5, z2: z + 0.5 }); tamb.push({ peau, coup: 0, x, z });
      });
      // le pupitre « Écouter le soir », entre l'ascenseur et la place
      const pup = new THREE.Group(); pup.position.set(0, 0, CZ + 4.6); e.g.add(pup);
      const pied = new THREE.Mesh(new THREE.BoxGeometry(0.08, 1, 0.08), CADRE); pied.position.y = 0.5; pup.add(pied);
      const cart = vive(512, 320, (g, w, h) => {
        const d = D[jour]; g.fillStyle = '#fbfbf8'; g.fillRect(0, 0, w, h); g.fillStyle = '#1b2124'; g.font = '700 44px Georgia, serif'; g.fillText(joue ? T.arreter : T.ecouter, 28, 70);
        g.font = '400 25px system-ui, sans-serif'; g.fillStyle = '#4c5558'; g.fillText(T.soir_du(dateCourte(d.date), d.edition), 28, 118); g.fillStyle = '#1b2124';
        ecrire(g, T.pupitre, 28, 166, 456, 32);
      });
      const cm = new THREE.Mesh(new THREE.PlaneGeometry(0.72, 0.45), MB(cart.t)); cm.position.set(0, 1.08, 0); cm.rotation.x = -0.6; cm.userData.son = 'ecouter'; pup.add(cm); e.cibles.push(cm);
      e.obs.push({ x1: -0.2, x2: 0.2, z1: CZ + 4.4, z2: CZ + 4.8 });
      // la partition du soir, au fond (24 heures × 6 régions × 10 temps, comme un rouleau de piano mécanique)
      const FW = 2048, FH = 700;
      const fr = vive(FW, FH, (g, w, h) => {
        const d = D[jour], P = d.partition; g.fillStyle = '#fbfbf8'; g.fillRect(0, 0, w, h); g.fillStyle = '#1b2124'; g.font = '700 46px Georgia, serif'; g.fillText(T.partition + ' · ' + dateCourte(d.date), 24, 56);
        g.font = '400 22px system-ui, sans-serif'; g.fillStyle = '#4c5558'; g.fillText(T.partition_l, 24, 90);
        const x0 = 150, y0 = 130, cw = (w - x0 - 20) / P.length, rh = 78;
        P.forEach((hh, ih) => {
          const x = x0 + ih * cw;
          if (ih === colJ) { g.fillStyle = 'rgba(201,164,71,.28)'; g.fillRect(x, y0 - 30, cw, 6 * rh + 60); }
          g.fillStyle = '#4c5558'; g.font = '400 18px system-ui, sans-serif'; g.textAlign = 'center'; g.fillText(hh.h + ' h', x + cw / 2, y0 - 8); g.textAlign = 'left';
          hh.r.forEach((m, r) => {
            const y = y0 + r * rh; if (!m) { g.fillStyle = '#c5cac5'; g.fillRect(x + 6, y + rh / 2 - 1, cw - 12, 2); return; }
            bits(m[0], m[1]).forEach((v, b) => { const cx = x + 4 + b * (cw - 8) / 10, ww = (cw - 8) / 10 - 1.5; g.fillStyle = v ? (ih === colJ && b === tempsJ ? '#c9a447' : '#1b2124') : '#e2e5e0'; g.fillRect(cx, y + 8, ww, rh - 30); });
            g.fillStyle = '#4c5558'; g.font = '400 13px system-ui, sans-serif'; g.fillText(m[2], x + 4, y + rh - 8);
          });
          if (uni(hh)) { g.fillStyle = '#1f7a46'; g.fillRect(x + 4, y0 + 6 * rh + 4, cw - 8, 6); }
        });
        g.font = '700 20px system-ui, sans-serif'; g.fillStyle = '#1b2124'; REGIONS.forEach((nm, r) => g.fillText(region(nm), 14, y0 + r * rh + rh / 2 + 4));
      });
      const LP = 13.2, HP = LP * FH / FW; boiteE(e, LP + 0.2, HP + 0.2, 0.05, 0, 2.55, Z2 + 0.13, CADRE, false);
      const frm = new THREE.Mesh(new THREE.PlaneGeometry(LP, HP), MB(fr.t)); frm.position.set(0, 2.55, Z2 + 0.16); e.g.add(frm); cible(e, frm, 'partition');
      // le mur des soirs (à droite) : une barre par soir, hauteur = heures à l'unisson ; toucher une barre joue ce soir-là
      const barres = [], pas = Math.min(0.9, 18 / n), VERT = 0x1f7a46, OR = 0xc9a447;
      D.forEach((d, k) => {
        const hg = 0.12 + 3 * (d.unisson || 0) / 24; const b = new THREE.Mesh(new THREE.BoxGeometry(0.28, hg, pas * 0.62), new THREE.MeshStandardMaterial({ color: VERT, roughness: 0.6 }));
        b.position.set(X - 0.26, 0.9 + hg / 2, CZ - (n - 1) * pas / 2 + k * pas); b.userData.son = 'jour'; b.userData.k = k; e.g.add(b); e.cibles.push(b); barres.push(b);
      });
      const mm = new THREE.Mesh(new THREE.PlaneGeometry(6.1, 0.9), MB(new THREE.CanvasTexture(toile(2048, 300, (g, w, h) => {
        g.fillStyle = '#f6f6f2'; g.fillRect(0, 0, w, h); g.fillStyle = '#1b2124'; g.font = '700 60px Georgia, serif'; g.fillText(T.unisson_mur, 30, 80);
        g.font = '400 32px system-ui, sans-serif'; g.fillStyle = '#4c5558'; g.fillText(T.unisson_txt, 30, 145);
        g.font = '700 36px system-ui, sans-serif'; g.fillStyle = '#1b2124'; g.fillText(dateCourte(D[0].date) + SEP + T.unisson(D[0].unisson, D[0].heures) + (n > 1 ? '   →   ' + dateCourte(D[n - 1].date) + SEP + T.unisson(D[n - 1].unisson, D[n - 1].heures) : ''), 30, 225);
      }))));
      mm.position.set(X - 0.12, 4.4, CZ); mm.rotation.y = -Math.PI / 2; e.g.add(mm);
      const LW = Math.min(4096, n * 200);
      const dts = new THREE.Mesh(new THREE.PlaneGeometry(n * pas, n * pas * 64 / LW), MB(new THREE.CanvasTexture(toile(LW, 64, (g, w, h) => { g.fillStyle = '#f6f6f2'; g.fillRect(0, 0, w, h); g.fillStyle = '#4c5558'; g.font = '400 30px system-ui, sans-serif'; g.textAlign = 'center'; D.forEach((d, k) => { if (n < 12 || k % 2 === 0 || k === n - 1) g.fillText(dateCourte(d.date), (k + 0.5) * w / n, 44); }); }))));
      dts.position.set(X - 0.12, 0.68, CZ); dts.rotation.y = -Math.PI / 2; e.g.add(dts);
      // le critique (à gauche) : ses deux lignes, puis ce qui est vrai
      const cr = vive(1024, 660, (g, w, h) => {
        const d = D[jour], l = ((d.critique || {})[LG]) || [];
        g.fillStyle = '#fbfbf8'; g.fillRect(0, 0, w, h); g.fillStyle = '#1b2124'; g.font = '700 64px Georgia, serif'; g.fillText(T.critique, 48, 92);
        g.font = 'italic 400 44px Georgia, serif'; let y = ecrire(g, l[0] || '', 48, 180, 928, 56);
        g.font = '400 32px system-ui, sans-serif'; y = ecrire(g, l.slice(1).join(' '), 48, y + 16, 928, 44);
        g.fillStyle = '#1f7a46'; g.fillRect(48, y + 10, 928, 4); g.fillStyle = '#1b2124'; g.font = '700 30px system-ui, sans-serif'; g.fillText(T.vrai, 48, y + 64);
        g.font = '400 30px system-ui, sans-serif'; ecrire(g, T.chant.v, 48, y + 108, 928, 40);
      });
      const crm = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 2.06), MB(cr.t)); crm.position.set(-X + 0.13, 2.0, CZ); crm.rotation.y = Math.PI / 2; e.g.add(crm); cible(e, crm, 'chant');
      panneau(e, 'chant', [T.chant.t, T.chant.d + ' · ' + T.lire], 0.62, 0.3, -X + 0.13, 0.95, CZ + 2.1, Math.PI / 2, { titre: 44, corps: 30 });
      // le son : six timbres fabriqués par le navigateur, placés sur les tambours
      const sonBtn = $('#m3-son'), sonH = $('#m3-heure');
      let ctx = null, br = null, timer = null, pasT = 0, suivant = 0, att = [], pans = [];
      const TT = 0.2, HEURE = 12;
      const env = (gn, t, v, d) => { gn.gain.setValueAtTime(0.0001, t); gn.gain.exponentialRampToValueAtTime(v, t + 0.004); gn.gain.exponentialRampToValueAtTime(0.0001, t + d); };
      const osc = (o2, t, f0, f1, d, v, ty) => { const o = ctx.createOscillator(), gn = ctx.createGain(); o.type = ty || 'sine'; o.frequency.setValueAtTime(f0, t); o.frequency.exponentialRampToValueAtTime(f1, t + d); env(gn, t, v, d); o.connect(gn).connect(o2); o.start(t); o.stop(t + d + 0.02); };
      const souffle = (o2, t, ty, f, q, d, v) => { const s = ctx.createBufferSource(), fl = ctx.createBiquadFilter(), gn = ctx.createGain(); s.buffer = br; fl.type = ty; fl.frequency.value = f; fl.Q.value = q; env(gn, t, v, d); s.connect(fl).connect(gn).connect(o2); s.start(t); s.stop(t + d + 0.02); };
      const TIMBRE = [(o, t) => osc(o, t, 110, 45, 0.22, 0.7), (o, t) => souffle(o, t, 'bandpass', 1800, 8, 0.06, 1.2), (o, t) => { osc(o, t, 820, 800, 0.18, 0.1, 'square'); osc(o, t, 1230, 1210, 0.15, 0.08, 'square'); }, (o, t) => osc(o, t, 70, 38, 0.4, 0.8), (o, t) => souffle(o, t, 'highpass', 6000, 1, 0.09, 0.5), (o, t) => souffle(o, t, 'bandpass', 1100, 1.5, 0.05, 1.1)];
      const sortie = (r) => { const p = ctx.createPanner(); p.panningModel = 'equalpower'; p.distanceModel = 'inverse'; p.refDistance = 2.2; p.rolloffFactor = 1.1; const t = tamb[r]; if (p.positionX) { p.positionX.value = t.x; p.positionY.value = 0.9; p.positionZ.value = t.z; } else p.setPosition(t.x, 0.9, t.z); p.connect(ctx.destination); return p; };
      const etat = () => { sonBtn.textContent = joue ? T.arreter : T.ecouter; sonBtn.classList.toggle('on', joue); cart.maj(); };
      function planifier() {
        const P = D[jour].partition, total = P.length * HEURE;
        while (suivant < ctx.currentTime + 0.15) {
          if (pasT >= total) { arreter(); return; }
          const ih = Math.floor(pasT / HEURE), b = pasT % HEURE, h = P[ih], t = suivant, fr2 = [];
          if (b < 10) h.r.forEach((x, r) => { if (x && bits(x[0], x[1])[b]) { TIMBRE[r](pans[r], t); fr2.push(r); } });
          att.push(setTimeout(() => { if (!joue) return; fr2.forEach((r) => { tamb[r].coup = 1; }); colJ = ih; tempsJ = b < 10 ? b : -1; fr.maj(); sonH.textContent = h.h + ' h · ' + (b < 10 ? (b + 1) + '/10' : '—'); }, Math.max(0, (t - ctx.currentTime) * 1000)));
          pasT++; suivant += TT;
        }
      }
      function lancer() {
        const AC = window.AudioContext || window.webkitAudioContext; if (!AC) return;
        ctx = ctx || new AC(); ctx.resume();
        if (!br) { br = ctx.createBuffer(1, ctx.sampleRate * 0.5, ctx.sampleRate); const a = br.getChannelData(0); let s = 12345; for (let i = 0; i < a.length; i++) { s = (s * 1103515245 + 12345) >>> 0; a[i] = s / 2147483648 - 1; } }
        if (!pans.length) pans = tamb.map((_, r) => sortie(r));
        arreter(); joue = true; pasT = 0; suivant = ctx.currentTime + 0.1; timer = setInterval(planifier, 40); etat();
      }
      function arreter() { const j = joue; joue = false; clearInterval(timer); att.forEach(clearTimeout); att = []; colJ = -1; tempsJ = -1; if (j) fr.maj(); sonH.textContent = ''; etat(); }
      function choisir(k) { jour = k; barres.forEach((b, i) => b.material.color.set(i === k ? OR : VERT)); fr.maj(); cr.maj(); cart.maj(); }
      sonBtn.onclick = () => (joue ? arreter() : lancer());
      SON = {
        clic: (quoi, k) => { if (quoi === 'jour') { choisir(k); lancer(); } else if (joue) arreter(); else lancer(); },
        arreter, fermer: () => { arreter(); if (ctx && ctx.close) ctx.close(); },
        etat: () => ({ joue, jour, colJ }),
      };
      e.anim.push((t, dt) => {
        if (ctx) {
          const l = ctx.listener, fw = new THREE.Vector3(0, 0, -1).applyQuaternion(camera.quaternion);
          if (l.positionX) { l.positionX.value = joueur.x; l.positionY.value = 1.62; l.positionZ.value = joueur.z; l.forwardX.value = fw.x; l.forwardY.value = fw.y; l.forwardZ.value = fw.z; l.upX.value = 0; l.upY.value = 1; l.upZ.value = 0; }
          else { l.setPosition(joueur.x, 1.62, joueur.z); l.setOrientation(fw.x, fw.y, fw.z, 0, 1, 0); }
        }
        tamb.forEach((tb) => { tb.peau.position.y = 0.83 - 0.025 * tb.coup; tb.peau.material.emissiveIntensity = 0.55 * tb.coup; tb.coup = Math.max(0, tb.coup - dt * 6); });
      });
      choisir(jour);
    }

    // ---------------------------------------------------------------- −5 : planétarium du cerveau (Bran, 13/11/2026)
    // Une salle noire : on marche au milieu du cerveau de citoyen du président en fonction (9 entrées, 6 neurones cachés,
    // 3 sorties, ses 81 poids publiés). Trois modes : propagation, rétropropagation (façon Hinton), récompense (façon Waïnas).
    // Les poids qui changent ici sont une copie : rien de ce qu'on fait dans la salle ne touche au vrai pays.
    let CERV = null;
    function niveauCerveau(e) {
      const g = e.g, X = 8, Z1 = 3, Z2 = -21, Hn = H * 2; Object.assign(e, { X, Z1, Z2 });
      CARTELS.cerveau = { ...T.cerveau(statue.nom), html: srcDe(statue.fichier) + (pres ? verifier(pres) : '') };
      const NOIR = new THREE.MeshBasicMaterial({ color: 0x030506 });
      const sol = new THREE.Mesh(new THREE.PlaneGeometry(2 * X, Z1 - Z2), new THREE.MeshBasicMaterial({ color: 0x020304 })); sol.rotation.x = -Math.PI / 2; sol.position.set(0, 0, (Z1 + Z2) / 2); g.add(sol);
      const gr = new THREE.GridHelper(24, 24, 0x2f8a52, 0x173b25); gr.position.set(0, 0.01, (Z1 + Z2) / 2); gr.material.transparent = true; gr.material.opacity = 0.6; gr.material.toneMapped = false; g.add(gr);
      const dome = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.IcosahedronGeometry(13, 1)), new THREE.LineBasicMaterial({ color: 0x5fe08f, transparent: true, opacity: 0.16, toneMapped: false })); dome.position.set(0, 0, -9); g.add(dome);
      boiteE(e, 0.2, Hn, Z1 - Z2, -X, Hn / 2, (Z1 + Z2) / 2, NOIR); boiteE(e, 0.2, Hn, Z1 - Z2, X, Hn / 2, (Z1 + Z2) / 2, NOIR); boiteE(e, 2 * X, Hn, 0.2, 0, Hn / 2, Z2, NOIR); boiteE(e, 2 * X, Hn, 0.2, 0, Hn / 2, Z1, NOIR);
      { const pos = [], r = mul(77); for (let i = 0; i < 1500; i++) { const a = r() * Math.PI * 2, b = Math.acos(r() * 0.9), R2 = 30; pos.push(Math.cos(a) * Math.sin(b) * R2, Math.cos(b) * R2 * 0.6 + 2, -9 + Math.sin(a) * Math.sin(b) * R2); }
        const gg = new THREE.BufferGeometry(); gg.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.add(new THREE.Points(gg, new THREE.PointsMaterial({ color: 0x9fb3c0, size: 0.05, toneMapped: false, transparent: true, opacity: 0.7 }))); }
      cage(e, 0, 1.7, -1);
      // les vrais poids du président en fonction : entier × 5 / 127, ordre w1[6][10] (biais en dernier) puis w2[3][7]
      const p = statue.poids.map((v) => v * 5 / 127);
      const W = [[...Array(6)].map((_, h) => p.slice(h * 10, h * 10 + 9)), [...Array(3)].map((_, o) => p.slice(60 + o * 7, 60 + o * 7 + 6))];
      const Bv = [[...Array(6)].map((_, h) => p[h * 10 + 9]), [...Array(3)].map((_, o) => p[60 + o * 7 + 6])];
      const L = [9, 6, 3], ZL = [-3.5, -9.5, -15.5], RL = [3.2, 3.6, 2.2], rnd = mul(5);
      const nodes = L.map((n, c) => [...Array(n)].map((_, i) => { const a = i / n * Math.PI * 2 + (c === 1 ? 0.3 : 0); return new THREE.Vector3(Math.cos(a) * RL[c], 2.1 + Math.sin(a) * RL[c] * 0.55, ZL[c] + Math.sin(a * 2) * 0.4); }));
      const RIM = new THREE.ShaderMaterial({ uniforms: { c: { value: new THREE.Color(0x5fe08f) }, k: { value: 0.3 } }, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
        vertexShader: 'varying vec3 vN;varying vec3 vV;void main(){vec4 mv=modelViewMatrix*vec4(position,1.);vN=normalize(normalMatrix*normal);vV=normalize(-mv.xyz);gl_Position=projectionMatrix*mv;}',
        fragmentShader: 'uniform vec3 c;uniform float k;varying vec3 vN;varying vec3 vV;void main(){float f=pow(1.-abs(dot(vN,vV)),2.2);gl_FragColor=vec4(c*(.5+1.3*k)*f,1.);}' });
      const sph = nodes.map((col) => col.map((v) => { const m = new THREE.Mesh(new THREE.SphereGeometry(0.3, 32, 20), RIM.clone()); m.position.copy(v); g.add(m); cible(e, m, 'cerveau'); return m; }));
      const aretes = []; for (let c = 0; c < 2; c++) for (let j = 0; j < L[c + 1]; j++) for (let i = 0; i < L[c]; i++) aretes.push({ c, i, j, a: nodes[c][i], b: nodes[c + 1][j] });
      const lp = new Float32Array(aretes.length * 6), lc = new Float32Array(aretes.length * 6); aretes.forEach((r, n) => { lp.set([r.a.x, r.a.y, r.a.z, r.b.x, r.b.y, r.b.z], n * 6); });
      const lg = new THREE.BufferGeometry(); lg.setAttribute('position', new THREE.BufferAttribute(lp, 3)); lg.setAttribute('color', new THREE.BufferAttribute(lc, 3));
      g.add(new THREE.LineSegments(lg, new THREE.LineBasicMaterial({ vertexColors: true, transparent: true, opacity: 0.5, toneMapped: false, blending: THREE.AdditiveBlending, depthWrite: false })));
      const pp = new Float32Array(aretes.length * 3), pc = new Float32Array(aretes.length * 3); const pg = new THREE.BufferGeometry(); pg.setAttribute('position', new THREE.BufferAttribute(pp, 3)); pg.setAttribute('color', new THREE.BufferAttribute(pc, 3));
      g.add(new THREE.Points(pg, new THREE.PointsMaterial({ size: 0.14, vertexColors: true, transparent: true, toneMapped: false, blending: THREE.AdditiveBlending, depthWrite: false, map: new THREE.CanvasTexture(toile(64, 64, (gg, w, h) => { const d = gg.createRadialGradient(32, 32, 0, 32, 32, 32); d.addColorStop(0, '#fff'); d.addColorStop(0.4, 'rgba(255,255,255,.6)'); d.addColorStop(1, 'rgba(255,255,255,0)'); gg.fillStyle = d; gg.fillRect(0, 0, w, h); })) })));
      const op = { fond: '#0c1113', encre: '#e8ece9', doux: '#b9c3be', titre: 46, corps: 28 };
      panneau(e, 'cerveau', T.pl[0], 2.2, 1.3, -X + 0.11, 1.9, -3, Math.PI / 2, op);
      panneau(e, 'cerveau', [T.cerveau(statue.nom).t, T.cerveau(statue.nom).d + ' · ' + T.lire], 2.2, 0.8, -X + 0.11, 1.9, -9, Math.PI / 2, op);
      panneau(e, 'cerveau', T.pl[1], 2.0, 1.0, X - 0.11, 1.9, -5, -Math.PI / 2, op);
      panneau(e, 'cerveau', T.pl[2], 2.0, 1.15, X - 0.11, 1.9, -10, -Math.PI / 2, op);
      panneau(e, 'cerveau', T.pl[3], 2.0, 1.1, X - 0.11, 1.9, -15, -Math.PI / 2, op);
      CERV = { nodes, sph, W, Bv, aretes, lg, pg, L, x: [...Array(9)].map(() => rnd()), h: [], o: [], mode: 'prop', t0: 0, rnd };
      e.anim.push(animerCerveau);
    }
    const borne = (v) => Math.max(-5, Math.min(5, v));
    function cerveauCalcul(Cv) { Cv.h = Cv.W[0].map((r, j) => Math.tanh(r.reduce((t, w, i) => t + w * Cv.x[i], Cv.Bv[0][j]))); Cv.o = Cv.W[1].map((r, j) => Math.tanh(r.reduce((t, w, i) => t + w * Cv.h[i], Cv.Bv[1][j]))); }
    function animerCerveau(t) {
      const Cv = CERV; if (!Cv) return;
      const etape = Math.floor(t / 2600);
      if (etape !== Cv.t0) {
        Cv.t0 = etape; Cv.x = Cv.x.map(() => (Cv.rnd() < 0.45 ? 1 : 0)); cerveauCalcul(Cv);
        if (Cv.mode === 'retro') {
          const cib = Math.floor(Cv.rnd() * 3), err = Cv.o.map((o, j) => (j === cib ? 1 : -1) - o), lr = 0.15;
          const d2 = err.map((e2, j) => e2 * (1 - Cv.o[j] ** 2)); const d1 = Cv.h.map((h, i) => (1 - h * h) * d2.reduce((t2, d, j) => t2 + d * Cv.W[1][j][i], 0));
          Cv.W[1].forEach((r, j) => r.forEach((w, i) => { r[i] = borne(w + lr * d2[j] * Cv.h[i]); })); Cv.W[0].forEach((r, j) => r.forEach((w, i) => { r[i] = borne(w + lr * d1[j] * Cv.x[i]); }));
          $('#m3-info').textContent = T.info_retro(cib + 1, (err.reduce((a, b) => a + b * b, 0) / 3).toFixed(2));
        } else if (Cv.mode === 'recomp') {
          const act = Cv.o.indexOf(Math.max(...Cv.o)), bien = act === (Cv.x[0] + Cv.x[1] > Cv.x[7] + Cv.x[8] ? 0 : 2), r = bien ? 1 : -1, lr = 0.12;
          Cv.W[1][act].forEach((w, i) => { Cv.W[1][act][i] = borne(w + lr * r * Cv.h[i]); }); Cv.W[0].forEach((row, j) => row.forEach((w, i) => { if (Cv.x[i]) row[i] = borne(w + lr * 0.5 * r * Cv.h[j] * Math.sign(Cv.W[1][act][j])); }));
          $('#m3-info').textContent = T.info_recomp(act + 1, bien);
        } else $('#m3-info').textContent = T.info_prop;
      }
      const inv = Cv.mode === 'retro', val = [Cv.x, Cv.h, Cv.o];
      Cv.sph.forEach((col, c) => col.forEach((m, i) => { m.material.uniforms.k.value = Math.abs(val[c][i] || 0); if (inv) m.material.uniforms.c.value.setRGB(0.94, 0.71, 0.3); else m.material.uniforms.c.value.setRGB(0.37, 0.88, 0.56); }));
      const lc = Cv.lg.attributes.color, pp = Cv.pg.attributes.position, pc = Cv.pg.attributes.color;
      Cv.aretes.forEach((r, n) => {
        const w = Cv.W[r.c][r.j][r.i], f = Math.min(1, Math.abs(w) / 1.2), col = w >= 0 ? [0.37, 0.88, 0.56] : [0.94, 0.71, 0.3];
        lc.setXYZ(2 * n, col[0] * f, col[1] * f, col[2] * f); lc.setXYZ(2 * n + 1, col[0] * f, col[1] * f, col[2] * f);
        const src = r.c === 0 ? Cv.x[r.i] : Math.abs(Cv.h[r.i] || 0), u = ((t / 1400) + n * 0.137) % 1, k = inv ? 1 - u : u;
        pp.setXYZ(n, r.a.x + (r.b.x - r.a.x) * k, r.a.y + (r.b.y - r.a.y) * k, r.a.z + (r.b.z - r.a.z) * k); const b = inv ? 0.9 : src * f; pc.setXYZ(n, inv ? b : 0.7 * b, inv ? 0.45 * b : b, inv ? 0.3 * b : 0.8 * b);
      });
      lc.needsUpdate = true; pp.needsUpdate = true; pc.needsUpdate = true;
    }
    boite.querySelectorAll('.m3-mode').forEach((b) => { b.onclick = () => { boite.querySelectorAll('.m3-mode').forEach((x) => x.classList.toggle('on', x === b)); if (CERV) { CERV.mode = b.dataset.m; CERV.t0 = -1; } }; });

    // ---------------------------------------------------------------- +1 : la réserve du Créateur (cachée : par la vis du panneau seulement)
    function reserve(e) {
      salleSimple(e, 5, 3, -19); cage(e, 0, 1.7, -1);
      Object.assign(CARTELS, T.R);
      const G = -5 + 0.11, Dr = 5 - 0.11, F = -19 + 0.11, RG = Math.PI / 2, RD = -Math.PI / 2;
      const et = (id, x, y, z, ry) => panneau(e, id, [T.R[id].t, T.R[id].d + ' · ' + T.lire], 0.46, 0.22, x, y, z, ry, { titre: 44, corps: 30 });
      boiteE(e, 1.5, 2.1, 0.18, 0, 1.05, -2.8, SOCLE);
      panneau(e, 'ancetres', [T.R.ancetres.t, T.R.ancetres.d, ...T.R.ancetres.m.slice(0, 3)], 1.36, 1.86, 0, 1.05, -2.8 + 0.095, 0, { titre: 72, corps: 34 });
      photo(e, 'fusee', 'fusee', 1.05, G, 1.75, -4.5, RG); et('fusee', G + 0.01, 1.0, -4.5 + 0.95, RG);
      photo(e, 'bateau', 'bateau', 1.6, G, 1.7, -8.2, RG); et('bateau', G + 0.01, 1.0, -8.2 + 1.15, RG);
      photo(e, 'robo', 'robo', 1.25, G, 1.7, -11.8, RG); et('robo', G + 0.01, 1.0, -11.8 + 0.95, RG);
      photo(e, 'flipper', 'flipper', 1.25, G, 1.85, -15.8, RG); et('flipper', G + 0.01, 1.0, -15.8 + 0.95, RG);
      photo(e, 'radio', 'radio', 2, -2.3, 1.75, F, 0); et('radio', -2.3 + 1.25, 1.0, F + 0.01, 0);
      photo(e, 'brosse', 'brosse', 1.5, 1.6, 2.05, F, 0); et('brosse', 1.6 + 1.0, 1.0, F + 0.01, 0);
      const video = document.createElement('video'); video.src = BASE + 'musee-reserve/brosse.mp4'; video.muted = true; video.loop = true; video.playsInline = true; video.setAttribute('playsinline', ''); video.autoplay = true; video.play().catch(() => {});
      const vt = new THREE.VideoTexture(video); vt.encoding = THREE.sRGBEncoding;
      const pv = new THREE.Mesh(new THREE.PlaneGeometry(0.54, 0.96), new THREE.MeshBasicMaterial({ map: vt, toneMapped: false })); pv.position.set(3.6, 1.35, F + 0.06); e.g.add(pv); cible(e, pv, 'brosse');
      boiteE(e, 0.62, 1.06, 0.06, 3.6, 1.35, F + 0.03, CADRE, false);
      e.video = video;
      photo(e, 'borne', 'borne', 1.9, Dr, 1.85, -15.5, RD); et('borne', Dr - 0.01, 1.0, -15.5 - 1.2, RD);
      photo(e, 'jeu', 'jeu', 1.15, Dr, 1.75, -12.1, RD); et('jeu', Dr - 0.01, 1.0, -12.1 - 0.85, RD);
      photo(e, 'aramis', 'aramis', 0.55, Dr, 1.9, -10.4, RD); et('aramis', Dr - 0.01, 1.35, -10.4, RD);
      photo(e, 'table', 'table', 1.05, Dr, 1.8, -6.9, RD); et('table', Dr - 0.01, 1.0, -6.9 - 0.8, RD);
      photo(e, 'table', 'dessous', 1.3, Dr, 1.6, -4.3, RD);
    }

    // ---------------------------------------------------------------- les autres visiteurs (idée de Bran, 13/11/2026)
    // N personnes dans le musée 3D = N−1 silhouettes grises et autant de points orange sur le plan de l'entrée.
    // Le NOMBRE est réel (petit compteur Cloudflare sur l'adresse du site, voir worker-visiteurs) ; les PLACES sont tirées
    // au hasard : le musée ne montre jamais où sont les gens. Jamais dans la réserve. Au plus 30 silhouettes, qui s'effacent
    // quand on s'approche. Sans réponse du compteur : aucune silhouette, aucun chiffre (jamais de faux visiteurs).
    const VIS = (() => {
      const MAXS = 30, FANT = [], NIVX = Object.keys(DEF).filter((id) => id !== '-1'), rnd = mul((Math.random() * 1e9) | 0);
      const MATF = new THREE.MeshStandardMaterial({ color: 0x4a5154, roughness: 0.85, transparent: true, opacity: 0.6 });
      const GC = new THREE.CylinderGeometry(0.17, 0.22, 1.15, 12), GT = new THREE.SphereGeometry(0.13, 14, 10);
      const EX = typeof window.MCL_VISITEURS_ESSAI === 'number';   // aperçu hors du site seulement : nombre d'exemple, annoncé comme tel
      const SITE = /(^|\.)microcontroland\.org$/.test(location.hostname) && !/[?&]essai\b/.test(location.search);
      const DNT = navigator.doNotTrack === '1' || window.doNotTrack === '1' || navigator.globalPrivacyControl === true;
      const ID = Array.from(crypto.getRandomValues(new Uint8Array(8)), (b) => b.toString(16).padStart(2, '0')).join('');   // en mémoire seulement
      let n = EX ? window.MCL_VISITEURS_ESSAI : null, rates = 0, minuterie = null, affiche;
      const libreE = (e, x, z) => !e.obs.some((o) => x > o.x1 - 0.35 && x < o.x2 + 0.35 && z > o.z1 - 0.35 && z < o.z2 + 0.35);
      function pointAuHasard(id) {
        const D = DEF[id], e = ETAGES[id];
        for (let q = 0; q < 40; q++) {
          let x, z;
          if (D.n != null) { const c = e && e.damier ? e.damier : spirale(D.n + 1), [cx, cz] = c[Math.floor(rnd() * c.length)]; x = cx * CASE + (rnd() - 0.5) * 8; z = cz * CASE + (rnd() - 0.5) * 8; }
          else { x = (rnd() * 2 - 1) * (D.X - 1); z = D.Z2 + 1 + rnd() * (D.Z1 - D.Z2 - 2); }
          if (!e || libreE(e, x, z)) return [x, z];
        }
        return e ? [e.depart.x, e.depart.z] : [0, 0];
      }
      function mettre(f) {   // une silhouette n'a de corps que dans un niveau déjà construit
        const e = ETAGES[f.id]; if (!e || f.gr) return;
        if (!libreE(e, f.x, f.z)) [f.x, f.z] = pointAuHasard(f.id);
        f.mf = MATF.clone(); f.gr = new THREE.Group();
        const c = new THREE.Mesh(GC, f.mf); c.position.y = 0.78; f.gr.add(c); const t = new THREE.Mesh(GT, f.mf); t.position.y = 1.52; f.gr.add(t);
        f.gr.position.set(f.x, 0, f.z); e.g.add(f.gr); f.but = pointAuHasard(f.id);
      }
      function ajuster() {
        const voulu = n == null ? 0 : Math.max(0, Math.min(MAXS, n - 1));
        while (FANT.length < voulu) { const id = NIVX[Math.floor(rnd() * NIVX.length)], [x, z] = pointAuHasard(id); const f = { id, x, z, but: pointAuHasard(id), pause: rnd() * 4, v: 0.8 + rnd() * 0.5, ph: rnd() * 6, gr: null }; mettre(f); FANT.push(f); }
        while (FANT.length > voulu) { const f = FANT.pop(); if (f.gr) { f.gr.parent.remove(f.gr); f.mf.dispose(); } }
        if (affiche) affiche();
      }
      function signal(m) {
        if (!SITE) return;
        fetch('/musee-visiteurs' + (m === 'GET' ? '' : '?id=' + ID), { method: m, cache: 'no-store', keepalive: m === 'DELETE' })
          .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
          .then((j) => { if (m !== 'DELETE' && Number.isInteger(j.n)) { n = Math.max(DNT ? j.n + 1 : j.n, 1); rates = 0; ajuster(); } })
          .catch(() => { if (++rates >= 2) { n = null; ajuster(); } });
      }
      const battre = () => { if (!document.hidden) signal(DNT ? 'GET' : 'POST'); };
      if (SITE) { battre(); minuterie = setInterval(battre, 60000); }
      return {
        compteur(e, x, y, z) {   // « Visiteurs en ce moment : N », sous le plan
          const cv = document.createElement('canvas'); cv.width = 768; cv.height = 96; const t = new THREE.CanvasTexture(cv); t.encoding = THREE.sRGBEncoding;
          const m = new THREE.Mesh(new THREE.PlaneGeometry(0.62, 0.078), new THREE.MeshBasicMaterial({ map: t, toneMapped: false })); m.position.set(x, y, z); e.g.add(m); cible(e, m, 'plan');
          affiche = () => { const g = cv.getContext('2d'); g.fillStyle = '#f7f8f5'; g.fillRect(0, 0, 768, 96); g.fillStyle = '#b36b12'; g.font = '600 38px system-ui, sans-serif'; g.textBaseline = 'middle'; g.fillText(T.visiteurs(n, EX), 22, 50); t.needsUpdate = true; m.visible = n != null; };
          affiche();
          const pts = new THREE.BufferGeometry(); pts.setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(3 * (MAXS + 2)), 3));
          const p = new THREE.Points(pts, new THREE.PointsMaterial({ color: 0xffb347, size: 0.018, toneMapped: false, transparent: true })); p.renderOrder = 4; p.frustumCulled = false;
          return { pts, p };
        },
        niveau() { ajuster(); for (const f of FANT) mettre(f); },
        animer(t, dt) {
          for (const f of FANT) {
            if (f.gr && f.id === courant.id) { const d = Math.hypot(f.x - joueur.x, f.z - joueur.z); f.mf.opacity = Math.max(0.06, Math.min(0.6, (d - 1.2) / 3)); }
            if (f.pause > 0) { f.pause -= dt; continue; }
            const dx = f.but[0] - f.x, dz = f.but[1] - f.z, d = Math.hypot(dx, dz);
            if (d < 0.3) { f.but = pointAuHasard(f.id); f.pause = 2 + rnd() * 6; continue; }   // s'arrête devant une œuvre, puis repart
            const nx = f.x + dx / d * f.v * dt, nz = f.z + dz / d * f.v * dt, e = ETAGES[f.id];
            if (!e || libreE(e, nx, nz)) { f.x = nx; f.z = nz; if (f.gr) { f.gr.position.set(f.x, Math.abs(Math.sin(t / 260 + f.ph)) * 0.03, f.z); f.gr.rotation.y = Math.atan2(-dx, -dz); } }
            else f.but = pointAuHasard(f.id);
          }
          if (PLAN && PLAN.compteur && courant.id === '0') {
            const P = PLAN.compteur; if (!P.p.parent) PLAN.dec.add(P.p);
            const a = P.pts.attributes.position; let i = 0;
            for (const f of FANT) { const D = DEF[f.id], cz = D.n != null ? 1.0 : D.cz; a.setXYZ(i++, f.x * PLAN.k, PLAN.Y[f.id] + PLAN.hN * 0.5, (f.z - cz) * PLAN.k); }
            for (; i < MAXS + 2; i++) a.setXYZ(i, 0, -9, 0); a.needsUpdate = true;
          }
        },
        etat: () => ({ n, silhouettes: FANT.length, ici: FANT.filter((f) => f.id === courant.id).length, niveaux: [...new Set(FANT.map((f) => f.id))] }),
        fermer() { if (minuterie) clearInterval(minuterie); if (SITE && !DNT) signal('DELETE'); },
      };
    })();

    // ---------------------------------------------------------------- lumière : cycle selon l'heure du visiteur (Bran, 2/11/2026 ; repris dans le bunker le 16/11)
    // Nuit avant 6 h et après 22 h ; aube de 6 h à 8 h ; jour jusqu'à 17 h 30 ; soir jusqu'à 20 h ; tombée de la nuit jusqu'à 22 h.
    // Le bouton choisit « votre heure », jour, soir ou nuit (choix gardé dans le navigateur seulement). Le planétarium (−5) reste noir.
    const LUM = (() => {
      const AMB = {
        jour: { hemi: 0.75, c: 0xfffbf0, soleil: 0.5, fond: 0xdfe2dd, vue: 0xffffff, lampes: 1, expo: 1.05, halo: 0.1 },
        soir: { hemi: 0.5, c: 0xffd9b0, soleil: 0.28, fond: 0xc9b9a6, vue: 0xd6b898, lampes: 1, expo: 1.0, halo: 0.25 },
        nuit: { hemi: 0.16, c: 0x9fb0d0, soleil: 0.0, fond: 0x1a1e24, vue: 0x3a4252, lampes: 0.7, expo: 0.88, halo: 0.45 },
      };
      const NOIR = { ...AMB.jour, fond: 0x030506 };   // −5 : le planétarium garde sa nuit d'étoiles à toute heure
      const MODES = ['auto', 'jour', 'soir', 'nuit'], mel = (a, b, t) => a + (b - a) * t, melC = (a, b, t) => new THREE.Color(a).lerp(new THREE.Color(b), t);
      function etatHeure(h) {
        if (h < 6 || h >= 22) return ['nuit', 'nuit', 0];
        if (h < 8) return ['nuit', 'jour', (h - 6) / 2];
        if (h < 17.5) return ['jour', 'jour', 0];
        if (h < 20) return ['jour', 'soir', (h - 17.5) / 2.5];
        return ['soir', 'nuit', (h - 20) / 2];
      }
      let mode = 'auto', e = null, vitres = [], lampes = [], halos = [];
      try { const m = localStorage.getItem('mcl-musee-lumiere'); if (MODES.includes(m)) mode = m; } catch (_) { /* stockage indisponible : votre heure */ }
      const bLum = $('#m3-lum');
      function eclairer() {
        if (!e) return;
        const d = new Date(), h = d.getHours() + d.getMinutes() / 60, [a, b, t] = mode === 'auto' ? etatHeure(h) : [mode, mode, 0];
        const A = e.id === '5' ? NOIR : AMB[a], B = e.id === '5' ? NOIR : AMB[b];
        HEMI.intensity = mel(A.hemi, B.hemi, t); HEMI.color = melC(A.c, B.c, t); soleil.intensity = mel(A.soleil, B.soleil, t);
        renderer.toneMappingExposure = mel(A.expo, B.expo, t);
        const f = melC(A.fond, B.fond, t); scene.background.copy(f); scene.fog.color.copy(f);
        const v = melC(A.vue, B.vue, t); for (const m of vitres) m.material.color.copy(v);
        const k = mel(A.lampes, B.lampes, t); for (const l of lampes) l.intensity = l.userData.base * k;
        const ho = mel(A.halo, B.halo, t); for (const m of halos) m.material.opacity = ho;
        bLum.textContent = T.lumiere[mode] + (mode === 'auto' ? ` (${String(d.getHours()).padStart(2, '0')} h ${String(d.getMinutes()).padStart(2, '0')})` : '');
      }
      bLum.onclick = () => { mode = MODES[(MODES.indexOf(mode) + 1) % MODES.length]; try { localStorage.setItem('mcl-musee-lumiere', mode); } catch (_) { /* rien */ } eclairer(); };
      const minuteur = setInterval(eclairer, 60000);
      return {
        niveau(n) {
          e = n; vitres = []; lampes = []; halos = [];
          n.g.traverse((o) => { if (o.userData.vitre) vitres.push(o); if (o.userData.halo) halos.push(o); if (o.isPointLight) { if (o.userData.base == null) o.userData.base = o.intensity; lampes.push(o); } });
          eclairer();
        },
        ajouter(m) { halos.push(m); eclairer(); },   // photos de la réserve, chargées après la construction du niveau
        mode(m) { if (MODES.includes(m)) { mode = m; eclairer(); } },
        etat: () => ({ mode, halos: halos.length, halo: halos[0] ? +halos[0].material.opacity.toFixed(2) : null, fond: '#' + scene.background.getHexString(), hemi: +HEMI.intensity.toFixed(3) }),
        fermer() { clearInterval(minuteur); },
      };
    })();

    // ---------------------------------------------------------------- changer d'échelle : la galaxie des dessins (clin d'œil à Elite)
    let univers = null, camU = null, echelle = null;
    const DESSINS = atelier ? atelier.dessins.filter(Boolean) : [];
    const NCASES = DESSINS.reduce((t, d) => t + d.length, 0);
    function construireUnivers() {
      const U = new THREE.Scene(); U.background = new THREE.Color(0x020306); const pos = [], col = [];
      DESSINS.forEach((d, i) => {
        const r = Math.floor(i / 20), k = i % 20, rayon = 5 + k * 2.4, ang = r * Math.PI / 3 + k * 0.2, cx = Math.cos(ang) * rayon, cz = Math.sin(ang) * rayon, cy = Math.sin(i * 1.7) * 0.8;
        for (let b = 0; b < d.length; b++) { pos.push(cx + ((b % 5) - 2) * 0.34, cy, cz + (Math.floor(b / 5) - 2) * 0.34); col.push(...(d[b] === '1' ? [0.72, 1, 0.82] : [0.16, 0.22, 0.27])); }
      });
      const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
      U.add(new THREE.Points(g, new THREE.PointsMaterial({ size: 0.22, vertexColors: true, toneMapped: false })));
      const fil = new THREE.LineBasicMaterial({ color: 0x5fe08f, toneMapped: false }); U.add(new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(0.6, 0.26, 0.4)), fil));
      for (let c = 0; c < 7; c++) { const m = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(0.05, 0.16, 0.3)), fil); m.position.set(-0.24 + c * 0.08, 0, 0); U.add(m); }
      camU = new THREE.PerspectiveCamera(60, 1, 0.02, 400); return U;
    }
    function changerEchelle() {
      if (!DESSINS.length) return;
      if (!univers) univers = construireUnivers();
      echelle = { t0: performance.now() }; $('#m3-vraiU').textContent = T.vrai_u(dateLongue(atelier.date)); $('#m3-univ').hidden = false;
    }
    $('#m3-retour').onclick = () => { echelle = null; $('#m3-univ').hidden = true; };
    function dessinerUnivers(t) {
      const u = lent ? 1 : Math.min(1, (t - echelle.t0) / 9000), e = u * u * (3 - 2 * u), dist = 0.9 * Math.pow(80, e), ang = 0.6 + (t - echelle.t0) / 9000;
      camU.aspect = camera.aspect; camU.updateProjectionMatrix(); camU.position.set(Math.sin(ang) * dist, dist * 0.45, Math.cos(ang) * dist); camU.lookAt(0, 0, 0);
      const et = T.etapes[e < 0.25 ? 0 : e < 0.75 ? 1 : 2], txt = typeof et === 'function' ? et(NCASES) : et;
      if ($('#m3-etape').textContent !== txt) $('#m3-etape').textContent = txt;
      renderer.render(univers, camU);
    }

    // ---------------------------------------------------------------- l'ascenseur
    const AFF = { '0': '0', '1': '−1', '2': '−2', '3': '−3', '4': '−4', '5': '−5', '6': '−6', '-1': '+1' };
    const PROF = (id) => (id === '-1' ? 0 : 4.5 * Number(id));   // 3,8 m de salle + 0,7 m de dalle par niveau
    const asc = $('#m3-asc'), fondu = $('#m3-fondu'), ecran = $('#m3-ecran'), msg = $('#m3-msg');
    const afficher = (id) => { ecran.innerHTML = `${AFF[id]}<small>${esc(T.profondeur(PROF(id)))}</small>`; };
    $('#m3-eres').innerHTML = `<button type="button" class="m3-ere on">${T.ere(aile.ere)}</button><button type="button" class="m3-ere" disabled title="${esc(T.attente)}">${T.ere(aile.ere + 1)}</button>`;
    boite.querySelectorAll('.m3-etage').forEach((b) => {
      const id = b.dataset.e;
      if (!DEF[id]) { b.disabled = true; b.querySelector('small').textContent = T.chantier; }
      b.onclick = () => { if (!b.disabled) aller(id); };
    });
    let essais = 0;
    function ouvrirAsc() {
      if (!asc.hidden) return; essais = 0; msg.textContent = T.asc_msg;
      boite.querySelectorAll('.m3-etage').forEach((b) => b.classList.toggle('on', b.dataset.e === courant.id)); afficher(courant.id); asc.hidden = false; bouclier(asc);
    }
    $('#m3-rester').onclick = () => { asc.hidden = true; joueur.z += 0.8 * (courant.sens || 1); };
    $('#m3-vis').onclick = () => { essais++; if (essais < 2) { msg.textContent = T.vis1; return; } msg.textContent = T.vis2; setTimeout(() => aller('-1'), 700); };
    function aller(id) { afficher(id); fondu.classList.add('on'); setTimeout(() => { asc.hidden = true; montrer(id); fondu.classList.remove('on'); }, 380); }
    function montrer(id) {
      if (SON && id !== '3') SON.arreter();
      if (courant) { courant.g.visible = false; if (courant.video) courant.video.pause(); }
      courant = obtenir(id); VIS.niveau(); courant.g.visible = true; if (courant.video) courant.video.play().catch(() => {});
      $('#m3-modes').hidden = id !== '5'; $('#m3-musique').hidden = id !== '3';
      LUM.niveau(courant); scene.fog.far = id === '5' ? 120 : 38;
      noterVu(id); if (PLAN) PLAN.maj();
      const d = courant.depart; joueur.x = d.x; joueur.z = d.z; joueur.yaw = d.yaw ?? Math.PI; joueur.pitch = -0.03;
      const [a, b] = courant.nom.split(' · '); $('#m3-ou').innerHTML = `<b>${esc(a)}</b>${b ? ' · ' + esc(b) : ''}`;
    }

    // ---------------------------------------------------------------- déplacements
    const joueur = { x: 0, z: 4.8, yaw: 0, pitch: -0.03 }, touches = {};
    let VIRAGE = 0, RAPIDE = false;
    const demiTour = () => { if (!VIRAGE) VIRAGE = Math.PI; };
    $('#m3-demitour').onclick = demiTour;
    $('#m3-rapide').onclick = () => { RAPIDE = !RAPIDE; $('#m3-rapide').setAttribute('aria-pressed', RAPIDE); };
    $('#m3-sortir').onclick = fermer;
    // déplacement rapide (Bran, 17/11/2026) : un menu mène directement à chaque niveau ouvert, et à l'aile des présidents ;
    // jamais à la réserve secrète, qui ne s'atteint que par la vis de l'ascenseur
    const menu = $('#m3-aller'), NIV_MENU = ['0', '1', '2', '3', '4', '5', '6'].filter((id) => DEF[id]);
    menu.innerHTML = `<option value="">${esc(T.aller)}</option>` + NIV_MENU.map((id) => `<option value="${id}">${esc(AFF[id] + ' · ' + T.niveaux[id][0])}</option>`).join('')
      + (DEF['0'].aile ? `<option value="pres">${esc('0 · ' + T.aller_pres)}</option>` : '');
    menu.onchange = () => {
      const v = menu.value; menu.value = ''; menu.blur(); if (!v) return;
      if (!voile.hidden) fermerCartel(); echelle = null; $('#m3-univ').hidden = true;
      if (v === 'pres') { aller('0'); setTimeout(() => { joueur.x = 9.6; joueur.z = -2; joueur.yaw = -Math.PI / 2; }, 420); }
      else aller(v);
    };
    const bas = (e) => {
      if (e.key === 'Escape') { if (!voile.hidden) fermerCartel(); else if (!asc.hidden) $('#m3-rester').onclick(); else if (echelle) $('#m3-retour').onclick(); else fermer(); return; }
      if ((e.key === 'r' || e.key === 'R') && voile.hidden && asc.hidden) demiTour();
      touches[e.key.toLowerCase()] = true;
    };
    const haut = (e) => { touches[e.key.toLowerCase()] = false; };
    addEventListener('keydown', bas); addEventListener('keyup', haut);
    boite.querySelectorAll('.m3-pad button[data-k]').forEach((b) => {
      const k = 'pad-' + b.dataset.k, on = (e) => { e.preventDefault(); touches[k] = true; }, off = () => { touches[k] = false; };
      b.addEventListener('pointerdown', on); b.addEventListener('pointerup', off); b.addEventListener('pointerleave', off); b.addEventListener('pointercancel', off);
    });
    let glisse = null, bouge = 0;
    canvas.addEventListener('pointerdown', (e) => { glisse = { x: e.clientX, y: e.clientY }; bouge = 0; canvas.setPointerCapture(e.pointerId); });
    canvas.addEventListener('pointermove', (e) => { if (!glisse) return; const dx = e.clientX - glisse.x, dy = e.clientY - glisse.y; bouge += Math.abs(dx) + Math.abs(dy); glisse = { x: e.clientX, y: e.clientY }; joueur.yaw -= dx * 0.005; joueur.pitch = Math.max(-0.9, Math.min(0.9, joueur.pitch - dy * 0.004)); });
    const ray = new THREE.Raycaster();
    canvas.addEventListener('pointerup', (e) => {
      const clic = bouge < 6; glisse = null; if (!clic || echelle) return; const r = canvas.getBoundingClientRect();
      ray.setFromCamera({ x: (e.clientX - r.left) / r.width * 2 - 1, y: -(e.clientY - r.top) / r.height * 2 + 1 }, camera);
      const h = ray.intersectObjects(courant.cibles)[0]; if (!h || h.distance > 9) return;
      const u = h.object.userData;
      if (u.asc) ouvrirAsc();
      else if (u.son && SON) SON.clic(u.son, u.k);
      else { const c = u.cartel || u.id; ouvrir(typeof c === 'string' ? CARTELS[c] : c); }
    });
    const libre = (x, z) => { const R = 0.35; return !courant.obs.some((o) => x > o.x1 - R && x < o.x2 + R && z > o.z1 - R && z < o.z2 + R); };
    const taille = () => { const w = boite.clientWidth || innerWidth, h = boite.clientHeight || innerHeight; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); };
    addEventListener('resize', taille); taille();
    montrer('0');
    let t0 = performance.now(), actif = true;
    function boucle(t) {
      if (!actif) return;
      const dt = Math.min(0.05, (t - t0) / 1000); t0 = t;
      if (echelle) { dessinerUnivers(t); requestAnimationFrame(boucle); return; }
      if (voile.hidden && asc.hidden) {
        const k = touches, v = 2.4 * dt * (RAPIDE || k.shift ? 2.5 : 1); let av = 0, tr = 0;
        if (k.arrowup || k.z || k.w || k['pad-av']) av += 1; if (k.arrowdown || k.s || k['pad-ar']) av -= 1;
        if (k.arrowleft || k.q || k.a || k['pad-g']) tr += 1; if (k.arrowright || k.d || k['pad-d']) tr -= 1;
        if (VIRAGE) { const pas = Math.min(VIRAGE, dt * 7); joueur.yaw += pas; VIRAGE -= pas; }
        joueur.yaw += tr * 1.8 * dt; const nx = joueur.x - Math.sin(joueur.yaw) * av * v, nz = joueur.z - Math.cos(joueur.yaw) * av * v;
        if (libre(nx, joueur.z)) joueur.x = nx; if (libre(joueur.x, nz)) joueur.z = nz;
      }
      camera.position.set(joueur.x, 1.62, joueur.z); camera.rotation.order = 'YXZ'; camera.rotation.y = joueur.yaw; camera.rotation.x = joueur.pitch;
      animerHinton(t); VIS.animer(t, dt); for (const f of courant.anim) f(t, dt);
      renderer.render(scene, camera); requestAnimationFrame(boucle);
    }
    requestAnimationFrame(boucle);
    window.MCL_MUSEE = { aller: (id) => DEF[id] && montrer(id), joueur, etat: () => ({ niveau: courant.id, niveaux: Object.keys(DEF), son: SON && SON.etat(), visiteurs: VIS.etat(), lumiere: LUM.etat() }), lumiere: (m) => LUM.mode(m), ouvrirAsc, changerEchelle };
    // à la sortie : tout s'arrête, rien ne reste en mémoire
    return () => {
      actif = false; if (SON) SON.fermer(); VIS.fermer(); LUM.fermer();
      removeEventListener('keydown', bas); removeEventListener('keyup', haut); removeEventListener('resize', taille);
      for (const id in ETAGES) if (ETAGES[id].video) ETAGES[id].video.pause();
      renderer.dispose(); delete window.MCL_MUSEE;
    };
  }
})();
