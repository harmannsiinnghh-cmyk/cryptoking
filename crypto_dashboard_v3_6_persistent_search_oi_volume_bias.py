
import time
from datetime import datetime
import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Harmann Crypto Bias Dashboard V3.6 Persistent Search + OI Volume Bias",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ================= SOURCES =================
BINANCE_FAPI = "https://fapi.binance.com"
BINANCE_SPOT = "https://api.binance.com"
BYBIT = "https://api.bybit.com"
OKX = "https://www.okx.com"
COINGECKO = "https://api.coingecko.com/api/v3"
FEAR_GREED = "https://api.alternative.me/fng/"
COINBASE = "https://api.exchange.coinbase.com"

ASSETS = {
    "BTC": {"symbol": "BTCUSDT", "cg": "bitcoin", "coinbase": "BTC-USD", "icon": "₿"},
    "ETH": {"symbol": "ETHUSDT", "cg": "ethereum", "coinbase": "ETH-USD", "icon": "◆"},
    "SOL": {"symbol": "SOLUSDT", "cg": "solana", "coinbase": "SOL-USD", "icon": "◉"},
    "BNB": {"symbol": "BNBUSDT", "cg": "binancecoin", "coinbase": None, "icon": "🟡"},
    "XRP": {"symbol": "XRPUSDT", "cg": "ripple", "coinbase": "XRP-USD", "icon": "✕"},
}

# ================= STYLE =================
st.markdown("""
<style>
#MainMenu, footer, header {visibility:hidden;height:0}
.block-container{padding:.5rem .75rem .4rem .75rem!important;max-width:100%!important}
html,body,.stApp{background:#06101b!important;color:#eaf6ff!important}
*{font-family:Inter,Segoe UI,Arial,sans-serif}
h1{font-size:1.55rem!important;margin:0!important}
.note{font-size:.72rem;color:#a7c8f5;margin-top:3px}
.topline{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:.45rem}
.badge{border:1px solid #365b8e;border-radius:10px;padding:8px 12px;background:#0c1728;font-weight:800}
.top{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin-bottom:9px}
.topcard{background:linear-gradient(180deg,#0e1b2e,#071320);border:1px solid #294b76;border-radius:10px;padding:10px 13px;min-height:68px}
.label{color:#b7d6ff;font-size:.84rem;font-weight:800}
.big{font-size:1.8rem;font-weight:950;line-height:1}
.green{color:#20e878!important}.red{color:#ff465a!important}.yellow{color:#ffd24d!important}.muted{color:#9bb8da}
.searchWrap{border:1px solid #31598d;border-radius:12px;background:#0b1728;margin:8px 0 11px 0;padding:10px}
div[data-testid="stTextInput"] input{
    background:#f5f7fb!important;color:#06101b!important;border-radius:9px!important;
    font-weight:850!important;font-size:1rem!important;height:43px!important;
}
.stButton>button{
    height:43px!important;border-radius:9px!important;border:0!important;
    background:linear-gradient(90deg,#006dff,#7b2cff,#ff00b8)!important;
    color:white!important;font-size:1rem!important;font-weight:950!important;
    text-align:center!important;
}
.main{display:grid;grid-template-columns:1.05fr 1.05fr 1.05fr 2.15fr;gap:8px}
.coin,.panel,.liqbox,.searchResult,.summary{
    background:linear-gradient(180deg,#0e1b2e,#071320);border:1px solid #294b76;border-radius:11px;
    padding:11px;box-shadow:0 0 18px rgba(0,0,0,.25)
}
.coin{min-height:280px}
.coinHead{display:flex;justify-content:space-between;align-items:center}
.coinName{font-size:1.35rem;font-weight:950}
.price{font-size:1.45rem;font-weight:950;margin-top:8px}
.score{font-size:2rem;font-weight:950;text-align:right}
.row{display:flex;justify-content:space-between;border-bottom:1px solid rgba(123,160,210,.22);padding:5px 0;font-size:.95rem}
.source{font-size:.72rem;color:#79b8ff;margin-top:9px}
.tableBox{background:linear-gradient(180deg,#0e1b2e,#071320);border:1px solid #294b76;border-radius:11px;margin-top:9px;padding:9px}
.title{font-size:1.05rem;font-weight:950;margin-bottom:8px}
table{width:100%;border-collapse:collapse;font-size:.88rem}
th,td{border:1px solid rgba(92,130,176,.32);padding:8px;text-align:center}
th{color:#b7d6ff;background:#0a1a2c}
td{text-align:center}
.left{text-align:left}
.arrow{font-size:1.45rem;font-weight:950}
.liqGrid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.liqCard{border-radius:10px;border:1px solid #2d5b86;background:#071322;padding:10px;text-align:center}
.liqGreen{background:linear-gradient(180deg,rgba(0,255,100,.14),rgba(0,80,50,.08));border-color:#138a52}
.liqRed{background:linear-gradient(180deg,rgba(255,30,60,.14),rgba(80,0,30,.08));border-color:#9b2635}
.liqLabel{font-weight:950;font-size:.86rem}
.liqPrice{font-size:1.35rem;font-weight:950;margin:7px 0}
.levelRows{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:9px}
.levelMini{border:1px solid rgba(92,130,176,.32);border-radius:8px;padding:8px;background:#071322}
.searchResult{margin:8px 0 10px 0;border-color:#3b6eaa}
.searchGrid{display:grid;grid-template-columns:1fr 1fr 1fr 1.3fr;gap:9px}
.footer{font-size:.75rem;color:#a7c8f5;margin:7px 0}
@media(max-width:900px){
    .top{grid-template-columns:1fr 1fr}.main{grid-template-columns:1fr}.searchGrid{grid-template-columns:1fr}
    table{font-size:.82rem}.coin{min-height:auto}
}
</style>
""", unsafe_allow_html=True)

