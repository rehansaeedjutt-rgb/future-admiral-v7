"""
Future Admiral v7 - Institutional Trading Desk
Complete: Light/Dark theme, Discord toggle, Auto-save, Google Sheet sync
"""
import streamlit as st
import time, traceback, os, csv, subprocess
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="Future Admiral", layout="wide",
                   initial_sidebar_state="expanded")

# ============ STATE ============
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

TRADES_FILE = Path("paper_trades.csv")


# ============ PAPER TRADE HELPERS ============
def load_trades():
    if not TRADES_FILE.exists():
        return []
    try:
        with open(TRADES_FILE, "r", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def save_signal(symbol, timeframe, futures, spot):
    ap = (spot or {}).get("action_plan") or {}
    tp = (futures or {}).get("take_profit") or []
    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "symbol": symbol,
        "timeframe": timeframe,
        "fut_bias": (futures or {}).get("bias", "neutral"),
        "fut_type": (futures or {}).get("trade_type", "none"),
        "fut_entry": (futures or {}).get("entry") or "",
        "fut_sl": (futures or {}).get("stop_loss") or "",
        "fut_tp1": tp[0] if len(tp) > 0 else "",
        "fut_tp2": tp[1] if len(tp) > 1 else "",
        "fut_rr": (futures or {}).get("risk_reward") or "",
        "fut_conf": f"{(futures or {}).get('confidence', 0)*100:.0f}%",
        "fut_duration_h": (futures or {}).get("duration_hours") or "",
        "spot_action": ap.get("action", ""),
        "spot_recommendation": (spot or {}).get("recommendation", ""),
        "spot_buy_trigger": ap.get("buy_trigger_price") or "",
        "spot_avoid_above": ap.get("avoid_above_price") or "",
        "spot_fund_score": (spot or {}).get("fundamental_score", ""),
        "spot_institutional": (spot or {}).get("institutional_signal", ""),
        "outcome": "PENDING",
        "pnl_pct": "",
        "notes": "",
    }
    write_header = not TRADES_FILE.exists()
    with open(TRADES_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        if write_header:
            w.writeheader()
        w.writerow(row)
    return row


def sync_to_gsheets():
    """Run sync_to_sheets.py using the same Python interpreter."""
    import sys
    try:
        script = str(Path.cwd() / "sync_to_sheets.py")
        r = subprocess.run(
            [sys.executable, script],
            capture_output=True, text=True, timeout=90,
            cwd=str(Path.cwd()),
        )
        out = (r.stdout or "").strip()
        err = (r.stderr or "").strip()

        if "Synced" in out and "Done" in out:
            # Extract "Synced X/Y" line
            lines = [l for l in out.splitlines() if "Done" in l]
            detail = lines[-1] if lines else "Synced"
            return True, f"Synced to Google Sheets ({detail})"
        if "up to date" in out:
            return True, "Google Sheets already up to date"
        if "not set" in out:
            return False, "GSHEET_WEBHOOK_URL missing in .env"

        # Fallback — show real error
        msg = out[-200:] if out else (err[-200:] if err else "empty output")
        return False, f"Sync: {msg}"
    except Exception as e:
        return False, f"Sync exception: {type(e).__name__}: {e}"


# ============ THEME ============
theme = st.session_state.theme
if theme == "dark":
    V = {
        "bg":"#0b1020","bg2":"#131a2e","bg3":"#1a2340",
        "border":"#232d4a","border2":"#3a4770",
        "text":"#f1f5fb","text2":"#c4cde0","muted":"#7d8aa8","muted2":"#5a6786",
        "accent":"#7ab8ff","green":"#4ade80","red":"#f87171","amber":"#fbbf24",
        "btn":"#4f8cff","btn_border":"#6ba3ff","hover":"#1a2340",
    }
else:
    V = {
        "bg":"#fafbfc","bg2":"#ffffff","bg3":"#f4f6f9",
        "border":"#e4e8ee","border2":"#cdd5e0",
        "text":"#0f172a","text2":"#3a4a5f","muted":"#6b7a92","muted2":"#98a4b8",
        "accent":"#2563eb","green":"#059669","red":"#dc2626","amber":"#d97706",
        "btn":"#2563eb","btn_border":"#3b82f6","hover":"#f4f6f9",
    }

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
* {{ font-family: 'Inter', sans-serif; }}
.stApp {{ background: {V['bg']}; }}
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1600px; }}

.fa-topbar {{ display:flex; align-items:center; gap:20px; padding:0 0 24px 0;
    border-bottom:1px solid {V['border']}; margin-bottom:28px; }}
.fa-brand {{ display:flex; align-items:center; gap:14px; }}
.fa-mark {{ width:44px; height:44px;
    background:linear-gradient(135deg,{V['bg2']},{V['bg3']});
    border:1px solid {V['border']}; border-radius:10px;
    display:flex; align-items:center; justify-content:center;
    font-family:'JetBrains Mono',monospace; font-weight:800; font-size:20px;
    color:{V['accent']}; letter-spacing:-1px; }}
