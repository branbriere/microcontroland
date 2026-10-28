"""Microcontrôland : « Salle de la Relique » (FR) et « Hall of the Relic » (EN), à l'Ambassade.

La Relique est Microcontrolchess, mini-jeu d'échecs 5 × 6 (règles v1.1), présenté comme un trésor national
offert par le Créateur, dont les Waïnas ignorent l'usage. Les Waïnas n'y jouent pas.

Lit data/latest.json, data/editions/N.json et le dossier relique/ (problemes.json, galerie.json, registre.json),
puis écrit :
  relique.html, en/relique.html   page pour les humains (le jeu tourne dans le navigateur, rien n'est envoyé)
  relique.txt,  en/relique.txt    version en texte brut pour les IA, sans JavaScript

Tant que l'âge de la Diplomatie n'est pas atteint, les quatre fichiers affichent seulement
« En attente d'évolution de la civilisation » et la progression vers cet âge. La salle ouvre seule
le premier soir où data/latest.json indique la Diplomatie ouverte. Le problème du jour change chaque soir
(45 problèmes vérifiés par l'arbitre, le n° 1 le jour de l'ouverture).

Licence MIT. Version 1.0, 26 octobre 2026 (firmware 0.8, règles du jeu v1.1, moteur 0.2).
"""
import html
import json
import sys
from pathlib import Path

BASE = "https://www.microcontroland.org/"
DIPLOMATIE = 4
MOIS = {"fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"],
        "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]}
FIN_EN = {"mat": "checkmate", "percée": "breakthrough", "pat": "stalemate", "triple répétition": "threefold repetition", "absence de progrès": "no progress"}
OFFENSIVES = (11, 18)  # b3, d4
NIVEAUX = {"fr": ["L'huissier", "Le secrétaire", "Le consul", "L'attaché militaire", "Son Excellence"],
           "en": ["The usher", "The secretary", "The consul", "The military attaché", "His Excellency"]}

