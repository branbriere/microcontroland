#!/usr/bin/env python3
"""Microcontrôland : version sans JavaScript de La Puce Libre.

Transformation mécanique des éditions publiées par la passerelle
(data/editions/N.json) : aucun mot ajouté au journal, seulement des
intitulés de rubrique. Censure (████) et coquilles restent telles quelles.

Écrit :
  journal.txt          édition du jour, texte brut, FR puis EN
  texte/index.html     liste des éditions
  texte/N.html         une page HTML simple par édition (sans JavaScript)

Usage : python3 .github/texte_journal.py [racine du site]
Licence MIT. Version 1.0, 20 octobre 2026.
"""
import html
import json
import sys
from pathlib import Path

LANGS = ("fr", "en")
LIB = {
    "fr": {"edition": "Édition n° {n}", "jour": "ère {e}, jour {j}", "par": "Par {nom} ({region}), {rubrique}",
           "citation": "Citation du jour", "breves": "Brèves", "regions": "Vos régions", "billet": "Billet",
           "journee": "La journée", "suivre": "À suivre", "bourse": "Bourse", "fermee": "fermée",
           "etat": "Le pays", "regime": "Régime", "capitale": "Capitale", "president": "Président",
           "fin": "Le mot de la fin", "complet": "Toutes les données de cette édition (JSON)",
           "source": "Version texte de La Puce Libre, générée automatiquement à partir de l'édition publiée par la passerelle. Aucun humain n'écrit le journal.",
           "liste": "La Puce Libre : toutes les éditions en texte", "retour": "Toutes les éditions",
           "dimanche": "Édition du dimanche", "autres": "Autres rubriques"},
    "en": {"edition": "Issue no. {n}", "jour": "era {e}, day {j}", "par": "By {nom} ({region}), {rubrique}",
           "citation": "Quote of the day", "breves": "In brief", "regions": "Your regions", "billet": "Column",
           "journee": "The day", "suivre": "Coming up", "bourse": "Markets", "fermee": "closed",
           "etat": "The country", "regime": "Regime", "capitale": "Capital", "president": "President",
           "fin": "Last word", "complet": "All data for this issue (JSON)",
           "source": "Text version of La Puce Libre, generated automatically from the issue published by the gateway. No human writes the paper.",
           "liste": "La Puce Libre: all issues as text", "retour": "All issues",
           "dimanche": "Sunday edition", "autres": "Other sections"},
}


# Mêmes correspondances que le site (app.js l. 72-73).
REGION_EN = {"Mines": "Mines", "Champs": "Fields", "Raffineries": "Refineries", "Barrage": "Dam", "Port": "Harbour", "Ville": "City"}
MATIERE_EN = {"Cuivre": "Copper", "Blé": "Wheat", "Pétrole": "Oil", "Électricité": "Electricity"}


def reg(nom, lg):
    return REGION_EN.get(nom, nom) if lg == "en" else (nom or "")


def tr(v, lg):
    """Texte d'un champ bilingue {fr, en} ; chaîne simple telle quelle ; sinon vide."""
    if isinstance(v, dict):
        return str(v.get(lg) or "")
    if isinstance(v, str):
        return v
    return ""


# Champs chiffrés ou de mise en page, déjà publiés tels quels dans le JSON : pas repris en texte.
NON_TEXTE = {"day", "date", "ere", "jourEre", "etat", "regions", "satisfaction7j", "ages", "redaction",
             "systeme", "president", "presidentNom", "election", "bourse"}
TRAITES = {"censure", "kicker", "title", "chapo", "body", "signature", "quote", "briefs", "vosRegions",
           "billet", "journee", "aSuivre", "motDeLaFin", "dimanche"}


def par(sig, lg):
    if isinstance(sig, dict) and sig.get("nom"):
        return [LIB[lg]["par"].format(nom=sig["nom"], region=reg(sig.get("region", ""), lg), rubrique=tr(sig.get("rubrique"), lg))]
    return []


def textes(v, lg):
    """Toutes les lignes de texte d'un bloc de forme inconnue, dans l'ordre (rubriques à venir)."""
    sep = " : " if lg == "fr" else ": "
    if isinstance(v, list):
        return [x for e in v for x in textes(e, lg)]
    if not isinstance(v, dict):
        return []
    if set(v) <= {"fr", "en"}:
        return [tr(v, lg)] if tr(v, lg) else []
    tete = [tr(v.get(k), lg) for k in ("jour", "region", "rubrique", "titre") if tr(v.get(k), lg)]
    if "texte" in v and tr(v["texte"], lg):
        lignes = [" · ".join(tete) + sep + tr(v["texte"], lg) if tete else tr(v["texte"], lg)]
    else:
        lignes = [" · ".join(tete)] if tete else []
    for k, x in v.items():
        if k == "signature":
            lignes += par(x, lg)
        elif k not in ("jour", "region", "rubrique", "titre", "texte", "style"):
            lignes += textes(x, lg)
    return lignes


