from __future__ import annotations

from datetime import date
from typing import Sequence

from sqlalchemy import and_, select, func, distinct
from sqlalchemy.orm import Session

from indian_swing.database.models import Recommendation, Signal
from indian_swing.database.repositories.base import BaseRepository


class SignalRepository(BaseRepository[Signal]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Signal)

    def get_by_stock_date(
        self, stock_id: int, signal_date: date, strategy: str | None = None
    ) -> Sequence[Signal]:
        q = select(Signal).where(
            and_(Signal.stock_id == stock_id, Signal.signal_date == signal_date)
        )
        if strategy:
            q = q.where(Signal.strategy_name == strategy)
        return self._session.execute(q.order_by(Signal.confidence_score.desc())).scalars().all()


class RecommendationRepository(BaseRepository[Recommendation]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Recommendation)

    def get_by_date(self, scan_date: date) -> Sequence[Recommendation]:
        return self._session.execute(
            select(Recommendation)
            .where(Recommendation.scan_date == scan_date)
            .order_by(Recommendation.rank)
        ).scalars().all()

    def get_latest(self, limit: int = 50) -> Sequence[Recommendation]:
        latest_date = self._session.execute(
            select(func.max(Recommendation.scan_date))
        ).scalar_one_or_none()
        if not latest_date:
            return []
        return self._session.execute(
            select(Recommendation)
            .where(Recommendation.scan_date == latest_date)
            .order_by(Recommendation.rank)
            .limit(limit)
        ).scalars().all()

    def get_available_dates(self, limit: int = 30) -> list[date]:
        result = self._session.execute(
            select(distinct(Recommendation.scan_date))
            .order_by(Recommendation.scan_date.desc())
            .limit(limit)
        ).scalars().all()
        return list(result)
