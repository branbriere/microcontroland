"""Microcontrôland : page « Les premières écritures » (FR) et « The First Writings » (EN).

Depuis l'âge de l'État civil, chaque mot des régions peut s'écrire avec un glyphe de 5 cases sur 5.
Le glyphe se calcule à partir du mot qu'une région emploie pour une idée (fichier brut quotidien du
dépôt microcontroland-data, « lexiques », figés au début du jour) : la règle est fixe et publique,
les mots sont ceux que les régions ont inventés. La passerelle ne garde aucun glyphe, comme elle ne
garde aucun lexique : chaque région écrit son propre mot.

Règle G1 « la hampe » (validée par Bran le 5 novembre 2026) : colonne du milieu toujours pleine ;
1re syllabe à gauche, 2e à droite ; rangée i (0 en haut) : trait de 2 cases si le bit (4 − i) de la
syllabe vaut 1 (syllabe = consonne × 4 + voyelle, de 0 à 31). Un glyphe est commun quand au moins
5 régions sur 6 écrivent le même.

Cartouche des noms propres (validé par Bran le 6 novembre 2026) : un cadre d'une case ; chaque
syllabe a sa propre hampe et des traits d'une case à droite ; une colonne vide entre les syllabes ;
la terminaison (coda) est une petite hampe sans trait, en haut pour la 1re coda de l'ère, en bas
pour la 2e ; l'apostrophe (certaines ères seulement) est un point en haut de l'espace qui suit la syllabe. Les sons de l'ère sont recalculés à partir de la graine publiée (« graines.ere »), avec
le même générateur que le firmware (mcl_rng.h, mcl_names.h).

ecriture.json garde chaque jour déjà écrit ; une journée déjà écrite n'est jamais réécrite.
Rien avant l'âge de l'État civil (pays.age < 3) ; une région absente (null) n'écrit rien ce jour-là.
La passerelle et le journal ne changent pas. Licence MIT. Version 1.0, 6 novembre 2026 (firmware 0.9).
1.0.1, 7 novembre 2026 : menu complet du site (Le tourisme, Le Temple), comme les autres pages.

  python3 .github/ecriture.py <racine du site> [--source URL_OU_DOSSIER] [--attendre SECONDES]
"""
import hashlib
import html
import json
import struct
import sys
import time
import urllib.request
from pathlib import Path

BASE = "https://www.microcontroland.org/"
SOURCE = "https://raw.githubusercontent.com/branbriere/microcontroland-data/main/"
DONNEES = "https://donnees.microcontroland.org/"
REGLE = "G1 v1 + cartouche v1"
AGE_ETAT_CIVIL = 3
SEUIL = 5
REGIONS = ["Mines", "Champs", "Raffineries", "Barrage", "Port", "Ville"]
REGION_EN = {"Mines": "Mines", "Champs": "Fields", "Raffineries": "Refineries", "Barrage": "Dam", "Port": "Harbour", "Ville": "City"}
MOIS = {"fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"],
        "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]}


# ---------------------------------------------------------------- règle G1 « la hampe »

def glyphe(s1, s2):
    """Chaîne de 25 caractères, rangée par rangée, « 1 » = case pleine."""
    g = []
    for i in range(5):
        b = 4 - i
        a = (s1 >> b) & 1
        c = (s2 >> b) & 1
        g += [a, a, 1, c, c]
    return "".join(str(x) for x in g)


# ---------------------------------------------------------------- les sons de l'ère (copie exacte de mcl_rng.h et mcl_names.h)

M32 = 0xFFFFFFFF
F32 = lambda x: struct.unpack("f", struct.pack("f", x))[0]
P06, P035, P025, P05 = F32(0.6), F32(0.35), F32(0.25), F32(0.5)
CONS_TOUS = ["p", "t", "k", "b", "d", "g", "m", "n", "s", "z", "r", "l", "v", "f", "h", "j", "w", "ch"]
VOY_TOUS = ["a", "e", "i", "o", "u", "y", "é", "ô", "ï", "ou", "aï"]
CODA_TOUS = ["n", "r", "s", "l", "k", "m", "x", "th"]


