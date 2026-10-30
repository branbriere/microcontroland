"""Microcontrôland : page « La République en chantier » (FR) et « Republic Under Construction » (EN).

Lit institutions.json (registre tenu à la main à chaque mise à jour) et les données publiées
par la passerelle (data/latest.json, data/langue.json, data/editions/N.json), puis écrit :
  chantiers.html       version française
  en/chantiers.html    version anglaise

Aucun mot n'est ajouté au journal et la passerelle ne change pas. Un édifice « fermé » passe seul
« en service » le soir où le pays atteint son âge. Inauguration = date d'ouverture et président en
fonction ce jour-là, lus dans les éditions. Discours = uniquement des mots communs réels du pays.
Le mot de l'Ambassade reste « en attente d'évolution de la civilisation » tant que la Diplomatie
n'est pas atteinte. Aucune date n'est promise pour ce qui est prévu.

Licence MIT. Version 1.0, 26 octobre 2026 (firmware 0.8).
"""
import html
import json
import sys
from pathlib import Path

BASE = "https://www.microcontroland.org/"
AGES = {"fr": ["la Fondation", "la Parole", "la Mémoire", "l'État civil", "la Diplomatie", "la Curiosité"],
        "en": ["the Founding", "Speech", "Memory", "the Civil Registry", "Diplomacy", "Curiosity"]}
DIPLOMATIE = 4
MOIS = {"fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"],
        "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]}
REGION_EN = {"Mines": "Mines", "Champs": "Fields", "Raffineries": "Refineries", "Barrage": "Dam", "Port": "Harbour", "Ville": "City"}
GROUPES = ("service", "ferme", "prevu", "reserve")

