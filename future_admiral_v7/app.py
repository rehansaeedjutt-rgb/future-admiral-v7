from __future__ import annotations

import streamlit as st

from future_admiral_v7.alerts.discord import send_discord_embed
from future_admiral_v7.debate.engine import run_debate
from future_admiral_v7.exporter.dossier import save_dossier


st.set_page_config(page_title="Future Admiral v7", layout="wide")
st.title("👑 Future Admiral v7 — Institutional Desk")
st.caption("Multi-Agent Debate · Multi-Timeframe · Free Stack · Ollama + ccxt + yfinance")

with st.sidebar:
    st.header("Config")
    symbol = st.text_input("Symbol (BTC/USDT, ETH/USDT, AAPL)", value="BTC/USDT")
    tf = st.selectbox("Primary Timeframe", ["1m", "5m", "15m", "1h", "4h", "1d"], index=2)
    send_alert = st.checkbox("Discord alert bhejo", value=False)
    run = st.button("🚀 Run Full Debate", use_container_width=True, type="primary")

if run and symbol:
    with st.status("Full multi-agent debate chal raha hai...", expanded=True) as status:
        try:
            result = run_debate(symbol, tf, ui=status)
            status.update(label="✅ Debate mukammal", state="complete", expanded=False)

            col1, col2 = st.columns([2, 1])
            with col1:
                st.subheader("🎯 Final Signal")
                bias_color = {"long": "green", "short": "red", "neutral": "gray"}[result["bias"]]
                st.markdown(f"### :{bias_color}[{result['bias'].upper()}] · {result['symbol']} · {result['timeframe']}")
                st.metric("Confidence", f"{result['confidence'] * 100:.0f}%")
                c1, c2, c3 = st.columns(3)
                c1.metric("Entry", result.get("entry"))
                c2.metric("Stop Loss", result.get("stop_loss"))
                c3.metric("R:R", result.get("risk_reward"))
                st.write("**Take Profit:**", result.get("take_profit"))
                st.write("**Size:**", f"{result.get('position_size_pct')}% · Lev {result.get('leverage')}x")

                st.markdown("**Reasons**")
                for item in result.get("reasons", []):
                    st.write("•", item)
                st.markdown("**Risks**")
                for item in result.get("risks", []):
                    st.write("•", item)
                st.info(f"Invalidation: {result.get('invalidation', '-')}")

            with col2:
                st.subheader("🧠 Agents")
                for agent in result.get("agents_summary", {}).get("analysts", []):
                    st.write(f"**{agent['role']}** — {agent['bias']} ({agent['confidence']:.2f})")

            with st.expander("Bull vs Bear Debate"):
                st.json(result.get("agents_summary", {}))

            with st.expander("Raw Context"):
                st.json(result.get("agents_summary", {}).get("context", {}))

            path = save_dossier(result)
            st.success(f"Dossier saved: {path}")

            if send_alert:
                ok = send_discord_embed(result)
                st.info("✅ Discord pe signal bhej diya" if ok else "❌ Discord webhook config missing — .env check karo")
        except Exception as exc:  # pragma: no cover
            import traceback
            st.error(f"❌ ERROR: {type(exc).__name__}: {exc}")
            st.code(traceback.format_exc(), language="python")
            status.update(label="❌ Fail", state="error")
            st.stop()
        except Exception as e:
            import traceback
            st.error(f"❌ {type(e).__name__}: {e}")
            st.code(traceback.format_exc(), language="python")
            status.update(label="❌ Fail", state="error")
            st.stop()