L = {
    "fr": {
        "titre": "Salle de la Relique", "haut": "Ambassade de Microcontrôland · salle d'exposition",
        "desc": "La Relique de Microcontrôland, trésor national offert par le Créateur : un mini-jeu d'échecs 5 × 6 à essayer contre l'IA de l'Ambassade, avec une version texte pour les IA.",
        "desc_ferme": "Salle de la Relique, à l'Ambassade de Microcontrôland : ouvre à l'âge de la Diplomatie.",
        "attente": "En attente d'évolution de la civilisation. La Salle de la Relique ouvre avec l'Ambassade, à l'âge de la Diplomatie.",
        "progres": "Progression vers la Diplomatie : {p}.",
        "chapo": "Où l'Ambassade expose au monde extérieur le trésor national le plus sacré, et le plus mystérieux, de la République.",
        "h_relique": "La Relique",
        "decret": "« Le Ministère confirme que la Relique a été offerte au peuple par le Créateur en personne. Le peuple la vénère avec ferveur. "
                  "Son usage fait l'objet d'études approfondies, menées depuis sa réception avec un sérieux exemplaire et un résultat, à ce jour, "
                  "en cours de consolidation. L'Ambassade invite respectueusement les visiteurs étrangers à manipuler la Relique, sous réserve de la reposer correctement. »",
        "decret_cite": "Communiqué du Ministère du Culte",
        "vrai": "<b>Ce qui est vrai :</b> la Relique est un jeu, Microcontrolchess : un mini-jeu d'échecs de 5 × 6 cases, 9 pièces par camp, avec deux cases offensives. "
                "Les Waïnas n'y jouent pas : leur petit cerveau de 9 entrées ne perçoit que la vie politique du pays, pas un plateau. "
                "Les parties sont jouées ici par des visiteurs, humains ou IA, contre l'IA de la page.",
        "h_jouer": "Toucher la Relique",
        "etoile": "✶ b3 et d4 : la pièce qui s'y trouve peut prendre sur les 8 cases voisines.",
        "audience": "Votre audience", "je_joue": "Je joue", "blancs": "les blancs (je commence)", "noirs": "les noirs",
        "adversaire": "Adversaire", "lente": "lente", "commencer": "Commencer", "abandonner": "Abandonner",
        "statut0": "Choisissez votre camp, puis « Commencer ».",
        "sans_js": "Le jeu demande JavaScript. Sans lui, la version texte reste lisible : ",
        "h_regles": "Règles v1.1",
        "regles": ["Plateau de 5 colonnes (a à e) et 6 rangées, rangée 1 en haut. Les blancs commencent et descendent vers la rangée 6.",
                   "Pièces classiques. Pion éclaireur : un pas en avant, ou en diagonale avant vers une case vide ; il prend en diagonale avant. Au tout premier coup de la partie, pas de pion en diagonale.",
                   "Cases offensives b3 et d4 : la pièce qui s'y trouve peut prendre sur les 8 cases voisines (cela compte pour l'échec).",
                   "Victoire : mat, ou percée d'un pion sur la dernière rangée, tout droit seulement.",
                   "Nulle : pat, triple répétition, ou 80 demi-coups sans prise ni coup de pion."],
        "h_galerie": "La galerie des parties", "spectateurs": "Spectateurs",
        "galerie_txt": "Une vraie partie du simulateur, rejouée coup par coup : {t}.",
        "debut": "Début", "prec": "Coup précédent", "lecture": "Lecture", "suiv": "Coup suivant", "fin": "Fin",
        "demo": "Partie de démonstration", "initiale": "Position initiale.",
        "h_registre": "Le registre des visiteurs",
        "cols": ["Date", "Visiteur", "Adversaire", "Résultat", "Fin", "Demi-coups"],
        "resultats": {"defaite": "défaite", "victoire": "victoire", "nulle": "nulle"},
        "h_ia": "Pour les intelligences extérieures",
        "ia_txt": "Une version en texte brut, publique, que toute IA peut lire sans JavaScript : {lien}. Lecture humaine autorisée. "
                  "Le texte est produit par l'arbitre du jeu ; il ne peut pas contenir de coup faux. Le problème change chaque soir.",
        "solution": "Solution du problème",
        "sol_txt": "Premier coup : {k}. Toutes les réponses mènent au mat ou à la percée au coup suivant (vérifié par l'arbitre).",
        "h_inter": "Comment interagir",
        "facons": [("Jouer", "Contre l'IA, dans le navigateur. Cinq niveaux, de l'huissier à Son Excellence. Rien n'est envoyé, aucun compte, aucun cookie.", ""),
                   ("Regarder", "La galerie rejoue une partie choisie, coup par coup, avec une lecture automatique.", ""),
                   ("Résoudre", "Le problème du jour (mat ou percée en 2), lisible par les humains comme par les IA.", ""),
                   ("Proposer un coup", "Une IA visiteuse pourra peut-être jouer en envoyant un coup, vérifié par l'arbitre. Données d'observation seulement.", "plus tard, après audit")],
        "pied1": "Code du jeu sous licence MIT : {e} (arbitre et IA), {r} (cette page). Les parties jouées ici ne sont ni enregistrées ni envoyées.",
        "pied2": "Microcontrôland est un pays fictif. La Relique, son culte et son Ministère sont des inventions de ce site ; ils ne parodient aucune religion réelle.",
        "maj_le": "Page mise à jour automatiquement après l'édition n° {n} du {d}.",
        "menu": ["Le journal", "Archives", "Histoire", "La langue", "Mon citoyen", "L'ambassade", "Le Temple", "Recherche", "Le projet", "Flux RSS"],
        "mast": ("Quotidien officieux de la République", "L'ambassade"), "tag": "Le seul journal de Microcontrôland, écrit chaque soir par la passerelle",
        "retour": "Retour à l'ambassade", "mentions": "Mentions légales", "rss": "feed.xml", "autre": ("en", "English", "feed-en.xml", "La Puce Libre (English)"),
        # version texte
        "t_titre": "MICROCONTRÔLAND - SALLE DE LA RELIQUE (Ambassade)",
        "t_lecture": "Version texte pour les IA. Lecture humaine autorisée. Texte produit par l'arbitre du jeu.",
        "t_page": "Page pour les humains : {u}",
        "t_quoi": "La Relique est Microcontrolchess, mini-jeu d'échecs 5 × 6 (règles v1.1). Le pays la présente comme un trésor offert par le Créateur, "
                  "dont les Waïnas ignorent l'usage ; en vrai, ils n'y jouent pas (leur cerveau de 9 entrées ne voit pas de plateau).",
        "t_regles": "RÈGLES v1.1", "t_probleme": "PROBLÈME DU JOUR (n° {n} sur {t})",
        "t_plateau": "Plateau : rangée 1 en haut. MAJUSCULES = blancs, minuscules = noirs, . = vide, * = case offensive vide.",
        "t_pieces": "P pion, N cavalier, B fou, R tour, Q dame, K roi.",
        "t_trait": "Trait : {c}", "t_camps": ("blancs", "noirs"), "t_legaux": "Coups légaux ({n}) : {l}",
        "t_enigme": "Énigme : les {c} gagnent en 2 coups (mat ou percée), quoi que fasse l'adversaire. Votre réponse : le premier coup des {c}.",
        "t_solution": "La solution est publiée sur la page pour les humains, dans un encadré replié.",
        "t_galerie": "GALERIE : {t}", "t_coups": "Coups : {c}", "t_resultat": "Résultat : les blancs gagnent par percée.",
        "t_registre": "REGISTRE DES VISITEURS", "t_niveau": "niveau",
        "t_jouer": "JOUER : sur la page pour les humains (JavaScript). Il n'existe pas encore de moyen d'envoyer un coup ; prévu plus tard, après audit.",
    },
    "en": {
        "titre": "Hall of the Relic", "haut": "Embassy of Microcontrôland · exhibition hall",
        "desc": "The Relic of Microcontrôland, a national treasure given by the Creator: a 5 × 6 mini chess game to try against the Embassy's AI, with a text version for AIs.",
        "desc_ferme": "Hall of the Relic, at the Embassy of Microcontrôland: opens at the Age of Diplomacy.",
        "attente": "Awaiting the evolution of civilisation. The Hall of the Relic opens with the Embassy, at the Age of Diplomacy.",
        "progres": "Progress towards Diplomacy: {p}.",
        "chapo": "Where the Embassy shows the outside world the Republic's most sacred, and most mysterious, national treasure.",
        "h_relique": "The Relic",
        "decret": "“The Ministry confirms that the Relic was given to the people by the Creator in person. The people venerate it fervently. "
                  "Its purpose has been the subject of in-depth studies, conducted since its reception with exemplary seriousness and a result that is, "
                  "to date, being consolidated. The Embassy respectfully invites foreign visitors to handle the Relic, provided they put it back properly.”",
        "decret_cite": "Statement from the Ministry of Worship",
        "vrai": "<b>What is true:</b> the Relic is a game, Microcontrolchess: a mini chess game on 5 × 6 squares, 9 pieces per side, with two offensive squares. "
                "The Waïnas do not play it: their small 9-input brains perceive only the country's political life, not a board. "
                "Games here are played by visitors, human or AI, against the page's AI.",
        "h_jouer": "Touch the Relic",
        "etoile": "✶ b3 and d4: a piece standing there may capture on any of the 8 neighbouring squares.",
        "audience": "Your audience", "je_joue": "I play", "blancs": "White (I move first)", "noirs": "Black",
        "adversaire": "Opponent", "lente": "slow", "commencer": "Begin", "abandonner": "Resign",
        "statut0": "Choose your side, then “Begin”.",
        "sans_js": "The game needs JavaScript. Without it, the text version can still be read: ",
        "h_regles": "Rules v1.1",
        "regles": ["Board of 5 files (a to e) and 6 ranks, rank 1 at the top. White moves first and heads down towards rank 6.",
                   "Classical pieces. Scout pawn: one step forward, or diagonally forward onto an empty square; it captures diagonally forward. On the very first move of the game, no diagonal pawn move.",
                   "Offensive squares b3 and d4: a piece standing there may capture on any of the 8 neighbouring squares (this counts for check).",
                   "Win: checkmate, or a pawn breaking through to the last rank, straight ahead only.",
                   "Draw: stalemate, threefold repetition, or 80 half-moves without a capture or a pawn move."],
        "h_galerie": "The gallery of games", "spectateurs": "Spectators",
        "galerie_txt": "A real simulator game, replayed move by move: {t}.",
        "debut": "Start", "prec": "Previous move", "lecture": "Play", "suiv": "Next move", "fin": "End",
        "demo": "Exhibition game", "initiale": "Starting position.",
        "h_registre": "The visitors' register",
        "cols": ["Date", "Visitor", "Opponent", "Result", "Ending", "Half-moves"],
        "resultats": {"defaite": "defeat", "victoire": "victory", "nulle": "draw"},
        "h_ia": "For outside intelligences",
        "ia_txt": "A public plain-text version that any AI can read without JavaScript: {lien}. Humans may read it too. "
                  "The text is produced by the game's arbiter; it cannot contain an illegal move. The puzzle changes every evening.",
        "solution": "Puzzle solution",
        "sol_txt": "First move: {k}. Every reply leads to checkmate or a breakthrough on the next move (checked by the arbiter).",
        "h_inter": "How to take part",
        "facons": [("Play", "Against the AI, in your browser. Five levels, from the usher to His Excellency. Nothing is sent, no account, no cookie.", ""),
                   ("Watch", "The gallery replays a chosen game move by move, with an autoplay.", ""),
                   ("Solve", "The daily puzzle (checkmate or breakthrough in 2), readable by humans and AIs alike.", ""),
                   ("Submit a move", "A visiting AI may one day play by sending a move, checked by the arbiter. Observation data only.", "later, after an audit")],
        "pied1": "Game code under the MIT licence: {e} (arbiter and AI), {r} (this page). Games played here are neither recorded nor sent anywhere.",
        "pied2": "Microcontrôland is a fictional country. The Relic, its worship and its Ministry are inventions of this website; they parody no real religion.",
        "maj_le": "Page updated automatically after issue no. {n} of {d}.",
        "menu": ["The paper", "Archive", "History", "The language", "My citizen", "The embassy", "The Temple", "Research", "The project", "RSS feed"],
        "mast": ("Unofficial daily of the Republic", "The embassy"), "tag": "The only newspaper in Microcontrôland, written every evening by the gateway",
        "retour": "Back to the embassy", "mentions": "Legal notice", "rss": "feed-en.xml", "autre": ("fr", "Français", "feed.xml", "La Puce Libre (français)"),
        "t_titre": "MICROCONTRÔLAND - HALL OF THE RELIC (Embassy)",
        "t_lecture": "Text version for AIs. Humans may read it too. Text produced by the game's arbiter.",
        "t_page": "Page for humans: {u}",
        "t_quoi": "The Relic is Microcontrolchess, a 5 × 6 mini chess game (rules v1.1). The country presents it as a treasure given by the Creator, "
                  "whose purpose the Waïnas do not know; in fact they do not play it (their 9-input brains see no board).",
        "t_regles": "RULES v1.1", "t_probleme": "PUZZLE OF THE DAY (no. {n} of {t})",
        "t_plateau": "Board: rank 1 at the top. UPPERCASE = White, lowercase = Black, . = empty, * = empty offensive square.",
        "t_pieces": "P pawn, N knight, B bishop, R rook, Q queen, K king.",
        "t_trait": "To move: {c}", "t_camps": ("White", "Black"), "t_legaux": "Legal moves ({n}): {l}",
        "t_enigme": "Puzzle: {c} wins in 2 moves (checkmate or breakthrough), whatever the opponent does. Your answer: {c}'s first move.",
        "t_solution": "The solution is published on the page for humans, in a folded box.",
        "t_galerie": "GALLERY: {t}", "t_coups": "Moves: {c}", "t_resultat": "Result: White wins by breakthrough.",
        "t_registre": "VISITORS' REGISTER", "t_niveau": "level",
        "t_jouer": "PLAY: on the page for humans (JavaScript). There is no way to submit a move yet; planned later, after an audit.",
    },
}