L = {
    "fr": {
        "titre": "La République en chantier", "haut": "Ministère des Grands Travaux · registre public",
        "chapo": "Ce que Microcontrôland possède déjà, ce qui est construit mais pas encore ouvert, et ce qui figure sur les plans. "
                 "Chaque édifice correspond à un vrai mécanisme du programme, ou à une mise à jour réellement prévue. "
                 "Aucune date n'est promise : un chantier ouvre quand le pays atteint l'âge requis.",
        "desc": "Registre public des institutions de Microcontrôland : en service, construites mais fermées, prévues, en réserve.",
        "groupes": {"service": ("En service", "vérifié dans le programme installé et les données publiées"),
                    "ferme": ("Construit, pas encore ouvert", "le code existe ; il attend son âge"),
                    "prevu": ("Sur les plans", "prévu, rien n'est encore codé ; l'ordre peut changer"),
                    "reserve": ("En réserve", "seulement si le pays est stable")},
        "tampon": {"service": "En service", "ferme": "Fermé", "prevu": "Prévu", "reserve": "Réserve"},
        "compte": {"service": "en service", "ferme": "construits, fermés", "prevu": "prévus", "reserve": "en réserve"},
        "derniere": "Dernière inauguration", "ouverture": "Ouverture", "ruban": "Ruban", "discours": "Discours",
        "ambassade": "Ambassade", "en_fonction": "le président {p}, en fonction ce jour-là", "sans_pres": "aucun président en fonction ce jour-là",
        "discours_txt": "({g}). Le pays compte {n} mots communs ; le discours n'en utilise pas d'autres.",
        "silence": "Silence : le pays n'a pas encore de mot commun pour saluer.",
        "attente": "En attente d'évolution de la civilisation. L'Ambassade ouvre à l'âge de la Diplomatie.",
        "pas_de_mot": "L'Ambassade n'a pas encore commenté cet édifice.",
        "ouvert_le": "ouvert le {d}", "president": "président : {p}", "age": "ouvre à l'âge de {a}", "maj": "mise à jour {n}",
        "site": "sur ce site", "progres": "progrès : {p}", "verifier": "vérifier : {v}", "capitale": "capitale ce soir : {c}",
        "ministres": "ministres ce soir : {n}", "croyants": "condition : un tiers de croyants (ce soir : {n} %)",
        "pied1": "Les inaugurations sont une convention de cette page : on y inscrit la date d'ouverture et le président en fonction ce jour-là, "
                 "d'après les éditions publiées. Aucun Waïna n'a coupé de ruban, et le discours n'emploie que des mots réellement communs du pays.",
        "pied2": "Ce registre amuse ; il ne fait pas foi. La référence est l'{lien}, sur le site des données.",
        "lien": "état des fonctionnalités", "doc": "https://donnees.microcontroland.org/documentation/etat-fonctionnalites.md",
        "maj_le": "Page mise à jour automatiquement après l'édition n° {n} du {d}.",
        "menu": ["Le journal", "Archives", "Histoire", "La langue", "Mon citoyen", "L'ambassade", "Recherche", "Le projet", "Flux RSS"],
        "mast": ("Quotidien officieux de la République", "Le registre"), "tag": "Le seul journal de Microcontrôland, écrit chaque soir par la passerelle",
        "retour": "Lire la dernière édition", "mentions": "Mentions légales", "rss": "feed.xml", "autre": ("en", "English", "feed-en.xml", "La Puce Libre (English)"),
    },
    "en": {
        "titre": "Republic Under Construction", "haut": "Ministry of Public Works · public register",
        "chapo": "What Microcontrôland already has, what is built but not yet open, and what is still on the drawing board. "
                 "Every building matches a real mechanism in the program, or an update that is genuinely planned. "
                 "No date is promised: a site opens when the country reaches the required age.",
        "desc": "Public register of Microcontrôland's institutions: in service, built but closed, planned, held in reserve.",
        "groupes": {"service": ("In service", "checked in the installed program and the published data"),
                    "ferme": ("Built, not yet open", "the code exists; it waits for its age"),
                    "prevu": ("On the drawing board", "planned, nothing coded yet; the order may change"),
                    "reserve": ("Held in reserve", "only if the country is stable")},
        "tampon": {"service": "In service", "ferme": "Closed", "prevu": "Planned", "reserve": "Reserve"},
        "compte": {"service": "in service", "ferme": "built, closed", "prevu": "planned", "reserve": "in reserve"},
        "derniere": "Latest inauguration", "ouverture": "Opened", "ruban": "Ribbon", "discours": "Speech",
        "ambassade": "Embassy", "en_fonction": "President {p}, in office that day", "sans_pres": "no president in office that day",
        "discours_txt": "({g}). The country shares {n} words; the speech uses no others.",
        "silence": "Silence: the country has no shared word for a greeting yet.",
        "attente": "Awaiting the evolution of civilisation. The Embassy opens at the Age of Diplomacy.",
        "pas_de_mot": "The Embassy has not yet commented on this building.",
        "ouvert_le": "opened {d}", "president": "president: {p}", "age": "opens at {a}", "maj": "update {n}",
        "site": "on this website", "progres": "progress: {p}", "verifier": "check: {v}", "capitale": "capital tonight: {c}",
        "ministres": "ministers tonight: {n}", "croyants": "condition: a third of believers (tonight: {n}%)",
        "pied1": "Inaugurations are a convention of this page: it records the opening date and the president in office that day, "
                 "from the published issues. No Waïna has cut a ribbon, and the speech uses only words the country really shares.",
        "pied2": "This register is for fun; it is not the reference. The reference is the {lien} on the data site.",
        "lien": "feature status page", "doc": "https://donnees.microcontroland.org/documentation/etat-fonctionnalites.en.md",
        "maj_le": "Page updated automatically after issue no. {n} of {d}.",
        "menu": ["The paper", "Archive", "History", "The language", "My citizen", "The embassy", "Research", "The project", "RSS feed"],
        "mast": ("Unofficial daily of the Republic", "The register"), "tag": "The only newspaper in Microcontrôland, written every evening by the gateway",
        "retour": "Read the latest issue", "mentions": "Legal notice", "rss": "feed-en.xml", "autre": ("fr", "Français", "feed.xml", "La Puce Libre (français)"),
    },
}

STYLE = """<style>
.reg{list-style:none;margin:0;padding:0;border-top:2px solid var(--ink)}
.reg li{display:grid;grid-template-columns:1fr auto;gap:2px 14px;padding:10px 0;border-bottom:1px solid var(--rule)}
.reg .nom{font-weight:700}.reg .quoi{grid-column:1;color:var(--muted);min-width:0}
.reg .meta{grid-column:1;font:12.5px/1.5 var(--f-data);color:var(--muted);display:flex;flex-wrap:wrap;gap:2px 14px;min-width:0}
.tampon{grid-column:2;grid-row:1/span 3;align-self:start;font:700 11px var(--f-data);letter-spacing:.1em;text-transform:uppercase;padding:3px 7px;border:1.5px solid currentColor;transform:rotate(-2deg);white-space:nowrap}
.t-service{color:var(--up)}.t-ferme{color:var(--mask)}.t-prevu{color:var(--warn)}.t-reserve{color:var(--neutral)}
.plaque{border:1px solid var(--rule);background:var(--sheet);padding:14px 16px;margin:18px 0}
.plaque dl{display:grid;grid-template-columns:max-content 1fr;gap:4px 14px;margin:6px 0 0}.plaque dt{font:12px var(--f-data);text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
.plaque dd{margin:0;min-width:0}.compte{font:13px var(--f-data);color:var(--muted)}.mot{font-family:var(--f-data);font-weight:700}
@media (max-width:520px){.reg li{grid-template-columns:1fr}.tampon{grid-column:1;grid-row:auto;justify-self:start}}
</style>"""


