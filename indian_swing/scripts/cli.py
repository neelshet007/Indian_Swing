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
        lookback = DynamicLookbackEngine.get_required_lookback(strategy)

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


@app.command("strategies")
def list_strategies():
    configure_logging(fmt="console")
    from indian_swing.strategies.registry import strategy_registry

    strategy_registry.discover()
    for strategy in strategy_registry.all():
        typer.echo(f"{strategy.name} v{strategy.version} - {strategy.description}")


if __name__ == "__main__":
    app()