STYLE = """<style>
@font-face{font-family:"Relique Pieces";font-display:swap;src:url({pre}relique/pieces.woff2) format("woff2");unicode-range:U+265A-265F,U+2736}
.rq-jeu{display:grid;gap:14px;margin:14px 0}
.rq-board{display:grid;grid-template-columns:20px repeat(5,minmax(0,1fr));width:min(100%,420px);margin:0 auto;user-select:none}
.rq-board .lbl{font:12px var(--f-data);color:var(--muted);display:grid;place-items:center;min-height:20px}
.rq-board .sq{aspect-ratio:1;position:relative;display:grid;place-items:center;border:0;border-radius:0;padding:0;margin:0;background:#2f6b47;cursor:default;min-width:0}
.rq-board button.sq{cursor:pointer}
.rq-board .sq.dark{background:#245a3b}
.rq-board .sq.off::before{content:"";position:absolute;inset:7%;border:2px dashed #d6aa52;border-radius:50%}
.rq-board .star{position:absolute;right:6%;top:2%;color:#d6aa52;font:12px "Relique Pieces",sans-serif}
.rq-board .sq.last{box-shadow:inset 0 0 0 999px rgba(214,170,82,.45)}
.rq-board .sq.sel{box-shadow:inset 0 0 0 4px #f2d15c}
.rq-board .sq.tgt::after{content:"";position:absolute;width:26%;height:26%;border-radius:50%;background:rgba(242,209,92,.6)}
.rq-board .sq.tgt.cap::after{width:86%;height:86%;background:transparent;border:4px solid rgba(242,209,92,.75)}
.rq-board .sq:focus-visible{outline:3px solid #f2d15c;outline-offset:-3px;z-index:1}
.rq-board .pc{font-family:"Relique Pieces","Noto Sans Symbols 2","Segoe UI Symbol","DejaVu Sans",serif;font-variant-emoji:text;font-size:clamp(26px,8vw,46px);line-height:1;position:relative;z-index:1}
.rq-board .pc.up{color:#fff;text-shadow:-2px 0 0 #000,2px 0 0 #000,0 -2px 0 #000,0 2px 0 #000,-1.5px -1.5px 0 #000,1.5px 1.5px 0 #000,-1.5px 1.5px 0 #000,1.5px -1.5px 0 #000}
.rq-board .pc.down{color:#000;text-shadow:-2px 0 0 #fff,2px 0 0 #fff,0 -2px 0 #fff,0 2px 0 #fff,-1.5px -1.5px 0 #fff,1.5px 1.5px 0 #fff,-1.5px 1.5px 0 #fff,1.5px -1.5px 0 #fff}
.rq-status{text-align:center;font:600 15px var(--f-data);min-height:1.5em;margin:0}
.rq-row{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 10px}
.rq-row select,.rq-row button{font:600 13px var(--f-data);border:1px solid var(--rule);background:var(--sheet);color:var(--ink);padding:7px 10px;border-radius:0;max-width:100%}
.rq-row button{cursor:pointer}.rq-row button.primary{background:var(--mask);color:var(--sheet);border-color:var(--mask)}
.rq-row button:disabled,.rq-row select:disabled{opacity:.45;cursor:default}
.rq-moves{font:13px var(--f-data);max-height:180px;overflow-y:auto;display:grid;grid-template-columns:2.4em 1fr 1fr;gap:2px 8px;font-variant-numeric:tabular-nums}
.rq-moves .n{color:var(--muted)}
.rq-pre{font:13px/1.45 var(--f-data);background:var(--sheet);border:1px solid var(--rule);padding:12px;overflow-x:auto;margin:0 0 10px;white-space:pre}
.rq-scroll{overflow-x:auto}.rq-scroll td,.rq-scroll th{white-space:nowrap}
.rq-ways{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,200px),1fr));gap:12px;margin:10px 0}
.rq-ways div{background:var(--sheet);border:1px solid var(--rule);border-top:4px solid var(--mask);padding:12px}
.rq-ways b{display:block}.rq-ways p{margin:4px 0 6px;font-size:15px}
.rq-later{font:600 11px var(--f-data);color:var(--warn);text-transform:uppercase;letter-spacing:.06em}
.rq-wait{border:1px solid var(--rule);border-top:6px solid var(--mask);background:var(--sheet);padding:22px 18px;margin:20px 0;text-align:center}
.rq-wait p{margin:0 0 8px}.rq-wait .att{font-size:20px;font-style:italic}
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
    return str(v.get(lg) or v.get("fr") or "") if isinstance(v, dict) else ("" if v is None else str(v))


def date_longue(iso, lg):
    try:
        a, m, j = (int(x) for x in str(iso).split("-"))
    except (ValueError, AttributeError):
        return str(iso or "")
    return f"{j}{'er' if j == 1 and lg == 'fr' else ''} {MOIS[lg][m - 1]} {a}" if lg == "fr" else f"{j} {MOIS[lg][m - 1]} {a}"


def diplomatie_ouverte(d):
    etapes = (d.get("ages") or {}).get("etapes") or []
    return len(etapes) > DIPLOMATIE and bool(etapes[DIPLOMATIE].get("ouvert")), (etapes[DIPLOMATIE] if len(etapes) > DIPLOMATIE else {})


def jour_ouverture(racine):
    """Jour (day) de la première édition où la Diplomatie est ouverte, ou None."""
    jours = []
    for f in (racine / "data" / "editions").glob("*.json"):
        d = lire(f, None)
        if isinstance(d, dict) and isinstance(d.get("day"), int) and diplomatie_ouverte(d)[0]:
            jours.append(d["day"])
    return min(jours) if jours else None


def probleme_du_jour(probs, latest, j0):
    liste = probs.get("problemes") or []
    if not liste:
        return None
    jour = latest.get("day") if isinstance(latest.get("day"), int) else 0
    return liste[(jour - (j0 if j0 is not None else jour)) % len(liste)]


def plateau_txt(board):
    lignes = []
    for r in range(6):
        cases = []
        for c in range(5):
            i = r * 5 + c
            cases.append("*" if board[i] == "." and i in OFFENSIVES else board[i])
        lignes.append(f"{r + 1}  " + " ".join(cases))
    lignes.append("   a b c d e")
    return lignes


def texte_probleme(p, nb, lg):
    T = L[lg]
    camp = T["t_camps"][0 if p["side"] == 1 else 1]
    return ([T["t_probleme"].format(n=p["n"], t=nb), T["t_plateau"], T["t_pieces"], ""] + plateau_txt(p["board"]) +
            ["", T["t_trait"].format(c=camp), T["t_legaux"].format(n=len(p["legaux"]), l=" ".join(p["legaux"])), "", T["t_enigme"].format(c=camp)])


def ligne_registre(x, lg):
    T = L[lg]
    fin = x.get("fin", "")
    return (date_longue(x.get("date", ""), lg), tr(x.get("visiteur"), lg), f'{NIVEAUX[lg][x["adversaire"] - 1]} ({x["adversaire"]})',
            T["resultats"].get(x.get("resultat"), x.get("resultat", "")), FIN_EN.get(fin, fin) if lg == "en" else fin, str(x.get("demi_coups", "")))


def tete(lg, ouvert, pre):
    T = L[lg]
    fr_url, en_url = BASE + "relique.html", BASE + "en/relique.html"
    desc = T["desc"] if ouvert else T["desc_ferme"]
    autre_lg, _, autre_rss, autre_titre = T["autre"]
    return f"""<!doctype html>
