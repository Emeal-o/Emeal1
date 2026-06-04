import streamlit as st
import fastf1
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
import os, warnings
warnings.filterwarnings("ignore")

os.makedirs("f1_cache", exist_ok=True)
fastf1.Cache.enable_cache("f1_cache")

st.set_page_config(page_title="F1 2026 Live Hub", page_icon="🏎", layout="wide", initial_sidebar_state="collapsed")

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
TEAM_COLORS = {
    "Mercedes":"#00D2BE","Ferrari":"#DC143C","Red Bull Racing":"#3671C6","Red Bull":"#3671C6",
    "McLaren":"#FF8000","Aston Martin":"#006F62","Alpine":"#0090FF","Williams":"#005AFF",
    "Racing Bulls":"#1E41D0","RB":"#1E41D0","Haas F1 Team":"#B6BABD","Haas":"#B6BABD",
    "Kick Sauber":"#00E48D","Audi":"#FF0000","Cadillac":"#CC0000",
}
TYRE_COLORS = {"SOFT":"#e8002d","MEDIUM":"#ffd700","HARD":"#f0f0f0","INTERMEDIATE":"#39b54a","WET":"#0067ff","UNKNOWN":"#444"}
TYRE_ABBR   = {"SOFT":"S","MEDIUM":"M","HARD":"H","INTERMEDIATE":"I","WET":"W","UNKNOWN":"?"}
TYRE_LIFE   = {"SOFT":22,"MEDIUM":35,"HARD":50,"INTERMEDIATE":40,"WET":55}

DRIVERS_2026 = {
    "ANT":{"name":"Kimi Antonelli",   "team":"Mercedes",        "num":12},
    "RUS":{"name":"George Russell",   "team":"Mercedes",        "num":63},
    "LEC":{"name":"Charles Leclerc",  "team":"Ferrari",         "num":16},
    "HAM":{"name":"Lewis Hamilton",   "team":"Ferrari",         "num":44},
    "NOR":{"name":"Lando Norris",     "team":"McLaren",         "num":4},
    "PIA":{"name":"Oscar Piastri",    "team":"McLaren",         "num":81},
    "VER":{"name":"Max Verstappen",   "team":"Red Bull Racing", "num":1},
    "HAD":{"name":"Isack Hadjar",     "team":"Red Bull Racing", "num":6},
    "ALO":{"name":"Fernando Alonso",  "team":"Aston Martin",    "num":14},
    "STR":{"name":"Lance Stroll",     "team":"Aston Martin",    "num":18},
    "SAI":{"name":"Carlos Sainz",     "team":"Williams",        "num":55},
    "ALB":{"name":"Alexander Albon",  "team":"Williams",        "num":23},
    "COL":{"name":"Franco Colapinto", "team":"Alpine",          "num":43},
    "GAS":{"name":"Pierre Gasly",     "team":"Alpine",          "num":10},
    "BEA":{"name":"Oliver Bearman",   "team":"Haas F1 Team",    "num":87},
    "OCO":{"name":"Esteban Ocon",     "team":"Haas F1 Team",    "num":31},
    "LAW":{"name":"Liam Lawson",      "team":"Racing Bulls",    "num":30},
    "LIN":{"name":"Arvid Lindblad",   "team":"Racing Bulls",    "num":8},
    "HUL":{"name":"Nico Hulkenberg",  "team":"Audi",            "num":27},
    "BOR":{"name":"Gabriel Bortoleto","team":"Audi",            "num":5},
}

CALENDAR = [
    {"round":1, "name":"Australian GP",    "circuit":"Melbourne Grand Prix Circuit","country":"Australia 🇦🇺","race":"2026-03-08","fp1":"2026-03-06 01:30","fp2":"2026-03-06 05:00","fp3":"2026-03-07 01:30","q":"2026-03-07 05:00","status":"done","winner":"George Russell","team":"Mercedes"},
    {"round":2, "name":"Chinese GP",       "circuit":"Shanghai International","country":"China 🇨🇳","race":"2026-03-15","fp1":"2026-03-13 03:30","fp2":"2026-03-13 07:00","fp3":"2026-03-14 03:30","q":"2026-03-14 07:00","status":"done","winner":"Kimi Antonelli","team":"Mercedes"},
    {"round":3, "name":"Japanese GP",      "circuit":"Suzuka International","country":"Japan 🇯🇵","race":"2026-03-29","fp1":"2026-03-27 02:30","fp2":"2026-03-27 06:00","fp3":"2026-03-28 02:30","q":"2026-03-28 06:00","status":"done","winner":"Kimi Antonelli","team":"Mercedes"},
    {"round":4, "name":"Bahrain GP",       "circuit":"Bahrain International Circuit","country":"Bahrain 🇧🇭","race":"2026-04-12","fp1":None,"fp2":None,"fp3":None,"q":None,"status":"cancelled","winner":None,"team":None},
    {"round":5, "name":"Saudi Arabian GP", "circuit":"Jeddah Corniche Circuit","country":"Saudi Arabia 🇸🇦","race":"2026-04-19","fp1":None,"fp2":None,"fp3":None,"q":None,"status":"cancelled","winner":None,"team":None},
    {"round":6, "name":"Miami GP",         "circuit":"Miami International Autodrome","country":"USA 🇺🇸","race":"2026-05-03","fp1":"2026-05-01 17:30","fp2":"2026-05-01 21:00","fp3":"2026-05-02 17:30","q":"2026-05-02 21:00","status":"done","winner":"Kimi Antonelli","team":"Mercedes"},
    {"round":7, "name":"Canadian GP",      "circuit":"Circuit Gilles-Villeneuve","country":"Canada 🇨🇦","race":"2026-05-24","fp1":"2026-05-22 18:30","fp2":"2026-05-22 22:00","fp3":"2026-05-23 17:30","q":"2026-05-23 21:00","status":"done","winner":"Kimi Antonelli","team":"Mercedes"},
    {"round":8, "name":"Monaco GP",        "circuit":"Circuit de Monaco","country":"Monaco 🇲🇨","race":"2026-06-07","fp1":"2026-06-05 11:30","fp2":"2026-06-05 15:00","fp3":"2026-06-06 10:30","q":"2026-06-06 14:00","status":"upcoming","winner":None,"team":None},
    {"round":9, "name":"Spanish GP",       "circuit":"Circuit de Barcelona-Catalunya","country":"Spain 🇪🇸","race":"2026-06-14","fp1":"2026-06-12 11:30","fp2":"2026-06-12 15:00","fp3":"2026-06-13 10:30","q":"2026-06-13 14:00","status":"upcoming","winner":None,"team":None},
    {"round":10,"name":"Austrian GP",      "circuit":"Red Bull Ring","country":"Austria 🇦🇹","race":"2026-06-28","fp1":"2026-06-26 11:30","fp2":"2026-06-26 15:00","fp3":"2026-06-27 10:30","q":"2026-06-27 14:00","status":"upcoming","winner":None,"team":None},
    {"round":11,"name":"British GP",       "circuit":"Silverstone Circuit","country":"UK 🇬🇧","race":"2026-07-05","fp1":"2026-07-03 11:30","fp2":"2026-07-03 15:00","fp3":"2026-07-04 10:30","q":"2026-07-04 14:00","status":"upcoming","winner":None,"team":None},
    {"round":12,"name":"Belgian GP",       "circuit":"Circuit de Spa-Francorchamps","country":"Belgium 🇧🇪","race":"2026-07-19","fp1":"2026-07-17 11:30","fp2":"2026-07-17 15:00","fp3":"2026-07-18 10:30","q":"2026-07-18 14:00","status":"upcoming","winner":None,"team":None},
    {"round":13,"name":"Hungarian GP",     "circuit":"Hungaroring","country":"Hungary 🇭🇺","race":"2026-07-26","fp1":"2026-07-24 11:30","fp2":"2026-07-24 15:00","fp3":"2026-07-25 10:30","q":"2026-07-25 14:00","status":"upcoming","winner":None,"team":None},
    {"round":14,"name":"Dutch GP",         "circuit":"Circuit Park Zandvoort","country":"Netherlands 🇳🇱","race":"2026-08-23","fp1":"2026-08-21 10:30","fp2":"2026-08-21 14:00","fp3":"2026-08-22 10:30","q":"2026-08-22 14:00","status":"upcoming","winner":None,"team":None},
    {"round":15,"name":"Italian GP",       "circuit":"Autodromo Nazionale Monza","country":"Italy 🇮🇹","race":"2026-09-06","fp1":"2026-09-04 11:30","fp2":"2026-09-04 15:00","fp3":"2026-09-05 10:30","q":"2026-09-05 14:00","status":"upcoming","winner":None,"team":None},
    {"round":16,"name":"Spanish GP 2",     "circuit":"Madring Circuit","country":"Spain 🇪🇸","race":"2026-09-13","fp1":"2026-09-11 11:30","fp2":"2026-09-11 15:00","fp3":"2026-09-12 10:30","q":"2026-09-12 14:00","status":"upcoming","winner":None,"team":None},
    {"round":17,"name":"Azerbaijan GP",    "circuit":"Baku City Circuit","country":"Azerbaijan 🇦🇿","race":"2026-09-26","fp1":"2026-09-24 09:30","fp2":"2026-09-24 13:00","fp3":"2026-09-25 09:30","q":"2026-09-25 13:00","status":"upcoming","winner":None,"team":None},
    {"round":18,"name":"Singapore GP",     "circuit":"Marina Bay Street Circuit","country":"Singapore 🇸🇬","race":"2026-10-11","fp1":"2026-10-09 09:30","fp2":"2026-10-09 13:00","fp3":"2026-10-10 09:30","q":"2026-10-10 13:00","status":"upcoming","winner":None,"team":None},
    {"round":19,"name":"United States GP", "circuit":"Circuit of the Americas","country":"USA 🇺🇸","race":"2026-10-25","fp1":"2026-10-23 18:30","fp2":"2026-10-23 22:00","fp3":"2026-10-24 17:30","q":"2026-10-24 21:00","status":"upcoming","winner":None,"team":None},
    {"round":20,"name":"Mexico City GP",   "circuit":"Autodromo Hermanos Rodriguez","country":"Mexico 🇲🇽","race":"2026-11-01","fp1":"2026-10-30 18:30","fp2":"2026-10-30 22:00","fp3":"2026-10-31 17:30","q":"2026-10-31 21:00","status":"upcoming","winner":None,"team":None},
    {"round":21,"name":"São Paulo GP",     "circuit":"Autodromo Jose Carlos Pace","country":"Brazil 🇧🇷","race":"2026-11-08","fp1":"2026-11-06 14:30","fp2":"2026-11-06 18:00","fp3":"2026-11-07 14:30","q":"2026-11-07 18:00","status":"upcoming","winner":None,"team":None},
    {"round":22,"name":"Las Vegas GP",     "circuit":"Las Vegas Street Circuit","country":"USA 🇺🇸","race":"2026-11-22","fp1":"2026-11-20 04:30","fp2":"2026-11-20 08:00","fp3":"2026-11-21 04:30","q":"2026-11-21 08:00","status":"upcoming","winner":None,"team":None},
    {"round":23,"name":"Qatar GP",         "circuit":"Losail International Circuit","country":"Qatar 🇶🇦","race":"2026-11-29","fp1":"2026-11-27 12:30","fp2":"2026-11-27 16:00","fp3":"2026-11-28 12:30","q":"2026-11-28 16:00","status":"upcoming","winner":None,"team":None},
    {"round":24,"name":"Abu Dhabi GP",     "circuit":"Yas Marina Circuit","country":"UAE 🇦🇪","race":"2026-12-06","fp1":"2026-12-04 09:30","fp2":"2026-12-04 13:00","fp3":"2026-12-05 09:30","q":"2026-12-05 13:00","status":"upcoming","winner":None,"team":None},
]

