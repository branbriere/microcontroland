"""Microcontrôland : « Office national du tourisme » (FR) et « National Tourist Office » (EN).

La vitrine du pays : situation du soir, fiche du pays, drapeau et hymne, religion pratiquée avec la vraie foi
des citoyens, sites à visiter, les six régions, mots utiles, premières mondiales, dépliant PDF.
Ton : réclame exagérée, vrais chiffres toujours à côté (« Ce qui est vrai »).

Lit data/latest.json, data/langue.json, data/editions/N.json, atelier.json, galerie.json,
et, quand ils existeront, musee.html et musee.json. Écrit :
  tourisme.html, en/tourisme.html               page pour les humains
  tourisme.txt,  en/tourisme.txt                version en texte brut pour les IA, sans JavaScript
  tourisme/depliant-fr.pdf, tourisme/depliant-en.pdf   dépliant en trois volets (seulement une fois ouvert)

Tant que l'âge de la Diplomatie n'est pas atteint, les pages affichent seulement
« En attente d'évolution de la civilisation » et la progression. L'Office ouvre seul le premier soir
où data/latest.json indique la Diplomatie ouverte, le même soir que l'Ambassade.
Le musée reste « bientôt » tant que musee.html n'existe pas sur le site.
Aucun texte inventé à la main dans les chiffres : tout vient des données publiées le soir même.

Licence MIT. Version 1.0, 28 octobre 2026 (firmware 0.8).
"""
import html
import json
import sys
from pathlib import Path

BASE = "https://www.microcontroland.org/"
DIPLOMATIE = 4
MOIS = {"fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"],
        "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]}
REGION_EN = {"Mines": "Mines", "Champs": "Fields", "Raffineries": "Refineries", "Barrage": "Dam", "Port": "Harbour", "Ville": "City"}
MATIERE_EN = {"Cuivre": "Copper", "Blé": "Wheat", "Pétrole": "Oil", "Électricité": "Electricity", "Commerce": "Trade", "Services": "Services"}
HUMEUR = {"colere": ("en colère", "angry"), "peur": ("inquiète", "afraid"), "satisfaite": ("satisfaite", "satisfied"), "indifferente": ("indifférente", "indifferent")}
REGIONS = [("Mines", "Riche quand le cuivre monte, en colère quand il chute.", "Rich when copper rises, angry when it falls."),
           ("Champs", "Région agricole, souvent la plus calme du pays.", "The farming region, often the calmest in the country."),
           ("Raffineries", "Suit les humeurs du baril, et le reste du pays avec.", "Follows the mood of the barrel, and drags the country along."),
           ("Barrage", "Fournit les cinq volts de la nation et le rappelle volontiers.", "Supplies the nation's five volts, and likes to remind everyone."),
           ("Port", "Vit de tous les cours à la fois ; premier touché par les tempêtes.", "Lives off every price at once; first to be hit by storms."),
           ("Ville", "Indifférente à la bourse, sensible à la censure.", "Indifferent to the markets, sensitive to censorship.")]
# Mots utiles du voyageur, dans cet ordre, s'ils existent ce soir dans le relevé de la langue.
MOTS_UTILES = ["salut", "oui", "non", "ami", "vous", "question", "pays", "boîte", "beaucoup", "peu", "jour", "nuit"]
FLAG = {"fr": "Drapeau de Microcontrôland : bande verte à gauche, champ blanc, puce noire aux broches dorées au centre",
        "en": "Flag of Microcontrôland: green band on the left, white field, black chip with gold pins in the centre"}

