"""Translates service-layer exceptions into HTTP responses."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.services.exceptions import ConflictError, NotFoundError, UpstreamError
from app.services.idempotency import IdempotencyConflictError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def _not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(IdempotencyConflictError)
    async def _idem_conflict(_: Request, exc: IdempotencyConflictError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": str(exc), "code": "idempotency_conflict"},
        )

    @app.exception_handler(ConflictError)
    async def _conflict(_: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(UpstreamError)
    async def _upstream(_: Request, exc: UpstreamError) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={"detail": str(exc), "code": "upstream_error"},
        )
