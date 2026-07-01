"""
Generic sync repository base. Compatible with Python 3.14 (no greenlet).
"""
from __future__ import annotations

from typing import Any, Generic, Sequence, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from indian_swing.database.models import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    def __init__(self, session: Session, model: Type[ModelT]) -> None:
        self._session = session
        self._model = model

    def get_by_id(self, id_: Any) -> ModelT | None:
        return self._session.get(self._model, id_)

    def all(self) -> Sequence[ModelT]:
        return self._session.execute(select(self._model)).scalars().all()

    def add(self, obj: ModelT) -> ModelT:
        self._session.add(obj)
        self._session.flush()
        return obj

    def add_all(self, objs: list[ModelT]) -> None:
        self._session.add_all(objs)
        self._session.flush()

    def delete(self, obj: ModelT) -> None:
        self._session.delete(obj)
        self._session.flush()
