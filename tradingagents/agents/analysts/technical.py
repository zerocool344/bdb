"""
Technical Analyst Agent for TradingAgents.
Evaluates price momentum, moving average trend structures, RSI/MACD oscillators, and volatility bands.
"""

from typing import Dict, Any, List


class TechnicalAnalyst:
    """
    Performs quantitative momentum, trend, and support/resistance analysis.
    Generates technical scores, multi-indicator signals, and breakout/breakdown alerts.
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes market data and returns structured technical momentum intelligence.
        """
        profile = data.get("profile", {})
        tech = data.get("technicals", {})
        ticker = profile.get("ticker", "UNKNOWN")

        current_price = tech.get("current_price", 100.0)
        sma_20 = tech.get("sma_20", current_price)
        sma_50 = tech.get("sma_50", current_price)
        sma_200 = tech.get("sma_200", current_price)
        rsi_14 = tech.get("rsi_14", 50.0)
        macd = tech.get("macd", 0.0)
        macd_signal = tech.get("macd_signal", 0.0)
        macd_hist = tech.get("macd_hist", 0.0)
        bb_upper = tech.get("bb_upper", current_price * 1.05)
        bb_lower = tech.get("bb_lower", current_price * 0.95)
        bb_mid = tech.get("bb_mid", current_price)
        pct_b = tech.get("bb_pct_b", 0.5)
        atr_14 = tech.get("atr_14", current_price * 0.02)
        support = tech.get("support_level", current_price * 0.92)
        resistance = tech.get("resistance_level", current_price * 1.08)
        trend_structure = tech.get("trend_structure", "NEUTRAL")

        # 1. Trend Alignment Score (0 - 100)
        trend_score = 50.0
        if current_price > sma_20:
            trend_score += 10
        if current_price > sma_50:
            trend_score += 15
        if current_price > sma_200:
            trend_score += 15
        if sma_50 > sma_200:
            trend_score += 10  # Golden cross environment

        if current_price < sma_20:
            trend_score -= 10
        if current_price < sma_50:
            trend_score -= 15
        if current_price < sma_200:
            trend_score -= 15

        trend_score = max(5.0, min(95.0, trend_score))

        # 2. Momentum / Oscillators Score (0 - 100)
        mom_score = 50.0
        # RSI analysis
        if 50.0 <= rsi_14 <= 65.0:
            mom_score += 20  # Bullish sweet spot
        elif 40.0 <= rsi_14 < 50.0:
            mom_score += 5
        elif rsi_14 > 70.0:
            mom_score += 5   # Strong trend but overbought risk
        elif rsi_14 < 30.0:
            mom_score -= 10  # Oversold (potential bounce or collapse)
        else:
            mom_score -= 15

        # MACD analysis
        if macd > macd_signal and macd_hist > 0:
            mom_score += 20  # Bullish divergence & momentum
        elif macd > macd_signal:
            mom_score += 10
        elif macd < macd_signal and macd_hist < 0:
            mom_score -= 20
        else:
            mom_score -= 10

        mom_score = max(5.0, min(95.0, mom_score))

        # 3. Volatility & Envelopes Score (0 - 100)
        vol_score = 50.0
        if 0.4 <= pct_b <= 0.8:
            vol_score += 25  # Healthy upper band ride
        elif pct_b > 1.0:
            vol_score += 10  # Breakout but extended
        elif pct_b < 0.2:
            vol_score -= 20  # Hovering on lower band

        vol_score = max(5.0, min(95.0, vol_score))

        # Composite Technical Score (0 - 100)
        technical_score = round((trend_score * 0.45) + (mom_score * 0.40) + (vol_score * 0.15), 1)

        # Trend Bias
        if technical_score >= 70:
            trend_bias = "BULLISH"
        elif technical_score <= 38:
            trend_bias = "BEARISH"
        else:
            trend_bias = "NEUTRAL / CONSOLIDATION"

        # Signal checklist
        signals = []
        if current_price >= sma_50:
            signals.append(f"🟢 Price above 50-day SMA (${sma_50})")
        else:
            signals.append(f"🔴 Price below 50-day SMA (${sma_50})")

        if current_price >= sma_200:
            signals.append(f"🟢 Price above 200-day SMA (${sma_200})")
        else:
            signals.append(f"🔴 Price below 200-day SMA (${sma_200})")

        if macd > macd_signal:
            signals.append(f"🟢 MACD Bullish Crossover (MACD {macd} > Signal {macd_signal})")
        else:
            signals.append(f"🔴 MACD Bearish Divergence (MACD {macd} < Signal {macd_signal})")

        if rsi_14 > 70:
            signals.append(f"⚠️ RSI Overbought ({rsi_14}) — pullback risk")
        elif rsi_14 < 30:
            signals.append(f"⚠️ RSI Oversold ({rsi_14}) — mean reversion candidate")
        else:
            signals.append(f"🟢 RSI In Equilibrium ({rsi_14})")

        if pct_b >= 0.8:
            signals.append(f"🟢 Bollinger Band Upper Probe (%B: {pct_b})")
        elif pct_b <= 0.2:
            signals.append(f"🔴 Bollinger Band Lower Compression (%B: {pct_b})")

        report_markdown = f"""### 📈 Technical Analyst Dossier: **{ticker}**
**Technical Score:** `{technical_score}/100` | **Trend Bias:** `{trend_bias}` | **Market Regime:** `{trend_structure}`

#### Key Price Architecture & Levels
- **Current Price:** `${current_price}`
- **Moving Averages:** 20 SMA: `${sma_20}` | 50 SMA: `${sma_50}` | 200 SMA: `${sma_200}`
- **Oscillators:** 14-day RSI: **{rsi_14}** | MACD Hist: **{macd_hist}**
- **Bollinger Envelopes:** Upper: `${bb_upper}` | Lower: `${bb_lower}` | %B: **{pct_b}**
- **Support & Resistance:** Key Support: **${support}** | Key Resistance: **${resistance}**
- **Daily Volatility (ATR 14):** `${atr_14}`

#### Active Technical Signals
{chr(10).join(['- ' + s for s in signals])}
"""

        return {
            "score": technical_score,
            "trend_score": trend_score,
            "momentum_score": mom_score,
            "trend_bias": trend_bias,
            "trend_structure": trend_structure,
            "current_price": current_price,
            "signals": signals,
            "levels": {
                "support": support,
                "resistance": resistance,
                "sma_20": sma_20,
                "sma_50": sma_50,
                "sma_200": sma_200,
                "bb_upper": bb_upper,
                "bb_lower": bb_lower,
                "rsi_14": rsi_14,
                "macd": macd,
                "macd_signal": macd_signal,
                "atr_14": atr_14,
            },
            "report_markdown": report_markdown,
        }
