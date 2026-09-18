"""
Future Admiral v7 - Professional Institutional Dashboard
"""
import streamlit as st
import time
import traceback
from datetime import datetime

st.set_page_config(
    page_title="Future Admiral v7",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(180deg, #0a0e1a 0%, #0f1420 100%); }
#MainMenu, footer, header { visibility: hidden; }

.block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 1400px; }

/* Header */
.fa-header { display: flex; align-items: center; gap: 16px; padding: 16px 0 20px 0;
    border-bottom: 1px solid rgba(56,189,248,0.15); margin-bottom: 24px; }
.fa-logo { font-size: 40px; filter: drop-shadow(0 0 12px rgba(251,191,36,0.5)); }
.fa-title { font-size: 26px; font-weight: 800;
    background: linear-gradient(90deg,#38bdf8 0%,#34d399 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    letter-spacing: -0.5px; margin: 0; }
.fa-subtitle { color: #64748b; font-size: 12px; letter-spacing: 0.5px; margin-top: 2px; }
.fa-status-badge { margin-left: auto; display: inline-flex; align-items: center; gap: 8px;
    padding: 6px 14px; background: rgba(16,185,129,0.1);
    border: 1px solid rgba(16,185,129,0.3); border-radius: 20px;
    color: #10b981; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; }
.fa-status-dot { width: 8px; height: 8px; background: #10b981; border-radius: 50%;
    animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

/* Signal Card */
.signal-card { background: linear-gradient(135deg,rgba(17,24,39,0.9),rgba(15,23,42,0.9));
    border: 1px solid rgba(56,189,248,0.2); border-radius: 16px;
    padding: 24px; margin: 12px 0; box-shadow: 0 20px 40px -20px rgba(0,0,0,0.5); }
.signal-card-long { border-left: 4px solid #10b981; }
.signal-card-short { border-left: 4px solid #ef4444; }
.signal-card-neutral { border-left: 4px solid #6b7280; }
.signal-bias { font-size: 30px; font-weight: 800; letter-spacing: -1px; }
.signal-bias-long { color: #10b981; }
.signal-bias-short { color: #ef4444; }
.signal-bias-neutral { color: #94a3b8; }
.signal-symbol { font-size: 15px; color: #94a3b8; font-weight: 500; margin-left: 12px; }
.signal-meta { color: #64748b; font-size: 13px; margin-top: 6px; }

/* Metric Grid */
.metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 20px 0; }
.metric-box { background: rgba(30,41,59,0.4); border: 1px solid rgba(71,85,105,0.3);
    border-radius: 10px; padding: 12px 14px; transition: all 0.2s; }
.metric-box:hover { border-color: rgba(56,189,248,0.5); transform: translateY(-2px); }
.metric-label { color: #64748b; font-size: 10px; font-weight: 700;
    letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 4px; }
.metric-value { color: #e2e8f0; font-size: 18px; font-weight: 700;
    font-variant-numeric: tabular-nums; }
.metric-value-green { color: #10b981; }
.metric-value-red { color: #ef4444; }
.metric-value-blue { color: #38bdf8; }
.metric-value-amber { color: #fbbf24; }

/* Analyst Row */
.analyst-row { display: flex; justify-content: space-between; align-items: center;
    padding: 12px 16px; background: rgba(30,41,59,0.35); border-radius: 10px;
    margin: 6px 0; border-left: 3px solid transparent; }
.analyst-row-bullish { border-left-color: #10b981; }
.analyst-row-bearish { border-left-color: #ef4444; }
.analyst-row-neutral { border-left-color: #6b7280; }
.analyst-name { color: #cbd5e1; font-weight: 600; font-size: 14px; }
.analyst-bias { font-size: 11px; font-weight: 700; padding: 4px 10px;
    border-radius: 6px; letter-spacing: 0.5px; }
.bias-pill-bullish { background: rgba(16,185,129,0.15); color: #10b981; }
.bias-pill-bearish { background: rgba(239,68,68,0.15); color: #ef4444; }
.bias-pill-neutral { background: rgba(107,114,128,0.15); color: #94a3b8; }

/* Section */
.section-title { color: #94a3b8; font-size: 11px; font-weight: 700;
    letter-spacing: 1.5px; text-transform: uppercase; margin: 20px 0 10px 0;
    padding-bottom: 6px; border-bottom: 1px solid rgba(71,85,105,0.3); }
.reason-item { color: #cbd5e1; font-size: 13px; padding: 6px 0 6px 18px;
    position: relative; }
.reason-item::before { content: "▸"; color: #38bdf8; position: absolute;
    left: 0; font-weight: bold; }

/* Sidebar */
section[data-testid="stSidebar"] { background: linear-gradient(180deg,#0a0e1a,#0f172a);
    border-right: 1px solid rgba(56,189,248,0.1); }

/* Button */
.stButton > button[kind="primary"] {
    background: linear-gradient(90deg,#ef4444,#dc2626);
    border: none; border-radius: 10px; font-weight: 700;
    padding: 12px 24px; color: white; transition: all 0.2s;
    box-shadow: 0 8px 20px -8px rgba(239,68,68,0.6); }
.stButton > button[kind="primary"]:hover { transform: translateY(-1px);
    box-shadow: 0 12px 24px -8px rgba(239,68,68,0.8); }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 8px; background: transparent; }
.stTabs [data-baseweb="tab"] { background: rgba(30,41,59,0.4);
    border-radius: 8px; padding: 8px 16px; color: #94a3b8; font-weight: 600; }
.stTabs [aria-selected="true"] { background: rgba(56,189,248,0.15) !important;
    color: #38bdf8 !important; }

/* Footer */
.fa-footer { margin-top: 50px; padding-top: 20px;
    border-top: 1px solid rgba(71,85,105,0.3); text-align: center;
    color: #475569; font-size: 11px; letter-spacing: 0.3px; }
</style>
""", unsafe_allow_html=True)


st.markdown("""
<div class="fa-header">
    <span class="fa-logo">👑</span>
    <div>
        <h1 class="fa-title">Future Admiral v7</h1>
        <div class="fa-subtitle">INSTITUTIONAL MULTI-AGENT TRADING DESK</div>
    </div>
    <div class="fa-status-badge">
        <span class="fa-status-dot"></span>
        SYSTEM LIVE
    </div>
</div>
""", unsafe_allow_html=True)


with st.sidebar:
    st.markdown('<div class="section-title">Configuration</div>', unsafe_allow_html=True)
    symbol = st.text_input("Asset Symbol", value="XRP/USDT",
                           help="BTC/USDT, ETH/USDT, SOL/USDT, AAPL...")
    timeframe = st.selectbox("Primary Timeframe",
                              ["1m","5m","15m","1h","4h","1d"], index=2)
    send_discord_flag = st.checkbox("Send Discord Alert", value=True)

    st.markdown("")
    run = st.button("⚡  RUN FULL DEBATE", use_container_width=True, type="primary")

    st.markdown('<div class="section-title">System Status</div>', unsafe_allow_html=True)

    try:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        groq_key = os.getenv("GROQ_API_KEY", "").strip()
    except Exception:
        groq_key = ""

    try:
        import requests
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        ollama_ok = r.status_code == 200
        ollama_models = [m["name"] for m in r.json().get("models", [])] if ollama_ok else []
    except Exception:
        ollama_ok = False
        ollama_models = []

    if groq_key:
        st.success("🟢 Groq Cloud (Primary)")
    else:
        st.info("🔵 Ollama Local (Primary)")

    if ollama_ok:
        st.success("🟢 Ollama Server")
        if ollama_models:
            st.caption(f"Models: {len(ollama_models)} available")
    else:
        st.error("🔴 Ollama Offline")

    st.caption(f"⏱ {datetime.now().strftime('%Y-%m-%d %H:%M')}")


if run and symbol:
    result = None
    elapsed = 0.0

    with st.status(f"🔍 Initializing multi-agent debate for {symbol}...",
                   expanded=True) as status:
        try:
            st.write("📊 Step 1: Ingesting market data (6 timeframes)...")
            from future_admiral_v7.debate.engine import run_debate
            st.write("🧠 Step 2: Running 7 analyst agents...")
            t = time.time()
            result = run_debate(symbol, timeframe, ui=status)
            elapsed = time.time() - t
            status.update(label=f"✅ Analysis complete in {elapsed:.0f}s",
                          state="complete", expanded=False)
        except Exception as e:
            status.update(label="❌ Analysis failed", state="error", expanded=True)
            st.error(f"**{type(e).__name__}**: {e}")
            st.code(traceback.format_exc())

    if result:
        st.divider()

        bias = result.get("bias", "neutral").upper()
        trade_type = result.get("trade_type", "none").upper()
        confidence = result.get("confidence", 0)
        duration = result.get("duration_hours", 0)
        current_price = result.get("current_price")
        entry = result.get("entry")
        sl = result.get("stop_loss")
        tp = result.get("take_profit") or []
        rr = result.get("risk_reward", 0)
        size_pct = result.get("position_size_pct", 0)
        leverage = result.get("leverage", 1)
        reasons = result.get("reasons", [])
        risks = result.get("risks", [])
        support = result.get("support", [])
        resistance = result.get("resistance", [])
        invalidation = result.get("invalidation", "")

        bias_class = {"LONG": "long", "SHORT": "short"}.get(bias, "neutral")
        tp1 = tp[0] if len(tp) > 0 else "—"
        tp2 = tp[1] if len(tp) > 1 else "—"

        st.markdown(f"""
        <div class="signal-card signal-card-{bias_class}">
            <div>
                <span class="signal-bias signal-bias-{bias_class}">{bias}</span>
                <span class="signal-symbol">{result.get('symbol','')} · {result.get('timeframe','')}</span>
            </div>
            <div class="signal-meta">
                Type: <b>{trade_type}</b> &nbsp;·&nbsp;
                Duration: <b>{duration}h</b> &nbsp;·&nbsp;
                Confidence: <b>{confidence*100:.0f}%</b>
            </div>
            <div class="metric-grid">
                <div class="metric-box"><div class="metric-label">Current Price</div><div class="metric-value metric-value-blue">{current_price or '—'}</div></div>
                <div class="metric-box"><div class="metric-label">Entry</div><div class="metric-value">{entry or '—'}</div></div>
                <div class="metric-box"><div class="metric-label">Stop Loss</div><div class="metric-value metric-value-red">{sl or '—'}</div></div>
                <div class="metric-box"><div class="metric-label">Take Profit 1</div><div class="metric-value metric-value-green">{tp1}</div></div>
                <div class="metric-box"><div class="metric-label">Take Profit 2</div><div class="metric-value metric-value-green">{tp2}</div></div>
                <div class="metric-box"><div class="metric-label">Risk / Reward</div><div class="metric-value metric-value-amber">{rr}</div></div>
                <div class="metric-box"><div class="metric-label">Position Size</div><div class="metric-value">{size_pct}%</div></div>
                <div class="metric-box"><div class="metric-label">Leverage</div><div class="metric-value">{leverage}x</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        tab_overview, tab_analysts, tab_debate, tab_json = st.tabs(
            ["📊 Overview", "🧠 Analysts", "⚔ Debate", "🔍 Full Data"]
        )

        with tab_overview:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<div class="section-title">Key Levels</div>', unsafe_allow_html=True)
                if support:
                    st.markdown("🟢 **Support**")
                    for s in support[:3]:
                        st.markdown(f"&nbsp;&nbsp;&nbsp;`{s}`")
                if resistance:
                    st.markdown("🔴 **Resistance**")
                    for r_ in resistance[:3]:
                        st.markdown(f"&nbsp;&nbsp;&nbsp;`{r_}`")
            with c2:
                st.markdown('<div class="section-title">Reasoning</div>', unsafe_allow_html=True)
                for r_ in reasons[:6]:
                    st.markdown(f'<div class="reason-item">{r_}</div>', unsafe_allow_html=True)

            if risks:
                st.markdown('<div class="section-title">Risks</div>', unsafe_allow_html=True)
                for r_ in risks[:5]:
                    st.markdown(f'<div class="reason-item">{r_}</div>', unsafe_allow_html=True)

            if invalidation:
                st.warning(f"⚠️ **Invalidation:** {invalidation}")

        with tab_analysts:
            st.markdown('<div class="section-title">Analyst Views</div>', unsafe_allow_html=True)
            analysts = result.get("agents_summary", {}).get("analysts", [])
            for a in analysts:
                role = a.get("role", "Analyst")
                a_bias = a.get("bias", "neutral")
                a_conf = a.get("confidence", 0)
                a_points = a.get("key_points", [])
                a_risks = a.get("risks", [])
                st.markdown(f"""
                <div class="analyst-row analyst-row-{a_bias}">
                    <div>
                        <div class="analyst-name">{role}</div>
                        <div style="color:#64748b;font-size:11px;margin-top:2px;">Confidence: {a_conf:.0%}</div>
                    </div>
                    <span class="analyst-bias bias-pill-{a_bias}">{a_bias.upper()}</span>
                </div>
                """, unsafe_allow_html=True)
                if a_points or a_risks:
                    with st.expander(f"{role} details"):
                        if a_points:
                            st.markdown("**Key Points:**")
                            for p in a_points[:5]:
                                st.markdown(f"- {p}")
                        if a_risks:
                            st.markdown("**Risks:**")
                            for r_ in a_risks[:5]:
                                st.markdown(f"- {r_}")

        with tab_debate:
            summary = result.get("agents_summary", {})
            bull = summary.get("bull", {})
            bear = summary.get("bear", {})
            col_b, col_s = st.columns(2)
            with col_b:
                st.markdown("### 🐂 Bull Case")
                st.info(bull.get("thesis", "—"))
                st.caption(f"Confidence: {bull.get('confidence', 0):.0%}")
            with col_s:
                st.markdown("### 🐻 Bear Case")
                st.warning(bear.get("thesis", "—"))
                st.caption(f"Confidence: {bear.get('confidence', 0):.0%}")

        with tab_json:
            st.json(result)

        if send_discord_flag:
            try:
                from future_admiral_v7.alerts.discord import send_discord_embed
                ok = send_discord_embed(result)
                if ok:
                    st.success("✅ Discord alert sent")
                else:
                    st.warning("⚠️ Discord webhook not configured")
            except Exception as e:
                st.warning(f"Discord error: {e}")

st.markdown("""
<div class="fa-footer">
    👑 <b>Future Admiral v7</b> · Institutional Multi-Agent Trading Desk<br>
    100% Free · Ollama + ccxt + yfinance · Not financial advice
</div>
""", unsafe_allow_html=True)
