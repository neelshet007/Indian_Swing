# Graph Report - C:\Indian_Swing  (2026-07-15)

## Corpus Check
- 93 files · ~103,105 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 629 nodes · 1394 edges · 55 communities detected
- Extraction: 46% EXTRACTED · 54% INFERRED · 0% AMBIGUOUS · INFERRED: 752 edges (avg confidence: 0.62)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]

## God Nodes (most connected - your core abstractions)
1. `RecommendationScanner` - 39 edges
2. `OHLCVRepository` - 34 edges
3. `Stock` - 33 edges
4. `BaseIndicator` - 31 edges
5. `get_sync_session()` - 30 edges
6. `DataPipeline` - 29 edges
7. `SignalDirection` - 28 edges
8. `RiskLevel` - 28 edges
9. `SignalQuality` - 28 edges
10. `ATR` - 28 edges

## Surprising Connections (you probably didn't know these)
- `check_rules()` --calls--> `InstitutionalVCP`  [INFERRED]
  C:\Indian_Swing\check_rules_stats.py → C:\Indian_Swing\indian_swing\strategies\institutional_vcp.py
- `check_rules()` --calls--> `get_sync_session()`  [INFERRED]
  C:\Indian_Swing\check_rules_stats.py → C:\Indian_Swing\indian_swing\database\connection.py
- `BacktestRequest` --uses--> `BacktestRunner`  [INFERRED]
  C:\Indian_Swing\indian_swing\api\routes\backtest.py → C:\Indian_Swing\indian_swing\backtesting\runner.py
- `run_backtest()` --calls--> `BacktestConfig`  [INFERRED]
  C:\Indian_Swing\indian_swing\api\routes\backtest.py → C:\Indian_Swing\indian_swing\backtesting\runner.py
