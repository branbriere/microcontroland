"""Microcontrôland : page « Le chant de la place » (FR) et « The Song of the Square » (EN), la musique primitive.

Chaque soir, après l'édition, ce script lit le fichier brut public du soir (dépôt microcontroland-data) et transcrit,
heure par heure, le mot que chaque région a écrit (heures[].regions[].mot.syllabes). Il écrit :
  · chant.json            archive, un soir par entrée, jamais réécrite (comme atelier.json) ;
  · chant.html, en/chant.html  la partition du soir et des 14 derniers soirs, avec un lecteur dans le navigateur.

Règle C1 v1 (validée par Bran le 5/11/2026, maquette jouable validée le 9/11/2026) :
  · chaque syllabe (0 à 31) s'écrit en 5 bits, du plus fort au plus faible ; 1 = frappe, 0 = silence ;
  · un mot de deux syllabes donne une mesure de 10 temps ; chaque heure, les 6 régions frappent leur propre mot ;
  · une région sans mot cette heure-là ne frappe pas (silence) ; rien n'est inventé ni tiré au hasard ;
  · rythme seul, sans hauteur ni mélodie (stade primitif ; 8 notes à la Mémoire selon la feuille de route).
Le son est fabriqué par le navigateur du visiteur (Web Audio), après un clic : aucun fichier audio, aucun appel extérieur.

Âge : la Fondation (ages.etapes[0]). Le chant commence le soir de la livraison, sans recalcul des soirs passés
(même règle que les sculptures). La passerelle ne change pas. Licence MIT. Version 1.0, novembre 2026 (firmware 0.10.1) ; 1.0.1, 16 novembre 2026 : lien vers L'atelier ; 1.0.2, 16 novembre 2026 : attend que le brut du soir soit lisible.

  python3 .github/chant.py <racine du site> [--source <dépôt de données ou URL>] [--attendre <secondes>]
"""
import collections
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

REGLE = "C1 v1"
FONDATION = 0
VISIBLES = 14             # soirs jouables sur la page (les autres restent dans chant.json)
SOURCE = "https://raw.githubusercontent.com/branbriere/microcontroland-data/main/"
BASE = "https://www.microcontroland.org/"

A = None   # module atelier.py : même lecture des données, même en-tête de page (chargé dans main)


