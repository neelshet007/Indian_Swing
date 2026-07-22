# Graph Report - C:\Indian_Swing  (2026-07-22)

## Corpus Check
- 143 files · ~203,746 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 855 nodes · 1960 edges · 90 communities detected
- Extraction: 46% EXTRACTED · 54% INFERRED · 0% AMBIGUOUS · INFERRED: 1054 edges (avg confidence: 0.63)
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
- [[_COMMUNITY_Community 84|Community 84]]
- [[_COMMUNITY_Community 85|Community 85]]
- [[_COMMUNITY_Community 86|Community 86]]
- [[_COMMUNITY_Community 87|Community 87]]
- [[_COMMUNITY_Community 88|Community 88]]
- [[_COMMUNITY_Community 89|Community 89]]

## God Nodes (most connected - your core abstractions)
1. `Stock` - 56 edges
2. `get_sync_session()` - 52 edges
3. `OHLCVRepository` - 50 edges
4. `ScanJob` - 46 edges
5. `RecommendationScanner` - 44 edges
6. `Recommendation` - 43 edges
7. `StockRepository` - 43 edges
8. `HistoricalScanManager` - 37 edges
9. `HistoricalScanSession` - 33 edges
10. `PaperTrade` - 33 edges

## Surprising Connections (you probably didn't know these)
- `check_rules()` --calls--> `InstitutionalVCP`  [INFERRED]
  C:\Indian_Swing\check_rules_stats.py → C:\Indian_Swing\indian_swing\strategies\institutional_vcp.py
- `check_rules()` --calls--> `add_daily_indicators()`  [INFERRED]
  C:\Indian_Swing\check_rules_stats.py → C:\Indian_Swing\indian_swing\indicators\calculator.py
- `ProgressPollingFilter` --uses--> `ScanJob`  [INFERRED]
  C:\Indian_Swing\indian_swing\api\main.py → C:\Indian_Swing\indian_swing\database\models.py
- `ProgressPollingFilter` --uses--> `RecommendationScanner`  [INFERRED]
  C:\Indian_Swing\indian_swing\api\main.py → C:\Indian_Swing\indian_swing\recommendations\scanner.py
- `_heal_stale_scan_jobs()` --calls--> `get_sync_session()`  [INFERRED]
  C:\Indian_Swing\indian_swing\api\main.py → C:\Indian_Swing\indian_swing\database\connection.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.04