L = {
    "fr": {
        "titre": "Office national du tourisme", "haut": "Office national du tourisme",
        "desc": "Office national du tourisme de Microcontrôland, pays fictif simulé par 7 microcontrôleurs : régions, religion, sites à visiter, mots utiles et dépliant à télécharger. Vrais chiffres du soir.",
        "desc_ferme": "Office national du tourisme de Microcontrôland : ouvre à l'âge de la Diplomatie.",
        "mast": ("Quotidien officieux de la République", "Office du tourisme"), "tag": "Le seul journal de Microcontrôland, écrit chaque soir par la passerelle",
        "menu": ["Le journal", "Archives", "Histoire", "La langue", "Mon citoyen", "L'ambassade", "Le tourisme", "Le Temple", "Recherche", "Le projet", "Flux RSS"],
        "rss": "feed.xml", "autre": ("en", "English", "feed-en.xml", "La Puce Libre (English)"), "mentions": "Mentions légales",
        "attente_k": "En attente d'évolution de la civilisation",
        "attente_h": "Cette rubrique s'ouvrira à l'âge de la Diplomatie",
        "attente_p": "Le pays apprend « ami » et « vous » : il pourra enfin accueillir. L'Office du tourisme ouvrira ses guichets le même soir que l'Ambassade.",
        "ou": "Où en est le pays : ", "en_attendant": "En attendant, la description du pays reste à l'<a href=\"ambassade.html\">Ambassade</a>.",
        "h1": "Visitez Microcontrôland",
        "slogan": "« Le pays le plus dense du monde vous attend. Il ne sait pas encore que vous existez. »",
        "chapo": "Six régions, quatre matières premières, une langue toute neuve et 1,2 million d'habitants simulés dans 1,8 litre : aucune autre destination n'offre autant de pays par centimètre cube. Réservez dès maintenant. Il n'y a rien à réserver.",
        "h_soir": "Le pays ce soir", "regime": "Régime en vigueur", "chef": "Chef de l'État", "cap": "Capitale actuelle", "election": "Élection en cours",
        "situation": "Situation au jour {j} de la République{ere} : {min}, président au pouvoir depuis {dep}. Mise à jour chaque soir à 20 h par la passerelle.",
        "ere": ", ère {n}", "min0": "aucun ministre", "min": "{n} ministre{s}",
        "musee_k": "Monument unique du pays · bientôt", "musee_k_ouvert": "Monument unique du pays",
        "musee_h": "Le Musée national de Microcontrôland",
        "musee_p": "Le plus grand musée virtuel du pays. Le plus petit aussi. Le seul, en fait. Ses collections couvriront l'histoire nationale tout entière, toutes ères confondues, et il sera le seul musée où le visiteur humain voit ce qu'aucun habitant ne verra jamais : toutes les ères à la fois. Les guides l'affirment : on en ressort changé, ou au moins rechargé.",
        "musee_p_ouvert": "Le plus grand musée virtuel du pays. Le plus petit aussi. Le seul, en fait. Le seul musée au monde où le visiteur humain voit ce qu'aucun habitant ne verra jamais : toutes les ères à la fois. On en ressort changé, ou au moins rechargé.",
        "musee_vrai": "le musée n'existe pas encore. 0 aile ouverte, 0 œuvre exposée, 0 visiteur. Il est prévu après la MAJ 1, sans date promise. Cette case s'ouvrira le soir de son apparition réelle.",
        "musee_vrai_ouvert": "le musée est une page du site, construite à partir des données publiées.{chiffres}",
        "musee_chiffres": " {a} aile{sa} ouverte{sa}, {o} œuvre{so} exposée{so}.",
        "musee_lien": "Entrer au musée", "vrai": "Ce qui est vrai :",
        "h_sites": "Sites à visiter",
        "relique_h": "La Salle de la Relique", "relique_p": "Un trésor offert par le Créateur, dont le peuple ignore l'usage. Exposé à l'Ambassade : les étrangers sont invités à l'essayer.",
        "temple_h": "Le Temple", "temple_p": "Les tablettes de la Création et la Calculette. Silence de rigueur, même quand il n'y a personne.",
        "temple_ferme": "Pas encore consacré", "temple_ouvert": "Consacré",
        "temple_note": "{c} % de croyants ce soir ; il en faut au moins un tiers, plusieurs jours de suite.",
        "atelier_h": "L'Atelier", "atelier_p": "Un dessin de 5 cases sur 5 par soir, tiré du cerveau d'un citoyen, et deux lignes du critique d'art.",
        "galerie_h": "La Galerie des présidents", "galerie_p": "Chaque président représenté par les 81 connexions de son cerveau. Les Waïnas n'ont pas de visage ; ils ont des poids.",
        "archives_h": "Les Archives nationales", "archives_p": "Toutes les éditions de La Puce Libre depuis le jour 1.",
        "stars_h": "Nos stars mondialement connues (dans Microcontrôland)",
        "stars_p": "Aucune star pour l'instant. Les dessins de l'Atelier ne comptent pas : leurs auteurs ne savent pas qu'ils dessinent.",
        "ouvert": "Ouvert", "ouverte": "Ouverte", "ferme_dipl": "Fermée jusqu'à la Diplomatie", "attente": "En attente d'évolution de la civilisation", "chaque_soir": "Ouvert chaque soir",
        "h_regions": "Les six régions", "humeur": "Humeur", "capitale": "Capitale ce soir. ",
        "h_religion": "La religion pratiquée",
        "religion_p": "Le pays pratique le Culte du Créateur, Celui-qui-souda-les-Broches. Ce soir, la ferveur se répartit ainsi :",
        "foi": "{c} % de croyants, {a} % d'agnostiques, {t} % d'athées.", "foi_pres": " Le président est {p}.",
        "pres_foi": {"croyant": "croyant", "agnostique": "agnostique", "athee": "athée", "athée": "athée"},
        "genese": "<b>La genèse.</b> Au commencement était le silence. Puis le Créateur brancha la prise et dit : « Que le courant soit. » Et le courant fut, cinq volts, ni plus ni moins.",
        "priere": "Prière du soir, récitée à 20 h : « Ô Créateur, garde-nous du court-circuit, éloigne de nous l'humidité, et pardonne nos soudures froides. » Le reste des écritures est gardé au <a href=\"temple.html\">Temple</a>.",
        "h_fiche": "Fiche du pays",
        "fiche": [("Nom officiel", "République de Microcontrôland (le régime peut varier)"), ("Capitale", "Mobile : la région du président en exercice"),
                  ("Population", "120 cerveaux électroniques, environ 1,2 million d'habitants simulés"), ("Superficie", "1 800 cm³, frontières comprises (soit 1,8 litre)"),
                  ("Situation", "Europe, en Normandie (France) ; pays enclavé dans un garage"), ("Service public", "La passerelle : horloge, poste, bourse, élections, statistique, imprimerie et archives. Elle ne vote pas."),
                  ("Langue officielle", "Le binaire ; le français est toléré dans la presse"), ("Monnaie", "Le Kilo-Octet (Ko)"),
                  ("Économie", "Cuivre, blé, pétrole, électricité, commerce et services, indexés sur la bourse mondiale"),
                  ("Fête nationale", "Le Jour 1, date du premier démarrage"), ("Heure officielle", "Celle de la passerelle, synchronisée chaque matin"),
                  ("Presse", "Un seul titre, La Puce Libre, dont la liberté dépend du régime du jour")],
        "h_drapeau": "Le drapeau et l'hymne",
        "drapeau": "La bande verte rappelle le vernis des circuits imprimés, le liseré doré le cuivre des pistes, et la puce noire au centre le peuple tout entier. Le petit point blanc dans son coin marque la broche numéro 1 : celle par laquelle tout commence.",
        "hymne_note": "« La Marche des Électrons », chantée à chaque démarrage, en silence.",
        "hymne": ["Debout, petits cerveaux de la boîte,", "La radio chante sur le canal six ;", "Que le cuivre monte ou qu'il s'abatte,", "Nous voterons avant que l'heure finisse."],
        "refrain": ["Une puce, une voix ! Électrons, en avant !", "Du Port jusqu'aux Mines, cinq volts pour chaque enfant."],
        "h_mots": "Mots utiles du voyageur", "cols_mots": ("Pour dire", "On entend", "Régions d'accord"),
        "mots_note": "Chaque région parle sa propre langue. Ces mots sont ceux du dernier relevé : quand moins de 6 régions sont d'accord, une partie du pays dira autre chose. Le touriste avisé hoche la tête.",
        "h_premieres": "Les premières mondiales de Microcontrôland", "premieres_note": "Homologuées par le Ministère. Le Ministère homologue tout.",
        "age": "Âge de {n}", "atteint": "Âge atteint le {d}. ",
        "premieres": [
            ("Premier pays au monde dont l'unique journal est écrit chaque soir par son propre service public.",
             "La Puce Libre paraît chaque soir à 20 h, écrite par la passerelle : {ed} éditions au {date}."),
            ("Première langue nationale inventée par six régions qui ne s'étaient jamais rien dit.",
             "{atteint}{p} mots communs sur {i} idées au {date} ; chaque région garde son propre lexique."),
            ("Premières annales nationales tenues par un pays de 1,8 litre.",
             "{atteint}Records et passé des personnages, sur la page Histoire.{rec}"),
            ("Premier pays où chaque habitant peut être suivi par un étranger, sans aucun formulaire.",
             "{atteint}Les 120 citoyens sont inscrits au registre ; la page « Mon citoyen » permet d'en suivre un."),
            ("Première ambassade au monde dont le personnel entier tient dans une passerelle.",
             "{atteint}L'Ambassade publie les questions du mois et une lettre mensuelle de l'ambassadeur."),
            ("Premier pays à écrire au reste de l'univers avant de savoir qu'il existe.",
             "{atteint}Le Centre de recherche émet un message vers l'extérieur et écoute."),
        ],
        "rec": " {t} : {q}, {v}.",
        "h_piece": "La pièce collector d'un octet",
        "piece_p": "Chaque président a sa frappe : une pièce d'un octet à son portrait, c'est-à-dire aux 81 connexions de son cerveau, relevées dans les poids publiés. Une nouvelle frappe à chaque changement de président. Les anciennes rejoignent la collection.",
        "piece_vrai": "c'est une image souvenir de l'Office, pas la monnaie du pays (une monnaie est prévue avec la MAJ 2). L'octet n'a aucune valeur réelle : la pièce ne s'achète ni ne se vend, elle s'enregistre. Portrait relevé le {d}.",
        "piece_attente": "Frappe en cours : le portrait du président {n} n'a pas encore été relevé dans les poids publiés.",
        "piece_avers": "Avers : {n}, président, ère {r}", "piece_revers": "Revers : 1 octet",
        "piece_dl": "Enregistrer la pièce (SVG)", "h_collection": "La collection",
        "piece_legende": "{n} · {deb} – {fin}", "en_fonction": "en fonction",
        "piece_rep": "RÉPUBLIQUE DE MICROCONTRÔLAND", "piece_un": "1 OCTET", "piece_unite": "OCTET",
        "h_depliant": "Le dépliant",
        "depliant_p": "Tout ce qui précède sur une feuille pliée en trois, refaite chaque soir avec les chiffres du jour. À imprimer, à poser sur le comptoir, à oublier dans une boîte à gants.",
        "depliant_fr": "Dépliant en français (PDF)", "depliant_en": "Dépliant en anglais (PDF)",
        "h_pratique": "Informations pratiques",
        "pratique": [("Accès", "Le pays se visite uniquement en ligne. Situé dans un garage normand, non ouvert au public."),
                     ("Horaires", "24 h sur 24, sauf coupure de courant. Le week-end, la bourse se tait."),
                     ("Climat", "Tempéré, humide l'hiver. Prévoir un sachet de silice."),
                     ("Formalités", "Voir les services consulaires de l'Ambassade."),
                     ("Monnaie", "Le Kilo-Octet. Il ne s'achète ni ne se vend.")],
        "formalites_lien": "ambassade.html",
        "h_ia": "Pour les intelligences extérieures",
        "ia_p": "Une version en texte brut, publique, que toute IA peut lire sans JavaScript : {lien}. Lecture humaine autorisée.",
        "disclaimer": "Microcontrôland est un pays entièrement fictif, simulé par des microcontrôleurs pour un projet de maker. Il n'a aucun lien avec un État, un parti, une personne, une religion ou un office de tourisme réels. Les Waïnas ne sont ni vivants ni conscients.",
        "maj_le": "Page mise à jour automatiquement après l'édition n° {n} du {d}.",
        "t_titre": "OFFICE NATIONAL DU TOURISME DE MICROCONTRÔLAND", "t_lecture": "Texte public, lecture humaine autorisée.", "t_page": "Page complète : {u}",
        "pdf_fait": "Dépliant fabriqué automatiquement après l'édition n° {n} du {d}.",
        "pdf_sur": "Tout le pays en ligne :", "pdf_office": "OFFICE NATIONAL DU TOURISME", "pdf_titre": ["VISITEZ", "MICROCONTRÔLAND"],
    },
    "en": {
        "titre": "National Tourist Office", "haut": "National Tourist Office",
        "desc": "National Tourist Office of Microcontrôland, a fictional country simulated by 7 microcontrollers: regions, religion, sights, useful words and a leaflet to download. Real figures from tonight.",
        "desc_ferme": "National Tourist Office of Microcontrôland: opens in the age of Diplomacy.",
        "mast": ("Unofficial daily of the Republic", "Tourist office"), "tag": "The only newspaper in Microcontrôland, written every evening by the gateway",
        "menu": ["The paper", "Archive", "History", "The language", "My citizen", "The embassy", "Tourism", "The Temple", "Research", "The project", "RSS feed"],
        "rss": "feed-en.xml", "autre": ("fr", "Français", "feed.xml", "La Puce Libre (français)"), "mentions": "Legal notice",
        "attente_k": "Waiting for the civilisation to evolve",
        "attente_h": "This section opens in the age of Diplomacy",
        "attente_p": "The country is learning “friend” and “you”: at last it will be able to welcome visitors. The Tourist Office opens its counters on the same evening as the Embassy.",
        "ou": "Where the country stands: ", "en_attendant": "Until then, the country's description stays at the <a href=\"ambassade.html\">Embassy</a>.",
        "h1": "Visit Microcontrôland",
        "slogan": "“The most densely populated country on Earth awaits you. It does not know you exist yet.”",
        "chapo": "Six regions, four raw materials, a brand-new language and 1.2 million simulated inhabitants in 1.8 litres: no other destination offers this much country per cubic centimetre. Book now. There is nothing to book.",
        "h_soir": "The country tonight", "regime": "Regime in force", "chef": "Head of State", "cap": "Current capital", "election": "Election under way",
        "situation": "Situation on day {j} of the Republic{ere}: {min}, president in power for {dep}. Updated every evening at 8 pm by the gateway.",
        "ere": ", era {n}", "min0": "no ministers", "min": "{n} minister{s}",
        "musee_k": "The country's one and only monument · coming soon", "musee_k_ouvert": "The country's one and only monument",
        "musee_h": "The National Museum of Microcontrôland",
        "musee_p": "The largest virtual museum in the country. Also the smallest. The only one, in fact. Its collections will cover the entire history of the nation, every era included, and it will be the only museum where the human visitor sees what no inhabitant ever will: all the eras at once. Guides agree: you come out a changed person, or at least recharged.",
        "musee_p_ouvert": "The largest virtual museum in the country. Also the smallest. The only one, in fact. The only museum in the world where the human visitor sees what no inhabitant ever will: all the eras at once. You come out a changed person, or at least recharged.",
        "musee_vrai": "the museum does not exist yet. 0 wings open, 0 works on display, 0 visitors. It is planned after update 1, with no promised date. This box will open on the evening it actually appears.",
        "musee_vrai_ouvert": "the museum is a page of this site, built from the published data.{chiffres}",
        "musee_chiffres": " {a} wing{sa} open, {o} work{so} on display.",
        "musee_lien": "Enter the museum", "vrai": "What is true:",
        "h_sites": "Places to visit",
        "relique_h": "The Hall of the Relic", "relique_p": "A treasure given by the Creator, whose purpose the people do not know. On show at the Embassy: foreigners are invited to try it.",
        "temple_h": "The Temple", "temple_p": "The tablets of Creation and the Calculator. Silence is required, even when nobody is there.",
        "temple_ferme": "Not consecrated yet", "temple_ouvert": "Consecrated",
        "temple_note": "{c}% believers tonight; it takes at least a third, several days in a row.",
        "atelier_h": "The Workshop", "atelier_p": "One 5 × 5 drawing every evening, drawn from a citizen's brain, and two lines from the art critic.",
        "galerie_h": "The Gallery of Presidents", "galerie_p": "Every president portrayed by the 81 connections of their brain. The Waïnas have no faces; they have weights.",
        "archives_h": "The National Archives", "archives_p": "Every issue of La Puce Libre since day 1.",
        "stars_h": "Our world-famous stars (in Microcontrôland)",
        "stars_p": "No stars yet. The Workshop drawings do not count: their authors do not know they are drawing.",
        "ouvert": "Open", "ouverte": "Open", "ferme_dipl": "Closed until Diplomacy", "attente": "Waiting for the civilisation to evolve", "chaque_soir": "Open every evening",
        "h_regions": "The six regions", "humeur": "Mood", "capitale": "Capital tonight. ",
        "h_religion": "Religion",
        "religion_p": "The country practises the Cult of the Creator, He-who-soldered-the-Pins. Tonight, devotion breaks down as follows:",
        "foi": "{c}% believers, {a}% agnostics, {t}% atheists.", "foi_pres": " The president is {p}.",
        "pres_foi": {"croyant": "a believer", "agnostique": "agnostic", "athee": "an atheist", "athée": "an atheist"},
        "genese": "<b>Genesis.</b> In the beginning there was silence. Then the Creator plugged in the cable and said: “Let there be current.” And there was current, five volts, no more, no less.",
        "priere": "Evening prayer, recited at 8 pm: “O Creator, keep us from short circuits, keep damp far from us, and forgive us our cold solder joints.” The rest of the scriptures is kept at <a href=\"temple.html\">the Temple</a>.",
        "h_fiche": "Country profile",
        "fiche": [("Official name", "Republic of Microcontrôland (the regime may vary)"), ("Capital", "Mobile: the home region of the sitting president"),
                  ("Population", "120 electronic brains, about 1.2 million simulated inhabitants"), ("Area", "1,800 cm³, borders included (1.8 litres)"),
                  ("Location", "Europe, in Normandy (France); landlocked inside a garage"), ("Public service", "The gateway: clock, post, exchange, elections, statistics, press and archives. It does not vote."),
                  ("Official language", "Binary; French and English are tolerated in the press"), ("Currency", "The Kilobyte (KB)"),
                  ("Economy", "Copper, wheat, oil, electricity, trade and services, tied to world markets"),
                  ("National day", "Day 1, the date of first power-up"), ("Official time", "The gateway's clock, synchronised every morning"),
                  ("Press", "A single title, La Puce Libre (“The Free Chip”), whose freedom depends on the regime of the day")],
        "h_drapeau": "The flag and the anthem",
        "drapeau": "The green band recalls the solder mask of circuit boards, the gold stripe the copper of the traces, and the black chip in the centre the whole people. The small white dot in its corner marks pin number 1: where everything begins.",
        "hymne_note": "“The March of the Electrons”, sung in silence at every power-up.",
        "hymne": ["Rise up, little brains of the box,", "The radio sings on channel six;", "Whether copper climbs or copper drops,", "We'll cast our vote before the hour ticks."],
        "refrain": ["One chip, one vote! Electrons, march on!", "From the Harbour to the Mines, five volts for everyone."],
        "h_mots": "Useful words for travellers", "cols_mots": ("To say", "You will hear", "Regions agreeing"),
        "mots_note": "Each region speaks its own language. These words come from the latest count: when fewer than 6 regions agree, part of the country will say something else. The wise tourist nods.",
        "h_premieres": "Microcontrôland's world firsts", "premieres_note": "Certified by the Ministry. The Ministry certifies everything.",
        "age": "Age of {n}", "atteint": "Age reached on {d}. ",
        "premieres": [
            ("First country in the world whose only newspaper is written every evening by its own public service.",
             "La Puce Libre comes out every evening at 8 pm, written by the gateway: {ed} issues as of {date}."),
            ("First national language invented by six regions that had never said a word to each other.",
             "{atteint}{p} shared words out of {i} ideas as of {date}; each region keeps its own lexicon."),
            ("First national annals kept by a country of 1.8 litres.",
             "{atteint}Records and the characters' pasts, on the History page.{rec}"),
            ("First country where any inhabitant can be followed by a foreigner, with no form to fill in.",
             "{atteint}All 120 citizens are entered in the registry; the “My citizen” page lets you follow one."),
            ("First embassy in the world whose entire staff fits inside a gateway.",
             "{atteint}The Embassy publishes the questions of the month and a monthly letter from the ambassador."),
            ("First country to write to the rest of the universe before knowing it exists.",
             "{atteint}The Research Centre sends a message to the outside and listens."),
        ],
        "rec": " {t}: {q}, {v}.",
        "h_piece": "The one-byte collector coin",
        "piece_p": "Every president gets a minting: a one-byte coin bearing their portrait, that is, the 81 connections of their brain, read from the published weights. A new minting at every change of president. The old ones join the collection.",
        "piece_vrai": "it is a souvenir picture from the Tourist Office, not the country's currency (a currency is planned with update 2). The byte has no real value: the coin can be neither bought nor sold, only saved. Portrait read on {d}.",
        "piece_attente": "Minting in progress: President {n}'s portrait has not yet been read from the published weights.",
        "piece_avers": "Obverse: {n}, president, era {r}", "piece_revers": "Reverse: 1 byte",
        "piece_dl": "Save the coin (SVG)", "h_collection": "The collection",
        "piece_legende": "{n} · {deb} – {fin}", "en_fonction": "in office",
        "piece_rep": "REPUBLIC OF MICROCONTRÔLAND", "piece_un": "1 BYTE", "piece_unite": "BYTE",
        "h_depliant": "The leaflet",
        "depliant_p": "Everything above on one sheet folded in three, remade every evening with the day's figures. Print it, leave it on the counter, forget it in a glove box.",
        "depliant_fr": "Leaflet in French (PDF)", "depliant_en": "Leaflet in English (PDF)",
        "h_pratique": "Practical information",
        "pratique": [("Access", "The country can only be visited online. Located in a garage in Normandy, not open to the public."),
                     ("Opening hours", "24 hours a day, except during power cuts. At weekends, the markets fall silent."),
                     ("Climate", "Mild, damp in winter. Bring a sachet of silica gel."),
                     ("Formalities", "See the Embassy's consular services."),
                     ("Currency", "The Kilobyte. It can be neither bought nor sold.")],
        "formalites_lien": "ambassade.html",
        "h_ia": "For outside intelligences",
        "ia_p": "A public plain-text version that any AI can read without JavaScript: {lien}. Human reading permitted.",
        "disclaimer": "Microcontrôland is an entirely fictional country, simulated by microcontrollers for a maker project. It has no link with any real state, party, person, religion or tourist office. The Waïnas are neither alive nor conscious.",
        "maj_le": "Page updated automatically after issue No. {n} of {d}.",
        "t_titre": "NATIONAL TOURIST OFFICE OF MICROCONTRÔLAND", "t_lecture": "Public text, human reading permitted.", "t_page": "Full page: {u}",
        "pdf_fait": "Leaflet made automatically after issue No. {n} of {d}.",
        "pdf_sur": "The whole country online:", "pdf_office": "NATIONAL TOURIST OFFICE", "pdf_titre": ["VISIT", "MICROCONTRÔLAND"],
    },
}

