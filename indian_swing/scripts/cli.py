from __future__ import annotations

import asyncio
from datetime import date
from typing import Optional

import typer

from indian_swing.core.logging_setup import configure_logging

app = typer.Typer(help="Indian Swing Trading Platform CLI")
db_app = typer.Typer(help="Database commands")
data_app = typer.Typer(help="Data commands")
scan_app = typer.Typer(help="Scanner commands")

app.add_typer(db_app, name="db")
app.add_typer(data_app, name="data")
app.add_typer(scan_app, name="scan")


@db_app.command("init")
def db_init():
    configure_logging(fmt="console")

    async def _init():
        from indian_swing.database.connection import init_db
        await init_db()

    asyncio.run(_init())
    typer.echo("Database initialized.")


@data_app.command("download")
def data_download(
    symbols: Optional[str] = typer.Option(None, help="Comma-separated symbols to download."),
    force: bool = typer.Option(False, "--force", help="Force complete refresh of all data."),
    bars: Optional[int] = typer.Option(None, "--bars", help="Number of historical daily bars to download (e.g. 1150 to go back to Jan 2022)."),
    start: Optional[str] = typer.Option(None, "--start", help="Start date to download (YYYY-MM-DD)."),
    end: Optional[str] = typer.Option(None, "--end", help="End date to download (YYYY-MM-DD)."),
):
    configure_logging(fmt="console")

    async def _download():
        from datetime import datetime
        from indian_swing.config.settings import settings
        from indian_swing.core.lookback_engine import DynamicLookbackEngine
        from indian_swing.data.pipeline import DataPipeline
        from indian_swing.data.universe import UniverseLoader
        from indian_swing.database.connection import get_sync_session, init_db
        from indian_swing.database.repositories.stock_repo import StockRepository
        from indian_swing.strategies.registry import strategy_registry

        await init_db()
        strategy_registry.discover()
        strategy = strategy_registry.get("sivcs_vcp")
        lookback = bars or DynamicLookbackEngine.get_required_lookback(strategy)

        with get_sync_session() as session:
            UniverseLoader(session).load_universe()
            repo = StockRepository(session)
            universe_symbols = [stock.symbol for stock in repo.get_active()]

        selected = [value.strip().upper() for value in symbols.split(",")] if symbols else universe_symbols
        if settings.scanner.benchmark_symbol not in selected:
            selected.append(settings.scanner.benchmark_symbol)

        start_date = datetime.strptime(start, "%Y-%m-%d").date() if start else None
        end_date = datetime.strptime(end, "%Y-%m-%d").date() if end else date.today()

        if start_date:
            summary = await DataPipeline().run_full(selected, start=start_date, end=end_date, force_refresh=force)
        else:
            summary = await DataPipeline().run_incremental(selected, required_daily_bars=lookback, end=end_date, force_refresh=force)
        typer.echo(f"Download complete. Succeeded: {summary.succeeded}, failed: {summary.failed}, records: {summary.records_added}")
        for error in summary.errors[:10]:
            typer.echo(f"- {error}")

    asyncio.run(_download())


@scan_app.command("run")
def scan_run(strategy: str = typer.Option("all", help="Strategy to run ('sivcs_vcp', 'amrc', or 'all')")):
    configure_logging(fmt="console")

    async def _scan():
        from indian_swing.database.connection import init_db
        from indian_swing.recommendations.scanner import RecommendationScanner
        from indian_swing.strategies.registry import strategy_registry

        await init_db()
        scanner = RecommendationScanner()

        strategies_to_run = ["sivcs_vcp", "amrc"] if strategy == "all" else [strategy]

        for s in strategies_to_run:
            try:
                scanner.strategy = strategy_registry.get(s)
                result = await scanner.scan(date.today())
                typer.echo(
                    f"Scan complete for {s}. Stocks scanned: {result.stocks_scanned}, "
                    f"recommendations: {result.recommendations_saved}, failed: {result.failed_stocks}"
                )
            except Exception as e:
                typer.echo(f"Failed to scan strategy {s}: {e}")

    asyncio.run(_scan())


