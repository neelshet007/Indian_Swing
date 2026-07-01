# Graph Report - C:\Indian_Swing  (2026-07-01)

## Corpus Check
- 62 files · ~83,826 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 474 nodes · 1023 edges · 41 communities detected
- Extraction: 54% EXTRACTED · 46% INFERRED · 0% AMBIGUOUS · INFERRED: 467 edges (avg confidence: 0.59)
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

## God Nodes (most connected - your core abstractions)
1. `BaseIndicator` - 30 edges
2. `OHLCVRepository` - 27 edges
3. `ATR` - 27 edges
4. `RecommendationScanner` - 27 edges
5. `Stock` - 24 edges
6. `BacktestRunner` - 22 edges
7. `DataPipeline` - 22 edges
8. `BaseStrategy` - 22 edges
9. `StrategySignal` - 20 edges
10. `StockRepository` - 19 edges

## Surprising Connections (you probably didn't know these)
- `Performance metrics engine. All institutional-grade metrics: CAGR, Sharpe, Sorti` --uses--> `Trade`  [INFERRED]
  C:\Indian_Swing\indian_swing\backtesting\metrics.py → C:\Indian_Swing\indian_swing\backtesting\trade.py
- `Compute all backtest performance metrics from trade list and equity curve.` --uses--> `Trade`  [INFERRED]
  C:\Indian_Swing\indian_swing\backtesting\metrics.py → C:\Indian_Swing\indian_swing\backtesting\trade.py
- `Returns {YYYY-MM: return_pct} for each month.` --uses--> `Trade`  [INFERRED]
  C:\Indian_Swing\indian_swing\backtesting\metrics.py → C:\Indian_Swing\indian_swing\backtesting\trade.py
- `lifespan()` --calls--> `dispose_engine()`  [INFERRED]
  C:\Indian_Swing\indian_swing\api\main.py → C:\Indian_Swing\indian_swing\database\connection.py
- `FastAPI application entry point. Mounts all routers, configures CORS, lifespan e` --uses--> `RecommendationScanner`  [INFERRED]
  C:\Indian_Swing\indian_swing\api\main.py → C:\Indian_Swing\indian_swing\recommendations\scanner.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (54): BaseIndicator, BaseStrategy, Return False if DataFrame is insufficient for this strategy., All indicators extend this.     Subclasses implement compute() using vectorized, Standardized output from every strategy — the engine only knows this type., All strategies must inherit from this.     Implement generate_signals() and opti, Unique strategy identifier e.g. 'EMABreakout'., Human-readable strategy description. (+46 more)

### Community 1 - "Community 1"
Cohesion: 0.09
Nodes (26): dispose_engine(), get_engine(), get_session(), get_session_factory(), get_sync_session(), _get_sync_url(), init_db(), SQLAlchemy sync engine wrapped for async usage via run_in_executor. Python 3.14 (+18 more)

### Community 2 - "Community 2"
Cohesion: 0.09
Nodes (21): OHLCVCleaner, OHLCVResampler, Data cleaning and corporate action adjustment. All timeframes are derived intern, Clean and adjust raw OHLCV data., Fill gaps in trading days (holidays etc.) using forward fill — max 3 days., Replace negative or zero volume with NaN then ffill., Derive weekly, monthly, quarterly, yearly candles from daily data.     Never cal, DataValidationError (+13 more)

