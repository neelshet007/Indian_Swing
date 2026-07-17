# Graph Report - C:\Indian_Swing  (2026-07-17)

## Corpus Check
- 125 files · ~137,239 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 765 nodes · 1646 edges · 84 communities detected
- Extraction: 47% EXTRACTED · 53% INFERRED · 0% AMBIGUOUS · INFERRED: 866 edges (avg confidence: 0.63)
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
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]
- [[_COMMUNITY_Community 77|Community 77]]
- [[_COMMUNITY_Community 78|Community 78]]
- [[_COMMUNITY_Community 79|Community 79]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 81|Community 81]]
- [[_COMMUNITY_Community 82|Community 82]]
- [[_COMMUNITY_Community 83|Community 83]]

## God Nodes (most connected - your core abstractions)
1. `RecommendationScanner` - 41 edges
2. `get_sync_session()` - 39 edges
3. `OHLCVRepository` - 36 edges
4. `Stock` - 34 edges
5. `BaseIndicator` - 31 edges
6. `DataPipeline` - 30 edges
7. `SignalDirection` - 28 edges
8. `RiskLevel` - 28 edges
9. `SignalQuality` - 28 edges
10. `Base` - 28 edges

## Surprising Connections (you probably didn't know these)
- `SIVCSScanner` --uses--> `DataAggregator`  [INFERRED]
  C:\Indian_Swing\indian_swing\core\scanner.py → C:\Indian_Swing\indian_swing\data\aggregator.py
- `IndicatorRequirement` --calls--> `indicator_requirements()`  [INFERRED]
  C:\Indian_Swing\indian_swing\strategies\base.py → C:\Indian_Swing\indian_swing\strategies\institutional_vcp.py
- `StrategyDataRequirements` --calls--> `data_requirements()`  [INFERRED]
  C:\Indian_Swing\indian_swing\strategies\base.py → C:\Indian_Swing\indian_swing\strategies\institutional_vcp.py
- `check_rules()` --calls--> `get_sync_session()`  [INFERRED]
  C:\Indian_Swing\check_rules_stats.py → C:\Indian_Swing\indian_swing\database\connection.py
