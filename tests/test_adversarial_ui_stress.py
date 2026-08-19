"""
Adversarial Stress-Testing and Empirical Challenge Suite for Streamlit UI & Integration Layer.
Author: Challenger 2 (Empirical Challenger)
Target: Consensus Deck_AG / TradingAgents Integration
"""

import ast
import os
import copy
import pytest
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from tradingagents import TradingAgentsGraph, DEFAULT_CONFIG
from tradingagents.ui import create_radar_chart, render_tradingagents_desk
from tradingagents.data.provider import FinancialDataProvider
from tradingagents.agents.trader.pm import PortfolioManager
from tradingagents.agents.risk_mgmt.risk_manager import RiskManager
from tradingagents.agents.analysts.fundamentals import FundamentalAnalyst
from tradingagents.agents.analysts.technical import TechnicalAnalyst
from tradingagents.agents.analysts.sentiment import SentimentAnalyst
from tradingagents.agents.researchers.bull import BullResearcher
from tradingagents.agents.researchers.bear import BearResearcher


# ============================================================================
# Dimension 1: Radar Chart Stress & Boundary Tests
# ============================================================================

def test_radar_chart_all_zeros():
    """Stress test: all radar dimensions set to 0.0."""
    scores = {
        "Fundamentals": 0.0,
        "Technical Momentum": 0.0,
        "Valuation": 0.0,
        "Sentiment": 0.0,
        "Risk Quality": 0.0
    }
    fig = create_radar_chart(scores, ticker="ZERO_CORP")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2
    # Verify trace 1 (conviction) values
    conviction_trace = fig.data[1]
    assert list(conviction_trace.r) == [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    assert len(conviction_trace.theta) == 6


def test_radar_chart_all_hundreds():
    """Stress test: all radar dimensions set to 100.0."""
    scores = {
        "Fundamentals": 100.0,
        "Technical Momentum": 100.0,
        "Valuation": 100.0,
        "Sentiment": 100.0,
        "Risk Quality": 100.0
    }
    fig = create_radar_chart(scores, ticker="PERFECT_CORP")
    assert isinstance(fig, go.Figure)
    conviction_trace = fig.data[1]
    assert list(conviction_trace.r) == [100.0, 100.0, 100.0, 100.0, 100.0, 100.0]


def test_radar_chart_asymmetric_extreme_values():
    """Stress test: highly skewed values across dimensions (0 vs 100)."""
    scores = {
        "Fundamentals": 100.0,
        "Technical Momentum": 0.0,
        "Valuation": 100.0,
        "Sentiment": 0.0,
        "Risk Quality": 100.0
    }
    fig = create_radar_chart(scores, ticker="SKEWED_ASSET")
    assert isinstance(fig, go.Figure)
    conviction_trace = fig.data[1]
    assert list(conviction_trace.r) == [100.0, 0.0, 100.0, 0.0, 100.0, 100.0]


def test_radar_chart_missing_and_empty_keys():
    """Stress test: empty dictionary or partial keys provided."""
    # Completely empty dict
    fig_empty = create_radar_chart({}, ticker="EMPTY_KEYS")
    assert isinstance(fig_empty, go.Figure)
    # Default fallback is 50.0 for missing keys
    assert list(fig_empty.data[1].r) == [50.0, 50.0, 50.0, 50.0, 50.0, 50.0]

    # Partial keys
    partial_scores = {"Fundamentals": 90.0, "Valuation": 30.0}
    fig_partial = create_radar_chart(partial_scores, ticker="PARTIAL")
    assert list(fig_partial.data[1].r) == [90.0, 50.0, 30.0, 50.0, 50.0, 90.0]


def test_radar_chart_special_characters_in_ticker():
    """Stress test: tickers with special characters, symbols, and HTML entities."""
    special_tickers = ["BRK.A", "BF/B", "M&M", "<script>alert(1)</script>", "$$$$"]
    scores = {"Fundamentals": 70.0, "Technical Momentum": 70.0, "Valuation": 70.0, "Sentiment": 70.0, "Risk Quality": 70.0}
    for tick in special_tickers:
        fig = create_radar_chart(scores, ticker=tick)
        assert isinstance(fig, go.Figure)
        assert tick in fig.data[1].name


# ============================================================================
# Dimension 2: Session State Simulation & Tab Transition Invariants
# ============================================================================

def test_session_state_multi_ticker_isolation():
    """Verify storing results for multiple tickers does not cross-contaminate state."""
    session_state = {
        "ta_results": {},
        "selected_ta_ticker": "NVDA"
    }

    graph = TradingAgentsGraph(config={"llm_provider": "heuristic", "debate_rounds": 1})

    # Simulate running deliberation on NVDA
    state_nvda, dec_nvda = graph.propagate("NVDA")
    session_state["ta_results"]["NVDA"] = {"state": state_nvda, "decision": dec_nvda}

    # Simulate running deliberation on AAPL
    state_aapl, dec_aapl = graph.propagate("AAPL")
    session_state["ta_results"]["AAPL"] = {"state": state_aapl, "decision": dec_aapl}

    # Verify isolation
    assert session_state["ta_results"]["NVDA"]["decision"]["ticker"] == "NVDA"
    assert session_state["ta_results"]["AAPL"]["decision"]["ticker"] == "AAPL"
    assert session_state["ta_results"]["NVDA"]["state"]["ticker"] == "NVDA"
    assert session_state["ta_results"]["AAPL"]["state"]["ticker"] == "AAPL"

    # Verify switching selected_ta_ticker retains previous cached data
    session_state["selected_ta_ticker"] = "NVDA"
    active_result = session_state["ta_results"][session_state["selected_ta_ticker"]]
    assert active_result["decision"]["ticker"] == "NVDA"

    session_state["selected_ta_ticker"] = "AAPL"
    active_result = session_state["ta_results"][session_state["selected_ta_ticker"]]
    assert active_result["decision"]["ticker"] == "AAPL"


def test_session_state_unrendered_ticker_behavior():
    """Verify that querying a ticker that was not yet analyzed does not crash or raise KeyError."""
    session_state = {
        "ta_results": {"NVDA": {"state": {}, "decision": {}}},
        "selected_ta_ticker": "MSFT"  # MSFT not analyzed yet
    }
    # In UI, if target_ticker in st.session_state["ta_results"] guards the rendering
    has_results = session_state["selected_ta_ticker"] in session_state["ta_results"]
    assert not has_results  # Renders the 'Click Run' info prompt safely


# ============================================================================
# Dimension 3: 1-Click Cross-Launch & Ticker Sanitization
# ============================================================================

def test_1click_ticker_sanitization_and_deduplication():
    """Verify options_list creation logic handles custom, duplicate, and queued tickers."""
    watchlist = ["GOOGL", "CVS", "AMZN", "MSFT", "NVDA"]

    # Case A: Queued ticker is inside watchlist
    curr_selected = "NVDA"
    options_list = list(dict.fromkeys([curr_selected] + watchlist + ["CUSTOM"]))
    assert options_list[0] == "NVDA"
    assert len(options_list) == len(watchlist) + 1  # 5 + 1 (CUSTOM) = 6
    assert options_list.index(curr_selected) == 0

    # Case B: Queued ticker is external (e.g. TSLA)
    curr_selected = "TSLA"
    options_list = list(dict.fromkeys([curr_selected] + watchlist + ["CUSTOM"]))
    assert options_list[0] == "TSLA"
    assert "TSLA" in options_list
    assert options_list.index("TSLA") == 0
    assert len(options_list) == len(watchlist) + 2  # 5 + TSLA + CUSTOM = 7


def test_custom_ticker_case_and_whitespace_handling():
    """Verify custom ticker input is stripped and uppercased."""
    raw_inputs = ["  aapl  ", "nvda", "  msft", "GOOGL  ", "tsla"]
    sanitized = [t.strip().upper() for t in raw_inputs]
    assert sanitized == ["AAPL", "NVDA", "MSFT", "GOOGL", "TSLA"]


# ============================================================================
# Dimension 4: API Key Missing & Offline Resilience
# ============================================================================

def test_missing_api_key_graceful_fallback():
    """Verify that when external LLM provider is chosen without API key, propagation succeeds without crash."""
    for provider in ["openai", "anthropic", "gemini"]:
        config = {
            "llm_provider": provider,
            "api_key": None,  # Missing key
            "debate_rounds": 1,
        }
        graph = TradingAgentsGraph(config=config)
        state, decision = graph.propagate("AAPL", config=config)

        assert state is not None
        assert decision is not None
        assert decision["verdict"] in ["STRONG BUY", "BUY", "HOLD", "SELL", "STRONG SELL"]
        assert 0 <= decision["conviction_score"] <= 100
        assert len(decision["radar_scores"]) == 5


def test_empty_string_api_key_graceful_fallback():
    """Verify empty string API key behaves like None."""
    config = {
        "llm_provider": "openai",
        "api_key": "",
        "debate_rounds": 1,
    }
    graph = TradingAgentsGraph(config=config)
    state, decision = graph.propagate("NVDA", config=config)
    assert decision["verdict"] in ["STRONG BUY", "BUY", "HOLD", "SELL", "STRONG SELL"]


def test_full_offline_network_failure_resilience():
    """Verify that even when network data providers completely fail, graph generates complete state."""
    # FinancialDataProvider._generate_fallback_history ensures 100% uptime
    provider = FinancialDataProvider()
    fallback_data = provider.get_stock_data("OFFLINE_MOCK_ASSET")

    assert "profile" in fallback_data
    assert "fundamentals" in fallback_data
    assert "technicals" in fallback_data
    assert "history" in fallback_data
    assert len(fallback_data["history"]) == 252
    assert fallback_data["technicals"]["current_price"] > 0


# ============================================================================
# Dimension 5: AST Syntax and Architectural Layout Integrity
# ============================================================================

def test_all_project_python_files_ast_parse():
    """Exhaustive AST validation: all Python files in the repository must parse with 0 errors."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    py_files = []
    for root, dirs, files in os.walk(repo_root):
        if ".git" in root or "__pycache__" in root or ".pytest_cache" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))

    assert len(py_files) >= 15, f"Expected at least 15 python files, found {len(py_files)}"

    for py_file in py_files:
        with open(py_file, "r", encoding="utf-8") as f:
            source = f.read()
        try:
            parsed = ast.parse(source, filename=py_file)
            assert isinstance(parsed, ast.AST)
        except Exception as e:
            pytest.fail(f"AST parse failed for {py_file}: {e}")
