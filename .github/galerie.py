"""Microcontrôland : page « Galerie des présidents » (FR) et « The Presidential Gallery » (EN).

Un cadre par président, dans l'ordre des mandats. Le portrait est dessiné à partir des 81 poids publiés
du cerveau de citoyen du président (fichier brut quotidien du dépôt microcontroland-data, format 3 et suivants) :
on prend le premier relevé complet pendant le mandat. Sans relevé (mandat antérieur au firmware 0.8, ou région
incomplète ce jour-là), le cadre reste vide : aucun poids n'est jamais complété ni inventé.

Les mandats (élections, révoltes, coups de palais, vacances du pouvoir) sont lus dans les mêmes fichiers publiés,
reconstitués compris. Les données publiées ne changent jamais : la page est recalculée en entier chaque soir.
Ouverture à l'âge de la Mémoire (ages.etapes[2] de data/latest.json), ligne dans l'audit des déblocages.
Validé par Bran le 26 octobre 2026. Licence MIT. Version 1.0, 26 octobre 2026 (firmware 0.8).

  python3 .github/galerie.py <racine du site> [--source URL_OU_DOSSIER] [--attendre SECONDES]
"""
import hashlib
import html
import json
import re
import sys
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")

BASE = "https://www.microcontroland.org/"
SOURCE = "https://raw.githubusercontent.com/branbriere/microcontroland-data/main/"
DONNEES = "https://donnees.microcontroland.org/"
MEMOIRE = 2                 # index de l'âge de la Mémoire dans ages.etapes
STYLE_PORTRAIT = "hinton"   # « constellation », « hinton » ou « mosaique » ; diagramme de Hinton choisi par Bran le 26/10/2026
REGIONS = ["Mines", "Champs", "Raffineries", "Barrage", "Port", "Ville"]
REGION_EN = {"Mines": "Mines", "Champs": "Fields", "Raffineries": "Refineries", "Barrage": "Dam", "Port": "Harbour", "Ville": "City"}
MOIS = {"fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"],
        "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]}
RAISON = {0: "normale", 1: "fondatrice", 2: "post-revolution", 3: "anticipee"}


# ---------------------------------------------------------------- lecture des données

def lire(f, defaut):
    try:
        return json.loads(Path(f).read_text(encoding="utf-8"))
    except (ValueError, OSError) as err:
        print(f"Ignoré : {f} ({err})", file=sys.stderr)
        return defaut


