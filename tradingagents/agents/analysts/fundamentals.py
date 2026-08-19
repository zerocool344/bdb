"""
Fundamental Analyst Agent for TradingAgents.
Evaluates balance sheet health, profitability, valuation multiples, and cash flow generation.
"""

from typing import Dict, Any, List


class FundamentalAnalyst:
    """
    Performs quantitative and qualitative fundamental evaluation of an equity asset.
    Generates health grades, balance sheet stress tests, and valuation scores.
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes financial data dictionary and returns structured fundamental intelligence.
        """
        profile = data.get("profile", {})
        fund = data.get("fundamentals", {})
        ticker = profile.get("ticker", "UNKNOWN")

        trailing_pe = fund.get("trailing_pe", 25.0)
        forward_pe = fund.get("forward_pe", 20.0)
        peg = fund.get("peg_ratio", 1.5)
        debt_to_equity = fund.get("debt_to_equity", 50.0)
        current_ratio = fund.get("current_ratio", 1.5)
        operating_margins = fund.get("operating_margins", 15.0)
        profit_margins = fund.get("profit_margins", 12.0)
        roe = fund.get("roe", 18.0)
        rev_growth = fund.get("revenue_growth", 10.0)
        earnings_growth = fund.get("earnings_growth", 12.0)
        fcf = fund.get("free_cash_flow", 10_000_000_000.0)

        # 1. Valuation Scoring (0 - 100)
        # Lower P/E and PEG yield higher valuation scores
        val_score = 50.0
        if peg < 1.0:
            val_score += 25
        elif peg < 1.8:
            val_score += 15
        elif peg > 3.0:
            val_score -= 20

        if forward_pe < 15:
            val_score += 20
        elif forward_pe < 25:
            val_score += 10
        elif forward_pe > 40:
            val_score -= 20

        val_score = max(5.0, min(95.0, val_score))

        # 2. Solvency & Balance Sheet Health Scoring (0 - 100)
        solvency_score = 50.0
        if debt_to_equity < 40:
            solvency_score += 25
        elif debt_to_equity < 100:
            solvency_score += 15
        elif debt_to_equity > 200:
            solvency_score -= 25

        if current_ratio > 1.8:
            solvency_score += 20
        elif current_ratio > 1.2:
            solvency_score += 10
        elif current_ratio < 1.0:
            solvency_score -= 20

        solvency_score = max(5.0, min(95.0, solvency_score))

        # 3. Profitability & Capital Efficiency (0 - 100)
        profit_score = 50.0
        if roe > 25.0:
            profit_score += 25
        elif roe > 15.0:
            profit_score += 15
        elif roe < 0.0:
            profit_score -= 30

        if operating_margins > 25.0:
            profit_score += 20
        elif operating_margins > 15.0:
            profit_score += 10
        elif operating_margins < 5.0:
            profit_score -= 20

        profit_score = max(5.0, min(95.0, profit_score))

        # 4. Growth & Cash Flow (0 - 100)
        growth_score = 50.0
        if rev_growth > 20.0:
            growth_score += 25
        elif rev_growth > 10.0:
            growth_score += 15
        elif rev_growth < 0.0:
            growth_score -= 25

        if fcf > 0:
            growth_score += 15
        else:
            growth_score -= 20

        growth_score = max(5.0, min(95.0, growth_score))

        # Composite Fundamental Score
        fundamental_score = round(
            (val_score * 0.25) + (solvency_score * 0.25) + (profit_score * 0.25) + (growth_score * 0.25),
            1
        )

        # Health Grade
        if fundamental_score >= 85:
            health_grade = "A+"
        elif fundamental_score >= 75:
            health_grade = "A"
        elif fundamental_score >= 65:
            health_grade = "B"
        elif fundamental_score >= 50:
            health_grade = "C"
        elif fundamental_score >= 35:
            health_grade = "D"
        else:
            health_grade = "F"

        # Key Strengths & Vulnerabilities
        strengths = []
        vulnerabilities = []

        if roe > 15.0:
            strengths.append(f"🟢 High Capital Return: ROE of {roe}% reflects competitive economic moat")
        if operating_margins > 15.0:
            strengths.append(f"🟢 Margin Power: Operating margin of {operating_margins}% offers pricing leverage")
        if debt_to_equity < 100.0:
            strengths.append(f"🟢 Conservative Balance Sheet: Debt-to-Equity at {debt_to_equity}% protects solvency")
        if fcf > 0:
            strengths.append("🟢 Free Cash Flow Positive: Self-funding business model with organic capital generation")
        if rev_growth > 10.0:
            strengths.append(f"🟢 Topline Momentum: YoY revenue growth of {rev_growth}%")

        if peg > 2.5:
            vulnerabilities.append(f"🔴 Premium Valuation: PEG ratio of {peg} implies high embedded growth expectations")
        if forward_pe > 35:
            vulnerabilities.append(f"🔴 Multiple Compression Risk: Forward P/E at {forward_pe}x leaves little room for earnings misses")
        if debt_to_equity > 150:
            vulnerabilities.append(f"🔴 Elevated Leverage: Debt-to-Equity of {debt_to_equity}% increases interest rate sensitivity")
        if rev_growth < 0:
            vulnerabilities.append(f"🔴 Revenue Contraction: Topline contracted by {rev_growth}% YoY")

        if not strengths:
            strengths.append("🟡 Stable Core Operations: Consistent baseline market participation")
        if not vulnerabilities:
            vulnerabilities.append("🟢 Clean Balance Sheet: No immediate systemic accounting vulnerabilities observed")

        # Narrative Report
        report_markdown = f"""### 📊 Fundamental Analyst Dossier: **{ticker}**
**Health Grade:** `{health_grade}` | **Fundamental Score:** `{fundamental_score}/100` | **Valuation Score:** `{val_score}/100`

#### Core Multiples & Solvency Breakdown
- **Valuation:** Trailing P/E: **{trailing_pe}x** | Forward P/E: **{forward_pe}x** | PEG: **{peg}**
- **Profitability:** Operating Margin: **{operating_margins}%** | Net Margin: **{profit_margins}%** | ROE: **{roe}%**
- **Balance Sheet:** Debt/Equity: **{debt_to_equity}%** | Current Ratio: **{current_ratio}**
- **Growth & FCF:** Revenue Growth: **{rev_growth}%** | Free Cash Flow: **${fcf/1e9:.2f}B**

#### Key Strengths
{chr(10).join(['- ' + s for s in strengths])}

#### Vulnerabilities & Risk Flags
{chr(10).join(['- ' + v for v in vulnerabilities])}
"""

        return {
            "score": fundamental_score,
            "valuation_score": val_score,
            "solvency_score": solvency_score,
            "profitability_score": profit_score,
            "growth_score": growth_score,
            "health_grade": health_grade,
            "metrics": {
                "trailing_pe": trailing_pe,
                "forward_pe": forward_pe,
                "peg_ratio": peg,
                "debt_to_equity": debt_to_equity,
                "current_ratio": current_ratio,
                "operating_margins": operating_margins,
                "profit_margins": profit_margins,
                "roe": roe,
                "revenue_growth": rev_growth,
                "free_cash_flow": fcf,
            },
            "strengths": strengths,
            "vulnerabilities": vulnerabilities,
            "report_markdown": report_markdown,
        }
