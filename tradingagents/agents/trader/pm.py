"""
Portfolio Manager Agent for TradingAgents.
Synthesizes analyst dossiers, debate resolutions, and risk guardrails into final consensus decisions.
"""

from typing import Dict, Any, Tuple


class PortfolioManager:
    """
    Acts as the Executive Committee Chair. Evaluates committee consensus,
    generates 5-axis conviction radar metrics, and formulates final trading directives.
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def synthesize_decision(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes state containing analyst outputs, debate rounds, and risk assessment,
        and produces the unified institutional investment verdict.
        """
        profile = state.get("profile", {})
        fund = state.get("fundamentals", {})
        tech = state.get("technicals", {})
        sent = state.get("sentiment", {})
        debate = state.get("debate", [])
        risk = state.get("risk", {})

        ticker = profile.get("ticker", "ASSET")
        name = profile.get("name", ticker)
        current_price = tech.get("current_price", 100.0)
        wall_st_target = profile.get("target_mean_price", current_price * 1.12)

        # 1. Five Radar Dimension Scores (0 - 100)
        fund_score = float(fund.get("score", 60.0))
        tech_score = float(tech.get("score", 60.0))
        val_score = float(fund.get("valuation_score", 55.0))
        sent_score = float(sent.get("score", 58.0))
        risk_score = float(risk.get("risk_quality_score", 62.0))

        radar_scores = {
            "Fundamentals": round(fund_score, 1),
            "Technical Momentum": round(tech_score, 1),
            "Valuation": round(val_score, 1),
            "Sentiment": round(sent_score, 1),
            "Risk Quality": round(risk_score, 1),
        }

        # 2. Institutional Conviction Score (0 - 100)
        raw_conviction = (
            fund_score * 0.25 +
            tech_score * 0.20 +
            val_score * 0.20 +
            sent_score * 0.15 +
            risk_score * 0.20
        )
        conviction_score = int(round(max(5.0, min(95.0, raw_conviction))))

        # 3. Dynamic Target Price Synthesis
        # Anchor between Wall Street mean and Bull/Bear targets weighted by conviction
        bull_target = current_price * 1.20
        bear_target = current_price * 0.88
        for d in debate:
            if d.get("speaker") == "Bull Researcher" and "upside_target_price" in d:
                bull_target = d["upside_target_price"]
            elif d.get("speaker") == "Bear Researcher" and "downside_target_price" in d:
                bear_target = d["downside_target_price"]

        bull_weight = conviction_score / 100.0
        bear_weight = 1.0 - bull_weight
        blended_target = (bull_target * bull_weight) + (bear_target * bear_weight)
        
        # Pull toward wall street consensus slightly
        final_target_price = round((blended_target * 0.70) + (wall_st_target * 0.30), 2)
        target_upside_pct = round(((final_target_price - current_price) / current_price) * 100, 1)

        # 4. Risk and Stop Loss Integration
        stop_loss = risk.get("stop_loss", round(current_price * 0.92, 2))
        position_size_pct = risk.get("position_size_pct", 10.0)
        risk_tier = risk.get("risk_tier", "MEDIUM RISK")

        # 5. Final Institutional Verdict
        if conviction_score >= 78 and target_upside_pct >= 10.0 and risk_tier != "EXTREME RISK":
            verdict = "STRONG BUY"
            badge = "🟢 STRONG BUY"
            color = "#00C853"
        elif conviction_score >= 62 and target_upside_pct >= 4.0:
            verdict = "BUY"
            badge = "🟢 BUY"
            color = "#2E7D32"
        elif conviction_score <= 32 or (target_upside_pct < -8.0 and risk_tier == "EXTREME RISK"):
            verdict = "STRONG SELL"
            badge = "🔴 STRONG SELL"
            color = "#D50000"
        elif conviction_score <= 45 or target_upside_pct < -2.0:
            verdict = "SELL"
            badge = "🔴 SELL"
            color = "#C62828"
        else:
            verdict = "HOLD"
            badge = "🟡 HOLD"
            color = "#F57F17"

        # 6. Executive Narrative Synthesis
        direction = "Upside" if target_upside_pct >= 0 else "Downside"
        executive_summary = f"""### 🏛️ Executive Investment Committee Verdict: **{verdict}** (`{conviction_score}/100 Conviction`)

**Asset:** `{ticker}` ({name}) | **Current Market Price:** `${current_price}`

#### 🎯 Strategic Directive & Trade Structure
- **Verdict Action:** `{badge}`
- **Price Target (12M):** **${final_target_price}** ({abs(target_upside_pct)}% implied {direction})
- **Stop Loss Guardrail:** **${stop_loss}** ({abs(round(((stop_loss-current_price)/current_price)*100, 1))}% max risk exit)
- **Recommended Portfolio Size:** **{position_size_pct}%** (Risk-Parity Adjusted)
- **Risk Classification:** `{risk_tier}`

#### 🔬 Committee Synthesis & Debate Resolution
The committee completed a {len(debate)}-round dialectical debate between Bull and Bear researchers.
The **Fundamental Pillar** shows `{fund.get('health_grade', 'B')}` tier solvency with **{fund.get('score', 60)}/100** composite score.
**Technical Momentum** is positioned at **{tech.get('score', 60)}/100** ({tech.get('trend_bias', 'NEUTRAL')}), while **Sentiment & Media Scan** scores **{sent.get('score', 58)}/100**.

*Execution Mandate:* Initiate / rebalance allocation to **{position_size_pct}%** with strict stop-loss adherence at **${stop_loss}** to maintain downside skew discipline.
"""

        return {
            "ticker": ticker,
            "name": name,
            "verdict": verdict,
            "verdict_badge": badge,
            "verdict_color": color,
            "conviction_score": conviction_score,
            "target_price": final_target_price,
            "target_upside_pct": target_upside_pct,
            "stop_loss": stop_loss,
            "position_size_pct": position_size_pct,
            "risk_tier": risk_tier,
            "radar_scores": radar_scores,
            "executive_summary": executive_summary,
        }