CIRCUIT_FACTS = {
    "Monaco GP":       {"laps":78,"km":"3.337","record":"1:12.909 Leclerc 2021","drs":1,"fact":"So narrow a modern F1 car is wider than some roads. Qualifying is almost everything."},
    "Australian GP":   {"laps":58,"km":"5.278","record":"1:20.235 Leclerc 2022","drs":3,"fact":"Temporary circuit around Albert Park lake. Always opens the F1 season."},
    "Chinese GP":      {"laps":56,"km":"5.451","record":"1:32.238 Bottas 2018","drs":2,"fact":"Long back straight perfect for DRS overtaking. One of the fastest circuits."},
    "Japanese GP":     {"laps":53,"km":"5.807","record":"1:30.983 Hamilton 2019","drs":2,"fact":"Suzuka's unique figure-8 layout. The 130R corner is one of the most famous in F1."},
    "Canadian GP":     {"laps":70,"km":"4.361","record":"1:13.078 Bottas 2019","drs":2,"fact":"The Wall of Champions has claimed multiple world champions in qualifying."},
    "British GP":      {"laps":52,"km":"5.891","record":"1:27.097 Hamilton 2020","drs":3,"fact":"Home of F1. Copse corner at 185mph is one of the fastest in the world."},
    "Spanish GP":      {"laps":66,"km":"4.675","record":"1:16.330 Rosberg 2016","drs":2,"fact":"Most tested circuit — teams know it better than any other on the calendar."},
    "Italian GP":      {"laps":53,"km":"5.793","record":"1:21.046 Barrichello 2004","drs":2,"fact":"The Temple of Speed. Highest average speeds of any F1 circuit."},
    "Belgian GP":      {"laps":44,"km":"7.004","record":"1:41.252 Bottas 2018","drs":2,"fact":"Eau Rouge/Raidillon is the most famous corner complex in motorsport."},
    "Singapore GP":    {"laps":62,"km":"4.940","record":"1:35.867 Leclerc 2023","drs":3,"fact":"The only F1 night race. Brutally hot and humid. Highest chance of Safety Car."},
    "Austrian GP":     {"laps":71,"km":"4.318","record":"1:02.939 Bottas 2020","drs":3,"fact":"Short, fast and furious. The Red Bull Ring sits in the stunning Styrian mountains."},
}

def tc(name):
    if not name: return "#888"
    for k,v in TEAM_COLORS.items():
        if k.lower() in (name or "").lower(): return v
    return "#888"

