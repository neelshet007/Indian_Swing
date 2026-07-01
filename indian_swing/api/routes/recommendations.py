from __future__ import annotations

import asyncio
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from indian_swing.database.connection import get_sync_session
from indian_swing.database.models import Recommendation, Signal, Stock
from indian_swing.database.repositories.signal_repo import RecommendationRepository

router = APIRouter()


@router.get("/")
async def get_recommendations(
    scan_date: Optional[date] = Query(None),
    limit: int = Query(50, le=200),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
):
    loop = asyncio.get_event_loop()

    def _fetch():
        with get_sync_session() as session:
            repo = RecommendationRepository(session)
            if scan_date:
                recs = repo.get_by_date(scan_date)
            else:
                recs = repo.get_latest(limit=limit)

            result = []
            for rec in recs:
                if rec.confidence_score < min_confidence:
                    continue
                stock = session.get(Stock, rec.stock_id)
                signal = session.get(Signal, rec.signal_id)
                if stock and signal:
                    result.append(_rec_dict(rec, stock, signal))
            return result

    return await loop.run_in_executor(None, _fetch)


@router.get("/dates/available")
async def get_available_scan_dates():
    loop = asyncio.get_event_loop()

    def _fetch():
        with get_sync_session() as session:
            repo = RecommendationRepository(session)
            return [str(d) for d in repo.get_available_dates()]

    dates = await loop.run_in_executor(None, _fetch)
    return {"dates": dates}


@router.get("/{rec_id}")
async def get_recommendation_detail(rec_id: str):
    loop = asyncio.get_event_loop()

    def _fetch():
        with get_sync_session() as session:
            rec = session.get(Recommendation, rec_id)
            if not rec:
                return None
            stock = session.get(Stock, rec.stock_id)
            signal = session.get(Signal, rec.signal_id)
            return _rec_dict(rec, stock, signal, detailed=True)

    result = await loop.run_in_executor(None, _fetch)
    if result is None:
        raise HTTPException(status_code=404, detail="Recommendation not found.")
    return result


def _rec_dict(rec, stock, signal, detailed=False) -> dict:
    base = {
        "id": rec.id,
        "rank": rec.rank,
        "scan_date": str(rec.scan_date),
        "confidence_score": rec.confidence_score,
        "risk_level": rec.risk_level,
        "symbol": stock.symbol,
        "company_name": stock.name,
        "sector": stock.sector,
        "strategy_name": signal.strategy_name,
        "direction": signal.direction,
        "entry_price": signal.entry_price,
        "stop_loss": signal.stop_loss,
        "target_1": signal.target_1,
        "target_2": signal.target_2,
        "risk_reward": signal.risk_reward,
        "holding_days": signal.holding_days,
        "quality": signal.quality,
        "reasons": signal.reasons,
        "historical_win_rate": rec.historical_win_rate,
        "summary": rec.summary,
    }
    if detailed:
        base["metadata"] = signal.metadata_
    return base
