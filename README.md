# La Puce Libre — site de Microcontrôland

Site statique, gratuit, hébergé sur GitHub Pages.

**Cette version est prête à déposer** dans le dépôt `branbriere/microcontroland` : le pseudo est en place partout, et elle ne contient ni éditions d'exemple ni dossier `demo/`. Le site affiche « La première édition sera publiée ce soir à 20 h » jusqu'à ce que la passerelle publie.

## Mise en ligne (une seule fois, environ 10 minutes)

1. Crée un compte sur https://github.com si tu n'en as pas.
2. Crée un nouveau dépôt **public** nommé `microcontroland`.
3. Dans le dépôt : **Add file → Upload files**, puis dépose tout le contenu de ce dossier (pas le dossier lui-même). Valide avec **Commit changes**.
4. Va dans **Settings → Pages**. Sous **Build and deployment**, choisis **Deploy from a branch**, branche `main`, dossier `/ (root)`, puis **Save**.
5. Après une à deux minutes, le site est en ligne à l'adresse `https://TON-PSEUDO.github.io/microcontroland/`.
6. Dans `feed.xml`, remplace `branbriere` par ton pseudo GitHub (la passerelle le fera ensuite elle-même).

## Ce que la passerelle envoie chaque soir à 20 h

| Fichier | Contenu |
| --- | --- |
| `data/latest.json` | L'édition du jour (la page d'accueil l'affiche) |
| `data/editions/N.json` | Copie de l'édition du jour N (lien `#jour-N`) |
| `data/archive.json` | Liste des éditions, la plus récente en premier |
| `feed.xml` et `feed-en.xml` | Les flux RSS français et anglais, 20 dernières éditions |

Les pages (françaises à la racine, anglaises dans `en/`), `style.css` et les scripts `.js` ne changent jamais : la passerelle n'envoie que des données, quelques kilo-octets par jour.

La page `regles.html` (et `en/regles.html`) explique le cerveau d'un citoyen et toutes les règles du pays. Sa dernière partie, « Ce qui est prévu », décrit ce qui n'est pas encore dans la boîte (commerce en octets, outils, terre inconnue, effondrement) : à mettre à jour quand ces règles seront livrées.

Pour l'envoi, elle utilise l'API GitHub (requête `PUT /repos/TON-PSEUDO/microcontroland/contents/<chemin>`) avec un jeton « fine-grained » limité à ce seul dépôt, droit **Contents : Read and write**.

## Format d'une édition

Voir `data/latest.json` : rubrique, titre, chapô, paragraphes, citation, brèves, journée heure par heure, état du pays, cours de la bourse, régions et état du système. Les clés sont en français. Chaque texte est bilingue : `{"fr": "…", "en": "…"}`. La passerelle rédige les deux versions avec ses deux jeux de modèles de phrases.

## Tester sur ton PC

Les pages lisent les fichiers JSON : ouvrir `index.html` par double-clic ne suffit pas (le navigateur bloque la lecture de fichiers locaux). Lance plutôt un petit serveur dans ce dossier :

```
python -m http.server 8000
```

puis ouvre http://localhost:8000.

## Avant la mise en ligne

- **Adresse du site.** Dans tous les fichiers `.html`, remplace `branbriere.github.io/microcontroland` par l'adresse réelle de ton site (recherche et remplacement dans VS Code). Elle sert à l'image d'aperçu `apercu.png`, affichée quand on partage un lien sur les réseaux.
- **Mentions légales.** Relis `mentions.html` et `en/mentions.html` : ton nom y figure comme éditeur à titre personnel. Si tu ajoutes un jour un formulaire ou un compteur de votes hébergé ailleurs, il faudra le déclarer dans cette page.
- **Photos.** Dépose `boite.jpg` et `interieur.jpg` dans le dossier `photos/` : elles apparaissent dans la page « Le projet ». Sans fichier, l'emplacement reste invisible.
- **Polices.** Elles sont dans `fonts/` et servies par le site lui-même : aucun appel vers un serveur extérieur.

## Les âges de la civilisation

