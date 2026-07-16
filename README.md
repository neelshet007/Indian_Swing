# 🇮🇳 Indian Swing — Institutional Swing Trading Platform

> **Institutional-grade swing trading recommendation system for Indian equities.**  
> Scans 2,300+ NSE stocks daily using the Minervini VCP (Volatility Contraction Pattern) strategy, stores everything in PostgreSQL, and presents results through a modern React dashboard.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Project Architecture](#project-architecture)
4. [Tech Stack](#tech-stack)
5. [Prerequisites](#prerequisites)
6. [Installation & Setup](#installation--setup)
7. [Configuration](#configuration)
8. [Running the App](#running-the-app)
9. [How the Scanner Works](#how-the-scanner-works)
10. [API Reference](#api-reference)
11. [Dashboard Pages](#dashboard-pages)
12. [Database Schema](#database-schema)
13. [Data Flow](#data-flow)
14. [Common Issues & Troubleshooting](#common-issues--troubleshooting)
15. [Development](#development)

---

## Overview

Indian Swing is a full-stack trading research platform that:

- **Downloads** historical OHLCV data for 2,300+ NSE stocks from Upstox
- **Runs** the Minervini SIVCS VCP strategy nightly (or on demand)
- **Stores** all data, signals, and recommendations in PostgreSQL with zero duplication
- **Serves** a REST API (FastAPI) consumed by a React dashboard
- **Displays** buy recommendations, scan analytics, backtesting, and trade replay

---

## Features

| Feature | Description |
|---|---|
| 📈 **VCP Scanner** | Minervini Volatility Contraction Pattern with trend template, Stage 2, RS, breakout, and risk gates |
| 📊 **2,300+ Stocks** | Full NSE universe from `EQUITY_L.csv` — all series |
| 🔄 **Incremental Data** | Only fetches missing date gaps from Upstox — no duplicate downloads |
| 💾 **PostgreSQL** | All OHLCV, stocks, signals, and scan jobs stored with unique constraints |
| ⚡ **Smart Caching** | DB-first query; API only called for genuinely missing data |
| 🩺 **Auto-Deactivation** | Stocks with no valid history are automatically marked inactive |
| 🗓️ **Historical Replay** | Scan any past date independently via date picker |
| 📉 **Backtesting** | Replay any recommendation against actual price outcomes |
| 🔴 **Live Scan Progress** | Real-time progress bar with per-stock stage tracking |
| ⚠️ **Error Surface** | Inactive / delisted stocks surfaced in UI with reason |
| 🕐 **Auto Scheduler** | APScheduler runs the scan at 4 PM IST every weekday (configurable) |

---

## Project Architecture

```
Indian_Swing/
│
├── indian_swing/               ← Python backend package
│   ├── api/                    ← FastAPI application
│   │   ├── main.py             ← App entry point, routers, CORS, scheduler
│   │   └── routes/             ← REST API endpoints
│   │       ├── recommendations.py
│   │       ├── scans.py
│   │       ├── scanner.py
│   │       ├── stocks.py
│   │       ├── backtest.py
│   │       ├── replay.py
│   │       └── strategies.py
│   │
│   ├── config/
│   │   └── settings.py         ← Pydantic-settings config (YAML + env override)
│   │
│   ├── core/
│   │   ├── logging_setup.py    ← Structured JSON logging (structlog)
│   │   ├── lookback_engine.py  ← Dynamic lookback calculator
│   │   ├── symbols.py          ← Symbol normalization (NSE_EQ| prefix for Upstox)
│   │   └── types.py            ← Enums: SignalDirection, SignalQuality, RiskLevel
│   │
│   ├── data/
│   │   ├── pipeline.py         ← Incremental data fetch orchestrator
│   │   ├── universe.py         ← CSV to DB stock universe loader
│   │   └── providers/
│   │       └── upstox.py       ← Upstox historical candle API client
│   │
│   ├── database/
│   │   ├── connection.py       ← SQLAlchemy engine (sync + async)
│   │   ├── models.py           ← ORM models: Stock, OHLCV, ScanJob, Signal, Recommendation
│   │   └── repositories/
│   │       ├── ohlcv_repo.py   ← Coverage check, gap detection, DataFrame builder
│   │       └── stock_repo.py   ← Bulk upsert, active/inactive management
│   │
│   ├── indicators/
│   │   └── calculator.py       ← pandas-ta indicators: SMA, ATR, RS, Stage2, weekly
│   │
│   ├── recommendations/
│   │   ├── scanner.py          ← Main scan orchestrator (universe to signals to DB)
│   │   └── validator.py        ← Deduplication, staleness, and sanity checks
│   │
│   ├── strategies/
│   │   ├── base.py             ← BaseStrategy ABC + StrategySignal + StrategyContext
│   │   ├── institutional_vcp.py ← SIVCS VCP strategy implementation
│   │   └── registry.py         ← Auto-discovery strategy registry
│   │
│   ├── backtesting/            ← Trade simulation engine
│   ├── replay/                 ← Historical trade replay
│   ├── scripts/                ← CLI (db init, scan run, data download)
│   └── EQUITY_L.csv            ← NSE full equity list (2,386 stocks)
│
├── dashboard/                  ← React frontend (Vite)
│   └── src/
│       ├── pages/
│       │   ├── Dashboard.jsx       ← Main scan results + recommendations
│       │   ├── TradeDetail.jsx     ← Single recommendation deep-dive
│       │   ├── ScanAnalytics.jsx   ← Funnel analysis, VCP stats
│       │   ├── Backtesting.jsx     ← Strategy backtest runner
│       │   ├── ReplayPage.jsx      ← Historical trade replay
│       │   └── Stocks.jsx          ← Stock universe browser
│       ├── index.css               ← Design system (dark theme, glassmorphism)
│       └── App.jsx                 ← Router + navigation
│
├── config/
│   └── config.yaml             ← Main config (overrides defaults in settings.py)
│
├── data/                       ← Runtime data (DB, cache)
├── tests/                      ← pytest test suite
├── pyproject.toml              ← Python dependencies + tool config
└── Makefile                    ← Developer shortcuts
```

---

## Tech Stack

### Backend
| Layer | Technology |
|---|---|
| Web Framework | FastAPI + Uvicorn |
| ORM | SQLAlchemy 2.0 (sync + async) |
| Database | PostgreSQL (primary) / SQLite (dev) |
| Data Provider | Upstox Historical Candle API v3 |
| Indicators | pandas-ta |
| Scheduling | APScheduler (cron) |
| Config | Pydantic-Settings + YAML |
| Logging | structlog (JSON) |
| CLI | Typer |

### Frontend
| Layer | Technology |
|---|---|
| Framework | React 18 + Vite |
| HTTP Client | Axios |
| Routing | React Router v6 |
| Charts | Recharts |
| Styling | Vanilla CSS (dark glassmorphism theme) |

---

## Prerequisites

Before running this project, ensure you have:

- **Python 3.11+** — check with `python --version`
- **Node.js 18+** — check with `node --version`
- **PostgreSQL 14+** — running locally or remote (optional, SQLite works too)
- **Upstox Developer Account** — for historical market data API access
- **Git**

> **SQLite alternative:** The app works with SQLite for development with zero database setup. See Configuration section below.

---

## Installation & Setup

### Step 1 — Clone the repository

```bash
git clone https://github.com/neelshet007/Indian_Swing.git
cd Indian_Swing
```

### Step 2 — Create Python virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### Step 3 — Install Python dependencies

```bash
pip install -e ".[dev]"
```

### Step 4 — Configure environment variables

```bash
# Copy the example env file
cp .env.example .env
```

Open `.env` and fill in your values. The most important one is `UPSTOX_ACCESS_TOKEN`.

### Step 5 — Update the universe file path in config

Open `config/config.yaml` and set the **absolute path** to `EQUITY_L.csv`:

```yaml
# Line 4 in config.yaml — update to match your system path
universe_file: "C:/Indian_Swing/indian_swing/EQUITY_L.csv"
```

> On macOS/Linux: `universe_file: "/home/yourname/Indian_Swing/indian_swing/EQUITY_L.csv"`

### Step 6 — Initialize the database

```bash
python -m indian_swing.scripts.cli db init
```

### Step 7 — Install frontend dependencies

```bash
cd dashboard
npm install
cd ..
```

---

## Configuration

### `.env` — Environment Variables

```ini
# Application
APP_ENV=development
LOG_LEVEL=INFO

# Database — choose one:
DATABASE_URL=sqlite+aiosqlite:///./data/swing.db
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/indian_swing

# Upstox API — REQUIRED for market data
UPSTOX_ACCESS_TOKEN=your_upstox_access_token_here

# Scanner
SCANNER_ENABLED=true
SCANNER_CRON=0 16 * * 1-5    # 4 PM IST weekdays

# API
API_HOST=0.0.0.0
API_PORT=8000
```

### `config/config.yaml` — Application Config

```yaml
universe_file: "C:/Indian_Swing/indian_swing/EQUITY_L.csv"   # EDIT THIS PATH

scanner:
  max_recommendations: 50
  min_confidence_score: 0.6

pipeline:
  min_price: 10.0          # Filter stocks below Rs 10
  min_volume: 50000        # Filter stocks with low liquidity

backtesting:
  initial_capital: 1000000  # Rs 10 lakh
```

### Getting an Upstox Access Token

1. Create a developer account at [developer.upstox.com](https://developer.upstox.com)
2. Create a new app and note the API key and secret
3. Generate an authorization URL and log in with your Upstox credentials
4. Exchange the authorization code for an access token
5. Copy the access token into `.env` as `UPSTOX_ACCESS_TOKEN=...`

> **Important:** Upstox access tokens expire after 24 hours. You must refresh the token each day before running scans.

---

## Running the App

Open **two separate terminal windows**:

### Terminal 1 — Backend (FastAPI)

```bash
cd Indian_Swing
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

uvicorn indian_swing.api.main:app --port 8000 --reload --reload-dir indian_swing
```

Backend runs at: **http://localhost:8000**  
API docs at: **http://localhost:8000/api/docs**

### Terminal 2 — Frontend (React)

```bash
cd Indian_Swing/dashboard
npm run dev
```

Dashboard runs at: **http://localhost:5173**

---

### Running a Scan

**Via UI:** Click the **"Run Scan"** button on the dashboard  
**Via CLI:**
```bash
python -m indian_swing.scripts.cli scan run
python -m indian_swing.scripts.cli scan run --date 2026-07-15
```

---

## How the Scanner Works

### Scan Pipeline Steps

```
1. Universe Load
   Reads EQUITY_L.csv (2386 stocks) and upserts into database.
   Separates active vs. inactive (delisted/no-history) stocks.

2. Incremental Data Fetch
   For each stock:
     a. Check sw_ohlcv — what dates are already stored?
     b. Calculate gap: last_stored_date + 1 day to scan_date
     c. If gap exists, call Upstox API for only those dates
     d. Insert new candles (unique constraint prevents duplicates)
   Stocks with permanent data errors → marked is_active = False

3. Strategy Evaluation (per active stock)
   Gate 1: Liquidity     — turnover_50 >= Rs 1Cr AND vol_50 >= 1L shares
   Gate 2: Trend         — Minervini 8-point trend template (SMA50/150/200 alignment)
   Gate 3: Stage 2       — Weekly stage 2 (price above rising 30/40-week SMA)
   Gate 4: RS            — Relative Strength score vs NIFTY 50 > 0
   Gate 5: VCP           — Tightening contractions + volume dry-up over 50 days
   Gate 6: Breakout      — Close > pivot AND volume >= 1.5x 50-day avg
   Gate 7: Risk          — Stop loss <= 10% from entry; position fits portfolio

4. Signal Persistence
   Stocks passing all gates → Signal + Recommendation saved to database

5. Completion
   ScanJob marked completed with full analytics JSON
```

### Stop Loss & Target Calculation

```
stop_loss  = max(20-day low, close - 2 x ATR14)
target_1   = close + 2 x (close - stop_loss)   [2:1 Risk-Reward]
target_2   = close + 3 x (close - stop_loss)   [3:1 Risk-Reward]

position_size = min(
    Rs 1,00,000 x 1% / risk_per_share,   # risk-based sizing
    Rs 1,00,000 x 10% / close            # max 10% portfolio cap
)
```

### Data Deduplication Guarantee

The `sw_ohlcv` table enforces a unique constraint on `(stock_uuid, date, timeframe)`.  
Before any API call, the coverage repository checks what is already stored and only fetches the gap. No data is ever downloaded twice.

---

## API Reference

**Base URL:** `http://localhost:8000`  
**Interactive Docs:** `http://localhost:8000/api/docs`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Server + DB health check |
| POST | `/api/scanner/run` | Trigger a scan (`?scan_date=YYYY-MM-DD&force_refresh=false`) |
| GET | `/api/scanner/progress` | Live scan progress (poll while scan is running) |
| GET | `/api/scans/latest` | Most recent completed scan |
| GET | `/api/scans/date/{YYYY-MM-DD}` | Scan for a specific trading date |
| GET | `/api/scans/uuid/{scan_uuid}` | Scan by UUID |
| GET | `/api/scans/history` | Last 50 completed scans |
| GET | `/api/scans/{scan_uuid}/analytics` | Funnel + failure reasons analytics |
| GET | `/api/recommendations/{scan_uuid}` | All BUY recommendations for a scan |
| GET | `/api/recommendations/detail/{rec_id}` | Single recommendation with full signal detail |
| GET | `/api/stocks` | Full stock universe |
| GET | `/api/stocks/{symbol}` | Stock detail |
| POST | `/api/backtest/run` | Run strategy backtest |
| GET | `/api/replay/{rec_id}` | Replay a specific trade recommendation |

---

## Dashboard Pages

| Page | Route | Description |
|---|---|---|
| Trading Terminal | `/` | Date picker, scan trigger, recommendation cards, error panel |
| Trade Detail | `/recommendation/:id` | Entry/stop/target, chart, full strategy explanation per gate |
| Scan Analytics | `/analytics/:scan_uuid` | Funnel chart, top rejection reasons, stock journeys |
| Backtesting | `/backtesting` | Run strategy over a historical date range |
| Historical Replay | `/replay` | Replay any past recommendation vs actual outcomes |
| Stock Universe | `/stocks` | Browse all 2386 NSE stocks, active/inactive status |

---

## Database Schema

| Table | Purpose |
|---|---|
| `sw_stocks` | Stock universe — symbol, ISIN, sector, is_active flag |
| `sw_ohlcv` | OHLCV candles — unique on (stock_uuid, date, timeframe) |
| `sw_scan_jobs` | Scan metadata — status, counts, errors JSON, analytics JSON |
| `sw_signals` | Raw strategy signals with full indicator snapshot |
| `sw_recommendations` | BUY recommendations with entry/stop/target/rank |

---

## Data Flow

```
EQUITY_L.csv (2386 stocks)
        |
        v
  UniverseLoader
  upsert into sw_stocks
        |
        v
  DataPipeline.run_incremental()
  coverage check in sw_ohlcv
        |
   gap found?  ──── No ──→  skip (already in DB)
        |
       Yes
        v
  Upstox API v3 (historical candle)
  insert into sw_ohlcv
        |
        v
  IndicatorCalculator
  SMA / ATR / RS / Stage2 / VCP
        |
        v
  InstitutionalVCP.generate_signals()
  7-gate filter chain
        |
    PASS all gates?  ──── No ──→ rejected (recorded in analytics)
        |
       Yes
        v
  RecommendationValidator
  dedup + staleness check
        |
        v
  sw_signals + sw_recommendations
        |
        v
  FastAPI  →  React Dashboard
```

---

## Common Issues & Troubleshooting

### Upstox token not set or expired
```
Error: No access token configured for Upstox provider
```
Add or refresh your token in `.env`:
```ini
UPSTOX_ACCESS_TOKEN=your_fresh_token
```
Tokens expire after 24 hours. Generate a new one from Upstox developer portal each day.

---

### Dashboard shows "No Scan Completed Yet"
No scan has been run. Click **Run Scan** in the UI, or run from CLI:
```bash
python -m indian_swing.scripts.cli scan run
```

---

### Universe file not found
```
FileNotFoundError: Universe file ... not found
```
Edit `config/config.yaml` and set the absolute path to match your system:
```yaml
universe_file: "C:/YourPath/Indian_Swing/indian_swing/EQUITY_L.csv"
```

---

### First scan is very slow
Expected! On first run the system downloads ~2 years of history for all 2,300+ stocks from Upstox. This takes **45–90 minutes** depending on internet speed. Every subsequent scan is fast (only fetches missing days).

---

### PostgreSQL connection refused
Either:
- Start PostgreSQL: `pg_ctl start` or start via services
- Or switch to SQLite (zero setup): `DATABASE_URL=sqlite+aiosqlite:///./data/swing.db` in `.env`

---

### `No daily history available` in error panel
This is normal for newly listed, suspended, or delisted stocks. They are automatically marked inactive and skipped in all future scans. They appear in the amber warning panel in the UI.

---

### Multiple tabs / different dates
Each tab can view a different scan date independently — the date picker is per-tab. Scans are stored in the database by date so historical data is always available without re-running.

---

## Development

### Tests
```bash
pytest tests/ -v
pytest tests/ --cov=indian_swing --cov-report=html
```

### Lint and format
```bash
ruff check indian_swing/
ruff format indian_swing/
mypy indian_swing/
```

### Makefile reference
```bash
make install      # Install Python dependencies
make api          # Start backend server
make dashboard    # Start React dev server
make db-init      # Initialize database tables
make db-reset     # Wipe and reinitialize database
make scan         # Run today's scan via CLI
make test         # Run test suite
make lint         # Run ruff + mypy
make clean        # Remove __pycache__ etc.
```

### Add a new strategy
1. Create `indian_swing/strategies/my_strategy.py` extending `BaseStrategy`
2. Implement `name`, `version`, `indicator_requirements`, `data_requirements`, and `generate_signals()`
3. The registry auto-discovers it at startup — no manual registration needed

---

**GitHub:** https://github.com/neelshet007/Indian_Swing  
**Strategy:** SIVCS VCP (Minervini Volatility Contraction Pattern) v2.0.0  
**Universe:** NSE — 2,386 stocks (EQUITY_L.csv)  
**Benchmark:** NIFTY 50  
**Data Source:** Upstox Historical Candle API v3
