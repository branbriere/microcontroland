"""Microcontrôland : la Bibliothèque nationale (FR) / The National Library (EN). Version de base, 1b-5.

Validée par Bran le 5 novembre 2026 : elle remplace l'Encyclopédie prévue. Des livres rangés par ère et
par rayon, compilés chaque soir par ce script à partir des seules données publiées du site (data/latest.json,
data/langue.json, data/histoire.json, data/editions/, data/ambassade.json, galerie.json, atelier.json).
Aucun texte inventé, aucun appel extérieur. Les livres ne sont pas écrits par les Waïnas : ils sont
« compilés par les bibliothécaires de la République », c'est-à-dire par ce programme.

Règles :
- la bibliothèque d'une ère ouvre à l'âge de l'État civil (bibliotheque-catalogue.json, « ouverture ») ;
- chaque livre s'ouvre à son âge, et seulement s'il a un compilateur ; sinon, « en attente d'évolution
  de la civilisation » ; une donnée d'une autre ère n'entre jamais dans un livre ;
- bibliotheque/ere-NNN.json est réécrit chaque soir tant que l'ère est en cours, puis plus jamais :
  les bibliothèques des ères passées restent consultables telles quelles ;
- bibliotheque-index.json : un passage par ligne, pour la recherche (dans la page, sans serveur) et les IA.

Pas de rayon Roman : rien n'y figure avant la sortie du livre concerné (ajout à la main ce jour-là).
Licence MIT. Version 1.0, 9 novembre 2026.

  python3 .github/bibliotheque.py <racine du site>
"""
import html
import json
import re
import unicodedata
import sys
from pathlib import Path

BASE = "https://www.microcontroland.org/"
REGIONS = ["Mines", "Champs", "Raffineries", "Barrage", "Port", "Ville"]
REGION_EN = {"Mines": "Mines", "Champs": "Fields", "Raffineries": "Refineries", "Barrage": "Dam", "Port": "Harbour", "Ville": "City"}
SPEC_EN = {"Cuivre": "Copper", "Blé": "Wheat", "Pétrole": "Oil", "Électricité": "Electricity", "Commerce": "Trade", "Services": "Services"}
MOIS = {"fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"],
        "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]}
AGES = [("la Fondation", "the Founding"), ("la Parole", "Speech"), ("la Mémoire", "Memory"), ("l'État civil", "the Civil Registry"),
        ("la Diplomatie", "Diplomacy"), ("la Curiosité", "Curiosity")]


def T(fr, en=None):
    return {"fr": fr, "en": fr if en is None else en}


def lire(f, defaut):
    try:
        return json.loads(Path(f).read_text(encoding="utf-8"))
    except (ValueError, OSError) as err:
        print(f"Ignoré : {f} ({err})", file=sys.stderr)
        return defaut


def e(x):
    return html.escape(str(x), quote=True)


def date_longue(iso, lg):
    try:
        a, m, j = (int(x) for x in str(iso).split("-"))
    except (ValueError, AttributeError):
        return str(iso or "")
    return f"{j}{'er' if j == 1 else ''} {MOIS['fr'][m - 1]} {a}" if lg == "fr" else f"{j} {MOIS['en'][m - 1]} {a}"


def D(iso):
    """Date courte pour les tableaux (lisible sur téléphone)."""
    try:
        a, m, j = (int(x) for x in str(iso).split("-"))
    except (ValueError, AttributeError):
        return T(str(iso or ""))
    fr = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
    return T(f"{j} {fr[m - 1]} {a}", f"{j} {MOIS['en'][m - 1][:3]} {a}")


def pct(n, lg):
    return f"{n} %" if lg == "fr" else f"{n}%"


def P(n):
    return T(pct(n, "fr"), pct(n, "en"))


def heure(h, lg):
    return f"{h} h" if lg == "fr" else f"{int(h):02d}:00"


def rg(r, lg):
    return REGION_EN.get(r, r) if lg == "en" else r


def R(r):
    return T(r, REGION_EN.get(r, r))


def liste(xs, lg):
    xs = list(xs)
    if len(xs) <= 1:
        return "".join(xs)
    return ", ".join(xs[:-1]) + (" et " if lg == "fr" else " and ") + xs[-1]


def lgs(f):
    """Construit un texte {fr, en} à partir d'une fonction de la langue."""
    return {"fr": f("fr"), "en": f("en")}


def chap(titre, *blocs):
    return {"titre": titre, "blocs": [b for b in blocs if b]}


def table(entetes, lignes):
    return {"table": {"entetes": entetes, "lignes": lignes}}


# ---------------------------------------------------------------- les données de l'ère

class Ctx:
    def __init__(self, racine):
        self.latest = lire(racine / "data" / "latest.json", {})
        self.ere = int(self.latest.get("ere") or 1)
        self.age = int(((self.latest.get("ages") or {}).get("age")) or 0)
        self.date = str(self.latest.get("date") or "")
        self.edition = self.latest.get("day")
        self.langue = lire(racine / "data" / "langue.json", {})
        self.histoire = [m for m in lire(racine / "data" / "histoire.json", []) if isinstance(m, dict) and m.get("ere") == self.ere]
        self.galerie = lire(racine / "galerie.json", {})
        self.atelier = lire(racine / "atelier.json", {})
        self.ambassade = lire(racine / "data" / "ambassade.json", {})
        eds = []
        d = racine / "data" / "editions"
        for f in sorted(d.glob("*.json"), key=lambda p: int(p.stem) if p.stem.isdigit() else 0) if d.exists() else []:
            x = lire(f, None)
            if isinstance(x, dict) and int(x.get("ere") or 0) == self.ere:
                eds.append(x)
        self.editions = eds
        # date de chaque âge : la première édition de l'ère qui l'annonce atteint
        self.age_date = {}
        for x in eds:
            a = int(((x.get("ages") or {}).get("age")) or 0)
            for k in range(a + 1):
                self.age_date.setdefault(k, x.get("date"))

    def meme_ere(self, d):
        return isinstance(d, dict) and int(d.get("ere") or 0) == self.ere


# ---------------------------------------------------------------- les compilateurs (un par livre)

MOT_RE = re.compile(r"«\s*([^»]+?)\s*»\s*\(([^),]+)")
NE_RE = re.compile(r"«\s*([^»]+?)\s*»\s*veut dire\s*«\s*([^»]+?)\s*»")
RETOUR_RE = re.compile(r"Retour d'un mot commun\s*:\s*«\s*([^»]+?)\s*»\s*pour dire\s*«\s*([^»]+?)\s*»")


