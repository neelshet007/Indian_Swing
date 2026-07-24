from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta
import math
from typing import Any, List, Optional

from sqlalchemy import select, delete
from indian_swing.core.logging_setup import get_logger
from indian_swing.database.connection import get_sync_session
from indian_swing.database.models import (
    HistoricalScanSession,
    PaperTrade,
    Recommendation,
    ScanJob,
    Stock,
)
from indian_swing.database.repositories.ohlcv_repo import OHLCVRepository
from indian_swing.recommendations.scanner import RecommendationScanner

logger = get_logger(__name__)


def validate_date(date_str: str) -> Optional[date]:
    """Validate date format DD/MM/YY and return date object."""
    try:
        dt = datetime.strptime(date_str.strip(), "%d/%m/%y")
        return dt.date()
    except ValueError:
        return None


class HistoricalScanManager:
    def __init__(self) -> None:
        self.scanner = RecommendationScanner()

    def preload_bundles(self, trading_dates: list[date]) -> dict[str, Any]:
        """Pre-calculate indicator bundles once for all active stocks across the session date range."""
        lookback = 282
        min_date = min(trading_dates) - timedelta(days=int(lookback * 1.8))
        max_date = max(trading_dates)
        
        with get_sync_session() as session:
            from indian_swing.config.settings import settings
            from indian_swing.database.repositories.ohlcv_repo import OHLCVRepository
            from indian_swing.database.repositories.stock_repo import StockRepository
            from indian_swing.indicators.calculator import IndicatorCalculator
            
            active_stocks = StockRepository(session).get_active()
            all_uuids = [s.stock_uuid for s in active_stocks]
            bulk_dfs = OHLCVRepository(session).to_dataframe_bulk(all_uuids, min_date, max_date, "1d")
            
            benchmark_stock = StockRepository(session).get_by_symbol(
                settings.scanner.benchmark_symbol,
                exchange=settings.scanner.benchmark_exchange,
            )
            precalculated_benchmark = None
            if benchmark_stock and benchmark_stock.stock_uuid in bulk_dfs:
                benchmark_df = bulk_dfs[benchmark_stock.stock_uuid]
                if not benchmark_df.empty:
                    precalculated_benchmark = IndicatorCalculator.add_daily_indicators(benchmark_df)
            
            bundles = {}
            for stock in active_stocks:
                df = bulk_dfs.get(stock.stock_uuid)
                if df is None or len(df) < 252:
                    continue
                try:
                    bundles[stock.stock_uuid] = IndicatorCalculator.build(
                        df, precalculated_benchmark=precalculated_benchmark
                    )
                except Exception:
                    pass
            return bundles

    def get_active_session(self) -> Optional[HistoricalScanSession]:
        """Find an active historical scan session."""
        with get_sync_session() as session:
            return session.execute(
                select(HistoricalScanSession)
                .where(HistoricalScanSession.status == "active")
                .order_by(HistoricalScanSession.created_at.desc())
            ).scalars().first()

    def create_session(self, dates: List[date], strategy_name: str = "sivcs_vcp") -> HistoricalScanSession:
        """Create a new historical scan session."""
        from sqlalchemy import update
        with get_sync_session() as session:
            # Mark older active sessions as paused to avoid conflicts and retain history
            session.execute(
                update(HistoricalScanSession)
                .where(HistoricalScanSession.status == "active")
                .values(status="paused")
            )
            
            queue_str = [d.strftime("%d/%m/%y") for d in dates]
            new_session = HistoricalScanSession(
                total_days=len(dates),
                completed_days=0,
                queue=queue_str,
                status="active",
                strategy_name=strategy_name
            )
            session.add(new_session)
            session.commit()
            
            # Retrieve from fresh query
            return session.get(HistoricalScanSession, new_session.id)

    def update_paper_trades(self, db_session, current_date: date) -> None:
        """Update entry/exit triggers for all active/pending paper trades on current_date."""
        # 1. Fetch pending and active paper trades where recommendation scan_date is on or before current_date
        trades = db_session.execute(
            select(PaperTrade)
            .join(Recommendation)
            .where(
                PaperTrade.status.in_(["Pending", "Active"]),
                Recommendation.scan_date <= current_date
            )
        ).scalars().all()

        ohlcv_repo = OHLCVRepository(db_session)

        for trade in trades:
            # Load recommendation to get stop loss, target, etc.
            rec = trade.recommendation
            if not rec:
                continue

            # Fetch candle for this stock on current_date
            df = ohlcv_repo.to_dataframe(trade.stock_uuid, current_date, current_date, "1d")
            if df.empty:
                continue  # Holiday or no trade data for this symbol

            row = df.iloc[-1]
            c_open = float(row["open"])
            c_high = float(row["high"])
            c_low = float(row["low"])
            c_close = float(row["close"])

            if trade.status == "Pending":
                # Check if entry is triggered: if we are after recommendation date
                # and price hits entry_price
                if current_date > rec.scan_date:
                    if c_high >= rec.entry_price:
                        # Entry triggered!
                        trade.status = "Active"
                        trade.entry_date = current_date
                        # If open gaps above entry, enter at open, otherwise at entry price
                        trade.entry_price = max(rec.entry_price, c_open)
                        trade.highest_price = c_high
                        trade.lowest_price = c_low
                        trade.max_drawdown = 0.0
                        trade.max_favorable_excursion = 0.0
                        trade.max_adverse_excursion = 0.0
                        
                        # Evaluate exits on the same day if triggered immediately
                        self._evaluate_exits(trade, rec, c_open, c_high, c_low, c_close, current_date)

            elif trade.status == "Active":
                # Only update/exit active trades if current_date is on or after the entry_date
                if trade.entry_date and current_date < trade.entry_date:
                    continue

                # Update metrics
                trade.highest_price = max(trade.highest_price or c_high, c_high)
                trade.lowest_price = min(trade.lowest_price or c_low, c_low)

                # MFE / MAE / Drawdown
                trade.max_favorable_excursion = max(
                    trade.max_favorable_excursion or 0.0,
                    (trade.highest_price - trade.entry_price) / trade.entry_price * 100
                )
                trade.max_adverse_excursion = max(
                    trade.max_adverse_excursion or 0.0,
                    (trade.entry_price - trade.lowest_price) / trade.entry_price * 100
                )
                
                current_dd = (trade.highest_price - c_low) / trade.highest_price * 100
                trade.max_drawdown = max(trade.max_drawdown or 0.0, current_dd)

                self._evaluate_exits(trade, rec, c_open, c_high, c_low, c_close, current_date)

    def _evaluate_exits(
        self,
        trade: PaperTrade,
        rec: Recommendation,
        c_open: float,
        c_high: float,
        c_low: float,
        c_close: float,
        current_date: date
    ) -> None:
        """Evaluate exit triggers for an active trade."""
        # Stop Loss
        if c_low <= rec.stop_loss:
            exit_price = rec.stop_loss
            if c_open < rec.stop_loss:
                exit_price = c_open  # Gap down below SL
            self._close_trade(trade, rec, current_date, exit_price, "Stop Loss")
            return

        # Target
        if c_high >= rec.target_price:
            exit_price = rec.target_price
            if c_open > rec.target_price:
                exit_price = c_open  # Gap up above target
            self._close_trade(trade, rec, current_date, exit_price, "Target")
            return
        # Time Exit is disabled to allow trades to run longer without default restrictions.
        pass


    def _close_trade(
        self,
        trade: PaperTrade,
        rec: Recommendation,
        exit_date: date,
        exit_price: float,
        reason: str
    ) -> None:
        trade.status = "Closed"
        trade.exit_date = exit_date
        trade.exit_price = exit_price
        trade.exit_reason = reason
        trade.holding_days = (exit_date - trade.entry_date).days
        
        risk = trade.entry_price - rec.stop_loss
        if risk > 0:
            trade.risk_reward = round((rec.target_price - trade.entry_price) / risk, 2)
            trade.r_multiple = round((exit_price - trade.entry_price) / risk, 2)
        else:
            trade.risk_reward = 0.0
            trade.r_multiple = 0.0
            
        trade.pnl = round((exit_price - trade.entry_price) / trade.entry_price * 100, 2)
        trade.pnl_absolute = round((exit_price - trade.entry_price) * (rec.position_size or 0), 2)

    def create_pending_trades(self, db_session, scan_uuid: str) -> int:
        """Create pending paper trades for all recommendations generated in scan_uuid."""
        recs = db_session.execute(
            select(Recommendation).where(Recommendation.scan_uuid == scan_uuid)
        ).scalars().all()

        created_count = 0
        for rec in recs:
            # Check if paper trade already exists for this recommendation
            existing = db_session.execute(
                select(PaperTrade).where(PaperTrade.recommendation_id == rec.id)
            ).scalars().first()
            if not existing:
                from indian_swing.core.universe_badge import badge_lookup
                is_nifty_500 = badge_lookup.has_badge(rec.stock.symbol, "NIFTY 500")
                universe_label = "NIFTY500" if is_nifty_500 else "NON_NIFTY500"
                paper_trade = PaperTrade(
                    recommendation_id=rec.id,
                    stock_uuid=rec.stock_uuid,
                    symbol=rec.stock.symbol,
                    status="Pending",
                    stop_loss=rec.stop_loss,
                    original_target_price=rec.target_price,
                    execution_universe=universe_label
                )
                db_session.add(paper_trade)
                created_count += 1
        if created_count > 0:
            db_session.flush()
        return created_count

    @staticmethod
    def _calculate_metrics(trades: list[PaperTrade], total_scans_len: int, total_recs_len: int) -> dict[str, Any]:
        if not trades:
            return {
                "total_scans": total_scans_len,
                "total_recommendations": total_recs_len,
                "total_trades": 0,
                "win_rate": 0.0,
                "loss_rate": 0.0,
                "profit_factor": 0.0,
                "avg_return": 0.0,
                "avg_winner": 0.0,
                "avg_loser": 0.0,
                "expectancy": 0.0,
                "cagr": 0.0,
                "max_drawdown": 0.0,
                "avg_holding_period": 0.0,
                "avg_r_multiple": 0.0,
                "total_return": 0.0,
                "monthly_stats": {},
                "yearly_stats": {},
                "equity_curve": [],
                "journal": []
            }

        wins = [t for t in trades if (t.pnl or 0.0) > 0]
        losses = [t for t in trades if (t.pnl or 0.0) <= 0]
        
        win_rate = len(wins) / len(trades) * 100
        loss_rate = len(losses) / len(trades) * 100
        
        gross_profit = sum(t.pnl_absolute for t in wins if t.pnl_absolute is not None)
        gross_loss = abs(sum(t.pnl_absolute for t in losses if t.pnl_absolute is not None))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')
        
        r_multiples = [t.r_multiple for t in trades if t.r_multiple is not None]
        avg_r = sum(r_multiples) / len(trades) if r_multiples else 0.0
        
        holding_periods = [t.holding_days for t in trades if t.holding_days is not None]
        avg_hold = sum(holding_periods) / len(trades) if holding_periods else 0.0

        pnls = [t.pnl for t in trades if t.pnl is not None]
        avg_return = sum(pnls) / len(trades) if pnls else 0.0
        avg_winner = sum(t.pnl for t in wins if t.pnl is not None) / len(wins) if wins else 0.0
        avg_loser = sum(t.pnl for t in losses if t.pnl is not None) / len(losses) if losses else 0.0
        expectancy = sum(pnls) / len(trades) if pnls else 0.0

        sorted_trades = sorted(trades, key=lambda t: t.exit_date or date.min)
        
        capital = 1_000_000.0
        initial_capital = 1_000_000.0
        equity_curve = [{"date": str(sorted_trades[0].entry_date or sorted_trades[0].created_at.date()), "equity": capital}]
        peak_equity = capital
        max_dd = 0.0
        
        for t in sorted_trades:
            pnl_abs = t.pnl_absolute or 0.0
            capital += pnl_abs
            equity_curve.append({"date": str(t.exit_date or t.updated_at.date()), "equity": capital})
            
            if capital > peak_equity:
                peak_equity = capital
            dd = (peak_equity - capital) / peak_equity * 100
            if dd > max_dd:
                max_dd = dd

        total_return_pct = ((capital - initial_capital) / initial_capital) * 100

        if sorted_trades:
            start_date = sorted_trades[0].entry_date or sorted_trades[0].created_at.date()
            end_date = sorted_trades[-1].exit_date or sorted_trades[-1].updated_at.date()
            if start_date and end_date:
                days = (end_date - start_date).days
                years = days / 365.25
                if years > 0 and capital > 0:
                    cagr = ((capital / initial_capital) ** (1 / years) - 1) * 100
                else:
                    cagr = 0.0
            else:
                cagr = 0.0
        else:
            cagr = 0.0

        monthly_stats = {}
        yearly_stats = {}
        for t in sorted_trades:
            exit_dt = t.exit_date
            if not exit_dt:
                continue
            year_str = str(exit_dt.year)
            month_str = exit_dt.strftime("%B")
            pnl_abs = t.pnl_absolute or 0.0

            yearly_stats[year_str] = yearly_stats.get(year_str, 0.0) + pnl_abs
            if year_str not in monthly_stats:
                monthly_stats[year_str] = {}
            monthly_stats[year_str][month_str] = monthly_stats[year_str].get(month_str, 0.0) + pnl_abs

        journal = [
            {
                "symbol": t.symbol,
                "entry_date": str(t.entry_date),
                "entry_price": t.entry_price,
                "exit_date": str(t.exit_date),
                "exit_price": t.exit_price,
                "exit_reason": t.exit_reason,
                "holding_days": t.holding_days,
                "pnl_pct": t.pnl,
                "pnl_abs": t.pnl_absolute,
                "r_multiple": t.r_multiple,
                "execution_universe": t.execution_universe,
            }
            for t in sorted_trades
        ]

        return {
            "total_scans": total_scans_len,
            "total_recommendations": total_recs_len,
            "total_trades": len(trades),
            "win_rate": round(win_rate, 2),
            "loss_rate": round(loss_rate, 2),
            "profit_factor": round(profit_factor, 2) if not math.isinf(profit_factor) else "Infinite",
            "avg_return": round(avg_return, 2),
            "avg_winner": round(avg_winner, 2),
            "avg_loser": round(avg_loser, 2),
            "expectancy": round(expectancy, 2),
            "cagr": round(cagr, 2),
            "max_drawdown": round(max_dd, 2),
            "avg_holding_period": round(avg_hold, 2),
            "avg_r_multiple": round(avg_r, 2),
            "total_return": round(total_return_pct, 2),
            "monthly_stats": monthly_stats,
            "yearly_stats": yearly_stats,
            "equity_curve": equity_curve,
            "journal": journal
        }

    def generate_final_report(self) -> dict[str, Any]:
        """Compute final statistics and metrics for completed runs."""
        with get_sync_session() as session:
            trades = session.execute(
                select(PaperTrade).where(PaperTrade.status == "Closed")
            ).scalars().all()
            
            total_scans = session.execute(
                select(ScanJob).where(ScanJob.status == "completed")
            ).scalars().all()
            
            total_recs = session.execute(
                select(Recommendation)
            ).scalars().all()

            def get_stats(trade_list):
                return self._calculate_metrics(trade_list, len(total_scans), len(total_recs))

            overall_trades = trades
            nifty_trades = [t for t in trades if t.execution_universe == "NIFTY500"]
            non_nifty_trades = [t for t in trades if t.execution_universe != "NIFTY500"]

            sivcs_trades = [t for t in trades if (t.recommendation.strategy_name if t.recommendation else "sivcs_vcp") == "sivcs_vcp"]
            sivcs_nifty = [t for t in sivcs_trades if t.execution_universe == "NIFTY500"]
            sivcs_non_nifty = [t for t in sivcs_trades if t.execution_universe != "NIFTY500"]

            amrc_trades = [t for t in trades if (t.recommendation.strategy_name if t.recommendation else "") == "amrc"]
            amrc_nifty = [t for t in amrc_trades if t.execution_universe == "NIFTY500"]
            amrc_non_nifty = [t for t in amrc_trades if t.execution_universe != "NIFTY500"]

            mftsm_trades = [t for t in trades if (t.recommendation.strategy_name if t.recommendation else "") == "mf_tsm"]
            mftsm_nifty = [t for t in mftsm_trades if t.execution_universe == "NIFTY500"]
            mftsm_non_nifty = [t for t in mftsm_trades if t.execution_universe != "NIFTY500"]

            overall_dict = get_stats(overall_trades)
            nifty500_dict = get_stats(nifty_trades)
            non_nifty500_dict = get_stats(non_nifty_trades)

            report_data = dict(overall_dict)
            report_data["overall"] = {
                "overall": overall_dict,
                "nifty500": nifty500_dict,
                "non_nifty500": non_nifty500_dict,
            }
            report_data["sivcs_vcp"] = {
                "overall": get_stats(sivcs_trades),
                "nifty500": get_stats(sivcs_nifty),
                "non_nifty500": get_stats(sivcs_non_nifty),
            }
            report_data["amrc"] = {
                "overall": get_stats(amrc_trades),
                "nifty500": get_stats(amrc_nifty),
                "non_nifty500": get_stats(amrc_non_nifty),
            }
            report_data["mf_tsm"] = {
                "overall": get_stats(mftsm_trades),
                "nifty500": get_stats(mftsm_nifty),
                "non_nifty500": get_stats(mftsm_non_nifty),
            }
            report_data["nifty500"] = nifty500_dict
            return report_data

    def generate_excel_report(self, db_session, universe: str = "all", accuracy: str = "all", save_path: str = "c:/Indian_Swing/indian_swing_historical_journal.xlsx") -> None:
        """Generate a professionally formatted Excel workbook representing the trading journal."""
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        from openpyxl.utils import get_column_letter

        wb = Workbook()
        
        # 1. Styles
        font_header = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        font_title = Font(name="Segoe UI", size=14, bold=True, color="1B365D")
        font_body = Font(name="Segoe UI", size=10)
        
        fill_header = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid")
        fill_green = PatternFill(start_color="D4EDDA", end_color="D4EDDA", fill_type="solid")
        fill_red = PatternFill(start_color="F8D7DA", end_color="F8D7DA", fill_type="solid")
        fill_yellow = PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid")
        
        thin_side = Side(border_style="thin", color="CCCCCC")
        border_all = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
        
        align_center = Alignment(horizontal="center", vertical="center")
        align_left = Alignment(horizontal="left", vertical="center")
        align_right = Alignment(horizontal="right", vertical="center")

        def style_sheet(ws, is_summary=False):
            ws.views.sheetView[0].showGridLines = True
            if not is_summary:
                ws.freeze_panes = "A2"
                # Apply headers
                for cell in ws[1]:
                    cell.font = font_header
                    cell.fill = fill_header
                    cell.alignment = align_center
                    cell.border = border_all
                ws.row_dimensions[1].height = 25
            else:
                ws.row_dimensions[1].height = 30

        # Sheet 1: Paper Trades
        ws_trades = wb.active
        ws_trades.title = "Paper Trades"
        
        headers_trades = [
            "Trade ID", "Scan UUID", "Recommendation UUID", "Symbol", "Company Name",
            "Exchange", "Sector", "Industry", "Execution Universe", "Accuracy %", "Scan Date", "Entry Date", "Entry Price",
            "Stop Loss", "Original Target Price", "Quantity", "Capital Allocated", "Exit Date", "Exit Price",
            "Exit Reason", "Holding Days", "Gross P&L", "Net P&L", "Return %", "Risk Amount",
            "Reward Amount", "R Multiple", "MFE %", "MAE %", "Highest Price", "Lowest Price",
            "Trade Status", "Strategy Version", "Indicator Version", "Data Provider"
        ]
        ws_trades.append(headers_trades)
        style_sheet(ws_trades)

        all_trades = db_session.execute(select(PaperTrade)).scalars().all()
        trades = []
        for t in all_trades:
            # Universe Filter
            if universe == "nifty500" and t.execution_universe != "NIFTY500":
                continue
            if universe == "non_nifty500" and t.execution_universe == "NIFTY500":
                continue
            
            # Accuracy Filter
            raw_score = (t.recommendation.confidence_score * 100) if (t.recommendation and t.recommendation.confidence_score is not None) else 0.0
            score = round(raw_score)
            if accuracy == '90_100':
                if not (90 <= score <= 100):
                    continue
            elif accuracy == '80_90':
                if not (80 <= score <= 90):
                    continue
            elif accuracy == '70_80':
                if not (70 <= score <= 80):
                    continue
            elif accuracy == 'below_70':
                if not (score < 70):
                    continue
            trades.append(t)

        for idx, t in enumerate(trades, start=2):
            rec = t.recommendation
            
            scan_date = str(rec.scan_date) if rec else "N/A"
            entry_date = str(t.entry_date) if t.entry_date else "N/A"
            exit_date = str(t.exit_date) if t.exit_date else "N/A"
            
            qty = rec.position_size or 0 if rec else 0
            effective_entry = t.entry_price if t.entry_price is not None else (rec.entry_price if rec else None)
            entry_val = effective_entry if effective_entry is not None else 0.0
            capital = qty * entry_val
            
            risk_amt = qty * (entry_val - (t.stop_loss or 0.0)) if (entry_val and t.stop_loss is not None) else 0.0
            reward_amt = qty * ((t.original_target_price or 0.0) - entry_val) if (entry_val and t.original_target_price is not None) else 0.0

            row_data = [
                t.id, rec.scan_uuid if rec else "N/A", rec.recommendation_uuid if rec else "N/A",
                t.symbol, rec.stock.name if (rec and rec.stock) else "N/A",
                rec.stock.exchange if (rec and rec.stock) else "N/A",
                rec.stock.sector if (rec and rec.stock) else "N/A",
                rec.stock.industry if (rec and rec.stock) else "N/A",
                t.execution_universe or "N/A",
                rec.confidence_score if rec else 0.0,
                scan_date, entry_date, effective_entry, t.stop_loss,
                t.original_target_price, qty, capital, exit_date, t.exit_price,
                t.exit_reason, t.holding_days, t.pnl_absolute, t.pnl_absolute,
                (t.pnl / 100.0) if t.pnl is not None else None, risk_amt, reward_amt, t.r_multiple,
                (t.max_favorable_excursion / 100.0) if t.max_favorable_excursion is not None else None,
                (t.max_adverse_excursion / 100.0) if t.max_adverse_excursion is not None else None,
                t.highest_price, t.lowest_price, t.status,
                rec.strategy_version if rec else "2.0.0",
                rec.indicator_version if rec else "1.0.0",
                "Upstox"
            ]
            ws_trades.append(row_data)
            
            # Formatting and styles
            for col_idx in range(1, len(headers_trades) + 1):
                cell = ws_trades.cell(row=idx, column=col_idx)
                cell.font = font_body
                cell.border = border_all
                
                # Alignments
                if col_idx in [1, 2, 3, 4, 6, 9, 10, 11, 12, 18, 20, 32, 33, 34, 35]:
                    cell.alignment = align_center
                elif col_idx in [5, 7, 8]:
                    cell.alignment = align_left
                else:
                    cell.alignment = align_right
                
                # Formats
                if col_idx in [13, 14, 15, 17, 19, 22, 23, 25, 26, 30, 31]:
                    cell.number_format = '"₹"#,##0.00'
                elif col_idx in [10, 24, 28, 29]:
                    cell.number_format = '0.00%'
                elif col_idx in [16, 21]:
                    cell.number_format = '#,##0'

            # Row colors
            status_cell = ws_trades.cell(row=idx, column=32)
            pnl_cell = ws_trades.cell(row=idx, column=24)
            if t.status == "Closed":
                fill_color = fill_green if (t.pnl or 0) > 0 else fill_red
            else:
                fill_color = fill_yellow
            
            status_cell.fill = fill_color
            pnl_cell.fill = fill_color

        # Sheet 2: Daily Recommendations
        ws_recs = wb.create_sheet(title="Daily Recommendations")
        headers_recs = [
            "Scan Date", "Symbol", "Company Name", "Entry", "Stop Loss", "Target",
            "Risk/Reward", "Recommendation Score", "Stage", "Relative Strength",
            "VCP Status", "Breakout Status", "Recommendation UUID", "Scan UUID"
        ]
        ws_recs.append(headers_recs)
        style_sheet(ws_recs)

        all_recs = db_session.execute(select(Recommendation)).scalars().all()
        recs = []
        for r in all_recs:
            raw_score = (r.confidence_score * 100) if r.confidence_score is not None else 0.0
            score = round(raw_score)
            if accuracy == '90_100':
                if not (90 <= score <= 100):
                    continue
            elif accuracy == '80_90':
                if not (80 <= score <= 90):
                    continue
            elif accuracy == '70_80':
                if not (70 <= score <= 80):
                    continue
            elif accuracy == 'below_70':
                if not (score < 70):
                    continue
            recs.append(r)

        for idx, r in enumerate(recs, start=2):
            sig = r.signal
            explanation = sig.explanation if sig else {}
            row_data = [
                str(r.scan_date), r.stock.symbol, r.stock.name, r.entry_price, r.stop_loss, r.target_price,
                sig.risk_reward if sig else 0.0, r.confidence_score,
                explanation.get("Stage", {}).get("status", "N/A"),
                explanation.get("Relative Strength", {}).get("status", "N/A"),
                explanation.get("VCP", {}).get("status", "N/A"),
                explanation.get("Breakout", {}).get("status", "N/A"),
                r.recommendation_uuid, r.scan_uuid
            ]
            ws_recs.append(row_data)
            
            for col_idx in range(1, len(headers_recs) + 1):
                cell = ws_recs.cell(row=idx, column=col_idx)
                cell.font = font_body
                cell.border = border_all
                if col_idx in [1, 2, 9, 10, 11, 12, 13, 14]:
                    cell.alignment = align_center
                elif col_idx == 3:
                    cell.alignment = align_left
                else:
                    cell.alignment = align_right
                
                if col_idx in [4, 5, 6]:
                    cell.number_format = '"₹"#,##0.00'
                elif col_idx in [7, 8]:
                    cell.number_format = '0.00'

        # Helper to generate Performance Sheets (Overall vs NIFTY500)
        def create_performance_sheet(ws_name, trades_list):
            ws_perf = wb.create_sheet(title=ws_name)
            style_sheet(ws_perf, is_summary=True)
            ws_perf.append([f"Historical Trading Strategy {ws_name} Summary"])
            ws_perf.cell(row=1, column=1).font = font_title
            ws_perf.cell(row=1, column=1).alignment = align_left
            
            c_trades = [t for t in trades_list if t.status == "Closed"]
            w_trades = [t for t in c_trades if (t.pnl or 0.0) > 0]
            l_trades = [t for t in c_trades if (t.pnl or 0.0) <= 0]
            a_trades = [t for t in trades_list if t.status in ["Active", "Pending"]]
            
            t_closed = len(c_trades)
            w_rate = (len(w_trades) / t_closed) if t_closed > 0 else 0.0
            l_rate = (len(l_trades) / t_closed) if t_closed > 0 else 0.0
            
            g_profit = sum(t.pnl_absolute for t in w_trades if t.pnl_absolute is not None)
            g_loss = abs(sum(t.pnl_absolute for t in l_trades if t.pnl_absolute is not None))
            p_factor = (g_profit / g_loss) if g_loss > 0 else (float('inf') if g_profit > 0 else 1.0)
            
            a_hold = sum(t.holding_days or 0 for t in c_trades) / t_closed if t_closed > 0 else 0.0
            a_ret = sum(t.pnl or 0.0 for t in c_trades) / t_closed if t_closed > 0 else 0.0
            a_r = sum(t.r_multiple or 0.0 for t in c_trades) / t_closed if t_closed > 0 else 0.0
            
            l_winner = max([t.pnl_absolute for t in w_trades if t.pnl_absolute is not None], default=0.0)
            l_loser = min([t.pnl_absolute for t in l_trades if t.pnl_absolute is not None], default=0.0)
            
            a_winner = g_profit / len(w_trades) if w_trades else 0.0
            a_loser = -g_loss / len(l_trades) if l_trades else 0.0
            
            cap_val = 1_000_000.0
            pk_val = cap_val
            m_dd = 0.0
            sorted_c = sorted(c_trades, key=lambda t: t.exit_date or date.min)
            for t in sorted_c:
                cap_val += (t.pnl_absolute or 0.0)
                if cap_val > pk_val:
                    pk_val = cap_val
                dd_val = (pk_val - cap_val) / pk_val * 100.0
                if dd_val > m_dd:
                    m_dd = dd_val

            cagr_val = 0.0
            if sorted_c:
                start_d = sorted_c[0].entry_date or sorted_c[0].created_at.date()
                end_d = sorted_c[-1].exit_date or sorted_c[-1].updated_at.date()
                if start_d and end_d:
                    days_c = (end_d - start_d).days
                    years_c = days_c / 365.25
                    if years_c > 0 and cap_val > 0:
                        cagr_val = ((cap_val / 1_000_000.0) ** (1 / years_c) - 1) * 100.0

            stats = [
                ("Total Trades (Completed)", t_closed, "#,##0"),
                ("Winning Trades", len(w_trades), "#,##0"),
                ("Losing Trades", len(l_trades), "#,##0"),
                ("Open/Active Trades", len(a_trades), "#,##0"),
                ("Win Rate", w_rate, "0.0%"),
                ("Loss Rate", l_rate, "0.0%"),
                ("Profit Factor", p_factor if not math.isinf(p_factor) else "Infinite", "0.00"),
                ("Average Holding Period", a_hold, "0.0 days"),
                ("Average Return per Trade", a_ret / 100.0, "0.00%"),
                ("Average R Multiple", a_r, "0.00"),
                ("Largest Winner", l_winner, '"₹"#,##0.00'),
                ("Largest Loser", l_loser, '"₹"#,##0.00'),
                ("Average Winner", a_winner, '"₹"#,##0.00'),
                ("Average Loser", a_loser, '"₹"#,##0.00'),
                ("Maximum Drawdown During Run", m_dd / 100.0, "0.00%"),
                ("CAGR", cagr_val / 100.0, "0.00%"),
                ("Total Net Return", cap_val - 1_000_000.0, '"₹"#,##0.00'),
                ("Ending Capital", cap_val, '"₹"#,##0.00'),
            ]

            ws_perf.append(["Performance Metric", "Value"])
            ws_perf.cell(row=2, column=1).font = Font(name="Segoe UI", bold=True)
            ws_perf.cell(row=2, column=2).font = Font(name="Segoe UI", bold=True)
            ws_perf.cell(row=2, column=1).border = Border(bottom=Side(style="medium"))
            ws_perf.cell(row=2, column=2).border = Border(bottom=Side(style="medium"))
            
            for r_idx, (m, val, fmt_str) in enumerate(stats, start=3):
                ws_perf.append([m, val])
                cell_m = ws_perf.cell(row=r_idx, column=1)
                cell_v = ws_perf.cell(row=r_idx, column=2)
                cell_m.font = font_body
                cell_v.font = font_body
                cell_m.border = border_all
                cell_v.border = border_all
                cell_v.alignment = align_right
                if fmt_str:
                    cell_v.number_format = fmt_str

        # Generate separate performance tabs
        create_performance_sheet("Overall Performance", trades)
        nifty_500_trades = [t for t in trades if t.execution_universe == "NIFTY500"]
        create_performance_sheet("NIFTY500 Performance", nifty_500_trades)

        # Sheet 4: Trade Timeline
        ws_timeline = wb.create_sheet(title="Trade Timeline")
        headers_timeline = [
            "Entry Date", "Exit Date", "Symbol", "Status", "Return %", "Running Equity", "Running Drawdown"
        ]
        ws_timeline.append(headers_timeline)
        style_sheet(ws_timeline)

        cap = 1_000_000.0
        pk = cap
        sorted_closed = sorted([t for t in trades if t.status == "Closed"], key=lambda t: t.exit_date or date.min)
        for idx, t in enumerate(sorted_closed, start=2):
            cap += (t.pnl_absolute or 0.0)
            if cap > pk:
                pk = cap
            dd = (pk - cap) / pk
            
            row_data = [
                str(t.entry_date), str(t.exit_date), t.symbol, t.status,
                (t.pnl / 100.0) if t.pnl is not None else 0.0, cap, dd
            ]
            ws_timeline.append(row_data)
            
            for col_idx in range(1, len(headers_timeline) + 1):
                cell = ws_timeline.cell(row=idx, column=col_idx)
                cell.font = font_body
                cell.border = border_all
                if col_idx in [1, 2, 3, 4]:
                    cell.alignment = align_center
                else:
                    cell.alignment = align_right
                
                if col_idx == 5:
                    cell.number_format = '0.00%'
                elif col_idx == 6:
                    cell.number_format = '"₹"#,##0.00'
                elif col_idx == 7:
                    cell.number_format = '0.00%'

        # Sheet 5: Scan Summary
        ws_scans = wb.create_sheet(title="Scan Summary")
        headers_scans = [
            "Scan Date", "Number of Stocks Scanned", "Number of Recommendations",
            "Scan Duration", "Active Trades", "Closed Trades", "Strategy Version", "Data Provider"
        ]
        ws_scans.append(headers_scans)
        style_sheet(ws_scans)

        jobs = db_session.execute(select(ScanJob).order_by(ScanJob.scan_date)).scalars().all()
        # Pre-query all recommendation IDs mapped to scan_uuid
        recs_rows = db_session.execute(select(Recommendation.scan_uuid, Recommendation.id)).all()
        rec_ids_by_scan: dict[str, list[str]] = {}
        for s_uuid, r_id in recs_rows:
            rec_ids_by_scan.setdefault(s_uuid, []).append(r_id)

        # Pre-query paper trades status mapped to recommendation_id
        trades_rows = db_session.execute(select(PaperTrade.recommendation_id, PaperTrade.status)).all()
        trade_status_by_rec: dict[str, str] = {r_id: status for r_id, status in trades_rows}

        for idx, j in enumerate(jobs, start=2):
            rec_ids = rec_ids_by_scan.get(j.scan_uuid, [])
            active_cnt = sum(1 for r_id in rec_ids if trade_status_by_rec.get(r_id) == "Active")
            closed_cnt = sum(1 for r_id in rec_ids if trade_status_by_rec.get(r_id) == "Closed")

            duration = ""
            if j.completed_at and j.started_at:
                duration = f"{round((j.completed_at - j.started_at).total_seconds(), 1)}s"
                
            row_data = [
                str(j.scan_date), j.stocks_scanned, j.recommendations_created,
                duration, active_cnt, closed_cnt, j.strategy_version, "Upstox"
            ]
            ws_scans.append(row_data)
            
            for col_idx in range(1, len(headers_scans) + 1):
                cell = ws_scans.cell(row=idx, column=col_idx)
                cell.font = font_body
                cell.border = border_all
                if col_idx in [1, 4, 7, 8]:
                    cell.alignment = align_center
                else:
                    cell.alignment = align_right
                
                if col_idx in [2, 3, 5, 6]:
                    cell.number_format = '#,##0'

        # Auto-size columns for all sheets
        for sheet in wb.worksheets:
            for col in sheet.columns:
                max_len = 0
                for cell in col:
                    # Ignore title row in Performance sheets when sizing columns
                    if "Performance" in sheet.title and cell.row == 1:
                        continue
                    val_str = str(cell.value or "")
                    if cell.number_format and ('%' in cell.number_format):
                        val_str += "%"
                    if len(val_str) > max_len:
                        max_len = len(val_str)
                col_letter = get_column_letter(col[0].column)
                sheet.column_dimensions[col_letter].width = max(max_len + 4, 12)
                
            # Add auto-filters on row 1 headers
            if "Performance" not in sheet.title:
                sheet.auto_filter.ref = f"A1:{get_column_letter(sheet.max_column)}{sheet.max_row}"

        wb.save(save_path)