class Rng:
    def __init__(self, x):
        self.s = []
        for _ in range(4):
            x = (x + 0x9E3779B9) & M32
            z = x
            z = ((z ^ (z >> 16)) * 0x85EBCA6B) & M32
            z = ((z ^ (z >> 13)) * 0xC2B2AE35) & M32
            self.s.append(z ^ (z >> 16))
        if not any(self.s):
            self.s[0] = 1

    def next(self):
        s = self.s
        rotl = lambda v, k: ((v << k) | (v >> (32 - k))) & M32
        r = (rotl((s[1] * 5) & M32, 7) * 9) & M32
        t = (s[1] << 9) & M32
        s[2] ^= s[0]; s[3] ^= s[1]; s[1] ^= s[2]; s[0] ^= s[3]
        s[2] ^= t
        s[3] = rotl(s[3], 11)
        return r

    def uniform(self):
        return (self.next() >> 8) * (1.0 / 16777216.0)

    def below(self, n):
        return (self.next() * n) >> 32 if n else 0


def phonologie(graine):
    """(consonnes, voyelles, codas, apostrophe, rng) : Phonology::build après NameTable::build."""
    r = Rng(graine ^ 0x4E4F4D53)
    cons, vu = [], set()
    for _ in range(8):
        while True:
            k = r.below(18)
            if k not in vu:
                break
        vu.add(k); cons.append(CONS_TOUS[k])
    voy, vu = [], set()
    for _ in range(4):
        while True:
            k = r.below(11)
            if k not in vu:
                break
        vu.add(k); voy.append(VOY_TOUS[k])
    k0 = r.below(8)
    while True:
        k1 = r.below(8)
        if k1 != k0:
            break
    apo = r.uniform() < P025
    return cons, voy, [CODA_TOUS[k0], CODA_TOUS[k1]], apo, r


def prenoms(graine):
    """Les 120 prénoms de l'ère (NameTable::build), pour le contrôle seulement."""
    cons, voy, coda, apo, r = phonologie(graine)
    noms = []
    for _ in range(120):
        nom = ""
        for tries in range(40):
            n = 2 if (r.uniform() < P06 and tries < 20) else 3
            b = b""
            for i in range(n):
                if i == 1 and apo and r.uniform() < P05:
                    b += b"'" if len(b) + 1 < 16 else b""
                for x in (cons[r.below(8)], voy[r.below(4)]):
                    x = x.encode("utf-8")
                    if len(b) + len(x) < 16:
                        b += x
            if r.uniform() < P035:
                x = coda[r.below(2)].encode("utf-8")
                if len(b) + len(x) < 16:
                    b += x
            if b and 97 <= b[0] <= 122:
                b = bytes([b[0] - 32]) + b[1:]
            nom = b.decode("utf-8")
            if nom not in noms:
                break
        noms.append(nom)
    return noms


def syllabes_du_nom(nom, cons, voy, coda):
    """[(« s », 0-31) …, (« c », 0 ou 1)] ; None si le nom ne se lit pas avec les sons de l'ère."""
    n, out, i = nom.lower(), [], 0
    while i < len(n):
        if n[i] == "'" and out and out[-1][0] == "s":
            out.append(("a", 0)); i += 1; continue
        trouve = None
        for c in sorted(range(8), key=lambda k: -len(cons[k])):
            if n.startswith(cons[c], i):
                j = i + len(cons[c])
                for v in sorted(range(4), key=lambda k: -len(voy[k])):
                    if n.startswith(voy[v], j):
                        trouve = (c * 4 + v, j + len(voy[v]))
                        break
            if trouve:
                break
        if trouve:
            out.append(("s", trouve[0])); i = trouve[1]; continue
        k = next((k for k in (0, 1) if n[i:] == coda[k]), None)
        if k is None:
            return None
        out.append(("c", k)); break
    return out if out and out[0][0] == "s" else None


def cartouche(syl):
    """Liste de rangées (chaînes de « 0 »/« 1 »), cadre compris : 7 rangées."""
    cols = [[0] * 5]
    for t, v in syl:
        if t == "a":
            cols[-1] = [1, 0, 0, 0, 0]   # apostrophe : un point en haut de l'espace entre deux syllabes
            continue
        if t == "s":
            cols.append([1] * 5)
            cols.append([(v >> (4 - i)) & 1 for i in range(5)])
        else:
            cols.append([1, 1, 1, 0, 0] if v == 0 else [0, 0, 1, 1, 1])
        cols.append([0] * 5)
    w = len(cols) + 2
    rangs = ["1" * w] + ["1" + "".join(str(c[y]) for c in cols) + "1" for y in range(5)] + ["1" * w]
    return rangs