<html lang="{lg}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<link rel="icon" href="{pre}favicon.ico" sizes="32x32">
<link rel="icon" href="{pre}favicon.svg" type="image/svg+xml">
<title>{e(T["titre"])} — Microcontrôland</title>
<meta name="description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="La Puce Libre — Microcontrôland">
<meta property="og:title" content="{e(T["titre"])} — Microcontrôland">
<meta property="og:description" content="{e(desc)}">
<link rel="alternate" hreflang="fr" href="{fr_url}">
<link rel="alternate" hreflang="en" href="{en_url}">
<link rel="alternate" hreflang="x-default" href="{fr_url}">
<link rel="alternate" type="text/plain" href="{BASE}{'en/' if lg == 'en' else ''}relique.txt">
<link rel="alternate" type="application/rss+xml" title="La Puce Libre" href="{pre}{T["rss"]}">
<link rel="alternate" type="application/rss+xml" title="{e(autre_titre)}" hreflang="{autre_lg}" href="{pre}{autre_rss}">
<link rel="stylesheet" href="{pre}style.css">
<script src="{pre}mesure.js" defer></script>
{STYLE.replace("{pre}", pre) if ouvert else STYLE.split("@font-face")[0] + STYLE[STYLE.index(".rq-wait"):]}
</head>
<body>
<div class="wrap">
  <header class="mast">
    <div class="top"><span>{e(T["mast"][0])}</span><span>{e(T["mast"][1])}</span></div>
    <div class="title"><a href="./">La Puce <span>Libre</span></a></div>
    <p class="tag">{e(T["tag"])}</p>
  </header>
  <nav class="main" aria-label="Navigation">
