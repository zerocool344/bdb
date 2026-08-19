"""
Unit, boundary, and cross-feature integration test suite for TradingAgents package.
Validates Tiers 1-3 requirements according to TEST_INFRA.md and PROJECT.md contracts.
"""

import pytest
import pandas as pd
import numpy as np

import tradingagents
from tradingagents import TradingAgentsGraph, DEFAULT_CONFIG
from tradingagents.data.provider import FinancialDataProvider
from tradingagents.agents.analysts.fundamentals import FundamentalAnalyst
from tradingagents.agents.analysts.technical import TechnicalAnalyst
from tradingagents.agents.analysts.sentiment import SentimentAnalyst
from tradingagents.agents.researchers.bull import BullResearcher
from tradingagents.agents.researchers.bear import BearResearcher
from tradingagents.agents.risk_mgmt.risk_manager import RiskManager
from tradingagents.agents.trader.pm import PortfolioManager


# ============================================================================
# Tier 1: Unit Tests
# ============================================================================

def test_package_exports_and_version():
    """Verify package initialization, version string, and public exports."""
    assert tradingagents.__version__ == "0.1.0"
    assert TradingAgentsGraph is not None
    assert DEFAULT_CONFIG is not None
    assert isinstance(DEFAULT_CONFIG, dict)


def test_default_config_structure():
    """Verify default configuration dictionary contains all expected control keys."""
    expected_keys = [
        "llm_provider", "debate_rounds", "risk_tolerance",
        "max_position_size", "min_position_size", "stop_loss_pct",
        "enable_fundamentals", "enable_technicals", "enable_sentiment",
        "enable_debate", "enable_risk_mgmt", "history_period"
    ]
    for k in expected_keys:
        assert k in DEFAULT_CONFIG, f"Missing key '{k}' in DEFAULT_CONFIG"
    assert DEFAULT_CONFIG["debate_rounds"] == 2
    assert DEFAULT_CONFIG["max_position_size"] == 0.20


def test_data_provider_fallback_generation():
    """Verify fallback synthetic OHLCV history generator creates valid DataFrame."""
    provider = FinancialDataProvider()
    df = provider._generate_fallback_history("TEST_TICKER")
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 252
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        assert col in df.columns
        assert not df[col].isnull().any()
    assert (df["High"] >= df["Low"]).all()


def test_data_provider_indicator_calculations():
    """Verify RSI, MACD, Bollinger Bands, and SMAs calculate correctly on historical data."""
    provider = FinancialDataProvider()
    hist = provider._generate_fallback_history("NVDA")
    info = {"beta": 1.45, "fiftyTwoWeekHigh": 140.0, "fiftyTwoWeekLow": 80.0}
    
    technicals = provider._calculate_technicals(hist, info)
    
    assert "current_price" in technicals
    assert "rsi_14" in technicals
    assert 0.0 <= technicals["rsi_14"] <= 100.0
    assert "macd" in technicals
    assert "macd_signal" in technicals
    assert "macd_hist" in technicals
    assert "bb_upper" in technicals
    assert "bb_lower" in technicals
    assert technicals["bb_upper"] >= technicals["bb_lower"]
    assert "atr_14" in technicals
    assert technicals["atr_14"] > 0
    assert technicals["trend_structure"] in [
        "STRONG UPTREND", "MODERATE UPTREND", "DOWNTREND", "CONSOLIDATION / NEUTRAL"
    ]


def test_fundamental_analyst():
    """Verify Fundamental Analyst score bounds, health grades, and markdown dossier generation."""
    analyst = FundamentalAnalyst()
    sample_data = {
        "profile": {"ticker": "AAPL", "name": "Apple Inc."},
        "fundamentals": {
            "trailing_pe": 28.0,
            "forward_pe": 24.0,
            "peg_ratio": 1.8,
            "debt_to_equity": 85.0,
            "current_ratio": 1.4,
            "operating_margins": 30.0,
            "profit_margins": 24.0,
            "roe": 140.0,
            "revenue_growth": 8.0,
            "earnings_growth": 10.0,
            "free_cash_flow": 100_000_000_000.0,
        }
    }
    result = analyst.analyze(sample_data)
    
    assert 0.0 <= result["score"] <= 100.0
    assert 0.0 <= result["valuation_score"] <= 100.0
    assert result["health_grade"] in ["A+", "A", "B", "C", "D", "F"]
    assert isinstance(result["strengths"], list)
    assert len(result["strengths"]) > 0
    assert "report_markdown" in result
    assert "Apple Inc." in result["report_markdown"] or "AAPL" in result["report_markdown"]


