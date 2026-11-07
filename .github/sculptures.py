"""Microcontrôland : les sculptures (art secondaire, cubes 8 × 8 × 8), exposées au Musée national.

Chaque soir, après l'édition, ce script lit le fichier brut public du soir (dépôt microcontroland-data : les 81 poids de
chacun des 120 cerveaux), calcule une sculpture par citoyen avec la règle S1, désigne le sculpteur du soir et écrit :
  · sculptures.json      archive, un soir par entrée, jamais réécrite (comme atelier.json) ;
  · sculptures-soir.json les 120 sculptures du dernier soir (remplacé chaque soir, c'est l'état du jour, pas l'archive).
Le musée (musee.py) lit ces deux fichiers. La passerelle ne change pas.

Règle S1 v1 (validée par Bran le 26/10/2026 dans son principe, formule simulée le 5/11/2026) :
  · grille 8 × 8 × 8, case (X, Y, Z) dans [−1, 1]³ ;
  · entrées du cerveau : X, Y, Z, |X|, |Y|, |Z|, distance / √3, X·Y·Z, 1 ; sortie n° 1 (soutien), sans bruit ni hasard ;
  · un cube est posé dans chaque case dont la sortie dépasse celle de la 385e case par ordre croissant
    (le quart supérieur : 127 cubes sur 512) ; taille 1 à 9 selon la valeur, entre ce seuil et le maximum ;
  · une seule couleur (la couleur est réservée à l'art évolué de la Curiosité).
Codage : 512 chiffres, case n° (i·64 + j·8 + k) pour X = i, Y = j, Z = k ; « 0 » = pas de cube, « 1 » à « 9 » = taille.

Âge : la Mémoire (ages.etapes[2] de data/latest.json). Les sculptures commencent le soir de la livraison, sans
recalcul des soirs passés (décision de Bran du 5/11/2026). Aucune sculpture n'est inventée : une région qui n'a pas
envoyé ses 20 × 81 poids ce soir-là n'a pas de sculpture (null).
Licence MIT. Version 1.0, novembre 2026 (firmware 0.9, site seulement).

  python3 .github/sculptures.py <racine du site> [--source <dépôt de données ou URL>] [--attendre <secondes>]
"""
import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

REGLE = "S1 v1"
N = 8
MEMOIRE = 2
SEUIL = 384               # index (ordre croissant) de la case-seuil : 512 − 384 − 1 = 127 cubes au-dessus
SOURCE = "https://raw.githubusercontent.com/branbriere/microcontroland-data/main/"


