"""
UI Components and Visualizations for TradingAgents Streamlit Integration.
Includes Conviction Radar Chart, Debate Speech Cards, and Specialist Sub-Tabs.
"""

from typing import Dict, Any, List, Optional
import streamlit as st
import plotly.graph_objects as go
from .graph.trading_graph import TradingAgentsGraph
from .default_config import DEFAULT_CONFIG, AVAILABLE_PROVIDERS


def create_radar_chart(radar_scores: Dict[str, float], ticker: str = "") -> go.Figure:
    """
    Creates an interactive 5-axis Plotly Spider/Radar chart for multi-agent conviction dimensions.
    Axes: Fundamentals, Technical Momentum, Valuation, Sentiment, Risk Quality.
    """
    categories = ["Fundamentals", "Technical Momentum", "Valuation", "Sentiment", "Risk Quality"]
    
    # Extract values in fixed order with fallback
    values = [radar_scores.get(c, 50.0) for c in categories]
    
    # Close the radar polygon by appending the first item at the end
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()

    # Benchmark neutral line (50 score)
    fig.add_trace(go.Scatterpolar(
        r=[50, 50, 50, 50, 50, 50],
        theta=categories_closed,
        mode='lines',
        name='Neutral Benchmark (50)',
        line=dict(color='rgba(150, 150, 150, 0.4)', dash='dash', width=1.5),
        hoverinfo='skip'
    ))

    # Ticker Conviction polygon
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill='toself',
        name=f'{ticker} Multi-Agent Conviction',
        fillcolor='rgba(38, 166, 154, 0.35)',
        line=dict(color='#26a69a', width=3),
        marker=dict(size=8, color='#00e676', symbol='circle')
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickvals=[20, 40, 60, 80, 100],
                ticktext=["20", "40", "60", "80", "100"],
                gridcolor="rgba(128, 128, 128, 0.25)",
                linecolor="rgba(128, 128, 128, 0.25)",
                angle=90
            ),
            angularaxis=dict(
                gridcolor="rgba(128, 128, 128, 0.25)",
                linecolor="rgba(128, 128, 128, 0.25)",
                rotation=90,
                direction="clockwise"
            ),
            bgcolor="rgba(0,0,0,0)"
        ),
        showlegend=False,
        height=380,
        margin=dict(l=30, r=30, t=30, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return fig


def render_tradingagents_desk(watchlist: List[str]):
    """
    Renders the full TradingAgents Multi-Agent Desk interface in Streamlit.
    """
    st.subheader("🤖 TradingAgents Multi-Agent Deliberation Desk")
    st.markdown(
        "Institutional AI Investment Committee featuring **Specialist Intelligence Analysts**, "
        "adversarial **Bull vs. Bear Dialectical Debate**, quantitative **Risk Management**, and an "
        "autonomous **Portfolio Manager Executive Verdict**."
    )

    # Initialize session state storage
    if "ta_results" not in st.session_state:
        st.session_state["ta_results"] = {}
    if "selected_ta_ticker" not in st.session_state:
        st.session_state["selected_ta_ticker"] = watchlist[0] if watchlist else "NVDA"

    # Top Control Panel
    with st.container(border=True):
        c1, c2, c3 = st.columns([2.5, 2, 2.5])
        
        with c1:
            # Check if user selected from other tab
            curr_selected = st.session_state.get("selected_ta_ticker", watchlist[0] if watchlist else "NVDA")
            
            target_ticker = st.text_input(
                "🎯 Enter Target Asset Ticker",
                value=curr_selected,
                help="Type any ticker symbol to analyze (e.g., AAPL, TSLA, NVDA)"
            ).strip().upper()
                
            st.session_state["selected_ta_ticker"] = target_ticker

        with c2:
            debate_rounds = st.slider(
                "⚔️ Bull vs. Bear Debate Rounds",
                min_value=1,
                max_value=3,
                value=2,
                help="Number of adversarial cross-examination turns between Bull and Bear researchers"
            )

        with c3:
            st.markdown("<br>", unsafe_allow_html=True)
            run_button = st.button(
                "⚡ Run Multi-Agent Analysis",
                type="primary",
                use_container_width=True,
                help="Triggers full multi-agent committee deliberation and risk stress test"
            )

        # Advanced Settings Accordion
        with st.expander("⚙️ LLM Provider & Execution Engine Settings", expanded=False):
            sc1, sc2 = st.columns(2)
            with sc1:
                provider_names = [p["name"] for p in AVAILABLE_PROVIDERS]
                selected_provider_name = st.selectbox("AI Engine Provider", provider_names, index=0)
                selected_provider_id = next(p["id"] for p in AVAILABLE_PROVIDERS if p["name"] == selected_provider_name)
            
            with sc2:
                if selected_provider_id in ["openai", "anthropic", "gemini"]:
                    api_key_input = st.text_input(
                        f"{selected_provider_name.split()[0]} API Key (Optional)",
                        type="password",
                        help="Enter API key for live LLM reasoning, or leave blank to use Quant Heuristic mode."
                    )
                else:
                    api_key_input = None
                    st.info("💡 Deterministic Quant Engine runs instantly with zero API keys required.")

            st.caption("🛡️ **Zero-Failure Fallback Guarantee:** If an external LLM key is absent or hits rate limits, TradingAgents automatically falls back to the high-fidelity deterministic quant engine using live market data.")

    # Execution Handler
    if run_button or (target_ticker not in st.session_state["ta_results"] and run_button):
        with st.status(f"🤖 Assembling AI Investment Committee for **{target_ticker}**...", expanded=True) as status:
            st.write(f"📊 **Step 1/5:** Ingesting live market data, OHLCV history, fundamental balance sheets & news...")
            
            # Configure Graph
            graph_config = {
                "debate_rounds": debate_rounds,
                "llm_provider": selected_provider_id,
                "api_key": api_key_input,
            }
            graph = TradingAgentsGraph(config=graph_config)
            
            st.write("🧠 **Step 2/5:** Specialist Analysts evaluating Fundamentals, Technical Momentum & Sentiment...")
            
            st.write("⚔️ **Step 3/5:** Bull & Bear Researchers conducting adversarial multi-round debate...")
            
            st.write("🛡️ **Step 4/5:** Risk Manager calculating volatility-adjusted sizing, VaR, and dynamic stop-loss...")
            
            state, decision = graph.propagate(target_ticker, config=graph_config)
            
            st.write("🏛️ **Step 5/5:** Portfolio Manager synthesizing Executive Consensus Verdict...")
            
            # Cache results in session state
            st.session_state["ta_results"][target_ticker] = {
                "state": state,
                "decision": decision
            }
            status.update(label=f"✅ Multi-Agent Deliberation Complete for {target_ticker}!", state="complete", expanded=False)

    # Render Results if Available
    if target_ticker in st.session_state["ta_results"]:
        result_bundle = st.session_state["ta_results"][target_ticker]
        state = result_bundle["state"]
        decision = result_bundle["decision"]
        
        profile = state.get("profile", {})
        fund = state.get("fundamentals", {})
        tech = state.get("technicals", {})
        sent = state.get("sentiment", {})
        debate = state.get("debate", [])
        risk = state.get("risk", {})

        st.markdown("---")

        # 1. Executive Consensus Cockpit Banner
        verdict = decision.get("verdict", "HOLD")
        badge = decision.get("verdict_badge", "🟡 HOLD")
        color = decision.get("verdict_color", "#F57F17")
        conviction = decision.get("conviction_score", 50)
        target_price = decision.get("target_price", 0.0)
        target_upside = decision.get("target_upside_pct", 0.0)
        stop_loss = decision.get("stop_loss", 0.0)
        stop_loss_pct = decision.get("stop_loss_pct", -8.0)
        pos_size = decision.get("position_size_pct", 10.0)
        risk_tier = decision.get("risk_tier", "MEDIUM RISK")
        current_price = tech.get("current_price", 100.0)

        # Verdict Header
        st.markdown(
            f"""
            <div style="background: linear-gradient(90deg, rgba(20,25,35,0.95), rgba(30,40,60,0.95)); 
                        border-left: 6px solid {color}; border-radius: 8px; padding: 18px; margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                    <div>
                        <span style="font-size: 1.1rem; color: #90caf9; font-weight: 600;">EXECUTIVE COMMITTEE CONSENSUS VERDICT</span>
                        <h1 style="margin: 4px 0 0 0; color: {color}; font-size: 2.2rem;">{badge}</h1>
                        <span style="color: #b0bec5; font-size: 0.95rem;">{profile.get('name', target_ticker)} ({target_ticker}) • Current Price: <strong>${current_price}</strong></span>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 0.9rem; color: #b0bec5;">CONVICTION SCORE</span>
                        <h2 style="margin: 0; color: #ffffff; font-size: 2rem;">{conviction}<span style="font-size: 1.1rem; color: #90caf9;"> / 100</span></h2>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 5 Key KPI Metric Cards
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        with kpi1:
            kpi1.metric(
                label="Conviction Score",
                value=f"{conviction}/100",
                delta=f"{'+' if conviction >= 50 else ''}{conviction - 50} pts vs base"
            )
        with kpi2:
            direction = "Upside" if target_upside >= 0 else "Downside"
            # For a SELL verdict, a lower price target is the goal, so we invert the delta color
            d_color = "inverse" if "SELL" in verdict else "normal"
            kpi2.metric(
                label="12M Target Price",
                value=f"${target_price}",
                delta=f"{abs(target_upside)}% Implied {direction}",
                delta_color=d_color
            )
        with kpi3:
            kpi3.metric(
                label="Dynamic Stop-Loss",
                value=f"${stop_loss}",
                delta=f"{abs(stop_loss_pct)}% Exit Risk",
                delta_color="inverse"
            )
        with kpi4:
            kpi4.metric(
                label="Recommended Sizing",
                value=f"{pos_size}%",
                help="Volatility-adjusted allocation recommendation based on fractional Kelly risk-parity"
            )
        with kpi5:
            kpi5.metric(
                label="Risk Tier",
                value=risk_tier.replace(" RISK", ""),
                delta=risk.get("risk_badge", "🟡")
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Cockpit Body: Conviction Radar Chart & Executive Narrative
        rc1, rc2 = st.columns([5, 5])
        
        with rc1:
            st.markdown("#### 🕸️ 5-Axis Conviction Radar")
            radar_fig = create_radar_chart(decision.get("radar_scores", {}), target_ticker)
            st.plotly_chart(radar_fig, use_container_width=True)

        with rc2:
            st.markdown("#### 📜 Executive Committee Synthesis")
            st.markdown(decision.get("executive_summary", "Synthesis unavailable."))

        st.markdown("<br>", unsafe_allow_html=True)

        # 2. Dialectical Bull vs. Bear Debate Arena
        st.markdown("### ⚔️ Dialectical Bull vs. Bear Debate Arena")
        st.markdown("Structured adversarial cross-examination between Bull Researcher and Bear Researcher.")

        # Debate Rounds Tabbed or Sequential Display
        if debate:
            # Group by rounds
            rounds_dict = {}
            for turn in debate:
                r_num = turn.get("round", 1)
                if r_num not in rounds_dict:
                    rounds_dict[r_num] = []
                rounds_dict[r_num].append(turn)

            round_tab_labels = [f"Round {r}: {'Initial Theses' if r==1 else 'Cross-Examination Rebuttals' if r==2 else 'Final Arguments'}" for r in rounds_dict.keys()]
            
            # Fix nested tabs Streamlit bug by using radio button
            selected_round_label = st.radio("Select Debate Round", round_tab_labels, horizontal=True, label_visibility="collapsed")
            selected_idx = round_tab_labels.index(selected_round_label)
            r_num = list(rounds_dict.keys())[selected_idx]

            for turn in rounds_dict[r_num]:
                        speaker = turn.get("speaker", "Researcher")
                        avatar = turn.get("avatar", "🗣️")
                        dialogue = turn.get("dialogue", "")
                        
                        if "Bull" in speaker:
                            st.markdown(
                                f"""
                                <div style="background-color: rgba(38, 166, 154, 0.12); border-left: 5px solid #26a69a; 
                                            border-radius: 8px; padding: 14px; margin: 10px 0;">
                                    <div style="font-weight: 700; color: #26a69a; margin-bottom: 6px;">
                                        {avatar} {speaker} — Target: ${turn.get('upside_target_price', target_price)} (+{turn.get('upside_potential_pct', 0)}%) | Conviction: {turn.get('conviction', 75)}%
                                    </div>
                                    <div style="color: #eceff1; line-height: 1.5;">{dialogue}</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(
                                f"""
                                <div style="background-color: rgba(239, 83, 80, 0.12); border-left: 5px solid #ef5350; 
                                            border-radius: 8px; padding: 14px; margin: 10px 0;">
                                    <div style="font-weight: 700; color: #ef5350; margin-bottom: 6px;">
                                        {avatar} {speaker} — Downside: ${turn.get('downside_target_price', stop_loss)} ({turn.get('downside_potential_pct', 0)}%) | Skepticism: {turn.get('conviction', 70)}%
                                    </div>
                                    <div style="color: #eceff1; line-height: 1.5;">{dialogue}</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

            # Key Points of Contention Comparison Matrix
            with st.expander("🔍 View Key Points of Contention Matrix", expanded=False):
                cm1, cm2 = st.columns(2)
                with cm1:
                    st.markdown("#### 🐂 Bull Growth Catalysts")
                    bull_turns = [t for t in debate if "Bull" in t.get("speaker", "")]
                    if bull_turns and "catalysts" in bull_turns[0]:
                        for cat in bull_turns[0]["catalysts"]:
                            st.markdown(f"- 🟢 {cat}")
                    else:
                        st.write("Robust cash flow and competitive market positioning.")
                with cm2:
                    st.markdown("#### 🐻 Bear Downside Vulnerabilities")
                    bear_turns = [t for t in debate if "Bear" in t.get("speaker", "")]
                    if bear_turns and "risks" in bear_turns[0]:
                        for rsk in bear_turns[0]["risks"]:
                            st.markdown(f"- 🔴 {rsk}")
                    else:
                        st.write("Valuation multiples and macroeconomic sensitivity.")

        st.markdown("<br>", unsafe_allow_html=True)

        # 3. Specialist Agent Deep-Dive Sub-Tabs
        st.markdown("### 🔬 Specialist Intelligence Deep-Dives")
        
        deep_dive_options = ["📊 Fundamental Analysis", "📈 Technical Analysis", "📰 Sentiment & News", "🛡️ Risk & Volatility"]
        selected_deep_dive = st.radio("Select Deep-Dive Report", deep_dive_options, horizontal=True, label_visibility="collapsed")
        
        if selected_deep_dive == "📊 Fundamental Analysis":
            st.markdown(fund.get("report_markdown", "No fundamental report generated."))
        elif selected_deep_dive == "📈 Technical Analysis":
            st.markdown(tech.get("report_markdown", "No technical report generated."))
        elif selected_deep_dive == "📰 Sentiment & News":
            st.markdown(sent.get("report_markdown", "No sentiment report generated."))
        elif selected_deep_dive == "🛡️ Risk & Volatility":
            st.markdown(risk.get("report_markdown", "No risk report generated."))

    else:
        st.info("👆 Click **'⚡ Run Multi-Agent Analysis'** above to convene the AI Investment Committee and generate deep multi-agent insights.")
