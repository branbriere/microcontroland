"""Microcontrôland : page « Institut national de sondage » (FR) et « National Polling Institute » (EN).

Idée de Bran (17/11/2026), validée le 17/11/2026 : une vision d'ensemble de la population en graphiques, choisis dans
un menu déroulant qu'on enrichit à chaque mise à jour. Facette satirique (site du journal) ; chiffres exacts, tous
calculés à partir du seul fichier brut publié chaque soir dans le dépôt microcontroland-data (SHA-256 vérifié avec
le manifeste). Aucun chiffre n'est inventé, aucun graphique n'est simulé.

Ce que le script écrit :
  · institut.json             archive, un soir par entrée, jamais réécrite (les soirs passés sont calculés une fois,
                               au premier passage, à partir des bruts déjà publiés, comme data/historique.json) ;
  · institut.html, en/institut.html  la page (graphiques SVG écrits ici, lisibles sans JavaScript ; le menu
                               déroulant ne fait qu'afficher un graphique à la fois).

Règles :
  · Foi : seuils du firmware (mcl_region_logic.h) : croyant si foi/255 > 0,66, athée si < 0,33, agnostique sinon.
    Source : citoyens[] du brut (relevé de l'édition) ; le chiffre de pays.croyantsPct (relevé des régions) peut
    différer d'une unité, la page le dit.
  · « A voté pour le président en place » = drapeau vote-president (CIV_VOTED_PRES : dernier vote du citoyen) ;
    « censuré » = drapeau censure (citoyen touché par la censure).
  · Le sondage contre la vérité : election.sondage (20 citoyens interrogés) contre election.candidats (le vote).
  · Un graphique ne s'allume que si son mécanisme est publié dans le brut (champ « nouveautes ») ; sinon il reste
    dans le menu, grisé, « en attente d'évolution de la civilisation ». Les graphiques prévus (partis, emploi du
    temps, démographie) n'ont ni code ni chiffre : seulement une ligne grisée.
  · Âge : l'État civil (ages.etapes[3]). Avant, la page attend et rien n'est calculé (audit des déblocages).
  · Directeur : un citoyen tiré au sort une fois par ère, de façon vérifiable : numéro = (empreinte SHA-256 du brut du
    soir d'ouverture, lue comme un nombre) modulo 120, plus 1. Son mot = une ligne satirique + une ligne de faits.

La passerelle ne change pas. Licence MIT. Version 1.0, novembre 2026 (firmware 0.10.1, format 6 de la 0.11 prévu).

  python3 .github/institut.py <racine du site> [--source <dépôt de données ou URL>] [--attendre <secondes>]
"""
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

ETAT_CIVIL = 3
BASE = "https://www.microcontroland.org/"
SOURCE = "https://raw.githubusercontent.com/branbriere/microcontroland-data/main/"
REGIONS = ["Mines", "Champs", "Raffineries", "Barrage", "Port", "Ville"]
REGIMES_EN = {"Démocratie": "Democracy", "Démocratie fragile": "Fragile democracy", "Oligarchie": "Oligarchy", "Autocratie": "Autocracy",
              "Junte": "Junta", "Dictature": "Dictatorship", "Agitation révolutionnaire": "Revolutionary unrest"}

A = None   # module atelier.py : même lecture des données, mêmes menus et en-têtes (chargé dans main)


