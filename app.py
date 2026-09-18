"""Future Admiral v7 - Professional SPOT + FUTURES Dashboard"""
import streamlit as st
import time, traceback
from datetime import datetime

st.set_page_config(page_title="Future Admiral v7", page_icon="👑", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(180deg,#0a0e1a,#0f1420); }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1rem; max-width: 1500px; }
.fa-header { display:flex; align-items:center; gap:16px; padding:16px 0 20px 0;
    border-bottom:1px solid rgba(56,189,248,0.15); margin-bottom:24px; }
.fa-logo { font-size:42px; filter:drop-shadow(0 0 14px rgba(251,191,36,0.6)); }
.fa-title { font-size:28px; font-weight:800;
    background:linear-gradient(90deg,#38bdf8,#34d399);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin:0; }
.fa-subtitle { color:#64748b; font-size:11px; letter-spacing:1.5px; text-transform:uppercase; margin-top:4px; }
.fa-badge { margin-left:auto; padding:7px 16px; background:rgba(16,185,129,0.1);
    border:1px solid rgba(16,185,129,0.3); border-radius:24px;
    color:#10b981; font-size:10px; font-weight:700; letter-spacing:1px; }
.rec-banner { padding:22px 26px; border-radius:16px; margin:14px 0; }
.rec-buy-now { background:linear-gradient(135deg,rgba(16,185,129,0.22),rgba(5,150,105,0.08));
    border:1px solid rgba(16,185,129,0.4); }
.rec-buy-dip { background:linear-gradient(135deg,rgba(251,191,36,0.22),rgba(217,119,6,0.08));
    border:1px solid rgba(251,191,36,0.4); }
.rec-wait { background:linear-gradient(135deg,rgba(56,189,248,0.15),rgba(14,165,233,0.06));
    border:1px solid rgba(56,189,248,0.3); }
.rec-avoid { background:linear-gradient(135deg,rgba(239,68,68,0.22),rgba(220,38,38,0.08));
    border:1px solid rgba(239,68,68,0.4); }
.rec-title { font-size:26px; font-weight:800; letter-spacing:-0.5px; margin:0; }
.rec-sub { color:#94a3b8; font-size:13px; margin-top:8px; line-height:1.6; }
.mgrid { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:18px 0; }
.mbox { background:rgba(30,41,59,0.5); border:1px solid rgba(71,85,105,0.3);
    border-radius:12px; padding:14px 16px; }
.mlabel { color:#64748b; font-size:9px; font-weight:700; letter-spacing:1px;
    text-transform:uppercase; margin-bottom:6px; }
.mval { color:#e2e8f0; font-size:17px; font-weight:700; }
.mval-green { color:#10b981; } .mval-red { color:#ef4444; }
.mval-blue { color:#38bdf8; } .mval-amber { color:#fbbf24; }
.section-title { color:#94a3b8; font-size:11px; font-weight:700; letter-spacing:1.5px;
    text-transform:uppercase; margin:24px 0 12px 0; padding-bottom:8px;
    border-bottom:1px solid rgba(71,85,105,0.3); }
.reason-item { color:#cbd5e1; font-size:13px; padding:7px 0 7px 20px; position:relative; }
.reason-item::before { content:"▸"; color:#38bdf8; position:absolute; left:0; font-weight:bold; }
.analyst-row { display:flex; justify-content:space-between; align-items:center;
    padding:14px 18px; background:rgba(30,41,59,0.4); border-radius:10px;
    margin:6px 0; border-left:3px solid transparent; }
.analyst-row-bullish { border-left-color:#10b981; }
.analyst-row-bearish { border-left-color:#ef4444; }
.analyst-row-neutral { border-left-color:#6b7280; }
.analyst-name { color:#cbd5e1; font-weight:600; font-size:13px; }
.analyst-conf { color:#64748b; font-size:11px; margin-top:3px; }
.analyst-bias-pill { padding:5px 12px; border-radius:6px; font-size:10px;
    font-weight:800; letter-spacing:0.5px; }
.pill-bullish { background:rgba(16,185,129,0.15); color:#10b981; }
.pill-bearish { background:rgba(239,68,68,0.15); color:#ef4444; }
.pill-neutral { background:rgba(107,114,128,0.15); color:#94a3b8; }
section[data-testid="stSidebar"] { background:linear-gradient(180deg,#0a0e1a,#0f172a);
    border-right:1px solid rgba(56,189,248,0.1); }
.stButton > button[kind="primary"] { background:linear-gradient(90deg,#ef4444,#dc2626);
    border:none; border-radius:12px; font-weight:800; padding:14px 24px; }
.stTabs [data-baseweb="tab"] { background:rgba(30,41,59,0.4); border-radius:10px;
    padding:10px 20px; color:#94a3b8; font-weight:700; font-size:13px; }
.stTabs [aria-selected="true"] { background:rgba(56,189,248,0.15) !important;
    color:#38bdf8 !important; }
.fa-footer { margin-top:60px; padding-top:24px;
    border-top:1px solid rgba(71,85,105,0.3); text-align:center;
    color:#475569; font-size:11px; line-height:1.8; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="fa-header">
    <span class="fa-logo">👑</span>
    <div>
        <h1 class="fa-title">Future Admiral v7</h1>
        <div class="fa-subtitle">Institutional Multi-Agent Trading Desk</div>
    </div>
    <div class="fa-badge">● SYSTEM LIVE</div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="section-title">Configuration</div>', unsafe_allow_html=True)
    symbol = st.text_input("Asset Symbol", value="XRP/USDT")
    timeframe = st.selectbox("Primary Timeframe", ["1m","5m","15m","1h","4h","1d"], index=2)
    send_discord_flag = st.checkbox("Send Discord Alert", value=True)
    run = st.button("⚡  RUN FULL ANALYSIS", use_container_width=True, type="primary")
    st.markdown('<div class="section-title">System Status</div>', unsafe_allow_html=True)
    try:
        import requests, os
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        from dotenv import load_dotenv
        load_dotenv()
        if os.getenv("GROQ_API_KEY"):
            st.success("🟢 Groq Cloud (Primary)")
        else:
            st.info("🔵 Ollama (Primary)")
        if r.status_code == 200:
            st.success("🟢 Ollama Server")
    except Exception:
        st.error("🔴 Ollama offline")
    st.caption(f"⏱ {datetime.now().strftime('%Y-%m-%d %H:%M')}")

if run and symbol:
    result = None
    with st.status(f"🔍 Analyzing {symbol}...", expanded=True) as status:
        try:
            from future_admiral_v7.debate.engine import run_debate
            t = time.time()
            result = run_debate(symbol, timeframe, ui=status)
            elapsed = time.time() - t
            status.update(label=f"✅ Complete in {elapsed:.0f}s", state="complete", expanded=False)
        except Exception as e:
            status.update(label="❌ Failed", state="error", expanded=True)
            st.error(f"**{type(e).__name__}**: {e}")
            st.code(traceback.format_exc())

    if result:
        futures = result.get("futures", {}) or {}
        spot = result.get("spot", {}) or {}
        st.divider()

        # ===== ACTION BANNER =====
        ap = spot.get("action_plan") or {}
        if ap and ap.get("action"):
            action = ap.get("action", "AVOID")
            rec_class = {
                "BUY_NOW": "rec-buy-now", "BUY_DIP": "rec-buy-dip",
                "WAIT_FOR_PRICE": "rec-wait", "HOLD": "rec-buy-now",
                "SELL_AT_PRICE": "rec-buy-dip", "SELL_NOW": "rec-avoid",
                "AVOID": "rec-avoid", "SET_ALERT": "rec-wait",
            }.get(action, "rec-wait")
            emoji = {"BUY_NOW":"💎","BUY_DIP":"📉","WAIT_FOR_PRICE":"⏸","HOLD":"🤲",
                     "SELL_AT_PRICE":"🎯","SELL_NOW":"🚨","AVOID":"🚫","SET_ALERT":"🔔"}.get(action,"•")
            st.markdown(f"""
            <div class="rec-banner {rec_class}">
                <div class="rec-title">{emoji} {action.replace('_',' ')}</div>
                <div class="rec-sub"><b>{ap.get('headline','')}</b><br>{ap.get('plain_explanation','')}</div>
            </div>
            """, unsafe_allow_html=True)

            cols = st.columns(4)
            cols[0].metric("Buy Trigger", ap.get("buy_trigger_price") or "—")
            cols[1].metric("Avoid Above", ap.get("avoid_above_price") or "—")
            cols[2].metric("Wait Days", f"{ap.get('wait_days_min',0)}–{ap.get('wait_days_max',0)}")
            cols[3].metric("Hold Until", ap.get("hold_until_price") or "—")

            if ap.get("why_this_action"):
                with st.expander("💡 Why this action"):
                    for w in ap["why_this_action"]:
                        st.markdown(f'<div class="reason-item">{w}</div>', unsafe_allow_html=True)

        # ===== TABS =====
        tab_spot, tab_fut, tab_data = st.tabs(["💎 SPOT", "⚡ FUTURES", "🔍 Full Data"])

        with tab_spot:
            cp = spot.get("current_price")
            rec = (spot.get("recommendation") or "wait").upper()
            fund = spot.get("fundamental_score", 0) or 0
            inst = spot.get("institutional_signal", "neutral")
            fund_cls = "mval-green" if fund >= 65 else "mval-red" if fund <= 35 else "mval-amber"
            st.markdown(f"""
            <div class="mgrid">
                <div class="mbox"><div class="mlabel">Recommendation</div><div class="mval">{rec}</div></div>
                <div class="mbox"><div class="mlabel">Current Price</div><div class="mval mval-blue">{cp or '—'}</div></div>
                <div class="mbox"><div class="mlabel">Fundamental</div><div class="mval {fund_cls}">{fund}/100</div></div>
                <div class="mbox"><div class="mlabel">Institutional</div><div class="mval">{inst.upper()}</div></div>
                <div class="mbox"><div class="mlabel">Target 1D</div><div class="mval mval-green">{spot.get('target_1d') or '—'}</div></div>
                <div class="mbox"><div class="mlabel">Target 5D</div><div class="mval mval-green">{spot.get('target_5d') or '—'}</div></div>
                <div class="mbox"><div class="mlabel">Target 10D</div><div class="mval mval-green">{spot.get('target_10d') or '—'}</div></div>
                <div class="mbox"><div class="mlabel">Target 30D</div><div class="mval mval-green">{spot.get('target_30d') or '—'}</div></div>
            </div>
            """, unsafe_allow_html=True)
            if spot.get("thesis"):
                st.info(spot["thesis"])

            col_b, col_s = st.columns(2)
            with col_b:
                st.markdown("### 🐂 Spot Bull")
                st.success(spot.get("bull_thesis") or "—")
                st.caption(f"Confidence: {(spot.get('bull_confidence',0) or 0)*100:.0f}%")
            with col_s:
                st.markdown("### 🐻 Spot Bear")
                st.error(spot.get("bear_thesis") or "—")
                st.caption(f"Confidence: {(spot.get('bear_confidence',0) or 0)*100:.0f}%")

            col_r, col_rk = st.columns(2)
            with col_r:
                st.markdown('<div class="section-title">Reasons</div>', unsafe_allow_html=True)
                for r_ in (spot.get("reasons") or [])[:6]:
                    st.markdown(f'<div class="reason-item">{r_}</div>', unsafe_allow_html=True)
            with col_rk:
                st.markdown('<div class="section-title">Risks</div>', unsafe_allow_html=True)
                for r_ in (spot.get("risks") or [])[:6]:
                    st.markdown(f'<div class="reason-item">{r_}</div>', unsafe_allow_html=True)

        with tab_fut:
            bias = (futures.get("bias") or "neutral").upper()
            tt = (futures.get("trade_type") or "none").upper()
            conf_f = futures.get("confidence", 0) or 0
            dur = futures.get("duration_hours", 0) or 0
            entry_f = futures.get("entry")
            sl_f = futures.get("stop_loss")
            tp_f = futures.get("take_profit") or []
            rr_f = futures.get("risk_reward", 0)
            size_f = futures.get("position_size_pct", 0)
            lev_f = futures.get("leverage", 1)
            cp_f = futures.get("current_price")
            bias_cls = "mval-green" if bias == "LONG" else "mval-red" if bias == "SHORT" else "mval-amber"
            tp1 = tp_f[0] if len(tp_f) > 0 else "—"
            tp2 = tp_f[1] if len(tp_f) > 1 else "—"
            st.markdown(f"""
            <div class="mgrid">
                <div class="mbox"><div class="mlabel">Bias</div><div class="mval {bias_cls}">{bias}</div></div>
                <div class="mbox"><div class="mlabel">Type</div><div class="mval">{tt}</div></div>
                <div class="mbox"><div class="mlabel">Current</div><div class="mval mval-blue">{cp_f or '—'}</div></div>
                <div class="mbox"><div class="mlabel">Entry</div><div class="mval">{entry_f or '—'}</div></div>
                <div class="mbox"><div class="mlabel">Stop Loss</div><div class="mval mval-red">{sl_f or '—'}</div></div>
                <div class="mbox"><div class="mlabel">TP 1</div><div class="mval mval-green">{tp1}</div></div>
                <div class="mbox"><div class="mlabel">TP 2</div><div class="mval mval-green">{tp2}</div></div>
                <div class="mbox"><div class="mlabel">R:R</div><div class="mval mval-amber">{rr_f}</div></div>
                <div class="mbox"><div class="mlabel">Size</div><div class="mval">{size_f}%</div></div>
                <div class="mbox"><div class="mlabel">Leverage</div><div class="mval">{lev_f}x</div></div>
                <div class="mbox"><div class="mlabel">Duration</div><div class="mval">{dur}h</div></div>
                <div class="mbox"><div class="mlabel">Confidence</div><div class="mval">{conf_f*100:.0f}%</div></div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('<div class="section-title">Analyst Panel</div>', unsafe_allow_html=True)
            for a in futures.get("agents_summary", {}).get("analysts", []):
                ab = a.get("bias", "neutral")
                st.markdown(f"""
                <div class="analyst-row analyst-row-{ab}">
                    <div>
                        <div class="analyst-name">{a.get('role','?')}</div>
                        <div class="analyst-conf">Confidence: {(a.get('confidence',0) or 0)*100:.0f}%</div>
                    </div>
                    <span class="analyst-bias-pill pill-{ab}">{ab.upper()}</span>
                </div>""", unsafe_allow_html=True)

        with tab_data:
            st.json(result)

        if send_discord_flag:
            try:
                from future_admiral_v7.alerts.discord import send_discord_embed
                ok = send_discord_embed(futures)
                if ok:
                    st.success("✅ Discord alert sent")
                else:
                    st.warning("⚠️ Discord webhook not configured")
            except Exception as e:
                st.warning(f"Discord error: {e}")

st.markdown("""
<div class="fa-footer">
    👑 <b>Future Admiral v7</b> · SPOT + FUTURES Multi-Agent Desk<br>
    ⚠️ Research tool only — NOT financial advice · Always paper trade first
</div>
""", unsafe_allow_html=True)
