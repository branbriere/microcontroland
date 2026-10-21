#!/usr/bin/env python3
"""Microcontrôland : version sans JavaScript de La Puce Libre.

Transformation mécanique des éditions publiées par la passerelle
(data/editions/N.json) : aucun mot ajouté au journal, seulement des
intitulés de rubrique. Censure (████) et coquilles restent telles quelles.

Écrit :
  journal.txt          édition du jour, texte brut, FR puis EN
  texte/index.html     liste des éditions
  texte/N.html         une page HTML simple par édition (sans JavaScript)
  texte/histoire.html  présidents et ères (data/histoire.json), fermée avant l'âge de la Mémoire
  texte/langue.html    lexique et « qui comprend qui » (data/langue.json), fermée avant la Parole
  sitemap.xml          plan du site pour les moteurs et les agents

Usage : python3 .github/texte_journal.py [racine du site]
Licence MIT. Version 1.1, 21 octobre 2026 (1.0 : 20 octobre 2026).
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
            '<p><a href="../journal.txt">journal.txt</a> · <a href="histoire.html">Histoire / History</a> · '
            '<a href="langue.html">La langue / Language</a> · <a href="../llms.txt">llms.txt</a></p>\n'
            f'<ul>{li}</ul>\n<p><small>{e(LIB["fr"]["source"])}</small></p></body></html>\n')


# ---------------------------------------------------------------------------
# Pages Histoire et Langue : mêmes textes et même ouverture par âge que le site
# (histoire.js, langue.js, commun.js). Aucun mot ajouté.
# ---------------------------------------------------------------------------
STYLE = "<style>body{max-width:42em;margin:2em auto;padding:0 1em;font:1.05em/1.5 Georgia,serif}table{border-collapse:collapse}td,th{border:1px solid #999;padding:.2em .5em;text-align:left}</style>"
ATTENTE = {"fr": {"k": "En attente d'évolution de la civilisation", "t": "Cette rubrique s'ouvrira à l'âge de {n}", "ou": "Où en est le pays"},
           "en": {"k": "Waiting for the civilisation to evolve", "t": "This section opens in the age of {n}", "ou": "Where the country stands"}}
REGIONS = ["Mines", "Champs", "Raffineries", "Barrage", "Port", "Ville"]


def pl(n, fr, en, lg):
    """Pluriel comme sur le site : « s » si n > 1."""
    return (fr if lg == "fr" else en) + ("s" if n > 1 else "")


def attente(latest, need, lg):
    """Panneau d'attente d'une rubrique fermée (commun.js, wait)."""
    e = html.escape
    A = ATTENTE[lg]
    et = ((latest or {}).get("ages") or {}).get("etapes") or []
    if need >= len(et):
        return []
    s = et[need]
    return [f"<p><small>{e(A['k'])}</small></p>", f"<h2>{e(A['t'].format(n=tr(s.get('nom'), lg)))}</h2>",
            f"<p>{e(tr(s.get('ouvre'), lg))}</p>",
            f"<p><b>{e(A['ou'])}{' : ' if lg == 'fr' else ': '}</b>{e(tr(s.get('progres'), lg)) or '—'}</p>"]


def duree(h, lg):
    d, r = divmod(int(h), 24)
    return (f"{d} j {r} h" if d else f"{r} h") if lg == "fr" else (f"{d} d {r} h" if d else f"{r} h")


def histoire_lg(rows, latest, lg):
    e = html.escape
    fr = lg == "fr"
    if (latest or {}).get("ages", {}).get("age", 0) < 2:
        return attente(latest, 2, lg)
    rows = list(rows)
    if latest and latest.get("president"):
        et = latest.get("etat") or {}
        rows.append({"ere": latest.get("ere") or 1, "id": latest["president"], "nom": latest.get("presidentNom") or "",
                     "region": et.get("capitale", ""), "current": True, "since": tr(et.get("auPouvoirDepuis"), lg), "regime": et.get("regime")})
    if not rows:
        return [f"<p>{e('L’histoire n’a pas encore commencé : le premier président apparaîtra ici.'.replace('’', chr(39)) if fr else 'History has not started yet: the first president will appear here.')}</p>"]
    done = [r for r in rows if not r.get("current")]
    eres = sorted({r.get("ere") for r in rows}, reverse=True)
    rue = sum(1 for r in done if any(m in tr(r.get("finPar"), lg) for m in ("rue", "street")))
    mini = sum(1 for r in done if any(m in tr(r.get("finPar"), lg) for m in ("ministre", "minister")))
    p, ne = len(rows), len(eres)
    if fr:
        resume = f"{p} {pl(p, 'règne', '', lg)} en {ne} {pl(ne, 'ère', '', lg)} : {rue} {pl(rue, 'renversé', '', lg)} par la rue, {mini} {pl(mini, 'trahi', '', lg)} par un ministre."
    else:
        resume = f"{p} {pl(p, '', 'reign', lg)} over {ne} {pl(ne, '', 'era', lg)}: {rue} toppled by the street, {mini} betrayed by a minister."
    if done:
        lg_ = max(done, key=lambda r: r.get("heures", 0))
        resume += (" Plus long règne : " if fr else " Longest reign: ") + f"{lg_.get('nom') or 'nº ' + str(lg_.get('id'))} ({duree(lg_.get('heures', 0), lg)})."
    out = [f"<p>{e(resume)}</p>"]
    rec = (latest or {}).get("records") or []
    if rec:
        out.append(f"<h2>{'Records de l' + chr(39) + 'ère' if fr else 'Records of the era'}</h2><table>" + "".join(
            f"<tr><td><b>{e(tr(r.get('titre'), lg))}</b></td><td>{e(tr(r.get('valeur'), lg))}</td><td>{e(tr(r.get('qui'), lg))}</td>"
            f"<td>{'jour' if fr else 'day'} {e(str(r.get('jour', '')))}</td></tr>" for r in rec) + "</table>")
    tete = ["Président", "Région", "Au pouvoir", "Durée", "Fin du règne", "Régime dominant"] if fr else \
           ["President", "Region", "In power", "Lasted", "How it ended", "Main regime"]
    for n in eres:
        liste = [r for r in rows if r.get("ere") == n][::-1]
        out.append(f"<h2>{'Ère' if fr else 'Era'} {n} ({len(liste)} {pl(len(liste), 'règne', 'reign', lg)})</h2><table><tr>"
                   + "".join(f"<th>{e(t)}</th>" for t in tete) + "</tr>")
        for r in liste:
            m = r.get("mandats") or 0
            elu = (f" · {m} {pl(m, 'élection', 'election', lg)} {pl(m, 'gagnée', '', lg) if fr else 'won'}" if m > 1 else "")
            quand = ("En fonction" if fr else "In office") if r.get("current") else \
                str(r.get("debut", "")) + (" – " + str(r.get("fin")) if r.get("fin") != r.get("debut") else "")
            out.append(f"<tr><td><b>{e(r.get('nom') or 'nº ' + str(r.get('id')))}</b> (nº {e(str(r.get('id')))}{e(elu)})</td>"
                       f"<td>{e(reg(r.get('region', ''), lg))}</td><td>{e(quand)}</td>"
                       f"<td>{e(r['since'] if r.get('current') else duree(r.get('heures', 0), lg))}</td>"
                       f"<td>{e(('toujours au pouvoir' if fr else 'still in power') if r.get('current') else tr(r.get('finPar'), lg))}</td>"
                       f"<td>{e(tr(r.get('regime'), lg))}</td></tr>")
        out.append("</table>")
    return out


LANGUE = {
    "fr": {"sum": lambda p, i, e: f"Ère {e} : {p} mot{'s' if p > 1 else ''} commun{'s' if p > 1 else ''} sur {i} idées que le pays a vécues.",
           "idea": "Idée", "word": "Mot", "agree": "Régions qui le disent", "shared": "Mots communs", "forming": "Encore en discussion",
           "sounds": "Les sons de cette ère", "cons": "Consonnes", "vow": "Voyelles",
           "soundsNote": "Chaque ère tire au sort ses propres sons. Les prénoms et les mots en sont faits : chaque ère a donc sa musique.",
           "comp": "Qui comprend qui", "compNote": "Part des idées pour lesquelles deux régions emploient le même mot. Une région en révolte n'écoute plus et s'éloigne.",
           "none": "Aucun mot n'est encore fixé.", "how": "Comment naît un mot",
           "howText": "Chaque heure, la passerelle propose une idée. Toutes les régions disent leur mot ; l'une d'elles est tirée au sort comme oratrice et les autres apprennent d'elle. Une idée n'entre dans la langue que lorsque le pays l'a vécue : pas de mot pour « révolte » avant la première révolte."},
    "en": {"sum": lambda p, i, e: f"Era {e}: {p} shared word{'s' if p > 1 else ''} out of {i} ideas the country has lived through.",
           "idea": "Idea", "word": "Word", "agree": "Regions that say it", "shared": "Shared words", "forming": "Still being settled",
           "sounds": "The sounds of this era", "cons": "Consonants", "vow": "Vowels",
           "soundsNote": "Every era draws its own sounds. Names and words are built from them, so each era sounds different.",
           "comp": "Who understands whom", "compNote": "Share of ideas for which two regions use the same word. A region in revolt stops listening and drifts away.",
           "none": "No word is settled yet.", "how": "How a word is born",
           "howText": "Each hour the gateway names an idea. Every region says its word; one of them is picked as the speaker and the others learn from it. An idea only enters the language once the country has lived it: no word for “revolt” before the first revolt."},
}


def langue_lg(d, latest, lg):
    e = html.escape
    L = LANGUE[lg]
    if (latest or {}).get("ages", {}).get("age", 0) < 1:
        return attente(latest, 1, lg)
    mots = [m for m in d.get("mots") or [] if isinstance(m, dict)]
    tri = sorted(mots, key=lambda m: (-m.get("accord", 0), tr(m.get("idee"), lg).lower()))

    def table(rows):
        if not rows:
            return f"<p>{e(L['none'])}</p>"
        return (f"<table><tr><th>{e(L['idea'])}</th><th>{e(L['word'])}</th><th>{e(L['agree'])}</th></tr>"
                + "".join(f"<tr><td>{e(tr(m.get('idee'), lg))}</td><td><b>{e(str(m.get('mot', '')))}</b></td><td>{m.get('accord', 0)}/6</td></tr>" for m in rows)
                + "</table>")
    communs = [m for m in tri if m.get("accord", 0) >= 5]
    encours = [m for m in tri if m.get("accord", 0) < 5]
    out = [f"<p>{e(L['sum'](d.get('partages', 0), d.get('idees', 0), d.get('ere', '?')))}</p>",
           f"<h2>{e(L['shared'])} ({len(communs)})</h2>", table(communs)]
    if encours:
        out += [f"<h2>{e(L['forming'])} ({len(encours)})</h2>", table(encours)]
    so = d.get("sons") or {}
    out += [f"<h2>{e(L['sounds'])}</h2>",
            f"<p><b>{e(L['cons'])}</b> {e(' · '.join(so.get('consonnes') or []))}<br><b>{e(L['vow'])}</b> {e(' · '.join(so.get('voyelles') or []))}</p>",
            f"<p><small>{e(L['soundsNote'])}</small></p>"]
    c = d.get("comprehension") or []
    if c:
        noms = [reg(r, lg) for r in REGIONS]
        out.append(f"<h2>{e(L['comp'])}</h2><table><tr><th></th>" + "".join(f"<th>{e(n)}</th>" for n in noms) + "</tr>"
                   + "".join(f"<tr><th>{e(noms[i] if i < len(noms) else str(i))}</th>"
                             + "".join("<td>—</td>" if i == j else f"<td>{v} %</td>" for j, v in enumerate(row)) + "</tr>"
                             for i, row in enumerate(c)) + "</table>")
        out.append(f"<p><small>{e(L['compNote'])}</small></p>")
    out += [f"<h2>{e(L['how'])}</h2>", f"<p>{e(L['howText'])}</p>"]
    return out


def page_rubrique(titres, corps_lg, source):
    """Page FR puis EN ; titres = {lg: titre}, corps_lg(lg) -> [html]."""
    e = html.escape
    corps = []
    for lg in LANGS:
        corps.append(f'<article lang="{lg}"><h1>{e(titres[lg])}</h1>')
        corps += corps_lg(lg)
        corps.append(f'<p><a href="../{source}">{e("Données (JSON)" if lg == "fr" else "Data (JSON)")}</a></p></article><hr>')
    nav = '<nav><a href="index.html">' + e(LIB["fr"]["retour"]) + " / " + e(LIB["en"]["retour"]) + "</a></nav>"
    return (f'<!doctype html>\n<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{e(titres["fr"])}</title><link rel="alternate" type="application/json" href="../{source}">{STYLE}</head><body>\n'
            f'{nav}\n' + "\n".join(corps) + f'\n{nav}\n</body></html>\n')


def lire(f, defaut):
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (ValueError, OSError) as err:
        print(f"Ignoré : {f.name} ({err})", file=sys.stderr)
        return defaut


def sitemap(racine, base, eds):
    """Toutes les pages publiques du site, plus les versions texte."""
    urls = []
    for f in sorted(racine.glob("*.html")) + sorted((racine / "en").glob("*.html")):
        rel = f.relative_to(racine).as_posix()
        urls.append((base + ("" if rel == "index.html" else rel.replace("/index.html", "/")), None))
    dernier = str(eds[-1].get("date", "")) if eds else None
    urls += [(base + "journal.txt", dernier), (base + "llms.txt", None), (base + "texte/", dernier),
             (base + "texte/histoire.html", dernier), (base + "texte/langue.html", dernier)]
    urls += [(f"{base}texte/{d['day']}.html", str(d.get("date", "")) or None) for d in eds]
    ok = lambda x: x and len(x) == 10 and x[4] == "-" and x[7] == "-"
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "".join(f"  <url><loc>{html.escape(u)}</loc>" + (f"<lastmod>{m}</lastmod>" if ok(m) else "") + "</url>\n" for u, m in urls)
            + "</urlset>\n")


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
    latest = lire(racine / "data" / "latest.json", {})
    if not isinstance(latest, dict):
        latest = {}
    hist = lire(racine / "data" / "histoire.json", [])
    hist = [r for r in hist if isinstance(r, dict)] if isinstance(hist, list) else []
    (out / "histoire.html").write_text(page_rubrique(
        {"fr": "Histoire de Microcontrôland : présidents, régimes et ères", "en": "History of Microcontrôland: presidents, regimes and eras"},
        lambda lg: histoire_lg(hist, latest, lg), "data/histoire.json"), encoding="utf-8")
    lang = lire(racine / "data" / "langue.json", {})
    if not isinstance(lang, dict):
        lang = {}
    (out / "langue.html").write_text(page_rubrique(
        {"fr": "La langue de Microcontrôland : le microcontrôlandais", "en": "The language of Microcontrôland"},
        lambda lg: langue_lg(lang, latest, lg), "data/langue.json"), encoding="utf-8")
    (racine / "sitemap.xml").write_text(sitemap(racine, base, eds), encoding="utf-8")
    print(f"{len(eds)} éditions ; journal.txt = n° {eds[-1]['day']} ; histoire, langue et sitemap.xml écrits")
    return 0


if __name__ == "__main__":
    sys.exit(main())