Nodes (54): _calculate_metrics(), list_saved_results(), check_db_rows(), check(), check_jobs(), check_pfc(), check_pfc_history(), check() (+46 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (70): HistoricalScanManager, Evaluate exit triggers for an active trade., Create pending paper trades for all recommendations generated in scan_uuid., Create pending paper trades for all recommendations generated in scan_uuid., Compute final statistics and metrics for completed runs., Validate date format DD/MM/YY and return date object., Generate a professionally formatted Excel workbook representing the trading jour, Compute final statistics and metrics for completed runs. (+62 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (46): BaseIndicator, All indicators extend this.     Subclasses implement compute() using vectorized, BaseIndicator, Replay Engine — sync DB version., ReplayEngine, ReplaySession, ReplayState, Requested replay session does not exist. (+38 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (42): BacktestRequest, run_backtest(), BaseStrategy, StrategySignal, data_download(), db_init(), list_strategies(), scan_historical() (+34 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (42): data_requirements(), IndicatorRequirement, StrategyContext, StrategyDataRequirements, BaseStrategy, analyze_breakout(), BreakoutAnalyzer, Enum (+34 more)

### Community 5 - "Community 5"
Cohesion: 0.06
Nodes (41): DataProvider, Provider-agnostic interface for fetching OHLCV data and stock metadata.     Impl, Return True if provider is reachable. Default implementation always True., DataProvider, Exception, BacktestError, ConfigurationError, DatabaseError (+33 more)

### Community 6 - "Community 6"
Cohesion: 0.08
Nodes (15): aggregate_monthly(), aggregate_weekly(), DataAggregator, DataFetcher, Fetches ONLY missing daily data from Yahoo Finance.         Handles provider-spe, MarketDataRepository, SIVCSScanner, get_provider_symbol() (+7 more)

### Community 7 - "Community 7"
Cohesion: 0.14
Nodes (27): compute(), name(), Base indicator with result caching. All indicators are stateless, vectorized, an, BaseModel, DeclarativeBase, Presentation-layer only. Returns universe membership badges for a symbol.     D, Returns only active, ready, or open recommendations from the database., Retrieve full paginated history for audit screens. (+19 more)

### Community 8 - "Community 8"
Cohesion: 0.11
Nodes (17): OHLCVCleaner, OHLCVResampler, Data cleaning and corporate action adjustment. All timeframes are derived intern, Clean and adjust raw OHLCV data., Fill gaps in trading days (holidays etc.) using forward fill — max 3 days., Replace negative or zero volume with NaN then ffill., Derive weekly, monthly, quarterly, yearly candles from daily data.     Never cal, DataValidationError (+9 more)

### Community 9 - "Community 9"
Cohesion: 0.14
Nodes (20): add_daily_indicators(), add_relative_strength(), add_weekly_indicators(), build(), IndicatorBundle, IndicatorCalculator, _require_length(), validate_required_columns() (+12 more)

### Community 10 - "Community 10"
Cohesion: 0.11
Nodes (15): ABC, _confidence_label(), _escape_html(), NotificationChannel, notify_recommendations(), Telegram notification channel for IndianSwing.  Architecture ------------ Th, Send recommendations to Telegram.  Never raises., Split a long message at newline boundaries, respecting the 4096-char limit. (+7 more)

### Community 11 - "Community 11"
Cohesion: 0.14
Nodes (12): BaseSettings, APISettings, BacktestSettings, DatabaseSettings, get_settings(), _merge_yaml_into_env(), PipelineSettings, ProviderSettings (+4 more)

### Community 12 - "Community 12"
Cohesion: 0.18
Nodes (14): add_column(), dispose_engine(), get_engine(), get_session(), get_session_factory(), _get_sync_url(), init_db(), _heal_stale_scan_jobs() (+6 more)

### Community 13 - "Community 13"
Cohesion: 0.15
Nodes (3): BaseRepository, RecommendationRepository, SignalRepository

### Community 14 - "Community 14"
Cohesion: 0.22
Nodes (10): calculate_greeks(), FnoStrategyEngine, _is_macro_event_day(), normal_cdf(), normal_pdf(), Returns (is_safe, reason). True means market is safe to trade., High-precision numerical approximation of standard normal CDF., Standard normal probability density function. (+2 more)

### Community 15 - "Community 15"
Cohesion: 0.27
Nodes (6): fmt(), fmtCr(), fmtK(), fmtNum(), fmtPct(), TradeDetail()

### Community 16 - "Community 16"
Cohesion: 0.43
Nodes (2): UniverseManager, UniverseStock

### Community 17 - "Community 17"
Cohesion: 0.29
Nodes (0): 

### Community 18 - "Community 18"
Cohesion: 0.33
Nodes (1): ErrorBoundary

### Community 19 - "Community 19"
Cohesion: 0.33
Nodes (1): _serialize_recommendation()

### Community 20 - "Community 20"
Cohesion: 0.4
Nodes (2): FOTrading(), useFnoEngine()

### Community 21 - "Community 21"
Cohesion: 0.4
Nodes (1): ScanAnalytics()

### Community 22 - "Community 22"
Cohesion: 0.67
Nodes (2): getConvictionClass(), RecCard()

### Community 23 - "Community 23"
Cohesion: 0.67
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
Nodes (0): 

### Community 50 - "Community 50"
Cohesion: 1.0
Nodes (0): 

### Community 51 - "Community 51"
Cohesion: 1.0
Nodes (0): 

### Community 52 - "Community 52"
Cohesion: 1.0
Nodes (0): 

### Community 53 - "Community 53"
Cohesion: 1.0
Nodes (0): 

### Community 54 - "Community 54"
Cohesion: 1.0
Nodes (0): 

### Community 55 - "Community 55"
Cohesion: 1.0
Nodes (0): 

### Community 56 - "Community 56"
Cohesion: 1.0
Nodes (0): 

### Community 57 - "Community 57"
Cohesion: 1.0
Nodes (1): Convert a canonical internal symbol to the provider's specific format.

### Community 58 - "Community 58"
Cohesion: 1.0
Nodes (1): Name of the provider (e.g., 'yahoo', 'groww').

### Community 59 - "Community 59"
Cohesion: 1.0
Nodes (1): Cleans up a symbol to its canonical form (no whitespace, uppercase, no suffixes)

### Community 60 - "Community 60"
Cohesion: 1.0
Nodes (1): Gets the provider-specific symbol, utilizing caching to prevent redundant format

### Community 61 - "Community 61"
Cohesion: 1.0
Nodes (0): 

### Community 62 - "Community 62"
Cohesion: 1.0
Nodes (1): Converts daily OHLCV DataFrame to Weekly.

### Community 63 - "Community 63"
Cohesion: 1.0
Nodes (1): Converts daily OHLCV DataFrame to Monthly.

### Community 64 - "Community 64"
Cohesion: 1.0
Nodes (0): 

### Community 65 - "Community 65"
Cohesion: 1.0
Nodes (1): Unique provider identifier e.g. 'yfinance'.

### Community 66 - "Community 66"
Cohesion: 1.0
Nodes (1): Fetch OHLCV data for a single symbol.          Returns:             DataFrame wi

### Community 67 - "Community 67"
Cohesion: 1.0
Nodes (1): Fetch OHLCV for multiple symbols efficiently (batch/parallel where supported).

### Community 68 - "Community 68"
Cohesion: 1.0
Nodes (1): Fetch company metadata: name, sector, industry, market cap, ISIN.         Return

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
Nodes (1): Compute indicator on OHLCV DataFrame.          Args:             df: OHLCV DataF

### Community 73 - "Community 73"
Cohesion: 1.0
Nodes (0): 

### Community 74 - "Community 74"
Cohesion: 1.0
Nodes (1): Send a list of recommendation dicts to the channel.          Each dict must co

### Community 75 - "Community 75"
Cohesion: 1.0
Nodes (0): 

### Community 76 - "Community 76"
Cohesion: 1.0
Nodes (0): 

### Community 77 - "Community 77"
Cohesion: 1.0
Nodes (0): 

### Community 78 - "Community 78"
Cohesion: 1.0
Nodes (0): 

### Community 79 - "Community 79"
Cohesion: 1.0
Nodes (1): Analyzes the quality of a breakout candle, checks the closing position of the pr

### Community 80 - "Community 80"
Cohesion: 1.0
Nodes (1): Classifies the current market regime (Bull, Bear, Sideways, Correction, Recovery

### Community 81 - "Community 81"
Cohesion: 1.0
Nodes (1): Validates trade and portfolio risk guidelines, checking sector exposure limits

### Community 82 - "Community 82"
Cohesion: 1.0
Nodes (1): Computes a unified, fully explainable institutional score (0-100)         based

### Community 83 - "Community 83"
Cohesion: 1.0
Nodes (1): Enriches the weekly dataframe with institutional stage classifications,

### Community 84 - "Community 84"
Cohesion: 1.0
Nodes (0): 

### Community 85 - "Community 85"
Cohesion: 1.0
Nodes (0): 

### Community 86 - "Community 86"
Cohesion: 1.0
Nodes (0): 

### Community 87 - "Community 87"
Cohesion: 1.0
Nodes (0): 

### Community 88 - "Community 88"
Cohesion: 1.0
Nodes (0): 

### Community 89 - "Community 89"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **77 isolated node(s):** `Trade domain model for backtesting.`, `Pydantic-settings based configuration management. Loads from config.yaml, then o`, `Inject YAML values as env vars if not already set (env vars take priority).`, `Domain exception hierarchy. All platform exceptions flow from SwingBaseError so`, `Root exception for the entire platform.` (+72 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 24`** (2 nodes): `MarketCard.jsx`, `MarketCard()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (2 nodes): `MetricCard.jsx`, `MetricCard()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (2 nodes): `SystemStatusCard.jsx`, `SystemStatusCard()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (2 nodes): `TableCard.jsx`, `TableCard()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (2 nodes): `UniverseBadge.jsx`, `UniverseBadge()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (2 nodes): `MonitoringCard.jsx`, `MonitoringCard()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (2 nodes): `MonitoringToolbar.jsx`, `MonitoringToolbar()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (2 nodes): `index.js`, `formatExpiryDate()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (2 nodes): `FnoAnalysis.jsx`, `FnoAnalysis()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (2 nodes): `FnoHistory.jsx`, `FnoHistory()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 34`** (2 nodes): `FnoSavedDetail.jsx`, `FnoSavedDetail()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 35`** (2 nodes): `FnoSavedList.jsx`, `FnoSavedList()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 36`** (2 nodes): `HistoricalScan.jsx`, `HistoricalScan()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 37`** (2 nodes): `HomeDashboard.jsx`, `HomeDashboard()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (2 nodes): `Logs.jsx`, `Logs()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (1 nodes): `vite.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 40`** (1 nodes): `main.jsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 41`** (1 nodes): `executionService.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 42`** (1 nodes): `marketService.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 43`** (1 nodes): `optionChainService.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 44`** (1 nodes): `riskService.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 45`** (1 nodes): `backtester.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 46`** (1 nodes): `indicatorEngine.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (1 nodes): `positionBuilder.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 48`** (1 nodes): `regimeFilter.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (1 nodes): `strategyService.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 50`** (1 nodes): `strikeSelection.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (1 nodes): `index.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 52`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 53`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 54`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 55`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 56`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 57`** (1 nodes): `Convert a canonical internal symbol to the provider's specific format.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 58`** (1 nodes): `Name of the provider (e.g., 'yahoo', 'groww').`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 59`** (1 nodes): `Cleans up a symbol to its canonical form (no whitespace, uppercase, no suffixes)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 60`** (1 nodes): `Gets the provider-specific symbol, utilizing caching to prevent redundant format`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 61`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 62`** (1 nodes): `Converts daily OHLCV DataFrame to Weekly.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 63`** (1 nodes): `Converts daily OHLCV DataFrame to Monthly.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 64`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 65`** (1 nodes): `Unique provider identifier e.g. 'yfinance'.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 66`** (1 nodes): `Fetch OHLCV data for a single symbol.          Returns:             DataFrame wi`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 67`** (1 nodes): `Fetch OHLCV for multiple symbols efficiently (batch/parallel where supported).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 68`** (1 nodes): `Fetch company metadata: name, sector, industry, market cap, ISIN.         Return`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 69`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 70`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 71`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 72`** (1 nodes): `Compute indicator on OHLCV DataFrame.          Args:             df: OHLCV DataF`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 73`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 74`** (1 nodes): `Send a list of recommendation dicts to the channel.          Each dict must co`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 75`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 76`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 77`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 78`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 79`** (1 nodes): `Analyzes the quality of a breakout candle, checks the closing position of the pr`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 80`** (1 nodes): `Classifies the current market regime (Bull, Bear, Sideways, Correction, Recovery`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 81`** (1 nodes): `Validates trade and portfolio risk guidelines, checking sector exposure limits`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 82`** (1 nodes): `Computes a unified, fully explainable institutional score (0-100)         based`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 83`** (1 nodes): `Enriches the weekly dataframe with institutional stage classifications,`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 84`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 85`** (1 nodes): `check_aaron.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 86`** (1 nodes): `read_exception.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 87`** (1 nodes): `read_scanner_log.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 88`** (1 nodes): `read_task_log.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 89`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_sync_session()` connect `Community 0` to `Community 1`, `Community 12`, `Community 4`, `Community 6`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Why does `OHLCVRepository` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 8`, `Community 13`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Why does `Stock` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 6`, `Community 7`, `Community 8`, `Community 16`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Are the 54 inferred relationships involving `Stock` (e.g. with `Get progress of the active historical scan session.` and `List completed historical scans.`) actually correct?**
  _`Stock` has 54 INFERRED edges - model-reasoned connections that need verification._
- **Are the 50 inferred relationships involving `get_sync_session()` (e.g. with `check_rules()` and `_heal_stale_scan_jobs()`) actually correct?**
  _`get_sync_session()` has 50 INFERRED edges - model-reasoned connections that need verification._
- **Are the 41 inferred relationships involving `OHLCVRepository` (e.g. with `Presentation-layer only. Returns universe membership badges for a stock symbol.` and `BacktestConfig`) actually correct?**
  _`OHLCVRepository` has 41 INFERRED edges - model-reasoned connections that need verification._
- **Are the 42 inferred relationships involving `str` (e.g. with `health()` and `list_saved_results()`) actually correct?**
  _`str` has 42 INFERRED edges - model-reasoned connections that need verification._