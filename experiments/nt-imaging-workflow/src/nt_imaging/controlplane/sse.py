from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

from fastapi import Depends, FastAPI, Request
from fastapi.responses import StreamingResponse

from .db import ControlDB, iso, now
from .worker import public_state

_connections = 0


def active_sse_connections() -> int:
    return _connections


def _frame(event_type: str, data: dict[str, Any], sequence: int | None = None) -> str:
    identifier = f"id: {sequence}\n" if sequence is not None else ""
    return f"{identifier}event: {event_type}\ndata: {json.dumps(data, default=str)}\n\n"


def _snapshots(db: ControlDB, run_id: str | None) -> dict[str, Any]:
    if run_id:
        return {
            "run": public_state(db.snapshot(run_id) or {}),
            "last_sequence": db.latest_sequence(),
        }
    return {
        "runs": [public_state(run) for run in db.snapshots()],
        "last_sequence": db.latest_sequence(),
    }


async def event_stream(
    request: Request, db: ControlDB, run_id: str | None = None
) -> AsyncIterator[str]:
    global _connections
    try:
        last = int(request.headers.get("last-event-id", "0"))
    except ValueError:
        last = 0
    last = max(0, last)
    last_run_sequence = db.run_sequence_for_event(last) or 0 if run_id else 0
    heartbeat_count = 0
    _connections += 1
    try:
        yield "retry: 3000\n\n"
        yield _frame("snapshot", _snapshots(db, run_id), db.latest_sequence())
        while True:
            if await request.is_disconnected():
                break
            events = db.events(after=last, run_id=run_id, limit=500)
            for event in events:
                sequence = int(event["sequence"])
                run_sequence = event.get("run_sequence")
                gap = (
                    sequence > last + 1
                    if not run_id
                    else bool(
                        last_run_sequence and run_sequence and run_sequence > last_run_sequence + 1
                    )
                )
                if gap:
                    yield _frame("resync", _snapshots(db, run_id), db.latest_sequence())
                yield _frame(str(event["event_type"]), event, sequence)
                last = max(last, sequence)
                if run_sequence:
                    last_run_sequence = max(last_run_sequence, int(run_sequence))
            heartbeat_count += 1
            if heartbeat_count % 20 == 0:
                if not db.session(request.cookies.get("__Host-nt_session", "")):
                    yield _frame("session-expired", {"message": "Session expired"})
                    break
                yield _frame("heartbeat", {"timestamp_utc": iso(now())})
            await asyncio.sleep(0.5)
    finally:
        _connections -= 1


def sse_response(request: Request, db: ControlDB, run_id: str | None = None) -> StreamingResponse:
    return StreamingResponse(
        event_stream(request, db, run_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


def register_sse_routes(app: FastAPI, db: ControlDB, actor: Any, state_for: Any) -> None:
    @app.get("/api/events")
    async def global_events(request: Request, _: str = Depends(actor)) -> StreamingResponse:
        return sse_response(request, db)

    @app.get("/api/runs/{run}/events")
    async def run_events(request: Request, run: str, _: str = Depends(actor)) -> StreamingResponse:
        state_for(run)
        return sse_response(request, db, run)