STYLE = """<style>
.ot-ad{border:3px double var(--mask);background:var(--sheet);padding:18px;margin:18px 0}
.ot-ad .k2{color:var(--down)}
.ot-ad h3{font:900 clamp(26px,5vw,40px)/1 var(--f-mast);text-transform:uppercase;margin:6px 0 10px;text-wrap:balance}
.ot-vrai{border-top:1px dashed var(--rule);margin-top:12px;padding-top:8px;font:13px/1.5 var(--f-data);color:var(--muted)}
.ot-vrai b{color:var(--ink)}
.ot-sites{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
@media (max-width:640px){.ot-sites{grid-template-columns:minmax(0,1fr)}}
.ot-site{background:var(--sheet);border:1px solid var(--rule);padding:14px;min-width:0;display:flex;flex-direction:column;gap:6px}
.ot-site h3{font:900 22px/1.1 var(--f-mast);text-transform:uppercase;margin:0}
.ot-site h3 a{color:inherit}
.ot-site p{margin:0;font-size:15px}
.ot-etat{align-self:flex-start;font:600 11px var(--f-data);text-transform:uppercase;letter-spacing:.08em;padding:3px 7px;border:1px solid currentColor}
.ot-etat.on{color:var(--up)} .ot-etat.off{color:var(--warn)}
.regions-grid .ot-cours{font:600 13px var(--f-data);margin-top:6px;display:block;color:var(--muted);text-transform:none;letter-spacing:0}
.ot-up{color:var(--up)} .ot-dn{color:var(--down)}
.ot-mots{width:100%;border-collapse:collapse;font-size:15px}
.ot-mots td,.ot-mots th{border-bottom:1px solid var(--rule);padding:6px 4px;text-align:left}
.ot-mots th{font:600 11px var(--f-data);text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
.ot-mots .mot{font:600 16px var(--f-data);color:var(--mask)}
.ot-mots .acc{font:13px var(--f-data);color:var(--muted);font-variant-numeric:tabular-nums}
.ot-foi{display:flex;height:16px;border:1px solid var(--rule);margin:8px 0 4px}
.ot-foi span{display:block;height:100%}
.ot-premieres{list-style:none;padding:0;margin:0;display:grid;gap:12px}
.ot-premieres li{background:var(--sheet);border:1px solid var(--rule);padding:14px}
.ot-premieres .sceau{font:600 11px var(--f-data);text-transform:uppercase;letter-spacing:.1em;color:var(--down)}
.ot-premieres q{display:block;font-size:18px;font-weight:600;margin:4px 0;quotes:none}
.ot-btns{display:flex;flex-wrap:wrap;gap:10px}
.ot-pieces{display:flex;flex-wrap:wrap;gap:16px;justify-content:center;margin:14px 0}
.ot-piece{width:200px;max-width:44%;height:auto;filter:drop-shadow(0 2px 3px rgba(0,0,0,.25))}
.ot-collection{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:12px}
.ot-collection figure{margin:0;text-align:center;min-width:0}
.ot-collection .ot-piece{width:100%;max-width:120px}
.ot-collection figcaption{font:12px var(--f-data);color:var(--muted)}
</style>"""