def dictionnaire(c):
    L = c.langue
    if not c.meme_ere(L) or not L.get("ouvert") or not L.get("mots"):
        return None
    mots = sorted(L["mots"], key=lambda m: unicodedata.normalize("NFD", m.get("mot", "")).encode("ascii", "ignore"))
    en_of = {m["idee"]["fr"]: m["idee"].get("en", m["idee"]["fr"]) for m in L["mots"] if isinstance(m.get("idee"), dict)}
    sons = L.get("sons") or {}
    intro = lgs(lambda lg: (
        f"Ce dictionnaire recense les {L.get('idees')} idées du relevé de la langue. Pour chacune, il donne le mot le plus dit dans le pays "
        f"et le nombre de régions qui le disent. Chaque région garde son propre lexique : le « mot commun » n'est qu'un relevé, celui que disent "
        f"au moins cinq régions sur six. Au {date_longue(c.date, 'fr')}, {L.get('partages')} mots sont communs."
        if lg == "fr" else
        f"This dictionary lists the {L.get('idees')} ideas in the language survey. For each one it gives the word most often said in the country "
        f"and how many regions say it. Every region keeps its own lexicon: the “common word” is only a survey, the one said by at least five "
        f"regions out of six. On {date_longue(c.date, 'en')}, {L.get('partages')} words are common."))
    s = lgs(lambda lg: (f"Les sons de l'ère : {', '.join(sons.get('consonnes', []))} pour les consonnes ; {', '.join(sons.get('voyelles', []))} pour les voyelles."
                        if lg == "fr" else
                        f"The sounds of the era: {', '.join(sons.get('consonnes', []))} for consonants; {', '.join(sons.get('voyelles', []))} for vowels.")) if sons else None
    lignes = [[m["mot"], T(m["idee"]["fr"], m["idee"].get("en")), {"accord": int(m.get("accord") or 0)}] for m in mots]
    ent = table({"fr": ["Mot", "Idée", "Régions d'accord"], "en": ["Word", "Idea", "Regions in agreement"]}, lignes)
    # naissance des mots, d'après la journée des éditions
    nes = []
    for x in c.editions:
        for j in x.get("journee") or []:
            t = ((j.get("texte") or {}).get("fr")) or ""
            if t.startswith("La langue s'enrichit"):
                ms = [(a, b.strip()) for a, b in MOT_RE.findall(t)]
                if ms:
                    nes.append((x.get("date"), "nes", ms, t.endswith("…")))
            elif t.startswith("Un mot commun est né"):
                m = NE_RE.search(t)
                if m:
                    nes.append((x.get("date"), "nes", [(m.group(1), m.group(2))], False))
            elif t.startswith("Retour d'un mot commun"):
                m = RETOUR_RE.search(t)
                if m:
                    nes.append((x.get("date"), "retour", [(m.group(1), m.group(2))], False))

    def ligne(n, lg):
        date, genre, ms, coupe = n
        f = [f"« {a} » ({b if lg == 'fr' else en_of.get(b, b)})" if lg == "fr" else f"“{a}” ({en_of.get(b, b)})" for a, b in ms]
        if genre == "retour":
            return (f"{date_longue(date, 'fr')} : retour de {f[0]}." if lg == "fr" else f"{date_longue(date, 'en')}: {f[0]} comes back.")
        suite = (" et d'autres" if lg == "fr" else " and others") if coupe else ""
        return (f"{date_longue(date, 'fr')} : {liste(f, 'fr')}{suite}." if lg == "fr" else f"{date_longue(date, 'en')}: {liste(f, 'en')}{suite}.")

    naissance = [lgs(lambda lg, n=n: ligne(n, lg)) for n in nes]
    ch = [chap(T("Avertissement", "Foreword"), intro, s), chap(T("Les entrées", "The entries"), ent)]
    if naissance:
        ch.append(chap(T("Naissance des mots, selon le journal", "How the words were born, according to the paper"),
                       T("Dates de parution dans la journée de La Puce Libre.", "Dates as printed in La Puce Libre's “Today” column."), *naissance))
    return {"sous": lgs(lambda lg: (f"Ère {c.ere}, édition du {date_longue(c.date, 'fr')}" if lg == "fr" else f"Era {c.ere}, edition of {date_longue(c.date, 'en')}")),
            "chapitres": ch, "sources": "data/langue.json ; data/editions/ (journée)"}


def _mandats(c):
    g = c.galerie
    if not c.meme_ere(g):
        return []
    out = []
    for m in g.get("mandats") or []:
        if not isinstance(m, dict) or str((m.get("debut") or {}).get("date") or "") > c.date:
            continue   # jamais un fait daté après l'édition du soir
        m = dict(m, elections=[x for x in m.get("elections") or [] if str(x.get("date") or "") <= c.date])
        if m.get("fin") and str(m["fin"].get("date") or "") > c.date:
            m["fin"] = None
        out.append(m)
    return out


def _fin(m, c, lg):
    h = next((x for x in c.histoire if x.get("id") == m.get("id") and x.get("debut") == (m.get("debut") or {}).get("date")), None)
    if h and isinstance(h.get("finPar"), dict):
        return h["finPar"].get(lg) or h["finPar"].get("fr")
    f = m.get("fin")
    if not f:
        return "en fonction" if lg == "fr" else "in office"
    return {"revolte": ("renversé par la rue", "toppled by the street"), "battu": ("battu aux élections", "voted out")}.get(f.get("genre"), ("fin de mandat", "end of term"))[lg == "en"]


RAISON = {"fondatrice": ("élection fondatrice", "founding election"), "post-revolution": ("élection après la révolte", "post-revolt election")}


def annales(c):
    ms = _mandats(c)
    if not c.editions:
        return None
    ages = []
    for k in range(min(c.age, len(AGES) - 1) + 1):
        d = c.age_date.get(k)
        if d:
            ages.append(lgs(lambda lg, k=k, d=d: (f"{'Fondation' if k == 0 else 'Âge de ' + AGES[k][0]} : {date_longue(d, 'fr')}." if lg == "fr"
                                                 else f"{'Founding' if k == 0 else 'Age of ' + AGES[k][1]}: {date_longue(d, 'en')}.")))
    ev = []
    for m in ms:
        for i, el in enumerate(m.get("elections") or []):
            ev.append((el.get("date"), el.get("heure") or 0, lgs(lambda lg, m=m, el=el, i=i: (
                f"{date_longue(el.get('date'), 'fr')} : {m['nom']} ({rg(m['region'], 'fr')}) {'réélu' if i else 'élu'} avec {pct(el.get('pct'), 'fr')}"
                f"{' (' + RAISON[el['raison']][0] + ')' if el.get('raison') in RAISON else ''}."
                if lg == "fr" else
                f"{date_longue(el.get('date'), 'en')}: {m['nom']} ({rg(m['region'], 'en')}) {'re-elected' if i else 'elected'} with {pct(el.get('pct'), 'en')}"
                f"{' (' + RAISON[el['raison']][1] + ')' if el.get('raison') in RAISON else ''}."))))
        f = m.get("fin")
        if f and f.get("date"):
            if f.get("genre") == "revolte":
                txt = lgs(lambda lg, m=m, f=f: (f"{date_longue(f['date'], 'fr')} à {heure(f.get('heure', 0), 'fr')} : révolte de {f.get('rebelles', '?')} rebelles, {m['nom']} renversé par la rue."
                                                  if lg == "fr" else
                                                  f"{date_longue(f['date'], 'en')} at {heure(f.get('heure', 0), 'en')}: a revolt of {f.get('rebelles', '?')} rebels topples {m['nom']}."))
            else:
                txt = lgs(lambda lg, m=m, f=f: (f"{date_longue(f['date'], 'fr')} : fin du mandat de {m['nom']} ({_fin(m, c, 'fr').lower()})."
                                                  if lg == "fr" else
                                                  f"{date_longue(f['date'], 'en')}: end of {m['nom']}'s term ({_fin(m, c, 'en').lower()})."))
            ev.append((f["date"], (f.get("heure") or 0) - 0.5, txt))
    ev.sort(key=lambda x: (x[0] or "", x[1]))
    rec = [lgs(lambda lg, r=r: (f"{r['titre'][lg]} : {r['valeur'][lg]}{', ' + r['qui'] if r.get('qui') else ''}, jour {r.get('jour')}." if lg == "fr"
                                 else f"{r['titre'][lg]}: {r['valeur'][lg]}{', ' + r['qui'] if r.get('qui') else ''}, day {r.get('jour')}."))
           for r in c.latest.get("records") or [] if isinstance(r.get("titre"), dict) and isinstance(r.get("valeur"), dict)]
    debut = c.editions[0].get("date")
    ch = [chap(T("Les âges de la civilisation", "The ages of civilisation"), *ages)]
    if ev:
        ch.append(chap(T("Chronologie", "Timeline"), *[x[2] for x in ev]))
    if rec:
        ch.append(chap(T("Records de l'ère", "Records of the era"), *rec))
    return {"sous": lgs(lambda lg: (f"Du {date_longue(debut, 'fr')} au {date_longue(c.date, 'fr')}" if lg == "fr" else f"From {date_longue(debut, 'en')} to {date_longue(c.date, 'en')}")),
            "chapitres": ch, "sources": "data/editions/ (âges) ; galerie.json (mandats) ; data/histoire.json ; data/latest.json (records)"}


