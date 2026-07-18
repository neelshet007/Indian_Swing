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

    def get_active_session(self) -> Optional[HistoricalScanSession]:
        """Find an active historical scan session."""
        with get_sync_session() as session:
            return session.execute(
                select(HistoricalScanSession)
                .where(HistoricalScanSession.status == "active")
                .order_by(HistoricalScanSession.created_at.desc())
            ).scalars().first()

    def create_session(self, dates: List[date]) -> HistoricalScanSession:
        """Create a new historical scan session."""
        with get_sync_session() as session:
            # Delete older active sessions to avoid conflicts
            session.execute(
                delete(HistoricalScanSession).where(HistoricalScanSession.status == "active")
            )
            
            queue_str = [d.strftime("%d/%m/%y") for d in dates]
            new_session = HistoricalScanSession(
                total_days=len(dates),
                completed_days=0,
                queue=queue_str,
                status="active"
            )
            session.add(new_session)
            session.commit()
            
            # Retrieve from fresh query
            return session.get(HistoricalScanSession, new_session.id)

    def update_paper_trades(self, db_session, current_date: date) -> None:
        """Update entry/exit triggers for all active/pending paper trades on current_date."""
        # 1. Fetch pending and active paper trades
        trades = db_session.execute(
            select(PaperTrade).where(PaperTrade.status.in_(["Pending", "Active"]))
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

        # Time Exit
        holding_days = (current_date - trade.entry_date).days
        max_holding = rec.signal.holding_days if (rec.signal and rec.signal.holding_days is not None) else 45
        if holding_days >= max_holding:
            self._close_trade(trade, rec, current_date, c_close, "Time Exit")
            return


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
                paper_trade = PaperTrade(
                    recommendation_id=rec.id,
                    stock_uuid=rec.stock_uuid,
                    symbol=rec.stock.symbol,
                    status="Pending"
                )
                db_session.add(paper_trade)
                created_count += 1
        if created_count > 0:
            db_session.flush()
        return created_count

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

            if not trades:
                return {
                    "total_scans": len(total_scans),
                    "total_recommendations": len(total_recs),
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "loss_rate": 0.0,
                    "profit_factor": 0.0,
                    "expectancy": 0.0,
                    "cagr": 0.0,
                    "max_drawdown": 0.0,
                    "avg_holding_period": 0.0,
                    "avg_r_multiple": 0.0,
                    "monthly_stats": {},
                    "yearly_stats": {},
                    "equity_curve": [],
                    "journal": []
                }

            wins = [t for t in trades if t.pnl > 0]
            losses = [t for t in trades if t.pnl <= 0]
            
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
            expectancy = sum(pnls) / len(trades) if pnls else 0.0

            sorted_trades = sorted(trades, key=lambda t: t.exit_date or date.min)
            
            capital = 1_000_000.0
            equity_curve = [{"date": str(sorted_trades[0].entry_date), "equity": capital}]
            peak_equity = capital
            max_dd = 0.0
            
            for t in sorted_trades:
                pnl_abs = t.pnl_absolute or 0.0
                capital += pnl_abs
                equity_curve.append({"date": str(t.exit_date), "equity": capital})
                
                if capital > peak_equity:
                    peak_equity = capital
                dd = (peak_equity - capital) / peak_equity * 100
                if dd > max_dd:
                    max_dd = dd

            if sorted_trades:
                start_date = sorted_trades[0].entry_date
                end_date = sorted_trades[-1].exit_date
                days = (end_date - start_date).days
                years = days / 365.25
                if years > 0 and capital > 0:
                    cagr = ((capital / 1_000_000.0) ** (1 / years) - 1) * 100
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
                }
                for t in sorted_trades
            ]

            return {
                "total_scans": len(total_scans),
                "total_recommendations": len(total_recs),
                "total_trades": len(trades),
                "win_rate": round(win_rate, 2),
                "loss_rate": round(loss_rate, 2),
                "profit_factor": round(profit_factor, 2) if not math.isinf(profit_factor) else "Infinite",
                "expectancy": round(expectancy, 2),
                "cagr": round(cagr, 2),
                "max_drawdown": round(max_dd, 2),
                "avg_holding_period": round(avg_hold, 2),
                "avg_r_multiple": round(avg_r, 2),
                "monthly_stats": monthly_stats,
                "yearly_stats": yearly_stats,
                "equity_curve": equity_curve,
                "journal": journal
            }

    def generate_excel_report(self, db_session) -> None:
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
            "Exchange", "Sector", "Industry", "Scan Date", "Entry Date", "Entry Price",
            "Stop Loss", "Target", "Quantity", "Capital Allocated", "Exit Date", "Exit Price",
            "Exit Reason", "Holding Days", "Gross P&L", "Net P&L", "Return %", "Risk Amount",
            "Reward Amount", "R Multiple", "MFE %", "MAE %", "Highest Price", "Lowest Price",
            "Trade Status", "Strategy Version", "Indicator Version", "Data Provider"
        ]
        ws_trades.append(headers_trades)
        style_sheet(ws_trades)

        trades = db_session.execute(select(PaperTrade)).scalars().all()
        for idx, t in enumerate(trades, start=2):
            rec = t.recommendation
            sig = rec.signal if rec else None
            
            scan_date = str(rec.scan_date) if rec else "N/A"
            entry_date = str(t.entry_date) if t.entry_date else "N/A"
            exit_date = str(t.exit_date) if t.exit_date else "N/A"
            
            qty = rec.position_size or 0 if rec else 0
            capital = qty * (t.entry_price or 0.0)
            
            risk_amt = qty * ((t.entry_price or 0.0) - (rec.stop_loss or 0.0)) if (t.entry_price and rec) else 0.0
            reward_amt = qty * ((rec.target_price or 0.0) - (t.entry_price or 0.0)) if (t.entry_price and rec) else 0.0

            row_data = [
                t.id, rec.scan_uuid if rec else "N/A", rec.recommendation_uuid if rec else "N/A",
                t.symbol, rec.stock.name if (rec and rec.stock) else "N/A",
                rec.stock.exchange if (rec and rec.stock) else "N/A",
                rec.stock.sector if (rec and rec.stock) else "N/A",
                rec.stock.industry if (rec and rec.stock) else "N/A",
                scan_date, entry_date, t.entry_price, rec.stop_loss if rec else None,
                rec.target_price if rec else None, qty, capital, exit_date, t.exit_price,
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
                if col_idx in [1, 2, 3, 4, 6, 9, 10, 16, 18, 30, 31, 32, 33]:
                    cell.alignment = align_center
                elif col_idx in [5, 7, 8]:
                    cell.alignment = align_left
                else:
                    cell.alignment = align_right
                
                # Formats
                if col_idx in [11, 12, 13, 15, 17, 20, 21, 23, 24, 28, 29]:
                    cell.number_format = '"₹"#,##0.00'
                elif col_idx in [22, 26, 27]:
                    cell.number_format = '0.00%'
                elif col_idx in [14, 19]:
                    cell.number_format = '#,##0'

            # Row colors
            status_cell = ws_trades.cell(row=idx, column=30)
            pnl_cell = ws_trades.cell(row=idx, column=22)
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

        recs = db_session.execute(select(Recommendation)).scalars().all()
        for idx, r in enumerate(recs, start=2):
            sig = r.signal
            explanation = sig.explanation if sig else {}
            row_data = [
                str(r.scan_date), r.stock.symbol, r.stock.name, r.entry_price, r.stop_loss, r.target_price,
                r.risk_reward, r.confidence_score,
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

        # Sheet 3: Performance Summary
        ws_summary = wb.create_sheet(title="Performance Summary")
        style_sheet(ws_summary, is_summary=True)
        ws_summary.append(["Historical Trading Strategy Performance Summary"])
        ws_summary.cell(row=1, column=1).font = font_title
        ws_summary.cell(row=1, column=1).alignment = align_left
        
        # Calculate stats
        closed_trades = [t for t in trades if t.status == "Closed"]
        wins = [t for t in closed_trades if (t.pnl or 0.0) > 0]
        losses = [t for t in closed_trades if (t.pnl or 0.0) <= 0]
        active_trades = [t for t in trades if t.status in ["Active", "Pending"]]
        
        total_closed = len(closed_trades)
        win_rate = (len(wins) / total_closed) if total_closed > 0 else 0.0
        loss_rate = (len(losses) / total_closed) if total_closed > 0 else 0.0
        
        gross_profit = sum(t.pnl_absolute for t in wins if t.pnl_absolute is not None)
        gross_loss = abs(sum(t.pnl_absolute for t in losses if t.pnl_absolute is not None))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (float('inf') if gross_profit > 0 else 1.0)
        
        avg_hold = sum(t.holding_days or 0 for t in closed_trades) / total_closed if total_closed > 0 else 0.0
        avg_ret = sum(t.pnl or 0.0 for t in closed_trades) / total_closed if total_closed > 0 else 0.0
        avg_r = sum(t.r_multiple or 0.0 for t in closed_trades) / total_closed if total_closed > 0 else 0.0
        
        largest_winner = max([t.pnl_absolute for t in wins if t.pnl_absolute is not None], default=0.0)
        largest_loser = min([t.pnl_absolute for t in losses if t.pnl_absolute is not None], default=0.0)
        
        avg_winner = gross_profit / len(wins) if wins else 0.0
        avg_loser = -gross_loss / len(losses) if losses else 0.0
        
        # Drawdown and CAGR calculations
        capital = 1_000_000.0
        peak = capital
        max_dd = 0.0
        sorted_closed = sorted(closed_trades, key=lambda t: t.exit_date or date.min)
        for t in sorted_closed:
            capital += (t.pnl_absolute or 0.0)
            if capital > peak:
                peak = capital
            dd = (peak - capital) / peak * 100.0
            if dd > max_dd:
                max_dd = dd

        cagr = 0.0
        if sorted_closed:
            start_d = sorted_closed[0].entry_date
            end_d = sorted_closed[-1].exit_date
            if start_d and end_d:
                days = (end_d - start_d).days
                years = days / 365.25
                if years > 0 and capital > 0:
                    cagr = ((capital / 1_000_000.0) ** (1 / years) - 1) * 100.0

        stats = [
            ("Total Trades (Completed)", total_closed, "#,##0"),
            ("Winning Trades", len(wins), "#,##0"),
            ("Losing Trades", len(losses), "#,##0"),
            ("Open/Active Trades", len(active_trades), "#,##0"),
            ("Win Rate", win_rate, "0.0%"),
            ("Loss Rate", loss_rate, "0.0%"),
            ("Profit Factor", profit_factor if not math.isinf(profit_factor) else "Infinite", "0.00"),
            ("Average Holding Period", avg_hold, "0.0 days"),
            ("Average Return per Trade", avg_ret / 100.0, "0.00%"),
            ("Average R Multiple", avg_r, "0.00"),
            ("Largest Winner", largest_winner, '"₹"#,##0.00'),
            ("Largest Loser", largest_loser, '"₹"#,##0.00'),
            ("Average Winner", avg_winner, '"₹"#,##0.00'),
            ("Average Loser", avg_loser, '"₹"#,##0.00'),
            ("Maximum Drawdown During Run", max_dd / 100.0, "0.00%"),
            ("CAGR", cagr / 100.0, "0.00%"),
            ("Total Net Return", capital - 1_000_000.0, '"₹"#,##0.00'),
            ("Ending Capital", capital, '"₹"#,##0.00'),
        ]

        ws_summary.append(["Performance Metric", "Value"])
        ws_summary.cell(row=2, column=1).font = Font(name="Segoe UI", bold=True)
        ws_summary.cell(row=2, column=2).font = Font(name="Segoe UI", bold=True)
        ws_summary.cell(row=2, column=1).border = Border(bottom=Side(style="medium"))
        ws_summary.cell(row=2, column=2).border = Border(bottom=Side(style="medium"))
        
        for r_idx, (m, val, fmt) in enumerate(stats, start=3):
            ws_summary.append([m, val])
            cell_m = ws_summary.cell(row=r_idx, column=1)
            cell_v = ws_summary.cell(row=r_idx, column=2)
            cell_m.font = font_body
            cell_v.font = font_body
            cell_m.border = border_all
            cell_v.border = border_all
            cell_v.alignment = align_right
            if fmt:
                cell_v.number_format = fmt

        # Sheet 4: Trade Timeline
        ws_timeline = wb.create_sheet(title="Trade Timeline")
        headers_timeline = [
            "Entry Date", "Exit Date", "Symbol", "Status", "Return %", "Running Equity", "Running Drawdown"
        ]
        ws_timeline.append(headers_timeline)
        style_sheet(ws_timeline)

        cap = 1_000_000.0
        pk = cap
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

        jobs = db_session.execute(select(ScanJob).where(ScanJob.strategy_name == "sivcs_vcp").order_by(ScanJob.scan_date)).scalars().all()
        for idx, j in enumerate(jobs, start=2):
            recs_for_job = db_session.execute(select(Recommendation).where(Recommendation.scan_uuid == j.scan_uuid)).scalars().all()
            rec_ids = [r.id for r in recs_for_job]
            active_cnt = 0
            closed_cnt = 0
            if rec_ids:
                active_cnt = len(db_session.execute(select(PaperTrade).where(PaperTrade.recommendation_id.in_(rec_ids), PaperTrade.status == "Active")).scalars().all())
                closed_cnt = len(db_session.execute(select(PaperTrade).where(PaperTrade.recommendation_id.in_(rec_ids), PaperTrade.status == "Closed")).scalars().all())

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
                    # Ignore title row in Performance Summary when sizing columns
                    if sheet.title == "Performance Summary" and cell.row == 1:
                        continue
                    val_str = str(cell.value or "")
                    if cell.number_format and ('%' in cell.number_format):
                        val_str += "%"
                    if len(val_str) > max_len:
                        max_len = len(val_str)
                col_letter = get_column_letter(col[0].column)
                sheet.column_dimensions[col_letter].width = max(max_len + 4, 12)
                
            # Add auto-filters on row 1 headers
            if sheet.title != "Performance Summary":
                sheet.auto_filter.ref = f"A1:{get_column_letter(sheet.max_column)}{sheet.max_row}"

        wb.save("c:/Indian_Swing/indian_swing_historical_journal.xlsx")

