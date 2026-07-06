from abc import ABC, abstractmethod
from typing import Dict, Optional

class ProviderAdapter(ABC):
    @abstractmethod
    def format_symbol(self, canonical_symbol: str) -> str:
        """Convert a canonical internal symbol to the provider's specific format."""
        pass
        
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the provider (e.g., 'yahoo', 'groww')."""
        pass

class YahooAdapter(ProviderAdapter):
    @property
    def name(self) -> str:
        return "yahoo"

    def format_symbol(self, canonical_symbol: str) -> str:
        # Yahoo Finance uses .NS for NSE stocks
        # Verify it doesn't already end with .NS
        if canonical_symbol.endswith(".NS"):
            return canonical_symbol
            
        return f"{canonical_symbol}.NS"

class SymbolManager:
    """
    Centralized Symbol Management Layer.
    Ensures internal symbols are canonical, and converts to provider formats correctly.
    """
    _cache: Dict[str, Dict[str, str]] = {}
    
    @staticmethod
    def normalize_internal_symbol(symbol: str) -> str:
        """
        Cleans up a symbol to its canonical form (no whitespace, uppercase, no suffixes).
        """
        if not symbol:
            raise ValueError("Symbol cannot be empty.")
            
        cleaned = symbol.strip().upper()
        
        # Remove any known provider suffixes if accidentally included
        if cleaned.endswith(".NS"):
            cleaned = cleaned[:-3]
            
        # Ensure no whitespace exists inside
        if " " in cleaned:
            raise ValueError(f"Symbol '{cleaned}' contains whitespace.")
            
        return cleaned
        
    @classmethod
    def get_provider_symbol(cls, symbol: str, adapter: ProviderAdapter) -> str:
        """
        Gets the provider-specific symbol, utilizing caching to prevent redundant formatting.
        """
        canonical = cls.normalize_internal_symbol(symbol)
        provider_name = adapter.name
        
        if canonical not in cls._cache:
            cls._cache[canonical] = {}
            
        if provider_name not in cls._cache[canonical]:
            formatted = adapter.format_symbol(canonical)
            
            # Final verification of Yahoo adapter logic just in case
            if provider_name == "yahoo":
                if formatted.count(".NS") > 1:
                    raise ValueError(f"Duplicate suffix detected in '{formatted}'")
                    
            cls._cache[canonical][provider_name] = formatted
            
        return cls._cache[canonical][provider_name]
