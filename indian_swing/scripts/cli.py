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
):
    configure_logging(fmt="console")

    async def _download():
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

        summary = await DataPipeline().run_incremental(selected, required_daily_bars=lookback, end=date.today(), force_refresh=force)
        typer.echo(f"Download complete. Succeeded: {summary.succeeded}, failed: {summary.failed}, records: {summary.records_added}")
        for error in summary.errors[:10]:
            typer.echo(f"- {error}")

    asyncio.run(_download())


@scan_app.command("run")
def scan_run():
    configure_logging(fmt="console")

    async def _scan():
        from indian_swing.database.connection import init_db
        from indian_swing.recommendations.scanner import RecommendationScanner

        await init_db()
        result = await RecommendationScanner().scan(date.today())
        typer.echo(
            f"Scan complete. Stocks scanned: {result.stocks_scanned}, "
            f"recommendations: {result.recommendations_saved}, failed: {result.failed_stocks}"
        )

    asyncio.run(_scan())


@scan_app.command("historical")
def scan_historical():
    configure_logging(fmt="console")

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
            num_days = click.prompt("How many trading days do you want to scan?", type=int)
            typer.echo(f"Please enter {num_days} trading days.")
            for i in range(num_days):
                while True:
                    date_input = click.prompt(f"Please enter Trading Day {i+1} (DD/MM/YY)")
                    parsed = validate_date(date_input)
                    if parsed:
                        dates.append(parsed)
                        break
                    else:
                        typer.echo("Error: Invalid date format. Please use DD/MM/YY (e.g. 11/06/26).")
            session_obj = manager.create_session(dates)
            start_idx = 0

        total = len(dates)
        start_time = datetime.now()
        
        for idx in range(start_idx, total):
            curr_date = dates[idx]
            date_str = curr_date.strftime("%d/%m/%y")
            
            typer.echo("\n" + "="*40)
            typer.echo(f"Trading Day {idx+1} of {total}")
            typer.echo(f"Current Date: {date_str}")
            typer.echo("Status: Scanning...")

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

            typer.echo(f"Recommendations Found: {result.recommendations_saved}")
            typer.echo("Saved: Yes")
            typer.echo(f"Paper Trades Created: {trades_created}")
            typer.echo("Status: Completed")

            if idx + 1 < total:
                typer.echo("\nTrading Day completed. Continuing to next queued date...")

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
