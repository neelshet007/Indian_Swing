"""
Provider factory. The rest of the application uses get_provider() — never imports concrete providers.
"""
from __future__ import annotations

from functools import lru_cache

from indian_swing.config.settings import settings
from indian_swing.core.exceptions import ConfigurationError
from indian_swing.data.providers.base import DataProvider


@lru_cache(maxsize=1)
def get_provider() -> DataProvider:
    """Return the configured data provider singleton."""
    provider_name = settings.provider.default.lower()

    if provider_name == "upstox":
        from indian_swing.data.providers.upstox_provider import UpstoxProvider
        return UpstoxProvider()

    # Future providers plug in here
    # elif provider_name == "zerodha":
    #     from indian_swing.data.providers.zerodha_provider import ZerodhaProvider
    #     return ZerodhaProvider()

    raise ConfigurationError(
        f"Unknown data provider: {provider_name!r}. "
        "Valid options: ['upstox']"
    )