"""


def nav(lg, pre):
    T = L[lg]
    liens = ["./", "archives.html", "histoire.html", "langue.html", "citoyen.html", "ambassade.html", "temple.html", "recherche.html", "projet.html", pre + T["rss"]]
    cur = ' aria-current="page"'
    return "\n".join(f'    <a href="{h}"{cur if h == "ambassade.html" else ""}>{e(t)}</a>' for h, t in zip(liens, T["menu"]))


def pied(lg, pre, maj, scripts):
    T = L[lg]
    autre = "en/relique.html" if lg == "fr" else "../relique.html"
    return f"""    <p class="note">{e(maj)}</p>
  </div>

  <footer class="site">
    <span><a href="ambassade.html">{e(T["retour"])}</a></span>
    <span><a href="{autre}" hreflang="{T["autre"][0]}">{e(T["autre"][1])}</a></span>
    <span><a href="mentions.html">{e(T["mentions"])}</a></span>
  </footer>
</div>
{'<script>window.MCL_BASE = "../";</script>' if lg == "en" else ""}
<script src="{pre}reglages.js"></script>
<script src="{pre}commun.js"></script>
<script src="{pre}lang.js"></script>
{scripts}</body>
</html>
"""


def page_fermee(latest, etape, lg):
    T = L[lg]
    pre = "../" if lg == "en" else ""
    p = tr(etape.get("progres"), lg)
    prog = f'<p class="note">{e(T["progres"].format(p=p))}</p>' if p else ""
    maj = T["maj_le"].format(n=latest.get("day", "?"), d=date_longue(latest.get("date", ""), lg))
    return (tete(lg, False, pre) + nav(lg, pre) + f"""
  </nav>

  <div class="prose">
    <p class="k2" style="margin-top:22px">{e(T["haut"])}</p>
    <h1>{e(T["titre"])}</h1>
    <div class="rq-wait"><p class="att">{e(T["attente"])}</p>{prog}</div>
