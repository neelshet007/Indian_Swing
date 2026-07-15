from __future__ import annotations

from datetime import date
from typing import Sequence

from sqlalchemy import and_, case, distinct, func, select
from sqlalchemy.orm import Session, joinedload

from indian_swing.database.models import Recommendation, ScanJob, Signal
from indian_swing.database.repositories.base import BaseRepository


class SignalRepository(BaseRepository[Signal]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Signal)

    def get_by_stock_date(self, stock_uuid: str, signal_date: date, strategy: str | None = None) -> Sequence[Signal]:
        query = select(Signal).where(
            and_(Signal.stock_uuid == stock_uuid, Signal.signal_date == signal_date)
        )
        if strategy:
            query = query.where(Signal.strategy_name == strategy)
        return self._session.execute(query.order_by(Signal.confidence_score.desc())).scalars().all()


class RecommendationRepository(BaseRepository[Recommendation]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Recommendation)

    def get_by_scan(self, scan_uuid: str) -> Sequence[Recommendation]:
        return self._session.execute(
            select(Recommendation)
            .where(Recommendation.scan_uuid == scan_uuid)
            .options(joinedload(Recommendation.stock), joinedload(Recommendation.signal))
            .order_by(Recommendation.rank)
        ).scalars().all()

    def get_by_date(self, scan_date: date) -> Sequence[Recommendation]:
        from datetime import datetime, timedelta
        from sqlalchemy import and_
        stale_cutoff = datetime.utcnow() - timedelta(hours=2)
        # A 'running' job is only considered live if it started within the last 2 hours.
        # Stale orphans (server killed) must not shadow completed scans.
        latest_scan = self._session.execute(
            select(ScanJob.scan_uuid)
            .where(
                ScanJob.scan_date == scan_date,
                (
                    (ScanJob.status == "completed") |
                    ((ScanJob.status == "running") & (ScanJob.started_at >= stale_cutoff))
                ),
            )
            .order_by(
                case((ScanJob.status == "running", 1), (ScanJob.status == "completed", 2), else_=3).asc(),
                ScanJob.created_at.desc(),
            )
            .limit(1)
        ).scalar_one_or_none()
        if not latest_scan:
            return []
        return self.get_by_scan(latest_scan)

    def get_latest(self, limit: int = 50) -> Sequence[Recommendation]:
        from datetime import datetime, timedelta
        stale_cutoff = datetime.utcnow() - timedelta(hours=2)
        latest_scan = self._session.execute(
            select(ScanJob.scan_uuid)
            .where(
                (ScanJob.status == "completed") |
                ((ScanJob.status == "running") & (ScanJob.started_at >= stale_cutoff))
            )
            .order_by(
                case((ScanJob.status == "running", 1), (ScanJob.status == "completed", 2), else_=3).asc(),
                ScanJob.created_at.desc(),
            )
            .limit(1)
        ).scalar_one_or_none()
        if not latest_scan:
            return []
        return self._session.execute(
            select(Recommendation)
            .where(Recommendation.scan_uuid == latest_scan)
            .options(joinedload(Recommendation.stock), joinedload(Recommendation.signal))
            .order_by(Recommendation.rank)
            .limit(limit)
        ).scalars().all()

    def get_latest_scan(self) -> ScanJob | None:
        from datetime import datetime, timedelta
        stale_cutoff = datetime.utcnow() - timedelta(hours=2)
        return self._session.execute(
            select(ScanJob)
            .where(
                (ScanJob.status == "completed") |
                ((ScanJob.status == "running") & (ScanJob.started_at >= stale_cutoff))
            )
            .order_by(
                case((ScanJob.status == "running", 1), (ScanJob.status == "completed", 2), else_=3).asc(),
                ScanJob.created_at.desc(),
            )
            .limit(1)
        ).scalar_one_or_none()

    def get_available_dates(self, limit: int = 30) -> list[date]:
        return list(
            self._session.execute(
                select(distinct(ScanJob.scan_date))
                .where(ScanJob.status == "completed")
                .order_by(ScanJob.scan_date.desc())
                .limit(limit)
            ).scalars().all()
        )