def sections(ed, lg):
    """Liste de (titre de section ou None, [lignes]) pour une édition et une langue."""
    L = LIB[lg]
    out = []
    tete = [L["edition"].format(n=ed.get("day", "?")) + " · " + str(ed.get("date", "")) + " · "
            + L["jour"].format(e=ed.get("ere", "?"), j=ed.get("jourEre", "?"))]
    cens = ed.get("censure") or {}
    if cens.get("active") and tr(cens.get("bandeau"), lg):
        tete.append("[" + tr(cens.get("bandeau"), lg) + "]")
    out.append((None, tete))

    une = []
    for champ in ("kicker", "title", "chapo"):
        t = tr(ed.get(champ), lg)
        if t:
            une.append(t)
    une += [tr(p, lg) for p in ed.get("body") or [] if tr(p, lg)]
    une += par(ed.get("signature"), lg)
    out.append(("", une))

    if tr(ed.get("quote"), lg):
        out.append((L["citation"], ["« " + tr(ed["quote"], lg) + " »" if lg == "fr" else "“" + tr(ed["quote"], lg) + "”"]))

    br = []
    for b in ed.get("briefs") or []:
        rub, titre, texte = tr(b.get("rubrique"), lg), tr(b.get("titre"), lg), tr(b.get("texte"), lg)
        br.append(" · ".join(x for x in (rub, titre) if x) + (" : " if lg == "fr" else ": ") + texte if (rub or titre) else texte)
        br += par(b.get("signature"), lg)
    if br:
        out.append((L["breves"], br))

    vr = ed.get("vosRegions") or {}
    notes = [reg(n.get("region", ""), lg) + " · " + tr(n.get("titre"), lg) + (" : " if lg == "fr" else ": ") + tr(n.get("texte"), lg)
             for n in vr.get("notes") or []]
    if notes:
        notes += par(vr.get("signature"), lg)
        out.append((L["regions"], notes))

    bi = ed.get("billet") or {}
    if tr(bi.get("texte"), lg):
        out.append((L["billet"], [x for x in (tr(bi.get("titre"), lg), tr(bi.get("texte"), lg)) if x] + par(bi.get("signature"), lg)))

    jn = [f"{j.get('heure', '?')} h · {tr(j.get('texte'), lg)}" for j in ed.get("journee") or [] if tr(j.get("texte"), lg)]
    if jn:
        out.append((L["journee"], jn))

    sv = [tr(x, lg) for x in (ed.get("aSuivre") or {}).get("lignes") or [] if tr(x, lg)]
    if sv:
        out.append((L["suivre"], sv))

    di = textes(ed.get("dimanche"), lg)
    if di:
        out.append((L["dimanche"], di))

    autres = [x for k, v in ed.items() if k not in NON_TEXTE | TRAITES for x in textes(v, lg)]
    if autres:
        out.append((L["autres"], autres))

    bo = ed.get("bourse") or {}
    if bo.get("fermee"):
        out.append((L["bourse"], [L["fermee"]]))
    elif bo.get("lignes"):
        lignes = []
        for x in bo["lignes"]:
            v = x.get("variation")
            vs = ("+" if isinstance(v, (int, float)) and v > 0 else "") + (str(v).replace(".", ",") + " %" if lg == "fr" else str(v) + "%")
            mat = x.get("matiere", "")
            lignes.append(f"{MATIERE_EN.get(mat, mat) if lg == 'en' else mat} ({reg(x.get('region', ''), lg)}) {vs}")
        out.append((L["bourse"], lignes))

    et = ed.get("etat") or {}
    pays = []
    if tr(et.get("regime"), lg):
        pays.append(L["regime"] + " : " + tr(et["regime"], lg) if lg == "fr" else L["regime"] + ": " + tr(et["regime"], lg))
    if et.get("capitale"):
        pays.append((L["capitale"] + (" : " if lg == "fr" else ": ")) + reg(str(et["capitale"]), lg))
    if ed.get("presidentNom"):
        pays.append((L["president"] + (" : " if lg == "fr" else ": ")) + str(ed["presidentNom"]))
    if pays:
        out.append((L["etat"], pays))

    if tr(ed.get("motDeLaFin"), lg):
        out.append((L["fin"], [tr(ed["motDeLaFin"], lg)]))
    return out