# ---------------------------------------------------------------- un jour

def jour_du_brut(brut):
    """Entrée de ecriture.json, ou None avant l'État civil."""
    if int((brut.get("pays") or {}).get("age") or 0) < AGE_ETAT_CIVIL:
        return None
    idees = (brut.get("langue") or {}).get("idees") or []
    vecues = [x for x in idees if x.get("depouilleTick")]
    lex = brut.get("lexiques") or []
    mots = {}
    for x in vecues:
        c = int(x["id"])
        ligne = []
        for r in range(6):
            reg = lex[r] if r < len(lex) else None
            m = reg[c] if isinstance(reg, list) and c < len(reg) and reg[c] else None
            ligne.append([int(m["syllabes"][0]), int(m["syllabes"][1]), m.get("ecrit", "")] if m else None)
        mots[str(c)] = ligne
    soir = None
    for h in reversed(brut.get("heures") or []):
        idee = h.get("idee") or {}
        if "id" not in idee:
            continue
        regs = h.get("regions") or []
        ligne = []
        for r in range(6):
            reg = regs[r] if r < len(regs) else None
            m = (reg or {}).get("mot")
            ligne.append([int(m["syllabes"][0]), int(m["syllabes"][1]), m.get("ecrit", "")] if m else None)
        if any(ligne):
            soir = {"idee": int(idee["id"]), "heure": h.get("heure"), "tick": h.get("tick"), "mots": ligne}
            break
    graine = (brut.get("graines") or {}).get("ere")
    cons, voy, coda, _, _ = phonologie(int(graine)) if graine is not None else (None, None, None, None, None)
    return {"ere": brut.get("ere"), "date": brut.get("date"), "jourEre": brut.get("jourEre"), "edition": brut.get("edition"),
            "age": brut["pays"]["age"], "graine": graine,
            "sons": {"consonnes": cons, "voyelles": voy, "codas": coda} if cons else None,
            "sens": {str(x["id"]): [x.get("fr"), x.get("en")] for x in vecues},
            "mots": mots, "soir": soir}


def commun(ligne):
    """Le glyphe écrit par au moins SEUIL régions, ou None."""
    gs = [glyphe(m[0], m[1]) for m in ligne if m]
    for g in set(gs):
        if gs.count(g) >= SEUIL:
            return g
    return None


# ---------------------------------------------------------------- lecture des données

def lire(f, defaut):
    try:
        return json.loads(Path(f).read_text(encoding="utf-8"))
    except (ValueError, OSError) as err:
        print(f"Ignoré : {f} ({err})", file=sys.stderr)
        return defaut


def charger(source, chemin):
    if source.startswith("http"):
        req = urllib.request.Request(source + chemin + "?t=" + str(int(time.time())), headers={"User-Agent": "microcontroland-ecriture"})
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


def svg(rangs, cls, titre):
    """rangs : chaîne de 25 caractères (glyphe) ou liste de rangées (cartouche)."""
    if isinstance(rangs, str):
        rangs = [rangs[i * 5:(i + 1) * 5] for i in range(5)]
    h, w = len(rangs), len(rangs[0])
    cases = "".join(f'<rect x="{x + .06:.2f}" y="{y + .06:.2f}" width=".88" height=".88"/>' for y, r in enumerate(rangs) for x, c in enumerate(r) if c == "1")
    return (f'<svg class="{cls}" viewBox="0 0 {w} {h}" style="aspect-ratio:{w}/{h}" role="img" aria-label="{e(titre)}">'
            f'<rect class="fond" x="0" y="0" width="{w}" height="{h}"/>{cases}</svg>')


def texte(rangs):
    """Le glyphe en caractères, pour les lecteurs sans image et les IA."""
    if isinstance(rangs, str):
        rangs = [rangs[i * 5:(i + 1) * 5] for i in range(5)]
    return "\n".join("".join("█" if c == "1" else "·" for c in r) for r in rangs)


