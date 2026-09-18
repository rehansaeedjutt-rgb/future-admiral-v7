"""
Future Admiral v7 - Streamlit UI (Discord-only)
"""
import streamlit as st
import traceback
import time

st.set_page_config(page_title="Future Admiral v7", layout="wide")

st.title("👑 Future Admiral v7 — Institutional Desk")
st.caption("Multi-Agent Debate · Multi-Timeframe · 100% Free (Ollama + ccxt + yfinance)")

# ---------- Sidebar ----------
with st.sidebar:
    st.header("⚙️ Config")
    symbol = st.text_input("Symbol", value="BTC/USDT")
    timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "4h", "1d"], index=2)
    send_discord = st.checkbox("Discord alert bhejo", value=True)
    run = st.button("🚀 Run Full Debate", use_container_width=True, type="primary")

    st.divider()
    st.subheader("Status")

    # Ollama check
    try:
        import requests
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            st.write(f"Ollama: ✅")
            st.caption(f"Models: {', '.join(models)}")
        else:
            st.write("Ollama: ❌ (not responding)")
    except Exception:
        st.write("Ollama: ❌")
        st.caption("`ollama serve` chalao")

# ---------- Main ----------
if run and symbol:
    with st.status("Full multi-agent debate chal raha hai...", expanded=True) as status:
        try:
            st.write("⏳ Importing engine...")
            from future_admiral_v7.debate.engine import run_debate

            st.write(f"🧠 Running debate for {symbol} @ {timeframe}...")
            t = time.time()
            result = run_debate(symbol, timeframe, ui=status)
            elapsed = time.time() - t

            status.update(label=f"✅ DONE in {elapsed:.0f}s", state="complete", expanded=False)

            # Display
            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader("🎯 Final Signal")
                bias = result.get("bias", "neutral")
                color = {"long": "green", "short": "red", "neutral": "gray"}.get(bias, "gray")
                st.markdown(f"### :{color}[{bias.upper()}] · {result.get('symbol')} · {result.get('timeframe')}")
                st.metric("Confidence", f"{result.get('confidence', 0)*100:.0f}%")

                c1, c2, c3 = st.columns(3)
                c1.metric("Entry", result.get("entry") or "—")
                c2.metric("Stop Loss", result.get("stop_loss") or "—")
                c3.metric("R:R", result.get("risk_reward") or "—")

                st.write("**Take Profit:**", result.get("take_profit") or "—")
                st.write("**Size:**", f"{result.get('position_size_pct', 0)}% · Lev {result.get('leverage', 1)}x")

                st.markdown("**Reasons**")
                for r in result.get("reasons", [])[:5]:
                    st.write("•", r)

                st.markdown("**Risks**")
                for r in result.get("risks", [])[:5]:
                    st.write("•", r)

                if result.get("invalidation"):
                    st.info(f"Invalidation: {result['invalidation']}")

            with col2:
                st.subheader("🧠 Analysts")
                analysts = result.get("agents_summary", {}).get("analysts", [])
                for a in analysts:
                    st.write(f"**{a.get('role', '?')}**")
                    st.caption(f"{a.get('bias', '?')} ({a.get('confidence', 0):.2f})")

            with st.expander("📊 Full Analysis (JSON)"):
                st.json(result)

            # Discord alert
            if send_discord:
                try:
                    from future_admiral_v7.alerts.discord import send_discord_embed
                    ok = send_discord_embed(result)
                    if ok:
                        st.success("✅ Discord pe signal bhej diya")
                    else:
                        st.warning("⚠️ Discord webhook config missing (.env check karo)")
                except Exception as e:
                    st.warning(f"Discord error: {e}")

        except Exception as e:
            status.update(label="❌ Fail", state="error", expanded=True)
            st.error(f"**{type(e).__name__}**: {e}")
            st.subheader("Full Traceback")
            st.code(traceback.format_exc(), language="python")
