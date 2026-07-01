from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from indian_swing.core.exceptions import ReplayError, ReplaySessionNotFoundError
from indian_swing.replay.engine import replay_engine

router = APIRouter()


class CreateReplayRequest(BaseModel):
    symbol: str
    strategy_name: str
    start_date: date
    end_date: date


@router.post("/sessions")
async def create_replay_session(req: CreateReplayRequest):
    try:
        session_id = await replay_engine.create_session(
            symbol=req.symbol,
            strategy_name=req.strategy_name,
            start_date=req.start_date,
            end_date=req.end_date,
        )
        session = replay_engine.get_session(session_id)
        state = session.current_state()
        return {"session_id": session_id, "state": _state_dict(state)}
    except ReplayError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_replay_state(session_id: str):
    try:
        session = replay_engine.get_session(session_id)
        return _state_dict(session.current_state())
    except ReplaySessionNotFoundError:
        raise HTTPException(status_code=404, detail="Replay session not found.")


@router.post("/sessions/{session_id}/forward")
async def step_forward(session_id: str, steps: int = 1):
    try:
        session = replay_engine.get_session(session_id)
        return _state_dict(session.step_forward(steps))
    except ReplaySessionNotFoundError:
        raise HTTPException(status_code=404, detail="Replay session not found.")


@router.post("/sessions/{session_id}/backward")
async def step_backward(session_id: str, steps: int = 1):
    try:
        session = replay_engine.get_session(session_id)
        return _state_dict(session.step_backward(steps))
    except ReplaySessionNotFoundError:
        raise HTTPException(status_code=404, detail="Replay session not found.")


@router.post("/sessions/{session_id}/restart")
async def restart_session(session_id: str):
    try:
        session = replay_engine.get_session(session_id)
        return _state_dict(session.restart())
    except ReplaySessionNotFoundError:
        raise HTTPException(status_code=404, detail="Replay session not found.")


@router.post("/sessions/{session_id}/jump")
async def jump_to_date(session_id: str, target_date: date):
    try:
        session = replay_engine.get_session(session_id)
        return _state_dict(session.jump_to_date(target_date))
    except ReplaySessionNotFoundError:
        raise HTTPException(status_code=404, detail="Replay session not found.")


@router.delete("/sessions/{session_id}")
async def destroy_session(session_id: str):
    replay_engine.destroy_session(session_id)
    return {"status": "destroyed", "session_id": session_id}


@router.websocket("/sessions/{session_id}/ws")
async def replay_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket for real-time replay playback.
    Client sends: {"action": "forward"|"backward"|"restart"|"jump", "steps": N, "date": "YYYY-MM-DD"}
    Server sends: state JSON after each action.
    """
    await websocket.accept()
    try:
        session = replay_engine.get_session(session_id)
    except ReplaySessionNotFoundError:
        await websocket.close(code=4004, reason="Session not found")
        return

    try:
        while True:
            msg = await websocket.receive_json()
            action = msg.get("action", "forward")
            steps = msg.get("steps", 1)

            if action == "forward":
                state = session.step_forward(steps)
            elif action == "backward":
                state = session.step_backward(steps)
            elif action == "restart":
                state = session.restart()
            elif action == "jump":
                from datetime import date as date_type
                target = date_type.fromisoformat(msg["date"])
                state = session.jump_to_date(target)
            else:
                state = session.current_state()

            await websocket.send_json(_state_dict(state))
    except WebSocketDisconnect:
        pass


def _state_dict(state) -> dict:
    return {
        "session_id": state.session_id,
        "symbol": state.symbol,
        "strategy_name": state.strategy_name,
        "current_index": state.current_index,
        "total_candles": state.total_candles,
        "progress_pct": state.progress_pct,
        "current_date": str(state.current_date),
        "candles": state.candles,
        "indicators": state.indicators,
        "signal": state.signal,
        "open_trade": state.open_trade,
        "pnl": state.pnl,
        "cumulative_pnl": state.cumulative_pnl,
        "drawdown": state.drawdown,
        "mfe": state.mfe,
        "mae": state.mae,
        "is_complete": state.is_complete,
    }