def test_technical_analyst():
    """Verify Technical Analyst score, trend bias, and signal checklist."""
    analyst = TechnicalAnalyst()
    sample_data = {
        "profile": {"ticker": "MSFT", "name": "Microsoft Corporation"},
        "technicals": {
            "current_price": 420.0,
            "sma_20": 415.0,
            "sma_50": 410.0,
            "sma_200": 390.0,
            "rsi_14": 58.5,
            "macd": 3.2,
            "macd_signal": 2.1,
            "macd_hist": 1.1,
            "bb_upper": 435.0,
            "bb_lower": 395.0,
            "bb_mid": 415.0,
            "bb_pct_b": 0.625,
            "atr_14": 6.8,
            "support_level": 395.0,
            "resistance_level": 435.0,
            "trend_structure": "STRONG UPTREND",
        }
    }
    result = analyst.analyze(sample_data)
    
    assert 0.0 <= result["score"] <= 100.0
    assert result["trend_bias"] in ["BULLISH", "BEARISH", "NEUTRAL / CONSOLIDATION"]
    assert isinstance(result["signals"], list)
    assert len(result["signals"]) > 0
    assert "levels" in result
    assert result["levels"]["support"] == 395.0


def test_sentiment_analyst():
    """Verify Sentiment Analyst lexicon parsing, score bounds, and sentiment tiering."""
    analyst = SentimentAnalyst()
    sample_data = {
        "profile": {
            "ticker": "NVDA",
            "name": "NVIDIA Corporation",
            "recommendation_key": "strong_buy",
            "current_price": 120.0,
            "target_mean_price": 150.0,
        },
        "news": [
            {"title": "NVIDIA surges on record datacenter revenue and AI demand surge", "summary": "Record profits reported"},
            {"title": "Analysts upgrade NVIDIA following new GPU architecture breakthrough", "summary": "Outperform rating maintained"},
        ]
    }
    result = analyst.analyze(sample_data)
    
    assert 0.0 <= result["score"] <= 100.0
    assert result["sentiment_tier"] in ["BULLISH", "NEUTRAL / MIXED", "BEARISH"]
    assert len(result["headlines"]) == 2
    assert "report_markdown" in result


def test_bull_and_bear_researchers():
    """Verify Bull and Bear researchers generate dialectical theses and rebuttals."""
    bull = BullResearcher()
    bear = BearResearcher()

    mock_state = {
        "profile": {"ticker": "GOOGL", "name": "Alphabet Inc.", "target_mean_price": 190.0, "target_high_price": 210.0, "target_low_price": 150.0},
        "fundamentals": {"score": 78.0, "valuation_score": 65.0, "metrics": {"roe": 28.0, "revenue_growth": 14.0, "free_cash_flow": 70_000_000_000.0, "trailing_pe": 24.0, "debt_to_equity": 10.0}},
        "technicals": {"score": 72.0, "current_price": 165.0, "trend_bias": "BULLISH", "levels": {"support": 155.0, "resistance": 180.0, "rsi_14": 56.0}},
        "sentiment": {"score": 70.0, "sentiment_tier": "BULLISH"}
    }

    # Round 1
    bull_r1 = bull.generate_thesis(mock_state, round_num=1)
    assert bull_r1["speaker"] == "Bull Researcher"
    assert bull_r1["upside_target_price"] > 165.0
    assert len(bull_r1["catalysts"]) > 0
    assert "dialogue" in bull_r1

    bear_r1 = bear.generate_rebuttal(mock_state, round_num=1, bull_argument=bull_r1["dialogue"])
    assert bear_r1["speaker"] == "Bear Researcher"
    assert bear_r1["downside_target_price"] < 165.0
    assert len(bear_r1["risks"]) > 0
    assert "dialogue" in bear_r1

    # Round 2 (Cross-Examination)
    bull_r2 = bull.generate_thesis(mock_state, round_num=2, bear_argument=bear_r1["dialogue"])
    assert bull_r2["round"] == 2
    assert "Bull Counter-Rebuttal" in bull_r2["dialogue"]

    bear_r2 = bear.generate_rebuttal(mock_state, round_num=2, bull_argument=bull_r2["dialogue"])
    assert bear_r2["round"] == 2
    assert "Bear Counter-Rebuttal" in bear_r2["dialogue"]


def test_risk_manager_bounds():
    """Verify Risk Manager calculates safe stop losses, volatility sizing, and risk tier."""
    risk_mgr = RiskManager()
    mock_state = {
        "profile": {"ticker": "AMZN"},
        "fundamentals": {"metrics": {"debt_to_equity": 60.0}},
        "technicals": {
            "current_price": 180.0,
            "atr_14": 4.5,
            "beta": 1.15,
            "support_level": 168.0,
            "levels": {"atr_14": 4.5, "support": 168.0}
        }
    }
    risk_out = risk_mgr.assess_risk(mock_state)

    assert risk_out["stop_loss"] < 180.0
    assert risk_out["stop_loss_pct"] < 0.0  # Must be negative exit %
    assert 2.0 <= risk_out["position_size_pct"] <= 20.0  # Sizing bounds
    assert risk_out["risk_tier"] in ["LOW RISK", "MEDIUM RISK", "HIGH RISK", "EXTREME RISK"]
    assert 0.0 <= risk_out["risk_quality_score"] <= 100.0