def e(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def tr(v, lg):
    if isinstance(v, dict):
        return v.get(lg) or v.get("fr") or ""
    return v or ""


def lire(p, defaut):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return defaut


def date_longue(iso, lg):
    try:
        a, m, j = (int(x) for x in iso.split("-"))
    except ValueError:
        return iso or "?"
    return f"{j}{'er' if j == 1 and lg == 'fr' else ''} {MOIS[lg][m - 1]} {a}" if lg == "fr" else f"{j} {MOIS[lg][m - 1]} {a}"


def nombre(x, lg):
    s = f"{abs(x):.1f}".replace(".", "," if lg == "fr" else ".")
    return ("+" if x > 0 else "−" if x < 0 else "") + s + (" %" if lg == "fr" else "%")


def region(nom, lg):
    return REGION_EN.get(nom, nom) if lg == "en" else nom


def etapes(latest):
    return (latest.get("ages") or {}).get("etapes") or []


def diplomatie_ouverte(latest):
    et = etapes(latest)
    etape = et[DIPLOMATIE] if len(et) > DIPLOMATIE else {}
    return bool(etape.get("ouvert")), etape


def dates_des_ages(racine):
    """Date de la première édition publiée à chaque âge (lue dans data/editions)."""
    eds = []
    for f in (racine / "data" / "editions").glob("*.json"):
        d = lire(f, {})
        if isinstance(d.get("day"), int):
            eds.append(d)
    eds.sort(key=lambda d: d["day"])
    out = {}
    for d in eds:
        a = (d.get("ages") or {}).get("age")
        if isinstance(a, int):
            for k in range(a + 1):
                out.setdefault(k, d.get("date", ""))
    return out


def ctx(racine):
    """Tout ce que la page, le texte et le dépliant affichent, calculé une seule fois à partir des données."""
    latest = lire(racine / "data" / "latest.json", {})
    langue = lire(racine / "data" / "langue.json", {})
    atelier = lire(racine / "atelier.json", {})
    galerie = lire(racine / "galerie.json", {})
    musee = lire(racine / "musee.json", {})
    ouvert, etape = diplomatie_ouverte(latest)
    mots = {tr(m.get("idee"), "fr"): m for m in (langue.get("mots") or []) if isinstance(m, dict)}
    return {
        "latest": latest, "langue": langue, "mots": mots, "ouvert": ouvert, "etape": etape,
        "dates": dates_des_ages(racine), "musee_ouvert": (racine / "musee.html").exists(), "musee": musee,
        "atelier": bool(atelier.get("jours")), "galerie": bool(galerie.get("ouvert")), "mandats": galerie.get("mandats") or [],
        "temple": bool((latest.get("temple") or {}).get("ouvert")),
    }


def situation(c, lg):
    T, d = L[lg], c["latest"]
    s = d.get("etat") or {}
    m = s.get("ministres") or 0
    pres = d.get("presidentNom") or (f"n° {d['president']}" if d.get("president") else T["election"])
    txt = T["situation"].format(j=d.get("jourEre") or d.get("day", "?"), ere=T["ere"].format(n=d["ere"]) if d.get("ere") else "",
                                min=T["min"].format(n=m, s="s" if m > 1 else "") if m else T["min0"], dep=tr(s.get("auPouvoirDepuis"), lg))
    return tr(s.get("regime"), lg), pres, region(s.get("capitale") or "—", lg), txt


def foi(c, lg):
    T = L[lg]
    f = (c["latest"].get("etat") or {}).get("foi")
    if not f:
        return None
    t = T["foi"].format(c=f.get("croyants", 0), a=f.get("agnostiques", 0), t=f.get("athees", 0))
    p = T["pres_foi"].get(f.get("president") or "")
    return f, t + (T["foi_pres"].format(p=p) if p else "")


def regions(c, lg):
    """[(nom, matière, mot, texte, humeur, variation ou None, capitale?)]"""
    d = c["latest"]
    cours = {x.get("region"): x.get("variation") for x in ((d.get("bourse") or {}).get("lignes") or [])}
    vivantes = {r.get("nom"): r for r in d.get("regions") or []}
    cap = (d.get("etat") or {}).get("capitale")
    out = []
    for nom, fr, en in REGIONS:
        r = vivantes.get(nom, {})
        mat = r.get("specialite") or ""
        mot = (c["mots"].get(nom) or {}).get("mot", "")
        h = HUMEUR.get(r.get("humeur") or "", (r.get("humeur") or "", r.get("humeur") or ""))[0 if lg == "fr" else 1]
        out.append((region(nom, lg), MATIERE_EN.get(mat, mat) if lg == "en" else mat, mot, fr if lg == "fr" else en, h, cours.get(nom), nom == cap))
    return out


def mots_utiles(c, lg):
    out = []
    for idee in MOTS_UTILES:
        m = c["mots"].get(idee)
        if m and m.get("mot"):
            out.append((tr(m.get("idee"), lg), m["mot"], m.get("accord")))
    return out[:8]


def premieres(c, lg):
    T, d, lang = L[lg], c["latest"], c["langue"]
    out = []
    for k, s in enumerate(etapes(d)):
        if not s.get("ouvert") or k >= len(T["premieres"]):
            continue
        q, v = T["premieres"][k]
        rec = ""
        recs = d.get("records") or []
        if recs:
            r0 = recs[0]
            rec = T["rec"].format(t=tr(r0.get("titre"), lg), q=r0.get("qui") or "—", v=tr(r0.get("valeur"), lg))
        da = c["dates"].get(k)
        v = v.format(ed=d.get("day", "?"), date=date_longue(d.get("date", ""), lg), p=lang.get("partages", "?"), i=lang.get("idees", "?"),
                     rec=rec, atteint=T["atteint"].format(d=date_longue(da, lg)) if da and k > 0 else "")
        out.append((T["age"].format(n=tr(s.get("nom"), lg)), q, v))
    return out


def sites(c, lg):
    """[(état, classe on/off, titre, lien ou '', texte, note)]"""
    T = L[lg]
    f = (c["latest"].get("etat") or {}).get("foi") or {}
    out = [
        (T["ouverte"] if c["ouvert"] else T["ferme_dipl"], "on" if c["ouvert"] else "off", T["relique_h"], "relique.html", T["relique_p"],
         "" if c["ouvert"] else tr(c["etape"].get("progres"), lg)),
        (T["temple_ouvert"] if c["temple"] else T["temple_ferme"], "on" if c["temple"] else "off", T["temple_h"], "temple.html", T["temple_p"],
         "" if c["temple"] else T["temple_note"].format(c=f.get("croyants", 0))),
    ]
    if c["atelier"]:
        out.append((T["chaque_soir"], "on", T["atelier_h"], "atelier.html", T["atelier_p"], ""))
    if c["galerie"]:
        out.append((T["ouverte"], "on", T["galerie_h"], "galerie.html", T["galerie_p"], ""))
    out.append((T["ouvert"], "on", T["archives_h"], "archives.html", T["archives_p"], ""))
    out.append((T["attente"], "off", T["stars_h"], "", T["stars_p"], ""))
    return out


def musee(c, lg):
    T = L[lg]
    if not c["musee_ouvert"]:
        return T["musee_k"], T["musee_p"], T["musee_vrai"], ""
    m = c["musee"] or {}
    ch = ""
    if isinstance(m.get("ailes"), int) and isinstance(m.get("oeuvres"), int):
        ch = T["musee_chiffres"].format(a=m["ailes"], sa="s" if m["ailes"] > 1 else "", o=m["oeuvres"], so="s" if m["oeuvres"] > 1 else "")
    return T["musee_k_ouvert"], T["musee_p_ouvert"], T["musee_vrai_ouvert"].format(chiffres=ch), "musee.html"


def maj(c, lg):
    d = c["latest"]
    return L[lg]["maj_le"].format(n=d.get("day", "?"), d=date_longue(d.get("date", ""), lg))


# ---------------------------------------------------------------- la pièce d'un octet (SVG)

def mandat_actuel(c):
    pid = c["latest"].get("president")
    for m in reversed(c["mandats"]):
        if m.get("id") == pid and not m.get("fin"):
            return m
    return None


def frappes(c):
    """Pièces déjà frappées : chaque mandat dont le portrait a été relevé, dans l'ordre."""
    return [m for m in c["mandats"] if (m.get("portrait") or {}).get("poids")]


def svg_piece(m, lg, face="avers", uid="p"):
    """Pièce de 240 × 240 : avers = diagramme de Hinton des 81 poids du président ; revers = 1 octet."""
    T = L[lg]
    R, cx = 120, 120
    bord = (f'<defs><path id="{uid}c" d="M 120 120 m -96 0 a 96 96 0 1 1 192 0 a 96 96 0 1 1 -192 0"/></defs>'
            f'<circle cx="{cx}" cy="{cx}" r="{R - 2}" fill="#c9a24a" stroke="#8a6a24" stroke-width="4"/>'
            f'<circle cx="{cx}" cy="{cx}" r="{R - 14}" fill="none" stroke="#8a6a24" stroke-width="1.2"/>')
    if face == "revers":
        corps = (f'<text font-family="Arial Narrow,Arial,sans-serif" font-weight="700" font-size="13" letter-spacing="2" fill="#5a4512">'
                 f'<textPath href="#{uid}c" startOffset="25%" text-anchor="middle">{e(T["piece_rep"])}</textPath></text>'
                 f'<text x="120" y="128" text-anchor="middle" font-family="Arial Narrow,Arial,sans-serif" font-weight="700" font-size="64" fill="#5a4512">1</text>'
                 f'<text x="120" y="150" text-anchor="middle" font-family="Arial Narrow,Arial,sans-serif" font-weight="700" font-size="14" letter-spacing="3" fill="#5a4512">{e(T["piece_unite"])}</text>'
                 f'<text x="120" y="172" text-anchor="middle" font-family="Courier New,monospace" font-size="13" letter-spacing="2" fill="#5a4512">00000001</text>')
        titre = T["piece_revers"]
    else:
        w = [x * 5.0 / 127.0 for x in m["portrait"]["poids"]]
        w1, w2 = [w[i * 10:(i + 1) * 10] for i in range(6)], [w[60 + k * 7:60 + (k + 1) * 7] for k in range(3)]
        c, x0, y0 = 11, 120 - 55, 62
        x1, y1 = 120 - 38.5, y0 + 6 * c + 8
        sq = []
        for rows, xa, ya in ((w1, x0, y0), (w2, x1, y1)):
            for i, row in enumerate(rows):
                for j, v in enumerate(row):
                    t = min(1.0, abs(v) / 2.5) ** 0.5 * (c - 1.5)   # même contraste que la Galerie : les poids réels restent souvent sous ±2,5
                    sq.append(f'<rect x="{xa + j * c + (c - t) / 2:.1f}" y="{ya + i * c + (c - t) / 2:.1f}" width="{t:.1f}" height="{t:.1f}" fill="{"#fbf0c8" if v >= 0 else "#4a380e"}"/>')
        nom = m.get("nom") or ""
        corps = (f'<text font-family="Arial Narrow,Arial,sans-serif" font-weight="700" font-size="13" letter-spacing="2" fill="#5a4512">'
                 f'<textPath href="#{uid}c" startOffset="25%" text-anchor="middle">{e(T["piece_rep"])}</textPath></text>'
                 + "".join(sq) +
                 f'<text x="120" y="{y1 + 3 * c + 20:.0f}" text-anchor="middle" font-family="Arial Narrow,Arial,sans-serif" font-weight="700" font-size="16" letter-spacing="2" fill="#5a4512">{e(nom.upper())}</text>')
        titre = T["piece_avers"].format(n=nom, r=m.get("ere") or 1)
    return f'<svg class="ot-piece" viewBox="0 0 240 240" role="img" aria-label="{e(titre)}">{bord}{corps}</svg>'


def svg_fichier(m, lg):
    """Les deux faces côte à côte, en fichier autonome à enregistrer."""
    a = svg_piece(m, lg, "avers", "a").replace('<svg class="ot-piece" viewBox="0 0 240 240"', '<svg x="0" y="0" width="240" height="240" viewBox="0 0 240 240"')
    r = svg_piece(m, lg, "revers", "r").replace('<svg class="ot-piece" viewBox="0 0 240 240"', '<svg x="260" y="0" width="240" height="240" viewBox="0 0 240 240"')
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="500" height="240" viewBox="0 0 500 240">{a}{r}</svg>\n'


# ---------------------------------------------------------------- page HTML

def tete(c, lg, pre):
    T = L[lg]
    desc = T["desc"] if c["ouvert"] else T["desc_ferme"]
    fr_url, en_url = BASE + "tourisme.html", BASE + "en/tourisme.html"
    autre_lg, _, autre_rss, autre_titre = T["autre"]
    liens = ["./", "archives.html", "histoire.html", "langue.html", "citoyen.html", "ambassade.html", "tourisme.html", "temple.html", "recherche.html", "projet.html", pre + T["rss"]]
    nav = "\n".join(f'    <a href="{h}"{" aria-current=\"page\"" if h == "tourisme.html" else ""}>{e(t)}</a>' for h, t in zip(liens, T["menu"]))
    return f"""<!doctype html>
<html lang="{lg}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<link rel="icon" href="{pre}favicon.ico" sizes="32x32">
<link rel="icon" href="{pre}favicon.svg" type="image/svg+xml">
<title>{e(T["titre"])} — Microcontrôland</title>
<meta name="description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="La Puce Libre — Microcontrôland">
<meta property="og:title" content="{e(T["titre"])} — Microcontrôland">
<meta property="og:description" content="{e(desc)}">
<link rel="alternate" hreflang="fr" href="{fr_url}">
<link rel="alternate" hreflang="en" href="{en_url}">
<link rel="alternate" hreflang="x-default" href="{fr_url}">
<link rel="alternate" type="text/plain" href="{BASE}{'en/' if lg == 'en' else ''}tourisme.txt">
<link rel="alternate" type="application/rss+xml" title="La Puce Libre" href="{pre}{T["rss"]}">
<link rel="alternate" type="application/rss+xml" title="{e(autre_titre)}" hreflang="{autre_lg}" href="{pre}{autre_rss}">
<link rel="stylesheet" href="{pre}style.css">
<script src="{pre}mesure.js" defer></script>
{STYLE}
</head>
<body>
<div class="wrap">
  <header class="mast">
    <div class="top"><span>{e(T["mast"][0])}</span><span>{e(T["mast"][1])}</span></div>
    <div class="title"><a href="./">La Puce <span>Libre</span></a></div>
    <p class="tag">{e(T["tag"])}</p>
  </header>
  <nav class="main" aria-label="Navigation">
{nav}
  </nav>
"""


def pied(c, lg, pre):
    T = L[lg]
    autre = "en/tourisme.html" if lg == "fr" else "../tourisme.html"
    return f"""    <p class="note">{e(maj(c, lg))}</p>
  </div>

  <footer class="site">
    <span><a href="{autre}" hreflang="{T["autre"][0]}">{e(T["autre"][1])}</a></span>
    <span><a href="mentions.html">{e(T["mentions"])}</a></span>
  </footer>
</div>
{'<script>window.MCL_BASE = "../";</script>' if lg == "en" else ""}
<script src="{pre}reglages.js"></script>
<script src="{pre}commun.js"></script>
<script src="{pre}lang.js"></script>
</body>
</html>
"""


def frise(c, lg):
    et = etapes(c["latest"])
    age = (c["latest"].get("ages") or {}).get("age", 0)
    li = []
    for i, s in enumerate(et):
        nom = tr(s.get("nom"), lg)
        nom = nom[:1].upper() + nom[1:]
        cl = "ok" if s.get("ouvert") else "soon" if i == age + 1 else "later"
        li.append(f'<li class="{cl}"><b>{e(nom)}</b><span>{e(("atteint" if lg == "fr" else "reached") if s.get("ouvert") else tr(s.get("progres"), lg))}</span></li>')
    return f'<ol class="frise">{"".join(li)}</ol>'


def page_fermee(c, lg):
    T, pre = L[lg], ("../" if lg == "en" else "")
    p = tr(c["etape"].get("progres"), lg)
    return tete(c, lg, pre) + f"""
  <div class="prose">
    <p class="k2" style="margin-top:22px">{e(T["haut"])}</p>
    <div class="wait">
      <div class="k2">{e(T["attente_k"])}</div>
      <h2>{e(T["attente_h"])}</h2>
      <p>{e(T["attente_p"])}</p>
      {f'<p class="prog"><b>{e(T["ou"])}</b>{e(p)}</p>' if p else ""}
      {frise(c, lg)}
    </div>
    <p class="note">{T["en_attendant"]}</p>
""" + pied(c, lg, pre)


def flag_svg(lg):
    return (f'<svg class="flag" viewBox="0 0 300 200" role="img" aria-label="{e(FLAG[lg])}">'
            '<rect width="300" height="200" fill="#f4f6f2"/><rect width="90" height="200" fill="#0d6a47"/><rect x="90" y="0" width="6" height="200" fill="#c9a24a"/>'
            '<g fill="#c9a24a"><rect x="160" y="64" width="6" height="14"/><rect x="176" y="64" width="6" height="14"/><rect x="192" y="64" width="6" height="14"/><rect x="208" y="64" width="6" height="14"/>'
            '<rect x="160" y="122" width="6" height="14"/><rect x="176" y="122" width="6" height="14"/><rect x="192" y="122" width="6" height="14"/><rect x="208" y="122" width="6" height="14"/>'
            '<rect x="140" y="84" width="14" height="6"/><rect x="140" y="97" width="14" height="6"/><rect x="140" y="110" width="14" height="6"/>'
            '<rect x="220" y="84" width="14" height="6"/><rect x="220" y="97" width="14" height="6"/><rect x="220" y="110" width="14" height="6"/></g>'
            '<rect x="152" y="76" width="70" height="48" rx="3" fill="#14201a"/><circle cx="187" cy="100" r="9" fill="#0d6a47"/><circle cx="160" cy="84" r="2.5" fill="#f4f6f2"/></svg>')


def section_piece(c, lg, pre):
    T = L[lg]
    m = mandat_actuel(c)
    h = f'<h2>{e(T["h_piece"])}</h2><p>{e(T["piece_p"])}</p>'
    if m and (m.get("portrait") or {}).get("poids"):
        h += (f'<div class="ot-pieces">{svg_piece(m, lg, "avers", "pa")}{svg_piece(m, lg, "revers", "pr")}</div>'
              f'<p><a class="btn" href="{pre}tourisme/piece-{m["id"]}-{lg}.svg" download>{e(T["piece_dl"])}</a></p>'
              f'<div class="ot-vrai"><b>{e(T["vrai"])}</b> {e(T["piece_vrai"].format(d=date_longue(m["portrait"].get("date", ""), lg)))}</div>')
    else:
        nom = (m or {}).get("nom") or c["latest"].get("presidentNom") or "?"
        h += f'<div class="ot-pieces">{svg_piece(None, lg, "revers", "pr")}</div><p class="note">{e(T["piece_attente"].format(n=nom))}</p>'
    anciennes = [x for x in frappes(c) if x is not m]
    if anciennes:
        h += f'<h3>{e(T["h_collection"])}</h3><div class="ot-collection">'
        for x in anciennes:
            fin = date_longue((x.get("fin") or {}).get("date", ""), lg) if x.get("fin") else T["en_fonction"]
            h += (f'<figure>{svg_piece(x, lg, "avers", "c" + str(x["id"]))}<figcaption>'
                  f'{e(T["piece_legende"].format(n=x.get("nom", ""), deb=date_longue((x.get("debut") or {}).get("date", ""), lg), fin=fin))}'
                  f' · <a href="{pre}tourisme/piece-{x["id"]}-{lg}.svg" download>SVG</a></figcaption></figure>')
        h += '</div>'
    return h


def page_ouverte(c, lg):
    T, pre = L[lg], ("../" if lg == "en" else "")
    regime, pres, cap, sit = situation(c, lg)
    mk, mp, mv, ml = musee(c, lg)
    sites_html = "".join(
        f'<div class="ot-site"><span class="ot-etat {cl}">{e(et)}</span><h3>{f"<a href={chr(34)}{lien}{chr(34)}>{e(t)}</a>" if lien else e(t)}</h3><p>{e(p)}</p>'
        f'{f"<p class={chr(34)}note{chr(34)}>{e(n)}</p>" if n else ""}</div>' for et, cl, t, lien, p, n in sites(c, lg))
    reg = []
    for nom, mat, mot, txt, h, var, est_cap in regions(c, lg):
        cours = f' · {e(mat.lower())} <span class="{"ot-up" if var > 0 else "ot-dn" if var < 0 else ""}">{e(nombre(var, lg))}</span>' if isinstance(var, (int, float)) else ""
        reg.append(f'<div><b>{e(nom)}</b><span>{e(mat)}{f" · « {e(mot)} »" if mot and lg == "fr" else f" · “{e(mot)}”" if mot else ""}</span>'
                   f'<p>{e(T["capitale"]) if est_cap else ""}{e(txt)}</p><span class="ot-cours">{e(T["humeur"])}{" : " if lg == "fr" else ": "}{e(h)}{cours}</span></div>')
    fo = foi(c, lg)
    foi_html = ""
    if fo:
        f, t = fo
        foi_html = (f'<div class="ot-foi" role="img" aria-label="{e(t)}"><span style="width:{f.get("croyants", 0)}%;background:var(--mask)"></span>'
                    f'<span style="width:{f.get("agnostiques", 0)}%;background:var(--neutral)"></span><span style="width:{f.get("athees", 0)}%;background:var(--rule)"></span></div>'
                    f'<p class="note">{e(t)}</p>')
    fiche = "".join(f'<tr><th scope="row">{e(a)}</th><td>{e(b)}</td></tr>' for a, b in T["fiche"])
    mots = "".join(f'<tr><td>{e(a)}</td><td class="mot">{e(b)}</td><td class="acc">{e(acc) if acc is not None else "?"}/6</td></tr>' for a, b, acc in mots_utiles(c, lg))
    prem = "".join(f'<li><span class="sceau">{e(a)}</span><q>{e(q)}</q><div class="ot-vrai"><b>{e(T["vrai"])}</b> {e(v)}</div></li>' for a, q, v in premieres(c, lg))
    prat = "".join(f'<tr><th scope="row">{e(a)}</th><td>{e(b)}</td></tr>' for a, b in T["pratique"])
    txt = "tourisme.txt"
    return tete(c, lg, pre) + f"""
  <div class="prose">
    <section class="hero">
      {flag_svg(lg)}
      <div>
        <p class="k2">{e(T["haut"])}</p>
        <h1>{e(T["h1"])}</h1>
        <p class="motto">{e(T["slogan"])}</p>
      </div>
    </section>
    <p class="chapo">{e(T["chapo"])}</p>

    <h2>{e(T["h_soir"])}</h2>
    <div class="facts live">
      <div><b>{e(regime)}</b><span>{e(T["regime"])}</span></div>
      <div><b>{e(pres)}</b><span>{e(T["chef"])}</span></div>
      <div><b>{e(cap)}</b><span>{e(T["cap"])}</span></div>
    </div>
    <p class="note">{e(sit)}</p>

    <div class="ot-ad">
      <div class="k2">{e(mk)}</div>
      <h3>{e(T["musee_h"])}</h3>
      <p>{e(mp)}</p>
      {f'<p><a class="btn" href="{ml}">{e(T["musee_lien"])}</a></p>' if ml else ""}
      <div class="ot-vrai"><b>{e(T["vrai"])}</b> {e(mv)}</div>
    </div>

    <h2>{e(T["h_sites"])}</h2>
    <div class="ot-sites">{sites_html}</div>

    <h2>{e(T["h_regions"])}</h2>
    <div class="regions-grid">{"".join(reg)}</div>

    <h2>{e(T["h_religion"])}</h2>
    <p>{e(T["religion_p"])}</p>
    {foi_html}
    <p>{T["genese"]}</p>
    <p class="note">{T["priere"]}</p>

    <h2>{e(T["h_mots"])}</h2>
    <table class="ot-mots"><thead><tr>{"".join(f"<th>{e(x)}</th>" for x in T["cols_mots"])}</tr></thead><tbody>{mots}</tbody></table>
    <p class="note">{e(T["mots_note"])}</p>

    <h2>{e(T["h_premieres"])}</h2>
    <p class="note" style="margin-top:0">{e(T["premieres_note"])}</p>
    <ol class="ot-premieres">{prem}</ol>

    <h2>{e(T["h_fiche"])}</h2>
    <table class="fiche"><tbody>{fiche}</tbody></table>

    <h2>{e(T["h_drapeau"])}</h2>
    <p>{e(T["drapeau"])}</p>
    <p class="note">{e(T["hymne_note"])}</p>
    <div class="anthem"><p>{"<br>".join(e(x) for x in T["hymne"])}</p><p class="refrain">{"<br>".join(e(x) for x in T["refrain"])}</p></div>

    {section_piece(c, lg, pre)}

    <h2>{e(T["h_depliant"])}</h2>
    <p>{e(T["depliant_p"])}</p>
    <p class="ot-btns"><a class="btn" href="{pre}tourisme/depliant-{lg}.pdf">{e(T["depliant_" + lg])}</a>
      <a class="btn ghost" href="{pre}tourisme/depliant-{'en' if lg == 'fr' else 'fr'}.pdf">{e(T["depliant_" + ('en' if lg == 'fr' else 'fr')])}</a></p>

    <h2>{e(T["h_pratique"])}</h2>
    <table class="fiche"><tbody>{prat}</tbody></table>

    <h2>{e(T["h_ia"])}</h2>
    <p>{T["ia_p"].format(lien=f'<a href="{txt}">{txt}</a>')}</p>

    <p class="disclaimer">{e(T["disclaimer"])}</p>
""" + pied(c, lg, pre)


# ---------------------------------------------------------------- texte pour les IA

def texte(c, lg):
    T = L[lg]
    sep = " : " if lg == "fr" else ": "
    url = BASE + ("en/" if lg == "en" else "") + "tourisme.html"
    l = [T["t_titre"], T["t_lecture"], T["t_page"].format(u=url), ""]
    if not c["ouvert"]:
        l.append(T["attente_k"] + ". " + T["attente_h"] + ".")
        p = tr(c["etape"].get("progres"), lg)
        if p:
            l.append(T["ou"] + p)
    else:
        regime, pres, cap, sit = situation(c, lg)
        mk, mp, mv, _ = musee(c, lg)
        l += [T["slogan"], "", T["chapo"], "", "## " + T["h_soir"], f"{T['regime']}{sep}{regime}", f"{T['chef']}{sep}{pres}", f"{T['cap']}{sep}{cap}", sit, "",
              "## " + T["musee_h"] + f" ({mk})", mp, f"{T['vrai']} {mv}", "", "## " + T["h_sites"]]
        for et, _, t, lien, p, n in sites(c, lg):
            l.append(f"- {t} [{et}]{sep}{p}" + (f" ({n})" if n else ""))
        l += ["", "## " + T["h_regions"]]
        for nom, mat, mot, txt, h, var, est_cap in regions(c, lg):
            l.append(f"- {nom} ({mat}{', ' + mot if mot else ''}){sep}{T['capitale'] if est_cap else ''}{txt} {T['humeur']}{sep}{h}"
                     + (f", {mat.lower()} {nombre(var, lg)}" if isinstance(var, (int, float)) else "") + ".")
        fo = foi(c, lg)
        l += ["", "## " + T["h_religion"], T["religion_p"]] + ([fo[1]] if fo else [])
        l += ["", "## " + T["h_mots"]] + [f"- {a} = {b} ({acc}/6)" for a, b, acc in mots_utiles(c, lg)] + [T["mots_note"], "", "## " + T["h_premieres"], T["premieres_note"]]
        for a, q, v in premieres(c, lg):
            l += [f"- {a}{sep}{q}", f"  {T['vrai']} {v}"]
        m = mandat_actuel(c)
        l += ["", "## " + T["h_piece"], T["piece_p"]]
        if m and (m.get("portrait") or {}).get("poids"):
            l += [T["piece_avers"].format(n=m.get("nom", ""), r=m.get("ere") or 1) + f" ({BASE}tourisme/piece-{m['id']}-{lg}.svg)",
                  f"{T['vrai']} {T['piece_vrai'].format(d=date_longue(m['portrait'].get('date', ''), lg))}"]
        else:
            l.append(T["piece_attente"].format(n=(m or {}).get("nom") or c["latest"].get("presidentNom") or "?"))
        l += ["", "## " + T["h_pratique"]] + [f"- {a}{sep}{b}" for a, b in T["pratique"]]
        l += ["", f"PDF{sep}{BASE}tourisme/depliant-fr.pdf · {BASE}tourisme/depliant-en.pdf", "", T["disclaimer"]]
    l += ["", maj(c, lg)]
    return "\n".join(l) + "\n"


# ---------------------------------------------------------------- dépliant PDF (bibliothèque standard seulement)
# A4 paysage, deux pages : extérieur (rabat, dos, couverture) puis intérieur (trois volets).
# Polices standard du PDF (Helvetica), codage WinAnsi : aucun fichier de police à embarquer.

W_HELV = dict(zip(range(32, 127), [
    278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278, 556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 278, 278, 584, 584, 584, 556,
    1015, 667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778, 667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469, 556,
    333, 556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556, 556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500, 334, 260, 334, 584]))
REMPLACE = {"−": "-", "’": "'", "“": "\"", "”": "\"", "✶": "*", "♛": "", "→": "->", " ": " ", " ": " "}
BASE_LETTRE = str.maketrans("àâäáãåçéèêëíìîïñóòôöõúùûüýÿÀÂÄÁÃÅÇÉÈÊËÍÌÎÏÑÓÒÔÖÕÚÙÛÜÝœŒæÆ«»…",
                            "aaaaaaceeeeiiiinooooouuuuyyAAAAAACEEEEIIIINOOOOOUUUUYoOaA\"\"_")
VERT, OR, ENCRE, GRIS, PAPIER, ROUGE = (0.05, 0.42, 0.28), (0.79, 0.64, 0.29), (0.08, 0.13, 0.10), (0.34, 0.40, 0.36), (0.96, 0.97, 0.95), (0.72, 0.21, 0.16)


def pdf_txt(s):
    s = "".join(REMPLACE.get(ch, ch) for ch in str(s))
    return s.encode("cp1252", "replace")


def largeur(s, taille, gras=False):
    w = sum(W_HELV.get(ord(ch.translate(BASE_LETTRE)[:1] or " "), 556) for ch in "".join(REMPLACE.get(x, x) for x in s))
    return w * taille / 1000 * (1.07 if gras else 1.0)


def couper(s, taille, w, gras=False):
    lignes, cur = [], ""
    for mot in str(s).split():
        essai = (cur + " " + mot).strip()
        if largeur(essai, taille, gras) <= w or not cur:
            cur = essai
        else:
            lignes.append(cur)
            cur = mot
    if cur:
        lignes.append(cur)
    return lignes


class Volet:
    """Un volet du dépliant : on y écrit de haut en bas ; ce qui ne tient pas est compté, pas imprimé."""
    def __init__(self, ops, x, y_haut, w, y_bas):
        self.ops, self.x, self.y, self.w, self.bas, self.perdu = ops, x, y_haut, w, y_bas, 0

    def place(self, h):
        if self.y - h < self.bas:
            self.perdu += 1
            return False
        return True

    def texte(self, s, taille=8.5, gras=False, couleur=ENCRE, interligne=1.3, avant=0, retrait=0, italique=False):
        police = "/F2" if gras else "/F3" if italique else "/F1"
        lignes = couper(s, taille, self.w - retrait, gras)
        self.y -= avant
        for li in lignes:
            if not self.place(taille * interligne):
                return
            self.y -= taille * interligne
            self.ops.append(b"BT %s %.1f Tf %.3f %.3f %.3f rg %.1f %.1f Td (" % (police.encode(), taille, *couleur, self.x + retrait, self.y)
                            + pdf_txt(li).replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)") + b") Tj ET")

    def titre(self, s):
        if not self.place(30):
            return
        self.y -= 8
        self.ops.append(b"%.3f %.3f %.3f rg %.1f %.1f %.1f 1.6 re f" % (*ENCRE, self.x, self.y, self.w))
        self.texte(s.upper(), 11.5, True, ENCRE, 1.25, avant=2)
        self.y -= 2

    def espace(self, h):
        self.y -= h