### Community 3 - "Community 3"
Cohesion: 0.1
Nodes (14): BacktestRequest, run_backtest(), BacktestResult, Stock, OHLCVRepository, BacktestConfig, BacktestRunner, BacktestRunResult (+6 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (34): BaseModel, Exception, BacktestError, DatabaseError, DataError, DataNotFoundError, DuplicateRecordError, EngineError (+26 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (12): list_saved_results(), BaseRepository, Requested strategy is not registered., StrategyNotFoundError, Auto-discovery strategy registry. Scans the strategies/ package at startup. User, Singleton registry that auto-discovers and holds all BaseStrategy subclasses., Import every module in strategies/ and register concrete BaseStrategy subclasses, StrategyRegistry (+4 more)

### Community 6 - "Community 6"
Cohesion: 0.11
Nodes (16): ReplayEngine, ReplaySession, _uuid(), _rec_dict(), create_replay_session(), get_replay_state(), jump_to_date(), replay_websocket() (+8 more)

### Community 7 - "Community 7"
Cohesion: 0.13
Nodes (20): DataProvider, Provider-agnostic interface for fetching OHLCV data and stock metadata.     Impl, Return True if provider is reachable. Default implementation always True., DataProvider, ConfigurationError, DataProviderError, Platform misconfiguration detected., External data provider failed to return data. (+12 more)

### Community 8 - "Community 8"
Cohesion: 0.11
Nodes (20): data_download(), db_init(), list_strategies(), CLI entry point using Typer. Usage:   swing db init   swing data download --univ, List all discovered strategies., List all discovered strategies., Initialize database tables., Download OHLCV data for the specified universe. (+12 more)

### Community 9 - "Community 9"
Cohesion: 0.16
Nodes (12): BaseSettings, APISettings, BacktestSettings, DatabaseSettings, get_settings(), _merge_yaml_into_env(), PipelineSettings, ProviderSettings (+4 more)

### Community 10 - "Community 10"
Cohesion: 0.15
Nodes (4): ABC, compute(), name(), BaseStrategy contract. Strategies inherit this, implement generate_signals(), an

### Community 11 - "Community 11"
Cohesion: 0.27
Nodes (11): compute_metrics(), compute_monthly_returns(), _empty_metrics(), _equity_series(), _max_drawdown(), _profit_factor(), Performance metrics engine. All institutional-grade metrics: CAGR, Sharpe, Sorti, Compute all backtest performance metrics from trade list and equity curve. (+3 more)

### Community 12 - "Community 12"
Cohesion: 0.47
Nodes (3): ConfidenceBadge(), getConvictionClass(), RecCard()

### Community 13 - "Community 13"
Cohesion: 0.4
Nodes (0): 

### Community 14 - "Community 14"
Cohesion: 0.6
Nodes (4): get_ohlcv(), get_stock(), list_stocks(), _stock_dict()

### Community 15 - "Community 15"
Cohesion: 0.67
Nodes (0): 

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
Nodes (0): 

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (0): 

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (1): Unique provider identifier e.g. 'yfinance'.

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (1): Fetch OHLCV data for a single symbol.          Returns:             DataFrame wi

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (1): Fetch OHLCV for multiple symbols efficiently (batch/parallel where supported).

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (1): Fetch company metadata: name, sector, industry, market cap, ISIN.         Return

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

## Knowledge Gaps
- **41 isolated node(s):** `Trade domain model for backtesting.`, `Pydantic-settings based configuration management. Loads from config.yaml, then o`, `Inject YAML values as env vars if not already set (env vars take priority).`, `Domain exception hierarchy. All platform exceptions flow from SwingBaseError so`, `Root exception for the entire platform.` (+36 more)
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
- **Thin community `Community 26`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (1 nodes): `Unique provider identifier e.g. 'yfinance'.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (1 nodes): `Fetch OHLCV data for a single symbol.          Returns:             DataFrame wi`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (1 nodes): `Fetch OHLCV for multiple symbols efficiently (batch/parallel where supported).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (1 nodes): `Fetch company metadata: name, sector, industry, market cap, ISIN.         Return`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 34`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 35`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 36`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 37`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 40`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `OHLCVRepository` connect `Community 3` to `Community 0`, `Community 1`, `Community 2`, `Community 5`, `Community 6`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Why does `Stock` connect `Community 3` to `Community 0`, `Community 1`, `Community 2`, `Community 6`, `Community 8`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Why does `ATR` connect `Community 0` to `Community 6`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Are the 25 inferred relationships involving `str` (e.g. with `list_saved_results()` and `_rec_dict()`) actually correct?**
  _`str` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `BaseIndicator` (e.g. with `RSI` and `Stochastic`) actually correct?**
  _`BaseIndicator` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `OHLCVRepository` (e.g. with `BacktestConfig` and `BacktestRunResult`) actually correct?**
  _`OHLCVRepository` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `ATR` (e.g. with `Average True Range (Wilder's smoothing).` and `EMA`) actually correct?**
  _`ATR` has 22 INFERRED edges - model-reasoned connections that need verification._