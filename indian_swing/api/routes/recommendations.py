from __future__ import annotations

import asyncio
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from indian_swing.database.connection import get_sync_session
from indian_swing.database.models import Recommendation
from indian_swing.database.repositories.signal_repo import RecommendationRepository

router = APIRouter()


@router.get("/")
async def get_recommendations(
    scan_date: Optional[date] = Query(None),
    limit: int = Query(50, le=200),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
):
    loop = asyncio.get_running_loop()

    def _fetch() -> list[dict]:
        with get_sync_session() as session:
            repo = RecommendationRepository(session)
            recommendations = repo.get_by_date(scan_date) if scan_date else repo.get_latest(limit=limit)
            result: list[dict] = []
            for recommendation in recommendations:
                if recommendation.confidence_score < min_confidence:
                    continue
                result.append(_serialize_recommendation(recommendation))
            return result

    return await loop.run_in_executor(None, _fetch)


@router.get("/latest")
async def get_latest_scan_snapshot():
    loop = asyncio.get_running_loop()

    def _fetch() -> dict:
        with get_sync_session() as session:
            repo = RecommendationRepository(session)
            scan = repo.get_latest_scan()
            if scan is None:
                return {
                    "scan": None,
                    "recommendations": [],
                }
            recommendations = [_serialize_recommendation(rec) for rec in repo.get_by_scan(scan.id)]
            return {
                "scan": {
                    "id": scan.id,
                    "scan_date": str(scan.scan_date),
                    "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
                    "market_status": scan.market_status,
                    "total_stocks": scan.total_stocks,
                    "stocks_scanned": scan.stocks_scanned,
                    "failed_stocks": scan.failed_stocks,
                    "filter_summary": scan.filter_summary,
                    "validation_summary": scan.validation_summary,
                    "recommendations_created": scan.recommendations_created,
                },
                "recommendations": recommendations,
            }

    return await loop.run_in_executor(None, _fetch)


@router.get("/dates/available")
async def get_available_scan_dates():
    loop = asyncio.get_running_loop()
    def _fetch():
        with get_sync_session() as session:
            return {"dates": [str(value) for value in RecommendationRepository(session).get_available_dates()]}
    return await loop.run_in_executor(None, _fetch)


@router.get("/{rec_id}")
async def get_recommendation_detail(rec_id: str):
    loop = asyncio.get_running_loop()

    def _fetch() -> dict | None:
        with get_sync_session() as session:
            recommendation = session.get(Recommendation, rec_id)
            return _serialize_recommendation(recommendation, detailed=True) if recommendation else None

    result = await loop.run_in_executor(None, _fetch)
    if result is None:
        raise HTTPException(status_code=404, detail="Recommendation not found.")
    return result


def _serialize_recommendation(recommendation: Recommendation, detailed: bool = False) -> dict:
    stock = recommendation.stock
    signal = recommendation.signal
    payload = {
        "id": recommendation.id,
        "recommendation_uuid": recommendation.recommendation_uuid,
        "scan_job_id": recommendation.scan_job_id,
        "scan_date": str(recommendation.scan_date),
        "strategy_name": recommendation.strategy_name,
        "strategy_version": recommendation.strategy_version,
        "rank": recommendation.rank,
        "action": recommendation.action,
        "confidence_score": recommendation.confidence_score,
        "risk_level": recommendation.risk_level,
        "symbol": stock.symbol,
        "exchange": stock.exchange,
        "company_name": stock.name,
        "sector": stock.sector,
        "entry_price": recommendation.entry_price,
        "stop_loss": recommendation.stop_loss,
        "target_1": recommendation.target_price,
        "risk_reward": signal.risk_reward,
        "holding_days": signal.holding_days,
        "quality": signal.quality,
        "reasons": signal.reasons,
        "position_size": recommendation.position_size,
        "portfolio_weight_pct": recommendation.portfolio_weight_pct,
        "summary": recommendation.summary,
        "explanation": recommendation.explanation,
        "indicator_snapshot": signal.indicator_snapshot,
        "generated_at": recommendation.generated_at.isoformat() if recommendation.generated_at else None,
    }
    if detailed:
        payload["metadata"] = signal.metadata_
    return payload
