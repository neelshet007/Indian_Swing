import ast
import inspect
import re
from typing import Dict, Any

from indian_swing.strategies.base import BaseStrategy
from indian_swing.core.logging_setup import get_logger

logger = get_logger(__name__)

class DynamicLookbackEngine:
    """
    Parses strategy source code to automatically determine required lookback.
    """
    _cache: Dict[str, int] = {}
    
    # Warmup buffer rules. 
    # Multiply the required days by a factor to ensure indicator stabilization.
    WARMUP_MULTIPLIER = 1.25 
    MIN_WARMUP_DAYS = 50

    @classmethod
    def get_required_lookback(cls, strategy: BaseStrategy) -> int:
        strategy_name = strategy.name
        
        if strategy_name in cls._cache:
            return cls._cache[strategy_name]
            
        logger.info(f"Dynamically calculating lookback for strategy: {strategy_name}")
        
        # 1. Get source code of the strategy class
        try:
            source_file = inspect.getsourcefile(strategy.__class__)
            if not source_file:
                 raise ValueError("Could not locate source file")
                 
            with open(source_file, 'r', encoding='utf-8') as f:
                source_code = f.read()
                
            # 2. Parse AST
            tree = ast.parse(source_code)
        except Exception as e:
            logger.error(f"Failed to parse AST for {strategy_name}: {e}. Defaulting to 200.")
            return 200
            
        # 3. Extract string literals that match indicator patterns
        indicator_strings = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                indicator_strings.add(node.value)
            # Support for older python where strings are ast.Str
            elif isinstance(node, getattr(ast, 'Str', type(None))):
                indicator_strings.add(node.s)
                
        # 4. Analyze patterns to find requirements
        # Matches formats like: sma_200, ema_50, atr_14, high_52w, sma_30w
        pattern = re.compile(r'^[a-zA-Z]+_(\d+)(w)?$')
        
        max_required_days = 0
        
        for ind in indicator_strings:
            match = pattern.match(ind)
            if match:
                val = int(match.group(1))
                is_weekly = bool(match.group(2))
                
                # If weekly, 1 week ~ 5 trading days
                days_required = val * 5 if is_weekly else val
                
                if days_required > max_required_days:
                    max_required_days = days_required
                    
        # 5. Apply warm-up buffer
        if max_required_days == 0:
            # Fallback if no indicators found
            final_lookback = 100 
        else:
            final_lookback = int(max(
                max_required_days * cls.WARMUP_MULTIPLIER, 
                max_required_days + cls.MIN_WARMUP_DAYS
            ))
            
        logger.info(f"Strategy '{strategy_name}' requires max {max_required_days} days. With warmup buffer, setting final lookback to {final_lookback} days.")
        
        cls._cache[strategy_name] = final_lookback
        return final_lookback
