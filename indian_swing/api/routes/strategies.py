from __future__ import annotations

from fastapi import APIRouter

from indian_swing.strategies.registry import strategy_registry

router = APIRouter()


@router.get("/")
async def list_strategies():
    strategy_registry.discover()
    return [
        {
            "name": s.name,
            "description": s.description,
            "version": s.version,
            "required_lookback": s.required_lookback,
            "default_params": s.default_params,
        }
        for s in strategy_registry.all()
    ]
