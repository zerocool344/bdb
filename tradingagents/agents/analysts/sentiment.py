"""
Sentiment & News Analyst Agent for TradingAgents.
Evaluates market sentiment, corporate news headlines, and Wall Street analyst revisions.
"""

from typing import Dict, Any, List


class SentimentAnalyst:
    """
    Performs sentiment analysis on news headlines, Wall Street consensus recommendations,
    and institutional price target dispersion.
    """

    POSITIVE_WORDS = {
        "surge", "surges", "soar", "soars", "jump", "jumps", "beat", "beats", "record",
        "growth", "bull", "bullish", "upgrade", "upgrades", "outperform", "buy", "profit",
        "rally", "rallies", "partnership", "breakthrough", "gain", "gains", "lead", "expand",
        "dividend", "strong", "accelerate", "win", "high", "top"
    }

    NEGATIVE_WORDS = {
        "drop", "drops", "fall", "falls", "plunge", "plunges", "miss", "misses", "cut",
        "cuts", "downgrade", "downgrades", "underperform", "sell", "loss", "losses", "slump",
        "lawsuit", "investigation", "probe", "regulatory", "headwind", "decline", "declines",
        "warn", "warning", "weak", "delay", "crash", "risk", "debt"
    }

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes news headlines and consensus ratings to produce structured sentiment intelligence.
        """
        profile = data.get("profile", {})
        news_items = data.get("news", [])
        ticker = profile.get("ticker", "UNKNOWN")
        rec_key = profile.get("recommendation_key", "hold").lower()
        current_price = profile.get("current_price", 100.0)
        target_mean = profile.get("target_mean_price", current_price * 1.1)

        # 1. News Lexicon Sentiment Scoring
        news_score = 50.0
        analyzed_headlines = []

        if news_items:
            pos_count = 0
            neg_count = 0
            for item in news_items:
                title = item.get("title", "")
                summary = item.get("summary", "")
                words = set((title + " " + summary).lower().replace(".", " ").replace(",", " ").split())
                
                has_pos = bool(words & self.POSITIVE_WORDS)
                has_neg = bool(words & self.NEGATIVE_WORDS)
                
                if has_pos and not has_neg:
                    pos_count += 1
                    analyzed_headlines.append(f"🟢 {title}")
                elif has_neg and not has_pos:
                    neg_count += 1
                    analyzed_headlines.append(f"🔴 {title}")
                else:
                    analyzed_headlines.append(f"⚪ {title}")

            total_tagged = pos_count + neg_count
            if total_tagged > 0:
                net_polarity = (pos_count - neg_count) / total_tagged
                news_score = 50.0 + (net_polarity * 30.0)
        else:
            analyzed_headlines = [
                f"⚪ Market consensus monitoring active order flow on {ticker}",
                f"⚪ Baseline institutional positioning steady"
            ]

        news_score = max(10.0, min(90.0, news_score))

        # 2. Wall Street Consensus Analyst Sentiment
        consensus_score = 50.0
        if "strong_buy" in rec_key or "strongbuy" in rec_key:
            consensus_score = 88.0
        elif "buy" in rec_key:
            consensus_score = 72.0
        elif "outperform" in rec_key:
            consensus_score = 68.0
        elif "hold" in rec_key or "neutral" in rec_key:
            consensus_score = 50.0
        elif "underperform" in rec_key:
            consensus_score = 35.0
        elif "sell" in rec_key:
            consensus_score = 20.0

        # Target upside multiplier
        upside_pct = ((target_mean - current_price) / current_price) * 100 if current_price > 0 else 0.0
        if upside_pct > 25.0:
            consensus_score += 10.0
        elif upside_pct < 0.0:
            consensus_score -= 10.0

        consensus_score = max(5.0, min(95.0, consensus_score))

        # Composite Sentiment Score (0 - 100)
        sentiment_score = round((news_score * 0.40) + (consensus_score * 0.60), 1)

        if sentiment_score >= 68:
            sentiment_tier = "BULLISH"
        elif sentiment_score <= 40:
            sentiment_tier = "BEARISH"
        else:
            sentiment_tier = "NEUTRAL / MIXED"

        report_markdown = f"""### 📰 Sentiment & News Analyst Dossier: **{ticker}**
**Sentiment Score:** `{sentiment_score}/100` | **Tone Bias:** `{sentiment_tier}` | **Analyst Consensus:** `{rec_key.replace('_', ' ').title()}`

#### Wall Street & Media Drivers
- **Mean Price Target:** `${target_mean}` ({'+' if upside_pct >= 0 else ''}{upside_pct:.1f}% implied upside)
- **News Lexicon Score:** `{news_score:.1f}/100`
- **Consensus Rating Score:** `{consensus_score:.1f}/100`

#### Recent News & Sentiment Scanner
{chr(10).join(['- ' + h for h in analyzed_headlines[:6]])}
"""

        return {
            "score": sentiment_score,
            "news_score": news_score,
            "consensus_score": consensus_score,
            "sentiment_tier": sentiment_tier,
            "headlines": analyzed_headlines,
            "report_markdown": report_markdown,
        }