def module(racine, nom):
    spec = importlib.util.spec_from_file_location(nom, racine / ".github" / f"{nom}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


A = None   # module atelier.py : mêmes cerveaux, même lecture des données que L'atelier (chargé dans main)


# ---------------------------------------------------------------- la sculpture (règle S1)

COORD = [(i - (N - 1) / 2) / ((N - 1) / 2) for i in range(N)]


def entrees(X, Y, Z):
    return [X, Y, Z, abs(X), abs(Y), abs(Z), math.sqrt(X * X + Y * Y + Z * Z) / math.sqrt(3), X * Y * Z, 1.0]


def valeurs(poids):
    c = A.cerveau(poids)
    return [A.soutien(c, entrees(X, Y, Z)) for X in COORD for Y in COORD for Z in COORD]


def sculpture(poids):
    """Chaîne de 512 chiffres (0 = vide, 1 à 9 = taille du cube) et écart au seuil le plus petit (contrôle)."""
    v = valeurs(poids)
    s = sorted(v)
    t, mx = s[SEUIL], s[-1]
    out = []
    for x in v:
        if x > t:
            out.append(str(1 + min(8, int(9 * (x - t) / (mx - t)))) if mx > t else "1")
        else:
            out.append("0")
    marge = min(s[SEUIL + 1] - t, t - s[SEUIL - 1])
    return "".join(out), marge


def sculptures_du_jour(brut):
    out, marges = [None] * 120, []
    regs = ((brut.get("poids") or {}).get("regions")) or []
    for r in range(6):
        reg = regs[r] if r < len(regs) else None
        if not reg or not isinstance(reg.get("citoyens"), list) or len(reg["citoyens"]) != 20:
            continue
        for k, p in enumerate(reg["citoyens"]):
            if isinstance(p, list) and len(p) == 81:
                out[r * 20 + k], m = sculpture(p)
                marges.append(m)
    return out, (min(marges) if marges else None)


def cubes(s):
    return {i for i, c in enumerate(s) if c != "0"}


def deplaces(a, b):
    """Cubes qui ne sont plus à la même place qu'hier (le nombre de cubes reste 127)."""
    return len(cubes(a) - cubes(b))


def symetrie(s):
    """Cubes dont le reflet gauche-droite (X → −X) porte aussi un cube."""
    c = cubes(s)
    return sum(1 for i in c if ((N - 1 - i // 64) * 64 + i % 64) in c)


def hauteur(s):
    """Part des cubes dans la moitié haute (Z ≥ 4), en %."""
    c = cubes(s)
    return round(100 * sum(1 for i in c if i % 8 >= 4) / len(c)) if c else 0


# ---------------------------------------------------------------- le critique (deux lignes, anglais d'abord)

def critique(f, jour_ere):
    """La première ligne est l'avis du critique ; la seconde donne toujours les faits. Aucune intention prêtée."""
    n, rg_fr = f["id"], f["region"]
    rg_en = A.REGION_EN.get(rg_fr, rg_fr)
    A_en, A_fr = f"Citizen No. {n} of the {rg_en}", f"le citoyen n° {n} ({rg_fr})"
    Af = A_fr[0].upper() + A_fr[1:]

    def pick(lst):
        return lst[jour_ere % len(lst)]

    d, h = f["deplaces"], f["haut"]
    if f["president"]:
        en1, fr1 = pick([("The President's sculpture takes the central plinth, as protocol requires.",
                          "La sculpture du président occupe le socle central, comme le veut le protocole."),
                         ("From the palace, a block of rare constancy.", "Du palais, un bloc d'une rare constance.")])
        en2 = f"The facts: {A_en} holds the presidency; a president's citizen brain does not learn during the term, so the sculpture cannot change before it ends."
        fr2 = f"Les faits : {A_fr} est président ; pendant le mandat, son cerveau de citoyen n'apprend pas, et la sculpture ne peut pas changer avant la fin du mandat."
    elif f["premiere"]:
        en1, fr1 = pick([(f"The Sculpture Hall opens: {A_en} takes the first plinth.", f"La salle des sculptures ouvre : {A_fr} prend le premier socle."),
                         (f"Opening night in three dimensions, led by {A_en}.", f"Vernissage en trois dimensions, ouvert par {A_fr}.")])
        en2 = f"The facts: 127 cubes out of 512, {h}% of them in the upper half; no sculpture from the previous day to compare with, so tonight's sculptor was chosen by rotation."
        fr2 = f"Les faits : 127 cubes sur 512, dont {h} % dans la moitié haute ; aucune sculpture de la veille pour comparer, le sculpteur du soir est donc désigné par roulement."
    elif d >= 20:
        en1, fr1 = pick([(f"{A_en} knocks the block down and starts again.", f"{Af} abat le bloc et recommence."),
                         (f"A landslide in the work of {A_en}; the critic steps back.", f"Éboulement dans l'œuvre de {A_fr} ; le critique recule d'un pas.")])
        en2 = f"The facts: {d} of the 127 cubes moved overnight, as the brain went on learning. Nobody carved anything: the sculpture is computed from the weights."
        fr2 = f"Les faits : {d} des 127 cubes ont changé de place en une nuit, au fil de ce que le cerveau a appris. Personne n'a rien taillé : la sculpture est calculée à partir des poids."
    elif d <= 3:
        en1, fr1 = pick([(f"{A_en} polishes rather than carves.", f"{Af} polit plutôt qu'il ne taille."),
                         (f"A touch of the chisel from {A_en}, for connoisseurs only.", f"Un coup de ciseau chez {A_fr}, réservé aux connaisseurs.")])
        en2 = f"The facts: {d} cube{'s' if d > 1 else ''} out of 127 moved since yesterday; tonight it was the largest change in the country."
        fr2 = f"Les faits : {d} cube{'s' if d > 1 else ''} sur 127 {'ont' if d > 1 else 'a'} changé de place depuis hier ; c'est ce soir le plus grand changement du pays."
    else:
        en1, fr1 = pick([(f"{A_en} works the block, cube by cube.", f"{Af} travaille le bloc, cube par cube."),
                         (f"A sculpture on the move from {A_en}; the critic will come back tomorrow.", f"Une sculpture en mouvement chez {A_fr} ; le critique repassera demain.")])
        en2 = f"The facts: {d} of the 127 cubes moved since yesterday; {h}% of them now sit in the upper half. The sculpture only changes when the brain learns."
        fr2 = f"Les faits : {d} des 127 cubes ont changé de place depuis hier ; {h} % sont maintenant dans la moitié haute. La sculpture ne change que lorsque le cerveau apprend."
    return {"en": [en1, en2], "fr": [fr1, fr2]}


def calme(n, region):
    rg_en = A.REGION_EN.get(region, region)
    return {"en": ["A quiet evening in the Sculpture Hall: not one cube in the country has moved.",
                   f"The facts: no brain changed its sculpture since yesterday; the central plinth goes by rotation to Citizen No. {n} of the {rg_en}."],
            "fr": ["Soirée calme à la salle des sculptures : aucun cube du pays n'a bougé.",
                   f"Les faits : aucun cerveau n'a changé de sculpture depuis hier ; le socle central revient par roulement au citoyen n° {n} ({region})."]}


# ---------------------------------------------------------------- une soirée

def soiree(brut, veille_brut):
    jour, marge = sculptures_du_jour(brut)
    veille = sculptures_du_jour(veille_brut)[0] if veille_brut else None
    if veille and not any(a and b for a, b in zip(jour, veille)):
        veille = None
    je = int(brut.get("jourEre") or 0)
    pres = A.president(brut)
    ent = {"ere": brut.get("ere"), "date": brut.get("date"), "jourEre": je, "edition": brut.get("edition"),
           "firmware": brut.get("firmware"), "regle": REGLE, "president": pres, "sculpteur": None, "deplaces": None,
           "sculpture": None, "critique": None, "marge": marge}
    pool = [i + 1 for i in range(120) if jour[i]]
    if not pool:
        ent["critique"] = {"en": ["The Sculpture Hall is closed tonight.", "The facts: no region sent all its weights today, so there is nothing to sculpt. No sculpture is ever made up."],
                           "fr": ["La salle des sculptures est fermée ce soir.", "Les faits : aucune région n'a envoyé tous ses poids aujourd'hui, il n'y a donc rien à sculpter. Aucune sculpture n'est jamais inventée."]}
        return ent, jour
    ex, mx = [], 0
    if veille:
        ch = {i + 1: deplaces(jour[i], veille[i]) for i in range(120) if jour[i] and veille[i]}
        mx = max(ch.values(), default=0)
        ex = sorted(i for i, v in ch.items() if v == mx) if mx > 0 else []
    n = ex[je % len(ex)] if ex else pool[je % len(pool)]
    s = jour[n - 1]
    region = A.REGIONS[(n - 1) // 20]
    ent.update({"sculpteur": n, "deplaces": mx if ex else (0 if veille else None), "sculpture": s})
    if veille and not ex and n != pres:
        ent["critique"] = calme(n, region)
        return ent, jour
    f = {"id": n, "region": region, "deplaces": mx, "haut": hauteur(s), "president": n == pres, "premiere": veille is None}
    ent["critique"] = critique(f, je)
    return ent, jour


# ---------------------------------------------------------------- programme

def ouverte(latest):
    etapes = (latest.get("ages") or {}).get("etapes") or []
    return len(etapes) > MEMOIRE and bool(etapes[MEMOIRE].get("ouvert"))


def lire_brut(source, f):
    octets = A.charger(source, f["fichier"])
    if f.get("sha256") and hashlib.sha256(octets).hexdigest() != f["sha256"]:
        raise ValueError(f"empreinte différente du manifeste : {f['fichier']}")
    return json.loads(octets)


def mettre_a_jour(racine, source, attendre=0):
    chemin, soir = racine / "sculptures.json", racine / "sculptures-soir.json"
    arch = A.lire(chemin, None) if chemin.exists() else None
    arch = arch or {"format": 1, "regle": REGLE, "jours": []}
    jours = arch["jours"]
    latest = A.lire(racine / "data" / "latest.json", {})
    if not ouverte(latest):
        print("sculptures : l'âge de la Mémoire n'est pas atteint, rien n'est calculé (audit des déblocages)")
        return 0
    ere = int(latest.get("ere") or 1)
    fin = time.time() + attendre
    while True:
        fichiers = [f for f in A.manifeste(source, ere) if f.get("fichier")]
        if not attendre or latest.get("date") in {f.get("date") for f in fichiers} or time.time() > fin:
            break
        print("Fichier brut du soir pas encore publié : nouvel essai dans 60 s")
        time.sleep(60)
    fichiers.sort(key=lambda x: x.get("date") or "")
    deja = {(j.get("ere"), j.get("date")) for j in jours}
    derniere = max((j["date"] for j in jours if j.get("ere") == ere), default=None)
    if derniere is None:
        # Premier soir de l'ère (ou livraison) : seulement le dernier brut publié, jamais les soirs passés.
        fichiers = fichiers[-1:]
    else:
        fichiers = [f for f in fichiers if f.get("date", "") > derniere]
    ajoutes, dernier_jour = 0, None
    for f in fichiers:
        if (ere, f.get("date")) in deja:
            continue
        try:
            brut = lire_brut(source, f)
        except Exception as err:
            print(f"Illisible : {f.get('fichier')} ({err}) ; nouvel essai au prochain passage", file=sys.stderr)
            break    # on n'expose jamais un soir avant le précédent
        if int(brut.get("format") or 0) < 3 or "poids" not in brut:
            continue
        je = int(brut.get("jourEre") or 0)
        veille_f = max((g for g in A.manifeste(source, ere) if g.get("date") and g["date"] < f["date"]), key=lambda g: g["date"], default=None)
        veille_brut = None
        if veille_f:
            try:
                vb = lire_brut(source, veille_f)
                if int(vb.get("jourEre") or 0) == je - 1 and int(vb.get("format") or 0) >= 3:
                    veille_brut = vb
            except Exception as err:
                print(f"Veille illisible ({err}) : soir sans comparaison", file=sys.stderr)
        ent, dernier_jour = soiree(brut, veille_brut)
        ent["source"] = f["fichier"]
        jours.append(ent)
        deja.add((ere, f.get("date")))
        ajoutes += 1
    if ajoutes:
        chemin.write_text(json.dumps(arch, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        d = jours[-1]
        soir.write_text(json.dumps({"format": 1, "regle": REGLE, "ere": d["ere"], "date": d["date"], "jourEre": d["jourEre"],
                                    "edition": d["edition"], "source": d["source"], "sculpteur": d["sculpteur"],
                                    "president": d["president"], "sculptures": dernier_jour},
                                   ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"sculptures : {ajoutes} soir(s) ajouté(s), {len(jours)} au total")
    return ajoutes


def main():
    global A
    args = sys.argv[1:]
    racine = Path(args[0] if args and not args[0].startswith("--") else ".")
    source = args[args.index("--source") + 1] if "--source" in args else SOURCE
    attendre = int(args[args.index("--attendre") + 1]) if "--attendre" in args else 0
    if not source.startswith("http") and not source.endswith("/"):
        source += "/"
    A = module(racine, "atelier")
    mettre_a_jour(racine, source, attendre)


if __name__ == "__main__":
    main()