Le site contient dès le départ toutes les rubriques, mais certaines restent « en attente d'évolution de la civilisation » tant que le pays n'a pas atteint l'âge voulu. La passerelle l'indique dans chaque édition (`ages` dans `data/latest.json`) et les pages s'ouvrent toutes seules.

| Âge | Rubrique | Fichiers publiés par la passerelle |
|---|---|---|
| Fondation | Journal, archives, À suivre, dernière minute | `data/latest.json`, `data/editions/`, `data/archive.json`, `data/depeches.json` |
| Parole | `langue.html` | `data/langue.json` |
| Mémoire | `histoire.html` (règnes, records) | `data/histoire.json` |
| État civil | `citoyen.html` (adopter un citoyen) | `data/citoyens.json` |
| Diplomatie | `ambassade.html` (questions, lettres) | `data/ambassade.json`, `data/lettres.json` |
| Curiosité | `recherche.html`, `signal.txt` | `data/signal.json`, `data/contacts.json` |

**Voir le site « évolué » sans attendre.** Ajoute `?demo` à l'adresse (par exemple `https://ton-site/?demo`) : le site lit alors le dossier `demo/`, un pays d'exemple qui a déjà vécu 100 jours et ouvert tous les âges. Un bandeau le signale. Tu peux supprimer le dossier `demo/` quand tu veux.

## Réglages (`reglages.js`)

- `depot` : l'adresse du dépôt GitHub du site. Le Centre de recherche s'en sert pour le bouton « Répondre au signal ». L'onglet **Issues** du dépôt doit être activé (il l'est par défaut).
- `votes` : l'adresse du formulaire de vote de l'ambassade. Laisse vide tant qu'il n'existe pas.

## Le vote de l'ambassade (facultatif)

Sans vote, l'ambassadeur choisit lui-même trois questions par mois. Pour laisser les visiteurs voter :

1. Crée un formulaire Google avec une seule question à choix unique, dont les 16 réponses commencent par `Q1` à `Q16` (par exemple « Q3 — Croyez-vous au Créateur ? »), dans l'ordre de la page Ambassade.
2. Dans la feuille de réponses : Fichier → Partager → Publier sur le Web → format CSV. Copie l'adresse obtenue dans `include/secrets.h` du firmware (`MCL_VOTES_URL`).
3. Mets l'adresse publique du formulaire dans `reglages.js` (`votes`).

Le formulaire ne change jamais : chaque fin de mois, la passerelle ne retient que les votes arrivés depuis la lettre précédente.
Pense à signaler ce service tiers dans `mentions.html`.

## Couper l'écoute du Centre de recherche

Crée le fichier `data/controle.json` contenant `{"ecoute": false}` : la passerelle cesse de relever les réponses au signal. Supprime le fichier (ou mets `true`) pour reprendre.

## Répétition générale

La passerelle peut publier des éditions d'essai dans le dossier `repetition/` du dépôt. Pour les lire, ajoute `?essai` à l'adresse du site (par exemple `https://ton-site/?essai`). Un bandeau rappelle que ce sont des essais. Le dossier `repetition/` peut être supprimé ensuite.

## Histoire

La page `histoire.html` liste tous les présidents, ère par ère. Elle lit `data/histoire.json`, que la passerelle complète à chaque changement de président, et `data/latest.json` pour le président en place.

Si la passerelle ne publie plus rien pendant deux jours, la page d'accueil affiche un bandeau d'alerte au-dessus de la dernière édition.

## Archives

Chaque édition reste sur le site pour toujours dans `data/editions/`. Une édition pèse environ 3 Ko : dix ans d'histoire font environ 11 Mo, très loin de la limite recommandée de GitHub Pages (1 Go). La page `archives.html` les liste par mois, avec recherche et filtre par rubrique. La liste de l'année en cours est dans `data/archive.json` ; à chaque nouvelle année, la passerelle range la précédente dans `data/archive-AAAA.json`, que la page lit aussi.

## Deux langues

Les pages françaises sont à la racine, les pages anglaises dans `en/`, avec les mêmes noms de fichiers. Le bouton FR | EN du menu bascule de l'une à l'autre et retient le choix du visiteur. Au premier passage, un navigateur réglé en anglais est dirigé automatiquement vers la version anglaise.