.fa-name {{ font-size:17px; font-weight:700; color:{V['text']}; line-height:1.2; }}
.fa-tag {{ font-size:10px; color:{V['muted']}; letter-spacing:1.5px;
    text-transform:uppercase; font-weight:600; margin-top:2px; }}
.fa-right {{ margin-left:auto; display:flex; align-items:center; gap:20px; }}
.fa-stat {{ display:flex; flex-direction:column; align-items:flex-end; }}
.fa-stat-label {{ font-size:9px; color:{V['muted']}; letter-spacing:1px;
    text-transform:uppercase; font-weight:600; }}
.fa-stat-value {{ font-size:13px; color:{V['text']}; font-weight:700;
    font-family:'JetBrains Mono',monospace; margin-top:2px; }}
.fa-live {{ display:inline-flex; align-items:center; gap:7px; padding:6px 12px;
    background:rgba(63,185,80,0.12); border:1px solid rgba(63,185,80,0.4);
    border-radius:6px; color:{V['green']}; font-size:10px; font-weight:800;
    letter-spacing:1.2px; }}
.fa-live-dot {{ width:6px; height:6px; background:{V['green']};
    border-radius:50%; animation:blink 2s infinite; }}
@keyframes blink {{ 0%,100%{{opacity:1}} 50%{{opacity:0.3}} }}

.sec-header {{ display:flex; align-items:center; gap:12px; margin:32px 0 16px 0; }}
.sec-num {{ font-family:'JetBrains Mono',monospace; font-size:11px;
    color:{V['accent']}; font-weight:700; padding:3px 8px;
    background:rgba(88,166,255,0.1); border:1px solid rgba(88,166,255,0.25);
    border-radius:4px; letter-spacing:0.5px; }}
.sec-title {{ font-size:12px; color:{V['text']}; font-weight:700;
    letter-spacing:1.8px; text-transform:uppercase; }}
.sec-line {{ flex:1; height:1px; background:{V['border']}; }}

.verdict {{ padding:26px 30px; border-radius:12px; border-left:4px solid;
    background:{V['bg2']}; margin-bottom:20px; box-shadow:0 1px 3px rgba(0,0,0,0.06); }}
.verdict-long {{ border-left-color:{V['green']}; background:linear-gradient(90deg,rgba(63,185,80,0.08) 0%,{V['bg2']} 40%); }}
.verdict-short {{ border-left-color:{V['red']}; background:linear-gradient(90deg,rgba(248,81,73,0.08) 0%,{V['bg2']} 40%); }}
.verdict-neutral {{ border-left-color:{V['muted']}; background:linear-gradient(90deg,rgba(139,148,158,0.08) 0%,{V['bg2']} 40%); }}
.verdict-buy {{ border-left-color:{V['green']}; background:linear-gradient(90deg,rgba(63,185,80,0.10) 0%,{V['bg2']} 40%); }}
.verdict-wait {{ border-left-color:{V['amber']}; background:linear-gradient(90deg,rgba(210,153,34,0.10) 0%,{V['bg2']} 40%); }}
.verdict-avoid {{ border-left-color:{V['red']}; background:linear-gradient(90deg,rgba(248,81,73,0.10) 0%,{V['bg2']} 40%); }}
.verdict-top {{ display:flex; align-items:center; gap:16px; margin-bottom:12px; }}
.verdict-tag {{ font-size:10px; color:{V['muted']}; letter-spacing:1.5px;
    text-transform:uppercase; font-weight:700; }}
.verdict-action {{ font-size:22px; font-weight:800; color:{V['text']};
    letter-spacing:-0.5px; }}
.verdict-headline {{ font-size:15px; color:{V['text']}; font-weight:600;
    line-height:1.4; margin-bottom:6px; }}
.verdict-desc {{ font-size:13px; color:{V['text2']}; line-height:1.55; }}

.mgrid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:1px;
    background:{V['border']}; border:1px solid {V['border']};
    border-radius:10px; overflow:hidden; margin:16px 0; }}
.mcell {{ background:{V['bg2']}; padding:16px 18px; transition:background 0.15s; }}
.mcell:hover {{ background:{V['hover']}; }}
.mcell-label {{ font-size:9px; color:{V['muted']}; letter-spacing:1.3px;
    text-transform:uppercase; font-weight:700; margin-bottom:8px; }}
.mcell-value {{ font-family:'JetBrains Mono',monospace; font-size:18px;
    color:{V['text']}; font-weight:600; letter-spacing:-0.3px; }}
.mcell-value.green {{ color:{V['green']}; }}
.mcell-value.red {{ color:{V['red']}; }}
.mcell-value.blue {{ color:{V['accent']}; }}
.mcell-value.amber {{ color:{V['amber']}; }}
.mcell-sub {{ font-size:10px; color:{V['muted']}; margin-top:4px; font-weight:500; }}

.info-panel {{ background:{V['bg2']}; border:1px solid {V['border']};
    border-radius:10px; padding:20px 22px; margin:12px 0;
    box-shadow:0 1px 2px rgba(0,0,0,0.04); }}
