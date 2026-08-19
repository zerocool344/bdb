"""
TradingAgents Multi-Agent Financial Framework.
Vendored integration for Consensus Deck_AG.
"""

from .graph.trading_graph import TradingAgentsGraph
from .default_config import DEFAULT_CONFIG

__version__ = "0.1.0"
__all__ = ["TradingAgentsGraph", "DEFAULT_CONFIG", "__version__"]