def presidents(c):
    ms = _mandats(c)
    if not ms:
        return None
    lignes = []
    for m in ms:
        els = m.get("elections") or []
        fin = (m.get("fin") or {}).get("date")
        lignes.append([m["nom"], R(m["region"]), D((m.get("debut") or {}).get("date")),
                       D(fin) if fin else T("en fonction", "in office"),
                       lgs(lambda lg, els=els: ", ".join(pct(x.get("pct"), lg) for x in els)),
                       lgs(lambda lg, m=m: _fin(m, c, lg) if m.get("fin") else "—")])
    n_el = sum(len(m.get("elections") or []) for m in ms)
    reg = table({"fr": ["Président", "Région", "Du", "Au", "Scores", "Fin"], "en": ["President", "Region", "From", "To", "Results", "End"]}, lignes)
    et = c.latest.get("etat") or {}
    gouv = None
    if et:
        mins = [x for x in et.get("ministresNoms") or [] if isinstance(x, dict)]
        gouv = lgs(lambda lg: (
            f"Régime : {(et.get('regime') or {}).get('fr', '?')}. Capitale : {et.get('capitale', '?')}. {c.latest.get('presidentNom', '?')} gouverne depuis "
            f"{(et.get('auPouvoirDepuis') or {}).get('fr', '?')}"
            + (f", avec {len(mins)} ministres : {liste([x.get('nom', '?') + ' (' + rg(x.get('region'), 'fr') + ')' for x in mins], 'fr')}" if mins else "")
            + f". Satisfaction : {pct(et.get('satisfaction', '?'), 'fr')}."
            if lg == "fr" else
            f"Regime: {(et.get('regime') or {}).get('en', '?')}. Capital: {rg(et.get('capitale', '?'), 'en')}. {c.latest.get('presidentNom', '?')} has governed for "
            f"{(et.get('auPouvoirDepuis') or {}).get('en', '?')}"
            + (f", with {len(mins)} ministers: {liste([x.get('nom', '?') + ' (' + rg(x.get('region'), 'en') + ')' for x in mins], 'en')}" if mins else "")
            + f". Satisfaction: {pct(et.get('satisfaction', '?'), 'en')}."))
    cens = [x.get("date") for x in c.editions if isinstance(x.get("censure"), dict) and x["censure"].get("active")]
    ch = [chap(T("Registre des mandats", "Register of terms"), reg)]
    if gouv:
        ch.append(chap(lgs(lambda lg: f"Le gouvernement au {date_longue(c.date, lg)}" if lg == "fr" else f"The government on {date_longue(c.date, lg)}"), gouv))
    if cens:
        ch.append(chap(T("La censure", "Censorship"), lgs(lambda lg: (
            f"Le journal a paru sous censure du {date_longue(cens[0], 'fr')} au {date_longue(cens[-1], 'fr')} ({len(cens)} éditions). "
            "Seuls les articles étaient relus par le palais : les chiffres du pays ont toujours été publiés tels quels."
            if lg == "fr" else
            f"The paper came out under censorship from {date_longue(cens[0], 'en')} to {date_longue(cens[-1], 'en')} ({len(cens)} issues). "
            "Only the articles were read by the palace: the country's figures were always published as they were."))))
    return {"sous": lgs(lambda lg: (f"{len(ms)} présidents, {n_el} élections" if lg == "fr" else f"{len(ms)} presidents, {n_el} elections")),
            "chapitres": ch, "sources": "galerie.json ; data/histoire.json ; data/latest.json (etat) ; data/editions/ (censure)"}


def atlas(c):
    regs = [r for r in c.latest.get("regions") or [] if isinstance(r, dict) and r.get("nom")]
    if len(regs) != 6:
        return None
    L = c.langue if c.meme_ere(c.langue) else {}
    mot = {m["idee"]["fr"]: m["mot"] for m in L.get("mots") or [] if isinstance(m.get("idee"), dict)}
    cap = (c.latest.get("etat") or {}).get("capitale")
    lignes = [[T(r["nom"] + (" (capitale)" if r["nom"] == cap else ""), REGION_EN.get(r["nom"], r["nom"]) + (" (capital)" if r["nom"] == cap else "")),
               mot.get(r["nom"], "—"), T(r.get("specialite", "—"), SPEC_EN.get(r.get("specialite"), r.get("specialite", "—"))), str(r.get("cerveaux", "?"))] for r in regs]
    tab = table({"fr": ["Région", "Nom dans la langue", "Spécialité", "Cerveaux"], "en": ["Region", "Name in the language", "Speciality", "Brains"]}, lignes)
    n = sum(int(r.get("cerveaux") or 0) for r in regs)
    pop = ((c.latest.get("etat") or {}).get("population")) or {}
    pays = lgs(lambda lg: (
        (f"Le pays tout entier se dit « {mot['pays']} » et tient dans une « {mot['boîte']} », la boîte. " if lg == "fr" and "pays" in mot and "boîte" in mot else
         f"The whole country is called “{mot['pays']}” and fits in a “{mot['boîte']}”, the box. " if "pays" in mot and "boîte" in mot else "")
        + (f"Population officielle : {pop.get('fr', '?')} selon le journal ; {n} cerveaux selon le recensement." if lg == "fr"
           else f"Official population: {pop.get('en', '?')} according to the paper; {n} brains according to the census.")))
    b = c.latest.get("bourse") or {}
    if b.get("fermee"):
        bo = T(f"Le {date_longue(c.date, 'fr')}, la bourse était fermée.", f"On {date_longue(c.date, 'en')}, the stock exchange was closed.")
    else:
        bo = lgs(lambda lg: (f"Bourse du {date_longue(c.date, 'fr')} : " if lg == "fr" else f"Stock exchange on {date_longue(c.date, 'en')}: ")
                 + ", ".join(f"{(x.get('matiere') if lg == 'fr' else SPEC_EN.get(x.get('matiere'), x.get('matiere'))).lower()} "
                             f"{'+' if (x.get('variation') or 0) > 0 else ''}{str(x.get('variation')).replace('.', ',') if lg == 'fr' else x.get('variation')}{' %' if lg == 'fr' else '%'}"
                             for x in b.get("lignes") or []) + ".")
    return {"sous": T(f"{n} cerveaux en six régions", f"{n} brains in six regions"),
            "chapitres": [chap(T("Les régions", "The regions"), tab, pays), chap(T("Le relief économique", "The economic landscape"), bo)],
            "sources": "data/latest.json (regions, etat, bourse) ; data/langue.json"}


