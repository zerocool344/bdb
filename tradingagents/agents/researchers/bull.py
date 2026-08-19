"""
Bull Researcher Agent for TradingAgents.
Advocates for long positioning, identifies upside catalysts, and defends thesis during debate.
"""

from typing import Dict, Any, Optional, List


class BullResearcher:
    """
    Formulates institutional bull case, sets upside price targets, and debates Bear researcher.
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def generate_thesis(
        self,
        state: Dict[str, Any],
        round_num: int = 1,
        bear_argument: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates initial Bull thesis (Round 1) or rebuttal against Bear counter-points (Rounds > 1).
        """
        profile = state.get("profile", {})
        fund = state.get("fundamentals", {})
        tech = state.get("technicals", {})
        sent = state.get("sentiment", {})
        
        ticker = profile.get("ticker", "ASSET")
        current_price = tech.get("current_price", 100.0)
        target_mean = profile.get("target_mean_price", current_price * 1.20)
        target_high = profile.get("target_high_price", current_price * 1.35)
        
        # Calculate upside target: at least 15% above current price or target high
        upside_target = round(max(target_mean, target_high, current_price * 1.15), 2)
        upside_pct = round(((upside_target - current_price) / current_price) * 100, 1)

        fund_score = fund.get("score", 60.0)
        tech_score = tech.get("score", 60.0)
        sent_score = sent.get("score", 60.0)
        bull_conviction = int(min(98, max(25, (fund_score * 0.4 + tech_score * 0.35 + sent_score * 0.25) * 1.1)))

        catalysts = []
        if fund.get("metrics", {}).get("roe", 0) > 15.0:
            catalysts.append(f"High Return on Equity ({fund['metrics']['roe']}%) guarantees compound reinvestment advantage.")
        if fund.get("metrics", {}).get("revenue_growth", 0) > 8.0:
            catalysts.append(f"Strong organic revenue growth ({fund['metrics']['revenue_growth']}%) outpaces industry sector.")
        if tech.get("trend_bias") == "BULLISH":
            catalysts.append(f"Robust technical trend alignment with price trading above key structural moving averages.")
        if sent.get("sentiment_tier") == "BULLISH":
            catalysts.append("Favorable institutional analyst revisions and positive news velocity.")
        if not catalysts:
            catalysts.append("Resilient core market franchise with secular tailwinds and defensive balance sheet positioning.")
            catalysts.append("Attractive risk/reward entry point with favorable asymmetric upside skew.")

        if round_num == 1:
            dialogue = (
                f"**Bull Thesis (Round 1):** We recommend an aggressive accumulation of **{ticker}** with a 12-month "
                f"upside target of **${upside_target} (+{upside_pct}%)**. The asset demonstrates exceptional economic "
                f"moat characteristics, supported by a Fundamental Score of `{fund_score}/100` and Technical Momentum at "
                f"`{tech_score}/100`. Key catalysts driving our upside thesis include: "
                f"{'; '.join(catalysts[:2])}."
            )
        else:
            dialogue = (
                f"**Bull Counter-Rebuttal (Round {round_num}):** While the Bear raises valid short-term risk factors "
                f"regarding market friction and valuation multiples, they materially underestimate {ticker}'s pricing "
                f"power and free cash flow durability (${fund.get('metrics', {}).get('free_cash_flow', 0)/1e9:.1f}B). "
                f"Historical pullbacks to support (${tech.get('levels', {}).get('support', current_price*0.92)}) have "
                f"consistently served as high-alpha entry points. We maintain our upside objective of **${upside_target}**."
            )

        return {
            "round": round_num,
            "speaker": "Bull Researcher",
            "avatar": "🐂",
            "upside_target_price": upside_target,
            "upside_potential_pct": upside_pct,
            "conviction": bull_conviction,
            "catalysts": catalysts,
            "dialogue": dialogue,
        }