- `Performance metrics engine. All institutional-grade metrics: CAGR, Sharpe, Sorti` --uses--> `Trade`  [INFERRED]
  C:\Indian_Swing\indian_swing\backtesting\metrics.py → C:\Indian_Swing\indian_swing\backtesting\trade.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (45): BaseRepository, CLI entry point using Typer. Usage:   swing db init   swing data download --univ, List all discovered strategies., List all discovered strategies., List all discovered strategies., Initialize database tables., Download OHLCV data for the specified universe., Download OHLCV data for the specified universe. (+37 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (50): BacktestRequest, BaseStrategy, data_requirements(), IndicatorRequirement, BaseStrategy contract. Strategies inherit this, implement generate_signals(), an, Override to provide configurable defaults., Return False if DataFrame is insufficient for this strategy., Analyze the DataFrame and return zero or more signals.          Args: (+42 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (42): BaseModel, ReplayEngine, ReplaySession, Exception, BacktestError, DatabaseError, DataError, DataNotFoundError (+34 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (32): BaseIndicator, All indicators extend this.     Subclasses implement compute() using vectorized, BaseIndicator, Replay Engine — sync DB version., ReplayState, CCI, Momentum indicators: RSI, Stochastic, Williams %R, CCI, ROC., ROC (+24 more)

### Community 4 - "Community 4"
Cohesion: 0.07
Nodes (25): list_saved_results(), run_backtest(), data_download(), db_init(), list_strategies(), scan_run(), configure_logging(), get_logger() (+17 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (19): _detect_vcp(), DynamicLookbackEngine, get_required_lookback(), OHLCVRepository, _df_to_records(), list_scan_jobs(), trigger_scan(), get_ohlcv() (+11 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (24): add_column(), check_db_rows(), check(), check_jobs(), check_pfc(), check_pfc_history(), check(), check_stock_data() (+16 more)

### Community 7 - "Community 7"
Cohesion: 0.08
Nodes (21): aggregate_monthly(), aggregate_weekly(), DataAggregator, add_daily_indicators(), add_relative_strength(), add_weekly_indicators(), build(), IndicatorBundle (+13 more)

### Community 8 - "Community 8"
Cohesion: 0.1
Nodes (19): OHLCVCleaner, OHLCVResampler, Data cleaning and corporate action adjustment. All timeframes are derived intern, Clean and adjust raw OHLCV data., Fill gaps in trading days (holidays etc.) using forward fill — max 3 days., Replace negative or zero volume with NaN then ffill., Derive weekly, monthly, quarterly, yearly candles from daily data.     Never cal, DataValidationError (+11 more)

### Community 9 - "Community 9"
Cohesion: 0.12
Nodes (22): DataProvider, Provider-agnostic interface for fetching OHLCV data and stock metadata.     Impl, Return True if provider is reachable. Default implementation always True., DataProvider, ConfigurationError, DataProviderError, Platform misconfiguration detected., External data provider failed to return data. (+14 more)

### Community 10 - "Community 10"
Cohesion: 0.11
Nodes (11): ABC, compute(), name(), DataFetcher, Fetches ONLY missing daily data from Yahoo Finance.         Handles provider-spe, get_provider_symbol(), normalize_internal_symbol(), ProviderAdapter (+3 more)

### Community 11 - "Community 11"
Cohesion: 0.15
Nodes (12): BaseSettings, APISettings, BacktestSettings, DatabaseSettings, get_settings(), _merge_yaml_into_env(), PipelineSettings, ProviderSettings (+4 more)

### Community 12 - "Community 12"
Cohesion: 0.17
Nodes (8): Requested strategy is not registered., StrategyNotFoundError, Auto-discovery strategy registry. Scans the strategies/ package at startup. User, Singleton registry that auto-discovers and holds all BaseStrategy subclasses., Import every module in strategies/ and register concrete BaseStrategy subclasses, StrategyRegistry, ReplayPage(), list_strategies()

### Community 13 - "Community 13"
Cohesion: 0.33
Nodes (1): _serialize_recommendation()

### Community 14 - "Community 14"
Cohesion: 0.4
Nodes (0): 

### Community 15 - "Community 15"
Cohesion: 0.67
Nodes (2): getConvictionClass(), RecCard()

### Community 16 - "Community 16"
Cohesion: 0.67
Nodes (0): 

### Community 17 - "Community 17"
Cohesion: 0.67
Nodes (0): 

### Community 18 - "Community 18"
Cohesion: 1.0
Nodes (0): 

### Community 19 - "Community 19"
Cohesion: 1.0
Nodes (0): 

### Community 20 - "Community 20"
Cohesion: 1.0
Nodes (0): 

### Community 21 - "Community 21"
Cohesion: 1.0
Nodes (0): 

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (0): 

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (0): 

### Community 24 - "Community 24"
Cohesion: 1.0
Nodes (0): 

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (0): 

### Community 26 - "Community 26"
Cohesion: 1.0
Nodes (1): Convert a canonical internal symbol to the provider's specific format.

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (1): Name of the provider (e.g., 'yahoo', 'groww').

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (1): Cleans up a symbol to its canonical form (no whitespace, uppercase, no suffixes)

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (1): Gets the provider-specific symbol, utilizing caching to prevent redundant format

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (0): 

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (1): Converts daily OHLCV DataFrame to Weekly.

### Community 32 - "Community 32"
Cohesion: 1.0
Nodes (1): Converts daily OHLCV DataFrame to Monthly.

### Community 33 - "Community 33"
Cohesion: 1.0
Nodes (0): 

### Community 34 - "Community 34"
Cohesion: 1.0
Nodes (1): Unique provider identifier e.g. 'yfinance'.

### Community 35 - "Community 35"
Cohesion: 1.0
Nodes (1): Fetch OHLCV data for a single symbol.          Returns:             DataFrame wi

### Community 36 - "Community 36"
Cohesion: 1.0
Nodes (1): Fetch OHLCV for multiple symbols efficiently (batch/parallel where supported).

### Community 37 - "Community 37"
Cohesion: 1.0
Nodes (1): Fetch company metadata: name, sector, industry, market cap, ISIN.         Return

### Community 38 - "Community 38"
Cohesion: 1.0
Nodes (0): 

### Community 39 - "Community 39"
Cohesion: 1.0
Nodes (0): 

### Community 40 - "Community 40"
Cohesion: 1.0
Nodes (0): 

### Community 41 - "Community 41"
Cohesion: 1.0
Nodes (0): 

### Community 42 - "Community 42"
Cohesion: 1.0
Nodes (0): 

### Community 43 - "Community 43"
Cohesion: 1.0
Nodes (0): 

### Community 44 - "Community 44"
Cohesion: 1.0
Nodes (0): 

### Community 45 - "Community 45"
Cohesion: 1.0
Nodes (0): 

### Community 46 - "Community 46"
Cohesion: 1.0
Nodes (0): 

### Community 47 - "Community 47"
Cohesion: 1.0
Nodes (0): 

### Community 48 - "Community 48"
Cohesion: 1.0
Nodes (0): 

### Community 49 - "Community 49"
Cohesion: 1.0
Nodes (0): 

### Community 50 - "Community 50"
Cohesion: 1.0
Nodes (1): Inject YAML values as env vars if not already set (env vars take priority).

### Community 51 - "Community 51"
Cohesion: 1.0
Nodes (1): SQLAlchemy ORM models. All tables prefixed with `sw_` to avoid collisions if sha

### Community 52 - "Community 52"
Cohesion: 1.0
Nodes (1): Adds standard daily indicators to a daily OHLCV dataframe.

### Community 53 - "Community 53"
Cohesion: 1.0
Nodes (1): Adds standard weekly indicators to a weekly OHLCV dataframe.

### Community 54 - "Community 54"
Cohesion: 1.0
Nodes (1): Inject YAML values as env vars if not already set (env vars take priority).

## Knowledge Gaps
- **63 isolated node(s):** `Trade domain model for backtesting.`, `Pydantic-settings based configuration management. Loads from config.yaml, then o`, `Inject YAML values as env vars if not already set (env vars take priority).`, `Domain exception hierarchy. All platform exceptions flow from SwingBaseError so`, `Root exception for the entire platform.` (+58 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 18`** (2 nodes): `Stocks.jsx`, `Stocks()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (1 nodes): `vite.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (1 nodes): `main.jsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (1 nodes): `Convert a canonical internal symbol to the provider's specific format.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (1 nodes): `Name of the provider (e.g., 'yahoo', 'groww').`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (1 nodes): `Cleans up a symbol to its canonical form (no whitespace, uppercase, no suffixes)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (1 nodes): `Gets the provider-specific symbol, utilizing caching to prevent redundant format`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (1 nodes): `Converts daily OHLCV DataFrame to Weekly.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (1 nodes): `Converts daily OHLCV DataFrame to Monthly.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 34`** (1 nodes): `Unique provider identifier e.g. 'yfinance'.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 35`** (1 nodes): `Fetch OHLCV data for a single symbol.          Returns:             DataFrame wi`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 36`** (1 nodes): `Fetch OHLCV for multiple symbols efficiently (batch/parallel where supported).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 37`** (1 nodes): `Fetch company metadata: name, sector, industry, market cap, ISIN.         Return`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 40`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 41`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 42`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 43`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 44`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 45`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 46`** (1 nodes): `read_exception.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (1 nodes): `read_scanner_log.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 48`** (1 nodes): `read_task_log.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 50`** (1 nodes): `Inject YAML values as env vars if not already set (env vars take priority).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (1 nodes): `SQLAlchemy ORM models. All tables prefixed with `sw_` to avoid collisions if sha`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 52`** (1 nodes): `Adds standard daily indicators to a daily OHLCV dataframe.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 53`** (1 nodes): `Adds standard weekly indicators to a weekly OHLCV dataframe.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 54`** (1 nodes): `Inject YAML values as env vars if not already set (env vars take priority).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `OHLCVRepository` connect `Community 5` to `Community 0`, `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 7`, `Community 8`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Why does `get_sync_session()` connect `Community 6` to `Community 0`, `Community 5`, `Community 7`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Why does `Stock` connect `Community 0` to `Community 1`, `Community 2`, `Community 3`, `Community 4`, `Community 7`, `Community 8`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Are the 28 inferred relationships involving `RecommendationScanner` (e.g. with `FastAPI application entry point. Mounts all routers, configures CORS, lifespan e` and `DynamicLookbackEngine`) actually correct?**
  _`RecommendationScanner` has 28 INFERRED edges - model-reasoned connections that need verification._
- **Are the 29 inferred relationships involving `str` (e.g. with `health()` and `list_saved_results()`) actually correct?**
  _`str` has 29 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `OHLCVRepository` (e.g. with `BacktestConfig` and `BacktestRunResult`) actually correct?**
  _`OHLCVRepository` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `Stock` (e.g. with `BacktestConfig` and `BacktestRunResult`) actually correct?**
  _`Stock` has 31 INFERRED edges - model-reasoned connections that need verification._