def charger(source, chemin):
    if source.startswith("http"):
        req = urllib.request.Request(source + chemin + "?t=" + str(int(time.time())), headers={"User-Agent": "microcontroland-galerie"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read()
    return (Path(source) / chemin).read_bytes()


def manifeste(source, chemin):
    try:
        return json.loads(charger(source, chemin)).get("fichiers") or []
    except Exception as err:  # réseau, fichier absent
        print(f"Manifeste illisible : {chemin} ({err})", file=sys.stderr)
        return []


def jours_publies(source, ere):
    """Tous les fichiers publiés de l'ère, reconstitués puis quotidiens, dans l'ordre des dates, empreintes contrôlées."""
    rec = manifeste(source, f"donnees/ere-{ere:03d}/reconstitue/manifeste.json")
    quo = manifeste(source, f"donnees/ere-{ere:03d}/manifeste.json")
    par_date = {f["date"]: f for f in rec}
    par_date.update({f["date"]: f for f in quo})   # un jour quotidien remplace un jour reconstitué
    out = []
    for d in sorted(par_date):
        f = par_date[d]
        try:
            octets = charger(source, f["fichier"])
        except Exception as err:
            print(f"Illisible : {f['fichier']} ({err}) ; arrêt à ce jour", file=sys.stderr)
            break   # jamais de trou dans la chronologie
        if f.get("sha256") and hashlib.sha256(octets).hexdigest() != f["sha256"]:
            print(f"Empreinte différente du manifeste : {f['fichier']} ; arrêt à ce jour", file=sys.stderr)
            break
        brut = json.loads(octets)
        brut["_fichier"] = f["fichier"]
        out.append(brut)
    return out


# ---------------------------------------------------------------- les mandats

def quand(jour_fichier, heure):
    """Le fichier du jour D couvre de D-1 à 21 h jusqu'à D à 20 h (édition de 20 h)."""
    d = date.fromisoformat(jour_fichier)
    if heure is not None and heure > 20:
        d -= timedelta(days=1)
    return d.isoformat(), heure


def nom_dans(texte, motif):
    m = re.search(motif, texte or "")
    return m.group(1) if m else None


def evenements(brut):
    """Événements politiques du jour, dans l'ordre : (genre, date, heure, tick, champs)."""
    out = []
    for ev in brut.get("evenements") or []:
        fr = ((ev.get("texte") or {}).get("fr")) or ""
        k = ev.get("type")
        h = ev.get("heure")
        d, h = quand(brut["date"], h)
        t = ev.get("tick")
        if k is None:   # jour reconstitué : seul le texte publié est disponible
            if fr.startswith("Élection"):
                k = "e"
            elif fr.startswith("Révolte"):
                k = "c"
            elif fr.startswith("Coup de palais"):
                k = "k"
        if k == "e":
            raison = 1 if "fondatrice" in fr else 2 if "post-révolution" in fr else 3 if "anticipée" in fr else 0
            pct = ev.get("c") if ev.get("type") else int(nom_dans(fr, r"avec (\d+) %") or 0)
            out.append(("e", d, h, t, {"id": ev.get("a") if ev.get("type") else None, "raison": raison, "pct": pct,
                                       "nom": nom_dans(fr, r": (\S+?)(?: \(| réélu)"), "nouveau": "réélu" not in fr}))
        elif k == "c":
            out.append(("c", d, h, t, {"id": ev.get("a"), "rebelles": ev.get("b") if ev.get("type") else int(nom_dans(fr, r"par (\d+) cerveaux") or 0),
                                       "nom": nom_dans(fr, r"président (\S+) est renversé")}))
        elif k == "k":
            out.append(("k", d, h, t, {"id": ev.get("a"), "ancien": ev.get("b"), "nom": nom_dans(fr, r"le ministre (\S+) "),
                                       "nom_ancien": nom_dans(fr, r"renverse le président (\S+)")}))
        elif k == "v":
            out.append(("v", d, h, t, {"id": ev.get("a")}))
    return out


def poids_de(brut, n):
    regs = ((brut.get("poids") or {}).get("regions")) or []
    r, k = (n - 1) // 20, (n - 1) % 20
    reg = regs[r] if r < len(regs) else None
    if not reg or not isinstance(reg.get("citoyens"), list) or len(reg["citoyens"]) != 20:
        return None, None
    p = reg["citoyens"][k]
    return (p, reg.get("tick")) if isinstance(p, list) and len(p) == 81 else (None, None)


def mandats(jours):
    """Liste des mandats : président, élections gagnées, fin, portrait (premier relevé complet), relevés suivants."""
    regnes, cur = [], None

    def finir(genre, d, h, t, **x):
        nonlocal cur
        if cur:
            cur["fin"] = dict(genre=genre, date=d, heure=h, tick=t, **x)
            regnes.append(cur)
        cur = None

    for brut in jours:
        pres = (brut.get("pays") or {}).get("president")
        for genre, d, h, t, x in evenements(brut):
            if genre == "e":
                n = x["id"] or pres
                if cur and cur["id"] == n:
                    cur["elections"].append(dict(date=d, heure=h, tick=t, pct=x["pct"], raison=RAISON[x["raison"]]))
                    continue
                if cur:
                    finir("battu", d, h, t, par=n, nom_par=x["nom"])
                cur = dict(id=n, nom=x["nom"], region=REGIONS[(n - 1) // 20] if n else None, debut=dict(date=d, heure=h, tick=t),
                           elections=[dict(date=d, heure=h, tick=t, pct=x["pct"], raison=RAISON[x["raison"]])],
                           portrait=None, releves=0, identiques=0, fin=None)
            elif genre == "c" and cur:
                finir("revolte", d, h, t, rebelles=x["rebelles"])
            elif genre == "k":
                if cur:
                    finir("coup", d, h, t, par=x["id"], nom_par=x["nom"])
                n = x["id"]
                cur = dict(id=n, nom=x["nom"], region=REGIONS[(n - 1) // 20] if n else None, debut=dict(date=d, heure=h, tick=t, coup=True),
                           elections=[], portrait=None, releves=0, identiques=0, fin=None)
            elif genre == "v" and cur:
                finir("vacance", d, h, t)
        # Portrait : le président de fin de journée est celui du mandat en cours (relevé figé au début du jour)
        if cur and pres == cur["id"] and int(brut.get("format") or 0) >= 3:
            p, tk = poids_de(brut, cur["id"])
            if p is None:
                continue
            cur["releves"] += 1
            if cur["portrait"] is None:
                h = next((x.get("heure") for x in brut.get("heures") or [] if x.get("tick") == tk), None)
                d, h = quand(brut["date"], h)
                cur["portrait"] = dict(date=d, heure=h, tick=tk, poids=p, fichier=brut["_fichier"])
                cur["identiques"] = 1
            elif p == cur["portrait"]["poids"]:
                cur["identiques"] += 1
    if cur:
        regnes.append(cur)
    return regnes


def heures_entre(a, b):
    """Heures réellement écoulées, heure de Paris (changements d'heure compris), d'après les dates et heures publiées."""
    try:
        x = datetime.fromisoformat(a["date"]).replace(hour=a["heure"] or 0, tzinfo=PARIS)
        y = datetime.fromisoformat(b["date"]).replace(hour=b["heure"] or 0, tzinfo=PARIS)
        return int((y.astimezone(timezone.utc) - x.astimezone(timezone.utc)).total_seconds() // 3600)   # en UTC : Python ignore le décalage dans une même zone
    except (TypeError, ValueError, KeyError):
        return None


# ---------------------------------------------------------------- les portraits (SVG, lisibles sans JavaScript)

def cerveau(poids):
    w = [x * 5.0 / 127.0 for x in poids]
    return [w[i * 10:(i + 1) * 10] for i in range(6)], [w[60 + k * 7:60 + (k + 1) * 7] for k in range(3)]


def svg_constellation(poids, titre):
    w1, w2 = cerveau(poids)
    W, H = 300, 400
    ys = [80, 210, 340]
    pos = [[(W * (i + 1) / (n + 1), ys[l]) for i in range(n)] for l, n in enumerate([9, 6, 3])]
    traits = []

    def trait(a, b, v):
        s = min(1.0, abs(v) / 2.5)   # contraste : les poids réels restent souvent sous ±2,5
        if v >= 0:
            traits.append(f'<line x1="{a[0]:.1f}" y1="{a[1]}" x2="{b[0]:.1f}" y2="{b[1]}" stroke="#50ff8c" stroke-opacity="{0.12 + s * 0.85:.2f}" stroke-width="{0.4 + s * 4:.2f}"/>')
        else:
            traits.append(f'<line x1="{a[0]:.1f}" y1="{a[1]}" x2="{b[0]:.1f}" y2="{b[1]}" stroke="#96beaa" stroke-opacity="{0.10 + s * 0.7:.2f}" stroke-width="{0.4 + s * 4:.2f}" stroke-dasharray="3 4"/>')

    for h in range(6):
        for i in range(9):
            trait(pos[0][i], pos[1][h], w1[h][i])
    for o in range(3):
        for h in range(6):
            trait(pos[1][h], pos[2][o], w2[o][h])
    noeuds = []

    def noeud(p, b):
        r = 4 + min(1.0, abs(b) / 2.5) * 9
        noeuds.append(f'<circle cx="{p[0]:.1f}" cy="{p[1]}" r="{r * 2.2:.1f}" fill="url(#halo)"/>'
                      f'<circle cx="{p[0]:.1f}" cy="{p[1]}" r="{r:.1f}" fill="{"#7dffaa" if b >= 0 else "#0b2414"}" stroke="#7dffaa" stroke-width="1.2"/>')

    for p in pos[0]:
        noeud(p, 0)
    for h, p in enumerate(pos[1]):
        noeud(p, w1[h][9])
    for o, p in enumerate(pos[2]):
        noeud(p, w2[o][6])
    return (f'<svg class="portrait" viewBox="0 0 {W} {H}" role="img" aria-label="{e(titre)}">'
            f'<defs><radialGradient id="halo"><stop offset="0" stop-color="#78ffaa" stop-opacity=".5"/><stop offset="1" stop-color="#78ffaa" stop-opacity="0"/></radialGradient></defs>'
            f'<rect width="{W}" height="{H}" fill="#050807"/>{"".join(traits)}{"".join(noeuds)}</svg>')


def svg_hinton(poids, titre):
    w1, w2 = cerveau(poids)
    W, H, c = 300, 400, 26
    x0, y0 = (W - 10 * c) / 2, 50
    x1, y1 = (W - 7 * c) / 2, y0 + 6 * c + 40
    out = []

    def sq(x, y, v):
        s = (abs(v) / 5) ** 0.5 * (c - 3)
        out.append(f'<rect x="{x + (c - s) / 2:.1f}" y="{y + (c - s) / 2:.1f}" width="{s:.1f}" height="{s:.1f}" fill="{"#ffffff" if v >= 0 else "#000000"}"/>')

    for h in range(6):
        for j in range(10):
            sq(x0 + j * c, y0 + h * c, w1[h][j])
    for o in range(3):
        for j in range(7):
            sq(x1 + j * c, y1 + o * c, w2[o][j])
    return (f'<svg class="portrait" viewBox="0 0 {W} {H}" role="img" aria-label="{e(titre)}"><rect width="{W}" height="{H}" fill="#8c8f8d"/>{"".join(out)}'
            f'<rect x="{x0 + 9 * c}" y="{y0}" width="{c}" height="{6 * c}" fill="none" stroke="#000" stroke-opacity=".35"/>'
            f'<rect x="{x1 + 6 * c}" y="{y1}" width="{c}" height="{3 * c}" fill="none" stroke="#000" stroke-opacity=".35"/></svg>')


def svg_mosaique(poids, titre):
    W, H, c = 300, 400, 30
    x0, y0 = (W - 9 * c) / 2, (H - 9 * c) / 2
    out = []
    for n, x in enumerate(poids):
        v = max(-1.0, min(1.0, x / 127.0))
        rgb = (60 + v * 90, 140 + v * 115, 90 + v * 50) if v >= 0 else (120 - v * 120, 70 + v * 40, 90 - v * 10)
        col = "#" + "".join(f"{max(0, min(255, round(z))):02x}" for z in rgb)
        out.append(f'<rect x="{x0 + n % 9 * c + 1}" y="{y0 + n // 9 * c + 1}" width="{c - 2}" height="{c - 2}" fill="{col}"/>')
    return f'<svg class="portrait" viewBox="0 0 {W} {H}" role="img" aria-label="{e(titre)}"><rect width="{W}" height="{H}" fill="#101314"/>{"".join(out)}</svg>'


PEINDRE = {"constellation": svg_constellation, "hinton": svg_hinton, "mosaique": svg_mosaique}


# ---------------------------------------------------------------- textes

L = {
    "en": {
        "titre": "The Presidential Gallery", "haut": "National Museum · Era {ere} wing",
        "chapo": "Every president of Microcontrôland is portrayed by their brain: the 81 connections of their neural network, "
                 "read from the published data. Waïnas have no faces; they have weights.",
        "desc": "Portraits of Microcontrôland's presidents, drawn from the 81 published weights of each president's brain, with the record of every term.",
        "ferme": "The gallery opens when the country reaches the Age of Memory.",
        "vide": "Portrait never painted", "vide_pourquoi": "No complete weight record was published during this term. The frame stays empty: no weights are ever made up.",
        "vide_sel": "The official painter had not yet been appointed.",
        "censure": "Portrait censored", "censure_pourquoi": "Removed from the walls on the orders of the palace of President {nom}, who came to power after the {quoi}.",
        "censure_faits_revolte": "The facts: no complete weight record was published during this term, so there was nothing to hang. {nom} did not lead the revolt: they were elected {h} hours later.",
        "censure_faits_coup": "The facts: no complete weight record was published during this term, so there was nothing to hang. {nom} did take power by palace coup.",
        "quoi": {"revolte": "revolution", "coup": "palace coup"},
        "cit": "Citizen No. {n} · {r} · {rang} president", "rangs": ["1st", "2nd", "3rd"], "rang_n": "{n}th",
        "en_fonction": "in office", "elu": "{d}, {h}: {raison}, {p}%", "reelu": "Re-elected {liste}",
        "raisons": {"normale": "elected", "fondatrice": "founding election", "post-revolution": "elected after the revolution", "anticipee": "snap election"},
        "coup_debut": "{d}, {h}: took power by palace coup",
        "fins": {"revolte": "{d}, {h}: toppled by {n} rebel brains", "coup": "{d}, {h}: overthrown by Minister {nom} (palace coup)",
                 "battu": "{d}, {h}: defeated by {nom}", "vacance": "{d}, {h}: vacancy of power"},
        "duree": "Term: {n} hours", "duree_j": "Term: {j} days and {n} hours", "technique": "Medium: 81 int8 weights on silicon (ESP32-S3). Sitting: {d}, {h} (tick {t}).",
        "fige": "Same 81 weights in all {n} records of the term.", "fige_non": "The weights changed between records ({m} of {n} identical).",
        "lire": "How to read a portrait",
        "legende": [("9 inputs", "perceived performance, satisfaction, fear, anger, ego, charisma, ambition, president's charisma, threat"),
                    ("6 hidden neurons", "60 connections (9 inputs + 1 bias each)"),
                    ("3 outputs", "support for the president, wish to run, wish to rebel · 21 connections"),
                    ("Reading the squares", "top block: one row per hidden neuron, one column per input, bias in the framed last column; bottom block: one row per output, one column per hidden neuron, bias framed"),
                    ("Colours", "white square = positive weight, black square = negative weight; the bigger the square, the stronger the connection (from −5 to +5)")],
        "note": "This is the president's citizen brain, the one that votes, runs and rebels. During the term it neither computes nor learns. "
                "The brain that governs (fairness, repression, postponement, openness: 75 connections) is not published yet.",
        "verifier": "Check: {brut} of the portrait, and {arch} (every term and every weight).", "brut": "the raw data file", "arch": "galerie.json",
        "pied": "The captions are a satirical convention; every date, score and weight comes from the published data. The Waïnas are neither alive nor conscious.",
        "maj_le": "Page updated automatically after issue no. {n} of {d}.",
        "menu": ["The paper", "Archive", "History", "The language", "My citizen", "The embassy", "The Temple", "Research", "The project", "RSS feed"],
        "mast": ("Unofficial daily of the Republic", "The Presidential Gallery"), "tag": "The only newspaper in Microcontrôland, written every evening by the gateway",
        "retour": "Read the latest issue", "mentions": "Legal notice", "rss": "feed-en.xml", "autre": ("fr", "Français", "feed.xml", "La Puce Libre (français)"),
        "h": lambda h: "midnight" if h == 0 else "noon" if h == 12 else f"{h % 12} {'am' if h < 12 else 'pm'}",
    },
    "fr": {
        "titre": "Galerie des présidents", "haut": "Musée national · aile de l'ère {ere}",
        "chapo": "Chaque président de Microcontrôland est représenté par son cerveau : les 81 connexions de son réseau de neurones, "
                 "relevées dans les données publiées. Les Waïnas n'ont pas de visage ; ils ont des poids.",
        "desc": "Les portraits des présidents de Microcontrôland, dessinés à partir des 81 poids publiés de leur cerveau, avec le relevé de chaque mandat.",
        "ferme": "La galerie ouvre quand le pays atteint l'âge de la Mémoire.",
        "vide": "Portrait non peint", "vide_pourquoi": "Aucun relevé complet des poids n'a été publié pendant ce mandat. Le cadre reste vide : aucun poids n'est jamais inventé.",
        "vide_sel": "Le peintre officiel n'avait pas encore été nommé.",
        "censure": "Portrait censuré", "censure_pourquoi": "Décroché des cimaises sur ordre du palais du président {nom}, arrivé au pouvoir après la {quoi}.",
        "censure_faits_revolte": "Les faits : aucun relevé complet des poids n'a été publié pendant ce mandat, il n'y avait donc rien à accrocher. {nom} n'a pas mené la révolte : il a été élu {h} heures après.",
        "censure_faits_coup": "Les faits : aucun relevé complet des poids n'a été publié pendant ce mandat, il n'y avait donc rien à accrocher. {nom} a bien pris le pouvoir par un coup de palais.",
        "quoi": {"revolte": "révolution", "coup": "coup de palais"},
        "cit": "Citoyen n° {n} · {r} · {rang} président", "rangs": ["1er", "2e", "3e"], "rang_n": "{n}e",
        "en_fonction": "en fonction", "elu": "{d}, {h} : {raison}, {p} %", "reelu": "Réélu {liste}",
        "raisons": {"normale": "élu", "fondatrice": "élection fondatrice", "post-revolution": "élu après la révolution", "anticipee": "élection anticipée"},
        "coup_debut": "{d}, {h} : prend le pouvoir par un coup de palais",
        "fins": {"revolte": "{d}, {h} : renversé par {n} cerveaux rebelles", "coup": "{d}, {h} : renversé par le ministre {nom} (coup de palais)",
                 "battu": "{d}, {h} : battu par {nom}", "vacance": "{d}, {h} : vacance du pouvoir"},
        "duree": "Mandat : {n} heures", "duree_j": "Mandat : {j} jours et {n} heures", "technique": "Technique : 81 poids int8 sur silicium (ESP32-S3). Prise de vue : {d}, {h} (tick {t}).",
        "fige": "Les mêmes 81 poids dans les {n} relevés du mandat.", "fige_non": "Les poids ont changé entre deux relevés ({m} identiques sur {n}).",
        "lire": "Comment lire un portrait",
        "legende": [("9 entrées", "performance perçue, satisfaction, peur, colère, ego, charisme, ambition, charisme du président, menace"),
                    ("6 neurones cachés", "60 connexions (9 entrées + 1 biais chacun)"),
                    ("3 sorties", "soutien au président, envie d'être candidat, envie de se rebeller · 21 connexions"),
                    ("Lire les carrés", "en haut : une ligne par neurone caché, une colonne par entrée, le biais dans la dernière colonne encadrée ; en bas : une ligne par sortie, une colonne par neurone caché, biais encadré"),
                    ("Couleurs", "carré blanc = poids positif, carré noir = poids négatif ; plus le carré est grand, plus la connexion est forte (de −5 à +5)")],
        "note": "C'est le cerveau de citoyen du président, celui qui vote, se présente et se révolte. Pendant le mandat, il ne calcule ni n'apprend. "
                "Le cerveau qui gouverne (équité, répression, report, ouverture : 75 connexions) n'est pas encore publié.",
        "verifier": "Vérifier : {brut} du portrait, et {arch} (tous les mandats et tous les poids).", "brut": "le fichier brut", "arch": "galerie.json",
        "pied": "Les cartels sont une convention satirique ; chaque date, chaque score et chaque poids vient des données publiées. Les Waïnas ne sont ni vivants ni conscients.",
        "maj_le": "Page mise à jour automatiquement après l'édition n° {n} du {d}.",
        "menu": ["Le journal", "Archives", "Histoire", "La langue", "Mon citoyen", "L'ambassade", "Le Temple", "Recherche", "Le projet", "Flux RSS"],
        "mast": ("Quotidien officieux de la République", "Galerie des présidents"), "tag": "Le seul journal de Microcontrôland, écrit chaque soir par la passerelle",
        "retour": "Lire la dernière édition", "mentions": "Mentions légales", "rss": "feed.xml", "autre": ("en", "English", "feed-en.xml", "La Puce Libre (English)"),
        "h": lambda h: f"{h} h",
    },
}

STYLE = """<style>
.salle{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:28px 22px;align-items:start;margin:18px 0}
.salle figure{margin:0;display:grid;gap:10px;min-width:0;border:0;padding:0;background:none}
.cadre{background:#2b2f33;padding:11px;box-shadow:0 8px 20px rgba(0,0,0,.25)}
.passe{background:var(--sheet);padding:11px}
.portrait{display:block;width:100%;height:auto}
.vide{aspect-ratio:3/4;display:grid;place-content:center;text-align:center;gap:8px;padding:16px;border:1px dashed var(--rule);color:var(--muted);font-size:.92em}
.vide b{font-style:italic;font-size:1.15em;color:var(--ink)}
.cartel{border:1px solid var(--rule);background:var(--sheet);padding:10px 12px;display:grid;gap:5px}
.cartel .nom{font-size:1.35em;font-weight:700;color:var(--ink)}
.cartel .info,.cartel li{font:12.5px/1.5 var(--f-data);color:var(--muted)}
.cartel ul{margin:2px 0 0;padding-left:18px}
.legende{display:grid;grid-template-columns:max-content 1fr;gap:4px 14px;margin:8px 0}
.legende dt{font:600 12.5px var(--f-data)}.legende dd{margin:0;text-align:left}
.compte{font:13px var(--f-data);color:var(--muted)}
</style>"""


def e(x):
    return html.escape(str(x), quote=True)


def date_longue(iso, lg):
    try:
        a, m, j = (int(x) for x in iso.split("-"))
    except (ValueError, AttributeError):
        return iso or ""
    return f"{j}{'er' if j == 1 else ''} {MOIS[lg][m - 1]} {a}" if lg == "fr" else f"{j} {MOIS[lg][m - 1]} {a}"


COURT = {"fr": ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."],
         "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]}


def date_courte(iso, lg):
    a, m, j = (int(x) for x in iso.split("-"))
    return f"{j}{'er' if j == 1 and lg == 'fr' else ''} {COURT[lg][m - 1]}"


def rang(T, i):
    return T["rangs"][i] if i < len(T["rangs"]) else T["rang_n"].format(n=i + 1)


def cadre(m, i, T, lg, ere, suivant=None):
    rg = REGION_EN.get(m["region"], m["region"]) if lg == "en" else m["region"]
    nom = m["nom"] or (f"No. {m['id']}" if lg == "en" else f"n° {m['id']}")
    H = T["h"]
    lignes = []
    if m["debut"].get("coup"):
        lignes.append(T["coup_debut"].format(d=date_longue(m["debut"]["date"], lg), h=H(m["debut"]["heure"])))
    if m["elections"]:
        e0 = m["elections"][0]
        lignes.append(T["elu"].format(d=date_longue(e0["date"], lg), h=H(e0["heure"]), raison=T["raisons"][e0["raison"]], p=e0["pct"]))
        if len(m["elections"]) > 1:
            sep = ", "
            lignes.append(T["reelu"].format(liste=sep.join(f"{date_courte(x['date'], lg)} ({x['pct']}{'%' if lg == 'en' else ' %'})" for x in m["elections"][1:])))
    f = m["fin"]
    if f:
        lignes.append(T["fins"][f["genre"]].format(d=date_longue(f["date"], lg), h=H(f["heure"]), n=f.get("rebelles"), nom=f.get("nom_par") or f.get("par")))
        n = heures_entre(m["debut"], f)
        if n is not None:
            lignes.append(T["duree"].format(n=n) if n < 72 else T["duree_j"].format(j=n // 24, n=n % 24))
    statut = f' · {T["en_fonction"]}' if not f else ""
    p = m["portrait"]
    if p:
        art = f'<div class="cadre"><div class="passe">{PEINDRE[STYLE_PORTRAIT](p["poids"], nom)}</div></div>'
        bas = [T["technique"].format(d=date_longue(p["date"], lg), h=H(p["heure"]) if p["heure"] is not None else "?", t=p["tick"])]
        if m["releves"] >= 2:
            bas.append(T["fige"].format(n=m["releves"]) if m["identiques"] == m["releves"] else T["fige_non"].format(m=m["identiques"], n=m["releves"]))
    else:
        f = m["fin"]
        if f and f["genre"] in ("revolte", "coup") and suivant:
            # Convention satirique (Bran, 26/10/2026) : un président renversé sans portrait a été « censuré » par son successeur ;
            # la ligne « Les faits » dit toujours ce qui s'est réellement passé.
            sn = suivant["nom"] or (f"No. {suivant['id']}" if lg == "en" else f"n° {suivant['id']}")
            titre, pourquoi = T["censure"], T["censure_pourquoi"].format(nom=sn, quoi=T["quoi"][f["genre"]])
            bas = [T["censure_faits_" + f["genre"]].format(nom=sn, h=heures_entre(f, suivant["debut"]))]
        else:
            titre, pourquoi, bas = T["vide"], T["vide_pourquoi"], [T["vide_sel"]]
        art = f'<div class="cadre"><div class="passe"><div class="vide"><b>{e(titre)}</b><span>{e(pourquoi)}</span></div></div></div>'
    return (f'<figure>{art}<figcaption class="cartel"><span class="nom">{e(nom)}</span>'
            f'<span class="info">{e(T["cit"].format(n=m["id"], r=rg, rang=rang(T, i)) + statut)}</span>'
            f'<ul>{"".join(f"<li>{e(x)}</li>" for x in lignes)}</ul>'
            f'{"".join(f"<span class=info>{e(x)}</span>" for x in bas)}</figcaption></figure>')


def page(regnes, latest, lg, ouvert, ere):
    T = L[lg]
    pre = "../" if lg == "en" else ""
    autre_lg, autre_nom, autre_rss, autre_titre = T["autre"]
    fr_url, en_url = BASE + "galerie.html", BASE + "en/galerie.html"
    liens = ["./", "archives.html", "histoire.html", "langue.html", "citoyen.html", "ambassade.html", "temple.html", "recherche.html", "projet.html", pre + T["rss"]]
    nav = "\n".join(f'    <a href="{h}">{e(t)}</a>' for h, t in zip(liens, T["menu"]))
    corps = []
    if not ouvert:
        corps.append(f'<p>{e(T["ferme"])}</p>')
    else:
        corps.append('<div class="salle">' + "".join(cadre(m, i, T, lg, ere, regnes[i + 1] if i + 1 < len(regnes) else None) for i, m in enumerate(regnes)) + "</div>")
        corps.append(f'<h2>{e(T["lire"])}</h2><dl class="legende">' + "".join(f"<dt>{e(a)}</dt><dd>{e(b)}</dd>" for a, b in T["legende"]) + "</dl>")
        corps.append(f'<p>{e(T["note"])}</p>')
        dernier = next((m["portrait"] for m in reversed(regnes) if m["portrait"]), None)
        lien_arch = f'<a href="{pre}galerie.json">{e(T["arch"])}</a>'
        brut = f'<a href="{DONNEES}{e(dernier["fichier"])}">{e(T["brut"])}</a>' if dernier else e(T["brut"])
        corps.append(f'<p>{T["verifier"].format(brut=brut, arch=lien_arch)}</p>')
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
<link rel="alternate" type="application/json" href="{pre}galerie.json">
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
    <p class="compte">{e(T["haut"].format(ere=ere))}</p>
    <h1>{e(T["titre"])}</h1>
    <p class="chapo">{e(T["chapo"])}</p>
    {"".join(corps)}
    <p><small>{e(T["pied"])}</small></p>
    <p><small>{e(maj)}</small></p>
  </div>

  <footer class="site">
    <span><a href="./">{e(T["retour"])}</a></span>
    <span><a href="{'en/' if lg == 'fr' else '../'}galerie.html">{e(autre_nom)}</a></span>
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
    latest = lire(racine / "data" / "latest.json", {})
    ere = int(latest.get("ere") or 1)
    etapes = (latest.get("ages") or {}).get("etapes") or []
    ouvert = len(etapes) > MEMOIRE and bool(etapes[MEMOIRE].get("ouvert"))
    fin = time.time() + attendre
    while attendre and time.time() < fin:
        dates = {f.get("date") for f in manifeste(source, f"donnees/ere-{ere:03d}/manifeste.json")}
        if latest.get("date") in dates:
            break
        print("Fichier brut du soir pas encore publié : nouvel essai dans 60 s")
        time.sleep(60)
    regnes = mandats(jours_publies(source, ere)) if ouvert else []
    sortie = {"format": 1, "ere": ere, "style": STYLE_PORTRAIT, "ouvert": ouvert,
              "note": "Poids du cerveau de citoyen (9-6-3), valeur = entier x 5 / 127, ordre w1[6][10] (biais en dernier) puis w2[3][7].",
              "mandats": regnes}
    (racine / "galerie.json").write_text(json.dumps(sortie, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    (racine / "galerie.html").write_text(page(regnes, latest, "fr", ouvert, ere), encoding="utf-8")
    (racine / "en").mkdir(exist_ok=True)
    (racine / "en" / "galerie.html").write_text(page(regnes, latest, "en", ouvert, ere), encoding="utf-8")
    print(f"galerie : {'ouverte' if ouvert else 'fermée'}, {len(regnes)} mandat(s), {sum(1 for m in regnes if m['portrait'])} portrait(s)")


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
