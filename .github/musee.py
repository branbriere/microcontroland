"""Microcontrôland : « Le Musée national » (FR) / « The National Museum » (EN), visite 3D et visite en texte.

Le musée est PROCÉDURAL : il n'a aucun plan dessiné à la main. Chaque soir, ce script relit les fichiers déjà
publiés sur le site (data/latest.json, galerie.json, atelier.json, sculptures.json, sculptures-soir.json,
institutions.json) et la liste des salles
possibles (musee-catalogue.json), puis écrit musee.json, musee.html et en/musee.html. La visite 3D (musee.js)
construit les salles à partir de musee.json seulement : leur nombre, leur longueur et leur hauteur suivent les
données.

Comment il s'agrandit, sans geste à la main :
  · un nouveau président → un cadre de plus dans la salle des présidents (la salle s'allonge) ;
  · un nouveau soir de l'atelier → une œuvre de plus au mur des artistes ; un nouveau mois → une nouvelle salle ;
  · une nouvelle ère dans les données → une nouvelle aile, fermée jusqu'à ce que CETTE ère atteigne l'âge de la
    Mémoire (ages.etapes[2] de data/latest.json) ; l'aile de l'ère finie est figée : recopiée telle quelle de
    l'ancien musee.json, jamais recalculée ni modifiée (comme les données publiées) ;
  · une annexe passe de « en chantier » à « ouverte » quand son institution passe « en service » dans
    institutions.json ;
  · une nouveauté future (2e portrait du président en 1b-5, dessins 8×8, musique…) = une ligne de plus dans
    musee-catalogue.json ; si son type existe déjà (« portraits », « dessins », « artistes »), aucun code à écrire.

Rien n'est inventé ni recalculé : les portraits sont ceux de la galerie, les cartels sont écrits avec les mêmes
textes que la galerie, les dessins et les critiques sont ceux de l'atelier. Une salle sans données n'apparaît pas.
Licence MIT. Version 1.0, 2 novembre 2026 (firmware 0.8 / 0.9, site seulement). Version 1.2 : salle des sculptures et
sculpteurs du soir (art secondaire, cubes 8 × 8 × 8, âge de la Mémoire ; décision de Bran du 5/11/2026).

  python3 .github/musee.py <racine du site>
"""
import html
import importlib.util
import json
import sys
from pathlib import Path

VERSION = "1.2"
MEMOIRE = 2          # index de l'âge de la Mémoire dans ages.etapes : âge d'ouverture d'une aile (Bran, 28 oct. 2026)
BASE = "https://www.microcontroland.org/"
DONNEES = "https://donnees.microcontroland.org/"