.info-title {{ font-size:10px; color:{V['muted']}; letter-spacing:1.3px;
    text-transform:uppercase; font-weight:700; margin-bottom:12px; }}
.info-item {{ font-size:13px; color:{V['text2']}; padding:7px 0 7px 18px;
    position:relative; line-height:1.55;
    border-bottom:1px solid {V['border']}; }}
.info-item:last-child {{ border-bottom:none; }}
.info-item::before {{ content:""; position:absolute; left:4px; top:14px;
    width:4px; height:4px; background:{V['accent']}; border-radius:50%; }}

.arow {{ display:flex; align-items:center; justify-content:space-between;
    padding:16px 20px; background:{V['bg2']}; border:1px solid {V['border']};
    border-radius:8px; margin:8px 0; border-left:3px solid {V['border']};
    box-shadow:0 1px 2px rgba(0,0,0,0.04); }}
.arow.bull {{ border-left-color:{V['green']}; }}
.arow.bear {{ border-left-color:{V['red']}; }}
.arow.neutral {{ border-left-color:{V['muted']}; }}
.arole {{ font-size:13px; color:{V['text']}; font-weight:600; }}
.aconf {{ font-size:11px; color:{V['muted']}; margin-top:3px;
    font-family:'JetBrains Mono',monospace; }}
.apill {{ padding:5px 12px; border-radius:5px; font-size:10px; font-weight:800;
    letter-spacing:1px; font-family:'JetBrains Mono',monospace; }}
.apill.bull {{ background:rgba(63,185,80,0.12); color:{V['green']};
    border:1px solid rgba(63,185,80,0.3); }}
.apill.bear {{ background:rgba(248,81,73,0.12); color:{V['red']};
    border:1px solid rgba(248,81,73,0.3); }}
.apill.neutral {{ background:rgba(139,148,158,0.12); color:{V['muted']};
    border:1px solid rgba(139,148,158,0.3); }}

.debate-card {{ background:{V['bg2']}; border:1px solid {V['border']};
    border-radius:10px; padding:20px 22px; box-shadow:0 1px 2px rgba(0,0,0,0.04); }}
.debate-card.bull {{ border-top:3px solid {V['green']}; }}
.debate-card.bear {{ border-top:3px solid {V['red']}; }}
.debate-label {{ font-size:10px; letter-spacing:1.5px; font-weight:800;
    text-transform:uppercase; margin-bottom:10px; }}
.debate-card.bull .debate-label {{ color:{V['green']}; }}
.debate-card.bear .debate-label {{ color:{V['red']}; }}
.debate-text {{ font-size:13px; color:{V['text2']}; line-height:1.55; }}
.debate-conf {{ margin-top:12px; padding-top:12px;
    border-top:1px solid {V['border']}; font-size:11px;
    color:{V['muted']}; font-family:'JetBrains Mono',monospace; }}

section[data-testid="stSidebar"] {{ background:{V['bg2']};
    border-right:1px solid {V['border']}; }}
section[data-testid="stSidebar"] label {{
    color:{V['muted']} !important; font-weight:700 !important;
    letter-spacing:0.5px !important; font-size:11px !important;
    text-transform:uppercase !important; }}

.sb-title {{ font-size:10px; color:{V['muted']}; letter-spacing:1.5px;
    text-transform:uppercase; font-weight:700; margin:24px 0 12px 0;
    padding-bottom:8px; border-bottom:1px solid {V['border']}; }}
.sb-status {{ display:flex; align-items:center; gap:8px;
    padding:10px 12px; background:{V['bg']}; border:1px solid {V['border']};
    border-radius:6px; margin:6px 0; font-size:12px; color:{V['text2']}; }}
.sb-dot {{ width:6px; height:6px; border-radius:50%; }}
.sb-dot.on {{ background:{V['green']}; box-shadow:0 0 8px rgba(63,185,80,0.6); }}
.sb-dot.off {{ background:{V['red']}; }}