def anatomie(c):
    et = c.latest.get("etat") or {}
    s7 = c.latest.get("satisfaction7j") or []
    if not et:
        return None
    ana = T("Chaque citoyen est un petit réseau de neurones : 9 entrées, 6 neurones cachés, 3 sorties. Il porte 81 poids : 6 × 10 pour la première couche "
            "(9 entrées et un biais) et 3 × 7 pour la seconde (6 cachés et un biais). Chaque poids est rangé comme un entier ; sa valeur vaut l'entier × 5 / 127. "
            "120 cerveaux de 81 poids tiennent en 9 720 octets.",
            "Every citizen is a small neural network: 9 inputs, 6 hidden neurons, 3 outputs. It carries 81 weights: 6 × 10 for the first layer "
            "(9 inputs and a bias) and 3 × 7 for the second (6 hidden and a bias). Each weight is stored as an integer; its value is the integer × 5 / 127. "
            "120 brains of 81 weights fit in 9,720 bytes.")
    gal = T("Les poids des présidents, quand ils ont été relevés, sont exposés à la Galerie des présidents.", "The presidents' weights, when they were recorded, are on show in the Presidential Gallery.")
    phy = lgs(lambda lg: (
        f"Humeur du pays le {date_longue(c.date, 'fr')} : {pct(et.get('satisfaction', '?'), 'fr')} de satisfaction, peur {et.get('peur', '?')}, colère {et.get('colere', '?')}."
        + (f" Sur sept jours : {liste([pct(x, 'fr') for x in s7], 'fr')}." if s7 else "")
        if lg == "fr" else
        f"The country's mood on {date_longue(c.date, 'en')}: {pct(et.get('satisfaction', '?'), 'en')} satisfaction, fear {et.get('peur', '?')}, anger {et.get('colere', '?')}."
        + (f" Over seven days: {liste([pct(x, 'en') for x in s7], 'en')}." if s7 else "")))
    pat = T("Chapitre en préparation : les cas observés seront comptés dans les fichiers bruts avant d'être écrits. Les soins viendront avec la mise à jour 5.",
            "Chapter in preparation: observed cases will be counted in the raw files before being written up. Care will come with update 5.")
    return {"sous": T("Tome I : le cerveau 9-6-3", "Volume I: the 9-6-3 brain"),
            "chapitres": [chap(T("Anatomie", "Anatomy"), ana, gal), chap(T("Physiologie", "Physiology"), phy), chap(T("Pathologies", "Pathologies"), pat)],
            "sources": "galerie.json (note) ; data/latest.json (etat, satisfaction7j)"}


def foi(c):
    f = ((c.latest.get("etat") or {}).get("foi")) or {}
    if not isinstance(f.get("croyants"), int):
        return None
    pres = f.get("president")
    pres_en = {"croyant": "a believer", "agnostique": "agnostic", "athée": "an atheist", "athee": "an atheist"}.get(pres, pres)
    rec = lgs(lambda lg: (
        f"Au {date_longue(c.date, 'fr')} : {pct(f['croyants'], 'fr')} de croyants, {pct(f.get('agnostiques', '?'), 'fr')} d'agnostiques, {pct(f.get('athees', '?'), 'fr')} d'athées."
        + (f" Le président {c.latest.get('presidentNom', '')} est {pres}." if pres else "")
        if lg == "fr" else
        f"On {date_longue(c.date, 'en')}: {pct(f['croyants'], 'en')} believers, {pct(f.get('agnostiques', '?'), 'en')} agnostics, {pct(f.get('athees', '?'), 'en')} atheists."
        + (f" President {c.latest.get('presidentNom', '')} is {pres_en}." if pres else "")))
    barre = {"barre": [[f["croyants"], "c"], [f.get("agnostiques", 0), "a"], [f.get("athees", 0), "t"]]}
    L = c.langue if c.meme_ere(c.langue) else {}
    sacre = [m for m in L.get("mots") or [] if isinstance(m.get("idee"), dict) and m["idee"]["fr"] in ("Créateur", "fin du monde", "foi", "doute")]
    voc = lgs(lambda lg: (" ; " if lg == "fr" else "; ").join(
        (f"« {m['mot']} », {m['idee']['fr']} ({m['accord']} région{'s' if m['accord'] > 1 else ''} sur 6)" if lg == "fr"
         else f"“{m['mot']}”, {m['idee'].get('en', m['idee']['fr'])} ({m['accord']} region{'s' if m['accord'] > 1 else ''} out of 6)") for m in sacre) + ".") if sacre else None
    tem = lgs(lambda lg: (
        f"Il faudra un tiers de croyants pendant plusieurs jours. Le pays en compte {pct(f['croyants'], 'fr')}. Le Temple n'est construit ni dans le pays ni dans le programme : il est prévu à la mise à jour 3."
        if lg == "fr" else
        f"It will take one third of believers for several days. The country has {pct(f['croyants'], 'en')}. The Temple is built neither in the country nor in the program: it is planned for update 3."))
    ch = [chap(T("Le recensement de la foi", "The census of faith"), barre, rec)]
    if voc:
        ch.append(chap(T("Le vocabulaire sacré", "The sacred vocabulary"), voc))
    ch.append(chap(T("Le Temple", "The Temple"), tem))
    return {"sous": T("Croyants, agnostiques et athées", "Believers, agnostics and atheists"), "chapitres": ch,
            "sources": "data/latest.json (etat.foi) ; data/langue.json"}