- `check_rules()` --calls--> `add_daily_indicators()`  [INFERRED]
  C:\Indian_Swing\check_rules_stats.py → C:\Indian_Swing\indian_swing\indicators\calculator.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (29): BaseRepository, StrategyContext, BaseStrategy, check(), check(), check_rules(), data_requirements(), _detect_vcp() (+21 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (50): check_db_rows(), check_jobs(), check_pfc(), check_pfc_history(), check_stock_data(), check_stock_details(), get_sync_session(), SQLAlchemy sync engine wrapped for async usage via run_in_executor. Python 3.14 (+42 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (32): DataProvider, Provider-agnostic interface for fetching OHLCV data and stock metadata.     Impl, Return True if provider is reachable. Default implementation always True., DataProvider, Exception, ConfigurationError, DataProviderError, Platform misconfiguration detected. (+24 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (35): IndicatorCalculator, CLI entry point using Typer. Usage:   swing db init   swing data download --univ, List all discovered strategies., List all discovered strategies., List all discovered strategies., Initialize database tables., Download OHLCV data for the specified universe., Download OHLCV data for the specified universe. (+27 more)

### Community 4 - "Community 4"
Cohesion: 0.07
Nodes (34): BacktestRequest, list_saved_results(), run_backtest(), BaseModel, data_download(), db_init(), list_strategies(), scan_run() (+26 more)

### Community 5 - "Community 5"
Cohesion: 0.06
Nodes (40): ReplayEngine, ReplaySession, BacktestError, DatabaseError, DataError, DataNotFoundError, DuplicateRecordError, EngineError (+32 more)

### Community 6 - "Community 6"
Cohesion: 0.08
Nodes (32): BaseIndicator, All indicators extend this.     Subclasses implement compute() using vectorized, BaseIndicator, Replay Engine — sync DB version., ReplayState, CCI, Momentum indicators: RSI, Stochastic, Williams %R, CCI, ROC., ROC (+24 more)

### Community 7 - "Community 7"
Cohesion: 0.09
Nodes (35): BaseStrategy, compute(), data_requirements(), IndicatorRequirement, name(), BaseStrategy contract. Strategies inherit this, implement generate_signals(), an, Override to provide configurable defaults., Return False if DataFrame is insufficient for this strategy. (+27 more)

### Community 8 - "Community 8"
Cohesion: 0.07
Nodes (24): aggregate_monthly(), aggregate_weekly(), DataAggregator, OHLCVCleaner, OHLCVResampler, Data cleaning and corporate action adjustment. All timeframes are derived intern, Clean and adjust raw OHLCV data., Fill gaps in trading days (holidays etc.) using forward fill — max 3 days. (+16 more)

### Community 9 - "Community 9"
Cohesion: 0.07
Nodes (24): ABC, DataFetcher, Fetches ONLY missing daily data from Yahoo Finance.         Handles provider-spe, get_provider_symbol(), normalize_internal_symbol(), ProviderAdapter, Centralized Symbol Management Layer.     Ensures internal symbols are canonical,, SymbolManager (+16 more)

### Community 10 - "Community 10"
Cohesion: 0.14
Nodes (16): add_column(), dispose_engine(), get_engine(), get_session(), get_session_factory(), _get_sync_url(), init_db(), _heal_stale_scan_jobs() (+8 more)

### Community 11 - "Community 11"
Cohesion: 0.14
Nodes (12): BaseSettings, APISettings, BacktestSettings, DatabaseSettings, get_settings(), _merge_yaml_into_env(), PipelineSettings, ProviderSettings (+4 more)

### Community 12 - "Community 12"
Cohesion: 0.22
Nodes (12): add_daily_indicators(), add_relative_strength(), add_weekly_indicators(), build(), IndicatorBundle, _require_length(), validate_required_columns(), InsufficientDataError (+4 more)

### Community 13 - "Community 13"
Cohesion: 0.22
Nodes (7): Requested strategy is not registered., StrategyNotFoundError, Auto-discovery strategy registry. Scans the strategies/ package at startup. User, Singleton registry that auto-discovers and holds all BaseStrategy subclasses., Import every module in strategies/ and register concrete BaseStrategy subclasses, StrategyRegistry, list_strategies()

### Community 14 - "Community 14"
Cohesion: 0.27
Nodes (6): fmt(), fmtCr(), fmtK(), fmtNum(), fmtPct(), TradeDetail()

### Community 15 - "Community 15"
Cohesion: 0.25
Nodes (1): _serialize_scan()

### Community 16 - "Community 16"
Cohesion: 0.4
Nodes (0): 

### Community 17 - "Community 17"
Cohesion: 0.67
Nodes (2): getConvictionClass(), RecCard()

### Community 18 - "Community 18"
Cohesion: 0.5
Nodes (2): FOTrading(), useFnoEngine()

### Community 19 - "Community 19"
Cohesion: 0.67
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
Nodes (0): 

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (0): 

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (0): 

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (0): 

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (0): 

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (0): 

### Community 32 - "Community 32"
Cohesion: 1.0
Nodes (0): 

### Community 33 - "Community 33"
Cohesion: 1.0
Nodes (0): 

### Community 34 - "Community 34"
Cohesion: 1.0
Nodes (0): 

### Community 35 - "Community 35"
Cohesion: 1.0
Nodes (0): 

### Community 36 - "Community 36"
Cohesion: 1.0
Nodes (0): 

### Community 37 - "Community 37"
Cohesion: 1.0
Nodes (0): 

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
Nodes (1): Convert a canonical internal symbol to the provider's specific format.

### Community 50 - "Community 50"
Cohesion: 1.0
Nodes (1): Name of the provider (e.g., 'yahoo', 'groww').

### Community 51 - "Community 51"
Cohesion: 1.0
Nodes (1): Cleans up a symbol to its canonical form (no whitespace, uppercase, no suffixes)

### Community 52 - "Community 52"
Cohesion: 1.0
Nodes (1): Gets the provider-specific symbol, utilizing caching to prevent redundant format

### Community 53 - "Community 53"
Cohesion: 1.0
Nodes (0): 

### Community 54 - "Community 54"
Cohesion: 1.0
Nodes (1): Converts daily OHLCV DataFrame to Weekly.

### Community 55 - "Community 55"
Cohesion: 1.0
Nodes (1): Converts daily OHLCV DataFrame to Monthly.

### Community 56 - "Community 56"
Cohesion: 1.0
Nodes (0): 

### Community 57 - "Community 57"
Cohesion: 1.0
Nodes (1): Unique provider identifier e.g. 'yfinance'.

### Community 58 - "Community 58"
Cohesion: 1.0
Nodes (1): Fetch OHLCV data for a single symbol.          Returns:             DataFrame wi

### Community 59 - "Community 59"
Cohesion: 1.0
Nodes (1): Fetch OHLCV for multiple symbols efficiently (batch/parallel where supported).

### Community 60 - "Community 60"
Cohesion: 1.0
Nodes (1): Fetch company metadata: name, sector, industry, market cap, ISIN.         Return

### Community 61 - "Community 61"
Cohesion: 1.0
Nodes (0): 

### Community 62 - "Community 62"
Cohesion: 1.0
Nodes (0): 

### Community 63 - "Community 63"
Cohesion: 1.0
Nodes (0): 

### Community 64 - "Community 64"
Cohesion: 1.0
Nodes (0): 

### Community 65 - "Community 65"
Cohesion: 1.0
Nodes (1): Send a list of recommendation dicts to the channel.          Each dict must cont

### Community 66 - "Community 66"
Cohesion: 1.0
Nodes (0): 

### Community 67 - "Community 67"
Cohesion: 1.0
Nodes (0): 

### Community 68 - "Community 68"
Cohesion: 1.0
Nodes (0): 

### Community 69 - "Community 69"
Cohesion: 1.0
Nodes (0): 

### Community 70 - "Community 70"
Cohesion: 1.0
Nodes (0): 

### Community 71 - "Community 71"
Cohesion: 1.0
Nodes (0): 

### Community 72 - "Community 72"
Cohesion: 1.0
Nodes (0): 

### Community 73 - "Community 73"
Cohesion: 1.0
Nodes (0): 

### Community 74 - "Community 74"
Cohesion: 1.0
Nodes (0): 

### Community 75 - "Community 75"
Cohesion: 1.0
Nodes (1): Inject YAML values as env vars if not already set (env vars take priority).

### Community 76 - "Community 76"
Cohesion: 1.0
Nodes (1): Centralized Symbol Management Layer.     Ensures internal symbols are canonical,

### Community 77 - "Community 77"
Cohesion: 1.0
Nodes (1): Cleans up a symbol to its canonical form (no whitespace, uppercase, no suffixes)

### Community 78 - "Community 78"
Cohesion: 1.0
Nodes (1): Gets the provider-specific symbol, utilizing caching to prevent redundant format

### Community 79 - "Community 79"
Cohesion: 1.0
Nodes (1): Inject YAML values as env vars if not already set (env vars take priority).

### Community 80 - "Community 80"
Cohesion: 1.0
Nodes (1): SQLAlchemy ORM models. All tables prefixed with `sw_` to avoid collisions if sha

### Community 81 - "Community 81"
Cohesion: 1.0
Nodes (1): Adds standard daily indicators to a daily OHLCV dataframe.

### Community 82 - "Community 82"
Cohesion: 1.0
Nodes (1): Adds standard weekly indicators to a weekly OHLCV dataframe.

### Community 83 - "Community 83"
Cohesion: 1.0
Nodes (1): Inject YAML values as env vars if not already set (env vars take priority).

## Knowledge Gaps
- **79 isolated node(s):** `Trade domain model for backtesting.`, `Pydantic-settings based configuration management. Loads from config.yaml, then o`, `Inject YAML values as env vars if not already set (env vars take priority).`, `Domain exception hierarchy. All platform exceptions flow from SwingBaseError so`, `Root exception for the entire platform.` (+74 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 20`** (2 nodes): `MarketCard.jsx`, `MarketCard()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (2 nodes): `MetricCard.jsx`, `MetricCard()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (2 nodes): `SystemStatusCard.jsx`, `SystemStatusCard()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (2 nodes): `TableCard.jsx`, `TableCard()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (2 nodes): `MonitoringCard.jsx`, `MonitoringCard()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (2 nodes): `MonitoringToolbar.jsx`, `MonitoringToolbar()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (2 nodes): `index.js`, `formatExpiryDate()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (2 nodes): `FnoAnalysis.jsx`, `FnoAnalysis()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (2 nodes): `FnoHistory.jsx`, `FnoHistory()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (2 nodes): `HomeDashboard.jsx`, `HomeDashboard()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (2 nodes): `Logs.jsx`, `Logs()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (1 nodes): `vite.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (1 nodes): `main.jsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (1 nodes): `executionService.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 34`** (1 nodes): `marketService.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 35`** (1 nodes): `optionChainService.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 36`** (1 nodes): `riskService.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 37`** (1 nodes): `backtester.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (1 nodes): `indicatorEngine.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (1 nodes): `positionBuilder.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 40`** (1 nodes): `regimeFilter.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 41`** (1 nodes): `strategyService.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 42`** (1 nodes): `strikeSelection.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 43`** (1 nodes): `index.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 44`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 45`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 46`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 48`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (1 nodes): `Convert a canonical internal symbol to the provider's specific format.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 50`** (1 nodes): `Name of the provider (e.g., 'yahoo', 'groww').`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (1 nodes): `Cleans up a symbol to its canonical form (no whitespace, uppercase, no suffixes)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 52`** (1 nodes): `Gets the provider-specific symbol, utilizing caching to prevent redundant format`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 53`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 54`** (1 nodes): `Converts daily OHLCV DataFrame to Weekly.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 55`** (1 nodes): `Converts daily OHLCV DataFrame to Monthly.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 56`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 57`** (1 nodes): `Unique provider identifier e.g. 'yfinance'.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 58`** (1 nodes): `Fetch OHLCV data for a single symbol.          Returns:             DataFrame wi`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 59`** (1 nodes): `Fetch OHLCV for multiple symbols efficiently (batch/parallel where supported).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 60`** (1 nodes): `Fetch company metadata: name, sector, industry, market cap, ISIN.         Return`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 61`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 62`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 63`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 64`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 65`** (1 nodes): `Send a list of recommendation dicts to the channel.          Each dict must cont`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 66`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 67`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 68`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 69`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 70`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 71`** (1 nodes): `read_exception.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 72`** (1 nodes): `read_scanner_log.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 73`** (1 nodes): `read_task_log.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 74`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 75`** (1 nodes): `Inject YAML values as env vars if not already set (env vars take priority).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 76`** (1 nodes): `Centralized Symbol Management Layer.     Ensures internal symbols are canonical,`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 77`** (1 nodes): `Cleans up a symbol to its canonical form (no whitespace, uppercase, no suffixes)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 78`** (1 nodes): `Gets the provider-specific symbol, utilizing caching to prevent redundant format`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 79`** (1 nodes): `Inject YAML values as env vars if not already set (env vars take priority).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 80`** (1 nodes): `SQLAlchemy ORM models. All tables prefixed with `sw_` to avoid collisions if sha`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 81`** (1 nodes): `Adds standard daily indicators to a daily OHLCV dataframe.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 82`** (1 nodes): `Adds standard weekly indicators to a weekly OHLCV dataframe.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 83`** (1 nodes): `Inject YAML values as env vars if not already set (env vars take priority).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_sync_session()` connect `Community 1` to `Community 0`, `Community 8`, `Community 10`, `Community 3`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Why does `OHLCVRepository` connect `Community 0` to `Community 3`, `Community 4`, `Community 5`, `Community 6`, `Community 8`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Why does `Stock` connect `Community 3` to `Community 0`, `Community 1`, `Community 4`, `Community 5`, `Community 6`, `Community 8`, `Community 10`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Are the 40 inferred relationships involving `str` (e.g. with `health()` and `list_saved_results()`) actually correct?**
  _`str` has 40 INFERRED edges - model-reasoned connections that need verification._
- **Are the 29 inferred relationships involving `RecommendationScanner` (e.g. with `FastAPI application entry point. Mounts all routers, configures CORS, lifespan e` and `Mark any ScanJob still in 'running' status after 2+ hours as 'failed'.     These`) actually correct?**
  _`RecommendationScanner` has 29 INFERRED edges - model-reasoned connections that need verification._
- **Are the 37 inferred relationships involving `get_sync_session()` (e.g. with `check_rules()` and `_heal_stale_scan_jobs()`) actually correct?**
  _`get_sync_session()` has 37 INFERRED edges - model-reasoned connections that need verification._
- **Are the 27 inferred relationships involving `OHLCVRepository` (e.g. with `BacktestConfig` and `BacktestRunResult`) actually correct?**
  _`OHLCVRepository` has 27 INFERRED edges - model-reasoned connections that need verification._