# État des fonctionnalités

*[English version](etat-fonctionnalites.en.md)*

**État au 21 octobre 2026, firmware 0.7 en service.** C'est la référence unique pour savoir si une fonction annoncée sur l'un des deux sites existe. En cas de divergence, ce tableau l'emporte sur les autres pages, et le code l'emporte sur ce tableau. Il est mis à jour à chaque version.

**États :**
- **En service** : la fonction tourne dans la boîte ou sur les sites.
- **Codé, fermé** : le code est dans le firmware en service, mais la fonction ne s'ouvre qu'à un âge que le pays n'a pas encore atteint, ou attend un réglage.
- **Prévu** : rien n'est encore codé, ou le code n'est pas installé. L'ordre et le contenu peuvent changer.

Le firmware n'est pas encore public (il le sera avec les études). D'ici là, la colonne « Où le vérifier » renvoie aux données et aux pages publiques.

## La boîte et les données

| Fonction | État | Depuis | Où le vérifier |
| --- | --- | --- | --- |
| Pays de 120 citoyens sur 6 régions et une passerelle (radio ESP-NOW) | En service | 0.3, 8 oct. 2026 | [architecture.md](architecture.md) |
| Une heure du pays = une heure réelle, à l'heure française | En service | 0.3 | `heures[]` dans chaque fichier brut |
| Cours de bourse réels : taux de la Banque centrale européenne, relevés à 18 h les jours ouvrés | En service | 0.3 | `bourse` dans chaque édition |
| Ce qui entre de l'extérieur : aujourd'hui, seulement les cours de la bourse. Votes comptés et réponses au signal : voir les âges ci-dessous | En service (bourse) | 0.3 | page « Le projet » |
| Météo simulée : tempêtes, épidémies, sécheresses, crises, abondance, tirées au sort par la passerelle | En service | 0.3 | page des règles ; aucune donnée météo réelle |
| Élections tous les 3 jours, ministres, censure, report, révolte, coup de palais, vacance | En service | 0.3 | journal, `data/histoire.json` |
| Foi des citoyens (croyant, agnostique, athée) | En service | 0.3 | journal |
| Langue commune : une idée par heure, oratrice tirée au sort | En service | 0.3 | `data/langue.json` |
| Effet de la langue sur la politique : deux régions qui se comprennent mal se font moins confiance (les électeurs favorisent un candidat d'une région qui « parle comme eux », et une région qui comprend mal la capitale se fâche un peu plus). C'est une règle fixe de la passerelle et des régions. Les mots eux-mêmes ne sont pas des entrées des cerveaux, et leurs décisions n'en dépendent pas directement | En service | 0.3 | `comprehension` dans `data/langue.json` et le fichier brut ; [grille-criteres-v2.md](grille-criteres-v2.md) (critère 09) |
| Apprentissage par récompense des cerveaux (poids renforcés ou affaiblis selon la satisfaction) | En service comme mécanisme ; son effet sur le comportement n'est pas encore démontré (export des poids en 0.8, puis études) | 0.3 | [grille-criteres-v2.md](grille-criteres-v2.md) |
| Fichier brut quotidien avec manifeste SHA-256 | En service | 0.6, 15 oct. 2026 | [dictionnaire-donnees.md](dictionnaire-donnees.md) |
| Graines du hasard publiées (format 2) | En service | 0.7, 18 oct. 2026 | bloc `graines` du fichier brut |
| Consommation électrique relevée chaque heure (prise locale) | En service | 0.7 | `heures[].prise` |
| Relance Wi-Fi automatique après une coupure | En service | 0.7 | `systeme.notes` (type `wifi`) |
| Publication différée en cas de coupure d'Internet | En service | 0.3 | [registre-incidents.md](registre-incidents.md) |
| Copie du pays hors de la boîte chaque soir | En service | 0.3 | `data/sauvegarde.json` (site du journal) |
| Bouton RESET caché (Grand Reset) | En service | 0.3 | jamais utilisé à ce jour |
| Abstention, vote blanc, sondages | Prévu | 0.8 | [historique-versions.md](historique-versions.md) |
| Export des poids des cerveaux, sauvegarde format 4 | Prévu | 0.8 | [historique-versions.md](historique-versions.md) |
| Travail, monnaie, école, générations, etc. (mises à jour 2 à 7) | Prévu | — | page des règles, « Ce qui est prévu » |

## Les âges de la civilisation

| Âge | Ce qui s'ouvre | État | Où le vérifier |
| --- | --- | --- | --- |
| Fondation | La gazette | En service depuis le 9 oct. 2026 | journal |
| Parole | La page « La langue » | En service depuis le 18 oct. 2026 | `ages` dans `data/latest.json` |
| Mémoire | La page « Histoire », les records | Codé, fermé | même champ : progression vers l'âge |
| État civil | Adopter un citoyen | Codé, fermé | idem |
| Diplomatie | L'ambassade, ses questions et sa lettre mensuelle | Codé, fermé | idem |
| Diplomatie | Démentis de l'Ambassade dans le journal (coquilles des éditions passées) | Codé (0.5), fermé | idem |
| Diplomatie | Votes du public sur les questions de l'ambassade (simples compteurs) | Codé, fermé, et en attente du service de vote (pas encore choisi) | page des mentions légales |
| Curiosité | Le signal du Centre de recherche et l'écoute des réponses (écrites dans la langue du pays uniquement) | Codé, fermé | idem |

## Le journal

| Fonction | État | Depuis | Où le vérifier |
| --- | --- | --- | --- |
| Journal bilingue écrit par la passerelle, chaque soir à 20 h | En service | 0.3 | `data/editions/N.json` |
| Suivi des personnages (« Que devient… ? », parcours de la semaine) | En service | 0.5 et 0.6 | éditions |
| Rubriques, journalistes citoyens signataires, billet, édition du dimanche | En service | 0.6 | `signature` dans les éditions |
| Presse censurée (articles noircis, jamais les chiffres) | En service | 0.6 | éditions sous censure |
| Biographie de chaque citoyen, notoriété | Prévu | — | page des règles |

## Les sites

| Fonction | État | Depuis | Où le vérifier |
| --- | --- | --- | --- |
| Domaine microcontroland.org (journal sur www, données sur donnees) | En service | 21 oct. 2026 | — |
| Journal lisible sans JavaScript (`journal.txt`, `/texte/`) | En service | 21 oct. 2026 | [journal.txt](https://www.microcontroland.org/journal.txt) |
| Histoire et langue sans JavaScript, robots.txt, plan du site | En service | 21 oct. 2026 | [/texte/](https://www.microcontroland.org/texte/) |
| Page « Découvrir le pays en 5 minutes » (état du pays mis à jour chaque soir) | En service | 21 oct. 2026 | [decouvrir.html](https://www.microcontroland.org/decouvrir.html) |
| Plan statique du site des données | En service | 21 oct. 2026 | [plan.html](https://donnees.microcontroland.org/plan.html) |
| Relevé anonyme des robots qui se déclarent (jour, robot, page, statut ; ni IP ni cookie) | En service | 21 oct. 2026 | export mensuel prévu dans `agents-ia/` |
| Tableau des 18 critères de vie artificielle (grille v2) | En service, états « en attente » | 19 oct. 2026 | [grille-criteres-v2.md](grille-criteres-v2.md) |
| Calcul de l'indice des critères | Prévu : seuils datés avant le premier calcul, affichage à l'âge de la Curiosité | — | idem |
| Publication du code du firmware | Prévu, avec les études | — | — |