def driver_avatar(abbr, size=36):
    d = DRIVERS_2026.get(abbr, {})
    col = tc(d.get("team",""))
    initials = abbr[:3]
    return f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:{col};display:inline-flex;align-items:center;justify-content:center;font-size:{size//3}px;font-weight:900;color:#000;flex-shrink:0">{initials}</div>'

def fmt_lap(secs):
    if not secs or secs != secs: return "—"
    m=int(secs//60); s=secs%60
    return f"{m}:{s:06.3f}"

def fmt_countdown(dt_str):
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        diff = dt - datetime.utcnow()
        if diff.total_seconds() < 0: return "DONE", "#00c853"
        d=diff.days; h=diff.seconds//3600; m=(diff.seconds%3600)//60
        if d>0: return f"{d}d {h}h", "#e10600"
        if h>0: return f"{h}h {m}m", "#ffd700"
        return f"{m}m", "#00ff88"
    except: return "TBC", "#444"

# ── DATA ──────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3, show_spinner=False)
def get_openf1(endpoint, params=""):
    try:
        r = requests.get(f"https://api.openf1.org/v1/{endpoint}?{params}", timeout=8)
        if r.status_code==200: return r.json()
    except: pass
    return []

@st.cache_data(ttl=300, show_spinner=False)
def get_standings():
    drv, con = [], []
    try:
        h={"User-Agent":"Mozilla/5.0"}
        r=requests.get("https://www.formula1.com/en/results/2026/drivers",headers=h,timeout=12)
        if r.status_code==200:
            soup=BeautifulSoup(r.content,"html.parser")
            for row in soup.find_all("tr"):
                cols=row.find_all("td")
                if len(cols)>=5:
                    try:
                        pos=cols[0].text.strip()
                        name=" ".join(cols[1].text.strip().split()[:2])
                        team=cols[3].text.strip()
                        pts=cols[4].text.strip()
                        if pos.isdigit() and pts.replace(".","").isdigit():
                            drv.append({"pos":int(pos),"name":name,"team":team,"pts":float(pts)})
                    except: pass
    except: pass
    try:
        h={"User-Agent":"Mozilla/5.0"}
        r=requests.get("https://www.formula1.com/en/results/2026/team",headers=h,timeout=12)
        if r.status_code==200:
            soup=BeautifulSoup(r.content,"html.parser")
            for row in soup.find_all("tr"):
                cols=row.find_all("td")
                if len(cols)>=3:
                    try:
                        pos=cols[0].text.strip(); team=cols[1].text.strip(); pts=cols[2].text.strip()
                        if pos.isdigit() and pts.replace(".","").isdigit():
                            con.append({"pos":int(pos),"name":team,"pts":float(pts)})
                    except: pass
    except: pass
    return drv, con

@st.cache_data(ttl=3600, show_spinner=False)
def load_ff1(year, rnd, stype="R"):
    try:
        s=fastf1.get_session(year,rnd,stype)
        s.load(telemetry=False,weather=True,messages=True,laps=True)
        return s
    except: return None

def get_session_info():
    sessions=get_openf1("sessions","year=2026")
    now=datetime.now(timezone.utc)
    past=[s for s in sessions if s.get("date_start") and datetime.fromisoformat(s["date_start"].replace("Z","+00:00"))<now]
    if not past: return None,False,False
    latest=past[-1]
    start=datetime.fromisoformat(latest["date_start"].replace("Z","+00:00"))
    end_str=latest.get("date_end")
    end=datetime.fromisoformat(end_str.replace("Z","+00:00"))+timedelta(hours=1) if end_str else start+timedelta(hours=4)
    live=start-timedelta(minutes=5)<=now<=end
    recent=not live and (now-end)<timedelta(hours=30)
    return latest,live,recent

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;600;700;900&family=Space+Mono:wght@400;700&display=swap');
*,[class*="css"]{font-family:'Barlow Condensed',sans-serif!important}
.stApp{background:#050505!important;color:#f0f0f0!important}
.block-container{padding:0!important;max-width:100%!important}
/* HERO */
.hero{background:linear-gradient(180deg,#000 0%,#080808 100%);border-bottom:3px solid #e10600;padding:18px 24px 14px;position:relative;overflow:hidden}
.hero::before{content:'F1';position:absolute;right:-20px;top:-20px;font-size:200px;font-weight:900;color:rgba(225,6,0,.04);line-height:1;pointer-events:none}
.h-badge{background:#e10600;color:#fff;font-size:9px;font-weight:700;letter-spacing:4px;padding:3px 9px;text-transform:uppercase;display:inline-block;margin-bottom:5px}
.h-title{font-size:clamp(1.8rem,5vw,3.2rem);font-weight:900;text-transform:uppercase;letter-spacing:-1px;line-height:1}
.h-title b{color:#e10600}
.h-sub{font-family:'Space Mono',monospace;font-size:9px;color:#333;letter-spacing:2px;margin-top:3px}
/* STATUS */
.status{display:flex;align-items:center;gap:10px;padding:9px 24px;background:#080808;border-bottom:1px solid #111;flex-wrap:wrap}
.sdot{width:9px;height:9px;border-radius:50%;flex-shrink:0}
.sdot.live{background:#00ff88;animation:p 1.4s infinite}
.sdot.recent{background:#ffd700}
.sdot.off{background:#2a2a2a}
@keyframes p{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.3;transform:scale(.7)}}
.slabel{font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase}
.sbadge{font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;padding:2px 9px;border:1px solid}
.sbadge.live{color:#00ff88;border-color:#00ff88}
.sbadge.recent{color:#ffd700;border-color:#ffd700}
.sbadge.off{color:#333;border-color:#222}
/* TABS */
.stTabs [data-baseweb="tab-list"]{background:#000!important;border-bottom:1px solid #1a1a1a!important;padding:0 16px!important;gap:0!important;overflow-x:auto}
.stTabs [data-baseweb="tab"]{background:transparent!important;color:#333!important;font-family:'Barlow Condensed',sans-serif!important;font-size:11px!important;font-weight:700!important;letter-spacing:2px!important;text-transform:uppercase!important;padding:11px 14px!important;border-bottom:3px solid transparent!important;white-space:nowrap!important}
.stTabs [aria-selected="true"]{color:#e10600!important;border-bottom-color:#e10600!important}
.stTabs [data-baseweb="tab-panel"]{background:transparent!important;padding:18px 16px 60px!important}
/* METRIC */
.mrow{display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:8px;margin-bottom:16px}
.mc{background:#0d0d0d;border:1px solid #1a1a1a;padding:12px 10px;text-align:center;transition:border-color .2s}
.mc:hover{border-color:#e10600}
.mc-v{font-size:1.7rem;font-weight:900;color:#e10600;line-height:1;font-family:'Space Mono',monospace}
.mc-l{font-size:8px;letter-spacing:2px;text-transform:uppercase;color:#333;margin-top:3px}
/* SECTION */
.sec{font-size:.85rem;font-weight:900;letter-spacing:3px;text-transform:uppercase;color:#e10600;border-left:3px solid #e10600;padding-left:9px;margin:18px 0 12px}
/* TABLE */
.tw{background:#0d0d0d;border:1px solid #1a1a1a;overflow:hidden;margin-bottom:16px}
.th{background:#000;padding:9px 12px;border-bottom:1px solid #1a1a1a;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:6px}
.tt{font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#e10600}
.ts{font-family:'Space Mono',monospace;font-size:9px;color:#333}
/* TIMING ROW */
.tr-hdr{display:grid;grid-template-columns:32px 1fr 80px 75px 52px 48px 32px;padding:6px 12px;border-bottom:1px solid #1a1a1a;font-size:8px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#2a2a2a;background:#000}
.tr{display:grid;grid-template-columns:32px 1fr 80px 75px 52px 48px 32px;padding:8px 12px;border-bottom:1px solid #0d0d0d;align-items:center;transition:background .1s}
.tr:hover{background:rgba(225,6,0,.03)}
.tr.p1{background:rgba(225,6,0,.06)}
.tpos{font-family:'Space Mono',monospace;font-size:11px;font-weight:700;color:#333}
.tpos.f{color:#e10600}
.tnm{font-size:14px;font-weight:900}
.tteam{font-size:9px;color:#333;margin-top:1px}
.tgap{font-family:'Space Mono',monospace;font-size:11px;color:#444}
.tgap.l{color:#e10600;font-weight:700}
.tint{font-family:'Space Mono',monospace;font-size:10px;color:#333}
.tyre{display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:50%;font-size:9px;font-weight:900;color:#000}
.tpit{font-family:'Space Mono',monospace;font-size:10px;color:#333;text-align:center}
/* PROGRESS */
.prog-wrap{background:#0d0d0d;border:1px solid #1a1a1a;padding:14px 16px;margin-bottom:14px}
.prog-bar-bg{background:#1a1a1a;height:8px;border-radius:4px;overflow:hidden;margin-top:8px}
.prog-bar-fill{height:100%;background:linear-gradient(90deg,#e10600,#ff4444);border-radius:4px;transition:width .5s ease}
/* STANDINGS */
.sr{display:flex;align-items:center;gap:10px;padding:8px 12px;border-bottom:1px solid #0d0d0d;transition:background .1s}
.sr:hover{background:rgba(225,6,0,.03)}
.spos{font-family:'Space Mono',monospace;font-size:10px;color:#333;min-width:22px}
.snm{font-size:13px;font-weight:700;flex:1}
.steam{font-size:9px;color:#333;margin-top:1px}
.spts{font-family:'Space Mono',monospace;font-weight:700;font-size:13px;color:#e10600;min-width:40px;text-align:right}
.sbar{height:3px;background:#1a1a1a;margin-top:3px}
.sbar-fill{height:100%}
/* RESULTS */
.rr{display:grid;grid-template-columns:32px 1fr 100px 60px;padding:8px 12px;border-bottom:1px solid #0d0d0d;align-items:center;font-size:13px;transition:background .1s}
.rr:hover{background:rgba(225,6,0,.03)}
.rr.pod{background:rgba(225,6,0,.04)}
/* CALENDAR */
.cr{padding:10px 12px;border-bottom:1px solid #0d0d0d;transition:background .1s}
.cr:hover{background:rgba(225,6,0,.03)}
.cr.next{background:rgba(225,6,0,.06);border-left:3px solid #e10600}
.cr.done{opacity:.6}
.cr.can{opacity:.3}
/* WEATHER */
.wgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(95px,1fr));gap:8px;margin-bottom:16px}
.wc{background:#0d0d0d;border:1px solid #1a1a1a;padding:11px 9px;text-align:center}
.wv{font-size:1.3rem;font-weight:900;color:#e10600;line-height:1}
.wl{font-size:8px;letter-spacing:2px;text-transform:uppercase;color:#333;margin-top:2px}
/* RADIO */
.radio-row{display:flex;gap:10px;padding:9px 12px;border-bottom:1px solid #0d0d0d;align-items:flex-start}
.radio-time{font-family:'Space Mono',monospace;font-size:9px;color:#333;min-width:50px;margin-top:2px}
.radio-msg{font-size:12px;color:#bbb;line-height:1.5}
/* RC */
.rc-row{display:flex;gap:10px;padding:9px 12px;border-bottom:1px solid #0d0d0d;align-items:flex-start}
.rc-t{font-family:'Space Mono',monospace;font-size:9px;color:#333;min-width:50px;margin-top:2px}
.rc-b{font-size:8px;font-weight:700;letter-spacing:1px;padding:2px 6px;display:inline-block;margin-right:4px}
.rc-sc{background:rgba(255,215,0,.1);color:#ffd700;border:1px solid rgba(255,215,0,.2)}
.rc-red{background:rgba(225,6,0,.1);color:#e10600;border:1px solid rgba(225,6,0,.2)}
.rc-drs{background:rgba(0,200,80,.08);color:#00c850;border:1px solid rgba(0,200,80,.15)}
.rc-pen{background:rgba(255,165,0,.1);color:#ffa500;border:1px solid rgba(255,165,0,.2)}
.rc-inf{background:rgba(255,255,255,.03);color:#444;border:1px solid #1a1a1a}
.rc-msg{font-size:12px;color:#bbb;line-height:1.5}
/* HEAD TO HEAD */
.h2h{display:grid;grid-template-columns:1fr auto 1fr;gap:8px;align-items:center;padding:10px 12px;border-bottom:1px solid #0d0d0d}
.h2h-val{font-family:'Space Mono',monospace;font-size:13px;font-weight:700}
.h2h-lab{font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#333;text-align:center}
/* NEXT HERO */
.next-hero{background:linear-gradient(135deg,#0a0a0a,#111);border:1px solid #1a1a1a;border-left:4px solid #e10600;padding:20px;margin-bottom:16px}
.next-rnd{font-size:9px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#e10600;margin-bottom:4px}
.next-nm{font-size:clamp(1.6rem,4vw,2.8rem);font-weight:900;text-transform:uppercase;letter-spacing:-1px;line-height:1}
.next-circ{font-size:12px;color:#444;margin-top:4px;font-family:'Space Mono',monospace}
.next-cd{font-size:2.2rem;font-weight:900;color:#e10600;margin-top:10px;line-height:1;font-family:'Space Mono',monospace}
.next-dt{font-size:11px;color:#333;font-family:'Space Mono',monospace;margin-top:3px}
/* SESSION SCHED */
.sched-row{display:grid;grid-template-columns:60px 1fr 80px 80px;gap:0;padding:8px 12px;border-bottom:1px solid #0d0d0d;align-items:center;font-size:12px}
.sched-type{font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;padding:2px 7px;border:1px solid;text-align:center}
/* PIT PREDICTOR */
.pit-row{display:grid;grid-template-columns:40px 1fr 60px 80px 80px;gap:0;padding:8px 12px;border-bottom:1px solid #0d0d0d;align-items:center;font-size:12px}
/* EMPTY */
.empty{padding:28px 14px;text-align:center;color:#2a2a2a;font-size:12px;font-family:'Space Mono',monospace;line-height:1.8}
/* FL badge */
.fl{color:#c000ff;font-size:9px;font-weight:700;margin-left:4px}
/* SCROLLBAR */
::-webkit-scrollbar{width:4px;height:4px}
::-webkit-scrollbar-track{background:#050505}
::-webkit-scrollbar-thumb{background:#1a1a1a}
::-webkit-scrollbar-thumb:hover{background:#e10600}
@media(max-width:600px){
  .tr-hdr,.tr{grid-template-columns:28px 1fr 65px 55px 38px;}.tr .tint,.tr .tpit{display:none}
  .sched-row{grid-template-columns:50px 1fr 70px}
}
</style>
""", unsafe_allow_html=True)

# ── SESSION ───────────────────────────────────────────────────────────────────
sess, is_live, is_recent = get_session_info()
sk = sess.get("session_key") if sess else None
now_dt = datetime.now()

done = [r for r in CALENDAR if r["status"]=="done"]
upcoming = [r for r in CALENDAR if r["status"]=="upcoming"]
next_race = upcoming[0] if upcoming else None

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero">
  <div class="h-badge">Formula 1 · 2026 Season</div>
  <div class="h-title">Live <b>Season</b> Hub</div>
  <div class="h-sub">FastF1 + OpenF1 + F1 Official · {now_dt.strftime('%H:%M:%S UTC')} · Auto-refresh 3s</div>
</div>
""", unsafe_allow_html=True)

# ── STATUS ────────────────────────────────────────────────────────────────────
if is_live:
    dcls,bcls="live","live"
    stxt=f"🟢 LIVE — {sess.get('session_name','')} · {sess.get('location','')}, {sess.get('country_name','')}"
    btxt="LIVE"
elif is_recent and sess:
    dcls,bcls="recent","recent"
    stxt=f"Recent: {sess.get('session_name','')} · {sess.get('location','')}"
    btxt="RECENT"
else:
    dcls,bcls="off","off"
    days=(datetime.strptime(next_race["race"],"%Y-%m-%d")-now_dt).days if next_race else 0
    stxt=f"Off Weekend · Next: {next_race['name']} in {days}d" if next_race else "Off Weekend"
    btxt="OFF WEEKEND"

st.markdown(f"""
<div class="status">
  <div class="sdot {dcls}"></div>
  <span class="slabel">{stxt}</span>
  <span class="sbadge {bcls}">{btxt}</span>
</div>
""", unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────────────────────
tabs=st.tabs(["🏁 Live Timing","📊 Standings","📅 Season","🏆 Results","📈 Laps","📻 Radio & Control"])

# ════════════════════════════════════════════════════
# TAB 1 — LIVE TIMING
# ════════════════════════════════════════════════════
with tabs[0]:

    col_r, col_i = st.columns([1,4])
    with col_r:
        if st.button("⟳ Refresh",key="r1"): st.cache_data.clear(); st.rerun()

    # Session progress
    if is_live and sk:
        with st.spinner(""):
            laps_data = get_openf1("laps",f"session_key={sk}")
        if laps_data:
            current_lap = max((l.get("lap_number",0) for l in laps_data), default=0)
            total_laps = sess.get("total_laps") or 78
            pct = min(round(current_lap/total_laps*100),100)
            st.markdown(f"""
            <div class="prog-wrap">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <span style="font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#444">Session Progress</span>
                <span style="font-family:'Space Mono',monospace;font-size:11px;color:#e10600">Lap {current_lap} / {total_laps}</span>
              </div>
              <div class="prog-bar-bg"><div class="prog-bar-fill" style="width:{pct}%"></div></div>
            </div>
            """, unsafe_allow_html=True)

    if is_live or is_recent:
        if sk:
            with st.spinner(""):
                intervals  = get_openf1("intervals", f"session_key={sk}")
                drivers_r  = get_openf1("drivers",   f"session_key={sk}")
                stints_r   = get_openf1("stints",    f"session_key={sk}")
                pits_r     = get_openf1("pit",       f"session_key={sk}")
                laps_r     = get_openf1("laps",      f"session_key={sk}")

            drv_map={}
            for d in drivers_r:
                drv_map[d["driver_number"]]=d

            int_map={}
            for i in intervals:
                n=i["driver_number"]
                if n not in int_map or i["date"]>int_map[n]["date"]: int_map[n]=i

            stint_map={}
            for s in stints_r:
                n=s["driver_number"]
                if n not in stint_map or s.get("lap_start",0)>stint_map[n].get("lap_start",0): stint_map[n]=s

            pit_map={}
            for p in pits_r: pit_map[p["driver_number"]]=pit_map.get(p["driver_number"],0)+1

            # Fastest laps
            fl_map={}
            for l in laps_r:
                n=l.get("driver_number")
                t=l.get("lap_duration")
                if n and t and (n not in fl_map or t<fl_map[n]):
                    fl_map[n]=t

            rows=sorted(int_map.values(),key=lambda x:(
                0 if x.get("gap_to_leader") in [None,0,"0"] else
                float(str(x.get("gap_to_leader","9999")).replace("+","") or 9999)
            ))

            if rows:
                overall_fl_driver = min(fl_map, key=fl_map.get) if fl_map else None
                sname=f"{sess.get('session_name','')} · {sess.get('location','')}"

                # Gap visualization chart (HTML-based, no Plotly)
                st.markdown('<div class="sec">Gap to Leader</div>', unsafe_allow_html=True)
                st.markdown('<div class="tw"><div style="padding:12px 16px">', unsafe_allow_html=True)
                max_gap=2.0
                for row in rows[:10]:
                    n=row["driver_number"]; drv=drv_map.get(n,{}); team=drv.get("team_name","")
                    col=tc(team); abbr=drv.get("name_acronym",f"#{n}")
                    gap=row.get("gap_to_leader",0)
                    try: gap_f=float(str(gap).replace("+","")) if gap and gap!=0 else 0
                    except: gap_f=0
                    pct_g=min(round(gap_f/max_gap*100),100)
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:8px;margin:4px 0">
                      <div style="min-width:35px;font-size:11px;font-weight:900;color:{col}">{abbr}</div>
                      <div style="flex:1;background:#1a1a1a;height:16px;position:relative">
                        <div style="width:{pct_g}%;background:{col};height:100%;min-width:2px"></div>
                      </div>
                      <div style="min-width:55px;font-family:'Space Mono',monospace;font-size:10px;color:#555;text-align:right">{'+'+str(gap) if gap and gap!=0 else 'LEADER'}</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div></div>', unsafe_allow_html=True)

                # Main timing tower
                st.markdown(f'<div class="sec">Timing Tower — {sname}</div>', unsafe_allow_html=True)
                st.markdown(f"""
                <div class="tw">
                  <div class="th"><span class="tt">{sname}</span><span class="ts">{len(rows)} cars · {'🔴 LIVE' if is_live else '🟡 Recent'}</span></div>
                  <div class="tr-hdr"><div>POS</div><div>DRIVER</div><div>GAP</div><div>INTERVAL</div><div>TYRE</div><div>LAPS</div><div>PIT</div></div>
                """, unsafe_allow_html=True)

                for idx,row in enumerate(rows):
                    n=row["driver_number"]; drv=drv_map.get(n,{})
                    abbr=drv.get("name_acronym",f"#{n}"); team=drv.get("team_name",""); col=tc(team)
                    stint=stint_map.get(n,{}); compound=(stint.get("compound") or "UNKNOWN").upper()
                    tc_col=TYRE_COLORS.get(compound,"#444"); ta=TYRE_ABBR.get(compound,"?")
                    tl="?"
                    if stint.get("tyre_age_at_start") is not None and stint.get("lap_end") is not None:
                        tl=stint["lap_end"]-stint.get("lap_start",0)+stint["tyre_age_at_start"]
                    pits=pit_map.get(n,0)
                    gap="LEADER" if idx==0 else (f"+{row['gap_to_leader']}" if row.get("gap_to_leader") else "—")
                    intv="—" if idx==0 else (f"+{row['interval']}" if row.get("interval") else "—")
                    txt="#000" if compound not in ["UNKNOWN"] else "#888"
                    fl_badge='<span class="fl">⬡FL</span>' if n==overall_fl_driver else ""
                    # Pit predictor
                    pred=""
                    if tl!="?" and compound in TYRE_LIFE:
                        laps_left=TYRE_LIFE[compound]-int(tl)
                        if laps_left>0: pred=f"+{laps_left}L"
                        else: pred="PIT!"
                    st.markdown(f"""
                    <div class="tr {'p1' if idx==0 else ''}">
                      <div class="tpos {'f' if idx==0 else ''}">{idx+1}</div>
                      <div>
                        <div class="tnm" style="color:{col}">{abbr}{fl_badge}</div>
                        <div class="tteam">{team}</div>
                      </div>
                      <div class="tgap {'l' if idx==0 else ''}">{gap}</div>
                      <div class="tint">{intv}</div>
                      <div><span class="tyre" style="background:{tc_col};color:{txt}">{ta}</span></div>
                      <div style="font-family:'Space Mono',monospace;font-size:10px;color:#444">{tl}</div>
                      <div class="tpit" style="color:{'#e10600' if pred=='PIT!' else '#333'}">{pits or pred or '—'}</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

                # Fastest lap leaderboard
                if fl_map:
                    st.markdown('<div class="sec">Fastest Laps</div>', unsafe_allow_html=True)
                    fl_sorted=sorted(fl_map.items(),key=lambda x:x[1])
                    fastest=fl_sorted[0][1]
                    st.markdown('<div class="tw">', unsafe_allow_html=True)
                    for i,(n,t) in enumerate(fl_sorted[:10]):
                        drv=drv_map.get(n,{}); team=drv.get("team_name",""); col=tc(team)
                        abbr=drv.get("name_acronym",f"#{n}")
                        gap=t-fastest
                        gap_str="⬡ FASTEST" if i==0 else f"+{gap:.3f}s"
                        gap_col="#c000ff" if i==0 else "#444"
                        st.markdown(f"""
                        <div style="display:grid;grid-template-columns:28px 50px 120px 1fr;padding:7px 12px;border-bottom:1px solid #0d0d0d;align-items:center;font-size:12px;{'background:rgba(192,0,255,.05)' if i==0 else ''}">
                          <div style="font-family:'Space Mono',monospace;font-size:10px;color:#333">{i+1}</div>
                          <div style="font-weight:900;color:{col}">{abbr}</div>
                          <div style="font-family:'Space Mono',monospace;font-size:11px">{fmt_lap(t)}</div>
                          <div style="font-family:'Space Mono',monospace;font-size:10px;color:{gap_col}">{gap_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                # Stint tracker
                if stint_map:
                    st.markdown('<div class="sec">Live Stint Tracker</div>', unsafe_allow_html=True)
                    st.markdown('<div class="tw"><div style="padding:12px 16px">', unsafe_allow_html=True)
                    for n,s in sorted(stint_map.items()):
                        drv=drv_map.get(n,{}); team=drv.get("team_name",""); col=tc(team)
                        abbr=drv.get("name_acronym",f"#{n}")
                        comp=(s.get("compound") or "UNKNOWN").upper()
                        age=s.get("tyre_age_at_start",0)
                        ls=s.get("lap_start",0); le=s.get("lap_end",ls)
                        stint_laps=le-ls+age
                        max_life=TYRE_LIFE.get(comp,30)
                        pct=min(round(stint_laps/max_life*100),100)
                        tc_col=TYRE_COLORS.get(comp,"#444")
                        warn="⚠️" if pct>85 else ""
                        st.markdown(f"""
                        <div style="display:grid;grid-template-columns:40px 30px 1fr 40px;gap:8px;align-items:center;margin:5px 0">
                          <div style="font-size:11px;font-weight:900;color:{col}">{abbr}</div>
                          <div><span class="tyre" style="background:{tc_col};color:#000">{TYRE_ABBR.get(comp,'?')}</span></div>
                          <div style="background:#1a1a1a;height:14px;border-radius:2px;overflow:hidden">
                            <div style="width:{pct}%;background:{tc_col};height:100%"></div>
                          </div>
                          <div style="font-family:'Space Mono',monospace;font-size:9px;color:#444">{warn}{stint_laps}L</div>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown("</div></div>", unsafe_allow_html=True)

    else:
        # Off weekend
        if next_race:
            rd=datetime.strptime(next_race["race"],"%Y-%m-%d")
            days=(rd-now_dt).days
            facts=CIRCUIT_FACTS.get(next_race["name"],{})
            st.markdown(f"""
            <div class="next-hero">
              <div class="next-rnd">Round {next_race['round']} · Next Race</div>
              <div class="next-nm">{next_race['name']}</div>
              <div class="next-circ">{next_race['circuit']} · {next_race['country']}</div>
              <div class="next-cd">{days} day{'s' if days!=1 else ''} away</div>
              <div class="next-dt">{rd.strftime('%d %B %Y')} · Race Start 15:00 Local</div>
              {f'<div style="font-size:11px;color:#333;margin-top:10px;font-style:italic;line-height:1.6">💡 {facts["fact"]}</div>' if facts.get("fact") else ''}
              {f'<div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap"><span style="background:#0d0d0d;border:1px solid #1a1a1a;padding:4px 10px;font-size:10px;font-family:Space Mono,monospace">🔄 {facts["laps"]} laps</span><span style="background:#0d0d0d;border:1px solid #1a1a1a;padding:4px 10px;font-size:10px;font-family:Space Mono,monospace">📏 {facts["km"]} km</span><span style="background:#0d0d0d;border:1px solid #1a1a1a;padding:4px 10px;font-size:10px;font-family:Space Mono,monospace">🚦 {facts["drs"]} DRS zones</span><span style="background:#0d0d0d;border:1px solid #1a1a1a;padding:4px 10px;font-size:10px;font-family:Space Mono,monospace">⏱ {facts["record"]}</span></div>' if facts else ''}
            </div>
            """, unsafe_allow_html=True)

        if done:
            last=done[-1]; wcol=tc(last.get("team",""))
            st.markdown(f'<div class="sec">Last Race — {last["name"]}</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="tw"><div style="padding:18px">
              <div style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#333;margin-bottom:6px">Race Winner · Round {last['round']}</div>
              <div style="font-size:2rem;font-weight:900;color:{wcol}">{last.get('winner','TBC')}</div>
              <div style="font-size:12px;color:#333;margin-top:3px">{last.get('team','')} · {last['circuit']}</div>
            </div></div>
            """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════
# TAB 2 — STANDINGS + HEAD TO HEAD
# ════════════════════════════════════════════════════
with tabs[1]:
    with st.spinner("Loading standings…"):
        drv_std, con_std = get_standings()

    src="formula1.com (official)" if drv_std else "estimated fallback"
    st.markdown(f'<div style="font-family:Space Mono,monospace;font-size:9px;color:#222;padding:5px 12px;background:#080808;border-bottom:1px solid #111">📡 {src}</div>', unsafe_allow_html=True)

    FALLBACK_DRV=[
        {"pos":1,"name":"Kimi Antonelli","team":"Mercedes","pts":131},
        {"pos":2,"name":"George Russell","team":"Mercedes","pts":88},
        {"pos":3,"name":"Charles Leclerc","team":"Ferrari","pts":75},
        {"pos":4,"name":"Lewis Hamilton","team":"Ferrari","pts":72},
        {"pos":5,"name":"Lando Norris","team":"McLaren","pts":58},
        {"pos":6,"name":"Oscar Piastri","team":"McLaren","pts":48},
        {"pos":7,"name":"Max Verstappen","team":"Red Bull Racing","pts":43},
        {"pos":8,"name":"Franco Colapinto","team":"Alpine","pts":32},
        {"pos":9,"name":"Oliver Bearman","team":"Haas F1 Team","pts":25},
        {"pos":10,"name":"Liam Lawson","team":"Racing Bulls","pts":20},
        {"pos":11,"name":"Isack Hadjar","team":"Red Bull Racing","pts":18},
        {"pos":12,"name":"Pierre Gasly","team":"Alpine","pts":14},
        {"pos":13,"name":"Carlos Sainz","team":"Williams","pts":9},
        {"pos":14,"name":"Arvid Lindblad","team":"Racing Bulls","pts":8},
        {"pos":15,"name":"Fernando Alonso","team":"Aston Martin","pts":7},
        {"pos":16,"name":"Lance Stroll","team":"Aston Martin","pts":5},
        {"pos":17,"name":"Gabriel Bortoleto","team":"Audi","pts":4},
        {"pos":18,"name":"Esteban Ocon","team":"Haas F1 Team","pts":2},
        {"pos":19,"name":"Alexander Albon","team":"Williams","pts":1},
        {"pos":20,"name":"Nico Hulkenberg","team":"Audi","pts":0},
    ]
    FALLBACK_CON=[
        {"pos":1,"name":"Mercedes","pts":219},{"pos":2,"name":"Ferrari","pts":147},
        {"pos":3,"name":"McLaren","pts":106},{"pos":4,"name":"Red Bull Racing","pts":61},
        {"pos":5,"name":"Alpine","pts":46},{"pos":6,"name":"Racing Bulls","pts":28},
        {"pos":7,"name":"Haas F1 Team","pts":27},{"pos":8,"name":"Aston Martin","pts":12},
        {"pos":9,"name":"Williams","pts":10},{"pos":10,"name":"Audi","pts":4},{"pos":11,"name":"Cadillac","pts":0},
    ]

    if not drv_std: drv_std=FALLBACK_DRV
    if not con_std: con_std=FALLBACK_CON

    col_d, col_c = st.columns(2)

    with col_d:
        st.markdown('<div class="sec">Drivers</div>', unsafe_allow_html=True)
        max_d=drv_std[0]["pts"] if drv_std else 1
        st.markdown('<div class="tw">', unsafe_allow_html=True)
        for d in drv_std:
            col=tc(d.get("team",""))
            pct=round(d["pts"]/max_d*100) if max_d>0 else 0
            # driver avatar
            initials=d["name"].split()[0][0]+d["name"].split()[-1][:2] if len(d["name"].split())>1 else d["name"][:3]
            st.markdown(f"""
            <div class="sr">
              <div class="spos">{d['pos']}</div>
              <div style="width:28px;height:28px;border-radius:50%;background:{col};display:inline-flex;align-items:center;justify-content:center;font-size:9px;font-weight:900;color:#000;flex-shrink:0">{initials[:2].upper()}</div>
              <div style="flex:1;min-width:0;margin-left:8px">
                <div class="snm" style="color:{col}">{d['name']}</div>
                <div class="steam">{d.get('team','')}</div>
                <div class="sbar"><div class="sbar-fill" style="width:{pct}%;background:{col}"></div></div>
              </div>
              <div class="spts">{int(d['pts'])}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_c:
        st.markdown('<div class="sec">Constructors</div>', unsafe_allow_html=True)
        max_c=con_std[0]["pts"] if con_std else 1
        st.markdown('<div class="tw">', unsafe_allow_html=True)
        for c in con_std:
            col=tc(c.get("name",""))
            pct=round(c["pts"]/max_c*100) if max_c>0 else 0
            st.markdown(f"""
            <div class="sr">
              <div class="spos">{c['pos']}</div>
              <div style="flex:1;min-width:0">
                <div class="snm" style="color:{col}">{c['name']}</div>
                <div class="sbar"><div class="sbar-fill" style="width:{pct}%;background:{col}"></div></div>
              </div>
              <div class="spts">{int(c['pts'])}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Head to Head
    st.markdown('<div class="sec">Driver Head to Head</div>', unsafe_allow_html=True)
    driver_names=[d["name"] for d in drv_std]
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        d1_name=st.selectbox("Driver 1",driver_names,index=0,key="h2h1")
    with col_h2:
        d2_name=st.selectbox("Driver 2",driver_names,index=2,key="h2h2")

    d1=next((d for d in drv_std if d["name"]==d1_name),None)
    d2=next((d for d in drv_std if d["name"]==d2_name),None)

    if d1 and d2:
        col1=tc(d1.get("team","")); col2=tc(d2.get("team",""))
        metrics=[
            ("Championship Pts",int(d1["pts"]),int(d2["pts"]),"pts"),
            ("Position",d1["pos"],d2["pos"],"pos",True),
        ]
        st.markdown(f"""
        <div class="tw">
          <div class="th">
            <span style="font-size:13px;font-weight:900;color:{col1}">{d1_name}</span>
            <span style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#333">vs</span>
            <span style="font-size:13px;font-weight:900;color:{col2}">{d2_name}</span>
          </div>
          <div class="h2h">
            <div style="text-align:right"><div class="h2h-val" style="color:{col1}">{int(d1['pts'])}</div><div style="font-size:9px;color:#333">{d1.get('team','')}</div></div>
            <div class="h2h-lab">POINTS</div>
            <div><div class="h2h-val" style="color:{col2}">{int(d2['pts'])}</div><div style="font-size:9px;color:#333">{d2.get('team','')}</div></div>
          </div>
          <div class="h2h">
            <div style="text-align:right"><div class="h2h-val" style="color:{col1}">P{d1['pos']}</div></div>
            <div class="h2h-lab">STANDING</div>
            <div><div class="h2h-val" style="color:{col2}">P{d2['pos']}</div></div>
          </div>
          <div class="h2h">
            <div style="text-align:right"><div class="h2h-val" style="color:{col1}">{int(d1['pts'])-int(d2['pts'])}</div></div>
            <div class="h2h-lab">PTS GAP</div>
            <div><div class="h2h-val" style="color:{col2}">{int(d2['pts'])-int(d1['pts'])}</div></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Lap delta if FastF1 data available
        st.markdown('<div style="font-size:10px;color:#333;font-family:Space Mono,monospace;padding:8px 12px">📈 Qualifying lap delta from completed rounds (FastF1)</div>', unsafe_allow_html=True)
        d1_abbr=next((k for k,v in DRIVERS_2026.items() if v["name"]==d1_name),None)
        d2_abbr=next((k for k,v in DRIVERS_2026.items() if v["name"]==d2_name),None)

        if d1_abbr and d2_abbr:
            h2h_data=[]
            for race in done[:5]:
                try:
                    ff1_q=load_ff1(2026,race["round"],"Q")
                    if ff1_q and ff1_q.results is not None:
                        r1=ff1_q.results[ff1_q.results["Abbreviation"]==d1_abbr]
                        r2=ff1_q.results[ff1_q.results["Abbreviation"]==d2_abbr]
                        if len(r1)>0 and len(r2)>0:
                            t1=r1.iloc[0].get("Q3") or r1.iloc[0].get("Q2") or r1.iloc[0].get("Q1")
                            t2=r2.iloc[0].get("Q3") or r2.iloc[0].get("Q2") or r2.iloc[0].get("Q1")
                            if pd.notna(t1) and pd.notna(t2):
                                delta=t1.total_seconds()-t2.total_seconds()
                                h2h_data.append({"race":f"R{race['round']}","delta":delta,"d1_faster":delta<0})
                except: pass

            if h2h_data:
                st.markdown('<div class="tw">', unsafe_allow_html=True)
                st.markdown(f'<div style="display:grid;grid-template-columns:50px 1fr 80px;padding:6px 12px;border-bottom:2px solid #e10600;font-size:8px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#333;background:#000"><div>ROUND</div><div>LAP DELTA (QUALIFYING)</div><div>FASTER</div></div>', unsafe_allow_html=True)
                for h in h2h_data:
                    w_col=col1 if h["d1_faster"] else col2
                    w_name=d1_name.split()[-1] if h["d1_faster"] else d2_name.split()[-1]
                    bar_pct=min(abs(h["delta"])/2*100,100)
                    bar_dir="right" if h["d1_faster"] else "left"
                    st.markdown(f"""
                    <div style="display:grid;grid-template-columns:50px 1fr 80px;padding:8px 12px;border-bottom:1px solid #0d0d0d;align-items:center;font-size:12px">
                      <div style="font-family:'Space Mono',monospace;font-size:10px;color:#333">{h['race']}</div>
                      <div style="background:#1a1a1a;height:12px;position:relative">
                        <div style="width:{bar_pct}%;background:{w_col};height:100%;{'margin-left:auto' if not h['d1_faster'] else ''}"></div>
                      </div>
                      <div style="font-size:11px;color:{w_col};font-weight:700;text-align:right">{w_name} +{abs(h['delta']):.3f}s</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty">Head-to-head qualifying data loads via FastF1 1-2 days after each race</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════
# TAB 3 — SEASON CALENDAR
# ════════════════════════════════════════════════════
with tabs[2]:
    done_cnt=len([r for r in CALENDAR if r["status"]=="done"])
    can_cnt=len([r for r in CALENDAR if r["status"]=="cancelled"])
    rem_cnt=len([r for r in CALENDAR if r["status"]=="upcoming"])

    st.markdown(f"""
    <div class="mrow">
      <div class="mc"><div class="mc-v">{done_cnt}</div><div class="mc-l">Done</div></div>
      <div class="mc"><div class="mc-v">{can_cnt}</div><div class="mc-l">Cancelled</div></div>
      <div class="mc"><div class="mc-v">{rem_cnt}</div><div class="mc-l">Remaining</div></div>
      <div class="mc"><div class="mc-v">24</div><div class="mc-l">Total Rounds</div></div>
    </div>
    """, unsafe_allow_html=True)

    next_rnd=next((r["round"] for r in CALENDAR if r["status"]=="upcoming"),99)

    for race in CALENDAR:
        rd=datetime.strptime(race["race"],"%Y-%m-%d")
        days=(rd-now_dt).days
        is_next=race["round"]==next_rnd
        row_cls="next" if is_next else race["status"]

        if race["status"]=="done":
            stat=f'<span style="color:#00c853;font-size:10px;font-weight:700">✓ DONE</span>'
            wcol=tc(race.get("team",""))
            win_html=f'<div style="font-size:10px;color:{wcol};margin-top:2px">🏆 {race["winner"]}</div>' if race.get("winner") else ""
        elif race["status"]=="cancelled":
            stat=f'<span style="color:#2a2a2a;font-size:10px;font-weight:700">✕ CANCELLED</span>'
            win_html=""
        elif is_next:
            stat=f'<span style="color:#e10600;font-size:10px;font-weight:700">NEXT · {days}d</span>'
            win_html=""
        else:
            stat=f'<span style="color:#333;font-size:10px">in {days}d</span>'
            win_html=""

        st.markdown(f"""
        <div class="cr {row_cls}" style="display:grid;grid-template-columns:32px 1fr 60px 80px;align-items:center;gap:0">
          <div style="font-family:'Space Mono',monospace;font-size:9px;color:#2a2a2a">R{race['round']}</div>
          <div>
            <div style="font-size:13px;font-weight:700;{'color:#f0f0f0' if is_next or race['status']=='upcoming' else 'color:#555' if race['status']=='done' else 'color:#2a2a2a'}">{race['name']}</div>
            <div style="font-size:9px;color:#2a2a2a">{race['circuit']} · {race['country']}</div>
            {win_html}
          </div>
          <div style="font-family:'Space Mono',monospace;font-size:10px;color:#333">{rd.strftime('%d %b')}</div>
          <div>{stat}</div>
        </div>
        """, unsafe_allow_html=True)

        # Session schedule for upcoming races
        if is_next and race.get("fp1"):
            sessions_sched=[
                ("FP1",race.get("fp1")),("FP2",race.get("fp2")),
                ("FP3",race.get("fp3")),("QUALI",race.get("q")),("RACE",race.get("race")+" 15:00"),
            ]
            type_colors={"FP1":"#444","FP2":"#444","FP3":"#444","QUALI":"#ffd700","RACE":"#e10600"}
            st.markdown('<div style="background:#080808;border:1px solid #111;border-top:none;padding:10px 12px">', unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#333;margin-bottom:8px">Session Schedule · {race["country"]}</div>', unsafe_allow_html=True)
            for stype, stime in sessions_sched:
                if stype=="RACE": stime=race["race"]+" 15:00"
                if not stime: continue
                cd, cd_col = fmt_countdown(stime)
                sc=type_colors.get(stype,"#444")
                try: dt_str=datetime.strptime(stime,"%Y-%m-%d %H:%M").strftime("%d %b %H:%M UTC")
                except: dt_str=stime
                st.markdown(f"""
                <div style="display:grid;grid-template-columns:55px 1fr 80px 70px;padding:5px 0;border-bottom:1px solid #0d0d0d;align-items:center;font-size:11px">
                  <span style="font-size:8px;font-weight:700;letter-spacing:1px;padding:2px 6px;border:1px solid {sc};color:{sc}">{stype}</span>
                  <div style="font-family:'Space Mono',monospace;font-size:9px;color:#333;padding-left:8px">{dt_str}</div>
                  <div style="font-family:'Space Mono',monospace;font-size:10px;color:{cd_col};text-align:right">{cd}</div>
                  <div></div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════
# TAB 4 — RESULTS
# ════════════════════════════════════════════════════
with tabs[3]:
    st.markdown('<div class="sec">Race Results — Full Classification</div>', unsafe_allow_html=True)
    if not done:
        st.markdown('<div class="empty">No completed races yet</div>', unsafe_allow_html=True)
    else:
        race_opts={f"R{r['round']}: {r['name']} ({datetime.strptime(r['race'],'%Y-%m-%d').strftime('%d %b')})":r["round"] for r in done}
        sel_name=st.selectbox("Select Race",list(race_opts.keys()),key="rsel")
        sel_rnd=race_opts[sel_name]
        sel_info=next(r for r in CALENDAR if r["round"]==sel_rnd)

        col_race, col_q = st.columns([3,2])

        with col_race:
            st.markdown(f'<div class="sec">{sel_info["name"]} · Race</div>', unsafe_allow_html=True)
            with st.spinner("Loading via FastF1…"):
                ff1r=load_ff1(2026,sel_rnd,"R")

            if ff1r and ff1r.results is not None and len(ff1r.results)>0:
                st.markdown('<div style="font-family:Space Mono,monospace;font-size:9px;color:#222;padding:4px 12px;background:#080808">📡 FastF1 official timing</div>', unsafe_allow_html=True)
                st.markdown(f"""
                <div class="tw">
                  <div style="display:grid;grid-template-columns:32px 1fr 100px 60px;padding:6px 12px;border-bottom:2px solid #e10600;font-size:8px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#2a2a2a;background:#000">
                    <div>P</div><div>DRIVER</div><div>TIME</div><div>PTS</div>
                  </div>
                """, unsafe_allow_html=True)
                for _,row in ff1r.results.iterrows():
                    pos=str(row.get("Position","?"))
                    status=str(row.get("Status",""))
                    is_dnf=status not in ["Finished","+1 Lap","+2 Laps","+3 Laps",""] and not status.startswith("+")
                    medal="🥇" if pos=="1" else "🥈" if pos=="2" else "🥉" if pos=="3" else pos
                    fn=str(row.get("FirstName",""))[:1]; ln=str(row.get("LastName","?"))
                    team=row.get("TeamName",""); col=tc(team)
                    time_v=str(row.get("Time","")) if not is_dnf else f"DNF · {status}"
                    try: time_v=str(time_v).split("0 days ")[-1][:12]
                    except: pass
                    pts=int(row.get("Points",0))
                    fl=row.get("FastestLap")==True
                    abbr=row.get("Abbreviation","???")
                    initials=(fn+ln[:2]).upper()[:3]
                    st.markdown(f"""
                    <div class="rr {'pod' if pos in ['1','2','3'] else ''}">
                      <div style="font-size:{'1rem' if pos in ['1','2','3'] else '11px'};font-family:'Space Mono',monospace">{medal}</div>
                      <div style="display:flex;align-items:center;gap:8px">
                        <div style="width:24px;height:24px;border-radius:50%;background:{col};display:inline-flex;align-items:center;justify-content:center;font-size:7px;font-weight:900;color:#000;flex-shrink:0">{initials}</div>
                        <div>
                          <div style="font-size:13px;font-weight:700;color:{col}">{abbr}{'<span class="fl">⬡FL</span>' if fl else ''}</div>
                          <div style="font-size:9px;color:#333">{team}</div>
                        </div>
                      </div>
                      <div style="font-family:'Space Mono',monospace;font-size:10px;color:{'#e10600' if is_dnf else '#555'}">{time_v}</div>
                      <div style="font-family:'Space Mono',monospace;font-weight:700;font-size:11px;color:{col}">+{pts}</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

                # DNFs
                dnfs=ff1r.results[~ff1r.results["Status"].isin(["Finished","+1 Lap","+2 Laps","+3 Laps",""])]
                dnfs=dnfs[~dnfs["Status"].str.startswith("+",na=False)]
                if len(dnfs)>0:
                    st.markdown('<div class="sec">Retirements</div>', unsafe_allow_html=True)
                    st.markdown('<div class="tw">', unsafe_allow_html=True)
                    for _,row in dnfs.iterrows():
                        abbr=row.get("Abbreviation","?"); team=row.get("TeamName",""); col=tc(team)
                        st.markdown(f'<div style="padding:7px 12px;border-bottom:1px solid #0d0d0d;font-size:12px"><span style="color:{col};font-weight:700">{abbr}</span> <span style="color:#333;font-family:Space Mono,monospace;font-size:10px">{row.get("Status","")}</span></div>', unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                HARDCODED={
                    1:[("George Russell","Mercedes","1:23:45.XXX",25,False),("Kimi Antonelli","Mercedes","+12s",18,False),("Charles Leclerc","Ferrari","+18s",15,True)],
                    2:[("Kimi Antonelli","Mercedes","1:XX:XX",25,True),("George Russell","Mercedes","+Xs",18,False),("Charles Leclerc","Ferrari","+XXs",15,False)],
                    3:[("Kimi Antonelli","Mercedes","1:XX:XX",25,False),("Oscar Piastri","McLaren","+13.7s",18,True),("George Russell","Mercedes","+XXs",15,False)],
                    6:[("Kimi Antonelli","Mercedes","1:XX:XX",25,False),("Lando Norris","McLaren","+Xs",18,True),("Charles Leclerc","Ferrari","+XXs",15,False)],
                    7:[("Kimi Antonelli","Mercedes","1:XX:XX",25,False),("Lewis Hamilton","Ferrari","+10.7s",18,False),("George Russell","Mercedes","+XXs",15,True)],
                }
                results=HARDCODED.get(sel_rnd,[])
                st.markdown('<div style="font-family:Space Mono,monospace;font-size:9px;color:#222;padding:4px 12px;background:#080808">📡 FastF1 loading · Known results shown</div>', unsafe_allow_html=True)
                if results:
                    medals=["🥇","🥈","🥉"]
                    st.markdown('<div class="tw">', unsafe_allow_html=True)
                    for i,(name,team,time_v,pts,fl) in enumerate(results):
                        col=tc(team); abbr=name.split()[-1][:3].upper()
                        initials=(name.split()[0][0]+name.split()[-1][:2]).upper()
                        st.markdown(f"""
                        <div class="rr pod">
                          <div style="font-size:1rem">{medals[i]}</div>
                          <div style="display:flex;align-items:center;gap:8px">
                            <div style="width:24px;height:24px;border-radius:50%;background:{col};display:inline-flex;align-items:center;justify-content:center;font-size:7px;font-weight:900;color:#000">{initials}</div>
                            <div><div style="font-size:13px;font-weight:700;color:{col}">{abbr}{'<span class="fl">⬡FL</span>' if fl else ''}</div><div style="font-size:9px;color:#333">{team}</div></div>
                          </div>
                          <div style="font-family:'Space Mono',monospace;font-size:10px;color:#555">{time_v}</div>
                          <div style="font-family:'Space Mono',monospace;font-weight:700;font-size:11px;color:{col}">+{pts}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="empty">Full results via FastF1 1-2 days post-race</div>', unsafe_allow_html=True)

        with col_q:
            st.markdown(f'<div class="sec">Qualifying · {sel_info["name"]}</div>', unsafe_allow_html=True)
            with st.spinner(""):
                ff1q=load_ff1(2026,sel_rnd,"Q")
            if ff1q and ff1q.results is not None and len(ff1q.results)>0:
                st.markdown("""
                <div class="tw">
                  <div style="display:grid;grid-template-columns:28px 1fr 75px 75px 75px;padding:6px 12px;border-bottom:2px solid #e10600;font-size:8px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#2a2a2a;background:#000">
                    <div>P</div><div>DRV</div><div>Q1</div><div>Q2</div><div>Q3</div>
                  </div>
                """, unsafe_allow_html=True)
                for _,row in ff1q.results.iterrows():
                    pos=str(row.get("Position","?"))
                    fn=str(row.get("FirstName",""))[:1]; ln=str(row.get("LastName","?"))
                    team=row.get("TeamName",""); col=tc(team)
                    abbr=row.get("Abbreviation","???")
                    def fq(t):
                        try:
                            if pd.isna(t): return "—"
                            s=t.total_seconds(); m=int(s//60); sec=s%60
                            return f"{m}:{sec:06.3f}"
                        except: return "—"
                    q1=fq(row.get("Q1")); q2=fq(row.get("Q2")); q3=fq(row.get("Q3"))
                    st.markdown(f"""
                    <div style="display:grid;grid-template-columns:28px 1fr 75px 75px 75px;padding:7px 12px;border-bottom:1px solid #0d0d0d;align-items:center;font-size:11px;{'background:rgba(225,6,0,.04)' if pos in ['1','2','3'] else ''}">
                      <div style="font-family:'Space Mono',monospace;font-size:9px;color:#333">{pos}</div>
                      <div><div style="font-size:12px;font-weight:700;color:{col}">{abbr}</div><div style="font-size:9px;color:#333">{team[:12]}</div></div>
                      <div style="font-family:'Space Mono',monospace;font-size:9px;color:#555">{q1}</div>
                      <div style="font-family:'Space Mono',monospace;font-size:9px;color:#555">{q2}</div>
                      <div style="font-family:'Space Mono',monospace;font-size:9px;color:#e10600">{q3}</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty">Qualifying data loads via FastF1 after the weekend</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════
# TAB 5 — LAP ANALYSIS
# ════════════════════════════════════════════════════
with tabs[4]:
    st.markdown('<div class="sec">Lap Analysis — FastF1</div>', unsafe_allow_html=True)
    if not done:
        st.markdown('<div class="empty">No completed races yet</div>', unsafe_allow_html=True)
    else:
        lap_opts={f"R{r['round']}: {r['name']}":r["round"] for r in done}
        ca,cb=st.columns([2,1])
        with ca: sel_lr=st.selectbox("Race",list(lap_opts.keys()),key="lr")
        with cb: sel_st=st.selectbox("Session",["R","Q","FP1","FP2","FP3"],key="lst",format_func=lambda x:{"R":"Race","Q":"Qualifying","FP1":"FP1","FP2":"FP2","FP3":"FP3"}[x])
        sel_lr_rnd=lap_opts[sel_lr]

        with st.spinner("Loading via FastF1…"):
            ff1l=load_ff1(2026,sel_lr_rnd,sel_st)

        if ff1l and ff1l.laps is not None and len(ff1l.laps)>0:
            ldf=ff1l.laps.copy().dropna(subset=["LapTime"])
            ldf["LapTimeSec"]=ldf["LapTime"].dt.total_seconds()
            ldf=ldf[ldf["LapTimeSec"]>0]
            all_drvs=sorted(ldf["Driver"].unique())
            sel_drvs=st.multiselect("Drivers",all_drvs,default=all_drvs[:6] if len(all_drvs)>=6 else all_drvs,key="ld")

            if sel_drvs:
                # Lap times HTML chart (no Plotly dependency)
                st.markdown('<div class="sec">Lap Times</div>', unsafe_allow_html=True)
                try:
                    fig=go.Figure()
                    for d in sel_drvs:
                        dl=ldf[ldf["Driver"]==d].sort_values("LapNumber")
                        try: tn=ff1l.results[ff1l.results["Abbreviation"]==d]["TeamName"].values; col=tc(tn[0] if len(tn)>0 else "")
                        except: col="#888"
                        fig.add_trace(go.Scatter(x=dl["LapNumber"],y=dl["LapTimeSec"],mode="lines+markers",name=d,
                                                  line=dict(color=col,width=2),marker=dict(size=3,color=col),
                                                  hovertemplate=f"<b>{d}</b><br>Lap %{{x}}<br>%{{y:.3f}}s<extra></extra>"))
                    fig.update_layout(paper_bgcolor="#0d0d0d",plot_bgcolor="#0d0d0d",
                                      font=dict(family="Barlow Condensed",color="#f0f0f0"),
                                      xaxis=dict(title="Lap",gridcolor="#111",tickfont=dict(color="#444")),
                                      yaxis=dict(title="Time (s)",gridcolor="#111",tickfont=dict(color="#444")),
                                      legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(size=11)),
                                      margin=dict(l=20,r=20,t=20,b=20),height=340,hovermode="x unified")
                    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
                except:
                    # Fallback: show fastest lap per driver as bars
                    st.markdown('<div class="tw"><div style="padding:12px">', unsafe_allow_html=True)
                    fl_by_d={d:ldf[ldf["Driver"]==d]["LapTimeSec"].min() for d in sel_drvs}
                    min_t=min(fl_by_d.values()) if fl_by_d else 1
                    for d,t in sorted(fl_by_d.items(),key=lambda x:x[1]):
                        try: col=tc(ff1l.results[ff1l.results["Abbreviation"]==d]["TeamName"].values[0])
                        except: col="#888"
                        pct=max(0,100-(t-min_t)/min_t*1000)
                        st.markdown(f'<div style="display:flex;gap:8px;align-items:center;margin:4px 0"><div style="min-width:35px;font-weight:900;color:{col};font-size:11px">{d}</div><div style="flex:1;background:#1a1a1a;height:16px"><div style="width:{pct:.0f}%;background:{col};height:100%"></div></div><div style="min-width:70px;font-family:Space Mono,monospace;font-size:9px;color:#555">{fmt_lap(t)}</div></div>', unsafe_allow_html=True)
                    st.markdown('</div></div>', unsafe_allow_html=True)

                # Tyre strategy
                if "Compound" in ldf.columns:
                    st.markdown('<div class="sec">Tyre Strategy</div>', unsafe_allow_html=True)
                    max_lap=int(ldf["LapNumber"].max())
                    st.markdown('<div class="tw"><div style="padding:14px 16px">', unsafe_allow_html=True)
                    for d in sel_drvs:
                        dl=ldf[ldf["Driver"]==d].sort_values("LapNumber")
                        try: col=tc(ff1l.results[ff1l.results["Abbreviation"]==d]["TeamName"].values[0])
                        except: col="#888"
                        grps=dl.groupby((dl["Compound"]!=dl["Compound"].shift()).cumsum())
                        segs=""
                        for _,stint in grps:
                            comp=(stint["Compound"].iloc[0] or "UNKNOWN").upper()
                            lps=len(stint); pct_s=max(1,round(lps/max_lap*100))
                            tc_c=TYRE_COLORS.get(comp,"#444"); ta=TYRE_ABBR.get(comp,"?")
                            segs+=f'<div style="width:{pct_s}%;background:{tc_c};height:100%;display:flex;align-items:center;justify-content:center;font-size:8px;font-weight:900;color:#000;min-width:12px" title="{comp} {lps}L">{ta}</div>'
                        st.markdown(f'<div style="display:flex;align-items:center;gap:8px;margin:5px 0"><div style="min-width:35px;font-size:10px;font-weight:900;color:{col}">{d}</div><div style="flex:1;display:flex;height:18px;gap:1px;background:#1a1a1a">{segs}</div></div>', unsafe_allow_html=True)
                    st.markdown('</div></div>', unsafe_allow_html=True)

                # Fastest laps table
                st.markdown('<div class="sec">Fastest Laps</div>', unsafe_allow_html=True)
                fl_df=ldf.groupby("Driver")["LapTimeSec"].min().reset_index().sort_values("LapTimeSec").reset_index(drop=True)
                fl_df["Gap"]=fl_df["LapTimeSec"]-fl_df["LapTimeSec"].iloc[0]
                st.markdown('<div class="tw">', unsafe_allow_html=True)
                st.markdown('<div style="display:grid;grid-template-columns:28px 50px 110px 90px;padding:6px 12px;border-bottom:2px solid #e10600;font-size:8px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#2a2a2a;background:#000"><div>P</div><div>DRV</div><div>LAP TIME</div><div>GAP</div></div>', unsafe_allow_html=True)
                for i,row in fl_df.iterrows():
                    d=row["Driver"]
                    try: col=tc(ff1l.results[ff1l.results["Abbreviation"]==d]["TeamName"].values[0])
                    except: col="#888"
                    gap="⬡ FASTEST" if i==0 else f"+{row['Gap']:.3f}s"
                    gc="#c000ff" if i==0 else "#333"
                    bg="background:rgba(192,0,255,.04);" if i==0 else ""
                    st.markdown(f'<div style="display:grid;grid-template-columns:28px 50px 110px 90px;padding:7px 12px;border-bottom:1px solid #0d0d0d;align-items:center;font-size:11px;{bg}"><div style="font-family:Space Mono,monospace;font-size:9px;color:#333">{i+1}</div><div style="font-weight:900;color:{col}">{d}</div><div style="font-family:Space Mono,monospace;font-size:11px">{fmt_lap(row["LapTimeSec"])}</div><div style="font-family:Space Mono,monospace;font-size:10px;color:{gc}">{gap}</div></div>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty">FastF1 lap data available 1-2 days after each race weekend</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════
# TAB 6 — RADIO & CONTROL
# ════════════════════════════════════════════════════
with tabs[5]:
    col_wx, col_rc = st.columns([1,2])

    with col_wx:
        st.markdown('<div class="sec">Track Weather</div>', unsafe_allow_html=True)
        if sk and (is_live or is_recent):
            wx_raw=get_openf1("weather",f"session_key={sk}")
            wx=wx_raw[-1] if wx_raw else None
        else: wx=None

        if wx:
            rain="🌧 Rain" if wx.get("rainfall",0)>0 else "☀️ Dry"
            st.markdown(f"""
            <div class="wgrid">
              <div class="wc"><div class="wv">{wx.get('track_temperature','—')}°</div><div class="wl">Track</div></div>
              <div class="wc"><div class="wv">{wx.get('air_temperature','—')}°</div><div class="wl">Air</div></div>
              <div class="wc"><div class="wv">{wx.get('humidity','—')}%</div><div class="wl">Humidity</div></div>
              <div class="wc"><div class="wv">{wx.get('wind_speed','—')}</div><div class="wl">Wind m/s</div></div>
              <div class="wc"><div class="wv">{wx.get('pressure','—')}</div><div class="wl">mbar</div></div>
              <div class="wc"><div class="wv" style="font-size:.9rem">{rain}</div><div class="wl">Conditions</div></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            if next_race:
                facts=CIRCUIT_FACTS.get(next_race["name"],{})
                st.markdown(f"""
                <div class="tw"><div style="padding:16px">
                  <div style="font-size:9px;letter-spacing:2px;text-transform:uppercase;color:#333;margin-bottom:6px">Next · {next_race['name']}</div>
                  <div style="font-size:12px;color:#2a2a2a;font-family:Space Mono,monospace">Live weather streams during active sessions</div>
                  {f'<div style="font-size:11px;color:#333;margin-top:10px;font-style:italic">💡 {facts.get("fact","")}</div>' if facts else ''}
                  {f'<div style="margin-top:8px;font-family:Space Mono,monospace;font-size:10px;color:#333">🚦 {facts.get("drs","?")} DRS zones</div>' if facts else ''}
                </div></div>
                """, unsafe_allow_html=True)

        # Team radio
        st.markdown('<div class="sec">Team Radio</div>', unsafe_allow_html=True)
        if sk and (is_live or is_recent):
            radio_raw=get_openf1("team_radio",f"session_key={sk}")
        else: radio_raw=[]

        if radio_raw:
            st.markdown('<div class="tw" style="max-height:300px;overflow-y:auto">', unsafe_allow_html=True)
            for msg in reversed(radio_raw[-30:]):
                n=msg.get("driver_number","?")
                drv_info={}
                t=msg.get("date","")
                if t:
                    try: t=datetime.fromisoformat(t.replace("Z","+00:00")).strftime("%H:%M:%S")
                    except: pass
                url=msg.get("recording_url","")
                abbr=f"#{n}"
                col="#888"
                st.markdown(f'<div class="radio-row"><div class="radio-time">{t}</div><div><span style="font-size:10px;font-weight:900;color:{col};margin-right:6px">{abbr}</span><span class="radio-msg">{"🔊 Audio available" if url else "No audio"}</span></div></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty">Team radio streams during active sessions<br>Monaco FP1 starts Friday 5 June</div>', unsafe_allow_html=True)

    with col_rc:
        st.markdown('<div class="sec">Race Control Feed</div>', unsafe_allow_html=True)
        if sk and (is_live or is_recent):
            rc_raw=get_openf1("race_control",f"session_key={sk}")
        else: rc_raw=[]

        if rc_raw:
            st.markdown('<div class="tw" style="max-height:500px;overflow-y:auto">', unsafe_allow_html=True)
            for msg in reversed(rc_raw[-80:]):
                m=msg.get("message",""); mu=m.upper()
                t=msg.get("date","")
                if t:
                    try: t=datetime.fromisoformat(t.replace("Z","+00:00")).strftime("%H:%M:%S")
                    except: pass
                cc,cl="rc-inf","INFO"
                if "SAFETY CAR" in mu and "VIRTUAL" not in mu and "CLEAR" not in mu: cc,cl="rc-sc","SC"
                elif "VIRTUAL" in mu or "VSC" in mu: cc,cl="rc-sc","VSC"
                elif "RED FLAG" in mu: cc,cl="rc-red","RED"
                elif "YELLOW" in mu: cc,cl="rc-red","YEL"
                elif "DRS ENABLED" in mu: cc,cl="rc-drs","DRS"
                elif "FASTEST LAP" in mu: cc,cl="rc-drs","FL"
                elif "PENALTY" in mu or "INVESTIGATION" in mu: cc,cl="rc-pen","PEN"
                elif "RETIRE" in mu: cc,cl="rc-pen","RET"
                st.markdown(f'<div class="rc-row"><div class="rc-t">{t}</div><div><span class="rc-b {cc}">{cl}</span><span class="rc-msg">{m}</span></div></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty">Race control feed activates during sessions<br>Monaco FP1 · Friday 5 June · 11:30 UTC</div>', unsafe_allow_html=True)

# ── AUTO REFRESH ──────────────────────────────────────────────────────────────
if is_live:
    import time
    time.sleep(3)
    st.rerun()
elif is_recent:
    import time
    time.sleep(15)
    st.rerun()

# FOOTER
st.markdown("""
<div style="border-top:1px solid #0d0d0d;padding:12px 16px;font-family:'Space Mono',monospace;font-size:9px;color:#1a1a1a;text-align:center;line-height:1.8">
  FastF1 · OpenF1 API · formula1.com · Auto-refresh 3s live / 15s recent / manual off-weekend
</div>
""", unsafe_allow_html=True)
