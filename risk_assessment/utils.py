"""
Utility functions for the risk assessment workflow.
"""

import logging
from typing import Optional


def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured logger
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger("risk_assessment")


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "gemini-2.0-flash-exp"
) -> dict:
    """
    Calculate estimated API cost based on token usage.
    
    Pricing (as of 2025):
    - Gemini 2.0 Flash: Free tier up to rate limits, then $0.075/1M input, $0.30/1M output
    - Tavily: Free tier 1000 searches/month
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model name
        
    Returns:
        Dict with cost breakdown
    """
    pricing = {
        "gemini-2.0-flash-exp": {
            "input_per_1m": 0.075,
            "output_per_1m": 0.30
        },
        "gemini-1.5-flash": {
            "input_per_1m": 0.075,
            "output_per_1m": 0.30
        }
    }
    
    if model not in pricing:
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "estimated_cost_usd": 0.0,
            "note": f"Pricing not available for {model}"
        }
    
    rates = pricing[model]
    input_cost = (input_tokens / 1_000_000) * rates["input_per_1m"]
    output_cost = (output_tokens / 1_000_000) * rates["output_per_1m"]
    
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "estimated_cost_usd": round(input_cost + output_cost, 6),
        "cost_breakdown": {
            "input": round(input_cost, 6),
            "output": round(output_cost, 6)
        }
    }