L = {
    "fr": {
        "titre": "Les premières écritures", "haut": "État civil · l'écriture",
        "chapo": "Depuis l'âge de l'État civil, chaque mot des régions peut s'écrire. Un glyphe de 5 cases sur 5 se calcule à partir du mot : "
                 "la règle est fixe et la même pour tous, les mots sont ceux que les régions ont inventés et se sont transmis. "
                 "Il n'y a pas d'écriture officielle : chaque région écrit son propre mot, et un glyphe devient commun quand 5 régions sur 6 l'écrivent pareil.",
        "desc": "L'écriture de Microcontrôland : des glyphes de 5×5 cases calculés à partir des mots que les régions ont inventés, depuis l'âge de l'État civil.",
        "soir": "Le mot du soir", "soir_sous": "L'idée de la dernière heure du relevé ({h} h) : « {fr} ». Voici comment chaque région l'écrit.",
        "soir_accord": "{n} régions sur 6 l'écrivent de la même façon.", "soir_seul": "Les régions ne l'écrivent pas encore de la même façon.",
        "muette": "muette",
        "soir_muet": "Le {d}, aucune région n'a envoyé son lexique : la page montre le dernier soir reçu, le {r}. Aucun mot n'est jamais inventé.",
        "abc": "L'abécédaire de l'ère {ere}", "abc_sous": "{n} glyphes communs le {d}. L'écriture s'ouvre le {o} ; pour les glyphes venus ensuite, la date est celle du premier jour où au moins 5 régions l'ont écrit pareil.",
        "depuis": "depuis le {d}",
        "var": "Les écritures régionales", "var_sous": "Idées que les régions écrivent encore de plusieurs façons le {d}.",
        "noms": "Les noms", "noms_sous": "Les prénoms ne sont dans aucun lexique, mais ils sont faits des mêmes sons. Ils s'écrivent dans un cadre, une hampe par syllabe : on reconnaît un nom au premier coup d'œil.",
        "pres": "président du {a} au {b}", "pres_en_cours": "président depuis le {a}",
        "lire": "Comment lire un glyphe",
        "regle": "Chaque mot a deux syllabes, et chaque syllabe est un nombre de 0 à 31 (8 consonnes × 4 voyelles, tirées au sort à chaque ère). "
                 "La colonne du milieu, la hampe, est toujours pleine. La première syllabe s'écrit à gauche, la seconde à droite. "
                 "On écrit la syllabe en binaire, de haut en bas : un 1 trace un trait de deux cases, un 0 ne trace rien. "
                 "Les trois rangées du haut donnent la consonne, les deux du bas la voyelle. Deux mots différents ne donnent jamais le même glyphe.",
        "regle_nom": "Dans un nom, chaque syllabe a sa propre hampe et des traits d'une seule case, à droite ; la terminaison est une petite hampe sans trait, en haut ou en bas.",
        "verifier": "Vérifier : {brut} du jour (« lexiques ») et {arch} (tous les jours écrits).", "brut": "le fichier brut", "arch": "ecriture.json",
        "attente": "L'écriture s'ouvre à l'âge de l'État civil. Ce pays n'y est pas encore : aucun glyphe n'est écrit.",
        "maj_le": "Page mise à jour automatiquement après l'édition n° {n} du {d}.",
        "menu": ["Le journal", "Archives", "Histoire", "La langue", "Mon citoyen", "L'ambassade", "Le tourisme", "Le Temple", "Recherche", "Le projet", "Flux RSS"],
        "mast": ("Quotidien officieux de la République", "L'écriture"), "tag": "Le seul journal de Microcontrôland, écrit chaque soir par la passerelle",
        "retour": "Lire la dernière édition", "mentions": "Mentions légales", "rss": "feed.xml", "autre": ("en", "English", "feed-en.xml", "La Puce Libre (English)"),
    },
    "en": {
        "titre": "The First Writings", "haut": "Civil Registry · writing",
        "chapo": "Since the Age of the Civil Registry, every word of the regions can be written down. A glyph of 5 by 5 squares is computed from the word: "
                 "the rule is fixed and the same for everyone, while the words are the ones the regions invented and passed on to each other. "
                 "There is no official script: each region writes its own word, and a glyph becomes common when 5 regions out of 6 write it the same way.",
        "desc": "Writing in Microcontrôland: 5×5 glyphs computed from the words the regions invented, since the Age of the Civil Registry.",
        "soir": "Tonight's word", "soir_sous": "The idea of the last hour on record ({h}:00): “{en}”. Here is how each region writes it.",
        "soir_accord": "{n} regions out of 6 write it the same way.", "soir_seul": "The regions do not yet write it the same way.",
        "muette": "silent",
        "soir_muet": "On {d}, no region sent its lexicon: this page shows the last evening received, {r}. No word is ever made up.",
        "abc": "The alphabet book of era {ere}", "abc_sous": "{n} common glyphs on {d}. Writing opens on {o}; for glyphs that came later, the date is the first day on which at least 5 regions wrote it the same way.",
        "depuis": "since {d}",
        "var": "Regional spellings", "var_sous": "Ideas the regions still write in more than one way on {d}.",
        "noms": "Names", "noms_sous": "First names are in no lexicon, but they are made of the same sounds. They are written inside a frame, one stem per syllable, so a name stands out at a glance.",
        "pres": "President from {a} to {b}", "pres_en_cours": "President since {a}",
        "lire": "How to read a glyph",
        "regle": "Every word has two syllables, and each syllable is a number from 0 to 31 (8 consonants × 4 vowels, drawn at random in each era). "
                 "The middle column, the stem, is always filled. The first syllable is written on the left, the second on the right. "
                 "The syllable is written in binary, top to bottom: a 1 draws a two-square stroke, a 0 draws nothing. "
                 "The top three rows give the consonant, the bottom two the vowel. Two different words never give the same glyph.",
        "regle_nom": "In a name, each syllable has its own stem and one-square strokes on the right; the ending is a short stem with no stroke, at the top or the bottom.",
        "verifier": "Check: {brut} of the day (“lexiques”) and {arch} (every day written so far).", "brut": "the raw data file", "arch": "ecriture.json",
        "attente": "Writing opens at the Age of the Civil Registry. This country has not reached it yet: no glyph has been written.",
        "maj_le": "Page updated automatically after issue no. {n} of {d}.",
        "menu": ["The paper", "Archive", "History", "The language", "My citizen", "The embassy", "Tourism", "The Temple", "Research", "The project", "RSS feed"],
        "mast": ("Unofficial daily of the Republic", "Writing"), "tag": "The only newspaper in Microcontrôland, written every evening by the gateway",
        "retour": "Read the latest issue", "mentions": "Legal notice", "rss": "feed-en.xml", "autre": ("fr", "Français", "feed.xml", "La Puce Libre (français)"),
    },
}

