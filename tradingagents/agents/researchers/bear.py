"""
Bear Researcher Agent for TradingAgents.
Advocates for risk awareness, identifies downside vulnerabilities, and challenges Bull thesis during debate.
"""

from typing import Dict, Any, Optional, List


class BearResearcher:
    """
    Formulates institutional bear case, sets downside price targets, and cross-examines Bull researcher.
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def generate_rebuttal(
        self,
        state: Dict[str, Any],
        round_num: int = 1,
        bull_argument: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates initial Bear thesis (Round 1) or cross-examination against Bull arguments (Rounds > 1).
        """
        profile = state.get("profile", {})
        fund = state.get("fundamentals", {})
        tech = state.get("technicals", {})
        sent = state.get("sentiment", {})

        ticker = profile.get("ticker", "ASSET")
        current_price = tech.get("current_price", 100.0)
        target_low = profile.get("target_low_price", current_price * 0.85)
        support = tech.get("levels", {}).get("support", current_price * 0.88)

        # Downside price target: lower bound of support / Wall St low
        downside_target = round(min(target_low, support, current_price * 0.88), 2)
        downside_pct = round(((downside_target - current_price) / current_price) * 100, 1)

        fund_val_score = fund.get("valuation_score", 50.0)
        trailing_pe = fund.get("metrics", {}).get("trailing_pe", 25.0)
        debt_to_eq = fund.get("metrics", {}).get("debt_to_equity", 50.0)
        rsi_14 = tech.get("levels", {}).get("rsi_14", 50.0)

        bear_conviction = int(min(95, max(20, (100.0 - fund_val_score) * 0.5 + (100.0 - fund.get("score", 60.0)) * 0.3 + 25)))

        downside_risks = []
        if trailing_pe > 30.0:
            downside_risks.append(f"Elevated multiple of {trailing_pe}x P/E invites aggressive multiple compression upon growth deceleration.")
        if debt_to_eq > 120.0:
            downside_risks.append(f"High debt load (Debt/Equity {debt_to_eq}%) limits balance sheet flexibility in a high-rate regime.")
        if rsi_14 > 68.0:
            downside_risks.append(f"Overbought technical momentum (RSI {rsi_14}) indicates near-term exhaustion and buyer fatigue.")
        if tech.get("trend_bias") == "BEARISH":
            downside_risks.append("Broken technical structure with distribution volume below key moving averages.")
        if not downside_risks:
            downside_risks.append("Macroeconomic demand softening and rising competitive margin pressure.")
            downside_risks.append("Asymmetry skewed to downside if quarterly guidance misses elevated street consensus.")

        if round_num == 1:
            dialogue = (
                f"**Bear Thesis (Round 1):** We urge extreme caution on **{ticker}** and project downside risk to "
                f"**${downside_target} ({downside_pct}%)**. The Bull's euphoria ignores valuation vulnerabilities "
                f"(Valuation score `{fund_val_score}/100`, P/E `{trailing_pe}x`). Key vulnerabilities: "
                f"{'; '.join(downside_risks[:2])}."
            )
        else:
            dialogue = (
                f"**Bear Counter-Rebuttal (Round {round_num}):** The Bull fails to account for macro sensitivity and "
                f"diminishing incremental margins. If market volatility spikes, {ticker}'s multiple will contract toward "
                f"its historical mean, threatening a break below key support (${support}). Downside risk to **${downside_target}** "
                f"remains our baseline risk-adjusted forecast."
            )

        return {
            "round": round_num,
            "speaker": "Bear Researcher",
            "avatar": "🐻",
            "downside_target_price": downside_target,
            "downside_potential_pct": downside_pct,
            "conviction": bear_conviction,
            "risks": downside_risks,
            "dialogue": dialogue,
        }
