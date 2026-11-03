"""Microcontrôland : historique de chaque citoyen, pour la page « Mon citoyen ».

Relit tous les fichiers bruts publiés de l'ère (dépôt microcontroland-data, reconstitués puis quotidiens) et en tire,
pour chacun des 120 citoyens, les faits datés : élections, défaites, révolutions, coups de palais, entrées et sorties
du gouvernement, candidatures, et les périodes de révolte et de censure. Le fichier data/historique.json ne contient
que des codes : la page les met en phrases, en français et en anglais.

Ce qui est relevé, et depuis quand :
- les faits politiques, depuis le premier jour de l'ère (dans les jours reconstitués, lus dans le texte publié) ;
- les candidatures et les périodes de révolte et de censure, depuis le premier fichier quotidien (15 octobre 2026),
  car les jours reconstitués ne publient pas l'état des citoyens.
Rien n'est jamais déduit au-delà des données publiées. Les biographies tenues par la passerelle (firmware 0.9)
prennent le relais à partir de leur date de début ; la page n'affiche l'historique qu'avant cette date.
Demandé par Bran le 28 octobre 2026 (« pour avoir un historique du citoyen »). Licence MIT. Version 1.0.

  python3 .github/historique.py <racine du site> [--source URL_OU_DOSSIER] [--attendre SECONDES]
"""
import hashlib
import json
import re
import sys
import time
import urllib.request
from datetime import date, timedelta
from pathlib import Path

SOURCE = "https://raw.githubusercontent.com/branbriere/microcontroland-data/main/"
RAISON = {0: "normale", 1: "fondatrice", 2: "post-revolution", 3: "anticipee"}
RAISON_TXT = {"Élection fondatrice": 1, "Élection post-révolution": 2, "Élection anticipée": 3, "Élection": 0}


# ---------------------------------------------------------------- lecture des données publiées

def lire(f, defaut):
    try:
        return json.loads(Path(f).read_text(encoding="utf-8"))
    except (ValueError, OSError) as err:
        print(f"Ignoré : {f} ({err})", file=sys.stderr)
        return defaut


def charger(source, chemin):
    if source.startswith("http"):
        req = urllib.request.Request(source + chemin + "?t=" + str(int(time.time())), headers={"User-Agent": "microcontroland-historique"})
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
        out.append(json.loads(octets))
    return out


def quand(jour_fichier, heure):
    """Le fichier du jour D couvre de D-1 à 21 h jusqu'à D à 20 h (édition de 20 h)."""
    d = date.fromisoformat(jour_fichier)
    if heure is not None and heure > 20:
        d -= timedelta(days=1)
    return d.isoformat()


# ---------------------------------------------------------------- les faits

def faits_du_texte(fr, ids):
    """Jours reconstitués : seul le texte publié est disponible. Renvoie (type, champs) comme un événement quotidien."""
    m = re.match(r"(Élection(?: fondatrice| post-révolution| anticipée)?) : (\S+) \(\S+\) élu avec (\d+) %(?:, (\S+) battu)?", fr)
    if m:
        return "e", dict(sous=1 | (RAISON_TXT[m.group(1)] << 1), a=ids.get(m.group(2)), c=int(m.group(3)), d=ids.get(m.group(4)) if m.group(4) else 0)
    m = re.match(r"Élection(?: fondatrice| post-révolution| anticipée)? : (\S+) réélu avec (\d+) %", fr)
    if m:
        return "e", dict(sous=0, a=ids.get(m.group(1)), c=int(m.group(2)))
    m = re.match(r"Révolte ! Le président (\S+) est renversé par (\d+) cerveaux", fr)
    if m:
        return "c", dict(a=ids.get(m.group(1)), b=int(m.group(2)))
    m = re.match(r"Coup de palais : le ministre (\S+) \(\S+\) renverse le président (\S+)", fr)
    if m:
        return "k", dict(a=ids.get(m.group(1)), b=ids.get(m.group(2)))
    m = re.match(r"(\S+) entre au gouvernement du président (\S+)", fr)
    if m:
        return "m", dict(sous=2, a=ids.get(m.group(1)), b=ids.get(m.group(2)))
    m = re.match(r"Le ministre (\S+) est limogé", fr)
    if m:
        return "m", dict(sous=0, a=ids.get(m.group(1)))
    m = re.match(r"Remaniement : (\S+) quitte le gouvernement", fr)
    if m:
        return "m", dict(sous=1, a=ids.get(m.group(1)))
    m = re.match(r"Le président (\S+) ne répond plus", fr)
    if m:
        return "v", dict(a=ids.get(m.group(1)))
    return None, None