/* Streamlit widget overrides */
.stButton > button, .stButton > button[kind="primary"],
button[kind="primary"], button[kind="secondary"] {{
    color: #ffffff !important; font-weight: 700 !important; }}
.stButton > button p, .stButton > button span, .stButton > button div {{
    color: #ffffff !important; }}
.stTextInput input, .stTextInput > div > div > input {{
    background: {V['bg2']} !important; color: {V['text']} !important;
    border: 1px solid {V['border2']} !important; border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600 !important; font-size: 13px !important;
    padding: 10px 14px !important; }}
.stSelectbox div[data-baseweb="select"] > div {{
    background: {V['bg2']} !important; color: {V['text']} !important;
    border: 1px solid {V['border2']} !important; border-radius: 8px !important; }}
.stSelectbox div[data-baseweb="select"] * {{
    color: {V['text']} !important; font-weight: 600 !important; }}
[data-baseweb="popover"] {{ background: {V['bg2']} !important;
    border: 1px solid {V['border']} !important; }}
[data-baseweb="menu"] li {{ background: {V['bg2']} !important;
    color: {V['text']} !important; }}
[data-baseweb="menu"] li:hover {{ background: {V['hover']} !important; }}
.stRadio > div {{ display:flex; flex-direction:row; gap:6px;
    background:{V['bg']}; padding:4px; border:1px solid {V['border']};
    border-radius:10px; }}
.stRadio > div > label {{ padding:8px 16px !important;
    border-radius:7px !important; background:transparent !important;
    color:{V['muted']} !important; font-weight:700 !important;
    font-size:12px !important; letter-spacing:0.5px !important;
    cursor:pointer !important; margin:0 !important; }}
.stRadio > div > label:hover {{ background:{V['hover']} !important;
    color:{V['text']} !important; }}
.stRadio > div > label[data-checked="true"] {{
    background:{V['accent']} !important; color:#ffffff !important; }}
.stRadio > div > label > div:first-child {{ display:none !important; }}
.stCheckbox label span, .stCheckbox label p {{
    color:{V['text2']} !important; font-weight:500 !important; }}

.stTabs [data-baseweb="tab-list"] {{ gap:4px; background:transparent;
    border-bottom:1px solid {V['border']}; padding-bottom:0; }}
.stTabs [data-baseweb="tab"] {{ background:transparent; border:none;
    border-radius:0; padding:12px 20px; color:{V['muted']};
    font-weight:700; font-size:12px; letter-spacing:1.2px;
    text-transform:uppercase; border-bottom:2px solid transparent;
    margin-bottom:-1px; }}
.stTabs [data-baseweb="tab"]:hover {{ color:{V['text2']}; }}
.stTabs [aria-selected="true"] {{ background:transparent !important;
    color:{V['accent']} !important; border-bottom:2px solid {V['accent']} !important; }}

.stButton > button[kind="primary"] {{ background:{V['btn']};
    border:1px solid {V['btn_border']}; border-radius:8px; font-weight:700;
    padding:14px 24px; color:white; letter-spacing:0.5px; font-size:13px; }}
.stButton > button[kind="primary"]:hover {{ background:{V['btn_border']}; }}

.stDownloadButton > button {{ background:{V['bg2']} !important;
    color:{V['text']} !important; border:1px solid {V['border2']} !important;
    border-radius:8px !important; font-weight:600 !important; }}

.fa-footer {{ margin-top:60px; padding-top:24px;
    border-top:1px solid {V['border']}; text-align:center;
    color:{V['muted2']}; font-size:11px; letter-spacing:0.5px;
    font-family:'JetBrains Mono',monospace; }}

.stMarkdown, .stText, p, span, label {{ color:{V['text2']}; }}
h1, h2, h3, h4, h5, h6 {{ color:{V['text']}; }}
</style>
""", unsafe_allow_html=True)


# ============ TOPBAR ============
st.markdown(f"""
<div class="fa-topbar">
    <div class="fa-brand">
        <div class="fa-mark">FA</div>
        <div>
            <div class="fa-name">Future Admiral</div>
            <div class="fa-tag">Institutional Trading Desk</div>
        </div>
    </div>
    <div class="fa-right">
        <div class="fa-stat">
            <div class="fa-stat-label">Session</div>
            <div class="fa-stat-value">{datetime.now().strftime('%H:%M')} UTC+5</div>
        </div>
        <div class="fa-live"><span class="fa-live-dot"></span>LIVE</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ============ SIDEBAR ============
with st.sidebar:
    st.markdown('<div class="sb-title">Appearance</div>', unsafe_allow_html=True)
    tc = st.radio("Theme", ["Dark", "Light"],
                  index=0 if st.session_state.theme == "dark" else 1,
                  horizontal=True, label_visibility="collapsed")
    if tc.lower() != st.session_state.theme:
        st.session_state.theme = tc.lower()
        st.rerun()

    st.markdown('<div class="sb-title">Configuration</div>', unsafe_allow_html=True)
    symbol = st.text_input("ASSET SYMBOL", value="XRP/USDT")
    timeframe = st.selectbox("TIMEFRAME", ["1m","5m","15m","1h","4h","1d"], index=2)
    send_discord_flag = st.checkbox("Send Discord Alert", value=False)
    auto_save_flag = st.checkbox("Auto-save to Paper Log", value=True)
    auto_gsheet_flag = st.checkbox("Auto-sync to Google Sheets", value=True)

    st.markdown("")
    run = st.button("EXECUTE ANALYSIS", width="stretch", type="primary")

    st.markdown('<div class="sb-title">System Status</div>', unsafe_allow_html=True)

    from dotenv import load_dotenv
    load_dotenv()
    groq_ok = bool(os.getenv("GROQ_API_KEY"))
    gsheet_ok = bool(os.getenv("GSHEET_WEBHOOK_URL"))
    try:
        import requests
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        ollama_ok = r.status_code == 200
    except Exception:
        ollama_ok = False

    trades_count = len(load_trades())

    st.markdown(f"""
    <div class="sb-status"><span class="sb-dot {'on' if groq_ok else 'off'}"></span>Groq Cloud (Primary)</div>
    <div class="sb-status"><span class="sb-dot {'on' if ollama_ok else 'off'}"></span>Ollama Local (Fallback)</div>
    <div class="sb-status"><span class="sb-dot {'on' if gsheet_ok else 'off'}"></span>Google Sheets</div>
    <div class="sb-status"><span class="sb-dot on"></span>Paper Log: {trades_count} signals</div>
    """, unsafe_allow_html=True)


# ============ MAIN ============
if run and symbol:
    result = None
    with st.status(f"Analyzing {symbol} across 12 data sources...", expanded=True) as status:
        try:
            from future_admiral_v7.debate.engine import run_debate
            t = time.time()
            result = run_debate(symbol, timeframe, ui=status)
            elapsed = time.time() - t
            status.update(label=f"Analysis complete in {elapsed:.0f}s",
                          state="complete", expanded=False)
        except Exception as e:
            status.update(label="Analysis failed", state="error", expanded=True)
            st.error(f"**{type(e).__name__}**: {e}")
            st.code(traceback.format_exc())

    if result:
        futures = result.get("futures", {}) or {}
        spot = result.get("spot", {}) or {}
        ap = spot.get("action_plan") or {}

        # Auto-save
        if auto_save_flag:
            try:
                save_signal(symbol, timeframe, futures, spot)
                st.success("Signal saved to paper_trades.csv")
            except Exception as e:
                st.warning(f"Save failed: {e}")

        # Google Sheets sync
        if auto_gsheet_flag:
            ok, msg = sync_to_gsheets()
            if ok:
                st.success(msg)
            else:
                st.info(msg)

        # Discord
        if send_discord_flag:
            try:
                from future_admiral_v7.alerts.discord import send_discord_embed
                if send_discord_embed(futures):
                    st.success("Discord alert dispatched")
                else:
                    st.warning("Discord not configured")
            except Exception as e:
                st.warning(f"Discord error: {e}")

        # Tabs
        tab_fut, tab_spot, tab_log, tab_scan, tab_data = st.tabs(
            ["FUTURES", "SPOT", "PAPER LOG", "SCAN ALL COINS", "RAW DATA"])

        # -------- FUTURES --------
        with tab_fut:
            bias = (futures.get("bias") or "neutral").upper()
            conf = futures.get("confidence", 0) or 0
            tt = (futures.get("trade_type") or "none").upper()
            dur = futures.get("duration_hours", 0) or 0
            cp = futures.get("current_price")
            entry = futures.get("entry")
            sl = futures.get("stop_loss")
            tp = futures.get("take_profit") or []
            rr = futures.get("risk_reward", 0)
            size = futures.get("position_size_pct", 0)
            lev = futures.get("leverage", 1)
            inval = futures.get("invalidation") or "—"
            reasons = futures.get("reasons") or []
            risks = futures.get("risks") or []

            vclass = {"LONG":"verdict-long","SHORT":"verdict-short"}.get(bias, "verdict-neutral")
            tp1 = tp[0] if len(tp) > 0 else "—"
            tp2 = tp[1] if len(tp) > 1 else "—"

            st.markdown(f"""
            <div class="verdict {vclass}">
                <div class="verdict-top">
                    <span class="verdict-tag">Futures Direction</span>
                    <span class="verdict-action">{bias}</span>
                </div>
                <div class="verdict-headline">Trade Type: {tt} &nbsp;·&nbsp; Duration: {dur}h &nbsp;·&nbsp; Confidence: {conf*100:.0f}%</div>
                <div class="verdict-desc">Invalidation: {inval}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="sec-header"><span class="sec-num">01</span><span class="sec-title">Execution Parameters</span><span class="sec-line"></span></div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="mgrid">
                <div class="mcell"><div class="mcell-label">Current Price</div><div class="mcell-value blue">{cp or '—'}</div></div>
                <div class="mcell"><div class="mcell-label">Entry</div><div class="mcell-value">{entry or '—'}</div></div>
                <div class="mcell"><div class="mcell-label">Stop Loss</div><div class="mcell-value red">{sl or '—'}</div></div>
                <div class="mcell"><div class="mcell-label">Risk / Reward</div><div class="mcell-value amber">{rr}</div></div>
                <div class="mcell"><div class="mcell-label">Take Profit 1</div><div class="mcell-value green">{tp1}</div></div>
                <div class="mcell"><div class="mcell-label">Take Profit 2</div><div class="mcell-value green">{tp2}</div></div>
                <div class="mcell"><div class="mcell-label">Position Size</div><div class="mcell-value">{size}%</div></div>
                <div class="mcell"><div class="mcell-label">Leverage</div><div class="mcell-value">{lev}x</div></div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="sec-header"><span class="sec-num">02</span><span class="sec-title">Investment Thesis</span><span class="sec-line"></span></div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                rhtml = "".join(f'<div class="info-item">{r}</div>' for r in reasons[:6]) or '<div class="info-item">—</div>'
                st.markdown(f'<div class="info-panel"><div class="info-title">Supporting Reasons</div>{rhtml}</div>', unsafe_allow_html=True)
            with c2:
                khtml = "".join(f'<div class="info-item">{r}</div>' for r in risks[:6]) or '<div class="info-item">—</div>'
                st.markdown(f'<div class="info-panel"><div class="info-title">Risk Factors</div>{khtml}</div>', unsafe_allow_html=True)

            st.markdown('<div class="sec-header"><span class="sec-num">03</span><span class="sec-title">Analyst Panel</span><span class="sec-line"></span></div>', unsafe_allow_html=True)
            for a in futures.get("agents_summary", {}).get("analysts", []):
                ab = a.get("bias", "neutral")
                acls = {"bullish":"bull","bearish":"bear"}.get(ab, "neutral")
                st.markdown(f"""
                <div class="arow {acls}">
                    <div>
                        <div class="arole">{a.get('role','?')}</div>
                        <div class="aconf">Confidence: {(a.get('confidence',0) or 0)*100:.0f}%</div>
                    </div>
                    <span class="apill {acls}">{ab.upper()}</span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('<div class="sec-header"><span class="sec-num">04</span><span class="sec-title">Bull vs Bear Debate</span><span class="sec-line"></span></div>', unsafe_allow_html=True)
            bull = futures.get("agents_summary", {}).get("bull", {})
            bear = futures.get("agents_summary", {}).get("bear", {})
            cb, cs = st.columns(2)
            with cb:
                st.markdown(f"""
                <div class="debate-card bull">
                    <div class="debate-label">Bull Case</div>
                    <div class="debate-text">{bull.get('thesis') or '—'}</div>
                    <div class="debate-conf">Confidence: {(bull.get('confidence',0) or 0)*100:.0f}%</div>
                </div>
                """, unsafe_allow_html=True)
            with cs:
                st.markdown(f"""
                <div class="debate-card bear">
                    <div class="debate-label">Bear Case</div>
                    <div class="debate-text">{bear.get('thesis') or '—'}</div>
                    <div class="debate-conf">Confidence: {(bear.get('confidence',0) or 0)*100:.0f}%</div>
                </div>
                """, unsafe_allow_html=True)

        # -------- SPOT --------
        with tab_spot:
            rec = (spot.get("recommendation") or "wait").upper()
            cp_s = spot.get("current_price")
            fund = spot.get("fundamental_score", 0) or 0
            inst = (spot.get("institutional_signal") or "neutral").upper()

            action = ap.get("action", "AVOID")
            headline = ap.get("headline", "")
            explanation = ap.get("plain_explanation", "")
            bt = ap.get("buy_trigger_price")
            aa = ap.get("avoid_above_price")
            hu = ap.get("hold_until_price")
            wmin = ap.get("wait_days_min", 0) or 0
            wmax = ap.get("wait_days_max", 0) or 0
            why = ap.get("why_this_action") or []
            cm = ap.get("what_would_change_mind", "")

            rmap = {"BUY_NOW":"verdict-buy","WAIT_FOR_PRICE":"verdict-wait",
                    "HOLD":"verdict-buy","SELL_AT_PRICE":"verdict-wait",
                    "SELL_NOW":"verdict-avoid","AVOID":"verdict-avoid",
                    "SET_ALERT":"verdict-wait"}
            vcls = rmap.get(action, "verdict-wait")

            st.markdown(f"""
            <div class="verdict {vcls}">
                <div class="verdict-top">
                    <span class="verdict-tag">Spot Recommendation</span>
                    <span class="verdict-action">{action.replace('_',' ')}</span>
                </div>
                <div class="verdict-headline">{headline}</div>
                <div class="verdict-desc">{explanation}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="sec-header"><span class="sec-num">01</span><span class="sec-title">Action Triggers</span><span class="sec-line"></span></div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="mgrid">
                <div class="mcell"><div class="mcell-label">Buy Trigger</div><div class="mcell-value green">{bt or '—'}</div></div>
                <div class="mcell"><div class="mcell-label">Avoid Above</div><div class="mcell-value red">{aa or '—'}</div></div>
                <div class="mcell"><div class="mcell-label">Wait Window</div><div class="mcell-value amber">{wmin}–{wmax}d</div></div>
                <div class="mcell"><div class="mcell-label">Hold Until</div><div class="mcell-value blue">{hu or '—'}</div></div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="sec-header"><span class="sec-num">02</span><span class="sec-title">Position Overview</span><span class="sec-line"></span></div>', unsafe_allow_html=True)
            fcls = "green" if fund >= 65 else "red" if fund <= 35 else "amber"
            st.markdown(f"""
            <div class="mgrid">
                <div class="mcell"><div class="mcell-label">Recommendation</div><div class="mcell-value">{rec}</div></div>
                <div class="mcell"><div class="mcell-label">Current Price</div><div class="mcell-value blue">{cp_s or '—'}</div></div>
                <div class="mcell"><div class="mcell-label">Fundamental Score</div><div class="mcell-value {fcls}">{fund}/100</div></div>
                <div class="mcell"><div class="mcell-label">Institutional</div><div class="mcell-value">{inst}</div></div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="sec-header"><span class="sec-num">03</span><span class="sec-title">Price Targets</span><span class="sec-line"></span></div>', unsafe_allow_html=True)
            t1 = spot.get("target_1d"); t5 = spot.get("target_5d")
            t10 = spot.get("target_10d"); t30 = spot.get("target_30d")
            p1 = (spot.get("prob_1d",0) or 0)*100
            p5 = (spot.get("prob_5d",0) or 0)*100
            p10 = (spot.get("prob_10d",0) or 0)*100
            p30 = (spot.get("prob_30d",0) or 0)*100
            st.markdown(f"""
            <div class="mgrid">
                <div class="mcell"><div class="mcell-label">1 Day</div><div class="mcell-value green">{t1 or '—'}</div><div class="mcell-sub">Probability {p1:.0f}%</div></div>
                <div class="mcell"><div class="mcell-label">5 Days</div><div class="mcell-value green">{t5 or '—'}</div><div class="mcell-sub">Probability {p5:.0f}%</div></div>
                <div class="mcell"><div class="mcell-label">10 Days</div><div class="mcell-value green">{t10 or '—'}</div><div class="mcell-sub">Probability {p10:.0f}%</div></div>
                <div class="mcell"><div class="mcell-label">30 Days</div><div class="mcell-value green">{t30 or '—'}</div><div class="mcell-sub">Probability {p30:.0f}%</div></div>
            </div>
            """, unsafe_allow_html=True)

            if spot.get("thesis"):
                st.markdown('<div class="sec-header"><span class="sec-num">04</span><span class="sec-title">Investment Thesis</span><span class="sec-line"></span></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="info-panel"><div class="info-item">{spot["thesis"]}</div></div>', unsafe_allow_html=True)

            st.markdown('<div class="sec-header"><span class="sec-num">05</span><span class="sec-title">Reasoning & Risks</span><span class="sec-line"></span></div>', unsafe_allow_html=True)
            cr, ck = st.columns(2)
            with cr:
                rhtml = "".join(f'<div class="info-item">{r}</div>' for r in (spot.get("reasons") or [])[:6]) or '<div class="info-item">—</div>'
                st.markdown(f'<div class="info-panel"><div class="info-title">Reasons</div>{rhtml}</div>', unsafe_allow_html=True)
            with ck:
                khtml = "".join(f'<div class="info-item">{r}</div>' for r in (spot.get("risks") or [])[:6]) or '<div class="info-item">—</div>'
                st.markdown(f'<div class="info-panel"><div class="info-title">Risks</div>{khtml}</div>', unsafe_allow_html=True)

            st.markdown('<div class="sec-header"><span class="sec-num">06</span><span class="sec-title">Spot Debate</span><span class="sec-line"></span></div>', unsafe_allow_html=True)
            cb2, cs2 = st.columns(2)
            with cb2:
                st.markdown(f"""
                <div class="debate-card bull">
                    <div class="debate-label">Spot Bull</div>
                    <div class="debate-text">{spot.get('bull_thesis') or '—'}</div>
                    <div class="debate-conf">Confidence: {(spot.get('bull_confidence',0) or 0)*100:.0f}%</div>
                </div>
                """, unsafe_allow_html=True)
            with cs2:
                st.markdown(f"""
                <div class="debate-card bear">
                    <div class="debate-label">Spot Bear</div>
                    <div class="debate-text">{spot.get('bear_thesis') or '—'}</div>
                    <div class="debate-conf">Confidence: {(spot.get('bear_confidence',0) or 0)*100:.0f}%</div>
                </div>
                """, unsafe_allow_html=True)

            if why or cm:
                st.markdown('<div class="sec-header"><span class="sec-num">07</span><span class="sec-title">Decision Rationale</span><span class="sec-line"></span></div>', unsafe_allow_html=True)
                whtml = "".join(f'<div class="info-item">{w}</div>' for w in why)
                cmhtml = f'<div class="info-item"><b>Change mind if:</b> {cm}</div>' if cm else ''
                st.markdown(f'<div class="info-panel">{whtml}{cmhtml}</div>', unsafe_allow_html=True)

            if spot.get("institutional_evidence") or spot.get("onchain_evidence"):
                st.markdown('<div class="sec-header"><span class="sec-num">08</span><span class="sec-title">Institutional & On-Chain Evidence</span><span class="sec-line"></span></div>', unsafe_allow_html=True)
                ev = (spot.get("institutional_evidence") or []) + (spot.get("onchain_evidence") or [])
                evhtml = "".join(f'<div class="info-item">{e}</div>' for e in ev[:6])
                st.markdown(f'<div class="info-panel">{evhtml}</div>', unsafe_allow_html=True)

        # -------- PAPER LOG --------
        with tab_log:
            trades = load_trades()
            st.markdown('<div class="sec-header"><span class="sec-num">LOG</span><span class="sec-title">Paper Trade History</span><span class="sec-line"></span></div>', unsafe_allow_html=True)

            if not trades:
                st.info("No paper trades yet.")
            else:
                total = len(trades)
                st.markdown(f"""
                <div class="mgrid">
                    <div class="mcell"><div class="mcell-label">Total Signals</div><div class="mcell-value">{total}</div></div>
                    <div class="mcell"><div class="mcell-label">File</div><div class="mcell-value" style="font-size:11px">{TRADES_FILE.name}</div></div>
                    <div class="mcell"><div class="mcell-label">First</div><div class="mcell-value" style="font-size:11px">{trades[0].get('timestamp','')[:16]}</div></div>
                    <div class="mcell"><div class="mcell-label">Latest</div><div class="mcell-value" style="font-size:11px">{trades[-1].get('timestamp','')[:16]}</div></div>
                </div>
                """, unsafe_allow_html=True)

                csv_data = TRADES_FILE.read_text(encoding="utf-8")
                st.download_button(
                    label="DOWNLOAD CSV (for Google Sheets)",
                    data=csv_data,
                    file_name=f"paper_trades_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                )

                st.markdown("**Recent Signals** (latest 20)")
                cols = ["timestamp","symbol","fut_timeframe","fut_bias","fut_entry","fut_sl","fut_tp1","spot_action","outcome"]
                # Normalize timeframe key
                display = []
                for t in trades[-20:]:
                    display.append({
                        "timestamp": t.get("timestamp",""),
                        "symbol": t.get("symbol",""),
                        "timeframe": t.get("timeframe","") or t.get("fut_timeframe",""),
                        "fut_bias": t.get("fut_bias",""),
                        "fut_entry": t.get("fut_entry",""),
                        "fut_sl": t.get("fut_sl",""),
                        "fut_tp1": t.get("fut_tp1",""),
                        "spot_action": t.get("spot_action",""),
                        "outcome": t.get("outcome",""),
                    })
                st.dataframe(display, width="stretch", hide_index=True)
                st.caption("Open this CSV in Excel or upload to Google Sheets to track outcomes.")

        # -------- SCAN ALL COINS --------
        with tab_scan:
            st.markdown('<div class="sec-header"><span class="sec-num">SCAN</span><span class="sec-title">Multi-Coin Scanner</span><span class="sec-line"></span></div>', unsafe_allow_html=True)
            st.caption("Scan every available coin on the exchange. Results saved to scan_results.csv.")

            c1, c2, c3 = st.columns(3)
            scan_limit = c1.number_input("Limit (0 = all)", min_value=0, value=10, step=5, key="scan_lim")
            scan_min = c2.number_input("Min score", min_value=1, value=5, step=1, key="scan_min")
            scan_sleep = c3.number_input("Delay (sec)", min_value=0.0, value=0.5, step=0.1, key="scan_sleep")

            if st.button("SCAN ALL COINS", type="primary", key="scan_btn"):
                with st.status("Scanning exchange...", expanded=True) as sstatus:
                    try:
                        from batch_scanner import scan as run_scan
                        results = run_scan(limit=int(scan_limit), sleep_sec=float(scan_sleep), min_score=int(scan_min))
                        sstatus.update(label=f"Scan complete — {len(results)} strong signals", state="complete", expanded=False)
                        if results:
                            st.dataframe(results, width="stretch", hide_index=True)
                        else:
                            st.info("No signals above min score.")
                    except Exception as e:
                        sstatus.update(label="Scan failed", state="error", expanded=True)
                        st.error(f"{type(e).__name__}: {e}")

            # Show previous results
            from pathlib import Path as _P
            scan_csv = _P("scan_results.csv")
            if scan_csv.exists():
                st.markdown('<div class="sec-header"><span class="sec-num">HIST</span><span class="sec-title">Previous Scan Results</span><span class="sec-line"></span></div>', unsafe_allow_html=True)
                try:
                    import pandas as _pd
                    df_scan = _pd.read_csv(scan_csv)
                    st.dataframe(df_scan.tail(50), width="stretch", hide_index=True)
                    st.download_button("DOWNLOAD scan_results.csv", data=scan_csv.read_text(), file_name="scan_results.csv", mime="text/csv", key="scan_dl")
                except Exception as e:
                    st.warning(f"Could not read scan_results.csv: {e}")

        # -------- RAW DATA --------
        with tab_data:
            st.markdown('<div class="sec-header"><span class="sec-num">DATA</span><span class="sec-title">Complete JSON Output</span><span class="sec-line"></span></div>', unsafe_allow_html=True)
            st.json(result)


st.markdown("""
<div class="fa-footer">
    FUTURE ADMIRAL · INSTITUTIONAL MULTI-AGENT TRADING DESK<br>
    Research tool — not financial advice · Paper trade before real capital
</div>
""", unsafe_allow_html=True)
