"""Microcontrôland : rubrique « Contre-enquête » (FR) et « Counter-investigation » (EN).

Deux parties, sur une seule page :
- les dossiers (contre-enquete/dossiers.json), rédigés par Claude en journaliste indépendant et validés par Bran
  avant publication ; seuls les dossiers datés (« publie ») paraissent ;
- le carnet de l'enquêteur : une fiche factuelle par élection, révolte, coup de palais ou vacance du pouvoir,
  recalculée chaque soir à partir des fichiers bruts publiés du dépôt microcontroland-data (voix par région,
  abstentions, rebelles et censurés à l'heure de l'événement). Aucune donnée n'est complétée ni inventée :
  un jour reconstitué ne donne que le texte publié.

Le journal publié n'est jamais retouché : la rubrique est une page à part (passerelle « sourire, comprendre,
vérifier »). Ouverture à l'âge de la Mémoire (ages.etapes[2] de data/latest.json), comme la Galerie.
Validé par Bran le 30 octobre 2026. Licence MIT. Version 1.0, 3 novembre 2026 (firmware 0.9).

  python3 .github/contre_enquete.py <racine du site> [--source URL_OU_DOSSIER] [--attendre SECONDES]
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import galerie as G  # lecture des fichiers publiés, dates, menu : mêmes règles que la Galerie des présidents

REGIONS, REGION_EN, DONNEES, BASE = G.REGIONS, G.REGION_EN, G.DONNEES, G.BASE
GENRES = {"e": ("Élection", "Election"), "c": ("Révolte", "Revolt"), "k": ("Coup de palais", "Palace coup"),
          "v": ("Vacance du pouvoir", "Power vacuum")}
e = G.e


# ---------------------------------------------------------------- le carnet : une fiche par événement politique

def genre_de(ev):
    k = ev.get("type")
    if k:
        return k if k in GENRES else None
    fr = ((ev.get("texte") or {}).get("fr")) or ""   # jour reconstitué : seul le texte publié existe
    for k, mot in (("e", "Élection"), ("c", "Révolte"), ("k", "Coup de palais")):
        if fr.startswith(mot):
            return k
    return None


def region_de(r, lg):
    return REGION_EN.get(REGIONS[r], REGIONS[r]) if lg == "en" else REGIONS[r]


def contexte(brut, tick):
    """Rebelles et censurés par région à l'heure de l'événement (relevé horaire), ou None."""
    if tick is None:
        return None
    h = next((x for x in brut.get("heures") or [] if x.get("tick") == tick), None)
    if not h:
        return None
    regs = h.get("regions") or []
    out = {"utc": h.get("utc"), "rebelles": [], "censures": []}
    for r in range(len(REGIONS)):
        x = regs[r] if r < len(regs) else None
        out["rebelles"].append(x.get("rebelles") if x else None)
        out["censures"].append(x.get("censures") if x else None)
    return out


def scrutin(brut, heure):
    el = brut.get("election")
    if not el or el.get("heure") != heure:
        return None
    cands = el.get("candidats") or []
    par_region = []
    for r, x in enumerate(el.get("regions") or []):
        if not x:
            par_region.append(None)
            continue
        v = x.get("voix") or []
        m = max(v) if v else 0
        tete = [cands[j]["id"] for j, n in enumerate(v) if m > 0 and n == m and j < len(cands)]   # ex aequo : tous
        par_region.append({"voix": v, "abstentions": x.get("abstentions"), "blancs": x.get("blancs"), "enTete": tete})
    return {k: el.get(k) for k in ("inscrits", "exprimes", "abstentions", "blancs", "abstentionPermise", "blancPermis")} | {
        "candidats": cands, "regions": par_region}


def fiches(jours):
    out = []
    for brut in jours:
        for ev in brut.get("evenements") or []:
            k = genre_de(ev)
            if not k:
                continue
            d, h = G.quand(brut["date"], ev.get("heure"))
            f = {"id": f"{d}-{h:02d}-{k}" if h is not None else f"{d}-{k}", "genre": k, "date": d, "heure": h,
                 "tick": ev.get("tick"), "texte": ev.get("texte"), "fichier": brut["_fichier"],
                 "reconstitue": bool(brut.get("reconstitue"))}
            ctx = contexte(brut, ev.get("tick"))
            if ctx:
                f["contexte"] = ctx
            if k == "e":
                s = scrutin(brut, ev.get("heure"))
                if s:
                    f["scrutin"] = s
            out.append(f)
    return out


# ---------------------------------------------------------------- textes

L = {
    "fr": {
        "titre": "Contre-enquête", "haut": "La rubrique qui vérifie le journal · ère {ere}",
        "chapo": "Le journal raconte ; ici, on vérifie. Pour les événements qui en valent la peine, notre enquêteur reprend "
                 "l'histoire à partir des seuls faits publiés : les éditions, les fichiers bruts et les règles du monde. "
                 "Le journal, lui, n'est jamais retouché.",
        "dossiers": "Les dossiers", "dossier_n": "Dossier n° {n}", "evt": "Événement du {d}", "verdict": "Verdict de l'enquêteur",
        "sources": "Vérifier par vous-même (changement de registre : données brutes)", "rectif": "Rectificatif",
        "aucun_dossier": "Le premier dossier est sous presse.",
        "carnet": "Le carnet de l'enquêteur",
        "carnet_chapo": "Une fiche par élection, révolte, coup de palais ou vacance du pouvoir, recalculée chaque soir à partir des "
                        "fichiers bruts publiés. Les chiffres, rien que les chiffres : l'humour est réservé aux dossiers.",
        "aucune_fiche": "Aucun événement politique publié pour l'instant.",
        "reconst": "Jour reconstitué à partir de l'édition publiée : pas de relevé horaire ni de détail du scrutin.",
        "inscrits": "{i} inscrits, {x} suffrages exprimés, {a} abstentions, {b} votes blancs.", "blancs_txt": "{b} votes blancs", "blancs_non": "vote blanc pas encore permis", "fiche_de": "Fiche du carnet",
        "cand": "Candidats", "voix": "{v} voix ({p} %)", "par_region": "En tête par région",
        "non_comptee": "non comptée", "ex": " et ", "heure_ctx": "À l'heure de l'événement",
        "reb": "rebelles", "cen": "réduits au silence cette heure-là", "dossier_lie": "Lire le dossier",
        "fiche_brut": "fichier brut", "ferme": "La rubrique ouvrira à l'âge de la Mémoire. Notre enquêteur attend que le pays ait des souvenirs.",
        "desc": "Contre-enquête : comment les événements de Microcontrôland sont vraiment arrivés, d'après les données publiées.",
        "pied": "Les dossiers sont rédigés par Claude (une IA), journaliste indépendant de la rubrique, et relus par Bran Brière avant publication. "
                "Ils ne prêtent aucune pensée aux Waïnas : un cerveau de 81 connexions calcule, il ne veut rien.",
        "maj_le": "Carnet recalculé après l'édition n° {n} du {d}.",
        "json": "toutes les fiches (JSON)", "h": lambda h: f"{h} h", "pct": " %",
        "sommaire": "Sommaire : {n} dossiers", "sommaire1": "Sommaire : 1 dossier", "vers_carnet": "Le carnet de l'enquêteur ({n} fiches)",
        "retour_sommaire": "Retour au sommaire",
    },
    "en": {
        "titre": "Counter-investigation", "haut": "The column that checks the paper · era {ere}",
        "chapo": "The paper tells the story; here we check it. For the events worth it, our investigator retraces the story "
                 "from published facts only: the issues, the raw files and the rules of the world. The paper itself is never edited.",
        "dossiers": "The files", "dossier_n": "File no. {n}", "evt": "Event of {d}", "verdict": "The investigator's verdict",
        "sources": "Check for yourself (change of register: raw data)", "rectif": "Correction",
        "aucun_dossier": "The first file is in press.",
        "carnet": "The investigator's notebook",
        "carnet_chapo": "One card per election, revolt, palace coup or power vacuum, recomputed every evening from the published raw "
                        "files. Figures, nothing but figures: the jokes are kept for the files.",
        "aucune_fiche": "No political event published yet.",
        "reconst": "Day rebuilt from the published issue: no hourly record and no vote details.",
        "inscrits": "{i} registered, {x} valid votes, {a} abstentions, {b} blank votes.", "blancs_txt": "{b} blank votes", "blancs_non": "blank votes not yet allowed", "fiche_de": "Notebook card",
        "cand": "Candidates", "voix": "{v} votes ({p}%)", "par_region": "Leading in each region",
        "non_comptee": "not counted", "ex": " and ", "heure_ctx": "At the time of the event",
        "reb": "rebels", "cen": "silenced that hour", "dossier_lie": "Read the file",
        "fiche_brut": "raw file", "ferme": "The column opens at the Age of Memory. Our investigator is waiting for the country to have memories.",
        "desc": "Counter-investigation: how Microcontrôland's events really happened, according to the published data.",
        "pied": "The files are written by Claude (an AI), the column's independent journalist, and read by Bran Brière before publication. "
                "They attribute no thoughts to the Waïnas: an 81-connection brain computes, it wants nothing.",
        "maj_le": "Notebook recomputed after issue no. {n} of {d}.",
        "sommaire": "Contents: {n} files", "sommaire1": "Contents: 1 file", "vers_carnet": "The investigator's notebook ({n} cards)",
        "retour_sommaire": "Back to contents",
        "json": "all cards (JSON)", "h": lambda h: (f"{h % 12 or 12} {'am' if h < 12 else 'pm'}" if h not in (0, 12) else ("midnight" if h == 0 else "noon")), "pct": "%",
    },
}

STYLE = """<style>
.dossier{border-top:3px double var(--rule);margin:26px 0 8px;padding-top:12px}
.dossier .no{font:600 12px var(--f-data);letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.dossier h2{margin:.2em 0 .3em}
.dossier .accroche{font-size:1.08em;font-style:italic}
.dossier h3{font-size:1em;margin:1.1em 0 .3em;text-transform:uppercase;letter-spacing:.04em}
.verdict{border-left:4px solid var(--ink);padding:6px 12px;margin:14px 0;background:var(--sheet)}
.verdict b{display:block;font:600 12px var(--f-data);text-transform:uppercase;letter-spacing:.06em;margin-bottom:2px}
.sig{font:12.5px/1.5 var(--f-data);color:var(--muted)}
.sommaire{border:1px solid var(--rule);background:var(--sheet);padding:8px 12px;margin:14px 0}
.sommaire summary{cursor:pointer;font:600 13px/1.5 var(--f-data);text-transform:uppercase;letter-spacing:.05em}
.sommaire ol{list-style:none;margin:8px 0 2px;padding:0}
.sommaire li{padding:5px 0;border-top:1px solid var(--rule)}
.sommaire li span{display:block;font:12px var(--f-data);color:var(--muted)}
.retour{font:12.5px var(--f-data)}
.carnet details{border:1px solid var(--rule);background:var(--sheet);padding:6px 10px;margin:6px 0}
.carnet summary{cursor:pointer;font:13px/1.5 var(--f-data)}
.carnet table{border-collapse:collapse;font:12.5px/1.45 var(--f-data);margin:6px 0;width:100%}
.carnet td,.carnet th{border-bottom:1px solid var(--rule);padding:2px 6px;text-align:left}
.carnet .muted{color:var(--muted);font:12.5px var(--f-data)}
</style>"""


def quand_txt(d, h, lg):
    t = G.date_longue(d, lg)
    return t + (f", {L[lg]['h'](h)}" if h is not None else "")


def html_dossier(d, lg, T, fiche_ids):
    t = lambda x: (x or {}).get(lg) or ""
    parts = [f'<article class="dossier" id="{e(d["id"])}">',
             f'<p class="no">{e(T["dossier_n"].format(n=d["numero"]))} · {e(T["evt"].format(d=G.date_longue(d["evenement"], lg)))}</p>',
             f'<h2>{e(t(d["titre"]))}</h2>', f'<p class="accroche">{e(t(d["accroche"]))}</p>']
    for s in d.get("sections") or []:
        parts.append(f'<h3>{e(t(s["titre"]))}</h3>')
        parts += [f"<p>{e(t(p))}</p>" for p in s.get("paragraphes") or []]
        if s.get("liste"):
            parts.append("<ul>" + "".join(f"<li>{e(t(x))}</li>" for x in s["liste"]) + "</ul>")
    parts.append(f'<div class="verdict"><b>{e(T["verdict"])}</b>{e(t(d["verdict"]))}</div>')
    liens = [f'<a href="{e(x["url"])}">{e(t(x))}</a>' for x in d.get("sources") or []]
    liens += [f'<a href="#{e(f["id"])}">{e(T["fiche_de"])} : {e(quand_txt(f["date"], f["heure"], lg))}</a>' for f in fiche_ids]
    parts.append(f'<p class="sig"><b>{e(T["sources"])}</b><br>' + "<br>".join(liens) + "</p>")
    for r in d.get("rectificatifs") or []:
        parts.append(f'<p class="sig"><b>{e(T["rectif"])} ({e(G.date_longue(r.get("date", ""), lg))})</b> {e(t(r))}</p>')
    parts.append(f'<p class="retour"><a href="#sommaire">↑ {e(T["retour_sommaire"])}</a></p></article>')
    return "".join(parts)


def html_sommaire(dossiers, fs, lg, T):
    """Sommaire déroulant sans JavaScript (<details>) : grandit tout seul avec dossiers.json, le plus récent en haut."""
    t = lambda x: (x or {}).get(lg) or ""
    n = len(dossiers)
    tete = T["sommaire1"] if n == 1 else T["sommaire"].format(n=n)
    items = "".join(f'<li><a href="#{e(d["id"])}">{e(t(d["titre"]))}</a>'
                    f'<span>{e(T["dossier_n"].format(n=d["numero"]))} · {e(T["evt"].format(d=G.date_longue(d["evenement"], lg)))}</span></li>'
                    for d in sorted(dossiers, key=lambda d: -d["numero"]))
    items += f'<li><a href="#carnet">{e(T["vers_carnet"].format(n=len(fs)))}</a></li>'
    return f'<details class="sommaire" id="sommaire"><summary>{e(tete)}</summary><ol>{items}</ol></details>'


def html_fiche(f, lg, T, dossier_par_date):
    t = lambda x: (x or {}).get(lg) or ""
    pct = T["pct"]
    tete = f'{quand_txt(f["date"], f["heure"], lg)} · {t(f["texte"])}'
    corps = []
    if f["reconstitue"]:
        corps.append(f'<p class="muted">{e(T["reconst"])}</p>')
    s = f.get("scrutin")
    if s:
        regle = T["inscrits"].format(i=s["inscrits"], x=s["exprimes"], a=s["abstentions"], b=s["blancs"])
        if not s.get("blancPermis"):
            regle = regle.replace(T["blancs_txt"].format(b=s["blancs"]), T["blancs_non"])
        corps.append(f'<p>{e(regle)}</p>')
        noms = {c["id"]: c["nom"] for c in s["candidats"]}
        lignes = "".join(f'<tr><td>{e(c["nom"])}</td><td>{e(region_de(REGIONS.index(c["region"]), lg) if c.get("region") in REGIONS else c.get("region"))}</td>'
                         f'<td>{e(T["voix"].format(v=c["voix"], p=c["pct"]).replace(" %", pct))}</td></tr>' for c in sorted(s["candidats"], key=lambda c: -c["voix"]))
        corps.append(f'<table><tr><th colspan="3">{e(T["cand"])}</th></tr>{lignes}</table>')
        reg = [f'{region_de(r, lg)} : {T["ex"].join(noms.get(i, "?") for i in x["enTete"]) or "—"}' if x else f'{region_de(r, lg)} : {T["non_comptee"]}'
               for r, x in enumerate(s["regions"])]
        corps.append(f'<p class="muted">{e(T["par_region"])} : {e(" · ".join(reg))}</p>')
    c = f.get("contexte")
    if c:
        def ligne(v, mot):
            tot = sum(x for x in v if x is not None)
            det = " · ".join(f'{region_de(r, lg)} {x if x is not None else "?"}' for r, x in enumerate(v))
            return f"{tot} {mot} ({det})"
        corps.append(f'<p class="muted">{e(T["heure_ctx"])} : {e(ligne(c["rebelles"], T["reb"]))} ; {e(ligne(c["censures"], T["cen"]))}.</p>')
    liens = [f'<a href="{DONNEES}{e(f["fichier"])}">{e(T["fiche_brut"])}</a>']
    d = dossier_par_date.get(f["date"])
    if d:
        liens.append(f'<a href="#{e(d["id"])}">{e(T["dossier_lie"])} : {e(t(d["titre"]))}</a>')
    corps.append(f'<p class="muted">{" · ".join(liens)}</p>')
    return f'<details id="{e(f["id"])}"><summary>{e(tete)}</summary>{"".join(corps)}</details>'


def page(dossiers, signature, fs, latest, lg, ouvert, ere):
    T, Tg = L[lg], G.L[lg]
    pre = "../" if lg == "en" else ""
    autre_lg, autre_nom, autre_rss, autre_titre = Tg["autre"]
    fr_url, en_url = BASE + "contre-enquete.html", BASE + "en/contre-enquete.html"
    liens = ["./", "archives.html", "histoire.html", "langue.html", "citoyen.html", "ambassade.html", "tourisme.html", "temple.html", "recherche.html", "projet.html", pre + Tg["rss"]]
    nav = "\n".join(f'    <a href="{h}">{e(t)}</a>' for h, t in zip(liens, Tg["menu"]))
    corps = []
    if not ouvert:
        corps.append(f'<p>{e(T["ferme"])}</p>')
    else:
        par_date = {d["evenement"]: d for d in dossiers}
        corps.append(f'<h2>{e(T["dossiers"])}</h2>')
        corps.append(f'<p class="sig">{e(signature.get(lg, ""))}</p>')
        if dossiers:
            corps.append(html_sommaire(dossiers, fs, lg, T))
            for d in dossiers:
                ids = [f for f in fs if f["date"] == d["evenement"]]
                corps.append(html_dossier(d, lg, T, ids))
        else:
            corps.append(f'<p>{e(T["aucun_dossier"])}</p>')
        corps.append(f'<section class="carnet" id="carnet"><h2>{e(T["carnet"])}</h2><p>{e(T["carnet_chapo"])}</p>')
        corps.append("".join(html_fiche(f, lg, T, par_date) for f in reversed(fs)) or f'<p>{e(T["aucune_fiche"])}</p>')
        corps.append(f'<p class="muted"><a href="{pre}contre-enquete.json">{e(T["json"])}</a></p></section>')
    maj = T["maj_le"].format(n=latest.get("day", "?"), d=G.date_longue(str(latest.get("date", "")), lg))
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
<link rel="alternate" type="application/rss+xml" title="La Puce Libre" href="{pre}{Tg["rss"]}">
<link rel="alternate" type="application/rss+xml" title="{e(autre_titre)}" hreflang="{autre_lg}" href="{pre}{autre_rss}">
<link rel="alternate" type="application/json" href="{pre}contre-enquete.json">
<link rel="alternate" type="text/plain" href="{pre}contre-enquete.txt">
<link rel="stylesheet" href="{pre}style.css">
<script src="{pre}mesure.js" defer></script>
{STYLE}
</head>
<body>
<div class="wrap">
  <header class="mast">
    <div class="top"><span>{e(Tg["mast"][0])}</span><span>{e(T["titre"])}</span></div>
    <div class="title"><a href="./">La Puce <span>Libre</span></a></div>
    <p class="tag">{e(Tg["tag"])}</p>
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
    <span><a href="./">{e(Tg["retour"])}</a></span>
    <span><a href="{'en/' if lg == 'fr' else '../'}contre-enquete.html">{e(autre_nom)}</a></span>
    <span><a href="mentions.html">{e(Tg["mentions"])}</a></span>
  </footer>
</div>
{'<script>window.MCL_BASE = "../";</script>' if lg == "en" else ""}
<script src="{pre}reglages.js"></script>
<script src="{pre}commun.js"></script>
<script src="{pre}lang.js"></script>
</body>
</html>
"""


def texte(dossiers, signature, fs, lg, ouvert):
    """Version texte brut pour les lecteurs sans JavaScript et les IA (mêmes mots que la page)."""
    T = L[lg]
    t = lambda x: (x or {}).get(lg) or ""
    out = [T["titre"].upper(), "", T["chapo"], ""]
    if not ouvert:
        return "\n".join(out + [T["ferme"], ""])
    out += [signature.get(lg, ""), ""]
    if dossiers:
        n = len(dossiers)
        out.append((T["sommaire1"] if n == 1 else T["sommaire"].format(n=n)).upper())
        out += [f'- {T["dossier_n"].format(n=d["numero"])} · {G.date_longue(d["evenement"], lg)} · {t(d["titre"])}'
                for d in sorted(dossiers, key=lambda d: -d["numero"])]
        out.append("")
    for d in dossiers:
        out += ["=" * 60, T["dossier_n"].format(n=d["numero"]) + " · " + T["evt"].format(d=G.date_longue(d["evenement"], lg)),
                t(d["titre"]), "", t(d["accroche"]), ""]
        for s in d.get("sections") or []:
            out.append("## " + t(s["titre"]))
            out += [t(p) for p in s.get("paragraphes") or []]
            out += ["- " + t(x) for x in s.get("liste") or []]
            out.append("")
        out += [T["verdict"] + " : " + t(d["verdict"]), ""]
        out += [f'- {t(x)} : {x["url"]}' for x in d.get("sources") or []]
        out.append("")
    out += ["=" * 60, T["carnet"], T["carnet_chapo"], ""]
    for f in reversed(fs):
        out.append(f'- {quand_txt(f["date"], f["heure"], lg)} · {t(f["texte"])} ({DONNEES}{f["fichier"]})')
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- programme

def mettre_a_jour(racine, source, attendre=0):
    latest = G.lire(racine / "data" / "latest.json", {})
    ere = int(latest.get("ere") or 1)
    etapes = (latest.get("ages") or {}).get("etapes") or []
    ouvert = len(etapes) > G.MEMOIRE and bool(etapes[G.MEMOIRE].get("ouvert"))
    fin = time.time() + attendre
    while attendre and time.time() < fin:
        dates = {f.get("date") for f in G.manifeste(source, f"donnees/ere-{ere:03d}/manifeste.json")}
        if latest.get("date") in dates:
            break
        print("Fichier brut du soir pas encore publié : nouvel essai dans 60 s")
        time.sleep(60)
    src = G.lire(racine / "contre-enquete" / "dossiers.json", {})
    dossiers = sorted((d for d in src.get("dossiers") or [] if d.get("publie")), key=lambda d: d["numero"])
    signature = src.get("signature") or {}
    fs = fiches(G.jours_publies(source, ere)) if ouvert else []
    sortie = {"format": 1, "ere": ere, "ouvert": ouvert,
              "note": "Fiches recalculées chaque soir depuis les fichiers bruts publiés ; dossiers rédigés à la main (contre-enquete/dossiers.json).",
              "dossiers": dossiers if ouvert else [], "fiches": fs}
    (racine / "contre-enquete.json").write_text(json.dumps(sortie, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    (racine / "en").mkdir(exist_ok=True)
    for lg, pre in (("fr", racine), ("en", racine / "en")):
        (pre / "contre-enquete.html").write_text(page(dossiers, signature, fs, latest, lg, ouvert, ere), encoding="utf-8")
        (pre / "contre-enquete.txt").write_text(texte(dossiers, signature, fs, lg, ouvert), encoding="utf-8")
    print(f"contre-enquête : {'ouverte' if ouvert else 'fermée'}, {len(dossiers)} dossier(s) publié(s), {len(fs)} fiche(s)")


def main():
    args = sys.argv[1:]
    racine = Path(args[0] if args and not args[0].startswith("--") else ".")
    source = args[args.index("--source") + 1] if "--source" in args else G.SOURCE
    attendre = int(args[args.index("--attendre") + 1]) if "--attendre" in args else 0
    if not source.startswith("http") and not source.endswith("/"):
        source += "/"
    mettre_a_jour(racine, source, attendre)


if __name__ == "__main__":
    main()