# ================= HELPERS =================
def render_html(html, height=800):
    inner_css = """
    <style>
    html,body{margin:0!important;background:#06101b!important;color:#eaf6ff!important;font-family:Inter,Segoe UI,Arial,sans-serif!important;}
    *{box-sizing:border-box;font-family:Inter,Segoe UI,Arial,sans-serif!important}
    .green{color:#20e878!important}.red{color:#ff465a!important}.yellow{color:#ffd24d!important}.muted{color:#9bb8da!important}
    .main{display:grid;grid-template-columns:1.05fr 1.05fr 1.05fr 2.15fr;gap:8px;background:#06101b!important;color:#eaf6ff!important}
    .coin,.panel,.liqbox,.searchResult,.summary,.tableBox{
        background:linear-gradient(180deg,#0e1b2e,#071320)!important;
        border:1px solid #294b76!important;border-radius:11px!important;
        padding:11px!important;box-shadow:0 0 18px rgba(0,0,0,.25)!important;color:#eaf6ff!important;
    }
    .coin{min-height:280px!important}
    .coinHead{display:flex!important;justify-content:space-between!important;align-items:center!important}
    .coinName{font-size:1.35rem!important;font-weight:950!important;color:#fff!important}
    .label{color:#b7d6ff!important;font-size:.84rem!important;font-weight:800!important}
    .price{font-size:1.45rem!important;font-weight:950!important;margin-top:8px!important;color:#fff!important}
    .score{font-size:2rem!important;font-weight:950!important;text-align:right!important;color:#fff!important}
    .row{display:flex!important;justify-content:space-between!important;border-bottom:1px solid rgba(123,160,210,.22)!important;padding:5px 0!important;font-size:.95rem!important;color:#eaf6ff!important}
    .source{font-size:.72rem!important;color:#79b8ff!important;margin-top:9px!important}
    .title{font-size:1.05rem!important;font-weight:950!important;margin-bottom:8px!important;color:#fff!important}
    table{width:100%!important;border-collapse:collapse!important;font-size:.88rem!important;color:#eaf6ff!important}
    th,td{border:1px solid rgba(92,130,176,.32)!important;padding:8px!important;text-align:center!important;color:#eaf6ff!important}
    th{color:#b7d6ff!important;background:#0a1a2c!important;font-weight:900!important}
    .left{text-align:left!important}
    .arrow{font-size:1.45rem!important;font-weight:950!important}
    .liqGrid{display:grid!important;grid-template-columns:1fr 1fr!important;gap:10px!important}
    .liqCard{border-radius:10px!important;border:1px solid #2d5b86!important;background:#071322!important;padding:10px!important;text-align:center!important;color:#eaf6ff!important}
    .liqGreen{background:linear-gradient(180deg,rgba(0,255,100,.14),rgba(0,80,50,.08))!important;border-color:#138a52!important}
    .liqRed{background:linear-gradient(180deg,rgba(255,30,60,.14),rgba(80,0,30,.08))!important;border-color:#9b2635!important}
    .liqLabel{font-weight:950!important;font-size:.86rem!important}
    .liqPrice{font-size:1.35rem!important;font-weight:950!important;margin:7px 0!important;color:#fff!important}
    .levelRows{display:grid!important;grid-template-columns:1fr 1fr!important;gap:8px!important;margin-top:9px!important}
    .levelMini{border:1px solid rgba(92,130,176,.32)!important;border-radius:8px!important;padding:8px!important;background:#071322!important;color:#eaf6ff!important}
    .searchResult{margin:8px 0 10px 0!important;border-color:#3b6eaa!important}
    .searchGrid{display:grid!important;grid-template-columns:1fr 1fr 1fr 1.3fr!important;gap:9px!important}
    .footer{font-size:.75rem!important;color:#a7c8f5!important;margin:7px 0!important}
    .biasBadge{display:inline-block!important;border-radius:7px!important;padding:2px 7px!important;font-size:.78rem!important;font-weight:950!important;margin-left:6px!important}
    .bullBadge{background:rgba(32,232,120,.12)!important;color:#20e878!important;border:1px solid rgba(32,232,120,.35)!important}
    .bearBadge{background:rgba(255,70,90,.12)!important;color:#ff465a!important;border:1px solid rgba(255,70,90,.35)!important}
    .neutralBadge{background:rgba(255,210,77,.12)!important;color:#ffd24d!important;border:1px solid rgba(255,210,77,.35)!important}
    @media(max-width:900px){.main{grid-template-columns:1fr!important}.searchGrid{grid-template-columns:1fr!important}.liqGrid{grid-template-columns:1fr!important}table{font-size:.82rem!important}.coin{min-height:auto!important}}
    </style>
    """
    components.html(inner_css + html, height=height, scrolling=False)