def module(racine, nom):
    spec = importlib.util.spec_from_file_location(nom, racine / ".github" / f"{nom}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ---------------------------------------------------------------- les chiffres d'un soir

def groupe_foi(f):
    x = f / 255
    return 0 if x > 0.66 else (2 if x < 0.33 else 1)    # 0 croyant, 1 agnostique, 2 athée


def tranches(vals, n=5):
    t = [0] * n
    for v in vals:
        t[min(n - 1, max(0, int(v) * n // 256))] += 1
    return t


def chiffres(brut):
    cit = [c for c in (brut.get("citoyens") or []) if isinstance(c, dict)]
    pays = brut.get("pays") or {}
    foi = [[0, 0, 0] for _ in REGIONS]
    pol = [[0, 0, 0] for _ in REGIONS]     # a voté pour le président, rebelle, censuré
    par_region = [0] * 6
    for c in cit:
        r = REGIONS.index(c["region"]) if c.get("region") in REGIONS else None
        if r is None:
            continue
        par_region[r] += 1
        foi[r][groupe_foi(int(c.get("foi") or 0))] += 1
        etat = c.get("etat") or []
        pol[r][0] += "vote-president" in etat
        pol[r][1] += "rebelle" in etat
        pol[r][2] += "censure" in etat
    j = {
        "date": brut.get("date"), "jourEre": brut.get("jourEre"), "edition": brut.get("edition"), "firmware": brut.get("firmware"),
        "n": len(cit), "parRegion": par_region, "regime": pays.get("regime"), "president": pays.get("president"),
        "foi": foi, "foiPays": [pays.get("croyantsPct"), pays.get("atheesPct")], "rebellesPays": pays.get("rebelles"),
        "politique": pol, "ministres": len(pays.get("ministres") or []),
        "humeur": {k: tranches(int(c.get(k) or 0) for c in cit) for k in ("satisfaction", "colere", "peur")},
    }
    no = brut.get("notoriete")
    if isinstance(no, list) and no:
        top = sorted(((v, i + 1) for i, v in enumerate(no) if isinstance(v, (int, float)) and v > 0), key=lambda x: (-x[0], x[1]))[:10]
        j["notoriete"] = [[i, v] for v, i in top]
    el = brut.get("election")
    if isinstance(el, dict) and el.get("candidats"):
        j["election"] = {"heure": el.get("heure"), "inscrits": el.get("inscrits"), "exprimes": el.get("exprimes"),
                         "abstentions": el.get("abstentions"), "blancs": el.get("blancs"),
                         "candidats": [[c.get("id"), c.get("nom"), c.get("region"), c.get("voix"), c.get("pct")] for c in el["candidats"]],
                         "sondage": el.get("sondage")}
    nv = brut.get("nouveautes") or {}
    if nv.get("travail"):
        eco = [{"octets": 0, "heures": 0, "sansEmploi": 0, "postes": 0, "grevistes": 0} for _ in REGIONS]
        for h in brut.get("heures") or []:
            for r, x in enumerate((h.get("regions") or [])[:6]):
                t = x.get("travail") if isinstance(x, dict) else None
                if not isinstance(t, dict):
                    continue
                e = eco[r]
                e["octets"] += int(t.get("octets") or 0)
                e["heures"] += 1
                e["sansEmploi"] += int(t.get("sansEmploi") or 0)
                e["postes"] += int(t.get("postes") or 0)
                e["grevistes"] = max(e["grevistes"], int(t.get("grevistes") or 0))
        ec = brut.get("economie") or {}
        j["economie"] = {"regions": [[e["octets"], e["heures"], round(e["sansEmploi"] / e["heures"], 1) if e["heures"] else None,
                                      round(e["postes"] / e["heures"], 1) if e["heures"] else None, e["grevistes"]] for e in eco],
                         "valeurOctet": ec.get("valeurOctet"), "greves": ec.get("greves"),
                         "chomage": bool(nv.get("chomage")), "greve": bool(nv.get("greve"))}
    return j


# ---------------------------------------------------------------- textes

T = {
    "fr": {
        "titre": "Institut national de sondage", "haut": "République de Microcontrôland · statistique officielle",
        "chapo": "L'Institut national de sondage ne sonde presque personne : il compte tout le monde. Chaque soir, les 120 citoyens "
                 "sont relevés un par un dans le fichier brut publié par la passerelle, et l'Institut en tire ses graphiques. "
                 "Le seul vrai sondage du pays interroge vingt citoyens avant chaque élection ; l'Institut le publie à côté du vrai résultat.",
        "desc": "L'Institut national de sondage de Microcontrôland : la population entière en graphiques (foi, politique, humeur), calculée chaque soir à partir des données brutes publiées.",
        "slogan": ["Taux de réponse : 100 %. Personne n'a eu le choix.", "Marge d'erreur : 0 point. Échantillon : tout le monde."],
        "choisir": "Choisir un graphique", "attente_court": "en attente d'évolution de la civilisation",
        "sommaire": "Les graphiques",
        "directeur": "Le mot du directeur", "dir_qui": "{nom}, citoyen n° {n} ({r}), directeur de l'Institut, tiré au sort le {d}",
        "dir_tirage": "Tirage vérifiable : empreinte SHA-256 du brut du {d} ({h}…), lue comme un nombre, modulo 120, plus 1.",
        "soir": "Relevé du {d}, édition n° {n}, {c} citoyens recensés.",
        "methode": "Méthode", "question": "Question au lecteur", "verifier": "Vérifier : {brut} du soir et {arch} (tous les soirs).",
        "brut": "le fichier brut", "arch": "institut.json",
        "foi_croy": "croyants", "foi_agn": "agnostiques", "foi_ath": "athées", "total": "Pays",
        "pol_vote": "ont voté pour le président en place", "pol_reb": "rebelles", "pol_cen": "touchés par la censure",
        "sat": "Satisfaction", "col": "Colère", "peur": "Peur", "tr": ["très basse", "basse", "moyenne", "haute", "très haute"],
        "sondage": "sondage (20 citoyens)", "urnes": "vote réel", "ecart": "Écart moyen entre le sondage et les urnes",
        "pts": "points", "pas_sondage": "Pas de sondage publié avant ce scrutin.",
        "election_du": "Élection du {d} à {h} h : {e} exprimés sur {i} inscrits, {a} abstentions, {b} blancs.",
        "octets": "octets produits dans la journée", "sansemploi": "sans-emploi (moyenne de l'heure)", "valeur": "valeur de l'octet",
        "jours": "jour de l'ère", "pct": "% de la population",
        "regime_ce_soir": "Régime ce soir : {r}.", "regimes": "Les régimes de l'ère (relevé de l'édition)", "du_au": "jours {a} à {b}",
        "attente": "L'Institut ouvre avec l'âge de l'État civil : on ne recense pas un pays qui n'a pas encore d'état civil.",
        "pied": "L'Institut est une institution satirique ; ses chiffres sont mesurés. Les Waïnas ne sont ni vivants ni conscients : ils n'ont ni opinions ni croyances au sens humain, seulement des nombres que le programme appelle ainsi.",
        "voir": "Voir aussi : <a href=\"chantiers.html\">La République en chantier</a> · <a href=\"histoire.html\">Histoire</a> · <a href=\"citoyen.html\">Mon citoyen</a>.",
        "g": {
            "foi": ("La foi par région", "Croyants, agnostiques et athées, au total et dans chaque région.",
                    "Pour chaque citoyen, la foi publiée (0 à 255) est rangée avec les seuils du programme : croyant au-dessus de 0,66, athée en dessous de 0,33, agnostique entre les deux.",
                    "Une région qui croit plus que les autres pense-t-elle autrement, ou a-t-elle seulement vécu autre chose ?"),
            "foi-courbe": ("La foi depuis le début de l'ère", "Part des croyants et des athées, soir après soir.",
                           "Même règle que « La foi par région », appliquée à chaque fichier brut publié depuis le premier export.",
                           "Une croyance qui monte ou qui baisse : qui la fait bouger, les citoyens ou les événements ?"),
            "politique": ("Le soutien au pouvoir", "Qui a voté pour le président en place, qui s'est rebellé, qui est touché par la censure, région par région.",
                          "Drapeaux publiés pour chaque citoyen : vote-president (son dernier vote est allé au président en place), rebelle, censure.",
                          "Peut-on gouverner un pays où une minorité seulement a voté pour vous ?"),
            "politique-courbe": ("Le pouvoir depuis le début de l'ère", "Soutiens du président en place et rebelles, soir après soir, avec le régime.",
                                 "Mêmes drapeaux que « Le soutien au pouvoir », pour chaque fichier brut publié.",
                                 "La colère précède-t-elle la chute, ou la suit-elle ?"),
            "sondage": ("Le sondage contre la vérité", "Avant chaque élection, vingt citoyens sont interrogés. Voici ce qu'ils annonçaient, et ce que les urnes ont dit.",
                        "Champ election du brut : sondage (pourcentages des 20 interrogés) et candidats (pourcentages du vote). Sondages publiés depuis le 1er novembre 2026.",
                        "Vingt citoyens peuvent-ils dire ce que pensent cent vingt ? Et un sondage publié change-t-il le vote qu'il prétend mesurer ?"),
            "humeur": ("L'humeur du pays", "Combien de citoyens dans chaque tranche de satisfaction, de colère et de peur.",
                       "Valeurs publiées pour chaque citoyen (0 à 255), rangées en cinq tranches égales.",
                       "Une moyenne rassurante peut-elle cacher deux pays : l'un content, l'autre furieux ?"),
            "notoriete": ("Les plus connus", "Les dix citoyens dont le nom circule le plus.",
                          "Champ notoriete du brut (une valeur par citoyen) ; à égalité, le plus petit numéro d'abord.",
                          "Être connu, est-ce la même chose qu'être écouté ?"),
            "economie": ("Le travail des régions", "Octets produits dans la journée et sans-emploi, région par région.",
                         "Champ heures[].regions[].travail du brut (firmware 0.11) : somme des octets de la journée, moyenne horaire des sans-emploi.",
                         "Une région qui produit plus vit-elle mieux ? Il faudra regarder la satisfaction à côté."),
            "partis": ("Les partis", "", "", ""),
            "journee": ("L'emploi du temps des Waïnas", "", "", ""),
            "demographie": ("La démographie", "", "", ""),
        },
        "dir1": ["L'Institut confirme que tout le monde a répondu.", "L'Institut rappelle qu'aucun citoyen n'a été oublié, ni consulté.",
                 "Les chiffres sont formels, l'Institut n'en dira pas plus.", "Le directeur a compté deux fois ; il trouve la même chose."],
        "dir2": "Les faits : {c} croyants, {g} agnostiques et {a} athées sur {n} ; {v} ont voté pour le président en place ; {r} rebelles{dr}.",
        "dr_plus": " ({x:+d} depuis la veille)",
        "dir_pres": "Le directeur est aussi le président en exercice. L'Institut tient à souligner son indépendance totale.",
        "bourdieu": "« L'opinion publique n'existe pas » : c'est le titre d'une conférence du sociologue Pierre Bourdieu, publiée dans Les Temps modernes (n° 318, janvier 1973). Il y discute trois postulats des sondages : que tout le monde a une opinion, que toutes les opinions se valent, et que la question posée est la question que les gens se posent. À chacun de voir si l'argument vaut pour vingt Waïnas.",
        "foi_note": "Le journal compte avec le relevé des régions : {p} % de croyants et {q} % d'athées ce soir. L'Institut compte citoyen par citoyen ; les deux relevés ne sont pas pris au même moment et peuvent différer de quelques unités.",
        "reb_note": "Le journal annonce {r} rebelles ce soir (relevé des régions) ; l'Institut en compte {s} citoyen par citoyen. Les deux relevés ne sont pas pris au même moment.",
        "maj_le": None,
    },
    "en": {
        "titre": "National Polling Institute", "haut": "Republic of Microcontrôland · official statistics",
        "chapo": "The National Polling Institute hardly polls anyone: it counts everyone. Every evening, all 120 citizens are read one by one "
                 "from the raw data file published by the gateway, and the Institute draws its charts from them. "
                 "The country's only real poll asks twenty citizens before each election; the Institute publishes it next to the actual result.",
        "desc": "Microcontrôland's National Polling Institute: the whole population in charts (faith, politics, mood), computed every evening from the published raw data.",
        "slogan": ["Response rate: 100%. Nobody had a choice.", "Margin of error: 0 points. Sample: everyone."],
        "choisir": "Choose a chart", "attente_court": "awaiting the evolution of civilisation",
        "sommaire": "The charts",
        "directeur": "A word from the director", "dir_qui": "{nom}, Citizen No. {n} ({r}), Director of the Institute, drawn by lot on {d}",
        "dir_tirage": "Verifiable draw: SHA-256 hash of the raw file of {d} ({h}…), read as a number, modulo 120, plus 1.",
        "soir": "Count of {d}, issue no. {n}, {c} citizens counted.",
        "methode": "Method", "question": "A question for the reader", "verifier": "Check: {brut} of the evening and {arch} (every evening).",
        "brut": "the raw data file", "arch": "institut.json",
        "foi_croy": "believers", "foi_agn": "agnostics", "foi_ath": "atheists", "total": "Country",
        "pol_vote": "voted for the sitting president", "pol_reb": "rebels", "pol_cen": "affected by censorship",
        "sat": "Satisfaction", "col": "Anger", "peur": "Fear", "tr": ["very low", "low", "medium", "high", "very high"],
        "sondage": "poll (20 citizens)", "urnes": "actual vote", "ecart": "Average gap between the poll and the ballot box",
        "pts": "points", "pas_sondage": "No poll was published before this election.",
        "election_du": "Election of {d} at {h}:00: {e} votes cast out of {i} registered, {a} abstentions, {b} blank.",
        "octets": "bytes produced during the day", "sansemploi": "jobless (hourly average)", "valeur": "value of the byte",
        "jours": "day of the era", "pct": "% of the population",
        "regime_ce_soir": "Regime tonight: {r}.", "regimes": "The regimes of the era (count at issue time)", "du_au": "days {a} to {b}",
        "attente": "The Institute opens with the Civil Registry age: you cannot take a census of a country that has no civil registry yet.",
        "pied": "The Institute is a satirical institution; its figures are measured. The Waïnas are neither alive nor conscious: they have no opinions or beliefs in the human sense, only numbers the program calls by those names.",
        "voir": "See also: <a href=\"chantiers.html\">Republic Under Construction</a> · <a href=\"histoire.html\">History</a> · <a href=\"citoyen.html\">My citizen</a>.",
        "g": {
            "foi": ("Faith by region", "Believers, agnostics and atheists, overall and in each region.",
                    "For each citizen, the published faith value (0 to 255) is sorted with the program's thresholds: believer above 0.66, atheist below 0.33, agnostic in between.",
                    "Does a region that believes more than the others think differently, or has it simply lived through other things?"),
            "foi-courbe": ("Faith since the start of the era", "Share of believers and atheists, evening after evening.",
                           "Same rule as “Faith by region”, applied to every raw data file published since the first export.",
                           "When a belief rises or falls, who moves it: the citizens or the events?"),
            "politique": ("Support for those in power", "Who voted for the sitting president, who rebelled, who is affected by censorship, region by region.",
                          "Flags published for each citizen: vote-president (their last vote went to the sitting president), rebelle, censure.",
                          "Can you govern a country where only a minority voted for you?"),
            "politique-courbe": ("Power since the start of the era", "Supporters of the sitting president and rebels, evening after evening, with the regime.",
                                 "Same flags as “Support for those in power”, for every published raw data file.",
                                 "Does anger come before the fall, or after it?"),
            "sondage": ("The poll versus the truth", "Before each election, twenty citizens are asked. Here is what they announced, and what the ballot box said.",
                        "Field election in the raw data: sondage (percentages of the 20 asked) and candidats (percentages of the vote). Polls published since 1 November 2026.",
                        "Can twenty citizens tell what a hundred and twenty think? And does a published poll change the vote it claims to measure?"),
            "humeur": ("The country's mood", "How many citizens fall in each band of satisfaction, anger and fear.",
                       "Values published for each citizen (0 to 255), sorted into five equal bands.",
                       "Can a reassuring average hide two countries, one content and one furious?"),
            "notoriete": ("The best known", "The ten citizens whose names travel furthest.",
                          "Field notoriete in the raw data (one value per citizen); on a tie, the lowest number first.",
                          "Is being known the same as being listened to?"),
            "economie": ("The regions at work", "Bytes produced during the day and jobless citizens, region by region.",
                         "Field heures[].regions[].travail in the raw data (firmware 0.11): sum of the day's bytes, hourly average of jobless citizens.",
                         "Does a region that produces more live better? Look at satisfaction next to it."),
            "partis": ("Political parties", "", "", ""),
            "journee": ("How the Waïnas spend their day", "", "", ""),
            "demographie": ("Demography", "", "", ""),
        },
        "dir1": ["The Institute confirms that everyone answered.", "The Institute points out that no citizen was forgotten, or consulted.",
                 "The figures are categorical; the Institute will say no more.", "The Director counted twice and found the same thing."],
        "dir2": "The facts: {c} believers, {g} agnostics and {a} atheists out of {n}; {v} voted for the sitting president; {r} rebels{dr}.",
        "dr_plus": " ({x:+d} since the day before)",
        "dir_pres": "The Director is also the sitting President. The Institute wishes to stress its complete independence.",
        "bourdieu": "“Public opinion does not exist”: this is the title of a lecture by the sociologist Pierre Bourdieu, published in Les Temps modernes (no. 318, January 1973). He questions three assumptions behind opinion polls: that everyone has an opinion, that all opinions are of equal weight, and that the question asked is the one people are asking themselves. Readers can judge whether the argument holds for twenty Waïnas.",
        "foi_note": "The paper counts with the regions' figures: {p}% believers and {q}% atheists tonight. The Institute counts citizen by citizen; the two counts are not taken at the same moment and can differ by a few units.",
        "reb_note": "The paper reports {r} rebels tonight (regions' count); the Institute counts {s} citizen by citizen. The two counts are not taken at the same moment.",
        "maj_le": None,
    },
}

# Ordre du menu déroulant. « besoin » : ce qu'il faut dans le soir pour allumer le graphique.
# Les trois derniers sont prévus par la feuille de route : aucune donnée, aucun code, une ligne grisée seulement.
GRAPHIQUES = [
    ("foi", lambda j, js: True),
    ("foi-courbe", lambda j, js: len(js) >= 2),
    ("politique", lambda j, js: True),
    ("politique-courbe", lambda j, js: len(js) >= 2),
    ("sondage", lambda j, js: any((x.get("election") or {}).get("sondage") for x in js)),
    ("humeur", lambda j, js: True),
    ("notoriete", lambda j, js: bool(j.get("notoriete"))),
    ("economie", lambda j, js: bool(j.get("economie"))),
    ("partis", None),
    ("journee", None),
    ("demographie", None),
]

STYLE = """<style>
.inst-slogan{font:600 13px var(--f-data);color:var(--muted);margin:4px 0 14px}
.inst-cmd{display:flex;flex-wrap:wrap;gap:10px;align-items:center;position:sticky;top:0;z-index:5;background:var(--paper);padding:10px 0;border-bottom:1px solid var(--rule);margin:14px 0}
.inst-cmd select{font:600 14px var(--f-data);border-radius:4px;border:1px solid var(--ink);padding:8px 12px;background:var(--sheet);color:var(--ink);max-width:100%}
.inst-g{border:1px solid var(--rule);background:var(--sheet);padding:12px 14px;margin:0 0 18px}
.inst-g h2{margin-top:0}
.inst-g svg{width:100%;height:auto;display:block;margin:8px 0;font-family:var(--f-data)}
.inst-g .m,.inst-g .q{font-size:.92em}.inst-g .q{font-style:italic}
.inst-leg{display:flex;flex-wrap:wrap;gap:6px 16px;font:12.5px var(--f-data);color:var(--muted);margin:4px 0}
.inst-leg i{display:inline-block;width:11px;height:11px;margin-right:5px;vertical-align:-1px}
.c0{fill:var(--warn);background:var(--warn)}.c1{fill:var(--neutral);background:var(--neutral)}.c2{fill:var(--mask);background:var(--mask)}.c3{fill:var(--down);background:var(--down)}
.s0{stroke:var(--warn)}.s1{stroke:var(--neutral)}.s2{stroke:var(--mask)}.s3{stroke:var(--down)}
.inst-g text{fill:var(--ink);font-size:13px}.inst-g text.mu{fill:var(--muted)}
.inst-g line.ax{stroke:var(--rule)}
.inst-dir{border-left:3px solid var(--mask);padding:4px 0 4px 12px;margin:14px 0}
.inst-dir p{margin:0 0 6px}
.inst-off{color:var(--muted)}
.js .inst-g[hidden]{display:none}
</style>"""

JS = r"""<script>
(function(){
  var sel = document.getElementById('inst-choix'); if (!sel) return;
  document.documentElement.classList.add('js');
  var cmd = document.getElementById('inst-cmd'); cmd.hidden = false;
  var som = document.getElementById('inst-sommaire'); if (som) som.hidden = true;
  var all = Array.prototype.slice.call(document.querySelectorAll('.inst-g'));
  function show(id){ all.forEach(function(g){ g.hidden = g.id !== 'g-' + id; }); }
  var h = (location.hash || '').replace('#g-', '');
  var ok = Array.prototype.some.call(sel.options, function(o){ return o.value === h && !o.disabled; });
  if (ok) sel.value = h;
  show(sel.value);
  sel.addEventListener('change', function(){ show(sel.value); try { history.replaceState(null, '', '#g-' + sel.value); } catch (e) {} });
})();
</script>"""


# ---------------------------------------------------------------- petits graphiques SVG (sans bibliothèque)

def e(x):
    return A.e(x)


def barres_empilees(lignes, classes, largeur=520):
    """lignes : [(étiquette, [valeurs…], total)] ; une barre horizontale par ligne, en % du total."""
    h, g = 28, 100
    out = []
    for k, (lab, vals, tot) in enumerate(lignes):
        y = 8 + k * h
        out.append(f'<text x="0" y="{y + 14}">{e(lab)}</text>')
        x = g
        for v, c in zip(vals, classes):
            w = (largeur - g - 10) * (v / tot if tot else 0)
            if w > 0:
                out.append(f'<rect class="{c}" x="{x:.1f}" y="{y}" width="{w:.1f}" height="18"><title>{e(lab)} : {v}</title></rect>')
                if w > 22:
                    out.append(f'<text x="{x + w / 2:.1f}" y="{y + 13}" text-anchor="middle" style="fill:var(--paper)">{v}</text>')
            x += w
    H = 8 + len(lignes) * h
    return f'<svg viewBox="0 0 {largeur} {H}" role="img">{"".join(out)}</svg>'


def barres_groupees(groupes, series, classes, maxi=None, largeur=520, unite="", lg="fr"):
    """groupes : étiquettes ; series : [[valeur par groupe]…] ; barres verticales côte à côte."""
    H, bas, gauche = 210, 170, 30
    maxi = maxi or max([v for s in series for v in s if v is not None] + [1])
    lg = (largeur - gauche - 10) / max(1, len(groupes))
    bw = min(26, (lg - 10) / max(1, len(series)))
    out = [f'<line class="ax" x1="{gauche}" y1="{bas}" x2="{largeur - 5}" y2="{bas}"/>']
    for gi, lab in enumerate(groupes):
        x0 = gauche + gi * lg + (lg - bw * len(series)) / 2
        for si, s in enumerate(series):
            v = s[gi]
            if v is None:
                continue
            hh = (bas - 20) * v / maxi
            out.append(f'<rect class="{classes[si]}" x="{x0 + si * bw:.1f}" y="{bas - hh:.1f}" width="{bw - 2:.1f}" height="{hh:.1f}"><title>{e(lab)} : {nombre(v, lg)}{unite}</title></rect>')
            out.append(f'<text x="{x0 + si * bw + (bw - 2) / 2:.1f}" y="{bas - hh - 4:.1f}" text-anchor="middle" class="mu">{nombre(v, lg)}</text>')
        out.append(f'<text x="{gauche + gi * lg + lg / 2:.1f}" y="{bas + 16}" text-anchor="middle">{e(lab)}</text>')
    return f'<svg viewBox="0 0 {largeur} {H}" role="img">{"".join(out)}</svg>'


def courbes(xs, series, classes, maxi=100, largeur=520, unite=" %"):
    H, bas, haut, gauche = 200, 170, 12, 34
    n = len(xs)
    def X(i):
        return gauche + (largeur - gauche - 10) * (i / (n - 1) if n > 1 else 0)
    def Y(v):
        return bas - (bas - haut) * v / maxi
    out = []
    for p in (0, maxi / 2, maxi):
        out.append(f'<line class="ax" x1="{gauche}" y1="{Y(p):.1f}" x2="{largeur - 10}" y2="{Y(p):.1f}"/><text x="0" y="{Y(p) + 4:.1f}" class="mu">{p:g}</text>')
    for s, c in zip(series, classes):
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(s) if v is not None)
        out.append(f'<polyline class="{c.replace("c", "s")}" fill="none" stroke-width="2.2" points="{pts}"/>')
        if s and s[-1] is not None:
            out.append(f'<circle class="{c}" cx="{X(n - 1):.1f}" cy="{Y(s[-1]):.1f}" r="3.5"/>')
    for i in sorted({0, n - 1, n // 2}):
        if 0 <= i < n:
            out.append(f'<text x="{X(i):.1f}" y="{bas + 18}" text-anchor="middle" class="mu">{e(xs[i])}</text>')
    return f'<svg viewBox="0 0 {largeur} {H}" role="img">{"".join(out)}</svg>'


def nombre(v, lg):
    s = f"{v:g}"
    return s.replace(".", ",") if lg == "fr" else s


def legende(noms, classes):
    return '<div class="inst-leg">' + "".join(f'<span><i class="{c}"></i>{e(n)}</span>' for n, c in zip(noms, classes)) + "</div>"


# ---------------------------------------------------------------- les graphiques

def region_nom(r, lg):
    return A.REGION_EN.get(REGIONS[r], REGIONS[r]) if lg == "en" else REGIONS[r]


def corps_graphique(gid, j, js, t, lg, noms):
    if gid == "foi":
        tot = [sum(r[k] for r in j["foi"]) for k in range(3)]
        lignes = [(t["total"], tot, sum(tot))] + [(region_nom(r, lg), j["foi"][r], sum(j["foi"][r])) for r in range(6)]
        s = legende([t["foi_croy"], t["foi_agn"], t["foi_ath"]], ["c0", "c1", "c2"]) + barres_empilees(lignes, ["c0", "c1", "c2"])
        p, q = j.get("foiPays") or [None, None]
        if p is not None and q is not None:
            s += f'<p class="m">{e(t["foi_note"].format(p=p, q=q))}</p>'
        return s
    if gid == "foi-courbe":
        xs = [x["jourEre"] for x in js]
        cr = [round(100 * sum(r[0] for r in x["foi"]) / x["n"], 1) if x["n"] else None for x in js]
        at = [round(100 * sum(r[2] for r in x["foi"]) / x["n"], 1) if x["n"] else None for x in js]
        return legende([t["foi_croy"], t["foi_ath"]], ["c0", "c2"]) + courbes(xs, [cr, at], ["c0", "c2"]) + f'<p class="m">{e(t["jours"])} · {e(t["pct"])}</p>'
    if gid == "politique":
        groupes = [region_nom(r, lg) for r in range(6)]
        series = [[j["politique"][r][k] for r in range(6)] for k in range(3)]
        tot = [sum(s) for s in series]
        reg = j.get("regime") or ""
        reg = REGIMES_EN.get(reg, reg) if lg == "en" else reg
        return (legende([f'{t["pol_vote"]} ({tot[0]})', f'{t["pol_reb"]} ({tot[1]})', f'{t["pol_cen"]} ({tot[2]})'], ["c2", "c3", "c0"])
                + barres_groupees(groupes, series, ["c2", "c3", "c0"], maxi=20, lg=lg) + f'<p class="m">{e(t["regime_ce_soir"].format(r=reg))}</p>'
                + (f'<p class="m">{e(t["reb_note"].format(r=j["rebellesPays"], s=tot[1]))}</p>' if j.get("rebellesPays") is not None and j["rebellesPays"] != tot[1] else ""))
    if gid == "politique-courbe":
        xs = [x["jourEre"] for x in js]
        so = [round(100 * sum(r[0] for r in x["politique"]) / x["n"], 1) if x["n"] else None for x in js]
        re = [round(100 * sum(r[1] for r in x["politique"]) / x["n"], 1) if x["n"] else None for x in js]
        runs = []
        for x in js:
            r = x.get("regime") or "?"
            r = REGIMES_EN.get(r, r) if lg == "en" else r
            if runs and runs[-1][0] == r:
                runs[-1][2] = x["jourEre"]
            else:
                runs.append([r, x["jourEre"], x["jourEre"]])
        reg = "".join(f'<li>{e(r)} : {e(t["du_au"].format(a=a, b=b))}</li>' for r, a, b in runs)
        return (legende([t["pol_vote"], t["pol_reb"]], ["c2", "c3"]) + courbes(xs, [so, re], ["c2", "c3"]) + f'<p class="m">{e(t["jours"])} · {e(t["pct"])}</p>'
                + f'<h3>{e(t["regimes"])}</h3><ul>{reg}</ul>')
    if gid == "sondage":
        els = [x for x in js if x.get("election")]
        avec = [x for x in els if x["election"].get("sondage")]
        s = ""
        if avec:
            der = avec[-1]
            el = der["election"]
            cands = el["candidats"]
            groupes = [c[1] or f"n° {c[0]}" for c in cands]
            s += legende([t["sondage"], t["urnes"]], ["c1", "c2"]) + barres_groupees(groupes, [list(el["sondage"]), [c[4] for c in cands]], ["c1", "c2"], unite=" %", lg=lg)
            s += f'<p class="m">{e(t["election_du"].format(d=A.date_longue(der["date"], lg), h=el.get("heure"), e=el.get("exprimes"), i=el.get("inscrits"), a=el.get("abstentions"), b=el.get("blancs")))}</p>'
            ecarts = []
            for x in avec:
                el = x["election"]
                d = [abs(a - c[4]) for a, c in zip(el["sondage"], el["candidats"]) if a is not None and c[4] is not None]
                ecarts.append((x["date"], round(sum(d) / len(d), 1) if d else None))
            s += f'<h3>{e(t["ecart"])}</h3><ul>' + "".join(f'<li>{e(A.date_longue(dd, lg))}{" :" if lg == "fr" else ":"} {nombre(v, lg)} {e(t["pts"])}</li>' for dd, v in ecarts if v is not None) + "</ul>"
        s += f'<p class="m">{e(t["bourdieu"])}</p>'
        return s
    if gid == "humeur":
        groupes = t["tr"]
        series = [j["humeur"]["satisfaction"], j["humeur"]["colere"], j["humeur"]["peur"]]
        return legende([t["sat"], t["col"], t["peur"]], ["c2", "c3", "c0"]) + barres_groupees(groupes, series, ["c2", "c3", "c0"], lg=lg)
    if gid == "notoriete":
        lignes = []
        for i, v in j["notoriete"]:
            nom = noms.get(i) or (f"Citizen No. {i}" if lg == "en" else f"citoyen n° {i}")
            r = region_nom((i - 1) // 20, lg)
            lignes.append(f"<li>{e(nom)} ({e(r)}, n° {i}) : {v:g}</li>" if lg == "fr" else f"<li>{e(nom)} ({e(r)}, No. {i}): {v:g}</li>")
        return "<ol>" + "".join(lignes) + "</ol>"
    if gid == "economie":
        ec = j["economie"]
        groupes = [region_nom(r, lg) for r in range(6)]
        s = legende([t["octets"]], ["c2"]) + barres_groupees(groupes, [[x[0] for x in ec["regions"]]], ["c2"], lg=lg)
        if ec.get("chomage"):
            s += legende([t["sansemploi"]], ["c3"]) + barres_groupees(groupes, [[x[2] for x in ec["regions"]]], ["c3"], lg=lg)
        v = ec.get("valeurOctet")
        if isinstance(v, list) and len(v) == 6:
            s += legende([t["valeur"]], ["c0"]) + barres_groupees(groupes, [[round(x, 2) if isinstance(x, (int, float)) else None for x in v]], ["c0"], lg=lg)
        return s
    return ""


def directeur_html(arch, j, js, t, lg, noms):
    d = arch.get("directeur")
    if not d:
        return ""
    r = region_nom((d["id"] - 1) // 20, lg)
    qui = t["dir_qui"].format(nom=d.get("nom") or noms.get(d["id"]) or ("Citizen" if lg == "en" else "Citoyen"), n=d["id"], r=r, d=A.date_longue(d["date"], lg))
    tot = [sum(x[k] for x in j["foi"]) for k in range(3)]
    vo = sum(x[0] for x in j["politique"])
    re = sum(x[1] for x in j["politique"])
    dr = ""
    if len(js) >= 2:
        avant = sum(x[1] for x in js[-2]["politique"])
        if re != avant:
            dr = t["dr_plus"].format(x=re - avant)
    l1 = t["dir1"][int(j.get("jourEre") or 0) % len(t["dir1"])]
    if j.get("president") == d["id"]:
        l1 = t["dir_pres"]
    l2 = t["dir2"].format(c=tot[0], g=tot[1], a=tot[2], n=j["n"], v=vo, r=re, dr=dr)
    return (f'<div class="inst-dir"><h2>{e(t["directeur"])}</h2><p>{e(l1)}</p><p>{e(l2)}</p>'
            f'<p><small>{e(qui)}. {e(t["dir_tirage"].format(d=A.date_longue(d["date"], lg), h=d["sha256"][:12]))}</small></p></div>')


def page(arch, latest, noms, lg, ouverte):
    t, P = T[lg], A.L[lg]
    pre = "../" if lg == "en" else ""
    autre_lg, autre_nom, autre_rss, autre_titre = P["autre"]
    fr_url, en_url = BASE + "institut.html", BASE + "en/institut.html"
    liens = ["./", "archives.html", "histoire.html", "langue.html", "citoyen.html", "ambassade.html", "tourisme.html", "temple.html", "recherche.html", "projet.html", pre + P["rss"]]
    nav = "\n".join(f'    <a href="{h}">{e(x)}</a>' for h, x in zip(liens, P["menu"]))
    ere = int(latest.get("ere") or 1)
    js = [x for x in arch.get("jours", []) if x.get("ere", ere) == ere]
    corps = [f'<p class="inst-slogan">{e(t["slogan"][0])}<br>{e(t["slogan"][1])}</p>']
    script = ""
    if not ouverte or not js:
        corps.append(f'<p>⏳ {e(t["attente"])}</p>')
    else:
        j = js[-1]
        corps.append(f'<p class="compte">{e(t["soir"].format(d=A.date_longue(j["date"], lg), n=j.get("edition"), c=j["n"]))}</p>')
        corps.append(directeur_html(arch, j, js, t, lg, noms))
        options, sommaire, sections = [], [], []
        for gid, besoin in GRAPHIQUES:
            nom = t["g"][gid][0]
            if besoin is None or not besoin(j, js):
                options.append(f'<option value="{gid}" disabled>⏳ {e(nom)} ({e(t["attente_court"])})</option>')
                sommaire.append(f'<li class="inst-off">⏳ {e(nom)} ({e(t["attente_court"])})</li>')
                continue
            titre, sous, methode, question = t["g"][gid]
            options.append(f'<option value="{gid}">{e(nom)}</option>')
            sommaire.append(f'<li><a href="#g-{gid}">{e(nom)}</a></li>')
            sections.append(f'<section class="inst-g" id="g-{gid}"><h2>{e(titre)}</h2><p>{e(sous)}</p>{corps_graphique(gid, j, js, t, lg, noms)}'
                            f'<p class="m"><b>{e(t["methode"])} :</b> {e(methode)}</p>' if lg == "fr" else
                            f'<section class="inst-g" id="g-{gid}"><h2>{e(titre)}</h2><p>{e(sous)}</p>{corps_graphique(gid, j, js, t, lg, noms)}'
                            f'<p class="m"><b>{e(t["methode"])}:</b> {e(methode)}</p>')
            sections[-1] += f'<p class="q"><b>{e(t["question"])} :</b> {e(question)}</p></section>' if lg == "fr" else f'<p class="q"><b>{e(t["question"])}:</b> {e(question)}</p></section>'
        corps.append(f'<div class="inst-cmd" id="inst-cmd" hidden><label for="inst-choix">{e(t["choisir"])}</label> <select id="inst-choix">{"".join(options)}</select></div>')
        corps.append(f'<nav id="inst-sommaire" aria-label="{e(t["sommaire"])}"><h2>{e(t["sommaire"])}</h2><ul>{"".join(sommaire)}</ul></nav>')
        corps.extend(sections)
        brut = f'<a href="{A.DONNEES}donnees/ere-{ere:03d}/quotidien/{e(j["date"])}.json">{e(t["brut"])}</a>'
        lien_arch = '<a href="' + pre + 'institut.json">' + e(t["arch"]) + '</a>'
        corps.append(f'<p>{t["verifier"].format(brut=brut, arch=lien_arch)}</p><p>{t["voir"]}</p>')
        script = JS
    maj = P["maj_le"].format(n=latest.get("day", "?"), d=A.date_longue(str(latest.get("date", "")), lg))
    return f"""<!doctype html>
<html lang="{lg}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<link rel="icon" href="{pre}favicon.ico" sizes="32x32">
<link rel="icon" href="{pre}favicon.svg" type="image/svg+xml">
<title>{e(t["titre"])} — Microcontrôland</title>
<meta name="description" content="{e(t["desc"])}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="La Puce Libre — Microcontrôland">
<meta property="og:title" content="{e(t["titre"])} — Microcontrôland">
<meta property="og:description" content="{e(t["desc"])}">
<link rel="alternate" hreflang="fr" href="{fr_url}">
<link rel="alternate" hreflang="en" href="{en_url}">
<link rel="alternate" hreflang="x-default" href="{fr_url}">
<link rel="alternate" type="application/rss+xml" title="La Puce Libre" href="{pre}{P["rss"]}">
<link rel="alternate" type="application/rss+xml" title="{e(autre_titre)}" hreflang="{autre_lg}" href="{pre}{autre_rss}">
<link rel="alternate" type="application/json" href="{pre}institut.json">
<link rel="stylesheet" href="{pre}style.css">
<script src="{pre}mesure.js" defer></script>
{STYLE}
</head>
<body>
<div class="wrap">
  <header class="mast">
    <div class="top"><span>{e(P["mast"][0])}</span><span>{e(t["titre"])}</span></div>
    <div class="title"><a href="./">La Puce <span>Libre</span></a></div>
    <p class="tag">{e(P["tag"])}</p>
  </header>
  <nav class="main" aria-label="Navigation">
{nav}
  </nav>

  <div class="prose">
    <p class="compte">{e(t["haut"])}</p>
    <h1>{e(t["titre"])}</h1>
    <p class="chapo">{e(t["chapo"])}</p>
    {"".join(corps)}
    <p><small>{e(t["pied"])}</small></p>
    <p><small>{e(maj)}</small></p>
  </div>

  <footer class="site">
    <span><a href="./">{e(P["retour"])}</a></span>
    <span><a href="{'en/' if lg == 'fr' else '../'}institut.html">{e(autre_nom)}</a></span>
    <span><a href="mentions.html">{e(P["mentions"])}</a></span>
  </footer>
</div>
{'<script>window.MCL_BASE = "../";</script>' if lg == "en" else ""}
<script src="{pre}reglages.js"></script>
<script src="{pre}commun.js"></script>
<script src="{pre}lang.js"></script>
{script}
</body>
</html>
"""


# ---------------------------------------------------------------- programme

def ouverte(latest):
    etapes = (latest.get("ages") or {}).get("etapes") or []
    return len(etapes) > ETAT_CIVIL and bool(etapes[ETAT_CIVIL].get("ouvert"))


def lire_noms(racine):
    d = A.lire(racine / "data" / "citoyens.json", {}) if (racine / "data" / "citoyens.json").exists() else {}
    noms = {}
    for c in d.get("citoyens") or []:
        if isinstance(c, list) and len(c) > 1:
            noms[c[0]] = c[1]
    return noms


def mettre_a_jour(racine, source, attendre=0):
    chemin = racine / "institut.json"
    arch = A.lire(chemin, None) if chemin.exists() else None
    arch = arch or {"format": 1, "jours": []}
    jours = arch["jours"]
    latest = A.lire(racine / "data" / "latest.json", {})
    noms = lire_noms(racine)
    ok = ouverte(latest)
    ajoutes = 0
    if not ok:
        print("institut : l'âge de l'État civil n'est pas ouvert, rien n'est calculé (audit des déblocages)")
    else:
        ere = int(latest.get("ere") or 1)
        fin = time.time() + attendre
        while True:
            fichiers = [f for f in A.manifeste(source, ere) if f.get("fichier")]
            if not attendre or latest.get("date") in {f.get("date") for f in fichiers} or time.time() > fin:
                break
            print("Fichier brut du soir pas encore publié : nouvel essai dans 60 s")
            time.sleep(60)
        fichiers = sorted((f for f in fichiers if "/quotidien/" in f.get("fichier", "")), key=lambda x: x.get("date") or "")
        derniere = max((j["date"] for j in jours if j.get("ere") == ere), default="")
        # Premier passage de l'ère : tous les bruts déjà publiés sont calculés une fois (courbes de l'ère) ; ensuite, les nouveaux seulement.
        for f in [f for f in fichiers if f.get("date", "") > derniere]:
            try:
                octets = A.charger(source, f["fichier"])
                if f.get("sha256") and hashlib.sha256(octets).hexdigest() != f["sha256"]:
                    raise ValueError("empreinte différente du manifeste")
                brut = json.loads(octets)
            except Exception as err:
                print(f"Illisible : {f.get('fichier')} ({err}) ; nouvel essai au prochain passage", file=sys.stderr)
                break    # on n'expose jamais un soir avant le précédent
            if not brut.get("citoyens"):
                continue
            ent = chiffres(brut)
            ent["ere"] = ere
            ent["source"] = f["fichier"]
            ent["sha256"] = hashlib.sha256(octets).hexdigest()
            jours.append(ent)
            ajoutes += 1
        dirs = arch.setdefault("directeurs", [])
        if jours and not any(d.get("ere") == ere for d in dirs):
            der = [j for j in jours if j.get("ere") == ere][-1]
            n = int(der["sha256"], 16) % 120 + 1
            dirs.append({"ere": ere, "id": n, "nom": noms.get(n), "date": der["date"], "sha256": der["sha256"]})
            ajoutes += 1
        arch["directeur"] = next((d for d in dirs if d.get("ere") == ere), None)
        if ajoutes:
            chemin.write_text(json.dumps(arch, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    (racine / "institut.html").write_text(page(arch, latest, noms, "fr", ok), encoding="utf-8")
    (racine / "en").mkdir(exist_ok=True)
    (racine / "en" / "institut.html").write_text(page(arch, latest, noms, "en", ok), encoding="utf-8")
    print(f"institut : {ajoutes} ajout(s), {len(jours)} soir(s) au total")
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
