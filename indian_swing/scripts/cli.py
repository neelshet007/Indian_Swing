"""
CLI entry point using Typer.
Usage:
  swing db init
  swing data download --universe nifty50
  swing scan run
  swing strategies list
"""
from __future__ import annotations

import asyncio
from datetime import date
from typing import Optional

import typer

from indian_swing.core.logging_setup import configure_logging, get_logger

app = typer.Typer(help="Indian Swing Trading Platform CLI")
db_app = typer.Typer(help="Database commands")
data_app = typer.Typer(help="Data commands")
scan_app = typer.Typer(help="Scanner commands")

app.add_typer(db_app, name="db")
app.add_typer(data_app, name="data")
app.add_typer(scan_app, name="scan")


@db_app.command("init")
def db_init():
    """Initialize database tables."""
    configure_logging(fmt="console")
    logger = get_logger(__name__)

    async def _init():
        from indian_swing.database.connection import init_db
        await init_db()

    asyncio.run(_init())
    typer.echo("[OK] Database initialized.")


@data_app.command("download")
def data_download(
    universe: str = typer.Option("nifty50", help="nifty50 | nifty500 | custom | all"),
    symbols: Optional[str] = typer.Option(None, help="Comma-separated symbols to download."),
    years: int = typer.Option(10, help="Years of historical data to fetch."),
    force: bool = typer.Option(False, "--force", help="Force complete refresh of all data."),
):
    """Download OHLCV data for the specified universe."""
    configure_logging(fmt="console")

    async def _download():
        from indian_swing.core.universe import UniverseManager
        from indian_swing.data.pipeline import DataPipeline
        from indian_swing.database.connection import init_db

        await init_db()
        manager = UniverseManager()

        if symbols:
            syms = [s.strip().upper() for s in symbols.split(",")]
            # Ensure stocks exist in DB
            await manager.sync_to_db()
        else:
            count = await manager.sync_to_db()
            typer.echo(f"Universe: {count} stocks synced to database.")
            syms = await manager.get_active_symbols()

        typer.echo(f"Downloading data for {len(syms)} symbols ({years} years)...")
        pipeline = DataPipeline()
        from datetime import date, timedelta
        end_date = date.today()
        start_date = end_date - timedelta(days=years * 365)
        summary = await pipeline.run_full(syms, start=start_date, end=end_date, force_refresh=force)
        typer.echo(f"[OK] Done: {summary.succeeded} succeeded, {summary.failed} failed, {summary.records_added} records added.")
        if summary.errors:
            typer.echo(f"[WARN] Errors: {len(summary.errors)}")
            for e in summary.errors[:10]:
                typer.echo(f"  - {e}")

    asyncio.run(_download())


@scan_app.command("run")
def scan_run():
    """Run the recommendation scanner."""
    configure_logging(fmt="console")

    async def _scan():
        from indian_swing.recommendations.scanner import RecommendationScanner
        from indian_swing.database.connection import init_db

        await init_db()
        scanner = RecommendationScanner()
        target = date.today()
        typer.echo(f"Scanning {target}...")
        result = await scanner.scan(target)
        typer.echo(
            f"[OK] Scan complete: {result.stocks_scanned} stocks, "
            f"{result.signals_generated} signals, "
            f"{result.recommendations_saved} recommendations."
        )

    asyncio.run(_scan())


@app.command("strategies")
def list_strategies():
    """List all discovered strategies."""
    configure_logging(fmt="console")
    from indian_swing.strategies.registry import strategy_registry
    strategy_registry.discover()
    for s in strategy_registry.all():
        typer.echo(f"  {s.name:<30} v{s.version}  — {s.description[:60]}...")


if __name__ == "__main__":
    app()