def jget(url, params=None, timeout=8):
    try:
        r = requests.get(url, params=params, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        return r.json(), ""
    except Exception as e:
        return None, str(e)

def fmt_money(x):
    try: x=float(x)
    except: return "$0"
    if abs(x)>=1e12: return f"${x/1e12:.2f}T"
    if abs(x)>=1e9: return f"${x/1e9:.2f}B"
    if abs(x)>=1e6: return f"${x/1e6:.2f}M"
    if abs(x)>=1e3: return f"${x/1e3:.1f}K"
    return f"${x:.2f}"

def fmt_price(x):
    try: x=float(x)
    except: return "0"
    if x >= 1000: return f"{x:,.0f}"
    if x >= 1: return f"{x:,.3f}"
    return f"{x:.5f}"

def pct_cls(x):
    try: return "green" if float(x)>=0 else "red"
    except: return "yellow"

def trend_arrow(v):
    try: v=float(v)
    except: return "→","yellow"
    if v > 0: return "↑","green"
    if v < 0: return "↓","red"
    return "→","yellow"

def oi_volume_bias(oi_value, volume_value, price_change=0):
    """
    Simple readable bias based on OI + Volume direction/proxy.
    Green when participation supports move, red when pressure weak/bearish.
    """
    oi_ar, oi_c = trend_arrow(oi_value)
    vol_ar, vol_c = trend_arrow(volume_value)

    # OI bias text
    if oi_c == "green" and price_change >= 0:
        oi_bias = "OI Bullish"
        oi_badge = "bullBadge"
    elif oi_c == "green" and price_change < 0:
        oi_bias = "OI Bearish Shorts"
        oi_badge = "bearBadge"
    elif oi_c == "red" and price_change >= 0:
        oi_bias = "Short Cover"
        oi_badge = "neutralBadge"
    elif oi_c == "red" and price_change < 0:
        oi_bias = "OI Weak"
        oi_badge = "neutralBadge"
    else:
        oi_bias = "OI Neutral"
        oi_badge = "neutralBadge"

    # Volume bias text
    if vol_c == "green" and price_change >= 0:
        vol_bias = "Vol Bullish"
        vol_badge = "bullBadge"
    elif vol_c == "green" and price_change < 0:
        vol_bias = "Vol Bearish"
        vol_badge = "bearBadge"
    elif vol_c == "red":
        vol_bias = "Vol Weak"
        vol_badge = "neutralBadge"
    else:
        vol_bias = "Vol Neutral"
        vol_badge = "neutralBadge"

    return oi_ar, oi_c, oi_bias, oi_badge, vol_ar, vol_c, vol_bias, vol_badge

def signal_from_score(score):
    if score >= 75: return "Strong Long 🟢"
    if score >= 60: return "Long 🟢"
    if score >= 41: return "Wait 🟡"
    if score >= 25: return "Short 🔴"
    return "Strong Short 🔴"

def bias_txt(score):
    if score >= 60: return "Long 🟢"
    if score <= 40: return "Short 🔴"
    return "Neutral 🟡"

def bias_score(chg, funding, ls, taker, fng):
    s = 50
    s += max(-15, min(15, chg * 3))
    s += 8 if funding > 0 else -8 if funding < 0 else 0
    s += 8 if ls > 1.05 else -8 if ls < .95 else 0
    s += 6 if taker > 1.05 else -6 if taker < .95 else 0
    s += 4 if fng >= 55 else -4 if fng <= 35 else 0
    return int(max(5, min(95, s)))

def chances(score):
    up = int(max(5, min(95, score)))
    return up, 100-up

# ================= DATA =================
@st.cache_data(ttl=60, show_spinner=False)
def fear_greed_live():
    d, err = jget(FEAR_GREED, {"limit": 1, "format": "json"}, timeout=8)
    try:
        x = d["data"][0]
        return int(x["value"]), x["value_classification"]
    except Exception:
        return 0, "N/A"

@st.cache_data(ttl=60, show_spinner=False)
def global_data():
    d, err = jget(f"{COINGECKO}/global", timeout=8)
    try:
        data = d["data"]
        return (float(data["market_cap_percentage"].get("btc",0) or 0),
                float(data["total_market_cap"].get("usd",0) or 0),
                float(data["total_volume"].get("usd",0) or 0))
    except Exception:
        return 0,0,0

@st.cache_data(ttl=60, show_spinner=False)
def coingecko_prices():
    ids = ",".join([m["cg"] for m in ASSETS.values() if m.get("cg")])
    d, err = jget(f"{COINGECKO}/simple/price", {
        "ids": ids, "vs_currencies": "usd", "include_24hr_change": "true",
        "include_24hr_vol": "true", "include_market_cap": "true"
    }, timeout=10)
    out={}
    for a,m in ASSETS.items():
        row = d.get(m["cg"], {}) if isinstance(d,dict) else {}
        out[a] = {
            "price": float(row.get("usd",0) or 0),
            "chg": float(row.get("usd_24h_change",0) or 0),
            "vol": float(row.get("usd_24h_vol",0) or 0),
            "mcap": float(row.get("usd_market_cap",0) or 0)
        }
    return out

def coinbase_price(product):
    if not product: return 0
    d, e = jget(f"{COINBASE}/products/{product}/ticker", timeout=6)
    try: return float(d.get("price",0) or 0)
    except: return 0

def binance_price(symbol):
    for base,url in [("Binance Futures", f"{BINANCE_FAPI}/fapi/v1/ticker/24hr"), ("Binance Spot", f"{BINANCE_SPOT}/api/v3/ticker/24hr")]:
        d,e = jget(url, {"symbol": symbol}, timeout=6)
        try:
            return float(d.get("lastPrice",0) or 0), float(d.get("priceChangePercent",0) or 0), float(d.get("quoteVolume",0) or 0), base
        except: pass
    return 0,0,0,"No Binance"

@st.cache_data(ttl=180, show_spinner=False)
def cg_symbol_lookup(sym):
    d,e = jget(f"{COINGECKO}/coins/markets", {
        "vs_currency":"usd","order":"volume_desc","per_page":250,"page":1,
        "sparkline":"false","price_change_percentage":"1h,24h"
    }, timeout=12)
    if not isinstance(d,list): return None
    for x in d:
        if str(x.get("symbol","")).upper() == sym.upper():
            return x
    return None

def metrics_okx(symbol):
    res={"funding":0.0,"oi":0.0,"ls":1.0,"taker":1.0,"src":"OKX"}
    inst=symbol.replace("USDT","-USDT-SWAP")
    f,e1=jget(f"{OKX}/api/v5/public/funding-rate",{"instId":inst},timeout=6)
    oi,e2=jget(f"{OKX}/api/v5/public/open-interest",{"instType":"SWAP","instId":inst},timeout=6)
    try: res["funding"]=float(f["data"][0].get("fundingRate",0))*100
    except: pass
    try: res["oi"]=float(oi["data"][0].get("oi",0))
    except: pass
    return res

def metrics_bybit(symbol):
    res={"funding":0.0,"oi":0.0,"ls":1.0,"taker":1.0,"src":"Bybit"}
    d,e=jget(f"{BYBIT}/v5/market/tickers",{"category":"linear","symbol":symbol},timeout=6)
    try:
        row=d["result"]["list"][0]
        res["funding"]=float(row.get("fundingRate",0))*100
        res["oi"]=float(row.get("openInterest",0))
    except: pass
    return res

def metrics_binance(symbol):
    res={"funding":0.0,"oi":0.0,"ls":1.0,"taker":1.0,"src":"Binance"}
    f,e1=jget(f"{BINANCE_FAPI}/fapi/v1/premiumIndex",{"symbol":symbol},timeout=6)
    oi,e2=jget(f"{BINANCE_FAPI}/fapi/v1/openInterest",{"symbol":symbol},timeout=6)
    ls,e3=jget(f"{BINANCE_FAPI}/futures/data/globalLongShortAccountRatio",{"symbol":symbol,"period":"5m","limit":1},timeout=6)
    tk,e4=jget(f"{BINANCE_FAPI}/futures/data/takerlongshortRatio",{"symbol":symbol,"period":"5m","limit":1},timeout=6)
    try: res["funding"]=float(f.get("lastFundingRate",0))*100
    except: pass
    try: res["oi"]=float(oi.get("openInterest",0))
    except: pass
    try: res["ls"]=float(ls[-1].get("longShortRatio",1)) if isinstance(ls,list) and ls else 1.0
    except: pass
    try: res["taker"]=float(tk[-1].get("buySellRatio",1)) if isinstance(tk,list) and tk else 1.0
    except: pass
    return res

@st.cache_data(ttl=60, show_spinner=False)
def futures_metrics(symbol):
    for fn in (metrics_okx, metrics_bybit, metrics_binance):
        x=fn(symbol)
        if x["oi"]>0 or abs(x["funding"])>0.000001:
            return x
    return {"funding":0.0,"oi":0.0,"ls":1.0,"taker":1.0,"src":"No futures"}

def meta_for_symbol(sym):
    sym=sym.upper().replace("USDT","").replace("-USD","").strip()
    if sym in ASSETS:
        return sym, ASSETS[sym]
    return sym, {"symbol": f"{sym}USDT", "cg": None, "coinbase": f"{sym}-USD", "icon":"🟡"}

@st.cache_data(ttl=60, show_spinner=False)
def depth_map(sym, depth_limit=1000):
    asset, meta = meta_for_symbol(sym)
    symbol = meta["symbol"]
    cb = meta.get("coinbase")
    sources = [
        ("Binance Futures", f"{BINANCE_FAPI}/fapi/v1/depth", {"symbol":symbol,"limit":depth_limit}),
        ("Binance Spot", f"{BINANCE_SPOT}/api/v3/depth", {"symbol":symbol,"limit":depth_limit}),
    ]
    if cb:
        sources.append(("Coinbase", f"{COINBASE}/products/{cb}/book", {"level":2}))
    last=""
    for src,url,params in sources:
        d,e = jget(url,params,timeout=8)
        if e or not isinstance(d,dict):
            last = f"{src}: {e}"[:70]; continue
        if "bids" not in d or "asks" not in d:
            last = f"{src}: no book"; continue
        try:
            bids_all=[(float(x[0]),float(x[1]),float(x[0])*float(x[1])) for x in d["bids"]]
            asks_all=[(float(x[0]),float(x[1]),float(x[0])*float(x[1])) for x in d["asks"]]
            best_bid=max(x[0] for x in bids_all); best_ask=min(x[0] for x in asks_all)
            mid=(best_bid+best_ask)/2
            near_pct=.025
            bids=[x for x in bids_all if x[0] >= mid*(1-near_pct)]
            asks=[x for x in asks_all if x[0] <= mid*(1+near_pct)]
            bids=sorted(sorted(bids,key=lambda x:x[2],reverse=True)[:8], key=lambda x:x[0], reverse=True)
            asks=sorted(sorted(asks,key=lambda x:x[2],reverse=True)[:8], key=lambda x:x[0])
            return {"asset":asset,"mid":mid,"bids":bids,"asks":asks,"src":src,"err":""}
        except Exception as ex:
            last = str(ex)[:70]
    return {"asset":asset,"mid":0,"bids":[],"asks":[],"src":"No source","err":last}

@st.cache_data(ttl=90, show_spinner=False)
def candles_15m(sym, limit=120):
    asset, meta = meta_for_symbol(sym)
    symbol=meta["symbol"]; cb=meta.get("coinbase")
    for src,url,params in [
        ("Binance Futures", f"{BINANCE_FAPI}/fapi/v1/klines", {"symbol":symbol,"interval":"15m","limit":limit}),
        ("Binance Spot", f"{BINANCE_SPOT}/api/v3/klines", {"symbol":symbol,"interval":"15m","limit":limit}),
    ]:
        d,e=jget(url,params,timeout=8)
        if isinstance(d,list) and len(d)>10:
            try:
                return [{"h":float(x[2]),"l":float(x[3]),"c":float(x[4])} for x in d], src
            except: pass
    if cb:
        d,e=jget(f"{COINBASE}/products/{cb}/candles", {"granularity":900}, timeout=8)
        if isinstance(d,list) and len(d)>10:
            d=sorted(d,key=lambda x:x[0])[-limit:]
            return [{"h":float(x[2]),"l":float(x[1]),"c":float(x[4])} for x in d], "Coinbase"
    return [], "No candles"

def sr_15m(sym, current_price):
    candles, src = candles_15m(sym)
    if not candles:
        return {"r1":0,"r2":0,"s1":0,"s2":0,"src":src}
    p = current_price or candles[-1]["c"]
    recent = candles[-96:]
    if p > 10000: step,min_gap=25,120
    elif p > 1000: step,min_gap=2.5,12
    elif p > 100: step,min_gap=.25,1.2
    elif p > 10: step,min_gap=.05,.25
    else: step,min_gap=.0025,.012
    highs=[]; lows=[]
    for i in range(2,len(recent)-2):
        if recent[i]["h"] >= max(recent[i-2]["h"],recent[i-1]["h"],recent[i+1]["h"],recent[i+2]["h"]): highs.append(recent[i]["h"])
        if recent[i]["l"] <= min(recent[i-2]["l"],recent[i-1]["l"],recent[i+1]["l"],recent[i+2]["l"]): lows.append(recent[i]["l"])
    if len(highs)<2: highs=[x["h"] for x in recent]
    if len(lows)<2: lows=[x["l"] for x in recent]
    def cluster(levels, side):
        buckets={}
        for lv in levels:
            r=round(lv/step)*step
            buckets.setdefault(r,[]).append(lv)
        arr=[]
        for vals in buckets.values():
            avg=sum(vals)/len(vals)
            if side=="r" and avg<=p: continue
            if side=="s" and avg>=p: continue
            arr.append((avg,len(vals)))
        arr=sorted(arr,key=lambda x: (x[0]-p) if side=="r" else (p-x[0]))
        return arr
    def pick(arr, side):
        if not arr: return (0,0)
        one=arr[0][0]; two=one
        for lv,t in arr[1:]:
            if abs(lv-one) >= min_gap:
                two=lv; break
        if two==one and len(arr)>1:
            two=arr[-1][0]
        return one,two
    r1,r2=pick(cluster(highs,"r"),"r")
    s1,s2=pick(cluster(lows,"s"),"s")
    return {"r1":r1,"r2":r2,"s1":s1,"s2":s2,"src":src}

def short_and_major(lm):
    asks=lm.get("asks",[]) or []
    bids=lm.get("bids",[]) or []
    mid=lm.get("mid",0) or 0
    near_asks=[x for x in asks if mid and x[0] <= mid*1.012] or asks
    near_bids=[x for x in bids if mid and x[0] >= mid*.988] or bids
    st_up=max(near_asks,key=lambda x:x[2]) if near_asks else (0,0,0)
    st_dn=max(near_bids,key=lambda x:x[2]) if near_bids else (0,0,0)
    mj_up=max(asks,key=lambda x:x[2]) if asks else (0,0,0)
    mj_dn=max(bids,key=lambda x:x[2]) if bids else (0,0,0)
    return st_up, st_dn, mj_up, mj_dn

# ================= RENDER HELPERS =================
def liq_panel_btc(lm, sr, price):
    st_up, st_dn, mj_up, mj_dn = short_and_major(lm)
    above = "".join([f"<div>{fmt_price(x[0])} <span class='muted'>{fmt_money(x[2])}</span></div>" for x in sorted(lm.get("asks",[]), key=lambda x:x[0])[:5]])
    below = "".join([f"<div>{fmt_price(x[0])} <span class='muted'>{fmt_money(x[2])}</span></div>" for x in sorted(lm.get("bids",[]), key=lambda x:x[0], reverse=True)[:5]])
    return f"""
    <div class='liqbox'>
      <div class='title'>₿ BTC LIQUIDITY MAP <span class='muted'>(Nearest + Major)</span></div>
      <div class='liqGrid'>
        <div>
          <div class='title' style='font-size:.9rem'>SHORT-TERM LIQUIDITY</div>
          <div class='liqCard liqGreen'><div class='liqLabel green'>UP WALL (Nearest Strongest)</div><div class='liqPrice'>{fmt_price(st_up[0])} ↑</div><div>{fmt_money(st_up[2])}</div></div>
          <div class='liqCard liqRed' style='margin-top:8px'><div class='liqLabel red'>DOWN WALL (Nearest Strongest)</div><div class='liqPrice'>{fmt_price(st_dn[0])} ↓</div><div>{fmt_money(st_dn[2])}</div></div>
        </div>
        <div>
          <div class='title' style='font-size:.9rem'>MAJOR LIQUIDITY</div>
          <div class='liqCard liqGreen'><div class='liqLabel green'>MAJOR UP LIQUIDITY</div><div class='liqPrice'>{fmt_price(mj_up[0])} ↑</div><div>{fmt_money(mj_up[2])}</div></div>
          <div class='liqCard liqRed' style='margin-top:8px'><div class='liqLabel red'>MAJOR DOWN LIQUIDITY</div><div class='liqPrice'>{fmt_price(mj_dn[0])} ↓</div><div>{fmt_money(mj_dn[2])}</div></div>
        </div>
      </div>
      <div class='levelRows'>
        <div class='levelMini'><b class='green'>Above Price</b><br>{above}</div>
        <div class='levelMini'><b class='red'>Below Price</b><br>{below}</div>
      </div>
      <div class='levelMini' style='margin-top:9px;text-align:center'>
        <b>BTC Current Price</b><br><span class='price'>${price:,.2f}</span><br>
        15m R1: <span class='green'>{fmt_price(sr['r1'])}</span> &nbsp; R2: <span class='green'>{fmt_price(sr['r2'])}</span> &nbsp;
        S1: <span class='red'>{fmt_price(sr['s1'])}</span> &nbsp; S2: <span class='red'>{fmt_price(sr['s2'])}</span>
      </div>
    </div>
    """

def coin_card(r, sr):
    cls = "green" if r["Score"]>=60 else "red" if r["Score"]<=40 else "yellow"
    return f"""
    <div class='coin'>
      <div class='coinHead'><div class='coinName'>{r['Icon']} {r['Asset']}</div><div class='label'>Bias</div></div>
      <div style='display:flex;justify-content:space-between;align-items:end'>
        <div><div class='price'>${r['Price']:,.4f}</div><div class='{pct_cls(r['24h %'])}'>{r['24h %']:+.2f}% (24h)</div></div>
        <div><div class='score'>{r['Score']}%</div><div class='{cls}' style='font-weight:950'>{r['Bias']}</div></div>
      </div>
      <div style='margin-top:12px'>
        <div class='row'><span>Funding</span><span class='{pct_cls(r['Funding %'])}'>{r['Funding %']:+.5f}%</span></div>
        <div class='row'><span>OI</span><span>{r['OI']/1_000_000:.2f}M</span></div>
        <div class='row'><span>Long/Short</span><span>{r['Long/Short']:.2f}</span></div>
        <div class='row'><span>Volume</span><span>{fmt_money(r['Volume 24h'])}</span></div>
        <div class='row'><span>Taker B/S</span><span>{r['Taker B/S']:.2f}</span></div>
        <div class='row'><span>15m R1/S1</span><span>{fmt_price(sr['r1'])}/{fmt_price(sr['s1'])}</span></div>
        <div class='row'><span>15m R2/S2</span><span>{fmt_price(sr['r2'])}/{fmt_price(sr['s2'])}</span></div>
      </div>
      <div class='source'>Data: {r['Source']}</div>
    </div>
    """

def table_rows(rows, movers=False):
    out=""
    for i,r in enumerate(rows,1):
        oi_ar, oi_c, oi_bias, oi_badge, vo_ar, vo_c, vol_bias, vol_badge = oi_volume_bias(r.get("OI Trend",0), r.get("Vol Trend",0), r.get("24h %",0))
        sig = signal_from_score(r["Score"])
        up,down = chances(r["Score"])
        out += f"""
        <tr>
          <td>{i}</td><td class='left'><b>{r.get('Icon','')} {r['Asset']}</b></td>
          <td>${r['Price']:,.4f}<br><span class='{pct_cls(r['24h %'])}'>{r['24h %']:+.2f}%</span></td>
          <td>{fmt_money(r['Volume 24h'])}</td>
          <td><span class='arrow {vo_c}'>{vo_ar}</span><br><span class='biasBadge {vol_badge}'>{vol_bias}</span></td>
          <td>{r['OI']/1_000_000:.2f}M</td>
          <td><span class='arrow {oi_c}'>{oi_ar}</span><br><span class='biasBadge {oi_badge}'>{oi_bias}</span></td>
          <td class='green'>{up}%</td><td class='red'>{down}%</td>
          <td class='{"green" if r["Score"]>=60 else "red" if r["Score"]<=40 else "yellow"}'><b>{sig}</b></td>
        </tr>"""
    return out

def search_coin(symbol, fng_val):
    sym, meta = meta_for_symbol(symbol)
    price, chg, vol, ps = binance_price(meta["symbol"])
    if price <= 0:
        price = coinbase_price(meta.get("coinbase"))
        ps = "Coinbase" if price else ps
    cg = cg_symbol_lookup(sym)
    if price <= 0 and cg:
        price = float(cg.get("current_price",0) or 0)
        chg = float(cg.get("price_change_percentage_24h",0) or 0)
        vol = float(cg.get("total_volume",0) or 0)
        ps = "CoinGecko"
    if price <= 0:
        return None
    met = futures_metrics(meta["symbol"])
    lm = depth_map(sym)
    sr = sr_15m(sym, price)
    sc = bias_score(chg, met["funding"], met["ls"], met["taker"], fng_val)
    return {"Asset":sym,"Icon":meta.get("icon","🟡"),"Price":price,"24h %":chg,"Volume 24h":vol,
            "Funding %":met["funding"],"Long/Short":met["ls"],"Taker B/S":met["taker"],
            "OI":met["oi"],"Source":met["src"] if met["src"]!="No futures" else ps,
            "Score":sc,"Bias":bias_txt(sc),"liq":lm,"sr":sr}

def search_result_html(d):
    st_up, st_dn, mj_up, mj_dn = short_and_major(d["liq"])
    oi_ar, oi_c, oi_bias, oi_badge, vo_ar, vo_c, vol_bias, vol_badge = oi_volume_bias(d["OI"], d["Volume 24h"], d["24h %"])
    up, down = chances(d["Score"])
    return f"""
    <div class='searchResult'>
      <div class='title'>🔎 Search Result: {d['Asset']} Full Bias Panel</div>
      <div class='searchGrid'>
        <div class='levelMini'><div class='label'>Price / Bias</div><div class='price'>${d['Price']:,.5f}</div><div class='{pct_cls(d['24h %'])}'>{d['24h %']:+.2f}% 24h</div><div style='font-size:1.2rem;font-weight:950'>{d['Bias']}</div></div>
        <div class='levelMini'><div class='label'>OI / Volume Bias</div><div class='row'><span>OI</span><span>{d['OI']/1_000_000:.2f}M <b class='{oi_c}'>{oi_ar}</b> <span class='biasBadge {oi_badge}'>{oi_bias}</span></span></div><div class='row'><span>Volume</span><span>{fmt_money(d['Volume 24h'])} <b class='{vo_c}'>{vo_ar}</b> <span class='biasBadge {vol_badge}'>{vol_bias}</span></span></div><div class='row'><span>Funding</span><span class='{pct_cls(d['Funding %'])}'>{d['Funding %']:+.5f}%</span></div></div>
        <div class='levelMini'><div class='label'>Valid 15m S/R</div><div class='row'><span>R1</span><span class='green'>{fmt_price(d['sr']['r1'])}</span></div><div class='row'><span>R2</span><span class='green'>{fmt_price(d['sr']['r2'])}</span></div><div class='row'><span>S1</span><span class='red'>{fmt_price(d['sr']['s1'])}</span></div><div class='row'><span>S2</span><span class='red'>{fmt_price(d['sr']['s2'])}</span></div></div>
        <div class='levelMini'><div class='label'>Liquidity + Signal</div><div class='row'><span>Short Up</span><span>{fmt_price(st_up[0])} {fmt_money(st_up[2])}</span></div><div class='row'><span>Short Down</span><span>{fmt_price(st_dn[0])} {fmt_money(st_dn[2])}</span></div><div class='row'><span>Major Up</span><span>{fmt_price(mj_up[0])} {fmt_money(mj_up[2])}</span></div><div class='row'><span>Major Down</span><span>{fmt_price(mj_dn[0])} {fmt_money(mj_dn[2])}</span></div><div class='row'><span>Up/Down</span><span class='green'>{up}%</span>/<span class='red'>{down}%</span></div><div style='font-size:1.15rem;font-weight:950'>{signal_from_score(d['Score'])}</div></div>
      </div>
    </div>
    """

# ================= MAIN =================
btc_dom, total_mcap, total_vol = global_data()
fng_val, fng_text = fear_greed_live()
prices = coingecko_prices()

rows=[]
for a,m in ASSETS.items():
    p=prices.get(a,{})
    met=futures_metrics(m["symbol"])
    sc=bias_score(p.get("chg",0),met["funding"],met["ls"],met["taker"],fng_val)
    rows.append({
        "Asset":a,"Icon":m["icon"],"Price":p.get("price",0),"24h %":p.get("chg",0),
        "Volume 24h":p.get("vol",0),"Funding %":met["funding"],"Long/Short":met["ls"],
        "Taker B/S":met["taker"],"OI":met["oi"],"Source":met["src"],"Score":sc,
        "Bias":bias_txt(sc),
        "Vol Trend":p.get("chg",0),       # practical arrow: green when 24h move/volume flow is positive
        "OI Trend":met["funding"]         # practical arrow proxy when historical OI change unavailable
    })

srmap={r["Asset"]:sr_15m(r["Asset"],r["Price"]) for r in rows}
btc_lm=depth_map("BTC")
avg=int(sum(r["Score"] for r in rows)/len(rows))
overall_up, overall_down = chances(avg)

st.markdown(f"""
<div class='topline'>
 <div><h1>⚡ Harmann Crypto Bias Dashboard V3.6 Persistent Search + OI Volume Bias</h1><div class='note'>Real-time Market Insights & Bias Detector | Last update {datetime.now().strftime('%H:%M:%S')}</div></div>
 <div class='badge'>⟳ Refresh: 30s</div>
</div>
<div class='top'>
 <div class='topcard'><div class='label'>BTC Dominance</div><div class='big'>{btc_dom:.2f}%</div></div>
 <div class='topcard'><div class='label'>Fear & Greed Index</div><div class='big'>{fng_val}/100 <span class='{ "green" if fng_val>=55 else "red" if fng_val<=35 else "yellow"}' style='font-size:.9rem'>{fng_text}</span></div></div>
 <div class='topcard'><div class='label'>Total Market Cap</div><div class='big'>{fmt_money(total_mcap)}</div></div>
 <div class='topcard'><div class='label'>24h Volume</div><div class='big'>{fmt_money(total_vol)}</div></div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div class='searchWrap'>", unsafe_allow_html=True)
c1,c2,c3 = st.columns([1.3,1.3,1.4])
with c1:
    q = st.text_input("Search coin", placeholder="Search any crypto (BTC, ETH, SOL, DOGE, LINK...)", label_visibility="collapsed")
with c2:
    clicked = st.button("SEARCH CRYPTO", use_container_width=True)
with c3:
    st.empty()
st.markdown("</div>", unsafe_allow_html=True)

# Persistent search panel: stays open until Close button is clicked
if "search_coin_symbol" not in st.session_state:
    st.session_state.search_coin_symbol = ""
if "show_search_panel" not in st.session_state:
    st.session_state.show_search_panel = False

if clicked and q.strip():
    st.session_state.search_coin_symbol = q.strip()
    st.session_state.show_search_panel = True

if st.session_state.show_search_panel and st.session_state.search_coin_symbol:
    close_col1, close_col2 = st.columns([6, 1])
    with close_col2:
        if st.button("CLOSE ✕", use_container_width=True):
            st.session_state.show_search_panel = False
            st.session_state.search_coin_symbol = ""

if st.session_state.show_search_panel and st.session_state.search_coin_symbol:
    d = search_coin(st.session_state.search_coin_symbol, fng_val)
    if d:
        render_html(search_result_html(d), height=350)
    else:
        st.warning("Coin data not found. Try DOGE, LINK, XRP, AVAX, PEPE, BTC, ETH, SOL.")

render_html(f"""
<div class='main'>
 {coin_card(rows[0], srmap['BTC'])}
 {coin_card(rows[1], srmap['ETH'])}
 {coin_card(rows[2], srmap['SOL'])}
 {liq_panel_btc(btc_lm, srmap['BTC'], rows[0]['Price'])}
</div>
""", height=385)

render_html(f"""
<div class='tableBox'>
 <div class='title'>📈 MARKET OVERVIEW</div>
 <table>
  <tr><th>#</th><th>Coin</th><th>Price</th><th>Volume (24h)</th><th>Volume Trend</th><th>OI (Total)</th><th>OI Trend</th><th>Up Chance</th><th>Down Chance</th><th>Signal</th></tr>
  {table_rows(rows)}
 </table>
 <div class='footer'><span class='green'>↑ Increase</span> &nbsp;&nbsp; <span class='red'>↓ Decrease</span> &nbsp;&nbsp; Data: CoinGecko + Binance/Bybit/OKX + Coinbase</div>
</div>
""", height=385)

# Potential movers from CoinGecko
@st.cache_data(ttl=180, show_spinner=False)
def potential_movers():
    d,e=jget(f"{COINGECKO}/coins/markets",{
        "vs_currency":"usd","order":"volume_desc","per_page":120,"page":1,
        "sparkline":"false","price_change_percentage":"1h,24h"
    },timeout=10)
    if not isinstance(d,list): return []
    stable={"usdt","usdc","dai","fdusd","tusd","usde","busd"}
    out=[]
    for x in d:
        sym=str(x.get("symbol","")).upper()
        if sym.lower() in stable: continue
        h1=x.get("price_change_percentage_1h_in_currency")
        h24=x.get("price_change_percentage_24h_in_currency")
        if h1 is None or h24 is None: continue
        try: h1=float(h1); h24=float(h24)
        except: continue
        if abs(h1)<=1.75 and float(x.get("total_volume",0) or 0)>20_000_000:
            sc=50 + (8 if h1>0 else -8) + (8 if h24>0 else -8)
            out.append({"Asset":sym,"Icon":"🚀","Price":float(x.get("current_price",0) or 0),"24h %":h24,
                        "1h %":h1,"Volume 24h":float(x.get("total_volume",0) or 0),"OI":0,"Score":int(max(5,min(95,sc))),
                        "Vol Trend":h1,"OI Trend":h24})
    return sorted(out,key=lambda r:(abs(r["1h %"]),-r["Volume 24h"]))[:5]

movers=potential_movers()
mov_rows=""
for i,r in enumerate(movers,1):
    oa,oc,oi_bias,oi_badge,va,vc,vol_bias,vol_badge = oi_volume_bias(r["OI Trend"], r["Vol Trend"], r["24h %"])
    up,down=chances(r["Score"])
    mov_rows += f"<tr><td>{i}</td><td class='left'><b>{r['Asset']}</b></td><td>${r['Price']:,.5f}</td><td class='{pct_cls(r['1h %'])}'>{r['1h %']:+.2f}%</td><td class='{pct_cls(r['24h %'])}'>{r['24h %']:+.2f}%</td><td><span class='arrow {oc}'>{oa}</span><br><span class='biasBadge {oi_badge}'>{oi_bias}</span></td><td><span class='arrow {vc}'>{va}</span><br><span class='biasBadge {vol_badge}'>{vol_bias}</span></td><td class='green'>{up}%</td><td class='red'>{down}%</td><td><b>{signal_from_score(r['Score'])}</b></td></tr>"

render_html(f"""
<div class='tableBox'>
 <div class='title'>🚀 POTENTIAL MOVERS <span class='muted'>(Next Move Scanner)</span></div>
 <table>
  <tr><th>#</th><th>Coin</th><th>Price</th><th>1h %</th><th>24h %</th><th>OI Trend</th><th>Volume Trend</th><th>Up Chance</th><th>Down Chance</th><th>Setup</th></tr>
  {mov_rows}
 </table>
</div>
<div class='summary' style='margin-top:9px;text-align:center'>
 <div class='title'>🎯 MARKET BIAS SUMMARY</div>
 <span class='green' style='font-size:1.6rem;font-weight:950'>Up Chance {overall_up}%</span>
 &nbsp;&nbsp;&nbsp;
 <span class='red' style='font-size:1.6rem;font-weight:950'>Down Chance {overall_down}%</span>
 <div style='font-size:1.8rem;font-weight:950;margin-top:8px'>{signal_from_score(avg)}</div>
</div>
""", height=455)

time.sleep(30)
st.rerun()