@scan_app.command("historical")
def scan_historical():
    configure_logging(level="WARNING", fmt="console")

    async def _run():
        from indian_swing.database.connection import get_sync_session, init_db
        from indian_swing.recommendations.automation import HistoricalScanManager, validate_date
        import click
        from datetime import datetime

        await init_db()
        manager = HistoricalScanManager()
        
        # Check active session
        existing = manager.get_active_session()
        dates = []
        start_idx = 0
        session_obj = None

        if existing:
            typer.echo("A previous historical scan was found.")
            typer.echo(f"Completed:\n{existing.completed_days} of {existing.total_days} trading days.")
            typer.echo("Do you want to:")
            typer.echo("1 -> Resume")
            typer.echo("2 -> Start a new historical scan")
            choice = click.prompt("Enter choice (1 or 2)", type=int, default=1)
            if choice == 1:
                session_obj = existing
                start_idx = existing.completed_days
                for ds in existing.queue:
                    dt = datetime.strptime(ds, "%d/%m/%y").date()
                    dates.append(dt)

        if not dates:
            while True:
                from_str = click.prompt("Enter From Date (YYYY-MM-DD)")
                to_str = click.prompt("Enter To Date (YYYY-MM-DD)")
                try:
                    from_d = datetime.strptime(from_str.strip(), "%Y-%m-%d").date()
                    to_d = datetime.strptime(to_str.strip(), "%Y-%m-%d").date()
                    if from_d > to_d:
                        typer.echo("Error: From Date must be before or equal to To Date.")
                        continue
                    break
                except ValueError:
                    typer.echo("Error: Invalid date format. Use YYYY-MM-DD.")

            typer.echo("Fetching benchmark calendar to identify active trading days...")
            from indian_swing.database.repositories.stock_repo import StockRepository
            from indian_swing.config.settings import settings
            from indian_swing.database.models import Stock, OHLCV
            
            benchmark_symbol = settings.scanner.benchmark_symbol
            lookback = 282
            try:
                await manager.scanner.pipeline.run_incremental(
                    [benchmark_symbol],
                    required_daily_bars=lookback,
                    end=to_d,
                    force_refresh=False
                )
            except Exception as exc:
                typer.echo(f"Error fetching benchmark data: {exc}")
                return

            with get_sync_session() as session:
                benchmark_stock = StockRepository(session).get_by_symbol(
                    benchmark_symbol,
                    exchange=settings.scanner.benchmark_exchange
                )
                if not benchmark_stock:
                    typer.echo("Error: Benchmark stock metadata not found.")
                    return

                candles = session.execute(
                    select(OHLCV)
                    .where(OHLCV.stock_uuid == benchmark_stock.stock_uuid)
                    .where(OHLCV.timeframe == "1d")
                    .where(OHLCV.date >= from_d)
                    .where(OHLCV.date <= to_d)
                    .order_by(OHLCV.date)
                ).scalars().all()
                dates = [c.date for c in candles]

            if not dates:
                typer.echo("Error: No active trading days found in the selected date range.")
                return

            typer.echo(f"Found {len(dates)} active trading days to scan.")
            session_obj = manager.create_session(dates)
            start_idx = 0

        total = len(dates)
        start_time = datetime.now()
        
        for idx in range(start_idx, total):
            curr_date = dates[idx]
            date_str = curr_date.strftime("%d/%m/%y")
            
            # Run scan first to fetch/download OHLCV data for curr_date
            result = await manager.scanner.scan(scan_date=curr_date, force_refresh=False)

            with get_sync_session() as db_session:
                # Update session info
                db_session.add(session_obj)
                session_obj.current_date = date_str
                session_obj.status = "active"
                db_session.flush()
                # Run paper trade checks AFTER scan is complete so data exists in the database
                manager.update_paper_trades(db_session, curr_date)

            with get_sync_session() as db_session:
                from sqlalchemy import select
                from indian_swing.database.models import PaperTrade
                trades_created = manager.create_pending_trades(db_session, result.scan_uuid)
                
                completed_count = len(db_session.execute(
                    select(PaperTrade).where(PaperTrade.status == "Closed")
                ).scalars().all())
                active_count = len(db_session.execute(
                    select(PaperTrade).where(PaperTrade.status == "Active")
                ).scalars().all())

                # Calculate ETA
                processed = idx + 1 - start_idx
                elapsed = (datetime.now() - start_time).total_seconds()
                avg_time = elapsed / processed if processed > 0 else 0
                remaining = total - (idx + 1)
                eta_min = (avg_time * remaining) / 60.0

                db_session.add(session_obj)
                session_obj.completed_days = idx + 1
                session_obj.stocks_scanned = result.stocks_scanned
                session_obj.total_stocks = result.stocks_scanned + result.failed_stocks
                session_obj.recommendations_today = result.recommendations_saved
                session_obj.paper_trades_created = trades_created
                session_obj.completed_trades = completed_count
                session_obj.active_trades = active_count
                session_obj.eta_minutes = eta_min
                if idx + 1 == total:
                    session_obj.status = "completed"
                db_session.flush()

                # Generate Excel
                manager.generate_excel_report(db_session)

            typer.echo(f"Trading Day {idx+1}/{total} | Date: {date_str} | Recs Found: {result.recommendations_saved} | Trades Created: {trades_created} | ETA: {eta_min:.1f}m")

            pass

        typer.echo("\n" + "="*40)
        typer.echo("Historical scan and paper trading simulation completed!")
        report = manager.generate_final_report()
        
        typer.echo("\n--- Final Report ---")
        typer.echo(f"Total Trading Days Processed: {report['total_scans']}")
        typer.echo(f"Total Recommendations: {report['total_recommendations']}")
        typer.echo(f"Total Paper Trades: {report['total_trades']}")
        typer.echo(f"Win Rate: {report['win_rate']}%")
        typer.echo(f"Loss Rate: {report['loss_rate']}%")
        typer.echo(f"Profit Factor: {report['profit_factor']}")
        typer.echo(f"Expectancy: {report['expectancy']}%")
        typer.echo(f"CAGR: {report['cagr']}%")
        typer.echo(f"Maximum Drawdown: {report['max_drawdown']}%")
        typer.echo(f"Average Holding Period: {report['avg_holding_period']} days")
        typer.echo(f"Average R Multiple: {report['avg_r_multiple']}")

    asyncio.run(_run())



@app.command("strategies")
def list_strategies():
    configure_logging(fmt="console")
    from indian_swing.strategies.registry import strategy_registry

    strategy_registry.discover()
    for strategy in strategy_registry.all():
        typer.echo(f"{strategy.name} v{strategy.version} - {strategy.description}")


if __name__ == "__main__":
    app()
