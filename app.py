"""
Future Admiral v7 - Streamlit UI (Discord-only, Groq-ready)
"""
import streamlit as st
import traceback
import time

st.set_page_config(page_title="Future Admiral v7", layout="wide")

st.title("👑 Future Admiral v7 — Institutional Desk")
st.caption("Multi-Agent Debate · Multi-Timeframe · 100% Free (Groq/Ollama + ccxt + yfinance)")

with st.sidebar:
    st.header("⚙️ Config")
    symbol = st.text_input("Symbol", value="SOL/USDT")
    timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "4h", "1d"], index=2)
    send_discord_alert = st.checkbox("Discord alert bhejo", value=True)
    run = st.button("🚀 Run Full Debate", use_container_width=True, type="primary")

    st.divider()
    st.subheader("Status")

    # LLM check
    try:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        groq_key = os.getenv("GROQ_API_KEY", "")
        if groq_key:
            st.write("LLM: ✅ Groq (cloud)")
            st.caption(f"Model: {os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')}")
        else:
            st.write("LLM: ✅ Ollama (local)")
            st.caption("Groq key nahi mila — local use ho raha hai")
    except Exception:
        st.write("LLM: ⚠️")

    # Ollama check
    try:
        import requests
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        if r.status_code == 200:
            st.write("Ollama: ✅")
    except Exception:
        st.write("Ollama: ❌ (offline)")

# ---------- Main ----------
if run and symbol:
    result = None
    elapsed = 0

    with st.status("Multi-agent debate chal raha hai...", expanded=True) as status:
        try:
            st.write("⏳ Importing engine...")
            from future_admiral_v7.debate.engine import run_debate

            st.write(f"🧠 Analyzing {symbol} @ {timeframe}...")
            t = time.time()
            result = run_debate(symbol, timeframe, ui=status)
            elapsed = time.time() - t
            status.update(label=f"✅ DONE in {elapsed:.0f}s", state="complete", expanded=False)
        except Exception as e:
            status.update(label="❌ Failed", state="error", expanded=True)
            st.error(f"**{type(e).__name__}**: {e}")
            st.code(traceback.format_exc(), language="python")

    # ------- DISPLAY OUTSIDE STATUS BLOCK -------
    if result:
        st.divider()
        col1, col2 = st.columns([2, 1])

        with col1:
            bias = result.get("bias", "neutral")
            trade_type = result.get("trade_type", "none")
            color = {"long": "green", "short": "red", "neutral": "gray"}.get(bias, "gray")

            st.markdown(f"## :{color}[{bias.upper()}] · {result.get('symbol')} · {result.get('timeframe')}")
            st.caption(f"Trade type: **{trade_type.upper()}** · Duration: **{result.get('duration_hours', 0)}h** · Confidence: **{result.get('confidence', 0)*100:.0f}%**")

            if result.get("reasoning_duration"):
                st.caption(f"⏱️ {result['reasoning_duration']}")

            c1, c2, c3 = st.columns(3)
            c1.metric("Current Price", result.get("current_price") or "—")
            c2.metric("Entry", result.get("entry") or "—")
            c3.metric("R:R", result.get("risk_reward") or "—")

            c4, c5, c6 = st.columns(3)
            c4.metric("Stop Loss", result.get("stop_loss") or "—")
            tps = result.get("take_profit") or []
            c5.metric("Take Profit 1", tps[0] if len(tps) > 0 else "—")
            c6.metric("Take Profit 2", tps[1] if len(tps) > 1 else "—")

            st.markdown(f"**Size:** {result.get('position_size_pct', 0)}% · **Lev:** {result.get('leverage', 1)}x")

            # S/R
            if result.get("support") or result.get("resistance"):
                st.markdown("**Key Levels**")
                st.write(f"🟢 Support: `{result.get('support', [])}`")
                st.write(f"🔴 Resistance: `{result.get('resistance', [])}`")

            st.markdown("**Reasons**")
            for r in result.get("reasons", [])[:5]:
                st.write("•", r)

            st.markdown("**Risks**")
            for r in result.get("risks", [])[:5]:
                st.write("•", r)

            if result.get("invalidation"):
                st.warning(f"⚠️ **Invalidation:** {result['invalidation']}")

        with col2:
            st.subheader("🧠 Analysts")
            analysts = result.get("agents_summary", {}).get("analysts", [])
            for a in analysts:
                role = a.get("role", "?")
                bias_a = a.get("bias", "?")
                conf_a = a.get("confidence", 0)
                emoji = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}.get(bias_a, "⚪")
                st.write(f"{emoji} **{role}**")
                st.caption(f"{bias_a} ({conf_a:.2f})")

        with st.expander("📊 Full JSON Analysis"):
            st.json(result)

        # Discord alert
        if send_discord_alert:
            try:
                from future_admiral_v7.alerts.discord import send_discord_embed
                ok = send_discord_embed(result)
                if ok:
                    st.success("✅ Discord pe signal bhej diya")
                else:
                    st.warning("⚠️ Discord webhook config missing")
            except Exception as e:
                st.warning(f"Discord error: {e}")