def e(x):
    return html.escape(str(x), quote=True)


def lire(f, defaut):
    try:
        return json.loads(Path(f).read_text(encoding="utf-8"))
    except (ValueError, OSError) as err:
        print(f"Ignoré : {f} ({err})", file=sys.stderr)
        return defaut


def tr(v, lg):
    return str(v.get(lg) or "") if isinstance(v, dict) else (v if isinstance(v, str) else "")


def date_longue(iso, lg):
    try:
        a, m, j = (int(x) for x in iso.split("-"))
    except (ValueError, AttributeError):
        return iso or ""
    return f"{j}{'er' if j == 1 and lg == 'fr' else ''} {MOIS[lg][m - 1]} {a}" if lg == "fr" else f"{j} {MOIS[lg][m - 1]} {a}"


def reg(nom, lg):
    return REGION_EN.get(nom, nom) if lg == "en" else (nom or "")


def editions(racine):
    eds = []
    for f in (racine / "data" / "editions").glob("*.json"):
        d = lire(f, None)
        if isinstance(d, dict) and isinstance(d.get("day"), int):
            eds.append(d)
    return sorted(eds, key=lambda d: d["day"])


def ouverture_age(eds, k):
    """Première édition où l'âge k est ouvert : (date, président, capitale), ou None."""
    for d in eds:
        etapes = (d.get("ages") or {}).get("etapes") or []
        if len(etapes) > k and etapes[k].get("ouvert"):
            return d
    return None


def edition_du(eds, iso):
    for d in eds:
        if str(d.get("date")) == iso:
            return d
    return None


def president_de(ed, lg):
    if not ed or not ed.get("presidentNom"):
        return None
    cap = (ed.get("etat") or {}).get("capitale")
    return ed["presidentNom"] + (f" ({reg(cap, lg)})" if cap else "")


def discours(langue):
    """Salut + pays, seulement si ce sont des mots communs (accord ≥ 5 régions sur 6)."""
    mots = {tr(m.get("idee"), "fr"): m for m in (langue.get("mots") or []) if (m.get("accord") or 0) >= 5}
    pris = [mots[i] for i in ("salut", "pays") if i in mots]
    if not pris or pris[0] is not mots.get("salut"):
        return None
    return pris


def construire(reg_json, latest, langue, eds):
    """Calcule l'état réel de chaque édifice ce soir (un « fermé » dont l'âge est atteint passe en service)."""
    etapes = (latest.get("ages") or {}).get("etapes") or []
    sortie = []
    for it in reg_json.get("institutions", []):
        it = dict(it)
        if it["etat"] == "ferme":
            k = it.get("age", 0)
            if len(etapes) > k and etapes[k].get("ouvert"):
                ed = ouverture_age(eds, k)
                it["etat"], it["ouvre"] = "service", ed
            elif len(etapes) > k:
                it["progres"] = etapes[k].get("progres") or {}
        elif it["etat"] == "service" and it.get("depuis"):
            it["ouvre"] = edition_du(eds, it["depuis"]) or {"date": it["depuis"]}
        sortie.append(it)
    return sortie


def meta(it, latest, lg):
    T, m = L[lg], []
    ed = it.get("ouvre")
    if ed:
        m.append(T["ouvert_le"].format(d=date_longue(str(ed.get("date", "")), lg)))
        p = president_de(ed, lg)
        if p:
            m.append(T["president"].format(p=p))
    if it["etat"] != "service" and it.get("age"):
        m.append(T["age"].format(a=AGES[lg][it["age"]]))
    if it.get("maj"):
        m.append(T["maj"].format(n=it["maj"]))
    if it.get("site"):
        m.append(T["site"])
    et = latest.get("etat") or {}
    if it.get("dyn") == "capitale" and et.get("capitale"):
        m.append(T["capitale"].format(c=reg(et["capitale"], lg)))
    if it.get("dyn") == "ministres" and et.get("ministres") is not None:
        m.append(T["ministres"].format(n=et["ministres"]))
    if it.get("dyn") == "croyants" and (et.get("foi") or {}).get("croyants") is not None:
        m.append(T["croyants"].format(n=et["foi"]["croyants"]))
    if it.get("progres") and tr(it["progres"], lg):
        m.append(T["progres"].format(p=tr(it["progres"], lg)))
    if it.get("verifier"):
        m.append(T["verifier"].format(v=it["verifier"]))
    return "".join(f"<span>{e(x)}</span>" for x in m)