def art_primitif(c):
    jours = [j for j in (c.atelier.get("jours") or []) if int(j.get("ere") or 0) == c.ere and str(j.get("date") or "") <= c.date]
    if not jours:
        return None
    a = jours[-1]
    n = a.get("artiste")
    blocs = []
    if n and a.get("dessins") and a["dessins"][n - 1]:
        reg = REGIONS[(n - 1) // 20]
        blocs.append({"dessin": a["dessins"][n - 1], "legende": T(f"Sans titre, citoyen n° {n} ({reg}), soir du {date_longue(a.get('date'), 'fr')}",
                                                                  f"Untitled, Citizen No. {n} ({REGION_EN[reg]}), evening of {date_longue(a.get('date'), 'en')}")})
    cr = a.get("critique") or {}
    if cr.get("fr"):
        blocs.append(T(" ".join(cr["fr"]), " ".join(cr.get("en") or cr["fr"])))
    nb = sum(1 for g in a.get("dessins") or [] if g)
    blocs.append(T(f"{nb} dessins exposés ce soir-là ; {len(jours)} soirs à l'atelier depuis le {date_longue(jours[0].get('date'), 'fr')}.",
                   f"{nb} drawings shown that evening; {len(jours)} evenings at the Studio since {date_longue(jours[0].get('date'), 'en')}."))
    st = T("Art primitif (5 × 5, une couleur) aujourd'hui. Art intermédiaire (cubes 8 × 8 × 8) dans une autre mise à jour. Art évolué, en couleur, à la Curiosité.",
           "Primitive art (5 × 5, one colour) today. Intermediate art (8 × 8 × 8 cubes) in a later update. Advanced art, in colour, at Curiosity.")
    return {"sous": T("Les dessins 5 × 5 du soir", "The evening's 5 × 5 drawings"),
            "chapitres": [chap(lgs(lambda lg: f"Planche du {date_longue(a.get('date'), 'fr')}" if lg == "fr" else f"Plate of {date_longue(a.get('date'), 'en')}"), *blocs),
                          chap(T("Stades de l'art", "Stages of art"), st)],
            "sources": "atelier.json ; feuille de route (stades de l'art)"}


def relations(c):
    am = c.ambassade
    if not c.meme_ere(am) or not am.get("ouvert"):
        return None
    d = c.age_date.get(4)
    qs = [x for x in am.get("questions") or [] if isinstance(x.get("q"), dict)]
    voix = sum(int(x.get("voix") or 0) for x in qs)
    amb = am.get("ambassadeur", "?")
    o = lgs(lambda lg: (
        f"L'Ambassade de la République a ouvert le {date_longue(d, 'fr')}, à l'âge de la Diplomatie. Ambassadeur : {amb}. Lettres envoyées : {am.get('lettres', 0)}."
        if lg == "fr" else
        f"The Embassy of the Republic opened on {date_longue(d, 'en')}, at the Age of Diplomacy. Ambassador: {amb}. Letters sent: {am.get('lettres', 0)}."))
    q = [T(f"{x['id']}. {x['q']['fr']}", f"{x['id']}. {x['q'].get('en', x['q']['fr'])}") for x in qs]
    v = T(f"Voix reçues à ce jour : {voix}. La République s'en tient, pour l'instant, à une diplomatie de l'écoute.",
          f"Votes received to date: {voix}. For now, the Republic practises a diplomacy of listening.")
    return {"sous": T("Tome I : l'ouverture au monde", "Volume I: opening to the world"),
            "chapitres": [chap(T("L'Ambassade", "The Embassy"), o),
                          chap(T("Les questions de l'ambassadeur", "The ambassador's questions"), *q, v)],
            "sources": "data/ambassade.json ; data/editions/ (âge de la Diplomatie)"}


COMPILATEURS = {"dictionnaire": dictionnaire, "annales": annales, "presidents": presidents, "atlas": atlas, "anatomie": anatomie,
                "foi": foi, "art_primitif": art_primitif, "relations": relations}


def compiler(c, cat):
    """Les livres de l'ère en cours. Un livre n'est compilé que si son âge est atteint."""
    livres = []
    for b in cat.get("livres") or []:
        if str(b.get("rayon")) == "roman":
            continue   # jamais par le script : ajout à la main le jour de la sortie
        ent = {"cote": b["cote"], "rayon": b["rayon"], "titre": T(b["fr"], b["en"]), "age": int(b.get("age") or 0)}
        corps = None
        if c.age >= ent["age"] and b.get("compilateur") in COMPILATEURS:
            try:
                corps = COMPILATEURS[b["compilateur"]](c)
            except Exception as err:   # une donnée manquante ne doit jamais casser la bibliothèque
                print(f"{b['cote']} : non compilé ({err!r})", file=sys.stderr)
                corps = None
        if corps:
            ent.update(corps)
        else:
            k = ent["age"]
            att = b.get("attente") or {}
            ent["attente"] = {lg: att.get(lg) or (f"Âge de {AGES[k][0]}." if lg == "fr" else f"The Age of {AGES[k][1]}.") for lg in ("fr", "en")}
        livres.append(ent)
    return livres


# ---------------------------------------------------------------- la page

L = {
    "fr": {
        "titre": "Bibliothèque nationale", "haut": "République de Microcontrôland · salle de lecture",
        "chapo": "Les livres de la République, rangés par ère et par rayon. Ils sont compilés chaque soir par les bibliothécaires de la République "
                 "(un programme) à partir des seules données publiées ; aucun n'est écrit par les Waïnas. Un rayon s'ouvre quand la civilisation y arrive, "
                 "et une ère terminée reste consultable pour toujours.",
        "desc": "La Bibliothèque nationale de Microcontrôland : des livres par ère et par rayon, compilés chaque soir à partir des données publiées du pays.",
        "regles": [["Silence : 120 cerveaux réfléchissent.", "120 citoyens, 81 poids chacun."],
                   ["Le fonds le plus riche du pays.", "C'est la seule bibliothèque. {o} livres ouverts, {a} en attente."],
                   ["Prêt illimité, aucun retard possible.", "Chaque livre est une page du site : tous les lecteurs peuvent l'emprunter en même temps."]],
        "vrai": "Ce qui est vrai : ",
        "chercher": "Chercher dans les livres (mot, nom, date…)", "exemple": "ex. Kiti, censure, doute, Barrage", "tous": "Tous les rayons",
        "trouve": "{n} livre(s) contiennent « {q} »", "rien": "Aucun passage ne contient « {q} ».",
        "ere": "Ère {n}", "en_cours": "en cours", "close": "terminée, fonds figé",
        "ouverte": "salle ouverte depuis l'âge de l'État civil ({d})", "fermee": "La salle de lecture de l'ère {n} ouvrira à l'âge de l'État civil.",
        "attente": "En attente d'évolution de la civilisation", "chapitres": "{n} chapitres", "sources": "Sources : ",
        "ouverts": "{o} / {t} ouvert(s)", "accord": "{n} région{s} sur 6",
        "foi_leg": ["croyants", "agnostiques", "athées"],
        "pied": "Les livres sont compilés automatiquement ; leurs chiffres sont ceux des données publiées, et le ton de bibliothèque nationale est une plaisanterie. "
                "Catalogue : {cat}. Index de recherche : {idx}.",
        "maj_le": "Page mise à jour automatiquement après l'édition n° {n} du {d}.",
        "menu": ["Le journal", "Archives", "Histoire", "La langue", "Mon citoyen", "L'ambassade", "Le tourisme", "Le Temple", "Recherche", "Le projet", "Flux RSS"],
        "mast": ("Quotidien officieux de la République", "Bibliothèque nationale"), "tag": "Le seul journal de Microcontrôland, écrit chaque soir par la passerelle",
        "retour": "Lire la dernière édition", "mentions": "Mentions légales", "rss": "feed.xml", "autre": ("en", "English", "feed-en.xml", "La Puce Libre (English)"),
    },
    "en": {
        "titre": "National Library", "haut": "Republic of Microcontrôland · reading room",
        "chapo": "The books of the Republic, shelved by era and by section. They are compiled every evening by the librarians of the Republic "
                 "(a program) from published data alone; none is written by the Waïnas. A section opens when civilisation gets there, "
                 "and a finished era stays open for reading forever.",
        "desc": "Microcontrôland's National Library: books by era and by section, compiled every evening from the country's published data.",
        "regles": [["Silence: 120 brains at work.", "120 citizens, 81 weights each."],
                   ["The richest collection in the country.", "It is the only library. {o} books open, {a} waiting."],
                   ["Unlimited loans, no late returns.", "Every book is a page of the website: all readers can borrow it at the same time."]],
        "vrai": "What is true: ",
        "chercher": "Search the books (word, name, date…)", "exemple": "e.g. Kiti, censorship, doubt, Dam", "tous": "All sections",
        "trouve": "{n} book(s) contain “{q}”", "rien": "No passage contains “{q}”.",
        "ere": "Era {n}", "en_cours": "ongoing", "close": "ended, collection frozen",
        "ouverte": "reading room open since the Age of the Civil Registry ({d})", "fermee": "The reading room of era {n} will open at the Age of the Civil Registry.",
        "attente": "Waiting for civilisation to evolve", "chapitres": "{n} chapters", "sources": "Sources: ",
        "ouverts": "{o} / {t} open", "accord": "{n} region{s} out of 6",
        "foi_leg": ["believers", "agnostics", "atheists"],
        "pied": "The books are compiled automatically; their figures are those of the published data, and the national-library tone is a joke. "
                "Catalogue: {cat}. Search index: {idx}.",
        "maj_le": "Page updated automatically after issue no. {n} of {d}.",
        "menu": ["The paper", "Archive", "History", "The language", "My citizen", "The embassy", "Tourism", "The Temple", "Research", "The project", "RSS feed"],
        "mast": ("Unofficial daily of the Republic", "National Library"), "tag": "The only newspaper in Microcontrôland, written every evening by the gateway",
        "retour": "Read the latest issue", "mentions": "Legal notice", "rss": "feed-en.xml", "autre": ("fr", "Français", "feed.xml", "La Puce Libre (français)"),
    },
}

STYLE = """<style>
.bn-regles{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin:18px 0}
.bn-regles div{border-top:2px solid var(--ink);padding-top:6px;min-width:0}.bn-regles p{margin:0}.bn-regles .j{font-weight:600}
.bn-regles .v{font:13px/1.5 var(--f-data);color:var(--muted);margin-top:4px}
.bn-cherche{display:grid;gap:8px;margin:18px 0;padding:12px 0;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule)}
.bn-cherche label{font:13px var(--f-data);color:var(--muted)}
.bn-cherche input{width:100%;font:inherit;padding:8px 10px;border:1px solid var(--ink);background:var(--sheet);color:var(--ink);border-radius:0}
.bn-puces{display:flex;flex-wrap:wrap;gap:6px}
.bn-puces button{font:12.5px var(--f-data);border:1px solid var(--ink);background:transparent;color:var(--ink);padding:3px 8px;cursor:pointer}
.bn-puces button[aria-pressed="true"]{background:var(--ink);color:var(--sheet)}
.bn-compte{font:13px var(--f-data);color:var(--muted)}
.bn-ere{font:13px var(--f-data);color:var(--muted);margin:22px 0 4px}.bn-ere b{background:var(--ink);color:var(--sheet);padding:2px 8px;margin-right:6px}
.bn-rayon h3{margin:20px 0 6px;display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}.bn-rayon h3 small{font:12.5px var(--f-data);color:var(--muted);font-weight:400}
details.bn-livre{border:1px solid var(--rule);background:var(--sheet);margin:8px 0;padding:0 14px;min-width:0}
details.bn-livre summary{cursor:pointer;padding:10px 0;list-style-position:outside}
details.bn-livre summary .cote{font:12.5px var(--f-data);color:var(--warn);margin-right:8px}
details.bn-livre summary .st{display:block;font:12.5px var(--f-data);color:var(--muted)}
details.bn-livre[open] summary{border-bottom:1px solid var(--rule);margin-bottom:6px}
.bn-livre h4{margin:16px 0 4px}.bn-livre p{margin:6px 0}
.bn-livre .src{font:12.5px var(--f-data);color:var(--muted);margin:14px 0 12px}
.bn-attente{border:1px dashed var(--rule);padding:10px 14px;margin:8px 0;color:var(--muted)}
.bn-attente .tampon{display:inline-block;margin-top:6px;font:700 11.5px var(--f-data);letter-spacing:.05em;text-transform:uppercase;color:var(--warn);border:2px solid var(--warn);padding:2px 6px;transform:rotate(-2deg)}
.bn-table{overflow-x:auto;margin:8px 0}.bn-table table{border-collapse:collapse;width:100%;font-size:.95em}
.bn-table th,.bn-table td{border-bottom:1px solid var(--rule);padding:4px 8px 4px 0;text-align:left;vertical-align:top}
.bn-table .acc{white-space:nowrap;letter-spacing:1px}
.bn-barre{display:flex;height:14px;border:1px solid var(--rule);margin:8px 0 2px}.bn-barre span{display:block;height:100%}
.bn-barre .c{background:var(--warn)}.bn-barre .a{background:var(--muted)}.bn-barre .t{background:var(--ink)}
.bn-leg{font:12.5px var(--f-data);color:var(--muted)}
.bn-dessin{display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin:8px 0}.bn-dessin svg{width:90px;height:90px}
.bn-dessin svg .fond{fill:var(--rule);opacity:.35}.bn-dessin svg rect:not(.fond){fill:var(--ink)}
.bn-livre mark{background:var(--warn);color:var(--sheet);padding:0 1px}
</style>"""

SCRIPT = """<script>
(function(){
  var box=document.getElementById('bn-cherche'); if(!box) return; box.hidden=false;
  var q=document.getElementById('bn-q'), out=document.getElementById('bn-res'), filtre='';
  var livres=[].slice.call(document.querySelectorAll('.bn-livre,.bn-attente'));
  var T=JSON.parse(box.getAttribute('data-t'));
  function norm(s){return s.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,'');}
  livres.forEach(function(l){l._txt=norm(l.textContent);l._open=l.open;});
  function nettoie(){[].slice.call(document.querySelectorAll('.bn-livre mark')).forEach(function(m){m.replaceWith(document.createTextNode(m.textContent));});
    [].slice.call(document.querySelectorAll('.bn-livre')).forEach(function(l){l.normalize();});}
  function surligne(el,k){var w=document.createTreeWalker(el,NodeFilter.SHOW_TEXT,null),ns=[],n;while((n=w.nextNode()))ns.push(n);
    ns.forEach(function(t){var s=t.nodeValue,ns2=norm(s),i=ns2.indexOf(k);if(i<0||t.parentNode.closest('summary'))return;var f=document.createDocumentFragment(),a=0;
      while(i>=0){f.appendChild(document.createTextNode(s.slice(a,i)));var m=document.createElement('mark');m.textContent=s.slice(i,i+k.length);f.appendChild(m);a=i+k.length;i=ns2.indexOf(k,a);}
      f.appendChild(document.createTextNode(s.slice(a)));t.parentNode.replaceChild(f,t);});}
  function go(){
    nettoie(); var k=norm(q.value.trim()), n=0;
    [].slice.call(document.querySelectorAll('.bn-rayon')).forEach(function(r){r.hidden=!!filtre&&r.getAttribute('data-rayon')!==filtre;});
    livres.forEach(function(l){var ok=k.length<2||l._txt.indexOf(k)>=0; l.hidden=!ok; if(l.tagName==='DETAILS'){l.open=k.length>=2&&ok?true:l._open; if(k.length>=2&&ok){n++;surligne(l,k);}}});
    out.textContent=k.length<2?'':(n?T.trouve.replace('{n}',n):T.rien).replace('{q}',q.value.trim());
  }
  q.addEventListener('input',go);
  [].slice.call(document.querySelectorAll('.bn-puces button')).forEach(function(b){b.addEventListener('click',function(){filtre=b.getAttribute('data-r');
    [].slice.call(document.querySelectorAll('.bn-puces button')).forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false');});go();});});
})();
</script>"""


def texte(b, lg):
    return b.get(lg) or b.get("fr") or ""


def svg5(g, titre):
    rects = "".join(f'<rect x="{k % 5}" y="{k // 5}" width="1" height="1"/>' for k, ch in enumerate(g) if ch == "1")
    return f'<svg viewBox="0 0 5 5" role="img" aria-label="{e(titre)}"><rect x="0" y="0" width="5" height="5" class="fond"/>{rects}</svg>'


def bloc_html(b, lg):
    Tl = L[lg]
    if "table" in b:
        t = b["table"]
        th = "".join(f"<th>{e(x)}</th>" for x in t["entetes"][lg])
        rows = []
        for ln in t["lignes"]:
            cells = []
            for x in ln:
                if isinstance(x, dict) and "accord" in x:
                    n = int(x["accord"])
                    cells.append(f'<td class="acc" title="{e(Tl["accord"].format(n=n, s="s" if n > 1 else ""))}">{"●" * n}{"○" * (6 - n)} <small>{n}/6</small></td>')
                elif isinstance(x, dict):
                    cells.append(f"<td>{e(texte(x, lg))}</td>")
                else:
                    cells.append(f"<td>{e(x)}</td>")
            rows.append("<tr>" + "".join(cells) + "</tr>")
        return f'<div class="bn-table"><table><thead><tr>{th}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
    if "barre" in b:
        tot = sum(max(0, int(v)) for v, _ in b["barre"]) or 1
        sp = "".join(f'<span class="{c}" style="width:{100 * max(0, int(v)) / tot:.1f}%"></span>' for v, c in b["barre"])
        leg = " · ".join(f"{n} {pct(v, lg)}" for (v, _), n in zip(b["barre"], Tl["foi_leg"]))
        return f'<div class="bn-barre" role="img" aria-label="{e(leg)}">{sp}</div><p class="bn-leg">{e(leg)}</p>'
    if "dessin" in b:
        leg = texte(b["legende"], lg)
        return f'<figure class="bn-dessin">{svg5(b["dessin"], leg)}<figcaption>{e(leg)}</figcaption></figure>'
    return f"<p>{e(texte(b, lg))}</p>"


def livre_html(ere, b, lg):
    Tl = L[lg]
    tit = texte(b["titre"], lg)
    if b.get("attente"):
        return (f'<div class="bn-attente" id="ere{ere}-{e(b["cote"])}"><b>{e(tit)}</b> <span class="bn-compte">{e(b["cote"])}</span>'
                f'<br>{e(texte(b["attente"], lg))}<br><span class="tampon">{e(Tl["attente"])}</span></div>')
    ch = "".join(f'<h4>{e(texte(c["titre"], lg))}</h4>' + "".join(bloc_html(x, lg) for x in c["blocs"]) for c in b["chapitres"])
    return (f'<details class="bn-livre" id="ere{ere}-{e(b["cote"])}"><summary><span class="cote">{e(b["cote"])}</span><b>{e(tit)}</b>'
            f'<span class="st">{e(texte(b["sous"], lg))} · {e(Tl["chapitres"].format(n=len(b["chapitres"])))}</span></summary>'
            f'{ch}<p class="src">{e(Tl["sources"])}{e(b.get("sources", ""))}.</p></details>')


def page(eres, cat, latest, lg):
    Tl = L[lg]
    pre = "../" if lg == "en" else ""
    autre_lg, autre_nom, autre_rss, autre_titre = Tl["autre"]
    fr_url, en_url = BASE + "bibliotheque.html", BASE + "en/bibliotheque.html"
    liens = ["./", "archives.html", "histoire.html", "langue.html", "citoyen.html", "ambassade.html", "tourisme.html", "temple.html", "recherche.html", "projet.html", pre + Tl["rss"]]
    nav = "\n".join(f'    <a href="{h}">{e(t)}</a>' for h, t in zip(liens, Tl["menu"]))
    rayons = [(r["id"], r[lg]) for r in cat.get("rayons") or []]
    tous = [b for x in eres for b in x.get("livres") or []]
    o = sum(1 for b in tous if not b.get("attente"))
    corps = []
    if tous:
        corps.append('<div class="bn-regles">' + "".join(f'<div><p class="j">{e(j)}</p><p class="v">{e(Tl["vrai"])}{e(v.format(o=o, a=len(tous) - o))}</p></div>'
                                                        for j, v in Tl["regles"]) + "</div>")
        t = json.dumps({"trouve": Tl["trouve"], "rien": Tl["rien"]}, ensure_ascii=False)
        puces = f'<button type="button" aria-pressed="true" data-r="">{e(Tl["tous"])}</button>' + "".join(
            f'<button type="button" aria-pressed="false" data-r="{e(k)}">{e(n)}</button>' for k, n in rayons)
        corps.append(f'<div class="bn-cherche" id="bn-cherche" role="search" hidden data-t="{e(t)}"><label for="bn-q">{e(Tl["chercher"])}</label>'
                     f'<input id="bn-q" type="search" placeholder="{e(Tl["exemple"])}" autocomplete="off"><div class="bn-puces">{puces}</div>'
                     f'<div class="bn-compte" id="bn-res" aria-live="polite"></div></div>')
    for x in sorted(eres, key=lambda y: -int(y["ere"])):
        etat = Tl["en_cours"] if x.get("enCours") else Tl["close"]
        if not x.get("livres"):
            corps.append(f'<p class="bn-ere"><b>{e(Tl["ere"].format(n=x["ere"]))}</b>{e(etat)}</p><p>{e(Tl["fermee"].format(n=x["ere"]))}</p>')
            continue
        corps.append(f'<p class="bn-ere"><b>{e(Tl["ere"].format(n=x["ere"]))}</b>{e(etat)} · {e(Tl["ouverte"].format(d=date_longue(x.get("ouverture"), lg)))}</p>')
        for k, n in rayons:
            bs = [b for b in x["livres"] if b["rayon"] == k]
            if not bs:
                continue
            ok = sum(1 for b in bs if not b.get("attente"))
            corps.append(f'<section class="bn-rayon" data-rayon="{e(k)}"><h3>{e(n)}<small>{e(Tl["ouverts"].format(o=ok, t=len(bs)))}</small></h3>'
                         + "".join(livre_html(x["ere"], b, lg) for b in bs) + "</section>")
    maj = Tl["maj_le"].format(n=latest.get("day", "?"), d=date_longue(str(latest.get("date", "")), lg))
    pied = Tl["pied"].format(cat=f'<a href="{pre}bibliotheque-catalogue.json">bibliotheque-catalogue.json</a>',
                             idx=f'<a href="{pre}bibliotheque-index.json">bibliotheque-index.json</a>')
    return f"""<!doctype html>
<html lang="{lg}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<link rel="icon" href="{pre}favicon.ico" sizes="32x32">
<link rel="icon" href="{pre}favicon.svg" type="image/svg+xml">
<title>{e(Tl["titre"])} — Microcontrôland</title>
<meta name="description" content="{e(Tl["desc"])}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="La Puce Libre — Microcontrôland">
<meta property="og:title" content="{e(Tl["titre"])} — Microcontrôland">
<meta property="og:description" content="{e(Tl["desc"])}">
<link rel="alternate" hreflang="fr" href="{fr_url}">
<link rel="alternate" hreflang="en" href="{en_url}">
<link rel="alternate" hreflang="x-default" href="{fr_url}">
<link rel="alternate" type="application/rss+xml" title="La Puce Libre" href="{pre}{Tl["rss"]}">
<link rel="alternate" type="application/rss+xml" title="{e(autre_titre)}" hreflang="{autre_lg}" href="{pre}{autre_rss}">
<link rel="alternate" type="application/json" href="{pre}bibliotheque-index.json">
<link rel="stylesheet" href="{pre}style.css">
<script src="{pre}mesure.js" defer></script>
{STYLE}
</head>
<body>
<div class="wrap">
  <header class="mast">
    <div class="top"><span>{e(Tl["mast"][0])}</span><span>{e(Tl["mast"][1])}</span></div>
    <div class="title"><a href="./">La Puce <span>Libre</span></a></div>
    <p class="tag">{e(Tl["tag"])}</p>
  </header>
  <nav class="main" aria-label="Navigation">
{nav}
  </nav>

  <div class="prose">
    <p class="compte">{e(Tl["haut"])}</p>
    <h1>{e(Tl["titre"])}</h1>
    <p class="chapo">{e(Tl["chapo"])}</p>
    {"".join(corps)}
    <p><small>{pied}</small></p>
    <p><small>{e(maj)}</small></p>
  </div>

  <footer class="site">
    <span><a href="./">{e(Tl["retour"])}</a></span>
    <span><a href="{'en/' if lg == 'fr' else '../'}bibliotheque.html">{e(autre_nom)}</a></span>
    <span><a href="mentions.html">{e(Tl["mentions"])}</a></span>
  </footer>
</div>
{SCRIPT}
{'<script>window.MCL_BASE = "../";</script>' if lg == "en" else ""}
<script src="{pre}reglages.js"></script>
<script src="{pre}commun.js"></script>
<script src="{pre}lang.js"></script>
</body>
</html>
"""


def index(eres):
    out = []
    for x in eres:
        for b in x.get("livres") or []:
            if b.get("attente"):
                continue
            for c in b["chapitres"]:
                for bl in c["blocs"]:
                    if "table" in bl:
                        for ln in bl["table"]["lignes"]:
                            out.append({"ere": x["ere"], "cote": b["cote"], "rayon": b["rayon"], "chapitre": c["titre"],
                                        **{lg: " · ".join(texte(v, lg) if isinstance(v, dict) and "accord" not in v else str(v.get("accord")) + "/6" if isinstance(v, dict) else str(v) for v in ln) for lg in ("fr", "en")}})
                    elif "barre" in bl or "dessin" in bl:
                        continue
                    else:
                        out.append({"ere": x["ere"], "cote": b["cote"], "rayon": b["rayon"], "chapitre": c["titre"], "fr": texte(bl, "fr"), "en": texte(bl, "en")})
    return out


def mettre_a_jour(racine):
    cat = lire(racine / "bibliotheque-catalogue.json", {})
    c = Ctx(racine)
    dossier = racine / "bibliotheque"
    dossier.mkdir(exist_ok=True)
    seuil = int(((cat.get("ouverture") or {}).get("age")) or 3)
    cur = dossier / f"ere-{c.ere:03d}.json"
    ouverte = c.age >= seuil and c.age_date.get(seuil)
    contenu = {"format": 1, "ere": c.ere, "enCours": True, "ouverture": c.age_date.get(seuil) if ouverte else None,
               "edition": c.edition, "date": c.date, "livres": compiler(c, cat) if ouverte else []}
    nouveau = json.dumps(contenu, ensure_ascii=False, separators=(",", ":")) + "\n"
    if not cur.exists() or cur.read_text(encoding="utf-8") != nouveau:
        cur.write_text(nouveau, encoding="utf-8")
    eres = [contenu]
    for f in sorted(dossier.glob("ere-*.json")):
        if f == cur:
            continue
        x = lire(f, None)
        if not isinstance(x, dict) or int(x.get("ere") or 0) >= c.ere:
            continue   # jamais une ère « future » ni un doublon de l'ère en cours
        if x.get("enCours"):
            # ère terminée : on la marque close une seule fois, sans toucher aux livres, puis plus jamais
            x["enCours"] = False
            f.write_text(json.dumps(x, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        eres.append(x)
    (racine / "bibliotheque-index.json").write_text(
        json.dumps({"format": 1, "note": "Un passage par ligne : ère, cote, rayon, chapitre, texte FR et EN. Compilé à partir des données publiées.",
                    "passages": index(eres)}, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    (racine / "bibliotheque.html").write_text(page(eres, cat, c.latest, "fr"), encoding="utf-8")
    (racine / "en").mkdir(exist_ok=True)
    (racine / "en" / "bibliotheque.html").write_text(page(eres, cat, c.latest, "en"), encoding="utf-8")
    n = sum(1 for b in contenu["livres"] if not b.get("attente"))
    print(f"bibliothèque : ère {c.ere}, âge {c.age}, {'ouverte' if ouverte else 'fermée'}, {n} livre(s) ouverts sur {len(contenu['livres'])}, {len(eres)} ère(s)")
    return contenu


def main():
    args = sys.argv[1:]
    mettre_a_jour(Path(args[0] if args else "."))


if __name__ == "__main__":
    main()