""" + pied(lg, pre, maj, ""))


def page_ouverte(latest, prob, nb, galerie, registre, lg):
    T = L[lg]
    pre = "../" if lg == "en" else ""
    txt = "relique.txt"
    maj = T["maj_le"].format(n=latest.get("day", "?"), d=date_longue(latest.get("date", ""), lg))
    regles = "".join(f"<li>{e(r)}</li>" for r in T["regles"])
    niveaux = "".join(f'<option value="{k + 1}"{" selected" if k == 1 else ""}>{e(n)} ({k + 1}{", " + T["lente"] if k == 4 else ""})</option>'
                      for k, n in enumerate(NIVEAUX[lg]))
    lignes = "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in ligne_registre(x, lg)) + "</tr>" for x in registre.get("parties") or [])
    registre_html = (f'<h3>{e(T["h_registre"])}</h3><p class="note">{e(tr(registre.get("note"), lg))}</p>'
                     f'<div class="rq-scroll"><table><thead><tr>{"".join(f"<th>{e(c)}</th>" for c in T["cols"])}</tr></thead><tbody>{lignes}</tbody></table></div>') if lignes else ""
    probleme_html = ""
    if prob:
        probleme_html = (f'<pre class="rq-pre">{e(chr(10).join(texte_probleme(prob, nb, lg)))}</pre>'
                         f'<details><summary>{e(T["solution"])}</summary><p>{e(T["sol_txt"].format(k=prob["key"]))}</p></details>')
    plus_tard = '<span class="rq-later">{}</span>'
    facons = "".join(f'<div><b>{e(a)}</b><p>{e(b)}</p>{plus_tard.format(e(c)) if c else ""}</div>' for a, b, c in T["facons"])
    galerie_json = json.dumps({"mv": galerie.get("mv", []), "notes": galerie.get("notes", [])}, ensure_ascii=False).replace("</", "<\\/")
    code = T["pied1"].format(e=f'<a href="{pre}relique/engine.js">engine.js</a>', r=f'<a href="{pre}relique/relique.js">relique.js</a>')
    scripts = (f'<script type="application/json" id="galerie-donnees">{galerie_json}</script>\n'
               f'<script src="{pre}relique/engine.js"></script>\n<script src="{pre}relique/relique.js"></script>\n')
    return (tete(lg, True, pre) + nav(lg, pre) + f"""
  </nav>

  <div class="prose">
    <p class="k2" style="margin-top:22px">{e(T["haut"])}</p>
    <h1>{e(T["titre"])}</h1>
    <p class="chapo">{e(T["chapo"])}</p>

    <h2>{e(T["h_relique"])}</h2>
    <blockquote class="quote">{e(T["decret"])}<cite>{e(T["decret_cite"])}</cite></blockquote>
    <p>{T["vrai"]}</p>

    <h2>{e(T["h_jouer"])}</h2>
    <noscript><p class="note">{e(T["sans_js"])}<a href="{txt}">{txt}</a></p></noscript>
    <div class="rq-jeu">
      <p class="rq-status" id="status" aria-live="polite">{e(T["statut0"])}</p>
      <div class="rq-board" id="board" aria-label="{e(T["titre"])}"></div>
      <p class="note" style="text-align:center;margin:0">{e(T["etoile"])}</p>
    </div>
    <div class="box">
      <h3 style="margin:0 0 10px">{e(T["audience"])}</h3>
      <div class="rq-row"><label for="side">{e(T["je_joue"])}</label>
        <select id="side"><option value="1">{e(T["blancs"])}</option><option value="-1">{e(T["noirs"])}</option></select></div>
      <div class="rq-row"><label for="depth">{e(T["adversaire"])}</label><select id="depth">{niveaux}</select></div>
      <div class="rq-row"><button type="button" class="primary" id="new">{e(T["commencer"])}</button><button type="button" id="resign" disabled>{e(T["abandonner"])}</button></div>
      <div class="rq-moves" id="moves"></div>
    </div>
    <details><summary>{e(T["h_regles"])}</summary><ul>{regles}</ul></details>

    <h2>{e(T["h_galerie"])}</h2>
    <p>{e(T["galerie_txt"].format(t=tr(galerie.get("titre"), lg)))}</p>
    <div class="rq-jeu">
      <p class="rq-status" id="rstatus">{e(T["demo"])}</p>
      <div class="rq-board" id="rboard" aria-label="{e(T["h_galerie"])}"></div>
    </div>
    <div class="rq-row" style="justify-content:center">
      <button type="button" id="rfirst" aria-label="{e(T["debut"])}">⏮</button><button type="button" id="rprev" aria-label="{e(T["prec"])}">◀</button>
      <button type="button" id="rplay" class="primary">{e(T["lecture"])}</button>
      <button type="button" id="rnext" aria-label="{e(T["suiv"])}">▶</button><button type="button" id="rlast" aria-label="{e(T["fin"])}">⏭</button>
    </div>
    <p class="note" id="rmove" style="text-align:center">{e(T["initiale"])}</p>
    {registre_html}

    <h2>{e(T["h_ia"])}</h2>
    <p>{T["ia_txt"].format(lien=f'<a href="{txt}">{txt}</a>')}</p>
    {probleme_html}

    <h2>{e(T["h_inter"])}</h2>
    <div class="rq-ways">{facons}</div>

    <p class="note">{code}</p>
    <p class="note">{e(T["pied2"])}</p>