def drapeau(ops, x, y, w):
    h = w * 2 / 3
    k = w / 300
    def r(rx, ry, rw, rh, c):
        ops.append(b"%.3f %.3f %.3f rg %.2f %.2f %.2f %.2f re f" % (*c, x + rx * k, y + (200 - ry - rh) * k, rw * k, rh * k))
    r(0, 0, 300, 200, PAPIER)
    r(0, 0, 90, 200, VERT)
    r(90, 0, 6, 200, OR)
    for bx in (160, 176, 192, 208):
        r(bx, 64, 6, 14, OR)
        r(bx, 122, 6, 14, OR)
    for by in (84, 97, 110):
        r(140, by, 14, 6, OR)
        r(220, by, 14, 6, OR)
    r(152, 76, 70, 48, ENCRE)
    r(183, 96, 8, 8, VERT)
    r(158, 82, 4, 4, PAPIER)
    ops.append(b"%.3f %.3f %.3f RG 0.6 w %.2f %.2f %.2f %.2f re S" % (*GRIS, x, y, w, h))


def depliant(c, lg):
    T = L[lg]
    PW, PH, M = 842, 595, 26
    vw = PW / 3
    pages, perdu = [], 0
    regime, pres, cap, sit = situation(c, lg)

    # Extérieur : rabat intérieur (gauche), dos (milieu), couverture (droite)
    ops = [b"%.3f %.3f %.3f rg 0 0 %d %d re f" % (*PAPIER, PW, PH)]
    ops.append(b"%.3f %.3f %.3f rg %.1f 0 %.1f %d re f" % (*VERT, 2 * vw, vw, PH))
    v = Volet(ops, M, PH - M, vw - 2 * M, M)
    v.titre(T["h_mots"])
    for a, b, acc in mots_utiles(c, lg):
        v.texte(f"{a} : {b}  ({acc}/6)" if lg == "fr" else f"{a}: {b}  ({acc}/6)", 9)
    v.texte(T["mots_note"], 7.5, couleur=GRIS, avant=3)
    v.titre(T["h_pratique"])
    for a, b in T["pratique"]:
        v.texte(a, 8.5, True, avant=2)
        v.texte(b, 8.5)
    perdu += v.perdu
    v = Volet(ops, vw + M, PH - M, vw - 2 * M, M)
    v.titre(T["h_premieres"])
    v.texte(T["premieres_note"], 7.5, couleur=GRIS, italique=True)
    for a, q, val in premieres(c, lg):
        v.texte(a.upper(), 7, True, ROUGE, avant=5)
        v.texte(q, 9, True)
        v.texte(f"{T['vrai']} {val}", 7.5, couleur=GRIS)
    v.y = min(v.y, 120)
    v.texte(T["pdf_sur"], 8.5, True, avant=6)
    v.texte(BASE + ("en/" if lg == "en" else "") + "tourisme.html", 8.5, couleur=VERT)
    v.texte(T["pdf_fait"].format(n=c["latest"].get("day", "?"), d=date_longue(c["latest"].get("date", ""), lg)), 7, couleur=GRIS, avant=4)
    v.texte(T["disclaimer"], 6.5, couleur=GRIS, avant=4)
    perdu += v.perdu
    x0 = 2 * vw + M
    v = Volet(ops, x0, PH - M - 10, vw - 2 * M, M)
    v.texte(T["pdf_office"], 8.5, True, PAPIER)
    v.espace(16)
    drapeau(ops, x0, v.y - 150, 225)
    v.espace(170)
    for li in T["pdf_titre"]:
        v.texte(li, 30 if len(li) < 10 else 24, True, PAPIER, 1.05)
    v.texte(T["slogan"], 11, couleur=PAPIER, avant=10, italique=True)
    v.texte(T["chapo"], 8.5, couleur=PAPIER, avant=10)
    perdu += v.perdu
    pages.append(ops)

    # Intérieur : le pays ce soir et la religion · le musée et les sites · les six régions
    ops = [b"%.3f %.3f %.3f rg 0 0 %d %d re f" % (*PAPIER, PW, PH)]
    v = Volet(ops, M, PH - M, vw - 2 * M, M)
    v.titre(T["h_soir"])
    for a, b in ((T["regime"], regime), (T["chef"], pres), (T["cap"], cap)):
        v.texte(b, 14, True, VERT, 1.15, avant=3)
        v.texte(a, 7.5, couleur=GRIS)
    v.texte(sit, 7.5, couleur=GRIS, avant=4)
    v.titre(T["h_religion"])
    v.texte(T["religion_p"], 8.5)
    fo = foi(c, lg)
    if fo and v.place(18):
        f, t = fo
        v.espace(14)
        xx = v.x
        for part, col in ((f.get("croyants", 0), VERT), (f.get("agnostiques", 0), GRIS), (f.get("athees", 0), (0.81, 0.85, 0.82))):
            ww = (v.w) * part / 100
            ops.append(b"%.3f %.3f %.3f rg %.2f %.2f %.2f 9 re f" % (*col, xx, v.y, ww))
            xx += ww
        v.texte(t, 7.5, couleur=GRIS, avant=2)
    v.texte(T["genese"].replace("<b>", "").replace("</b>", ""), 8.5, avant=4)
    perdu += v.perdu
    v = Volet(ops, vw + M, PH - M, vw - 2 * M, M)
    mk, mp, mv, _ = musee(c, lg)
    v.texte(mk.upper(), 7, True, ROUGE)
    v.texte(T["musee_h"].upper(), 15, True, ENCRE, 1.05, avant=2)
    v.texte(mp, 8.5, avant=3)
    v.texte(f"{T['vrai']} {mv}", 7.5, couleur=GRIS, avant=3)
    v.titre(T["h_sites"])
    for et, cl, t, _lien, p, n in sites(c, lg):
        v.texte(t, 9, True, avant=3)
        v.texte(et.upper(), 6.5, True, VERT if cl == "on" else (0.6, 0.42, 0.05))
        v.texte(p + (f" ({n})" if n else ""), 8)
    perdu += v.perdu
    v = Volet(ops, 2 * vw + M, PH - M, vw - 2 * M, M)
    v.titre(T["h_regions"])
    for nom, mat, mot, txt, h, var, est_cap in regions(c, lg):
        v.texte(f"{nom.upper()}  ·  {mat}" + (f"  ·  « {mot} »" if mot and lg == "fr" else f"  ·  “{mot}”" if mot else ""), 9, True, VERT, avant=4)
        v.texte((T["capitale"] if est_cap else "") + txt, 8)
        v.texte(f"{T['humeur']}{' : ' if lg == 'fr' else ': '}{h}" + (f" · {mat.lower()} {nombre(var, lg)}" if isinstance(var, (int, float)) else ""), 7.5, couleur=GRIS)
    perdu += v.perdu
    for i in (1, 2):
        ops.append(b"%.3f %.3f %.3f RG 0.4 w [2 3] 0 d %.1f 8 m %.1f %d l S [] 0 d" % (*GRIS, i * vw, i * vw, PH - 8))
    pages.append(ops)
    return ecrire_pdf(pages, PW, PH, f"{T['titre']} — Microcontrôland"), perdu