STYLE = """<style>
svg .fond{fill:var(--rule);opacity:.3}svg rect:not(.fond){fill:var(--ink)}
.soir{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px;border:1px solid var(--rule);background:var(--sheet);padding:16px;margin:12px 0}
@media (max-width:620px){.soir{grid-template-columns:repeat(3,minmax(0,1fr))}}
.soir figure,.abc figure,.var figure,.noms figure{margin:0;padding:0;border:0;background:none;box-shadow:none;display:grid;gap:3px;justify-items:center;min-width:0}
.soir svg{width:100%;max-width:90px;height:auto}
.abc{display:grid;grid-template-columns:repeat(auto-fill,minmax(92px,1fr));gap:14px;margin:8px 0 18px}
.abc svg{width:56px;height:56px}
.var{display:grid;gap:14px;margin:8px 0 18px}.var .ligne{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:8px;align-items:start;border-top:1px solid var(--rule);padding-top:8px}
.var .ligne .sens{grid-column:1/-1;font-style:italic}
@media (max-width:620px){.var .ligne{grid-template-columns:repeat(3,minmax(0,1fr))}}
.var svg{width:40px;height:40px}
.noms{display:flex;flex-wrap:wrap;gap:18px;margin:8px 0 18px}.noms svg{height:64px;width:auto;max-width:100%}
figcaption{font:11.5px/1.35 var(--f-data);color:var(--muted);text-align:center;overflow-wrap:normal;hyphens:auto}
figcaption b{color:var(--ink);font-weight:600}
.compte{font:13px var(--f-data);color:var(--muted)}
pre.glyphe{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
</style>"""