def plaque(items, latest, langue, lg):
    T = L[lg]
    ouverts = [it for it in items if it["etat"] == "service" and it.get("ouvre") and it["ouvre"].get("date")]
    if not ouverts:
        return ""
    it = max(ouverts, key=lambda x: (str(x["ouvre"]["date"]), x["ouvre"].get("day", 0)))
    ed = it["ouvre"]
    p = president_de(ed, lg)
    mots = discours(langue)
    if mots:
        txt = ", ".join(m["mot"] for m in mots)
        glose = ", ".join(tr(m.get("idee"), lg) for m in mots)
        q = ("« ", " ! »") if lg == "fr" else ("“", "!”")
        dis = f'<span class="mot">{q[0]}{e(txt)}{q[1]}</span> ' + e(T["discours_txt"].format(g=glose, n=langue.get("partages", "?")))
    else:
        dis = e(T["silence"])
    etapes = (latest.get("ages") or {}).get("etapes") or []
    diplo = len(etapes) > DIPLOMATIE and etapes[DIPLOMATIE].get("ouvert")
    amb = tr(it.get("ambassade"), lg) or T["pas_de_mot"] if diplo else T["attente"]
    jour = f", {'jour' if lg == 'fr' else 'day'} {ed['jourEre']}" if ed.get("jourEre") else ""
    return (f'<div class="plaque"><p class="compte">{e(T["derniere"])}</p><h2 style="margin:0;border:0;padding:0">{e(it[lg][0])}</h2><dl>'
            f'<dt>{e(T["ouverture"])}</dt><dd>{e(date_longue(str(ed["date"]), lg) + jour)}</dd>'
            f'<dt>{e(T["ruban"])}</dt><dd>{e(T["en_fonction"].format(p=p) if p else T["sans_pres"])}</dd>'
            f'<dt>{e(T["discours"])}</dt><dd>{dis}</dd>'
            f'<dt>{e(T["ambassade"])}</dt><dd><i>{e(amb)}</i></dd></dl></div>')


def page(items, latest, langue, lg):
    T = L[lg]
    pre = "../" if lg == "en" else ""
    autre_lg, autre_nom, autre_rss, autre_titre = T["autre"]
    fr_url, en_url = BASE + "chantiers.html", BASE + "en/chantiers.html"
    liens = ["./", "archives.html", "histoire.html", "langue.html", "citoyen.html", "ambassade.html", "recherche.html", "projet.html", pre + T["rss"]]
    nav = "\n".join(f'    <a href="{h}">{e(t)}</a>' for h, t in zip(liens, T["menu"]))
    compte = {g: sum(1 for it in items if it["etat"] == g) for g in GROUPES}
    corps = []
    for g in GROUPES:
        lis = []
        for it in items:
            if it["etat"] != g:
                continue
            lis.append(f'<li><span class="nom">{e(it[lg][0])}</span><span class="tampon t-{g}">{e(T["tampon"][g])}</span>'
                       f'<span class="quoi">{e(it[lg][1])}</span><span class="meta">{meta(it, latest, lg)}</span></li>')
        if lis:
            titre, sous = T["groupes"][g]
            corps.append(f'<h2>{e(titre)}</h2><p class="compte">{e(sous)}</p><ol class="reg">{"".join(lis)}</ol>')
    maj = T["maj_le"].format(n=latest.get("day", "?"), d=date_longue(str(latest.get("date", "")), lg))
    doc = f'<a href="{T["doc"]}">{e(T["lien"])}</a>'
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
<link rel="alternate" type="application/json" href="{pre}institutions.json">
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
    <p class="compte">{" · ".join(f"{compte[g]} {e(T['compte'][g])}" for g in GROUPES)}</p>
    {plaque(items, latest, langue, lg)}
    {"".join(corps)}
    <p><small>{e(T["pied1"])}</small></p>
    <p><small>{T["pied2"].format(lien=doc)}</small></p>
    <p><small>{e(maj)}</small></p>
  </div>

  <footer class="site">
    <span><a href="./">{e(T["retour"])}</a></span>
    <span><a href="{('' if lg == 'fr' else '../') + ('en/' if lg == 'fr' else '')}chantiers.html">{e(autre_nom)}</a></span>
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


def main():
    racine = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    registre = lire(racine / "institutions.json", {"institutions": []})
    latest = lire(racine / "data" / "latest.json", {})
    langue = lire(racine / "data" / "langue.json", {})
    eds = editions(racine)
    items = construire(registre, latest, langue, eds)
    (racine / "chantiers.html").write_text(page(items, latest, langue, "fr"), encoding="utf-8")
    (racine / "en").mkdir(exist_ok=True)
    (racine / "en" / "chantiers.html").write_text(page(items, latest, langue, "en"), encoding="utf-8")
    c = {g: sum(1 for it in items if it["etat"] == g) for g in GROUPES}
    print(f"chantiers.html et en/chantiers.html écrits : {c}")


if __name__ == "__main__":
    main()