def historique(jours, ids):
    """Faits datés de chaque citoyen (clé : numéro). Les périodes de révolte et de censure sont des intervalles de dates."""
    h = {n: [] for n in range(1, 121)}
    ministres = set()
    periodes = {"rebelle": {}, "censure": {}}   # numéro -> date de début de la période en cours
    premier_etat = None
    veille = None

    def ajoute(n, x):
        if isinstance(n, int) and 1 <= n <= 120:
            h[n].append(x)

    for brut in jours:
        jf = brut["date"]
        for ev in brut.get("evenements") or []:
            k, x = ev.get("type"), dict(ev)
            if k is None:
                k, x = faits_du_texte(((ev.get("texte") or {}).get("fr")) or "", ids)
                if k is None:
                    continue
            hr = ev.get("heure")
            d = quand(jf, hr)
            base = {"d": d, "h": hr}
            if k == "e":
                n = x.get("a")
                if x.get("sous", 0) & 1:
                    ajoute(n, {**base, "t": "elu", "p": x.get("c"), "r": RAISON[(x.get("sous", 0) >> 1) & 3]})
                    if x.get("d"):
                        ajoute(x["d"], {**base, "t": "battu", "par": n})
                    # Nouveau président : l'ancien gouvernement s'en va (les ministres reconduits réapparaissent par « entre »)
                    for m in sorted(ministres):
                        ajoute(m, {**base, "t": "quitte"})
                    ministres.clear()
                else:
                    ajoute(n, {**base, "t": "reelu", "p": x.get("c")})
            elif k == "c":
                ajoute(x.get("a"), {**base, "t": "renverse", "n": x.get("b")})
                for m in sorted(ministres):
                    ajoute(m, {**base, "t": "quitte", "chute": 1})
                ministres.clear()
            elif k == "k":
                ajoute(x.get("a"), {**base, "t": "coup", "contre": x.get("b")})
                ajoute(x.get("b"), {**base, "t": "trahi", "par": x.get("a")})
                for m in sorted(ministres - {x.get("a")}):
                    ajoute(m, {**base, "t": "quitte", "chute": 1})
                ministres.clear()
            elif k == "m":
                s, n = x.get("sous"), x.get("a")
                if s == 2:
                    ajoute(n, {**base, "t": "entre", "pres": x.get("b")})
                    ministres.add(n)
                elif s in (0, 1):
                    ajoute(n, {**base, "t": "limoge" if s == 0 else "quitte"})
                    ministres.discard(n)
            elif k == "v":
                ajoute(x.get("a"), {**base, "t": "injoignable"})
        # État des citoyens (fichiers quotidiens seulement)
        cits = brut.get("citoyens")
        if isinstance(cits, list) and cits:
            if premier_etat is None:
                premier_etat = jf
            pays = brut.get("pays") or {}
            if isinstance(pays.get("ministres"), list):
                ministres = set(pays["ministres"])   # l'état publié fait foi en fin de journée
            # Une candidature date de l'ouverture de la campagne, quand elle est dans le même fichier ; sinon, du jour du fichier
            o = next((ev for ev in brut.get("evenements") or [] if ev.get("type") == "o"), None)
            cand = {"d": quand(jf, o.get("heure")), "h": o.get("heure")} if o else {"d": jf, "h": None}
            for c in cits:
                n = c.get("id")
                etat, jour = set(c.get("etat") or []), set(c.get("jour") or [])
                if "candidat" in jour:
                    ajoute(n, {**cand, "t": "candidat"})
                for p in ("rebelle", "censure"):
                    cours = periodes[p]
                    if p in etat and n not in cours:
                        cours[n] = jf
                    elif p not in etat and n in cours:
                        ajoute(n, {"d": cours.pop(n), "fin": veille, "t": p})
            veille = jf
    for p, cours in periodes.items():   # périodes encore en cours au dernier jour publié
        for n, debut in cours.items():
            ajoute(n, {"d": debut, "fin": None, "t": p})
    for n in h:
        h[n].sort(key=lambda x: (x["d"], -1 if x.get("h") is None and "fin" in x else (x.get("h") if x.get("h") is not None else 99)))
    return h, premier_etat


# ---------------------------------------------------------------- programme

def mettre_a_jour(racine, source, attendre=0):
    latest = lire(racine / "data" / "latest.json", {})
    ere = int(latest.get("ere") or 1)
    registre = lire(racine / "data" / "citoyens.json", {})
    ids = {r[1]: r[0] for r in registre.get("citoyens") or [] if isinstance(r, list) and len(r) > 1}
    fin = time.time() + attendre
    while attendre and time.time() < fin:
        dates = {f.get("date") for f in manifeste(source, f"donnees/ere-{ere:03d}/manifeste.json")}
        if latest.get("date") in dates:
            break
        print("Fichier brut du soir pas encore publié : nouvel essai dans 60 s")
        time.sleep(60)
    jours = jours_publies(source, ere)
    if registre.get("ere") not in (None, ere) or not jours:
        print("Rien à écrire (ère différente ou aucun jour publié).")
        return
    h, premier_etat = historique(jours, ids)
    sortie = {"format": 1, "ere": ere, "du": jours[0]["date"], "au": jours[-1]["date"], "etatsDepuis": premier_etat,
              "note": "Faits relevés dans les fichiers bruts publiés (microcontroland-data). d = date (heure de Paris), h = heure du pays, "
                      "t = type ; rebelle et censure : période du d au fin (fin null = en cours au dernier jour publié).",
              "citoyens": {str(n): v for n, v in h.items() if v}}
    (racine / "data" / "historique.json").write_text(json.dumps(sortie, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"historique : ère {ere}, {len(jours)} jour(s), {sum(len(v) for v in h.values())} fait(s) pour {len(sortie['citoyens'])} citoyen(s)")


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
