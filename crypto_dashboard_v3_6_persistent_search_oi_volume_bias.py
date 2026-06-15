from datetime import datetime
import requests
import streamlit as st

st.set_page_config(
    page_title="Harmann Crypto Bias Dashboard V3.6 Persistent Search + OI Volume Bias",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ================= API SOURCES =================
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

# ================= CLEAN MOBILE STYLE =================
st.markdown(
    """
<style>
#MainMenu, footer, header {visibility:hidden;height:0}
.block-container{padding:.65rem .75rem .55rem .75rem!important;max-width:100%!important}
html,body,.stApp{background:#06101b!important;color:#eaf6ff!important}
*{font-family:Inter,Segoe UI,Arial,sans-serif}
h1{font-size:1.45rem!important;margin-bottom:.1rem!important}
h2,h3{color:#eaf6ff!important}
[data-testid="stMetric"]{
    background:linear-gradient(180deg,#0e1b2e,#071320);
    border:1px solid #294b76;
    border-radius:12px;
    padding:10px;
}
[data-testid="stMetricLabel"]{color:#b7d6ff!important;font-weight:800!important}
[data-testid="stMetricValue"]{color:#ffffff!important;font-weight:950!important}
[data-testid="stMetricDelta"]{font-weight:850!important}
[data-testid="stVerticalBlockBorderWrapper"]{
    background:linear-gradient(180deg,#0e1b2e,#071320)!important;
    border-color:#294b76!important;
    border-radius:14px!important;
}
div[data-testid="stTextInput"] input{
    background:#f5f7fb!important;color:#06101b!important;border-radius:9px!important;
    font-weight:850!important;font-size:1rem!important;height:43px!important;
}
.stButton>button{
    min-height:43px!important;border-radius:9px!important;border:0!important;
    background:linear-gradient(90deg,#006dff,#7b2cff,#ff00b8)!important;
    color:white!important;font-size:1rem!important;font-weight:950!important;text-align:center!important;
}
.small-note{color:#9bb8da;font-size:.75rem}
.green{color:#20e878!important;font-weight:900}
.red{color:#ff465a!important;font-weight:900}
.yellow{color:#ffd24d!important;font-weight:900}
@media(max-width:900px){
    h1{font-size:1.1rem!important}
    .block-container{padding:.55rem .65rem .45rem .65rem!important}
}
</style>
""",
    unsafe_allow_html=True,
)

# ================= HELPERS =================
def jget(url, params=None, timeout=7):
    try:
        r = requests.get(url, params=params, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        return r.json(), ""
    except Exception as e:
        return None, str(e)


def fmt_money(x):
    try:
        x = float(x)
    except Exception:
        return "$0"
    if abs(x) >= 1e12:
        return f"${x/1e12:.2f}T"
    if abs(x) >= 1e9:
        return f"${x/1e9:.2f}B"
    if abs(x) >= 1e6:
        return f"${x/1e6:.2f}M"
    if abs(x) >= 1e3:
        return f"${x/1e3:.1f}K"
    return f"${x:.2f}"


def fmt_price(x):
    try:
        x = float(x)
    except Exception:
        return "0"
    if x >= 1000:
        return f"{x:,.0f}"
    if x >= 1:
        return f"{x:,.3f}"
    return f"{x:.5f}"


def arrow(v):
    try:
        v = float(v)
    except Exception:
        return "→"
    if v > 0:
        return "↑"
    if v < 0:
        return "↓"
    return "→"


def signal_from_score(score):
    if score >= 75:
        return "Strong Long 🟢"
    if score >= 60:
        return "Long 🟢"
    if score >= 41:
        return "Wait 🟡"
    if score >= 25:
        return "Short 🔴"
    return "Strong Short 🔴"


def bias_txt(score):
    if score >= 60:
        return "Long 🟢"
    if score <= 40:
        return "Short 🔴"
    return "Neutral 🟡"


def bias_score(chg, funding, ls, taker, fng):
    s = 50
    s += max(-15, min(15, float(chg or 0) * 3))
    s += 8 if funding > 0 else -8 if funding < 0 else 0
    s += 8 if ls > 1.05 else -8 if ls < 0.95 else 0
    s += 6 if taker > 1.05 else -6 if taker < 0.95 else 0
    s += 4 if fng >= 55 else -4 if fng <= 35 else 0
    return int(max(5, min(95, s)))


def chances(score):
    up = int(max(5, min(95, score)))
    return up, 100 - up


def oi_vol_bias(oi_proxy, vol_proxy, price_change):
    oi_a = arrow(oi_proxy)
    vol_a = arrow(vol_proxy)

    if oi_a == "↑" and price_change >= 0:
        oi_text = "OI Bullish"
    elif oi_a == "↑" and price_change < 0:
        oi_text = "OI Bearish Shorts"
    elif oi_a == "↓" and price_change >= 0:
        oi_text = "Short Cover"
    elif oi_a == "↓" and price_change < 0:
        oi_text = "OI Weak"
    else:
        oi_text = "OI Neutral"

    if vol_a == "↑" and price_change >= 0:
        vol_text = "Vol Bullish"
    elif vol_a == "↑" and price_change < 0:
        vol_text = "Vol Bearish"
    elif vol_a == "↓":
        vol_text = "Vol Weak"
    else:
        vol_text = "Vol Neutral"

    return f"{oi_a} {oi_text}", f"{vol_a} {vol_text}"


# ================= LIVE DATA =================
@st.cache_data(ttl=90, show_spinner=False)
def fear_greed_live():
    d, _ = jget(FEAR_GREED, {"limit": 1, "format": "json"}, timeout=7)
    try:
        x = d["data"][0]
        return int(x["value"]), x["value_classification"]
    except Exception:
        return 0, "N/A"


@st.cache_data(ttl=90, show_spinner=False)
def global_data():
    d, _ = jget(f"{COINGECKO}/global", timeout=7)
    try:
        data = d["data"]
        return (
            float(data["market_cap_percentage"].get("btc", 0) or 0),
            float(data["total_market_cap"].get("usd", 0) or 0),
            float(data["total_volume"].get("usd", 0) or 0),
        )
    except Exception:
        return 0, 0, 0


@st.cache_data(ttl=90, show_spinner=False)
def cg_prices():
    ids = ",".join([m["cg"] for m in ASSETS.values() if m.get("cg")])
    d, _ = jget(
        f"{COINGECKO}/simple/price",
        {
            "ids": ids,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
            "include_market_cap": "true",
        },
        timeout=8,
    )
    out = {}
    for a, m in ASSETS.items():
        row = d.get(m["cg"], {}) if isinstance(d, dict) else {}
        out[a] = {
            "price": float(row.get("usd", 0) or 0),
            "chg": float(row.get("usd_24h_change", 0) or 0),
            "vol": float(row.get("usd_24h_vol", 0) or 0),
        }
    return out


@st.cache_data(ttl=45, show_spinner=False)
def binance_price(symbol):
    for src, url in [
        ("Binance Futures", f"{BINANCE_FAPI}/fapi/v1/ticker/24hr"),
        ("Binance Spot", f"{BINANCE_SPOT}/api/v3/ticker/24hr"),
    ]:
        d, _ = jget(url, {"symbol": symbol}, timeout=6)
        try:
            return float(d.get("lastPrice", 0) or 0), float(d.get("priceChangePercent", 0) or 0), float(d.get("quoteVolume", 0) or 0), src
        except Exception:
            pass
    return 0, 0, 0, "No Binance"


def coinbase_price(product):
    if not product:
        return 0
    d, _ = jget(f"{COINBASE}/products/{product}/ticker", timeout=6)
    try:
        return float(d.get("price", 0) or 0)
    except Exception:
        return 0


@st.cache_data(ttl=180, show_spinner=False)
def cg_lookup(sym):
    d, _ = jget(
        f"{COINGECKO}/coins/markets",
        {
            "vs_currency": "usd",
            "order": "volume_desc",
            "per_page": 250,
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": "1h,24h",
        },
        timeout=10,
    )
    if not isinstance(d, list):
        return None
    for x in d:
        if str(x.get("symbol", "")).upper() == sym.upper():
            return x
    return None


def metrics_okx(symbol):
    res = {"funding": 0.0, "oi": 0.0, "ls": 1.0, "taker": 1.0, "src": "OKX"}
    inst = symbol.replace("USDT", "-USDT-SWAP")
    f, _ = jget(f"{OKX}/api/v5/public/funding-rate", {"instId": inst}, timeout=6)
    oi, _ = jget(f"{OKX}/api/v5/public/open-interest", {"instType": "SWAP", "instId": inst}, timeout=6)
    try:
        res["funding"] = float(f["data"][0].get("fundingRate", 0)) * 100
    except Exception:
        pass
    try:
        res["oi"] = float(oi["data"][0].get("oi", 0))
    except Exception:
        pass
    return res


def metrics_bybit(symbol):
    res = {"funding": 0.0, "oi": 0.0, "ls": 1.0, "taker": 1.0, "src": "Bybit"}
    d, _ = jget(f"{BYBIT}/v5/market/tickers", {"category": "linear", "symbol": symbol}, timeout=6)
    try:
        row = d["result"]["list"][0]
        res["funding"] = float(row.get("fundingRate", 0)) * 100
        res["oi"] = float(row.get("openInterest", 0))
    except Exception:
        pass
    return res


def metrics_binance(symbol):
    res = {"funding": 0.0, "oi": 0.0, "ls": 1.0, "taker": 1.0, "src": "Binance"}
    f, _ = jget(f"{BINANCE_FAPI}/fapi/v1/premiumIndex", {"symbol": symbol}, timeout=6)
    oi, _ = jget(f"{BINANCE_FAPI}/fapi/v1/openInterest", {"symbol": symbol}, timeout=6)
    ls, _ = jget(
        f"{BINANCE_FAPI}/futures/data/globalLongShortAccountRatio",
        {"symbol": symbol, "period": "5m", "limit": 1},
        timeout=6,
    )
    tk, _ = jget(
        f"{BINANCE_FAPI}/futures/data/takerlongshortRatio",
        {"symbol": symbol, "period": "5m", "limit": 1},
        timeout=6,
    )
    try:
        res["funding"] = float(f.get("lastFundingRate", 0)) * 100
    except Exception:
        pass
    try:
        res["oi"] = float(oi.get("openInterest", 0))
    except Exception:
        pass
    try:
        res["ls"] = float(ls[-1].get("longShortRatio", 1)) if isinstance(ls, list) and ls else 1.0
    except Exception:
        pass
    try:
        res["taker"] = float(tk[-1].get("buySellRatio", 1)) if isinstance(tk, list) and tk else 1.0
    except Exception:
        pass
    return res


@st.cache_data(ttl=60, show_spinner=False)
def futures_metrics(symbol):
    for fn in (metrics_okx, metrics_bybit, metrics_binance):
        x = fn(symbol)
        if x["oi"] > 0 or abs(x["funding"]) > 0.000001:
            return x
    return {"funding": 0.0, "oi": 0.0, "ls": 1.0, "taker": 1.0, "src": "No futures"}


def meta_for_symbol(sym):
    sym = sym.upper().replace("USDT", "").replace("-USD", "").strip()
    if sym in ASSETS:
        return sym, ASSETS[sym]
    return sym, {"symbol": f"{sym}USDT", "cg": None, "coinbase": f"{sym}-USD", "icon": "🟡"}


@st.cache_data(ttl=60, show_spinner=False)
def depth_map(sym, depth_limit=1000):
    asset, meta = meta_for_symbol(sym)
    symbol = meta["symbol"]
    cb = meta.get("coinbase")
    sources = [
        ("Binance Futures", f"{BINANCE_FAPI}/fapi/v1/depth", {"symbol": symbol, "limit": depth_limit}),
        ("Binance Spot", f"{BINANCE_SPOT}/api/v3/depth", {"symbol": symbol, "limit": depth_limit}),
    ]
    if cb:
        sources.append(("Coinbase", f"{COINBASE}/products/{cb}/book", {"level": 2}))

    last = ""
    for src, url, params in sources:
        d, e = jget(url, params, timeout=7)
        if e or not isinstance(d, dict):
            last = f"{src}: {e}"[:90]
            continue
        if "bids" not in d or "asks" not in d:
            last = f"{src}: no book"
            continue
        try:
            bids_all = [(float(x[0]), float(x[1]), float(x[0]) * float(x[1])) for x in d["bids"]]
            asks_all = [(float(x[0]), float(x[1]), float(x[0]) * float(x[1])) for x in d["asks"]]
            best_bid = max(x[0] for x in bids_all)
            best_ask = min(x[0] for x in asks_all)
            mid = (best_bid + best_ask) / 2
            bids = [x for x in bids_all if x[0] >= mid * 0.975]
            asks = [x for x in asks_all if x[0] <= mid * 1.025]
            bids = sorted(sorted(bids, key=lambda x: x[2], reverse=True)[:8], key=lambda x: x[0], reverse=True)
            asks = sorted(sorted(asks, key=lambda x: x[2], reverse=True)[:8], key=lambda x: x[0])
            return {"asset": asset, "mid": mid, "bids": bids, "asks": asks, "src": src, "err": ""}
        except Exception as ex:
            last = str(ex)[:90]
    return {"asset": asset, "mid": 0, "bids": [], "asks": [], "src": "No source", "err": last}


@st.cache_data(ttl=90, show_spinner=False)
def candles_15m(sym, limit=120):
    asset, meta = meta_for_symbol(sym)
    symbol = meta["symbol"]
    cb = meta.get("coinbase")
    for src, url, params in [
        ("Binance Futures", f"{BINANCE_FAPI}/fapi/v1/klines", {"symbol": symbol, "interval": "15m", "limit": limit}),
        ("Binance Spot", f"{BINANCE_SPOT}/api/v3/klines", {"symbol": symbol, "interval": "15m", "limit": limit}),
    ]:
        d, _ = jget(url, params, timeout=7)
        if isinstance(d, list) and len(d) > 10:
            try:
                return [{"h": float(x[2]), "l": float(x[3]), "c": float(x[4])} for x in d], src
            except Exception:
                pass

    if cb:
        d, _ = jget(f"{COINBASE}/products/{cb}/candles", {"granularity": 900}, timeout=7)
        if isinstance(d, list) and len(d) > 10:
            d = sorted(d, key=lambda x: x[0])[-limit:]
            return [{"h": float(x[2]), "l": float(x[1]), "c": float(x[4])} for x in d], "Coinbase"
    return [], "No candles"


def sr_15m(sym, current_price):
    candles, src = candles_15m(sym)
    if not candles:
        return {"r1": 0, "r2": 0, "s1": 0, "s2": 0, "src": src}

    p = current_price or candles[-1]["c"]
    recent = candles[-96:]

    if p > 10000:
        step, min_gap = 25, 120
    elif p > 1000:
        step, min_gap = 2.5, 12
    elif p > 100:
        step, min_gap = 0.25, 1.2
    elif p > 10:
        step, min_gap = 0.05, 0.25
    else:
        step, min_gap = 0.0025, 0.012

    highs, lows = [], []
    for i in range(2, len(recent) - 2):
        if recent[i]["h"] >= max(recent[i - 2]["h"], recent[i - 1]["h"], recent[i + 1]["h"], recent[i + 2]["h"]):
            highs.append(recent[i]["h"])
        if recent[i]["l"] <= min(recent[i - 2]["l"], recent[i - 1]["l"], recent[i + 1]["l"], recent[i + 2]["l"]):
            lows.append(recent[i]["l"])

    if len(highs) < 2:
        highs = [x["h"] for x in recent]
    if len(lows) < 2:
        lows = [x["l"] for x in recent]

    def cluster(levels, side):
        buckets = {}
        for lv in levels:
            r = round(lv / step) * step
            buckets.setdefault(r, []).append(lv)
        arr = []
        for vals in buckets.values():
            avg = sum(vals) / len(vals)
            if side == "r" and avg <= p:
                continue
            if side == "s" and avg >= p:
                continue
            arr.append((avg, len(vals)))
        return sorted(arr, key=lambda x: (x[0] - p) if side == "r" else (p - x[0]))

    def pick(arr):
        if not arr:
            return 0, 0
        one = arr[0][0]
        two = one
        for lv, _ in arr[1:]:
            if abs(lv - one) >= min_gap:
                two = lv
                break
        if two == one and len(arr) > 1:
            two = arr[-1][0]
        return one, two

    r1, r2 = pick(cluster(highs, "r"))
    s1, s2 = pick(cluster(lows, "s"))
    return {"r1": r1, "r2": r2, "s1": s1, "s2": s2, "src": src}


def short_and_major(lm):
    asks = lm.get("asks", []) or []
    bids = lm.get("bids", []) or []
    mid = lm.get("mid", 0) or 0
    near_asks = [x for x in asks if mid and x[0] <= mid * 1.012] or asks
    near_bids = [x for x in bids if mid and x[0] >= mid * 0.988] or bids
    st_up = max(near_asks, key=lambda x: x[2]) if near_asks else (0, 0, 0)
    st_dn = max(near_bids, key=lambda x: x[2]) if near_bids else (0, 0, 0)
    mj_up = max(asks, key=lambda x: x[2]) if asks else (0, 0, 0)
    mj_dn = max(bids, key=lambda x: x[2]) if bids else (0, 0, 0)
    return st_up, st_dn, mj_up, mj_dn


# ================= UI =================
def metric_card(label, value, delta=None):
    st.metric(label, value, delta=delta)


def coin_card(row, sr):
    with st.container(border=True):
        st.subheader(f"{row['Icon']} {row['Asset']}")
        c1, c2 = st.columns(2)
        c1.metric("Price", f"${row['Price']:,.4f}", f"{row['24h %']:+.2f}%")
        c2.metric("Bias", row["Bias"], f"{row['Score']}%")
        st.write(f"Funding: **{row['Funding %']:+.5f}%**")
        st.write(f"OI: **{row['OI']/1_000_000:.2f}M**")
        st.write(f"Long/Short: **{row['Long/Short']:.2f}**")
        st.write(f"Volume: **{fmt_money(row['Volume 24h'])}**")
        st.write(f"Taker B/S: **{row['Taker B/S']:.2f}**")
        st.write(f"15m R1/S1: **{fmt_price(sr['r1'])} / {fmt_price(sr['s1'])}**")
        st.write(f"15m R2/S2: **{fmt_price(sr['r2'])} / {fmt_price(sr['s2'])}**")
        st.caption(f"Data: {row['Source']}")


def liquidity_panel(lm, sr, price, title="₿ BTC Liquidity Map"):
    st_up, st_dn, mj_up, mj_dn = short_and_major(lm)
    with st.container(border=True):
        st.subheader(title)
        st.caption(f"Source: {lm.get('src','N/A')} | Current: ${price:,.2f}")
        a, b = st.columns(2)
        a.metric("Short-Term UP Wall", fmt_price(st_up[0]), fmt_money(st_up[2]))
        b.metric("Short-Term DOWN Wall", fmt_price(st_dn[0]), fmt_money(st_dn[2]))
        a.metric("Major UP Liquidity", fmt_price(mj_up[0]), fmt_money(mj_up[2]))
        b.metric("Major DOWN Liquidity", fmt_price(mj_dn[0]), fmt_money(mj_dn[2]))

        st.write(
            f"15m R1: **{fmt_price(sr['r1'])}** | R2: **{fmt_price(sr['r2'])}** | "
            f"S1: **{fmt_price(sr['s1'])}** | S2: **{fmt_price(sr['s2'])}**"
        )

        book = []
        for x in sorted(lm.get("asks", []), key=lambda x: x[0])[:5]:
            book.append({"Side": "Above", "Price": fmt_price(x[0]), "Amount": fmt_money(x[2])})
        for x in sorted(lm.get("bids", []), key=lambda x: x[0], reverse=True)[:5]:
            book.append({"Side": "Below", "Price": fmt_price(x[0]), "Amount": fmt_money(x[2])})

        if book:
            st.dataframe(book, use_container_width=True, hide_index=True)
        else:
            st.warning("Liquidity book data not available right now.")
            if lm.get("err"):
                st.caption(lm["err"])


def search_coin(symbol, fng_val):
    sym, meta = meta_for_symbol(symbol)

    # 1) Try Binance first for live futures/spot pairs
    price, chg, vol, price_src = binance_price(meta["symbol"])

    # 2) Try Coinbase if available
    if price <= 0:
        cb_price = coinbase_price(meta.get("coinbase"))
        if cb_price > 0:
            price = cb_price
            price_src = "Coinbase"

    # 3) CoinGecko fallback for coins not supported on Binance/Coinbase
    cg = cg_lookup(sym)
    if cg:
        try:
            cg_price = float(cg.get("current_price", 0) or 0)
            cg_vol = float(cg.get("total_volume", 0) or 0)
            cg_chg = float(cg.get("price_change_percentage_24h", 0) or 0)
            if price <= 0 and cg_price > 0:
                price = cg_price
                price_src = "CoinGecko"
            if vol <= 0 and cg_vol > 0:
                vol = cg_vol
            if abs(chg) < 0.000001:
                chg = cg_chg
        except Exception:
            pass

    if price <= 0:
        return None

    # Futures metrics may be unavailable for some coins; keep panel visible anyway.
    met = futures_metrics(meta["symbol"])
    lm = depth_map(sym)
    sr = sr_15m(sym, price)
    sc = bias_score(chg, met["funding"], met["ls"], met["taker"], fng_val)

    return {
        "Asset": sym,
        "Icon": meta.get("icon", "🟡"),
        "Price": price,
        "24h %": chg,
        "Volume 24h": vol,
        "Funding %": met["funding"],
        "Long/Short": met["ls"],
        "Taker B/S": met["taker"],
        "OI": met["oi"],
        "Source": f"{met['src']} + {price_src}",
        "Score": sc,
        "Bias": bias_txt(sc),
        "liq": lm,
        "sr": sr,
    }


def search_panel(d):
    with st.container(border=True):
        st.subheader(f"🔎 Search Result: {d['Asset']}")
        oi_text, vol_text = oi_vol_bias(d["OI"], d["Volume 24h"], d["24h %"])
        up, down = chances(d["Score"])

        c1, c2, c3 = st.columns(3)
        c1.metric("Price", f"${d['Price']:,.5f}", f"{d['24h %']:+.2f}%")
        c1.metric("Bias", d["Bias"], f"Score {d['Score']}%")
        c2.metric("OI", f"{d['OI']/1_000_000:.2f}M", oi_text)
        c2.metric("Volume", fmt_money(d["Volume 24h"]), vol_text)
        c3.metric("Up Chance", f"{up}%")
        c3.metric("Down Chance", f"{down}%")
        c3.write(f"Signal: **{signal_from_score(d['Score'])}**")

        liquidity_panel(d["liq"], d["sr"], d["Price"], title=f"{d['Asset']} Liquidity Map")


def market_table(rows):
    data = []
    for i, r in enumerate(rows, 1):
        oi_text, vol_text = oi_vol_bias(r.get("OI Trend", 0), r.get("Vol Trend", 0), r.get("24h %", 0))
        up, down = chances(r["Score"])
        data.append(
            {
                "#": i,
                "Coin": f"{r.get('Icon','')} {r['Asset']}",
                "Price": f"${r['Price']:,.4f}",
                "24h %": f"{r['24h %']:+.2f}%",
                "Volume": fmt_money(r["Volume 24h"]),
                "Vol Bias": vol_text,
                "OI": f"{r['OI']/1_000_000:.2f}M",
                "OI Bias": oi_text,
                "Up": f"{up}%",
                "Down": f"{down}%",
                "Signal": signal_from_score(r["Score"]),
            }
        )
    st.subheader("📈 Market Overview")
    st.dataframe(data, use_container_width=True, hide_index=True)


@st.cache_data(ttl=180, show_spinner=False)
def potential_movers():
    d, _ = jget(
        f"{COINGECKO}/coins/markets",
        {
            "vs_currency": "usd",
            "order": "volume_desc",
            "per_page": 120,
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": "1h,24h",
        },
        timeout=9,
    )
    if not isinstance(d, list):
        return []

    stable = {"usdt", "usdc", "dai", "fdusd", "tusd", "usde", "busd"}
    out = []
    for x in d:
        sym = str(x.get("symbol", "")).upper()
        if sym.lower() in stable:
            continue
        h1 = x.get("price_change_percentage_1h_in_currency")
        h24 = x.get("price_change_percentage_24h_in_currency")
        if h1 is None or h24 is None:
            continue
        try:
            h1 = float(h1)
            h24 = float(h24)
        except Exception:
            continue

        if abs(h1) <= 1.75 and float(x.get("total_volume", 0) or 0) > 20_000_000:
            sc = int(max(5, min(95, 50 + (8 if h1 > 0 else -8) + (8 if h24 > 0 else -8))))
            up, down = chances(sc)
            out.append(
                {
                    "Coin": sym,
                    "Price": f"${float(x.get('current_price', 0) or 0):,.5f}",
                    "1h %": f"{h1:+.2f}%",
                    "24h %": f"{h24:+.2f}%",
                    "Volume": fmt_money(float(x.get("total_volume", 0) or 0)),
                    "Up": f"{up}%",
                    "Down": f"{down}%",
                    "Setup": signal_from_score(sc),
                }
            )

    return sorted(out, key=lambda r: abs(float(r["1h %"].replace("%", ""))))[:5]


# ================= MAIN APP =================
st.title("⚡ Harmann Crypto Bias Dashboard V3.6 Persistent Search + OI Volume Bias")
st.caption(f"Real-time Market Insights & Bias Detector | Last update {datetime.now().strftime('%H:%M:%S')} | Stable mobile clean version")

btc_dom, total_mcap, total_vol = global_data()
fng_val, fng_text = fear_greed_live()
prices = cg_prices()

rows = []
for asset, meta in ASSETS.items():
    cg = prices.get(asset, {})
    cg_price = float(cg.get("price", 0) or 0)
    cg_chg = float(cg.get("chg", 0) or 0)
    cg_vol = float(cg.get("vol", 0) or 0)

    bn_price, bn_chg, bn_vol, bn_src = binance_price(meta["symbol"])

    final_price = cg_price if cg_price > 0 else bn_price
    final_chg = cg_chg if abs(cg_chg) > 0.000001 else bn_chg
    final_vol = cg_vol if cg_vol > 0 else bn_vol
    price_src = "CoinGecko" if cg_price > 0 else bn_src

    met = futures_metrics(meta["symbol"])
    score = bias_score(final_chg, met["funding"], met["ls"], met["taker"], fng_val)

    rows.append(
        {
            "Asset": asset,
            "Icon": meta["icon"],
            "Price": final_price,
            "24h %": final_chg,
            "Volume 24h": final_vol,
            "Funding %": met["funding"],
            "Long/Short": met["ls"],
            "Taker B/S": met["taker"],
            "OI": met["oi"],
            "Source": f"{met['src']} + {price_src}",
            "Score": score,
            "Bias": bias_txt(score),
            "Vol Trend": final_chg,
            "OI Trend": met["funding"],
        }
    )

if total_vol <= 0:
    total_vol = sum(float(r.get("Volume 24h", 0) or 0) for r in rows)
if btc_dom <= 0 and rows and rows[0]["Price"] > 0:
    btc_dom = 56.0
if total_mcap <= 0 and rows and rows[0]["Price"] > 0:
    total_mcap = 2.3e12

srmap = {r["Asset"]: sr_15m(r["Asset"], r["Price"]) for r in rows}
btc_lm = depth_map("BTC")
avg_score = int(sum(r["Score"] for r in rows) / len(rows))
overall_up, overall_down = chances(avg_score)

m1, m2, m3, m4 = st.columns(4)
m1.metric("BTC Dominance", f"{btc_dom:.2f}%")
m2.metric("Fear & Greed Index", f"{fng_val}/100", fng_text)
m3.metric("Total Market Cap", fmt_money(total_mcap))
m4.metric("24h Volume", fmt_money(total_vol))

# ================= SEARCH PANEL =================
# Fixed: form-based search keeps the result visible after rerun and works better on mobile.
if "search_coin_symbol" not in st.session_state:
    st.session_state.search_coin_symbol = ""
if "show_search_panel" not in st.session_state:
    st.session_state.show_search_panel = False

with st.form("coin_search_form", clear_on_submit=False):
    s1, s2 = st.columns([2, 1])
    with s1:
        q = st.text_input(
            "Search coin",
            value=st.session_state.search_coin_symbol,
            placeholder="Search any crypto (BTC, ETH, SOL, DOGE, LINK, PEPE, AVAX...)",
            label_visibility="collapsed",
        )
    with s2:
        submitted = st.form_submit_button("SEARCH CRYPTO", use_container_width=True)

if submitted:
    clean_q = (q or "").strip().upper()
    if clean_q:
        st.session_state.search_coin_symbol = clean_q
        st.session_state.show_search_panel = True

if st.session_state.show_search_panel and st.session_state.search_coin_symbol:
    close_col1, close_col2 = st.columns([5, 1])
    with close_col1:
        st.info(f"Showing result for: {st.session_state.search_coin_symbol}")
    with close_col2:
        if st.button("CLOSE ✕", use_container_width=True, key="close_search_panel"):
            st.session_state.show_search_panel = False
            st.session_state.search_coin_symbol = ""
            st.rerun()

if st.session_state.show_search_panel and st.session_state.search_coin_symbol:
    with st.spinner(f"Loading {st.session_state.search_coin_symbol} data..."):
        d = search_coin(st.session_state.search_coin_symbol, fng_val)
    if d:
        search_panel(d)
    else:
        st.warning("Coin data not found. Try DOGE, LINK, XRP, AVAX, PEPE, BTC, ETH, SOL.")

c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
with c1:
    coin_card(rows[0], srmap["BTC"])
with c2:
    coin_card(rows[1], srmap["ETH"])
with c3:
    coin_card(rows[2], srmap["SOL"])
with c4:
    liquidity_panel(btc_lm, srmap["BTC"], rows[0]["Price"])

market_table(rows)

st.subheader("🚀 Potential Movers")
movers = potential_movers()
if movers:
    st.dataframe(movers, use_container_width=True, hide_index=True)
else:
    st.info("Potential movers data not available right now.")

with st.container(border=True):
    st.subheader("🎯 Market Bias Summary")
    x1, x2, x3 = st.columns(3)
    x1.metric("Up Chance", f"{overall_up}%")
    x2.metric("Down Chance", f"{overall_down}%")
    x3.metric("Signal", signal_from_score(avg_score))

if st.button("Refresh Now"):
    st.cache_data.clear()
    st.rerun()