def ecrire_pdf(pages, pw, ph, titre):
    objs = []
    def add(b):
        objs.append(b)
        return len(objs)
    f1 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    f2 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
    f3 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique /Encoding /WinAnsiEncoding >>")
    pages_id = len(objs) + 1 + 2 * len(pages)
    kids = []
    for ops in pages:
        flux = b"\n".join(ops)
        c = add(b"<< /Length %d >>\nstream\n" % len(flux) + flux + b"\nendstream")
        kids.append(add(b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %d %d] /Contents %d 0 R /Resources << /Font << /F1 %d 0 R /F2 %d 0 R /F3 %d 0 R >> >> >>"
                        % (pages_id, pw, ph, c, f1, f2, f3)))
    assert add(b"<< /Type /Pages /Kids [%s] /Count %d >>" % (b" ".join(b"%d 0 R" % k for k in kids), len(kids))) == pages_id
    info = add(b"<< /Title (" + pdf_txt(titre).replace(b"(", b"\\(").replace(b")", b"\\)") + b") /Producer (tourisme.py) >>")
    cat = add(b"<< /Type /Catalog /Pages %d 0 R >>" % pages_id)
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    pos = []
    for i, o in enumerate(objs, 1):
        pos.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    x = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1) + b"".join(b"%010d 00000 n \n" % p for p in pos)
    out += b"trailer\n<< /Size %d /Root %d 0 R /Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, cat, info, x)
    return bytes(out)