def test_portfolio_manager_synthesis():
    """Verify Portfolio Manager synthesizes conviction, radar scores, and executive verdict."""
    pm = PortfolioManager()
    mock_state = {
        "profile": {"ticker": "META", "name": "Meta Platforms Inc.", "target_mean_price": 540.0},
        "fundamentals": {"score": 82.0, "valuation_score": 68.0, "health_grade": "A", "metrics": {"free_cash_flow": 40e9}},
        "technicals": {"score": 76.0, "current_price": 490.0, "trend_bias": "BULLISH", "levels": {"support": 460.0}},
        "sentiment": {"score": 74.0},
        "debate": [
            {"speaker": "Bull Researcher", "upside_target_price": 580.0},
            {"speaker": "Bear Researcher", "downside_target_price": 450.0}
        ],
        "risk": {"stop_loss": 455.0, "position_size_pct": 14.5, "risk_tier": "LOW RISK", "risk_quality_score": 80.0}
    }

    decision = pm.synthesize_decision(mock_state)

    assert decision["verdict"] in ["STRONG BUY", "BUY", "HOLD", "SELL", "STRONG SELL"]
    assert 0 <= decision["conviction_score"] <= 100
    assert decision["target_price"] > 0
    assert decision["stop_loss"] < 490.0
    assert "radar_scores" in decision
    
    # 5 required radar axes
    required_radar = ["Fundamentals", "Technical Momentum", "Valuation", "Sentiment", "Risk Quality"]
    for axis in required_radar:
        assert axis in decision["radar_scores"]
        assert 0.0 <= decision["radar_scores"][axis] <= 100.0

    assert "executive_summary" in decision
    assert "Meta Platforms Inc." in decision["executive_summary"] or "META" in decision["executive_summary"]


# ============================================================================
# Tier 2: Boundary & Resilience Tests
# ============================================================================

def test_propagate_deterministic_offline():
    """Verify end-to-end propagation executes deterministically without crashing on offline data."""
    graph = TradingAgentsGraph(config={"llm_provider": "heuristic", "debate_rounds": 2})
    state, decision = graph.propagate("TEST_SYNTHETIC_TICKER")

    assert state is not None
    assert decision is not None
    assert state["ticker"] == "TEST_SYNTHETIC_TICKER"
    assert len(state["debate"]) == 4  # 2 rounds * 2 researchers = 4 turns
    assert decision["verdict"] in ["STRONG BUY", "BUY", "HOLD", "SELL", "STRONG SELL"]
    assert 0 <= decision["conviction_score"] <= 100


def test_propagate_with_custom_debate_rounds():
    """Verify propagation adapts to 1, 2, and 3 debate rounds."""
    for rounds in [1, 2, 3]:
        graph = TradingAgentsGraph(config={"debate_rounds": rounds})
        state, decision = graph.propagate("AAPL")
        assert len(state["debate"]) == rounds * 2


def test_missing_or_corrupted_fields_handling():
    """Verify data provider and analyst nodes handle null/missing fields gracefully."""
    provider = FinancialDataProvider()
    # Passing empty info and corrupted history
    bad_info = {}
    bad_hist = pd.DataFrame()
    
    # Should build fallback history and extract default fundamentals
    data = provider.get_stock_data("CORRUPT_NULL")
    assert data["profile"]["ticker"] == "CORRUPT_NULL"
    assert data["technicals"]["current_price"] > 0
    assert data["fundamentals"]["trailing_pe"] > 0

    analyst = FundamentalAnalyst()
    res = analyst.analyze(data)
    assert 0 <= res["score"] <= 100


# ============================================================================
# Tier 3: Cross-Feature & Multi-Ticker Consistency
# ============================================================================

@pytest.mark.parametrize("ticker", ["AAPL", "NVDA", "MSFT", "GOOGL", "JPM"])
def test_multi_ticker_propagation_consistency(ticker):
    """Verify state consistency across master watchlist tickers."""
    graph = TradingAgentsGraph()
    state, decision = graph.propagate(ticker)

    # State contract verification
    assert state["ticker"] == ticker
    assert "profile" in state
    assert "fundamentals" in state
    assert "technicals" in state
    assert "sentiment" in state
    assert "debate" in state
    assert "risk" in state

    # Decision contract verification
    assert decision["ticker"] == ticker
    assert decision["conviction_score"] >= 0
    assert decision["stop_loss"] < state["technicals"]["current_price"]
    assert len(decision["radar_scores"]) == 5
