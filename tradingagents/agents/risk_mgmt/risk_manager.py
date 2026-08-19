"""
Risk Manager Agent for TradingAgents.
Computes volatility-adjusted position sizing, dynamic stop losses, and drawdown limits.
"""

from typing import Dict, Any


class RiskManager:
    """
    Assesses market and balance-sheet risk to determine institutional position sizing,
    stop loss protection levels, and risk classification tiers.
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.max_position_size = self.config.get("max_position_size", 0.20)
        self.min_position_size = self.config.get("min_position_size", 0.02)
        self.default_stop_pct = self.config.get("stop_loss_pct", 0.08)

    def assess_risk(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesizes technical volatility, beta, balance sheet leverage, and downside scenarios.
        """
        profile = state.get("profile", {})
        fund = state.get("fundamentals", {})
        tech = state.get("technicals", {})
        ticker = profile.get("ticker", "ASSET")

        current_price = tech.get("current_price", 100.0)
        atr = tech.get("levels", {}).get("atr_14") or tech.get("atr_14", current_price * 0.02)
        beta = tech.get("beta", 1.0)
        support = tech.get("levels", {}).get("support") or tech.get("support_level", current_price * 0.92)
        debt_to_eq = fund.get("metrics", {}).get("debt_to_equity", 50.0)

        # 1. Stop Loss Calculation (ATR & Support Based)
        # Place stop ~2x ATR below price, but not above support and within 5% - 12% bounds
        atr_stop_distance = max(atr * 2.0, current_price * 0.05)
        raw_stop = current_price - atr_stop_distance
        
        # Check against support level
        if support < current_price:
            raw_stop = min(raw_stop, support * 0.99)

        # Hard guardrails: stop loss must be between 5% and 12% below current price
        min_stop = current_price * 0.88  # Max 12% drop
        max_stop = current_price * 0.95  # Min 5% drop
        stop_loss = round(max(min_stop, min(max_stop, raw_stop)), 2)
        stop_loss_pct = round(((stop_loss - current_price) / current_price) * 100, 1)

        # 2. Position Sizing (Volatility-Adjusted Risk Parity)
        # Sizing scales inversely with volatility and Beta
        risk_per_unit = max(0.01, (current_price - stop_loss) / current_price)
        portfolio_risk_budget = 0.012  # Risk 1.2% of total portfolio equity on this trade
        raw_size = portfolio_risk_budget / risk_per_unit

        # Scale by beta factor
        beta_scale = 1.0 / max(0.6, min(2.0, beta))
        adjusted_size = raw_size * beta_scale

        # Clamp between min (2%) and max (20%)
        position_size_pct = round(max(self.min_position_size, min(self.max_position_size, adjusted_size)) * 100, 1)

        # 3. Risk Tier Classification
        if beta > 1.8 or debt_to_eq > 200:
            risk_tier = "EXTREME RISK"
            risk_badge = "🔴 EXTREME"
        elif beta > 1.3 or debt_to_eq > 120:
            risk_tier = "HIGH RISK"
            risk_badge = "🟠 HIGH"
        elif beta < 0.9 and debt_to_eq < 80:
            risk_tier = "LOW RISK"
            risk_badge = "🟢 LOW"
        else:
            risk_tier = "MEDIUM RISK"
            risk_badge = "🟡 MEDIUM"

        # 4. Value-at-Risk & Expected Drawdown
        var_95_1m = round(current_price * (beta * 0.08 + (atr / current_price) * 2.0), 2)
        var_pct = round((var_95_1m / current_price) * 100, 1)

        # 5. Risk Quality Score (0 - 100) -> Higher is safer / better risk-adjusted
        base_risk_score = 100.0 - (beta * 20.0 + (debt_to_eq / 10.0) + (atr / current_price * 250.0))
        risk_quality_score = round(max(10.0, min(95.0, base_risk_score)), 1)

        report_markdown = f"""### 🛡️ Risk Management Dossier: **{ticker}**
**Risk Tier:** `{risk_tier}` | **Risk Quality Score:** `{risk_quality_score}/100` | **Recommended Size:** `{position_size_pct}%`

#### Volatility & Risk Parameters
- **Current Price:** `${current_price}`
- **Dynamic Stop-Loss:** `${stop_loss}` (**{stop_loss_pct}%** from entry)
- **ATR (14-Day):** `${atr:.2f}` (**{atr/current_price*100:.1f}%** daily volatility)
- **Beta:** `{beta:.2f}` (Systematic market sensitivity)
- **1-Month 95% VaR:** `${var_95_1m}` (**-{var_pct}%** tail risk)
- **Solvency Burden:** Debt/Equity at **{debt_to_eq}%**
"""

        return {
            "risk_tier": risk_tier,
            "risk_badge": risk_badge,
            "risk_quality_score": risk_quality_score,
            "position_size_pct": position_size_pct,
            "stop_loss": stop_loss,
            "stop_loss_pct": stop_loss_pct,
            "atr": atr,
            "beta": beta,
            "var_95_1m": var_95_1m,
            "var_pct": var_pct,
            "report_markdown": report_markdown,
        }