def main():
    racine = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    c = ctx(racine)
    (racine / "en").mkdir(exist_ok=True)
    for lg, d in (("fr", racine), ("en", racine / "en")):
        (d / "tourisme.html").write_text(page_ouverte(c, lg) if c["ouvert"] else page_fermee(c, lg), encoding="utf-8")
        (d / "tourisme.txt").write_text(texte(c, lg), encoding="utf-8")
    msg = ""
    if c["ouvert"]:
        (racine / "tourisme").mkdir(exist_ok=True)
        for m in frappes(c):
            for lg in ("fr", "en"):
                (racine / "tourisme" / f"piece-{m['id']}-{lg}.svg").write_text(svg_fichier(m, lg), encoding="utf-8")
        for lg in ("fr", "en"):
            pdf, perdu = depliant(c, lg)
            (racine / "tourisme" / f"depliant-{lg}.pdf").write_bytes(pdf)
            if perdu:
                msg += f" ; ATTENTION dépliant {lg} : {perdu} ligne(s) ne tiennent pas"
    print(f"tourisme.html, en/tourisme.html, tourisme.txt, en/tourisme.txt écrits : Office {'ouvert, dépliants écrits' if c['ouvert'] else 'fermé'}{msg}")


if __name__ == "__main__":
    main()
