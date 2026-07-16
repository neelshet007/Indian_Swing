"""
Pydantic-settings based configuration management.
Loads from config.yaml, then overrides from environment variables / .env file.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_YAML = ROOT_DIR / "config" / "config.yaml"


def _load_yaml() -> dict[str, Any]:
    if CONFIG_YAML.exists():
        with CONFIG_YAML.open() as f:
            return yaml.safe_load(f) or {}
    return {}


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/indian_swing", 
        validation_alias="DATABASE_URL"
    )
    pool_size: int = Field(default=10, validation_alias="DATABASE_POOL_SIZE")
    echo: bool = False


class ProviderSettings(BaseSettings):
    default: str = "upstox"
    yfinance_threads: int = 4
    yfinance_rate_limit_delay: float = 0.5
    yfinance_retry_attempts: int = 3
    upstox_access_token: str | None = Field(default=None, validation_alias="UPSTOX_ACCESS_TOKEN")


class PipelineSettings(BaseSettings):
    lookback_years: int = 10
    min_trading_days: int = 252
    min_price: float = 10.0
    min_volume: int = 50_000
    max_gap_pct: float = 20.0
    warmup_days: int = 30


class ScannerSettings(BaseSettings):
    enabled: bool = True
    cron: str = "0 16 * * 1-5"
    max_workers: int = 8
    min_confidence_score: float = 0.6
    max_recommendations: int = 50
    benchmark_symbol: str = "^NSEI"
    benchmark_exchange: str = "INDEX"
    risk_per_trade_pct: float = 0.01
    max_portfolio_allocation_pct: float = 10.0


class BacktestSettings(BaseSettings):
    initial_capital: float = 1_000_000.0
    brokerage_pct: float = 0.0003
    stt_pct: float = 0.001
    slippage_pct: float = 0.0005
    max_positions: int = 10
    risk_per_trade_pct: float = 0.02


class APISettings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"]
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "development"
    log_level: str = "INFO"
    log_format: str = "json"

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    pipeline: PipelineSettings = Field(default_factory=PipelineSettings)
    scanner: ScannerSettings = Field(default_factory=ScannerSettings)
    backtesting: BacktestSettings = Field(default_factory=BacktestSettings)
    api: APISettings = Field(default_factory=APISettings)
    provider: ProviderSettings = Field(default_factory=ProviderSettings)
    upstox_access_token: str | None = Field(default=None, validation_alias="UPSTOX_ACCESS_TOKEN")

    data_dir: Path = ROOT_DIR / "data"
    cache_dir: Path = ROOT_DIR / "data" / "cache"
    universe_file: Path = ROOT_DIR / "config" / "universe.csv"

    @field_validator("data_dir", "cache_dir", mode="before")
    @classmethod
    def coerce_path(cls, v: Any) -> Path:
        return Path(v)

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def environment_name(self) -> str:
        return self.app_env.upper()

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)


def _merge_yaml_into_env(yaml_data: dict[str, Any]) -> None:
    """Inject YAML values as env vars if not already set (env vars take priority)."""
    flat: dict[str, str] = {}

    def _flatten(d: dict, prefix: str = "") -> None:
        for k, v in d.items():
            key = f"{prefix}{k}".upper()
            if isinstance(v, dict):
                _flatten(v, f"{key}__")
            elif v is not None:
                flat[key] = str(v)

    _flatten(yaml_data)
    for k, v in flat.items():
        os.environ.setdefault(k, v)


_yaml_data = _load_yaml()
_merge_yaml_into_env(_yaml_data)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    s = Settings()
    s.ensure_dirs()
    return s


settings: Settings = get_settings()
