"""Microcontrôland : page « L'atelier » (FR) et « The Studio » (EN), l'art primitif des Waïnas.

Chaque soir, un dessin de 5 × 5 cases calculé à partir des 81 poids publiés de chaque citoyen
(fichier brut quotidien du dépôt microcontroland-data, format 3 et suivants), et deux lignes du critique.

Règle B3 (validée par Bran le 26 octobre 2026) : pour la case de la colonne j et de la ligne i,
X = (j - 2) / 2 et Y = (i - 2) / 2. Le cerveau reçoit les 9 nombres X, Y, |X|, |Y|, √(X² + Y²), X·Y,
X + Y, X − Y et 1, sans bruit ; on lit sa première sortie (« soutien »). La case est pleine si la valeur
dépasse la médiane des 25 valeurs. Ces nombres ne décrivent aucune situation de la vie du citoyen :
le dessin est un portrait mathématique du cerveau, pas une intention.

Artiste du soir : le citoyen dont le dessin a le plus changé depuis la veille ; à égalité, un tour selon
le jour de l'ère ; si rien n'a changé (ou pas de veille), un tour parmi tous les dessins du soir.
Région incomplète (poids null) : pas de dessin, jamais de zéros à la place.

atelier.json garde chaque soir déjà exposé ; une journée déjà écrite n'est jamais réécrite.
La passerelle et le journal ne changent pas. Licence MIT. Version 1.0, 26 octobre 2026 (firmware 0.8).

  python3 .github/atelier.py <racine du site> [--source URL_OU_DOSSIER] [--attendre SECONDES]
"""
import hashlib
import html
import json
import math
import sys
import time
import urllib.request
from pathlib import Path

BASE = "https://www.microcontroland.org/"
SOURCE = "https://raw.githubusercontent.com/branbriere/microcontroland-data/main/"
DONNEES = "https://donnees.microcontroland.org/"
REGLE = "B3 v1"
N = 5
REGIONS = ["Mines", "Champs", "Raffineries", "Barrage", "Port", "Ville"]
REGION_EN = {"Mines": "Mines", "Champs": "Fields", "Raffineries": "Refineries", "Barrage": "Dam", "Port": "Harbour", "Ville": "City"}
MOIS = {"fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"],
        "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]}
ARCHIVE_VISIBLE = 30


# ---------------------------------------------------------------- le dessin (règle B3)

def cerveau(poids):
    """81 entiers int8 (valeur × 5 / 127), ordre w1[6][10] (biais en dernier) puis w2[3][7]."""
    w = [x * 5.0 / 127.0 for x in poids]
    return [w[i * 10:(i + 1) * 10] for i in range(6)], [w[60 + k * 7:60 + (k + 1) * 7] for k in range(3)]


def soutien(c, x):
    w1, w2 = c
    h = [math.tanh(r[9] + sum(r[j] * x[j] for j in range(9))) for r in w1]
    r = w2[0]
    return 1.0 / (1.0 + math.exp(-(r[6] + sum(r[j] * h[j] for j in range(6)))))


