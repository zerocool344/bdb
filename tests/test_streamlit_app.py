"""
Streamlit application and UI integration test suite.
Validates Tier 4 requirements according to TEST_INFRA.md and PROJECT.md contracts.
"""

import ast
import os
import pytest
import plotly.graph_objects as go
from tradingagents.ui import create_radar_chart, render_tradingagents_desk
from tradingagents import TradingAgentsGraph


def test_app_ast_syntax():
    """Verify that app.py parses completely without Python syntax or indentation errors."""
    app_path = os.path.join(os.path.dirname(__file__), "..", "app.py")
    assert os.path.exists(app_path), f"app.py not found at {app_path}"

    with open(app_path, "r", encoding="utf-8") as f:
        source = f.read()

    # ast.parse will raise SyntaxError if invalid
    parsed = ast.parse(source)
    assert isinstance(parsed, ast.AST)


def test_all_seven_tabs_defined_in_app():
    """Verify that app.py defines all 7 required tabs including TradingAgents Desk."""
    app_path = os.path.join(os.path.dirname(__file__), "..", "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        source = f.read()

    expected_tab_strings = [
        "Live Overview (Consensus)",
        "🤖 TradingAgents Desk",
        "Interactive Stock Insights",
        "🧬 Deep Insights",
        "🇺🇸 Pelosi Tracker",
        "📈 ETF Benchmarks",
        "📚 Master Lists"
    ]

    for tab_str in expected_tab_strings:
        assert tab_str in source, f"Tab '{tab_str}' was not found in app.py"


def test_tradingagents_imports_in_app():
    """Verify that app.py imports TradingAgents framework components."""
    app_path = os.path.join(os.path.dirname(__file__), "..", "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        source = f.read()

    assert "from tradingagents import TradingAgentsGraph" in source
    assert "from tradingagents.ui import render_tradingagents_desk" in source
    assert "render_tradingagents_desk(WATCHLIST)" in source


def test_radar_chart_generation():
    """Verify create_radar_chart produces a valid Plotly Figure with 5 axes and 2 traces."""
    sample_scores = {
        "Fundamentals": 85.0,
        "Technical Momentum": 78.0,
        "Valuation": 62.0,
        "Sentiment": 74.0,
        "Risk Quality": 80.0
    }
    fig = create_radar_chart(sample_scores, ticker="NVDA")

    assert isinstance(fig, go.Figure)
    # Check traces: trace 0 is benchmark (50), trace 1 is NVDA conviction
    assert len(fig.data) == 2
    assert fig.data[0].name == "Neutral Benchmark (50)"
    assert "NVDA" in fig.data[1].name
    assert fig.layout.polar.radialaxis.range == (0, 100) or list(fig.layout.polar.radialaxis.range) == [0, 100]


def test_1click_launch_mechanisms_in_app():
    """Verify that 1-click launch buttons are wired to selected_ta_ticker in session state."""
    app_path = os.path.join(os.path.dirname(__file__), "..", "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        source = f.read()

    assert 'st.session_state["selected_ta_ticker"]' in source
    assert "btn_quick_launch_tab1" in source
    assert "btn_ta_tab2_" in source


def test_offline_ui_deliberation_contract():
    """Verify that TradingAgents UI components can execute end-to-end data pipeline."""
    graph = TradingAgentsGraph(config={"llm_provider": "heuristic", "debate_rounds": 1})
    state, decision = graph.propagate("AAPL")

    assert decision["verdict"] in ["STRONG BUY", "BUY", "HOLD", "SELL", "STRONG SELL"]
    radar_fig = create_radar_chart(decision["radar_scores"], ticker="AAPL")
    assert isinstance(radar_fig, go.Figure)
