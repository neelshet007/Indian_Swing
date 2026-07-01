"""
Auto-discovery strategy registry.
Scans the strategies/ package at startup.
Users drop a .py file into strategies/ and it is immediately available — no config changes needed.
"""
from __future__ import annotations

import importlib
import inspect
import pkgutil
from pathlib import Path

from indian_swing.core.exceptions import StrategyNotFoundError
from indian_swing.core.logging_setup import get_logger
from indian_swing.strategies.base import BaseStrategy

logger = get_logger(__name__)

_STRATEGIES_PKG = "indian_swing.strategies"
_STRATEGIES_DIR = Path(__file__).parent


class StrategyRegistry:
    """Singleton registry that auto-discovers and holds all BaseStrategy subclasses."""

    def __init__(self) -> None:
        self._registry: dict[str, BaseStrategy] = {}
        self._discovered = False

    def discover(self) -> None:
        """Import every module in strategies/ and register concrete BaseStrategy subclasses."""
        if self._discovered:
            return

        for _, module_name, is_pkg in pkgutil.iter_modules([str(_STRATEGIES_DIR)]):
            if module_name in ("base", "registry", "__init__"):
                continue
            fqn = f"{_STRATEGIES_PKG}.{module_name}"
            try:
                module = importlib.import_module(fqn)
            except Exception as e:
                logger.warning("registry.import_failed", module=fqn, error=str(e))
                continue

            for _, cls in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(cls, BaseStrategy)
                    and cls is not BaseStrategy
                    and not inspect.isabstract(cls)
                ):
                    try:
                        instance = cls()
                        self._registry[instance.name] = instance
                        logger.debug("registry.registered", strategy=instance.name)
                    except Exception as e:
                        logger.warning("registry.instantiation_failed", cls=cls.__name__, error=str(e))

        self._discovered = True
        logger.info("registry.discovery_complete", count=len(self._registry))

    def get(self, name: str) -> BaseStrategy:
        self.discover()
        if name not in self._registry:
            raise StrategyNotFoundError(f"Strategy '{name}' not found. Available: {self.list_names()}")
        return self._registry[name]

    def all(self) -> list[BaseStrategy]:
        self.discover()
        return list(self._registry.values())

    def list_names(self) -> list[str]:
        self.discover()
        return sorted(self._registry.keys())

    def __len__(self) -> int:
        self.discover()
        return len(self._registry)


# Module-level singleton
strategy_registry = StrategyRegistry()