def fig(rangs, haut, bas, cls="mini"):
    return (f'<figure>{svg(rangs, cls, haut)}<pre class="glyphe">{e(texte(rangs))}</pre>'
            f'<figcaption><b>{e(haut)}</b>{"<br>" + e(bas) if bas else ""}</figcaption></figure>')


def page(jours, latest, galerie, lg):
    T = L[lg]
    pre = "../" if lg == "en" else ""
    autre_lg, autre_nom, autre_rss, autre_titre = T["autre"]
    fr_url, en_url = BASE + "ecriture.html", BASE + "en/ecriture.html"
    liens = ["./", "archives.html", "histoire.html", "langue.html", "citoyen.html", "ambassade.html", "tourisme.html", "temple.html", "recherche.html", "projet.html", pre + T["rss"]]
    nav = "\n".join(f'    <a href="{h}">{e(t)}</a>' for h, t in zip(liens, T["menu"]))
    rg = (lambda r: REGION_EN.get(r, r)) if lg == "en" else (lambda r: r)
    sens = (lambda j, c: j["sens"][c][1 if lg == "en" else 0])
    corps = []
    if not jours:
        corps.append(f'<p>{e(T["attente"])}</p>')
    else:
        # Soir muet (tous les lexiques à null, ex. 10/11/2026, passerelle revenue en 0.9) : on montre le dernier soir reçu,
        # sinon l'abécédaire tomberait à 0 glyphe. ecriture.json garde le soir muet tel quel (jamais réécrit).
        parlants = [j for j in jours if any(any(m for m in (l or [])) for l in (j.get("mots") or {}).values())]
        a = parlants[-1] if parlants else jours[-1]
        if a is not jours[-1]:
            corps.append(f'<p class="compte"><i>{e(T["soir_muet"].format(d=date_longue(jours[-1]["date"], lg), r=date_longue(a["date"], lg)))}</i></p>')
        ere = a.get("ere")
        de_l_ere = [j for j in jours if j.get("ere") == ere]
        d = date_longue(a["date"], lg)
        # le mot du soir
        s = a.get("soir")
        if s and str(s["idee"]) in a["sens"]:
            figs = "".join(fig(glyphe(m[0], m[1]), m[2], rg(REGIONS[r])) if m else f'<figure><figcaption>{e(rg(REGIONS[r]))}<br>{e(T["muette"])}</figcaption></figure>'
                           for r, m in enumerate(s["mots"]))
            gs = [glyphe(m[0], m[1]) for m in s["mots"] if m]
            n = max((gs.count(g) for g in set(gs)), default=0)
            fr_, en_ = a["sens"][str(s["idee"])]
            corps.append(f'<h2>{e(T["soir"])}</h2><p class="compte">{e(T["soir_sous"].format(h=s.get("heure"), fr=fr_, en=en_))}</p>'
                         f'<div class="soir">{figs}</div><p class="compte">{e(T["soir_accord"].format(n=n) if n >= SEUIL else T["soir_seul"])}</p>')
        # l'abécédaire : premier jour commun de chaque idée
        premier = {}
        for j in de_l_ere:
            for c, ligne in j["mots"].items():
                g = commun(ligne)
                if g and c not in premier:
                    premier[c] = j["date"]
        actuels = [(c, commun(l)) for c, l in a["mots"].items()]
        actuels = [(c, g) for c, g in actuels if g]
        actuels.sort(key=lambda t: (premier.get(t[0], a["date"]), int(t[0])))
        ecrit = {c: next(m[2] for m in a["mots"][c] if m and glyphe(m[0], m[1]) == g) for c, g in actuels}
        ouverture = de_l_ere[0]["date"]

        def quand(c):
            p = premier.get(c, a["date"])
            return "" if p == ouverture else " · " + T["depuis"].format(d=p[8:].lstrip("0") + "/" + p[5:7].lstrip("0"))
        figs = "".join(fig(g, ecrit[c], sens(a, c) + quand(c)) for c, g in actuels)
        corps.append(f'<h2>{e(T["abc"].format(ere=ere))}</h2>'
                     f'<p class="compte">{e(T["abc_sous"].format(n=len(actuels), d=d, o=date_longue(de_l_ere[0]["date"], lg)))}</p><div class="abc">{figs}</div>')
        # les écritures régionales
        lignes = []
        for c, l in sorted(a["mots"].items(), key=lambda t: int(t[0])):
            if commun(l):
                continue
            cel = "".join(fig(glyphe(m[0], m[1]), m[2], rg(REGIONS[r])) if m else f'<figure><figcaption>{e(rg(REGIONS[r]))}<br>{e(T["muette"])}</figcaption></figure>' for r, m in enumerate(l))
            lignes.append(f'<div class="ligne"><span class="sens">{e(sens(a, c))}</span>{cel}</div>')
        if lignes:
            corps.append(f'<h2>{e(T["var"])}</h2><p class="compte">{e(T["var_sous"].format(d=d))}</p><div class="var">{"".join(lignes)}</div>')
        # les noms
        sons = a.get("sons")
        mandats = [m for m in (galerie or {}).get("mandats") or [] if (galerie or {}).get("ere") == ere]
        figs = []
        if sons:
            for m in mandats:
                syl = syllabes_du_nom(m.get("nom", ""), sons["consonnes"], sons["voyelles"], sons["codas"])
                if not syl:
                    continue
                deb = date_longue((m.get("debut") or {}).get("date"), lg)
                fin = (m.get("fin") or {}).get("date")
                bas = T["pres"].format(a=deb, b=date_longue(fin, lg)) if fin else T["pres_en_cours"].format(a=deb)
                figs.append(fig(cartouche(syl), m["nom"], f'{rg(m.get("region", ""))} · {bas}', "nom"))
        if figs:
            corps.append(f'<h2>{e(T["noms"])}</h2><p class="compte">{e(T["noms_sous"])}</p><div class="noms">{"".join(figs)}</div>')
        brut = f'<a href="{DONNEES}donnees/ere-{int(ere or 1):03d}/quotidien/{e(a["date"])}.json">{e(T["brut"])}</a>'
        lien_arch = f'<a href="{pre}ecriture.json">{e(T["arch"])}</a>'
        corps.append(f'<h2>{e(T["lire"])}</h2><p>{e(T["regle"])}</p><p>{e(T["regle_nom"])}</p>'
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
<link rel="alternate" type="application/json" href="{pre}ecriture.json">
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
    <p><small>{e(maj)}</small></p>
  </div>

  <footer class="site">
    <span><a href="./">{e(T["retour"])}</a></span>
    <span><a href="{'en/' if lg == 'fr' else '../'}ecriture.html">{e(autre_nom)}</a></span>
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
    """Ajoute à ecriture.json les jours publiés qui n'y sont pas encore. Renvoie le nombre de jours ajoutés."""
    chemin = racine / "ecriture.json"
    vide = {"format": 1, "regle": REGLE, "jours": []}
    arch = lire(chemin, vide) if chemin.exists() else vide
    jours = arch["jours"]
    deja = {(j.get("ere"), j.get("date")) for j in jours}
    latest = lire(racine / "data" / "latest.json", {})
    galerie = lire(racine / "galerie.json", {}) if (racine / "galerie.json").exists() else {}
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
            break   # on n'écrit jamais un jour avant le précédent
        if f.get("sha256") and hashlib.sha256(octets).hexdigest() != f["sha256"]:
            print(f"Empreinte différente du manifeste : {f['fichier']} ignoré", file=sys.stderr)
            break
        brut = json.loads(octets)
        if int(brut.get("format") or 0) < 3 or "lexiques" not in brut:
            continue   # avant la 0.8 : aucun lexique publié
        ent = jour_du_brut(brut)
        if ent is None:
            continue   # avant l'État civil : pas d'écriture
        ent["source"] = f["fichier"]
        jours.append(ent)
        deja.add((ere, f.get("date")))
        ajoutes += 1
    if ajoutes:
        chemin.write_text(json.dumps(arch, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    (racine / "ecriture.html").write_text(page(jours, latest, galerie, "fr"), encoding="utf-8")
    (racine / "en").mkdir(exist_ok=True)
    (racine / "en" / "ecriture.html").write_text(page(jours, latest, galerie, "en"), encoding="utf-8")
    print(f"ecriture : {ajoutes} jour(s) ajouté(s), {len(jours)} au total")
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