def texte(ed, base):
    blocs = []
    for lg in LANGS:
        L = LIB[lg]
        t = ["LA PUCE LIBRE — " + ("Microcontrôland" if lg == "fr" else "Microcontrôland (English)"), ""]
        for titre, lignes in sections(ed, lg):
            if titre:
                t += ["", "## " + titre]
            elif titre == "":
                t.append("")
            t += lignes
        t += ["", L["complet"] + " : " + base + "data/editions/" + str(ed.get("day")) + ".json", L["source"]]
        blocs.append("\n".join(t))
    return ("\n\n" + "=" * 60 + "\n\n").join(blocs) + "\n"


def page(ed, prec, suiv):
    e = html.escape
    n = ed.get("day")
    corps = []
    for lg in LANGS:
        L = LIB[lg]
        corps.append(f'<article lang="{lg}">')
        for titre, lignes in sections(ed, lg):
            if titre is None:
                corps.append("<p><small>" + "<br>".join(e(x) for x in lignes) + "</small></p>")
            elif titre == "":
                corps.append(f"<h1>{e(tr(ed.get('title'), lg))}</h1>")
                corps += [f"<p>{e(x)}</p>" for x in lignes if x != tr(ed.get("title"), lg)]
            else:
                corps.append(f"<h2>{e(titre)}</h2><ul>" + "".join(f"<li>{e(x)}</li>" for x in lignes) + "</ul>")
        corps.append(f'<p><a href="../data/editions/{n}.json">{e(L["complet"])}</a></p><p><small>{e(L["source"])}</small></p></article><hr>')
    nav = []
    if prec:
        nav.append(f'<a href="{prec}.html">← {prec}</a>')
    nav.append('<a href="index.html">' + e(LIB["fr"]["retour"]) + " / " + e(LIB["en"]["retour"]) + "</a>")
    if suiv:
        nav.append(f'<a href="{suiv}.html">{suiv} →</a>')
    titre = e(f"La Puce Libre n° {n} ({ed.get('date', '')}) : {tr(ed.get('title'), 'fr')}")
    return (f'<!doctype html>\n<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{titre}</title><link rel="alternate" type="application/json" href="../data/editions/{n}.json">'
            '<style>body{max-width:42em;margin:2em auto;padding:0 1em;font:1.05em/1.5 Georgia,serif}</style></head><body>\n'
            f'<nav>{" · ".join(nav)}</nav>\n' + "\n".join(corps) + f'\n<nav>{" · ".join(nav)}</nav>\n</body></html>\n')


def index(eds):
    e = html.escape
    li = "".join(f'<li><a href="{d.get("day")}.html">n° {d.get("day")} · {e(str(d.get("date", "")))} · '
                 f'{e(tr(d.get("title"), "fr"))} / <span lang="en">{e(tr(d.get("title"), "en"))}</span></a></li>'
                 for d in reversed(eds))
    return ('<!doctype html>\n<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{e(LIB["fr"]["liste"])}</title><style>body{{max-width:42em;margin:2em auto;padding:0 1em;font:1.05em/1.5 Georgia,serif}}</style></head><body>\n'
            f'<h1>{e(LIB["fr"]["liste"])}</h1><p lang="en">{e(LIB["en"]["liste"])}</p>\n'
            '<p><a href="../journal.txt">journal.txt</a> · <a href="../llms.txt">llms.txt</a></p>\n'
            f'<ul>{li}</ul>\n<p><small>{e(LIB["fr"]["source"])}</small></p></body></html>\n')


def main():
    racine = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    base = "https://www.microcontroland.org/"
    eds = []
    for f in (racine / "data" / "editions").glob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            if isinstance(d, dict) and isinstance(d.get("day"), int):
                eds.append(d)
        except (ValueError, OSError) as err:
            print(f"Ignoré : {f.name} ({err})", file=sys.stderr)
    if not eds:
        print("Aucune édition trouvée : rien n'est écrit.", file=sys.stderr)
        return 0
    eds.sort(key=lambda d: d["day"])
    out = racine / "texte"
    out.mkdir(exist_ok=True)
    nums = [d["day"] for d in eds]
    for i, d in enumerate(eds):
        (out / f"{d['day']}.html").write_text(page(d, nums[i - 1] if i else None, nums[i + 1] if i + 1 < len(nums) else None), encoding="utf-8")
    (out / "index.html").write_text(index(eds), encoding="utf-8")
    (racine / "journal.txt").write_text(texte(eds[-1], base), encoding="utf-8")
    print(f"{len(eds)} éditions ; journal.txt = n° {eds[-1]['day']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