def dessin(poids):
    """Chaîne de 25 caractères, ligne par ligne, « 1 » = case pleine."""
    c = cerveau(poids)
    v = []
    for i in range(N):
        for j in range(N):
            X, Y = (j - (N - 1) / 2) / ((N - 1) / 2), (i - (N - 1) / 2) / ((N - 1) / 2)
            v.append(soutien(c, [X, Y, abs(X), abs(Y), math.hypot(X, Y), X * Y, X + Y, X - Y, 1.0]))
    m = sorted(v)[len(v) // 2]
    return "".join("1" if x > m else "0" for x in v)


def dessins_du_jour(brut):
    """120 dessins (None quand la région n'a pas envoyé tous ses poids ce jour-là)."""
    out = [None] * 120
    regs = ((brut.get("poids") or {}).get("regions")) or []
    for r in range(6):
        reg = regs[r] if r < len(regs) else None
        if not reg or not isinstance(reg.get("citoyens"), list) or len(reg["citoyens"]) != 20:
            continue
        for k, p in enumerate(reg["citoyens"]):
            if isinstance(p, list) and len(p) == 81:
                out[r * 20 + k] = dessin(p)
    return out


# ---------------------------------------------------------------- les faits mesurés

def ecart(a, b):
    return sum(1 for p, q in zip(a, b) if p != q)


def symetrie(g):
    return sum(1 for i in range(N) for j in range(N) if g[i * N + j] == g[i * N + N - 1 - j])


def moitie_haute(g):
    return sum(1 for c in g[:10] if c == "1"), sum(1 for c in g[15:] if c == "1")


def choisir(jour, veille):
    """(numéro de l'artiste, cases changées ou None)."""
    if veille:
        ch = {i + 1: ecart(jour[i], veille[i]) for i in range(120) if jour[i] and veille[i]}
        mx = max(ch.values(), default=0)
        if mx > 0:
            ex = sorted(i for i, n in ch.items() if n == mx)
            return ex, mx
    return None, 0


def president(brut):
    for c in brut.get("citoyens") or []:
        if c and "president" in (c.get("etat") or []):
            return c.get("id")
    return None


# ---------------------------------------------------------------- le critique (deux lignes, anglais d'abord)

def critique(f, jour_ere):
    """Deux lignes par langue. La première est l'avis du critique ; la seconde donne toujours les faits.
    Aucune intention n'est prêtée au citoyen : il ne sait pas qu'il dessine."""
    n, rg_fr, rg_en = f["id"], f["region"], REGION_EN.get(f["region"], f["region"])
    A_en, A_fr = f"Citizen No. {n} of the {rg_en}", f"le citoyen n° {n} ({rg_fr})"
    Af = A_fr[0].upper() + A_fr[1:]
    v = jour_ere

    def pick(lst):
        return lst[v % len(lst)]

    s, ch, tw, stable = f["symetrie"], f["cases"], f["jumeaux"], f["stable"]
    if f["president"]:
        en1, fr1 = pick([(f"The President's work hangs in the place of honour, as protocol requires.",
                          f"L'œuvre du président occupe la place d'honneur, comme le veut le protocole."),
                         (f"From the palace, a work of rare constancy.", f"Du palais, une œuvre d'une rare constance.")])
        en2 = f"The facts: {A_en} holds the presidency; a president's citizen brain neither computes nor learns during the term, so the drawing cannot change until it ends."
        fr2 = f"Les faits : {A_fr} est président ; pendant le mandat, son cerveau de citoyen ne calcule ni n'apprend, et le dessin ne peut pas changer avant la fin du mandat."
    elif f["premiere"]:
        en1, fr1 = pick([(f"Opening night at the Studio: {A_en} is the first to hang.", f"Vernissage à l'atelier : {A_fr} ouvre le bal."),
                         (f"A new exhibition opens, and {A_en} takes the first wall.", f"Nouvelle exposition : {A_fr} prend le premier mur.")])
        en2 = f"The facts: no drawing from the previous day to compare with; tonight's artist was chosen by rotation. {f['pleines']} of 25 squares are filled."
        fr2 = f"Les faits : aucun dessin de la veille pour comparer ; l'artiste du soir est désigné par roulement. {f['pleines']} cases pleines sur 25."
    elif tw:
        autres_en = ", ".join(f"No. {x}" for x in tw[:3]) + (" and others" if len(tw) > 3 else "")
        autres_fr = ", ".join(f"n° {x}" for x in tw[:3]) + (" et d'autres" if len(tw) > 3 else "")
        en1, fr1 = pick([(f"A school is born: {A_en} draws exactly like {autres_en}.", f"Une école est née : {A_fr} dessine exactement comme {autres_fr}."),
                         (f"The critic suspects a movement, perhaps a plagiarism.", f"Le critique soupçonne un mouvement, voire un plagiat.")])
        en2 = f"The facts: {A_en} changed {ch} of 25 squares since yesterday and now has the same drawing as {len(tw)} other citizen{'s' if len(tw) > 1 else ''} ({autres_en}). Nobody copied anyone: similar brains give similar drawings."
        fr2 = f"Les faits : {A_fr} a changé {ch} cases sur 25 depuis hier et a maintenant le même dessin que {len(tw)} autre{'s' if len(tw) > 1 else ''} citoyen{'s' if len(tw) > 1 else ''} ({autres_fr}). Personne n'a copié personne : des cerveaux proches donnent des dessins proches."
    elif ch >= 8:
        haut, bas = f["haut"], f["bas"]
        detail_en = " The upper half now carries the weight." if haut >= bas + 4 else " The lower half now carries the weight." if bas >= haut + 4 else ""
        detail_fr = " Tout le poids monte dans la moitié haute." if haut >= bas + 4 else " Tout le poids descend dans la moitié basse." if bas >= haut + 4 else ""
        en1, fr1 = pick([(f"A clean break from {A_en}: the work turns its back on yesterday's.{detail_en}", f"Rupture nette chez {A_fr} : l'œuvre tourne le dos à celle d'hier.{detail_fr}"),
                         (f"The critic speaks of a manifesto from {A_en}.{detail_en}", f"Le critique parle de manifeste chez {A_fr}.{detail_fr}")])
        en2 = f"The facts: {ch} of the 25 squares changed overnight, as the brain went on learning. The artist was not consulted, having no opinion on the matter."
        fr2 = f"Les faits : {ch} cases sur 25 ont changé en une nuit, au fil de ce que le cerveau a appris. L'artiste n'a pas été consulté, faute d'avis sur la question."
    elif s == 25:
        en1, fr1 = pick([(f"Perfect symmetry from {A_en}: the critic reaches for a mirror.", f"Symétrie parfaite chez {A_fr} : le critique cherche un miroir."),
                         (f"Left and right agree at last, in the work of {A_en}.", f"La gauche et la droite tombent enfin d'accord, chez {A_fr}.")])
        en2 = f"The facts: each square matches its mirror image; {ch} of 25 squares changed since yesterday."
        fr2 = f"Les faits : chaque case est identique à son reflet ; {ch} cases sur 25 ont changé depuis hier."
    elif ch <= 3:
        en1, fr1 = pick([(f"{A_en} retouches rather than repaints: the art of the detail.", f"{Af} retouche plutôt qu'il ne repeint : l'art du détail."),
                         (f"A discreet evolution from {A_en}, for the connoisseur only.", f"Évolution discrète chez {A_fr}, réservée aux connaisseurs.")])
        apres_en = f", after {stable} day{'s' if stable != 1 else ''} without any change" if stable else ""
        apres_fr = f", après {stable} jour{'s' if stable != 1 else ''} sans aucun changement" if stable else ""
        en2 = f"The facts: {ch} of 25 squares changed since yesterday{apres_en}. Tonight it was the largest change in the country."
        fr2 = f"Les faits : {ch} case{'s' if ch > 1 else ''} sur 25 {'ont' if ch > 1 else 'a'} changé depuis hier{apres_fr}. C'est ce soir le plus grand changement du pays."
    else:
        en1, fr1 = pick([(f"{A_en} pursues the search, square by square.", f"{Af} poursuit sa recherche, case par case."),
                         (f"A work in motion from {A_en}; the critic awaits the next phase.", f"Une œuvre en mouvement chez {A_fr} ; le critique attend la suite.")])
        en2 = f"The facts: {ch} of 25 squares changed since yesterday; {f['pleines']} are filled. The drawing only moves when the brain learns."
        fr2 = f"Les faits : {ch} cases sur 25 ont changé depuis hier ; {f['pleines']} sont pleines. Le dessin ne bouge que lorsque le cerveau apprend."
    return {"en": [en1, en2], "fr": [fr1, fr2]}


def calme(jour_ere, pleines, n, region):
    """Soir sans aucun changement : l'artiste est désigné par roulement."""
    rg_en = REGION_EN.get(region, region)
    return {"en": [f"A quiet evening in the Studio: not one drawing in the country has changed.",
                   f"The facts: no brain changed its drawing since yesterday; tonight's wall goes by rotation to Citizen No. {n} of the {rg_en} ({pleines} of 25 squares filled)."],
            "fr": [f"Soirée calme à l'atelier : aucun dessin du pays n'a bougé.",
                   f"Les faits : aucun cerveau n'a changé de dessin depuis hier ; le mur du soir revient par roulement au citoyen n° {n} ({region}), {pleines} cases pleines sur 25."]}


# ---------------------------------------------------------------- une soirée

def soiree(brut, veille_entree, archive):
    jour = dessins_du_jour(brut)
    je = int(brut.get("jourEre") or 0)
    veille = veille_entree["dessins"] if veille_entree else None
    # Pas de comparaison possible si aucun citoyen n'a un dessin hier ET ce soir (veille fermée, régions muettes)
    if veille and not any(a and b for a, b in zip(jour, veille)):
        veille = None
    pres = president(brut)
    ent = {"ere": brut.get("ere"), "date": brut.get("date"), "jourEre": je, "edition": brut.get("edition"),
           "firmware": brut.get("firmware"), "regle": REGLE, "dessins": jour, "president": pres,
           "artiste": None, "cases": None, "critique": None}
    pool = [i + 1 for i in range(120) if jour[i]]
    if not pool:
        ent["critique"] = {"en": ["The Studio is closed tonight.", "The facts: no region sent all its weights today, so there is nothing to draw. No drawing is ever made up."],
                           "fr": ["L'atelier est fermé ce soir.", "Les faits : aucune région n'a envoyé tous ses poids aujourd'hui, il n'y a donc rien à dessiner. Aucun dessin n'est jamais inventé."]}
        return ent
    ex, mx = choisir(jour, veille)
    if ex:
        n = ex[je % len(ex)]
    else:
        n = pool[je % len(pool)]
    g = jour[n - 1]
    region = REGIONS[(n - 1) // 20]
    ent["artiste"], ent["cases"] = n, (mx if ex else (0 if veille else None))
    if veille and not ex and n != pres:
        ent["critique"] = calme(je, g.count("1"), n, region)
        return ent
    # jours sans changement avant ce soir (archive de la même ère, jours consécutifs)
    stable = 0
    par_jour = {a["jourEre"]: a for a in archive if a.get("ere") == brut.get("ere")}
    d = je - 1
    while d - 1 in par_jour and d in par_jour and par_jour[d]["dessins"][n - 1] and par_jour[d]["dessins"][n - 1] == par_jour[d - 1]["dessins"][n - 1]:
        stable += 1
        d -= 1
    haut, bas = moitie_haute(g)
    faits = {"id": n, "region": region, "symetrie": symetrie(g), "cases": mx, "pleines": g.count("1"), "haut": haut, "bas": bas,
             "jumeaux": [i + 1 for i in range(120) if i != n - 1 and jour[i] == g], "stable": stable,
             "president": n == pres, "premiere": veille is None}
    ent["critique"] = critique(faits, je)
    return ent


# ---------------------------------------------------------------- lecture des données

def lire(f, defaut):
    try:
        return json.loads(Path(f).read_text(encoding="utf-8"))
    except (ValueError, OSError) as err:
        print(f"Ignoré : {f} ({err})", file=sys.stderr)
        return defaut


def charger(source, chemin):
    if source.startswith("http"):
        req = urllib.request.Request(source + chemin + "?t=" + str(int(time.time())), headers={"User-Agent": "microcontroland-atelier"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read()
    return (Path(source) / chemin).read_bytes()


def manifeste(source, ere):
    try:
        return json.loads(charger(source, f"donnees/ere-{ere:03d}/manifeste.json")).get("fichiers") or []
    except Exception as err:  # réseau, fichier absent
        print(f"Manifeste illisible : {err}", file=sys.stderr)
        return []


# ---------------------------------------------------------------- la page

def e(x):
    return html.escape(str(x), quote=True)


def date_longue(iso, lg):
    try:
        a, m, j = (int(x) for x in iso.split("-"))
    except (ValueError, AttributeError):
        return iso or ""
    return f"{j}{'er' if j == 1 and lg == 'fr' else ''} {MOIS[lg][m - 1]} {a}" if lg == "fr" else f"{j} {MOIS[lg][m - 1]} {a}"


def svg(g, cls, titre, changees=None):
    if not g:
        return f'<svg class="{cls} vide" viewBox="0 0 5 5" role="img" aria-label="{e(titre)}"><rect x="0" y="0" width="5" height="5" class="fond"/></svg>'
    cases = "".join(f'<rect x="{k % 5 + .06:.2f}" y="{k // 5 + .06:.2f}" width=".88" height=".88"/>' for k, c in enumerate(g) if c == "1")
    marques = ""
    if changees:
        marques = "".join(f'<rect class="chg" x="{k % 5 + .1:.1f}" y="{k // 5 + .1:.1f}" width=".8" height=".8"/>' for k in changees)
    return f'<svg class="{cls}" viewBox="0 0 5 5" role="img" aria-label="{e(titre)}"><rect x="0" y="0" width="5" height="5" class="fond"/>{cases}{marques}</svg>'


L = {
    "fr": {
        "titre": "L'atelier", "haut": "Galerie nationale · art primitif",
        "chapo": "Chaque soir, un dessin de 5 cases sur 5, tiré du cerveau d'un citoyen, et deux lignes du critique d'art. "
                 "Les Waïnas ne savent pas qu'ils dessinent : le dessin est la réponse de leur cerveau à une grille de nombres, "
                 "calculée à partir des poids publiés le jour même. Chacun peut le refaire et le vérifier.",
        "desc": "L'art primitif de Microcontrôland : chaque soir, un dessin 5×5 calculé à partir du cerveau d'un citoyen, avec deux lignes du critique.",
        "oeuvre": "L'œuvre du soir", "sans_titre": "Sans titre", "cit": "citoyen n° {n} ({r})", "soir": "soir du {d}, édition n° {n}",
        "pres": "président", "reserve": "La réserve", "reserve_sous": "Les {n} dessins du {d}. Le président est encadré.",
        "muette": "Région muette ce jour-là : pas de dessin.", "precedentes": "Les œuvres précédentes",
        "comment": "Comment le dessin est fait",
        "regle": "Pour chacune des 25 cases, le cerveau du citoyen (9 entrées, 6 neurones cachés, 3 sorties) reçoit neuf nombres tirés de la position de la case "
                 "(X et Y entre −1 et 1, leurs valeurs absolues, la distance au centre, X·Y, X+Y, X−Y et 1). On lit sa première sortie, sans bruit. "
                 "La case est pleine si la valeur dépasse la médiane des 25. Seule la couche de sortie apprend : le dessin change quand le cerveau apprend. "
                 "Le cerveau de citoyen d'un président ne calcule ni n'apprend pendant le mandat : son dessin reste figé.",
        "artiste": "L'artiste du soir est le citoyen dont le dessin a le plus changé depuis la veille ; à égalité, ou si rien n'a changé, un roulement selon le jour.",
        "verifier": "Vérifier : {brut} du jour, et {arch} (tous les soirs exposés).", "brut": "le fichier brut", "arch": "atelier.json",
        "attente": "L'atelier ouvre avec le premier relevé complet des poids des cerveaux (firmware 0.8, à partir du 26 octobre 2026). Les soirs précédents n'ont pas de dessin.",
        "pied": "Le critique est une rubrique satirique ; les faits qu'il cite sont mesurés. Les Waïnas ne sont ni vivants ni conscients, et ils n'ont aucune intention artistique.",
        "maj_le": "Page mise à jour automatiquement après l'édition n° {n} du {d}.",
        "menu": ["Le journal", "Archives", "Histoire", "La langue", "Mon citoyen", "L'ambassade", "Recherche", "Le projet", "Flux RSS"],
        "mast": ("Quotidien officieux de la République", "L'atelier"), "tag": "Le seul journal de Microcontrôland, écrit chaque soir par la passerelle",
        "retour": "Lire la dernière édition", "mentions": "Mentions légales", "rss": "feed.xml", "autre": ("en", "English", "feed-en.xml", "La Puce Libre (English)"),
    },
    "en": {
        "titre": "The Studio", "haut": "National Gallery · primitive art",
        "chapo": "Every evening, a drawing of 5 by 5 squares taken from a citizen's brain, and two lines from the art critic. "
                 "The Waïnas do not know they are drawing: the drawing is how their brain responds to a grid of numbers, "
                 "computed from the weights published that same day. Anyone can recompute it and check it.",
        "desc": "Microcontrôland's primitive art: every evening, a 5×5 drawing computed from a citizen's brain, with two lines from the critic.",
        "oeuvre": "Tonight's work", "sans_titre": "Untitled", "cit": "Citizen No. {n} ({r})", "soir": "evening of {d}, issue no. {n}",
        "pres": "president", "reserve": "The store room", "reserve_sous": "The {n} drawings of {d}. The President is framed.",
        "muette": "This region was silent that day: no drawing.", "precedentes": "Earlier works",
        "comment": "How the drawing is made",
        "regle": "For each of the 25 squares, the citizen's brain (9 inputs, 6 hidden neurons, 3 outputs) receives nine numbers derived from the square's position "
                 "(X and Y between −1 and 1, their absolute values, the distance to the centre, X·Y, X+Y, X−Y and 1). Its first output is read, with no noise. "
                 "The square is filled if the value is above the median of the 25. Only the output layer learns: the drawing changes when the brain learns. "
                 "A president's citizen brain neither computes nor learns during the term, so that drawing stays frozen.",
        "artiste": "Tonight's artist is the citizen whose drawing changed most since the previous day; on a tie, or if nothing changed, a rotation by day.",
        "verifier": "Check: {brut} of the day, and {arch} (every evening shown so far).", "brut": "the raw data file", "arch": "atelier.json",
        "attente": "The Studio opens with the first complete record of the brains' weights (firmware 0.8, from 26 October 2026). Earlier evenings have no drawing.",
        "pied": "The critic is a satirical column; the facts quoted are measured. The Waïnas are neither alive nor conscious, and have no artistic intent.",
        "maj_le": "Page updated automatically after issue no. {n} of {d}.",
        "menu": ["The paper", "Archive", "History", "The language", "My citizen", "The embassy", "Research", "The project", "RSS feed"],
        "mast": ("Unofficial daily of the Republic", "The Studio"), "tag": "The only newspaper in Microcontrôland, written every evening by the gateway",
        "retour": "Read the latest issue", "mentions": "Legal notice", "rss": "feed-en.xml", "autre": ("fr", "Français", "feed.xml", "La Puce Libre (français)"),
    },
}

STYLE = """<style>
.oeuvre{display:grid;grid-template-columns:minmax(0,260px) minmax(0,1fr);gap:22px;align-items:start;border:1px solid var(--rule);background:var(--sheet);padding:18px;margin:18px 0}
@media (max-width:620px){.oeuvre{grid-template-columns:1fr}}
.oeuvre svg{width:100%;max-width:260px;height:auto}
svg .fond{fill:var(--rule);opacity:.35}svg rect:not(.fond):not(.chg){fill:var(--ink)}svg .chg{fill:none;stroke:var(--warn);stroke-width:.08}
svg.vide .fond{opacity:.15}
.cartel{display:grid;gap:8px;min-width:0}.cartel .titre{font-style:italic;font-size:1.25em}
.cartel .info{font:12.5px/1.5 var(--f-data);color:var(--muted)}
.crit{border-top:1px solid var(--rule);padding-top:8px;display:grid;gap:6px}.crit p{margin:0}
.mur{display:grid;grid-template-columns:repeat(auto-fill,minmax(46px,1fr));gap:8px;margin:6px 0 16px}
.mur figure{margin:0;display:grid;gap:2px;justify-items:center}.mur svg{width:38px;height:38px}
.mur figcaption,.arch figcaption{font:11px var(--f-data);color:var(--muted);font-variant-numeric:tabular-nums;text-align:center}
.mur figure.pres svg{outline:2px solid var(--warn);outline-offset:2px}
.arch{display:flex;gap:12px;overflow-x:auto;padding:4px 0 8px}.arch figure{margin:0;display:grid;gap:2px;justify-items:center;flex:0 0 auto}.arch svg{width:44px;height:44px}
.compte{font:13px var(--f-data);color:var(--muted)}
</style>"""


def page(archive, latest, lg):
    T = L[lg]
    pre = "../" if lg == "en" else ""
    autre_lg, autre_nom, autre_rss, autre_titre = T["autre"]
    fr_url, en_url = BASE + "atelier.html", BASE + "en/atelier.html"
    liens = ["./", "archives.html", "histoire.html", "langue.html", "citoyen.html", "ambassade.html", "recherche.html", "projet.html", pre + T["rss"]]
    nav = "\n".join(f'    <a href="{h}">{e(t)}</a>' for h, t in zip(liens, T["menu"]))
    rg = (lambda r: REGION_EN.get(r, r)) if lg == "en" else (lambda r: r)
    corps = []
    expo = [a for a in archive if a.get("artiste")]
    if not archive:
        corps.append(f'<p>{e(T["attente"])}</p>')
    else:
        a = archive[-1]
        d = date_longue(a["date"], lg)
        if a.get("artiste"):
            n = a["artiste"]
            veille = next((b for b in reversed(archive[:-1]) if b.get("ere") == a.get("ere") and b["jourEre"] == a["jourEre"] - 1), None)
            chg = None
            if veille and veille["dessins"][n - 1]:
                chg = [k for k, (p, q) in enumerate(zip(a["dessins"][n - 1], veille["dessins"][n - 1])) if p != q]
            cit = T["cit"].format(n=n, r=rg(REGIONS[(n - 1) // 20]))
            corps.append(f'<h2>{e(T["oeuvre"])}</h2><div class="oeuvre">{svg(a["dessins"][n - 1], "grand", cit, chg)}'
                         f'<div class="cartel"><span class="titre">{e(T["sans_titre"])}, {e(cit)}</span>'
                         f'<span class="info">{e(T["soir"].format(d=d, n=a.get("edition")))}</span>'
                         f'<div class="crit">{"".join(f"<p>{e(x)}</p>" for x in a["critique"][lg])}</div></div></div>')
        else:
            corps.append(f'<h2>{e(T["oeuvre"])}</h2><div class="oeuvre"><div class="cartel">{"".join(f"<p>{e(x)}</p>" for x in a["critique"][lg])}</div></div>')
        nb = sum(1 for g in a["dessins"] if g)
        regs = []
        for r in range(6):
            ds = a["dessins"][r * 20:(r + 1) * 20]
            if not any(ds):
                regs.append(f'<h3>{e(rg(REGIONS[r]))}</h3><p class="compte">{e(T["muette"])}</p>')
                continue
            figs = "".join(f'<figure{" class=\"pres\"" if r * 20 + k + 1 == a.get("president") else ""}>{svg(g, "mini", T["cit"].format(n=r * 20 + k + 1, r=rg(REGIONS[r])))}'
                           f'<figcaption>{"Pr. " if r * 20 + k + 1 == a.get("president") else "n° " if lg == "fr" else "No. "}{r * 20 + k + 1}</figcaption></figure>' for k, g in enumerate(ds))
            regs.append(f'<h3>{e(rg(REGIONS[r]))}</h3><div class="mur">{figs}</div>')
        corps.append(f'<h2>{e(T["reserve"])}</h2><p class="compte">{e(T["reserve_sous"].format(n=nb, d=d))}</p>{"".join(regs)}')
        if len(expo) > 1:
            figs = "".join(f'<figure>{svg(b["dessins"][b["artiste"] - 1], "mini", T["cit"].format(n=b["artiste"], r=rg(REGIONS[(b["artiste"] - 1) // 20])))}'
                           f'<figcaption>{e(b["date"][5:])}<br>{"n° " if lg == "fr" else "No. "}{b["artiste"]}</figcaption></figure>'
                           for b in reversed(expo[-ARCHIVE_VISIBLE - 1:-1]))
            corps.append(f'<h2>{e(T["precedentes"])}</h2><div class="arch">{figs}</div>')
        brut = f'<a href="{DONNEES}donnees/ere-{int(a.get("ere") or 1):03d}/quotidien/{e(a["date"])}.json">{e(T["brut"])}</a>'
        lien_arch = f'<a href="{pre}atelier.json">{e(T["arch"])}</a>'
        corps.append(f'<h2>{e(T["comment"])}</h2><p>{e(T["regle"])}</p><p>{e(T["artiste"])}</p>'
                     f'<p>{T["verifier"].format(brut=brut, arch=lien_arch)}</p>')
    maj = T["maj_le"].format(n=latest.get("day", "?"), d=date_longue(str(latest.get("date", "")), lg))
    return f"""<!doctype html>
<html lang="{lg}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<link rel="icon" href="{pre}favicon.ico" sizes="32x32">
<link rel="icon" href="{pre}favicon.svg" type="image/svg+xml">
<title>{e(T["titre"])} — Microcontrôland</title>
<meta name="description" content="{e(T["desc"])}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="La Puce Libre — Microcontrôland">
<meta property="og:title" content="{e(T["titre"])} — Microcontrôland">
<meta property="og:description" content="{e(T["desc"])}">
<link rel="alternate" hreflang="fr" href="{fr_url}">
<link rel="alternate" hreflang="en" href="{en_url}">
<link rel="alternate" hreflang="x-default" href="{fr_url}">
<link rel="alternate" type="application/rss+xml" title="La Puce Libre" href="{pre}{T["rss"]}">
<link rel="alternate" type="application/rss+xml" title="{e(autre_titre)}" hreflang="{autre_lg}" href="{pre}{autre_rss}">
<link rel="alternate" type="application/json" href="{pre}atelier.json">
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

  <div class="prose">
    <p class="compte">{e(T["haut"])}</p>
    <h1>{e(T["titre"])}</h1>
    <p class="chapo">{e(T["chapo"])}</p>
    {"".join(corps)}
    <p><small>{e(T["pied"])}</small></p>
    <p><small>{e(maj)}</small></p>
  </div>

  <footer class="site">
    <span><a href="./">{e(T["retour"])}</a></span>
    <span><a href="{'en/' if lg == 'fr' else '../'}atelier.html">{e(autre_nom)}</a></span>
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


# ---------------------------------------------------------------- programme

def mettre_a_jour(racine, source, attendre=0):
    """Ajoute à atelier.json les soirs publiés qui n'y sont pas encore. Renvoie le nombre de soirs ajoutés."""
    chemin = racine / "atelier.json"
    arch = lire(chemin, {"format": 1, "regle": REGLE, "jours": []}) if chemin.exists() else {"format": 1, "regle": REGLE, "jours": []}
    jours = arch["jours"]
    deja = {(j.get("ere"), j.get("date")) for j in jours}
    latest = lire(racine / "data" / "latest.json", {})
    ere = int(latest.get("ere") or (jours[-1]["ere"] if jours else 1))
    fin = time.time() + attendre
    while True:
        fichiers = manifeste(source, ere)
        dates = {f.get("date") for f in fichiers}
        if not attendre or latest.get("date") in dates or time.time() > fin:
            break
        print("Fichier brut du soir pas encore publié : nouvel essai dans 60 s")
        time.sleep(60)
    ajoutes = 0
    for f in sorted(fichiers, key=lambda x: x.get("date") or ""):
        if (ere, f.get("date")) in deja:
            continue
        try:
            octets = charger(source, f["fichier"])
        except Exception as err:
            print(f"Illisible : {f.get('fichier')} ({err}) ; nouvel essai au prochain passage", file=sys.stderr)
            break   # on n'expose jamais un soir avant le précédent
        if f.get("sha256") and hashlib.sha256(octets).hexdigest() != f["sha256"]:
            print(f"Empreinte différente du manifeste : {f['fichier']} ignoré", file=sys.stderr)
            break
        brut = json.loads(octets)
        if int(brut.get("format") or 0) < 3 or "poids" not in brut:
            continue   # avant la 0.8 : aucun poids publié, aucun dessin
        veille = next((j for j in reversed(jours) if j.get("ere") == ere and j.get("jourEre") == int(brut.get("jourEre") or 0) - 1), None)
        ent = soiree(brut, veille, jours)
        ent["source"] = f["fichier"]
        jours.append(ent)
        deja.add((ere, f.get("date")))
        ajoutes += 1
    if ajoutes:
        chemin.write_text(json.dumps(arch, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    (racine / "atelier.html").write_text(page(jours, latest, "fr"), encoding="utf-8")
    (racine / "en").mkdir(exist_ok=True)
    (racine / "en" / "atelier.html").write_text(page(jours, latest, "en"), encoding="utf-8")
    print(f"atelier : {ajoutes} soir(s) ajouté(s), {len(jours)} au total")
    return ajoutes


def main():
    args = sys.argv[1:]
    racine = Path(args[0] if args and not args[0].startswith("--") else ".")
    source = args[args.index("--source") + 1] if "--source" in args else SOURCE
    attendre = int(args[args.index("--attendre") + 1]) if "--attendre" in args else 0
    if not source.startswith("http") and not source.endswith("/"):
        source += "/"
    mettre_a_jour(racine, source, attendre)


if __name__ == "__main__":
    main()
