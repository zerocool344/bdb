"""
Default configuration for TradingAgents multi-agent financial framework.
"""

DEFAULT_CONFIG = {
    # Engine & Provider settings
    "llm_provider": "heuristic",  # "heuristic", "openai", "anthropic", "gemini", "ollama"
    "api_key": None,
    "quick_think_llm": "gpt-4o-mini",
    "deep_think_llm": "gpt-4o",
    "ollama_base_url": "http://localhost:11434",
    
    # Deliberation depth & Debate controls
    "debate_rounds": 2,  # Multi-turn Bull vs Bear debate rounds (1-3)
    
    # Risk Management controls
    "risk_tolerance": "moderate",  # "conservative", "moderate", "aggressive"
    "max_position_size": 0.20,     # Max 20% portfolio allocation
    "min_position_size": 0.02,     # Min 2% portfolio allocation
    "stop_loss_pct": 0.08,         # 8% default stop loss floor
    "target_volatility": 0.15,     # 15% annualized target volatility
    
    # Feature toggles
    "enable_fundamentals": True,
    "enable_technicals": True,
    "enable_sentiment": True,
    "enable_debate": True,
    "enable_risk_mgmt": True,
    
    # Historical market window
    "history_period": "1y",
}

AVAILABLE_PROVIDERS = [
    {"id": "heuristic", "name": "Deterministic Quant Engine (Free, Offline & Fast)", "requires_key": False},
    {"id": "openai", "name": "OpenAI (GPT-4o / GPT-4o-mini)", "requires_key": True},
    {"id": "anthropic", "name": "Anthropic (Claude 3.5 Sonnet / Haiku)", "requires_key": True},
    {"id": "gemini", "name": "Google Gemini (Gemini 1.5 Pro / Flash)", "requires_key": True},
    {"id": "ollama", "name": "Ollama (Local Open-Source LLMs)", "requires_key": False},
]