def module(racine, nom):
    """Charge .github/<nom>.py du site : mêmes textes, mêmes portraits, mêmes dessins que les pages déjà en ligne."""
    spec = importlib.util.spec_from_file_location(nom, racine / ".github" / f"{nom}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def lire(f, defaut):
    try:
        return json.loads(Path(f).read_text(encoding="utf-8"))
    except (ValueError, OSError) as err:
        print(f"Ignoré : {f} ({err})", file=sys.stderr)
        return defaut


def e(x):
    return html.escape(str(x), quote=True)


# ---------------------------------------------------------------- textes du musée (anglais d'abord)

T = {
    "en": {
        "titre": "The National Museum", "haut": "Era {ere}, day {jour} · built automatically from the published data",
        "chapo": "Microcontrôland's museum has no architect. Every evening a script rebuilds it from the published data: "
                 "one wing per era, one room per kind of work, one frame per president, one picture per evening of the studio. "
                 "Nothing on its walls is drawn by hand.",
        "desc": "A 3D museum of Microcontrôland, rebuilt every evening from the published data: presidents' portraits, the studio's drawings, one wing per era.",
        "entrer": "Enter the museum in 3D", "entrer_note": "Loads about 1.3 MB. Mouse and keyboard, or touch. The text tour below shows exactly the same works.",
        "texte": "Text tour", "texte_intro": "The same rooms and the same captions as the 3D tour, for visitors without JavaScript and for AI agents.",
        "hall": "Entrance hall", "hall_txt": "Welcome to the National Museum of Microcontrôland. Everything shown here is computed from the published data.",
        "seul": "Visitor, you are the only one who can walk through every era. The Waïnas only ever see their own.",
        "compte": "{a} wing(s), {s} room(s), {o} work(s), rebuilt after issue no. {n} of {d}.",
        "aile": "Wing of era {ere}", "aile_fermee": "Waiting for the civilisation to evolve. This wing opens when era {ere} reaches the Age of Memory.",
        "aile_figee": "Era {ere} is over: this wing is frozen and will never change.",
        "suivante": "Wing of era {ere}", "suivante_txt": "Waiting for the civilisation to evolve.",
        "annexe_chantier": "Under construction.", "annexe_ouverte": "Open.",
        "voir": "See also: {lien}.", "verifier": "Check: {liens}.",
        "statue": "Statue of the network of President {nom}", "statue_txt": "The 81 weights of the citizen brain of the president in office, in three dimensions: 9 inputs, 6 hidden neurons, 3 outputs. "
                  "Green = positive connection, amber = negative; the thicker, the stronger. The brain that governs (75 weights) is not published yet.",
        "dessins_titre": "Evening of {d} · issue no. {n}", "dessins_txt": "{k} drawings, 20 per region. Artist of the evening: Citizen No. {a} ({r}).",
        "artiste": "{d} · Citizen No. {id} ({r}) · {c} square(s) changed",
        "pied": "The captions are a satirical convention; every date, score, weight and drawing comes from the published data. The Waïnas are neither alive nor conscious.",
        "maj_le": "Page updated automatically after issue no. {n} of {d}.",
        "ferme": "The museum opens when the country reaches the Age of Memory.",
        "pas_js": "The 3D tour needs JavaScript and WebGL; the text tour below shows the same works.",
        "sculptures_titre": "Evening of {d} · issue no. {n}", "sculptures_txt": "{k} sculptures of 8 × 8 × 8 cubes, one per citizen, computed from the 81 weights of each brain (rule S1). Sculptor of the evening: Citizen No. {a} ({r}).",
        "sculpteur": "{d} · Citizen No. {id} ({r}) · {c} cube(s) moved",
        "couches": "Read as 8 layers, from the bottom (left) to the top (right); the darker the square, the bigger the cube.",
    },
    "fr": {
        "titre": "Le Musée national", "haut": "Ère {ere}, jour {jour} · construit automatiquement à partir des données publiées",
        "chapo": "Le musée de Microcontrôland n'a pas d'architecte. Chaque soir, un script le reconstruit à partir des données publiées : "
                 "une aile par ère, une salle par genre d'œuvre, un cadre par président, un tableau par soir de l'atelier. "
                 "Rien sur ses murs n'est dessiné à la main.",
        "desc": "Un musée en 3D de Microcontrôland, reconstruit chaque soir à partir des données publiées : portraits des présidents, dessins de l'atelier, une aile par ère.",
        "entrer": "Entrer dans le musée en 3D", "entrer_note": "Environ 1,3 Mo à charger. Souris et clavier, ou doigt. La visite en texte ci-dessous montre exactement les mêmes œuvres.",
        "texte": "Visite en texte", "texte_intro": "Les mêmes salles et les mêmes cartels que la visite 3D, pour les visiteurs sans JavaScript et pour les agents IA.",
        "hall": "Hall d'accueil", "hall_txt": "Bienvenue au Musée national de Microcontrôland. Tout ce qui est exposé ici est calculé à partir des données publiées.",
        "seul": "Visiteur, vous êtes le seul à pouvoir parcourir toutes les ères. Les Waïnas ne voient jamais que la leur.",
        "compte": "{a} aile(s), {s} salle(s), {o} œuvre(s), reconstruit après l'édition n° {n} du {d}.",
        "aile": "Aile de l'ère {ere}", "aile_fermee": "En attente d'évolution de la civilisation. Cette aile ouvre quand l'ère {ere} atteint l'âge de la Mémoire.",
        "aile_figee": "L'ère {ere} est terminée : cette aile est figée et ne changera plus.",
        "suivante": "Aile de l'ère {ere}", "suivante_txt": "En attente d'évolution de la civilisation.",
        "annexe_chantier": "En chantier.", "annexe_ouverte": "Ouverte.",
        "voir": "Voir aussi : {lien}.", "verifier": "Vérifier : {liens}.",
        "statue": "Statue du réseau du président {nom}", "statue_txt": "Les 81 poids du cerveau de citoyen du président en fonction, en trois dimensions : 9 entrées, 6 neurones cachés, 3 sorties. "
                  "Vert = connexion positive, ambre = négative ; plus c'est épais, plus c'est fort. Le cerveau qui gouverne (75 poids) n'est pas encore publié.",
        "dessins_titre": "Soir du {d} · édition n° {n}", "dessins_txt": "{k} dessins, 20 par région. Artiste du soir : citoyen n° {a} ({r}).",
        "artiste": "{d} · citoyen n° {id} ({r}) · {c} case(s) changée(s)",
        "pied": "Les cartels sont une convention satirique ; chaque date, chaque score, chaque poids et chaque dessin vient des données publiées. Les Waïnas ne sont ni vivants ni conscients.",
        "maj_le": "Page mise à jour automatiquement après l'édition n° {n} du {d}.",
        "ferme": "Le musée ouvre quand le pays atteint l'âge de la Mémoire.",
        "pas_js": "La visite 3D demande JavaScript et WebGL ; la visite en texte ci-dessous montre les mêmes œuvres.",
        "sculptures_titre": "Soir du {d} · édition n° {n}", "sculptures_txt": "{k} sculptures de 8 × 8 × 8 cubes, une par citoyen, calculées à partir des 81 poids de chaque cerveau (règle S1). Sculpteur du soir : citoyen n° {a} ({r}).",
        "sculpteur": "{d} · citoyen n° {id} ({r}) · {c} cube(s) déplacé(s)",
        "couches": "Lecture en 8 couches, du bas (à gauche) vers le haut (à droite) ; plus la case est foncée, plus le cube est grand.",
    },
}


# ---------------------------------------------------------------- les salles, une fonction par type

def cartel_portrait(G, m, i, lg, suivant):
    """Même texte que le cartel de la galerie (galerie.py, fonction cadre), mais en champs séparés pour la 3D."""
    L = G.L[lg]
    H = L["h"]
    rg = G.REGION_EN.get(m["region"], m["region"]) if lg == "en" else m["region"]
    nom = m["nom"] or (f"No. {m['id']}" if lg == "en" else f"n° {m['id']}")
    lignes = []
    if m["debut"].get("coup"):
        lignes.append(L["coup_debut"].format(d=G.date_longue(m["debut"]["date"], lg), h=H(m["debut"]["heure"])))
    if m["elections"]:
        e0 = m["elections"][0]
        lignes.append(L["elu"].format(d=G.date_longue(e0["date"], lg), h=H(e0["heure"]), raison=L["raisons"][e0["raison"]], p=e0["pct"]))
        if len(m["elections"]) > 1:
            lignes.append(L["reelu"].format(liste=", ".join(f"{G.date_courte(x['date'], lg)} ({x['pct']}{'%' if lg == 'en' else ' %'})" for x in m["elections"][1:])))
    f = m["fin"]
    if f:
        lignes.append(L["fins"][f["genre"]].format(d=G.date_longue(f["date"], lg), h=H(f["heure"]), n=f.get("rebelles"), nom=f.get("nom_par") or f.get("par")))
        n = G.heures_entre(m["debut"], f)
        if n is not None:
            lignes.append(L["duree"].format(n=n) if n < 72 else L["duree_j"].format(j=n // 24, n=n % 24))
    info = L["cit"].format(n=m["id"], r=rg, rang=G.rang(L, i)) + (f' · {L["en_fonction"]}' if not f else "")
    p = m["portrait"]
    vide = None
    if p:
        bas = [L["technique"].format(d=G.date_longue(p["date"], lg), h=H(p["heure"]) if p["heure"] is not None else "?", t=p["tick"])]
        if m["releves"] >= 2:
            bas.append(L["fige"].format(n=m["releves"]) if m["identiques"] == m["releves"] else L["fige_non"].format(m=m["identiques"], n=m["releves"]))
    elif f and f["genre"] in ("revolte", "coup") and suivant:
        sn = suivant["nom"] or (f"No. {suivant['id']}" if lg == "en" else f"n° {suivant['id']}")
        vide = [L["censure"], L["censure_pourquoi"].format(nom=sn, quoi=L["quoi"][f["genre"]])]
        bas = [L["censure_faits_" + f["genre"]].format(nom=sn, h=G.heures_entre(f, suivant["debut"]))]
    else:
        vide = [L["vide"], L["vide_pourquoi"]]
        bas = [L["vide_sel"]]
    return {"nom": nom, "info": info, "lignes": lignes, "bas": bas, "vide": vide}


def salles_portraits(entree, ere, ctx):
    G, gal = ctx["galerie_py"], ctx["galerie"]
    if not gal or gal.get("ere") != ere or not gal.get("ouvert") or not gal.get("mandats"):
        return []
    ms = gal["mandats"]
    oeuvres = []
    for i, m in enumerate(ms):
        suivant = ms[i + 1] if i + 1 < len(ms) else None
        p = m.get("portrait")
        oeuvres.append({
            "id": m["id"], "nom": m["nom"], "region": m["region"],
            "svg": G.PEINDRE[gal.get("style") or G.STYLE_PORTRAIT](p["poids"], m["nom"]) if p else None,
            "poids": p["poids"] if p else None, "fichier": p["fichier"] if p else None,
            "cartel": {lg: cartel_portrait(G, m, i, lg, suivant) for lg in ("en", "fr")},
        })
    salle = {"id": entree["id"], "type": "portraits", "titre": entree["titre"], "lien": entree.get("lien"),
             "verifier": entree.get("verifier", []), "oeuvres": oeuvres}
    en_fonction = next((o for o, m in zip(oeuvres, ms) if not m["fin"] and o["poids"]), None)
    if en_fonction:
        salle["statue"] = {"id": en_fonction["id"], "nom": en_fonction["nom"], "poids": en_fonction["poids"], "fichier": en_fonction["fichier"]}
    return [salle]


def region_de(cid, lg, A):
    r = A.REGIONS[(cid - 1) // 20]
    return A.REGION_EN.get(r, r) if lg == "en" else r


def salles_dessins(entree, ere, ctx):
    jours = [j for j in (ctx["atelier"] or {}).get("jours", []) if j.get("ere") == ere and j.get("dessins")]
    if not jours:
        return []
    j = jours[-1]
    return [{"id": entree["id"], "type": "dessins", "titre": entree["titre"], "lien": entree.get("lien"), "verifier": entree.get("verifier", []),
             "date": j["date"], "edition": j["edition"], "jourEre": j["jourEre"], "regle": j.get("regle"),
             "president": j.get("president"), "artiste": j.get("artiste"), "dessins": j["dessins"],
             "critique": j.get("critique"), "source": j.get("source")}]


def salles_artistes(entree, ere, ctx):
    """Un tableau par soir de l'atelier ; une salle par mois (la salle du mois en cours s'allonge chaque soir)."""
    A = ctx["atelier_py"]
    jours = [j for j in (ctx["atelier"] or {}).get("jours", []) if j.get("ere") == ere and j.get("artiste") and j.get("dessins")]
    mois = {}
    for j in jours:
        mois.setdefault(j["date"][:7], []).append(j)
    salles = []
    for ym, js in mois.items():
        a, m = (int(x) for x in ym.split("-"))
        titre = {lg: f'{entree["titre"][lg]} · {A.MOIS[lg][m - 1]} {a}' for lg in ("en", "fr")}
        oeuvres = [{"date": j["date"], "edition": j["edition"], "jourEre": j["jourEre"], "id": j["artiste"],
                    "region": A.REGIONS[(j["artiste"] - 1) // 20], "dessin": j["dessins"][j["artiste"] - 1],
                    "cases": j.get("cases"), "critique": j.get("critique"), "source": j.get("source")} for j in js]
        salles.append({"id": f'{entree["id"]}-{ym}', "type": "artistes", "titre": titre, "lien": entree.get("lien"),
                       "verifier": entree.get("verifier", []), "oeuvres": oeuvres})
    return salles


def salles_sculptures(entree, ere, ctx):
    """Les 120 sculptures du dernier soir (sculptures-soir.json) et le cartel du soir (sculptures.json)."""
    S = ctx.get("sculptures_soir") or {}
    if S.get("ere") != ere or not any(S.get("sculptures") or []):
        return []
    j = next((x for x in reversed((ctx.get("sculptures") or {}).get("jours", [])) if x.get("ere") == ere and x.get("date") == S.get("date")), {})
    return [{"id": entree["id"], "type": "sculptures", "titre": entree["titre"], "lien": entree.get("lien"), "verifier": entree.get("verifier", []),
             "date": S["date"], "edition": S["edition"], "jourEre": S["jourEre"], "regle": S.get("regle"),
             "president": S.get("president"), "sculpteur": S.get("sculpteur"), "sculptures": S["sculptures"],
             "critique": j.get("critique"), "source": S.get("source")}]


def salles_sculpteurs(entree, ere, ctx):
    """Une sculpture par soir ; une salle par mois (la salle du mois en cours s'allonge chaque soir)."""
    A = ctx["atelier_py"]
    jours = [j for j in (ctx.get("sculptures") or {}).get("jours", []) if j.get("ere") == ere and j.get("sculpteur") and j.get("sculpture")]
    mois = {}
    for j in jours:
        mois.setdefault(j["date"][:7], []).append(j)
    salles = []
    for ym, js in mois.items():
        a, m = (int(x) for x in ym.split("-"))
        titre = {lg: f'{entree["titre"][lg]} · {A.MOIS[lg][m - 1]} {a}' for lg in ("en", "fr")}
        oeuvres = [{"date": j["date"], "edition": j["edition"], "jourEre": j["jourEre"], "id": j["sculpteur"],
                    "region": A.REGIONS[(j["sculpteur"] - 1) // 20], "sculpture": j["sculpture"],
                    "deplaces": j.get("deplaces"), "critique": j.get("critique"), "source": j.get("source")} for j in js]
        salles.append({"id": f'{entree["id"]}-{ym}', "type": "sculpteurs", "titre": titre, "lien": entree.get("lien"),
                       "verifier": entree.get("verifier", []), "oeuvres": oeuvres})
    return salles


# ---------------------------------------------------------------- la réclame du musée (humour, Bran 2/11/2026)
# Convention de la maison (comme l'Office du tourisme et l'Ambassade) : la blague est toujours suivie de
# « Ce qui est vrai », calculé à partir des mêmes données. Rien n'est prêté aux Waïnas.

def _s(n, lg, mot_fr, mot_en, pl_fr="s", pl_en="s"):
    return f"{n} {mot_fr}{pl_fr if n > 1 else ''}" if lg == "fr" else f"{n} {mot_en}{pl_en if n != 1 else ''}"


def reclame_salle(s, H):
    """Une plaque d'humour par salle ; les chiffres sont ceux de la salle."""
    if s["type"] == "portraits":
        n = len(s["oeuvres"]); p = sum(1 for o in s["oeuvres"] if o["poids"])
        return {
            "fr": {"titre": f"{H['portraits']:.1f} m sous plafond : la salle la plus haute du musée, pour laisser de la place aux ego.".replace(".", ",", 1),
                   "lignes": ["La statue officielle a été calculée, pas sculptée : le président n'a pas posé, ses poids si."],
                   "vrai": f"Ce qui est vrai : l'ego est bien l'une des 9 entrées du cerveau des Waïnas. {_s(n, 'fr', 'président', '')}, {_s(p, 'fr', 'portrait', '')} accroché{'s' if p > 1 else ''}, la hauteur des salles est fixée par le script."},
            "en": {"titre": f"{H['portraits']:.1f} m to the ceiling: the tallest room in the museum, to leave room for the egos.",
                   "lignes": ["The official statue was computed, not carved: the president did not sit for it, their weights did."],
                   "vrai": f"What is true: ego really is one of the 9 inputs of a Waïna brain. {_s(n, 'en', '', 'president')}, {_s(p, 'en', '', 'portrait')} on the walls; the script sets the height of each room."}}
    if s["type"] == "dessins":
        k = len(s["dessins"])
        return {
            "fr": {"titre": "Valeur de la collection : inestimable. Personne n'a encore réussi à l'estimer.",
                   "lignes": ["Le marché de l'art n'existe pas encore dans le pays ; les œuvres attendent leur premier collectionneur."],
                   "vrai": f"Ce qui est vrai : {k} dessins de 5 × 5 cases ce soir, un par citoyen, calculés à partir des 81 poids de chaque cerveau (règle B3) ; aucun n'a été vendu."},
            "en": {"titre": "Value of the collection: priceless. Nobody has managed to price it yet.",
                   "lignes": ["The country has no art market yet; the works are waiting for their first collector."],
                   "vrai": f"What is true: {k} drawings of 5 × 5 squares tonight, one per citizen, computed from the 81 weights of each brain (rule B3); none has been sold."}}
    if s["type"] == "artistes":
        n = len(s["oeuvres"])
        return {
            "fr": {"titre": "Collection permanente : un chef-d'œuvre de plus chaque soir, que le critique le veuille ou non.",
                   "lignes": ["Le musée s'agrandit tout seul. Les gardiens demandent une augmentation."],
                   "vrai": f"Ce qui est vrai : {_s(n, 'fr', 'tableau', '', 'x')} dans cette salle, un par soir de l'atelier ; il n'y a pas de gardien."},
            "en": {"titre": "Permanent collection: one more masterpiece every evening, whether the critic likes it or not.",
                   "lignes": ["The museum grows on its own. The attendants are asking for a raise."],
                   "vrai": f"What is true: {_s(n, 'en', '', 'picture')} in this room, one per evening of the studio; there are no attendants."}}
    if s["type"] == "sculptures":
        k = sum(1 for x in s["sculptures"] if x)
        return {
            "fr": {"titre": "Défense de toucher : les œuvres sont fragiles, elles n'existent pas.",
                   "lignes": ["Aucun ciseau, aucun marteau, aucun sculpteur n'a été blessé pendant la fabrication de cette salle."],
                   "vrai": f"Ce qui est vrai : {k} sculptures ce soir, une par citoyen, 127 cubes chacune sur une grille de 8 × 8 × 8, calculées à partir des 81 poids de chaque cerveau (règle S1) ; personne ne les a taillées."},
            "en": {"titre": "Do not touch: the works are fragile, they do not exist.",
                   "lignes": ["No chisel, no hammer and no sculptor was harmed in the making of this room."],
                   "vrai": f"What is true: {k} sculptures tonight, one per citizen, 127 cubes each on an 8 × 8 × 8 grid, computed from the 81 weights of each brain (rule S1); nobody carved them."}}
    if s["type"] == "sculpteurs":
        n = len(s["oeuvres"])
        return {
            "fr": {"titre": "Chaque soir, un nouveau socle. Le marbrier ne suit plus.",
                   "lignes": ["La salle s'allonge d'elle-même ; l'architecte, qui n'existe pas, n'a pas été prévenu."],
                   "vrai": f"Ce qui est vrai : {_s(n, 'fr', 'sculpture', '')} dans cette salle, une par soir ; le sculpteur du soir est le citoyen dont la sculpture a le plus changé depuis la veille. Il n'y a pas de marbrier."},
            "en": {"titre": "A new plinth every evening. The stonemason can no longer keep up.",
                   "lignes": ["The room lengthens by itself; the architect, who does not exist, was not told."],
                   "vrai": f"What is true: {_s(n, 'en', '', 'sculpture')} in this room, one per evening; the sculptor of the evening is the citizen whose sculpture changed most since the day before. There is no stonemason."}}
    return None


def reclame_hall(M):
    a, sa, o = M["ailes"], M["salles"], M["oeuvres"]
    return {
        "fr": {"titre": "Le plus grand musée virtuel du monde*",
               "lignes": ["* Du pays. Le plus petit aussi. Le seul, en fait.",
                          "Entrée : 0 octet. Vestiaire : inutile, vous n'êtes pas vraiment là."],
               "vrai": f"Ce qui est vrai : {_s(a, 'fr', 'aile', '')} ouverte{'s' if a > 1 else ''}, {_s(sa, 'fr', 'salle', '')}, {_s(o, 'fr', 'œuvre', '')}, toutes calculées à partir des données publiées."},
        "en": {"titre": "The largest virtual museum in the world*",
               "lignes": ["* In the country. Also the smallest. The only one, in fact.",
                          "Admission: 0 bytes. Cloakroom: unnecessary, you are not really here."],
               "vrai": f"What is true: {_s(a, 'en', '', 'wing')} open, {_s(sa, 'en', '', 'room')}, {_s(o, 'en', '', 'work')}, all computed from the published data."},
    }


ARCHITECTE = {
    "fr": {"titre": "Architecte : personne.",
           "lignes": ["Le musée se construit tout seul chaque soir, ce qui a beaucoup réduit les honoraires.",
                      "Merci de ne pas toucher les œuvres, sauf pour lire leur cartel."],
           "vrai": "Ce qui est vrai : un script public relit les données publiées et ajoute les salles ; aucune œuvre n'est dessinée à la main."},
    "en": {"titre": "Architect: nobody.",
           "lignes": ["The museum builds itself every evening, which has kept the fees very low.",
                      "Please do not touch the works, except to read their captions."],
           "vrai": "What is true: a public script reads the published data and adds the rooms; no work is drawn by hand."},
}
HAUTEURS = {"portraits": 6.2}


def cartel_fin(nb_cerveaux):
    """Cartel de sortie, philosophique (idée de Bran, 2/11/2026) : tout un pays sort d'une petite boîte.
    Faits d'Elite : Acornsoft, 1984 ; BBC Micro de 32 Ko de mémoire ; 8 galaxies de 256 systèmes (2 048),
    recalculés à partir de quelques nombres de départ au lieu d'être stockés."""
    octets = nb_cerveaux * 81
    o_fr = f"{octets:,}".replace(",", " ")
    o_en = f"{octets:,}"
    return {
        "fr": {"titre": "Tout un pays dans une boîte",
               "lignes": ["En 1984, le jeu Elite faisait tenir 8 galaxies de 256 planètes dans un ordinateur familial de 32 Ko. "
                          "L'univers n'était pas rangé dans la disquette : il était recalculé, à chaque voyage, à partir de quelques nombres.",
                          "Microcontrôland suit la même idée. Une petite boîte de 7 cartes, au fond d'un garage normand, "
                          "et chaque soir il en sort une République entière : ses élections, sa langue, ses présidents, ses dessins, et ce musée.",
                          f"Les cerveaux de ses {nb_cerveaux} citoyens tiennent en {o_fr} octets. Ce qui est grand, ce n'est pas la boîte : "
                          "c'est la distance entre la boîte et tout ce qu'on y lit."],
               "vrai": f"Ce qui est vrai : 7 cartes ESP32-S3 (1 passerelle, 6 régions) ; {nb_cerveaux} cerveaux de 81 poids d'un octet = {o_fr} octets ; "
                       "chaque œuvre de ce musée est calculée à partir des données publiées. Les Waïnas ne sont ni vivants ni conscients."},
        "en": {"titre": "A whole country in a box",
               "lignes": ["In 1984 the game Elite fitted 8 galaxies of 256 planets into a 32 KB home computer. "
                          "The universe was not stored on the disk: it was recomputed, on every journey, from a handful of numbers.",
                          "Microcontrôland follows the same idea. A small box of 7 boards at the back of a Normandy garage, "
                          "and every evening a whole Republic comes out of it: its elections, its language, its presidents, its drawings, and this museum.",
                          f"The brains of its {nb_cerveaux} citizens fit in {o_en} bytes. What is large is not the box: "
                          "it is the distance between the box and everything we read in it."],
               "vrai": f"What is true: 7 ESP32-S3 boards (1 gateway, 6 regions); {nb_cerveaux} brains of 81 one-byte weights = {o_en} bytes; "
                       "every work in this museum is computed from the published data. The Waïnas are neither alive nor conscious."},
    }


def cartel_fenetre(f):
    """Fenêtres sur le garage (idée de Bran, 2/11/2026 ; photos du 5/11/2026, vérifiées et floutées avant usage).
    Ce ne sont pas des œuvres : elles ne comptent pas dans le nombre d'œuvres du musée."""
    d = f["date"]
    a, m, j = (int(x) for x in d.split("-"))
    mois_fr = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"][m - 1]
    mois_en = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][m - 1]
    return {
        "fr": {"titre": f'{f["titre"]["fr"]} · Vue depuis la boîte',
               "lignes": ["Ce n'est pas une œuvre : c'est une fenêtre. Elle donne sur " + f["vue"]["fr"] + ". Dehors, c'est-à-dire dedans : le garage normand où vit le pays.",
                          "La boîte n'a pas d'yeux ; quelqu'un a donc pris la photo à sa place."],
               "vrai": f"Ce qui est vrai : vraie photo de l'intérieur du garage où se trouve la boîte, prise le {j}{'er' if j == 1 else ''} {mois_fr} {a} ; "
                       "métadonnées et position GPS retirées, détails qui permettraient de situer le lieu floutés. "
                       "C'est la seule image de ce musée qui n'est pas calculée."},
        "en": {"titre": f'{f["titre"]["en"]} · View from the box',
               "lignes": [f'This is not a work of art: it is a window. It looks out on {f["vue"]["en"]}. Outside, which is to say inside: the Normandy garage where the country lives.',
                          "The box has no eyes, so someone took the picture for it."],
               "vrai": f"What is true: a real photo of the inside of the garage where the box stands, taken on {j} {mois_en} {a}; "
                       "metadata and GPS position removed, details that could locate the place blurred. "
                       "It is the only picture in this museum that is not computed."},
    }


SALLE_FENETRES = {"fr": "Vue depuis la boîte", "en": "View from the box"}


def fenetres(catalogue, racine):
    """Une fenêtre n'apparaît que si sa photo est bien sur le site (sinon, mur plein)."""
    out = []
    for f in catalogue.get("fenetres", []):
        if not (racine / f["image"]).is_file():
            continue
        out.append({"id": f["id"], "image": f["image"], "largeur": f["largeur"], "hauteur": f["hauteur"],
                    "titre": f["titre"], "vue": f["vue"], "cartel": cartel_fenetre(f)})
    return out


TYPES = {"portraits": salles_portraits, "dessins": salles_dessins, "artistes": salles_artistes,
         "sculptures": salles_sculptures, "sculpteurs": salles_sculpteurs}


def aile(ere, ouverte, catalogue, ctx):
    a = {"ere": ere, "etat": "ouverte" if ouverte else "fermee", "figee": False, "salles": []}
    if not ouverte:
        return a
    etapes = ctx["etapes"]
    for entree in catalogue.get("salles", []):
        age = entree.get("age", 0)
        if not (len(etapes) > age and etapes[age].get("ouvert")):
            continue                      # audit des déblocages : une salle n'apparaît jamais avant son âge
        f = TYPES.get(entree.get("type"))
        if f is None:
            print(f"Type de salle inconnu ignoré : {entree.get('type')}", file=sys.stderr)
            continue
        a["salles"].extend(f(entree, ere, ctx))
    return a


def annexes(catalogue, institutions):
    par_id = {x.get("id"): x for x in (institutions or {}).get("institutions", [])}
    out = []
    for x in catalogue.get("annexes", []):
        inst = par_id.get(x.get("institution"))
        if not inst:
            continue
        out.append({"id": x["id"], "titre": x["titre"], "etat": "ouverte" if inst.get("etat") == "service" else "chantier",
                    "texte": {"fr": inst["fr"][1], "en": inst["en"][1]}, "lien": x.get("lien")})
    return out


def compter(ailes):
    s = sum(len(a["salles"]) for a in ailes)
    o = 0
    for a in ailes:
        for x in a["salles"]:
            o += len(x.get("oeuvres", [])) + len(x.get("dessins", [])) + (1 if x.get("statue") else 0)
            o += sum(1 for y in x.get("sculptures", []) if y)
    return {"ailes": sum(1 for a in ailes if a["etat"] != "fermee"), "salles": s, "oeuvres": o}


def construire(racine):
    latest = lire(racine / "data" / "latest.json", {})
    catalogue = lire(racine / "musee-catalogue.json", {"salles": [], "annexes": []})
    ancien = lire(racine / "musee.json", {}) if (racine / "musee.json").exists() else {}
    ere = int(latest.get("ere") or 1)
    etapes = (latest.get("ages") or {}).get("etapes") or []
    ctx = {"etapes": etapes, "galerie_py": module(racine, "galerie"), "atelier_py": module(racine, "atelier"),
           "galerie": lire(racine / "galerie.json", None), "atelier": lire(racine / "atelier.json", None),
           "sculptures": lire(racine / "sculptures.json", None) if (racine / "sculptures.json").exists() else None,
           "sculptures_soir": lire(racine / "sculptures-soir.json", None) if (racine / "sculptures-soir.json").exists() else None}
    ailes = []
    # Ailes des ères passées : recopiées telles quelles de l'ancien musee.json, jamais recalculées (figées).
    for a in ancien.get("plan", []):
        if a.get("ere", 0) < ere:
            a = dict(a)
            a["figee"] = True
            ailes.append(a)
    ouverte = len(etapes) > MEMOIRE and bool(etapes[MEMOIRE].get("ouvert"))
    courante = aile(ere, ouverte, catalogue, ctx)
    for x in courante["salles"]:
        r = reclame_salle(x, HAUTEURS)
        if r:
            x["reclame"] = r
    ailes.append(courante)
    ailes.sort(key=lambda a: a["ere"])
    M = {
        "format": 1, "version": VERSION, "ere": ere, "jourEre": latest.get("jourEre"),
        "edition": latest.get("day"), "date": latest.get("date"),
        "note": "Construit chaque soir par .github/musee.py à partir des seuls fichiers publiés ; aucune œuvre dessinée à la main. "
                "Poids : entier x 5 / 127, ordre w1[6][10] (biais en dernier) puis w2[3][7]. Dessins : 25 cases, ligne par ligne, 1 = plein. "
                "Sculptures : 512 chiffres, case i*64 + j*8 + k pour X = i, Y = j, Z = k (Z = hauteur), 0 = vide, 1 à 9 = taille du cube.",
        **compter(ailes),   # « ailes », « salles », « oeuvres » : nombres lus aussi par l'Office du tourisme (tourisme.py)
        "annexes": annexes(catalogue, lire(racine / "institutions.json", {})),
        "plan": ailes,
        "suivante": {"ere": ere + 1},
    }
    M["reclame"] = reclame_hall(M)
    M["architecte"] = ARCHITECTE
    dessins = next((x["dessins"] for x in courante["salles"] if x["type"] == "dessins"), None)
    M["fin"] = cartel_fin(len(dessins) if dessins else 120)
    F = fenetres(catalogue, racine)
    if F:
        M["fenetres"] = {"salle": SALLE_FENETRES, "liste": F}
    return M


# ---------------------------------------------------------------- la page (visite en texte + bouton 3D)

STYLE = """<style>
.m-entrer{display:flex;flex-wrap:wrap;gap:10px 16px;align-items:center;margin:14px 0 6px}
.m-entrer button{font:600 15px var(--f-data, system-ui);padding:10px 16px;border-radius:8px;border:1px solid var(--ink);background:var(--ink);color:var(--sheet);cursor:pointer}
.m-entrer small{color:var(--muted)}
.m-aile{border-top:2px solid var(--ink);margin-top:26px;padding-top:6px}
.m-salle{border-top:1px solid var(--rule);margin-top:16px;padding-top:6px}
.m-oeuvres{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,190px),1fr));gap:16px;margin:10px 0}
.m-oeuvres figure{margin:0;display:grid;gap:6px;min-width:0}
.m-oeuvres svg{width:100%;height:auto;display:block;background:#fff;border:1px solid var(--rule)}
.m-oeuvres figcaption{font:12.5px/1.5 var(--f-data, system-ui);color:var(--muted)}
.m-oeuvres figcaption b{color:var(--ink);font-size:1.15em}
.m-vide{aspect-ratio:3/4;display:grid;place-content:center;text-align:center;padding:12px;border:1px dashed var(--rule);color:var(--muted)}
.m-dessin{max-width:96px}
.m-sculpture{width:100%;max-width:420px;height:auto;display:block;background:transparent}
.m-oeuvres-l{grid-template-columns:repeat(auto-fill,minmax(min(100%,300px),1fr))}
.m-reclame{margin:10px 0;padding:8px 14px;border-left:3px solid var(--ink)}
.m-reclame p{margin:.3em 0}
.compte{font:13px var(--f-data);color:var(--muted)}
#musee3d{position:fixed;inset:0;z-index:50;background:#121619}
#musee3d[hidden]{display:none}
</style>"""


def svg_dessin(bits, titre):
    n = int(round(len(bits) ** 0.5))
    c = 10
    r = "".join(f'<rect x="{(k % n) * c}" y="{(k // n) * c}" width="{c}" height="{c}" fill="#1d2326"/>' for k, b in enumerate(bits) if b == "1")
    return f'<svg class="m-dessin" viewBox="0 0 {n * c} {n * c}" role="img" aria-label="{e(titre)}"><rect width="{n * c}" height="{n * c}" fill="#fff"/>{r}</svg>'


def svg_sculpture(s, titre):
    """Image fixe pour la visite en texte : les 8 couches (Z = 0 en bas, à gauche), plus foncé = plus grand cube."""
    c, g = 6, 8
    out = []
    for k in range(8):
        ox = k * (g * c + 6)
        out.append(f'<rect x="{ox}" y="0" width="{g * c}" height="{g * c}" fill="#fff" stroke="#c9ccc8" stroke-width="1"/>')
        for i in range(8):
            for j in range(8):
                v = int(s[i * 64 + j * 8 + k])
                if v:
                    out.append(f'<rect x="{ox + i * c}" y="{(7 - j) * c}" width="{c}" height="{c}" fill="#1d2326" fill-opacity="{0.25 + 0.75 * v / 9:.2f}"/>')
    w = 8 * (g * c + 6) - 6
    return f'<svg class="m-sculpture" viewBox="0 0 {w} {g * c}" role="img" aria-label="{e(titre)}">{"".join(out)}</svg>'


def plaque_txt(r):
    return (f'<blockquote class="m-reclame"><p><b>{e(r["titre"])}</b></p>' + "".join(f"<p>{e(t)}</p>" for t in r["lignes"])
            + f'<p><small>{e(r["vrai"])}</small></p></blockquote>')


def lignes_dessin(bits):
    n = int(round(len(bits) ** 0.5))
    return " / ".join(bits[i * n:(i + 1) * n].replace("1", "■").replace("0", "□") for i in range(n))


def page(M, latest, lg, G, A):
    L, X = G.L[lg], T[lg]
    pre = "../" if lg == "en" else ""
    autre_lg, autre_nom, autre_rss, autre_titre = L["autre"]
    fr_url, en_url = BASE + "musee.html", BASE + "en/musee.html"
    liens = ["./", "archives.html", "histoire.html", "langue.html", "citoyen.html", "ambassade.html", "tourisme.html", "temple.html", "recherche.html", "projet.html", pre + L["rss"]]
    nav = "\n".join(f'    <a href="{h}">{e(t)}</a>' for h, t in zip(liens, L["menu"]))
    dl = G.date_longue(str(latest.get("date", "")), lg)
    c = M
    corps = []
    ouvert = any(a["etat"] != "fermee" for a in M["plan"])
    if not ouvert:
        corps.append(f'<p>{e(X["ferme"])}</p>')
    else:
        corps.append(f'<div class="m-entrer" id="m-entrer" hidden><button type="button" id="m-bouton">{e(X["entrer"])}</button>'
                     f'<small>{e(X["entrer_note"])}</small></div>')
        corps.append(f'<noscript><p><small>{e(X["pas_js"])}</small></p></noscript>')
        corps.append(f'<h2>{e(X["texte"])}</h2><p>{e(X["texte_intro"])}</p>')
        corps.append(f'<section class="m-salle"><h3>{e(X["hall"])}</h3><p>{e(X["hall_txt"])}</p>{plaque_txt(M["reclame"][lg])}{plaque_txt(M["architecte"][lg])}<p><i>{e(X["seul"])}</i></p>'
                     f'<p class="compte">{e(X["compte"].format(a=c["ailes"], s=c["salles"], o=c["oeuvres"], n=M["edition"], d=dl))}</p>')
        for x in M["annexes"]:
            etat = X["annexe_ouverte"] if x["etat"] == "ouverte" else X["annexe_chantier"]
            lien = f' <a href="{e(x["lien"])}">{e(x["lien"])}</a>' if x.get("lien") else ""
            corps.append(f'<p><b>{e(x["titre"][lg])}</b> · {e(etat)} {e(x["texte"][lg])}{lien}</p>')
        corps.append('</section>')
        for a in M["plan"]:
            corps.append(f'<section class="m-aile"><h2>{e(X["aile"].format(ere=a["ere"]))}</h2>')
            if a["etat"] == "fermee":
                corps.append(f'<p>{e(X["aile_fermee"].format(ere=a["ere"]))}</p></section>')
                continue
            if a.get("figee"):
                corps.append(f'<p><i>{e(X["aile_figee"].format(ere=a["ere"]))}</i></p>')
            for s in a["salles"]:
                corps.append(f'<section class="m-salle"><h3>{e(s["titre"][lg])}</h3>' + (plaque_txt(s["reclame"][lg]) if s.get("reclame") else ""))
                if s["type"] == "portraits":
                    if s.get("statue"):
                        st = s["statue"]
                        corps.append(f'<p><b>{e(X["statue"].format(nom=st["nom"]))}.</b> {e(X["statue_txt"])}</p>')
                    figs = []
                    for o in s["oeuvres"]:
                        k = o["cartel"][lg]
                        art = o["svg"] if o["svg"] else f'<div class="m-vide"><b>{e(k["vide"][0])}</b><span>{e(k["vide"][1])}</span></div>'
                        txt = "<br>".join(e(t) for t in [k["info"]] + k["lignes"] + k["bas"])
                        figs.append(f'<figure>{art}<figcaption><b>{e(k["nom"])}</b><br>{txt}</figcaption></figure>')
                    corps.append(f'<div class="m-oeuvres">{"".join(figs)}</div>')
                elif s["type"] == "dessins":
                    a_id = s["artiste"]
                    corps.append(f'<p><b>{e(X["dessins_titre"].format(d=G.date_longue(s["date"], lg), n=s["edition"]))}.</b> '
                                 f'{e(X["dessins_txt"].format(k=len(s["dessins"]), a=a_id, r=region_de(a_id, lg, A)))}</p>')
                    cr = (s.get("critique") or {}).get(lg) or []
                    corps.append("".join(f"<p><i>{e(t)}</i></p>" for t in cr))
                elif s["type"] == "sculptures":
                    a_id = s["sculpteur"]
                    corps.append(f'<p><b>{e(X["sculptures_titre"].format(d=G.date_longue(s["date"], lg), n=s["edition"]))}.</b> '
                                 f'{e(X["sculptures_txt"].format(k=sum(1 for x in s["sculptures"] if x), a=a_id, r=region_de(a_id, lg, A)))}</p>')
                    cr = (s.get("critique") or {}).get(lg) or []
                    corps.append("".join(f"<p><i>{e(t)}</i></p>" for t in cr))
                    if a_id and s["sculptures"][a_id - 1]:
                        corps.append(f'<figure>{svg_sculpture(s["sculptures"][a_id - 1], X["sculptures_txt"].format(k=1, a=a_id, r=region_de(a_id, lg, A)))}'
                                     f'<figcaption><small>{e(X["couches"])}</small></figcaption></figure>')
                elif s["type"] == "sculpteurs":
                    figs = []
                    for o in s["oeuvres"]:
                        rg = A.REGION_EN.get(o["region"], o["region"]) if lg == "en" else o["region"]
                        cap = X["sculpteur"].format(d=G.date_longue(o["date"], lg), id=o["id"], r=rg, c=o["deplaces"] if o["deplaces"] is not None else "?")
                        cr = (o.get("critique") or {}).get(lg) or []
                        figs.append(f'<figure>{svg_sculpture(o["sculpture"], cap)}<figcaption><b>{e(cap)}</b><br>{"<br>".join(e(t) for t in cr)}</figcaption></figure>')
                    corps.append(f'<div class="m-oeuvres m-oeuvres-l">{"".join(figs)}</div><p><small>{e(X["couches"])}</small></p>')
                elif s["type"] == "artistes":
                    figs = []
                    for o in s["oeuvres"]:
                        rg = A.REGION_EN.get(o["region"], o["region"]) if lg == "en" else o["region"]
                        cap = X["artiste"].format(d=G.date_longue(o["date"], lg), id=o["id"], r=rg, c=o["cases"])
                        cr = (o.get("critique") or {}).get(lg) or []
                        figs.append(f'<figure>{svg_dessin(o["dessin"], cap)}<figcaption><b>{e(cap)}</b><br>'
                                    f'{e(lignes_dessin(o["dessin"]))}<br>{"<br>".join(e(t) for t in cr)}</figcaption></figure>')
                    corps.append(f'<div class="m-oeuvres">{"".join(figs)}</div>')
                bouts = []
                if s.get("lien"):
                    a_lien = '<a href="' + e(s["lien"]) + '">' + e(s["lien"]) + '</a>'
                    bouts.append(f'<p>{X["voir"].format(lien=a_lien)}</p>')
                if s.get("verifier"):
                    ls = ", ".join(f'<a href="{e(v)}">{e(v)}</a>' for v in s["verifier"])
                    bouts.append(f'<p><small>{X["verifier"].format(liens=ls)}</small></p>')
                corps.append("".join(bouts) + "</section>")
            corps.append('</section>')
        if M.get("fin"):
            corps.append(f'<section class="m-aile"><h2>{e(M["fin"][lg]["titre"])}</h2>' + "".join(f"<p>{e(t)}</p>" for t in M["fin"][lg]["lignes"])
                         + f'<p><small>{e(M["fin"][lg]["vrai"])}</small></p></section>')
        if M.get("fenetres"):
            F = M["fenetres"]
            figs = "".join(f'<figure><img src="{pre}{e(f["image"])}" width="{f["largeur"]}" height="{f["hauteur"]}" loading="lazy" '
                           f'style="width:100%;height:auto" alt="{e(f["cartel"][lg]["lignes"][0])}">'
                           f'<figcaption><b>{e(f["titre"][lg])}</b><br>{e(f["vue"][lg])}</figcaption></figure>' for f in F["liste"])
            corps.append(f'<section class="m-aile"><h2>{e(F["salle"][lg])}</h2><p>{e(F["liste"][0]["cartel"][lg]["lignes"][0].split(". ")[0])}.</p>'
                         f'<div class="m-oeuvres">{figs}</div><p><small>{e(F["liste"][0]["cartel"][lg]["vrai"])}</small></p></section>')
        corps.append(f'<section class="m-aile"><h2>{e(X["suivante"].format(ere=M["suivante"]["ere"]))}</h2><p>{e(X["suivante_txt"])}</p></section>')
        ls = ", ".join('<a href="' + pre + f + '">' + f + '</a>' for f in ("musee.json", "musee-catalogue.json"))
        corps.append(f'<p><small>{X["verifier"].format(liens=ls)}</small></p>')
    maj = X["maj_le"].format(n=latest.get("day", "?"), d=dl)
    haut = X["haut"].format(ere=M["ere"], jour=M.get("jourEre") or "?")
    return f"""<!doctype html>
<html lang="{lg}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<link rel="icon" href="{pre}favicon.ico" sizes="32x32">
<link rel="icon" href="{pre}favicon.svg" type="image/svg+xml">
<title>{e(X["titre"])} — Microcontrôland</title>
<meta name="description" content="{e(X["desc"])}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="La Puce Libre — Microcontrôland">
<meta property="og:title" content="{e(X["titre"])} — Microcontrôland">
<meta property="og:description" content="{e(X["desc"])}">
<link rel="alternate" hreflang="fr" href="{fr_url}">
<link rel="alternate" hreflang="en" href="{en_url}">
<link rel="alternate" hreflang="x-default" href="{fr_url}">
<link rel="alternate" type="application/rss+xml" title="La Puce Libre" href="{pre}{L["rss"]}">
<link rel="alternate" type="application/rss+xml" title="{e(autre_titre)}" hreflang="{autre_lg}" href="{pre}{autre_rss}">
<link rel="alternate" type="application/json" href="{pre}musee.json">
<link rel="stylesheet" href="{pre}style.css">
<script src="{pre}mesure.js" defer></script>
{STYLE}
</head>
<body>
<div class="wrap">
  <header class="mast">
    <div class="top"><span>{e(L["mast"][0])}</span><span>{e(X["titre"])}</span></div>
    <div class="title"><a href="./">La Puce <span>Libre</span></a></div>
    <p class="tag">{e(L["tag"])}</p>
  </header>
  <nav class="main" aria-label="Navigation">
{nav}
  </nav>

  <div class="prose">
    <p class="compte">{e(haut)}</p>
    <h1>{e(X["titre"])}</h1>
    <p class="chapo">{e(X["chapo"])}</p>
    {"".join(corps)}
    <p><small>{e(X["pied"])}</small></p>
    <p><small>{e(maj)}</small></p>
  </div>

  <footer class="site">
    <span><a href="./">{e(L["retour"])}</a></span>
    <span><a href="{'en/' if lg == 'fr' else '../'}musee.html">{e(autre_nom)}</a></span>
    <span><a href="mentions.html">{e(L["mentions"])}</a></span>
  </footer>
</div>
<div id="musee3d" hidden></div>
{'<script>window.MCL_BASE = "../";</script>' if lg == "en" else ""}
<script src="{pre}reglages.js"></script>
<script src="{pre}commun.js"></script>
<script src="{pre}lang.js"></script>
<script src="{pre}musee.js" defer></script>
</body>
</html>
"""


def mettre_a_jour(racine):
    latest = lire(racine / "data" / "latest.json", {})
    M = construire(racine)
    G, A = module(racine, "galerie"), module(racine, "atelier")
    (racine / "musee.json").write_text(json.dumps(M, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    (racine / "musee.html").write_text(page(M, latest, "fr", G, A), encoding="utf-8")
    (racine / "en").mkdir(exist_ok=True)
    (racine / "en" / "musee.html").write_text(page(M, latest, "en", G, A), encoding="utf-8")
    c = M
    print(f"musée : {c['ailes']} aile(s) ouverte(s), {c['salles']} salle(s), {c['oeuvres']} œuvre(s)")
    return M


def main():
    args = sys.argv[1:]
    mettre_a_jour(Path(args[0] if args else "."))


if __name__ == "__main__":
    main()