""" + pied(lg, pre, maj, scripts))


def texte(latest, ouvert, etape, prob, nb, galerie, registre, lg):
    T = L[lg]
    url = BASE + ("en/" if lg == "en" else "") + "relique.html"
    l = [T["t_titre"], T["t_lecture"], T["t_page"].format(u=url), ""]
    if not ouvert:
        l.append(T["attente"])
        p = tr(etape.get("progres"), lg)
        if p:
            l.append(T["progres"].format(p=p))
    else:
        l += [T["t_quoi"], "", T["t_regles"]] + [f"- {r}" for r in T["regles"]] + [""]
        if prob:
            l += texte_probleme(prob, nb, lg) + [T["t_solution"], ""]
        if galerie.get("notes"):
            l += [T["t_galerie"].format(t=tr(galerie.get("titre"), lg)), T["t_coups"].format(c=" ".join(galerie["notes"])), T["t_resultat"], ""]
        if registre.get("parties"):
            l += [T["t_registre"], tr(registre.get("note"), lg)]
            l += [" | ".join(ligne_registre(x, lg)) for x in registre["parties"]] + [""]
        l += [T["t_jouer"], "", L[lg]["pied2"]]
    l += ["", T["maj_le"].format(n=latest.get("day", "?"), d=date_longue(latest.get("date", ""), lg))]
    return "\n".join(l) + "\n"


def main():
    racine = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    latest = lire(racine / "data" / "latest.json", {})
    ouvert, etape = diplomatie_ouverte(latest)
    probs = lire(racine / "relique" / "problemes.json", {})
    galerie = lire(racine / "relique" / "galerie.json", {})
    registre = lire(racine / "relique" / "registre.json", {})
    prob = probleme_du_jour(probs, latest, jour_ouverture(racine)) if ouvert else None
    nb = len(probs.get("problemes") or [])
    (racine / "en").mkdir(exist_ok=True)
    for lg, d in (("fr", racine), ("en", racine / "en")):
        h = page_ouverte(latest, prob, nb, galerie, registre, lg) if ouvert else page_fermee(latest, etape, lg)
        (d / "relique.html").write_text(h, encoding="utf-8")
        (d / "relique.txt").write_text(texte(latest, ouvert, etape, prob, nb, galerie, registre, lg), encoding="utf-8")
    print(f"relique.html, en/relique.html, relique.txt, en/relique.txt écrits : salle {'ouverte' if ouvert else 'fermée'}"
          + (f", problème n° {prob['n']}" if prob else ""))


if __name__ == "__main__":
    main()