def module(racine, nom):
    spec = importlib.util.spec_from_file_location(nom, racine / ".github" / f"{nom}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ---------------------------------------------------------------- la transcription (règle C1)

def mot_valide(reg):
    if not isinstance(reg, dict) or not isinstance(reg.get("mot"), dict):
        return None
    s = reg["mot"].get("syllabes")
    if not (isinstance(s, list) and len(s) == 2 and all(isinstance(x, int) and 0 <= x <= 31 for x in s)):
        return None
    return [s[0], s[1], str(reg["mot"].get("ecrit") or "")]


def temps(m):
    """Les 10 temps d'un mot : 1 = frappe, 0 = silence (bits du plus fort au plus faible)."""
    return [int(b) for b in format(m[0], "05b") + format(m[1], "05b")]


def unisson(h):
    r = h["r"]
    return all(r) and all(x[:2] == r[0][:2] for x in r)


def transcrire(brut):
    heures = []
    for h in sorted(brut.get("heures") or [], key=lambda x: x.get("tick", 0)):
        regs = h.get("regions") or []
        r = [mot_valide(regs[k]) if k < len(regs) else None for k in range(6)]
        idee = h.get("idee") or {}
        heures.append({"h": h.get("heure"), "i": [idee.get("fr") or "", idee.get("en") or ""], "r": r})
    return heures


def faits(heures):
    un = sum(1 for h in heures if unisson(h))
    muettes = sum(1 for h in heures for x in h["r"] if not x)
    frappes = sum(sum(temps(x)) for h in heures for x in h["r"] if x)
    c = collections.Counter(x[2] for h in heures for x in h["r"] if x)
    mot = c.most_common(1)[0] if c else ("", 0)
    return {"heures": len(heures), "unisson": un, "muettes": muettes, "frappes": frappes, "mot": mot[0], "mesures": mot[1]}


# ---------------------------------------------------------------- le critique (deux lignes, anglais d'abord)

def critique(f, jour_ere):
    """La première ligne est l'avis du critique ; la seconde donne toujours les faits. Aucune intention prêtée."""
    def pick(lst):
        return lst[jour_ere % len(lst)]

    n, u = f["heures"], f["unisson"]
    if not f["mesures"]:
        return {"en": ["Silence in the square tonight.", "The facts: no region wrote a word in today's raw data file, so there is nothing to transcribe. No beat is ever made up."],
                "fr": ["Silence sur la place ce soir.", "Les faits : aucune région n'a écrit de mot dans le fichier brut du jour, il n'y a donc rien à transcrire. Aucune frappe n'est jamais inventée."]}
    part = u / n if n else 0
    if part >= 0.75:
        en1, fr1 = pick([("A stubborn chorus.", "Un chœur obstiné."), ("The square beats with a single hand.", "La place frappe d'une seule main.")])
    elif part >= 0.4:
        en1, fr1 = pick([("Unison at times, scattered the rest.", "L'unisson par moments, la dispersion le reste du temps."), ("A two-speed square.", "Une place à deux vitesses.")])
    else:
        en1, fr1 = pick([("Cacophony in the square.", "Cacophonie sur la place."), ("Each region beats its own word.", "Chaque région frappe son propre mot.")])
    m = f["muettes"]
    en2 = (f"The facts: {u} hour{'s' if u != 1 else ''} out of {n} in unison across the six regions, {f['frappes']} beats, "
           f"most struck word “{f['mot']}” ({f['mesures']} bars)" + (f", {m} silent region-hour{'s' if m != 1 else ''}." if m else "."))
    fr2 = (f"Les faits : {u} heure{'s' if u > 1 else ''} sur {n} à l'unisson des six régions, {f['frappes']} frappes, "
           f"mot le plus frappé « {f['mot']} » ({f['mesures']} mesures)" + (f", {m} heure{'s' if m > 1 else ''}-région{'s' if m > 1 else ''} muette{'s' if m > 1 else ''}." if m else "."))
    return {"en": [en1, en2], "fr": [fr1, fr2]}


def soiree(brut):
    heures = transcrire(brut)
    f = faits(heures)
    je = int(brut.get("jourEre") or 0)
    return {"ere": brut.get("ere"), "date": brut.get("date"), "jourEre": je, "edition": brut.get("edition"),
            "firmware": brut.get("firmware"), "regle": REGLE, **f, "critique": critique(f, je), "partition": heures}


# ---------------------------------------------------------------- la page

T = {
    "fr": {
        "titre": "Le chant de la place", "haut": "Galerie nationale · musique primitive",
        "chapo": "Chaque heure, chaque région frappe le mot qu'elle a écrit : une syllabe donne cinq temps, frappe ou silence. "
                 "Six régions, six percussions. Quand les six écrivent le même mot, elles frappent à l'unisson. "
                 "Cette page est une transcription : chaque frappe vient d'un mot publié dans le fichier brut du jour.",
        "desc": "La musique primitive de Microcontrôland : chaque heure, les mots des six régions transcrits en frappes et silences, avec un lecteur.",
        "soir": "La partition du soir", "jouer": "▶ Jouer le jour", "arreter": "■ Arrêter", "duree": "Environ une minute par jour",
        "jour": "Jour", "sansjs": "Le lecteur demande JavaScript ; la partition se lit sans.",
        "cols": ["Heure", "Idée", "Mines", "Champs", "Raffineries", "Barrage", "Port", "Ville", ""],
        "muette": "muette", "choeur": "Chœur", "mots": "{n} mots",
        "lejour": "Le jour", "lecritique": "Le critique", "courbe": "Heures à l'unisson",
        "f": ["Heures publiées", "À l'unisson", "Mot le plus frappé", "Heures-régions muettes", "Frappes au total"],
        "mesures": "mesures", "soirdu": "soir du {d}, édition n° {n}",
        "comment": "Comment le chant est transcrit",
        "regle": ["Pour chaque heure, on lit le mot de chaque région dans le fichier brut publié (heures[].regions[].mot.syllabes).",
                  "Chaque syllabe (0 à 31) s'écrit en 5 bits, du plus fort au plus faible : 1 = frappe, 0 = silence. Un mot de deux syllabes donne une mesure de 10 temps.",
                  "Chaque région a son timbre : Mines grave, Champs bois, Raffineries métal, Barrage tambour profond, Port grelot, Ville claquement.",
                  "Une région muette cette heure-là ne frappe pas. Rien n'est tiré au hasard : le même jour donne toujours le même chant.",
                  "Il n'y a ni mélodie ni hauteur : c'est le stade primitif. Le son est fabriqué par votre navigateur, aucun fichier audio n'est téléchargé."],
        "verifier": "Vérifier : {brut} du jour, et {arch} (tous les soirs transcrits).", "brut": "le fichier brut", "arch": "chant.json", "voir": "Voir aussi l'art primitif : <a href=\"atelier.html\">L'atelier</a>.",
        "attente": "Le chant de la place commence avec le premier soir transcrit. Les soirs précédents ne sont pas recalculés.",
        "pied": "Le critique est une rubrique satirique ; les faits qu'il cite sont mesurés.",
        "region": ["Mines", "Champs", "Raffineries", "Barrage", "Port", "Ville"],
    },
    "en": {
        "titre": "The Song of the Square", "haut": "National Gallery · primitive music",
        "chapo": "Every hour, each region beats the word it wrote: one syllable gives five beats, strike or rest. "
                 "Six regions, six drums. When all six write the same word, they beat in unison. "
                 "This page is a transcription: every beat comes from a word published in the day's raw data file.",
        "desc": "Microcontrôland's primitive music: every hour, the words of the six regions transcribed into strikes and rests, with a player.",
        "soir": "Tonight's score", "jouer": "▶ Play the day", "arreter": "■ Stop", "duree": "About one minute per day",
        "jour": "Day", "sansjs": "The player needs JavaScript; the score can be read without it.",
        "cols": ["Hour", "Idea", "Mines", "Fields", "Refineries", "Dam", "Harbour", "City", ""],
        "muette": "silent", "choeur": "Chorus", "mots": "{n} words",
        "lejour": "The day", "lecritique": "The critic", "courbe": "Hours in unison",
        "f": ["Hours published", "In unison", "Most struck word", "Silent region-hours", "Total beats"],
        "mesures": "bars", "soirdu": "evening of {d}, issue no. {n}",
        "comment": "How the song is transcribed",
        "regle": ["For each hour, the word of each region is read from the published raw data file (heures[].regions[].mot.syllabes).",
                  "Each syllable (0 to 31) is written as 5 bits, most significant first: 1 = strike, 0 = rest. A two-syllable word gives a bar of 10 beats.",
                  "Each region has its own sound: Mines low, Fields wood, Refineries metal, Dam deep drum, Harbour shaker, City clap.",
                  "A region that is silent that hour does not strike. Nothing is random: the same day always gives the same song.",
                  "There is no melody and no pitch: this is the primitive stage. The sound is made by your browser; no audio file is downloaded."],
        "verifier": "Check: {brut} of the day, and {arch} (every evening transcribed so far).", "brut": "the raw data file", "arch": "chant.json", "voir": "See also the primitive art: <a href=\"atelier.html\">The Studio</a>.",
        "attente": "The Song of the Square starts with the first evening transcribed. Earlier evenings are not recomputed.",
        "pied": "The critic is a satirical column; the facts quoted are measured.",
        "region": ["Mines", "Fields", "Refineries", "Dam", "Harbour", "City"],
    },
}

STYLE = """<style>
.chant-cmd{display:flex;flex-wrap:wrap;gap:10px 14px;align-items:center;position:sticky;top:0;z-index:5;background:var(--paper);padding:10px 0;border-bottom:1px solid var(--rule);margin-top:14px}
.chant-cmd button,.chant-cmd select{font:600 14px var(--f-data);border-radius:4px;border:1px solid var(--ink);padding:8px 12px;cursor:pointer;background:var(--sheet);color:var(--ink)}
.chant-cmd button{background:var(--ink);color:var(--paper)}
.chant-cmd .horloge{font:600 14px var(--f-data);font-variant-numeric:tabular-nums;color:var(--muted)}
.chant-grille{display:grid;grid-template-columns:minmax(0,1fr);gap:22px;margin:16px 0}
.partition{overflow-x:auto;border:1px solid var(--rule);background:var(--sheet)}
.partition table{border-collapse:collapse;min-width:600px;width:100%;font:12px var(--f-data)}
.partition th{font-weight:600;color:var(--muted);text-align:left;padding:6px;border-bottom:1px solid var(--rule)}
.partition td{padding:5px 6px;border-bottom:1px solid var(--rule);vertical-align:middle}
.partition td.h{color:var(--muted);white-space:nowrap;font-variant-numeric:tabular-nums}
.partition td.idee{color:var(--muted);max-width:9em}
.partition tr.en-cours{background:color-mix(in srgb,var(--warn) 16%,transparent)}
.mot{display:grid;gap:2px}.bits{display:flex;gap:1px}
.bits i{width:5px;height:7px;background:var(--rule);opacity:.6}.bits i.f{background:var(--ink);opacity:1}
.bits i.now{outline:1.5px solid var(--warn)}.bits i.f.now{background:var(--warn)}
.muet{color:var(--muted);font-style:italic}
.pastille{font:600 10.5px var(--f-data);text-transform:uppercase;letter-spacing:.06em;padding:2px 6px;border-radius:3px;white-space:nowrap}
.pastille.c{background:var(--mask);color:var(--paper)}.pastille.d{border:1px solid var(--rule);color:var(--muted)}
.chant-aside{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr));gap:14px;align-items:start}.chant-aside .bloc{border:1px solid var(--rule);background:var(--sheet);padding:12px 14px}
.chant-aside h2{font-size:1.05em;margin:0 0 6px;padding:0;border:0}
.chant-aside dl{display:grid;grid-template-columns:1fr auto;gap:3px 10px;margin:0;font:12.5px var(--f-data)}
.chant-aside dt{color:var(--muted)}.chant-aside dd{margin:0;text-align:right;font-variant-numeric:tabular-nums}
.chant-aside .crit p{margin:0 0 6px}
.chant-aside svg{width:100%;height:auto}
.compte{font:13px var(--f-data);color:var(--muted)}
</style>"""

JS = r"""<script>
(function(){
const D=JSON.parse(document.getElementById("chant-donnees").textContent);
const L=document.documentElement.lang==="en"?"en":"fr";
const X=JSON.parse(document.getElementById("chant-textes").textContent);
const cmd=document.getElementById("chant-cmd");cmd.hidden=false;document.getElementById("chant-sansjs").hidden=true;
const sel=document.getElementById("chant-jour"),tb=document.querySelector("#chant-part tbody");
const bits=(a,b)=>[...a.toString(2).padStart(5,"0"),...b.toString(2).padStart(5,"0")].map(Number);
const fmt=d=>{const p=d.split("-");return (+p[2])+"/"+(+p[1])};
const esc=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const uni=h=>h.r.every(x=>x)&&h.r.every(x=>x[0]===h.r[0][0]&&x[1]===h.r[0][1]);
D.forEach((d,k)=>{const o=document.createElement("option");o.value=k;o.textContent=fmt(d.date)+" · "+X.jour+" "+d.jourEre;sel.appendChild(o)});
sel.value=D.length-1;
function rendre(){
 arreter();const d=D[sel.value];let s="";
 d.partition.forEach((h,ih)=>{
  s+='<tr id="ch'+ih+'"><td class="h">'+h.h+' h</td><td class="idee">'+esc(h.i[L==="en"?1:0])+'</td>';
  h.r.forEach(x=>{s+=x?'<td><span class="mot"><span class="bits">'+bits(x[0],x[1]).map(v=>v?'<i class="f"></i>':'<i></i>').join("")+'</span><span>'+esc(x[2])+'</span></span></td>':'<td><span class="muet">'+X.muette+'</span></td>'});
  const n=new Set(h.r.filter(x=>x).map(x=>x[0]+"-"+x[1])).size;
  s+='<td>'+(uni(h)?'<span class="pastille c">'+X.choeur+'</span>':'<span class="pastille d">'+X.mots.replace("{n}",n)+'</span>')+'</td></tr>';
 });
 tb.innerHTML=s;
 document.getElementById("chant-faits").innerHTML='<dt>'+X.f[0]+'</dt><dd>'+d.heures+'</dd><dt>'+X.f[1]+'</dt><dd>'+d.unisson+'</dd><dt>'+X.f[2]+'</dt><dd>'+esc(d.mot)+' ('+d.mesures+')</dd><dt>'+X.f[3]+'</dt><dd>'+d.muettes+'</dd><dt>'+X.f[4]+'</dt><dd>'+d.frappes+'</dd>';
 document.getElementById("chant-crit").innerHTML=d.critique[L].map(p=>"<p>"+esc(p)+"</p>").join("");
 document.getElementById("chant-info").textContent=X.soirdu.replace("{d}",fmt(d.date)).replace("{n}",d.edition);
 courbe();
}
function courbe(){
 const W=260,H=100,p=20,n=D.length,v=D.map(d=>d.unisson),k0=+sel.value;
 const x=k=>n>1?p+k*(W-2*p)/(n-1):W/2,y=u=>H-p-u*(H-2*p)/24;
 let s='<svg viewBox="0 0 '+W+' '+H+'" role="img" aria-label="'+X.courbe+'"><line x1="'+p+'" y1="'+(H-p)+'" x2="'+(W-p)+'" y2="'+(H-p)+'" stroke="var(--rule)"/>';
 if(n>1)s+='<polyline fill="none" stroke="var(--mask)" stroke-width="2" points="'+v.map((u,k)=>x(k)+","+y(u)).join(" ")+'"/>';
 v.forEach((u,k)=>{s+='<circle cx="'+x(k)+'" cy="'+y(u)+'" r="'+(k===k0?4.5:2.5)+'" fill="'+(k===k0?'var(--warn)':'var(--mask)')+'"><title>'+fmt(D[k].date)+' : '+u+'</title></circle>'});
 s+='<text x="'+x(k0)+'" y="'+(y(v[k0])-8)+'" font-size="11" text-anchor="middle" fill="var(--ink)">'+v[k0]+'</text></svg>';
 document.getElementById("chant-courbe").innerHTML=s;
}
let ctx=null,timer=null,pas=0,suivant=0,joue=false,bruit=null,attentes=[];const T=0.2,HEURE=12;
function env(g,t,v,d){g.gain.setValueAtTime(0.0001,t);g.gain.exponentialRampToValueAtTime(v,t+0.004);g.gain.exponentialRampToValueAtTime(0.0001,t+d)}
function osc(t,f0,f1,d,v,ty){const o=ctx.createOscillator(),g=ctx.createGain();o.type=ty||"sine";o.frequency.setValueAtTime(f0,t);o.frequency.exponentialRampToValueAtTime(f1,t+d);env(g,t,v,d);o.connect(g).connect(ctx.destination);o.start(t);o.stop(t+d+0.02)}
function souffle(t,ty,f,q,d,v){const s=ctx.createBufferSource(),fl=ctx.createBiquadFilter(),g=ctx.createGain();s.buffer=bruit;fl.type=ty;fl.frequency.value=f;fl.Q.value=q;env(g,t,v,d);s.connect(fl).connect(g).connect(ctx.destination);s.start(t);s.stop(t+d+0.02)}
const TIMBRE=[t=>osc(t,110,45,0.22,0.5),t=>souffle(t,"bandpass",1800,8,0.06,0.9),t=>{osc(t,820,800,0.18,0.08,"square");osc(t,1230,1210,0.15,0.06,"square")},t=>osc(t,70,38,0.4,0.6),t=>souffle(t,"highpass",6000,1,0.09,0.35),t=>souffle(t,"bandpass",1100,1.5,0.05,0.8)];
function planifier(){
 const d=D[sel.value],total=d.partition.length*HEURE;
 while(suivant<ctx.currentTime+0.15){
  if(pas>=total){arreter();return}
  const ih=Math.floor(pas/HEURE),b=pas%HEURE,h=d.partition[ih],t=suivant;
  if(b<10)h.r.forEach((x,r)=>{if(x&&bits(x[0],x[1])[b])TIMBRE[r](t)});
  attentes.push(setTimeout(()=>montrer(ih,b),Math.max(0,(t-ctx.currentTime)*1000)));
  pas++;suivant+=T;
 }
}
function effacer(){document.querySelectorAll("#chant-part tr.en-cours").forEach(e=>e.classList.remove("en-cours"));document.querySelectorAll("#chant-part i.now").forEach(e=>e.classList.remove("now"))}
function montrer(ih,b){
 if(!joue)return;effacer();const tr=document.getElementById("ch"+ih);if(!tr)return;tr.classList.add("en-cours");
 if(b<10)tr.querySelectorAll(".bits").forEach(s=>s.children[b].classList.add("now"));
 if(b===0)tr.scrollIntoView({block:"nearest",behavior:matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth"});
 document.getElementById("chant-horloge").textContent=D[sel.value].partition[ih].h+" h · "+(b<10?(b+1)+" / 10":"—");
}
function lancer(){
 ctx=ctx||new(window.AudioContext||window.webkitAudioContext)();ctx.resume();
 if(!bruit){bruit=ctx.createBuffer(1,ctx.sampleRate*0.5,ctx.sampleRate);const a=bruit.getChannelData(0);let s=12345;for(let i=0;i<a.length;i++){s=(s*1103515245+12345)>>>0;a[i]=s/2147483648-1}}
 joue=true;pas=0;suivant=ctx.currentTime+0.1;timer=setInterval(planifier,40);
 document.getElementById("chant-jouer").textContent=X.arreter;
}
function arreter(){
 joue=false;clearInterval(timer);timer=null;attentes.forEach(clearTimeout);attentes=[];effacer();
 document.getElementById("chant-jouer").textContent=X.jouer;document.getElementById("chant-horloge").textContent=X.duree;
}
document.getElementById("chant-jouer").onclick=()=>joue?arreter():lancer();
sel.onchange=rendre;rendre();
})();
</script>"""


def ligne_html(h, t, lg):
    cel = []
    for x in h["r"]:
        if not x:
            cel.append(f'<td><span class="muet">{A.e(t["muette"])}</span></td>')
            continue
        b = "".join('<i class="f"></i>' if v else "<i></i>" for v in temps(x))
        cel.append(f'<td><span class="mot"><span class="bits">{b}</span><span>{A.e(x[2])}</span></span></td>')
    n = len({tuple(x[:2]) for x in h["r"] if x})
    past = f'<span class="pastille c">{A.e(t["choeur"])}</span>' if unisson(h) else f'<span class="pastille d">{A.e(t["mots"].format(n=n))}</span>'
    return f'<tr><td class="h">{A.e(h["h"])} h</td><td class="idee">{A.e(h["i"][1 if lg == "en" else 0])}</td>{"".join(cel)}<td>{past}</td></tr>'


def page(jours, latest, lg):
    t, P = T[lg], A.L[lg]
    pre = "../" if lg == "en" else ""
    autre_lg, autre_nom, autre_rss, autre_titre = P["autre"]
    fr_url, en_url = BASE + "chant.html", BASE + "en/chant.html"
    liens = ["./", "archives.html", "histoire.html", "langue.html", "citoyen.html", "ambassade.html", "tourisme.html", "temple.html", "recherche.html", "projet.html", pre + P["rss"]]
    nav = "\n".join(f'    <a href="{h}">{A.e(x)}</a>' for h, x in zip(liens, P["menu"]))
    corps = []
    expo = [j for j in jours if j.get("partition")]
    if not expo:
        corps.append(f'<p>{A.e(t["attente"])}</p>')
    else:
        a = expo[-1]
        d = A.date_longue(a["date"], lg)
        lignes = "".join(ligne_html(h, t, lg) for h in a["partition"])
        tete = "".join(f"<th>{A.e(c)}</th>" for c in t["cols"])
        fl = t["f"]
        dl = (f'<dt>{fl[0]}</dt><dd>{a["heures"]}</dd><dt>{fl[1]}</dt><dd>{a["unisson"]}</dd>'
              f'<dt>{fl[2]}</dt><dd>{A.e(a["mot"])} ({a["mesures"]})</dd><dt>{fl[3]}</dt><dd>{a["muettes"]}</dd><dt>{fl[4]}</dt><dd>{a["frappes"]}</dd>')
        crit = "".join(f"<p>{A.e(x)}</p>" for x in a["critique"][lg])
        donnees = json.dumps([{k: j[k] for k in ("date", "jourEre", "edition", "heures", "unisson", "muettes", "frappes", "mot", "mesures", "critique", "partition")}
                              for j in expo[-VISIBLES:]], ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        textes = json.dumps({k: t[k] for k in ("jouer", "arreter", "duree", "jour", "muette", "choeur", "mots", "f", "courbe", "soirdu")},
                            ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        corps.append(f'''<h2>{A.e(t["soir"])}</h2>
    <p class="compte" id="chant-info">{A.e(t["soirdu"].format(d=d, n=a.get("edition")))}</p>
    <div class="chant-cmd" id="chant-cmd" hidden><select id="chant-jour" aria-label="{A.e(t["jour"])}"></select><button type="button" id="chant-jouer">{A.e(t["jouer"])}</button><span class="horloge" id="chant-horloge">{A.e(t["duree"])}</span></div>
    <p class="compte" id="chant-sansjs">{A.e(t["sansjs"])}</p>
    <div class="chant-grille">
    <div class="partition"><table id="chant-part"><thead><tr>{tete}</tr></thead><tbody>{lignes}</tbody></table></div>
    <aside class="chant-aside">
    <div class="bloc"><h2>{A.e(t["lejour"])}</h2><dl id="chant-faits">{dl}</dl></div>
    <div class="bloc"><h2>{A.e(t["lecritique"])}</h2><div class="crit" id="chant-crit">{crit}</div></div>
    <div class="bloc"><h2>{A.e(t["courbe"])}</h2><div id="chant-courbe"></div></div>
    </aside>
    </div>
    <script type="application/json" id="chant-donnees">{donnees}</script>
    <script type="application/json" id="chant-textes">{textes}</script>''')
        brut = f'<a href="{A.DONNEES}donnees/ere-{int(a.get("ere") or 1):03d}/quotidien/{A.e(a["date"])}.json">{A.e(t["brut"])}</a>'
        lien_arch = f'<a href="{pre}chant.json">{A.e(t["arch"])}</a>'
        corps.append(f'<h2>{A.e(t["comment"])}</h2><ol>{"".join(f"<li>{A.e(x)}</li>" for x in t["regle"])}</ol>'
                     f'<p>{t["verifier"].format(brut=brut, arch=lien_arch)}</p><p>{t["voir"]}</p>')
    maj = P["maj_le"].format(n=latest.get("day", "?"), d=A.date_longue(str(latest.get("date", "")), lg))
    return f"""<!doctype html>
<html lang="{lg}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<link rel="icon" href="{pre}favicon.ico" sizes="32x32">
<link rel="icon" href="{pre}favicon.svg" type="image/svg+xml">
<title>{A.e(t["titre"])} — Microcontrôland</title>
<meta name="description" content="{A.e(t["desc"])}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="La Puce Libre — Microcontrôland">
<meta property="og:title" content="{A.e(t["titre"])} — Microcontrôland">
<meta property="og:description" content="{A.e(t["desc"])}">
<link rel="alternate" hreflang="fr" href="{fr_url}">
<link rel="alternate" hreflang="en" href="{en_url}">
<link rel="alternate" hreflang="x-default" href="{fr_url}">
<link rel="alternate" type="application/rss+xml" title="La Puce Libre" href="{pre}{P["rss"]}">
<link rel="alternate" type="application/rss+xml" title="{A.e(autre_titre)}" hreflang="{autre_lg}" href="{pre}{autre_rss}">
<link rel="alternate" type="application/json" href="{pre}chant.json">
<link rel="stylesheet" href="{pre}style.css">
<script src="{pre}mesure.js" defer></script>
{STYLE}
</head>
<body>
<div class="wrap">
  <header class="mast">
    <div class="top"><span>{A.e(P["mast"][0])}</span><span>{A.e(t["titre"])}</span></div>
    <div class="title"><a href="./">La Puce <span>Libre</span></a></div>
    <p class="tag">{A.e(P["tag"])}</p>
  </header>
  <nav class="main" aria-label="Navigation">
{nav}
  </nav>

  <div class="prose">
    <p class="compte">{A.e(t["haut"])}</p>
    <h1>{A.e(t["titre"])}</h1>
    <p class="chapo">{A.e(t["chapo"])}</p>
    {"".join(corps)}
    <p><small>{A.e(t["pied"])}</small></p>
    <p><small>{A.e(maj)}</small></p>
  </div>

  <footer class="site">
    <span><a href="./">{A.e(P["retour"])}</a></span>
    <span><a href="{'en/' if lg == 'fr' else '../'}chant.html">{A.e(autre_nom)}</a></span>
    <span><a href="mentions.html">{A.e(P["mentions"])}</a></span>
  </footer>
</div>
{'<script>window.MCL_BASE = "../";</script>' if lg == "en" else ""}
<script src="{pre}reglages.js"></script>
<script src="{pre}commun.js"></script>
<script src="{pre}lang.js"></script>
{JS if expo else ""}
</body>
</html>
"""


# ---------------------------------------------------------------- programme

def ouverte(latest):
    etapes = (latest.get("ages") or {}).get("etapes") or []
    return len(etapes) > FONDATION and bool(etapes[FONDATION].get("ouvert"))


def mettre_a_jour(racine, source, attendre=0):
    chemin = racine / "chant.json"
    arch = A.lire(chemin, None) if chemin.exists() else None
    arch = arch or {"format": 1, "regle": REGLE, "jours": []}
    jours = arch["jours"]
    latest = A.lire(racine / "data" / "latest.json", {})
    if not ouverte(latest):
        print("chant : l'âge de la Fondation n'est pas ouvert, rien n'est transcrit (audit des déblocages)")
        return 0
    ere = int(latest.get("ere") or 1)
    fin = time.time() + attendre
    while True:
        fichiers = [f for f in A.manifeste(source, ere) if f.get("fichier")]
        pret = [f for f in fichiers if f.get("date") == latest.get("date")]
        if attendre and pret:
            # 1.0.2 : le manifeste peut annoncer le brut avant qu'il soit lisible (16/11/2026 : le soir n'a pas été
            # transcrit) ; pendant l'attente, on vérifie que le fichier se lit et correspond à son empreinte.
            try:
                o = A.charger(source, pret[0]["fichier"])
                if pret[0].get("sha256") and hashlib.sha256(o).hexdigest() != pret[0]["sha256"]:
                    raise ValueError("empreinte différente du manifeste")
            except Exception as err:
                print(f"Brut du soir annoncé mais pas encore lisible ({err})", file=sys.stderr)
                pret = []
        if not attendre or pret or time.time() > fin:
            break
        print("Fichier brut du soir pas encore publié : nouvel essai dans 60 s")
        time.sleep(60)
    fichiers.sort(key=lambda x: x.get("date") or "")
    deja = {(j.get("ere"), j.get("date")) for j in jours}
    derniere = max((j["date"] for j in jours if j.get("ere") == ere), default=None)
    # Premier soir (livraison ou nouvelle ère) : seulement le dernier brut publié, jamais les soirs passés.
    fichiers = fichiers[-1:] if derniere is None else [f for f in fichiers if f.get("date", "") > derniere]
    ajoutes = 0
    for f in fichiers:
        if (ere, f.get("date")) in deja:
            continue
        try:
            octets = A.charger(source, f["fichier"])
            if f.get("sha256") and hashlib.sha256(octets).hexdigest() != f["sha256"]:
                raise ValueError("empreinte différente du manifeste")
            brut = json.loads(octets)
        except Exception as err:
            print(f"Illisible : {f.get('fichier')} ({err}) ; nouvel essai au prochain passage", file=sys.stderr)
            break    # on n'expose jamais un soir avant le précédent
        if int(brut.get("format") or 0) < 3:
            continue
        ent = soiree(brut)
        ent["source"] = f["fichier"]
        jours.append(ent)
        deja.add((ere, f.get("date")))
        ajoutes += 1
    if ajoutes:
        chemin.write_text(json.dumps(arch, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    (racine / "chant.html").write_text(page(jours, latest, "fr"), encoding="utf-8")
    (racine / "en").mkdir(exist_ok=True)
    (racine / "en" / "chant.html").write_text(page(jours, latest, "en"), encoding="utf-8")
    print(f"chant : {ajoutes} soir(s) ajouté(s), {len(jours)} au total")
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
